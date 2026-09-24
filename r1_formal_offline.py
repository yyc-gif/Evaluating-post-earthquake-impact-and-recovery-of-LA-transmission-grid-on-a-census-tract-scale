"""Exact-event evaluation of saved July92 states under frozen tract mappings.

This is algebraically the existing mapping/gate evaluator: because mapping is
fixed in time, W times a left-rectangle station integral equals the integral
of W times station state.  No scheduler, sampling, or source gate is here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


def weighted_gini_exact(values: np.ndarray, population: np.ndarray) -> float:
    """O(n log n) form of the retained population-weighted pairwise Gini."""
    x = np.asarray(values, float)
    w = np.asarray(population, float)
    keep = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[keep], w[keep]
    if not len(x):
        return float("nan")
    if (x < 0).any() or (w < 0).any():
        raise ValueError("Burden/Gini population must be nonnegative")
    total_wx = float(np.dot(w, x))
    if total_wx == 0:
        return 0.0
    order = np.argsort(x, kind="stable")
    x, w = x[order], w[order]
    before_w = np.cumsum(w) - w
    before_wx = np.cumsum(w * x) - w * x
    numerator = float(np.sum(w * (x * before_w - before_wx)))
    return numerator / (float(w.sum()) * total_wx)


@dataclass(frozen=True)
class PreparedMapping:
    name: str
    tract_ids: np.ndarray
    station_ids: np.ndarray
    weight: np.ndarray
    population: np.ndarray
    quartile: np.ndarray
    hospital: np.ndarray

    @classmethod
    def from_frame(cls, name: str, frame: pd.DataFrame, station_ids,
                   population: pd.Series, quartile: pd.Series,
                   hospital_tracts) -> "PreparedMapping":
        if frame.index.has_duplicates or frame.columns.has_duplicates:
            raise ValueError("Mapping identities are duplicated")
        ids = np.asarray(list(map(str, station_ids)), dtype=str)
        if set(map(str, frame.columns)) != set(ids):
            raise ValueError("Mapping does not cover the frozen stations")
        ordered = frame.reindex(columns=ids)
        w = np.ascontiguousarray(ordered.to_numpy(float))
        if not np.isfinite(w).all() or (w < 0).any() or (w.sum(axis=1) > 1 + 1e-12).any():
            raise ValueError("Mapping weights are invalid")
        tracts = np.asarray(list(map(str, ordered.index)), dtype=str)
        p = population.reindex(tracts).to_numpy(float)
        q = quartile.reindex(tracts).to_numpy(str)
        if not np.isfinite(p).all() or (p < 0).any() or not np.isin(q, ["Q1", "Q2", "Q3", "Q4"]).all():
            raise ValueError("Population/quartiles are incomplete")
        hospital = np.isin(tracts, list(map(str, hospital_tracts)))
        return cls(name, tracts, ids, w, p, q, hospital)


def evaluate_exact_event_arrays(*, mapping: PreparedMapping, event_time_hr,
                                f, e, L_self, L_threshold, L_source, L_total):
    time = np.asarray(event_time_hr, float)
    if time.ndim != 1 or len(time) < 2 or time[0] != 0 or np.any(np.diff(time) <= 0):
        raise ValueError("Event time must be strictly increasing from zero")
    values = {name: np.asarray(value, float) for name, value in
              {"f": f, "e": e, "L_self": L_self, "L_threshold": L_threshold,
               "L_source": L_source, "L_total": L_total}.items()}
    shape = (len(time), len(mapping.station_ids))
    if any(x.shape != shape for x in values.values()):
        raise ValueError("Event arrays differ from mapping station/time dimensions")
    known = np.isfinite(values["f"][0])
    if any(not np.array_equal(np.isfinite(v), np.broadcast_to(known, shape)) for v in values.values()):
        raise ValueError("Event identification mask is inconsistent")
    station = {name: np.sum(np.nan_to_num(values[name][:-1]) * np.diff(time)[:, None], axis=0)
               for name in ("L_self", "L_threshold", "L_source", "L_total")}
    if np.max(np.abs(station["L_self"] + station["L_threshold"] + station["L_source"] - station["L_total"])) > 1e-10:
        raise ValueError("Station loss accounting differs")
    w = mapping.weight
    resolved = w[:, known].sum(axis=1)
    eligible = resolved > 1e-15
    component = {name: w @ integral for name, integral in station.items()}
    burden = np.divide(component["L_total"], resolved,
                       out=np.full(len(resolved), np.nan), where=eligible)
    p = mapping.population
    denominator_pop = float(p[eligible].sum())
    denominator_mass = float(np.dot(p, resolved))
    summary = {
        "population_weighted_normalized_burden_hr":
            float(np.dot(p[eligible], burden[eligible]) / denominator_pop) if denominator_pop else np.nan,
        "population_resolved_mass_weighted_burden_hr":
            float(np.dot(p, component["L_total"]) / denominator_mass) if denominator_mass else np.nan,
        "represented_population": denominator_pop,
        "population_times_resolved_mass": denominator_mass,
        "unresolved_population": float(p[~eligible].sum()),
        "resolved_tract_count": int(eligible.sum()),
        "unresolved_tract_count": int((~eligible).sum()),
        "horizon_hr": float(time[-1]),
        "burden_gini": weighted_gini_exact(burden, p),
    }
    for label in ("Q1", "Q2", "Q3", "Q4"):
        use = eligible & (mapping.quartile == label)
        denom = float(p[use].sum())
        summary[f"burden_{label}_hr"] = float(np.dot(p[use], burden[use]) / denom) if denom else np.nan
    summary["signed_Q4_minus_Q1_hr"] = summary["burden_Q4_hr"] - summary["burden_Q1_hr"]
    summary["absolute_Q4_minus_Q1_hr"] = abs(summary["signed_Q4_minus_Q1_hr"])
    hosp = eligible & mapping.hospital
    summary["hospital_mean_normalized_burden_hr"] = float(np.mean(burden[hosp])) if hosp.any() else np.nan
    station_mass = mapping.weight.T @ p
    available = np.nan_to_num(values["e"]) @ station_mass
    curve = available / denominator_mass if denominator_mass else np.full(len(time), np.nan)
    for target, label in ((.5, "T50"), (.8, "T80"), (.9, "T90")):
        hit = np.flatnonzero(curve >= target)
        summary[f"population_{label}_hr"] = float(time[hit[0]]) if len(hit) else np.nan
    for name in ("L_self", "L_threshold", "L_source", "L_total"):
        summary[name + "_population_mass_weighted_hr"] = (
            float(np.dot(p, component[name]) / denominator_mass) if denominator_mass else np.nan)
    total = summary["L_total_population_mass_weighted_hr"]
    for name in ("L_self", "L_threshold", "L_source"):
        summary[name + "_fraction"] = summary[name + "_population_mass_weighted_hr"] / total if total > 0 else np.nan
    tract = dict(resolved_mass=resolved, normalized_burden_hr=burden,
                 restoration_burden_mass_hr=np.where(eligible, component["L_total"], np.nan),
                 status=np.where(eligible, "resolved", "unresolved"))
    for name in ("L_self", "L_threshold", "L_source", "L_total"):
        tract[name + "_mass_hr"] = np.where(eligible, component[name], np.nan)
    return summary, tract, station


def evaluate_frozen_archive_shard(*, input_folder: Path, output_folder: Path,
                                  hazard: str, strategy: str, resource_case: str,
                                  population: pd.Series, quartile: pd.Series,
                                  hospital_tracts, mappings: dict,
                                  graph, sources, physical_hashes: dict,
                                  trajectory_code_sha: str, offline_code_sha: str,
                                  matrix_sha256: str,
                                  H_eval_hr: float, all_robustness: bool) -> dict:
    """Evaluate one 1000-realization shard, retaining compact exact integrals.

    Stage 4/5 schedules and physical samples are never invoked here.  Shards
    are committed atomically and can be checked/reused by identical identity.
    """
    from r1_formal_archive import inspect_formal_archive, sha256_file
    from r1_mapping_gate_robustness import GATE_CASES
    from r1_source_gate import evaluate_source_gate

    input_folder, output_folder = Path(input_folder), Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    stem = f"{hazard}__{resource_case}__{strategy}"
    summary_path = output_folder / (stem + "__SUMMARY.parquet")
    integral_path = output_folder / (stem + "__INTEGRALS.npz")
    record_path = output_folder / (stem + "__EVALUATION.json")
    map_names = (list(mappings) if all_robustness else
                 ["M0_JULY_003", "M1_UTILITY_003"] if resource_case == "C57_D1" else
                 ["M1_UTILITY_003"])
    gate_names = list(GATE_CASES) if all_robustness else ["G1_BASELINE_050"]
    identity = dict(hazard=hazard, strategy=strategy, resource_case=resource_case,
                    trajectory_executable_code_commit_sha=trajectory_code_sha,
                    offline_executable_code_commit_sha=offline_code_sha,
                    matrix_sha256=matrix_sha256, H_eval_hr=H_eval_hr,
                    mapping_cases=map_names, gate_cases=gate_names,
                    physical_hashes_sha256=hashlib.sha256(("\n".join(
                        physical_hashes[f"{hazard}__evaluation_{i:04d}"] for i in range(1000))+"\n").encode()).hexdigest())
    exists = [path.exists() for path in (summary_path, integral_path, record_path)]
    if any(exists):
        if not all(exists):
            raise ValueError("Partial formal offline shard exists")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record["identity"] != identity or record["status"] != "FORMAL_FROZEN_MATRIX_V1":
            raise ValueError("Formal offline shard identity changed on resume")
        if sha256_file(summary_path) != record["summary_sha256"] or sha256_file(integral_path) != record["integral_sha256"]:
            raise ValueError("Formal offline shard contents changed on resume")
        return dict(status="reused", **record)
    if all_robustness:
        map_names = list(mappings)
    station_ids = np.array(next(iter(mappings.values())).station_ids)
    prepared = {name: mappings[name] for name in map_names}
    common_names = ["M0_JULY_003", "M1_UTILITY_003", "M3_SCE_SUPPORTED"] if all_robustness else []
    common = None
    if all_robustness:
        support = mappings["M3_SCE_SUPPORTED"]
        common_ids = support.tract_ids[support.weight.sum(axis=1) > 0]
        if len(common_ids) != 320:
            raise ValueError("SCE common positive-mass domain differs from frozen 320")
        common = {}
        for name in common_names:
            base = mappings[name]
            take = pd.Index(base.tract_ids).get_indexer(common_ids)
            if (take < 0).any():
                raise ValueError("SCE common domain cannot be selected from mapping")
            common[name] = PreparedMapping(name, base.tract_ids[take], base.station_ids,
                                           base.weight[take], base.population[take],
                                           base.quartile[take], base.hospital[take])
    summaries = []
    integral_rows = {gate: {name: [] for name in
                     ("L_self", "L_threshold", "L_source", "L_total")}
                     for gate in gate_names}
    primary_tract = {name: [] for name in
                     ("M1_UTILITY_003", "M0_JULY_003") if name in prepared}
    for sample_index in range(1000):
        realization_id = f"{hazard}__evaluation_{sample_index:04d}"
        manifest_path = input_folder / (realization_id + ".json")
        if not manifest_path.is_file():
            raise ValueError("Formal station trajectory is incomplete")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_identity = manifest["identity"]
        if (source_identity["hazard"] != hazard or source_identity["strategy"] != strategy or
                source_identity["resource_scenario"] != resource_case or
                source_identity["realization_id"] != realization_id or
                source_identity["physical_sample_hash"] != physical_hashes[realization_id] or
                source_identity["executable_code_commit_sha"] != trajectory_code_sha or
                source_identity["event_horizon_hr"] != H_eval_hr or
                source_identity["mapping_method_id"] != "M1_UTILITY_003"):
            raise ValueError("Formal station trajectory identity mismatch")
        inspect_formal_archive(input_folder, identity=source_identity, stem=realization_id)
        with np.load(input_folder / (realization_id + ".npz"), allow_pickle=False) as saved:
            if not np.array_equal(saved["station_ids"].astype(str), station_ids):
                raise ValueError("Formal station IDs changed within offline shard")
            time = saved["event_time_hr"].copy()
            f = saved["f"].copy()
            base_arrays = {name: saved[name].copy() for name in
                           ("e", "L_self", "L_threshold", "L_source", "L_total")}
        for gate in gate_names:
            if gate == "G1_BASELINE_050":
                arrays = dict(f=f, **base_arrays)
            else:
                mode, threshold = GATE_CASES[gate]
                raw = pd.DataFrame(f, index=time, columns=station_ids)
                trace = evaluate_source_gate(raw, graph, sources, mode=mode, threshold=threshold)
                arrays = {name: getattr(trace, name).to_numpy() for name in
                          ("f", "e", "L_self", "L_threshold", "L_source", "L_total")}
            station_integrals = None
            for name, prepared_map in prepared.items():
                summary, tract, station = evaluate_exact_event_arrays(
                    mapping=prepared_map, event_time_hr=time, **arrays)
                if station_integrals is None:
                    station_integrals = station
                summaries.append(dict(hazard=hazard, realization_id=realization_id,
                                      strategy_id=strategy, resource_scenario=resource_case,
                                      mapping=name, gate=gate,
                                      comparison_domain="mapping_native_domain", **summary))
                if gate == "G1_BASELINE_050" and name in primary_tract:
                    primary_tract[name].append(tract["normalized_burden_hr"])
            for name in common_names:
                summary, _, _ = evaluate_exact_event_arrays(
                    mapping=common[name], event_time_hr=time, **arrays)
                summaries.append(dict(hazard=hazard, realization_id=realization_id,
                                      strategy_id=strategy, resource_scenario=resource_case,
                                      mapping=name, gate=gate,
                                      comparison_domain="SCE_common_positive_support", **summary))
            for name in integral_rows[gate]:
                integral_rows[gate][name].append(station_integrals[name])
    summary = pd.DataFrame(summaries)
    payload = {f"{gate}__{name}": np.stack(values)
               for gate, fields in integral_rows.items() for name, values in fields.items()}
    payload.update({f"{name}__normalized_burden_hr": np.stack(values)
                    for name, values in primary_tract.items()})
    payload["station_ids"] = station_ids
    payload["physical_hashes"] = np.array([physical_hashes[f"{hazard}__evaluation_{i:04d}"]
                                          for i in range(1000)], dtype=str)
    for path, writer in ((summary_path, lambda p: summary.to_parquet(p, index=False)),
                         (integral_path, lambda p: np.savez_compressed(p, **payload))):
        fd, name = tempfile.mkstemp(prefix=path.stem + ".", suffix=path.suffix, dir=output_folder)
        os.close(fd)
        temp = Path(name)
        try:
            writer(temp)
            os.replace(temp, path)
        finally:
            temp.unlink(missing_ok=True)
    record = dict(status="FORMAL_FROZEN_MATRIX_V1", identity=identity,
                  realization_count=1000, summary_row_count=len(summary),
                  summary_sha256=sha256_file(summary_path),
                  integral_sha256=sha256_file(integral_path))
    fd, name = tempfile.mkstemp(prefix=stem + ".", suffix=".json", dir=output_folder)
    os.close(fd)
    temp = Path(name)
    try:
        temp.write_text(json.dumps(record, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        os.replace(temp, record_path)
    finally:
        temp.unlink(missing_ok=True)
    return dict(status="written", **record)


def evaluate_all_frozen_archives(*, output_root: Path, context: dict,
                                 matrix_id: str, matrix_sha256: str,
                                 offline_code_sha: str) -> dict:
    """Original main entry's offline Stage 6 precursor on saved station states."""
    from r1_final_matrix import HAZARDS, SCHEDULED
    from r1_formal_archive import sha256_file
    from r1_mapping import load_mapping
    from r1_mapping_gate_robustness import mapping_cases

    root = Path(output_root)
    trajectory_identity = json.loads((root / "TRAJECTORY_EXECUTION_IDENTITY.json").read_text(encoding="utf-8"))
    if trajectory_identity["matrix_id"] != matrix_id or trajectory_identity["matrix_sha256"] != matrix_sha256:
        raise ValueError("Formal trajectory executable identity differs from matrix")
    trajectory_sha = trajectory_identity["executable_code_commit_sha"]
    horizon = json.loads((root / "Formal_Schedule_Prepass" / "EVALUATION_HORIZON.json").read_text(encoding="utf-8"))
    if horizon["matrix_id"] != matrix_id or horizon["schedule_shards"] != 80:
        raise ValueError("Frozen horizon/schedule prepass is incomplete")
    H_eval_hr = float(horizon["H_eval_hr"])
    physical = json.loads((root / "Stage 1 Output_expanded" / "PHYSICAL_INPUTS_FROZEN.json").read_text(encoding="utf-8"))
    if physical["matrix_id"] != matrix_id or physical["evaluation_count"] != 4000 or physical["planning_count"] != 64:
        raise ValueError("Frozen physical input manifest differs from matrix")
    from r1_mapping import ROOT
    meta = pd.read_csv(ROOT / "R1_Comment1_July92_Utility_Constraint" /
                       "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
                       dtype={"tract_id": str}).set_index("tract_id")
    frames, candidates = mapping_cases()
    production_file = load_mapping(ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv")
    m1 = frames["M1_UTILITY_003"]
    np.testing.assert_allclose(m1.to_numpy(), production_file.reindex(
        index=m1.index, columns=m1.columns, fill_value=0).to_numpy(), rtol=0, atol=1e-12)
    if len(candidates) != 337 or len(meta) != 2315:
        raise ValueError("Frozen tract mapping/evidence domain differs")
    prepared = {name: PreparedMapping.from_frame(name, frame, context["ids"],
                 meta.population, meta.SOVI_quartile, set(meta.index[meta.hospital_tract]))
                for name, frame in frames.items()}
    out = root / "Formal_Offline_Evaluation"
    out.mkdir(exist_ok=True)
    records = []
    total_rows = 0
    for hazard in HAZARDS:
        cases = ["C57_D1"]
        if hazard == "2pc50":
            cases += ["C29_D1", "C86_D1", "C114_D1", "C57_D075", "C57_D125", "C57_D150"]
        for resource in cases:
            strategies = ["unconstrained", *SCHEDULED] if resource == "C57_D1" else SCHEDULED
            for strategy in strategies:
                source = root / "Formal_Trajectories" / hazard / resource / strategy
                if not source.is_dir():
                    raise ValueError("Formal trajectory shard is missing")
                result = evaluate_frozen_archive_shard(
                    input_folder=source, output_folder=out,
                    hazard=hazard, strategy=strategy, resource_case=resource,
                    population=meta.population, quartile=meta.SOVI_quartile,
                    hospital_tracts=set(meta.index[meta.hospital_tract]),
                    mappings=prepared, graph=context["G"], sources=context["sources"],
                    physical_hashes=physical["sample_hashes"],
                    trajectory_code_sha=trajectory_sha, offline_code_sha=offline_code_sha,
                    matrix_sha256=matrix_sha256,
                    H_eval_hr=H_eval_hr,
                    all_robustness=(hazard == "2pc50" and resource == "C57_D1"))
                records.append(dict(hazard=hazard, resource_scenario=resource,
                                    strategy=strategy, status=result["status"],
                                    summary_rows=result["summary_row_count"],
                                    summary_sha256=result["summary_sha256"],
                                    integral_sha256=result["integral_sha256"]))
                total_rows += result["summary_row_count"]
    if len(records) != 84 or total_rows != 462000:
        raise ValueError("Formal offline shard/summary count differs from frozen matrix")
    summary_paths = [out / f"{row['hazard']}__{row['resource_scenario']}__{row['strategy']}__SUMMARY.parquet"
                     for row in records]
    summary_path = out / "FORMAL_REALIZATION_STRATEGY_SUMMARY.parquet"
    if summary_path.exists():
        existing = pd.read_parquet(summary_path)
        if len(existing) != total_rows:
            raise ValueError("Existing formal summary row count differs")
    else:
        pd.concat([pd.read_parquet(path) for path in summary_paths],
                  ignore_index=True).to_parquet(summary_path, index=False)
    final = dict(status="FORMAL_FROZEN_MATRIX_V1", matrix_id=matrix_id,
                 trajectory_executable_code_commit_sha=trajectory_sha,
                 offline_executable_code_commit_sha=offline_code_sha,
                 offline_shards=len(records), summary_rows=total_rows,
                 H_eval_hr=H_eval_hr,
                 consolidated_summary_sha256=sha256_file(summary_path))
    (out / "FORMAL_OFFLINE_INDEX.json").write_text(json.dumps(final, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    pd.DataFrame(records).to_csv(out / "FORMAL_OFFLINE_SHARDS.csv", index=False)
    return final
