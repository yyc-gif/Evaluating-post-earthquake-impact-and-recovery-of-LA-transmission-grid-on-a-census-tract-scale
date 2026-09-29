"""Render the closed SCE-supported planning-capacity sensitivity.

This is presentation-only.  It reads the frozen closure summary and supported
station table and never re-runs damage, scheduling, source-gate, or capacity
post-processing.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import la_grid.plotting.Project_Visualizer as july
from la_grid.paths import REPO_ROOT as ROOT

RESULTS = ROOT / "results" / "capacity"
OUT = ROOT / "results" / "figures"
SUMMARY = RESULTS / "SCE_CAPACITY_SENSITIVITY_SUMMARY.csv"
SUPPORTED = RESULTS / "SCE_CAPACITY_SUPPORTED_STATIONS.csv"
STEM = "vis_sce_capacity_supported_sensitivity"

HAZARDS = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
POLICIES = [
    "centrality-first", "impact-first", "betweenness-first", "degree-first",
    "closeness-first", "hospital-first", "random", "vulnerability-first",
    "Unconstrained",
]
DISPLAY = {
    "centrality-first": "Centrality",
    "impact-first": "Impact",
    "betweenness-first": "Betweenness",
    "degree-first": "Degree",
    "closeness-first": "Closeness",
    "hospital-first": "Hospital",
    "random": "Random",
    "vulnerability-first": "Vulnerability",
    "Unconstrained": "Unconstrained",
}


def _policy_rows(summary: pd.DataFrame) -> pd.DataFrame:
    if "row_type" in summary.columns:
        summary = summary.loc[summary["row_type"].fillna("policy").eq("policy")].copy()
    return summary


def render_from_frames(supported: pd.DataFrame, summary: pd.DataFrame, *, binding_count: int | None = None):
    july.apply_publication_style()
    summary = _policy_rows(summary)
    supported = supported.copy()
    supported["D_MW"] = pd.to_numeric(supported["D_MW"], errors="raise")
    supported["K_MW"] = pd.to_numeric(supported["K_MW"], errors="raise")
    if binding_count is None:
        binding_count = int((supported["D_MW"] > supported["K_MW"]).sum())

    fig = plt.figure(figsize=july.get_figsize("COMPOSITE_FULL_DENSE", width_cm=18.5, height_cm=15.2))
    gs = fig.add_gridspec(
        2, 2, width_ratios=[1.42, 1.0], height_ratios=[1, 1],
        left=.10, right=.98, bottom=.14, top=.91, wspace=.38, hspace=.48,
    )
    a = fig.add_subplot(gs[:, 0])
    b = fig.add_subplot(gs[0, 1])
    c = fig.add_subplot(gs[1, 1])

    # A: 19 one-to-one supported facilities.  D and K remain on the same MW axis.
    rows = supported.sort_values("D_MW").reset_index(drop=True)
    y = np.arange(len(rows))
    a.scatter(rows["D_MW"], y, label="D: SCE cumulative forecast demand (MW)",
              marker="o", s=18, zorder=3)
    a.scatter(rows["K_MW"], y, label="K: facility loading limit (MW)",
              marker="s", s=18, zorder=3)
    for i, row in rows.iterrows():
        a.plot([row["D_MW"], row["K_MW"]], [i, i], linewidth=.75, color="#b7b7b7", zorder=1)
        if row["D_MW"] > row["K_MW"]:
            a.annotate(
                "D > K", (row["D_MW"], i), xytext=(4, 4), textcoords="offset points",
                fontsize=july.FS_ANNOTATION, fontweight="semibold",
            )
    a.set_yticks(y)
    a.set_yticklabels(rows["StationName"], fontsize=july.FS_TICK)
    july.style_axis(
        a,
        title=f"A  Supported one-to-one SCE facilities\nCapacity binding in {binding_count} of 19 stations",
        xlabel="Planning quantity (MW)",
    )
    july.format_legend(a.legend(loc="lower right", frameon=True))

    # B: four-hazard Hospital-first change. Use a dot plot on an explicitly
    # expanded scale rather than a truncated bar chart.
    bh = summary.loc[summary["Policy"].eq("hospital-first")].set_index("Hazard").reindex(HAZARDS)
    if bh["delta"].isna().any():
        raise ValueError("Capacity summary lacks the four Hospital-first hazard rows")
    x = np.arange(len(HAZARDS))
    vals = bh["delta"].to_numpy(float)
    b.plot(x, vals, marker="o", linewidth=1.0)
    b.set_xticks(x, ["Northridge", "San Fernando", "Long Beach", "2pc50"], rotation=20, ha="right")
    pad = max(.0025, (vals.max() - vals.min()) * .35)
    b.set_ylim(vals.min() - pad, vals.max() + pad * 1.45)
    for i, value in enumerate(vals):
        b.annotate(f"{value:.3f}", (i, value), xytext=(0, 5), textcoords="offset points",
                   ha="center", fontsize=july.FS_ANNOTATION)
    july.style_axis(
        b,
        title="B  Hospital-first across hazards",
        ylabel="Δ population burden (h)\n(expanded scale)",
    )
    b.grid(axis="y", color="#e1e1e1", linewidth=.4)

    # C: 2pc50 strategy response, again as points on an explicit expanded scale.
    cp = summary.loc[summary["Hazard"].eq("2pc50")].set_index("Policy").reindex(POLICIES)
    if cp["delta"].isna().any():
        raise ValueError("Capacity summary lacks one or more final 2pc50 policy rows")
    x = np.arange(len(POLICIES))
    vals = cp["delta"].to_numpy(float)
    c.plot(x, vals, marker="o", linewidth=.9)
    c.set_xticks(x, [DISPLAY[p] for p in POLICIES], rotation=45, ha="right")
    pad = max(.0015, (vals.max() - vals.min()) * .30)
    c.set_ylim(vals.min() - pad, vals.max() + pad * 1.8)
    for i, value in enumerate(vals):
        c.annotate(f"{value:.3f}", (i, value), xytext=(0, 5), textcoords="offset points",
                   ha="center", fontsize=july.FS_ANNOTATION)
    july.style_axis(
        c,
        title="C  2pc50 frozen policy comparison",
        ylabel="Δ population burden (h)\n(expanded scale)",
    )
    c.grid(axis="y", color="#e1e1e1", linewidth=.4)

    fig.suptitle("SCE-supported planning-capacity sensitivity", fontsize=july.FS_SUPTITLE, y=.975)
    OUT.mkdir(parents=True, exist_ok=True)
    july.save_plot(fig, str(OUT), STEM + ".png")
    return OUT / (STEM + ".png"), OUT / (STEM + ".pdf")


def render():
    supported = pd.read_csv(SUPPORTED, dtype={"StationID": str})
    summary = pd.read_csv(SUMMARY)
    return render_from_frames(supported, summary)


if __name__ == "__main__":
    print("\n".join(map(str, render())))
