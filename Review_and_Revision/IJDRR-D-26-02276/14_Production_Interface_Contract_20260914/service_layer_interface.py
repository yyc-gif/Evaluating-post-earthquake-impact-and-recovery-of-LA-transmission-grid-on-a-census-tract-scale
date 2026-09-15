"""Production boundary for Architecture B service-access proxy evaluation.

The module consumes externally produced R1 effective states. It contains no
network, source, damage, repair, routing, scheduling, or optimization logic.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import numpy as np
import pandas as pd


ATTACHMENT_A = "A_DIRECT_IDENTITY_ATTACHMENT"
ATTACHMENT_B = "B_NAMED_SYSTEM_UPSTREAM_PROXY"
ATTACHMENT_C = "C_UNRESOLVED_ATTACHMENT"
ATTACHMENT_CLASSES = {ATTACHMENT_A, ATTACHMENT_B, ATTACHMENT_C}
DEFAULT_TOLERANCE = 1e-12
W1_SERIALIZATION_TOLERANCE = 5e-12


class ServiceLayerContractError(ValueError):
    """Raised when an input violates the frozen service-layer contract."""


@dataclass(frozen=True)
class ValidatedTrajectory:
    """Canonical time-by-R1 representation of an external state trajectory."""

    serialized_values: pd.DataFrame
    identified_mask: pd.DataFrame
    semantic_states: pd.DataFrame


@dataclass(frozen=True)
class ServiceLayerEvaluation:
    """Outputs from one pure service-layer interface evaluation."""

    network_trajectory: pd.DataFrame
    network_identified_mask: pd.DataFrame
    service_trajectory: pd.DataFrame
    tract_intervals: pd.DataFrame
    aggregate_intervals: pd.DataFrame


def _string_ids(values: Iterable[object]) -> list[str]:
    result = [str(value).strip() for value in values]
    if any(not value for value in result):
        raise ServiceLayerContractError("Identifiers must be nonempty strings")
    if len(result) != len(set(result)):
        raise ServiceLayerContractError("Expected identifier list contains duplicates")
    return result


def _required_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required - set(frame.columns)
    if missing:
        raise ServiceLayerContractError(f"{name} is missing columns: {sorted(missing)}")


def load_validate_r1_effective_state_trajectory(
    trajectory: pd.DataFrame,
    expected_r1_ids: Iterable[object],
    expected_identified_mask: pd.Series | None = None,
) -> ValidatedTrajectory:
    """Validate and standardize an externally supplied R1 effective trajectory.

    Required long-form columns are ``time_index``, ``R1_station_id``,
    ``effective_state_value``, and ``state_identified``. The numeric field must
    remain finite in [0, 1]. Missing semantics are carried exclusively by the
    Boolean identified mask and become NaN in ``semantic_states``.

    This function never generates, modifies, or interprets upstream states.
    """

    _required_columns(
        trajectory,
        {"time_index", "R1_station_id", "effective_state_value", "state_identified"},
        "trajectory",
    )
    expected_ids = _string_ids(expected_r1_ids)
    frame = trajectory.copy(deep=True)
    frame["R1_station_id"] = frame["R1_station_id"].astype(str).str.strip()

    if frame.duplicated(["time_index", "R1_station_id"]).any():
        raise ServiceLayerContractError("Trajectory contains duplicate time/R1 ID rows")

    numeric_time = pd.to_numeric(frame["time_index"], errors="coerce")
    if numeric_time.isna().any() or not np.isfinite(numeric_time).all():
        raise ServiceLayerContractError("time_index must be finite numeric values")
    frame["time_index"] = numeric_time
    row_time = frame["time_index"].to_numpy()
    if len(row_time) > 1 and np.any(np.diff(row_time) < 0):
        raise ServiceLayerContractError("time_index blocks must be strictly ordered")
    time_indices = list(pd.unique(frame["time_index"]))
    if len(time_indices) < 1 or any(
        later <= earlier for earlier, later in zip(time_indices, time_indices[1:])
    ):
        raise ServiceLayerContractError("time_index values must be unique and strictly increasing")

    values = pd.to_numeric(frame["effective_state_value"], errors="coerce")
    if values.isna().any() or not np.isfinite(values).all():
        raise ServiceLayerContractError("effective states must be finite")
    if not values.between(0.0, 1.0).all():
        raise ServiceLayerContractError("identified state values must be within [0, 1]")
    frame["effective_state_value"] = values.astype(float)

    identified_text = frame["state_identified"].astype(str).str.strip().str.lower()
    allowed_boolean = {"true", "false", "1", "0", "yes", "no", "y", "n"}
    if not set(identified_text).issubset(allowed_boolean):
        raise ServiceLayerContractError("state_identified contains invalid Boolean values")
    frame["state_identified"] = identified_text.isin({"true", "1", "yes", "y"})

    expected_set = set(expected_ids)
    for time_index, block in frame.groupby("time_index", sort=False):
        block_ids = list(block["R1_station_id"])
        if len(block_ids) != len(expected_ids) or set(block_ids) != expected_set:
            missing = sorted(expected_set - set(block_ids))
            unknown = sorted(set(block_ids) - expected_set)
            raise ServiceLayerContractError(
                f"time {time_index} R1 membership mismatch; missing={missing}, unknown={unknown}"
            )

    serialized = frame.pivot(index="time_index", columns="R1_station_id", values="effective_state_value")
    identified = frame.pivot(index="time_index", columns="R1_station_id", values="state_identified")
    serialized = serialized.reindex(index=time_indices, columns=expected_ids)
    identified = identified.reindex(index=time_indices, columns=expected_ids).astype(bool)

    first_mask = identified.iloc[0]
    if not identified.eq(first_mask, axis="columns").all().all():
        raise ServiceLayerContractError("identified/missing mask changes across time")

    if expected_identified_mask is not None:
        expected_mask = expected_identified_mask.copy()
        expected_mask.index = expected_mask.index.astype(str)
        expected_mask = expected_mask.reindex(expected_ids)
        if expected_mask.isna().any() or not first_mask.equals(expected_mask.astype(bool)):
            raise ServiceLayerContractError("identified/missing mask does not match frozen T0")

    semantic = serialized.where(identified, np.nan)
    return ValidatedTrajectory(
        serialized_values=serialized.copy(),
        identified_mask=identified.copy(),
        semantic_states=semantic.copy(),
    )


def validate_service_attachment_ledger(
    attachment_ledger: pd.DataFrame,
    expected_service_ids: Iterable[object],
    expected_r1_ids: Iterable[object],
) -> pd.DataFrame:
    """Validate the one-upstream A/B and zero-upstream C attachment contract."""

    _required_columns(
        attachment_ledger,
        {"service_node_id", "attachment_class", "selected_upstream_R1_id"},
        "attachment ledger",
    )
    service_ids = _string_ids(expected_service_ids)
    r1_ids = set(_string_ids(expected_r1_ids))
    ledger = attachment_ledger.copy(deep=True)
    ledger["service_node_id"] = ledger["service_node_id"].astype(str).str.strip()
    ledger["attachment_class"] = ledger["attachment_class"].astype(str).str.strip()
    ledger["selected_upstream_R1_id"] = ledger["selected_upstream_R1_id"].astype(str).str.strip()

    if ledger["service_node_id"].duplicated().any():
        raise ServiceLayerContractError("Attachment ledger contains duplicate service IDs")
    if set(ledger["service_node_id"]) != set(service_ids) or len(ledger) != len(service_ids):
        raise ServiceLayerContractError("Attachment ledger does not contain the exact service ID set")
    if not set(ledger["attachment_class"]).issubset(ATTACHMENT_CLASSES):
        raise ServiceLayerContractError("Attachment ledger contains an unknown attachment class")

    multi_pattern = re.compile(r"[|;,]\s*\S")
    for row in ledger.itertuples(index=False):
        upstream = row.selected_upstream_R1_id
        if row.attachment_class in {ATTACHMENT_A, ATTACHMENT_B}:
            if not upstream:
                raise ServiceLayerContractError(
                    f"A/B service node {row.service_node_id} must have exactly one upstream R1 ID"
                )
            if multi_pattern.search(upstream):
                raise ServiceLayerContractError(
                    f"A/B service node {row.service_node_id} has multiple upstream R1 IDs"
                )
            if upstream not in r1_ids:
                raise ServiceLayerContractError(
                    f"A/B service node {row.service_node_id} references unknown R1 ID {upstream}"
                )
        elif upstream:
            raise ServiceLayerContractError(
                f"Class C service node {row.service_node_id} must not have an upstream R1 ID"
            )

    return ledger.set_index("service_node_id").reindex(service_ids).copy()


def propagate_network_state_to_service_layer(
    network_states: pd.DataFrame,
    attachment_ledger: pd.DataFrame,
) -> pd.DataFrame:
    """Apply the frozen A/B lookup and Class C missing-state rules."""

    service_ids = list(attachment_ledger.index.astype(str))
    service = pd.DataFrame(np.nan, index=network_states.index, columns=service_ids, dtype=float)
    for service_id, row in attachment_ledger.iterrows():
        if row["attachment_class"] == ATTACHMENT_C:
            continue
        upstream_id = row["selected_upstream_R1_id"]
        if upstream_id not in network_states.columns:
            raise ServiceLayerContractError(
                f"Service node {service_id} references unavailable upstream R1 ID {upstream_id}"
            )
        service[service_id] = network_states[upstream_id]
    return service


def validate_w1(
    w1: pd.DataFrame,
    expected_service_ids: Iterable[object],
    tolerance: float = W1_SERIALIZATION_TOLERANCE,
) -> pd.DataFrame:
    """Validate the complete, nonnegative tract-by-service candidate matrix."""

    if "tract_id" not in w1.columns:
        raise ServiceLayerContractError("W1 is missing tract_id")
    service_ids = _string_ids(expected_service_ids)
    frame = w1.copy(deep=True)
    frame["tract_id"] = frame["tract_id"].astype(str).str.strip()
    if frame["tract_id"].duplicated().any() or (frame["tract_id"] == "").any():
        raise ServiceLayerContractError("W1 tract IDs must be unique and nonempty")
    missing_columns = set(service_ids) - set(frame.columns)
    extra_service_columns = {
        column for column in frame.columns if str(column).startswith("SCE-SVC-")
    } - set(service_ids)
    if missing_columns or extra_service_columns:
        raise ServiceLayerContractError(
            f"W1 service columns mismatch; missing={sorted(missing_columns)}, extra={sorted(extra_service_columns)}"
        )
    matrix = frame.set_index("tract_id")[service_ids].apply(pd.to_numeric, errors="coerce")
    if matrix.isna().any().any() or not np.isfinite(matrix.to_numpy()).all():
        raise ServiceLayerContractError("W1 contains missing or nonfinite values")
    if (matrix < 0).any().any():
        raise ServiceLayerContractError("W1 contains negative values")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=tolerance, rtol=0.0):
        raise ServiceLayerContractError("W1 row sums violate the unit-mass contract")
    return matrix.copy()


def aggregate_service_states_to_tract_intervals(
    service_states: pd.DataFrame,
    w1: pd.DataFrame,
    tract_metadata: pd.DataFrame,
    tolerance: float = DEFAULT_TOLERANCE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate service states to partially identified tract intervals.

    Any missing service state, whether Class C or a missing upstream A/B state,
    remains candidate mass in the interval width. W1 is never renormalized.
    """

    service_ids = list(service_states.columns.astype(str))
    w1_tolerance = max(tolerance, W1_SERIALIZATION_TOLERANCE)
    matrix = validate_w1(w1, service_ids, tolerance=w1_tolerance)
    _required_columns(tract_metadata, {"tract_id", "population"}, "tract metadata")
    metadata = tract_metadata.copy(deep=True)
    metadata["tract_id"] = metadata["tract_id"].astype(str).str.strip()
    if metadata["tract_id"].duplicated().any():
        raise ServiceLayerContractError("Tract metadata contains duplicate tract IDs")
    if set(metadata["tract_id"]) != set(matrix.index) or len(metadata) != len(matrix):
        raise ServiceLayerContractError("Tract metadata does not match the W1 tract set")
    metadata = metadata.set_index("tract_id").reindex(matrix.index)
    population = pd.to_numeric(metadata["population"], errors="coerce")
    if population.isna().any() or not np.isfinite(population).all() or (population < 0).any():
        raise ServiceLayerContractError("Population must be finite and nonnegative")
    if population.sum() <= 0:
        raise ServiceLayerContractError("Population total must be positive")

    records = []
    for time_index, state_row in service_states.iterrows():
        identified = state_row.notna().to_numpy()
        missing = ~identified
        if identified.any():
            identified_values = state_row.to_numpy(dtype=float)[identified]
            if not np.isfinite(identified_values).all() or not (
                (identified_values >= 0.0) & (identified_values <= 1.0)
            ).all():
                raise ServiceLayerContractError("Identified service states must be finite in [0, 1]")
        resolved_mass = matrix.to_numpy()[:, identified].sum(axis=1)
        unresolved_mass = matrix.to_numpy()[:, missing].sum(axis=1)
        known_available = (
            matrix.to_numpy()[:, identified] @ state_row.to_numpy(dtype=float)[identified]
            if identified.any()
            else np.zeros(len(matrix))
        )
        lower = known_available
        upper = known_available + unresolved_mass
        conditional = np.divide(
            known_available,
            resolved_mass,
            out=np.full(len(matrix), np.nan),
            where=resolved_mass > 0,
        )
        for position, tract_id in enumerate(matrix.index):
            records.append(
                {
                    "time_index": time_index,
                    "tract_id": tract_id,
                    "population": float(population.loc[tract_id]),
                    "resolved_mass": float(resolved_mass[position]),
                    "unresolved_mass": float(unresolved_mass[position]),
                    "known_available_mass": float(known_available[position]),
                    "lower": float(lower[position]),
                    "upper": float(upper[position]),
                    "width": float(upper[position] - lower[position]),
                    "conditional_resolved_availability_diagnostic": float(conditional[position]),
                }
            )

    intervals = pd.DataFrame(records)
    if not np.allclose(
        intervals["resolved_mass"] + intervals["unresolved_mass"],
        1.0,
        atol=w1_tolerance,
        rtol=0.0,
    ):
        raise ServiceLayerContractError("Resolved and unresolved tract mass do not sum to one")

    aggregate_records = []
    for time_index, block in intervals.groupby("time_index", sort=False):
        weights = block["population"].to_numpy()
        aggregate_records.append(
            {
                "time_index": time_index,
                "population_weighted_lower": float(np.average(block["lower"], weights=weights)),
                "population_weighted_upper": float(np.average(block["upper"], weights=weights)),
                "population_weighted_width": float(np.average(block["width"], weights=weights)),
            }
        )
    aggregate = pd.DataFrame(aggregate_records)
    return intervals, aggregate


