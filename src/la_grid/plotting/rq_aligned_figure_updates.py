"""Source-bound Figure 3-7 refinements for the isolated 1021 review suite."""
from io import BytesIO

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


MM = 72 / 25.4
FILTER = {
    "hazard": "2pc50",
    "resource_scenario": "C57_D1",
    "mapping": "M1_UTILITY_003",
    "gate": "G1_BASELINE_050",
}
FIG4_ORDER = ["impact-first", "hospital-first", "degree-first",
              "vulnerability-first", "betweenness-first", "random", "unconstrained"]
DISPLAY = {
    "impact-first": "Impact-first",
    "hospital-first": "Hospital-first",
    "degree-first": "Degree-first",
    "vulnerability-first": "Vulnerability-first",
    "betweenness-first": "Betweenness-first",
    "centrality-first": "Spectral-connectivity-first",
    "closeness-first": "Closeness-first",
    "random": "Random",
    "unconstrained": "Unconstrained",
}
COLORS = {
    "impact-first": "#ff7f00",
    "hospital-first": "#555555",
    "degree-first": "#4daf4a",
    "vulnerability-first": "#a65628",
    "betweenness-first": "#b59a00",
    "random": "#9a9a9a",
    "unconstrained": "#111111",
}
MARKERS = {
    "impact-first": "s", "hospital-first": "o", "degree-first": "^",
    "vulnerability-first": "D", "betweenness-first": "P", "random": "o",
    "unconstrained": "o",
}
COMPONENTS = [
    ("L_self_population_mass_weighted_hr", "Substation damage"),
    ("L_threshold_population_mass_weighted_hr", "Functionality threshold"),
    ("L_source_population_mass_weighted_hr", "Source-path loss"),
    ("L_total_population_mass_weighted_hr", "Total service loss"),
]
OUTCOMES = [
    ("population_weighted_normalized_burden_hr", "All tracts"),
    ("burden_Q4_hr", "Q4 tracts"),
    ("signed_Q4_minus_Q1_hr", "Signed Q4-Q1 gap"),
    ("absolute_Q4_minus_Q1_hr", "Mean within-realization |Q4-Q1|"),
    ("hospital_mean_normalized_burden_hr", "Hospital-linked tracts"),
]
REFERENCES = ["hospital-first", "impact-first", "degree-first"]
REFERENCE_COLORS = {"hospital-first": "#555555", "impact-first": "#ff7f00",
                    "degree-first": "#4daf4a"}

plt.rcParams.update({
    "font.family": "Arial", "font.sans-serif": ["Arial"], "font.size": 7.5,
    "axes.titlesize": 9.0, "axes.titleweight": "bold", "axes.labelsize": 7.5,
    "xtick.labelsize": 7.0, "ytick.labelsize": 7.0, "legend.fontsize": 7.2,
    "axes.linewidth": 0.55, "pdf.fonttype": 42, "figure.facecolor": "white",
})


def _selected(data, strategies=None):
    mask = np.ones(len(data), dtype=bool)
    for col, value in FILTER.items():
        mask &= data[col].eq(value).to_numpy()
    out = data.loc[mask].copy()
    if strategies is not None:
        out = out.loc[out.strategy_id.isin(strategies)].copy()
    return out


def _quantiles(values):
    arr = np.asarray(values, dtype=float)
    return float(np.mean(arr)), float(np.quantile(arr, .05)), float(np.quantile(arr, .95))


def _paired(primary, vulnerability, strategy, metric):
    va = vulnerability.set_index("realization_id").sort_index()
    ref = primary.loc[primary.strategy_id.eq(strategy)].set_index("realization_id").sort_index()
    assert va.index.is_unique and ref.index.is_unique and va.index.equals(ref.index)
    delta = va[metric].to_numpy(float) - ref[metric].to_numpy(float)
    assert len(delta) == 1000 and np.isfinite(delta).all()
    return delta


