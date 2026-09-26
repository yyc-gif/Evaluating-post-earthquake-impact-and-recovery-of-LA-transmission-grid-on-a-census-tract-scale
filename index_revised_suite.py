"""Refresh the existing suite's inspectable index and provenance manifest."""
from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parent
SUITE = ROOT.parent / "LA_Grid_Revised_Suite_20260925"
JULY = ROOT.parent / "Evaluating post-earthquake impact and recovery of LA transmission grid on a census tract scale"
STAGES = [SUITE / f"Stage {i} Output_expanded" for i in range(1, 8)]
SENS = SUITE / "Sensitivity Output_clean"
MAIN = SUITE / "Submission_Package" / "Main_Figures"
SUPP = SUITE / "Submission_Package" / "Supplementary_Figures"
CANDIDATE_SOURCES = {
    "Candidate_Figure_All_Strategy_Recovery":"Stage 6 Output_expanded/vis_stage6_recovery_curve_2pc50_population",
    "Candidate_Figure_Network_Topology":"Stage 2 Output_expanded/vis_stage2_topology_with_tracts_latlon",
    "Candidate_Figure_Population_Burden":"Stage 6 Output_expanded/vis_stage6_paired_population_resolved_mass_weighted_burden_hr_2pc50",
    "Candidate_Figure_T80":"Stage 6 Output_expanded/vis_stage6_paired_population_T80_hr_2pc50",
    "Candidate_Figure_Hospital_Burden":"Stage 6 Output_expanded/vis_stage6_paired_hospital_mean_normalized_burden_hr_2pc50",
    "Candidate_Figure_Q1_Q4_Absolute_Burden":"Stage 6 Output_expanded/vis_stage6_absolute_group_burdens_2pc50",
    "Candidate_Figure_Source_Path_Burden":"Stage 6 Output_expanded/vis_stage6_paired_source_loss_2pc50",
    "Candidate_S1_Damage_Severity":"Stage 1 Output_expanded/vis_stage1_supp_damage_severity_scenarios",
    "Candidate_S2_Initial_Service_CDF":"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_ecdf_scenarios",
    "Candidate_S3_Initial_Service_Map":"Stage 1 Output_expanded/vis_stage1_supp_initial_supply_maps_scenarios",
    "Candidate_S4_Unconstrained_T80_Map":"Stage 3 Output_expanded/vis_stage3_map_T80_2pc50",
    "Candidate_S5_Directed_Travel":"Stage 4 Output_expanded/vis_stage4_logistics_heatmap_full",
    "Candidate_S6_SCE_Candidate_Benchmark":"Sensitivity Output_clean/vis_sce_candidate_benchmark",
    "Candidate_S7_Gate_Decomposition":"Stage 3 Output_expanded/vis_stage3_loss_decomposition_2pc50",
    "Candidate_S8_Dynamic_Path_Concentration":"Sensitivity Output_clean/vis_dynamic_source_loss_concentration",
    "Candidate_S9_GA_Reproducibility":"Stage 5 Output_expanded/vis_stage5_five_seed_convergence",
    "Candidate_S10_PCA_Scree":"Stage 7 Output_expanded/vis_stage7_pca_scree_plot",
    "Candidate_S11_Kmeans_Elbow":"Stage 7 Output_expanded/vis_stage7_elbow_curve_analysis",
    "Candidate_S12_PCA_Loadings":"Stage 7 Output_expanded/vis_stage7_pca_loadings_heatmap",
    "Candidate_S13_Cluster_Map":"Stage 7 Output_expanded/vis_stage7_map_clusters",
    "Candidate_S14_Hotspot_Map":"Stage 7 Output_expanded/vis_stage7_map_hotspot_score",
    "Candidate_S15_Mapping_Shift":"Sensitivity Output_clean/vis_mapping_shift_magnitude_2pc50",
    "Candidate_S16_Cutoff_Robustness":"Sensitivity Output_clean/vis_mapping_cutoff_response",
    "Candidate_S17_Resource_Sensitivity":"Sensitivity Output_clean/vis_resource_crew_population_resolved_mass_weighted_burden_hr",
    "Candidate_S18_Equity_Efficiency_Tradeoff":"Stage 6 Output_expanded/vis_stage6_equity_efficiency_2pc50",
    "Candidate_S19_Vulnerability_Tract_Effects":"Stage 6 Output_expanded/vis_stage6_vulnerability_effect_magnitude_vs_hospital-first",
    "Candidate_S20_Resource_Equity_Tradeoff":"Sensitivity Output_clean/vis_resource_duration_burden_Q4_hr",
    "Candidate_S21_Crew_Base_Locations":"Stage 4 Output_expanded/vis_stage4_crew_bases_map",
}

