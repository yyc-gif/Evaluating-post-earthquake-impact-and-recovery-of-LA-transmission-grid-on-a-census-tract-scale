"""Stage 05 — Service and Tract Evaluation

Purpose:
    Validate frozen offline evaluations and accepted service/distribution results.

Scientific implementation:
    Existing authority modules under src/la_grid/; this entrypoint performs validation/reuse only.

Primary inputs:
    Formal/equity offline shards; tract weights; result indexes

Primary outputs:
    Offline shard and result authority hashes

Default mode:
    --resume (validate and reuse existing authoritative outputs)

Does NOT:
    Does not recompute service or burden metrics.
"""
from pathlib import Path
import sys

# One bootstrap line locates the repository package when this file is run by path.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from FINAL_REVISION_RUN_SEQUENCE.stage_runner import run_stage_cli

if __name__ == "__main__":
    raise SystemExit(run_stage_cli("05"))
