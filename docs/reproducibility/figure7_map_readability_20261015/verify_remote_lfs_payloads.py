"""Fetch this update's LFS assets into a fresh store and verify their bytes."""
from __future__ import annotations

import hashlib
import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = "0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68"
PUSHED = "33b048adabad0791a5db959143d006eeb317a798"
REMOTE_REF = "refs/heads/1021"
POINTER = re.compile(rb"oid sha256:([0-9a-f]{64})\nsize (\d+)")


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true", help="verify remote bytes without replacing the saved receipt")
    parser.add_argument("--storage", help="reuse an existing isolated LFS store instead of allocating another temporary copy")
    args = parser.parse_args()
    remote_head = git("ls-remote", "origin", REMOTE_REF).decode().split()[0]
    subprocess.run(["git", "-C", str(ROOT), "fetch", "--quiet", "origin", REMOTE_REF], check=True)
    ancestor = subprocess.run(
        ["git", "-C", str(ROOT), "merge-base", "--is-ancestor", PUSHED, "FETCH_HEAD"],
        check=False,
    )
    assert ancestor.returncode == 0, (remote_head, PUSHED)
    changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", PUSHED).decode().splitlines()
    objects: dict[str, dict[str, object]] = {}
    lfs_paths = []
    for rel in changed:
        blob = git("show", f"{PUSHED}:{rel}")
        match = POINTER.search(blob)
        if not match or not blob.startswith(b"version https://git-lfs.github.com/spec/v1"):
            continue
        oid, size = match.group(1).decode(), int(match.group(2))
        lfs_paths.append(rel)
        record = objects.setdefault(oid, {"sha256": oid, "size": size, "paths": []})
        record["paths"].append(rel)

    assert len(objects) >= 24, f"Expected at least the 24 uploaded LFS objects, found {len(objects)}"
    storage = Path(args.storage) if args.storage else Path(tempfile.mkdtemp(prefix="fig7_lfs_remote_verify_"))
    assert (storage / "objects").is_dir(), f"LFS storage has no objects directory: {storage}"
    include = ",".join(sorted(lfs_paths))
    fetch = subprocess.run(
        ["git", "-C", str(ROOT), "-c", f"lfs.storage={storage}", "lfs", "fetch",
         f"--include={include}", "origin", PUSHED],
        check=True,
        capture_output=True,
        text=True,
    )

    for oid, record in objects.items():
        candidates = list((storage / "objects").glob(f"{oid[:2]}/{oid[2:4]}/{oid}"))
        assert len(candidates) == 1, f"Fresh remote LFS payload not found for {oid}"
        payload = candidates[0].read_bytes()
        actual = hashlib.sha256(payload).hexdigest()
        assert actual == oid and len(payload) == record["size"], oid
        record["verified_bytes"] = len(payload)
        record["verified_sha256"] = actual

    result = {
        "remote": "origin",
        "remote_ref": REMOTE_REF,
        "remote_head_at_verification": remote_head,
        "pushed_commit": PUSHED,
        "remote_head_contains_pushed_commit": True,
        "baseline_commit": BASE,
        "fresh_lfs_store": str(storage),
        "fetch_output": fetch.stdout.strip(),
        "lfs_paths_checked": len(lfs_paths),
        "unique_lfs_objects_checked": len(objects),
        "all_actual_payload_sha256_and_sizes_match_pointers": True,
        "objects": sorted(objects.values(), key=lambda item: item["sha256"]),
    }
    output = ROOT / "docs/reproducibility/figure7_map_readability_20261015/REMOTE_LFS_PAYLOAD_VERIFICATION.json"
    if not args.no_write:
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
