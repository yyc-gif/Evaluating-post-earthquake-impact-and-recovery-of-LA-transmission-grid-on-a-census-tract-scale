"""Rebuild the independent tract evidence from the immutable Git LFS snapshot."""
import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import subprocess

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import ScalarFormatter
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

REV = "1887bca4872f24d6d547637440db5619a4423452"
STAGE = "results/stage7/2026-10-14/"
REVIEW = "docs/data_research/stage7_path_b_p2_integration_review_20261014/"
SOURCES = {
    "burden": STAGE + "five_policy_total_deficit.csv",
    "p2": REVIEW + "FROZEN_P2_TRACT_TABLE_2315.csv",
    "policy": REVIEW + "inputs/FROZEN_POLICY_TRACT_MEANS_2315.csv",
    "features": STAGE + "tract_features.csv",
    "geometry": REVIEW + "inputs/FULL_2315_GEOMETRY.gpkg",
    "blocks": REVIEW + "inputs/SPATIAL_BLOCK_ASSIGNMENTS.csv",
    "membership": REVIEW + "P2_FROZEN_MEMBERSHIPS.csv",
    "eligibility": REVIEW + "P2_COHORT_ELIGIBILITY_2315.csv",
    "components": "Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_SOURCE_LOSS_BY_TRACT.csv",
}
REPORTED = {
    "burden": ("8d182f5485315f3da13dd2182e86f91799365a4b5636a6c38e863d59c22fcc37", 176630),
    "p2": ("4f5ca1fab302443ed899c919894de89622ec60b458b6511325105ac3d934f211", 829685),
    "policy": ("f2746d8b985ddc89c0930a0b334aa7eb5c3f7b0a83035f31f861adad4a310a30", 565348),
}
Q = "frozen_SOVI_quartile"
B = "B_Unconstrained"
M = "MeanDelta"
T = "MeanTotal5"
POLICY = ["impact-first", "hospital-first", "degree-first", "betweenness-first", "vulnerability-first"]
ADDED = [M] + ["Delta_" + p for p in POLICY] + ["MeanDelta_no_vulnerability"]
CLASS_NAME = {
    "C1": "Higher vulnerability, lower added burden",
    "C2": "Lower baseline, higher added burden",
    "C3": "Higher baseline burden",
}
SPATIAL = ["broad_region", "block_10000"]
TOL = 1e-10
COLORS = {"Neither": "#e5e7e9", "Baseline only": "#2067a0", "Added only": "#d88813",
          "Both": "#6b378a"}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def acquire(repo, cache, fetch):
    git = ["git", "-C", str(repo)]
    if fetch:
        subprocess.run(git + ["-c", f"lfs.storage={cache}", "lfs", "fetch",
                              "--include=" + ",".join(SOURCES.values()), "--exclude=", "origin", REV],
                       check=True)
    records, paths = {}, {}
    for name, rel in SOURCES.items():
        blob = subprocess.check_output(git + ["show", f"{REV}:{rel}"]).decode("ascii")
        pointer = re.fullmatch(
            r"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n?",
            blob.replace("\r\n", "\n")
        )
        check(pointer is not None, f"Not a Git LFS pointer at {REV}: {rel}")
        oid, size = pointer.group(1), int(pointer.group(2))
        if name in REPORTED:
            check((oid, size) == REPORTED[name], f"Exploration package disagrees: {rel}")
        payload = cache / "objects" / oid[:2] / oid[2:4] / oid
        with payload.open("rb") as stream:
            observed = hashlib.file_digest(stream, "sha256").hexdigest()
        check(observed == oid and payload.stat().st_size == size, f"Payload mismatch: {rel}")
        records[name] = {"path": rel, "lfs_sha256": oid, "observed_sha256": observed, "bytes": size}
        paths[name] = payload
    return paths, records


def read_table(path):
    return pd.read_csv(path, dtype={"tract_id": str}, float_precision="round_trip")


def indexed(frame, name, domain=None):
    check(frame.tract_id.str.fullmatch(r"\d{11}", na=False).all(), f"Invalid GEOID: {name}")
    check(frame.tract_id.is_unique, f"Duplicate GEOID: {name}")
    result = frame.set_index("tract_id").sort_index()
    if domain is not None:
        check(result.index.equals(domain), f"GEOID domain mismatch: {name}")
    return result


