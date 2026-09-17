"""Deterministic dispatch-only scheduler for the revised R1 pilot contract.

This module consumes a complete, explicitly identified scheduling domain and
precomputed damage, duration, travel, roster, and priority inputs.  It does not
generate scientific state, calculate priority, or evaluate recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Sequence

import numpy as np
import pandas as pd


EVENT_COLUMNS = (
    "task_id",
    "damage_state",
    "full_priority_rank",
    "dispatch_rank",
    "crew_index",
    "crew_id",
    "crew_origin_key",
    "previous_task_id",
    "crew_available_before_hr",
    "travel_hr",
    "arrival_hr",
    "realized_duration_hr",
    "completion_hr",
)


@dataclass(frozen=True)
class R1EventScheduleResult:
    """In-memory dispatch result; it contains no recovery or network state."""

    task_events: pd.DataFrame
    task_start_hr: pd.Series
    task_completion_hr: pd.Series
    task_crew_index: pd.Series
    task_travel_hr: pd.Series
    filtered_task_sequence: tuple[str, ...]
    crew_final_available_hr: pd.Series


def _string_ids(values: Sequence[str], name: str, *, nonempty: bool = True) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be a sequence of explicit string IDs, not a scalar string")
    result = tuple(values)
    if nonempty and not result:
        raise ValueError(f"{name} must be nonempty")
    if any(type(value) is not str or not value or value != value.strip() for value in result):
        raise TypeError(f"{name} must contain nonempty, whitespace-stable string IDs")
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicate IDs")
    return result


def _station_series(series: pd.Series, domain: tuple[str, ...], name: str) -> pd.Series:
    if not isinstance(series, pd.Series):
        raise TypeError(f"{name} must be a pandas Series with explicit station-ID index")
    if series.index.has_duplicates:
        raise ValueError(f"{name} contains duplicate station IDs")
    index = _string_ids(tuple(series.index), f"{name}.index")
    if set(index) != set(domain) or len(index) != len(domain):
        raise ValueError(f"{name} station domain does not exactly match domain_ids")
    return series.copy(deep=True).reindex(domain)


def _numeric_matrix(frame: pd.DataFrame, name: str) -> np.ndarray:
    if any(not pd.api.types.is_numeric_dtype(dtype) or pd.api.types.is_bool_dtype(dtype)
           for dtype in frame.dtypes):
        raise TypeError(f"{name} must contain numeric, non-Boolean values")
    values = frame.to_numpy(dtype=float, copy=True)
    if not np.isfinite(values).all():
        raise ValueError(f"{name} contains NaN or infinite travel")
    if (values < 0.0).any():
        raise ValueError(f"{name} contains negative travel")
    if (values == 24.0).any():
        raise ValueError(f"{name} contains the prohibited 24 h fallback sentinel")
    return values


def _validate_inputs(
    *,
    domain_ids: Sequence[str],
    full_priority_sequence: Sequence[str],
    damage_states: pd.Series,
    realized_duration_hr: pd.Series,
    base_to_task_hr: pd.DataFrame,
    task_to_task_hr: pd.DataFrame,
    crew_roster: pd.DataFrame,
):
    domain = _string_ids(domain_ids, "domain_ids")
    priority = _string_ids(full_priority_sequence, "full_priority_sequence")
    if len(priority) != len(domain) or set(priority) != set(domain):
        raise ValueError("full_priority_sequence must contain every domain ID exactly once")

    damage = _station_series(damage_states, domain, "damage_states")
    for station_id, value in damage.items():
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"damage state for {station_id} must be an integer")
        if int(value) not in {0, 1, 2, 3, 4}:
            raise ValueError(f"damage state for {station_id} must be in 0..4")
    damage = damage.astype(np.int8)

    duration = _station_series(realized_duration_hr, domain, "realized_duration_hr")
    if not pd.api.types.is_numeric_dtype(duration.dtype) or pd.api.types.is_bool_dtype(duration.dtype):
        raise TypeError("realized_duration_hr must be numeric and non-Boolean")
    duration = duration.astype(float)
    for station_id in domain:
        value = float(duration.loc[station_id])
        ds = int(damage.loc[station_id])
        if not np.isfinite(value):
            raise ValueError(f"duration for {station_id} must be finite")
        if ds == 0 and value != 0.0:
            raise ValueError(f"DS0 duration for {station_id} must equal 0")
        if ds > 0 and value <= 0.0:
            raise ValueError(f"damaged duration for {station_id} must be strictly positive")

    if not isinstance(base_to_task_hr, pd.DataFrame):
        raise TypeError("base_to_task_hr must be a DataFrame with explicit IDs")
    if base_to_task_hr.index.has_duplicates or base_to_task_hr.columns.has_duplicates:
        raise ValueError("base_to_task_hr contains duplicate IDs")
    base_origins = _string_ids(tuple(base_to_task_hr.index), "base_to_task_hr.index")
    base_columns = _string_ids(tuple(base_to_task_hr.columns), "base_to_task_hr.columns")
    if set(base_columns) != set(domain) or len(base_columns) != len(domain):
        raise ValueError("base_to_task_hr columns must exactly match domain_ids")
    base = base_to_task_hr.copy(deep=True).reindex(index=base_origins, columns=domain)
    _numeric_matrix(base, "base_to_task_hr")

    if not isinstance(task_to_task_hr, pd.DataFrame):
        raise TypeError("task_to_task_hr must be a DataFrame with explicit IDs")
    if task_to_task_hr.index.has_duplicates or task_to_task_hr.columns.has_duplicates:
        raise ValueError("task_to_task_hr contains duplicate IDs")
    task_rows = _string_ids(tuple(task_to_task_hr.index), "task_to_task_hr.index")
    task_columns = _string_ids(tuple(task_to_task_hr.columns), "task_to_task_hr.columns")
    if set(task_rows) != set(domain) or set(task_columns) != set(domain):
        raise ValueError("task_to_task_hr rows and columns must exactly match domain_ids")
    task = task_to_task_hr.copy(deep=True).reindex(index=domain, columns=domain)
    task_values = _numeric_matrix(task, "task_to_task_hr")
    if not np.array_equal(np.diag(task_values), np.zeros(len(domain))):
        raise ValueError("task_to_task_hr diagonal must be exactly zero")

    if not isinstance(crew_roster, pd.DataFrame):
        raise TypeError("crew_roster must be a DataFrame")
    required = {"crew_index", "crew_id", "origin_key"}
    if not required.issubset(crew_roster.columns):
        raise ValueError(f"crew_roster is missing required columns: {sorted(required - set(crew_roster.columns))}")
    crew = crew_roster.loc[:, ["crew_index", "crew_id", "origin_key"]].copy(deep=True)
    if crew.empty:
        raise ValueError("crew_roster must contain at least one crew")
    if crew[["crew_index", "crew_id", "origin_key"]].isna().any().any():
        raise ValueError("crew_roster contains missing required values")
    if crew.crew_index.duplicated().any():
        raise ValueError("crew_index must be unique")
    if crew.crew_id.duplicated().any():
        raise ValueError("crew_id must be unique")
    if any(isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer))
           for value in crew.crew_index):
        raise TypeError("crew_index must contain integers")
    if any(type(value) is not str or not value or value != value.strip()
           for value in crew.crew_id):
        raise TypeError("crew_id must contain explicit string IDs")
    if any(type(value) is not str or not value or value != value.strip()
           for value in crew.origin_key):
        raise TypeError("origin_key must contain explicit string IDs")
    crew = crew.sort_values("crew_index", kind="mergesort").reset_index(drop=True)
    expected_indices = list(range(len(crew)))
    if crew.crew_index.tolist() != expected_indices:
        raise ValueError("crew_index must be the contiguous range 0..N-1")
    unknown_origins = set(crew.origin_key) - set(base_origins)
    if unknown_origins:
        raise ValueError(f"crew origin_key absent from base_to_task_hr: {sorted(unknown_origins)}")

    return domain, priority, damage, duration, base, task, crew


def execute_event_based_schedule(
    *,
    domain_ids: Sequence[str],
    full_priority_sequence: Sequence[str],
    damage_states: pd.Series,
    realized_duration_hr: pd.Series,
    base_to_task_hr: pd.DataFrame,
    task_to_task_hr: pd.DataFrame,
    crew_roster: pd.DataFrame,
) -> R1EventScheduleResult:
    """Dispatch a frozen static priority list using earliest-release crew events.

    Realized duration affects completion and subsequent crew release only.  It
    never changes the filtered priority queue or selects the next task.
    """

    domain, priority, damage, duration, base, task, crew = _validate_inputs(
        domain_ids=domain_ids,
        full_priority_sequence=full_priority_sequence,
        damage_states=damage_states,
        realized_duration_hr=realized_duration_hr,
        base_to_task_hr=base_to_task_hr,
        task_to_task_hr=task_to_task_hr,
        crew_roster=crew_roster,
    )
    filtered = tuple(station_id for station_id in priority if int(damage.loc[station_id]) > 0)
    full_rank = {station_id: rank for rank, station_id in enumerate(priority, start=1)}

    starts = pd.Series(np.nan, index=pd.Index(domain, name="task_id"), dtype=float,
                       name="task_start_hr")
    completions = pd.Series(np.nan, index=starts.index, dtype=float,
                            name="task_completion_hr")
    crew_assignment = pd.Series(pd.array([pd.NA] * len(domain), dtype="Int64"),
                                index=starts.index, name="task_crew_index")
    travel_series = pd.Series(np.nan, index=starts.index, dtype=float,
                              name="task_travel_hr")

    crew_id = dict(zip(crew.crew_index, crew.crew_id))
    crew_origin = dict(zip(crew.crew_index, crew.origin_key))
    calendar = [(0.0, int(index), None) for index in crew.crew_index]
    heapq.heapify(calendar)
    events = []

    for dispatch_rank, station_id in enumerate(filtered, start=1):
        available, index, previous = heapq.heappop(calendar)
        if previous is None:
            travel = float(base.loc[crew_origin[index], station_id])
        else:
            travel = float(task.loc[previous, station_id])
        arrival = available + travel
        task_duration = float(duration.loc[station_id])
        completion = arrival + task_duration
        events.append({
            "task_id": station_id,
            "damage_state": int(damage.loc[station_id]),
            "full_priority_rank": int(full_rank[station_id]),
            "dispatch_rank": dispatch_rank,
            "crew_index": index,
            "crew_id": crew_id[index],
            "crew_origin_key": crew_origin[index],
            "previous_task_id": previous,
            "crew_available_before_hr": available,
            "travel_hr": travel,
            "arrival_hr": arrival,
            "realized_duration_hr": task_duration,
            "completion_hr": completion,
        })
        starts.loc[station_id] = arrival
        completions.loc[station_id] = completion
        crew_assignment.loc[station_id] = index
        travel_series.loc[station_id] = travel
        heapq.heappush(calendar, (completion, index, station_id))

    event_frame = pd.DataFrame(events, columns=EVENT_COLUMNS)
    expected_indices = list(range(len(crew)))
    final_available = pd.Series(
        0.0,
        index=pd.Index(expected_indices, name="crew_index"),
        dtype=float,
        name="crew_final_available_hr",
    )
    for available, index, _ in calendar:
        final_available.loc[index] = available
    if list(final_available.index) != expected_indices:
        raise RuntimeError("internal crew calendar identity error")

    return R1EventScheduleResult(
        task_events=event_frame,
        task_start_hr=starts,
        task_completion_hr=completions,
        task_crew_index=crew_assignment,
        task_travel_hr=travel_series,
        filtered_task_sequence=filtered,
        crew_final_available_hr=final_available,
    )
