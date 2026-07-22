import logging
import os
import json
from dataclasses import dataclass
from typing import Optional, Set

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from topology_outputs import (
    apply_min_weight_threshold,
    build_W_matrix,
    export_edges_from_direct_links,
    export_mapping_from_W,
    export_nodes_csv,
)
from topology_visualization import (
    visualize_topology,
    visualize_topology_interactive,
)
from shapely import wkt
from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.ops import substring


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
    DEVICES_CSV: str = str(DATA_DIR / "working_area_substations_with_fragility.csv")
    LA_TRACTS_SHP: str = str(DATA_DIR / "LA_Tracts_With_Population.shp")
    TRANSMISSION_LINES_SHP: str = str(DATA_DIR / "TransmissionLine_CEC.shp")
    CITY_TRACTS_LIST_CSV: str = str(DATA_DIR / "Tracts_Within_Expanded_Area.csv")

    # --------------------
    # Output paths (Data/)
    # --------------------
    OUTPUT_MAPPING_CSV: str = str(DATA_DIR / "tract_to_substation_mapping_CEC_expanded.csv")
    OUTPUT_UNTHRESHOLDED_MAPPING_CSV: str = str(
        DATA_DIR / "tract_to_substation_mapping_CEC_expanded_unthresholded.csv"
    )
    OUTPUT_GRAPH_EDGES_CSV: str = str(DATA_DIR / "substation_graph_CEC_edges_expanded.csv")
    OUTPUT_GRAPH_NODES_CSV: str = str(DATA_DIR / "substation_graph_CEC_nodes_expanded.csv")
    OUTPUT_PLOT_PNG: Optional[str] = str(DATA_DIR / "topology_final_validation_expanded.png")
    OUTPUT_INTERACTIVE_HTML: str = str(DATA_DIR / "topology_interactive_validation_expanded.html")
    OUTPUT_SUPPRESSED_THRESHOLD_CSV: str = str(DATA_DIR / "substations_suppressed_by_threshold_expanded.csv")
    OUTPUT_LINE_SPLIT_AUDIT_CSV: str = str(DATA_DIR / "transmission_line_substation_split_audit_expanded.csv")
    OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_AUDIT_CSV: str = str(DATA_DIR / "direct_link_projection_anchor_audit_expanded.csv")
    OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_DEBUG_CSV: str = str(DATA_DIR / "direct_link_projection_anchor_debug_expanded.csv")

    # --------------------
    # Core parameters
    # --------------------
    BBOX_PAD_KM: float = 50.0
    LINE_SNAP_TOLERANCE_M: float = 150.0  # Active primary endpoint-to-substation snap tier.
    LINE_SNAP_SECONDARY_TOLERANCE_M: float = 375.0  # Active guarded secondary consideration tier.
    LINE_SNAP_SECONDARY_RATIO_MAX: float = 0.75  # Active secondary nearest/second-nearest ratio guard.
    LINE_SNAP_SECONDARY_MARGIN_M: float = 75.0  # Active secondary nearest/second-nearest distance margin.
    LINE_SNAP_SECONDARY_OUTER_START_M: Optional[float] = 300.0  # Stricter secondary shell start.
    LINE_SNAP_SECONDARY_OUTER_MARGIN_M: Optional[float] = 300.0  # Stricter outer-shell margin.
    LINE_SNAP_SECONDARY_OUTER_RATIO_MAX: Optional[float] = 0.55  # Stricter outer-shell ratio.
    MAX_SUBSTATION_TO_GRAPH_SNAP_DIST_M: float = 250.0
    ENABLE_PROTECTED_JUNCTION_CLUSTER_SNAP: bool = True
    ENABLE_SUBSTATION_LINE_SPLIT: bool = True
    LINE_SPLIT_TOLERANCE_M: float = 10.0
    LINE_SPLIT_MIN_ENDPOINT_DIST_M: float = 25.0
    LINE_SPLIT_MIN_SEGMENT_LENGTH_M: float = 10.0
    ENABLE_SUBSTATION_PROJECTION_CONNECTORS: bool = True
    DIRECT_LINK_MAX_DIST_KM: Optional[float] = None
    LINE_ENDPOINT_MERGE_TOLERANCE_M: float = 75.0
    EXCLUDE_BBOX_EDGE_ENDPOINTS_FROM_MERGE: bool = True
    BBOX_EDGE_EXCLUSION_BUFFER_M: float = 100.0
    MIN_EFFECTIVE_WEIGHT: float = 0.03


ACCEPTED_SUBSTATION_SNAP_TYPES = {
    "substation_snap_primary",
    "substation_snap_secondary",
    "protected_junction_cluster_snap",
    "local_substation_anchor_fix",
}

DOUBLE_SNAP_MAX_LENGTH_M: float = 250.0
DOUBLE_SNAP_SUPPRESS_REASON: str = "same_substation_double_snap_suppressed"
LINE_JUNCTION_PROTECT_REASON: str = "existing_line_junction_protected"


TRANSMISSION_LINE_ATTRIBUTE_OVERRIDES = {
    # LA BREA area: CEC labels these short LADWP-owned segments as SCE 220kV,
    # but local topology and adjacent line attributes indicate LADWP 138kV.
    "b0b99ac7-11e7-432c-ab70-4180dea52a14": {
        "Name": "LADWP 138kV",
        "kV": "138",
        "kV_Sort": "138",
        "Owner": "LADWP",
        "Legend": "LADWP_115_138kV",
    },
    "3a539900-975c-4b32-8262-c1090804868d": {
        "Name": "LADWP 138kV",
        "kV": "138",
        "kV_Sort": "138",
        "Owner": "LADWP",
        "Legend": "LADWP_115_138kV",
    },
    "87b12e66-0050-4150-980e-eb843eb9ff9f": {
        "Name": "LADWP 138kV",
        "kV": "138",
        "kV_Sort": "138",
        "Owner": "LADWP",
        "Legend": "LADWP_115_138kV",
    },
    # LADWP Barren Ridge: source rows omit owner/voltage in the CEC file, but
    # public references and surrounding topology support treating it as LADWP 230kV.
    "6c51e02d-a56f-4054-b576-9cc45ad851b6": {
        "Name": "LADWP Barren Ridge",
        "kV": "230",
        "kV_Sort": "230",
        "Owner": "LADWP",
        "Legend": "LADWP_220_287kV",
    },
}


