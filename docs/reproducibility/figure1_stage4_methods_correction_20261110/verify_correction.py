from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import fitz
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src/la_grid/plotting"))
import build_s6_main4_review as builder
import figure_presentation

START = "54b64c2ad01d6b6b2dbfd5892e7567d82a71f463"
SUITE = ROOT / "results/figure_review_s6_main4_20261107"
OUT = ROOT / "docs/reproducibility/figure1_stage4_methods_correction_20261110"
FIGURE = "results/figure_review_s6_main4_20261107/Main/Fig01"
PANEL_RECT = fitz.Rect(9.5, 481.7, 256.3, 614.7)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render(pdf_bytes: bytes, dpi: int, clip: fitz.Rect | None = None) -> bytes:
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        return doc[0].get_pixmap(dpi=dpi, alpha=False, clip=clip).tobytes("png")


def build_comparison(before_pdf: bytes, after_pdf: bytes) -> bytes:
    with fitz.open(stream=before_pdf, filetype="pdf") as before, \
            fitz.open(stream=after_pdf, filetype="pdf") as after:
        w, h = before[0].rect.width, before[0].rect.height
        comparison_doc = fitz.open()
        comparison = comparison_doc.new_page(width=2 * w, height=h + 22)
        comparison.insert_font(fontname="Arial", fontfile="C:/Windows/Fonts/arial.ttf")
        comparison.insert_font(fontname="Arial-Bold", fontfile="C:/Windows/Fonts/arialbd.ttf")
        comparison.insert_text((w / 2 - 29, 15), "BEFORE", fontname="Arial-Bold",
                               fontsize=9, color=(0.15, 0.19, 0.22))
        comparison.insert_text((w + w / 2 - 25, 15), "CORRECTED", fontname="Arial-Bold",
                               fontsize=9, color=(0.15, 0.19, 0.22))
        comparison.show_pdf_page(fitz.Rect(0, 22, w, h + 22), before, 0)
        comparison.show_pdf_page(fitz.Rect(w, 22, 2 * w, h + 22), after, 0)
        data = comparison_doc.tobytes(garbage=4, deflate=True, no_new_id=True)
        comparison_doc.close()
        return data


