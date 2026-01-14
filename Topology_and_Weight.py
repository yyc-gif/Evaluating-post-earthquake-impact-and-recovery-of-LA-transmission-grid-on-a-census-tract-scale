import logging
import os
from dataclasses import dataclass
from typing import Set

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely import wkt
from shapely.geometry import LineString, MultiLineString, MultiPoint, Point, box
from shapely.ops import snap, split


# ---------------------------------------------------------------------------
# 1) Config
# ---------------------------------------------------------------------------

from pathlib import Path

# Project root = the directory containing this script (the "Evaluating ..." folder)
PROJECT_ROOT = Path(__file__).resolve().parent

# Central data directory (inputs + exported derived files)
DATA_DIR = PROJECT_ROOT / "Data"


@dataclass
class Paths:
    """
    Central path configuration.

    All inputs are expected under ./Data.
    All derived outputs (mapping + graph CSVs + validation plots) are also written under ./Data
    to keep the workflow self-contained and reproducible.
    """

    # --------------------
    # Input paths (Data/)
    # --------------------
    DEVICES_CSV: str = str(DATA_DIR / "LA_Substations_WithFragility_UPDATED_CEC.csv")
    LA_TRACTS_SHP: str = str(DATA_DIR / "LA_Tracts_With_Population.shp")
    TRANSMISSION_LINES_SHP: str = str(DATA_DIR / "TransmissionLine_CEC.shp")
    CITY_TRACTS_LIST_CSV: str = str(DATA_DIR / "Tracts_Within_Los_Angeles.csv")

    # --------------------
    # Output paths (Data/)
    # --------------------
    OUTPUT_MAPPING_CSV: str = str(DATA_DIR / "tract_to_substation_mapping_CEC.csv")
    OUTPUT_GRAPH_EDGES_CSV: str = str(DATA_DIR / "substation_graph_CEC_edges.csv")
    OUTPUT_GRAPH_NODES_CSV: str = str(DATA_DIR / "substation_graph_CEC_nodes.csv")
    OUTPUT_PLOT_PNG: str = str(DATA_DIR / "topology_final_validation.png")

    # --------------------
    # Core parameters
    # --------------------
    BBOX_PAD_KM: float = 50.0
    LINE_SNAP_TOLERANCE_M: float = 50 # Strong snapping tolerance (meters)
    MAX_LINE_ENDPOINT_DIST_KM: float = 0.5
    LINE_SPLIT_TOLERANCE_M: float = 50.0  # Line split tolerance at substation points (meters)

PATHS = Paths()


# ---------------------------------------------------------------------------
# 2) Helpers
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
    )


def detect_geoid_col(df) -> str:
    """
    Detect a tract GEOID column name from common candidates.
    Raises ValueError if no candidate is found.
    """
    candidates = ["GEOID", "GEOID20", "GEOID10", "geoid", "TRACTCE", "tract_id"]
    for c in candidates:
        if c in df.columns:
            return c
    raise ValueError(f"Could not find tract ID col in {list(df.columns)}")


def load_city_whitelist(csv_path: str) -> Set[str]:
    """
    Load a whitelist of tract GEOIDs from a CSV and normalize to 11-char zero-padded strings.
    Returns an empty set if the CSV does not exist.
    """
    if not os.path.exists(csv_path):
        logging.warning(f"File not found: {csv_path}, skipping filter.")
        return set()

    df = pd.read_csv(csv_path)
    geoid_col = detect_geoid_col(df)
    return set(df[geoid_col].astype(str).str.strip().str.zfill(11))


def load_substations(devices_csv: str) -> gpd.GeoDataFrame:
    """
    Load substation points from a CSV and return a GeoDataFrame in EPSG:4326.
    Performs ID and lat/lon column normalization.
    """
    if not os.path.exists(devices_csv):
        raise FileNotFoundError(f"File not found: {devices_csv}")

    df = pd.read_csv(devices_csv)

    # ID normalization
    if "id" not in df.columns:
        if "HIFLD_ID" in df.columns:
            df = df.rename(columns={"HIFLD_ID": "id"})
        elif "OBJECTID" in df.columns:
            df["id"] = df["OBJECTID"].astype(str)
        elif "substation_id" in df.columns:
            df = df.rename(columns={"substation_id": "id"})
        else:
            df["id"] = df.index.astype(str)

    df["id"] = df["id"].astype(str).str.strip()

    # Coordinate normalization
    if "lon" not in df.columns and "Lon" in df.columns:
        df = df.rename(columns={"Lon": "lon"})
    if "lat" not in df.columns and "Lat" in df.columns:
        df = df.rename(columns={"Lat": "lat"})

    for col in ["lat", "lon"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lon"], df["lat"]),
        crs="EPSG:4326",
    )

    logging.info(f"Loaded {len(gdf)} substations.")
    return gdf


def load_tracts_filtered(shp_path: str, whitelist: Set[str]) -> gpd.GeoDataFrame:
    """
    Load tract polygons from a shapefile, project to EPSG:3310, normalize tract IDs,
    and optionally filter by a whitelist.
    """
    if not os.path.exists(shp_path):
        logging.warning("Tract shapefile missing, skipping.")
        return gpd.GeoDataFrame()

    gdf = gpd.read_file(shp_path).to_crs(epsg=3310)
    geoid_col = detect_geoid_col(gdf)
    gdf["tract_id"] = gdf[geoid_col].astype(str).str.strip().str.zfill(11)

    if whitelist:
        gdf = gdf[gdf["tract_id"].isin(whitelist)].copy()

    logging.info(f"Loaded {len(gdf)} filtered tracts.")
    return gdf