# ---------------------------------------------------------------------------
# 2) Helpers
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """Initialize module-wide logging for the topology-construction workflow."""
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
    if "lon" not in df.columns and "LONGITUDE" in df.columns:
        df = df.rename(columns={"LONGITUDE": "lon"})
    if "lat" not in df.columns and "LATITUDE" in df.columns:
        df = df.rename(columns={"LATITUDE": "lat"})

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
    strict_tolerance_m: Optional[float] = None,
    extended_tolerance_m: Optional[float] = None,
    second_nearest_margin_m: Optional[float] = None,
    second_nearest_ratio_max: Optional[float] = None,
    secondary_outer_start_m: Optional[float] = None,
    secondary_outer_margin_m: Optional[float] = None,
    secondary_outer_ratio_max: Optional[float] = None,
    tolerance_m: Optional[float] = None,
    return_endpoint_audit: bool = False,
):
    """
    Snap true line endpoints to nearby substations under the audited guard rules.

    This is the authoritative geometry-repair stage of the topology workflow.
    Only start and end vertices are eligible for movement, non-geometry line
    attributes are preserved, and each endpoint receives a detailed diagnostic
    record describing whether it was accepted, rejected, or left unchanged.
    """
    if tolerance_m is not None and strict_tolerance_m is None:
        strict_tolerance_m = tolerance_m
    if strict_tolerance_m is None:
        raise ValueError("strict_tolerance_m must be provided explicitly.")
    if extended_tolerance_m is None:
        extended_tolerance_m = strict_tolerance_m
    if second_nearest_margin_m is None:
        raise ValueError("second_nearest_margin_m must be provided explicitly.")
    if second_nearest_ratio_max is None:
        raise ValueError("second_nearest_ratio_max must be provided explicitly.")

    strict_tolerance_m = float(strict_tolerance_m)
    extended_tolerance_m = max(float(extended_tolerance_m), strict_tolerance_m)
    second_nearest_margin_m = float(second_nearest_margin_m)
    second_nearest_ratio_max = float(second_nearest_ratio_max)
    secondary_outer_start_m = (
        float(secondary_outer_start_m)
        if secondary_outer_start_m is not None
        else None
    )
    secondary_outer_margin_m = (
        float(secondary_outer_margin_m)
        if secondary_outer_margin_m is not None
        else second_nearest_margin_m
    )
    secondary_outer_ratio_max = (
        float(secondary_outer_ratio_max)
        if secondary_outer_ratio_max is not None
        else second_nearest_ratio_max
    )
    secondary_outer_guard_enabled = (
        secondary_outer_start_m is not None
        and extended_tolerance_m > secondary_outer_start_m
    )

    logging.info(
        (
            "Force snapping line endpoints to substations "
            "(primary=%sm, secondary=%sm, secondary_ratio_max=%s, secondary_margin=%sm)..."
        ),
        strict_tolerance_m,
        extended_tolerance_m,
        second_nearest_ratio_max,
        second_nearest_margin_m,
    )
    if secondary_outer_guard_enabled:
        logging.info(
            (
                "Secondary outer snap guard active "
                "(outer_start=%sm, outer_margin=%sm, outer_ratio_max=%s)."
            ),
            secondary_outer_start_m,
            secondary_outer_margin_m,
            secondary_outer_ratio_max,
        )

    if subs_gdf.empty:
        logging.warning("No substations available for endpoint snapping.")
        out = lines_gdf.copy()
        if return_endpoint_audit:
            return out, pd.DataFrame()
        return out

    # 1) Build a KDTree for substation coordinates (in the same CRS as lines_gdf)
    sub_coords = np.array([(p.x, p.y) for p in subs_gdf.geometry])
    sub_tree = cKDTree(sub_coords)
    sub_ids = subs_gdf["id"].astype(str).str.strip().tolist()
    name_col = next(
        (c for c in ["NAME", "name", "Name", "SUBSTATION", "substation_name", "station_name"] if c in subs_gdf.columns),
        None,
    )
    if name_col is not None:
        sub_names = subs_gdf[name_col].fillna("").astype(str).str.strip().tolist()
    else:
        sub_names = [""] * len(sub_ids)

    endpoint_junction_peer_counts = {}
    vertex_registry = {}
    for line_row_idx, (_, row) in enumerate(lines_gdf.iterrows()):
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
        for part_idx, part in enumerate(parts):
            coords = list(part.coords)
            if len(coords) < 2:
                continue
            for coord_idx, coord in enumerate(coords):
                node_key = _graph_node_key(coord)
                occurrence = (line_row_idx, int(part_idx), int(coord_idx))
                vertex_registry.setdefault(node_key, []).append(occurrence)

    for line_row_idx, (_, row) in enumerate(lines_gdf.iterrows()):
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
        for part_idx, part in enumerate(parts):
            coords = list(part.coords)
            if len(coords) < 2:
                continue
            endpoint_specs = [
                ("start", 0),
                ("end", len(coords) - 1),
            ]
            for endpoint_type, coord_idx in endpoint_specs:
                coord = coords[coord_idx]
                node_key = _graph_node_key(coord)
                own_occurrence = (line_row_idx, int(part_idx), int(coord_idx))
                peers = [
                    occurrence
                    for occurrence in vertex_registry.get(node_key, [])
                    if occurrence != own_occurrence
                ]
                if peers:
                    endpoint_junction_peer_counts[
                        (line_row_idx, int(part_idx), endpoint_type)
                    ] = len(peers)

    def _query_two_nearest(endpoint_xy: tuple[float, float]) -> dict:
        """Query the nearest and second-nearest substations for one endpoint."""
        k = min(2, len(sub_coords))
        dists, idxs = sub_tree.query(endpoint_xy, k=k)

        if np.isscalar(dists):
            dists = [float(dists)]
            idxs = [int(idxs)]
        else:
            dists = [float(x) for x in np.atleast_1d(dists).tolist()]
            idxs = [int(x) for x in np.atleast_1d(idxs).tolist()]

        nearest = {
            "id": sub_ids[idxs[0]],
            "name": sub_names[idxs[0]],
            "distance_m": float(dists[0]),
            "coord": tuple(float(v) for v in sub_coords[idxs[0]]),
        }

        second = None
        if len(dists) > 1 and np.isfinite(dists[1]):
            second = {
                "id": sub_ids[idxs[1]],
                "distance_m": float(dists[1]),
            }

        return {"nearest": nearest, "second": second}

    def _evaluate_snap(
        endpoint_xy: tuple[float, float],
        *,
        line_junction_peer_count: int = 0,
    ) -> dict:
        """Evaluate one endpoint against the active primary and secondary snap rules."""
        query = _query_two_nearest(endpoint_xy)
        nearest = query["nearest"]
        second = query["second"]
        d1 = nearest["distance_m"]
        d2 = second["distance_m"] if second is not None else np.nan

        result = {
            "repaired_coord": tuple(float(v) for v in endpoint_xy),
            "repair_type": "none",
            "snap_decision_reason": "outside_secondary_tolerance",
            "nearest_substation_id": nearest["id"],
            "nearest_substation_name": nearest["name"],
            "nearest_distance_m": float(d1),
            "second_nearest_substation_id": second["id"] if second is not None else None,
            "second_nearest_distance_m": float(d2) if second is not None else np.nan,
            "line_junction_protected": bool(line_junction_peer_count),
            "line_junction_peer_count": int(line_junction_peer_count),
        }

        if line_junction_peer_count:
            result["snap_decision_reason"] = LINE_JUNCTION_PROTECT_REASON
            return result

        if d1 <= strict_tolerance_m:
            result["repaired_coord"] = nearest["coord"]
            result["repair_type"] = "substation_snap_primary"
            result["snap_decision_reason"] = "primary_tier_within_150m"
            return result

        if d1 > extended_tolerance_m:
            return result

        if second is None:
            result["repair_type"] = "substation_snap_secondary_rejected_no_second_nearest"
            result["snap_decision_reason"] = "secondary_tier_requires_second_nearest"
            return result

        active_margin_m = second_nearest_margin_m
        active_ratio_max = second_nearest_ratio_max
        secondary_guard_tier = "inner"
        if secondary_outer_guard_enabled and d1 > secondary_outer_start_m:
            active_margin_m = secondary_outer_margin_m
            active_ratio_max = secondary_outer_ratio_max
            secondary_guard_tier = "outer"

        margin_ok = (d2 - d1) >= active_margin_m
        ratio_ok = (d1 / d2) <= active_ratio_max if d2 > 0 else False

        if margin_ok and ratio_ok:
            result["repaired_coord"] = nearest["coord"]
            result["repair_type"] = "substation_snap_secondary"
            result["snap_decision_reason"] = f"secondary_{secondary_guard_tier}_tier_guard_passed"
            return result

        reject_reasons = []
        if not margin_ok:
            reject_reasons.append(f"secondary_{secondary_guard_tier}_margin_guard_failed")
        if not ratio_ok:
            reject_reasons.append(f"secondary_{secondary_guard_tier}_ratio_guard_failed")
        result["repair_type"] = "substation_snap_secondary_rejected"
        result["snap_decision_reason"] = ";".join(reject_reasons) or "secondary_guard_failed"
        return result

    def _build_endpoint_audit_row(
        *,
        line_row_idx: int,
        line_part_index: int,
        endpoint_type: str,
        original_pt: tuple[float, float],
        repaired_pt: tuple[float, float],
        snap_result: dict,
    ) -> dict:
        """Build one endpoint-level audit record from the snap evaluation output."""
        second_nearest_dist = snap_result["second_nearest_distance_m"]
        return {
            "line_row_index": line_row_idx,
            "line_part_index": line_part_index,
            "endpoint_type": endpoint_type,
            "original_x": float(original_pt[0]),
            "original_y": float(original_pt[1]),
            "repaired_x": float(repaired_pt[0]),
            "repaired_y": float(repaired_pt[1]),
            "repair_type": snap_result["repair_type"],
            "cluster_id": None,
            "nearest_substation_id": snap_result["nearest_substation_id"],
            "nearest_substation_name": snap_result["nearest_substation_name"],
            "nearest_distance_m": float(snap_result["nearest_distance_m"]),
            "second_nearest_substation_id": snap_result["second_nearest_substation_id"],
            "second_nearest_distance_m": (
                float(second_nearest_dist) if np.isfinite(second_nearest_dist) else np.nan
            ),
            "line_junction_protected": bool(
                snap_result.get("line_junction_protected", False)
            ),
            "line_junction_peer_count": int(
                snap_result.get("line_junction_peer_count", 0) or 0
            ),
            "snap_decision_reason": snap_result["snap_decision_reason"],
        }

    def _guard_same_station_snap(
        *,
        start_pt: tuple[float, float],
        end_pt: tuple[float, float],
        start_result: dict,
        end_result: dict,
        segment_length_m: float,
    ) -> tuple[dict, dict]:
        """
        Prevent short segments from being collapsed by snapping both endpoints
        onto the same substation.
        """
        if segment_length_m > DOUBLE_SNAP_MAX_LENGTH_M:
            return start_result, end_result
        if start_result["repair_type"] not in ACCEPTED_SUBSTATION_SNAP_TYPES:
            return start_result, end_result
        if end_result["repair_type"] not in ACCEPTED_SUBSTATION_SNAP_TYPES:
            return start_result, end_result
        if start_result["nearest_substation_id"] != end_result["nearest_substation_id"]:
            return start_result, end_result

        start_result = start_result.copy()
        end_result = end_result.copy()
        start_dist = float(start_result["nearest_distance_m"])
        end_dist = float(end_result["nearest_distance_m"])
        if start_dist <= end_dist:
            suppressed_result = end_result
            suppressed_original_pt = end_pt
        else:
            suppressed_result = start_result
            suppressed_original_pt = start_pt

        suppressed_result["repaired_coord"] = tuple(float(v) for v in suppressed_original_pt)
        suppressed_result["repair_type"] = "none"
        suppressed_result["snap_decision_reason"] = DOUBLE_SNAP_SUPPRESS_REASON
        return start_result, end_result

    new_geometries = []
    endpoint_audit_rows = []
    primary_snap_count = 0
    secondary_snap_count = 0
    secondary_reject_count = 0
    secondary_no_second_count = 0
    line_junction_protected_count = 0

    # Process geometry only; preserve other columns by copying the GeoDataFrame at the end.
    for line_row_idx, geom in enumerate(lines_gdf.geometry):
        if geom is None or geom.is_empty:
            new_geometries.append(geom)
            continue

        # Handle MultiLineString by processing each part independently.
        parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
        modified_parts = []

        for part_idx, part in enumerate(parts):
            coords = list(part.coords)
            if len(coords) < 2:
                modified_parts.append(part)
                continue

            start_pt = tuple(coords[0])
            end_pt = tuple(coords[-1])

            start_result = _evaluate_snap(
                start_pt,
                line_junction_peer_count=endpoint_junction_peer_counts.get(
                    (int(line_row_idx), int(part_idx), "start"),
                    0,
                ),
            )
            end_result = _evaluate_snap(
                end_pt,
                line_junction_peer_count=endpoint_junction_peer_counts.get(
                    (int(line_row_idx), int(part_idx), "end"),
                    0,
                ),
            )
            segment_length_m = float(part.length)
            start_result, end_result = _guard_same_station_snap(
                start_pt=start_pt,
                end_pt=end_pt,
                start_result=start_result,
                end_result=end_result,
                segment_length_m=segment_length_m,
            )

            start_repaired = start_result["repaired_coord"]
            start_repair_type = start_result["repair_type"]
            if start_repair_type in ACCEPTED_SUBSTATION_SNAP_TYPES:
                coords[0] = start_repaired
                if start_repair_type == "substation_snap_primary":
                    primary_snap_count += 1
                else:
                    secondary_snap_count += 1
            elif start_repair_type == "substation_snap_secondary_rejected":
                secondary_reject_count += 1
            elif start_repair_type == "substation_snap_secondary_rejected_no_second_nearest":
                secondary_no_second_count += 1
            elif start_result["snap_decision_reason"] == LINE_JUNCTION_PROTECT_REASON:
                line_junction_protected_count += 1

            end_repaired = end_result["repaired_coord"]
            end_repair_type = end_result["repair_type"]
            if end_repair_type in ACCEPTED_SUBSTATION_SNAP_TYPES:
                coords[-1] = end_repaired
                if end_repair_type == "substation_snap_primary":
                    primary_snap_count += 1
                else:
                    secondary_snap_count += 1
            elif end_repair_type == "substation_snap_secondary_rejected":
                secondary_reject_count += 1
            elif end_repair_type == "substation_snap_secondary_rejected_no_second_nearest":
                secondary_no_second_count += 1
            elif end_result["snap_decision_reason"] == LINE_JUNCTION_PROTECT_REASON:
                line_junction_protected_count += 1

            modified_parts.append(LineString(coords))

            endpoint_audit_rows.extend(
                [
                    _build_endpoint_audit_row(
                        line_row_idx=line_row_idx,
                        line_part_index=part_idx,
                        endpoint_type="start",
                        original_pt=start_pt,
                        repaired_pt=start_repaired,
                        snap_result=start_result,
                    ),
                    _build_endpoint_audit_row(
                        line_row_idx=line_row_idx,
                        line_part_index=part_idx,
                        endpoint_type="end",
                        original_pt=end_pt,
                        repaired_pt=end_repaired,
                        snap_result=end_result,
                    ),
                ]
            )

        if len(modified_parts) == 1:
            new_geometries.append(modified_parts[0])
        else:
            new_geometries.append(MultiLineString(modified_parts))

    logging.info(
        (
            "Endpoint snap summary: primary=%s, secondary=%s, secondary_rejected=%s, "
            "secondary_rejected_no_second=%s, line_junction_protected=%s, total_accepted=%s"
        ),
        primary_snap_count,
        secondary_snap_count,
        secondary_reject_count,
        secondary_no_second_count,
        line_junction_protected_count,
        primary_snap_count + secondary_snap_count,
    )

    out = lines_gdf.copy()
    out["geometry"] = new_geometries
    if return_endpoint_audit:
        return out, pd.DataFrame(endpoint_audit_rows)
    return out


