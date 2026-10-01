"""Presentation-only v2 figure candidates from frozen LA-grid results.

This script reads committed/frozen tabular and figure authorities. It does not
sample, simulate, schedule, optimize, or cluster. All outputs are isolated in
this candidate_v2 directory; results/figures is never written by this script.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import fitz
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import MaxNLocator
from PIL import Image, ImageOps, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
STAGE = ROOT / "results" / "revised_suite" / "LA_Grid_Revised_Suite_20260925"
FORMAL = ROOT / "Formal_Experiment_20260923"
EQUITY = FORMAL / "Equity_Amendment"
STAGE7 = FORMAL / "Stage 7 Output_SOVI_Harmonized"
FIGURES = ROOT / "results" / "figures"
SHAPE = ROOT / "Data" / "LA_Tracts_With_Population.shp"

W_MM = 185.0
DPI = 600
PREVIEW_DPI = 150

STRATEGY_ORDER = [
    "centrality-first", "impact-first", "betweenness-first", "degree-first",
    "closeness-first", "hospital-first", "random", "vulnerability-first",
    "unconstrained",
]
LABEL = {
    "centrality-first": "Centrality-first", "impact-first": "Impact-first",
    "betweenness-first": "Betweenness-first", "degree-first": "Degree-first",
    "closeness-first": "Closeness-first", "hospital-first": "Hospital-first",
    "random": "Random", "vulnerability-first": "Vulnerability-first",
    "unconstrained": "Unconstrained",
}
# One explicit display map is shared by every policy panel in this candidate set.
STYLE = {
    "centrality-first": ("#e41a1c", "-."),
    "impact-first": ("#ff7f00", ":"),
    "betweenness-first": ("#b59a00", (0, (5, 1.5, 1.2, 1.5))),
    "degree-first": ("#4daf4a", "--"),
    "closeness-first": ("#377eb8", (0, (4, 1.6))),
    "hospital-first": ("#555555", (0, (2.2, 1.4))),
    "random": ("#9a9a9a", "-"),
    "vulnerability-first": ("#a65628", "-"),
    "unconstrained": ("#111111", "--"),
}
QUARTILE_COLS = {"Q1": "burden_Q1_hr", "Q2": "burden_Q2_hr", "Q3": "burden_Q3_hr", "Q4": "burden_Q4_hr"}
HAZARDS = ["LongBeach", "SanFernando", "Northridge", "2pc50"]
HAZARD_LABEL = {"LongBeach": "Long Beach", "SanFernando": "San Fernando", "Northridge": "Northridge", "2pc50": "2pc50"}
POLICIES_4 = ["impact-first", "hospital-first", "degree-first", "vulnerability-first"]

plt.rcParams.update({
    "font.family": "Arial", "font.sans-serif": ["Arial"],
    "font.size": 7.5, "axes.titlesize": 9.5, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.2, "ytick.labelsize": 7.2,
    "legend.fontsize": 7.2, "axes.linewidth": 0.6,
    "lines.linewidth": 1.2, "patch.linewidth": 0.5,
    "grid.linewidth": 0.4, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_figure(fig, stem: str):
    """Write exact 185-mm PDF, 600-dpi PNG and a 150-dpi page-width preview."""
    pdf = OUT / f"{stem}.pdf"
    png = OUT / f"{stem}.png"
    preview = OUT / f"{stem}_preview.png"
    meta = {"Title": stem.replace("_", " "), "Author": "Frozen-results figure review candidate v2"}
    fig.savefig(pdf, format="pdf", dpi=DPI, metadata=meta, facecolor="white")
    fig.savefig(png, format="png", dpi=DPI, facecolor="white")
    fig.savefig(preview, format="png", dpi=PREVIEW_DPI, facecolor="white")
    plt.close(fig)
    return pdf, png, preview


def fig_mm(height_mm: float):
    return plt.figure(figsize=(W_MM / 25.4, height_mm / 25.4), facecolor="white")


def title(ax, label: str, text: str):
    ax.set_title(f"{label}. {text}", loc="left", fontweight="bold", pad=5.5)


def read_eval():
    formal = pd.read_parquet(FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
    vulnerability = pd.read_parquet(EQUITY / "VULNERABILITY_PRIMARY_SUMMARY.parquet")
    key = ("hazard", "realization_id", "strategy_id", "resource_scenario", "mapping", "gate")
    use = [
        *key, "population_weighted_normalized_burden_hr", "population_T80_hr",
        "hospital_mean_normalized_burden_hr", "burden_gini", "burden_Q1_hr",
        "burden_Q2_hr", "burden_Q3_hr", "burden_Q4_hr",
        "signed_Q4_minus_Q1_hr", "absolute_Q4_minus_Q1_hr",
        "L_source_population_mass_weighted_hr", "horizon_hr",
    ]
    a = formal[[c for c in use if c in formal.columns]].copy()
    b = vulnerability[[c for c in use if c in vulnerability.columns]].copy()
    d = pd.concat([a, b], ignore_index=True)
    filt = d[
        d.hazard.eq("2pc50") & d.mapping.eq("M1_UTILITY_003") &
        d.gate.eq("G1_BASELINE_050")
    ].copy()
    if filt.duplicated(["resource_scenario", "realization_id", "strategy_id"]).any():
        raise ValueError("Frozen formal outcome inputs contain duplicate strategy-realization rows")
    return filt


def scenario_slice(data: pd.DataFrame, resource: str):
    return data[data.resource_scenario.eq(resource)].copy()


def summary_5_95(values):
    v = pd.to_numeric(pd.Series(values), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if not len(v):
        return np.nan, np.nan, np.nan, 0
    return float(np.mean(v)), float(np.quantile(v, .05)), float(np.quantile(v, .95)), int(len(v))


def map_domain():
    tracts = gpd.read_file(SHAPE)
    tracts["tract_id"] = tracts["GEOID"].astype(str).str.zfill(11)
    return tracts


def projected_map_data(frame: gpd.GeoDataFrame):
    if frame.crs is not None and frame.crs.to_epsg() != 3310:
        return frame.to_crs(epsg=3310)
    return frame


def style_map_axis(ax):
    ax.set_axis_off()
    ax.set_aspect("equal")


def panel_legend(ax, handles, ncol=3, y=-.03):
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(.5, y),
              ncol=ncol, frameon=False, handlelength=1.6, columnspacing=1.1,
              handletextpad=.45, borderaxespad=0.)


def image_crop_from_pdf(pdf_path: Path, rect_points: tuple[float, float, float, float], dpi=600):
    doc = fitz.open(pdf_path)
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), clip=fitz.Rect(*rect_points), alpha=False)
    image = Image.open(__import__("io").BytesIO(pix.tobytes("png"))).convert("RGB")
    doc.close()
    return image


def build_fig01():
    fig = fig_mm(100)
    ax = fig.add_axes([.025, .08, .95, .84])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(.5, .98, "Revised analytical framework", ha="center", va="top", fontsize=10,
            fontweight="bold", transform=ax.transAxes)
    cards = [
        ("01  Hazard and damage", "Four fixed PGA scenarios\nStation DS sampled per\nphysical realization", "Fixed PGA; aleatory DS"),
        ("02  Network service", "Functional station plus a\npath to an active Core\nsource", "Topology gate; no load-flow"),
        ("03  Tract dependency", "Revised utility-compatible\nweights distribute station\nservice to 2,315 tracts", "Public-site agreement check"),
        ("04  Restoration", "Eight fixed priorities;\nrealized repair tasks,\ndirected travel and crews", "Vulnerability-first included"),
        ("05  Community outcomes", "Recovery, burden, hospitals,\nQ1-Q4, inequality, typology\nand hotspot screening", "Capacity robustness is bounded"),
    ]
    xs = np.linspace(.105, .895, 5)
    width, y, height = .168, .52, .43
    fill = ["#edf1f3", "#e4edf2", "#eaf0e8", "#f4eee5", "#eee9f0"]
    for i, (x, (head, body, tag)) in enumerate(zip(xs, cards)):
        card = FancyBboxPatch((x-width/2, y-height/2), width, height,
                              boxstyle="round,pad=0.012,rounding_size=0.012",
                              facecolor=fill[i], edgecolor="#53616a", linewidth=.65)
        ax.add_patch(card)
        ax.text(x, y+height*.29, head, ha="center", va="center", fontsize=8.0, weight="bold", wrap=True)
        ax.text(x, y+.02, body, ha="center", va="center", fontsize=7.3, linespacing=1.25)
        ax.text(x, y-height*.33, tag, ha="center", va="center", fontsize=7.0, color="#46535a", wrap=True)
        if i < 4:
            ax.add_patch(FancyArrowPatch((x+width*.52, y), (xs[i+1]-width*.52, y),
                                         arrowstyle="-|>", mutation_scale=8, linewidth=.65,
                                         color="#52616a"))
    ax.text(.5, .17,
            "Strategy evaluation reuses paired frozen physical realizations.  Stage 7 typology and SCE capacity checks are descriptive/robustness layers, not new service gates.",
            ha="center", va="center", fontsize=7.4, color="#3b454b", wrap=True)
    ax.text(.5, .075,
            "The production source gate represents reachability only; electrical capacity, load flow and delivered MW are not modeled.",
            ha="center", va="center", fontsize=7.2, style="italic", color="#555555", wrap=True)
    fig.subplots_adjust(0, 0, 1, 1)
    return save_figure(fig, "Fig01_Revised_Analytical_Framework")


def build_fig02():
    source_pdf = FIGURES / "Fig02_System_Network_and_Mapping.pdf"
    # Crops retain the original July network-map content; only plot interiors are
    # placed in a new comparison layout. Map keys are redrawn in the same colors.
    crop_a = image_crop_from_pdf(source_pdf, (123, 18, 433, 219))
    crop_b = image_crop_from_pdf(source_pdf, (123, 268, 433, 474))
    crop_c = image_crop_from_pdf(source_pdf, (20, 545, 470, 815))
    bench_path = ROOT / "provenance" / "reviewer_working" / "R1_Comment1_2_External_Evidence_20260922" / "SCE_MAPPING_BENCHMARK_SUMMARY.csv"
    bench = pd.read_csv(bench_path)
    bench = bench[(bench.version == "NEW_20260922") & (bench.candidate_kind == "direct_site")].copy()
    expected = {"JULY_BASELINE_92", "JULY_UTILITY_CONSTRAINED_92"}
    if set(bench.mapping) != expected or not (bench.tract_count == 337).all():
        raise ValueError("337-tract direct-site benchmark scope does not match expected frozen rows")
    fig = fig_mm(170)
    gs = fig.add_gridspec(2, 2, left=.045, right=.965, top=.955, bottom=.075,
                          wspace=.12, hspace=.24, height_ratios=[1, 1])
    axa = fig.add_subplot(gs[0, 0]); axb = fig.add_subplot(gs[0, 1])
    axa.imshow(crop_a); axb.imshow(crop_b)
    for ax in (axa, axb): ax.axis("off")
    title(axa, "A", "Physical GIS network")
    title(axb, "B", "Simplified retained topology")
    handles_a = [
        Line2D([0], [0], color="#999999", lw=1.0, ls="--", label="CEC transmission lines"),
        Line2D([0], [0], color="#3f8dbf", lw=1.2, label="Direct substation links"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#f05a28", markeredgecolor="white", markersize=5, label="Retained grid stations"),
    ]
    handles_b = [
        Line2D([0], [0], color="#666666", lw=1.0, label="CEC transmission lines"),
        Line2D([0], [0], color="#7fb6dc", lw=1.2, label="Simplified topology"),
        Line2D([0], [0], marker="x", color="#f05a28", lw=0, markersize=5, label="CEC substations"),
    ]
    panel_legend(axa, handles_a, ncol=2, y=-.02)
    panel_legend(axb, handles_b, ncol=2, y=-.02)
    # Bottom-left mapping map remains the frozen mapped-station-count map.
    axc = fig.add_subplot(gs[1, 0]); axc.imshow(crop_c); axc.axis("off")
    title(axc, "C", "Utility-compatible tract dependency")
    # Add an explicit color key: count of mapped stations, not validation accuracy.
    cbar_ax = axc.inset_axes([.18, -.055, .64, .055])
    sm = matplotlib.cm.ScalarMappable(norm=mcolors.Normalize(1, 9), cmap="Blues")
    cb = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal", ticks=[1, 3, 5, 7, 9])
    cb.set_label("Mapped substations per tract", fontsize=7.2, labelpad=1)
    cb.ax.tick_params(labelsize=7.0, length=2, width=.5)
    # Public-site agreement, not accuracy or feeder-territory validation.
    axd = fig.add_subplot(gs[1, 1])
    title(axd, "D", "Public-site match in 337 comparable tracts")
    metrics = [("Any candidate", "any_match"), ("Top-1", "top1"), ("Top-3", "top3")]
    y = np.arange(len(metrics)); offsets = [-.13, .13]
    colors = {"JULY_BASELINE_92": "#8d989f", "JULY_UTILITY_CONSTRAINED_92": "#386f8e"}
    names = {"JULY_BASELINE_92": "July baseline", "JULY_UTILITY_CONSTRAINED_92": "Utility-compatible"}
    for off, mapping in zip(offsets, ["JULY_BASELINE_92", "JULY_UTILITY_CONSTRAINED_92"]):
        row = bench[bench.mapping.eq(mapping)].iloc[0]
        vals = [100 * float(row[col]) for _, col in metrics]
        axd.scatter(vals, y+off, s=26, color=colors[mapping], label=names[mapping], zorder=3)
        for xv, yv in zip(vals, y+off):
            axd.text(xv+.25, yv, f"{xv:.1f}%", va="center", fontsize=7.0, color=colors[mapping])
    axd.set_yticks(y, [m for m, _ in metrics]); axd.invert_yaxis()
    axd.set_ylim(2.55, -.55)
    axd.set_xlim(80, 101); axd.set_xticks([80, 85, 90, 95, 100])
    axd.set_xlabel("Public-site agreement (%) - axis shown from 80%")
    axd.grid(axis="x", alpha=.22)
    axd.text(.02, .98, "Gray: July baseline    Blue: utility-compatible", transform=axd.transAxes,
             fontsize=7.0, va="top", color="#454545")
    return save_figure(fig, "Fig02_System_Network_Mapping_and_Public_Site_Check")


def build_fig03(eval_data):
    damage_dir = STAGE / "Stage 1 Output_expanded"
    init_t80 = pd.read_csv(damage_dir / "S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv")
    decomp = pd.read_csv(STAGE / "Stage 3 Output_expanded" / "LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv")
    service = init_t80[init_t80.hazard.isin(HAZARDS)].copy()
    geoms = map_domain()
    if service[service.hazard.eq("2pc50")].tract_id.astype(str).nunique() != 2315:
        raise ValueError("Expected 2,315 tracts in frozen initial service/T80 table")
    fig = fig_mm(216)
    gs = fig.add_gridspec(3, 2, left=.13, right=.965, top=.96, bottom=.07,
                          hspace=.55, wspace=.28, height_ratios=[.9, .92, 1.25])
    # A: one mean damage-state value per station, each itself averaged across 1,000.
    axa = fig.add_subplot(gs[0, 0]); title(axa, "A", "Mean station damage state")
    ds = [pd.read_csv(damage_dir / f"MC_Device_Damage_AvgDS_{h}.csv").avg_damage_state.to_numpy() for h in HAZARDS]
    bp = axa.boxplot(ds, patch_artist=True, showfliers=False, whis=(5, 95), widths=.56)
    for box, h in zip(bp["boxes"], HAZARDS): box.set_facecolor({"LongBeach":"#6f8fa6","SanFernando":"#4c9278","Northridge":"#9a7559","2pc50":"#a65628"}[h]); box.set_alpha(.68)
    for key in ("medians", "whiskers", "caps"):
        for item in bp[key]: item.set_color("#34424a"); item.set_linewidth(.65)
    axa.set_xticks(np.arange(1, 5), [HAZARD_LABEL[h] for h in HAZARDS], rotation=15, ha="right")
    axa.set_ylabel("Station mean damage state (DS0-DS4)"); axa.grid(axis="y", alpha=.2)
    # B: tract-level mean initial service, not realization spread.
    axb = fig.add_subplot(gs[0, 1]); title(axb, "B", "Initial tract-service distributions")
    for h in HAZARDS:
        x = np.sort(service.loc[service.hazard.eq(h), "mean_initial_service_proxy"].dropna().to_numpy())
        if len(x): axb.plot(x, np.arange(1, len(x)+1)/len(x), color={"LongBeach":"#6f8fa6","SanFernando":"#4c9278","Northridge":"#9a7559","2pc50":"#a65628"}[h], lw=1.2, label=HAZARD_LABEL[h])
    axb.set_xlim(0, 1); axb.set_ylim(0, 1); axb.set_xlabel("Mean initial modeled tract service"); axb.set_ylabel("Cumulative share of tracts")
    axb.grid(alpha=.18); axb.legend(frameon=False, loc="lower right", ncol=2)
    # C: four-hazard integrated decomposition under the formal Hospital-first policy.
    axc = fig.add_subplot(gs[1, :]); title(axc, "C", "Where modeled service burden accumulates")
    d = decomp[(decomp.resource_scenario.eq("C57_D1")) & decomp.strategy_id.eq("hospital-first")].copy()
    d = d.set_index("hazard").loc[HAZARDS].reset_index()
    y = np.arange(len(HAZARDS)); left = np.zeros(len(HAZARDS))
    parts = [("Local physical damage", "self_mean_hr", "#68757d"), ("Functionality threshold", "threshold_mean_hr", "#8fb8c9"), ("Loss of source path", "source_mean_hr", "#d17b3f")]
    for label, col, color in parts:
        vals = d[col].to_numpy(float)
        axc.barh(y, vals, left=left, height=.57, color=color, label=label, edgecolor="white", linewidth=.4)
        left += vals
    shares = d.source_fraction_of_mean_total.to_numpy(float) * 100
    for i, (total, share) in enumerate(zip(left, shares)):
        axc.text(total+.18, i, f"source-path {share:.1f}%", va="center", fontsize=7.0)
    axc.set_yticks(y, [HAZARD_LABEL[h] for h in HAZARDS]); axc.invert_yaxis()
    axc.set_xlabel("Population-weighted modeled service burden (h)")
    axc.grid(axis="x", alpha=.18); axc.set_axisbelow(True)
    axc.set_xlim(0, float(left.max()) + 7.0)
    axc.legend(frameon=False, loc="upper right", ncol=1)
    # D: realization-level population T80 beside mean tract-level T80 map.
    axd = fig.add_subplot(gs[2, 0]); title(axd, "D", "Unconstrained population T80")
    u = scenario_slice(eval_data, "C57_D1")
    u = u[u.strategy_id.eq("unconstrained")]
    vals = pd.to_numeric(u.population_T80_hr, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if not len(vals): raise ValueError("No finite population T80 observations for unconstrained 2pc50")
    axd.hist(vals, bins=26, color="#7897ad", edgecolor="white", linewidth=.45)
    med = float(np.median(vals)); axd.axvline(med, color="#273d4b", ls="--", lw=1.0, label=f"Median {med:.1f} h")
    axd.set_xlabel("Population-weighted time to 80% service (h)"); axd.set_ylabel("Realizations (n)")
    axd.legend(frameon=False); axd.grid(axis="y", alpha=.18)
    map_ax = fig.add_subplot(gs[2, 1])
    t = init_t80[init_t80.hazard.eq("2pc50")].copy()
    t["tract_id"] = t.tract_id.astype(str).str.zfill(11)
    gm = projected_map_data(geoms.merge(t, on="tract_id", how="inner"))
    vals_map = gm.mean_T80_hr_when_reached.replace([np.inf, -np.inf], np.nan)
    vmin = float(vals_map.min()); vmax = float(vals_map.max())
    gm.plot(column="mean_T80_hr_when_reached", ax=map_ax, cmap="YlGnBu", vmin=vmin, vmax=vmax,
            linewidth=.05, edgecolor="#f5f5f5", missing_kwds={"color":"#eeeeee"})
    style_map_axis(map_ax)
    map_ax.text(0, 1.02, "Mean tract T80 when reached", transform=map_ax.transAxes, ha="left", va="bottom", fontsize=8.1, weight="bold")
    cax = map_ax.inset_axes([.20, -.06, .62, .035])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=mcolors.Normalize(vmin, vmax), cmap="YlGnBu"), cax=cax, orientation="horizontal")
    cb.set_label("Mean tract T80 (h)", fontsize=7.0, labelpad=1); cb.ax.tick_params(labelsize=7, length=2)
    return save_figure(fig, "Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline")


def build_fig04(eval_data):
    d = scenario_slice(eval_data, "C57_D1")
    d = d[d.strategy_id.isin(STRATEGY_ORDER)].copy()
    curves = pd.read_csv(STAGE / "Stage 6 Output_expanded" / "ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv")
    curves = curves[(curves.hazard.eq("2pc50")) & curves.strategy_id.isin(STRATEGY_ORDER) & (curves.time_hr <= 120)]
    if set(curves.strategy_id.unique()) != set(STRATEGY_ORDER): raise ValueError("Recovery curve source is missing one or more distinct policies")
    fig = fig_mm(205)
    gs = fig.add_gridspec(2, 1, left=.16, right=.98, top=.91, bottom=.14, hspace=.42, height_ratios=[.78, 1.25])
    ax = fig.add_subplot(gs[0, 0]); title(ax, "A", "Population-weighted service recovery")
    for key in STRATEGY_ORDER:
        c = curves[curves.strategy_id.eq(key)].sort_values("time_hr")
        color, ls = STYLE[key]
        ax.plot(c.time_hr, c.mean_population_availability_proxy, color=color, ls=ls,
                lw=1.45 if key in POLICIES_4 else 1.0,
                alpha=1.0 if key in POLICIES_4 or key == "unconstrained" else .75,
                label=LABEL[key])
    ax.set_xlim(0, 120); ax.set_ylim(0, 1.02); ax.set_xlabel("Time after earthquake (h)")
    ax.set_ylabel("Mean population service availability")
    ax.grid(alpha=.2); ax.legend(frameon=False, ncol=3, loc="lower right", columnspacing=1.0)
    ax.text(.01, -.34, "Curve display: 0-120 h. Burden metrics below integrate over the full 0-480 h evaluation horizon.", transform=ax.transAxes, fontsize=7.1)
    metrics = [
        ("population_weighted_normalized_burden_hr", "Population burden (h)"),
        ("population_T80_hr", "Population T80 (h)"),
        ("hospital_mean_normalized_burden_hr", "Hospital-linked burden (h)"),
        ("L_source_population_mass_weighted_hr", "Source-path loss (h)"),
    ]
    sub = gs[1, 0].subgridspec(1, 4, wspace=.34)
    order = STRATEGY_ORDER
    y = np.arange(len(order))
    for j, (metric, lab) in enumerate(metrics):
        axm = fig.add_subplot(sub[0, j]);
        if j == 0: title(axm, "B", "Outcome ranges")
        else: axm.set_title(lab, loc="left", fontweight="bold", fontsize=8.2, pad=5.5)
        means=[]; lo=[]; hi=[]
        for key in order:
            v=d.loc[d.strategy_id.eq(key), metric]
            m,p5,p95,n=summary_5_95(v); means.append(m);lo.append(p5);hi.append(p95)
        for yy,key,m,p5,p95 in zip(y,order,means,lo,hi):
            color,_=STYLE[key]
            axm.errorbar(m, yy, xerr=[[max(0,m-p5)],[max(0,p95-m)]], fmt="o", ms=3.5,
                         color=color, ecolor=color, elinewidth=.8, capsize=2.1, alpha=.95)
        axm.set_yticks(y, [LABEL[k] for k in order] if j==0 else [""]*len(order)); axm.invert_yaxis()
        axm.set_xlabel(lab); axm.grid(axis="x", alpha=.18); axm.set_axisbelow(True)
        lo_all=np.array(lo,float); hi_all=np.array(hi,float); lo_all=lo_all[np.isfinite(lo_all)]; hi_all=hi_all[np.isfinite(hi_all)]
        if len(lo_all):
            pad=max((hi_all.max()-lo_all.min())*.06,.1); axm.set_xlim(lo_all.min()-pad, hi_all.max()+pad)
        axm.tick_params(axis="y", length=0, labelsize=7.0 if j==0 else 1)
    fig.text(.17, .045, "Dots = mean across 1,000 frozen realizations; whiskers = 5th-95th realization range, not confidence intervals.", fontsize=7.2)
    return save_figure(fig, "Fig04_All_Policy_Recovery_and_Outcomes")


def build_fig05(eval_data, tracts):
    base=scenario_slice(eval_data,"C57_D1")
    base=base[base.strategy_id.isin(STRATEGY_ORDER)].copy()
    if len(base[base.strategy_id.eq("vulnerability-first")]) != 1000: raise ValueError("VF frozen base results incomplete")
    fig=fig_mm(238)
    gs=fig.add_gridspec(4,1,left=.205,right=.975,top=.95,bottom=.055,hspace=.42,height_ratios=[.82,.78,1.18,.92])
    # A: absolute Q1-Q4 outcomes for four explicit comparator strategies.
    axa=fig.add_subplot(gs[0,0]); title(axa,"A","Absolute burden by vulnerability quartile")
    x=np.arange(1,5)
    for key in POLICIES_4:
        means=[];low=[];high=[]
        for q,col in QUARTILE_COLS.items():
            m,p5,p95,n=summary_5_95(base.loc[base.strategy_id.eq(key),col]);means.append(m);low.append(p5);high.append(p95)
        color,ls=STYLE[key]
        axa.errorbar(x,means,yerr=[np.array(means)-np.array(low),np.array(high)-np.array(means)],
                     color=color,ls=ls,marker="o",ms=3.2,lw=1.1,capsize=2,label=LABEL[key],alpha=.95)
    axa.set_xticks(x,["Q1 lowest","Q2","Q3","Q4 highest"]); axa.set_ylabel("Quartile service burden (h)")
    axa.grid(axis="y",alpha=.18); axa.legend(frameon=False,ncol=4,loc="upper center",bbox_to_anchor=(.5,-.20))
    # B: policy mean outcomes; full distinct scheduled set plus Unconstrained.
    bgs=gs[1,0].subgridspec(1,2,width_ratios=[4.3,1.4],wspace=.08)
    axb=fig.add_subplot(bgs[0,0]); title(axb,"B","Aggregate burden and highest-vulnerability burden")
    legend_ax=fig.add_subplot(bgs[0,1]); legend_ax.axis("off")
    legend_handles=[]
    for key in STRATEGY_ORDER:
        sub=base[base.strategy_id.eq(key)]
        if sub.empty: continue
        mx=float(sub.population_weighted_normalized_burden_hr.mean()); my=float(sub.burden_Q4_hr.mean()); color,_=STYLE[key]
        axb.scatter(mx,my,s=29,color=color,edgecolor="white",linewidth=.45,zorder=3)
        legend_handles.append(Line2D([0],[0],marker="o",color=color,lw=0,markersize=5,label=LABEL[key]))
    axb.set_xlabel("Population-weighted service burden (h)"); axb.set_ylabel("Q4 burden (h)")
    axb.grid(alpha=.18)
    legend_ax.legend(handles=legend_handles,frameon=False,ncol=1,loc="center left",fontsize=7.0,labelspacing=.65,handletextpad=.5)
    # C: matched Vulnerability-first minus reference changes; 5 hour metrics share an honest axis, Gini has its own labeled axis.
    cgs=gs[2,0].subgridspec(3,2,height_ratios=[.17,.18,1],width_ratios=[5,1.15],hspace=.01,wspace=.14)
    ctitle_ax=fig.add_subplot(cgs[0,:]);ctitle_ax.axis("off")
    ctitle_ax.text(0,.15,"C. Vulnerability-first change relative to matched policies",transform=ctitle_ax.transAxes,
                   ha="left",va="bottom",fontsize=9.0,fontweight="bold")
    ref_legend_ax=fig.add_subplot(cgs[1,:]);ref_legend_ax.axis("off")
    axc=fig.add_subplot(cgs[2,0])
    refs=["impact-first","hospital-first","degree-first"]
    refcol={"impact-first":STYLE["impact-first"][0],"hospital-first":STYLE["hospital-first"][0],"degree-first":STYLE["degree-first"][0]}
    metrics=[
        ("population_weighted_normalized_burden_hr","Aggregate burden (h)"),
        ("burden_Q4_hr","Q4 burden (h)"),
        ("signed_Q4_minus_Q1_hr","Signed Q4-Q1 (h)"),
        ("absolute_Q4_minus_Q1_hr","Absolute Q4-Q1 gap (h)"),
        ("hospital_mean_normalized_burden_hr","Hospital-linked (h)"),
    ]
    vf=base[base.strategy_id.eq("vulnerability-first")]
    offsets={"impact-first":-.18,"hospital-first":0,"degree-first":.18}
    for i,(metric,lab) in enumerate(metrics):
        for ref in refs:
            rr=base[base.strategy_id.eq(ref)][["realization_id",metric]].rename(columns={metric:"ref"})
            vv=vf[["realization_id",metric]].rename(columns={metric:"vf"})
            mrg=vv.merge(rr,on="realization_id",validate="one_to_one"); diff=mrg.vf-mrg.ref
            m,p5,p95,n=summary_5_95(diff)
            yy=i+offsets[ref]
            axc.errorbar(m,yy,xerr=[[max(0,m-p5)],[max(0,p95-m)]],fmt="o",color=refcol[ref],ecolor=refcol[ref],
                         ms=3.2,elinewidth=.8,capsize=1.7)
    axc.axvline(0,color="#333333",lw=.55,ls="--",zorder=0)
    axc.set_yticks(np.arange(len(metrics)),[m[1] for m in metrics]);axc.invert_yaxis()
    axc.set_xlabel("Change under Vulnerability-first (h)");axc.grid(axis="x",alpha=.18)
    handles=[Line2D([0],[0],marker="o",color=refcol[r],lw=0,label=LABEL[r]) for r in refs]
    axc.set_ylim(len(metrics)-.5,-.5)
    ref_legend_ax.legend(handles=handles,frameon=False,ncol=3,loc="center left",fontsize=7.0,columnspacing=1.2)
    axg=fig.add_subplot(cgs[2,1]); axg.set_title("Gini",loc="left",fontsize=8.2,fontweight="bold",pad=5.5)
    gmets=[]
    for ref in refs:
        rr=base[base.strategy_id.eq(ref)][["realization_id","burden_gini"]].rename(columns={"burden_gini":"ref"})
        vv=vf[["realization_id","burden_gini"]].rename(columns={"burden_gini":"vf"})
        z=vv.merge(rr,on="realization_id",validate="one_to_one"); gmets.append((ref,z.vf-z.ref))
    for i,(ref,values) in enumerate(gmets):
        m,p5,p95,n=summary_5_95(values)
        axg.errorbar(m,i,xerr=[[max(0,m-p5)],[max(0,p95-m)]],fmt="o",color=refcol[ref],ecolor=refcol[ref],ms=3.2,elinewidth=.8,capsize=1.7)
    axg.axvline(0,color="#333333",lw=.55,ls="--");axg.set_yticks(range(3),["Impact","Hospital","Degree"])
    axg.set_xlabel("Change");axg.grid(axis="x",alpha=.18)
    axg.set_ylim(2.5,-.75)
    # D: frozen tract-level mean paired differences; no artificial +/-1 h classification.
    axd=fig.add_subplot(gs[3,0]);title(axd,"D","Mean tract burden change: Vulnerability-first minus Hospital-first")
    tract_effect_path=EQUITY/"VULNERABILITY_TRACT_EFFECTS.parquet"
    te=pd.read_parquet(tract_effect_path)
    te=te[(te.hazard.eq("2pc50"))&(te.reference_strategy.eq("hospital-first"))].copy()
    te["tract_id"]=te.tract_id.astype(str).str.zfill(11)
    study_geoms=tracts[tracts.tract_id.isin(te.tract_id)].copy()
    gm=projected_map_data(study_geoms.merge(te[["tract_id","mean_paired_delta_burden_hr","population"]],on="tract_id",how="inner"))
    if gm.tract_id.nunique()!=2315: raise ValueError("Tract-effect map must cover the formal 2,315-tract domain")
    v=gm.mean_paired_delta_burden_hr.dropna().to_numpy();lim=max(float(np.nanmax(np.abs(v))) if len(v) else 0,.25)
    norm=mcolors.TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim)
    gm.plot(column="mean_paired_delta_burden_hr",ax=axd,cmap="RdBu_r",norm=norm,linewidth=.045,edgecolor="#f2f2f2",
            missing_kwds={"color":"#eeeeee"})
    style_map_axis(axd)
    axd.set_position([.24,.028,.43,.205])
    cax=axd.inset_axes([1.02,.13,.035,.72]);cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap="RdBu_r"),cax=cax)
    cb.set_label("Mean burden change (h)",fontsize=7.0,labelpad=3);cb.ax.tick_params(labelsize=7,length=2)
    nlow=int((gm.mean_paired_delta_burden_hr<0).sum());nhigh=int((gm.mean_paired_delta_burden_hr>0).sum())
    fig.text(.74,.135,f"Lower mean burden\n{nlow} tracts",fontsize=7.5,ha="left",va="center",color="#315b67")
    fig.text(.74,.085,f"Higher mean burden\n{nhigh} tracts",fontsize=7.5,ha="left",va="center",color="#8b4d48")
    return save_figure(fig,"Fig05_Distributional_Outcomes_and_Reference_Sensitivity")


def build_fig06(eval_data):
    d=eval_data[eval_data.resource_scenario.isin(["C29_D1","C57_D1"]) & eval_data.strategy_id.isin(POLICIES_4)].copy()
    if d.groupby(["resource_scenario","strategy_id"]).realization_id.nunique().min()!=1000:
        raise ValueError("C29/C57 frozen strategy coverage is incomplete")
    metrics=[("population_weighted_normalized_burden_hr","Population-weighted service burden (h)"),
             ("burden_Q4_hr","Highest-vulnerability quartile burden (h)"),
             ("absolute_Q4_minus_Q1_hr","Absolute Q4-Q1 separation (h)"),
             ("hospital_mean_normalized_burden_hr","Hospital-linked tract burden (h)")]
    fig=fig_mm(169);gs=fig.add_gridspec(2,2,left=.12,right=.98,top=.90,bottom=.12,hspace=.47,wspace=.3)
    scens=["C29_D1","C57_D1"];offsets=np.linspace(-.24,.24,len(POLICIES_4))
    for j,(metric,lab) in enumerate(metrics):
        ax=fig.add_subplot(gs[j//2,j%2]);title(ax,"ABCD"[j],lab)
        for k,key in enumerate(POLICIES_4):
            color,_=STYLE[key]
            for si,sc in enumerate(scens):
                vals=d[(d.resource_scenario.eq(sc))&(d.strategy_id.eq(key))][metric]
                m,p5,p95,n=summary_5_95(vals);xx=si+offsets[k]
                ax.errorbar(xx,m,yerr=[[max(0,m-p5)],[max(0,p95-m)]],fmt="o",ms=3.5,color=color,
                            ecolor=color,elinewidth=.8,capsize=2)
        ax.set_xticks([0,1],["29 crews","57 crews"]);ax.set_ylabel(lab);ax.grid(axis="y",alpha=.18)
        ax.set_xlim(-.5,1.5)
    handles=[Line2D([0],[0],marker="o",color=STYLE[k][0],lw=0,label=LABEL[k]) for k in POLICIES_4]
    fig.legend(handles=handles,frameon=False,ncol=4,loc="upper center",bbox_to_anchor=(.55,.99),
               fontsize=7.0,columnspacing=1.15,handletextpad=.4)
    fig.text(.13,.055,"2pc50, frozen D1 repair-duration scenario. Dots = means; whiskers = 5th-95th realization range (n=1,000 per policy/resource case).",fontsize=7.2)
    return save_figure(fig,"Fig06_Resource_Response_of_Policy_Outcomes")


def build_fig07():
    labels_path=STAGE7/"clusters_labels_final.csv"
    status_path=STAGE7/"stage7_full_domain_tract_status.csv"
    profiles_path=STAGE7/"stage7_cluster_profiles_raw_values.csv"
    labels=pd.read_csv(labels_path);labels=labels[labels.scenario.eq("2pc50")].copy()
    labels["tract_id"]=labels.tract_id.astype(str).str.zfill(11)
    status=pd.read_csv(status_path);status=status[status.scenario.eq("2pc50")].copy();status["tract_id"]=status.tract_id.astype(str).str.zfill(11)
    if len(status)!=2315 or labels.tract_id.nunique()!=2291: raise ValueError("Stage 7 domain membership changed from frozen 2,315/2,291 split")
    features=["T80","Pre_1970_Ratio","Pop_Density","NRI_RISK_SCORE","NRI_BUILDVALUE","SOVI_SCORE"]
    merged=labels[["tract_id","cluster",*features]].copy()
    means=merged.groupby("cluster")[features].mean().sort_index()
    z=(means-means.mean(axis=0))/means.std(axis=0,ddof=1).replace(0,1)
    pretty=["Tract T80","Pre-1970 housing ratio","Population density","NRI risk score","NRI building value","FEMA NRI social-vulnerability score"]
    geo=projected_map_data(map_domain().merge(status,on="tract_id",how="inner"))
    # Cluster colors are explicitly keyed by integer cluster ID, as in the Stage 7 authority.
    palette=["#303E4E","#C0A55B","#567E58","#BAD1DB","#724B63"]
    color_by={str(i+1):palette[i] for i in range(5)}
    fig=fig_mm(188);gs=fig.add_gridspec(2,2,left=.19,right=.96,top=.94,bottom=.17,hspace=.32,wspace=.12,height_ratios=[.95,1.25])
    axa=fig.add_subplot(gs[0,:]);title(axa,"A","Residential typology profiles")
    im=axa.imshow(z[features].T.to_numpy(),cmap="coolwarm",norm=mcolors.TwoSlopeNorm(vmin=-2,vcenter=0,vmax=2),aspect="auto")
    cluster_n=merged.groupby("cluster").size().reindex(range(1,6))
    axa.set_xticks(np.arange(5),[f"C{i} (n={int(cluster_n.loc[i])})" for i in range(1,6)])
    axa.set_yticks(np.arange(len(features)),pretty)
    axa.tick_params(axis="both",labelsize=7.0)
    cb=fig.colorbar(im,ax=axa,orientation="vertical",fraction=.022,pad=.015);cb.set_label("Z-score across five cluster means",fontsize=7.0);cb.ax.tick_params(labelsize=7)
    axa.set_ylim(5.5,-.5)
    # B: all domain boundaries, ineligible tracts explicitly gray.
    axb=fig.add_subplot(gs[1,0]);title(axb,"B","Residential typology geography")
    geo["cluster_key"]=geo.cluster.map(lambda x: str(int(x)) if pd.notna(x) else "N/A")
    for key,color in color_by.items(): geo[geo.cluster_key.eq(key)].plot(ax=axb,color=color,edgecolor="white",linewidth=.07)
    geo[geo.cluster_key.eq("N/A")].plot(ax=axb,color="#eeeeee",edgecolor="#777777",linewidth=.16,hatch="///")
    style_map_axis(axb)
    handles=[Line2D([0],[0],marker="s",lw=0,color="none",markerfacecolor=color,markeredgecolor="none",label=f"Cluster {k}") for k,color in color_by.items()]
    handles.append(Line2D([0],[0],marker="s",lw=0,color="none",markerfacecolor="#eeeeee",markeredgecolor="#777777",label="Not in residential typology (n=24)"))
    fig.legend(handles=handles,frameon=False,ncol=3,loc="lower center",bbox_to_anchor=(.50,.055),fontsize=7.0,columnspacing=1.1)
    # C: official combined screening score; preserve true score missingness.
    axc=fig.add_subplot(gs[1,1]);title(axc,"C","Slow-vulnerable hotspot screening")
    geo.plot(column="SlowVulnerable_Hotspot_Score",ax=axc,cmap="Blues",linewidth=.05,edgecolor="#f3f3f3",
             missing_kwds={"color":"#eeeeee","edgecolor":"#888888","hatch":"///"})
    style_map_axis(axc)
    hvals=geo.SlowVulnerable_Hotspot_Score.dropna();vmin=float(hvals.min());vmax=float(hvals.max())
    cax=axc.inset_axes([.91,.15,.025,.65]);cb=fig.colorbar(plt.cm.ScalarMappable(norm=mcolors.Normalize(vmin,vmax),cmap="Blues"),cax=cax)
    cb.set_label("Combined screening score",fontsize=7.0,labelpad=3);cb.ax.tick_params(labelsize=7)
    return save_figure(fig,"Fig07_Community_Typology_and_Hotspots")


def build_figs05():
    ga_dir=FORMAL/"Stage 5 Output_expanded"
    conv=pd.read_csv(ga_dir/"GA_FIVE_SEED_CONVERGENCE.csv").sort_values("seed")
    seeds=sorted(conv.seed.astype(int).unique())
    if len(seeds)!=5: raise ValueError("Expected five frozen GA seeds")
    histories=[]
    for seed in seeds:
        p=ga_dir/f"GA_HISTORY_2pc50_{seed}.csv"
        h=pd.read_csv(p); histories.append(h)
    fig=fig_mm(145);gs=fig.add_gridspec(2,2,left=.14,right=.97,top=.93,bottom=.15,hspace=.42,wspace=.32)
    ax=fig.add_subplot(gs[:,0]);title(ax,"A","Five-seed best-so-far convergence")
    colors=["#1b6b83","#537f68","#a65628","#6b5b95","#8c6d31"]
    for seed,h,color in zip(seeds,histories,colors):
        ax.plot(h.generation,h.best_so_far,color=color,lw=.85,alpha=.78,label=f"Seed {seed}")
    ax.set_xlabel("Generation");ax.set_ylabel("GA objective (frozen fitness scale)")
    ax.grid(alpha=.18);ax.legend(frameon=False,ncol=2,loc="lower right")
    ax.text(.03,.97,"All five seed traces overlap at the frozen Impact-first incumbent.",transform=ax.transAxes,va="top",fontsize=7.0)
    axb=fig.add_subplot(gs[0,1]);title(axb,"B","No seed improved the incumbent")
    y=np.arange(len(conv));vals=conv.search_improved_incumbent.astype(bool).to_numpy()
    axb.scatter(np.full(len(y),.07),y,c=["#777777" if not q else "#4c9278" for q in vals],s=27,marker="s",transform=axb.get_yaxis_transform())
    axb.set_xlim(0,1);axb.set_xticks([]);axb.set_yticks(y,[f"Seed {s}" for s in conv.seed]);axb.set_ylim(len(y)-.5,-.5)
    axb.set_ylabel("Planning seed")
    axb.grid(axis="x",alpha=.15)
    for yi,row in zip(y,conv.itertuples()):
        axb.text(.07,yi,"■",transform=axb.get_yaxis_transform(),va="center",ha="center",fontsize=9.0,color="#777777")
        axb.text(.20,yi,f"Best generation {row.best_generation} | objective {row.fitness:.4f}",transform=axb.get_yaxis_transform(),va="center",fontsize=7.0)
    axc=fig.add_subplot(gs[1,1]);title(axc,"C","Retained sequence identity")
    axc.axis("off")
    axc.text(.03,.78,"GA retained sequence",fontsize=7.5,color="#555555")
    axc.text(.03,.60,"Impact-first",fontsize=10,weight="bold",color=STYLE["impact-first"][0])
    axc.annotate("",xy=(.88,.61),xytext=(.51,.61),xycoords="axes fraction",arrowprops={"arrowstyle":"<->","lw":.8,"color":"#54636a"})
    axc.text(.03,.42,"Direct-community",fontsize=8.3,color="#444444")
    axc.text(.03,.17,"Same frozen sequence; not a ninth scheduled policy.\nNo search seed improved the incumbent; this is not a global-optimality proof.",fontsize=7.0,va="bottom",wrap=True)
    fig.text(.15,.055,"Planning/evaluation split and five seeds are preserved in the frozen GA manifests; this figure reports the existing search result only.",fontsize=7.0)
    return save_figure(fig,"FigS05_GA_Reproducibility")


CAPTIONS = {
"Fig01_Revised_Analytical_Framework": "Revised analytical framework. Four fixed hazard scenarios provide station-level PGA inputs for realization-specific damage-state sampling. Network-side modeled service requires station functionality and source reachability through the production topology gate; it does not represent load flow, generation adequacy, transmission capacity, or delivered MW. The utility-compatible mapping distributes station service to the 2,315-tract domain. Frozen repair policies operate on realization-specific damaged tasks using directed travel and crew dispatch. Downstream evaluation reports service recovery, burden, critical-service and vulnerability-group outcomes, and descriptive community typology. The bounded SCE capacity analysis is a robustness layer and is not applied as a new production gate.",
"Fig02_System_Network_Mapping_and_Public_Site_Check": "System representation and public-site mapping comparison. (A) Physical CEC transmission/substation context. (B) Simplified retained topology; the formal graph contains 92 stations, 318 edges, and 14 active Core sources. (C) Revised utility-compatible tract dependency, displayed as mapped substations per tract; this count describes mapping structure and is not a validation statistic. (D) Public-site agreement for the 337 tracts with comparable site evidence: any candidate match means at least one mapped candidate matches a public site; top-1 tests the highest-weight candidate; top-3 tests whether any of the three highest-weight candidates matches. Values compare the frozen July baseline and utility-compatible mapping on the same 337-tract set. The earlier 342-tract crosswalk is a different evidence set (316 tracts overlap; 26 old-only and 21 current-only) and its values are not pooled with these results. Public-site agreement is not feeder or service-territory ground truth and is not a validation of the full service/recovery model. The public-site percentage axis is explicitly shown from 80% to 100%.",
"Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline": "Hazard context, modeled service-loss components, and unconstrained baseline. (A) Each box summarizes 92 station-level mean damage states, where each station value averages 1,000 frozen physical realizations; the boxes describe spatial heterogeneity across stations, not Monte Carlo uncertainty. (B) Empirical distribution across tracts of mean initial modeled service, with one tract mean formed from the frozen realization archive for each hazard. (C) Population-weighted integrated burden decomposition for Hospital-first under the 57-crew, D1 repair-duration case; local physical damage, functionality-threshold loss, and source-path loss are integrated over the common 0-480 h horizon. The source-path shares are 4.3% for Long Beach, 8.7% for San Fernando, 14.9% for Northridge, and 11.8% for 2pc50. Cross-hazard differences also reflect the adopted split between historical-hazard and current 2pc50 fragility parameter sets, so they cannot be attributed to PGA alone. (D, left) Distribution across 1,000 frozen 2pc50 realizations of population-weighted T80 for the Unconstrained reference; all 1,000 reached T80 and none is assigned the 480 h horizon as a substitute. (D, right) Mean tract T80 among realizations in which the tract reached 80% service; gray denotes no reached mean. The population-level realization T80 and tract-level conditional mean T80 are different estimands.",
"Fig04_All_Policy_Recovery_and_Outcomes": "Recovery and outcomes for all eight distinct scheduled policies and the Unconstrained reference under 2pc50 and the 57-crew, D1 repair-duration case. Panel A shows the mean population service-availability proxy over 0-120 h; the outcome summaries use the full 0-480 h horizon. Panel B reports population-weighted service burden, population T80, hospital-linked tract burden, and source-path-related burden. Dots are means across 1,000 frozen realizations and whiskers are the 5th-95th realization range, not confidence intervals. Strategies use matched physical realizations. Direct-community has the same frozen sequence as Impact-first and is not shown as a separate policy. Source-path-related burden is a modeled loss component, not a measure of delivered power or capacity.",
"Fig05_Distributional_Outcomes_and_Reference_Sensitivity": "Distributional outcomes and reference sensitivity under 2pc50 and the 57-crew, D1 repair-duration case. (A) Absolute tract burden in the lowest through highest social-vulnerability quartiles for Impact-first, Hospital-first, Degree-first, and Vulnerability-first; whiskers show 5th-95th realization ranges. (B) Policy mean population-weighted service burden versus mean highest-vulnerability-quartile burden for the full set of eight distinct scheduled policies and Unconstrained. (C) Matched realization change under Vulnerability-first relative to Impact-first, Hospital-first, and Degree-first; negative values indicate lower burden for burden-valued metrics. The five hour-scale outcomes share the displayed hour axis; the Gini change uses its own labeled unitless axis. Population-weighted Gini equals 0 under equal tract burden and increases as tract burdens become more unequal. (D) Continuous tract-level mean paired burden change, Vulnerability-first minus Hospital-first, across matched frozen realizations. The map colors show mean effects, not per-realization improved population or statistical significance. Q4 denotes the highest social-vulnerability quartile; Q1 denotes the lowest.",
"Fig06_Resource_Response_of_Policy_Outcomes": "Resource response of four policy outcomes under 2pc50 for the frozen D1 duration case. Each panel compares the 29-crew and 57-crew cases for Impact-first, Hospital-first, Degree-first, and Vulnerability-first. Dots are means and whiskers are the 5th-95th realization range from 1,000 frozen outcomes per policy/resource case. The panels show population-weighted service burden, highest-vulnerability-quartile burden, absolute Q4-Q1 burden separation, and hospital-linked tract burden. Q1 and Q4 denote the lowest- and highest-social-vulnerability quartiles. These scenario results test how modeled resource availability changes outcomes; they do not establish a universal direction across unshown hazards or other resource/duration cases.",
"Fig07_Community_Typology_and_Hotspots": "Harmonized Stage 7 community typology and hotspot screening for 2pc50. (A) Means for six selected features are shown as z-scores across the five cluster-level means; the values are not tract-level z-scores. (B) Residential typology membership for 2,291 of 2,315 study tracts using the fixed cluster-ID color palette. The 24 tracts outside residential typology are hatched gray and are not assigned a cluster. (C) Official combined slow-vulnerable hotspot score; missing scores remain unclassified. Cluster labels describe community typology and the hotspot score is a screening indicator, not a repair priority, intervention ranking, or independent causal validation.",
"FigS05_GA_Reproducibility": "Frozen five-seed genetic algorithm (GA) evidence for 2pc50 planning. (A) Best-so-far objective traces for the five retained seeds. (B) The existing convergence summary records no seed improving the frozen incumbent; the objective scale is shown without claiming global optimality. (C) The retained sequence is Impact-first, and Direct-community is sequence-equivalent rather than an additional scheduled policy. The figure reports only existing planning outputs; it does not rerun GA or select policies using evaluation realizations.",
}


def shapefile_sources():
    base=SHAPE.with_suffix("")
    required=[base.with_suffix(ext) for ext in (".shp",".shx",".dbf",".prj")]
    optional=[base.with_suffix(".cpg")]
    missing=[str(p) for p in required if not p.exists()]
    if missing: raise FileNotFoundError(f"Study tract shapefile bundle incomplete: {missing}")
    return [*required,*[p for p in optional if p.exists()]]


def source_map():
    return {
        "Fig01_Revised_Analytical_Framework": [ROOT/"config"/"parent_frozen_design"/"FINAL_EXPERIMENT_MATRIX.json", ROOT/"FINAL_REVISION_RUN_SEQUENCE"/"FINAL_REVISION_RUN_MATRIX.json", ROOT/"src"/"la_grid"/"revision"/"r1_source_gate.py"],
        "Fig02_System_Network_Mapping_and_Public_Site_Check": [FIGURES/"Fig02_System_Network_and_Mapping.pdf", ROOT/"Data"/"substation_graph_CEC_edges.csv", ROOT/"Data"/"tract_to_substation_mapping_CEC_expanded.csv", ROOT/"provenance"/"reviewer_working"/"R1_Comment1_2_External_Evidence_20260922"/"SCE_MAPPING_BENCHMARK_SUMMARY.csv", ROOT/"provenance"/"reviewer_working"/"R1_Comment1_2_External_Evidence_20260922"/"SCE_MAPPING_BENCHMARK_TRACTS.csv"],
        "Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline": [STAGE/"Stage 1 Output_expanded"/"S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv", *[STAGE/"Stage 1 Output_expanded"/f"MC_Device_Damage_AvgDS_{h}.csv" for h in HAZARDS], STAGE/"Stage 3 Output_expanded"/"LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv", FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet", *shapefile_sources()],
        "Fig04_All_Policy_Recovery_and_Outcomes": [STAGE/"Stage 6 Output_expanded"/"ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv", FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet", EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig05_Distributional_Outcomes_and_Reference_Sensitivity": [FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet", EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet", EQUITY/"VULNERABILITY_TRACT_EFFECTS.parquet", *shapefile_sources()],
        "Fig06_Resource_Response_of_Policy_Outcomes": [FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet", EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig07_Community_Typology_and_Hotspots": [STAGE7/"clusters_labels_final.csv", STAGE7/"stage7_cluster_profiles_raw_values.csv", STAGE7/"stage7_full_domain_tract_status.csv", STAGE7/"stage7_typology_noneligible_tracts.csv", ROOT/"src"/"la_grid"/"plotting"/"Project_Visualizer.py", *shapefile_sources()],
        "FigS05_GA_Reproducibility": [FORMAL/"Stage 5 Output_expanded"/"GA_FIVE_SEED_CONVERGENCE.csv", *[FORMAL/"Stage 5 Output_expanded"/f"GA_HISTORY_2pc50_{seed}.csv" for seed in range(42,47)], FORMAL/"Stage 5 Output_expanded"/"INCUMBENT_DIRECT_SCORES_2pc50.csv"],
    }


def write_crosswalk_and_matrix():
    rows = [
        ["Fig01-A","Revised analytical framework","How do hazard, network service, tract dependency, restoration, and community outcomes connect?","Frozen method definitions and accepted stage registry","Process diagram; no numerical result","No reference policy; method architecture","Production gate is reachability; bounded capacity check is not a new gate"],
        ["Fig02-A","Study-system representation","What physical GIS network context underlies the study?","results/figures/Fig02_System_Network_and_Mapping.pdf","CEC transmission lines, direct links, retained station map","Physical CEC context","Image panel cropped from existing authority; geography/content preserved"],
        ["Fig02-B","Reduced system representation","What topology is used for modeled source connectivity?","results/figures/Fig02_System_Network_and_Mapping.pdf; Data/substation_graph_CEC_edges.csv","92 stations; 318 edges; 14 active Core sources","Retained graph","Reachability is not electrical adequacy or delivered MW"],
        ["Fig02-C","Tract dependency","How does utility-compatible mapping distribute station dependencies across tracts?","results/figures/Fig02_System_Network_and_Mapping.pdf; Data/tract_to_substation_mapping_CEC_expanded.csv","Mapped substations per tract","JULY_UTILITY_CONSTRAINED_92 / M1","Count map describes dependency structure, not validation"],
        ["Fig02-D","External mapping evidence","How often do mapped candidates match public-site evidence?","SCE_MAPPING_BENCHMARK_SUMMARY.csv; SCE_MAPPING_BENCHMARK_TRACTS.csv","Any, top-1, top-3 site match among 337 comparable tracts","July baseline vs utility-compatible mapping","Public-site agreement; not feeder/service-territory truth; 342 set is different"],
        ["Fig03-A","Hazard damage","How does station damage severity differ among hazards?","MC_Device_Damage_AvgDS_{hazard}.csv x4","Distribution of 92 station means, each over 1,000 realizations","Four fixed hazards","Station heterogeneity, not Monte Carlo interval"],
        ["Fig03-B","Initial service","How does mean initial tract service differ across hazards?","S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv","ECDF of mean initial service, one mean per tract","Four fixed hazards","Tract means over frozen realizations"],
        ["Fig03-C","Loss mechanisms","How much integrated burden is assigned to damage, threshold, and source-path loss?","LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv","Component means (h) and source share","Hospital-first, C57_D1 across four hazards","Integrated over 0-480 h"],
        ["Fig03-D-left","Unconstrained recovery distribution","What is the realization-level no-crew 2pc50 population T80 distribution?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet","Population-weighted T80 in each frozen realization; 1,000 values, median marker","Unconstrained","Unreached values are not assigned 480 h"],
        ["Fig03-D-right","Unconstrained tract recovery map","Where is mean tract T80 high among tracts that reached 80%?","S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv","Mean tract T80 conditional on reached status","Unconstrained","Distinct estimand from realization-level population T80; unavailable values remain gray"],
        ["Fig04-A","Policy recovery curves","How do the full eight scheduled policies compare over recovery?","ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv","Mean population service availability, 0-120 h display","Eight policies plus Unconstrained","Burden below integrates over 0-480 h"],
        ["Fig04-B1","Aggregate policy outcome","How does population-weighted service burden vary by policy?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000","Eight policies plus Unconstrained; 2pc50 C57_D1","Range is not a confidence interval"],
        ["Fig04-B2","Population recovery timing","How does population T80 vary by policy?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000","Eight policies plus Unconstrained; 2pc50 C57_D1","Unreached values remain missing, not set to horizon"],
        ["Fig04-B3","Hospital-linked tract outcome","How does modeled service burden in hospital-linked tracts vary by policy?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000","Eight policies plus Unconstrained; 2pc50 C57_D1","Not hospital supply or clinical-service capacity"],
        ["Fig04-B4","Source-path loss component","How does source-path-related burden vary by policy?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000","Eight policies plus Unconstrained; 2pc50 C57_D1","A service-loss component, not delivered MW"],
        ["Fig05-A","Absolute distributional outcomes","How does absolute burden vary from Q1 to Q4 for core policy contrasts?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Quartile burdens (h), means and 5th-95th realization ranges","Impact, Hospital, Degree, Vulnerability-first","All four are explicit subsets of the full policy set"],
        ["Fig05-B","Efficiency-distribution relationship","How do aggregate burden and Q4 burden co-vary across policies?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Policy means: overall burden (h) vs Q4 burden (h)","All eight policies plus Unconstrained","Descriptive policy mean plane; no causal or universal equity claim"],
        ["Fig05-C","Reference sensitivity","Does the Vulnerability-first contrast depend on comparator policy?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Matched VF minus Impact/Hospital/Degree differences; mean and 5th-95th paired range","C57_D1, same realization IDs","Hour outcomes share labeled axis; Gini separately scaled with ticks"],
        ["Fig05-D","Spatial paired effects","Where does mean tract burden rise/fall under Vulnerability-first vs Hospital-first?","VULNERABILITY_TRACT_EFFECTS.parquet","Mean paired tract burden change (h), continuous","Vulnerability-first minus Hospital-first","Mean sign is not per-run affected population or significance"],
        ["Fig06-A","Resource response: aggregate burden","How does crew count affect population-weighted service burden?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000 per strategy/resource case","2pc50, D1; C29 vs C57","Frozen scenarios only; not a universal resource law"],
        ["Fig06-B","Resource response: Q4 burden","How does crew count affect highest-vulnerability-quartile burden?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000 per strategy/resource case","2pc50, D1; C29 vs C57","Q4 is highest social-vulnerability quartile"],
        ["Fig06-C","Resource response: group separation","How does crew count affect absolute Q4-Q1 burden separation?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000 per strategy/resource case","2pc50, D1; C29 vs C57","Absolute difference does not show direction; signed group outcomes are in Fig05"],
        ["Fig06-D","Resource response: hospital-linked burden","How does crew count affect modeled service burden in hospital-linked tracts?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet; VULNERABILITY_PRIMARY_SUMMARY.parquet","Mean and 5th-95th realization range, n=1,000 per strategy/resource case","2pc50, D1; C29 vs C57","Not hospital supply or clinical-service capacity"],
        ["Fig07-A","Community profiles","How do five descriptive residential clusters differ on selected variables?","clusters_labels_final.csv; Project_Visualizer.py selected-theme definitions","Cluster-mean z-scores across the five cluster means","Harmonized Stage 7; 2pc50","Not tract-level z-scores"],
        ["Fig07-B","Community typology geography","Where are the 2,291 residential typology members and 24 nonmembers?","stage7_full_domain_tract_status.csv; stage7_typology_noneligible_tracts.csv","Five fixed cluster IDs; 24 N/A in gray hatch","2,315 tract full boundary","Not a service-absence map"],
        ["Fig07-C","Hotspot screening","Where is the official combined slow-vulnerable screening score elevated?","stage7_full_domain_tract_status.csv","SlowVulnerable_Hotspot_Score","Official Stage 7 authority","Screening indicator, not repair/intervention rank"],
        ["FigS05-A","GA convergence","Did the five frozen planning seeds improve the incumbent over generations?","GA_HISTORY_2pc50_42-46.csv","Best-so-far objective by generation","Five planning seeds","Flat traces describe this search only, not global optimality"],
        ["FigS05-B","Incumbent improvement","Did any frozen seed beat the incumbent, and at what generation?","GA_FIVE_SEED_CONVERGENCE.csv","Improved-incumbent flag, best generation, retained objective","Five planning seeds; Impact-first incumbent","No seed improvement is not proof of a global optimum"],
        ["FigS05-C","Retained sequence identity","What sequence was retained and how does Direct-community relate?","INCUMBENT_DIRECT_SCORES_2pc50.csv","Strategy identity and sequence equivalence","Impact-first sequence","Direct-community is not a ninth scheduled policy"],
    ]
    panel_df=pd.DataFrame(rows,columns=["panel_id","theme","scientific_question","frozen_source","metric_definition","reference","interpretation_boundary"])
    prior={
        "Fig01-A":"results/figures/Fig01_Methodology_Workflow.pdf; FINAL_REVISION_RUN_SEQUENCE/ workflow authority",
        "Fig02-A":"results/figures/Fig02_System_Network_and_Mapping.pdf panel A (physical GIS network)",
        "Fig02-B":"results/figures/Fig02_System_Network_and_Mapping.pdf panel B (retained topology)",
        "Fig02-C":"results/figures/Fig02_System_Network_and_Mapping.pdf panel C (mapping count map)",
        "Fig02-D":"results/figures/FigS06_Mapping_Robustness.pdf plus frozen 337-tract SCE benchmark tables",
        "Fig03-A":"results/figures/FigS01_Damage_Severity.pdf; four frozen Stage 1 damage tables",
        "Fig03-B":"results/figures/FigS02_Initial_Service.pdf; frozen Stage 1 tract initial-service table",
        "Fig03-C":"results/figures/FigS04_Network_Criticality_and_Percolation.pdf and Stage 3 loss-decomposition table",
        "Fig03-D-left":"results/figures/Fig03_Unconstrained_Recovery.pdf; formal realization summary",
        "Fig03-D-right":"results/figures/Fig03_Unconstrained_Recovery.pdf; frozen tract T80 table",
        "Fig04-A":"results/figures/Fig04_Restoration_Strategy_Tradeoffs.pdf panel A",
        "Fig04-B1":"results/figures/Fig04_Restoration_Strategy_Tradeoffs.pdf policy burden outcome",
        "Fig04-B2":"results/figures/Fig04_Restoration_Strategy_Tradeoffs.pdf policy T80 outcome",
        "Fig04-B3":"results/figures/Fig04_Restoration_Strategy_Tradeoffs.pdf and Fig05 hospital outcome (deduplicated here)",
        "Fig04-B4":"frozen Stage 3 and formal per-realization source-loss outputs",
        "Fig05-A":"results/figures/Fig06_Vulnerability_Targeting_and_Distributional_Tradeoffs.pdf quartile panel",
        "Fig05-B":"new visual synthesis from the full frozen strategy outcome table",
        "Fig05-C":"results/figures/Fig06_Vulnerability_Targeting_and_Distributional_Tradeoffs.pdf paired/reference panel",
        "Fig05-D":"results/figures/Fig06_Vulnerability_Targeting_and_Distributional_Tradeoffs.pdf tract-effect map",
        "Fig06-A":"results/figures/FigS08_Capacity_Sensitivity.pdf plus frozen C29/C57 formal/equity results",
        "Fig06-B":"results/figures/FigS08_Capacity_Sensitivity.pdf plus frozen C29/C57 formal/equity results",
        "Fig06-C":"results/figures/FigS08_Capacity_Sensitivity.pdf plus frozen C29/C57 formal/equity results",
        "Fig06-D":"results/figures/FigS08_Capacity_Sensitivity.pdf plus frozen C29/C57 formal/equity results",
        "Fig07-A":"results/figures/Fig07_Community_Typology_and_Hotspots.pdf profile panel; harmonized Stage 7 output",
        "Fig07-B":"results/figures/Fig07_Community_Typology_and_Hotspots.pdf cluster map; harmonized Stage 7 output",
        "Fig07-C":"results/figures/Fig07_Community_Typology_and_Hotspots.pdf hotspot map; harmonized Stage 7 output",
        "FigS05-A":"results/figures/FigS05_GA_Reproducibility.pdf; frozen GA history files",
        "FigS05-B":"results/figures/FigS05_GA_Reproducibility.pdf; frozen five-seed summary",
        "FigS05-C":"results/figures/FigS05_GA_Reproducibility.pdf; frozen incumbent identity",
    }
    panel_sources={
        "Fig01-A":[ROOT/"config"/"parent_frozen_design"/"FINAL_EXPERIMENT_MATRIX.json",ROOT/"FINAL_REVISION_RUN_SEQUENCE"/"FINAL_REVISION_RUN_MATRIX.json",ROOT/"src"/"la_grid"/"revision"/"r1_source_gate.py"],
        "Fig02-A":[FIGURES/"Fig02_System_Network_and_Mapping.pdf"],
        "Fig02-B":[FIGURES/"Fig02_System_Network_and_Mapping.pdf",ROOT/"Data"/"substation_graph_CEC_edges.csv"],
        "Fig02-C":[FIGURES/"Fig02_System_Network_and_Mapping.pdf",ROOT/"Data"/"tract_to_substation_mapping_CEC_expanded.csv"],
        "Fig02-D":[ROOT/"provenance"/"reviewer_working"/"R1_Comment1_2_External_Evidence_20260922"/"SCE_MAPPING_BENCHMARK_SUMMARY.csv",ROOT/"provenance"/"reviewer_working"/"R1_Comment1_2_External_Evidence_20260922"/"SCE_MAPPING_BENCHMARK_TRACTS.csv"],
        "Fig03-A":[STAGE/"Stage 1 Output_expanded"/f"MC_Device_Damage_AvgDS_{h}.csv" for h in HAZARDS],
        "Fig03-B":[STAGE/"Stage 1 Output_expanded"/"S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv"],
        "Fig03-C":[STAGE/"Stage 3 Output_expanded"/"LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv"],
        "Fig03-D-left":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet"],
        "Fig03-D-right":[STAGE/"Stage 1 Output_expanded"/"S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv",*shapefile_sources()],
        "Fig04-A":[STAGE/"Stage 6 Output_expanded"/"ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv"],
        "Fig04-B1":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig04-B2":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig04-B3":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig04-B4":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig05-A":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig05-B":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig05-C":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig05-D":[EQUITY/"VULNERABILITY_TRACT_EFFECTS.parquet",*shapefile_sources()],
        "Fig06-A":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig06-B":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig06-C":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig06-D":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig07-A":[STAGE7/"clusters_labels_final.csv",STAGE7/"stage7_cluster_profiles_raw_values.csv",ROOT/"src"/"la_grid"/"plotting"/"Project_Visualizer.py"],
        "Fig07-B":[STAGE7/"clusters_labels_final.csv",STAGE7/"stage7_full_domain_tract_status.csv",STAGE7/"stage7_typology_noneligible_tracts.csv",*shapefile_sources()],
        "Fig07-C":[STAGE7/"stage7_full_domain_tract_status.csv",*shapefile_sources()],
        **{f"FigS05-A": [FORMAL/"Stage 5 Output_expanded"/f"GA_HISTORY_2pc50_{seed}.csv" for seed in range(42,47)]},
        "FigS05-B":[FORMAL/"Stage 5 Output_expanded"/"GA_FIVE_SEED_CONVERGENCE.csv"],
        "FigS05-C":[FORMAL/"Stage 5 Output_expanded"/"INCUMBENT_DIRECT_SCORES_2PC50.csv"],
    }
    for panel_id,files in panel_sources.items():
        missing=[str(f) for f in files if not f.exists()]
        if missing: raise FileNotFoundError(f"Panel {panel_id} source missing: {missing}")
    panel_df["previous_figure_or_location"]=panel_df.panel_id.map(prior).fillna("No direct prior panel; new frozen-result presentation")
    panel_df["source_paths"]=panel_df.panel_id.map(lambda k:"; ".join(rel(x) for x in panel_sources[k]))
    panel_df.to_csv(OUT/"FIGURE_V2_PANEL_CROSSWALK.csv",index=False)
    source_rows=[]
    for stem,paths in source_map().items():
        for p in paths:
            if not p.exists(): raise FileNotFoundError(p)
            source_rows.append({"figure":stem,"source_path":rel(p),"sha256":sha256(p),"bytes":p.stat().st_size,"role":"frozen source authority"})
    pd.DataFrame(source_rows).drop_duplicates().to_csv(OUT/"FIGURE_V2_SOURCE_HASHES.csv",index=False)

    matrix = """# Story-evidence matrix - candidate v2\n\nThis is an evidence map for author review, not a final Main/Supplement decision. Candidate v2 is derived only from frozen accepted results. Existing `results/figures/` remains unchanged.\n\n| Evidence topic | Current evidence location | Candidate-v2 evidence | Main candidate direct evidence | Existing/supporting supplement evidence | Duplication or omission note |\n|---|---|---|---|---|---|\n| System representation | Fig02 A-B; retained graph inputs | Fig02 A-B | Yes, Fig02 A-B | Existing network criticality figures | Preserve July GIS/network content; current Fig02 was tall |\n| Tract dependency / mapping validation | Fig02 C; FigS06; SCE benchmark CSV | Fig02 C-D | Yes, dependency and 337 public-site match | FigS06 mapping/cutoff robustness | Map count is not validation; 342 and 337 sets differ |\n| Hazard damage | FigS01; Stage 1 damage tables | Fig03 A | Yes | Full hazard damage maps remain supporting | Box summarizes station means, not realization uncertainty; historical-vs-2pc50 differences also reflect different adopted fragility parameter sets |\n| Initial service | FigS02; frozen tract initial-service table | Fig03 B | Yes, four-hazard tract ECDF | Four-hazard maps remain FigS02 source | ECDF is across tract means |\n| Local / threshold / source-path loss | FigS04; loss decomposition tables | Fig03 C | Yes, four-hazard integrated decomposition | Dynamic route details remain FigS04/FigS07 sources | Dynamic time-varying mechanism is not in the main candidate; see gap audit below |\n| Unconstrained recovery | Fig03 current; Stage 3 outputs | Fig03 D | Yes | Historical-hazard T80 remains in source suite | Population T80 distribution and mean tract T80 are distinct |\n| Full eight-policy recovery | Current Fig04; recovery curve CSV | Fig04 A-B | Yes, all eight plus Unconstrained | Full strategy results by hazard remain tables/source suite | No strategy omitted; direct-community duplicate not separately plotted |\n| Aggregate burden | Current Fig04 B | Fig04 B and Fig05 B | Yes | Full hazard/resource tables retained | Fig04/Fig05 no longer duplicate hospital burden panels |\n| T80 | Current Fig04 D; formal parquet | Fig04 B, Fig03 D | Yes | All strategy/hazard distributions remain source tables | No imputation for unreached outcomes |\n| Hospital-linked burden | Current Fig04 C and Fig05 B | Fig04 B once | Yes, once with the same 5-95 range convention | Existing Hospital-priority construction candidate may remain a review reference | Meaning is tract service burden, not hospital supply/clinical capacity |\n| Q1-Q4 absolute burden | Current Fig06 A; formal and equity parquets | Fig05 A | Yes, four explicit policy contrasts | Full policies/hazards in frozen tables | Degree-first is added to absolute comparison |\n| Signed / absolute Q4-Q1 | Current Fig06 B/C; frozen metrics | Fig05 C | Yes, matched changes vs three references | Full Q1-Q4 result tables remain supporting | Signed and absolute separation are shown as different metrics |\n| Population-weighted Gini | Current Fig06 C | Fig05 C (separately scaled with ticks) | Yes | Full result tables retained | Not treated as the sole equity measure |\n| Tract paired effects | Current Fig06 D; VULNERABILITY_TRACT_EFFECTS.parquet | Fig05 D | Yes, continuous mean map for VF-Hospital | Full tract effect table retained | Mean sign is not significance nor per-run affected-population mean |\n| Resource dependence | Current FigS08/Sensitivity files | Fig06 A-D | Yes, C29 vs C57 for four policies and four outcomes | Other C86/C114 and duration cases remain frozen source suite | 2pc50 D1 comparison only; no universal direction claim |\n| GA reproducibility | Current FigS05 and Stage 5 logs/manifests | FigS05 A-C | Supporting candidate | Five-seed archive and manifest | Clarifies convergence/incumbent evidence; not a global-optimum claim |\n| Mapping / gate robustness | Current FigS06 and sensitivity tables | Not redrawn in Fig01-Fig07 | No | Existing FigS06 and frozen robustness tables | Must remain in supporting evidence chain |\n| Source redundancy | Current FigS07 | Not redrawn in main candidates | No | Existing FigS07 and source diagnostics | Reachability reliability is not delivered MW |\n| Capacity sensitivity | Current FigS08 and capacity closure outputs | Not redrawn in main candidates | No | Existing FigS08 and closure tables | 19 bounded stations, not full 92-station adequacy |\n| Stage 7 typology / hotspots | Current Fig07/FigS09 and harmonized outputs | Fig07 A-C | Yes | FigS09 remains source diagnostic | Cluster profile, cluster map and screening map are separate measures |\n| Cross-hazard strategy effects | Current tables/source suite | Strategy context in Fig03 only | Not fully | Frozen 4-hazard strategy summaries | `STORY_EVIDENCE_GAP` for claims that policy effects/rankings remain consistent across hazards, resources, and durations; do not generalize 2pc50 Fig04-Fig06 |\n| Logistics / repair duration | Current FigS03 and Stage 4 files | Not main | No | Existing crew/travel and duration/resource results | Bases/travel are inputs; response result is Fig06 |\n\n## Explicit claim-scope audit\n\nNo `STORY_EVIDENCE_GAP` remains for the three core questions when claims are scoped to the panels and scenarios shown below. A broader claim that strategy effects or rankings are consistent across all four hazards, crew counts, and duration cases would be a `STORY_EVIDENCE_GAP` in these main candidates: the frozen results exist in `PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet`, but must be cited in a table or separately reviewed supporting figure rather than inferred from 2pc50 panels. Similarly, Fig02-D is public-site agreement only, not feeder ground truth or validation of the full service model.\n\n## Core-question coverage audit\n\n| Core question | Direct candidate evidence | Current supporting evidence | Status |\n|---|---|---|---|\n| 1. How do hazard and network dependency produce tract service disruption? | Fig02 B-C; Fig03 A-C; Fig03 D baseline | FigS02 initial maps; FigS04 dynamic topology/source-loss diagnostics; FigS07 source reliability | Directly supported at the integrated-outcome scale; dynamic path timing is in supporting FigS04/FigS07, so Fig03 C alone should not be read as time-resolved restoration evidence. |\n| 2. Under logistics/resource constraints, how do priorities change overall and critical-service recovery? | Fig04 A-B; Fig06 A-D | Existing crew/travel inputs and full resource/duration tables | Directly supported for 2pc50, 57 crews and the 29-vs-57 crew D1 contrast. `STORY_EVIDENCE_GAP` for generalization across all hazards/resource/duration combinations; those results need a supporting table or additional reviewed figure. |\n| 3. How are burdens redistributed across vulnerability groups and places? | Fig05 A-D; Fig06 B-C; Fig07 A-C descriptive context | Existing complete tract and quartile tables; FigS09 diagnostics | Directly supported for the shown 2pc50 comparisons; no single scalar fairness claim is made. |\n"""
    (OUT/"STORY_EVIDENCE_MATRIX.md").write_text(matrix,encoding="utf-8")
    caps="# Figure v2 draft captions\n\nThese are synchronized draft captions for author review; no final figure selection is implied.\n\n"
    for stem,cap in CAPTIONS.items(): caps+=f"## {stem}\n\n{cap}\n\n"
    (OUT/"FIGURE_V2_CAPTIONS.md").write_text(caps,encoding="utf-8")
    readme="""# Candidate v2 review set\n\nThis is a presentation-only draft set for author review. It does not replace or edit `results/figures/`. No analysis, simulation, scheduling, GA search, or clustering was run.\n\nThe seven process-chain figure candidates and the GA reproducibility candidate are generated from the frozen sources listed in `FIGURE_V2_PANEL_CROSSWALK.csv` and `FIGURE_V2_SOURCE_HASHES.csv`. PDF is the vector-oriented candidate, PNG is a 600-dpi review/render copy, and `_preview.png` is the 150-dpi 185-mm page-width preview. `FIGURE_V2_REVIEW_PACKET.pdf` alternates each full-size figure with its caption/source page.\n\nRead `STORY_EVIDENCE_MATRIX.md` before interpreting coverage. Candidate numbering is temporary and does not imply Main/Supplement selection.\n"""
    (OUT/"README.md").write_text(readme,encoding="utf-8")