def close(a, b, name, evidence):
    gap = float(np.max(np.abs(np.asarray(a) - np.asarray(b))))
    check(np.isfinite(gap) and gap <= TOL, f"{name}: {gap}")
    evidence[name] = gap


def finite(frame, cols):
    check(np.isfinite(frame[cols].to_numpy(dtype=float)).all(), f"Missing/nonfinite in {cols}")


def exact_decimal_errors(paths):
    def rows(name):
        with paths[name].open(encoding="utf-8", newline="") as stream:
            return {r["tract_id"]: r for r in csv.DictReader(stream)}
    main, policies = rows("p2"), rows("policy")
    errors = {}
    for geoid, a in main.items():
        p = policies[geoid]
        values = [Decimal(p["B_" + policy]) for policy in POLICY]
        checks = {
            "saved_total_minus_baseline_plus_added_h": Decimal(a[T]) - Decimal(a[B]) - Decimal(a[M]),
            "saved_total_minus_policy_average_h": Decimal(a[T]) - sum(values) / 5,
            "saved_added_minus_matched_policy_added_h":
                Decimal(a[M]) - (sum(values) / 5 - Decimal(p["B_unconstrained"])),
        }
        for name, error in checks.items():
            errors[name] = max(errors.get(name, Decimal(0)), abs(error))
    check(max(errors.values()) < Decimal("1e-12"), "Stored-precision reconciliation failed")
    return {k: str(v) for k, v in errors.items()}


