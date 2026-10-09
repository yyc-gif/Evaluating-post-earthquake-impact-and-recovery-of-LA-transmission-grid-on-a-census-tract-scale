"""Planning-only confirmations, budget extension and equal-budget hybrid runs."""
from dataclasses import replace,asdict
from pathlib import Path
import argparse,json,subprocess,sys,time,os,psutil
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load,summarize,definitions,add_configs,parallel
from la_grid.diagnostics.ga_variant_engine import Variant
from la_grid.diagnostics.ga_local_refinement_20261009 import refine
from la_grid.diagnostics import ga_search_budget_sensitivity as old


def confirmations():
    d=summarize();q=d[d.phase.eq('operators')];rank=q.groupby('config_id').best_planning_loss_hr.agg(['mean','std']).sort_values(['mean','std']);chosen=list(rank.index[:2]);selection=dict(rule='Two lowest five-seed means under equal 50,000 distinct budgets, standard deviation breaks ties; planning only',config_ids=chosen,seed_range=[42,61],budget=100000)
    (OUT/'OPERATOR_CONFIRMATION_SELECTION.json').write_text(json.dumps(selection,indent=2)+'\n');parallel([('operator_confirmation',cid,s,100000) for cid in chosen for s in range(42,62)],workers=16);summarize()


def budget_extension():
    d=summarize();q=d[d.phase.isin(['shortlist','operator_confirmation'])];rank=q.groupby('config_id').best_planning_loss_hr.agg(['mean','std']).sort_values(['mean','std']);chosen=list(dict.fromkeys(['original_p100',rank.index[0]]));record=dict(rule='Original baseline plus lowest 20-seed mean configuration at 100,000 distinct evaluations; planning only, bounded cost',config_ids=chosen,seed_range=[42,46],budget=500000,common_checkpoints=[50000,100000,250000,500000])
    (OUT/'BUDGET_EXTENSION_SELECTION.json').write_text(json.dumps(record,indent=2)+'\n');parallel([('budget_extension',cid,s,500000) for cid in chosen for s in range(42,47)],workers=10);summarize()


def hybrid_one(cid,seed):
    folder=OUT/'hybrid'/f'{cid}_s{seed}';folder.mkdir(parents=True,exist_ok=True)
    if (folder/'HYBRID_IDENTITY.json').exists():return
    source=OUT/'shortlist'/f'{cid}_s{seed}'
    checkpoint=pd.read_csv(source/'BUDGET_CHECKPOINTS.csv');prefix=checkpoint[checkpoint.distinct_evaluations.eq(50000)].iloc[0];sequence=json.loads(prefix.sequence.replace("'",'"'))
    with np.load(source/'CANDIDATES.npz') as z:
        keys=z['orders'][:50000];cache={k.tobytes():float(v) for k,v in zip(keys,z['fitness'][:50000])};assert len(cache)==50000
    kernel,inc,quality=load();started=time.perf_counter();result,cache=refine(kernel=kernel,start_sequence=sequence,budget=100000,folder=folder,initial_cache=cache,initial_used=50000)
    record=dict(config_id=cid,seed=seed,method='GA_50K_PLUS_LOCAL_50K',ga_prefix_source=str(source.relative_to(old.ROOT)),ga_prefix_distinct_evaluations=50000,ga_prefix_attempts=int(prefix.total_attempts),ga_prefix_elapsed_seconds=float(prefix.elapsed_seconds),ga_prefix_best_planning_loss_hr=float(prefix.best_service_loss_hr),joint_distinct_evaluations=len(cache),joint_total_attempts=int(prefix.total_attempts)+result['total_attempts'],joint_elapsed_seconds=float(prefix.elapsed_seconds)+result['elapsed_seconds'],shared_cache=True,peak_rss_mb=getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss)/2**20,local_attempts_count_excludes_ga_prefix=True,setup_and_reporting_outside_budget=True,formal_policy_replaced=False)
    result.update(method='GA_50K_PLUS_LOCAL_50K',seed=seed,config_id=cid,joint_distinct_evaluations=len(cache),joint_elapsed_seconds=record['joint_elapsed_seconds']);(folder/'RUN.json').write_text(json.dumps(result,indent=2)+'\n');(folder/'HYBRID_IDENTITY.json').write_text(json.dumps(record,indent=2)+'\n');print('HYBRID COMPLETE',seed,result['best_planning_loss_hr'],flush=True)


def hybrid():
    d=summarize();q=d[(d.phase.eq('shortlist')) & d.config_id.ne('original_p100')];cid=q.groupby('config_id').best_planning_loss_hr.mean().sort_values().index[0];pending=list(range(42,62));active=[]
    (OUT/'HYBRID_SELECTION.json').write_text(json.dumps({'planning_only_parent_configuration':cid,'seeds':[42,61],'joint_distinct_budget':100000,'split':'50,000 GA distinct queries + local refinement until joint cache reaches 100,000'},indent=2)+'\n')
    while pending or active:
        while pending and len(active)<8:
            seed=pending.pop(0);f=(OUT/'local_logs'/f'hybrid_{seed}.log').open('w');p=subprocess.Popen([sys.executable,'-u','-m','la_grid.diagnostics.ga_optimization_followup_20261009','--hybrid-one',cid,str(seed)],stdout=f,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));active.append((p,f))
        for p,f in active.copy():
            if p.poll() is not None:f.close();assert p.returncode==0;active.remove((p,f))
        time.sleep(3)


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['confirm','budgets','hybrid']);p.add_argument('--hybrid-one',nargs=2);a=p.parse_args()
    if a.hybrid_one:return hybrid_one(a.hybrid_one[0],int(a.hybrid_one[1]))
    if a.stage=='confirm':return confirmations()
    if a.stage=='budgets':return budget_extension()
    if a.stage=='hybrid':return hybrid()
if __name__=='__main__':main()
