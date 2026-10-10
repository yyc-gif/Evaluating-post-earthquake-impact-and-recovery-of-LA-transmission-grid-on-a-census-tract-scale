"""Replay saved local objective caches to audit cloud-control comparability."""
import json,subprocess
import numpy as np
import pandas as pd
from la_grid.diagnostics.ga_variant_engine import Variant,run_search
from la_grid.diagnostics.ga_initialization_reconcile_20261009 import ROOT,OUT,DIAG_BASE,csv,dump
from la_grid.diagnostics.ga_search_budget_sensitivity import identity,digest
def main():
 config=json.loads((ROOT/'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json').read_text())
 formal=json.loads((ROOT/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']
 inc={k:tuple(formal[k]) for k in config['initialization']['deterministic_order']}
 quality=tuple(config['initialization']['prior_best_sequence']);rows=[]
 cloud=json.loads(subprocess.check_output(['git','show',DIAG_BASE+':results/diagnostics/ga_parameter_followup_20261009/SCREENING_DATA.json'],cwd=ROOT))['records']
 cloud={x['seed']:x for x in cloud if x['phase']=='parameters' and x['case']=='baseline'}
 v=Variant(population=100,crossover=.8,mutation=.1,tournament=3,elites=1,initialization='quality_mix',mutation_operator='swap')
 def forbidden(seq):raise AssertionError('No new objective evaluation permitted in cached parity audit')
 for seed in range(42,47):
  source=ROOT/f'results/diagnostics/ga_optimization_20261009/operator_confirmation/operator_swap_s{seed}'
  run=json.loads((source/'RUN.json').read_text());assert run['config']==v.__dict__
  assert digest(source/'CANDIDATES.npz')==run['files_sha256']['CANDIDATES.npz']
  with np.load(source/'CANDIDATES.npz') as z:
   ids=tuple(z['station_ids'].astype(str));cache={x.tobytes():float(f) for x,f in zip(z['orders'],z['fitness'])}
  result=run_search(items=ids,incumbents=inc,objective=forbidden,seed=seed,config=v,max_evaluations=20000,checkpoints=(20000,),quality=quality,folder=None,lookup_objective=cache)
  q=cloud[seed];error=-result['best_fitness']-q['final_best_loss_hr'];same=identity(result['best_sequence'])==q['sequence_sha256']
  row=dict(seed=seed,cloud_20k_loss_hr=q['final_best_loss_hr'],local_saved_20k_loss_hr=-result['best_fitness'],error_hr=error,within_numeric_tolerance=abs(error)<1e-10,exact_best_sequence_identity=same,cloud_sequence_sha256=q['sequence_sha256'],local_sequence_sha256=identity(result['best_sequence']),new_objective_evaluations=result['state']['expensive_calls'],lookup_queries=result['state']['lookup_calls'],source_cache=str((source/'CANDIDATES.npz').relative_to(ROOT)),source_cache_sha256=digest(source/'CANDIDATES.npz'))
  assert row['new_objective_evaluations']==0
  rows.append(row);print('CACHED_PARITY',seed,error,same,flush=True)
 csv('CLOUD_LOCAL_CACHED_SEARCH_PARITY.csv',rows)
 dump('CLOUD_LOCAL_CACHED_SEARCH_PARITY.json',dict(replayed_seed_count=5,new_objective_evaluations=0,all_loss_parity=all(x['within_numeric_tolerance'] for x in rows),all_sequence_parity=all(x['exact_best_sequence_identity'] for x in rows),scope='Saved local 100k cache replay to20k versus completed cloud five-seed screen; no completed objective batch rerun',not_exact_local_replay_of_cloud_seeds_100_119=True))

if __name__=='__main__':main()
