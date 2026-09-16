"""In-memory controller for default-disabled R1 producer instrumentation.

The controller owns one independent Round 18 materializer and Round 19
observer per realization. It labels caller-precomputed segments, broadcasts a
caller-supplied station-static mask, and collects finalized objects in memory.
It performs no source, graph, damage, recovery, averaging, export, or I/O work.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, Mapping, Optional

import numpy as np
import pandas as pd

from r1_effective_state_materializer import (
    R1MaterializedRealization,
    R1RealizationMaterializer,
    create_r1_realization_materializer,
)
from r1_effective_state_producer_observer import (
    IDENTIFIABILITY_SCOPE,
    R1EffectiveStateProducerObserver,
    create_r1_effective_state_producer_observer,
    observe_precomputed_r1_segment,
)


class R1MainInstrumentationError(ValueError):
    """Raised when enabled main-model instrumentation violates its contract."""


def _normalize_ids(values: Iterable[object]) -> tuple[str, ...]:
    ids = tuple(str(value).strip() for value in values)
    if len(ids) != 310:
        raise R1MainInstrumentationError(
            f"Instrumentation requires exactly 310 frozen R1 IDs, got {len(ids)}"
        )
    if any(not value for value in ids) or len(set(ids)) != len(ids):
        raise R1MainInstrumentationError("Frozen R1 IDs must be unique and nonempty")
    return ids


def _normalize_source_time(values: Iterable[object]) -> tuple[object, ...]:
    source_time = tuple(values)
    if not source_time:
        raise R1MainInstrumentationError("source_time must not be empty")
    index = pd.Index(source_time)
    if index.hasnans or not index.is_unique or not index.is_monotonic_increasing:
        raise R1MainInstrumentationError(
            "source_time must be nonmissing, unique, and strictly increasing"
        )
    return source_time


def _normalize_station_mask(
    mask: pd.Series, frozen_ids: tuple[str, ...]
) -> pd.Series:
    if not isinstance(mask, pd.Series):
        raise R1MainInstrumentationError(
            "authoritative_station_mask must be a pandas Series"
        )
    if mask.index.has_duplicates:
        raise R1MainInstrumentationError(
            "authoritative_station_mask contains duplicate station IDs"
        )
    ids = [str(value).strip() for value in mask.index]
    if len(ids) != len(frozen_ids) or set(ids) != set(frozen_ids):
        raise R1MainInstrumentationError(
            "authoritative_station_mask does not match the frozen 310 IDs"
        )
    values = mask.to_numpy(dtype=object)
    valid = np.vectorize(lambda value: isinstance(value, (bool, np.bool_)))(values)
    if not valid.all():
        raise R1MainInstrumentationError(
            "authoritative_station_mask must contain explicit Boolean values"
        )
    bool_values = mask.to_numpy(dtype=bool)
    if int(bool_values.sum()) != 306 or int((~bool_values).sum()) != 4:
        raise R1MainInstrumentationError(
            "authoritative_station_mask must preserve the frozen 306 identified / 4 unidentified domain"
        )
    result = mask.astype(bool).copy(deep=True)
    result.index = ids
    return result.reindex(list(frozen_ids))


@dataclass
class R1ProducerInstrumentationSession:
    """One independent realization session; never shared across MC indices."""

    controller: "R1MainModelProducerInstrumentation"
    mc_index: int
    realization_id: str
    key: tuple[str, str, str]
    materializer: R1RealizationMaterializer
    observer: R1EffectiveStateProducerObserver
    finalized: bool = False

    def _mask_segment(self, time_start: int, time_stop: int) -> pd.DataFrame:
        length = time_stop - time_start
        values = np.broadcast_to(
            self.controller.authoritative_station_mask.to_numpy(dtype=bool),
            (length, len(self.controller.frozen_r1_ids)),
        ).copy()
        return pd.DataFrame(
            values,
            index=pd.Index(self.controller.source_time[time_start:time_stop]),
            columns=self.controller.frozen_r1_ids,
        )

    def observe_precomputed_segment(
        self,
        *,
        time_start: int,
        time_stop: int,
        caller_owned_segment: object,
    ) -> None:
        """Label and observe a segment already computed by the scientific caller."""

        if self.finalized:
            raise R1MainInstrumentationError("Cannot observe after session finalize")
        if not isinstance(caller_owned_segment, np.ndarray):
            raise R1MainInstrumentationError(
                "Main scientific segment must be an explicit NumPy array"
            )
        expected_shape = (
            time_stop - time_start,
            len(self.controller.frozen_r1_ids),
        )
        if caller_owned_segment.shape != expected_shape:
            raise R1MainInstrumentationError(
                f"Scientific segment shape {caller_owned_segment.shape} "
                f"does not match {expected_shape}"
            )
        state_frame = pd.DataFrame(
            caller_owned_segment.copy(),
            index=pd.Index(self.controller.source_time[time_start:time_stop]),
            columns=self.controller.frozen_r1_ids,
        )
        mask_frame = self._mask_segment(time_start, time_stop)
        returned = observe_precomputed_r1_segment(
            observer=self.observer,
            time_start=time_start,
            time_stop=time_stop,
            effective_state_segment=state_frame,
            state_identified_segment=mask_frame,
        )
        if returned is not None:
            raise R1MainInstrumentationError(
                "Observer must not return a replacement scientific segment"
            )
        return None

    def observe_explicit_zero_segment(
        self, *, time_start: int, time_stop: int
    ) -> None:
        """Represent a zero interval only when scientific control flow requests it."""

        zero_segment = np.zeros(
            (time_stop - time_start, len(self.controller.frozen_r1_ids)),
            dtype=np.float64,
        )
        self.observe_precomputed_segment(
            time_start=time_start,
            time_stop=time_stop,
            caller_owned_segment=zero_segment,
        )
        return None

    def finalize(self) -> None:
        """Finalize once and place the object in the controller's memory collector."""

        if self.finalized:
            raise R1MainInstrumentationError("Session has already been finalized")
        materialized = self.materializer.finalize()
        self.controller._collect(self.key, materialized)
        self.finalized = True
        return None


