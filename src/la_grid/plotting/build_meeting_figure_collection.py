"""Build the meeting-preparation figure collection from frozen result tables.

This is presentation-only. It does not calculate or change a scientific model,
trajectory, schedule, GA result, cluster assignment, or inferential statistic.
"""
from __future__ import annotations

import csv
import hashlib
import os
import shutil
from pathlib import Path

import fitz
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import la_grid.plotting.Project_Visualizer as july
from la_grid.paths import REPO_ROOT as ROOT

LEGACY = ROOT / "provenance" / "reviewer_working" / "meeting_preparation_20260929"
OUT = Path(os.environ.get("LA_GRID_MEETING_FIGURE_DRAFT_DIR", str(ROOT / "provenance" / "artwork_drafts")))
FORMAL = ROOT / "Formal_Experiment_20260923"
SUITE = ROOT / "results" / "revised_suite" / "LA_Grid_Revised_Suite_20260925"
STAGE7 = FORMAL / "Stage 7 Output_SOVI_Harmonized"
CM = 1 / 2.54

STRATEGIES = ["impact-first", "hospital-first", "vulnerability-first", "degree-first"]
STRATEGY_LABELS = {
    "impact-first": "Impact-first", "hospital-first": "Hospital-first",
    "vulnerability-first": "Vulnerability-first", "degree-first": "Degree-first",
    "centrality-first": "Centrality-first", "betweenness-first": "Betweenness-first",
    "closeness-first": "Closeness-first", "random": "Random",
    "unconstrained": "Unconstrained",
}
STRATEGY_COLORS = {
    "impact-first": "#ff7f00", "hospital-first": "#555555",
    "vulnerability-first": "#a65628", "degree-first": "#4daf4a",
    "unconstrained": "#111111",
    "centrality-first": "#e41a1c", "betweenness-first": "#b59a00",
    "closeness-first": "#377eb8", "random": "#9a9a9a",
}
STRATEGY_LINES = {
    "impact-first": ":", "hospital-first": (0, (2.2, 1.4)),
    "vulnerability-first": "-", "degree-first": "--", "unconstrained": "--",
    "centrality-first": "-.", "betweenness-first": (0, (5, 1.5, 1.2, 1.5)),
    "closeness-first": (0, (4, 1.6)), "random": "-",
}
ARIAL_BOLD: Path | None = None


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def configure() -> None:
    global ARIAL_BOLD
    font_path = font_manager.findfont("Arial", fallback_to_default=False)
    if not font_path.lower().endswith(("arial.ttf", "arialbd.ttf")):
        raise RuntimeError(f"Publication figures require installed Arial, found {font_path}")
    ARIAL_BOLD = Path(font_manager.findfont(font_manager.FontProperties(family="Arial", weight="bold"), fallback_to_default=False))
    july.apply_publication_style()
    matplotlib.rcParams.update({
        "font.family": "Arial", "font.sans-serif": ["Arial"],
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "pdf.use14corefonts": False, "savefig.dpi": 600,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })
    OUT.mkdir(parents=True, exist_ok=True)


def style_axis(ax, *, title=None, xlabel=None, ylabel=None) -> None:
    july.style_axis(ax, title=title, xlabel=xlabel, ylabel=ylabel,
                    title_size=july.FS_TITLE, label_size=july.FS_LABEL)
    ax.grid(True, color="#e4e4e4", linewidth=.4, linestyle="--", alpha=.68)
    ax.set_axisbelow(True)


def save_figure(fig, stem: str) -> None:
    pdf = OUT / f"{stem}.pdf"
    png = OUT / f"{stem}.png"
    fig.savefig(pdf, format="pdf", bbox_inches="tight", pad_inches=.04,
                facecolor="white", metadata={"Creator": "LA Grid presentation-only renderer"})
    fig.savefig(png, format="png", dpi=600, bbox_inches="tight", pad_inches=.04,
                facecolor="white")
    plt.close(fig)


def original(name: str) -> Path:
    return LEGACY / name


def copy_pair(old_stem: str, new_stem: str, *, source_dir: Path | None = None) -> None:
    source_dir = source_dir or LEGACY
    for suffix in (".pdf", ".png"):
        src = source_dir / (old_stem + suffix)
        if not src.is_file():
            raise FileNotFoundError(src)
        shutil.copy2(src, OUT / (new_stem + suffix))


def combine_pdf_panels(stem: str, panels: list[tuple[str, Path]]) -> None:
    """Stack native-size vector pages; no source panel is scaled or rasterized."""
    docs = []
    pages = []
    width = 0.0
    heights = []
    for title, path in panels:
        doc = fitz.open(path)
        if doc.page_count < 1:
            raise ValueError(f"Empty panel PDF: {path}")
        page = doc[0]
        docs.append(doc)
        pages.append((title, doc, page))
        width = max(width, float(page.rect.width))
        heights.append(float(page.rect.height))
    label_heights = [14.0 if title else 0.0 for title, _, _ in pages]
    gap = 4.0
    outdoc = fitz.open()
    page = outdoc.new_page(width=width, height=sum(heights) + sum(label_heights) + gap * (len(panels) - 1))
    page.insert_font(fontname="ArBold", fontfile=str(ARIAL_BOLD))
    y = 0.0
    for (title, doc, src_page), h, label_h in zip(pages, heights, label_heights):
        if title:
            page.insert_text((8.0, y + 9.5), title, fontname="ArBold", fontsize=8.2,
                             color=(.1, .1, .1), overlay=True)
        rect = fitz.Rect((width - src_page.rect.width) / 2, y + label_h,
                         (width + src_page.rect.width) / 2, y + label_h + src_page.rect.height)
        page.show_pdf_page(rect, doc, 0, keep_proportion=True, overlay=True)
        y += label_h + h + gap
    pdf_path = OUT / f"{stem}.pdf"
    outdoc.save(pdf_path, garbage=4, deflate=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(600 / 72, 600 / 72), alpha=False)
    pix.set_dpi(600, 600)
    pix.save(OUT / f"{stem}.png")
    outdoc.close()
    for doc in docs:
        doc.close()


def plot_supp_fig07_station_map() -> Path:
    """Display frozen station reliabilities on the formal expanded tract footprint."""
    tracts = tract_geometry()
    nodes = pd.read_csv(ROOT / "Data/substation_graph_CEC_nodes_expanded.csv", dtype={"id": str})
    edges = pd.read_csv(ROOT / "Data/substation_graph_CEC_edges_expanded.csv", dtype={"u": str, "v": str})
    station = pd.read_csv(ROOT / "results/diagnostics/SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv",
                          dtype={"station_id": str})
    if len(nodes) != 92 or len(edges) != 318 or len(station) != 92:
        raise ValueError("Frozen 92/318 reliability map identity mismatch")
    points = map_points(nodes, tracts.crs).merge(station, left_on="id", right_on="station_id",
                                                 validate="one_to_one")
    non = points.loc[~points.is_core_source].copy()
    core = points.loc[points.is_core_source].copy()
    if len(non) != 78 or len(core) != 14:
        raise ValueError("Expected 78 non-source and 14 Core-source stations")
    lookup = points.set_index("id").geometry
    fig, axes = plt.subplots(1, 2, figsize=(18.5 * CM, 7.6 * CM))
    specifications = [
        ("R_path_full", "C. Full-network conditional reachability", "YlGnBu",
         "Conditional source-path reliability"),
        ("Delta_R_redundancy", "D. Alternative-route gain", "YlOrRd",
         "Additional reliability from alternate routes"),
    ]
    for ax, (column, title, palette, scale_label) in zip(axes, specifications):
        draw_tract_base(ax, tracts)
        for edge in edges.itertuples(index=False):
            if edge.u in lookup.index and edge.v in lookup.index:
                a, b = lookup.loc[edge.u], lookup.loc[edge.v]
                ax.plot([a.x, b.x], [a.y, b.y], color="#9ca5aa", lw=.36, alpha=.38, zorder=2)
        scatter = ax.scatter(non.geometry.x, non.geometry.y, c=non[column], cmap=palette,
                             vmin=0, vmax=float(non[column].max()), s=24,
                             edgecolors="white", linewidths=.32, zorder=3)
        ax.scatter(core.geometry.x, core.geometry.y, marker="^", s=37,
                   facecolors="white", edgecolors="#252525", linewidths=.68, zorder=4)
        ax.set_title(title, fontsize=july.FS_TITLE, weight="bold", pad=5)
        cbar = fig.colorbar(scatter, ax=ax, orientation="horizontal", fraction=.045, pad=.025,
                            shrink=.82)
        cbar.set_label(scale_label, fontsize=7.1)
        cbar.ax.tick_params(labelsize=7.0, width=.5, length=2)
        cbar.outline.set_linewidth(.5)
    fig.legend(handles=[Line2D([], [], marker="^", color="none", markerfacecolor="white",
                               markeredgecolor="#252525", markersize=5, label="Core source")],
               loc="lower center", bbox_to_anchor=(.5, .005), frameon=False, fontsize=7.1)
    fig.subplots_adjust(left=.015, right=.985, bottom=.16, top=.91, wspace=.035)
    path = OUT / "_FigS07_expanded_station_map.pdf"
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=.025,
                facecolor="white", metadata={"Creator": "LA Grid presentation-only renderer"})
    plt.close(fig)
    return path


def tract_geometry() -> gpd.GeoDataFrame:
    path = ROOT / "Data" / "LA_Tracts_With_Population.shp"
    g = gpd.read_file(path)
    if "GEOID" not in g.columns:
        raise ValueError("Expected full study-area tract GEOID in retained geometry")
    g["tract_id_norm"] = g.GEOID.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    # The retained geometry file contains more county tracts than the formal
    # study domain. Use frozen M1 IDs to keep every map on the same 2,315 tracts.
    mapping = pd.read_csv(ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv", dtype={"tract_id": str})
    ids = set(mapping.tract_id.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11))
    g = g[g.tract_id_norm.isin(ids)].copy()
    if len(g) != 2315:
        raise ValueError(f"Expected expanded study area of 2,315 tracts, found {len(g)}")
    return g


