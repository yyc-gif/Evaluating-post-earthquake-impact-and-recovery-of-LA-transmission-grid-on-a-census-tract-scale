"""Consistency checks for the diagnostic method freeze, not scientific reruns."""
from pathlib import Path
import hashlib
import json
import random
import numpy as np
import pandas as pd
from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_variant_engine import Variant, initialize

OUT=REPO_ROOT/'results/diagnostics/final_ga_method_20261009'

def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def identity(seq):
    return hashlib.sha256(('\n'.join(seq)+'\n').encode('utf-8')).hexdigest()

def test_freeze_receipt_pins_method_sequence_and_validation_before_sampling():
    receipt=read('FREEZE_RECEIPT.json')
    assert receipt['new_physical_samples']==0 and not receipt['formal_promotion']
    for name,expected in receipt['files_sha256'].items():
        assert sha(OUT/name)==expected, name
    config=read('FINAL_GA_CONFIG_CANDIDATE.json')
    selected=read('SELECTED_SEQUENCE.json')
    protocol=read('FINAL_VALIDATION_PROTOCOL.json')
    assert identity(selected['sequence'])==selected['sequence_sha256']==config['selected']['sequence_sha256']==protocol['selected_sequence_sha256']
    assert sha(OUT/'SELECTED_SEQUENCE.txt')==selected['sequence_sha256']
    assert len(selected['sequence'])==92 and len(set(selected['sequence']))==92

