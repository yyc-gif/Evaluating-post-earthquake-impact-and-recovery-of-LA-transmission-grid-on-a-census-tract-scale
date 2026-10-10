"""Snapshot/verify the untouched revision checkout and hydrate exact LFS inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_research_collect_20261009 import ROOT, long_path, save

INPUTS = (
    "Data/JULY_UTILITY_CONSTRAINED_92.csv",
    "Data/substation_graph_CEC_edges_expanded.csv",
    "Data/source_nodes_core_expanded.csv",
    "Data/stage45_depot_inputs_final_origin_proxy.csv",
    "Data/stage45_active_crew_bases_C57.csv",
    "data/travel/travel_task_to_task.csv",
    "data/travel/travel_base_to_task.csv",
    "Formal_Experiment_20260923/Stage 5 Output_expanded/INCUMBENT_DIRECT_SCORES_2pc50.csv",
)


def git(root, *args):
    return subprocess.check_output(["git", "-c", "filter.lfs.process=", "-c",
        "filter.lfs.smudge=", "-c", "filter.lfs.required=false", *args], cwd=root)


def sha(path):
    return hashlib.sha256(long_path(path).read_bytes()).hexdigest()


def snapshot(root):
    baseline = json.loads(long_path(root / "docs/data_research/built_environment_20261009/PRESERVATION_BASELINE.json").read_text())
    model = json.loads(long_path(root / "results/diagnostics/ga_optimization_20261009/ORIGINAL_PROTECTED_HASHES.json").read_text())
    paths = sorted(set(baseline["protected_files"]) | set(model["files_sha256"]))
    return dict(revision_head=git(root, "rev-parse", "HEAD").decode().strip(),
        revision_branch=git(root, "branch", "--show-current").decode().strip(),
        staged_diff_sha256=hashlib.sha256(git(root, "diff", "--cached", "--binary", "--no-ext-diff")).hexdigest(),
        files_sha256={p: sha(root / p) for p in paths})


def hydrate(names=INPUTS, receipt="LOCAL_MODEL_INPUT_HYDRATION.json"):
    common = Path(git(REPO_ROOT, "rev-parse", "--git-common-dir").decode().strip()).resolve()
    rows = []
    for name in names:
        path = REPO_ROOT / name
        pointer = long_path(path).read_bytes()
        if pointer.startswith(b"version https://git-lfs.github.com/spec/v1"):
            fields = dict(line.split(" ", 1) for line in pointer.decode().splitlines())
            oid = fields["oid"].removeprefix("sha256:")
            source = common / "lfs/objects" / oid[:2] / oid[2:4] / oid
            data = long_path(source).read_bytes()
            assert len(data) == int(fields["size"]) and hashlib.sha256(data).hexdigest() == oid
            long_path(path).write_bytes(data)
        rows.append(dict(path=name, sha256=sha(path)))
    save(ROOT / receipt, rows)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--revision-checkout", type=Path, required=True)
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    dest = ROOT / "CONTINUATION_PRESERVATION_BASELINE.json"
    current = snapshot(a.revision_checkout.resolve())
    if a.verify:
        expected = json.loads(long_path(dest).read_text())
        assert current == expected, "Untouched revision checkout has changed; do not overwrite it."
        save(ROOT / "CONTINUATION_PRESERVATION_VERIFIED.json", dict(status="PASS", **current))
        print("PRESERVATION_PASS", len(current["files_sha256"]), current["staged_diff_sha256"])
    else:
        if long_path(dest).exists():
            assert json.loads(long_path(dest).read_text()) == current
        else:
            save(dest, current)
        hydrate()
        print("PRESERVATION_BASELINE", len(current["files_sha256"]), "HYDRATED", len(INPUTS))


if __name__ == "__main__":
    main()