# ---------------------------------------------------------------------------
# 3) Topology Logic
# ---------------------------------------------------------------------------

def force_snap_endpoints_to_substations(
    lines_gdf: gpd.GeoDataFrame,
    subs_gdf: gpd.GeoDataFrame,
    tolerance_m: float,
) -> gpd.GeoDataFrame:
    """
    Force-snap line endpoints to the nearest substation point within `tolerance_m`.

    Key property: preserve all non-geometry attributes (e.g., kV). Only geometry
    coordinates are modified.
    """
    logging.info(
        "Force snapping line endpoints to substations (tolerance=%sm)...",
        tolerance_m,
    )

    # 1) Build a KDTree for substation coordinates (in the same CRS as lines_gdf)
    sub_coords = np.array([(p.x, p.y) for p in subs_gdf.geometry])
    sub_tree = cKDTree(sub_coords)

    new_geometries = []
    snapped_count = 0

    # Process geometry only; preserve other columns by copying the GeoDataFrame at the end.
    for geom in lines_gdf.geometry:
        if geom is None or geom.is_empty:
            new_geometries.append(geom)
            continue

        # Handle MultiLineString by processing each part independently.
        parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
        modified_parts = []

        for part in parts:
            coords = list(part.coords)
            if len(coords) < 2:
                modified_parts.append(part)
                continue

            start_pt = coords[0]
            end_pt = coords[-1]

            # Snap start endpoint if within tolerance
            d_start, idx_start = sub_tree.query(start_pt)
            if d_start <= tolerance_m:
                coords[0] = tuple(sub_coords[idx_start])
                snapped_count += 1

            # Snap end endpoint if within tolerance
            d_end, idx_end = sub_tree.query(end_pt)
            if d_end <= tolerance_m:
                coords[-1] = tuple(sub_coords[idx_end])
                snapped_count += 1

            modified_parts.append(LineString(coords))

        if len(modified_parts) == 1:
            new_geometries.append(modified_parts[0])
        else:
            new_geometries.append(MultiLineString(modified_parts))

    logging.info("Snapped %s endpoints to substation locations strictly.", snapped_count)

    out = lines_gdf.copy()
    out["geometry"] = new_geometries
    return out


def split_lines_at_points(
    lines_gdf: gpd.GeoDataFrame,
    points_gdf: gpd.GeoDataFrame,
    tolerance: float = 100.0,
) -> gpd.GeoDataFrame:
    """
    Split transmission lines at (projected) substation point locations.

    Steps:
      1) Explode MultiLineString features into single LineStrings.
      2) For each line, find nearby points via spatial index.
      3) Project points to the line; exclude near-endpoint projections.
      4) Split the line; all resulting segments inherit the original attributes.
    """
    logging.info("Splitting transmission lines at substation locations (preserving attributes)...")

    # Explode MultiLineString into LineString rows; explode duplicates attributes automatically.
    lines_gdf = lines_gdf.explode(index_parts=False).reset_index(drop=True)

    # Precompute columns to preserve
    attr_cols = [c for c in lines_gdf.columns if c != "geometry"]

    # Spatial index for points
    points_sindex = points_gdf.sindex

    new_rows = []  # list[dict]: each dict includes attributes + geometry

    for _, line_row in lines_gdf.iterrows():
        line_geom = line_row.geometry
        row_attrs = line_row[attr_cols].to_dict()

        if line_geom is None or line_geom.is_empty:
            continue

        xmin, ymin, xmax, ymax = line_geom.bounds
        possible_inds = list(
            points_sindex.intersection(
                (xmin - tolerance, ymin - tolerance, xmax + tolerance, ymax + tolerance)
            )
        )

        if not possible_inds:
            new_rows.append({**row_attrs, "geometry": line_geom})
            continue

        cut_points = []
        possible_points = points_gdf.iloc[possible_inds]

        start_p = Point(line_geom.coords[0])
        end_p = Point(line_geom.coords[-1])

        for _, pt_row in possible_points.iterrows():
            pt = pt_row.geometry
            if line_geom.distance(pt) < tolerance:
                proj_pt = line_geom.interpolate(line_geom.project(pt))

                # Exclude projections too close to endpoints (avoid degenerate splits)
                if not (proj_pt.dwithin(start_p, 0.1) or proj_pt.dwithin(end_p, 0.1)):
                    cut_points.append(proj_pt)

        if not cut_points:
            new_rows.append({**row_attrs, "geometry": line_geom})
            continue

        splitter = MultiPoint(cut_points)
        snapped_line = snap(line_geom, splitter, tolerance)
        result = split(snapped_line, splitter)

        for seg_geom in result.geoms:
            new_rows.append({**row_attrs, "geometry": seg_geom})

    result_gdf = gpd.GeoDataFrame(new_rows, crs=lines_gdf.crs)
    logging.info("Split completed. Lines count: %s -> %s", len(lines_gdf), len(result_gdf))
    return result_gdf


