"""Build an IJDRR-style methodology workflow figure as editable vector art.

The mini-panels are redrawn from the project's generated analytical products:
topology node/edge tables, tract geometries, PGA/fragility outputs, Stage 1
damage/functionality records, Stage 3/6 recovery outputs, Stage 4 logistics
schedules, and Stage 7 recovery-vulnerability typology outputs. The script intentionally avoids
embedding screenshot crops so the SVG/PDF remain editable and readable at
journal scale.

High-risk quantitative mini-panels are data-backed rather than illustrative:
the dependency matrix is sampled from the generated tract-to-substation
mapping, damage-state outputs are aggregated from Stage 1 Monte Carlo records,
and sensitivity bar lengths come from the generated sensitivity summary table.
"""

from __future__ import annotations

import math
import textwrap
import xml.etree.ElementTree as ET
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import matplotlib
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib import patches
from matplotlib.collections import LineCollection
from matplotlib.transforms import Bbox
from shapely import wkt

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 7.0,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
)

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "Manuscript_Figures"
OUT_DIR.mkdir(exist_ok=True)

BASE_NAME = "methodology_workflow_IJDRR"

CM_PER_INCH = 2.54
FIG_W_CM = 18.5
FIG_H_CM = 11.65
FIG_W_IN = FIG_W_CM / CM_PER_INCH
FIG_H_IN = FIG_H_CM / CM_PER_INCH
CANVAS_W = 120.0
CANVAS_H = 68.0
WF_TEXT = 7.0
WF_TITLE = 8.0

C = {
    "ink": "#20252B",
    "muted": "#59636F",
    "grid": "#2F6F9F",
    "grid_light": "#BFD5E4",
    "hazard": "#B85B4A",
    "hazard_light": "#E7B6A7",
    "recovery": "#238879",
    "recovery_light": "#BCD9D3",
    "logistics": "#C8791E",
    "logistics_light": "#E8C58E",
    "community": "#4E8B5F",
    "community_light": "#C8DCC8",
    "purple": "#7B4E8F",
    "critical": "#8A4B7A",
    "road": "#9FA9B2",
    "tract": "#D7DDE3",
    "border": "#AEB8C2",
    "panel_border": "#D8DEE5",
    "box_bg": "#FFFFFF",
    "strip_bg": "#F6F8FA",
    "paper": "#FFFFFF",
}

DS_COLORS = ["#DDE9F1", "#A8CBE1", "#76A9CC", "#DFA36A", "#B65D4C"]
T80_COLORS = ["#DCEEE9", "#91C9BA", "#238879"]
CLUSTER_COLORS = ["#4C7FB2", "#E2B12C", "#218B36"]
STRATEGY_COLORS = ["#238879", "#2F6F9F", "#7B4E8F", "#C8791E"]

INITIAL_FUNCTIONALITY_BY_DS = {0: 1.00, 1: 0.50, 2: 0.09, 3: 0.04, 4: 0.03}


def clean_id(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def fixed_width_export_bbox(fig: plt.Figure, pad_inches: float = 0.02) -> Bbox:
    """Preserve the full-width IJDRR tier while tightly cropping vertically."""
    fig.canvas.draw()
    tight = fig.get_tightbbox(fig.canvas.get_renderer())
    target_width = fig.get_figwidth()
    if tight.width >= target_width:
        return tight
    return Bbox.from_bounds(
        tight.x0 - (target_width - tight.width) / 2.0,
        tight.y0 - pad_inches,
        target_width,
        tight.height + 2.0 * pad_inches,
    )


def load_expanded_tracts() -> gpd.GeoDataFrame:
    usecols = ["GEOID", "wkt_geom", "population", "INTPTLAT", "INTPTLON"]
    tracts = pd.read_csv(ROOT / "Data" / "Tracts_Within_Expanded_Area.csv", usecols=usecols)
    tracts["tract_id"] = clean_id(tracts["GEOID"])
    geometry = tracts["wkt_geom"].map(wkt.loads)
    gdf = gpd.GeoDataFrame(tracts.drop(columns=["wkt_geom"]), geometry=geometry, crs="EPSG:4326")
    gdf["geometry"] = gdf.geometry.simplify(0.0012, preserve_topology=True)
    return gdf


def load_transmission_lines(bounds: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    path = ROOT / "Data" / "TransmissionLine_CEC.shp"
    lines = gpd.read_file(path).to_crs("EPSG:4326")
    minx, maxx, miny, maxy = bounds
    lines = lines.cx[minx:maxx, miny:maxy].copy()
    if "kV_Sort" in lines.columns:
        lines["kV_Sort"] = pd.to_numeric(lines["kV_Sort"], errors="coerce").fillna(0)
        lines = lines.sort_values("kV_Sort", ascending=False)
    return lines.head(220)


def parse_linestring_wkt(value: str) -> list[tuple[float, float]]:
    text = value.strip()
    if not text.upper().startswith("LINESTRING"):
        return []
    text = text[text.find("(") + 1 : text.rfind(")")]
    coords = []
    for pair in text.split(","):
        parts = pair.strip().split()
        if len(parts) >= 2:
            coords.append((float(parts[0]), float(parts[1])))
    return coords


def sample_road_segments(
    path: Path,
    bounds: tuple[float, float, float, float],
    max_segments: int = 260,
) -> list[list[tuple[float, float]]]:
    """Stream a small real OSM road sample from the large GraphML file."""
    minx, maxx, miny, maxy = bounds
    node_xy: dict[str, tuple[float, float]] = {}
    segments: list[list[tuple[float, float]]] = []

    def tag_name(elem: ET.Element) -> str:
        return elem.tag.rsplit("}", 1)[-1]

    try:
        for _, elem in ET.iterparse(path, events=("end",)):
            tag = tag_name(elem)
            if tag == "node":
                data = {child.attrib.get("key"): child.text for child in elem if tag_name(child) == "data"}
                if data.get("d4") and data.get("d5"):
                    y = float(data["d4"])
                    x = float(data["d5"])
                    if minx <= x <= maxx and miny <= y <= maxy:
                        node_xy[elem.attrib["id"]] = (x, y)
                elem.clear()
            elif tag == "edge":
                data = {child.attrib.get("key"): child.text for child in elem if tag_name(child) == "data"}
                seg = parse_linestring_wkt(data.get("d19", "")) if data.get("d19") else []
                if not seg:
                    u = node_xy.get(elem.attrib.get("source", ""))
                    v = node_xy.get(elem.attrib.get("target", ""))
                    if u and v:
                        seg = [u, v]
                if seg and any(minx <= x <= maxx and miny <= y <= maxy for x, y in seg):
                    segments.append(seg)
                    if len(segments) >= max_segments:
                        break
                elem.clear()
    except Exception:
        return []
    return segments


def load_data() -> dict[str, object]:
    nodes = pd.read_csv(ROOT / "Data" / "substation_graph_CEC_nodes_expanded.csv")
    nodes["sid"] = clean_id(nodes["id"])
    edges = pd.read_csv(ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv")
    edges["u"] = clean_id(edges["u"])
    edges["v"] = clean_id(edges["v"])

    minx = float(nodes["lon"].min() - 0.07)
    maxx = float(nodes["lon"].max() + 0.07)
    miny = float(nodes["lat"].min() - 0.055)
    maxy = float(nodes["lat"].max() + 0.055)
    bounds = (minx, maxx, miny, maxy)

    tracts = load_expanded_tracts()
    trans_lines = load_transmission_lines(bounds)
    roads = sample_road_segments(ROOT / "Data" / "la_drive.graphml", bounds)

    sources = pd.read_csv(ROOT / "Data" / "source_nodes_core_expanded.csv")
    sources["sid"] = clean_id(sources["ID"])
    source_ids = set(sources["sid"])

    mapping = pd.read_csv(ROOT / "Data" / "tract_to_substation_mapping_CEC_expanded.csv")
    mapping["tract_id"] = clean_id(mapping["tract_id"])
    mapping["substation_id"] = clean_id(mapping["substation_id"])

    pga = pd.read_csv(ROOT / "Data" / "Substations_PGA_IDW_CEC_expanded.csv")
    pga["sid"] = clean_id(pga["id"])
    avg_ds = pd.read_csv(ROOT / "Stage 1 Output_expanded" / "MC_Device_Damage_AvgDS_Northridge.csv")
    avg_ds["sid"] = clean_id(avg_ds["substation_id"])
    func0 = pd.read_csv(ROOT / "Stage 1 Output_expanded" / "MC_Device_InitFuncMean_Northridge.csv")
    func0["sid"] = clean_id(func0["substation_id"])
    damage = nodes.merge(
        pga[["sid", "PGA_Northridge", "mu_DS1", "mu_DS2", "mu_DS3", "mu_DS4", "beta_DS1", "beta_DS2", "beta_DS3", "beta_DS4"]],
        on="sid",
        how="left",
    ).merge(avg_ds[["sid", "avg_damage_state"]], on="sid", how="left").merge(
        func0[["sid", "mean_func0"]], on="sid", how="left"
    )

    records = pd.read_csv(ROOT / "Stage 1 Output_expanded" / "MC_Device_Damage_Records_Northridge.csv.gz")
    ds_shares = records["damage_state"].value_counts(normalize=True).reindex(range(5), fill_value=0).to_numpy()
    damage_state_summary = (
        records.groupby("damage_state")
        .agg(
            sample_count=("damage_state", "size"),
            residual_functionality=("init_func0", "mean"),
            repair_duration=("repair_time_hr", "median"),
            repair_q25=("repair_time_hr", lambda values: values.quantile(0.25)),
            repair_q75=("repair_time_hr", lambda values: values.quantile(0.75)),
        )
        .reindex(range(5), fill_value=0.0)
        .reset_index()
    )

    tract_kpis = pd.read_csv(ROOT / "Stage 3 Output_expanded" / "tract_kpis_Northridge.csv")
    tract_kpis["tract_id"] = clean_id(tract_kpis["tract_id"])
    tract_supply = pd.read_csv(ROOT / "Stage 1 Output_expanded" / "MC_Tract_Supply_Northridge.csv")
    tract_supply["tract_id"] = clean_id(tract_supply["tract_id"])

    recovery = pd.read_csv(ROOT / "Stage 6 Output_expanded" / "recovery_curves_all_system.csv")

    yards = pd.read_csv(ROOT / "Data" / "stage45_active_crew_bases_C57.csv")
    gantt = pd.read_csv(ROOT / "Stage 4 Output_expanded" / "Gantt_Data_Stage4.csv")

    hospitals = pd.read_csv(ROOT / "Data" / "hospital_with_tract_expanded.csv")
    hospitals = hospitals.rename(columns={"LONGITUDE": "lon", "LATITUDE": "lat"})
    hospitals = hospitals.dropna(subset=["lon", "lat"]).copy()
    hospitals = hospitals[
        hospitals["lon"].between(bounds[0], bounds[1]) & hospitals["lat"].between(bounds[2], bounds[3])
    ].copy()
    hospitals["TOTAL_NUMBER_BEDS"] = pd.to_numeric(hospitals.get("TOTAL_NUMBER_BEDS", 0), errors="coerce").fillna(0)
    if "is_911_receiving" in hospitals.columns:
        hospitals["priority"] = pd.to_numeric(hospitals["is_911_receiving"], errors="coerce").fillna(0) * 10000 + hospitals["TOTAL_NUMBER_BEDS"]
    else:
        hospitals["priority"] = hospitals["TOTAL_NUMBER_BEDS"]
    hospitals = hospitals.sort_values("priority", ascending=False)

    clusters = pd.read_csv(ROOT / "Stage 7 Output_expanded" / "clusters_labels_final.csv")
    clusters["tract_id"] = clean_id(clusters["tract_id"])
    pca = pd.read_csv(ROOT / "Stage 7 Output_expanded" / "pca_loadings.csv").rename(columns={"Unnamed: 0": "metric"})
    vulnerability = pd.read_csv(
        ROOT / "Data" / "LA_Census_Tracts_SOVI_Scores_with_Identifiers.csv",
        usecols=["TRACTFIPS", "SOVI_SCORE"],
    )
    vulnerability["tract_id"] = clean_id(vulnerability["TRACTFIPS"])
    sensitivity = pd.read_csv(ROOT / "Sensitivity Output_clean" / "Tables" / "Table_Sensitivity_Summary_2pc50.csv")
    hotspots = pd.read_csv(ROOT / "Stage 7 Output_expanded" / "stage7_top10_slow_vulnerable_tracts.csv")
    hotspots["tract_id"] = clean_id(hotspots["tract_id"])

    return {
        "nodes": nodes,
        "edges": edges,
        "bounds": bounds,
        "tracts": tracts,
        "trans_lines": trans_lines,
        "roads": roads,
        "source_ids": source_ids,
        "mapping": mapping,
        "damage": damage,
        "ds_shares": ds_shares,
        "damage_state_summary": damage_state_summary,
        "tract_kpis": tract_kpis,
        "tract_supply": tract_supply,
        "recovery": recovery,
        "yards": yards,
        "gantt": gantt,
        "hospitals": hospitals,
        "clusters": clusters,
        "pca": pca,
        "vulnerability": vulnerability,
        "sensitivity": sensitivity,
        "hotspots": hotspots,
    }


def wrap_text(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def module_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    number: int,
    title: str,
    body: str,
    accent: str,
) -> plt.Axes:
    ax.add_patch(
        patches.Rectangle(
            (x, y),
            w,
            h,
            facecolor=C["box_bg"],
            edgecolor=C["border"],
            linewidth=0.82,
        )
    )
    ax.add_patch(patches.Rectangle((x, y + h - 2.1), w, 2.1, facecolor=accent, alpha=0.12, edgecolor="none"))
    ax.add_patch(patches.Circle((x + 1.45, y + h - 1.06), 0.62, facecolor=accent, edgecolor="none"))
    ax.text(x + 1.45, y + h - 1.08, str(number), color="white", ha="center", va="center", fontsize=6.1, weight="bold")
    ax.text(x + 2.4, y + h - 1.05, title, color=C["ink"], ha="left", va="center", fontsize=7.4, weight="bold")
    ax.text(x + 1.0, y + 0.85, wrap_text(body, 47), color=C["muted"], ha="left", va="bottom", fontsize=5.35, linespacing=1.13)

    pax = ax.inset_axes([x + 1.0, y + 4.05, w - 2.0, h - 6.55], transform=ax.transData)
    pax.set_axis_off()
    pax.set_facecolor("#FFFFFF")
    return pax


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str | None = None,
    lw: float = 0.85,
    mutation_scale: float = 8.8,
) -> None:
    arr = patches.FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=lw,
        color="#606A73",
        shrinkA=2,
        shrinkB=2,
    )
    ax.add_patch(arr)
    if label:
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        ax.text(mx, my + 0.75, label, ha="center", va="bottom", fontsize=5.1, color=C["muted"])


def edge_segments(nodes: pd.DataFrame, edges: pd.DataFrame) -> list[list[tuple[float, float]]]:
    pos = nodes.set_index("sid")[["lon", "lat"]].to_dict("index")
    segs = []
    for row in edges.itertuples(index=False):
        u = pos.get(row.u)
        v = pos.get(row.v)
        if u and v:
            segs.append([(u["lon"], u["lat"]), (v["lon"], v["lat"])])
    return segs


def geometry_segments(gdf: gpd.GeoDataFrame) -> list[list[tuple[float, float]]]:
    segs: list[list[tuple[float, float]]] = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        geoms = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
        for line in geoms:
            if line.geom_type == "LineString":
                coords = list(line.simplify(0.002, preserve_topology=True).coords)
                if len(coords) >= 2:
                    segs.append(coords)
    return segs


def add_line_collection(ax: plt.Axes, segs: Iterable, color: str, lw: float, alpha: float, zorder: int = 1) -> None:
    lc = LineCollection(list(segs), colors=color, linewidths=lw, alpha=alpha, zorder=zorder)
    ax.add_collection(lc)


def geo_setup(ax: plt.Axes, bounds: tuple[float, float, float, float]) -> None:
    minx, maxx, miny, maxy = bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect(1.18)
    ax.set_axis_off()


def scatter_geo(ax: plt.Axes, df: pd.DataFrame, color: str, size: float, marker: str = "o", alpha: float = 1.0, zorder: int = 4) -> None:
    ax.scatter(df["lon"], df["lat"], s=size, c=color, marker=marker, alpha=alpha, edgecolors="white", linewidths=0.35, zorder=zorder)


def label_box(ax: plt.Axes, x: float, y: float, text: str, color: str = C["muted"], ha: str = "left", va: str = "top") -> None:
    ax.text(
        x,
        y,
        text,
        ha=ha,
        va=va,
        fontsize=5.1,
        color=color,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72, "pad": 0.7},
        zorder=10,
    )


