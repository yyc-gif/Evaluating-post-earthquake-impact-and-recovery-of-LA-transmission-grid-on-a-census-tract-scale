"""One-realization execution kernel for the revised R1 / Architecture B model.

The reusable ``run_revised_realization`` function accepts complete authoritative
inputs.  It does not sample damage or duration, calculate priority, rebuild the
network, generate travel, or fill missing data.  The command-line entry point
constructs the explicitly labeled Round 25 deterministic integration fixture and
executes it once.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
from statistics import NormalDist
import sys
from types import SimpleNamespace
from typing import Callable, Mapping, Sequence

import networkx as nx
import numpy as np
import pandas as pd


SCENARIO_ID = "R25_TEST_ONLY_DETERMINISTIC_REALIZATION"
STRATEGY_ID = "HOSPITAL_FIRST_FROZEN_R23"
REALIZATION_ID = "r25_test_000000"
SOURCE_TIME_UNIT = "hours_since_event"
FUNCTIONAL_THRESHOLD = 0.5
N_TEST_TASKS = 80
UNRESOLVED_IDS = ("301479", "303265", "304137", "305021")
IDENTIFIED_SOURCELESS_IDS = ("306980", "309598")
OUTSIDE_COMPONENT2_IDS = ("303547", "307683")
REFERENCE_SOURCE_IDS = (
    "300232", "301318", "302376", "302865", "303473", "303547",
    "306001", "306365", "306450", "306473", "306489", "307039",
    "307373", "307512", "307693", "308540", "308581", "309553",
    "309569", "309703", "310199",
)
INITIAL_FUNCTIONALITY_BY_DS = {0: 1.0, 1: 0.5, 2: 0.09, 3: 0.04, 4: 0.03}
DURATION_PARAMETERS = {1: (1.0, 0.5), 2: (6.0, 3.0), 3: (12.0, 4.0), 4: (36.0, 12.0)}


@dataclass(frozen=True)
class R1RevisedRealizationResult:
    schedule: object
    event_times_hr: np.ndarray
    raw_functionality: pd.DataFrame
    effective_network_state: pd.DataFrame
    state_identified: pd.DataFrame
    exported_trajectory: pd.DataFrame
    service_evaluation: object


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def newline_hash(values: Sequence[object]) -> str:
    return hashlib.sha256(("\n".join(map(str, values)) + "\n").encode()).hexdigest()


def indexed_numeric_hash(series: pd.Series) -> str:
    lines = [f"{index},{float(value):.17g}" for index, value in series.items()]
    return newline_hash(lines)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    module_dir = str(path.resolve().parent)
    inserted = module_dir not in sys.path
    if inserted:
        sys.path.insert(0, module_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted:
            sys.path.remove(module_dir)
    return module


def _strict_string_ids(values: Sequence[object], name: str) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(type(value) is not str or not value or value != value.strip()
                         for value in result):
        raise ValueError(f"{name} must contain explicit nonempty string IDs")
    if len(result) != len(set(result)):
        raise ValueError(f"{name} contains duplicate IDs")
    return result


def deterministic_integration_fixture(
    domain_ids: Sequence[str],
) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    """Build the fixed hash-ranked test fixture; this is not a hazard draw."""

    domain = _strict_string_ids(domain_ids, "domain_ids")
    ranked = sorted(
        ((hashlib.sha256(f"R25_INTEGRATION|{station_id}".encode()).hexdigest(), station_id)
         for station_id in domain),
        key=lambda item: (item[0], item[1]),
    )
    selected = ranked[:N_TEST_TASKS]
    damage = pd.Series(0, index=pd.Index(domain, name="R1_station_id"), dtype=np.int8,
                       name="damage_state")
    duration = pd.Series(0.0, index=damage.index, dtype=float,
                         name="realized_duration_hr")
    records = []
    denominator = float(1 << 256)
    for position, (selection_hash, station_id) in enumerate(selected):
        damage_state = position % 4 + 1
        duration_hash = hashlib.sha256(f"R25_DURATION|{station_id}".encode()).hexdigest()
        integer = int(duration_hash, 16)
        u = (integer + 0.5) / denominator
        mu, sigma = DURATION_PARAMETERS[damage_state]
        distribution = NormalDist(mu, sigma)
        lower_cdf = distribution.cdf(0.0)
        probability = lower_cdf + u * (1.0 - lower_cdf)
        value = distribution.inv_cdf(probability)
        if not np.isfinite(value) or value <= 0.0:
            raise RuntimeError(f"Deterministic positive-conditioned duration failed for {station_id}")
        damage.loc[station_id] = damage_state
        duration.loc[station_id] = value
        records.append({
            "selection_rank": position + 1,
            "R1_station_id": station_id,
            "selection_hash_sha256": selection_hash,
            "damage_state": damage_state,
            "duration_hash_sha256": duration_hash,
            "duration_u_open01": u,
            "realized_duration_hr": value,
        })
    if (damage > 0).sum() != N_TEST_TASKS:
        raise RuntimeError("Fixture does not contain exactly 80 tasks")
    if damage.value_counts().to_dict() != {0: 222, 1: 20, 2: 20, 3: 20, 4: 20}:
        raise RuntimeError("Fixture damage-state counts violate the mechanical assignment")
    if not (duration[damage > 0] > 0).all() or not (duration[damage == 0] == 0).all():
        raise RuntimeError("Fixture duration contract failed")
    return damage, duration, pd.DataFrame(records)


def evaluate_raw_functionality_events(
    *,
    full_r1_ids: Sequence[str],
    scheduling_domain_ids: Sequence[str],
    damage_states: pd.Series,
    task_completion_hr: pd.Series,
    state_identified_static: pd.Series,
    requested_event_horizon: str | float,
    initial_functionality_by_ds: Mapping[int, float],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create event-step raw state and an authoritative static mask.

    D302 tasks retain their DS residual before completion and become 1 at and
    after completion.  Identified records outside D302 remain fixed at raw=1;
    unidentified records use inert numeric zero with a false semantic mask.
    """

    full_ids = _strict_string_ids(full_r1_ids, "full_r1_ids")
    domain = _strict_string_ids(scheduling_domain_ids, "scheduling_domain_ids")
    if not set(domain).issubset(full_ids):
        raise ValueError("Scheduling domain is not a subset of full R1 IDs")
    damage = damage_states.copy().reindex(domain)
    completion = task_completion_hr.copy().reindex(domain)
    if damage.isna().any():
        raise ValueError("Damage-state domain mismatch")
    mask = state_identified_static.copy()
    mask.index = mask.index.astype(str)
    mask = mask.reindex(full_ids)
    if mask.isna().any() or mask.dtype != bool:
        raise ValueError("Authoritative state-identification mask is incomplete or non-Boolean")

    task_completions = completion[damage > 0]
    if task_completions.isna().any() or not np.isfinite(task_completions).all():
        raise ValueError("Every damaged task must have a finite completion time")
    unique_completions = sorted(set(float(value) for value in task_completions))
    if requested_event_horizon == "max_completion":
        horizon = max(unique_completions) if unique_completions else 0.0
    else:
        horizon = float(requested_event_horizon)
        if not np.isfinite(horizon) or horizon < 0.0:
            raise ValueError("Requested event horizon must be finite and nonnegative")
        if unique_completions and horizon < max(unique_completions):
            raise ValueError("Requested horizon ends before the last completion")
    event_times = sorted(set([0.0, *unique_completions, horizon]))

    raw = pd.DataFrame(1.0, index=pd.Index(event_times, name="source_time"),
                       columns=full_ids, dtype=float)
    raw.loc[:, ~mask.to_numpy()] = 0.0
    for station_id in domain:
        ds = int(damage.loc[station_id])
        if ds not in initial_functionality_by_ds:
            raise ValueError(f"No initial functionality is defined for DS{ds}")
        residual = float(initial_functionality_by_ds[ds])
        if ds == 0:
            raw.loc[:, station_id] = 1.0
        else:
            finish = float(completion.loc[station_id])
            raw.loc[raw.index < finish, station_id] = residual
            raw.loc[raw.index >= finish, station_id] = 1.0
    mask_frame = pd.DataFrame(
        np.broadcast_to(mask.to_numpy(dtype=bool), raw.shape).copy(),
        index=raw.index, columns=full_ids, dtype=bool,
    )
    return raw, mask_frame