def make_figure4(primary, vulnerability, gate_components, source_pdf):
    """Restore the two-panel, seven-strategy scope using saved curves and outcomes."""
    base_strategies = [key for key in FIG4_ORDER if key != "vulnerability-first"]
    data = pd.concat([_selected(primary, base_strategies),
                      _selected(vulnerability, ["vulnerability-first"])],
                     ignore_index=True, sort=False)
    counts = data.groupby("strategy_id").size().to_dict()
    assert counts == {key: 1000 for key in FIG4_ORDER}, counts
    sets = [set(group.realization_id) for _, group in data.groupby("strategy_id")]
    assert all(ids == sets[0] for ids in sets[1:])

    # Build the service-loss/T80 panel directly from realization-level outcomes.
    width, height = 185 / 25.4, 230 / 72
    fig = plt.figure(figsize=(width, height))
    measures = [
        ("population_weighted_normalized_burden_hr", "All-tract service loss", "#497f9b"),
        ("burden_Q4_hr", "Q4 service loss", "#c48a43"),
        ("hospital_mean_normalized_burden_hr", "Hospital-linked service loss", "#8a989f"),
    ]
    fig.legend(handles=[Patch(facecolor=color, label=label) for _, label, color in measures],
               loc="upper center", bbox_to_anchor=(.5, 1-32.4235/230), ncol=3, frameon=False,
               fontsize=7.5,borderaxespad=0,borderpad=0,
               handlelength=1.0, handletextpad=.35, columnspacing=.75)
    ax = fig.add_axes([.215, (230-199.8235)/230, .475, 145/230])
    tx = fig.add_axes([.795, (230-199.8235)/230, .17, 145/230])
    outcome_rows = []
    for row, strategy in enumerate(FIG4_ORDER):
        q = data.loc[data.strategy_id.eq(strategy)]
        for j, (field, label, color) in enumerate(measures):
            mean, p05, p95 = _quantiles(q[field])
            y = row + (j - 1) * .22
            ax.barh(y, mean, height=.19, color=color, alpha=1 if strategy in FIG4_ORDER[:4] + ["unconstrained"] else .66,
                    edgecolor="white", linewidth=.2, zorder=2)
            ax.errorbar(mean, y, xerr=[[mean-p05], [p95-mean]], fmt="none",
                        ecolor="#303030", elinewidth=.55, capsize=1.2, zorder=3)
            outcome_rows.append(dict(strategy_id=strategy, metric=field, mean=mean,
                                     p05=p05, p95=p95, n_realizations=1000))
        mean, p05, p95 = _quantiles(q.population_T80_hr)
        tx.errorbar(mean, row, xerr=[[mean-p05], [p95-mean]], fmt=MARKERS[strategy],
                    color=COLORS[strategy], markersize=3, linewidth=.65, capsize=1.2)
        outcome_rows.append(dict(strategy_id=strategy, metric="population_T80_hr", mean=mean,
                                 p05=p05, p95=p95, n_realizations=1000))
    ax.set_yticks(range(len(FIG4_ORDER)), [DISPLAY[key] for key in FIG4_ORDER],fontsize=7.5)
    ax.set_ylim(len(FIG4_ORDER)-.45, -.55)
    ax.set_xlim(0, 50)
    ax.set_xlabel("Service loss (h)")
    ax.tick_params(axis="y", length=0, pad=3)
    tx.set_yticks([])
    tx.set_ylim(len(FIG4_ORDER)-.45, -.55)
    tx.set_xlim(35, 62)
    tx.set_xticks([40, 50, 60])
    tx.set_xlabel("Population T80 (h)")
    for target in (ax, tx):
        target.tick_params(labelsize=7.5)
        target.spines[["top", "right"]].set_visible(False)
        target.grid(axis="x", color="#e5e5e5", linewidth=.4, zorder=0)
    outcome_pdf = BytesIO()
    fig.savefig(outcome_pdf, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)

    # Paired component differences are computed on the same 1,000 physical realizations.
    indexed = data.set_index(["strategy_id", "realization_id"])
    degree = indexed.loc["degree-first"].sort_index()
    hospital = indexed.loc["hospital-first"].sort_index()
    assert degree.index.equals(hospital.index) and len(degree) == 1000
    deltas = degree[[name for name, _ in COMPONENTS]] - hospital[[name for name, _ in COMPONENTS]]
    component_rows = []
    means = []
    for row, (field, label) in enumerate(COMPONENTS):
        values = deltas[field].to_numpy(float)
        mean, p05, p95 = _quantiles(values)
        means.append(mean)
        component_rows.append(dict(component=field, label=label, degree_minus_hospital_mean_hr=mean,
                                   p05=p05, p95=p95, n_paired_realizations=1000))

    source = fitz.open(stream=source_pdf, filetype="pdf")
    assert len(source) == 1
    page_w = source[0].rect.width
    out_h = 530.0
    out = fitz.open()
    page = out.new_page(width=page_w, height=out_h)
    # Translate (never scale) the saved legend and trajectory vectors.
    page.show_pdf_page(fitz.Rect(0,22.92,page_w,76.92),source,0,
                       clip=fitz.Rect(0,0,page_w,54))
    page.show_pdf_page(fitz.Rect(0,82.57,page_w,288.57),source,0,
                       clip=fitz.Rect(0,101,page_w,307))
    page.show_pdf_page(fitz.Rect(0,300,page_w,out_h),
                       fitz.open(stream=outcome_pdf.getvalue(), filetype="pdf"), 0)
    page.insert_font(fontname='Figure4Heading',fontfile='C:/Windows/Fonts/arialbd.ttf')
    heading_font=fitz.Font(fontfile='C:/Windows/Fonts/arialbd.ttf')
    for label,baseline in [('A. Population-weighted service recovery',16),
                           ('B. Service loss and recovery time',317)]:
        page.insert_text(((page_w-heading_font.text_length(label,fontsize=9.5))/2,baseline),
                         label,fontname='Figure4Heading',fontsize=9.5,color=(0,0,0))
    out.set_metadata({"title": "Figure 4. Restoration strategy comparisons",
                      "subject": "Seven-strategy recovery curves, service loss and recovery time"})
    source.close()
    aggregate = gate_components.loc[
        gate_components.hazard.eq("2pc50")
        & gate_components.resource_scenario.eq("C57_D1")
        & gate_components.strategy_id.isin(["degree-first", "hospital-first"])
    ].set_index("strategy_id")
    assert set(aggregate.index) == {"degree-first", "hospital-first"}
    aggregate_fields = {
        "L_self_population_mass_weighted_hr": "self_mean_hr",
        "L_threshold_population_mass_weighted_hr": "threshold_mean_hr",
        "L_source_population_mass_weighted_hr": "source_mean_hr",
        "L_total_population_mass_weighted_hr": "total_mean_hr",
    }
    aggregate_crosscheck = {}
    for component, source_field in aggregate_fields.items():
        reference_difference = float(aggregate.loc["degree-first", source_field]
                                    - aggregate.loc["hospital-first", source_field])
        raw_difference = float(deltas[component].mean())
        assert abs(reference_difference - raw_difference) < 1e-10, component
        aggregate_crosscheck[component] = dict(
            paired_realization_mean=raw_difference,
            difference_of_saved_strategy_means=reference_difference,
            absolute_error=abs(reference_difference-raw_difference))
    qa = {
        "source_pdf_vector_panel_A_preserved": True,
        "source_pdf_sha256": __import__("hashlib").sha256(source_pdf).hexdigest(),
        "source_trajectory_curves_regenerated": False,
        "main_panels": ["A", "B"],
        "single_pair_decomposition_in_main": False,
        "pairwise_rows_retained_as_diagnostic_only": True,
        "source_panel_A_translations_pt": {"legend": 22.92, "curves": -18.43},
        "outcome_source_rows": len(data),
        "strategies": counts,
        "shared_realization_identity_across_strategies": True,
        "service_loss_and_T80_rows": outcome_rows,
        "paired_component_rows": component_rows,
        "aggregate_component_mean_crosscheck": aggregate_crosscheck,
        "component_additivity_max_abs_error_hr": float(np.max(np.abs(deltas[[x[0] for x in COMPONENTS[:3]]].sum(axis=1)-deltas[COMPONENTS[3][0]]))),
        "component_mean_difference_sum_error_hr": float(abs(sum(means[:3])-means[3])),
        "page_size_mm": [float(page_w/MM), float(out_h/MM)],
        "uncertainty": "5th-95th realization ranges, not confidence intervals",
    }
    assert qa["component_additivity_max_abs_error_hr"] < 1e-10
    assert qa["component_mean_difference_sum_error_hr"] < 1e-10
    return out.tobytes(garbage=4, deflate=True, no_new_id=True), qa


