"""Offline k=1/2/3 source-route requirements on frozen July92 event states.

No physical sampling, scheduling, recovery simulation, mapping generation, or
production gate mutation occurs here. The saved event clock and raw f are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse

from la_grid.diagnostics.r1_connectivity_state_analysis import HAZARDS, STRATEGIES, trajectory_path
from la_grid.diagnostics.r1_dynamic_topology_kernel import station_independent_routes_mask
from la_grid.diagnostics.r1_formal_dynamic_topology import _graph_arrays
from la_grid.revision.formal.offline import weighted_gini_exact

from la_grid.paths import REPO_ROOT as ROOT
FORMAL = ROOT / "Formal_Experiment_20260923"
OUT = FORMAL / "Formal_Reviewer_Results"
MAPPING = ROOT / "Data/JULY_UTILITY_CONSTRAINED_92.csv"
META = ROOT / "provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv"
REF = "hospital-first"


def inputs(ids):
    edges_u, edges_v, _, _, source, _ = _graph_arrays(ids)
    m = pd.read_csv(MAPPING, dtype={"tract_id": str, "substation_id": str})
    m.tract_id = m.tract_id.str.zfill(11)
    # Offline G1 saved tract arrays in the M1 CSV's first-occurrence row
    # order, inherited from July rather than lexicographic FIPS order.
    tracts = m.tract_id.drop_duplicates().to_numpy(str)
    assert len(tracts) == 2315 and len(ids) == 92 and len(edges_u) == 318 and source.sum() == 14
    ti = {x:i for i,x in enumerate(tracts)}
    si = {x:i for i,x in enumerate(ids)}
    W = sparse.csr_matrix((m.weight.to_numpy(float),
                           ([ti[x] for x in m.tract_id], [si[x] for x in m.substation_id])),
                          shape=(2315,92))
    meta = pd.read_csv(META, dtype={"tract_id": str}).set_index("tract_id").reindex(tracts)
    population = meta.population.to_numpy(float)
    quartile = meta.SOVI_quartile.to_numpy(str)
    hospital = meta.hospital_tract.to_numpy(bool)
    if not np.allclose(np.asarray(W.sum(axis=1)).ravel(),1.,atol=1e-12):
        raise ValueError("Frozen M1 weights do not sum to one")
    if not (np.isfinite(population).all() and np.isin(quartile,["Q1","Q2","Q3","Q4"]).all()):
        raise ValueError("Frozen tract metadata incomplete")
    return edges_u,edges_v,source,W,tracts,population,quartile,hospital


def gate_from_routes(f, F, routes, source, k):
    eligible = (routes >= k) | (F & source[None,:])
    return f * F * eligible


def thresholds(times, service):
    out = {}
    for threshold,label in ((.5,"T50"),(.8,"T80")):
        reached = np.flatnonzero(service >= threshold)
        out[label] = float(times[reached[0]]) if len(reached) else np.nan
        out[label+"_unreached"] = int(len(reached)==0)
    return out


def summarize(times, e, W, p, q, hospital, station_mass, resolved):
    dt = np.diff(times)
    station_loss = dt @ (1-e[:-1])
    mass_loss = np.asarray(W @ station_loss).ravel()
    burden = np.divide(mass_loss,resolved,out=np.full(len(resolved),np.nan),where=resolved>0)
    eligible = resolved>0
    row = dict(population_normalized_burden_hr=float(np.average(burden[eligible],weights=p[eligible])),
               population_resolved_mass_weighted_burden_hr=float(np.dot(p,mass_loss)/np.dot(p,resolved)),
               hospital_burden_hr=float(np.mean(burden[hospital & eligible])),
               population_weighted_gini=weighted_gini_exact(burden,p),
               represented_population=float(p[eligible].sum()),
               unresolved_population=float(p[~eligible].sum()))
    for label in ("Q1","Q2","Q3","Q4"):
        use=(q==label)&eligible
        row[f"{label}_burden_hr"]=float(np.average(burden[use],weights=p[use]))
    row["signed_Q4_minus_Q1_hr"]=row["Q4_burden_hr"]-row["Q1_burden_hr"]
    row["absolute_Q4_minus_Q1_hr"]=abs(row["signed_Q4_minus_Q1_hr"])
    curve=e @ station_mass/np.dot(p,resolved)
    row.update(thresholds(times,curve))
    return row,burden


def feasibility(ids,eu,ev,source,W,tracts,p):
    routes=station_independent_routes_mask(np.ones(92,dtype=np.bool_),source,eu,ev)
    rows=[]
    for k in (1,2,3):
        capable=source|(routes>=k)
        max_service=np.asarray(W @ capable.astype(float)).ravel()
        dep_mass=float(np.dot(p,max_service)/p.sum())
        for i,station in enumerate(ids):
            rows.append(dict(record_type="station",k=k,station_id=station,tract_id="",
                             active_source=bool(source[i]),intact_independent_routes=int(routes[i]),
                             structurally_capable=bool(capable[i]),
                             population_dependency_mass=dep_mass,
                             tract_maximum_service=np.nan,tract_population=np.nan))
        for i,tract in enumerate(tracts):
            rows.append(dict(record_type="tract",k=k,station_id="",tract_id=tract,
                             active_source=np.nan,intact_independent_routes=np.nan,
                             structurally_capable=np.nan,population_dependency_mass=dep_mass,
                             tract_maximum_service=max_service[i],tract_population=p[i]))
    return pd.DataFrame(rows)


def frozen_reference(hazard,strategy):
    if strategy=="vulnerability-first":
        folder=FORMAL/"Equity_Amendment"/"Offline"
    else:
        folder=FORMAL/"Formal_Offline_Evaluation"
    stem=f"{hazard}__C57_D1__{strategy}"
    return folder/(stem+"__INTEGRALS.npz"),folder/(stem+"__SUMMARY.parquet")


def validate_formal_metrics(realization):
    current=realization.loc[realization.k.eq(1)].copy()
    current["realization_id"]=[f"{h}__evaluation_{i:04d}" for h,i in
                               zip(current.hazard,current.realization_id)]
    frozen=[]
    for hazard in HAZARDS:
        for strategy in STRATEGIES:
            _,path=frozen_reference(hazard,strategy)
            frame=pd.read_parquet(path)
            frozen.append(frame[(frame.mapping=="M1_UTILITY_003")&
                                (frame.gate=="G1_BASELINE_050")&
                                (frame.comparison_domain=="mapping_native_domain")])
    joined=current.merge(pd.concat(frozen,ignore_index=True),
        left_on=["hazard","strategy","realization_id"],
        right_on=["hazard","strategy_id","realization_id"],
        validate="one_to_one",suffixes=("_new","_frozen"))
    if len(joined)!=36000:raise ValueError("Frozen G1 metric parity coverage differs")
    pairs={"population_normalized_burden_hr":"population_weighted_normalized_burden_hr",
           "population_resolved_mass_weighted_burden_hr":"population_resolved_mass_weighted_burden_hr",
           "hospital_burden_hr":"hospital_mean_normalized_burden_hr",
           "population_weighted_gini":"burden_gini",
           "signed_Q4_minus_Q1_hr":"signed_Q4_minus_Q1_hr",
           "absolute_Q4_minus_Q1_hr":"absolute_Q4_minus_Q1_hr",
           "T50":"population_T50_hr","T80":"population_T80_hr"}
    pairs.update({f"{q}_burden_hr":f"burden_{q}_hr" for q in ("Q1","Q2","Q3","Q4")})
    errors={}
    for name,former in pairs.items():
        a=joined[name+("_new" if name==former else "")].to_numpy(float)
        b=joined[former+("_frozen" if name==former else "")].to_numpy(float)
        if not np.array_equal(np.isnan(a),np.isnan(b)):
            raise ValueError(f"Frozen G1 NA pattern differs for {name}")
        errors[name]=float(np.nanmax(np.abs(a-b)))
    if max(errors.values())>1e-8:raise ValueError(f"Frozen G1 metric parity failed: {errors}")
    return errors


def run(*,start=0,stop=1000,write=True):
    if write and (start!=0 or stop!=1000):
        raise ValueError("Formal outputs require all 1000 paired realizations")
    with np.load(FORMAL/"Stage 1 Output_expanded/physical_inputs_2pc50.npz",allow_pickle=False) as z:
        ids=z["station_ids"].astype(str).tolist()
    eu,ev,source,W,tracts,p,q,hospital=inputs(ids)
    ftable=feasibility(ids,eu,ev,source,W,tracts,p)
    if write: ftable.to_csv(ROOT/"results"/"diagnostics"/"ROUTE_REQUIREMENT_FEASIBILITY.csv",index=False)
    station_mass=np.asarray(W.T @ p).ravel()
    resolved=np.asarray(W.sum(axis=1)).ravel()
    # Prime the existing tested Numba kernel outside the timed event loop.
    station_independent_routes_mask(np.ones(92,dtype=np.bool_),source,eu,ev)
    results=[]
    tract_totals={}
    parity=dict(station_e=0.,tract_service=0.,tract_burden=0.,population_burden=0.,T50=0.,T80=0.)
    for hazard in HAZARDS:
        for strategy in STRATEGIES:
            ref_npz,ref_parquet=frozen_reference(hazard,strategy)
            if not ref_npz.is_file() or not ref_parquet.is_file():
                raise FileNotFoundError(str(ref_npz))
            with np.load(ref_npz,allow_pickle=False) as z:
                prior_burden=z["M1_UTILITY_003__normalized_burden_hr"].copy()
            prior=pd.read_parquet(ref_parquet)
            prior=prior[(prior.mapping=="M1_UTILITY_003")&(prior.gate=="G1_BASELINE_050")&
                        (prior.comparison_domain=="mapping_native_domain")].set_index("realization_id")
            if len(prior)!=1000:raise ValueError("Frozen G1 summary incomplete")
            accum=np.zeros((3,len(tracts)),dtype=float)
            route_cache={}
            for n in range(start,stop):
                path=trajectory_path(hazard,strategy,n)
                with np.load(path,allow_pickle=False) as z:
                    if z["station_ids"].astype(str).tolist()!=ids:raise ValueError("Frozen station order differs")
                    times=z["event_time_hr"].copy()
                    f=z["f"].copy(); F=z["F"].astype(bool); C=z["C"].astype(bool); frozen_e=z["e"].copy()
                if times[0]!=0 or times[-1]!=480 or np.any(np.diff(times)<=0):
                    raise ValueError("Frozen event intervals invalid")
                route=np.empty(F.shape,dtype=np.int16)
                for event,mask in enumerate(F):
                    key=np.packbits(mask).tobytes()
                    found=route_cache.get(key)
                    if found is None:
                        found=station_independent_routes_mask(mask,source,eu,ev)
                        route_cache[key]=found
                    route[event]=found
                for k in (1,2,3):
                    e=gate_from_routes(f,F,route,source,k)
                    summary,burden=summarize(times,e,W,p,q,hospital,station_mass,resolved)
                    accum[k-1]+=burden
                    results.append(dict(hazard=hazard,strategy=strategy,realization_id=n,k=k,**summary))
                    if k==1:
                        parity["station_e"]=max(parity["station_e"],float(np.max(abs(e-frozen_e))))
                        parity["tract_service"]=max(parity["tract_service"],float(np.max(abs(W @ (e-frozen_e).T))))
                        parity["tract_burden"]=max(parity["tract_burden"],float(np.max(abs(burden-prior_burden[n]))))
                        rid=f"{hazard}__evaluation_{n:04d}"
                        frozen=prior.loc[rid]
                        parity["population_burden"]=max(parity["population_burden"],abs(summary["population_resolved_mass_weighted_burden_hr"]-frozen.population_resolved_mass_weighted_burden_hr))
                        for label in ("T50","T80"):
                            old=float(frozen[f"population_{label}_hr"])
                            new=summary[label]
                            if not (np.isnan(old) and np.isnan(new)):
                                parity[label]=max(parity[label],abs(new-old))
                        if max(parity.values())>1e-8:
                            raise ValueError(f"k=1 G1 parity failed {hazard} {strategy} {n}: {parity}")
            for k in (1,2,3):tract_totals[(hazard,strategy,k)]=accum[k-1]/(stop-start)
            print(json.dumps(dict(hazard=hazard,strategy=strategy,samples=stop-start,
                                  route_cache_states=len(route_cache),parity=parity)),flush=True)
    if not write:return parity,pd.DataFrame(results),ftable
    realization=pd.DataFrame(results)
    formal_metric_errors=validate_formal_metrics(realization)
    composition=pd.read_parquet(OUT/"FORMAL_CONNECTIVITY_REALIZATION_SUMMARY.parquet")
    composition["k2_expected_burden"]=(480.-composition.active_source_service_hr-
                                       composition.multiple_route_service_hr)
    k2check=realization.loc[realization.k.eq(2),[
        "hazard","strategy","realization_id","population_resolved_mass_weighted_burden_hr"]].merge(
        composition[["hazard","strategy","realization_id","k2_expected_burden"]],
        on=["hazard","strategy","realization_id"],validate="one_to_one")
    k2_parity=float(np.max(np.abs(k2check.population_resolved_mass_weighted_burden_hr-
                                  k2check.k2_expected_burden)))
    if len(k2check)!=36000 or k2_parity>1e-9:
        raise ValueError("k=2 differs from the saved source-plus-multiple-route decomposition")
    realization.to_parquet(OUT/"ROUTE_REQUIREMENT_REALIZATIONS.parquet",index=False)
    metrics=[c for c in realization if c not in {"hazard","strategy","realization_id","k"}]
    summary=realization.groupby(["hazard","strategy","k"],sort=False)[metrics].agg(["mean","median"]).reset_index()
    summary.columns=["_".join(str(a) for a in item if a) for item in summary.columns]
    summary.to_csv(ROOT/"results"/"diagnostics"/"ROUTE_REQUIREMENT_SENSITIVITY_SUMMARY.csv",index=False)
    rows=[]
    for hazard in HAZARDS:
        for strategy in STRATEGIES:
            for k in (1,2,3):
                case=realization[(realization.hazard==hazard)&(realization.strategy==strategy)&(realization.k==k)].set_index("realization_id")
                ref=realization[(realization.hazard==hazard)&(realization.strategy==REF)&(realization.k==k)].set_index("realization_id")
                base=realization[(realization.hazard==hazard)&(realization.strategy==strategy)&(realization.k==1)].set_index("realization_id")
                for metric in ("population_normalized_burden_hr","population_resolved_mass_weighted_burden_hr",
                               "hospital_burden_hr","Q1_burden_hr","Q4_burden_hr","signed_Q4_minus_Q1_hr",
                               "absolute_Q4_minus_Q1_hr","population_weighted_gini","T50","T80"):
                    a=case[metric].to_numpy(float); b=ref[metric].to_numpy(float); c=base[metric].to_numpy(float)
                    valid=np.isfinite(a)&np.isfinite(b); change=np.isfinite(a)&np.isfinite(c)
                    delta=a[valid]-b[valid]
                    shift=a[change]-c[change]
                    rng=np.random.default_rng(np.random.SeedSequence([20260926,HAZARDS.index(hazard),STRATEGIES.index(strategy),k,metrics.index(metric) if metric in metrics else 999]))
                    if len(delta):
                        boot=np.mean(delta[rng.integers(len(delta),size=(1000,len(delta)))],axis=1)
                        low,high=np.quantile(boot,[.025,.975])
                    else:low=high=np.nan
                    rows.append(dict(hazard=hazard,strategy=strategy,reference=REF,k=k,metric=metric,
                                     paired_n=len(delta),paired_mean=float(np.mean(delta)) if len(delta) else np.nan,
                                     paired_median=float(np.median(delta)) if len(delta) else np.nan,
                                     paired_ci95_low=low,paired_ci95_high=high,
                                     k_vs_k1_mean=float(np.mean(shift)) if len(shift) else np.nan,
                                     case_unreached=int(np.isnan(a).sum()) if metric in ("T50","T80") else 0,
                                     reference_unreached=int(np.isnan(b).sum()) if metric in ("T50","T80") else 0))
    pd.DataFrame(rows).to_csv(ROOT/"results"/"diagnostics"/"ROUTE_REQUIREMENT_STRATEGY_EFFECTS.csv",index=False)
    tract_rows=[]
    structural = {(int(row.k),row.tract_id):float(row.tract_maximum_service)
                  for row in ftable.itertuples() if row.record_type=="tract"}
    for (hazard,strategy,k),burden in tract_totals.items():
        shift=burden-tract_totals[(hazard,strategy,1)]
        for i,tract in enumerate(tracts):
            tract_rows.append(dict(hazard=hazard,strategy=strategy,k=k,tract_id=tract,population=p[i],
                                   quartile=q[i],hospital_tract=bool(hospital[i]),
                                   intact_maximum_service=structural[(k,tract)],
                                   T50_structurally_unreachable=structural[(k,tract)]<.5-1e-12,
                                   T80_structurally_unreachable=structural[(k,tract)]<.8-1e-12,
                                   mean_normalized_burden_hr=burden[i],paired_mean_shift_vs_k1_hr=shift[i]))
    pd.DataFrame(tract_rows).to_parquet(ROOT/"results"/"diagnostics"/"ROUTE_REQUIREMENT_TRACT_EFFECTS.parquet",index=False)
    (OUT/"ROUTE_REQUIREMENT_VALIDATION.json").write_text(json.dumps(dict(k1_max_absolute_error=parity,
        k1_reused_formal_metric_max_absolute_error=formal_metric_errors,
        k2_saved_route_composition_max_absolute_error_hr=k2_parity,
        topology=dict(stations=92,edges=318,core_sources=14),horizon_hr=480,
        trajectories_regenerated=False,production_gate_changed=False,
        scenarios=["k1","k2","k3"],realizations_per_hazard=stop-start),indent=2)+"\n")
    return parity,realization,ftable


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--validate-sample",action="store_true")
    args=parser.parse_args()
    run(stop=1,write=False) if args.validate_sample else run()
