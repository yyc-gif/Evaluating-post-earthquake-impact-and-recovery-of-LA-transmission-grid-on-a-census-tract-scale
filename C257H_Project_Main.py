# ==========================================================================
# [PART 1] Environment Setup, Configuration & Logging
# =============================================================================
# Contains: Imports, Runtime guards, Config dataclass, Logging setup, Path helpers
# --- Runtime environment guards (keep behavior identical) --------------------
import os as _os
import sys as _sys

_os.environ.setdefault("OMP_NUM_THREADS", "13")
_os.environ.setdefault("LOKY_MAX_CPU_COUNT", "13")

try:
    if hasattr(_sys.stdout, "reconfigure"):
        _sys.stdout.reconfigure(encoding="utf-8")
    _os.environ.setdefault("PYTHONIOENCODING", "utf-8")
except Exception:
    pass

"""
This script implements a full-stack evaluation of earthquake impacts on the
LA power grid. It covers:

- Stage 0:   Data Loading & Weight Matrix (W) Construction
- Stage 1:   Monte Carlo Fragility Sampling & Damage Propagation
- Stage 2:   Static Graph Criticality & Percolation
- Stage 3:   Dynamic Step-Recovery Simulation (MC Mean)
- Stage 4:   Rule-Based Scheduling Baselines
- Stage 5:   GA-Based Scheduling Optimization
- Stage 6:   Consolidation, KPI Calculation & Plotting
- Stage 7:   Tract-Level Typology (PCA + K-Means)
"""

# --- Standard library imports -------------------------------------------------
import logging
import math
import os
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --- Third-party imports ------------------------------------------------------
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from geopy.distance import geodesic
from joblib import Parallel, delayed
from scipy.stats import lognorm
from shapely.geometry import Point
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler

# 
from scipy.spatial import cKDTree
from shapely import wkt
from shapely.geometry import Point, LineString, MultiPoint, MultiLineString, box
from shapely.ops import split, snap
import random
from deap import base, creator, tools, algorithms

# Configure Matplotlib for headless environments (kept in-place)
matplotlib.use("Agg")

# =========================
# Project paths (portable)
# =========================
# Project root is the directory containing this script.
PROJECT_ROOT = Path(__file__).resolve().parent

# All input files are stored under ./Data.
DATA_DIR = PROJECT_ROOT / "Data"

# Outputs are written under the project root by default (Stage X Output folders).
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT
OUTPUT_ROOT = str(DEFAULT_OUTPUT_ROOT)

# === Enforce stepwise I/O helpers =============================================
def stage_dir(stage: str) -> str:
    return os.path.join(OUTPUT_ROOT, f"Stage {stage} Output")

def stage_file(stage: str, filename: str) -> str:
    return os.path.join(stage_dir(stage), filename)

# ==============================================================================
@dataclass
class Config:
    """Configuration dataclass for the entire pipeline."""

    # =========================================================================
    DEVICES_CSV: str = str(DATA_DIR / "LA_Substations_WithFragility_UPDATED_CEC.csv")
    PGA_CSV: str = str(DATA_DIR / "Substations_PGA_IDW_CEC.csv")
    MAP_TRACT_SUB_CSV: str = str(DATA_DIR / "tract_to_substation_mapping_CEC.csv")
    CEC_GRAPH_EDGES_CSV: str = str(DATA_DIR / "substation_graph_CEC_edges.csv")
    CEC_GRAPH_NODES_CSV: str = str(DATA_DIR / "substation_graph_CEC_nodes.csv")
    LA_TRACTS_PATH: str = str(DATA_DIR / "LA_Tracts_With_Population.shp")
    HOSPITAL_TRACTS_CSV: str = str(DATA_DIR / "hospital_with_tract.csv")

    # --- Social Vulnerability Index (tract-level, optional)
    SVI_CSV: str = str(DATA_DIR / "LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv")
    SVI_GEOID_COL: str = "TRACTFIPS"
    SVI_VALUE_COL: str = "SOVI_SCORE"
    SVI_FLOW_WEIGHT: float = 1.0

    # --- Transmission line shapefile (CEC real network)
    TRANSMISSION_LINES_SHP: str = str(DATA_DIR / "TransmissionLine_CEC.shp")
    MAX_LINE_ENDPOINT_DIST_KM: float = 0.5  # Endpoint matching radius

    # --- Travel Time Inputs
    # Precomputed travel times conceptually live with Stage 4.
    TRAVEL_BASE_TO_TASK_CSV: str = stage_file("4", "travel_base_to_task.csv")
    TRAVEL_TASK_TO_TASK_CSV: str = stage_file("4", "travel_task_to_task.csv")


    # =========================================================================
    # OUTPUT DIRS (Relative to output root; follow the staged workflow naming)
    # =========================================================================
    STAGE1_DIR: str = "Stage 1 Output"
    STAGE2_DIR: str = "Stage 2 Output"
    STAGE3_DIR: str = "Stage 3 Output"
    STAGE4_DIR: str = "Stage 4 Output"
    STAGE5_DIR: str = "Stage 5 Output"
    STAGE6_DIR: str = "Stage 6 Output"
    STAGE7_DIR: str = "Stage 7 Output"
    SCHEDULE_DIR: str = "schedules"  # Subdirectory for GA runs

    # =========================================================================
    # RUNTIME PARAMETERS
    # =========================================================================
    SCENARIOS: tuple = ("Northridge", "SanFernando", "LongBeach")
    TIME_END_HR: float = 480
    SUPPLY_THRESH: float = 0.8
    DT_HR: float = 1.0
    N_MC: int = 1000  # Number of MC samples per scenario
    UNDAMAGED_EPS_HR: float = 0.5     # Treat repair time <= eps as undamaged
    FUNCTIONAL_THRESHOLD: float = 0.5  # Substation functional if value >= threshold
    GA_EXTRA_EVAL_HR: float = 24.0     # Extra horizon used in GA evaluation
    RNG_SEED: int = 42
    N_CREWS: int = 135  # 7 bases * 3 crews
    N_CORES: int = -1  # Use all available cores for Joblib
    K_NEIGHBORS: int = 5  # Fallback k for KNN graph

    # --- GA Parameters
    GA_POP_SIZE: int = 100
    GA_N_GEN: int = 50
    GA_CXPB: float = 0.8
    GA_MUTPB: float = 0.2
    GA_N_RUNS: int = 3
    W_POP: float = 1.0
    W_HOSP: float = 20.0
    W_MAKESPAN: float = 0.05

    # --- Toggle Stages
    RUN_STAGE_1: bool = True
    RUN_STAGE_2: bool = True
    RUN_STAGE_3: bool = True
    RUN_STAGE_4: bool = True
    RUN_STAGE_5: bool = True
    RUN_STAGE_6: bool = True
    RUN_STAGE_7: bool = True

    # --- Crew Bases
    CREW_BASES: list = field(
        default_factory=lambda: [
            ("West LA Yard", 34.0453, -118.4536),
            ("Western Yard", 34.0455, -118.3615),
            ("Central Yard", 34.0375, -118.2555),
            ("Wilmington Yard", 33.7731, -118.2633),
            ("Van Nuys Yard", 34.1876, -118.4497),
            ("Sun Valley Yard", 34.2318, -118.3817),
            ("South LA Yard", 33.9813, -118.2920),
        ]
    )

def setup_logging(log_file: Path) -> logging.Logger:
    """
    Configure root logging to both a file and stdout.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers to prevent duplicate output across re-runs.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # File handler (overwrite each run).
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    # Console handler (stdout).
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
    logger.addHandler(console_handler)

    logging.info("Logging initialized.")

    # Reduce verbosity from common dependencies.
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

    # Silence a known GeoPandas/pyogrio warning pattern.
    warnings.filterwarnings("ignore", "Sequential read of iterator", UserWarning)

    return logger


def make_out_dirs(cfg: Config) -> Dict[str, Path]:
    """
    Create and validate the output directory structure.

    Notes:
        This function also updates the module-level OUTPUT_ROOT so that helpers
        (stage_dir / stage_file) remain consistent with the chosen output root.

    Returns:
        paths: A dict mapping directory keys to Path objects, including:
            - ROOT
            - STAGE1_DIR, STAGE2_DIR, STAGE3_DIR, STAGE4_DIR, STAGE5_DIR, STAGE6_DIR, STAGE7_DIR
            - SCHEDULE_DIR (special subdirectory for GA runs)
    """
    logger = logging.getLogger()

    # Select output root.
    root = Path(DEFAULT_OUTPUT_ROOT)
    root.mkdir(parents=True, exist_ok=True)

    # Synchronize global OUTPUT_ROOT used by stage_dir()/stage_file().
    global OUTPUT_ROOT
    OUTPUT_ROOT = str(root)

    dir_keys = [
        "STAGE1_DIR",
        "STAGE2_DIR",
        "STAGE3_DIR",
        "STAGE4_DIR",
        "STAGE5_DIR",
        "STAGE6_DIR",
        "STAGE7_DIR",
    ]

    paths: Dict[str, Path] = {"ROOT": root}

    for key in dir_keys:
        dir_name = getattr(cfg, key)
        dir_path = root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        paths[key] = dir_path
        logger.info(f"Output directory ensured: {dir_path}")

    # Special subdirectory for GA runs.
    sched_dir = paths["STAGE5_DIR"] / cfg.SCHEDULE_DIR
    sched_dir.mkdir(parents=True, exist_ok=True)
    paths["SCHEDULE_DIR"] = sched_dir

    return paths


# --- Repair / functionality parameter tables ---------------------------------
REPAIR_PARAM_LOGNORMAL = {
    # ds: (mean_hr, log_std_dev).
    1: (4.0, 0.5),   # Slight:   ~1 day
    2: (12.0, 0.5),  # Moderate: ~3 days
    3: (24.0, 0.5),  # Extensive: ~7 days
    4: (72.0, 0.5),  # Complete: ~30 days
}

# Capacity multiplier by damage state (DS0 is undamaged).
DS_CAPACITY = {0: 1.0, 1: 0.9, 2: 0.5, 3: 0.1, 4: 0.0}


#  ==========================================================================
# [PART 2] Stage 0: Data Ingestion & Weight Matrix Construction
# =============================================================================
# Contains: Data loaders (devices, PGA, mapping), W matrix builder, run_stage_0
def load_devices(path: str) -> pd.DataFrame:
    """
    Load device/substation inventory and standardize the primary key to column 'id'.

    Priority for ID mapping (if 'id' is missing):
        1) 'HIFLD_ID' (preferred for CEC graph alignment)
        2) 'substation_id'
        3) 'OBJECTID'
    """
    logger = logging.getLogger()

    try:
        devices = pd.read_csv(path)

        if "id" not in devices.columns:
            # 1) Highest priority: HIFLD_ID (matches CEC graph)
            if "HIFLD_ID" in devices.columns:
                devices["id"] = devices["HIFLD_ID"].astype(str)
                logger.info("Using 'HIFLD_ID' as primary device key.")

            # 2) Secondary options
            elif "substation_id" in devices.columns:
                devices = devices.rename(columns={"substation_id": "id"})
            elif "OBJECTID" in devices.columns:
                devices["id"] = devices["OBJECTID"].astype(str)
            else:
                logger.error(
                    "Devices CSV must have an ID column (HIFLD_ID, substation_id, or OBJECTID)."
                )
                raise KeyError("No usable ID column in devices CSV")

        devices["id"] = devices["id"].astype(str).str.strip()
        return devices

    except FileNotFoundError:
        logger.error(f"FATAL: Devices file not found at {path}")
        raise


def load_pga(path: str, scenarios: list) -> pd.DataFrame:
    """
    Load PGA data for multiple scenarios and standardize columns.

    Compatible column patterns include:
        - pga_<Scenario> (lowercase)
        - PGA_<Scenario>
        - PGA_<Scenario>_IDW
        - <Scenario> (scenario name only)

    Returns:
        DataFrame with standardized columns:
            - id
            - pga_<Scenario> for each scenario in `scenarios`
    """
    logger = logging.getLogger()

    if not _os.path.exists(path):
        logger.error(f"PGA file not found: {path}")
        raise FileNotFoundError(f"PGA file not found: {path}")

    pga = pd.read_csv(path)

    # 1) Auto-detect and standardize the ID column to 'id'.
    if "id" not in pga.columns:
        if "HIFLD_ID" in pga.columns:
            pga["id"] = pga["HIFLD_ID"].astype(str)
            logger.info("load_pga: mapped 'HIFLD_ID' to 'id'")
        elif "substation_id" in pga.columns:
            pga = pga.rename(columns={"substation_id": "id"})
            logger.info("load_pga: mapped 'substation_id' to 'id'")
        elif "OBJECTID" in pga.columns:
            pga["id"] = pga["OBJECTID"].astype(str)
            logger.info("load_pga: mapped 'OBJECTID' to 'id'")
        else:
            logger.error(f"PGA CSV missing ID column. Available: {list(pga.columns)}")
            raise KeyError("PGA CSV must have an ID column.")

    pga["id"] = pga["id"].astype(str).str.strip()

    # 2) Detect scenario columns and standardize them to 'pga_<scenario>'.
    for scen in scenarios:
        col_candidates = [
            f"pga_{scen}", 
            f"PGA_{scen}",      
            f"PGA_{scen}_IDW",  
            scen,               
        ]

        found_col = None
        for c in col_candidates:
            if c in pga.columns:
                found_col = c
                break

        if not found_col:
            logger.error(f"Missing PGA column for '{scen}'. Checked: {col_candidates}")
            logger.error(f"Actual columns in file: {list(pga.columns)}")
            raise KeyError(f"Missing PGA column for {scen}")

        # Standardize into pga_<scenario>.
        target_col = f"pga_{scen}"
        if found_col != target_col:
            pga[target_col] = pga[found_col]

    keep_cols = ["id"] + [f"pga_{s}" for s in scenarios]
    logger.info(f"Loaded PGA data from {path}. Columns standardized.")
    return pga[keep_cols]


def load_mapping(path: str) -> pd.DataFrame:
    """Load tract-to-substation mapping data and standardize key columns."""
    logger = logging.getLogger()

    try:
        mapping = pd.read_csv(path)

        # --- 1) Standardize substation_id ------------------------------------
        if "substation_id" not in mapping.columns:
            if "HIFLD_ID" in mapping.columns:
                logger.info("Mapping: using 'HIFLD_ID' as 'substation_id'.")
                mapping = mapping.rename(columns={"HIFLD_ID": "substation_id"})
            elif "id" in mapping.columns:
                logger.info("Mapping: using 'id' as 'substation_id'.")
                mapping = mapping.rename(columns={"id": "substation_id"})
            else:
                logger.error("Mapping file must contain 'substation_id', 'HIFLD_ID' or 'id'.")
                raise ValueError("No usable substation id column in mapping file.")

        # --- 2) Standardize tract_id ------------------------------------------
        if "tract_id" not in mapping.columns:
            for cand in ["GEOID", "GEOID10", "geoid", "geoid10"]:
                if cand in mapping.columns:
                    logger.info(f"Mapping: using '{cand}' as 'tract_id'.")
                    mapping = mapping.rename(columns={cand: "tract_id"})
                    break

            if "tract_id" not in mapping.columns:
                logger.error("Mapping file must contain 'tract_id' or a GEOID column.")
                raise ValueError("No usable tract id column in mapping file.")

        # --- 3) Clean IDs ------------------------------------------------------
        mapping["substation_id"] = mapping["substation_id"].astype(str).str.strip()
        mapping["tract_id"] = mapping["tract_id"].astype(str).str.strip()
        mapping = mapping.dropna(subset=["substation_id", "tract_id"])

        # --- 4) Standardize weight column -------------------------------------
        if "weight" not in mapping.columns:
            if "share" in mapping.columns:
                logger.info("Mapping file missing 'weight'; using 'share' as 'weight'.")
                mapping = mapping.rename(columns={"share": "weight"})
            else:
                logger.warning("Mapping file missing 'weight' and 'share'; defaulting weight = 1.0.")
                mapping["weight"] = 1.0

        logger.info(f"Loaded mapping: {len(mapping)} rows from {path}")
        return mapping

    except FileNotFoundError:
        logger.error(f"FATAL: Mapping file not found at {path}")
        sys.exit(1)


def build_W_matrix(mapping_df: pd.DataFrame) -> Tuple[np.ndarray, pd.Index, pd.Index]:
    """Return (W, tract_index, sub_index) with row-normalized W."""
    logger = logging.getLogger()

    if "weight" not in mapping_df.columns:
        logger.error("FATAL: Cannot build W matrix. 'weight' column missing from mapping.")
        raise ValueError("Mapping file must have a 'weight' column.")

    logger.info("Building W matrix (tracts x substations)...")

    # Use pivot_table to handle duplicate (tract_id, substation_id) pairs via summation.
    W_df = (
        mapping_df.pivot_table(
            index="tract_id",
            columns="substation_id",
            values="weight",
            aggfunc="sum",
        )
        .fillna(0.0)
    )

    W_df.index = W_df.index.astype(str).str.strip()
    W_df.columns = W_df.columns.astype(str).str.strip()

    tract_index = W_df.index
    sub_index = W_df.columns
    W_mat = W_df.values

    # --- Row normalization (per spec) ----------------------------------------
    row_sums = W_mat.sum(axis=1)

    # Log tracts with poor normalization (e.g., incomplete shares).
    under_normalized = row_sums < 0.99
    if np.any(under_normalized):
        n_under = under_normalized.sum()
        logger.warning(
            f"{n_under} tracts have row sums < 0.99. "
            f"Mean sum for them: {row_sums[under_normalized].mean():.2f}"
        )

    # Avoid division by zero for tracts with no linked substations.
    W_norm = W_mat.copy()
    valid_rows = row_sums > 0
    W_norm[valid_rows] = W_norm[valid_rows] / row_sums[valid_rows, np.newaxis]

    logger.info(
        "W matrix built. Shape: (N_tracts: %d, N_subs: %d)",
        W_norm.shape[0],
        W_norm.shape[1],
    )

    return W_norm, tract_index, sub_index


def run_stage_0(cfg: Config) -> Dict[str, Any]:
    """Orchestrate Stage 0: load datasets, merge device + PGA, and build W."""
    logger = logging.getLogger()

    logger.info("=" * 50)
    logger.info("--- STAGE 0: Load & Build ---")

    # --- 1) Load inputs -------------------------------------------------------
    devices = load_devices(cfg.DEVICES_CSV)
    pga = load_pga(cfg.PGA_CSV, cfg.SCENARIOS)
    mapping = load_mapping(cfg.MAP_TRACT_SUB_CSV)

    # --- 2) Sanitize and (re-)ensure 'id' columns ---
    # Devices table: strip column-name whitespace, then ensure 'id' exists.
    devices.columns = [c.strip() for c in devices.columns]
    if "id" not in devices.columns:
        candidates = ["HIFLD_ID", "substation_id", "OBJECTID"]
        found = next((c for c in candidates if c in devices.columns), None)
        if found:
            devices["id"] = devices[found].astype(str)
        else:
            logger.error(f"Devices columns: {list(devices.columns)}")
            raise KeyError("Devices DF missing 'id' column before merge.")

    # PGA table: strip column-name whitespace, then ensure 'id' exists.
    pga.columns = [c.strip() for c in pga.columns]
    if "id" not in pga.columns:
        # load_pga() should already standardize this; this is a second layer of defense.
        logger.error(f"PGA columns: {list(pga.columns)}")
        if pga.index.name == "id":
            pga = pga.reset_index()
        else:
            raise KeyError("PGA DF missing 'id' column before merge.")

    # Ensure IDs are clean strings for merge alignment.
    devices["id"] = devices["id"].astype(str).str.strip()
    pga["id"] = pga["id"].astype(str).str.strip()

    # --- 3) Merge devices with PGA --------------------------------------------
    try:
        devices_merged = devices.merge(pga, on="id", how="left")
    except Exception as e:
        logger.error(f"Merge failed. Devices head: {devices[['id']].head()}")
        logger.error(f"PGA head: {pga[['id']].head()}")
        raise e

    # Ensure all expected PGA columns exist; fill missing with 0.0.
    pga_cols = [f"pga_{scen}" for scen in cfg.SCENARIOS]

    missing_cols = [c for c in pga_cols if c not in devices_merged.columns]
    if missing_cols:
        logger.warning(f"Missing PGA columns after merge: {missing_cols}. Filling with 0.")
        for c in missing_cols:
            devices_merged[c] = 0.0

    devices_merged[pga_cols] = devices_merged[pga_cols].fillna(0.0)
    logger.info(f"Merged devices + PGA: {len(devices_merged)} rows.")

    # --- 4) Build W matrix -----------------------------------------------------
    W_mat, tract_index, sub_index = build_W_matrix(mapping)

    # --- 5) Align device rows to sub_index ordering ---------------------------
    sub_index_str = [str(s).strip() for s in sub_index]

    devices_merged = devices_merged.set_index("id")
    devices_merged = devices_merged.reindex(sub_index_str)
    devices_merged.index.name = "id"
    devices_merged = devices_merged.reset_index()

    # --- 6) Defensive numeric conversion for coordinates ----------------------
    for col in ["lat", "lon"]:
        if col in devices_merged.columns:
            devices_merged[col] = (
                pd.to_numeric(devices_merged[col].fillna(0.0), errors="coerce")
                .fillna(0.0)
            )

    devices_merged = devices_merged.fillna(0.0)

    # Ensure 'id' exists as a column after reindex/reset (defensive).
    if "id" not in devices_merged.columns:
        devices_merged["id"] = devices_merged.index.astype(str)

    logger.info(f"Devices aligned. Count: {len(devices_merged)}")
    logger.info("--- STAGE 0 Complete ---")

    return {
        "devices_merged": devices_merged,
        "mapping_df": mapping,
        "W_mat": W_mat,
        "tract_index": tract_index,
        "sub_index": sub_index,
    }


# ==========================================================================
# [PART 3] Stage 1: Monte Carlo Fragility & Damage Simulation
# =============================================================================
# Contains: Fragility functions (lognorm), MC sampling logic, run_stage_1 (MC engine)
def sample_damage_states(
    pga_series: pd.Series,
    devices_df: pd.DataFrame,
    n_mc: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Sample Monte Carlo damage states (DS = 0..4) for each substation given PGA and
    lognormal fragility parameters.
    """
    logger = logging.getLogger()

    n_devices = len(devices_df)
    pga_vals = pga_series.values

    if len(pga_vals) != n_devices:
        raise ValueError(
            "sample_damage_states: PGA series length "
            f"{len(pga_vals)} != devices_df length {n_devices}"
        )

    # 1) Extract mu and beta arrays
    try:
        mu_mat = devices_df[[f"mu_DS{ds}" for ds in range(1, 5)]].values.astype(float)
        betas = devices_df[[f"beta_DS{ds}" for ds in range(1, 5)]].values.astype(float)
    except KeyError as e:
        logger.error(f"Missing fragility columns: {e}")
        raise

    # 2) SciPy lognorm convention: scale = exp(mu)
    scales = np.exp(mu_mat)

    # 3) Numerical cleanup to avoid invalid parameters
    scales = np.clip(scales, 1e-6, None)
    betas = np.clip(betas, 1e-4, None)

    # 4) Compute exceedance probabilities: P(DS >= j | PGA) = CDF_lognormal(PGA; mu_j, beta_j)
    pga_vals_broad = pga_vals.reshape(-1, 1)  # (n_devices, 1)
    p_exc = lognorm.cdf(pga_vals_broad, s=betas, scale=scales)  # (n_devices, 4)

    # Replace NaN/inf to keep probabilities well-defined downstream
    p_exc = np.nan_to_num(p_exc, nan=0.0, posinf=1.0, neginf=0.0)

    # 5) Convert exceedance probabilities into state probabilities P(DS = j)
    p_ds = np.empty((n_devices, 5), dtype=float)
    p_ds[:, 0] = 1.0 - p_exc[:, 0]          # DS0
    p_ds[:, 1] = p_exc[:, 0] - p_exc[:, 1]  # DS1
    p_ds[:, 2] = p_exc[:, 1] - p_exc[:, 2]  # DS2
    p_ds[:, 3] = p_exc[:, 2] - p_exc[:, 3]  # DS3
    p_ds[:, 4] = p_exc[:, 3]                # DS4

    # Clamp and renormalize to correct for numerical drift
    p_ds = np.clip(p_ds, 0.0, 1.0)
    row_sums = p_ds.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0.0] = 1.0
    p_ds /= row_sums

    # 6) Row-wise sampling via inverse CDF on cumulative probabilities
    cum_probs = np.cumsum(p_ds, axis=1)  # (n_devices, 5)
    r = rng.random((n_devices, n_mc))    # (n_devices, n_mc), uniform in [0, 1)

    # For each (device, sample), pick the first DS with cum_prob > r
    ds_samples = (r[..., np.newaxis] < cum_probs[:, np.newaxis, :]).argmax(axis=2)

    return ds_samples.astype(int)


