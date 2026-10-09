"""Planning-selected exploratory evaluation; never writes formal authorities."""
from pathlib import Path
import hashlib,json,time
import numpy as np,pandas as pd
from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import INITIAL_BY_DS,evaluate_completion_step_functionality
from la_grid.revision.r1_source_gate import evaluate_source_gate
from la_grid.revision.formal.offline import PreparedMapping,evaluate_exact_event_arrays
SEARCH=R/'results/diagnostics/extended_ga_20261008';OUT=SEARCH/'independent_evaluation'

def selection():
    assert (SEARCH/'SEARCH_DECISION.json').exists(),'Search must finish before planning-only selection'
    rows=pd.read_csv(SEARCH/'SEARCH_SUMMARY.csv').sort_values('retained_service_loss_hr')
    selected=[];seen=set()
    for _,row in rows.iterrows():
        if row.sequence_sha256 in seen or not row.strict_improvement:continue
        folder=f'p{int(row.population)}_g{int(row.generations)}_s{int(row.seed)}';run=json.loads((SEARCH/folder/'RUN.json').read_text())
        seq=run['retained_sequence'];assert old.identity(seq)==row.sequence_sha256
        selected.append(dict(candidate_id=f'ga-exploratory-{len(selected)+1:02}',planning_run=folder,sequence_sha256=row.sequence_sha256,sequence=seq,planning_loss_hr=float(row.retained_service_loss_hr)))
        seen.add(row.sequence_sha256)
        if len(selected)==2:break
    assert len(selected)==2
    record=dict(selection_rule='Two lowest planning losses among distinct sequences from the completed unchanged-operator search; evaluation outcomes not consulted.',selection_time_utc=pd.Timestamp.now(tz='UTC').isoformat(),candidate_count=2,candidates=selected,formal_policy_replaced=False)
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'CANDIDATE_SELECTION.json'
    if path.exists():
        saved=json.loads(path.read_text());assert saved['candidates']==selected;return saved
    path.write_text(json.dumps(record,indent=2)+'\n');return record

def load():
    formal=R/'Formal_Experiment_20260923';path=formal/'Stage 1 Output_expanded/physical_inputs_2pc50.npz';manifest=json.loads((path.parent/'PHYSICAL_INPUTS_FROZEN.json').read_text());assert old.digest(path)==manifest['files_sha256']['2pc50']
    with np.load(path) as z:ids=z['station_ids'].astype(str).tolist();ds=z['evaluation_ds'].T.copy();dur=z['evaluation_duration'].T.copy()
    context,decoder,hashes=execution_context(ids);origins=decoder.origins(context['origins'])
    long=pd.read_csv(R/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str,'substation_id':str});w=long.pivot_table(index='tract_id',columns='substation_id',values='weight',aggfunc='sum',fill_value=0).reindex(columns=ids,fill_value=0)
    meta=pd.read_csv(R/'provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv',dtype={'tract_id':str}).set_index('tract_id')
    mapping=PreparedMapping.from_frame('M1_UTILITY_003',w,ids,meta.population,meta.SOVI_quartile,set(meta.index[meta.hospital_tract]))
    return ids,ds,dur,manifest,context,decoder,origins,mapping,hashes

