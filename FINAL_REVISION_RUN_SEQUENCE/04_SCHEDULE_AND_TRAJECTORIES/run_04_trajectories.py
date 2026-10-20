"""Stage 04 — Schedules and Trajectories

Purpose:
    Validate and reuse the frozen formal and Vulnerability-first event archives.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    84,000 formal and 10,000 Vulnerability-first trajectory archives and identity indexes

Primary outputs:
    Trajectory identity checks and stage validation manifest

Default mode:
    --resume (validate and reuse existing authoritative outputs)

Does NOT:
    Does not sample, schedule or dispatch.
"""
from pathlib import Path
import sys

# One bootstrap line locates the repository package when this file is run by path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from FINAL_REVISION_RUN_SEQUENCE.stage_runner import run_stage_cli

if __name__ == "__main__":
    raise SystemExit(run_stage_cli("04"))
