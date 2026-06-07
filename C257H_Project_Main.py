# ==========================================================================
# [PART 1] Environment Setup, Configuration & Logging
# =============================================================================
# Contains: Imports, Runtime guards, Config dataclass, Logging setup, Path helpers
# --- Runtime environment guards (keep behavior identical) --------------------
import os as _os
import sys as _sys

_os.environ.setdefault("OMP_NUM_THREADS", "5")
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
- Stage 7:   Tract-Level Typology (K-Means + PCA Diagnostics)
- Sensitivity: 2%-in-50-year scenario only
"""

# --- Standard library imports -------------------------------------------------
import logging
import os
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import zlib

# --- Third-party imports ------------------------------------------------------
import matplotlib
import networkx as nx
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from joblib import Parallel, delayed
from scipy.stats import lognorm
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import norm
import random
from deap import base, creator, tools, algorithms

# --- GLOBAL LOG STORE ---
GLOBAL_GANTT_LOG = []
_TIMESTAMPED_BACKUPS_CREATED = set()

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
    DEVICES_CSV: str = str(DATA_DIR / "Los_Angeles_City_SUBSTATION_with_fragility_ORIGINAL.csv")
    PGA_CSV: str = str(DATA_DIR / "Substations_PGA_IDW_CEC.csv")
    MAP_TRACT_SUB_CSV: str = str(DATA_DIR / "tract_to_substation_mapping_CEC.csv")
    CEC_GRAPH_EDGES_CSV: str = str(DATA_DIR / "substation_graph_CEC_edges.csv")
    CEC_GRAPH_NODES_CSV: str = str(DATA_DIR / "substation_graph_CEC_nodes.csv")
    HOSPITAL_TRACTS_CSV: str = str(DATA_DIR / "hospital_with_tract.csv")
    SOURCE_NODES_CSV: str = str(DATA_DIR / "source_nodes_core.csv")
    STAGE7_SVI_DATA_PATH: str = str(DATA_DIR / "California.csv")
    STAGE7_NRI_DATA_PATH: str = str(DATA_DIR / "NRI_Table_CensusTracts_California.csv")
    STAGE7_HOUSING_DATA_PATH: str = str(DATA_DIR / "ACSDT5Y2022.B25034-Data.csv")

    # --- Social Vulnerability Index (tract-level)
    SVI_CSV: str = str(DATA_DIR / "LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv")
    SVI_GEOID_COL: str = "TRACTFIPS"
    SVI_VALUE_COL: str = "SOVI_SCORE"
    W_SVI: float = 1.0

    # --- Travel Time Inputs
    # Precomputed travel times conceptually live with Stage 4.
    TRAVEL_BASE_TO_TASK_CSV: str = stage_file("4", "travel_base_to_task.csv")
    TRAVEL_TASK_TO_TASK_CSV: str = stage_file("4", "travel_task_to_task.csv")
    VIRTUAL_VEL_KMH = 30.0  # Virtual travel speed for unconnected pairs

    # --- Stage 4/5 C57 depot and crew-origin inputs
    STAGE45_DEPOT_INPUT_CSV: str = str(DATA_DIR / "stage45_depot_inputs_final_origin_proxy.csv")
    STAGE45_C57_SCENARIO_LABEL: str = "C57_substation_ratio_main"
    STAGE45_C57_ALLOCATION_LABEL: str = "C57_yard_allocation_no_deletion_tie_coherent_zero_low"
    STAGE45_C57_TOTAL_EXACT: float = 56.905860
    STAGE45_ACTIVE_CREW_BASES_CSV: str = str(DATA_DIR / "stage45_active_crew_bases_C57.csv")
    STAGE45_ALL_DEPOT_AUDIT_CSV: str = str(DATA_DIR / "stage45_all_depot_crew_inputs_C57_audit.csv")
    STAGE45_EXPANDED_CREW_ORIGINS_CSV: str = str(DATA_DIR / "stage45_C57_expanded_crew_origins.csv")

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
    SCENARIOS: tuple = ("Northridge", "SanFernando", "LongBeach", "2pc50")
    TIME_END_HR: float = 480
    SUPPLY_THRESH: float = 0.8
    DT_HR: float = 0.05
    N_MC: int = 1000  # Number of MC samples per scenario
    FUNCTIONAL_THRESHOLD: float = 0.5  # Substation functional if value >= threshold
    SOURCE_GATE_ENABLED: bool = True  # Require functional substations to connect to an active source island
    MC_SOURCE_GATE_N_JOBS: int = 8
    REPAIR_TASK_MIN_MEAN_HR: Optional[float] = None  # None = DS1 mean repair time threshold
    GA_EXTRA_EVAL_HR: float = 24.0     # Extra horizon used in GA evaluation
    RNG_SEED: int = 42
    MUTUAL_AID_DELAY_HR: float = 8.0
    N_CORES: int = -1

    # --- GA Parameters
    GA_POP_SIZE: int = 100
    GA_N_GEN: int = 100
    GA_CXPB: float = 0.8
    GA_MUTPB: float = 0.2
    STAGE5_NODE_IMPORTANCE_ALPHA: float = 1.0
    STAGE5_NODE_IMPORTANCE_LINES_SCALE: float = 12.0
    STAGE5_NODE_IMPORTANCE_ROLE_WEIGHT: float = 0.70
    STAGE5_NODE_IMPORTANCE_VOLTAGE_WEIGHT: float = 0.20
    STAGE5_NODE_IMPORTANCE_LINES_WEIGHT: float = 0.10
    STAGE7_HOTSPOT_TOP_N: int = 10
    GA_SCENARIOS_CONFIG: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "Balanced":   {"W_POP": 1.0, "W_HOSP": 3.0,  "W_MAKESPAN": 0.5},
            "HospFirst":  {"W_POP": 1.0, "W_HOSP": 20.0, "W_MAKESPAN": 0.1},
            "Efficiency": {"W_POP": 1.0, "W_HOSP": 1.0,  "W_MAKESPAN": 2.0},
        }
    )

    # --- Toggle Stages
    RUN_STAGE_1: bool = True
    RUN_STAGE_2: bool = True
    RUN_STAGE_3: bool = True
    RUN_STAGE_4: bool = True
    RUN_STAGE_5: bool = True
    RUN_STAGE_6: bool = True
    RUN_STAGE_7: bool = True
    RUN_SENSITIVITY_ANALYSIS: bool = True

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
        logger.debug("Output directory ensured: %s", dir_path)

    # Special subdirectory for GA runs.
    sched_dir = paths["STAGE5_DIR"] / cfg.SCHEDULE_DIR
    sched_dir.mkdir(parents=True, exist_ok=True)
    paths["SCHEDULE_DIR"] = sched_dir
    logger.info("Stage output directories ensured.")

    return paths


# --- Repair / Functionality Parameter Tables ---------------------------------
# Conventions:
# - INITIAL_FUNCTIONALITY_BY_DS: directly specified residual functionality at t=0
# - REPAIR_PARAM_NORMAL_HR: (mean_hours, std_hours)
# - REPAIR_PARAM_LOGNORMAL: (median_hours, beta)  where beta is lognormal dispersion (ln-space)

INITIAL_FUNCTIONALITY_BY_DS = {
    0: 1.00,
    1: 0.50,
    2: 0.09,
    3: 0.04,
    4: 0.03,
}

REPAIR_PARAM_NORMAL_HR = {
    # DS1 (Slight)
    # Service-restoration actions: inspection/confirmation, relay reset, and switching.
    # DS1 is already at 50% initial functionality and remains source-gate passable.
    1: (1.0, 0.5),

    # DS2 (Moderate)
    # Typical actions: travel/inspection (3.5 h) + isolate one phase (2.5 h)
    # Reference: standard utility operating protocol for N-1 operation
    2: (6.0, 3.0),

    # DS3 (Extensive)
    # Typical actions: inspection, manual isolation, tie switching, and temporary bypass work
    # Recommended value: 12 +/- 4 h
    3: (12.0, 4.0),

    # DS4 (Complete)
    # Typical actions: major field reconfiguration, mobile/temporary equipment, and energization
    # Recommended value: 36 +/- 12 h
    4: (36.0, 12.0),
}

REPAIR_PARAM_LOGNORMAL = {
    # DS1 (Slight)
    # Dominant actions: automated/remote reset and minor checks
    # Assumed median repair time: 0.25 h
    1: (0.25, 1.082),

    # DS2 (Moderate)
    # Dominant actions: manual switching and small temporary reconfiguration
    # Assumed median repair time: 2.0 h
    2: (2.00, 1.082),

    # DS3 (Extensive)
    # Dominant actions: temporary bypass, transfer switching, and field work
    # Assumed median repair time: 10.0 h
    3: (10.0, 0.857),

    # DS4 (Complete)
    # Dominant actions: mobile equipment deployment and major reconfiguration
    # Assumed median repair time: 24.0 h
    4: (24.0, 0.857),
}


def get_repair_task_threshold_hr(cfg: Config) -> float:
    """Return the expected-repair-time threshold for dispatchable crew tasks."""
    configured = getattr(cfg, "REPAIR_TASK_MIN_MEAN_HR", None)
    if configured is not None:
        return float(configured)
    return float(REPAIR_PARAM_NORMAL_HR[1][0])


def select_repair_tasks(mean_repair_times: pd.Series, cfg: Config) -> Tuple[pd.Series, float]:
    """Select substations whose expected repair workload is DS1-equivalent or larger."""
    threshold_hr = get_repair_task_threshold_hr(cfg)
    repair_times = pd.to_numeric(mean_repair_times, errors="coerce").fillna(0.0)
    repair_times.index = repair_times.index.astype(str).str.strip()
    return repair_times[repair_times >= threshold_hr], threshold_hr


def build_repair_task_threshold_audit(
    scenario: str,
    mean_repair_times: pd.Series,
    ds_probs: pd.DataFrame,
    cfg: Config,
) -> pd.DataFrame:
    """Build a substation-level audit table for the repair-task threshold."""
    repair_times = pd.to_numeric(mean_repair_times, errors="coerce").fillna(0.0)
    repair_times.index = repair_times.index.astype(str).str.strip()
    threshold_hr = get_repair_task_threshold_hr(cfg)

    probs = ds_probs.reindex(index=repair_times.index, columns=range(5), fill_value=0.0)
    out = pd.DataFrame(
        {
            "scenario": scenario,
            "substation_id": repair_times.index,
            "mean_repair_time_hr": repair_times.values,
            "task_threshold_hr": threshold_hr,
            "is_repair_task": repair_times.values >= threshold_hr,
            "avg_damage_state": (probs.values * np.arange(5)).sum(axis=1),
            "p_ds_ge1": probs[[1, 2, 3, 4]].sum(axis=1).values,
            "p_ds_ge2": probs[[2, 3, 4]].sum(axis=1).values,
            "p_ds_ge3": probs[[3, 4]].sum(axis=1).values,
            "p_ds4": probs[4].values,
        }
    )
    return out


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
                devices["id"] = devices["HIFLD_ID"]
                logger.info("Using 'HIFLD_ID' as primary device key.")

            # 2) Secondary options
            elif "substation_id" in devices.columns:
                devices = devices.rename(columns={"substation_id": "id"})
            elif "OBJECTID" in devices.columns:
                devices["id"] = devices["OBJECTID"]
            else:
                logger.error(
                    "Devices CSV must have an ID column (HIFLD_ID, substation_id, or OBJECTID)."
                )
                raise KeyError("No usable ID column in devices CSV")

        devices["id"] = devices["id"].map(clean_substation_id)
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
            pga["id"] = pga["HIFLD_ID"]
            logger.info("load_pga: mapped 'HIFLD_ID' to 'id'")
        elif "substation_id" in pga.columns:
            pga = pga.rename(columns={"substation_id": "id"})
            logger.info("load_pga: mapped 'substation_id' to 'id'")
        elif "OBJECTID" in pga.columns:
            pga["id"] = pga["OBJECTID"]
            logger.info("load_pga: mapped 'OBJECTID' to 'id'")
        else:
            logger.error(f"PGA CSV missing ID column. Available: {list(pga.columns)}")
            raise KeyError("PGA CSV must have an ID column.")

    pga["id"] = pga["id"].map(clean_substation_id)

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
        mapping["substation_id"] = mapping["substation_id"].map(clean_substation_id)
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
    W_df.columns = W_df.columns.map(clean_substation_id)

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
            devices["id"] = devices[found]
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
    devices["id"] = devices["id"].map(clean_substation_id)
    pga["id"] = pga["id"].map(clean_substation_id)

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
    sub_index_str = [clean_substation_id(s) for s in sub_index]

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

    # 2) SciPy lognorm convention: scale = mu
    scales = mu_mat

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
    cfg: Config,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Map sampled damage states to initial functionality and repair times.
    """
    # 1) Init functionality @ t=0: use the manually specified DS residuals.
    func0_samples = np.full(ds_samples.shape, np.nan, dtype=float)
    for ds, val in INITIAL_FUNCTIONALITY_BY_DS.items():
        func0_samples[ds_samples == ds] = float(val)

    # 2) Repair time samples (hr)
    repair_time_samples = np.zeros_like(ds_samples, dtype=float)
    min_repair_time = 0

    for ds in range(1, 5):
        mask = (ds_samples == ds)
        n = int(mask.sum())
        if n <= 0:
            continue

        try:
            mean_hr, std_hr = REPAIR_PARAM_NORMAL_HR.get(ds, (np.nan, np.nan))
            mean_hr = float(mean_hr)
            std_hr  = float(std_hr)

            if std_hr <= 1e-9:
                samples = np.full(n, mean_hr, dtype=float)
            else:
                samples = rng.normal(loc=mean_hr, scale=std_hr, size=n)

            repair_time_samples[mask] = np.maximum(samples, min_repair_time)

        except Exception:
            raise ValueError(f"Invalid repair parameters for DS {ds}: mean={mean_hr}, std={std_hr}")

    return func0_samples, repair_time_samples


# Substation ID normalization utilities
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
            df[SUBSTATION_ID_CANON_COL] = df[col].map(clean_substation_id)
            return df

    raise KeyError(
        "No usable substation ID column found in devices_df. "
        f"Tried {SUBSTATION_ID_SOURCE_COLS}; available columns: {df.columns.tolist()}"
    )


def get_substation_id_array(df: pd.DataFrame) -> np.ndarray:
    """Return the standardized 'substation_id' array (string dtype)."""
    df = ensure_substation_id_col(df)
    return df[SUBSTATION_ID_CANON_COL].values


def clean_substation_id(value: Any) -> str:
    """Normalize ID values imported from CSVs without changing substantive digits."""
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "<na>"}:
        return ""
    try:
        f = float(s)
        if np.isfinite(f) and f.is_integer():
            return str(int(f))
    except Exception:
        pass
    if s.endswith(".0"):
        return s[:-2]
    return s