def map_points(nodes: pd.DataFrame, target_crs) -> gpd.GeoDataFrame:
    from shapely.geometry import Point
    p = gpd.GeoDataFrame(nodes.copy(), geometry=gpd.points_from_xy(nodes.lon, nodes.lat), crs="EPSG:4326")
    return p.to_crs(target_crs)


def draw_tract_base(ax, g: gpd.GeoDataFrame, colors=None) -> None:
    if colors is None:
        g.plot(ax=ax, color="#f7f7f7", edgecolor="#c9c9c9", linewidth=.12, zorder=1)
    else:
        g.assign(_fill=colors).plot(ax=ax, color=colors, edgecolor="#c9c9c9", linewidth=.12, zorder=1)
    ax.set_axis_off()
    ax.set_aspect("equal")


def plot_fig02() -> None:
    tracts = tract_geometry()
    nodes = pd.read_csv(ROOT / "Data" / "substation_graph_CEC_nodes_expanded.csv", dtype={"id": str})
    nodes["id"] = nodes.id.astype(str)
    edges = pd.read_csv(ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv", dtype={"u": str, "v": str})
    edges["u"], edges["v"] = edges.u.astype(str), edges.v.astype(str)
    core = pd.read_csv(ROOT / "Data" / "source_nodes_core_expanded.csv", dtype={"ID": str})
    core = set(core.loc[core.level.eq("Core"), "ID"].astype(str))
    if len(nodes) != 92 or len(edges) != 318 or len(core) != 14:
        raise ValueError("System map frozen topology identity does not match 92/318/14")
    points = map_points(nodes, tracts.crs).set_index("id")
    mapping = pd.read_csv(ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv", dtype={"tract_id": str, "substation_id": str})
    counts = mapping.groupby("tract_id").substation_id.nunique().rename("links")
    tracts = tracts.merge(counts, left_on="tract_id_norm", right_index=True, how="left")
    tracts["links"] = tracts.links.fillna(0).astype(int)
    fig, axes = plt.subplots(1, 2, figsize=(18.5 * CM, 7.8 * CM))
    ax = axes[0]
    draw_tract_base(ax, tracts)
    for row in edges.itertuples(index=False):
        if row.u in points.index and row.v in points.index:
            a, b = points.loc[row.u].geometry, points.loc[row.v].geometry
            ax.plot([a.x, b.x], [a.y, b.y], color="#8c9298", lw=.45, alpha=.68, zorder=2)
    pts = points.reset_index()
    non = pts[~pts.id.isin(core)]
    src = pts[pts.id.isin(core)]
    ax.scatter(non.geometry.x, non.geometry.y, s=8, c="#3b6b8e", edgecolors="white", linewidths=.28, zorder=3)
    ax.scatter(src.geometry.x, src.geometry.y, s=21, marker="^", c="#222222", edgecolors="white", linewidths=.35, zorder=4)
    style_axis(ax, title=None, xlabel=None, ylabel=None)
    ax.set_axis_off()
    handles=[
        Line2D([], [], marker="o", color="none", markerfacecolor="#3b6b8e", markeredgecolor="white", markersize=4, label="Retained station (n=92)"),
        Line2D([], [], marker="^", color="none", markerfacecolor="#222222", markeredgecolor="white", markersize=5, label="Core source (n=14)"),
        Line2D([], [], color="#8c9298", lw=.65, label="Retained edge (n=318)"),
    ]
    ax = axes[1]
    tracts.plot(column="links", ax=ax, cmap="Blues", vmin=0, vmax=max(1, tracts.links.max()),
                edgecolor="#c9c9c9", linewidth=.12, legend=True,
                legend_kwds={"label": "Mapped substations per tract", "shrink": .68, "pad": .02})
    style_axis(ax, title=None, xlabel=None, ylabel=None)
    ax.set_axis_off(); ax.set_aspect("equal")
    fig.text(.255, .95, "A. Retained network", ha="center", va="center", fontsize=july.FS_TITLE, weight="bold")
    fig.text(.73, .95, "B. Utility-compatible tract mapping", ha="center", va="center", fontsize=july.FS_TITLE, weight="bold")
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .015),
               frameon=False, fontsize=7.1, ncol=3, columnspacing=2.5)
    fig.subplots_adjust(left=.025, right=.97, bottom=.14, top=.91, wspace=.06)
    save_figure(fig, "Fig02_System_Network_and_Mapping")


def plot_supp_fig03_crew_map() -> Path:
    """Draw the frozen C57 origins against the formal expanded tract footprint."""
    tracts = tract_geometry()
    nodes = pd.read_csv(ROOT / "Data" / "substation_graph_CEC_nodes_expanded.csv", dtype={"id": str})
    bases = pd.read_csv(ROOT / "Data" / "stage45_active_crew_bases_C57.csv")
    bases = bases.loc[bases.integer_crews.gt(0)].copy()
    if len(nodes) != 92 or int(bases.integer_crews.sum()) != 57:
        raise ValueError("Frozen 92-station / C57 crew-origin identity mismatch")
    points = map_points(nodes, tracts.crs)
    crews = gpd.GeoDataFrame(bases, geometry=gpd.points_from_xy(bases.longitude, bases.latitude),
                             crs="EPSG:4326").to_crs(tracts.crs)
    fig, ax = plt.subplots(figsize=(13.2 * CM, 8.4 * CM))
    draw_tract_base(ax, tracts)
    ax.scatter(points.geometry.x, points.geometry.y, s=9, c="#89939b", alpha=.72,
               edgecolors="white", linewidths=.22, zorder=3)
    colors = {"LADWP": "#377eb8", "SCE": "#d95f02"}
    for utility, group in crews.groupby("utility"):
        ax.scatter(group.geometry.x, group.geometry.y, s=43, c=colors.get(utility, "#6a3d9a"),
                   edgecolors="white", linewidths=.45, zorder=4)
    ax.set_title("C57 crew origins across the expanded study area", fontsize=july.FS_TITLE, pad=4)
    handles = [
        Line2D([], [], marker="o", color="none", markerfacecolor="#89939b",
               markeredgecolor="white", markersize=4.2, label="Retained station (n=92)"),
        Line2D([], [], marker="o", color="none", markerfacecolor=colors["LADWP"],
               markeredgecolor="white", markersize=5.2, label="LADWP crew origin"),
        Line2D([], [], marker="o", color="none", markerfacecolor=colors["SCE"],
               markeredgecolor="white", markersize=5.2, label="SCE crew origin"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .02),
               frameon=False, fontsize=7.1, ncol=3)
    fig.subplots_adjust(left=.015, right=.985, bottom=.13, top=.91)
    path = OUT / "_FigS03_expanded_crew_map.pdf"
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=.025,
                facecolor="white", metadata={"Creator": "LA Grid presentation-only renderer"})
    plt.close(fig)
    return path


def plot_mapping_tract_shift_panel() -> Path:
    """Presentation-only map from the frozen Hospital-first M1–M0 tract table."""
    source = FORMAL / "Formal_Results" / "TRACT_MAPPING_SHIFT.parquet"
    shift = pd.read_parquet(source)
    shift = shift.loc[(shift.hazard == "2pc50") &
                      (shift.strategy_id == "hospital-first")].copy()
    shift["tract_id_norm"] = shift.tract_id.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    geo = tract_geometry().merge(
        shift[["tract_id_norm", "mean_M1_minus_M0_burden_hr"]],
        on="tract_id_norm", how="left", validate="one_to_one")
    values = geo.mean_M1_minus_M0_burden_hr.to_numpy(dtype=float)
    if len(geo) != 2315 or not np.isfinite(values).all():
        raise ValueError("Frozen M1–M0 map must cover all 2,315 study tracts")
    span = float(np.nanpercentile(np.abs(values), 99))
    if not np.isfinite(span) or span <= 0:
        raise ValueError("Frozen M1–M0 display range must be finite and nonzero")
    fig, ax = plt.subplots(figsize=(8.9 * CM, 7.0 * CM))
    geo.plot(column="mean_M1_minus_M0_burden_hr", ax=ax, cmap="RdBu_r",
             vmin=-span, vmax=span, edgecolor="#d1d1d1", linewidth=.08)
    ax.set_title("Hospital-first: M1 minus July M0 (2pc50)",
                 fontsize=july.FS_TITLE, pad=4.0)
    ax.set_axis_off(); ax.set_aspect("equal")
    sm = plt.cm.ScalarMappable(norm=TwoSlopeNorm(vmin=-span, vcenter=0, vmax=span), cmap="RdBu_r")
    cbar = fig.colorbar(sm, ax=ax, fraction=.045, pad=.025)
    cbar.set_label("Change in mean tract burden (h)", fontsize=july.FS_COLORBAR)
    cbar.ax.tick_params(labelsize=7.0, width=.55, length=2.0)
    cbar.outline.set_linewidth(.5)
    fig.subplots_adjust(left=.015, right=.91, bottom=.02, top=.91)
    path = OUT / "_Fig02_mapping_shift_panel.pdf"
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=.025,
                facecolor="white", metadata={"Creator": "LA Grid presentation-only renderer"})
    plt.close(fig)
    return path


