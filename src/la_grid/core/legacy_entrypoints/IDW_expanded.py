"""Expanded-area wrapper for PGA interpolation.

This wrapper keeps the original IDW interpolation logic unchanged and only
rewires the expanded-area input/output paths.
"""

from pathlib import Path

import la_grid.core.IDW as base
from la_grid.paths import REPO_ROOT as PROJECT_ROOT
DATA_DIR = PROJECT_ROOT / "Data"


EXPANDED_CONFIG = base.IDWConfig(
    sub_csv=str(DATA_DIR / "working_area_substations_with_fragility.csv"),
    final_output_csv=str(DATA_DIR / "Substations_PGA_IDW_CEC_expanded.csv"),
)


def main() -> None:
    base.main(EXPANDED_CONFIG)


if __name__ == "__main__":
    main()
