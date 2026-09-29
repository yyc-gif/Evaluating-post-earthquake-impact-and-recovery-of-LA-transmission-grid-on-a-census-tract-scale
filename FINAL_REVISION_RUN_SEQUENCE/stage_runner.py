"""Shared read-only runner for individual stages and the canonical run_all command."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if Path(getattr(sys.modules.get("__main__"), "__file__", "")).resolve() == (HERE / "run_all.py").resolve():
    # run_all.py was invoked directly; reuse that exact module instance.
    validator = sys.modules["__main__"]
else:
    # Individual wrappers import this package and share the same validator source.
    from . import run_all as validator
STAGE_IDS = {name: sid for sid, name in validator.STAGES}

def run_stage(stage_id: str, *, matrix=None, registry=None, run_manifest=None):
    """Invoke the canonical validator for one stage; never generate scientific outputs."""
    matrix = matrix if matrix is not None else validator.read_json(HERE / "FINAL_REVISION_RUN_MATRIX.json")
    registry = registry if registry is not None else validator.read_json(HERE / "EXTERNAL_ARCHIVE_MANIFEST.json")
    if stage_id not in dict(validator.STAGES):
        raise validator.ValidationError(f"Unknown stage id: {stage_id}")
    if stage_id not in matrix.get("stage_authorities", {}):
        raise validator.ValidationError(f"Canonical matrix lacks stage authority for {stage_id}")
    if run_manifest is None:
        run_manifest = {"workflow":"FINAL_REVISION_RUN_SEQUENCE","mode":"resume","status":"RUNNING_VALIDATION","started_at_utc":datetime.now(timezone.utc).isoformat(),"repository_head":validator.run_git("rev-parse","HEAD"),"branch":validator.run_git("branch","--show-current"),"parent_matrix_id":matrix["parent_frozen_design"]["matrix_id"],"parent_matrix_sha256":matrix["parent_frozen_design"]["matrix_sha256"],"scientific_computation_performed":False,"stages":[]}
    return validator.validate_stage(stage_id, registry, run_manifest)

def run_stage_cli(stage_id: str, argv=None) -> int:
    parser=argparse.ArgumentParser(description=f"Validate/reuse canonical Stage {stage_id}; no science is run.")
    parser.add_argument("--resume",action="store_true",help="validate and reuse existing authoritative outputs only")
    args=parser.parse_args(argv)
    if not args.resume:
        parser.error("Specify --resume. This stage only validates and reuses frozen outputs.")
    try:
        run_stage(stage_id)
    except Exception as exc:
        print(f"Stage {stage_id}: FAIL — {type(exc).__name__}: {exc}",file=sys.stderr)
        return 2
    return 0
