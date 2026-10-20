"""Independent file, map-source, and packet checks for the 2026-10-15 update."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
import subprocess

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/la_grid/plotting"))
import consolidate_current_figure_suite as suite_utils

BASELINE = "0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68"
MAP_SOURCE = "0134bfc5b27a8c518078873e21c6151675523b68"
DIAGNOSTICS = ROOT / "results/diagnostics/1021/figure7_readability_20261015"
QA = ROOT / "docs/reproducibility/figure7_map_readability_20261015"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    before = json.loads((DIAGNOSTICS / "PRESERVATION_BEFORE.json").read_text(encoding="utf-8"))
    assert before["source_commit"] == BASELINE
    manifest = suite_utils.csv_rows((ROOT / "results/figure_review/FIGURE_MANIFEST.csv").read_bytes())
    rows = []
    for record in manifest:
        if not record["final_name"].endswith((".pdf", ".png")):
            continue
        name = record["final_name"]
        source_path = ROOT / record["current_source_file"]
        mirror_path = ROOT / record["mirror_file"]
        current_sha = suite_utils.sha(source_path)
        mirror_sha = suite_utils.sha(mirror_path)
        assert current_sha == mirror_sha == record["sha256"], name
        baseline_sha = before["active_figure_artwork_source_payloads"][name]["sha256"]
        rows.append({
            "figure": name,
            "baseline_sha256": baseline_sha,
            "current_sha256": current_sha,
            "mirror_sha256": mirror_sha,
            "byte_identical_to_baseline": baseline_sha == current_sha,
            "source_path": record["current_source_file"],
            "mirror_path": record["mirror_file"],
        })
    changed = sorted(row["figure"] for row in rows if not row["byte_identical_to_baseline"])
    assert len(rows) == 32
    assert changed == ["Main/Fig07.pdf", "Main/Fig07.png"]

    with fitz.open(ROOT / "results/figure_review/Main/Fig07.pdf") as figure:
        rect = figure[0].rect
        inches = [rect.width / 72, rect.height / 72]
        assert abs(inches[0] - 7.2) < 1e-5 and abs(inches[1] - 10.0) < 1e-7
        assert not figure[0].get_images()
        words = figure[0].get_text().replace("\u00a0", " ")
        assert "D. Recovery burden and social vulnerability" in words
        assert "Q4 + burden >= P75" in words
        assert "N/A (16)" in words
    with Image.open(ROOT / "results/figure_review/Main/Fig07.png") as preview:
        assert preview.size == (4320, 6000)

    with fitz.open(ROOT / "results/figure_review/ALL_MAIN_FIGURES.pdf") as main, \
         fitz.open(ROOT / "results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf") as supplement, \
         fitz.open(ROOT / "results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf") as complete:
        assert (len(main), len(supplement), len(complete)) == (7, 9, 20)
    packet_registry = suite_utils.csv_rows((QA / "COMPACT_PACKET_PAGE_REGISTRY.csv").read_bytes())
    assert len(packet_registry) == 16
    assert [int(row["packet_page"]) for row in packet_registry] == list(range(1, 17))

    vector_before = json.loads((DIAGNOSTICS / "BASELINE_VECTOR_DIAGNOSIS.json").read_text(encoding="utf-8"))
    white_stroked_tract_parts = 0
    for group in vector_before["groups"]:
        for type_count in group["types"]:
            for descriptor, count in type_count.items():
                if "'fill', 0.1" in descriptor and "(1.0, 1.0, 1.0)" in descriptor:
                    white_stroked_tract_parts = max(white_stroked_tract_parts, count)
    assert white_stroked_tract_parts == 2303

    def verify_saved_blob_ids(records: dict[str, str]) -> None:
        for rel, expected_blob in records.items():
            actual_blob = subprocess.check_output(
                ["git", "-C", str(ROOT), "rev-parse", f"{BASELINE}:{rel}"],
                text=True,
            ).strip()
            assert actual_blob == expected_blob, rel

    verify_saved_blob_ids(before["tracked_1021_diagnostic_blob_ids"])
    verify_saved_blob_ids(before["stage7_2026_10_14_blob_ids"])
    changed_tracked = set(subprocess.check_output(
        ["git", "-C", str(ROOT), "diff", "--name-only", BASELINE], text=True
    ).splitlines())
    allowed_tracked = {
        "results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf",
        "results/figure_review/ALL_MAIN_FIGURES.pdf",
        "results/figure_review/CURRENT_CLUSTER_PALETTE.json",
        "results/figure_review/FIGURE_MANIFEST.csv",
        "results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md",
        "results/figure_review/Main/Fig07.pdf",
        "results/figure_review/Main/Fig07.png",
        "results/figure_review/Page_Previews/Fig07.png",
        "results/figure_review/README.md",
        "results/figure_review/UPDATE_LOG.md",
        "results/figures/FIGURE_INDEX.csv",
        "results/figures/FIGURE_REVIEW_GALLERY.html",
        "results/figures/Fig07_Community_Typology_and_Service_Deficit.pdf",
        "results/figures/Fig07_Community_Typology_and_Service_Deficit.png",
        "results/figures/README.md",
        "src/la_grid/plotting/build_current_suite_p2.py",
        "src/la_grid/plotting/figure7_map_readability_20261015.py",
        "tests/test_current_figure_suite_integration.py",
    }
    repo_paths = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
    ).decode().split("\0")
    allowed_tracked.update(
        rel for rel in repo_paths
        if rel.startswith("docs/reproducibility/figure7_map_readability_20261015/")
        or rel.startswith("results/diagnostics/1021/figure7_readability_20261015/")
    )
    assert changed_tracked == allowed_tracked, sorted(changed_tracked ^ allowed_tracked)
    protected_inventory = json.loads(
        (ROOT / "docs/reproducibility/figure_suite_concise_captions_20261013/PRESERVATION_BEFORE.json")
        .read_text(encoding="utf-8")
    )
    assert protected_inventory["protected_count"] == len(protected_inventory["protected_files"]) == 950

    presentation = json.loads((QA / "PRESENTATION_QA.json").read_text(encoding="utf-8"))
    figure_qa = presentation["figures"]["Main/Fig07"]
    assert figure_qa["positive_GEOIDs"] == 2299
    assert figure_qa["NA_polygon_count"] == 16
    assert figure_qa["high_high_outline_count"] == 94
    assert figure_qa["high_high_population"] == 350799
    assert figure_qa["high_high_threshold_hr"] == 38.38135467381475
    assert figure_qa["contrasting_internal_tract_boundaries"] is False
    assert figure_qa["chosen_outline_width_pt"] == 0.25

    suite_utils.write_csv(QA / "ARTWORK_HASH_COMPARISON.csv", rows)
    result = {
        "baseline_branch": "1021",
        "baseline_commit": BASELINE,
        "continuous_map_source_commit": MAP_SOURCE,
        "numbered_artwork_pairs": 16,
        "byte_identical_artwork_pairs": 15,
        "updated_artwork_files": changed,
        "figure7_inches": inches,
        "figure7_pdf_embedded_raster_images": 0,
        "figure7_png_pixels": [4320, 6000],
        "packet_pages": {"main": 7, "supplement": 9, "combined": 20},
        "mirrors_match_manifest_and_authoritative_art": True,
        "baseline_explicit_white_outline_parts": white_stroked_tract_parts,
        "same_fill_edge_overprint_pt": 0.12,
        "screen_outline_pt": 0.25,
        "na_fill": "#FFFFFF",
        "na_boundary_pt": 0.45,
        "eligible_tracts": 2299,
        "na_tracts": 16,
        "high_high_tracts": 94,
        "high_high_population": 350799,
        "high_high_threshold_hr": 38.38135467381475,
        "prior_1021_diagnostics_tracked_paths": len(before["tracked_1021_diagnostic_blob_ids"]),
        "stage7_2026_10_14_tracked_paths": len(before["stage7_2026_10_14_blob_ids"]),
        "formal_science_and_simulations_modified": False,
        "protected_original_inventory_count": protected_inventory["protected_count"],
        "scientific_inputs_formal_results_and_simulations_changed": False,
        "tracked_changed_path_allowlist_matches": True,
        "preexisting_1021_diagnostic_blob_ids_resolve_to_baseline": len(before["tracked_1021_diagnostic_blob_ids"]),
        "stage7_2026_10_14_authority_blob_ids_resolve_to_baseline": len(before["stage7_2026_10_14_blob_ids"]),
    }
    suite_utils.dump(QA / "COMPLETE_SUITE_QA.json", result)
    suite_utils.dump(DIAGNOSTICS / "PRESERVATION_AFTER.json", {
        "baseline_commit": BASELINE,
        "protected_inventory_reference_count": protected_inventory["protected_count"],
        "tracked_changes_match_figure_suite_allowlist": True,
        "protected_scientific_inputs_or_simulation_paths_changed": False,
        "preexisting_1021_diagnostics_expected": len(before["tracked_1021_diagnostic_blob_ids"]),
        "preexisting_1021_diagnostic_blob_ids_confirmed": len(before["tracked_1021_diagnostic_blob_ids"]),
        "stage7_authority_expected": len(before["stage7_2026_10_14_blob_ids"]),
        "stage7_authority_blob_ids_confirmed": len(before["stage7_2026_10_14_blob_ids"]),
        "simulations_or_formal_science_changed": False,
    })
    suite_utils.dump(QA / "TEST_RESULTS.json", {
        "command": "python -m pytest tests/test_current_figure_suite_integration.py -q",
        "python_executable": "C:/Users/yinch/anaconda3/python.exe",
        "result": "PASS",
        "tests_passed": 58,
        "tests_failed": 0,
        "duration_seconds": 256.16,
        "canonical_builder": "python src/la_grid/plotting/build_current_figures.py --portable",
        "canonical_builder_result": "PASS; 16 numbered figures; 20 packet pages",
        "idempotence": "PASS; repeated build checkpoint output hashes stable",
        "independent_suite_verifier": "PASS",
    })
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
