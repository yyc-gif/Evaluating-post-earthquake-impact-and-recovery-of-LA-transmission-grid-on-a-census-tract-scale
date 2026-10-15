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
sha, git = legacy.sha, legacy.git
START = "5e6a950e2bf58fc72279991430dd0ed5731f6d3f"
import numpy as np
import pandas as pd


def payload(rel):
    try:
        return legacy.payload(rel)
    except FileNotFoundError:
        pointer = git("show", legacy.START+":"+rel)
        match = legacy.re.search(rb"oid sha256:([0-9a-f]{64})", pointer)
        if not match:
            raise
        oid = match[1].decode()
        common = Path(git("rev-parse", "--git-common-dir").decode().strip())
        # Windows' normal path APIs can reject this shared cache's long paths.
        p = Path("\\\\?\\"+str(common/"lfs/objects"/oid[:2]/oid[2:4]/oid))
        if p.is_file() and sha(p) == oid:
            return p.read_bytes()
        raise


def csv_payload(rel, **kwargs):
    return pd.read_csv(legacy.io.BytesIO(payload(rel)), **kwargs)


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
