"""2pc50 station-only source-terminal reliability on the retained July92 graph.

Only new topology-only Bernoulli states are sampled. Formal damage and recovery
trajectories are read, never regenerated. Transmission edges are fixed.
"""
from __future__ import annotations

import argparse
import heapq
import json
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit

from fragility_connectivity_audit import production_ds_probabilities
from r1_connectivity_state_analysis import STRATEGIES, trajectory_path, mapping_matrix
from r1_formal_dynamic_topology import _graph_arrays

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "Formal_Experiment_20260923"
RESULTS = FORMAL / "Formal_Reviewer_Results"
HAZARD = "2pc50"
N = 100_000
CHECKPOINTS = (10_000,25_000,50_000,100_000)
TIMES = np.array([0.,6.,12.,24.,48.,72.,120.,240.,480.])


@njit(cache=True)
def _root(parent, i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


@njit(cache=True)
def _component_counts(states, edge_u, edge_v, adjacency, degree, source_indices, checkpoints):
    """Component masks plus conditional-on-target-functional connectivity.

    The other 91 independently sampled states are held fixed. If a target is
    sampled off, its hypothetical activation connects it to its active
    neighbors' components. This gives 100k conditional draws even when r_i is
    too small to produce a functional target in the unconditional sample.
    """
    ns,n = states.shape
    functional = np.zeros((len(checkpoints),n),np.int64)
    connected = np.zeros_like(functional)
    conditional = np.zeros_like(functional)
    individual = np.zeros((len(checkpoints),n,len(source_indices)),np.int64)
    fcount=np.zeros(n,np.int64); ccount=np.zeros(n,np.int64)
    conditional_count=np.zeros(n,np.int64)
    source_counts=np.zeros((n,len(source_indices)),np.int64)
    source_bit=np.zeros(n,dtype=np.int32)
    for s in range(len(source_indices)):source_bit[source_indices[s]]=1<<s
    for sample in range(ns):
        active=states[sample]
        parent=np.arange(n,dtype=np.int16)
        rank=np.zeros(n,dtype=np.int8)
        for e in range(len(edge_u)):
            u=edge_u[e];v=edge_v[e]
            if not(active[u] and active[v]):continue
            a=_root(parent,u);b=_root(parent,v)
            if a==b:continue
            if rank[a]<rank[b]:parent[a]=b
            elif rank[a]>rank[b]:parent[b]=a
            else:parent[b]=a;rank[a]+=1
        source_mask=np.zeros(n,dtype=np.int32)
        for s in range(len(source_indices)):
            i=source_indices[s]
            if active[i]:source_mask[_root(parent,i)] |= 1<<s
        for i in range(n):
            if active[i]:
                fcount[i]+=1
                mask=source_mask[_root(parent,i)]
                if mask:ccount[i]+=1
            else:
                mask=source_bit[i]
                for a in range(degree[i]):
                    neighbor=adjacency[i,a]
                    if active[neighbor]:mask |= source_mask[_root(parent,neighbor)]
            if mask:conditional_count[i]+=1
            for s in range(len(source_indices)):
                if mask & (1<<s):source_counts[i,s]+=1
        if sample+1 in checkpoints:
            c=np.searchsorted(checkpoints,sample+1)
            functional[c]=fcount
            connected[c]=ccount
            conditional[c]=conditional_count
            individual[c]=source_counts
    return functional,connected,conditional,individual


def best_paths(ids, eu, ev, source, r):
    """Minimize node -log(r), excluding target and including source endpoint."""
    n=len(ids);adj=[[] for _ in ids]
    for u,v in zip(eu,ev):adj[u].append(v);adj[v].append(u)
    cost=-np.log(np.clip(r,np.finfo(float).tiny,1.))
    dist=np.full(n,np.inf); nxt=np.full(n,-1,dtype=int)
    origin=np.full(n,-1,dtype=int); heap=[]
    for s in np.flatnonzero(source):
        dist[s]=0.;origin[s]=s;heapq.heappush(heap,(0.,int(s)))
    while heap:
        d,u=heapq.heappop(heap)
        if d>dist[u]+1e-14:continue
        for v in adj[u]:
            if source[v]:continue
            candidate=d+cost[u]
            if candidate<dist[v]-1e-14 or (abs(candidate-dist[v])<=1e-14 and origin[u]<origin[v]):
                dist[v]=candidate;nxt[v]=u;origin[v]=origin[u]
                heapq.heappush(heap,(candidate,int(v)))
    paths=[]
    for i in range(n):
        path=[i];seen={i};j=i
        while not source[j]:
            j=int(nxt[j])
            if j<0 or j in seen:raise ValueError("Best source path absent or cyclic")
            path.append(j);seen.add(j)
        paths.append(path)
        if origin[i]!=j:raise ValueError("Best source identity inconsistent")
    return np.exp(-dist),paths,origin


def _confidence(p,n):
    return np.sqrt(np.clip(p*(1-p),0,1)/np.maximum(n,1))


def static_reliability():
    with np.load(FORMAL/"Stage 1 Output_expanded/physical_inputs_2pc50.npz",allow_pickle=False) as z:
        ids=z["station_ids"].astype(str).tolist()
    eu,ev,adj,degree,source,static=_graph_arrays(ids)
    if len(ids)!=92 or len(eu)!=318 or source.sum()!=14:raise ValueError("Frozen graph/source identity differs")
    source_ix=np.flatnonzero(source).astype(np.int16)
    frame=pd.read_csv(ROOT/"Data/Substations_PGA_IDW_CEC_expanded.csv",dtype={"ID":str}).set_index("ID").loc[ids]
    pga=frame.PGA_2pc50.to_numpy(float)
    mu=frame[[f"mu_DS{i}" for i in range(1,5)]].to_numpy(float)
    beta=frame[[f"beta_DS{i}" for i in range(1,5)]].to_numpy(float)
    exceed,ds=production_ds_probabilities(pga,mu,beta)
    r=ds[:,:2].sum(axis=1)
    analytic_best,paths,best_source_ix=best_paths(ids,eu,ev,source,r)
    rng=np.random.default_rng(np.random.SeedSequence([20260926,3,991]))
    states=rng.random((N,92))<r
    f,c,conditional,by_source=_component_counts(states,eu,ev,adj,degree,source_ix,np.array(CHECKPOINTS))
    final_f=f[-1];final_c=c[-1]
    full_raw=conditional[-1]/N
    indiv_raw=by_source[-1]/N
    per_source_path=np.column_stack([
        best_paths(ids,eu,ev,np.arange(92)==s,r)[0] for s in source_ix])
    indiv=np.maximum(indiv_raw,per_source_path)
    # A finite 100k draw cannot resolve rare paths with probability <<1/N.
    # Enforce the known analytical best-path lower bound transparently and
    # retain the unadjusted MC estimate/count alongside it.
    full=np.maximum(full_raw,analytic_best)
    rconn=r*full
    best_source=np.max(indiv,axis=1)
    empirical_best=np.array([(states[:,path[1:]].all(axis=1)).mean()
                             for i,path in enumerate(paths)])
    # Within the same draws, the best-path event is a subset of the full event.
    if np.any(full_raw+1e-15<empirical_best):raise ValueError("Best path exceeds full network in common draws")
    analytic_delta=full-analytic_best
    se=_confidence(full_raw,N)
    if np.any(analytic_delta < -1e-15) or np.any(full+1e-15<best_source):
        raise ValueError("Known path/source lower bound violated")
    # Wilson interval for the raw conditional MC proportion, including zero hits.
    z=1.96
    center=(full_raw+z*z/(2*N))/(1+z*z/N)
    half=z*np.sqrt(full_raw*(1-full_raw)/N+z*z/(4*N*N))/(1+z*z/N)
    tracts,pop,W,station_pop=mapping_matrix(ids)
    roles=pd.read_csv(ROOT/"Revision_Mapping_Gate/SOURCE_NODE_EVIDENCE_CROSSWALK.csv",dtype={"July_ID":str})
    role_by_id=roles.set_index("July_ID")["original_source_type"].to_dict()
    source_labels=[ids[i] for i in source_ix]
    rows=[]
    for i,station in enumerate(ids):
        row=dict(station_id=station,station_name=frame.iloc[i].NAME,pga_g=pga[i],
                 fragility_class=frame.iloc[i].fragility_class,is_core_source=bool(source[i]),
                 source_role=role_by_id.get(station,"non-source"),
                 r_i=r[i],P_DS0=ds[i,0],P_DS1=ds[i,1],P_DS2=ds[i,2],P_DS3=ds[i,3],P_DS4=ds[i,4],
                 R_best_path=analytic_best[i],R_best_path_common_draws=empirical_best[i],
                 R_path_full=full[i],R_path_full_MC_raw=full_raw[i],
                 R_path_full_MC_count=int(conditional[-1,i]),
                 R_path_MC_wilson95_lower=max(analytic_best[i],center[i]-half[i]),
                 R_path_MC_wilson95_upper=max(analytic_best[i],center[i]+half[i]),
                 full_MC_below_exact_path_bound=bool(full_raw[i]<analytic_best[i]),
                 R_conn_full=rconn[i],
                 Delta_R_redundancy=analytic_delta[i],
                 Delta_R_redundancy_common_draws=full[i]-empirical_best[i],
                 R_path_mc_se=se[i],functional_draw_count=int(final_f[i]),
                 best_source=ids[best_source_ix[i]],best_path_station_ids="|".join(ids[j] for j in paths[i]),
                 best_path_length_edges=len(paths[i])-1,
                 best_individual_source_reliability=best_source[i],
                 any_source_reliability=full[i],Delta_R_source=full[i]-best_source[i],
                 population_dependency_weight=station_pop[i],
                 intact_reachable_sources=int(static[i,3]),
                 intact_edge_disjoint_paths=int(static[i,4]),
                 intact_node_disjoint_paths=int(static[i,5]),
                 intact_single_path=bool(static[i,8]))
        row.update({f"R_to_source_{sid}":indiv[i,s] for s,sid in enumerate(source_labels)})
        rows.append(row)
    station=pd.DataFrame(rows)
    station.to_csv(ROOT/"SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv",index=False)
    conn=np.asarray(W @ rconn).ravel()
    best=np.asarray(W @ (r*analytic_best)).ravel()
    tract=pd.DataFrame(dict(tract_id=tracts,population=pop,
        expected_connected_dependency_mass=conn,
        best_single_path_dependency_mass=best,
        redundancy_gain_dependency_mass=conn-best,
        expected_conditional_path_dependency=np.asarray(W @ full).ravel()))
    tract.to_csv(ROOT/"SOURCE_TERMINAL_TRACT_RELIABILITY_2PC50.csv",index=False)
    convergence=[]
    for ix,count in enumerate(CHECKPOINTS):
        path=conditional[ix]/count
        connection=r*path
        convergence.append(dict(draws=count,population_weighted_R_path=float(station_pop@path),
            population_weighted_R_conn=float(station_pop@connection),
            max_path_mc_se=float(_confidence(path,count).max()),
            mean_absolute_path_change_from_100k=float(np.average(abs(path-full_raw),weights=station_pop)),
            max_absolute_path_change_from_100k=float(np.max(abs(path-full_raw)))))
    old=pd.read_csv(ROOT/"SUBSTATION_CONNECTIVITY_RELIABILITY.csv",dtype={"station_id":str})
    old=old[old.hazard==HAZARD].set_index("station_id").loc[ids]
    comparison=dict(max_abs_vs_prior_100k_R_path=float(np.max(abs(full-old.R_path.to_numpy(float)))),
                    pop_weighted_abs_vs_prior_100k_R_path=float(station_pop@abs(full-old.R_path.to_numpy(float))),
                    max_abs_vs_prior_100k_R_conn=float(np.max(abs(r*full_raw-old.R_conn.to_numpy(float)))),
                    max_abs_unconditional_connection_check=float(np.max(abs(final_c/N-r*full_raw))),
                    raw_MC_below_exact_best_path_count=int((full_raw<analytic_best).sum()),
                    zero_conditional_connection_count=int((conditional[-1]==0).sum()),
                    analytical_lower_bound_used_count=int((full>full_raw).sum()),
                    common_draw_negative_delta_count=int(((full-empirical_best)<-1e-15).sum()))
    return ids,paths,source,station_pop,station,tract,pd.DataFrame(convergence),comparison


def dynamic_reliability(ids,paths,source,station_pop,*,samples=1000):
    ntime=len(TIMES)
    rows=[];aggregate=[]
    for strategy in STRATEGIES:
        functional=np.zeros((ntime,92),np.int64)
        connected=np.zeros_like(functional)
        best=np.zeros_like(functional)
        for n in range(samples):
            with np.load(trajectory_path(HAZARD,strategy,n),allow_pickle=False) as z:
                if z["station_ids"].astype(str).tolist()!=ids:raise ValueError("Frozen station order differs")
                event=z["event_time_hr"]
                F=z["F"].astype(bool)
                C=z["C"].astype(bool)
            position=np.clip(np.searchsorted(event,TIMES,side="right")-1,0,len(event)-1)
            state=F[position];full=state&C[position]
            path_state=np.column_stack([state[:,path].all(axis=1) for path in paths])
            if not np.all(path_state<=full):raise ValueError("Fixed best-path event not subset of full connection")
            functional+=state;connected+=full;best+=path_state
        pF=functional/samples
        pconn=connected/samples
        pbest=best/samples
        ppath=np.divide(connected,functional,out=np.full((ntime,92),np.nan),where=functional>0)
        pbestcond=np.divide(best,functional,out=np.full((ntime,92),np.nan),where=functional>0)
        for ti,time in enumerate(TIMES):
            for i,station in enumerate(ids):
                rows.append(dict(strategy=strategy,time_hr=time,station_id=station,
                    functional_count=int(functional[ti,i]),draws=samples,
                    P_functional=pF[ti,i],R_path_full_conditional=ppath[ti,i],
                    R_conn_full=pconn[ti,i],R_best_fixed_path_conditional=pbestcond[ti,i],
                    Delta_R_redundancy_conditional=ppath[ti,i]-pbestcond[ti,i],
                    R_best_fixed_path_unconditional=pbest[ti,i]))
            aggregate.append(dict(strategy=strategy,time_hr=time,
                population_dependency_weighted_R_conn=float(station_pop@pconn[ti]),
                population_dependency_weighted_best_path_connection=float(station_pop@pbest[ti]),
                population_dependency_weighted_redundancy_gain=float(station_pop@(pconn[ti]-pbest[ti])),
                population_dependency_weighted_R_path_conditional=float(station_pop@np.nan_to_num(ppath[ti])),
                population_dependency_weighted_best_path_conditional=float(station_pop@np.nan_to_num(pbestcond[ti]))))
        print(json.dumps(dict(strategy=strategy,read_only_trajectories=samples)),flush=True)
    station=pd.DataFrame(rows);station.to_csv(ROOT/"SOURCE_TERMINAL_DYNAMIC_STATION_2PC50.csv",index=False)
    summary=pd.DataFrame(aggregate);summary.to_csv(ROOT/"SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv",index=False)
    return station,summary


def main(*,dynamic=True):
    ids,paths,source,weights,station,tract,conv,comparison=static_reliability()
    conv.to_csv(ROOT/"SOURCE_TERMINAL_MC_CONVERGENCE_2PC50.csv",index=False)
    if dynamic:dynamic_reliability(ids,paths,source,weights)
    print(json.dumps(dict(stations=92,edges=318,core_sources=14,draws=N,
        comparison=comparison,convergence=conv.to_dict("records"))),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--static-only",action="store_true")
    args=p.parse_args();main(dynamic=not args.static_only)
