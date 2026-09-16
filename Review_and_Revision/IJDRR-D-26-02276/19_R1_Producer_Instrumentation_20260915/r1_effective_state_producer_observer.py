"""Observe precomputed R1 segments without participating in scientific state.

The caller retains and accumulates its original segment. When explicitly
enabled, this observer deep-copies the segment and authoritative mask into a
Round 18 materializer for structural QA. It returns no replacement state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

import numpy as np
import pandas as pd

from r1_effective_state_materializer import R1RealizationMaterializer


REALIZATION_SCOPE = "realization"
IDENTIFIABILITY_SCOPE = "STATION_STATIC_WITHIN_TRAJECTORY"
REQUIRED_REALIZATION_FIELDS = {
    "scenario_id",
    "strategy_id",
    "realization_id",
    "trajectory_scope",
}


class R1ProducerObserverError(ValueError):
    """Raised when enabled observational instrumentation is incomplete."""


@dataclass
class R1EffectiveStateProducerObserver:
    """Default-disabled holder for one realization's observational side path."""

    enabled: bool = False
    materializer: Optional[R1RealizationMaterializer] = None
    provenance: Optional[Mapping[str, object]] = None
    authoritative_station_mask: Optional[pd.Series] = None
    segments_observed: int = 0
    cells_observed: int = 0


def _validate_realization_provenance(provenance: Mapping[str, object]) -> None:
    if not isinstance(provenance, Mapping):
        raise R1ProducerObserverError("provenance must be a mapping")
    missing = REQUIRED_REALIZATION_FIELDS - set(provenance)
    if missing:
        raise R1ProducerObserverError(
            f"Realization provenance is missing fields: {sorted(missing)}"
        )
    empty = [
        field
        for field in REQUIRED_REALIZATION_FIELDS
        if provenance[field] is None or not str(provenance[field]).strip()
    ]
    if empty:
        raise R1ProducerObserverError(
            f"Realization provenance has empty fields: {sorted(empty)}"
        )
    if str(provenance["trajectory_scope"]).strip() != REALIZATION_SCOPE:
        raise R1ProducerObserverError(
            "trajectory_scope must be 'realization'; aggregate observations are forbidden"
        )


def _validate_authoritative_station_mask(mask: pd.Series) -> pd.Series:
    if not isinstance(mask, pd.Series):
        raise R1ProducerObserverError(
            "authoritative_station_mask must be a pandas Series with explicit R1 IDs"
        )
    if len(mask) != 310:
        raise R1ProducerObserverError(
            f"authoritative_station_mask must contain 310 stations, got {len(mask)}"
        )
    if mask.index.has_duplicates:
        raise R1ProducerObserverError(
            "authoritative_station_mask contains duplicate station IDs"
        )
    ids = [str(value).strip() for value in mask.index]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise R1ProducerObserverError(
            "authoritative_station_mask has invalid station identity"
        )
    values = mask.to_numpy(dtype=object)
    valid = np.vectorize(lambda value: isinstance(value, (bool, np.bool_)))(values)
    if not valid.all():
        raise R1ProducerObserverError(
            "authoritative_station_mask must contain explicit Boolean values"
        )
    result = mask.astype(bool).copy(deep=True)
    result.index = ids
    result.index.name = "R1_station_id"
    return result


def create_r1_effective_state_producer_observer(
    *,
    enabled: bool = False,
    materializer: Optional[R1RealizationMaterializer] = None,
    provenance: Optional[Mapping[str, object]] = None,
    authoritative_station_mask: Optional[pd.Series] = None,
) -> R1EffectiveStateProducerObserver:
    """Create an inactive observer by default, without inspecting inputs."""

    if not enabled:
        return R1EffectiveStateProducerObserver()
    if materializer is None:
        raise R1ProducerObserverError("Enabled observer requires a materializer")
    if provenance is None:
        raise R1ProducerObserverError("Enabled observer requires provenance")
    if authoritative_station_mask is None:
        raise R1ProducerObserverError(
            "Enabled observer requires an authoritative station mask"
        )
    _validate_realization_provenance(provenance)
    station_mask = _validate_authoritative_station_mask(
        authoritative_station_mask
    )
    return R1EffectiveStateProducerObserver(
        enabled=True,
        materializer=materializer,
        provenance=dict(provenance),
        authoritative_station_mask=station_mask,
    )


def _validate_segment_mask_against_authority(
    segment_mask: pd.DataFrame, authoritative_mask: pd.Series
) -> None:
    if not isinstance(segment_mask, pd.DataFrame):
        raise R1ProducerObserverError(
            "state_identified_segment must be a DataFrame with explicit station IDs"
        )
    if segment_mask.columns.has_duplicates:
        raise R1ProducerObserverError(
            "state_identified_segment contains duplicate station IDs"
        )
    columns = [str(value).strip() for value in segment_mask.columns]
    expected = list(authoritative_mask.index)
    if len(columns) != len(expected) or set(columns) != set(expected):
        raise R1ProducerObserverError(
            "state_identified_segment does not match the authoritative 310-station domain"
        )
    normalized = segment_mask.copy(deep=True)
    normalized.columns = columns
    normalized = normalized.reindex(columns=expected)
    values = normalized.to_numpy(dtype=object)
    valid = np.vectorize(lambda value: isinstance(value, (bool, np.bool_)))(values)
    if not valid.all():
        raise R1ProducerObserverError(
            "state_identified_segment must contain explicit Boolean values"
        )
    expected_values = authoritative_mask.to_numpy(dtype=bool)
    if not np.array_equal(
        normalized.to_numpy(dtype=bool),
        np.broadcast_to(expected_values, normalized.shape),
    ):
        raise R1ProducerObserverError(
            "Segment mask differs from the authoritative station-static mask"
        )


def observe_precomputed_r1_segment(
    *,
    observer: Optional[R1EffectiveStateProducerObserver],
    time_start: object = None,
    time_stop: object = None,
    effective_state_segment: object = None,
    state_identified_segment: object = None,
) -> None:
    """Deep-copy one caller-computed segment into the materializer when enabled.

    The disabled branch returns before inspecting any payload. The enabled
    branch validates structure and delegates copies to the materializer. No
    state is generated, transformed, returned, or offered to the caller as an
    accumulation replacement.
    """

    if observer is None or not observer.enabled:
        return None
    if observer.materializer is None:
        raise R1ProducerObserverError("Enabled observer has no materializer")
    if observer.provenance is None:
        raise R1ProducerObserverError("Enabled observer has no provenance")
    if observer.authoritative_station_mask is None:
        raise R1ProducerObserverError(
            "Enabled observer has no authoritative station mask"
        )
    _validate_realization_provenance(observer.provenance)
    if effective_state_segment is None:
        raise R1ProducerObserverError("effective_state_segment is required")
    if state_identified_segment is None:
        raise R1ProducerObserverError("state_identified_segment is required")
    if not isinstance(effective_state_segment, pd.DataFrame):
        raise R1ProducerObserverError(
            "effective_state_segment must be a DataFrame with explicit station IDs"
        )

    state_snapshot = effective_state_segment.copy(deep=True)
    mask_snapshot = state_identified_segment.copy(deep=True)
    _validate_segment_mask_against_authority(
        mask_snapshot, observer.authoritative_station_mask
    )
    observer.materializer.append_segment(
        time_start,
        time_stop,
        state_snapshot,
        mask_snapshot,
    )
    observer.segments_observed += 1
    observer.cells_observed += int(state_snapshot.size)
    return None
