"""Adapt frozen July92 formal results to the retained July visualizer.

This module does presentation-only aggregation. It never samples damage,
dispatches crews, evaluates source gates, or changes frozen scientific inputs.
"""
from __future__ import annotations

import csv
import hashlib
import shutil
import sys
from pathlib import Path

import fitz
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy import sparse

import Project_Visualizer as july

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
SUITE = ROOT.parent / "LA_Grid_Revised_Suite_20260925"
FORMAL = ROOT / "Formal_Experiment_20260923"
STAGE1 = SUITE / "Stage 1 Output_expanded"
STAGE3 = SUITE / "Stage 3 Output_expanded"
STAGE6 = SUITE / "Stage 6 Output_expanded"
STAGE7 = SUITE / "Stage 7 Output_expanded"
MAIN = SUITE / "Submission_Package" / "Main_Figures"
SUPP = SUITE / "Submission_Package" / "Supplementary_Figures"
HAZARDS = ["Northridge", "SanFernando", "LongBeach", "2pc50"]
POLICIES = ["centrality-first", "impact-first", "betweenness-first",
            "degree-first", "closeness-first", "hospital-first", "random",
            "vulnerability-first"]
for folder in [STAGE1, STAGE3, STAGE6, STAGE7, MAIN, SUPP]:
    folder.mkdir(parents=True, exist_ok=True)

july.OUTPUT_ROOT = str(SUITE)
july.apply_publication_style()

mapping = pd.read_csv(ROOT / "Data" / "JULY_UTILITY_CONSTRAINED_92.csv",
                      dtype={"tract_id": str, "substation_id": str})
mapping["tract_id"] = mapping.tract_id.str.zfill(11)
tracts = sorted(mapping.tract_id.unique())
station_ids = list(np.load(FORMAL / "Stage 1 Output_expanded" /
                           "physical_inputs_2pc50.npz")["station_ids"].astype(str))
assert len(tracts) == 2315 and len(station_ids) == 92
ri = {v: i for i, v in enumerate(tracts)}
ci = {v: i for i, v in enumerate(station_ids)}
W = sparse.csr_matrix((mapping.weight.astype(float),
                       ([ri[v] for v in mapping.tract_id],
                        [ci[v] for v in mapping.substation_id])), shape=(2315, 92))
assert np.allclose(np.asarray(W.sum(axis=1)).ravel(), 1)
geo = gpd.read_file(ROOT / "Data" / "LA_Tracts_With_Population.shp")
geo["tract_id"] = geo.GEOID.astype(str).str.zfill(11)
geo = geo[geo.tract_id.isin(tracts)].copy()
assert len(geo) == 2315


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_pair(src: Path, target: Path) -> None:
    for suffix in (".png", ".pdf"):
        a = src.with_suffix(suffix)
        assert a.is_file(), a
        b = target.with_suffix(suffix)
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(a, b)


# Stage 1: the July function receives revised formal DS and initial-service
# tables under its original input schema. Average DS is a station statistic,
# never a count of stations in each DS category.
initial = pd.read_csv(STAGE1 / "S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv",
                      dtype={"tract_id": str})
for hazard in HAZARDS:
    physical = np.load(FORMAL / "Stage 1 Output_expanded" /
                       f"physical_inputs_{hazard}.npz")
    assert list(physical["station_ids"].astype(str)) == station_ids
    ds = physical["evaluation_ds"]
    assert ds.shape == (92, 1000)
    pd.DataFrame({"substation_id": station_ids, "scenario": hazard,
                  "avg_damage_state": ds.mean(axis=1)}).to_csv(
        STAGE1 / f"MC_Device_Damage_AvgDS_{hazard}.csv", index=False)
    part = initial[initial.hazard == hazard]
    assert len(part) == 2315
    part[["tract_id", "mean_initial_service_proxy"]].rename(
        columns={"mean_initial_service_proxy": "supply"}).to_csv(
        STAGE1 / f"MC_Tract_Supply_{hazard}.csv", index=False)
july.vis_stage1(geo.copy())
copy_pair(STAGE1 / "vis_stage1_supp_damage_severity_scenarios",
          SUPP / "Candidate_S1_Damage_Severity")
copy_pair(STAGE1 / "vis_stage1_supp_initial_supply_ecdf_scenarios",
          SUPP / "Candidate_S2_Initial_Service_CDF")
copy_pair(STAGE1 / "vis_stage1_supp_initial_supply_maps_scenarios",
          SUPP / "Candidate_S3_Initial_Service_Map")