def make_packet():
    stems=list(CAPTIONS.keys())
    packet=fitz.open()
    for stem in stems:
        source=fitz.open(OUT/f"{stem}.pdf")
        packet.insert_pdf(source)
        source.close()
        page=packet.new_page(width=W_MM/25.4*72,height=340/25.4*72)
        margin=30
        page.insert_text((margin,32),stem.replace("_"," "),fontsize=14,fontname="hebo",color=(.15,.2,.23))
        page.insert_text((margin,52),"Draft caption and frozen-source trace",fontsize=10,fontname="hebo",color=(.31,.36,.39))
        cap=CAPTIONS[stem]
        rect=fitz.Rect(margin,68,page.rect.width-margin,290)
        result=page.insert_textbox(rect,cap,fontsize=9.5,fontname="helv",lineheight=1.23,color=(.12,.14,.15),align=0)
        if result<0: raise ValueError(f"Caption overflow on packet page for {stem}: {result}")
        y=310
        page.insert_text((margin,y),"Panel source authorities:",fontsize=9,fontname="hebo",color=(.15,.2,.23))
        srcs=source_map()[stem]
        source_text="\n".join(f"- {rel(p)}  |  SHA-256 {sha256(p)}" for p in srcs)
        result=page.insert_textbox(fitz.Rect(margin,y+7,page.rect.width-margin,page.rect.height-24),source_text,
                                   fontsize=6.4,fontname="cour",lineheight=1.15,color=(.25,.27,.28))
        if result<0: raise ValueError(f"Source list overflow on packet page for {stem}: {result}")
    out=OUT/"FIGURE_V2_REVIEW_PACKET.pdf"
    packet.set_metadata({"title":"LA Grid Figure Review Packet - Candidate v2","author":"Frozen-results figure review candidate"})
    packet.save(out,garbage=4,deflate=True)
    packet.close()