def make_figure5(primary, vulnerability, pairwise, source_pdf):
    """Replace only the lower-left signed/absolute comparison panel with raw-pair calculations."""
    p = _selected(primary)
    v = _selected(vulnerability)
    assert len(v) == 1000 and v.strategy_id.eq("vulnerability-first").all()
    assert p.realization_id.nunique() == 1000 and v.realization_id.nunique() == 1000
    assert set(p.realization_id) == set(v.realization_id)
    assert v.physical_sample_hash.notna().all() and v.physical_sample_hash.nunique() == 1000

    comparison_rows = []
    pairwise_checks = []
    all_display = []
    for ref in REFERENCES:
        paired = {}
        for field, label in OUTCOMES:
            values = _paired(p, v, ref, field)
            mean, p05, p95 = _quantiles(values)
            paired[field] = values
            comparison_rows.append(dict(reference_strategy=ref, outcome=field, label=label,
                                        mean_vulnerability_first_minus_reference_hr=mean,
                                        p05=p05, p95=p95, n_paired_realizations=1000))
            all_display.extend([p05, p95])

        # Independently stored pairwise means are an independent numerical check.
        for field, label in OUTCOMES:
            row = next(item for item in comparison_rows
                       if item["reference_strategy"] == ref and item["outcome"] == field)
            match = pairwise.loc[
                pairwise.hazard.eq(FILTER["hazard"])
                & pairwise.resource_scenario.eq(FILTER["resource_scenario"])
                & pairwise.strategy_id.eq("vulnerability-first")
                & pairwise.reference_strategy.eq(ref)
                & pairwise.metric.eq(field), "paired_mean_difference"]
            if not match.empty:
                assert len(match) == 1
                observed = row["mean_vulnerability_first_minus_reference_hr"]
                assert abs(float(match.iloc[0])-observed) < 1e-10, (ref, field)
                pairwise_checks.append(dict(reference_strategy=ref, outcome=field,
                                            raw_mean=observed, saved_mean=float(match.iloc[0])))

    width_pt, height_pt = 300.0, 141.0
    fig = plt.figure(figsize=(width_pt/72, height_pt/72))
    ax = fig.add_axes([.34, .23, .64, .69])
    x_positions = []
    for y, (field, label) in enumerate(OUTCOMES):
        for j, ref in enumerate(REFERENCES):
            row = next(r for r in comparison_rows if r["reference_strategy"] == ref and r["outcome"] == field)
            mean, p05, p95 = (row["mean_vulnerability_first_minus_reference_hr"], row["p05"], row["p95"])
            yy = y + (j-1)*.20
            ax.errorbar(mean, yy, xerr=[[mean-p05], [p95-mean]], fmt=MARKERS[ref],
                        color=REFERENCE_COLORS[ref], markersize=3.0, linewidth=.7, capsize=1.3)
            x_positions.extend([p05, p95])
    ax.axvline(0, color="#555555", linewidth=.65, linestyle="--")
    ax.set_yticks(range(len(OUTCOMES)), [label for _, label in OUTCOMES])
    ax.set_ylim(len(OUTCOMES)-.5, -.5)
    lim = max(4.5, float(np.ceil(max(abs(min(x_positions)), abs(max(x_positions)))*2)/2))
    ax.set_xlim(-lim, lim)
    ax.set_xlabel("Vulnerability-first minus reference (h)")
    ax.grid(axis="x", color="#e5e5e5", linewidth=.4)
    ax.spines[["top", "right"]].set_visible(False)
    panel = BytesIO()
    fig.savefig(panel, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)

    original = fitz.open(stream=source_pdf, filetype="pdf")
    assert len(original) == 1
    page = original[0]
    w, h = page.rect.width, page.rect.height
    out = fitz.open()
    target = out.new_page(width=w, height=h)
    # Retain original A/B, C/D headings and legend, D, and E as source vector clips.
    preserved_clips = [fitz.Rect(0, 0, w, 260), fitz.Rect(0, 260, w, 303),
                       fitz.Rect(370, 303, w, 445), fitz.Rect(0, 445, w, h)]
    for clip in preserved_clips:
        target.show_pdf_page(clip, original, 0, clip=clip)
    c_rect = fitz.Rect(65, 303, 370, 445)
    target.show_pdf_page(c_rect, fitz.open(stream=panel.getvalue(), filetype="pdf"), 0)
    out.set_metadata({"title": "Figure 5. Distributional consequences",
                      "subject": "Signed and absolute vulnerability-gap outcomes across matched strategies"})
    original.close()
    qa = {
        "source_pdf_sha256": __import__("hashlib").sha256(source_pdf).hexdigest(),
        "source_A_B_D_E_and_map_vectors_preserved": True,
        "source_C_panel_replaced_with_vector_plot_from_realization_rows": True,
        "n_vulnerability_first_rows": len(v),
        "n_matched_realization_ids": int(v.realization_id.nunique()),
        "physical_sample_hash_unique_count": int(v.physical_sample_hash.nunique()),
        "comparison_rows": comparison_rows,
        "pairwise_summary_mean_check_rows": pairwise_checks,
        "pairwise_summary_mean_checks_passed": len(pairwise_checks) > 0,
        "uncertainty": "5th-95th quantiles of paired realization differences, not confidence intervals",
        "panel_C_row_order": [label for _, label in OUTCOMES],
        "panel_C_xlim_hr": [-lim, lim],
        "ordinary_plot_values_or_strategy_results_changed": False,
    }
    return out.tobytes(garbage=4, deflate=True, no_new_id=True), qa


