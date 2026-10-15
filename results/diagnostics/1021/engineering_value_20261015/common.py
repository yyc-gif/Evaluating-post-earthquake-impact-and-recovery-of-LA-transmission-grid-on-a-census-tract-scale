"""Hash-bound inputs; all writes confined to this follow-up directory."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
ROOT = HERE.parents[3]
AUTH = ROOT / "results/stage7/2026-10-14"
START = "3f10ff621a2aab36d056f6dfcb6be8dc750f91aa"
FROZEN = "b307e6deafc054864787a3db63ad95218be91659"
ARCHIVE = Path(os.environ.get("LA_GRID_FROZEN_SOURCE_ROOT", "C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/LA_grid_reviewer_revision"))
FORMAL = "Formal_Experiment_20260923/"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def payload(rel):
    blob = git("show", START+":"+rel)
    match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n", blob)
    if not match:
        return blob
    oid = match[1].decode()
    common = Path(git("rev-parse", "--git-common-dir").decode().strip())
    if not common.is_absolute():
        common = ROOT/common
    candidates = [ROOT/rel, ARCHIVE/rel, common/"lfs/objects"/oid[:2]/oid[2:4]/oid]
    for p in candidates:
        if p.is_file() and sha(p) == oid:
            return p.read_bytes()
    raise FileNotFoundError(f"Fetch actual LFS payload: {rel} {oid}")


def csv_payload(rel, **kwargs):
    return pd.read_csv(io.BytesIO(payload(rel)), **kwargs)


def save(name, rows):
    pd.DataFrame(rows).to_csv(HERE/name, index=False, float_format="%.17g", lineterminator="\n")


def dump(name, value):
    (HERE/name).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", newline="\n")


def inputs():
    manifest = json.loads((AUTH/"ARTIFACT_HASHES.json").read_text())
    assert all(sha(AUTH/k) == v for k, v in manifest.items())
    old = json.loads((PARENT/"PACKAGE_HASHES.json").read_text())
    assert all(sha(PARENT/k) == v for k, v in old.items())
    a = np.load(AUTH/"preprocessing_and_labels.npz", allow_pickle=False)
    f = pd.read_csv(AUTH/"tract_features.csv", dtype={"tract_id": str})
    z = np.load(PARENT/"outputs/ALL_FITTED_ARRAYS.npz", allow_pickle=False)
    assert np.array_equal(a["tract_ids"], f.tract_id)
    assert len(f) == 2299 and f.Population.sum() == 9066522
    labels = {2: z["full_k2_s42_labels"], 3: a["K3_labels"], 4: a["K4_sensitivity_labels"]}
    return a, f, labels


def meaningful(name):
    if "unreached" in name:
        return .05
    if "T80" in name:
        return 6.
    if "early24" in name:
        return 2.
    if "middle24_72" in name:
        return 3.
    return 5.


def mae_margin(name):
    if "unreached" in name:
        return .02
    if "T80" in name:
        return 2.
    if "early24" in name or "middle24_72" in name:
        return .5
    return 1.