def load_source_role_table(cfg: Config, sub_index: Optional[pd.Index] = None) -> pd.DataFrame:
    """
    Read the project source-node table once and expose common role fields.

    Returns columns:
        - substation_id
        - role_key
        - role_text
        - is_source
        - source_role_score
    """
    logger = logging.getLogger()
    source_path = Path(getattr(cfg, "SOURCE_NODES_CSV", ""))
    empty = pd.DataFrame(
        columns=["substation_id", "role_key", "role_text", "is_source", "source_role_score"]
    )

    if not source_path.exists():
        logger.warning("Source role table not found: %s", source_path)
        return empty

    try:
        source_df = pd.read_csv(source_path)
    except Exception as e:
        logger.warning("Failed to read source role table %s: %s", source_path, e)
        return empty

    id_col = next(
        (
            c
            for c in ["substation_id", "HIFLD_ID", "ID", "id", "node_id"]
            if c in source_df.columns
        ),
        None,
    )
    if id_col is None:
        logger.warning("Source role table missing usable ID column: %s", source_path)
        return empty

    role_candidates = ["level", "role", "source_level", "source_type", "active_set"]
    role_cols = [c for c in role_candidates if c in source_df.columns]

    role_text = pd.Series("", index=source_df.index, dtype="object")
    for col in role_cols:
        role_text = role_text + " " + source_df[col].astype(str).str.lower()

    if role_cols:
        role_key_col = next((c for c in role_candidates if c in source_df.columns), role_cols[0])
        role_key = source_df[role_key_col].astype(str).str.strip().str.lower()
    else:
        role_key = pd.Series("", index=source_df.index, dtype="object")

    is_source = (
        role_text.str.contains("core", na=False)
        | role_text.str.contains("import_interface_proxy", na=False)
        | role_text.str.contains("in_basin_generation_proxy", na=False)
    )
    is_source &= ~role_text.str.contains("transit_hub_not_source|\\btransit\\b", na=False)

    role_map = {
        "core": 1.0,
        "transit": 0.60,
        "import_interface_proxy": 1.0,
        "in_basin_generation_proxy": 1.0,
        "transit_hub_not_source": 0.60,
    }
    role_score = role_key.map(role_map)
    role_score = role_score.where(~role_score.isna(), np.where(is_source, 1.0, np.nan))
    role_score = pd.Series(role_score, index=source_df.index).fillna(0.0).astype(float)

    out = pd.DataFrame(
        {
            "substation_id": source_df[id_col].map(clean_substation_id),
            "role_key": role_key,
            "role_text": role_text.str.strip(),
            "is_source": is_source.astype(bool),
            "source_role_score": role_score,
        }
    )
    out = out[out["substation_id"].astype(bool)].drop_duplicates("substation_id").copy()

    if sub_index is not None:
        valid_ids = {clean_substation_id(x) for x in sub_index}
        missing_ids = sorted(set(out["substation_id"]) - valid_ids)
        if missing_ids:
            logger.info("Source role table: %d IDs absent from active substation universe.", len(missing_ids))
        out = out[out["substation_id"].isin(valid_ids)].copy()

    return out


def load_source_gate_nodes(cfg: Config, sub_index: Optional[pd.Index] = None) -> set[str]:
    """
    Load source/generation/import nodes used to gate delivered functionality.

    The project has used two source-table schemas: the city-scale file has
    ``node_id`` plus ``active_set=core``; the expanded file has ``ID`` plus
    ``level=Core``. This helper accepts both and treats only core/import/
    generation rows as energizing sources.
    """
    logger = logging.getLogger()
    role_df = load_source_role_table(cfg, sub_index=sub_index)
    source_ids = set(role_df.loc[role_df["is_source"], "substation_id"])
    logger.debug("Source gate: loaded %d active source nodes.", len(source_ids))
    return source_ids


def apply_source_gate_to_substation_series(
    sub_series_df: pd.DataFrame,
    G: nx.Graph,
    cfg: Config,
    source_ids: Optional[set[str]] = None,
    label: str = "",
) -> pd.DataFrame:
    """
    Zero substation functionality unless it belongs to an energized source island.

    At each timestep, nodes with functionality >= cfg.FUNCTIONAL_THRESHOLD form
    the functional transmission subgraph. Only components containing at least
    one active source node are allowed to deliver functionality downstream.
    """
    logger = logging.getLogger()
    if not getattr(cfg, "SOURCE_GATE_ENABLED", True):
        return sub_series_df
    if sub_series_df.empty or G is None or G.number_of_nodes() == 0:
        return sub_series_df

    columns_norm = [clean_substation_id(c) for c in sub_series_df.columns]
    col_index = pd.Index(columns_norm)

    if source_ids is None:
        source_ids = load_source_gate_nodes(cfg, pd.Index(columns_norm))
    source_ids = {sid for sid in (clean_substation_id(s) for s in source_ids) if sid}

    G_norm = nx.relabel_nodes(G, lambda n: clean_substation_id(n), copy=True)
    graph_nodes = {n for n in G_norm.nodes() if n}
    valid_sources = source_ids & graph_nodes & set(columns_norm)
    if not valid_sources:
        logger.warning(
            "Source gate%s: no valid source nodes overlap the recovery series and graph; "
            "leaving functionality ungated.",
            f" ({label})" if label else "",
        )
        return sub_series_df

    threshold = float(getattr(cfg, "FUNCTIONAL_THRESHOLD", 0.5))
    values = sub_series_df.to_numpy(dtype=float, copy=True)
    raw_values = values.copy()
    valid_col_mask = np.array([c in graph_nodes for c in columns_norm], dtype=bool)
    gate_cache: Dict[Tuple[str, ...], Tuple[np.ndarray, int, int]] = {}

    first_active_sources = 0
    first_kept_nodes = 0
    last_active_sources = 0
    last_kept_nodes = 0

    for row_idx in range(values.shape[0]):
        functional_mask = (values[row_idx, :] >= threshold) & valid_col_mask
        functional_nodes = tuple(col_index[functional_mask])

        cached = gate_cache.get(functional_nodes)
        if cached is None:
            functional_set = set(functional_nodes)
            active_sources = valid_sources & functional_set
            keep_nodes: set[str] = set()

            if active_sources:
                G_t = G_norm.subgraph(functional_set)
                for component in nx.connected_components(G_t):
                    if active_sources.intersection(component):
                        keep_nodes.update(component)

            keep_mask = np.array([c in keep_nodes for c in columns_norm], dtype=bool)
            cached = (keep_mask, len(active_sources), len(keep_nodes))
            gate_cache[functional_nodes] = cached

        keep_mask, active_source_count, kept_node_count = cached
        values[row_idx, ~keep_mask] = 0.0

        if row_idx == 0:
            first_active_sources = active_source_count
            first_kept_nodes = kept_node_count
        last_active_sources = active_source_count
        last_kept_nodes = kept_node_count

    label_text = f" ({label})" if label else ""
    log_source_gate = logger.info if str(label).startswith("Stage3") else logger.debug
    log_source_gate(
        "Source gate%s: sources=%d, t0_active_sources=%d, t0_source_connected_nodes=%d, "
        "final_active_sources=%d, final_source_connected_nodes=%d, mean_t0 %.3f->%.3f",
        label_text,
        len(valid_sources),
        first_active_sources,
        first_kept_nodes,
        last_active_sources,
        last_kept_nodes,
        float(np.nanmean(raw_values[0, :])) if raw_values.size else 0.0,
        float(np.nanmean(values[0, :])) if values.size else 0.0,
    )

    return pd.DataFrame(values, index=sub_series_df.index, columns=sub_series_df.columns)


def apply_source_gate_to_initial_functionality_samples(
    func0_samples: np.ndarray,
    sub_ids: np.ndarray,
    G: nx.Graph,
    cfg: Config,
    source_ids: Optional[set[str]] = None,
) -> np.ndarray:
    """
    Apply the same active-source island gate used by recovery stages to Stage 1
    Monte Carlo initial functionality samples.

    Input shape is (n_substations, n_samples). The source-gate helper works on
    row-wise time/sample frames, so we transpose to samples x substations and
    transpose back after gating.
    """
    if not getattr(cfg, "SOURCE_GATE_ENABLED", True):
        return func0_samples
    if G is None or G.number_of_nodes() == 0:
        return func0_samples
    if func0_samples.size == 0:
        return func0_samples

    sample_df = pd.DataFrame(
        func0_samples.T,
        columns=[clean_substation_id(s) for s in sub_ids],
    )
    gated_df = apply_source_gate_to_substation_series(
        sample_df,
        G,
        cfg,
        source_ids=source_ids,
        label="Stage1",
    )
    return gated_df.to_numpy(dtype=float).T


def _process_mc_chunk(
    scenario,
    pga_series,
    devices_df,
    W_mat,
    tract_index,
    n_chunk,
    rng_seed,
    cfg,
    source_gate_graph=None,
    source_ids=None,
):
    """Helper function for parallel MC processing with voltage-dependent redundancy."""
    rng = np.random.default_rng(rng_seed)
    n_devices = len(devices_df)

    # --- Generate samples for this chunk ------------------------------------
    ds_samples = sample_damage_states(pga_series, devices_df, n_chunk, rng)

    # DS -> (func0, repair_time)
    func0_samples, repair_time_samples = damage_to_functionality_and_repair(
        ds_samples,
        rng,
        cfg,
    )
    sub_ids = get_substation_id_array(devices_df)
    func0_samples = apply_source_gate_to_initial_functionality_samples(
        func0_samples,
        sub_ids,
        source_gate_graph,
        cfg,
        source_ids=source_ids,
    )

    # --- Device-level aggregation -------------------------------------------
    # Mean DS per device over this chunk (memory-saving)
    ds_avg_chunk = ds_samples.mean(axis=1)

    # Mean t=0 functionality per device over this chunk (new)
    func0_avg_chunk = func0_samples.mean(axis=1)

    # --- Tract-level aggregation --------------------------------------------
    # (n_tracts, n_devices) @ (n_devices, n_chunk) -> (n_tracts, n_chunk)
    S_t_samples = W_mat @ func0_samples
    tract_supply_chunk = S_t_samples.mean(axis=1)

    # --- Records ------------------------------------------------------------
    mc_ids = (
        np.arange(n_chunk, dtype=np.uint32)
        .reshape(1, -1)
        .repeat(n_devices, axis=0)
    )

    sub_ids_rep = np.repeat(sub_ids.reshape(-1, 1), n_chunk, axis=1)

    device_records_df = pd.DataFrame(
        {
            "scenario": scenario,
            "mc_id": mc_ids.ravel(),
            "substation_id": sub_ids_rep.ravel(),
            "damage_state": ds_samples.ravel(),
            "init_func0": func0_samples.ravel(), 
            "repair_time_hr": repair_time_samples.ravel(),
        }
    )

    return (
        device_records_df,
        ds_avg_chunk,
        func0_avg_chunk,  
        tract_supply_chunk,
        repair_time_samples,
    )


def run_stage_1(cfg: Config, stage_0_data: Dict, out_dirs: Dict) -> Dict:
    """Orchestrate Stage 1 Monte Carlo fragility sampling (Joblib parallel)."""
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
        devices_merged["substation_id"].map(clean_substation_id),
        name="substation_id",
    )

    source_gate_graph = nx.Graph()
    source_ids: set[str] = set()
    if getattr(cfg, "SOURCE_GATE_ENABLED", True):
        source_gate_graph = build_base_graph(cfg, devices_merged, sub_index)
        source_ids = load_source_gate_nodes(cfg, sub_index)
        if source_gate_graph.number_of_nodes() > 0 and source_ids:
            logger.info(
                "Stage 1 source gate enabled for initial supply: %d active source nodes, graph=%d nodes/%d edges.",
                len(source_ids),
                source_gate_graph.number_of_nodes(),
                source_gate_graph.number_of_edges(),
            )
        else:
            logger.warning(
                "Stage 1 source gate requested but graph/source nodes are unavailable; "
                "initial supply will remain fragility-only."
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

    all_mc_repair_times = {}
    all_mean_func0 = {} 
    for scenario in cfg.SCENARIOS:
        logger.info(f"Processing scenario: {scenario}...")

        pga_col = f"pga_{scenario}"

        scen_key = str(scenario).lower()
        use_new_fragility = ("2pc" in scen_key)
        devices_scen = devices_merged.copy()
        if use_new_fragility:
            pass
        else:
            for ds in range(1, 5):
                devices_scen[f"mu_DS{ds}"] = devices_scen[f"mu_DS{ds}_old"]
                devices_scen[f"beta_DS{ds}"] = devices_scen[f"beta_DS{ds}_old"]

        pga_series = devices_scen[pga_col]

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
                devices_scen,
                W_mat,
                tract_index,
                n_chunk,
                seed,
                cfg,
                source_gate_graph,
                source_ids,
            )
            for n_chunk, seed in zip(chunks, chunk_seeds)
        )

        # --- Unpack and aggregate chunk results --------------------------------
        device_records_list = [r[0] for r in results]
        ds_avg_chunks       = np.stack([r[1] for r in results], axis=1)
        func0_avg_chunks    = np.stack([r[2] for r in results], axis=1)
        tract_supply_chunks = np.stack([r[3] for r in results], axis=1)
        repair_time_chunks  = [r[4] for r in results]

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
        logger.debug("Saved device records: %s", out_path)

        # Free memory
        del device_records_df, device_records_list

        # --- 2a) MC_Device_Damage_AvgDS_<scenario>.csv ---------------------------
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

        # --- 2b) MC_Device_InitFuncMean_<scenario>.csv --------------------------
        device_mean_func0 = np.average(func0_avg_chunks, axis=1, weights=weights)

        df_init = pd.DataFrame(
            {
                "substation_id": sub_index,
                "scenario": scenario,
                "mean_func0": device_mean_func0,
            }
        )

        out_path = out_dirs["STAGE1_DIR"] / f"MC_Device_InitFuncMean_{scenario}.csv"
        df_init.to_csv(out_path, index=False)
        logger.debug("Saved init func mean: %s", out_path)

        all_mean_func0[scenario] = device_mean_func0

        # --- 3) MC_Tract_Supply_<scenario>.csv ------------------------------
        tract_supply = np.average(tract_supply_chunks, axis=1, weights=weights)
        df_tract_supply = pd.DataFrame(
            {
                "tract_id": tract_index,
                "scenario": scenario,
                "supply": tract_supply,
            }
        )

        out_path = out_dirs["STAGE1_DIR"] / f"MC_Tract_Supply_{scenario}.csv"
        df_tract_supply.to_csv(out_path, index=False)

        # --- 4) Store full repair time samples ----------------------
        all_mc_repair_times[scenario] = np.concatenate(repair_time_chunks, axis=1)
        logger.info("Aggregated Stage 1 results for %s.", scenario)

    logger.info("--- STAGE 1 Complete ---")
    return {"all_mc_repair_times": all_mc_repair_times, "all_mean_func0": all_mean_func0}


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

        edf["u"] = edf["u"].map(clean_substation_id)
        edf["v"] = edf["v"].map(clean_substation_id)

        # 3) Build full multigraph
        G_full = nx.from_pandas_edgelist(
            edf,
            source="u",
            target="v",
            edge_attr=["length_km"],
            create_using=nx.MultiGraph(),
        )

        # 4) Filter to device IDs (intersection: in edge list AND in device inventory)
        sub_index_set = {clean_substation_id(s) for s in sub_index}
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
                    ndf[id_col] = ndf[id_col].map(clean_substation_id)
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
    nodes_all = [clean_substation_id(n) for n in G.nodes()]

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
    m["substation_id"] = m["substation_id"].map(clean_substation_id)
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


