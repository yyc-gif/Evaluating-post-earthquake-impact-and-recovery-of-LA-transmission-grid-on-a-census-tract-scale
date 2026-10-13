"""Refresh only the existing suite's Stage 7 panels from frozen SOVI tables.

This intentionally does not call the suite-wide renderer or rerun PCA/K-means.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd

import la_grid.plotting.Project_Visualizer as july
from la_grid.revision.r1_stage7_harmonized import STAGE7_FOLDER, verify_harmonized_stage7


from la_grid.paths import REPO_ROOT as ROOT
FORMAL = ROOT / "Formal_Experiment_20260923"
SOURCE = FORMAL / STAGE7_FOLDER
SUITE = ROOT / "results" / "revised_suite" / "LA_Grid_Revised_Suite_20260925"
STAGE = SUITE / "Stage 7 Output_expanded"
SUPP = SUITE / "Submission_Package" / "Supplementary_Figures"
TABLES = SUITE / "Submission_Package" / "Tables"
PANELS = {
    "vis_stage7_pca_scree_plot": "Candidate_S10_PCA_Scree",
    "vis_stage7_elbow_curve_analysis": "Candidate_S11_Kmeans_Elbow",
    "vis_stage7_pca_loadings_heatmap": "Candidate_S12_PCA_Loadings",
    "vis_stage7_map_clusters": "Candidate_S13_Cluster_Map",
    "vis_stage7_map_hotspot_score": "Candidate_S14_Hotspot_Map",
}
EXPECTED = (
    "vis_stage7_pca_scree_plot", "vis_stage7_elbow_curve_analysis",
    "vis_stage7_pca_loadings_heatmap", "vis_stage7_pca_kmeans_scatter",
    "vis_stage7_pca_kmeans_scatter_3d", "vis_stage7_map_clusters",
    "vis_stage7_map_hotspot_score", "vis_stage7_raw_vs_log_cluster_comparison",
    "vis_stage7_heatmap", "vis_stage7_heatmap_halfpanel",
    "vis_stage7_kde_profiles", "vis_stage7_kde_profiles_halfpanel",
)


def main() -> None:
    identity = verify_harmonized_stage7(FORMAL)
    if not SUITE.is_dir() or not STAGE.is_dir():
        raise FileNotFoundError("Existing revised suite Stage 7 directory is required")
    for source in SOURCE.glob("*.csv"):
        shutil.copy2(source, STAGE / source.name)
    # The old CDC exclusion file has a different scientific meaning and must
    # never be consumed alongside the harmonized residential-domain status.
    obsolete = STAGE / "stage7_svi_excluded_tracts.csv"
    if obsolete.is_file():
        obsolete.unlink()
    tract_ids = set(pd.read_csv(STAGE / "stage7_full_domain_tract_status.csv",
                                dtype={"tract_id": str}).tract_id.str.zfill(11))
    geo = gpd.read_file(ROOT / "Data" / "LA_Tracts_With_Population.shp")
    geo["tract_id"] = geo.GEOID.astype(str).str.zfill(11)
    geo = geo[geo.tract_id.isin(tract_ids)].copy()
    if len(geo) != 2315 or set(geo.tract_id) != tract_ids:
        raise ValueError("Stage 7 map does not cover exactly the full study domain")
    july.OUTPUT_ROOT = str(SUITE)
    july.apply_publication_style()
    started = time.time()
    july.vis_stage7(geo)
    for stem in EXPECTED:
        for suffix in (".png", ".pdf"):
            path = STAGE / (stem + suffix)
            if not path.is_file() or path.stat().st_mtime < started - 2:
                raise RuntimeError(f"Harmonized Stage 7 panel was not refreshed: {path}")
            # Keep the committed, reproducible panel pair beside the frozen
            # Stage 7 tables; the sibling suite remains the review copy.
            shutil.copy2(path, SOURCE / path.name)
    for source, target in PANELS.items():
        for suffix in (".png", ".pdf"):
            shutil.copy2(STAGE / (source + suffix), SUPP / (target + suffix))
    for name, source in {
        "Table_S7_Cluster_Profiles.csv": "stage7_cluster_profiles_raw_values.csv",
        "Table_S8_Hotspots.csv": "stage7_top10_slow_vulnerable_tracts.csv",
        "Table_S9_Typology_Domain.csv": "stage7_full_domain_tract_status.csv",
    }.items():
        shutil.copy2(SOURCE / source, TABLES / name)
    readme = SUITE / "README_REVISED_SUITE.md"
    content = readme.read_text(encoding="utf-8")
    prefix = "**Stage 7 version notice (2026-09-26):**"
    if prefix in content:
        first, tail = content.split(prefix, 1)
        _, remaining = tail.split("\n\n", 1)
        content = (first + "**Stage 7 harmonized (2026-09-26):** Stage 7 panels, "
                   "candidate copies, and Tables S7–S9 use the frozen FEMA NRI v1.19 "
                   "`SOVI_SCORE` typology. All 2,315 tracts retain service and social "
                   "scores; 2,291 enter the residential typology and 24 appear as "
                   "not applicable, never as zero service.\n\n" + remaining)
        readme.write_text(content, encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "index_revised_suite.py")],
                   cwd=ROOT, check=True)
    print(f"Refreshed {len(EXPECTED)} Stage 7 panel pairs from {identity['source_directory']}")


if __name__ == "__main__":
    main()