def _build_simple_graph(lines_gdf: gpd.GeoDataFrame) -> nx.MultiGraph:
    """
    Build a physical MultiGraph from line geometries.

    - Uses nx.MultiGraph to support parallel (multi) edges.
    - Attempts to detect a voltage column ("KV", "VOLTAGE", "VOLT") and stores as edge attribute `voltage`.
    - Stores edge attributes: `weight` (distance in CRS units), `length_km`, and `voltage`.
    """
    logging.info("Building MultiGraph with Voltage attributes...")

    lines_gdf = lines_gdf.explode(index_parts=False).reset_index(drop=True)
    G = nx.MultiGraph()

    def _coord_key(pt):
        return (round(pt[0], 1), round(pt[1], 1))

    # Detect voltage column
    kv_col = None
    for c in lines_gdf.columns:
        if str(c).upper() in {"KV", "VOLTAGE", "VOLT"}:
            kv_col = c
            break

    if kv_col:
        logging.info("Using column '%s' for voltage attributes.", kv_col)
    else:
        logging.warning("No voltage column found (expected 'kV' or 'VOLTAGE'). Edges will have voltage=0.")

    for _, row in lines_gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        # Voltage value (clean to float; fallback 0.0)
        voltage_val = row[kv_col] if kv_col else 0.0
        try:
            voltage_val = float(voltage_val)
        except Exception:
            voltage_val = 0.0

        coords = list(geom.coords)
        for i in range(len(coords) - 1):
            u = _coord_key(coords[i])
            v = _coord_key(coords[i + 1])

            dist = Point(u).distance(Point(v))
            if dist <= 0.1:
                continue

            G.add_edge(
                u,
                v,
                weight=dist,
                length_km=dist / 1000.0,
                voltage=voltage_val,
            )

    return G


def build_topology_wrapper(
    lines_path: str,
    subs_gdf: gpd.GeoDataFrame,
    bbox_pad_km: float,
    snap_tol: float,
):
    """
    Load + project transmission lines, clip to a padded substation bounding box,
    then apply:
      A) force-snap endpoints to substations
      B) split lines at (projected) substation points
      C) build a physical MultiGraph (with voltage attributes if available)

    Returns:
        (G, lines_split, subs_proj, lines_gdf)
        If failure, returns (None, None, None, None).
    """
    logger = logging.getLogger()

    # 1) Load lines and project
    if not os.path.exists(lines_path):
        logger.error(f"Transmission line file not found: {lines_path}")
        return None, None, None, None

    if lines_path.lower().endswith(".csv"):
        lines_df = pd.read_csv(lines_path)
        wkt_col = next(
            (c for c in lines_df.columns if "wkt" in c.lower() or "geom" in c.lower()),
            None,
        )
        if not wkt_col:
            logger.error("CSV does not contain WKT/geometry column.")
            return None, None, None, None

        lines_df["geometry"] = lines_df[wkt_col].apply(wkt.loads)
        lines_gdf = gpd.GeoDataFrame(lines_df, geometry="geometry", crs="EPSG:3857")
    else:
        lines_gdf = gpd.read_file(lines_path)

    lines_proj = lines_gdf.to_crs(epsg=3310)
    subs_proj = subs_gdf.to_crs(epsg=3310)

    # 2) Clip to padded bbox around substations
    minx, miny, maxx, maxy = subs_proj.total_bounds
    pad_m = bbox_pad_km * 1000.0

    lines_clipped = lines_proj.cx[
        minx - pad_m : maxx + pad_m,
        miny - pad_m : maxy + pad_m,
    ].copy()

    if lines_clipped.empty:
        logger.error("No transmission lines inside bbox.")
        return None, None, None, None

    # A) Force-snap line endpoints to substations (geometry-only edit; attrs preserved)
    lines_snapped = force_snap_endpoints_to_substations(
        lines_clipped,
        subs_proj,
        tolerance_m=snap_tol,
    )

    # B) Split lines at (projected) substation points (attrs preserved)
    lines_split = split_lines_at_points(
        lines_snapped,
        subs_proj,
        tolerance=PATHS.LINE_SPLIT_TOLERANCE_M,
    )

    # C) Build MultiGraph with voltage attributes (if present)
    G = _build_simple_graph(lines_split)

    return G, lines_split, subs_proj, lines_gdf


# ---------------------------------------------------------------------------
# 4) Direct substation links: compute + visualize + export
# ---------------------------------------------------------------------------