def plot_fig03() -> None:
    primary_path = FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet"
    d = pd.read_parquet(primary_path)
    d = d[(d.hazard == "2pc50") & (d.resource_scenario == "C57_D1") &
          (d.mapping == "M1_UTILITY_003") & (d.gate == "G1_BASELINE_050") &
          (d.strategy_id == "unconstrained")]
    if len(d) != 1000:
        raise ValueError(f"Expected 1000 frozen Unconstrained realizations; found {len(d)}")
    kpis = pd.read_csv(SUITE / "Stage 3 Output_expanded" / "tract_kpis_2pc50.csv", dtype={"tract_id": str})
    kpis["tract_id_norm"] = kpis.tract_id.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    if len(kpis) != 2315 or kpis.tract_id_norm.nunique() != 2315 or not np.isfinite(kpis.T80).all():
        raise ValueError("Frozen Unconstrained T80 table must cover all 2,315 tracts")
    geo = tract_geometry().merge(kpis[["tract_id_norm", "T80"]], on="tract_id_norm", how="left", validate="one_to_one")
    fig, (ax_dist, ax_map) = plt.subplots(1, 2, figsize=(18.5 * CM, 6.7 * CM))
    values = d.population_T80_hr.dropna().to_numpy(float)
    lo = 2 * np.floor(values.min() / 2)
    hi = 2 * np.ceil(values.max() / 2)
    bins = np.arange(lo, hi + 2, 2)
    ax_dist.hist(values, bins=bins, color="#8faed2", edgecolor="white", linewidth=.35)
    ax_dist.axvline(float(np.median(values)), color="#345f88", lw=1.0, ls="--",
                    label="Median")
    style_axis(ax_dist, title=None,
               xlabel="Time to 80% service (h)", ylabel="Realization count")
    ax_dist.legend(frameon=False, fontsize=7.0, loc="upper left")
    geo.plot(column="T80", ax=ax_map, cmap="viridis", edgecolor="#d1d1d1", linewidth=.12,
             legend=True, legend_kwds={"label": "Mean tract T80 (h)", "shrink": .70, "pad": .02})
    style_axis(ax_map, title=None, xlabel=None, ylabel=None)
    ax_map.set_axis_off(); ax_map.set_aspect("equal"); ax_map.set_anchor("N")
    fig.text(.27, .95, "A. Unconstrained population T80 (2pc50)",
             ha="center", va="center", fontsize=july.FS_TITLE, weight="bold")
    fig.text(.74, .95, "B. Unconstrained mean tract T80",
             ha="center", va="center", fontsize=july.FS_TITLE, weight="bold")
    fig.subplots_adjust(left=.09, right=.97, bottom=.16, top=.85, wspace=.25)
    save_figure(fig, "Fig03_Unconstrained_Recovery")


def plot_unconstrained_t80_map_panel() -> Path:
    """Render the frozen tract T80 table without recalculating recovery times."""
    table = SUITE / "Stage 3 Output_expanded" / "tract_kpis_2pc50.csv"
    kpis = pd.read_csv(table, dtype={"tract_id": str})
    kpis["tract_id_norm"] = kpis.tract_id.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    if len(kpis) != 2315 or kpis.tract_id_norm.nunique() != 2315 or not np.isfinite(kpis.T80).all():
        raise ValueError("Frozen Unconstrained T80 table must cover all 2,315 tracts")
    geo = tract_geometry().merge(kpis[["tract_id_norm", "T80"]], on="tract_id_norm",
                                 how="left", validate="one_to_one")
    if len(geo) != 2315 or not np.isfinite(geo.T80.to_numpy(dtype=float)).all():
        raise ValueError("Frozen T80 values did not join to the full study-area geometry")
    fig, ax = plt.subplots(figsize=(8.9 * CM, 7.0 * CM))
    geo.plot(column="T80", ax=ax, cmap="viridis", edgecolor="#d1d1d1", linewidth=.08)
    ax.set_title("Unconstrained tract time to 80% service (2pc50)",
                 fontsize=july.FS_TITLE, pad=4.0)
    ax.set_axis_off(); ax.set_aspect("equal")
    sm = plt.cm.ScalarMappable(cmap="viridis")
    sm.set_clim(float(geo.T80.min()), float(geo.T80.max()))
    cbar = fig.colorbar(sm, ax=ax, fraction=.045, pad=.025)
    cbar.set_label("Mean tract T80 (h)", fontsize=july.FS_COLORBAR)
    cbar.ax.tick_params(labelsize=7.0, width=.55, length=2.0)
    cbar.outline.set_linewidth(.5)
    fig.subplots_adjust(left=.015, right=.91, bottom=.02, top=.91)
    path = OUT / "_Fig03_unconstrained_t80_map_panel.pdf"
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=.025,
                facecolor="white", metadata={"Creator": "LA Grid presentation-only renderer"})
    plt.close(fig)
    return path


def baseline_realizations() -> pd.DataFrame:
    primary = pd.read_parquet(FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
    primary = primary[(primary.hazard == "2pc50") & (primary.resource_scenario == "C57_D1") &
                      (primary.mapping == "M1_UTILITY_003") & (primary.gate == "G1_BASELINE_050") &
                      (primary.strategy_id.isin(["impact-first", "hospital-first", "degree-first", "unconstrained"]))].copy()
    vuln = pd.read_parquet(FORMAL / "Equity_Amendment" / "VULNERABILITY_PRIMARY_SUMMARY.parquet")
    vuln = vuln[(vuln.hazard == "2pc50") & (vuln.resource_scenario == "C57_D1") &
                (vuln.mapping == "M1_UTILITY_003") & (vuln.gate == "G1_BASELINE_050") &
                (vuln.strategy_id == "vulnerability-first")].copy()
    d = pd.concat([primary, vuln], ignore_index=True)
    expected = {"impact-first", "hospital-first", "vulnerability-first", "degree-first", "unconstrained"}
    counts = d.groupby("strategy_id").realization_id.nunique().to_dict()
    if set(counts) != expected or any(v != 1000 for v in counts.values()):
        raise ValueError(f"Frozen main policy display must be five groups × 1000 realizations: {counts}")
    return d


def plot_box(ax, df, metric: str, keys: list[str], positions=None, *, width=.58) -> None:
    positions = positions or list(range(1, len(keys) + 1))
    for key, x in zip(keys, positions):
        vals = df.loc[df.strategy_id.eq(key), metric].dropna().to_numpy(float)
        ax.boxplot(vals, positions=[x], widths=width, patch_artist=True,
                   boxprops={"facecolor": STRATEGY_COLORS[key], "edgecolor": STRATEGY_COLORS[key], "alpha": .38, "linewidth": .75},
                   medianprops={"color": STRATEGY_COLORS[key], "linewidth": 1.05},
                   whiskerprops={"color": STRATEGY_COLORS[key], "linewidth": .75},
                   capprops={"color": STRATEGY_COLORS[key], "linewidth": .75},
                   flierprops={"marker": ".", "markersize": 1.7, "markerfacecolor": STRATEGY_COLORS[key], "markeredgecolor": "none", "alpha": .22})
    ax.set_xticks(positions, [STRATEGY_LABELS[k] for k in keys], rotation=0, ha="center")
    ax.tick_params(axis="x", labelsize=7.0)


def plot_fig04(data: pd.DataFrame) -> None:
    keys = ["impact-first", "hospital-first", "vulnerability-first", "degree-first", "unconstrained"]
    panels = [
        ("population_resolved_mass_weighted_burden_hr", "A. Population service burden", "Burden (h)"),
        ("L_source_population_mass_weighted_hr", "B. Source-path burden", "Burden (h)"),
        ("hospital_mean_normalized_burden_hr", "C. Hospital-linked tract burden", "Burden (h)"),
        ("population_T80_hr", "D. Population time to 80% service", "Time (h)"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(18.5 * CM, 13.2 * CM))
    for ax, (metric, title, unit_label) in zip(axes.flat, panels):
        plot_box(ax, data, metric, keys, width=.55)
        # The shared strategy legend carries the full names once; repeating five
        # long labels below each narrow panel made the strategy axis unreadable.
        ax.set_xticks(range(1, len(keys) + 1), [""] * len(keys))
        ax.tick_params(axis="x", length=0)
        style_axis(ax, title=title, xlabel=None, ylabel=unit_label)
        ax.set_xlabel("")
    handles = [Patch(facecolor=STRATEGY_COLORS[k], edgecolor=STRATEGY_COLORS[k], alpha=.45,
                     label=STRATEGY_LABELS[k]) for k in keys]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .012), ncol=5,
               frameon=False, fontsize=7.5, handlelength=1.2, columnspacing=1.5)
    fig.text(.5, .985, "2pc50 · matched physical realizations · lower values indicate less burden or faster recovery",
             ha="center", va="top", fontsize=7.5, color="#555555")
    fig.subplots_adjust(left=.10, right=.985, bottom=.145, top=.91, wspace=.27, hspace=.25)
    save_figure(fig, "Fig04_Restoration_Strategy_Tradeoffs")