def damage_to_functionality_and_repair(
    ds_samples: np.ndarray,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Map sampled damage states to:
        (1) initial functionality (capacity multiplier)
        (2) stochastic repair time samples (hours), sampled from LogNormal parameters

    Repair-time parameterization:
        REPAIR_PARAM_LOGNORMAL[ds] = (mean_hr, sigma).
        SciPy lognorm uses s=sigma and scale=exp(mu) (= median), where:
            mean = exp(mu + 0.5*sigma^2)
        Therefore:
            mu = ln(mean_hr) - 0.5*sigma^2
            scale = exp(mu)
    """
    logger = logging.getLogger()

    # 1) Map to initial functionality
    v_func = np.vectorize(DS_CAPACITY.get)
    func0_samples = v_func(ds_samples)

    # 2) Map to repair times
    repair_time_samples = np.zeros_like(ds_samples, dtype=float)

    for ds in range(1, 5):
        mask = ds_samples == ds
        try:
            n_samples_ds = int(mask.sum())
            if n_samples_ds <= 0:
                continue

            params = REPAIR_PARAM_LOGNORMAL.get(ds, (12.0, 0.5))
            mean_hr, sigma = params

            # Guard against non-positive or degenerate parameters
            mean_hr = max(float(mean_hr), 1e-6)
            sigma = max(float(sigma), 1e-6)

            # Convert mean -> mu so that E[T] = mean_hr
            mu = np.log(mean_hr) - 0.5 * (sigma ** 2)

            # SciPy lognorm: scale = exp(mu) = median
            scale = np.exp(mu)

            repair_time_samples[mask] = lognorm(s=sigma, scale=scale).rvs(
                size=n_samples_ds,
                random_state=rng,
            )

        except Exception as e:
            logger.error(f"Error sampling repair time for DS={ds}: {e}")
            # Fallback: use the mean directly (consistent with parameter-table semantics)
            repair_time_samples[mask] = float(REPAIR_PARAM_LOGNORMAL.get(ds, (12.0, 0.5))[0])

    return func0_samples, repair_time_samples                                                                                                                                                                                                                                                                                                                                                                    


# ==============================================================================
# Substation ID normalization utilities
# ==============================================================================
SUBSTATION_ID_CANON_COL = "substation_id"
SUBSTATION_ID_SOURCE_COLS = ["substation_id", "HIFLD_ID", "id"]


def ensure_substation_id_col(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure df contains a canonical 'substation_id' column.

    Priority:
        1) existing 'substation_id'
        2) 'HIFLD_ID'
        3) 'id'

    Behavior:
        - Copies the first available source column into 'substation_id'
        - Casts to string and strips whitespace
    """
    for col in SUBSTATION_ID_SOURCE_COLS:
        if col in df.columns:
            df[SUBSTATION_ID_CANON_COL] = df[col].astype(str).str.strip()
            return df

    raise KeyError(
        "No usable substation ID column found in devices_df. "
        f"Tried {SUBSTATION_ID_SOURCE_COLS}; available columns: {df.columns.tolist()}"
    )


def get_substation_id_array(df: pd.DataFrame) -> np.ndarray:
    """Return the standardized 'substation_id' array (string dtype)."""
    df = ensure_substation_id_col(df)
    return df[SUBSTATION_ID_CANON_COL].values


def _process_mc_chunk(
    scenario,
    pga_series,
    devices_df,
    W_mat,
    tract_index,
    n_chunk,
    rng_seed,
):
    """Helper function for parallel MC processing."""
    rng = np.random.default_rng(rng_seed)
    n_devices = len(devices_df)
    n_tracts = len(tract_index)

    # --- Generate samples for this chunk --------------------------------------
    ds_samples = sample_damage_states(pga_series, devices_df, n_chunk, rng)
    func0_samples, repair_time_samples = damage_to_functionality_and_repair(ds_samples, rng)

    # --- Device-level aggregation ---------------------------------------------
    # Return mean DS (not all samples) to reduce memory usage
    ds_avg_chunk = ds_samples.mean(axis=1)

    # --- Tract-level aggregation ----------------------------------------------
    # Project initial functionality to tracts:
    # (n_tracts, n_devices) @ (n_devices, n_chunk) -> (n_tracts, n_chunk)
    S_t_samples = W_mat @ func0_samples

    # Tract outage probability (supply < 40% per the legacy script)
    tract_outage_chunk = (S_t_samples < 0.4).mean(axis=1)

    # Tract average DS (legacy script convention)
    tract_ds_samples = np.digitize(1 - S_t_samples, bins=[0.1, 0.3, 0.6, 1.0])
    tract_avg_ds_chunk = tract_ds_samples.mean(axis=1)

    # --- Records ---------------------------------------------------------------
    # Build long-form device-level MC records
    mc_ids = (
        np.arange(n_chunk, dtype=np.uint32)
        .reshape(1, -1)
        .repeat(n_devices, axis=0)
    )

    # Use standardized substation_id
    sub_ids = get_substation_id_array(devices_df)
    sub_ids_rep = np.repeat(sub_ids.reshape(-1, 1), n_chunk, axis=1)

    device_records_df = pd.DataFrame(
        {
            "scenario": scenario,
            "mc_id": mc_ids.ravel(),
            "substation_id": sub_ids_rep.ravel(),
            "damage_state": ds_samples.ravel(),
            "repair_time_hr": repair_time_samples.ravel(),
        }
    )

    return (
        device_records_df,
        ds_avg_chunk,
        tract_outage_chunk,
        tract_avg_ds_chunk,
        repair_time_samples,
    )


def run_stage_1(cfg: Config, stage_0_data: Dict, out_dirs: Dict) -> Dict:
    """Orchestrate Stage 2 Monte Carlo fragility sampling (Joblib parallel)."""
    if not cfg.RUN_STAGE_1:
        logging.info("--- STAGE 1: Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 1: Fragility Sampling ---")

    # Work on a copy because we may append the canonical 'substation_id' column.
    devices_merged = stage_0_data["devices_merged"].copy()
    devices_merged = ensure_substation_id_col(devices_merged)

    W_mat = stage_0_data["W_mat"]
    tract_index = stage_0_data["tract_index"]

    # Derive sub_index from the canonical substation_id.
    sub_index = pd.Index(
        devices_merged["substation_id"].astype(str),
        name="substation_id",
    )

    # Determine parallelism
    n_cores = (os.cpu_count() or 1) if cfg.N_CORES == -1 else max(1, cfg.N_CORES)
    n_workers = min(n_cores, cfg.N_MC)
    logger.info(f"Running {cfg.N_MC} MC simulations across {n_workers} workers...")

    # Distribute N_MC evenly across workers; add +1 to the first `rem` workers.
    base = cfg.N_MC // n_workers
    rem = cfg.N_MC % n_workers
    chunks = [base + (1 if i < rem else 0) for i in range(n_workers)]

    # Create deterministic seeds per worker chunk
    base_rng = np.random.default_rng(cfg.RNG_SEED)
    chunk_seeds = base_rng.integers(low=1, high=2**31, size=n_workers)

    all_mc_repair_times = {}  # For Stage 3

    for scenario in cfg.SCENARIOS:
        logger.info(f"Processing scenario: {scenario}...")

        pga_col = f"pga_{scenario}"
        pga_series = devices_merged[pga_col]

        pga_stats = pga_series.describe()
        logger.info(
            f"PGA statistics for {scenario}: "
            f"mean={pga_stats['mean']:.2f}, "
            f"std={pga_stats['std']:.2f}, "
            f"max={pga_stats['max']:.2f}"
        )

        # Run per-chunk MC in parallel
        results = Parallel(n_jobs=n_workers)(
            delayed(_process_mc_chunk)(
                scenario,
                pga_series,
                devices_merged,
                W_mat,
                tract_index,
                n_chunk,
                seed,
            )
            for n_chunk, seed in zip(chunks, chunk_seeds)
        )

        # --- Unpack and aggregate chunk results --------------------------------
        device_records_list = [r[0] for r in results]

        ds_avg_chunks = np.stack([r[1] for r in results], axis=1)
        tract_outage_chunks = np.stack([r[2] for r in results], axis=1)
        tract_avg_ds_chunks = np.stack([r[3] for r in results], axis=1)

        repair_time_chunks = [r[4] for r in results]  # list of (n_devices, n_chunk)

        # --- 1) MC_Device_Damage_Records_<scenario>.csv.gz ----------------------
        device_records_df = pd.concat(device_records_list, ignore_index=True)

        # Re-assign mc_id to be contiguous (per substation_id)
        device_records_df["mc_id"] = device_records_df.groupby(["substation_id"]).cumcount()

        # Storage optimizations
        device_records_df["substation_id"] = device_records_df["substation_id"].astype("category")
        if device_records_df["mc_id"].max() < 65535:
            device_records_df["mc_id"] = device_records_df["mc_id"].astype("uint16")

        out_path = out_dirs["STAGE1_DIR"] / f"MC_Device_Damage_Records_{scenario}.csv.gz"
        device_records_df.to_csv(out_path, index=False, compression="gzip")
        logger.info(f"Saved device records: {out_path}")

        # Free memory
        del device_records_df, device_records_list

        # --- 2) MC_Device_Damage_AvgDS_<scenario>.csv ---------------------------
        # Aggregate: (n_devices, n_chunks) -> (n_devices,)
        weights = np.array(chunks) / cfg.N_MC
        device_avg_ds = np.average(ds_avg_chunks, axis=1, weights=weights)

        df_dev_avg = pd.DataFrame(
            {
                "substation_id": sub_index, 
                "scenario": scenario,
                "avg_damage_state": device_avg_ds,
            }
        )

        out_path = out_dirs["STAGE1_DIR"] / f"MC_Device_Damage_AvgDS_{scenario}.csv"
        df_dev_avg.to_csv(out_path, index=False)

        # --- 3) MC_TractAvgDS_<scenario>.csv -----------------------------------
        tract_avg_ds = np.average(tract_avg_ds_chunks, axis=1, weights=weights)
        df_tract_avg = pd.DataFrame(
            {
                "tract_id": tract_index,
                "scenario": scenario,
                "tract_avg_damage_state": tract_avg_ds,
            }
        )

        out_path = out_dirs["STAGE1_DIR"] / f"MC_TractAvgDS_{scenario}.csv"
        df_tract_avg.to_csv(out_path, index=False)

        # --- 4) MC_TractOutage_Prob_<scenario>.csv ------------------------------
        tract_outage_prob = np.average(tract_outage_chunks, axis=1, weights=weights)
        df_tract_outage = pd.DataFrame(
            {
                "tract_id": tract_index,
                "scenario": scenario,
                "peak_outage_prob": tract_outage_prob,
            }
        )

        out_path = out_dirs["STAGE1_DIR"] / f"MC_TractOutage_Prob_{scenario}.csv"
        df_tract_outage.to_csv(out_path, index=False)

        # --- 5) Store full repair time samples for Stage 3 ----------------------
        all_mc_repair_times[scenario] = np.concatenate(repair_time_chunks, axis=1)
        logger.info(f"Aggregated results for {scenario}.")

    logger.info("--- STAGE 1 Complete ---")
    return {"all_mc_repair_times": all_mc_repair_times}


# ==========================================================================
# [PART 4] Stage 2: Network Topology & Criticality Analysis
# =============================================================================
# Contains: Graph building, Centrality metrics, Percolation, run_stage_2
def build_base_graph(cfg: Config, devices_df: pd.DataFrame, sub_index: pd.Index) -> nx.Graph:
    """
    Build a NetworkX graph from the CEC edge list CSV, then filter it to match the
    device inventory IDs (sub_index) as strictly as possible.
    """
    logger = logging.getLogger()

    if devices_df.empty or len(sub_index) == 0:
        logger.warning("build_base_graph: devices/sub_index empty; returning empty graph.")
        return nx.Graph()

    edges_path = getattr(cfg, "CEC_GRAPH_EDGES_CSV", "")
    nodes_path = getattr(cfg, "CEC_GRAPH_NODES_CSV", "")

    # --- 0) Load prebuilt CSV graph ------------------------------
    if edges_path and _os.path.exists(edges_path):
        logger.info(f"Loading prebuilt CEC edge list: {edges_path}")
        edf = pd.read_csv(edges_path)

        # 1) Validate required columns
        for c in ["u", "v"]:
            if c not in edf.columns:
                raise ValueError(f"Edge list CSV missing column '{c}': {edges_path}")

        # 2) Standardize edge weight column
        if "length_km" not in edf.columns:
            if "weight" in edf.columns:
                edf = edf.rename(columns={"weight": "length_km"})
            else:
                edf["length_km"] = 1.0

        edf["u"] = edf["u"].astype(str).str.strip()
        edf["v"] = edf["v"].astype(str).str.strip()

        # 3) Build full multigraph
        G_full = nx.from_pandas_edgelist(
            edf,
            source="u",
            target="v",
            edge_attr=["length_km"],
            create_using=nx.MultiGraph(),
        )

        # 4) Filter to device IDs (intersection: in edge list AND in device inventory)
        sub_index_set = {str(s).strip() for s in sub_index}
        valid_nodes = [n for n in G_full.nodes() if n in sub_index_set]
        G = G_full.subgraph(valid_nodes).copy()

        # 5) Add isolated nodes that are in sub_index but absent from the edge list
        for sid in sub_index_set:
            if sid not in G:
                G.add_node(sid)

        # 6) Attach lat/lon node attributes from the nodes CSV
        if nodes_path and _os.path.exists(nodes_path):
            try:
                ndf = pd.read_csv(nodes_path)

                id_col = next((c for c in ["id", "HIFLD_ID", "substation_id"] if c in ndf.columns), None)
                lat_col = next((c for c in ["lat", "Latitude", "Lat"] if c in ndf.columns), None)
                lon_col = next((c for c in ["lon", "Longitude", "Lon"] if c in ndf.columns), None)

                if id_col and lat_col and lon_col:
                    # Sanitize IDs in node table, then index by ID
                    ndf[id_col] = ndf[id_col].astype(str).str.strip()
                    ndf = ndf.set_index(id_col)

                    pos_dict = {}
                    for n in G.nodes():
                        if n in ndf.index:
                            pos_dict[n] = {"lat": ndf.at[n, lat_col], "lon": ndf.at[n, lon_col]}

                    nx.set_node_attributes(G, pos_dict)
                    logger.info("Attached lat/lon attributes to graph nodes.")

            except Exception as e:
                logger.warning(f"Failed to attach node attributes: {e}")

        logger.info(
            "Loaded prebuilt CEC graph for Stage 2: %d nodes, %d edges from %s",
            G.number_of_nodes(),
            G.number_of_edges(),
            edges_path,
        )
        return G

    logger.warning(f"Prebuilt CEC edge list not found at {edges_path}. Returning empty graph.")
    return nx.Graph()


def _algebraic_connectivity(G: nx.Graph) -> float:
    """
    Compute the algebraic connectivity (λ2) of a graph.

    Notes:
        - If G is a MultiGraph, it is first collapsed into a simple Graph
          (parallel edges are ignored).
        - Returns 0.0 for graphs with <= 1 node or when λ2 is not defined.
    """
    # MultiGraph -> Graph (ignore parallel edges)
    if isinstance(G, nx.MultiGraph):
        H = nx.Graph()
        H.add_nodes_from(G.nodes())
        for u, v in G.edges():
            H.add_edge(u, v)
        G = H

    n = G.number_of_nodes()
    if n <= 1:
        return 0.0

    nodes = list(G.nodes())

    # Build adjacency matrix A and Laplacian L = D - A
    A = nx.to_numpy_array(G, nodelist=nodes, dtype=float)
    deg = A.sum(axis=1)
    L = np.diag(deg) - A

    # L is symmetric, so eigvalsh is appropriate
    eigvals = np.linalg.eigvalsh(L)
    eigvals.sort()

    # Algebraic connectivity = 2nd-smallest eigenvalue
    if len(eigvals) < 2:
        return 0.0
    return float(eigvals[1])


def compute_impact_centrality(G: nx.Graph) -> pd.Series:
    """
    Impact Centrality (algebraic-connectivity based):

    For each node v:
        - Compute λ2_base on the initial largest connected component (LCC)
        - Remove v and compute λ2_new on the modified graph
        - Impact(v) = (λ2_base - λ2_new) / λ2_base  (clipped to >= 0)

    Nodes outside the initial LCC receive Impact = 0.0.
    """
    logger = logging.getLogger()

    if G.number_of_nodes() == 0:
        return pd.Series(dtype=float)

    try:
        initial_lcc_nodes = max(nx.connected_components(G), key=len)
    except ValueError:
        return pd.Series(dtype=float)

    initial_lcc_nodes = set(initial_lcc_nodes)
    G0 = G.subgraph(initial_lcc_nodes).copy()

    lambda2_base = _algebraic_connectivity(G0)
    if lambda2_base <= 0:
        logger.warning(
            "Base algebraic connectivity λ2 == 0; "
            "impact is undefined. Returning all zeros."
        )
        return pd.Series(0.0, index=list(G.nodes()), name="impact_centrality")

    logger.info(
        "Computing algebraic-connectivity-based Impact Centrality for %d nodes... "
        "(Base lambda2 = %.4f)",
        len(G),
        lambda2_base,
    )

    impact_c: Dict[Any, float] = {}
    critical_count = 0

    for node in list(G.nodes()):
        # Nodes outside the initial LCC do not affect the main network island
        if node not in initial_lcc_nodes:
            impact_c[node] = 0.0
            continue

        # Work on a copy of the LCC subgraph
        G_copy = G0.copy()
        if node not in G_copy:
            impact_c[node] = 0.0
            continue

        G_copy.remove_node(node)

        if G_copy.number_of_nodes() <= 1:
            lambda2_new = 0.0
        else:
            lambda2_new = _algebraic_connectivity(G_copy)

        diff = max(lambda2_base - lambda2_new, 0.0)
        impact_val = diff / max(lambda2_base, 1e-9)
        impact_c[node] = impact_val

        if diff > 1e-6:
            critical_count += 1

    logger.info(
        "Computed algebraic-connectivity impact centrality. "
        "Found %d structurally critical nodes (lambda2 loss > 0).",
        critical_count,
    )

    return pd.Series(impact_c, name="impact_centrality")


def compute_population_impact(G: nx.Graph, mapping_df: Optional[pd.DataFrame]) -> pd.Series:
    """
    Population-based impact:

        Impact_pop(v) = (population losing supply after removing v) / (total population)

    Assumptions:
        - mapping_df contains: substation_id, tract_id, weight, population
        - Each mapping row represents: "within this tract, a fraction `weight` of the tract
          population is supplied by `substation_id`".

    Implementation detail:
        - Treat the LCC as the "main energized island"; nodes outside it are considered outaged.
    """
    logger = logging.getLogger()
    nodes_all = [str(n) for n in G.nodes()]

    if G.number_of_nodes() == 0:
        return pd.Series(dtype=float, name="impact_population")

    if mapping_df is None:
        logger.warning("compute_population_impact: mapping_df is None; returning zeros.")
        return pd.Series(0.0, index=nodes_all, name="impact_population")

    m = mapping_df.copy()

    if "population" not in m.columns:
        logger.warning(
            "compute_population_impact: mapping_df missing 'population' column; returning zeros."
        )
        return pd.Series(0.0, index=nodes_all, name="impact_population")

    if "weight" not in m.columns:
        logger.warning(
            "compute_population_impact: mapping_df missing 'weight' column; returning zeros."
        )
        return pd.Series(0.0, index=nodes_all, name="impact_population")

    # Sanitize IDs and numeric fields
    m["substation_id"] = m["substation_id"].astype(str).str.strip()
    m["population"] = pd.to_numeric(m["population"], errors="coerce").fillna(0.0)
    m["weight"] = pd.to_numeric(m["weight"], errors="coerce").fillna(0.0)

    # Aggregate weighted population per substation_id
    m["weighted_pop"] = m["population"] * m["weight"]
    pop_per_sub = m.groupby("substation_id")["weighted_pop"].sum()

    # Align to graph nodes
    pop_per_sub = pop_per_sub.reindex(nodes_all, fill_value=0.0)
    total_pop = float(pop_per_sub.sum())

    if total_pop <= 0:
        logger.warning("compute_population_impact: total_pop <= 0; returning zeros.")
        return pd.Series(0.0, index=nodes_all, name="impact_population")

    impact_pop: Dict[str, float] = {}

    for node in nodes_all:
        G_copy = G.copy()
        if node in G_copy:
            G_copy.remove_node(node)

        if G_copy.number_of_nodes() == 0:
            # If nothing remains, treat all population as lost
            lost_pop = total_pop
        else:
            try:
                lcc_nodes = max(nx.connected_components(G_copy), key=len)
            except ValueError:
                lcc_nodes = []

            lcc_set = {str(n) for n in lcc_nodes}

            # Treat the LCC as energized; everything else is considered outaged
            lost_nodes = set(nodes_all) - lcc_set
            lost_pop = float(pop_per_sub.loc[list(lost_nodes)].sum())

        impact_pop[node] = lost_pop / total_pop

    return pd.Series(impact_pop, index=nodes_all, name="impact_population")


def compute_percolation_curves(G: nx.Graph, centrality: pd.Series, out_path: Path):
    """
    Compute a node-removal percolation curve by removing nodes in descending
    centrality order and tracking the size of the largest connected component (LCC).

    Output:
        CSV columns: nodes_removed, lcc_size, lcc_fraction
    """
    logger = logging.getLogger()

    if G.number_of_nodes() == 0 or centrality.empty:
        logger.warning("Skipping percolation curve (empty graph or centrality).")
        return

    nodes_sorted = centrality.sort_values(ascending=False).index

    lcc_sizes: List[int] = []
    G_copy = G.copy()

    try:
        initial_lcc_size = len(max(nx.connected_components(G_copy), key=len))
    except ValueError:
        initial_lcc_size = 0

    lcc_sizes.append(initial_lcc_size)

    for node in nodes_sorted:
        if node not in G_copy:
            continue

        G_copy.remove_node(node)

        if G_copy.number_of_nodes() == 0:
            lcc_sizes.append(0)
            continue

        try:
            lcc = max(nx.connected_components(G_copy), key=len, default=set())
            lcc_sizes.append(len(lcc))
        except ValueError:
            lcc_sizes.append(0)

    denom = initial_lcc_size if initial_lcc_size > 0 else 1

    df = pd.DataFrame(
        {
            "nodes_removed": np.arange(len(lcc_sizes)),
            "lcc_size": lcc_sizes,
            "lcc_fraction": np.array(lcc_sizes) / denom,
        }
    )

    df.to_csv(out_path, index=False)
    logger.info(f"Percolation curve saved to {out_path}")


def run_stage_2(cfg: Config, stage_0_data: Dict, out_dirs: Dict) -> Dict:
    """Orchestrate Stage 2.5: graph criticality metrics and percolation curves."""
    if not cfg.RUN_STAGE_2:
        logging.info("--- STAGE 2: Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 2: Criticality & Percolation ---")

    # Ensure devices_merged has a canonical 'substation_id' column
    devices_merged = stage_0_data["devices_merged"].copy()
    devices_merged = ensure_substation_id_col(devices_merged)

    sub_index = pd.Index(
        devices_merged["substation_id"].astype(str),
        name="substation_id",
    )

    out_dir = out_dirs["STAGE2_DIR"]

    # Use the real CEC transmission network where available.
    G = build_base_graph(cfg, devices_merged, sub_index)

    if G.number_of_nodes() == 0:
        logger.error("Graph build failed. Skipping Stage 2.5.")
        return {}

    # -------------------------------------------------------------------------
    # Centrality metrics
    # -------------------------------------------------------------------------
    degree = pd.Series(dict(G.degree()), name="degree")

    # Betweenness can be expensive; sample if the graph is large.
    k_sample = None
    if G.number_of_nodes() > 1000:
        logger.info(f"Graph is large ({G.number_of_nodes()}), sampling betweenness...")
        k_sample = min(200, G.number_of_nodes())

    betweenness = pd.Series(
        nx.betweenness_centrality(G, k=k_sample, seed=cfg.RNG_SEED),
        name="betweenness_centrality",
    )

    closeness = pd.Series(
        nx.closeness_centrality(G),
        name="closeness_centrality",
    )

    # Structural impact: based on algebraic connectivity (lambda2)
    impact_struct = compute_impact_centrality(G)

    # Population impact: uses mapping_df (population * weight), if available
    mapping_df = stage_0_data.get("mapping_df", None)
    impact_pop = compute_population_impact(G, mapping_df)

    centrality_df = pd.concat(
        [degree, betweenness, closeness, impact_struct, impact_pop],
        axis=1,
    ).fillna(0.0)

    # Align to the standardized sub_index (string HIFLD_ID / substation_id)
    centrality_df = centrality_df.reindex(sub_index).fillna(0.0)

    out_path = out_dir / "impact_centrality_substations.csv"
    centrality_df.to_csv(out_path, index_label="substation_id")
    logger.info(f"Centrality metrics saved to {out_path}")

    # -------------------------------------------------------------------------
    # Percolation curves
    # -------------------------------------------------------------------------

    # 1) Targeted attack: remove nodes in descending lambda2-based impact order
    perc_path = out_dir / "percolation_curve_impact.csv"
    compute_percolation_curves(G, impact_struct, perc_path)

    # 2) Random failure: remove nodes by random ordering (encoded as random scores)
    rng = np.random.default_rng(cfg.RNG_SEED)
    node_list = list(G.nodes())

    random_scores = pd.Series(
        rng.random(len(node_list)),
        index=node_list,
        name="random_score",
    )

    perc_rand_path = out_dir / "percolation_curve_random.csv"
    compute_percolation_curves(G, random_scores, perc_rand_path)

    logger.info("--- STAGE 2 Complete ---")
    return {"centrality_df": centrality_df, "G": G}


# ==========================================================================
# [PART 5] Stage 3: Dynamic Recovery Simulation (Theoretical Limit)
# =============================================================================
# Contains: Step recovery simulation, KPIs (T50/T80), Graph Robustness, run_stage_3
def simulate_step_recovery(
    sub_repair_times: np.ndarray,
    t_grid: np.ndarray,
    sub_index: pd.Index,
) -> pd.DataFrame:
    """
    Build substation step-recovery time series:
        R_sub[i](t) = 1{ t >= repair_time_i }

    Returns:
        DataFrame of shape (n_timesteps, n_substations)
        with index = t_grid and columns = sub_index.
    """
    # (n_timesteps, 1) >= (1, n_substations) -> (n_timesteps, n_substations)
    t_grid_col = t_grid.reshape(-1, 1)
    repair_times_row = sub_repair_times.reshape(1, -1)

    R_sub_mat = (t_grid_col >= repair_times_row).astype(float)
    return pd.DataFrame(R_sub_mat, index=t_grid, columns=sub_index)


def propagate_to_tracts(
    sub_series_df: pd.DataFrame,
    W: np.ndarray,
    tract_index: pd.Index,
) -> pd.DataFrame:
    """
    Propagate substation time series to tracts via W.

    Computes:
        S_tract(t) = W * R_sub(t)

    Where:
        sub_series_df is (n_timesteps, n_substations)
        W is (n_tracts, n_substations)

    Returns:
        DataFrame (n_timesteps, n_tracts) with tract_index columns.
    """
    sub_series_mat = sub_series_df.values  # (n_timesteps, n_substations)

    # (n_timesteps, n_substations) @ (n_substations, n_tracts) -> (n_timesteps, n_tracts)
    S_tract_mat = sub_series_mat @ W.T
    return pd.DataFrame(S_tract_mat, index=sub_series_df.index, columns=tract_index)


def kpis_from_series(series_df: pd.DataFrame, t_end: float) -> pd.DataFrame:
    """
    Compute per-column KPIs from a recovery (or supply) time series.

    KPIs:
        - AUC: normalized area under the recovery curve over [t0, t_end]
        - T50: first time series reaches >= 0.5
        - T80: first time series reaches >= 0.8
    """
    kpi_data: Dict[str, Any] = {}
    t_grid = series_df.index.values

    # Extend to t_end for accurate AUC if needed
    if t_grid.max() < t_end:
        t_grid_ext = np.append(t_grid, t_end)
        series_ext = pd.concat(
            [
                series_df,
                pd.DataFrame(
                    series_df.iloc[[-1]].values,
                    index=[t_end],
                    columns=series_df.columns,
                ),
            ]
        )
    else:
        t_grid_ext = t_grid
        series_ext = series_df

    # 1) AUC (normalized by the duration)
    auc_raw = np.trapz(series_ext.values, t_grid_ext, axis=0)
    kpi_data["AUC"] = auc_raw / (t_grid_ext[-1] - t_grid_ext[0])

    # 2) T50 / T80
    def find_crossing_time(series: pd.Series, threshold: float):
        vals = series.values
        idxs = np.where(vals >= threshold)[0]
        return np.nan if idxs.size == 0 else series.index[idxs[0]]

    kpi_data["T50"] = series_df.apply(find_crossing_time, threshold=0.5)
    kpi_data["T80"] = series_df.apply(find_crossing_time, threshold=0.8)

    return pd.DataFrame(kpi_data, index=series_df.columns)


def compute_graph_robustness(
    G: nx.Graph,
    sub_series_df: pd.DataFrame,
    t_grid: np.ndarray,
    cfg: Config,
) -> pd.DataFrame:
    """
    Compute dynamic graph robustness over time.

    Metric:
        - Largest connected component (LCC) size among "functional" nodes
        - Average degree of the LCC subgraph: avg_degree = 2 * E / N
        - LCC fraction relative to the initial (baseline) LCC size in G

    Functional-node definition:
        - A node is considered functional at time t if its series value > 0.5
    """
    logger = logging.getLogger()
    logger.info("Computing dynamic graph robustness (Metric: Average Degree)...")

    if sub_series_df.empty or G.number_of_nodes() == 0:
        return pd.DataFrame(columns=["t", "lcc_size", "avg_degree", "lcc_fraction"])

    # -------------------------------------------------------------------------
    # 1) Normalize IDs to align Graph nodes and DataFrame columns
    # -------------------------------------------------------------------------
    node_map = {n: str(n).strip() for n in G.nodes()}
    nodes_norm = set(node_map.values())

    col_norm = [str(c).strip() for c in sub_series_df.columns]
    col_to_norm = dict(zip(sub_series_df.columns, col_norm))
    norm_to_col = {v: k for k, v in col_to_norm.items()}

    # -------------------------------------------------------------------------
    # 2) Find overlap and compute robustness on aligned identifiers
    # -------------------------------------------------------------------------
    inter_norm = list(nodes_norm.intersection(set(col_norm)))

    if len(inter_norm) > 0:
        keep_cols = [norm_to_col[s] for s in inter_norm]
        sub_series_filtered = sub_series_df[keep_cols].copy()

        # Map normalized strings back to original graph node IDs
        norm_to_graph_node = {}
        for n, s in node_map.items():
            if s in inter_norm:
                norm_to_graph_node[s] = n

        new_cols = [norm_to_graph_node[col_to_norm[c]] for c in keep_cols]
        sub_series_filtered.columns = new_cols

        # Baseline LCC size for normalization
        try:
            initial_lcc_size = len(max(nx.connected_components(G), key=len))
        except ValueError:
            initial_lcc_size = 0

        if initial_lcc_size == 0:
            return pd.DataFrame(columns=["t", "lcc_size", "avg_degree", "lcc_fraction"])

        metrics = []
        last_functional_set = None

        for t in t_grid:
            func_mask = sub_series_filtered.loc[t] > cfg.FUNCTIONAL_THRESHOLD
            functional_nodes = set(func_mask.index[func_mask])

            # Reuse previous timestep's result when the functional set is unchanged
            if functional_nodes == last_functional_set and metrics:
                row = metrics[-1].copy()
                row["t"] = t
                metrics.append(row)
                continue

            last_functional_set = functional_nodes

            if not functional_nodes:
                metrics.append({"t": t, "lcc_size": 0, "avg_degree": 0.0})
                continue

            G_t = G.subgraph(functional_nodes)

            try:
                lcc_nodes = max(nx.connected_components(G_t), key=len, default=set())
                lcc_size = len(lcc_nodes)
            except ValueError:
                lcc_size = 0

            if lcc_size > 1:
                G_t_lcc = G_t.subgraph(lcc_nodes)
                # Average degree: 2E / N
                n_nodes = G_t_lcc.number_of_nodes()
                n_edges = G_t_lcc.number_of_edges()
                avg_deg = (2.0 * n_edges) / n_nodes if n_nodes > 0 else 0.0
            else:
                avg_deg = 0.0

            metrics.append({"t": t, "lcc_size": lcc_size, "avg_degree": avg_deg})

        df = pd.DataFrame(metrics)
        df["lcc_fraction"] = df["lcc_size"] / initial_lcc_size
        return df

    # -------------------------------------------------------------------------
    # 3) Fallback: no overlap after normalization
    # -------------------------------------------------------------------------
    logger.warning("No overlapping nodes after normalization; using fallback robustness.")

    frac_series = sub_series_df.mean(axis=1).clip(0, 1)

    try:
        initial_lcc_size = len(max(nx.connected_components(G), key=len))
    except ValueError:
        initial_lcc_size = 0

    rows = []
    for t in t_grid:
        f = float(frac_series.loc[t]) if t in frac_series.index else 0.0
        lcc_size = int(round(f * initial_lcc_size))
        rows.append({"t": t, "lcc_size": lcc_size, "avg_degree": 0.0})

    df = pd.DataFrame(rows)
    df["lcc_fraction"] = (df["lcc_size"] / initial_lcc_size) if initial_lcc_size else 0.0
    return df


def run_stage_3(
    cfg,
    stage_1_data,
    stage_0_data,
    stage_2_data,
    out_dirs,
) -> dict:
    """Orchestrate Stage 3: step recovery simulation using mean repair times."""
    if not cfg.RUN_STAGE_3:
        logging.info("--- STAGE 3: Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 3: Step Recovery Simulation ---")

    all_mc_repair_times = stage_1_data.get("all_mc_repair_times")
    if not all_mc_repair_times:
        logger.error("FATAL: Missing 'all_mc_repair_times' from Stage 2. Cannot run Stage 3.")
        return {}

    W_mat = stage_0_data["W_mat"]
    tract_index = stage_0_data["tract_index"]
    sub_index = stage_0_data["sub_index"]
    G = stage_2_data.get("G", nx.Graph())

    t_grid = np.arange(0, cfg.TIME_END_HR + cfg.DT_HR, cfg.DT_HR)

    all_mean_sub_repair_times = {}
    all_mean_tract_series = {}

    for scenario in cfg.SCENARIOS:
        logger.info(f"Processing scenario: {scenario}...")

        repair_times_samples = all_mc_repair_times[scenario]

        # 1) Mean repair time across Monte Carlo samples (per substation)
        mean_vals = repair_times_samples.mean(axis=1)

        # If a substation is undamaged in all MC runs, force mean to 0
        mean_vals[repair_times_samples.max(axis=1) == 0] = 0

        mean_series = pd.Series(
            mean_vals,
            index=sub_index,
            name="mean_repair_time_hr",
        )
        all_mean_sub_repair_times[scenario] = mean_series

        # 2) Simulate the mean step-recovery curve
        logger.info(f"Simulating mean recovery curve for {scenario}...")
        R_sub_mean_df = simulate_step_recovery(mean_series.values, t_grid, sub_index)

        # 3) Enforce correct state at t=0 for undamaged substations
        undamaged_subs = mean_series[mean_series <= cfg.UNDAMAGED_EPS_HR].index
        t0_idx = 0 if 0 in R_sub_mean_df.index else 0.0
        if t0_idx in R_sub_mean_df.index:
            R_sub_mean_df.loc[t0_idx, undamaged_subs] = 1.0
            logger.info(f"Fixed t=0 state for {len(undamaged_subs)} undamaged substations.")

        # 4) Propagate substation recovery to census tracts
        S_tract_mean_df = propagate_to_tracts(R_sub_mean_df, W_mat, tract_index)
        all_mean_tract_series[scenario] = S_tract_mean_df

        # 5) Save tract-level time series
        out_path = out_dirs["STAGE3_DIR"] / f"tract_step_recovery_mean_{scenario}.csv.gz"
        S_tract_mean_df.to_csv(out_path, compression="gzip", float_format="%.4f")

        # 6) Compute and save KPIs (T50, T80, AUC)
        kpis = kpis_from_series(S_tract_mean_df, cfg.TIME_END_HR)
        kpi_path = out_dirs["STAGE3_DIR"] / f"tract_kpis_{scenario}.csv"
        kpis.to_csv(kpi_path)

        # 7) Log system-wide summary
        system_curve = S_tract_mean_df.mean(axis=1)
        system_kpis = kpis_from_series(system_curve.to_frame("system"), cfg.TIME_END_HR)

        logger.info(
            f"OK {scenario}: {len(tract_index)} tracts saved. "
            f"System T50: {system_kpis['T50'].values[0]:.1f} hr, "
            f"System T80: {system_kpis['T80'].values[0]:.1f} hr."
        )

        # 8) Compute dynamic graph robustness (if graph exists)
        if G.number_of_nodes() > 0:
            robust_df = compute_graph_robustness(G, R_sub_mean_df, t_grid, cfg)
            robust_path = out_dirs["STAGE3_DIR"] / f"graph_robustness_mean_{scenario}.csv"
            robust_df.to_csv(robust_path, index=False)
            logger.info(f"Saved dynamic graph robustness to {robust_path}")

    logger.info("--- STAGE 3 Complete ---")
    return {
        "all_mean_sub_repair_times": all_mean_sub_repair_times,
        "all_mean_tract_series": all_mean_tract_series,
    }


# ==========================================================================
# [PART 6] Stage 4: Crew Scheduling & Repair Logistics (Rule-Based)
# =============================================================================
# Contains: Travel matrices, Substation ordering rules, Scheduling engine, run_stage_4
def load_travel_matrices(
    cfg,
    devices_df: pd.DataFrame,
    task_sub_ids: list,
    all_sub_ids: list,
) -> dict:
    """
    Load or generate travel-time matrices:
      - Base -> Task  (crew bases to substations)
      - Task -> Task  (substation to substation)

    If the CSVs are missing (or detected as stale), generate fallback matrices
    using great-circle distance (geodesic) and a constant virtual velocity.

    Returns:
        {
            "base_to_task": DataFrame (index=base_ids, columns=task_sub_ids),
            "task_to_task": DataFrame (index=task_sub_ids, columns=task_sub_ids),
        }
    """
    logger = logging.getLogger()

    base_to_task_path = Path(cfg.TRAVEL_BASE_TO_TASK_CSV)
    task_to_task_path = Path(cfg.TRAVEL_TASK_TO_TASK_CSV)

    force_regen_base = False
    force_regen_task = False
    all_sub_ids_set = set(all_sub_ids)

    # Expand crew bases: each base becomes a unique base_id (base_0, base_1, ...)
    crew_bases_expanded = [
        (name, lat, lon, f"base_{idx}")
        for idx, (name, lat, lon) in enumerate(cfg.CREW_BASES)
    ]
    crew_base_ids = [c[3] for c in crew_bases_expanded]

    # Extract coordinates for relevant task substations
    # NOTE: This function assumes devices_df has columns: ["id", "lat", "lon"].
    task_devices = devices_df.set_index("id").reindex(task_sub_ids)

    # =========================================================================
    # 1) Base -> Task matrix
    # =========================================================================
    if base_to_task_path.exists():
        logger.info(f"[Travel] Loading Base->Task CSV: {base_to_task_path}")
        base_to_task = pd.read_csv(base_to_task_path, index_col=0)

        # Normalize IDs (string + strip) to improve matching robustness
        base_to_task.index = base_to_task.index.astype(str).str.strip()
        base_to_task.columns = base_to_task.columns.astype(str).str.strip()

        # Integrity checks: expected to contain all substations and all crew bases
        if not all_sub_ids_set.issubset(base_to_task.columns):
            logger.warning("[Travel] Base->Task file is stale (missing substation IDs). Forcing fallback.")
            force_regen_base = True
        elif not set(crew_base_ids).issubset(base_to_task.index):
            logger.warning("[Travel] Base->Task file is stale (missing crew base IDs). Forcing fallback.")
            force_regen_base = True
        else:
            # Slice to current task set
            base_to_task = base_to_task.reindex(index=crew_base_ids, columns=task_sub_ids)

    if (not base_to_task_path.exists()) or force_regen_base:
        logger.warning("[Travel] Generating fallback Base->Task matrix (Haversine/Geodesic)...")

        data = {}
        for name, lat_b, lon_b, base_id in crew_bases_expanded:
            row = {}
            for sub_id in task_sub_ids:
                try:
                    lat_t, lon_t = task_devices.loc[sub_id, ["lat", "lon"]]
                    dist_km = geodesic((lat_b, lon_b), (lat_t, lon_t)).km
                    row[sub_id] = dist_km / cfg.VIRTUAL_VEL_KMH
                except Exception:
                    row[sub_id] = np.inf
            data[base_id] = row

        base_to_task = pd.DataFrame(data).T
        base_to_task.to_csv(base_to_task_path)

    # =========================================================================
    # 2) Task -> Task matrix
    # =========================================================================
    if task_to_task_path.exists():
        logger.info(f"[Travel] Loading Task->Task CSV: {task_to_task_path}")
        task_to_task = pd.read_csv(task_to_task_path, index_col=0)

        # Normalize IDs
        task_to_task.index = task_to_task.index.astype(str).str.strip()
        task_to_task.columns = task_to_task.columns.astype(str).str.strip()

        # Integrity checks: expected to contain all substations in both axes
        if (not all_sub_ids_set.issubset(task_to_task.columns)) or (not all_sub_ids_set.issubset(task_to_task.index)):
            logger.warning("[Travel] Task->Task file is stale. Forcing fallback.")
            force_regen_task = True
        else:
            task_to_task = task_to_task.reindex(index=task_sub_ids, columns=task_sub_ids)

    if (not task_to_task_path.exists()) or force_regen_task:
        logger.warning("[Travel] Generating fallback Task->Task matrix (Haversine/Geodesic)...")

        coords = task_devices[["lat", "lon"]].values
        n = len(task_sub_ids)
        data = np.full((n, n), np.inf)

        for i in range(n):
            for j in range(n):
                if i == j:
                    data[i, j] = 0.0
                    continue
                try:
                    dist_km = geodesic(coords[i], coords[j]).km
                    data[i, j] = dist_km / cfg.VIRTUAL_VEL_KMH
                except Exception:
                    continue

        task_to_task = pd.DataFrame(data, index=task_sub_ids, columns=task_sub_ids)
        task_to_task.to_csv(task_to_task_path)

    return {
        "base_to_task": base_to_task.fillna(np.inf),
        "task_to_task": task_to_task.fillna(np.inf),
    }


def order_substations(
    rule: str,
    task_sub_ids: list,
    stage_0_data: dict,
    stage_2_data: dict,
    cfg,
) -> list:
    """
    Sort the *repair task* substations (task_sub_ids) under a given priority rule.

    Supported rules:
      - "centrality-first": impact_centrality (lambda2) -> betweenness -> degree
      - "betweenness-first"
      - "degree-first"
      - "closeness-first"
      - "impact-first": impact_population (Stage 2.5)
      - "hospital-first": hospital-tract coverage -> population
      - "random": random baseline
    """
    logger = logging.getLogger()

    # Normalize IDs as strings
    task_sub_ids = [str(s) for s in task_sub_ids]
    tasks_set = set(task_sub_ids)

    # -------------------------------------------------------------------------
    # Random baseline
    # -------------------------------------------------------------------------
    if rule == "random":
        rng = np.random.default_rng(cfg.RNG_SEED)
        shuffled = list(task_sub_ids)
        rng.shuffle(shuffled)
        return shuffled

    # Pull centrality table (used by multiple rules)
    centrality_df = stage_2_data.get("centrality_df")
    if centrality_df is not None:
        centrality_df = centrality_df.copy()
        centrality_df.index = centrality_df.index.astype(str)

    def _order_by_metrics(metric_names, ascending_flags=None):
        """
        Sort by one or more metrics in centrality_df, then filter to task_sub_ids.
        Falls back to random if centrality_df or metrics are unavailable.
        """
        if centrality_df is None:
            logger.warning(f"{rule}: centrality_df missing. Falling back to random.")
            return order_substations("random", task_sub_ids, stage_0_data, stage_2_data, cfg)

        cols = [m for m in metric_names if m in centrality_df.columns]
        if not cols:
            logger.warning(f"{rule}: none of {metric_names} found in centrality_df. Falling back to random.")
            return order_substations("random", task_sub_ids, stage_0_data, stage_2_data, cfg)

        if ascending_flags is None:
            ascending_flags = [False] * len(cols)

        ordered_all = centrality_df.sort_values(by=cols, ascending=ascending_flags).index
        return [sid for sid in ordered_all if sid in tasks_set]

    # -------------------------------------------------------------------------
    # Metric-based rules (centrality_df)
    # -------------------------------------------------------------------------
    if rule == "centrality-first":
        return _order_by_metrics(
            ["impact_centrality", "betweenness_centrality", "degree"],
            [False, False, False],
        )

    if rule == "betweenness-first":
        return _order_by_metrics(["betweenness_centrality", "degree"], [False, False])

    if rule == "degree-first":
        return _order_by_metrics(["degree", "betweenness_centrality"], [False, False])

    if rule == "closeness-first":
        return _order_by_metrics(["closeness_centrality", "degree"], [False, False])

    if rule == "impact-first":
        return _order_by_metrics(["impact_population"], [False])

    # -------------------------------------------------------------------------
    # Hospital-first (needs mapping_df + hospital tract file)
    # -------------------------------------------------------------------------
    if rule == "hospital-first":
        mapping_df = stage_0_data.get("mapping_df")
        if mapping_df is None:
            logger.warning("hospital-first: mapping_df missing. Falling back to random.")
            return order_substations("random", task_sub_ids, stage_0_data, stage_2_data, cfg)

        try:
            hospital_tracts_df = pd.read_csv(cfg.HOSPITAL_TRACTS_CSV)
            hosp_tract_ids = set(
                hospital_tracts_df["geoid"]
                .astype(str)
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )
        except Exception as e:
            logger.warning(f"Hospital data load failed: {e}. Falling back to random.")
            return order_substations("random", task_sub_ids, stage_0_data, stage_2_data, cfg)

        m = mapping_df.copy()
        m["tract_id_clean"] = (
            m["tract_id"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        )
        m["substation_id"] = m["substation_id"].astype(str).str.strip()
        m["is_hosp_tract"] = m["tract_id_clean"].isin(hosp_tract_ids)

        sub_hosp_priority = m.groupby("substation_id")["is_hosp_tract"].sum()
        pop_impact = m.groupby("substation_id")["population"].sum()

        priority_df = pd.concat([sub_hosp_priority, pop_impact], axis=1).fillna(0.0)
        priority_df.columns = ["hosp_score", "pop_score"]
        priority_df.index = priority_df.index.astype(str)

        ordered_all = priority_df.sort_values(
            by=["hosp_score", "pop_score"],
            ascending=[False, False],
        ).index

        return [sid for sid in ordered_all if sid in tasks_set]

    # Unknown rule -> fallback
    logger.warning(f"Unknown rule '{rule}', falling back to random.")
    return order_substations("random", task_sub_ids, stage_0_data, stage_2_data, cfg)


def simulate_rule_schedule(
    order: list,
    n_crews: int,
    travel_mats: dict,
    t_grid: np.ndarray,
    sub_repair_durations: pd.Series,
    sub_index: pd.Index,
    cfg: Config,
) -> pd.DataFrame:
    """
    Simulate a multi-crew repair schedule under a fixed task ordering.

    Key behaviors (unchanged):
      - Each crew starts at a yard base_id.
      - If current_loc is a base_id: use Base->Task matrix.
      - If current_loc is a substation: use Task->Task matrix.
      - If a required entry is missing / non-finite: apply a hard fallback travel time (24.0 hr).
      - Undamaged substations (repair_duration == 0) are marked completed at t=0.
      - Returns a step-recovery matrix via simulate_step_recovery().
    """
    logger = logging.getLogger()

    base_to_task = travel_mats["base_to_task"].copy()
    task_to_task = travel_mats["task_to_task"].copy()

    # Normalize IDs (string + strip) to avoid int/str mismatches
    base_to_task.index = base_to_task.index.astype(str).str.strip()
    base_to_task.columns = base_to_task.columns.astype(str).str.strip()

    task_to_task.index = task_to_task.index.astype(str).str.strip()
    task_to_task.columns = task_to_task.columns.astype(str).str.strip()

    order = [str(x).strip() for x in order]
    sub_index = pd.Index([str(x).strip() for x in sub_index])

    sub_repair_durations = sub_repair_durations.copy()
    sub_repair_durations.index = sub_repair_durations.index.astype(str).str.strip()

    # All yard IDs
    base_ids = list(base_to_task.index)
    base_id_set = set(base_ids)

    # -------------------------------------------------------------------------
    # 1) Initialize crew clocks and starting locations
    # -------------------------------------------------------------------------
    crew_clocks = np.zeros(n_crews)

    if base_ids:
        repeated = (base_ids * ((n_crews // len(base_ids)) + 1))[:n_crews]
        crew_locations = repeated.copy()
    else:
        # Extreme fallback: no base info
        crew_locations = [None] * n_crews

    # -------------------------------------------------------------------------
    # 2) Initialize completion times for each substation
    # -------------------------------------------------------------------------
    sub_end_times = pd.Series(np.inf, index=sub_index)

    undamaged_subs = sub_repair_durations[sub_repair_durations <= cfg.UNDAMAGED_EPS_HR].index
    sub_end_times.loc[undamaged_subs] = 0.0

    # Task queue: only tasks that require repair
    task_queue = list(order)

    # Precompute average Base->Task times (used only as a fallback)
    avg_base_to_task = base_to_task.mean(axis=0) if not base_to_task.empty else pd.Series(dtype=float)

    # -------------------------------------------------------------------------
    # 3) Main scheduling loop: dispatch the earliest-available crew to next task
    # -------------------------------------------------------------------------
    while task_queue:
        next_crew_idx = int(np.argmin(crew_clocks))
        current_time = float(crew_clocks[next_crew_idx])
        current_loc = crew_locations[next_crew_idx]

        next_task_id = task_queue.pop(0)

        # --- 3.1 Travel time ---
        if current_loc in base_id_set:
            # From yard/base
            try:
                travel_time = float(base_to_task.loc[current_loc, next_task_id])
            except KeyError:
                travel_time = float(avg_base_to_task.get(next_task_id, np.inf))

        elif current_loc is None:
            # Extreme fallback: no base location info
            travel_time = float(avg_base_to_task.get(next_task_id, np.inf))

        else:
            # From previous substation
            try:
                travel_time = float(task_to_task.loc[current_loc, next_task_id])
            except KeyError:
                travel_time = np.inf

        if not np.isfinite(travel_time):
            # Hard penalty: treat as nearly unreachable
            travel_time = 24.0

        # --- 3.2 Completion time ---
        arrival_time = current_time + travel_time
        repair_duration = float(sub_repair_durations.get(next_task_id, 0.0))
        end_time = arrival_time + repair_duration

        crew_clocks[next_crew_idx] = end_time
        crew_locations[next_crew_idx] = next_task_id

        if next_task_id in sub_end_times.index:
            sub_end_times.loc[next_task_id] = end_time
        else:
            logger.warning(f"Task {next_task_id} not in sub_end_times index.")

    # -------------------------------------------------------------------------
    # 4) Convert completion times into step-recovery time series (Stage 3 helper)
    # -------------------------------------------------------------------------
    return simulate_step_recovery(sub_end_times.values, t_grid, sub_index)


def get_analysis_weights(cfg: Config, stage_0_data: Dict) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Helper: compute tract-level analysis weights.

    Returns:
        (pop_weights, svi_pop_weights)

    Where:
        - pop_weights: normalized population weights over tract_index
        - svi_pop_weights: normalized (population * SVI) weights over tract_index (or None if unavailable)
    """
    logger = logging.getLogger()

    mapping_df = stage_0_data.get("mapping_df")
    tract_index = stage_0_data.get("tract_index")

    # -------------------------------------------------------------------------
    # 1) Population weights (Population / TotalPopulation)
    # -------------------------------------------------------------------------
    if mapping_df is not None and "population" in mapping_df.columns:
        pop_per_tract = (
            mapping_df.groupby("tract_id")["population"]
            .first()
            .reindex(tract_index)
            .fillna(0.0)
        )

        total_pop = float(pop_per_tract.sum())
        if total_pop > 0:
            pop_weights = pop_per_tract.values.astype(float) / total_pop
        else:
            pop_weights = np.ones(len(tract_index), dtype=float) / len(tract_index)
    else:
        pop_weights = np.ones(len(tract_index), dtype=float) / len(tract_index)

    # -------------------------------------------------------------------------
    # 2) SVI * Population weights (optional)
    # -------------------------------------------------------------------------
    svi_pop_weights: Optional[np.ndarray] = None

    if getattr(cfg, "SVI_CSV", None):
        try:
            svi_df = pd.read_csv(cfg.SVI_CSV)

            # Default column names (configurable)
            geoid_col = getattr(cfg, "SVI_GEOID_COL", "geoid")
            value_col = getattr(cfg, "SVI_VALUE_COL", "SVI")

            # If the configured column names are missing, attempt auto-detection
            if geoid_col not in svi_df.columns:
                for c in svi_df.columns:
                    c_lower = str(c).lower()
                    if "geoid" in c_lower or "tract" in c_lower:
                        geoid_col = c
                        break

            if value_col not in svi_df.columns:
                for c in ["SVI", "svi", "RPL_THEMES", "rpl_themes"]:
                    if c in svi_df.columns:
                        value_col = c
                        break

            if geoid_col in svi_df.columns and value_col in svi_df.columns:
                svi_df[geoid_col] = svi_df[geoid_col].astype(str)

                svi_series = svi_df.set_index(geoid_col)[value_col].astype(float)
                svi_aligned = svi_series.reindex(tract_index).fillna(0.0)
                svi_vals = svi_aligned.values

                # Clean NaN/inf and ensure nonnegative
                svi_vals[~np.isfinite(svi_vals)] = 0.0
                if np.min(svi_vals) < 0:
                    svi_vals -= np.min(svi_vals)

                # Core logic: weights = population * SVI
                # NOTE: This block assumes `total_pop` exists from the population-weight branch.
                raw_w = pop_weights * total_pop * svi_vals if total_pop > 0 else svi_vals

                if raw_w.sum() > 0:
                    svi_pop_weights = raw_w / raw_w.sum()
                    logger.info("SVI weights calculated successfully for analysis.")

        except Exception as e:
            logger.warning(f"Failed to calculate SVI weights: {e}")

    return pop_weights, svi_pop_weights


def run_stage_4(
    cfg,
    stage_3_data: dict,
    stage_0_data: dict,
    stage_2_data: dict,
    stage_2_5_graph_data: dict,
    out_dirs: dict,
) -> dict:
    """
    Stage 4B: rule-based scheduling baselines (with Population and optional SVI-weighted curves).

    Output (per scenario):
        - rule_curves_pop_{scenario}.csv
        - rule_curves_svi_{scenario}.csv (if SVI weights available)
        - rule_kpis_pop_{scenario}.csv
        - rule_graphrobustness_{scenario}_{rule}.csv
    """
    if not cfg.RUN_STAGE_4:
        logging.info("--- STAGE 4: Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 4: Rule-Based Baselines (Modified for SVI) ---")

    all_mean_sub_repair_times = stage_3_data.get("all_mean_sub_repair_times")
    if not all_mean_sub_repair_times:
        logger.error("FATAL: Missing 'all_mean_sub_repair_times'. Stage 3 might have failed.")
        return {}

    W_mat = stage_0_data["W_mat"]
    tract_index = stage_0_data["tract_index"]
    sub_index = stage_0_data["sub_index"]

    G = stage_2_5_graph_data.get("G", nx.Graph())
    t_grid = np.arange(0, cfg.TIME_END_HR + cfg.DT_HR, cfg.DT_HR)

    rules = [
        "centrality-first",   # Impact (lambda2)
        "impact-first",       # Impact (population)
        "betweenness-first",  # Bridges
        "degree-first",       # Hubs
        "closeness-first",    # Accessibility
        "hospital-first",     # Critical facilities coverage
        "random",             # Baseline
    ]

    # -------------------------------------------------------------------------
    # Analysis weights (Population + optional SVI*Population)
    # -------------------------------------------------------------------------
    pop_weights, svi_pop_weights = get_analysis_weights(cfg, stage_0_data)
    if svi_pop_weights is None:
        logger.warning("SVI weights not available. SVI curves will not be generated.")

    # Separate result containers for Population-weighted vs SVI-weighted curves
    results_pop: Dict[str, pd.DataFrame] = {}
    results_svi: Dict[str, pd.DataFrame] = {}

    out_dir = out_dirs["STAGE4_DIR"]

    for scenario in cfg.SCENARIOS:
        logger.info(f"Processing scenario: {scenario}...")

        sub_repair_durations = all_mean_sub_repair_times[scenario]

        # Tasks = damaged substations only
        tasks_to_do_series = sub_repair_durations[sub_repair_durations > 0]
        task_sub_ids = list(tasks_to_do_series.index)

        if not task_sub_ids:
            logger.warning(f"No damaged substations for {scenario}. Skipping.")
            continue

        # Travel matrices (Base->Task, Task->Task)
        travel_mats = load_travel_matrices(
            cfg,
            stage_0_data["devices_merged"],
            task_sub_ids,
            sub_index.to_list(),
        )

        scenario_curves_pop: Dict[str, np.ndarray] = {}
        scenario_curves_svi: Dict[str, np.ndarray] = {}
        scenario_kpis_pop: Dict[str, pd.DataFrame] = {}

        for rule in rules:
            logger.info(f"   - Simulating rule: {rule}")

            order = order_substations(rule, task_sub_ids, stage_0_data, stage_2_data, cfg)

            R_sub_df = simulate_rule_schedule(
                order,
                cfg.N_CREWS,
                travel_mats,
                t_grid,
                sub_repair_durations,
                sub_index,
                cfg,
            )

            S_tract_df = propagate_to_tracts(R_sub_df, W_mat, tract_index)

            # 1) Population-weighted system curve
            system_curve_pop = S_tract_df.values @ pop_weights
            scenario_curves_pop[rule] = system_curve_pop

            # KPIs (Population only, to preserve backward compatibility)
            kpis = kpis_from_series(
                pd.DataFrame({"system": system_curve_pop}, index=t_grid),
                cfg.TIME_END_HR,
            )
            kpis["rule"] = rule
            scenario_kpis_pop[rule] = kpis

            # 2) SVI-weighted system curve (optional)
            if svi_pop_weights is not None:
                system_curve_svi = S_tract_df.values @ svi_pop_weights
                scenario_curves_svi[rule] = system_curve_svi

            # Dynamic graph robustness (unchanged)
            if G.number_of_nodes() > 0:
                dyn_df = compute_graph_robustness(G, R_sub_df, t_grid, cfg)
                dyn_df.to_csv(out_dir / f"rule_graphrobustness_{scenario}_{rule}.csv", index=False)
            else:
                pd.DataFrame({"t": [0], "lcc_fraction": [0.0]}).to_csv(
                    out_dir / f"rule_graphrobustness_{scenario}_{rule}.csv",
                    index=False,
                )

        # ---------------------------------------------------------------------
        # Write outputs
        # ---------------------------------------------------------------------
        df_pop = pd.DataFrame(scenario_curves_pop, index=t_grid)
        df_pop.to_csv(out_dir / f"rule_curves_pop_{scenario}.csv", index_label="time_hr")
        results_pop[scenario] = df_pop

        if scenario_curves_svi:
            df_svi = pd.DataFrame(scenario_curves_svi, index=t_grid)
            df_svi.to_csv(out_dir / f"rule_curves_svi_{scenario}.csv", index_label="time_hr")
            results_svi[scenario] = df_svi

        if scenario_kpis_pop:
            kpis_df = pd.concat(scenario_kpis_pop.values())
            kpis_df.to_csv(out_dir / f"rule_kpis_pop_{scenario}.csv", index=False)

        logger.info(f"Wrote rule-based curves (Pop & SVI) to {out_dir} for {scenario}")

    logger.info("--- STAGE 4 Complete ---")

    # Return separated dicts for Stage 6 consumption
    return {"pop": results_pop, "svi": results_svi}


# =============================================================================
# Stage 5: Genetic Algorithm Optimization
# =============================================================================

def run_stage_5(
    cfg: Config,
    stage_0_data: Dict,
    stage_3_data: Dict,
    out_dirs: Dict,
) -> Dict:
    if not cfg.RUN_STAGE_5:
        logging.info("--- STAGE 5 (GA): Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 5: Genetic Algorithm Optimization (Evolutionary with Inversion Mutation) ---")

    # Prepare Data
    all_mean_sub = stage_3_data["all_mean_sub_repair_times"]
    W_mat = stage_0_data["W_mat"]
    sub_index = stage_0_data["sub_index"]
    tract_index = stage_0_data["tract_index"]

    # --- Normalize indices to strings (avoid mismatched int/str ids)
    sub_index_str = [str(s).strip() for s in list(sub_index)]
    tract_index_str = pd.Index(tract_index).astype(str).str.split(".").str[0].str.strip()

    # --- Hospital score (optional)
    try:
        hosp_df = pd.read_csv(cfg.HOSPITAL_TRACTS_CSV)

        geo_col = "geoid"
        if geo_col not in hosp_df.columns:
            for cand in ["GEOID", "tract_id", "TRACTFIPS"]:
                if cand in hosp_df.columns:
                    geo_col = cand
                    break

        hosp_ids = set(hosp_df[geo_col].astype(str).str.split(".").str[0].str.strip())
        is_hosp = pd.Series(0.0, index=tract_index_str)
        is_hosp.loc[is_hosp.index.isin(hosp_ids)] = 1.0

        # is_hosp: (n_tract,), W_mat: (n_tract, n_sub) => sub_hosp_score: (n_sub,)
        sub_hosp_score = is_hosp.values @ W_mat
    except Exception as e:
        logger.warning(f"Hospital score unavailable; using zeros. Reason: {e}")
        sub_hosp_score = np.zeros(len(sub_index_str), dtype=float)

    # DEAP creator guards
    if not hasattr(creator, "FitnessMax"):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()

    # Precompute population impact per substation (aligned to sub_index)
    pop_per_tract = (
        stage_0_data["mapping_df"]
        .groupby("tract_id")["population"]
        .first()
    )
    pop_per_tract.index = pop_per_tract.index.astype(str).str.split(".").str[0].str.strip()
    pop_vec = pop_per_tract.reindex(tract_index_str).fillna(0.0).values  # (n_tract,)
    pop_imp = pop_vec @ W_mat  # (n_sub,)

    sub_idx_map = {sid: i for i, sid in enumerate(sub_index_str)}

    ga_results = {}

    for scenario in cfg.SCENARIOS:
        logger.info(f"Running GA for {scenario}...")

        run_seed = cfg.RNG_SEED + abs(hash(scenario))
        random.seed(run_seed)
        logger.info(f"  > GA Random Seed set to: {run_seed}")

        repair_times = all_mean_sub[scenario]
        tasks = repair_times[repair_times > 0.1]
        task_ids = list(tasks.index)
        n_tasks = len(task_ids)

        if n_tasks == 0:
            continue

        # Travel matrices (restricted to task list)
        tmats = load_travel_matrices(cfg, stage_0_data["devices_merged"], task_ids, list(sub_index))
        base_mat = tmats["base_to_task"].values   # (n_bases, n_tasks)
        task_mat = tmats["task_to_task"].values   # (n_tasks, n_tasks)

        # --- Fixed base assignment for crews (CRITICAL FIX)
        n_bases = int(base_mat.shape[0])
        crew_base_idx = np.array(
            (list(range(n_bases)) * ((cfg.N_CREWS // n_bases) + 1))[: cfg.N_CREWS],
            dtype=int,
        )

        # Align task ids to global sub indices
        task_ids_str = [str(t).strip() for t in task_ids]
        global_idxs = []
        for t in task_ids_str:
            if t not in sub_idx_map:
                raise ValueError(f"[GA] Task substation id '{t}' not found in sub_index.")
            global_idxs.append(sub_idx_map[t])

        task_vals = cfg.W_POP * pop_imp[global_idxs] + cfg.W_HOSP * sub_hosp_score[global_idxs]
        task_times = tasks.values  # aligned with task_ids order

        def eval_sched(ind):
            clocks = np.zeros(cfg.N_CREWS, dtype=float)
            locs = np.full(cfg.N_CREWS, -1, dtype=int)
            end_times = np.zeros(n_tasks, dtype=float)

            for t_idx in ind:
                c = int(np.argmin(clocks))
                prev = int(locs[c])

                # Travel time:
                # - First task: from crew's assigned base ONLY (no min over all bases).
                # - Otherwise: from previous task.
                if prev == -1:
                    travel = float(base_mat[crew_base_idx[c], t_idx])
                else:
                    travel = float(task_mat[prev, t_idx])

                start = clocks[c] + travel
                end = start + float(task_times[t_idx])

                clocks[c] = end
                locs[c] = int(t_idx)
                end_times[int(t_idx)] = end

            T_MAX = float(cfg.TIME_END_HR) + float(cfg.GA_EXTRA_EVAL_HR)
            valid = end_times < T_MAX

            score = float(np.sum(task_vals[valid] * (T_MAX - end_times[valid])))
            score -= float(cfg.W_MAKESPAN) * float(np.max(clocks)) * float(np.mean(task_vals))
            return (score,)

        # Inversion mutation
        def mutInversion(individual, indpb):
            """Inversion Mutation: reverse a random subsequence with probability indpb."""
            if random.random() < indpb:
                size = len(individual)
                if size < 2:
                    return (individual,)
                a, b = random.sample(range(size), 2)
                if a > b:
                    a, b = b, a
                individual[a:b+1] = individual[a:b+1][::-1]
            return (individual,)

        # Register operators
        toolbox.register("evaluate", eval_sched)
        toolbox.register("mate", tools.cxOrdered)
        toolbox.register("mutate", mutInversion, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)

        # Init population
        pop = []
        for _ in range(cfg.GA_POP_SIZE - 2):
            p = list(range(n_tasks))
            random.shuffle(p)
            pop.append(creator.Individual(p))
        pop.append(creator.Individual(np.argsort(task_vals)[::-1].tolist()))
        pop.append(creator.Individual(np.argsort(task_times).tolist()))

        algo_stats = tools.Statistics(lambda ind: ind.fitness.values)
        algo_stats.register("max", np.max)

        # Run GA
        pop, log = algorithms.eaSimple(
            pop,
            toolbox,
            cxpb=cfg.GA_CXPB,
            mutpb=cfg.GA_MUTPB,
            ngen=cfg.GA_N_GEN,
            verbose=False,
            stats=algo_stats,
        )

        best_ind = tools.selBest(pop, 1)[0]
        logger.info(f"  > Gen {cfg.GA_N_GEN} Best Fitness: {best_ind.fitness.values[0]:.2e}")

        best_order = [task_ids[i] for i in best_ind]

        # Build recovery curve (population-weighted)
        t_grid = np.arange(0, cfg.TIME_END_HR + cfg.DT_HR, cfg.DT_HR)

        # Use full repair_times series for safety (tasks is subset; either works if simulate_rule_schedule handles it)
        R_sub = simulate_rule_schedule(best_order, cfg.N_CREWS, tmats, t_grid, repair_times, sub_index, cfg)
        S_tract = propagate_to_tracts(R_sub, W_mat, tract_index)

        pop_w, _ = get_analysis_weights(cfg, stage_0_data)
        curve = S_tract.values @ pop_w

        ga_results[scenario] = pd.Series(curve, index=t_grid, name="GA_Best")

    out = {"pop": {}}
    for scen, ser in ga_results.items():
        df = pd.DataFrame({"GA_Best": ser})
        df.index.name = "time_hr"
        out["pop"][scen] = df

    return out

# ==========================================================================
# [PART 7] Stage 6: Visualization & Results Consolidation
# =============================================================================
# Contains: Consolidating Stage 3 & 4B results, Plotting curves, Saving System KPIs
def run_stage_6(
    cfg: Config,
    stage_0_data: Dict,
    stage_3_data: Dict,
    stage_4_data: Dict,
    stage_5_data: Dict,
    out_dirs: Dict,
):
    """
    Stage 6: Consolidation & plotting.

    Consolidates:
      - Stage 3 theoretical (unconstrained) system recovery curves
      - Stage 4B rule-based scheduling system recovery curves
      - Stage 5 GA-optimized system recovery curves (if provided via stage_5_data)

    Produces:
      - Per-scenario plots (Population-weighted and optional SVI-weighted)
      - recovery_curves_all_system.csv
      - recovery_kpis_all_system.csv
    """
    if not cfg.RUN_STAGE_6:
        logging.info("--- STAGE 6: Skipped ---")
        return

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 6: Consolidation & Separate Plotting (Adaptive X; GA optional) ---")

    out_dir = out_dirs["STAGE6_DIR"]
    t_grid = np.arange(0, cfg.TIME_END_HR + cfg.DT_HR, cfg.DT_HR)

    # -------------------------------------------------------------------------
    # 1) Weights
    # -------------------------------------------------------------------------
    pop_weights, svi_pop_weights = get_analysis_weights(cfg, stage_0_data)

    # -------------------------------------------------------------------------
    # 2) Result containers
    # -------------------------------------------------------------------------
    all_system_curves: Dict[str, pd.Series] = {}
    all_kpis: List[pd.DataFrame] = []

    # -------------------------------------------------------------------------
    # 3) Plot styling
    # -------------------------------------------------------------------------
    style_config = {
        "GA_Best":           ("GA Optimized", "purple", "-", 3.5, 1.0, 10),

        # Stage 3 theoretical limit
        "S3_Mean": ("Theoretical Limit (Unconstrained)", "black", "--", 2.0, 0.6, 1),

        # Rule-based baselines (Stage 4B)
        "centrality-first":  ("Impact λ2-First (Grid Topo)",      "#e41a1c",   "-", 3.0, 0.9, 3),
        "impact-first":      ("Impact-First (Population)",        "#ff7f00",   "-", 3.0, 0.9, 4),
        "betweenness-first": ("Betweenness-First (Bridges)",      "#ffd92f",   "-", 3.0, 0.9, 5),
        "degree-first":      ("Degree-First (Hubs)",              "#4daf4a",   "-", 3.0, 0.9, 6),
        "closeness-first":   ("Closeness-First (Accessibility)",  "#377eb8",   "-", 3.0, 0.9, 7),
        "hospital-first":    ("Hospital-First (Critical)",        "#555555",   "-", 3.0, 0.9, 8),
        "random":            ("Baseline (Random)",                "lightgray", ":", 2.5, 0.9, 2),
    }

    # -------------------------------------------------------------------------
    # Helper: Align series to t_grid
    # -------------------------------------------------------------------------
    def _align_to_tgrid(series: pd.Series) -> pd.Series:
        """Ensure series index matches t_grid for consistent plotting/export."""
        if series is None:
            return series
        s = series.copy()
        try:
            s = s.sort_index()
            # Reindex to t_grid (fills gaps if any). Use forward-fill then back-fill as safe fallback.
            s = s.reindex(t_grid)
            s = s.ffill().bfill()
        except Exception:
            # If anything goes wrong, just return original series.
            return series
        return s

    # -------------------------------------------------------------------------
    # Helper: single-scenario plot
    # -------------------------------------------------------------------------
    def plot_single_scenario(scenario_name: str, data_dict: Dict[str, pd.Series], weight_type: str) -> None:
        """
        Plot a single scenario's recovery curves.

        Args:
            scenario_name: scenario label
            data_dict: mapping {curve_key -> pd.Series(time->value)}
            weight_type: "Population" or "SVI_Weighted"
        """
        try:
            sns.set_style("whitegrid")
            sns.set_context("talk", font_scale=1.2)
        except Exception:
            plt.style.use("ggplot")

        fig, ax = plt.subplots(figsize=(10, 7))

        plotted_series: List[pd.Series] = []
        has_plotted = False

        # Plot in style_config order (controls legend order)
        for key, (label, color, ls, lw, alpha, zorder) in style_config.items():
            if key not in data_dict:
                continue

            series = _align_to_tgrid(data_dict[key])
            plotted_series.append(series)

            # Legend label tweaks for SVI plot (only these two labels change)
            final_label = label
            if weight_type == "SVI_Weighted":
                if key == "impact-first":
                    final_label = "Impact-First (SVI-Adjusted)"
                elif key == "S3_Mean":
                    final_label = "Theoretical Limit (SVI-Weighted)"

            ax.plot(
                series.index,
                series.values,
                label=final_label,
                color=color,
                linestyle=ls,
                linewidth=lw,
                alpha=alpha,
                zorder=zorder,
            )
            has_plotted = True

        # --- Adaptive X-axis trimming ---
        if plotted_series:
            try:
                df_plot = pd.concat(plotted_series, axis=1)
                unfinished = df_plot < 0.999
                if unfinished.any().any():
                    last_t = unfinished.any(axis=1).iloc[::-1].idxmax()
                    limit_t = min(cfg.TIME_END_HR, float(last_t) * 1.25)
                    ax.set_xlim(0, limit_t)
                else:
                    ax.set_xlim(0, cfg.TIME_END_HR)
            except Exception:
                ax.set_xlim(0, cfg.TIME_END_HR)
        else:
            ax.set_xlim(0, cfg.TIME_END_HR)

        suffix = " (SVI Weighted)" if weight_type == "SVI_Weighted" else " (Population Weighted)"
        ax.set_title(
            f"System Recovery: {scenario_name}{suffix}",
            fontsize=20,
            fontweight="bold",
            pad=14,
        )

        y_label = "Functionality (%)" if weight_type == "Population" else "SVI-Weighted Recovery (%)"
        ax.set_ylabel(y_label, fontsize=18)
        ax.set_xlabel("Time (Hours)", fontsize=18)
        ax.set_ylim(-0.02, 1.05)
        ax.tick_params(axis="both", labelsize=16)

        if has_plotted:
            leg = ax.legend(loc="lower right", framealpha=0.95, fontsize=14)
            if leg.get_title() is not None:
                leg.get_title().set_fontsize(14)

        ax.grid(True, linestyle="--", alpha=0.6)

        filename = f"recovery_curve_{scenario_name}_{weight_type}.png"
        plt.tight_layout()
        plt.savefig(out_dir / filename, dpi=300, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved plot: {filename}")

    # -------------------------------------------------------------------------
    # 4) Main loop: consolidate per scenario
    # -------------------------------------------------------------------------
    for scenario in cfg.SCENARIOS:
        logger.info(f"Consolidating for {scenario}...")

        current_pop_curves: Dict[str, pd.Series] = {}
        current_svi_curves: Dict[str, pd.Series] = {}

        # ---------------------------------------------------------------------
        # A) Stage 3 theoretical limit
        # ---------------------------------------------------------------------
        s3_curves = stage_3_data.get("all_mean_tract_series", {})
        if scenario in s3_curves:
            s3_tract_df = s3_curves[scenario]

            # Population-weighted system curve
            s3_pop = pd.Series(s3_tract_df.values @ pop_weights, index=s3_tract_df.index)
            s3_pop = _align_to_tgrid(s3_pop)
            current_pop_curves["S3_Mean"] = s3_pop
            all_system_curves[f"{scenario}_S3_Mean_Pop"] = s3_pop

            kpis = kpis_from_series(pd.DataFrame({"system": s3_pop}), cfg.TIME_END_HR)
            kpis["scenario"] = scenario
            kpis["rule"] = "Stage3_Mean"
            all_kpis.append(kpis)

            # SVI-weighted system curve (optional)
            if svi_pop_weights is not None:
                s3_svi = pd.Series(s3_tract_df.values @ svi_pop_weights, index=s3_tract_df.index)
                s3_svi = _align_to_tgrid(s3_svi)
                current_svi_curves["S3_Mean"] = s3_svi
                all_system_curves[f"{scenario}_S3_Mean_SVI"] = s3_svi

                kpis_svi = kpis_from_series(pd.DataFrame({"system": s3_svi}), cfg.TIME_END_HR)
                kpis_svi["scenario"] = scenario
                kpis_svi["rule"] = "Stage3_Mean_SVIpop"
                all_kpis.append(kpis_svi)

        # ---------------------------------------------------------------------
        # B) Stage 4B rule-based scheduling curves
        # ---------------------------------------------------------------------
        s4b_pop_data = stage_4_data.get("pop", {}).get(scenario)
        s4b_svi_data = stage_4_data.get("svi", {}).get(scenario)

        if s4b_pop_data is not None:
            for rule in s4b_pop_data.columns:
                series = _align_to_tgrid(s4b_pop_data[rule])
                current_pop_curves[rule] = series
                all_system_curves[f"{scenario}_S4B_{rule}_Pop"] = series

                kpis = kpis_from_series(pd.DataFrame({rule: series}), cfg.TIME_END_HR)
                kpis["scenario"] = scenario
                kpis["rule"] = f"Stage4B_{rule}"
                all_kpis.append(kpis)

        if s4b_svi_data is not None:
            for rule in s4b_svi_data.columns:
                series = _align_to_tgrid(s4b_svi_data[rule])
                current_svi_curves[rule] = series
                all_system_curves[f"{scenario}_S4B_{rule}_SVI"] = series

        # ---------------------------------------------------------------------
        # C) Stage 5 GA curves
        # ---------------------------------------------------------------------
        if stage_5_data and isinstance(stage_5_data, dict) and "pop" in stage_5_data:
            ga_scen = stage_5_data["pop"].get(scenario)

            if ga_scen is not None and isinstance(ga_scen, pd.DataFrame) and "GA_Best" in ga_scen.columns:
                series = _align_to_tgrid(ga_scen["GA_Best"])

                current_pop_curves["GA_Best"] = series
                all_system_curves[f"{scenario}_GA_Best_Pop"] = series

                # KPIs
                kpis = kpis_from_series(pd.DataFrame({"GA_Best": series}), cfg.TIME_END_HR)
                kpis["scenario"] = scenario
                kpis["rule"] = "Stage5_GA"
                all_kpis.append(kpis)
            else:
                logger.info(f"GA output not found for scenario={scenario} (or missing 'GA_Best').")

        # ---------------------------------------------------------------------
        # D) Plotting
        # ---------------------------------------------------------------------
        if current_pop_curves:
            plot_single_scenario(scenario, current_pop_curves, "Population")

        if current_svi_curves and svi_pop_weights is not None:
            plot_single_scenario(scenario, current_svi_curves, "SVI_Weighted")

    # -------------------------------------------------------------------------
    # 5) Write consolidated outputs
    # -------------------------------------------------------------------------
    if all_system_curves:
        all_curves_df = pd.DataFrame(all_system_curves)
        all_curves_df = all_curves_df.reindex(t_grid)  # enforce unified time index in CSV
        all_curves_df.to_csv(out_dir / "recovery_curves_all_system.csv", index_label="time_hr")

    if all_kpis:
        all_kpis_df = pd.concat(all_kpis).reset_index(drop=True)
        all_kpis_df.to_csv(out_dir / "recovery_kpis_all_system.csv", index=False)

    logger.info("--- STAGE 6 Complete ---")


# ==========================================================================
# [PART 8] Stage 7: Typology Clustering (PCA + K-Means)
# =============================================================================
# Contains: Feature Engineering, PCA, K-Means Clustering, run_stage_8
def run_stage_7(
    cfg,
    stage_3_data,
    stage_0_data,
    stage_1_data,
    out_dirs,
) -> dict:
    if not cfg.RUN_STAGE_7:
        logging.info("--- STAGE 7: Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 7: PCA + K-Means (Final Enhanced) ---")
    out_dir = out_dirs["STAGE7_DIR"]

    # =========================================================
    # 1. Feature Engineering (Data Preparation)
    # =========================================================
    logger.info("1. Preparing Features...")

    # -----------------------------
    # Helper(s) (formatting only)
    # -----------------------------
    def _normalize_tract_id(series: pd.Series) -> pd.Series:
        """
        Standardize tract_id to common 10-digit style:
        keep numeric part only, drop decimal suffix, and strip leading zeros
        (e.g., 06001400100 -> 6001400100).
        """
        return (
            series.astype(str)
            .str.split(".")
            .str[0]
            .str.extract(r"(\d+)")[0]
            .str.lstrip("0")
        )

    # ---------------------------------------------------------
    # A. Recovery Metrics (from Stage 3)
    # ---------------------------------------------------------
    dynamic_rows = []
    for scen in cfg.SCENARIOS:
        s3_kpi_path = out_dirs["STAGE3_DIR"] / f"tract_kpis_{scen}.csv"
        if not s3_kpi_path.exists():
            continue

        df_s3 = pd.read_csv(s3_kpi_path)
        if "tract_id" not in df_s3.columns:
            df_s3.rename(columns={df_s3.columns[0]: "tract_id"}, inplace=True)

        df_s3["tract_id"] = df_s3["tract_id"].astype(str).str.split(".").str[0]
        for _, row in df_s3.iterrows():
            dynamic_rows.append(
                {
                    "tract_id": row["tract_id"],
                    "scenario": scen,
                    "T50": row.get("T50", 0),
                    "T80": row.get("T80", 0),
                    "AUC": row.get("AUC", 0),
                }
            )

    if not dynamic_rows:
        return {}

    df_main_raw = pd.DataFrame(dynamic_rows)

    # ---------------------------------------------------------
    # B. Resistance Metrics (from Stage 2)
    # ---------------------------------------------------------
    prob_frames = []
    for scen in cfg.SCENARIOS:
        prob_file = out_dirs["STAGE1_DIR"] / f"MC_TractOutage_Prob_{scen}.csv"
        if not prob_file.exists():
            continue

        df_p = pd.read_csv(prob_file)
        col_id = "tract" if "tract" in df_p.columns else df_p.columns[0]
        col_val = "outage_prob" if "outage_prob" in df_p.columns else df_p.columns[-1]

        df_p[col_id] = df_p[col_id].astype(str).str.split(".").str[0]
        df_p = df_p.rename(columns={col_id: "tract_id", col_val: "Init_Prob"})
        df_p["scenario"] = scen
        prob_frames.append(df_p[["tract_id", "scenario", "Init_Prob"]])

    if prob_frames:
        df_main_raw = (
            pd.merge(
                df_main_raw,
                pd.concat(prob_frames),
                on=["tract_id", "scenario"],
                how="left",
            )
            .fillna(0)
        )
    else:
        df_main_raw["Init_Prob"] = 0

    # ---------------------------------------------------------
    # Aggregation across scenarios (mean)
    # ---------------------------------------------------------
    logger.info("Aggregating metrics across scenarios (taking mean)...")
    df_main = (
        df_main_raw.groupby("tract_id")[["T50", "T80", "AUC", "Init_Prob"]]
        .mean()
        .reset_index()
    )

    # Standardize tract_id: keep digits only, remove decimal suffix, strip leading zeros
    df_main["tract_id"] = _normalize_tract_id(df_main["tract_id"])

    # ---------------------------------------------------------
    # C. Grid Centrality & Network Structure Features
    # ---------------------------------------------------------
    cent_path = out_dirs["STAGE2_DIR"] / "impact_centrality_substations.csv"
    mapping_df = stage_0_data.get("mapping_df", None)

    # Default values
    df_main["Grid_Centrality"] = 0.0
    df_main["Grid_ImpactLambda2"] = 0.0
    df_main["Grid_Betweenness"] = 0.0
    df_main["N_subs"] = 0
    df_main["Redundancy_HHI"] = np.nan
    df_main["Redundancy_MaxShare"] = np.nan
    df_main["Dist_to_CrewYard_km"] = np.nan

    if cent_path.exists() and mapping_df is not None:
        try:
            df_cent = pd.read_csv(cent_path)

            # Identify substation id column
            sub_col = None
            for c in df_cent.columns:
                cl = c.lower()
                if "substation" in cl and "id" in cl:
                    sub_col = c
                    break
            if sub_col is None:
                sub_col = df_cent.columns[0]

            df_cent[sub_col] = df_cent[sub_col].astype(str).str.strip()
            df_cent = df_cent.set_index(sub_col)

            # Centrality column names
            deg_col = "degree" if "degree" in df_cent.columns else df_cent.columns[0]
            bet_col = (
                "betweenness_centrality"
                if "betweenness_centrality" in df_cent.columns
                else None
            )
            imp_col = (
                "impact_centrality" if "impact_centrality" in df_cent.columns else None
            )

            m = mapping_df.copy()
            # IMPORTANT: use the same tract_id normalization as df_main
            m["tract_id"] = _normalize_tract_id(m["tract_id"])
            m["substation_id"] = m["substation_id"].astype(str).str.strip()

            join_cols = [deg_col]
            if bet_col:
                join_cols.append(bet_col)
            if imp_col:
                join_cols.append(imp_col)

            m = m.merge(
                df_cent[join_cols],
                left_on="substation_id",
                right_index=True,
                how="left",
            )

            rename_map = {deg_col: "deg"}
            if bet_col and bet_col in m.columns:
                rename_map[bet_col] = "bet"
            if imp_col and imp_col in m.columns:
                rename_map[imp_col] = "imp"
            m = m.rename(columns=rename_map)

            g = m.groupby("tract_id")

            # 1) Grid_Centrality: mean degree
            if "deg" in m.columns:
                grid_deg = g["deg"].mean()
                df_main["Grid_Centrality"] = (
                    df_main["tract_id"].map(grid_deg).fillna(0.0)
                )

            # 2) Grid_ImpactLambda2: mean impact_centrality
            if "imp" in m.columns:
                grid_imp = g["imp"].mean()
                df_main["Grid_ImpactLambda2"] = (
                    df_main["tract_id"].map(grid_imp).fillna(0.0)
                )

            # 3) Grid_Betweenness: mean betweenness
            if "bet" in m.columns:
                grid_bet = g["bet"].mean()
                df_main["Grid_Betweenness"] = (
                    df_main["tract_id"].map(grid_bet).fillna(0.0)
                )

            # 4) N_subs
            tract_nsubs = g["substation_id"].nunique()
            df_main["N_subs"] = (
                df_main["tract_id"].map(tract_nsubs).fillna(0).astype(int)
            )

            # 5) Redundancy metrics (if weights exist)
            if "weight" in m.columns:

                def _redundancy_stats(grp):
                    w = grp["weight"].values.astype(float)
                    total = w.sum()
                    if total <= 0:
                        return pd.Series(
                            {
                                "Redundancy_HHI": np.nan,
                                "Redundancy_MaxShare": np.nan,
                            }
                        )
                    shares = w / total
                    return pd.Series(
                        {
                            "Redundancy_HHI": float(np.sum(shares**2)),
                            "Redundancy_MaxShare": float(np.max(shares)),
                        }
                    )

                red_df = g.apply(_redundancy_stats)
                red_df.index = red_df.index.astype(str)

                df_main["Redundancy_HHI"] = df_main["tract_id"].map(
                    red_df["Redundancy_HHI"]
                )
                df_main["Redundancy_MaxShare"] = df_main["tract_id"].map(
                    red_df["Redundancy_MaxShare"]
                )

            # 6) Dist_to_CrewYard_km (nearest crew yard) — USE TRACT GEOMETRY CENTROID
            if getattr(cfg, "CREW_BASES", None) and os.path.exists(cfg.LA_TRACTS_PATH):

                def haversine_km(lat1, lon1, lat2, lon2):
                    R = 6371.0  # km
                    phi1 = math.radians(lat1)
                    phi2 = math.radians(lat2)
                    dphi = math.radians(lat2 - lat1)
                    dlambda = math.radians(lon2 - lon1)
                    a = (
                        math.sin(dphi / 2) ** 2
                        + math.cos(phi1)
                        * math.cos(phi2)
                        * math.sin(dlambda / 2) ** 2
                    )
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    return R * c

                # Load tract geometries
                tracts = gpd.read_file(cfg.LA_TRACTS_PATH)

                # Find a tract id column
                cand_cols = ["tract_id", "GEOID", "GEOID10", "TRACTFIPS", "FIPS"]
                tid_col = next((c for c in cand_cols if c in tracts.columns), None)
                if tid_col is None:
                    for c in tracts.columns:
                        if "geoid" in c.lower():
                            tid_col = c
                            break
                if tid_col is None:
                    tid_col = tracts.columns[0]

                # Normalize tract ids to match df_main
                tracts[tid_col] = _normalize_tract_id(tracts[tid_col])

                # Ensure CRS, then compute centroid in a projected CRS
                if tracts.crs is None:
                    tracts = tracts.set_crs("EPSG:4326", allow_override=True)

                tracts_proj = tracts.to_crs(epsg=3310)  # California Albers
                cent_proj = tracts_proj.geometry.centroid
                cent_wgs = gpd.GeoSeries(cent_proj, crs=tracts_proj.crs).to_crs(
                    epsg=4326
                )

                tracts["cent_lat"] = cent_wgs.y
                tracts["cent_lon"] = cent_wgs.x

                tract_xy = (
                    tracts[[tid_col, "cent_lat", "cent_lon"]]
                    .dropna()
                    .drop_duplicates(subset=[tid_col])
                    .set_index(tid_col)
                )

                yard_coords = [(lat, lon) for _, lat, lon in cfg.CREW_BASES]

                def _min_dist_cent(row):
                    lat_t, lon_t = row["cent_lat"], row["cent_lon"]
                    if pd.isna(lat_t) or pd.isna(lon_t):
                        return np.nan
                    if not yard_coords:
                        return np.nan
                    return float(
                        min(haversine_km(lat_t, lon_t, ylat, ylon) for (ylat, ylon) in yard_coords)
                    )

                tract_xy["Dist_to_CrewYard_km"] = tract_xy.apply(_min_dist_cent, axis=1)
                df_main["Dist_to_CrewYard_km"] = df_main["tract_id"].map(
                    tract_xy["Dist_to_CrewYard_km"]
                )

        except Exception as e:
            logger.warning(f"Stage 7: failed to compute grid/logistics features: {e}")

    # ---------------------------------------------------------
    # D. SVI & Population Density (External Census Data, 4 themes)
    # ---------------------------------------------------------
    SVI_FILE_PATH = r"C:\2025-2026 Fall\Network science\Project\California.csv"
    svi_factor_cols = []  # up to four theme factors: SVI_THEME1-4

    if os.path.exists(SVI_FILE_PATH):
        try:
            df_svi = pd.read_csv(SVI_FILE_PATH)

            # LA County only: 6037
            if "STCNTY" in df_svi.columns:
                df_la = df_svi[df_svi["STCNTY"] == 6037].copy()
            else:
                df_la = df_svi[df_svi["FIPS"].astype(str).str.startswith("6037")].copy()

            # Clean -999 across EP_*, RPL_*, and (population/area if present)
            clean_cols = []
            clean_cols += [c for c in df_la.columns if c.startswith("EP_")]
            clean_cols += [c for c in df_la.columns if c.startswith("RPL_")]
            for extra in ["E_TOTPOP", "AREA_SQMI"]:
                if extra in df_la.columns:
                    clean_cols.append(extra)
            clean_cols = list(dict.fromkeys(clean_cols))

            for c in clean_cols:
                df_la[c] = df_la[c].replace(-999, np.nan)
                df_la[c] = df_la[c].fillna(df_la[c].median())

            # County-level population density
            if "E_TOTPOP" in df_la.columns and "AREA_SQMI" in df_la.columns:
                df_la["Pop_Density"] = df_la["E_TOTPOP"] / df_la["AREA_SQMI"].replace(0, 1)
            else:
                df_la["Pop_Density"] = 0.0

            # 1) Prefer official RPL_THEME1-4
            theme_cols = []
            rpl_to_theme = {
                "RPL_THEME1": "SVI_THEME1",
                "RPL_THEME2": "SVI_THEME2",
                "RPL_THEME3": "SVI_THEME3",
                "RPL_THEME4": "SVI_THEME4",
            }
            for rpl, svi_name in rpl_to_theme.items():
                if rpl in df_la.columns:
                    df_la[svi_name] = df_la[rpl]
                    theme_cols.append(svi_name)

            # 2) If RPL_THEME* not available, build themes from EP_* variables
            if not theme_cols:
                theme1_vars = [v for v in ["EP_POV150", "EP_UNEMP", "EP_PCI", "EP_NOHSDP"] if v in df_la.columns]
                theme2_vars = [v for v in ["EP_AGE65", "EP_AGE17", "EP_DISABL", "EP_SNGPNT"] if v in df_la.columns]
                theme3_vars = [v for v in ["EP_MINRTY", "EP_LIMENG"] if v in df_la.columns]
                theme4_vars = [v for v in ["EP_MUNIT", "EP_MOBILE", "EP_CROWD", "EP_NOVEH", "EP_GROUPQ", "EP_GRPQ"] if v in df_la.columns]

                def build_theme(df, var_list, name, invert_vars=None):
                    """
                    CDC-like logic:
                    - percentile-rank each EP_* variable
                    - invert variables if needed (e.g., EP_PCI: higher income -> lower vulnerability)
                    - sum ranks, then percentile-rank again for the theme score
                    """
                    if invert_vars is None:
                        invert_vars = set()

                    var_list = [v for v in var_list if v in df.columns]
                    if not var_list:
                        return False

                    ranks = []
                    for v in var_list:
                        r = df[v].rank(pct=True)
                        if v in invert_vars:
                            r = 1.0 - r
                        ranks.append(r)

                    theme_sum = pd.concat(ranks, axis=1).sum(axis=1)
                    df[name + "_SUM"] = theme_sum
                    df[name] = theme_sum.rank(pct=True)
                    return True

                if build_theme(df_la, theme1_vars, "SVI_THEME1", invert_vars={"EP_PCI"}):
                    theme_cols.append("SVI_THEME1")
                if build_theme(df_la, theme2_vars, "SVI_THEME2"):
                    theme_cols.append("SVI_THEME2")
                if build_theme(df_la, theme3_vars, "SVI_THEME3"):
                    theme_cols.append("SVI_THEME3")
                if build_theme(df_la, theme4_vars, "SVI_THEME4"):
                    theme_cols.append("SVI_THEME4")

            # 3) Map theme columns + Pop_Density to tract_id
            if not theme_cols:
                logger.warning(
                    "No SVI theme columns (RPL_THEME* or EP_* aggregation) found; skipping SVI features."
                )
            else:
                df_la["FIPS_STR"] = df_la["FIPS"].astype(str)

                cols_to_merge = theme_cols + ["Pop_Density"]
                # Include EP_POV150 for later summary if it exists
                if "EP_POV150" in df_la.columns:
                    cols_to_merge.append("EP_POV150")

                df_la_subset = df_la[["FIPS_STR"] + cols_to_merge].copy()
                svi_lookup = df_la_subset.set_index("FIPS_STR")[cols_to_merge]

                def get_svi_row(tid):
                    if tid in svi_lookup.index:
                        return svi_lookup.loc[tid]
                    if len(tid) == 10:
                        t2 = "0" + tid
                        if t2 in svi_lookup.index:
                            return svi_lookup.loc[t2]
                    # If no match, return NaNs (filled by median later)
                    return pd.Series({c: np.nan for c in cols_to_merge})

                svi_data = df_main["tract_id"].apply(get_svi_row)
                df_main = pd.concat([df_main, svi_data], axis=1)

                # Tract-level median fill (per column)
                for c in cols_to_merge:
                    df_main[c] = df_main[c].fillna(df_main[c].median())

                # These theme columns enter the global PCA
                svi_factor_cols = [
                    c
                    for c in ["SVI_THEME1", "SVI_THEME2", "SVI_THEME3", "SVI_THEME4"]
                    if c in df_main.columns
                ]

        except Exception as e:
            logger.error(f"SVI Load Failed: {e}")
            svi_factor_cols = []
    else:
        logger.warning(f"SVI file not found: {SVI_FILE_PATH}")
        svi_factor_cols = []

    # ---------------------------------------------------------
    # E. NRI: multi-hazard risk & resilience (tract-level)
    # ---------------------------------------------------------
    NRI_FILE_PATH = (
        r"C:\2025-2026 Fall\Network science\Project\NRI_Table_CensusTracts_California"
        r"\NRI_Table_CensusTracts_California.csv"
    )

    if os.path.exists(NRI_FILE_PATH):
        logger.info(f"Loading NRI tract table from {NRI_FILE_PATH}")
        df_nri = pd.read_csv(NRI_FILE_PATH)

        # Construct tract_id to match 10-digit style (no leading zero)
        # Priority: NRI_ID (e.g., T06001400100)
        if "NRI_ID" in df_nri.columns:
            df_nri["tract_id"] = (
                df_nri["NRI_ID"].astype(str).str.extract(r"(\d+)")[0].str.lstrip("0")
            )
        elif "TRACTFIPS" in df_nri.columns:
            df_nri["tract_id"] = (
                df_nri["TRACTFIPS"].astype(str).str.extract(r"(\d+)")[0].str.lstrip("0")
            )
        elif {"STCOFIPS", "TRACT"} <= set(df_nri.columns):
            df_nri["tract_id"] = (
                df_nri["STCOFIPS"].astype(str).str.zfill(5)
                + df_nri["TRACT"].astype(str).str.zfill(6)
            )
            df_nri["tract_id"] = (
                df_nri["tract_id"].astype(str).str.extract(r"(\d+)")[0].str.lstrip("0")
            )
        else:
            logger.warning(
                "NRI file missing NRI_ID / TRACTFIPS / (STCOFIPS+TRACT); skipping NRI features."
            )
            df_nri = None

        if df_nri is not None:
            # Keep only target columns; skip missing ones
            base_keep = [
                "tract_id",
                "BUILDVALUE",
                "RISK_SCORE",
                "EAL_SCORE",
                "POPULATION",
                "AREA",
            ]
            keep_cols = [c for c in base_keep if c in df_nri.columns]
            missing = [c for c in base_keep if c not in df_nri.columns]
            if missing:
                logger.warning(
                    f"NRI file missing columns {missing}; continuing with {keep_cols}."
                )

            df_nri = df_nri[keep_cols].copy()

            # Population density using NRI POPULATION / AREA
            if {"POPULATION", "AREA"} <= set(df_nri.columns):
                df_nri["NRI_Pop_Density"] = df_nri["POPULATION"] / df_nri["AREA"].replace({0: np.nan})
                df_nri["NRI_Pop_Density"] = df_nri["NRI_Pop_Density"].replace([np.inf, -np.inf], np.nan)

            # Rename to NRI_*
            rename_map = {}
            if "RISK_SCORE" in df_nri.columns:
                rename_map["RISK_SCORE"] = "NRI_RISK_SCORE"
            if "EAL_SCORE" in df_nri.columns:
                rename_map["EAL_SCORE"] = "NRI_EAL_SCORE"
            if "RESL_SCORE" in df_nri.columns:
                rename_map["RESL_SCORE"] = "NRI_RESL_SCORE"
            if "BUILDVALUE" in df_nri.columns:
                rename_map["BUILDVALUE"] = "NRI_BUILDVALUE"

            df_nri = df_nri.rename(columns=rename_map)

            # Merge into df_main
            df_main = df_main.merge(df_nri, on="tract_id", how="left")

            # Median-fill NRI-related missing values (BUILDVALUE not logged)
            for col in [
                "NRI_RISK_SCORE",
                "NRI_EAL_SCORE",
                "NRI_BUILDVALUE",
                "NRI_Pop_Density",
            ]:
                if col in df_main.columns:
                    df_main[col] = pd.to_numeric(df_main[col], errors="coerce")
                    df_main[col] = df_main[col].fillna(df_main[col].median())
    else:
        logger.warning(
            f"NRI tract table not found at {NRI_FILE_PATH}; skipping NRI-based PCA features."
        )

    # ---------------------------------------------------------
    # F. Housing Age (External ACS Data)
    # ---------------------------------------------------------
    HOUSING_FILE_PATH = (
        r"C:\2025-2026 Fall\Network science\Project\ACSDT5Y2022.B25034_2025-11-19T135920"
        r"\ACSDT5Y2022.B25034-Data.csv"
    )

    if os.path.exists(HOUSING_FILE_PATH):
        try:
            df_house = pd.read_csv(HOUSING_FILE_PATH, header=1)
            id_col = [c for c in df_house.columns if "Geography" in c or "GEO" in c][0]
            df_house["tract_id"] = df_house[id_col].astype(str).str.split("US").str[-1]

            total_col = [c for c in df_house.columns if "Estimate!!Total" in c and "Built" not in c][0]

            old_cols = []
            for col in df_house.columns:
                for kw in [
                    "Built 1960 to 1969",
                    "Built 1950 to 1959",
                    "Built 1940 to 1949",
                    "Built 1939 or earlier",
                ]:
                    if kw in col and "Margin" not in col:
                        old_cols.append(col)
                        break

            for c in old_cols + [total_col]:
                df_house[c] = pd.to_numeric(df_house[c], errors="coerce").fillna(0)

            df_house["Pre_1970_Ratio"] = df_house[old_cols].sum(axis=1) / df_house[total_col].replace(0, 1)

            hmap = df_house.set_index("tract_id")["Pre_1970_Ratio"].to_dict()

            def get_h(tid):
                val = hmap.get(tid)
                if val is not None:
                    return val
                if len(tid) == 10:
                    return hmap.get("0" + tid)
                return 0

            df_main["Pre_1970_Ratio"] = df_main["tract_id"].apply(get_h).fillna(0)
        except Exception:
            df_main["Pre_1970_Ratio"] = 0
    else:
        df_main["Pre_1970_Ratio"] = 0

    # =========================================================
    # 2. PCA & Clustering
    # =========================================================
    feat_cols = [
        "T80",
        "AUC",
        "Init_Prob",
        "Grid_Centrality",
        "Grid_ImpactLambda2",
        "Grid_Betweenness",
        "N_subs",
        "Redundancy_HHI",
        "Dist_to_CrewYard_km",
        "Pre_1970_Ratio",
        "Pop_Density",
        "NRI_RISK_SCORE",
        "NRI_EAL_SCORE",
        "NRI_BUILDVALUE",
    ] + svi_factor_cols  # svi_factor_cols is either the theme list or []

    # Filter out invalid/constant columns
    valid_cols = [c for c in feat_cols if c in df_main.columns and df_main[c].std() > 1e-6]
    logger.info(f"Clustering on {len(valid_cols)} features: {valid_cols}")

    X = df_main[valid_cols].values
    X_scaled = StandardScaler().fit_transform(X)

    # ---------------------------------------------------------
    # 2.1 Full PCA (Eigenvalues & Scree Plot)
    # ---------------------------------------------------------
    pca = PCA()
    X_pca_full = pca.fit_transform(X_scaled)

    eigenvalues = pca.explained_variance_
    variance_ratios = pca.explained_variance_ratio_

    # Save PCA stats (includes eigenvalues)
    pd.DataFrame(
        {
            "PC": [f"PC{i+1}" for i in range(len(eigenvalues))],
            "Eigenvalue": eigenvalues,
            "Explained_Variance_Ratio": variance_ratios,
            "Cumulative_Ratio": np.cumsum(variance_ratios),
        }
    ).to_csv(out_dir / "pca_stats_with_eigenvalues.csv", index=False)

    # =========================================================
    # 2.2 Select n_components (Automatic Kaiser Criterion)
    # =========================================================
    eigenvalues = pca.explained_variance_
    n_components_auto = np.sum(eigenvalues > 1)
    n_components = max(2, n_components_auto)

    logger.info(f" > Kaiser Criterion: Selected {n_components} PCs (Eigenvalues > 1)")

    X_pca = X_pca_full[:, :n_components]

    # Save loadings (PC1..PCn)
    loadings = pca.components_.T[:, :n_components]
    pd.DataFrame(
        loadings,
        index=valid_cols,
        columns=[f"PC{i+1}" for i in range(n_components)],
    ).to_csv(out_dir / "pca_loadings.csv")

    # Additional scree plot (preserved behavior)
    plt.figure(figsize=(10, 6))
    pc_range = range(1, len(eigenvalues) + 1)
    plt.plot(pc_range, eigenvalues, "bo-", linewidth=2, markersize=8, label="Eigenvalue")
    plt.axhline(y=1, color="r", linestyle="--", linewidth=2, label="Kaiser Criterion (Ev=1)")
    plt.title("PCA Scree Plot")
    plt.xlabel("Principal Component")
    plt.ylabel("Eigenvalue")
    plt.xticks(pc_range)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_dir / "pca_scree_plot.png", dpi=300)
    plt.close()
    logger.info("Saved pca_scree_plot.png")

    # =========================================================
    # K-Means Clustering (Elbow Method)
    # =========================================================
    iners = []
    for k in range(1, 11):
        km = KMeans(n_clusters=k, random_state=cfg.RNG_SEED, n_init=10)
        km.fit(X_pca)
        iners.append(km.inertia_)

    # Elbow detection (distance to line between endpoints)
    p1, p2 = np.array([1, iners[0]]), np.array([10, iners[-1]])
    dists = [
        np.abs(np.cross(p2 - p1, p1 - np.array([k, iners[k - 1]]))) / np.linalg.norm(p2 - p1)
        for k in range(1, 11)
    ]
    best_k = int(np.argmax(dists) + 1)
    logger.info(f" > Auto-detected Best k (Clusters) = {best_k}")

    # Final clustering
    kmeans = KMeans(n_clusters=best_k, random_state=cfg.RNG_SEED, n_init=10)
    df_main["cluster"] = kmeans.fit_predict(X_pca)

    # Append selected PC scores to df_main
    for i in range(n_components):
        df_main[f"PC{i+1}"] = X_pca[:, i]

    # Keep only intended output columns
    cols_keep = [
        "tract_id",
        "scenario",
        "cluster",
        "T50",
        "T80",
        "AUC",
        "Init_Prob",
        "Grid_Centrality",
        "Grid_ImpactLambda2",
        "Grid_Betweenness",
        "N_subs",
        "Redundancy_HHI",
        "Redundancy_MaxShare",
        "Dist_to_CrewYard_km",
        "Pre_1970_Ratio",
        "Pop_Density",
        "SVI_THEME1",
        "SVI_THEME2",
        "SVI_THEME3",
        "SVI_THEME4",
        "NRI_BUILDVALUE",
        "NRI_RISK_SCORE",
        "NRI_EAL_SCORE",
    ] + [f"PC{i+1}" for i in range(n_components)]

    cols_keep = [c for c in cols_keep if c in df_main.columns]
    df_main = df_main[cols_keep]

    df_main.to_csv(out_dir / "clusters_labels_final.csv", index=False)

    # =========================================================
    # 3. Visualization
    # =========================================================
    try:
        import seaborn as sns

        # Elbow plot
        plt.figure(figsize=(8, 6))
        plt.plot(range(1, 11), iners, "bo-")
        plt.plot([best_k], [iners[best_k - 1]], "rx", markersize=12)
        plt.title(f"Elbow Method (k={best_k})")
        plt.xlabel("Number of clusters (k)")
        plt.ylabel("Inertia (within-cluster SSE)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(out_dir / "elbow_curve_analysis.png", dpi=300)
        plt.close()

        # Scatter plot (PC1 vs PC2)
        if n_components >= 2:
            plt.figure(figsize=(10, 8))
            sns.scatterplot(
                x="PC1",
                y="PC2",
                hue="cluster",
                data=df_main,
                palette="viridis",
                s=50,
                alpha=0.7,
            )
            plt.title(f"Tract Typology (k={best_k})")
            plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%})")
            plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%})")
            plt.grid(True, linestyle=":", alpha=0.6)
            plt.savefig(out_dir / "pca_kmeans_scatter.png", dpi=300)
            plt.close()
            logger.info("Saved pca_kmeans_scatter.png")
    except Exception as e:
        logger.warning(f"Plotting failed: {e}")

    logger.info("--- STAGE 7 Complete ---")
    return {"clusters": df_main}


# ==========================================================================
# [PART 9] Main Execution Pipeline
# =============================================================================
# Contains: main() orchestration function and entry point
def main() -> None:
    """
    Orchestrate the end-to-end pipeline.

    Stages:
      0) Data loading & W-matrix construction
      2) Monte Carlo fragility sampling
      2.5) Static criticality & topology analysis
      3) Dynamic step-recovery simulation
      4B) Rule-based scheduling baselines
      5) GA scheduling (disabled)
      6) Consolidation & KPI plotting
      7) Replica OD flow & accessibility analysis (optional; currently disabled)
      8) Tract typology clustering (PCA + K-Means)
    """
    # ---------------------------------------------------------------------
    # 1) Configuration & setup
    # ---------------------------------------------------------------------
    cfg = Config()

    root_override = Path(OUTPUT_ROOT)
    root_override.mkdir(parents=True, exist_ok=True)

    log_file = root_override / "pipeline_run.log"
    logger = setup_logging(log_file)

    logger.info("=" * 70)
    logger.info("STARTING INTEGRATED EARTHQUAKE IMPACT PIPELINE")
    logger.info(f"Output Root Override: {root_override}")
    logger.info("=" * 70)

    out_dirs = make_out_dirs(cfg)

    # ---------------------------------------------------------------------
    # 2) Pipeline execution
    # ---------------------------------------------------------------------
    try:
        # Stage 0: Data loading & weight matrix construction
        stage_0_data = run_stage_0(cfg)

        # Stage 1: Monte Carlo fragility sampling
        stage_1_data = run_stage_1(cfg, stage_0_data, out_dirs)

        # Stage 2: Static criticality & topology analysis
        stage_2_data = run_stage_2(cfg, stage_0_data, out_dirs)

        # Stage 3: Dynamic step-recovery simulation
        stage_3_data = run_stage_3(
            cfg,
            stage_1_data,
            stage_0_data,
            stage_2_data,
            out_dirs,
        )

        # Stage 4: Rule-based scheduling baselines
        stage_4_data = run_stage_4(
            cfg,
            stage_3_data,
            stage_0_data,
            stage_2_data,
            stage_2_data,
            out_dirs,
        )

        # Stage 5: Genetic algorithm scheduling
        stage_5_data = run_stage_5(
            cfg,
            stage_0_data,
            stage_3_data,
            out_dirs,
        )

        # Stage 6: Consolidation & KPI plotting
        run_stage_6(
            cfg,
            stage_0_data,
            stage_3_data,
            stage_4_data,
            stage_5_data,
            out_dirs,
        )

        # Stage 7: Tract typology clustering (PCA + K-Means)
        run_stage_7(
            cfg,
            stage_3_data,
            stage_0_data,
            stage_1_data,
            out_dirs,
        )

        logger.info("=" * 70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 70)

    except Exception as e:
        logger.critical(
            f"PIPELINE FAILED with unhandled exception: {e}",
            exc_info=True,
        )
        logger.info("=" * 70)
        logger.info("PIPELINE TERMINATED WITH ERROR")
        logger.info("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
