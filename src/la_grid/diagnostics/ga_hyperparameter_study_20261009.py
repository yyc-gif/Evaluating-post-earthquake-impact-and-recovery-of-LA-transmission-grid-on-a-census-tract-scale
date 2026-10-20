"""Staged, equal-distinct-evaluation GA study. Original authorities are read-only."""
from pathlib import Path
from dataclasses import asdict,replace
import argparse,json,time,subprocess,sys,os,random,hashlib
import numpy as np,pandas as pd
import psutil
from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.diagnostics.ga_variant_engine import Variant,run_search
OUT=R/'results/diagnostics/ga_optimization_20261009'
BASE='164f4564c0dabdeffdaf3870af000bbca725f71a'
PREVIOUS=R/'results/diagnostics/extended_ga_20261008/p100_g2000_s46/RUN.json'


def load():
    kernel,inc,identity=old.load_inputs();saved=json.loads(PREVIOUS.read_text());quality=tuple(saved['retained_sequence']);quality_loss=-kernel.score(quality);assert abs(quality_loss-33.03813174326729)<1e-9
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'INPUT_IDENTITY.json'
    record=dict(base_commit=BASE,original_inputs=identity,previous_best_sequence_sha256=old.identity(quality),previous_best_planning_loss_hr=quality_loss,physical_inputs_changed=False)
    if path.exists():assert json.loads(path.read_text())==record
    else:path.write_text(json.dumps(record,indent=2)+'\n')
    return kernel,inc,quality


def screen_design():
    cases={f'original_p{p}':Variant(population=p) for p in [50,100,250,500]}
    for p in [100,500]:
        for m in [.05,.1,.4,.6]:cases[f'p{p}_m{m:g}']=Variant(population=p,mutation=m)
        for k in [2,5]:cases[f'p{p}_k{k}']=Variant(population=p,tournament=k)
        for e in [1,3]:cases[f'p{p}_e{e}']=Variant(population=p,elites=e)
        for init in ['diverse','quality_mix']:cases[f'p{p}_{init}']=Variant(population=p,initialization=init)
    for c in [.6,.95]:
        for m in [.1,.4]:cases[f'p100_c{c:g}_m{m:g}']=Variant(crossover=c,mutation=m)
    assert len(cases)==28
    return cases


def definitions():
    path=OUT/'CONFIGURATIONS.json'
    if path.exists():return json.loads(path.read_text())
    return {}


def add_configs(cases):
    config=definitions()
    for key,value in cases.items():
        d=asdict(value)
        if key in config:assert config[key]==d
        config[key]=d
    (OUT/'CONFIGURATIONS.json').write_text(json.dumps(config,indent=2)+'\n')


def run_one(phase,cid,seed,budget):
    job_started=time.perf_counter();config=Variant(**definitions()[cid]);kernel,inc,quality=load();setup_seconds=time.perf_counter()-job_started;folder=OUT/phase/f'{cid}_s{seed}';folder.mkdir(parents=True,exist_ok=True);path=folder/'RUN.json'
    if path.exists():
        data=json.loads(path.read_text())
        if data['budget']>=budget and data['status']=='COMPLETE_BUDGET':
            for name,h in data['files_sha256'].items():assert old.digest(folder/name)==h
            return data
    result=run_search(items=kernel.ids,incumbents=inc,objective=kernel.score,seed=seed,config=config,max_evaluations=budget,folder=folder,quality=quality)
    state=result['state'];seq=result['best_sequence'];values=old.per_sample(kernel,seq);reference=old.per_sample(kernel,quality)
    pd.DataFrame({'planning_realization':np.arange(64),'service_loss_hr':values,'previous_best_service_loss_hr':reference,'difference_hr':values-reference}).to_csv(folder/'PLANNING_REALIZATIONS.csv',index=False)
    checkpoints=result['budget_rows'];rss=psutil.Process().memory_info();peak=max(state['peak_rss_bytes'],getattr(rss,'peak_wset',rss.rss))/2**20
    data=dict(status='COMPLETE_BUDGET' if len(result['cache'])==budget else 'ATTEMPT_CAP_REACHED',phase=phase,config_id=cid,config=asdict(config),seed=seed,budget=budget,distinct_evaluations=len(result['cache']),total_attempts=state['attempts'],actual_expensive_calls=state['expensive_calls'],generation=state['generation'],partial_generation=state['phase']=='evaluate',best_planning_loss_hr=-result['best_fitness'],original_completed_generation_archive_loss_hr=-result['archive_fitness'],improvement_vs_previous_hr=33.03813174326729+result['best_fitness'],improvement_vs_impact_hr=33.57830255999924+result['best_fitness'],elapsed_seconds=result['elapsed_seconds'],job_wall_seconds=time.perf_counter()-job_started,setup_seconds=setup_seconds,setup_validation_objective_calls=8,postsearch_full_sample_summaries=2,objective_seconds=state['score_seconds'],peak_rss_mb=peak,best_sequence=list(seq),sequence_sha256=old.identity(seq),original_archive_sequence=list(result['archive_sequence']),restart_count=state['restart_count'],kernel_input_identity_sha256=old.digest(OUT/'INPUT_IDENTITY.json'),engine_sha256=old.digest(R/'src/la_grid/diagnostics/ga_variant_engine.py'),formal_policy_replaced=False,parameter_or_operator_variant=asdict(config)!=asdict(Variant()),files_sha256={p.name:old.digest(p) for p in folder.iterdir() if p.suffix in ['.json','.csv','.npz'] and p.name!='RUN.json'})
    temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(data,indent=2)+'\n');temp.replace(path);print('COMPLETE',phase,cid,seed,budget,-result['best_fitness'],flush=True);return data


