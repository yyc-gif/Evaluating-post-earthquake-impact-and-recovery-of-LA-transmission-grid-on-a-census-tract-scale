"""Presentation-only candidate v2.1 from accepted frozen LA-grid outputs.

This renderer never writes to results/figures and never samples, schedules,
optimizes, simulates damage/recovery, or reclusters. It creates review-only
figure candidates under this directory from already accepted authorities.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE_PATH = ROOT / "results" / "figure_review" / "candidate_v2" / "build_candidate_v2.py"
SPEC = importlib.util.spec_from_file_location("la_grid_candidate_v2_base", BASE_PATH)
base = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(base)
base.OUT = OUT

FORMAL = ROOT / "Formal_Experiment_20260923"
EQUITY = FORMAL / "Equity_Amendment"
STAGE = ROOT / "results" / "revised_suite" / "LA_Grid_Revised_Suite_20260925"
STAGE7 = FORMAL / "Stage 7 Output_SOVI_Harmonized"
FIGURES = ROOT / "results" / "figures"
MAPPING_AUDIT = ROOT / "provenance" / "reviewer_working" / "R1_Comment1_July92_Utility_Constraint" / "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv"
BENCHMARK = STAGE / "Stage 2 Output_expanded" / "SCE_PUBLIC_CANDIDATE_BENCHMARK.csv"
STRATEGY_ORDER = list(base.STRATEGY_ORDER)
SCHEDULED = [x for x in STRATEGY_ORDER if x != "unconstrained"]
FIXED_POLICIES = [x for x in SCHEDULED if x != "vulnerability-first"]
POLICY_LABEL = dict(base.LABEL)
STYLE = dict(base.STYLE)
CORE_POLICIES = set(base.POLICIES_4)
HAZARDS = list(base.HAZARDS)
HAZARD_LABEL = dict(base.HAZARD_LABEL)
W_MM = 185.0
DPI = 600
PREVIEW_DPI = 150

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
    out_pdf = OUT / f"{stem}.pdf"
    out_png = OUT / f"{stem}.png"
    out_preview = OUT / f"{stem}_preview.png"
    metadata = {"Title": stem.replace("_", " "), "Author": "Frozen-results figure review candidate v2.1"}
    fig.savefig(out_pdf, format="pdf", dpi=DPI, metadata=metadata, facecolor="white")
    fig.savefig(out_png, format="png", dpi=DPI, facecolor="white")
    fig.savefig(out_preview, format="png", dpi=PREVIEW_DPI, facecolor="white")
    plt.close(fig)
    return out_pdf, out_png, out_preview


def fig_mm(height: float):
    return plt.figure(figsize=(W_MM / 25.4, height / 25.4), facecolor="white")


def panel_title(ax, letter: str, text: str):
    ax.set_title(f"{letter}. {text}", loc="left", fontweight="bold", pad=4.5)


def load_full_frozen_summary():
    formal = pd.read_parquet(FORMAL / "Formal_Results" / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
    vuln = pd.read_parquet(EQUITY / "VULNERABILITY_PRIMARY_SUMMARY.parquet")
    full = pd.concat([formal, vuln], ignore_index=True)
    full = full[full.mapping.eq("M1_UTILITY_003") & full.gate.eq("G1_BASELINE_050")].copy()
    return full


def get_cluster_palette():
    # Parse the authority constant so Fig07 and FigS09 cannot drift apart.
    source = ROOT / "src" / "la_grid" / "plotting" / "Project_Visualizer.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "STAGE7_IJDRR_CLUSTER_PALETTE" for t in node.targets):
            return list(ast.literal_eval(node.value)), source
    raise KeyError("STAGE7_IJDRR_CLUSTER_PALETTE not found in plotting authority")


def build_fig02():
    # Preserve the already accepted July physical-system and retained-network panels.
    source_pdf = FIGURES / "Fig02_System_Network_and_Mapping.pdf"
    crop_a = base.image_crop_from_pdf(source_pdf, (123, 18, 433, 219))
    crop_b = base.image_crop_from_pdf(source_pdf, (123, 268, 433, 474))
    sensitivity = pd.read_csv(MAPPING_AUDIT, dtype={"tract_id": str})
    if len(sensitivity) != 2315 or sensitivity.tract_id.nunique() != 2315:
        raise ValueError("Frozen utility-domain/mapping-shift table must cover 2,315 unique tracts")
    benchmark = pd.read_csv(BENCHMARK)
    benchmark = benchmark[(benchmark.version == "NEW_20260922") & (benchmark.candidate_kind == "direct_site")]
    if set(benchmark.mapping) != {"JULY_BASELINE_92", "JULY_UTILITY_CONSTRAINED_92"} or not (benchmark.tract_count == 337).all():
        raise ValueError("The displayed direct-site comparison must be the frozen 337-tract set")
    fig = fig_mm(174)
    gs = fig.add_gridspec(2, 2, left=.045, right=.965, top=.955, bottom=.13,
                          wspace=.12, hspace=.24, height_ratios=[1, 1])
    axa = fig.add_subplot(gs[0, 0]); axb = fig.add_subplot(gs[0, 1])
    axa.imshow(crop_a); axb.imshow(crop_b)
    for ax in (axa, axb): ax.axis("off")
    panel_title(axa, "A", "Physical GIS network")
    panel_title(axb, "B", "Simplified retained topology")
    handles_a = [
        Line2D([0], [0], color="#999999", lw=1, ls="--", label="CEC transmission lines"),
        Line2D([0], [0], color="#3f8dbf", lw=1.2, label="Direct substation links"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#f05a28", markeredgecolor="white", markersize=5, label="Retained grid stations"),
    ]
    handles_b = [
        Line2D([0], [0], color="#666666", lw=1, label="CEC transmission lines"),
        Line2D([0], [0], color="#7fb6dc", lw=1.2, label="Simplified topology"),
        Line2D([0], [0], marker="x", color="#f05a28", lw=0, markersize=5, label="CEC substations"),
    ]
    axa.legend(handles=handles_a, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(.5, -.04), fontsize=7.0)
    axb.legend(handles=handles_b, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(.5, -.04), fontsize=7.0)

    # C depicts the frozen utility-domain eligibility rule directly.
    axc = fig.add_subplot(gs[1, 0]); panel_title(axc, "C", "Utility candidate-eligibility domains")
    geo = base.map_domain()
    geo["tract_id"] = geo.tract_id.astype(str).str.zfill(11)
    # The source shapefile includes more county tracts than the retained study
    # domain; the frozen sensitivity table defines the exact 2,315-tract map.
    gm = base.projected_map_data(geo.merge(sensitivity, on="tract_id", how="inner", validate="one_to_one"))
    if len(gm) != 2315 or gm.utility_domain.isna().any():
        raise ValueError("Utility eligibility map must cover exactly 2,315 retained tracts")
    domain_counts = gm.utility_domain.value_counts()
    domain_colors = {"SCE": "#8f789f", "LADWP": "#6f9db3", "other / ambiguous": "#d8dcde"}
    for domain, color in domain_colors.items():
        gm[gm.utility_domain.eq(domain)].plot(ax=axc, color=color, linewidth=.035, edgecolor="#f4f4f4")
    base.style_map_axis(axc)
    domain_handles = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor=domain_colors["SCE"], markersize=5,
               label=f"SCE (n={int(domain_counts.get('SCE', 0))})"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=domain_colors["LADWP"], markersize=5,
               label=f"LADWP (n={int(domain_counts.get('LADWP', 0))})"),
        Line2D([0], [0], marker="s", color="none", markerfacecolor=domain_colors["other / ambiguous"], markersize=5,
               label=f"Other/ambiguous; general pool (n={int(domain_counts.get('other / ambiguous', 0))})"),
    ]
    axc.legend(handles=domain_handles, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(.50, -.14),
               fontsize=7.0, labelspacing=.25, handletextpad=.35, columnspacing=.8)

    # D is public-site agreement, not accuracy or feeder validation.
    axd = fig.add_subplot(gs[1, 1]); panel_title(axd, "D", "Public-site agreement (337 comparable tracts)")
    metrics = [("Any candidate", "any_match"), ("Top-1 candidate", "top1"), ("Top-3 candidates", "top3")]
    yy = np.arange(len(metrics)); offsets = [-.13, .13]
    colors = {"JULY_BASELINE_92": "#8d989f", "JULY_UTILITY_CONSTRAINED_92": "#386f8e"}
    names = {"JULY_BASELINE_92": "Distance-based baseline", "JULY_UTILITY_CONSTRAINED_92": "Utility-compatible"}
    for off, mapping in zip(offsets, ["JULY_BASELINE_92", "JULY_UTILITY_CONSTRAINED_92"]):
        row = benchmark[benchmark.mapping.eq(mapping)].iloc[0]
        vals = [100 * float(row[c]) for _, c in metrics]
        axd.scatter(vals, yy + off, s=23, color=colors[mapping], label=names[mapping], zorder=3)
        for xv, yv in zip(vals, yy + off):
            axd.text(xv + .22, yv, f"{xv:.1f}%", va="center", fontsize=7.0, color=colors[mapping])
    axd.set_yticks(yy, [x[0] for x in metrics]); axd.invert_yaxis(); axd.set_ylim(2.55, -.55)
    axd.set_xlim(80, 101); axd.set_xticks([80, 85, 90, 95, 100])
    axd.set_xlabel("Agreement with public-site evidence (%)")
    axd.grid(axis="x", alpha=.2)
    axd.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(.5, -.21),
               fontsize=7.0, columnspacing=.9, handletextpad=.35)
    return save_figure(fig, "Fig02_System_Network_Mapping_and_Public_Site_Check")


def build_fig03(eval_data):
    damage_dir = STAGE / "Stage 1 Output_expanded"
    init_t80_path = damage_dir / "S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv"
    init_t80 = pd.read_csv(init_t80_path)
    decomp = pd.read_csv(STAGE / "Stage 3 Output_expanded" / "LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv")
    decomp = decomp[(decomp.resource_scenario == "C57_D1") & (decomp.strategy_id == "unconstrained")]
    if set(decomp.hazard) != set(HAZARDS) or len(decomp) != 4:
        raise ValueError("Frozen Unconstrained decomposition must include one row for each of four hazards")
    service = init_t80[init_t80.hazard.isin(HAZARDS)].copy()
    geoms = base.map_domain()
    if service[service.hazard.eq("2pc50")].tract_id.astype(str).nunique() != 2315:
        raise ValueError("Expected 2,315 tracts in frozen initial-service/T80 table")
    fig = fig_mm(216)
    gs = fig.add_gridspec(3, 2, left=.13, right=.965, top=.96, bottom=.07,
                          hspace=.50, wspace=.28, height_ratios=[.9, .92, 1.25])
    axa = fig.add_subplot(gs[0, 0]); panel_title(axa, "A", "Mean station damage state")
    ds = [pd.read_csv(damage_dir / f"MC_Device_Damage_AvgDS_{h}.csv").avg_damage_state.to_numpy() for h in HAZARDS]
    bp = axa.boxplot(ds, patch_artist=True, showfliers=False, whis=(5, 95), widths=.56)
    hazard_colors = {"LongBeach": "#6f8fa6", "SanFernando": "#4c9278", "Northridge": "#9a7559", "2pc50": "#a65628"}
    for box, h in zip(bp["boxes"], HAZARDS): box.set_facecolor(hazard_colors[h]); box.set_alpha(.68)
    for key in ("medians", "whiskers", "caps"):
        for item in bp[key]: item.set_color("#34424a"); item.set_linewidth(.65)
    axa.set_xticks(np.arange(1, 5), [HAZARD_LABEL[h] for h in HAZARDS], rotation=15, ha="right")
    axa.set_ylabel("Station mean damage state (DS0–DS4)"); axa.grid(axis="y", alpha=.2)

    axb = fig.add_subplot(gs[0, 1]); panel_title(axb, "B", "Initial tract-service distributions")
    for h in HAZARDS:
        vals = np.sort(service.loc[service.hazard.eq(h), "mean_initial_service_proxy"].dropna().to_numpy())
        if len(vals): axb.plot(vals, np.arange(1, len(vals) + 1) / len(vals), color=hazard_colors[h], lw=1.2, label=HAZARD_LABEL[h])
    axb.set_xlim(0, 1); axb.set_ylim(0, 1); axb.set_xlabel("Mean initial modeled tract service"); axb.set_ylabel("Cumulative share of tracts")
    axb.grid(alpha=.18); axb.legend(frameon=False, loc="lower right", ncol=2, fontsize=7.0)

    # C is explicitly Unconstrained, matching the policy-independent baseline chain.
    axc = fig.add_subplot(gs[1, :]); panel_title(axc, "C", "Unconstrained service-loss decomposition")
    d = decomp.set_index("hazard").loc[HAZARDS].reset_index()
    y = np.arange(len(HAZARDS)); left = np.zeros(len(HAZARDS))
    parts = [("Local physical damage", "self_mean_hr", "#68757d"),
             ("Functionality threshold", "threshold_mean_hr", "#8fb8c9"),
             ("Loss of source path", "source_mean_hr", "#d17b3f")]
    for label, col, color in parts:
        vals = d[col].to_numpy(float)
        axc.barh(y, vals, left=left, height=.57, color=color, label=label, edgecolor="white", linewidth=.4)
        left += vals
    shares = d.source_fraction_of_mean_total.to_numpy(float) * 100
    for i, (total, share) in enumerate(zip(left, shares)):
        axc.text(total + .15, i, f"source-path {share:.1f}%", va="center", fontsize=7.1)
    axc.set_yticks(y, [HAZARD_LABEL[h] for h in HAZARDS]); axc.invert_yaxis()
    axc.set_xlabel("Population-weighted modeled service burden (h)")
    axc.grid(axis="x", alpha=.18); axc.set_axisbelow(True); axc.set_xlim(0, float(left.max()) + 7.0)
    axc.legend(frameon=False, loc="upper right", ncol=3, fontsize=7.0)

    axd = fig.add_subplot(gs[2, 0]); panel_title(axd, "D", "Unconstrained population T80")
    u = eval_data[eval_data.resource_scenario.eq("C57_D1") & eval_data.strategy_id.eq("unconstrained")]
    vals = pd.to_numeric(u.population_T80_hr, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if len(vals) != 1000: raise ValueError(f"Expected 1,000 finite Unconstrained population T80 values; found {len(vals)}")
    axd.hist(vals, bins=26, color="#7897ad", edgecolor="white", linewidth=.45)
    med = float(np.median(vals)); axd.axvline(med, color="#273d4b", ls="--", lw=1.0, label=f"Median {med:.1f} h")
    axd.set_xlabel("Population-weighted time to 80% service (h)"); axd.set_ylabel("Realizations (n)")
    axd.legend(frameon=False, fontsize=7.0); axd.grid(axis="y", alpha=.18)
    map_ax = fig.add_subplot(gs[2, 1])
    tract = init_t80[init_t80.hazard.eq("2pc50")].copy(); tract["tract_id"] = tract.tract_id.astype(str).str.zfill(11)
    gm = base.projected_map_data(geoms.merge(tract, on="tract_id", how="inner"))
    mvals = gm.mean_T80_hr_when_reached.replace([np.inf, -np.inf], np.nan)
    vmin, vmax = float(mvals.min()), float(mvals.max())
    gm.plot(column="mean_T80_hr_when_reached", ax=map_ax, cmap="YlGnBu", vmin=vmin, vmax=vmax,
            linewidth=.05, edgecolor="#f5f5f5", missing_kwds={"color": "#eeeeee"})
    base.style_map_axis(map_ax)
    map_ax.text(0, 1.02, "Mean tract T80 when reached", transform=map_ax.transAxes, ha="left", va="bottom", fontsize=8.0, weight="bold")
    cax = map_ax.inset_axes([.20, -.06, .62, .035])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=mcolors.Normalize(vmin, vmax), cmap="YlGnBu"), cax=cax, orientation="horizontal")
    cb.set_label("Mean tract T80 (h)", fontsize=7.0, labelpad=1); cb.ax.tick_params(labelsize=7.0, length=2)
    return save_figure(fig, "Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline")


def build_fig05(eval_data, tracts):
    base_data = eval_data[eval_data.resource_scenario.eq("C57_D1") & eval_data.strategy_id.isin(STRATEGY_ORDER)].copy()
    if len(base_data[base_data.strategy_id.eq("vulnerability-first")]) != 1000:
        raise ValueError("Frozen Vulnerability-first C57_D1 summary is incomplete")
    fig = fig_mm(218)
    gs = fig.add_gridspec(4, 1, left=.205, right=.975, top=.91, bottom=.065,
                          hspace=.39, height_ratios=[.68, .68, 1.12, 1.35])
    axa = fig.add_subplot(gs[0, 0]); panel_title(axa, "A", "Absolute burden by vulnerability quartile")
    x = np.arange(1, 5)
    for key in base.POLICIES_4:
        means=[]; low=[]; high=[]
        for _, col in base.QUARTILE_COLS.items():
            m, p5, p95, _ = base.summary_5_95(base_data.loc[base_data.strategy_id.eq(key), col])
            means.append(m); low.append(p5); high.append(p95)
        color, ls = STYLE[key]
        axa.errorbar(x, means, yerr=[np.array(means)-np.array(low), np.array(high)-np.array(means)],
                     color=color, ls=ls, marker="o", ms=3.2, lw=1.1, capsize=2,
                     label=POLICY_LABEL[key], alpha=.95)
    axa.set_xticks(x, ["Q1 lowest", "Q2", "Q3", "Q4 highest"])
    axa.set_ylabel("Quartile burden (h)"); axa.grid(axis="y", alpha=.18)
    policy_handles=[Line2D([0],[0],color=STYLE[k][0],lw=1.1,ls=STYLE[k][1],marker="o",ms=3,label=POLICY_LABEL[k]) for k in base.POLICIES_4]
    fig.legend(handles=policy_handles,frameon=False,ncol=4,loc="upper center",bbox_to_anchor=(.57,.99),fontsize=7.0,columnspacing=1.0)

    bgs = gs[1, 0].subgridspec(1, 2, width_ratios=[4.3, 1.4], wspace=.08)
    axb = fig.add_subplot(bgs[0, 0]); panel_title(axb, "B", "Mean aggregate and Q4 burdens by policy")
    legend_ax = fig.add_subplot(bgs[0, 1]); legend_ax.axis("off")
    legend_handles=[]
    for key in STRATEGY_ORDER:
        sub = base_data[base_data.strategy_id.eq(key)]
        if sub.empty: continue
        mx=float(sub.population_weighted_normalized_burden_hr.mean()); my=float(sub.burden_Q4_hr.mean()); color, _ = STYLE[key]
        axb.scatter(mx, my, s=27, color=color, edgecolor="white", linewidth=.45, zorder=3)
        legend_handles.append(Line2D([0], [0], marker="o", color=color, lw=0, markersize=5, label=POLICY_LABEL[key]))
    axb.set_xlabel("Population-weighted service burden (h)"); axb.set_ylabel("Q4 burden (h)")
    axb.grid(alpha=.18)
    legend_ax.legend(handles=legend_handles, frameon=False, ncol=1, loc="center left", fontsize=7.0, labelspacing=.55)

    cgs = gs[2, 0].subgridspec(3, 2, height_ratios=[.17, .18, 1], width_ratios=[5, 1.25], hspace=.01, wspace=.14)
    ctitle_ax=fig.add_subplot(cgs[0, :]); ctitle_ax.axis("off")
    ctitle_ax.text(0, .15, "C. Vulnerability-first change relative to matched policies", transform=ctitle_ax.transAxes,
                   ha="left", va="bottom", fontsize=9.0, fontweight="bold")
    ref_legend_ax=fig.add_subplot(cgs[1, :]); ref_legend_ax.axis("off")
    axc=fig.add_subplot(cgs[2, 0])
    refs=["impact-first", "hospital-first", "degree-first"]
    refcol={r: STYLE[r][0] for r in refs}
    metrics=[
        ("population_weighted_normalized_burden_hr", "Population burden (h)"),
        ("burden_Q4_hr", "Q4 service burden (h)"),
        ("signed_Q4_minus_Q1_hr", "Signed Q4–Q1 gap (h)"),
        ("absolute_Q4_minus_Q1_hr", "Absolute Q4–Q1 gap (h)"),
        ("hospital_mean_normalized_burden_hr", "Hospital-linked burden (h)"),
    ]
    vf=base_data[base_data.strategy_id.eq("vulnerability-first")]
    offsets={"impact-first":-.18, "hospital-first":0, "degree-first":.18}
    for i, (metric, lab) in enumerate(metrics):
        for ref in refs:
            rr=base_data[base_data.strategy_id.eq(ref)][["realization_id", metric]].rename(columns={metric:"reference"})
            vv=vf[["realization_id", metric]].rename(columns={metric:"candidate"})
            joined=vv.merge(rr, on="realization_id", validate="one_to_one")
            delta=joined.candidate-joined.reference
            m,p5,p95,n=base.summary_5_95(delta); yy=i+offsets[ref]
            axc.errorbar(m, yy, xerr=[[max(0,m-p5)],[max(0,p95-m)]], fmt="o", color=refcol[ref], ecolor=refcol[ref],
                         ms=3.1, elinewidth=.75, capsize=1.7)
    axc.axvline(0, color="#333333", lw=.55, ls="--", zorder=0)
    axc.set_yticks(np.arange(len(metrics)), [m[1] for m in metrics]); axc.invert_yaxis()
    axc.set_xlabel("Change (h)"); axc.grid(axis="x", alpha=.18); axc.set_ylim(len(metrics)-.5, -.5)
    handles=[Line2D([0],[0],marker="o",color=refcol[r],lw=0,label=POLICY_LABEL[r]) for r in refs]
    ref_legend_ax.legend(handles=handles, frameon=False, ncol=3, loc="center left", fontsize=7.0, columnspacing=1.2)
    axg=fig.add_subplot(cgs[2, 1]); axg.set_title("Gini change", loc="left", fontsize=7.6, fontweight="bold", pad=5.5)
    for i, ref in enumerate(refs):
        rr=base_data[base_data.strategy_id.eq(ref)][["realization_id","burden_gini"]].rename(columns={"burden_gini":"reference"})
        vv=vf[["realization_id","burden_gini"]].rename(columns={"burden_gini":"candidate"})
        z=vv.merge(rr,on="realization_id",validate="one_to_one"); delta=z.candidate-z.reference
        m,p5,p95,n=base.summary_5_95(delta)
        axg.errorbar(m,i,xerr=[[max(0,m-p5)],[max(0,p95-m)]],fmt="o",color=refcol[ref],ecolor=refcol[ref],ms=3.1,elinewidth=.75,capsize=1.7)
    axg.axvline(0,color="#333333",lw=.55,ls="--"); axg.set_yticks(range(3),["Impact", "Hospital", "Degree"])
    axg.set_xlabel("Change (unitless)"); axg.grid(axis="x",alpha=.18); axg.set_ylim(2.5,-.75)

    dgs=gs[3,0].subgridspec(1,2,width_ratios=[5.0,1.0],wspace=.02)
    axd=fig.add_subplot(dgs[0,0]); panel_title(axd,"D","Mean tract burden change: Vulnerability-first − Impact-first")
    cax_holder=fig.add_subplot(dgs[0,1]); cax_holder.axis("off")
    tract_effect_path=EQUITY/"VULNERABILITY_TRACT_EFFECTS.parquet"
    te=pd.read_parquet(tract_effect_path)
    te=te[(te.hazard.eq("2pc50"))&(te.reference_strategy.eq("impact-first"))].copy()
    te["tract_id"]=te.tract_id.astype(str).str.zfill(11)
    geo=tracts[tracts.tract_id.isin(te.tract_id)].copy()
    gm=base.projected_map_data(geo.merge(te[["tract_id","mean_paired_delta_burden_hr","population"]],on="tract_id",how="inner",validate="one_to_one"))
    if gm.tract_id.nunique()!=2315: raise ValueError("Tract-effect map must cover all 2,315 tracts")
    vals=gm.mean_paired_delta_burden_hr.dropna().to_numpy(); lim=max(float(np.nanmax(np.abs(vals))) if len(vals) else 0,.25)
    norm=mcolors.TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim)
    gm.plot(column="mean_paired_delta_burden_hr",ax=axd,cmap="RdBu_r",norm=norm,linewidth=.045,edgecolor="#f2f2f2",
            missing_kwds={"color":"#eeeeee"})
    base.style_map_axis(axd)
    cax=cax_holder.inset_axes([.24,.18,.18,.64])
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap="RdBu_r"),cax=cax)
    cb.set_label("Mean change (h)",fontsize=7.0,labelpad=3); cb.ax.tick_params(labelsize=7.0,length=2)
    return save_figure(fig,"Fig05_Distributional_Outcomes_and_Reference_Sensitivity")


def build_fig06(eval_data):
    d=eval_data[eval_data.resource_scenario.isin(["C29_D1","C57_D1"]) & eval_data.strategy_id.isin(base.POLICIES_4)].copy()
    counts=d.groupby(["resource_scenario","strategy_id"]).realization_id.nunique()
    if counts.min()!=1000 or len(counts)!=8:
        raise ValueError("C29/C57 frozen comparison must include four policies and 1,000 realizations each")
    metrics=[("population_weighted_normalized_burden_hr","Population-weighted service burden (h)"),
             ("burden_Q4_hr","Highest-vulnerability quartile burden (h)"),
             ("absolute_Q4_minus_Q1_hr","Absolute high–low vulnerability burden difference (h)"),
             ("hospital_mean_normalized_burden_hr","Hospital-linked tract service burden (h)")]
    fig=fig_mm(169); gs=fig.add_gridspec(2,2,left=.12,right=.98,top=.86,bottom=.13,hspace=.47,wspace=.3)
    scenarios=["C29_D1","C57_D1"]; offsets=np.linspace(-.24,.24,len(base.POLICIES_4))
    for j,(metric,lab) in enumerate(metrics):
        ax=fig.add_subplot(gs[j//2,j%2]); panel_title(ax,"ABCD"[j],lab)
        for k,key in enumerate(base.POLICIES_4):
            color,_=STYLE[key]
            for si,scenario in enumerate(scenarios):
                vals=d[(d.resource_scenario.eq(scenario))&(d.strategy_id.eq(key))][metric]
                mean,p5,p95,n=base.summary_5_95(vals); xx=si+offsets[k]
                ax.errorbar(xx,mean,yerr=[[max(0,mean-p5)],[max(0,p95-mean)]],fmt="o",ms=3.3,color=color,
                            ecolor=color,elinewidth=.75,capsize=1.7,alpha=.96)
        ax.set_xticks([0,1],["29 crews", "57 crews"]); ax.set_ylabel(lab); ax.grid(axis="y",alpha=.18); ax.set_xlim(-.5,1.5)
    handles=[Line2D([0],[0],marker="o",color=STYLE[k][0],lw=0,label=POLICY_LABEL[k]) for k in base.POLICIES_4]
    fig.suptitle("Two-level crew-resource contrast under 2pc50 (D1)",fontsize=10.0,fontweight="bold",y=.985)
    fig.legend(handles=handles,frameon=False,ncol=4,loc="upper center",bbox_to_anchor=(.55,.935),fontsize=7.0,columnspacing=1.15,handletextpad=.4)
    fig.text(.13,.055,"Dots = means; whiskers = 5th–95th realization range (n=1,000 per policy and crew case). Only the frozen 29- and 57-crew cases are compared.",fontsize=7.0)
    return save_figure(fig,"Fig06_Two_Level_Crew_Resource_Contrast")


def build_fig07():
    labels_path=STAGE7/"clusters_labels_final.csv"; status_path=STAGE7/"stage7_full_domain_tract_status.csv"
    profiles_path=STAGE7/"stage7_cluster_profiles_raw_values.csv"
    labels=pd.read_csv(labels_path); labels=labels[labels.scenario.eq("2pc50")].copy(); labels["tract_id"]=labels.tract_id.astype(str).str.zfill(11)
    status=pd.read_csv(status_path); status=status[status.scenario.eq("2pc50")].copy(); status["tract_id"]=status.tract_id.astype(str).str.zfill(11)
    if len(status)!=2315 or labels.tract_id.nunique()!=2291: raise ValueError("Stage 7 2,315/2,291 membership identity changed")
    palette, _ = get_cluster_palette(); color_by={str(i+1):palette[i] for i in range(5)}
    features=["T80","Pre_1970_Ratio","Pop_Density","NRI_RISK_SCORE","NRI_BUILDVALUE","SOVI_SCORE"]
    merged=labels[["tract_id","cluster",*features]].copy(); means=merged.groupby("cluster")[features].mean().sort_index()
    z=(means-means.mean(axis=0))/means.std(axis=0,ddof=1).replace(0,1)
    pretty=["Tract T80","Pre-1970 housing ratio","Population density","NRI risk score","NRI building value","NRI social vulnerability"]
    geo=base.projected_map_data(base.map_domain().merge(status,on="tract_id",how="inner"))
    fig=fig_mm(188); gs=fig.add_gridspec(2,2,left=.19,right=.96,top=.94,bottom=.17,hspace=.32,wspace=.12,height_ratios=[.95,1.25])
    axa=fig.add_subplot(gs[0,:]); panel_title(axa,"A","Residential typology profiles")
    im=axa.imshow(z[features].T.to_numpy(),cmap="coolwarm",norm=mcolors.TwoSlopeNorm(vmin=-2,vcenter=0,vmax=2),aspect="auto")
    ncl=merged.groupby("cluster").size().reindex(range(1,6)); axa.set_xticks(np.arange(5),[f"C{i} (n={int(ncl.loc[i])})" for i in range(1,6)])
    axa.set_yticks(np.arange(len(features)),pretty); axa.tick_params(axis="both",labelsize=7.0)
    cb=fig.colorbar(im,ax=axa,orientation="vertical",fraction=.022,pad=.015); cb.set_label("Z-score across five cluster means",fontsize=7.0); cb.ax.tick_params(labelsize=7.0)
    axa.set_ylim(5.5,-.5)
    axb=fig.add_subplot(gs[1,0]); panel_title(axb,"B","Residential typology geography")
    geo["cluster_key"]=geo.cluster.map(lambda x:str(int(x)) if pd.notna(x) else "N/A")
    for key,color in color_by.items(): geo[geo.cluster_key.eq(key)].plot(ax=axb,color=color,edgecolor="white",linewidth=.07)
    geo[geo.cluster_key.eq("N/A")].plot(ax=axb,color="#eeeeee",edgecolor="#777777",linewidth=.16,hatch="///")
    base.style_map_axis(axb)
    handles=[Line2D([0],[0],marker="s",lw=0,color="none",markerfacecolor=color,markeredgecolor="none",label=f"Cluster {k}") for k,color in color_by.items()]
    handles.append(Line2D([0],[0],marker="s",lw=0,color="none",markerfacecolor="#eeeeee",markeredgecolor="#777777",label="Outside typology (n=24)"))
    fig.legend(handles=handles,frameon=False,ncol=3,loc="lower center",bbox_to_anchor=(.50,.055),fontsize=7.0,columnspacing=1.1)
    axc=fig.add_subplot(gs[1,1]); panel_title(axc,"C","Slow-vulnerable hotspot screening")
    geo.plot(column="SlowVulnerable_Hotspot_Score",ax=axc,cmap="Blues",linewidth=.05,edgecolor="#f3f3f3",
             missing_kwds={"color":"#eeeeee","edgecolor":"#888888","hatch":"///"})
    base.style_map_axis(axc); hvals=geo.SlowVulnerable_Hotspot_Score.dropna()
    cax=axc.inset_axes([.91,.15,.025,.65]); cb=fig.colorbar(plt.cm.ScalarMappable(norm=mcolors.Normalize(float(hvals.min()),float(hvals.max())),cmap="Blues"),cax=cax)
    cb.set_label("Combined screening score",fontsize=7.0,labelpad=3); cb.ax.tick_params(labelsize=7.0)
    return save_figure(fig,"Fig07_Community_Typology_and_Hotspots")


def build_figs05():
    ga_dir=FORMAL/"Stage 5 Output_expanded"
    conv=pd.read_csv(ga_dir/"GA_FIVE_SEED_CONVERGENCE.csv").sort_values("seed")
    seeds=sorted(conv.seed.astype(int).unique())
    if len(seeds)!=5: raise ValueError("Expected five frozen GA seeds")
    histories=[pd.read_csv(ga_dir/f"GA_HISTORY_2pc50_{seed}.csv") for seed in seeds]
    incumbent=pd.read_csv(ga_dir/"INCUMBENT_DIRECT_SCORES_2pc50.csv")
    incumbent_value=float(conv.incumbent_fitness.iloc[0])
    if not np.allclose(conv.incumbent_fitness,incumbent_value) or conv.search_improved_incumbent.astype(bool).any():
        raise ValueError("Frozen five-seed incumbent status changed; inspect source before plotting")
    fig=fig_mm(148); gs=fig.add_gridspec(2,2,left=.14,right=.97,top=.93,bottom=.20,hspace=.42,wspace=.32)
    ax=fig.add_subplot(gs[:,0]); panel_title(ax,"A","Generation-mean candidate objective")
    seed_colors=["#1b6b83","#537f68","#a65628","#6b5b95","#8c6d31"]
    for seed,h,color in zip(seeds,histories,seed_colors):
        ax.plot(h.generation,h.generation_mean,color=color,lw=.85,alpha=.82,label=f"Seed {seed} mean")
    ax.axhline(incumbent_value,color="#171717",lw=1.1,ls="--",label="Impact-first incumbent")
    ax.set_xlabel("Generation"); ax.set_ylabel("Planning objective (frozen fitness scale)")
    ax.grid(alpha=.18)
    line_handles,line_labels=ax.get_legend_handles_labels()
    fig.legend(line_handles,line_labels,frameon=False,ncol=3,loc="lower center",bbox_to_anchor=(.31,.035),
               fontsize=7.0,columnspacing=.7,handletextpad=.35,labelspacing=.35)
    axb=fig.add_subplot(gs[0,1]); panel_title(axb,"B","Best candidate by seed vs incumbent")
    y=np.arange(len(conv))
    best=[]
    for seed,h in zip(seeds,histories): best.append(float(h.generation_best.max()))
    axb.scatter(best,y,c=seed_colors,s=28,zorder=3)
    axb.axvline(incumbent_value,color="#171717",lw=1.0,ls="--")
    axb.set_yticks(y,[f"Seed {s}" for s in conv.seed]); axb.invert_yaxis(); axb.set_xlabel("Best generation candidate objective")
    axb.grid(axis="x",alpha=.18)
    for yi,v in zip(y,best): axb.text(v-.018,yi,f"{v:.2f}",ha="right",va="center",fontsize=7.0)
    axc=fig.add_subplot(gs[1,1]); panel_title(axc,"C","Retained sequence identity")
    axc.axis("off")
    text=("Retained: Impact-first\n"
          "No seed beat the incumbent.\n"
          "Direct-community = same sequence.\n"
          "Finite search does not prove global optimality.")
    axc.text(.04,.82,text,transform=axc.transAxes,ha="left",va="top",fontsize=7.0,linespacing=1.4,
             bbox={"boxstyle":"round,pad=.5","facecolor":"#f4f6f7","edgecolor":"#c4cbd0","linewidth":.6})
    return save_figure(fig,"FigS05_GA_Reproducibility")


def build_figs09():
    labels=pd.read_csv(STAGE7/"clusters_labels_final.csv"); labels=labels[labels.scenario.eq("2pc50")].copy()
    if labels.tract_id.nunique()!=2291: raise ValueError("Frozen Stage 7 PCA scatter must cover 2,291 typology tracts")
    palette, _ = get_cluster_palette(); colors={int(i+1):palette[i] for i in range(5)}
    stats=pd.read_csv(STAGE7/"pca_stats_with_eigenvalues.csv")
    load=pd.read_csv(STAGE7/"pca_loadings.csv",index_col=0)
    kdiag=pd.read_csv(STAGE7/"kmeans_k_diagnostics.csv")
    fig=fig_mm(174); gs=fig.add_gridspec(2,2,left=.17,right=.94,top=.92,bottom=.12,hspace=.38,wspace=.48)
    axa=fig.add_subplot(gs[0,0]); panel_title(axa,"A","PCA scores by final cluster")
    for cid,color in colors.items():
        sub=labels[labels.cluster.eq(cid)]
        axa.scatter(sub.PC1,sub.PC2,s=5.0,color=color,alpha=.55,linewidths=0,label=f"Cluster {cid}")
    axa.set_xlabel("PC1 score"); axa.set_ylabel("PC2 score"); axa.grid(alpha=.16); axa.legend(frameon=False,ncol=2,fontsize=7.0)
    axb=fig.add_subplot(gs[0,1]); panel_title(axb,"B","Explained variance by component")
    pcnum=np.arange(1,len(stats)+1); ratios=stats.Explained_Variance_Ratio.to_numpy(float)
    axb.plot(pcnum,ratios,marker="o",color="#386f8e",lw=1.1,ms=3.2)
    axb.set_xticks(pcnum,[str(i) for i in pcnum]); axb.set_ylabel("Explained variance ratio"); axb.set_xlabel("Principal component")
    axb.grid(axis="y",alpha=.18)
    axc=fig.add_subplot(gs[1,0]); panel_title(axc,"C","PCA feature loadings")
    mat=load.iloc[:,:5].to_numpy(float)
    im=axc.imshow(mat,cmap="coolwarm",norm=mcolors.TwoSlopeNorm(vmin=-1,vcenter=0,vmax=1),aspect="auto")
    feature_labels={"T80":"Tract T80","Init_Supply":"Initial service","Grid_Degree":"Network degree",
                    "Grid_Impact":"Network impact","Grid_Betweenness":"Network betweenness","Redundancy_HHI":"Dependency HHI",
                    "Pre_1970_Ratio":"Pre-1970 housing","Pop_Density":"Population density",
                    "NRI_RISK_SCORE":"NRI risk","NRI_BUILDVALUE":"NRI building value","SOVI_SCORE":"NRI social vulnerability"}
    load_labels=[]
    for x in load.index:
        key=str(x)
        if key.startswith("log1p(") and key.endswith(")"):
            key=key[6:-1]
        load_labels.append(feature_labels.get(key,key))
    axc.set_xticks(np.arange(5),[f"PC{i}" for i in range(1,6)]); axc.set_yticks(np.arange(len(load)),load_labels)
    axc.tick_params(labelsize=7.0); cb=fig.colorbar(im,ax=axc,fraction=.05,pad=.03); cb.ax.tick_params(labelsize=7.0)
    axd=fig.add_subplot(gs[1,1]); panel_title(axd,"D","K-means support diagnostics")
    axd.plot(kdiag.k,kdiag.inertia,marker="o",color="#465f6c",lw=1.0,ms=3,label="Within-cluster sum of squares")
    axd.set_xlabel("Number of clusters (k)"); axd.set_ylabel("Inertia"); axd.grid(axis="y",alpha=.18)
    axd2=axd.twinx(); axd2.plot(kdiag.k,kdiag.silhouette,marker="s",color="#a65628",lw=.9,ms=3,ls="--",label="Silhouette")
    axd2.set_ylabel(""); axd2.tick_params(labelsize=7.0)
    h1,l1=axd.get_legend_handles_labels();h2,l2=axd2.get_legend_handles_labels()
    axd.legend(h1+h2,l1+l2,frameon=False,fontsize=7.0,loc="upper right")
    return save_figure(fig,"FigS09_Stage7_Diagnostics")


def paired_policy_effects(full):
    metrics={
        "population_weighted_normalized_burden_hr": "Population-weighted service burden (h)",
        "burden_Q4_hr": "Highest-vulnerability quartile burden (h)",
        "population_T80_hr": "Population T80 (h)",
        "hospital_mean_normalized_burden_hr": "Hospital-linked tract service burden (h)",
        "L_source_population_mass_weighted_hr": "Source-path-related burden (h)",
        "absolute_Q4_minus_Q1_hr": "Absolute high–low vulnerability burden difference (h)",
        "burden_gini": "Population-weighted Gini (unitless)",
    }
    rows=[]
    for hazard in HAZARDS:
        case=full[(full.hazard.eq(hazard)) & full.resource_scenario.eq("C57_D1")]
        ref=case[case.strategy_id.eq("unconstrained")]
        if ref.realization_id.nunique()!=1000: raise ValueError(f"Unconstrained baseline incomplete for {hazard}")
        for strategy in SCHEDULED:
            candidate=case[case.strategy_id.eq(strategy)]
            if candidate.realization_id.nunique()!=1000: raise ValueError(f"Frozen {strategy} results incomplete for {hazard}")
            merged=candidate.merge(ref,on="realization_id",suffixes=("_candidate","_reference"),validate="one_to_one")
            for metric,label in metrics.items():
                a=pd.to_numeric(merged[f"{metric}_candidate"],errors="coerce")
                b=pd.to_numeric(merged[f"{metric}_reference"],errors="coerce")
                delta=(a-b).replace([np.inf,-np.inf],np.nan).dropna()
                rows.append({"hazard":hazard,"strategy_id":strategy,"strategy_label":POLICY_LABEL[strategy],
                             "reference":"Unconstrained","metric":metric,"metric_label":label,
                             "n_paired":int(delta.shape[0]),"mean_paired_difference":float(delta.mean()) if len(delta) else np.nan,
                             "p05_paired_difference":float(delta.quantile(.05)) if len(delta) else np.nan,
                             "p95_paired_difference":float(delta.quantile(.95)) if len(delta) else np.nan,
                             "interval_definition":"5th–95th range of paired realization differences; not a confidence interval"})
    return pd.DataFrame(rows)


def build_cross_hazard(full, effects):
    metrics=[("population_weighted_normalized_burden_hr","Population-weighted burden (h)"),
             ("population_T80_hr","Population T80 (h)"),
             ("burden_Q4_hr","Highest-vulnerability quartile burden (h)"),
             ("hospital_mean_normalized_burden_hr","Hospital-linked tract burden (h)")]
    policies=SCHEDULED
    fig=fig_mm(214); gs=fig.add_gridspec(2,2,left=.205,right=.93,top=.91,bottom=.18,hspace=.38,wspace=.34)
    summary=effects.copy()
    for j,(metric,label) in enumerate(metrics):
        short_titles=["Population burden − Unconstrained","Population T80 − Unconstrained","Q4 burden − Unconstrained","Hospital burden − Unconstrained"]
        ax=fig.add_subplot(gs[j//2,j%2]); panel_title(ax,"ABCD"[j],short_titles[j])
        subset=summary[summary.metric.eq(metric)]
        matrix=np.full((len(policies),len(HAZARDS)),np.nan)
        for iy,policy in enumerate(policies):
            for ix,hazard in enumerate(HAZARDS):
                q=subset[(subset.strategy_id.eq(policy))&(subset.hazard.eq(hazard))]
                if not q.empty: matrix[iy,ix]=float(q.mean_paired_difference.iloc[0])
        finite=matrix[np.isfinite(matrix)]
        limit=max(float(np.max(np.abs(finite))) if finite.size else 1,.01)
        cmap=plt.get_cmap("RdBu_r").copy(); cmap.set_bad("#e4e6e7")
        norm=mcolors.TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit)
        im=ax.imshow(np.ma.masked_invalid(matrix),cmap=cmap,norm=norm,aspect="auto")
        ax.set_xticks(np.arange(4),[HAZARD_LABEL[h] for h in HAZARDS],rotation=15,ha="right")
        if j % 2 == 0:
            ax.set_yticks(np.arange(len(policies)),[POLICY_LABEL[p] for p in policies]); ax.set_ylabel("Scheduled policy")
        else:
            ax.set_yticks(np.arange(len(policies)),[""]*len(policies)); ax.tick_params(axis="y",length=0); ax.set_ylabel("")
        ax.tick_params(axis="both",labelsize=7.0)
        for iy in range(len(policies)):
            for ix in range(len(HAZARDS)):
                val=matrix[iy,ix]
                text="NA" if not np.isfinite(val) else f"{val:+.2f}"
                ax.text(ix,iy,text,ha="center",va="center",fontsize=7.0,color="#15232a")
        cb=fig.colorbar(im,ax=ax,fraction=.046,pad=.03); cb.set_label("Paired mean difference (h)",fontsize=7.0); cb.ax.tick_params(labelsize=7.0)
        if j % 2 == 0:
            ax.set_ylabel("Scheduled policy")
        else:
            ax.set_ylabel("")
        if j >= 2:
            ax.set_xlabel("Hazard scenario")
        else:
            ax.set_xlabel("")
    fig.text(.12,.045,"Cells show within-hazard mean paired differences from Unconstrained; source CSV records paired 5th–95th ranges.\nHistorical and 2pc50 fragility parameterizations differ; these are not pure PGA sensitivities.",fontsize=7.0,linespacing=1.15)
    return save_figure(fig,"Candidate_Supplement_Cross_Hazard_Policy_Robustness")


def build_discrete_case_figure(eval_data, case_kind: str):
    if case_kind=="crew":
        scenarios=["C29_D1","C57_D1","C86_D1","C114_D1"]
        labels=["29","57","86","114"]
        xlab="Crew condition (D1 held fixed; discrete cases)"
        stem="Candidate_Supplement_Crew_Resource_Contrasts"
        title_text="Frozen crew-resource cases under 2pc50"
    else:
        scenarios=["C57_D075","C57_D1","C57_D125","C57_D150"]
        labels=["0.75×","1×","1.25×","1.50×"]
        xlab="Repair-duration multiplier (C57 held fixed; discrete cases)"
        stem="Candidate_Supplement_Repair_Duration_Contrasts"
        title_text="Frozen repair-duration cases under 2pc50"
    metrics=[("population_weighted_normalized_burden_hr","Population-weighted service burden (h)"),
             ("burden_Q4_hr","Highest-vulnerability quartile burden (h)"),
             ("absolute_Q4_minus_Q1_hr","Absolute high–low vulnerability burden difference (h)"),
             ("hospital_mean_normalized_burden_hr","Hospital-linked tract service burden (h)")]
    d=eval_data[eval_data.resource_scenario.isin(scenarios)&eval_data.strategy_id.isin(SCHEDULED)].copy()
    counts=d.groupby(["resource_scenario","strategy_id"]).realization_id.nunique()
    if len(counts)!=len(scenarios)*len(SCHEDULED) or counts.min()!=1000:
        raise ValueError(f"Incomplete frozen {case_kind} cases: expected {len(scenarios)} x {len(SCHEDULED)} x 1,000")
    fig=fig_mm(190); gs=fig.add_gridspec(2,2,left=.12,right=.98,top=.83,bottom=.13,hspace=.42,wspace=.30)
    offsets=np.linspace(-.30,.30,len(SCHEDULED))
    for j,(metric,lab) in enumerate(metrics):
        ax=fig.add_subplot(gs[j//2,j%2]); panel_title(ax,"ABCD"[j],lab)
        for k,key in enumerate(SCHEDULED):
            color,_=STYLE[key]; alpha=.98 if key in CORE_POLICIES else .5
            for ix,(scenario,xlabel) in enumerate(zip(scenarios,labels)):
                vals=d[(d.resource_scenario.eq(scenario))&(d.strategy_id.eq(key))][metric]
                mean,p5,p95,n=base.summary_5_95(vals)
                ax.errorbar(ix+offsets[k],mean,yerr=[[max(0,mean-p5)],[max(0,p95-mean)]],fmt="o",ms=2.8,
                            color=color,ecolor=color,elinewidth=.65,capsize=1.4,alpha=alpha)
        ax.set_xticks(range(len(labels)),labels); ax.set_xlabel(xlab,fontsize=7.2); ax.set_ylabel(lab,fontsize=7.8)
        ax.grid(axis="y",alpha=.18); ax.set_xlim(-.55,len(labels)-.45)
    handles=[Line2D([0],[0],marker="o",color=STYLE[k][0],lw=0,markersize=4,label=POLICY_LABEL[k],alpha=.98 if k in CORE_POLICIES else .6) for k in SCHEDULED]
    fig.suptitle(title_text,fontsize=10.0,fontweight="bold",y=.985)
    fig.legend(handles=handles,frameon=False,ncol=4,loc="upper center",bbox_to_anchor=(.54,.94),fontsize=7.0,columnspacing=1.0,handletextpad=.4)
    fig.text(.12,.055,"Means and 5th–95th realization ranges (n=1,000); not confidence intervals. Discrete frozen scenarios only; no interpolation is implied.\nDirect-community is omitted because its sequence equals Impact-first.",fontsize=7.0,linespacing=1.15)
    return save_figure(fig,stem)


CAPTIONS={
"Fig01_Revised_Analytical_Framework":"Revised analytical framework. Fixed earthquake scenarios provide station-level PGA inputs for damage-state sampling. Modeled station service is combined with the production source-reachability gate and utility-compatible tract dependency. Frozen restoration policies operate on damaged tasks with realized durations, directed travel, and crew dispatch. Downstream evaluation reports recovery, burden, distributional outcomes, descriptive typology, and bounded robustness checks. The production source gate is a reachability representation; it does not model power flow, generation adequacy, capacity, or delivered MW.",
"Fig02_System_Network_Mapping_and_Public_Site_Check":"Study system, utility-compatible tract dependency, and public-site agreement. (A) Physical CEC network context and (B) the retained model graph (92 stations, 318 edges, 14 Core sources); both geographic source panels are preserved from the existing authority. (C) Frozen utility-domain eligibility for all 2,315 study tracts: SCE (817) and LADWP (848) domains use utility-matched candidate pools; other/ambiguous tracts (650) retain the July general candidate pool. The separate M0-to-revised dependency-weight shift remains in the mapping-robustness evidence. (D) Any-, top-1-, and top-3-candidate agreement with public-site evidence for the 337 directly comparable tracts contrasts the distance-based general-pool baseline with revised utility-compatible eligibility. The 337-row direct-site set differs from the earlier 342-tract crosswalk (316 shared; 26 old-only and 21 current-only); denominators are not pooled. Public-site agreement is supporting evidence, not accuracy, feeder validation, or service-territory ground truth.",
"Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline":"Hazard context and Unconstrained baseline chain. (A) Distribution across 92 stations of station-specific mean damage state, each mean derived from 1,000 frozen realizations; boxes summarize station heterogeneity, not Monte Carlo uncertainty. (B) Empirical tract distribution of mean initial modeled service for each hazard. (C) Unconstrained integrated burden decomposition into local physical damage, functionality-threshold loss, and source-path loss; all component values use the accepted C57_D1 summary row for the no-scheduling Unconstrained reference and the common 0–480 h integral. This is not a restoration-policy comparison. (D, left) 2pc50 population-weighted T80 across 1,000 Unconstrained realizations; unreached outcomes are not assigned the 480 h horizon. (D, right) Mean tract T80 among reached tracts; unreached/missing values remain gray. Historical hazards and 2pc50 use different adopted fragility parameter sets, so cross-hazard differences are not pure PGA sensitivity.",
"Fig04_All_Policy_Recovery_and_Outcomes":"Recovery and outcomes for all eight distinct scheduled policies plus the Unconstrained reference under 2pc50, C57_D1. Panel A displays mean population service availability over 0–120 h; panels B summarize outcomes integrated/evaluated over the full 0–480 h horizon. Dots are realization means and whiskers show the 5th–95th realization range (n=1,000), not confidence intervals. Impact-first, Degree-first, Hospital-first, and Vulnerability-first receive stronger visual emphasis; Centrality-first, Betweenness-first, Closeness-first, and Random remain displayed as lower-emphasis comparators. Unconstrained is the black reference. Direct-community is omitted because its frozen sequence is the same as Impact-first. Source-path-related burden is a modeled loss component, not delivered electricity.",
"Fig05_Distributional_Outcomes_and_Reference_Sensitivity":"Distributional outcomes and matched-reference sensitivity under 2pc50, C57_D1. (A) Absolute Q1–Q4 service burden for Impact-first, Hospital-first, Degree-first, and Vulnerability-first; whiskers are 5th–95th realization ranges, not confidence intervals. Q1 and Q4 denote the lowest- and highest-social-vulnerability quartiles. (B) Mean aggregate population-weighted service burden versus mean Q4 burden for all eight distinct scheduled policies and Unconstrained; points are summary estimates and no two-dimensional uncertainty is encoded in this panel. (C) For each physical realization, the Vulnerability-first outcome is differenced from Impact-first, Hospital-first, or Degree-first. Hour-valued outcomes use the labeled hour axis; population-weighted Gini change uses a separate unitless axis. Gini is 0 under equal tract burden and increases with inequality. Whiskers are 5th–95th paired-realization ranges. (D) Tract-level mean burden change, Vulnerability-first minus Impact-first, over the same physical realizations. Negative values indicate lower mean burden under Vulnerability-first; the map does not show statistical significance or the per-realization count of people helped.",
"Fig06_Two_Level_Crew_Resource_Contrast":"Two-level crew-resource contrast for 2pc50 with the frozen D1 repair-duration case. The figure compares the accepted 29-crew and 57-crew cases for Impact-first, Hospital-first, Degree-first, and Vulnerability-first on population-weighted service burden, highest-vulnerability-quartile burden, absolute high–low vulnerability burden difference, and hospital-linked tract service burden. Dots are means and whiskers are 5th–95th realization ranges (n=1,000 per policy/case), not confidence intervals. This is a comparison of two tested crew conditions, not a continuous response curve or a result for unshown resource levels.",
"Fig07_Community_Typology_and_Hotspots":"Harmonized Stage 7 community typology and hotspot screening for 2pc50. (A) Cluster means for selected variables expressed as z-scores across the five cluster means. (B) The residential typology includes 2,291 of 2,315 study tracts; the 24 tracts outside the residential typology are hatched gray and are not assigned a cluster. Cluster colors use the official Stage 7 cluster-ID palette, shared with FigS09. (C) The official combined slow-vulnerable score is a screening indicator, not a repair priority, intervention ranking, or independent causal validation.",
"FigS05_GA_Reproducibility":"Frozen five-seed Genetic Algorithm (GA) planning evidence for 2pc50. (A) Generation-mean candidate objective for each seed and the frozen Impact-first incumbent/best-so-far reference. Candidate means vary by generation; the best candidate attained by each seed does not exceed the incumbent. (B) Best generation candidate by seed compared with the incumbent; no seed improved it. (C) The retained sequence is Impact-first; Direct-community is sequence-equivalent, not an additional scheduled policy. This finite five-seed search does not establish global optimality and did not use evaluation realizations to choose a strategy.",
"FigS09_Stage7_Diagnostics":"Frozen Stage 7 support diagnostics for the harmonized 2pc50 residential typology. (A) PCA scores for 2,291 eligible tracts colored by the same official cluster-ID palette used in Fig07. (B) Explained variance by component. (C) Loadings in the accepted log1p-exposure, standardized feature space. (D) Frozen k-means inertia (left scale) and silhouette coefficient (right scale) across candidate cluster counts. These panels document dimensionality-reduction and clustering support; they do not turn clusters or hotspots into repair strategies.",
"Candidate_Supplement_Cross_Hazard_Policy_Robustness":"Cross-hazard policy contrasts from frozen accepted summaries. Each cell is the mean paired difference between one scheduled policy and the Unconstrained reference within the same hazard-specific 1,000 physical realizations; the source CSV records 5th–95th paired-realization ranges. Negative burden differences indicate lower burden relative to Unconstrained; negative T80 differences indicate earlier population recovery. Each panel has its own symmetric color scale centered at zero. The four hazard scenarios use different fragility parameter sets for historical hazards versus 2pc50, so the panels are scenario contrasts, not pure PGA sensitivity. Direct-community is omitted as Impact-first sequence-equivalent.",
"Candidate_Supplement_Crew_Resource_Contrasts":"Frozen discrete crew-count comparisons under 2pc50 and D1 for all eight distinct scheduled policies. Panels show population-weighted burden, highest-vulnerability-quartile burden, absolute high–low vulnerability burden difference, and hospital-linked tract service burden. Dots are realization means and whiskers are 5th–95th realization ranges (n=1,000 per policy/case), not confidence intervals. The tested categories are 29, 57, 86, and 114 crews; connecting values or trends between these categories are not inferred. Direct-community is omitted because its sequence equals Impact-first; Unconstrained has no scheduled crew case.",
"Candidate_Supplement_Repair_Duration_Contrasts":"Frozen discrete repair-duration comparisons under 2pc50 and C57 for all eight distinct scheduled policies. Panels show population-weighted burden, highest-vulnerability-quartile burden, absolute high–low vulnerability burden difference, and hospital-linked tract service burden. Dots are realization means and whiskers are 5th–95th realization ranges (n=1,000 per policy/case), not confidence intervals. The accepted tested multipliers are D0.75, D1, D1.25, and D1.50; categories are discrete scenarios and no interpolation is implied. Direct-community is omitted because its sequence equals Impact-first; Unconstrained has no scheduled repair-duration case.",
}


def all_sources():
    shape=base.shapefile_sources()
    project_visualizer=ROOT/"src"/"la_grid"/"plotting"/"Project_Visualizer.py"
    ga=FORMAL/"Stage 5 Output_expanded"
    return {
        "Fig01_Revised_Analytical_Framework":[ROOT/"config"/"parent_frozen_design"/"FINAL_EXPERIMENT_MATRIX.json",ROOT/"FINAL_REVISION_RUN_SEQUENCE"/"FINAL_REVISION_RUN_MATRIX.json",ROOT/"src"/"la_grid"/"revision"/"r1_source_gate.py"],
        "Fig02_System_Network_Mapping_and_Public_Site_Check":[FIGURES/"Fig02_System_Network_and_Mapping.pdf",ROOT/"Data"/"substation_graph_CEC_edges.csv",ROOT/"Data"/"substation_graph_CEC_edges_expanded.csv",ROOT/"Data"/"JULY_UTILITY_CONSTRAINED_92.csv",MAPPING_AUDIT,BENCHMARK,*shape],
        "Fig03_Hazard_Service_Loss_and_Unconstrained_Baseline":[STAGE/"Stage 1 Output_expanded"/"S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv",*[STAGE/"Stage 1 Output_expanded"/f"MC_Device_Damage_AvgDS_{h}.csv" for h in HAZARDS],STAGE/"Stage 3 Output_expanded"/"LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv",FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",*shape],
        "Fig04_All_Policy_Recovery_and_Outcomes":[STAGE/"Stage 6 Output_expanded"/"ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv",FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig05_Distributional_Outcomes_and_Reference_Sensitivity":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet",EQUITY/"VULNERABILITY_TRACT_EFFECTS.parquet",*shape],
        "Fig06_Two_Level_Crew_Resource_Contrast":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Fig07_Community_Typology_and_Hotspots":[STAGE7/"clusters_labels_final.csv",STAGE7/"stage7_cluster_profiles_raw_values.csv",STAGE7/"stage7_full_domain_tract_status.csv",STAGE7/"stage7_typology_noneligible_tracts.csv",project_visualizer,*shape],
        "FigS05_GA_Reproducibility":[ga/"GA_FIVE_SEED_CONVERGENCE.csv",*[ga/f"GA_HISTORY_2pc50_{s}.csv" for s in range(42,47)],ga/"INCUMBENT_DIRECT_SCORES_2pc50.csv"],
        "FigS09_Stage7_Diagnostics":[STAGE7/"clusters_labels_final.csv",STAGE7/"pca_stats_with_eigenvalues.csv",STAGE7/"pca_loadings.csv",STAGE7/"kmeans_k_diagnostics.csv",project_visualizer],
        "Candidate_Supplement_Cross_Hazard_Policy_Robustness":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Candidate_Supplement_Crew_Resource_Contrasts":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
        "Candidate_Supplement_Repair_Duration_Contrasts":[FORMAL/"Formal_Results"/"PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",EQUITY/"VULNERABILITY_PRIMARY_SUMMARY.parquet"],
    }


def write_metadata(effects):
    paths=all_sources()
    source_rows=[]
    for figure,items in paths.items():
        for p in items:
            if not p.exists(): raise FileNotFoundError(f"Frozen source missing for {figure}: {p}")
            source_rows.append({"figure":figure,"source_path":rel(p),"sha256":sha256(p),"bytes":p.stat().st_size,"source_role":"frozen accepted authority"})
    pd.DataFrame(source_rows).drop_duplicates().to_csv(OUT/"FIGURE_V2_1_SOURCE_HASHES.csv",index=False)

    index=[]
    for stem,caption in CAPTIONS.items():
        p=OUT/f"{stem}.pdf"
        role="Process-chain candidate" if stem.startswith("Fig0") else ("Stage 7 diagnostic candidate" if stem.startswith("FigS09") else ("GA evidence candidate" if stem.startswith("FigS05") else "Robustness evidence candidate"))
        index.append({"figure_stem":stem,"pdf":p.name,"png_600dpi":f"{stem}.png","185mm_preview":f"{stem}_preview.png",
                      "review_role":role,"promotion_status":"REVIEW ONLY; NOT PROMOTED","page_width_mm":W_MM,
                      "caption":caption,"source_authority":"; ".join(rel(x) for x in paths[stem])})
    pd.DataFrame(index).to_csv(OUT/"FIGURE_V2_1_INDEX.csv",index=False)

    qa=[]
    for stem in CAPTIONS:
        p=OUT/f"{stem}.pdf"
        with fitz.open(p) as doc:
            page=doc[0]; spans=[]
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    for sp in line.get("spans",[]):
                        if sp.get("text","").strip(): spans.append(sp)
            fonts=sorted({sp.get("font","") for sp in spans})
            dpi=[]
            for im in page.get_image_info(xrefs=True):
                box=im.get("bbox")
                if box and box[2]>box[0] and box[3]>box[1]: dpi.append(min(im["width"]*72/(box[2]-box[0]),im["height"]*72/(box[3]-box[1])))
            outside=sum(1 for sp in spans if sp["bbox"][0]<-0.5 or sp["bbox"][1]<-0.5 or sp["bbox"][2]>page.rect.width+.5 or sp["bbox"][3]>page.rect.height+.5)
            png=Image.open(OUT/f"{stem}.png")
            qa.append({"file":p.name,"page_count":len(doc),"width_mm":page.rect.width/72*25.4,"height_mm":page.rect.height/72*25.4,
                       "minimum_extractable_text_pt":min([sp["size"] for sp in spans],default=np.nan),"fonts":";".join(fonts),
                       "embedded_image_count":len(dpi),"min_embedded_image_dpi":min(dpi) if dpi else np.nan,
                       "text_outside_page_count":outside,"png_px_width":png.width,"png_px_height":png.height,
                       "review":"visual check still required; see packet/contact sheets"})
    pd.DataFrame(qa).to_csv(OUT/"FIGURE_V2_1_RENDER_QA.csv",index=False)
    effects.to_csv(OUT/"CROSS_HAZARD_POLICY_EFFECTS.csv",index=False)

    old=pd.read_csv(ROOT/"results"/"figure_review"/"candidate_v2"/"FIGURE_V2_PANEL_CROSSWALK.csv")
    changes={
        "Fig02-C":"Replaced station-count/weight-shift display with a direct map of the frozen utility-domain eligibility rule and domain counts; M0-to-revised weight-shift evidence remains in the mapping-robustness source.",
        "Fig02-D":"Retained 337 direct-site agreement definition; caption distinguishes it from the 342-tract crosswalk and prohibits accuracy/territory language.",
        "Fig03-C":"Changed reference from Hospital-first to Unconstrained using the existing accepted Unconstrained rows; Fig03 is now baseline-policy independent.",
        "Fig04-A":"Retained all eight scheduled policies plus black Unconstrained reference; four explanatory policies emphasized and four retained at lower visual weight.",
        "Fig04-B1":"All policy outcomes retain 5th–95th realization ranges; no confidence-interval encoding.",
        "Fig04-B2":"All policy outcomes retain 5th–95th realization ranges; 0–480 h evaluation kept distinct from 0–120 h curve display.",
        "Fig04-B3":"All policy outcomes retain 5th–95th realization ranges; 0–480 h evaluation kept distinct from 0–120 h curve display.",
        "Fig04-B4":"All policy outcomes retain 5th–95th realization ranges; source-path measure remains a loss component.",
        "Fig05-D":"Changed tract-map reference from Hospital-first to Impact-first using frozen paired-effect rows; gave the map more vertical space, removed in-map prose, and moved the color scale outside the map.",
        "Fig06-A":"Renamed the figure and title as a two-level C29/C57 contrast; no continuous response-curve claim.",
        "Fig06-B":"Renamed as a two-level C29/C57 contrast; all four frozen outcome metrics retained.",
        "Fig06-C":"Renamed as a two-level C29/C57 contrast; all four frozen outcome metrics retained.",
        "Fig06-D":"Renamed as a two-level C29/C57 contrast; all four frozen outcome metrics retained.",
        "Fig07-B":"Uses Stage 7 authority palette keyed directly by integer cluster ID; same explicit mapping is used in new FigS09.",
        "FigS05-A":"Replaced overlapping best-so-far-only display with the five frozen generation-mean candidate objective traces and incumbent reference.",
        "FigS05-B":"Shows each seed's best generation candidate against the same incumbent reference; no improvement is not global-optimality evidence.",
    }
    old["candidate_v2_1_panel_id"]=old.panel_id
    old["v2_1_change"]=old.panel_id.map(changes).fillna("Retained from v2 without scientific-result changes; same frozen metric, reference and source.")
    old.loc[old.panel_id.eq("Fig02-D"), "reference"] = "Distance-based general-pool baseline vs utility-compatible candidate eligibility"
    cidx=old.panel_id.eq("Fig02-C")
    old.loc[cidx,"theme"]="Utility candidate eligibility"
    old.loc[cidx,"scientific_question"]="Which tracts use utility-specific candidate pools in the revised mapping?"
    old.loc[cidx,"frozen_source"]="MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv"
    old.loc[cidx,"metric_definition"]="Categorical frozen utility_domain for each of the 2,315 retained tracts; domain counts are shown in the legend."
    old.loc[cidx,"reference"]="SCE/LADWP utility-matched candidate pools; July general pool for other/ambiguous tracts"
    old.loc[cidx,"interpretation_boundary"]="Shows the eligibility domains, not validation against feeder/service-territory ground truth; M0-to-revised weight shift remains a separate mapping-robustness result."
    old.loc[cidx,"previous_figure_or_location"]="v2 Fig02-C station-count map; v2.1 draft weight-shift map"
    old.loc[cidx,"source_paths"]="; ".join(rel(p) for p in [MAPPING_AUDIT,*base.shapefile_sources()])
    extra=[]
    def add(pid,theme,question,source,metric,reference,boundary,previous,action):
        extra.append({"panel_id":pid,"theme":theme,"scientific_question":question,"frozen_source":source,
                      "metric_definition":metric,"reference":reference,"interpretation_boundary":boundary,
                      "previous_figure_or_location":previous,"source_paths":"","candidate_v2_1_panel_id":pid,"v2_1_change":action})
    for letter,metric in zip("ABCD",["Population-weighted burden","Population T80","Q4 burden","Hospital-linked tract burden"]):
        add(f"CrossHazard-{letter}","Cross-hazard policy robustness",f"How does the frozen {metric.lower()} contrast vary by scenario?","PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet + VULNERABILITY_PRIMARY_SUMMARY.parquet",
            f"Mean within-hazard paired strategy-minus-Unconstrained difference; companion CSV records 5th–95th paired realization range", "Unconstrained within hazard",
            "Historical/current fragility parameter sets differ; not pure PGA sensitivity", "No prior candidate panel", "New frozen-summary presentation; eight strategies and all four hazards")
    for group,letters in [("Crew", "ABCD"),("Duration","ABCD")]:
        for letter,metric in zip(letters,["Population-weighted burden","Q4 burden","Absolute high–low burden difference","Hospital-linked tract burden"]):
            add(f"{group}-{letter}",f"Frozen {group.lower()} robustness",f"How does {metric.lower()} vary across discrete {group.lower()} scenarios?",
                "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet + VULNERABILITY_PRIMARY_SUMMARY.parquet",
                "Mean and 5th–95th realization range, n=1,000 per strategy/case", "2pc50; D1 for crew or C57 for duration",
                "Discrete frozen cases; no interpolation or factorial crew-duration interaction", "Formal frozen 2pc50 cases", "New presentation of existing cases; all eight distinct scheduled policies")
    for letter,topic in zip("ABCD",["PCA scores","Explained variance","PCA loadings","K-means inertia/silhouette"]):
        add(f"Stage7-{letter}","Stage 7 diagnostics",f"What frozen Stage 7 diagnostic supports the typology?","Stage 7 Output_SOVI_Harmonized CSV authorities",
            topic,"Harmonized 2pc50 Stage 7", "Descriptive dimensionality/clustering support; not a repair-policy ranking",
            "Existing Stage 7 diagnostic source figures", "New grouped diagnostic candidate; categorical colors keyed to official cluster ID")
    extra_df=pd.DataFrame(extra)
    extra_stem={"CrossHazard-":"Candidate_Supplement_Cross_Hazard_Policy_Robustness",
                "Crew-":"Candidate_Supplement_Crew_Resource_Contrasts",
                "Duration-":"Candidate_Supplement_Repair_Duration_Contrasts",
                "Stage7-":"FigS09_Stage7_Diagnostics"}
    for idx,row in extra_df.iterrows():
        stem=next(v for prefix,v in extra_stem.items() if row.panel_id.startswith(prefix))
        extra_df.loc[idx,"source_paths"]="; ".join(rel(p) for p in paths[stem])
    pd.concat([old,extra_df],ignore_index=True,sort=False).to_csv(OUT/"FIGURE_V2_1_PANEL_CROSSWALK.csv",index=False)

    matrix="""# Story-evidence matrix — candidate v2.1

