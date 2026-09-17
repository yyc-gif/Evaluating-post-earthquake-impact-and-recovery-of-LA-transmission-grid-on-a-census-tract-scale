from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal


HERE = Path(__file__).resolve().parent
ROOT = Path("R:/")
ROUND23 = ROOT / "Review_and_Revision" / "IJDRR-D-26-02276" / "23_R1_310_Scheduling_Input_Readiness_20260916"
sys.path.insert(0, str(HERE))

from r1_event_based_scheduler import execute_event_based_schedule  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manual_fixture():
    domain = ("A", "B", "C", "D", "E", "F")
    damage = pd.Series([1, 0, 2, 3, 4, 1], index=domain, dtype=int)
    duration = pd.Series([4.0, 0.0, 2.0, 1.0, 3.0, 1.5], index=domain)
    base = pd.DataFrame(
        [[1.0, 0.0, 2.0, 4.0, 6.0, 7.0],
         [2.0, 0.0, 1.0, 3.0, 5.0, 8.0]],
        index=["O0", "O1"], columns=domain)
    task = pd.DataFrame(5.0, index=domain, columns=domain)
    np.fill_diagonal(task.values, 0.0)
    task.loc["C", "D"] = 2.0
    task.loc["D", "C"] = 9.0
    task.loc["A", "E"] = 1.5
    task.loc["E", "A"] = 8.0
    task.loc["D", "F"] = 0.5
    task.loc["F", "D"] = 7.0
    crew = pd.DataFrame({"crew_index": [0, 1], "crew_id": ["C0", "C1"],
                         "origin_key": ["O0", "O1"]})
    return dict(domain_ids=domain, full_priority_sequence=domain,
                damage_states=damage, realized_duration_hr=duration,
                base_to_task_hr=base, task_to_task_hr=task, crew_roster=crew)


def basic_fixture(domain=("A", "B", "C"), crews=2):
    damage = pd.Series([1] * len(domain), index=domain, dtype=int)
    duration = pd.Series([1.0] * len(domain), index=domain)
    origins = [f"O{k}" for k in range(crews)]
    base = pd.DataFrame(0.0, index=origins, columns=domain)
    task = pd.DataFrame(0.0, index=domain, columns=domain)
    roster = pd.DataFrame({"crew_index": list(range(crews)),
                           "crew_id": [f"C{k}" for k in range(crews)],
                           "origin_key": origins})
    return dict(domain_ids=tuple(domain), full_priority_sequence=tuple(domain),
                damage_states=damage, realized_duration_hr=duration,
                base_to_task_hr=base, task_to_task_hr=task, crew_roster=roster)


def test_fixture_a_independent_hand_oracle_exact():
    result = execute_event_based_schedule(**manual_fixture())
    expected = pd.read_csv(HERE / "SYNTHETIC_SCHEDULER_ORACLE.csv",
                           dtype={"task_id": str, "crew_id": str,
                                  "crew_origin_key": str, "previous_task_id": str})
    actual = result.task_events.copy()
    actual["previous_task_id"] = actual.previous_task_id.fillna("")
    expected["previous_task_id"] = expected.previous_task_id.fillna("")
    assert_frame_equal(actual, expected, check_dtype=False, check_exact=True)
    assert result.filtered_task_sequence == ("A", "C", "D", "E", "F")
    assert pd.isna(result.task_start_hr.loc["B"])
    assert pd.isna(result.task_completion_hr.loc["B"])
    assert pd.isna(result.task_crew_index.loc["B"])
    assert pd.isna(result.task_travel_hr.loc["B"])


def test_fixture_b_crew_tie_break_at_zero_and_later_tie():
    f = basic_fixture(("A", "B", "C"), crews=2)
    f["realized_duration_hr"] = pd.Series([2.0, 2.0, 1.0], index=f["domain_ids"])
    f["task_to_task_hr"].loc["A", "C"] = 0.5
    f["task_to_task_hr"].loc["B", "C"] = 7.0
    result = execute_event_based_schedule(**f)
    assert result.task_events.crew_index.tolist() == [0, 1, 0]
    assert result.task_events.previous_task_id.fillna("").tolist() == ["", "", "A"]
    assert result.task_events.travel_hr.tolist() == [0.0, 0.0, 0.5]


