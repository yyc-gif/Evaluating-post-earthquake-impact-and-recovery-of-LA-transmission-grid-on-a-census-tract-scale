"""Finish July-style display panels from frozen formal summaries only.

No damage, scheduling, GA, or service model is executed here. This file uses
Project_Visualizer's publication sizing, style, labels, maps, and export path.
"""
from pathlib import Path
import shutil
import sys
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import Project_Visualizer as july

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
FORMAL = ROOT / "Formal_Experiment_20260923"
SUITE = ROOT.parent / "LA_Grid_Revised_Suite_20260925"
S3 = SUITE / "Stage 3 Output_expanded"
S5 = SUITE / "Stage 5 Output_expanded"
S6 = SUITE / "Stage 6 Output_expanded"
SENS = SUITE / "Sensitivity Output_clean"
MAIN = SUITE / "Submission_Package" / "Main_Figures"
SUPP = SUITE / "Submission_Package" / "Supplementary_Figures"
for p in (S3, S5, S6, SENS, MAIN, SUPP): p.mkdir(parents=True, exist_ok=True)
july.OUTPUT_ROOT = str(SUITE)
july.apply_publication_style()
HAZARDS = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
POLICIES = ["centrality-first", "impact-first", "betweenness-first", "degree-first",
            "closeness-first", "hospital-first", "random", "vulnerability-first"]
july.STAGE6_SHARED_LINE_STYLES["vulnerability-first"] = {
    "color": "#a65628", "ls": "-", "lw_recovery": 1.08,
    "lw_topology": .98, "alpha_recovery": .85, "alpha_topology": .82, "zorder": 9}
july.STAGE6_RECOVERY_STYLE_CONFIG["vulnerability-first"] = {
    "label": "Vulnerability First (Q4)", **july._stage6_line_style("vulnerability-first")}

def export(fig, folder, name):
    july.save_plot(fig, str(folder), name + ".png")

def copy_panel(src, dst):
    for ext in (".png", ".pdf"):
        a, b = src.with_suffix(ext), dst.with_suffix(ext)
        assert a.is_file(), a
        shutil.copy2(a, b)

summ = pd.read_csv(S6 / "ALL_DISTINCT_STRATEGIES_BY_HAZARD.csv")
base = pd.read_csv(FORMAL / "Formal_Results" / "PAIRED_STRATEGY_EFFECTS.csv")
vuln = pd.read_csv(FORMAL / "Equity_Amendment" / "VULNERABILITY_PAIRWISE_EFFECTS.csv")
effects = pd.concat([base, vuln], ignore_index=True)
effects = effects[(effects.resource_scenario == "C57_D1") &
                  (effects.reference_strategy == "hospital-first")]
formal_rows = pd.read_parquet(FORMAL / "Formal_Results" /
                              "PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet")
formal_rows = formal_rows[(formal_rows.resource_scenario == "C57_D1") &
                          (formal_rows.mapping == "M1_UTILITY_003") &
                          (formal_rows.gate == "G1_BASELINE_050")]
vuln_rows = pd.read_parquet(FORMAL / "Equity_Amendment" /
                           "VULNERABILITY_PRIMARY_SUMMARY.parquet")
