"""Stage 08 — Final Stage 7 Typology

Purpose:
    Validate the harmonized Stage 7 authority and its saved products.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    Stage 7 Output_SOVI_Harmonized identity and output inventory

Primary outputs:
    Stage 8 output hash manifest and stage validation manifest

Default mode:
    --resume (validate and reuse existing authoritative outputs)

Does NOT:
    Does not rerun PCA, K-means or hotspot analysis.
"""
from pathlib import Path
import sys

# One bootstrap line locates the repository package when this file is run by path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from FINAL_REVISION_RUN_SEQUENCE.stage_runner import run_stage_cli

if __name__ == "__main__":
    raise SystemExit(run_stage_cli("08"))