def run_revised_realization(
    *,
    domain_ids: Sequence[str],
    full_priority_sequence: Sequence[str],
    damage_states: pd.Series,
    realized_duration_hr: pd.Series,
    base_to_task_hr: pd.DataFrame,
    task_to_task_hr: pd.DataFrame,
    crew_roster: pd.DataFrame,
    full_r1_ids: Sequence[str],
    state_identified_static: pd.Series,
    graph: nx.Graph,
    source_ids: set[str],
    requested_event_horizon: str | float,
    service_attachment_ledger: pd.DataFrame,
    w1: pd.DataFrame,
    tract_metadata: pd.DataFrame,
    service_ids: Sequence[str],
    scheduler_callable: Callable,
    source_gate_callable: Callable,
    exporter_callable: Callable,
    service_evaluator_callable: Callable,
    exporter_provenance: Mapping[str, object],
) -> R1RevisedRealizationResult:
    """Execute one authoritative revised realization end to end."""

    schedule = scheduler_callable(
        domain_ids=domain_ids,
        full_priority_sequence=full_priority_sequence,
        damage_states=damage_states,
        realized_duration_hr=realized_duration_hr,
        base_to_task_hr=base_to_task_hr,
        task_to_task_hr=task_to_task_hr,
        crew_roster=crew_roster,
    )
    raw, state_identified = evaluate_raw_functionality_events(
        full_r1_ids=full_r1_ids,
        scheduling_domain_ids=domain_ids,
        damage_states=damage_states,
        task_completion_hr=schedule.task_completion_hr,
        state_identified_static=state_identified_static,
        requested_event_horizon=requested_event_horizon,
        initial_functionality_by_ds=INITIAL_FUNCTIONALITY_BY_DS,
    )
    gate_cfg = SimpleNamespace(SOURCE_GATE_ENABLED=True,
                               FUNCTIONAL_THRESHOLD=FUNCTIONAL_THRESHOLD)
    effective = source_gate_callable(
        raw, graph, gate_cfg, source_ids=source_ids, label="R25_TEST_ONLY_EVENT_GATE")
    export = exporter_callable(
        effective_state=effective,
        state_identified=state_identified,
        source_time=list(raw.index),
        source_time_unit=SOURCE_TIME_UNIT,
        frozen_r1_ids=full_r1_ids,
        provenance=exporter_provenance,
    )
    service_evaluation = service_evaluator_callable(
        trajectory=export.trajectory,
        service_attachment_ledger=service_attachment_ledger,
        w1=w1,
        tract_metadata=tract_metadata,
        expected_r1_ids=full_r1_ids,
        expected_service_ids=service_ids,
        expected_identified_mask=state_identified_static,
        tolerance=1e-12,
    )
    return R1RevisedRealizationResult(
        schedule=schedule,
        event_times_hr=raw.index.to_numpy(dtype=float),
        raw_functionality=raw,
        effective_network_state=effective,
        state_identified=state_identified,
        exported_trajectory=export.trajectory,
        service_evaluation=service_evaluation,
    )


