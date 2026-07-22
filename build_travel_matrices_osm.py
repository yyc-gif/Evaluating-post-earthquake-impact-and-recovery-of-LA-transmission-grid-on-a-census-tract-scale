"""
build_travel_matrices_osm.py

Description:
    This script precomputes travel time matrices using an OSMnx road network graph.
    It replaces Euclidean/Geodesic distance estimates with real-world road network travel times.

Outputs (saved to 'Stage 4 Output_expanded'):
    1. travel_base_to_task.csv: Travel times from Crew Bases to Substations.
    2. travel_task_to_task.csv: Travel times between all pairs of Substations.

Compatibility:
    - Designed to match the 'load_travel_matrices()' function in 'C257H_Project_Main.py'.
    - Handles OSMnx version differences (nearest_nodes API).
    - Optimizes Dijkstra calculations by grouping substations at the same graph node.
"""

import os
import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
from pathlib import Path

# ======================= USER CONFIGURATION =======================

# --- File Paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
GRAPHML_PATH = str(DATA_DIR / "la_drive.graphml")
SUBS_CSV = str(DATA_DIR / "working_area_substations_with_fragility.csv")
DEPOT_INPUT_CSV = str(DATA_DIR / "stage45_depot_inputs_final_origin_proxy.csv")

# --- Output Settings ---
OUTPUT_ROOT = str(BASE_DIR)
STAGE4_DIR = "Stage 4 Output_expanded"
TRAVEL_BASE_TO_TASK_CSV = "travel_base_to_task.csv"
TRAVEL_TASK_TO_TASK_CSV = "travel_task_to_task.csv"

# --- Column Mappings (Input CSV) ---
# The script will prioritize these columns but falls back to defaults if not found.
ID_COL = "HIFLD_ID"
LON_COL = "LONGITUDE"
LAT_COL = "LATITUDE"

# --- Calculation Parameters ---
# Substation IDs to include (None = Process all substations in CSV)
# Keep the travel task universe aligned with the tract-analysis baseline by
# default, rather than the broader raw inventory.
MAPPING_CSV = str(DATA_DIR / "tract_to_substation_mapping_CEC_expanded.csv")
LIMIT_TO_SUB_IDS: Optional[List[str]] = None
SUBS_COORD_FALLBACK_CSVS: Tuple[str, ...] = ()

# Max travel time in seconds (e.g., 6 hours).
# Dijkstra will stop searching beyond this limit to save time.
MAX_TRAVEL_TIME_SEC = 6 * 3600.0


@dataclass(frozen=True)
class TravelMatrixConfig:
    graphml_path: str = GRAPHML_PATH
    subs_csv: str = SUBS_CSV
    output_root: str = OUTPUT_ROOT
    stage4_dir: str = STAGE4_DIR
    travel_base_to_task_csv: str = TRAVEL_BASE_TO_TASK_CSV
    travel_task_to_task_csv: str = TRAVEL_TASK_TO_TASK_CSV
    mapping_csv: str = MAPPING_CSV
    depot_input_csv: str = DEPOT_INPUT_CSV
    substation_coordinate_fallback_csvs: Tuple[str, ...] = SUBS_COORD_FALLBACK_CSVS
    limit_to_sub_ids: Optional[List[str]] = None
    id_col: str = ID_COL
    lon_col: str = LON_COL
    lat_col: str = LAT_COL
    max_travel_time_sec: float = MAX_TRAVEL_TIME_SEC


# ======================= HELPER FUNCTIONS =======================