vuln_rows = vuln_rows[vuln_rows.resource_scenario == "C57_D1"]
metric_specs = [
    ("population_resolved_mass_weighted_burden_hr", "Population cumulative burden", "h"),
    ("population_T80_hr", "Population T80", "h"),
    ("hospital_mean_normalized_burden_hr", "Hospital-tract burden", "h"),
    ("burden_Q4_hr", "Change in Q4 burden relative to Hospital First", "h"),
    ("L_source_population_mass_weighted_hr", "Source-path burden", "h"),
]
for hazard in HAZARDS:
    for metric, title, unit in metric_specs:
        # Effect/interval is a paired realization comparison, never an
        # unpaired SD bar. If the frozen paired table lacks this metric,
        # leave the original absolute-data panel as the display candidate.
        d = effects[(effects.hazard == hazard) & (effects.metric == metric)]
        if set(POLICIES) - {"hospital-first"} - set(d.strategy_id):
            continue
        rows = d.set_index("strategy_id").reindex([s for s in POLICIES if s != "hospital-first"])
        fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
        ys = np.arange(len(rows))
        for i, (strategy, row) in enumerate(rows.iterrows()):
            style = july.STAGE6_RECOVERY_STYLE_CONFIG[strategy]
            lo, hi = row.bootstrap_ci_low, row.bootstrap_ci_high
            mean = row.paired_mean_difference
            ax.plot([lo, hi], [i, i], color=style["color"], lw=1.2)
            ax.plot(mean, i, marker="o", color=style["color"], ms=3)
        ax.axvline(0, color="0.35", lw=.6, ls="--")
        ax.set_yticks(ys, [july.STAGE6_RECOVERY_STYLE_CONFIG[s]["label"] for s in rows.index])
        ax.invert_yaxis()
        july.style_axis(ax, title=f"{hazard}: {title}",
                        xlabel=f"Paired difference from Hospital First ({unit}); 95% bootstrap CI")
        ax.grid(axis="y", visible=False)
        export(fig, S6, f"vis_stage6_paired_{metric}_{hazard}")
    # Absolute group burdens must accompany the gap/Gini interpretation.
    d = summ[summ.hazard == hazard].set_index("strategy_id").reindex(POLICIES)
    fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
    x = np.arange(1, 5)
    for s, row in d.iterrows():
        st = july.STAGE6_RECOVERY_STYLE_CONFIG[s]
        y = [row[f"burden_Q{i}_hr_mean"] for i in x]
        ax.plot(x, y, marker="o", ms=2.6, color=st["color"], ls=st["ls"],
                lw=st["lw"], label=st["label"])
    ax.set_xticks(x, ["Q1", "Q2", "Q3", "Q4"])
    july.style_axis(ax, title=f"{hazard}: absolute vulnerability-group burden",
                    xlabel="SOVI quartile (Q4 highest)",
                    ylabel="Population-weighted normalized burden (h)")
    lg = ax.legend(ncol=2, frameon=False, loc="best"); july.format_legend(lg)
    export(fig, S6, f"vis_stage6_absolute_group_burdens_{hazard}")
    fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
    for offset,s in ((-.10,"hospital-first"),(0,"impact-first"),(.10,"vulnerability-first")):
        subset = (vuln_rows if s == "vulnerability-first" else formal_rows)
        subset = subset[(subset.hazard == hazard) & (subset.strategy_id == s)]
        assert len(subset) == 1000, (hazard,s,len(subset))
        means = [subset[f"burden_Q{i}_hr"].mean() for i in x]
        lo = [subset[f"burden_Q{i}_hr"].quantile(.05) for i in x]
        hi = [subset[f"burden_Q{i}_hr"].quantile(.95) for i in x]
        st = july.STAGE6_RECOVERY_STYLE_CONFIG[s]
        ax.errorbar(x+offset, means,
                    yerr=[np.array(means)-lo, np.array(hi)-means],
                    color=st["color"], linestyle=st["ls"], linewidth=1.0,
                    marker="o", markersize=2.5, capsize=1.4, label=st["label"])
    ax.set_xticks(x, ["Q1", "Q2", "Q3", "Q4"])
    july.style_axis(ax, title=f"{hazard}: absolute group burden and realization spread",
                    xlabel="SOVI quartile (Q4 highest)",
                    ylabel="Population-weighted normalized burden (h)")
    lg = ax.legend(frameon=False); july.format_legend(lg)
    export(fig, S6, f"vis_stage6_group_burden_uncertainty_{hazard}")
    fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
    for s,row in d.iterrows():
        st = july.STAGE6_RECOVERY_STYLE_CONFIG[s]
        ax.scatter(row.population_resolved_mass_weighted_burden_hr_mean,
                   row.burden_Q4_hr_mean, s=25, color=st["color"], label=st["label"])
    july.style_axis(ax, title=f"{hazard}: system burden and Q4 burden",
                    xlabel="Population-resolved-mass cumulative burden (h)",
                    ylabel="Q4 absolute burden (h)")
    lg = ax.legend(ncol=2, frameon=False, loc="best"); july.format_legend(lg)
    export(fig, S6, f"vis_stage6_equity_efficiency_{hazard}")

# Source-gate decomposition in the full eight-strategy comparison.
gate = pd.read_csv(FORMAL / "Formal_Reviewer_Results" / "FORMAL_GATE_COMPONENTS.csv")
v_gate = vuln_rows[(vuln_rows.mapping == "M1_UTILITY_003") &
                   (vuln_rows.gate == "G1_BASELINE_050") &
                   (vuln_rows.resource_scenario == "C57_D1")]
assert len(v_gate) == 4000
v_component_cols = ["L_self_population_mass_weighted_hr",
                    "L_threshold_population_mass_weighted_hr",
                    "L_source_population_mass_weighted_hr"]
assert np.isfinite(v_gate[v_component_cols +
                           ["L_total_population_mass_weighted_hr"]].to_numpy(float)).all()
assert np.allclose(v_gate[v_component_cols].sum(axis=1),
                   v_gate.L_total_population_mass_weighted_hr, atol=1e-9)
assert np.allclose(v_gate.L_total_population_mass_weighted_hr,
                   v_gate.population_resolved_mass_weighted_burden_hr, atol=1e-9)