def plot_fig05(data: pd.DataFrame) -> None:
    mapping_path = ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv"
    hospital_path = ROOT / "Data" / "hospital_with_tract_expanded.csv"
    nodes_path = ROOT / "Data" / "substation_graph_CEC_nodes_expanded.csv"
    rules_path = FORMAL / "Stage 4 Output_expanded" / "FULL_RULE_SEQUENCES.json"
    mapping = pd.read_csv(mapping_path, dtype={"tract_id": str, "substation_id": str})
    hospital = pd.read_csv(hospital_path, dtype={"GEOID": str})
    hosp_tracts = set(hospital.GEOID.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(11))
    mapping["tract_norm"] = mapping.tract_id.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(11)
    mapping["is_hosp"] = mapping.tract_norm.isin(hosp_tracts)
    hosp_score = mapping.groupby("substation_id").is_hosp.sum()
    pop_score = mapping.groupby("substation_id").population.sum()
    rank = pd.concat([hosp_score, pop_score], axis=1).fillna(0.0)
    rank.columns = ["hospital_tract_count", "population_tiebreak"]
    rank = rank.sort_values(["hospital_tract_count", "population_tiebreak"], ascending=[False, False])
    import json
    frozen = json.loads(rules_path.read_text(encoding="utf-8"))["2pc50"]["hospital-first"]
    if list(map(str, rank.index)) != list(map(str, frozen)):
        raise ValueError("Hospital-priority map ranking differs from frozen Hospital-first sequence")
    rank["rank"] = np.arange(1, len(rank) + 1)
    nodes = pd.read_csv(nodes_path, dtype={"id": str}); nodes["id"] = nodes.id.astype(str)
    nodes = nodes.join(rank, on="id", how="left")
    tracts = tract_geometry()
    tracts["hospital_link"] = tracts.tract_id_norm.isin(hosp_tracts)
    pts = map_points(nodes, tracts.crs)
    priority = pts[pts.hospital_tract_count.fillna(0).gt(0)]
    top = rank.head(5).reset_index().rename(columns={"substation_id": "Station"})
    fig = plt.figure(figsize=(18.5 * CM, 10.5 * CM))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.27, .73], wspace=.23)
    axmap = fig.add_subplot(gs[0, 0]); axbox = fig.add_subplot(gs[0, 1])
    colors = np.where(tracts.hospital_link, "#d69b55", "#f7f7f7")
    draw_tract_base(axmap, tracts, colors)
    pts.plot(ax=axmap, color="#55758b", markersize=7, marker="o", edgecolor="white", linewidth=.22, zorder=3)
    priority.plot(ax=axmap, color="#a65628", markersize=11, marker="o", edgecolor="white", linewidth=.35, zorder=4)
    for rr in top.itertuples(index=False):
        point = pts[pts.id.eq(str(rr.Station))].geometry.iloc[0]
        axmap.annotate(str(rr.rank), (point.x, point.y), xytext=(5, 5), textcoords="offset points",
                       fontsize=7.0, weight="bold", color="#222222",
                       bbox={"boxstyle": "circle,pad=.16", "fc": "white", "ec": "#a65628", "lw": .7}, zorder=7)
    style_axis(axmap, title="A. Hospital priority targets substations", xlabel=None, ylabel=None)
    axmap.set_axis_off()
    handles = [Patch(facecolor="#d69b55", edgecolor="none", label="Hospital-linked tracts"),
               Line2D([], [], marker="o", color="none", markerfacecolor="#55758b", markeredgecolor="white", markersize=4, label="All substations"),
               Line2D([], [], marker="o", color="none", markerfacecolor="#a65628", markeredgecolor="white", markersize=4, label="Hospital-priority substations")]
    axmap.legend(handles=handles, frameon=False, loc="lower center", bbox_to_anchor=(.5,-.13),
                 fontsize=7.0, ncol=2, columnspacing=.8, handlelength=1.0)
    keys = STRATEGIES
    plot_box(axbox, data, "hospital_mean_normalized_burden_hr", keys, width=.50)
    axbox.set_xticks([1,2,3,4], ["Impact-\nfirst", "Hospital-\nfirst", "Vulnerability-\nfirst", "Degree-\nfirst"])
    style_axis(axbox, title="B. Hospital-linked tract burden", xlabel=None,
               ylabel="Cumulative burden (h)")
    axbox.tick_params(axis="x", labelsize=7.0)
    fig.subplots_adjust(left=.035, right=.98, bottom=.20, top=.91)
    save_figure(fig, "Fig05_Hospital_Priority_and_Critical_Service")


def plot_fig06(data: pd.DataFrame) -> None:
    qpath = FORMAL / "Equity_Amendment" / "Figures" / "FIGURE_B_SOURCE.csv"
    effect_path = FORMAL / "Equity_Amendment" / "VULNERABILITY_PAIRWISE_EFFECTS.csv"
    tract_path = FORMAL / "Equity_Amendment" / "Figures" / "FIGURE_C_SOURCE.csv"
    q = pd.read_csv(qpath)
    q = q[q.strategy.isin(STRATEGIES) & q.quartile.isin(["Q1", "Q2", "Q3", "Q4"])].copy()
    effect = pd.read_csv(effect_path)
    effect = effect[(effect.hazard == "2pc50") & (effect.resource_scenario == "C57_D1") &
                    (effect.strategy_id == "vulnerability-first") & (effect.reference_strategy == "hospital-first")]
    tract = pd.read_csv(tract_path, dtype={"tract_id": str})
    tract = tract[(tract.hazard == "2pc50") & tract.reference_strategy.eq("hospital-first")].copy()
    if len(tract) != 2315 or set(q.strategy.unique()) != {"impact-first", "hospital-first", "vulnerability-first"}:
        raise ValueError("Frozen equity panel inputs do not cover expected strategies/tracts")
    q_order = ["Q1", "Q2", "Q3", "Q4"]
    fig = plt.figure(figsize=(18.5 * CM, 14.8 * CM))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.0],
                          hspace=.38, wspace=.28)
    ax_a = fig.add_subplot(gs[0, 0]); ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0]); ax_d = fig.add_subplot(gs[1, 1])
    offsets = {"impact-first": -.22, "hospital-first": 0, "vulnerability-first": .22}
    for key in ["impact-first", "hospital-first", "vulnerability-first"]:
        part = q[q.strategy.eq(key)].set_index("quartile").loc[q_order]
        xx = np.arange(4) + offsets[key]
        yy = part.mean_burden_hr.to_numpy(float)
        low, high = yy - part.ci_low.to_numpy(float), part.ci_high.to_numpy(float) - yy
        ax_a.errorbar(xx, yy, yerr=np.vstack([low, high]), fmt="o", markersize=3.5,
                      color=STRATEGY_COLORS[key], ecolor=STRATEGY_COLORS[key], lw=.8, capsize=1.8,
                      linestyle="none", label=STRATEGY_LABELS[key])
    ax_a.set_xticks(np.arange(4), q_order)
    style_axis(ax_a, title="A. Absolute burden by social-vulnerability quartile", xlabel=None, ylabel="Cumulative burden (h)")
    handles, labels = ax_a.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=7.0, ncol=3,
               loc="upper center", bbox_to_anchor=(.5, .995))
    b = effect[effect.metric.isin([f"burden_Q{i}_hr" for i in range(1,5)])].copy()
    b["quartile"] = b.metric.str.extract(r"(Q[1-4])")
    b = b.set_index("quartile").loc[q_order]
    yy = b.paired_mean_difference.to_numpy(float)
    ax_b.errorbar(yy, np.arange(4), xerr=np.vstack([yy - b.bootstrap_ci_low.to_numpy(float), b.bootstrap_ci_high.to_numpy(float) - yy]),
                  fmt="o", color=STRATEGY_COLORS["vulnerability-first"], ecolor=STRATEGY_COLORS["vulnerability-first"],
                  lw=.9, capsize=2.0, markersize=4.0)
    ax_b.axvline(0, color="#666666", lw=.65, ls="--")
    ax_b.set_yticks(np.arange(4), q_order)
    style_axis(ax_b, title="B. Vulnerability-first change relative to Hospital-first", xlabel="Change relative to Hospital-first (h)", ylabel=None)
    ax_b.grid(True, axis="x", color="#e4e4e4", linewidth=.4, alpha=.68); ax_b.grid(False, axis="y")
    # Panel C uses only fixed realization-level summary rows and descriptive means.
    stats = []
    for key in ["impact-first", "hospital-first", "vulnerability-first"]:
        dd = data[data.strategy_id.eq(key)]
        stats.append({"strategy": key,
                      "burden": float(dd.population_resolved_mass_weighted_burden_hr.mean()),
                      "gap": float(dd.absolute_Q4_minus_Q1_hr.mean()),
                      "gini": float(dd.burden_gini.mean())})
    stat = pd.DataFrame(stats).set_index("strategy").loc[
        ["impact-first", "hospital-first", "vulnerability-first"]].reset_index()
    ax_c.set_axis_off()
    ax_c.set_title("C. Distributional trade-off", loc="left", fontsize=july.FS_TITLE, pad=3)
    table_values = [[metric, *[f"{v:.3f}" for v in values]] for metric, values in [
        ("Population burden (h)", stat.burden.to_numpy(float)),
        ("|Q4-Q1| gap (h)", stat.gap.to_numpy(float)),
        ("Burden Gini", stat.gini.to_numpy(float)),
    ]]
    tab = ax_c.table(cellText=table_values,
                     colLabels=["Outcome", "Impact", "Hospital", "Vulnerability"],
                     colWidths=[.38, .18, .20, .24], loc="center",
                     cellLoc="center", colLoc="center", bbox=[.005, .24, .99, .58])
    tab.auto_set_font_size(False); tab.set_fontsize(7.0)
    for (ri, ci), cell in tab.get_celld().items():
        cell.set_linewidth(.35); cell.set_edgecolor("#c5c5c5")
        if ri == 0:
            cell.set_facecolor("#e8edf0"); cell.set_text_props(weight="bold")
        elif ci > 0:
            cell.get_text().set_color(STRATEGY_COLORS[stat.iloc[ci-1].strategy])
    ax_c.text(.01,.12,"Q4 = highest social-vulnerability quartile.",
              transform=ax_c.transAxes,fontsize=7.0,ha="left",va="center")
    # Full-domain continuous tract effect map; 0 is the neutral reference.
    tracts = tract_geometry()
    tracts["tract_id_norm"] = tracts.tract_id_norm.astype(str).str.zfill(11)
    tract["tract_id_norm"] = tract.tract_id.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    tract = tract.rename(columns={"population": "effect_population"})
    mapped = tracts.merge(tract[["tract_id_norm", "mean_paired_delta_burden_hr", "effect_population"]], on="tract_id_norm", how="left")
    if mapped.mean_paired_delta_burden_hr.notna().sum() != 2315:
        raise ValueError("Continuous tract-effect map does not cover all 2,315 study tracts")
    vmax = float(np.nanmax(np.abs(mapped.mean_paired_delta_burden_hr.to_numpy(float))))
    mapped.plot(column="mean_paired_delta_burden_hr", ax=ax_d, cmap="RdBu_r",
                norm=TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax),
                edgecolor="#c9c9c9", linewidth=.10,
                legend=True, legend_kwds={"label": "Burden change (h)", "shrink": .70, "pad": .02})
    style_axis(ax_d, title="D. Tract burden change", xlabel=None, ylabel=None)
    ax_d.set_axis_off(); ax_d.set_aspect("equal")
    # Population summaries retain continuous sign and magnitude; no threshold band is introduced.
    delta = mapped[["effect_population", "mean_paired_delta_burden_hr"]].dropna()
    pop = delta.effect_population.to_numpy(float); val = delta.mean_paired_delta_burden_hr.to_numpy(float)
    lower = float(pop[val < 0].sum()); higher = float(pop[val > 0].sum()); equal = float(pop[val == 0].sum())
    fig.text(.51, .075, f"Population with lower / higher burden: {lower/1e6:.2f} / {higher/1e6:.2f} million",
             fontsize=7.0, ha="left", va="center")
    fig.subplots_adjust(left=.075, right=.98, bottom=.11, top=.88)
    save_figure(fig, "Fig06_Vulnerability_Targeting_and_Distributional_Tradeoffs")


