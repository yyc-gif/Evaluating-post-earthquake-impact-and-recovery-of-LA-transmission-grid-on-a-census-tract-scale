"""Transparent revised GA search and explicit legacy/direct evaluators."""
from dataclasses import dataclass
from typing import Callable,Mapping,Sequence
import random
import numpy as np
import pandas as pd
from r1_realization_scheduling import RealizationInputs,execute_realization_schedule,evaluate_completion_step_functionality
from r1_distributional_metrics import compute_tract_burden

@dataclass(frozen=True)
class RevisedGAConfig:
    population_size:int=100
    generations:int=100
    crossover_probability:float=.8
    mutation_probability:float=.2
    tournament_size:int=3

@dataclass(frozen=True)
class RevisedGAResult:
    seed:int
    best_sequence:tuple[str,...]
    best_fitness:float
    best_generation:int
    candidate_source:str
    incumbent_best_fitness:float
    search_improved_incumbent:bool
    history:pd.DataFrame

def _validate_permutation(sequence:Sequence[object],items:tuple[str,...])->tuple[str,...]:
    x=tuple(str(v) for v in sequence)
    if len(x)!=len(items) or len(set(x))!=len(x) or set(x)!=set(items):raise ValueError('Candidate must be a full permutation.')
    return x

def _ordered_crossover(a:tuple[str,...],b:tuple[str,...],rng:random.Random):
    n=len(a)
    if n<2:return a,b
    lo,hi=sorted(rng.sample(range(n),2));hi+=1
    def child(p,q):
        out=[None]*n;out[lo:hi]=p[lo:hi];rotated=[q[(hi+i)%n] for i in range(n)];fill=[x for x in rotated if x not in out];spots=list(range(hi,n))+list(range(0,lo))
        for spot,value in zip(spots,fill):out[spot]=value
        return tuple(out)
    return child(a,b),child(b,a)

def _mutate_inversion(x:tuple[str,...],rng:random.Random)->tuple[str,...]:
    if len(x)<2:return x
    lo,hi=sorted(rng.sample(range(len(x)),2));out=list(x);out[lo:hi+1]=reversed(out[lo:hi+1]);return tuple(out)

def run_revised_permutation_ga(*,items:Sequence[object],objective:Callable[[tuple[str,...]],float],incumbents:Mapping[str,Sequence[object]],seed:int,config:RevisedGAConfig=RevisedGAConfig())->RevisedGAResult:
    """Fixed-budget GA returning the best seen candidate, never a worse final individual."""
    domain=tuple(str(x) for x in items)
    if not domain or len(set(domain))!=len(domain):raise ValueError('items must be unique and nonempty.')
    if config.population_size<2 or config.generations<0 or config.tournament_size<2:raise ValueError('Invalid GA budget.')
    if not incumbents:raise ValueError('At least one deterministic incumbent is required.')
    rng=random.Random(int(seed));inc={str(k):_validate_permutation(v,domain) for k,v in incumbents.items()}
    score_cache={}
    def score(x):
        if x not in score_cache:
            value=float(objective(x))
            if not np.isfinite(value):raise ValueError('Objective returned nonfinite fitness.')
            score_cache[x]=value
        return score_cache[x]
    inc_scored=[(score(x),name,x) for name,x in inc.items()];inc_scored.sort(key=lambda z:(-z[0],z[1],z[2]));inc_best,inc_name,inc_seq=inc_scored[0]
    population=list(inc.values())
    while len(population)<config.population_size:population.append(tuple(rng.sample(domain,len(domain))))
    population=population[:config.population_size]
    archive_score=inc_best;archive_seq=inc_seq;archive_source=f'incumbent:{inc_name}';archive_generation=0;history=[]
    def update(generation,pop):
        nonlocal archive_score,archive_seq,archive_source,archive_generation
        scored=[score(x) for x in pop];idx=max(range(len(pop)),key=lambda i:(scored[i],tuple(pop[i])))
        if scored[idx]>archive_score:
            archive_score=scored[idx];archive_seq=pop[idx];archive_source=f'ga_seed:{seed}';archive_generation=generation
        history.append({'generation':generation,'generation_best':max(scored),'generation_mean':float(np.mean(scored)),'best_so_far':archive_score})
    update(0,population)
    for generation in range(1,config.generations+1):
        scored=[score(x) for x in population]
        def tournament():
            idx=[rng.randrange(len(population)) for _ in range(config.tournament_size)];return population[max(idx,key=lambda i:scored[i])]
        parents=[tournament() for _ in range(config.population_size)];offspring=[]
        for i in range(0,config.population_size,2):
            a=parents[i];b=parents[(i+1)%config.population_size]
            if rng.random()<config.crossover_probability:a,b=_ordered_crossover(a,b,rng)
            if rng.random()<config.mutation_probability:a=_mutate_inversion(a,rng)
            if rng.random()<config.mutation_probability:b=_mutate_inversion(b,rng)
            offspring.extend([a,b])
        population=offspring[:config.population_size];update(generation,population)
    return RevisedGAResult(int(seed),archive_seq,float(archive_score),archive_generation,archive_source,float(inc_best),bool(archive_score>inc_best),pd.DataFrame(history))