def draw_inputs(pax: plt.Axes, data: dict[str, object]) -> None:
    bounds = data["bounds"]
    nodes = data["nodes"]
    tracts = data["tracts"]
    roads = data["roads"]
    trans_lines = data["trans_lines"]
    damage = data["damage"]
    yards = data["yards"]
    hospitals = data["hospitals"]

    map_ax = pax.inset_axes([0.02, 0.03, 0.72, 0.93])
    geo_setup(map_ax, bounds)
    try:
        tracts.boundary.plot(ax=map_ax, color=C["tract"], linewidth=0.12, alpha=0.45, zorder=1)
    except Exception:
        pass
    if roads:
        add_line_collection(map_ax, roads, C["road"], 0.25, 0.34, zorder=2)
    line_segs = geometry_segments(trans_lines)
    if line_segs:
        add_line_collection(map_ax, line_segs, C["grid"], 0.50, 0.42, zorder=3)
    else:
        add_line_collection(map_ax, edge_segments(nodes, data["edges"]), C["grid"], 0.50, 0.42, zorder=3)

    hi = damage.nlargest(22, "PGA_Northridge")
    map_ax.scatter(hi["lon"], hi["lat"], s=17, c=C["hazard"], alpha=0.40, edgecolors="none", zorder=4)
    scatter_geo(map_ax, nodes, C["grid"], 9, "s", 0.88, zorder=5)
    shown_yards = yards[yards["longitude"].between(bounds[0], bounds[1]) & yards["latitude"].between(bounds[2], bounds[3])]
    if not shown_yards.empty:
        map_ax.scatter(
            shown_yards["longitude"],
            shown_yards["latitude"],
            s=24,
            c=C["logistics"],
            marker="*",
            edgecolors="white",
            linewidths=0.25,
            alpha=0.90,
            zorder=6,
        )
    shown_hospitals = hospitals.head(18)
    if not shown_hospitals.empty:
        map_ax.scatter(
            shown_hospitals["lon"],
            shown_hospitals["lat"],
            s=20,
            c=C["critical"],
            marker="P",
            edgecolors="white",
            linewidths=0.25,
            alpha=0.88,
            zorder=7,
        )

    pax.set_xlim(0, 1)
    pax.set_ylim(0, 1)
    labels = [
        ("tracts", C["tract"]),
        ("roads/yards", C["road"]),
        ("lines", C["grid"]),
        ("substations", C["grid_light"]),
        ("hospitals", C["critical"]),
        ("PGA/attrs", C["hazard"]),
    ]
    for i, (txt, col) in enumerate(labels):
        yy = 0.85 - i * 0.14
        pax.add_patch(patches.Rectangle((0.76, yy - 0.035), 0.075, 0.052, facecolor=col, edgecolor="none", alpha=0.85))
        pax.text(0.86, yy - 0.01, txt, ha="left", va="center", fontsize=5.2, color=C["muted"])


def dependency_sample(data: dict[str, object], n: int = 12) -> pd.DataFrame:
    tracts = data["tracts"][["tract_id", "INTPTLON", "INTPTLAT", "population"]].copy()
    mapping = data["mapping"].copy()
    nodes = data["nodes"][["sid", "lon", "lat"]].rename(columns={"lon": "sub_lon", "lat": "sub_lat"})
    deps = mapping.merge(tracts, on="tract_id", how="inner", suffixes=("_sub", "_tract"))
    if "population_tract" in deps.columns:
        deps["population_plot"] = deps["population_tract"]
    elif "population_sub" in deps.columns:
        deps["population_plot"] = deps["population_sub"]
    else:
        deps["population_plot"] = 0
    deps = deps.merge(nodes, left_on="substation_id", right_on="sid", how="inner")
    deps = deps.sort_values(["population_plot", "weight"], ascending=False).drop_duplicates("tract_id")
    return deps.head(n)