def plot_stage7_maps() -> tuple[Path, Path]:
    g = tract_geometry()
    status_path = STAGE7 / "stage7_full_domain_tract_status.csv"
    status = pd.read_csv(status_path, dtype={"tract_id": str})
    status["tract_id_norm"] = status.tract_id.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    merged = g.merge(status, on="tract_id_norm", how="left", suffixes=("", "_s7"))
    cluster_col = "cluster_s7" if "cluster_s7" in merged else "cluster"
    score_candidates = [c for c in merged.columns if "SlowVulnerable_Hotspot_Score" in c]
    score_col = score_candidates[-1]
    if len(merged) != 2315 or merged[cluster_col].notna().sum() != 2291:
        raise ValueError("Stage 7 final map must preserve 2,291 typology members and 24 not-applicable tracts")
    cmap = {str(c): july.STAGE7_IJDRR_CLUSTER_PALETTE[i % len(july.STAGE7_IJDRR_CLUSTER_PALETTE)] for i,c in enumerate(sorted(merged[cluster_col].dropna().unique(), key=lambda x: int(float(x))))}
    colors = merged[cluster_col].map(lambda x: cmap.get(str(x), july.STAGE7_NA_COLOR))
    f1, ax1 = plt.subplots(figsize=(8.9 * CM, 7.2 * CM))
    draw_tract_base(ax1, merged, colors)
    ax1.set_title("B. Residential typology", fontsize=july.FS_TITLE, loc="left", pad=3)
    handles = [Patch(facecolor=c, edgecolor="white", linewidth=.25, label=f"Cluster {int(float(k))}") for k,c in cmap.items()]
    handles.append(Patch(facecolor=july.STAGE7_NA_COLOR, edgecolor="#bcbcbc", linewidth=.35, label="Not in residential typology"))
    ax1.legend(handles=handles, frameon=False, loc="upper center", bbox_to_anchor=(.5,-.02), ncol=2, fontsize=7.0)
    f1.subplots_adjust(left=.02, right=.98, top=.91, bottom=.24)
    cluster_pdf = OUT / "_Fig07_cluster_map_panel.pdf"
    f1.savefig(cluster_pdf, bbox_inches="tight", pad_inches=.025, facecolor="white")
    plt.close(f1)
    f2, ax2 = plt.subplots(figsize=(8.9 * CM, 7.2 * CM))
    merged.plot(column=score_col, ax=ax2, cmap=july.STAGE7_HOTSPOT_SCORE_CMAP,
                edgecolor="#c9c9c9", linewidth=.12, legend=True,
                legend_kwds={"label": "Slow-vulnerable hotspot score", "shrink": .67, "pad": .02},
                missing_kwds={"color": july.STAGE7_NA_COLOR, "edgecolor": "#bcbcbc", "label": "Not in residential typology"})
    ax2.set_axis_off(); ax2.set_aspect("equal")
    ax2.set_title("C. Hotspot score", fontsize=july.FS_TITLE, loc="left", pad=3)
    f2.subplots_adjust(left=.02, right=.98, top=.91, bottom=.05)
    hotspot_pdf = OUT / "_Fig07_hotspot_map_panel.pdf"
    f2.savefig(hotspot_pdf, bbox_inches="tight", pad_inches=.025, facecolor="white")
    plt.close(f2)
    return cluster_pdf, hotspot_pdf


def plot_fig07() -> None:
    panel_b, panel_c = plot_stage7_maps()
    panels = [
        ("A. Cluster profile differences", STAGE7 / "vis_stage7_heatmap.pdf"),
        ("", panel_b), ("", panel_c),
    ]
    # Build a balanced page: profile at native full width, two maps at native 89 mm width.
    docs = [(title, fitz.open(path)) for title, path in panels]
    prof = docs[0][1][0]
    map1, map2 = docs[1][1][0], docs[2][1][0]
    width = max(prof.rect.width, map1.rect.width * 2 + 12)
    gap_h = 18.0
    bottom_h = max(map1.rect.height, map2.rect.height) + gap_h
    total_h = prof.rect.height + 17 + bottom_h
    outdoc = fitz.open(); page = outdoc.new_page(width=width, height=total_h)
    page.insert_font(fontname="ArBold", fontfile=str(ARIAL_BOLD))
    page.insert_text((8,9.5), "A. Cluster profile differences", fontname="ArBold", fontsize=8.2, color=(.1,.1,.1))
    x_profile = (width - prof.rect.width) / 2
    page.show_pdf_page(fitz.Rect(x_profile,17,x_profile+prof.rect.width,17+prof.rect.height), docs[0][1], 0, keep_proportion=True)
    y = 17 + prof.rect.height
    y += 4.0
    page.show_pdf_page(fitz.Rect((width/2-map1.rect.width)/2, y, (width/2-map1.rect.width)/2+map1.rect.width, y+map1.rect.height), docs[1][1], 0, keep_proportion=True)
    page.show_pdf_page(fitz.Rect(width/2+(width/2-map2.rect.width)/2, y, width/2+(width/2-map2.rect.width)/2+map2.rect.width, y+map2.rect.height), docs[2][1], 0, keep_proportion=True)
    outdoc.save(OUT / "Fig07_Community_Typology_and_Hotspots.pdf", garbage=4, deflate=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(600/72,600/72), alpha=False)
    pix.set_dpi(600, 600)
    pix.save(OUT / "Fig07_Community_Typology_and_Hotspots.png")
    for _, d in docs: d.close()
    outdoc.close()
    panel_b.unlink(missing_ok=True); panel_c.unlink(missing_ok=True)


def plot_supp_fig04() -> None:
    stage2 = SUITE / "Stage 2 Output_expanded"
    fig, ax = plt.subplots(figsize=(18.5*CM, 7.2*CM))
    attack = [("impact", "Impact"), ("random", "Random"), ("degree", "Degree"), ("betweenness_centrality", "Betweenness"), ("closeness_centrality", "Closeness")]
    colors={"impact":"#ff7f00","random":"#888888","degree":"#4daf4a","betweenness_centrality":"#b59a00","closeness_centrality":"#377eb8"}
    linestyles={"impact":":","random":"-","degree":"--","betweenness_centrality":"-.","closeness_centrality":(0,(4,1.6))}
    for stem, label in attack:
        path = stage2 / (f"percolation_curve_{stem}.csv" if stem in {"impact","random"} else f"exploratory_percolation_curve_{stem}.csv")
        d = pd.read_csv(path); ax.plot(d.nodes_removed,d.lcc_fraction,lw=1.0,color=colors[stem],ls=linestyles[stem],label=label)
    style_axis(ax, title="Static station-removal criticality", xlabel="Stations removed", ylabel="Largest-component fraction")
    ax.legend(frameon=False,fontsize=7.0,ncol=5,loc="upper center",bbox_to_anchor=(.5,1.02))
    fig.subplots_adjust(left=.11,right=.985,bottom=.17,top=.84)
    panel=OUT/"_FigS04_percolation_panel.pdf"
    fig.savefig(panel,format="pdf",bbox_inches="tight",pad_inches=.025,facecolor="white")
    plt.close(fig)
    source_panel=plot_source_path_panel()
    combine_pdf_panels("FigS04_Network_Criticality_and_Percolation",[
        ("",panel),
        ("",original("vis_stage6_network_topology_recovery_2pc50.pdf")),
        ("",source_panel)])
    panel.unlink(missing_ok=True); source_panel.unlink(missing_ok=True)


def plot_source_path_panel() -> Path:
    p=SUITE/"Stage 6 Output_expanded/SOURCE_PATH_PAIRED_EFFECT_DISPLAY.csv"
    d=pd.read_csv(p); d=d[d.hazard.eq("2pc50")].copy()
    keys=["centrality-first","impact-first","betweenness-first","degree-first","closeness-first","random","vulnerability-first"]
    if set(d.strategy_id)!=set(keys):
        raise ValueError(f"Frozen 2pc50 source-path effects have unexpected policy set: {sorted(d.strategy_id.unique())}")
    d=d.set_index("strategy_id").loc[keys].reset_index()
    fig,ax=plt.subplots(figsize=(18.5*CM,7.4*CM)); y=np.arange(len(d))[::-1]
    for yy,row in zip(y,d.itertuples(index=False)):
        color=STRATEGY_COLORS[row.strategy_id]
        ax.hlines(yy,row.p05_paired_delta_hr,row.p95_paired_delta_hr,color=color,lw=1.1)
        ax.plot(row.mean_paired_delta_hr,yy,marker={"centrality-first":"o","impact-first":"s","betweenness-first":"^","degree-first":"D","closeness-first":"v","random":"P","vulnerability-first":"X"}[row.strategy_id],
                color=color,markersize=4.0,linestyle="none")
    ax.axvline(0,color="#666666",lw=.65,ls="--")
    ax.set_yticks(y,[STRATEGY_LABELS[k] for k in d.strategy_id])
    style_axis(ax,title="Source-path burden change by restoration priority",xlabel="Change relative to Hospital-first (h), 5–95% realization range",ylabel=None)
    ax.grid(True,axis="x",color="#e4e4e4",lw=.4);ax.grid(False,axis="y")
    fig.subplots_adjust(left=.24,right=.985,bottom=.20,top=.85)
    path=OUT/"_FigS04_source_path_panel.pdf"
    fig.savefig(path,format="pdf",bbox_inches="tight",pad_inches=.025,facecolor="white");plt.close(fig)
    return path


