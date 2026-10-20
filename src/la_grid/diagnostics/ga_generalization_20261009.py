"""Predeclared internal split diagnostics and reused-cohort evaluation.
No new physical sampling. Held-out rows are excluded from each CV search.
"""
from pathlib import Path
import copy,json,argparse,time,subprocess,sys,os
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.diagnostics.ga_variant_engine import Variant,run_search
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.paths import REPO_ROOT as R
from la_grid.plotting.selected_strategy_evidence import METRICS


def mean_ci(values,seed=641209,reps=10000):
    v=np.asarray(values,float);v=v[np.isfinite(v)];rng=np.random.default_rng(seed)
    means=np.concatenate([v[rng.integers(0,len(v),(min(1000,reps-j),len(v)))].mean(axis=1) for j in range(0,reps,1000)])
    return np.quantile(means,[.025,.975])


def previous_pair():
    parent=R/'results/diagnostics/extended_ga_20261008/independent_evaluation'
    a=pd.read_csv(parent/'ga-exploratory-01/SUMMARY.csv').set_index('realization_id');b=pd.read_csv(parent/'ga-exploratory-02/SUMMARY.csv').set_index('realization_id');rows=[]
    for field,label in METRICS.items():
        v=(b[field]-a[field]).dropna().to_numpy();ci=mean_ci(v)
        rows.append(dict(candidate='existing-exploratory-02',reference='existing-exploratory-01',source_field=field,metric=label,n=len(v),mean_change=v.mean(),median_change=np.median(v),p05=np.quantile(v,.05),p95=np.quantile(v,.95),bootstrap_mean_ci95_low=ci[0],bootstrap_mean_ci95_high=ci[1],bootstrap_replicates=10000,bootstrap_seed=641209,cohort_status='Previously inspected evaluation cohort; exploratory comparison'))
    pd.DataFrame(rows).to_csv(OUT/'EXISTING_EXPLORATORY_PAIR_DIFFERENCES.csv',index=False)


def cv_one(fold,seed,elite):
    kernel,inc,quality=load();full=kernel;train=copy.copy(kernel);split=np.random.default_rng(19371).permutation(64);test_ids=split.reshape(4,16)[fold];train_ids=np.setdiff1d(np.arange(64),test_ids);train.damage=kernel.damage[train_ids].copy();train.duration=kernel.duration[train_ids].copy()
    folder=OUT/'internal_cv'/f'fold{fold}_e{elite}_s{seed}';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'RUN.json').exists():return
    result=run_search(items=kernel.ids,incumbents=inc,objective=train.score,seed=seed,config=Variant(elites=elite),max_evaluations=25000,checkpoints=(25000,),folder=folder,quality=None)
    values=old.per_sample(full,result['best_sequence']);impact=old.per_sample(full,inc['impact-first']);previous=old.per_sample(full,quality)
    pd.DataFrame({'planning_realization':range(64),'fold':fold,'used_for_search':np.isin(np.arange(64),train_ids),'candidate_service_loss_hr':values,'impact_service_loss_hr':impact,'previous_all64_selected_service_loss_hr':previous}).to_csv(folder/'TRAIN_AND_HELDOUT.csv',index=False)
    record=dict(fold=fold,seed=seed,elites=elite,total_attempts=result['state']['attempts'],elapsed_seconds=result['elapsed_seconds'],observed_search_peak_rss_mb=result['state']['peak_rss_bytes']/2**20,configuration=dict(population=100,crossover=.8,mutation=.2,tournament=3,elites=elite,initialization='legacy',mutation_operator='inversion',crossover_operator='ordered'),objective_scope='48 training samples, held-out 16 excluded from objective and sequence selection',configuration_scope='Predeclared baseline and one-elite variant, not selected using full64 tuning results',train_ids=train_ids.tolist(),heldout_ids=test_ids.tolist(),distinct_evaluations=len(result['cache']),best_sequence=list(result['best_sequence']),sequence_sha256=old.identity(result['best_sequence']),training_mean_hr=float(values[train_ids].mean()),heldout_mean_hr=float(values[test_ids].mean()),training_change_vs_impact_hr=float((values-impact)[train_ids].mean()),heldout_change_vs_impact_hr=float((values-impact)[test_ids].mean()),previous_all64_candidate_heldout_comparison_is_postselection=True,new_physical_sampling=False,formal_policy_replaced=False)
    (folder/'RUN.json').write_text(json.dumps(record,indent=2)+'\n');print('CV COMPLETE',fold,seed,elite,record['heldout_change_vs_impact_hr'],flush=True)


