"""Summarize controlled effects without treating selected minima as optima."""
import json,math,hashlib
from pathlib import Path
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,summarize,definitions,load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.diagnostics.ga_generalization_20261009 import mean_ci


def tables():
    d=summarize();rows=[]
    for (phase,cid),q in d.groupby(['phase','config_id']):
        v=q.best_planning_loss_hr.to_numpy();rows.append(dict(phase=phase,config_id=cid,seeds=len(q),budget=q.budget.iloc[0],mean_hr=v.mean(),median_hr=np.median(v),std_hr=np.std(v,ddof=1),min_hr=v.min(),max_hr=v.max(),success_vs_impact=np.mean(v<33.57830256-1e-9),success_vs_previous=np.mean(v<33.03813174326729-1e-9),mean_attempts=q.total_attempts.mean(),mean_elapsed_seconds=q.elapsed_seconds.mean(),mean_job_seconds=q.job_wall_seconds.mean(),max_peak_rss_mb=q.peak_rss_mb.max()))
    pd.DataFrame(rows).to_csv(OUT/'CONFIGURATION_SUMMARY.csv',index=False)
    screen=d[d.phase.eq('screen')].set_index(['config_id','seed']);effects=[]
    def diff(a,b):
        aa=screen.loc[a].best_planning_loss_hr;bb=screen.loc[b].best_planning_loss_hr;assert set(aa.index)==set(bb.index);return aa.sort_index().to_numpy()-bb.sort_index().to_numpy()
    def append(factor,contrast,values,scope):
        ci=mean_ci(values,reps=10000);effects.append(dict(factor=factor,contrast=contrast,mean_effect_hr=float(np.mean(values)),std_across_seed_effect_hr=float(np.std(values,ddof=1)),min_seed_effect_hr=float(np.min(values)),max_seed_effect_hr=float(np.max(values)),bootstrap_seed_mean_ci95_low=float(ci[0]),bootstrap_seed_mean_ci95_high=float(ci[1]),seed_count=len(values),scope=scope,negative_means_lower_loss=True,exploratory_multiple_comparisons_not_corrected=True))
    for p in [50,250,500]:append('population',f'P{p} minus P100',diff(f'original_p{p}','original_p100'),'Legacy initialization; archive only, crossover .8, mutation .2, tournament3')
    for p in [100,500]:
        for m in [.05,.1,.4,.6]:append('mutation',f'P{p}: mutation {m:g} minus .2',diff(f'p{p}_m{m:g}',f'original_p{p}'),'Other mechanisms fixed')
        for k in [2,5]:append('selection',f'P{p}: tournament{k} minus3',diff(f'p{p}_k{k}',f'original_p{p}'),'Other mechanisms fixed')
        for e in [1,3]:append('elitism',f'P{p}: elite{e} minus archive-only',diff(f'p{p}_e{e}',f'original_p{p}'),'Archive in both; comparison changes evolving-population survival')
        for init in ['diverse','quality_mix']:append('initialization',f'P{p}: {init} minus legacy',diff(f'p{p}_{init}',f'original_p{p}'),'Quality mixture includes previous best: total effect includes warm-start advantage')
    for m in [.05,.1,.4,.6]:append('population x mutation',f'P500 minus P100 differential effect of mutation{m:g}',diff(f'p500_m{m:g}','original_p500')-diff(f'p100_m{m:g}','original_p100'),'Difference in differences; five common seeds')
    for k in [2,5]:append('population x selection',f'P500 minus P100 differential effect of tournament{k}',diff(f'p500_k{k}','original_p500')-diff(f'p100_k{k}','original_p100'),'Difference in differences')
    for e in [1,3]:append('population x elitism',f'P500 minus P100 differential effect of elite{e}',diff(f'p500_e{e}','original_p500')-diff(f'p100_e{e}','original_p100'),'Difference in differences')
    for c in [.6,.95]:append('crossover x mutation',f'crossover{c:g} minus .8 differential effect .4 versus .1 mutation',diff(f'p100_c{c:g}_m0.4',f'p100_c{c:g}_m0.1')-diff('p100_m0.4','p100_m0.1'),'Difference in differences; population100')
    for c in [.6,.95]:
        for m in [.1,.4]:append('crossover',f'crossover{c:g} minus .8 at mutation{m:g}',diff(f'p100_c{c:g}_m{m:g}',f'p100_m{m:g}'),'Population100, archive-only')
    pd.DataFrame(effects).to_csv(OUT/'CONTROLLED_FACTOR_EFFECTS.csv',index=False)
    budget=pd.read_csv(OUT/'GA_COMPUTATIONAL_BUDGET_COMPARISON.csv');gain=[]
    for (phase,cid,seed),q in budget.groupby(['phase','config_id','seed']):
        for a,b in [(50000,100000),(100000,250000),(250000,500000)]:
            x=q[q.distinct_evaluations.eq(a)];y=q[q.distinct_evaluations.eq(b)]
            if len(x)==1 and len(y)==1:gain.append(dict(phase=phase,config_id=cid,seed=seed,from_budget=a,to_budget=b,change_hr=y.best_service_loss_hr.iloc[0]-x.best_service_loss_hr.iloc[0],incremental_wall_seconds=y.elapsed_seconds.iloc[0]-x.elapsed_seconds.iloc[0]))
    pd.DataFrame(gain).to_csv(OUT/'BUDGET_INCREMENTAL_GAINS.csv',index=False)
    local=[]
    for parent in ['local_search','hybrid']:
        for p in (OUT/parent).glob('*/RUN.json'):
            r=json.loads(p.read_text());r['source_run']=p.relative_to(old.ROOT).as_posix();local.append({k:v for k,v in r.items() if not isinstance(v,(list,dict))})
    pd.DataFrame(local).to_csv(OUT/'GA_LOCAL_SEARCH_AND_HYBRID_RESULTS.csv',index=False)
    replays=[]
    for p in (OUT/'original_behavior_replay').glob('*/PARITY.json'):
        r=json.loads(p.read_text());q=pd.read_csv(p.parent/'GENERATION_DIAGNOSTICS.csv');lost=q[q.deterministic_incumbents_remaining.eq(0)]
        for g in [0,1,2,5,100,1000]:
            z=q[q.generation.eq(g)]
            if z.empty:continue
            z=z.iloc[0];replays.append(dict(label=r['label'],seed=r['seed'],population=r['population'],generation=g,first_generation_without_incumbents=None if lost.empty else int(lost.generation.iloc[0]),**{f:z[f] for f in ['population_best_service_loss_hr','best_so_far_service_loss_hr','unique_population','positional_hamming_fraction','mean_pair_rank_correlation','directed_adjacency_overlap','position_entropy','deterministic_incumbents_remaining','duplicate_objective_fraction','parent_selection_intensity','offspring_improving_parent_fraction'] if f in z}))
    pd.DataFrame(replays).to_csv(OUT/'ORIGINAL_SEARCH_DYNAMICS_SUMMARY.csv',index=False)
    initialization=[]
    for p in OUT.glob('*/*/RUN.json'):
        r=json.loads(p.read_text())
        if 'config' not in r:continue
        q=pd.read_csv(p.parent/'GENERATION_DIAGNOSTICS.csv');z=q[q.generation.eq(0)].iloc[0];initialization.append(dict(phase=r['phase'],config_id=r['config_id'],seed=r['seed'],generation0_best_hr=z.best_observed_service_loss_hr,final_hr=r['best_planning_loss_hr'],post_initialization_improvement_hr=z.best_observed_service_loss_hr-r['best_planning_loss_hr'],warm_start_previous_best_included=r['config']['initialization']=='quality_mix'))
    pd.DataFrame(initialization).to_csv(OUT/'INITIALIZATION_VERSUS_SEARCH_GAINS.csv',index=False)
    print('ANALYSIS TABLES',len(d),'GA runs; local/hybrid',len(local))


