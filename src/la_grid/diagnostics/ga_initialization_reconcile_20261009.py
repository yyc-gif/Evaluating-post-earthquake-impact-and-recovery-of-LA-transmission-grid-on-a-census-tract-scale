"""Reconcile immutable cloud GA evidence and estimate seed-level contrasts."""
from __future__ import annotations
import hashlib,json,subprocess,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from la_grid.paths import REPO_ROOT as ROOT
OUT=ROOT/'results/diagnostics/ga_initialization_reconciliation_20261009'
DIAG_BASE='9142b9994b34ff023edd47bf18b90d36a6743c69'
REVISION_BASE='031d2c675f8e7d58035d27448be040b809ced086'
BASELINE='baseline_7h_1w_25n'
CASES={
 BASELINE:(7,1,25,13),'heuristics_0':(0,1,25,13),'heuristics_1_impact':(1,1,25,13),
 'heuristics_3_top':(3,1,25,13),'heuristics_6_no_fixed_random':(6,1,25,13),
 'warm_copies_0':(7,0,25,13),'warm_copies_3':(7,3,25,13),'warm_copies_5':(7,5,25,13),
 'neighbors_0':(7,1,0,0),'neighbors_10':(7,1,10,5),'neighbors_50':(7,1,50,25),'neighbors_75':(7,1,75,38),
 'neighbors_25_prior_only':(7,1,25,25),'neighbors_25_impact_only':(7,1,25,0),
 'neighbors_25_prior_25pct':(7,1,25,6),'neighbors_25_prior_75pct':(7,1,25,19),'heuristics_only':(7,0,0,0)}
CONFIRM=(BASELINE,'heuristics_only','neighbors_0','neighbors_50','heuristics_0')

def sha(b):return hashlib.sha256(b).hexdigest()
def dump(name,value):(OUT/name).write_bytes((json.dumps(value,indent=2,allow_nan=False)+'\n').encode())
def csv(name,rows):pd.DataFrame(rows).to_csv(OUT/name,index=False)
def fromgit(path,ref=DIAG_BASE):return subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)