def test_pinned_initial_population_reproduces_full_representation_and_warm_start():
    config=read('FINAL_GA_CONFIG_CANDIDATE.json')
    formal=json.loads((REPO_ROOT/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']
    inc={n:tuple(formal[n]) for n in config['initialization']['deterministic_order']}
    prior=tuple(config['initialization']['prior_best_sequence'])
    example=read('INITIAL_POPULATION_SEED42.json')
    actual=initialize(tuple(config['chromosome']['station_ids']),inc,random.Random(42),Variant(**config['algorithm']),prior)
    assert [list(x) for x in actual]==example['population']
    assert example['slot_categories'].count('deterministic')==7
    assert example['slot_categories'].count('prior_best')==1
    assert example['slot_categories'].count('one_inversion_neighbor')==25
    assert example['slot_categories'].count('uniform_random')==67
    assert actual[7]==prior and identity(prior)==config['initialization']['prior_best_sha256']
    assert all(len(x)==92 and set(x)==set(config['chromosome']['station_ids']) for x in actual)

def test_attribution_conserves_gains_and_keeps_equal_distinct_budgets():
    d=pd.read_csv(OUT/'GA_INITIALIZATION_VS_SEARCH_IMPROVEMENT.csv')
    assert d.groupby('method').seed.apply(set).map(lambda x:x==set(range(42,47))).all()
    assert d.distinct_expensive_evaluations.eq(50000).all()
    assert d.total_attempts.ge(d.distinct_expensive_evaluations).all()
    np.testing.assert_allclose(d.initial_gain_vs_impact_hr+d.postinitialization_improvement_hr,d.total_improvement_vs_impact_hr,atol=1e-12)
    np.testing.assert_allclose(d.initial_best_generation0_hr-d.final_best_hr,d.postinitialization_improvement_hr,atol=1e-12)
    config={name:json.loads(z.iloc[0].source_config) for name,z in d.groupby('method')}
    assert config['B_quality_original']['mutation']==config['C_quality_elite_inversion_m02']['mutation']==config['D_quality_elite_swap_m02']['mutation']==0.2
    assert config['B_quality_original']['elites']==0 and config['C_quality_elite_inversion_m02']['elites']==1
    assert config['C_quality_elite_inversion_m02']['mutation_operator']=='inversion' and config['D_quality_elite_swap_m02']['mutation_operator']=='swap'
    assert d.new_calls_this_round.sum()==500000

def test_budget_continuation_is_fixed_before_validation_and_monotone():
    config=read('FINAL_GA_CONFIG_CANDIDATE.json');p=config['search_protocol']
    assert p['stage_A_seeds']==list(range(42,62)) and p['stage_B_seeds']==list(range(42,47))
    assert p['continue_stage_A'] and not p['validation_guided_selection']
    assert len(p['stage_A_seeds'])*p['stage_A_distinct_budget']+len(p['stage_B_seeds'])*(p['stage_B_total_distinct_budget']-p['stage_A_distinct_budget'])==p['nominal_distinct_queries']==4000000
    d=pd.read_csv(OUT/'FINAL_BUDGET_CHECKPOINTS.csv')
    for seed,z in d.groupby('seed'):
        z=z.sort_values('distinct_evaluations')
        assert z.distinct_evaluations.tolist()==[50000,100000,250000,500000]
        assert np.all(np.diff(z.best_hr)<=1e-12)
        assert z.fully_completed_generation.le(z.actual_generation).all()
        assert z.cpu_status.str.startswith('NOT_RECORDED').all()

def test_comparator_identity_is_fixed_without_formal_sequence_replacement():
    q=read('VALIDATION_COMPARATOR_SEQUENCES.json');domain=set(read('FINAL_GA_CONFIG_CANDIDATE.json')['chromosome']['station_ids'])
    assert q['total_conditions']==10 and len(q['ordered_policies'])==9 and not q['selection_uses_validation']
    assert {x['strategy'] for x in q['ordered_policies']}=={'impact-first','hospital-first','degree-first','betweenness-first','random','vulnerability-first','ga-exploratory-01','ga-exploratory-02','ga-final-method-candidate'}
    for x in q['ordered_policies']:
        assert len(x['sequence'])==92 and set(x['sequence'])==domain and identity(x['sequence'])==x['sequence_sha256']
    assert not q['unconstrained']['crew_competition'] and not q['unconstrained']['directed_travel']

def test_schedule_equivalence_does_not_collapse_chromosome_or_crew_identity():
    c=pd.read_csv(OUT/'SEQUENCE_EQUIVALENCE_CLASSES.csv');p=pd.read_csv(OUT/'SEQUENCE_EQUIVALENCE_PER_REALIZATION.csv')
    assert c.sequence_sha256.nunique()==c.damaged_order_class.nunique()==c.operational_class.nunique()==3
    assert c.recovery_class.nunique()==c.crew_relabelled_route_class.nunique()==1
    assert len(p)==3*64
    assert p[['completion_equal','arrival_equal','travel_equal','predecessor_equal','crew_origin_equal','origin_grouped_clock_multiset_equal']].all().all()
    assert not p.loc[p.candidate.ne('ga-optimized-01'),'crew_equal'].any()

def test_independent_protocol_preserves_480h_and_separates_new_cohort():
    q=read('FINAL_VALIDATION_PROTOCOL.json')
    assert q['sample_size']==2000 and q['hazard']=='2pc50' and q['resource']=='C57_D1'
    assert q['randomness']['master_seed']!=42 and q['randomness']['split_code']==2
    assert q['primary']['horizon_hr']==[0,480] and q['primary']['reference']=='Impact-first'
    assert q['statistical']['no_optional_stopping'] and q['statistical']['no_reselection']
    assert q['statistical']['resampling_unit']=='Whole shared physical realization'
    assert q['estimate']['new_samples_generated']==0 and not q['estimate']['physical_sampling_benchmarked']
    assert q['endpoint_normalization_audit']['max_deviation_from1']<1e-14 and not q['endpoint_normalization_audit']['mapping_recomputed']

def test_completed_missing_comparisons_retain_records_and_cpu_accounting():
    records=list((OUT/'controlled_comparisons').glob('*/RUN.json'));assert len(records)==10
    for path in records:
        q=json.loads(path.read_text())
        assert q['status']=='COMPLETE_BUDGET' and q['distinct_evaluations']==q['actual_expensive_calls']==50000
        assert not q['formal_policy_replaced'] and not q['new_physical_sampling']
        assert q['setup_validation_objective_calls']==8 and q['process_cpu_seconds']>0 and q['objective_cpu_seconds']>0
        for name,h in q['files_sha256'].items():assert sha(path.parent/name)==h
"""Generated records are diagnostic artifacts, never formal strategy authority."""