def evaluate_one(sequence,b,inputs):
    ids,ds,dur,manifest,context,decoder,origins,mapping,hashes=inputs
    sample=f'2pc50__evaluation_{b:04}'
    h=hashlib.sha256(('\n'.join(ids)+'\n').encode()+ds[b].astype('<i8').tobytes()+dur[b].astype('<f8').tobytes()).hexdigest();assert h==manifest['sample_hashes'][sample]
    completion,arrival,travel,crew,previous,dispatch,clocks=decoder.decode(order=decoder.order(sequence),damage=ds[b],duration=dur[b],origins=origins)
    finite=completion[np.isfinite(completion)];assert len(finite)==np.count_nonzero(ds[b]) and finite.max()<480
    event=np.unique(np.r_[0,finite,480.]);raw=evaluate_completion_step_functionality(damage_state=pd.Series(ds[b],index=ids),completion_time_hr=pd.Series(completion,index=ids),time_hr=event,initial_functionality_by_ds=INITIAL_BY_DS)
    trace=evaluate_source_gate(raw,context['graph'],context['sources'],threshold=.5)
    arrays={k:getattr(trace,k).to_numpy() for k in ['f','F','C','e','L_self','L_threshold','L_source','L_total']}
    summary,tract,station=evaluate_exact_event_arrays(mapping=mapping,event_time_hr=event,**{k:v for k,v in arrays.items() if k not in ['F','C']})
    summary.update(realization_id=sample,task_count=len(finite),makespan_hr=float(finite.max()),total_travel_hr=float(travel[np.isfinite(travel)].sum()))
    tasks=[dict(realization_id=sample,station_id=ids[j],damage_state=int(ds[b,j]),dispatch_rank=int(dispatch[j])+1,crew_index=int(crew[j]),arrival_hr=float(arrival[j]),completion_hr=float(completion[j]),travel_hr=float(travel[j]),previous_station=ids[previous[j]] if previous[j]>=0 else '') for j in np.argsort(dispatch) if dispatch[j]>=0]
    return summary,tract,tasks,event,arrays

def run(candidate,inputs):
    folder=OUT/candidate['candidate_id'];folder.mkdir(exist_ok=True)
    if (folder/'EVALUATION.json').exists():
        saved=json.loads((folder/'EVALUATION.json').read_text());assert saved['sequence_sha256']==candidate['sequence_sha256']
        for f,h in saved['files_sha256'].items():assert old.digest(folder/f)==h
        return
    ids,ds,dur,manifest,context,decoder,origins,mapping,hashes=inputs
    grid=np.arange(481);records=[];tasks=[];curves=np.zeros((len(grid),3));integrals=[]
    for batch in range(10):
        file=folder/f'batch_{batch:02}.npz';csv=folder/f'batch_{batch:02}_summary.csv';taskfile=folder/f'batch_{batch:02}_tasks.csv';batch_record=folder/f'batch_{batch:02}.json'
        if batch_record.exists():
            saved=json.loads(batch_record.read_text());assert saved['sequence_sha256']==candidate['sequence_sha256']
            for f,h in saved['files_sha256'].items():assert old.digest(folder/f)==h
            with np.load(file) as z:curves+=z['curve_sum'];integrals.extend(z['tract_normalized_loss']);
            records.extend(pd.read_csv(csv).to_dict('records'));tasks.extend(pd.read_csv(taskfile,keep_default_na=False).to_dict('records'));continue
        batchrows=[];batchtasks=[];events=[];allarrays={k:[] for k in ['f','F','C','e','L_self','L_threshold','L_source','L_total']};length=[];tractrows=[];curve_sum=np.zeros_like(curves)
        for b in range(batch*100,(batch+1)*100):
            summary,tract,event_tasks,event,arrays=evaluate_one(candidate['sequence'],b,inputs)
            records.append(summary);batchrows.append(summary);tasks.extend(event_tasks);batchtasks.extend(event_tasks);events.append(event);length.append(len(event));integrals.append(tract['normalized_burden_hr']);tractrows.append(tract['normalized_burden_hr'])
            for k in allarrays:allarrays[k].append(arrays[k])
            ix=np.clip(np.searchsorted(event,grid,side='right')-1,0,len(event)-1);mass=mapping.weight.T@mapping.population;total=float(mass.sum())
            curve_sum+=np.column_stack([arrays['f'][ix].mean(axis=1),arrays['e'][ix].mean(axis=1),arrays['e'][ix]@mass/total])
        curves+=curve_sum
        np.savez_compressed(file,station_ids=np.array(ids),tract_ids=mapping.tract_ids,event_lengths=length,event_time_hr=np.concatenate(events),tract_normalized_loss=np.array(tractrows),curve_sum=curve_sum,**{k:np.concatenate(v) for k,v in allarrays.items()})
        pd.DataFrame(batchrows).to_csv(csv,index=False);pd.DataFrame(batchtasks).to_csv(taskfile,index=False)
        batch_record.write_text(json.dumps({'sequence_sha256':candidate['sequence_sha256'],'realization_count':100,'files_sha256':{f.name:old.digest(f) for f in [file,csv,taskfile]}},indent=2)+'\n')
        print('Evaluation',candidate['candidate_id'],(batch+1)*100,'of 1000',flush=True)
    summary=pd.DataFrame(records);assert len(summary)==1000 and not summary.realization_id.duplicated().any();summary['candidate_id']=candidate['candidate_id'];summary.to_csv(folder/'SUMMARY.csv',index=False)
    pd.DataFrame(tasks).to_csv(folder/'TASK_EXECUTION.csv',index=False)
    np.savez_compressed(folder/'TRACT_LOSS.npz',tract_ids=mapping.tract_ids,loss=np.array(integrals))
    pd.DataFrame({'time_hr':grid,'station_mean_f':curves[:,0]/1000,'station_mean_e':curves[:,1]/1000,'population_service_availability':curves[:,2]/1000}).to_csv(folder/'CURVES.csv',index=False)
    identity=dict(status='COMPLETE_EXPLORATORY_EVALUATION',formal_policy_replaced=False,sequence_sha256=candidate['sequence_sha256'],planning_selection_sha256=old.digest(OUT/'CANDIDATE_SELECTION.json'),sample_file_sha256=manifest['files_sha256']['2pc50'],mapping='M1_UTILITY_003',gate='G1_BASELINE_050',resource='C57_D1',horizon_hr=480,context_identity=hashes,files_sha256={p.name:old.digest(p) for p in folder.iterdir() if p.suffix in ['.csv','.npz']})
    (folder/'EVALUATION.json').write_text(json.dumps(identity,indent=2)+'\n')

