"""Execute only the frozen vulnerability-first amendment on retained samples.

Uses the existing formal decoder, completion-event state evaluator, source
gate, archive and offline metric evaluator. Existing trajectories are read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import networkx as nx
import numpy as np
import pandas as pd

from C257H_Project_Main import load_stage45_C57_depot_inputs, _scale_sensitivity_crew_origins
from r1_formal_archive import inspect_formal_archive, retain_formal_trajectory, sha256_file
from r1_formal_schedule import FormalScheduleDecoder
from r1_realization_scheduling import INITIAL_BY_DS, evaluate_completion_step_functionality
from r1_source_gate import evaluate_source_gate


ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "Formal_Experiment_20260923"
AMEND = FORMAL / "Equity_Amendment"
STRATEGY = "vulnerability-first"
HAZARDS = ("Northridge", "SanFernando", "LongBeach", "2pc50")
EVENT_COLUMNS = ("dispatch_rank", "task_id", "damage_state", "crew_index", "crew_origin_id",
                 "previous_task_id", "crew_available_before_hr", "travel_hr", "arrival_hr",
                 "realized_duration_hr", "completion_hr")
CASES = (("C57_D1", 1.0, 1.0), ("C29_D1", .5, 1.0),
         ("C86_D1", 1.5, 1.0), ("C114_D1", 2.0, 1.0),
         ("C57_D075", 1.0, .75), ("C57_D125", 1.0, 1.25),
         ("C57_D150", 1.0, 1.5))


def frozen_inputs():
    amendment = json.loads((AMEND / "EQUITY_POLICY_AMENDMENT.json").read_text(encoding="utf-8"))
    sequence = json.loads((AMEND / "VULNERABILITY_FIRST_SEQUENCE.json").read_text(encoding="utf-8"))
    if amendment["status"] != "FROZEN_BEFORE_EQUITY_POLICY_EXECUTION" or sequence["status"] != amendment["status"]:
        raise ValueError("Equity amendment was not frozen before execution")
    if sequence["amendment_sha256"] != sha256_file(AMEND / "EQUITY_POLICY_AMENDMENT.json"):
        raise ValueError("Sequence was not derived from the frozen amendment")
    if amendment["parent_matrix_sha256"] != sha256_file(ROOT / "FINAL_EXPERIMENT_MATRIX.json"):
        raise ValueError("Frozen final matrix changed")
    file_map = {
        "fixed_formal_tract_metadata": ROOT / "R1_Comment1_July92_Utility_Constraint" / "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
        "production_M1_mapping": ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv",
        "formal_physical_manifest": FORMAL / "Stage 1 Output_expanded" / "PHYSICAL_INPUTS_FROZEN.json",
        "formal_evaluation_horizon": FORMAL / "Formal_Schedule_Prepass" / "EVALUATION_HORIZON.json",
        "frozen_direct_community_sequence": FORMAL / "Stage 5 Output_expanded" / "FINAL_DIRECT_COMMUNITY_SEQUENCE.json",
    }
    for label, path in file_map.items():
        if sha256_file(path) != amendment["input_sha256"][label]:
            raise ValueError(f"Frozen amendment input changed: {label}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if sequence["executable_code_commit_sha"] != commit:
        raise ValueError("Equity sequence executable commit differs from current HEAD")
    physical = json.loads(file_map["formal_physical_manifest"].read_text(encoding="utf-8"))
    horizon = json.loads(file_map["formal_evaluation_horizon"].read_text(encoding="utf-8"))
    original = json.loads((FORMAL / "FORMAL_TRAJECTORY_ARCHIVE_INDEX.json").read_text(encoding="utf-8"))
    if (physical["evaluation_count"] != 4000 or physical["planning_count"] != 64 or
            horizon["H_eval_hr"] != 480 or original["trajectory_count"] != 84000):
        raise ValueError("Formal archive/sample dimensions or horizon changed")
    return amendment, sequence, physical, original


def execution_context(ids):
    edge_file = ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv"
    source_file = ROOT / "Data" / "source_nodes_core_expanded.csv"
    base_file = ROOT / "Stage 4 Output_expanded" / "travel_base_to_task.csv"
    task_file = ROOT / "Stage 4 Output_expanded" / "travel_task_to_task.csv"
    depot_file = ROOT / "Data" / "stage45_depot_inputs_final_origin_proxy.csv"
    edges = pd.read_csv(edge_file, dtype={"u": str, "v": str})
    graph = nx.from_pandas_edgelist(edges, "u", "v")
    source_data = pd.read_csv(source_file, dtype={"ID": str})
    sources = set(source_data.loc[source_data.level.eq("Core"), "ID"])
    if len(graph) != 92 or graph.number_of_edges() != 318 or set(graph) != set(ids) or len(sources) != 14:
        raise ValueError("July92/318/14 topology or source identity changed")
    depot = load_stage45_C57_depot_inputs(ROOT / "Data", str(depot_file))
    origins = depot["expanded_crew_origins_df"].travel_matrix_origin_key.astype(str).tolist()
    if len(origins) != 57:
        raise ValueError("Frozen C57 roster changed")
    base = pd.read_csv(base_file, index_col=0)
    task = pd.read_csv(task_file, index_col=0)
    for frame in (base, task):
        frame.index = frame.index.astype(str)
        frame.columns = frame.columns.astype(str)
    context = dict(ids=ids, base=base, task=task, origins=origins, graph=graph, sources=sources)
    decoder = FormalScheduleDecoder(context)
    graph_edges = [tuple(sorted((str(a), str(b)))) for a, b in graph.edges()]
    graph_hash = hashlib.sha256(("\n".join("|".join(x) for x in sorted(graph_edges)) + "\n").encode()).hexdigest()
    source_hash = hashlib.sha256(("\n".join(sorted(sources)) + "\n").encode()).hexdigest()
    travel_hash = hashlib.sha256((sha256_file(base_file) + "|" + sha256_file(task_file)).encode()).hexdigest()
    expected = json.loads((FORMAL / "FORMAL_TRAJECTORY_ARCHIVE_INDEX.json").read_text(encoding="utf-8"))["common_identity"]
    if (graph_hash != expected["graph_hash"] or source_hash != expected["source_set_hash"] or
            travel_hash != expected["directed_travel_hash"]):
        raise ValueError("Amendment graph/source/directed travel differs from original formal trajectory")
    return context, decoder, dict(graph_hash=graph_hash, source_set_hash=source_hash,
                                  directed_travel_hash=travel_hash)


def run():
    amendment, sequence, physical, original = frozen_inputs()
    physical_folder = FORMAL / "Stage 1 Output_expanded"
    with np.load(physical_folder / "physical_inputs_2pc50.npz", allow_pickle=False) as z:
        ids = z["station_ids"].astype(str).tolist()
    if len(ids) != 92 or len(set(ids)) != 92 or set(sequence["ordered_station_ids"]) != set(ids):
        raise ValueError("Frozen vulnerability sequence does not match July92")
    context, decoder, hashes = execution_context(ids)
    order = decoder.order(sequence["ordered_station_ids"])
    output = AMEND / "Trajectories"
    summary_rows = []
    counts = {"written": 0, "reused": 0}
    for hazard in HAZARDS:
        physical_path = physical_folder / f"physical_inputs_{hazard}.npz"
        if sha256_file(physical_path) != physical["files_sha256"][hazard]:
            raise ValueError("Frozen physical sample file changed")
        with np.load(physical_path, allow_pickle=False) as z:
            if not np.array_equal(z["station_ids"].astype(str), ids):
                raise ValueError("Physical station order differs")
            DS = z["evaluation_ds"].copy()
            duration_base = z["evaluation_duration"].copy()
        if DS.shape != (92, 1000) or duration_base.shape != (92, 1000):
            raise ValueError("Formal evaluation physical sample dimensions differ")
        for case, crew_scale, duration_scale in (CASES if hazard == "2pc50" else CASES[:1]):
            origins = (context["origins"] if crew_scale == 1 else
                       _scale_sensitivity_crew_origins(context["origins"], crew_scale))
            required_count = {"C57_D1": 57, "C29_D1": 29, "C86_D1": 86, "C114_D1": 114,
                              "C57_D075": 57, "C57_D125": 57, "C57_D150": 57}[case]
            if len(origins) != required_count:
                raise ValueError("Frozen OFAT roster size differs")
            roster_hash = hashlib.sha256(("\n".join(origins) + "\n").encode()).hexdigest()
            prior_schedule = json.loads((FORMAL / "Formal_Schedule_Prepass" /
                                         f"{hazard}__{case}__hospital-first.json").read_text(encoding="utf-8"))
            if roster_hash != prior_schedule["identity"]["crew_roster_sha256"]:
                raise ValueError("Amendment crew roster differs from retained formal roster")
            crew_keys = decoder.origins(origins)
            folder = output / hazard / case / STRATEGY
            for sample in range(1000):
                stem = f"{hazard}__evaluation_{sample:04d}"
                ds = DS[:, sample].astype("<i8", copy=False)
                duration = (duration_base[:, sample] * duration_scale).astype("<f8", copy=False)
                sample_hash = hashlib.sha256(("\n".join(ids) + "\n").encode() +
                                              ds.tobytes() + duration_base[:, sample].astype("<f8").tobytes()).hexdigest()
                if sample_hash != physical["sample_hashes"][stem]:
                    raise ValueError("Amendment sample is not the frozen evaluation physical realization")
                identity = dict(matrix_id=amendment["parent_matrix_id"],
                                amendment_id=amendment["amendment_id"],
                                amendment_sha256=sha256_file(AMEND / "EQUITY_POLICY_AMENDMENT.json"),
                                sequence_sha256=sequence["station_sequence_sha256"],
                                executable_code_commit_sha=sequence["executable_code_commit_sha"],
                                hazard=hazard, realization_id=stem, split="evaluation", strategy=STRATEGY,
                                resource_scenario=case,
                                DS_hash=hashlib.sha256(ds.tobytes()).hexdigest(),
                                duration_hash=hashlib.sha256(duration.tobytes()).hexdigest(),
                                physical_sample_hash=sample_hash, graph_hash=hashes["graph_hash"],
                                source_set_hash=hashes["source_set_hash"], mapping_method_id="M1_UTILITY_003",
                                crew_roster_hash=roster_hash,
                                directed_travel_hash=hashes["directed_travel_hash"],
                                event_horizon_hr=480.0)
                existing = inspect_formal_archive(folder, identity=identity, stem=stem)
                if existing is not None:
                    counts["reused"] += 1
                    events = pd.read_csv(folder / f"{stem}__TASK_EVENTS.csv", dtype={"task_id": str})
                    makespan = float(events.completion_hr.max()) if len(events) else 0.0
                    travel_total = float(events.travel_hr.sum()) if len(events) else 0.0
                else:
                    completion, arrival, travel, crew, previous, dispatch, _ = decoder.decode(
                        order=order, damage=ds, duration=duration, origins=crew_keys)
                    completed = completion[np.isfinite(completion)]
                    if completed.size and completed.max() > 480:
                        raise ValueError("Amendment task completion exceeds frozen common horizon")
                    event_times = np.unique(np.r_[0.0, completed, 480.0])
                    raw = evaluate_completion_step_functionality(
                        damage_state=pd.Series(ds, index=ids),
                        completion_time_hr=pd.Series(completion, index=ids), time_hr=event_times,
                        initial_functionality_by_ds=INITIAL_BY_DS)
                    trace = evaluate_source_gate(raw, context["graph"], context["sources"], threshold=.5)
                    rows = []
                    for j in np.argsort(dispatch):
                        if dispatch[j] < 0:
                            continue
                        rows.append(dict(dispatch_rank=int(dispatch[j])+1, task_id=ids[j],
                                         damage_state=int(ds[j]), crew_index=int(crew[j]),
                                         crew_origin_id=origins[int(crew[j])],
                                         previous_task_id=(ids[int(previous[j])] if previous[j]>=0 else None),
                                         crew_available_before_hr=float(arrival[j]-travel[j]),
                                         travel_hr=float(travel[j]), arrival_hr=float(arrival[j]),
                                         realized_duration_hr=float(duration[j]),
                                         completion_hr=float(completion[j])))
                    events = pd.DataFrame(rows, columns=EVENT_COLUMNS)
                    if len(rows) != int(np.count_nonzero(ds)):
                        raise ValueError("Amendment task set differs from DS>0")
                    action = retain_formal_trajectory(folder, trace=trace, task_events=events,
                                                      identity=identity, stem=stem)
                    counts[action] += 1
                    makespan = float(completed.max()) if completed.size else 0.0
                    travel_total = float(np.nansum(travel))
                summary_rows.append(dict(hazard=hazard, realization_id=stem,
                                         resource_scenario=case, strategy_id=STRATEGY,
                                         physical_sample_hash=sample_hash, DS_hash=identity["DS_hash"],
                                         duration_hash=identity["duration_hash"],
                                         task_count=int(np.count_nonzero(ds)),
                                         makespan_hr=makespan, total_travel_hr=travel_total))
            print(json.dumps({"hazard": hazard, "resource": case, **counts}), flush=True)
    if sum(counts.values()) != 10000 or len(summary_rows) != 10000:
        raise ValueError("Amendment trajectory count differs from 10000")
    index_path = AMEND / "VULNERABILITY_TRAJECTORY_INDEX.json"
    summary_path = AMEND / "VULNERABILITY_LOGISTICS.csv"
    if index_path.exists() or summary_path.exists():
        raise ValueError("Amendment compact output already exists; inspect before rerun")
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)
    index = dict(status="FORMAL_EQUITY_AMENDMENT_V1", amendment_id=amendment["amendment_id"],
                 sequence_sha256=sequence["station_sequence_sha256"],
                 executable_code_commit_sha=sequence["executable_code_commit_sha"],
                 trajectory_count=10000, physical_evaluation_count=4000,
                 written=counts["written"], reused=counts["reused"],
                 logistics_sha256=sha256_file(summary_path))
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.run:
        print(json.dumps(run(), indent=2), flush=True)


if __name__ == "__main__":
    main()
