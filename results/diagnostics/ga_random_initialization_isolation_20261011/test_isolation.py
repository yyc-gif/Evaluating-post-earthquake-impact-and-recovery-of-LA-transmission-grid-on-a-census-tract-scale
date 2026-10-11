"""Fast diagnostic tests; no scientific input or independent-validation access."""
import hashlib
import pickle
import random
import numpy as np
import study
import analyze

IDS=tuple(str(300000+i) for i in range(92))
IMPACT=IDS


def test_matched_pool_rng():
    a,b={},{}
    aa=study.engine(study.MODES[0],IMPACT,a)
    bb=study.engine(study.MODES[1],IMPACT,b)
    ra,rb=random.Random(1234),random.Random(1234)
    pa=aa.initialize(IDS,{},ra,study.config(),None)
    pb=bb.initialize(IDS,{},rb,study.config(),None)
    assert pa[1:]==pb[1:] and pb[0]==IMPACT
    assert ra.getstate()==rb.getstate()
    assert a['common_random_pool']==b['common_random_pool']
    assert a['archive_before_first_evaluation']==b['archive_before_first_evaluation']==[]
    assert pa==[tuple(x) for x in a['common_random_pool']]
    assert pa[0]!=IMPACT


def test_archive_first_actual_random_score():
    capture={};eng=study.engine(study.MODES[0],IMPACT,capture);calls=[]
    def objective(seq):
        calls.append(seq)
        return -sum((i+1)*int(x) for i,x in enumerate(seq))
    r=eng.run_search(items=IDS,incumbents={},objective=objective,seed=1234,
        config=study.config(),max_evaluations=1000,checkpoints=(100,1000))
    assert calls[:100]==[tuple(x) for x in capture['initial_sequences']]
    assert len(calls)==len(r['cache'])==1000
    assert r['state']['lookup_calls']==0
    assert r['state']['expensive_calls']==1000
    assert r['best_fitness']>=r['history'].iloc[0].generation_best


def test_fixed_configuration():
    c=study.config()
    assert (c.population,c.crossover,c.mutation,c.tournament,c.elites)==(100,.8,.1,3,1)
    assert c.mutation_operator=='swap' and c.crossover_operator=='ordered'
    assert not c.adaptive and not c.restart and not c.diversity_replacement


def test_seed_unit_intervals_and_sign():
    d=np.arange(20)*.0001
    r=analyze.paired(d)
    assert r['n']==20 and r['seeded_wins']==19 and r['ties']==1
    assert r['mean_delta_hr']==np.mean(d)
    assert r['simultaneous95_low_hr']<r['t95_low_hr']
    assert r['simultaneous95_high_hr']>r['t95_high_hr']
    assert analyze.paired(d)==r


def test_engine_source_not_edited():
    design=study.read(study.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    name='src/la_grid/diagnostics/ga_variant_engine.py'
    assert study.digest(study.ROOT/name)==design['source_hashes'][name]
    assert not set(study.MAIN)&set(study.SMOKE)
    assert study.RESERVE==study.MAIN[:10]
