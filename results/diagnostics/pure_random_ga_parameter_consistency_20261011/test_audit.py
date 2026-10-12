"""Narrow implementation coverage; no physical sampling or validation access."""
import random
from dataclasses import replace
import numpy as np
import audit as a

IDS=tuple(str(300000+i) for i in range(92))

def test_same_size_population_rng_and_prefix():
    captures={}
    for case in a.CASES:
        cfg=replace(a.REFERENCE,**a.CASES[case]);captures[case]={}
        r=random.Random(123)
        pool=a.engine(captures[case]).initialize(IDS,{},r,cfg,None)
        expected=random.Random(123)
        assert pool==[tuple(expected.sample(IDS,92)) for _ in range(cfg.population)]
        assert captures[case]['initial_cache']==captures[case]['archive_before_first_evaluation']==[]
    for case in set(a.CASES)-{'P50','P250'}: assert captures[case]==captures['REF']
    assert captures['P50']['initial_sequences']==captures['REF']['initial_sequences'][:50]
    assert captures['REF']['initial_sequences']==captures['P250']['initial_sequences'][:100]

def test_ox_segment_and_other_parent_order():
    m=a.engine({});x=IDS;y=IDS[::-1]
    for seed in range(100):
        rng=random.Random(seed);lo,hi=sorted(rng.sample(range(92),2));hi+=1
        child,_=m.crossover(x,y,random.Random(seed),'ordered')
        assert child[lo:hi]==x[lo:hi]
        slots=list(range(hi,92))+list(range(lo))
        expected=[y[(hi+i)%92] for i in range(92) if y[(hi+i)%92] not in x[lo:hi]]
        assert [child[i] for i in slots]==expected
        assert set(child)==set(IDS) and len(child)==92

def test_swap_changes_exactly_two_positions():
    for seed in range(100):
        child=a.engine({}).mutation(IDS,random.Random(seed),'swap')
        assert sum(x!=y for x,y in zip(IDS,child))==2 and set(child)==set(IDS)

def test_no_elite_still_retains_best_observed_and_exact_budget():
    calls=[]
    def f(seq):
        calls.append(seq)
        return -sum((i+1)*int(x) for i,x in enumerate(seq))
    r=a.engine({}).run_search(items=IDS,incumbents={},objective=f,seed=92,
        config=replace(a.REFERENCE,elites=0),max_evaluations=1000,checkpoints=(100,1000))
    assert len(calls)==len(r['cache'])==r['state']['expensive_calls']==1000
    assert r['state']['lookup_calls']==0
    assert r['best_fitness']==max(r['cache'].values())
    assert r['state']['attempts']>=1000+r['state']['generation']*100

def test_first_exact_fitness_tie_is_retained():
    capture={};m=a.engine(capture)
    r=m.run_search(items=IDS,incumbents={},objective=lambda seq:0.,seed=92,
        config=a.REFERENCE,max_evaluations=333,checkpoints=(333,))
    assert list(r['best_sequence'])==capture['initial_sequences'][0]

def test_simultaneous_interval_and_replication_unit():
    x=np.linspace(-.2,.1,20);r=a.paired(x,3,101)
    assert r['n']==20 and r['family_size']==3
    assert r['simultaneous95_low_hr']<r['pointwise95_low_hr']
    assert r['simultaneous95_high_hr']>r['pointwise95_high_hr']
    assert r['wins']+r['losses']+r['ties']==20
    assert r==a.paired(x,3,101)
