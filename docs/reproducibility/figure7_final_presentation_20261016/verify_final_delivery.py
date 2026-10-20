"""Verify the 2026-10-16 Figure 7 presentation against the 1021 HEAD inputs."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import fitz
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/la_grid/plotting"))
import consolidate_current_figure_suite as suite

BASELINE = "2779c0b0f2694af2818debeb69241edbe8762260"
SCIENCE = "937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f"
REVIEW = ROOT / "docs/reproducibility/figure7_final_presentation_20261016"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check() -> dict:
    baseline_manifest = suite.payload(BASELINE, "results/figure_review/FIGURE_MANIFEST.csv")
    rows = list(csv.DictReader(baseline_manifest.decode("utf-8-sig").splitlines()))
    assert len(rows) == 32
    comparisons = []
    for row in rows:
        rel = row["current_source_file"]
        base = suite.payload(BASELINE, rel)
        current = (ROOT / rel).read_bytes()
        mirror = (ROOT / row["mirror_file"]).read_bytes()
        current_sha, base_sha = sha(current), sha(base)
        is_fig7 = row["final_name"].startswith("Main/Fig07.")
        assert (current_sha != base_sha) if is_fig7 else (current_sha == base_sha), rel
        assert current == mirror, row["mirror_file"]
        comparisons.append({
            "figure_file": row["final_name"], "baseline_path": rel,
            "baseline_sha256": base_sha, "current_sha256": current_sha,
            "figure7_changed": is_fig7, "baseline_bytes_unchanged": current_sha == base_sha,
            "mirror_path": row["mirror_file"], "mirror_matches_current": current == mirror,
        })
    with (REVIEW / "BASELINE_ARTWORK_SHA256_COMPARISON.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)

    table = pd.read_csv(
        suite.io.BytesIO(suite.payload(SCIENCE,
            "docs/data_research/stage7_path_b_p2_integration_review_20261014/FROZEN_P2_TRACT_TABLE_2315.csv")),
        dtype={"tract_id": str}, float_precision="round_trip")
    eligible = table.loc[table.Population.gt(0)].copy()
    assert len(table) == 2315 and len(eligible) == 2299
    assert eligible.tract_id.str.fullmatch(r"\d{11}").all()
    assert int(eligible.Population.sum()) == 9066522
    assert int(eligible.additional_zero_housing_positive_population.sum()) == 8
    assert eligible.P2_K3_class.value_counts().sort_index().tolist() == [1235, 428, 636]
    assert int((table.Population.eq(0)).sum()) == 16
    p75 = float(np.percentile(eligible.MeanTotal5.to_numpy(), 75))
    q4 = eligible.frozen_SOVI_quartile.eq("Q4")
    screen = q4 & eligible.MeanTotal5.ge(p75)
    assert abs(p75 - 38.38135467381475) < 1e-12
    assert int(screen.sum()) == 94 and int(eligible.loc[screen, "Population"].sum()) == 350799

    with fitz.open(ROOT / "results/figure_review/Main/Fig07.pdf") as doc:
        page = doc[0]
        assert len(doc) == 1 and abs(page.rect.width - 518.4) < 1e-3
        assert abs(page.rect.height - 650) < 1e-3 and not page.get_images()
        text = " ".join(page.get_text().replace("\u00a0", " ").split())
        expected = ["Initial service availability", "Spectral network impact",
                    "Dependency concentration (HHI)", "Unconstrained service deficit",
                    "Mean additional service deficit (five policies)",
                    "Social vulnerability score", "Tract population"]
        assert all(label in text for label in expected)
        spans = [s for b in page.get_text("dict")["blocks"] for line in b.get("lines", [])
                 for s in line["spans"]]
        min_font = min(s["size"] for s in spans if s["text"].strip())
        assert min_font >= 7.49
        assert all(page.rect.contains(fitz.Rect(s["bbox"])) for s in spans if s["text"].strip())
        font_records = []
        for item in page.get_fonts(full=True):
            extracted = doc.extract_font(item[0])
            font_records.append({"xref": item[0], "name": item[3], "extension": extracted[1],
                                 "embedded_bytes": len(extracted[3])})
        assert all(f["embedded_bytes"] > 0 for f in font_records)
        drawing_count = len(page.get_drawings())
        assert drawing_count > 5000

    manifest_now = list(csv.DictReader((ROOT / "results/figure_review/FIGURE_MANIFEST.csv").open(encoding="utf-8-sig")))
    assert len(manifest_now) == 32
    assert sum(r["final_name"].startswith("Main/") and r["final_name"].endswith(".pdf") for r in manifest_now) == 7
    assert sum(r["final_name"].startswith("Supplement/") and r["final_name"].endswith(".pdf") for r in manifest_now) == 9
    packet_pages = {}
    for rel, expected_pages in (("results/figure_review/ALL_MAIN_FIGURES.pdf", 7),
                                ("results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf", 9),
                                ("results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf", 20)):
        with fitz.open(ROOT / rel) as doc:
            assert len(doc) == expected_pages
            packet_pages[rel] = {"pages": len(doc), "sha256": suite.sha(ROOT / rel)}

    palette = json.loads((ROOT / "results/figure_review/CURRENT_CLUSTER_PALETTE.json").read_text(encoding="utf-8"))
    assert palette["colors"] == {"1": "#3C9198", "2": "#52699E", "3": "#C69EBA"}
    comparison = pd.DataFrame(comparisons)
    unaffected = comparison.loc[~comparison.figure7_changed]
    assert len(unaffected) == 30 and unaffected.baseline_bytes_unchanged.all()
    result = {
        "branch_baseline_commit": BASELINE,
        "science_input_commit": SCIENCE,
        "numbered_artwork_files": 32,
        "unchanged_non_figure7_artwork_files": int(unaffected.baseline_bytes_unchanged.sum()),
        "figure7_artwork_files_changed": int(comparison.figure7_changed.sum()),
        "all_mirrors_match": bool(comparison.mirror_matches_current.all()),
        "cohort": {"tracts": len(eligible), "population": int(eligible.Population.sum()),
                   "class_counts": eligible.P2_K3_class.value_counts().sort_index().tolist(),
                   "zero_population_na": int(table.Population.eq(0).sum()),
                   "zero_housing_positive_population": int(eligible.additional_zero_housing_positive_population.sum())},
        "screen": {"P75_hours": p75, "tracts": int(screen.sum()),
                   "population": int(eligible.loc[screen, "Population"].sum())},
        "figure7": {"page_points": [518.4, 650], "width_in": 7.2,
                    "height_in": 650 / 72, "height_mm": 650 * 25.4 / 72,
                    "min_text_pt": min_font, "embedded_fonts": font_records,
                    "image_objects": 0, "vector_drawing_objects": drawing_count},
        "packets": packet_pages,
        "all_16_pdf_png_artwork_mirrors_verified": True,
        "pass": True,
    }
    (REVIEW / "FINAL_OUTPUT_VERIFICATION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