This matrix locates accepted evidence for author review. It is not a manuscript figure selection, does not promote candidates, and does not alter `results/figures/`. Candidate v2 remains untouched.

| Evidence topic | Current frozen authority | v2.1 review location | Evidence status / boundary |
|---|---|---|---|
| System representation | CEC GIS panels; 92-node/318-edge graph; 14 Core sources | Fig02 A–B | Direct system representation; reachability is not electrical adequacy. |
| Utility eligibility and revised tract dependency | Frozen 2,315-tract utility-domain and mapping-shift crosswalks | Fig02 C shows SCE/LADWP/other eligibility domains and domain counts; existing mapping-robustness evidence shows M0-to-revised weight shifts | **Closed for the eligibility representation:** the main candidate now directly shows which candidate pool applies spatially. Neither panel validates feeder or service-territory truth. |
| Public mapping evidence | Frozen 337 direct-site agreement summary; earlier 342-tract crosswalk | Fig02 D | Direct-site agreement shown on 337 comparable tracts; distinct 342 set is disclosed; not accuracy or feeder validation. |
| Four-hazard damage and initial service | Frozen four-hazard damage and tract initial-service tables | Fig03 A–B | Direct scenario context; historical/current fragility sets differ. |
| Local, threshold, source-path loss mechanism | Frozen `LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv`, Unconstrained rows | Fig03 C | **Closed:** a policy-independent Unconstrained decomposition exists for all four hazards and replaces the prior Hospital-first integral. It is an integrated component summary, not dynamic timing. |
| Unconstrained recovery baseline | Frozen C57_D1 Unconstrained summary and tract initial/T80 table | Fig03 D | Direct 2pc50 population T80 distribution and reached-tract T80 map; distinct estimands. |
| Full scheduled-policy recovery | Frozen recovery curves and 84k+10k summary authorities | Fig04 A–B | **Closed:** all eight distinct policies plus Unconstrained are shown; four explanatory strategies emphasized, remaining four retained. Curves display 0–120 h; burden/outcomes use 0–480 h. |
| Aggregate burden, T80 and hospital-linked burden | Frozen strategy summaries | Fig04 B | All policies retained with uniform 5th–95th realization ranges, not confidence intervals. Hospital-linked tract service is not hospital electricity or clinical capacity. |
| Q1–Q4 absolute burden | Frozen 2pc50 strategy/equity summaries | Fig05 A | Four policy contrasts shown; Q4 is highest and Q1 lowest social-vulnerability quartile. |
| Aggregate vs Q4 burden | Frozen strategy summaries | Fig05 B | Mean summary estimates only; no uncertainty encoded in this plane. The adjacent matched-effects panel carries paired-realization ranges. |
| Reference sensitivity, signed/absolute group separation and Gini | Frozen strategy/equity summaries | Fig05 C | Matched VF−Impact/Hospital/Degree contrasts shown; Gini is separately unitless and is not treated as a single equity verdict. |
| Spatial paired effects | Frozen tract-effects table contains VF−Impact and VF−Hospital | Fig05 D | **Closed:** map uses VF−Impact, 2pc50, all 2,315 tracts. Mean sign/magnitude is not significance or per-realization improved population. |
| Two-level crew contrast | Frozen C29_D1/C57_D1 outcomes | Fig06 | **Closed at the stated scope:** exact 29- vs 57-crew comparison; no continuous response language. |
| Full discrete crew cases | Frozen C29/C57/C86/C114 summaries, eight distinct scheduled policies, n=1,000 each | Candidate supplement: Crew Resource Contrasts | **Closed:** all tested discrete crew cases are visualized for four outcomes; no values between cases are inferred. |
| Repair-duration cases | Frozen C57_D0.75/D1/D1.25/D1.50 summaries, eight distinct scheduled policies, n=1,000 each | Candidate supplement: Repair Duration Contrasts | **Closed:** complete frozen D variants exist and are visualized for four outcomes; claims are limited to tested 2pc50 cases. |
| Cross-hazard policy contrasts | Frozen formal plus Vulnerability-first summary tables; all eight strategies, each n=1,000/hazard | Candidate supplement: Cross-Hazard Policy Robustness | **Closed for descriptive scenario contrasts:** all four hazards and eight policies have frozen results. Fragility vintage differs, so not a pure PGA sensitivity. |
| GA reproducibility | Five fixed-seed histories, incumbent summary, sequence identity | FigS05 A–C | **Closed:** candidate mean traces vary, best-so-far remains at Impact-first incumbent, no seed improves it. This is not proof of global optimality. |
| Stage 7 typology/hotspots | Harmonized Stage 7 labels/status/profiles/hotspot output | Fig07 A–C; FigS09 A–D | **Closed:** same Stage 7 cluster-ID palette in Fig07 map and FigS09 scatter. 2,291 typology members; 24 tracts remain explicitly outside typology. |
| Mapping/gate robustness | Existing frozen mapping, cutoff and gate sensitivity tables | Existing supporting authorities; not recomputed here | Evidence remains available in the prior collection; this v2.1 pass does not add a new sensitivity. |
| Source redundancy | Frozen station/dynamic connectivity diagnostics | Existing supporting authorities; not recomputed here | A connectivity diagnostic, not delivered MW or capacity. |
| Capacity sensitivity | Frozen SCE closure and supported-station output | Existing supporting authorities; not recomputed here | Limited supported subset; cannot establish full-system earthquake-time electrical adequacy. |