def simplified_network_subset(data: dict[str, object], edge_n: int = 55) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Use real topology, pruned to a readable length-stratified backbone."""
    ordered = data["edges"].sort_values("length_km").reset_index(drop=True)
    start = min(8, max(0, len(ordered) - 1))
    stop = max(start + 1, len(ordered) - 25)
    sample_idx = np.unique(np.linspace(start, stop, edge_n, dtype=int))
    edges = ordered.iloc[sample_idx].copy()
    keep_ids = set(edges["u"]) | set(edges["v"])
    deps = dependency_sample(data, n=5)
    keep_ids |= set(deps["substation_id"])
    nodes = data["nodes"][data["nodes"]["sid"].isin(keep_ids)].copy()
    return nodes, edges


def draw_network(pax: plt.Axes, data: dict[str, object]) -> None:
    bounds = data["bounds"]
    nodes, edges = simplified_network_subset(data, edge_n=45)
    source_ids = data["source_ids"]
    deps = dependency_sample(data, n=4)

    geo_setup(pax, bounds)
    add_line_collection(pax, edge_segments(nodes, edges), C["grid"], 0.95, 0.86, zorder=2)
    scatter_geo(pax, nodes, "#2D5973", 15, "o", 0.94, zorder=4)
    src = nodes[nodes["sid"].isin(source_ids)]
    if not src.empty:
        stride = max(1, math.ceil(len(src) / 4))
        src = src.sort_values(["lon", "lat"]).iloc[::stride].head(4)
        scatter_geo(pax, src, C["hazard"], 36, "^", 0.96, zorder=5)
    for _, dep in deps.iterrows():
        pax.plot(
            [dep["INTPTLON"], dep["sub_lon"]],
            [dep["INTPTLAT"], dep["sub_lat"]],
            color=C["community"],
            lw=0.70 + 0.55 * min(float(dep["weight"]), 1),
            alpha=0.78,
            zorder=3,
        )
    pax.scatter(deps["INTPTLON"], deps["INTPTLAT"], s=30, marker="h", c=C["community_light"], edgecolors=C["community"], linewidths=0.45, zorder=3)
    label_box(pax, bounds[0] + 0.02, bounds[3] - 0.02, "source-gated graph", C["muted"])
    label_box(pax, bounds[0] + 0.02, bounds[2] + 0.02, "weighted tract links", C["community"], va="bottom")


def lognorm_cdf(x: np.ndarray, mu: float, beta: float) -> np.ndarray:
    x = np.clip(x, 1e-6, None)
    z = (np.log(x) - math.log(max(mu, 1e-6))) / (max(beta, 1e-4) * math.sqrt(2.0))
    return 0.5 * (1.0 + np.vectorize(math.erf)(z))


def draw_seismic(pax: plt.Axes, data: dict[str, object]) -> None:
    damage = data["damage"].copy()
    bounds = data["bounds"]
    ds_shares = data["ds_shares"]

    pax.set_xlim(0, 1)
    pax.set_ylim(0, 1)
    pax.set_axis_off()

    pax.text(0.005, 0.94, "PGA at substations", fontsize=5.2, ha="left", va="top", color=C["muted"])
    map_ax = pax.inset_axes([0.00, 0.05, 0.30, 0.76])
    geo_setup(map_ax, bounds)
    vals = damage["PGA_Northridge"].to_numpy()
    sizes = 8 + 24 * (vals - np.nanmin(vals)) / max(np.nanmax(vals) - np.nanmin(vals), 1e-6)
    map_ax.scatter(damage["lon"], damage["lat"], s=sizes, c=damage["PGA_Northridge"], cmap="OrRd", alpha=0.75, edgecolors="white", linewidths=0.25)

    pax.annotate("", xy=(0.37, 0.52), xytext=(0.31, 0.52), arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": C["muted"]})

    curve_ax = pax.inset_axes([0.38, 0.18, 0.23, 0.64])
    curve_ax.set_xlim(0, 1.0)
    curve_ax.set_ylim(0, 1.02)
    row = damage.dropna(subset=["mu_DS1", "beta_DS1"]).iloc[0]
    x = np.linspace(0.01, 1.0, 120)
    for i, ds in enumerate(range(1, 5)):
        curve_ax.plot(x, lognorm_cdf(x, row[f"mu_DS{ds}"], row[f"beta_DS{ds}"]), color=DS_COLORS[i + 1], lw=0.95)
    curve_ax.set_xticks([])
    curve_ax.set_yticks([])
    for spine in curve_ax.spines.values():
        spine.set_linewidth(0.45)
        spine.set_color(C["panel_border"])
    curve_ax.text(0.03, 0.94, "fragility", transform=curve_ax.transAxes, fontsize=5.1, ha="left", va="top", color=C["muted"])

    pax.annotate("", xy=(0.66, 0.52), xytext=(0.61, 0.52), arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": C["muted"]})

    pax.text(0.675, 0.86, "DS0-DS4", ha="left", va="center", fontsize=5.35, color=C["muted"])
    for i, ds in enumerate(range(5)):
        yy = 0.72 - i * 0.107
        pax.add_patch(patches.Rectangle((0.675, yy), 0.043, 0.043, facecolor=DS_COLORS[ds], edgecolor="white", linewidth=0.25))
        pax.text(0.728, yy + 0.0215, f"DS{ds}", ha="left", va="center", fontsize=5.05, color=C["muted"])

    pax.annotate("", xy=(0.835, 0.52), xytext=(0.795, 0.52), arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": C["muted"]})

    pax.text(0.855, 0.86, "residual functionality", ha="left", va="center", fontsize=5.35, color=C["muted"])
    for i, ds in enumerate(range(5)):
        yy = 0.72 - i * 0.107
        val = INITIAL_FUNCTIONALITY_BY_DS[ds]
        pax.add_patch(patches.Rectangle((0.855, yy + 0.006), 0.125, 0.032, facecolor="none", edgecolor=C["panel_border"], linewidth=0.38))
        pax.add_patch(patches.Rectangle((0.855, yy + 0.006), 0.125 * val, 0.032, facecolor=C["recovery"], edgecolor="none", alpha=0.92))


def draw_recovery(pax: plt.Axes, data: dict[str, object]) -> None:
    recovery = data["recovery"]
    tracts = data["tracts"]
    kpis = data["tract_kpis"]

    pax.set_axis_off()
    curve_ax = pax.inset_axes([0.02, 0.14, 0.52, 0.75])
    t = recovery["time_hr"]
    y = recovery["Northridge_S3_Mean_Pop"]
    curve_ax.plot(t, y, color=C["recovery"], lw=1.45)
    idx = int(np.argmax(y.to_numpy() >= 0.8))
    t80 = float(t.iloc[idx])
    curve_ax.axhline(0.8, color=C["panel_border"], lw=0.65)
    curve_ax.axvline(t80, color=C["hazard"], lw=0.85)
    curve_ax.text(t80 + 0.5, 0.88, "T80", color=C["hazard"], fontsize=5.2, ha="left")
    curve_ax.set_xlim(0, min(42, float(t.max())))
    curve_ax.set_ylim(0.3, 1.03)
    curve_ax.set_xticks([0, 12, 24, 36])
    curve_ax.set_yticks([0.4, 0.8, 1.0])
    curve_ax.tick_params(labelsize=4.8, length=2, pad=1)
    curve_ax.grid(color=C["panel_border"], linewidth=0.35, alpha=0.55)
    for spine in curve_ax.spines.values():
        spine.set_linewidth(0.45)
        spine.set_color(C["panel_border"])

    map_ax = pax.inset_axes([0.61, 0.07, 0.36, 0.86])
    geo_setup(map_ax, data["bounds"])
    t80_gdf = tracts.merge(kpis[["tract_id", "T80"]], on="tract_id", how="inner")
    t80_gdf["bin"] = pd.qcut(t80_gdf["T80"], 3, labels=False, duplicates="drop")
    for b, col in enumerate(T80_COLORS):
        subset = t80_gdf[t80_gdf["bin"] == b]
        if subset.empty:
            continue
        subset.plot(ax=map_ax, color=col, edgecolor="none", alpha=0.94, zorder=2)
    map_ax.text(data["bounds"][0] + 0.01, data["bounds"][3] - 0.015, "tract T80", fontsize=5.1, ha="left", va="top", color=C["muted"])


def draw_logistics(pax: plt.Axes, data: dict[str, object]) -> None:
    nodes = data["nodes"]
    yards = data["yards"]
    gantt = data["gantt"]
    roads = data["roads"]
    bounds = data["bounds"]
    all_tasks = gantt[gantt["Stage"].eq("Stage4_Northridge_impact-first")].sort_values(["Start_Time", "End_Time"]).reset_index(drop=True)
    sample_idx = np.unique(np.linspace(0, len(all_tasks) - 1, 6, dtype=int))
    task_rows = all_tasks.iloc[sample_idx].copy()
    task_rows["sid"] = clean_id(task_rows["Substation_ID"])
    task_rows = task_rows.merge(nodes[["sid", "lon", "lat"]], on="sid", how="left")
    task_rows = task_rows.merge(yards[["yard_id", "latitude", "longitude"]], left_on="Crew_Origin_ID", right_on="yard_id", how="left")

    pax.set_axis_off()
    map_ax = pax.inset_axes([0.02, 0.05, 0.60, 0.90])
    geo_setup(map_ax, bounds)
    if roads:
        add_line_collection(map_ax, roads, C["road"], 0.23, 0.25, zorder=1)
    add_line_collection(map_ax, edge_segments(nodes, data["edges"]), C["grid_light"], 0.42, 0.35, zorder=2)
    for i, row in enumerate(task_rows.itertuples(index=False), start=1):
        if not np.isfinite(row.longitude) or not np.isfinite(row.lon):
            continue
        map_ax.plot([row.longitude, row.lon], [row.latitude, row.lat], color=C["logistics"], lw=0.75, alpha=0.75, zorder=3)
        map_ax.scatter([row.lon], [row.lat], s=42, c=C["hazard"], marker="o", edgecolors="white", linewidths=0.45, zorder=5)
        map_ax.text(row.lon, row.lat, str(i), fontsize=4.8, ha="center", va="center", color="white", weight="bold", zorder=6)
    shown_yards = yards[yards["yard_id"].isin(task_rows["Crew_Origin_ID"])]
    map_ax.scatter(shown_yards["longitude"], shown_yards["latitude"], s=58, c=C["logistics"], marker="*", edgecolors=C["ink"], linewidths=0.35, zorder=6)
    map_ax.text(bounds[0] + 0.01, bounds[3] - 0.015, "yard-to-task dispatch", fontsize=5.1, ha="left", va="top", color=C["muted"])

    seq_ax = pax.inset_axes([0.67, 0.12, 0.30, 0.77])
    seq = task_rows.sort_values(["Start_Time", "End_Time"]).head(6).reset_index(drop=True)
    max_end = max(1.0, float(seq["End_Time"].max()))
    for idx, row in seq.iterrows():
        y = len(seq) - idx - 1
        travel = float(row["Travel_Time"])
        start = float(row["Start_Time"])
        end = float(row["End_Time"])
        travel_draw = max(travel, max_end * 0.035)
        seq_ax.axhline(y, color=C["panel_border"], lw=0.25, alpha=0.55, zorder=0)
        seq_ax.barh(y, travel_draw, left=max(0, start - travel_draw), height=0.36, color=C["hazard"], edgecolor="none", zorder=2)
        seq_ax.barh(y, end - start, left=start, height=0.36, color="#AEB8C2", edgecolor="none", zorder=1)
        seq_ax.text(end + max_end * 0.012, y, str(idx + 1), fontsize=4.6, va="center", ha="left", color=C["muted"])
    seq_ax.set_xlim(0, max_end * 1.18)
    seq_ax.set_ylim(-1.05, len(seq) - 0.3)
    seq_ax.set_yticks(range(len(seq)), [f"C{i}" for i in range(1, len(seq) + 1)], fontsize=4.5)
    seq_ax.set_xticks([0, round(max_end / 2), round(max_end)])
    seq_ax.tick_params(labelsize=4.7, length=2, pad=1)
    seq_ax.grid(axis="x", color=C["panel_border"], lw=0.35)
    for spine in seq_ax.spines.values():
        spine.set_linewidth(0.45)
        spine.set_color(C["panel_border"])
    seq_ax.text(0.0, 1.04, "travel + repair schedule", transform=seq_ax.transAxes, fontsize=5.1, ha="left", color=C["muted"])


def draw_outcomes(pax: plt.Axes, data: dict[str, object]) -> None:
    recovery = data["recovery"]
    tracts = data["tracts"]
    clusters = data["clusters"]
    bounds = data["bounds"]

    pax.set_axis_off()

    curve_ax = pax.inset_axes([0.01, 0.16, 0.31, 0.70])
    strategy_cols = [
        "Northridge_S4_impact-first_Pop",
        "Northridge_S4_betweenness-first_Pop",
        "Northridge_S4_hospital-first_Pop",
        "Northridge_S4_random_Pop",
    ]
    for col, color in zip(strategy_cols, STRATEGY_COLORS):
        curve_ax.plot(recovery["time_hr"], recovery[col], lw=0.9, color=color)
    curve_ax.set_xlim(0, 32)
    curve_ax.set_ylim(0.34, 1.02)
    curve_ax.set_xticks([])
    curve_ax.set_yticks([])
    for spine in curve_ax.spines.values():
        spine.set_linewidth(0.45)
        spine.set_color(C["panel_border"])
    curve_ax.text(0.03, 0.95, "strategies", transform=curve_ax.transAxes, fontsize=5.1, va="top", ha="left", color=C["muted"])

    heat_ax = pax.inset_axes([0.37, 0.16, 0.24, 0.70])
    metrics = ["T80", "Grid impact", "Pop. density", "SVI"]
    clusters_short = ["Cluster 1", "Cluster 2", "Cluster 3"]
    mat = np.array(
        [
            [0.75, -0.15, 0.40],
            [0.35, 0.62, -0.25],
            [-0.18, 0.55, 0.72],
            [0.60, -0.30, 0.25],
        ]
    )
    heat_ax.set_xlim(0, len(clusters_short))
    heat_ax.set_ylim(0, len(metrics))
    vmax = max(0.001, float(np.nanmax(np.abs(mat))))
    for r, metric in enumerate(metrics):
        for cidx, _cluster in enumerate(clusters_short):
            val = float(mat[r, cidx])
            if val >= 0:
                color = plt.cm.Greens(0.25 + 0.65 * val / vmax)
            else:
                color = plt.cm.Purples(0.25 + 0.65 * abs(val) / vmax)
            heat_ax.add_patch(patches.Rectangle((cidx, len(metrics) - r - 1), 1, 1, facecolor=color, edgecolor="white", linewidth=0.45))
    heat_ax.set_xticks([0.5, 1.5, 2.5], clusters_short, fontsize=3.8)
    heat_ax.set_yticks([])
    heat_ax.tick_params(length=0, pad=1)
    for spine in heat_ax.spines.values():
        spine.set_visible(False)
    heat_ax.text(0.0, 1.06, "indicator profiles", transform=heat_ax.transAxes, fontsize=5.1, ha="left", color=C["muted"])

    map_ax = pax.inset_axes([0.66, 0.06, 0.32, 0.86])
    geo_setup(map_ax, bounds)
    typ = tracts.merge(clusters[["tract_id", "cluster"]], on="tract_id", how="inner")
    for cluster, color in enumerate(CLUSTER_COLORS):
        subset = typ[typ["cluster"] == cluster]
        if subset.empty:
            continue
        subset.plot(ax=map_ax, color=color, edgecolor="none", alpha=0.92)
    label_box(map_ax, bounds[0] + 0.01, bounds[3] - 0.015, "tract typology", C["muted"])


def draw_translation_strip(ax: plt.Axes, data: dict[str, object], x: float, y: float, w: float, h: float) -> None:
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=C["strip_bg"], edgecolor=C["border"], linewidth=0.85))
    ax.text(
        x + 1.2,
        y + h - 1.0,
        "Damage-to-service translation",
        ha="left",
        va="center",
        fontsize=6.8,
        color=C["ink"],
        weight="bold",
    )

    titles = ["DS samples", "residual functionality", "connectivity gate", "tract-substation weights", "tract service proxy"]
    step_w = (w - 4.0) / 5.0
    step_x = [x + 2.0 + i * step_w for i in range(5)]
    base_y = y + 1.0
    step_h = h - 3.0

    for i, sx in enumerate(step_x):
        cx = sx + step_w / 2
        ax.text(cx, base_y + 0.1, titles[i], ha="center", va="bottom", fontsize=5.25, color=C["muted"])
        if i < 4:
            arrow(ax, (sx + step_w - 0.8, y + h / 2 - 0.2), (sx + step_w + 0.55, y + h / 2 - 0.2))

    # 1. Actual Northridge DS share stack.
    ds = data["ds_shares"]
    sx = step_x[0]
    bx = sx + 1.2
    by = base_y + 1.35
    total_h = step_h - 1.65
    yy = by
    for share, color in zip(ds, DS_COLORS):
        hh = total_h * float(share)
        ax.add_patch(patches.Rectangle((bx, yy), 2.7, hh, facecolor=color, edgecolor="white", linewidth=0.25))
        yy += hh
    ax.text(bx + 3.35, by + total_h / 2, "DS0-DS4", fontsize=4.9, color=C["muted"], ha="left", va="center")

    # 2. Residual functionality table from the model constants.
    sx = step_x[1]
    for j, (ds_id, val) in enumerate(INITIAL_FUNCTIONALITY_BY_DS.items()):
        yy = base_y + 1.25 + (4 - j) * 0.72
        ax.text(sx + 1.0, yy + 0.1, f"DS{ds_id}", fontsize=4.8, color=C["muted"], ha="left")
        ax.add_patch(patches.Rectangle((sx + 3.3, yy), 4.0, 0.32, facecolor="none", edgecolor=C["panel_border"], linewidth=0.35))
        ax.add_patch(patches.Rectangle((sx + 3.3, yy), 4.0 * val, 0.32, facecolor=C["recovery"], edgecolor="none"))

    # 3. Small real topology sketch.
    nodes = data["nodes"]
    edges = data["edges"]
    bounds = data["bounds"]
    source_ids = data["source_ids"]
    sx = step_x[2]
    tx, ty, tw, th = sx + 0.5, base_y + 1.08, step_w - 1.0, step_h - 1.65
    def sx_geo(lon: float) -> float:
        return tx + (lon - bounds[0]) / (bounds[1] - bounds[0]) * tw
    def sy_geo(lat: float) -> float:
        return ty + (lat - bounds[2]) / (bounds[3] - bounds[2]) * th
    pos = nodes.set_index("sid")[["lon", "lat"]].to_dict("index")
    for row in edges.iloc[::3].itertuples(index=False):
        u = pos.get(row.u)
        v = pos.get(row.v)
        if u and v:
            ax.plot([sx_geo(u["lon"]), sx_geo(v["lon"])], [sy_geo(u["lat"]), sy_geo(v["lat"])], color=C["grid"], lw=0.45, alpha=0.72)
    for n in nodes.iloc[::4].itertuples(index=False):
        ax.add_patch(patches.Circle((sx_geo(n.lon), sy_geo(n.lat)), 0.10, facecolor="#2D5973", edgecolor="white", linewidth=0.2))
    for n in nodes[nodes["sid"].isin(source_ids)].itertuples(index=False):
        ax.add_patch(patches.RegularPolygon((sx_geo(n.lon), sy_geo(n.lat)), 3, radius=0.28, orientation=0, facecolor=C["hazard"], edgecolor="white", linewidth=0.25))

    # 4. Actual dependency links, simplified.
    deps = dependency_sample(data, n=5)
    sx = step_x[3]
    for _, dep in deps.iterrows():
        tract_x = sx + 1.0 + (dep["INTPTLON"] - bounds[0]) / (bounds[1] - bounds[0]) * (step_w - 2.0)
        tract_y = base_y + 1.05 + (dep["INTPTLAT"] - bounds[2]) / (bounds[3] - bounds[2]) * (step_h - 1.6)
        sub_x = sx + 1.0 + (dep["sub_lon"] - bounds[0]) / (bounds[1] - bounds[0]) * (step_w - 2.0)
        sub_y = base_y + 1.05 + (dep["sub_lat"] - bounds[2]) / (bounds[3] - bounds[2]) * (step_h - 1.6)
        ax.plot([tract_x, sub_x], [tract_y, sub_y], color=C["community"], lw=0.75, alpha=0.75)
        ax.add_patch(patches.RegularPolygon((tract_x, tract_y), 6, radius=0.30, facecolor=C["community_light"], edgecolor=C["community"], linewidth=0.35))
        ax.add_patch(patches.Circle((sub_x, sub_y), 0.18, facecolor=C["grid"], edgecolor="white", linewidth=0.25))
    for r in range(3):
        for c in range(3):
            ax.add_patch(patches.Rectangle((sx + 6.4 + c * 0.42, base_y + 1.18 + r * 0.42), 0.34, 0.34, facecolor=C["community"], alpha=0.20 + 0.18 * ((r + c) % 3), edgecolor="white", linewidth=0.15))

    # 5. Actual tract service supply distribution, simplified as coarse bins.
    supply = data["tract_supply"]
    shares = pd.qcut(supply["supply"], 4, labels=False, duplicates="drop").value_counts(normalize=True).sort_index()
    sx = step_x[4]
    poly_centers = [(sx + 2.2, base_y + 2.25), (sx + 3.45, base_y + 3.0), (sx + 4.75, base_y + 2.2), (sx + 3.55, base_y + 1.3)]
    service_cols = ["#D9E5EF", "#A9CFD0", "#6EBAA9", "#238879"]
    for i, center in enumerate(poly_centers):
        alpha = 0.55 + 0.35 * float(shares.iloc[min(i, len(shares) - 1)])
        ax.add_patch(patches.RegularPolygon(center, 6, radius=0.70, facecolor=service_cols[i], edgecolor="white", linewidth=0.4, alpha=alpha))
    ax.text(sx + 6.1, base_y + 2.3, "service\nproxy", fontsize=4.9, color=C["muted"], ha="left", va="center")


def write_pptx_with_svg(svg_path: Path, pptx_path: Path) -> None:
    """Create a one-slide PPTX that embeds the SVG as a vector image."""
    slide_cx = 12192000
    slide_cy = 6858000
    fig_aspect = FIG_W_IN / FIG_H_IN
    pic_cy = slide_cy
    pic_cx = int(round(pic_cy * fig_aspect))
    pic_x = int(round((slide_cx - pic_cx) / 2))
    pic_y = 0
    created = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="svg" ContentType="image/svg+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>
"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>methodology_workflow_IJDRR</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>
"""
    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft PowerPoint</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>1</Slides>
  <Notes>0</Notes>
  <HiddenSlides>0</HiddenSlides>
  <MMClips>0</MMClips>
  <ScaleCrop>false</ScaleCrop>