def _expand_c57_roster(roster_definition: pd.DataFrame) -> pd.DataFrame:
    rows = []
    definition = roster_definition.loc[
        roster_definition["crew_scenario"] == "C57_REFERENCE"
    ].sort_values("yard_id", kind="mergesort")
    for row in definition.itertuples():
        for _ in range(int(row.integer_crews)):
            index = len(rows)
            rows.append({"crew_index": index, "crew_id": f"C57_{index:03d}",
                         "origin_key": str(row.yard_id)})
    roster = pd.DataFrame(rows)
    if len(roster) != 57:
        raise RuntimeError("C57 expansion did not yield exactly 57 crews")
    return roster


def _pivot_tract_field(intervals: pd.DataFrame, field: str,
                       time_count: int, tract_ids: Sequence[str]) -> np.ndarray:
    pivot = intervals.pivot(index="time_index", columns="tract_id", values=field)
    return pivot.reindex(index=range(time_count), columns=tract_ids).to_numpy(dtype=float)


def main() -> None:
    root = Path("R:/")
    review = root / "Review_and_Revision" / "IJDRR-D-26-02276"
    output = review / "25_R1_One_Realization_Schedule_Integration_20260917"
    output.mkdir(parents=True, exist_ok=True)
    runner_path = Path(__file__).resolve()
    manifest_path = output / "ONE_REALIZATION_INPUT_MANIFEST.json"
    event_path = output / "ONE_REALIZATION_SCHEDULE_EVENTS.csv"
    evidence_path = output / "ONE_REALIZATION_END_TO_END_EVIDENCE.npz"
    report_path = output / "ONE_REALIZATION_SCHEDULE_INTEGRATION_REPORT.md"
    for path in (manifest_path, event_path, evidence_path, report_path):
        if path.exists():
            raise RuntimeError(f"Refusing to overwrite an existing Round 25 artifact: {path.name}")

    r5 = review / "05_R1_310_DryBuild_20260913"
    r6 = review / "06_R1_310_LocalClosure_20260914"
    r10 = review / "10_SCE_ServiceLayer_Architecture_20260914"
    r14 = review / "14_Production_Interface_Contract_20260914"
    r16 = review / "16_R1_Dynamic_Export_Contract_20260915"
    r23 = review / "23_R1_310_Scheduling_Input_Readiness_20260916"
    r24 = review / "24_R1_Event_Based_Scheduler_20260917"

    input_paths = {
        "main_model": root / "C257H_Project_Main.py",
        "graph_checkpoint": r6 / "R1_310_EDGES.csv",
        "station_qa": r5 / "R1_310_STATIONS_QA.csv",
        "task_domain": r23 / "R1_TASK_DOMAIN_AND_ELIGIBILITY.csv",
        "priority_components": r23 / "R1_ARCHB_PRIORITY_COMPONENTS.csv",
        "base_to_task": r23 / "R1_BASE_TO_TASK_TRAVEL_HR.csv",
        "task_to_task": r23 / "R1_TASK_TO_TASK_TRAVEL_HR.csv",
        "crew_rosters": r23 / "R1_CREW_SCENARIO_ROSTERS.csv",
        "scheduler": r24 / "r1_event_based_scheduler.py",
        "exporter": r16 / "r1_effective_state_exporter.py",
        "service_interface": r14 / "service_layer_interface.py",
        "service_nodes": r10 / "SCE_SERVICE_NODES_196.csv",
        "attachment_ledger": r10 / "SERVICE_UPSTREAM_ATTACHMENT_LEDGER.csv",
        "w1": r10 / "SCE_TRACT_SERVICE_W1.csv",
        "tract_metadata": r10 / "SERVICE_LAYER_COVERAGE_QA.csv",
    }
    input_hashes_before = {name: sha256_file(path) for name, path in input_paths.items()}
    expected_hashes = {
        "main_model": "90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145",
        "graph_checkpoint": "e2dd039ec40336ea800adc29aa6cf790ae3d89553c1491c149096b3be6377090",
        "task_domain": "bcd8f493078f51365e9e7a9cafd63d0ec3d5738f358f901f6a841a1d5276fa83",
        "priority_components": "53c7687c2ca7a4c87b1e5a53946fe67c7f5e05188f40003a3f1fe6371218a1f6",
        "base_to_task": "16177e57cd7e77ea2075e347318c3b7698937af6b0b7dc702f18b9da65662690",
        "task_to_task": "68c03537853bad92544f13688ade89247e135e829b989c71c96be2f8ef45a6de",
        "crew_rosters": "4940f0c15e56c884ae2f3fd7717cd93f12e2f37de2bb936a27a8b752df5f3f11",
        "scheduler": "8096fa7ad72d5f7a5cb9c6f186d65adef2ab8f7fc336938f0dba396ed31ee43f",
        "exporter": "79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b",
        "service_interface": "d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514",
        "attachment_ledger": "b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e",
        "w1": "a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221",
        "tract_metadata": "4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b",
    }
    for name, expected in expected_hashes.items():
        if input_hashes_before[name] != expected:
            raise RuntimeError(f"Frozen input hash mismatch for {name}")

    station_qa = pd.read_csv(input_paths["station_qa"], dtype={"station_id": str})
    full_ids = tuple(sorted(station_qa.station_id.astype(str)))
    if len(full_ids) != 310 or newline_hash(full_ids) != "d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5":
        raise RuntimeError("Frozen 310-ID identity mismatch")
    domain_table = pd.read_csv(input_paths["task_domain"], dtype={"station_id": str})
    domain_ids = tuple(domain_table.loc[domain_table.final_task_domain, "station_id"].astype(str))
    if len(domain_ids) != 302 or len(set(domain_ids)) != 302:
        raise RuntimeError("D302 identity mismatch")
    priority = pd.read_csv(input_paths["priority_components"], dtype={"R1_station_id": str})
    full_priority = tuple(priority.sort_values("hospital_first_rank").R1_station_id.astype(str))
    if len(full_priority) != 302 or set(full_priority) != set(domain_ids):
        raise RuntimeError("Hospital-first sequence mismatch")

    damage, duration, fixture_ledger = deterministic_integration_fixture(domain_ids)
    repeat_damage, repeat_duration, repeat_ledger = deterministic_integration_fixture(domain_ids)
    if not damage.equals(repeat_damage) or not duration.equals(repeat_duration) or not fixture_ledger.equals(repeat_ledger):
        raise RuntimeError("Deterministic fixture repeat check failed")

    base = pd.read_csv(input_paths["base_to_task"], dtype={"yard_id": str}).set_index("yard_id")
    base.columns = base.columns.astype(str)
    task = pd.read_csv(input_paths["task_to_task"], dtype={"R1_station_id": str}).set_index("R1_station_id")
    task.columns = task.columns.astype(str)
    roster_definition = pd.read_csv(input_paths["crew_rosters"], dtype={"yard_id": str})
    crew_roster = _expand_c57_roster(roster_definition)

    edges = pd.read_csv(input_paths["graph_checkpoint"], dtype={"src": str, "tgt": str})
    graph = nx.Graph()
    graph.add_nodes_from(full_ids)
    graph.add_edges_from(edges[["src", "tgt"]].itertuples(index=False, name=None))
    component_sizes = sorted((len(nodes) for nodes in nx.connected_components(graph)), reverse=True)
    if graph.number_of_nodes() != 310 or graph.number_of_edges() != 1040 or component_sizes != [302, 2, 1, 1, 1, 1, 1, 1]:
        raise RuntimeError("Frozen graph identity mismatch")
    if newline_hash(sorted(REFERENCE_SOURCE_IDS)) != "c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3":
        raise RuntimeError("Reference source identity mismatch")

    identified_mask = pd.Series(True, index=full_ids, dtype=bool)
    identified_mask.loc[list(UNRESOLVED_IDS)] = False
    if int(identified_mask.sum()) != 306:
        raise RuntimeError("Authoritative 306/4 mask mismatch")

    service_nodes = pd.read_csv(input_paths["service_nodes"], dtype=str)
    service_ids = tuple(service_nodes.service_node_id.astype(str))
    attachment = pd.read_csv(input_paths["attachment_ledger"], dtype=str, keep_default_na=False)
    w1 = pd.read_csv(input_paths["w1"], dtype={"tract_id": str})
    tract_metadata = pd.read_csv(input_paths["tract_metadata"], dtype={"tract_id": str})

    scheduler_module = _load_module(input_paths["scheduler"], "r25_scheduler")
    exporter_module = _load_module(input_paths["exporter"], "r25_exporter")
    service_module = _load_module(input_paths["service_interface"], "r25_service")
    main_module = _load_module(input_paths["main_model"], "r25_main_gate")

    producer_hash = sha256_file(runner_path)
    provenance = {
        "schema_version": exporter_module.SCHEMA_VERSION,
        "trajectory_id": f"{SCENARIO_ID}|{STRATEGY_ID}|{REALIZATION_ID}",
        "producer_file": runner_path.name,
        "producer_function": "run_revised_realization",
        "effective_state_semantics": exporter_module.EFFECTIVE_STATE_SEMANTICS,
        "frozen_R1_ID_hash": exporter_module.hash_frozen_r1_ids(full_ids),
        "source_time_unit": SOURCE_TIME_UNIT,
        "source_scenario_identifier": "REFERENCE_SOURCE_AVAILABILITY_SCENARIO_21",
        "producer_code_hash": producer_hash,
    }

    fixture_entries = fixture_ledger.to_dict(orient="records")
    manifest = {
        "schema": "R25_ONE_REALIZATION_SCHEDULE_INTEGRATION_V1",
        "scientific_status": "TEST_ONLY_NOT_A_PAPER_RESULT",
        "scientific_execution_count_authorized": 1,
        "pre_scientific_attempts": [
            {
                "status": "FAILED_BEFORE_SCIENTIFIC_EXECUTION",
                "reason": "runner import path omitted repository root; strategy_names was not importable",
                "scientific_calls_completed": 0,
                "resolution": "module loader now temporarily exposes only the imported file's parent directory",
            }
        ],
        "scenario_id": SCENARIO_ID,
        "strategy_id": STRATEGY_ID,
        "realization_id": REALIZATION_ID,
        "task_selection_rule": "sort SHA256('R25_INTEGRATION|' + R1_ID); first 80",
        "duration_rule": "SHA256('R25_DURATION|' + R1_ID) open-unit mapping; positive-conditioned Normal inverse CDF",
        "duration_parameters": {str(ds): {"mean_hr": mu, "sd_hr": sigma}
                                for ds, (mu, sigma) in DURATION_PARAMETERS.items()},
        "requested_event_horizon": "max_completion",
        "dimensions": {"full_r1": 310, "D302": 302, "tasks": 80,
                       "crews": 57, "service_nodes": 196, "tracts": 817},
        "damage_counts": {str(int(k)): int(v) for k, v in damage.value_counts().sort_index().items()},
        "damage_vector_sha256": indexed_numeric_hash(damage),
        "duration_vector_sha256": indexed_numeric_hash(duration),
        "selected_task_ids_sha256": newline_hash(fixture_ledger.R1_station_id.tolist()),
        "selected_tasks": fixture_entries,
        "full_r1_id_sha256": newline_hash(full_ids),
        "D302_id_sha256": newline_hash(domain_ids),
        "hospital_first_sequence_sha256": newline_hash(full_priority),
        "source_ids": list(REFERENCE_SOURCE_IDS),
        "source_id_sha256": newline_hash(sorted(REFERENCE_SOURCE_IDS)),
        "functional_threshold": FUNCTIONAL_THRESHOLD,
        "authoritative_mask": {"identified": 306, "unidentified": 4,
                               "unidentified_ids": list(UNRESOLVED_IDS)},
        "out_of_domain_semantics": {
            "unresolved_registration": "numeric inert zero plus state_identified=False; no task",
            "identified_source_less": "fixed raw=1, identified=True, source gate yields zero",
            "component2": "fixed raw=1, identified=True, no task",
        },
        "graph": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(),
                  "component_sizes": component_sizes},
        "runner_code_sha256": producer_hash,
        "input_hashes": input_hashes_before,
        "forbidden_outputs": ["T50", "T80", "T90", "AUC", "cumulative_service_deficit",
                              "strategy_comparison", "equity_analysis", "hospital_outcomes"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    manifest_hash = sha256_file(manifest_path)

    # The single authorized deterministic end-to-end scientific execution.
    result = run_revised_realization(
        domain_ids=domain_ids,
        full_priority_sequence=full_priority,
        damage_states=damage,
        realized_duration_hr=duration,
        base_to_task_hr=base,
        task_to_task_hr=task,
        crew_roster=crew_roster,
        full_r1_ids=full_ids,
        state_identified_static=identified_mask,
        graph=graph,
        source_ids=set(REFERENCE_SOURCE_IDS),
        requested_event_horizon="max_completion",
        service_attachment_ledger=attachment,
        w1=w1,
        tract_metadata=tract_metadata,
        service_ids=service_ids,
        scheduler_callable=scheduler_module.execute_event_based_schedule,
        source_gate_callable=main_module.apply_source_gate_to_substation_series,
        exporter_callable=exporter_module.export_r1_effective_state_trajectory,
        service_evaluator_callable=service_module.evaluate_service_layer_trajectory,
        exporter_provenance=provenance,
    )

    schedule = result.schedule
    events = schedule.task_events.copy()
    events = events.merge(fixture_ledger, left_on="task_id", right_on="R1_station_id",
                          how="left", validate="one_to_one").drop(columns="R1_station_id")
    if len(events) != 80 or events.task_id.nunique() != 80:
        raise RuntimeError("Schedule does not contain exactly 80 unique tasks")
    expected_queue = tuple(station_id for station_id in full_priority if damage.loc[station_id] > 0)
    if schedule.filtered_task_sequence != expected_queue or tuple(events.task_id) != expected_queue:
        raise RuntimeError("Filtered Hospital-first queue changed")
    if not np.array_equal(events.realized_duration_hr_x.to_numpy(),
                          events.realized_duration_hr_y.to_numpy()):
        raise RuntimeError("Scheduler changed realized durations")
    events = events.rename(columns={"realized_duration_hr_x": "realized_duration_hr"}).drop(
        columns="realized_duration_hr_y")
    if not np.array_equal(events.completion_hr.to_numpy(),
                          (events.arrival_hr + events.realized_duration_hr).to_numpy()):
        raise RuntimeError("Completion is not exactly arrival plus duration")
    base_legs = int(events.previous_task_id.isna().sum())
    task_legs = int(events.previous_task_id.notna().sum())
    crews_used = int(events.crew_index.nunique())
    if base_legs != 57 or task_legs != 23 or crews_used != 57:
        raise RuntimeError("C57 base/task leg integration was not exercised as expected")
    for _, block in events.groupby("crew_index", sort=False):
        block = block.sort_values("dispatch_rank")
        previous_completion = 0.0
        for row in block.itertuples():
            if row.crew_available_before_hr != previous_completion:
                raise RuntimeError("Crew release time does not equal previous task completion")
            previous_completion = row.completion_hr

    raw = result.raw_functionality
    effective = result.effective_network_state
    mask_frame = result.state_identified
    event_times = result.event_times_hr
    time_position = {float(value): k for k, value in enumerate(event_times)}
    raw_transition_count = 0
    effective_transition_count = 0
    for row in events.itertuples():
        current = time_position[float(row.completion_hr)]
        if current == 0:
            raise RuntimeError("A positive-duration task completed at t=0")
        previous = current - 1
        residual = INITIAL_FUNCTIONALITY_BY_DS[int(row.damage_state)]
        if raw.iloc[previous][row.task_id] != residual or raw.iloc[current][row.task_id] != 1.0:
            raise RuntimeError(f"Raw completion transition failed for {row.task_id}")
        raw_transition_count += 1
        if effective.iloc[current][row.task_id] > effective.iloc[previous][row.task_id]:
            effective_transition_count += 1
    if raw_transition_count != 80:
        raise RuntimeError("Not all raw transitions occurred at completion")

    if list(mask_frame.columns) != list(full_ids) or int(mask_frame.to_numpy().sum()) != 306 * len(event_times):
        raise RuntimeError("R1 missing mask changed")
    if not (~mask_frame.loc[:, list(UNRESOLVED_IDS)]).all().all():
        raise RuntimeError("Unresolved R1 records did not remain missing")
    raw_diff = np.diff(raw.to_numpy(), axis=0)
    effective_diff = np.diff(effective.to_numpy(), axis=0)
    if (raw_diff < -1e-12).any():
        raise RuntimeError("Raw functionality decreased in a repair-only realization")
    if (effective_diff < -1e-12).any():
        raise RuntimeError("Effective network state decreased in a repair-only realization")
    identified_values = effective.to_numpy()[mask_frame.to_numpy()]
    if not np.isfinite(identified_values).all() or (identified_values < 0).any() or (identified_values > 1).any():
        raise RuntimeError("Identified effective state violates [0,1]")

    evaluation = result.service_evaluation
    service_states = evaluation.service_trajectory
    attachment_indexed = attachment.set_index("service_node_id").reindex(service_ids)
    class_c = attachment_indexed.attachment_class == service_module.ATTACHMENT_C
    if not service_states.loc[:, class_c].isna().all().all():
        raise RuntimeError("Class C service states did not remain missing")
    ab_mismatch = 0
    for service_id, row in attachment_indexed.loc[~class_c].iterrows():
        upstream = str(row.selected_upstream_R1_id)
        observed = service_states[service_id].to_numpy()
        expected = evaluation.network_trajectory[upstream].to_numpy()
        if not np.array_equal(observed, expected, equal_nan=True):
            ab_mismatch += 1
    if ab_mismatch:
        raise RuntimeError("A/B service lookup differs from selected upstream state")

    intervals = evaluation.tract_intervals
    if (intervals.lower > intervals.upper + 1e-12).any():
        raise RuntimeError("Tract lower bound exceeds upper bound")
    mass_error = float(np.max(np.abs(intervals.resolved_mass + intervals.unresolved_mass - 1.0)))
    if mass_error > 5e-12:
        raise RuntimeError("Resolved plus unresolved W1 mass violates unit sum")
    w1_matrix = w1.set_index("tract_id").loc[:, list(service_ids)].to_numpy(dtype=float)
    w1_hash_after = sha256_file(input_paths["w1"])
    if w1_hash_after != input_hashes_before["w1"]:
        raise RuntimeError("W1 input changed")
    service_missing = service_states.isna().to_numpy()
    for time_index in range(len(event_times)):
        expected_unresolved = w1_matrix[:, service_missing[time_index]].sum(axis=1)
        observed_unresolved = intervals.loc[intervals.time_index == time_index,
                                            "unresolved_mass"].to_numpy()
        if not np.allclose(observed_unresolved, expected_unresolved, atol=5e-12, rtol=0.0):
            raise RuntimeError("Production service aggregation renormalized missing W1 mass")

    for station_id in IDENTIFIED_SOURCELESS_IDS:
        if not np.all(effective[station_id].to_numpy() == 0.0):
            raise RuntimeError(f"Expected identified source-unreachable state for {station_id}")
    if not mask_frame.loc[:, list(OUTSIDE_COMPONENT2_IDS)].all().all():
        raise RuntimeError("Component-2 non-task records lost identified-state semantics")

    r1_varying = int((np.ptp(effective.to_numpy(), axis=0) > 1e-12).sum())
    service_ab_values = service_states.loc[:, ~class_c].to_numpy(dtype=float)
    service_varying = int((np.ptp(service_ab_values, axis=0) > 1e-12).sum())
    tract_ids = tract_metadata.tract_id.astype(str).tolist()
    tract_lower = _pivot_tract_field(intervals, "lower", len(event_times), tract_ids)
    tract_upper = _pivot_tract_field(intervals, "upper", len(event_times), tract_ids)
    tract_resolved = _pivot_tract_field(intervals, "resolved_mass", len(event_times), tract_ids)
    tract_unresolved = _pivot_tract_field(intervals, "unresolved_mass", len(event_times), tract_ids)
    tract_varying = int((np.ptp(tract_lower, axis=0) > 1e-12).sum())
    if r1_varying == 0 or service_varying == 0 or tract_varying == 0:
        raise RuntimeError("Real dynamic propagation was not exercised")

    input_hashes_after = {name: sha256_file(path) for name, path in input_paths.items()}
    if input_hashes_after != input_hashes_before:
        raise RuntimeError("A frozen input changed during execution")

    event_path.parent.mkdir(parents=True, exist_ok=True)
    events.to_csv(event_path, index=False, float_format="%.17g", lineterminator="\n")
    np.savez_compressed(
        evidence_path,
        full_r1_ids=np.array(full_ids),
        d302_ids=np.array(domain_ids),
        event_times_hr=event_times,
        damage_states=damage.to_numpy(dtype=np.int8),
        realized_duration_hr=duration.to_numpy(dtype=float),
        task_ids=events.task_id.astype(str).to_numpy(),
        task_completion_hr=events.completion_hr.to_numpy(dtype=float),
        raw_functionality=raw.to_numpy(dtype=float),
        effective_network_state=effective.to_numpy(dtype=float),
        state_identified=mask_frame.to_numpy(dtype=bool),
        service_ids=np.array(service_ids),
        service_state=service_states.to_numpy(dtype=float),
        tract_ids=np.array(tract_ids),
        tract_lower=tract_lower,
        tract_upper=tract_upper,
        tract_resolved_mass=tract_resolved,
        tract_unresolved_mass=tract_unresolved,
    )
    event_hash = sha256_file(event_path)
    evidence_hash = sha256_file(evidence_path)
    makespan = float(events.completion_hr.max())
    report = f"""# One-Realization Schedule Integration Report

## Decision

**PASS — REVISED ONE-REALIZATION END-TO-END INTEGRATION VERIFIED**

- `EXECUTION_ENGINE_PRODUCTION_INTEGRATED = YES`
- `SCIENTIFIC_EXECUTIONS = 1`
- `DAMAGE_OR_DURATION_RANDOM_DRAWS = 0`
- `GA_MC_KPI_EXECUTIONS = 0`
- `MAIN_LEGACY_STAGE4_STAGE5_EXECUTIONS = 0`

One preliminary command failed before the scheduler, gate, or any scientific-state
calculation because the runner's isolated module loader did not expose the repository
root for `strategy_names`. No manifest or scientific output was produced. The loader
path was corrected; no frozen module, scientific input, or model parameter changed.

This is a test-only deterministic architecture integration. It is not a paper result
and is not interpreted as a recovery, policy, hospital, population, or equity finding.

## Frozen inputs and mechanical fixture

The run used D302, the frozen C57 pooled roster, the Round 23 Hospital-first full
sequence, strict directed 11×302 and 302×302 travel matrices, the frozen 310-node /
1040-edge graph, and the 21-node reference source-availability scenario.

The 80 task IDs were selected only by ascending
`SHA256("R25_INTEGRATION|" + R1_ID)`. Damage states cycle DS1–DS4 by hash rank,
giving 20 tasks per state and 222 DS0 assets. Each task duration is the positive-
conditioned Normal inverse CDF of the open-unit value derived from
`SHA256("R25_DURATION|" + R1_ID)`. Repeated fixture construction was exact. The
complete vectors and all 80 hash records are frozen in the manifest/evidence.

- DS vector SHA-256: `{indexed_numeric_hash(damage)}`
- duration vector SHA-256: `{indexed_numeric_hash(duration)}`
- input manifest SHA-256: `{manifest_hash}`

## Actual event schedule

- scheduled tasks: 80, each exactly once
- crews available: 57; crews used: {crews_used}
- Base→Task legs: {base_legs}
- Task→Task legs: {task_legs}
- filtered order: exact Hospital-first full sequence with DS0 removed
- duration preservation: 80/80 exact
- completion equation: 80/80 exact `arrival + duration`
- crew release: every next crew availability equals its previous completion
- integration-only makespan: {makespan:.12f} h

The makespan is retained only as dispatch QA and has no policy interpretation.

## Raw functionality and source/component gate

The event grid contains t=0 plus every unique completion time; the final horizon is
the maximum completion. No dense 0.05 h grid was generated. All 80 tasks retained
their DS residual at the preceding event and changed to raw=1 at their exact
completion event. Crew release, task completion, and raw restoration therefore share
the same event time for 80/80 tasks.

The frozen source/component gate was executed over every event using threshold 0.5
and the unchanged 21-node reference scenario. It is a source-connected upstream
availability proxy, not power flow.

- raw-increase completions: {raw_transition_count}
- task completions with simultaneous own effective-state increase: {effective_transition_count}
- raw restored while own effective state did not increase: {raw_transition_count - effective_transition_count}
- identified R1 states varying over time: {r1_varying}
- raw monotonicity: PASS
- effective-state monotonicity: PASS

An unchanged effective state at completion is valid when source connectivity still
does not support the asset.

The eight non-task R1 records retain frozen representation semantics: four unresolved
registrations (`301479`, `303265`, `304137`, `305021`) use inert numeric zero with
`state_identified=False`; `306980` and `309598` are identified, fixed raw=1 isolates
and remain source-unreachable; `303547` and `307683` are identified component-2
records fixed at raw=1 and are never repair tasks.

## Architecture B propagation

The complete effective trajectory passed through the frozen Round 16 exporter and
Round 14 production interface. No mapping logic was added.

- Class A/B service lookup mismatches: 0
- Class C missing-state violations: 0
- A/B service nodes varying over time: {service_varying}
- tract lower bounds varying over time: {tract_varying}
- unresolved R1 states remain missing: PASS
- effective states within [0,1] where identified: PASS
- W1 file unchanged and never renormalized: PASS
- maximum `|resolved + unresolved - 1|`: {mass_error:.17g}
- tract `lower <= upper`: PASS

Actual service/tract aggregate values and all recovery KPIs are deliberately omitted.

## Execution boundary and integrity

- revised scheduler calls: 1
- source/component gate calls: 1 trajectory call covering all event times
- exporter calls: 1
- Architecture B production-interface calls: 1
- GA calls: 0
- Monte Carlo calls: 0
- T50/T80/T90/AUC calculations: 0
- legacy Stage 4/5 calls: 0
- frozen input hash changes: 0
- `C257H_Project_Main.py` modified: NO

Artifacts:

- schedule events SHA-256: `{event_hash}`
- end-to-end evidence SHA-256: `{evidence_hash}`
- runner SHA-256: `{producer_hash}`

## Conclusion

The revised execution architecture is connected end to end:

`D302 deterministic fixture → C57 event scheduler → completion-step raw state → frozen source gate → frozen exporter → Architecture B service states → 817 tract intervals`.

`EXECUTION_ENGINE_PRODUCTION_INTEGRATED = YES`.

Engineering QA stops here. The next work is **GA reproducibility + revised paired
pilot**: freeze the 2pc50 hazard, generate Architecture-B GA inputs, run multi-seed
convergence for the three GA policies, freeze their 302-ID ex-ante sequences, and
then execute the paired 32×4 C57 pilot with realization-level outputs.
"""
    report_path.write_text(report, encoding="utf-8")
    print(json.dumps({
        "decision": "PASS_REVISED_ONE_REALIZATION_END_TO_END_INTEGRATION_VERIFIED",
        "tasks": len(events), "crews_used": crews_used,
        "base_legs": base_legs, "task_legs": task_legs,
        "event_times": len(event_times), "raw_transitions": raw_transition_count,
        "effective_task_increases": effective_transition_count,
        "r1_varying": r1_varying, "service_varying": service_varying,
        "tract_varying": tract_varying, "makespan_hr_QA_only": makespan,
        "manifest_sha256": manifest_hash, "events_sha256": event_hash,
        "evidence_sha256": evidence_hash,
    }, indent=2))


if __name__ == "__main__":
    main()
