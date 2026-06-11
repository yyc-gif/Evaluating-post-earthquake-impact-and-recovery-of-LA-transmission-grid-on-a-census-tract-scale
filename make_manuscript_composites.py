"""Create manuscript-ready composites directly from project output data.

The panels are rendered at their final physical sizes. No raster result
thumbnails are resized into the composites.
"""

from __future__ import annotations

from pathlib import Path
import re

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import pandas as pd
import seaborn as sns


CM_PER_INCH = 2.54
EXPORT_DPI = 600
FIGURE_WIDTH_CM = 18.5

ROOT = Path(__file__).resolve().parent
MANUSCRIPT_DIR = ROOT / "Manuscript_Figures"
STAGE3 = ROOT / "Stage 3 Output_expanded"
STAGE4 = ROOT / "Stage 4 Output_expanded"
STAGE5 = ROOT / "Stage 5 Output_expanded"
STAGE6 = ROOT / "Stage 6 Output_expanded"
STAGE7 = ROOT / "Stage 7 Output_expanded"
TRACT_SHP = ROOT / "Data" / "LA_Tracts_With_Population.shp"

TIME_CMAP = LinearSegmentedColormap.from_list(
    "recovery_time",
    ["#3b4cc0", "#80b1d3", "#fee08b", "#f46d43", "#a50026"],
)
HOTSPOT_CMAP = LinearSegmentedColormap.from_list(
    "hotspot_score",
    ["#2c7bb6", "#abd9e9", "#ffffbf", "#f46d43", "#8b1e3f"],
)
CLUSTER_COLORS = {
    "1": "#607d9e",
    "2": "#b99b4a",
    "3": "#5e8b61",
    "4": "#86afc0",
    "5": "#92607f",
    "6": "#b97070",
}

RC = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 8.0,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8.0,
    "xtick.labelsize": 7.0,
    "ytick.labelsize": 7.0,
    "legend.fontsize": 7.0,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "grid.linewidth": 0.45,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.facecolor": "white",
}


def cm(value: float) -> float:
    return value / CM_PER_INCH


def normalize_tract_id(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .str[-10:]
    )


def load_tracts() -> gpd.GeoDataFrame:
    tracts = gpd.read_file(TRACT_SHP).to_crs(epsg=4326)
    tracts = tracts.copy()
    tracts["tract_id"] = normalize_tract_id(tracts["GEOID"])
    return tracts


def style_axis(ax: plt.Axes, grid: bool = True) -> None:
    ax.tick_params(direction="out", color="#4d4d4d")
    for spine in ax.spines.values():
        spine.set_color("#bdbdbd")
        spine.set_linewidth(0.6)
    if grid:
        ax.grid(True, color="#d9d9d9", alpha=0.65, linewidth=0.45)
        ax.set_axisbelow(True)


def panel_label(ax: plt.Axes, label: str, x: float = -0.10, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10.0,
        fontweight="bold",
        color="#111111",
        clip_on=False,
    )


def save_pair(fig: plt.Figure, stem: str) -> None:
    MANUSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = MANUSCRIPT_DIR / f"{stem}.png"
    pdf_path = MANUSCRIPT_DIR / f"{stem}.pdf"
    fig.savefig(png_path, dpi=EXPORT_DPI, bbox_inches=None, pad_inches=0)
    fig.savefig(pdf_path, format="pdf", bbox_inches=None, pad_inches=0)
    plt.close(fig)
    print(f"Saved: {png_path}")
    print(f"Saved: {pdf_path}")


