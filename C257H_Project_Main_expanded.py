"""Expanded-area thin wrapper for the integrated earthquake impact pipeline."""

import os
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
    MAP_TRACT_SUB_CSV: str = str(DATA_DIR / "tract_to_substation_mapping_CEC_expanded.csv")
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


def main() -> None:
    """Run the integrated earthquake-impact pipeline with the expanded study-area config."""
    base.run_pipeline(ExpandedConfig())


if __name__ == "__main__":
    main()