def cv_all():
    jobs=[(fold,seed,e) for e in [0,1] for fold in range(4) for seed in range(42,47)]
    pending=list(jobs);active=[]
    while pending or active:
        while pending and len(active)<8:
            fold,seed,e=pending.pop(0);log=(OUT/'local_logs'/f'cv_f{fold}_e{e}_s{seed}.log').open('w');p=subprocess.Popen([sys.executable,'-u','-m','la_grid.diagnostics.ga_generalization_20261009','--cv-one',str(fold),str(seed),str(e)],stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));active.append((p,log))
        for p,f in active.copy():
            if p.poll() is not None:f.close();assert p.returncode==0;active.remove((p,f))
        time.sleep(3)
    rows=[json.loads(p.read_text()) for p in (OUT/'internal_cv').glob('*/RUN.json')];assert len(rows)==40
    pd.DataFrame([{k:v for k,v in d.items() if not isinstance(v,(list,dict))} for d in rows]).to_csv(OUT/'INTERNAL_PLANNING_CV.csv',index=False)


def subset_stability():
    choices=[]
    for path in OUT.glob('*/*/RUN.json'):
        data=json.loads(path.read_text())
        if 'best_sequence' in data and 'best_planning_loss_hr' in data:choices.append(data)
    chosen=sorted(choices,key=lambda d:d['best_planning_loss_hr']);seqs=[];seen=set()
    for q in chosen:
        if q['sequence_sha256'] in seen:continue
        seen.add(q['sequence_sha256']);seqs.append((q.get('config_id',q.get('method','local'))+'_'+str(q.get('seed',''))+'_'+q['sequence_sha256'][:12],q['best_sequence']))
        if len(seqs)==12:break
    kernel,inc,previous=load();seqs=[('impact-first',inc['impact-first']),('previous-best',previous)]+seqs
    records=[];matrix=np.stack([old.per_sample(kernel,seq) for name,seq in seqs]);rng=np.random.default_rng(743091)
    for rep in range(500):
        ids=rng.choice(64,32,replace=False);mean=matrix[:,ids].mean(axis=1);ranks=pd.Series(mean).rank(method='average').to_numpy()
        for i,(name,seq) in enumerate(seqs):records.append(dict(subset=rep,candidate=name,sequence_sha256=old.identity(seq),subset_n=32,mean_service_loss_hr=mean[i],rank=ranks[i],postselection_diagnostic=True,heldout_validation=False))
    pd.DataFrame(records).to_csv(OUT/'PLANNING_SUBSET_RANK_STABILITY.csv',index=False)


def select_candidates():
    paths=list(OUT.glob('*/*/RUN.json'));records=[]
    for p in paths:
        d=json.loads(p.read_text())
        if 'best_sequence' in d and 'best_planning_loss_hr' in d and not p.parent.parent.name=='internal_cv':records.append((float(d['best_planning_loss_hr']),str(p.relative_to(R)),d))
    summary=pd.read_csv(OUT/'CONFIGURATION_SUMMARY.csv')
    reliability=summary[summary.phase.isin(['shortlist','operator_confirmation'])].set_index('config_id').mean_hr.to_dict()
    records.sort(key=lambda d:(d[0],reliability.get(d[2].get('config_id',''),float('inf')),d[1]));selected=[];seen=set()
    prior=json.loads((R/'results/diagnostics/extended_ga_20261008/independent_evaluation/CANDIDATE_SELECTION.json').read_text());seen.update(c['sequence_sha256'] for c in prior['candidates'])
    for value,source,d in records:
        h=d['sequence_sha256']
        if h in seen:continue
        seen.add(h);selected.append(dict(candidate_id=f'ga-optimized-{len(selected)+1:02}',source_run=source,sequence=d['best_sequence'],sequence_sha256=h,planning_loss_hr=value))
        if len(selected)==3:break
    assert len(selected)==3
    folder=OUT/'reused_evaluation';folder.mkdir(exist_ok=True);record=dict(rule='Three lowest full64 planning losses among distinct sequences after completed predeclared search phases; existing exploratory orders remain fixed comparators; no cohort metrics consulted',selected_before_reused_evaluation=True,selection_time_utc=pd.Timestamp.now(tz='UTC').isoformat(),cohort='Previously inspected 1000 saved 2pc50/C57_D1 realizations, exploratory reuse',formal_policy_replaced=False,candidates=selected)
    path=folder/'CANDIDATE_SELECTION.json'
    if path.exists():
        saved=json.loads(path.read_text());assert saved['candidates']==selected;return saved
    path.write_text(json.dumps(record,indent=2)+'\n');return record


def evaluation_one(cid):
    from la_grid.diagnostics import evaluate_extended_ga_20261008 as evaluator
    evaluator.OUT=OUT/'reused_evaluation';saved=json.loads((evaluator.OUT/'CANDIDATE_SELECTION.json').read_text());c=next(x for x in saved['candidates'] if x['candidate_id']==cid);evaluator.run(c,evaluator.load())