def plot_mapping_shift_panel() -> Path:
    p=SUITE/"Sensitivity Output_clean/FORMAL_MAPPING_EFFECTS.csv"
    d=pd.read_csv(p)
    d=d[(d.hazard=="2pc50")&(d.comparison=="full92")&(d.domain=="mapping_native_domain")&
        (d.reference_mapping=="M0_JULY_003")&(d.target_mapping=="M1_UTILITY_003")&
        (d.metric.isin(["population_resolved_mass_weighted_burden_hr","population_T80_hr"]))].copy()
    keys=["centrality-first","impact-first","betweenness-first","degree-first","closeness-first","hospital-first","random","unconstrained"]
    d=d[~d.strategy_id.eq("direct-community")]
    if set(d.strategy_id)!=set(keys) or any(d.groupby(["metric","strategy_id"]).size()!=1):
        raise ValueError("Frozen M0/M1 mapping effects do not cover the expected distinct policies")
    fig,axes=plt.subplots(1,2,figsize=(18.5*CM,10.1*CM))
    metrics=[("population_resolved_mass_weighted_burden_hr","Population-weighted modeled service burden (h)"),
             ("population_T80_hr","Population time to 80% service (h)")]
    markers={"centrality-first":"o","impact-first":"s","betweenness-first":"^","degree-first":"D","closeness-first":"v","hospital-first":"P","random":"X","unconstrained":"o"}
    for ax,(metric,label) in zip(axes,metrics):
        part=d[d.metric.eq(metric)].set_index("strategy_id").loc[keys]
        for y,key in enumerate(keys[::-1]):
            row=part.loc[key]
            ax.plot(row.mean_delta,y,marker=markers[key],color=STRATEGY_COLORS[key],markersize=4.0,linestyle="none")
        ax.axvline(0,color="#666666",lw=.65,ls="--")
        ax.set_yticks(range(len(keys)),[STRATEGY_LABELS[k] for k in keys[::-1]])
        style_axis(ax,title=label,xlabel="M1 minus July M0",ylabel=None)
        ax.grid(True,axis="x",color="#e4e4e4",lw=.4);ax.grid(False,axis="y")
    fig.suptitle("Mapping comparison across frozen formal policies",fontsize=july.FS_TITLE,y=.98)
    fig.subplots_adjust(left=.19,right=.985,bottom=.13,top=.85,wspace=.31)
    path=OUT/"_FigS06_mapping_effects_panel.pdf"
    fig.savefig(path,format="pdf",bbox_inches="tight",pad_inches=.025,facecolor="white");plt.close(fig)
    return path


def plot_supp_fig05() -> None:
    path=FORMAL/"Stage 5 Output_expanded"/"GA_FIVE_SEED_CONVERGENCE.csv"
    d=pd.read_csv(path)
    required={"seed","fitness","incumbent_fitness","search_improved_incumbent"}
    if not required.issubset(d.columns) or len(d)!=5:
        raise ValueError(f"Unexpected frozen five-seed GA table: {d.columns.tolist()}")
    if d.fitness.nunique()!=1 or not np.allclose(d.fitness,d.incumbent_fitness,atol=1e-12):
        raise ValueError("Expected frozen five-seed incumbent identity was not reproduced")
    d=d.sort_values("seed")
    fig,ax=plt.subplots(figsize=(13.2*CM,4.7*CM))
    x=np.arange(5)
    ax.hlines(0,x[0],x[-1],color="#bdbdbd",lw=.7)
    ax.scatter(x,np.zeros(5),s=42,color=STRATEGY_COLORS["impact-first"],zorder=3)
    ax.set_xlim(-.45,4.45);ax.set_ylim(-.7,.7)
    ax.set_xticks(x,[str(int(v)) for v in d.seed]);ax.set_yticks([])
    style_axis(ax,title="All five GA seeds retained Impact-first",xlabel="Independent planning seed",ylabel=None)
    ax.grid(False)
    ax.text(.5,.81,f"Same planning objective: {d.fitness.iloc[0]:.3f}",
            transform=ax.transAxes,ha="center",va="center",fontsize=7.5)
    ax.text(.5,.20,"Search improvement over retained incumbent: 0 of 5",
            transform=ax.transAxes,ha="center",va="center",fontsize=7.0)
    fig.subplots_adjust(left=.08,right=.98,bottom=.23,top=.82)
    save_figure(fig,"FigS05_GA_Reproducibility")


def plot_supp_fig06() -> None:
    """Show frozen cutoff and strict-SCE checks without internal mapping codes."""
    source = ROOT / "provenance/reviewer_working/Supplement_Rebuild_20260925/Tables"
    cutoff = pd.read_csv(source / "S3_CUTOFF_HOSPITAL_FIRST_2PC50.csv")
    cutoff = cutoff[(cutoff.hazard == "2pc50") &
                    (cutoff.strategy_id == "hospital-first") &
                    (cutoff.target_mapping.str.startswith("M1_UTILITY"))]
    if set(cutoff.target_mapping) != {"M1_UTILITY_001", "M1_UTILITY_NO_CUTOFF"}:
        raise ValueError("Frozen production-mapping cutoff rows are incomplete")
    values = [float(cutoff.loc[cutoff.target_mapping.eq("M1_UTILITY_NO_CUTOFF"), "mean_delta"].iloc[0]),
              float(cutoff.loc[cutoff.target_mapping.eq("M1_UTILITY_001"), "mean_delta"].iloc[0]), 0.0]
    sce = pd.read_csv(source / "S3_SCE_337_CANDIDATE_BENCHMARK.csv")
    sce = sce[(sce.version == "NEW_20260922") & (sce.candidate_kind == "direct_site")]
    if set(sce.mapping) != {"JULY_BASELINE_92", "JULY_UTILITY_CONSTRAINED_92"} or not (sce.tract_count == 337).all():
        raise ValueError("Frozen strict-SCE benchmark has unexpected mapping/domain")
    fig, axes = plt.subplots(1, 2, figsize=(18.5 * CM, 8.0 * CM))
    ax = axes[0]
    ax.plot([0, 1, 3], values, color=STRATEGY_COLORS["hospital-first"],
            marker="o", markersize=4.0, lw=1.0)
    ax.axhline(0, color="#777777", lw=.55, ls="--")
    ax.set_xticks([0, 1, 3], ["No cutoff", "1%", "3%\nproduction"])
    style_axis(ax, title="A. Tract-mapping cutoff response", xlabel="Candidate-weight cutoff",
               ylabel="Change from 3% production (h)")
    ax.grid(False, axis="x")
    ax = axes[1]
    labels = ["Any match", "Top 1", "Top 3"]
    columns = ["any_match", "top1", "top3"]
    y = np.arange(3)[::-1]
    july_row = sce[sce.mapping.eq("JULY_BASELINE_92")].iloc[0]
    production_row = sce[sce.mapping.eq("JULY_UTILITY_CONSTRAINED_92")].iloc[0]
    for yy, name, col in zip(y, labels, columns):
        a, b = 100 * float(july_row[col]), 100 * float(production_row[col])
        ax.hlines(yy, min(a, b), max(a, b), color="#adadad", lw=.7, zorder=1)
        ax.plot(a, yy, "o", color="#377eb8", ms=3.6, label="July baseline" if yy == y[0] else None)
        ax.plot(b, yy, "D", color="#ff7f00", ms=3.5, label="Utility-compatible" if yy == y[0] else None)
    ax.set_yticks(y, labels)
    ax.set_xlim(84, 100)
    style_axis(ax, title="B. Strict-SCE tract benchmark (337 tracts)",
               xlabel="Tracts matching public candidates (%)", ylabel=None)
    ax.grid(False, axis="y")
    ax.legend(frameon=False, loc="center right", bbox_to_anchor=(.99, .50), fontsize=7.0, ncol=1)
    fig.subplots_adjust(left=.11, right=.985, bottom=.22, top=.88, wspace=.36)
    save_figure(fig, "FigS06_Mapping_Robustness")


def plot_capacity_increment_panel() -> Path:
    """Compact display of the already-closed capacity-bounded increments."""
    path = ROOT / "results/capacity/SCE_CAPACITY_SENSITIVITY_SUMMARY.csv"
    data = pd.read_csv(path)
    keys = ["impact-first", "hospital-first", "vulnerability-first", "degree-first"]
    data = data[(data.row_type == "policy") & (data.Hazard == "2pc50") &
                data.Policy.isin(keys)].set_index("Policy").loc[keys]
    if len(data) != 4 or not (data.binding_station_count == 1).all():
        raise ValueError("Closed 2pc50 capacity increments were not found")
    fig, ax = plt.subplots(figsize=(18.5 * CM, 5.4 * CM))
    y = np.arange(len(keys))[::-1]
    vals = data.delta.to_numpy(float)
    for yy, key, value in zip(y, keys, vals):
        ax.plot(value, yy, "o", ms=4.4, color=STRATEGY_COLORS[key])
        ax.annotate(f"{value:.3f} h", (value, yy), xytext=(5, 0),
                    textcoords="offset points", ha="left", va="center", fontsize=7.0)
    ax.set_yticks(y, [STRATEGY_LABELS[k] for k in keys])
    ax.set_xlim(0.118, 0.134)
    ax.set_ylim(-.5, 3.5)
    style_axis(ax, title="2pc50: additional population burden under the capacity bound",
               xlabel="Capacity-bounded minus baseline burden (h; expanded scale)", ylabel=None)
    ax.grid(False, axis="y")
    fig.subplots_adjust(left=.25, right=.95, bottom=.25, top=.84)
    panel = OUT / "_FigS08_capacity_increment_panel.pdf"
    fig.savefig(panel, format="pdf", bbox_inches="tight", pad_inches=.025, facecolor="white")
    plt.close(fig)
    return panel


