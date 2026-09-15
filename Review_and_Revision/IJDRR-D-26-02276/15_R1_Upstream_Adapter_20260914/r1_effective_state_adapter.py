"""Read-only schema adapter for retained R1 effective-state snapshots.

The adapter changes representation only. It does not calculate an upstream
state, source connectivity, topology, damage, repair, or recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


NATIVE_SCHEMA_NAME = "R1_STATIC_EFFECTIVE_STATE_SNAPSHOT_V1"
NATIVE_SCHEMA_DEFINITION = {
    "schema_name": NATIVE_SCHEMA_NAME,
    "record_selector": {"record_type": "R1_NETWORK_ASSET"},
    "station_id_column": "record_id",
    "state_column": "effective_no_damage_network_state",
    "missing_encoding": "empty field or dataframe NA; numeric zero is identified",
    "native_time": "one implicit static snapshot; sequence time is supplied by an outer envelope",
    "sequence_envelope_columns": [
        "native_snapshot_time_index",
        "source_time",
        "source_time_unit",
    ],
    "canonical_output_order": "time_index then caller-supplied frozen R1 ID order",
}

STANDARD_COLUMNS = [
    "time_index",
    "R1_station_id",
    "effective_state_value",
    "state_identified",
    "source_time",
    "source_time_unit",
]
AMBIGUOUS_MISSING_TOKENS = {"na", "n/a", "nan", "null", "none", "unknown", "missing"}


class R1EffectiveStateAdapterError(ValueError):
    """Raised when a native R1 artifact violates the adapter contract."""


@dataclass(frozen=True)
class NativeR1Snapshot:
    """One native effective-state frame plus explicit outer time provenance."""

    frame: pd.DataFrame
    time_index: float | int
    source_time: object
    source_time_unit: str


def native_schema_sha256() -> str:
    """Return the hash of the canonical native-schema definition."""

    payload = json.dumps(
        NATIVE_SCHEMA_DEFINITION,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _frozen_ids(values: Iterable[object]) -> list[str]:
    ids = [str(value).strip() for value in values]
    if not ids or any(not value for value in ids):
        raise R1EffectiveStateAdapterError("Frozen R1 IDs must be nonempty")
    if len(ids) != len(set(ids)):
        raise R1EffectiveStateAdapterError("Frozen R1 ID list contains duplicates")
    return ids


def _required_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = required - set(frame.columns)
    if missing:
        raise R1EffectiveStateAdapterError(f"{label} is missing columns: {sorted(missing)}")


def _numeric_time(value: object) -> float | int:
    converted = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(converted) or not np.isfinite(converted):
        raise R1EffectiveStateAdapterError("time_index must be finite and numeric")
    return converted


def _parse_native_snapshot(
    frame: pd.DataFrame,
    expected_r1_ids: list[str],
) -> tuple[pd.Series, pd.Series]:
    _required_columns(
        frame,
        {"record_type", "record_id", "effective_no_damage_network_state"},
        "native R1 snapshot",
    )
    native = frame.copy(deep=True)
    native["record_type"] = native["record_type"].astype(str).str.strip()
    native = native.loc[native["record_type"].eq("R1_NETWORK_ASSET")].copy()
    native["record_id"] = native["record_id"].astype(str).str.strip()

    if native.empty:
        raise R1EffectiveStateAdapterError("Native snapshot has no R1_NETWORK_ASSET rows")
    if native["record_id"].duplicated().any():
        raise R1EffectiveStateAdapterError("Native snapshot contains duplicate R1 station IDs")

    actual = set(native["record_id"])
    expected = set(expected_r1_ids)
    if len(native) != len(expected_r1_ids) or actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise R1EffectiveStateAdapterError(
            f"Unexpected station set; missing={missing}, unknown={unknown}"
        )

    raw_state = native.set_index("record_id")["effective_no_damage_network_state"].reindex(
        expected_r1_ids
    )
    text = raw_state.astype(str).str.strip()
    explicit_missing = raw_state.isna() | text.eq("")
    ambiguous = text.str.lower().isin(AMBIGUOUS_MISSING_TOKENS) & ~explicit_missing
    if ambiguous.any():
        bad_ids = list(raw_state.index[ambiguous])
        raise R1EffectiveStateAdapterError(
            f"Ambiguous missing sentinel in effective state for R1 IDs {bad_ids}"
        )

    numeric = pd.to_numeric(raw_state.where(~explicit_missing), errors="coerce")
    nonnumeric = numeric.isna() & ~explicit_missing
    if nonnumeric.any():
        bad_ids = list(raw_state.index[nonnumeric])
        raise R1EffectiveStateAdapterError(
            f"Non-numeric effective state for R1 IDs {bad_ids}"
        )
    identified_values = numeric.loc[~explicit_missing]
    if not np.isfinite(identified_values.to_numpy(dtype=float)).all():
        raise R1EffectiveStateAdapterError("Identified effective states must be finite")
    if not identified_values.between(0.0, 1.0).all():
        raise R1EffectiveStateAdapterError("Identified effective states must be within [0, 1]")

    identified = (~explicit_missing).astype(bool)
    serialized = numeric.fillna(0.0).astype(float)
    return serialized, identified


def adapt_native_r1_effective_state_snapshots(
    snapshots: Iterable[NativeR1Snapshot],
    expected_r1_ids: Iterable[object],
) -> pd.DataFrame:
    """Convert native snapshots to the production trajectory schema.

    The finite value ``0.0`` used on a missing serialized row is only a storage
    placeholder. ``state_identified=False`` preserves the semantic missingness,
    and the production loader restores that row to NA.
    """

    expected_ids = _frozen_ids(expected_r1_ids)
    snapshot_list = list(snapshots)
    if not snapshot_list:
        raise R1EffectiveStateAdapterError("At least one native snapshot is required")

    numeric_times = [_numeric_time(snapshot.time_index) for snapshot in snapshot_list]
    if any(later <= earlier for earlier, later in zip(numeric_times, numeric_times[1:])):
        raise R1EffectiveStateAdapterError("Snapshot time indices must be unique and strictly increasing")

    output_blocks: list[pd.DataFrame] = []
    for snapshot, time_index in zip(snapshot_list, numeric_times):
        source_time_unit = str(snapshot.source_time_unit).strip()
        if not source_time_unit:
            raise R1EffectiveStateAdapterError("source_time_unit must be nonempty")
        if snapshot.source_time is None or str(snapshot.source_time).strip() == "":
            raise R1EffectiveStateAdapterError("source_time must be explicitly supplied")
        serialized, identified = _parse_native_snapshot(snapshot.frame, expected_ids)
        output_blocks.append(
            pd.DataFrame(
                {
                    "time_index": time_index,
                    "R1_station_id": expected_ids,
                    "effective_state_value": serialized.to_numpy(dtype=float),
                    "state_identified": identified.to_numpy(dtype=bool),
                    "source_time": snapshot.source_time,
                    "source_time_unit": source_time_unit,
                }
            )
        )
    return pd.concat(output_blocks, ignore_index=True)[STANDARD_COLUMNS]


def adapt_native_r1_effective_state_table(
    native_table: pd.DataFrame,
    expected_r1_ids: Iterable[object],
    *,
    time_index: float | int,
    source_time: object,
    source_time_unit: str,
) -> pd.DataFrame:
    """Adapt one retained native static snapshot without modifying its state."""

    return adapt_native_r1_effective_state_snapshots(
        [
            NativeR1Snapshot(
                frame=native_table,
                time_index=time_index,
                source_time=source_time,
                source_time_unit=source_time_unit,
            )
        ],
        expected_r1_ids,
    )


def load_native_r1_effective_state_csv(
    path: str | Path,
    expected_r1_ids: Iterable[object],
    *,
    time_index: float | int,
    source_time: object,
    source_time_unit: str,
) -> pd.DataFrame:
    """Read one native CSV and return a contract-ready read-only adaptation."""

    native = pd.read_csv(path, keep_default_na=False, dtype={"record_id": str})
    return adapt_native_r1_effective_state_table(
        native,
        expected_r1_ids,
        time_index=time_index,
        source_time=source_time,
        source_time_unit=source_time_unit,
    )


def adapt_native_r1_effective_state_envelope(
    envelope: pd.DataFrame,
    expected_r1_ids: Iterable[object],
) -> pd.DataFrame:
    """Adapt a sequence envelope whose inner rows use the retained native schema.

    The three envelope columns provide time provenance that the retained static
    native artifact does not contain. They do not alter the inner state values.
    """

    required_envelope = {
        "native_snapshot_time_index",
        "source_time",
        "source_time_unit",
        "record_type",
        "record_id",
        "effective_no_damage_network_state",
    }
    _required_columns(envelope, required_envelope, "native snapshot envelope")
    frame = envelope.copy(deep=True)
    numeric_time = pd.to_numeric(frame["native_snapshot_time_index"], errors="coerce")
    if numeric_time.isna().any() or not np.isfinite(numeric_time).all():
        raise R1EffectiveStateAdapterError("Envelope time indices must be finite and numeric")
    frame["native_snapshot_time_index"] = numeric_time

    block_start = frame["native_snapshot_time_index"].ne(
        frame["native_snapshot_time_index"].shift()
    )
    block_times = frame.loc[block_start, "native_snapshot_time_index"].tolist()
    if len(block_times) != len(set(block_times)):
        raise R1EffectiveStateAdapterError("Envelope contains a duplicate, discontiguous time block")
    if any(later <= earlier for earlier, later in zip(block_times, block_times[1:])):
        raise R1EffectiveStateAdapterError("Envelope time blocks must be strictly increasing")

    snapshots: list[NativeR1Snapshot] = []
    for time_index, block in frame.groupby("native_snapshot_time_index", sort=False):
        source_times = block["source_time"].drop_duplicates().tolist()
        source_units = block["source_time_unit"].drop_duplicates().tolist()
        if len(source_times) != 1 or len(source_units) != 1:
            raise R1EffectiveStateAdapterError(
                f"Time block {time_index} has inconsistent source-time provenance"
            )
        native_columns = [
            column
            for column in block.columns
            if column not in {"native_snapshot_time_index", "source_time", "source_time_unit"}
        ]
        snapshots.append(
            NativeR1Snapshot(
                frame=block[native_columns].copy(),
                time_index=time_index,
                source_time=source_times[0],
                source_time_unit=str(source_units[0]),
            )
        )
    return adapt_native_r1_effective_state_snapshots(snapshots, expected_r1_ids)