extra = []
for hazard, rows in v_gate.groupby("hazard"):
    assert len(rows) == 1000
    values = rows[v_component_cols].mean()
    extra.append({"hazard":hazard,"resource_scenario":"C57_D1",
                  "strategy_id":"vulnerability-first",
                  "self_mean_hr":values.iloc[0],"threshold_mean_hr":values.iloc[1],
                  "source_mean_hr":values.iloc[2],
                  "total_mean_hr":rows.L_total_population_mass_weighted_hr.mean()})
gate = pd.concat([gate, pd.DataFrame(extra)], ignore_index=True)
gate.to_csv(S3 / "LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv",index=False)
for hazard in HAZARDS:
    d = gate[(gate.hazard == hazard) & (gate.resource_scenario == "C57_D1")]
    assert set(POLICIES).issubset(d.strategy_id)
    d = d.set_index("strategy_id").reindex(POLICIES)
    cols = ["self_mean_hr", "threshold_mean_hr", "source_mean_hr", "total_mean_hr"]
    assert np.isfinite(d[cols].to_numpy(float)).all(), hazard
    assert np.allclose(d[cols[:3]].sum(axis=1), d.total_mean_hr, atol=1e-9), hazard
    fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
    x = np.arange(len(POLICIES))
    bottom = np.zeros(len(x))
    for col, lab, color in (("self_mean_hr", "Own-station damage", "#729ece"),
                            ("threshold_mean_hr", "Functional threshold", "#f6a03c"),
                            ("source_mean_hr", "Source-path disconnection", "#b22222")):
        y = d[col].to_numpy(float)
        ax.bar(x, y, bottom=bottom, color=color, label=lab, linewidth=.5)
        bottom += y
    ax.set_xticks(x, [july.STAGE6_RECOVERY_STYLE_CONFIG[s]["label"] for s in POLICIES],
                  rotation=35, ha="right")
    july.style_axis(ax, title=f"{hazard}: cumulative modeled service-loss components",
                    ylabel="Population-resolved-mass burden (h)")
    lg = ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.20))
    july.format_legend(lg)
    export(fig, S3, f"vis_stage3_loss_decomposition_{hazard}")

# The July map function supplies study-area framing and colorbar formatting.
geo = gpd.read_file(ROOT / "Data" / "LA_Tracts_With_Population.shp")
geo["tract_id"] = geo.GEOID.astype(str).str.zfill(11)
tract_set = set(pd.read_csv(ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv",
                            usecols=["tract_id"], dtype={"tract_id": str}).tract_id)
geo = geo[geo.tract_id.isin(tract_set)].copy()
assert len(geo) == 2315
source = pd.read_csv(FORMAL / "Formal_Reviewer_Results" / "FORMAL_SOURCE_LOSS_BY_TRACT.csv",
                     dtype={"tract_id": str})
for hazard in HAZARDS:
    d = source[(source.hazard == hazard) & (source.resource_scenario == "C57_D1") &
               (source.strategy_id == "hospital-first")].set_index("tract_id")
    assert len(d) == 2315
    july.plot_map(geo.copy(), d.mean_source_loss_hr,
                  f"{hazard}: source-path loss", str(S3),
                  f"vis_stage3_source_loss_map_{hazard}.png", label="Source-path loss (h)",
                  cmap="OrRd", figure_role="PANEL_MAP_TALL")
shift = pd.read_parquet(FORMAL / "Formal_Results" / "TRACT_MAPPING_SHIFT.parquet")
map_display_metadata = []
for hazard in HAZARDS:
    d = shift[(shift.hazard == hazard) & (shift.strategy_id == "hospital-first")].set_index("tract_id")
    assert len(d) == 2315
    span = float(np.nanpercentile(np.abs(d.mean_M1_minus_M0_burden_hr), 99))
    map_display_metadata.append({"panel":f"vis_mapping_shift_magnitude_{hazard}",
                                 "display_clip":"symmetric 99th percentile of absolute paired mean difference",
                                 "display_min_hr":-span,"display_max_hr":span,
                                 "actual_min_hr":d.mean_M1_minus_M0_burden_hr.min(),
                                 "actual_max_hr":d.mean_M1_minus_M0_burden_hr.max()})
    july.plot_map(geo.copy(), d.mean_M1_minus_M0_burden_hr,
                  f"{hazard}: M1 − M0 burden", str(SENS),
                  f"vis_mapping_shift_magnitude_{hazard}.png", label="Paired burden shift (h)",
                  cmap="coolwarm", vmin=-span, vmax=span, cmap_low=0, figure_role="PANEL_MAP_TALL")

