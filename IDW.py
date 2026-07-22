import os
import json
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from pyproj import Transformer
from pathlib import Path
from scipy.spatial import cKDTree

# GIS: lon/lat (EPSG:4326) -> meters (EPSG:3310, CA Albers)
TARGET_CRS = "EPSG:3310"
TRANSFORMER = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)

IDW_RADIUS_KM = 11.0
IDW_RADIUS_M = IDW_RADIUS_KM * 1000.0

# ================= Paths =================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
GRID_DIR: str = str(DATA_DIR / "MS_048_CA_pt01_MMI_GM_datafiles")

# 1) Substation file
SUB_CSV = os.path.join(DATA_DIR, "Los_Angeles_City_SUBSTATION_with_fragility_29.csv")

# 2) Output file
FINAL_OUTPUT_CSV = os.path.join(DATA_DIR, "Substations_PGA_IDW_CEC.csv")

# 3) Scenarios: (type, path, column_name_for_csv)
SCENARIOS = {
    # Legacy (CovJSON)
    "Northridge":  ("json", os.path.join(DATA_DIR, "Northridge_PGA.covjson"), None),
    "SanFernando": ("json", os.path.join(DATA_DIR, "SanFernando_PGA.covjson"), None),
    "LongBeach":  ("json", os.path.join(DATA_DIR, "LongBeach_PGA.covjson"), None),
    # New (CSV)
    "2pc50": ("csv", os.path.join(GRID_DIR, "CA_pt01_GM_maps.csv"), "PGA-2pc50"),
}

# ================= Parameters =================
IDW_POWER = 2
IDW_K = 8

# ================= Reliability policy =================
FAIL_FAST = True

# CovJSON:
# - True  : values are ln(g)
# - False : values are g
# - None  : infer from CovJSON metadata (unit symbol/label). If not recognized, fail.
COVJSON_VALUES_ARE_LN = None

# CSV grid:
# - True  : values are ln(g)
# - False : values are g and will be converted to ln(g)
CSV_VALUES_ARE_LN = False


@dataclass(frozen=True)
class IDWConfig:
    sub_csv: str = SUB_CSV
    final_output_csv: str = FINAL_OUTPUT_CSV
    scenarios: dict = field(default_factory=lambda: dict(SCENARIOS))

# ================= Helpers =================
def _die(msg: str) -> None:
    if FAIL_FAST:
        raise ValueError(msg)
    print(f"[ERROR] {msg}")

def _warn(msg: str) -> None:
    print(f"[WARN] {msg}")

def _to_numeric(series: pd.Series) -> np.ndarray:
    return pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)

def _finite_mask(*arrays) -> np.ndarray:
    mask = np.ones_like(arrays[0], dtype=bool)
    for a in arrays:
        mask &= np.isfinite(a)
    return mask

def _safe_log_g(vals_g: np.ndarray, context: str) -> np.ndarray:
    """
    Convert g -> ln(g).
    Non-positive values (<=0) are treated as NaN (warn only).
    """
    vals_g = np.asarray(vals_g, dtype=float)
    out = np.full_like(vals_g, np.nan, dtype=float)

    finite = np.isfinite(vals_g)
    positive = finite & (vals_g > 0.0)
    bad = finite & (vals_g <= 0.0)

    if np.any(bad):
        _warn(f"{context}: Found non-positive PGA values (<=0). Treated as NaN. Count={int(bad.sum())}.")

    out[positive] = np.log(vals_g[positive])
    return out

