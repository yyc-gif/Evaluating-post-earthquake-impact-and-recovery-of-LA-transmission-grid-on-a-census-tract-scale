"""Read-only input and source-worktree registry; never generate scientific data."""
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTH = ROOT / "results/stage7/2026-10-14"
BASE = "b307e6deafc054864787a3db63ad95218be91659"
SOURCE = ROOT.parent / "_final_p2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=cwd).decode().strip()


def snapshot():
    manifest = json.loads((AUTH / "ARTIFACT_HASHES.json").read_text())
    actual = {name: sha(AUTH / name) for name in manifest}
    assert actual == manifest, "Frozen input bytes differ or remain LFS pointers"
    a = np.load(AUTH / "preprocessing_and_labels.npz", allow_pickle=False)
    f = pd.read_csv(AUTH / "tract_features.csv", dtype={"tract_id": str})
    assert len(f) == 2299 and f.tract_id.is_unique
    assert f.tract_id.str.fullmatch(r"\d{11}").all()
    assert np.array_equal(f.tract_id, a["tract_ids"])
    assert f.Population.sum() == 9066522 and (f.Population > 0).all()
    assert f.additional_zero_housing_positive_population.sum() == 8
    assert np.isfinite(a["raw"]).all()
    rebuilt = ((a["raw"] - a["raw"].mean(0)) / a["raw"].std(0, ddof=0)
               * np.sqrt(a["budgets"]))
    np.testing.assert_allclose(rebuilt, a["weighted_matrix"], atol=1e-14, rtol=1e-14)
    np.testing.assert_allclose(a["budgets"], [1/9]*3 + [1/6]*4, atol=1e-16)
    assert list(a["feature_names"]) == ["Init_Supply", "Grid_Impact", "Redundancy_HHI",
                                       "B_Unconstrained", "MeanDelta", "SOVI_SCORE",
                                       "log1p_Population"]
    source_index = Path(git("rev-parse", "--git-path", "index", cwd=SOURCE))
    if not source_index.is_absolute():
        source_index = SOURCE / source_index
    return {
        "baseline_branch": "2026-10-14", "baseline_commit": BASE,
        "source_head": git("rev-parse", "HEAD", cwd=SOURCE),
        "source_status": git("status", "--porcelain=v1", "--untracked-files=all", cwd=SOURCE),
        "source_index_sha256": sha(source_index),
        "baseline_tree": git("rev-parse", BASE + "^{tree}"),
        "frozen_payload_sha256": actual,
        "source_frozen_payload_sha256": {n: sha(SOURCE / "results/stage7/2026-10-14" / n)
                                         for n in manifest},
        "eligible_tracts": len(f), "population": int(f.Population.sum()),
        "zero_housing_positive_population": 8,
        "GEOID_sequence_sha256": hashlib.sha256("\n".join(f.tract_id).encode()).hexdigest(),
        "weighted_matrix_float64_sha256": hashlib.sha256(a["weighted_matrix"].tobytes()).hexdigest(),
        "reconstruction_max_abs_error": float(np.max(abs(rebuilt-a["weighted_matrix"]))),
        "historical_K3_sizes": np.bincount(a["K3_labels"]).tolist(),
        "historical_K4_sizes": np.bincount(a["K4_sensitivity_labels"]).tolist(),
        "input_acquisition": "git lfs pull --include=results/stage7/2026-10-14/*",
    }


if __name__ == "__main__":
    result = snapshot()
    assert result["source_head"] == BASE
    # A user-side byte-identical packet rename appeared after the initial clean check.
    expected_status = ("D results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf\n"
                       "?? results/figure_review/PowerGridRestoration_Figures_20261014_YY_YL_MG.pdf")
    assert result["source_status"] in ("", expected_status)
    if result["source_status"]:
        renamed = SOURCE / "results/figure_review/PowerGridRestoration_Figures_20261014_YY_YL_MG.pdf"
        assert sha(renamed) == "ad31b9373a43ced979ad0bcb43ac03566f19e5b1ac3be42cae532901037a1616"
    (HERE / "FROZEN_INPUT_REGISTRY.json").write_text(json.dumps(result, indent=2) + "\n", newline="\n")
    print(json.dumps({k: v for k, v in result.items() if "payload" not in k}, indent=2))