def export_graph_sanity_diagnostics(
    G: nx.Graph,
    out_dir: Path,
    cfg: Optional[Config] = None,
    devices_df: Optional[pd.DataFrame] = None,
) -> None:
    """Export compact topology sanity checks for the prebuilt substation graph."""
    logger = logging.getLogger()
    out_dir = Path(out_dir)

    degree = pd.Series(dict(G.degree()), name="degree").astype(float)
    degree_summary = pd.DataFrame(
        {
            "metric": ["count", "min", "p25", "median", "p75", "p90", "p95", "max", "mean"],
            "degree": [
                float(degree.count()),
                float(degree.min()) if len(degree) else np.nan,
                float(degree.quantile(0.25)) if len(degree) else np.nan,
                float(degree.quantile(0.50)) if len(degree) else np.nan,
                float(degree.quantile(0.75)) if len(degree) else np.nan,
                float(degree.quantile(0.90)) if len(degree) else np.nan,
                float(degree.quantile(0.95)) if len(degree) else np.nan,
                float(degree.max()) if len(degree) else np.nan,
                float(degree.mean()) if len(degree) else np.nan,
            ],
        }
    )
    degree_summary.to_csv(out_dir / "graph_degree_summary.csv", index=False)

    degree_dist = (
        degree.astype(int)
        .value_counts()
        .sort_index()
        .rename_axis("degree")
        .reset_index(name="n_nodes")
    )
    degree_dist["share_nodes"] = degree_dist["n_nodes"] / max(G.number_of_nodes(), 1)
    degree_dist.to_csv(out_dir / "graph_degree_distribution.csv", index=False)

    node_degree = degree.sort_values(ascending=False).rename_axis("substation_id").reset_index()
    node_degree.to_csv(out_dir / "graph_node_degree_rank.csv", index=False)

    edge_rows = []
    for u, v, attrs in G.edges(data=True):
        length_km = pd.to_numeric(attrs.get("length_km", np.nan), errors="coerce")
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        u_lat = pd.to_numeric(u_data.get("lat", np.nan), errors="coerce")
        u_lon = pd.to_numeric(u_data.get("lon", np.nan), errors="coerce")
        v_lat = pd.to_numeric(v_data.get("lat", np.nan), errors="coerce")
        v_lon = pd.to_numeric(v_data.get("lon", np.nan), errors="coerce")

        straight_km = np.nan
        if np.isfinite(u_lat) and np.isfinite(u_lon) and np.isfinite(v_lat) and np.isfinite(v_lon):
            try:
                straight_km = geodesic((u_lat, u_lon), (v_lat, v_lon)).km
            except Exception:
                straight_km = np.nan

        edge_rows.append(
            {
                "u": u,
                "v": v,
                "length_km": float(length_km) if np.isfinite(length_km) else np.nan,
                "straight_line_km": float(straight_km) if np.isfinite(straight_km) else np.nan,
                "length_to_straight_ratio": (
                    float(length_km) / float(straight_km)
                    if np.isfinite(length_km) and np.isfinite(straight_km) and straight_km > 0
                    else np.nan
                ),
                "u_degree": int(G.degree(u)),
                "v_degree": int(G.degree(v)),
            }
        )

    edge_df = pd.DataFrame(edge_rows)
    if edge_df.empty:
        logger.warning("Graph sanity diagnostics: no edges available for length checks.")
        return

    lengths = pd.to_numeric(edge_df["length_km"], errors="coerce").dropna()
    length_summary = pd.DataFrame(
        {
            "metric": ["count", "min", "p25", "median", "p75", "p90", "p95", "p99", "max", "mean"],
            "length_km": [
                float(lengths.count()),
                float(lengths.min()) if len(lengths) else np.nan,
                float(lengths.quantile(0.25)) if len(lengths) else np.nan,
                float(lengths.quantile(0.50)) if len(lengths) else np.nan,
                float(lengths.quantile(0.75)) if len(lengths) else np.nan,
                float(lengths.quantile(0.90)) if len(lengths) else np.nan,
                float(lengths.quantile(0.95)) if len(lengths) else np.nan,
                float(lengths.quantile(0.99)) if len(lengths) else np.nan,
                float(lengths.max()) if len(lengths) else np.nan,
                float(lengths.mean()) if len(lengths) else np.nan,
            ],
        }
    )
    length_summary.to_csv(out_dir / "graph_edge_length_summary.csv", index=False)

    bins = [0, 1, 2, 5, 10, 20, 50, 100, 200, np.inf]
    edge_df["length_bin_km"] = pd.cut(
        edge_df["length_km"],
        bins=bins,
        right=False,
        labels=["0-1", "1-2", "2-5", "5-10", "10-20", "20-50", "50-100", "100-200", "200+"],
    )
    length_dist = (
        edge_df.groupby("length_bin_km", observed=False)
        .size()
        .reset_index(name="n_edges")
    )
    length_dist["share_edges"] = length_dist["n_edges"] / max(G.number_of_edges(), 1)
    length_dist.to_csv(out_dir / "graph_edge_length_distribution.csv", index=False)

    top_links = edge_df.sort_values("length_km", ascending=False).head(25)
    top_links.to_csv(out_dir / "graph_top_links_sanity.csv", index=False)

    node_ids = [clean_substation_id(n) for n in G.nodes()]
    node_attrs = node_degree.copy()
    node_attrs["substation_id"] = node_attrs["substation_id"].map(clean_substation_id)

    if devices_df is not None and not devices_df.empty:
        try:
            dev = ensure_substation_id_col(devices_df.copy())
            keep_cols = [
                c
                for c in ["substation_id", "NAME", "CITY", "Owner", "MAX_VOLT", "LINES"]
                if c in dev.columns
            ]
            dev = dev[keep_cols].drop_duplicates("substation_id")
            node_attrs = node_attrs.merge(dev, on="substation_id", how="left")
        except Exception as e:
            logger.warning("Graph hub sanity: failed to attach device attributes: %s", e)

    if cfg is not None:
        roles = load_source_role_table(cfg, sub_index=pd.Index(node_ids))
        if not roles.empty:
            roles = roles[["substation_id", "role_key", "role_text", "is_source", "source_role_score"]]
            node_attrs = node_attrs.merge(roles, on="substation_id", how="left")

    for col in ["MAX_VOLT", "LINES"]:
        if col not in node_attrs.columns:
            node_attrs[col] = np.nan
    if "role_text" not in node_attrs.columns:
        node_attrs["role_text"] = ""

    node_attrs["MAX_VOLT_N"] = pd.to_numeric(node_attrs["MAX_VOLT"], errors="coerce")
    node_attrs["LINES_N"] = pd.to_numeric(node_attrs["LINES"], errors="coerce")
    role_text = node_attrs["role_text"].fillna("").astype(str).str.lower()
    node_attrs["is_role_hub"] = role_text.str.contains("core|transit|import_interface|generation", na=False)
    node_attrs["is_voltage_hub"] = node_attrs["MAX_VOLT_N"] >= 138
    node_attrs["is_line_hub"] = node_attrs["LINES_N"] >= 6
    node_attrs["hub_evidence_count"] = node_attrs[["is_role_hub", "is_voltage_hub", "is_line_hub"]].sum(axis=1)
    node_attrs["sanity_flag"] = "ok"
    suspicious_mask = (node_attrs["degree"] >= 20) & (node_attrs["hub_evidence_count"] == 0)
    mixed_mask = (node_attrs["degree"] >= 20) & (node_attrs["hub_evidence_count"] == 1)
    node_attrs.loc[suspicious_mask, "sanity_flag"] = "suspicious_high_degree_low_hub_evidence"
    node_attrs.loc[mixed_mask, "sanity_flag"] = "mixed_evidence"
    node_attrs.to_csv(out_dir / "graph_hub_sanity_rank.csv", index=False)

    sensitivity_thresholds = [None, 20.0, 25.0, 30.0, 35.0, 40.0, 50.0]
    sensitivity_rows = []
    sensitivity_top_rows = []
    for threshold in sensitivity_thresholds:
        label = "none" if threshold is None else f"le_{threshold:g}km"
        H = nx.Graph()
        H.add_nodes_from(G.nodes())
        for u, v, attrs in G.edges(data=True):
            length_val = pd.to_numeric(attrs.get("length_km", np.nan), errors="coerce")
            if threshold is None or (np.isfinite(length_val) and float(length_val) <= threshold):
                H.add_edge(u, v)

        sens_degree = (
            pd.Series(dict(H.degree()), name="degree")
            .rename_axis("substation_id")
            .reset_index()
        )
        sens_degree["substation_id"] = sens_degree["substation_id"].map(clean_substation_id)
        sens_attrs = sens_degree.merge(
            node_attrs.drop(columns=["degree"], errors="ignore"),
            on="substation_id",
            how="left",
        ).sort_values("degree", ascending=False)

        sens_attrs["threshold"] = label
        sens_attrs["sanity_flag"] = "ok"
        sens_suspicious = (sens_attrs["degree"] >= 20) & (sens_attrs["hub_evidence_count"] == 0)
        sens_mixed = (sens_attrs["degree"] >= 20) & (sens_attrs["hub_evidence_count"] == 1)
        sens_attrs.loc[sens_suspicious, "sanity_flag"] = "suspicious_high_degree_low_hub_evidence"
        sens_attrs.loc[sens_mixed, "sanity_flag"] = "mixed_evidence"
        high = sens_attrs[sens_attrs["degree"] >= 20]
        components = sorted((len(c) for c in nx.connected_components(H)), reverse=True)
        top10 = sens_attrs.head(10)

        sensitivity_rows.append(
            {
                "threshold": label,
                "max_dist_km": "" if threshold is None else threshold,
                "n_nodes": H.number_of_nodes(),
                "n_edges": H.number_of_edges(),
                "n_components": nx.number_connected_components(H) if H.number_of_nodes() else 0,
                "largest_component_nodes": components[0] if components else 0,
                "second_component_nodes": components[1] if len(components) > 1 else 0,
                "isolates": nx.number_of_isolates(H),
                "mean_degree": float(np.mean([d for _, d in H.degree()])) if H.number_of_nodes() else 0.0,
                "median_degree": float(sens_attrs["degree"].median()) if len(sens_attrs) else np.nan,
                "p90_degree": float(sens_attrs["degree"].quantile(0.90)) if len(sens_attrs) else np.nan,
                "max_degree": int(sens_attrs["degree"].max()) if len(sens_attrs) else 0,
                "nodes_degree_ge20": int(len(high)),
                "suspicious_degree_ge20": int((high["hub_evidence_count"] == 0).sum()),
                "mixed_degree_ge20": int((high["hub_evidence_count"] == 1).sum()),
                "top10_hub_evidence_ge2": int((top10["hub_evidence_count"] >= 2).sum()),
                "top10_names": "; ".join(top10.get("NAME", top10["substation_id"]).fillna("").astype(str)),
            }
        )
        sensitivity_top_rows.append(sens_attrs.head(30))

    pd.DataFrame(sensitivity_rows).to_csv(
        out_dir / "graph_direct_link_length_sensitivity.csv",
        index=False,
    )
    pd.concat(sensitivity_top_rows, ignore_index=True).to_csv(
        out_dir / "graph_direct_link_length_sensitivity_top30.csv",
        index=False,
    )

    logger.info(
        "Graph sanity diagnostics saved: max degree=%s, median edge=%.2f km, p95 edge=%.2f km, max edge=%.2f km.",
        int(degree.max()) if len(degree) else 0,
        float(lengths.quantile(0.50)) if len(lengths) else np.nan,
        float(lengths.quantile(0.95)) if len(lengths) else np.nan,
        float(lengths.max()) if len(lengths) else np.nan,
    )


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
        devices_merged["substation_id"].map(clean_substation_id),
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

    export_graph_sanity_diagnostics(G, out_dir, cfg=cfg, devices_df=devices_merged)

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
# [PART 5] Stage 3: MC Source-Gated Recovery Simulation
# =============================================================================
# Contains: MC damage-state recovery, KPIs (T50/T80), Graph Robustness, run_stage_3


def _damage_records_to_state_matrix(
    df_recs: pd.DataFrame,
    sub_index: pd.Index,
) -> np.ndarray:
    """
    Convert long-form Stage 1 MC damage records into a substation x MC matrix.

    The Stage 1 writer keeps ``mc_id`` aligned across substations, so each
    matrix column is one Monte Carlo realization over the full network.
    """
    if not {"substation_id", "mc_id", "damage_state"}.issubset(df_recs.columns):
        raise ValueError("Damage records must contain substation_id, mc_id, and damage_state columns.")

    recs = df_recs[["substation_id", "mc_id", "damage_state"]].copy()
    recs["substation_id"] = recs["substation_id"].map(clean_substation_id)
    recs["mc_id"] = pd.to_numeric(recs["mc_id"], errors="coerce").astype("Int64")
    recs = recs.dropna(subset=["mc_id"])
    recs["mc_id"] = recs["mc_id"].astype(int)

    ds_matrix_df = recs.pivot_table(
        index="substation_id",
        columns="mc_id",
        values="damage_state",
        aggfunc="first",
    )
    ds_matrix_df = ds_matrix_df.reindex(
        index=[clean_substation_id(s) for s in sub_index],
        columns=sorted(ds_matrix_df.columns),
    )
    if ds_matrix_df.isna().any().any():
        missing = int(ds_matrix_df.isna().sum().sum())
        raise ValueError(f"Damage-state matrix has {missing} missing substation/MC entries.")

    return ds_matrix_df.to_numpy(dtype=np.int8)


def _precompute_ds_recovery_curves(
    t_grid: np.ndarray,
    sub_index: pd.Index,
    start_times: Optional[np.ndarray] = None,
    method: str = "normal",
) -> np.ndarray:
    """Precompute one recovery curve per damage state and substation."""
    n_time = len(t_grid)
    n_subs = len(sub_index)

    if start_times is None:
        start_times = np.zeros(n_subs)
    start_times = np.asarray(start_times, dtype=float)
    if start_times.shape[0] != n_subs:
        raise ValueError(f"start_times length {start_times.shape[0]} != n_subs {n_subs}")

    t_eff_matrix = t_grid[:, np.newaxis] - start_times[np.newaxis, :]
    t_eff_matrix = np.maximum(t_eff_matrix, 1e-9)

    curves = np.zeros((5, n_time, n_subs), dtype=np.float32)
    curves[0, :, :] = 1.0

    ds_params = REPAIR_PARAM_LOGNORMAL if method == "lognormal" else REPAIR_PARAM_NORMAL_HR
    for ds in range(1, 5):
        params = ds_params.get(ds)
        if params is None:
            continue
        p1, p2 = params
        if method == "lognormal":
            raw_cdf_vals = lognorm.cdf(t_eff_matrix, s=p2, scale=p1)
            cdf_at_zero = float(lognorm.cdf(0.0, s=p2, scale=p1))
        elif method == "normal":
            raw_cdf_vals = norm.cdf(t_eff_matrix, loc=p1, scale=p2)
            cdf_at_zero = float(norm.cdf(0.0, loc=p1, scale=p2))
        else:
            raise ValueError(f"Unknown method: {method}")

        init_func = float(INITIAL_FUNCTIONALITY_BY_DS.get(ds, 0.0))
        denom = max(1.0 - cdf_at_zero, 1e-12)
        progress_vals = np.clip((raw_cdf_vals - cdf_at_zero) / denom, 0.0, 1.0)
        curves[ds, :, :] = (init_func + (1.0 - init_func) * progress_vals).astype(np.float32)

    return np.clip(curves, 0.0, 1.0)