def make_t80_composite(tracts: gpd.GeoDataFrame) -> None:
    kpis = pd.read_csv(STAGE3 / "tract_kpis_2pc50.csv")
    kpis["tract_id"] = normalize_tract_id(kpis["tract_id"])
    kpis["T80"] = pd.to_numeric(kpis["T80"], errors="coerce")
    values = kpis["T80"].dropna()
    mapped = tracts.merge(kpis[["tract_id", "T80"]], on="tract_id", how="inner")

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(7.8)))
        gs = fig.add_gridspec(
            1,
            2,
            width_ratios=[0.92, 1.18],
            left=0.070,
            right=0.955,
            bottom=0.17,
            top=0.91,
            wspace=0.18,
        )
        ax_hist = fig.add_subplot(gs[0, 0])
        ax_map = fig.add_subplot(gs[0, 1])

        bins = np.linspace(values.min(), values.max(), 65)
        ax_hist.hist(
            values,
            bins=bins,
            color="#86a5cf",
            edgecolor="white",
            linewidth=0.25,
            alpha=0.82,
        )
        kde_ax = ax_hist.twinx()
        sns.kdeplot(
            x=values,
            ax=kde_ax,
            color="#315f9b",
            linewidth=1.4,
            bw_adjust=0.22,
            cut=0,
        )
        kde_ax.set_yticks([])
        kde_ax.set_ylabel("")
        kde_ax.spines["right"].set_visible(False)
        kde_ax.spines["top"].set_visible(False)
        kde_ax.spines["left"].set_visible(False)
        ax_hist.set_title("2pc50 T80 distribution", fontweight="bold", pad=4)
        ax_hist.set_xlabel("T80 (hr)")
        ax_hist.set_ylabel("Count")
        style_axis(ax_hist)

        mapped.plot(
            column="T80",
            ax=ax_map,
            cmap=TIME_CMAP,
            linewidth=0.18,
            edgecolor="white",
            vmin=float(values.min()),
            vmax=float(values.max()),
        )
        ax_map.set_title("2pc50 tract-level T80", fontweight="bold", pad=4)
        ax_map.set_axis_off()
        ax_map.set_aspect("equal")
        norm = mpl.colors.Normalize(vmin=float(values.min()), vmax=float(values.max()))
        sm = mpl.cm.ScalarMappable(norm=norm, cmap=TIME_CMAP)
        cbar = fig.colorbar(sm, ax=ax_map, fraction=0.040, pad=0.018)
        cbar.set_label("T80 (hr)", fontsize=8.0)
        cbar.ax.tick_params(labelsize=7.0, width=0.5, length=2.5)
        cbar.outline.set_linewidth(0.5)

        panel_label(ax_hist, "A", x=-0.14)
        panel_label(ax_map, "B", x=-0.03)
        save_pair(fig, "t80_distribution_and_spatial_pattern_composite")


RECOVERY_STYLES = {
    "S3_Mean": ("Theoretical limit", "#111111", "--", 1.55),
    "Impact λ2 first": ("Impact λ2 first", "#e41a1c", "-.", 1.05),
    "Betweenness first": ("Betweenness first", "#e6ab02", "-.", 1.05),
    "Impact population first": ("Impact (population) first", "#ff7f00", ":", 1.10),
    "Degree first": ("Degree first", "#4daf4a", "--", 1.05),
    "Closeness first": ("Closeness first", "#377eb8", "--", 1.05),
    "Hospital first": ("Hospital first", "#666666", ":", 1.05),
    "Random": ("Random baseline", "#c9c9c9", "-", 1.20),
    "GA-Balanced": ("GA (balanced)", "#6a51a3", "-", 1.15),
    "GA-HospitalFirst": ("GA (hospital-first)", "#dd3497", "-", 1.15),
    "GA-Efficiency": ("GA (efficiency)", "#1b9e77", "-", 1.15),
}

GRAPH_STYLES = {
    "S3_Mean": ("Theoretical limit", "#111111", "--", 1.35),
    "centrality-first": ("Impact λ2 first", "#e41a1c", "-.", 0.95),
    "betweenness-first": ("Betweenness first", "#e6ab02", "-.", 0.95),
    "impact-first": ("Impact (population) first", "#ff7f00", ":", 0.95),
    "degree-first": ("Degree first", "#4daf4a", "--", 0.95),
    "closeness-first": ("Closeness first", "#377eb8", "--", 0.95),
    "hospital-first": ("Hospital first", "#666666", ":", 0.95),
    "random": ("Random baseline", "#c9c9c9", "-", 1.05),
    "GA-Balanced": ("GA (balanced)", "#6a51a3", "-", 1.0),
    "GA-HospFirst": ("GA (hospital-first)", "#dd3497", "-", 1.0),
    "GA-Efficiency": ("GA (efficiency)", "#1b9e77", "-", 1.0),
}


def recovery_column(curves: pd.DataFrame, strategy: str) -> str | None:
    target = f"2pc50 | {strategy} | Population"
    return target if target in curves.columns else None


