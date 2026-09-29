"""Stage 03 — Strategy and GA Freeze

Purpose:
    Validate frozen rule sequences, GA provenance, incumbent and final strategy registry.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    Fixed strategy sequences; GA result identities; frozen Vulnerability-first sequence

Primary outputs:
    FINAL_STRATEGY_SET.json and stage validation manifest

Default mode:
    --resume (validate and reuse existing authoritative outputs)

Does NOT:
    Does not run GA or rerank Vulnerability-first.
"""
from pathlib import Path
import sys

# One bootstrap line locates the repository package when this file is run by path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from FINAL_REVISION_RUN_SEQUENCE.stage_runner import run_stage_cli

if __name__ == "__main__":
    raise SystemExit(run_stage_cli("03"))
