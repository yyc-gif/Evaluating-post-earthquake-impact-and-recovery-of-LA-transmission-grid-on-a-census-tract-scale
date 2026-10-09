"""Behavioral guards for fixed-budget diagnostics and permutation variants."""
import random
import numpy as np,pandas as pd,pytest
from la_grid.diagnostics.ga_variant_engine import Variant,run_search,crossover,mutation
from la_grid.revision.r1_ga_revision import RevisedGAConfig,run_revised_permutation_ga
from la_grid.revision.r1_ga_exact_kernel import _one_sample
ITEMS=tuple(map(str,range(8)));INC={'impact-first':ITEMS,'other':ITEMS[::-1]}
def objective(x):return -float(np.dot(np.arange(1,9),(np.array(list(map(int,x)))-np.array([3,7,1,5,0,6,4,2]))**2))
@pytest.mark.parametrize('seed',[42,43,44,45,46])
def test_observation_preserves_original_random_stream(seed):
    new=run_search(items=ITEMS,incumbents=INC,objective=objective,seed=seed,config=Variant(population=20),max_evaluations=100000,max_generations=80)
    old=run_revised_permutation_ga(items=ITEMS,incumbents=INC,objective=objective,seed=seed,config=RevisedGAConfig(20,80,.8,.2,3))
    pd.testing.assert_frame_equal(new['history'][['generation','generation_best','generation_mean','best_so_far']],old.history)
    assert new['archive_sequence']==old.best_sequence

def test_mid_generation_budget_resume_is_exact(tmp_path):
    v=Variant(population=20);folder=tmp_path/'partial'
    run_search(items=ITEMS,incumbents=INC,objective=objective,seed=91,config=v,max_evaluations=101,folder=folder,checkpoints=(101,203))
    resumed=run_search(items=ITEMS,incumbents=INC,objective=objective,seed=91,config=v,max_evaluations=203,folder=folder,checkpoints=(101,203))
    direct=run_search(items=ITEMS,incumbents=INC,objective=objective,seed=91,config=v,max_evaluations=203,checkpoints=(101,203))
    assert resumed['cache']==direct['cache'] and resumed['best_sequence']==direct['best_sequence']
    assert len(resumed['cache'])==resumed['state']['expensive_calls']==203
    pd.testing.assert_frame_equal(resumed['history'][['generation_best','generation_mean','best_so_far']],direct['history'][['generation_best','generation_mean','best_so_far']])

@pytest.mark.parametrize('elites',[1,3])
def test_elitism_preserves_strong_population_chromosome(elites):
    run=run_search(items=ITEMS,incumbents=INC,objective=objective,seed=62,config=Variant(population=20,elites=elites),max_evaluations=100000,max_generations=70)
    assert np.all(np.diff(run['history'].population_best_service_loss_hr)<=0)
    assert run['history'].archive_copies_in_population.ge(1).all()

@pytest.mark.parametrize('operator',['ordered','cycle','pmx'])
def test_crossover_is_full_permutation(operator):
    for seed in range(100):
        a,b=crossover(ITEMS,tuple(random.Random(seed).sample(ITEMS,8)),random.Random(seed),operator)
        assert len(a)==len(b)==8 and set(a)==set(b)==set(ITEMS)

@pytest.mark.parametrize('operator',['inversion','swap','insertion','mixed'])
def test_mutation_is_full_permutation(operator):
    for seed in range(100):
        x=mutation(ITEMS,random.Random(seed),operator);assert len(x)==8 and set(x)==set(ITEMS)

def test_unlimited_zero_travel_relaxation_is_lower_bound():
    ds=np.array([2,4,1,0,3,2]);duration=np.array([3.,8.,1.,0.,5.,2.]);offset=np.array([0,1,3,5,7,9,10]);neighbors=np.array([1,0,2,1,3,2,4,3,5,4]);sources=np.array([True,False,False,False,False,False]);mass=np.arange(1,7,dtype=float);order=np.arange(6);lb=_one_sample(order,ds,duration,np.zeros(6,dtype=np.int64),np.zeros((1,6)),np.zeros((6,6)),offset,neighbors,sources,mass,mass.sum(),100.)
    for seed in range(30):
        x=np.array(random.Random(seed).sample(range(6),6));actual=_one_sample(x,ds,duration,np.array([0,0]),np.ones((1,6)),np.ones((6,6)),offset,neighbors,sources,mass,mass.sum(),100.);assert actual>=lb-1e-12