def make_contact_sheet():
    stems=list(CAPTIONS.keys())
    thumbs=[]
    for stem in stems:
        im=Image.open(OUT/f"{stem}_preview.png").convert("RGB")
        im.thumbnail((740,880),Image.Resampling.LANCZOS)
        canvas=Image.new("RGB",(780,940),"white")
        canvas.paste(im,((780-im.width)//2,36))
        draw=ImageDraw.Draw(canvas)
        draw.text((20,10),stem.replace("_"," "),fill="#24333b")
        thumbs.append(canvas)
    sheet=Image.new("RGB",(1560,940*math.ceil(len(thumbs)/2)),"#e5e8e9")
    for i,im in enumerate(thumbs): sheet.paste(im,((i%2)*780,(i//2)*940))
    sheet.save(OUT/"FIGURE_V2_ORDER_CONTACT_SHEET.png",dpi=(150,150))


def make_pdf_render_contact():
    """Contact sheet rendered from current PDF pages, separate from the full-size packet."""
    stems=list(CAPTIONS)
    thumbs=[]
    for stem in stems:
        with fitz.open(OUT/f"{stem}.pdf") as doc:
            pix=doc[0].get_pixmap(matrix=fitz.Matrix(1.0,1.0),alpha=False)
            im=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
        im.thumbnail((740,880),Image.Resampling.LANCZOS)
        canvas=Image.new("RGB",(780,940),"white")
        canvas.paste(im,((780-im.width)//2,36))
        draw=ImageDraw.Draw(canvas)
        draw.text((20,10),stem.replace("_"," "),fill="#24333b")
        thumbs.append(canvas)
    sheet=Image.new("RGB",(1560,940*math.ceil(len(thumbs)/2)),"#e5e8e9")
    for i,im in enumerate(thumbs): sheet.paste(im,((i%2)*780,(i//2)*940))
    sheet.save(OUT/"FIGURE_V2_PDF_RENDER_CONTACT.png",dpi=(150,150))


def write_index_and_qa():
    rows=[]
    pdfs=list(CAPTIONS)
    for stem in pdfs:
        rows.append({"figure":stem,"pdf":f"{stem}.pdf","png_600dpi":f"{stem}.png","page_width_preview":f"{stem}_preview.png",
                     "caption":CAPTIONS[stem],"role":"main-figure candidate" if stem.startswith("Fig0") else "GA reproducibility supporting candidate",
                     "source_authority":"; ".join(rel(p) for p in source_map()[stem])})
    pd.DataFrame(rows).to_csv(OUT/"FIGURE_V2_INDEX.csv",index=False)
    qa=[]
    for stem in pdfs+["FIGURE_V2_REVIEW_PACKET"]:
        p=OUT/f"{stem}.pdf";doc=fitz.open(p)
        if stem!="FIGURE_V2_REVIEW_PACKET":
            page=doc[0]; spans=[]
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    for sp in line.get("spans",[]):
                        if sp.get("text","").strip():spans.append(sp)
            minpt=min([x["size"] for x in spans],default=np.nan)
            fonts=sorted({x.get("font","") for x in spans})
            image_dpi=[]
            for image_info in page.get_image_info(xrefs=True):
                bbox=image_info.get("bbox")
                if bbox and bbox[2]>bbox[0] and bbox[3]>bbox[1]:
                    image_dpi.append(min(image_info["width"]*72/(bbox[2]-bbox[0]),image_info["height"]*72/(bbox[3]-bbox[1])))
            qa.append({"file":p.name,"page_count":len(doc),"width_mm":page.rect.width/72*25.4,"height_mm":page.rect.height/72*25.4,
                       "min_extracted_text_pt":minpt,"font_names":";".join(fonts),"embedded_image_count":len(image_dpi),
                       "minimum_embedded_image_dpi":min(image_dpi) if image_dpi else np.nan,
                       "vector_pdf":"native vector text/charts; embedded raster panels measured separately"})
            png=OUT/f"{stem}.png";im=Image.open(png)
            qa[-1]["png_width_px"]=im.width;qa[-1]["png_height_px"]=im.height;qa[-1]["png_effective_dpi_x"]=im.width/(W_MM/25.4)
        else: qa.append({"file":p.name,"page_count":len(doc),"width_mm":np.nan,"height_mm":np.nan,"min_extracted_text_pt":np.nan,"font_names":"packet typography","vector_pdf":"figure pages are inserted at original physical dimensions"})
        doc.close()
    pd.DataFrame(qa).to_csv(OUT/"FIGURE_V2_RENDER_QA.csv",index=False)
    # Machine-readable input identity and this renderer identity.
    identity={"base_head":"d5ec162e17de49747a065f4bc0111e77181a14e5","renderer":rel(Path(__file__)),"renderer_sha256":sha256(Path(__file__)),
              "operation":"presentation-only figures from frozen outputs","results_figures_modified":False,
              "scientific_computation_rerun":False,"candidate_outputs":pdfs+["FIGURE_V2_REVIEW_PACKET"]}
    (OUT/"FIGURE_V2_IDENTITY.json").write_text(json.dumps(identity,indent=2),encoding="utf-8")


def main():
    if not OUT.exists(): OUT.mkdir(parents=True)
    eval_data=read_eval()
    tracts=map_domain()
    outputs=[]
    outputs.append(build_fig01())
    outputs.append(build_fig02())
    outputs.append(build_fig03(eval_data))
    outputs.append(build_fig04(eval_data))
    outputs.append(build_fig05(eval_data,tracts))
    outputs.append(build_fig06(eval_data))
    outputs.append(build_fig07())
    outputs.append(build_figs05())
    write_crosswalk_and_matrix()
    make_packet()
    make_contact_sheet()
    make_pdf_render_contact()
    write_index_and_qa()
    print("Generated PDF candidates:",len(outputs)+1)
    print("Outputs:")
    for p in outputs: print(p[0].name,p[0].stat().st_size,p[1].stat().st_size,p[2].stat().st_size)
    print((OUT/"FIGURE_V2_REVIEW_PACKET.pdf").name,(OUT/"FIGURE_V2_REVIEW_PACKET.pdf").stat().st_size)
    print("Story matrix:",OUT/"STORY_EVIDENCE_MATRIX.md")


if __name__ == "__main__":
    main()