tract_effect = pd.read_parquet(FORMAL / "Equity_Amendment" / "VULNERABILITY_TRACT_EFFECTS.parquet")
for reference in ("hospital-first", "impact-first"):
    d = tract_effect[(tract_effect.hazard == "2pc50") &
                     (tract_effect.reference_strategy == reference)].set_index("tract_id")
    assert len(d) == 2315
    span = float(np.nanpercentile(np.abs(d.mean_paired_delta_burden_hr), 99))
    map_display_metadata.append({"panel":f"vis_stage6_vulnerability_effect_magnitude_vs_{reference}",
                                 "display_clip":"symmetric 99th percentile of absolute paired mean difference",
                                 "display_min_hr":-span,"display_max_hr":span,
                                 "actual_min_hr":d.mean_paired_delta_burden_hr.min(),
                                 "actual_max_hr":d.mean_paired_delta_burden_hr.max()})
    july.plot_map(geo.copy(), d.mean_paired_delta_burden_hr,
                  f"Vulnerability First − {reference}", str(S6),
                  f"vis_stage6_vulnerability_effect_magnitude_vs_{reference}.png",
                  label="Paired mean burden difference (h)", cmap="coolwarm",
                  vmin=-span, vmax=span, cmap_low=0, figure_role="PANEL_MAP_TALL")
pd.DataFrame(map_display_metadata).to_csv(SENS/"SPATIAL_DISPLAY_SCALE_METADATA.csv",index=False)

# Formal GA histories (search mean and retained best) are the revised
# equivalent of July's GA convergence display. Incumbent is explicit.
history_dir = FORMAL / "Stage 5 Output_expanded"
fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
for seed in (42, 43, 44, 45, 46):
    d = pd.read_csv(history_dir / f"GA_HISTORY_2pc50_{seed}.csv")
    xcol = "generation" if "generation" in d else d.columns[0]
    best = next(c for c in d if "best_so_far" in c.lower())
    ax.plot(d[xcol], d[best], lw=1.0, label=f"Seed {seed}")
inc = pd.read_csv(history_dir / "INCUMBENT_DIRECT_SCORES_2pc50.csv")
score = float(inc["planning_fitness"].max())
ax.axhline(score, color="0.2", ls="--", lw=.8, label="Impact-first incumbent")
july.style_axis(ax, title="Direct-community GA: retained fitness across five seeds",
                xlabel="Generation", ylabel="Fitness = negative mean population burden")
lg = ax.legend(frameon=False); july.format_legend(lg)
export(fig, S5, "vis_stage5_five_seed_convergence")

# Resource response keeps crew count and repair-duration scaling separate.
resource = pd.read_csv(FORMAL / "Formal_Reviewer_Results" / "FORMAL_RESOURCE_EFFECTS.csv")
vuln_resource = pd.read_parquet(FORMAL / "Equity_Amendment" / "VULNERABILITY_PRIMARY_SUMMARY.parquet")
for metric in ("population_resolved_mass_weighted_burden_hr", "burden_Q4_hr", "L_source_population_mass_weighted_hr"):
    readable = {"population_resolved_mass_weighted_burden_hr":"Population cumulative burden",
                "burden_Q4_hr":"Q4 absolute burden",
                "L_source_population_mass_weighted_hr":"Source-path cumulative burden"}[metric]
    for kind, cases, xs, xlabel in (
        ("crew", ["C29_D1", "C57_D1", "C86_D1", "C114_D1"], [29, 57, 86, 114], "Available crews"),
        ("duration", ["C57_D075", "C57_D1", "C57_D125", "C57_D150"], [.75, 1, 1.25, 1.5], "Repair-duration scale")):
        fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
        for s in POLICIES:
            vals = []
            for case in cases:
                if s == "vulnerability-first":
                    d = vuln_resource[(vuln_resource.resource_scenario == case) &
                                      (vuln_resource.hazard == "2pc50")]
                    vals.append(float(d[metric].mean()))
                elif case == "C57_D1":
                    d = summ[(summ.hazard == "2pc50") & (summ.strategy_id == s)]
                    vals.append(float(d[f"{metric}_mean"].iloc[0]))
                else:
                    d = resource[(resource.resource_scenario == case) &
                                 (resource.strategy_id == s) & (resource.metric == metric)]
                    if len(d) == 1:
                        vals.append(float(d.target_mean.iloc[0]))
                    else:
                        archived = pd.read_parquet(FORMAL / "Formal_Offline_Evaluation" /
                                                   f"2pc50__{case}__{s}__SUMMARY.parquet")
                        assert len(archived) == 1000, (case, s)
                        vals.append(float(archived[metric].mean()))
            st = july.STAGE6_RECOVERY_STYLE_CONFIG[s]
            ax.plot(xs, vals, marker="o", ms=2.4, color=st["color"], ls=st["ls"],
                    lw=st["lw"], label=st["label"])
        ax.set_xticks(xs, [str(n) for n in xs] if kind == "crew" else
                      [f"{n:.2f}" for n in xs])
        july.style_axis(ax, title=f"2pc50: {readable} — {kind} OFAT",
                        xlabel=xlabel + " (one factor at a time)", ylabel="Cumulative burden (h)")
        lg = ax.legend(ncol=2, frameon=False); july.format_legend(lg)
        export(fig, SENS, f"vis_resource_{kind}_{metric}")