def run_multiseed_revised_ga(*,items,objective,incumbents,seeds,config=RevisedGAConfig()):
    return {int(seed):run_revised_permutation_ga(items=items,objective=objective,incumbents=incumbents,seed=int(seed),config=config) for seed in seeds}

def legacy_station_completion_objective(*,task_priority:pd.Series,expected_duration_hr:pd.Series,crew_origin_ids,base_to_task_hr,task_to_task_hr,tmax_hr:float,makespan_weight:float):
    """July station weighted-completion surrogate, exposed under an explicit name."""
    ids=pd.Index(task_priority.index.astype(str));priority=pd.to_numeric(task_priority,errors='raise');duration=pd.to_numeric(expected_duration_hr,errors='raise').reindex(ids)
    if duration.isna().any() or (duration<=0).any() or tmax_hr<=0:raise ValueError('Legacy objective inputs invalid.')
    ds=pd.Series(1,index=ids);total=max(float(np.clip(priority.to_numpy(float),0,None).sum()),1e-12);denom=tmax_hr*total
    def objective(sequence):
        events,_,clocks,_=execute_realization_schedule(full_priority_sequence=sequence,damage_state=ds,realized_duration_hr=duration,crew_origin_ids=crew_origin_ids,base_to_task_hr=base_to_task_hr,task_to_task_hr=task_to_task_hr)
        finish=events.set_index('task_id').completion_hr.reindex(ids);credit=np.clip(tmax_hr-finish.to_numpy(float),0,tmax_hr);benefit=float(np.sum(priority.to_numpy(float)*credit)/denom);return benefit-float(makespan_weight)*float(clocks.max()/tmax_hr)
    return objective

def evaluate_direct_population_burden(*,sequence,realization:RealizationInputs,crew_origin_ids,base_to_task_hr,task_to_task_hr,time_hr,source_gate:Callable[[pd.DataFrame],pd.DataFrame],tract_weight_matrix:np.ndarray,tract_ids:Sequence[object],tract_population:pd.Series):
    """Decode schedule -> completion state -> source gate -> tract burden."""
    events,completion,clocks,_=execute_realization_schedule(full_priority_sequence=sequence,damage_state=realization.damage_state,realized_duration_hr=realization.realized_duration_hr,crew_origin_ids=crew_origin_ids,base_to_task_hr=base_to_task_hr,task_to_task_hr=task_to_task_hr)
    if len(clocks) and float(np.max(clocks))>float(np.max(np.asarray(time_hr,float))):raise ValueError('Direct-objective horizon ends before schedule completion.')
    event_times=np.unique(np.concatenate([np.asarray(time_hr,float),completion.dropna().to_numpy(float)]))
    raw=evaluate_completion_step_functionality(damage_state=realization.damage_state,completion_time_hr=completion,time_hr=event_times);effective=source_gate(raw.copy(deep=True))
    from r1_source_gate import GateTrace
    if isinstance(effective,GateTrace): effective=effective.e
    W=np.asarray(tract_weight_matrix,float);tids=pd.Index([str(x) for x in tract_ids]);sids=pd.Index(realization.damage_state.index.astype(str))
    if W.shape!=(len(tids),len(sids)):raise ValueError('tract_weight_matrix shape mismatch.')
    if not np.isfinite(W).all() or (W<0).any():raise ValueError('Tract weights must be finite and nonnegative.')
    resolved=pd.Series(W.sum(axis=1),index=tids);known=pd.DataFrame(effective.to_numpy(float)@W.T,index=effective.index,columns=tids)
    for tract in tids[resolved<=1e-15]:known[tract]=np.nan
    burden=compute_tract_burden(known,resolved,interpolation='previous');pop=pd.to_numeric(tract_population,errors='raise');pop.index=pop.index.astype(str);pop=pop.reindex(tids)
    valid=burden.status.eq('resolved');weights=pop*burden.resolved_mass;denom=float(weights[valid].sum())
    if pop.isna().any() or denom<=0:raise ValueError('Population coverage/denominator invalid.')
    population_burden=float((pop[valid]*burden.restoration_burden_mass_hr[valid]).sum()/denom)
    return {'population_burden_hr':population_burden,'makespan_hr':float(clocks.max()) if len(clocks) else 0.,'task_events':events,'raw_functionality':raw,'effective_functionality':effective,'tract_burden':burden}

def direct_population_burden_objective(**fixed_inputs):
    """Maximization-form objective: negative direct population burden."""
    def objective(sequence):return -evaluate_direct_population_burden(sequence=sequence,**fixed_inputs)['population_burden_hr']
    return objective