## STORY_EVIDENCE_GAP closure and remaining claim boundaries

**Closed by existing frozen evidence:** the loss-mechanism panel can be a general Unconstrained baseline because all four hazards have frozen Unconstrained decomposition rows; the resource/duration review no longer lacks its scenario coverage because all four crew cases and four duration cases have 1,000-realization summaries for the eight distinct scheduled policies; Vulnerability-first also has frozen summaries in all four hazards; the tract map can use the existing Vulnerability-first minus Impact-first tract-effect authority; and the GA plot has generation-mean candidate traces as well as incumbent history.

**Resolved by narrower claims rather than new evidence:** cross-hazard contrasts must be called scenario contrasts because historical hazards and 2pc50 use different adopted fragility parameter sets. Crew count and duration are separate discrete one-factor scenario families; the archive does not define a full crew-by-duration factorial, so no interaction or interpolated response claim is supported. Public-site comparison is candidate-site agreement on 337 comparable tracts, not accuracy, feeder validation, service-territory ground truth, or whole-model predictive validation. Capacity support is not full-network adequacy. Source reachability/redundancy is not delivered power. Stage 7 cluster/hotspot outputs are descriptive/screening products, not intervention priorities.

| Previously identified gap / claim risk | Status in v2.1 | Frozen evidence or claim boundary |
|---|---|---|
| Policy-independent loss-mechanism decomposition | CLOSED | Four-hazard Unconstrained rows in the accepted decomposition table; no restoration policy is used as a general baseline. |
| Utility candidate eligibility visible in the system figure | CLOSED for representation | Fig02-C maps the frozen 2,315-tract utility domains and candidate-pool rule. External public-site comparison remains support/agreement only. |
| Resource and duration robustness absent from review figures | CLOSED for tested cases | All four crew-count cases and all four duration-multiplier cases have 1,000 frozen realizations per distinct scheduled policy. They are separate discrete scenario families. |
| Cross-hazard policy evidence | CLOSED for descriptive contrasts; interpretation narrowed | All four hazards are represented. Differences across hazards are not pure PGA effects because adopted fragility parameter vintages differ. |
| GA candidate search hidden by coincident incumbent curves | CLOSED for execution evidence | Five frozen generation-mean candidate histories are shown against the retained incumbent. The finite search does not establish global optimality. |
| Full-network earthquake-time electrical adequacy | OPEN; claim must remain bounded | No compatible load-flow case supports calculation of delivered MW, overload, or adequacy. Source reachability is not electrical delivery. |
| Feeder/service-territory mapping truth | OPEN; claim must remain bounded | Public-site candidate agreement is not feeder ground truth or predictive mapping accuracy. |
| Crew-by-duration interaction / continuous response | OPEN; claim must remain bounded | No complete frozen factorial or continuous parameter support exists; do not interpolate between cases. |
| All 2,315 tracts in residential typology | OPEN by defined scope, explicitly represented | Only 2,291 tracts enter residential clustering; 24 are labeled outside/not applicable and are not assigned a cluster. |