def read_data(paths, records):
    names = ["burden", "p2", "policy", "features", "blocks", "eligibility", "membership"]
    raw = {name: read_table(paths[name]) for name in names}
    for name, table in raw.items():
        records[name].update(rows=len(table), missing_by_column=table.isna().sum().to_dict())
    p2 = indexed(raw["p2"], "p2 full domain")
    d = p2[[B, M, T, Q, "Population"]].copy()
    domain = d.index
    check(len(d) == 2315 and d.Population.gt(0).sum() == 2299 and d.Population.sum() == 9066522,
          "Frozen domain, cohort or population differs")
    check(d[Q].notna().all() and d.Population.ge(0).all() and set(d[Q]) == {"Q1", "Q2", "Q3", "Q4"}, "Invalid population or quartile")
    positive = d.index[d.Population.gt(0)]
    policy = indexed(raw["policy"], "policy", domain)
    eligibility = indexed(raw["eligibility"], "eligibility", domain)
    feature = indexed(raw["features"], "features", positive)
    compact = indexed(raw["burden"], "compact burden", positive)
    for name, frame in [("policy", policy), ("features", feature), ("compact", compact),
                        ("eligibility", eligibility)]:
        check(frame[Q].equals(d.loc[frame.index, Q]) and
              np.array_equal(frame.Population, d.loc[frame.index, "Population"]),
              f"Frozen population or quartile mismatch: {name}")
    check(np.array_equal(eligibility.eligible, d.Population.gt(0)), "Frozen eligibility disagrees")
    m = indexed(raw["membership"].loc[raw["membership"].model.eq("P2_K3")], "K3 membership", positive)
    check(set(m.class_id) == set(CLASS_NAME) and
          np.array_equal(m.saved_label.to_numpy() + 1, p2.loc[positive, "P2_K3_class"]),
          "Saved class IDs disagree")
    check(m.class_id.value_counts().to_dict() == {"C1": 1235, "C2": 428, "C3": 636},
          "Saved class sizes disagree")
    check(m.groupby("class_id").apply(lambda g: d.loc[g.index, "Population"].sum(),
                                      include_groups=False).to_dict() ==
          {"C1": 5184036, "C2": 1695501, "C3": 2186985}, "Saved class populations disagree")
    d["community_id"] = m.class_id
    d["community_type"] = d.community_id.map(CLASS_NAME)
    evidence = {}
    for frame, name in [(compact, "compact"), (feature, "features")]:
        for field in [B, M, T]:
            close(d.loc[positive, field], frame[field], f"{name}_{field}", evidence)
    for field in ["Init_Supply", "Grid_Impact", "Redundancy_HHI", "SOVI_SCORE"]:
        close(p2.loc[positive, field], feature[field], field, evidence)
        d[field] = p2[field]
    close(d[B], policy.B_unconstrained, "matched_policy_baseline", evidence)
    cols = ["B_" + p for p in POLICY]
    d[cols] = policy[cols]
    for p in POLICY:
        d["Delta_" + p] = policy["B_" + p] - policy.B_unconstrained
    d["MeanDelta_no_vulnerability"] = d[ADDED[1:-2]].mean(axis=1)
    close(d["MeanDelta_no_vulnerability"], policy.MeanDelta4_no_Vulnerability,
          "mean_added_without_vulnerability_first", evidence)
    close(d[M], policy.MeanDelta5, "saved_policy_mean_added", evidence)
    close(d[T], policy.MeanTotal5, "saved_policy_mean_total", evidence)
    d[["utm_x_m", "utm_y_m"]] = p2[["utm_x_m", "utm_y_m"]]
    blocks = indexed(raw["blocks"], "spatial blocks")
    check(blocks.index.equals(domain) or blocks.index.equals(positive), "Unexpected block domain")
    d[SPATIAL] = blocks[SPATIAL]
    # If the archived blocks cover only the eligible cohort, retain those labels and
    # compute meter-grid IDs for the remaining 16. Broad-region runs use the cohort.
    derived_10km = (np.floor(d.utm_x_m / 10000).astype(int).astype(str) + "_" +
                    np.floor(d.utm_y_m / 10000).astype(int).astype(str))
    check(d.loc[blocks.index, "block_10000"].equals(derived_10km.loc[blocks.index]),
          "Archived grid is inconsistent with recorded coordinates")
    d["block_10000"] = d.block_10000.fillna(derived_10km)
    geo = indexed(gpd.read_file(paths["geometry"], engine="pyogrio"), "geometry", domain)
    check(geo.crs is not None and (~geo.geometry.is_empty & geo.geometry.notna()).all(), "Missing geometry")
    records["geometry"].update(rows=len(geo), invalid_polygons=int((~geo.geometry.is_valid).sum()),
                               crs=str(geo.crs))
    finite(d, [B, T, "Population", *ADDED, *cols, "Redundancy_HHI", "SOVI_SCORE",
               "Grid_Impact", "Init_Supply", "utm_x_m", "utm_y_m"])
    check(d.loc[positive, SPATIAL].notna().all().all(), "Missing positive-cohort block")
    return d, geo.to_crs(26911), evidence


def add_components(d, paths, records, checks):
    raw = read_table(paths["components"])
    selected = raw.loc[raw.hazard.eq("2pc50") & raw.resource_scenario.eq("C57_D1")]
    matched = ["unconstrained"] + POLICY[:-1]
    field_set = ["mean_self_loss_hr", "mean_threshold_loss_hr", "mean_source_loss_hr", "mean_total_loss_hr"]
    records["components"].update(rows=len(raw), target_policies=matched,
                                 missing_by_column=raw.isna().sum().to_dict())
    source_cols = []
    for policy in matched:
        f = indexed(selected.loc[selected.strategy_id.eq(policy)], policy + " component", d.index)
        finite(f, field_set)
        check(np.array_equal(f.population, d.Population), "Component population mismatch")
        close(f[field_set[:3]].sum(axis=1), f.mean_total_loss_hr, "component_sum_" + policy, checks)
        close(f.mean_total_loss_hr, d[B if policy == "unconstrained" else "B_" + policy],
              "component_total_" + policy, checks)
        name = "source_path_" + policy + "_h"
        d[name] = f.mean_source_loss_hr
        source_cols.append(name)
    d["source_path_added_4_h"] = d[source_cols[1:]].mean(axis=1) - d[source_cols[0]]
    d["baseline_without_source_h"] = d[B] - d[source_cols[0]]
    d["added_without_source_4_h"] = d.MeanDelta_no_vulnerability - d.source_path_added_4_h