def reconcile():
 meta=json.loads((OUT/'CLOUD_ARTIFACT_MANIFEST.json').read_text());records={};dups=[];origins=[]
 assert len(meta)==50 and len({x['id'] for x in meta})==50
 for a in meta:
  b=(ROOT/a['local_archive']).read_bytes();assert sha(b)==a['zip_sha256']==a['digest'].split(':')[1]
  z=zipfile.ZipFile(ROOT/a['local_archive']);q=json.loads(z.read(a['all_cases'][0]));budget=q['budget'];seed=q['seed'];expected=set(CASES if budget==20000 else CONFIRM)
  assert q['status']=='COMPLETED' and not q['physical_sampling'] and not q['formal_policy_replaced']
  assert {x['case'] for x in q['cases']}==expected and len(q['cases'])==len(expected)
  for x in q['cases']:
   key=(budget,seed,x['case']);assert key not in records
   assert x['seed']==seed and x['final_best_loss_hr']<=x['initial_best_loss_hr']+1e-10
   h,w,n,prior=CASES[x['case']]
   assert (x['heuristic_count'],x['warm_copy_count'],x['neighbor_count'],x['prior_neighbor_count'])==(h,w,n,prior)
   assert x['random_count']==100-h-w-n and x['actual_unique_chromosomes']+x['actual_duplicate_chromosomes']==100
   name=next(t for t in z.namelist() if t.endswith('/'+x['case']+'.json'));assert json.loads(z.read(name))==x
   records[key]=x;origins.append(dict(budget=budget,seed=seed,case=x['case'],artifact_id=a['id'],run_id=a['run_id'],head_sha=a['head_sha'],member=a['all_cases'][0],json_sha256=sha(json.dumps(x,sort_keys=True,separators=(',',':')).encode())))
   dups.append(dict(budget=budget,seed=seed,case=x['case'],representation='per-case member duplicates ALL_CASES member',source=a['local_archive']+'!'+name))
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',DIAG_BASE,'results/diagnostics/ga_initialization_replication_20261009/raw_chunks','results/diagnostics/ga_initialization_100k_confirmation_20261009/raw_chunks'],cwd=ROOT,text=True).splitlines()
 for p in paths:
  q=json.loads(fromgit(p))
  for x in q['records']:
   budget=x.get('budget',x.get('distinct_evaluation_budget'));key=(budget,x['seed'],x['case']);assert records[key]==x,(p,key)
   dups.append(dict(budget=budget,seed=x['seed'],case=x['case'],representation='committed partial chunk duplicates cloud observation',source=p,source_commit=DIAG_BASE))
 expected={(20000,s,c) for s in range(100,130) for c in CASES}|{(100000,s,c) for s in range(100,120) for c in CONFIRM}
 assert set(records)==expected
 prefix=[]
 for seed in range(100,120):
  for case in CONFIRM:
   a=records[(20000,seed,case)];b=records[(100000,seed,case)];checkpoint={x['evaluations']:x['loss_hr'] for x in b['checkpoints']}
   assert a['initial_population_sha256']==b['initial_population_sha256'];assert abs(a['initial_best_loss_hr']-b['initial_best_loss_hr'])<1e-10;assert abs(checkpoint[20000]-a['final_best_loss_hr'])<1e-10
   prefix.append(dict(case=case,seed=seed,initial_population_hash_equal=True,initial_best_exact_equal=a['initial_best_loss_hr']==b['initial_best_loss_hr'],initial_best_error_hr=b['initial_best_loss_hr']-a['initial_best_loss_hr'],loss_20k_exact_equal=checkpoint[20000]==a['final_best_loss_hr'],loss_20k_error_hr=checkpoint[20000]-a['final_best_loss_hr'],objective_parity_tolerance_hr=1e-10,within_parity_tolerance=True,loss_20k=checkpoint[20000],loss_50k=checkpoint[50000],loss_100k=checkpoint[100000],prefix_is_independent_observation=False))
 rows=[]
 for (budget,seed,case),x in records.items():
  row={k:v for k,v in x.items() if k!='checkpoints'};row.update(budget=budget,seed=seed,case=case);rows.append(row)
 d=pd.DataFrame(rows).sort_values(['budget','case','seed']);csv('UNIQUE_INITIALIZATION_OBSERVATIONS.csv',d);csv('DUPLICATE_REPRESENTATION_AUDIT.csv',dups);csv('OBSERVATION_SOURCE_INDEX.csv',origins);csv('MATCHED_20K_CHECKPOINT_AUDIT.csv',prefix)
 checkpoints=[]
 for (budget,seed,case),x in records.items():
  points=x.get('checkpoints',[{'evaluations':20000,'loss_hr':x['final_best_loss_hr']}])
  for p in points:
   # The common 20k prefix is already represented by the 30-seed study.
   if budget==100000 and p['evaluations']==20000:continue
   checkpoints.append(dict(case=case,seed=seed,budget=p['evaluations'],loss_hr=p['loss_hr']))
 csv('UNIQUE_BUDGET_CHECKPOINTS.csv',checkpoints)
 counts=dict(artifact_count=50,sha_verified_archives=50,unique_final_run_observations=len(records),replication_20k_runs=510,confirmation_100k_runs=100,removed_duplicate_representations=len(dups),duplicates_in_individual_json_members=610,committed_chunk_duplicates=len(dups)-610,matched_20k_prefixes=100,max_absolute_prefix_error_hr=max(abs(x['loss_20k_error_hr']) for x in prefix),exact_prefix_matches=sum(x['loss_20k_exact_equal'] for x in prefix),objective_parity_tolerance_hr=1e-10,independent_seed_counts={'20000':30,'100000':20},overlapping_seed_count=20,not_50_independent_seeds=True,nominal_actual_distinct_calls=20200000,prefix_replay_calls=2000000,unique_per_run_checkpoint_paths_no_replay=18200000,globally_unique_physical_inputs=False,completed_batches_rerun=False)
 dump('RECONCILIATION_AUDIT.json',counts)
 return d,pd.DataFrame(checkpoints),counts

def estimate(values,seed=2026100902,tests=1):
 x=np.asarray(values,dtype=float);n=len(x);mean=x.mean();sd=x.std(ddof=1);se=sd/np.sqrt(n);t=stats.t.ppf(.975,n-1);family=stats.t.ppf(1-.025/tests,n-1)
 boot=np.random.default_rng(seed).choice(x,size=(50000,n),replace=True).mean(axis=1);lo,hi=np.quantile(boot,[.025,.975])
 return dict(n_seeds=n,mean_change_hr=mean,median_change_hr=float(np.median(x)),paired_sd_hr=sd,seed_mcse_hr=se,t95_low_hr=mean-t*se,t95_high_hr=mean+t*se,bootstrap95_low_hr=lo,bootstrap95_high_hr=hi,bonferroni95_low_hr=mean-family*se,bonferroni95_high_hr=mean+family*se,win_fraction=float((x<0).mean()),exact_tie_fraction=float((x==0).mean()),p_t_two_sided=float(stats.ttest_1samp(x,0).pvalue) if sd else 1.,bootstrap_unit='GA seed; fixed 64 physical samples')

