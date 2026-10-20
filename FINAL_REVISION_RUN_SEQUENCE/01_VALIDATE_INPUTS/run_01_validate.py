"""Stage 01 — Validate Inputs

Purpose:
    Verify frozen configuration, input identities, code authority and protected archive identity.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    config/parent_frozen_design/FINAL_EXPERIMENT_MATRIX.json; frozen model/mapping/travel inputs; external archive registry

Primary outputs:
    01_VALIDATION_MANIFEST.json and stage validation manifest

Default mode:
    --resume (validate and reuse existing authoritative outputs)

Does NOT:
    No sampling, model execution or fallback.
"""
from pathlib import Path
import sys

# One bootstrap line locates the repository package when this file is run by path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from FINAL_REVISION_RUN_SEQUENCE.stage_runner import run_stage_cli

if __name__ == "__main__":
    raise SystemExit(run_stage_cli("01"))
