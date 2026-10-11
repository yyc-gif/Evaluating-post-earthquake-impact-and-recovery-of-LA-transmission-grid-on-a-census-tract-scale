"""Verify newly delivered Git LFS payloads from actual remote bytes."""
from common import OUT, git, sha, dump, log
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import hashlib, requests, time, datetime

REPO = "yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale"
PREFIX = "docs/data_research/built_environment_20261009/candidate_admission_rebuild_20261010/"

def main():
    commit = git("rev-parse", "HEAD").decode().strip()
    branch = git("branch", "--show-current").decode().strip()
    remote = git("ls-remote", "origin", "refs/heads/" + branch).decode().split()[0]
    if remote != commit:
        raise RuntimeError("Remote HEAD differs from local HEAD")
    paths = git("ls-tree", "-r", "--name-only", commit, "--", PREFIX).decode().splitlines()
    expected = []
    for path in paths:
        if not path.endswith((".csv", ".tif")):
            continue
        blob = git("show", commit + ":" + path)
        if not blob.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
            raise RuntimeError("Expected LFS pointer: " + path)
        lines = blob.decode().splitlines()
        oid = next(x[11:] for x in lines if x.startswith("oid sha256:"))
        size = int(next(x[5:] for x in lines if x.startswith("size ")))
        local = OUT / path[len(PREFIX):]
        if local.stat().st_size != size or sha(local) != oid:
            raise RuntimeError("Local LFS payload mismatch: " + path)
        expected.append({"path": path, "oid": oid, "expected_size": size})

    def verify(item):
        url = "https://media.githubusercontent.com/media/" + REPO + "/" + commit + "/" + quote(item["path"], safe="/")
        errors = []
        for attempt in range(3):
            try:
                h, size, prefix = hashlib.sha256(), 0, b""
                with requests.get(url, stream=True, timeout=(15, 90)) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(1024 * 1024):
                        if not chunk:
                            continue
                        if not prefix:
                            prefix = chunk[:150]
                        h.update(chunk)
                        size += len(chunk)
                        if size > item["expected_size"]:
                            raise ValueError("Remote payload exceeds expected size")
                actual = h.hexdigest()
                is_pointer = prefix.startswith(b"version https://git-lfs.github.com/spec/v1")
                if size != item["expected_size"] or actual != item["oid"] or is_pointer:
                    raise ValueError("Remote byte hash/size/pointer mismatch")
                return {**item, "url": url, "actual_sha256": actual, "actual_size": size, "is_pointer": is_pointer, "pass": True, "attempt_errors": errors}
            except Exception as exc:
                errors.append(repr(exc))
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
        return {**item, "url": url, "pass": False, "errors": errors}

    rows = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(verify, item) for item in expected]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(f"{len(rows)}/{len(expected)} {'PASS' if row['pass'] else 'FAIL'} {row['path'].split('/')[-1]}", flush=True)
    all_pass = bool(rows) and all(row["pass"] for row in rows)
    report = {"verified_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "payload_commit": commit, "remote_head_at_verification": remote, "branch": branch, "lfs_files": len(rows), "verified_bytes": sum(x.get("actual_size", 0) for x in rows), "all_pass": all_pass, "files": sorted(rows, key=lambda x: x["path"])}
    dump("REMOTE_LFS_BYTE_VERIFICATION.json", report)
    log(f"Remote LFS actual-byte verification: {len(rows)} files, {report['verified_bytes']} bytes, all_pass={all_pass}; payload commit {commit}.")
    if not all_pass:
        raise RuntimeError("Remote verification incomplete")

if __name__ == "__main__":
    main()