def build_stage4_comparison(before_pdf: bytes, after_pdf: bytes) -> tuple[bytes, bytes]:
    with fitz.open(stream=before_pdf, filetype="pdf") as before, \
            fitz.open(stream=after_pdf, filetype="pdf") as after:
        w, h = PANEL_RECT.width, PANEL_RECT.height
        comparison_doc = fitz.open()
        page = comparison_doc.new_page(width=2 * w, height=h + 22)
        page.insert_font(fontname="Arial-Bold", fontfile="C:/Windows/Fonts/arialbd.ttf")
        page.insert_text((w / 2 - 29, 15), "BEFORE", fontname="Arial-Bold",
                         fontsize=9, color=(0.15, 0.19, 0.22))
        page.insert_text((w + w / 2 - 25, 15), "CORRECTED", fontname="Arial-Bold",
                         fontsize=9, color=(0.15, 0.19, 0.22))
        page.show_pdf_page(fitz.Rect(0, 22, w, h + 22), before, 0, clip=PANEL_RECT)
        page.show_pdf_page(fitz.Rect(w, 22, 2 * w, h + 22), after, 0, clip=PANEL_RECT)
        pdf_bytes = comparison_doc.tobytes(garbage=4, deflate=True, no_new_id=True)
        png_bytes = page.get_pixmap(dpi=150, alpha=False).tobytes("png")
        comparison_doc.close()
        return pdf_bytes, png_bytes


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before_pdf = builder.u.payload(START, FIGURE + ".pdf")
    after_pdf = (ROOT / (FIGURE + ".pdf")).read_bytes()
    after_png = (ROOT / (FIGURE + ".png")).read_bytes()
    panel_pdf, panel_png, panel_audit = builder.workflow_figure.build_stage4_process_panel()
    saved_panel_pdf = (SUITE / "QA/FIG01_STAGE4_METHOD_PANEL.pdf").read_bytes()
    saved_panel_png = (SUITE / "QA/FIG01_STAGE4_METHOD_PANEL.png").read_bytes()
    assert panel_pdf == saved_panel_pdf and panel_png == saved_panel_png

    with fitz.open(stream=panel_pdf, filetype="pdf") as panel:
        panel_text = " ".join(panel[0].get_text().replace("\xa0", " ").split())
        assert len(panel) == 1
        panel_vector_count = len(panel[0].get_contents())
        panel_image_count = len(panel[0].get_images())
        panel_fonts = sorted({font[3] for font in panel[0].get_fonts()})
    required = ("1", "2", "3", "4", "5")
    rejected = ("availability curves", "Impact-first service-availability", "T80",
                "cumulative service loss", "population-weighted service availability")
    assert panel_text.split() == list(required), panel_text
    assert panel_audit["uses_priority_map"] and panel_audit["uses_logistics_artwork"]
    assert not any(text.lower() in panel_text.lower() for text in rejected), panel_text
    assert panel_vector_count > 0

    with fitz.open(stream=before_pdf, filetype="pdf") as before, \
            fitz.open(stream=after_pdf, filetype="pdf") as after:
        assert len(before) == len(after) == 1
        assert before[0].rect == after[0].rect
        before_pix = before[0].get_pixmap(dpi=120, alpha=False)
        after_pix = after[0].get_pixmap(dpi=120, alpha=False)
        before_rgb = np.frombuffer(before_pix.samples, dtype=np.uint8).reshape(
            before_pix.height, before_pix.width, 3)
        after_rgb = np.frombuffer(after_pix.samples, dtype=np.uint8).reshape(
            after_pix.height, after_pix.width, 3)
        scale = 120 / 72
        x0 = max(0, int(np.floor(PANEL_RECT.x0 * scale)) - 2)
        x1 = min(before_pix.width, int(np.ceil(PANEL_RECT.x1 * scale)) + 2)
        y0 = max(0, int(np.floor(PANEL_RECT.y0 * scale)) - 2)
        y1 = min(before_pix.height, int(np.ceil(PANEL_RECT.y1 * scale)) + 2)
        outside = np.ones(before_rgb.shape[:2], dtype=bool)
        outside[y0:y1, x0:x1] = False
        outside_identical = bool(np.array_equal(before_rgb[outside], after_rgb[outside]))
        assert outside_identical
        assert after[0].get_pixmap(dpi=600, alpha=False).tobytes("png") == after_png
        before_rect = list(before[0].rect)
        after_rect = list(after[0].rect)

    for name, data in (
        ("FIG01_STAGE4_FINAL_600DPI.png", render(after_pdf, 600, PANEL_RECT)),
        ("FIG01_COMPLETE_PAGE_FINAL_150DPI.png", render(after_pdf, 150)),
    ):
        (OUT / name).write_bytes(data)
    stage4_comparison_pdf, stage4_comparison_png = build_stage4_comparison(before_pdf, after_pdf)
    (OUT / "FIG01_STAGE4_DETAIL_BEFORE_AFTER.pdf").write_bytes(stage4_comparison_pdf)
    (OUT / "FIG01_STAGE4_DETAIL_BEFORE_AFTER.png").write_bytes(stage4_comparison_png)

    s5_files = (
        "results/figure_review_s6_main4_20261107/Supplement/FigS05.pdf",
        "results/figure_review_s6_main4_20261107/Supplement/FigS05.png",
        "results/figure_review_s6_main4_20261107/Page_Previews/FigS05.png",
    )
    s5_hashes = {}
    for rel in s5_files:
        old = builder.u.payload(START, rel)
        new = (ROOT / rel).read_bytes()
        assert old == new
        s5_hashes[rel] = {"sha256": sha(new), "byte_identical_to_start": True}

    with (SUITE / "FIGURE_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    f1 = next(row for row in manifest if row["final_name"] == "Main/Fig01.pdf")
    assert sha(after_pdf) == f1["sha256"]
    assert (ROOT / f1["mirror_file"]).read_bytes() == after_pdf
    assert (ROOT / "results/figures_s6_main4_20261107/Fig01_Methodology_Workflow.pdf").read_bytes() == after_pdf

    with fitz.open(SUITE / "ALL_FIGURES_WITH_CAPTIONS.pdf") as packet, \
            fitz.open(SUITE / "ALL_MAIN_FIGURES.pdf") as main_packet, \
            fitz.open(SUITE / "ALL_SUPPLEMENT_FIGURES.pdf") as supp_packet:
        packet_pages = {"complete": len(packet), "main": len(main_packet), "supplement": len(supp_packet)}
        assert packet_pages == {"complete": 16, "main": 8, "supplement": 8}
        first_page_text = " ".join(packet[0].get_text().split())
        assert "map illustrates Impact-first" in first_page_text
        assert "Unconstrained parallel repair" in first_page_text
        (OUT / "FIGURE_PACKET_PAGE1_FINAL_150DPI.png").write_bytes(
            packet[0].get_pixmap(dpi=150, alpha=False).tobytes("png"))

    (OUT / "FIG01_BEFORE_AFTER.pdf").write_bytes(
        build_comparison(before_pdf, after_pdf))
    report = {
        "starting_commit": START,
        "starting_branch": "review/fig1-moduleD-s5-final-20261109",
        "source_figure_commit": builder.BASE,
        "figure1_before_sha256": sha(before_pdf),
        "figure1_after_sha256": sha(after_pdf),
        "figure1_png_sha256": sha(after_png),
        "figure1_pdf_dimensions_pt": before_rect,
        "figure1_after_dimensions_pt": after_rect,
        "stage4_generator": builder.WORKFLOW_GENERATOR,
        "stage4_generator_sha256": sha((ROOT / builder.WORKFLOW_GENERATOR).read_bytes()),
        "figure_presentation_sha256": sha((ROOT / "src/la_grid/plotting/figure_presentation.py").read_bytes()),
        "s6_builder_sha256": sha((ROOT / "src/la_grid/plotting/build_s6_main4_review.py").read_bytes()),
        "p2_builder_sha256": sha((ROOT / "src/la_grid/plotting/build_current_suite_p2.py").read_bytes()),
        "scheduler_source_sha256": sha((ROOT / builder.SCHEDULER_SOURCE).read_bytes()),
        "ga_source_sha256": sha((ROOT / builder.GA_SOURCE).read_bytes()),
        "stage4_panel_pdf_sha256": sha(panel_pdf),
        "stage4_panel_png_sha256": sha(panel_png),
        "stage4_text_checks": {"no_explanatory_text": True, "priority_rank_markers": True},
        "stage4_priority_map_sha256": panel_audit["priority_map_sha256"],
        "stage4_logistics_figure_sha256": panel_audit["logistics_figure_sha256"],
        "stage4_rejected_result_terms_absent": True,
        "stage4_vector_content_stream_count": panel_vector_count,
        "stage4_embedded_image_count": panel_image_count,
        "stage4_fonts": panel_fonts,
        "stage4_implementation_checks": panel_audit["implementation_checks"],
        "outside_stage4_render_pixels_identical_at_120dpi": outside_identical,
        "s5_hashes": s5_hashes,
        "packet_page_counts": packet_pages,
        "figure1_mirror_and_manifest_match": True,
        "simulations_or_schedules_rerun": False,
    }
    (OUT / "FIGURE1_STAGE4_NUMERICAL_AND_PRESERVATION_QA.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