stage_images = [p for folder in [*STAGES, SENS] for p in sorted(folder.glob("vis_*.png"))]
candidate_images = [*sorted(MAIN.glob("Candidate_*.png")), *sorted(SUPP.glob("Candidate_*.png"))]
images = stage_images + candidate_images
assert images

pdf = fitz.open()
toc = []
for i, path in enumerate(images, start=1):
    rel = path.relative_to(SUITE).as_posix()
    with Image.open(path) as im:
        im = im.convert("RGB")
        im.thumbnail((2100, 2800), Image.Resampling.LANCZOS)
        stream = io.BytesIO()
        im.save(stream, format="JPEG", quality=87, optimize=True)
        w, h = im.size
    page_width, page_height = ((841.89, 420.0) if w / h > 2.0 else
                               (841.89, 595.28) if w / h > 1.15 else
                               (595.28, 841.89))
    page = pdf.new_page(width=page_width, height=page_height)
    page.insert_textbox(fitz.Rect(24, 14, page_width-24, 45), rel,
                        fontname="hebo", fontsize=8, color=(.12,.12,.12))
    box = fitz.Rect(18, 52, page_width-18, page_height-20)
    scale = min(box.width/w, box.height/h)
    pw, ph = w*scale, h*scale
    x, y = box.x0+(box.width-pw)/2, box.y0+(box.height-ph)/2
    page.insert_image(fitz.Rect(x,y,x+pw,y+ph), stream=stream.getvalue())
    toc.append([1, rel, i])
pdf.set_toc(toc)
pdf.save(SUITE / "FIGURE_INDEX.pdf", garbage=4, deflate=True)
pdf.close()

def hash_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def origin(path):
    rel = path.relative_to(SUITE)
    name = path.stem
    stage = rel.parts[0]
    if stage.startswith("Stage 1"):
        return "Project_Visualizer.py::vis_stage1", "Formal Stage 1 physical samples and initial service"
    if stage.startswith("Stage 2"):
        return "Project_Visualizer.py::vis_stage2", "July unchanged 92-node topology/percolation"
    if stage.startswith("Stage 3"):
        if "source_loss" in name or "decomposition" in name:
            return "Project_Visualizer.py::plot_map/style_axis", "Formal_Reviewer_Results/FORMAL_SOURCE_LOSS_BY_TRACT.csv or FORMAL_GATE_COMPONENTS.csv"
        return "Project_Visualizer.py::vis_stage3", "Formal unconstrained event states and M1 integrals"
    if stage.startswith("Stage 4"):
        return "Project_Visualizer.py::vis_stage4", "July unchanged crew bases/directed travel"
    if stage.startswith("Stage 5"):
        return "Project_Visualizer.py::style_axis", "Formal Stage 5 GA_HISTORY_2pc50_{42..46}.csv"
    if stage.startswith("Stage 6"):
        if "recovery_curve" in name:
            return "Project_Visualizer.py::_stage6_plot_single_scenario_recovery_curve", "Formal event trajectories and M1 mapping"
        return "Project_Visualizer.py::style_axis/STAGE6_RECOVERY_STYLE_CONFIG", "Formal paired or strategy summaries"
    if stage.startswith("Stage 7"):
        return "Project_Visualizer.py::vis_stage7", "Formal Stage 7 typology output"
    if stage.startswith("Sensitivity"):
        return "Project_Visualizer.py::plot_map/style_axis", "Formal resource and mapping summaries"
    if name.startswith("Candidate_"):
        return "See corresponding stage panel", "Copy of formal stage panel or frozen formal summary"
    return "", ""

manifest_path = SUITE / "RESULT_SUITE_MANIFEST.csv"
rows = []
for path in sorted(SUITE.rglob("*")):
    if not path.is_file() or path == manifest_path:
        continue
    rel = path.relative_to(SUITE)
    display_source = CANDIDATE_SOURCES.get(path.stem, "") if rel.parts[0] == "Submission_Package" else ""
    source_for_crosswalk = Path(display_source + path.suffix) if display_source else rel
    plotter, result = origin(SUITE / source_for_crosswalk)
    july_rel = source_for_crosswalk.as_posix() if (JULY / source_for_crosswalk).is_file() else ""
    rows.append({"suite_path": rel.as_posix(), "bytes": path.stat().st_size,
                 "sha256": hash_file(path), "july_corresponding_figure": july_rel,
                 "original_plotting_function": plotter, "formal_source": result,
                 "display_source_panel": display_source,
                 "display_role": "stage_panel" if rel.parts[0].startswith("Stage") else
                                  "candidate" if rel.parts[0] == "Submission_Package" else "support"})
with manifest_path.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
print(f"Index: {len(images)} full-page panels; manifest: {len(rows)} suite files")
