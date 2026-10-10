"""Integrity and inference gates for cloud reconciliation and bounded GA tests."""
from pathlib import Path
import hashlib,json,zipfile
import numpy as np
import pandas as pd
from la_grid.paths import REPO_ROOT as ROOT
from la_grid.diagnostics.ga_initialization_reconcile_20261009 import OUT,BASELINE,CASES,CONFIRM,estimate
from la_grid.diagnostics.ga_parameter_confirmation_20261009 import CASES as PARAMETERS,SEEDS,BUDGET

def read(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def test_immutable_cloud_archives_match_remote_digest_and_expected_members():
 manifest=read('CLOUD_ARTIFACT_MANIFEST.json')
 assert len(manifest)==50 and len({a['id'] for a in manifest})==50
 for a in manifest:
  path=ROOT/a['local_archive']
  assert sha(path)==a['zip_sha256']==a['digest'].split(':')[1]
  with zipfile.ZipFile(path) as z:
   allcases=json.loads(z.read(a['all_cases'][0]))
   expected=17 if allcases['budget']==20000 else 5
   assert len(z.namelist())==expected+1
   assert len(allcases['cases'])==expected and allcases['status']=='COMPLETED'
   assert not allcases['physical_sampling'] and not allcases['formal_policy_replaced']
   for case in allcases['cases']:
    member=next(name for name in z.namelist() if name.endswith('/'+case['case']+'.json'))
    assert json.loads(z.read(member))==case

def test_complete_case_seed_grid_and_no_fifty_seed_pseudoreplication():
 d=pd.read_csv(OUT/'UNIQUE_INITIALIZATION_OBSERVATIONS.csv');a=read('RECONCILIATION_AUDIT.json')
 keys=set(zip(d.budget,d.seed,d.case))
 expected={(20000,s,c) for s in range(100,130) for c in CASES}|{(100000,s,c) for s in range(100,120) for c in CONFIRM}
 assert keys==expected and len(d)==len(keys)==610
 assert a['removed_duplicate_representations']==1153
 assert a['committed_chunk_duplicates']==543 and a['duplicates_in_individual_json_members']==610
 assert d.seed.nunique()==30 and set(d[d.budget.eq(100000)].seed)<=set(d[d.budget.eq(20000)].seed)
 assert a['not_50_independent_seeds'] and not a['completed_batches_rerun']
 assert a['nominal_actual_distinct_calls']==20200000
 assert a['nominal_actual_distinct_calls']-a['prefix_replay_calls']==a['unique_per_run_checkpoint_paths_no_replay']==18200000


def test_same_seed_prefixes_are_numerically_equal_without_false_bitwise_claim():
 p=pd.read_csv(OUT/'MATCHED_20K_CHECKPOINT_AUDIT.csv')
 assert len(p)==100 and p.initial_population_hash_equal.all()
 assert p.loss_20k_exact_equal.sum()==90
 assert p.loss_20k_error_hr.abs().max()<=1e-10
 assert p.within_parity_tolerance.all() and not p.prefix_is_independent_observation.any()
 assert np.all(p.loss_100k<=p.loss_50k+1e-10) and np.all(p.loss_50k<=p.loss_20k+1e-10)
 q=pd.read_csv(OUT/'UNIQUE_BUDGET_CHECKPOINTS.csv')
 assert not q.duplicated(['case','seed','budget']).any()


def test_initialization_components_and_incomplete_ablation_controls_are_explicit():
 c=pd.read_csv(OUT/'INITIALIZATION_ALLOCATION_AUDIT.csv').set_index('case')
 assert (c.heuristics+c.exact_prior_copies+c.inversion_neighbors+c.random_permutations).eq(100).all()
 assert (c.prior_derived_neighbors+c.impact_derived_neighbors).eq(c.inversion_neighbors).all()
 assert c.loc['heuristics_0','heuristics']==0 and c.loc['heuristics_0','impact_derived_neighbors']==12
 assert c.loc['warm_copies_0','exact_prior_copies']==0 and c.loc['warm_copies_0','prior_derived_neighbors']==13
 assert c.loc['heuristics_only','exact_prior_copies']==c.loc['heuristics_only','inversion_neighbors']==0
 text=(OUT/'INITIALIZATION_EVIDENCE_AND_LIMITATIONS.md').read_text()
 assert 'not removal of heuristic information' in text and 'not removal of all inherited GA information' in text
 assert 'not a clean isolated estimate' in text


def test_paired_effects_conserve_initial_and_postinitialization_contributions():
 c=pd.read_csv(OUT/'PAIRED_INITIALIZATION_EFFECTS.csv')
 np.testing.assert_allclose(c.mean_initial_change_hr-c.mean_evolution_gain_change_hr,c.mean_change_hr,atol=1e-12)
 d=pd.read_csv(OUT/'PAIRED_SEED_EFFECTS.csv')
 np.testing.assert_allclose(d.initial_change_hr-d.evolution_gain_change_hr,d.final_change_hr,atol=1e-12)
 for _,row in c.iterrows():
  values=d[(d.case==row.case)&(d.budget==row.budget)].final_change_hr
  q=estimate(values,tests=16 if row.budget==20000 else 4)
  assert abs(q['mean_change_hr']-row.mean_change_hr)<1e-12
  assert abs(q['t95_low_hr']-row.t95_low_hr)<1e-12
  assert row.bonferroni95_low_hr<=row.t95_low_hr<=row.t95_high_hr<=row.bonferroni95_high_hr
 precision=pd.read_csv(OUT/'PRACTICAL_TOLERANCE_PRECISION.csv')
 assert not precision.equivalence_established.any() and not precision.prospectively_approved_practical_tolerance.any()
 assert read('STATISTICAL_RULES.json')['scientifically_approved_negligibility_tolerance'] is None


def test_followup_was_bounded_and_count_scaling_is_not_pure_population_effect():
 p=read('PARAMETER_FOLLOWUP_DESIGN.json')
 assert p['seed_set']==SEEDS and p['distinct_budget_per_run']==BUDGET and len(PARAMETERS)==9
 assert p['new_runs']==180 and p['new_distinct_query_ceiling']==18000000
 assert not p['precision_target_is_negligibility_tolerance'] and p['variance_estimate_is_uncertain']
 for q in p['population_scaling']:
  assert q['neighbors']==q['population']//4
  assert q['heuristics']==7 and q['warm']==q['elite']==1
  assert q['random']==q['population']-8-q['neighbors']
  assert q['prior_neighbors']+q['impact_neighbors']==q['neighbors']
 assert 'not a pure population effect' in p['population_effect_scope']
 parity=pd.read_csv(OUT/'REUSED_BASELINE_INITIALIZER_PARITY.csv')
 assert len(parity)==20 and parity.exact_equal.all() and parity.expensive_search_queries.eq(0).all()
 assert read('REUSED_CONTROL_SOURCE_PARITY.json')['baseline_queries_rerun']==0


def test_previous_screening_shared_baseline_is_not_duplicated_as_evidence():
 d=pd.read_csv(OUT/'PREVIOUS_SCREENING_UNIQUE_OBSERVATIONS.csv')
 dup=pd.read_csv(OUT/'PREVIOUS_SCREENING_DUPLICATES.csv')
 assert len(d)==85 and len(dup)==5
 assert not d.assign(case=d.case.where(d.case.ne('baseline'),'shared_baseline')).duplicated(['case','seed']).any()


def test_completed_parameter_followup_is_exact_fixed_budget_and_verifiable():
 paths=list((OUT/'parameter_100k').glob('*/RUN.json'))
 assert len(paths)==180
 keys=set()
 for path in paths:
  q=json.loads(path.read_text());keys.add((q['case'],q['seed']))
  assert q['status']=='COMPLETED' and q['distinct_evaluations']==q['budget']==100000
  from dataclasses import asdict
  from la_grid.diagnostics.ga_parameter_confirmation_20261009 import BASE
  expected=asdict(BASE);expected.update(PARAMETERS[q['case']]);assert q['config']==expected
  assert q['design_sha256']==sha(OUT/'PARAMETER_FOLLOWUP_DESIGN.json')
  assert q['total_attempts']-q['duplicate_calls']==q['distinct_evaluations']
  assert q['fully_completed_generation']<=q['actual_generation']
  assert q['new_physical_samples']==0 and not q['formal_candidate_replaced']
  assert len(q['best_sequence'])==len(set(q['best_sequence']))==92
  original=json.loads((ROOT/'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json').read_text())
  assert set(q['best_sequence'])==set(original['chromosome']['station_ids'])
  identity=hashlib.sha256(('\n'.join(q['best_sequence'])+'\n').encode()).hexdigest()
  assert identity==q['sequence_sha256']
  for name,h in q['files_sha256'].items():assert sha(path.parent/name)==h
  cp=json.loads((path.parent/'CHECKPOINTS.json').read_text())
  assert [x['distinct_evaluations'] for x in cp]==[20000,50000,100000]
  assert all(x['actual_expensive_calls']==x['distinct_evaluations'] for x in cp)
  assert cp[-1]['sequence_sha256']==q['sequence_sha256'] and abs(cp[-1]['best_service_loss_hr']-q['final_best_loss_hr'])<1e-12
  assert all(cp[i+1]['best_service_loss_hr']<=cp[i]['best_service_loss_hr']+1e-12 for i in range(2))
 assert keys=={(c,s) for c in PARAMETERS for s in SEEDS}


def test_scientific_authorities_match_this_round_preservation_baseline():
 p=read('PRESERVATION_BASELINE.json')
 assert len(p['files_sha256'])==834
 for name,h in p['files_sha256'].items():assert sha(ROOT/name)==h,name


def test_cached_platform_controls_replay_existing_scores_without_new_queries():
 q=read('CLOUD_LOCAL_CACHED_SEARCH_PARITY.json')
 assert q['replayed_seed_count']==5 and q['new_objective_evaluations']==0
 assert q['all_loss_parity'] and q['all_sequence_parity']
 p=pd.read_csv(OUT/'CLOUD_LOCAL_CACHED_SEARCH_PARITY.csv')
 assert set(p.seed)==set(range(42,47))
 assert p.new_objective_evaluations.eq(0).all() and p.exact_best_sequence_identity.all()
 assert p.error_hr.abs().max()<1e-10
 for _,r in p.iterrows():assert sha(ROOT/r.source_cache)==r.source_cache_sha256
