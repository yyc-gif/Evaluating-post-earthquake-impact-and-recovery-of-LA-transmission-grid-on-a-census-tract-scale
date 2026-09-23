"""Expanded-area thin wrapper for the integrated earthquake impact pipeline."""

import os
import argparse
from dataclasses import dataclass
from pathlib import Path

import C257H_Project_Main as base


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Data"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT
OUTPUT_ROOT = str(DEFAULT_OUTPUT_ROOT)


def stage_dir(stage: str) -> str:
    """Return the expanded-area output directory for a numbered pipeline stage."""
    return os.path.join(OUTPUT_ROOT, f"Stage {stage} Output_expanded")


def stage_file(stage: str, filename: str) -> str:
    """Build an absolute path inside the expanded-area output directory for one stage."""
    return os.path.join(stage_dir(stage), filename)


@dataclass
class ExpandedConfig(base.Config):
    """Expanded-area pipeline configuration overriding the base city-scale file layout."""
    DEVICES_CSV: str = str(DATA_DIR / "working_area_substations_with_fragility.csv")
    PGA_CSV: str = str(DATA_DIR / "Substations_PGA_IDW_CEC_expanded.csv")
    MAP_TRACT_SUB_CSV: str = str(DATA_DIR / "JULY_UTILITY_CONSTRAINED_92.csv")
    JULY_BASELINE_MAPPING_CSV: str = str(DATA_DIR / "tract_to_substation_mapping_CEC_expanded.csv")
    MAPPING_METHOD: str = "JULY_UTILITY_CONSTRAINED_92"
    SENSITIVITY_RAW_MAPPING_CSV: str = str(
        DATA_DIR / "JULY_UTILITY_CONSTRAINED_92_UNTHRESHOLDED.csv"
    )
    CEC_GRAPH_EDGES_CSV: str = str(DATA_DIR / "substation_graph_CEC_edges_expanded.csv")
    CEC_GRAPH_NODES_CSV: str = str(DATA_DIR / "substation_graph_CEC_nodes_expanded.csv")
    SOURCE_NODES_CSV: str = str(DATA_DIR / "source_nodes_core_expanded.csv")
    HOSPITAL_TRACTS_CSV: str = str(DATA_DIR / "hospital_with_tract_expanded.csv")
    STAGE7_SVI_DATA_PATH: str = str(DATA_DIR / "California.csv")
    STAGE7_NRI_DATA_PATH: str = str(DATA_DIR / "NRI_Table_CensusTracts_California.csv")
    STAGE7_HOUSING_DATA_PATH: str = str(DATA_DIR / "ACSDT5Y2022.B25034-Data.csv")
    SVI_CSV: str = str(DATA_DIR / "LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv")

    TRAVEL_BASE_TO_TASK_CSV: str = stage_file("4", "travel_base_to_task.csv")
    TRAVEL_TASK_TO_TASK_CSV: str = stage_file("4", "travel_task_to_task.csv")

    STAGE1_DIR: str = "Stage 1 Output_expanded"
    STAGE2_DIR: str = "Stage 2 Output_expanded"
    STAGE3_DIR: str = "Stage 3 Output_expanded"
    STAGE4_DIR: str = "Stage 4 Output_expanded"
    STAGE5_DIR: str = "Stage 5 Output_expanded"
    STAGE6_DIR: str = "Stage 6 Output_expanded"
    STAGE7_DIR: str = "Stage 7 Output_expanded"
    PIPELINE_LOG_FILENAME: str = "pipeline_run_expanded.log"
    REPAIR_TASK_MIN_MEAN_HR: float = 1.0
    REVISION_EVENT_PATH: bool = True
    REVISION_TRIAL: bool = False
    REVISION_FINAL_MATRIX_FROZEN: bool = False
    REVISION_PLANNING_N: int = 0
    REVISION_GA_SEEDS: tuple = (42, 43)
    REVISION_OFFLINE_EVALUATION: bool = True


def main() -> None:
    """Run the integrated earthquake-impact pipeline with the expanded study-area config."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--revised-trial', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--resume', action='store_true', help='Reuse retained physical samples and completed stage archives; no resampling.')
    parser.add_argument('--legacy', action='store_true', help='Explicit July reproduction path; retains all original stages.')
    args = parser.parse_args()
    cfg = ExpandedConfig()
    if args.legacy:
        cfg.REVISION_EVENT_PATH = False
        cfg.MAP_TRACT_SUB_CSV = cfg.JULY_BASELINE_MAPPING_CSV
    if args.revised_trial:
        if args.legacy or args.output is None:
            parser.error('--revised-trial requires --output and cannot use --legacy')
        output = args.output.resolve()
        if output.exists() and not args.resume:
            parser.error('Output already exists; use --resume to reuse retained inputs/results')
        output.mkdir(parents=True, exist_ok=args.resume)
        base.OUTPUT_ROOT = str(output)
        cfg.OUTPUT_DIRECTORY = str(output)
        cfg.REVISION_TRIAL = True
        cfg.SCENARIOS = ('2pc50',)
        cfg.N_MC = 3
        cfg.REVISION_PLANNING_N = 2
        cfg.GA_POP_SIZE = 8
        cfg.GA_N_GEN = 3
        cfg.N_CORES = 1
        cfg.MC_SOURCE_GATE_N_JOBS = 1
        cfg.RUN_SENSITIVITY_ANALYSIS = False  # offline evaluation, not July re-execution sensitivity
    base.run_pipeline(cfg)


if __name__ == "__main__":
    main()