# Stage 3: calculate tract KPI display summaries from saved unconstrained
# event states. The event grid and scientific kernel remain untouched.
for hazard in HAZARDS:
    folder = FORMAL / "Formal_Trajectories" / hazard / "C57_D1" / "unconstrained"
    paths = sorted(folder.glob("*.npz"))
    assert len(paths) == 1000, (hazard, len(paths))
    totals = np.zeros((2, 2315)); counts = np.zeros((2, 2315), dtype=int)
    for path in paths:
        with np.load(path) as z:
            assert list(z["station_ids"].astype(str)) == station_ids
            availability = W @ z["e"].T  # tract × event; sparse dependency projection
            times = z["event_time_hr"]
            for row, threshold in enumerate((.5, .8)):
                reached = availability >= threshold
                valid = reached.any(axis=1)
                when = times[np.argmax(reached, axis=1)]
                totals[row, valid] += when[valid]
                counts[row, valid] += 1
    with np.load(FORMAL / "Formal_Offline_Evaluation" /
                 f"{hazard}__C57_D1__unconstrained__INTEGRALS.npz") as z:
        burden = z["M1_UTILITY_003__normalized_burden_hr"]
        assert burden.shape == (1000, 2315)
        auc = 1 - np.nanmean(burden, axis=0) / 480.
    t50 = np.divide(totals[0], counts[0], out=np.full(2315, np.nan), where=counts[0] > 0)
    t80 = np.divide(totals[1], counts[1], out=np.full(2315, np.nan), where=counts[1] > 0)
    frozen_t80 = initial[initial.hazard == hazard].set_index("tract_id").reindex(tracts)
    assert np.allclose(t80, frozen_t80.mean_T80_hr_when_reached, atol=1e-7, equal_nan=True)
    pd.DataFrame({"tract_id": tracts, "AUC": auc, "T50": t50, "T80": t80}).to_csv(
        STAGE3 / f"tract_kpis_{hazard}.csv", index=False)
july.vis_stage3(geo.copy())


# Stage 6: the original recovery-curve function keeps the July strategy color,
# dash, label and layout vocabulary. A post-event step is used because revised
# restoration happens at completion events; the hourly grid is display-only.
july.STAGE6_SHARED_LINE_STYLES["vulnerability-first"] = {
    "color": "#a65628", "ls": "-", "lw_recovery": 1.08,
    "lw_topology": .98, "alpha_recovery": .85, "alpha_topology": .82, "zorder": 9}
july.STAGE6_RECOVERY_STYLE_CONFIG["vulnerability-first"] = {
    "label": "Vulnerability First (Q4)",
    **july._stage6_line_style("vulnerability-first")}
july.STAGE6_LEGEND_ORDER.append("vulnerability-first")
july.STAGE6_RECOVERY_STYLE_CONFIG["S3_Mean"]["label"] = "Unconstrained recovery"
curves = pd.read_csv(STAGE6 / "ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv")
for hazard in HAZARDS:
    part = curves[curves.hazard == hazard]
    assert set(part.strategy_id) == set(POLICIES + ["unconstrained"])
    grid = pd.Index(sorted(part.time_hr.unique().astype(float)), name="time_hr")
    series = {}
    for strategy in ["unconstrained", *POLICIES]:
        values = part[part.strategy_id == strategy].set_index("time_hr")[
            "mean_population_availability_proxy"].reindex(grid).to_numpy()
        series["S3_Mean" if strategy == "unconstrained" else strategy] = pd.Series(
            values, index=grid)
    july._stage6_plot_single_scenario_recovery_curve(
        hazard, series, "Population", str(STAGE6), grid, event_step=True)
    if hazard == "2pc50":
        copy_pair(STAGE6 / f"vis_stage6_recovery_curve_{hazard}_population",
                  MAIN / "Candidate_Figure_All_Strategy_Recovery")

# Hospital and fixed Q1–Q4 service trajectories use the same mapping and
# denominators as the formal burden summaries. These curves are descriptive
# means of saved event states, not averages of realization-level T80 values.
meta = pd.read_csv(ROOT / "R1_Comment1_July92_Utility_Constraint" /
                   "MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv",
                   dtype={"tract_id": str}).set_index("tract_id").reindex(tracts)
assert meta.index.is_unique and not meta.population.isna().any()
population = meta.population.to_numpy(float)
def group_station_weight(mask, population_weighted=True):
    values = population * mask if population_weighted else mask.astype(float)
    assert values.sum() > 0
    return np.asarray(W.T @ (values / values.sum())).ravel()
