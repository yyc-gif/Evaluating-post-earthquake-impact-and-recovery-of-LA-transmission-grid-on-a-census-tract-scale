"""Realization-specific paired scheduling for the reviewer-driven path.

July Stage 4/5 functions remain available for submission reproduction. This
module consumes one retained damage vector and its matching duration vector;
it does not sample damage, compute priorities, or alter the source gate.
"""
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence
import numpy as np
import pandas as pd

INITIAL_BY_DS={0:1.00,1:0.50,2:0.09,3:0.04,4:0.03}

@dataclass(frozen=True)
class RealizationInputs:
    realization_id:str
    damage_state:pd.Series
    realized_duration_hr:pd.Series

@dataclass(frozen=True)
class RealizationStrategyResult:
    realization_id:str
    strategy_id:str
    filtered_task_sequence:tuple[str,...]
    task_events:pd.DataFrame
    completion_time_hr:pd.Series
    raw_functionality:pd.DataFrame
    effective_functionality:pd.DataFrame
    crew_final_available_hr:np.ndarray
    gate_trace:object=None

def _ids(values):
    x=pd.Index([str(v).strip() for v in values],dtype='object')
    if x.empty or x.has_duplicates or (x=='').any(): raise ValueError('Station IDs must be nonempty and unique.')
    return x

def draw_positive_normal(rng:np.random.Generator,*,mean_hr:float,std_hr:float,size:int)->np.ndarray:
    """Draw Normal repair durations conditioned on strictly positive time."""
    mean_hr=float(mean_hr); std_hr=float(std_hr)
    if size<0 or not np.isfinite([mean_hr,std_hr]).all() or std_hr<0: raise ValueError('Invalid Normal repair parameters.')
    if size==0:return np.empty(0)
    if std_hr==0:
        if mean_hr<=0: raise ValueError('Deterministic repair duration must be positive.')
        return np.full(size,mean_hr)
    out=np.empty(size); pending=np.arange(size)
    while pending.size:
        candidate=rng.normal(mean_hr,std_hr,pending.size); ok=np.isfinite(candidate)&(candidate>0)
        out[pending[ok]]=candidate[ok]; pending=pending[~ok]
    return out

def _validate(ds:pd.Series,duration:pd.Series)->pd.Index:
    ids=_ids(ds.index); dids=_ids(duration.index)
    if not ids.equals(dids): raise ValueError('Damage and duration station identity/order differ.')
    dsv=pd.to_numeric(ds,errors='raise').to_numpy(float); tv=pd.to_numeric(duration,errors='raise').to_numpy(float)
    if not np.isfinite(dsv).all() or not np.equal(dsv,np.floor(dsv)).all() or not np.isin(dsv.astype(int),range(5)).all(): raise ValueError('Damage states must be integers 0..4.')
    if not np.isfinite(tv).all(): raise ValueError('Durations must be finite.')
    damaged=dsv>0
    if np.any(tv[~damaged]!=0): raise ValueError('DS0 duration must be zero.')
    if np.any(tv[damaged]<=0): raise ValueError('Damaged-task duration must be positive.')
    return ids

def realization_inputs_from_stage3(stage_3_data:Mapping[str,object],*,scenario:str,realization_index:int,station_ids:Sequence[object])->RealizationInputs:
    ids=_ids(station_ids); ds_map=stage_3_data.get('all_damage_state_samples'); time_map=stage_3_data.get('all_mc_repair_times')
    if not isinstance(ds_map,Mapping) or scenario not in ds_map: raise KeyError(f'Missing damage samples for {scenario}.')
    if not isinstance(time_map,Mapping) or scenario not in time_map: raise KeyError(f'Missing duration samples for {scenario}.')
    ds=np.asarray(ds_map[scenario]); times=np.asarray(time_map[scenario],float)
    if ds.shape!=times.shape or ds.ndim!=2 or ds.shape[0]!=len(ids): raise ValueError('Stage 3 DS/duration matrices are not aligned.')
    if not 0<=realization_index<ds.shape[1]: raise IndexError('realization_index out of range.')
    ds_s=pd.Series(ds[:,realization_index],index=ids,dtype='int64',name='damage_state')
    time_s=pd.Series(times[:,realization_index],index=ids,name='realized_duration_hr')
    _validate(ds_s,time_s)
    return RealizationInputs(f'mc_{realization_index:06d}',ds_s.copy(),time_s.copy())

