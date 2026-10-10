"""Retrieve existing Actions evidence without launching or rerunning calculations."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

from la_grid.paths import REPO_ROOT

REPO = "yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale"
BRANCH = "diagnostics/ga-algorithm-interaction-and-alternatives-20261009"
REQUIRED = (38023902724, 38023988574, 38024145330, 38024876916,
            38024927358, 38025468939, 38025309567, 38025630104,
            38025701964, 38025814612, 38025896534)
ROOT = REPO_ROOT / "results/diagnostics/ga_deeper_research_20261009"


def long_path(path):
    import os
    return Path("\\\\?\\" + str(path.resolve())) if os.name == "nt" else path


def session(authenticate=False):
    s = requests.Session()
    s.headers.update({"Accept": "application/vnd.github+json",
                      "X-GitHub-Api-Version": "2022-11-28"})
    if authenticate:
        # GCM's Windows child Git rejects this worktree's long GIT_DIR.
        # Host-scoped credentials work from the shorter non-repository parent.
        credential = subprocess.run(["git", "credential", "fill"],
            cwd=REPO_ROOT.parent, input="protocol=https\nhost=github.com\n\n",
            text=True, capture_output=True, check=True)
        fields = dict(line.split("=", 1) for line in credential.stdout.splitlines() if "=" in line)
        s.headers["Authorization"] = "Bearer " + fields["password"]
    return s


def get(s, suffix, **params):
    r = s.get(f"https://api.github.com/repos/{REPO}/{suffix}", params=params, timeout=90)
    r.raise_for_status()
    return r.json()


def pages(s, suffix, key, **params):
    out = []
    page = 1
    while True:
        data = get(s, suffix, per_page=100, page=page, **params)[key]
        out.extend(data)
        if len(data) < 100:
            return out
        page += 1


def save(path, data):
    long_path(path).parent.mkdir(parents=True, exist_ok=True)
    long_path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--inventory-only", action="store_true")
    p.add_argument("--local-only", action="store_true", help="Verify and extract already downloaded ZIPs.")
    p.add_argument("--refresh-run", type=int, help="Refresh one outstanding run, retaining the rest of the inventory.")
    p.add_argument("--url-map", type=Path,
                   help="Temporary download URLs supplied by the GitHub connector.")
    a = p.parse_args()
    urls = json.loads(a.url_map.read_text()) if a.url_map else {}
    ROOT.mkdir(parents=True, exist_ok=True)
    s = session(authenticate=not a.local_only and not urls)
    saved = ROOT / "ACTIONS_RECONCILIATION_MANIFEST.json"
    if urls or a.local_only or a.refresh_run:
        previous = json.loads(long_path(saved).read_text())
        selected = {r["id"]: r for r in previous["runs"]}
        if a.refresh_run:
            selected[a.refresh_run] = get(s, f"actions/runs/{a.refresh_run}")
    else:
        all_runs = pages(s, "actions/runs", "workflow_runs", branch=BRANCH)
        selected = {r["id"]: r for r in all_runs
                    if r["id"] >= min(REQUIRED) and r["path"].startswith(".github/workflows/ga-")}
    for run_id in REQUIRED:
        if run_id not in selected:
            selected[run_id] = get(s, f"actions/runs/{run_id}")
    manifest = dict(retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                    metadata_asof_utc=(previous.get("metadata_asof_utc", previous["retrieved_at_utc"])
                        if urls or a.local_only else datetime.now(timezone.utc).isoformat()),
                    repository=REPO, branch=BRANCH, runs=[], artifacts=[])
    for run_id, run in sorted(selected.items()):
        cached_metadata = urls or a.local_only or (a.refresh_run and run_id != a.refresh_run)
        jobs = run["jobs"] if cached_metadata else pages(s, f"actions/runs/{run_id}/jobs", "jobs", filter="all")
        artifacts = run["artifacts"] if cached_metadata else pages(s, f"actions/runs/{run_id}/artifacts", "artifacts")
        entry = {k: run[k] for k in ("id", "name", "path", "head_sha", "head_branch",
                 "run_attempt", "status", "conclusion", "created_at", "updated_at", "html_url")}
        entry.update(jobs=jobs, artifacts=artifacts)
        manifest["runs"].append(entry)
        print("RUN", run_id, run["conclusion"], run["status"], run["name"],
              "jobs", len(jobs), "artifacts", len(artifacts), flush=True)
        for artifact in artifacts:
            record = dict(run_id=run_id, artifact_id=artifact["id"], name=artifact["name"],
                          expired=artifact["expired"], size_bytes=artifact["size_in_bytes"],
                          github_digest=artifact.get("digest"), source_commit=run["head_sha"])
            manifest["artifacts"].append(record)
            save(saved, manifest)
            if a.inventory_only or artifact["expired"]:
                continue
            archive = ROOT / "actions_raw" / str(run_id) / f"{artifact['id']}.zip"
            local_archive = long_path(archive)
            already_local = local_archive.exists()
            if a.local_only and not local_archive.exists():
                record["download_pending"] = True
                continue
            if not local_archive.exists():
                download = s.get(urls.get(str(artifact["id"]), artifact["archive_download_url"]), timeout=180)
                download.raise_for_status()
                local_archive.parent.mkdir(parents=True, exist_ok=True)
                local_archive.write_bytes(download.content)
            digest = hashlib.sha256(local_archive.read_bytes()).hexdigest()
            if artifact.get("digest"):
                assert artifact["digest"] == "sha256:" + digest, artifact["id"]
            record.update(local_archive=str(archive.relative_to(REPO_ROOT)), sha256=digest)
            extracted = archive.with_suffix("")
            members = []
            with zipfile.ZipFile(local_archive) as z:
                for member in z.infolist():
                    target = extracted / member.filename
                    assert target.resolve().is_relative_to(extracted.resolve()), member.filename
                    if member.is_dir():
                        continue
                    data = z.read(member)
                    dest = long_path(target)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    members.append(dict(path=member.filename, size=len(data),
                                        sha256=hashlib.sha256(data).hexdigest()))
            record["members"] = members
            if not already_local:
                print("ARTIFACT", artifact["id"], artifact["name"], digest, len(members), flush=True)
        save(ROOT / "ACTIONS_RECONCILIATION_MANIFEST.json", manifest)
    save(ROOT / "ACTIONS_RECONCILIATION_MANIFEST.json", manifest)
    print("COMPLETE", len(manifest["runs"]), len(manifest["artifacts"]), flush=True)


if __name__ == "__main__":
    main()