def calculate_connectivity(
    G: nx.Graph,
    subs_proj: gpd.GeoDataFrame,
    max_snap_km: float,
):
    """
    Map substations to nearest graph nodes (within max_snap_km),
    then compute pairwise substation distances via single-source Dijkstra from
    each substation node.

    Returns:
        dist_ss: dict[src_sid][tgt_sid] = shortest path distance (km)
        sub_id_to_node: dict[substation_id] = graph_node
        all_paths: dict[src_sid, dict[node, list[node]]] 
    """
    logger = logging.getLogger()

    graph_nodes = list(G.nodes())
    if not graph_nodes:
        return {}, {}, {}

    node_tree = cKDTree(np.array(graph_nodes))
    snap_dist_m = max_snap_km * 1000.0

    # 1) Snap substations to graph nodes.
    #    With force-snap earlier, this should match very tightly.
    sub_id_to_node = {}
    for _, row in subs_proj.iterrows():
        sid = str(row["id"])
        pt = (row.geometry.x, row.geometry.y)

        d, idx_node = node_tree.query(pt)
        if d <= snap_dist_m:
            sub_id_to_node[sid] = graph_nodes[idx_node]

    if not sub_id_to_node:
        logger.warning("No substations snapped to the network.")
        return {}, {}, {}

    # 2) Build node->substations reverse lookup (handles multiple subs at same node)
    node_to_subs = {}
    for sid, node in sub_id_to_node.items():
        node_to_subs.setdefault(node, []).append(sid)

    targets = set(sub_id_to_node.values())

    dist_ss = {sid: {} for sid in sub_id_to_node}
    all_paths = {}

    # 3) Single-source Dijkstra for each source substation
    for src_sid, src_node in sub_id_to_node.items():
        try:
            # Works on MultiGraph; picks minimum-weight edges automatically
            lengths, paths = nx.single_source_dijkstra(G, src_node, weight="weight")
            all_paths[src_sid] = paths

            for tgt_node in targets:
                if tgt_node not in lengths:
                    continue

                d_km = lengths[tgt_node] / 1000.0
                if tgt_node in node_to_subs:
                    for tgt_sid in node_to_subs[tgt_node]:
                        dist_ss[src_sid][tgt_sid] = d_km

        except Exception as e:
            logger.warning(f"Error calculating paths for {src_sid}: {e}")

    return dist_ss, sub_id_to_node, all_paths


def compute_direct_links(
    dist_ss,
    sub_id_to_node,
    all_paths,
    max_dist_km=None,
):
    """
    Identify "direct" substation adjacency:
      - reachable on the physical graph
      - path does not pass through any other substation node internally
      - optional max distance threshold (km)
      - undirected de-duplication (a,b) == (b,a)

    Returns:
        direct_links: list[dict] with keys: src, tgt, length_km, path_nodes
    """
    # node -> [substation_ids]
    node_to_subs = {}
    for sid, node in sub_id_to_node.items():
        sid = str(sid)
        node_to_subs.setdefault(node, []).append(sid)

    direct_links = []
    seen = set()  # dedupe undirected pairs

    for src_sid, src_node in sub_id_to_node.items():
        src_sid = str(src_sid)
        paths_from_src = all_paths.get(src_sid, {})

        for tgt_sid, tgt_node in sub_id_to_node.items():
            tgt_sid = str(tgt_sid)
            if tgt_sid == src_sid:
                continue

            # Not reachable on the physical graph
            if tgt_node not in paths_from_src:
                continue

            d_km = dist_ss.get(src_sid, {}).get(tgt_sid, np.inf)
            if not np.isfinite(d_km):
                continue
            if max_dist_km is not None and d_km > max_dist_km:
                continue

            path_nodes = paths_from_src[tgt_node]
            if len(path_nodes) < 2:
                continue

            # Reject if path interior intersects another substation node
            internal_nodes = path_nodes[1:-1]
            if any(n in node_to_subs for n in internal_nodes):
                continue

            a, b = sorted([src_sid, tgt_sid])
            key = (a, b)
            if key in seen:
                continue

            seen.add(key)
            direct_links.append(
                {
                    "src": a,
                    "tgt": b,
                    "length_km": float(d_km),
                    "path_nodes": path_nodes,
                }
            )

    logging.info(f"Computed {len(direct_links)} direct substation links.")
    return direct_links


def build_display_graph(direct_links):
    """
    Build a simple undirected display graph from the computed direct substation links.
    If multiple links exist between the same (src, tgt), keep the minimum length_km.
    """
    G_display = nx.Graph()

    for link in direct_links:
        src = str(link["src"])
        tgt = str(link["tgt"])
        d_km = float(link["length_km"])

        if src == tgt:
            continue

        if G_display.has_edge(src, tgt):
            if d_km < G_display[src][tgt].get("length_km", np.inf):
                G_display[src][tgt]["length_km"] = d_km
            continue

        G_display.add_edge(src, tgt, length_km=d_km)

    return G_display


