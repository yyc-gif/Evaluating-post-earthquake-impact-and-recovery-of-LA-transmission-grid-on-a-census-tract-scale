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
from PIL import Image

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


def save_figure(fig, stem: str, *, tight: bool = True) -> None:
    pdf = OUT / f"{stem}.pdf"
    png = OUT / f"{stem}.png"
    bbox = "tight" if tight else None
    fig.savefig(pdf, format="pdf", bbox_inches=bbox, pad_inches=.04 if tight else 0,
                facecolor="white", metadata={"Creator": "LA Grid presentation-only renderer"})
    fig.savefig(png, format="png", dpi=600, bbox_inches=bbox, pad_inches=.04 if tight else 0,
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
        ("R_path_full", "C. Full-network conditional reachability", "Blues",
         "Conditional source-path reliability"),
        ("Delta_R_redundancy", "D. Alternative-route gain", "Reds",
         "Additional reliability from alternate routes"),
    ]
    for ax, (column, title, palette, scale_label) in zip(axes, specifications):
        draw_tract_base(ax, tracts)
        for edge in edges.itertuples(index=False):
            if edge.u in lookup.index and edge.v in lookup.index:
                a, b = lookup.loc[edge.u], lookup.loc[edge.v]
                ax.plot([a.x, b.x], [a.y, b.y], color="#9ca5aa", lw=.36, alpha=.38, zorder=2)
        scatter = ax.scatter(non.geometry.x, non.geometry.y, c=non[column], cmap=palette,
                             vmin=0, vmax=float(non[column].max()), s=10,
                             edgecolors="white", linewidths=.25, zorder=3)
        ax.scatter(core.geometry.x, core.geometry.y, marker="^", s=12,
                   facecolors="#26323b", edgecolors="white", linewidths=.32, zorder=4)
        ax.set_title(title, fontsize=july.FS_TITLE, weight="bold", pad=5)
        cbar = fig.colorbar(scatter, ax=ax, orientation="horizontal", fraction=.045, pad=.025,
                            shrink=.82)
        cbar.set_label(scale_label, fontsize=7.1)
        cbar.ax.tick_params(labelsize=7.0, width=.5, length=2)
        cbar.outline.set_linewidth(.5)
    fig.legend(handles=[Line2D([], [], marker="^", color="none", markerfacecolor="#26323b",
                               markeredgecolor="white", markersize=4, label="Core source")],
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
    """Restore the July real-network panels and retain the revised M1 mapping.

    July panels A and B are reused pixel-for-pixel. The former percolation panel
    C is replaced with the already-frozen revised mapping table. No scientific
    path or mapping calculation is repeated.
    """
    july_png = (ROOT / "provenance" / "legacy_outputs" /
                "Submission_Package" / "Figure_2.png")
    if not july_png.is_file():
        raise FileNotFoundError(july_png)
    old = Image.open(july_png).convert("RGB")
    if old.size != (4370, 5925):
        raise ValueError(f"Unexpected frozen July Figure 2 raster: {old.size}")
    physical_panel = old.crop((0, 0, old.width, 2055))
    path_panel = old.crop((0, 2070, old.width, 4215))

    tracts = tract_geometry()
    mapping = pd.read_csv(ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv",
                          dtype={"tract_id": str, "substation_id": str})
    mapping["tract_id"] = mapping.tract_id.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
    counts = mapping.groupby("tract_id").substation_id.nunique().rename("links")
    tracts = tracts.merge(counts, left_on="tract_id_norm", right_index=True,
                          how="left", validate="one_to_one")
    if len(tracts) != 2315 or tracts.links.isna().any():
        raise ValueError("Revised mapping display must cover all 2,315 study tracts")
    fig, ax = plt.subplots(figsize=(18.5 * CM, 7.4 * CM))
    tracts.plot(column="links", ax=ax, cmap="Blues", vmin=1,
                vmax=max(1, int(tracts.links.max())), edgecolor="#bcbcbc",
                linewidth=.12, legend=True,
                legend_kwds={"label": "Mapped substations per tract", "shrink": .72, "pad": .02})
    ax.set_axis_off(); ax.set_aspect("equal")
    fig.subplots_adjust(left=.06, right=.94, bottom=.03, top=.91)
    map_pdf = OUT / "_Fig02_M1_mapping_panel.pdf"
    fig.savefig(map_pdf, format="pdf", bbox_inches="tight", pad_inches=.025,
                facecolor="white", metadata={"Creator": "LA Grid presentation-only renderer"})
    plt.close(fig)

    width = 524.4094
    px_to_pt = width / old.width
    crops = [physical_panel, path_panel]
    crop_heights = [im.height * px_to_pt for im in crops]
    map_doc = fitz.open(map_pdf); map_page = map_doc[0]
    map_height = width * map_page.rect.height / map_page.rect.width
    header, gap = 15.0, 5.0
    page_height = sum(crop_heights) + map_height + header + 2 * gap
    doc = fitz.open(); page = doc.new_page(width=width, height=page_height)
    page.insert_font(fontname="ArBold", fontfile=str(ARIAL_BOLD))
    y = gap
    for i, image in enumerate(crops):
        tmp = OUT / f"_Fig02_july_panel_{i+1}.png"
        image.save(tmp, dpi=(600, 600))
        h = crop_heights[i]
        page.insert_image(fitz.Rect(0, y, width, y + h), filename=str(tmp))
        y += h + gap
    page.insert_text((8, y + 10.2), "C. Revised utility-compatible tract–substation mapping",
                     fontname="ArBold", fontsize=9.5, color=(.12, .17, .20))
    y += header
    page.show_pdf_page(fitz.Rect(0, y, width, y + map_height), map_doc, 0,
                       keep_proportion=True)
    doc.save(OUT / "Fig02_System_Network_and_Mapping.pdf", garbage=4, deflate=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(600/72, 600/72), alpha=False)
    pix.set_dpi(600, 600); pix.save(OUT / "Fig02_System_Network_and_Mapping.png")
    doc.close(); map_doc.close(); map_pdf.unlink(missing_ok=True)
    for i in (1, 2):
        (OUT / f"_Fig02_july_panel_{i}.png").unlink(missing_ok=True)


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
    ax.set_title("Crew origins across the study area (57 modeled crews)", fontsize=july.FS_TITLE, pad=4)
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
                      (primary.strategy_id.isin([
                          "centrality-first", "impact-first", "betweenness-first", "degree-first",
                          "closeness-first", "hospital-first", "random", "unconstrained",
                      ]))].copy()
    vuln = pd.read_parquet(FORMAL / "Equity_Amendment" / "VULNERABILITY_PRIMARY_SUMMARY.parquet")
    vuln = vuln[(vuln.hazard == "2pc50") & (vuln.resource_scenario == "C57_D1") &
                (vuln.mapping == "M1_UTILITY_003") & (vuln.gate == "G1_BASELINE_050") &
                (vuln.strategy_id == "vulnerability-first")].copy()
    d = pd.concat([primary, vuln], ignore_index=True)
    expected = {"centrality-first", "impact-first", "betweenness-first", "degree-first",
                "closeness-first", "hospital-first", "random", "vulnerability-first", "unconstrained"}
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
    """Show complete recovery paths and outcome distributions for all policies.

    Curves and realization-level distributions are read from frozen outputs;
    this function changes only their presentation.
    """
    curve_path = SUITE / "Stage 6 Output_expanded" / "ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv"
    curves = pd.read_csv(curve_path)
    curves = curves[curves.hazard.eq("2pc50")].copy()
    all_keys = ["unconstrained", "centrality-first", "impact-first", "betweenness-first",
                "degree-first", "closeness-first", "hospital-first", "random",
                "vulnerability-first"]
    if set(curves.strategy_id.unique()) != set(all_keys):
        raise ValueError("Frozen 2pc50 curve table must include eight scheduled policies and Unconstrained")
    style_map = {key: july._stage6_line_style(key, role="recovery")
                 for key in all_keys if key != "unconstrained"}
    style_map["vulnerability-first"] = {
        "color": STRATEGY_COLORS["vulnerability-first"], "ls": "-", "lw": 1.08,
        "alpha": .9, "zorder": 9,
    }
    style_map["betweenness-first"] = {**style_map["betweenness-first"],
                                     "color": STRATEGY_COLORS["betweenness-first"]}
    # The legacy Random gray is darkened slightly so its line remains visible
    # on a white page while its marker/line role remains unchanged.
    style_map["random"] = {**style_map["random"], "color": "#858585"}
    style_map["unconstrained"] = {"color": "#111111", "ls": "--", "lw": 1.3,
                                  "alpha": .98, "zorder": 11}
    fig = plt.figure(figsize=(18.5 * CM, 19.0 * CM))
    gs = fig.add_gridspec(4, 1, height_ratios=[1.2, 1.0, 1.0, 1.0], hspace=.52)
    ax_curve = fig.add_subplot(gs[0, 0])
    for key in all_keys:
        part = curves[curves.strategy_id.eq(key)].sort_values("time_hr")
        line_style = style_map[key]
        ax_curve.step(part.time_hr, part.mean_population_availability_proxy,
                      where="post", color=line_style["color"], linestyle=line_style["ls"],
                      linewidth=line_style["lw"], alpha=line_style["alpha"],
                      label=STRATEGY_LABELS[key], zorder=line_style["zorder"])
    style_axis(ax_curve, title="A. Population-weighted service recovery",
               xlabel="Time after earthquake (h)", ylabel="Modeled service availability")
    ax_curve.set_xlim(0, 120); ax_curve.set_ylim(0, 1.04)
    ax_curve.set_yticks(np.linspace(0, 1, 6))
    ax_curve.grid(True, color="#e4e4e4", linewidth=.4, linestyle="--", alpha=.68)
    handles, labels = ax_curve.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .998), ncol=3,
               frameon=False, fontsize=7.0, handlelength=1.7,
               columnspacing=1.1, handletextpad=.38)

    panels = [
        ("population_resolved_mass_weighted_burden_hr", "B. Population-weighted cumulative service burden", "Cumulative burden (h)"),
        ("hospital_mean_normalized_burden_hr", "C. Hospital-linked tract cumulative burden", "Cumulative burden (h)"),
        ("population_T80_hr", "D. Population time to 80% service", "Time (h)"),
    ]
    for ax, (metric, title, xlabel) in zip(
            [fig.add_subplot(gs[i, 0]) for i in range(1, 4)], panels):
        values = [data.loc[data.strategy_id.eq(key), metric].dropna().to_numpy(float)
                  for key in all_keys]
        if any(len(v) != 1000 for v in values):
            raise ValueError(f"Expected 1,000 frozen realization values for {metric}")
        positions = np.arange(len(all_keys), 0, -1)
        artists = ax.boxplot(values, vert=False, positions=positions, widths=.58,
                             whis=(5, 95), showfliers=False, patch_artist=True,
                             medianprops={"linewidth": 1.05},
                             whiskerprops={"linewidth": .75},
                             capprops={"linewidth": .75})
        for box, key in zip(artists["boxes"], all_keys):
            box.set_facecolor(STRATEGY_COLORS[key]); box.set_edgecolor(STRATEGY_COLORS[key])
            box.set_alpha(.32); box.set_linewidth(.75)
        for med, key in zip(artists["medians"], all_keys):
            med.set_color(STRATEGY_COLORS[key]); med.set_linewidth(1.05)
        for i, key in enumerate(all_keys):
            for whisk in artists["whiskers"][2*i:2*i+2]:
                whisk.set_color(STRATEGY_COLORS[key])
            for cap in artists["caps"][2*i:2*i+2]:
                cap.set_color(STRATEGY_COLORS[key])
        ax.set_yticks(positions, [STRATEGY_LABELS[k] for k in all_keys])
        ax.tick_params(axis="y", labelsize=7.1, length=0)
        style_axis(ax, title=title, xlabel=xlabel, ylabel=None)
        ax.grid(True, axis="x", color="#e4e4e4", linewidth=.4, linestyle="--", alpha=.68)
        ax.grid(False, axis="y")
    fig.subplots_adjust(left=.22, right=.985, bottom=.045, top=.91)
    save_figure(fig, "Fig04_Restoration_Strategy_Tradeoffs", tight=False)


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
    colors = np.where(tracts.hospital_link, "#d9c8eb", "#f7f7f7")
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
    handles = [Patch(facecolor="#d9c8eb", edgecolor="none", label="Hospital-linked tracts"),
               Line2D([], [], marker="o", color="none", markerfacecolor="#55758b", markeredgecolor="white", markersize=4, label="All substations"),
               Line2D([], [], marker="o", color="none", markerfacecolor="#a65628", markeredgecolor="white", markersize=4, label="Hospital-priority substations"),
               Line2D([], [], marker="o", color="none", markerfacecolor="white", markeredgecolor="#a65628", markersize=5,
                      label="Numbered circles = substation priority rank")]
    axmap.legend(handles=handles, frameon=False, loc="lower center", bbox_to_anchor=(.5,-.14),
                 fontsize=7.0, ncol=2, columnspacing=.8, handlelength=1.0)
    keys = STRATEGIES
    plot_box(axbox, data, "hospital_mean_normalized_burden_hr", keys, width=.50)
    axbox.set_xticks([1,2,3,4], ["Impact-\nfirst", "Hospital-\nfirst", "Vulnerability-\nfirst", "Degree-\nfirst"])
    style_axis(axbox, title="B. Hospital-linked burden", xlabel=None,
               ylabel="Cumulative burden (h)")
    axbox.tick_params(axis="x", labelsize=7.0)
    fig.subplots_adjust(left=.035, right=.98, bottom=.20, top=.91)
    save_figure(fig, "Fig05_Hospital_Priority_and_Critical_Service", tight=False)


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
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.16],
                          hspace=.34, wspace=.28)
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
    ax_a.set_xticks(np.arange(4), ["Q1", "Q2", "Q3", "Q4"])
    style_axis(ax_a, title="A. Absolute burden by social-vulnerability quartile", xlabel=None, ylabel="Cumulative burden (h)")
    handles, labels = ax_a.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=7.2, ncol=3,
               loc="upper center", bbox_to_anchor=(.5, .992))
    b = effect[effect.metric.isin([f"burden_Q{i}_hr" for i in range(1,5)])].copy()
    b["quartile"] = b.metric.str.extract(r"(Q[1-4])")
    b = b.set_index("quartile").loc[q_order]
    yy = b.paired_mean_difference.to_numpy(float)
    ci_low = b.bootstrap_ci_low.to_numpy(float); ci_high = b.bootstrap_ci_high.to_numpy(float)
    qx = np.arange(4)
    ax_b.errorbar(qx, yy, yerr=np.vstack([yy - ci_low, ci_high - yy]),
                  fmt="o", color=STRATEGY_COLORS["vulnerability-first"], ecolor=STRATEGY_COLORS["vulnerability-first"],
                  lw=1.0, capsize=2.2, markersize=4.2)
    ax_b.axhline(0, color="#666666", lw=.65, ls="--")
    ax_b.set_xticks(qx, ["Q1\n(lowest)", "Q2", "Q3", "Q4\n(highest)"])
    style_axis(ax_b, title="B. Quartile burden change", xlabel="Social-vulnerability quartile",
               ylabel="Change relative to Hospital-first (h)")
    ax_b.tick_params(axis="x", labelsize=7.0, rotation=0)
    ax_b.grid(True, axis="y", color="#e4e4e4", linewidth=.4, alpha=.68); ax_b.grid(False, axis="x")
    ax_b.set_ylim(min(float(ci_low.min()), 0) - .35, max(float(ci_high.max()), 0) + .42)
    for qlabel, estimate, xpos in zip(["Q1", "Q2", "Q3", "Q4"], yy, qx):
        ax_b.annotate(f"{estimate:+.3f} h", (xpos, estimate), xytext=(0, 6),
                      textcoords="offset points", ha="center", va="bottom", fontsize=7.0,
                      color=STRATEGY_COLORS["vulnerability-first"])
    # Panel C is a dot-and-interval effect profile, not a numeric table. Each
    # row has its own scale because the effects have different units/magnitudes.
    effect_rows = [
        ("population_resolved_mass_weighted_burden_hr", "Population-weighted cumulative\nservice burden (h)", "h"),
        ("absolute_Q4_minus_Q1_hr", "High–low vulnerability burden\ndifference (h)", "h"),
        ("burden_gini", "Tract-burden inequality\n(population-weighted Gini)", ""),
        ("population_T80_hr", "Population time to 80%\nservice (h)", "h"),
        ("hospital_mean_normalized_burden_hr", "Hospital-linked tract cumulative\nburden (h)", "h"),
    ]
    effect_lookup = effect.set_index("metric")
    ax_c.remove()
    cgrid = gs[1, 0].subgridspec(6, 3, height_ratios=[.62, 1, 1, 1, 1, 1],
                                 width_ratios=[1.2, 1.45, .55], hspace=.25, wspace=.12)
    title_ax = fig.add_subplot(cgrid[0, :]); title_ax.set_axis_off()
    title_ax.text(.5, .60, "C. Broader distributional and system effects",
                  ha="center", va="center", fontsize=july.FS_TITLE,
                  fontweight="bold", color="#26323b", transform=title_ax.transAxes)
    title_ax.text(.5, .05, "Dot = mean change; line = 95% interval; scales are metric-specific.",
                  ha="center", va="center", fontsize=7.0, color="#555555",
                  transform=title_ax.transAxes)
    for idx, (metric, label, unit) in enumerate(effect_rows):
        if metric not in effect_lookup.index:
            raise ValueError(f"Frozen paired-effects table missing {metric}")
        row = effect_lookup.loc[metric]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]
        value = float(row.paired_mean_difference)
        ci0 = float(row.bootstrap_ci_low); ci1 = float(row.bootstrap_ci_high)
        row_id = idx + 1
        label_ax = fig.add_subplot(cgrid[row_id, 0]); label_ax.set_axis_off()
        plot_ax = fig.add_subplot(cgrid[row_id, 1])
        value_ax = fig.add_subplot(cgrid[row_id, 2]); value_ax.set_axis_off()
        span = max(abs(ci0), abs(ci1), .01) * 1.32
        plot_ax.set_xlim(-span, span); plot_ax.set_ylim(-.5, .5)
        plot_ax.axvline(0, color="#737373", lw=.6, ls="--", zorder=0)
        plot_ax.hlines(0, ci0, ci1, color=STRATEGY_COLORS["vulnerability-first"], lw=1.15, zorder=2)
        plot_ax.plot(value, 0, marker="o", ms=3.8, color=STRATEGY_COLORS["vulnerability-first"], zorder=3)
        plot_ax.set_yticks([]); plot_ax.set_xticks([])
        for spine in ("left", "right", "top", "bottom"):
            plot_ax.spines[spine].set_visible(False)
        label_ax.text(1, .5, label, ha="right", va="center", fontsize=7.0,
                      color="#26323b", transform=label_ax.transAxes)
        value_ax.text(0, .5, f"{value:+.3f}{' '+unit if unit else ''}",
                      ha="left", va="center", fontsize=7.0,
                      color=STRATEGY_COLORS["vulnerability-first"],
                      transform=value_ax.transAxes)
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
    style_axis(ax_d, title="D. Continuous tract effect", xlabel=None, ylabel=None)
    ax_d.set_axis_off(); ax_d.set_aspect("equal")
    # Population summaries retain continuous sign and magnitude; no threshold band is introduced.
    delta = mapped[["effect_population", "mean_paired_delta_burden_hr"]].dropna()
    pop = delta.effect_population.to_numpy(float); val = delta.mean_paired_delta_burden_hr.to_numpy(float)
    lower = float(pop[val < 0].sum()); higher = float(pop[val > 0].sum()); equal = float(pop[val == 0].sum())
    fig.text(.08, .064, "Q4 = highest and Q1 = lowest social-vulnerability quartile. Population-weighted Gini: 0 = equal tract burden; larger = more unequal.",
             fontsize=7.0, ha="left", va="center")
    fig.text(.08, .043, f"Population with lower / higher burden: {lower/1e6:.2f} / {higher/1e6:.2f} million.",
             fontsize=7.0, ha="left", va="center")
    fig.subplots_adjust(left=.08, right=.92, bottom=.095, top=.88)
    save_figure(fig, "Fig06_Vulnerability_Targeting_and_Distributional_Tradeoffs", tight=False)


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
    # The original pale yellow cluster was difficult to distinguish on the
    # white tract boundary layer. Use a muted, color-vision-friendlier display
    # palette only; cluster IDs and membership remain unchanged.
    review_colors = ["#2878B5", "#D55E00", "#2A8C68", "#9A6FB0", "#52606D"]
    cmap = {str(c): review_colors[i % len(review_colors)] for i,c in enumerate(sorted(merged[cluster_col].dropna().unique(), key=lambda x: int(float(x))))}
    colors = merged[cluster_col].map(lambda x: cmap.get(str(x), july.STAGE7_NA_COLOR))
    f1, ax1 = plt.subplots(figsize=(8.9 * CM, 7.2 * CM))
    draw_tract_base(ax1, merged, colors)
    ax1.set_title("B. Residential typology", fontsize=july.FS_TITLE, loc="center", pad=3)
    handles = [Patch(facecolor=c, edgecolor="white", linewidth=.25, label=f"Cluster {int(float(k))}") for k,c in cmap.items()]
    handles.append(Patch(facecolor=july.STAGE7_NA_COLOR, edgecolor="#bcbcbc", linewidth=.35, label="Not in residential typology"))
    ax1.legend(handles=handles, frameon=False, loc="upper center", bbox_to_anchor=(.5,-.02), ncol=2, fontsize=7.0)
    f1.subplots_adjust(left=.02, right=.98, top=.91, bottom=.24)
    cluster_pdf = OUT / "_Fig07_cluster_map_panel.pdf"
    f1.savefig(cluster_pdf, bbox_inches="tight", pad_inches=.025, facecolor="white")
    plt.close(f1)
    f2, ax2 = plt.subplots(figsize=(8.9 * CM, 7.2 * CM))
    merged.plot(column=score_col, ax=ax2, cmap="Blues",
                edgecolor="#c9c9c9", linewidth=.12, legend=True,
                legend_kwds={"label": "Slow-vulnerable hotspot score", "shrink": .67, "pad": .02},
                missing_kwds={"color": july.STAGE7_NA_COLOR, "edgecolor": "#bcbcbc", "label": "Not in residential typology"})
    ax2.set_axis_off(); ax2.set_aspect("equal")
    ax2.set_title("C. Hotspot score", fontsize=july.FS_TITLE, loc="center", pad=3)
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
    # Build a full-width page while keeping all three panels at their native
    # physical size; only the containing page gains a little white margin.
    docs = [(title, fitz.open(path)) for title, path in panels]
    prof = docs[0][1][0]
    map1, map2 = docs[1][1][0], docs[2][1][0]
    width = 524.4094
    gap_h = 4.0
    bottom_h = max(map1.rect.height, map2.rect.height)
    title_h = 17.0
    total_h = title_h + prof.rect.height + gap_h + bottom_h + 4.0
    outdoc = fitz.open(); page = outdoc.new_page(width=width, height=total_h)
    page.insert_font(fontname="ArBold", fontfile=str(ARIAL_BOLD))
    title_rect = fitz.Rect(0, 1, width, 15)
    page.insert_textbox(title_rect, "A. Cluster profile differences", fontname="ArBold",
                        fontsize=9.5, color=(.1,.1,.1), align=1, overlay=True)
    x_profile = (width - prof.rect.width) / 2
    page.show_pdf_page(fitz.Rect(x_profile,title_h,x_profile+prof.rect.width,title_h+prof.rect.height),
                       docs[0][1], 0, keep_proportion=True)
    y = title_h + prof.rect.height + gap_h
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
    if d.search_improved_incumbent.astype(bool).any() or d.best_generation.ne(0).any():
        raise ValueError("Frozen GA closure no longer matches the retained-incumbent result")
    if not np.allclose(d.fitness,d.incumbent_fitness,atol=1e-12):
        raise ValueError("Frozen GA final scores do not match their retained incumbents")
    rules=pd.read_csv(FORMAL/"Stage 5 Output_expanded"/"INCUMBENT_DIRECT_SCORES_2pc50.csv")
    if not np.allclose(rules.planning_fitness,-rules.planning_burden_hr,atol=1e-9):
        raise ValueError("Fixed-rule scores do not match the frozen planning-burden definition")
    rules=rules.sort_values("planning_burden_hr",ascending=True)
    histories=[]
    for seed in sorted(d.seed.astype(int)):
        h=pd.read_csv(FORMAL/"Stage 5 Output_expanded"/f"GA_HISTORY_2pc50_{seed}.csv")
        if len(h)!=101 or set(h.seed.astype(int))!={seed}:
            raise ValueError(f"Unexpected frozen GA history for seed {seed}")
        histories.append(h)
    fig,axes=plt.subplots(1,2,figsize=(18.5*CM,9.2*CM),gridspec_kw={"width_ratios":[.86,1.14]})
    ax=axes[0]; y=np.arange(len(rules))[::-1]
    for yy,row in zip(y,rules.itertuples(index=False)):
        color=STRATEGY_COLORS.get(row.rule,"#555555")
        ax.hlines(yy,0,row.planning_burden_hr,color="#dddddd",lw=.7,zorder=1)
        ax.plot(row.planning_burden_hr,yy,marker="o",ms=4.1,color=color,zorder=2)
        ax.annotate(f"{row.planning_burden_hr:.3f}",(row.planning_burden_hr,yy),xytext=(4,0),
                    textcoords="offset points",ha="left",va="center",fontsize=7.0,color="#26323b")
    ax.set_yticks(y,[STRATEGY_LABELS.get(k,k) for k in rules.rule])
    style_axis(ax,title="A. Fixed-rule planning objectives",xlabel="Planning burden (h; lower is better)",ylabel=None)
    ax.set_xlim(0,float(rules.planning_burden_hr.max())*1.18); ax.grid(False,axis="y")
    ax=axes[1]
    trace_colors=["#2878B5","#D55E00","#2A8C68","#9A6FB0","#52606D"]
    for h,color in zip(histories,trace_colors):
        ax.plot(h.generation,-h.generation_mean,color=color,lw=.82,alpha=.78,
                label=f"Seed {int(h.seed.iloc[0])}")
    incumbent=float(rules.loc[rules.rule.eq("impact-first"),"planning_burden_hr"].iloc[0])
    ax.axhline(incumbent,color=STRATEGY_COLORS["impact-first"],lw=1.2,ls="--",
               label=f"Impact-first incumbent ({incumbent:.3f} h)")
    style_axis(ax,title="B. Genetic algorithm (GA) search across five seeds",
               xlabel="Generation",ylabel="Mean candidate planning burden (h)")
    ax.set_xlim(0,100); ax.set_xticks([0,20,40,60,80,100])
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.5, .995),
               frameon=False, ncol=3, fontsize=7.0, handlelength=1.4, columnspacing=1.0)
    fig.text(.5,.025,"No seed improved the retained incumbent; the resolved GA sequence equals Impact-first.",
             ha="center",va="center",fontsize=7.1,color="#26323b")
    fig.subplots_adjust(left=.14,right=.985,bottom=.17,top=.84,wspace=.32)
    save_figure(fig,"FigS05_GA_Reproducibility")


