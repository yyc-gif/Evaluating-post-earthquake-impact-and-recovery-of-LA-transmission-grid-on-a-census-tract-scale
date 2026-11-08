"""Paired event-level accounting for the frozen GA vs Impact-first comparison.

This is post-processing only. It reads the completed 2,000-realization
validation capsule; it does not sample physical damage, schedule repairs, or
run the GA. The event decomposition is an exact accounting identity for the
saved source-loss step curves, not a causal intervention attribution.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ARCHIVE_SHA256 = "74d83734549c83b7bcb57270a07db3ab4c696d4384c5a851461184cfcb28947d"
ARCHIVE_SIZE = 694277779
FREEZE_SHA256 = "45d157c0a3b9460d7c29e389b649afef0f0e6bc568bfba8eb773f9b5b974ae15"
GA_SEQUENCE_SHA256 = "8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab"
IMPACT_SEQUENCE_SHA256 = "d75ee1dc0fed0671b40d7f539d1e456ea42402105554cb1eb41ab3ec41bc9168"
MAPPING_SHA256 = "472aaa865e74b0d613e60e480e8da46d13604056048b90ba1f1f429060489446"
GRAPH_SHA256 = "1a3073240a6dca3e902e0bf5c2b975c67ff100892d85f007270e9855250bd225"
SOURCE_SHA256 = "892f5ec3e9a260db138c7fb2454dea09fcb75a8989ef13695aefca417b8c2955"
VALIDATION_SEED_PREFIX = [202610091, 3, 2]
N_REALIZATIONS = 2000
HORIZON_HR = 480.0
TOTAL_POPULATION_EXPECTED = 9066522.0
BOOTSTRAP_REPLICATES = 20000
BOOTSTRAP_SEED = 2026100901
INITIAL_BY_DS = {0: 1.0, 1: 0.5, 2: 0.09, 3: 0.04, 4: 0.03}
POLICY_GA = "ga-final-method-candidate"
POLICY_IMPACT = "impact-first"
COMPONENT_COLUMNS = {
    "self": "L_self_population_mass_weighted_hr",
    "threshold": "L_threshold_population_mass_weighted_hr",
    "source": "L_source_population_mass_weighted_hr",
    "total": "L_total_population_mass_weighted_hr",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _long_path(path: str | Path) -> str:
    raw = str(path)
    if raw.startswith("\\\\?\\"):
        return raw
    raw = os.path.abspath(raw)
    if os.name == "nt" and len(raw) >= 240 and not raw.startswith("\\\\?\\"):
        raw = "\\\\?\\" + raw
    return raw


def _path_arg(value: str) -> Path:
    """Resolve Windows long input paths without copying frozen source files."""
    return Path(_long_path(value))


def sequence_hash(sequence: list[str] | tuple[str, ...]) -> str:
    return sha256_bytes(("\n".join(map(str, sequence)) + "\n").encode("utf-8"))


def _read_json(payload: bytes | Path):
    if isinstance(payload, Path):
        with open(_long_path(payload), "r", encoding="utf-8") as stream:
            return json.load(stream)
    return json.loads(payload.decode("utf-8"))


def load_mapping(path: Path, station_ids: list[str]):
    station_index = {station: j for j, station in enumerate(station_ids)}
    population_by_tract: dict[str, float] = {}
    row_weights: dict[str, float] = defaultdict(float)
    station_mass = np.zeros(len(station_ids), dtype=float)
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"tract_id", "substation_id", "weight", "population"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"M1 mapping lacks required columns: {required}")
        seen = set()
        for row in reader:
            tract = str(row["tract_id"])
            station = str(row["substation_id"])
            key = (tract, station)
            if key in seen:
                raise ValueError(f"Duplicate M1 tract-station row: {key}")
            seen.add(key)
            weight = float(row["weight"])
            population = float(row["population"])
            if not np.isfinite([weight, population]).all() or weight < 0 or population < 0:
                raise ValueError("M1 contains an invalid weight or population")
            if station not in station_index:
                raise ValueError(f"Unexpected M1 station: {station}")
            if tract in population_by_tract and population_by_tract[tract] != population:
                raise ValueError(f"Inconsistent frozen population for tract {tract}")
            population_by_tract[tract] = population
            row_weights[tract] += weight
            station_mass[station_index[station]] += weight * population
    if len(population_by_tract) != 2315:
        raise ValueError(f"Expected 2,315 M1 tracts, found {len(population_by_tract)}")
    max_row_error = max(abs(value - 1.0) for value in row_weights.values())
    total_population = float(sum(population_by_tract.values()))
    if max_row_error > 1e-12 or abs(total_population - TOTAL_POPULATION_EXPECTED) > 1e-7:
        raise ValueError("M1 row-mass or frozen-population identity failed")
    if abs(station_mass.sum() - total_population) > 1e-7:
        raise ValueError("Mapped station dependency mass does not conserve population")
    return station_mass, total_population, set(population_by_tract), {
        "tract_count": len(population_by_tract),
        "tract_id_sha256": sha256_bytes(("\n".join(sorted(population_by_tract)) + "\n").encode("utf-8")),
        "population": total_population,
        "max_row_mass_error": max_row_error,
        "station_population_mass_sum": float(station_mass.sum()),
    }


def load_graph(path: Path, source_path: Path, station_ids: list[str]):
    station_index = {station: j for j, station in enumerate(station_ids)}
    adjacency = [set() for _ in station_ids]
    edge_count = 0
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            u, v = str(row["u"]), str(row["v"])
            if u not in station_index or v not in station_index or u == v:
                raise ValueError(f"Invalid frozen graph edge: {u}, {v}")
            i, j = station_index[u], station_index[v]
            adjacency[i].add(j)
            adjacency[j].add(i)
            edge_count += 1
    if edge_count != 318 or any(not neighbors for neighbors in adjacency):
        raise ValueError("Frozen graph is not the expected 92-node / 318-edge graph")
    with open(_long_path(source_path), "r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    id_col = next((c for c in ("substation_id", "HIFLD_ID", "ID", "id", "node_id")
                   if rows and c in rows[0]), None)
    if id_col is None:
        raise ValueError("Frozen source table has no station ID field")
    role_cols = [c for c in ("level", "role", "source_level", "source_type", "active_set")
                 if rows and c in rows[0]]
    sources = set()
    station_metadata = {}
    for row in rows:
        roles = " ".join(str(row.get(c, "")).lower() for c in role_cols)
        station = str(row[id_col])
        if station in station_index:
            station_metadata[station] = {
                "name": str(row.get("agreed_label") or row.get("NAME") or row.get("name") or ""),
                "level": str(row.get("level") or ""),
                "source_type": str(row.get("source_type") or ""),
            }
        is_source = ("core" in roles or "import_interface_proxy" in roles
                     or "in_basin_generation_proxy" in roles)
        if is_source and not re.search(r"transit_hub_not_source|\btransit\b", roles):
            if station in station_index:
                sources.add(station_index[station])
    if len(sources) != 14:
        raise ValueError(f"Expected 14 frozen Core-source proxies, found {len(sources)}")
    return adjacency, sources, station_metadata


def source_connected(functionality: np.ndarray, adjacency, sources) -> np.ndarray:
    active = np.asarray(functionality, dtype=float) >= 0.5
    connected = np.zeros(active.size, dtype=bool)
    stack = [int(source) for source in sources if active[int(source)]]
    if stack:
        connected[stack] = True
    while stack:
        node = stack.pop()
        for neighbor in adjacency[node]:
            if active[neighbor] and not connected[neighbor]:
                connected[neighbor] = True
                stack.append(neighbor)
    return connected


def event_loss_components(f_before, F_before, C_before,
                          f_after, F_after, C_after,
                          event_stations, station_mass, total_population,
                          time_hr, horizon_hr=HORIZON_HR):
    """Return exact direct/other-station source-loss event integrals."""
    event_mask = np.zeros(len(station_mass), dtype=bool)
    event_mask[np.asarray(event_stations, dtype=int)] = True
    loss_before = np.asarray(f_before) * np.asarray(F_before) * (1.0 - np.asarray(C_before))
    loss_after = np.asarray(f_after) * np.asarray(F_after) * (1.0 - np.asarray(C_after))
    delta_loss = loss_after - loss_before
    remaining = max(0.0, float(horizon_hr) - float(time_hr))
    scale = remaining / float(total_population)
    direct = float(np.dot(station_mass[event_mask], delta_loss[event_mask]) * scale)
    external = float(np.dot(station_mass[~event_mask], delta_loss[~event_mask]) * scale)
    unlocked = (~event_mask) & np.asarray(F_before, bool) & np.asarray(F_after, bool)
    unlocked &= (~np.asarray(C_before, bool)) & np.asarray(C_after, bool)
    unlocked_mass = float(station_mass[unlocked].sum())
    unlocked_effective_mass = float(np.dot(station_mass[unlocked], np.asarray(f_after)[unlocked]))
    return {
        "direct_source_loss_delta_hr": direct,
        "external_source_loss_delta_hr": external,
        "unlocked_station_count": int(unlocked.sum()),
        "unlocked_dependency_mass_person_equiv": unlocked_mass,
        "unlocked_effective_service_mass_person_equiv": unlocked_effective_mass,
        "unlocked_station_indices": np.flatnonzero(unlocked).tolist(),
    }


def _new_downstream_counter():
    return {
        "source_loss_contribution_hr": {POLICY_IMPACT: 0.0, POLICY_GA: 0.0},
        "unlock_transition_count": {POLICY_IMPACT: 0, POLICY_GA: 0},
        "dependency_mass_person_equiv": {POLICY_IMPACT: 0.0, POLICY_GA: 0.0},
        "completion_time_sum_hr": {POLICY_IMPACT: 0.0, POLICY_GA: 0.0},
    }


def _paired_bootstrap_ci(matrix: np.ndarray):
    n, columns = matrix.shape
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    boot = np.empty((BOOTSTRAP_REPLICATES, columns), dtype=float)
    chunk = 250
    offset = 0
    while offset < BOOTSTRAP_REPLICATES:
        size = min(chunk, BOOTSTRAP_REPLICATES - offset)
        index = rng.integers(0, n, size=(size, n))
        boot[offset:offset + size] = matrix[index].mean(axis=1)
        offset += size
    return np.quantile(boot, [0.025, 0.975], axis=0)


def _load_sequence_pair(selected_path: Path, validation_dir: Path):
    selected = _read_json(selected_path)
    ga_sequence = list(map(str, selected["sequence"]))
    if len(ga_sequence) != 92 or len(set(ga_sequence)) != 92:
        raise ValueError("Selected GA sequence is not a unique ordering of all 92 stations")
    if sequence_hash(ga_sequence) != GA_SEQUENCE_SHA256 or selected.get("sequence_sha256") != GA_SEQUENCE_SHA256:
        raise ValueError("Selected GA sequence does not match the frozen SHA-256")
    comparator_path = validation_dir.parent / "FINAL_COMPARATOR_MANIFEST.json"
    comparator = _read_json(comparator_path)
    by_name = {item["strategy"]: item for item in comparator["ordered_policies"]}
    impact = list(map(str, by_name[POLICY_IMPACT]["sequence"]))
    if len(impact) != 92 or len(set(impact)) != 92:
        raise ValueError("Impact-first comparator is not a unique ordering of all 92 stations")
    ga_archived = list(map(str, by_name[POLICY_GA]["sequence"]))
    if sequence_hash(impact) != IMPACT_SEQUENCE_SHA256:
        raise ValueError("Impact-first sequence hash differs from frozen comparator")
    if sequence_hash(ga_archived) != GA_SEQUENCE_SHA256 or ga_archived != ga_sequence:
        raise ValueError("2,000-case GA comparator differs from the selected sequence")
    return ga_sequence, impact, comparator_path, selected


def _load_case_csv(payload: bytes):
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8-sig"))))


def _policy_trace(npz, policy_index, lengths, offsets):
    start = int(offsets[policy_index])
    end = start + int(lengths[policy_index])
    return {
        "times": np.asarray(npz["event_time_hr"][start:end], dtype=float),
        "f": np.asarray(npz["f"][start:end], dtype=float),
        "F": np.asarray(npz["F"][start:end], dtype=bool),
        "C": np.asarray(npz["C"][start:end], dtype=bool),
        "e": np.asarray(npz["e"][start:end], dtype=float),
        "component_integrals": np.asarray(npz["station_component_integrals_hr"][policy_index], dtype=float),
    }


def _integrate_components(trace, station_mass, total_population):
    dt = np.diff(trace["times"])
    if len(dt) == 0 or np.any(dt < 0) or abs(trace["times"][0]) > 1e-12 or abs(trace["times"][-1] - HORIZON_HR) > 1e-8:
        raise ValueError("Event trajectory does not span sorted [0, 480] h")
    f = trace["f"]
    F = trace["F"]
    C = trace["C"]
    components = {
        "self": 1.0 - f,
        "threshold": f * (~F),
        "source": f * F * (~C),
        "total": 1.0 - trace["e"],
    }
    integrals = {}
    station_integrals = {}
    for name, values in components.items():
        per_station = np.sum(values[:-1] * dt[:, None], axis=0)
        station_integrals[name] = per_station
        integrals[name] = float(np.dot(station_mass, per_station) / total_population)
    identity = integrals["self"] + integrals["threshold"] + integrals["source"] - integrals["total"]
    return integrals, station_integrals, float(abs(identity))


def _array_event_contribution(trace, task_rows, station_ids, station_mass,
                              total_population, policy, realization_index, realization_id,
                              station_result, trigger_result, downstream_result):
    index = {sid: i for i, sid in enumerate(station_ids)}
    by_time: dict[float, list[int]] = defaultdict(list)
    for row in task_rows:
        sid = str(row["task_id"])
        completion = float(row["completion_hr"])
        by_time[completion].append(index[sid])
        item = station_result[sid]
        item["rank"][policy][realization_index] = int(row["dispatch_rank"])
        item["completion"][policy][realization_index] = completion
        item["crew"][policy][realization_index] = str(row["crew_index"])
        item["travel"][policy][realization_index] = float(row["travel_hr"])
        item["arrival"][policy][realization_index] = float(row["arrival_hr"])
        item["duration"][policy][realization_index] = float(row["realized_duration_hr"])

    times = trace["times"]
    event_count = 0
    unlocked_transitions = 0
    dependency_mass = 0.0
    effective_mass = 0.0
    source_loss_initial = float(np.dot(
        station_mass,
        trace["f"][0] * trace["F"][0] * (~trace["C"][0]),
    ) / total_population)
    total_direct = 0.0
    total_external = 0.0
    max_downstream_identity_error = 0.0
    for completion, event_stations in sorted(by_time.items()):
        if completion <= 0.0 or completion >= HORIZON_HR:
            continue
        match = np.flatnonzero(np.isclose(times, completion, rtol=0.0, atol=1e-8))
        if match.size != 1:
            raise ValueError(f"{policy} event time not uniquely present in trajectory: {completion}")
        j = int(match[0])
        if j == 0:
            raise ValueError("Positive completion unexpectedly maps to initial state")
        before_f, after_f = trace["f"][j - 1], trace["f"][j]
        before_F, after_F = trace["F"][j - 1], trace["F"][j]
        before_C, after_C = trace["C"][j - 1], trace["C"][j]
        contribution = event_loss_components(
            before_f, before_F, before_C, after_f, after_F, after_C,
            event_stations, station_mass, total_population, completion,
        )
        direct = contribution["direct_source_loss_delta_hr"]
        external = contribution["external_source_loss_delta_hr"]
        remaining = max(0.0, HORIZON_HR - completion)
        delta_loss = (after_f * after_F * (1.0 - after_C)
                      - before_f * before_F * (1.0 - before_C))
        for station_index in event_stations:
            sid = str(station_ids[station_index])
            station_result[sid]["direct"][policy][realization_index] = float(
                station_mass[station_index] * delta_loss[station_index]
                * remaining / total_population
            )
        total_direct += direct
        total_external += external
        event_count += int(contribution["unlocked_station_count"] > 0)
        unlocked_transitions += contribution["unlocked_station_count"]
        dependency_mass += contribution["unlocked_dependency_mass_person_equiv"]
        effective_mass += contribution["unlocked_effective_service_mass_person_equiv"]
        event_label = (str(station_ids[event_stations[0]]) if len(event_stations) == 1
                       else "MULTI:" + ";".join(str(station_ids[x]) for x in sorted(event_stations)))
        trigger = trigger_result.setdefault(event_label, {"impact-first": 0.0, POLICY_GA: 0.0,
                                                           "unlock_events": {"impact-first": 0, POLICY_GA: 0},
                                                           "unlock_transitions": {"impact-first": 0, POLICY_GA: 0},
                                                           "dependency_mass_person_equiv": {"impact-first": 0.0, POLICY_GA: 0.0},
                                                           "effective_mass_person_equiv": {"impact-first": 0.0, POLICY_GA: 0.0},
                                                           "completion_sum_hr": {"impact-first": 0.0, POLICY_GA: 0.0},
                                                           "event_count": {"impact-first": 0, POLICY_GA: 0},
                                                           "downstream_stations": {}})
        trigger[policy] += external
        trigger["unlock_events"][policy] += int(contribution["unlocked_station_count"] > 0)
        trigger["unlock_transitions"][policy] += contribution["unlocked_station_count"]
        trigger["dependency_mass_person_equiv"][policy] += contribution["unlocked_dependency_mass_person_equiv"]
        trigger["effective_mass_person_equiv"][policy] += contribution["unlocked_effective_service_mass_person_equiv"]
        trigger["completion_sum_hr"][policy] += completion
        trigger["event_count"][policy] += 1
        unlocked_loss_sum = 0.0
        for downstream_index in contribution["unlocked_station_indices"]:
            downstream_id = str(station_ids[downstream_index])
            station_contribution = float(
                station_mass[downstream_index] * delta_loss[downstream_index]
                * remaining / total_population
            )
            unlocked_loss_sum += station_contribution
            global_row = downstream_result.setdefault(downstream_id, _new_downstream_counter())
            global_row["source_loss_contribution_hr"][policy] += station_contribution
            global_row["unlock_transition_count"][policy] += 1
            global_row["dependency_mass_person_equiv"][policy] += float(station_mass[downstream_index])
            global_row["completion_time_sum_hr"][policy] += completion
            trigger_row = trigger["downstream_stations"].setdefault(
                downstream_id, _new_downstream_counter()
            )
            trigger_row["source_loss_contribution_hr"][policy] += station_contribution
            trigger_row["unlock_transition_count"][policy] += 1
            trigger_row["dependency_mass_person_equiv"][policy] += float(station_mass[downstream_index])
            trigger_row["completion_time_sum_hr"][policy] += completion
        max_downstream_identity_error = max(
            max_downstream_identity_error, abs(unlocked_loss_sum - external)
        )
    return {
        "direct_source_loss_event_delta_hr": total_direct,
        "external_source_loss_event_delta_hr": total_external,
        "event_unlock_count": event_count,
        "external_station_unlock_transitions": unlocked_transitions,
        "external_dependency_mass_person_equiv": dependency_mass,
        "external_effective_service_mass_person_equiv": effective_mass,
        "source_loss_at_t0": source_loss_initial,
        "max_downstream_identity_error_hr": max_downstream_identity_error,
    }


def _mean_effect(vector):
    vector = np.asarray(vector, dtype=float)
    n = int(vector.size)
    mean = float(vector.mean())
    return {"mean": mean, "mcse": float(vector.std(ddof=1) / math.sqrt(n)),
            "p05": float(np.quantile(vector, 0.05)), "median": float(np.median(vector)),
            "p95": float(np.quantile(vector, 0.95)),
            "negative_count": int(np.sum(vector < 0)), "positive_count": int(np.sum(vector > 0)),
            "tie_count": int(np.sum(vector == 0))}


def _write_figures(output: Path, component_effects, source_category_diffs,
                   station_rows, source_curve_difference):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.titlesize": 11, "axes.labelsize": 9,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(1, 3, figsize=(14.2, 5.3), constrained_layout=True,
                             gridspec_kw={"width_ratios": [1.1, 1.0, 1.55]})
    ax = axes[0]
    order = ["self", "threshold", "source", "total"]
    labels = ["Self", "Threshold", "Source path", "Total"]
    means = np.array([component_effects[name]["mean"] for name in order])
    lo = np.array([component_effects[name]["bootstrap_95ci"][0] for name in order])
    hi = np.array([component_effects[name]["bootstrap_95ci"][1] for name in order])
    ax.axhline(0, color="#444444", lw=0.8)
    ax.bar(np.arange(4), means, color=["#6c8799", "#9ba6ad", "#2f887e", "#303d4b"], width=0.68)
    ax.errorbar(np.arange(4), means, yerr=np.vstack((means - lo, hi - means)),
                fmt="none", ecolor="#202020", capsize=3, lw=1.0)
    ax.set_xticks(np.arange(4), labels, rotation=25, ha="right")
    ax.set_ylabel("GA minus Impact-first (equivalent hours)")
    ax.set_title("Paired burden difference")
    ax.text(0.02, 0.02, "Negative favors GA", transform=ax.transAxes, fontsize=8)

    ax = axes[1]
    cats = ["Repaired stations'\nown source loss", "Other stations'\nsource-path change"]
    vals = [source_category_diffs["direct_source_loss_delta_hr"]["mean"],
            source_category_diffs["external_source_loss_delta_hr"]["mean"]]
    cis = [source_category_diffs["direct_source_loss_delta_hr"]["bootstrap_95ci"],
           source_category_diffs["external_source_loss_delta_hr"]["bootstrap_95ci"]]
    ax.axhline(0, color="#444444", lw=0.8)
    ax.bar(np.arange(2), vals, color=["#b66f55", "#2f887e"], width=0.62)
    for j, (value, ci) in enumerate(zip(vals, cis)):
        ax.errorbar(j, value, yerr=[[value-ci[0]], [ci[1]-value]], fmt="none",
                    ecolor="#202020", capsize=3, lw=1.0)
        ax.text(j, value * 0.5, f"{value:+.3f} h", ha="center", va="center",
                color="white", fontweight="bold", fontsize=8)
    ax.set_xticks(np.arange(2), cats)
    ax.set_ylabel("Paired source-loss contribution (h)")
    ax.set_title("Exact event accounting")

    ax = axes[2]
    favorable = sorted(station_rows, key=lambda x: x["external_source_loss_delta_hr"])[:4]
    offsetting = sorted(station_rows, key=lambda x: x["external_source_loss_delta_hr"], reverse=True)[:4]
    selected = favorable + offsetting
    selected = sorted(selected, key=lambda x: x["external_source_loss_delta_hr"])
    ypos = np.arange(len(selected))
    x = np.array([r["external_source_loss_delta_hr"] for r in selected])
    ax.axvline(0, color="#444444", lw=0.8)
    colors = ["#2f887e" if v < 0 else "#b66f55" for v in x]
    ax.barh(ypos, x, color=colors, height=0.68)
    labels = [f"{r['trigger_event']}  (rank {r['mean_rank_ga']:.1f} vs {r['mean_rank_impact']:.1f})"
              for r in selected]
    ax.set_yticks(ypos, labels, fontsize=7.4)
    ax.set_xlabel("External path-unlock source-loss contribution (h)")
    ax.set_title("Largest favorable and offsetting events")
    fig.suptitle("GA vs Impact-first: source-connectivity mechanism", fontsize=13, y=1.02)
    fig.savefig(_long_path(output / "GA_IMPACT_EVENT_MECHANISM.pdf"), bbox_inches="tight")
    fig.savefig(_long_path(output / "GA_IMPACT_EVENT_MECHANISM.png"), dpi=600, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.6, 4.7), constrained_layout=True)
    grid = source_curve_difference["time_hr"]
    mean = np.asarray(source_curve_difference["mean_ga_minus_impact_source_loss"], dtype=float)
    p05 = np.asarray(source_curve_difference["p05"], dtype=float)
    p95 = np.asarray(source_curve_difference["p95"], dtype=float)
    ax.axhline(0, color="#555555", lw=0.8)
    ax.fill_between(grid, p05, p95, color="#5d8d87", alpha=0.2,
                    label="5th-95th realization range")
    ax.plot(grid, mean, color="#246d67", lw=2.0, label="Mean paired difference")
    ax.set_xlabel("Hours after restoration begins")
    ax.set_ylabel("GA minus Impact-first source-path deficit")
    ax.set_title("Paired source-path deficit over time")
    ax.legend(frameon=False, loc="best")
    ax.text(0.02, 0.02, "Step states from the saved 2,000-realization event archive",
            transform=ax.transAxes, fontsize=8)
    fig.savefig(_long_path(output / "GA_IMPACT_SOURCE_PATH_TIME.pdf"), bbox_inches="tight")
    fig.savefig(_long_path(output / "GA_IMPACT_SOURCE_PATH_TIME.png"), dpi=600, bbox_inches="tight")
    plt.close(fig)


def analyze(args):
    archive = _path_arg(args.archive)
    validation_dir = _path_arg(args.validation_dir)
    selected_path = _path_arg(args.selected_sequence)
    mapping_path = _path_arg(args.mapping)
    graph_path = _path_arg(args.graph)
    source_path = _path_arg(args.sources)
    output = _path_arg(args.output)
    output.mkdir(parents=True, exist_ok=True)

    if archive.stat().st_size != ARCHIVE_SIZE or sha256_file(archive) != ARCHIVE_SHA256:
        raise ValueError("The 2,000-case LFS archive size/SHA-256 does not match the frozen identity")
    for path, expected, label in ((mapping_path, MAPPING_SHA256, "M1 mapping"),
                                  (graph_path, GRAPH_SHA256, "station graph"),
                                  (source_path, SOURCE_SHA256, "Core-source table")):
        if sha256_file(path) != expected:
            raise ValueError(f"{label} SHA-256 differs from the frozen input registry")

    ga_sequence, impact_sequence, comparator_path, selected_metadata = _load_sequence_pair(selected_path, validation_dir)
    manifest = _read_json(validation_dir / "FULL_ARCHIVE_MANIFEST.json")
    qa = _read_json(validation_dir / "POST_COMPLETION_QA.json")
    validation_receipt = _read_json(validation_dir / "fixed_2000_20261010" / "REPRODUCIBILITY_RECEIPT.json")
    run_identity = None
    station_ids = None
    station_mass = total_population = None
    mapping_tract_ids = None
    mapping_qa = None
    adjacency = source_indices = station_metadata = None
    tract_ids = None

    if qa.get("status") != "PASS" or qa.get("sample_count") != N_REALIZATIONS or qa.get("policy_record_count") != 26000:
        raise ValueError("Existing independent-validation completion QA is not a PASS for 2,000/26,000")
    if not qa.get("fixed_20000_bootstrap_reproduced", False):
        raise ValueError("Frozen 20,000-replicate bootstrap reproduction QA is incomplete")
    if (validation_receipt.get("status") != "INDEPENDENT_VALIDATION_COMPLETED"
            or validation_receipt.get("sample_count") != N_REALIZATIONS
            or validation_receipt.get("unique_physical_hashes") != N_REALIZATIONS):
        raise ValueError("Frozen independent-validation execution receipt is incomplete")

    n = N_REALIZATIONS
    deltas = {name: np.empty(n, dtype=float) for name in COMPONENT_COLUMNS}
    direct_delta = np.empty(n, dtype=float)
    external_delta = np.empty(n, dtype=float)
    integrated_source_delta = np.empty(n, dtype=float)
    per_policy_source = {POLICY_IMPACT: np.empty(n), POLICY_GA: np.empty(n)}
    absolute_policy_components = {
        policy: {component: np.empty(n, dtype=float) for component in COMPONENT_COLUMNS}
        for policy in (POLICY_IMPACT, POLICY_GA)
    }
    per_policy_unlock_events = {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)}
    per_policy_unlock_transitions = {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)}
    per_policy_unlock_mass = {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)}
    per_policy_unlock_effective_mass = {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)}
    rank_matrix = {POLICY_IMPACT: np.empty((n, 92)), POLICY_GA: np.empty((n, 92))}
    completion_matrix = {POLICY_IMPACT: np.empty((n, 92)), POLICY_GA: np.empty((n, 92))}
    travel_matrix = {POLICY_IMPACT: np.empty((n, 92)), POLICY_GA: np.empty((n, 92))}
    crew_matrix = {POLICY_IMPACT: np.empty((n, 92), dtype="U8"), POLICY_GA: np.empty((n, 92), dtype="U8")}
    station_records = {sid: {"direct": {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)},
                             "rank": {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)},
                             "completion": {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)},
                             "travel": {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)},
                             "crew_changed": np.zeros(n, dtype=bool)} for sid in []}
    external_records: dict[str, dict] = {}
    downstream_records: dict[str, dict] = {}
    source_curve_grid = np.arange(0.0, HORIZON_HR + 1.0, 1.0)
    source_curve = {POLICY_IMPACT: np.empty((n, source_curve_grid.size), dtype=float),
                    POLICY_GA: np.empty((n, source_curve_grid.size), dtype=float)}
    physical_hashes = set()
    physical_hash_by_realization = np.full(n, "", dtype="U64")
    max_gate_error = 0.0
    max_saved_integral_error = 0.0
    max_pair_event_identity_error = 0.0
    max_task_array_error = 0.0
    max_downstream_identity_error = 0.0
    case_file_checks = 0
    protocol_seed_identity_checks = 0

    with zipfile.ZipFile(archive, "r") as bundle:
        members = set(bundle.namelist())
        run_identity = _read_json(bundle.read("RUN_IDENTITY.json"))
        if run_identity.get("freeze_sha256") != FREEZE_SHA256 or run_identity.get("sample_size") != N_REALIZATIONS:
            raise ValueError("Archive RUN_IDENTITY does not match the fixed independent validation")
        if manifest.get("entry_count") != len(members):
            raise ValueError("Archive member count differs from the complete archive manifest")

        for realization_index in range(n):
            realization_id = f"2pc50__independent_{realization_index:04d}"
            base = f"cases/{realization_id}/"
            names = {name: base + name for name in ("COMPLETE.json", "PHYSICAL.json", "SUMMARY.csv",
                                                    "TASK_EXECUTION.csv", "TRAJECTORIES.npz")}
            if not all(name in members for name in names.values()):
                raise ValueError(f"Incomplete saved archive case {realization_id}")
            payloads = {key: bundle.read(value) for key, value in names.items()}
            complete = _read_json(payloads["COMPLETE.json"])
            if complete.get("status") != "COMPLETE_SHARED_REALIZATION" or complete["identity"].get("realization_id") != realization_id:
                raise ValueError(f"Invalid completion receipt for {realization_id}")
            for name, payload in payloads.items():
                if name == "COMPLETE.json":
                    continue
                leaf = names[name].split("/")[-1]
                digest = sha256_bytes(payload)
                expected_case = complete["files_sha256"].get(leaf)
                expected_archive = manifest["files"].get(names[name], {}).get("sha256")
                if digest != expected_case or digest != expected_archive:
                    raise ValueError(f"Case payload SHA-256 mismatch: {names[name]}")
                case_file_checks += 1

            physical = _read_json(payloads["PHYSICAL.json"])
            physical_id = str(physical["realization_id"])
            physical_hash = str(physical["physical_sha256"])
            physical_ds = np.asarray(physical["damage_state"], dtype=int)
            physical_duration = np.asarray(physical["duration_hr"], dtype=float)
            expected_entropy = VALIDATION_SEED_PREFIX + [realization_index]
            draw_name = f"physical/{realization_index:04d}/DRAW.json"
            if draw_name not in members:
                raise ValueError(f"Registered sample identity record is missing: {draw_name}")
            draw = _read_json(bundle.read(draw_name))
            draw_payload_sha = draw.pop("payload_sha256", None)
            if (draw_payload_sha is None
                    or sha256_bytes(json.dumps(draw, sort_keys=True).encode("utf-8")) != draw_payload_sha):
                raise ValueError(f"Registered draw-record digest mismatch at r={realization_index}")
            if (draw.get("r") != realization_index
                    or draw.get("entropy") != expected_entropy
                    or draw.get("freeze_sha256") != FREEZE_SHA256):
                raise ValueError(f"Frozen validation seed/freeze identity mismatch at {realization_id}")
            if (list(map(str, draw["station_ids"])) != list(map(str, physical["station_ids"]))
                    or not np.array_equal(np.asarray(draw["damage_state"], dtype=int), physical_ds)
                    or not np.array_equal(np.asarray(draw["duration_hr"], dtype=float), physical_duration)
                    or draw.get("physical_sha256") != physical_hash):
                raise ValueError(f"Registered draw identity does not match executed case {realization_id}")
            protocol_seed_identity_checks += 1
            if physical_ds.shape != (92,):
                raise ValueError(f"Damage-state vector is not the 92-station frozen order at {realization_id}")
            if physical_id != realization_id or complete["identity"].get("physical_sha256") != physical_hash:
                raise ValueError(f"Physical identity mismatch for {realization_id}")
            if physical_hash in physical_hashes:
                raise ValueError(f"Duplicate physical state hash in the independent cohort: {realization_id}")
            physical_hashes.add(physical_hash)
            physical_hash_by_realization[realization_index] = physical_hash
            if sha256_bytes(np.asarray(physical["damage_state"], dtype="<i8").tobytes()) != physical["damage_sha256"]:
                raise ValueError(f"Damage-state bytes fail their saved digest: {realization_id}")
            if sha256_bytes(np.asarray(physical["duration_hr"], dtype="<f8").tobytes()) != physical["duration_sha256"]:
                raise ValueError(f"Repair-duration bytes fail their saved digest: {realization_id}")

            npz = np.load(io.BytesIO(payloads["TRAJECTORIES.npz"]))
            ids = list(map(str, npz["station_ids"].tolist()))
            if station_ids is None:
                station_ids = ids
                if len(ids) != 92 or len(set(ids)) != 92 or set(ids) != set(map(str, physical["station_ids"])):
                    raise ValueError("Archive station identity is not the frozen 92-station set")
                station_mass, total_population, mapping_tract_ids, mapping_qa = load_mapping(mapping_path, station_ids)
                adjacency, source_indices, station_metadata = load_graph(graph_path, source_path, station_ids)
                station_records = {sid: {"direct": {POLICY_IMPACT: np.zeros(n), POLICY_GA: np.zeros(n)},
                                         "rank": {POLICY_IMPACT: np.full(n, np.nan), POLICY_GA: np.full(n, np.nan)},
                                         "completion": {POLICY_IMPACT: np.full(n, np.nan), POLICY_GA: np.full(n, np.nan)},
                                         "travel": {POLICY_IMPACT: np.full(n, np.nan), POLICY_GA: np.full(n, np.nan)},
                                         "crew": {POLICY_IMPACT: np.full(n, None, dtype=object), POLICY_GA: np.full(n, None, dtype=object)},
                                         "arrival": {POLICY_IMPACT: np.full(n, np.nan), POLICY_GA: np.full(n, np.nan)},
                                         "duration": {POLICY_IMPACT: np.full(n, np.nan), POLICY_GA: np.full(n, np.nan)},
                                         "crew_changed": np.zeros(n, dtype=bool)} for sid in station_ids}
            elif ids != station_ids:
                raise ValueError(f"Station array order changed at {realization_id}")
            if list(map(str, physical["station_ids"])) != station_ids:
                raise ValueError(f"Physical station order mismatch at {realization_id}")
            if npz["tract_ids"].size != 2315 or len(set(map(str, npz["tract_ids"].tolist()))) != 2315:
                raise ValueError(f"Tract identity domain mismatch at {realization_id}")
            case_tract_ids = list(map(str, npz["tract_ids"].tolist()))
            if tract_ids is None:
                tract_ids = case_tract_ids
                if set(tract_ids) != mapping_tract_ids:
                    raise ValueError(f"Archive tract GEOIDs differ from the M1 mapping at {realization_id}")
            elif case_tract_ids != tract_ids:
                raise ValueError(f"Tract order changed at {realization_id}")
            if npz["policies"].size != 13:
                raise ValueError(f"Expected 13 frozen policies in trajectory archive at {realization_id}")
            policies = list(map(str, npz["policies"].tolist()))
            if POLICY_IMPACT not in policies or POLICY_GA not in policies:
                raise ValueError(f"Missing paired strategy trajectories at {realization_id}")
            lengths = np.asarray(npz["event_lengths"], dtype=int)
            offsets = np.r_[0, np.cumsum(lengths[:-1])]
            if int(lengths.sum()) != len(npz["event_time_hr"]):
                raise ValueError(f"Event-segment offset identity failed at {realization_id}")

            summary_rows = _load_case_csv(payloads["SUMMARY.csv"])
            summary_by_policy = {row["strategy"]: row for row in summary_rows}
            task_rows = _load_case_csv(payloads["TASK_EXECUTION.csv"])
            tasks_by_policy = defaultdict(list)
            for row in task_rows:
                tasks_by_policy[row["strategy"]].append(row)
            if len(summary_by_policy) != 13 or len(tasks_by_policy) != 13:
                raise ValueError(f"Policy row counts are incomplete at {realization_id}")
            if any(row.get("physical_sha256") != physical_hash for row in summary_rows):
                raise ValueError(f"Policies do not share one physical identity at {realization_id}")

            per_policy_integrals = {}
            per_policy_traces = {}
            for policy, expected_sequence in ((POLICY_IMPACT, impact_sequence), (POLICY_GA, ga_sequence)):
                rows = tasks_by_policy[policy]
                damaged_ids = {station_ids[j] for j in range(92) if physical_ds[j] > 0}
                if len(rows) != len(damaged_ids) or {str(row["task_id"]) for row in rows} != damaged_ids:
                    raise ValueError(f"{policy} task set does not equal the non-DS0 physical stations at {realization_id}")
                rank_order = sorted(rows, key=lambda row: int(row["dispatch_rank"]))
                expected_damaged_sequence = [sid for sid in expected_sequence if sid in damaged_ids]
                if [str(row["task_id"]) for row in rank_order] != expected_damaged_sequence:
                    raise ValueError(f"{policy} task order differs from its hashed sequence at {realization_id}")
                if len({int(row["dispatch_rank"]) for row in rows}) != len(damaged_ids):
                    raise ValueError(f"Duplicate dispatch rank in {policy} at {realization_id}")
                trace = _policy_trace(npz, policies.index(policy), lengths, offsets)
                if trace["f"].shape != (lengths[policies.index(policy)], 92):
                    raise ValueError(f"Functionality state shape mismatch at {realization_id}/{policy}")
                if np.any(trace["F"] != (trace["f"] >= 0.5)):
                    raise ValueError(f"Saved threshold gate differs from f>=0.5 at {realization_id}/{policy}")
                if np.any(np.abs(trace["e"] - trace["f"] * trace["F"] * trace["C"]) > 1e-12):
                    raise ValueError(f"Saved effective service is not f*F*C at {realization_id}/{policy}")
                for state_i, frow in enumerate(trace["f"]):
                    calculated_C = source_connected(frow, adjacency, source_indices)
                    gate_error = int(np.sum(calculated_C != trace["C"][state_i]))
                    max_gate_error = max(max_gate_error, float(gate_error))
                    if gate_error:
                        raise ValueError(f"Saved source connectivity differs from graph reconstruction at {realization_id}/{policy}/{state_i}")
                metrics, station_integrals, additivity_error = _integrate_components(trace, station_mass, total_population)
                summary = summary_by_policy[policy]
                for component, column in COMPONENT_COLUMNS.items():
                    saved = float(summary[column])
                    error = abs(metrics[component] - saved)
                    max_saved_integral_error = max(max_saved_integral_error, error)
                    if error > 1e-8:
                        raise ValueError(f"Reintegrated {component} differs from saved summary at {realization_id}/{policy}")
                saved_station_components = trace["component_integrals"]
                if saved_station_components.shape != (4, 92):
                    raise ValueError(f"Station component integral shape mismatch at {realization_id}/{policy}")
                for c, name in enumerate(("self", "threshold", "source", "total")):
                    error = float(np.max(np.abs(saved_station_components[c] - station_integrals[name])))
                    max_saved_integral_error = max(max_saved_integral_error, error)
                    if error > 1e-8:
                        raise ValueError(f"Per-station {name} integral differs from event reconstruction at {realization_id}/{policy}")
                per_policy_integrals[policy] = metrics
                per_policy_traces[policy] = trace
                for component in COMPONENT_COLUMNS:
                    absolute_policy_components[policy][component][realization_index] = metrics[component]

                physical_duration = np.asarray(physical["duration_hr"], dtype=float)
                phys_index = {sid: i for i, sid in enumerate(station_ids)}
                for row in rows:
                    j = phys_index[str(row["task_id"])]
                    if int(row["damage_state"]) != int(physical_ds[j]):
                        raise ValueError(f"Task damage state differs from matched physical draw at {realization_id}/{policy}")
                    task_duration = float(row["realized_duration_hr"])
                    task_error = abs(task_duration - physical_duration[j])
                    max_task_array_error = max(max_task_array_error, task_error)
                    if task_error > 1e-9:
                        raise ValueError(f"Scheduled task duration differs from matched physical draw at {realization_id}/{policy}")

                result = _array_event_contribution(
                    trace, rows, station_ids, station_mass, total_population, policy,
                    realization_index, realization_id, station_records, external_records,
                    downstream_records,
                )
                max_downstream_identity_error = max(
                    max_downstream_identity_error,
                    result["max_downstream_identity_error_hr"],
                )
                if policy == POLICY_IMPACT:
                    per_policy_unlock_events[policy][realization_index] = result["event_unlock_count"]
                    per_policy_unlock_transitions[policy][realization_index] = result["external_station_unlock_transitions"]
                    per_policy_unlock_mass[policy][realization_index] = result["external_dependency_mass_person_equiv"]
                    per_policy_unlock_effective_mass[policy][realization_index] = result["external_effective_service_mass_person_equiv"]
                else:
                    per_policy_unlock_events[policy][realization_index] = result["event_unlock_count"]
                    per_policy_unlock_transitions[policy][realization_index] = result["external_station_unlock_transitions"]
                    per_policy_unlock_mass[policy][realization_index] = result["external_dependency_mass_person_equiv"]
                    per_policy_unlock_effective_mass[policy][realization_index] = result["external_effective_service_mass_person_equiv"]
                if policy == POLICY_IMPACT:
                    direct_delta[realization_index] = result["direct_source_loss_event_delta_hr"]
                    external_delta[realization_index] = result["external_source_loss_event_delta_hr"]

                grid_index = np.searchsorted(trace["times"], source_curve_grid, side="right") - 1
                grid_index = np.clip(grid_index, 0, len(trace["times"]) - 1)
                source_curve[policy][realization_index] = (
                    (trace["f"][grid_index] * trace["F"][grid_index] * (~trace["C"][grid_index]))
                    @ station_mass / total_population
                )
            for name in COMPONENT_COLUMNS:
                deltas[name][realization_index] = (
                    float(summary_by_policy[POLICY_GA][COMPONENT_COLUMNS[name]])
                    - float(summary_by_policy[POLICY_IMPACT][COMPONENT_COLUMNS[name]])
                )
            per_policy_source[POLICY_IMPACT][realization_index] = per_policy_integrals[POLICY_IMPACT]["source"]
            per_policy_source[POLICY_GA][realization_index] = per_policy_integrals[POLICY_GA]["source"]
            integrated_source_delta[realization_index] = per_policy_source[POLICY_GA][realization_index] - per_policy_source[POLICY_IMPACT][realization_index]

            # Recompute the paired event-loss decomposition for both strategies.
            # direct_delta/external_delta are overwritten below with paired effects.
            pair_category = {}
            for policy in (POLICY_IMPACT, POLICY_GA):
                # Per-policy event contributions were collected in station_records and external_records.
                pair_category[policy] = 0.0
            # Rebuild event totals directly from per-event transitions to avoid
            # deriving a paired effect from rounded aggregate outputs.
            event_totals = {POLICY_IMPACT: [0.0, 0.0], POLICY_GA: [0.0, 0.0]}
            for policy, sequence in ((POLICY_IMPACT, impact_sequence), (POLICY_GA, ga_sequence)):
                trace = per_policy_traces[policy]
                rows = tasks_by_policy[policy]
                by_time: dict[float, list[int]] = defaultdict(list)
                id_index = {sid: j for j, sid in enumerate(station_ids)}
                for row in rows:
                    by_time[float(row["completion_hr"])].append(id_index[str(row["task_id"])])
                for t, event_stations in by_time.items():
                    if t <= 0 or t >= HORIZON_HR:
                        continue
                    jmatches = np.flatnonzero(np.isclose(trace["times"], t, rtol=0, atol=1e-8))
                    if jmatches.size != 1:
                        raise ValueError(f"Event-time mismatch at {realization_id}/{policy}")
                    j = int(jmatches[0])
                    part = event_loss_components(trace["f"][j-1], trace["F"][j-1], trace["C"][j-1],
                                                 trace["f"][j], trace["F"][j], trace["C"][j],
                                                 event_stations, station_mass, total_population, t)
                    event_totals[policy][0] += part["direct_source_loss_delta_hr"]
                    event_totals[policy][1] += part["external_source_loss_delta_hr"]
            direct_pair = event_totals[POLICY_GA][0] - event_totals[POLICY_IMPACT][0]
            external_pair = event_totals[POLICY_GA][1] - event_totals[POLICY_IMPACT][1]
            direct_delta[realization_index] = direct_pair
            external_delta[realization_index] = external_pair
            pair_error = abs(direct_pair + external_pair - integrated_source_delta[realization_index])
            max_pair_event_identity_error = max(max_pair_event_identity_error, pair_error)
            if pair_error > 1e-8:
                raise ValueError(f"Direct/external event accounting does not sum to paired source loss at {realization_id}")

            for sid in station_ids:
                record = station_records[sid]
                crew_ga = record["crew"][POLICY_GA][realization_index]
                crew_impact = record["crew"][POLICY_IMPACT][realization_index]
                record["crew_changed"][realization_index] = (
                    crew_ga is not None and crew_impact is not None and crew_ga != crew_impact
                )

    if len(physical_hashes) != N_REALIZATIONS or case_file_checks != N_REALIZATIONS * 4:
        raise ValueError("Not all 2,000 paired physical cases and four payloads per case passed")
    component_matrix = np.column_stack([deltas[k] for k in ("self", "threshold", "source", "total")]
                                       + [direct_delta, external_delta])
    boot_ci = _paired_bootstrap_ci(component_matrix)
    effect_names = ["self", "threshold", "source", "total",
                    "direct_source_loss_event_delta_hr", "external_source_loss_event_delta_hr"]
    effects = {}
    for j, name in enumerate(effect_names):
        item = _mean_effect(component_matrix[:, j])
        item["bootstrap_95ci"] = [float(boot_ci[0, j]), float(boot_ci[1, j])]
        effects[name] = item

    unlock_names = ("unlock_events", "external_station_unlock_transitions",
                    "dependency_mass_person_equiv", "effective_service_mass_person_equiv")
    unlock_matrix = np.column_stack([
        per_policy_unlock_events[POLICY_GA] - per_policy_unlock_events[POLICY_IMPACT],
        per_policy_unlock_transitions[POLICY_GA] - per_policy_unlock_transitions[POLICY_IMPACT],
        per_policy_unlock_mass[POLICY_GA] - per_policy_unlock_mass[POLICY_IMPACT],
        per_policy_unlock_effective_mass[POLICY_GA] - per_policy_unlock_effective_mass[POLICY_IMPACT],
    ])
    unlock_boot_ci = _paired_bootstrap_ci(unlock_matrix)
    unlock_differences = {}
    for j, name in enumerate(unlock_names):
        item = _mean_effect(unlock_matrix[:, j])
        item["bootstrap_95ci"] = [float(unlock_boot_ci[0, j]), float(unlock_boot_ci[1, j])]
        unlock_differences[name] = item

    station_rows = []
    for sid in station_ids:
        rec = station_records[sid]
        rank_delta = np.asarray(rec["rank"][POLICY_GA]) - np.asarray(rec["rank"][POLICY_IMPACT])
        completion_delta = np.asarray(rec["completion"][POLICY_GA]) - np.asarray(rec["completion"][POLICY_IMPACT])
        travel_delta = np.asarray(rec["travel"][POLICY_GA]) - np.asarray(rec["travel"][POLICY_IMPACT])
        arrival_delta = np.asarray(rec["arrival"][POLICY_GA]) - np.asarray(rec["arrival"][POLICY_IMPACT])
        duration_delta = np.asarray(rec["duration"][POLICY_GA]) - np.asarray(rec["duration"][POLICY_IMPACT])
        direct_station_delta = np.asarray(rec["direct"][POLICY_GA]) - np.asarray(rec["direct"][POLICY_IMPACT])
        paired_task = np.isfinite(rank_delta)
        if not np.any(paired_task):
            continue
        station_rows.append({
            "station_id": sid,
            "metadata": station_metadata.get(sid, {}),
            "realizations_with_paired_repair": int(np.sum(paired_task)),
            "mean_rank_ga": float(np.nanmean(rec["rank"][POLICY_GA])),
            "mean_rank_impact": float(np.nanmean(rec["rank"][POLICY_IMPACT])),
            "mean_rank_change_ga_minus_impact": float(np.nanmean(rank_delta)),
            "fraction_ga_rank_earlier": float(np.mean(rank_delta[paired_task] < 0)),
            "mean_completion_ga_hr": float(np.nanmean(rec["completion"][POLICY_GA])),
            "mean_completion_impact_hr": float(np.nanmean(rec["completion"][POLICY_IMPACT])),
            "mean_completion_change_hr": float(np.nanmean(completion_delta)),
            "completion_change_p05_hr": float(np.nanquantile(completion_delta, 0.05)),
            "completion_change_p95_hr": float(np.nanquantile(completion_delta, 0.95)),
            "fraction_ga_completes_earlier": float(np.mean(completion_delta[paired_task] < -1e-10)),
            "fraction_ga_completes_later": float(np.mean(completion_delta[paired_task] > 1e-10)),
            "fraction_crew_assignment_changed": float(np.mean(rec["crew_changed"][paired_task])),
            "mean_travel_change_hr": float(np.nanmean(travel_delta)),
            "mean_arrival_change_hr": float(np.nanmean(arrival_delta)),
            "mean_realized_duration_change_hr": float(np.nanmean(duration_delta)),
            "direct_station_source_loss_contribution_delta_hr": float(direct_station_delta.mean()),
        })

    paired_station_repairs = sum(row["realizations_with_paired_repair"] for row in station_rows)
    schedule_summary = {
        "paired_station_repair_observations": int(paired_station_repairs),
        "mean_rank_change_ga_minus_impact": float(sum(
            row["mean_rank_change_ga_minus_impact"] * row["realizations_with_paired_repair"]
            for row in station_rows
        ) / paired_station_repairs),
        "mean_completion_change_hr_ga_minus_impact": float(sum(
            row["mean_completion_change_hr"] * row["realizations_with_paired_repair"]
            for row in station_rows
        ) / paired_station_repairs),
        "mean_travel_change_hr_per_paired_repair": float(sum(
            row["mean_travel_change_hr"] * row["realizations_with_paired_repair"]
            for row in station_rows
        ) / paired_station_repairs),
        "mean_arrival_change_hr_per_paired_repair": float(sum(
            row["mean_arrival_change_hr"] * row["realizations_with_paired_repair"]
            for row in station_rows
        ) / paired_station_repairs),
        "paired_repair_fraction_ga_earlier": float(sum(
            row["fraction_ga_completes_earlier"] * row["realizations_with_paired_repair"]
            for row in station_rows
        ) / paired_station_repairs),
        "paired_repair_fraction_ga_later": float(sum(
            row["fraction_ga_completes_later"] * row["realizations_with_paired_repair"]
            for row in station_rows
        ) / paired_station_repairs),
        "paired_repair_fraction_crew_changed": float(sum(
            row["fraction_crew_assignment_changed"] * row["realizations_with_paired_repair"]
            for row in station_rows
        ) / paired_station_repairs),
        "realized_duration_change_hr": 0.0,
        "realized_duration_is_matched_physical_draw": True,
    }

    trigger_rows = []
    for trigger, rec in external_records.items():
        ga_mean = rec[POLICY_GA] / n
        impact_mean = rec[POLICY_IMPACT] / n
        trigger_ids = trigger[6:].split(";") if trigger.startswith("MULTI:") else [trigger]
        metadata = [station_metadata.get(sid, {}) for sid in trigger_ids]
        downstream_rows = []
        for downstream_id, downstream in rec["downstream_stations"].items():
            ga_count = downstream["unlock_transition_count"][POLICY_GA]
            impact_count = downstream["unlock_transition_count"][POLICY_IMPACT]
            downstream_rows.append({
                "station_id": downstream_id,
                "metadata": station_metadata.get(downstream_id, {}),
                "source_loss_contribution_ga_hr": downstream["source_loss_contribution_hr"][POLICY_GA] / n,
                "source_loss_contribution_impact_hr": downstream["source_loss_contribution_hr"][POLICY_IMPACT] / n,
                "source_loss_delta_ga_minus_impact_hr": (
                    downstream["source_loss_contribution_hr"][POLICY_GA]
                    - downstream["source_loss_contribution_hr"][POLICY_IMPACT]
                ) / n,
                "unlock_transition_count_ga": ga_count,
                "unlock_transition_count_impact": impact_count,
                "dependency_mass_person_equiv_per_realization_ga": (
                    downstream["dependency_mass_person_equiv"][POLICY_GA] / n
                ),
                "dependency_mass_person_equiv_per_realization_impact": (
                    downstream["dependency_mass_person_equiv"][POLICY_IMPACT] / n
                ),
                "mean_unlock_completion_hr_ga": (
                    downstream["completion_time_sum_hr"][POLICY_GA] / ga_count if ga_count else None
                ),
                "mean_unlock_completion_hr_impact": (
                    downstream["completion_time_sum_hr"][POLICY_IMPACT] / impact_count
                    if impact_count else None
                ),
            })
        downstream_rows.sort(key=lambda item: item["source_loss_delta_ga_minus_impact_hr"])
        trigger_rows.append({"trigger_event": trigger,
                             "trigger_station_ids": trigger_ids,
                             "trigger_station_metadata": metadata,
                             "external_source_loss_delta_ga_hr": float(ga_mean),
                             "external_source_loss_delta_impact_hr": float(impact_mean),
                             "external_source_loss_delta_hr": float(ga_mean-impact_mean),
                             "unlock_event_count_ga": rec["unlock_events"][POLICY_GA],
                             "unlock_event_count_impact": rec["unlock_events"][POLICY_IMPACT],
                             "unlock_transition_count_ga": rec["unlock_transitions"][POLICY_GA],
                             "unlock_transition_count_impact": rec["unlock_transitions"][POLICY_IMPACT],
                             "mean_dependency_mass_person_equiv_per_realization_ga": rec["dependency_mass_person_equiv"][POLICY_GA]/n,
                             "mean_dependency_mass_person_equiv_per_realization_impact": rec["dependency_mass_person_equiv"][POLICY_IMPACT]/n,
                             "mean_effective_mass_person_equiv_per_realization_ga": rec["effective_mass_person_equiv"][POLICY_GA]/n,
                             "mean_effective_mass_person_equiv_per_realization_impact": rec["effective_mass_person_equiv"][POLICY_IMPACT]/n,
                             "mean_completion_hr_ga": (rec["completion_sum_hr"][POLICY_GA]/rec["event_count"][POLICY_GA]
                                                        if rec["event_count"][POLICY_GA] else None),
                             "mean_completion_hr_impact": (rec["completion_sum_hr"][POLICY_IMPACT]/rec["event_count"][POLICY_IMPACT]
                                                            if rec["event_count"][POLICY_IMPACT] else None),
                             "downstream_station_effects": downstream_rows})
    trigger_rows.sort(key=lambda row: row["external_source_loss_delta_hr"])
    station_rows_by_id = {row["station_id"]: row for row in station_rows}
    for row in trigger_rows:
        if row["trigger_event"].startswith("MULTI:"):
            row["mean_rank_ga"] = None
            row["mean_rank_impact"] = None
        else:
            srow = station_rows_by_id[row["trigger_event"]]
            row["mean_rank_ga"] = srow["mean_rank_ga"]
            row["mean_rank_impact"] = srow["mean_rank_impact"]

    downstream_rows = []
    for downstream_id, downstream in downstream_records.items():
        ga_count = downstream["unlock_transition_count"][POLICY_GA]
        impact_count = downstream["unlock_transition_count"][POLICY_IMPACT]
        downstream_rows.append({
            "station_id": downstream_id,
            "metadata": station_metadata.get(downstream_id, {}),
            "source_loss_contribution_ga_hr": downstream["source_loss_contribution_hr"][POLICY_GA] / n,
            "source_loss_contribution_impact_hr": downstream["source_loss_contribution_hr"][POLICY_IMPACT] / n,
            "source_loss_delta_ga_minus_impact_hr": (
                downstream["source_loss_contribution_hr"][POLICY_GA]
                - downstream["source_loss_contribution_hr"][POLICY_IMPACT]
            ) / n,
            "unlock_transition_count_ga": ga_count,
            "unlock_transition_count_impact": impact_count,
            "dependency_mass_person_equiv_per_realization_ga": (
                downstream["dependency_mass_person_equiv"][POLICY_GA] / n
            ),
            "dependency_mass_person_equiv_per_realization_impact": (
                downstream["dependency_mass_person_equiv"][POLICY_IMPACT] / n
            ),
            "mean_unlock_completion_hr_ga": (
                downstream["completion_time_sum_hr"][POLICY_GA] / ga_count if ga_count else None
            ),
            "mean_unlock_completion_hr_impact": (
                downstream["completion_time_sum_hr"][POLICY_IMPACT] / impact_count
                if impact_count else None
            ),
        })
    downstream_rows.sort(key=lambda item: item["source_loss_delta_ga_minus_impact_hr"])

    source_curve_diff = source_curve[POLICY_GA] - source_curve[POLICY_IMPACT]
    time_summary = {
        "time_hr": source_curve_grid.tolist(),
        "mean_ga_minus_impact_source_loss": source_curve_diff.mean(axis=0).tolist(),
        "p05": np.quantile(source_curve_diff, 0.05, axis=0).tolist(),
        "p95": np.quantile(source_curve_diff, 0.95, axis=0).tolist(),
        "range_definition": "5th-95th percentile across paired physical realizations; not a confidence interval",
    }
    total_direct = effects["direct_source_loss_event_delta_hr"]["mean"]
    total_external = effects["external_source_loss_event_delta_hr"]["mean"]
    total_source = effects["source"]["mean"]
    additivity_error = abs(total_direct + total_external - total_source)
    if additivity_error > 1e-8:
        raise ValueError("Mean event-level direct/external attribution fails to sum to source effect")
    trigger_sum_error = abs(sum(row["external_source_loss_delta_hr"] for row in trigger_rows) - total_external)
    downstream_sum_error = abs(
        sum(row["source_loss_delta_ga_minus_impact_hr"] for row in downstream_rows) - total_external
    )
    trigger_downstream_error = max((abs(
        sum(item["source_loss_delta_ga_minus_impact_hr"] for item in row["downstream_station_effects"])
        - row["external_source_loss_delta_hr"]
    ) for row in trigger_rows), default=0.0)
    station_direct_sum_error = abs(sum(
        row["direct_station_source_loss_contribution_delta_hr"] for row in station_rows
    ) - total_direct)
    if max(trigger_sum_error, station_direct_sum_error, downstream_sum_error,
           trigger_downstream_error, max_downstream_identity_error) > 1e-8:
        raise ValueError("Per-trigger or per-station attribution does not sum to its event component")
    trigger_sum_error = abs(sum(row["external_source_loss_delta_hr"] for row in trigger_rows) - total_external)
    station_direct_sum_error = abs(sum(
        row["direct_station_source_loss_contribution_delta_hr"] for row in station_rows
    ) - total_direct)
    if max(trigger_sum_error, station_direct_sum_error, downstream_sum_error,
           trigger_downstream_error, max_downstream_identity_error) > 1e-8:
        raise ValueError("Per-trigger or per-station attribution does not sum to its event component")

    # Percent of paired total-service outcomes with a lower burden under GA.
    result = {
        "status": "PASS",
        "estimand": "ga-final-method-candidate minus impact-first; paired population-weighted normalized service-deficit integrals over 0-480 h",
        "cohort": {
            "realizations": n,
            "unique_physical_hashes": len(physical_hashes),
            "paired_policy_rows": 2*n,
            "all_policy_records_in_source_capsule": 26000,
            "station_count": 92,
            "tract_count": mapping_qa["tract_count"],
            "population": mapping_qa["population"],
            "horizon_hr": HORIZON_HR,
        },
        "identity": {
            "archive_sha256": ARCHIVE_SHA256,
            "archive_size_bytes": ARCHIVE_SIZE,
            "freeze_sha256": FREEZE_SHA256,
            "ga_sequence_sha256": GA_SEQUENCE_SHA256,
            "impact_sequence_sha256": IMPACT_SEQUENCE_SHA256,
            "mapping_sha256": MAPPING_SHA256,
            "graph_sha256": GRAPH_SHA256,
            "source_table_sha256": SOURCE_SHA256,
            "selected_sequence_json_sha256": sha256_file(selected_path),
            "comparator_manifest_sha256": sha256_file(comparator_path),
            "full_archive_manifest_sha256": sha256_file(validation_dir / "FULL_ARCHIVE_MANIFEST.json"),
            "validation_receipt_sha256": sha256_file(validation_dir / "fixed_2000_20261010" / "REPRODUCIBILITY_RECEIPT.json"),
            "post_completion_qa_sha256": sha256_file(validation_dir / "POST_COMPLETION_QA.json"),
            "validation_qa_status": qa["status"],
            "validation_execution_commit": "c178bff7f924257b33f1e8c17e0d5e59a1fe68e9",
            "physical_sample_seed_protocol": "numpy.default_rng(SeedSequence([202610091,3,2,r])) for r=0..1999",
            "physical_sample_seed_identity_checks": protocol_seed_identity_checks,
            "selected_sequence_json_path": str(selected_path),
            "ga_selection_source_commit": selected_metadata.get("source_commit"),
            "ga_selection_source_file": selected_metadata.get("source_file"),
            "ga_selection_source_file_sha256": selected_metadata.get("source_file_sha256"),
            "ga_sequence_selection_uses_evaluation": selected_metadata.get("selection_uses_evaluation"),
            "ga_candidate_planning_loss_hr": selected_metadata.get("planning_loss_hr"),
            "ga_sequence_station_ids_in_order": ga_sequence,
            "impact_sequence_station_ids_in_order": impact_sequence,
            "validation_archive_pointer_path": str(validation_dir / "FIXED_2000_FULL_ARCHIVE.zip"),
            "archive_materialized_path": str(archive),
            "mapping_path": str(mapping_path),
            "graph_path": str(graph_path),
            "core_source_table_path": str(source_path),
        },
        "mapping_qa": mapping_qa,
        "numerical_qa": {
            "case_payload_sha_checks": case_file_checks,
            "max_saved_vs_reintegrated_summary_error_hr": max_saved_integral_error,
            "max_gate_state_mismatch_count": max_gate_error,
            "max_task_vs_physical_duration_error_hr": max_task_array_error,
            "max_paired_event_attribution_identity_error_hr": max_pair_event_identity_error,
            "max_unlocked_downstream_vs_external_event_error_hr": max_downstream_identity_error,
            "mean_direct_plus_external_minus_source_error_hr": additivity_error,
            "trigger_rows_minus_external_component_error_hr": trigger_sum_error,
            "downstream_station_rows_minus_external_component_error_hr": downstream_sum_error,
            "trigger_downstream_rows_identity_error_hr": trigger_downstream_error,
            "station_rows_minus_direct_component_error_hr": station_direct_sum_error,
            "trigger_rows_minus_external_component_error_hr": trigger_sum_error,
            "station_rows_minus_direct_component_error_hr": station_direct_sum_error,
            "event_accounting_share_of_source_effect_pct": 100.0,
            "events_are_exact_integral_accounting_not_causal_effects": True,
        },
        "paired_effects": effects,
        "absolute_policy_mean_components": {
            policy: {component: float(values.mean()) for component, values in by_component.items()}
            for policy, by_component in absolute_policy_components.items()
        },
        "policy_unlock_summary": {
            policy: {
                "realizations_with_any_external_source_unlock": int(np.sum(per_policy_unlock_events[policy] > 0)),
                "mean_unlock_events_per_realization": float(per_policy_unlock_events[policy].mean()),
                "mean_external_station_unlock_transitions_per_realization": float(per_policy_unlock_transitions[policy].mean()),
                "mean_dependency_mass_person_equiv_per_realization": float(per_policy_unlock_mass[policy].mean()),
                "mean_effective_service_mass_person_equiv_per_realization": float(per_policy_unlock_effective_mass[policy].mean()),
            } for policy in (POLICY_IMPACT, POLICY_GA)
        },
        "paired_unlock_differences_ga_minus_impact": unlock_differences,
        "schedule_change_summary": schedule_summary,
        "top_external_unlock_trigger_events": trigger_rows[:20],
        "largest_positive_external_trigger_offsets": list(reversed(trigger_rows[-10:])),
        "downstream_station_attribution": downstream_rows,
        "largest_downstream_station_source_loss_gains": downstream_rows[:12],
        "largest_downstream_station_source_loss_offsets": list(reversed(downstream_rows[-8:])),
        "largest_direct_station_source_loss_gains": sorted(
            station_rows,
            key=lambda row: row["direct_station_source_loss_contribution_delta_hr"],
        )[:8],
        "largest_direct_station_source_loss_offsets": sorted(
            station_rows,
            key=lambda row: row["direct_station_source_loss_contribution_delta_hr"],
            reverse=True,
        )[:6],
        "station_schedule_changes": station_rows,
        "source_loss_curve": time_summary,
        "counterexamples": {
            "ga_lower_total_burden_realizations": int(np.sum(deltas["total"] < -1e-12)),
            "impact_lower_total_burden_realizations": int(np.sum(deltas["total"] > 1e-12)),
            "total_ties": int(np.sum(np.abs(deltas["total"]) <= 1e-12)),
            "ga_lower_source_loss_realizations": int(np.sum(deltas["source"] < -1e-12)),
            "impact_lower_source_loss_realizations": int(np.sum(deltas["source"] > 1e-12)),
            "ga_higher_self_loss_realizations": int(np.sum(deltas["self"] > 1e-12)),
            "source_improved_but_total_worsened": int(np.sum((deltas["source"] < -1e-12) & (deltas["total"] > 1e-12))),
            "source_worsened_but_total_improved": int(np.sum((deltas["source"] > 1e-12) & (deltas["total"] < -1e-12))),
        },
        "interpretation_limits": [
            "Population dependency mass is a mapped person-equivalent weight, not observed customers or delivered electricity.",
            "Source connectivity is the frozen binary Core-source proxy gate, not electrical power-flow validation.",
            "Event decomposition is exact accounting of saved step trajectories; it does not isolate causal effects of individual tasks under alternative sequences.",
            "The quoted -0.533 h / (-0.821, +0.277, +0.011 h) tuple is not reproduced by this exact frozen 2,000-case GA-final-method-candidate comparison; its source sequence/cohort remains unverified.",
        ],
    }
    sample_qa_path = output / "GA_VALIDATION_SAMPLE_IDENTITY_QA.json"
    if not sample_qa_path.is_file():
        raise ValueError("Independent registered sample-identity QA must pass before reporting")
    sample_qa = _read_json(sample_qa_path)
    if (sample_qa.get("status") != "PASS"
            or sample_qa.get("archived_sample_seed_records_verified") != N_REALIZATIONS
            or sample_qa.get("overlap_with_original_physical_hashes") != 0):
        raise ValueError("Independent sample-identity QA is not a complete PASS")
    result["independent_sample_identity_qa"] = {
        "status": sample_qa["status"],
        "path": sample_qa_path.name,
        "sha256": sha256_file(sample_qa_path),
        "seed_records_verified": sample_qa["archived_sample_seed_records_verified"],
        "unique_validation_physical_hashes": sample_qa["unique_validation_physical_hashes"],
        "original_physical_hashes_checked": sample_qa["original_planning_and_evaluation_hashes"],
        "overlap": sample_qa["overlap_with_original_physical_hashes"],
        "bitwise_regenerated_indices": [row["r"] for row in sample_qa["independently_regenerated_indices"]],
    }
    paired_rows = []
    for realization_index in range(n):
        row = {
            "realization_id": f"2pc50__independent_{realization_index:04d}",
            "physical_sha256": str(physical_hash_by_realization[realization_index]),
            "paired_delta_ga_minus_impact_hr": {
                key: float(deltas[key][realization_index]) for key in ("self", "threshold", "source", "total")
            },
            "event_source_delta_ga_minus_impact_hr": {
                "own_repaired_station_states": float(direct_delta[realization_index]),
                "other_station_source_connection_states": float(external_delta[realization_index]),
            },
            "external_unlock_delta_ga_minus_impact": {
                "completion_events": float(per_policy_unlock_events[POLICY_GA][realization_index]
                                            - per_policy_unlock_events[POLICY_IMPACT][realization_index]),
                "other_station_transitions": float(per_policy_unlock_transitions[POLICY_GA][realization_index]
                                                    - per_policy_unlock_transitions[POLICY_IMPACT][realization_index]),
                "mapped_dependency_mass_person_equiv": float(per_policy_unlock_mass[POLICY_GA][realization_index]
                                                              - per_policy_unlock_mass[POLICY_IMPACT][realization_index]),
            },
        }
        paired_rows.append(row)
    paired_payload = {
        "definition": "Paired per-realization outcomes for the fixed GA final-method candidate minus Impact-first on the same frozen physical draw. Burden components are 0-480 h population-weighted normalized service-deficit hours. Event rows are exact accounting, not causal task effects.",
        "realization_count": n,
        "ga_sequence_sha256": sequence_hash(ga_sequence),
        "impact_sequence_sha256": sequence_hash(impact_sequence),
        "validation_archive_sha256": ARCHIVE_SHA256,
        "seed_protocol": "numpy.default_rng(SeedSequence([202610091,3,2,r]))",
        "realizations": paired_rows,
    }
    with open(_long_path(output / "GA_IMPACT_PAIRED_REALIZATION_EFFECTS.json"), "w", encoding="utf-8") as stream:
        stream.write(json.dumps(paired_payload, indent=2) + "\n")
    with open(_long_path(output / "GA_IMPACT_EVENT_MECHANISM.json"), "w", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")
    station_effects_path = output / "GA_IMPACT_STATION_EVENT_ATTRIBUTION.json"
    station_payload = {
        "definition": "Mean per-station contribution to GA-minus-Impact source-loss difference. Trigger-event rows preserve simultaneous repair batches; downstream rows identify the other stations newly connected at each completed event. Contributions are exact step-trajectory integral accounting, not causal task effects.",
        "stations": station_rows,
        "trigger_events": trigger_rows,
        "downstream_stations": downstream_rows,
    }
    with open(_long_path(station_effects_path), "w", encoding="utf-8") as stream:
        stream.write(json.dumps(station_payload, indent=2) + "\n")
    _write_figures(output, effects,
                   {"direct_source_loss_delta_hr": effects["direct_source_loss_event_delta_hr"],
                    "external_source_loss_delta_hr": effects["external_source_loss_event_delta_hr"]},
                   trigger_rows, time_summary)
    _write_report(output, result)
    _write_output_hash_manifest(output, result)
    return result


def _write_output_hash_manifest(output: Path, result: dict):
    manifest_path = output / "GA_IMPACT_OUTPUT_SHA256.json"
    output_hashes = {
        path.name: sha256_file(path)
        for path in sorted(output.iterdir(), key=lambda item: item.name)
        if path.is_file() and path != manifest_path
    }
    script = Path(__file__).resolve()
    repo_root = script.parents[3]
    test_path = repo_root / "tests/test_ga_impact_event_mechanism_20261106.py"
    verifier_path = script.with_name("verify_ga_validation_samples_20261106.py")
    payload = {
        "status": "PASS",
        "output_files_sha256": output_hashes,
        "analysis_script_sha256": sha256_file(script),
        "sample_identity_verifier_sha256": sha256_file(verifier_path),
        "unit_test_sha256": sha256_file(test_path) if test_path.is_file() else None,
        "registered_inputs": {
            key: result["identity"].get(key)
            for key in ("archive_sha256", "freeze_sha256", "ga_sequence_sha256",
                        "impact_sequence_sha256", "mapping_sha256", "graph_sha256",
                        "source_table_sha256", "selected_sequence_json_sha256",
                        "comparator_manifest_sha256", "full_archive_manifest_sha256",
                        "validation_receipt_sha256", "post_completion_qa_sha256")
        },
        "independent_sample_identity_qa": result["independent_sample_identity_qa"],
    }
    with open(_long_path(manifest_path), "w", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _write_report(output: Path, result: dict):
    effects = result["paired_effects"]
    cat = effects
    src = result["policy_unlock_summary"]
    unlock_diff = result["paired_unlock_differences_ga_minus_impact"]
    schedule = result["schedule_change_summary"]
    trigger = result["top_external_unlock_trigger_events"]
    curve = result["source_loss_curve"]
    curve_mean = np.asarray(curve["mean_ga_minus_impact_source_loss"], dtype=float)
    curve_min_idx = int(np.argmin(curve_mean))
    lines = [
        "# GA versus Impact-first: Paired Source-Connectivity Mechanism",
        "",
        "## Result",
        "",
        (f"On the exact saved, paired 2,000-realization 2pc50/C57_D1 cohort, the frozen GA final-method candidate changed total "
         f"modeled burden by {cat['total']['mean']:+.6f} h versus Impact-first "
         f"(paired bootstrap 95% CI {cat['total']['bootstrap_95ci'][0]:+.6f} to {cat['total']['bootstrap_95ci'][1]:+.6f} h)."),
        (f"The component changes were self {cat['self']['mean']:+.6f} h, threshold {cat['threshold']['mean']:+.6f} h, "
         f"and source path {cat['source']['mean']:+.6f} h. These add to the total within {result['numerical_qa']['mean_direct_plus_external_minus_source_error_hr']:.2e} h."),
        (f"The paired source-path difference decomposes exactly into {cat['direct_source_loss_event_delta_hr']['mean']:+.6f} h "
         f"from each repaired station's own source-loss state change and {cat['external_source_loss_event_delta_hr']['mean']:+.6f} h "
         f"from other already-functional stations whose source connection changed at completion events. Their sum is "
         f"{cat['source']['mean']:+.6f} h."),
        (f"On the saved 1-hour descriptive curve, the mean paired source-path deficit difference reaches "
         f"{curve_mean[curve_min_idx]:+.5f} at hour {curve['time_hr'][curve_min_idx]:g} and is effectively zero by 72 h; "
         "the 480-hour effect above is integrated exactly from the original event times, not from this hourly display."),
        "",
        "## Paired Effects",
        "",
        "Effect is GA minus Impact-first; negative values favor GA. All are population-weighted normalized service-deficit hours over 0-480 h.",
        "",
        "| Component | Mean (h) | Paired MCSE (h) | Paired bootstrap 95% interval (h) |",
        "|---|---:|---:|---:|",
    ]
    for name, label in (("self", "Self functionality"), ("threshold", "Functionality threshold"),
                        ("source", "Source path"), ("total", "Total")):
        value = cat[name]
        lines.append(f"| {label} | {value['mean']:+.6f} | {value['mcse']:.6f} | [{value['bootstrap_95ci'][0]:+.6f}, {value['bootstrap_95ci'][1]:+.6f}] |")
    absolute = result["absolute_policy_mean_components"]
    lines += ["", "| Strategy | Self (h) | Threshold (h) | Source path (h) | Total (h) |",
              "|---|---:|---:|---:|---:|"]
    for policy in (POLICY_IMPACT, POLICY_GA):
        values = absolute[policy]
        lines.append(f"| {policy} | {values['self']:.6f} | {values['threshold']:.6f} | {values['source']:.6f} | {values['total']:.6f} |")
    lines += ["", "At each completion event the source-path loss state is `f_s * F_s * (1 - C_s)`: `f` is modeled station functionality, `F` is the 0.5 functionality gate, and `C` is connection to a frozen Core-source proxy. The direct event term is the changed mapped source loss on stations repaired at that event; the external term is the changed source loss on all other stations. Each is integrated over remaining time to 480 h and normalized by total mapped population.",
              ""]
    direct_mean = cat["direct_source_loss_event_delta_hr"]["mean"]
    external_mean = cat["external_source_loss_event_delta_hr"]["mean"]
    offset_pct = 100.0 * external_mean / -direct_mean
    lines += ["", "## What Produces the Source-Path Improvement?", "",
              (f"The GA-minus-Impact source-path difference is **{direct_mean:+.6f} h** at the repaired stations' own mapped source-loss states, "
               f"but **{external_mean:+.6f} h** across other stations whose source connection changes at completion events. "
               f"The latter offsets {offset_pct:.1f}% of the own-station source-path benefit, leaving the net {cat['source']['mean']:+.6f} h gain. "
               "So the result is not produced by GA unlocking more external dependency overall."),
              (f"Instead, the fixed GA order moves selected stations earlier while delaying others. Across {schedule['paired_station_repair_observations']:,} "
               f"paired damaged-station repairs, its mean completion shift was {schedule['mean_completion_change_hr_ga_minus_impact']:+.4f} h per repair "
               f"({schedule['paired_repair_fraction_ga_earlier']:.1%} earlier; {schedule['paired_repair_fraction_ga_later']:.1%} later); "
               f"crew assignments differed in {schedule['paired_repair_fraction_crew_changed']:.1%} of paired station-repair cases. "
               f"The matched repair durations were identical; average task travel changed {schedule['mean_travel_change_hr_per_paired_repair']:+.4f} h per repair."),
              "",
              "| External-unlock quantity (GA minus Impact-first) | Mean per realization | Paired bootstrap 95% interval |",
              "|---|---:|---:|"]
    for key, label in (("unlock_events", "Completion events with >=1 other-station unlock"),
                       ("external_station_unlock_transitions", "Other-station connectivity transitions"),
                       ("dependency_mass_person_equiv", "M1 mapped person-equivalent dependency mass")):
        value = unlock_diff[key]
        lines.append(f"| {label} | {value['mean']:+.4f} | [{value['bootstrap_95ci'][0]:+.4f}, {value['bootstrap_95ci'][1]:+.4f}] |")
    lines += ["", "External-unlock mass is the sum of population-weighted M1 station dependencies newly connected at each completion, averaged across realizations. It is not a count of distinct residents; tract population is fractionally mapped across substations.",
              "",
              "Event-trigger contrasts below are GA minus Impact-first in the other-station source-loss integral; negative means that event's external loss contribution is lower under GA. Completion is the mean scheduled completion time for that station across cases where it required repair.",
              "",
              "| Completion trigger | Source-register label / role | External contribution (h) | Mean repair rank GA vs Impact | Mean completion GA vs Impact (h) |",
              "|---|---|---:|---:|---:|"]
    for row in trigger[:8]:
        meta = row["trigger_station_metadata"][0] if len(row["trigger_station_metadata"]) == 1 else {}
        label = meta.get("name") or "station label unavailable in source register"
        role = ", ".join(x for x in (meta.get("level"), meta.get("source_type")) if x) or "not in source-only register"
        rank_text = (f"{row['mean_rank_ga']:.1f} vs {row['mean_rank_impact']:.1f}"
                     if row["mean_rank_ga"] is not None else "simultaneous completion group")
        comp_delta = (row["mean_completion_hr_ga"] - row["mean_completion_hr_impact"]
                      if row["mean_completion_hr_ga"] is not None and row["mean_completion_hr_impact"] is not None
                      else float("nan"))
        lines.append(f"| {row['trigger_event']} | {label} ({role}) | {row['external_source_loss_delta_hr']:+.6f} | {rank_text} | {comp_delta:+.2f} |")
    lines += ["", "### Downstream stations newly connected at those completion events", "",
              "These rows identify the other station whose binary source-connection state changed at a completion. Contributions are integrated step-trajectory accounting, not causal task effects.",
              "", "| Trigger completion | Newly connected station | Source role | GA−Impact contribution (h) | Unlock transitions per 2,000 cases (GA / Impact) |", "|---|---|---|---:|---:|"]
    downstream_items = []
    for row in trigger[:8]:
        for item in row["downstream_station_effects"][:2]:
            downstream_items.append((row, item))
    for trigger_row, item in downstream_items:
        meta = item["metadata"]
        label = meta.get("name") or "label unavailable"
        role = ", ".join(x for x in (meta.get("level"), meta.get("source_type")) if x) or "not in source-only register"
        lines.append(
            f"| {trigger_row['trigger_event']} | {item['station_id']} ({label}) | {role} | "
            f"{item['source_loss_delta_ga_minus_impact_hr']:+.6f} | "
            f"{item['unlock_transition_count_ga']} / {item['unlock_transition_count_impact']} |"
        )
    lines += ["", "### Own-station source-loss changes on repaired stations", "",
              "Negative values mean lower own-station source-path deficit under GA. This table separates direct station restoration from downstream source reconnection.",
              "", "| Repaired station | Source role | GA−Impact own-station contribution (h) | Mean completion GA vs Impact (h) | GA completes earlier |", "|---|---|---:|---:|---:|"]
    for row in result["largest_direct_station_source_loss_gains"][:6]:
        meta = row["metadata"]
        label = meta.get("name") or row["station_id"]
        role = ", ".join(x for x in (meta.get("level"), meta.get("source_type")) if x) or "not in source-only register"
        lines.append(
            f"| {row['station_id']} ({label}) | {role} | "
            f"{row['direct_station_source_loss_contribution_delta_hr']:+.6f} | "
            f"{row['mean_completion_change_hr']:+.2f} | {row['fraction_ga_completes_earlier']:.1%} |"
        )
    offsets = result["largest_positive_external_trigger_offsets"][:5]
    lines += ["", "Largest offsetting event groups (positive means higher external source-path deficit under GA):", "",
              "| Completion trigger | External contribution (h) | GA unlock events / Impact unlock events |", "|---|---:|---:|"]
    for row in offsets:
        lines.append(f"| {row['trigger_event']} | {row['external_source_loss_delta_hr']:+.6f} | {row['unlock_event_count_ga']} / {row['unlock_event_count_impact']} |")
    lines += ["", "The full station-level rank, crew, travel, arrival, completion, realized-duration and own-station contribution comparison is in `GA_IMPACT_STATION_EVENT_ATTRIBUTION.json`. Negative rank/completion differences indicate GA earlier than Impact-first.",
              (f"The source-path component favored GA in {result['counterexamples']['ga_lower_source_loss_realizations']:,}/2,000 cases; "
               f"it was worse in {result['counterexamples']['impact_lower_source_loss_realizations']:,}. Total burden favored GA in "
               f"{result['counterexamples']['ga_lower_total_burden_realizations']:,}/2,000 and favored Impact-first in "
               f"{result['counterexamples']['impact_lower_total_burden_realizations']:,}."),
              "", "## Provenance and Reconciliation", "",
              f"- Physical cohort: {result['cohort']['realizations']} paired unique physical hashes; all 2,000 cases passed embedded payload hashes.",
              f"- Independent sample identity QA: PASS; {result['independent_sample_identity_qa']['seed_records_verified']:,} registered seed records, {result['independent_sample_identity_qa']['unique_validation_physical_hashes']:,} unique draws, zero overlap with {result['independent_sample_identity_qa']['original_physical_hashes_checked']:,} original hashes; bitwise sampler checks at r={', '.join(map(str, result['independent_sample_identity_qa']['bitwise_regenerated_indices']))}.",
              f"- GA sequence SHA-256: `{result['identity']['ga_sequence_sha256']}`; Impact-first sequence SHA-256: `{result['identity']['impact_sequence_sha256']}`.",
              f"- GA candidate provenance: seed 43, source commit `{result['identity']['ga_selection_source_commit']}`, candidate planning loss {result['identity']['ga_candidate_planning_loss_hr']:.6f} h, selection uses evaluation = `{result['identity']['ga_sequence_selection_uses_evaluation']}`; source `{result['identity']['ga_selection_source_file']}` (SHA-256 `{result['identity']['ga_selection_source_file_sha256']}`).",
              f"- LFS archive SHA-256: `{result['identity']['archive_sha256']}`; validation freeze: `{result['identity']['freeze_sha256']}`.",
              "- The Oct 9 sequence JSON is the exact `ga-final-method-candidate` sequence in the completed Oct 10 independent validation manifest. The execution accounting records one completed 2,000-sample run, not merely a protocol plan.",
              "- The latest PR comment's approximate (-0.533 h total; -0.821, +0.277, +0.011 h components) does not match the exact paired component table in this archive. The active checkout's current FigS04 is network recovery; its GA diagnostic is FigS05 and describes a different 1,000-realization exploratory comparison. No artifact-level proof was found tying the comment's tuple to the exact frozen 2,000-case GA sequence.",
              "",
              "## Interpretation Limits", "",
              "The event split is an exact decomposition of saved completion-step source-loss curves. It quantifies own-station versus other-station source-path changes at each completion, but it is not a causal intervention on an individual bridge station: event order, crew assignment and travel jointly determine the state at each repair. The modeled source gate is a binary Core-source proxy, not power flow or observed service.",
              "The independent 2,000-realization cohort is conditional Monte Carlo validation of the frozen model, not observed-outage validation. No new cohort, repair schedule, or GA optimization was generated here; four archived samples were independently regenerated solely to verify their registered identity.",
              "", "## Reproduction", "",
              "Run the script with the archived materialized LFS object and the original input files:", "",
              "```powershell",
              "python src/la_grid/diagnostics/ga_impact_event_mechanism_20261106.py `",
              "  --archive results/diagnostics/independent_validation_ready_20261010/authorized_validation/FIXED_2000_FULL_ARCHIVE.zip `",
              "  --validation-dir results/diagnostics/independent_validation_ready_20261010/authorized_validation `",
              "  --selected-sequence results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json `",
              "  --mapping Data/JULY_UTILITY_CONSTRAINED_92.csv `",
              "  --graph Data/substation_graph_CEC_edges_expanded.csv `",
              "  --sources Data/source_nodes_core_expanded.csv `",
              "  --output results/research_contribution1_20261105/GA_IMPACT_EVENT_FOLLOWUP_20261106",
              "```", ""]
    with open(_long_path(output / "GA_IMPACT_EVENT_MECHANISM_REPORT.md"), "w", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, help="Materialized LFS ZIP with SHA 74d837...")
    parser.add_argument("--validation-dir", required=True, help="authorized_validation directory with manifest and QA")
    parser.add_argument("--selected-sequence", required=True, help="Frozen SELECTED_SEQUENCE.json")
    parser.add_argument("--mapping", required=True, help="Frozen M1 long mapping CSV")
    parser.add_argument("--graph", required=True, help="Frozen 92-node station graph CSV")
    parser.add_argument("--sources", required=True, help="Frozen Core-source table CSV")
    parser.add_argument("--output", required=True, help="Output directory for compact derived evidence")
    args = parser.parse_args()
    result = analyze(args)
    print(json.dumps({"status": result["status"], "output": str(_path_arg(args.output)),
                      "effects": result["paired_effects"], "qa": result["numerical_qa"]}, indent=2))


if __name__ == "__main__":
    main()