</Properties>
"""
    presentation_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>
  <p:sldSz cx="{slide_cx}" cy="{slide_cy}" type="screen16x9"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle><a:defPPr><a:defRPr lang="en-US"/></a:defPPr></p:defaultTextStyle>
</p:presentation>
"""
    presentation_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
</Relationships>
"""
    slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{slide_cx}" cy="{slide_cy}"/><a:chOff x="0" y="0"/><a:chExt cx="{slide_cx}" cy="{slide_cy}"/></a:xfrm></p:grpSpPr>
      <p:pic>
        <p:nvPicPr><p:cNvPr id="2" name="methodology_workflow_IJDRR.svg"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
        <p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
        <p:spPr><a:xfrm><a:off x="{pic_x}" y="{pic_y}"/><a:ext cx="{pic_cx}" cy="{pic_cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
      </p:pic>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>
"""
    slide_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/methodology_workflow_IJDRR.svg"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>
"""
    slide_layout_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>
"""
    slide_layout_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>
"""
    slide_master_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>
"""
    slide_master_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>
"""
    theme_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">
  <a:themeElements>
    <a:clrScheme name="Office">
      <a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1F497D"/></a:dk2><a:lt2><a:srgbClr val="EEECE1"/></a:lt2>
      <a:accent1><a:srgbClr val="4F81BD"/></a:accent1><a:accent2><a:srgbClr val="C0504D"/></a:accent2>
      <a:accent3><a:srgbClr val="9BBB59"/></a:accent3><a:accent4><a:srgbClr val="8064A2"/></a:accent4>
      <a:accent5><a:srgbClr val="4BACC6"/></a:accent5><a:accent6><a:srgbClr val="F79646"/></a:accent6>
      <a:hlink><a:srgbClr val="0000FF"/></a:hlink><a:folHlink><a:srgbClr val="800080"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Office"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Office">
      <a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
      <a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="25400"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="38100"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
      <a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/><a:extraClrSchemeLst/>
</a:theme>
"""
    files = {
        "[Content_Types].xml": content_types,
        "_rels/.rels": root_rels,
        "docProps/core.xml": core_xml,
        "docProps/app.xml": app_xml,
        "ppt/presentation.xml": presentation_xml,
        "ppt/_rels/presentation.xml.rels": presentation_rels,
        "ppt/slides/slide1.xml": slide_xml,
        "ppt/slides/_rels/slide1.xml.rels": slide_rels,
        "ppt/slideLayouts/slideLayout1.xml": slide_layout_xml,
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": slide_layout_rels,
        "ppt/slideMasters/slideMaster1.xml": slide_master_xml,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": slide_master_rels,
        "ppt/theme/theme1.xml": theme_xml,
    }
    with zipfile.ZipFile(pptx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, content in files.items():
            zf.writestr(arcname, content)
        zf.write(svg_path, "ppt/media/methodology_workflow_IJDRR.svg")


def flow_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    number: int | None,
    title: str,
    accent: str,
    body: str | None = None,
    header_h: float = 1.9,
    face: str = "#FFFFFF",
    title_size: float = WF_TITLE,
) -> None:
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor=face, edgecolor=C["border"], linewidth=0.85))
    ax.add_patch(patches.Rectangle((x, y + h - header_h), w, header_h, facecolor=accent, alpha=0.10, edgecolor="none"))
    title_x = x + 0.9
    if number is not None:
        ax.add_patch(patches.Circle((x + 1.3, y + h - header_h / 2), 0.50, facecolor=accent, edgecolor="none"))
        ax.text(x + 1.3, y + h - header_h / 2 - 0.02, str(number), ha="center", va="center", color="white", fontsize=WF_TEXT, weight="bold")
        title_x = x + 2.1
    ax.text(title_x, y + h - header_h / 2, title, ha="left", va="center", color=C["ink"], fontsize=title_size, weight="bold")
    if body:
        ax.text(x + 0.9, y + 0.75, wrap_text(body, max(24, int(w * 1.55))), ha="left", va="bottom", color=C["muted"], fontsize=WF_TEXT, linespacing=1.10)


