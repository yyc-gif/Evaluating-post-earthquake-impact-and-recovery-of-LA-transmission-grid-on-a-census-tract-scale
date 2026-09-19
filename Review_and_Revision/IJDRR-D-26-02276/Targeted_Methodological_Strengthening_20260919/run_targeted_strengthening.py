"""Authorized 64 corrected-candidate + 128 DS4-duration chains; no new sampling/GA.

Checkpoints are saved immediately after each scientific return. Postprocessing is
separate and can be repaired without repeating a scientific execution.
"""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import sys
import time
import traceback
import zipfile
import numpy as np
import pandas as pd
import networkx as nx

ROOT = Path('R:/')
REVIEW = ROOT/'Review_and_Revision/IJDRR-D-26-02276'
OUT = Path(__file__).resolve().parent
R26 = REVIEW/'26_GA_Reproducibility_and_Revised_Paired_Pilot_20260919'
ASSESS = REVIEW/'Methodological_Strengthening_Assessment_20260919'
STRATEGIES = ('Hospital-first','GA-Balanced','GA-HospFirst','GA-Efficiency')
ARCHIVE = OUT/'SCIENTIFIC_RUN_CHECKPOINTS.zip'
JOURNAL = OUT/'EXECUTION_JOURNAL.jsonl'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def nhash(values):
    return hashlib.sha256(('\n'.join(map(str,values))+'\n').encode()).hexdigest()

def vhash(ids, values):
    return nhash(f'{i},{float(v):.17g}' for i,v in zip(ids,values))

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    sys.path.insert(0,str(Path(path).parent))
    try: spec.loader.exec_module(module)
    finally: sys.path.pop(0)
    return module

def record(**row):
    with JOURNAL.open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(row,ensure_ascii=False)+'\n');handle.flush()

