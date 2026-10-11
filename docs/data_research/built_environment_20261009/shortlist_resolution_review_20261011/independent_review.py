"""Freeze matching local runs and independently check them without fitting models."""
import argparse
import datetime
import hashlib
import itertools
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
BASE = "94faefd30273dec8318197de443f2f992fa29e5c"
ORIGINAL = Path(r"C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision")
PREFIX = "docs/data_research/built_environment_20261009/"
UNRESOLVED = {"06037189703", "06037301601", "06037301602", "06037404600"}
FIXED = ["B_480_hr", "Init_Supply", "Grid_Degree", "Grid_Impact", "Grid_Betweenness", "Redundancy_HHI", "SOVI_SCORE", "log1p_BUILDVALUE", "ALR_NPCTL"]


def lp(path):
    return Path("\\\\?\\" + str(Path(str(path).removeprefix("\\\\?\\")).resolve()))


def sha(path):
    h = hashlib.sha256()
    with lp(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(["git", *args], cwd=str(cwd))


def write_json(name, value):
    lp(OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def read(name):
    return pd.read_csv(lp(OUT / name), dtype={"tract_id": str})


def source(name):
    rel = PREFIX + name
    blob = git("show", BASE + ":" + rel)
    digest = blob.decode().split("oid sha256:")[1].splitlines()[0].strip() if blob.startswith(b"version https://git-lfs") else hashlib.sha256(blob).hexdigest()
    for root in [ROOT, ROOT.parent / "_ca10", ORIGINAL, ROOT.parent / "_cw10"]:
        p = lp(root / rel)
        if p.exists() and sha(p) == digest:
            return p
    raise FileNotFoundError("Missing verified payload: " + rel)


def snapshot():
    prior = json.loads(source("candidate_admission_rebuild_20261010/PENDING_COMPLETION_PROTECTION_AFTER.json").read_text(encoding="utf-8"))
    files = {p: sha(ORIGINAL / p) if lp(ORIGINAL / p).exists() else None for p in prior["protected_files"]}
    return {
        "original_head": git("rev-parse", "HEAD", cwd=ORIGINAL).decode().strip(),
        "original_branch": git("branch", "--show-current", cwd=ORIGINAL).decode().strip(),
        "logical_index_sha256": hashlib.sha256(git("ls-files", "--stage", "-z", cwd=ORIGINAL)).hexdigest(),
        "status_sha256": hashlib.sha256(git("status", "--porcelain=v1", "-z", cwd=ORIGINAL)).hexdigest(),
        "staged_count": len([p for p in git("diff", "--cached", "--name-only", "-z", cwd=ORIGINAL).split(b"\0") if p]),
        "protected_count": len(files), "protected_files": files,
    }


def freeze(src):
    assert git("rev-parse", "HEAD").decode().strip() == BASE
    before = snapshot()
    assert before["protected_count"] == 950 and before["staged_count"] == 862
    write_json("REVIEW_PRESERVATION_BEFORE.json", before)
    src = lp(src)
    assert src.is_dir() and (src / "COMPARISON_COMPLETION_QA.json").is_file()
    rows = []
    reserved = {"README.md", "FINAL_VARIABLE_RECOMMENDATION.md", "FINAL_CANDIDATE_CONSTRUCT_DECISION.md", "DOMAIN_WEIGHT_REQUIREMENTS.md"}
    for p in sorted(src.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts or ".pytest_cache" in p.parts or p.suffix == ".pyc":
            continue
        rel = p.relative_to(src)
        dest_rel = Path("reused_narratives") / rel if str(rel) in reserved else rel
        target = lp(OUT / dest_rel)
        if target.exists():
            raise FileExistsError(target)
        digest = sha(p)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
        assert sha(p) == sha(target) == digest, "Source changed during evidence freeze"
        rows.append({"source_relative_path": rel.as_posix(), "snapshot_relative_path": dest_rel.as_posix(), "sha256": digest, "bytes": target.stat().st_size})
    pd.DataFrame(rows).to_csv(lp(OUT / "REUSED_RUN_BYTE_MANIFEST.csv"), index=False)
    write_json("REUSE_PROVENANCE.json", {
        "source_worktree": str(src), "source_HEAD": BASE,
        "source_status_at_freeze": git("status", "--porcelain=v1", cwd=Path(str(src).removeprefix("\\\\?\\")).parents[3]).decode(),
        "freeze_UTC": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "files": len(rows), "bytes": sum(r["bytes"] for r in rows),
        "source_was_uncommitted_matching_run_package": True,
        "not_a_claim_of_new_preregistration_or_new_fits": True,
        "new_KMeans_fits_in_review": 0,
    })
    print("Frozen", len(rows), "files; original 950 files/862 staged items inventoried.", flush=True)


def matching(labels, pred, train):
    table = np.zeros((4, 4), dtype=int)
    np.add.at(table, (labels[train], pred[train]), 1)
    a, b = linear_sum_assignment(-table)
    mapping = np.empty(4, dtype=int)
    mapping[b] = a
    return mapping[pred]


def review():
    matrix = read("SHORTLIST_FEATURE_MATRIX.csv").set_index("tract_id")
    admitted = pd.read_csv(source("candidate_admission_rebuild_20261010/CANDIDATE_VALUES_RESIDENTIAL_2291.csv"), dtype={"tract_id": str}).set_index("tract_id")
    historical = pd.read_csv(source("final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv"), dtype={"tract_id": str}).set_index("tract_id")
    assert len(matrix) == 2291 and matrix.index.is_unique and set(matrix.index) == set(admitted.index)
    assert set(matrix.index[~matrix.primary2287]) == UNRESOLVED
    assert matrix.common2286.sum() == 2286 and matrix.primary2287.sum() == 2287
    assert admitted.assessor2022_gross_floor_area_ratio.isna().all()
    fixed_old = historical.loc[historical.primary_complete_case, [x if x != "log1p_BUILDVALUE" else "log1p_NRI_BUILDVALUE" for x in FIXED]].copy()
    fixed_old.columns = FIXED
    np.testing.assert_allclose(matrix.loc[fixed_old.index, FIXED], fixed_old, rtol=0, atol=1e-10)
    for col in matrix.columns.intersection(admitted.columns):
        if pd.api.types.is_numeric_dtype(matrix[col]) and pd.api.types.is_numeric_dtype(admitted[col]):
            np.testing.assert_allclose(matrix[col], admitted.loc[matrix.index, col], equal_nan=True, rtol=1e-12, atol=1e-9)
    spec = json.loads(lp(OUT / "CONTROLLED_SHORTLIST_SPECIFICATION.json").read_text(encoding="utf-8"))
    assert spec["KMeans"] == {"n_clusters": 4, "n_init": 100, "max_iter": 500, "tol": 0.0001, "algorithm": "lloyd"}
    assert spec["seeds"] == list(range(42, 62)) and spec["spatial_unique_deletion_sets"] == 17
    runs = read("BOUNDED_RUN_RECORDS.csv").set_index(["model", "seed"])
    pair_tables = read("BETWEEN_MODEL_CONTINGENCIES.csv")
    results, summaries, arrays = [], [], {}
    for path in sorted(lp(OUT / "run_records").glob("*.npz")):
        name = path.stem
        if name == "CORE3_coverage":
            continue
        z = np.load(path, allow_pickle=False)
        arrays[name] = z
        meta = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
        assert meta["completed_seeds"] == list(range(42, 62))
        ids = z["tract_ids"]
        d = matrix.loc[ids]
        cols = z["feature_columns"].tolist()
        factors = z["coordinate_factors"]
        sc = StandardScaler().fit(d[cols])
        np.testing.assert_allclose(sc.mean_, z["scaler_mean"], rtol=1e-12, atol=1e-10)
        np.testing.assert_allclose(sc.scale_, z["scaler_scale"], rtol=1e-12, atol=1e-10)
        x = sc.transform(d[cols]) * factors
        assert hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest() == meta["signature"]["matrix_sha256"]
        assert np.isclose((factors**2).sum(), 1)
        physical = [c for c in cols if c not in FIXED]
        for group in [FIXED[:2], FIXED[2:6], physical, ["SOVI_SCORE"], FIXED[-2:]]:
            assert np.isclose(sum(factors[cols.index(c)]**2 for c in group), .2)
        fullseedari = [adjusted_rand_score(z[f"s{a}_labels"], z[f"s{b}_labels"]) for a, b in itertools.combinations(range(42, 62), 2)]
        spatialari, changes = [], []
        for seed in range(42, 62):
            r = runs.loc[(name, seed)]
            labels, centers = z[f"s{seed}_labels"], z[f"s{seed}_centers"]
            if name != "HIST":
                assert np.array_equal(np.square(x[:, None] - centers[None]).sum(axis=2).argmin(axis=1), labels)
                inertia = np.square(x - centers[labels]).sum()
                np.testing.assert_allclose(inertia, r.full_inertia, rtol=1e-10)
            else:
                old = np.load(source("final_feature_validation_20261010/run_records/D__equal_five_domains.npz"))
                assert np.array_equal(labels, old[f"s{seed}_k4"])
            train = z[f"s{seed}_train_mask"]
            sp_sc = StandardScaler().fit(d.loc[train, cols])
            np.testing.assert_allclose(sp_sc.mean_, z[f"s{seed}_spatial_mean"], rtol=1e-12, atol=1e-10)
            np.testing.assert_allclose(sp_sc.scale_, z[f"s{seed}_spatial_scale"], rtol=1e-12, atol=1e-10)
            xx = sp_sc.transform(d[cols]) * factors
            sp_cent = z[f"s{seed}_spatial_centers"]
            pred = np.square(xx[:, None] - sp_cent[None]).sum(axis=2).argmin(axis=1)
            assert np.array_equal(pred, z[f"s{seed}_spatial_prediction"])
            if name == "HIST":
                old_sp = np.load(source(f"spatial_k4_validation_20261010/run_records/D_s{seed}.npz"))
                assert np.array_equal(pred, old_sp["raw_prediction"])
            else:
                np.testing.assert_allclose(np.square(xx[train] - sp_cent[pred[train]]).sum(), r.spatial_inertia, rtol=1e-10)
            for scope, mask, key in [("full", np.ones(len(d), dtype=bool), "full_ARI"), ("training", train, "training_ARI"), ("heldout", ~train, "heldout_ARI")]:
                np.testing.assert_allclose(adjusted_rand_score(labels[mask], pred[mask]), r[key], atol=1e-12)
            changed = int((labels != matching(labels, pred, train)).sum())
            assert changed == r.aligned_reassigned_n
            spatialari.append(adjusted_rand_score(labels, pred))
            changes.append(changed)
            results.append({"model": name, "seed": seed, "n": len(d), "full_labels_verified": True, "spatial_prediction_verified": True, "train_scaler_verified": True, "ARI_verified": True, "reassigned_n": changed, "HIST_centers_are_partition_means_not_original_estimator": name == "HIST"})
        summaries.append({"model": name, "n": len(d), "seed_pair_ARI_median": float(np.median(fullseedari)), "spatial_ARI_median": float(np.median(spatialari)), "spatial_ARI_p05": float(np.quantile(spatialari, .05)), "spatial_ARI_min": float(min(spatialari)), "max_reassigned": max(changes), "new_fit_count": 0})
        print("Independent weighted prediction and inertia checks:", name, flush=True)
    for (a, b, seed), group in pair_tables.groupby(["model_a", "model_b", "seed"]):
        za, zb = arrays[a], arrays[b]
        common = pd.Index(za["tract_ids"]).intersection(zb["tract_ids"], sort=False)
        la = pd.Series(za[f"s{seed}_labels"], index=za["tract_ids"]).loc[common].to_numpy()
        lb = pd.Series(zb[f"s{seed}_labels"], index=zb["tract_ids"]).loc[common].to_numpy()
        tab = np.zeros((4, 4), dtype=int)
        np.add.at(tab, (la, lb), 1)
        observed = group.pivot(index="class_a", columns="class_b_raw", values="n").reindex(index=range(4), columns=range(4)).to_numpy()
        assert np.array_equal(tab, observed)
    coverage = np.load(lp(OUT / "run_records/CORE3_coverage.npz"))
    coverage_meta = json.loads(lp(OUT / "run_records/CORE3_coverage.json").read_text(encoding="utf-8"))
    cover_d = matrix.loc[coverage["tract_ids"]]
    cover_cols = coverage["feature_columns"].tolist()
    cover_train = coverage["train_mask"]
    cover_sc = StandardScaler().fit(cover_d.loc[cover_train, cover_cols])
    cover_x = cover_sc.transform(cover_d[cover_cols]) * coverage["coordinate_factors"]
    assert int(cover_train.sum()) == 1715
    for row in coverage_meta["rows"]:
        seed = row["seed"]
        pred = np.square(cover_x[:, None] - coverage[f"s{seed}_centers"][None]).sum(axis=2).argmin(axis=1)
        assert np.array_equal(pred, coverage[f"s{seed}_prediction"])
        np.testing.assert_allclose(cover_sc.mean_, coverage[f"s{seed}_mean"])
        np.testing.assert_allclose(cover_sc.scale_, coverage[f"s{seed}_scale"])
        np.testing.assert_allclose(adjusted_rand_score(arrays["CORE3"][f"s{seed}_labels"], pred), row["full_ARI"], atol=1e-12)
    # Independently derive covariance-aware shares from original 80 count replicates.
    with zipfile.ZipFile(source("validation/sources/B25024_06.csv.zip")) as archive:
        vre = pd.read_csv(archive.open(archive.namelist()[0]), dtype={"GEOID": str})
    vre = vre.loc[vre.GEOID.str.startswith("1400000US06037", na=False)].copy()
    vre["tract_id"] = vre.GEOID.str[-11:]
    ids = arrays["CORE3"]["tract_ids"]
    d_acs = admitted.loc[ids]
    rep_cols = [f"Var_Rep{i}" for i in range(1, 81)]
    vre_rows = {k: vre.loc[vre.ORDER.eq(k)].set_index("tract_id").loc[ids] for k in [1, 2, 6, 7, 8, 9]}
    rep_den = vre_rows[1][rep_cols].to_numpy(float)
    assert (rep_den > 0).all()
    saved_reps = np.load(lp(OUT / "ACS_CONFIGURATION_REPLICATES.npz"))
    assert np.array_equal(saved_reps["tract_ids"], ids)
    for feature, orders in [("housing_5plus_share", [6, 7, 8, 9]), ("housing_detached_share", [2])]:
        replicate = sum(vre_rows[k][rep_cols].to_numpy(float) for k in orders) / rep_den
        np.testing.assert_allclose(replicate, saved_reps[feature], rtol=0, atol=1e-12)
        point = d_acs[feature].to_numpy()
        se = np.sqrt(4 / 80 * np.square(replicate - point[:, None]).sum(axis=1))
        boundary = d_acs[feature + "_boundary_model"].to_numpy(bool)
        den = d_acs.housing_total.to_numpy()
        pstar = np.minimum(.5, 2.3 * 16 / den)
        se[boundary] = np.sqrt(pstar[boundary] * (1 - pstar[boundary]) * 16 / den[boundary])
        np.testing.assert_allclose(1.645 * se, d_acs[feature + "_moe90"], rtol=1e-7, atol=1e-10)
    core = arrays["CORE3"]
    core_cols = core["feature_columns"].tolist()
    core_d = matrix.loc[ids]
    core_x = (core_d[core_cols].to_numpy() - core["scaler_mean"]) / core["scaler_scale"] * core["coordinate_factors"]
    boundary = d_acs.housing_5plus_share_boundary_model.to_numpy(bool)
    ci = core_cols.index("housing_5plus_share")
    stress = []
    for direction in [-1, 1]:
        values = d_acs.housing_5plus_share.to_numpy().copy()
        values[boundary] = np.clip(values[boundary] + direction * d_acs.housing_5plus_share_moe90.to_numpy()[boundary], 0, 1)
        xx = core_x.copy()
        xx[:, ci] = (values - core["scaler_mean"][ci]) / core["scaler_scale"][ci] * core["coordinate_factors"][ci]
        pred = np.square(xx[:, None] - core["s42_centers"][None]).sum(axis=2).argmin(axis=1)
        stress.append({"direction": "all_boundary_MOE_lower" if direction == -1 else "all_boundary_MOE_upper", "boundary_n": int(boundary.sum()), "n": len(ids), "coordinates_changed_n": int((values != d_acs.housing_5plus_share.to_numpy()).sum()), "labels_changed_n": int((pred != core["s42_labels"]).sum()), "ARI": adjusted_rand_score(core["s42_labels"], pred), "refit": False, "interpretation": "Nonprobabilistic simultaneous endpoint stress; not a confidence interval or worst-case optimization"})
    pd.DataFrame(stress).to_csv(lp(OUT / "ACS_BOUNDARY_FIXED_CENTROID_STRESS.csv"), index=False)
    pairs = read("SAME_CONSTRUCT_SOURCE_SUBSTITUTIONS.csv")
    d = matrix.loc[matrix.common2286]
    paired = []
    for r in pairs.itertuples():
        a, b = d[r.source_a], d[r.source_b]
        delta = b - a
        values = {"pearson": pearsonr(a, b).statistic, "spearman": spearmanr(a, b).statistic, "mean_difference": delta.mean(), "mean_absolute_difference": delta.abs().mean(), "p90_absolute_difference": delta.abs().quantile(.9)}
        for key, value in values.items():
            np.testing.assert_allclose(value, getattr(r, key), atol=1e-12)
        paired.append({"source_a": r.source_a, "source_b": r.source_b, "n": len(d), **values, "verified_from_frozen_measurements": True})
    stock = pearsonr(d.log1p_BUILDVALUE, d.ALR_NPCTL).statistic
    pd.DataFrame(results).to_csv(lp(OUT / "INDEPENDENT_FIT_CHECKS.csv"), index=False)
    pd.DataFrame(summaries).to_csv(lp(OUT / "INDEPENDENT_COMPARISON_CHECKS.csv"), index=False)
    pd.DataFrame(paired).to_csv(lp(OUT / "INDEPENDENT_SOURCE_DIFFERENCES.csv"), index=False)
    # Omitted land is unknown: bounds are not observed errors or full-tract entropy.
    bounds = read("SCAG_CLASSIFIED_LAND_SUPPORT_BOUNDS.csv")
    support = []
    for vintage, g in bounds.groupby("vintage"):
        support.append({"vintage": int(vintage), "n": int(g.bound_width.notna().sum()), "median_classified_land_fraction": float(g.classified_land_fraction.median()), "p10_classified_land_fraction": float(g.classified_land_fraction.quantile(.1)), "median_unknown_land_entropy_bound_width": float(g.bound_width.median()), "p90_unknown_land_entropy_bound_width": float(g.bound_width.quantile(.9))})
    pd.DataFrame(support).to_csv(lp(OUT / "INDEPENDENT_SUPPORT_REVIEW.csv"), index=False)
    profiles = read("CLUSTER_PROFILE_VALUES.csv")
    pattern = []
    for model, g in profiles.groupby("model"):
        p = g.pivot(index="display_class", columns="feature", values="mean")
        loss_id, social_id = p.B_480_hr.idxmax(), p.SOVI_SCORE.idxmax()
        pattern.append({"model": model, "highest_loss_group": int(loss_id), "highest_SOVI_group": int(social_id), "same_group": bool(loss_id == social_id), "SOVI_at_highest_loss": p.loc[loss_id, "SOVI_SCORE"], "maximum_group_SOVI": p.SOVI_SCORE.max(), "highest_loss_group_B_hr": p.loc[loss_id, "B_480_hr"], "highest_SOVI_group_B_hr": p.loc[social_id, "B_480_hr"], "interpretation": "Within-model ordinal profile comparison; no class-ID transfer or causality"})
    pd.DataFrame(pattern).to_csv(lp(OUT / "CROSS_SPECIFICATION_PATTERN_AUDIT.csv"), index=False)
    before = json.loads(lp(OUT / "REVIEW_PRESERVATION_BEFORE.json").read_text(encoding="utf-8"))
    after = snapshot()
    assert after == before, "Original protected tree changed; report before publication"
    write_json("REVIEW_PRESERVATION_AFTER.json", after)
    write_json("INDEPENDENT_REVIEW_QA.json", {
        "UTC": datetime.datetime.now(datetime.timezone.utc).isoformat(), "status": "PASS",
        "reference_commit": BASE, "models": len(arrays), "paired_fit_cases": len(results),
        "between_model_tables_verified": len(pair_tables.groupby(["model_a", "model_b", "seed"])),
        "master_n": len(matrix), "primary_n": 2287, "age_common_n": 2286,
        "fixed_nonphysical_coordinates_verified": FIXED, "stock_ALR_Pearson": float(stock),
        "HIST_40_fits_reused_and_verified": True,
        "coverage_predictions_verified": 20, "raw_ACS_count_replicates_verified": 80,
        "boundary_MOEs_independently_verified": True, "boundary_endpoint_stress_cases": 2,
        "new_KMeans_fits": 0, "new_spatial_extractions": 0, "new_physical_samples": 0,
        "protected_files_unchanged": 950, "original_staged_items_unchanged": 862,
        "formal_labels_changed": False, "weights_selected_by_fit_metrics": False,
    })
    print("Independent review PASS; no fits, GIS overlays or formal changes.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["freeze", "review", "preservation"])
    parser.add_argument("--source-dir", type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.source_dir)
    elif args.mode == "review":
        review()
    else:
        after = snapshot()
        assert after == json.loads(lp(OUT / "REVIEW_PRESERVATION_BEFORE.json").read_text(encoding="utf-8"))
        write_json("REVIEW_PRESERVATION_FINAL.json", after)
        print("Original protected tree and index unchanged.")