def setup_logging():
    """Initialize logging format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def ensure_dir(path: str):
    """Ensure the output directory exists."""
    os.makedirs(path, exist_ok=True)


def load_task_ids_from_mapping(mapping_csv: str) -> Optional[List[str]]:
    """
    Read the tract-to-substation mapping and return the aligned task IDs used by
    the main analysis baseline. Falls back to None if the mapping is missing or
    unreadable so the script can still run against the full inventory.
    """
    logger = logging.getLogger()
    if not os.path.exists(mapping_csv):
        logger.warning("Mapping CSV not found for task filtering: %s", mapping_csv)
        return None

    try:
        mapping = pd.read_csv(mapping_csv)
    except Exception as exc:
        logger.warning("Failed to read mapping CSV %s: %s", mapping_csv, exc)
        return None

    if "substation_id" not in mapping.columns:
        logger.warning("Mapping CSV missing 'substation_id': %s", mapping_csv)
        return None

    ids = (
        mapping["substation_id"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    unique_ids = sorted(ids[ids.ne("")].dropna().unique().tolist())
    return unique_ids or None


def standardize_substation_coordinates(csv_path: str, cfg: TravelMatrixConfig) -> pd.DataFrame:
    """Load one substation coordinate table and return id/lon/lat columns."""
    df = pd.read_csv(csv_path)
    cols = list(df.columns)

    if cfg.id_col in cols:
        curr_id = cfg.id_col
    elif "HIFLD_ID" in cols:
        curr_id = "HIFLD_ID"
    elif "ID" in cols:
        curr_id = "ID"
    elif "id" in cols:
        curr_id = "id"
    else:
        raise ValueError(f"ID column not found in {csv_path}. Available: {cols}")

    if cfg.lon_col in cols and cfg.lat_col in cols:
        curr_lon, curr_lat = cfg.lon_col, cfg.lat_col
    elif "LONGITUDE" in cols and "LATITUDE" in cols:
        curr_lon, curr_lat = "LONGITUDE", "LATITUDE"
    elif "lon" in cols and "lat" in cols:
        curr_lon, curr_lat = "lon", "lat"
    elif "lon.1" in cols and "lat.1" in cols:
        curr_lon, curr_lat = "lon.1", "lat.1"
    else:
        raise ValueError(f"Coordinate columns not found in {csv_path}. Available: {cols}")

    out = df[[curr_id, curr_lon, curr_lat]].copy()
    out = out.rename(columns={curr_id: "id", curr_lon: "lon", curr_lat: "lat"})
    out["id"] = out["id"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    out["lon"] = pd.to_numeric(out["lon"], errors="coerce")
    out["lat"] = pd.to_numeric(out["lat"], errors="coerce")
    out = out.dropna(subset=["id", "lon", "lat"])
    return out.drop_duplicates("id", keep="first")


def load_c57_crew_bases(depot_csv: str) -> List[Tuple[str, float, float]]:
    """
    Load active C57 repair origins from the finalized Stage 4/5 depot input.

    Returns tuples in the same shape the OSM builder already expects:
    (origin_id, latitude, longitude), with origin_id equal to D01-D16 yard IDs.
    """
    logger = logging.getLogger()
    path = Path(depot_csv)
    if not path.exists():
        raise FileNotFoundError(f"C57 depot input not found: {path}")

    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "yard_id": "depot_id",
            "facility": "depot_name",
        }
    )
    allocation_cols = [
        "scenario_label",
        "allocation_label",
        "raw_visual_weight",
        "fractional_crews",
        "integer_crews",
        "active_in_integer_input",
    ]
    scenario_label = "C57_substation_ratio_main"
    allocation_label = "C57_yard_allocation_no_deletion_tie_coherent_zero_low"
    if any(c not in df.columns for c in allocation_cols):
        active_path = path.with_name("stage45_active_crew_bases_C57.csv")
        if active_path.exists():
            active_alloc = pd.read_csv(active_path).rename(
                columns={
                    "yard_id": "depot_id",
                    "facility": "depot_name",
                }
            )
            active_alloc["depot_id"] = active_alloc["depot_id"].astype(str).str.strip()
            merge_cols = ["depot_id"] + [
                c for c in allocation_cols if c not in df.columns and c in active_alloc.columns
            ]
            if len(merge_cols) > 1:
                df = df.merge(active_alloc[merge_cols], on="depot_id", how="left")
    defaults = {
        "scenario_label": scenario_label,
        "allocation_label": allocation_label,
        "raw_visual_weight": 0.0,
        "fractional_crews": 0.0,
        "integer_crews": 0,
        "active_in_integer_input": "no",
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)
    df.loc[pd.to_numeric(df["integer_crews"], errors="coerce").fillna(0) > 0, "active_in_integer_input"] = "yes"

    required = {
        "depot_id",
        "latitude",
        "longitude",
        "integer_crews",
        "active_in_integer_input",
        "scenario_label",
        "allocation_label",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"C57 depot input missing required columns: {missing}")

    expected_ids = [f"D{i:02d}" for i in range(1, 17)]
    expected_active = ["D01", "D02", "D03", "D04", "D05", "D06", "D07", "D09", "D10", "D12", "D13"]

    df = df.copy()
    df["depot_id"] = df["depot_id"].astype(str).str.strip()
    if sorted(df["depot_id"].tolist()) != expected_ids:
        raise ValueError("C57 depot input must contain exactly D01-D16 for travel matrix generation.")
    if not (df["scenario_label"].astype(str).str.strip() == scenario_label).all():
        raise ValueError("C57 depot scenario_label validation failed.")
    if not (df["allocation_label"].astype(str).str.strip() == allocation_label).all():
        raise ValueError("C57 depot allocation_label validation failed.")

    df["integer_crews"] = pd.to_numeric(df["integer_crews"], errors="raise").astype(int)
    if int(df["integer_crews"].sum()) != 57:
        raise ValueError("C57 depot integer_crews total must be 57.")

    active = df[df["integer_crews"] > 0].copy()
    actual_active = sorted(active["depot_id"].tolist())
    if actual_active != expected_active:
        raise ValueError(f"C57 active yard set invalid: {actual_active}")
    active_flag = df["active_in_integer_input"].astype(str).str.strip().str.lower()
    if not (active_flag[df["integer_crews"] > 0] == "yes").all():
        raise ValueError("C57 active depot rows must have active_in_integer_input=yes.")
    if not (active_flag[df["integer_crews"] == 0] == "no").all():
        raise ValueError("C57 inactive depot rows must have active_in_integer_input=no.")
    if active[["latitude", "longitude"]].isna().any().any():
        raise ValueError("C57 active depot coordinates must be non-null.")

    bases = [
        (str(row["depot_id"]), float(row["latitude"]), float(row["longitude"]))
        for _, row in active.sort_values("depot_id").iterrows()
    ]
    logger.info("Loaded %d active C57 crew bases from %s.", len(bases), path)
    return bases


def nearest_nodes_compat(G, xs, ys):
    """
    Compatibility wrapper for OSMnx's nearest_nodes function.
    Handles API changes between OSMnx < 1.0, 1.x, and 2.x.
    
    Args:
        G: The graph object.
        xs: List/Array of X coordinates (Longitude).
        ys: List/Array of Y coordinates (Latitude).
    """
    try:
        # Modern OSMnx (v1.3.0+)
        from osmnx.distance import nearest_nodes
        return nearest_nodes(G, xs, ys)
    except (ImportError, AttributeError):
        # Older OSMnx versions
        if hasattr(ox, "distance") and hasattr(ox.distance, "nearest_nodes"):
            return ox.distance.nearest_nodes(G, xs, ys)
        elif hasattr(ox, "get_nearest_nodes"):
            # Deprecated function (very old versions), works for single points
            return ox.get_nearest_nodes(G, xs, ys)
        else:
            raise RuntimeError("Could not find a compatible 'nearest_nodes' function in OSMnx.")


def load_graph_with_travel_time(graphml_path: str) -> nx.MultiDiGraph:
    """
    Load the GraphML file and ensure 'travel_time' attributes exist on edges.
    If 'travel_time' is missing or corrupted, it recalculates speeds and times.
    """
    logger = logging.getLogger()
    logger.info(f"Loading road network graph from {graphml_path} ...")
    
    # Load graph
    G = ox.load_graphml(graphml_path)

    # Validation: Check if 'travel_time' exists and is valid on edges
    logger.info("Validating edge 'travel_time' attributes...")
    missing_tt = False
    
    # Check a sample or all edges to ensure attribute existence
    for u, v, k, data in G.edges(keys=True, data=True):
        val = data.get("travel_time")
        if val is None or not isinstance(val, (int, float)) or not np.isfinite(val):
            missing_tt = True
            break
    
    if missing_tt:
        logger.warning("Missing or invalid 'travel_time' detected. Re-calculating edge speeds and times...")
        # Add free-flow speeds based on highway type
        G = ox.add_edge_speeds(G)
        # Calculate travel time (length / speed)
        G = ox.add_edge_travel_times(G)
    else:
        logger.info("Graph validation passed: 'travel_time' attributes are present.")

    return G


def load_substations(
    cfg: TravelMatrixConfig,
    limit_to_sub_ids: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Load substation data from CSV and standardize columns to ['id', 'lon', 'lat'].
    """
    logger = logging.getLogger()
    logger.info(f"Loading substations from {cfg.subs_csv} ...")

    out = standardize_substation_coordinates(cfg.subs_csv, cfg)

    # Optional filtering. If the primary inventory is missing mapped targets,
    # fill by exact substation ID from configured coordinate fallback tables.
    if limit_to_sub_ids is not None:
        limit_ids = [str(s).strip().replace(".0", "") for s in limit_to_sub_ids]
        limit_set = set(limit_ids)
        out = out[out["id"].isin(limit_set)].copy()

        missing_ids = sorted(limit_set - set(out["id"]))
        if missing_ids:
            logger.warning(
                "Primary substation file is missing %d mapped IDs; checking coordinate fallback tables.",
                len(missing_ids),
            )
            fallback_rows = []
            remaining_missing = set(missing_ids)
            for fallback_csv in cfg.substation_coordinate_fallback_csvs:
                if not remaining_missing:
                    break
                if not os.path.exists(fallback_csv):
                    logger.warning("Substation coordinate fallback missing: %s", fallback_csv)
                    continue
                fallback = standardize_substation_coordinates(fallback_csv, cfg)
                fallback = fallback[fallback["id"].isin(remaining_missing)].copy()
                if not fallback.empty:
                    fallback_rows.append(fallback)
                    remaining_missing -= set(fallback["id"])
                    logger.info(
                        "Filled %d mapped substation coordinates from fallback: %s",
                        len(fallback),
                        fallback_csv,
                    )

            if fallback_rows:
                out = pd.concat([out] + fallback_rows, ignore_index=True)
                out = out.drop_duplicates("id", keep="first")

        still_missing = sorted(limit_set - set(out["id"]))
        if still_missing:
            raise ValueError(
                f"Substation coordinate inventory missing mapped IDs after fallback lookup: {still_missing}"
            )

        out = out.set_index("id").reindex(limit_ids).reset_index()
        logger.info(f"Filtered to {len(out)} substations based on user settings.")

    return out