def simulate_recovery_mc_source_gated(
    t_grid: np.ndarray,
    sub_index: pd.Index,
    damage_state_samples: np.ndarray,
    G: nx.Graph,
    cfg: Config,
    source_ids: Optional[set[str]] = None,
    start_times: Optional[np.ndarray] = None,
    method: str = "normal",
    label: str = "",
) -> pd.DataFrame:
    """
    Estimate mean recovery as E[gate(F_run(t))] from MC damage realizations.

    The energized island test is evaluated separately for each Monte Carlo
    realization and each recovery time step before averaging.
    """
    logger = logging.getLogger()
    sub_index = pd.Index([clean_substation_id(s) for s in sub_index], name="substation_id")
    ds_arr = np.asarray(damage_state_samples, dtype=np.int8)
    n_subs = len(sub_index)
    if ds_arr.ndim != 2:
        raise ValueError("damage_state_samples must be a 2D substation x MC matrix.")
    if ds_arr.shape[0] != n_subs and ds_arr.shape[1] == n_subs:
        ds_arr = ds_arr.T
    if ds_arr.shape[0] != n_subs:
        raise ValueError(f"damage_state_samples shape {ds_arr.shape} incompatible with {n_subs} substations.")

    n_mc = int(ds_arr.shape[1])
    n_time = len(t_grid)
    curves_by_ds = _precompute_ds_recovery_curves(
        t_grid,
        sub_index,
        start_times=start_times,
        method=method,
    )

    source_gate_enabled = bool(getattr(cfg, "SOURCE_GATE_ENABLED", True))
    columns_norm = [clean_substation_id(s) for s in sub_index]
    G_norm = nx.relabel_nodes(G, lambda n: clean_substation_id(n), copy=True) if G is not None else nx.Graph()
    graph_nodes = {n for n in G_norm.nodes() if n}
    if source_ids is None:
        source_ids = load_source_gate_nodes(cfg, pd.Index(columns_norm))
    valid_sources = {clean_substation_id(s) for s in source_ids} & graph_nodes & set(columns_norm)
    valid_col_mask = np.array([c in graph_nodes for c in columns_norm], dtype=bool)

    if source_gate_enabled and not valid_sources:
        logger.warning(
            "MC source gate%s: no valid source nodes overlap graph/substations; leaving recovery ungated.",
            f" ({label})" if label else "",
        )
        source_gate_enabled = False

    node_pos = {sid: i for i, sid in enumerate(columns_norm)}
    gate_cache: Dict[bytes, np.ndarray] = {}

    def _keep_mask_for_functional(functional_mask: np.ndarray) -> np.ndarray:
        key = functional_mask.tobytes()
        cached = gate_cache.get(key)
        if cached is not None:
            return cached

        functional_mask = functional_mask & valid_col_mask
        functional_nodes = [columns_norm[i] for i in np.flatnonzero(functional_mask)]
        active_sources = valid_sources & set(functional_nodes)
        keep = np.zeros(n_subs, dtype=bool)

        if active_sources:
            G_t = G_norm.subgraph(functional_nodes)
            for component in nx.connected_components(G_t):
                if active_sources.intersection(component):
                    for node in component:
                        pos = node_pos.get(node)
                        if pos is not None:
                            keep[pos] = True

        gate_cache[key] = keep
        return keep

    threshold = float(getattr(cfg, "FUNCTIONAL_THRESHOLD", 0.5))
    crossing_idx_by_ds = np.full((5, n_subs), n_time, dtype=np.int32)
    for ds in range(5):
        crosses = curves_by_ds[ds, :, :] >= threshold
        has_crossing = crosses.any(axis=0)
        if np.any(has_crossing):
            crossing_idx_by_ds[ds, has_crossing] = np.argmax(crosses[:, has_crossing], axis=0)

    sub_positions = np.arange(n_subs)
    mc_source_gate_n_jobs = int(getattr(cfg, "MC_SOURCE_GATE_N_JOBS", 1) or 1)
    if mc_source_gate_n_jobs < 0:
        mc_source_gate_n_jobs = os.cpu_count() or 1
    mc_source_gate_n_jobs = max(1, min(mc_source_gate_n_jobs, n_mc))

    def _process_mc_range(mc_start: int, mc_stop: int) -> tuple[np.ndarray, int]:
        local_sum = np.zeros((n_time, n_subs), dtype=np.float64)
        for mc_idx in range(mc_start, mc_stop):
            ds_vec = ds_arr[:, mc_idx]

            if not source_gate_enabled:
                local_sum += curves_by_ds[ds_vec, :, sub_positions].T
                continue

            crossing_idx = crossing_idx_by_ds[ds_vec, sub_positions]
            event_idxs = np.unique(crossing_idx[crossing_idx < n_time])
            if len(event_idxs) == 0:
                continue

            for event_pos, time_start in enumerate(event_idxs):
                time_stop = int(event_idxs[event_pos + 1]) if event_pos + 1 < len(event_idxs) else n_time
                time_start = int(time_start)
                if time_start >= time_stop:
                    continue
                functional_mask = crossing_idx <= time_start
                keep_mask = _keep_mask_for_functional(functional_mask)
                if np.any(keep_mask):
                    local_sum[time_start:time_stop, :] += (
                        curves_by_ds[ds_vec, time_start:time_stop, sub_positions].T * keep_mask
                    )
        return local_sum, len(gate_cache)

    if mc_source_gate_n_jobs == 1:
        sum_recovery, _ = _process_mc_range(0, n_mc)
    else:
        chunk_edges = np.linspace(0, n_mc, mc_source_gate_n_jobs + 1, dtype=int)
        ranges = [
            (int(chunk_edges[i]), int(chunk_edges[i + 1]))
            for i in range(mc_source_gate_n_jobs)
            if chunk_edges[i] < chunk_edges[i + 1]
        ]
        results = Parallel(n_jobs=len(ranges))(
            delayed(_process_mc_range)(mc_start, mc_stop)
            for mc_start, mc_stop in ranges
        )
        sum_recovery = np.sum([item[0] for item in results], axis=0)

    mean_recovery = sum_recovery / max(n_mc, 1)
    logger.debug(
        "MC source-gated recovery%s complete: n_mc=%d, n_time=%d, cached_gate_masks=%d.",
        f" ({label})" if label else "",
        n_mc,
        n_time,
        len(gate_cache),
    )
    return pd.DataFrame(np.clip(mean_recovery, 0.0, 1.0), index=t_grid, columns=sub_index)


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
    logger.debug("Computing dynamic graph robustness (Metric: Average Degree)...")

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
            func_mask = sub_series_filtered.loc[t] >= cfg.FUNCTIONAL_THRESHOLD
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
    cfg: Config,
    stage_1_data: Dict,
    stage_0_data: Dict,
    stage_2_data: Dict,
    out_dirs: Dict,
) -> Dict:
    """
    Orchestrate Stage 3: MC source-gated probabilistic restoration.

    Logic:
    1. Reads raw Stage 1 MC damage-state samples.
    2. Builds DS-specific Hazus recovery curves for each realization.
    3. Applies the active-source island gate per realization and timestep.
    4. Averages the gated realizations into the substation recovery series.
    """
    if not cfg.RUN_STAGE_3:
        logging.info("--- STAGE 3: Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 3: MC Source-Gated Hazus Recovery ---")

    # --- 1. Validation & Setup ---
    # We still check for Stage 1 inputs, though we primarily read from disk now.
    if "all_mc_repair_times" not in stage_1_data:
         logger.warning("Stage 1 'all_mc_repair_times' not found in memory. Ensure Stage 1 ran.")

    W_mat = stage_0_data["W_mat"]
    tract_index = stage_0_data["tract_index"]
    sub_index = stage_0_data["sub_index"]
    G = stage_2_data.get("G", nx.Graph())
    source_ids = load_source_gate_nodes(cfg, sub_index) if getattr(cfg, "SOURCE_GATE_ENABLED", True) else set()
    if getattr(cfg, "SOURCE_GATE_ENABLED", True):
        logger.info("Source gate enabled: %d active source nodes.", len(source_ids))

    # --- 2. Simulation Loop ---
    t_grid = np.arange(0, cfg.TIME_END_HR + cfg.DT_HR, cfg.DT_HR)
    
    # Output Containers
    all_damage_probs = {}          # Damage-state probabilities retained for diagnostics only.
    all_damage_state_samples = {}
    all_mean_sub_repair_times = {} # Logistics: Duration for Crew Scheduling
    all_mean_sub_init_func0 = {}   # Consistency: t=0 state
    all_mean_tract_series = {}
    repair_task_audit_frames = []

    for scenario in cfg.SCENARIOS:
        logger.info(f"Processing scenario: {scenario}...")

        # A. Load Stage 1 Monte Carlo Records (The Raw Damage States)
        recs_path = out_dirs["STAGE1_DIR"] / f"MC_Device_Damage_Records_{scenario}.csv.gz"
        if not recs_path.exists():
            logger.error(f"Missing Stage 1 records file: {recs_path}")
            continue
        df_recs = pd.read_csv(recs_path)
        df_recs["substation_id"] = df_recs["substation_id"].map(clean_substation_id)
        damage_state_samples = _damage_records_to_state_matrix(df_recs, sub_index)
        all_damage_state_samples[scenario] = damage_state_samples

        # B. Calculate diagnostic damage probabilities.
        # Recovery synthesis uses MC damage-state samples directly below.
        ds_counts = pd.crosstab(df_recs["substation_id"], df_recs["damage_state"])
        ds_probs = ds_counts.div(ds_counts.sum(axis=1), axis=0)
        
        # Ensure matrix has all substations and all 5 DS columns (0-4)
        ds_probs = ds_probs.reindex(index=sub_index.astype(str), columns=range(5), fill_value=0.0)
        
        all_damage_probs[scenario] = ds_probs

        # C. Simulate recovery as E[gate(F_run(t))], with source connectivity
        # evaluated per MC realization before averaging.
        R_sub_mean_df = simulate_recovery_mc_source_gated(
            t_grid,
            sub_index,
            damage_state_samples,
            G,
            cfg,
            source_ids=source_ids,
            start_times=None,
            label=f"Stage3_{scenario}",
        )

        # D. Logistics: Calculate Mean Duration for Scheduling
        # Stage 4 needs a discrete "Job Duration" to book crews, even if the 
        # recovery itself is a probability curve. We use the MC mean for this.
        raw_times = stage_1_data["all_mc_repair_times"][scenario]
        mean_vals = raw_times.mean(axis=1)
        mean_vals[raw_times.max(axis=1) == 0] = 0.0 # Handle undamaged
        
        all_mean_sub_repair_times[scenario] = pd.Series(
            mean_vals, index=sub_index, name="mean_repair_time_hr"
        )
        repair_audit = build_repair_task_threshold_audit(
            scenario,
            all_mean_sub_repair_times[scenario],
            ds_probs,
            cfg,
        )
        repair_task_audit_frames.append(repair_audit)
        logger.info(
            "Repair task filter for %s: mean repair >= %.2f hr -> %d/%d dispatch tasks.",
            scenario,
            float(repair_audit["task_threshold_hr"].iloc[0]),
            int(repair_audit["is_repair_task"].sum()),
            len(repair_audit),
        )
        
        # Capture t=0 state from the generated curve
        all_mean_sub_init_func0[scenario] = R_sub_mean_df.iloc[0]

        # E. Propagate to Census Tracts
        S_tract_mean_df = propagate_to_tracts(R_sub_mean_df, W_mat, tract_index)
        all_mean_tract_series[scenario] = S_tract_mean_df

        # F. Save Results & Compute KPIs
        out_path = out_dirs["STAGE3_DIR"] / f"tract_step_recovery_mean_{scenario}.csv.gz"
        S_tract_mean_df.to_csv(out_path, compression="gzip", float_format="%.4f")

        kpis = kpis_from_series(S_tract_mean_df, cfg.TIME_END_HR)
        kpis.to_csv(out_dirs["STAGE3_DIR"] / f"tract_kpis_{scenario}.csv")
        
        # Log System T50
        system_curve = S_tract_mean_df.mean(axis=1)
        sys_t50 = system_curve.index[np.argmax(system_curve.values >= 0.5)] if system_curve.max() >= 0.5 else -1
        logger.info(f"Scenario {scenario} tract-mean T50: {sys_t50} hr")

        # G. Graph Robustness
        if G.number_of_nodes() > 0:
            robust_df = compute_graph_robustness(G, R_sub_mean_df, t_grid, cfg)
            robust_df.to_csv(out_dirs["STAGE3_DIR"] / f"graph_robustness_mean_{scenario}.csv", index=False)

    if repair_task_audit_frames:
        audit_path = out_dirs["STAGE3_DIR"] / "repair_task_threshold_audit.csv"
        pd.concat(repair_task_audit_frames, ignore_index=True).to_csv(audit_path, index=False)
        logger.info("Repair task threshold audit saved to %s", audit_path)

    logger.info("--- STAGE 3 Complete ---")
    
    return {
        "all_damage_probs": all_damage_probs,
        "all_damage_state_samples": all_damage_state_samples,
        "all_mean_sub_repair_times": all_mean_sub_repair_times,
        "all_mean_sub_init_func0": all_mean_sub_init_func0,
        "all_mean_tract_series": all_mean_tract_series,
    }


# ==========================================================================
# [PART 6] Stage 4: Crew Scheduling & Repair Logistics (Rule-Based)
# =============================================================================
# Contains: Travel matrices, Substation ordering rules, Scheduling engine, run_stage_4
def _timestamped_backup(path: Path) -> Optional[Path]:
    """Create one timestamped backup for a file during this process."""
    if not path.exists():
        return None
    resolved = str(path.resolve())
    if resolved in _TIMESTAMPED_BACKUPS_CREATED:
        return None
    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(f"{path.stem}.backup_{ts}{path.suffix}")
    import shutil

    shutil.copy2(path, backup_path)
    _TIMESTAMPED_BACKUPS_CREATED.add(resolved)
    return backup_path