def visualize_topology(
    G,
    lines_clipped,
    subs_proj,
    sub_id_to_node,
    direct_links,
    output_path,
):
    """
    Final visualization:
      1) clipped physical transmission lines (light grey)
      2) "direct" substation links (purple)
      3) substations classified by membership in the largest connected component:
         - main grid: green points
         - disconnected: red x + optional label annotation

    Note: plotting extents are set by a fixed LA City bbox in WGS84, reprojected to EPSG:3310.
    """
    logger = logging.getLogger()
    logger.info("Generating final visualization (physical lines + direct links)...")

    # ---------------------------------------------------------------------
    # 1) LA City bbox (WGS84) -> EPSG:3310 plotting bounds
    # ---------------------------------------------------------------------
    bbox_wgs = [-118.67, 33.70, -118.15, 34.34]

    p_min = (
        gpd.GeoSeries([Point(bbox_wgs[0], bbox_wgs[1])], crs="EPSG:4326")
        .to_crs(epsg=3310)
        .iloc[0]
    )
    p_max = (
        gpd.GeoSeries([Point(bbox_wgs[2], bbox_wgs[3])], crs="EPSG:4326")
        .to_crs(epsg=3310)
        .iloc[0]
    )

    fig, ax = plt.subplots(figsize=(15, 15))
    ax.set_xlim([p_min.x, p_max.x])
    ax.set_ylim([p_min.y, p_max.y])

    # ---------------------------------------------------------------------
    # 2) Physical transmission lines
    # ---------------------------------------------------------------------
    lines_clipped.plot(ax=ax, color="lightgrey", linewidth=0.5, zorder=1)

    # ---------------------------------------------------------------------
    # 3) Direct substation links (purple)
    # ---------------------------------------------------------------------
    if direct_links:
        path_geoms = [LineString(link["path_nodes"]) for link in direct_links]
        gpd.GeoSeries(path_geoms, crs="EPSG:3310").plot(
            ax=ax,
            color="purple",
            linewidth=1.5,
            alpha=0.7,
            zorder=2,
            label="Direct substation links",
        )

    # ---------------------------------------------------------------------
    # 4) Substation connectivity status (largest connected component)
    # ---------------------------------------------------------------------
    main_ids, island_ids = [], []

    if len(G) > 0:
        comps = list(nx.connected_components(G))
        main_comp = max(comps, key=len)

        main_ids = [
            sid for sid, node in sub_id_to_node.items()
            if node in main_comp
        ]
        island_ids = [
            sid for sid, node in sub_id_to_node.items()
            if node not in main_comp
        ]

        if main_ids:
            subs_proj[subs_proj["id"].isin(main_ids)].plot(
                ax=ax,
                color="green",
                markersize=50,
                label=f"Main Grid ({len(main_ids)})",
                zorder=3,
            )

        if island_ids:
            subs_proj[subs_proj["id"].isin(island_ids)].plot(
                ax=ax,
                color="red",
                marker="x",
                markersize=80,
                label=f"Disconnected ({len(island_ids)})",
                zorder=3,
            )

            # Annotate disconnected substations within plotting bbox
            island_subs = subs_proj[subs_proj["id"].isin(island_ids)]
            for _, row in island_subs.iterrows():
                x, y = row.geometry.x, row.geometry.y
                if p_min.x < x < p_max.x and p_min.y < y < p_max.y:
                    ax.annotate(
                        row.get("Name", row["id"]),
                        (x, y),
                        xytext=(3, 3),
                        textcoords="offset points",
                        fontsize=9,
                        color="red",
                        fontweight="bold",
                    )

    # ---------------------------------------------------------------------
    # 5) Final plot settings + save
    # ---------------------------------------------------------------------
    plt.title(
        "LA Power Grid Topology (Force Snapped & Validated)\n"
        f"Connected: {len(main_ids)} | Isolated: {len(island_ids)}",
        fontsize=20,
    )
    plt.legend(loc="upper right", fontsize=18)
    plt.axis("off")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    logger.info(f"Validation plot saved to: {output_path}")


# ---------------------------------------------------------------------------
# 5. W Matrix & Export
# ---------------------------------------------------------------------------

# Global IDW parameters
IDW_POWER: float = 2.0         # w ~ 1 / d^p (default p=1)
MIN_DIST: float = 1e-3          # avoid division by zero when d == 0
MIN_EFFECTIVE_WEIGHT: float = 0.01


def build_W_matrix(
    subs_gdf,
    tracts_gdf,
    dist_ss,
) -> pd.DataFrame:
    """
    Build tract-to-substation weight matrix W using IDW over network-reachable substations.

    Logic (unchanged):
      - For each tract, pick a single "access" substation by Euclidean distance (centroid -> substation).
      - For every substation, compute total distance:
            d_total = access_dist + network_shortest_path(access_sub, target_sub)
        (If target == access_sub, enforce a finite distance at least equal to access_dist.)
      - Apply inverse-distance weighting on all finite d_total:
            w_j ∝ 1 / d_total^IDW_POWER
      - Normalize each row to sum to 1.
      - If no substations are reachable (all inf), fall back to the nearest Euclidean substation with weight 1.
    """
    if tracts_gdf.empty:
        return pd.DataFrame()

    # Project to EPSG:3310 for metric distance calculations
    tracts_3310 = tracts_gdf.to_crs(epsg=3310)
    subs_3310 = subs_gdf.to_crs(epsg=3310)

    sub_ids = subs_3310["id"].astype(str).tolist()
    n_sub = len(sub_ids)

    sub_coords = np.column_stack((subs_3310.geometry.x, subs_3310.geometry.y))

    W_rows = []
    tract_ids = []

    logging.info("Building W matrix (IDW over all reachable substations)...")

    for _, tract_row in tracts_3310.iterrows():
        tid = str(tract_row["tract_id"])

        centroid = tract_row.geometry.centroid
        t_x, t_y = centroid.x, centroid.y

        # 1) Choose a single access substation by Euclidean distance (km)
        dists_euc_km = (
            np.sqrt((sub_coords[:, 0] - t_x) ** 2 + (sub_coords[:, 1] - t_y) ** 2) / 1000.0
        )
        nearest_idx = int(np.argmin(dists_euc_km))
        access_sub_id = sub_ids[nearest_idx]
        access_dist_km = float(dists_euc_km[nearest_idx])

        # 2) Total distance to each substation = access_dist + network_dist(access_sub -> target_sub)
        network_dists = dist_ss.get(access_sub_id, {})
        d_total_km = np.full(n_sub, np.inf)

        for j, target_sub_id in enumerate(sub_ids):
            net_d_km = network_dists.get(target_sub_id, np.inf)

            if np.isfinite(net_d_km):
                d_total_km[j] = access_dist_km + net_d_km
            elif target_sub_id == access_sub_id:
                # Ensure at least the access node is finite
                d_total_km[j] = access_dist_km

        valid_idx = np.where(np.isfinite(d_total_km))[0]

        if len(valid_idx) == 0:
            # Extreme fallback: nothing reachable -> assign full weight to nearest Euclidean substation
            w_row = np.zeros(n_sub)
            w_row[nearest_idx] = 1.0
        else:
            # 3) IDW on all finite distances: w ∝ 1 / d^p
            d_subset = d_total_km[valid_idx]

            # Avoid 0 distance => infinite weight
            d_subset = np.where(d_subset <= 0.0, MIN_DIST, d_subset)

            w_raw = 1.0 / (d_subset ** IDW_POWER)

            if w_raw.sum() > 0:
                w_row = np.zeros(n_sub)
                w_row[valid_idx] = w_raw / w_raw.sum()
            else:
                # Defensive fallback (should be rare): assign full weight to nearest
                w_row = np.zeros(n_sub)
                w_row[nearest_idx] = 1.0

        W_rows.append(w_row)
        tract_ids.append(tid)

    return pd.DataFrame(W_rows, index=tract_ids, columns=sub_ids)


