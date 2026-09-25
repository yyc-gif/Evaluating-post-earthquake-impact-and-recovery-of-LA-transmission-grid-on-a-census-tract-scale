"""Read-only dynamic topology analysis of frozen formal event archives.

Each sample artifact factors all station-by-event diagnostics into exact unique
functional masks plus event-to-mask indices. No state is sampled or skipped.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

import networkx as nx
import numpy as np
import pandas as pd

from r1_dynamic_topology_kernel import characterize_mask

METRIC_COLUMNS = ("functional", "active_source", "source_connected",
                  "reachable_active_sources", "edge_disjoint_remote_paths_or_local_marker",
                  "node_disjoint_remote_paths_or_local_marker", "bridge_dependent",
                  "articulation_dependent", "single_path", "disconnected")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _graph_arrays(station_ids):
    edge_path = Path("Data/substation_graph_CEC_edges_expanded.csv")
    source_path = Path("Data/source_nodes_core_expanded.csv")
    edge_frame = pd.read_csv(edge_path, dtype={"u":str,"v":str})
    graph = nx.from_pandas_edgelist(edge_frame,"u","v")
    if len(graph) != 92 or len(graph.edges) != 318 or set(graph) != set(station_ids):
        raise ValueError("Frozen July92/318 graph identity changed")
    lookup = {s:i for i,s in enumerate(station_ids)}
    edge = np.asarray([(lookup[str(row.u)],lookup[str(row.v)])
                       for row in edge_frame.itertuples()],dtype=np.int16)
    adjacency = np.zeros((92,92),dtype=np.int16)
    degree = np.zeros(92,dtype=np.int16)
    for u,v in edge:
        adjacency[u,degree[u]],adjacency[v,degree[v]] = v,u
        degree[u] += 1
        degree[v] += 1
    sf = pd.read_csv(source_path,dtype={"ID":str})
    sources = set(sf.loc[sf.level.eq("Core"),"ID"])
    if len(sources) != 14 or not sources <= set(station_ids):
        raise ValueError("Frozen 14 Core sources changed")
    source_flag = np.asarray([s in sources for s in station_ids],dtype=np.bool_)
    static_metrics = characterize_mask(np.ones(92,dtype=np.bool_),source_flag,
                                       edge[:,0],edge[:,1],adjacency,degree)
    return edge[:,0],edge[:,1],adjacency,degree,source_flag,static_metrics


def _case_catalog(root: Path):
    index = json.loads((root/"FORMAL_TRAJECTORY_ARCHIVE_INDEX.json").read_text(encoding="utf-8"))
    if index["case_count"] != 84 or len(index["per_case_count"]) != 84:
        raise ValueError("Formal trajectory case index changed")
    cases = {hazard:[] for hazard in ("Northridge","SanFernando","LongBeach","2pc50")}
    for key,count in index["per_case_count"].items():
        hazard,resource,strategy = key.split("|")
        if count != 1000:
            raise ValueError("Formal archive case does not have 1000 realizations")
        cases[hazard].append((resource,strategy))
    for hazard in cases:
        cases[hazard].sort()
    if [len(cases[h]) for h in cases] != [9,9,9,57]:
        raise ValueError("Formal archive baseline/OFAT case dimensions changed")
    return cases,index


def process_formal_sample(root: Path, hazard: str, sample_index: int,
                          *, output_folder: Path, cases=None) -> dict:
    root = Path(root)
    catalog,index = _case_catalog(root)
    if cases is None:
        cases = catalog[hazard]
    elif cases != catalog[hazard]:
        raise ValueError("Partial cases are not a formal sample")
    stem = f"{hazard}__evaluation_{sample_index:04d}"
    sample_path = output_folder/hazard/(stem+"__DYNAMIC.npz")
    meta_path = output_folder/hazard/(stem+"__DYNAMIC.json")
    if sample_path.exists() or meta_path.exists():
        if not sample_path.exists() or not meta_path.exists():
            raise ValueError("Incomplete dynamic topology sample artifact")
        existing = json.loads(meta_path.read_text(encoding="utf-8"))
        if existing["npz_sha256"] != _sha(sample_path) or existing["matrix_id"] != "JULY92_REVIEWER_REVISION_FINAL_V1":
            raise ValueError("Dynamic topology resume identity mismatch")
        return dict(status="reused",**{k:v for k,v in existing.items() if k!="status"})
    output_folder.joinpath(hazard).mkdir(parents=True,exist_ok=True)
    archive_root = root/"Formal_Trajectories"/hazard
    first = archive_root/cases[0][0]/cases[0][1]/(stem+".npz")
    with np.load(first,allow_pickle=False) as z:
        ids = z["station_ids"].astype(str).tolist()
    if len(ids) != 92 or len(set(ids)) != 92:
        raise ValueError("Formal station IDs not unique July92")
    edge_u,edge_v,adj,deg,source_flag,static_metrics = _graph_arrays(ids)
    cache = {}
    masks=[]
    metrics=[]
    event_indices=[]
    event_times=[]
    offsets=[0]
    run_names=[]
    run_source_integral=[]
    run_prior_single=[]
    run_prior_bridge=[]
    run_prior_articulation=[]
    run_prior_fallback=[]
    run_source_clearance=[]
    functional_changes=0
    cache_hits=0
    cache_misses=0
    physical_hash=None
    max_source_integral_difference=0.
    for resource,strategy in cases:
        archive = archive_root/resource/strategy/(stem+".npz")
        manifest = json.loads(archive.with_suffix(".json").read_text(encoding="utf-8"))
        identity=manifest["identity"]
        if (manifest["status"]!="FORMAL_FROZEN_MATRIX_V1" or
                identity["matrix_id"]!="JULY92_REVIEWER_REVISION_FINAL_V1" or
                identity["hazard"]!=hazard or identity["realization_id"]!=stem or
                identity["resource_scenario"]!=resource or identity["strategy"]!=strategy or
                identity["event_horizon_hr"]!=480):
            raise ValueError("Formal event archive identity mismatch")
        if physical_hash is None:
            physical_hash=identity["physical_sample_hash"]
        elif physical_hash!=identity["physical_sample_hash"]:
            raise ValueError("Strategy/resource physical sample mismatch")
        with np.load(archive,allow_pickle=False) as z:
            if not np.array_equal(z["station_ids"].astype(str),ids):
                raise ValueError("Station order changed across formal strategy archive")
            F=z["F"].astype(np.bool_)
            C=z["C"].astype(np.int16)
            loss=z["L_source"].astype(np.float64)
            times=z["event_time_hr"].astype(np.float64)
        if (times[0]!=0 or times[-1]!=480 or np.any(np.diff(times)<0) or
                F.shape!=C.shape or F.shape!=loss.shape or F.shape[1]!=92):
            raise ValueError("Malformed frozen event state")
        run_names.append(f"{resource}|{strategy}")
        last_connected = static_metrics.copy()
        seen_connected = np.zeros(92,dtype=np.bool_)
        source_integral=np.zeros(92)
        prior_single=np.zeros(92)
        prior_bridge=np.zeros(92)
        prior_articulation=np.zeros(92)
        prior_fallback=np.zeros(92)
        clearance=0.
        previous_key=None
        for event in range(len(times)):
            key=np.packbits(F[event].astype(np.uint8)).tobytes()
            if event == 0 or key != previous_key:
                functional_changes+=1
            previous_key=key
            pos=cache.get(key)
            if pos is None:
                q=characterize_mask(F[event],source_flag,edge_u,edge_v,adj,deg)
                pos=len(metrics)
                cache[key]=pos
                masks.append(np.frombuffer(key,dtype=np.uint8).copy())
                metrics.append(q)
                cache_misses+=1
            else:
                q=metrics[pos]
                cache_hits+=1
            if not np.array_equal(q[:,2],C[event]):
                raise ValueError("Cached source-connected mask differs from frozen production C")
            event_indices.append(pos)
            event_times.append(times[event])
            connected = (q[:,0]==1)&(q[:,2]==1)
            last_connected[connected]=q[connected]
            seen_connected[connected]=True
            if event==len(times)-1:
                continue
            dt=times[event+1]-times[event]
            if dt<0:
                raise ValueError("Event times decreased")
            amount=loss[event]*dt
            if np.any((amount>0)&((q[:,0]!=1)|(q[:,2]!=0))):
                raise ValueError("Source loss attributed to a functional connected station")
            source_integral+=amount
            prior_single+=amount*(last_connected[:,8]==1)
            prior_bridge+=amount*(last_connected[:,6]==1)
            prior_articulation+=amount*(last_connected[:,7]==1)
            prior_fallback+=amount*(~seen_connected)
            if amount.sum()>0:
                clearance=times[event+1]
        offsets.append(len(event_indices))
        # Match the retained independent station integral for every case/sample.
        integral_path=root/"Formal_Offline_Evaluation"/f"{hazard}__{resource}__{strategy}__INTEGRALS.npz"
        with np.load(integral_path,allow_pickle=False) as z:
            reference=z["G1_BASELINE_050__L_source"][sample_index]
            if not np.array_equal(z["station_ids"].astype(str),ids):
                raise ValueError("Independent integral station order changed")
        diff=float(np.max(np.abs(reference-source_integral)))
        max_source_integral_difference=max(max_source_integral_difference,diff)
        if diff>1e-10:
            raise ValueError(f"Dynamic source integral differs from frozen offline result: {diff}")
        run_source_integral.append(source_integral)
        run_prior_single.append(prior_single)
        run_prior_bridge.append(prior_bridge)
        run_prior_articulation.append(prior_articulation)
        run_prior_fallback.append(prior_fallback)
        run_source_clearance.append(clearance)
    args=dict(station_ids=np.asarray(ids),metric_columns=np.asarray(METRIC_COLUMNS),
              unique_functional_masks=np.asarray(masks,dtype=np.uint8),
              unique_state_metrics=np.asarray(metrics,dtype=np.int16),
              run_names=np.asarray(run_names),event_offsets=np.asarray(offsets,dtype=np.int32),
              event_times=np.asarray(event_times,dtype=np.float64),
              event_state_index=np.asarray(event_indices,dtype=np.int32),
              source_integral_hr=np.asarray(run_source_integral),
              source_prior_single_path_hr=np.asarray(run_prior_single),
              source_prior_bridge_hr=np.asarray(run_prior_bridge),
              source_prior_articulation_hr=np.asarray(run_prior_articulation),
              source_prior_static_fallback_hr=np.asarray(run_prior_fallback),
              source_loss_clearance_hr=np.asarray(run_source_clearance))
    temporary=sample_path.with_suffix(".tmp.npz")
    np.savez_compressed(temporary,**args)
    temporary.replace(sample_path)
    result=dict(status="FORMAL_FROZEN_MATRIX_V1",matrix_id="JULY92_REVIEWER_REVISION_FINAL_V1",
                hazard=hazard,realization_id=stem,physical_sample_hash=physical_hash,
                run_count=len(cases),event_state_count=len(event_indices),
                functional_change_states=functional_changes,cache_hits=cache_hits,
                cache_misses=cache_misses,cache_hit_fraction=cache_hits/len(event_indices),
                source_integral_parity_max_abs_hr=max_source_integral_difference,
                metric_columns=list(METRIC_COLUMNS),
                source_local_path_encoding="negative = -(remote_path_count+1); local own source never counted as upstream path",
                npz_sha256=_sha(sample_path))
    meta_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def execute_dynamic_topology(root: Path, *, start=0, stop=1000, hazards=None) -> dict:
    root=Path(root)
    cases,index=_case_catalog(root)
    if hazards is None:
        hazards=list(cases)
    out=root/"Formal_Dynamic_Topology"
    total=0
    hits=misses=events=0
    begun=time.time()
    for hazard in hazards:
        for sample in range(start,stop):
            info=process_formal_sample(root,hazard,sample,output_folder=out,cases=cases[hazard])
            total+=1
            hits+=info["cache_hits"]
            misses+=info["cache_misses"]
            events+=info["event_state_count"]
            if total%100==0:
                print(json.dumps(dict(samples=total,hazard=hazard,sample=sample,
                                      states=events,hits=hits,misses=misses,
                                      elapsed_s=round(time.time()-begun,1))),flush=True)
    return dict(samples=total,event_states=events,cache_hits=hits,cache_misses=misses,
                elapsed_s=time.time()-begun)


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--start",type=int,default=0)
    parser.add_argument("--stop",type=int,default=1000)
    parser.add_argument("--hazard",action="append")
    a=parser.parse_args()
    print(json.dumps(execute_dynamic_topology(a.root,start=a.start,stop=a.stop,
                                               hazards=a.hazard),indent=2),flush=True)