def figure3_decomposition_qa(gate_components, primary):
    aggregate = gate_components.loc[gate_components.resource_scenario.eq("C57_D1")
                                    & gate_components.strategy_id.eq("unconstrained")].copy()
    raw = primary.loc[primary.resource_scenario.eq("C57_D1")
                      & primary.mapping.eq("M1_UTILITY_003")
                      & primary.gate.eq("G1_BASELINE_050")
                      & primary.strategy_id.eq("unconstrained")].copy()
    assert set(aggregate.hazard) == set(raw.hazard) == {"LongBeach", "SanFernando", "Northridge", "2pc50"}
    result = []
    fields = {
        "L_self_population_mass_weighted_hr": ("self_mean_hr", "share_substation_damage"),
        "L_threshold_population_mass_weighted_hr": ("threshold_mean_hr", "share_functionality_threshold"),
        "L_source_population_mass_weighted_hr": ("source_mean_hr", "share_source_path"),
        "L_total_population_mass_weighted_hr": ("total_mean_hr", None),
    }
    for hazard, group in raw.groupby("hazard", sort=True):
        assert len(group) == 1000 and group.realization_id.is_unique
        a = aggregate.loc[aggregate.hazard.eq(hazard)].iloc[0]
        row = {"hazard": hazard, "strategy_id": "unconstrained", "n": len(group)}
        component_sum = (group["L_self_population_mass_weighted_hr"]
                         + group["L_threshold_population_mass_weighted_hr"]
                         + group["L_source_population_mass_weighted_hr"])
        error = float(np.max(np.abs(component_sum-group["L_total_population_mass_weighted_hr"])))
        assert error < 1e-10, (hazard, error)
        for source_field, (mean_field, share_field) in fields.items():
            mean = float(group[source_field].mean())
            assert abs(mean-float(a[mean_field])) < 1e-10, (hazard, mean_field)
            row[mean_field] = mean
            if share_field:
                row[share_field] = mean/float(group["L_total_population_mass_weighted_hr"].mean())
        row["component_sum_max_abs_error_hr"] = error
        result.append(row)
    return result