def plot_recovery_curves(ax: plt.Axes, curves: pd.DataFrame) -> None:
    time = pd.to_numeric(curves["time_hr"], errors="coerce")
    for strategy, (label, color, linestyle, width) in RECOVERY_STYLES.items():
        column = recovery_column(curves, strategy)
        if column is None:
            continue
        ax.plot(
            time,
            pd.to_numeric(curves[column], errors="coerce"),
            color=color,
            linestyle=linestyle,
            linewidth=width,
            label=label,
        )
    ax.set_xlim(0, 115)
    ax.set_ylim(-0.02, 1.04)
    ax.set_title("2pc50: population-weighted recovery", fontweight="bold", pad=4)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Functionality")
    style_axis(ax)
    legend = ax.legend(
        loc="lower right",
        frameon=False,
        ncol=1,
        fontsize=6.3,
        handlelength=2.1,
        labelspacing=0.24,
        borderaxespad=0.45,
    )
    for line in legend.get_lines():
        line.set_linewidth(1.35)


DISPLAY_STRATEGIES = {
    "GA-HospitalFirst": "GA hospital-first",
    "GA-Efficiency": "GA efficiency",
    "GA-Balanced": "GA balanced",
    "Random": "Random baseline",
    "Impact population first": "Impact population first",
    "Hospital first": "Hospital priority",
    "Degree first": "Degree first",
    "Closeness first": "Closeness first",
    "Impact λ2 first": "Impact (λ2) first",
    "Betweenness first": "Betweenness first",
    "Theoretical limit": "Theoretical limit",
}
STRATEGY_ORDER = list(DISPLAY_STRATEGIES)


def plot_t80_dumbbell(ax: plt.Axes, kpis: pd.DataFrame) -> None:
    data = kpis[kpis["scenario"].astype(str).eq("2pc50")].copy()
    wide = data.pivot_table(
        index="Strategy", columns="Weighting", values="T80", aggfunc="mean"
    )
    wide = wide.reindex(STRATEGY_ORDER).dropna(subset=["Pop", "SVI"], how="any")
    y = np.arange(len(wide)) + 1
    pop = wide["Pop"].to_numpy(float)
    svi = wide["SVI"].to_numpy(float)
    ax.hlines(y, np.minimum(pop, svi), np.maximum(pop, svi), color="#9e9e9e", lw=1.0)
    ax.scatter(pop, y, s=30, color="#1f77b4", edgecolor="white", lw=0.35, zorder=3)
    ax.scatter(svi, y, s=30, color="#ff7f0e", edgecolor="white", lw=0.35, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [DISPLAY_STRATEGIES[strategy] for strategy in wide.index],
        fontsize=7.0,
    )
    ax.set_ylim(len(wide) + 0.55, 0.30)
    all_values = np.r_[pop, svi]
    pad = max(1.0, (all_values.max() - all_values.min()) * 0.08)
    ax.set_xlim(max(0, all_values.min() - pad), all_values.max() + pad)
    ax.set_title(
        "2pc50 recovery-time comparison",
        fontweight="bold",
        pad=4,
        loc="left",
    )
    ax.set_xlabel("Recovery time T80 (hours)")
    style_axis(ax)
    ax.grid(axis="y", visible=False)
    handles = [
        Line2D([], [], marker="o", color="none", markerfacecolor="#1f77b4", markeredgecolor="white", label="Population-weighted"),
        Line2D([], [], marker="o", color="none", markerfacecolor="#ff7f0e", markeredgecolor="white", label="SVI-weighted"),
    ]
    ax.legend(
        handles=handles,
        loc="lower right",
        bbox_to_anchor=(1.0, 1.015),
        frameon=False,
        ncol=2,
        fontsize=7.0,
        borderaxespad=0,
        handletextpad=0.35,
        columnspacing=0.9,
    )


def graph_series() -> list[tuple[str, pd.DataFrame]]:
    series: list[tuple[str, pd.DataFrame]] = []
    baseline = STAGE3 / "graph_robustness_mean_2pc50.csv"
    if baseline.exists():
        series.append(("S3_Mean", pd.read_csv(baseline)))
    for rule in [
        "centrality-first",
        "betweenness-first",
        "impact-first",
        "degree-first",
        "closeness-first",
        "hospital-first",
        "random",
    ]:
        path = STAGE4 / f"rule_graphrobustness_2pc50_{rule}.csv"
        if path.exists():
            series.append((rule, pd.read_csv(path)))
    for policy, key in [
        ("Balanced", "GA-Balanced"),
        ("HospFirst", "GA-HospFirst"),
        ("Efficiency", "GA-Efficiency"),
    ]:
        path = STAGE5 / f"ga_graphrobustness_2pc50_{policy}.csv"
        if path.exists():
            series.append((key, pd.read_csv(path)))
    return series