def apply_min_weight_threshold(
    W: pd.DataFrame,
    min_weight: float = MIN_EFFECTIVE_WEIGHT,
) -> pd.DataFrame:
    """
    Apply a per-row minimum effective weight threshold.

    Logic (unchanged):
      1) Set weights < min_weight to 0
      2) Renormalize each row to sum to 1
      3) If a row becomes all zeros, revert to a one-hot vector at the largest entry
         from the original (pre-threshold) row.
    """
    if W.empty:
        return W

    # Keep a copy for fallback in case an entire row is zeroed out
    W_orig = W.copy()
    W_thr = W.copy()

    # 1) Thresholding: zero out small weights
    W_thr[W_thr < min_weight] = 0.0

    # 2) Compute row sums
    row_sums = W_thr.sum(axis=1)

    # 3) Rows that became all-zero after thresholding
    zero_rows = row_sums[row_sums <= 0.0].index

    for rid in zero_rows:
        row = W_orig.loc[rid]
        j = int(row.values.argmax())
        col = W_thr.columns[j]

        W_thr.loc[rid, :] = 0.0
        W_thr.loc[rid, col] = 1.0

    # Recompute row sums and renormalize
    row_sums = W_thr.sum(axis=1)
    W_thr = W_thr.div(row_sums, axis=0)

    return W_thr


