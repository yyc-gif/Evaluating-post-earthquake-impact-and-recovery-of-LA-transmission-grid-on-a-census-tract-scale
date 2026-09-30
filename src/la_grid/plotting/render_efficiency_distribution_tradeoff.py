"""Render the 2pc50 efficiency/distribution trade-off from frozen results.

No new policy, clustering, sampling, scheduling, or service calculation is
performed.  The figure reads the accepted 1,000-realization formal summaries
for Impact-first, Hospital-first, and Vulnerability-first.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd

import la_grid.plotting.Project_Visualizer as july
from la_grid.paths import REPO_ROOT as ROOT

FORMAL = ROOT / "Formal_Experiment_20260923"
OUT = ROOT / "results" / "figures"
TABLE_OUT = ROOT / "results" / "vulnerability" / "EFFICIENCY_DISTRIBUTION_TRADEOFF_2PC50.csv"
STEM = "Candidate_S18_Equity_Efficiency_Tradeoff"

POLICIES = ["impact-first", "hospital-first", "vulnerability-first"]
LABELS = {
    "impact-first": "Impact-first",
    "hospital-first": "Hospital-first",
    "vulnerability-first": "Vulnerability-first",
}
METRICS = [
    "population_weighted_normalized_burden_hr",
    "burden_Q4_hr",
    "absolute_Q4_minus_Q1_hr",
    "burden_gini",
]


def _load() -> pd.DataFrame:
    original = pd.read_parquet(
        FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet"
    )
    vuln = pd.read_parquet(
        FORMAL / "Equity_Amendment" / "VULNERABILITY_PRIMARY_SUMMARY.parquet"
    )
    common = (
        original["hazard"].eq("2pc50")
        & original["resource_scenario"].eq("C57_D1")
        & original["mapping"].eq("M1_UTILITY_003")
        & original["gate"].eq("G1_BASELINE_050")
        & original["comparison_domain"].eq("mapping_native_domain")
        & original["strategy_id"].isin(["impact-first", "hospital-first"])
    )
    vcommon = (
        vuln["hazard"].eq("2pc50")
        & vuln["resource_scenario"].eq("C57_D1")
        & vuln["mapping"].eq("M1_UTILITY_003")
        & vuln["gate"].eq("G1_BASELINE_050")
        & vuln["comparison_domain"].eq("mapping_native_domain")
        & vuln["strategy_id"].eq("vulnerability-first")
    )
    frame = pd.concat([original.loc[common], vuln.loc[vcommon]], ignore_index=True)
    if set(frame["strategy_id"]) != set(POLICIES):
        raise ValueError("Frozen trade-off inputs do not contain the three requested policies")
    if any(len(frame.loc[frame["strategy_id"].eq(p)]) != 1000 for p in POLICIES):
        raise ValueError("Trade-off input must contain 1,000 realizations per policy")
    if frame[METRICS].isna().any().any():
        raise ValueError("Trade-off input contains missing required metrics")
    return frame


def _summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy in POLICIES:
        d = frame.loc[frame["strategy_id"].eq(policy)]
        row = {"strategy_id": policy, "label": LABELS[policy], "n": len(d)}
        for metric in METRICS:
            row[metric] = float(d[metric].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def render():
    july.apply_publication_style()
    table = _summary(_load())
    TABLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(TABLE_OUT, index=False)

    july.STAGE6_SHARED_LINE_STYLES.setdefault(
        "vulnerability-first",
        {"color": "#a65628", "ls": "-", "lw_recovery": 1.08,
         "lw_topology": .98, "alpha_recovery": .85,
         "alpha_topology": .82, "zorder": 9},
    )
    july.STAGE6_RECOVERY_STYLE_CONFIG.setdefault(
        "vulnerability-first",
        {"label": "Vulnerability First (Q4)", **july._stage6_line_style("vulnerability-first")},
    )

    fig, axes = plt.subplots(
        1, 3, figsize=july.get_figsize("COMPOSITE_FULL_DENSE", width_cm=18.5, height_cm=7.5)
    )
    panels = [
        ("burden_Q4_hr", "A  Target-group outcome", "Q4 absolute burden (h)"),
        ("absolute_Q4_minus_Q1_hr", "B  Between-group separation", "Mean |Q4−Q1| burden gap (h)"),
        ("burden_gini", "C  Tract-wide inequality", "Population-weighted burden Gini"),
    ]
    xcol = "population_weighted_normalized_burden_hr"
    for ax, (ycol, title, ylabel) in zip(axes, panels):
        for row in table.itertuples(index=False):
            style = july.STAGE6_RECOVERY_STYLE_CONFIG[row.strategy_id]
            x = getattr(row, xcol)
            y = getattr(row, ycol)
            ax.scatter(x, y, s=30, color=style["color"], zorder=3)
        july.style_axis(
            ax, title=title,
            xlabel="Aggregate population burden (h)",
            ylabel=ylabel,
        )
        ax.grid(True, color="#e4e4e4", linewidth=.4)

    fig.suptitle(
        "2pc50/C57: aggregate efficiency and distributional outcomes",
        fontsize=july.FS_SUPTITLE, y=.985,
    )
    handles = [
        Line2D(
            [], [], linestyle="none", marker="o", markersize=5,
            markerfacecolor=july.STAGE6_RECOVERY_STYLE_CONFIG[policy]["color"],
            markeredgecolor=july.STAGE6_RECOVERY_STYLE_CONFIG[policy]["color"],
            label=LABELS[policy],
        )
        for policy in POLICIES
    ]
    fig.legend(
        handles=handles, loc="upper center", bbox_to_anchor=(.5, .91),
        ncol=3, frameon=False, fontsize=july.FS_LEGEND,
        handletextpad=.45, columnspacing=1.5,
    )
    fig.tight_layout(rect=(0, 0, 1, .83))
    OUT.mkdir(parents=True, exist_ok=True)
    july.save_plot(fig, str(OUT), STEM + ".png")
    return OUT / (STEM + ".png"), OUT / (STEM + ".pdf"), TABLE_OUT


if __name__ == "__main__":
    print("\n".join(map(str, render())))