def plot_graph_metric(ax: plt.Axes, metric: str, title: str, ylabel: str) -> None:
    for key, data in graph_series():
        if metric not in data.columns:
            continue
        label, color, linestyle, width = GRAPH_STYLES[key]
        ax.plot(
            pd.to_numeric(data["t"], errors="coerce"),
            pd.to_numeric(data[metric], errors="coerce"),
            label=label,
            color=color,
            linestyle=linestyle,
            linewidth=width,
        )
    ax.set_xlim(0, 96)
    if metric == "lcc_fraction":
        ax.set_ylim(-0.02, 1.04)
    ax.set_title(title, fontweight="bold", pad=4)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel(ylabel)
    style_axis(ax)


def make_recovery_composite() -> None:
    curves = pd.read_csv(STAGE6 / "recovery_curves_all_system.csv")
    kpis = pd.read_csv(STAGE6 / "recovery_kpis_all_system.csv")
    kpis["T80"] = pd.to_numeric(kpis["T80"], errors="coerce")

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(20.3)))
        gs = fig.add_gridspec(
            3,
            2,
            height_ratios=[0.92, 0.96, 1.08],
            left=0.17,
            right=0.985,
            bottom=0.135,
            top=0.975,
            hspace=0.52,
            wspace=0.31,
        )
        ax_a = fig.add_subplot(gs[0, :])
        ax_b = fig.add_subplot(gs[1, :])
        ax_c = fig.add_subplot(gs[2, 0])
        ax_d = fig.add_subplot(gs[2, 1])

        plot_recovery_curves(ax_a, curves)
        plot_t80_dumbbell(ax_b, kpis)
        plot_graph_metric(ax_c, "lcc_fraction", "2pc50: connectivity", "Giant component fraction")
        plot_graph_metric(ax_d, "avg_degree", "2pc50: average degree", "Average degree (k)")

        panel_label(ax_a, "A", x=-0.15, y=1.02)
        panel_label(ax_b, "B", x=-0.15, y=1.02)
        panel_label(ax_c, "C", x=-0.25, y=1.02)
        panel_label(ax_d, "D", x=-0.23, y=1.02)

        handles, labels = ax_c.get_legend_handles_labels()
        legend = fig.legend(
            handles,
            labels,
            loc="lower center",
            bbox_to_anchor=(0.55, 0.018),
            ncol=4,
            frameon=False,
            fontsize=6.8,
            handlelength=2.0,
            columnspacing=1.1,
            labelspacing=0.35,
        )
        for line in legend.get_lines():
            line.set_linewidth(1.2)
        save_pair(fig, "recovery_strategy_and_topology_composite")


FEATURES = [
    ("T80", "Recovery time (T80)"),
    ("Pre_1970_Ratio", "Pre-1970 housing"),
    ("Pop_Density", "Population density"),
    ("NRI_RISK_SCORE", "NRI risk score"),
    ("NRI_BUILDVALUE", "Building value"),
    ("SVI_Composite", "SVI composite"),
]


def stage7_data() -> pd.DataFrame:
    data = pd.read_csv(STAGE7 / "clusters_labels_final.csv")
    data["tract_id"] = normalize_tract_id(data["tract_id"])
    data["cluster"] = data["cluster"].astype(str).str.replace(r"\.0$", "", regex=True)
    for feature, _ in FEATURES:
        data[feature] = pd.to_numeric(data[feature], errors="coerce")
    return data


