"""Fixed higher-budget parameter follow-up; never changes a formal GA method."""
from dataclasses import asdict,replace
from pathlib import Path
import argparse,gzip,hashlib,json,os,subprocess,sys,time
import numpy as np
from la_grid.paths import REPO_ROOT as ROOT
from la_grid.diagnostics.ga_variant_engine import Variant,run_search
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import load
from la_grid.diagnostics.ga_search_budget_sensitivity import identity,digest
OUT=ROOT/'results/diagnostics/ga_initialization_reconciliation_20261009'
BASE=Variant(population=100,crossover=.8,mutation=.1,tournament=3,elites=1,initialization='quality_mix',mutation_operator='swap')
CASES={'crossover060':{'crossover':.6},'crossover095':{'crossover':.95},'mutation005':{'mutation':.05},'mutation020':{'mutation':.2},'tournament2':{'tournament':2},'tournament5':{'tournament':5},'population50':{'population':50},'population250':{'population':250},'population500':{'population':500}}
SEEDS=list(range(100,120));BUDGET=100000

def dump(path,x):path.write_bytes((json.dumps(x,indent=2,allow_nan=False)+'\n').encode())
def _run_owned(case,seed):
 p=OUT/'parameter_100k'/f'{case}_s{seed}';p.mkdir(parents=True,exist_ok=True);target=p/'RUN.json'
 if target.exists():
  q=json.loads(target.read_text());assert q['status']=='COMPLETED' and q['distinct_evaluations']==BUDGET
  for name,h in q['files_sha256'].items():assert digest(p/name)==h
  print('REUSE_COMPLETE',case,seed,flush=True);return
 start=time.perf_counter();cpu=time.process_time();k,inc,quality=load();cfg=replace(BASE,**CASES[case]);moves=[];calls=0;seen=-np.inf;objective_cpu=0.
 def objective(seq):
  nonlocal calls,seen,objective_cpu
  t=time.process_time();v=k.score(seq);objective_cpu+=time.process_time()-t;calls+=1
  if v>seen:
   moves.append(dict(distinct_evaluation=calls,loss_hr=-v,improvement_hr=None if not np.isfinite(seen) else v-seen,sequence=list(seq),sequence_sha256=identity(seq)));seen=v
  return v
 search_start=time.perf_counter();result=run_search(items=k.ids,incumbents=inc,objective=objective,seed=seed,config=cfg,max_evaluations=BUDGET,checkpoints=(20000,50000,100000),folder=None,quality=quality);elapsed=time.perf_counter()-search_start
 state=result['state'];assert calls==len(result['cache'])==state['expensive_calls']==BUDGET
 history=result['history'];history.to_csv(p/'GENERATION_HISTORY.csv.gz',index=False,compression={'method':'gzip','mtime':0})
 dump(p/'STRICT_IMPROVEMENTS.json',moves);dump(p/'CHECKPOINTS.json',result['budget_rows'])
 first=history.iloc[0];n=max(1,cfg.population//4)
 q=dict(status='COMPLETED',case=case,seed=seed,config=asdict(cfg),budget=BUDGET,distinct_evaluations=len(result['cache']),total_attempts=state['attempts'],duplicate_calls=state['attempts']-len(result['cache']),actual_generation=state['generation'],fully_completed_generation=int(history.generation.max()),partial_generation=state['phase']=='evaluate',initial_best_loss_hr=float(first.population_best_service_loss_hr),final_best_loss_hr=-result['best_fitness'],postinitialization_gain_hr=float(first.population_best_service_loss_hr)+result['best_fitness'],best_sequence=list(result['best_sequence']),sequence_sha256=identity(result['best_sequence']),completed_archive_loss_hr=-result['archive_fitness'],initialization=dict(heuristics=7,warm_copies=1,neighbors=n,prior_neighbors=(n+1)//2,impact_neighbors=n//2,random=cfg.population-8-n,initial_unique=int(first.unique_population)),elapsed_wall_seconds=elapsed,job_wall_seconds=time.perf_counter()-start,process_cpu_seconds=time.process_time()-cpu,objective_cpu_seconds=objective_cpu,peak_rss_mb=state['peak_rss_bytes']/2**20,setup_validation_objective_calls=8,design_sha256=digest(OUT/'PARAMETER_FOLLOWUP_DESIGN.json'),input_identity_sha256=digest(ROOT/'results/diagnostics/ga_optimization_20261009/INPUT_IDENTITY.json'),engine_sha256=digest(ROOT/'src/la_grid/diagnostics/ga_variant_engine.py'),new_physical_samples=0,formal_candidate_replaced=False,files_sha256={x.name:digest(x) for x in p.iterdir() if x.name!='RUN.json'})
 dump(target,q);print('COMPLETE',case,seed,q['final_best_loss_hr'],q['elapsed_wall_seconds'],flush=True)

def run_one(case,seed):
 # Process claim prevents two coordinators from evaluating the same observation.
 # This does not consume GA random numbers or change search behavior.
 claims=OUT/'local_logs';claims.mkdir(exist_ok=True)
 lock=claims/f'{case}_s{seed}.lock'
 while True:
  try:
   fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd);break
  except FileExistsError:time.sleep(1)
 try:return _run_owned(case,seed)
 finally:lock.unlink()

def batch(workers,cases=None):
 selected=list(CASES) if cases is None else cases
 assert set(selected)<=set(CASES)
 jobs=[(c,s) for c in selected for s in SEEDS];pending=jobs.copy();active=[];start=time.perf_counter();logs=OUT/'local_logs';logs.mkdir(exist_ok=True);done=0;tick=0
 while pending or active:
  while pending and len(active)<workers:
   case,seed=pending.pop(0);f=(logs/f'{case}_s{seed}.log').open('w');env=dict(os.environ,PYTHONPATH=str(ROOT/'src'),OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
   p=subprocess.Popen([sys.executable,'-u','-m','la_grid.diagnostics.ga_parameter_confirmation_20261009','--one',case,str(seed)],cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));active.append((p,f,case,seed))
  for p,f,c,s in active.copy():
   if p.poll() is not None:
    f.close();assert p.returncode==0,(c,s);active.remove((p,f,c,s));done+=1
  if time.perf_counter()-tick>35:print('PROGRESS',done,len(jobs),'ACTIVE',len(active),'WALL',time.perf_counter()-start,flush=True);tick=time.perf_counter()
  time.sleep(1)
 dump(OUT/('PARAMETER_BATCH_COST.json' if cases is None else 'PARAMETER_COORDINATOR_'+selected[0]+'_'+str(workers)+'.json'),dict(completed_process_jobs=done,distinct_results_count=len(list((OUT/'parameter_100k').glob('*/RUN.json'))),job_cases=selected,budget_per_observation=BUDGET,query_count_requires_run_deduplication=True,batch_elapsed_wall_seconds=time.perf_counter()-start,workers=workers))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--one',nargs=2);p.add_argument('--workers',type=int,default=6);p.add_argument('--cases',nargs='+',choices=list(CASES));a=p.parse_args()
 if a.one:run_one(a.one[0],int(a.one[1]))
 else:batch(a.workers,a.cases)
