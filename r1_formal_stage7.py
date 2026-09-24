"""Build original Stage 7 inputs from the frozen 1000-sample event archive.

This retains the original 2pc50 community typology entry.  Mean service is
formed at every distinct completion event; no dense time grid or interpolation
replaces the completion-step trajectories.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix


def materialize_formal_stage7_inputs(*, output_root: Path, station_ids,
                                     tract_ids, tract_station_weight,
                                     executable_code_sha: str) -> dict:
    output_root = Path(output_root)
    folder = output_root / "Formal_Trajectories" / "2pc50" / "C57_D1" / "direct-community"
    ids = np.asarray(list(map(str, station_ids)), dtype=str)
    tracts = np.asarray(list(map(str, tract_ids)), dtype=str)
    w = np.asarray(tract_station_weight, float)
    if len(ids) != 92 or len(tracts) != 2315 or w.shape != (2315, 92):
        raise ValueError("Formal Stage 7 requires frozen July92/2315 mapping dimensions")
    initial = np.zeros(92, dtype=float)
    all_times = []
    all_delta = []
    manifest_chain = hashlib.sha256()
    for sample in range(1000):
        stem = f"2pc50__evaluation_{sample:04d}"
        manifest_path = folder / (stem + ".json")
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        identity = manifest["identity"]
        if (identity["realization_id"] != stem or identity["strategy"] != "direct-community" or
                identity["resource_scenario"] != "C57_D1" or identity["event_horizon_hr"] != 480):
            raise ValueError("Formal Stage 7 archive identity changed")
        manifest_chain.update(hashlib.sha256(manifest_bytes).digest())
        with np.load(folder / (stem + ".npz"), allow_pickle=False) as z:
            if not np.array_equal(z["station_ids"].astype(str), ids):
                raise ValueError("Formal Stage 7 station order changed")
            time = z["event_time_hr"].copy()
            e = z["e"].copy()
        if time[0] != 0 or time[-1] != 480 or e.shape[1] != 92:
            raise ValueError("Formal Stage 7 event horizon/domain changed")
        delta = np.diff(e, axis=0)
        if (delta < -1e-12).any():
            raise ValueError("Repair-only source-gated availability decreased")
        initial += e[0]
        changed = (delta != 0).any(axis=1)
        all_times.append(time[1:][changed])
        all_delta.append(delta[changed])
    initial /= 1000
    mean_tract = w @ initial
    supply = pd.DataFrame(dict(tract_id=tracts, scenario="2pc50", supply=mean_tract))
    times = np.concatenate(all_times)
    changes = np.concatenate(all_delta, axis=0)
    order = np.argsort(times, kind="stable")
    times, changes = times[order], changes[order]
    sparse = csc_matrix(w)
    crossing = {threshold: np.where(mean_tract >= threshold, 0., np.nan)
                for threshold in (.5, .8, .9)}
    start = 0
    while start < len(times):
        end = int(np.searchsorted(times, times[start], side="right"))
        total_delta = changes[start:end].sum(axis=0) / 1000
        for station in np.flatnonzero(total_delta):
            lo, hi = sparse.indptr[station:station+2]
            mean_tract[sparse.indices[lo:hi]] += sparse.data[lo:hi] * total_delta[station]
        for threshold, value in crossing.items():
            mask = np.isnan(value) & (mean_tract >= threshold)
            value[mask] = times[start]
        start = end
    if np.isnan(crossing[.5]).any() or np.isnan(crossing[.8]).any():
        raise ValueError("Formal Stage 7 T50/T80 has unreached tract; preserve NA and stop")
    kpis = pd.DataFrame(dict(tract_id=tracts,T50=crossing[.5],
                             T80=crossing[.8],T90=crossing[.9]))
    stage1 = output_root / "Stage 1 Output_expanded"
    stage5 = output_root / "Stage 5 Output_expanded"
    supply_path = stage1 / "MC_Tract_Supply_2pc50.csv"
    kpi_path = stage5 / "tract_kpis_2pc50.csv"
    for path in (supply_path, kpi_path):
        if path.exists():
            raise ValueError(f"Formal Stage 7 input already exists: {path}")
    supply.to_csv(supply_path, index=False)
    kpis.to_csv(kpi_path, index=False)
    result = dict(status="FORMAL_FROZEN_MATRIX_V1", executable_code_commit_sha=executable_code_sha,
                  source_trajectory_count=1000, event_changes=len(times),
                  T50_unreached=int(np.isnan(crossing[.5]).sum()),
                  T80_unreached=int(np.isnan(crossing[.8]).sum()),
                  T90_unreached=int(np.isnan(crossing[.9]).sum()),
                  source_manifest_chain_sha256=manifest_chain.hexdigest())
    (output_root / "FORMAL_STAGE7_INPUT_IDENTITY.json").write_text(
        json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return result
