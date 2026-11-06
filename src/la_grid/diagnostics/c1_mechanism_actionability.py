"""Read-only Contribution 1 mechanism analysis on frozen July92 results.

No samples, restoration schedules, source histories, or optimization runs are
generated here. The registered prepass completion arrays are post-processed;
the exact saved production decoder is used only for the predeclared paired
local priority perturbations. Set NUMBA_DISABLE_JIT before import so the same
decoder body runs without writing cache files beside protected source code.
"""
from __future__ import annotations

import os
import tempfile
import faulthandler
faulthandler.enable()
_NUMBA_CACHE = os.path.join(tempfile.gettempdir(), "c1_mechanism_actionability_numba")
os.makedirs(_NUMBA_CACHE, exist_ok=True)
os.environ.setdefault("NUMBA_CACHE_DIR", _NUMBA_CACHE)

import argparse
import csv
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from la_grid.revision.formal.schedule import FormalScheduleDecoder, _decode
from la_grid.revision.r1_realization_scheduling import INITIAL_BY_DS, evaluate_completion_step_functionality
from la_grid.revision.r1_source_gate import evaluate_source_gate

OUT = ROOT / "results" / "research_contribution1_20261105"
FORMAL = ROOT / "Formal_Experiment_20260923"
PHYSICAL = FORMAL / "Stage 1 Output_expanded"
SCHEDULES = FORMAL / "Formal_Schedule_Prepass"
MAPPING_PATH = ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv"
GRAPH_PATH = ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv"
SOURCE_PATH = ROOT / "Data" / "source_nodes_core_expanded.csv"
CREW_PATH = ROOT / "Data" / "stage45_C57_expanded_crew_origins.csv"
BASE_TRAVEL = ROOT / "data" / "travel" / "travel_base_to_task.csv"
TASK_TRAVEL = ROOT / "data" / "travel" / "travel_task_to_task.csv"
PHYSICAL_NPZ = PHYSICAL / "physical_inputs_2pc50.npz"
PHYSICAL_MANIFEST = PHYSICAL / "PHYSICAL_SAMPLE_MANIFEST.csv"
PHYSICAL_IDENTITY = PHYSICAL / "PHYSICAL_INPUTS_FROZEN.json"
RULE_SEQUENCE_PATH = FORMAL / "Stage 4 Output_expanded" / "FULL_RULE_SEQUENCES.json"
VULN_SEQUENCE_PATH = FORMAL / "Equity_Amendment" / "VULNERABILITY_FIRST_SEQUENCE.json"
VULN_SUMMARY_PATH = FORMAL / "Equity_Amendment" / "VULNERABILITY_PRIMARY_SUMMARY.parquet"
OFFLINE_INDEX_PATH = FORMAL / "Formal_Offline_Evaluation" / "FORMAL_OFFLINE_INDEX.json"
QA03_PATH = ROOT / "results" / "figure_review_rq_aligned_20261101" / "QA" / "FIG03_COMPONENT_SHARE_QA.json"
QA04_PATH = ROOT / "results" / "figure_review_rq_aligned_20261101" / "QA" / "FIG04_MECHANISM_AND_OUTCOME_QA.json"

POLICIES = ("centrality-first", "impact-first", "betweenness-first",
            "degree-first", "closeness-first", "hospital-first", "random")
COMPARE = ("impact-first", "degree-first", "betweenness-first",
           "centrality-first", "closeness-first", "hospital-first", "random",
           "vulnerability-first", "unconstrained")
