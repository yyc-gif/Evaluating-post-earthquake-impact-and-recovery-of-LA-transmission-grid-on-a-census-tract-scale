"""Registered cross-K, held-out outcome and 70/85-percent subsampling analysis."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
import json
from itertools import combinations
import time
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.linear_model import Ridge
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from sklearn.preprocessing import SplineTransformer
from threadpoolctl import threadpool_limits
from common import *


def align(reference, prediction, k):
    counts = np.zeros((k, k), dtype=int)
    np.add.at(counts, (reference, prediction), 1)
    left, right = linear_sum_assignment(-counts)
    lookup = np.empty(k, dtype=int)
    lookup[right] = left
    return lookup[prediction]


def grouping(cuts_from, values, k):
    cuts = np.unique(np.quantile(cuts_from, np.arange(1, k)/k))
    return np.searchsorted(cuts, values, side="right"), cuts


def grouped_prediction(train_labels, test_labels, y):
    prediction = np.full((len(test_labels), y.shape[1]), np.nan)
    for c in np.unique(train_labels):
        with np.errstate(invalid="ignore"):
            average = np.nanmean(y[train_labels == c], axis=0)
        prediction[test_labels == c] = average
    return prediction


def mean_finite(a, axis=0):
    counts = np.sum(np.isfinite(a), axis=axis)
    return np.divide(np.nansum(a, axis=axis), counts, out=np.full_like(counts, np.nan, dtype=float), where=counts>0)


def main():
    started = time.time()
    assert json.loads((HERE/"SOURCE_QA.json").read_text())["status"] == "PASS"
    protocol = git("log", "-1", "--format=%H", "--", str(HERE/"PROTOCOL.md")).decode().strip()
    git("merge-base", "--is-ancestor", protocol, "refs/remotes/origin/1021")
    a, cohort, refs = inputs()
    x, n = a["weighted_matrix"], len(cohort)
    outcomes = pd.read_csv(HERE/"UNFITTED_TRACT_OUTCOMES.csv", dtype={"tract_id": str})
    np.testing.assert_array_equal(outcomes.tract_id, cohort.tract_id)
    names = [c for c in outcomes if c != "tract_id" and c != "unconstrained__B480_mean"]
    # Unconstrained B is a fitted coordinate; retain it in the source table ONLY.
    y = outcomes[names].to_numpy()
    save("OUTCOME_REGISTER.csv", [{"outcome": name, "meaningful_group_difference": meaningful(name),
                                   "notable_MAE_gain": mae_margin(name), "n_finite": int(np.isfinite(y[:, j]).sum()),
                                   "role": ("primary" if name in ["random__B480_mean", "impact__T80_reached_p50"]
                                            else "ancillary_identity_descriptor" if name == "impact__B480_mean" else "supporting"),
                                   "source_type": "same-model unfitted outcome; not external validation"} for j, name in enumerate(names)])
    arrays = {"tract_ids": a["tract_ids"], "outcome_names": np.array(names)}
    profiles, crosses, intersections, partitions = [], [], [], []
    reference_means = {}
    for k in [2, 3, 4]:
        arrays[f"reference_k{k}"] = refs[k]
        reference_means[k] = np.stack([mean_finite(y[refs[k] == c]) for c in range(k)])
        for c in range(k):
            mask = refs[k] == c
            for j, name in enumerate(names):
                vals = y[mask, j]
                profiles.append({"k": k, "cluster": c, "tracts": int(mask.sum()),
                                 "population": int(cohort.Population[mask].sum()), "outcome": name,
                                 "mean": float(reference_means[k][c, j]), "median": float(np.nanmedian(vals)),
                                 "p10": float(np.nanquantile(vals, .1)), "p90": float(np.nanquantile(vals, .9)),
                                 "valid": int(np.isfinite(vals).sum()),
                                 "population_weighted_mean": float(np.nansum(vals*cohort.Population[mask])/cohort.Population[mask][np.isfinite(vals)].sum())})
    for ka, kb in combinations([2, 3, 4], 2):
        partitions.append({"k_a": ka, "k_b": kb, "ARI": adjusted_rand_score(refs[ka], refs[kb]),
                           "NMI": normalized_mutual_info_score(refs[ka], refs[kb])})
        for ca in range(ka):
            for cb in range(kb):
                ma, mb = refs[ka] == ca, refs[kb] == cb
                mask = ma & mb
                crosses.append({"k_a": ka, "class_a": ca, "k_b": kb, "class_b": cb,
                                "tracts": int(mask.sum()), "population": int(cohort.Population[mask].sum()),
                                "fraction_of_a": mask.sum()/ma.sum(), "fraction_of_b": mask.sum()/mb.sum(),
                                "Jaccard": mask.sum()/np.sum(ma | mb)})
                if mask.any():
                    for j, name in enumerate(names):
                        intersections.append({"k_a": ka, "class_a": ca, "k_b": kb, "class_b": cb,
                                              "tracts": int(mask.sum()), "outcome": name,
                                              "mean": float(mean_finite(y[mask, j]))})
    save("REFERENCE_OUTCOME_PROFILES.csv", profiles)
    save("CROSS_K_MEMBERSHIP_OVERLAP.csv", crosses)
    save("CROSS_K_LABEL_INVARIANT_AGREEMENT.csv", partitions)
    save("CROSS_K_SHARED_SUBSET_OUTCOMES.csv", intersections)

    benchmarks = {"baseline_deficit": cohort.B_Unconstrained.to_numpy(),
                  "constraint_increment": cohort.MeanDelta.to_numpy(),
                  "SOVI": cohort.SOVI_SCORE.to_numpy(),
                  "mean_total_deficit": (cohort.B_Unconstrained+cohort.MeanDelta).to_numpy()}
    resampling, class_stability, scores, changes, contrasts, cut_rows = [], [], [], [], [], []
    assignment_counts = {k: np.zeros((2, n), dtype=int) for k in refs}
    oob_assignment_counts = {k: np.zeros((2, n), dtype=int) for k in refs}
    oob_denominator = np.zeros((2, n), dtype=int)
    for fi, percent in enumerate([70, 85]):
        size = int(np.floor(percent/100*n))
        for b in range(100):
            r = np.random.default_rng(np.random.SeedSequence([1021, percent, b]))
            train = np.sort(r.choice(n, size=size, replace=False))
            test = np.setdiff1d(np.arange(n), train)
            arrays[f"p{percent}_r{b}_train"] = train
            oob_denominator[fi, test] += 1
            models = {}
            for k in [2, 3, 4]:
                seed = int(r.integers(0, 2**31-1))
                model = KMeans(n_clusters=k, n_init=50, init="k-means++", algorithm="lloyd",
                               max_iter=500, tol=1e-4, random_state=seed).fit(x[train])
                raw_labels = model.predict(x)
                predicted = align(refs[k], raw_labels, k)
                models[f"K{k}"] = (raw_labels[train], raw_labels[test])
                arrays[f"p{percent}_r{b}_k{k}_labels"] = predicted.astype(np.int16)
                arrays[f"p{percent}_r{b}_k{k}_raw_labels"] = raw_labels.astype(np.int16)
                arrays[f"p{percent}_r{b}_k{k}_centers"] = model.cluster_centers_
                assignment_counts[k][fi] += predicted == refs[k]
                oob_assignment_counts[k][fi, test] += predicted[test] == refs[k][test]
                resampling.append({"percent": percent, "repeat": b, "k": k, "seed": seed,
                                   "train_n": len(train), "test_n": len(test),
                                   "full_ARI": adjusted_rand_score(refs[k], predicted),
                                   "test_ARI": adjusted_rand_score(refs[k][test], predicted[test]),
                                   "train_inertia": model.inertia_})
                new_means = np.stack([mean_finite(y[predicted == c]) for c in range(k)])
                for c in range(k):
                    target, member = refs[k] == c, predicted == c
                    for support, ix in [("full", np.arange(n)), ("held_out", test)]:
                        union = np.sum((target | member)[ix])
                        class_stability.append({"percent": percent, "repeat": b, "k": k, "cluster": c,
                                                "support": support, "reference_n": int(target[ix].sum()),
                                                "predicted_n": int(member[ix].sum()),
                                                "Jaccard": np.sum((target & member)[ix])/union if union else np.nan})
                    for j, name in enumerate(names):
                        difference = new_means[c, j]-reference_means[k][c, j]
                        changes.append({"percent": percent, "repeat": b, "k": k, "cluster": c, "outcome": name,
                                        "reference_mean": reference_means[k][c, j], "resample_mean": new_means[c, j],
                                        "mean_change": difference,
                                        "within_registered_profile_tolerance": abs(difference) <= mae_margin(name)})
                for ca, cb in combinations(range(k), 2):
                    old = reference_means[k][ca]-reference_means[k][cb]
                    new = new_means[ca]-new_means[cb]
                    for j, name in enumerate(names):
                        contrasts.append({"percent": percent, "repeat": b, "k": k, "a": ca, "b": cb,
                                          "outcome": name, "reference_difference": old[j], "resample_difference": new[j],
                                          "same_sign_and_meaningful": np.sign(old[j]) == np.sign(new[j]) and abs(new[j]) >= meaningful(name)})
            for label, values in benchmarks.items():
                for k in [2, 3, 4]:
                    groups, cuts = grouping(values[train], values, k)
                    models[f"Q{k}_{label}"] = (groups[train], groups[test])
                    cut_rows.append({"percent": percent, "repeat": b, "benchmark": label, "requested_k": k,
                                     "actual_training_groups": len(np.unique(groups[train])), "cutpoints": json.dumps(cuts.tolist())})
            predictions = {name: grouped_prediction(tr, te, y[train]) for name, (tr, te) in models.items()}
            linear_train = np.column_stack([np.ones(len(train)), x[train]])
            linear_test = np.column_stack([np.ones(len(test)), x[test]])
            transformer = SplineTransformer(n_knots=4, degree=3, knots="quantile", include_bias=False)
            spline_train, spline_test = transformer.fit_transform(x[train]), None
            spline_test = transformer.transform(x[test])
            ols = np.full((len(test), len(names)), np.nan)
            spline = ols.copy()
            all_finite = np.isfinite(y[train]).all(0)
            if all_finite.any():
                coef = np.linalg.lstsq(linear_train, y[train][:, all_finite], rcond=None)[0]
                ols[:, all_finite] = linear_test @ coef
                spline[:, all_finite] = Ridge(alpha=1).fit(spline_train, y[train][:, all_finite]).predict(spline_test)
            for j in np.flatnonzero(~all_finite):
                valid = np.isfinite(y[train, j])
                if valid.any():
                    ols[:, j] = linear_test @ np.linalg.lstsq(linear_train[valid], y[train, j][valid], rcond=None)[0]
                    spline[:, j] = Ridge(alpha=1).fit(spline_train[valid], y[train, j][valid]).predict(spline_test)
            predictions.update(OLS_seven=ols, additive_seven=spline)
            for method, pred in predictions.items():
                for j, name in enumerate(names):
                    valid = np.isfinite(y[test, j]) & np.isfinite(pred[:, j])
                    error = pred[valid, j]-y[test, j][valid]
                    scores.append({"percent": percent, "repeat": b, "method": method, "outcome": name,
                                   "MAE": np.mean(abs(error)) if len(error) else np.nan,
                                   "RMSE": np.sqrt(np.mean(error**2)) if len(error) else np.nan,
                                   "valid_test_n": len(error), "available_test_outcome_n": int(np.isfinite(y[test, j]).sum()),
                                   "total_test_n": len(test)})
            if (b+1) % 20 == 0:
                print(f"{percent}% subsampling {b+1}/100", flush=True)
    save("SUBSAMPLING_MEMBERSHIP.csv", resampling)
    save("SUBSAMPLING_CLASS_JACCARD.csv", class_stability)
    save("HELD_OUT_OUTCOME_SCORES.csv", scores)
    save("SUBSAMPLING_RECOVERY_PROFILE_CHANGES.csv", changes)
    save("SUBSAMPLING_ENGINEERING_CONTRAST_PERSISTENCE.csv", contrasts)
    save("SIMPLE_BENCHMARK_CUTS.csv", cut_rows)
    core_rows = []
    for k in refs:
        for i, tract in enumerate(cohort.tract_id):
            row = {"tract_id": tract, "k": k, "reference_class": int(refs[k][i]),
                   "Population": int(cohort.Population.iloc[i])}
            for fi, percent in enumerate([70, 85]):
                row[f"p{percent}_same_class_frequency"] = assignment_counts[k][fi, i]/100
                row[f"p{percent}_held_out_n"] = int(oob_denominator[fi, i])
                row[f"p{percent}_held_out_same_class_frequency"] = (oob_assignment_counts[k][fi, i]/oob_denominator[fi, i]
                                                                 if oob_denominator[fi, i] else np.nan)
            row["pooled_same_class_frequency"] = assignment_counts[k][:, i].sum()/200
            row["stable_core_ge_0_9"] = row["pooled_same_class_frequency"] >= .9
            core_rows.append(row)
    save("TRACT_MEMBERSHIP_CORE_FREQUENCIES.csv", core_rows)
    np.savez_compressed(HERE/"SUBSAMPLING_ARRAYS.npz", **arrays)
    dump("ANALYSIS_RUN.json", {"status": "FULL_REGISTERED", "start_commit": START, "protocol_commit": protocol,
                               "protocol_sha256": sha(HERE/"PROTOCOL.md"), "source_tract_values_sha256": sha(HERE/"UNFITTED_TRACT_OUTCOMES.csv"),
                               "samples_per_fraction": 100, "fractions": [70, 85], "outcomes": names,
                               "n_models": 600, "seconds": time.time()-started,
                               "continuous_models_are_not_external_validation": True})


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        main()