## Three core research questions

| Core question | Direct v2.1 evidence | Status |
|---|---|---|
| 1. How do hazard and network dependency produce tract service disruption? | Fig02 B–D; Fig03 A–D; existing mapping-robustness evidence | Direct evidence for retained topology, utility eligibility, public-site agreement, hazard loss decomposition, and Unconstrained baseline. Earthquake-time electrical adequacy remains a claim-limited gap: no load-flow/capacity simulation is supported. |
| 2. Under logistics/resource constraints, how do priorities change overall and critical-service recovery? | Fig04 A–B; Fig06; crew and duration robustness candidates; FigS05 | Direct for displayed 2pc50 cases and frozen discrete scenario families. No continuous interpolation or crew-duration interaction. |
| 3. How are burdens redistributed across vulnerability groups and places? | Fig05 A–D; Fig06; crew/duration candidates; Fig07 descriptive community context | Direct for the displayed metrics; no single “fairest policy” claim. |
"""
    (OUT/"STORY_EVIDENCE_MATRIX.md").write_text(matrix,encoding="utf-8")
    (OUT/"FIGURE_V2_1_CAPTIONS.md").write_text("# Figure v2.1 draft captions\n\n"+"\n\n".join(f"## {k}\n\n{v}" for k,v in CAPTIONS.items())+"\n",encoding="utf-8")
    readme="""# Candidate v2.1 review set

