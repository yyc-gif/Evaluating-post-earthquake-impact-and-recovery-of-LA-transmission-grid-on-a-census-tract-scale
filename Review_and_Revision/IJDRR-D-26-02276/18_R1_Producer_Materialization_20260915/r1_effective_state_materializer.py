"""Materialize already-computed R1 realization segments without science logic.

Every appended segment must already contain post-source/component-gate state
and its producer-authoritative identified mask. This module validates explicit
identity and coverage, then assembles one complete T x 310 producer object. It
does not calculate, export, or write any state.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, Mapping, Optional

import numpy as np
import pandas as pd


REALIZATION_SCOPE = "realization"
REQUIRED_PROVENANCE_FIELDS = {
    "scenario_id",
    "strategy_id",
    "realization_id",
    "trajectory_scope",
    "source_time_unit",
    "frozen_R1_ID_hash",
}


class R1RealizationMaterializationError(ValueError):
    """Raised when a segment or realization violates the materialization contract."""


@dataclass(frozen=True)
class R1MaterializedRealization:
    """Complete producer object ready for the disabled wiring boundary."""

    effective_state: pd.DataFrame
    state_identified: pd.DataFrame
    source_time: tuple[object, ...]
    source_time_unit: str
    frozen_r1_ids: tuple[str, ...]
    provenance: dict[str, object]


def _normalize_frozen_ids(values: Iterable[object]) -> tuple[str, ...]:
    ids = tuple(str(value).strip() for value in values)
    if len(ids) != 310:
        raise R1RealizationMaterializationError(
            f"Materialization requires exactly 310 frozen R1 IDs, got {len(ids)}"
        )
    if any(not value for value in ids):
        raise R1RealizationMaterializationError("Frozen R1 IDs must be nonempty")
    if len(set(ids)) != len(ids):
        raise R1RealizationMaterializationError("Frozen R1 IDs contain duplicates")
    return ids


def _validate_source_time(values: Iterable[object]) -> tuple[object, ...]:
    source_time = tuple(values)
    if not source_time:
        raise R1RealizationMaterializationError("source_time must not be empty")
    index = pd.Index(source_time)
    if index.hasnans:
        raise R1RealizationMaterializationError("source_time contains missing values")
    if not index.is_unique:
        raise R1RealizationMaterializationError("source_time contains duplicates")
    try:
        monotonic = index.is_monotonic_increasing
    except TypeError as exc:
        raise R1RealizationMaterializationError(
            "source_time values are not order-comparable"
        ) from exc
    if not monotonic:
        raise R1RealizationMaterializationError(
            "source_time must be strictly increasing"
        )
    return source_time


def _validate_provenance(
    provenance: Mapping[str, object],
    source_time_unit: str,
    frozen_ids: tuple[str, ...],
) -> dict[str, object]:
    if not isinstance(provenance, Mapping):
        raise R1RealizationMaterializationError("provenance must be a mapping")
    missing = REQUIRED_PROVENANCE_FIELDS - set(provenance)
    if missing:
        raise R1RealizationMaterializationError(
            f"Realization provenance is missing fields: {sorted(missing)}"
        )
    output = dict(provenance)
    empty = [
        field
        for field in REQUIRED_PROVENANCE_FIELDS
        if output[field] is None or not str(output[field]).strip()
    ]
    if empty:
        raise R1RealizationMaterializationError(
            f"Realization provenance has empty fields: {sorted(empty)}"
        )
    if str(output["trajectory_scope"]).strip() != REALIZATION_SCOPE:
        raise R1RealizationMaterializationError(
            "trajectory_scope must be 'realization'; aggregate objects are forbidden"
        )
    if str(output["source_time_unit"]).strip() != source_time_unit:
        raise R1RealizationMaterializationError(
            "provenance source_time_unit does not match materializer input"
        )
    expected_hash = hashlib.sha256(
        ("\n".join(frozen_ids) + "\n").encode("utf-8")
    ).hexdigest()
    if str(output["frozen_R1_ID_hash"]).strip() != expected_hash:
        raise R1RealizationMaterializationError(
            "provenance frozen R1 ID hash does not match materializer IDs"
        )
    return output


def _normalize_segment_columns(
    frame: pd.DataFrame, frozen_ids: tuple[str, ...], label: str
) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise R1RealizationMaterializationError(
            f"{label} must be a pandas DataFrame with explicit station IDs"
        )
    if frame.columns.has_duplicates:
        raise R1RealizationMaterializationError(f"{label} has duplicate station IDs")
    columns = [str(value).strip() for value in frame.columns]
    if any(not value for value in columns):
        raise R1RealizationMaterializationError(f"{label} has an empty station ID")
    if len(columns) != len(set(columns)):
        raise R1RealizationMaterializationError(
            f"{label} station IDs collide after normalization"
        )
    actual = set(columns)
    expected = set(frozen_ids)
    if len(columns) != len(frozen_ids) or actual != expected:
        raise R1RealizationMaterializationError(
            f"{label} station set mismatch; "
            f"missing={sorted(expected - actual)}, unknown={sorted(actual - expected)}"
        )
    result = frame.copy(deep=True)
    result.columns = columns
    return result.reindex(columns=list(frozen_ids))


def _validate_boolean_mask(mask: pd.DataFrame) -> pd.DataFrame:
    values = mask.to_numpy(dtype=object)
    valid = np.vectorize(lambda value: isinstance(value, (bool, np.bool_)))(values)
    if not valid.all():
        raise R1RealizationMaterializationError(
            "state_identified must contain explicit Boolean values only"
        )
    return mask.astype(bool)


def _validate_segment_values(
    state: pd.DataFrame, mask: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    raw_missing = state.isna().to_numpy(dtype=bool)
    numeric = state.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    nonnumeric = np.isnan(numeric) & ~raw_missing
    if nonnumeric.any():
        raise R1RealizationMaterializationError(
            "effective_state contains a nonnumeric, nonmissing value"
        )

    identified = mask.to_numpy(dtype=bool)
    invalid_identified = identified & (raw_missing | ~np.isfinite(numeric))
    if invalid_identified.any():
        raise R1RealizationMaterializationError(
            "An identified state is missing or nonfinite"
        )
    values = numeric[identified]
    if ((values < 0.0) | (values > 1.0)).any():
        raise R1RealizationMaterializationError(
            "Identified states must be within [0, 1]"
        )

    invalid_masked = (~identified) & ~raw_missing & (
        ~np.isfinite(numeric)
        | ~np.isclose(numeric, 0.0, rtol=0.0, atol=0.0)
    )
    if invalid_masked.any():
        raise R1RealizationMaterializationError(
            "A state_identified=False cell contains a nonzero or nonfinite value"
        )
    return numeric, identified


class R1RealizationMaterializer:
    """Strictly assemble a single realization from contiguous full-width segments."""

    def __init__(
        self,
        *,
        frozen_r1_ids: Iterable[object],
        source_time: Iterable[object],
        source_time_unit: str,
        provenance: Mapping[str, object],
    ) -> None:
        self._frozen_r1_ids = _normalize_frozen_ids(frozen_r1_ids)
        self._source_time = _validate_source_time(source_time)
        self._source_time_unit = str(source_time_unit).strip()
        if not self._source_time_unit:
            raise R1RealizationMaterializationError(
                "source_time_unit must be explicitly provided"
            )
        self._provenance = _validate_provenance(
            provenance, self._source_time_unit, self._frozen_r1_ids
        )

        shape = (len(self._source_time), len(self._frozen_r1_ids))
        self._effective_state = np.full(shape, np.nan, dtype=float)
        self._state_identified = np.zeros(shape, dtype=bool)
        self._coverage_written = np.zeros(shape, dtype=bool)
        self._next_time_start = 0
        self._finalized = False

    def append_segment(
        self,
        time_start: int,
        time_stop: int,
        effective_state_segment: pd.DataFrame,
        state_identified_segment: pd.DataFrame,
    ) -> None:
        """Append one explicit, contiguous, full-width segment."""

        if self._finalized:
            raise R1RealizationMaterializationError(
                "Cannot append after materialization has been finalized"
            )
        if not isinstance(time_start, (int, np.integer)) or not isinstance(
            time_stop, (int, np.integer)
        ):
            raise R1RealizationMaterializationError(
                "time_start and time_stop must be integer positions"
            )
        time_start = int(time_start)
        time_stop = int(time_stop)
        total_time = len(self._source_time)
        if time_start < 0 or time_stop > total_time or time_start >= time_stop:
            raise R1RealizationMaterializationError(
                f"Invalid segment interval [{time_start}, {time_stop}) for T={total_time}"
            )
        if time_start != self._next_time_start:
            raise R1RealizationMaterializationError(
                f"Segments must be contiguous and ordered; expected start "
                f"{self._next_time_start}, got {time_start}"
            )

        state = _normalize_segment_columns(
            effective_state_segment, self._frozen_r1_ids, "effective_state_segment"
        )
        mask = _normalize_segment_columns(
            state_identified_segment, self._frozen_r1_ids, "state_identified_segment"
        )
        if state.shape != mask.shape:
            raise R1RealizationMaterializationError(
                "State and mask segment shapes differ"
            )
        expected_rows = time_stop - time_start
        if len(state) != expected_rows:
            raise R1RealizationMaterializationError(
                f"Segment row count {len(state)} does not match interval length {expected_rows}"
            )
        if not state.index.equals(mask.index):
            raise R1RealizationMaterializationError(
                "State and mask segment time identities/order differ"
            )
        expected_index = pd.Index(self._source_time[time_start:time_stop])
        if not state.index.equals(expected_index):
            raise R1RealizationMaterializationError(
                "Segment row identity does not match the declared source_time slice"
            )

        mask = _validate_boolean_mask(mask)
        numeric, identified = _validate_segment_values(state, mask)
        if self._coverage_written[time_start:time_stop, :].any():
            raise R1RealizationMaterializationError(
                "Segment overlaps cells already written"
            )

        self._effective_state[time_start:time_stop, :] = numeric
        self._state_identified[time_start:time_stop, :] = identified
        self._coverage_written[time_start:time_stop, :] = True
        self._next_time_start = time_stop

    def finalize(self) -> R1MaterializedRealization:
        """Freeze and return the complete producer object exactly once."""

        if self._finalized:
            raise R1RealizationMaterializationError(
                "Materialization has already been finalized"
            )
        total_time = len(self._source_time)
        if self._next_time_start != total_time or not self._coverage_written.all():
            unwritten = int((~self._coverage_written).sum())
            raise R1RealizationMaterializationError(
                f"Cannot finalize incomplete realization; next_time_start="
                f"{self._next_time_start}, T={total_time}, unwritten_cells={unwritten}"
            )

        self._finalized = True
        index = pd.Index(self._source_time, name="source_time")
        columns = pd.Index(self._frozen_r1_ids, name="R1_station_id")
        state = pd.DataFrame(
            self._effective_state.copy(), index=index, columns=columns
        )
        mask = pd.DataFrame(
            self._state_identified.copy(), index=index, columns=columns
        )
        return R1MaterializedRealization(
            effective_state=state,
            state_identified=mask,
            source_time=self._source_time,
            source_time_unit=self._source_time_unit,
            frozen_r1_ids=self._frozen_r1_ids,
            provenance=dict(self._provenance),
        )


def create_r1_realization_materializer(
    *,
    enabled: bool = False,
    frozen_r1_ids: Optional[Iterable[object]] = None,
    source_time: Optional[Iterable[object]] = None,
    source_time_unit: Optional[str] = None,
    provenance: Optional[Mapping[str, object]] = None,
) -> Optional[R1RealizationMaterializer]:
    """Return no handle by default; construct only when explicitly enabled."""

    if not enabled:
        return None
    missing = sorted(
        name
        for name, value in {
            "frozen_r1_ids": frozen_r1_ids,
            "source_time": source_time,
            "source_time_unit": source_time_unit,
            "provenance": provenance,
        }.items()
        if value is None
    )
    if missing:
        raise R1RealizationMaterializationError(
            f"Enabled materializer requires explicit inputs; missing={missing}"
        )
    return R1RealizationMaterializer(
        frozen_r1_ids=frozen_r1_ids,
        source_time=source_time,
        source_time_unit=source_time_unit,
        provenance=provenance,
    )
