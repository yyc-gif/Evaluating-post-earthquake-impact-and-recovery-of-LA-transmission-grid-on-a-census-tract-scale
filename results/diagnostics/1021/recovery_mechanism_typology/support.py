"""Scoped outputs and read-only reuse of hash-bound prior sources."""
import importlib.util
import json
import os
from pathlib import Path
import sys

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
PRIOR = PARENT / "engineering_value_20261015"
spec = importlib.util.spec_from_file_location("prior_source_authority", PRIOR / "common.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
ROOT, AUTH, ARCHIVE, FORMAL = legacy.ROOT, legacy.AUTH, legacy.ARCHIVE, legacy.FORMAL
sha, git, payload, csv_payload = legacy.sha, legacy.git, legacy.payload, legacy.csv_payload
START = "5e6a950e2bf58fc72279991430dd0ed5731f6d3f"
import numpy as np
import pandas as pd


def save(name, rows):
    pd.DataFrame(rows).to_csv(HERE/name, index=False, float_format="%.17g", lineterminator="\n")


def dump(name, obj):
    (HERE/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+"\n", newline="\n")


def inputs():
    a, f, refs = legacy.inputs()
    registry = json.loads((HERE/"FROZEN_INPUT_REGISTRY.json").read_text())
    for rel, wanted in registry["preserved_prior_payloads"].items():
        assert sha(PARENT/rel) == wanted, rel
    d = pd.read_csv(PRIOR/"UNFITTED_TRACT_OUTCOMES.csv", dtype={"tract_id": str})
    np.testing.assert_array_equal(d.tract_id, f.tract_id)
    return a, f, refs, d


def snapshot():
    sys.path.insert(0, str(PARENT))
    import preflight
    return preflight.snapshot()