def analyze(d,checkpoints):
 contrasts=[];raw=[]
 for budget,z in d.groupby('budget'):
  base=z[z.case.eq(BASELINE)].set_index('seed');m=z.case.nunique()-1
  for case,a in z.groupby('case'):
   if case==BASELINE:continue
   a=a.set_index('seed');v=a.final_best_loss_hr-base.final_best_loss_hr;result=estimate(v,tests=m)
   contrasts.append(dict(case=case,budget=budget,mean_initial_change_hr=(a.initial_best_loss_hr-base.initial_best_loss_hr).mean(),mean_evolution_gain_change_hr=(a.postinitialization_gain_hr-base.postinitialization_gain_hr).mean(),**result))
   for seed,x in v.items():raw.append(dict(case=case,budget=budget,seed=seed,final_change_hr=x,initial_change_hr=a.loc[seed,'initial_best_loss_hr']-base.loc[seed,'initial_best_loss_hr'],evolution_gain_change_hr=a.loc[seed,'postinitialization_gain_hr']-base.loc[seed,'postinitialization_gain_hr']))
 c=pd.DataFrame(contrasts);csv('PAIRED_INITIALIZATION_EFFECTS.csv',c);csv('PAIRED_SEED_EFFECTS.csv',raw)
 summary=d.groupby(['budget','case']).agg(seeds=('seed','size'),initial_mean_hr=('initial_best_loss_hr','mean'),evolution_gain_mean_hr=('postinitialization_gain_hr','mean'),final_mean_hr=('final_best_loss_hr','mean'),final_sd_hr=('final_best_loss_hr','std'),final_median_hr=('final_best_loss_hr','median'),best_hr=('final_best_loss_hr','min'),worst_hr=('final_best_loss_hr','max'),mean_wall_seconds=('elapsed_wall_seconds','mean')).reset_index();csv('INITIALIZATION_SUMMARY.csv',summary)
 budgetrows=[]
 for case in CONFIRM:
  b=checkpoints[checkpoints.case.eq(case)&checkpoints.seed.lt(120)].pivot(index='seed',columns='budget',values='loss_hr')
  baseline=checkpoints[checkpoints.case.eq(BASELINE)&checkpoints.seed.lt(120)].pivot(index='seed',columns='budget',values='loss_hr')
  for level in [20000,50000,100000]:
   delta=b[level]-baseline[level]
   budgetrows.append(dict(case=case,budget=level,mean_loss_hr=b[level].mean(),median_loss_hr=b[level].median(),sd_loss_hr=b[level].std(),**estimate(delta,tests=4)))
  if case!=BASELINE:budgetrows.append(dict(case=case,budget='contrast_change_100k_minus_20k',**estimate((b[100000]-baseline[100000])-(b[20000]-baseline[20000]),tests=4)))
 csv('SAME_20_SEED_BUDGET_STABILITY.csv',budgetrows)
 precision=[]
 for _,x in c.iterrows():
  for tolerance in [.0005,.001,.002,.005,.01]:
   precision.append(dict(case=x.case,budget=x.budget,n_seeds=x.n_seeds,tolerance_hr=tolerance,pointwise_ci_wholly_inside_tolerance=bool(x.t95_low_hr>-tolerance and x.t95_high_hr<tolerance),family_ci_wholly_inside_tolerance=bool(x.bonferroni95_low_hr>-tolerance and x.bonferroni95_high_hr<tolerance),prospectively_approved_practical_tolerance=False,equivalence_established=False))
 csv('PRACTICAL_TOLERANCE_PRECISION.csv',precision)
 dump('STATISTICAL_RULES.json',dict(paired_unit='Complete GA random seed',bootstrap_replicates=50000,bootstrap_seed=2026100902,pointwise_ci='95% paired-seed percentile bootstrap plus paired t interval',multiplicity='Bonferroni t intervals:16 initialization contrasts at20k,4 at100k/50k; no equivalence claim from nonsignificance',scientifically_approved_negligibility_tolerance=None,tolerance_grid_hr=[.0005,.001,.002,.005,.01],budget_repeated_measure_not_independent=True,no_physical_generalization=True))
 return c,summary

def main():
 d,b,a=reconcile();c,s=analyze(d,b);print(json.dumps(a,indent=2));print(c[['budget','case','mean_change_hr','t95_low_hr','t95_high_hr']].to_string(index=False))
if __name__=='__main__':main()