print("Finished paired, distributional, source, mapping, GA and resource panels.")

# Time-varying loss components from archived event states. The hourly grid is
# for display only; the formal integrals still use the exact event intervals.
from scipy import sparse
mapping = pd.read_csv(ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv",
                      dtype={"tract_id": str, "substation_id": str})
tracts = sorted(mapping.tract_id.unique())
stations = list(np.load(FORMAL / "Stage 1 Output_expanded" /
                        "physical_inputs_2pc50.npz")["station_ids"].astype(str))
ri = {v:i for i,v in enumerate(tracts)}
ci = {v:i for i,v in enumerate(stations)}
W = sparse.csr_matrix((mapping.weight.astype(float),
                       ([ri[v] for v in mapping.tract_id],
                        [ci[v] for v in mapping.substation_id])), shape=(2315,92))
meta = pd.read_csv(ROOT / "R1_Comment1_July92_Utility_Constraint" /
                   "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
                   dtype={"tract_id": str}).set_index("tract_id").reindex(tracts)
p = meta.population.to_numpy(float)
station_mass = np.asarray(W.T @ p).ravel()
station_mass /= station_mass.sum()
hours = np.arange(481)
temporal_records = []
for hazard in HAZARDS:
    for policy in ("hospital-first", "impact-first", "vulnerability-first"):
        folder = (FORMAL / "Equity_Amendment" / "T" / hazard / "C57_D1"
                  if policy == "vulnerability-first" else
                  FORMAL / "Formal_Trajectories" / hazard / "C57_D1" / policy)
        files = sorted(folder.glob("*.npz"))
        assert len(files) == 1000, (hazard, policy)
        aggregate = np.zeros((481,3))
        for path in files:
            with np.load(path) as z:
                ix = np.clip(np.searchsorted(z["event_time_hr"], hours, side="right") - 1,
                             0, len(z["event_time_hr"]) - 1)
                aggregate[:,0] += z["L_self"][ix] @ station_mass
                aggregate[:,1] += z["L_threshold"][ix] @ station_mass
                aggregate[:,2] += z["L_source"][ix] @ station_mass
        aggregate /= 1000
        for i,t in enumerate(hours):
            temporal_records.append((hazard,policy,t,*aggregate[i]))
        if policy == "hospital-first":
            fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
            for k,(label,color) in enumerate((("Own-station loss","#729ece"),
                                               ("Threshold loss","#f6a03c"),
                                               ("Source-path loss","#b22222"))):
                ax.step(hours, aggregate[:,k], where="post", label=label,
                        color=color, lw=1.2)
            active = np.flatnonzero(aggregate.sum(axis=1) > .01)
            ax.set_xlim(0, min(480, max(24,int(active[-1]+8)) if len(active) else 24))
            july.style_axis(ax, title=f"{hazard}: service-loss mechanism over time",
                            xlabel="Time after event (h)", ylabel="Population-weighted deficit")
            lg = ax.legend(frameon=False); july.format_legend(lg)
            export(fig, S3, f"vis_stage3_temporal_loss_components_{hazard}")
pd.DataFrame(temporal_records, columns=["hazard","strategy_id","time_hr",
              "mean_self_deficit","mean_threshold_deficit","mean_source_deficit"]).to_csv(
                  S3 / "SOURCE_LOSS_DISPLAY_TIME_SERIES.csv", index=False)

# Existing paired realization rows also support the source-path burden
# comparison. The interval here describes realization spread, not a CI of
# the paired mean; the other paired panels retain their frozen bootstrap CIs.
source_effect_rows = []
source_metric = "L_source_population_mass_weighted_hr"
for hazard in HAZARDS:
    ref = formal_rows[(formal_rows.hazard == hazard) &
                      (formal_rows.strategy_id == "hospital-first")].set_index("realization_id").sort_index()
    fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
    others = [s for s in POLICIES if s != "hospital-first"]
    for k,s in enumerate(others):
        pool = vuln_rows if s == "vulnerability-first" else formal_rows
        target = pool[(pool.hazard == hazard) &
                      (pool.strategy_id == s)].set_index("realization_id").sort_index()
        assert len(ref) == len(target) == 1000
        assert ref.index.equals(target.index), (hazard,s)
        delta = (target[source_metric]-ref[source_metric]).to_numpy(float)
        mean,low,high = np.mean(delta),np.quantile(delta,.05),np.quantile(delta,.95)
        source_effect_rows.append((hazard,s,mean,low,high))
        color = july.STAGE6_RECOVERY_STYLE_CONFIG[s]["color"]
        ax.plot([low,high],[k,k],color=color,lw=1.2)
        ax.plot(mean,k,marker="o",color=color,ms=3)
    ax.axvline(0,color="0.35",lw=.6,ls="--")
    ax.set_yticks(np.arange(len(others)),
                  [july.STAGE6_RECOVERY_STYLE_CONFIG[s]["label"] for s in others])
    ax.invert_yaxis()
    july.style_axis(ax,title=f"{hazard}: paired source-path burden difference",
                    xlabel="Difference from Hospital First (h); 5–95% paired realization range")
    ax.grid(axis="y",visible=False)
    export(fig,S6,f"vis_stage6_paired_source_loss_{hazard}")