def main():
    selected=selection();inputs=load()
    formal=pd.concat([pd.read_parquet(R/'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet'),pd.read_parquet(R/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet')],ignore_index=True);formal=formal[formal.hazard.eq('2pc50')&formal.resource_scenario.eq('C57_D1')&formal.mapping.eq('M1_UTILITY_003')&formal.gate.eq('G1_BASELINE_050')]
    impact=json.loads((R/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']['impact-first'];baseline=formal[formal.strategy_id.eq('impact-first')].set_index('realization_id')
    parity=[]
    for b in range(3):
        values=evaluate_one(impact,b,inputs)[0];expected=baseline.loc[values['realization_id']]
        for k,v in values.items():
            if k in expected and isinstance(v,(int,float)):parity.append(abs(v-expected[k]))
    assert max(parity)<1e-8; (OUT/'FORMAL_PARITY.json').write_text(json.dumps({'three_realization_metric_max_abs_error':max(parity)},indent=2))
    for candidate in selected['candidates']:run(candidate,inputs)
    from la_grid.plotting.selected_strategy_evidence import METRICS
    effects=[];comparisons=[]
    for c in selected['candidates']:
        q=pd.read_csv(OUT/c['candidate_id']/'SUMMARY.csv').set_index('realization_id')
        for ref in ['impact-first','hospital-first','vulnerability-first','degree-first','betweenness-first','random','unconstrained']:
            base=formal[formal.strategy_id.eq(ref)].set_index('realization_id');assert set(q.index)==set(base.index)
            for field,label in METRICS.items():
                v=(q[field]-base[field]).to_numpy()
                effects.append(dict(candidate=c['candidate_id'],reference=ref,metric=label,source_field=field,mean_change=v.mean(),median_change=np.median(v),p05=np.quantile(v,.05),p95=np.quantile(v,.95),candidate_mean=q[field].mean(),reference_mean=base[field].mean(),n=1000,interval='5th-95th realization-difference range'))
            v=q.population_weighted_normalized_burden_hr-base.population_weighted_normalized_burden_hr
            comparisons.extend(dict(candidate=c['candidate_id'],reference=ref,realization_id=i,change_hr=float(x)) for i,x in v.items())
    pd.DataFrame(effects).to_csv(OUT/'OUTCOME_COMPARISONS.csv',index=False);pd.DataFrame(comparisons).to_csv(OUT/'REALIZATION_SERVICE_LOSS_CHANGES.csv',index=False)
    print(pd.DataFrame(effects).query("source_field=='population_weighted_normalized_burden_hr'").to_string(index=False),flush=True)
if __name__=='__main__':main()
