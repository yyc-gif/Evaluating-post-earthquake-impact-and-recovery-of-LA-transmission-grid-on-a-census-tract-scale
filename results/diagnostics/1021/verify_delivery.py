"""Download actual committed 1021 LFS payloads into an empty store and hash them."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

from preflight import BASE, HERE, ROOT


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args],
                                   env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()


def main(write=True):
    head = git("rev-parse", "refs/heads/1021").decode().strip()
    remote = lambda branch: git("ls-remote", "origin", "refs/heads/"+branch).decode().split()[0]
    assert remote("1021") == head
    assert remote("2026-10-14") == BASE
    paths = git("diff", "--name-only", BASE, head).decode().splitlines()
    assert all(p.startswith("results/diagnostics/1021/") for p in paths)
    payloads = []
    for path in paths:
        blob = git("show", head+":"+path)
        match = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n", blob)
        if match:
            payloads.append({"path": path, "oid": match[1].decode(), "size": int(match[2])})
    assert payloads
    cache = ROOT / "build" / ("remote_1021_"+str(time.time_ns()))
    assert not cache.exists()
    cache.mkdir(parents=True)
    fetch = subprocess.run(["git", "-C", str(ROOT), "-c", "lfs.storage="+str(cache), "lfs", "fetch",
                            "--include="+",".join(r["path"] for r in payloads), "--exclude=", "origin", head],
                           text=True, capture_output=True)
    assert fetch.returncode == 0, fetch.stdout+fetch.stderr
    for row in payloads:
        oid = row["oid"]
        actual = cache / "objects" / oid[:2] / oid[2:4] / oid
        assert actual.stat().st_size == row["size"]
        assert sha(actual) == oid == sha(ROOT / row["path"])
    assert remote("1021") == head and remote("2026-10-14") == BASE
    result = {"status": "PASS_ACTUAL_REMOTE_PAYLOAD_BYTES", "artifact_commit": head,
              "branch": "1021", "remote_HEAD_matches": True, "empty_download_store": True,
              "October14_remote_unchanged": BASE,
              "paths_verified": len(payloads),
              "unique_bytes_downloaded": sum({r["oid"]: r["size"] for r in payloads}.values()),
              "payloads": payloads}
    if write:
        (HERE / "REMOTE_DELIVERY_VERIFICATION.json").write_text(json.dumps(result, indent=2)+"\n", newline="\n")
    print(json.dumps({k: v for k, v in result.items() if k != "payloads"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write", action="store_true")
    main(write=not parser.parse_args().no_write)