def plot_kde_block(
    fig: plt.Figure,
    subspec,
    data: pd.DataFrame,
    cluster_counts: pd.Series,
) -> list[plt.Axes]:
    inner = subspec.subgridspec(
        3,
        3,
        height_ratios=[1.0, 1.0, 0.16],
        hspace=0.78,
        wspace=0.40,
    )
    axes: list[plt.Axes] = []
    cluster_order = sorted(data["cluster"].dropna().unique(), key=int)
    log_features = {"Pop_Density", "NRI_BUILDVALUE"}
    for index, (feature, label) in enumerate(FEATURES):
        ax = fig.add_subplot(inner[index // 3, index % 3])
        axes.append(ax)
        for cluster in cluster_order:
            subset = data.loc[data["cluster"].eq(cluster), feature].dropna()
            if subset.empty:
                continue
            x_values = np.log1p(subset.clip(lower=0)) if feature in log_features else subset
            sns.kdeplot(
                x=x_values,
                ax=ax,
                color=CLUSTER_COLORS.get(cluster, "#555555"),
                linewidth=1.05,
                common_norm=False,
                fill=False,
                warn_singular=False,
                bw_adjust=0.85 if feature != "T80" else 0.55,
                cut=0,
            )
            ax.axvline(
                float(np.median(x_values)),
                color=CLUSTER_COLORS.get(cluster, "#555555"),
                linestyle="--",
                linewidth=0.65,
                alpha=0.8,
            )
        title = f"{label}\n(log scale)" if feature in log_features else label
        ax.set_title(title, fontsize=6.8, fontweight="normal", pad=2)
        ax.set_xlabel("")
        ax.set_ylabel("Density" if index % 3 == 0 else "", fontsize=6.8)
        ax.tick_params(labelsize=6.4, length=2.2)
        style_axis(ax)
        sns.despine(ax=ax)
        if feature == "Pop_Density":
            ax.set_xticks(np.log1p([0, 10_000, 100_000]))
            ax.set_xticklabels(["0", "10k", "100k"])
        elif feature == "NRI_BUILDVALUE":
            ax.set_xticks(np.log1p([1e6, 1e8, 1e9]))
            ax.set_xticklabels(["1M", "100M", "1B"])

    legend_ax = fig.add_subplot(inner[2, :])
    legend_ax.axis("off")
    handles = [
        Line2D(
            [],
            [],
            color=CLUSTER_COLORS[str(cluster)],
            lw=1.5,
            label=f"C{cluster} (n={int(cluster_counts.get(str(cluster), 0))})",
        )
        for cluster in range(1, 7)
    ]
    handles.append(
        Line2D([], [], color="#222222", lw=0.9, ls="--", label="cluster median")
    )
    legend_ax.legend(
        handles=handles,
        loc="center",
        frameon=False,
        ncol=4,
        fontsize=6.5,
        handlelength=1.25,
        columnspacing=0.8,
        labelspacing=0.25,
        handletextpad=0.3,
    )
    return axes


def plot_cluster_heatmap(ax: plt.Axes, data: pd.DataFrame) -> None:
    features = [feature for feature, _ in FEATURES]
    grouped = data.groupby("cluster")[features].mean().sort_index(key=lambda index: index.astype(int))
    zscore = (grouped - grouped.mean()) / grouped.std().replace(0, 1)
    display_names = [
        "Recovery time",
        "Pre-1970 housing",
        "Population density",
        "NRI risk",
        "Building value",
        "SVI composite",
    ]
    sns.heatmap(
        zscore.T,
        ax=ax,
        cmap="coolwarm",
        center=0,
        annot=True,
        fmt=".1f",
        annot_kws={"fontsize": 6.3},
        linewidths=0.35,
        linecolor="white",
        cbar_kws={"label": "Profile z-score", "shrink": 0.82, "pad": 0.035},
    )
    ax.set_xticklabels(
        [f"C{cluster}" for cluster in zscore.index],
        rotation=0,
        fontsize=6.8,
    )
    ax.set_yticklabels(display_names, rotation=0, fontsize=6.5)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(length=0)
    colorbar = ax.collections[0].colorbar
    colorbar.ax.tick_params(labelsize=6.5, length=2)
    colorbar.set_label("Profile z-score", fontsize=7.0)
    colorbar.outline.set_linewidth(0.4)


def set_map_extent(ax: plt.Axes, bounds: tuple[float, float, float, float]) -> None:
    xmin, ymin, xmax, ymax = bounds
    dx = xmax - xmin
    dy = ymax - ymin
    ax.set_xlim(xmin - 0.018 * dx, xmax + 0.018 * dx)
    ax.set_ylim(ymin - 0.018 * dy, ymax + 0.018 * dy)
    ax.set_aspect("equal", adjustable="box")
    ax.set_anchor("C")


def plot_cluster_map(
    ax: plt.Axes,
    mapped: gpd.GeoDataFrame,
    bounds: tuple[float, float, float, float],
) -> None:
    for cluster in sorted(mapped["cluster"].dropna().unique(), key=int):
        subset = mapped[mapped["cluster"].eq(cluster)]
        subset.plot(
            ax=ax,
            color=CLUSTER_COLORS.get(cluster, "#999999"),
            edgecolor="white",
            linewidth=0.10,
        )
    top10 = mapped[mapped["SlowVulnerable_Hotspot_Top10"].fillna(False).astype(bool)]
    if not top10.empty:
        top10.boundary.plot(ax=ax, color="#222222", linewidth=0.65)
    set_map_extent(ax, bounds)
    ax.set_axis_off()
    ax.legend(
        handles=[
            Line2D(
                [],
                [],
                color="#222222",
                lw=0.8,
                label="Top-10 hotspot boundary",
            )
        ],
        loc="upper right",
        bbox_to_anchor=(0.99, 0.99),
        frameon=True,
        facecolor="white",
        framealpha=0.88,
        edgecolor="none",
        ncol=1,
        fontsize=6.5,
        handlelength=1.4,
        handletextpad=0.25,
    )


def plot_hotspot_map(
    fig: plt.Figure,
    ax: plt.Axes,
    mapped: gpd.GeoDataFrame,
    bounds: tuple[float, float, float, float],
) -> None:
    score = pd.to_numeric(mapped["SlowVulnerable_Hotspot_Score"], errors="coerce")
    vmin = float(score.min())
    vmax = float(score.max())
    mapped.plot(
        column="SlowVulnerable_Hotspot_Score",
        ax=ax,
        cmap=HOTSPOT_CMAP,
        vmin=vmin,
        vmax=vmax,
        edgecolor="white",
        linewidth=0.10,
    )
    top10 = mapped[mapped["SlowVulnerable_Hotspot_Top10"].fillna(False).astype(bool)]
    if not top10.empty:
        top10.boundary.plot(ax=ax, color="#222222", linewidth=0.65)
    set_map_extent(ax, bounds)
    ax.set_axis_off()
    sm = mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax), cmap=HOTSPOT_CMAP)
    cax = inset_axes(
        ax,
        width="58%",
        height="4.5%",
        loc="lower center",
        bbox_to_anchor=(0.0, -0.015, 1.0, 1.0),
        bbox_transform=ax.transAxes,
        borderpad=0,
    )
    cbar = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cbar.set_label("Recovery-vulnerability hotspot score", fontsize=7.0)
    cbar.ax.tick_params(labelsize=6.5, length=2, pad=1)
    cbar.outline.set_linewidth(0.4)


