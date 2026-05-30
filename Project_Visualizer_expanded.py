from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Data"
BASE_VISUALIZER_PATH = PROJECT_ROOT / "Project_Visualizer.py"

EXPANDED_BOUNDARY_PATH = PROJECT_ROOT / "Stage 2 Output_expanded" / "_visualizer_expanded_boundary.geojson"
STAGE_DIR_REPLACEMENTS = {
    "Stage 1 Output": "Stage 1 Output_expanded",
    "Stage 2 Output": "Stage 2 Output_expanded",
    "Stage 3 Output": "Stage 3 Output_expanded",
    "Stage 4 Output": "Stage 4 Output_expanded",
    "Stage 5 Output": "Stage 5 Output_expanded",
    "Stage 6 Output": "Stage 6 Output_expanded",
    "Stage 7 Output": "Stage 7 Output_expanded",
    "Stage5_Results": "Stage5_Results_expanded",
}

def _load_visualizer_namespace() -> dict:
    """Load the shared visualizer source and rewire stage-directory literals to expanded outputs."""
    source = BASE_VISUALIZER_PATH.read_text(encoding="utf-8")
    for old, new in STAGE_DIR_REPLACEMENTS.items():
        source = source.replace(old, new)
    if "_expanded_expanded" in source:
        raise RuntimeError(
            "Expanded visualizer path rewrite produced '_expanded_expanded'; "
            "check STAGE_DIR_REPLACEMENTS before running."
        )

    namespace = {
        "__name__": "_project_visualizer_expanded_base",
        "__file__": str(__file__),
    }
    exec(compile(source, str(BASE_VISUALIZER_PATH), "exec"), namespace)
    return namespace


def _find_tract_id_column(columns) -> str:
    """Choose the most likely tract identifier column from a heterogeneous schema."""
    preferred = [
        "tract_id",
        "TRACT_ID",
        "GEOID",
        "GEOID10",
        "GEOID20",
        "geoid",
        "Tract",
        "TRACT",
    ]
    for col in preferred:
        if col in columns:
            return col
    return list(columns)[0]


def _normalize_tract_ids(series: pd.Series) -> pd.Series:
    """Normalize valid tract identifiers to zero-padded 11-digit strings."""
    digits = series.astype(str).str.extract(r"(\d+)")[0]
    valid = digits.notna() & digits.str.len().gt(0)
    normalized = digits.where(valid).str.zfill(11)
    return normalized.mask(normalized == "00000000000")


def ensure_expanded_boundary_geojson() -> Path:
    """
    Build a runtime expanded study-area boundary from the accepted expanded tract list.

    This keeps expanded maps tied to the accepted expanded footprint instead of the city-only boundary.
    """
    tracts_path = DATA_DIR / "LA_Tracts_With_Population.shp"
    whitelist_path = DATA_DIR / "Tracts_Within_Expanded_Area.csv"

    if not tracts_path.exists():
        raise FileNotFoundError(f"Expanded visualizer boundary source missing: {tracts_path}")
    if not whitelist_path.exists():
        raise FileNotFoundError(f"Expanded tract whitelist missing: {whitelist_path}")

    tracts = gpd.read_file(tracts_path)
    if tracts.empty:
        raise RuntimeError("Expanded visualizer boundary build failed: tract shapefile is empty.")

    tract_col = _find_tract_id_column(tracts.columns)
    tracts = tracts.copy()
    tracts["tract_id"] = _normalize_tract_ids(tracts[tract_col])
    tracts = tracts.dropna(subset=["tract_id"]).copy()

    whitelist = pd.read_csv(whitelist_path)
    if whitelist.empty:
        raise RuntimeError("Expanded visualizer boundary build failed: tract whitelist is empty.")

    whitelist_col = _find_tract_id_column(whitelist.columns)
    expanded_ids = set(_normalize_tract_ids(whitelist[whitelist_col]).dropna())
    if not expanded_ids:
        raise RuntimeError("Expanded visualizer boundary build failed: no valid tract IDs in whitelist.")
    selected = tracts[tracts["tract_id"].isin(expanded_ids)].copy()
    if selected.empty:
        raise RuntimeError(
            "Expanded visualizer boundary build failed: no whitelist tracts matched the shared tract layer."
        )

    EXPANDED_BOUNDARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(selected.geometry, "union_all"):
        boundary_geom = selected.geometry.union_all()
    else:
        boundary_geom = selected.geometry.unary_union

    boundary = gpd.GeoDataFrame(
        {"name": ["Expanded study area"]},
        geometry=[boundary_geom],
        crs=selected.crs,
    )
    boundary.to_file(EXPANDED_BOUNDARY_PATH, driver="GeoJSON")
    return EXPANDED_BOUNDARY_PATH


def _vis_stage2_expanded(namespace: dict) -> None:
    """Expanded Stage 2 counterpart hook. Shared plotting remains owned by Project_Visualizer.py."""
    namespace["_orig_vis_stage2"]()


def _vis_stage3_expanded(namespace: dict, gdf) -> None:
    """Expanded Stage 3 counterpart hook. Shared plotting remains owned by Project_Visualizer.py."""
    namespace["_orig_vis_stage3"](gdf)


