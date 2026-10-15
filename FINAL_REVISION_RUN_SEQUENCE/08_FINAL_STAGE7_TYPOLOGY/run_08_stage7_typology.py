"""Stage 08 — Final Stage 7 Typology

Purpose:
    Validate the adopted seven-variable P2/K3 authority and saved products.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    results/stage7/2026-10-14 and config/current_stage7.json

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