Review-only, presentation-only drafts generated from accepted frozen result tables and existing figure authorities. This folder does not edit or replace `results/figures/`; candidate v2 is preserved. No simulation, physical sampling, scheduling, GA search, or Stage 7 clustering was run.

`FIGURE_V2_1_REVIEW_PACKET.pdf` contains each candidate at its exact 185 mm physical width followed by the full draft caption. PNGs are 600-dpi review copies; `_preview.png` files are 150-dpi page-width previews. `FIGURE_V2_1_PANEL_CROSSWALK.csv` identifies every panel's prior v2 location, frozen source, metric, reference, and v2.1 change. `STORY_EVIDENCE_MATRIX.md` records what is closed and what must remain claim-limited.

The crew-count and repair-duration candidates are separate discrete scenario families, not a continuous response surface or a full factorial. Cross-hazard panels are scenario contrasts, not pure PGA sensitivity. No Main/Supplement selection or promotion is implied.
"""
    (OUT/"README.md").write_text(readme,encoding="utf-8")


def make_review_packet():
    packet=fitz.open()
    for stem,caption in CAPTIONS.items():
        with fitz.open(OUT/f"{stem}.pdf") as source:
            packet.insert_pdf(source)
        page=packet.new_page(width=W_MM/25.4*72,height=340/25.4*72)
        margin=28
        page.insert_text((margin,32),stem.replace("_"," "),fontsize=14,fontname="hebo",color=(.15,.2,.23))
        page.insert_text((margin,52),"Candidate v2.1 draft caption",fontsize=10,fontname="hebo",color=(.31,.36,.39))
        rect=fitz.Rect(margin,68,page.rect.width-margin,220)
        result=page.insert_textbox(rect,caption,fontsize=9.4,fontname="helv",lineheight=1.23,color=(.12,.14,.15))
        if result<0: raise ValueError(f"Caption overflow for {stem}")
        source_paths=all_sources()[stem]
        y=238
        page.insert_text((margin,y),"Frozen source authorities:",fontsize=9,fontname="hebo",color=(.15,.2,.23))
        text="\n".join(f"• {rel(p)} | SHA-256 {sha256(p)}" for p in source_paths)
        result=page.insert_textbox(fitz.Rect(margin,y+8,page.rect.width-margin,page.rect.height-20),text,fontsize=6.5,fontname="cour",lineheight=1.18,color=(.25,.27,.28))
        if result<0: raise ValueError(f"Source list overflow for {stem}")
    out=OUT/"FIGURE_V2_1_REVIEW_PACKET.pdf"
    packet.set_metadata({"title":"LA Grid Figure Review Packet - Candidate v2.1","author":"Frozen-results figure review candidate"})
    packet.save(out,garbage=4,deflate=True); packet.close()


def make_contact_sheets():
    stems=list(CAPTIONS)
    for page_no,start in enumerate(range(0,len(stems),4),start=1):
        selected=stems[start:start+4]
        sheet=Image.new("RGB",(1600,1800),"#e7eaec")
        for j,stem in enumerate(selected):
            im=Image.open(OUT/f"{stem}_preview.png").convert("RGB")
            im.thumbnail((760,820),Image.Resampling.LANCZOS)
            tile=Image.new("RGB",(790,890),"white"); tile.paste(im,((790-im.width)//2,46))
            draw=ImageDraw.Draw(tile); draw.text((14,12),stem.replace("_"," "),fill="#25343b")
            sheet.paste(tile,((j%2)*800,(j//2)*900))
        sheet.save(OUT/f"FIGURE_V2_1_CONTACT_SHEET_{page_no:02d}.png",dpi=(150,150))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    eval_data=base.read_eval()
    tracts=base.map_domain()
    full=load_full_frozen_summary()
    expected={(h,s) for h in HAZARDS for s in SCHEDULED}
    have=set(full[(full.resource_scenario.eq("C57_D1"))].groupby(["hazard","strategy_id"]).size().index.tolist())
    if not expected.issubset(have): raise ValueError("Frozen four-hazard policy coverage is incomplete")
    out=[]
    out.append(base.build_fig01())
    out.append(build_fig02())
    out.append(build_fig03(eval_data))
    out.append(base.build_fig04(eval_data))
    out.append(build_fig05(eval_data,tracts))
    out.append(build_fig06(eval_data))
    out.append(build_fig07())
    out.append(build_figs05())
    out.append(build_figs09())
    effects=paired_policy_effects(full)
    out.append(build_cross_hazard(full,effects))
    out.append(build_discrete_case_figure(eval_data,"crew"))
    out.append(build_discrete_case_figure(eval_data,"duration"))
    write_metadata(effects)
    make_review_packet(); make_contact_sheets()
    identity={"base_head":"d5ec162e17de49747a065f4bc0111e77181a14e5","candidate":"v2.1","operation":"presentation-only rendering from frozen accepted outputs",
              "results_figures_modified":False,"scientific_simulation_or_reclustering_rerun":False,
              "figure_count":len(CAPTIONS),"full_width_mm":W_MM,"raster_preview_dpi":DPI,
              "policy_colors_and_lines":"shared STYLE from candidate_v2 builder","cluster_palette":"parsed from official Project_Visualizer.py cluster-ID constant"}
    (OUT/"FIGURE_V2_1_IDENTITY.json").write_text(json.dumps(identity,indent=2),encoding="utf-8")
    print(f"Rendered {len(out)} candidate figure files; packet={OUT/'FIGURE_V2_1_REVIEW_PACKET.pdf'}")
    print(f"Candidate folder: {OUT}")


if __name__=="__main__":
    main()
