"""Recompute matched deficit and equal-size screening results from frozen inputs."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, StrMethodFormatter
import numpy as np
import pandas as pd

DEST = Path(__file__).resolve().parent
sys.path.insert(0, str(DEST.parent))
import analyze as frozen

B, M, T = frozen.B, frozen.M, frozen.T
POLICIES = frozen.POLICY
DELTAS = ["Delta_" + p for p in POLICIES]
TARGETS = [(M, T)] + [(delta, "B_" + policy) for delta, policy in zip(DELTAS, POLICIES)]
LABELS = dict(zip([M, *DELTAS],
                  ["Five-priority mean", "Impact first", "Hospital first", "Degree first",
                   "Betweenness first", "Vulnerability first"]))
PRIOR = DEST.parent / "tract_metrics.csv"
BASE = "baseline"
MATCHED = "matched_total"
FIXED = "five_priority_mean_total"


def save_table(output, name, data):
    pd.DataFrame(data).to_csv(output / (name + ".csv"), index=False, lineterminator="\n")


def cohorts(d):
    return [("all_2315", d), ("positive_2299", d.loc[d.Population.gt(0)])]


def covariance(x, y, w):
    return float(np.average((x - np.average(x, weights=w)) *
                            (y - np.average(y, weights=w)), weights=w))


def moments(x, y, w):
    vx, vy = covariance(x, x, w), covariance(y, y, w)
    cov = covariance(x, y, w)
    return dict(covariance_h2=cov, baseline_sd_h=np.sqrt(vx), added_sd_h=np.sqrt(vy),
                pearson=cov / np.sqrt(vx * vy))


def strategy_covariances(d):
    components, combinations = [], []
    for scope, frame in cohorts(d):
        x, saved = frame[B].to_numpy(), frame[M].to_numpy()
        for weighting, w in [("equal_tract", np.ones(len(frame))),
                             ("population", frame.Population.to_numpy())]:
            common = dict(cohort=scope, weighting=weighting, n=len(frame),
                          residents=int(frame.Population.sum()))
            estimates = [moments(x, frame[delta].to_numpy(), w) for delta in DELTAS]
            for delta, estimate in zip(DELTAS, estimates):
                components.append(dict(**common, policy=delta.removeprefix("Delta_"), **estimate,
                                       contribution_to_five_mean_covariance_h2=estimate["covariance_h2"]/5))
            for omitted in [None, *range(len(POLICIES))]:
                keep = [j for j in range(len(POLICIES)) if j != omitted]
                added = frame[[DELTAS[j] for j in keep]].mean(axis=1).to_numpy()
                if omitted is None:
                    np.testing.assert_allclose(saved, added, atol=1e-12, rtol=0)
                    added = saved
                estimate = moments(x, added, w)
                terms = np.array([estimates[j]["covariance_h2"] for j in keep]) / len(keep)
                positives, negatives = terms[terms > 0].sum(), terms[terms < 0].sum()
                residual = estimate["covariance_h2"] - terms.sum()
                frozen.check(abs(residual) <= 1e-12, "Covariance identity failed")
                combinations.append(dict(**common, omitted="none" if omitted is None else POLICIES[omitted],
                                         policies=len(keep), **estimate,
                                         positive_covariance_terms_h2=positives,
                                         negative_covariance_terms_h2=negatives,
                                         sum_policy_covariance_terms_h2=terms.sum(),
                                         covariance_identity_residual_h2=residual,
                                         cancellation_fraction=1-abs(terms.sum())/abs(terms).sum()))
    return pd.DataFrame(components), pd.DataFrame(combinations)


def top_list(frame, field, size, p):
    # Frames are already sorted by GEOID. A stable descending sort uses that order for ties.
    scores = frame[field]
    order = scores.sort_values(ascending=False, kind="stable")
    cutoff = order.iloc[size-1]
    selected = frame.index.isin(order.index[:size])
    inclusive_cutoff = scores.quantile(p / 100)
    inclusive = scores.ge(inclusive_cutoff).to_numpy()
    return selected, dict(rank_cutoff_h=cutoff, tied_at_rank_cutoff=int(scores.eq(cutoff).sum()),
                          tied_excluded=int((scores.eq(cutoff) & ~selected).sum()),
                          inclusive_percentile_cutoff_h=inclusive_cutoff,
                          inclusive_percentile_n=int(inclusive.sum()),
                          inclusive_percentile_matches_exact_list=bool(np.array_equal(inclusive, selected)))


def coverage(frame, p):
    size = (len(frame) * (100 - p) + 99) // 100
    population = frame.Population.to_numpy()
    lists = {col: top_list(frame, col, size, p) for col in [B, M, T, *DELTAS, *[t for _, t in TARGETS[1:]]]}
    for outcome, matched in TARGETS:
        target, target_stats = lists[outcome]
        candidates = [(BASE, B), (MATCHED, matched)]
        if outcome != M:
            candidates.append((FIXED, T))
        for label, measure in candidates:
            selected, screen_stats = lists[measure]
            intersection = target & selected
            missed = target & ~selected
            found, found_pop = int(intersection.sum()), int(population[intersection].sum())
            target_pop = int(population[target].sum())
            yield dict(target=outcome, screen=label, screen_field=measure,
                       n=len(frame), residents=int(population.sum()), percentile=p,
                       nominal_screen_fraction=(100-p)/100, screen_size=size, target_size=size,
                       target_residents=target_pop, screen_residents=int(population[selected].sum()),
                       covered_tracts=found, tract_coverage=found/size, covered_residents=found_pop,
                       resident_coverage=found_pop/target_pop, missed_tracts=int(missed.sum()),
                       missed_residents=int(population[missed].sum()),
                       **{"target_"+k: v for k, v in target_stats.items()},
                       **{"screen_"+k: v for k, v in screen_stats.items()})


def sensitivity(d):
    point, spatial = [], []
    for cohort, frame in cohorts(d):
        for percentile in [70, 75, 80]:
            point.extend(dict(cohort=cohort, **row) for row in coverage(frame, percentile))
        for scheme in frozen.SPATIAL:
            if frame[scheme].isna().any():
                continue
            for block in sorted(frame[scheme].unique()):
                keep = frame.loc[frame[scheme].ne(block)]
                spatial.extend(dict(cohort=cohort, scheme=scheme, omitted_block=block,
                                    omitted_n=len(frame)-len(keep),
                                    omitted_residents=int(frame.Population.sum()-keep.Population.sum()),
                                    **row) for row in coverage(keep, 75))
    spatial = pd.DataFrame(spatial)
    rows = []
    for (cohort, scheme, target), g in spatial.groupby(["cohort", "scheme", "target"], sort=False):
        lookup = g.set_index(["screen", "omitted_block"])
        a = lookup.loc[BASE]
        for comparator in g.screen.unique():
            if comparator == BASE:
                continue
            b = lookup.loc[comparator].reindex(a.index)
            coverage_change = (b.tract_coverage - a.tract_coverage) * 100
            fewer_residents = a.missed_residents - b.missed_residents
            rows.append(dict(cohort=cohort, scheme=scheme, target=target, comparator=comparator,
                             leaveouts=len(a), baseline_coverage_min=a.tract_coverage.min(),
                             baseline_coverage_max=a.tract_coverage.max(),
                             total_coverage_min=b.tract_coverage.min(),
                             total_coverage_max=b.tract_coverage.max(),
                             coverage_change_pp_min=coverage_change.min(),
                             coverage_change_pp_max=coverage_change.max(),
                             fewer_missed_residents_min=fewer_residents.min(),
                             fewer_missed_residents_max=fewer_residents.max(),
                             count_higher_tract_coverage=int((coverage_change > 0).sum()),
                             count_fewer_missed_residents=int((fewer_residents > 0).sum())))
    return pd.DataFrame(point), spatial, pd.DataFrame(rows)


def verify(d, cov, screens, cache_records, numeric_checks, decimal_checks, prior):
    # Prior rows are a cross-check after the independent rebuild, never an input to it.
    expected = frozen.indexed(frozen.read_table(prior), "previous derived table", d.index)
    check_fields = [B, M, T, *DELTAS, *[col for _, col in TARGETS[1:]]]
    prior_errors = {}
    for field in check_fields:
        frozen.close(d[field], expected[field], field, prior_errors)
    frozen.check(d[frozen.Q].equals(expected[frozen.Q]), "Frozen quartiles differ from prior delivery")
    frozen.check(d.Population.equals(expected.Population), "Population differs from prior delivery")
    rows = cov.loc[cov.cohort.eq("all_2315") & cov.weighting.eq("equal_tract")].set_index("omitted")
    headline = screens.query("cohort == 'all_2315' and percentile == 75 and target == @M").set_index("screen")
    ref = {"pearson_five_priority_mean": 0.0269727566, "pearson_omit_degree_first": -0.1621060285,
           "target_size": 579, "baseline_covered_tracts": 212, "baseline_missed_residents": 1432501,
           "total_covered_tracts": 334, "total_missed_residents": 963079}
    observed = dict(pearson_five_priority_mean=float(rows.loc["none", "pearson"]),
                    pearson_omit_degree_first=float(rows.loc["degree-first", "pearson"]),
                    target_size=int(headline.loc[BASE, "target_size"]),
                    baseline_covered_tracts=int(headline.loc[BASE, "covered_tracts"]),
                    baseline_missed_residents=int(headline.loc[BASE, "missed_residents"]),
                    total_covered_tracts=int(headline.loc[MATCHED, "covered_tracts"]),
                    total_missed_residents=int(headline.loc[MATCHED, "missed_residents"]))
    for name, expected_value in ref.items():
        frozen.check(abs(observed[name] - expected_value) <= 5.1e-11,
                     f"Independent reference mismatch for {name}: {observed[name]}")
    return dict(status="PASS", frozen_source_commit=frozen.REV, source_lfs_inputs=cache_records,
                n_full=len(d), n_positive=int(d.Population.gt(0).sum()), residents=int(d.Population.sum()),
                frozen_input_numeric_qa=numeric_checks, decimal_identity_qa=decimal_checks,
                prior_csv_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
                prior_max_abs_differences_h=prior_errors, reference=ref, regenerated=observed,
                max_absolute_covariance_identity_residual_h2=cov.covariance_identity_residual_h2.abs().max())


def plot(screens, output):
    data = screens.query("cohort == 'all_2315' and percentile == 75 and screen in [@BASE, @MATCHED]")
    fig, (left, right) = plt.subplots(1, 2, figsize=(10.1, 4.65), layout="constrained",
                                     gridspec_kw={"width_ratios": [1, 1.05]}, sharey=True)
    labels = [LABELS[outcome] for outcome, _ in TARGETS]
    lines = np.arange(len(labels))
    styles = [(BASE, "Baseline deficit", "#226692", "o", -.145),
              (MATCHED, "Total deficit", "#a65511", "D", .145)]
    for field, label, color, marker, shift in styles:
        s = data.loc[data.screen.eq(field)].set_index("target").loc[list(LABELS)]
        left.scatter(s.tract_coverage*100, lines+shift, s=36, c=color, marker=marker, label=label, zorder=3)
        right.scatter(s.missed_residents/1e6, lines+shift, s=36, c=color, marker=marker, zorder=3)
    n = int(data.target_size.iloc[0])
    left.set(yticks=lines, yticklabels=labels, xlim=(0, 100),
             xlabel=f"Share of the {n} target tracts found")
    left.xaxis.set_major_formatter(PercentFormatter(xmax=100, decimals=0))
    right.set(xlabel="Residents in missed tracts (millions)", xlim=(0, 2),
              xticks=[0, .5, 1, 1.5, 2])
    right.xaxis.set_major_formatter(StrMethodFormatter("{x:.1f}"))
    left.set_title("A   Tract coverage", loc="left", fontsize=12, weight="semibold")
    right.set_title("B   Residents omitted", loc="left", fontsize=12, weight="semibold")
    left.invert_yaxis()
    for ax in (left, right):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", linewidth=.65, alpha=.4)
        ax.axhline(.5, color="#b7b9bd", linewidth=.8)
    left.legend(loc="upper left", bbox_to_anchor=(0, -.13), ncol=2, frameon=False)
    fig.savefig(output / "screening_coverage.png", dpi=220, facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=DEST.parents[3])
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEST)
    parser.add_argument("--prior", type=Path, default=PRIOR)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    cache = args.cache or args.repo / ".git" / "frozen_source_lfs"
    paths, records = frozen.acquire(args.repo.resolve(), cache.resolve(), args.fetch)
    d, _, numeric_checks = frozen.read_data(paths, records)
    decimal_checks = frozen.exact_decimal_errors(paths)
    components, combinations = strategy_covariances(d)
    screens, spatial, spatial_summary = sensitivity(d)
    qc = verify(d, combinations, screens, records, numeric_checks, decimal_checks, args.prior)
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, table in [("covariance_by_policy", components), ("covariance_leave_one_policy_out", combinations),
                            ("screening_coverage", screens), ("screening_leave_block_out", spatial),
                            ("screening_spatial_summary", spatial_summary)]:
        save_table(args.output, filename, table)
    (args.output / "quantitative_qa.json").write_text(json.dumps(qc, indent=2) + "\n",
                                                     encoding="utf-8", newline="\n")
    plot(screens, args.output)
    print("PASS: nine frozen input hashes, cohort joins, covariance identities and independent references")


if __name__ == "__main__":
    main()