COMPONENTS = ("self", "threshold", "source", "total")
SUMMARY_COL = {
    "self": "L_self_population_mass_weighted_hr",
    "threshold": "L_threshold_population_mass_weighted_hr",
    "source": "L_source_population_mass_weighted_hr",
    "total": "L_total_population_mass_weighted_hr",
}
EXPECTED_UNCONSTRAINED = {
    "self": 26.887247240546063,
    "threshold": 0.8764917719738314,
    "source": 3.57403796927675,
    "total": 31.337776981796647,
}
EXPECTED_DEGREE_MINUS_HOSPITAL = {
    "self": 2.944701949630948,
    "threshold": 0.1032344048873476,
    "source": -1.6466924084593768,
    "total": 1.4012439460589194,
}
EXPECTED_REALIZATION_RANGE = {
    "self": (2.2777557911430906, 3.7443651111204557),
    "threshold": (0.0724655418708217, 0.14035448241312135),
    "source": (-3.1820139956140365, -0.3537241041946505),
    "total": (-0.17550362366852598, 2.7844498143397014),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _filesystem_path(path: Path) -> Path:
    """Use the Windows extended path syntax for frozen files near MAX_PATH."""
    absolute = os.path.abspath(os.fspath(path))
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        absolute = "\\\\?\\" + absolute
    return Path(absolute)


def sequence_hash(sequence) -> str:
    return hashlib.sha256(("\n".join(map(str, sequence)) + "\n").encode()).hexdigest()


def physical_hash(ids, ds, duration) -> str:
    ids_bytes = ("\n".join(map(str, ids)) + "\n").encode()
    ds_bytes = np.asarray(ds, dtype="<i8").tobytes()
    duration_bytes = np.asarray(duration, dtype="<f8").tobytes()
    return hashlib.sha256(ids_bytes + ds_bytes + duration_bytes).hexdigest()


def paired_bootstrap(values: np.ndarray, *, seed: int, reps: int = 10000) -> tuple[float, float]:
    values = np.asarray(values, float)
    if values.ndim != 1 or not np.isfinite(values).all() or len(values) == 0:
        raise ValueError("Bootstrap requires finite paired realization effects")
    rng = np.random.default_rng(seed)
    boot = np.empty(reps, dtype=float)
    batch = 250
    for start in range(0, reps, batch):
        n = min(batch, reps - start)
        take = rng.integers(0, len(values), size=(n, len(values)))
        boot[start:start+n] = values[take].mean(axis=1)
    return float(np.quantile(boot, .025)), float(np.quantile(boot, .975))


def classify_damage_state_batch(value: str) -> str:
    """Classify a simultaneous repair batch without crediting a single station."""
    states = [int(part) for part in str(value).split(";")]
    if not states or any(state not in (1, 2, 3, 4) for state in states):
        raise ValueError(f"Invalid damaged-state batch: {value!r}")
    has_ds1 = 1 in states
    has_ds2_4 = any(state in (2, 3, 4) for state in states)
    if has_ds1 and has_ds2_4:
        return "mixed_DS1_and_DS2_4"
    return "DS1" if has_ds1 else "DS2_4"


def summarize_event_damage_states(events: pd.DataFrame, *, bootstrap_reps: int = 10000) -> list[dict]:
    """Summarize external unlocks by repair DS, with realizations as resampling units."""
    required = {"policy", "realization_id", "damage_states", "newly_source_connected_other_count",
                "newly_source_connected_other_dependency_mass_people", "indirect_service_gain_person_equiv"}
    missing = required.difference(events.columns)
    if missing:
        raise ValueError(f"Event table is missing required fields: {sorted(missing)}")
    frame = events.copy()
    frame["damage_state_group"] = frame["damage_states"].map(classify_damage_state_batch)
    grouped = frame.groupby(["policy", "realization_id", "damage_state_group"], sort=True)
    per_realization = grouped.agg(
        event_batches=("damage_states", "size"),
        external_unlock_batches=("newly_source_connected_other_count", lambda values: int((values > 0).sum())),
        newly_connected_other_count=("newly_source_connected_other_count", "sum"),
        newly_connected_dependency_mass_people=("newly_source_connected_other_dependency_mass_people", "sum"),
        indirect_gain_person_equiv=("indirect_service_gain_person_equiv", "sum"),
    ).reset_index()
    per_realization["external_unlock_batch_fraction"] = (
        per_realization.external_unlock_batches / per_realization.event_batches
    )
    for column in ("newly_connected_other_count", "newly_connected_dependency_mass_people", "indirect_gain_person_equiv"):
        per_realization[f"{column}_per_event"] = per_realization[column] / per_realization.event_batches

    output = []
    metrics = ("external_unlock_batch_fraction", "newly_connected_other_count_per_event",
               "newly_connected_dependency_mass_people_per_event", "indirect_gain_person_equiv_per_event")
    for index, ((policy, ds_group), group) in enumerate(
            per_realization.groupby(["policy", "damage_state_group"], sort=True)):
        record = {"policy": str(policy), "damage_state_group": str(ds_group),
                  "event_batches": int(group.event_batches.sum()),
                  "realizations_with_events": int(group.realization_id.nunique()),
                  "realization_unit": "equal-weighted realization means; bootstrap resamples realization IDs"}
        for metric in metrics:
            values = group[metric].to_numpy(float)
            lo, hi = paired_bootstrap(values, seed=20261108 + index, reps=bootstrap_reps)
            record[metric] = float(values.mean())
            record[f"{metric}_bootstrap_95ci"] = [lo, hi]
        output.append(record)
    return output


def write_event_damage_state_summary(event_path: Path, out: Path) -> list[dict]:
    events = pd.read_csv(event_path, dtype={"realization_id": str, "policy": str,
                                            "damage_states": str}, float_precision="round_trip")
    summary = summarize_event_damage_states(events)
    target = out / "EVENT_UNLOCK_DAMAGE_STATE_SUMMARY.json"
    target.write_text(json.dumps({"bootstrap_replicates": 10000, "bootstrap_seed_base": 20261108,
                                  "event_rows": len(events), "summary": summary},
                                 indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def save_event_unlock_examples(event_path: Path, data: dict, schedules: dict, out: Path) -> list[dict]:
    """Render three verified, explicitly illustrative pre/post network states."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    events = pd.read_csv(event_path, dtype={"realization_id": str, "policy": str,
                                           "station_ids": str, "damage_states": str},
                         float_precision="round_trip")
    policies = ("impact-first", "hospital-first", "degree-first")
    selected = []
    station_ids = list(map(str, data["station_ids"]))
    station_index = {station: i for i, station in enumerate(station_ids)}
    for policy in policies:
        candidates = events[(events.policy == policy) & (events.batch_size == 1)
                            & (events.newly_source_connected_other_count > 0)].copy()
        if candidates.empty:
            raise ValueError(f"No single-station external-unlock event available for {policy}")
        median_gain = float(candidates.indirect_service_gain_person_equiv.median())
        row = candidates.iloc[(candidates.indirect_service_gain_person_equiv - median_gain).abs().argmin()]
        realization_index = int(str(row.realization_id).rsplit("_", 1)[1])
        station = str(row.single_station_id)
        target_idx = station_index[station]
        ds = data["ds"][:, realization_index]
        completion = np.asarray(schedules[policy]["completion"][realization_index], float)
        trace = _trace(ds, completion, data["station_ids"], data["graph"], data["sources"],
                       data["mapping"], data["population"])
        time = float(row.completion_time_hr)
        event_index = int(np.flatnonzero(trace["times"] == time)[0])
        pre_f, post_f = trace["F"][event_index - 1], trace["F"][event_index]
        pre_c, post_c = trace["C"][event_index - 1], trace["C"][event_index]
        external = (~np.isin(np.arange(92), [target_idx]) & pre_f & post_f & ~pre_c & post_c)
        new_count = int(external.sum())
        mass = float(data["station_population_mass"][external].sum())
        if (new_count != int(row.newly_source_connected_other_count)
                or not math.isclose(mass, float(row.newly_source_connected_other_dependency_mass_people),
                                    rel_tol=0, abs_tol=1e-8)):
            raise ValueError(f"Illustrative event does not reproduce its external unlock: {policy}/{row.realization_id}")
        selected.append({"policy": policy, "realization_id": str(row.realization_id),
                         "physical_sample_hash": str(row.physical_sample_hash),
                         "completion_time_hr": time, "station_id": station,
                         "damage_state": int(str(row.damage_states)),
                         "newly_source_connected_other_count": new_count,
                         "newly_source_connected_other_dependency_mass_people": mass,
                         "indirect_service_gain_person_equiv": float(row.indirect_service_gain_person_equiv),
                         "pre_functional": pre_f, "post_functional": post_f,
                         "pre_connected": pre_c, "post_connected": post_c,
                         "newly_connected": external})

    graph = data["graph"]
    positions = nx.spring_layout(graph, seed=20261105, weight=None, iterations=100)
    fig, axes = plt.subplots(2, len(selected), figsize=(12.0, 7.2), squeeze=False)
    fig.suptitle("Event-time source-path unlocking", y=.985, fontsize=14)
    fig.text(.5, .947, "Selected verified examples; force-directed layout is schematic, not geography or a typical effect size",
             ha="center", fontsize=9)
    colors = {"connected": "#25818A", "new": "#D6A23C", "repaired": "#2F4E6F",
              "functional_disconnected": "#AAB1B7", "not_functional": "#E3E6E8", "source": "#20262B"}
    sources = set(map(str, data["sources"]))
    for col, item in enumerate(selected):
        graph_nodes = list(map(str, graph.nodes))
        for row_idx, phase in enumerate(("pre", "post")):
            ax = axes[row_idx, col]
            functional = item[f"{phase}_functional"]
            connected = item[f"{phase}_connected"]
            event_station = item["station_id"]
            newly = item["newly_connected"] if phase == "post" else np.zeros(92, dtype=bool)
            active_nodes = {station_ids[i] for i in np.flatnonzero(functional)}
            active_edges = [(u, v) for u, v in graph.edges if str(u) in active_nodes and str(v) in active_nodes]
            nx.draw_networkx_edges(graph, positions, edgelist=list(graph.edges), ax=ax,
                                   edge_color="#E0E4E7", width=.42, alpha=.8)
            nx.draw_networkx_edges(graph, positions, edgelist=active_edges, ax=ax,
                                   edge_color="#89939B", width=.85, alpha=.75)
            node_color = []
            for station in graph_nodes:
                i = station_index[station]
                if station in sources:
                    node_color.append(colors["source"])
                elif station == event_station and phase == "post":
                    node_color.append(colors["repaired"])
                elif newly[i]:
                    node_color.append(colors["new"])
                elif connected[i]:
                    node_color.append(colors["connected"])
                elif functional[i]:
                    node_color.append(colors["functional_disconnected"])
                else:
                    node_color.append(colors["not_functional"])
            nx.draw_networkx_nodes(graph, positions, nodelist=graph_nodes, node_color=node_color,
                                   node_size=30, linewidths=.25, edgecolors="white", ax=ax)
            ax.set_axis_off()
        fig.text((col + .5) / len(selected), .866,
                 f"{item['policy']} | station {item['station_id']} (DS{item['damage_state']}) | {item['completion_time_hr']:.1f} h\n"
                 f"{item['newly_source_connected_other_count']} newly connected; "
                 f"{item['newly_source_connected_other_dependency_mass_people']:,.0f} mapped-person mass",
                 ha="center", va="top", fontsize=8.5)
    fig.text(.012, .63, "BEFORE", rotation=90, ha="center", va="center", fontsize=8)
    fig.text(.012, .29, "AFTER", rotation=90, ha="center", va="center", fontsize=8)
    legend_items = [plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=colors[key],
                               markeredgecolor="white", markersize=7, label=label)
                    for key, label in (("source", "Core source"), ("connected", "Source-connected"),
                                       ("new", "Newly connected other station"),
                                       ("repaired", "Repaired station"),
                                       ("functional_disconnected", "Functional, not source-connected"),
                                       ("not_functional", "Not functional"))]
    fig.legend(handles=legend_items, loc="lower center", ncol=3, frameon=False,
               bbox_to_anchor=(.5, .015), fontsize=8)
    fig.subplots_adjust(left=.05, right=.985, top=.78, bottom=.13, wspace=.06, hspace=.08)
    fig.savefig(out / "FIG_EVENT_UNLOCK_ILLUSTRATIONS.pdf", bbox_inches="tight",
                metadata={"Title": "Selected external source-unlock event examples", "CreationDate": None})
    fig.savefig(out / "FIG_EVENT_UNLOCK_ILLUSTRATIONS.png", dpi=600, bbox_inches="tight")
    plt.close(fig)
    record = [{k: v for k, v in item.items() if k not in {"pre_functional", "post_functional", "pre_connected", "post_connected", "newly_connected"}}
              for item in selected]
    (out / "EVENT_UNLOCK_ILLUSTRATION_PROVENANCE.json").write_text(
        json.dumps({"selection": "single-station external-unlock event nearest the median positive indirect gain within each of Impact-first, Hospital-first, and Degree-first",
                    "interpretation": "illustrative verified pre/post network states only; not representative effect estimates",
                    "events": record}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def _load_sources(summary_path: Path):
    phys_meta = json.loads(PHYSICAL_IDENTITY.read_text(encoding="utf-8"))
    phys = np.load(PHYSICAL_NPZ, allow_pickle=False)
    station_ids = phys["station_ids"].astype(str)
    if station_ids.shape != (92,) or len(set(station_ids)) != 92:
        raise ValueError("Frozen physical input does not contain 92 ordered unique stations")
    ds = phys["evaluation_ds"].copy()
    durations = phys["evaluation_duration"].copy()
    if ds.shape != (92, 1000) or durations.shape != ds.shape:
        raise ValueError("2pc50 physical realization arrays are not 92 x 1000")
    if sha256(PHYSICAL_NPZ) != phys_meta["files_sha256"]["2pc50"]:
        raise ValueError("2pc50 physical NPZ hash differs from frozen manifest")

    manifest = pd.read_csv(PHYSICAL_MANIFEST, dtype={"realization_id": str})
    manifest = manifest[(manifest.scenario == "2pc50") & (manifest.split == "evaluation")].copy()
    manifest = manifest.sort_values("realization_id", kind="stable").reset_index(drop=True)
    if len(manifest) != 1000 or manifest.realization_id.tolist() != [f"2pc50__evaluation_{i:04d}" for i in range(1000)]:
        raise ValueError("2pc50 evaluation manifest does not contain the exact ordered 1,000 IDs")
    station_hash = hashlib.sha256(("\n".join(station_ids) + "\n").encode()).hexdigest()
    sample_hashes = []
    for i, row in manifest.iterrows():
        if row.ordered_station_id_hash != station_hash:
            raise ValueError(f"Station order hash mismatch: {row.realization_id}")
        if not np.array_equal(ds[:, i], ds[:, i].astype("<i8")):
            raise ValueError(f"Invalid damage state array at {row.realization_id}")
        ds_hash = hashlib.sha256(ds[:, i].astype("<i8").tobytes()).hexdigest()
        duration_hash = hashlib.sha256(durations[:, i].astype("<f8").tobytes()).hexdigest()
        if ds_hash != row.DS_hash or duration_hash != row.duration_hash:
            raise ValueError(f"DS/duration hash mismatch: {row.realization_id}")
        sample = physical_hash(station_ids, ds[:, i], durations[:, i])
        if sample != row.physical_input_hash or sample != phys_meta["sample_hashes"][row.realization_id]:
            raise ValueError(f"Physical input hash mismatch: {row.realization_id}")
        sample_hashes.append(sample)

    mapping_long = pd.read_csv(MAPPING_PATH, dtype={"tract_id": str, "substation_id": str})
    if mapping_long.duplicated(["tract_id", "substation_id"]).any():
        raise ValueError("M1 mapping contains duplicate tract-station pairs")
    if set(mapping_long.substation_id) != set(station_ids):
        raise ValueError("M1 mapping station domain differs from frozen 92 IDs")
    pop_nunique = mapping_long.groupby("tract_id").population.nunique()
    if len(pop_nunique) != 2315 or (pop_nunique != 1).any():
        raise ValueError("M1 mapping does not carry one frozen population per each of 2,315 tracts")
    map_wide = mapping_long.pivot(index="tract_id", columns="substation_id", values="weight").fillna(0.0)
    map_wide = map_wide.reindex(columns=station_ids)
    weight = map_wide.to_numpy(float)
    population = mapping_long.groupby("tract_id", sort=False).population.first().reindex(map_wide.index).to_numpy(float)
    row_mass = weight.sum(axis=1)
    if not np.isfinite(weight).all() or (weight < 0).any() or np.max(np.abs(row_mass - 1)) > 1e-12:
        raise ValueError("M1 mapping weights are not finite, nonnegative, and unit row-mass")
    if not math.isclose(float(population.sum()), 9066522.0, rel_tol=0, abs_tol=1e-7):
        raise ValueError("Frozen M1 tract population does not sum to 9,066,522")
    station_population_mass = weight.T @ population

    edge_frame = pd.read_csv(GRAPH_PATH, dtype={"u": str, "v": str})
    graph = nx.from_pandas_edgelist(edge_frame, "u", "v")
    if set(graph.nodes) != set(station_ids) or graph.number_of_nodes() != 92 or graph.number_of_edges() != 318:
        raise ValueError("Graph differs from frozen 92-station / 318-edge topology")
    source_frame = pd.read_csv(SOURCE_PATH)
    id_col = next((c for c in ("substation_id", "HIFLD_ID", "ID", "id", "node_id") if c in source_frame.columns), None)
    if id_col is None:
        raise ValueError("Source table lacks station IDs")
    role_cols = [c for c in ("level", "role", "source_level", "source_type", "active_set") if c in source_frame.columns]
    role_text = pd.Series("", index=source_frame.index, dtype="object")
    for col in role_cols:
        role_text += " " + source_frame[col].astype(str).str.lower()
    is_source = (role_text.str.contains("core", na=False)
                 | role_text.str.contains("import_interface_proxy", na=False)
                 | role_text.str.contains("in_basin_generation_proxy", na=False))
    is_source &= ~role_text.str.contains(r"transit_hub_not_source|\btransit\b", na=False, regex=True)
    sources = set(source_frame.loc[is_source, id_col].astype(str)) & set(station_ids)
    if len(sources) != 14:
        raise ValueError(f"Frozen source set differs from 14 Core sources: {len(sources)}")

    summary = pd.read_parquet(summary_path)
    vuln = pd.read_parquet(VULN_SUMMARY_PATH)
    primary_mask = ((summary.hazard == "2pc50") & (summary.resource_scenario == "C57_D1")
                    & (summary.mapping == "M1_UTILITY_003") & (summary.gate == "G1_BASELINE_050")
                    & (summary.comparison_domain == "mapping_native_domain"))
    primary = summary.loc[primary_mask].copy()
    vmask = ((vuln.hazard == "2pc50") & (vuln.resource_scenario == "C57_D1")
             & (vuln.mapping == "M1_UTILITY_003") & (vuln.gate == "G1_BASELINE_050")
             & (vuln.comparison_domain == "mapping_native_domain"))
    v = vuln.loc[vmask].copy()
    if len(v) != 1000 or set(v.strategy_id) != {"vulnerability-first"}:
        raise ValueError("Separate frozen Vulnerability-first result is not 1,000 matched rows")
    expected = dict(zip(manifest.realization_id, manifest.physical_input_hash))
    for frame, label in ((primary, "formal summary"), (v, "vulnerability amendment")):
        if frame.realization_id.duplicated().any() or len(frame) == 0:
            if label == "formal summary":
                pass
            else:
                raise ValueError(f"Duplicate or missing realization identities in {label}")
        if label == "vulnerability amendment":
            if any(expected.get(row.realization_id) != row.physical_sample_hash for row in frame.itertuples()):
                raise ValueError("Vulnerability-first physical realization hashes do not match frozen manifest")
    primary = pd.concat([primary, v], ignore_index=True)
    primary = primary[primary.strategy_id != "direct-community"].copy()
    if primary.duplicated(["strategy_id", "realization_id"]).any():
        raise ValueError("Primary policy table contains duplicate realization-policy rows")
    ids_by_policy = primary.groupby("strategy_id").realization_id.apply(set)
    expected_ids = set(manifest.realization_id.astype(str))
    actual_policies = set(ids_by_policy.index.astype(str))
    bad_policy_ids = {
        policy: (len(ids_by_policy.loc[policy] - expected_ids),
                 len(expected_ids - ids_by_policy.loc[policy]))
        for policy in actual_policies & set(COMPARE)
        if ids_by_policy.loc[policy] != expected_ids
    }
    if actual_policies != set(COMPARE) or bad_policy_ids:
        raise ValueError(f"Primary comparison realization mismatch; missing policies="
                         f"{sorted(set(COMPARE) - actual_policies)}, unexpected policies="
                         f"{sorted(actual_policies - set(COMPARE))}, ID differences={bad_policy_ids}")

    return dict(
        station_ids=station_ids, ds=ds, durations=durations, manifest=manifest,
        sample_hashes=np.asarray(sample_hashes, dtype=str), mapping=weight,
        population=population, tract_ids=map_wide.index.to_numpy(str),
        station_population_mass=station_population_mass, total_population=float(population.sum()),
        graph=graph, sources=sources, summary=summary, primary=primary,
    )


def _load_sequences_and_decoder(data):
    rule_data = json.loads(RULE_SEQUENCE_PATH.read_text(encoding="utf-8"))["2pc50"]
    vuln_data = json.loads(VULN_SEQUENCE_PATH.read_text(encoding="utf-8"))
    sequences = {k: tuple(map(str, v)) for k, v in rule_data.items()}
    sequences["vulnerability-first"] = tuple(map(str, vuln_data["ordered_station_ids"]))
    ids = tuple(map(str, data["station_ids"]))
    if any(len(seq) != 92 or set(seq) != set(ids) for seq in sequences.values()):
        raise ValueError("Frozen sequence is not a full 92-station permutation")
    origins = (pd.read_csv(CREW_PATH).sort_values("crew_origin_index")
               .travel_matrix_origin_key.astype(str).tolist())
    base = pd.read_csv(BASE_TRAVEL).set_index("base_id")
    base.index = base.index.astype(str)
    base.columns = base.columns.astype(str)
    task = pd.read_csv(TASK_TRAVEL).set_index("id")
    task.index = task.index.astype(str)
    task.columns = task.columns.astype(str)
    decoder = FormalScheduleDecoder({"ids": ids, "base": base, "task": task})
    zero_base = base.copy()
    zero_task = task.copy()
    zero_base.loc[:, :] = 0.0
    zero_task.loc[:, :] = 0.0
    zero_decoder = FormalScheduleDecoder({"ids": ids, "base": zero_base, "task": zero_task})
    origins_idx = decoder.origins(origins)
    zero_origins_idx = zero_decoder.origins(origins)
    return sequences, origins, decoder, origins_idx, zero_decoder, zero_origins_idx


def _verify_schedule_archives(data, sequences):
    rows = []
    manifest_hash = dict(zip(data["manifest"].realization_id, data["manifest"].physical_input_hash))
    for policy in POLICIES:
        path = _filesystem_path(SCHEDULES / f"2pc50__C57_D1__{policy}.npz")
        sidecar = path.with_suffix(".json")
        if not path.is_file() or not sidecar.is_file():
            raise FileNotFoundError(f"Frozen schedule archive missing: {path}")
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        actual_hash = sha256(path)
        seq_hash = sequence_hash(sequences[policy])
        if actual_hash != record["npz_sha256"] or record.get("status") != "FORMAL_FROZEN_MATRIX_V1":
            raise ValueError(f"Frozen prepass identity/hash mismatch: {path.name}")
        if record["identity"]["sequence_sha256"] != seq_hash:
            raise ValueError(f"Priority sequence hash mismatch: {policy}")
        if record["identity"]["physical_hashes_sha256"] != hashlib.sha256(("\n".join(data["sample_hashes"]) + "\n").encode()).hexdigest():
            raise ValueError(f"Schedule physical-hash chain mismatch: {policy}")
        z = np.load(path, allow_pickle=False)
        if not np.array_equal(z["station_ids"].astype(str), data["station_ids"]):
            raise ValueError(f"Schedule station order mismatch: {policy}")
        if not np.array_equal(z["physical_hashes"].astype(str), data["sample_hashes"]):
            raise ValueError(f"Schedule physical realization IDs mismatch: {policy}")
        rows.append({"policy": policy,
                     "schedule_file": f"Formal_Experiment_20260923/Formal_Schedule_Prepass/{path.name}",
                     "schedule_sha256": actual_hash, "sequence_sha256": seq_hash,
                     "realization_count": len(z["physical_hashes"]),
                     "physical_hashes_match": True, "station_order_match": True})
        z.close()
    return pd.DataFrame(rows)


def verify_decoder_samples(data, sequences, decoder, origins_idx):
    checks = []
    sample_ids = (0, 137, 999)
    for policy in POLICIES:
        z = np.load(_filesystem_path(SCHEDULES / f"2pc50__C57_D1__{policy}.npz"), allow_pickle=False)
        order = decoder.order(sequences[policy])
        for i in sample_ids:
            got = decoder.decode(order=order, damage=data["ds"][:, i],
                                 duration=data["durations"][:, i], origins=origins_idx)
            for j, key in enumerate(("completion", "arrival", "travel", "crew", "previous", "dispatch")):
                same = (np.array_equal(got[j], z[key][i]) if got[j].dtype.kind in "iu"
                        else np.allclose(got[j], z[key][i], rtol=0, atol=1e-12, equal_nan=True))
                checks.append({"policy": policy, "realization_index": i, "array": key,
                               "exact_match": bool(same),
                               "max_abs_difference": float(np.nanmax(np.abs(got[j] - z[key][i])))
                               if got[j].dtype.kind not in "iu" else 0.0})
                if not same:
                    raise ValueError(f"Production decoder mismatch: {policy}, {i}, {key}")
        z.close()
    return pd.DataFrame(checks)


def _summary_rows(data):
    keep = data["primary"].copy()
    cols = [SUMMARY_COL[c] for c in COMPONENTS]
    if not np.isfinite(keep[cols].to_numpy(float)).all():
        raise ValueError("Frozen per-realization component outcomes contain non-finite values")
    additivity = keep[cols[:3]].sum(axis=1).to_numpy() - keep[cols[3]].to_numpy()
    if np.max(np.abs(additivity)) >= 1e-10:
        raise ValueError("Frozen integrated component additivity exceeds 1e-10 h")
    return keep


def make_paired_effects(primary: pd.DataFrame) -> pd.DataFrame:
    records = []
    pivoted = {name: primary[primary.strategy_id == name].set_index("realization_id")
               for name in COMPARE}
    rng_seed = 20261107
    for candidate in COMPARE:
        if candidate == "hospital-first":
            continue
        for component in COMPONENTS:
            col = SUMMARY_COL[component]
            pair = pivoted[candidate][col].reindex(pivoted["hospital-first"].index).to_numpy(float) - pivoted["hospital-first"][col].to_numpy(float)
            lo, hi = paired_bootstrap(pair, seed=rng_seed + len(records))
            records.append({"contrast": f"{candidate} minus hospital-first", "candidate": candidate,
                            "reference": "hospital-first", "component": component,
                            "n_paired_realizations": len(pair), "mean_difference_hr": float(pair.mean()),
                            "paired_bootstrap_95ci_low_hr": lo, "paired_bootstrap_95ci_high_hr": hi,
                            "realization_p05_hr": float(np.quantile(pair, .05)),
                            "realization_p95_hr": float(np.quantile(pair, .95)),
                            "positive_count": int((pair > 0).sum()),
                            "negative_count": int((pair < 0).sum()),
                            "zero_count": int((pair == 0).sum())})
    # The direct-community duplicate is excluded from independent comparisons.
    return pd.DataFrame(records)


def reproduce_reference_checks(primary: pd.DataFrame) -> dict:
    means = (primary.groupby("strategy_id")[[SUMMARY_COL[c] for c in COMPONENTS]
             ].mean().rename(columns={v: k for k, v in SUMMARY_COL.items()}))
    un = means.loc["unconstrained"].to_dict()
    un_error = {k: float(un[k] - EXPECTED_UNCONSTRAINED[k]) for k in COMPONENTS}
    impact = primary[primary.strategy_id == "impact-first"].set_index("realization_id")
    hospital = primary[primary.strategy_id == "hospital-first"].set_index("realization_id")
    degree = primary[primary.strategy_id == "degree-first"].set_index("realization_id")
    delta = degree[[SUMMARY_COL[c] for c in COMPONENTS]] - hospital[[SUMMARY_COL[c] for c in COMPONENTS]]
    paired_mean = {c: float(delta[SUMMARY_COL[c]].mean()) for c in COMPONENTS}
    paired_range = {c: [float(delta[SUMMARY_COL[c]].quantile(.05)),
                        float(delta[SUMMARY_COL[c]].quantile(.95))] for c in COMPONENTS}
    errors = {c: paired_mean[c] - EXPECTED_DEGREE_MINUS_HOSPITAL[c] for c in COMPONENTS}
    if max(map(abs, un_error.values())) > 5e-8 or max(map(abs, errors.values())) > 5e-8:
        raise ValueError("Saved reference QA means were not reproduced from frozen realization rows")
    for component, expected in EXPECTED_REALIZATION_RANGE.items():
        if not np.allclose(paired_range[component], expected, rtol=0, atol=5e-8):
            raise ValueError(f"Degree-minus-Hospital individual realization range mismatch: {component}")
    return {"unconstrained_means_hr": un, "unconstrained_expected_errors_hr": un_error,
            "degree_minus_hospital_paired_means_hr": paired_mean,
            "degree_minus_hospital_mean_expected_errors_hr": errors,
            "degree_minus_hospital_realization_p05_p95_hr": paired_range,
            "max_integrated_additivity_error_hr": float(np.max(np.abs(
                primary[[SUMMARY_COL[c] for c in COMPONENTS[:3]]].sum(axis=1)
                - primary[SUMMARY_COL["total"]]))),
            "paired_unit": "physical realization ID",
            "confidence_method": "10,000 paired realization bootstrap; fixed seed 20261107"}


def _trace(ds: np.ndarray, completion: np.ndarray, station_ids, graph, sources,
           mapping: np.ndarray, population: np.ndarray, *, mode="source_gate"):
    ds = np.asarray(ds, int)
    completion = np.asarray(completion, float)
    if ds.shape != (92,) or completion.shape != (92,):
        raise ValueError("Trace requires 92 frozen station states")
    damaged = ds > 0
    if not np.isfinite(completion[damaged]).all() or np.any(completion[damaged] < 0):
        raise ValueError("Frozen damaged tasks require finite nonnegative completions")
    if np.any(completion[damaged] > 480.0):
        raise ValueError("Frozen schedule completion exceeds the registered 480 h horizon")
    initial = np.asarray([INITIAL_BY_DS[int(x)] for x in ds], float)
    event_times = np.unique(np.r_[0.0, completion[damaged], 480.0])
    f = np.tile(initial, (len(event_times), 1))
    for j in np.flatnonzero(damaged):
        f[event_times >= completion[j], j] = 1.0
    raw = pd.DataFrame(f, index=event_times, columns=station_ids)
    gate = evaluate_source_gate(raw, graph, sources, threshold=.5, mode=mode)
    names = ("L_self", "L_threshold", "L_source", "L_total")
    dt = np.diff(event_times)
    integrals = {name: np.sum(getattr(gate, name).to_numpy(float)[:-1] * dt[:, None], axis=0)
                 for name in names}
    station_mass = mapping.T @ population
    total_pop = float(population.sum())
    burden = {name.removeprefix("L_"): float(np.dot(station_mass, val) / total_pop)
              for name, val in integrals.items()}
    err = max(abs(burden["self"] + burden["threshold"] + burden["source"] - burden["total"]),
              float(np.max(np.abs(gate.L_self.to_numpy() + gate.L_threshold.to_numpy()
                                  + gate.L_source.to_numpy() - gate.L_total.to_numpy())) * 480.0))
    if err >= 1e-10:
        raise ValueError(f"Event/integrated component identity failed: {err}")
    return dict(times=event_times, f=gate.f.to_numpy(float), F=gate.F.to_numpy(bool),
                C=gate.C.to_numpy(bool), e=gate.e.to_numpy(float), gate=gate,
                metrics=burden, total_travel=None, additivity_error=err)


def _event_rows(policy, realization_id, physical_hash_value, ds, duration,
                completion, arrival, travel, crew, dispatch, trace, station_ids,
                station_mass, total_pop, degree, betweenness):
    rows = []
    comp = np.asarray(completion, float)
    valid = np.flatnonzero((np.asarray(ds) > 0) & np.isfinite(comp) & (comp > 0) & (comp <= 480))
    for t in np.unique(comp[valid]):
        stations = np.flatnonzero((comp == t) & (np.asarray(ds) > 0))
        idx = int(np.flatnonzero(trace["times"] == t)[0])
        before_e, after_e = trace["e"][idx - 1], trace["e"][idx]
        before_f, after_f = trace["f"][idx - 1], trace["f"][idx]
        before_F, after_F = trace["F"][idx - 1], trace["F"][idx]
        before_C, after_C = trace["C"][idx - 1], trace["C"][idx]
        event_mask = np.zeros(92, dtype=bool)
        event_mask[stations] = True
        new_other = (~event_mask) & before_F & after_F & (~before_C) & after_C
        delta_e = after_e - before_e
        direct_gain = float(np.dot(station_mass[event_mask], delta_e[event_mask]))
        indirect_gain = float(np.dot(station_mass[new_other], delta_e[new_other]))
        total_gain = float(np.dot(station_mass, delta_e))
        task_ids = [str(station_ids[j]) for j in stations]
        vals = lambda arr: ";".join("NA" if not np.isfinite(arr[j]) else f"{float(arr[j]):.12g}" for j in stations)
        rows.append({
            "hazard": "2pc50", "resource": "C57_D1", "policy": policy,
            "realization_id": realization_id, "physical_sample_hash": physical_hash_value,
            "completion_time_hr": float(t), "batch_size": int(len(stations)),
            "station_ids": ";".join(task_ids), "single_station_id": task_ids[0] if len(task_ids) == 1 else "",
            "damage_states": ";".join(str(int(ds[j])) for j in stations),
            "repair_durations_hr": vals(duration), "arrival_times_hr": vals(arrival),
            "crew_indices": ";".join(str(int(crew[j])) for j in stations),
            "travel_times_hr": vals(travel), "dispatch_ranks": ";".join(str(int(dispatch[j])) for j in stations),
            "new_threshold_eligible_count": int(np.sum((~before_F) & after_F & event_mask)),
            "newly_source_connected_other_count": int(new_other.sum()),
            "newly_source_connected_other_dependency_mass_people": float(station_mass[new_other].sum()),
            "direct_service_gain_person_equiv": direct_gain,
            "indirect_service_gain_person_equiv": indirect_gain,
            "total_service_gain_person_equiv": total_gain,
            "direct_service_gain_population_fraction": direct_gain / total_pop,
            "indirect_service_gain_population_fraction": indirect_gain / total_pop,
            "total_service_gain_population_fraction": total_gain / total_pop,
            "pre_event_functional_stations": int(before_F.sum()),
            "pre_event_source_connected_stations": int(before_C.sum()),
            "post_event_source_connected_stations": int(after_C.sum()),
            "mean_station_degree_static": float(np.mean(degree[stations])),
            "mean_station_betweenness_static": float(np.mean(betweenness[stations])),
        })
    return rows


def _single_state(raw_state, station_ids, graph, sources):
    raw = np.asarray(raw_state, float)
    if raw.shape != (len(station_ids),) or not np.isfinite(raw).all() or np.any((raw < 0) | (raw > 1)):
        raise ValueError("Single-state gate requires one complete finite [0,1] vector")
    functional = raw >= .5
    functional_nodes = {str(station_ids[i]) for i in np.flatnonzero(functional)}
    connected_nodes = set()
    for source in sources:
        source = str(source)
        if source not in functional_nodes or source in connected_nodes:
            continue
        stack = [source]
        connected_nodes.add(source)
        while stack:
            node = stack.pop()
            for neighbor in graph.adj[node]:
                neighbor = str(neighbor)
                if neighbor in functional_nodes and neighbor not in connected_nodes:
                    connected_nodes.add(neighbor)
                    stack.append(neighbor)
    connected = np.asarray([str(s) in connected_nodes for s in station_ids], dtype=bool)
    availability = raw * functional * connected
    return functional, connected, availability


def verify_single_state_gate_equivalence(data, n_checks=16):
    checks = []
    for i in range(n_checks):
        ds = data["ds"][:, i]
        raw = np.asarray([INITIAL_BY_DS[int(x)] for x in ds], float)
        repaired = np.flatnonzero(ds > 0)[:i]
        raw[repaired] = 1.0
        expected = _single_state(raw, data["station_ids"], data["graph"], data["sources"])
        frame = pd.DataFrame([raw], index=[0.0], columns=data["station_ids"])
        gate = evaluate_source_gate(frame, data["graph"], data["sources"], threshold=.5)
        actual = (gate.F.to_numpy(bool)[0], gate.C.to_numpy(bool)[0], gate.e.to_numpy(float)[0])
        equal = (np.array_equal(expected[0], actual[0]) and np.array_equal(expected[1], actual[1])
                 and np.allclose(expected[2], actual[2], rtol=0, atol=0))
        checks.append({"realization_index": i, "exact_equivalence": bool(equal)})
        if not equal:
            raise ValueError(f"Diagnostic single-state source gate differs from production at sample {i}")
    return checks


def _potential_external_unlock(j, t, ds, completion, station_ids, graph, sources, station_mass):
    initial = np.asarray([INITIAL_BY_DS[int(x)] for x in ds], float)
    pre = initial.copy()
    repaired_before = (np.asarray(ds) > 0) & (np.asarray(completion) < t)
    pre[repaired_before] = 1.0
    _, _, e0 = _single_state(pre, station_ids, graph, sources)
    after = pre.copy()
    after[j] = 1.0
    F1, C1, e1 = _single_state(after, station_ids, graph, sources)
    F0, C0, _ = _single_state(pre, station_ids, graph, sources)
    external = np.ones(92, bool)
    external[j] = False
    newly = external & F0 & F1 & (~C0) & C1
    gain = float(np.dot(station_mass[newly], e1[newly] - e0[newly]))
    return gain, int(newly.sum()), float(station_mass[newly].sum())


def _move_earlier(sequence, station, positions):
    seq = list(sequence)
    old = seq.index(station)
    new = max(0, old - positions)
    seq.pop(old)
    seq.insert(new, station)
    if set(seq) != set(sequence) or len(seq) != 92:
        raise RuntimeError("Priority perturbation did not preserve the station permutation")
    return tuple(seq), old, new


def _choose_targets(policy, ds, duration, completion, trace, events, station_ids,
                    station_mass, graph, sources, rng):
    damaged = np.flatnonzero(np.asarray(ds) > 0)
    if not len(damaged):
        return {}
    initial = np.asarray([INITIAL_BY_DS[int(x)] for x in ds], float)
    direct = station_mass * (1.0 - initial) * np.asarray(duration, float)
    targets = {"high_direct_self_loss": int(damaged[np.argmax(direct[damaged])])}

    single = [e for e in events if e["batch_size"] == 1]
    positive_external = [e for e in single if e["indirect_service_gain_person_equiv"] > 0]
    if positive_external:
        best = max(positive_external, key=lambda e: (e["indirect_service_gain_person_equiv"], -e["completion_time_hr"]))
        targets["high_observed_downstream_unlock"] = int(np.where(station_ids == best["single_station_id"])[0][0])

    direct_median = float(np.median(direct[damaged]))
    potentials = []
    for j in damaged:
        t = float(completion[j])
        gain, count, mass = _potential_external_unlock(j, t, ds, completion,
                                                      station_ids, graph, sources, station_mass)
        if direct[j] <= direct_median:
            potentials.append((gain, -float(direct[j]), int(j), count, mass))
    if potentials:
        best = max(potentials)
        if best[0] > 0:
            targets["low_direct_dynamic_bottleneck"] = best[2]
    targets["random_control"] = int(rng.choice(damaged))
    return targets


def _first_external_unlock(trace, completion):
    comp = np.asarray(completion, float)
    for idx, t in enumerate(trace["times"][1:], start=1):
        repaired = (np.isfinite(comp) & (comp == t))
        new_other = (~repaired) & trace["F"][idx - 1] & trace["F"][idx] & (~trace["C"][idx - 1]) & trace["C"][idx]
        if new_other.any():
            return float(t)
    return float("nan")


def _decode_metrics(decoder, sequence, ds, duration, origins, data):
    decoded = _decode_python_body(decoder, sequence, ds, duration, origins)
    completion, arrival, travel, crew, previous, dispatch, clocks = decoded
    trace = _trace(ds, completion, data["station_ids"], data["graph"], data["sources"],
                   data["mapping"], data["population"])
    trace["total_travel"] = float(np.nansum(travel))
    trace["completion"] = completion
    trace["arrival"] = arrival
    trace["travel"] = travel
    trace["crew"] = crew
    trace["previous"] = previous
    trace["dispatch"] = dispatch
    trace["clocks"] = clocks
    return trace


def _decode_python_body(decoder, sequence, ds, duration, origins):
    """Run the production decoder's exact source body without the Numba JIT."""
    fn = getattr(_decode, "py_func", _decode)
    return fn(decoder.order(sequence), np.asarray(ds, dtype=np.int64),
              np.asarray(duration, dtype=np.float64), np.asarray(origins, dtype=np.int64),
              decoder.base, decoder.task)


def run_perturbations(data, sequences, decoder, origins_idx, zero_decoder, zero_origins_idx,
                      schedules, sample_ids):
    rng_target = np.random.default_rng(20261106)
    rows = []
    pilot_checks = []
    station_mass = data["station_population_mass"]
    for policy in ("impact-first", "hospital-first"):
        schedule = schedules[policy]
        for i in range(8):
            got = _decode_python_body(decoder, sequences[policy], data["ds"][:, i],
                                      data["durations"][:, i], origins_idx)
            for j, key in enumerate(("completion", "arrival", "travel", "crew", "previous", "dispatch")):
                equal = (np.array_equal(got[j], schedule[key][i]) if got[j].dtype.kind in "iu"
                         else np.allclose(got[j], schedule[key][i], rtol=0, atol=1e-12, equal_nan=True))
                if not equal:
                    raise ValueError(f"Smoke-pilot decoder mismatch: {policy} {i} {key}")
                pilot_checks.append({"policy": policy, "realization_index": i, "array": key, "exact_match": True})

        for i in sample_ids:
            print(f"  perturbation start: {policy}, realization index {int(i)}", flush=True)
            ds = data["ds"][:, i]
            duration = data["durations"][:, i]
            baseline_sequence = sequences[policy]
            base_comp = schedule["completion"][i]
            baseline = _trace(ds, base_comp, data["station_ids"], data["graph"], data["sources"],
                              data["mapping"], data["population"])
            baseline["completion"] = np.asarray(base_comp, float)
            baseline["total_travel"] = float(np.nansum(schedule["travel"][i]))
            base_rows = _event_rows(policy, f"2pc50__evaluation_{i:04d}", data["sample_hashes"][i],
                                    ds, duration, base_comp, schedule["arrival"][i], schedule["travel"][i],
                                    schedule["crew"][i], schedule["dispatch"][i], baseline,
                                    data["station_ids"], station_mass, data["total_population"],
                                    data["degree"], data["betweenness"])
            targets = _choose_targets(policy, ds, duration, base_comp, baseline, base_rows,
                                      data["station_ids"], station_mass, data["graph"], data["sources"], rng_target)

            no_travel_base = _decode_metrics(zero_decoder, baseline_sequence, ds, duration, zero_origins_idx, data)
            for category, target_idx in targets.items():
                target = str(data["station_ids"][target_idx])
                for travel_case, active_decoder, active_origins, reference in (
                        ("production_directed_travel", decoder, origins_idx, baseline),
                        ("diagnostic_zero_travel", zero_decoder, zero_origins_idx, no_travel_base)):
                    for shift in (1, 3, 5):
                        shifted, old_pos, new_pos = _move_earlier(baseline_sequence, target, shift)
                        cf = _decode_metrics(active_decoder, shifted, ds, duration, active_origins, data)
                        target_finish = float(cf["completion"][target_idx])
                        original_finish = float(reference["completion"][target_idx])
                        result = {
                            "baseline_policy": policy, "target_category": category,
                            "target_station_id": target, "realization_index": int(i),
                            "realization_id": f"2pc50__evaluation_{i:04d}",
                            "physical_sample_hash": data["sample_hashes"][i],
                            "travel_condition": travel_case, "requested_positions_earlier": shift,
                            "original_full_sequence_position_0based": old_pos,
                            "new_full_sequence_position_0based": new_pos,
                            "actual_positions_earlier": old_pos - new_pos,
                            "baseline_total_burden_hr": reference["metrics"]["total"],
                            "counterfactual_total_burden_hr": cf["metrics"]["total"],
                            "delta_total_burden_hr": cf["metrics"]["total"] - reference["metrics"]["total"],
                            "baseline_self_hr": reference["metrics"]["self"],
                            "counterfactual_self_hr": cf["metrics"]["self"],
                            "delta_self_hr": cf["metrics"]["self"] - reference["metrics"]["self"],
                            "baseline_threshold_hr": reference["metrics"]["threshold"],
                            "counterfactual_threshold_hr": cf["metrics"]["threshold"],
                            "delta_threshold_hr": cf["metrics"]["threshold"] - reference["metrics"]["threshold"],
                            "baseline_source_hr": reference["metrics"]["source"],
                            "counterfactual_source_hr": cf["metrics"]["source"],
                            "delta_source_hr": cf["metrics"]["source"] - reference["metrics"]["source"],
                            "baseline_target_completion_hr": original_finish,
                            "counterfactual_target_completion_hr": target_finish,
                            "delta_target_completion_hr": target_finish - original_finish,
                            "baseline_total_travel_hr": reference["total_travel"],
                            "counterfactual_total_travel_hr": cf["total_travel"],
                            "delta_total_travel_hr": cf["total_travel"] - reference["total_travel"],
                            "baseline_first_external_unlock_hr": _first_external_unlock(reference, reference["completion"]),
                            "counterfactual_first_external_unlock_hr": _first_external_unlock(cf, cf["completion"]),
                        }
                        rows.append(result)
            if (i + 1) % 16 == 0:
                print(f"  paired counterfactuals: {policy}, sample {i} ({len(rows)} rows)", flush=True)
        print(f"  perturbations complete: {policy}", flush=True)
    return pd.DataFrame(rows), pd.DataFrame(pilot_checks)


def summarize_perturbations(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    group_cols = ["baseline_policy", "target_category", "travel_condition", "requested_positions_earlier"]
    for k, group in frame.groupby(group_cols, sort=True, dropna=False):
        group = group.sort_values("realization_index")
        # Each group has at most one result per realization; bootstrap unit is the realization.
        vals = group.delta_total_burden_hr.to_numpy(float)
        rng_seed = 20261107 + len(records)
        lo, hi = paired_bootstrap(vals, seed=rng_seed)
        records.append(dict(zip(group_cols, k), n_realizations=len(group),
                            mean_delta_total_burden_hr=float(vals.mean()),
                            paired_bootstrap_95ci_low_hr=lo, paired_bootstrap_95ci_high_hr=hi,
                            beneficial_count=int((vals < 0).sum()), harmful_count=int((vals > 0).sum()),
                            no_change_count=int((vals == 0).sum()),
                            median_delta_source_hr=float(group.delta_source_hr.median()),
                            median_delta_self_hr=float(group.delta_self_hr.median()),
                            mean_delta_travel_hr=float(group.delta_total_travel_hr.mean()),
                            mean_delta_target_completion_hr=float(group.delta_target_completion_hr.mean())))
    return pd.DataFrame(records)


def _write_event_outputs(data, schedules, out: Path):
    station_ids = data["station_ids"]
    degree = np.asarray([data["graph"].degree(str(s)) for s in station_ids], float)
    btw_map = nx.betweenness_centrality(data["graph"], normalized=True, weight=None)
    betweenness = np.asarray([btw_map[str(s)] for s in station_ids], float)
    station_mass = data["station_population_mass"]
    summary_rows = []
    csv_path = out / "REPAIR_EVENT_UNLOCKS.csv.gz"
    header = None
    compare = data["primary"].set_index(["strategy_id", "realization_id"])
    max_repro = 0.0
    max_event_additivity = 0.0
    sample_targets = {}
    perturb_sample = np.random.default_rng(20261105).choice(np.arange(8, 1000), size=128, replace=False)
    sample_set = set(map(int, perturb_sample))
    with gzip.open(csv_path, "wt", encoding="utf-8", newline="") as stream:
        writer = None
        for policy in POLICIES:
            z = schedules[policy]
            accum = {}
            for i in range(1000):
                ds = data["ds"][:, i]
                duration = data["durations"][:, i]
                completion = z["completion"][i]
                trace = _trace(ds, completion, station_ids, data["graph"], data["sources"],
                               data["mapping"], data["population"])
                row_id = f"2pc50__evaluation_{i:04d}"
                official = compare.loc[(policy, row_id)]
                err = max(abs(trace["metrics"][c] - float(official[SUMMARY_COL[c]])) for c in COMPONENTS)
                max_repro = max(max_repro, err)
                if err >= 1e-10:
                    raise ValueError(f"Reconstructed source-gate burden does not match frozen output: {policy} {row_id} {err}")
                events = _event_rows(policy, row_id, data["sample_hashes"][i], ds, duration,
                                     completion, z["arrival"][i], z["travel"][i], z["crew"][i],
                                     z["dispatch"][i], trace, station_ids, station_mass,
                                     data["total_population"], degree, betweenness)
                for event in events:
                    if writer is None:
                        header = list(event)
                        writer = csv.DictWriter(stream, fieldnames=header)
                        writer.writeheader()
                    writer.writerow(event)
                ext = np.asarray([e["indirect_service_gain_person_equiv"] for e in events], float)
                total = np.asarray([e["total_service_gain_person_equiv"] for e in events], float)
                accum.setdefault("n_events", []).append(len(events))
                accum.setdefault("fraction_events_external_unlock", []).append(float(np.mean(ext > 0)) if len(ext) else 0.0)
                accum.setdefault("mean_external_gain_person_equiv_per_event", []).append(float(ext.mean()) if len(ext) else 0.0)
                accum.setdefault("mean_total_gain_person_equiv_per_event", []).append(float(total.mean()) if len(total) else 0.0)
                accum.setdefault("first_external_unlock_hr", []).append(
                    min((e["completion_time_hr"] for e in events if e["indirect_service_gain_person_equiv"] > 0), default=np.nan))
                if i in sample_set and policy in ("impact-first", "hospital-first"):
                    sample_targets[(policy, i)] = events
            for metric, values in accum.items():
                vals = np.asarray(values, float)
                valid = vals[np.isfinite(vals)]
                lo, hi = paired_bootstrap(valid, seed=20261107 + len(summary_rows)) if len(valid) else (np.nan, np.nan)
                summary_rows.append({"policy": policy, "metric": metric, "n_realizations": len(valid),
                                     "mean": float(np.mean(valid)) if len(valid) else np.nan,
                                     "bootstrap_95ci_low": lo, "bootstrap_95ci_high": hi,
                                     "unit": "realization-level mean; event rows are not independent"})
            print(f"  event history complete: {policy}", flush=True)
    if max_repro >= 1e-10:
        raise ValueError("Frozen burden reconstruction check failed")
    return csv_path, pd.DataFrame(summary_rows), max_repro, perturb_sample, sample_targets, degree, betweenness


def _load_validated_event_checkpoint(data, schedules, out: Path):
    """Reuse a completed event pass after rechecking its full frozen event keys."""
    path = out / "REPAIR_EVENT_UNLOCKS.csv.gz"
    summary_path = out / "EVENT_UNLOCK_REALIZATION_SUMMARY.csv"
    sample_path = out / "PERTURBATION_SAMPLE_IDS.json"
    if not all(p.is_file() for p in (path, summary_path, sample_path)):
        raise FileNotFoundError("Completed event-history checkpoint is incomplete")
    events = pd.read_csv(path, dtype={"realization_id": str, "physical_sample_hash": str,
                                     "policy": str, "station_ids": str}, float_precision="round_trip")
    expected_policies = set(POLICIES)
    if set(events.policy) != expected_policies:
        raise ValueError("Event checkpoint does not contain every frozen comparison policy")
    expected_ids = {f"2pc50__evaluation_{i:04d}" for i in range(1000)}
    expected_hash = dict(zip(data["manifest"].realization_id, data["sample_hashes"]))
    for policy in POLICIES:
        subset = events[events.policy == policy]
        if not set(subset.realization_id).issubset(expected_ids):
            raise ValueError(f"Unexpected realization ID in event checkpoint: {policy}")
        if any(expected_hash.get(r.realization_id) != r.physical_sample_hash for r in subset.itertuples()):
            raise ValueError(f"Physical hash mismatch in event checkpoint: {policy}")
        expected_rows = []
        z = schedules[policy]
        for i in range(1000):
            comp = np.asarray(z["completion"][i], float)
            valid = (data["ds"][:, i] > 0) & np.isfinite(comp) & (comp > 0) & (comp <= 480)
            for t in np.unique(comp[valid]):
                stations = np.flatnonzero((comp == t) & (data["ds"][:, i] > 0))
                names = ";".join(str(data["station_ids"][j]) for j in stations)
                expected_rows.append((f"2pc50__evaluation_{i:04d}", float(t), names, len(stations)))
        got = subset[["realization_id", "completion_time_hr", "station_ids", "batch_size"]]
        if len(got) != len(expected_rows):
            raise ValueError(f"Incomplete completion-event rows in checkpoint: {policy}")
        expected = set(expected_rows)
        actual = set((str(r.realization_id), float(r.completion_time_hr), str(r.station_ids), int(r.batch_size))
                     for r in got.itertuples(index=False))
        if actual != expected:
            raise ValueError(f"Completion event identity mismatch in checkpoint: {policy}")
    metric_summary = pd.read_csv(summary_path)
    expected_metrics = {"n_events", "fraction_events_external_unlock",
                        "mean_external_gain_person_equiv_per_event",
                        "mean_total_gain_person_equiv_per_event", "first_external_unlock_hr"}
    if (len(metric_summary) != len(POLICIES) * len(expected_metrics)
            or set(metric_summary.policy) != expected_policies
            or set(metric_summary.metric) != expected_metrics
            or metric_summary.duplicated(["policy", "metric"]).any()):
        raise ValueError("Event realization-summary checkpoint has missing/duplicate policy metrics")
    sample_record = json.loads(sample_path.read_text(encoding="utf-8"))
    expected_sample = np.random.default_rng(20261105).choice(np.arange(8, 1000), size=128, replace=False).tolist()
    if (sample_record.get("pilot_ids_excluded") != list(range(8))
            or sample_record.get("sample_seed") != 20261105
            or sample_record.get("main_sample_ids") != expected_sample):
        raise ValueError("Saved paired perturbation sample differs from registered design")
    btw_map = nx.betweenness_centrality(data["graph"], normalized=True, weight=None)
    degree = np.asarray([data["graph"].degree(str(s)) for s in data["station_ids"]], float)
    betweenness = np.asarray([btw_map[str(s)] for s in data["station_ids"]], float)
    return path, metric_summary, None, np.asarray(expected_sample, dtype=int), {}, degree, betweenness


def _save_figures(event_summary: pd.DataFrame, perturb_summary: pd.DataFrame, out: Path):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.titlesize": 10, "axes.labelsize": 9,
                         "legend.fontsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42})
    event = event_summary[event_summary.metric.isin(("fraction_events_external_unlock",
                                                     "mean_external_gain_person_equiv_per_event"))]
    policies = list(POLICIES)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.0), constrained_layout=True)
    for ax, metric, title, ylabel in (
            (axes[0], "fraction_events_external_unlock", "Repair batches with external source unlock", "Fraction of completion batches"),
            (axes[1], "mean_external_gain_person_equiv_per_event", "Mean external modeled-service gain", "Population-equivalent availability units")):
        d = event[event.metric == metric].set_index("policy").reindex(policies)
        x = np.arange(len(policies))
        mean = d["mean"].to_numpy(float)
        low = d["bootstrap_95ci_low"].to_numpy(float)
        high = d["bootstrap_95ci_high"].to_numpy(float)
        ax.errorbar(x, mean, yerr=np.vstack([mean-low, high-mean]), fmt="o", capsize=3,
                    color="#277f8e", ecolor="#64747c", markersize=4)
        ax.set_xticks(x, policies, rotation=45, ha="right")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color="#dddddd", linewidth=.6)
    fig.suptitle("AUTHOR REVIEW — NOT A PHYSICAL POWER-FLOW OR CUSTOMER-OUTAGE MODEL", fontsize=10)
    fig.savefig(out / "FIG_MECHANISM_UNLOCK.pdf", bbox_inches="tight",
                metadata={"Title": "Frozen repair completion source-unlock events", "CreationDate": None})
    fig.savefig(out / "FIG_MECHANISM_UNLOCK.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    d = perturb_summary[(perturb_summary.travel_condition == "production_directed_travel")].copy()
    d["group"] = d.baseline_policy + " | " + d.target_category
    labels = list(dict.fromkeys(d.group.tolist()))
    fig, ax = plt.subplots(figsize=(10.2, 5.0), constrained_layout=True)
    colors = {1: "#398b91", 3: "#6477a5", 5: "#9a7494"}
    positions = np.arange(len(labels))
    for shift in (1, 3, 5):
        q = d[d.requested_positions_earlier == shift].set_index("group").reindex(labels)
        x = positions + ({1: -.18, 3: 0, 5: .18}[shift])
        mean = q.mean_delta_total_burden_hr.to_numpy(float)
        lo = q.paired_bootstrap_95ci_low_hr.to_numpy(float)
        hi = q.paired_bootstrap_95ci_high_hr.to_numpy(float)
        ax.errorbar(x, mean, yerr=np.vstack([mean-lo, hi-mean]), fmt="o", capsize=2.5,
                    color=colors[shift], label=f"Move earlier {shift} positions", markersize=4)
    ax.axhline(0, color="#333333", linewidth=.8)
    ax.set_xticks(positions, labels, rotation=55, ha="right")
    ax.set_ylabel("Paired change in total deficit (h); below zero is lower burden")
    ax.set_title("Local priority perturbations: same frozen DS/duration realization")
    ax.grid(axis="y", color="#dddddd", linewidth=.6)
    ax.legend(frameon=False, ncol=3, loc="upper right")
    fig.suptitle("AUTHOR REVIEW — EXACT DECODER; LOCAL COUNTERFACTUAL, NOT A FORMAL STRATEGY", fontsize=10)
    fig.savefig(out / "FIG_MARGINAL_REPAIR_BENEFIT.pdf", bbox_inches="tight",
                metadata={"Title": "Paired local repair-priority perturbations", "CreationDate": None})
    fig.savefig(out / "FIG_MARGINAL_REPAIR_BENEFIT.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _effect_tables(summary: pd.DataFrame, paired: pd.DataFrame, out: Path):
    # Main paired differences, using shared realization IDs and component-wise 95% bootstrap.
    paired.to_csv(out / "PAIRED_COMPONENT_EFFECTS.csv", index=False)
    keep = summary[(summary.hazard == "2pc50") & (summary.resource_scenario == "C57_D1")
                  & (summary.mapping == "M1_UTILITY_003") & (summary.comparison_domain == "mapping_native_domain")].copy()
    # Frozen accounting-control comparisons, not newly simulated trajectories.
    control_rows = []
    strategies = [x for x in sorted(set(keep.strategy_id)) if x != "direct-community"]
    for gate in ("G0_NO_GATE", "G1_BASELINE_050", "G2_RELAXED_005", "G3_STRICT_075"):
        g = keep[keep.gate == gate]
        for strategy in strategies:
            x = g[g.strategy_id == strategy]
            if len(x) == 0:
                continue
            for c in COMPONENTS:
                col = SUMMARY_COL[c]
                control_rows.append({"gate": gate, "strategy": strategy, "component": c,
                                     "n": x.realization_id.nunique(), "mean_hr": float(x[col].mean()),
                                     "median_hr": float(x[col].median())})
    pd.DataFrame(control_rows).to_csv(out / "FROZEN_GATE_SENSITIVITY.csv", index=False)

    # Resource and hazard context summaries are derived only from saved per-realization outputs.
    context = summary[(summary.mapping == "M1_UTILITY_003")
                      & (summary.gate == "G1_BASELINE_050")
                      & (summary.comparison_domain == "mapping_native_domain")].copy()
    rows = []
    for (hazard, resource, strategy), g in context.groupby(["hazard", "resource_scenario", "strategy_id"]):
        for c in COMPONENTS:
            col = SUMMARY_COL[c]
            rows.append({"hazard": hazard, "resource": resource, "strategy": strategy,
                         "component": c, "n": g.realization_id.nunique(),
                         "mean_hr": float(g[col].mean()), "median_hr": float(g[col].median()),
                         "p05_hr": float(g[col].quantile(.05)), "p95_hr": float(g[col].quantile(.95))})
    pd.DataFrame(rows).to_csv(out / "RESOURCE_AND_HAZARD_CONTEXT.csv", index=False)

    if (out / ".cache" / "source_loss_station.csv").is_file() and (out / ".cache" / "source_loss_tract.csv").is_file():
        station = pd.read_csv(out / ".cache" / "source_loss_station.csv")
        tract = pd.read_csv(out / ".cache" / "source_loss_tract.csv")
        st = station[(station.hazard == "2pc50") & (station.resource_scenario == "C57_D1")]
        tr = tract[(tract.hazard == "2pc50") & (tract.resource_scenario == "C57_D1")]
        attribution = []
        for policy in sorted(set(st.strategy_id) & set(tr.strategy_id)):
            s = st[st.strategy_id == policy].sort_values("mean_population_weighted_source_loss_hr", ascending=False)
            t = tr[tr.strategy_id == policy].copy()
            loss = (t.population * t.mean_source_loss_hr).clip(lower=0)
            ranked = loss.sort_values(ascending=False)
            total = float(loss.sum())
            attribution.append({"policy": policy, "aggregate_source_loss_hr": total,
                                "station_top1_share": float(s.head(1).mean_population_weighted_source_loss_hr.sum() / s.mean_population_weighted_source_loss_hr.sum()),
                                "station_top5_share": float(s.head(5).mean_population_weighted_source_loss_hr.sum() / s.mean_population_weighted_source_loss_hr.sum()),
                                "tract_top1_share_population_weighted": float(ranked.head(1).sum() / total) if total else 0,
                                "tract_top10_share_population_weighted": float(ranked.head(10).sum() / total) if total else 0,
                                "tract_top100_share_population_weighted": float(ranked.head(100).sum() / total) if total else 0,
                                "tracts_with_positive_mean_source_loss": int((t.mean_source_loss_hr > 0).sum()),
                                "stations_with_positive_mean_source_loss": int((s.mean_station_source_loss_integral_hr > 0).sum())})
        pd.DataFrame(attribution).to_csv(out / "SOURCE_LOSS_ATTRIBUTION_CONCENTRATION.csv", index=False)


def _make_registry(data, summary_path: Path, schedule_manifest: pd.DataFrame, out: Path):
    paths = [PHYSICAL_NPZ, PHYSICAL_MANIFEST, PHYSICAL_IDENTITY, MAPPING_PATH, GRAPH_PATH,
             SOURCE_PATH, CREW_PATH, BASE_TRAVEL, TASK_TRAVEL, RULE_SEQUENCE_PATH,
             VULN_SEQUENCE_PATH, VULN_SUMMARY_PATH, summary_path, OFFLINE_INDEX_PATH,
             QA03_PATH, QA04_PATH,
             ROOT / "src" / "la_grid" / "revision" / "formal" / "schedule.py",
             ROOT / "src" / "la_grid" / "revision" / "r1_source_gate.py",
             ROOT / "src" / "la_grid" / "revision" / "r1_realization_scheduling.py",
             ROOT / "src" / "la_grid" / "revision" / "formal" / "offline.py"]
    registry = {p.relative_to(ROOT).as_posix(): {"sha256": sha256(p), "size_bytes": p.stat().st_size}
                for p in paths if p.exists() and p != summary_path}
    registry["external_formal_summary_dependency"] = {
        "archive_path": "Formal_Experiment_20260923/Formal_Offline_Evaluation/FORMAL_REALIZATION_STRATEGY_SUMMARY.parquet",
        "local_materialized_path": summary_path.relative_to(ROOT).as_posix(),
        "sha256": sha256(summary_path), "size_bytes": summary_path.stat().st_size,
        "included_in_branch": False,
        "reason": "Frozen Git LFS source is required locally; do not duplicate the 52 MB source payload in this diagnostic package.",
    }
    registry["schedule_archives"] = schedule_manifest.to_dict("records")
    registry["frozen_identity"] = {
        "branch_baseline": "7704f766a648f6631acc474a8b02eb6e357adbc2",
        "matrix_id": "JULY92_REVIEWER_REVISION_FINAL_V1", "hazard": "2pc50",
        "resource": "C57_D1", "mapping": "M1_UTILITY_003", "source_gate": "G1_BASELINE_050",
        "horizon_hr": 480, "realizations": 1000, "stations": 92, "edges": 318,
        "sources": 14, "tracts": 2315, "population": data["total_population"],
        "physical_hashes_verified": 1000,
    }
    registry["issue_authority"] = {
        "issue": "https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/issues/4",
        "detailed_instructions_path": "docs/research/CONTRIBUTION1_REPAIR_SEQUENCING_MECHANISM_TEST_20261105.md",
        "detailed_instructions_blob_sha": "13795e3c4c715e1f5e5cb70b9d995c4f19e5a1f5",
    }
    (out / "FROZEN_INPUT_REGISTRY.json").write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(args):
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    summary_path = Path(args.summary).resolve()
    print("Loading and hashing frozen inputs...", flush=True)
    data = _load_sources(summary_path)
    single_state_checks = verify_single_state_gate_equivalence(data)
    primary = _summary_rows(data)
    effects = make_paired_effects(primary)
    reference_qa = reproduce_reference_checks(primary)
    sequences, origins, decoder, origins_idx, zero_decoder, zero_origins_idx = _load_sequences_and_decoder(data)
    schedule_manifest = _verify_schedule_archives(data, sequences)
    decoder_checks = verify_decoder_samples(data, sequences, decoder, origins_idx)
    print("Frozen identities and decoder spot checks passed; reconstructing event histories...", flush=True)

    means = (primary.groupby("strategy_id")[[SUMMARY_COL[c] for c in COMPONENTS]
             ].mean().rename(columns={v: k for k, v in SUMMARY_COL.items()}).reset_index())
    means.to_csv(out / "COMPONENT_MEANS_BY_POLICY.csv", index=False)
    decoder_checks.to_csv(out / "DECODER_REPRODUCTION_CHECKS.csv", index=False)
    schedule_manifest.to_csv(out / "FROZEN_SCHEDULE_IDENTITY.csv", index=False)
    (out / "REFERENCE_QA.json").write_text(json.dumps(reference_qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _effect_tables(data["summary"], effects, out)
    pd.DataFrame(single_state_checks).to_csv(out / "SINGLE_STATE_GATE_EQUIVALENCE.csv", index=False)

    schedules = {p: np.load(_filesystem_path(SCHEDULES / f"2pc50__C57_D1__{p}.npz"), allow_pickle=False)
                 for p in POLICIES}
    if args.reuse_event_history:
        event_path, event_summary, event_err, sample_ids, sample_events, degree, betweenness = _load_validated_event_checkpoint(
            data, schedules, out)
        print("Reused completed event checkpoint after verifying every frozen event key...", flush=True)
    else:
        event_path, event_summary, event_err, sample_ids, sample_events, degree, betweenness = _write_event_outputs(
            data, schedules, out)
    data["degree"] = degree
    data["betweenness"] = betweenness
    print("Event histories reproduce archived burdens; running paired priority perturbations...", flush=True)
    event_summary.to_csv(out / "EVENT_UNLOCK_REALIZATION_SUMMARY.csv", index=False)
    damage_state_summary = write_event_damage_state_summary(event_path, out)
    event_examples = save_event_unlock_examples(event_path, data, schedules, out)
    (out / "PERTURBATION_SAMPLE_IDS.json").write_text(json.dumps({
        "pilot_ids_excluded": list(range(8)), "main_sample_ids": list(map(int, sample_ids)),
        "sample_seed": 20261105, "sample_n": len(sample_ids),
    }, indent=2) + "\n", encoding="utf-8")

    perturb, pilot = run_perturbations(data, sequences, decoder, origins_idx, zero_decoder,
                                       zero_origins_idx, schedules, sample_ids)
    perturb.to_csv(out / "LOCAL_PRIORITY_PERTURBATIONS.csv", index=False)
    pilot.to_csv(out / "DECODER_SMOKE_PILOT.csv", index=False)
    perturb_summary = summarize_perturbations(perturb)
    perturb_summary.to_csv(out / "LOCAL_PRIORITY_PERTURBATION_SUMMARY.csv", index=False)
    _save_figures(event_summary, perturb_summary, out)
    print("Writing source registry and numerical QA...", flush=True)

    # Complete hash registry after all inputs and derived data are available.
    _make_registry(data, summary_path, schedule_manifest, out)
    qa = {
        "status": "PASS" if (event_err is None or event_err < 1e-10) and reference_qa["max_integrated_additivity_error_hr"] < 1e-10 else "FAIL",
        "primary_rows": len(primary), "realization_count_per_policy": 1000,
        "policies_in_primary_comparison": sorted(primary.strategy_id.unique().tolist()),
        "direct_community_excluded_as_duplicate": True,
        "physical_hashes_verified": 1000,
        "decoder_exact_checks": int(decoder_checks.exact_match.sum()),
        "decoder_check_count": len(decoder_checks),
        "single_state_gate_equivalence_checks": len(single_state_checks),
        "max_reconstructed_vs_archived_burden_difference_hr": event_err,
        "reconstructed_vs_archived_burden_tolerance_hr": 1e-10,
        "event_history_reconstruction_status": "fresh exact-event reconstruction passed <1e-10 h" if event_err is not None else "completed in immediately preceding run; checkpoint keys independently revalidated",
        "max_integrated_additivity_error_hr": reference_qa["max_integrated_additivity_error_hr"],
        "event_rows_path": event_path.name,
        "event_rows_compressed": True,
        "event_row_count": int(sum(1 for _ in gzip.open(event_path, "rt", encoding="utf-8")) - 1),
        "event_damage_state_summary_groups": len(damage_state_summary),
        "event_damage_state_bootstrap_replicates": 10000,
        "verified_event_illustrations": len(event_examples),
        "counterfactual_sample_n": int(len(sample_ids)),
        "counterfactual_rows": len(perturb),
        "counterfactual_effect_threshold": "No binary threshold; report paired estimates and realization-bootstrap intervals",
        "vulnerability_first_event_timing": "Not included; only its separately frozen realization-level results are used because an event-level prepass archive is absent",
        "ga_candidate": "Not included unless a matching frozen paired trajectory source is verified",
        "formal_simulation_or_optimizer_rerun": False,
    }
    (out / "NUMERICAL_QA.json").write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return qa


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default=str(FORMAL / "Formal_Offline_Evaluation" / "FORMAL_REALIZATION_STRATEGY_SUMMARY.parquet"),
                        help="Exact frozen realization-level summary; requires materialized Git LFS payload")
    parser.add_argument("--output", default=str(OUT), help="Derived output directory")
    parser.add_argument("--reuse-event-history", action="store_true",
                        help="Reuse a completed full-cohort event pass after validating all frozen event identities")
    args = parser.parse_args()
    qa = run(args)
    print(json.dumps(qa, indent=2, sort_keys=True))
    if qa["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