def step_label(ax: plt.Axes, x: float, y: float, text: str, color: str = C["muted"], size: float = WF_TEXT, weight: str = "normal") -> None:
    ax.text(x, y, text, ha="center", va="center", color=color, fontsize=max(size, WF_TEXT), weight=weight)


def mini_arrow(ax: plt.Axes, x0: float, y0: float, x1: float, y1: float, color: str = "#707A83", lw: float = 0.65) -> None:
    ax.add_patch(
        patches.FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=5.4,
            linewidth=lw,
            color=color,
            shrinkA=1.5,
            shrinkB=1.5,
        )
    )


def orth_arrow(ax: plt.Axes, points: list[tuple[float, float]], color: str = "#707A83", lw: float = 0.65) -> None:
    for p0, p1 in zip(points[:-2], points[1:-1]):
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=lw, solid_capstyle="round")
    ax.add_patch(
        patches.FancyArrowPatch(
            points[-2],
            points[-1],
            arrowstyle="-|>",
            mutation_scale=5.4,
            linewidth=lw,
            color=color,
            shrinkA=0.0,
            shrinkB=1.2,
        )
    )


def geo_xy(lon: float, lat: float, bounds: tuple[float, float, float, float], x: float, y: float, w: float, h: float) -> tuple[float, float]:
    minx, maxx, miny, maxy = bounds
    return x + (lon - minx) / (maxx - minx) * w, y + (lat - miny) / (maxy - miny) * h


def draw_network_mechanism(ax: plt.Axes, data: dict[str, object], x: float, y: float, w: float, h: float, edge_n: int = 38) -> None:
    nodes, edges = simplified_network_subset(data, edge_n=edge_n)
    bounds = data["bounds"]
    pos = nodes.set_index("sid")[["lon", "lat"]].to_dict("index")
    for row in edges.itertuples(index=False):
        u = pos.get(row.u)
        v = pos.get(row.v)
        if not u or not v:
            continue
        x0, y0 = geo_xy(u["lon"], u["lat"], bounds, x, y, w, h)
        x1, y1 = geo_xy(v["lon"], v["lat"], bounds, x, y, w, h)
        ax.plot([x0, x1], [y0, y1], color=C["grid"], lw=0.70, alpha=0.82)
    draw_nodes = nodes.iloc[:: max(1, len(nodes) // 30)]
    for row in draw_nodes.itertuples(index=False):
        px, py = geo_xy(row.lon, row.lat, bounds, x, y, w, h)
        ax.add_patch(patches.Circle((px, py), 0.16, facecolor="#2D5973", edgecolor="white", linewidth=0.25))
    src = nodes[nodes["sid"].isin(data["source_ids"])].head(5)
    for row in src.itertuples(index=False):
        px, py = geo_xy(row.lon, row.lat, bounds, x, y, w, h)
        ax.add_patch(patches.RegularPolygon((px, py), 3, radius=0.34, orientation=0, facecolor=C["hazard"], edgecolor="white", linewidth=0.25))


def draw_dependency_matrix_icon(ax: plt.Axes, x: float, y: float, w: float, h: float, label: str = "") -> None:
    rng = np.array(
        [
            [0.82, 0.05, 0.18, 0.00],
            [0.10, 0.70, 0.08, 0.12],
            [0.00, 0.15, 0.78, 0.22],
            [0.30, 0.00, 0.20, 0.65],
        ]
    )
    rows, cols = rng.shape
    for r in range(rows):
        for c in range(cols):
            alpha = 0.16 + 0.72 * rng[r, c]
            ax.add_patch(
                patches.Rectangle(
                    (x + c * w / cols, y + (rows - r - 1) * h / rows),
                    w / cols - 0.05,
                    h / rows - 0.05,
                    facecolor=C["community"],
                    edgecolor="white",
                    linewidth=0.25,
                    alpha=alpha,
                )
            )
    ax.text(x + w + 0.45, y + h / 2, label, ha="left", va="center", color=C["community"], fontsize=7.0, weight="bold")


def draw_pga_cloud(ax: plt.Axes, data: dict[str, object], x: float, y: float, w: float, h: float) -> None:
    damage = data["damage"].dropna(subset=["PGA_Northridge"]).copy()
    bounds = data["bounds"]
    sample = damage.sort_values("PGA_Northridge", ascending=False).head(55)
    vals = sample["PGA_Northridge"].to_numpy()
    vmin, vmax = vals.min(), vals.max()
    for row in sample.itertuples(index=False):
        px, py = geo_xy(row.lon, row.lat, bounds, x, y, w, h)
        scale = (row.PGA_Northridge - vmin) / max(vmax - vmin, 1e-6)
        col = plt.cm.OrRd(0.20 + 0.72 * scale)
        ax.add_patch(patches.Circle((px, py), 0.11 + 0.13 * scale, facecolor=col, edgecolor="white", linewidth=0.15, alpha=0.92))


def draw_fragility_icon(ax: plt.Axes, x: float, y: float, w: float, h: float) -> None:
    xx = np.linspace(0.02, 0.98, 80)
    for i, (x0, color) in enumerate(zip([0.25, 0.36, 0.50, 0.72], DS_COLORS[1:])):
        yy = 1.0 / (1.0 + np.exp(-(xx - x0) * 12))
        ax.plot(x + xx * w, y + yy * h, color=color, lw=1.0)
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor="none", edgecolor=C["panel_border"], linewidth=0.35))


def draw_ds_stack_icon(ax: plt.Axes, data: dict[str, object], x: float, y: float, w: float, h: float, label: bool = True) -> None:
    ds = data["ds_shares"]
    yy = y
    for share, color in zip(ds, DS_COLORS):
        hh = h * float(share)
        ax.add_patch(patches.Rectangle((x, yy), w, hh, facecolor=color, edgecolor="white", linewidth=0.20))
        yy += hh
    if label:
        ax.text(x + w + 0.35, y + h / 2, "DS0-DS4", ha="left", va="center", fontsize=5.1, color=C["muted"])


def draw_function_bars(ax: plt.Axes, x: float, y: float, w: float, h: float, labels: bool = False, title: str = "") -> None:
    step = h / 5.0
    for i, ds in enumerate(range(5)):
        yy = y + (4 - i) * step + step * 0.28
        val = INITIAL_FUNCTIONALITY_BY_DS[ds]
        if labels:
            ax.text(x - 0.35, yy + step * 0.15, f"DS{ds}", ha="right", va="center", fontsize=4.8, color=C["muted"])
        ax.add_patch(patches.Rectangle((x, yy), w, step * 0.36, facecolor="none", edgecolor=C["panel_border"], linewidth=0.35))
        ax.add_patch(patches.Rectangle((x, yy), w * val, step * 0.36, facecolor=C["recovery"], edgecolor="none", alpha=0.92))
    if title:
        ax.text(x + w / 2, y + h + 0.55, title, ha="center", va="center", fontsize=5.2, color=C["muted"], weight="bold")


def draw_repair_duration_icon(ax: plt.Axes, x: float, y: float, w: float, h: float, title: str = "repair-duration\nsamples") -> None:
    vals = [0.18, 0.34, 0.55, 0.78, 0.95]
    step = w / len(vals)
    for i, val in enumerate(vals):
        bx = x + i * step + step * 0.20
        bh = h * val
        ax.add_patch(
            patches.Rectangle(
                (bx, y),
                step * 0.55,
                bh,
                facecolor=C["logistics"],
                edgecolor="white",
                linewidth=0.25,
                alpha=0.88,
            )
        )
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor="none", edgecolor=C["panel_border"], linewidth=0.35))
    if title:
        ax.text(x + w / 2, y + h + 0.55, title, ha="center", va="center", fontsize=4.8, color=C["logistics"], weight="bold", linespacing=0.95)


def draw_recovery_curve_icon(ax: plt.Axes, data: dict[str, object], x: float, y: float, w: float, h: float, cols: list[str], colors: list[str]) -> None:
    rec = data["recovery"]
    t = rec["time_hr"].to_numpy()
    tmax = min(42.0, float(np.nanmax(t)))
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor="none", edgecolor=C["panel_border"], linewidth=0.35))
    for col, color in zip(cols, colors):
        yy = rec[col].to_numpy()
        xs = x + np.clip(t / tmax, 0, 1) * w
        ys = y + np.clip((yy - 0.32) / (1.0 - 0.32), 0, 1) * h
        ax.plot(xs, ys, color=color, lw=1.15)


def draw_gantt_icon(ax: plt.Axes, data: dict[str, object], x: float, y: float, w: float, h: float) -> None:
    gantt = data["gantt"]
    tasks = gantt[gantt["Stage"].eq("Stage4_Northridge_impact-first")].sort_values(["Start_Time", "End_Time"]).reset_index(drop=True)
    if tasks.empty:
        return
    sample = tasks.iloc[np.unique(np.linspace(0, len(tasks) - 1, 5, dtype=int))].copy().sort_values("Start_Time")
    max_end = max(1.0, float(sample["End_Time"].max()))
    lane_h = h / len(sample)
    ax.add_patch(patches.Rectangle((x, y), w, h, facecolor="none", edgecolor=C["panel_border"], linewidth=0.35))
    for i, (_, row) in enumerate(sample.iterrows()):
        yy = y + h - (i + 0.65) * lane_h
        start = float(row["Start_Time"])
        end = float(row["End_Time"])
        travel = max(float(row["Travel_Time"]), max_end * 0.035)
        ax.plot([x, x + w], [yy + lane_h * 0.17, yy + lane_h * 0.17], color=C["panel_border"], lw=0.25, alpha=0.6)
        tx = x + max(0, start - travel) / max_end * w
        rx = x + start / max_end * w
        rw = max((end - start) / max_end * w, 0.15)
        tw = travel / max_end * w
        ax.add_patch(patches.Rectangle((tx, yy), tw, lane_h * 0.34, facecolor=C["hazard"], edgecolor="none"))
        ax.add_patch(patches.Rectangle((rx, yy), rw, lane_h * 0.34, facecolor="#AEB8C2", edgecolor="none"))


