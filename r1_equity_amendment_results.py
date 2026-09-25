"""Read-only formal evaluation and paired equity-policy summaries.

The only new station trajectories are those of the predeclared
vulnerability-first sequence. Existing 84,000 archives and metric shards are
never regenerated.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from r1_equity_amendment_execute import AMEND, FORMAL, HAZARDS, CASES, STRATEGY, execution_context
from r1_formal_archive import sha256_file
from r1_formal_offline import PreparedMapping, evaluate_frozen_archive_shard
from r1_formal_results import _bootstrap_paired
from r1_mapping_gate_robustness import mapping_cases


METRICS = ("population_weighted_normalized_burden_hr",
           "population_resolved_mass_weighted_burden_hr", "population_T50_hr",
           "population_T80_hr", "hospital_mean_normalized_burden_hr",
           "burden_Q1_hr", "burden_Q2_hr", "burden_Q3_hr", "burden_Q4_hr",
           "signed_Q4_minus_Q1_hr", "absolute_Q4_minus_Q1_hr", "burden_gini",
           "makespan_hr", "total_travel_hr")
REFERENCES = ("hospital-first", "impact-first")


def _inputs():
    a = json.loads((AMEND / "EQUITY_POLICY_AMENDMENT.json").read_text(encoding="utf-8"))
    sequence = json.loads((AMEND / "VULNERABILITY_FIRST_SEQUENCE.json").read_text(encoding="utf-8"))
    physical = json.loads((FORMAL / "Stage 1 Output_expanded" /
                           "PHYSICAL_INPUTS_FROZEN.json").read_text(encoding="utf-8"))
    index = json.loads((AMEND / "VULNERABILITY_TRAJECTORY_INDEX.json").read_text(encoding="utf-8"))
    if (a["status"] != "FROZEN_BEFORE_EQUITY_POLICY_EXECUTION" or
            index["trajectory_count"] != 10000 or
            index["sequence_sha256"] != sequence["station_sequence_sha256"] or
            index["logistics_sha256"] != sha256_file(AMEND / "VULNERABILITY_LOGISTICS.csv")):
        raise ValueError("Equity trajectory archive is not the frozen complete amendment")
    with np.load(FORMAL / "Stage 1 Output_expanded" / "physical_inputs_2pc50.npz",
                 allow_pickle=False) as z:
        ids = z["station_ids"].astype(str).tolist()
    context, _, hashes = execution_context(ids)
    meta = pd.read_csv("R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
                       dtype={"tract_id": str}).set_index("tract_id")
    frames, _ = mapping_cases()
    maps = {name: PreparedMapping.from_frame(name, frame, ids, meta.population,
            meta.SOVI_quartile, set(meta.index[meta.hospital_tract]))
            for name, frame in frames.items() if name in ("M0_JULY_003", "M1_UTILITY_003")}
    if set(maps) != {"M0_JULY_003", "M1_UTILITY_003"} or len(meta) != 2315:
        raise ValueError("Formal tract mapping/Q4 domain differs")
    return a, sequence, physical, index, context, meta, maps


def evaluate_new_archives() -> list[dict]:
    a, sequence, physical, index, context, meta, maps = _inputs()
    output = AMEND / "Offline"
    offline_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    records = []
    for hazard in HAZARDS:
        for case, _, _ in (CASES if hazard == "2pc50" else CASES[:1]):
            record = evaluate_frozen_archive_shard(
                input_folder=AMEND / "T" / hazard / case,
                output_folder=output, hazard=hazard, strategy=STRATEGY,
                resource_case=case, population=meta.population,
                quartile=meta.SOVI_quartile,
                hospital_tracts=set(meta.index[meta.hospital_tract]),
                mappings=maps, graph=context["graph"], sources=context["sources"],
                physical_hashes=physical["sample_hashes"],
                trajectory_code_sha=sequence["executable_code_commit_sha"],
                offline_code_sha=offline_commit,
                matrix_sha256=a["parent_matrix_sha256"], H_eval_hr=480.0,
                all_robustness=False)
            records.append(record)
            print(json.dumps({"hazard":hazard,"case":case,"action":record["action"]}),flush=True)
    if len(records) != 10 or sum(x["realization_count"] for x in records) != 10000:
        raise ValueError("Amendment offline shard cardinality differs")
    output.joinpath("VULNERABILITY_OFFLINE_INDEX.json").write_text(json.dumps(
        dict(status="FORMAL_EQUITY_AMENDMENT_V1", shard_count=10,
             realization_count=10000, sequence_sha256=sequence["station_sequence_sha256"],
             shard_records=[dict(hazard=r["identity"]["hazard"],
                                 resource_case=r["identity"]["resource_case"],
                                 summary_sha256=r["summary_sha256"],
                                 integral_sha256=r["integral_sha256"]) for r in records]),
        indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return records


def _primary():
    logistics = pd.read_csv(AMEND / "VULNERABILITY_LOGISTICS.csv")
    frame=[]
    for hazard in HAZARDS:
        for case, _, _ in (CASES if hazard == "2pc50" else CASES[:1]):
            p=AMEND/"Offline"/f"{hazard}__{case}__{STRATEGY}__SUMMARY.parquet"
            f=pd.read_parquet(p)
            f=f.loc[f.mapping.eq("M1_UTILITY_003") & f.gate.eq("G1_BASELINE_050") &
                    f.comparison_domain.eq("mapping_native_domain")]
            if len(f)!=1000:raise ValueError("Equity primary summary lost a formal sample")
            frame.append(f)
    result=pd.concat(frame,ignore_index=True).merge(
        logistics[["hazard","realization_id","resource_scenario","strategy_id",
                   "physical_sample_hash","task_count","makespan_hr","total_travel_hr"]],
        on=["hazard","realization_id","resource_scenario","strategy_id"],validate="one_to_one")
    if len(result)!=10000 or result.physical_sample_hash.isna().any():
        raise ValueError("Equity primary summary/physical pairing differs")
    return result


def _paired_rows(candidate, reference, *, scope):
    keys=["hazard","resource_scenario","realization_id"]
    joined=candidate.merge(reference[keys+list(METRICS)],on=keys,
                           suffixes=("_candidate","_reference"),validate="one_to_one")
    if len(joined)!=len(candidate):
        raise ValueError("Reference realization/resource pairing incomplete")
    rows=[]
    for (hazard,case),group in joined.groupby(["hazard","resource_scenario"],sort=False):
        if len(group)!=1000:raise ValueError("Paired group is not 1000 formal realizations")
        for metric in METRICS:
            delta=group[f"{metric}_candidate"].to_numpy(float)-group[f"{metric}_reference"].to_numpy(float)
            rows.append(dict(scope=scope,hazard=hazard,resource_scenario=case,
                             strategy_id=STRATEGY,reference_strategy=reference.strategy_id.iloc[0],
                             metric=metric,**_bootstrap_paired(delta)))
    return rows


def _tract_tables(meta):
    tract_rows=[];class_rows=[]
    tracts=meta.index.astype(str).tolist()
    pop=meta.population.reindex(tracts).to_numpy(float)
    quartile=meta.SOVI_quartile.reindex(tracts).to_numpy(str)
    for hazard in HAZARDS:
        case="C57_D1"
        with np.load(AMEND/"Offline"/f"{hazard}__{case}__{STRATEGY}__INTEGRALS.npz",allow_pickle=False) as z:
            candidate=z["M1_UTILITY_003__normalized_burden_hr"].copy()
            hashes=z["physical_hashes"].copy()
        if candidate.shape!=(1000,2315):raise ValueError("Equity tract matrix differs")
        for ref in REFERENCES:
            with np.load(FORMAL/"Formal_Offline_Evaluation"/
                         f"{hazard}__{case}__{ref}__INTEGRALS.npz",allow_pickle=False) as z:
                reference=z["M1_UTILITY_003__normalized_burden_hr"].copy()
                if not np.array_equal(hashes,z["physical_hashes"]):
                    raise ValueError("Equity/reference tract physical samples differ")
            delta=candidate-reference
            valid=np.isfinite(delta)
            n=valid.sum(axis=0)
            mean=np.divide(np.nansum(delta,axis=0),n,out=np.full(2315,np.nan),where=n>0)
            labels=np.where(~np.isfinite(mean),"unresolved",
                    np.where(mean < -1,"improved",np.where(mean > 1,"worsened","near-zero")))
            tract_rows.extend(dict(hazard=hazard,reference_strategy=ref,tract_id=tracts[j],
                                   quartile=quartile[j],population=pop[j],
                                   mean_paired_delta_burden_hr=float(mean[j]),
                                   valid_realizations=int(n[j]),
                                   probability_delta_below_zero=float((delta[valid[:,j],j]<0).mean()) if n[j] else np.nan,
                                   mean_effect_classification=labels[j]) for j in range(2315))
            for scope in ("mean_paired_tract_effect","per_realization_mean_population"):
                for q in ("all","Q1","Q2","Q3","Q4"):
                    qmask=np.ones(2315,dtype=bool) if q=="all" else quartile==q
                    domain=float(pop[qmask].sum())
                    for label in ("improved","near-zero","worsened","unresolved"):
                        if scope=="mean_paired_tract_effect":
                            selected=qmask & (labels==label)
                            population=float(pop[selected].sum())
                            tract_count=int(selected.sum())
                        else:
                            selected=(delta < -1 if label=="improved" else
                                      delta > 1 if label=="worsened" else
                                      ~valid if label=="unresolved" else
                                      (np.abs(delta)<=1)&valid) & qmask[None,:]
                            population=float((selected@pop).mean())
                            tract_count=float(selected.sum(axis=1).mean())
                        class_rows.append(dict(hazard=hazard,reference_strategy=ref,
                            classification_scope=scope,quartile=q,classification=label,
                            tract_count=tract_count,population=population,
                            domain_population=domain,population_fraction=population/domain))
    return pd.DataFrame(tract_rows),pd.DataFrame(class_rows)


def compile_results():
    a,seq,physical,index,context,meta,maps=_inputs()
    primary=_primary()
    original=pd.read_parquet(FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
    rows=[]
    for ref in REFERENCES:
        reference=original.loc[original.strategy_id.eq(ref)]
        rows.extend(_paired_rows(primary,reference,scope="paired_strategy_effect"))
    effects=pd.DataFrame(rows)
    baseline=effects.loc[effects.resource_scenario.eq("C57_D1")].copy()
    resource=effects.loc[(effects.hazard.eq("2pc50"))&(~effects.resource_scenario.eq("C57_D1"))].copy()
    baseline_lookup=baseline.loc[baseline.hazard.eq("2pc50"),
        ["reference_strategy","metric","paired_mean_difference"]].rename(
        columns={"paired_mean_difference":"baseline_paired_mean_difference"})
    resource=resource.merge(baseline_lookup,on=["reference_strategy","metric"],validate="many_to_one")
    resource["change_in_strategy_difference_vs_baseline"]=resource.paired_mean_difference-resource.baseline_paired_mean_difference
    tract,classification=_tract_tables(meta)
    group=primary.loc[primary.resource_scenario.eq("C57_D1")].groupby("hazard",sort=False)
    group_rows=[]
    for hazard,frame in group:
        row=dict(hazard=hazard,strategy_id=STRATEGY,n=1000)
        for metric in METRICS:
            x=frame[metric].to_numpy(float);x=x[np.isfinite(x)]
            row[metric+"__mean"]=float(x.mean()) if len(x) else np.nan
            row[metric+"__median"]=float(np.median(x)) if len(x) else np.nan
            row[metric+"__p95"]=float(np.percentile(x,95)) if len(x) else np.nan
        group_rows.append(row)
    groups=pd.DataFrame(group_rows)
    paths={"VULNERABILITY_PRIMARY_SUMMARY.parquet":primary,
           "VULNERABILITY_PAIRWISE_EFFECTS.csv":baseline,
           "VULNERABILITY_RESOURCE_EFFECTS.csv":resource,
           "VULNERABILITY_TRACT_EFFECTS.parquet":tract,
           "VULNERABILITY_CLASSIFICATION_POPULATION.csv":classification,
           "VULNERABILITY_GROUP_SUMMARY.csv":groups}
    for name,frame in paths.items():
        path=AMEND/name
        if path.exists():raise ValueError(f"Refuse overwrite: {path}")
        if name.endswith(".parquet"):frame.to_parquet(path,index=False)
        else:frame.to_csv(path,index=False)
    result=dict(status="FORMAL_EQUITY_AMENDMENT_V1",new_trajectories=10000,
                original_trajectories_reused=84000,
                physical_sample_count=4000,sequence_sha256=seq["station_sequence_sha256"],
                result_rows={name:len(frame) for name,frame in paths.items()},
                result_sha256={name:sha256_file(AMEND/name) for name in paths})
    (AMEND/"VULNERABILITY_RESULTS_INDEX.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result