def project_lonlat_to_xy(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    x, y = TRANSFORMER.transform(lon, lat)
    return np.asarray(x, dtype=float), np.asarray(y, dtype=float)

def _pick_col(columns, candidates):
    """
    Case-insensitive column picker.
    Returns the original column name if found, else None.
    """
    col_map = {c.strip().lower(): c for c in columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in col_map:
            return col_map[key]
    return None

def covjson_values_are_ln_g(cov: dict, param_key: str) -> bool:
    """
    Determine whether CovJSON values are ln(g) based on metadata.
    Typical patterns:
      unit.symbol.value == 'ln(g)'  OR unit.label.en contains 'ln(g)'  => ln(g)
      unit.symbol.value == 'g'      OR unit.label.en == 'g'           => g
    """
    p = cov.get("parameters", {}).get(param_key, {})
    unit = p.get("unit", {})
    sym = str(unit.get("symbol", {}).get("value", "")).strip()
    lab = str(unit.get("label", {}).get("en", "")).strip()

    s = f"{sym} {lab}".lower().strip()

    # ln(g) detection
    if "ln(g)" in s or sym.lower().startswith("ln"):
        return True

    # g detection (avoid treating ln(g) as g)
    if ("g" == sym.lower().strip()) or ("g" == lab.lower().strip()) or (s == "g"):
        return False

    _die(
        f"CovJSON unit not recognized for parameter '{param_key}'. "
        f"unit.symbol='{sym}', unit.label.en='{lab}'. "
        f"Set COVJSON_VALUES_ARE_LN explicitly."
    )
    return False

# ================= IDW core =================
def idw_core(
    lon_pts: np.ndarray,
    lat_pts: np.ndarray,
    grid_lon: np.ndarray,
    grid_lat: np.ndarray,
    grid_val_ln: np.ndarray,
    *,
    radius_m: float = IDW_RADIUS_M,
    k: int = IDW_K,
    power: float = IDW_POWER,
) -> np.ndarray:
    """
    IDW interpolation using KDTree for high performance.
    Inputs/outputs are ln(g).
    """
    # ---------------------------------------------------------
    # 1. Input Validation and Data Cleaning
    # ---------------------------------------------------------
    # Ensure inputs are numpy arrays of floats
    lon_pts = np.asarray(lon_pts, dtype=float)
    lat_pts = np.asarray(lat_pts, dtype=float)

    # Check for missing or empty grid data
    if grid_lon is None or grid_lat is None or grid_val_ln is None:
        _die("IDW: grid arrays are None (data load failed).")
        return np.full(len(lon_pts), np.nan, dtype=float)

    if len(grid_lon) == 0:
        return np.full(len(lon_pts), np.nan, dtype=float)

    # Filter out non-finite (NaN/Inf) values from the grid data
    m = _finite_mask(grid_lon, grid_lat, grid_val_ln)
    if not np.any(m):
        _die("IDW: no finite grid points after filtering.")
        return np.full(len(lon_pts), np.nan, dtype=float)

    # Apply the mask to keep only valid grid points
    grid_lon = grid_lon[m]
    grid_lat = grid_lat[m]
    grid_val_ln = grid_val_ln[m]

    # ---------------------------------------------------------
    # 2. Coordinate Projection (EPSG:4326 -> Target Meters)
    # ---------------------------------------------------------
    # Convert degrees to meters for accurate Euclidean distance calculation
    sx, sy = project_lonlat_to_xy(lon_pts, lat_pts)
    gx, gy = project_lonlat_to_xy(grid_lon, grid_lat)

    # Identify valid substation coordinates (finite x, y)
    finite_sub = _finite_mask(sx, sy)

    # If all substations have invalid coordinates, return all NaNs immediately
    if not np.any(finite_sub):
        return np.full(len(lon_pts), np.nan, dtype=float)

    # ---------------------------------------------------------
    # 3. Spatial Indexing (KDTree Construction)
    # ---------------------------------------------------------
    # Stack coordinates into (N, 2) arrays for the tree
    grid_coords = np.column_stack((gx, gy))
    sub_coords = np.column_stack((sx, sy))

    # Build the KDTree from grid points. 
    # This enables fast O(log M) nearest-neighbor lookups.
    tree = cKDTree(grid_coords)

    # ---------------------------------------------------------
    # 4. Nearest Neighbor Query
    # ---------------------------------------------------------
    # Query the tree for the 'k' nearest neighbors within 'radius_m'.
    # - workers=-1: Use all available CPU cores for parallel processing.
    # - distance_upper_bound: Neighbors further than radius_m are ignored (returned as infinite).
    dists, indices = tree.query(
        sub_coords, 
        k=k, 
        distance_upper_bound=radius_m, 
        workers=-1
    )

    # Initialize the output array with NaNs
    out = np.full(len(lon_pts), np.nan, dtype=float)

    # ---------------------------------------------------------
    # 5. Weight Calculation and Interpolation
    # ---------------------------------------------------------
    # Iterate through each substation to compute the weighted average
    for i in range(len(lon_pts)):
        # Skip invalid substation coordinates
        if not finite_sub[i]:
            continue
            
        # Create a mask for valid neighbors:
        # 1. Distance must be finite (infinite means no neighbor found within radius)
        # 2. Index must be valid (cKDTree returns len(data) for missing neighbors)
        valid_neighbor_mask = (dists[i] != np.inf) & (indices[i] < len(grid_val_ln))

        # If no valid neighbors found within radius, result remains NaN
        if not np.any(valid_neighbor_mask):
            continue

        # Extract valid distances and values
        d_local = dists[i][valid_neighbor_mask]
        idx_local = indices[i][valid_neighbor_mask]
        v_local = grid_val_ln[idx_local]

        # Handle exact coordinate matches (distance ~ 0) to avoid division by zero.
        # If the substation is exactly on a grid point, use that point's value directly.
        if np.any(d_local <= 1e-9):
            out[i] = v_local[d_local <= 1e-9][0]
            continue

        # Standard IDW formula: weight = 1 / distance^power
        w = 1.0 / np.power(d_local, power)
        
        # Compute weighted average: sum(w * v) / sum(w)
        out[i] = np.sum(w * v_local) / np.sum(w)

    return out

# ================= Grid loaders =================
def load_covjson(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Read CovJSON grid.
    Returns (lon, lat, ln(g)).
    """
    if not os.path.exists(path):
        _die(f"CovJSON not found: {path}")
        return None, None, None

    with open(path, "r", encoding="utf-8") as f:
        cov = json.load(f)

    # Axes (assumed x=lon, y=lat)
    try:
        x = cov["domain"]["axes"]["x"]
        y = cov["domain"]["axes"]["y"]
        x_num = int(x["num"])
        y_num = int(y["num"])
        xs = np.linspace(float(x["start"]), float(x["stop"]), x_num)
        ys = np.linspace(float(y["start"]), float(y["stop"]), y_num)
    except Exception as e:
        _die(f"CovJSON axis parse failed for {path}: {e}")
        return None, None, None

    ranges = cov.get("ranges", {})
    if "PGA" in ranges:
        rkey = "PGA"
    elif len(ranges) == 1:
        rkey = next(iter(ranges.keys()))
        _warn(f"CovJSON ranges key is '{rkey}', not 'PGA'. Using it.")
    else:
        _die(f"CovJSON has no 'PGA' range and multiple ranges: {list(ranges.keys())}")
        return None, None, None

    r = ranges[rkey]
    vals = np.array(r.get("values", []), dtype=float)
    if vals.size == 0:
        _die(f"CovJSON has empty values array: {path}")
        return None, None, None

    # Strong shape/axis validation to prevent silent transpose/reshape errors
    axis_names = r.get("axisNames", None)
    shape = r.get("shape", None)
    if axis_names is not None and axis_names != ["y", "x"]:
        _die(f"CovJSON axisNames unexpected: {axis_names} (expected ['y','x'])")
        return None, None, None
    if shape is not None and (int(shape[0]) != y_num or int(shape[1]) != x_num):
        _die(f"CovJSON shape mismatch: {shape} vs expected {[y_num, x_num]}")
        return None, None, None
    if vals.size != x_num * y_num:
        _die(f"CovJSON values length mismatch: {vals.size} vs expected {x_num * y_num}")
        return None, None, None

    # Decide ln(g) vs g
    mode = COVJSON_VALUES_ARE_LN
    if mode is None:
        mode = covjson_values_are_ln_g(cov, rkey)

    # Flatten grid
    Xg, Yg = np.meshgrid(xs, ys)
    lon = Xg.ravel()
    lat = Yg.ravel()
    vals = vals.ravel()

    if mode:
        vals_ln = vals
    else:
        vals_ln = _safe_log_g(vals, context=f"CovJSON({os.path.basename(path)})")

    return lon, lat, vals_ln

def load_csv_grid(path: str, col_name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Read CSV grid.
    Returns (lon, lat, ln(g)).
    """
    if not os.path.exists(path):
        _die(f"CSV grid not found: {path}")
        return None, None, None

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    if col_name not in df.columns:
        _die(f"CSV grid column '{col_name}' not found. Available (head): {list(df.columns)[:30]}")
        return None, None, None

    lon_col = _pick_col(df.columns, ["lon", "longitude", "long", "x"])
    lat_col = _pick_col(df.columns, ["lat", "latitude", "y"])

    if lon_col is None or lat_col is None:
        _die(f"CSV grid missing lon/lat columns. Found lon_col={lon_col}, lat_col={lat_col}.")
        return None, None, None

    lon = _to_numeric(df[lon_col])
    lat = _to_numeric(df[lat_col])
    val = _to_numeric(df[col_name])

    m = _finite_mask(lon, lat, val)
    if not np.any(m):
        _die(f"CSV grid has no finite points after parsing: {path}")
        return None, None, None

    lon = lon[m]
    lat = lat[m]
    val = val[m]

    if CSV_VALUES_ARE_LN:
        val_ln = val
    else:
        val_ln = _safe_log_g(val, context=f"CSV({os.path.basename(path)}:{col_name})")

    return lon, lat, val_ln

# ================= Main =================
def main(cfg: IDWConfig | None = None) -> None:
    cfg = cfg if cfg is not None else IDWConfig()

    print(f"1) Loading substations: {cfg.sub_csv}")
    if not os.path.exists(cfg.sub_csv):
        _die(f"Substation CSV not found: {cfg.sub_csv}")

    subs = pd.read_csv(cfg.sub_csv)
    subs.columns = subs.columns.str.strip()

    # Ensure ID
    if "id" not in subs.columns:
        id_col = _pick_col(subs.columns, ["hifld_id", "substation_id", "objectid"])
        if id_col is not None:
            subs["id"] = subs[id_col].astype(str)
    if "id" not in subs.columns:
        _die("Substation table has no 'id' and no fallback ID column was found.")
    subs["id"] = subs["id"].astype(str)

    # Coordinate columns
    lat_col = _pick_col(subs.columns, ["lat", "latitude", "y"])
    lon_col = _pick_col(subs.columns, ["lon", "longitude", "x", "long"])
    if lat_col is None or lon_col is None:
        _die(f"Substation table missing lat/lon columns. Found lat_col={lat_col}, lon_col={lon_col}.")

    sub_lons = pd.to_numeric(subs[lon_col], errors="coerce").to_numpy(dtype=float)
    sub_lats = pd.to_numeric(subs[lat_col], errors="coerce").to_numpy(dtype=float)

    # Output container
    result_df = subs[["id"]].copy()

    print(f"2) Scenarios: {len(cfg.scenarios)}")
    for name, (ftype, path, col) in cfg.scenarios.items():
        print(f"\n--- Scenario: {name} ({ftype}) ---")
        if ftype == "json":
            glon, glat, gln = load_covjson(path)
        elif ftype == "csv":
            glon, glat, gln = load_csv_grid(path, col)
        else:
            _die(f"Unknown scenario file type: {ftype}")

        interp_ln = idw_core(sub_lons, sub_lats, glon, glat, gln)
        interp_g = np.exp(interp_ln)

        n_nan = int(np.sum(~np.isfinite(interp_g)))
        if n_nan > 0:
            _warn(f"{name}: {n_nan}/{len(interp_g)} substations have NaN PGA (coverage/load issue).")
            if FAIL_FAST:
                _die(f"{name}: NaN PGA encountered under FAIL_FAST. Fix coverage/data first.")

        # Keep both columns if downstream expects them
        result_df[f"PGA_{name}"] = interp_g

        finite = interp_g[np.isfinite(interp_g)]
        if finite.size > 0:
            print(f"  stats: min={finite.min():.4g}g, p50={np.median(finite):.4g}g, max={finite.max():.4g}g")

    print(f"\n3) Merging and writing: {cfg.final_output_csv}")

    final_df = pd.read_csv(cfg.sub_csv)
    final_df.columns = final_df.columns.str.strip()

    if "id" not in final_df.columns:
        final_df = subs.copy()

    final_df["id"] = final_df["id"].astype(str)

    # Drop old PGA_* columns to avoid stale duplicates
    cols_to_drop = [c for c in final_df.columns if c.startswith("PGA_")]
    if cols_to_drop:
        final_df.drop(columns=cols_to_drop, inplace=True)

    final_df = pd.merge(final_df, result_df, on="id", how="left")
    final_df.to_csv(cfg.final_output_csv, index=False)

    print("OK: finished writing output.")


if __name__ == "__main__":
    raise SystemExit(
        "IDW.py is the shared implementation; "
        "run IDW_expanded.py for the manuscript workflow."
    )
