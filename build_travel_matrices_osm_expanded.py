"""Expanded-area wrapper for OSM travel matrix generation.

This wrapper reuses the original implementation from
`build_travel_matrices_osm.py` and only swaps the expanded-area input/output
paths.
"""

from pathlib import Path

import build_travel_matrices_osm as base


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Data"


EXPANDED_CONFIG = base.TravelMatrixConfig(
    graphml_path=str(DATA_DIR / "la_drive.graphml"),
    subs_csv=str(DATA_DIR / "working_area_substations_with_fragility.csv"),
    output_root=str(PROJECT_ROOT),
    stage4_dir="Stage 4 Output_expanded",
    travel_base_to_task_csv="travel_base_to_task.csv",
    travel_task_to_task_csv="travel_task_to_task.csv",
    mapping_csv=str(DATA_DIR / "tract_to_substation_mapping_CEC_expanded.csv"),
    # Fallbacks are coordinate lookup only. They do not add substations outside
    # the current expanded mapping target set.
    substation_coordinate_fallback_csvs=(
        str(DATA_DIR / "working_area_substations_with_fragility_original.csv"),
        str(DATA_DIR / "Substations_PGA_IDW_CEC_expanded.csv"),
        str(DATA_DIR / "Los_Angeles_City_SUBSTATION_with_fragility_ORIGINAL.csv"),
    ),
    limit_to_sub_ids=None,
)


def main() -> None:
    base.main(EXPANDED_CONFIG)


if __name__ == "__main__":
    main()
