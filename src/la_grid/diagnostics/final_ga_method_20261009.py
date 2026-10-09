"""Bounded final-method attribution and documentation; no new physical samples."""
from pathlib import Path
from dataclasses import asdict
import argparse, hashlib, json, os, random, subprocess, sys, time
import numpy as np
import pandas as pd
from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics.ga_variant_engine import Variant, run_search, initialize
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import load, OUT as PRIOR
from la_grid.diagnostics import ga_search_budget_sensitivity as old
OUT=R/'results/diagnostics/final_ga_method_20261009'
BASE='73ef343f21e998eb9c9ccf7797d1aa0119d15c04'
SEEDS=list(range(42,47))
CONTROLLED={
 'C_quality_elite_inversion_m02':Variant(initialization='quality_mix',elites=1),
 'D_quality_elite_swap_m02':Variant(initialization='quality_mix',elites=1,mutation_operator='swap')}

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes((json.dumps(value,indent=2,allow_nan=False)+'\n').encode('utf-8'))

def run_one(cid,seed):
    folder=OUT/'controlled_comparisons'/f'{cid}_s{seed}'
    if (folder/'RUN.json').exists():
        q=json.loads((folder/'RUN.json').read_text())
        for name,h in q['files_sha256'].items():assert old.digest(folder/name)==h
        return
    started=time.perf_counter();cpu=time.process_time();k,inc,quality=load()
    config=CONTROLLED[cid];objective_cpu=0.
    def score(seq):
        nonlocal objective_cpu
        t=time.process_time();v=k.score(seq);objective_cpu+=time.process_time()-t;return v
    result=run_search(items=k.ids,incumbents=inc,objective=score,seed=seed,config=config,
        max_evaluations=50000,checkpoints=(50000,),folder=folder,quality=quality)
    st=result['state'];assert len(result['cache'])==50000
    for path in folder.glob('*.json'):
        path.write_bytes(path.read_bytes().replace(b'\r\n',b'\n'))
    data=dict(status='COMPLETE_BUDGET',config_id=cid,config=asdict(config),seed=seed,
        distinct_evaluations=len(result['cache']),actual_expensive_calls=st['expensive_calls'],
        total_attempts=st['attempts'],generation=st['generation'],partial_generation=st['phase']=='evaluate',
        best_planning_loss_hr=-result['best_fitness'],best_sequence=list(result['best_sequence']),
        sequence_sha256=old.identity(result['best_sequence']),elapsed_seconds=result['elapsed_seconds'],
        job_wall_seconds=time.perf_counter()-started,process_cpu_seconds=time.process_time()-cpu,
        objective_cpu_seconds=objective_cpu,peak_rss_mb=st['peak_rss_bytes']/2**20,
        engine_sha256=old.digest(R/'src/la_grid/diagnostics/ga_variant_engine.py'),
        input_identity_sha256=old.digest(PRIOR/'INPUT_IDENTITY.json'),formal_policy_replaced=False,
        new_physical_sampling=False,setup_validation_objective_calls=8,search_budget_excludes_setup_validation=True,files_sha256={p.name:old.digest(p) for p in folder.iterdir()
        if p.suffix in ['.json','.csv','.npz']})
    dump(folder/'RUN.json',data)
    print('CONTROLLED_COMPLETE',cid,seed,data['best_planning_loss_hr'],flush=True)

def controlled():
    OUT.mkdir(exist_ok=True);jobs=[(c,s) for c in CONTROLLED for s in SEEDS]
    dump(OUT/'CONTROLLED_COMPARISON_DESIGN.json',dict(base_commit=BASE,seeds=SEEDS,
        budget_per_seed=50000,missing_runs=len(jobs),maximum_new_queries=500000,
        configurations={c:asdict(v) for c,v in CONTROLLED.items()},
        rationale='Two missing steps isolate elitism at original mutation0.20, then swap at unchanged0.20; final0.10 comparison is a separate saved bridge.',
        prior_cost_pilot_seconds_per_query=.000856,estimated_serial_objective_seconds=428,
        workers=5,formal_results_changed=False))
    pending=list(jobs);active=[];start=time.perf_counter();last=0
    (OUT/'logs').mkdir(exist_ok=True)
    while pending or active:
        while pending and len(active)<5:
            cid,s=pending.pop(0);log=(OUT/'logs'/f'{cid}_s{s}.log').open('w')
            env=dict(os.environ,PYTHONPATH=str(R/'src'),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
            p=subprocess.Popen([sys.executable,'-u','-m','la_grid.diagnostics.final_ga_method_20261009','--one',cid,str(s)],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));active.append((p,log,cid,s))
        for p,f,cid,s in active.copy():
            if p.poll() is not None:
                f.close();assert p.returncode==0,(cid,s);active.remove((p,f,cid,s));print('FINISHED',cid,s,flush=True)
        if time.perf_counter()-last>35:
            print('PROGRESS',len(jobs)-len(pending)-len(active),'/',len(jobs),flush=True);last=time.perf_counter()
        time.sleep(2)
    dump(OUT/'CONTROLLED_BATCH_COST.json',dict(wall_seconds=time.perf_counter()-start,
        completed_runs=len(jobs),new_distinct_queries=500000,workers=5))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--one',nargs=2);a=p.parse_args()
    if a.one:run_one(a.one[0],int(a.one[1]))
    else:controlled()
