"""Paired postprocessing of frozen July92 formal station/tract evaluations.

The expanded original entry calls this only after all 84 offline shards exist.
No physical sample, schedule, source gate, or mapping is executed here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from r1_final_matrix import HAZARDS, SCHEDULED
from r1_formal_archive import sha256_file
from r1_mapping_gate_robustness import mapping_cases


BOOTSTRAP_METRICS = (
    "population_T80_hr", "population_weighted_normalized_burden_hr",
    "population_resolved_mass_weighted_burden_hr",
    "hospital_mean_normalized_burden_hr", "burden_Q4_hr",
    "signed_Q4_minus_Q1_hr", "burden_gini", "makespan_hr",
    "total_travel_hr",
)


def _bootstrap_paired(delta: np.ndarray, *, resamples=10000, seed=42):
    delta = np.asarray(delta, float)
    delta = delta[np.isfinite(delta)]
    if not len(delta):
        return dict(n_realizations=0, paired_mean_difference=np.nan,
                    paired_median_difference=np.nan, fraction_delta_below_zero=np.nan,
                    bootstrap_ci_low=np.nan, bootstrap_ci_high=np.nan)
    rng = np.random.default_rng(seed)
    means = np.empty(resamples)
    for start in range(0, resamples, 500):
        stop = min(start + 500, resamples)
        chosen = rng.integers(0, len(delta), size=(stop-start, len(delta)))
        means[start:stop] = delta[chosen].mean(axis=1)
    low, high = np.quantile(means, [.025, .975])
    return dict(n_realizations=len(delta), paired_mean_difference=float(delta.mean()),
                paired_median_difference=float(np.median(delta)),
                fraction_delta_below_zero=float(np.mean(delta < 0)),
                bootstrap_ci_low=float(low), bootstrap_ci_high=float(high))


def _logistics(root: Path) -> pd.DataFrame:
    schedule_dir = root / "Formal_Schedule_Prepass"
    physical_dir = root / "Stage 1 Output_expanded"
    rows = []
    for hazard in HAZARDS:
        with np.load(physical_dir / f"physical_inputs_{hazard}.npz", allow_pickle=False) as physical:
            ds = physical["evaluation_ds"]
            durations = physical["evaluation_duration"]
        if ds.shape != (92, 1000) or durations.shape != (92, 1000):
            raise ValueError("Frozen evaluation sample dimensions changed")
        for i in range(1000):
            damaged = ds[:, i] > 0
            rows.append(dict(hazard=hazard, realization_id=f"{hazard}__evaluation_{i:04d}",
                             strategy_id="unconstrained", resource_scenario="C57_D1",
                             task_count=int(damaged.sum()),
                             makespan_hr=float(durations[damaged, i].max()) if damaged.any() else 0.,
                             total_travel_hr=np.nan))
        cases = ["C57_D1"]
        if hazard == "2pc50":
            cases += ["C29_D1", "C86_D1", "C114_D1", "C57_D075", "C57_D125", "C57_D150"]
        for resource in cases:
            for strategy in SCHEDULED:
                stem = f"{hazard}__{resource}__{strategy}"
                record = json.loads((schedule_dir / (stem + ".json")).read_text(encoding="utf-8"))
                path = schedule_dir / (stem + ".npz")
                if sha256_file(path) != record["npz_sha256"]:
                    raise ValueError("Frozen schedule shard changed")
                with np.load(path, allow_pickle=False) as z:
                    completion, travel, dispatch = (z[k].copy() for k in
                                                    ("completion", "travel", "dispatch"))
                if completion.shape != (1000, 92):
                    raise ValueError("Frozen schedule dimensions changed")
                maximum = np.nanmax(np.where(np.isfinite(completion), completion, 0.), axis=1)
                travel_total = np.nansum(travel, axis=1)
                task_count = (dispatch >= 0).sum(axis=1)
                rows.extend(dict(hazard=hazard, realization_id=f"{hazard}__evaluation_{i:04d}",
                                 strategy_id=strategy, resource_scenario=resource,
                                 task_count=int(task_count[i]), makespan_hr=float(maximum[i]),
                                 total_travel_hr=float(travel_total[i])) for i in range(1000))
    out = pd.DataFrame(rows)
    if len(out) != 84000 or out.duplicated(["hazard", "realization_id", "strategy_id", "resource_scenario"]).any():
        raise ValueError("Formal logistics summary has wrong pairing cardinality")
    return out


def _primary_summary(root: Path, logistics: pd.DataFrame) -> pd.DataFrame:
    offline = root / "Formal_Offline_Evaluation"
    record = json.loads((offline / "FORMAL_OFFLINE_INDEX.json").read_text(encoding="utf-8"))
    path = offline / "FORMAL_REALIZATION_STRATEGY_SUMMARY.parquet"
    if record["status"] != "FORMAL_FROZEN_MATRIX_V1" or sha256_file(path) != record["consolidated_summary_sha256"]:
        raise ValueError("Formal offline summary bytes/identity changed")
    all_views = pd.read_parquet(path)
    if len(all_views) != 462000:
        raise ValueError("Formal offline view count differs")
    primary = all_views.loc[
        all_views.mapping.eq("M1_UTILITY_003") &
        all_views.gate.eq("G1_BASELINE_050") &
        all_views.comparison_domain.eq("mapping_native_domain")].copy()
    if len(primary) != 84000:
        raise ValueError("Formal production primary view count differs")
    primary = primary.merge(logistics, on=["hazard", "realization_id", "strategy_id",
                                            "resource_scenario"], how="left", validate="one_to_one")
    if primary.makespan_hr.isna().any() or primary.task_count.isna().any():
        raise ValueError("Primary metrics/logistics identity does not pair")
    return primary


def _paired_strategy_effects(primary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (hazard, resource), group in primary.groupby(["hazard", "resource_scenario"], sort=False):
        if group.realization_id.nunique() != 1000 or group.duplicated(["realization_id", "strategy_id"]).any():
            raise ValueError("Formal primary strategy groups are not paired")
        reference = group.loc[group.strategy_id.eq("hospital-first")].set_index("realization_id")
        if len(reference) != 1000:
            raise ValueError("Hospital-first reference is incomplete")
        for strategy, candidate in group.groupby("strategy_id", sort=False):
            if strategy == "hospital-first":
                continue
            candidate = candidate.set_index("realization_id").reindex(reference.index)
            if candidate.strategy_id.isna().any():
                raise ValueError("Paired strategy realization is missing")
            for metric in BOOTSTRAP_METRICS:
                delta = candidate[metric].to_numpy(float) - reference[metric].to_numpy(float)
                rows.append(dict(hazard=hazard, resource_scenario=resource,
                                 strategy_id=strategy, reference_strategy="hospital-first",
                                 metric=metric, **_bootstrap_paired(delta)))
    return pd.DataFrame(rows)


def _tract_effects(root: Path, prepared, population: pd.Series, quartile: pd.Series):
    integrals = root / "Formal_Offline_Evaluation"
    tracts = prepared["M1_UTILITY_003"].tract_ids
    pop = population.reindex(tracts).to_numpy(float)
    q = quartile.reindex(tracts).to_numpy(str)
    records = []
    classification = []
    mapping_shift = []
    for hazard in HAZARDS:
        resources = ["C57_D1"]
        if hazard == "2pc50":
            resources += ["C29_D1", "C86_D1", "C114_D1", "C57_D075", "C57_D125", "C57_D150"]
        for resource in resources:
            reference_path = integrals / f"{hazard}__{resource}__hospital-first__INTEGRALS.npz"
            with np.load(reference_path, allow_pickle=False) as z:
                reference = z["M1_UTILITY_003__normalized_burden_hr"].copy()
                reference_hashes = z["physical_hashes"].copy()
            if reference.shape != (1000, 2315):
                raise ValueError("Hospital-first tract burden dimensions differ")
            for strategy in SCHEDULED:
                if strategy == "hospital-first":
                    continue
                path = integrals / f"{hazard}__{resource}__{strategy}__INTEGRALS.npz"
                with np.load(path, allow_pickle=False) as z:
                    candidate = z["M1_UTILITY_003__normalized_burden_hr"].copy()
                    if not np.array_equal(z["physical_hashes"], reference_hashes):
                        raise ValueError("Tract strategy comparison is not physically paired")
                delta = candidate - reference
                valid = np.isfinite(delta)
                n = valid.sum(axis=0)
                mean = np.divide(np.nansum(delta, axis=0), n,
                                 out=np.full(len(tracts), np.nan), where=n>0)
                labels = np.full(len(tracts), "near-zero", dtype="<U10")
                labels[mean < -1] = "improved"
                labels[mean > 1] = "worsened"
                labels[~np.isfinite(mean)] = "unresolved"
                records.extend(dict(hazard=hazard, resource_scenario=resource,
                                    strategy_id=strategy, reference_strategy="hospital-first",
                                    tract_id=tracts[j], quartile=q[j], population=pop[j],
                                    paired_mean_delta_burden_hr=float(mean[j]),
                                    valid_paired_realizations=int(n[j]),
                                    probability_delta_below_zero=float(np.mean(delta[valid[:, j], j]<0)) if n[j] else np.nan,
                                    mean_effect_classification=labels[j]) for j in range(len(tracts)))
                for label, mask in (("improved", delta < -1), ("near-zero", abs(delta) <= 1),
                                    ("worsened", delta > 1), ("unresolved", ~valid)):
                    if label != "unresolved":
                        mask &= valid
                    represented_pop = mask @ pop
                    classification.append(dict(hazard=hazard, resource_scenario=resource,
                                               strategy_id=strategy, reference_strategy="hospital-first",
                                               classification_scope="per_realization_mean",
                                               classification=label,
                                               mean_population=float(represented_pop.mean()),
                                               domain_population=float(pop.sum()),
                                               mean_population_fraction=float(represented_pop.mean()/pop.sum())))
                for label in ("improved", "near-zero", "worsened", "unresolved"):
                    use = labels == label
                    classification.append(dict(hazard=hazard, resource_scenario=resource,
                                               strategy_id=strategy, reference_strategy="hospital-first",
                                               classification_scope="mean_paired_effect",
                                               classification=label,
                                               mean_population=float(pop[use].sum()),
                                               domain_population=float(pop.sum()),
                                               mean_population_fraction=float(pop[use].sum()/pop.sum())))
            if resource == "C57_D1":
                for strategy in ["unconstrained", *SCHEDULED]:
                    path = integrals / f"{hazard}__{resource}__{strategy}__INTEGRALS.npz"
                    with np.load(path, allow_pickle=False) as z:
                        m1 = z["M1_UTILITY_003__normalized_burden_hr"]
                        m0 = z["M0_JULY_003__normalized_burden_hr"]
                        difference = m1 - m0
                    average = np.nanmean(difference, axis=0)
                    mapping_shift.extend(dict(hazard=hazard, strategy_id=strategy,
                                              tract_id=tracts[j], population=pop[j],
                                              mean_M1_minus_M0_burden_hr=float(average[j]))
                                         for j in range(len(tracts)))
    return pd.DataFrame(records), pd.DataFrame(classification), pd.DataFrame(mapping_shift)


def build_formal_results(root: Path, *, executable_code_sha: str) -> dict:
    root = Path(root)
    output = root / "Formal_Results"
    output.mkdir(exist_ok=True)
    logistics = _logistics(root)
    primary = _primary_summary(root, logistics)
    effects = _paired_strategy_effects(primary)
    from r1_mapping_gate_robustness import mapping_cases
    from r1_mapping import ROOT
    maps, _ = mapping_cases()
    meta = pd.read_csv(ROOT / "R1_Comment1_July92_Utility_Constraint" /
                       "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
                       dtype={"tract_id": str}).set_index("tract_id")
    from r1_formal_offline import PreparedMapping
    stations = pd.read_csv(ROOT / "Data" / "working_area_substations_with_fragility.csv",
                           dtype={"ID": str}).ID.astype(str).to_numpy()
    prepared = {name: PreparedMapping.from_frame(name, w, stations, meta.population,
                 meta.SOVI_quartile, set(meta.index[meta.hospital_tract]))
                for name, w in maps.items() if name in ("M0_JULY_003", "M1_UTILITY_003")}
    tract, classification, mapping_shift = _tract_effects(root, prepared,
                                                            meta.population, meta.SOVI_quartile)
    paths = {
        "primary": output / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",
        "paired": output / "PAIRED_STRATEGY_EFFECTS.csv",
        "tract": output / "TRACT_PAIRED_EFFECTS.parquet",
        "classification": output / "TRACT_CLASSIFICATION_POPULATION.csv",
        "mapping_shift": output / "TRACT_MAPPING_SHIFT.parquet",
    }
    primary.to_parquet(paths["primary"], index=False)
    effects.to_csv(paths["paired"], index=False)
    tract.to_parquet(paths["tract"], index=False)
    classification.to_csv(paths["classification"], index=False)
    mapping_shift.to_parquet(paths["mapping_shift"], index=False)
    result = dict(status="FORMAL_FROZEN_MATRIX_V1", executable_code_commit_sha=executable_code_sha,
                  primary_rows=len(primary), paired_effect_rows=len(effects),
                  tract_effect_rows=len(tract), classification_rows=len(classification),
                  mapping_shift_rows=len(mapping_shift),
                  sha256={name: sha256_file(path) for name, path in paths.items()})
    (output / "FORMAL_RESULTS_INDEX.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return result