def weighted_r(x, y, w):
    x0 = x - np.average(x, weights=w)
    y0 = y - np.average(y, weights=w)
    return np.average(x0*y0, weights=w) / np.sqrt(
        np.average(x0*x0, weights=w) * np.average(y0*y0, weights=w)
    )


def weighted_midcdf(x, w):
    _, groups = np.unique(x, return_inverse=True)
    counts = np.bincount(groups, weights=w)
    return ((np.cumsum(counts) - counts / 2) / counts.sum())[groups]


def associations(d, xcol, ycol):
    x, y, w = d[[xcol, ycol, "Population"]].to_numpy(dtype=float).T
    return dict(pearson=weighted_r(x, y, np.ones(len(d))),
                spearman=weighted_r(rankdata(x), rankdata(y), np.ones(len(d))),
                pop_pearson=weighted_r(x, y, w),
                pop_spearman=weighted_r(weighted_midcdf(x, w), weighted_midcdf(y, w), w))


def distribution(d, field):
    x, w = d[field].to_numpy(), d.Population.to_numpy()
    order = np.argsort(x)
    cumulative = w[order].cumsum() / w.sum()
    p10, p25, p50, p75, p90 = np.quantile(x, [.1, .25, .50, .75, .9])
    wp10, wp25, wp50, wp75, wp90 = x[order][np.searchsorted(cumulative, [.1, .25, .50, .75, .9])]
    return dict(n=len(d), population=int(w.sum()), mean_h=x.mean(), p10_h=p10, p25_h=p25,
                median_h=p50, p75_h=p75, p90_h=p90, pop_mean_h=np.average(x, weights=w),
                pop_p10_h=wp10, pop_p25_h=wp25, pop_median_h=wp50, pop_p75_h=wp75, pop_p90_h=wp90,
                n_negative=int((x < 0).sum()), pop_negative=int(w[x < 0].sum()))


def qgap(d, field):
    s = [distribution(d.loc[d[Q].eq(q)], field) for q in ["Q1", "Q4"]]
    return {"q4_minus_q1_" + f: s[1][f] - s[0][f]
            for f in ["mean_h", "pop_mean_h", "median_h", "pop_median_h"]}


def top_overlap(d, xcol, ycol, percentile=.75):
    px, py = d[[xcol, ycol]].quantile(percentile)
    x, y = d[xcol].ge(px), d[ycol].ge(py)
    both, either = x & y, x | y
    w = d.Population
    ans = dict(n=len(d), population=int(w.sum()), threshold_quantile=percentile,
               baseline_cutoff_h=px, added_cutoff_h=py,
               baseline_at_cutoff_n=int(d[xcol].eq(px).sum()), added_at_cutoff_n=int(d[ycol].eq(py).sum()),
               jaccard=both.sum()/either.sum(), pop_jaccard=w[both].sum()/w[either].sum(),
               both_fraction_of_baseline=both.sum()/x.sum(), both_fraction_of_added=both.sum()/y.sum(),
               independence_benchmark_share=x.mean()*y.mean())
    for key, mask in dict(baseline_top=x, added_top=y, both=both, either=either, baseline_only=x & ~y,
                          added_only=y & ~x, neither=~either).items():
        ans[key+"_n"] = int(mask.sum())
        ans[key+"_tract_share"] = mask.mean()
        ans[key+"_pop"] = int(w[mask].sum())
        ans[key+"_pop_share"] = w[mask].sum()/w.sum()
    return ans, x, y


def overlap_label(x, y):
    return np.select([x & y, x, y], ["Both", "Baseline only", "Added only"], default="Neither")