def test_fixture_c_uses_directed_previous_to_next_cell():
    f = basic_fixture(("A", "B"), crews=1)
    f["task_to_task_hr"].loc["A", "B"] = 1.0
    f["task_to_task_hr"].loc["B", "A"] = 9.0
    result = execute_event_based_schedule(**f)
    assert result.task_events.travel_hr.tolist() == [0.0, 1.0]
    assert result.task_events.arrival_hr.tolist() == [0.0, 2.0]
    assert result.task_events.completion_hr.tolist() == [1.0, 3.0]


def test_fixture_d_ds0_filter_preserves_full_sequence_rank():
    f = basic_fixture(("A", "B", "C", "D"), crews=1)
    f["damage_states"] = pd.Series([1, 0, 2, 0], index=f["domain_ids"], dtype=int)
    f["realized_duration_hr"] = pd.Series([1.0, 0.0, 1.0, 0.0], index=f["domain_ids"])
    result = execute_event_based_schedule(**f)
    assert result.filtered_task_sequence == ("A", "C")
    assert result.task_events.full_priority_rank.tolist() == [1, 3]
    assert result.task_events.dispatch_rank.tolist() == [1, 2]


def test_fixture_e_duration_changes_release_not_priority_order():
    f1 = basic_fixture(("A", "B", "C", "D"), crews=2)
    f2 = basic_fixture(("A", "B", "C", "D"), crews=2)
    f1["realized_duration_hr"] = pd.Series([1.0, 10.0, 1.0, 1.0], index=f1["domain_ids"])
    f2["realized_duration_hr"] = pd.Series([10.0, 1.0, 1.0, 1.0], index=f2["domain_ids"])
    r1 = execute_event_based_schedule(**f1)
    r2 = execute_event_based_schedule(**f2)
    assert r1.filtered_task_sequence == r2.filtered_task_sequence == ("A", "B", "C", "D")
    assert r1.task_events.task_id.tolist() == r2.task_events.task_id.tolist()
    assert r1.task_events.crew_index.tolist() != r2.task_events.crew_index.tolist()


def test_fixture_f_single_crew_release_plus_directed_travel():
    f = basic_fixture(("A", "B", "C"), crews=1)
    f["realized_duration_hr"] = pd.Series([2.0, 3.0, 4.0], index=f["domain_ids"])
    f["base_to_task_hr"].loc["O0", "A"] = 0.5
    f["task_to_task_hr"].loc["A", "B"] = 1.25
    f["task_to_task_hr"].loc["B", "C"] = 2.5
    result = execute_event_based_schedule(**f)
    assert result.task_events.arrival_hr.tolist() == [0.5, 3.75, 9.25]
    assert result.task_events.completion_hr.tolist() == [2.5, 6.75, 13.25]
    assert result.crew_final_available_hr.loc[0] == 13.25


def test_empty_task_realization_is_valid_and_missing_not_zero():
    f = basic_fixture(("A", "B"), crews=2)
    f["damage_states"][:] = 0
    f["realized_duration_hr"][:] = 0.0
    result = execute_event_based_schedule(**f)
    assert result.filtered_task_sequence == ()
    assert result.task_events.empty
    assert result.task_start_hr.isna().all()
    assert result.task_completion_hr.isna().all()
    assert result.task_crew_index.isna().all()
    assert result.task_travel_hr.isna().all()
    assert result.crew_final_available_hr.tolist() == [0.0, 0.0]


def test_tasks_fewer_than_crews_dispatch_only_lowest_tied_indices():
    f = basic_fixture(("A", "B"), crews=5)
    result = execute_event_based_schedule(**f)
    assert result.task_events.crew_index.tolist() == [0, 1]
    assert result.crew_final_available_hr.tolist() == [1.0, 1.0, 0.0, 0.0, 0.0]