def make_stage7_composite(tracts: gpd.GeoDataFrame) -> None:
    data = stage7_data()
    mapped = tracts.merge(data, on="tract_id", how="inner")
    cluster_counts = data["cluster"].value_counts().sort_index(key=lambda index: index.astype(int))

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(17.6)))
        outer = fig.add_gridspec(
            2,
            2,
            width_ratios=[1.0, 1.0],
            height_ratios=[1.14, 1.0],
            left=0.055,
            right=0.965,
            bottom=0.045,
            top=0.955,
            hspace=0.27,
            wspace=0.30,
        )

        kde_axes = plot_kde_block(fig, outer[0, 0], data, cluster_counts)
        ax_heat = fig.add_subplot(outer[0, 1])
        ax_clusters = fig.add_subplot(outer[1, 0])
        ax_hotspots = fig.add_subplot(outer[1, 1])

        plot_cluster_heatmap(ax_heat, data)
        map_bounds = tuple(mapped.total_bounds)
        plot_cluster_map(ax_clusters, mapped, map_bounds)
        plot_hotspot_map(fig, ax_hotspots, mapped, map_bounds)

        panel_label(kde_axes[0], "A", x=-0.28, y=1.10)
        panel_label(ax_heat, "B", x=-0.32, y=1.08)
        panel_label(ax_clusters, "C", x=-0.06, y=1.02)
        panel_label(ax_hotspots, "D", x=-0.07, y=1.02)
        save_pair(fig, "recovery_vulnerability_typology_composite")


def main() -> None:
    tracts = load_tracts()
    make_t80_composite(tracts)
    make_recovery_composite()
    make_stage7_composite(tracts)


if __name__ == "__main__":
    main()
