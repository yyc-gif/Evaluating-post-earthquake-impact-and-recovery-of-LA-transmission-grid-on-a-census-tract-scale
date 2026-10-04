"""Targeted author-feedback artwork update for Fig06, Fig07 and FigS09.

Reads saved realization summaries, paired-effect rows and Stage 7 outputs.
It does not run simulations, scheduling, GA, PCA or clustering. Only the
Degree-first paired-reference rows are derived from frozen realization-level
metrics using the established paired-bootstrap helper.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUNDLE = ROOT / "results/figure_review/final_submission_candidate_20261002"
LAYOUT = ROOT / "results/figure_review/candidate_v2.1_layout"
FORMAL = ROOT / "Formal_Experiment_20260923/Formal_Results"
EQUITY = ROOT / "Formal_Experiment_20260923/Equity_Amendment"
STAGE7 = ROOT / "Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized"
MM = 72 / 25.4

sys.path.insert(0, str(ROOT / "src"))
from la_grid.revision.formal.results import _bootstrap_paired

matplotlib.rcParams.update({
    "font.family": "Arial", "font.size": 7.5,
    "axes.titlesize": 9.5, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.linewidth": 0.6,
    "grid.linewidth": 0.4, "pdf.fonttype": 42, "ps.fonttype": 42,
    "figure.facecolor": "white", "savefig.facecolor": "white",
})

METRICS = ["burden_Q4_hr", "population_weighted_normalized_burden_hr",
           "absolute_Q4_minus_Q1_hr"]
METRIC_LABEL = {
    "burden_Q4_hr": "Change in Q4 loss (h)",
    "population_weighted_normalized_burden_hr": "Change in population-weighted loss (h)",
    "absolute_Q4_minus_Q1_hr": "Change in absolute Q4–Q1 gap (h)",
}
CAPTION_FIG06 = (
    "Resource dependence of restoration-policy contrasts under 2pc50. Panels A–C compare the tested crew-availability "
    "multipliers with repair duration fixed at 1.00×; panels D–F compare the tested repair-duration multipliers while "
    "holding crew availability at the reference level. Within each condition, points show the Vulnerability-first "
    "outcome relative to Hospital-first (gray circles), Impact-first (orange squares), or Degree-first (open green triangles), "
    "paired on the same 1,000 saved physical realizations. The columns show cumulative service loss in Q4 (the highest "
    "social-vulnerability quartile), population-weighted cumulative service loss across all tracts, and the absolute "
    "Q4–Q1 burden separation. All loss integrals cover 0–480 h. Negative Q4 changes indicate lower Q4 loss; positive "
    "population-weighted changes indicate greater aggregate loss; positive separation changes indicate a wider "
    "between-group gap, not a change in Gini. Whiskers are 95% percentile-bootstrap confidence intervals for the mean "
    "matched difference from 10,000 resamples, not realization ranges. Hospital-first and Impact-first contrasts are read "
    "from the accepted paired-effect tables; Degree-first contrasts use the same paired metric values from saved "
    "realization summaries and the same bootstrap procedure. The tested crew and duration conditions are separate "
    "one-factor scenario families: no interpolation, continuous response or crew-by-duration interaction is estimated. "
    "The figure therefore compares tested conditions and does not assert a universal monotonic resource effect."
)
CAPTION_FIG07 = (
    "(A) Distributions of six descriptive features by community cluster under 2pc50; dashed lines mark cluster medians. "
    "(B) Standardized cluster profiles for recovery time (T80), pre-1970 housing share, population density, National Risk "
    "Index (NRI) risk score, NRI building value, and social vulnerability score. FEMA's National Risk Index "
    "documentation calls this metric the Social Vulnerability Score; the v1.19 data field used here is SOVI_SCORE, "
    "derived from the CDC/ATSDR Social Vulnerability Index 2020. It is not "
    "the older University of South Carolina/HVRI SoVI. These six profile features are descriptive and are not the full "
    "eleven-feature clustering input. (C) Cluster membership for 2,291 eligible residential tracts. (D) Hotspot score; "
    "outlines identify the ten highest-ranked tracts on this panel only. The study domain contains 2,315 tracts, including "
    "24 not-applicable tracts shown as N/A rather than as zero or low vulnerability. Clusters describe community "
    "typology; the hotspot score is descriptive and is not a validated intervention or repair-priority ranking."
)
CAPTION_FIGS09 = (
    "Diagnostics for the 2pc50 residential typology with 2,291 eligible tracts. (A) PCA scores colored by the same "
    "cluster-ID palette as Figure 7. (B) Explained variance by component. (C) Feature loadings in the standardized "
    "feature space, with log1p transformations for exposure features. (D) K-means inertia (within-cluster sum of "
    "squares) and silhouette coefficient across candidate cluster counts. These diagnostics describe dimensionality "
    "reduction and clustering support; they do not define repair or intervention priorities."
)
CREW_CASES = ["C29_D1", "C57_D1", "C86_D1", "C114_D1"]
DURATION_CASES = ["C57_D075", "C57_D1", "C57_D125", "C57_D150"]
REFERENCES = ["hospital-first", "impact-first", "degree-first"]
REF_STYLE = {
    "hospital-first": ("#555555", "o", "Hospital-first"),
    "impact-first": ("#ff7f00", "s", "Impact-first"),
    "degree-first": ("#4daf4a", "^", "Degree-first"),
}
CLUSTER_COLORS = ["#0072B2", "#E69F00", "#009E73", "#56B4E9", "#CC79A7"]
OLD_CLUSTER_COLORS = ["#303E4E", "#C0A55B", "#567E58", "#BAD1DB", "#724B63"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_pdf(pdf_path: Path):
    with fitz.open(pdf_path) as doc:
        page = doc[0]
        for dpi, suffix in ((600, ""), (150, "_page_preview")):
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
            pix.set_dpi(dpi, dpi)
            pix.save(str(pdf_path.with_name(pdf_path.stem + suffix + ".png")))


def load_fig06_effects() -> pd.DataFrame:
    baseline = pd.read_csv(EQUITY / "VULNERABILITY_PAIRWISE_EFFECTS.csv")
    resource = pd.read_csv(EQUITY / "VULNERABILITY_RESOURCE_EFFECTS.csv")
    keep = baseline.hazard.eq("2pc50") & baseline.metric.isin(METRICS) & baseline.resource_scenario.eq("C57_D1")
    existing = baseline.loc[keep & baseline.reference_strategy.isin(["hospital-first", "impact-first"])].copy()
    existing["effect_source"] = "VULNERABILITY_PAIRWISE_EFFECTS.csv (saved accepted paired effects)"
    resource_keep = resource.hazard.eq("2pc50") & resource.metric.isin(METRICS)
    existing_resource = resource.loc[
        resource_keep & resource.resource_scenario.ne("C57_D1") &
        resource.reference_strategy.isin(["hospital-first", "impact-first"])
    ].copy()
    existing_resource["effect_source"] = "VULNERABILITY_RESOURCE_EFFECTS.csv (saved accepted paired effects)"
    existing = pd.concat([existing, existing_resource], ignore_index=True, sort=False)
    expected_cases = set(CREW_CASES) | set(DURATION_CASES)
    existing = existing[existing.resource_scenario.isin(expected_cases)].copy()
    assert len(existing) == 42
    assert not existing.duplicated(["resource_scenario", "reference_strategy", "metric"]).any()

    metric_cols = ["hazard", "resource_scenario", "realization_id", "strategy_id", "mapping", "gate", *METRICS]
    raw = pd.concat([
        pd.read_parquet(FORMAL / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet", columns=metric_cols),
        pd.read_parquet(EQUITY / "VULNERABILITY_PRIMARY_SUMMARY.parquet", columns=metric_cols),
    ], ignore_index=True)
    raw = raw.loc[raw.hazard.eq("2pc50") & raw.mapping.eq("M1_UTILITY_003") &
                  raw.gate.eq("G1_BASELINE_050")]
    degree_rows = []
    # This is a new presentation contrast requested by the author. It uses
    # the saved 1,000 realization metrics and the established bootstrap helper.
    for case in sorted(expected_cases):
        d = raw.loc[raw.resource_scenario.eq(case)]
        cand = d.loc[d.strategy_id.eq("vulnerability-first")].set_index("realization_id")
        ref = d.loc[d.strategy_id.eq("degree-first")].set_index("realization_id")
        assert len(cand) == len(ref) == 1000
        assert cand.index.is_unique and ref.index.is_unique and set(cand.index) == set(ref.index)
        cand = cand.sort_index()
        ref = ref.loc[cand.index]
        for metric in METRICS:
            paired = _bootstrap_paired((cand[metric].to_numpy(float) - ref[metric].to_numpy(float)),
                                       resamples=10000, seed=42)
            degree_rows.append({
                "scope": "author-requested presentation contrast from saved realization metrics",
                "hazard": "2pc50", "resource_scenario": case,
                "strategy_id": "vulnerability-first", "reference_strategy": "degree-first",
                "metric": metric, **paired,
                "effect_source": "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet + VULNERABILITY_PRIMARY_SUMMARY.parquet; paired by realization_id; established 10,000-resample bootstrap (seed 42)",
            })
    degree = pd.DataFrame(degree_rows)
    assert len(degree) == 21 and degree.n_realizations.eq(1000).all()
    fields = ["scope", "hazard", "resource_scenario", "strategy_id", "reference_strategy", "metric",
              "n_realizations", "paired_mean_difference", "bootstrap_ci_low", "bootstrap_ci_high", "effect_source"]
    result = pd.concat([existing, degree], ignore_index=True, sort=False)
    result = result[fields].copy()
    assert len(result) == 63
    result.to_csv(OUT / "FIG06_DISPLAYED_EFFECT_ROWS.csv", index=False)
    return result


def render_fig06(effects: pd.DataFrame) -> Path:
    fig = plt.figure(figsize=(185 / 25.4, 166 / 25.4))
    gs = fig.add_gridspec(2, 3, left=.13, right=.985, top=.79, bottom=.13,
                          hspace=.89, wspace=.47)
    fig.text(.5, .985, "Resource dependence of restoration-policy contrasts under 2pc50",
             ha="center", va="top", fontsize=10, fontweight="bold")
    fig.text(.5, .946, "Vulnerability-first compared with each named policy reference",
             ha="center", va="top", fontsize=8)
    legend_handles = []
    for key in REFERENCES:
        color, marker, label = REF_STYLE[key]
        legend_handles.append(Line2D([0], [0], marker=marker, color=color, lw=0,
            markersize=5, markerfacecolor="white" if key == "degree-first" else color,
            markeredgewidth=1.0 if key == "degree-first" else .5,
            label=f"Reference: {label}"))
    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(.55, .918),
               ncol=3, frameon=False, columnspacing=1.7, handletextpad=.4)
    fig.text(.5, .862, "Crew-availability cases; repair duration held at 1.00×",
             ha="center", va="center", fontsize=7.5)
    titles = ["Q4 service loss", "Population-weighted loss", "Q4–Q1 separation"]
    source_index = []
    for row_i, cases in enumerate((CREW_CASES, DURATION_CASES)):
        for col_i, metric in enumerate(METRICS):
            ax = fig.add_subplot(gs[row_i, col_i])
            panel = chr(ord("A") + row_i * 3 + col_i)
            ax.set_title(f"{panel}. {titles[col_i]}", loc="left", fontsize=8.6,
                         pad=5, fontweight="bold")
            block = effects.loc[effects.metric.eq(metric)]
            lo = min(0.0, float(block.bootstrap_ci_low.min()))
            hi = max(0.0, float(block.bootstrap_ci_high.max()))
            pad = max((hi - lo) * .12, .05)
            ax.set_ylim(lo - pad, hi + pad)
            ax.axhline(0, color="#333333", linewidth=.75, linestyle="--", zorder=1)
            for ref_i, ref in enumerate(REFERENCES):
                color, marker, label = REF_STYLE[ref]
                offset = (ref_i - 1) * .17
                for x, case in enumerate(cases):
                    src = effects.loc[(effects.resource_scenario.eq(case)) &
                                      effects.reference_strategy.eq(ref) & effects.metric.eq(metric)]
                    assert len(src) == 1, (case, ref, metric)
                    item = src.iloc[0]
                    y = float(item.paired_mean_difference)
                    face = "white" if ref == "degree-first" else color
                    ax.errorbar(x + offset, y,
                        yerr=[[y - float(item.bootstrap_ci_low)],
                              [float(item.bootstrap_ci_high) - y]],
                        fmt=marker, color=color, ecolor=color, ms=4.8,
                        elinewidth=.75, capsize=2.0, markerfacecolor=face,
                        markeredgecolor=color, markeredgewidth=1.0 if ref == "degree-first" else .45,
                        zorder=4 + ref_i)
                    source_index.append({
                        "panel": panel, "condition": case, "metric": metric,
                        "reference": ref, "mean": y,
                        "ci_low": float(item.bootstrap_ci_low),
                        "ci_high": float(item.bootstrap_ci_high),
                        "n_realizations": int(item.n_realizations),
                        "source": item.effect_source,
                        "delta_definition": "Vulnerability-first outcome minus named reference",
                    })
            if row_i == 0:
                factors = np.array([29, 57, 86, 114], dtype=float) / 57.0
                labels = [f"{x:.2f}×" for x in factors]
                ax.set_xlabel("Crew availability multiplier", fontsize=7.6)
            else:
                labels = ["0.75×", "1.00×", "1.25×", "1.50×"]
                ax.set_xlabel("Repair-duration multiplier", fontsize=7.6)
            ax.set_xticks(range(4), labels)
            ax.set_xlim(-.45, 3.45)
            ax.set_ylabel(METRIC_LABEL[metric], fontsize=7.7)
            ax.grid(axis="y", alpha=.18, linewidth=.4)
            ax.tick_params(length=2.5, width=.6, labelsize=7.3)
            for spine in ax.spines.values():
                spine.set_linewidth(.6)
    fig.text(.5, .455, "Repair-duration cases: reference crew level held constant",
             ha="center", va="center", fontsize=7.5)
    fig.text(.5, .035,
             "Points: mean matched difference; whiskers: 95% bootstrap confidence intervals (10,000 resamples).",
             ha="center", va="center", fontsize=7.1)
    fig.text(.5, .012, "Loss integrals cover 0–480 h. Crew availability is normalized to the reference level (1.00×).",
             ha="center", va="center", fontsize=7.1)
    pdf = OUT / "Fig06_Author_Reviewed_Update.pdf"
    fig.savefig(pdf, metadata={"Title": "Resource dependence of restoration-policy contrasts under 2pc50",
                               "Author": "Author-review candidate"})
    plt.close(fig)
    pd.DataFrame(source_index).to_csv(OUT / "FIG06_PANEL_SOURCE_INDEX.csv", index=False)
    export_pdf(pdf)
    return pdf


def import_v21():
    source = ROOT / "results/figure_review/candidate_v2.1/build_candidate_v2_1.py"
    spec = importlib.util.spec_from_file_location("candidate_v21_author_feedback", source)
    v = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)
    return v


def patch_cluster_colors(doc: fitz.Document, old_hex, new_hex):
    old_rgb = [np.asarray(mcolors.to_rgb(c)) for c in old_hex]
    new_rgb = [mcolors.to_rgb(c) for c in new_hex]
    counts = [0] * len(old_hex)
    pattern = re.compile(rb"([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s+(RG|rg)\b")
    for page in doc:
        # show_pdf_page() stores the embedded original panels as nested Form
        # XObjects, so inspect both page streams and all imported vector forms.
        xrefs = set(page.get_contents())
        xrefs.update(item[0] for item in page.get_xobjects())
        for xref in sorted(xrefs):
            stream = doc.xref_stream(xref)
            def replace(match):
                rgb = np.array([float(match.group(i)) for i in (1, 2, 3)])
                for i, target in enumerate(old_rgb):
                    if np.allclose(rgb, target, atol=2e-5, rtol=0):
                        counts[i] += 1
                        return (" ".join(f"{v:.7f}" for v in new_rgb[i]) + " " +
                                match.group(4).decode()).encode()
                return match.group(0)
            doc.update_stream(xref, pattern.sub(replace, stream))
    if any(n == 0 for n in counts):
        raise AssertionError(f"A cluster color was not found in the PDF streams: {counts}")
    return counts


def redraw_maps(v, dest: Path):
    import geopandas as gpd
    labels = pd.read_csv(STAGE7 / "clusters_labels_final.csv")
    labels = labels.loc[labels.scenario.eq("2pc50")].copy()
    status = pd.read_csv(STAGE7 / "stage7_full_domain_tract_status.csv")
    status = status.loc[status.scenario.eq("2pc50")].copy()
    top = pd.read_csv(STAGE7 / "stage7_top10_slow_vulnerable_tracts.csv")
    top = top.loc[top.scenario.eq("2pc50")].copy()
    for frame in (labels, status, top):
        frame["tract_id"] = frame.tract_id.astype(str).str.zfill(11)
    assert len(status) == 2315 and len(labels) == 2291 and len(top) == 10
    geo = v.base.projected_map_data(v.base.map_domain().merge(status, on="tract_id", validate="one_to_one"))
    chosen = geo.loc[geo.tract_id.isin(top.tract_id)]
    assert len(chosen) == 10
    fig = plt.figure(figsize=(185 / 25.4, 75 / 25.4))
    axc = fig.add_axes([9/185, 14/75, 76/185, 59/75])
    axd = fig.add_axes([94/185, 14/75, 76/185, 59/75])
    for cid, color in enumerate(CLUSTER_COLORS, 1):
        geo.loc[geo.cluster.eq(cid)].plot(ax=axc, color=color, edgecolor="white", linewidth=.08)
    missing = geo.loc[geo.cluster.isna()]
    missing.plot(ax=axc, color="#eeeeee", edgecolor="#777777", hatch="///", linewidth=.16)
    norm = mcolors.Normalize(vmin=0, vmax=4)
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "july_hotspots", ["#2C7BB6", "#ABD9E9", "#FFFFBF", "#F46D43", "#8B1E3F"])
    geo.plot(column="SlowVulnerable_Hotspot_Score", ax=axd, cmap=cmap, norm=norm,
             edgecolor="#eeeeee", linewidth=.05,
             missing_kwds={"color": "#eeeeee", "edgecolor": "#777777", "hatch": "///"})
    # The accepted top-ten outline is drawn only over the hotspot-score panel.
    chosen.boundary.plot(ax=axd, color="#222222", linewidth=.40, zorder=8)
    for ax in (axc, axd):
        v.base.style_map_axis(ax)
    cbar_ax = fig.add_axes([172/185, 18/75, 2.2/185, 50/75])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, ticks=range(5))
    cb.set_label("Hotspot score", fontsize=8.5, labelpad=2)
    cb.ax.tick_params(labelsize=7.5, length=2, width=.6)
    cb.outline.set_linewidth(.5)
    cluster_handles = [Patch(facecolor=c, label=f"C{i}") for i, c in enumerate(CLUSTER_COLORS, 1)]
    cluster_handles.append(Patch(facecolor="#eeeeee", edgecolor="#777777", hatch="///", label="N/A (24)"))
    fig.legend(handles=cluster_handles, ncol=3, loc="lower center",
               bbox_to_anchor=(43/185, 0), frameon=False, fontsize=7.5,
               handlelength=.9, handletextpad=.3, columnspacing=.7, labelspacing=.3)
    fig.legend(handles=[Line2D([0], [0], color="#222222", lw=.40, label="Top-10 hotspot boundary")],
               ncol=1, loc="lower center", bbox_to_anchor=(139/185, 0), frameon=False,
               fontsize=7.5, handlelength=1.2, handletextpad=.35)
    tmp = OUT / "Fig07_Map_Panels_Author_Revision.pdf"
    fig.savefig(tmp, metadata={"Title": "Community cluster membership and hotspot score"})
    plt.close(fig)
    with fitz.open(tmp) as d:
        page = d[0]
        assert abs(page.rect.width / MM - 185) < .1 and abs(page.rect.height / MM - 75) < .1
        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)
        pix.save(str(OUT / "Fig07_Map_Panels_Author_Revision.png"))
    return tmp


def build_fig07(v, map_pdf: Path, dest: Path):
    source = OUT / "Fig07_Native_Panel_Reflow.pdf"
    with fitz.open(source) as original:
        patch_cluster_colors(original, OLD_CLUSTER_COLORS, CLUSTER_COLORS)
        # The source figure's panels A and B are retained as vector artwork.
        doc = fitz.open()
        page = doc.new_page(width=185 * MM, height=242 * MM)
        page.insert_font(fontname="ArialReview", fontfile="C:/Windows/Fonts/arial.ttf")
        page.insert_font(fontname="ArialReviewBold", fontfile="C:/Windows/Fonts/arialbd.ttf")
        page.show_pdf_page(fitz.Rect(0, 6*MM, 185*MM, 95*MM), original, 0,
                           clip=fitz.Rect(0, 0, 185*MM, 89*MM), keep_proportion=False)
        page.show_pdf_page(fitz.Rect(0, 103*MM, 185*MM, 164*MM), original, 0,
                           clip=fitz.Rect(0, 90*MM, 185*MM, 151*MM), keep_proportion=False)
        # White masks remove the old stand-alone A/B letters and the outdated
        # FEMA-prefixed label; no plot data or spatial features are covered.
        page.draw_rect(fitz.Rect(.5*MM, 8*MM, 5*MM, 13*MM), color=None, fill=(1,1,1), overlay=True)
        page.insert_text((2*MM, 6.5*MM), "A. Feature distributions across clusters",
                         fontsize=9.5, fontname="ArialReviewBold", color=(0,0,0))
        page.draw_rect(fitz.Rect(.5*MM, 104*MM, 5*MM, 109*MM), color=None, fill=(1,1,1), overlay=True)
        page.insert_text((2*MM, 101*MM), "B. Standardized feature profiles by cluster",
                         fontsize=9.5, fontname="ArialReviewBold", color=(0,0,0))
        # Replace the display phrase with the data-provider's metric name.
        page.draw_rect(fitz.Rect(123*MM, 48*MM, 184*MM, 53*MM), color=None,
                       fill=(1,1,1), overlay=True)
        page.insert_text((124*MM, 51*MM), "Social vulnerability score",
                         fontsize=9.5, fontname="ArialReviewBold", color=(0,0,0))
        page.draw_rect(fitz.Rect(36*MM, 151*MM, 75*MM, 160*MM), color=None,
                       fill=(1,1,1), overlay=True)
        page.insert_text((38*MM, 155*MM), "Social vulnerability",
                         fontsize=7.5, fontname="ArialReview", color=(0,0,0))
        page.insert_text((38*MM, 158*MM), "score",
                         fontsize=7.5, fontname="ArialReview", color=(0,0,0))
        with fitz.open(map_pdf) as map_doc:
            page.show_pdf_page(fitz.Rect(0, 167*MM, 185*MM, 242*MM), map_doc, 0,
                               keep_proportion=False)
        page.insert_text((9*MM, 166*MM), "C. Cluster membership",
                         fontsize=9.5, fontname="ArialReviewBold", color=(0,0,0))
        page.insert_text((94*MM, 166*MM), "D. Hotspot score",
                         fontsize=9.5, fontname="ArialReviewBold", color=(0,0,0))
        doc.set_metadata({"title": "Community typology and hotspot score",
                          "author": "Author-review artwork candidate"})
        doc.save(dest, garbage=4, deflate=True)
        doc.close()
    export_pdf(dest)
    return dest


def build_figs09_palette(dest: Path):
    source = OUT / "FigS09_Cluster_Visibility.pdf"
    with fitz.open(source) as doc:
        counts = patch_cluster_colors(doc, OLD_CLUSTER_COLORS, CLUSTER_COLORS)
        doc.save(dest, garbage=4, deflate=True)
    export_pdf(dest)
    return counts


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    BUNDLE.mkdir(parents=True, exist_ok=True)
    # Frozen source-file identity guards: only display derivatives below are written.
    guards = [
        FORMAL / "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet",
        EQUITY / "VULNERABILITY_PRIMARY_SUMMARY.parquet",
        EQUITY / "VULNERABILITY_PAIRWISE_EFFECTS.csv",
        EQUITY / "VULNERABILITY_RESOURCE_EFFECTS.csv",
        STAGE7 / "clusters_labels_final.csv",
        STAGE7 / "stage7_full_domain_tract_status.csv",
        STAGE7 / "stage7_top10_slow_vulnerable_tracts.csv",
        STAGE7 / "vis_stage7_kde_profiles.pdf",
        STAGE7 / "vis_stage7_heatmap.pdf",
    ]
    before = {p: sha(p) for p in guards}
    effects = load_fig06_effects()
    f6 = render_fig06(effects)
    v = import_v21()
    map_pdf = redraw_maps(v, OUT / "Fig07_Map_Panels_Author_Revision.pdf")
    f7 = build_fig07(v, map_pdf, OUT / "Fig07_Author_Reviewed_Update.pdf")
    f7s09 = OUT / "FigS09_Cluster_Palette_Author_Update.pdf"
    palette_counts = build_figs09_palette(f7s09)

    copies = [
        (f6, BUNDLE / "Main/Fig06.pdf"),
        (f7, BUNDLE / "Main/Fig07.pdf"),
        (f7s09, BUNDLE / "Supplement/FigS09.pdf"),
    ]
    for source, dest in copies:
        shutil.copyfile(source, dest)
        assert sha(source) == sha(dest)
        preview_png = source.with_name(source.stem + ".png")
        shutil.copyfile(preview_png, dest.with_suffix(".png"))
        stale_page_preview = dest.with_name(dest.stem + "_page_preview.png")
        if stale_page_preview.exists():
            stale_page_preview.unlink()

    update_bundle_text_and_pdfs()
    update_bundle_manifest()
    update_source_captions_and_rationale()

    for base in ("Main/Fig06", "Main/Fig07", "Supplement/FigS09"):
        pdf = OUT / ({"Main/Fig06": "Fig06_Author_Reviewed_Update.pdf",
                     "Main/Fig07": "Fig07_Author_Reviewed_Update.pdf",
                     "Supplement/FigS09": "FigS09_Cluster_Palette_Author_Update.pdf"}[base])
        # Actual-size page previews live beside the review source, not in Main/ or Supplement/.

    after = {p: sha(p) for p in guards}
    assert before == after, "A frozen scientific input changed during artwork generation."
    pd.DataFrame([{"input": p.relative_to(ROOT).as_posix(), "sha256_before": before[p],
                    "sha256_after": after[p], "unchanged": before[p] == after[p]} for p in guards]
                 ).to_csv(OUT / "FROZEN_INPUT_HASH_GUARD.csv", index=False)
    qa = []
    for p in [BUNDLE / "Main/Fig06.pdf", BUNDLE / "Main/Fig07.pdf", BUNDLE / "Supplement/FigS09.pdf"]:
        with fitz.open(p) as doc:
            page = doc[0]
            spans = [s for b in page.get_text("dict")["blocks"] if "lines" in b
                     for line in b["lines"] for s in line["spans"] if s["text"].strip()]
            qa.append({"file": p.relative_to(BUNDLE).as_posix(), "width_mm": page.rect.width / MM,
                       "height_mm": page.rect.height / MM, "min_font_pt": min(s["size"] for s in spans),
                       "fonts": ";".join(sorted(set(s["font"] for s in spans))),
                       "page_text_count": len(spans), "sha256": sha(p)})
    pd.DataFrame(qa).to_csv(OUT / "FIG06_FIG07_OUTPUT_QA.csv", index=False)
    (OUT / "CLUSTER_PALETTE_UPDATE.json").write_text(
        __import__("json").dumps({"cluster_ids": [1,2,3,4,5],
            "previous": OLD_CLUSTER_COLORS, "display_update": CLUSTER_COLORS,
            "figs09_replacements_per_color": palette_counts,
            "top10_boundaries": "hotspot map only; 0.40 pt",
            "science_changed": False}, indent=2), encoding="utf-8")
    print("Updated review-only Fig06, Fig07 and FigS09; scientific inputs unchanged.")
    print(pd.DataFrame(qa).to_string(index=False))


def update_bundle_text_and_pdfs():
    captions_path = BUNDLE / "MANUSCRIPT_FACING_CAPTIONS.md"
    md = captions_path.read_text(encoding="utf-8")
    section_patterns = [
        (r"(?ms)(^## Figure 6\.[^\n]*\n\n).*?(?=^## |\Z)", CAPTION_FIG06),
        (r"(?ms)(^## Figure 7\.[^\n]*\n\n).*?(?=^## |\Z)", CAPTION_FIG07),
        (r"(?ms)(^## Supplementary Figure S9\.[^\n]*\n\n).*?(?=^## |\Z)", CAPTION_FIGS09),
    ]
    for pattern, caption in section_patterns:
        md, n = re.subn(pattern, lambda m: m.group(1) + caption + "\n\n", md, count=1)
        assert n == 1, pattern
    captions_path.write_text(md, encoding="utf-8")

    # Compile the exact 7 + 13 figure order, keeping every artwork page at its
    # own physical size and following it immediately with its caption page.
    def title_for(main: bool, i: int) -> str:
        return (f"Figure {i}" if main else f"Supplementary Figure S{i:02d}")
    def caption_sections():
        matches = list(re.finditer(r"(?m)^## (.+)\n\n", md))
        sections = {}
        for i, m in enumerate(matches):
            end = matches[i+1].start() if i + 1 < len(matches) else len(md)
            body = md[m.end():end].strip()
            sections[m.group(1)] = body
        return sections
    sections = caption_sections()
    caption_lookup = {}
    for heading, body in sections.items():
        if heading.startswith("Figure "):
            n = int(heading.split(".", 1)[0].replace("Figure ", ""))
            caption_lookup[f"Main/Fig{n:02d}.pdf"] = (heading, body)
        elif heading.startswith("Supplementary Figure S"):
            n = int(heading.split(".", 1)[0].replace("Supplementary Figure S", ""))
            caption_lookup[f"Supplement/FigS{n:02d}.pdf"] = (heading, body)
    main_paths = [BUNDLE / f"Main/Fig{i:02d}.pdf" for i in range(1, 8)]
    supp_paths = [BUNDLE / f"Supplement/FigS{i:02d}.pdf" for i in range(1, 14)]
    for path in main_paths + supp_paths:
        assert path.exists() and path.stat().st_size > 1000
    for paths, output in ((main_paths, BUNDLE / "ALL_MAIN_FIGURES.pdf"),
                          (supp_paths, BUNDLE / "ALL_SUPPLEMENT_FIGURES.pdf")):
        merged = fitz.open()
        for path in paths:
            with fitz.open(path) as source:
                merged.insert_pdf(source)
        merged.save(output, garbage=4, deflate=True)
        merged.close()
    full = fitz.open()
    for paths in (main_paths, supp_paths):
        for path in paths:
            key = path.relative_to(BUNDLE).as_posix()
            assert key in caption_lookup, key
            heading, body = caption_lookup[key]
            with fitz.open(path) as source:
                full.insert_pdf(source)
            caption_page = full.new_page(width=185 * MM, height=350 * MM)
            caption_page.insert_font(fontname="ArialReview", fontfile="C:/Windows/Fonts/arial.ttf")
            caption_page.insert_font(fontname="ArialReviewBold", fontfile="C:/Windows/Fonts/arialbd.ttf")
            caption_page.insert_text((14*MM, 20*MM), heading, fontsize=9.5,
                                     fontname="ArialReviewBold", color=(0,0,0))
            remaining = caption_page.insert_textbox(
                fitz.Rect(14*MM, 29*MM, 171*MM, 333*MM), body,
                fontsize=9.2, fontname="ArialReview", lineheight=1.22,
                color=(0,0,0), align=0)
            assert remaining >= 0, f"Caption page overflow: {heading}"
    out = BUNDLE / "ALL_FIGURES_WITH_CAPTIONS.pdf"
    full.save(out, garbage=4, deflate=True)
    full.close()
    with fitz.open(out) as check:
        assert len(check) == 40, len(check)


def update_bundle_manifest():
    path = BUNDLE / "FIGURE_MANIFEST.csv"
    manifest = pd.read_csv(path, dtype=str).fillna("")
    records = {
        "Main/Fig06.pdf": (OUT / "Fig06_Author_Reviewed_Update.pdf", OUT / "Fig06_Author_Reviewed_Update.pdf"),
        "Main/Fig06.png": (OUT / "Fig06_Author_Reviewed_Update.png", OUT / "Fig06_Author_Reviewed_Update.pdf"),
        "Main/Fig07.pdf": (OUT / "Fig07_Author_Reviewed_Update.pdf", OUT / "Fig07_Author_Reviewed_Update.pdf"),
        "Main/Fig07.png": (OUT / "Fig07_Author_Reviewed_Update.png", OUT / "Fig07_Author_Reviewed_Update.pdf"),
        "Supplement/FigS09.pdf": (OUT / "FigS09_Cluster_Palette_Author_Update.pdf", OUT / "FigS09_Cluster_Palette_Author_Update.pdf"),
        "Supplement/FigS09.png": (OUT / "FigS09_Cluster_Palette_Author_Update.png", OUT / "FigS09_Cluster_Palette_Author_Update.pdf"),
    }
    for final_name, (source_pdf, measure_pdf) in records.items():
        file_path = BUNDLE / final_name
        with fitz.open(measure_pdf) as d:
            page = d[0]
            spans = [s for b in page.get_text("dict")["blocks"] if "lines" in b
                     for line in b["lines"] for s in line["spans"] if s["text"].strip()]
            size = f"{page.rect.width/MM:.3f} x {page.rect.height/MM:.3f}"
            minimum = f"{min(s['size'] for s in spans):.3f}"
        idx = manifest.index[manifest.final_name.eq(final_name)]
        assert len(idx) == 1, final_name
        i = idx[0]
        manifest.loc[i, "source_file"] = source_pdf.relative_to(ROOT).as_posix()
        manifest.loc[i, "source_commit"] = "REVIEW_UPDATE_COMMIT_PENDING"
        manifest.loc[i, "sha256"] = sha(file_path)
        manifest.loc[i, "size_mm"] = size
        manifest.loc[i, "min_font_pt"] = minimum
        manifest.loc[i, "status"] = "AUTHOR_REVIEW_UPDATE_NOT_PROMOTED"
    manifest.to_csv(path, index=False)
    readme = BUNDLE / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"Artwork is fixed to commit .*?; captions come from .*?\n",
        "The base artwork selection is from commit `a2a3c222b6c9180cc6b1c83cebe21c1d15a33ea6`; Fig06, Fig07 and FigS09 were updated for the author feedback of 2026-10-04 and remain review-only. Other selected figures are unchanged. Figure 01 is the submission-layout version. S14/S15 remain internal evidence and S16 is a review aid; they are not included.\n",
        text, count=1)
    readme.write_text(text, encoding="utf-8")


def update_source_captions_and_rationale():
    captions_path = OUT / "CAPTIONS.md"
    md = captions_path.read_text(encoding="utf-8")
    for heading, caption in [
        ("Fig06_Preferred_Resource_Policy_Contrasts", CAPTION_FIG06),
        ("Fig07_Native_Panel_Reflow", CAPTION_FIG07),
        ("FigS09_Cluster_Visibility", CAPTION_FIGS09),
    ]:
        pattern = rf"(?ms)(^## {re.escape(heading)}\n\n).*?(?=^## |\Z)"
        md, n = re.subn(pattern, lambda m: m.group(1) + caption + "\n\n", md, count=1)
        assert n == 1, heading
    captions_path.write_text(md, encoding="utf-8")
    rationale = OUT / "FIG06_REDESIGN_RATIONALE.md"
    existing = rationale.read_text(encoding="utf-8")
    marker = "\n## Author-feedback update — 2026-10-04\n"
    if marker in existing:
        existing = existing.split(marker)[0]
    addition = (
        marker +
        "\nThe three Fig06 outcomes are retained because they answer three distinct questions: whether Q4 loss changes, "
        "whether population-weighted loss changes, and whether the absolute Q4–Q1 burden gap changes. This is a focused "
        "policy-contrast figure, not a display of every outcome metric. Gini remains a separate overall inequality "
        "measure in Fig05; T80 and hospital-linked tract loss remain in the all-policy outcome figures. The Q4–Q1 gap "
        "is described as between-group separation, not Gini inequality.\n\n"
        "Degree-first is now shown as a third named reference. Its mean matched differences and 95% percentile-bootstrap "
        "intervals are derived from saved realization-level summary values using the existing paired bootstrap routine; "
        "the physical outcomes, source tables and trajectories are unchanged. Crew availability is displayed only as "
        "multipliers relative to the reference level. The duration row states that the reference crew level is held "
        "constant, without repeating a crew count.\n\n"
        "Fig07 uses FEMA National Risk Index v1.19 field `SOVI_SCORE`. FEMA's documentation calls this measure the "
        "Social Vulnerability Score; the figure uses that concise label. Cluster colors are brighter and keyed consistently "
        "across Fig07 and FigS09. Top-ten tract outlines appear only on the hotspot-score map, with a thin boundary stroke.\n\n"
        "Presentation update only; no promotion. Frozen scientific inputs changed = 0.\n"
    )
    rationale.write_text(existing.rstrip() + "\n" + addition, encoding="utf-8")


if __name__ == "__main__":
    main()