def evaluate():
    from la_grid.diagnostics import evaluate_extended_ga_20261008 as evaluator
    selected=select_candidates();evaluator.OUT=OUT/'reused_evaluation';inputs=evaluator.load()
    children=[]
    for candidate in selected['candidates']:
        f=(OUT/'local_logs'/f"evaluation_{candidate['candidate_id']}.log").open('w');proc=subprocess.Popen([sys.executable,'-u','-m','la_grid.diagnostics.ga_generalization_20261009','--evaluation-one',candidate['candidate_id']],stdout=f,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));children.append((proc,f))
    tick=time.monotonic()
    while any(p.poll() is None for p,f in children):
        if time.monotonic()-tick>45:print('EVALUATION PROGRESS',[(c['candidate_id'],len(list((evaluator.OUT/c['candidate_id']).glob('batch_*.json')))) for c in selected['candidates']],flush=True);tick=time.monotonic()
        time.sleep(3)
    for proc,f in children:f.close();assert proc.returncode==0,'Evaluation worker failed; inspect local log'
    for candidate in selected['candidates']:evaluator.run(candidate,inputs)
    formal=pd.concat([pd.read_parquet(R/'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet'),pd.read_parquet(R/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet')],ignore_index=True)
    formal=formal[formal.hazard.eq('2pc50')&formal.resource_scenario.eq('C57_D1')&formal.mapping.eq('M1_UTILITY_003')&formal.gate.eq('G1_BASELINE_050')]
    references={name:formal[formal.strategy_id.eq(name)].set_index('realization_id') for name in ['impact-first','hospital-first','degree-first','betweenness-first','vulnerability-first','random','unconstrained']}
    prior=R/'results/diagnostics/extended_ga_20261008/independent_evaluation'
    for cid in ['ga-exploratory-01','ga-exploratory-02']:references[cid]=pd.read_csv(prior/cid/'SUMMARY.csv').set_index('realization_id')
    effects=[];absolute=[];individual=[];execution=[]
    for candidate in selected['candidates']:
        cid=candidate['candidate_id'];q=pd.read_csv(evaluator.OUT/cid/'SUMMARY.csv').set_index('realization_id')
        for field,label in METRICS.items():
            v=q[field].dropna().to_numpy();ci=mean_ci(v);absolute.append(dict(candidate=cid,source_field=field,metric=label,n=len(v),mean=v.mean(),median=np.median(v),p05=np.quantile(v,.05),p95=np.quantile(v,.95),bootstrap_mean_ci95_low=ci[0],bootstrap_mean_ci95_high=ci[1]))
        for name,base in references.items():
            assert set(q.index)==set(base.index)
            for field,label in METRICS.items():
                v=(q[field]-base[field]).dropna().to_numpy();ci=mean_ci(v)
                effects.append(dict(candidate=cid,reference=name,source_field=field,metric=label,n=len(v),mean_change=v.mean(),median_change=np.median(v),p05=np.quantile(v,.05),p95=np.quantile(v,.95),bootstrap_mean_ci95_low=ci[0],bootstrap_mean_ci95_high=ci[1],bootstrap_replicates=10000,bootstrap_seed=641209,cohort='reused exploratory cohort'))
                individual.extend(dict(candidate=cid,reference=name,source_field=field,realization_id=j,change=float(x)) for j,x in (q[field]-base[field]).items())
        tasks=pd.read_csv(evaluator.OUT/cid/'TASK_EXECUTION.csv',dtype={'station_id':str});group=tasks.groupby('station_id').agg(damaged_realizations=('realization_id','size'),mean_dispatch_rank=('dispatch_rank','mean'),mean_completion_hr=('completion_hr','mean'),median_completion_hr=('completion_hr','median'),p05_completion_hr=('completion_hr',lambda x:x.quantile(.05)),p95_completion_hr=('completion_hr',lambda x:x.quantile(.95)),mean_travel_hr=('travel_hr','mean'));group['candidate']=cid;group['fixed_rank']=[candidate['sequence'].index(i)+1 for i in group.index];execution.append(group.reset_index())
    pd.DataFrame(absolute).to_csv(evaluator.OUT/'ABSOLUTE_OUTCOMES.csv',index=False);pd.DataFrame(effects).to_csv(evaluator.OUT/'OUTCOME_COMPARISONS.csv',index=False);pd.DataFrame(individual).to_csv(evaluator.OUT/'REALIZATION_DIFFERENCES.csv',index=False);pd.concat(execution).to_csv(evaluator.OUT/'STATION_EXECUTION.csv',index=False)
    print('REUSED COHORT EVALUATION COMPLETE',len(selected['candidates']),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--evaluation-one');p.add_argument('--cv-one',nargs=3,type=int);p.add_argument('--task',choices=['previous-pair','cv','stability','evaluate']);a=p.parse_args()
    if a.evaluation_one:return evaluation_one(a.evaluation_one)
    if a.cv_one:return cv_one(*a.cv_one)
    if a.task=='previous-pair':return previous_pair()
    if a.task=='cv':return cv_all()
    if a.task=='stability':return subset_stability()
    if a.task=='evaluate':return evaluate()
if __name__=='__main__':main()
