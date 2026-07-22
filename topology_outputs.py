"""Weight-matrix and CSV export helpers for the topology workflow."""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

# 5. W Matrix & Export
# ---------------------------------------------------------------------------

# Global IDW parameters
IDW_POWER: float = 2.0         # w ~ 1 / d^p (default p=1)
MIN_DIST: float = 1e-3          # avoid division by zero when d == 0
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
            w_j is proportional to 1 / d_total^IDW_POWER
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
            # 3) IDW on all finite distances: w is proportional to 1 / d^p.
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
    min_weight: float,
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


def export_mapping_from_W(
    W,
    tracts_gdf,
    subs_gdf,
    out_csv,
    *,
    graph_nodes_csv: Optional[str] = None,
    suppressed_threshold_csv: Optional[str] = None,
):
    """
    Export tract-to-substation mapping table with smart injection.

    Shared consistency rule:
      - export the thresholded/renormalized W matrix as-is
      - do not re-inject substations that still exist in the graph but were
        merely zeroed out by thresholding
      - only inject substations that are truly missing from the export chain
    """
    if W.empty:
        return

    WEIGHT_EXPORT_EPS = 1e-6
    VOLTAGE_THRESHOLD = 200.0
    MIN_CLAMP = 0.1
    MAX_CLAMP = 5.0

    if "MAX_VOLT" in subs_gdf.columns:
        volt_map = dict(
            zip(
                subs_gdf["id"].astype(str).str.strip(),
                subs_gdf["MAX_VOLT"].fillna(0.0),
            )
        )
    else:
        logging.warning("MAX_VOLT missing! Defaulting to Low Voltage logic for all islands.")
        volt_map = {}

    main_tree = None
    tract_centroids = None
    tract_ids_list = []
    subs_proj = subs_gdf

    if not tracts_gdf.empty:
        tracts_proj = tracts_gdf
        try:
            if subs_gdf.crs != tracts_proj.crs:
                subs_proj = subs_gdf.to_crs(tracts_proj.crs)
        except Exception:
            subs_proj = subs_gdf

        tract_centroids = tracts_proj.geometry.centroid
        tract_ids_list = tracts_proj["tract_id"].astype(str).tolist()

        connected_sub_ids = W.columns.astype(str).tolist()
        connected_subs_gdf = subs_proj[subs_proj["id"].astype(str).isin(connected_sub_ids)]
        if not connected_subs_gdf.empty:
            main_coords = list(zip(connected_subs_gdf.geometry.x, connected_subs_gdf.geometry.y))
            main_tree = cKDTree(main_coords)

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
    if df.empty:
        exported_subs = set()
    else:
        df["substation_id"] = df["substation_id"].astype(str).str.strip()
        df["tract_id"] = df["tract_id"].astype(str).str.strip()
        exported_subs = set(df["substation_id"].tolist())

    all_sub_ids = set(subs_gdf["id"].astype(str).str.strip().tolist())
    graph_node_ids = set()
    graph_nodes_path = Path(graph_nodes_csv) if graph_nodes_csv else None
    if graph_nodes_path is not None and graph_nodes_path.exists():
        graph_nodes_df = pd.read_csv(graph_nodes_path, dtype={"id": str})
        if "id" in graph_nodes_df.columns:
            graph_node_ids = set(graph_nodes_df["id"].astype(str).str.strip().tolist())

    zeroed_by_threshold_subs = sorted((all_sub_ids & graph_node_ids) - exported_subs)
    protected_proxy_subs = set(
        str(s).strip()
        for s in globals().get("PROTECTED_PROXY_SUB_IDS", set())
        if str(s).strip()
    )
    export_chain_failure_subs = sorted(all_sub_ids - exported_subs - set(zeroed_by_threshold_subs))
    truly_missing_subs = sorted(
        (protected_proxy_subs | set(export_chain_failure_subs)) - set(zeroed_by_threshold_subs)
    )
    if suppressed_threshold_csv:
        subs_meta = subs_gdf.copy()
        subs_meta["id"] = subs_meta["id"].astype(str).str.strip()
        suppressed_columns = [
            "substation_id",
            "thresholded_export_present",
            "in_graph_nodes",
            "protected_proxy_flag",
            "NAME",
            "CITY",
            "lat",
            "lon",
            "MAX_VOLT",
            "MAX_VOLT_N",
            "Owner",
        ]
        suppressed_rows = []
        for sid in zeroed_by_threshold_subs:
            sub_row = subs_meta[subs_meta["id"] == sid]
            rec = {
                "substation_id": sid,
                "thresholded_export_present": False,
                "in_graph_nodes": sid in graph_node_ids,
                "protected_proxy_flag": sid in protected_proxy_subs,
            }
            if not sub_row.empty:
                for col in ["NAME", "CITY", "lat", "lon", "MAX_VOLT", "MAX_VOLT_N", "Owner"]:
                    if col in sub_row.columns:
                        rec[col] = sub_row.iloc[0][col]
            suppressed_rows.append(rec)

        pd.DataFrame(suppressed_rows, columns=suppressed_columns).to_csv(suppressed_threshold_csv, index=False)
        logging.info(
            "Threshold-suppression audit saved to %s (n=%s)",
            suppressed_threshold_csv,
            len(suppressed_rows),
        )

    logging.info(
        "Mapping export classification: exported_subs=%s, zeroed_by_threshold_subs=%s, truly_missing_subs=%s",
        len(exported_subs),
        len(zeroed_by_threshold_subs),
        len(truly_missing_subs),
    )

    if truly_missing_subs and not tracts_gdf.empty:
        logging.info(
            "--- Smart Injection: Processing %s truly missing substations ---",
            len(truly_missing_subs),
        )
        injected_rows = []
        for sid in truly_missing_subs:
            sub_row = subs_proj[subs_proj["id"].astype(str).str.strip() == sid]
            if sub_row.empty:
                continue

            sub_pt = sub_row.geometry.iloc[0]
            dists_to_tracts = tract_centroids.distance(sub_pt).values
            nearest_idx = int(np.argmin(dists_to_tracts))
            target_tid = tract_ids_list[nearest_idx]
            d_island = max(float(dists_to_tracts[nearest_idx]), 1e-3)

            if main_tree:
                centroid_pt = tract_centroids.iloc[nearest_idx]
                d_main, _ = main_tree.query((centroid_pt.x, centroid_pt.y), k=1)
            else:
                d_main = d_island
            d_main = max(float(d_main), 1e-3)

            voltage = volt_map.get(sid, 0.0)
            if voltage >= VOLTAGE_THRESHOLD:
                final_weight = 0.001
            else:
                raw_weight = (d_main / d_island) ** 2
                final_weight = min(MAX_CLAMP, max(MIN_CLAMP, raw_weight))

            injected_rows.append(
                {
                    "tract_id": str(target_tid),
                    "substation_id": str(sid),
                    "weight": float(final_weight),
                }
            )

        if injected_rows:
            df = pd.concat([df, pd.DataFrame(injected_rows)], ignore_index=True)
            logging.info(
                "--- Smart Injection Complete: Added %s truly missing substations ---",
                len(injected_rows),
            )

    if not df.empty:
        df["tract_id"] = df["tract_id"].astype(str).str.strip()
        df["substation_id"] = df["substation_id"].astype(str).str.strip()
        df["weight"] = pd.to_numeric(df["weight"], errors="coerce").fillna(0.0)
        row_sums = df.groupby("tract_id")["weight"].transform("sum")
        valid_rows = row_sums > 0.0
        df.loc[valid_rows, "weight"] = df.loc[valid_rows, "weight"] / row_sums[valid_rows]

    pop_col = next(
        (c for c in ["population", "POPULATION", "E_TOTPOP", "totpop"] if c in tracts_gdf.columns),
        None,
    )
    if pop_col:
        pop_map = tracts_gdf.set_index("tract_id")[pop_col].to_dict()
        df["population"] = df["tract_id"].map(pop_map).fillna(0).astype(int)
    else:
        df["population"] = 0

    lat_map = subs_gdf.set_index("id")["lat"].to_dict()
    lon_map = subs_gdf.set_index("id")["lon"].to_dict()
    df["lat"] = df["substation_id"].map(lat_map)
    df["lon"] = df["substation_id"].map(lon_map)

    df.to_csv(out_csv, index=False)
    logging.info(f"Mapping saved to {out_csv}")


def export_nodes_csv(nodes_csv, subs_gdf):
    """Export node coordinates for the accepted substation inventory."""
    if not nodes_csv:
        return

    ndf = subs_gdf[["id", "lat", "lon"]].copy()
    ndf["id"] = ndf["id"].astype(str)
    ndf.to_csv(nodes_csv, index=False)
    logging.info(f"Nodes exported to {nodes_csv}")


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


# ---------------------------------------------------------------------------

