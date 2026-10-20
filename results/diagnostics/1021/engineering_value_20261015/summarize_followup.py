"""Summaries and only the figures needed to judge engineering utility."""
from itertools import combinations
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import *

plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                     "pdf.fonttype": 42, "font.family": "DejaVu Sans"})


def read(name):
    return pd.read_csv(HERE/(name+".csv"), dtype={"tract_id": str})


def summary(frame, groups, value):
    return frame.groupby(groups)[value].agg(mean="mean", median="median", minimum="min", maximum="max",
                                           p10=lambda s:s.quantile(.1), p90=lambda s:s.quantile(.9),
                                           n="count").reset_index()


def emit(fig, name):
    fig.suptitle("1021 ENGINEERING VALUE - EXPLORATORY, NOT PUBLICATION ARTWORK", fontsize=9, y=.99)
    fig.tight_layout(rect=(0, 0, 1, .96), h_pad=2, w_pad=2)
    fig.savefig(HERE/(name+".pdf"), metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(HERE/(name+".png"), dpi=300)
    plt.close(fig)


def main():
    scores = read("HELD_OUT_OUTCOME_SCORES")
    pivot = scores.pivot(index=["percent", "repeat", "outcome"], columns="method", values="MAE")
    pairs = [("K3", "K2"), ("K4", "K3")]
    pairs += [("K3", s) for s in ["Q3_baseline_deficit", "Q3_constraint_increment", "Q3_SOVI", "Q3_mean_total_deficit", "OLS_seven", "additive_seven"]]
    contrasts = []
    for candidate, comparison in pairs:
        result = (pivot[comparison]-pivot[candidate]).rename("MAE_improvement").reset_index()
        result["candidate"], result["comparison"] = candidate, comparison
        result["notable_MAE_margin"] = result.outcome.map(mae_margin)
        result["notable_improvement"] = result.MAE_improvement >= result.notable_MAE_margin
        contrasts.append(result)
    contrasts = pd.concat(contrasts, ignore_index=True)
    save("PAIRED_MAE_COMPARISONS.csv", contrasts)
    groups = ["percent", "outcome", "candidate", "comparison"]
    cs = summary(contrasts, groups, "MAE_improvement")
    cs = cs.merge(contrasts.groupby(groups).notable_improvement.mean().rename("fraction_notably_improved").reset_index(), on=groups)
    save("PAIRED_MAE_COMPARISON_SUMMARY.csv", cs)
    save("HELD_OUT_SCORE_SUMMARY.csv", summary(scores, ["percent", "method", "outcome"], "MAE"))
    memberships = read("SUBSAMPLING_MEMBERSHIP")
    save("MEMBERSHIP_STABILITY_SUMMARY.csv", summary(memberships, ["percent", "k"], "full_ARI"))
    js = read("SUBSAMPLING_CLASS_JACCARD")
    save("CLASS_JACCARD_SUMMARY.csv", summary(js, ["percent", "k", "cluster", "support"], "Jaccard"))
    changes = read("SUBSAMPLING_RECOVERY_PROFILE_CHANGES")
    ps = summary(changes, ["percent", "k", "cluster", "outcome"], "mean_change")
    ps = ps.merge(changes.groupby(["percent", "k", "cluster", "outcome"]).within_registered_profile_tolerance.mean().rename("profile_tolerance_fraction").reset_index())
    save("RECOVERY_PROFILE_STABILITY_SUMMARY.csv", ps)
    con = read("SUBSAMPLING_ENGINEERING_CONTRAST_PERSISTENCE")
    effects = con.groupby(["percent", "k", "a", "b", "outcome"]).agg(
        reference_difference=("reference_difference", "first"),
        fraction_same_sign_and_meaningful=("same_sign_and_meaningful", "mean"),
        mean_difference=("resample_difference", "mean"), p10=("resample_difference", lambda s:s.quantile(.1)),
        p90=("resample_difference", lambda s:s.quantile(.9))).reset_index()
    effects["reference_meaningful"] = effects.apply(lambda r: abs(r.reference_difference) >= meaningful(r.outcome), axis=1)
    save("ENGINEERING_CONTRAST_PERSISTENCE_SUMMARY.csv", effects)
    cores = read("TRACT_MEMBERSHIP_CORE_FREQUENCIES")
    core_summary = []
    for (k, c), block in cores.groupby(["k", "reference_class"]):
        for design, field in [("pooled_all", "pooled_same_class_frequency"),
                              ("70_all", "p70_same_class_frequency"), ("85_all", "p85_same_class_frequency"),
                              ("70_held_out", "p70_held_out_same_class_frequency"), ("85_held_out", "p85_held_out_same_class_frequency")]:
            mask = block[field] >= .9
            core_summary.append({"k": k, "cluster": c, "design": design, "tracts": len(block),
                                 "core_tracts": int(mask.sum()), "core_fraction": mask.mean(),
                                 "core_population": int(block.Population[mask].sum()),
                                 "mean_same_class_frequency": block[field].mean()})
    save("STABLE_CORE_SUMMARY.csv", core_summary)
    outcomes = read("UNFITTED_TRACT_OUTCOMES")
    core_profiles = []
    for (k, c), block in cores.groupby(["k", "reference_class"]):
        mask = block.stable_core_ge_0_9
        subset = outcomes.set_index("tract_id").loc[block.tract_id[mask]]
        for name in outcomes.columns[1:]:
            core_profiles.append({"k": k, "cluster": c, "core_tracts": len(subset), "outcome": name,
                                  "core_mean": subset[name].mean()})
    save("STABLE_CORE_OUTCOME_PROFILES.csv", core_profiles)
    _, _, ref_labels = inputs()
    rare = ref_labels[4] == 0
    overlap = []
    for (k, c), block in cores.groupby(["k", "reference_class"]):
        indices = pd.Index(outcomes.tract_id).get_indexer(block.tract_id)
        mask = block.stable_core_ge_0_9.to_numpy()
        overlap.append({"k": k, "cluster": c, "core_tracts": int(mask.sum()),
                        "core_in_historical_rare37": int(rare[indices][mask].sum()),
                        "historical_rare37_total": 37})
    save("CORE_SOURCE_PROXY_OVERLAP.csv", overlap)

    primary = ["random__B480_mean", "impact__T80_reached_p50"]
    reference = read("REFERENCE_OUTCOME_PROFILES")
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 6.6))
    chart_outcomes = primary+["2pc50__C29_D1__impact-first__B480_mean", "Northridge__C57_D1__impact-first__B480_mean"]
    titles = ["A. Excluded Random priority", "B. Time to 80% service", "C. Fewer crews (29)", "D. Northridge scenario"]
    for ax, name, title in zip(axs.flat, chart_outcomes, titles):
        sub = reference[reference.outcome == name]
        for (k, g), color in zip(sub.groupby("k"), ["#147f98", "#b35a32", "#7a5899"]):
            offsets = np.linspace(-.2, .2, len(g))
            ax.vlines(k+offsets, g.p10, g.p90, color=color, lw=1)
            ax.scatter(k+offsets, g["mean"], color=color, s=22)
            for xx, row in zip(k+offsets, g.itertuples()):
                ax.annotate(str(row.cluster+1), (xx, row.mean), xytext=(3,3), textcoords="offset points", fontsize=7, color=color)
        ax.set(title=title, xlabel="K (one point per class)", xticks=[2,3,4],
               ylabel="Tract-median recovery time (h)" if "T80" in name else "Equivalent deficit hours")
        ax.spines[["top", "right"]].set_visible(False)
    emit(fig, "01_UNFITTED_ENGINEERING_PROFILES")

    fig, axs = plt.subplots(1, 2, figsize=(7.2, 5.1))
    methods = ["K2", "Q3_baseline_deficit", "Q3_constraint_increment", "Q3_SOVI", "Q3_mean_total_deficit", "OLS_seven", "additive_seven"]
    labels = ["K2", "Baseline-deficit thirds", "Constraint-increment thirds", "SOVI thirds", "Total-deficit thirds", "Seven-input linear", "Seven-input additive"]
    for ax, name, title in zip(axs, primary, ["A. Random-policy deficit", "B. Time to 80% service"]):
        for percent, color, offset in [(70, "#147f98", -.1), (85, "#b35a32", .1)]:
            g = cs[(cs.outcome == name) & (cs.candidate == "K3") & (cs.percent == percent)].set_index("comparison").loc[methods]
            ys = np.arange(len(methods))+offset
            ax.hlines(ys, g.p10, g.p90, color=color, lw=1)
            ax.scatter(g["mean"], ys, c=color, s=19, label=f"{percent}% sample")
        ax.axvline(0, color="#555555", lw=.8)
        ax.axvline(mae_margin(name), color="#888888", lw=.8, ls="--")
        ax.set(title=title, xlabel="Benchmark MAE minus K3 MAE (h)", yticks=np.arange(len(methods)),
               yticklabels=labels if ax is axs[0] else [""]*len(labels))
        ax.invert_yaxis()
        ax.spines[["top", "right"]].set_visible(False)
    axs[0].legend(fontsize=7, loc="upper left")
    emit(fig, "02_HELD_OUT_ENGINEERING_VALUE")

    fig, axs = plt.subplots(1, 2, figsize=(7.2, 4.2))
    for percent, color, offset in [(70, "#147f98", -.07), (85, "#b35a32", .07)]:
        ms = summary(memberships[memberships.percent == percent], ["k"], "full_ARI")
        axs[0].vlines(ms.k+offset, ms.p10, ms.p90, color=color)
        axs[0].scatter(ms.k+offset, ms["mean"], color=color, label=f"{percent}% sample", s=22)
        cc = pd.DataFrame(core_summary)
        cc = cc[cc.design == f"{percent}_held_out"]
        for k, g in cc.groupby("k"):
            axs[1].scatter(k+np.linspace(-.2, .2, len(g))+offset, g.core_fraction, s=22, color=color)
    axs[0].set(title="A. Membership reproducibility", ylabel="All-tract ARI (mean; P10-P90)", xlabel="K", xticks=[2,3,4], ylim=(0,1.03))
    axs[1].set(title="B. Stable held-out membership cores", ylabel="Fraction of reference class", xlabel="K (one point per class)", xticks=[2,3,4], ylim=(-.03,1.03))
    axs[0].legend(fontsize=7)
    for ax in axs:
        ax.spines[["top", "right"]].set_visible(False)
    emit(fig, "03_MEMBERSHIP_CORES_AND_SUBSAMPLING")
    print(cs[cs.outcome.isin(primary+[chart_outcomes[2]])][["percent","outcome","candidate","comparison","mean","fraction_notably_improved"]].to_string(index=False))


if __name__ == "__main__":
    main()