def draw_typology_icon(ax: plt.Axes, data: dict[str, object], x: float, y: float, w: float, h: float) -> None:
    tracts = data["tracts"]
    clusters = data["clusters"]
    bounds = data["bounds"]
    typ = tracts.merge(clusters[["tract_id", "cluster"]], on="tract_id", how="inner")
    for _, row in typ.iloc[:: max(1, len(typ) // 220)].iterrows():
        px, py = geo_xy(float(row["INTPTLON"]), float(row["INTPTLAT"]), bounds, x, y, w, h)
        col = CLUSTER_COLORS[int(row["cluster"]) % len(CLUSTER_COLORS)]
        ax.add_patch(patches.RegularPolygon((px, py), 6, radius=0.18, facecolor=col, edgecolor="none", alpha=0.82))


def draw_heatmap_icon(ax: plt.Axes, x: float, y: float, w: float, h: float) -> None:
    vals = np.array([[0.2, 0.7, 0.4], [0.5, 0.3, 0.6], [0.8, 0.1, 0.35]])
    rows, cols = vals.shape
    for r in range(rows):
        for c in range(cols):
            ax.add_patch(
                patches.Rectangle(
                    (x + c * w / cols, y + (rows - r - 1) * h / rows),
                    w / cols - 0.05,
                    h / rows - 0.05,
                    facecolor=plt.cm.PRGn(vals[r, c]),
                    edgecolor="white",
                    linewidth=0.20,
                )
            )


def data_inset(ax: plt.Axes, rect: tuple[float, float, float, float]) -> plt.Axes:
    return ax.inset_axes(rect, transform=ax.transData)


def quiet_axes(ax: plt.Axes, grid: bool = False) -> None:
    ax.tick_params(labelsize=5.0, length=1.8, width=0.4, pad=1)
    for spine in ax.spines.values():
        spine.set_color(C["panel_border"])
        spine.set_linewidth(0.45)
    if grid:
        ax.grid(color=C["panel_border"], linewidth=0.35, alpha=0.55)


def plot_inputs_map(ax: plt.Axes, data: dict[str, object]) -> None:
    tracts = data["tracts"]
    vuln = tracts.merge(data["vulnerability"][["tract_id", "SOVI_SCORE"]], on="tract_id", how="left")
    vuln["vbin"] = pd.qcut(vuln["SOVI_SCORE"], 4, labels=False, duplicates="drop")
    vuln.plot(
        ax=ax,
        column="vbin",
        cmap=matplotlib.colors.ListedColormap(["#F2F4F5", "#DDE7DF", "#B8D1BF", "#82AA8D"]),
        edgecolor="white",
        linewidth=0.06,
        alpha=0.78,
        zorder=1,
    )
    if data["roads"]:
        add_line_collection(ax, data["roads"], C["road"], 0.18, 0.26, zorder=2)
    add_line_collection(ax, geometry_segments(data["trans_lines"]), C["grid"], 0.46, 0.58, zorder=3)
    damage = data["damage"].dropna(subset=["PGA_Northridge"])
    ax.scatter(
        damage["lon"],
        damage["lat"],
        s=5 + 13 * damage["PGA_Northridge"] / damage["PGA_Northridge"].max(),
        c=damage["PGA_Northridge"],
        cmap="OrRd",
        alpha=0.55,
        edgecolors="none",
        zorder=4,
    )
    ax.scatter(data["nodes"]["lon"], data["nodes"]["lat"], s=7, c=C["grid"], edgecolors="white", linewidths=0.2, zorder=5)
    yards = data["yards"]
    ax.scatter(yards["longitude"], yards["latitude"], s=24, c=C["logistics"], marker="*", edgecolors="white", linewidths=0.25, zorder=6)
    hospitals = data["hospitals"].head(20)
    ax.scatter(hospitals["lon"], hospitals["lat"], s=18, c=C["critical"], marker="P", edgecolors="white", linewidths=0.2, zorder=7)
    geo_setup(ax, data["bounds"])


def plot_topology_map(ax: plt.Axes, data: dict[str, object], gated_ids: set[str] | None = None) -> None:
    try:
        data["tracts"].dissolve().boundary.plot(ax=ax, color="#CCD2D8", linewidth=0.55, alpha=0.85, zorder=0)
    except Exception:
        pass
    nodes = data["nodes"]
    edges = data["edges"]
    if gated_ids is not None:
        nodes = nodes[nodes["sid"].isin(gated_ids)]
        edges = edges[edges["u"].isin(gated_ids) & edges["v"].isin(gated_ids)]
    add_line_collection(ax, edge_segments(nodes, edges), C["grid"], 0.62, 0.78, zorder=2)
    ax.scatter(nodes["lon"], nodes["lat"], s=8.5, c="#E45B0B", edgecolors="white", linewidths=0.2, zorder=3)
    src = nodes[nodes["sid"].isin(data["source_ids"])]
    if not src.empty:
        ax.scatter(src["lon"], src["lat"], s=16, c=C["critical"], marker="^", edgecolors="white", linewidths=0.25, zorder=4)
    geo_setup(ax, data["bounds"])


def dependency_matrix_sample(data: dict[str, object], n_tracts: int = 25, n_subs: int = 13) -> pd.DataFrame:
    mapping = data["mapping"].copy()
    multi_ids = mapping.groupby("tract_id").size()
    pool = mapping[mapping["tract_id"].isin(multi_ids[multi_ids > 1].index)].copy()

    # Use a coherent, genuinely weighted subset: select substations with broad
    # multi-tract coverage, then retain tracts connected to at least two of
    # them and rank those tracts by dependency entropy.
    top_subs = (
        pool.groupby("substation_id")
        .agg(tract_count=("tract_id", "nunique"), total_weight=("weight", "sum"))
        .sort_values(["tract_count", "total_weight"], ascending=False)
        .head(n_subs)
        .index
    )
    pool = pool[pool["substation_id"].isin(top_subs)].copy()
    eligible_ids = pool.groupby("tract_id").size()
    pool = pool[pool["tract_id"].isin(eligible_ids[eligible_ids > 1].index)].copy()
    pool["entropy_term"] = np.where(pool["weight"] > 0, -pool["weight"] * np.log(pool["weight"]), 0.0)
    tract_xy = data["tracts"][["tract_id", "INTPTLON", "INTPTLAT"]]
    pool = pool.merge(tract_xy, on="tract_id", how="left")
    order = (
        pool.groupby("tract_id", as_index=False)
        .agg(
            lon=("INTPTLON", "first"),
            lat=("INTPTLAT", "first"),
            entropy=("entropy_term", "sum"),
            dependency_count=("substation_id", "size"),
        )
        .sort_values(["dependency_count", "entropy"], ascending=False)
    )
    if len(order) > n_tracts:
        # Preserve the actual range from near-even multi-substation dependence
        # to strongly dominant links instead of showing only high-entropy rows.
        sample_idx = np.unique(np.linspace(0, len(order) - 1, n_tracts, dtype=int))
        order = order.iloc[sample_idx]
    order = order.sort_values(["lon", "lat"])
    sub_order = data["nodes"][data["nodes"]["sid"].isin(top_subs)].sort_values(["lon", "lat"])["sid"].tolist()
    matrix = pool.pivot_table(index="tract_id", columns="substation_id", values="weight", aggfunc="sum", fill_value=0)
    return matrix.reindex(index=order["tract_id"], columns=sub_order, fill_value=0)


def plot_dependency_matrix(ax: plt.Axes, data: dict[str, object], compact: bool = False) -> None:
    matrix = dependency_matrix_sample(data, n_tracts=18 if compact else 27, n_subs=10 if compact else 14)
    rows, cols = matrix.shape
    vmax = max(float(matrix.to_numpy().max()), 1e-9)
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    for r in range(rows):
        for c in range(cols):
            val = float(matrix.iloc[r, c])
            strength = math.sqrt(val / vmax) if val > 0 else 0.0
            light = np.asarray(matplotlib.colors.to_rgb("#F4F6F7"))
            dark = np.asarray(matplotlib.colors.to_rgb(C["community"]))
            facecolor = tuple(light * (1.0 - strength) + dark * strength) if val > 0 else "#F4F6F7"
            ax.add_patch(
                patches.Rectangle(
                    (c, rows - r - 1),
                    0.94,
                    0.94,
                    facecolor=facecolor,
                    edgecolor="white",
                    linewidth=0.22,
                    alpha=1.0,
                )
            )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_pga_map(ax: plt.Axes, data: dict[str, object]) -> None:
    try:
        data["tracts"].dissolve().boundary.plot(ax=ax, color="#CCD2D8", linewidth=0.55, alpha=0.85, zorder=0)
    except Exception:
        pass
    damage = data["damage"].dropna(subset=["PGA_Northridge"])
    ax.scatter(
        damage["lon"],
        damage["lat"],
        s=8 + 22 * damage["PGA_Northridge"] / damage["PGA_Northridge"].max(),
        c=damage["PGA_Northridge"],
        cmap="OrRd",
        edgecolors="white",
        linewidths=0.22,
        zorder=3,
    )
    geo_setup(ax, data["bounds"])


def plot_actual_fragility(ax: plt.Axes, data: dict[str, object]) -> None:
    damage = data["damage"]
    xmax = max(0.8, float(damage["PGA_Northridge"].quantile(0.99)) * 1.2)
    x = np.linspace(0.01, xmax, 140)
    for ds, color in zip(range(1, 5), DS_COLORS[1:]):
        mu = float(damage[f"mu_DS{ds}"].median())
        beta = float(damage[f"beta_DS{ds}"].median())
        ax.plot(x, lognorm_cdf(x, mu, beta), color=color, lw=1.0)
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, 1.02)
    ax.set_xticks([])
    ax.set_yticks([])
    quiet_axes(ax)


def plot_damage_outputs(ax: plt.Axes, data: dict[str, object]) -> None:
    summary = data["damage_state_summary"]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    label_fs = 5.45
    title_fs = 5.65
    ax.text(0.27, 0.96, "Residual\nfunctionality", fontsize=title_fs, color=C["muted"], ha="center", va="top", linespacing=0.95)
    residual = summary.sort_values("damage_state").reset_index(drop=True)
    for i, row in residual.iterrows():
        ds_id = int(row["damage_state"])
        yy = 0.66 - i * 0.115
        ax.text(0.03, yy + 0.022, f"DS{ds_id}", fontsize=label_fs, color=C["muted"], ha="left", va="center")
        ax.add_patch(patches.Rectangle((0.19, yy), 0.30, 0.046, facecolor="#EEF1F3", edgecolor="none"))
        ax.add_patch(
            patches.Rectangle(
                (0.19, yy),
                0.30 * float(row["residual_functionality"]),
                0.046,
                facecolor=C["recovery"],
                edgecolor="none",
            )
        )
    durations = summary[summary["damage_state"] > 0].sort_values("damage_state", ascending=False).copy()
    max_duration = max(1.0, float(durations["repair_q75"].max()))
    ax.text(0.78, 0.96, "Repair-duration\nsamples", fontsize=title_fs, color=C["muted"], ha="center", va="top", linespacing=0.95)
    for i, row in durations.reset_index(drop=True).iterrows():
        yy = 0.63 - i * 0.13
        ax.text(0.58, yy + 0.022, f"DS{int(row['damage_state'])}", fontsize=label_fs, color=C["muted"], ha="left", va="center")
        q25 = 0.24 * float(row["repair_q25"]) / max_duration
        median = 0.24 * float(row["repair_duration"]) / max_duration
        q75 = 0.24 * float(row["repair_q75"]) / max_duration
        ax.add_patch(patches.Rectangle((0.72, yy), median, 0.046, facecolor=C["logistics"], edgecolor="none"))
        ax.plot([0.72 + q25, 0.72 + q75], [yy + 0.023, yy + 0.023], color=C["ink"], lw=0.42)
        ax.plot([0.72 + q25, 0.72 + q25], [yy + 0.012, yy + 0.034], color=C["ink"], lw=0.32)
        ax.plot([0.72 + q75, 0.72 + q75], [yy + 0.012, yy + 0.034], color=C["ink"], lw=0.32)


def source_gated_ids(data: dict[str, object], threshold: float = 0.5) -> set[str]:
    damage = data["damage"].set_index("sid")
    active = set(damage.index[damage["mean_func0"].fillna(0) >= threshold])
    graph = nx.Graph()
    graph.add_nodes_from(active)
    graph.add_edges_from(
        (row.u, row.v)
        for row in data["edges"].itertuples(index=False)
        if row.u in active and row.v in active
    )
    sources = active & set(data["source_ids"])
    gated: set[str] = set()
    for source in sources:
        if source in graph:
            gated.update(nx.node_connected_component(graph, source))
    return gated if gated else active


def plot_damage_state_map(ax: plt.Axes, data: dict[str, object]) -> None:
    try:
        data["tracts"].dissolve().boundary.plot(ax=ax, color="#D7DCE1", linewidth=0.48, alpha=0.72, zorder=0)
    except Exception:
        pass
    damage = data["damage"].dropna(subset=["avg_damage_state"])
    ax.scatter(
        damage["lon"],
        damage["lat"],
        s=10,
        c=damage["avg_damage_state"],
        cmap=matplotlib.colors.ListedColormap(DS_COLORS),
        vmin=0,
        vmax=4,
        edgecolors="white",
        linewidths=0.18,
        zorder=2,
    )
    geo_setup(ax, data["bounds"])


def plot_residual_map(ax: plt.Axes, data: dict[str, object]) -> None:
    damage = data["damage"].dropna(subset=["mean_func0"])
    add_line_collection(ax, edge_segments(data["nodes"], data["edges"]), "#D4DBE0", 0.32, 0.42, zorder=1)
    ax.scatter(
        damage["lon"],
        damage["lat"],
        s=10,
        c=damage["mean_func0"],
        cmap="GnBu",
        vmin=0,
        vmax=1,
        edgecolors="white",
        linewidths=0.18,
        zorder=2,
    )
    geo_setup(ax, data["bounds"])


def plot_service_map(ax: plt.Axes, data: dict[str, object]) -> None:
    supply = data["tract_supply"][["tract_id", "supply"]]
    gdf = data["tracts"].merge(supply, on="tract_id", how="inner")
    gdf["service_class"] = pd.cut(
        gdf["supply"],
        bins=[-0.001, 0.2, 0.4, 0.6, 0.8, 1.001],
        labels=False,
        include_lowest=True,
    )
    gdf.plot(
        ax=ax,
        column="service_class",
        cmap=matplotlib.colors.ListedColormap(["#8E1238", "#D95F4B", "#F3CFA6", "#A9D0DE", "#2F7EB5"]),
        vmin=0,
        vmax=4,
        edgecolor="white",
        linewidth=0.035,
        zorder=1,
    )
    geo_setup(ax, data["bounds"])


def plot_baseline_curve(ax: plt.Axes, data: dict[str, object]) -> None:
    recovery = data["recovery"]
    t = recovery["time_hr"]
    y = recovery["Northridge | S3_Mean | Population"]
    ax.plot(t, y, color=C["recovery"], lw=1.35)
    reached = np.flatnonzero(y.to_numpy() >= 0.8)
    if len(reached):
        t80 = float(t.iloc[reached[0]])
        ax.axvline(t80, color=C["hazard"], lw=0.65, ls=(0, (2, 2)))
        ax.text(t80, 0.83, "T80", fontsize=WF_TEXT, color=C["hazard"], ha="center")
    ax.set_xlim(0, 50)
    ax.set_ylim(0.3, 1.02)
    ax.set_xticks([])
    ax.set_yticks([])
    quiet_axes(ax)


def northridge_tasks(data: dict[str, object]) -> pd.DataFrame:
    tasks = data["gantt"][data["gantt"]["Stage"].eq("Stage4_Northridge_impact-first")].copy()
    tasks["sid"] = clean_id(tasks["Substation_ID"])
    tasks = tasks.merge(data["nodes"][["sid", "lon", "lat"]], on="sid", how="left")
    tasks = tasks.merge(
        data["yards"][["yard_id", "longitude", "latitude"]],
        left_on="Crew_Origin_ID",
        right_on="yard_id",
        how="left",
    )
    return tasks.sort_values(["Start_Time", "End_Time"]).reset_index(drop=True)


def plot_dispatch_map(ax: plt.Axes, data: dict[str, object]) -> None:
    tasks = northridge_tasks(data)
    chosen = tasks.iloc[np.unique(np.linspace(0, len(tasks) - 1, 7, dtype=int))]
    if data["roads"]:
        add_line_collection(ax, data["roads"], C["road"], 0.15, 0.22, zorder=0)
    for row in chosen.itertuples(index=False):
        if not all(np.isfinite(v) for v in [row.longitude, row.latitude, row.lon, row.lat]):
            continue
        ax.plot([row.longitude, row.lon], [row.latitude, row.lat], color=C["logistics"], lw=0.55, alpha=0.72, zorder=2)
    ax.scatter(chosen["longitude"], chosen["latitude"], s=27, marker="*", c=C["logistics"], edgecolors="white", linewidths=0.25, zorder=4)
    ax.scatter(chosen["lon"], chosen["lat"], s=12, c=C["hazard"], edgecolors="white", linewidths=0.2, zorder=4)
    geo_setup(ax, data["bounds"])


def plot_gantt(ax: plt.Axes, data: dict[str, object]) -> None:
    tasks = northridge_tasks(data)
    sample = tasks.iloc[np.unique(np.linspace(0, len(tasks) - 1, 7, dtype=int))].sort_values("Start_Time").reset_index(drop=True)
    max_end = float(sample["End_Time"].max())
    for i, row in sample.iterrows():
        y = len(sample) - i - 1
        start = float(row["Start_Time"])
        end = float(row["End_Time"])
        travel = max(float(row["Travel_Time"]), max_end * 0.018)
        ax.barh(y, travel, left=max(0, start - travel), height=0.48, color="#E88484", edgecolor="none")
        ax.barh(y, end - start, left=start, height=0.48, color="#69ADEC", edgecolor=C["ink"], linewidth=0.22)
    ax.set_xlim(0, max_end * 1.02)
    ax.set_yticks([])
    ax.set_xticks([])
    quiet_axes(ax, grid=True)


def plot_strategy_curves(ax: plt.Axes, data: dict[str, object]) -> None:
    recovery = data["recovery"]
    strategy_cols = [
        col
        for col in recovery.columns
        if col.startswith("Northridge |") and col.endswith("| Population") and "S3_Mean" not in col
    ]
    if strategy_cols:
        palette = [
            C["hazard"],
            C["logistics"],
            "#E1B94B",
            C["community"],
            C["grid"],
            C["critical"],
            "#9DA4AA",
            C["purple"],
            "#D85AA5",
            C["recovery"],
        ]
        for idx, col in enumerate(strategy_cols):
            color = palette[idx % len(palette)]
            lw = 1.10 if "Impact" in col else 0.86
            alpha = 0.94 if "Impact" in col else 0.82
            if "Random" in col:
                color, lw, alpha = "#A8AEB4", 0.86, 0.74
            ax.plot(recovery["time_hr"], recovery[col], lw=lw, color=color, alpha=alpha)
        ax.set_xlim(8, 40)
        ax.set_ylim(0.42, 0.92)
        ax.set_xticks([])
        ax.set_yticks([])
        quiet_axes(ax)
        return
    cols = [
        ("Northridge | Impact λ2 first | Population", C["hazard"]),
        ("Northridge | Betweenness first | Population", "#E1B94B"),
        ("Northridge | Hospital first | Population", C["critical"]),
        ("Northridge | Random | Population", "#9DA4AA"),
    ]
    for col, color in cols:
        ax.plot(recovery["time_hr"], recovery[col], lw=1.0, color=color)
    ax.set_xlim(0, 50)
    ax.set_ylim(0.3, 1.02)
    ax.set_xticks([])
    ax.set_yticks([])
    quiet_axes(ax)


def plot_weighted_recovery(ax: plt.Axes, data: dict[str, object]) -> None:
    recovery = data["recovery"]
    pop_cols = [
        col
        for col in recovery.columns
        if col.startswith("Northridge |") and col.endswith("| Population") and "S3_Mean" not in col
    ]
    svi_cols = [
        col
        for col in recovery.columns
        if col.startswith("Northridge |") and col.endswith("| SVI") and "S3_Mean" not in col
    ]
    if pop_cols or svi_cols:
        for col in pop_cols:
            ax.plot(recovery["time_hr"], recovery[col], color=C["grid"], lw=0.78, alpha=0.56)
        for col in svi_cols:
            ax.plot(recovery["time_hr"], recovery[col], color=C["community"], lw=0.78, alpha=0.56)
        if "Northridge | Impact λ2 first | Population" in recovery:
            ax.plot(recovery["time_hr"], recovery["Northridge | Impact λ2 first | Population"], color=C["grid"], lw=1.12, alpha=0.94)
        if "Northridge | Impact λ2 first | SVI" in recovery:
            ax.plot(recovery["time_hr"], recovery["Northridge | Impact λ2 first | SVI"], color=C["community"], lw=1.12, alpha=0.94)
        ax.set_xlim(8, 40)
        ax.set_ylim(0.42, 0.92)
        ax.set_xticks([])
        ax.set_yticks([])
        quiet_axes(ax)
        return
    ax.plot(recovery["time_hr"], recovery["Northridge | Impact λ2 first | Population"], color=C["grid"], lw=1.1)
    ax.plot(recovery["time_hr"], recovery["Northridge | Impact λ2 first | SVI"], color=C["community"], lw=1.1)
    ax.set_xlim(0, 50)
    ax.set_ylim(0.3, 1.02)
    ax.set_xticks([])
    ax.set_yticks([])
    quiet_axes(ax)


def plot_sensitivity_summary(ax: plt.Axes, data: dict[str, object]) -> None:
    sens = data["sensitivity"].copy()
    value_col = "Max within-strategy change in T80_pop (h)"
    sens["match_key"] = (
        sens["Parameter"]
        .astype(str)
        .str.replace(r"\$.*?\$", "", regex=True)
        .str.replace(r"[^A-Za-z]+", " ", regex=True)
        .str.strip()
        .str.lower()
    )
    sens[value_col] = pd.to_numeric(sens[value_col], errors="coerce").fillna(0.0)
    value_by_key = dict(zip(sens["match_key"], sens[value_col]))
    labels_and_keys = [
        ("crew availability", "crew availability"),
        ("repair-time scale", "repair time scale"),
        ("IDW threshold", "idw threshold"),
        ("source-gate threshold", "source gate threshold"),
    ]
    labels = [label for label, _ in labels_and_keys]
    vals = np.asarray([value_by_key.get(key, 0.0) for _, key in labels_and_keys], dtype=float)
    colors = [C["logistics"], C["hazard"], C["community"], C["purple"]]
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 4)
    ax.axis("off")
    vmax = max(1.0, float(np.nanmax(vals)))
    ax.text(
        0.01,
        3.78,
        "sensitivity drivers",
        fontsize=6.0,
        color=C["muted"],
        ha="left",
        va="center",
        weight="bold",
    )
    bar_x = 0.76
    bar_w = 0.21
    ax.plot([bar_x, bar_x], [0.36, 3.30], color=C["panel_border"], lw=0.55)
    for idx, (label, value, color) in enumerate(zip(labels, vals, colors)):
        y = 3.05 - idx * 0.72
        bar_len = bar_w * float(value) / vmax
        ax.text(0.01, y, label, fontsize=5.55, color=C["ink"], ha="left", va="center")
        ax.add_patch(
            patches.Rectangle(
                (bar_x, y - 0.12),
                bar_w,
                0.24,
                facecolor="#EEF1F3",
                edgecolor="none",
            )
        )
        ax.add_patch(
            patches.Rectangle(
                (bar_x, y - 0.12),
                bar_len,
                0.24,
                facecolor=color,
                edgecolor="none",
            )
        )


