"""Instrument the unchanged formal GA for independent search-budget diagnostics."""
from pathlib import Path
import argparse, hashlib, inspect, json, time
import numpy as np
import pandas as pd
from la_grid.paths import REPO_ROOT
from la_grid.revision.r1_ga_revision import RevisedGAConfig, run_revised_permutation_ga
from la_grid.revision.r1_ga_exact_kernel import ExactDirectPlanningKernel, _one_sample
from la_grid.revision.r1_realization_scheduling import RealizationInputs
from la_grid.revision.r1_equity_amendment_execute import execution_context

ROOT=REPO_ROOT
OUT=ROOT/'results/diagnostics/ga_search_budget_20261007'
FORMAL=ROOT/'Formal_Experiment_20260923'
THRESHOLDS=(1e-6,1e-4,1e-3,1e-2)

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(seq):return hashlib.sha256(('\n'.join(seq)+'\n').encode()).hexdigest()

def load_inputs():
    stage=FORMAL/'Stage 5 Output_expanded'
    final=json.loads((stage/'FINAL_DIRECT_COMMUNITY_SEQUENCE.json').read_text())
    physical=FORMAL/'Stage 1 Output_expanded/physical_inputs_2pc50.npz'
    frozen=json.loads((physical.parent/'PHYSICAL_INPUTS_FROZEN.json').read_text())
    assert digest(physical)==frozen['files_sha256']['2pc50']
    with np.load(physical) as z:
        ids=z['station_ids'].astype(str).tolist();ds=z['planning_ds'].T.copy();duration=z['planning_duration'].T.copy()
    assert ds.shape==duration.shape==(64,92)
    sample_hashes=[];planning=[]
    for i in range(64):
        h=hashlib.sha256(('\n'.join(ids)+'\n').encode()+ds[i].astype('<i8').tobytes()+duration[i].astype('<f8').tobytes()).hexdigest()
        sample_hashes.append(h)
        planning.append(RealizationInputs(f'2pc50__planning_{i:04}',pd.Series(ds[i],index=ids),pd.Series(duration[i],index=ids)))
    assert sample_hashes==final['planning_sample_hashes']
    context,_,context_hashes=execution_context(ids);context['G']=context['graph']
    mapping=ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv'
    w=pd.read_csv(mapping,dtype={'tract_id':str,'substation_id':str})
    assert w.tract_id.nunique()==2315
    pop=w.groupby('tract_id').population.first()
    matrix=w.pivot_table(index='tract_id',columns='substation_id',values='weight',aggfunc='sum',fill_value=0).reindex(columns=ids,fill_value=0)
    mass=matrix.T.to_numpy()@pop.reindex(matrix.index).to_numpy()
    kernel=ExactDirectPlanningKernel(planning=planning,context=context,station_population_mass=mass,horizon_hr=final['H_plan_hr'])
    sequences=json.loads((FORMAL/'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']
    assert len(sequences)==7 and all(len(set(s))==92 for s in sequences.values())
    parity=pd.read_csv(stage/'INCUMBENT_DIRECT_SCORES_2pc50.csv').set_index('rule')
    scores={name:kernel.score(seq) for name,seq in sequences.items()}
    assert max(abs(scores[n]-parity.loc[n,'planning_fitness']) for n in sequences)<1e-9
    records={str(p.relative_to(ROOT)):digest(p) for p in [physical,mapping,stage/'FINAL_DIRECT_COMMUNITY_SEQUENCE.json',FORMAL/'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json',ROOT/'config/parent_frozen_design/FINAL_EXPERIMENT_MATRIX.json',ROOT/'src/la_grid/revision/r1_ga_revision.py',ROOT/'src/la_grid/revision/r1_ga_exact_kernel.py',ROOT/'data/travel/travel_task_to_task.csv',ROOT/'data/travel/travel_base_to_task.csv']}
    return kernel,sequences,dict(input_sha256=records,planning_sample_hashes=sample_hashes,context_identity=context_hashes,planning_horizon_hr=kernel.horizon,incumbent_fitness=scores,ds0_task_exclusions_per_realization=(ds==0).sum(axis=1).tolist())

def per_sample(kernel,seq):
    order=np.asarray([kernel.index[x] for x in seq],dtype=np.int64)
    return np.array([_one_sample(order,kernel.damage[i],kernel.duration[i],kernel.origin_index,kernel.base,kernel.travel,kernel.neighbor_offset,kernel.neighbors,kernel.source_flag,kernel.station_mass,kernel.total_mass,kernel.horizon) for i in range(64)])

def run_one(kernel,inc,global_cache,population,generations,seed,stage):
    folder=OUT/f'p{population}_g{generations}_s{seed}';folder.mkdir(parents=True,exist_ok=True)
    result_path=folder/'RUN.json'
    if result_path.exists():
        old=json.loads(result_path.read_text())
        if old['status']=='COMPLETE':
            expected=dict(population_size=population,generations=generations,crossover_probability=.8,mutation_probability=.2,tournament_size=3)
            assert old['config']==expected and old['summary']['seed']==seed
            for name,expected_sha in old['artifacts_sha256'].items():assert digest(folder/name)==expected_sha
            with np.load(folder/'CANDIDATES.npz') as z:
                for order,value in zip(z['orders'],z['fitness']):
                    key=order.tobytes()
                    if key in global_cache:assert abs(global_cache[key]-value)<1e-12
                    global_cache[key]=float(value)
            return old['summary']
    inc_set={tuple(s) for s in inc.values()}; impact=tuple(inc['impact-first']); inc_score=kernel.score(impact)
    seen=[];fitness=[];firstgen=[];started=time.time()
    def objective(seq):
        frame=inspect.currentframe().f_back;gen=0
        for _ in range(5):
            if frame is None:break
            if frame.f_code.co_name=='update':gen=frame.f_locals['generation'];break
            frame=frame.f_back
        order=bytes(kernel.index[x] for x in seq)
        if order not in global_cache:global_cache[order]=kernel.score(seq)
        value=global_cache[order];seen.append(order);fitness.append(value);firstgen.append(gen)
        return value
    config=RevisedGAConfig(population,generations,.8,.2,3)
    run=run_revised_permutation_ga(items=kernel.ids,objective=objective,incumbents=inc,seed=seed,config=config)
    fit=np.asarray(fitness);gen=np.asarray(firstgen,dtype=np.int16);orders=np.array([np.frombuffer(x,dtype=np.uint8) for x in seen])
    assert len(seen)==len(set(seen))
    non=np.array([tuple(kernel.ids[j] for j in order) not in inc_set for order in orders])
    idx=np.flatnonzero(non)[np.argmax(fit[non])]
    seq=tuple(kernel.ids[j] for j in orders[idx]);gap=-fit[idx]+inc_score
    history=run.history.copy()
    history['non_incumbent_best_so_far']=[float(fit[non & (gen<=g)].max()) if (non & (gen<=g)).any() else np.nan for g in history.generation]
    history.to_csv(folder/'HISTORY.csv',index=False)
    if population==100 and generations==100 and seed in range(42,47):
        original=pd.read_csv(FORMAL/f'Stage 5 Output_expanded/GA_HISTORY_2pc50_{seed}.csv')
        assert np.max(np.abs(original[['generation_best','generation_mean','best_so_far']].to_numpy()-history[['generation_best','generation_mean','best_so_far']].to_numpy()))<1e-9
    np.savez_compressed(folder/'CANDIDATES.npz',station_ids=np.array(kernel.ids),orders=orders,fitness=fit,first_generation=gen,non_incumbent=non)
    values=per_sample(kernel,seq);reference=per_sample(kernel,impact);changes=values-reference
    pd.DataFrame({'realization_id':[f'2pc50__planning_{i:04}' for i in range(64)],'impact_service_loss_hr':reference,'best_non_incumbent_service_loss_hr':values,'change_hr':changes}).to_csv(folder/'PLANNING_DIFFERENCES.csv',index=False)
    # The joint effective-task signature retains the damaged order in all 64 samples.
    masks=kernel.damage>0; joint=set();individual=[set() for _ in range(64)]
    for order in orders:
        h=hashlib.sha256()
        for i,mask in enumerate(masks):
            filtered=order[mask[order]].tobytes();h.update(bytes([len(filtered)]));h.update(filtered)
            individual[i].add(filtered)
        joint.add(h.digest())
    positions=np.array([seq.index(x) for x in impact])
    summary=dict(stage=stage,seed=seed,population=population,generations=generations,unique_candidates_evaluated=len(seen),
        unique_non_incumbent_candidates=int(non.sum()),best_incumbent_fitness=inc_score,best_incumbent_service_loss_hr=-inc_score,
        best_ga_generated_non_incumbent_fitness=float(fit[idx]),best_non_incumbent_service_loss_hr=float(-fit[idx]),
        gap_from_impact_hr=float(gap),retained_service_loss_hr=-run.best_fitness,delta_J_hr=-run.best_fitness+inc_score,
        strictly_improved_incumbent=bool(run.search_improved_incumbent),best_non_incumbent_sequence_identity=identity(seq),
        generation_found=int(gen[idx]),exact_tie_candidate_count=int((fit[non]==inc_score).sum()),
        improvement_hr=float(run.best_fitness-inc_score),improvement_percent=float(100*(run.best_fitness-inc_score)/(-inc_score)),
        displaced_stations=int((positions!=np.arange(92)).sum()),rank_correlation=float(np.corrcoef(np.arange(92),positions)[0,1]),
        top10_overlap=len(set(seq[:10])&set(impact[:10])),paired_mean_hr=float(changes.mean()),paired_median_hr=float(np.median(changes)),
        effective_joint_unique_orderings=len(joint),effective_ordering_duplicate_count=len(seen)-len(joint),
        mean_unique_effective_orderings_per_realization=float(np.mean([len(s) for s in individual])),elapsed_seconds=time.time()-started)
    for t in THRESHOLDS:summary[f'near_tie_abs_gap_lt_{t:g}_hr']=int((np.abs(-fit[non]+inc_score)<t).sum())
    result=dict(status='COMPLETE',diagnostic_only=True,config=config.__dict__,summary=summary,station_ids=list(kernel.ids),
        best_non_incumbent_sequence=list(seq),retained_sequence=list(run.best_sequence),retained_source=run.candidate_source,
        artifacts_sha256={p.name:digest(p) for p in folder.iterdir() if p.is_file() and p.name!='RUN.json'})
    result_path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
    return summary

def main():
    OUT.mkdir(parents=True,exist_ok=True);kernel,inc,inputs=load_inputs()
    identity_path=OUT/'INPUT_IDENTITY.json'
    if identity_path.exists():assert json.loads(identity_path.read_text())==inputs, 'Saved diagnostic inputs differ; do not reuse or overwrite this diagnostic.'
    else:identity_path.write_text(json.dumps(inputs,indent=2)+'\n')
    cache={};rows=[];expanded_improvement=False
    schedule=[('Baseline',100,100,list(range(42,47))),('A',100,250,list(range(42,47))),('A',100,500,list(range(42,47))),('A',100,1000,list(range(42,47))),('B',250,500,list(range(42,47))),('B',500,500,list(range(42,47)))]
    for stage,p,g,seeds in schedule:
        if stage!='Baseline' and expanded_improvement:break
        for seed in seeds:
            row=run_one(kernel,inc,cache,p,g,seed,stage);rows.append(row)
            pd.DataFrame(rows).to_csv(OUT/'GA_SEARCH_BUDGET_SENSITIVITY.csv',index=False)
        if stage!='Baseline' and any(r['strictly_improved_incumbent'] for r in rows if r['stage']==stage and r['generations']==g and r['population']==p):
            expanded_improvement=True;chosen=(p,g)
    if not expanded_improvement:chosen=(250,500)
    # Twenty independent seeds in the chosen extended configuration, including 42-46.
    p,g=chosen
    existing={(r['population'],r['generations'],r['seed']) for r in rows}
    for seed in range(42,62):
        if (p,g,seed) not in existing:
            rows.append(run_one(kernel,inc,cache,p,g,seed,'C'))
            pd.DataFrame(rows).to_csv(OUT/'GA_SEARCH_BUDGET_SENSITIVITY.csv',index=False)
    (OUT/'SEARCH_DECISION.json').write_text(json.dumps(dict(status='COMPLETE',strict_improvement_found=expanded_improvement,
        chosen_restart_configuration=dict(population=p,generations=g,seeds=list(range(42,62))),
        expensive_combinations_skipped_after_stage_A_improvement=expanded_improvement,run_count=len(rows),
        unique_scored_across_runs=len(cache),formal_strategy_replaced=False),indent=2)+'\n')

if __name__=='__main__':main()