def export_mapping_from_W(W, tracts_gdf, subs_gdf, out_csv):
    """
    Export tract-to-substation mapping table from W.

    Logic (unchanged):
      1) Export all (tract_id, substation_id, weight) entries where weight > 1e-6.
      2) Ensure every substation appears at least once; if missing, inject a tiny weight (1e-3)
         by assigning that substation to the nearest tract (by centroid distance).
      3) Append tract population if available.
      4) Append substation lat/lon.
      5) Write a single CSV to out_csv.
    """
    if W.empty:
        return

    WEIGHT_EXPORT_EPS = 1e-6
    INJECT_EPS_WEIGHT = 1e-3

    # ---------------------------------------------------------------------
    # 1) Export non-trivial weights from W (original threshold: > 1e-6)
    # ---------------------------------------------------------------------
    records = []
    for tid, row in W.iterrows():
        nz = row[row > WEIGHT_EXPORT_EPS]
        for sid, w in nz.items():
            records.append(
                {
                    "tract_id": str(tid),
                    "substation_id": str(sid),
                    "weight": float(w),
                }
            )

    df = pd.DataFrame(records)

    # ---------------------------------------------------------------------
    # 2) Ensure each substation appears at least once
    # ---------------------------------------------------------------------
    all_sub_ids = subs_gdf["id"].astype(str).tolist()

    if df.empty:
        used_sub_ids = set()
    else:
        df["substation_id"] = df["substation_id"].astype(str)
        df["tract_id"] = df["tract_id"].astype(str)
        used_sub_ids = set(df["substation_id"].tolist())

    missing_subs = [sid for sid in all_sub_ids if sid not in used_sub_ids]

    if missing_subs:
        logging.warning(
            f"{len(missing_subs)} substations have no non-zero weights in W. "
            f"Injecting minimal weights so each appears at least once."
        )

        if tracts_gdf.empty:
            logging.warning(
                "Tracts GeoDataFrame is empty; cannot attach missing substations to nearest tracts."
            )
        else:
            # Use tract CRS for nearest-tract lookup (keep original behavior)
            tracts_proj = tracts_gdf
            try:
                subs_proj = subs_gdf.to_crs(tracts_proj.crs) if subs_gdf.crs != tracts_proj.crs else subs_gdf
            except Exception:
                # Defensive fallback if CRS metadata is problematic
                subs_proj = subs_gdf.to_crs(tracts_proj.crs)

            centroids = tracts_proj.geometry.centroid
            tract_ids_list = tracts_proj["tract_id"].astype(str).tolist()

            injected_rows = []
            for sid in missing_subs:
                sub_row = subs_proj[subs_proj["id"].astype(str) == sid]
                if sub_row.empty:
                    logging.warning(
                        f"Substation {sid} not found in subs_gdf; skip injecting mapping for it."
                    )
                    continue

                sub_pt = sub_row.geometry.iloc[0]
                dists = centroids.distance(sub_pt).values
                nearest_idx = int(np.argmin(dists))
                tid = tract_ids_list[nearest_idx]

                injected_rows.append(
                    {
                        "tract_id": str(tid),
                        "substation_id": str(sid),
                        "weight": float(INJECT_EPS_WEIGHT),
                    }
                )

            if injected_rows:
                df = pd.concat([df, pd.DataFrame(injected_rows)], ignore_index=True)

    # ---------------------------------------------------------------------
    # 3) Append population (if available)
    # ---------------------------------------------------------------------
    pop_col = next(
        (c for c in ["population", "POPULATION", "E_TOTPOP", "totpop"] if c in tracts_gdf.columns),
        None,
    )

    if pop_col:
        pop_map = tracts_gdf.set_index("tract_id")[pop_col].to_dict()
        df["population"] = df["tract_id"].map(pop_map).fillna(0).astype(int)
    else:
        df["population"] = 0

    # ---------------------------------------------------------------------
    # 4) Append substation lat/lon
    # ---------------------------------------------------------------------
    lat_map = subs_gdf.set_index("id")["lat"].to_dict()
    lon_map = subs_gdf.set_index("id")["lon"].to_dict()
    df["lat"] = df["substation_id"].map(lat_map)
    df["lon"] = df["substation_id"].map(lon_map)

    # ---------------------------------------------------------------------
    # 5) Single CSV write (only once)
    # ---------------------------------------------------------------------
    df.to_csv(out_csv, index=False)
    logging.info(f"Mapping saved to {out_csv}")


def export_graph_csv(G, edges_csv, nodes_csv, subs_gdf):
    """
    Export graph nodes/edges CSVs.

    Behavior:
      - nodes_csv: writes (id, lat, lon) from subs_gdf
      - edges_csv: defensive fallback exporting nx.to_pandas_edgelist(G)
    """
    if nodes_csv:
        ndf = subs_gdf[["id", "lat", "lon"]].copy()
        ndf["id"] = ndf["id"].astype(str)
        ndf.to_csv(nodes_csv, index=False)
        logging.info(f"Nodes exported to {nodes_csv}")

    if edges_csv:
        # Defensive path: usually not used, but preserved
        edf = nx.to_pandas_edgelist(G)

        rename_map = {}
        if "source" in edf.columns:
            rename_map["source"] = "u"
        if "target" in edf.columns:
            rename_map["target"] = "v"
        if "length_km" not in edf.columns and "weight" in edf.columns:
            rename_map["weight"] = "length_km"

        edf = edf.rename(columns=rename_map)

        cols_to_save = ["u", "v", "length_km"]
        valid_cols = [c for c in cols_to_save if c in edf.columns]

        edf[valid_cols].to_csv(edges_csv, index=False)
        logging.info(f"Edges exported to {edges_csv} (Columns: {valid_cols})")


def export_edges_from_direct_links(direct_links, edges_csv):
    """
    Export undirected unique edges derived from direct_links.

    Logic:
      - Deduplicate undirected pairs (u, v)
      - Save columns: u, v, length_km
    """
    if not edges_csv:
        return

    rows = []
    seen = set()

    for link in direct_links:
        u = str(link["src"])
        v = str(link["tgt"])
        if u == v:
            continue

        a, b = sorted([u, v])
        key = (a, b)
        if key in seen:
            continue

        seen.add(key)
        rows.append({"u": a, "v": b, "length_km": float(link["length_km"])})

    df = pd.DataFrame(rows).sort_values(["u", "v"]).reset_index(drop=True)
    df.to_csv(edges_csv, index=False)
    logging.info(f"Edges (from direct_links) exported to {edges_csv} (n={len(df)})")


