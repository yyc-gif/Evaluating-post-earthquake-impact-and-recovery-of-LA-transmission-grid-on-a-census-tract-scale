"""Presentation-only refresh of selected final artwork from frozen display tables.

No simulations, scheduling, GA, PCA, clustering, service calculations, or
bootstrap procedures are performed here. Inputs are already-frozen summaries,
paired-effect tables, event-grid display curves, and Stage 7 cluster labels.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import font_manager, patches
from matplotlib.lines import Line2D
from pathlib import Path

import la_grid.plotting.Project_Visualizer as july
from la_grid.paths import REPO_ROOT as ROOT

OUT = ROOT / "results" / "figures"
SUITE = ROOT / "results" / "revised_suite" / "LA_Grid_Revised_Suite_20260925"
S3 = SUITE / "Stage 3 Output_expanded"
S6 = SUITE / "Stage 6 Output_expanded"
FORMAL = ROOT / "Formal_Experiment_20260923"
STAGE7 = FORMAL / "Stage 7 Output_SOVI_Harmonized"

SCHEDULED = [
    "centrality-first", "impact-first", "betweenness-first", "degree-first",
    "closeness-first", "hospital-first", "random", "vulnerability-first",
]
PAIRED_ORDER = [
    "centrality-first", "impact-first", "betweenness-first", "degree-first",
    "closeness-first", "random", "vulnerability-first",
]
DISPLAY = {
    "centrality-first": "Centrality-first",
    "impact-first": "Impact-first",
    "betweenness-first": "Betweenness-first",
    "degree-first": "Degree-first",
    "closeness-first": "Closeness-first",
    "hospital-first": "Hospital-first",
    "random": "Random",
    "vulnerability-first": "Vulnerability-first",
    "unconstrained": "Unconstrained",
    "S3_Mean": "Unconstrained",
}
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*", "o"]
CM = 1 / 2.54


def configure() -> None:
    font_path = font_manager.findfont("Arial", fallback_to_default=False)
    if not font_path.lower().endswith(("arial.ttf", "arialbd.ttf")):
        raise RuntimeError(f"Final artwork requires installed Arial; found {font_path}")
    july.apply_publication_style()
    matplotlib.rcParams.update({
        "font.family": "Arial", "font.sans-serif": ["Arial"],
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "pdf.use14corefonts": False, "savefig.dpi": 600,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })
    july.STAGE6_SHARED_LINE_STYLES.setdefault(
        "vulnerability-first",
        {"color": "#a65628", "ls": "-", "lw_recovery": 1.08,
         "lw_topology": .98, "alpha_recovery": .85,
         "alpha_topology": .82, "zorder": 9},
    )
    july.STAGE6_RECOVERY_STYLE_CONFIG.setdefault(
        "vulnerability-first",
        {"label": "Vulnerability-first", **july._stage6_line_style("vulnerability-first")},
    )
    july.STAGE6_RECOVERY_STYLE_CONFIG["S3_Mean"]["label"] = "Unconstrained"
    for key, label in DISPLAY.items():
        if key in july.STAGE6_RECOVERY_STYLE_CONFIG:
            july.STAGE6_RECOVERY_STYLE_CONFIG[key]["label"] = label
    OUT.mkdir(parents=True, exist_ok=True)


def save(fig, stem: str) -> None:
    july.save_plot(fig, str(OUT), stem + ".png")


def line_style(key: str, index: int = 0, role: str = "recovery") -> dict:
    raw = july._stage6_line_style(key, role=role)
    return {**raw, "marker": MARKERS[index % len(MARKERS)]}


def add_shared_legend(fig, handles, *, ncol=3, y=.99) -> None:
    legend = fig.legend(
        handles=handles, loc="upper center", bbox_to_anchor=(.5, y),
        ncol=ncol, frameon=False, handlelength=1.8, columnspacing=.95,
        handletextpad=.45, labelspacing=.32, fontsize=july.FS_LEGEND,
    )
    july.format_legend(legend)


def plot_recovery() -> None:
    d = pd.read_csv(S6 / "ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv")
    d = d[d.hazard.eq("2pc50")].copy()
    expected = {"unconstrained", *SCHEDULED}
    if set(d.strategy_id.unique()) != expected:
        raise ValueError("Frozen recovery display table must contain 8 policies + Unconstrained")
    fig, ax = plt.subplots(figsize=(18.5 * CM, 8.2 * CM))
    handles = []
    all_keys = ["unconstrained", *SCHEDULED]
    for i, key in enumerate(all_keys):
        s = d[d.strategy_id.eq(key)].sort_values("time_hr")
        style_key = "S3_Mean" if key == "unconstrained" else key
        st = line_style(style_key, i)
        line = ax.step(
            s.time_hr, s.mean_population_availability_proxy, where="post",
            color=st["color"], linestyle=st["ls"], linewidth=st["lw"],
            alpha=max(st["alpha"], .88), zorder=st["zorder"],
            marker=st["marker"], markevery=max(1, len(s) // 7), markersize=2.8,
            label=DISPLAY[key],
        )[0]
        handles.append(line)
    july.style_axis(
        ax, title="2pc50: population-weighted service availability",
        xlabel="Time (h)", ylabel=r"Service availability, $F_{\mathrm{pop}}(t)$",
        label_size=8.6, title_size=july.FS_TITLE,
    )
    ax.set_xlim(0, 120); ax.set_ylim(-.02, 1.05)
    ax.grid(True, color="#e4e4e4", linewidth=.4, linestyle="--", alpha=.65)
    add_shared_legend(fig, handles, ncol=3, y=.995)
    fig.subplots_adjust(left=.11, right=.985, bottom=.16, top=.73)
    save(fig, "Candidate_Figure_All_Strategy_Recovery")


def paired_rows(metric: str) -> pd.DataFrame:
    formal = pd.read_csv(FORMAL / "Formal_Results" / "PAIRED_STRATEGY_EFFECTS.csv")
    vuln = pd.read_csv(FORMAL / "Equity_Amendment" / "VULNERABILITY_PAIRWISE_EFFECTS.csv")
    f = formal[
        formal.hazard.eq("2pc50") & formal.resource_scenario.eq("C57_D1")
        & formal.reference_strategy.eq("hospital-first")
        & formal.strategy_id.isin(PAIRED_ORDER[:-1]) & formal.metric.eq(metric)
    ][["strategy_id", "paired_mean_difference", "bootstrap_ci_low", "bootstrap_ci_high"]]
    v = vuln[
        vuln.hazard.eq("2pc50") & vuln.resource_scenario.eq("C57_D1")
        & vuln.reference_strategy.eq("hospital-first")
        & vuln.strategy_id.eq("vulnerability-first") & vuln.metric.eq(metric)
    ][["strategy_id", "paired_mean_difference", "bootstrap_ci_low", "bootstrap_ci_high"]]
    out = pd.concat([f, v], ignore_index=True)
    if set(out.strategy_id) != set(PAIRED_ORDER) or len(out) != 7:
        raise ValueError(f"Missing paired 2pc50/C57_D1 rows for {metric}")
    return out.set_index("strategy_id").loc[PAIRED_ORDER].reset_index()


def plot_paired(stem: str, metric: str, title: str, xlabel: str) -> None:
    d = paired_rows(metric)
    fig, ax = plt.subplots(figsize=(18.5 * CM, 6.9 * CM))
    ypos = np.arange(len(d))[::-1]
    for y, row in zip(ypos, d.itertuples(index=False)):
        st = line_style(row.strategy_id, PAIRED_ORDER.index(row.strategy_id))
        lo = row.paired_mean_difference - row.bootstrap_ci_low
        hi = row.bootstrap_ci_high - row.paired_mean_difference
        ax.errorbar(
            row.paired_mean_difference, y, xerr=np.array([[lo], [hi]]),
            fmt=st["marker"], color=st["color"], ecolor=st["color"],
            markersize=4.3, elinewidth=1.05, capsize=2.0, alpha=.94, zorder=3,
        )
    july.style_axis(ax, title=title, xlabel=xlabel, title_size=july.FS_TITLE)
    ax.set_yticks(ypos, [DISPLAY[k] for k in d.strategy_id])
    ax.tick_params(axis="y", labelsize=july.FS_TICK)
    ax.axvline(0, color="#666666", linestyle="--", linewidth=.7, zorder=0)
    ax.grid(True, axis="x", color="#e4e4e4", linewidth=.4, alpha=.7)
    ax.grid(False, axis="y")
    fig.subplots_adjust(left=.25, right=.985, bottom=.19, top=.83)
    save(fig, stem)


def plot_source_path() -> None:
    p = S6 / "SOURCE_PATH_PAIRED_EFFECT_DISPLAY.csv"
    d = pd.read_csv(p)
    d = d[d.hazard.eq("2pc50")].copy()
    if set(d.strategy_id) != set(PAIRED_ORDER):
        raise ValueError("Source-path display table does not contain 7 distinct comparisons")
    d = d.set_index("strategy_id").loc[PAIRED_ORDER].reset_index()
    fig, ax = plt.subplots(figsize=(18.5 * CM, 6.9 * CM))
    ypos = np.arange(len(d))[::-1]
    for y, row in zip(ypos, d.itertuples(index=False)):
        st = line_style(row.strategy_id, PAIRED_ORDER.index(row.strategy_id))
        ax.hlines(y, row.p05_paired_delta_hr, row.p95_paired_delta_hr,
                  color=st["color"], linewidth=1.3, alpha=.95)
        ax.plot(row.mean_paired_delta_hr, y, marker=st["marker"], color=st["color"],
                markersize=4.3, linestyle="none", zorder=3)
    july.style_axis(
        ax, title="2pc50: paired source-path burden difference",
        xlabel="Difference from Hospital-first (h); 5–95% paired-realization range",
        title_size=july.FS_TITLE,
    )
    ax.set_yticks(ypos, [DISPLAY[k] for k in d.strategy_id])
    ax.tick_params(axis="y", labelsize=july.FS_TICK)
    ax.axvline(0, color="#666666", linestyle="--", linewidth=.7, zorder=0)
    ax.grid(True, axis="x", color="#e4e4e4", linewidth=.4, alpha=.7)
    fig.subplots_adjust(left=.25, right=.985, bottom=.19, top=.83)
    save(fig, "Candidate_Figure_Source_Path_Burden")


def plot_quartile_burden() -> None:
    summary = pd.read_csv(S6 / "ALL_DISTINCT_STRATEGIES_BY_HAZARD.csv")
    d = summary[summary.hazard.eq("2pc50") & summary.strategy_id.isin(SCHEDULED)].copy()
    if set(d.strategy_id) != set(SCHEDULED):
        raise ValueError("Expected eight scheduled strategy summary rows for Q1–Q4")
    qcols = [f"burden_Q{i}_hr_mean" for i in range(1, 5)]
    fig, ax = plt.subplots(figsize=(18.5 * CM, 6.9 * CM))
    handles = []
    for i, key in enumerate(SCHEDULED):
        row = d[d.strategy_id.eq(key)].iloc[0]
        st = line_style(key, i)
        line, = ax.plot(
            np.arange(1, 5), row[qcols].to_numpy(float),
            color=st["color"], linestyle=st["ls"], linewidth=1.15,
            marker=st["marker"], markersize=3.2, alpha=.94, label=DISPLAY[key],
        )
        handles.append(line)
    july.style_axis(
        ax, title="2pc50: absolute social-vulnerability-group burden",
        xlabel="Social-vulnerability quartile (Q4 highest)",
        ylabel="Mean cumulative burden (h)", title_size=july.FS_TITLE,
    )
    ax.set_xticks(np.arange(1, 5), ["Q1", "Q2", "Q3", "Q4"])
    ax.grid(True, color="#e4e4e4", linewidth=.4, alpha=.7)
    add_shared_legend(fig, handles, ncol=4, y=.995)
    fig.subplots_adjust(left=.11, right=.985, bottom=.16, top=.70)
    save(fig, "Candidate_Figure_Q1_Q4_Absolute_Burden")


def plot_loss_decomposition() -> None:
    d = pd.read_csv(S3 / "LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv")
    d = d[d.hazard.eq("2pc50") & d.resource_scenario.eq("C57_D1")
          & d.strategy_id.isin(SCHEDULED)].copy()
    if set(d.strategy_id) != set(SCHEDULED):
        raise ValueError("Loss decomposition summary must contain the eight scheduled policies")
    d = d.set_index("strategy_id").loc[SCHEDULED].reset_index()
    fig, ax = plt.subplots(figsize=(18.5 * CM, 8.4 * CM))
    y = np.arange(len(d))
    components = [
        ("self_mean_hr", "Own-station damage", "#729CC5"),
        ("threshold_mean_hr", "Functional threshold", "#E99B3C"),
        ("source_mean_hr", "Source-path disconnection", "#B5262B"),
    ]
    left = np.zeros(len(d))
    for col, label, color in components:
        vals = d[col].to_numpy(float)
        ax.barh(y, vals, left=left, height=.62, color=color,
                edgecolor="white", linewidth=.5, label=label)
        left += vals
    ax.set_yticks(y, [DISPLAY[k] for k in d.strategy_id])
    ax.invert_yaxis()
    july.style_axis(ax, title="2pc50: cumulative modeled service-loss components",
                    xlabel="Population-mass-weighted cumulative loss (h)",
                    title_size=july.FS_TITLE)
    ax.tick_params(axis="y", labelsize=july.FS_TICK)
    ax.grid(True, axis="x", color="#e4e4e4", linewidth=.4, alpha=.7)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    add_shared_legend(fig, handles, ncol=3, y=.995)
    fig.subplots_adjust(left=.25, right=.985, bottom=.15, top=.82)
    save(fig, "Candidate_S7_Gate_Decomposition")


def resource_means(metric: str, scenarios: list[str]) -> pd.DataFrame:
    # The per-realization formal/equity summary tables already contain this
    # metric for each frozen resource case. This is a table-to-figure mean only.
    formal = pd.read_parquet(FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
    vuln = pd.read_parquet(FORMAL / "Equity_Amendment" / "VULNERABILITY_PRIMARY_SUMMARY.parquet")
    fields = ["hazard", "resource_scenario", "mapping", "gate", "comparison_domain", "strategy_id", metric]
    formal = formal[fields].copy()
    vuln = vuln[fields].copy()
    frame = pd.concat([formal, vuln], ignore_index=True)
    frame = frame[
        frame.hazard.eq("2pc50") & frame.resource_scenario.isin(scenarios)
        & frame.mapping.eq("M1_UTILITY_003") & frame.gate.eq("G1_BASELINE_050")
        & frame.comparison_domain.eq("mapping_native_domain")
        & frame.strategy_id.isin(SCHEDULED)
    ]
    counts = frame.groupby(["resource_scenario", "strategy_id"]).size()
    if not counts.eq(1000).all() or set(counts.index.get_level_values("strategy_id")) != set(SCHEDULED):
        raise ValueError(f"Frozen resource summaries need 1,000 rows per policy/case for {metric}")
    out = (frame.groupby(["resource_scenario", "strategy_id"], as_index=False)[metric]
           .mean().rename(columns={"strategy_id": "strategy", metric: "value"}))
    if set(out.strategy) != set(SCHEDULED) or out.duplicated(["resource_scenario", "strategy"]).any():
        raise ValueError(f"Resource means incomplete or duplicated for {metric}")

    # Guard the population-burden display values against the already-published
    # OFAT summary where that same metric is available.
    if metric == "population_resolved_mass_weighted_burden_hr":
        published = pd.read_csv(SUITE / "Sensitivity Output_clean" / "FORMAL_RESOURCE_EFFECTS.csv")
        published = published[published.metric.eq(metric) & published.resource_scenario.isin(scenarios)
                              & published.strategy_id.ne("direct-community")]
        checks = out.merge(published[["resource_scenario", "strategy_id", "target_mean"]],
                           left_on=["resource_scenario", "strategy"],
                           right_on=["resource_scenario", "strategy_id"], how="inner")
        if not np.allclose(checks.value, checks.target_mean, rtol=0, atol=1e-10):
            raise ValueError("Frozen resource table and per-realization mean do not reconcile")
    return out


def plot_resource(stem: str, metric: str, xcases: list[tuple[str, float]],
                  title: str, xlabel: str, ylabel: str) -> None:
    means = resource_means(metric, [case for case, _ in xcases])
    fig, ax = plt.subplots(figsize=(18.5 * CM, 6.9 * CM))
    handles = []
    for i, key in enumerate(SCHEDULED):
        d = means[means.strategy.eq(key)].set_index("resource_scenario")
        vals = [float(d.loc[case, "value"]) for case, _ in xcases]
        st = line_style(key, i)
        line, = ax.plot(
            [x for _, x in xcases], vals, color=st["color"], linestyle=st["ls"],
            linewidth=1.15, marker=st["marker"], markersize=3.2,
            alpha=.94, label=DISPLAY[key],
        )
        handles.append(line)
    july.style_axis(ax, title=title, xlabel=xlabel, ylabel=ylabel,
                    title_size=july.FS_TITLE)
    ax.set_xticks([x for _, x in xcases], [f"{x:.2f}" if metric == "burden_Q4_hr" else f"{x:.0f}"
                                          for _, x in xcases])
    ax.grid(True, color="#e4e4e4", linewidth=.4, alpha=.7)
    add_shared_legend(fig, handles, ncol=4, y=.995)
    fig.subplots_adjust(left=.12, right=.985, bottom=.16, top=.70)
    save(fig, stem)


def plot_population_by_hazard() -> None:
    d = pd.read_csv(S6 / "ALL_DISTINCT_STRATEGIES_BY_HAZARD.csv")
    hazards = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
    strategies = [*SCHEDULED, "unconstrained"]
    fig, axes = plt.subplots(2, 2, figsize=(18.5 * CM, 12.8 * CM), sharey=False)
    for ax, hazard in zip(axes.flat, hazards):
        part = d[d.hazard.eq(hazard)].set_index("strategy_id")
        if set(part.index) != set(strategies):
            raise ValueError(f"Missing 8 scheduled + Unconstrained summary rows for {hazard}")
        y = np.arange(len(strategies))[::-1]
        for i, key in enumerate(strategies):
            style_key = "S3_Mean" if key == "unconstrained" else key
            st = line_style(style_key, i)
            ax.plot(part.loc[key, "population_resolved_mass_weighted_burden_hr_mean"],
                    y[i], marker=st["marker"], linestyle="none", markersize=4.0,
                    color=st["color"], zorder=3)
        ax.set_yticks(y, [DISPLAY[k] for k in strategies])
        ax.tick_params(axis="both", labelsize=july.FS_TICK, width=.6, length=2.5)
        july.style_axis(ax, title=hazard, xlabel="Population cumulative burden (h)",
                        title_size=july.FS_PANEL)
        ax.grid(True, axis="x", color="#e4e4e4", linewidth=.4, alpha=.7)
    # The right-column panels share the exact strategy order with the left
    # column. Keep labels once per row to prevent the two inner label blocks
    # from colliding at the fixed July full-width size.
    for ax in axes[:, 1]:
        ax.tick_params(axis="y", labelleft=False)
    fig.suptitle("Population cumulative burden across hazards and strategies",
                 fontsize=july.FS_TITLE, fontweight="semibold", y=.985)
    fig.subplots_adjust(left=.23, right=.985, bottom=.08, top=.93, wspace=.25, hspace=.30)
    save(fig, "formal_population_burden_by_hazard")


def plot_formal_impact_first_t80_map() -> None:
    """Re-render the retained tract-level T80 map from its frozen formal table.

    The archived image used the historical ``direct-community`` display alias.
    Its frozen sequence is identical to Impact-first; this output keeps the
    unique spatial information while using the current paper-facing name.
    """
    kpis = pd.read_csv(FORMAL / "Stage 5 Output_expanded" / "tract_kpis_2pc50.csv",
                       dtype={"tract_id": str})
    if len(kpis) != 2315 or not {"tract_id", "T80"}.issubset(kpis.columns):
        raise ValueError("Frozen formal tract T80 table must cover all 2,315 study tracts")
    kpis["tract_id"] = kpis.tract_id.str.replace(r"\.0$", "", regex=True).str.zfill(11)
    geometry = gpd.read_file(ROOT / "Data" / "LA_Tracts_With_Population.shp")
    geometry["tract_id"] = geometry.GEOID.astype(str).str.zfill(11)
    mapped = geometry.merge(kpis[["tract_id", "T80"]], on="tract_id", how="inner",
                            validate="one_to_one")
    if len(mapped) != 2315 or set(mapped.tract_id) != set(kpis.tract_id):
        raise ValueError("Frozen T80 table and full study-area geometry do not match")
    values = pd.Series(mapped.T80.to_numpy(dtype=float), index=mapped.tract_id)
    july.apply_publication_style()
    matplotlib.rcParams.update({
        "font.family": "Arial", "font.sans-serif": ["Arial"],
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "pdf.use14corefonts": False,
    })
    july.plot_map(
        mapped, values,
        title="2pc50: Impact-first mean tract T80",
        output_dir=str(OUT),
        filename="vis_formal_2pc50_impact_first_tract_T80_map.png",
        cmap="viridis", label="T80 (h)", figure_role="COMPOSITE_MEDIUM",
    )


def plot_cutoff_robustness() -> None:
    """Refresh the mapping-cutoff display using its frozen effect table."""
    d = pd.read_csv(FORMAL / "Formal_Reviewer_Results" / "FORMAL_MAPPING_EFFECTS.csv")
    values = []
    for comparison in ("2pc50_cutoff_M1_none", "2pc50_cutoff_M1_001"):
        row = d.loc[(d.comparison.eq(comparison)) &
                    (d.strategy_id.eq("hospital-first")) &
                    (d.metric.eq("population_resolved_mass_weighted_burden_hr"))]
        if len(row) != 1 or not np.isfinite(row.mean_delta.iloc[0]):
            raise ValueError(f"Expected one frozen Hospital-first cutoff row for {comparison}")
        values.append(float(row.mean_delta.iloc[0]))
    values.append(0.0)  # the fixed 3% production M1 baseline
    fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
    ax.plot([0, .01, .03], values, marker="o", markersize=3,
            linewidth=1.2, color="#b22222", label="Utility-compatible M1")
    ax.axhline(0, color=".4", linestyle="--", linewidth=.6)
    ax.set_xticks([0, .01, .03], ["No cutoff", "1%", "3% production"])
    july.style_axis(ax, title="2pc50: cutoff response vs 3% M1 (Hospital-first)",
                    xlabel="Candidate-weight cutoff",
                    ylabel="Δ population burden (h)")
    legend = ax.legend(frameon=False)
    july.format_legend(legend)
    fig.subplots_adjust(left=.20, right=.985, bottom=.22, top=.78)
    save(fig, "Candidate_S16_Cutoff_Robustness")


def plot_network_topology_recovery() -> None:
    d = pd.read_csv(S6 / "NETWORK_TOPOLOGY_DISPLAY_CURVES_2pc50.csv")
    expected = {"unconstrained", *SCHEDULED}
    if set(d.strategy_id.unique()) != expected:
        raise ValueError("Topology display curves must contain 8 policies + Unconstrained")
    fig, axes = plt.subplots(2, 1, figsize=(18.5 * CM, 12.0 * CM), sharex=True)
    handles = []
    for i, key in enumerate(["unconstrained", *SCHEDULED]):
        p = d[d.strategy_id.eq(key)].sort_values("time_hr")
        style_key = "S3_Mean" if key == "unconstrained" else key
        st = line_style(style_key, i, role="topology")
        for ax, col in zip(axes, ["mean_lcc_fraction", "mean_lcc_average_degree"]):
            ln, = ax.plot(p.time_hr, p[col], color=st["color"], linestyle=st["ls"],
                          linewidth=st["lw"], alpha=max(st["alpha"], .88),
                          marker=st["marker"], markevery=48, markersize=2.8,
                          label=DISPLAY[key])
        handles.append(ln)
    july.style_axis(axes[0], title="A  Largest connected component", ylabel="LCC size / 92 stations",
                    title_size=july.FS_PANEL)
    july.style_axis(axes[1], title="B  Active-network average degree",
                    xlabel="Time (h)", ylabel="Mean degree within the LCC",
                    title_size=july.FS_PANEL)
    axes[0].set_xlim(0, 120); axes[0].set_ylim(-.02, 1.05)
    for ax in axes:
        ax.grid(True, color="#e4e4e4", linewidth=.4, alpha=.7)
    add_shared_legend(fig, handles, ncol=3, y=.995)
    fig.subplots_adjust(left=.13, right=.985, bottom=.10, top=.79, hspace=.36)
    save(fig, "vis_stage6_network_topology_recovery_2pc50")


def plot_stage7_map_and_scores() -> None:
    status = pd.read_csv(STAGE7 / "stage7_full_domain_tract_status.csv",
                         dtype={"tract_id": str})
    status["tract_id"] = status.tract_id.str.zfill(11)
    clusters = pd.read_csv(STAGE7 / "clusters_labels_final.csv",
                           dtype={"tract_id": str})
    clusters["tract_id"] = clusters.tract_id.str.zfill(11)
    if len(status) != 2315 or len(clusters) != 2291:
        raise ValueError("Stage 7 display inputs must remain 2,315 tracts / 2,291 typology members")
    geo = gpd.read_file(ROOT / "Data" / "LA_Tracts_With_Population.shp")
    geo["tract_id"] = geo.GEOID.astype(str).str.zfill(11)
    geo = geo.merge(status[["tract_id", "typology_status", "cluster"]],
                    on="tract_id", how="inner", validate="one_to_one")
    if len(geo) != 2315:
        raise ValueError("Stage 7 map geometry must cover the complete study area")
    try:
        geo = geo.to_crs(epsg=3310)
    except Exception:
        pass
    cluster_keys = ["1", "2", "3", "4", "5"]
    colors = {str(i + 1): july.STAGE7_IJDRR_CLUSTER_PALETTE[i] for i in range(5)}
    fig, ax = plt.subplots(figsize=(12.8 * CM, 11.8 * CM))
    na = geo[geo.typology_status.ne("residential_typology_eligible")]
    obs = geo[geo.typology_status.eq("residential_typology_eligible")].copy()
    obs["cluster"] = obs.cluster.astype(float).astype(int).astype(str)
    if len(na) != 24 or set(obs.cluster.unique()) != set(cluster_keys):
        raise ValueError("Stage 7 map must retain 24 N/A tracts and clusters C1-C5")
    na.plot(ax=ax, color=july.STAGE7_NA_COLOR, edgecolor="white", linewidth=.13, zorder=0)
    obs.plot(ax=ax, color=obs.cluster.map(colors), edgecolor="white", linewidth=.13, zorder=1)
    geo.dissolve().boundary.plot(ax=ax, color="#666666", linewidth=.50, zorder=2)
    hot = pd.read_csv(STAGE7 / "stage7_top10_slow_vulnerable_tracts.csv",
                      dtype={"tract_id": str})
    hot["tract_id"] = hot.tract_id.str.zfill(11)
    hot_geo = geo[geo.tract_id.isin(set(hot.tract_id))]
    if not hot_geo.empty:
        hot_geo.boundary.plot(ax=ax, color="#222222", linewidth=1.15, zorder=10)
    x0, y0, x1, y1 = geo.total_bounds
    ax.set_xlim(x0 - .03*(x1-x0), x1 + .03*(x1-x0))
    ax.set_ylim(y0 - .03*(y1-y0), y1 + .03*(y1-y0))
    ax.set_aspect("equal"); ax.axis("off")
    handles = [patches.Patch(facecolor=colors[c], edgecolor="#454545", linewidth=.35,
                             label=f"C{c}") for c in cluster_keys]
    handles.append(patches.Patch(facecolor=july.STAGE7_NA_COLOR, edgecolor="#777777",
                                 linewidth=.35, label="Residential typology not applicable"))
    if not hot_geo.empty:
        handles.append(Line2D([], [], color="#222222", linewidth=1.15, label="Top-10 hotspots"))
    legend = ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, -.10),
                       ncol=4, frameon=False, fontsize=july.FS_LEGEND,
                       handlelength=1.1, columnspacing=.9, labelspacing=.35)
    july.format_legend(legend)
    fig.subplots_adjust(left=.02, right=.98, top=.98, bottom=.13)
    save(fig, "vis_stage7_map_clusters")

    # The PCA score plot uses frozen PC columns and frozen cluster membership.
    p = clusters.dropna(subset=["PC1", "PC2", "cluster"]).copy()
    p["cluster"] = p.cluster.astype(float).astype(int).astype(str)
    pca_stats_path = STAGE7 / "pca_stats_with_eigenvalues.csv"
    stats = pd.read_csv(pca_stats_path) if pca_stats_path.is_file() else None
    ratios = {}
    if stats is not None and {"PC", "Explained_Variance_Ratio"}.issubset(stats.columns):
        ratios = dict(zip(stats.PC.astype(str), stats.Explained_Variance_Ratio.astype(float)))
    fig, ax = plt.subplots(figsize=(13.2 * CM, 9.0 * CM))
    shapes = ["o", "s", "^", "D", "v"]
    for i, key in enumerate(cluster_keys):
        z = p[p.cluster.eq(key)]
        ax.scatter(z.PC1, z.PC2, s=15, alpha=.55, color=colors[key],
                   marker=shapes[i], linewidths=.15, edgecolors="white", label=f"C{key}")
    def pc_label(pc):
        return f"{pc} ({100*ratios[pc]:.1f}%)" if pc in ratios else pc
    july.style_axis(ax, title="PCA scores by frozen cluster membership",
                    xlabel=pc_label("PC1"), ylabel=pc_label("PC2"),
                    title_size=july.FS_PANEL)
    ax.grid(True, color="#e4e4e4", linewidth=.4, alpha=.65)
    legend = ax.legend(loc="upper center", bbox_to_anchor=(.5, -.17), ncol=5,
                       frameon=False, fontsize=july.FS_LEGEND, handletextpad=.35,
                       columnspacing=.8)
    july.format_legend(legend)
    fig.subplots_adjust(left=.14, right=.98, bottom=.24, top=.88)
    save(fig, "vis_stage7_pca_kmeans_scatter")


def plot_stage7_pca_loadings() -> None:
    """Rerender the frozen Stage 7 PCA-loading display table only.

    This reads the already-frozen loading matrix. It does not fit or rerun PCA.
    """
    path = STAGE7 / "pca_loadings.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Frozen Stage 7 loading table missing: {path}")
    loadings = pd.read_csv(path, index_col=0)
    pc_cols = [c for c in loadings.columns if str(c).strip().upper().startswith("PC")]
    pc_cols.sort(key=lambda col: int("".join(ch for ch in str(col) if ch.isdigit()) or 0))
    if pc_cols:
        loadings = loadings.loc[:, pc_cols]
    if loadings.empty or not loadings.apply(pd.to_numeric, errors="coerce").notna().all().all():
        raise ValueError("Frozen Stage 7 PCA-loading table is empty or nonnumeric")
    loadings = loadings.apply(pd.to_numeric, errors="raise").copy()
    loadings.index = [july.PRETTY_VAR_NAMES.get(str(i), str(i)) for i in loadings.index]
    max_abs = max(float(np.nanmax(np.abs(loadings.to_numpy(float)))), 1e-6)
    height_cm = max(july.PANEL_ASYM_LEFT["height_cm"], 0.9 * loadings.shape[0] + 4.0)
    fig, ax = plt.subplots(
        figsize=july.get_figsize(
            "COMPOSITE_FULL_DEFAULT",
            width_cm=july.FIGURE_WIDTH_FULL_CM,
            height_cm=height_cm,
        )
    )
    sns.heatmap(
        loadings,
        center=0.0,
        vmin=-max_abs,
        vmax=max_abs,
        cmap="coolwarm",
        linewidths=0.5,
        linecolor="white",
        annot=True,
        fmt=".2f",
        cbar_kws={"label": "PCA loading (feature weight)"},
        ax=ax,
    )
    mesh = ax.collections[0]
    july.style_colorbar_with_endpoints(
        mesh.colorbar, float(mesh.norm.vmin), float(mesh.norm.vmax), include_zero=True
    )
    ticklabels = mesh.colorbar.ax.get_yticklabels()
    if ticklabels:
        ticklabels[-1].set_verticalalignment("top")
        ticklabels[0].set_verticalalignment("bottom")
    july.style_axis(ax, xlabel="Principal component", ylabel="Features", xrotation=0, yrotation=0)
    july.save_plot(
        fig, str(OUT), "vis_stage7_pca_loadings_heatmap.png", top_clearance_inches=.10
    )


def main() -> None:
    configure()
    plot_recovery()
    plot_paired("Candidate_Figure_Population_Burden",
                "population_resolved_mass_weighted_burden_hr",
                "2pc50: population cumulative burden",
                "Paired difference from Hospital-first (h); 95% bootstrap CI")
    plot_paired("Candidate_Figure_Hospital_Burden",
                "hospital_mean_normalized_burden_hr",
                "2pc50: Hospital-tract burden",
                "Paired difference from Hospital-first (h); 95% bootstrap CI")
    plot_paired("Candidate_Figure_T80", "population_T80_hr",
                "2pc50: population T80",
                "Paired difference from Hospital-first (h); 95% bootstrap CI")
    plot_source_path()
    plot_quartile_burden()
    plot_loss_decomposition()
    plot_resource(
        "Candidate_S17_Resource_Sensitivity", "population_resolved_mass_weighted_burden_hr",
        [("C29_D1", 29), ("C57_D1", 57), ("C86_D1", 86), ("C114_D1", 114)],
        "2pc50: population cumulative burden — crew OFAT",
        "Available crews (one factor at a time)", "Cumulative burden (h)",
    )
    plot_resource(
        "Candidate_S20_Resource_Equity_Tradeoff", "burden_Q4_hr",
        [("C57_D075", .75), ("C57_D1", 1.00), ("C57_D125", 1.25), ("C57_D150", 1.50)],
        "2pc50: Q4 cumulative burden — duration OFAT",
        "Repair-duration scale (one factor at a time)", "Q4 cumulative burden (h)",
    )
    plot_population_by_hazard()
    plot_formal_impact_first_t80_map()
    plot_cutoff_robustness()
    plot_network_topology_recovery()
    plot_stage7_map_and_scores()


if __name__ == "__main__":
    main()