def load_stage45_C57_depot_inputs(data_dir, depot_csv: Optional[str] = None) -> Dict[str, Any]:
    """
    Load and validate the finalized C57 Stage 4/5 depot input.

    Returns all D01-D16 depots, active depots with integer_crews > 0, utility
    totals, and one expanded row per dispatchable crew.
    """
    data_dir = Path(data_dir)
    depot_path = Path(depot_csv) if depot_csv else data_dir / "stage45_depot_inputs_final_origin_proxy.csv"
    if not depot_path.exists():
        raise FileNotFoundError(f"Stage 4/5 C57 depot input not found: {depot_path}")

    scenario_label = "C57_substation_ratio_main"
    allocation_label = "C57_yard_allocation_no_deletion_tie_coherent_zero_low"
    expected_ids = [f"D{i:02d}" for i in range(1, 17)]
    active_ids = ["D01", "D02", "D03", "D04", "D05", "D06", "D07", "D09", "D10", "D12", "D13"]
    inactive_ids = ["D08", "D11", "D14", "D15", "D16"]

    df = pd.read_csv(depot_path)
    df = df.rename(
        columns={
            "yard_id": "depot_id",
            "facility": "depot_name",
        }
    )
    if "depot_id" not in df.columns:
        raise ValueError("C57 depot input must contain depot_id.")

    df["depot_id"] = df["depot_id"].astype(str).str.strip()
    if df["depot_id"].duplicated().any():
        dupes = sorted(df.loc[df["depot_id"].duplicated(), "depot_id"].unique())
        raise ValueError(f"Duplicate C57 depot_id values: {dupes}")

    missing = sorted(set(expected_ids) - set(df["depot_id"]))
    extra = sorted(set(df["depot_id"]) - set(expected_ids))
    if len(df) != 16 or missing or extra:
        raise ValueError(f"C57 depot input must be exactly D01-D16. missing={missing}, extra={extra}, rows={len(df)}")

    allocation_cols = [
        "scenario_label",
        "allocation_label",
        "raw_visual_weight",
        "fractional_crews",
        "integer_crews",
        "active_in_integer_input",
    ]
    if any(c not in df.columns for c in allocation_cols):
        active_path = data_dir / "stage45_active_crew_bases_C57.csv"
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

    required = [
        "depot_name",
        "utility",
        "latitude",
        "longitude",
        "scenario_label",
        "allocation_label",
        "raw_visual_weight",
        "fractional_crews",
        "integer_crews",
        "active_in_integer_input",
    ]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"C57 depot input missing required columns: {missing_cols}")

    if set(df["scenario_label"].astype(str)) != {scenario_label}:
        raise ValueError("C57 depot scenario_label validation failed.")
    if set(df["allocation_label"].astype(str)) != {allocation_label}:
        raise ValueError("C57 depot allocation_label validation failed.")

    df["integer_crews"] = pd.to_numeric(df["integer_crews"], errors="raise").astype(int)
    df["fractional_crews"] = pd.to_numeric(df["fractional_crews"], errors="raise")
    df["raw_visual_weight"] = pd.to_numeric(df["raw_visual_weight"], errors="raise")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="raise")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="raise")

    if int(df["integer_crews"].sum()) != 57:
        raise ValueError(f"C57 total integer crews must be 57, got {int(df['integer_crews'].sum())}.")
    ladwp_total = int(df[df["depot_id"].isin(expected_ids[:6])]["integer_crews"].sum())
    sce_total = int(df[df["depot_id"].isin(expected_ids[6:])]["integer_crews"].sum())
    if ladwp_total != 47 or sce_total != 10:
        raise ValueError(f"C57 utility crew totals invalid: LADWP={ladwp_total}, SCE={sce_total}.")

    actual_active = sorted(df.loc[df["integer_crews"] > 0, "depot_id"].tolist())
    actual_inactive = sorted(df.loc[df["integer_crews"] == 0, "depot_id"].tolist())
    if actual_active != sorted(active_ids):
        raise ValueError(f"C57 active yard set invalid: {actual_active}")
    if actual_inactive != sorted(inactive_ids):
        raise ValueError(f"C57 inactive yard set invalid: {actual_inactive}")
    active_flag = df["active_in_integer_input"].astype(str).str.strip().str.lower()
    if not (active_flag[df["integer_crews"] > 0] == "yes").all():
        raise ValueError("C57 active depot rows must have active_in_integer_input=yes.")
    if not (active_flag[df["integer_crews"] == 0] == "no").all():
        raise ValueError("C57 inactive depot rows must have active_in_integer_input=no.")

    active_df = df[df["integer_crews"] > 0].copy()
    if active_df[["latitude", "longitude"]].isna().any().any():
        raise ValueError("C57 active depot rows must have non-null coordinates.")

    rename_map = {"depot_id": "yard_id", "depot_name": "facility"}
    full_df = df.rename(columns=rename_map).copy()
    active_df = active_df.rename(columns=rename_map).copy()
    for out_df in (full_df, active_df):
        out_df["travel_matrix_origin_key"] = out_df["yard_id"]

    expanded_rows = []
    crew_idx = 0
    for _, row in active_df.iterrows():
        for _ in range(int(row["integer_crews"])):
            expanded_rows.append(
                {
                    "crew_origin_index": crew_idx,
                    "crew_id": f"C57_crew_{crew_idx + 1:02d}",
                    "yard_id": row["yard_id"],
                    "utility": row["utility"],
                    "facility": row["facility"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "travel_matrix_origin_key": row["travel_matrix_origin_key"],
                }
            )
            crew_idx += 1
    expanded_df = pd.DataFrame(expanded_rows)
    if len(expanded_df) != 57:
        raise ValueError(f"C57 expanded crew origins must contain 57 rows, got {len(expanded_df)}.")

    return {
        "depot_path": depot_path,
        "full_depot_df": full_df,
        "active_depot_df": active_df,
        "expanded_crew_origins_df": expanded_df,
        "total_integer_crews": 57,
        "utility_totals": {"LADWP": ladwp_total, "SCE": sce_total},
        "active_ids": active_ids,
        "inactive_ids": inactive_ids,
    }


def write_stage45_C57_base_outputs(cfg: Config, depot_inputs: Dict[str, Any]) -> None:
    """Write C57 active/all/expanded crew-origin audit outputs."""
    active_cols = [
        "yard_id",
        "utility",
        "facility",
        "integer_crews",
        "fractional_crews",
        "raw_visual_weight",
        "latitude",
        "longitude",
        "scenario_label",
        "allocation_label",
        "travel_matrix_origin_key",
    ]
    depot_inputs["active_depot_df"][active_cols].to_csv(cfg.STAGE45_ACTIVE_CREW_BASES_CSV, index=False)
    depot_inputs["full_depot_df"].to_csv(cfg.STAGE45_ALL_DEPOT_AUDIT_CSV, index=False)
    depot_inputs["expanded_crew_origins_df"].to_csv(cfg.STAGE45_EXPANDED_CREW_ORIGINS_CSV, index=False)


def load_travel_matrices(
    cfg,
    devices_df: pd.DataFrame,
    task_sub_ids: list,
    all_sub_ids: list,
    active_depot_df: Optional[pd.DataFrame] = None,
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

    if active_depot_df is None:
        raise ValueError("C57 travel matrix loading requires active_depot_df.")

    crew_bases_expanded = [
        (
            str(row["facility"]),
            float(row["latitude"]),
            float(row["longitude"]),
            str(row["travel_matrix_origin_key"]),
        )
        for _, row in active_depot_df.iterrows()
    ]
    crew_base_ids = [c[3] for c in crew_bases_expanded]

    # Extract coordinates for relevant task substations
    # NOTE: This function assumes devices_df has columns: ["id", "lat", "lon"].
    task_devices = devices_df.set_index("id").reindex(task_sub_ids)
    if "lon" not in task_devices.columns and "LONGITUDE" in task_devices.columns:
        task_devices = task_devices.rename(columns={"LONGITUDE": "lon"})
    if "lat" not in task_devices.columns and "LATITUDE" in task_devices.columns:
        task_devices = task_devices.rename(columns={"LATITUDE": "lat"})
        
    # =========================================================================
    # 1) Base -> Task matrix
    # =========================================================================
    if base_to_task_path.exists():
        logger.debug("[Travel] Loading Base->Task CSV: %s", base_to_task_path)
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
        _timestamped_backup(base_to_task_path)

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
        logger.debug("[Travel] Loading Task->Task CSV: %s", task_to_task_path)
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
            geo_col = "geoid"
            for cand in ["GEOID", "tract_id", "TRACTFIPS", "geoid"]:
                if cand in hospital_tracts_df.columns:
                    geo_col = cand
                    break
            
            hosp_tract_ids = set(
                hospital_tracts_df[geo_col]
                .astype(str)
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )
        except Exception as e:
            logger.critical(f"CRITICAL FAILURE in 'hospital-first': Could not load hospital data. Error: {e}")
            raise e

        m = mapping_df.copy()
        m["tract_id_clean"] = (
            m["tract_id"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        )
        m["substation_id"] = m["substation_id"].map(clean_substation_id)
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
    damage_state_samples: np.ndarray,
    log_tag: str = None,
    crew_origin_ids: Optional[List[str]] = None,
    source_gate_graph: Optional[nx.Graph] = None,
    source_ids: Optional[set[str]] = None,
) -> pd.DataFrame:
    """
    Simulate a multi-crew repair schedule and generate MC source-gated Hazus recovery curves.
    """
    logger = logging.getLogger()

    # --- 1. Load and Fix Matrices ---
    base_to_task = travel_mats["base_to_task"].copy()
    task_to_task = travel_mats["task_to_task"].copy()
    
    # Normalize IDs (Strip whitespace and force string)
    base_to_task.index = base_to_task.index.astype(str).str.strip()
    base_to_task.columns = base_to_task.columns.astype(str).str.strip()
    
    task_to_task.index = task_to_task.index.astype(str).str.strip()
    task_to_task.columns = task_to_task.columns.astype(str).str.strip()

    # Normalize inputs
    order = [str(x).strip() for x in order]
    sub_index = pd.Index([str(x).strip() for x in sub_index])
    
    sub_repair_durations = sub_repair_durations.copy()
    sub_repair_durations.index = sub_repair_durations.index.astype(str).str.strip()

    base_ids = list(base_to_task.index)
    base_id_set = set(base_ids)

    # --- 2. Initialize State ---
    if crew_origin_ids is None:
        raise ValueError("C57 schedule simulation requires crew_origin_ids.")

    crew_clocks = np.zeros(n_crews)
    crew_origin_ids_clean = [str(x).strip() for x in crew_origin_ids]
    crew_locations = list(crew_origin_ids_clean)
    if len(crew_origin_ids_clean) != n_crews:
        raise ValueError(f"crew_origin_ids length {len(crew_origin_ids_clean)} != n_crews {n_crews}")
    missing_origins = sorted(set(crew_origin_ids_clean) - base_id_set)
    if missing_origins:
        raise ValueError(f"Crew origin IDs missing from base_to_task matrix: {missing_origins}")

    # Track END times (Logistics). Default to Inf (never fixed).
    sub_end_times = pd.Series(np.inf, index=sub_index)

    task_queue = list(order)
    avg_base_to_task = base_to_task.mean(axis=0) if not base_to_task.empty else pd.Series(dtype=float)

    # Debug counter to limit print output
    debug_miss_count = 0

    # --- 3. Main Loop ---
    while task_queue:
        next_crew_idx = int(np.argmin(crew_clocks))
        current_time = float(crew_clocks[next_crew_idx])
        
        # Ensure current_loc is a clean string
        raw_loc = crew_locations[next_crew_idx]
        current_loc = str(raw_loc).strip() if raw_loc is not None else None
        
        next_task_id = str(task_queue.pop(0)).strip()

        # 3.1 Calculate Travel Time
        travel_time = 0.0
        
        if current_loc in base_id_set:
            try:
                travel_time = float(base_to_task.loc[current_loc, next_task_id])
            except KeyError:
                travel_time = float(avg_base_to_task.get(next_task_id, 24.0))

        elif current_loc is None:
            travel_time = float(avg_base_to_task.get(next_task_id, 24.0))

        else:
            try:
                travel_time = float(task_to_task.loc[current_loc, next_task_id])
            except KeyError:
                if debug_miss_count < 3:
                    print(f"⚠️ [Travel Lookup Failed] {current_loc} -> {next_task_id}")
                    debug_miss_count += 1
                travel_time = np.inf

        # Fallback
        if not np.isfinite(travel_time):
            travel_time = 24.0

        # 3.2 Update Times
        arrival_time = current_time + travel_time
        repair_duration = float(sub_repair_durations.get(next_task_id, 0.0))
        end_time = arrival_time + repair_duration

        # Log Gantt
        if log_tag is not None:
            GLOBAL_GANTT_LOG.append({
                "Stage": log_tag,
                "Crew_ID": next_crew_idx,
                "Crew_Origin_ID": crew_origin_ids_clean[next_crew_idx],
                "Substation_ID": next_task_id,
                "Start_Time": arrival_time,
                "End_Time": end_time,
                "Duration": repair_duration,
                "Travel_Time": travel_time
            })

        crew_clocks[next_crew_idx] = end_time
        crew_locations[next_crew_idx] = next_task_id 

        if next_task_id in sub_end_times.index:
            sub_end_times.loc[next_task_id] = end_time

    # --- 4. Generate Hazus Recovery Curves ---
    # We derived End Times above. The Hazus curve needs Start Time (Arrival).
    # Start = End - Duration
    # (Unvisited nodes remain Inf, so Start is Inf, so Recovery is 0. Correct.)
    
    aligned_durations = sub_repair_durations.reindex(sub_index, fill_value=0.0)
    repair_starts = sub_end_times - aligned_durations
    task_threshold_hr = get_repair_task_threshold_hr(cfg)
    no_dispatch_mask = (~np.isfinite(repair_starts.values)) & (aligned_durations.values < task_threshold_hr)
    if np.any(no_dispatch_mask):
        # Minor expected workloads are not field-dispatch tasks; let them recover from t=0.
        repair_starts.iloc[no_dispatch_mask] = 0.0

    if damage_state_samples is None:
        raise ValueError("simulate_rule_schedule requires MC damage_state_samples for source-gated recovery.")

    return simulate_recovery_mc_source_gated(
        t_grid=t_grid,
        sub_index=sub_index,
        damage_state_samples=damage_state_samples,
        G=source_gate_graph if source_gate_graph is not None else nx.Graph(),
        cfg=cfg,
        source_ids=source_ids,
        start_times=repair_starts.values,
        label=log_tag or "",
    )


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
    total_pop = 0.0

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
    # 2) SVI * Population weights
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
                    logger.debug("SVI weights calculated successfully for analysis.")

        except Exception as e:
            logger.warning(f"Failed to calculate SVI weights: {e}")

    return pop_weights, svi_pop_weights


def run_stage_4(
    cfg: Config,
    stage_3_data: dict,
    stage_0_data: dict,
    stage_2_data: dict,
    out_dirs: dict,
) -> dict:
    """
    Stage 4: Rule-based scheduling baselines (e.g., Centrality, Impact, Random).
    Uses MC source-gated Hazus restoration after scheduled repair starts.
    """
    if not cfg.RUN_STAGE_4:
        logging.info("--- STAGE 4: Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 4: Rule-Based Baselines (MC Source-Gated Hazus) ---")

    # =========================================================================
    # 1. Load Context
    # =========================================================================
    W_mat = stage_0_data["W_mat"]
    tract_index = stage_0_data["tract_index"]
    sub_index = stage_0_data["sub_index"]
    devices_df = stage_0_data["devices_merged"]

    # Validation: Ensure Stage 3 results exist
    all_mean_sub_repair_times = stage_3_data.get("all_mean_sub_repair_times")
    if not all_mean_sub_repair_times:
        logger.error("FATAL: Missing 'all_mean_sub_repair_times'. Stage 3 might have failed.")
        return {}

    all_damage_state_samples = stage_3_data.get("all_damage_state_samples", {})
    if not all_damage_state_samples:
        logger.error("FATAL: Missing 'all_damage_state_samples'. Stage 3 must run before Stage 4.")
        return {}

    # Load Graph
    G = stage_2_data.get("G", nx.Graph())
    source_ids = load_source_gate_nodes(cfg, sub_index) if getattr(cfg, "SOURCE_GATE_ENABLED", True) else set()

    # Simulation Grid
    t_grid = np.arange(0, cfg.TIME_END_HR + cfg.DT_HR, cfg.DT_HR)

    # Weights for Analysis
    pop_weights, svi_pop_weights = get_analysis_weights(cfg, stage_0_data)
    if svi_pop_weights is None:
        logger.warning("SVI weights not available. SVI curves will not be generated.")

    depot_inputs = load_stage45_C57_depot_inputs(DATA_DIR, getattr(cfg, "STAGE45_DEPOT_INPUT_CSV", None))
    write_stage45_C57_base_outputs(cfg, depot_inputs)
    active_depot_df = depot_inputs["active_depot_df"]
    crew_origin_ids = depot_inputs["expanded_crew_origins_df"]["travel_matrix_origin_key"].astype(str).tolist()
    n_c57_crews = int(depot_inputs["total_integer_crews"])
    logger.info(
        "Stage 4 using C57 depot CSV: %d active bases, %d expanded crews.",
        len(active_depot_df),
        n_c57_crews,
    )

    # Rules to Simulate
    rules = [
        "centrality-first",
        "impact-first",
        "betweenness-first",
        "degree-first",
        "closeness-first",
        "hospital-first",
        "random",
    ]

    out_dir = out_dirs["STAGE4_DIR"]
    stage_4_data = {}

    # =========================================================================
    # 2. Main Simulation Loop (Per Scenario)
    # =========================================================================
    for scenario in cfg.SCENARIOS:
        logger.info(f"Processing scenario: {scenario}...")

        if scenario not in all_mean_sub_repair_times:
            continue

        # Get Scenario Data
        sub_repair_durations = all_mean_sub_repair_times[scenario]
        damage_state_samples = all_damage_state_samples.get(scenario)
        if damage_state_samples is None:
            logger.error("FATAL: Missing MC damage-state samples for %s. Cannot run Stage 4 recovery.", scenario)
            continue

        # Identify dispatchable field-repair tasks.
        # Minor expected workloads below the DS1-equivalent threshold recover from t=0
        # and do not consume crew time.
        tasks_to_do_series, task_threshold_hr = select_repair_tasks(sub_repair_durations, cfg)
        task_sub_ids = list(tasks_to_do_series.index)
        logger.info(
            "Stage 4 task filter for %s: mean repair >= %.2f hr -> %d/%d tasks.",
            scenario,
            task_threshold_hr,
            len(task_sub_ids),
            len(sub_repair_durations),
        )

        if not task_sub_ids:
            logger.warning(f"No damaged substations for {scenario}. Skipping.")
            continue

        # Load Scenario-Specific Travel Matrices
        travel_mats = load_travel_matrices(
            cfg,
            devices_df,
            task_sub_ids,
            sub_index.to_list(),
            active_depot_df=active_depot_df,
        )

        # Local Containers for this Scenario
        scenario_curves_pop = {}
        scenario_curves_svi = {}
        scenario_kpis_pop = {}
        scenario_kpis_svi = {}

        # --- Run Each Rule ---
        for rule in rules:
            logger.debug("Simulating Stage 4 rule for %s: %s", scenario, rule)

            # A. Determine Repair Order
            order = order_substations(rule, task_sub_ids, stage_0_data, stage_2_data, cfg)

            # B. Simulate schedule and MC source-gated recovery.
            R_sub_df = simulate_rule_schedule(
                order=order,
                n_crews=n_c57_crews,
                travel_mats=travel_mats,
                t_grid=t_grid,
                sub_repair_durations=sub_repair_durations,
                sub_index=sub_index,
                cfg=cfg,
                damage_state_samples=damage_state_samples,
                log_tag=f"Stage4_{scenario}_{rule}",
                crew_origin_ids=crew_origin_ids,
                source_gate_graph=G,
                source_ids=source_ids,
            )

            # C. Propagate to Tracts (Tract = W * Substation)
            S_tract_df = propagate_to_tracts(R_sub_df, W_mat, tract_index)

            # D. Compute Population-Weighted Curve
            system_curve_pop = S_tract_df.values @ pop_weights
            scenario_curves_pop[rule] = system_curve_pop

            kpis_pop = kpis_from_series(
                pd.DataFrame({"system": system_curve_pop}, index=t_grid),
                cfg.TIME_END_HR,
            )
            kpis_pop["rule"] = rule
            scenario_kpis_pop[rule] = kpis_pop

            # E. Compute SVI-Weighted Curve (Optional)
            if svi_pop_weights is not None:
                system_curve_svi = S_tract_df.values @ svi_pop_weights
                scenario_curves_svi[rule] = system_curve_svi

                kpis_svi = kpis_from_series(
                    pd.DataFrame({"system": system_curve_svi}, index=t_grid),
                    cfg.TIME_END_HR,
                )
                kpis_svi["rule"] = rule
                scenario_kpis_svi[rule] = kpis_svi

            # F. Compute Graph Robustness
            if G.number_of_nodes() > 0:
                dyn_df = compute_graph_robustness(G, R_sub_df, t_grid, cfg)
                dyn_df.to_csv(out_dir / f"rule_graphrobustness_{scenario}_{rule}.csv", index=False)
            else:
                pd.DataFrame({"t": [0], "lcc_fraction": [0.0]}).to_csv(
                    out_dir / f"rule_graphrobustness_{scenario}_{rule}.csv",
                    index=False,
                )

        # =====================================================================
        # 3. Save Outputs (Disk & Memory)
        # =====================================================================
        df_pop = pd.DataFrame(scenario_curves_pop, index=t_grid)
        df_pop.to_csv(out_dir / f"rule_curves_pop_{scenario}.csv", index_label="time_hr")

        df_svi = pd.DataFrame()
        if scenario_curves_svi:
            df_svi = pd.DataFrame(scenario_curves_svi, index=t_grid)
            df_svi.to_csv(out_dir / f"rule_curves_svi_{scenario}.csv", index_label="time_hr")

        kpis_pop_df = pd.DataFrame()
        if scenario_kpis_pop:
            kpis_pop_df = pd.concat(scenario_kpis_pop.values())
            kpis_pop_df.to_csv(out_dir / f"rule_kpis_pop_{scenario}.csv", index=False)

        kpis_svi_df = pd.DataFrame()
        if scenario_kpis_svi:
            kpis_svi_df = pd.concat(scenario_kpis_svi.values())
            kpis_svi_df.to_csv(out_dir / f"rule_kpis_svi_{scenario}.csv", index=False)

        logger.info(
            "Completed Stage 4 schedules for %s: %d rules, %d damaged tasks.",
            scenario,
            len(scenario_curves_pop),
            len(task_sub_ids),
        )
        logger.debug("Wrote rule-based curves to %s for %s", out_dir, scenario)

        stage_4_data[scenario] = {
            "system_curves_pop": df_pop,
            "kpis_pop": kpis_pop_df,
            "system_curves_svi": df_svi,
            "kpis_svi": kpis_svi_df,
        }

    # =========================================================================
    # 4. Finalize
    # =========================================================================
    s4_gantt_data = [x for x in GLOBAL_GANTT_LOG if str(x.get("Stage", "")).startswith("Stage4")]
    if s4_gantt_data:
        df_s4 = pd.DataFrame(s4_gantt_data)
        gantt_path = out_dir / "Gantt_Data_Stage4.csv"
        df_s4.to_csv(gantt_path, index=False)
        logger.info("Stage 4 Gantt data written: %d rows.", len(df_s4))
        logger.debug("Stage 4 Gantt path: %s", gantt_path)
    else:
        logger.warning("No Gantt data found for Stage 4.")

    logger.info("--- STAGE 4 Complete ---")
    return {"results": stage_4_data}


# =============================================================================
# Stage 5: Genetic Algorithm Optimization
# =============================================================================
def run_stage_5(
    cfg: Config,
    stage_0_data: Dict,
    stage_3_data: Dict,
    out_dirs: Dict,
) -> Dict:
    """
    Stage 5: Genetic Algorithm (GA) optimization (Multi-Policy).
    Uses MC source-gated Hazus restoration after scheduled repair starts.
    """
    if not cfg.RUN_STAGE_5:
        logging.info("--- STAGE 5 (GA): Skipped ---")
        return {}

    logger = logging.getLogger()
    logger.info("=" * 50)
    logger.info("--- STAGE 5: Genetic Algorithm Optimization (MC Source-Gated Hazus) ---")

    # --- 1. Helpers & Inputs ---
    def _norm01(x, eps=1e-12):
        x = np.asarray(x, dtype=float)
        mn, mx = float(np.min(x)), float(np.max(x))
        return (x - mn) / (mx - mn + eps)

    all_mean_sub = stage_3_data["all_mean_sub_repair_times"]
    all_damage_state_samples = stage_3_data.get("all_damage_state_samples", {})
    if not all_damage_state_samples:
        logger.error("FATAL: Missing 'all_damage_state_samples'. Stage 3 must be run first.")
        return {}

    W_mat = stage_0_data["W_mat"]
    sub_index = stage_0_data["sub_index"]
    tract_index = stage_0_data["tract_index"]

    sub_index_str = [clean_substation_id(s) for s in list(sub_index)]
    sub_idx_map = {sid: i for i, sid in enumerate(sub_index_str)}
    out_dir_s5 = out_dirs["STAGE5_DIR"]

    # --- Build base graph once for GA graph-robustness export ---
    devices_merged = stage_0_data["devices_merged"].copy()
    devices_merged = ensure_substation_id_col(devices_merged)
    devices_merged["substation_id"] = devices_merged["substation_id"].map(clean_substation_id)

    G = build_base_graph(cfg, devices_merged, sub_index)
    source_ids = load_source_gate_nodes(cfg, sub_index) if getattr(cfg, "SOURCE_GATE_ENABLED", True) else set()

    depot_inputs = load_stage45_C57_depot_inputs(DATA_DIR, getattr(cfg, "STAGE45_DEPOT_INPUT_CSV", None))
    write_stage45_C57_base_outputs(cfg, depot_inputs)
    active_depot_df = depot_inputs["active_depot_df"]
    crew_origin_ids = depot_inputs["expanded_crew_origins_df"]["travel_matrix_origin_key"].astype(str).tolist()
    n_c57_crews = int(depot_inputs["total_integer_crews"])
    logger.info(
        "Stage 5 using C57 depot CSV: %d active bases, %d expanded crews.",
        len(active_depot_df),
        n_c57_crews,
    )

    # --- 2. Prepare Importance Vectors ---
    mapping_df = stage_0_data["mapping_df"]
    tract_index_str = pd.Index(tract_index).astype(str).str.split(".").str[0].str.strip()

    pop_per_tract = mapping_df.groupby("tract_id")["population"].first()
    pop_per_tract.index = pop_per_tract.index.astype(str).str.split(".").str[0].str.strip()
    pop_vec = pop_per_tract.reindex(tract_index_str).fillna(0.0).values
    pop_imp = pop_vec @ W_mat

    pop_w_global, svi_pop_w_global = get_analysis_weights(cfg, stage_0_data)
    has_svi = svi_pop_w_global is not None
    svi_imp = (np.asarray(svi_pop_w_global, dtype=float) @ W_mat) if has_svi else np.zeros(len(sub_index_str))

    try:
        hosp_df = pd.read_csv(cfg.HOSPITAL_TRACTS_CSV)
        geo_col = "geoid"
        for cand in ["GEOID", "tract_id", "TRACTFIPS"]:
            if cand in hosp_df.columns:
                geo_col = cand
                break
        hosp_ids = set(hosp_df[geo_col].astype(str).str.split(".").str[0].str.strip())
        is_hosp = pd.Series(0.0, index=tract_index_str)
        is_hosp.loc[is_hosp.index.isin(hosp_ids)] = 1.0
        sub_hosp_score = is_hosp.values @ W_mat
    except Exception:
        sub_hosp_score = np.zeros(len(sub_index_str))

    def _build_node_importance_components() -> pd.DataFrame:
        attr = devices_merged.copy()
        attr = ensure_substation_id_col(attr)
        attr["substation_id"] = attr["substation_id"].map(clean_substation_id)

        voltage_col = next((c for c in ["MAX_VOLT", "MAX_VOLT_N", "voltage_for_fragility"] if c in attr.columns), None)
        lines_col = next((c for c in ["LINES", "lines"] if c in attr.columns), None)

        base_attr = pd.DataFrame(index=pd.Index(sub_index_str, name="substation_id"))
        if voltage_col is not None:
            voltage = pd.to_numeric(attr[voltage_col], errors="coerce")
            voltage = voltage.where(voltage > 0)
            base_attr["MAX_VOLT"] = voltage.groupby(attr["substation_id"]).max()
        else:
            base_attr["MAX_VOLT"] = np.nan

        if lines_col is not None:
            lines = pd.to_numeric(attr[lines_col], errors="coerce")
            lines = lines.where(lines > 0, 0.0)
            base_attr["LINES"] = lines.groupby(attr["substation_id"]).max()
        else:
            base_attr["LINES"] = 0.0

        base_attr = base_attr.reindex(sub_index_str)

        source_roles = load_source_role_table(cfg, sub_index=base_attr.index)
        if source_roles.empty:
            role_score = pd.Series(0.0, index=base_attr.index)
            role_matched = pd.Series(False, index=base_attr.index)
        else:
            role_score = (
                source_roles.set_index("substation_id")["source_role_score"]
                .reindex(base_attr.index)
                .fillna(0.0)
            )
            role_matched = base_attr.index.to_series().isin(source_roles["substation_id"])

        voltage_map = {66: 0.20, 69: 0.20, 115: 0.50, 138: 0.50, 230: 0.80, 500: 1.00}
        voltage_score = (
            pd.to_numeric(base_attr["MAX_VOLT"], errors="coerce")
            .round()
            .astype("Int64")
            .map(voltage_map)
            .fillna(0.0)
        )
        lines_scale = float(getattr(cfg, "STAGE5_NODE_IMPORTANCE_LINES_SCALE", 12.0))
        lines_score = pd.to_numeric(base_attr["LINES"], errors="coerce").fillna(0.0) / lines_scale

        w_role = float(getattr(cfg, "STAGE5_NODE_IMPORTANCE_ROLE_WEIGHT", 0.70))
        w_voltage = float(getattr(cfg, "STAGE5_NODE_IMPORTANCE_VOLTAGE_WEIGHT", 0.20))
        w_lines = float(getattr(cfg, "STAGE5_NODE_IMPORTANCE_LINES_WEIGHT", 0.10))
        node_score = w_role * role_score.values + w_voltage * voltage_score.values + w_lines * lines_score

        return pd.DataFrame(
            {
                "node_importance_score": node_score,
                "importance_role_score": role_score.values,
                "importance_voltage_score": voltage_score.values,
                "importance_lines_score": lines_score,
                "importance_table_matched": role_matched.values,
            },
            index=base_attr.index,
        )

    node_importance_df = _build_node_importance_components()

    # --- 3. DEAP (GA) Setup ---
    if not hasattr(creator, "FitnessMax"):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    def mutInversion(individual, indpb):
        if random.random() < indpb:
            size = len(individual)
            if size < 2:
                return (individual,)
            a, b = random.sample(range(size), 2)
            if a > b:
                a, b = b, a
            individual[a : b + 1] = individual[a : b + 1][::-1]
        return (individual,)
    toolbox.register("mate", tools.cxOrdered)
    toolbox.register("mutate", mutInversion, indpb=0.2)
    toolbox.register("select", tools.selTournament, tournsize=3)

    combined_results_pop = {}
    combined_results_svi = {}

    # --- 4. Main Loop: Scenarios ---
    for scenario in cfg.SCENARIOS:
        logger.info(f"Processing Scenario: {scenario}...")
        combined_results_pop[scenario] = {}
        combined_results_svi[scenario] = {}

        if scenario not in all_mean_sub:
            continue

        repair_times = all_mean_sub[scenario]
        damage_state_samples = all_damage_state_samples.get(scenario)
        if damage_state_samples is None:
            logger.error("FATAL: Missing MC damage-state samples for %s. Cannot run Stage 5 recovery.", scenario)
            continue

        # Identify dispatchable field-repair tasks using the same threshold as Stage 4.
        tasks, task_threshold_hr = select_repair_tasks(repair_times, cfg)
        task_ids = list(tasks.index)
        n_tasks = len(task_ids)
        logger.info(
            "Stage 5 task filter for %s: mean repair >= %.2f hr -> %d/%d tasks.",
            scenario,
            task_threshold_hr,
            n_tasks,
            len(repair_times),
        )
        if n_tasks == 0:
            continue

        tmats = load_travel_matrices(
            cfg,
            stage_0_data["devices_merged"],
            task_ids,
            list(sub_index),
            active_depot_df=active_depot_df,
        )
        base_mat = tmats["base_to_task"].values
        task_mat = tmats["task_to_task"].values
        base_ids = tmats["base_to_task"].index.astype(str).tolist()
        base_idx_map = {bid: i for i, bid in enumerate(base_ids)}
        missing_crew_origins = sorted(set(crew_origin_ids) - set(base_ids))
        if missing_crew_origins:
            raise ValueError(f"C57 crew origins missing from Stage 5 base matrix: {missing_crew_origins}")
        crew_base_idx = np.array([base_idx_map[origin_id] for origin_id in crew_origin_ids], dtype=int)

        global_idxs = [sub_idx_map[clean_substation_id(t)] for t in task_ids]
        pop_n = _norm01(pop_imp[global_idxs])
        hosp_n = _norm01(sub_hosp_score[global_idxs])
        svi_n = _norm01(svi_imp[global_idxs])
        task_importance = node_importance_df.reindex([clean_substation_id(t) for t in task_ids]).fillna(0.0)
        task_times = tasks.values

        for policy_name, weights in cfg.GA_SCENARIOS_CONFIG.items():
            logger.debug("Running Stage 5 GA policy for %s: %s %s", scenario, policy_name, weights)

            W_POP, W_HOSP, W_MAKESPAN = weights["W_POP"], weights["W_HOSP"], weights["W_MAKESPAN"]
            W_SVI = getattr(cfg, "W_SVI", 0.0) if has_svi else 0.0

            task_vals_base = W_POP * pop_n + W_HOSP * hosp_n + W_SVI * svi_n
            positive_base = task_vals_base[task_vals_base > 0]
            s_ref = float(np.median(positive_base)) if len(positive_base) else 0.0
            node_importance_bonus = (
                float(getattr(cfg, "STAGE5_NODE_IMPORTANCE_ALPHA", 1.0))
                * s_ref
                * task_importance["node_importance_score"].values
            )
            task_vals = task_vals_base + node_importance_bonus
            component_df = pd.DataFrame(
                {
                    "substation_id": [clean_substation_id(t) for t in task_ids],
                    "sub_value_base": task_vals_base,
                    "node_importance_score": task_importance["node_importance_score"].values,
                    "node_importance_s_ref": s_ref,
                    "node_importance_bonus": node_importance_bonus,
                    "sub_value_final": task_vals,
                    "importance_role_score": task_importance["importance_role_score"].values,
                    "importance_voltage_score": task_importance["importance_voltage_score"].values,
                    "importance_lines_score": task_importance["importance_lines_score"].values,
                    "importance_table_matched": task_importance["importance_table_matched"].values,
                }
            )
            component_df.to_csv(out_dir_s5 / f"ga_sub_value_components_{scenario}_{policy_name}.csv", index=False)
            T_MAX = float(cfg.TIME_END_HR) + float(cfg.GA_EXTRA_EVAL_HR)

            def eval_sched(ind):
                clocks = np.zeros(n_c57_crews)
                locs = np.full(n_c57_crews, -1, dtype=int)
                end_times = np.zeros(n_tasks)
                for t_idx in ind:
                    c = int(np.argmin(clocks))
                    prev = int(locs[c])
                    travel = float(base_mat[crew_base_idx[c], t_idx]) if prev == -1 else float(task_mat[prev, t_idx])
                    start = clocks[c] + travel
                    end = start + float(task_times[t_idx])
                    clocks[c], locs[c], end_times[int(t_idx)] = end, int(t_idx), end

                valid = end_times < T_MAX
                score = np.sum(task_vals[valid] * (T_MAX - end_times[valid]))
                score -= W_MAKESPAN * np.max(clocks)
                return (score,)

            toolbox.register("evaluate", eval_sched)
            raw_seed_sum = cfg.RNG_SEED + zlib.crc32(scenario.encode()) + zlib.crc32(policy_name.encode())
            fixed_seed = raw_seed_sum & 0xFFFFFFFF
            random.seed(fixed_seed)
            np.random.seed(fixed_seed)
            pop = [creator.Individual(random.sample(range(n_tasks), n_tasks)) for _ in range(cfg.GA_POP_SIZE - 2)]
            pop.append(creator.Individual(np.argsort(task_vals)[::-1].tolist()))
            pop.append(creator.Individual(np.argsort(task_times).tolist()))

            pop, _ = algorithms.eaSimple(
                pop,
                toolbox,
                cxpb=cfg.GA_CXPB,
                mutpb=cfg.GA_MUTPB,
                ngen=cfg.GA_N_GEN,
                verbose=False,
            )

            best_ind = tools.selBest(pop, 1)[0]
            best_order = [task_ids[i] for i in best_ind]

            # --- Export Detailed Schedule for Visualization ---
            schedule_rows = []
        
            sim_clocks = np.zeros(n_c57_crews)
            sim_locs = np.full(n_c57_crews, -1, dtype=int)
            
            for rank, t_idx in enumerate(best_ind):
                c = int(np.argmin(sim_clocks))
                prev = int(sim_locs[c])
                if prev == -1:
                    travel = float(base_mat[crew_base_idx[c], t_idx])
                else:
                    travel = float(task_mat[prev, t_idx])
            
                start_time = sim_clocks[c] + travel
                duration = float(task_times[t_idx])
                finish_time = start_time + duration
                
                sim_clocks[c] = finish_time
                sim_locs[c] = int(t_idx)
                
                r_type = "C57"
                
                schedule_rows.append({
                    "repair_order": rank + 1,
                    "substation_id": task_ids[t_idx],
                    "Crew_ID": c,           
                    "Crew_Origin_ID": crew_origin_ids[c],
                    "Resource_Type": r_type,
                    "Start_Time": start_time,
                    "Finish_Time": finish_time,
                    "Travel_Time": travel,
                    "Duration": duration
                })
   
            out_csv_path = out_dir_s5 / f"GA_Schedule_{scenario}_{policy_name}.csv"
            pd.DataFrame(schedule_rows).to_csv(out_csv_path, index=False)
            logger.debug("Saved detailed GA schedule: %s", out_csv_path)

            t_grid = np.arange(0, cfg.TIME_END_HR + cfg.DT_HR, cfg.DT_HR)

            R_sub = simulate_rule_schedule(
                order=best_order,
                n_crews=n_c57_crews,
                travel_mats=tmats,
                t_grid=t_grid,
                sub_repair_durations=repair_times,
                sub_index=sub_index,
                cfg=cfg,
                damage_state_samples=damage_state_samples,
                crew_origin_ids=crew_origin_ids,
                source_gate_graph=G,
                source_ids=source_ids,
            )

            # --- Export GA dynamic graph robustness (per scenario, per GA policy) ---
            out_path = out_dir_s5 / f"ga_graphrobustness_{scenario}_{policy_name}.csv"

            if G.number_of_nodes() > 0:
                dyn_df = compute_graph_robustness(G, R_sub, t_grid, cfg)
                dyn_df.to_csv(out_path, index=False)
            else:
                pd.DataFrame(
                    {"t": [0], "lcc_size": [0], "avg_degree": [0.0], "lcc_fraction": [0.0]}
                ).to_csv(out_path, index=False)

            S_tract = propagate_to_tracts(R_sub, W_mat, tract_index)

            curve_pop = S_tract.values @ pop_w_global
            combined_results_pop[scenario][policy_name] = pd.Series(curve_pop, index=t_grid)
            pd.DataFrame({f"GA_{policy_name}": curve_pop}, index=t_grid).to_csv(
                out_dir_s5 / f"GA_Curve_Pop_{scenario}_{policy_name}.csv"
            )

            if has_svi:
                curve_svi = S_tract.values @ svi_pop_w_global
                combined_results_svi[scenario][policy_name] = pd.Series(curve_svi, index=t_grid)
                pd.DataFrame({f"GA_{policy_name}": curve_svi}, index=t_grid).to_csv(
                    out_dir_s5 / f"GA_Curve_SVI_{scenario}_{policy_name}.csv"
                )

            if policy_name == "Balanced":
                kpis = kpis_from_series(S_tract, cfg.TIME_END_HR)
                kpi_path = out_dir_s5 / f"tract_kpis_{scenario}.csv"
                kpis.to_csv(kpi_path, index_label="tract_id")
                logger.debug("Saved Stage 7 input: %s", kpi_path)

        logger.info(
            "Completed Stage 5 GA for %s: %d policies, %d damaged tasks.",
            scenario,
            len(cfg.GA_SCENARIOS_CONFIG),
            n_tasks,
        )

    # --- 5. Format Output for Stage 6 ---
    out = {"pop": {}, "svi": {}}

    for scen, policies in combined_results_pop.items():
        df_combined = pd.DataFrame(policies)
        df_combined.index.name = "time_hr"
        out["pop"][scen] = df_combined

    for scen, policies in combined_results_svi.items():
        df_combined = pd.DataFrame(policies)
        df_combined.index.name = "time_hr"
        out["svi"][scen] = df_combined

    logger.info("--- STAGE 5 Complete ---")
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
      - Stage 5 GA-optimized system recovery curves (Multi-Policy)

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
    logger.info("--- STAGE 6: Consolidation & Separate Plotting (Adaptive X; GA Multi-Policy) ---")

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
            return series
        return s

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
        # B) Stage 4 rule-based scheduling curves
        # ---------------------------------------------------------------------
        s4_results = stage_4_data.get("results", {})
        
        if scenario in s4_results:
            scen_data = s4_results[scenario]
            
            # --- 1. Population Curves (from memory) ---
            s4_pop_data = scen_data.get("system_curves_pop")
            if s4_pop_data is not None and not s4_pop_data.empty:
                for rule in s4_pop_data.columns:
                    series = _align_to_tgrid(s4_pop_data[rule])
                    current_pop_curves[rule] = series
                    all_system_curves[f"{scenario}_S4_{rule}_Pop"] = series
                
                # Retrieve KPIs from memory
                kpi_pop_df = scen_data.get("kpis_pop")
                if kpi_pop_df is not None:
                    # Make a copy to avoid modifying the original dict in place
                    kpi_pop_df = kpi_pop_df.copy()
                    kpi_pop_df["scenario"] = scenario
                    kpi_pop_df["rule"] = "Stage4_" + kpi_pop_df["rule"].astype(str)
                    all_kpis.append(kpi_pop_df)
            else:
                logger.warning(f"Stage 4 results found for {scenario}, but 'system_curves_pop' is empty.")

            # --- 2. SVI Curves (from memory, optional) ---
            if svi_pop_weights is not None:
                s4_svi_data = scen_data.get("system_curves_svi")
                if s4_svi_data is not None and not s4_svi_data.empty:
                    for rule in s4_svi_data.columns:
                        series = _align_to_tgrid(s4_svi_data[rule])
                        current_svi_curves[rule] = series
                        all_system_curves[f"{scenario}_S4_{rule}_SVI"] = series
                    
                    # Retrieve KPIs from memory
                    kpi_svi_df = scen_data.get("kpis_svi")
                    if kpi_svi_df is not None:
                        kpi_svi_df = kpi_svi_df.copy()
                        kpi_svi_df["scenario"] = scenario
                        kpi_svi_df["rule"] = "Stage4_" + kpi_svi_df["rule"].astype(str) + "_SVIpop"
                        all_kpis.append(kpi_svi_df)
        else:
            logger.warning(f"No Stage 4 in-memory data found for scenario: {scenario}")

        # ---------------------------------------------------------------------
        # C) Stage 5 GA curves (Multi-Policy Support)
        # ---------------------------------------------------------------------
        if stage_5_data and isinstance(stage_5_data, dict):
            # C1: Population Weighted
            if "pop" in stage_5_data:
                ga_pop_df = stage_5_data["pop"].get(scenario)
                if ga_pop_df is not None and not ga_pop_df.empty:
                    # Iterate through all available policy columns (Balanced, HospFirst, Efficiency)
                    for policy_name in ga_pop_df.columns:
                        series_pop = _align_to_tgrid(ga_pop_df[policy_name])
                        
                        # Label format matches style_config keys: "GA_Balanced", "GA_HospFirst"
                        label = f"GA_{policy_name}" 

                        current_pop_curves[label] = series_pop
                        all_system_curves[f"{scenario}_{label}_Pop"] = series_pop

                        # Calculate KPIs
                        kpis_pop = kpis_from_series(pd.DataFrame({"system": series_pop}), cfg.TIME_END_HR)
                        kpis_pop["scenario"] = scenario
                        kpis_pop["rule"] = f"Stage5_{label}" 
                        all_kpis.append(kpis_pop)

            # C2: SVI Weighted (Optional)
            if svi_pop_weights is not None and "svi" in stage_5_data:
                ga_svi_df = stage_5_data["svi"].get(scenario)
                if ga_svi_df is not None and not ga_svi_df.empty:
                    for policy_name in ga_svi_df.columns:
                        series_svi = _align_to_tgrid(ga_svi_df[policy_name])
                        label = f"GA_{policy_name}"

                        current_svi_curves[label] = series_svi
                        all_system_curves[f"{scenario}_{label}_SVI"] = series_svi

                        kpis_svi = kpis_from_series(pd.DataFrame({"system": series_svi}), cfg.TIME_END_HR)
                        kpis_svi["scenario"] = scenario
                        kpis_svi["rule"] = f"Stage5_{label}_SVI"
                        all_kpis.append(kpis_svi)

    # -------------------------------------------------------------------------
    # 5) Write consolidated outputs
    # -------------------------------------------------------------------------
    if all_system_curves:
        all_curves_df = pd.DataFrame(all_system_curves)
        all_curves_df = all_curves_df.reindex(t_grid)
        all_curves_df.to_csv(out_dir / "recovery_curves_all_system.csv", index_label="time_hr")

    if all_kpis:
        all_kpis_df = pd.concat(all_kpis).reset_index(drop=True)
        all_kpis_df.to_csv(out_dir / "recovery_kpis_all_system.csv", index=False)

    logger.info("--- STAGE 6 Complete ---")


# ==========================================================================
# [PART 8] Stage 7: Typology Clustering (K-Means + PCA Diagnostics)
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
    logger.info("--- STAGE 7: K-Means + PCA Diagnostics (Final Enhanced) ---")
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
        s = series.astype(str).str.strip()
        return (
            s.str.split(".").str[0]
             .str.extract(r"(\d+)")[0]
             .str.lstrip("0")
        )

    # ---------------------------------------------------------
    # A. Recovery Metrics (from Stage 5 GA) - single scenario
    # ---------------------------------------------------------
    target_scen = "2pc50"

    s5_kpi_path = out_dirs["STAGE5_DIR"] / f"tract_kpis_{target_scen}.csv"
    if not s5_kpi_path.exists():
        raise FileNotFoundError(f"Missing Stage 5 tract KPI file: {s5_kpi_path}")

    df_s5 = pd.read_csv(s5_kpi_path)
    if "tract_id" not in df_s5.columns:
        df_s5.rename(columns={df_s5.columns[0]: "tract_id"}, inplace=True)

    df_s5["tract_id"] = df_s5["tract_id"].astype(str).str.split(".").str[0].str.strip()
    df_s5["scenario"] = target_scen

    # Ensure KPI columns exist (defensive)
    for c in ["T50", "T80"]:
        if c not in df_s5.columns:
            df_s5[c] = 0.0

    df_main_raw = df_s5[["tract_id", "scenario", "T50", "T80"]].copy()

    # ---------------------------------------------------------
    # B. Initial Supply (from Stage 1 MC) - single scenario
    # ---------------------------------------------------------
    supply_file = out_dirs["STAGE1_DIR"] / f"MC_Tract_Supply_{target_scen}.csv"
    if supply_file.exists():
        df_s = pd.read_csv(supply_file)
        col_id = "tract" if "tract" in df_s.columns else df_s.columns[0]
        col_val = "supply" if "supply" in df_s.columns else df_s.columns[-1]
        df_s[col_id] = df_s[col_id].astype(str).str.split(".").str[0].str.strip()
        df_s = df_s.rename(columns={col_id: "tract_id", col_val: "Init_Supply"})
        df_s["scenario"] = target_scen
        df_s = df_s.copy()

        df_main_raw = (
            pd.merge(
                df_main_raw,
                df_s[["tract_id", "scenario", "Init_Supply"]],
                on=["tract_id", "scenario"],
                how="left",
            )
            .fillna(0)
        )
    else:
        df_main_raw["Init_Supply"] = 0.0

    # ---------------------------------------------------------
    # Aggregation (keep mean for safety; single-scenario -> identity)
    # ---------------------------------------------------------
    df_main = (
        df_main_raw.groupby("tract_id")[["T50", "T80", "Init_Supply"]]
        .mean()
        .reset_index()
    )

    # Standardize tract_id: keep digits only, drop decimal suffix, strip leading zeros
    df_main["tract_id"] = _normalize_tract_id(df_main["tract_id"])
    df_main["scenario"] = target_scen

    # ---------------------------------------------------------
    # C. Grid Centrality & Network Structure Features
    # ---------------------------------------------------------
    cent_path = out_dirs["STAGE2_DIR"] / "impact_centrality_substations.csv"
    mapping_df = stage_0_data.get("mapping_df", None)

    # Default values
    df_main["Grid_Degree"] = 0.0
    df_main["Grid_Impact"] = 0.0
    df_main["Grid_Betweenness"] = 0.0
    df_main["Redundancy_HHI"] = np.nan

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

            df_cent[sub_col] = df_cent[sub_col].map(clean_substation_id)
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
            m["substation_id"] = m["substation_id"].map(clean_substation_id)

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

            # 1) Grid_Degree: mean degree
            if "deg" in m.columns:
                grid_deg = g["deg"].mean()
                df_main["Grid_Degree"] = (
                    df_main["tract_id"].map(grid_deg).fillna(0.0)
                )

            # 2) Grid_Impact: mean lambda2-loss impact_centrality
            if "imp" in m.columns:
                grid_imp = g["imp"].mean()
                df_main["Grid_Impact"] = (
                    df_main["tract_id"].map(grid_imp).fillna(0.0)
                )

            # 3) Grid_Betweenness: mean betweenness
            if "bet" in m.columns:
                grid_bet = g["bet"].mean()
                df_main["Grid_Betweenness"] = (
                    df_main["tract_id"].map(grid_bet).fillna(0.0)
                )

            # 4) Redundancy metrics (if weights exist)
            if "weight" in m.columns:

                def _redundancy_stats(grp):
                    w = grp["weight"].values.astype(float)
                    total = w.sum()
                    if total <= 0:
                        return pd.Series(
                            {
                                "Redundancy_HHI": np.nan,
                            }
                        )
                    shares = w / total
                    return pd.Series(
                        {
                            "Redundancy_HHI": float(np.sum(shares**2)),
                        }
                    )

                red_df = g.apply(_redundancy_stats, include_groups = False)
                red_df.index = red_df.index.astype(str)

                df_main["Redundancy_HHI"] = df_main["tract_id"].map(
                    red_df["Redundancy_HHI"]
                )

        except Exception as e:
            logger.warning(f"Stage 7: failed to compute grid/logistics features: {e}")

    # ---------------------------------------------------------
    # D. SVI & Population Density (External Census Data, 4 themes)
    # ---------------------------------------------------------
    SVI_FILE_PATH = cfg.STAGE7_SVI_DATA_PATH
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
    NRI_FILE_PATH = cfg.STAGE7_NRI_DATA_PATH

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
    HOUSING_FILE_PATH = cfg.STAGE7_HOUSING_DATA_PATH

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

    # ---------------------------------------------------------
    # G. Compound slow-vulnerable hotspot score
    # ---------------------------------------------------------
    svi_cols_for_hotspot = [
        c
        for c in ["SVI_THEME1", "SVI_THEME2", "SVI_THEME3", "SVI_THEME4"]
        if c in df_main.columns
    ]
    if svi_cols_for_hotspot:
        df_main["Hotspot_SVI_Score"] = df_main[svi_cols_for_hotspot].mean(axis=1)
    elif "SVI_SCORE" in df_main.columns:
        df_main["Hotspot_SVI_Score"] = pd.to_numeric(df_main["SVI_SCORE"], errors="coerce")
    else:
        df_main["Hotspot_SVI_Score"] = np.nan

    def _rank_pct_component(source_col: str, out_col: str) -> bool:
        vals = pd.to_numeric(df_main.get(source_col), errors="coerce")
        vals = vals.replace([np.inf, -np.inf], np.nan)
        if vals.notna().sum() == 0 or vals.nunique(dropna=True) <= 1:
            df_main[out_col] = 0.0
            return False
        df_main[out_col] = vals.rank(pct=True, method="average").fillna(0.0)
        return True

    hotspot_component_defs = [
        ("T80", "Hotspot_T80_RankPct"),
        ("Pre_1970_Ratio", "Hotspot_Pre1970_RankPct"),
        ("NRI_RISK_SCORE", "Hotspot_NRI_Risk_RankPct"),
        ("Hotspot_SVI_Score", "Hotspot_SVI_RankPct"),
    ]
    hotspot_rank_cols = []
    for source_col, out_col in hotspot_component_defs:
        if source_col in df_main.columns and _rank_pct_component(source_col, out_col):
            hotspot_rank_cols.append(out_col)

    if hotspot_rank_cols:
        df_main["SlowVulnerable_Hotspot_Score"] = df_main[hotspot_rank_cols].sum(axis=1)
        df_main["SlowVulnerable_Hotspot_Rank"] = (
            df_main["SlowVulnerable_Hotspot_Score"]
            .rank(method="first", ascending=False)
            .astype(int)
        )
    else:
        logger.warning("Stage 7 hotspot score: no usable component columns found.")
        df_main["SlowVulnerable_Hotspot_Score"] = 0.0
        df_main["SlowVulnerable_Hotspot_Rank"] = np.arange(1, len(df_main) + 1)

    hotspot_top_n = int(getattr(cfg, "STAGE7_HOTSPOT_TOP_N", 10))
    df_main["SlowVulnerable_Hotspot_Top10"] = (
        df_main["SlowVulnerable_Hotspot_Rank"] <= hotspot_top_n
    )

    # =========================================================
    # 2. Clustering and PCA diagnostics
    # =========================================================
    # Avoid double-counting near-duplicate dimensions in the Stage 7
    # typology table. AUC is almost a monotone inverse of T80, and
    # NRI_EAL_SCORE closely tracks NRI_RISK_SCORE for this tract universe, so
    # keep the more interpretable representative from each pair.
    feat_cols = [
        "T80",
        "Init_Supply",
        "Grid_Degree",
        "Grid_Impact",
        "Grid_Betweenness",
        "Redundancy_HHI",
        "Pre_1970_Ratio",
        "Pop_Density",
        "NRI_RISK_SCORE",
        "NRI_BUILDVALUE",
    ] + svi_factor_cols  # svi_factor_cols is either the theme list or []

    # Filter out invalid/constant columns
    valid_cols = [c for c in feat_cols if c in df_main.columns and df_main[c].std() > 1e-6]
    logger.info(f"KMeans clustering on {len(valid_cols)} standardized features: {valid_cols}")

    X = df_main[valid_cols].values
    X_scaled = StandardScaler().fit_transform(X)

    # 2.1 Full PCA (Eigenvalues & Scree Plot)
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

    # 2.2 Select n_components (Automatic Kaiser Criterion)
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

    # 2.3 K-Means Clustering (Elbow + Silhouette) on standardized features.
    # PCA is retained for diagnostics/visualization, but it is not the
    # clustering feature space.
    from sklearn.metrics import silhouette_score

    Ks = list(range(1, 11))
    iners = []
    sils = []  # silhouette (None for k=1)

    for k in Ks:
        km = KMeans(n_clusters=k, random_state=cfg.RNG_SEED, n_init=10)
        labels = km.fit_predict(X_scaled)
        iners.append(km.inertia_)

        if k >= 2:
            # silhouette needs at least 2 clusters
            sils.append(silhouette_score(X_scaled, labels))
        else:
            sils.append(np.nan)

    # Elbow detection (distance to line between endpoints)
    p1, p2 = np.array([Ks[0], iners[0]]), np.array([Ks[-1], iners[-1]])
    dists = [
        np.abs(np.cross(p2 - p1, p1 - np.array([k, iners[k - Ks[0]]]))) / np.linalg.norm(p2 - p1)
        for k in Ks
    ]
    elbow_k = int(np.argmax(dists) + Ks[0])

    # Silhouette best-k (k >= 2)
    sil_ks = [k for k in Ks if k >= 2 and np.isfinite(sils[k - Ks[0]])]
    if sil_ks:
        sil_best_k = int(sil_ks[int(np.argmax([sils[k - Ks[0]] for k in sil_ks]))])
    else:
        sil_best_k = elbow_k  # fallback

    # Combine
    best_k = int(elbow_k)

    logger.info(f" > Elbow best k = {elbow_k}")
    logger.info(f" > Silhouette best k = {sil_best_k} (max silhouette = {sils[sil_best_k - Ks[0]]:.4f})")
    logger.info(f" > Selected Best k (Clusters) = {best_k}")

    # Optional: save a small CSV for debugging/record
    df_kdiag = pd.DataFrame(
        {
            "k": Ks,
            "inertia": iners,
            "silhouette": sils,
            "feature_space": "standardized_original_features",
        }
    )
    df_kdiag.to_csv(out_dir / "kmeans_k_diagnostics.csv", index=False)

    # Final clustering
    kmeans = KMeans(n_clusters=best_k, random_state=cfg.RNG_SEED, n_init=10)
    df_main["cluster"] = kmeans.fit_predict(X_scaled)

    # Append selected PC scores for visualization/interpretation only.
    for i in range(n_components):
        df_main[f"PC{i+1}"] = X_pca[:, i]

    hotspot_detail_cols = [
        "tract_id",
        "scenario",
        "cluster",
        "SlowVulnerable_Hotspot_Rank",
        "SlowVulnerable_Hotspot_Score",
        "T80",
        "Pre_1970_Ratio",
        "NRI_RISK_SCORE",
        "Hotspot_SVI_Score",
        "Hotspot_T80_RankPct",
        "Hotspot_Pre1970_RankPct",
        "Hotspot_NRI_Risk_RankPct",
        "Hotspot_SVI_RankPct",
        "T50",
        "Init_Supply",
    ]
    hotspot_detail_cols = [c for c in hotspot_detail_cols if c in df_main.columns]
    (
        df_main.sort_values("SlowVulnerable_Hotspot_Rank")
        .head(hotspot_top_n)[hotspot_detail_cols]
        .to_csv(out_dir / "stage7_top10_slow_vulnerable_tracts.csv", index=False)
    )

    # Keep only intended output columns
    cols_keep = [
        "tract_id",
        "scenario",
        "cluster",
        "T50",
        "T80",
        "Init_Supply",
        "Grid_Degree",
        "Grid_Impact",
        "Grid_Betweenness",
        "Redundancy_HHI",
        "Pre_1970_Ratio",
        "Pop_Density",
        "SVI_THEME1",
        "SVI_THEME2",
        "SVI_THEME3",
        "SVI_THEME4",
        "NRI_BUILDVALUE",
        "NRI_RISK_SCORE",
    ] + [f"PC{i+1}" for i in range(n_components)]

    cols_keep = [c for c in cols_keep if c in df_main.columns]
    df_main = df_main[cols_keep]

    df_main.to_csv(out_dir / "clusters_labels_final.csv", index=False)

    logger.info("--- STAGE 7 Complete ---")
    return {"clusters": df_main}


# ==========================================================================
# [PART 9] Main Execution Pipeline
# =============================================================================
# Contains: run_pipeline()/main() orchestration functions and entry point
def run_pipeline(cfg: Optional[Config] = None) -> None:
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
      8) Tract typology clustering (K-Means + PCA diagnostics)
    """
    # ---------------------------------------------------------------------
    # 1) Configuration & setup
    # ---------------------------------------------------------------------
    cfg = cfg if cfg is not None else Config()

    root_override = Path(OUTPUT_ROOT)
    root_override.mkdir(parents=True, exist_ok=True)

    log_file = root_override / getattr(cfg, "PIPELINE_LOG_FILENAME", "pipeline_run.log")
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

        # Stage 7: Tract typology clustering (K-Means + PCA diagnostics)
        run_stage_7(
            cfg,
            stage_3_data,
            stage_0_data,
            stage_1_data,
            out_dirs,
        )

        if cfg.RUN_SENSITIVITY_ANALYSIS:
            from build_sensitivity_outputs import run_sensitivity_analysis_2pc50

            run_sensitivity_analysis_2pc50()

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


def main() -> None:
    """Run the integrated earthquake-impact pipeline with the default config."""
    run_pipeline(Config())


if __name__ == "__main__":
    main()