group_names = ["network", "hospital", "Q1", "Q2", "Q3", "Q4"]
group_vectors = np.vstack([
    np.full(92, 1 / 92),
    group_station_weight(meta.hospital_tract.to_numpy(bool), False),
    *(group_station_weight((meta.SOVI_quartile == q).to_numpy()) for q in ("Q1", "Q2", "Q3", "Q4")),
])
grid = np.arange(481, dtype=float)
group_records = []
for hazard in HAZARDS:
    by_group = {name: {} for name in group_names}
    by_interval = {name: {} for name in group_names}
    for strategy in ["unconstrained", *POLICIES]:
        folder = (FORMAL / "Equity_Amendment" / "T" / hazard / "C57_D1"
                  if strategy == "vulnerability-first" else
                  FORMAL / "Formal_Trajectories" / hazard / "C57_D1" / strategy)
        paths = sorted(folder.glob("*.npz"))
        assert len(paths) == 1000, (hazard, strategy, len(paths))
        samples = np.empty((1000, len(grid), len(group_names)), dtype=np.float32)
        for j, path in enumerate(paths):
            with np.load(path) as z:
                assert list(z["station_ids"].astype(str)) == station_ids
                when = np.clip(np.searchsorted(z["event_time_hr"], grid, side="right") - 1,
                               0, len(z["event_time_hr"]) - 1)
                samples[j] = z["e"][when] @ group_vectors.T
        means = samples.mean(axis=0)
        lo, hi = np.quantile(samples, [.05, .95], axis=0)
        key = "S3_Mean" if strategy == "unconstrained" else strategy
        for k, name in enumerate(group_names):
            by_group[name][key] = pd.Series(means[:, k], index=grid)
            by_interval[name][key] = (lo[:, k], hi[:, k])
            group_records.extend((hazard, strategy, name, int(t), float(means[i,k]),
                                  float(lo[i,k]), float(hi[i,k])) for i,t in enumerate(grid))
        print("group event-state display", hazard, strategy, flush=True)
    for name in group_names:
        label = {"network": "Mean available station functionality",
                 "hospital": "Hospital-tract service availability"}.get(
                     name, f"{name} population-weighted availability")
        july._stage6_plot_single_scenario_recovery_curve(
            hazard, by_group[name], "Population", str(STAGE6), pd.Index(grid),
            event_step=True, ylabel_override=label,
            title_suffix_override=f"{name} modeled service availability",
            output_slug_override=f"{name.lower()}_all_strategies")
        if name in {"network", "hospital", "Q4"}:
            focus = {k: by_group[name][k] for k in
                     ("hospital-first", "impact-first", "vulnerability-first", "random")}
            july._stage6_plot_single_scenario_recovery_curve(
                hazard, focus, "Population", str(STAGE6), pd.Index(grid),
                event_step=True, ylabel_override=label,
                title_suffix_override=f"{name} availability; 5–95% realization band",
                output_slug_override=f"{name.lower()}_focused_uncertainty",
                interval_by_key={k: by_interval[name][k] for k in focus})
pd.DataFrame(group_records, columns=["hazard", "strategy_id", "group", "time_hr",
             "mean_availability", "p05_availability", "p95_availability"]).to_csv(
    STAGE6 / "GROUP_EVENT_STATE_DISPLAY_CURVES.csv", index=False)


# Stage 7: formal inputs use the July Stage-7 schema; invoke that plotting
# family directly to retain the feature, profile, PCA, cluster and continuous
# hotspot designs, including the original discrete cluster palette.
july.vis_stage7(geo.copy())
for src, target in [
    ("vis_stage7_pca_scree_plot", "Candidate_S10_PCA_Scree"),
    ("vis_stage7_elbow_curve_analysis", "Candidate_S11_Kmeans_Elbow"),
    ("vis_stage7_pca_loadings_heatmap", "Candidate_S12_PCA_Loadings"),
    ("vis_stage7_map_clusters", "Candidate_S13_Cluster_Map"),
    ("vis_stage7_map_hotspot_score", "Candidate_S14_Hotspot_Map"),
]:
    if (STAGE7 / (src + ".png")).is_file():
        copy_pair(STAGE7 / src, SUPP / target)


# Unchanged July topology and crew-base locations retain their actual July
# panels. All recovery values above are drawn anew from formal event archives.
july_root = ROOT.parent / "Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale"
copy_pair(july_root / "Stage 4 Output_expanded" / "vis_stage4_crew_bases_map",
          SUPP / "Candidate_S21_Crew_Base_Locations")

# A one-panel-per-page index permits checking map detail and legend size.
index = fitz.open()
paths = [*sorted(MAIN.glob("Candidate_*.png")), *sorted(SUPP.glob("Candidate_*.png"))]
for path in paths:
    page = index.new_page(width=595.28, height=841.89)
    page.insert_text((35, 32), path.stem, fontsize=11, fontname="hebo")
    img = fitz.Pixmap(str(path))
    avail = fitz.Rect(30, 58, 565, 795)
    scale = min(avail.width / img.width, avail.height / img.height)
    width, height = img.width * scale, img.height * scale
    x0 = avail.x0 + (avail.width - width) / 2
    y0 = avail.y0 + (avail.height - height) / 2
    page.insert_image(fitz.Rect(x0, y0, x0 + width, y0 + height), filename=str(path))
    img = None
index_path = SUITE / "FIGURE_INDEX.pdf"
index.save(index_path, garbage=4, deflate=True)
index.close()

manifest_path = SUITE / "RESULT_SUITE_MANIFEST.csv"
rows = []
for path in sorted(SUITE.rglob("*")):
    if not path.is_file() or path == manifest_path:
        continue
    rows.append({"suite_path": path.relative_to(SUITE).as_posix(),
                 "suite_sha256": file_hash(path), "bytes": path.stat().st_size,
                 "july_reference": "Project_Visualizer.py" if path.suffix.lower() in {".png", ".pdf"} else "",
                 "july_function": "vis_stage1 / vis_stage3 / Stage-6 curve / vis_stage7" if path.suffix.lower() in {".png", ".pdf"} else "",
                 "source_results_path": str(FORMAL)})
with manifest_path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
print("rendered", len(paths), "candidate PNGs; index pages", len(paths))
