"""Deterministic neighborhood search and a certified model relaxation bound."""
from pathlib import Path
import itertools,json,gzip,pickle,time,hashlib,argparse
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_ga_exact_kernel import _one_sample


def neighbors(order):
    n=len(order)
    for i in range(n-1):
        for j in range(i+1,n):
            v=list(order);v[i],v[j]=v[j],v[i];yield ('swap',i,j),tuple(v)
    for i in range(n):
        for j in range(n):
            if j==i:continue
            v=list(order);v.insert(j,v.pop(i));yield ('insertion',i,j),tuple(v)
    for i in range(n-1):
        for j in range(i+1,n):
            v=list(order);v[i:j+1]=reversed(v[i:j+1]);yield ('inversion',i,j),tuple(v)
    for width in [2,3,4]:
        for i in range(n-2*width+1):
            v=list(order);v[i:i+2*width]=v[i+width:i+2*width]+v[i:i+width];yield ('adjacent_block_exchange',i,width),tuple(v)


def refine(*,kernel,start_sequence,budget,folder,initial_cache=None,initial_used=0):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);path=folder/'LOCAL_CHECKPOINT.pkl.gz';tick=time.perf_counter();cache={} if initial_cache is None else dict(initial_cache)
    state=dict(current=tuple(start_sequence),value=kernel.score(start_sequence),round=0,scan_index=0,round_best=tuple(start_sequence),round_value=kernel.score(start_sequence),round_move=None,attempts=0,accepted=[],elapsed=0.,local_optimal=False,initial_budget=initial_used,search_start_objective=-kernel.score(start_sequence))
    def key(x):return bytes(kernel.index[v] for v in x)
    cache.setdefault(key(start_sequence),state['value'])
    if path.exists():
        with gzip.open(path,'rb') as f:data=pickle.load(f)
        state=data['state'];cache=data['cache']
    offset=state['elapsed'];last_saved=len(cache)
    def save():
        state['elapsed']=offset+time.perf_counter()-tick
        tmp=path.with_suffix('.tmp')
        with gzip.open(tmp,'wb',compresslevel=1) as f:pickle.dump(dict(state=state,cache=cache),f,protocol=5)
        tmp.replace(path)
    done=False
    while not done:
        complete=True
        for j,(move,candidate) in enumerate(neighbors(state['current'])):
            if j<state['scan_index']:continue
            k=key(candidate)
            if k not in cache and len(cache)>=budget:complete=False;done=True;break
            state['attempts']+=1
            if k not in cache:cache[k]=kernel.score(candidate)
            value=cache[k]
            if value>state['round_value']+1e-9:
                state['round_value']=value;state['round_best']=candidate;state['round_move']=move
            state['scan_index']=j+1
            if len(cache)-last_saved>=25000:save();last_saved=len(cache)
        if state['round_value']>state['value']+1e-9:
            state['accepted'].append(dict(round=state['round'],move=state['round_move'],before_service_loss_hr=-state['value'],after_service_loss_hr=-state['round_value'],improvement_hr=state['round_value']-state['value'],distinct_evaluations=len(cache),elapsed_seconds=offset+time.perf_counter()-tick,complete_neighborhood_scan=complete,sequence=list(state['round_best']),sequence_sha256=old.identity(state['round_best'])))
            state['current']=state['round_best'];state['value']=state['round_value'];state['round']+=1;state['round_move']=None;state['scan_index']=0
            print('LOCAL MOVE',folder.name,len(cache),-state['value'],flush=True)
        elif complete:state['local_optimal']=True;done=True
        else:done=True
    save();seq=state['current'];values=old.per_sample(kernel,seq);pd.DataFrame({'planning_realization':range(64),'service_loss_hr':values}).to_csv(folder/'PLANNING_REALIZATIONS.csv',index=False)
    (folder/'ACCEPTED_MOVES.json').write_text(json.dumps(state['accepted'],indent=2)+'\n')
    pd.DataFrame([{k:v for k,v in x.items() if k!='sequence'} for x in state['accepted']],columns=['round','move','before_service_loss_hr','after_service_loss_hr','improvement_hr','distinct_evaluations','elapsed_seconds','complete_neighborhood_scan','sequence_sha256']).to_csv(folder/'ACCEPTED_MOVES.csv',index=False)
    result=dict(method='DETERMINISTIC_STEEPEST_NEIGHBORHOOD_SEARCH',budget=budget,distinct_evaluations=len(cache),total_attempts=state['attempts'],start_sequence=list(start_sequence),start_sequence_sha256=old.identity(start_sequence),start_planning_loss_hr=state['search_start_objective'],best_sequence=list(seq),sequence_sha256=old.identity(seq),best_planning_loss_hr=-state['value'],improvement_vs_previous_hr=33.03813174326729+state['value'],accepted_moves=len(state['accepted']),tested_neighborhoods=['all pair swaps','all remove-and-reinsert moves','all contiguous inversions','adjacent block exchanges of widths 2,3,4'],local_optimal_up_to_1e_minus_9=state['local_optimal'],last_scan_complete=complete,elapsed_seconds=state['elapsed'],global_optimality_proven=False,formal_policy_replaced=False)
    (folder/'RUN.json').write_text(json.dumps(result,indent=2)+'\n');return result,cache