def map_points_to_nodes(G, df_subs: pd.DataFrame) -> Dict[str, int]:
    """
    Map each substation (lat/lon) to the nearest node ID in the road graph.
    Returns: Dictionary {substation_id: graph_node_id}
    """
    logger = logging.getLogger()
    xs = df_subs["lon"].values
    ys = df_subs["lat"].values

    logger.info("Snapping substations to nearest graph nodes...")
    nodes = nearest_nodes_compat(G, xs, ys)

    df_subs = df_subs.copy()
    df_subs["node"] = nodes

    mapping = dict(zip(df_subs["id"].astype(str), df_subs["node"]))
    
    n_unique = df_subs["node"].nunique()
    logger.info(f"Mapped {len(mapping)} substations to {n_unique} unique road network nodes.")
    
    return mapping


def get_base_nodes(G, cfg: TravelMatrixConfig) -> List[Tuple[str, int]]:
    """
    Map Crew Base coordinates to nearest graph nodes.
    Returns: List of tuples [(base_id, graph_node_id)]
    """
    logger = logging.getLogger()
    base_nodes: List[Tuple[str, int]] = []
    crew_bases = load_c57_crew_bases(cfg.depot_input_csv)

    for base_id, lat, lon in crew_bases:
        node_id = nearest_nodes_compat(G, [lon], [lat])[0]
        base_nodes.append((base_id, node_id))
        
    logger.info(f"Mapped {len(base_nodes)} crew bases to graph nodes.")
    return base_nodes


