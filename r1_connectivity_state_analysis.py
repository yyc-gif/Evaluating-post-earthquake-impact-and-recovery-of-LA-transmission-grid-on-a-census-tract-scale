"""Read-only route composition of frozen July92 formal event trajectories.

This is an analysis of the existing binary-gated availability. No trajectory,
mapping, gate, or physical sample is recomputed. Event intervals use the
left-state convention of the frozen formal experiment.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy import sparse

from r1_dynamic_topology_kernel import characterize_mask, station_independent_routes_mask
from r1_formal_dynamic_topology import _graph_arrays

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "Formal_Experiment_20260923"
RESULTS = FORMAL / "Formal_Reviewer_Results"
HAZARDS = ("Northridge", "SanFernando", "LongBeach", "2pc50")
STRATEGIES = ("unconstrained", "centrality-first", "impact-first",
              "betweenness-first", "degree-first", "closeness-first",
              "hospital-first", "random", "vulnerability-first")
TRACT_STRATEGIES = ("hospital-first", "impact-first", "centrality-first",
                    "vulnerability-first")
GRID = np.arange(481, dtype=np.float64)
CLASS_NAMES = ("Disconnected", "Active source", "One route", "Multiple routes")


def mapping_matrix(ids):
    frame = pd.read_csv(ROOT / "Data/JULY_UTILITY_CONSTRAINED_92.csv",
                        dtype={"tract_id": str, "substation_id": str})
    frame.tract_id = frame.tract_id.str.zfill(11)
    tracts = sorted(frame.tract_id.unique())
    assert len(tracts) == 2315
    si = {s:i for i,s in enumerate(ids)}
    ti = {t:i for i,t in enumerate(tracts)}
    W = sparse.csr_matrix((frame.weight.to_numpy(float),
                           ([ti[t] for t in frame.tract_id],
                            [si[s] for s in frame.substation_id])),
                          shape=(2315,92))
    assert np.allclose(np.asarray(W.sum(axis=1)).ravel(),1,atol=1e-12)
    pop = frame[["tract_id","population"]].drop_duplicates().set_index("tract_id")
    p = pop.loc[tracts,"population"].to_numpy(float)
    assert np.all(np.isfinite(p)) and np.all(p>=0) and p.sum()>0
    station_weight = np.asarray(W.T @ (p/p.sum())).ravel()
    return tracts,p,W,station_weight


def state_class(q, routes):
    functional = q[:,0] == 1
    local = q[:,1] == 1
    connected = q[:,2] == 1
    cls = np.zeros(len(q),dtype=np.uint8)
    cls[local] = 1
    cls[functional & connected & ~local & (routes==1)] = 2
    cls[functional & connected & ~local & (routes>=2)] = 3
    if np.any(functional & connected & (cls==0)):
        raise ValueError("Functional connected station has no route class")
    if np.any((cls>0) != (functional & connected)):
        raise ValueError("Route classes do not partition connected stations")
    if np.any((~connected) != (cls==0)):
        raise ValueError("Disconnected class disagrees with production C")
    return cls


def trajectory_path(hazard, strategy, sample):
    stem = f"{hazard}__evaluation_{sample:04d}.npz"
    if strategy == "vulnerability-first":
        return FORMAL/"Equity_Amendment"/"T"/hazard/"C57_D1"/stem
    return FORMAL/"Formal_Trajectories"/hazard/"C57_D1"/strategy/stem


def sample(hazard, n, *, validate_only=False):
    stem = f"{hazard}__evaluation_{n:04d}"
    dyn_path = FORMAL/"Formal_Dynamic_Topology"/hazard/(stem+"__DYNAMIC.npz")
    with np.load(dyn_path, allow_pickle=False) as z:
        ids = z["station_ids"].astype(str).tolist()
        masks = z["unique_functional_masks"]
        old = z["unique_state_metrics"]
        indices = z["event_state_index"]
        offsets = z["event_offsets"]
        runs = z["run_names"].astype(str).tolist()
    assert len(ids)==92 and len(set(ids))==92
    eu,ev,adj,deg,sources,_ = _graph_arrays(ids)
    assert sources.sum()==14 and len(eu)==318
    tracts,p,W,station_weight = mapping_matrix(ids)
    original = {name:i for i,name in enumerate(runs)}
    selected = [original["C57_D1|"+strategy] for strategy in STRATEGIES
                if strategy!="vulnerability-first"]
    needed = np.unique(np.concatenate([indices[offsets[j]:offsets[j+1]]
                                       for j in selected]))
    cache = {}
    for pos in needed:
        active = np.unpackbits(masks[pos])[:92].astype(np.bool_)
        q = old[pos]
        routes = station_independent_routes_mask(active,sources,eu,ev)
        cls = state_class(q,routes)
        cache[np.packbits(active).tobytes()] = (q,routes,cls)
    def lookup(F):
        key = np.packbits(F.astype(np.uint8)).tobytes()
        found = cache.get(key)
        if found is None:
            q = characterize_mask(F,sources,eu,ev,adj,deg)
            routes = station_independent_routes_mask(F,sources,eu,ev)
            found = (q,routes,state_class(q,routes))
            cache[key] = found
        return found

    summaries=[]
    interval_rows=[]
    hourly={}
    tract_rows=[]
    cross=defaultdict(float)
    coverage=0
    max_tract_error=0.
    max_c_error=0.
    for strategy in STRATEGIES:
        path=trajectory_path(hazard,strategy,n)
        if not path.is_file():
            raise FileNotFoundError(path)
        with np.load(path,allow_pickle=False) as z:
            if z["station_ids"].astype(str).tolist()!=ids:
                raise ValueError("Frozen station order changed")
            F=z["F"].astype(np.bool_)
            C=z["C"].astype(np.bool_)
            e=z["e"].astype(np.float64)
            times=z["event_time_hr"].astype(np.float64)
        if times[0]!=0 or times[-1]!=480 or np.any(np.diff(times)<0):
            raise ValueError("Frozen event horizon invalid")
        if F.shape!=C.shape or F.shape!=e.shape or F.shape[1]!=92:
            raise ValueError("Frozen state shape invalid")
        dt=np.diff(times)
        component=np.zeros((len(times),3),dtype=np.float64)
        diversity=np.zeros((len(times),2),dtype=np.float64)
        route_count=np.zeros((len(times),92),dtype=np.int16)
        source_count=np.zeros((len(times),92),dtype=np.int16)
        station_integral=np.zeros((3,92),dtype=np.float64)
        total_station=np.zeros(92,dtype=np.float64)
        for k in range(len(times)):
            q,routes,cls=lookup(F[k])
            if not np.array_equal(q[:,2].astype(bool),C[k]):
                raise ValueError("Recomputed C differs from frozen production C")
            if np.any((cls>0)!=(e[k]>0)):
                raise ValueError("Service and connected route classification differ")
            max_c_error=max(max_c_error,float(np.max(np.abs(q[:,2]-C[k].astype(int)))))
            route_count[k]=routes
            source_count[k]=q[:,3]
            coverage+=int(F[k].sum())
            if sum(int(np.count_nonzero(F[k] & (cls==j))) for j in range(4))!=int(F[k].sum()):
                raise ValueError("Functional classification coverage failed")
            station_partition=np.zeros(92,dtype=np.float64)
            for j in range(1,4):
                part=e[k]*(cls==j)
                station_partition+=part
                component[k,j-1]=float(part @ station_weight)
                if k<len(dt):
                    station_integral[j-1]+=dt[k]*part
            # W is linear: exact station equality proves the same identity
            # for every tract at this event, not just in the population mean.
            if not np.array_equal(station_partition,e[k]):
                raise ValueError("Event-by-station service partition fails")
            total=float(e[k] @ station_weight)
            if abs(total-component[k].sum())>1e-12:
                raise ValueError("Station service partition fails")
            diversity[k,0]=float((e[k]*(q[:,3]==1)) @ station_weight)
            diversity[k,1]=float((e[k]*(q[:,3]>=2)) @ station_weight)
            if abs(total-diversity[k].sum())>1e-12:
                raise ValueError("Source diversity partition fails")
            if k==len(dt):
                continue
            total_station+=dt[k]*e[k]
            interval_rows.append((hazard,n,strategy,float(times[k]),float(times[k+1]),
                                  total,*component[k],*diversity[k]))
            # Supporting checks use service-hours and exact interval lengths.
            amount=e[k]*station_weight*dt[k]
            old_node=q[:,5]
            edge=q[:,4]
            for j in (2,3):
                mask=cls==j
                cross[(hazard,strategy,"route_"+str(j))]+=float(amount[mask].sum())
                cross[(hazard,strategy,"old_node_1|route_"+str(j))]+=float(amount[mask & (old_node==1)].sum())
                cross[(hazard,strategy,"old_node_2plus|route_"+str(j))]+=float(amount[mask & (old_node>=2)].sum())
                cross[(hazard,strategy,"edge_1|route_"+str(j))]+=float(amount[mask & (edge==1)].sum())
                cross[(hazard,strategy,"single_flag|route_"+str(j))]+=float(amount[mask & (q[:,8]==1)].sum())
                cross[(hazard,strategy,"bridge|route_"+str(j))]+=float(amount[mask & (q[:,6]==1)].sum())
                cross[(hazard,strategy,"articulation|route_"+str(j))]+=float(amount[mask & (q[:,7]==1)].sum())
                cross[(hazard,strategy,"one_source|route_"+str(j))]+=float(amount[mask & (q[:,3]==1)].sum())
                cross[(hazard,strategy,"multi_source|route_"+str(j))]+=float(amount[mask & (q[:,3]>=2)].sum())
        tract_parts=np.stack([np.asarray(W @ v).ravel() for v in station_integral])
        tract_total=np.asarray(W @ total_station).ravel()
        err=float(np.max(np.abs(tract_parts.sum(axis=0)-tract_total)))
        max_tract_error=max(max_tract_error,err)
        if err>1e-9:
            raise ValueError(f"Tract service integral partition: {err}")
        integrals=dt @ component[:-1]
        diversity_integrals=dt @ diversity[:-1]
        valid=(route_count[:-1]>=0)&(source_count[:-1]>0)
        key=(route_count[:-1].astype(np.int32)*15+source_count[:-1]).ravel()
        weight=(e[:-1]*station_weight[None,:]*dt[:,None]).ravel()
        hist=np.bincount(key[valid.ravel()],weights=weight[valid.ravel()],minlength=93*15)
        for code in np.flatnonzero(hist):
            cross[(hazard,strategy,f"routes_{code//15}|sources_{code%15}")]+=float(hist[code])
        connected=float(integrals.sum())
        if not np.isclose(connected,float(dt @ (e[:-1] @ station_weight)),atol=1e-9):
            raise ValueError("Population-weighted service integral differs")
        summaries.append(dict(hazard=hazard,realization_id=n,strategy=strategy,
                              connected_service_hr=connected,
                              active_source_service_hr=float(integrals[0]),
                              one_route_service_hr=float(integrals[1]),
                              multiple_route_service_hr=float(integrals[2]),
                              one_source_service_hr=float(diversity_integrals[0]),
                              multiple_source_service_hr=float(diversity_integrals[1]),
                              multiple_route_share=float(integrals[2]/connected) if connected else np.nan))
        ix=np.clip(np.searchsorted(times,GRID,side="right")-1,0,len(times)-1)
        hourly[strategy]=np.column_stack((component[ix].sum(axis=1),component[ix],
                                          diversity[ix]))
        if hazard=="2pc50" and strategy in TRACT_STRATEGIES:
            frac=np.divide(tract_parts,tract_total,
                           out=np.full_like(tract_parts,np.nan),where=tract_total>0)
            tract_rows.append((strategy,tract_total,tract_parts,frac))
    return dict(summary=summaries,intervals=interval_rows,hourly=hourly,
                tract=tract_rows,cross=cross,tracts=tracts,pop=p,
                coverage=coverage,max_tract_error=max_tract_error,
                max_c_error=max_c_error,cache_size=len(cache))


def run(start=0,stop=1000,validate_only=False):
    if not validate_only and (start!=0 or stop!=1000):
        raise ValueError("Formal outputs require all 1000 samples per hazard")
    RESULTS.mkdir(exist_ok=True)
    summary=[]
    cross=defaultdict(float)
    hourly=defaultdict(lambda:np.zeros((481,6),dtype=np.float64))
    tract_acc={}
    event_path=RESULTS/"FORMAL_CONNECTIVITY_EVENT_INTERVALS.parquet"
    writer=None
    max_err=max_c=0.
    coverage=0
    total_cases=0
    interval_count=0
    for hazard in HAZARDS:
        for n in range(start,stop):
            out=sample(hazard,n,validate_only=validate_only)
            if validate_only:
                print(json.dumps(dict(hazard=hazard,sample=n,
                                      cache_states=out["cache_size"],
                                      max_tract_error=out["max_tract_error"])),flush=True)
                return
            summary.extend(out["summary"])
            total_cases+=len(out["summary"])
            interval_count+=len(out["intervals"])
            coverage+=out["coverage"]
            max_err=max(max_err,out["max_tract_error"])
            max_c=max(max_c,out["max_c_error"])
            for strategy,value in out["hourly"].items():
                hourly[(hazard,strategy)]+=value
            for key,value in out["cross"].items():
                cross[key]+=value
            if hazard=="2pc50":
                for strategy,total,parts,frac in out["tract"]:
                    if strategy not in tract_acc:
                        tract_acc[strategy]=dict(total=np.zeros_like(total),
                            parts=np.zeros_like(parts),fractions=np.zeros_like(parts),
                            valid=np.zeros_like(parts,dtype=np.int32))
                    a=tract_acc[strategy]
                    a["total"]+=total
                    a["parts"]+=parts
                    valid=np.isfinite(frac)
                    a["fractions"]+=np.where(valid,frac,0)
                    a["valid"]+=valid
            frame=pd.DataFrame(out["intervals"],columns=[
                "hazard","realization_id","strategy","start_hr","end_hr",
                "total_service","active_source_service","one_route_service",
                "multiple_route_service","one_source_service","multiple_source_service"])
            table=pa.Table.from_pandas(frame,preserve_index=False)
            if writer is None:
                writer=pq.ParquetWriter(event_path,table.schema,compression="zstd")
            writer.write_table(table)
            if n%100==0:
                print(json.dumps(dict(hazard=hazard,sample=n,cases=total_cases,
                    max_tract_error=max_err)),flush=True)
    if writer:
        writer.close()
    if total_cases!=36000 or len(tract_acc)!=4 or max_c!=0:
        raise ValueError("Formal baseline case or production C coverage incomplete")
    s=pd.DataFrame(summary)
    frozen=pd.concat([
        pd.read_parquet(FORMAL/"Formal_Results"/
                        "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet"),
        pd.read_parquet(FORMAL/"Equity_Amendment"/
                        "VULNERABILITY_PRIMARY_SUMMARY.parquet")],ignore_index=True)
    frozen=frozen[(frozen.resource_scenario=="C57_D1") &
                  (frozen.mapping=="M1_UTILITY_003") &
                  (frozen.gate=="G1_BASELINE_050") &
                  (frozen.comparison_domain=="mapping_native_domain") &
                  (frozen.strategy_id!="direct-community")]
    parity=s[["hazard","realization_id","strategy","connected_service_hr"]].copy()
    parity["realization_id"]=[f"{h}__evaluation_{int(i):04d}" for h,i in
                               zip(parity.hazard,parity.realization_id)]
    parity=parity.merge(frozen[["hazard","realization_id","strategy_id",
                                 "population_resolved_mass_weighted_burden_hr"]],
                        left_on=["hazard","realization_id","strategy"],
                        right_on=["hazard","realization_id","strategy_id"],
                        validate="one_to_one")
    burden_parity=float(np.max(np.abs(parity.connected_service_hr+
        parity.population_resolved_mass_weighted_burden_hr-480)))
    if len(parity)!=36000 or burden_parity>1e-9:
        raise ValueError("Connected service does not match frozen cumulative burden")
    for src,target in (("active_source","active_source"),
                       ("one_route","one_route"),("multiple_route","multiple_route"),
                       ("one_source","one_source"),("multiple_source","multiple_source")):
        s[target+"_share"]=s[src+"_service_hr"]/s.connected_service_hr
    s.to_parquet(RESULTS/"FORMAL_CONNECTIVITY_REALIZATION_SUMMARY.parquet",index=False)
    cols=[c for c in s if c.endswith("_share") or c.endswith("_service_hr")]
    agg=s.groupby(["hazard","strategy"])[cols].agg(["mean","median","std"]).reset_index()
    agg.columns=["_".join(str(z) for z in col if z) for col in agg.columns]
    for component in ("active_source","one_route","multiple_route",
                      "one_source","multiple_source"):
        agg[component+"_share_pooled"]=(agg[component+"_service_hr_mean"]/
                                          agg["connected_service_hr_mean"])
    agg.to_csv(RESULTS/"FORMAL_CONNECTIVITY_STATE_SUMMARY.csv",index=False)
    pd.DataFrame([dict(hazard=h,strategy=strategy,time_hr=int(t),
                       total_modeled_service=float(values[t,0]/1000),
                       active_source_supported_service=float(values[t,1]/1000),
                       one_route_supported_service=float(values[t,2]/1000),
                       multiple_route_supported_service=float(values[t,3]/1000),
                       one_source_supported_service=float(values[t,4]/1000),
                       multiple_source_supported_service=float(values[t,5]/1000))
                  for (h,strategy),values in hourly.items() for t in range(481)]
                 ).to_csv(RESULTS/"FORMAL_CONNECTIVITY_TIME_SERIES.csv",index=False)
    ref=s[(s.hazard=="2pc50")&(s.strategy=="hospital-first")].set_index("realization_id")
    effects=[]
    for strategy in STRATEGIES:
        if strategy=="hospital-first":
            continue
        other=s[(s.hazard=="2pc50")&(s.strategy==strategy)].set_index("realization_id")
        assert other.index.equals(ref.index)
        for metric in ("one_route_service_hr","multiple_route_service_hr",
                       "multiple_route_share","connected_service_hr"):
            d=other[metric]-ref[metric]
            effects.append(dict(hazard="2pc50",strategy=strategy,reference="hospital-first",
                metric=metric,n=len(d),paired_mean=float(d.mean()),paired_median=float(d.median()),
                paired_p05=float(d.quantile(.05)),paired_p95=float(d.quantile(.95)),
                fraction_negative=float((d<0).mean())))
    pd.DataFrame(effects).to_csv(RESULTS/"FORMAL_CONNECTIVITY_STRATEGY_EFFECTS.csv",index=False)
    tract_rows=[]
    for strategy,a in tract_acc.items():
        for i,tract in enumerate(out["tracts"]):
            denom=a["total"][i]
            tract_rows.append(dict(tract_id=tract,strategy=strategy,population=out["pop"][i],
                mean_connected_service_hr=float(denom/1000),
                mean_one_route_service_hr=float(a["parts"][1,i]/1000),
                mean_multiple_route_service_hr=float(a["parts"][2,i]/1000),
                one_route_share_pooled=float(a["parts"][1,i]/denom) if denom else np.nan,
                multiple_route_share_pooled=float(a["parts"][2,i]/denom) if denom else np.nan,
                one_route_share_mean=float(a["fractions"][1,i]/a["valid"][1,i]) if a["valid"][1,i] else np.nan,
                multiple_route_share_mean=float(a["fractions"][2,i]/a["valid"][2,i]) if a["valid"][2,i] else np.nan,
                valid_realizations=int(a["valid"][1,i])))
    pd.DataFrame(tract_rows).to_parquet(RESULTS/"FORMAL_CONNECTIVITY_TRACT_EFFECTS.parquet",index=False)
    check=pd.DataFrame([dict(hazard=h,strategy=strategy,comparison=name,
                             time_population_weighted_service_hours=value)
                        for (h,strategy,name),value in cross.items()])
    check.to_csv(RESULTS/"FORMAL_CONNECTIVITY_METRIC_CROSSCHECK.csv",index=False)
    tab=check[check.comparison.str.match(r"routes_\d+\|sources_\d+")].copy()
    extracted=tab.comparison.str.extract(r"routes_(\d+)\|sources_(\d+)")
    tab["station_independent_routes"]=extracted[0].astype(int)
    tab["reachable_active_sources"]=extracted[1].astype(int)
    totals=tab.groupby(["hazard","strategy"]).time_population_weighted_service_hours.transform("sum")
    tab["share_of_non_source_connected_service"]=tab.time_population_weighted_service_hours/totals
    tab.drop(columns="comparison").to_csv(
        RESULTS/"FORMAL_CONNECTIVITY_ROUTE_SOURCE_CROSSTAB.csv",index=False)
    meta=dict(stations=92,edges=318,core_sources=14,physical_samples=4000,
              baseline_trajectories=total_cases,classification_coverage="100%",
              max_production_C_difference=max_c,max_tract_integral_abs_error=max_err,
              event_intervals=interval_count,
              formal_population_burden_parity_n=len(parity),
              formal_population_burden_parity_max_abs_hr=burden_parity,
              vulnerability_first_baseline_per_hazard=1000,
              source_diversity_separate_from_route_count=True,
              state_classes=list(CLASS_NAMES),
              service_share_denominator="Time-integrated population-weighted connected modeled service; pooled shares sum component service-hours over 1000 realizations then divide by total service-hours.",
              horizon_hr=480,production_gate_changed=False,
              trajectory_rerun=False,direct_community_repeated=False)
    (RESULTS/"FORMAL_CONNECTIVITY_STATE_IDENTITY.json").write_text(
        json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(meta,indent=2),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--validate-sample",action="store_true")
    a=p.parse_args()
    run(stop=1,validate_only=True) if a.validate_sample else run()