def test_repeat_run_is_exact_and_inputs_are_not_mutated():
    f = manual_fixture()
    before = {}
    for key, value in f.items():
        if isinstance(value, (pd.Series, pd.DataFrame)):
            before[key] = value.copy(deep=True)
        else:
            before[key] = tuple(value)
    first = execute_event_based_schedule(**f)
    second = execute_event_based_schedule(**f)
    assert_frame_equal(first.task_events, second.task_events, check_exact=True)
    assert_series_equal(first.task_start_hr, second.task_start_hr, check_exact=True)
    assert_series_equal(first.task_completion_hr, second.task_completion_hr, check_exact=True)
    assert_series_equal(first.task_crew_index, second.task_crew_index, check_exact=True)
    assert_series_equal(first.task_travel_hr, second.task_travel_hr, check_exact=True)
    assert_series_equal(first.crew_final_available_hr, second.crew_final_available_hr, check_exact=True)
    for key, value in f.items():
        if isinstance(value, pd.DataFrame):
            assert_frame_equal(value, before[key], check_exact=True)
        elif isinstance(value, pd.Series):
            assert_series_equal(value, before[key], check_exact=True)
        else:
            assert tuple(value) == before[key]


def malformed_cases():
    cases = []
    f = basic_fixture(); f["full_priority_sequence"] = ("A", "B"); cases.append(("priority_missing", f))
    f = basic_fixture(); f["full_priority_sequence"] = ("A", "B", "B"); cases.append(("priority_duplicate", f))
    f = basic_fixture(); f["full_priority_sequence"] = ("A", "B", "X"); cases.append(("priority_unknown", f))
    f = basic_fixture(); f["damage_states"] = f["damage_states"].drop("C"); cases.append(("ds_missing", f))
    f = basic_fixture(); f["damage_states"].loc["A"] = 5; cases.append(("ds_five", f))
    f = basic_fixture(); f["damage_states"] = f["damage_states"].astype(float); cases.append(("ds_noninteger", f))
    f = basic_fixture(); f["damage_states"].loc["B"] = 0; f["realized_duration_hr"].loc["B"] = 1; cases.append(("ds0_duration", f))
    f = basic_fixture(); f["realized_duration_hr"].loc["A"] = 0; cases.append(("damaged_zero_duration", f))
    f = basic_fixture(); f["realized_duration_hr"].loc["A"] = -1; cases.append(("negative_duration", f))
    f = basic_fixture(); f["realized_duration_hr"].loc["A"] = np.nan; cases.append(("nan_duration", f))
    f = basic_fixture(); f["crew_roster"] = f["crew_roster"].drop(columns="crew_index"); cases.append(("missing_crew_index", f))
    f = basic_fixture(); f["crew_roster"].loc[1, "crew_index"] = 0; cases.append(("duplicate_crew_index", f))
    f = basic_fixture(); f["crew_roster"].loc[1, "crew_id"] = "C0"; cases.append(("duplicate_crew_id", f))
    f = basic_fixture(); f["crew_roster"].loc[0, "origin_key"] = "OX"; cases.append(("unknown_origin", f))
    f = basic_fixture(); f["base_to_task_hr"] = f["base_to_task_hr"].drop(columns="C"); cases.append(("missing_base_task", f))
    f = basic_fixture(); f["base_to_task_hr"].loc["O0", "A"] = np.inf; cases.append(("base_nonfinite", f))
    f = basic_fixture(); f["task_to_task_hr"] = f["task_to_task_hr"].drop(index="C", columns="C"); cases.append(("missing_task_id", f))
    f = basic_fixture(); f["task_to_task_hr"].loc["A", "B"] = np.nan; cases.append(("task_nonfinite", f))
    f = basic_fixture(); f["task_to_task_hr"].loc["A", "B"] = -1; cases.append(("negative_travel", f))
    f = basic_fixture(); f["task_to_task_hr"].loc["A", "A"] = 1; cases.append(("nonzero_diagonal", f))
    f = basic_fixture(); f["base_to_task_hr"].loc["O0", "A"] = 24.0; cases.append(("forbidden_24h_sentinel", f))
    f = basic_fixture(); f["domain_ids"] = ("A", "B", "X"); cases.append(("domain_mismatch", f))
    return cases


