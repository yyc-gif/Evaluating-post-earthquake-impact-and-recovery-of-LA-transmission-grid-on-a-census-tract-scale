"""Producer-side serializer for R1 effective network state trajectories.

This module accepts state and identifiability matrices that have already been
computed upstream. It validates, orders, and serializes them. It contains no
scientific state calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable, Mapping

import numpy as np
import pandas as pd


SCHEMA_VERSION = "R1_EFFECTIVE_STATE_EXPORT_V1"
EFFECTIVE_STATE_SEMANTICS = "post_source_component_gate_effective_network_state"
REQUIRED_PROVENANCE_FIELDS = {
    "schema_version",
    "trajectory_id",
    "producer_file",
    "producer_function",
    "effective_state_semantics",
    "frozen_R1_ID_hash",
    "source_time_unit",
    "source_scenario_identifier",
    "producer_code_hash",
}


class R1EffectiveStateExportError(ValueError):
    """Raised when producer output violates the export contract."""


@dataclass(frozen=True)
class R1EffectiveStateExport:
    """Canonical trajectory plus validated trajectory-level provenance."""

    trajectory: pd.DataFrame
    provenance: dict[str, str]


def hash_frozen_r1_ids(r1_ids: Iterable[object]) -> str:
    """Hash the ordered, newline-terminated frozen R1 identity list."""

    ids = _normalize_expected_ids(r1_ids)
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def canonical_trajectory_sha256(trajectory: pd.DataFrame) -> str:
    """Hash the canonical six-column CSV representation."""

    columns = [
        "time_index",
        "R1_station_id",
        "effective_state_value",
        "state_identified",
        "source_time",
        "source_time_unit",
    ]
    missing = set(columns) - set(trajectory.columns)
    if missing:
        raise R1EffectiveStateExportError(
            f"Cannot hash trajectory; missing columns: {sorted(missing)}"
        )
    payload = trajectory[columns].to_csv(
        index=False,
        lineterminator="\n",
        float_format="%.17g",
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalize_expected_ids(values: Iterable[object]) -> list[str]:
    ids = [str(value).strip() for value in values]
    if not ids or any(not value for value in ids):
        raise R1EffectiveStateExportError("Frozen R1 IDs must be nonempty")
    if len(ids) != len(set(ids)):
        raise R1EffectiveStateExportError("Frozen R1 ID list contains duplicates")
    return ids


def _validate_matrix_identity(
    frame: pd.DataFrame,
    expected_ids: list[str],
    label: str,
) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise R1EffectiveStateExportError(f"{label} must be a pandas DataFrame")
    if frame.empty:
        raise R1EffectiveStateExportError(f"{label} must contain at least one time row")
    if frame.index.has_duplicates:
        raise R1EffectiveStateExportError(f"{label} has duplicate trajectory time labels")
    if frame.columns.has_duplicates:
        raise R1EffectiveStateExportError(f"{label} has duplicate station columns")

    normalized_columns = [str(column).strip() for column in frame.columns]
    if any(not value for value in normalized_columns):
        raise R1EffectiveStateExportError(f"{label} has an empty station ID")
    if len(normalized_columns) != len(set(normalized_columns)):
        raise R1EffectiveStateExportError(
            f"{label} station IDs collide after string normalization"
        )
    actual = set(normalized_columns)
    expected = set(expected_ids)
    if len(normalized_columns) != len(expected_ids) or actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise R1EffectiveStateExportError(
            f"{label} station set mismatch; missing={missing}, unknown={unknown}"
        )

    result = frame.copy(deep=True)
    result.columns = normalized_columns
    return result.reindex(columns=expected_ids)


def _validate_boolean_mask(mask: pd.DataFrame) -> pd.DataFrame:
    values = mask.to_numpy(dtype=object)
    valid = np.vectorize(lambda value: isinstance(value, (bool, np.bool_)))(values)
    if not valid.all():
        raise R1EffectiveStateExportError(
            "state_identified must contain explicit Boolean values only"
        )
    return mask.astype(bool)


def _validate_source_time(source_time: Iterable[object], n_time: int) -> list[object]:
    values = list(source_time)
    if len(values) != n_time:
        raise R1EffectiveStateExportError(
            f"source_time length {len(values)} does not match trajectory length {n_time}"
        )
    index = pd.Index(values)
    if index.hasnans:
        raise R1EffectiveStateExportError("source_time contains missing values")
    if not index.is_unique:
        raise R1EffectiveStateExportError("source_time contains duplicate values")
    try:
        monotonic = index.is_monotonic_increasing
    except TypeError as exc:
        raise R1EffectiveStateExportError("source_time values are not order-comparable") from exc
    if not monotonic:
        raise R1EffectiveStateExportError("source_time must be strictly increasing")
    return values


def _validate_provenance(
    provenance: Mapping[str, object],
    expected_id_hash: str,
    source_time_unit: str,
) -> dict[str, str]:
    missing = REQUIRED_PROVENANCE_FIELDS - set(provenance)
    if missing:
        raise R1EffectiveStateExportError(
            f"Provenance is missing fields: {sorted(missing)}"
        )
    output = {key: str(provenance[key]).strip() for key in REQUIRED_PROVENANCE_FIELDS}
    empty = sorted(key for key, value in output.items() if not value)
    if empty:
        raise R1EffectiveStateExportError(f"Provenance has empty fields: {empty}")
    if output["schema_version"] != SCHEMA_VERSION:
        raise R1EffectiveStateExportError("Provenance schema_version is not R1_EFFECTIVE_STATE_EXPORT_V1")
    if output["effective_state_semantics"] != EFFECTIVE_STATE_SEMANTICS:
        raise R1EffectiveStateExportError("Provenance effective-state semantics are incompatible")
    if output["frozen_R1_ID_hash"] != expected_id_hash:
        raise R1EffectiveStateExportError("Provenance frozen R1 ID hash does not match input IDs")
    if output["source_time_unit"] != source_time_unit:
        raise R1EffectiveStateExportError("Provenance source_time_unit does not match the export call")
    return output


def export_r1_effective_state_trajectory(
    effective_state: pd.DataFrame,
    state_identified: pd.DataFrame,
    source_time: Iterable[object],
    source_time_unit: str,
    frozen_r1_ids: Iterable[object],
    provenance: Mapping[str, object],
) -> R1EffectiveStateExport:
    """Validate and serialize an already-computed effective R1 trajectory.

    ``effective_state`` and ``state_identified`` are dual authoritative input
    channels with shape T x N and explicit station-ID columns. Station columns
    may arrive in different orders because labels permit safe alignment. Their
    time-label indices must match exactly. Output ``time_index`` is the ordinal
    row index; the producer's true timeline remains in ``source_time``.

    A masked cell may contain NA or the inert numeric placeholder zero. A masked
    nonzero value is rejected as an internal producer inconsistency.
    """

    expected_ids = _normalize_expected_ids(frozen_r1_ids)
    if len(expected_ids) != 310:
        raise R1EffectiveStateExportError(
            f"R1_EFFECTIVE_STATE_EXPORT_V1 requires exactly 310 frozen IDs, got {len(expected_ids)}"
        )

    state = _validate_matrix_identity(effective_state, expected_ids, "effective_state")
    mask = _validate_matrix_identity(state_identified, expected_ids, "state_identified")
    if state.shape != mask.shape:
        raise R1EffectiveStateExportError("effective_state and state_identified shapes differ")
    if not state.index.equals(mask.index):
        raise R1EffectiveStateExportError(
            "effective_state and state_identified time identities/order differ"
        )
    mask = _validate_boolean_mask(mask)

    numeric_state = state.apply(pd.to_numeric, errors="coerce")
    raw_missing = state.isna() | state.astype(str).apply(lambda col: col.str.strip().eq(""))
    identified = mask.to_numpy(dtype=bool)
    numeric_values = numeric_state.to_numpy(dtype=float)
    missing_values = raw_missing.to_numpy(dtype=bool)

    invalid_identified = identified & (missing_values | ~np.isfinite(numeric_values))
    if invalid_identified.any():
        raise R1EffectiveStateExportError(
            "An identified state is missing, nonnumeric, or nonfinite"
        )
    identified_values = numeric_values[identified]
    if ((identified_values < 0.0) | (identified_values > 1.0)).any():
        raise R1EffectiveStateExportError("Identified states must be within [0, 1]")

    masked_nonzero = (~identified) & ~missing_values & (
        ~np.isfinite(numeric_values) | ~np.isclose(numeric_values, 0.0, rtol=0.0, atol=0.0)
    )
    if masked_nonzero.any():
        raise R1EffectiveStateExportError(
            "A state_identified=False cell contains a nonzero or nonfinite numeric value"
        )

    unit = str(source_time_unit).strip()
    if not unit:
        raise R1EffectiveStateExportError("source_time_unit must be explicitly provided")
    source_times = _validate_source_time(source_time, len(state))
    id_hash = hash_frozen_r1_ids(expected_ids)
    validated_provenance = _validate_provenance(provenance, id_hash, unit)

    serialized = np.where(identified, numeric_values, 0.0)
    records: list[pd.DataFrame] = []
    for time_index, source_value in enumerate(source_times):
        records.append(
            pd.DataFrame(
                {
                    "time_index": time_index,
                    "R1_station_id": expected_ids,
                    "effective_state_value": serialized[time_index, :],
                    "state_identified": identified[time_index, :],
                    "source_time": source_value,
                    "source_time_unit": unit,
                }
            )
        )
    trajectory = pd.concat(records, ignore_index=True)
    validated_provenance["trajectory_sha256"] = canonical_trajectory_sha256(trajectory)
    validated_provenance["time_count"] = str(len(state))
    validated_provenance["station_count"] = str(len(expected_ids))
    return R1EffectiveStateExport(
        trajectory=trajectory,
        provenance=validated_provenance,
    )


def provenance_sha256(provenance: Mapping[str, object]) -> str:
    """Hash a canonical producer-side provenance sidecar."""

    payload = json.dumps(
        {str(key): str(value) for key, value in provenance.items()},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
