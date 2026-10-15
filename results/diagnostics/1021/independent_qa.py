"""Recalculate validation outputs from archived labels without fitting models."""
import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import comb
from sklearn.metrics.cluster import contingency_matrix

from preflight import AUTH, BASE, HERE, ROOT, git, sha, snapshot


def file_digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify():
    out = HERE / "outputs"
    a = np.load(out / "ALL_FITTED_ARRAYS.npz", allow_pickle=False)
    source = np.load(AUTH / "preprocessing_and_labels.npz", allow_pickle=False)
    x = source["weighted_matrix"]
    current = snapshot()
    before = json.loads((HERE / "FROZEN_INPUT_REGISTRY.json").read_text())
    assert current == before, "Original worktree or scientific input changed"
    run = json.loads((out / "RUN_MANIFEST.json").read_text())
    assert run["status"] == "FULL_REGISTERED_ANALYSIS"
    assert run["protocol_sha256"] == sha(HERE / "PROTOCOL.md")
    for name, expected in run["output_sha256"].items():
        assert sha(out / name) == expected
    obs = pd.read_csv(out / "OBSERVED_INDICES.csv")
    for row in obs.itertuples():
        labels = a[f"full_k{row.k}_s{row.seed}_labels"]
        means = np.vstack([x[labels == j].mean(0) for j in range(row.k)])
        w = np.sum((x-means[labels])**2)
        np.testing.assert_allclose(w, row.inertia, atol=1e-9, rtol=1e-12)
    gaps = pd.read_csv(out / "GAP_REPLICATES.csv")
    summary = pd.read_csv(out / "GAP_SUMMARY.csv")
    gap_decisions = {}
    for name, block in gaps.groupby("reference"):
        pivot = block.pivot(index="replicate", columns="k", values="log_inertia")
        assert pivot.shape == (64, 8)
        observed = obs.groupby("k").inertia.min()
        gap = pivot.mean().to_numpy()-np.log(observed.to_numpy())
        spread = pivot.std(ddof=1).to_numpy()*np.sqrt(65/64)
        given = summary[summary.reference == name].sort_values("k")
        np.testing.assert_allclose(gap, given.gap, atol=1e-13)
        np.testing.assert_allclose(spread, given.s_1SE_rule, atol=1e-13)
        eligible = np.flatnonzero(gap[:-1] >= gap[1:]-spread[1:])
        gap_decisions[name] = int(eligible[0]+1) if len(eligible) else None
    ps = pd.read_csv(out / "PREDICTION_STRENGTH_REPETITIONS.csv")
    for row in ps.itertuples():
        prefix = f"ps_{row.design}_r{row.repeat}_k{row.k}_d{row.direction}"
        cm = contingency_matrix(a[prefix+"_actual"], a[prefix+"_predicted"])
        n = cm.sum(1)
        value = np.min(comb(cm, 2).sum(1)/comb(n, 2)) if np.all(n >= 2) else np.nan
        np.testing.assert_allclose(value, row.strength, atol=1e-14, equal_nan=True)
    boot = pd.read_csv(out / "BOOTSTRAP_CLUSTER_STABILITY.csv")
    references = {}
    for k, block in obs.groupby("k"):
        best = block.sort_values(["inertia", "seed"]).iloc[0]
        references[k] = a[f"full_k{k}_s{int(best.seed)}_labels"]
    for row in boot.itertuples():
        pred = a[f"bootstrap_r{row.repeat}_k{row.k}_full_predicted"]
        ix = (np.unique(a[f"bootstrap_r{row.repeat}_indices"])
              if row.support == "unique_inbag" else np.arange(len(x)))
        original_set = set(ix[references[row.k][ix] == row.cluster].tolist())
        matches = [set(ix[pred[ix] == j].tolist()) for j in np.unique(pred[ix])]
        best = max(len(original_set & other)/len(original_set | other) for other in matches)
        np.testing.assert_allclose(best, row.jaccard, atol=1e-14)
    # The complete baseline Git tree is unchanged outside this package.
    changed = git("diff", "--name-only", BASE).splitlines()
    assert all(p.startswith("results/diagnostics/1021/") for p in changed)
    protected_manifest_path = "docs/reproducibility/author_suite_final_layout_20261012/PRESERVATION_BEFORE.json"
    protected = json.loads(git("show", BASE+":"+protected_manifest_path))["protected_files"]
    protected_root = Path("C:/2025-2026 Fall/CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science/Project/LA_grid_reviewer_revision")
    failures = []
    for rel, expected in protected.items():
        path = protected_root / rel
        if not path.exists() or file_digest(path) != expected:
            failures.append(rel)
    assert len(protected) == 950 and failures == [], failures
    result = {"status": "PASS", "independent_observed_WCSS_checks": len(obs),
              "Gap_replicates": len(gaps), "Gap_1SE_decisions": gap_decisions,
              "prediction_strength_contingency_recalculations": len(ps),
              "bootstrap_set_Jaccard_recalculations": len(boot),
              "protected_scientific_files_unchanged": len(protected),
              "original_worktree_and_index_unchanged": True,
              "all_baseline_tracked_files_unchanged_outside_package": True,
              "output_hashes_verified": len(run["output_sha256"]),
              "no_formal_figures_manuscripts_or_results_modified": True}
    (HERE / "INDEPENDENT_QA.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    verify()
