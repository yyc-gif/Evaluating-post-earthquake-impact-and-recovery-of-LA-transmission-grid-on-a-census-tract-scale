import csv
import hashlib
import json
import re
from pathlib import Path

import fitz
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "results/figure_review_rq_aligned_20261101"
MIRRORS = ROOT / "results/figures_rq_aligned_20261101"
QA = SUITE / "QA"
ACTIVE = [f"Main/Fig{i:02d}" for i in range(1, 8)] + [
    f"Supplement/FigS{i:02d}" for i in range(1, 10)
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_review_suite_has_exact_seven_plus_nine_artwork_pairs():
    manifest = rows(SUITE / "FIGURE_MANIFEST.csv")
    expected = {f"{stem}.{ext}" for stem in ACTIVE for ext in ("pdf", "png")}
    assert {r["final_name"] for r in manifest} == expected
    for row in manifest:
        current = ROOT / row["current_source_file"]
        mirror = ROOT / row["mirror_file"]
        assert current.is_file() and mirror.is_file()
        assert sha(current) == row["sha256"] == sha(mirror)


def test_index_numbering_matches_manifest_without_retired_or_shifted_numbers():
    manifest = rows(SUITE / "FIGURE_MANIFEST.csv")
    index = rows(MIRRORS / "FIGURE_INDEX.csv")
    expected = {Path(stem).name for stem in ACTIVE}
    assert {Path(r["final_name"]).stem for r in manifest if r["final_name"].endswith(".pdf")} == expected
    assert {r["figure_number"] for r in index} == expected
    assert "FigS10" not in {r["figure_number"] for r in index}


def test_change_manifest_and_panel_audit_cover_the_complete_active_suite():
    changes = rows(QA / "FIGURE_CHANGE_MANIFEST.csv")
    assert len(changes) == 32
    expected_changed = {
        f"{stem}.{ext}" for stem in (
            "Main/Fig01", "Main/Fig04", "Main/Fig05", "Main/Fig07",
            "Supplement/FigS03", "Supplement/FigS08",
        ) for ext in ("pdf", "png")
    }
    assert {r["figure"] for r in changes if r["unchanged"].lower() == "false"} == expected_changed
    panel_audit = (QA / "RQ_ALIGNMENT_AND_PANEL_AUDIT.md").read_text(encoding="utf-8")
    assert all(label in panel_audit for label in (
        "Figure 1", "Figure 2", "Figure 3", "Figure 4", "Figure 5", "Figure 6", "Figure 7",
        "Supplementary Figure S1", "Supplementary Figure S9", "RQ1", "RQ2", "RQ3"
    ))


def test_full_packets_have_seven_main_nine_supplement_and_sixteen_combined_pages():
    for path, expected in ((SUITE / "ALL_MAIN_FIGURES.pdf", 7),
                           (SUITE / "ALL_SUPPLEMENT_FIGURES.pdf", 9),
                           (SUITE / "ALL_FIGURES_WITH_CAPTIONS.pdf", 16)):
        with fitz.open(path) as doc:
            assert len(doc) == expected
    with fitz.open(SUITE / "ALL_FIGURES_WITH_CAPTIONS.pdf") as doc:
        for i, stem in enumerate(ACTIVE):
            text = doc[i].get_text()
            name = Path(stem).name
            if name.startswith("FigS"):
                expected_title = f"Supplementary Figure S{int(name[4:])}."
            else:
                expected_title = f"Figure {int(name[3:])}."
            assert expected_title in text


def test_every_page_preview_is_rendered_from_its_current_artwork():
    from PIL import Image
    for stem in ACTIVE:
        with fitz.open(SUITE / f"{stem}.pdf") as doc:
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(160 / 72, 160 / 72), alpha=False)
        with Image.open(SUITE / "Page_Previews" / f"{Path(stem).name}.png") as preview:
            assert preview.size == (pix.width, pix.height), stem
            assert preview.convert("RGB").tobytes() == pix.samples, stem