def plot_supp_fig09() -> None:
    pca=STAGE7/"pca_stats_with_eigenvalues.csv"; km=STAGE7/"kmeans_k_diagnostics.csv"; loads=STAGE7/"pca_loadings.csv"; labels=STAGE7/"clusters_labels_final.csv"
    a=pd.read_csv(pca); b=pd.read_csv(km); l=pd.read_csv(loads).rename(columns={"Unnamed: 0":"feature"}); c=pd.read_csv(labels)
    fig,axes=plt.subplots(2,2,figsize=(18.5*CM,13.5*CM))
    ax=axes[0,0]; ax.plot(np.arange(1,len(a)+1),a.Explained_Variance_Ratio*100,marker="o",ms=2.7,lw=.9,color="#456f88")
    style_axis(ax,title="A. PCA explained variance",xlabel="Component",ylabel="Variance explained (%)")
    ax.set_xticks(np.arange(1,len(a)+1))
    ax=axes[0,1]; ax.plot(b.k,b.inertia,marker="o",ms=2.7,lw=.9,color="#456f88")
    style_axis(ax,title="B. K-means inertia by cluster count",xlabel="Number of clusters",ylabel="Inertia")
    ax=axes[1,0]; mat=l.set_index("feature")[["PC1","PC2","PC3","PC4","PC5"]]
    feature_labels={
        "T80":"Recovery time (T80)", "Init_Supply":"Initial service",
        "Grid_Degree":"Station degree", "Grid_Impact":"Station impact",
        "Grid_Betweenness":"Station betweenness", "Redundancy_HHI":"Mapping concentration",
        "Pre_1970_Ratio":"Older housing share", "Pop_Density":"Population density",
        "log1p(Pop_Density)":"Log population density",
        "SOVI_SCORE":"Social-vulnerability score", "NRI_RISK_SCORE":"NRI risk score",
        "NRI_BUILDVALUE":"NRI building exposure",
        "log1p(NRI_BUILDVALUE)":"Log building exposure",
    }
    mat.index=[feature_labels.get(str(x),str(x)) for x in mat.index]
    sns.heatmap(mat,ax=ax,cmap="RdBu_r",center=0,cbar_kws={"label":"Loading","shrink":.8},
                linewidths=.25,linecolor="white",annot=False)
    ax.set_title("C. PCA feature loadings",fontsize=july.FS_TITLE,loc="left")
    ax.set_xlabel("Principal component",fontsize=july.FS_LABEL); ax.set_ylabel("")
    ax.tick_params(axis="both",labelsize=7.0)
    ax=axes[1,1]
    cmap={str(k):july.STAGE7_IJDRR_CLUSTER_PALETTE[i%len(july.STAGE7_IJDRR_CLUSTER_PALETTE)] for i,k in enumerate(sorted(c.cluster.unique()))}
    for key,part in c.groupby("cluster"):
        ax.scatter(part.PC1,part.PC2,s=5,alpha=.62,color=cmap[str(key)],label=f"Cluster {key}",edgecolors="none")
    style_axis(ax,title="D. PCA scores by cluster",xlabel="PC1 score",ylabel="PC2 score")
    ax.legend(frameon=False,fontsize=7.0,ncol=1,loc="upper right")
    fig.subplots_adjust(left=.17,right=.985,bottom=.10,top=.95,wspace=.32,hspace=.34)
    save_figure(fig,"FigS09_Stage7_Diagnostics")


