"""Compact reviewer-facing tables from frozen formal archives only."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from r1_formal_dynamic_topology import _case_catalog, _graph_arrays

METRICS = ["population_T80_hr", "population_weighted_normalized_burden_hr",
           "population_resolved_mass_weighted_burden_hr",
           "hospital_mean_normalized_burden_hr", "burden_Q1_hr", "burden_Q2_hr",
           "burden_Q3_hr", "burden_Q4_hr", "signed_Q4_minus_Q1_hr",
           "absolute_Q4_minus_Q1_hr", "burden_gini"]


def _paired_effects(frame, reference_col, target_col, keys, metric_columns, labels):
    a=frame.loc[frame[reference_col].eq(labels[0]),keys+metric_columns].copy()
    b=frame.loc[frame[target_col].eq(labels[1]),keys+metric_columns].copy()
    joined=a.merge(b,on=keys,suffixes=("_reference","_target"),validate="one_to_one")
    rows=[]
    for group_key,group in joined.groupby([k for k in keys if k!="realization_id"],sort=False):
        if not isinstance(group_key,tuple):group_key=(group_key,)
        context=dict(zip([k for k in keys if k!="realization_id"],group_key))
        if len(group)!=1000:
            raise ValueError("Paired formal comparison does not have 1000 realizations")
        for metric in metric_columns:
            diff=group[metric+"_target"].to_numpy()-group[metric+"_reference"].to_numpy()
            valid=diff[np.isfinite(diff)]
            rows.append(dict(**context,reference=labels[0],target=labels[1],metric=metric,
                             n=len(valid),mean_delta=float(valid.mean()) if len(valid) else np.nan,
                             median_delta=float(np.median(valid)) if len(valid) else np.nan,
                             p95_delta=float(np.percentile(valid,95)) if len(valid) else np.nan,
                             fraction_delta_below_zero=float((valid<0).mean()) if len(valid) else np.nan))
    return pd.DataFrame(rows)


def _mapping_table(summary):
    baseline=summary.loc[(summary.resource_scenario=="C57_D1")&
                         (summary.gate=="G1_BASELINE_050")].copy()
    rows=[]
    choices=[("full92","mapping_native_domain","M0_JULY_003","M1_UTILITY_003"),
             ("2pc50_cutoff_M0_001","mapping_native_domain","M0_JULY_003","M0_JULY_001"),
             ("2pc50_cutoff_M0_none","mapping_native_domain","M0_JULY_003","M0_JULY_NO_CUTOFF"),
             ("2pc50_cutoff_M1_001","mapping_native_domain","M1_UTILITY_003","M1_UTILITY_001"),
             ("2pc50_cutoff_M1_none","mapping_native_domain","M1_UTILITY_003","M1_UTILITY_NO_CUTOFF"),
             ("SCE_common320_M3_vs_M0","SCE_common_positive_support","M0_JULY_003","M3_SCE_SUPPORTED"),
             ("SCE_common320_M3_vs_M1","SCE_common_positive_support","M1_UTILITY_003","M3_SCE_SUPPORTED")]
    for label,domain,reference,target in choices:
        q=baseline.loc[baseline.comparison_domain.eq(domain)]
        if label!="full92":q=q.loc[q.hazard.eq("2pc50")]
        left=q.loc[q.mapping.eq(reference),["hazard","strategy_id","realization_id"]+METRICS]
        right=q.loc[q.mapping.eq(target),["hazard","strategy_id","realization_id"]+METRICS]
        joined=left.merge(right,on=["hazard","strategy_id","realization_id"],
                          suffixes=("_reference","_target"),validate="one_to_one")
        for (hazard,strategy),group in joined.groupby(["hazard","strategy_id"],sort=False):
            if len(group)!=1000:raise ValueError("Mapping contrast lost paired realizations")
            for metric in METRICS:
                d=group[metric+"_target"].to_numpy()-group[metric+"_reference"].to_numpy()
                valid=d[np.isfinite(d)]
                rows.append(dict(comparison=label,domain=domain,hazard=hazard,strategy_id=strategy,
                                 reference_mapping=reference,target_mapping=target,metric=metric,
                                 n=len(valid),mean_delta=float(valid.mean()) if len(valid) else np.nan,
                                 median_delta=float(np.median(valid)) if len(valid) else np.nan,
                                 p95_delta=float(np.percentile(valid,95)) if len(valid) else np.nan,
                                 fraction_delta_below_zero=float((valid<0).mean()) if len(valid) else np.nan))
    return pd.DataFrame(rows)


def _gate_table(summary):
    q=summary.loc[(summary.mapping=="M1_UTILITY_003")&
                  (summary.comparison_domain=="mapping_native_domain")].copy()
    baseline=q.loc[q.gate.eq("G1_BASELINE_050")].copy()
    rows=[]
    for (hazard,resource,strategy),group in baseline.groupby(["hazard","resource_scenario","strategy_id"],sort=False):
        if len(group)!=1000:raise ValueError("Production gate group does not contain 1000")
        values={"self":"L_self_population_mass_weighted_hr",
                "threshold":"L_threshold_population_mass_weighted_hr",
                "source":"L_source_population_mass_weighted_hr",
                "total":"L_total_population_mass_weighted_hr"}
        result=dict(hazard=hazard,resource_scenario=resource,strategy_id=strategy,n=1000)
        for label,column in values.items():
            x=group[column].to_numpy()
            result[label+"_mean_hr"]=float(np.mean(x))
            result[label+"_median_hr"]=float(np.median(x))
            result[label+"_p95_hr"]=float(np.percentile(x,95))
        result["source_fraction_of_mean_total"]=result["source_mean_hr"]/result["total_mean_hr"]
        result["threshold_fraction_of_mean_total"]=result["threshold_mean_hr"]/result["total_mean_hr"]
        rows.append(result)
    return pd.DataFrame(rows)


def _strategy_table(primary):
    q=primary.loc[(primary.resource_scenario=="C57_D1")&
                  (primary.mapping=="M1_UTILITY_003")&
                  (primary.gate=="G1_BASELINE_050")].copy()
    metrics=METRICS+["L_self_population_mass_weighted_hr",
                     "L_source_population_mass_weighted_hr","makespan_hr","total_travel_hr"]
    base=q.loc[q.strategy_id.eq("hospital-first"),["hazard","realization_id"]+metrics]
    other=q.loc[~q.strategy_id.eq("hospital-first"),["hazard","realization_id","strategy_id"]+metrics]
    joined=other.merge(base,on=["hazard","realization_id"],suffixes=("_target","_reference"),validate="many_to_one")
    rows=[]
    for (hazard,strategy),group in joined.groupby(["hazard","strategy_id"],sort=False):
        if len(group)!=1000:raise ValueError("Strategy comparison lost paired realizations")
        for metric in metrics:
            d=group[metric+"_target"].to_numpy()-group[metric+"_reference"].to_numpy()
            valid=d[np.isfinite(d)]
            rows.append(dict(hazard=hazard,strategy_id=strategy,reference="hospital-first",metric=metric,
                             n=len(valid),mean_delta=float(valid.mean()) if len(valid) else np.nan,
                             median_delta=float(np.median(valid)) if len(valid) else np.nan,
                             p95_delta=float(np.percentile(valid,95)) if len(valid) else np.nan,
                             fraction_delta_below_zero=float((valid<0).mean()) if len(valid) else np.nan))
    return pd.DataFrame(rows)


def _resource_table(primary):
    q=primary.loc[(primary.hazard=="2pc50")&
                  (primary.mapping=="M1_UTILITY_003")&
                  (primary.gate=="G1_BASELINE_050")&
                  (~primary.strategy_id.eq("unconstrained"))].copy()
    baseline=q.loc[q.resource_scenario.eq("C57_D1")]
    other=q.loc[~q.resource_scenario.eq("C57_D1")]
    metrics=["population_resolved_mass_weighted_burden_hr",
             "population_T80_hr","hospital_mean_normalized_burden_hr",
             "signed_Q4_minus_Q1_hr","burden_gini","L_self_population_mass_weighted_hr",
             "L_threshold_population_mass_weighted_hr","L_source_population_mass_weighted_hr",
             "makespan_hr","total_travel_hr"]
    joined=other.merge(baseline[["realization_id","strategy_id"]+metrics],
                       on=["realization_id","strategy_id"],suffixes=("_target","_reference"),validate="many_to_one")
    rows=[]
    for (resource,strategy),group in joined.groupby(["resource_scenario","strategy_id"],sort=False):
        if len(group)!=1000:raise ValueError("Resource comparison lost paired realization")
        for metric in metrics:
            x=group[metric+"_target"].to_numpy()
            d=x-group[metric+"_reference"].to_numpy()
            valid=d[np.isfinite(d)]
            rows.append(dict(resource_scenario=resource,strategy_id=strategy,reference="C57_D1",
                             metric=metric,n=len(valid),target_mean=float(np.nanmean(x)),
                             mean_delta=float(valid.mean()) if len(valid) else np.nan,
                             median_delta=float(np.median(valid)) if len(valid) else np.nan,
                             p95_delta=float(np.percentile(valid,95)) if len(valid) else np.nan))
    return pd.DataFrame(rows)


def _distributional_table(primary):
    q=primary.loc[(primary.resource_scenario=="C57_D1")&
                  (primary.mapping=="M1_UTILITY_003")&
                  (primary.gate=="G1_BASELINE_050")].copy()
    columns=["burden_Q1_hr","burden_Q2_hr","burden_Q3_hr","burden_Q4_hr",
             "signed_Q4_minus_Q1_hr","absolute_Q4_minus_Q1_hr","burden_gini",
             "population_weighted_normalized_burden_hr"]
    rows=[]
    for (hazard,strategy),group in q.groupby(["hazard","strategy_id"],sort=False):
        if len(group)!=1000:raise ValueError("Distributional group lost realizations")
        result=dict(hazard=hazard,strategy_id=strategy,n=1000)
        for col in columns:
            values=group[col].dropna().to_numpy()
            result[col+"__mean"]=float(values.mean()) if len(values) else np.nan
            result[col+"__median"]=float(np.median(values)) if len(values) else np.nan
            result[col+"__p95"]=float(np.percentile(values,95)) if len(values) else np.nan
        rows.append(result)
    return pd.DataFrame(rows)


def generate_existing_result_tables(root: Path) -> dict:
    root=Path(root)
    out=root/"Formal_Reviewer_Results"
    out.mkdir(exist_ok=True)
    summary=pd.read_parquet(root/"Formal_Offline_Evaluation"/"FORMAL_REALIZATION_STRATEGY_SUMMARY.parquet")
    primary=pd.read_parquet(root/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
    if len(summary)!=462000 or len(primary)!=84000:
        raise ValueError("Formal summary dimensions changed")
    files={
        "FORMAL_MAPPING_EFFECTS.csv":_mapping_table(summary),
        "FORMAL_GATE_COMPONENTS.csv":_gate_table(summary),
        "FORMAL_STRATEGY_EFFECTS.csv":_strategy_table(primary),
        "FORMAL_RESOURCE_EFFECTS.csv":_resource_table(primary),
        "FORMAL_DISTRIBUTIONAL_EFFECTS.csv":_distributional_table(primary),
    }
    for name,frame in files.items():
        path=out/name
        if path.exists():raise ValueError(f"Refuse overwrite: {path}")
        frame.to_csv(path,index=False)
    return {name:len(frame) for name,frame in files.items()}


def _mapping_arrays(station_ids, path="Data/JULY_UTILITY_CONSTRAINED_92.csv"):
    frame=pd.read_csv(path,
                      dtype={"tract_id":str,"substation_id":str})
    frame["weight"]=pd.to_numeric(frame.weight)
    frame["population"]=pd.to_numeric(frame.population)
    tracts=sorted(frame.tract_id.unique())
    if len(tracts)!=2315 or set(frame.substation_id)!=set(station_ids):
        raise ValueError("Frozen M1 tract/station domain changed")
    w=frame.pivot_table(index="tract_id",columns="substation_id",values="weight",fill_value=0)
    w=w.reindex(index=tracts,columns=station_ids,fill_value=0)
    if np.max(np.abs(w.sum(axis=1).to_numpy()-1))>1e-10:
        raise ValueError("Frozen M1 row weights changed")
    population=frame.groupby("tract_id").population.first().reindex(tracts)
    if population.isna().any():raise ValueError("Population missing for source loss")
    return tracts,w.to_numpy(dtype=float),population.to_numpy(dtype=float)


def generate_source_loss_tables(root: Path) -> dict:
    root=Path(root)
    out=root/"Formal_Reviewer_Results"
    catalog,_=_case_catalog(root)
    first=root/"Formal_Trajectories"/"Northridge"/"C57_D1"/"hospital-first"/"Northridge__evaluation_0000.npz"
    with np.load(first,allow_pickle=False) as z:ids=z["station_ids"].astype(str).tolist()
    tracts,w,pop=_mapping_arrays(ids)
    mass=w.T@pop
    total_population=float(pop.sum())
    edge_u,edge_v,adj,deg,sources,static=_graph_arrays(ids)
    static_eight=[ids[i] for i in np.flatnonzero(static[:,8]==1)]
    if len(static_eight)!=8:raise ValueError(f"Expected eight static single-path stations, got {static_eight}")
    colorado=ids.index("306694")
    station_rows=[]
    tract_rows=[]
    concentration_rows=[]
    for hazard,cases in catalog.items():
        for resource,strategy in cases:
            path=root/"Formal_Offline_Evaluation"/f"{hazard}__{resource}__{strategy}__INTEGRALS.npz"
            with np.load(path,allow_pickle=False) as z:
                if not np.array_equal(z["station_ids"].astype(str),ids):
                    raise ValueError("Source integral station order changed")
                self_loss=z["G1_BASELINE_050__L_self"].copy()
                threshold_loss=z["G1_BASELINE_050__L_threshold"].copy()
                source_loss=z["G1_BASELINE_050__L_source"].copy()
                total_loss=z["G1_BASELINE_050__L_total"].copy()
            if self_loss.shape!=(1000,92) or np.max(np.abs(self_loss+threshold_loss+source_loss-total_loss))>1e-8:
                raise ValueError("Frozen source-loss integrals fail additive identity")
            contributions=source_loss*mass[None,:]/total_population
            total=contributions.sum(axis=1)
            sorted_contrib=np.sort(contributions,axis=1)[:,::-1]
            positive=total>0
            for realization in range(1000):
                denominator=total[realization]
                def fraction(value):
                    return float(value/denominator) if denominator>0 else np.nan
                concentration_rows.append(dict(hazard=hazard,resource_scenario=resource,
                                               strategy_id=strategy,realization_id=f"{hazard}__evaluation_{realization:04d}",
                                               population_weighted_source_loss_hr=denominator,
                                               top1_fraction=fraction(sorted_contrib[realization,:1].sum()),
                                               top5_fraction=fraction(sorted_contrib[realization,:5].sum()),
                                               top8_fraction=fraction(sorted_contrib[realization,:8].sum()),
                                               static_eight_fraction=fraction(contributions[realization,static[:,8]==1].sum()),
                                               colorado_fraction=fraction(contributions[realization,colorado]),
                                               colorado_source_loss_hr=float(contributions[realization,colorado])))
            contribution_mean=contributions.mean(axis=0)
            group_total=float(contribution_mean.sum())
            for i,station in enumerate(ids):
                station_rows.append(dict(hazard=hazard,resource_scenario=resource,strategy_id=strategy,
                                         station_id=station,mean_station_source_loss_integral_hr=float(source_loss[:,i].mean()),
                                         median_station_source_loss_integral_hr=float(np.median(source_loss[:,i])),
                                         p95_station_source_loss_integral_hr=float(np.percentile(source_loss[:,i],95)),
                                         mean_population_weighted_source_loss_hr=float(contribution_mean[i]),
                                         fraction_of_aggregate_source_loss=float(contribution_mean[i]/group_total) if group_total>0 else np.nan,
                                         static_single_path=bool(static[i,8]),static_bridge_dependent=bool(static[i,6]),
                                         static_articulation_dependent=bool(static[i,7]),
                                         static_reachable_sources=int(static[i,3]),
                                         static_edge_disjoint_remote_paths=int(static[i,4]),
                                         static_node_disjoint_remote_paths=int(static[i,5])))
            # Exact linear propagation of saved station integrals to tracts.
            mean_self=w@self_loss.mean(axis=0)
            mean_threshold=w@threshold_loss.mean(axis=0)
            mean_source=w@source_loss.mean(axis=0)
            mean_total=w@total_loss.mean(axis=0)
            count_source_more=np.zeros(len(tracts),dtype=np.int32)
            for start in range(0,1000,100):
                stop=start+100
                count_source_more+=np.sum(source_loss[start:stop]@w.T > self_loss[start:stop]@w.T,axis=0)
            for i,tract in enumerate(tracts):
                tract_rows.append(dict(hazard=hazard,resource_scenario=resource,
                                       strategy_id=strategy,tract_id=tract,population=pop[i],
                                       mean_self_loss_hr=float(mean_self[i]),
                                       mean_threshold_loss_hr=float(mean_threshold[i]),
                                       mean_source_loss_hr=float(mean_source[i]),
                                       mean_total_loss_hr=float(mean_total[i]),
                                       source_share_of_mean_total=float(mean_source[i]/mean_total[i]) if mean_total[i]>0 else np.nan,
                                       source_exceeds_self_by_mean=bool(mean_source[i]>mean_self[i]),
                                       source_exceeds_self_realization_fraction=count_source_more[i]/1000))
    outputs={"FORMAL_SOURCE_LOSS_BY_STATION.csv":pd.DataFrame(station_rows),
             "FORMAL_SOURCE_LOSS_BY_TRACT.csv":pd.DataFrame(tract_rows),
             "FORMAL_SOURCE_LOSS_CONCENTRATION.csv":pd.DataFrame(concentration_rows)}
    for name,frame in outputs.items():
        path=out/name
        if path.exists():raise ValueError(f"Refuse overwrite: {path}")
        frame.to_csv(path,index=False)
    return dict(static_eight=static_eight,Colorado_ID=ids[colorado],
                rows={name:len(frame) for name,frame in outputs.items()},
                population_denominator=total_population)


def generate_dynamic_summary(root: Path) -> dict:
    root=Path(root)
    folder=root/"Formal_Dynamic_Topology"
    out=root/"Formal_Reviewer_Results"
    catalog,_=_case_catalog(root)
    first=root/"Formal_Trajectories"/"Northridge"/"C57_D1"/"hospital-first"/"Northridge__evaluation_0000.npz"
    with np.load(first,allow_pickle=False) as z:ids=z["station_ids"].astype(str).tolist()
    _,w,pop=_mapping_arrays(ids)
    mass=w.T@pop
    denominator=float(pop.sum())
    rows=[]
    station_dynamic=defaultdict(lambda:np.zeros((5,92),dtype=float))
    total_hits=total_misses=total_states=total_functional=0
    max_parity=0.
    for hazard,cases in catalog.items():
        for sample in range(1000):
            stem=f"{hazard}__evaluation_{sample:04d}"
            path=folder/hazard/(stem+"__DYNAMIC.npz")
            meta=json.loads((folder/hazard/(stem+"__DYNAMIC.json")).read_text(encoding="utf-8"))
            if meta["npz_sha256"]!=hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError("Dynamic sample artifact hash changed")
            total_hits+=meta["cache_hits"]
            total_misses+=meta["cache_misses"]
            total_states+=meta["event_state_count"]
            total_functional+=meta["functional_change_states"]
            max_parity=max(max_parity,meta["source_integral_parity_max_abs_hr"])
            with np.load(path,allow_pickle=False) as z:
                if not np.array_equal(z["station_ids"].astype(str),ids):
                    raise ValueError("Dynamic sample station order changed")
                if list(z["run_names"].astype(str))!=[f"{r}|{s}" for r,s in cases]:
                    raise ValueError("Dynamic sample case order changed")
                source=z["source_integral_hr"]
                single=z["source_prior_single_path_hr"]
                bridge=z["source_prior_bridge_hr"]
                artic=z["source_prior_articulation_hr"]
                fallback=z["source_prior_static_fallback_hr"]
                clearance=z["source_loss_clearance_hr"]
            for i,(resource,strategy) in enumerate(cases):
                station_dynamic[(hazard,resource,strategy)][0]+=source[i]
                station_dynamic[(hazard,resource,strategy)][1]+=single[i]
                station_dynamic[(hazard,resource,strategy)][2]+=bridge[i]
                station_dynamic[(hazard,resource,strategy)][3]+=artic[i]
                station_dynamic[(hazard,resource,strategy)][4]+=fallback[i]
                total=float(source[i]@mass/denominator)
                def frac(array):
                    return float(array[i]@mass/denominator/total) if total>0 else np.nan
                rows.append(dict(hazard=hazard,resource_scenario=resource,strategy_id=strategy,
                                 realization_id=stem,source_loss_hr=total,
                                 source_clearance_hr=float(clearance[i]),
                                 prior_single_path_fraction=frac(single),
                                 prior_bridge_fraction=frac(bridge),
                                 prior_articulation_fraction=frac(artic),
                                 prior_static_fallback_fraction=frac(fallback)))
    detailed=pd.DataFrame(rows)
    if len(detailed)!=84000:
        raise ValueError("Dynamic topology did not cover all 84,000 formal trajectories")
    concentration=pd.read_csv(out/"FORMAL_SOURCE_LOSS_CONCENTRATION.csv")
    detailed=detailed.merge(concentration,
                            on=["hazard","resource_scenario","strategy_id","realization_id"],
                            validate="one_to_one")
    if len(detailed)!=84000 or np.max(np.abs(detailed.source_loss_hr-
                                               detailed.population_weighted_source_loss_hr))>1e-10:
        raise ValueError("Dynamic and frozen-integral source-loss identities differ")
    aggregates=[]
    values=["source_loss_hr","source_clearance_hr","prior_single_path_fraction",
            "prior_bridge_fraction","prior_articulation_fraction","prior_static_fallback_fraction",
            "top1_fraction","top5_fraction","top8_fraction","static_eight_fraction",
            "colorado_fraction","colorado_source_loss_hr"]
    for (hazard,resource,strategy),group in detailed.groupby(["hazard","resource_scenario","strategy_id"],sort=False):
        if len(group)!=1000:raise ValueError("Dynamic case did not cover all 1000 realizations")
        row=dict(hazard=hazard,resource_scenario=resource,strategy_id=strategy,n=1000)
        for col in values:
            x=group[col].dropna().to_numpy()
            row[col+"__mean"]=float(x.mean()) if len(x) else np.nan
            row[col+"__median"]=float(np.median(x)) if len(x) else np.nan
            row[col+"__p95"]=float(np.percentile(x,95)) if len(x) else np.nan
        aggregates.append(row)
    baseline=detailed.loc[detailed.strategy_id.eq("hospital-first"),
                          ["hazard","resource_scenario","realization_id","source_loss_hr","source_clearance_hr"]]
    joined=detailed.merge(baseline,on=["hazard","resource_scenario","realization_id"],
                          suffixes=("","_hospital"),validate="many_to_one")
    paired=[]
    for (hazard,resource,strategy),group in joined.groupby(["hazard","resource_scenario","strategy_id"],sort=False):
        row=dict(hazard=hazard,resource_scenario=resource,strategy_id=strategy)
        for col in ("source_loss_hr","source_clearance_hr"):
            delta=group[col]-group[col+"_hospital"]
            row[col+"__paired_mean_vs_hospital"]=float(delta.mean())
            row[col+"__paired_median_vs_hospital"]=float(delta.median())
            row[col+"__paired_p95_vs_hospital"]=float(delta.quantile(.95))
            row[col+"__paired_fraction_below_hospital"]=float((delta<0).mean())
        paired.append(row)
    result=pd.DataFrame(aggregates).merge(pd.DataFrame(paired),on=["hazard","resource_scenario","strategy_id"],validate="one_to_one")
    path=out/"FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv"
    if path.exists():raise ValueError(f"Refuse overwrite: {path}")
    result.to_csv(path,index=False)
    station_path=out/"FORMAL_SOURCE_LOSS_BY_STATION.csv"
    station_frame=pd.read_csv(station_path,dtype={"station_id":str})
    if len(station_frame)!=7728:
        raise ValueError("Expected complete station source-loss table before dynamic join")
    annotations=[]
    for (hazard,resource,strategy),array in station_dynamic.items():
        for i,station in enumerate(ids):
            total=array[0,i]
            annotations.append(dict(hazard=hazard,resource_scenario=resource,strategy_id=strategy,
                                    station_id=station,
                                    source_loss_prior_single_path_fraction=array[1,i]/total if total>0 else np.nan,
                                    source_loss_prior_bridge_fraction=array[2,i]/total if total>0 else np.nan,
                                    source_loss_prior_articulation_fraction=array[3,i]/total if total>0 else np.nan,
                                    source_loss_static_fallback_fraction=array[4,i]/total if total>0 else np.nan))
    enriched=station_frame.merge(pd.DataFrame(annotations),
                                 on=["hazard","resource_scenario","strategy_id","station_id"],
                                 validate="one_to_one")
    if len(enriched)!=7728:
        raise ValueError("Dynamic station-class join changed station table cardinality")
    enriched.to_csv(station_path,index=False)
    detail_path=folder/"FORMAL_DYNAMIC_REALIZATION_DIAGNOSTICS.parquet"
    if detail_path.exists():raise ValueError(f"Refuse overwrite: {detail_path}")
    detailed.to_parquet(detail_path,index=False)
    identity=dict(status="FORMAL_FROZEN_MATRIX_V1",sample_count=4000,trajectory_count=84000,
                  event_state_count=total_states,functional_change_states=total_functional,
                  exact_state_cache_hits=total_hits,exact_state_cache_misses=total_misses,
                  cache_hit_fraction=total_hits/total_states,
                  source_integral_parity_max_abs_hr=max_parity,
                  realization_detail_sha256=hashlib.sha256(detail_path.read_bytes()).hexdigest(),
                  summary_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  station_table_sha256=hashlib.sha256(station_path.read_bytes()).hexdigest())
    (folder/"FORMAL_DYNAMIC_TOPOLOGY_INDEX.json").write_text(json.dumps(identity,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return identity


def generate_mapping_tract_contrasts(root: Path) -> dict:
    root=Path(root)
    out=root/"Formal_Reviewer_Results"
    first=root/"Formal_Trajectories"/"Northridge"/"C57_D1"/"hospital-first"/"Northridge__evaluation_0000.npz"
    with np.load(first,allow_pickle=False) as z:ids=z["station_ids"].astype(str).tolist()
    tracts,w1,pop=_mapping_arrays(ids)
    baseline_tracts,w0,pop0=_mapping_arrays(ids,"Data/tract_to_substation_mapping_CEC_expanded.csv")
    if tracts!=baseline_tracts or not np.array_equal(pop,pop0):
        raise ValueError("July M0/M1 tract and population identities differ")
    shift=pd.read_parquet(root/"Formal_Results"/"TRACT_MAPPING_SHIFT.parquet")
    shift["tract_id"]=shift.tract_id.astype(str).str.zfill(11)
    rows=[]
    classes=[]
    catalog,_=_case_catalog(root)
    for hazard in catalog:
        for resource,strategy in catalog[hazard]:
            if resource!="C57_D1":continue
            path=root/"Formal_Offline_Evaluation"/f"{hazard}__C57_D1__{strategy}__INTEGRALS.npz"
            with np.load(path,allow_pickle=False) as z:
                source=z["G1_BASELINE_050__L_source"].mean(axis=0)
                total=z["G1_BASELINE_050__L_total"].mean(axis=0)
            source_shift=(w1-w0)@source
            total_shift=(w1-w0)@total
            saved=shift.loc[(shift.hazard==hazard)&(shift.strategy_id==strategy)]
            saved=saved.set_index("tract_id").reindex(tracts)
            if saved.mean_M1_minus_M0_burden_hr.isna().any() or np.max(np.abs(total_shift-saved.mean_M1_minus_M0_burden_hr.to_numpy()))>1e-8:
                raise ValueError("Station-factorized mapping shift differs from formal saved tract output")
            for i,tract in enumerate(tracts):
                rows.append(dict(hazard=hazard,strategy_id=strategy,tract_id=tract,population=pop[i],
                                 mean_M1_minus_M0_source_loss_hr=float(source_shift[i]),
                                 mean_M1_minus_M0_total_loss_hr=float(total_shift[i])))
            class_values=np.where(total_shift < -1,"improved",np.where(total_shift > 1,"worsened","near-zero"))
            for classification in ("improved","near-zero","worsened"):
                selected=class_values==classification
                classes.append(dict(hazard=hazard,strategy_id=strategy,
                                    classification_scope="mean_paired_M1_minus_M0",
                                    classification=classification,tract_count=int(selected.sum()),
                                    population=float(pop[selected].sum()),
                                    population_fraction=float(pop[selected].sum()/pop.sum())))
    outputs={"FORMAL_SOURCE_MAPPING_SHIFT_BY_TRACT.csv":pd.DataFrame(rows),
             "FORMAL_MAPPING_TRACT_CLASSES.csv":pd.DataFrame(classes)}
    for name,frame in outputs.items():
        path=out/name
        if path.exists():raise ValueError(f"Refuse overwrite: {path}")
        frame.to_csv(path,index=False)
    return {name:len(frame) for name,frame in outputs.items()}