def test_figure3_component_shares_are_from_all_four_saved_scenarios():
    audit = json.loads((QA / "FIG03_COMPONENT_SHARE_QA.json").read_text(encoding="utf-8"))
    expected = {
        "2pc50": (85.7981957564, 2.7969175110, 11.4048867326),
        "LongBeach": (91.5194388483, 4.0821924545, 4.3983686972),
        "Northridge": (81.5349501906, 3.3589892021, 15.1060606073),
        "SanFernando": (87.1441496218, 4.0156042423, 8.8402461359),
    }
    found = {r["hazard"]: r for r in audit["rows"]}
    assert set(found) == set(expected)
    for scenario, values in expected.items():
        row = found[scenario]
        assert row["n"] == 1000
        actual = tuple(100 * row[key] for key in (
            "share_substation_damage", "share_functionality_threshold", "share_source_path"))
        assert max(abs(a - b) for a, b in zip(actual, values)) < 1e-8
        assert row["component_sum_max_abs_error_hr"] < 1e-10


def test_figure4_uses_matched_outcomes_and_paired_mechanism_components():
    audit = json.loads((QA / "FIG04_MECHANISM_AND_OUTCOME_QA.json").read_text(encoding="utf-8"))
    assert audit["outcome_source_rows"] == 7000
    assert audit["shared_realization_identity_across_strategies"] is True
    assert audit["source_trajectory_curves_regenerated"] is False
    assert audit["uncertainty"] == "5th-95th realization ranges, not confidence intervals"
    assert audit["component_additivity_max_abs_error_hr"] < 1e-10
    assert audit["component_mean_difference_sum_error_hr"] < 1e-12
    assert all(r["n_paired_realizations"] == 1000 for r in audit["paired_component_rows"])
    with fitz.open(SUITE / "Main/Fig04.pdf") as doc:
        text = re.sub(r"\s+", " ", doc[0].get_text())
        assert audit['main_panels']==['A','B']
        assert audit['single_pair_decomposition_in_main'] is False
        assert "Degree-first minus Hospital-first (h)" not in text
        assert "C. Why" not in text
        for strategy in ['Impact-first','Hospital-first','Degree-first',
                         'Vulnerability-first','Betweenness-first','Random','Unconstrained']:
            assert strategy in text
        assert "Points: paired means" not in text


def test_figure5_separates_signed_and_within_realization_absolute_gaps():
    audit = json.loads((QA / "FIG05_SIGNED_GAP_QA.json").read_text(encoding="utf-8"))
    assert audit["n_matched_realization_ids"] == 1000
    assert audit["physical_sample_hash_unique_count"] == 1000
    outcomes = {r["outcome"] for r in audit["comparison_rows"]}
    assert "signed_Q4_minus_Q1_hr" in outcomes
    assert "absolute_Q4_minus_Q1_hr" in outcomes
    assert audit["ordinary_plot_values_or_strategy_results_changed"] is False
    caption = (SUITE / "MANUSCRIPT_FACING_CAPTIONS.md").read_text(encoding="utf-8")
    assert "mean within-realization absolute |Q4-Q1| gap" in caption


