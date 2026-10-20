"""Render source-terminal reliability panels from existing frozen result tables.

No fragility, Monte Carlo, schedule, mapping, or recovery calculation occurs.
The retained July visualizer owns typography, physical sizing, and export.
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import la_grid.plotting.Project_Visualizer as july
from la_grid.paths import REPO_ROOT as ROOT
DATA = ROOT / "Data"
CANONICAL = ROOT / "provenance" / "reviewer_working" / "meeting_preparation_20260929"

STATION_CSV = ROOT / "results" / "diagnostics" / "SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv"
DYNAMIC_CSV = ROOT / "results" / "diagnostics" / "SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv"
DYNAMIC_STATION_CSV = ROOT / "results" / "diagnostics" / "SOURCE_TERMINAL_DYNAMIC_STATION_2PC50.csv"
TRACT_CSV = ROOT / "results" / "diagnostics" / "SOURCE_TERMINAL_TRACT_RELIABILITY_2PC50.csv"

SCHEDULED = (
    "centrality-first", "impact-first", "betweenness-first", "degree-first",
    "closeness-first", "hospital-first", "random", "vulnerability-first",
)
STRATEGY_DISPLAY = {
    "centrality-first": "Centrality-first",
    "impact-first": "Impact-first",
    "betweenness-first": "Betweenness-first",
    "degree-first": "Degree-first",
    "closeness-first": "Closeness-first",
    "hospital-first": "Hospital-first",
    "random": "Random",
    "vulnerability-first": "Vulnerability-first",
}


def _inputs():
    station = pd.read_csv(STATION_CSV, dtype={"station_id": str})
    dynamic = pd.read_csv(DYNAMIC_CSV)
    dynamic_station = pd.read_csv(DYNAMIC_STATION_CSV, dtype={"station_id": str})
    tract = pd.read_csv(TRACT_CSV, dtype={"tract_id": str})
    if len(station) != 92 or station.station_id.nunique() != 92:
        raise ValueError("Static station table is not the retained 92-station result")
    if len(tract) != 2315:
        raise ValueError("Tract reliability table is not the retained study domain")
    if set(dynamic.strategy) != set(SCHEDULED) | {"unconstrained"}:
        raise ValueError("Frozen dynamic strategy set differs")
    if dynamic.duplicated(["strategy", "time_hr"]).any():
        raise ValueError("Duplicate strategy-time reliability result")
    if not dynamic_station.loc[dynamic_station.functional_count.eq(0),
                               "R_path_full_conditional"].isna().all():
        raise ValueError("Undefined station conditional reliability must be NA")
    expected = dynamic.population_dependency_weighted_fixed_precomputed_best_path_connection + \
        dynamic.population_dependency_weighted_full_minus_fixed_precomputed_best_path
    if not np.allclose(dynamic.population_dependency_weighted_R_conn, expected, atol=1e-12):
        raise ValueError("Frozen dynamic full/fixed-path accounting differs")
    return station, dynamic


def _export(fig, stem: str):
    CANONICAL.mkdir(parents=True, exist_ok=True)
    july.save_plot(fig, str(CANONICAL), stem + ".png")
    for suffix in (".png", ".pdf"):
        source = CANONICAL / (stem + suffix)
        if not source.is_file() or source.stat().st_size == 0:
            raise ValueError(f"Figure export missing: {source}")


def _style_for(strategy: str):
    # One extension to the established July palette for the reviewer amendment.
    if strategy == "vulnerability-first":
        return {"label": "Vulnerability first", "color": "#a65628", "ls": "-"}
    return july.STAGE6_RECOVERY_STYLE_CONFIG[strategy]


def full_vs_best_path(station):
    rows = station.loc[~station.is_core_source].copy()
    assert len(rows) == 78 and rows.R_best_path.gt(0).all()
    assert (rows.R_path_full + 1e-14 >= rows.R_best_path).all()
    top = rows.nlargest(7, "Delta_R_redundancy").iloc[::-1]

    fig = plt.figure(figsize=july.get_figsize("COMPOSITE_FULL_DEFAULT", height_cm=9.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.28, 1.0],
                          left=.11, right=.98, bottom=.17, top=.87, wspace=.62)
    ax = fig.add_subplot(gs[0, 0]); ax2 = fig.add_subplot(gs[0, 1])
    sizes = 11 + 65 * np.sqrt(rows.population_dependency_weight.clip(lower=0))
    ax.scatter(rows.R_best_path, rows.R_path_full, s=sizes,
               color="#377eb8", edgecolor="white", linewidth=.35, alpha=.50, zorder=3)
    lower = 1e-11; upper = 1e-1
    ax.plot([lower, upper], [lower, upper], color="#555555", lw=.8,
            ls="--", label="1:1 reference", zorder=2)
    ax.set(xscale="log", yscale="log", xlim=(lower, upper), ylim=(lower, upper))
    log_ticks = np.array([1e-11, 1e-9, 1e-7, 1e-5, 1e-3, 1e-1])
    # Plain scientific notation keeps every glyph in Arial at the full tick size.
    log_labels = ["1e-11", "1e-9", "1e-7", "1e-5", "1e-3", "1e-1"]
    ax.set_xticks(log_ticks, log_labels)
    ax.set_yticks(log_ticks, log_labels)
    july.style_axis(ax, title="A  Full network vs fixed best path",
                    xlabel="Fixed most-reliable path probability (log scale)",
                    ylabel="Full-network conditional reliability (log scale)")
    ax.tick_params(axis="both", which="major", labelsize=july.FS_TICK)
    ax.grid(True, which="major", color="#dedede", lw=.4)
    ax.grid(True, which="minor", color="#eeeeee", lw=.25)
    july.format_legend(ax.legend(loc="upper left"))

    ax2.plot(top.Delta_R_redundancy, range(len(top)), "o", color="#ff7f00", ms=3.5)
    for j, gain in enumerate(top.Delta_R_redundancy):
        ax2.plot([0, gain], [j, j], color="#b0b0b0", lw=.7, zorder=1)
    station_labels = top.station_name.str.title().str.replace(
        "Wilmington (Station C)", "Wilmington C", regex=False)
    ax2.set_yticks(range(len(top)), station_labels)
    ax2.axvline(0, color="#555555", lw=.6)
    ax2.set_xlim(left=0, right=float(top.Delta_R_redundancy.max()) * 1.12)
    july.style_axis(ax2, title="B  Largest alternative-route gains",
                    xlabel="Full network minus fixed path probability",
                    ylabel="Substation")
    ax2.tick_params(axis="y", labelsize=july.FS_TICK)
    ax2.grid(axis="x", color="#dedede", lw=.4)
    fig.suptitle("Full-network source-terminal reliability versus fixed most-reliable single-path reference\nunder 2pc50 station fragility",
                 fontsize=july.FS_SUPTITLE, y=.985)
    _export(fig, "vis_source_reliability_full_vs_best_path_2pc50")


def dynamic_redundancy(dynamic):
    data = dynamic[dynamic.time_hr.le(120)].copy()
    fig = plt.figure(figsize=july.get_figsize("COMPOSITE_FULL_DENSE", height_cm=13.0))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.05], left=.14, right=.97,
                          bottom=.22, top=.94, hspace=.36)
    a = fig.add_subplot(gs[0, 0]); b = fig.add_subplot(gs[1, 0], sharex=a)
    for strategy in ("impact-first", "hospital-first"):
        d = data[data.strategy.eq(strategy)].sort_values("time_hr")
        style = _style_for(strategy); color = style["color"]
        label = STRATEGY_DISPLAY[strategy]
        a.plot(d.time_hr, d.population_dependency_weighted_R_conn,
               color=color, ls="-", lw=1.2, marker="o", ms=2.4,
               label=f"{label}: full network")
        a.plot(d.time_hr,
               d.population_dependency_weighted_fixed_precomputed_best_path_connection,
               color=color, ls="--", lw=1.2, marker="o", ms=2.4,
               label=f"{label}: fixed path")
    july.style_axis(a, title="A  Full source access and fixed-path reference",
                    ylabel="Joint source-connected probability\n(population-dependency weighted)")
    a.set_ylim(-.02, 1.04)
    july.format_legend(a.legend(loc="lower right", ncol=2))
    for strategy in SCHEDULED:
        d = data[data.strategy.eq(strategy)].sort_values("time_hr")
        style = _style_for(strategy)
        b.plot(d.time_hr,
               d.population_dependency_weighted_full_minus_fixed_precomputed_best_path,
               color=style["color"], ls=style["ls"], lw=1.15,
               marker="o", ms=2.2, markeredgecolor="#444444", markeredgewidth=.25,
               label=STRATEGY_DISPLAY[strategy])
    july.style_axis(b, title="B  Alternative-route contribution during recovery",
                    xlabel="Time after earthquake (h)",
                    ylabel="Population-dependency-weighted\nalternative-route contribution")
    b.set(xlim=(0, 120), ylim=(-.005, .235), xticks=[0, 24, 48, 72, 96, 120])
    for ax in (a, b):
        for hour in (24, 48):
            ax.axvline(hour, color="#b9b9b9", lw=.55, ls="--", zorder=0)
        ax.grid(True, color="#e3e3e3", lw=.4)
    july.format_legend(b.legend(loc="upper center", bbox_to_anchor=(.5, -.19),
                                ncol=4, frameon=True))
    _export(fig, "vis_source_reliability_dynamic_redundancy_2pc50")


def station_map(station):
    nodes = pd.read_csv(DATA / "substation_graph_CEC_nodes_expanded.csv", dtype={"id": str})
    edges = pd.read_csv(DATA / "substation_graph_CEC_edges_expanded.csv", dtype={"u": str, "v": str})
    core = pd.read_csv(DATA / "source_nodes_core_expanded.csv", dtype={"ID": str})
    core_ids = set(core.loc[core.level.eq("Core"), "ID"])
    assert len(nodes) == 92 and len(edges) == 318 and len(core_ids) == 14
    assert set(nodes.id) == set(station.station_id)
    geo = gpd.read_file(DATA / "LA_Tracts_With_Population.shp")
    accepted = pd.read_csv(DATA / "Tracts_Within_Expanded_Area.csv", dtype={"GEOID": str})
    geo = geo.loc[geo.GEOID.astype(str).str.zfill(11).isin(
        set(accepted.GEOID.astype(str).str.zfill(11)))].copy()
    assert len(geo) == 2315
    boundary = geo.geometry.union_all() if hasattr(geo.geometry, "union_all") else geo.geometry.unary_union
    gdf = gpd.GeoDataFrame(geometry=[boundary], crs=geo.crs).to_crs(4326)
    node = nodes.merge(station, left_on="id", right_on="station_id", validate="one_to_one")
    non = node[~node.is_core_source].copy()
    sources = node[node.is_core_source].copy()
    assert len(non) == 78 and len(sources) == 14 and set(sources.id) == core_ids
    xy = nodes.set_index("id")[["lon", "lat"]]

    # Label only the three largest gains, on the gain panel, using deliberate
    # callout positions.  The five largest stations are geographically dense;
    # automatic text repulsion at this panel size left several labels touching.
    label_rows = non.nlargest(3, "Delta_R_redundancy")

    fig, axes = plt.subplots(1, 2, figsize=july.get_figsize("COMPOSITE_FULL_DEFAULT", height_cm=10.2))
    fig.subplots_adjust(left=.07, right=.99, top=.90, bottom=.24, wspace=.10)
    specs = [
        ("R_path_full", "A  Full-network conditional reachability", "YlGnBu",
         "Conditional source-path reliability (0–1)"),
        ("Delta_R_redundancy", "B  Alternative-route gain", "OrRd",
         "Additional source-path reliability from alternate routes"),
    ]
    xmin, ymin, xmax, ymax = gdf.total_bounds
    dx, dy = xmax - xmin, ymax - ymin
    for ax, (column, title, cmap, colorbar_label) in zip(axes, specs):
        gdf.boundary.plot(ax=ax, color="#a0a0a0", linewidth=.65, zorder=1)
        for e in edges.itertuples(index=False):
            ax.plot([xy.at[e.u, "lon"], xy.at[e.v, "lon"]],
                    [xy.at[e.u, "lat"], xy.at[e.v, "lat"]],
                    color="#a8a8a8", lw=.38, alpha=.38, zorder=2)
        values = non[column].to_numpy(float)
        norm = mcolors.Normalize(vmin=0, vmax=float(values.max()))
        im = ax.scatter(non.lon, non.lat, c=values, cmap=cmap, norm=norm,
                        s=18, edgecolor="white", linewidth=.25, zorder=3)
        ax.scatter(sources.lon, sources.lat, marker="^", s=27,
                   facecolor="white", edgecolor="#282828", linewidth=.65,
                   label="Core source", zorder=5)
        if column == "Delta_R_redundancy":
            callouts = {
                "310179": ((-12, 20), "right"),  # Wilmington (Station C)
                "300390": ((22, 12), "left"),     # Hinson
                "303371": ((10, 8), "left"),      # Goodrich
            }
            for row in label_rows.itertuples(index=False):
                offset, align = callouts.get(row.station_id, ((8, 8), "left"))
                label = ("Wilmington (C)" if row.station_id == "310179"
                         else str(row.station_name).title())
                ax.annotate(
                    label, (row.lon, row.lat),
                    xytext=offset, textcoords="offset points", ha=align,
                    fontsize=july.FS_ANNOTATION, fontweight="semibold",
                    color="#252525", zorder=7,
                    arrowprops=dict(arrowstyle="-", color="#555555", lw=.45,
                                    shrinkA=1, shrinkB=2),
                    bbox=dict(facecolor="white", edgecolor="none", alpha=.82, pad=.22),
                )
        ax.set_xlim(xmin-.035*dx, xmax+.035*dx)
        ax.set_ylim(ymin-.035*dy, ymax+.035*dy)
        ax.set_aspect(1/np.cos(np.deg2rad((ymin+ymax)/2)))
        july.style_axis(ax, title=title, ylabel="Latitude")
        cbar = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=.045,
                            pad=.12, shrink=.88)
        july.style_colorbar(cbar, label=colorbar_label)
        july.format_legend(ax.legend(loc="lower left"))
    fig.supxlabel("Longitude", y=.055, fontsize=july.FS_LABEL)
    _export(fig, "vis_source_reliability_station_map_2pc50")

def main():
    july.apply_publication_style()
    station, dynamic = _inputs()
    full_vs_best_path(station)
    dynamic_redundancy(dynamic)
    station_map(station)


if __name__ == "__main__":
    main()