pd.DataFrame(source_effect_rows,columns=["hazard","strategy_id","mean_paired_delta_hr",
              "p05_paired_delta_hr","p95_paired_delta_hr"]).to_csv(
                  S6/"SOURCE_PATH_PAIRED_EFFECT_DISPLAY.csv",index=False)

# A representative frozen task-event ledger can be shown through the original
# July Gantt function without invoking dispatch. The caption identifies its
# single-realization status; the inferential comparisons remain 1,000 paired runs.
stage4 = SUITE / "Stage 4 Output_expanded"
for policy in ("hospital-first", "impact-first", "vulnerability-first"):
    folder = (FORMAL / "Equity_Amendment" / "T" / "2pc50" / "C57_D1"
              if policy == "vulnerability-first" else
              FORMAL / "Formal_Trajectories" / "2pc50" / "C57_D1" / policy)
    taskfile = next(iter(sorted(folder.glob("*evaluation_0000*TASK_EVENTS.csv"))), None)
    assert taskfile is not None, (policy,folder)
    tasks = pd.read_csv(taskfile, dtype={"task_id":str})
    july.plot_gantt_chart(tasks.rename(columns={
        "crew_index":"Crew_ID", "arrival_hr":"Start_Time",
        "realized_duration_hr":"Duration", "travel_hr":"Travel_Time"}),
        str(stage4), f"2pc50_{policy}_evaluation_0000", max_crews=30,
        stage_label="stage4")

# External candidate consistency is conditional on official candidates being
# representable among the retained 92 stations (337 strict-SCE tracts).
bench = pd.read_csv(ROOT / "R1_Comment1_2_External_Evidence_20260922" /
                    "SCE_MAPPING_BENCHMARK_SUMMARY.csv")
bench = bench[(bench.version == "NEW_20260922") &
              (bench.candidate_kind == "direct_site") &
              (bench.mapping.isin(["JULY_BASELINE_92","JULY_UTILITY_CONSTRAINED_92"]))]
assert len(bench) == 2 and set(bench.tract_count) == {337}
fig, ax = plt.subplots(figsize=july.get_figsize("PANEL_FULLROW", height_cm=7.0))
old = bench.set_index("mapping").loc["JULY_BASELINE_92"]
new = bench.set_index("mapping").loc["JULY_UTILITY_CONSTRAINED_92"]
for y,(metric,label) in enumerate((("any_match","Any candidate"),
                                   ("top1","Top one"),("top3","Top three"))):
    v0,v1 = float(old[metric]),float(new[metric])
    ax.plot([v0,v1],[y,y],color="0.60",lw=1.0)
    ax.scatter([v0],[y],color="#4c78a8",s=22,zorder=3,
               label="July M0" if y==0 else None)
    ax.scatter([v1],[y],color="#b22222",s=22,zorder=3,
               label="Utility-compatible M1" if y==0 else None)
    ax.text(v0-.005,y+.19,f"{v0:.1%} ({round(v0*337)})",ha="right",fontsize=july.FS_ANNOTATION)
    ax.text(v1+.005,y+.19,f"{v1:.1%} ({round(v1*337)})",ha="left",fontsize=july.FS_ANNOTATION)
ax.set_yticks(range(3),["Any candidate","Top one","Top three"])
ax.set_ylim(2.48,-.48); ax.set_xlim(.82,1.01)
ax.set_xticks([.825,.85,.875,.90,.925,.95,.975,1.0])
july.style_axis(ax,title="SCE public candidates: 337 representable strict-SCE tracts",
                xlabel="Fraction matching the represented candidate set")
lg=ax.legend(frameon=False,loc="lower left");july.format_legend(lg)
export(fig,SENS,"vis_sce_candidate_benchmark")

