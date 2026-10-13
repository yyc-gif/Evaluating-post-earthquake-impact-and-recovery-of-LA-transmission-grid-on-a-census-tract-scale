"""Read-only identity checks for the completed FEMA-SOVI Stage 7 output."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


STAGE7_FOLDER = "Stage 7 Output_SOVI_Harmonized"
STAGE7_TABLES = (
    "clusters_labels_final.csv",
    "stage7_full_domain_tract_status.csv",
    "stage7_typology_noneligible_tracts.csv",
    "stage7_top10_slow_vulnerable_tracts.csv",
    "pca_loadings.csv",
    "pca_stats_with_eigenvalues.csv",
    "kmeans_k_diagnostics.csv",
    "stage7_cluster_profiles_raw_values.csv",
    "stage7_raw_vs_log_cluster_membership.csv",
    "stage7_raw_vs_log_k_diagnostics.csv",
    "stage7_raw_vs_log_cluster_crosstab.csv",
    "stage7_raw_vs_log_profile_stability.csv",
    "stage7_raw_vs_log_robustness_summary.csv",
    "stage7_long_tail_diagnostics.csv",
)


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_harmonized_stage7(output_root: Path) -> dict:
    """Reject old CDC-derived tables and incomplete residential/domain coverage."""
    folder = Path(output_root) / STAGE7_FOLDER
    missing = [name for name in STAGE7_TABLES if not (folder / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Harmonized Stage 7 tables absent: {missing}")
    full = pd.read_csv(folder / STAGE7_TABLES[1], dtype={"tract_id": str})
    clusters = pd.read_csv(folder / STAGE7_TABLES[0], dtype={"tract_id": str})
    excluded = pd.read_csv(folder / STAGE7_TABLES[2], dtype={"tract_id": str})
    if (len(full), len(clusters), len(excluded)) != (2315, 2291, 24):
        raise ValueError("Harmonized Stage 7 tract counts differ from frozen domain")
    if any(frame.tract_id.duplicated().any() for frame in (full, clusters, excluded)):
        raise ValueError("Duplicate tract in harmonized Stage 7")
    if set(full.tract_id) != set(clusters.tract_id) | set(excluded.tract_id):
        raise ValueError("Residential typology and noneligible tracts do not partition full domain")
    if set(clusters.tract_id) & set(excluded.tract_id):
        raise ValueError("Tract is both clustered and noneligible")
    if "SVI_Composite" in clusters or "SOVI_SCORE" not in clusters:
        raise ValueError("Stage 7 social feature is not FEMA NRI SOVI_SCORE")
    if not np.isfinite(pd.to_numeric(full.SOVI_SCORE, errors="coerce")).all():
        raise ValueError("FEMA SOVI does not cover all 2315 tracts")
    if not np.isfinite(pd.to_numeric(full.T80, errors="coerce")).all():
        raise ValueError("Frozen tract recovery does not cover all 2315 tracts")
    status = full.set_index("tract_id").typology_status
    if not status.loc[clusters.tract_id].eq("residential_typology_eligible").all():
        raise ValueError("Clustered tract has noneligible status")
    if status.loc[excluded.tract_id].eq("residential_typology_eligible").any():
        raise ValueError("Noneligible tract has residential status")
    return {
        "stage7_identity": "FEMA_NRI_V1_19_SOVI_RESIDENTIAL_TYPOLOGY",
        "source_directory": str(folder.resolve()),
        "full_service_and_sovi_tracts": len(full),
        "residential_typology_tracts": len(clusters),
        "explicit_noneligible_tracts": len(excluded),
        "input_sha256": {name: _digest(folder / name) for name in STAGE7_TABLES},
    }
