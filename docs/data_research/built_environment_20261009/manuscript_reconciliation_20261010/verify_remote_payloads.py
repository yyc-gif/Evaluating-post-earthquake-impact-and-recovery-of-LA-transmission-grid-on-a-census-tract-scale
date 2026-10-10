"""Verify the pushed branch and download/hash actual LFS review/source payloads."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen


BASE = "docs/data_research/built_environment_20261009/"
PACKAGE = BASE + "manuscript_reconciliation_20261010/"
BRANCH = "analysis/stage7-manuscript-reconciliation-20261010"
REMOTE = "https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git"


def git(repo, *args, input=None):
    return subprocess.check_output(["git", "-C", str(repo), *args], input=input, timeout=180)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    a = ap.parse_args()
    repo = a.repo.resolve()
    files = repo if os.name != "nt" else Path("\\\\?\\" + str(repo))
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    remote_head = git(repo, "ls-remote", "origin", "refs/heads/" + BRANCH).decode().split()[0]
    assert head == remote_head
    assert git(repo, "branch", "--show-current").decode().strip() == BRANCH
    paths = git(repo, "ls-files", "-z", "--", PACKAGE).decode().strip("\0").split("\0")
    preview = BASE + "manuscript_integration_preview_20261010/"
    paths += [preview + name for name in ["STAGE7_CANDIDATE_LABELS_2291.csv", "CLASSIFIED_FEATURE_VALUES_2287.csv",
              "STAGE7_CLUSTER_PROFILES.csv", "STAGE7_CLUSTER_PROFILES_LONG.csv", "FIG_STAGE7_TYPOLOGY_MAP.pdf",
              "FIG_STAGE7_CLUSTER_PROFILE.pdf", "FIG_STAGE7_SPATIAL_ROBUSTNESS.pdf"]]
    objects = {}
    normal = []
    for path in paths:
        blob = git(repo, "show", "HEAD:" + path)
        local = (files / path).read_bytes()
        if blob.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
            fields = dict(line.split(" ", 1) for line in blob.decode().strip().splitlines())
            oid = fields["oid"].split(":", 1)[1]
            size = int(fields["size"])
            assert hashlib.sha256(local).hexdigest() == oid and len(local) == size
            objects.setdefault(oid, {"oid": oid, "size": size, "paths": []})["paths"].append(path)
        else:
            # Git may normalize text line endings; binary DOCX is checked exactly.
            assert blob == local or blob == local.replace(b"\r\n", b"\n"), path
            normal.append({"path": path, "git_blob_sha1": hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest(),
                           "local_sha256": hashlib.sha256(local).hexdigest(), "bytes": len(local)})
    credentials = git(repo, "credential", "fill", input=b"protocol=https\nhost=github.com\n\n").decode()
    credentials = dict(line.split("=", 1) for line in credentials.splitlines() if "=" in line)
    auth = base64.b64encode((credentials["username"] + ":" + credentials["password"]).encode()).decode()
    body = {"operation": "download", "transfers": ["basic"],
            "objects": [{"oid": v["oid"], "size": v["size"]} for v in objects.values()]}
    request = Request(REMOTE + "/info/lfs/objects/batch", data=json.dumps(body).encode(),
                      headers={"Accept": "application/vnd.git-lfs+json", "Content-Type": "application/vnd.git-lfs+json",
                               "Authorization": "Basic " + auth}, method="POST")
    with urlopen(request, timeout=90) as response:
        result = json.load(response)
    verified = []
    for obj in result["objects"]:
        assert "error" not in obj, obj.get("error")
        action = obj["actions"]["download"]
        digest = hashlib.sha256()
        size = 0
        request = Request(action["href"], headers=action.get("header", {}))
        with urlopen(request, timeout=120) as response:
            while chunk := response.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
        expected = objects[obj["oid"]]
        assert digest.hexdigest() == expected["oid"] and size == expected["size"]
        verified.append({**expected, "actual_download_sha256": digest.hexdigest(), "actual_download_bytes": size, "status": "PASS"})
    assert len(verified) == len(objects)
    protected = git(repo, "ls-remote", "origin", "refs/heads/revision/reviewer-driven-core-rebuild-v2").decode().split()[0]
    assert protected == "031d2c675f8e7d58035d27448be040b809ced086"
    record = {"status": "PASS", "date": "2026-10-10", "remote": REMOTE, "branch": BRANCH,
              "verified_delivery_commit": head, "remote_HEAD_at_verification": remote_head,
              "protected_revision_remote_HEAD": protected, "actual_LFS_downloads": verified,
              "normal_git_blobs_at_verified_commit": normal, "credentials_recorded": False,
              "scope": "All delivery LFS payloads plus seven frozen figure/label/profile sources. Real bytes downloaded and hashed, not pointer existence or local-cache-only checks.",
              "followup_commit_scope": "The later verification-record commit adds this JSON only; final remote HEAD is checked again after that push."}
    (files / PACKAGE / "REMOTE_VERIFICATION.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("REMOTE PASS", head, "LFS_DOWNLOADS", len(verified), "BYTES", sum(v["size"] for v in verified))


if __name__ == "__main__":
    main()