def debug_compare_direct_links_and_edges(direct_links, G_display, debug_prefix=None):
    """
    Compare unique undirected edges derived from:
      - direct_links (list of dicts with src/tgt/length_km/path_nodes)
      - G_display (nx.Graph built from direct_links)

    If debug_prefix is provided, write CSV diagnostics:
      - *_direct_links_all.csv
      - *_G_display_all.csv
      - *_only_in_direct_links.csv
      - *_only_in_G_display.csv
    """
    # ---------------------------------------------------------------------
    # 1) direct_links -> unique (u, v) with segment counts
    # ---------------------------------------------------------------------
    dl_rows = []
    for link in direct_links:
        a = str(link["src"])
        b = str(link["tgt"])
        u, v = sorted([a, b])

        n_nodes = len(link.get("path_nodes", []))
        n_edges = max(n_nodes - 1, 0)

        dl_rows.append(
            {
                "u": u,
                "v": v,
                "length_km": float(link["length_km"]),
                "n_nodes": n_nodes,
                "n_edges": n_edges,
            }
        )

    dl_df = pd.DataFrame(dl_rows).drop_duplicates(subset=["u", "v"])
    set_dl = set(zip(dl_df["u"], dl_df["v"]))

    # ---------------------------------------------------------------------
    # 2) G_display -> unique (u, v)
    # ---------------------------------------------------------------------
    g_rows = []
    for u, v, data in G_display.edges(data=True):
        a, b = sorted([str(u), str(v)])
        g_rows.append(
            {
                "u": a,
                "v": b,
                "length_km": float(data.get("length_km", np.nan)),
            }
        )

    g_df = pd.DataFrame(g_rows).drop_duplicates(subset=["u", "v"])
    set_g = set(zip(g_df["u"], g_df["v"]))

    # ---------------------------------------------------------------------
    # 3) Set differences + logging
    # ---------------------------------------------------------------------
    only_in_dl = set_dl - set_g
    only_in_g = set_g - set_dl

    logging.info(f"[DEBUG] direct_links unique edges: {len(set_dl)}")
    logging.info(f"[DEBUG] G_display edges:          {len(set_g)}")
    logging.info(f"[DEBUG] only in direct_links:     {len(only_in_dl)}")
    logging.info(f"[DEBUG] only in G_display:        {len(only_in_g)}")

    if not dl_df.empty:
        logging.info("[DEBUG] Direct link segment counts per pair (u -- v):")
        for _, r in dl_df.iterrows():
            logging.info(
                f"    {r['u']} -- {r['v']}: "
                f"length={r['length_km']:.2f} km, segments={int(r['n_edges'])}"
            )

    # ---------------------------------------------------------------------
    # 4) Optional CSV dumps
    # ---------------------------------------------------------------------
    if debug_prefix:
        os.makedirs(os.path.dirname(debug_prefix), exist_ok=True)

        dl_df.to_csv(f"{debug_prefix}_direct_links_all.csv", index=False)
        g_df.to_csv(f"{debug_prefix}_G_display_all.csv", index=False)

        pd.DataFrame(list(only_in_dl), columns=["u", "v"]).to_csv(
            f"{debug_prefix}_only_in_direct_links.csv",
            index=False,
        )
        pd.DataFrame(list(only_in_g), columns=["u", "v"]).to_csv(
            f"{debug_prefix}_only_in_G_display.csv",
            index=False,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    setup_logging()
    logger = logging.getLogger()

    try:
        whitelist = load_city_whitelist(PATHS.CITY_TRACTS_LIST_CSV)
        subs = load_substations(PATHS.DEVICES_CSV)
        tracts = load_tracts_filtered(PATHS.LA_TRACTS_SHP, whitelist)

        # 1) Build physical topology
        G, lines_clipped, subs_proj, _ = build_topology_wrapper(
            PATHS.TRANSMISSION_LINES_SHP,
            subs,
            PATHS.BBOX_PAD_KM,
            PATHS.LINE_SNAP_TOLERANCE_M,
        )

        if G is None:
            logger.error("Topology calculation failed.")
            logger.info("ALL DONE.")
            return

        # 2) Compute along-network shortest paths between substations
        dist_ss, sub_node_map, all_paths = calculate_connectivity(
            G,
            subs_proj,
            PATHS.MAX_LINE_ENDPOINT_DIST_KM,
        )

        # 3) Extract “direct adjacency” links between substations
        direct_links = compute_direct_links(
            dist_ss,
            sub_node_map,
            all_paths,
            max_dist_km=None,
        )

        # 4) Visualize physical network + direct links (full view)
        visualize_topology(
            G,
            lines_clipped,
            subs_proj,
            sub_node_map,
            direct_links,
            PATHS.OUTPUT_PLOT_PNG,
        )

        # 5) Build simplified substation-level graph
        G_display = build_display_graph(direct_links)

        # 5a) Debug direct_links vs G_display
        debug_prefix = os.path.join(
            os.path.dirname(PATHS.OUTPUT_GRAPH_EDGES_CSV),
            "debug_topology",
        )
        debug_compare_direct_links_and_edges(
            direct_links,
            G_display,
            debug_prefix=debug_prefix,
        )

        # 5b) Export nodes (edges intentionally skipped here)
        export_graph_csv(
            G_display,
            None,  # do not export edges here
            PATHS.OUTPUT_GRAPH_NODES_CSV,
            subs,
        )

        # 5c) Export edges from direct_links
        export_edges_from_direct_links(
            direct_links,
            PATHS.OUTPUT_GRAPH_EDGES_CSV,
        )

        # 6) Build W matrix
        W = build_W_matrix(
            subs,
            tracts,
            dist_ss,
        )

        # 6b) Apply per-row minimum effective weight threshold + renormalize
        W = apply_min_weight_threshold(W, min_weight=MIN_EFFECTIVE_WEIGHT)

        # 7) Export mapping (keeping “each sub appears at least once” logic)
        export_mapping_from_W(
            W,
            tracts,
            subs,
            PATHS.OUTPUT_MAPPING_CSV,
        )

        logger.info("ALL DONE.")

    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