def worker(job_file):
    jobs=json.loads(Path(job_file).read_text())
    for phase,cid,seed,budget in jobs:
        p=subprocess.run([sys.executable,'-u','-m','la_grid.diagnostics.ga_hyperparameter_study_20261009','--one',phase,cid,str(seed),str(budget)],stdout=sys.stdout,stderr=sys.stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        assert p.returncode==0


def parallel(jobs,workers=8):
    logs=OUT/'local_logs';logs.mkdir(exist_ok=True);random.Random(90217).shuffle(jobs);buckets=[jobs[i::workers] for i in range(workers)];children=[]
    for i,bucket in enumerate(buckets):
        if not bucket:continue
        spec=logs/f'jobs_{i}.json';spec.write_text(json.dumps(bucket));log=(logs/f'worker_{i}.log').open('w',encoding='utf-8')
        env=dict(os.environ,PYTHONPATH=str(R/'src'),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
        p=subprocess.Popen([sys.executable,'-u','-m',__name__ if __name__!='__main__' else 'la_grid.diagnostics.ga_hyperparameter_study_20261009','--worker',str(spec)],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));children.append((p,log))
    tick=time.monotonic();done=-1
    while any(p.poll() is None for p,_ in children):
        count=sum(1 for phase,cid,seed,budget in jobs if (OUT/phase/f'{cid}_s{seed}'/'RUN.json').exists() and json.loads((OUT/phase/f'{cid}_s{seed}'/'RUN.json').read_text())['budget']>=budget)
        if count!=done or time.monotonic()-tick>45:print('PROGRESS',count,'/',len(jobs),flush=True);done=count;tick=time.monotonic()
        time.sleep(5)
    for p,f in children:f.close();assert p.returncode==0, 'Worker failed; inspect local_logs'
    print('STAGE COMPLETE',len(jobs),flush=True)


def parity():
    kernel,inc,quality=load();rows=[]
    schedule=[('original100',old.OUT,100,100),('original250',old.OUT,100,250),('extended100',R/'results/diagnostics/extended_ga_20261008',100,1000),('extended500',R/'results/diagnostics/extended_ga_20261008',500,1000)]
    for label,parent,p,g in schedule:
        for seed in range(42,47):
            source=parent/f'p{p}_g{g}_s{seed}';target=OUT/'original_behavior_replay'/f'{label}_s{seed}'
            if (target/'PARITY.json').exists():rows.append(json.loads((target/'PARITY.json').read_text()));continue
            with np.load(source/'CANDIDATES.npz') as z:cache={x.tobytes():float(v) for x,v in zip(z['orders'],z['fitness'])}
            result=run_search(items=kernel.ids,incumbents=inc,objective=kernel.score,seed=seed,config=Variant(population=p),max_evaluations=10**8,max_generations=g,folder=target,lookup_objective=cache)
            expect=pd.read_csv(source/'HISTORY.csv');cols=['generation_best','generation_mean','best_so_far'];error=float(np.max(np.abs(result['history'][cols].to_numpy()-expect[cols].to_numpy())));assert error<1e-9,error
            if label=='original100':
                formal=pd.read_csv(old.FORMAL/f'Stage 5 Output_expanded/GA_HISTORY_2pc50_{seed}.csv');assert np.max(np.abs(formal[cols].to_numpy()-result['history'][cols].to_numpy()))<1e-9
            assert result['state']['expensive_calls']==0,'Replay generated an unexpected candidate'
            saved=json.loads((source/'RUN.json').read_text())
            assert list(result['archive_sequence'])==saved['retained_sequence'],'Original archive sequence differs'
            record=dict(label=label,population=p,generations=g,seed=seed,history_max_abs_error=error,actual_expensive_calls=0,replay_cached_objectives=True,original_archive_sequence_exact_match=True,status='EXACT_BEHAVIOR_PARITY');(target/'PARITY.json').write_text(json.dumps(record,indent=2)+'\n');rows.append(record);print('PARITY',label,seed,error,flush=True)
    (OUT/'ORIGINAL_HISTORY_PARITY.json').write_text(json.dumps(rows,indent=2)+'\n')


def summarize():
    rows=[];budget=[];generation=[]
    for path in sorted(OUT.glob('*/*/RUN.json')):
        data=json.loads(path.read_text())
        if 'config' not in data:continue
        row={k:v for k,v in data.items() if not isinstance(v,(list,dict))};row.update(data['config']);rows.append(row)
        p=path.parent
        q=pd.read_csv(p/'BUDGET_CHECKPOINTS.csv');q['phase']=data['phase'];q['config_id']=data['config_id'];budget.append(q)
        q=pd.read_csv(p/'GENERATION_DIAGNOSTICS.csv');q['phase']=data['phase'];q['config_id']=data['config_id'];q['seed']=data['seed'];generation.append(q)
    d=pd.DataFrame(rows);d.to_csv(OUT/'GA_PARAMETER_SENSITIVITY.csv',index=False)
    if budget:pd.concat(budget,ignore_index=True).to_csv(OUT/'GA_COMPUTATIONAL_BUDGET_COMPARISON.csv',index=False)
    if generation:pd.concat(generation,ignore_index=True).to_csv(OUT/'GA_DIVERSITY_AND_SELECTION_DIAGNOSTICS.csv',index=False)
    return d


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker');parser.add_argument('--one',nargs=4);parser.add_argument('--stage',choices=['parity','screen','focused','shortlist','operators','summarize']);args=parser.parse_args()
    if args.one:return run_one(args.one[0],args.one[1],int(args.one[2]),int(args.one[3]))
    if args.worker:return worker(args.worker)
    if args.stage=='parity':return parity()
    load()
    if args.stage=='screen':
        cases=screen_design();add_configs(cases);parallel([('screen',cid,s,50000) for cid in cases for s in range(42,47)])
    elif args.stage=='focused':
        cases={
            'focused_p50_m01_e1':Variant(population=50,mutation=.1,elites=1),
            'focused_p100_m01_e1':Variant(mutation=.1,elites=1),
            'focused_p100_m005_e1':Variant(mutation=.05,elites=1),
            'focused_p100_c06_m01_e1':Variant(crossover=.6,mutation=.1,elites=1),
            'focused_p100_m01_k5_e1':Variant(mutation=.1,tournament=5,elites=1),
            'focused_p500_m01_k5_e1':Variant(population=500,mutation=.1,tournament=5,elites=1),
            'focused_p500_m01_k5_e3':Variant(population=500,mutation=.1,tournament=5,elites=3),
            'focused_p100_quality_m01_e1':Variant(mutation=.1,elites=1,initialization='quality_mix')}
        add_configs(cases);parallel([('focused',cid,s,50000) for cid in cases for s in range(42,47)])
    elif args.stage=='shortlist':
        data=summarize();screen=data[data.phase.isin(['screen','focused'])];ranks=screen.groupby('config_id').best_planning_loss_hr.agg(['mean','median','std']);config=definitions()
        legacy=[cid for cid in ranks.index if config[cid]['initialization']=='legacy'];best_legacy=ranks.loc[legacy].sort_values(['mean','std']).index[0];best_all=ranks.sort_values(['mean','std']).index[0]
        chosen=list(dict.fromkeys(['original_p100',best_legacy,best_all]));
        if len(chosen)<3:
            for cid in ranks.sort_values(['mean','std']).index:
                if cid not in chosen:chosen.append(cid)
                if len(chosen)==3:break
        selection=dict(rule='Lowest five-seed mean at identical 50,000 distinct evaluations, then standard deviation; baseline retained. No evaluation-cohort values consulted.',config_ids=chosen,shortlist_seed_count=20,seed_range=[42,61],budget=100000)
        (OUT/'SHORTLIST_SELECTION.json').write_text(json.dumps(selection,indent=2)+'\n');parallel([('shortlist',cid,s,100000) for cid in chosen for s in range(42,62)])
    elif args.stage=='operators':
        data=summarize();q=data[data.phase.eq('shortlist')];cid=q.groupby('config_id').best_planning_loss_hr.mean().sort_values().index[0];v=Variant(**definitions()[cid]);cases={}
        for op in ['inversion','swap','insertion','mixed']:cases['operator_'+op]=replace(v,mutation_operator=op)
        for op in ['cycle','pmx']:cases['operator_'+op]=replace(v,crossover_operator=op)
        cases['operator_adaptive']=replace(v,adaptive=True);cases['operator_restart']=replace(v,restart=True);cases['operator_crowding']=replace(v,diversity_replacement=True)
        add_configs(cases);(OUT/'OPERATOR_SELECTION.json').write_text(json.dumps({'planning_only_parent_configuration':cid,'variants':list(cases)},indent=2)+'\n');parallel([('operators',name,s,50000) for name in cases for s in range(42,47)],workers=16)
    summarize()
if __name__=='__main__':main()