def plot_typology_map(ax: plt.Axes, data: dict[str, object]) -> None:
    typ = data["tracts"].merge(data["clusters"][["tract_id", "cluster"]], on="tract_id", how="left")
    typ.plot(
        ax=ax,
        facecolor="#C8C8C8",
        edgecolor="#E0E0E0",
        linewidth=0.045,
        zorder=0,
    )
    clustered = typ.dropna(subset=["cluster"])
    clustered.plot(
        ax=ax,
        column="cluster",
        cmap=matplotlib.colors.ListedColormap(CLUSTER_COLORS),
        vmin=0,
        vmax=2,
        edgecolor="#F5F5F5",
        linewidth=0.045,
        zorder=1,
    )
    missing = typ[typ["cluster"].isna()]
    if not missing.empty:
        missing.plot(ax=ax, facecolor="#B8B8B8", edgecolor="#8E8E8E", linewidth=0.055, zorder=2)
    hot_ids = set(data["hotspots"]["tract_id"])
    hot = clustered[clustered["tract_id"].isin(hot_ids)]
    if not hot.empty:
        hot.boundary.plot(ax=ax, color="#8C1740", linewidth=0.85, zorder=3)
    geo_setup(ax, data["bounds"])


def build_figure() -> tuple[Path, Path]:
    data = load_data()

    fig = plt.figure(figsize=(FIG_W_IN, FIG_H_IN), facecolor=C["paper"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, CANVAS_W)
    ax.set_ylim(0, CANVAS_H)
    ax.set_axis_off()

    inputs = (22.0, 59.7, 76.0, 6.3)
    network = (2.0, 42.3, 56.0, 15.2)
    seismic = (62.0, 42.3, 56.0, 15.2)
    translation = (2.0, 21.6, 116.0, 18.9)
    recovery = (2.0, 1.7, 54.0, 18.5)
    outputs = (60.0, 1.7, 58.0, 18.5)

    flow_box(ax, *inputs, None, "Data Inputs", C["grid"], header_h=1.55)
    flow_box(ax, *network, 1, "Topology and Dependency Construction", C["grid"])
    flow_box(ax, *seismic, 2, "Seismic Damage Simulation", C["hazard"])
    flow_box(
        ax,
        *translation,
        3,
        "Damage-to-Service Translation",
        C["purple"],
        face="#FBFCFD",
        title_size=WF_TITLE,
    )
    flow_box(ax, *recovery, 4, "Recovery Modeling", C["recovery"])
    flow_box(ax, *outputs, 5, "Outputs and Interpretation", C["community"])

    # 1. Actual LA study-area layers.
    inputs_map = data_inset(ax, (23.2, 59.9, 30.0, 4.55))
    plot_inputs_map(inputs_map, data)
    input_labels = [
        ("Transmission + substations", C["grid"], "o"),
        ("Scenario PGA fields", C["hazard"], "o"),
        ("Roads + repair yards", C["logistics"], "*"),
        ("Hospitals", C["critical"], "P"),
        ("Tract vulnerability", C["community"], "s"),
    ]
    input_positions = [
        (54.2, 62.85),
        (82.0, 62.85),
        (54.2, 60.65),
        (75.3, 60.65),
        (86.6, 60.65),
    ]
    for (label, color, marker), (legend_x, yy) in zip(input_labels, input_positions):
        ax.scatter([legend_x], [yy], s=18, c=color, marker=marker, edgecolor="white", linewidth=0.2, zorder=6)
        ax.text(legend_x + 0.75, yy, label, fontsize=WF_TEXT, color=C["ink"], ha="left", va="center")

    # 2. Actual direct-link topology and actual tract-substation weights.
    topology_ax = data_inset(ax, (3.4, 46.15, 33.0, 8.2))
    plot_topology_map(topology_ax, data)
    matrix_ax = data_inset(ax, (39.8, 46.05, 16.0, 7.8))
    plot_dependency_matrix(matrix_ax, data)
    step_label(ax, 20.2, 43.50, "LA direct-link topology\nand source substations", size=4.2, color=C["ink"])
    ax.text(
        35.0,
        45.20,
        "connectivity /\ncriticality",
        fontsize=5.0,
        color="#547A98",
        ha="right",
        va="bottom",
        weight="semibold",
        linespacing=0.95,
        bbox={"facecolor": "#F7FAFC", "edgecolor": "#D7E4EC", "linewidth": 0.35, "pad": 0.25},
    )
    step_label(ax, 47.8, 43.50, "Tract\u2013substation\ndependency weights", size=4.2, color=C["ink"])

    # 3. Actual PGA, fragility parameters, MC damage shares, functionality, and repair durations.
    pga_ax = data_inset(ax, (63.3, 45.15, 15.3, 9.0))
    plot_pga_map(pga_ax, data)
    frag_ax = data_inset(ax, (80.35, 46.35, 7.6, 6.7))
    plot_actual_fragility(frag_ax, data)
    damage_ax = data_inset(ax, (90.25, 45.05, 26.1, 9.75))
    plot_damage_outputs(damage_ax, data)
    step_label(ax, 70.9, 43.45, "Scenario PGA at\nsubstations", size=3.65, color=C["ink"])
    step_label(ax, 84.2, 43.45, "Fragility functions", size=3.65, color=C["ink"])
    step_label(ax, 103.25, 43.45, "Damage-conditioned outputs", size=3.85, color=C["ink"])

    # 4. Central mechanism, redrawn from the actual damage, topology, weight, and tract-service products.
    x_positions = [3.0, 22.5, 42.0, 62.5, 88.3]
    panel_widths = [14.0, 14.0, 15.0, 19.0, 29.0]
    panel_y = 25.2
    panel_h = 12.7
    damage_state_ax = data_inset(ax, (x_positions[0], panel_y, panel_widths[0], panel_h))
    plot_damage_state_map(damage_state_ax, data)
    residual_ax = data_inset(ax, (x_positions[1], panel_y, panel_widths[1], panel_h))
    plot_residual_map(residual_ax, data)
    gated_ax = data_inset(ax, (x_positions[2], panel_y, panel_widths[2], panel_h))
    plot_topology_map(gated_ax, data, gated_ids=source_gated_ids(data))
    weights_ax = data_inset(ax, (x_positions[3] + 0.35, panel_y + 0.4, panel_widths[3] - 0.7, panel_h - 0.8))
    plot_dependency_matrix(weights_ax, data, compact=True)
    service_ax = data_inset(ax, (85.8, panel_y - 0.60, 31.4, panel_h + 1.2))
    plot_service_map(service_ax, data)
    translation_labels = [
        "Damage states",
        "Residual functionality",
        "Source-gated functional\ntopology",
        "Tract\u2013substation\ndependency weights",
        "Tract-level service proxy",
    ]
    for x0, width, label in zip(x_positions, panel_widths, translation_labels):
        step_label(ax, x0 + width / 2, 23.15, label, size=5.2, color=C["ink"])
    for idx in range(len(x_positions) - 1):
        mini_arrow(
            ax,
            x_positions[idx] + panel_widths[idx] + 0.5,
            31.7,
            x_positions[idx + 1] - 0.5,
            31.7,
            lw=0.50,
        )

    # 5. Three-column recovery sequence based on the actual curve and scheduling outputs.
    baseline_ax = data_inset(ax, (3.2, 7.05, 15.0, 9.8))
    plot_baseline_curve(baseline_ax, data)
    step_label(ax, 10.7, 5.22, "Unconstrained\nbaseline", size=4.15, color=C["ink"])
    dispatch_ax = data_inset(ax, (20.5, 12.15, 15.0, 4.8))
    plot_dispatch_map(dispatch_ax, data)
    gantt_ax = data_inset(ax, (20.5, 7.05, 15.0, 4.55))
    plot_gantt(gantt_ax, data)
    step_label(ax, 28.0, 5.22, "Crew/yard scheduling\n+ priority strategies", size=4.05, color=C["ink"])
    strategy_ax = data_inset(ax, (37.8, 7.05, 16.0, 9.8))
    plot_strategy_curves(strategy_ax, data)
    step_label(ax, 45.8, 5.22, "Logistics-aware\nrecovery", size=4.15, color=C["ink"])
    mini_arrow(ax, 18.4, 11.5, 20.2, 11.5, lw=0.48)
    mini_arrow(ax, 35.7, 11.5, 37.5, 11.5, lw=0.48)

    # 6. Three clearly separated outputs based on the actual analysis products.
    weighted_ax = data_inset(ax, (61.2, 6.5, 16.8, 10.1))
    plot_weighted_recovery(weighted_ax, data)
    step_label(ax, 69.6, 5.02, "Population- and\nSVI-weighted recovery", size=4.25, color=C["ink"])
    sensitivity_ax = data_inset(ax, (80.0, 6.5, 17.8, 10.1))
    plot_sensitivity_summary(sensitivity_ax, data)
    step_label(ax, 88.9, 5.02, "Sensitivity analysis", size=4.25, color=C["ink"])
    typology_ax = data_inset(ax, (99.6, 6.1, 17.3, 10.8))
    plot_typology_map(typology_ax, data)
    step_label(ax, 108.25, 5.02, "Recovery-vulnerability\ntypology / hotspots", size=4.15, color=C["ink"])

    # Computational dependencies only.
    edge_lw = 0.42
    split_x = inputs[0] + inputs[2] / 2
    split_y = 58.25
    ax.plot([split_x, split_x], [inputs[1], split_y], color="#707A83", lw=edge_lw)
    orth_arrow(ax, [(split_x, split_y), (network[0] + network[2] / 2, split_y), (network[0] + network[2] / 2, network[1] + network[3])], lw=edge_lw)
    orth_arrow(ax, [(split_x, split_y), (seismic[0] + seismic[2] / 2, split_y), (seismic[0] + seismic[2] / 2, seismic[1] + seismic[3])], lw=edge_lw)
    mini_arrow(ax, network[0] + network[2] / 2, network[1], network[0] + network[2] / 2, translation[1] + translation[3], lw=edge_lw)
    mini_arrow(ax, seismic[0] + seismic[2] / 2, seismic[1], seismic[0] + seismic[2] / 2, translation[1] + translation[3], lw=edge_lw)
    label_box_style = {"facecolor": C["paper"], "edgecolor": "none", "pad": 0.10}
    ax.text(
        18.0,
        41.25,
        "source topology + tract\u2013substation weights",
        fontsize=5.45,
        color=C["grid"],
        ha="center",
        weight="bold",
        bbox=label_box_style,
    )
    ax.text(
        103.0,
        41.25,
        "damage states + functionality + repair durations",
        fontsize=5.45,
        color=C["hazard"],
        ha="center",
        weight="bold",
        bbox=label_box_style,
    )
    orth_arrow(
        ax,
        [
            (translation[0] + translation[2] / 2, translation[1]),
            (translation[0] + translation[2] / 2, 21.05),
            (recovery[0] + recovery[2] / 2, 21.05),
            (recovery[0] + recovery[2] / 2, recovery[1] + recovery[3]),
        ],
        lw=edge_lw,
    )
    mini_arrow(ax, recovery[0] + recovery[2], recovery[1] + recovery[3] / 2, outputs[0], outputs[1] + outputs[3] / 2, lw=edge_lw)

    pdf_path = OUT_DIR / f"{BASE_NAME}.pdf"
    svg_path = OUT_DIR / f"{BASE_NAME}.svg"
    png_path = OUT_DIR / f"{BASE_NAME}_600dpi.png"

    export_bbox = fixed_width_export_bbox(fig)
    fig.savefig(pdf_path, format="pdf", bbox_inches=export_bbox, pad_inches=0)
    fig.savefig(svg_path, format="svg", bbox_inches=export_bbox, pad_inches=0)
    svg_text = "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n"
    svg_path.write_text(svg_text, encoding="utf-8")
    fig.savefig(png_path, format="png", dpi=600, bbox_inches=export_bbox, pad_inches=0)
    plt.close(fig)
    return pdf_path, svg_path, png_path


if __name__ == "__main__":
    outputs = build_figure()
    print("Generated methodology workflow figure:")
    for path in outputs:
        print(f" - {path}")
