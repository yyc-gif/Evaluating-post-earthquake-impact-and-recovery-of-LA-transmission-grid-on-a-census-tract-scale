"""Rerun only Stage 7 from frozen Stage 1/2/5 tables using NRI SOVI_SCORE.

No physical sample, restoration trajectory, or Stage 1-6 routine is called.
"""
import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from la_grid.core.C257H_Project_Main import Config, run_stage_7


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-existing-stage7-only", action="store_true",
                        help="Explicitly replace only the harmonized Stage 7 tables")
    parser.add_argument("--verify-existing", action="store_true",
                        help="Read-only verification of the completed harmonized Stage 7; no clustering")
    args = parser.parse_args()
    root = Path("Formal_Experiment_20260923")
    if args.verify_existing:
        if args.refresh_existing_stage7_only:
            parser.error("--verify-existing and --refresh-existing-stage7-only are exclusive")
        from la_grid.revision.r1_stage7_harmonized import verify_harmonized_stage7
        print(verify_harmonized_stage7(root))
        return
    stage7 = root / "Stage 7 Output_SOVI_Harmonized"
    if stage7.exists() and any(stage7.iterdir()) and not args.refresh_existing_stage7_only:
        raise FileExistsError(f"Refusing to overwrite Stage 7 output without explicit flag: {stage7}")
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
