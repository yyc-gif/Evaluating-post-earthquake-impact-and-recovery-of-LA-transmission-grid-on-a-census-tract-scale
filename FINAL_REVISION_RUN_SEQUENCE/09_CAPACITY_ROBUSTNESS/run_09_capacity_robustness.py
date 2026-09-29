"""Stage 09 — SCE Capacity Robustness

Purpose:
    Validate the closed SCE-supported capacity sensitivity outputs.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    Frozen trajectories; supported-station table; capacity closure results and figure

Primary outputs:
    Capacity summary/station/tract outputs and figure hashes

Default mode:
    --resume (validate and reuse existing authoritative outputs)

Does NOT:
    Does not execute capacity closure, reschedule or rerun GA.
"""
from pathlib import Path
import sys

# One bootstrap line locates the repository package when this file is run by path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from FINAL_REVISION_RUN_SEQUENCE.stage_runner import run_stage_cli

if __name__ == "__main__":
    raise SystemExit(run_stage_cli("09"))