def _vis_stage7_cluster_top10_impact_degree_km_expanded(
    namespace: dict,
    gdf,
    cluster_id: int = 0,
    top_n: int = 10,
    impact_mode: str = "lambda2",
) -> None:
    """Expanded Stage 7 cluster/top10 hook. Shared plotting remains owned by Project_Visualizer.py."""
    namespace["_orig_vis_stage7_cluster_top10_impact_degree_km"](
        gdf,
        cluster_id=cluster_id,
        top_n=top_n,
        impact_mode=impact_mode,
    )


def _vis_stage7_expanded(namespace: dict, gdf) -> None:
    """Expanded Stage 7 counterpart hook. Shared plotting remains owned by Project_Visualizer.py."""
    namespace["_orig_vis_stage7"](gdf)


def configure_namespace(namespace: dict) -> None:
    """Apply expanded study-area/path identity while keeping plotting logic shared."""
    namespace["DEVICES_CSV"] = str(DATA_DIR / "working_area_substations_with_fragility.csv")
    namespace["CEC_GRAPH_EDGES_CSV"] = str(DATA_DIR / "substation_graph_CEC_edges_expanded.csv")
    namespace["CEC_TRANSMISSION_SHP"] = str(DATA_DIR / "TransmissionLine_CEC.shp")
    namespace["SHAPEFILE_PATH"] = str(DATA_DIR / "LA_Tracts_With_Population.shp")
    namespace["CITY_BOUNDARY_SHP"] = str(ensure_expanded_boundary_geojson())
    namespace["OUTPUT_ROOT"] = str(PROJECT_ROOT)

    # Expanded maps cover a wider geography than the base study area. Keep the
    # original tall map height, but use the established full-row manuscript
    # width so equal-aspect map panels are not visually shrunk by tight export.
    expanded_map_size = {
        "width_cm": namespace["PANEL_FULLROW"]["width_cm"],
        "height_cm": namespace["PANEL_MAP_TALL"]["height_cm"],
    }
    namespace["PANEL_MAP_EXPANDED"] = expanded_map_size
    namespace["FIGURE_SIZE_PRESETS"]["PANEL_MAP_EXPANDED"] = expanded_map_size
    namespace["FIGURE_SIZE_PRESETS"]["PANEL_MAP_TALL"] = expanded_map_size

    pretty_names = namespace["PRETTY_VAR_NAMES"]
    pretty_names["T50"] = "Recovery time (T50, hr)"
    pretty_names["T80"] = "Recovery time (T80, hr)"
    pretty_names["Pre_1970_Ratio"] = "Pre-1970 housing ratio"
    pretty_names["Pop_Density"] = "Population density"
    pretty_names["NRI_RISK_SCORE"] = "NRI risk score"
    pretty_names["NRI_BUILDVALUE"] = "NRI building value"
    pretty_names["SVI_SCORE"] = "SVI score"

    namespace["_orig_vis_stage2"] = namespace["vis_stage2"]
    namespace["_orig_vis_stage3"] = namespace["vis_stage3"]
    namespace["_orig_vis_stage7"] = namespace["vis_stage7"]
    namespace["_orig_vis_stage7_cluster_top10_impact_degree_km"] = (
        namespace["vis_stage7_cluster_top10_impact_degree_km"]
    )

    namespace["vis_stage2"] = lambda: _vis_stage2_expanded(namespace)
    namespace["vis_stage3"] = lambda gdf: _vis_stage3_expanded(namespace, gdf)
    namespace["vis_stage7"] = lambda gdf: _vis_stage7_expanded(namespace, gdf)
    namespace["vis_stage7_cluster_top10_impact_degree_km"] = (
        lambda gdf, cluster_id=0, top_n=10, impact_mode="lambda2":
        _vis_stage7_cluster_top10_impact_degree_km_expanded(
            namespace,
            gdf,
            cluster_id=cluster_id,
            top_n=top_n,
            impact_mode=impact_mode,
        )
    )


def main() -> None:
    """Run the expanded-area visualization workflow using the shared base renderer.

    The expanded driver rewires file paths to the expanded outputs, rebuilds
    the expanded boundary geometry used for maps, and executes the full stage-
    by-stage visualization sequence.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    namespace = _load_visualizer_namespace()
    configure_namespace(namespace)

    print("=========================================")
    print(" ENHANCED VISUALIZATION GENERATOR (EXPANDED)")
    print("=========================================")
    print("Loading shapefile for mapping...")

    gdf_la = namespace["load_shapefile"]()

    namespace["vis_stage1"](gdf_la)
    namespace["vis_stage2"]()
    namespace["vis_stage3"](gdf_la)
    namespace["vis_stage4"]()
    namespace["vis_stage5"]()
    namespace["vis_stage6"]()
    namespace["vis_stage7_cluster_top10_impact_degree_km"](
        gdf_la,
        cluster_id=1,
        top_n=10,
        impact_mode="lambda2",
    )
    namespace["vis_stage7"](gdf_la)

    print("\nExpanded visualizations completed.")
    print("Paper-package duplicate outputs are disabled.")


if __name__ == "__main__":
    main()