def plot_supp_fig06() -> None:
    """Show frozen mapping-cutoff, external-match and mapping-effect results."""
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
    effects_path=SUITE/"Sensitivity Output_clean"/"FORMAL_MAPPING_EFFECTS.csv"
    effects=pd.read_csv(effects_path)
    effects=effects[(effects.comparison.eq("full92"))&(effects.domain.eq("mapping_native_domain"))&
                    (effects.reference_mapping.eq("M0_JULY_003"))&(effects.target_mapping.eq("M1_UTILITY_003"))&
                    (effects.metric.eq("population_resolved_mass_weighted_burden_hr"))&
                    (effects.strategy_id.eq("hospital-first"))].copy()
    if len(effects)!=4:
        raise ValueError("Expected four frozen hazard-level July-to-revised mapping effects")
    shifts=pd.read_parquet(FORMAL/"Formal_Results"/"TRACT_MAPPING_SHIFT.parquet")
    shifts=shifts[(shifts.hazard.eq("2pc50"))&(shifts.strategy_id.eq("hospital-first"))]
    shift_values=shifts.mean_M1_minus_M0_burden_hr.to_numpy(float)
    if len(shift_values)!=2315 or int((np.abs(shift_values)>1).sum())!=246:
        raise ValueError("Frozen tract mapping shifts do not match the 2,315-tract / 246-over-1h result")
    fig, axes = plt.subplots(2, 2, figsize=(18.5 * CM, 11.5 * CM))
    ax = axes[0,0]
    ax.plot([0, 1, 3], values, color=STRATEGY_COLORS["hospital-first"],
            marker="o", markersize=4.0, lw=1.0)
    ax.axhline(0, color="#777777", lw=.55, ls="--")
    ax.axvline(3, color="#7a3e65", lw=.7, ls=(0, (3, 2)), zorder=0)
    ax.set_xticks([0, 1, 3], ["No cutoff", "1%", "3% production"])
    for xx,vv in zip([0,1,3],values):
        if xx == 3:
            # The 3% production case defines the zero reference; do not add a
            # second zero label beside its x tick.
            continue
        else:
            ax.annotate(f"{vv:+.3f}",(xx,vv),xytext=(0,-12),textcoords="offset points",
                        ha="center",va="top",fontsize=7.0)
    style_axis(ax, title="A. Effect of the mapping-weight cutoff", xlabel="Candidate-weight cutoff",
               ylabel="Change from 3% production (h)")
    ax.set_xlim(-.18, 3.55)
    ax.annotate("Selected cutoff: 3%", xy=(3, .015),
                xytext=(1.55, max(values) * .78), textcoords="data",
                ha="center", va="center", fontsize=7.0, color="#7a3e65",
                arrowprops={"arrowstyle": "->", "color": "#7a3e65", "lw": .65})
    ax.grid(False, axis="x")
    ax = axes[0,1]
    labels = ["Any public site", "Nearest site", "Three nearest"]
    columns = ["any_match", "top1", "top3"]
    y = np.arange(3)[::-1]
    july_row = sce[sce.mapping.eq("JULY_BASELINE_92")].iloc[0]
    production_row = sce[sce.mapping.eq("JULY_UTILITY_CONSTRAINED_92")].iloc[0]
    for yy, name, col in zip(y, labels, columns):
        a, b = 100 * float(july_row[col]), 100 * float(production_row[col])
        ax.plot(a, yy, "o", color="#377eb8", ms=3.6,
                label="Distance-based baseline" if yy == y[0] else None, zorder=3)
        ax.plot(b, yy, "D", color="#ff7f00", ms=3.5,
                label="Utility-compatible mapping" if yy == y[0] else None, zorder=3)
        if yy == y[-1]:
            base_offset, base_va = (0, 7), "bottom"
            revised_offset, revised_va = (0, 19), "bottom"
        else:
            base_offset, base_va = (0, -10), "top"
            revised_offset, revised_va = (0, -22), "top"
        ax.annotate(f"{a:.1f}%", (a, yy), xytext=base_offset, textcoords="offset points",
                    ha="center", va=base_va, fontsize=7.0, color="#28618a")
        ax.annotate(f"{b:.1f}%", (b, yy), xytext=revised_offset, textcoords="offset points",
                    ha="center", va=revised_va, fontsize=7.0, color="#b85a00")
    ax.set_yticks(y, labels)
    ax.set_xlim(85, 100)
    style_axis(ax, title="B. Match to public SCE sites (n=337)",
               xlabel="Comparable tracts matched (%)", ylabel=None)
    ax.grid(False, axis="y")
    fig.legend(handles=[
        Line2D([], [], marker="o", color="none", markerfacecolor="#377eb8",
               markeredgecolor="#377eb8", markersize=3.8, label="Distance-based baseline"),
        Line2D([], [], marker="D", color="none", markerfacecolor="#ff7f00",
               markeredgecolor="#ff7f00", markersize=3.8, label="Utility-compatible mapping"),
    ], frameon=False, loc="upper center", bbox_to_anchor=(.5,.99),
       fontsize=7.0, ncol=2, columnspacing=1.8)

    ax=axes[1,0]
    hazard_order=["Northridge","SanFernando","LongBeach","2pc50"]
    ef=effects.set_index("hazard").loc[hazard_order]
    yy=np.arange(4)[::-1]; vv=ef.mean_delta.to_numpy(float)
    for yv,hz,value in zip(yy,hazard_order,vv):
        ax.hlines(yv,min(0,value),max(0,value),color="#aeb7bd",lw=1.0)
        ax.plot(value,yv,"o",ms=4.1,color="#2878B5" if value<0 else "#A64B3C")
        ax.annotate(f"{value:+.3f} h",(value,yv),xytext=(5,0),
                    textcoords="offset points",ha="left",va="center",fontsize=7.0)
    ax.axvline(0,color="#666666",lw=.65,ls="--")
    ax.set_yticks(yy,hazard_order)
    ax.set_xlim(min(-.08, float(vv.min())-.08), max(.08, float(vv.max())+.15))
    style_axis(ax,title="C. Population-burden change: July to revised mapping",
               xlabel="Revised minus July mapping (h)",ylabel=None)
    ax.grid(False,axis="y")

    ax=axes[1,1]
    sorted_shifts=np.sort(np.abs(shift_values)); ecdf=np.arange(1,len(sorted_shifts)+1)/len(sorted_shifts)
    ax.step(sorted_shifts,ecdf,where="post",color="#2878B5",lw=1.1)
    ax.axvline(1.0,color="#666666",lw=.65,ls="--")
    y1=float(np.searchsorted(sorted_shifts,1.0,side="right")/len(sorted_shifts))
    ax.scatter([1.0],[y1],s=18,facecolors="white",edgecolors="#555555",zorder=3)
    ax.annotate("246 of 2,315 tracts\nshift by >1 h",xy=(1.0,y1),xytext=(.54,.72),
                textcoords="axes fraction",fontsize=7.0,
                arrowprops={"arrowstyle":"-","color":"#555555","lw":.55})
    style_axis(ax,title="D. Tract-level shift magnitude (2pc50)",
               xlabel="Absolute mean burden shift (h)",ylabel="Cumulative share of tracts")
    ax.set_ylim(0,1.02); ax.set_xlim(left=0)
    fig.subplots_adjust(left=.115,right=.985,bottom=.13,top=.85,wspace=.38,hspace=.48)
    save_figure(fig, "FigS06_Mapping_Robustness", tight=False)


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
        "Fig04_Restoration_Strategy_Tradeoffs": ("Main", "How do all eight scheduled strategies compare with the Unconstrained reference?", "Compares population-weighted recovery and realization distributions for cumulative service burden, hospital-linked cumulative burden, and population T80.", "src/la_grid/plotting/build_meeting_figure_collection.py", [FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",FORMAL/"Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet"], "Caption: All eight scheduled strategies and the Unconstrained reference are shown. All scheduled strategies use the same frozen physical realizations; complete values are distributions across 1,000 realizations."),
        "Fig05_Hospital_Priority_and_Critical_Service": ("Main", "How is hospital priority constructed and how does it relate to hospital-linked tract burden?", "Maps hospital-linked tracts and hospital-priority substations with the frozen priority order, then compares four strategies using matched realizations.", "src/la_grid/plotting/build_meeting_figure_collection.py", [ROOT/"Data/JULY_UTILITY_CONSTRAINED_92.csv",ROOT/"Data/hospital_with_tract_expanded.csv",ROOT/"Data/substation_graph_CEC_nodes_expanded.csv",FORMAL/"Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json",FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",FORMAL/"Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet",ROOT/"Data/LA_Tracts_With_Population.shp",ROOT/"Data/LA_Tracts_With_Population.dbf",ROOT/"Data/LA_Tracts_With_Population.shx",ROOT/"Data/LA_Tracts_With_Population.prj"], "Caption: Hospital-first prioritizes substations, not tracts directly. The priority order first counts mapped links to hospital tracts and uses total mapped population only as a tie-break. Number labels identify frozen station priority ranks, not hospital IDs. All strategies use the same damage states, repair durations, and resource realization within each physical realization."),
        "Fig06_Vulnerability_Targeting_and_Distributional_Tradeoffs": ("Main", "What distributional gains and costs accompany Vulnerability-first relative to Hospital-first?", "Combines Q1–Q4 absolute burden, quartile changes, aggregate burden/gap/Gini, and a continuous tract-effect map.", "src/la_grid/plotting/build_meeting_figure_collection.py", [FORMAL/"Equity_Amendment/Figures/FIGURE_B_SOURCE.csv",FORMAL/"Equity_Amendment/VULNERABILITY_PAIRWISE_EFFECTS.csv",FORMAL/"Equity_Amendment/Figures/FIGURE_C_SOURCE.csv",FORMAL/"Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",FORMAL/"Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet",ROOT/"Data/LA_Tracts_With_Population.shp",ROOT/"Data/LA_Tracts_With_Population.dbf",ROOT/"Data/LA_Tracts_With_Population.shx",ROOT/"Data/LA_Tracts_With_Population.prj"], "Caption: Q4 denotes the highest social-vulnerability quartile. For each physical realization, Vulnerability-first and Hospital-first use the same damage states, repair durations, and resource realization before their outcomes are differenced. Gini is population-weighted tract-burden inequality: 0 means equal tract burden; larger values mean more unequal tract burden. The tract map displays the continuous mean change; negative values indicate reduced burden and positive values indicate increased burden."),
        "Fig07_Community_Typology_and_Hotspots": ("Main", "How do the final residential typologies and hotspot scores vary spatially?", "Shows harmonized cluster profiles, the full-domain residential typology map, and the hotspot score map.", "src/la_grid/plotting/build_meeting_figure_collection.py", [STAGE7/"vis_stage7_heatmap.pdf",STAGE7/"stage7_full_domain_tract_status.csv",ROOT/"Data/LA_Tracts_With_Population.shp",ROOT/"Data/LA_Tracts_With_Population.dbf",ROOT/"Data/LA_Tracts_With_Population.shx",ROOT/"Data/LA_Tracts_With_Population.prj"], "Caption: The typology is descriptive and is not a repair strategy. Tracts outside the residential typology eligibility domain are shown as not applicable, not as zero service or ordinary cluster members."),
        "FigS01_Damage_Severity": ("Supplement", "How do initial damage-severity states differ by hazard?", "Frozen four-hazard average damage-state distributions.", "Formal_Experiment_20260923/Stage 1 Output_expanded/vis_stage1_supp_damage_severity_scenarios.pdf", [SUITE/"Stage 1 Output_expanded/vis_stage1_supp_damage_severity_scenarios.pdf"], "Caption: Uses the frozen damage-state summaries; no new damage samples are generated."),
        "FigS02_Initial_Service": ("Supplement", "What service is initially available across hazards and where is it located?", "Combines cross-hazard initial-service distributions and full-domain maps.", "Formal_Experiment_20260923/Stage 1 Output_expanded/vis_stage1_supp_initial_supply_ecdf_scenarios.pdf", [SUITE/"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_ecdf_scenarios.pdf",SUITE/"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_maps_scenarios.pdf"], "Caption: Retains the original cross-hazard ECDF and spatial service panels."),
        "FigS03_Crew_Bases_and_Directed_Travel": ("Supplement", "Where are the frozen C57 crew origins, and how does directed travel vary by destination?", "Shows the active crew origins against all 2,315 study tracts and the retained directed-travel display.", "src/la_grid/plotting/build_meeting_figure_collection.py", [ROOT/"Data/stage45_active_crew_bases_C57.csv",ROOT/"Data/substation_graph_CEC_nodes_expanded.csv",ROOT/"Data/JULY_UTILITY_CONSTRAINED_92.csv",SUITE/"Stage 4 Output_expanded/vis_stage4_logistics_heatmap_full.pdf"], "Caption: The map uses the expanded study footprint, 92 retained stations, and the frozen C57 crew-origin allocation. Travel remains directed; these are logistics inputs, not a factorial experiment."),
        "FigS04_Network_Criticality_and_Percolation": ("Supplement", "How do static attack diagnostics and recovery-network mechanisms relate?", "Retains five static criticality curves, frozen dynamic LCC/average-degree recovery, and source-path burden effects.", "src/la_grid/plotting/build_meeting_figure_collection.py", [SUITE/"Stage 2 Output_expanded/percolation_curve_impact.csv",SUITE/"Stage 2 Output_expanded/percolation_curve_random.csv",SUITE/"Stage 2 Output_expanded/exploratory_percolation_curve_degree.csv",SUITE/"Stage 2 Output_expanded/exploratory_percolation_curve_betweenness_centrality.csv",SUITE/"Stage 2 Output_expanded/exploratory_percolation_curve_closeness_centrality.csv",original("vis_stage6_network_topology_recovery_2pc50.pdf"),SUITE/"Stage 6 Output_expanded/SOURCE_PATH_PAIRED_EFFECT_DISPLAY.csv"], "Caption: Static removal is a network diagnostic, not a repair policy. Source-path intervals show the 5–95% realization range; for each physical realization, the compared policy and Hospital-first use the same damage states, repair durations, and resource realization. Full distinct-strategy evidence is retained; Direct-community is not separately reported."),
        "FigS06_Mapping_Robustness": ("Supplement", "How sensitive are results to the selected mapping cutoff, and how does utility-compatible mapping compare with a distance-based baseline?", "Marks the selected 3% cutoff and directly labels the frozen match percentages for both mapping approaches.", "src/la_grid/plotting/build_meeting_figure_collection.py", [ROOT/"provenance/reviewer_working/Supplement_Rebuild_20260925/Tables/S3_CUTOFF_HOSPITAL_FIRST_2PC50.csv",ROOT/"provenance/reviewer_working/Supplement_Rebuild_20260925/Tables/S3_SCE_337_CANDIDATE_BENCHMARK.csv"], "Caption: The distance-based baseline is the submitted July network-distance IDW mapping. Values are public-site matching percentages over the same 337 comparable tracts. The selected 3% cutoff is marked on the frozen cutoff response."),
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
    plot_supp_fig04()
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
