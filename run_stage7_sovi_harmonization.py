"""Rerun only Stage 7 from frozen Stage 1/2/5 tables using NRI SOVI_SCORE.

No physical sample, restoration trajectory, or Stage 1-6 routine is called.
"""
from dataclasses import replace
from pathlib import Path

import pandas as pd

from C257H_Project_Main import Config, run_stage_7


def main() -> None:
    root = Path("Formal_Experiment_20260923")
    stage7 = root / "Stage 7 Output_SOVI_Harmonized"
    if stage7.exists() and any(stage7.iterdir()):
        raise FileExistsError(f"Refusing to overwrite Stage 7 result: {stage7}")
    stage7.mkdir(parents=True, exist_ok=True)
    paths = {
        "STAGE1_DIR": root / "Stage 1 Output_expanded",
        "STAGE2_DIR": root / "Stage 2 Output_expanded",
        "STAGE5_DIR": root / "Stage 5 Output_expanded",
        "STAGE7_DIR": stage7,
    }
    mapping = pd.read_csv("Data/JULY_UTILITY_CONSTRAINED_92.csv")
    cfg = replace(Config(), RUN_STAGE_7=True)
    cfg.REVISION_FORMAL = True
    result = run_stage_7(cfg, {}, {"mapping_df": mapping}, {}, paths)
    print(f"Stage 7-only completed: {len(result['clusters'])} tracts in {stage7}")


if __name__ == "__main__":
    main()