@dataclass
class R1MainModelProducerInstrumentation:
    """Run-level controller with an in-memory realization collector."""

    enabled: bool = False
    scenario_id: Optional[str] = None
    strategy_id: Optional[str] = None
    source_time: tuple[object, ...] = ()
    source_time_unit: Optional[str] = None
    frozen_r1_ids: tuple[str, ...] = ()
    authoritative_station_mask: Optional[pd.Series] = None
    collected_realizations: Optional[
        dict[tuple[str, str, str], R1MaterializedRealization]
    ] = None
    _validated_for_run: bool = False
    _started_keys: Optional[set[tuple[str, str, str]]] = None

    def validate_run_context(
        self,
        *,
        substation_ids: Iterable[object],
        source_time: Iterable[object],
        mc_source_gate_n_jobs: int,
    ) -> None:
        if not self.enabled:
            return None
        if int(mc_source_gate_n_jobs) != 1:
            raise R1MainInstrumentationError(
                "Enabled producer instrumentation requires MC_SOURCE_GATE_N_JOBS == 1"
            )
        actual_ids = tuple(str(value).strip() for value in substation_ids)
        if actual_ids != self.frozen_r1_ids:
            raise R1MainInstrumentationError(
                "Main sub_index order/identity does not match frozen instrumentation IDs"
            )
        actual_time = tuple(source_time)
        if actual_time != self.source_time:
            raise R1MainInstrumentationError(
                "Main t_grid does not exactly match explicit instrumentation source_time"
            )
        if len(actual_ids) != 310:
            raise R1MainInstrumentationError("Enabled instrumentation requires n_subs == 310")
        if self.authoritative_station_mask is None:
            raise R1MainInstrumentationError("Authoritative station mask is unavailable")
        self._validated_for_run = True
        return None

    def start_realization(self, mc_index: int) -> R1ProducerInstrumentationSession:
        if not self.enabled or not self._validated_for_run:
            raise R1MainInstrumentationError(
                "Instrumentation must be enabled and validated before starting a realization"
            )
        if not isinstance(mc_index, (int, np.integer)) or int(mc_index) < 0:
            raise R1MainInstrumentationError("mc_index must be a nonnegative integer")
        mc_index = int(mc_index)
        realization_id = f"mc_{mc_index:06d}"
        key = (str(self.scenario_id), str(self.strategy_id), realization_id)
        if self._started_keys is None or key in self._started_keys:
            raise R1MainInstrumentationError(f"Duplicate realization key: {key}")
        self._started_keys.add(key)

        id_hash = hashlib.sha256(
            ("\n".join(self.frozen_r1_ids) + "\n").encode("utf-8")
        ).hexdigest()
        provenance: dict[str, object] = {
            "schema_version": "R1_EFFECTIVE_STATE_EXPORT_V1",
            "trajectory_id": "__".join(key),
            "producer_file": "C257H_Project_Main.py",
            "producer_function": "simulate_recovery_mc_source_gated._process_mc_range",
            "effective_state_semantics": "post_source_component_gate_effective_network_state",
            "frozen_R1_ID_hash": id_hash,
            "source_time_unit": str(self.source_time_unit),
            "source_scenario_identifier": str(self.scenario_id),
            "producer_code_hash": "runtime_code_hash_required_before_export",
            "scenario_id": str(self.scenario_id),
            "strategy_id": str(self.strategy_id),
            "realization_id": realization_id,
            "mc_index": mc_index,
            "trajectory_scope": "realization",
            "identifiability_scope": IDENTIFIABILITY_SCOPE,
        }
        materializer = create_r1_realization_materializer(
            enabled=True,
            frozen_r1_ids=self.frozen_r1_ids,
            source_time=self.source_time,
            source_time_unit=str(self.source_time_unit),
            provenance=provenance,
        )
        observer = create_r1_effective_state_producer_observer(
            enabled=True,
            materializer=materializer,
            provenance=provenance,
            authoritative_station_mask=self.authoritative_station_mask,
        )
        if materializer is None or not observer.enabled:
            raise R1MainInstrumentationError(
                "Enabled instrumentation produced a disabled materializer or observer"
            )
        return R1ProducerInstrumentationSession(
            controller=self,
            mc_index=mc_index,
            realization_id=realization_id,
            key=key,
            materializer=materializer,
            observer=observer,
        )

    def _collect(
        self,
        key: tuple[str, str, str],
        materialized: R1MaterializedRealization,
    ) -> None:
        if self.collected_realizations is None:
            raise R1MainInstrumentationError("In-memory collector is unavailable")
        if key in self.collected_realizations:
            raise R1MainInstrumentationError(f"Duplicate finalized realization key: {key}")
        self.collected_realizations[key] = materialized


