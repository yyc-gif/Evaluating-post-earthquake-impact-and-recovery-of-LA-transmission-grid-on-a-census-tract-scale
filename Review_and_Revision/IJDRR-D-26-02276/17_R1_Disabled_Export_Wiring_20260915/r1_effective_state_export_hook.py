"""Fail-closed seam for future R1 realization-trajectory export.

This module performs no scientific calculation and no file I/O.  A future
producer must supply the complete post-gate state and authoritative identified
mask before this seam may call the frozen Round 16 exporter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional


REALIZATION_SCOPE = "realization"
REQUIRED_REALIZATION_IDENTITY_FIELDS = {
    "scenario_id",
    "strategy_id",
    "realization_id",
    "trajectory_scope",
}


class R1EffectiveStateExportHookError(ValueError):
    """Raised when an enabled hook lacks a complete realization object."""


@dataclass(frozen=True)
class R1EffectiveStateExportHook:
    """Default-disabled callback holder for the future producer boundary."""

    enabled: bool = False
    callback: Optional[Callable[..., Any]] = None


def _validate_realization_identity(provenance: Mapping[str, object]) -> None:
    if not isinstance(provenance, Mapping):
        raise R1EffectiveStateExportHookError("provenance must be a mapping")

    missing = REQUIRED_REALIZATION_IDENTITY_FIELDS - set(provenance)
    if missing:
        raise R1EffectiveStateExportHookError(
            f"Realization provenance is missing fields: {sorted(missing)}"
        )

    empty = []
    for field in REQUIRED_REALIZATION_IDENTITY_FIELDS:
        value = provenance[field]
        if value is None or not str(value).strip():
            empty.append(field)
    if empty:
        raise R1EffectiveStateExportHookError(
            f"Realization provenance has empty fields: {sorted(empty)}"
        )

    if str(provenance["trajectory_scope"]).strip() != REALIZATION_SCOPE:
        raise R1EffectiveStateExportHookError(
            "trajectory_scope must be 'realization'; aggregate or MC-mean objects are forbidden"
        )


def maybe_export_r1_effective_state(
    *,
    hook: Optional[R1EffectiveStateExportHook],
    effective_state: Any = None,
    state_identified: Any = None,
    source_time: Any = None,
    source_time_unit: Any = None,
    frozen_r1_ids: Any = None,
    provenance: Optional[Mapping[str, object]] = None,
) -> Any:
    """Transport a complete producer object to its callback when enabled.

    Disabled execution returns immediately, before inspecting producer inputs.
    Enabled execution requires both state channels and all remaining contract
    inputs.  This function never constructs, gates, averages, fills, or writes
    a trajectory.
    """

    if hook is None or not hook.enabled:
        return None

    if hook.callback is None:
        raise R1EffectiveStateExportHookError(
            "An enabled export hook requires a callback"
        )

    required_inputs = {
        "effective_state": effective_state,
        "state_identified": state_identified,
        "source_time": source_time,
        "source_time_unit": source_time_unit,
        "frozen_r1_ids": frozen_r1_ids,
        "provenance": provenance,
    }
    missing = sorted(name for name, value in required_inputs.items() if value is None)
    if missing:
        raise R1EffectiveStateExportHookError(
            f"Enabled export hook requires a complete producer object; missing={missing}"
        )

    _validate_realization_identity(provenance)

    return hook.callback(
        effective_state=effective_state,
        state_identified=state_identified,
        source_time=source_time,
        source_time_unit=source_time_unit,
        frozen_r1_ids=frozen_r1_ids,
        provenance=provenance,
    )