def prepare():
    original=json.loads((R26/'SCIENCE_RUN_MANIFEST.json').read_text())
    directories={
        'r5':REVIEW/'05_R1_310_DryBuild_20260913',
        'r6':REVIEW/'06_R1_310_LocalClosure_20260914',
        'r10':REVIEW/'10_SCE_ServiceLayer_Architecture_20260914',
        'r14':REVIEW/'14_Production_Interface_Contract_20260914',
        'r16':REVIEW/'16_R1_Dynamic_Export_Contract_20260915',
        'r23':REVIEW/'23_R1_310_Scheduling_Input_Readiness_20260916',
        'r24':REVIEW/'24_R1_Event_Based_Scheduler_20260917',
        'r25b':REVIEW/'25B_R1_One_Realization_Schedule_Integration_Repair_20260917',
    }
    d=directories
    paths={
        'main_model':ROOT/'C257H_Project_Main.py',
        'r1_readiness':d['r5']/'R1_310_INPUT_READINESS.csv',
        'station_qa':d['r5']/'R1_310_STATIONS_QA.csv',
        'graph':d['r6']/'R1_310_EDGES.csv',
        'task_domain':d['r23']/'R1_TASK_DOMAIN_AND_ELIGIBILITY.csv',
        'priority':d['r23']/'R1_ARCHB_PRIORITY_COMPONENTS.csv',
        'ga_readiness':d['r23']/'R1_GA_INPUT_READINESS.json',
        'base_travel':d['r23']/'R1_BASE_TO_TASK_TRAVEL_HR.csv',
        'task_travel':d['r23']/'R1_TASK_TO_TASK_TRAVEL_HR.csv',
        'crew_roster':d['r23']/'R1_CREW_SCENARIO_ROSTERS.csv',
        'scheduler':d['r24']/'r1_event_based_scheduler.py',
        'revised_runner':d['r25b']/'R1_REVISED_REALIZATION_RUNNER.py',
        'exporter':d['r16']/'r1_effective_state_exporter.py',
        'service_interface':d['r14']/'service_layer_interface.py',
        'service_nodes':d['r10']/'SCE_SERVICE_NODES_196.csv',
        'attachments':d['r10']/'SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv',
        'w1':d['r10']/'SCE_TRACT_SERVICE_W1.csv',
        'tract_metadata':d['r10']/'SERVICE_LAYER_COVERAGE_QA.csv',
    }
    hashes={k:sha(p) for k,p in paths.items()}
    assert hashes==original['input_hashes'], 'Frozen scientific input mismatch'
    outputs={p.name:sha(p) for p in R26.iterdir() if p.is_file() and p.name!='run_revised_paired_pilot.py'}
    assessed=json.loads((ASSESS/'ASSESSMENT_CALCULATION_PROVENANCE.json').read_text())
    for k,h in assessed['original_hashes'].items():
        if k!='run_revised_paired_pilot.py': assert outputs[k]==h,(k,'Round26 history modified')

    # Import definitions only: never call the Round26 main, run_ga, or sampling functions.
    legacy=load(R26/'run_revised_paired_pilot.py','strengthening_r26_definitions')
    evidence=np.load(R26/'REVISED_PAIRED_PILOT_EVIDENCE.npz',allow_pickle=True)
    ids=tuple(map(str,evidence['domain_ids']));full=tuple(map(str,evidence['full_r1_ids']))
    damage=evidence['physical_damage_states'].copy();duration=evidence['physical_duration_hr'].copy()
    oldseq=pd.read_csv(R26/'GA_CANONICAL_SEQUENCES.csv',dtype={'R1_station_id':str})
    seqs={s:tuple(g.sort_values('rank').R1_station_id) for s,g in oldseq.groupby('strategy')}
    priority=pd.read_csv(paths['priority'],dtype={'R1_station_id':str}).set_index('R1_station_id').loc[list(ids)]
    base=pd.read_csv(paths['base_travel'],dtype={'yard_id':str}).set_index('yard_id').loc[:,list(ids)]
    travel=pd.read_csv(paths['task_travel'],dtype={'R1_station_id':str}).set_index('R1_station_id').loc[list(ids),list(ids)]
    crew=legacy.expand_c57(pd.read_csv(paths['crew_roster'],dtype={'yard_id':str}))
    origins=np.array([base.index.get_loc(x) for x in crew.origin_key])
    score_rows=[];seqrows=[];scores={}
    work=evidence['expected_workload_hr'].copy()
    assessed_scores=pd.read_csv(ASSESS/'GA_SAVED_SEQUENCE_RESCORING.csv')
    history=pd.read_csv(R26/'GA_CONVERGENCE_BY_SEED.csv')
    index={v:i for i,v in enumerate(ids)}
    for policy,weights in legacy.POLICIES.items():
        pr=(weights['W_POP']*priority.population_priority_score+weights['W_HOSP']*priority.hospital_priority_score+weights['W_SVI']*priority.sovi_priority_score).to_numpy()/(weights['W_POP']+weights['W_HOSP']+weights['W_SVI'])
        decoder=legacy.SurrogateDecoder(base.to_numpy(),travel.to_numpy(),origins,work,pr,weights['W_MAKESPAN'])
        recovered=tuple(ids[i] for i in np.argsort(-pr,kind='stable'))
        expected=assessed_scores[(assessed_scores.objective==policy)&(assessed_scores.sequence=='initial_priority_desc')].iloc[0]
        assert nhash(recovered)==expected.sequence_sha256
        old=seqs[policy]
        if policy!='GA-Efficiency': seqs[policy]=recovered
        scores[policy]={}
        for label,sequence in [('original_last_generation',old),('recoverable_initializer',recovered),('Hospital-first_incumbent',seqs['Hospital-first']),('selected',seqs[policy])]:
            value=decoder.evaluate(tuple(index[x] for x in sequence))
            scores[policy][label]=value.fitness
            score_rows.append(dict(objective=policy,candidate=label,fitness=value.fitness,completion_benefit=value.completion_benefit,surrogate_makespan_hr=value.makespan_hr,sequence_hash=nhash(sequence)))
        historical_best=float(history.loc[history.policy==policy,'generation_best_fitness'].max())
        assert scores[policy]['selected']>=historical_best-1e-12
        assert scores[policy]['selected']>=scores[policy]['Hospital-first_incumbent']-1e-12
    for strategy in STRATEGIES:
        assert len(seqs[strategy])==302 and set(seqs[strategy])==set(ids)
        source='reconstructed_deterministic_priority_initializer' if strategy in ('GA-Balanced','GA-HospFirst') else 'retained_R26_canonical' if strategy=='GA-Efficiency' else 'frozen_R23_rule'
        for rank,station in enumerate(seqs[strategy],1):
            seqrows.append(dict(strategy=strategy,rank=rank,R1_station_id=station,candidate_source=source,sequence_hash=nhash(seqs[strategy]),objective_fitness=scores.get(strategy,{}).get('selected'),claim='known best recorded score candidate; not global optimum' if strategy!='Hospital-first' else 'fixed rule'))
    config=dict(
        assessment_commit='5f998edefc36d147c93a1ca3767e5d8ee14ecc9d',baseline_commit='1d1015ff2d636bb36385267ce5a52df7ac28aefc',
        input_paths={k:str(v) for k,v in paths.items()},input_hashes=hashes,original_R26_artifact_hashes=outputs,
        sequence_hashes={s:nhash(x) for s,x in seqs.items()},objective_scores=scores,
        driver_sha256=sha(__file__),GA_output_code_old_hash=original['runner_sha256'],GA_output_code_new_hash=sha(R26/'run_revised_paired_pilot.py'),
        new_GA_searches=0,new_physical_draws=0,maximum_new_scientific_executions=192,
        baseline_new_runs=64,baseline_reused_runs=64,DS4x2_new_runs=128,
        mapping_lambdas=[0.5,1,2],mapping_analysis='offline fixed decisions, C and resolved mass unchanged',
        duration_change='only stored DS4 durations multiplied by 2; no reoptimization',
        bootstrap_resamples=10000,bootstrap_seed=20260919,near_zero_hr=1.0,
        source_ids_hash=nhash(sorted(legacy.REFERENCE_SOURCE_IDS)),
        physical_vectors=[dict(realization_id=i,damage_hash=vhash(ids,damage[i]),baseline_duration_hash=vhash(ids,duration[i]),DS4x2_duration_hash=vhash(ids,np.where(damage[i]==4,2*duration[i],duration[i]))) for i in range(32)],
    )
    freeze=OUT/'STRENGTHENING_INPUT_MANIFEST.json'
    if freeze.exists():
        previous=json.loads(freeze.read_text())
        if previous!=config:
            repair=json.loads((OUT/'PREEXECUTION_HARNESS_REPAIR.json').read_text())
            assert previous['driver_sha256']==repair['original_driver_sha256']
            assert config['driver_sha256']==repair['corrected_driver_sha256']
            assert {k:v for k,v in previous.items() if k!='driver_sha256'}=={k:v for k,v in config.items() if k!='driver_sha256'},'Scientific inputs changed'
    else:
        pd.DataFrame(seqrows).to_csv(OUT/'FROZEN_CANDIDATE_SEQUENCES.csv',index=False,float_format='%.17g',lineterminator='\n')
        pd.DataFrame(score_rows).to_csv(OUT/'CANDIDATE_OBJECTIVE_COMPARISON.csv',index=False,float_format='%.17g',lineterminator='\n')
        freeze.write_text(json.dumps(config,indent=2),encoding='utf-8')
    print('PREEXECUTION FREEZE',sha(freeze), '64 corrected + 128 DS4x2; no GA or sampling',flush=True)

    modules={k:load(paths[k],'strengthening_'+k) for k in ('scheduler','revised_runner','exporter','service_interface','main_model')}
    edges=pd.read_csv(paths['graph'],dtype={'src':str,'tgt':str})
    graph=nx.Graph();graph.add_nodes_from(full);graph.add_edges_from(edges[['src','tgt']].itertuples(index=False,name=None))
    assert (graph.number_of_nodes(),graph.number_of_edges())==(310,1040)
    identified=pd.Series(True,index=full,dtype=bool);identified.loc[list(legacy.UNRESOLVED_IDS)]=False
    service_ids=tuple(pd.read_csv(paths['service_nodes'],dtype=str).service_node_id)
    attachments=pd.read_csv(paths['attachments'],dtype=str,keep_default_na=False)
    # Read these exactly as Round26, including its CSV numeric parser.
    w1=pd.read_csv(paths['w1'],dtype={'tract_id':str})
    metadata=pd.read_csv(paths['tract_metadata'],dtype={'tract_id':str})
    metadata['sovi_quartile']=pd.qcut(metadata.SOVI_SCORE,4,labels=['Q1','Q2','Q3','Q4'])
    return locals()

