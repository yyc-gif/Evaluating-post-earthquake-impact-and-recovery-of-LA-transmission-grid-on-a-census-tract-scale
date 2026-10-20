"""Identity-checked, atomic storage for frozen-matrix July92 trajectories.

The original expanded main entry is the execution driver.  This module only
stores an already produced event trajectory and refuses incompatible resume.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


REQUIRED_IDENTITY = (
    "matrix_id", "executable_code_commit_sha", "hazard", "realization_id",
    "split", "strategy", "resource_scenario", "DS_hash", "duration_hash",
    "physical_sample_hash", "graph_hash", "source_set_hash",
    "mapping_method_id", "crew_roster_hash", "directed_travel_hash",
    "event_horizon_hr",
)
TRACE_FIELDS = ("f", "F", "C", "e", "L_self", "L_threshold", "L_source", "L_total")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_identity(identity: dict) -> None:
    missing = set(REQUIRED_IDENTITY) - identity.keys()
    if missing:
        raise ValueError(f"Formal trajectory identity is incomplete: {sorted(missing)}")
    if identity["matrix_id"] != "JULY92_REVIEWER_REVISION_FINAL_V1":
        raise ValueError("Wrong frozen matrix ID")
    if identity["split"] != "evaluation":
        raise ValueError("Formal trajectory must use evaluation samples")
    if identity["mapping_method_id"] != "M1_UTILITY_003":
        raise ValueError("Formal production trajectory must use M1 mapping")
    if not np.isfinite(identity["event_horizon_hr"]) or identity["event_horizon_hr"] < 480:
        raise ValueError("Invalid common evaluation horizon")
    if any(identity[k] in (None, "") for k in REQUIRED_IDENTITY):
        raise ValueError("Formal trajectory identity contains an empty value")


def validate_trace(trace, identity: dict) -> dict[str, np.ndarray]:
    validate_identity(identity)
    arrays = {name: getattr(trace, name).to_numpy() for name in TRACE_FIELDS}
    frame = trace.f
    if frame.shape[1] != 92 or not frame.columns.is_unique:
        raise ValueError("Formal trace must contain 92 unique ordered stations")
    time = frame.index.to_numpy(float)
    if time.size < 2 or not np.isfinite(time).all() or time[0] != 0 or np.any(np.diff(time) <= 0):
        raise ValueError("Formal event time must start at zero and increase strictly")
    if time[-1] != identity["event_horizon_hr"]:
        raise ValueError("Trace does not reach the common evaluation horizon")
    for name, value in arrays.items():
        if value.shape != frame.shape or not np.isfinite(value).all():
            raise ValueError(f"Invalid formal trace array: {name}")
    if np.max(np.abs(arrays["L_self"] + arrays["L_threshold"] + arrays["L_source"] - arrays["L_total"])) > 1e-12:
        raise ValueError("Source-gate loss decomposition does not conserve")
    arrays["station_ids"] = np.asarray(frame.columns.astype(str), dtype=str)
    arrays["event_time_hr"] = time
    return arrays


def _atomic_write(path: Path, writer) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.stem + ".", suffix=path.suffix, dir=path.parent)
    os.close(fd)
    temp = Path(name)
    try:
        writer(temp)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def inspect_formal_archive(folder: Path, *, identity: dict, stem: str) -> dict | None:
    """Read-only pre-execution resume check; never silently accept partial files."""
    validate_identity(identity)
    folder = Path(folder)
    npz_path = folder / f"{stem}.npz"
    events_path = folder / f"{stem}__TASK_EVENTS.csv"
    manifest_path = folder / f"{stem}.json"
    exists = tuple(path.exists() for path in (npz_path, events_path, manifest_path))
    if not any(exists):
        return None
    if not all(exists):
        raise ValueError("Partial formal archive exists; stop for investigation")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["status"] != "FORMAL_FROZEN_MATRIX_V1" or manifest["identity"] != identity:
        raise ValueError("Formal archive identity changed on resume")
    if sha256_file(npz_path) != manifest["npz_sha256"] or sha256_file(events_path) != manifest["task_events_sha256"]:
        raise ValueError("Formal archive contents changed on resume")
    with np.load(npz_path, allow_pickle=False) as saved:
        if set(saved.files) != set(TRACE_FIELDS) | {"station_ids", "event_time_hr"}:
            raise ValueError("Formal archive arrays are incomplete")
        if saved["f"].shape[1] != 92 or saved["event_time_hr"][-1] != identity["event_horizon_hr"]:
            raise ValueError("Formal archive dimensions/horizon changed")
    return manifest


def retain_formal_trajectory(folder: Path, *, trace, task_events: pd.DataFrame,
                             identity: dict, stem: str) -> str:
    """Write once or verify exact existing identity and file hashes on resume."""
    arrays = validate_trace(trace, identity)
    folder = Path(folder)
    if not stem or stem != Path(stem).name or any(ch in stem for ch in "/\\"):
        raise ValueError("Invalid formal archive stem")
    npz_path = folder / f"{stem}.npz"
    events_path = folder / f"{stem}__TASK_EVENTS.csv"
    manifest_path = folder / f"{stem}.json"
    paths = (npz_path, events_path, manifest_path)
    manifest = inspect_formal_archive(folder, identity=identity, stem=stem)
    if manifest is not None:
        with np.load(npz_path, allow_pickle=False) as saved:
            if set(saved.files) != set(arrays) or any(not np.array_equal(saved[key], value) for key, value in arrays.items()):
                raise ValueError("New trajectory differs from saved formal archive")
        retained = pd.read_csv(events_path, dtype={"task_id": str}, float_precision="round_trip")
        if not retained.equals(task_events.reset_index(drop=True)):
            raise ValueError("New task events differ from saved formal archive")
        return "reused"
    _atomic_write(npz_path, lambda temp: np.savez_compressed(temp, **arrays))
    _atomic_write(events_path, lambda temp: task_events.to_csv(temp, index=False))
    manifest = {
        "status": "FORMAL_FROZEN_MATRIX_V1", "identity": identity,
        "npz_sha256": sha256_file(npz_path),
        "task_events_sha256": sha256_file(events_path),
        "event_count": int(len(task_events)),
    }
    _atomic_write(manifest_path, lambda temp: temp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"))
    return "written"
