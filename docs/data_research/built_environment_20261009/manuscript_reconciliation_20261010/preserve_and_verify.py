"""Hash protected science, untouched source manuscripts, and the original index."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def git(root, *args):
    return subprocess.check_output(["git", "-c", "filter.lfs.process=", "-c", "filter.lfs.smudge=", "-c", "filter.lfs.required=false", "-C", str(root), *args])


def snapshot(repo, package):
    inherited = json.loads((repo / "docs/data_research/built_environment_20261009/PRESERVATION_BASELINE.json").read_text())
    model = json.loads((repo / "results/diagnostics/ga_optimization_20261009/ORIGINAL_PROTECTED_HASHES.json").read_text())
    paths = sorted(set(inherited["protected_files"]) | set(model["files_sha256"]))
    sources = json.loads((package / "MANUSCRIPT_SOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    return {"original_HEAD": git(repo, "rev-parse", "HEAD").decode().strip(), "original_branch": git(repo, "branch", "--show-current").decode().strip(),
            "index_entries_sha256": hashlib.sha256(git(repo, "ls-files", "--stage", "-z")).hexdigest(),
            "staged_diff_sha256": hashlib.sha256(git(repo, "diff", "--cached", "--binary", "--no-ext-diff")).hexdigest(),
            "staged_item_count": len(git(repo, "diff", "--cached", "--name-only", "-z").rstrip(b"\0").split(b"\0")),
            "protected_science_sha256": {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths},
            "source_manuscripts_sha256": {r["path"]: hashlib.sha256(Path(r["path"]).read_bytes()).hexdigest() for r in sources if not r["path"].startswith("git:")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    current = snapshot(a.repo, a.package)
    dest = a.package / "PRESERVATION_BEFORE.json"
    if a.verify:
        assert current == json.loads(dest.read_text()), "Protected input or original staging changed; do not overwrite."
        dest = a.package / "PRESERVATION_AFTER.json"
        current = {"status": "PASS", "protected_files": len(current["protected_science_sha256"]), **current}
    elif dest.exists():
        assert current == json.loads(dest.read_text())
    dest.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    print("PRESERVATION", "PASS" if a.verify else "BASELINE", len(current["protected_science_sha256"]), "STAGED", current["staged_item_count"])


if __name__ == "__main__":
    main()