def compute_travel_times(
    G: nx.MultiDiGraph,
    base_nodes: List[Tuple[str, int]],
    sub_to_node: Dict[str, int],
    *,
    max_travel_time_sec: float = MAX_TRAVEL_TIME_SEC,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute shortest path travel times using Dijkstra's algorithm.
    
    Returns:
        1. Base->Task DataFrame (Rows: Bases, Cols: Substations)
        2. Task->Task DataFrame (Rows: Substations, Cols: Substations)
    """
    logger = logging.getLogger()
    sub_ids = sorted(sub_to_node.keys())
    n_sub = len(sub_ids)
    n_base = len(base_nodes)

    # ---------------------------------------------------------
    # PART 1: Base -> Task Matrix
    # ---------------------------------------------------------
    logger.info(f"Computing Base->Task Matrix ({n_base} bases)...")
    base_mat_sec = np.full((n_base, n_sub), np.nan, dtype=float)

    for i, (base_id, base_node) in enumerate(base_nodes):
        # Use 'cutoff' to stop searching nodes further than MAX_TRAVEL_TIME
        try:
            lengths = nx.single_source_dijkstra_path_length(
                G, base_node, weight="travel_time", cutoff=max_travel_time_sec
            )
        except TypeError:
            # Fallback for older NetworkX versions that don't support 'cutoff'
            lengths = nx.single_source_dijkstra_path_length(
                G, base_node, weight="travel_time"
            )
            
        for j, sid in enumerate(sub_ids):
            node = sub_to_node[sid]
            t_sec = lengths.get(node, np.nan)
            
            # Enforce cutoff manually if fallback was used
            if t_sec is not None and t_sec > max_travel_time_sec:
                t_sec = np.nan
                
            base_mat_sec[i, j] = t_sec

    # Convert to hours and create DataFrame
    base_to_task_hr = base_mat_sec / 3600.0
    base_to_task_df = pd.DataFrame(
        base_to_task_hr,
        index=[b[0] for b in base_nodes],
        columns=sub_ids,
    )
    base_to_task_df.index.name = "base_id"

    # ---------------------------------------------------------
    # PART 2: Task -> Task Matrix (Optimized)
    # ---------------------------------------------------------
    logger.info("Computing Task->Task Matrix...")
    
    # Optimization: Substations often snap to the same road node.
    # We only run Dijkstra for *unique* graph nodes to save computation time.
    unique_nodes = sorted(list(set(sub_to_node.values())))
    n_unique = len(unique_nodes)
    logger.info(f"Optimization: Calculating paths for {n_unique} unique nodes (instead of {n_sub} substations).")
    
    # Dictionary to store pre-computed distances: {source_node: {target_node: time}}
    node_dists = {} 
    
    for i, u_node in enumerate(unique_nodes):
        if i % 50 == 0:
            logger.info(f"Progress: Processed {i}/{n_unique} unique source nodes...")
        
        try:
            dists = nx.single_source_dijkstra_path_length(
                G, u_node, weight="travel_time", cutoff=max_travel_time_sec
            )
        except TypeError:
            dists = nx.single_source_dijkstra_path_length(
                G, u_node, weight="travel_time"
            )
        node_dists[u_node] = dists

    # Fill the full (Sub x Sub) matrix using the pre-computed node distances
    task_mat_sec = np.full((n_sub, n_sub), np.nan, dtype=float)
    
    for i, sid_o in enumerate(sub_ids):
        node_o = sub_to_node[sid_o]
        dists_from_o = node_dists.get(node_o, {})
        
        for j, sid_d in enumerate(sub_ids):
            if i == j:
                task_mat_sec[i, j] = 0.0
                continue
                
            node_d = sub_to_node[sid_d]
            t_sec = dists_from_o.get(node_d, np.nan)
            
            if t_sec is not None and t_sec > max_travel_time_sec:
                t_sec = np.nan
            task_mat_sec[i, j] = t_sec

    # Convert to hours and create DataFrame
    task_mat_hr = task_mat_sec / 3600.0
    task_df = pd.DataFrame(task_mat_hr, index=sub_ids, columns=sub_ids)
    task_df.index.name = "id"

    # ---------------------------------------------------------
    # Quality Assurance Check
    # ---------------------------------------------------------
    nan_ratio = np.isnan(task_mat_hr).mean()
    if nan_ratio > 0.05: # Warn if > 5% of pairs are unreachable
        logger.error(f"CRITICAL WARNING: {nan_ratio:.2%} of Task-to-Task pairs are unreachable (NaN).")
        logger.error("Check if the graph is connected or if MAX_TRAVEL_TIME_SEC is too low.")
        # We raise an error to prevent bad data from entering the simulation
        raise ValueError("Too many unreachable substations in travel matrix.")
    else:
        logger.info(f"Travel matrix computed successfully. Unreachable pair ratio: {nan_ratio:.2%}")

    return base_to_task_df, task_df


def save_outputs(
    base_to_task: pd.DataFrame,
    task_to_task: pd.DataFrame,
    cfg: TravelMatrixConfig,
):
    """
    Save matrices to CSV in the format expected by 'C257H_Project_Main.py'.
    """
    logger = logging.getLogger()
    stage4_path = os.path.join(cfg.output_root, cfg.stage4_dir)
    ensure_dir(stage4_path)

    # 1. Save Base -> Task
    # Format: Index matches 'base_id' (C57 yard IDs), Columns match 'sub_id'
    out_base = os.path.join(stage4_path, cfg.travel_base_to_task_csv)
    base_to_task.to_csv(out_base, index=True)
    logger.info(f"Saved Base->Task matrix to: {out_base}")

    # 2. Save Task -> Task
    # Format: First column 'id', subsequent columns are sub_ids.
    # Note: We reset index to make 'id' a standard column, matching standard pandas read_csv behavior.
    df_task = task_to_task.copy()
    df_task.reset_index(inplace=True) 
    
    out_task = os.path.join(stage4_path, cfg.travel_task_to_task_csv)
    df_task.to_csv(out_task, index=False)
    logger.info(f"Saved Task->Task matrix to: {out_task}")


# ======================= MAIN EXECUTION =======================

def main(cfg: Optional[TravelMatrixConfig] = None):
    setup_logging()
    logger = logging.getLogger()
    logger.info("=== build_travel_matrices_osm: START ===")
    cfg = cfg if cfg is not None else TravelMatrixConfig()

    try:
        limit_to_sub_ids = cfg.limit_to_sub_ids
        if limit_to_sub_ids is None:
            limit_to_sub_ids = load_task_ids_from_mapping(cfg.mapping_csv)
            if limit_to_sub_ids is not None:
                logger.info(
                    "Aligned travel task universe to tract mapping baseline: %s substations.",
                    len(limit_to_sub_ids),
                )

        # 1. Load Data
        G = load_graph_with_travel_time(cfg.graphml_path)
        subs_df = load_substations(cfg, limit_to_sub_ids=limit_to_sub_ids)

        # 2. Map Coordinates to Graph
        sub_to_node = map_points_to_nodes(G, subs_df)
        base_nodes = get_base_nodes(G, cfg)

        # 3. Compute Matrices
        base_to_task, task_to_task = compute_travel_times(
            G,
            base_nodes,
            sub_to_node,
            max_travel_time_sec=cfg.max_travel_time_sec,
        )

        # 4. Save
        save_outputs(base_to_task, task_to_task, cfg)
        
        logger.info("=== build_travel_matrices_osm: DONE ===")
        
    except Exception as e:
        logger.exception("Fatal error during execution:")
        raise e

if __name__ == "__main__":
    main()
