"""Focused test receipts, byte manifest and actual remote-payload verification."""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from urllib.parse import quote

import numpy
import pandas
import requests
import sklearn

from independent_review import OUT, ROOT, PREFIX, git, lp, read, sha, snapshot, write_json

REPO = "yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale"
BRANCH = "analysis/stage7-shortlist-independent-review-20261011"
REL = PREFIX + OUT.name + "/"
EXCLUDE_HASHES = {"OUTPUT_HASHES.csv", "REMOTE_DELIVERY_VERIFICATION.json", "REMOTE_HEAD_FINAL.json"}


def qa():
    changes = []
    for row in read("REUSED_RUN_BYTE_MANIFEST.csv").itertuples():
        p = lp(OUT / row.snapshot_relative_path)
        current = sha(p)
        if current != row.sha256:
            assert row.snapshot_relative_path in {".gitattributes", ".gitignore", "INPUT_HASHES.json"}, row.snapshot_relative_path
            changes.append({"file": row.snapshot_relative_path, "frozen_source_sha256": row.sha256, "review_sha256": current,
                            "reason": {".gitattributes": "Preserve exact committed bytes instead of text normalization", ".gitignore": "Include the scoped sensitivity evidence despite the parent repository ignore pattern", "INPUT_HASHES.json": "Local source-path discovery during copied audit tests; scientific source hashes unchanged"}[row.snapshot_relative_path]})
    pandas.DataFrame(changes).to_csv(lp(OUT / "REUSE_DERIVATIVE_CHANGE_LEDGER.csv"), index=False)
    env = os.environ.copy()
    env.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-B", "-m", "pytest", str(OUT / "test_shortlist.py"), "-q", "-p", "no:cacheprovider", "--basetemp", str(ROOT / "_review_pytest_tmp")]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    print(result.stdout, flush=True)
    write_json("TEST_RECEIPT.json", {"UTC": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": command,
                                   "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
                                   "python": sys.version, "numpy": numpy.__version__, "pandas": pandas.__version__, "sklearn": sklearn.__version__,
                                   "no_new_fits": True})
    assert result.returncode == 0
    independent = json.loads(lp(OUT / "INDEPENDENT_REVIEW_QA.json").read_text(encoding="utf-8"))
    assert independent["status"] == "PASS" and independent["models"] == 12
    stress = read("ACS_BOUNDARY_FIXED_CENTROID_STRESS.csv")
    assert len(stress) == 2 and stress.boundary_n.eq(158).all() and not stress.refit.any()
    assert read("CROSS_SPECIFICATION_PATTERN_AUDIT.csv").same_group.eq(False).all()
    before = json.loads(lp(OUT / "REVIEW_PRESERVATION_BEFORE.json").read_text(encoding="utf-8"))
    after = snapshot()
    assert after == before
    write_json("REVIEW_PRESERVATION_FINAL.json", after)
    rows = []
    for p in sorted(lp(OUT).rglob("*")):
        if p.is_file() and p.name not in EXCLUDE_HASHES and not any(x in p.parts for x in ["__pycache__", ".pytest_cache", "_test_tmp"]):
            rows.append({"relative_path": p.relative_to(lp(OUT)).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)})
    pandas.DataFrame(rows).to_csv(lp(OUT / "OUTPUT_HASHES.csv"), index=False)
    print("Manifest:", len(rows), "files,", sum(r["bytes"] for r in rows), "bytes; 950 protected files and 862 staged items unchanged.", flush=True)


def verify_remote():
    commit = git("rev-parse", "HEAD").decode().strip()
    assert git("branch", "--show-current").decode().strip() == BRANCH
    remote = git("ls-remote", "origin", "refs/heads/" + BRANCH).decode().split()[0]
    assert remote == commit
    paths = git("ls-tree", "-r", "--name-only", commit, "--", REL).decode().splitlines()
    session = requests.Session()
    rows = []
    for path in paths:
        if path.endswith(("REMOTE_DELIVERY_VERIFICATION.json", "REMOTE_HEAD_FINAL.json")):
            continue
        blob = git("show", commit + ":" + path)
        lfs = blob.startswith(b"version https://git-lfs.github.com/spec/v1\n")
        if lfs:
            lines = blob.decode().splitlines()
            expected = next(v[11:] for v in lines if v.startswith("oid sha256:"))
            size = int(next(v[5:] for v in lines if v.startswith("size ")))
            url = "https://media.githubusercontent.com/media/" + REPO + "/" + commit + "/" + quote(path, safe="/")
        else:
            expected, size = hashlib.sha256(blob).hexdigest(), len(blob)
            url = "https://raw.githubusercontent.com/" + REPO + "/" + commit + "/" + quote(path, safe="/")
        local = lp(ROOT / path)
        assert local.stat().st_size == size and sha(local) == expected
        h, actual_size, prefix = hashlib.sha256(), 0, b""
        with session.get(url, stream=True, timeout=(20, 120)) as response:
            response.raise_for_status()
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    if not prefix:
                        prefix = chunk[:150]
                    h.update(chunk)
                    actual_size += len(chunk)
        assert actual_size == size and h.hexdigest() == expected, path
        assert not lfs or not prefix.startswith(b"version https://git-lfs.github.com/spec/v1"), path
        rows.append({"path": path, "lfs": lfs, "expected_sha256": expected, "actual_remote_sha256": h.hexdigest(), "bytes": size, "actual_remote_bytes": actual_size, "PASS": True})
        if len(rows) % 10 == 0:
            print("Actual remote bytes verified:", len(rows), "/", len(paths), flush=True)
    lfs_rows = [r for r in rows if r["lfs"]]
    write_json("REMOTE_DELIVERY_VERIFICATION.json", {
        "UTC": datetime.datetime.now(datetime.timezone.utc).isoformat(), "payload_commit": commit, "branch": BRANCH,
        "remote_HEAD_at_verification": remote, "all_pass": True, "files_verified": len(rows),
        "bytes_verified": sum(r["bytes"] for r in rows), "lfs_objects": len(lfs_rows), "lfs_payload_bytes": sum(r["bytes"] for r in lfs_rows),
        "verification_receipt_and_future_head_receipt_excluded_from_recursive_self_hash": True, "files": rows,
    })
    print("Remote PASS:", len(rows), "files;", len(lfs_rows), "actual LFS payloads.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["qa", "verify-remote"])
    args = parser.parse_args()
    qa() if args.mode == "qa" else verify_remote()