def spatial_diagnostics(d, destination):
    positive = d.loc[d.Population.gt(0)]
    sensitivity = []
    for scope, frame in [("all_2315", d), ("positive_2299", positive)]:
        for scheme in SPATIAL:
            groups = frame[scheme]
            if groups.isna().any():
                continue
            for block in sorted(groups.unique()):
                keep = frame.loc[groups.ne(block)]
                for field in ADDED:
                    scores = associations(keep, B, field)
                    overlap, _, _ = top_overlap(keep, B, field)
                    sensitivity.append(dict(
                        cohort=scope, scheme=scheme, omitted_block=block, outcome=field, n=len(keep),
                        removed_n=len(frame)-len(keep), removed_pop=int(frame.Population.sum()-keep.Population.sum()),
                        **scores, **qgap(keep, B),
                        added_q4_minus_q1_pop_mean_h=qgap(keep, field)["q4_minus_q1_pop_mean_h"],
                        jaccard=overlap["jaccard"], both_pop_share=overlap["both_pop_share"]
                    ))
    pd.DataFrame(sensitivity).to_csv(destination / "spatial_leave_block_out.csv", index=False, lineterminator="\n")

    cv, profiles, counts = [], [], []
    for scope, frame in [("all_2315", d), ("positive_2299", positive)]:
        _, x, y = top_overlap(frame, B, M)
        frame = frame.assign(baseline_top=x.astype(int), added_top=y.astype(int),
                             overlap_group=overlap_label(x, y))
        for scheme in SPATIAL:
            for key, g in frame.groupby(scheme, dropna=False):
                for group in COLORS:
                    selected = g.loc[g.overlap_group.eq(group)]
                    counts.append(dict(cohort=scope, scheme=scheme, block=key, overlap_group=group,
                                       n=len(selected), population=int(selected.Population.sum()),
                                       block_n=len(g), block_population=int(g.Population.sum()),
                                       block_mean_tract_easting_km=g.utm_x_m.mean()/1000,
                                       block_mean_tract_northing_km=g.utm_y_m.mean()/1000))
        fields = ["Redundancy_HHI", "Grid_Impact", "source_path_unconstrained_h", "source_path_added_4_h"]
        for group, g in frame.groupby("overlap_group"):
            for field in fields:
                profiles.append(dict(cohort=scope, overlap_group=group, field=field, n=len(g),
                                     population=int(g.Population.sum()), mean=g[field].mean(),
                                     median=g[field].median(), pop_mean=np.average(g[field], weights=g.Population),
                                     p25=g[field].quantile(.25), p75=g[field].quantile(.75)))
        # Only baseline-side network predictors enter this model. Source-path changes
        # are in the outcome by definition and are examined by component subtraction.
        models = {
            "prevalence": [],
            "baseline_rank_class": ["baseline_top"],
            "hhi": ["Redundancy_HHI"],
            "baseline_source_path": ["source_path_unconstrained_h"],
            "hhi_grid": ["Redundancy_HHI", "Grid_Impact"],
            "hhi_source_grid": ["Redundancy_HHI", "source_path_unconstrained_h", "Grid_Impact"],
            "hhi_source_grid_baseline_rank_class":
                ["Redundancy_HHI", "source_path_unconstrained_h", "Grid_Impact", "baseline_top"],
        }
        for scheme in SPATIAL:
            if frame[scheme].isna().any():
                continue
            for model, columns in models.items():
                predictions = pd.Series(index=frame.index, dtype=float)
                for block, test in frame.groupby(scheme):
                    train = frame.loc[frame[scheme].ne(block)]
                    prediction = np.full(len(test), train.added_top.mean())
                    if columns:
                        estimator = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
                        estimator.fit(train[columns], train.added_top)
                        prediction = estimator.predict_proba(test[columns])[:, 1]
                    predictions.loc[test.index] = prediction
                outcome = frame.added_top
                error = (predictions - outcome)**2
                cv.append(dict(cohort=scope, scheme=scheme, blocks=frame[scheme].nunique(),
                               model=model, n=len(frame), brier=error.mean(),
                               pop_brier=np.average(error, weights=frame.Population),
                               predicted_risk_gap=predictions[x].mean()-predictions[~x].mean(),
                               observed_risk_gap=outcome[x].mean()-outcome[~x].mean()))
    for name, rows in [("spatial_overlap_by_block", counts), ("overlap_feature_profiles", profiles),
                       ("spatial_predictive_diagnostics", cv)]:
        pd.DataFrame(rows).to_csv(destination / (name + ".csv"), index=False, lineterminator="\n")


