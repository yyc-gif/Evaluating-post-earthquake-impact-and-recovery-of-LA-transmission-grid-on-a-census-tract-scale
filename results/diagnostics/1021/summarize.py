"""Tabulate registered outputs and make separate exploratory diagnostic artwork."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from preflight import AUTH, HERE

OUT = HERE / "outputs"
TITLE = "1021 EXPLORATORY VALIDATION - NOT FORMAL STAGE 7"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "axes.titlesize": 9, "axes.labelsize": 8,
                     "pdf.fonttype": 42, "ps.fonttype": 42})


def read(name):
    return pd.read_csv(OUT / (name+".csv"))


def dist_summary(frame, groups, value):
    return frame.groupby(groups)[value].agg(mean="mean", median="median", sd="std",
                                           p10=lambda s: s.quantile(.1), p90=lambda s: s.quantile(.9),
                                           minimum="min", maximum="max", valid="count", total="size").reset_index()


def save(fig, name):
    fig.suptitle(TITLE, fontsize=9, y=.99)
    fig.tight_layout(rect=[0, 0, 1, .965], h_pad=2.2, w_pad=2)
    fig.savefig(HERE / (name+".pdf"), metadata={"Title": name, "Author": "1021 independent validation"})
    fig.savefig(HERE / (name+".png"), dpi=300)
    plt.close(fig)


def main():
    ps = read("PREDICTION_STRENGTH_REPETITIONS")
    # Preserve undefined directions: their split cannot become defined by averaging.
    splits = ps.groupby(["design", "repeat", "k"]).strength.agg(
        lambda s: s.mean() if s.notna().all() else np.nan).reset_index()
    splits.to_csv(OUT / "PREDICTION_STRENGTH_BIDIRECTIONAL.csv", index=False)
    pss = dist_summary(splits, ["design", "k"], "strength")
    pss.to_csv(OUT / "PREDICTION_STRENGTH_SUMMARY.csv", index=False)
    boot = read("BOOTSTRAP_CLUSTER_STABILITY")
    bs = dist_summary(boot, ["support", "k", "cluster"], "jaccard")
    rates = boot.groupby(["support", "k", "cluster"])[["dissolved_J_lt_0_5", "recovered_J_ge_0_75"]].mean().reset_index()
    bs = bs.merge(rates, on=["support", "k", "cluster"])
    bs.to_csv(OUT / "BOOTSTRAP_CLUSTER_SUMMARY.csv", index=False)
    obs = read("OBSERVED_INDICES")
    ob = obs.groupby("k").agg(inertia=("inertia", "min"), mean_silhouette=("silhouette", "mean"),
                              mean_CH=("CH", "mean"), mean_DB=("DB", "mean"),
                              mean_negative_fraction=("negative_fraction", "mean")).reset_index()
    ob["relative_WCSS_step_reduction"] = -ob.inertia.diff()/ob.inertia.shift()
    ob["normalized_WCSS_reduction"] = 1-ob.inertia/ob.inertia.iloc[0]
    ob.to_csv(OUT / "CONVENTIONAL_INDEX_SUMMARY.csv", index=False)
    gap = read("GAP_SUMMARY")
    spatial = read("SPATIAL_LEAVE_QUADRANT_OUT")
    ward = read("WARD_COMPARISONS").groupby("k").first().reset_index()
    seed = read("SEED_STABILITY").groupby("k").ARI.min().reset_index()
    prior = read("PRIOR_POLICY_SET_STABILITY")
    print("Prediction strength\n", pss.to_string(index=False))
    print("Conventional indices\n", ob.to_string(index=False))
    print("Bootstrap\n", bs[bs.support == "unique_inbag"].to_string(index=False))
    print("Spatial leave-out\n", spatial.groupby("k").held_out_ARI.agg(["min", "median", "max"]).to_string())
    print("Ward\n", ward[["k", "ARI", "rare_jaccard"]].to_string(index=False))
    print("Prior policy columns", list(prior.columns))
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 7.0))
    ax = axs[0, 0]
    for (name, g), color in zip(gap.groupby("reference"), ["#147f98", "#b35a32"]):
        ax.errorbar(g.k, g.gap, yerr=g.s_1SE_rule, marker="o", ms=3, color=color,
                    label=name.replace("_", " "), capsize=2)
    ax.set(title="A. Gap statistic", xlabel="K", ylabel="Gap (bars: 1SE-rule spread)")
    ax.legend(fontsize=7)
    ax = axs[0, 1]
    for (name, g), color in zip(pss.groupby("design"), ["#147f98", "#b35a32"]):
        ax.plot(g.k, g["mean"], "o-", ms=3, label=name.replace("_", " "), color=color)
        ax.fill_between(g.k, g.p10, g.p90, color=color, alpha=.13)
    ax.axhline(.8, color="#555555", linestyle="--", lw=.8)
    ax.axhline(.9, color="#999999", linestyle=":", lw=.8)
    ax.set(title="B. Prediction strength", xlabel="K", ylabel="Minimum pair agreement", ylim=(0, 1.03))
    ax.legend(fontsize=7)
    ax = axs[1, 0]
    ax.plot(ob.k[1:], ob.mean_silhouette[1:], "o-", color="#147f98", ms=4)
    ax.set(title="C. Full-cohort silhouette", xlabel="K", ylabel="Mean silhouette")
    ax = axs[1, 1]
    ax.plot(ob.k, ob.inertia/ob.inertia.iloc[0], "o-", color="#7a5899", ms=4)
    ax.set(title="D. Within-cluster dispersion", xlabel="K", ylabel="WCSS / K1 WCSS", ylim=(0, 1.04))
    for ax in axs.flat:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#eeeeee")
    save(fig, "01_RESOLUTION_EVIDENCE")

    fig, axs = plt.subplots(2, 2, figsize=(7.2, 7.0))
    ax = axs[0, 0]
    b = bs[bs.support == "unique_inbag"]
    for (k, g), color in zip(b.groupby("k"), ["#147f98", "#b35a32", "#4b7c42", "#a34857", "#7a5899"]):
        offsets = np.linspace(-.18, .18, len(g))
        ax.vlines(k+offsets, g.p10, g.p90, lw=1, color=color)
        ax.plot(k+offsets, g["mean"], "o", ms=3, label=f"K{k}", color=color)
    ax.axhline(.75, color="#555555", ls="--", lw=.8)
    ax.set(title="A. Cluster-wise bootstrap Jaccard", xlabel="K (one point per class)",
           ylabel="Mean; P10-P90", ylim=(0, 1.04), xticks=range(2, 7))
    ax = axs[0, 1]
    for k, g in spatial.groupby("k"):
        ax.scatter(k+np.linspace(-.12, .12, len(g)), g.held_out_ARI, s=22, color="#147f98")
    ax.set(title="B. Leave-quadrant-out sensitivity", xlabel="K", ylabel="Held-out ARI", ylim=(0, 1.04), xticks=range(2, 7))
    ax = axs[1, 0]
    ax.plot(ward.k, ward.ARI, "o-", color="#b35a32", label="Ward vs K-means", ms=3)
    ax.plot(seed.k[1:], seed.ARI[1:], "s--", color="#147f98", label="Minimum seed-pair ARI", ms=3)
    ax.set(title="C. Algorithm and initialization", xlabel="K", ylabel="ARI", ylim=(0, 1.04))
    ax.legend(fontsize=7)
    ax = axs[1, 1]
    rare_boot = boot[boot.support == "unique_inbag"].drop_duplicates(["repeat", "k"])
    rr = rare_boot.groupby("k").rare_jaccard.agg(["mean", "min", "max"]).reset_index()
    projected = read("INIT_COORDINATE_PROJECTION").groupby("k").rare_jaccard.mean().reset_index()
    ax.plot(rr.k, rr["mean"], "o-", label="Bootstrap full-support match", color="#147f98", ms=3)
    ax.fill_between(rr.k, rr["min"], rr["max"], alpha=.13, color="#147f98")
    ax.plot(projected.k, projected.rare_jaccard, "s--", label="Init omitted (no redistribution)", color="#b35a32", ms=3)
    ax.set(title="D. Historical 37-tract set", xlabel="K", ylabel="Best-set Jaccard", ylim=(0, 1.04), xticks=range(2, 7))
    ax.legend(fontsize=7)
    for ax in axs.flat:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#eeeeee")
    save(fig, "02_REPRODUCIBILITY_AND_SENSITIVITY")

    a = np.load(AUTH / "preprocessing_and_labels.npz", allow_pickle=False)
    data = np.load(OUT / "ALL_FITTED_ARRAYS.npz", allow_pickle=False)
    cohort = pd.read_csv(AUTH / "tract_features.csv", dtype={"tract_id": str})
    cohort.loc[data["historical_rare37_mask"]].to_csv(OUT / "HISTORICAL_K4_37_TRACTS.csv", index=False)
    refs = obs.sort_values(["inertia", "seed"]).groupby("k").head(1).sort_values("k")
    refs[["k", "seed", "inertia"]].to_csv(OUT / "REFERENCE_FIT_REGISTRY.csv", index=False)
    weakest = []
    pairs = read("PREDICTION_STRENGTH_CLUSTER_PAIRS")
    rare = data["historical_rare37_mask"]
    for row in ps.itertuples():
        prefix = f"ps_{row.design}_r{row.repeat}_k{row.k}_d{row.direction}"
        valid = data[f"split_{row.design}_r{row.repeat}_half{1-row.direction}"]
        train = data[f"split_{row.design}_r{row.repeat}_half{row.direction}"]
        cl = pairs[(pairs.design == row.design) & (pairs.repeat == row.repeat)
                   & (pairs.k == row.k) & (pairs.direction == row.direction)].sort_values("strength").iloc[0]
        mask = data[prefix+"_actual"] == int(cl.cluster)
        weakest.append({"design": row.design, "repeat": row.repeat, "k": row.k, "direction": row.direction,
                        "minimum_strength": row.strength, "weakest_class_size": int(mask.sum()),
                        "weakest_class_rare37_fraction": float(rare[valid][mask].mean()),
                        "rare37_training_n": int(rare[train].sum()), "rare37_validation_n": int(rare[valid].sum())})
    pd.DataFrame(weakest).to_csv(OUT / "PREDICTION_STRENGTH_WEAK_LINKS.csv", index=False)
    features = ["Grid_Impact", "B_Unconstrained", "MeanDelta", "SOVI_SCORE"]
    display_names = ["Spectral impact", "Baseline deficit", "Constraint increment", "Social vulnerability"]
    fig, axs = plt.subplots(2, 4, figsize=(7.2, 5.0))
    colors = ["#147f98", "#b35a32", "#7a5899", "#4b7c42"]
    for row, k in enumerate([3, 4]):
        chosen = obs[obs.k == k].sort_values(["inertia", "seed"]).iloc[0]
        labels = data[f"full_k{k}_s{int(chosen.seed)}_labels"]
        for col, name in enumerate(features):
            ax = axs[row, col]
            j = list(a["feature_names"]).index(name)
            for c in range(k):
                values = np.sort(a["raw"][labels == c, j])
                ax.step(values, np.arange(1, len(values)+1)/len(values), where="post", lw=1,
                        color=colors[c], label=f"{c+1} (n={len(values)})")
            ax.set(title=f"K{k}\n{display_names[col]}", ylabel="ECDF" if col == 0 else "")
            if name in ("B_Unconstrained", "MeanDelta"):
                ax.set_xlabel("Deficit hours")
            ax.spines[["top", "right"]].set_visible(False)
            if col == 0:
                ax.legend(fontsize=7)
    save(fig, "03_WITHIN_CLASS_OVERLAP")

    choices = {}
    for design, group in pss.groupby("design"):
        choices[design] = {}
        for threshold in [.8, .9]:
            g = group[(group["mean"] >= threshold) & (group.valid == group.total)]
            choices[design][str(threshold)] = int(g.k.max()) if len(g) else None
    summary = {"prediction_strength_convention_K": choices,
               "silhouette_maximum_K": int(ob.loc[ob.mean_silhouette.idxmax(), "k"]),
               "CH_maximum_K": int(ob.loc[ob.mean_CH.idxmax(), "k"]),
               "DB_minimum_K": int(ob.loc[ob.mean_DB.idxmin(), "k"]),
               "no_automatic_scientific_selection": True}
    (OUT / "METHOD_SUMMARY.json").write_text(json.dumps(summary, indent=2)+"\n", newline="\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
