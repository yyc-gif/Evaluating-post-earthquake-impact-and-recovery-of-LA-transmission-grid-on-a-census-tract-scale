"""Registered clustering-only experiments. No publication or simulation writes."""
import os
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import hashlib
import json
import platform
import time
from itertools import combinations
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.cluster.hierarchy import linkage, cut_tree
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_samples)
from threadpoolctl import threadpool_limits

from preflight import AUTH, BASE, HERE, ROOT, git, sha


def rng(stage, repeat=0, k=0):
    return np.random.default_rng(np.random.SeedSequence([1021, stage, repeat, k]))


def fit(x, k, seed):
    return KMeans(n_clusters=k, init="k-means++", n_init=50, max_iter=500,
                  tol=1e-4, algorithm="lloyd", random_state=int(seed)).fit(x)


def new_seed(r):
    return int(r.integers(0, 2**31-1))


def pair_strength(actual, predicted):
    """Unordered-pair form of Tibshirani-Walther validation-cluster strength."""
    rows = []
    for c in np.unique(actual):
        part = predicted[actual == c]
        n = len(part)
        counts = np.unique(part, return_counts=True)[1]
        numerator = int(np.sum(counts * (counts-1) // 2))
        denominator = n * (n-1) // 2
        rows.append({"cluster": int(c), "n": n, "agreeing_pairs": numerator,
                     "all_pairs": denominator,
                     "strength": numerator/denominator if denominator else np.nan})
    values = [row["strength"] for row in rows]
    return (float(min(values)) if np.isfinite(values).all() else np.nan), rows


def best_jaccard(a, b):
    rows = []
    for c in np.unique(a):
        target = a == c
        best, best_d = -1., -1
        for d in np.unique(b):
            other = b == d
            score = np.sum(target & other) / np.sum(target | other)
            if score > best:
                best, best_d = float(score), int(d)
        rows.append({"cluster": int(c), "matched_cluster": best_d,
                     "jaccard": best, "n_reference": int(target.sum())})
    return rows


def rare_match(rare, labels):
    candidates = []
    for c in np.unique(labels):
        mask = labels == c
        overlap = int(np.sum(mask & rare))
        candidates.append((overlap / np.sum(mask | rare), int(c),
                           overlap, int(mask.sum())))
    j, c, overlap, size = max(candidates)
    return {"rare_jaccard": float(j), "rare_matched_cluster": c,
            "rare_capture": overlap/int(rare.sum()), "rare_precision": overlap/size,
            "matched_size": size, "rare_reference_size": int(rare.sum())}


def gap_select(gap, s):
    for i in range(len(gap)-1):
        if gap[i] >= gap[i+1] - s[i+1]:
            return i+1
    return None


def save_csv(out, name, rows):
    pd.DataFrame(rows).to_csv(out / (name + ".csv"), index=False, float_format="%.17g")


def run(pilot=False):
    start = time.time()
    out = HERE / ("pilot" if pilot else "outputs")
    out.mkdir(exist_ok=True)
    registry = json.loads((HERE / "FROZEN_INPUT_REGISTRY.json").read_text())
    for name, h in registry["frozen_payload_sha256"].items():
        assert sha(AUTH / name) == h
    protocol_commit = git("log", "-1", "--format=%H", "--", str(HERE / "PROTOCOL.md"))
    remote_before = git("rev-parse", "refs/remotes/origin/1021")
    assert git("merge-base", "--is-ancestor", protocol_commit, remote_before) == ""
    a = np.load(AUTH / "preprocessing_and_labels.npz", allow_pickle=False)
    x, raw, ids = a["weighted_matrix"], a["raw"], a["tract_ids"]
    f = pd.read_csv(AUTH / "tract_features.csv", dtype={"tract_id": str})
    n = len(x)
    rare = a["K4_sensitivity_labels"] == np.argmin(np.bincount(a["K4_sensitivity_labels"]))
    assert rare.sum() == 37
    arrays = {"GEOID": ids, "historical_rare37_mask": rare}
    ks = list(range(1, 9))
    observed, models, full_rows, profile_rows, contribution_rows = {}, {}, [], [], []
    per_cluster, seed_rows, history_rows = [], [], []
    for k in ks:
        fits = []
        for seed in range(42, 47):
            m = fit(x, k, seed)
            fits.append((m.inertia_, seed, m))
            labels = m.labels_
            arrays[f"full_k{k}_s{seed}_labels"] = labels.astype(np.int16)
            arrays[f"full_k{k}_s{seed}_centers"] = m.cluster_centers_
            row = {"k": k, "seed": seed, "inertia": m.inertia_, "iterations": m.n_iter_}
            if k > 1:
                sil = silhouette_samples(x, labels)
                arrays[f"full_k{k}_s{seed}_silhouette"] = sil
                row.update(silhouette=float(sil.mean()), silhouette_median=float(np.median(sil)),
                           negative_fraction=float(np.mean(sil < 0)),
                           CH=calinski_harabasz_score(x, labels), DB=davies_bouldin_score(x, labels))
                for c in range(k):
                    mask = labels == c
                    vals = sil[mask]
                    per_cluster.append({"k": k, "seed": seed, "cluster": c,
                                        "tracts": int(mask.sum()), "population": int(f.Population[mask].sum()),
                                        "mean_silhouette": vals.mean(), "median_silhouette": np.median(vals),
                                        "p10_silhouette": np.quantile(vals, .1), "p90_silhouette": np.quantile(vals, .9),
                                        "negative_fraction": np.mean(vals < 0)})
            full_rows.append(row)
        _, seed, m = min(fits, key=lambda t: (t[0], t[1]))
        observed[k], models[k] = m.inertia_, m
        for (_, sa, ma), (_, sb, mb) in combinations(fits, 2):
            seed_rows.append({"k": k, "seed_a": sa, "seed_b": sb,
                              "ARI": adjusted_rand_score(ma.labels_, mb.labels_)})
        if k in (3, 4):
            hist = a["K3_labels" if k == 3 else "K4_sensitivity_labels"]
            for _, s, mm in fits:
                history_rows.append({"k": k, "seed": s, "historical_ARI": adjusted_rand_score(hist, mm.labels_),
                                     **rare_match(rare, mm.labels_)})
        if k > 1:
            between = np.zeros(x.shape[1])
            for c in range(k):
                mask = m.labels_ == c
                between += mask.sum() * (x[mask].mean(0)-x.mean(0))**2
                for j, name in enumerate(a["feature_names"]):
                    vals = raw[mask, j]
                    profile_rows.append({"k": k, "reference_seed": seed, "cluster": c,
                                         "tracts": int(mask.sum()), "population": int(f.Population[mask].sum()),
                                         "feature": name, "mean": vals.mean(), "median": np.median(vals),
                                         "p10": np.quantile(vals, .1), "p90": np.quantile(vals, .9),
                                         "min": vals.min(), "max": vals.max(),
                                         "population_fraction": f.Population[mask].sum()/f.Population.sum(),
                                         "median_tract_population": f.Population[mask].median(),
                                         "Q1_fraction": np.mean(f.frozen_SOVI_quartile[mask] == "Q1"),
                                         "Q2_fraction": np.mean(f.frozen_SOVI_quartile[mask] == "Q2"),
                                         "Q3_fraction": np.mean(f.frozen_SOVI_quartile[mask] == "Q3"),
                                         "Q4_fraction": np.mean(f.frozen_SOVI_quartile[mask] == "Q4"),
                                         "zero_housing_tracts": int(f.additional_zero_housing_positive_population[mask].sum())})
            for j, name in enumerate(a["feature_names"]):
                contribution_rows.append({"k": k, "feature": name, "between_SS": between[j],
                                          "fraction_between": between[j]/between.sum(),
                                          "total_SS": np.sum((x[:, j]-x[:, j].mean())**2)})
        print(f"observed K={k} done", flush=True)
    for name, rows in [("OBSERVED_INDICES", full_rows), ("PER_CLUSTER_SILHOUETTE", per_cluster),
                       ("SEED_STABILITY", seed_rows), ("HISTORICAL_MEMBERSHIP_COMPARISON", history_rows),
                       ("ORIGINAL_UNIT_PROFILES", profile_rows), ("COORDINATE_CONTRIBUTIONS", contribution_rows)]:
        save_csv(out, name, rows)

    # Same null draw at all K within a replicate; no rescaling of simulated draws.
    gap_rows, gap_summary, gap_decisions = [], [], {}
    center = x.mean(0)
    rotation = np.linalg.svd(x-center, full_matrices=False)[2].T
    B = 2 if pilot else 64
    for ref, stage in [("axis_uniform", 10), ("PCA_uniform", 11)]:
        transformed = x if stage == 10 else (x-center) @ rotation
        lo, hi = transformed.min(0), transformed.max(0)
        logs = np.empty((B, 8))
        for b in range(B):
            r = rng(stage, b)
            draw = r.uniform(lo, hi, size=x.shape)
            if stage == 11:
                draw = draw @ rotation.T + center
            draw_hash = hashlib.sha256(draw.tobytes()).hexdigest()
            for k in ks:
                seed = new_seed(r)
                mm = fit(draw, k, seed)
                logs[b, k-1] = np.log(mm.inertia_)
                gap_rows.append({"reference": ref, "replicate": b, "k": k, "seed": seed,
                                 "inertia": mm.inertia_, "log_inertia": np.log(mm.inertia_),
                                 "draw_sha256": draw_hash, "iterations": mm.n_iter_})
                arrays[f"gap_{ref}_r{b}_k{k}_labels"] = mm.labels_.astype(np.int16)
                arrays[f"gap_{ref}_r{b}_k{k}_centers"] = mm.cluster_centers_
            if (b+1) % 8 == 0:
                print(f"Gap {ref} {b+1}/{B}", flush=True)
        gaps = logs.mean(0) - np.log([observed[k] for k in ks])
        sd = logs.std(0, ddof=1)
        s = sd * np.sqrt(1+1/B)
        gap_decisions[ref] = gap_select(gaps, s)
        for k in ks:
            i = k-1
            gap_summary.append({"reference": ref, "k": k, "B": B, "observed_WCSS": observed[k],
                                "gap": gaps[i], "reference_SD": sd[i], "MCSE_gap": sd[i]/np.sqrt(B),
                                "s_1SE_rule": s[i], "one_SE_selected_K": gap_decisions[ref],
                                "paired_gap_step_MCSE": (logs[:, i+1]-logs[:, i]).std(ddof=1)/np.sqrt(B) if k < 8 else np.nan,
                                "one_SE_margin": gaps[i]-gaps[i+1]+s[i+1] if k < 8 else np.nan})
    save_csv(out, "GAP_REPLICATES", gap_rows)
    save_csv(out, "GAP_SUMMARY", gap_summary)

    # Grid assignment is geometric, fixed before split outcomes are evaluated.
    geo = gpd.read_file(AUTH / "study_domain_geometry.gpkg").set_index("tract_id").loc[ids]
    assert str(geo.crs).upper() == "EPSG:3310"
    xy = np.column_stack([geo.geometry.centroid.x, geo.geometry.centroid.y])
    cell_xy = np.floor(xy / 20000).astype(int)
    _, cells = np.unique(cell_xy, axis=0, return_inverse=True)
    quadrants = (xy[:, 0] >= np.median(xy[:, 0])).astype(int) + 2*(xy[:, 1] >= np.median(xy[:, 1])).astype(int)
    save_csv(out, "GEOGRAPHIC_ASSIGNMENTS", [{"tract_id": str(ids[i]), "x_m": xy[i, 0], "y_m": xy[i, 1],
                                               "grid_x": cell_xy[i, 0], "grid_y": cell_xy[i, 1],
                                               "cell": cells[i], "quadrant": quadrants[i]} for i in range(n)])
    ps_rows, ps_clusters, spatial_rows = [], [], []
    for design, stage, repeats in [("random_half", 20, 2 if pilot else 50),
                                    ("spatial_20km", 21, 2 if pilot else 20)]:
        for b in range(repeats):
            r = rng(stage, b)
            if stage == 20:
                perm = r.permutation(n)
                halves = (perm[:n//2], perm[n//2:])
            else:
                cell_ids = r.permutation(np.unique(cells))
                halves = (np.flatnonzero(np.isin(cells, cell_ids[:len(cell_ids)//2])),
                          np.flatnonzero(np.isin(cells, cell_ids[len(cell_ids)//2:])))
            arrays[f"split_{design}_r{b}_half0"] = halves[0]
            arrays[f"split_{design}_r{b}_half1"] = halves[1]
            for k in range(2, 7):
                seeds = [new_seed(r), new_seed(r)]
                mm = [fit(x[part], k, seed) for part, seed in zip(halves, seeds)]
                for direction in range(2):
                    train, valid = direction, 1-direction
                    actual = mm[valid].labels_
                    pred = mm[train].predict(x[halves[valid]])
                    strength, rows = pair_strength(actual, pred)
                    prefix = f"ps_{design}_r{b}_k{k}_d{direction}"
                    arrays[prefix+"_actual"] = actual.astype(np.int16)
                    arrays[prefix+"_predicted"] = pred.astype(np.int16)
                    arrays[prefix+"_training_centers"] = mm[train].cluster_centers_
                    ps_rows.append({"design": design, "repeat": b, "k": k, "direction": direction,
                                    "training_seed": seeds[train], "validation_seed": seeds[valid],
                                    "training_n": len(halves[train]), "validation_n": len(halves[valid]),
                                    "strength": strength, "minimum_validation_size": min(z["n"] for z in rows),
                                    "ARI_not_prediction_strength": adjusted_rand_score(actual, pred),
                                    **rare_match(rare, mm[train].predict(x))})
                    for row in rows:
                        ps_clusters.append({"design": design, "repeat": b, "k": k, "direction": direction, **row})
            if (b+1) % 10 == 0:
                print(f"Prediction strength {design} {b+1}/{repeats}", flush=True)
    for q in range(4):
        train, test = np.flatnonzero(quadrants != q), np.flatnonzero(quadrants == q)
        for k in range(2, 7):
            r = rng(21, 100+q, k)
            seed = new_seed(r)
            mm = fit(x[train], k, seed)
            pred = mm.predict(x)
            arrays[f"quadrant{q}_k{k}_predicted"] = pred.astype(np.int16)
            arrays[f"quadrant{q}_k{k}_centers"] = mm.cluster_centers_
            spatial_rows.append({"quadrant": q, "k": k, "seed": seed, "held_out_n": len(test),
                                 "full_ARI": adjusted_rand_score(models[k].labels_, pred),
                                 "held_out_ARI": adjusted_rand_score(models[k].labels_[test], pred[test]),
                                 **rare_match(rare, pred)})
    save_csv(out, "PREDICTION_STRENGTH_REPETITIONS", ps_rows)
    save_csv(out, "PREDICTION_STRENGTH_CLUSTER_PAIRS", ps_clusters)
    save_csv(out, "SPATIAL_LEAVE_QUADRANT_OUT", spatial_rows)

    bootstrap_rows = []
    Bboot = 2 if pilot else 100
    for b in range(Bboot):
        r = rng(30, b)
        sample = r.integers(0, n, n)
        unique = np.unique(sample)
        arrays[f"bootstrap_r{b}_indices"] = sample
        for k in range(2, 7):
            seed = new_seed(r)
            mm = fit(x[sample], k, seed)
            predicted = mm.predict(x)
            arrays[f"bootstrap_r{b}_k{k}_labels"] = mm.labels_.astype(np.int16)
            arrays[f"bootstrap_r{b}_k{k}_centers"] = mm.cluster_centers_
            arrays[f"bootstrap_r{b}_k{k}_full_predicted"] = predicted.astype(np.int16)
            for support, ix in [("unique_inbag", unique), ("full_prediction", np.arange(n))]:
                rows = best_jaccard(models[k].labels_[ix], predicted[ix])
                for row in rows:
                    bootstrap_rows.append({"repeat": b, "k": k, "seed": seed, "support": support,
                                           "unique_inbag": len(unique), "inertia": mm.inertia_,
                                           "dissolved_J_lt_0_5": row["jaccard"] < .5,
                                           "recovered_J_ge_0_75": row["jaccard"] >= .75,
                                           **row, **rare_match(rare, predicted)})
        if (b+1) % 10 == 0:
            print(f"Bootstrap {b+1}/{Bboot}", flush=True)
    save_csv(out, "BOOTSTRAP_CLUSTER_STABILITY", bootstrap_rows)

    ward_rows = []
    hierarchy = linkage(x, method="ward", metric="euclidean")
    arrays["ward_linkage"] = hierarchy
    for k in range(2, 9):
        labels = cut_tree(hierarchy, n_clusters=[k])[:, 0]
        arrays[f"ward_k{k}_labels"] = labels.astype(np.int16)
        sil = silhouette_samples(x, labels)
        for row in best_jaccard(models[k].labels_, labels):
            ward_rows.append({"k": k, "ARI": adjusted_rand_score(models[k].labels_, labels),
                              "ward_silhouette": sil.mean(), "ward_negative_fraction": np.mean(sil < 0),
                              **row, **rare_match(rare, labels)})
    save_csv(out, "WARD_COMPARISONS", ward_rows)

    ablation_rows = []
    projected = x.copy()
    projected[:, 0] = 0
    for k in range(2, 7):
        for seed in range(42, 47):
            mm = fit(projected, k, seed)
            arrays[f"init_projection_k{k}_s{seed}_labels"] = mm.labels_.astype(np.int16)
            arrays[f"init_projection_k{k}_s{seed}_centers"] = mm.cluster_centers_
            ablation_rows.append({"k": k, "seed": seed, "no_budget_redistribution": True,
                                   "ARI": adjusted_rand_score(models[k].labels_, mm.labels_),
                                   "silhouette_conditional_geometry": silhouette_samples(projected, mm.labels_).mean(),
                                   **rare_match(rare, mm.labels_)})
    save_csv(out, "INIT_COORDINATE_PROJECTION", ablation_rows)
    np.savez_compressed(out / "ALL_FITTED_ARRAYS.npz", **arrays)
    # Preserve previous policy sensitivity as prior evidence, not new experiments.
    (out / "PRIOR_POLICY_SET_STABILITY.csv").write_bytes((AUTH / "policy_set_stability.csv").read_bytes())
    elapsed = time.time()-start
    manifest = {
        "status": "PILOT_NOT_FULL" if pilot else "FULL_REGISTERED_ANALYSIS",
        "protocol_commit": protocol_commit, "protocol_sha256": sha(HERE / "PROTOCOL.md"),
        "remote_tracking_HEAD_before_run": remote_before,
        "baseline": BASE, "Python": platform.python_version(), "platform": platform.platform(),
        "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
        "pandas": pd.__version__, "seconds": elapsed, "Gap_B_each": B,
        "prediction_random_repetitions": 2 if pilot else 50,
        "prediction_spatial_repetitions": 2 if pilot else 20, "bootstrap_repetitions": Bboot,
        "gap_1SE_decisions": gap_decisions,
        "Kmeans": {"init": "k-means++", "n_init": 50, "algorithm": "lloyd", "max_iter": 500, "tol": 1e-4},
        "thread_limit": 1, "input_registry_sha256": sha(HERE / "FROZEN_INPUT_REGISTRY.json"),
        "output_sha256": {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != "RUN_MANIFEST.json"},
        "no_physical_simulation_or_formal_output_changes": True,
    }
    (out / "RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=2)+"\n", newline="\n")
    print(json.dumps({"status": manifest["status"], "elapsed_s": elapsed, "Gap": gap_decisions}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(pilot=args.pilot)