def calculate(d, destination):
    correlations, strata, gaps, overlaps, overlap_quartiles = [], [], [], [], []
    for scope, f in [("all_2315", d), ("positive_2299", d.loc[d.Population.gt(0)])]:
        _, baseline_top, ensemble_top = top_overlap(f, B, M)
        for label, g in f.assign(overlap_group=overlap_label(baseline_top, ensemble_top)).groupby("overlap_group"):
            for q, qg in g.groupby(Q):
                overlap_quartiles.append(dict(cohort=scope, overlap_group=label, vulnerability_quartile=q,
                                              n=len(qg), population=int(qg.Population.sum())))
        for field in ADDED:
            correlations.append(dict(cohort=scope, added_field=field, n=len(f),
                                     population=int(f.Population.sum()), **associations(f, B, field)))
        groupings = [(Q, "frozen_vulnerability")]
        if scope == "positive_2299":
            groupings += [("community_id", "frozen_community_type")]
        for field in [B, *ADDED]:
            gaps.append(dict(cohort=scope, field=field, **qgap(f, field)))
            for by, label in groupings:
                for group, g in f.groupby(by):
                    strata.append(dict(cohort=scope, grouping=label, group=group,
                                       display_name=CLASS_NAME.get(group, group), field=field,
                                       **distribution(g, field)))
        comparisons = [("baseline_vs_added", B, field, .75) for field in ADDED]
        comparisons += [("ensemble_added_vs_policy_added", M, field, .75) for field in ADDED[1:]]
        comparisons += [("threshold_sensitivity", B, M, p) for p in [.70, .80]]
        comparisons += [
            ("four_policy_remove_source_from_added", B, "added_without_source_4_h", .75),
            ("four_policy_remove_source_from_baseline", "baseline_without_source_h",
             "MeanDelta_no_vulnerability", .75),
            ("four_policy_remove_source_from_both", "baseline_without_source_h", "added_without_source_4_h", .75),
        ]
        for label, x, y, p in comparisons:
            values, top_x, top_y = top_overlap(f, x, y, p)
            overlaps.append(dict(cohort=scope, comparison=label, baseline_field=x, added_field=y, **values))
            if label == "baseline_vs_added":
                d.loc[f.index, f"{scope}_top_{x}"] = top_x.to_numpy()
                d.loc[f.index, f"{scope}_top_{y}"] = top_y.to_numpy()
                if y == M:
                    d.loc[f.index, f"{scope}_overlap_group"] = overlap_label(top_x, top_y)
    for name, rows in [("associations", correlations), ("group_distributions", strata),
                       ("signed_vulnerability_gaps", gaps), ("top_quartile_overlap", overlaps),
                       ("overlap_by_vulnerability", overlap_quartiles)]:
        pd.DataFrame(rows).to_csv(destination / (name + ".csv"), index=False, lineterminator="\n")
    spatial_diagnostics(d, destination)
    d.to_csv(destination / "tract_metrics.csv", lineterminator="\n")