def execute_realization_schedule(*,full_priority_sequence:Sequence[object],damage_state:pd.Series,realized_duration_hr:pd.Series,crew_origin_ids:Sequence[object],base_to_task_hr:pd.DataFrame,task_to_task_hr:pd.DataFrame):
    ids=_validate(damage_state,realized_duration_hr); seq=tuple(str(v).strip() for v in full_priority_sequence)
    if len(seq)!=len(ids) or len(set(seq))!=len(seq) or set(seq)!=set(ids): raise ValueError('Priority sequence must be a full station permutation.')
    origins=tuple(str(v).strip() for v in crew_origin_ids)
    if not origins or any(not v for v in origins): raise ValueError('Explicit crew origins required.')
    base=base_to_task_hr.copy(); task=task_to_task_hr.copy()
    base.index=base.index.astype(str).str.strip(); base.columns=base.columns.astype(str).str.strip(); task.index=task.index.astype(str).str.strip(); task.columns=task.columns.astype(str).str.strip()
    if not set(origins).issubset(base.index) or set(base.columns)!=set(ids) or set(task.index)!=set(ids) or set(task.columns)!=set(ids): raise ValueError('Travel matrices do not cover explicit IDs.')
    base=base.reindex(index=pd.Index(origins),columns=ids); task=task.reindex(index=ids,columns=ids)
    for matrix in (base,task):
        x=matrix.to_numpy(float)
        if not np.isfinite(x).all() or (x<0).any(): raise ValueError('Travel must be finite and nonnegative; no fallback is used.')
    ds=damage_state.reindex(ids); duration=realized_duration_hr.reindex(ids); queue=tuple(s for s in seq if int(ds.loc[s])>0)
    clocks=np.zeros(len(origins)); previous=[None]*len(origins); rows=[]; completion=pd.Series(np.nan,index=ids,name='completion_time_hr')
    for rank,station in enumerate(queue,1):
        crew=int(np.argmin(clocks)); free=float(clocks[crew]); prev=previous[crew]
        travel=float(base.loc[origins[crew],station] if prev is None else task.loc[prev,station]); arrival=free+travel; dur=float(duration.loc[station]); finish=arrival+dur
        rows.append({'dispatch_rank':rank,'task_id':station,'damage_state':int(ds.loc[station]),'crew_index':crew,'crew_origin_id':origins[crew],'previous_task_id':prev,'crew_available_before_hr':free,'travel_hr':travel,'arrival_hr':arrival,'realized_duration_hr':dur,'completion_hr':finish})
        clocks[crew]=finish; previous[crew]=station; completion.loc[station]=finish
    return pd.DataFrame(rows),completion,clocks.copy(),queue

def evaluate_completion_step_functionality(*,damage_state:pd.Series,completion_time_hr:pd.Series,time_hr:Sequence[float],initial_functionality_by_ds:Mapping[int,float]=INITIAL_BY_DS)->pd.DataFrame:
    ids=_ids(damage_state.index); times=np.asarray(time_hr,float)
    if times.ndim!=1 or times.size==0 or not np.isfinite(times).all() or np.any(np.diff(times)<0): raise ValueError('time_hr must be finite and nondecreasing.')
    ds=pd.to_numeric(damage_state.reindex(ids),errors='raise').to_numpy(int); completion=completion_time_hr.reindex(ids)
    values=np.broadcast_to([float(initial_functionality_by_ds[int(x)]) for x in ds],(len(times),len(ids))).copy()
    for j,state in enumerate(ds):
        if state==0: values[:,j]=1.; continue
        finish=float(completion.iloc[j])
        if not np.isfinite(finish): raise ValueError('Damaged task lacks completion time.')
        values[times>=finish,j]=1.
    return pd.DataFrame(values,index=times,columns=ids)

def simulate_paired_realization_strategies(*,realization:RealizationInputs,strategy_sequences:Mapping[str,Sequence[object]],crew_origin_ids:Sequence[object],base_to_task_hr:pd.DataFrame,task_to_task_hr:pd.DataFrame,time_hr:Sequence[float],source_gate:Callable[[pd.DataFrame],pd.DataFrame],initial_functionality_by_ds:Mapping[int,float]=INITIAL_BY_DS):
    if not strategy_sequences: raise ValueError('At least one strategy required.')
    ds=realization.damage_state.copy(deep=True); duration=realization.realized_duration_hr.copy(deep=True); results={}
    for name,seq in strategy_sequences.items():
        events,completion,clocks,queue=execute_realization_schedule(full_priority_sequence=seq,damage_state=ds,realized_duration_hr=duration,crew_origin_ids=crew_origin_ids,base_to_task_hr=base_to_task_hr,task_to_task_hr=task_to_task_hr)
        if float(np.max(time_hr)) < float(clocks.max()): raise ValueError('Horizon ends before schedule completion.')
        event_times=np.unique(np.concatenate([np.asarray(time_hr,float),completion.dropna().to_numpy(float)]))
        raw=evaluate_completion_step_functionality(damage_state=ds,completion_time_hr=completion,time_hr=event_times,initial_functionality_by_ds=initial_functionality_by_ds)
        gate_output=source_gate(raw.copy(deep=True))
        from r1_source_gate import GateTrace
        trace=gate_output if isinstance(gate_output,GateTrace) else None
        effective=trace.e if trace is not None else gate_output
        if not isinstance(effective,pd.DataFrame) or effective.shape!=raw.shape: raise ValueError('source_gate returned incompatible output.')
        results[str(name)]=RealizationStrategyResult(realization.realization_id,str(name),queue,events,completion,raw,effective.copy(deep=True),clocks,trace)
    if not realization.damage_state.equals(ds) or not realization.realized_duration_hr.equals(duration): raise RuntimeError('Shared realization was mutated.')
    return results