def create_r1_main_model_producer_instrumentation(
    *,
    enabled: bool = False,
    scenario_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    source_time: Optional[Iterable[object]] = None,
    source_time_unit: Optional[str] = None,
    frozen_r1_ids: Optional[Iterable[object]] = None,
    authoritative_station_mask: Optional[pd.Series] = None,
    trajectory_scope: str = "realization",
) -> R1MainModelProducerInstrumentation:
    """Create a disabled no-state controller or a fully validated run context."""

    if not enabled:
        return R1MainModelProducerInstrumentation(enabled=False)
    required = {
        "scenario_id": scenario_id,
        "strategy_id": strategy_id,
        "source_time": source_time,
        "source_time_unit": source_time_unit,
        "frozen_r1_ids": frozen_r1_ids,
        "authoritative_station_mask": authoritative_station_mask,
    }
    missing = sorted(
        name
        for name, value in required.items()
        if value is None or (isinstance(value, str) and not value.strip())
    )
    if missing:
        raise R1MainInstrumentationError(
            f"Enabled instrumentation requires structured context; missing={missing}"
        )
    if str(trajectory_scope).strip() != "realization":
        raise R1MainInstrumentationError(
            "trajectory_scope must be 'realization'; aggregate instrumentation is forbidden"
        )
    unit = str(source_time_unit).strip()
    if not unit:
        raise R1MainInstrumentationError("source_time_unit must be explicit")
    ids = _normalize_ids(frozen_r1_ids)
    times = _normalize_source_time(source_time)
    station_mask = _normalize_station_mask(authoritative_station_mask, ids)
    return R1MainModelProducerInstrumentation(
        enabled=True,
        scenario_id=str(scenario_id).strip(),
        strategy_id=str(strategy_id).strip(),
        source_time=times,
        source_time_unit=unit,
        frozen_r1_ids=ids,
        authoritative_station_mask=station_mask,
        collected_realizations={},
        _started_keys=set(),
    )