def plot(d, geometry, destination):
    plt.rcParams.update({"font.size": 10.5, "axes.spines.right": False, "axes.spines.top": False,
                         "axes.labelcolor": "#202a31", "text.color": "#202a31",
                         "axes.titleweight": "semibold", "font.family": "DejaVu Sans"})
    totals, x, y = top_overlap(d, B, M)
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.25), layout="constrained",
                           gridspec_kw={"width_ratios": [1.35, 1, 1]})
    density = ax[0].hexbin(d[B], d[M], gridsize=38, mincnt=1, cmap="Blues", bins="log",
                           linewidths=.15)
    ax[0].axvline(totals["baseline_cutoff_h"], color="#33434c", linewidth=.85, ls="--")
    ax[0].axhline(totals["added_cutoff_h"], color="#33434c", linewidth=.85, ls="--")
    ax[0].set(xlabel="Baseline deficit (h)", ylabel="Added deficit (h)")
    fig.colorbar(density, ax=ax[0], label="Tracts per bin", shrink=.89,
                 ticks=[1, 5, 10, 25], format=ScalarFormatter())
    ax[0].set_title("A   Tract-level association", loc="left")
    for panel, field, color, title in [(ax[1], B, COLORS["Baseline only"], "B   Baseline by vulnerability"),
                                       (ax[2], M, "#b36909", "C   Added by vulnerability")]:
        q = [distribution(d.loc[d[Q].eq(group)], field) for group in ["Q1", "Q2", "Q3", "Q4"]]
        for i, s in enumerate(q, start=1):
            panel.vlines(i, s["p10_h"], s["p90_h"], color=color, linewidth=1.1)
            panel.vlines(i, s["p25_h"], s["p75_h"], color=color, linewidth=5.5, alpha=.68)
            panel.scatter(i, s["median_h"], color="white", edgecolor=color, s=34, zorder=3)
            panel.scatter(i+.15, s["pop_mean_h"], color=color, marker="D", s=25, zorder=3)
        panel.set(xticks=range(1, 5), xticklabels=["Q1", "Q2", "Q3", "Q4"], xlim=(.65,4.5),
                  xlabel="Frozen vulnerability quartile", ylabel="Modeled deficit (h)")
        panel.set_title(title, loc="left")
        panel.grid(axis="y", alpha=.2)
    fig.savefig(destination / "association_and_vulnerability.png", dpi=240, facecolor="white")
    plt.close(fig)

    geo = geometry.assign(group=pd.Series(overlap_label(x, y), index=d.index))
    fig, ax = plt.subplots(figsize=(8.45, 7.8), layout="constrained")
    for group, color in COLORS.items():
        geo.loc[geo.group.eq(group)].plot(ax=ax, color=color, edgecolor="white", linewidth=.18)
    labels = [("Neither", "neither"), ("Baseline only", "baseline_only"), ("Added only", "added_only"),
              ("Both", "both")]
    ax.legend(handles=[Patch(facecolor=COLORS[group],
                             label=f"{group}  ·  {totals[key+'_n']:,} tracts") for group, key in labels],
              loc="upper right", frameon=False, fontsize=10)
    xmin, ymin, xmax, ymax = geo.total_bounds
    scale_x = xmin + (xmax-xmin)*.055
    scale_y = ymin + (ymax-ymin)*.024
    ax.plot([scale_x, scale_x+20000], [scale_y, scale_y], linewidth=1.4, color="#202a31")
    ax.annotate("20 km", (scale_x+10000, scale_y), xytext=(0, 6), textcoords="offset points",
                ha="center", fontsize=9)
    ax.annotate("N", xy=(.94,.19), xytext=(.94,.115), xycoords="axes fraction", ha="center",
                arrowprops={"arrowstyle": "-|>", "color": "#202a31", "lw": 1.1}, fontsize=9)
    ax.set_title("Where the highest baseline and added burdens overlap", loc="left", pad=10)
    ax.set_axis_off()
    fig.savefig(destination / "top_burden_overlap.png", dpi=240, facecolor="white")
    plt.close(fig)


def main():
    root = Path(__file__).resolve().parent
    repo = root.parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=root)
    parser.add_argument("--fetch", action="store_true", help="Fetch exact Git LFS objects into --cache.")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cache = args.cache or args.repo / ".source_lfs"
    paths, records = acquire(args.repo.resolve(), cache.resolve(), args.fetch)
    d, geometry, float_checks = read_data(paths, records)
    add_components(d, paths, records, float_checks)
    decimal_checks = exact_decimal_errors(paths)
    calculate(d, args.output)
    plot(d, geometry, args.output)
    result = dict(source_commit=REV, source_policy_count=5, status="PASS",
                  n_full=len(d), n_positive=int(d.Population.gt(0).sum()),
                  population=int(d.Population.sum()), frozen_sovi_counts=d[Q].value_counts().to_dict(),
                  zero_population_by_sovi=d.loc[d.Population.eq(0), Q].value_counts().to_dict(),
                  feature_join_missing_used_fields=0,
                  main_numeric_comparison_max_abs_error=float_checks,
                  stored_decimal_max_abs_error_h=decimal_checks, inputs=records)
    (args.output / "source_qa.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: verified {len(paths)} payloads and {len(d)} GEOIDs")


if __name__ == "__main__":
    main()
