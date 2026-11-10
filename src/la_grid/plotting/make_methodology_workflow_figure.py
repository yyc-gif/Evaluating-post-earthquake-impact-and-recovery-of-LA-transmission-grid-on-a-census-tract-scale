"""Render the current methodology workflow as compact, editable vector artwork.

This is a presentation-only schematic. It reads no scientific result tables and
does not execute any model or analysis. Longer definitions belong in the
manuscript caption; the flow and methods shown here are the adopted workflow.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from matplotlib import font_manager, patches
import matplotlib.pyplot as plt
import hashlib
import io
import os
from pathlib import Path
import fitz

try:
    from la_grid.paths import REPO_ROOT
except ModuleNotFoundError:
    REPO_ROOT = Path(__file__).resolve().parents[3]


BASE_NAME = "methodology_workflow_IJDRR"
OUT_DIR = Path(os.environ.get("LA_GRID_ARTWORK_DRAFT_DIR", str(REPO_ROOT / "provenance" / "artwork_drafts")))
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIDTH_CM = 18.5
HEIGHT_CM = 11.2
DPI = 600

COLORS = {
    "ink": "#26323B",
    "muted": "#59636F",
    "outline": "#87939D",
    "rule": "#D5DCE1",
    "paper": "#FFFFFF",
    "grid": "#2F6F9F",
    "hazard": "#B85B4A",
    "planning": "#7B4E8F",
    "recovery": "#238879",
    "service": "#C8791E",
    "community": "#4E8B5F",
    "soft": "#F5F7F8",
    "band": "#EEF2F4",
}

BOXES = [
    {
        "title": "Network &\nmapping",
        "color": COLORS["grid"],
        "items": [
            "Expanded grid\ntopology",
            "Utility-compatible\ntract weights",
            "Mapping sensitivity",
        ],
    },
    {
        "title": "Seismic\ndamage",
        "color": COLORS["hazard"],
        "items": [
            "Scenario-specific\nPGA",
            "Per-realization\nstation DS",
            "Residual station\nfunctionality",
        ],
    },
    {
        "title": "Strategy\nplanning",
        "color": COLORS["planning"],
        "items": [
            "Community-burden\nGA objective",
            "Vulnerability-first\nrule (Q4 target)",
            "Eight fixed priority\nrules",
            "Unconstrained\nreference",
        ],
    },
    {
        "title": "Repair\nexecution",
        "color": COLORS["recovery"],
        "items": [
            "DS-specific repair\ntime",
            "Directed road\ntravel",
            "Per-realization\ncrew dispatch",
            "Repair completion\nrestores function",
        ],
    },
    {
        "title": "Service &\noutcomes",
        "color": COLORS["community"],
        "items": [
            "Functionality\nthreshold = 0.5",
            "Source-path\navailability",
            "Population weight\n× tract service",
            "Population +\nhospital burden",
            "Q1–Q4 burden",
            "Continuous tract\neffects",
        ],
    },
]


def apply_artwork_style() -> None:
    """Use installed local Arial for the final submission artwork export."""
    font_path = font_manager.findfont("Arial", fallback_to_default=False)
    if not font_path.lower().endswith(("arial.ttf", "arialbd.ttf")):
        raise RuntimeError(f"Expected a locally installed Arial font, found: {font_path}")
    matplotlib.rcParams.update(
        {
            "font.family": "Arial",
            "font.sans-serif": ["Arial"],
            "font.size": 7.2,
            "axes.linewidth": 0.6,
            "figure.facecolor": COLORS["paper"],
            "axes.facecolor": COLORS["paper"],
            "savefig.facecolor": COLORS["paper"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "pdf.use14corefonts": False,
        }
    )


def build_stage4_process_panel(width_pt: float = 246.8,
                               height_pt: float = 133.0) -> tuple[bytes, bytes, dict]:
    """Render Figure 1 Stage 4 from the implemented priority/schedule/event flow."""
    schedule_path = REPO_ROOT / "src/la_grid/revision/r1_realization_scheduling.py"
    ga_path = REPO_ROOT / "src/la_grid/revision/r1_ga_revision.py"
    schedule_source = schedule_path.read_text(encoding="utf-8")
    ga_source = ga_path.read_text(encoding="utf-8")
    implementation_checks = {
        "damaged_tasks_only": "queue=tuple(s for s in seq if int(ds.loc[s])>0)" in schedule_source,
        "earliest_available_crew": "crew=int(np.argmin(clocks))" in schedule_source,
        "travel_then_realized_repair": "arrival=free+travel; dur=float(duration.loc[station]); finish=arrival+dur" in schedule_source,
        "completion_restores_raw_functionality": "values[times>=finish,j]=1." in schedule_source,
        "completion_state_passes_source_gate": "gate_output=source_gate(raw.copy(deep=True))" in schedule_source,
        "ga_task_order_search": "def run_revised_permutation_ga(" in ga_source,
        "direct_service_burden_objective": "def direct_population_burden_objective(" in ga_source,
    }
    assert all(implementation_checks.values()), implementation_checks

    width_pt = float(width_pt)
    height_pt = float(height_pt)
    assert width_pt == 246.8 and height_pt == 133.0
    priority_path = REPO_ROOT / "results/figure_review_s6_main4_20261107/Supplement/FigS07.pdf"
    logistics_path = REPO_ROOT / "results/figure_review_s6_main4_20261107/Supplement/FigS02.pdf"
    assert priority_path.is_file() and logistics_path.is_file()
    doc = fitz.open()
    page = doc.new_page(width=width_pt, height=height_pt)
    with fitz.open(priority_path) as priority, fitz.open(logistics_path) as logistics:
        assert len(priority) == len(logistics) == 1
        # Actual priority-map and logistics artwork, clipped to omit its page titles.
        page.show_pdf_page(fitz.Rect(4, 6, 77, 100), priority, 0,
                           clip=fitz.Rect(52, 535, 302, 678), keep_proportion=True)
        page.show_pdf_page(fitz.Rect(91, 5, 159, 55), logistics, 0,
                           clip=fitz.Rect(68, 40, 424, 275), keep_proportion=True)
        page.show_pdf_page(fitz.Rect(91, 60, 159, 101), logistics, 0,
                           clip=fitz.Rect(78, 350, 430, 584), keep_proportion=True)

    ink = (0.19, 0.24, 0.28)
    teal = (0.14, 0.53, 0.47)
    muted = (0.43, 0.49, 0.53)
    purple = (0.48, 0.31, 0.56)
    for x0, x1 in ((78, 88), (161, 171)):
        page.draw_line((x0, 52), (x1 - 3, 52), color=muted, width=0.8)
        page.draw_polyline([(x1 - 5, 49), (x1, 52), (x1 - 5, 55)],
                           color=muted, width=0.8)

    # Event-driven repair: travel, repair, then an instantaneous station update.
    for y, offset in ((21, 0), (49, 12), (77, 24)):
        page.draw_circle((181, y + 5), 3.5, color=muted, fill=muted)
        page.draw_line((185, y + 5), (197 + offset / 3, y + 5),
                       color=muted, width=1, dashes="[2 2] 0")
        page.draw_rect(fitz.Rect(198 + offset / 3, y + 1, 219 + offset / 3, y + 9),
                       color=purple, fill=purple, width=0.3)
        finish = 220 + offset / 3
        page.draw_line((finish, y - 2), (finish, y + 13), color=teal, width=1.3)
        page.draw_circle((finish + 7, y + 5), 4, color=teal, fill=teal)
        page.draw_circle((finish + 7, y + 5), 1.4, color=None, fill=(1, 1, 1))

    # A separate parallel-repair lane denotes the Unconstrained reference.
    page.draw_line((5, 108), (241, 108), color=(0.82, 0.85, 0.87), width=0.5)
    for y in (115, 121, 127):
        page.draw_rect(fitz.Rect(88, y - 1.5, 157, y + 1.5),
                       color=(0.72, 0.77, 0.79), fill=(0.72, 0.77, 0.79), width=0.2)
    page.draw_line((165, 113), (165, 130), color=teal, width=0.8)
    for y in (115, 121, 127):
        page.draw_circle((171, y), 2, color=teal, fill=teal)
    pdf_bytes = doc.tobytes(garbage=4, deflate=True, no_new_id=True)
    doc.close()
    with fitz.open(stream=pdf_bytes, filetype="pdf") as rendered:
        png_bytes = rendered[0].get_pixmap(dpi=DPI, alpha=False).tobytes("png")
    audit = {
        "source_generator": "src/la_grid/plotting/make_methodology_workflow_figure.py",
        "scheduler_source": "src/la_grid/revision/r1_realization_scheduling.py",
        "scheduler_source_sha256": hashlib.sha256(schedule_path.read_bytes()).hexdigest(),
        "ga_source": "src/la_grid/revision/r1_ga_revision.py",
        "ga_source_sha256": hashlib.sha256(ga_path.read_bytes()).hexdigest(),
        "implementation_checks": implementation_checks,
        "separate_unconstrained_reference": True,
        "connected_operations": ["Priority rules", "Repair scheduling and execution",
                                 "Repair-completion events"],
        "priority_map_sha256": hashlib.sha256(priority_path.read_bytes()).hexdigest(),
        "logistics_figure_sha256": hashlib.sha256(logistics_path.read_bytes()).hexdigest(),
        "uses_priority_map": True,
        "uses_logistics_artwork": True,
        "no_explanatory_text": True,
        "width_pt": width_pt,
        "height_pt": height_pt,
        "body_font": None,
        "body_font_pt": None,
        "no_recovery_curves_or_downstream_outcomes": True,
        "no_simulation_or_schedule_rerun": True,
        "panel_pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "panel_png_sha256": hashlib.sha256(png_bytes).hexdigest(),
    }
    return pdf_bytes, png_bytes, audit


def add_card(ax: plt.Axes, x: float, y: float, width: float, height: float,
             index: int, title: str, items: list[str], color: str) -> None:
    """Draw one concise workflow stage with publication-size lettering."""
    card = patches.FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        facecolor="white", edgecolor=COLORS["outline"], linewidth=0.65,
        zorder=1,
    )
    ax.add_patch(card)
    header_height = 0.86
    header = patches.FancyBboxPatch(
        (x, y + height - header_height), width, header_height,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        facecolor=color, edgecolor=color, linewidth=0.55,
        zorder=2,
    )
    ax.add_patch(header)
    # Mask the lower rounded corners of the header to make its bottom edge flat.
    ax.add_patch(patches.Rectangle(
        (x, y + height - header_height), width, 0.14,
        facecolor=color, edgecolor="none", zorder=2.1,
    ))
    ax.add_patch(patches.Circle(
        (x + 0.33, y + height - header_height / 2), 0.19,
        facecolor="white", edgecolor="none", zorder=3,
    ))
    ax.text(
        x + 0.33, y + height - header_height / 2, str(index),
        ha="center", va="center", fontsize=7.2, weight="bold",
        color=color, zorder=4,
    )
    ax.text(
        x + 0.70, y + height - header_height / 2, title,
        ha="left", va="center", fontsize=9.5, linespacing=0.90, weight="bold",
        color="white", zorder=4,
    )

    body_top = y + height - header_height - 0.22
    body_bottom = y + 0.18
    body_height = body_top - body_bottom
    row_weights = [len(label.splitlines()) + 0.65 for label in items]
    total_weight = sum(row_weights)
    cursor = body_top
    for row, label in enumerate(items):
        row_height = body_height * row_weights[row] / total_weight
        center_y = cursor - row_height / 2
        cursor -= row_height
        ax.add_patch(patches.Circle(
            (x + 0.25, center_y), 0.045,
            facecolor=color, edgecolor="none", zorder=3,
        ))
        ax.text(
            x + 0.39, center_y, label,
            ha="left", va="center", fontsize=7.0, linespacing=0.88,
            color=COLORS["ink"], zorder=3, clip_on=True, clip_path=card,
        )


def build_figure() -> tuple[Path, Path, Path]:
    apply_artwork_style()
    fig = plt.figure(figsize=(WIDTH_CM / 2.54, HEIGHT_CM / 2.54), layout=None)
    ax = fig.add_axes([0, 0, 1, 1])
    fig.patch.set_facecolor(COLORS["paper"])
    ax.set_facecolor(COLORS["paper"])
    ax.set_xlim(0, WIDTH_CM)
    ax.set_ylim(0, HEIGHT_CM)
    ax.axis("off")
    ax.text(WIDTH_CM / 2, 10.91, "LA transmission-grid damage, recovery and community service",
            ha="center", va="center", fontsize=10.0, weight="bold", color=COLORS["ink"])

    # Match the July submission's tiered information flow: input band, two
    # construction blocks, one service-translation block, and two output blocks.
    def box(x: float, y: float, w: float, h: float, letter: str, title: str,
            lines: list[str], color: str) -> None:
        ax.add_patch(patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.05",
            facecolor="white", edgecolor=COLORS["outline"], linewidth=0.6))
        ax.add_patch(patches.Rectangle((x, y + h - .43), w, .43,
                                       facecolor=COLORS["soft"], edgecolor="none"))
        ax.add_patch(patches.Rectangle((x, y + h - .43), .07, .43,
                                       facecolor=color, edgecolor="none"))
        ax.text(x + .17, y + h - .21, f"{letter}  {title}", fontsize=9.5,
                fontweight="bold", ha="left", va="center", color=COLORS["ink"])
        step = (h - .63) / len(lines)
        for n, line in enumerate(lines):
            yy = y + h - .57 - (n + .5) * step
            ax.add_patch(patches.Circle((x + .23, yy), .035,
                                        facecolor=color, edgecolor="none"))
            ax.text(x + .37, yy, line, fontsize=7.3, ha="left", va="center",
                    color=COLORS["ink"])

    ax.add_patch(patches.FancyBboxPatch(
        (.38, 9.68), 17.74, .91, boxstyle="round,pad=.01,rounding_size=.04",
        facecolor=COLORS["soft"], edgecolor=COLORS["outline"], linewidth=.55))
    ax.text(.56, 10.33, "Data inputs", fontsize=8.5, fontweight="bold",
            color=COLORS["ink"], ha="left", va="center")
    for x, lines in zip((.58, 5.05, 9.20, 13.25), (
        ("92 stations · 318 links", "14 Core sources"),
        ("Scenario PGA", "Station fragility"),
        ("Directed road travel", "Repair durations"),
        ("2,315 tracts · population", "Hospitals · SOVI"))):
        for yy, label in zip((10.03, 9.80), lines):
            ax.text(x, yy, label, fontsize=7.1, color=COLORS["ink"], ha="left", va="center")

    box(.38, 7.22, 8.64, 2.18, "A", "Topology and dependency construction", [
        "Retained network and active Core-source identities",
        "Utility-compatible tract-to-station weights",
        "Mapping cutoff and baseline comparisons are checks",
    ], COLORS["grid"])
    box(9.48, 7.22, 8.64, 2.18, "B", "Seismic damage sampling", [
        "Fixed hazard PGA field → DS0–DS4 per station",
        "Residual functionality and DS-specific repair tasks",
        "Paired physical realizations across strategies",
    ], COLORS["hazard"])
    box(.38, 4.68, 17.74, 2.16, "C", "Damage-to-service translation", [
        "Raw station functionality → threshold 0.5 → source-connected station state",
        "Unchanged tract weights aggregate modeled available station service",
        "Exact event intervals produce tract cumulative burden and T50/T80",
    ], COLORS["service"])
    box(.38, 1.13, 8.64, 3.16, "D", "Restoration strategies and execution", [
        "Rule-based priorities include Vulnerability-first",
        "GA searches task orders by service burden",
        "Finite crews schedule DS-specific tasks and durations",
        "Directed road travel links repair tasks",
        "Completion restores station function; service is reevaluated",
    ], COLORS["recovery"])
    box(9.48, 1.13, 8.64, 3.16, "E", "Outputs and interpretation", [
        "Population, hospital and Q1–Q4 burdens",
        "Paired strategy effects and continuous tract changes",
        "Residential typology and hotspot descriptions",
        "Source-path and capacity robustness checks",
    ], COLORS["community"])
    for start, end in (((9.24, 9.68), (9.24, 9.42)),
                       ((9.24, 7.20), (9.24, 6.86)),
                       ((9.24, 4.65), (9.24, 4.32))):
        ax.annotate("", xy=end, xytext=start,
                    arrowprops={"arrowstyle": "-|>", "color": COLORS["muted"],
                                "linewidth": .65, "mutation_scale": 8})
    ax.text(WIDTH_CM / 2, .59,
            "Damage → repair schedules → functional network → source-connected service → community outcomes",
            fontsize=7.5, color=COLORS["muted"], ha="center", va="center")

    pdf_path = OUT_DIR / f"{BASE_NAME}.pdf"
    png_path = OUT_DIR / f"{BASE_NAME}_600dpi.png"
    svg_path = OUT_DIR / f"{BASE_NAME}.svg"
    save_options = {}
    fig.savefig(pdf_path, format="pdf", **save_options)
    fig.savefig(svg_path, format="svg", **save_options)
    # Matplotlib emits harmless trailing blanks in multiline SVG path data;
    # trim line-end whitespace so the generated publication asset passes git
    # whitespace checks without changing SVG geometry or typography.
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text(
        "\n".join(line.rstrip(" \t\r") for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    fig.savefig(png_path, format="png", dpi=DPI, **save_options)
    plt.close(fig)
    return pdf_path, png_path, svg_path


if __name__ == "__main__":
    for artifact in build_figure():
        print(artifact)