@pytest.mark.parametrize("label,fixture", malformed_cases(), ids=[x[0] for x in malformed_cases()])
def test_malformed_inputs_fail_fast(label, fixture):
    with pytest.raises((TypeError, ValueError)):
        execute_event_based_schedule(**fixture)


def test_positional_anonymous_inputs_are_rejected():
    f = basic_fixture()
    f["damage_states"] = np.array([1, 1, 1])
    with pytest.raises(TypeError):
        execute_event_based_schedule(**f)


def test_round23_real_artifacts_schema_and_hash_only_no_schedule_execution():
    expected_hashes = {
        "R1_TASK_DOMAIN_AND_ELIGIBILITY.csv": "bcd8f493078f51365e9e7a9cafd63d0ec3d5738f358f901f6a841a1d5276fa83",
        "R1_ARCHB_PRIORITY_COMPONENTS.csv": "53c7687c2ca7a4c87b1e5a53946fe67c7f5e05188f40003a3f1fe6371218a1f6",
        "R1_BASE_TO_TASK_TRAVEL_HR.csv": "16177e57cd7e77ea2075e347318c3b7698937af6b0b7dc702f18b9da65662690",
        "R1_TASK_TO_TASK_TRAVEL_HR.csv": "68c03537853bad92544f13688ade89247e135e829b989c71c96be2f8ef45a6de",
        "R1_CREW_SCENARIO_ROSTERS.csv": "4940f0c15e56c884ae2f3fd7717cd93f12e2f37de2bb936a27a8b752df5f3f11",
    }
    for name, expected in expected_hashes.items():
        assert sha(ROUND23 / name) == expected
    task_domain = pd.read_csv(ROUND23 / "R1_TASK_DOMAIN_AND_ELIGIBILITY.csv")
    ids = task_domain.loc[task_domain.final_task_domain, "station_id"].astype(str).tolist()
    assert len(ids) == len(set(ids)) == 302
    priority = pd.read_csv(ROUND23 / "R1_ARCHB_PRIORITY_COMPONENTS.csv")
    sequence = priority.sort_values("hospital_first_rank").R1_station_id.astype(str).tolist()
    assert len(sequence) == len(set(sequence)) == 302 and set(sequence) == set(ids)
    base = pd.read_csv(ROUND23 / "R1_BASE_TO_TASK_TRAVEL_HR.csv", dtype={"yard_id": str})
    task = pd.read_csv(ROUND23 / "R1_TASK_TO_TASK_TRAVEL_HR.csv", dtype={"R1_station_id": str})
    assert base.shape == (11, 303) and task.shape == (302, 303)
    assert set(base.columns[1:]) == set(ids)
    assert set(task.columns[1:]) == set(ids) and set(task.R1_station_id) == set(ids)
    assert np.isfinite(base.iloc[:, 1:].to_numpy(float)).all()
    task_values = task.iloc[:, 1:].to_numpy(float)
    assert np.isfinite(task_values).all() and np.array_equal(np.diag(task_values), np.zeros(302))
    rosters = pd.read_csv(ROUND23 / "R1_CREW_SCENARIO_ROSTERS.csv")
    assert rosters.groupby("crew_scenario").integer_crews.sum().to_dict() == {
        "C29_SCARCITY": 29, "C57_REFERENCE": 57, "C114_ABUNDANCE": 114}
    for _, group in rosters.groupby("crew_scenario"):
        expanded = []
        for row in group.sort_values("yard_id").itertuples():
            expanded.extend([row.yard_id] * int(row.integer_crews))
        assert len(expanded) == int(group.scenario_total.iloc[0])
        assert all(origin in set(base.yard_id) for origin in expanded)


def test_main_model_hash_and_dependency_boundary():
    assert sha(ROOT / "C257H_Project_Main.py") == "90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145"
    source_path = HERE / "r1_event_based_scheduler.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {"__future__", "dataclasses", "heapq", "typing", "numpy", "pandas"}
    forbidden = ["to_csv(", "to_excel(", "networkx", "geopy", "scipy", "random.",
                 "np.random", "DEAP", "deap", "source_gate(", "service_layer."]
    for token in forbidden:
        assert token not in source