def snap_protected_junction_clusters_to_substations(
    lines_gdf: gpd.GeoDataFrame,
    subs_gdf: gpd.GeoDataFrame,
    endpoint_audit_df: Optional[pd.DataFrame],
    strict_tolerance_m: float,
    extended_tolerance_m: Optional[float] = None,
    second_nearest_margin_m: Optional[float] = None,
    second_nearest_ratio_max: Optional[float] = None,
    secondary_outer_start_m: Optional[float] = None,
    secondary_outer_margin_m: Optional[float] = None,
    secondary_outer_ratio_max: Optional[float] = None,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Move whole existing line-junction clusters onto nearby compatible substations.

    Endpoint snapping deliberately protects endpoints that already share an exact
    transmission-line vertex, because moving just one endpoint would tear apart
    an existing line-line junction. This repair handles the safe counterpart:
    when the whole shared junction passes the same primary/secondary substation
    snap guards as a normal endpoint and every line in that cluster is
    voltage-compatible with the substation, move every vertex occurrence in the
    cluster together. That preserves the original line-line connectivity while
    registering the junction at the substation point.
    """
    logger = logging.getLogger()
    strict_tolerance_m = float(strict_tolerance_m)
    extended_tolerance_m = (
        max(float(extended_tolerance_m), strict_tolerance_m)
        if extended_tolerance_m is not None
        else strict_tolerance_m
    )
    if second_nearest_margin_m is None:
        raise ValueError("second_nearest_margin_m must be provided explicitly.")
    if second_nearest_ratio_max is None:
        raise ValueError("second_nearest_ratio_max must be provided explicitly.")
    second_nearest_margin_m = float(second_nearest_margin_m)
    second_nearest_ratio_max = float(second_nearest_ratio_max)
    secondary_outer_start_m = (
        float(secondary_outer_start_m)
        if secondary_outer_start_m is not None
        else None
    )
    secondary_outer_margin_m = (
        float(secondary_outer_margin_m)
        if secondary_outer_margin_m is not None
        else second_nearest_margin_m
    )
    secondary_outer_ratio_max = (
        float(secondary_outer_ratio_max)
        if secondary_outer_ratio_max is not None
        else second_nearest_ratio_max
    )
    secondary_outer_guard_enabled = (
        secondary_outer_start_m is not None
        and extended_tolerance_m > secondary_outer_start_m
    )
    if lines_gdf.empty or subs_gdf.empty or endpoint_audit_df is None or endpoint_audit_df.empty:
        return lines_gdf, endpoint_audit_df if endpoint_audit_df is not None else pd.DataFrame()

    audit_df = endpoint_audit_df.copy()
    required_cols = {
        "line_junction_protected",
        "nearest_substation_id",
        "nearest_distance_m",
        "original_x",
        "original_y",
    }
    if not required_cols.issubset(audit_df.columns):
        logger.info("Protected junction cluster snap skipped: endpoint audit lacks required columns.")
        return lines_gdf, audit_df

    kv_col = _detect_voltage_column(lines_gdf)
    sub_rows_by_id = {
        str(row["id"]).strip(): row
        for _, row in subs_gdf.iterrows()
        if "id" in row.index and pd.notna(row["id"])
    }
    sub_coords_by_id = {
        sid: (float(row.geometry.x), float(row.geometry.y))
        for sid, row in sub_rows_by_id.items()
        if row.geometry is not None and not row.geometry.is_empty
    }

    vertex_registry: dict[tuple, list[tuple[int, int, int]]] = {}
    for line_row_idx, (_, row) in enumerate(lines_gdf.iterrows()):
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
        for part_idx, part in enumerate(parts):
            coords = list(part.coords)
            for coord_idx, coord in enumerate(coords):
                node_key = _graph_node_key(coord)
                vertex_registry.setdefault(node_key, []).append(
                    (int(line_row_idx), int(part_idx), int(coord_idx))
                )

    def _evaluate_regular_snap_guard(d1: float, d2: float) -> tuple[Optional[str], str]:
        if d1 <= strict_tolerance_m:
            return "primary", "protected_junction_cluster_snap_primary_guard_passed"

        if d1 > extended_tolerance_m:
            return None, "outside_secondary_tolerance"

        if not np.isfinite(d2):
            return None, "secondary_tier_requires_second_nearest"

        active_margin_m = second_nearest_margin_m
        active_ratio_max = second_nearest_ratio_max
        secondary_guard_tier = "inner"
        if secondary_outer_guard_enabled and d1 > secondary_outer_start_m:
            active_margin_m = secondary_outer_margin_m
            active_ratio_max = secondary_outer_ratio_max
            secondary_guard_tier = "outer"

        margin_ok = (d2 - d1) >= active_margin_m
        ratio_ok = (d1 / d2) <= active_ratio_max if d2 > 0 else False
        if margin_ok and ratio_ok:
            return (
                "secondary",
                f"protected_junction_cluster_snap_secondary_{secondary_guard_tier}_guard_passed",
            )

        reject_reasons = []
        if not margin_ok:
            reject_reasons.append(f"secondary_{secondary_guard_tier}_margin_guard_failed")
        if not ratio_ok:
            reject_reasons.append(f"secondary_{secondary_guard_tier}_ratio_guard_failed")
        return None, ";".join(reject_reasons) or "secondary_guard_failed"

    candidate_groups: dict[tuple[tuple, str], dict] = {}
    snap_guard_block_count = 0
    outside_secondary_count = 0
    for _, row in audit_df.iterrows():
        protected = bool(row.get("line_junction_protected", False)) or (
            row.get("snap_decision_reason") == LINE_JUNCTION_PROTECT_REASON
        )
        if not protected:
            continue

        try:
            nearest_distance_m = float(row["nearest_distance_m"])
        except Exception:
            continue
        try:
            second_nearest_distance_m = float(row.get("second_nearest_distance_m", np.nan))
        except Exception:
            second_nearest_distance_m = np.nan

        if not np.isfinite(nearest_distance_m):
            continue
        snap_tier, snap_reason = _evaluate_regular_snap_guard(
            nearest_distance_m,
            second_nearest_distance_m,
        )
        if snap_tier is None:
            if snap_reason == "outside_secondary_tolerance":
                outside_secondary_count += 1
            else:
                snap_guard_block_count += 1
            continue

        sid = str(row.get("nearest_substation_id", "")).strip()
        if not sid or sid not in sub_coords_by_id:
            continue

        try:
            node_key = _graph_node_key((row["original_x"], row["original_y"]))
        except Exception:
            continue

        key = (node_key, sid)
        existing = candidate_groups.get(key)
        if existing is None or nearest_distance_m < existing["nearest_distance_m"]:
            candidate_groups[key] = {
                "node_key": node_key,
                "sid": sid,
                "nearest_distance_m": nearest_distance_m,
                "second_nearest_distance_m": second_nearest_distance_m,
                "snap_tier": snap_tier,
                "snap_reason": snap_reason,
            }

    if not candidate_groups:
        logger.info(
            (
                "Protected junction cluster snap: no candidates passed regular snap guards "
                "(primary=%.1fm, secondary=%.1fm, guard_blocked=%s, outside_secondary=%s)."
            ),
            strict_tolerance_m,
            extended_tolerance_m,
            snap_guard_block_count,
            outside_secondary_count,
        )
        return lines_gdf, audit_df

    replacements_by_node_key: dict[tuple, tuple[float, float]] = {}
    cluster_ids_by_node_key: dict[tuple, str] = {}
    snap_reasons_by_node_key: dict[tuple, str] = {}
    accepted_substations: set[str] = set()
    moved_vertex_count = 0
    compatibility_block_count = 0
    missing_cluster_count = 0

    for _, candidate in sorted(
        candidate_groups.items(),
        key=lambda item: (item[1]["nearest_distance_m"], item[1]["sid"], item[1]["node_key"]),
    ):
        node_key = candidate["node_key"]
        sid = candidate["sid"]
        if node_key in replacements_by_node_key:
            continue

        occurrences = vertex_registry.get(node_key, [])
        if not occurrences:
            missing_cluster_count += 1
            continue

        substation_row = sub_rows_by_id.get(sid)
        row_indices = sorted({line_row_idx for line_row_idx, _, _ in occurrences})
        compatible = True
        for line_row_idx in row_indices:
            if line_row_idx < 0 or line_row_idx >= len(lines_gdf):
                compatible = False
                break
            line_row = lines_gdf.iloc[line_row_idx]
            line_family = _line_voltage_family(line_row, kv_col)
            owner_group = _topology_owner_group(_normalized_line_owner(line_row), line_family)
            voltage_ok, _ = _split_candidate_compatible_with_substation_voltage(
                line_row,
                kv_col,
                substation_row,
            )
            if not voltage_ok or not owner_group:
                compatible = False
                break

        if not compatible:
            compatibility_block_count += 1
            continue

        replacements_by_node_key[node_key] = sub_coords_by_id[sid]
        cluster_ids_by_node_key[node_key] = f"protected_junction_snap_{len(replacements_by_node_key) - 1}"
        snap_reasons_by_node_key[node_key] = str(candidate["snap_reason"])
        accepted_substations.add(sid)
        moved_vertex_count += len(occurrences)

    if not replacements_by_node_key:
        logger.info(
            (
                "Protected junction cluster snap complete: clusters=0, moved_vertices=0, "
                "compatibility_blocked=%s, snap_guard_blocked=%s, outside_secondary=%s, "
                "missing_clusters=%s, primary=%.1fm, secondary=%.1fm"
            ),
            compatibility_block_count,
            snap_guard_block_count,
            outside_secondary_count,
            missing_cluster_count,
            strict_tolerance_m,
            extended_tolerance_m,
        )
        return lines_gdf, audit_df

    new_geometries = []
    for _, geom in enumerate(lines_gdf.geometry):
        if geom is None or geom.is_empty:
            new_geometries.append(geom)
            continue

        parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
        modified_parts = []
        for part in parts:
            coords = []
            for coord in part.coords:
                node_key = _graph_node_key(coord)
                replacement = replacements_by_node_key.get(node_key)
                coords.append(replacement if replacement is not None else tuple(coord))
            modified_parts.append(LineString(coords))

        if len(modified_parts) == 1:
            new_geometries.append(modified_parts[0])
        else:
            new_geometries.append(MultiLineString(modified_parts))

    for idx, row in audit_df.iterrows():
        protected = bool(row.get("line_junction_protected", False)) or (
            row.get("snap_decision_reason") == LINE_JUNCTION_PROTECT_REASON
        )
        if not protected:
            continue
        try:
            node_key = _graph_node_key((row["original_x"], row["original_y"]))
        except Exception:
            continue
        replacement = replacements_by_node_key.get(node_key)
        if replacement is None:
            continue
        audit_df.at[idx, "repaired_x"] = float(replacement[0])
        audit_df.at[idx, "repaired_y"] = float(replacement[1])
        audit_df.at[idx, "repair_type"] = "protected_junction_cluster_snap"
        audit_df.at[idx, "cluster_id"] = cluster_ids_by_node_key[node_key]
        audit_df.at[idx, "snap_decision_reason"] = snap_reasons_by_node_key[node_key]

    out = lines_gdf.copy()
    out["geometry"] = new_geometries
    logger.info(
        (
            "Protected junction cluster snap complete: clusters=%s, substations=%s, "
            "moved_vertices=%s, compatibility_blocked=%s, snap_guard_blocked=%s, "
            "outside_secondary=%s, missing_clusters=%s, primary=%.1fm, secondary=%.1fm"
        ),
        len(replacements_by_node_key),
        len(accepted_substations),
        moved_vertex_count,
        compatibility_block_count,
        snap_guard_block_count,
        outside_secondary_count,
        missing_cluster_count,
        strict_tolerance_m,
        extended_tolerance_m,
    )
    return out, audit_df


def merge_nearby_line_endpoints(
    lines_gdf: gpd.GeoDataFrame,
    tolerance_m: float,
    protected_points_gdf: Optional[gpd.GeoDataFrame] = None,
    protected_tol_m: Optional[float] = None,
    bbox_geom=None,
    bbox_edge_buffer_m: Optional[float] = None,
    endpoint_audit_df: Optional[pd.DataFrame] = None,
):
    """
    Merge nearby line endpoints to each other as a conservative fallback repair.

    Rationale:
      - Substation snapping is the authoritative anchor step.
      - Endpoint merging is only a fallback for missing/out-of-scope junctions.
      - Only true line endpoints are modified; no endpoint is ever snapped to the
        interior of another line.
    """
    logger = logging.getLogger()
    logger.info(
        "Merging nearby line endpoints (tolerance=%sm, exclude_bbox_edge=%s)...",
        tolerance_m,
        bbox_edge_buffer_m is not None and bbox_geom is not None,
    )

    lines_single = lines_gdf.explode(index_parts=False).reset_index(drop=True).copy()
    if lines_single.empty:
        if endpoint_audit_df is None:
            endpoint_audit_df = pd.DataFrame(
                columns=[
                    "line_row_index",
                    "endpoint_type",
                    "original_x",
                    "original_y",
                    "repaired_x",
                    "repaired_y",
                    "repair_type",
                    "cluster_id",
                    "nearest_substation_id",
                    "nearest_substation_name",
                    "nearest_distance_m",
                    "second_nearest_substation_id",
                    "second_nearest_distance_m",
                    "line_junction_protected",
                    "line_junction_peer_count",
                    "snap_decision_reason",
                ]
            )
        return lines_single, endpoint_audit_df

    if endpoint_audit_df is None or endpoint_audit_df.empty:
        audit_rows = []
        for line_row_idx, geom in enumerate(lines_single.geometry):
            if geom is None or geom.is_empty:
                continue
            coords = list(geom.coords)
            if len(coords) < 2:
                continue
            audit_rows.extend(
                [
                    {
                        "line_row_index": line_row_idx,
                        "endpoint_type": "start",
                        "original_x": float(coords[0][0]),
                        "original_y": float(coords[0][1]),
                        "repaired_x": float(coords[0][0]),
                        "repaired_y": float(coords[0][1]),
                        "repair_type": "none",
                        "cluster_id": None,
                        "nearest_substation_id": None,
                        "nearest_substation_name": None,
                        "nearest_distance_m": np.nan,
                        "second_nearest_substation_id": None,
                        "second_nearest_distance_m": np.nan,
                        "line_junction_protected": False,
                        "line_junction_peer_count": 0,
                        "snap_decision_reason": "no_initial_snap_audit",
                    },
                    {
                        "line_row_index": line_row_idx,
                        "endpoint_type": "end",
                        "original_x": float(coords[-1][0]),
                        "original_y": float(coords[-1][1]),
                        "repaired_x": float(coords[-1][0]),
                        "repaired_y": float(coords[-1][1]),
                        "repair_type": "none",
                        "cluster_id": None,
                        "nearest_substation_id": None,
                        "nearest_substation_name": None,
                        "nearest_distance_m": np.nan,
                        "second_nearest_substation_id": None,
                        "second_nearest_distance_m": np.nan,
                        "line_junction_protected": False,
                        "line_junction_peer_count": 0,
                        "snap_decision_reason": "no_initial_snap_audit",
                    },
                ]
            )
        endpoint_audit_df = pd.DataFrame(audit_rows)
    else:
        endpoint_audit_df = endpoint_audit_df.copy()

    if "_pre_merge_repair_type" not in endpoint_audit_df.columns:
        endpoint_audit_df["_pre_merge_repair_type"] = pd.NA
    if "_pre_merge_reason" not in endpoint_audit_df.columns:
        endpoint_audit_df["_pre_merge_reason"] = pd.NA
    if "line_junction_protected" not in endpoint_audit_df.columns:
        endpoint_audit_df["line_junction_protected"] = False
    if "line_junction_peer_count" not in endpoint_audit_df.columns:
        endpoint_audit_df["line_junction_peer_count"] = 0

    protected_junction_endpoint_keys = {
        (int(row["line_row_index"]), str(row["endpoint_type"]))
        for _, row in endpoint_audit_df.iterrows()
        if bool(row.get("line_junction_protected", False))
        or row.get("snap_decision_reason") == LINE_JUNCTION_PROTECT_REASON
    }

    protected_tree = None
    protected_coords = np.empty((0, 2), dtype=float)
    effective_protected_tol = protected_tol_m if protected_tol_m is not None else tolerance_m
    if (
        protected_points_gdf is not None
        and not protected_points_gdf.empty
        and effective_protected_tol is not None
    ):
        protected_coords = np.array(
            [(geom.x, geom.y) for geom in protected_points_gdf.geometry if geom is not None and not geom.is_empty],
            dtype=float,
        )
        if len(protected_coords):
            protected_tree = cKDTree(protected_coords)

    bbox_boundary = bbox_geom.boundary if bbox_geom is not None else None
    endpoint_rows = []
    for line_row_idx, geom in enumerate(lines_single.geometry):
        if geom is None or geom.is_empty:
            continue
        coords = list(geom.coords)
        if len(coords) < 2:
            continue
        endpoint_rows.append(
            {
                "line_row_index": line_row_idx,
                "endpoint_type": "start",
                "coord": tuple(coords[0]),
                "line_junction_protected": (
                    (line_row_idx, "start") in protected_junction_endpoint_keys
                ),
            }
        )
        endpoint_rows.append(
            {
                "line_row_index": line_row_idx,
                "endpoint_type": "end",
                "coord": tuple(coords[-1]),
                "line_junction_protected": (
                    (line_row_idx, "end") in protected_junction_endpoint_keys
                ),
            }
        )

    if not endpoint_rows:
        return lines_single, endpoint_audit_df

    endpoint_coords = np.array([row["coord"] for row in endpoint_rows], dtype=float)
    merge_candidate_mask = np.ones(len(endpoint_rows), dtype=bool)

    for idx, row in enumerate(endpoint_rows):
        coord = row["coord"]
        protected_anchor = None
        if protected_tree is not None and len(protected_coords):
            d_protected, idx_protected = protected_tree.query(coord)
            if d_protected <= effective_protected_tol:
                protected_anchor = tuple(float(v) for v in protected_coords[idx_protected])
        row["protected_anchor"] = protected_anchor

        near_bbox_edge = False
        if bbox_boundary is not None and bbox_edge_buffer_m is not None:
            near_bbox_edge = Point(coord).distance(bbox_boundary) <= bbox_edge_buffer_m
        if near_bbox_edge:
            merge_candidate_mask[idx] = False
        if row.get("line_junction_protected", False):
            merge_candidate_mask[idx] = False

    candidate_indices = np.where(merge_candidate_mask)[0]
    if len(candidate_indices) == 0:
        logger.info("No eligible line endpoints for endpoint-to-endpoint merge repair.")
        return lines_single, endpoint_audit_df

    candidate_coords = endpoint_coords[candidate_indices]
    endpoint_tree = cKDTree(candidate_coords)
    close_pairs = list(endpoint_tree.query_pairs(tolerance_m))

    if not close_pairs:
        logger.info("No endpoint clusters found within %sm.", tolerance_m)
        return lines_single, endpoint_audit_df

    parent = list(range(len(candidate_indices)))

    def _find(i):
        """Return the union-find representative for one candidate endpoint."""
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def _union(i, j):
        """Merge two union-find endpoint sets using a stable representative rule."""
        ri, rj = _find(i), _find(j)
        if ri != rj:
            if ri < rj:
                parent[rj] = ri
            else:
                parent[ri] = rj

    for i, j in close_pairs:
        _union(i, j)

    clusters = {}
    for local_idx, global_idx in enumerate(candidate_indices):
        clusters.setdefault(_find(local_idx), []).append(global_idx)

    endpoint_replacements = {}
    merge_cluster_count = 0
    merged_endpoint_count = 0

    for cluster_members in sorted(
        clusters.values(),
        key=lambda members: (
            min(endpoint_rows[idx]["line_row_index"] for idx in members),
            min(endpoint_rows[idx]["endpoint_type"] for idx in members),
        ),
    ):
        if len(cluster_members) <= 1:
            continue

        protected_anchors = sorted(
            {
                (
                    round(endpoint_rows[idx]["protected_anchor"][0], 6),
                    round(endpoint_rows[idx]["protected_anchor"][1], 6),
                )
                for idx in cluster_members
                if endpoint_rows[idx]["protected_anchor"] is not None
            }
        )

        if len(protected_anchors) > 1:
            logger.info(
                "Skipping endpoint merge cluster with multiple protected anchors (size=%s).",
                len(cluster_members),
            )
            continue

        if len(protected_anchors) == 1:
            representative = tuple(float(v) for v in protected_anchors[0])
        else:
            cluster_coords = endpoint_coords[cluster_members]
            representative = (
                float(cluster_coords[:, 0].mean()),
                float(cluster_coords[:, 1].mean()),
            )

        cluster_id = f"merge_{merge_cluster_count}"
        merge_cluster_count += 1

        for endpoint_idx in cluster_members:
            row = endpoint_rows[endpoint_idx]
            original_coord = tuple(float(v) for v in row["coord"])
            endpoint_replacements[(row["line_row_index"], row["endpoint_type"])] = representative
            audit_mask = (
                (endpoint_audit_df["line_row_index"] == row["line_row_index"])
                & (endpoint_audit_df["endpoint_type"] == row["endpoint_type"])
            )
            if audit_mask.any():
                endpoint_audit_df.loc[audit_mask, "cluster_id"] = cluster_id
                endpoint_audit_df.loc[audit_mask, "repaired_x"] = representative[0]
                endpoint_audit_df.loc[audit_mask, "repaired_y"] = representative[1]

                current_repair_type = endpoint_audit_df.loc[audit_mask, "repair_type"].iloc[0]
                if current_repair_type not in ACCEPTED_SUBSTATION_SNAP_TYPES and (
                    abs(original_coord[0] - representative[0]) > 1e-6
                    or abs(original_coord[1] - representative[1]) > 1e-6
                ):
                    endpoint_audit_df.loc[audit_mask, "_pre_merge_repair_type"] = current_repair_type
                    endpoint_audit_df.loc[audit_mask, "_pre_merge_reason"] = endpoint_audit_df.loc[
                        audit_mask, "snap_decision_reason"
                    ].iloc[0]
                    endpoint_audit_df.loc[audit_mask, "repair_type"] = "endpoint_merge"
                    endpoint_audit_df.loc[audit_mask, "snap_decision_reason"] = "merged_nearby_endpoints"

            if (
                abs(original_coord[0] - representative[0]) > 1e-6
                or abs(original_coord[1] - representative[1]) > 1e-6
            ):
                merged_endpoint_count += 1

    repaired_geometries = []
    reverted_lines = 0
    for line_row_idx, geom in enumerate(lines_single.geometry):
        if geom is None or geom.is_empty:
            repaired_geometries.append(geom)
            continue

        coords = list(geom.coords)
        if len(coords) < 2:
            repaired_geometries.append(geom)
            continue

        original_coords = list(coords)
        start_key = (line_row_idx, "start")
        end_key = (line_row_idx, "end")
        if start_key in endpoint_replacements:
            coords[0] = endpoint_replacements[start_key]
        if end_key in endpoint_replacements:
            coords[-1] = endpoint_replacements[end_key]

        try:
            repaired_geom = LineString(coords)
            if repaired_geom.is_empty or repaired_geom.length <= 0.1:
                raise ValueError("Degenerate merged line.")
            repaired_geometries.append(repaired_geom)
        except Exception:
            repaired_geometries.append(LineString(original_coords))
            reverted_lines += 1
            for endpoint_type in ("start", "end"):
                audit_mask = (
                    (endpoint_audit_df["line_row_index"] == line_row_idx)
                    & (endpoint_audit_df["endpoint_type"] == endpoint_type)
                )
                if not audit_mask.any():
                    continue
                original_endpoint = original_coords[0] if endpoint_type == "start" else original_coords[-1]
                endpoint_audit_df.loc[audit_mask, "repaired_x"] = float(original_endpoint[0])
                endpoint_audit_df.loc[audit_mask, "repaired_y"] = float(original_endpoint[1])
                endpoint_audit_df.loc[audit_mask, "cluster_id"] = None
                if endpoint_audit_df.loc[audit_mask, "repair_type"].iloc[0] == "endpoint_merge":
                    prev_type = endpoint_audit_df.loc[audit_mask, "_pre_merge_repair_type"].iloc[0]
                    prev_reason = endpoint_audit_df.loc[audit_mask, "_pre_merge_reason"].iloc[0]
                    endpoint_audit_df.loc[audit_mask, "repair_type"] = (
                        prev_type if pd.notna(prev_type) else "none"
                    )
                    endpoint_audit_df.loc[audit_mask, "snap_decision_reason"] = (
                        prev_reason if pd.notna(prev_reason) else "merge_reverted"
                    )

    out = lines_single.copy()
    out["geometry"] = repaired_geometries
    endpoint_audit_df = endpoint_audit_df.drop(
        columns=["_pre_merge_repair_type", "_pre_merge_reason"],
        errors="ignore",
    )
    logger.info(
        "Endpoint merge repair complete: clusters=%s, moved_endpoints=%s, reverted_lines=%s",
        merge_cluster_count,
        merged_endpoint_count,
        reverted_lines,
    )
    return out, endpoint_audit_df


def _split_line_by_distances(
    line_geom: LineString,
    cut_distances: list[float],
    min_segment_length_m: float,
) -> list[LineString]:
    """Split a LineString at along-line distances without moving the geometry."""
    if line_geom is None or line_geom.is_empty:
        return []

    line_length = float(line_geom.length)
    if line_length <= 0:
        return []

    min_segment_length_m = max(float(min_segment_length_m), 0.0)
    kept_distances: list[float] = []
    for distance in sorted(float(d) for d in cut_distances if np.isfinite(d)):
        if distance <= min_segment_length_m or distance >= line_length - min_segment_length_m:
            continue
        if kept_distances and distance - kept_distances[-1] < min_segment_length_m:
            continue
        kept_distances.append(distance)

    if not kept_distances:
        return [line_geom]

    pieces = []
    stops = [0.0, *kept_distances, line_length]
    for start_dist, end_dist in zip(stops, stops[1:]):
        if end_dist - start_dist < min_segment_length_m:
            continue
        segment = substring(line_geom, start_dist, end_dist)
        if segment is None or segment.is_empty:
            continue
        if isinstance(segment, LineString) and segment.length > 0:
            pieces.append(segment)

    return pieces or [line_geom]


def _apply_transmission_line_attribute_overrides(lines_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Apply targeted source-data corrections before topology construction."""
    if lines_gdf is None or lines_gdf.empty:
        return lines_gdf

    gid_col = next((c for c in ("GlobalID", "GLOBALID", "globalid") if c in lines_gdf.columns), None)
    if gid_col is None:
        return lines_gdf

    out = lines_gdf.copy()
    gids = out[gid_col].astype(str).str.strip().str.lower()
    override_count = 0
    for gid, attrs in TRANSMISSION_LINE_ATTRIBUTE_OVERRIDES.items():
        mask = gids == gid.lower()
        if not mask.any():
            continue
        override_count += int(mask.sum())
        for col, value in attrs.items():
            if col in out.columns:
                if pd.api.types.is_numeric_dtype(out[col]):
                    assign_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
                else:
                    assign_value = str(value)
                out.loc[mask, col] = assign_value

    if override_count:
        logging.info(
            "Applied targeted transmission-line attribute overrides to %s row(s).",
            override_count,
        )
    return out


def _normalized_line_owner(row) -> str:
    """Return a stable owner string for conservative line compatibility checks."""
    if row is None:
        return ""
    for col in ("Owner", "OWNER", "owner"):
        if hasattr(row, "index") and col in row.index and pd.notna(row[col]):
            return str(row[col]).strip().upper()
    return ""


def _voltage_family(value) -> str:
    """Group nominally equivalent voltage labels for topology compatibility."""
    try:
        voltage = float(value)
    except Exception:
        text = str(value).strip()
        return text.upper() if text else ""

    if not np.isfinite(voltage):
        return ""
    if 60.0 <= voltage <= 70.0:
        return "66_69"
    if 130.0 <= voltage <= 145.0:
        return "138"
    if 200.0 <= voltage <= 240.0:
        return "220_230"
    return f"{voltage:g}"


def _line_voltage_family(row, kv_col) -> str:
    if row is None or not kv_col or not hasattr(row, "index") or kv_col not in row.index:
        return ""
    return _voltage_family(row[kv_col])


def _substation_voltage_families(row) -> set[str]:
    """Return reliable voltage families listed on a substation row."""
    if row is None or not hasattr(row, "index"):
        return set()

    families: set[str] = set()
    unknown_values = {"", "NAN", "NONE", "-999999", "-999999.0", "0", "0.0"}
    for col in ("MAX_VOLT_N", "MIN_VOLT_N", "MAX_VOLT", "MIN_VOLT", "voltage_for_fragility"):
        if col not in row.index or pd.isna(row[col]):
            continue
        text = str(row[col]).strip().upper()
        if text in unknown_values:
            continue
        family = _voltage_family(row[col])
        if family and family not in unknown_values:
            families.add(family)
    return families


def _split_candidate_compatible_with_substation_voltage(
    line_row,
    kv_col: Optional[str],
    substation_row,
) -> tuple[bool, str]:
    """
    Require through-line split voltage to match reliable substation voltage metadata.

    Unknown line/substation voltage metadata stays permissive; this guard is only
    meant to block clear mismatches such as a 66kV-only sub splitting a 220kV line.
    """
    line_family = _line_voltage_family(line_row, kv_col)
    substation_families = _substation_voltage_families(substation_row)

    if not line_family:
        return True, "unknown_line_voltage"
    if not substation_families:
        return True, "unknown_substation_voltage"
    if line_family in substation_families:
        return True, "sub_voltage_family_match"

    allowed = ",".join(sorted(substation_families))
    return False, f"blocked_sub_voltage_family_mismatch:{line_family}_not_in_{allowed}"


def _topology_owner_group(owner: str, voltage_family: str) -> str:
    """Return the owner grouping used only for physical topology joins."""
    owner = str(owner or "").strip().upper()
    if voltage_family == "66_69" and owner in {"SCE", "VENON", "VERNON"}:
        return "SCE_VENON_66"
    return owner


def _build_endpoint_snap_compatibility_by_substation(
    lines_gdf: gpd.GeoDataFrame,
    endpoint_audit_df: Optional[pd.DataFrame],
    kv_col: Optional[str],
) -> dict[str, list[dict]]:
    """
    Collect line attributes from accepted endpoint snaps.

    These attributes are later used as conservative evidence for whether a
    substation should be allowed to receive additional through-line split
    connectors. Distance alone is not enough for already endpoint-connected
    substations.
    """
    if endpoint_audit_df is None or endpoint_audit_df.empty:
        return {}

    required = {"repair_type", "nearest_substation_id", "line_row_index"}
    if not required.issubset(endpoint_audit_df.columns):
        return {}

    accepted = endpoint_audit_df[
        endpoint_audit_df["repair_type"].isin(ACCEPTED_SUBSTATION_SNAP_TYPES)
    ]
    if accepted.empty:
        return {}

    compatibility: dict[str, list[dict]] = {}
    for _, audit_row in accepted.iterrows():
        sid = audit_row.get("nearest_substation_id")
        if sid is None or pd.isna(sid):
            continue
        try:
            line_idx = int(audit_row["line_row_index"])
        except Exception:
            continue
        if line_idx < 0 or line_idx >= len(lines_gdf):
            continue

        line_row = lines_gdf.iloc[line_idx]
        entry = {
            "owner": _normalized_line_owner(line_row),
            "voltage_family": _line_voltage_family(line_row, kv_col),
        }
        if not entry["owner"] and not entry["voltage_family"]:
            continue
        compatibility.setdefault(str(sid), []).append(entry)

    return compatibility


def _split_candidate_compatible_with_endpoint_snaps(
    line_row,
    kv_col: Optional[str],
    endpoint_evidence: Optional[list[dict]],
) -> tuple[bool, str]:
    """
    Decide whether a split/projection connector is compatible with endpoint evidence.

    If the substation has no endpoint-snap evidence, keep the existing distance
    based behavior. If it does, require the candidate line to match at least one
    snapped endpoint's owner and voltage family.
    """
    if not endpoint_evidence:
        return True, "no_endpoint_snap_evidence"

    owner = _normalized_line_owner(line_row)
    voltage_family = _line_voltage_family(line_row, kv_col)
    for evidence in endpoint_evidence:
        evidence_owner = evidence.get("owner", "")
        evidence_family = evidence.get("voltage_family", "")
        owner_ok = bool(owner and evidence_owner and owner == evidence_owner)
        family_ok = bool(
            voltage_family
            and evidence_family
            and voltage_family == evidence_family
        )
        if owner_ok and family_ok:
            return True, "endpoint_snap_owner_voltage_family_match"

    return False, "blocked_endpoint_snap_owner_voltage_family_mismatch"


def split_lines_at_nearby_substations(
    lines_gdf: gpd.GeoDataFrame,
    subs_gdf: gpd.GeoDataFrame,
    tolerance_m: float,
    min_endpoint_dist_m: float,
    min_segment_length_m: float,
    add_projection_connectors: bool = False,
    endpoint_snap_compatibility_by_substation: Optional[dict[str, list[dict]]] = None,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    """
    Split through-lines at substations that are close to the line interior.

    The cut point is the substation's orthogonal projection onto the line, not
    a broad geometry snap. This preserves the original line shape while adding
    graph nodes where a nearby substation should block a direct-link path.
    When enabled, a short projection connector also ties the substation point to
    that anchor with its true offset length.
    """
    logger = logging.getLogger()
    tolerance_m = float(tolerance_m)
    min_endpoint_dist_m = float(min_endpoint_dist_m)
    min_segment_length_m = float(min_segment_length_m)

    lines_single = lines_gdf.explode(index_parts=False).reset_index(drop=True)
    attr_cols = [c for c in lines_single.columns if c != "geometry"]
    audit_columns = [
        "line_row_index",
        "line_topology_signature",
        "substation_id",
        "substation_name",
        "distance_to_line_m",
        "distance_along_line_m",
        "line_length_m",
        "cut_x",
        "cut_y",
        "sub_x",
        "sub_y",
        "connector_added",
        "connector_length_m",
        "split_compatibility_reason",
    ]

    if lines_single.empty or subs_gdf.empty or tolerance_m <= 0:
        return lines_single, pd.DataFrame(columns=audit_columns)

    kv_col = _detect_voltage_column(lines_single)

    name_col = next((c for c in ["NAME", "name", "Name"] if c in subs_gdf.columns), None)
    points_sindex = subs_gdf.sindex
    new_rows = []
    audit_rows = []
    split_line_count = 0
    total_cut_count = 0
    projection_connector_count = 0
    compatibility_block_count = 0

    for line_idx, line_row in lines_single.iterrows():
        line_geom = line_row.geometry
        row_attrs = line_row[attr_cols].to_dict()
        line_topology_signature = _line_topology_signature(line_row, kv_col)
        line_topology_signature_text = json.dumps(line_topology_signature)
        row_attrs["_is_projection_connector"] = False
        row_attrs["_connector_substation_id"] = ""
        row_attrs["_connector_distance_to_line_m"] = np.nan
        row_attrs["_connector_line_row_index"] = np.nan
        if line_geom is None or line_geom.is_empty:
            continue
        if not isinstance(line_geom, LineString):
            for part in getattr(line_geom, "geoms", []):
                if isinstance(part, LineString) and not part.is_empty:
                    new_rows.append({**row_attrs, "geometry": part})
            continue

        line_length = float(line_geom.length)
        if line_length <= max(2.0 * min_endpoint_dist_m, 2.0 * min_segment_length_m):
            new_rows.append({**row_attrs, "geometry": line_geom})
            continue

        xmin, ymin, xmax, ymax = line_geom.bounds
        possible_inds = list(
            points_sindex.intersection(
                (xmin - tolerance_m, ymin - tolerance_m, xmax + tolerance_m, ymax + tolerance_m)
            )
        )

        cut_candidates = []
        for _, pt_row in subs_gdf.iloc[possible_inds].iterrows():
            pt = pt_row.geometry
            if pt is None or pt.is_empty:
                continue
            distance_to_line = float(line_geom.distance(pt))
            if distance_to_line > tolerance_m:
                continue

            distance_along = float(line_geom.project(pt))
            if (
                distance_along <= min_endpoint_dist_m
                or distance_along >= line_length - min_endpoint_dist_m
            ):
                continue

            projected_pt = line_geom.interpolate(distance_along)
            sid = str(pt_row["id"]) if "id" in pt_row.index else ""
            sname = (
                str(pt_row[name_col]).strip()
                if name_col is not None and pd.notna(pt_row[name_col])
                else ""
            )
            compatible, compatibility_reason = _split_candidate_compatible_with_endpoint_snaps(
                line_row,
                kv_col,
                (endpoint_snap_compatibility_by_substation or {}).get(sid),
            )
            if not compatible:
                compatibility_block_count += 1
                continue
            compatible, voltage_reason = _split_candidate_compatible_with_substation_voltage(
                line_row,
                kv_col,
                pt_row,
            )
            if not compatible:
                compatibility_block_count += 1
                continue
            if voltage_reason not in {"unknown_line_voltage", "unknown_substation_voltage"}:
                compatibility_reason = f"{compatibility_reason};{voltage_reason}"

            cut_candidates.append(
                (
                    distance_along,
                    projected_pt,
                    sid,
                    sname,
                    distance_to_line,
                    pt,
                    compatibility_reason,
                )
            )

        if not cut_candidates:
            new_rows.append({**row_attrs, "geometry": line_geom})
            continue

        cut_candidates.sort(key=lambda item: item[0])
        kept_candidates = []
        for candidate in cut_candidates:
            if kept_candidates and candidate[0] - kept_candidates[-1][0] < min_segment_length_m:
                continue
            kept_candidates.append(candidate)

        pieces = _split_line_by_distances(
            line_geom,
            [candidate[0] for candidate in kept_candidates],
            min_segment_length_m=min_segment_length_m,
        )

        if len(pieces) <= 1:
            new_rows.append({**row_attrs, "geometry": line_geom})
            continue

        split_line_count += 1
        total_cut_count += len(kept_candidates)
        for (
            distance_along,
            projected_pt,
            sid,
            sname,
            distance_to_line,
            sub_pt,
            compatibility_reason,
        ) in kept_candidates:
            connector_added = False
            connector_length_m = float(distance_to_line)
            if add_projection_connectors and connector_length_m > 0.1:
                connector_attrs = {
                    **row_attrs,
                    "_is_projection_connector": True,
                    "_connector_substation_id": sid,
                    "_connector_distance_to_line_m": connector_length_m,
                    "_connector_line_row_index": line_idx,
                }
                connector_geom = LineString(
                    [
                        (float(sub_pt.x), float(sub_pt.y)),
                        (float(projected_pt.x), float(projected_pt.y)),
                    ]
                )
                if connector_geom.length > 0.1:
                    new_rows.append({**connector_attrs, "geometry": connector_geom})
                    projection_connector_count += 1
                    connector_added = True

            audit_rows.append(
                {
                    "line_row_index": line_idx,
                    "line_topology_signature": line_topology_signature_text,
                    "substation_id": sid,
                    "substation_name": sname,
                    "distance_to_line_m": distance_to_line,
                    "distance_along_line_m": distance_along,
                    "line_length_m": line_length,
                    "cut_x": float(projected_pt.x),
                    "cut_y": float(projected_pt.y),
                    "sub_x": float(sub_pt.x),
                    "sub_y": float(sub_pt.y),
                    "connector_added": bool(connector_added),
                    "connector_length_m": connector_length_m if connector_added else np.nan,
                    "split_compatibility_reason": compatibility_reason,
                }
            )
        for seg_geom in pieces:
            new_rows.append({**row_attrs, "geometry": seg_geom})

    result_gdf = gpd.GeoDataFrame(new_rows, crs=lines_single.crs)
    audit_df = pd.DataFrame(audit_rows, columns=audit_columns)
    logger.info(
        "Substation through-line split complete: lines=%s -> %s, split_lines=%s, cut_points=%s, projection_connectors=%s, compatibility_blocked=%s, tolerance=%.1fm",
        len(lines_single),
        len(result_gdf),
        split_line_count,
        total_cut_count,
        projection_connector_count,
        compatibility_block_count,
        tolerance_m,
    )
    return result_gdf, audit_df


def _graph_node_key(pt):
    """Round a coordinate pair to the graph-node precision used in topology building."""
    return (round(float(pt[0]), 1), round(float(pt[1]), 1))


def _node_xy(node):
    """Return the physical x/y coordinate for a graph node."""
    return (float(node[0]), float(node[1]))


def _node_point(node):
    """Return a Shapely point for a graph node's physical coordinate."""
    return Point(_node_xy(node))


def _line_topology_signature(row, kv_col):
    """
    Conservative electrical compatibility signature for shared line vertices.

    Exact shared vertices are allowed to connect when owner group and voltage
    family match. This intentionally does not include Name/Circuit/Type/Status.
    """
    owner = _normalized_line_owner(row)
    voltage_family = _line_voltage_family(row, kv_col)
    owner_group = _topology_owner_group(owner, voltage_family)
    return (
        ("Owner", owner_group),
        ("voltage_family", voltage_family),
    )


def _parse_line_topology_signature(signature_text):
    """Parse a JSON-encoded owner/voltage-family topology signature."""
    if signature_text is None or pd.isna(signature_text):
        return None
    try:
        parsed = json.loads(str(signature_text))
        return tuple(tuple(item) for item in parsed)
    except Exception:
        return None


def _node_attribute_signature(node):
    """Return the scoped line signature carried by an attribute-scoped graph node."""
    if (
        isinstance(node, tuple)
        and len(node) >= 4
        and node[2] == "line_attr_scope"
    ):
        return node[3]
    return None


def _build_simple_graph(
    lines_gdf: gpd.GeoDataFrame,
    protected_node_keys: Optional[Set[tuple]] = None,
) -> nx.MultiGraph:
    """
    Build a physical MultiGraph from line geometries.

    - Uses nx.MultiGraph to support parallel (multi) edges.
    - Attempts to detect a voltage column ("KV", "VOLTAGE", "VOLT") and stores as edge attribute `voltage`.
    - Stores edge attributes: `weight` (distance in CRS units), `length_km`, and `voltage`.
    """
    logging.info("Building MultiGraph with Voltage attributes...")

    lines_gdf = lines_gdf.explode(index_parts=False).reset_index(drop=True)
    G = nx.MultiGraph()
    protected_node_keys = set(protected_node_keys or set())

    kv_col = _detect_voltage_column(lines_gdf)

    if kv_col:
        logging.info("Using column '%s' for voltage attributes.", kv_col)
    else:
        logging.warning("No voltage column found (expected 'kV' or 'VOLTAGE'). Edges will have voltage=0.")

    vertex_registry = {}
    row_signatures = {}
    for row_idx, row in lines_gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        signature = _line_topology_signature(row, kv_col)
        row_signatures[row_idx] = signature
        coords = list(geom.coords)
        if len(coords) < 2:
            continue

        for coord_idx, coord in enumerate(coords):
            node_key = _graph_node_key(coord)
            registry = vertex_registry.setdefault(
                node_key,
                {"signatures": set(), "has_interior": False},
            )
            registry["signatures"].add(signature)
            if coord_idx not in {0, len(coords) - 1}:
                registry["has_interior"] = True

    attribute_scoped_node_keys = {
        node_key
        for node_key, registry in vertex_registry.items()
        if node_key not in protected_node_keys
        and len(registry["signatures"]) > 1
    }
    if attribute_scoped_node_keys:
        logging.info(
            "Attribute-scoped shared line vertices/endpoints: %s protected from false cross-line joins.",
            len(attribute_scoped_node_keys),
        )

    def graph_node_for(coord, row_idx):
        node_key = _graph_node_key(coord)
        if node_key in attribute_scoped_node_keys:
            return (node_key[0], node_key[1], "line_attr_scope", row_signatures.get(row_idx, ()))
        return node_key

    for row_idx, row in lines_gdf.iterrows():
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
            u = graph_node_for(coords[i], row_idx)
            v = graph_node_for(coords[i + 1], row_idx)

            dist = _node_point(u).distance(_node_point(v))
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


def _collapse_multigraph_min_weight(G: nx.Graph) -> nx.Graph:
    """Return a simple graph preserving the minimum-weight edge between node pairs."""
    if not G.is_multigraph():
        return G

    H = nx.Graph()
    H.add_nodes_from(G.nodes(data=True))
    for u, v, data in G.edges(data=True):
        weight = float(data.get("weight", _node_point(u).distance(_node_point(v))))
        if H.has_edge(u, v) and H[u][v].get("weight", np.inf) <= weight:
            continue
        H.add_edge(
            u,
            v,
            weight=weight,
            length_km=float(data.get("length_km", weight / 1000.0)),
            voltage=float(data.get("voltage", 0.0) or 0.0),
        )
    return H


def _detect_voltage_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    """Return the first voltage-like column used by the CEC line data."""
    for col in gdf.columns:
        if str(col).upper() in {"KV", "VOLTAGE", "VOLT"}:
            return col
    return None


def build_topology_wrapper(
    paths: Paths,
    lines_path: str,
    subs_gdf: gpd.GeoDataFrame,
    bbox_pad_km: float,
    snap_primary_tol_m: float,
    snap_secondary_tol_m: float,
    snap_secondary_margin_m: float,
    snap_secondary_ratio_max: float,
):
    """Build the repaired physical transmission graph used by shortest paths."""
    logger = logging.getLogger()

    if not os.path.exists(lines_path):
        logger.error("Transmission line file not found: %s", lines_path)
        return None, None, None, None, None

    if lines_path.lower().endswith(".csv"):
        lines_df = pd.read_csv(lines_path)
        wkt_col = next(
            (c for c in lines_df.columns if "wkt" in c.lower() or "geom" in c.lower()),
            None,
        )
        if not wkt_col:
            logger.error("CSV does not contain WKT/geometry column.")
            return None, None, None, None, None
        lines_df["geometry"] = lines_df[wkt_col].apply(wkt.loads)
        lines_gdf = gpd.GeoDataFrame(lines_df, geometry="geometry", crs="EPSG:3857")
    else:
        lines_gdf = gpd.read_file(lines_path)
    lines_gdf = _apply_transmission_line_attribute_overrides(lines_gdf)

    lines_proj = lines_gdf.to_crs(epsg=3310)
    subs_proj = subs_gdf.to_crs(epsg=3310)
    minx, miny, maxx, maxy = subs_proj.total_bounds
    pad_m = float(bbox_pad_km) * 1000.0
    bbox_geom = box(minx - pad_m, miny - pad_m, maxx + pad_m, maxy + pad_m)
    lines_clipped = lines_proj.cx[
        minx - pad_m : maxx + pad_m,
        miny - pad_m : maxy + pad_m,
    ].copy().explode(index_parts=False).reset_index(drop=True)
    if lines_clipped.empty:
        logger.error("No transmission lines inside bbox.")
        return None, None, None, None, None

    snap_primary_tol_m = float(snap_primary_tol_m)
    snap_secondary_tol_m = max(float(snap_secondary_tol_m), snap_primary_tol_m)
    lines_snapped, endpoint_audit_df = force_snap_endpoints_to_substations(
        lines_clipped,
        subs_proj,
        strict_tolerance_m=snap_primary_tol_m,
        extended_tolerance_m=snap_secondary_tol_m,
        second_nearest_margin_m=float(snap_secondary_margin_m),
        second_nearest_ratio_max=float(snap_secondary_ratio_max),
        secondary_outer_start_m=getattr(paths, "LINE_SNAP_SECONDARY_OUTER_START_M", None),
        secondary_outer_margin_m=getattr(paths, "LINE_SNAP_SECONDARY_OUTER_MARGIN_M", None),
        secondary_outer_ratio_max=getattr(paths, "LINE_SNAP_SECONDARY_OUTER_RATIO_MAX", None),
        return_endpoint_audit=True,
    )

    if getattr(paths, "ENABLE_PROTECTED_JUNCTION_CLUSTER_SNAP", False):
        lines_snapped, endpoint_audit_df = snap_protected_junction_clusters_to_substations(
            lines_snapped,
            subs_proj,
            endpoint_audit_df,
            strict_tolerance_m=snap_primary_tol_m,
            extended_tolerance_m=snap_secondary_tol_m,
            second_nearest_margin_m=float(snap_secondary_margin_m),
            second_nearest_ratio_max=float(snap_secondary_ratio_max),
            secondary_outer_start_m=getattr(paths, "LINE_SNAP_SECONDARY_OUTER_START_M", None),
            secondary_outer_margin_m=getattr(paths, "LINE_SNAP_SECONDARY_OUTER_MARGIN_M", None),
            secondary_outer_ratio_max=getattr(paths, "LINE_SNAP_SECONDARY_OUTER_RATIO_MAX", None),
        )

    endpoint_compatibility = _build_endpoint_snap_compatibility_by_substation(
        lines_snapped,
        endpoint_audit_df,
        _detect_voltage_column(lines_snapped),
    )

    bbox_edge_buffer_m = (
        paths.BBOX_EDGE_EXCLUSION_BUFFER_M
        if paths.EXCLUDE_BBOX_EDGE_ENDPOINTS_FROM_MERGE
        else None
    )
    lines_repaired, _ = merge_nearby_line_endpoints(
        lines_snapped,
        tolerance_m=paths.LINE_ENDPOINT_MERGE_TOLERANCE_M,
        protected_points_gdf=subs_proj,
        protected_tol_m=snap_primary_tol_m,
        bbox_geom=bbox_geom,
        bbox_edge_buffer_m=bbox_edge_buffer_m,
        endpoint_audit_df=endpoint_audit_df,
    )

    split_audit_df = pd.DataFrame()
    if paths.ENABLE_SUBSTATION_LINE_SPLIT:
        lines_for_graph, split_audit_df = split_lines_at_nearby_substations(
            lines_repaired,
            subs_proj,
            tolerance_m=paths.LINE_SPLIT_TOLERANCE_M,
            min_endpoint_dist_m=paths.LINE_SPLIT_MIN_ENDPOINT_DIST_M,
            min_segment_length_m=paths.LINE_SPLIT_MIN_SEGMENT_LENGTH_M,
            add_projection_connectors=getattr(paths, "ENABLE_SUBSTATION_PROJECTION_CONNECTORS", True),
            endpoint_snap_compatibility_by_substation=endpoint_compatibility,
        )
        if paths.OUTPUT_LINE_SPLIT_AUDIT_CSV:
            os.makedirs(os.path.dirname(paths.OUTPUT_LINE_SPLIT_AUDIT_CSV), exist_ok=True)
            split_audit_df.to_csv(paths.OUTPUT_LINE_SPLIT_AUDIT_CSV, index=False)
            logger.info(
                "Substation through-line split audit saved to %s (n=%s)",
                paths.OUTPUT_LINE_SPLIT_AUDIT_CSV,
                len(split_audit_df),
            )
    else:
        lines_for_graph = lines_repaired

    protected_node_keys = {
        _graph_node_key((geom.x, geom.y))
        for geom in subs_proj.geometry
        if geom is not None and not geom.is_empty
    }
    G = _build_simple_graph(
        lines_for_graph,
        protected_node_keys=protected_node_keys,
    )

    return G, lines_for_graph, subs_proj, lines_gdf, split_audit_df


# ---------------------------------------------------------------------------
# 4) Direct substation links
# ---------------------------------------------------------------------------

def calculate_connectivity(
    G: nx.Graph,
    subs_proj: gpd.GeoDataFrame,
    max_snap_m: float,
):
    """
    Register substations to the nearest graph nodes only when the geometric
    offset is small enough to confirm a real topology anchor.

    Map substations to nearest graph nodes (within max_snap_m),
    then compute pairwise substation distances via single-source Dijkstra from
    each substation node.

    Returns:
        dist_ss: dict[src_sid][tgt_sid] = shortest path distance (km)
        sub_id_to_node: dict[substation_id] = graph_node
        all_paths: dict[src_sid, dict[node, list[node]]] 
        diagnostics: dict with snap counts and unsnapped-substation details
    """
    logger = logging.getLogger()
    max_snap_m = float(max_snap_m)
    name_col = next((c for c in ["NAME", "name", "Name"] if c in subs_proj.columns), None)
    city_col = next((c for c in ["CITY", "city", "City"] if c in subs_proj.columns), None)
    diag_cols = [
        "substation_id",
        "substation_name",
        "city",
        "nearest_node",
        "nearest_node_distance_m",
        "snapped",
    ]

    path_graph = _collapse_multigraph_min_weight(G)
    graph_nodes = list(path_graph.nodes())
    if not graph_nodes:
        empty_diag = pd.DataFrame(columns=diag_cols)
        return {}, {}, {}, {
            "snapped_count": 0,
            "unsnapped_count": len(subs_proj),
            "snap_diagnostics": empty_diag,
            "unsnapped_substations": empty_diag.copy(),
            "snapped_distance_summary_m": {},
            "substations_over_50m": empty_diag.copy(),
            "substations_over_threshold": empty_diag.copy(),
        }

    graph_node_coords = np.array([_node_xy(node) for node in graph_nodes])
    node_tree = cKDTree(graph_node_coords)

    # 1) Snap substations to graph nodes.
    #    With endpoint repair earlier, this should match tightly.
    sub_id_to_node = {}
    snap_records = []
    for _, row in subs_proj.iterrows():
        sid = str(row["id"])
        pt = (row.geometry.x, row.geometry.y)
        sname = str(row[name_col]).strip() if name_col is not None and pd.notna(row[name_col]) else ""
        city = str(row[city_col]).strip() if city_col is not None and pd.notna(row[city_col]) else ""

        d, idx_node = node_tree.query(pt)
        snapped = d <= max_snap_m
        nearest_node = graph_nodes[idx_node]
        snap_records.append(
            {
                "substation_id": sid,
                "substation_name": sname,
                "city": city,
                "nearest_node": nearest_node,
                "nearest_node_distance_m": float(d),
                "snapped": bool(snapped),
            }
        )
        if d <= max_snap_m:
            sub_id_to_node[sid] = nearest_node

    snap_df = pd.DataFrame(snap_records)
    snapped_count = int(snap_df["snapped"].sum()) if not snap_df.empty else 0
    snapped_df = snap_df[snap_df["snapped"]].copy() if not snap_df.empty else snap_df.copy()
    unsnapped_df = snap_df[~snap_df["snapped"]].copy() if not snap_df.empty else snap_df.copy()
    over_50_df = snap_df[snap_df["nearest_node_distance_m"] > 50.0].copy() if not snap_df.empty else snap_df.copy()
    over_threshold_df = snap_df[snap_df["nearest_node_distance_m"] > max_snap_m].copy() if not snap_df.empty else snap_df.copy()
    unsnapped_count = len(unsnapped_df)
    snapped_distance_summary_m = {}
    if not snapped_df.empty:
        snapped_distance_summary_m = {
            "min": float(snapped_df["nearest_node_distance_m"].min()),
            "p50": float(snapped_df["nearest_node_distance_m"].quantile(0.50)),
            "p90": float(snapped_df["nearest_node_distance_m"].quantile(0.90)),
            "p95": float(snapped_df["nearest_node_distance_m"].quantile(0.95)),
            "max": float(snapped_df["nearest_node_distance_m"].max()),
        }
    logger.info(
        "Connectivity registration summary: snapped=%s, unsnapped=%s, max_substation_to_graph_snap_dist_m=%s",
        snapped_count,
        unsnapped_count,
        max_snap_m,
    )
    if snapped_distance_summary_m:
        logger.info(
            "Connectivity snapped-distance stats (m): min=%.2f, p50=%.2f, p90=%.2f, p95=%.2f, max=%.2f",
            snapped_distance_summary_m["min"],
            snapped_distance_summary_m["p50"],
            snapped_distance_summary_m["p90"],
            snapped_distance_summary_m["p95"],
            snapped_distance_summary_m["max"],
        )
    if not over_50_df.empty:
        logger.info(
            "Substations with nearest graph-node distance > 50 m: %s",
            over_50_df[["substation_id", "substation_name", "nearest_node_distance_m"]].to_dict("records"),
        )
    if unsnapped_count:
        logger.warning(
            "Unsnapped substations (> %.1f m): %s",
            max_snap_m,
            unsnapped_df[["substation_id", "substation_name", "nearest_node_distance_m"]].to_dict("records"),
        )

    if not sub_id_to_node:
        logger.warning("No substations snapped to the network.")
        return {}, {}, {}, {
            "snapped_count": snapped_count,
            "unsnapped_count": unsnapped_count,
            "snap_diagnostics": snap_df,
            "unsnapped_substations": unsnapped_df,
            "snapped_distance_summary_m": snapped_distance_summary_m,
            "substations_over_50m": over_50_df,
            "substations_over_threshold": over_threshold_df,
        }

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
            lengths, paths = nx.single_source_dijkstra(path_graph, src_node, weight="weight")
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

    return dist_ss, sub_id_to_node, all_paths, {
        "snapped_count": snapped_count,
        "unsnapped_count": unsnapped_count,
        "snap_diagnostics": snap_df,
        "unsnapped_substations": unsnapped_df,
        "snapped_distance_summary_m": snapped_distance_summary_m,
        "substations_over_50m": over_50_df,
        "substations_over_threshold": over_threshold_df,
    }


def compute_direct_links(
    dist_ss,
    sub_id_to_node,
    all_paths,
    max_dist_km=None,
    projection_anchor_df: Optional[pd.DataFrame] = None,
    projection_anchor_audit_csv: Optional[str] = None,
    projection_anchor_debug_csv: Optional[str] = None,
):
    """
    Identify "direct" substation adjacency:
      - reachable on the physical graph
      - path does not pass through any other substation node internally
      - path does not pass through another substation's projection split anchor
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

    projection_anchor_by_node = {}
    if projection_anchor_df is not None and not projection_anchor_df.empty:
        required_cols = {"substation_id", "cut_x", "cut_y"}
        if required_cols.issubset(projection_anchor_df.columns):
            for _, anchor_row in projection_anchor_df.iterrows():
                sid = str(anchor_row["substation_id"]).strip()
                if not sid:
                    continue
                try:
                    node = _graph_node_key((anchor_row["cut_x"], anchor_row["cut_y"]))
                except Exception:
                    continue
                projection_anchor_by_node.setdefault(node, []).append(
                    {
                        "substation_id": sid,
                        "substation_name": str(anchor_row.get("substation_name", "")).strip(),
                        "distance_to_line_m": float(anchor_row.get("distance_to_line_m", np.nan)),
                        "line_topology_signature": _parse_line_topology_signature(
                            anchor_row.get("line_topology_signature")
                        ),
                    }
                )

    direct_links = []
    projection_anchor_audit_rows = []
    projection_anchor_debug_rows = []
    seen = set()  # dedupe undirected pairs
    projection_anchor_debug_enabled = bool(projection_anchor_debug_csv)

    def _find_internal_projection_anchor(
        src_sid: str,
        tgt_sid: str,
        path_nodes: list,
    ) -> Optional[dict]:
        """Return the first non-endpoint substation projection anchor on the path interior."""
        if not projection_anchor_by_node:
            return None
        for node in path_nodes[1:-1]:
            node_key = _graph_node_key(_node_xy(node))
            node_signature = _node_attribute_signature(node)
            for anchor in projection_anchor_by_node.get(node_key, []):
                anchor_signature = anchor.get("line_topology_signature")
                if (
                    node_signature is not None
                    and (anchor_signature is None or node_signature != anchor_signature)
                ):
                    continue
                sid = anchor["substation_id"]
                if sid in {src_sid, tgt_sid}:
                    continue
                path_coords = [_node_xy(path_node) for path_node in path_nodes]
                path_line = LineString(path_coords)
                distance_along_m = float(path_line.project(Point(node_key))) if len(path_nodes) >= 2 else np.nan
                return {
                    "intermediate_substation_id": sid,
                    "intermediate_substation_name": anchor["substation_name"],
                    "projection_anchor_distance_to_path_m": 0.0,
                    "projection_anchor_distance_along_path_m": distance_along_m,
                    "path_length_km": float(path_line.length / 1000.0) if len(path_nodes) >= 2 else np.nan,
                    "projection_distance_to_line_m": anchor["distance_to_line_m"],
                }
        return None

    def _append_projection_anchor_debug_row(
        src_sid: str,
        tgt_sid: str,
        d_km: float,
        path_nodes: list,
        projection_anchor: Optional[dict],
        decision: str,
    ) -> None:
        if not projection_anchor_debug_enabled:
            return
        a, b = sorted([src_sid, tgt_sid])
        row = {
            "src": a,
            "tgt": b,
            "length_km": float(d_km),
            "path_nodes_count": len(path_nodes),
            "decision": decision,
        }
        if projection_anchor is not None:
            row.update(projection_anchor)
        else:
            row.update(
                {
                    "intermediate_substation_id": "",
                    "intermediate_substation_name": "",
                    "projection_anchor_distance_to_path_m": np.nan,
                    "projection_anchor_distance_along_path_m": np.nan,
                    "path_length_km": float(d_km),
                    "projection_distance_to_line_m": np.nan,
                }
            )
        projection_anchor_debug_rows.append(row)

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

            projection_anchor = _find_internal_projection_anchor(src_sid, tgt_sid, path_nodes)
            if projection_anchor is not None:
                a, b = sorted([src_sid, tgt_sid])
                projection_anchor_audit_rows.append(
                    {
                        "src": a,
                        "tgt": b,
                        "length_km": float(d_km),
                        "intermediate_substation_id": projection_anchor["intermediate_substation_id"],
                        "intermediate_substation_name": projection_anchor["intermediate_substation_name"],
                        "projection_anchor_distance_to_path_m": projection_anchor["projection_anchor_distance_to_path_m"],
                        "projection_anchor_distance_along_path_m": projection_anchor["projection_anchor_distance_along_path_m"],
                        "path_length_km": projection_anchor["path_length_km"],
                        "projection_distance_to_line_m": projection_anchor["projection_distance_to_line_m"],
                    }
                )
                _append_projection_anchor_debug_row(
                    src_sid,
                    tgt_sid,
                    d_km,
                    path_nodes,
                    projection_anchor,
                    decision="blocked_by_projection_anchor",
                )
                continue

            a, b = sorted([src_sid, tgt_sid])
            key = (a, b)
            if key in seen:
                continue

            seen.add(key)
            _append_projection_anchor_debug_row(
                src_sid,
                tgt_sid,
                d_km,
                path_nodes,
                None,
                decision="accepted",
            )
            direct_links.append(
                {
                    "src": a,
                    "tgt": b,
                    "length_km": float(d_km),
                    "path_nodes": path_nodes,
                }
            )

    if projection_anchor_audit_csv:
        projection_anchor_audit_df = pd.DataFrame(projection_anchor_audit_rows).drop_duplicates(
            subset=["src", "tgt"],
            keep="first",
        )
        os.makedirs(os.path.dirname(projection_anchor_audit_csv), exist_ok=True)
        projection_anchor_audit_df.to_csv(projection_anchor_audit_csv, index=False)
        logging.info(
            "Direct-link projection-anchor audit saved to %s (n=%s)",
            projection_anchor_audit_csv,
            len(projection_anchor_audit_df),
        )

    if projection_anchor_debug_csv:
        projection_anchor_debug_df = pd.DataFrame(projection_anchor_debug_rows).drop_duplicates(
            subset=["src", "tgt", "decision"],
            keep="first",
        )
        os.makedirs(os.path.dirname(projection_anchor_debug_csv), exist_ok=True)
        projection_anchor_debug_df.to_csv(projection_anchor_debug_csv, index=False)
        logging.info(
            "Direct-link projection-anchor debug saved to %s (n=%s)",
            projection_anchor_debug_csv,
            len(projection_anchor_debug_df),
        )

    logging.info(
        "Computed %s direct substation links%s.",
        len(direct_links),
        f" (projection anchors rejected {len(projection_anchor_audit_rows)} candidates)"
        if projection_anchor_by_node
        else "",
    )
    return direct_links


# Main
# ---------------------------------------------------------------------------

def main(paths: Optional[Paths] = None):
    """Run the end-to-end topology, connectivity, and mapping export pipeline."""
    setup_logging()
    logger = logging.getLogger()
    cfg = paths if paths is not None else Paths()

    try:
        whitelist = load_city_whitelist(cfg.CITY_TRACTS_LIST_CSV)
        subs = load_substations(cfg.DEVICES_CSV)
        tracts = load_tracts_filtered(cfg.LA_TRACTS_SHP, whitelist)

        # 1) Build physical topology
        G, lines_repaired, subs_proj, _, split_audit_df = build_topology_wrapper(
            paths=cfg,
            lines_path=cfg.TRANSMISSION_LINES_SHP,
            subs_gdf=subs,
            bbox_pad_km=cfg.BBOX_PAD_KM,
            snap_primary_tol_m=cfg.LINE_SNAP_TOLERANCE_M,
            snap_secondary_tol_m=cfg.LINE_SNAP_SECONDARY_TOLERANCE_M,
            snap_secondary_margin_m=cfg.LINE_SNAP_SECONDARY_MARGIN_M,
            snap_secondary_ratio_max=cfg.LINE_SNAP_SECONDARY_RATIO_MAX,
        )

        if G is None:
            logger.error("Topology calculation failed.")
            logger.info("ALL DONE.")
            return

        # 2) Compute along-network shortest paths between substations
        dist_ss, sub_node_map, all_paths, connectivity_diag = calculate_connectivity(
            G,
            subs_proj,
            cfg.MAX_SUBSTATION_TO_GRAPH_SNAP_DIST_M,
        )
        logger.info(
            "Substation-to-graph snap diagnostics: snapped=%s, unsnapped=%s",
            connectivity_diag["snapped_count"],
            connectivity_diag["unsnapped_count"],
        )

        # 3) Extract direct adjacency links between substations.
        direct_links = compute_direct_links(
            dist_ss,
            sub_node_map,
            all_paths,
            max_dist_km=cfg.DIRECT_LINK_MAX_DIST_KM,
            projection_anchor_df=split_audit_df,
            projection_anchor_audit_csv=cfg.OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_AUDIT_CSV,
            projection_anchor_debug_csv=cfg.OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_DEBUG_CSV,
        )

        # 4) Visualize physical network + direct links.
        if cfg.OUTPUT_PLOT_PNG:
            visualize_topology(
                G,
                lines_repaired,
                subs_proj,
                tracts,
                sub_node_map,
                direct_links,
                cfg.OUTPUT_PLOT_PNG,
            )

        visualize_topology_interactive(
            G,
            lines_repaired,
            subs_proj,
            tracts,
            sub_node_map,
            direct_links,
            cfg.OUTPUT_INTERACTIVE_HTML,
        )

        # 5) Export node coordinates for the accepted substation inventory.
        export_nodes_csv(
            cfg.OUTPUT_GRAPH_NODES_CSV,
            subs,
        )

        # 5b) Export edges from direct_links
        export_edges_from_direct_links(
            direct_links,
            cfg.OUTPUT_GRAPH_EDGES_CSV,
        )

        # 6) Build and export the unthresholded W matrix for sensitivity analysis.
        W_raw = build_W_matrix(
            subs,
            tracts,
            dist_ss,
        )
        export_mapping_from_W(
            W_raw,
            tracts,
            subs,
            cfg.OUTPUT_UNTHRESHOLDED_MAPPING_CSV,
            graph_nodes_csv=cfg.OUTPUT_GRAPH_NODES_CSV,
        )

        # 6b) Apply per-row minimum effective weight threshold + renormalize
        W = apply_min_weight_threshold(W_raw, min_weight=cfg.MIN_EFFECTIVE_WEIGHT)

        # 7) Export mapping while ensuring each substation appears at least once.
        export_mapping_from_W(
            W,
            tracts,
            subs,
            cfg.OUTPUT_MAPPING_CSV,
            graph_nodes_csv=cfg.OUTPUT_GRAPH_NODES_CSV,
            suppressed_threshold_csv=cfg.OUTPUT_SUPPRESSED_THRESHOLD_CSV,
        )

        logger.info("ALL DONE.")

    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()