def make_index() -> None:
    rows = []
    groups = {
        "Fig01_Methodology_Workflow": ("Main", "How does the revised analysis connect hazard damage, restoration, network service, and community burden?", "Preserves the July tiered input-to-service-to-outcome workflow while showing the adopted revision methods.", "src/la_grid/plotting/make_methodology_workflow_figure.py", [ROOT/"provenance/legacy_outputs/Submission_Package/Figure_1.pdf"], "Caption: The workflow links fixed hazard damage samples to restoration execution, source-path service, and tract distributional outcomes; Vulnerability-first and capacity robustness are post-freeze accepted additions."),
        "Fig02_System_Network_and_Mapping": ("Main", "What retained network and tract mapping define the study?", "Shows the retained 92-station network and utility-compatible tract dependencies across the expanded study area.", "src/la_grid/plotting/build_meeting_figure_collection.py", [ROOT/"Data/JULY_UTILITY_CONSTRAINED_92.csv",ROOT/"Data/substation_graph_CEC_nodes_expanded.csv",ROOT/"Data/substation_graph_CEC_edges_expanded.csv",ROOT/"Data/source_nodes_core_expanded.csv",ROOT/"Data/LA_Tracts_With_Population.shp",ROOT/"Data/LA_Tracts_With_Population.dbf",ROOT/"Data/LA_Tracts_With_Population.shx",ROOT/"Data/LA_Tracts_With_Population.prj"], "Caption: The right panel counts mapped station links per tract. This is a dependency map, not electrical capacity or delivered power."),
        "Fig03_Unconstrained_Recovery": ("Main", "How long does Unconstrained service recovery take across realizations and tracts?", "Pairs the 1,000-realization population T80 distribution with the expanded-study-area tract T80 map in the July two-panel layout.", "src/la_grid/plotting/build_meeting_figure_collection.py", [FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",SUITE/"Stage 3 Output_expanded/tract_kpis_2pc50.csv"], "Caption: T80 is time to 80% modeled service. Panel A uses 2-hour bins without density smoothing; Panel B maps the frozen mean tract T80 values under the Unconstrained reference."),
        "Fig04_Restoration_Strategy_Tradeoffs": ("Main", "How do four selected schedules compare with the Unconstrained reference?", "Compares cumulative population burden, population T80, hospital-linked tract burden, and source-path burden across Impact-first, Hospital-first, Vulnerability-first, Degree-first, and Unconstrained.", "src/la_grid/plotting/build_meeting_figure_collection.py", [FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",FORMAL/"Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet"], "Caption: All scheduled strategies use the same frozen physical realizations. Degree-first is retained as a mechanism comparator; complete strategy results remain available in tables and Supplement."),
        "Fig05_Hospital_Priority_and_Critical_Service": ("Main", "How is hospital priority constructed and how does it relate to hospital-linked tract burden?", "Maps hospital-linked tracts and hospital-priority substations with the frozen priority order, then compares four selected strategies across matched realizations.", "src/la_grid/plotting/build_meeting_figure_collection.py", [ROOT/"Data/JULY_UTILITY_CONSTRAINED_92.csv",ROOT/"Data/hospital_with_tract_expanded.csv",ROOT/"Data/substation_graph_CEC_nodes_expanded.csv",FORMAL/"Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json",FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",FORMAL/"Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet",ROOT/"Data/LA_Tracts_With_Population.shp",ROOT/"Data/LA_Tracts_With_Population.dbf",ROOT/"Data/LA_Tracts_With_Population.shx",ROOT/"Data/LA_Tracts_With_Population.prj"], "Caption: Hospital-first prioritizes substations, not tracts directly. The priority order first counts mapped links to hospital tracts and uses total mapped population only as a tie-break. All strategies use the same damage states, repair durations, and resource realization within each physical realization."),
        "Fig06_Vulnerability_Targeting_and_Distributional_Tradeoffs": ("Main", "What distributional gains and costs accompany Vulnerability-first relative to Hospital-first?", "Combines Q1–Q4 absolute burden, quartile changes, aggregate burden/gap/Gini, and a continuous tract-effect map.", "src/la_grid/plotting/build_meeting_figure_collection.py", [FORMAL/"Equity_Amendment/Figures/FIGURE_B_SOURCE.csv",FORMAL/"Equity_Amendment/VULNERABILITY_PAIRWISE_EFFECTS.csv",FORMAL/"Equity_Amendment/Figures/FIGURE_C_SOURCE.csv",FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",FORMAL/"Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet",ROOT/"Data/LA_Tracts_With_Population.shp",ROOT/"Data/LA_Tracts_With_Population.dbf",ROOT/"Data/LA_Tracts_With_Population.shx",ROOT/"Data/LA_Tracts_With_Population.prj"], "Caption: Q4 denotes the highest social-vulnerability quartile. For each physical realization, Vulnerability-first and Hospital-first use the same damage states, repair durations, and resource realization before their outcomes are differenced. Gini is population-weighted tract-burden inequality: 0 means equal tract burden; larger values mean more unequal tract burden. The tract map displays the continuous mean change; negative values indicate reduced burden and positive values indicate increased burden."),
        "Fig07_Community_Typology_and_Hotspots": ("Main", "How do the final residential typologies and hotspot scores vary spatially?", "Shows harmonized cluster profiles, the full-domain residential typology map, and the hotspot score map.", "src/la_grid/plotting/build_meeting_figure_collection.py", [STAGE7/"vis_stage7_heatmap.pdf",STAGE7/"stage7_full_domain_tract_status.csv",ROOT/"Data/LA_Tracts_With_Population.shp",ROOT/"Data/LA_Tracts_With_Population.dbf",ROOT/"Data/LA_Tracts_With_Population.shx",ROOT/"Data/LA_Tracts_With_Population.prj"], "Caption: The typology is descriptive and is not a repair strategy. Tracts outside the residential typology eligibility domain are shown as not applicable, not as zero service or ordinary cluster members."),
        "FigS01_Damage_Severity": ("Supplement", "How do initial damage-severity states differ by hazard?", "Frozen four-hazard average damage-state distributions.", "Formal_Experiment_20260923/Stage 1 Output_expanded/vis_stage1_supp_damage_severity_scenarios.pdf", [SUITE/"Stage 1 Output_expanded/vis_stage1_supp_damage_severity_scenarios.pdf"], "Caption: Uses the frozen damage-state summaries; no new damage samples are generated."),
        "FigS02_Initial_Service": ("Supplement", "What service is initially available across hazards and where is it located?", "Combines cross-hazard initial-service distributions and full-domain maps.", "Formal_Experiment_20260923/Stage 1 Output_expanded/vis_stage1_supp_initial_supply_ecdf_scenarios.pdf", [SUITE/"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_ecdf_scenarios.pdf",SUITE/"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_maps_scenarios.pdf"], "Caption: Retains the original cross-hazard ECDF and spatial service panels."),
        "FigS03_Crew_Bases_and_Directed_Travel": ("Supplement", "Where are the frozen C57 crew origins, and how does directed travel vary by destination?", "Shows the active crew origins against all 2,315 study tracts and the retained directed-travel display.", "src/la_grid/plotting/build_meeting_figure_collection.py", [ROOT/"Data/stage45_active_crew_bases_C57.csv",ROOT/"Data/substation_graph_CEC_nodes_expanded.csv",ROOT/"Data/JULY_UTILITY_CONSTRAINED_92.csv",SUITE/"Stage 4 Output_expanded/vis_stage4_logistics_heatmap_full.pdf"], "Caption: The map uses the expanded study footprint, 92 retained stations, and the frozen C57 crew-origin allocation. Travel remains directed; these are logistics inputs, not a factorial experiment."),
        "FigS04_Network_Criticality_and_Percolation": ("Supplement", "How do static attack diagnostics and recovery-network mechanisms relate?", "Retains five static criticality curves, frozen dynamic LCC/average-degree recovery, and source-path burden effects.", "src/la_grid/plotting/build_meeting_figure_collection.py", [SUITE/"Stage 2 Output_expanded/percolation_curve_impact.csv",SUITE/"Stage 2 Output_expanded/percolation_curve_random.csv",SUITE/"Stage 2 Output_expanded/exploratory_percolation_curve_degree.csv",SUITE/"Stage 2 Output_expanded/exploratory_percolation_curve_betweenness_centrality.csv",SUITE/"Stage 2 Output_expanded/exploratory_percolation_curve_closeness_centrality.csv",original("vis_stage6_network_topology_recovery_2pc50.pdf"),SUITE/"Stage 6 Output_expanded/SOURCE_PATH_PAIRED_EFFECT_DISPLAY.csv"], "Caption: Static removal is a network diagnostic, not a repair policy. Source-path intervals show the 5–95% realization range; for each physical realization, the compared policy and Hospital-first use the same damage states, repair durations, and resource realization. Full distinct-strategy evidence is retained; Direct-community is not separately reported."),
        "FigS05_GA_Reproducibility": ("Supplement", "How stable was the retained GA result across planning seeds?", "Displays the frozen five-seed convergence record.", "src/la_grid/plotting/build_meeting_figure_collection.py", [FORMAL/"Stage 5 Output_expanded/GA_FIVE_SEED_CONVERGENCE.csv"], "Caption: Uses the existing five-seed planning record; no GA is rerun."),
        "FigS06_Mapping_Robustness": ("Supplement", "How sensitive are results to the utility-compatible cutoff, and how do mapped sites compare with public SCE candidates?", "Shows the frozen cutoff response and discrete 337-tract SCE benchmark with reader-facing mapping names.", "src/la_grid/plotting/build_meeting_figure_collection.py", [ROOT/"provenance/reviewer_working/Supplement_Rebuild_20260925/Tables/S3_CUTOFF_HOSPITAL_FIRST_2PC50.csv",ROOT/"provenance/reviewer_working/Supplement_Rebuild_20260925/Tables/S3_SCE_337_CANDIDATE_BENCHMARK.csv"], "Caption: The cutoff check uses the frozen Hospital-first 2pc50 realizations. The strict-SCE benchmark covers 337 comparable tracts; Any match, Top 1 and Top 3 are separate discrete comparisons. No internal mapping codes appear in the artwork."),
        "FigS07_Source_Redundancy": ("Supplement", "How do alternative paths contribute to source connectivity during recovery and across stations?", "Combines dynamic alternative-route contribution with frozen station reliabilities mapped on the expanded study area.", "src/la_grid/plotting/build_meeting_figure_collection.py", [original("vis_source_reliability_dynamic_redundancy_2pc50.pdf"),ROOT/"results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv",ROOT/"results/diagnostics/SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv",ROOT/"Data/JULY_UTILITY_CONSTRAINED_92.csv"], "Caption: Panel C is conditional on target-station functionality; panel D is the alternative-route gain beyond a fixed precomputed path. These are connectivity diagnostics, not delivered power or capacity."),
        "FigS08_Capacity_Sensitivity": ("Supplement", "Does source reachability imply facility-level electrical adequacy, and how large is the bounded burden increment?", "Shows 34 documented SCE planning-loading rows and the small 2pc50 capacity-bounded burden increments for the four displayed policies.", "src/la_grid/plotting/build_meeting_figure_collection.py", [original("vis_source_gate_connected_vs_facility_loading.pdf"),ROOT/"results/capacity/SCE_CAPACITY_SENSITIVITY_SUMMARY.csv",ROOT/"results/capacity/CONNECTED_VS_ELECTRICAL_CONSTRAINT_BENCHMARK.csv"], "Caption: Facility loading is documented planning-condition evidence, not earthquake-time loading. The capacity-bounded comparison is a separate sensitivity. Its burden axis uses an explicitly expanded scale."),
        "FigS09_Stage7_Diagnostics": ("Supplement", "What dimensionality and clustering diagnostics support the final Stage 7 typology?", "Groups frozen PCA variance, K-means diagnostics, loadings, and the existing PC score scatter.", "src/la_grid/plotting/build_meeting_figure_collection.py", [STAGE7/"pca_stats_with_eigenvalues.csv",STAGE7/"kmeans_k_diagnostics.csv",STAGE7/"pca_loadings.csv",STAGE7/"clusters_labels_final.csv"], "Caption: PCA scores, loadings, and diagnostic values are read from the final harmonized Stage 7 authority; no PCA or clustering is rerun."),
    }
    file_rows = []
    for stem, (role, question, message, generator, sources, caption) in groups.items():
        ext_paths = {"pdf": OUT/(stem+".pdf"), "png": OUT/(stem+".png")}
        for fmt, path in ext_paths.items():
            if not path.is_file():
                raise FileNotFoundError(path)
            source_paths = [p for p in sources if p.is_file()]
            if not source_paths:
                raise FileNotFoundError(f"No source authority found for {stem}")
            primary_source = source_paths[0]
            # Record exact source-data identities, including all panels of a composite.
            source_list = [rel(p) for p in source_paths]
            hash_list = [digest(p) for p in source_paths]
            file_rows.append({
                "figure_number": stem.split("_")[0], "file": path.name, "role": role,
                "scientific_question": question, "main_message": message,
                "source_authority": "; ".join(source_list), "source_path": rel(primary_source),
                "generator": generator, "format": fmt,
                "submission_status": "UNAPPROVED review draft · vector PDF" if fmt == "pdf" else "UNAPPROVED review draft · 600-dpi preview",
                "notes": caption, "scientific_content": question,
                "current_status": "unapproved presentation draft from frozen result tables / vector source panels",
                "main_or_supplement": role.lower(), "sha256_or_lfs_oid": "sha256:"+digest(path),
                "include_in_final_figure_collection": "False",
                "source_data_path": ";".join(source_list), "source_data_sha256": ";".join("sha256:"+h for h in hash_list),
            })
    with (OUT/"FIGURE_INDEX.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=list(file_rows[0].keys()))
        writer.writeheader(); writer.writerows(file_rows)
    lines=["# Unapproved artwork drafts", "", "These are review drafts. They do not replace the protected July submission or the current `results/figures/` authority.", "", "Columns in `FIGURE_INDEX.csv` identify the scientific question, source authority, generator, format, and review status.", "", "## Proposed main figures: Fig01–Fig07", ""]
    main_sentences=[(s,groups[s][1]) for s in groups if s.startswith("Fig0")]
    for stem, question in main_sentences: lines.append(f"- **{stem}** — {question}")
    lines += ["", "## Proposed supplement: FigS01–FigS09", ""]
    supp_sentences=[(s,groups[s][1]) for s in groups if s.startswith("FigS")]
    for stem, question in supp_sentences: lines.append(f"- **{stem}** — {question}")
    (OUT/"README.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main() -> None:
    configure()
    from la_grid.plotting.make_methodology_workflow_figure import build_figure
    workflow_pdf, workflow_png, _ = build_figure()
    shutil.copy2(workflow_pdf, OUT/"Fig01_Methodology_Workflow.pdf")
    shutil.copy2(workflow_png, OUT/"Fig01_Methodology_Workflow.png")
    plot_fig02()
    plot_fig03()
    main_data=baseline_realizations()
    plot_fig04(main_data); plot_fig05(main_data); plot_fig06(main_data); plot_fig07()
    # Existing frozen panels are reused or combined at native scale, never re-rendered from pixels.
    copy_pair("vis_stage1_supp_damage_severity_scenarios", "FigS01_Damage_Severity",
              source_dir=SUITE/"Stage 1 Output_expanded")
    combine_pdf_panels("FigS02_Initial_Service", [
        ("",SUITE/"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_ecdf_scenarios.pdf"),
        ("",SUITE/"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_maps_scenarios.pdf")])
    combine_pdf_panels("FigS03_Crew_Bases_and_Directed_Travel", [
        ("",plot_supp_fig03_crew_map()),
        ("",SUITE/"Stage 4 Output_expanded/vis_stage4_logistics_heatmap_full.pdf")])
    (OUT/"_FigS03_expanded_crew_map.pdf").unlink(missing_ok=True)
    plot_supp_fig04(); plot_supp_fig05()
    plot_supp_fig06()
    station_map = plot_supp_fig07_station_map()
    combine_pdf_panels("FigS07_Source_Redundancy", [
        ("",original("vis_source_reliability_dynamic_redundancy_2pc50.pdf")),
        ("",station_map)])
    station_map.unlink(missing_ok=True)
    capacity_panel = plot_capacity_increment_panel()
    combine_pdf_panels("FigS08_Capacity_Sensitivity", [
        ("", original("vis_source_gate_connected_vs_facility_loading.pdf")),
        ("", capacity_panel)])
    capacity_panel.unlink(missing_ok=True)
    plot_supp_fig09()
    make_index()


if __name__ == "__main__":
    main()