def execute(c):
    legacy=c['legacy'];mods=c['modules'];ids=c['ids'];full=c['full']
    jobs=[('baseline',i,s) for i in range(32) for s in ('GA-Balanced','GA-HospFirst')]+[('DS4x2',i,s) for i in range(32) for s in STRATEGIES]
    records=[json.loads(x) for x in JOURNAL.read_text().splitlines()] if JOURNAL.exists() else []
    completed={r['key'] for r in records if r['status']=='checkpoint_saved'}
    pending=set()
    for r in records:
        if r['status']=='started':pending.add(r['key'])
        elif r['status'] in ('checkpoint_saved','pre_scientific_validation_failed'):pending.discard(r['key'])
    assert not pending, 'Uncheckpointed execution exists; inspect failure evidence before any restart'
    count=len(completed)
    metadata=c['metadata'];tract_ids=metadata.tract_id.tolist()
    for scenario,rid,strategy in jobs:
        key=f'{scenario}/r{rid:02d}/{strategy}'
        if key in completed: continue
        assert count<192
        ds=c['damage'][rid].copy();duration=c['duration'][rid].copy()
        if scenario=='DS4x2':duration[ds==4]*=2
        vectors=c['config']['physical_vectors'][rid]
        assert vhash(ids,ds)==vectors['damage_hash']
        assert vhash(ids,duration)==vectors['baseline_duration_hash' if scenario=='baseline' else 'DS4x2_duration_hash']
        provenance=dict(schema_version=mods['exporter'].SCHEMA_VERSION,trajectory_id=f'targeted|{scenario}|{strategy}|r{rid:02d}',producer_file=Path(__file__).name,producer_function='run_revised_realization',effective_state_semantics=mods['exporter'].EFFECTIVE_STATE_SEMANTICS,frozen_R1_ID_hash=mods['exporter'].hash_frozen_r1_ids(full),source_time_unit='hours_since_event',source_scenario_identifier='REFERENCE_SOURCE_AVAILABILITY_SCENARIO_21',producer_code_hash=sha(c['paths']['revised_runner']))
        record(key=key,status='started',ordinal=count+1,time_unix=time.time(),manifest_hash=sha(OUT/'STRENGTHENING_INPUT_MANIFEST.json'))
        count+=1;begin=time.perf_counter()
        try:
            result=mods['revised_runner'].run_revised_realization(
                domain_ids=ids,full_priority_sequence=c['seqs'][strategy],
                damage_states=pd.Series(ds,index=ids,name='damage_state'),realized_duration_hr=pd.Series(duration,index=ids,name='realized_duration_hr'),
                base_to_task_hr=c['base'],task_to_task_hr=c['travel'],crew_roster=c['crew'],
                full_r1_ids=full,state_identified_static=c['identified'],graph=c['graph'],source_ids=set(legacy.REFERENCE_SOURCE_IDS),requested_event_horizon='max_completion',
                service_attachment_ledger=c['attachments'],w1=c['w1'],tract_metadata=metadata,service_ids=c['service_ids'],
                scheduler_callable=mods['scheduler'].execute_event_based_schedule,
                source_gate_callable=mods['main_model'].apply_source_gate_to_substation_series,
                exporter_callable=mods['exporter'].export_r1_effective_state_trajectory,
                service_evaluator_callable=mods['service_interface'].evaluate_service_layer_trajectory,
                exporter_provenance=provenance,
            )
            record(key=key,status='scientific_returned',seconds=time.perf_counter()-begin)
            # Persist completed science before any reporting/invariant comparison.
            intervals=result.service_evaluation.tract_intervals
            lower=intervals.pivot(index='time_index',columns='tract_id',values='lower').reindex(columns=tract_ids).to_numpy()
            resolved=intervals[intervals.time_index==0].set_index('tract_id').reindex(tract_ids).resolved_mass.to_numpy()
            times=result.event_times_hr
            semantic=result.service_evaluation.network_trajectory.reindex(columns=full).to_numpy()
            services=result.service_evaluation.service_trajectory.reindex(columns=c['service_ids']).to_numpy()
            npz=io.BytesIO()
            np.savez_compressed(npz,domain_ids=np.array(ids),full_r1_ids=np.array(full),service_ids=np.array(c['service_ids']),tract_ids=np.array(tract_ids),times=times,damage=ds,duration=duration,raw=result.raw_functionality.to_numpy(),effective=semantic,identified=result.state_identified.to_numpy(),service_states=services,lower=lower,resolved_mass=resolved,network_deficit_integrals=np.sum((1-semantic[:-1])*np.diff(times)[:,None],axis=0),service_deficit_integrals=np.sum((1-services[:-1])*np.diff(times)[:,None],axis=0))
            with zipfile.ZipFile(ARCHIVE,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                z.writestr(key+'/evidence.npz',npz.getvalue())
                z.writestr(key+'/task_events.csv',result.schedule.task_events.to_csv(index=False,float_format='%.17g',lineterminator='\n'))
            record(key=key,status='checkpoint_saved',ordinal=count,seconds=time.perf_counter()-begin,evidence_sha256=hashlib.sha256(npz.getvalue()).hexdigest())

            events=result.schedule.task_events
            expected=[i for i in c['seqs'][strategy] if ds[ids.index(i)]>0]
            assert events.task_id.tolist()==expected,'Realized queue changed'
            assert np.array_equal(events.realized_duration_hr.to_numpy(),[duration[ids.index(i)] for i in expected])
            assert np.array_equal(events.damage_state.to_numpy(),[ds[ids.index(i)] for i in expected])
            assert np.array_equal(events.completion_hr.to_numpy(),events.arrival_hr.to_numpy()+events.realized_duration_hr.to_numpy())
            class_c=c['attachments'].set_index('service_node_id').loc[list(c['service_ids'])].attachment_class.str.startswith('C')
            assert np.isnan(services[:,class_c]).all()
            for j,row in c['attachments'].set_index('service_node_id').loc[list(c['service_ids'])].iterrows():
                if row.attachment_class.startswith('C'):continue
                assert np.array_equal(services[:,c['service_ids'].index(j)],semantic[:,full.index(row.selected_upstream_R1_id)],equal_nan=True)
            assert not (np.diff(result.raw_functionality.to_numpy(),axis=0)<-1e-12).any()
            assert not (np.diff(semantic,axis=0)<-1e-12).any()
            assert np.nanmin(semantic)>=0 and np.nanmax(semantic)<=1
            assert np.allclose(intervals.resolved_mass+intervals.unresolved_mass,1,atol=5e-12,rtol=0)
            assert (intervals.lower<=intervals.upper+1e-12).all()
            assert np.allclose(resolved[None,:]-lower[-1:,:],0,atol=5e-12,rtol=0)
            record(key=key,status='invariants_passed')
            print(f'COMPLETE {count}/192 {key} {time.perf_counter()-begin:.1f}s',flush=True)
            del result,intervals,lower,semantic,services,npz
        except Exception:
            record(key=key,status='failure',traceback=traceback.format_exc())
            raise
    assert count==192
    assert all(sha(p)==c['hashes'][k] for k,p in c['paths'].items())
    assert all(sha(R26/k)==h for k,h in c['outputs'].items())
    record(status='all_science_complete',scientific_executions=192,new_GA_searches=0,new_draws=0,frozen_inputs_unchanged=True)
    print('ALL SCIENCE COMPLETE; 192 new chains, 64 reused; no new GA or physical samples.',flush=True)

if __name__=='__main__':
    execute(prepare())