def lower_bound():
    kernel,inc,quality=load();order=np.arange(92,dtype=np.int64);zeros_base=np.zeros((1,92));zeros_travel=np.zeros((92,92));independent_crews=np.zeros(92,dtype=np.int64)
    values=np.array([_one_sample(order,kernel.damage[i],kernel.duration[i],independent_crews,zeros_base,zeros_travel,kernel.neighbor_offset,kernel.neighbors,kernel.source_flag,kernel.station_mass,kernel.total_mass,kernel.horizon) for i in range(64)])
    upper=old.per_sample(kernel,quality);assert np.all(values<=upper+1e-8)
    pd.DataFrame({'planning_realization':range(64),'certified_relaxation_loss_hr':values,'previous_best_loss_hr':upper}).to_csv(OUT/'RELAXATION_LOWER_BOUND.csv',index=False)
    record=dict(bound_type='Rigorous relaxation lower bound for the original fixed-64 planning model',lower_bound_hr=float(values.mean()),relaxation='Unlimited crews, zero travel, each damaged station completes at its saved repair duration; original functionality threshold and source-connected gate retained',proof='Any feasible schedule finishes station i no earlier than its saved duration: clocks and travel are nonnegative. Raw functionality under the relaxation is pointwise at least the feasible schedule. Functionality threshold, source-connected components and e=fFC are monotone under earlier station restoration. Nonnegative station population-dependency weights imply the relaxed service-loss integral is no larger for every realization and hence for their mean.',original_objective_unchanged=True,original_constraints_relaxed_not_redefined=True,scope='Original fixed 64 realizations and model, not an out-of-sample performance guarantee',previous_upper_bound_hr=float(upper.mean()),certifies_unique_optimum=False)
    (OUT/'RELAXATION_LOWER_BOUND.json').write_text(json.dumps(record,indent=2)+'\n');print('CERTIFIED RELAXATION',record['lower_bound_hr'],flush=True)


def reduced_exact():
    kernel,inc,quality=load();slots=[0,1,2,57,58,59];selected=[quality[i] for i in slots];best=quality;bestscore=kernel.score(quality);rows=[]
    for permutation in itertools.permutations(selected):
        seq=list(quality)
        for i,station in zip(slots,permutation):seq[i]=station
        value=kernel.score(tuple(seq));rows.append(dict(sequence_sha256=old.identity(seq),planning_loss_hr=-value,slot_station_order=';'.join(permutation)))
        if value>bestscore:bestscore=value;best=tuple(seq)
    pd.DataFrame(rows).to_csv(OUT/'EXACT_REDUCED_NEIGHBORHOOD.csv',index=False)
    (OUT/'EXACT_REDUCED_NEIGHBORHOOD.json').write_text(json.dumps({'tested_permutations':720,'fixed_slots_zero_based':slots,'remaining_stations_fixed':86,'selected_stations':selected,'best_sequence':list(best),'best_planning_loss_hr':-bestscore,'exact_within_this_restricted_instance':True,'global_lower_bound':False,'interpretation':'A feasible upper bound and exact conditional six-station neighborhood optimum, not a global optimum or full-problem lower bound.'},indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['bound','reduced','local']);p.add_argument('--budget',type=int,default=100000);a=p.parse_args()
    if a.task=='bound':return lower_bound()
    if a.task=='reduced':return reduced_exact()
    kernel,inc,quality=load();return refine(kernel=kernel,start_sequence=quality,budget=a.budget,folder=OUT/'local_search/previous_best')
if __name__=='__main__':main()