# Production M1 cutoff sensitivity, with the same fixed decision and samples.
mapping_effects=pd.read_csv(FORMAL/"Formal_Reviewer_Results"/"FORMAL_MAPPING_EFFECTS.csv")
fig,ax=plt.subplots(figsize=july.get_figsize("PANEL_FULLROW",height_cm=7.0))
for family,color in (("M1","#b22222"),):
    values=[]
    for comp in (f"2pc50_cutoff_{family}_none",f"2pc50_cutoff_{family}_001"):
        d=mapping_effects[(mapping_effects.comparison==comp)&
            (mapping_effects.strategy_id=="hospital-first")&
            (mapping_effects.metric=="population_resolved_mass_weighted_burden_hr")]
        assert len(d)==1,(comp,len(d))
        values.append(float(d.mean_delta.iloc[0]))
    values.append(0.0)
    ax.plot([0,.01,.03],values,marker="o",ms=3,lw=1.2,color=color,label="Utility-compatible M1")
ax.axhline(0,color="0.4",ls="--",lw=.6)
ax.set_xticks([0,.01,.03],["No cutoff","1%","3% baseline"])
july.style_axis(ax,title="2pc50: cutoff effect with fixed Hospital First decision",
                xlabel="Candidate-weight cutoff",ylabel="Change in population cumulative burden from M1 3% (h)")
lg=ax.legend(frameon=False);july.format_legend(lg)
export(fig,SENS,"vis_mapping_cutoff_response")

# Dynamic path concentration from the formal diagnostic archive.
dyn=pd.read_csv(FORMAL/"Formal_Reviewer_Results"/"FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv")
d=dyn[(dyn.resource_scenario=="C57_D1")&(dyn.strategy_id=="hospital-first")]
d=d.set_index("hazard").reindex(HAZARDS)
assert len(d)==4 and d["top1_fraction__mean"].notna().all()
fig,ax=plt.subplots(figsize=july.get_figsize("PANEL_FULLROW",height_cm=7.0))
for col,label,color in (("top1_fraction__mean","Largest station","#b22222"),
                         ("top5_fraction__mean","Top five stations","#f39c34"),
                         ("static_eight_fraction__mean","Eight static single-path stations","#4c78a8")):
    ax.plot(range(4),d[col],marker="o",ms=3,lw=1.2,color=color,label=label)
ax.set_xticks(range(4),HAZARDS)
ax.set_ylim(0,1.05)
july.style_axis(ax,title="Source-path loss concentration by hazard",
                ylabel="Mean share of source-path cumulative burden")
lg=ax.legend(frameon=False);july.format_legend(lg)
export(fig,SENS,"vis_dynamic_source_loss_concentration")

# Gate alternatives are frozen offline evaluations of the same Hospital-first
# trajectories. These four bars are alternative gate assumptions, not the
# additive components of the production gate shown in Stage 3.
offline = pd.read_parquet(FORMAL/"Formal_Offline_Evaluation"/
                          "2pc50__C57_D1__hospital-first__SUMMARY.parquet")
gate_ids = ["G0_NO_GATE","G2_RELAXED_005","G1_BASELINE_050","G3_STRICT_075"]
gate_names = ["G0: no gate","G2: threshold 0.05","G1: production 0.50",
              "G3: threshold 0.75"]
g = offline[(offline.mapping=="M1_UTILITY_003") &
            (offline.comparison_domain=="mapping_native_domain") &
            (offline.gate.isin(gate_ids))]
assert len(g)==4000 and all(g.groupby("gate").size().reindex(gate_ids)==1000)
gm = g.groupby("gate").population_resolved_mass_weighted_burden_hr.agg(["mean","median"])
gm = gm.reindex(gate_ids)
fig,ax=plt.subplots(figsize=july.get_figsize("PANEL_FULLROW",height_cm=7.0))
ax.bar(np.arange(4),gm["mean"],color=["#4c78a8","#72b7b2","#b22222","#f39c34"],
       width=.55,edgecolor="0.35",linewidth=.5)
ax.set_xticks(np.arange(4),gate_names)
july.style_axis(ax,title="2pc50: gate assumption and community burden",
                ylabel="Population cumulative burden (h)")
export(fig,SENS,"vis_gate_robustness_2pc50_hospital_first")
gm.reset_index().to_csv(SENS/"GATE_ROBUSTNESS_DISPLAY.csv",index=False)

# The reviewer-facing trade-off figure keeps the paired burden differences,
# continuous population-weighted tract effects, and system/hospital costs.
eq = vuln[(vuln.hazard=="2pc50") &
          (vuln.reference_strategy=="hospital-first") &
          (vuln.resource_scenario=="C57_D1")].set_index("metric")
tract_effects=pd.read_parquet(FORMAL/"Equity_Amendment"/
                              "VULNERABILITY_TRACT_EFFECTS.parquet")
tract_effects=tract_effects[(tract_effects.hazard=="2pc50") &
                            (tract_effects.reference_strategy=="hospital-first")]