def test_figure7_preserves_science_without_bottom_annotation_block():
    audit = json.loads((QA / 'FIG07_DISPLAY_QA.json').read_text(encoding='utf-8'))
    assert abs(audit['width_in']-7.2)<1e-12
    palette = json.loads((SUITE / "CURRENT_CLUSTER_PALETTE.json").read_text(encoding="utf-8"))
    assert palette["colors"] == {"1": "#3C9198", "2": "#52699E", "3": "#C69EBA"}
    profile = pd.DataFrame(audit['profile_rows'])
    ecdf = pd.DataFrame(audit['ecdf_rows'])
    assert len(profile) == 21
    assert len(ecdf) == 18
    assert set(profile["class_id"]) == {"C1", "C2", "C3"}
    assert set(profile["variable"]) == {
        "Init_Supply", "Grid_Impact", "Redundancy_HHI", "B_Unconstrained",
        "MeanDelta", "SOVI_SCORE", "log1p_Population"
    }
    with fitz.open(SUITE / "Main/Fig07.pdf") as doc:
        assert len(doc) == 1
        text = doc[0].get_text()
    text = re.sub(r"\s+", " ", text.replace("\u00a0", " ").replace("\u00ad", ""))
    text = text.replace("\u037e", ";")
    screen=audit['screen']
    assert screen['q4_tracts']==579 and screen['high_tracts']==575
    assert screen['joint_tracts']==94 and screen['joint_population']==350799
    assert abs(screen['threshold_hr']-38.38135467381475)<1e-12
    assert abs(screen['q4_prevalence_pct']-16.23488773747841)<1e-10
    assert abs(screen['non_q4_prevalence_pct']-27.96511627906977)<1e-10
    assert audit['summary_line_count']==0
    for phrase in ['Cohort P75:','Joint screen:','High-burden prevalence:',
                   'Descriptive five-policy comparison.','94 tracts','350,799 residents']:
        assert phrase not in text
    assert "NCV14" not in text


def test_s3_s4_and_ci_captions_match_active_artwork_definitions():
    captions = (SUITE / "MANUSCRIPT_FACING_CAPTIONS.md").read_text(encoding="utf-8")
    assert "## Supplementary Figure S3. Functional-network recovery" in captions
    assert "The curves describe network topology, not power flow or delivered electricity." in captions
    assert "## Supplementary Figure S4. Genetic-algorithm diagnostics" in captions
    assert "2,000 separate validation realizations" in captions
    assert "## Figure 6. Resource dependence" in captions
    assert "95% bootstrap confidence intervals for mean effects" in captions
    assert "not realization ranges" in captions
    with fitz.open(SUITE / "Supplement/FigS03.pdf") as doc:
        text = doc[0].get_text().lower().replace("\u00ad", "").replace("\u00a0", " ")
        assert "recovery of largest" in text or "largest connected component" in text
        assert "static percolation" not in text


def test_all_review_artwork_is_vector_bearing_and_font_embedding_is_audited():
    path_ops = re.compile(rb"(?:^|\s)(?:m|l|c|re)\s")
    paint_ops = re.compile(rb"(?:^|\s)(?:S|s|f|F|f\*|B|B\*|b|b\*)\s")
    manifest = rows(SUITE / "FIGURE_MANIFEST.csv")
    expected_vector = {
        "Main/Fig01.pdf", "Main/Fig03.pdf", "Main/Fig04.pdf", "Main/Fig05.pdf",
        "Main/Fig07.pdf", "Supplement/FigS03.pdf", "Supplement/FigS08.pdf",
    }
    for row in manifest:
        if row["final_name"] not in expected_vector:
            continue
        with fitz.open(ROOT / row["current_source_file"]) as doc:
            assert len(doc) == 1
            streams = [doc.xref_stream(xref) or b"" for xref in range(1, doc.xref_length())
                       if doc.xref_is_stream(xref)]
            assert any(path_ops.search(stream) and paint_ops.search(stream) for stream in streams), row["final_name"]
    for pdf in [ROOT / r["current_source_file"] for r in manifest if r["final_name"].endswith(".pdf")]:
        with fitz.open(pdf) as doc:
            for page in doc:
                for font in page.get_fonts(full=True):
                    basefont = re.sub(r"^[A-Z]{6}\+", "", font[3])
                    assert basefont.startswith("Arial"), (pdf.name, basefont)
                    assert doc.extract_font(font[0])[3], (pdf.name, basefont, "font not embedded")
    with fitz.open(SUITE / "ALL_FIGURES_WITH_CAPTIONS.pdf") as doc:
        for page in doc:
            for font in page.get_fonts(full=True):
                basefont = re.sub(r"^[A-Z]{6}\+", "", font[3])
                assert basefont.startswith("Arial"), basefont
                assert doc.extract_font(font[0])[3], (basefont, "font not embedded")