def planning_candidates():
    kernel,inc,previous=load();impact=tuple(inc['impact-first']);candidates=[]
    for p in OUT.glob('*/*/RUN.json'):
        q=json.loads(p.read_text())
        if 'best_planning_loss_hr' not in q or 'best_sequence' not in q:continue
        candidates.append((q['best_planning_loss_hr'],p,q))
    candidates.sort(key=lambda v:v[0]);seen=set();rows=[];values=[]
    for loss,p,q in candidates:
        if q['sequence_sha256'] in seen:continue
        seen.add(q['sequence_sha256']);seq=q['best_sequence'];ref=old.per_sample(kernel,impact);previous_v=old.per_sample(kernel,previous);v=old.per_sample(kernel,seq);pos=np.array([seq.index(s) for s in impact]);corr=1-6*np.sum((pos-np.arange(92))**2)/(92*(92*92-1));ci=mean_ci(v-previous_v)
        rows.append(dict(source_run=p.relative_to(old.ROOT).as_posix(),sequence_sha256=q['sequence_sha256'],planning_loss_hr=v.mean(),median_realization_hr=np.median(v),mean_change_vs_previous_hr=(v-previous_v).mean(),median_change_vs_previous_hr=np.median(v-previous_v),p05_change_vs_previous_hr=np.quantile(v-previous_v,.05),p95_change_vs_previous_hr=np.quantile(v-previous_v,.95),bootstrap_mean_change_ci95_low=ci[0],bootstrap_mean_change_ci95_high=ci[1],mean_change_vs_impact_hr=(v-ref).mean(),improvement_vs_impact_percent=100*(ref.mean()-v.mean())/ref.mean(),displaced_stations_vs_impact=int(np.sum(pos!=np.arange(92))),rank_correlation_vs_impact=corr,top10_overlap_vs_impact=len(set(seq[:10])&set(impact[:10])),no_global_optimality_claim=True))
        values.extend(dict(sequence_sha256=q['sequence_sha256'],planning_realization=i,service_loss_hr=x,change_vs_previous_hr=x-previous_v[i],change_vs_impact_hr=x-ref[i]) for i,x in enumerate(v))
        if len(rows)==20:break
    pd.DataFrame(rows).to_csv(OUT/'BEST_SEQUENCE_QUALITY.csv',index=False);pd.DataFrame(values).to_csv(OUT/'BEST_SEQUENCE_PLANNING_REALIZATIONS.csv',index=False)
    print('BEST DISTINCT PLANNING',rows[0])