def evaluate_service_layer_trajectory(
    trajectory: pd.DataFrame,
    service_attachment_ledger: pd.DataFrame,
    w1: pd.DataFrame,
    tract_metadata: pd.DataFrame,
    expected_r1_ids: Iterable[object],
    expected_service_ids: Iterable[object],
    expected_identified_mask: pd.Series | None = None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> ServiceLayerEvaluation:
    """Single production entry point for Architecture B trajectory evaluation."""

    validated_trajectory = load_validate_r1_effective_state_trajectory(
        trajectory,
        expected_r1_ids,
        expected_identified_mask=expected_identified_mask,
    )
    validated_attachments = validate_service_attachment_ledger(
        service_attachment_ledger,
        expected_service_ids,
        expected_r1_ids,
    )
    service = propagate_network_state_to_service_layer(
        validated_trajectory.semantic_states,
        validated_attachments,
    )
    intervals, aggregate = aggregate_service_states_to_tract_intervals(
        service,
        w1,
        tract_metadata,
        tolerance=tolerance,
    )
    return ServiceLayerEvaluation(
        network_trajectory=validated_trajectory.semantic_states.copy(),
        network_identified_mask=validated_trajectory.identified_mask.copy(),
        service_trajectory=service.copy(),
        tract_intervals=intervals.copy(),
        aggregate_intervals=aggregate.copy(),
    )