assert tract_effects.tract_id.nunique()==2315

def weighted_quantiles(values, weights, probabilities):
    order=np.argsort(values,kind="stable")
    values=np.asarray(values)[order]
    weights=np.asarray(weights)[order]
    cumulative=(np.cumsum(weights)-.5*weights)/weights.sum()
    return np.interp(probabilities,cumulative,values,left=values[0],right=values[-1])

distribution=[]
for scope in ["all","Q4"]:
    subset=tract_effects if scope=="all" else tract_effects[tract_effects.quartile=="Q4"]
    subset=subset[np.isfinite(subset.mean_paired_delta_burden_hr) &
                  np.isfinite(subset.population) & (subset.population>0)]
    assert len(subset)>0
    values=subset.mean_paired_delta_burden_hr.to_numpy()
    weights=subset.population.to_numpy()
    q=weighted_quantiles(values,weights,[.05,.25,.5,.75,.95])
    distribution.append(dict(scope=scope,tract_count=len(subset),population=weights.sum(),
                             population_weighted_mean_hr=np.average(values,weights=weights),
                             **{f"weighted_q{p}_hr":v for p,v in zip([5,25,50,75,95],q)}))
distribution=pd.DataFrame(distribution).set_index("scope")
fig=plt.figure(figsize=july.get_figsize("COMPOSITE_FULL_DEFAULT",height_cm=13.0))
gs=fig.add_gridspec(2,2,height_ratios=[1.15,1],hspace=.52,wspace=.47)
ax_a=fig.add_subplot(gs[0,:]); ax_b=fig.add_subplot(gs[1,0]); ax_c=fig.add_subplot(gs[1,1])
group_keys=[f"burden_Q{i}_hr" for i in range(1,5)]
for i,key in enumerate(group_keys):
    row=eq.loc[key]; v=float(row.paired_mean_difference)
    ax_a.plot([row.bootstrap_ci_low,row.bootstrap_ci_high],[i,i],
              color="#b22222" if v>0 else "#4c78a8",lw=1.2)
    ax_a.plot(v,i,"o",color="#b22222" if v>0 else "#4c78a8",ms=3)
ax_a.axvline(0,color="0.4",ls="--",lw=.6)
ax_a.set_yticks(range(4),["Q1","Q2","Q3","Q4"]); ax_a.invert_yaxis()
july.style_axis(ax_a,title="A  Group burden change",
                xlabel="Vulnerability First − Hospital First (h); 95% paired bootstrap CI")
for i,scope in enumerate(["all","Q4"]):
    row=distribution.loc[scope]
    ax_b.plot([row.weighted_q5_hr,row.weighted_q95_hr],[i,i],color="#777777",lw=1.2)
    ax_b.plot([row.weighted_q25_hr,row.weighted_q75_hr],[i,i],color="#4c78a8",lw=5,
              solid_capstyle="butt")
    ax_b.plot(row.weighted_q50_hr,i,"o",color="#111111",ms=3)
ax_b.axvline(0,color="0.4",ls="--",lw=.6)
ax_b.set_yticks([0,1],["All tracts","Q4"]);ax_b.invert_yaxis()
july.style_axis(ax_b,title="B  Population-weighted tract effects",
                xlabel="Burden change (h); 5–95% and 25–75% quantiles")
cost=[("population_resolved_mass_weighted_burden_hr","Pop. burden"),
      ("population_T80_hr","Pop. T80"),
      ("hospital_mean_normalized_burden_hr","Hospital burden"),
      ("absolute_Q4_minus_Q1_hr","|Q4–Q1| gap")]
for i,(key,label) in enumerate(cost):
    row=eq.loc[key]; v=float(row.paired_mean_difference)
    ax_c.plot([row.bootstrap_ci_low,row.bootstrap_ci_high],[i,i],
              color="#b22222" if v>0 else "#4c78a8",lw=1.2)
    ax_c.plot(v,i,"o",color="#b22222" if v>0 else "#4c78a8",ms=3)
ax_c.axvline(0,color="0.4",ls="--",lw=.6)
ax_c.set_yticks(range(4),[x[1] for x in cost]);ax_c.invert_yaxis()
july.style_axis(ax_c,title="C  System and hospital costs",
                xlabel="Paired change (h); 95% bootstrap CI")
export(fig,S6,"vis_stage6_vulnerability_tradeoff_vs_hospital_first")
eq.loc[group_keys+[x[0] for x in cost]].reset_index().to_csv(
    S6/"VULNERABILITY_TRADEOFF_PAIRED_DISPLAY.csv",index=False)
distribution.reset_index().to_csv(S6/"VULNERABILITY_TRADEOFF_CONTINUOUS_DISPLAY.csv",index=False)