def landscape():
    kernel,inc,previous=load();previous_key=np.array([kernel.index[x] for x in previous],dtype=np.uint8);reference=kernel.score(inc['impact-first']);rows=[]
    for path in OUT.glob('*/*/RUN.json'):
        record=json.loads(path.read_text())
        if 'config' not in record:continue
        file=path.parent/'CANDIDATES.npz'
        with np.load(file) as z:
            orders=z['orders'];fitness=z['fitness'];mask=np.ones(len(fitness),dtype=bool);mask[:7]=False
            if record['config']['initialization']=='quality_mix':mask[np.all(orders==previous_key,axis=1)]=False
            idx=np.flatnonzero(mask)[np.argmax(fitness[mask])];gap=-fitness[mask]+reference;seq=[kernel.ids[j] for j in orders[idx]];row=dict(phase=record['phase'],config_id=record['config_id'],seed=record['seed'],distinct_queries=len(fitness),generated_candidates_excluding_injected_references=int(mask.sum()),best_generated_loss_hr=-fitness[idx],best_generated_sequence_sha256=old.identity(seq),generation_found=int(z['first_generation'][idx]),exact_ties_with_impact=int(np.sum(fitness[mask]==reference)),strictly_better_than_impact=int(np.sum(fitness[mask]>reference)),fitness_unique_exact=int(np.unique(fitness[mask]).size),last_strict_best_query=int(np.flatnonzero(np.maximum.accumulate(fitness)==fitness.max())[0])+1)
            for threshold in [1e-6,1e-4,1e-3,1e-2]:row['near_impact_abs_gap_lt_'+str(threshold)]=int(np.sum(abs(gap)<threshold))
            bestgap=fitness[mask].max()-fitness[mask]
            for threshold in [1e-6,1e-4,1e-3,1e-2]:row['near_generated_best_abs_gap_lt_'+str(threshold)]=int(np.sum(bestgap<threshold))
            row['budget_since_last_best']=len(fitness)-row['last_strict_best_query'];rows.append(row)
    pd.DataFrame(rows).to_csv(OUT/'CANDIDATE_LANDSCAPE.csv',index=False)
    masks=kernel.damage>0;all_damaged=np.flatnonzero(masks.all(axis=1));assert len(all_damaged)>0
    (OUT/'EFFECTIVE_ORDER_SIGNATURE.json').write_text(json.dumps(dict(all92_damaged_planning_rows=all_damaged.tolist(),joint_signature_injective=True,reason='At least one planning realization has all 92 stations damaged; its effective order alone contains the full permutation. Joint DS>0-filtered order signatures therefore cannot collapse distinct chromosomes.',equal_objectives_do_not_imply_equal_effective_orders=True),indent=2)+'\n')

if __name__=='__main__':tables();planning_candidates();landscape()
