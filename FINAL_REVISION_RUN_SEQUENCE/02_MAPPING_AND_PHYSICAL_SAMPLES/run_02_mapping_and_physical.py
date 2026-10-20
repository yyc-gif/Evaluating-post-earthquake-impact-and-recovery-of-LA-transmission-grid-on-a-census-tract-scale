"""Stage 02 — Mapping and Physical Samples

Purpose:
    Validate and reuse the production mapping and frozen physical/planning samples.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    M1 mapping; 4,000 evaluation and 64 planning sample identities

Primary outputs:
    Stage validation manifest and frozen sample identities

Default mode:
    --resume (validate and reuse existing authoritative outputs)

Does NOT:
    Does not regenerate damage or planning/evaluation samples.
"""
from pathlib import Path
import sys

# One bootstrap line locates the repository package when this file is run by path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from FINAL_REVISION_RUN_SEQUENCE.stage_runner import run_stage_cli

if __name__ == "__main__":
    raise SystemExit(run_stage_cli("02"))
