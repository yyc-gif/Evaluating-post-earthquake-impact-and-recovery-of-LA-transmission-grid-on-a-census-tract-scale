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
    assert width_pt > 0 and height_pt > 0
    apply_artwork_style()
    ink = COLORS["ink"]
    muted = COLORS["muted"]
    outline = COLORS["outline"]
    rule = COLORS["rule"]
    teal = COLORS["recovery"]
    fig = plt.figure(figsize=(width_pt / 72.0, height_pt / 72.0),
                     facecolor=COLORS["paper"])
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width_pt)
    ax.set_ylim(0, height_pt)
    ax.axis("off")

    # The reference is deliberately outside the constrained three-step flow.
    ref_x, ref_y, ref_w, ref_h = 5.2, 111.0, width_pt - 10.4, 18.0
    ax.add_patch(patches.FancyBboxPatch(
        (ref_x, ref_y), ref_w, ref_h,
        boxstyle="round,pad=0.8,rounding_size=2.0",
        facecolor=COLORS["soft"], edgecolor=rule, linewidth=0.55,
    ))
    ax.text(ref_x + 5.0, ref_y + ref_h / 2,
            "Unconstrained reference", ha="left", va="center",
            fontsize=6.7, fontweight="bold", color=ink)
    ax.text(ref_x + 100.0, ref_y + ref_h / 2,
            "Parallel repairs; no finite-crew or travel limits.",
            ha="left", va="center", fontsize=6.2, color=muted)

    rows = [
        (77.0, "Priority rules",
         "Predefined network and community priorities include Vulnerability-first.",
         "GA plans repair-task order using a service-burden objective."),
        (43.0, "Repair scheduling and execution",
         "Queue DS > 0 tasks; finite crews; realized DS-specific durations.",
         "Directed travel/dispatch; finish = crew available + travel + repair."),
        (9.0, "Repair-completion events",
         "At completion, release crew; raw station functionality becomes 1.",
         "Pass updated state to source-connectivity and tract-service evaluation."),
    ]
    row_h = 24.0
    x, w = 5.2, width_pt - 10.4
    for number, (y, heading, line1, line2) in enumerate(rows, 1):
        ax.add_patch(patches.FancyBboxPatch(
            (x, y), w, row_h,
            boxstyle="round,pad=0.7,rounding_size=1.8",
            facecolor="white", edgecolor=rule, linewidth=0.5,
        ))
        ax.add_patch(patches.Circle((x + 10.0, y + row_h / 2), 5.0,
                                    facecolor=teal, edgecolor="none"))
        ax.text(x + 10.0, y + row_h / 2, str(number), ha="center", va="center",
                fontsize=6.4, fontweight="bold", color="white")
        ax.text(x + 21.0, y + row_h - 6.0, heading, ha="left", va="center",
                fontsize=6.8, fontweight="bold", color=ink)
        ax.text(x + 21.0, y + 9.5, line1, ha="left", va="center",
                fontsize=6.4, color=ink)
        ax.text(x + 21.0, y + 3.0, line2, ha="left", va="center",
                fontsize=6.4, color=ink)

    # Short down-arrows connect constrained restoration operations only.
    for lower_y, upper_y in ((77.0, 67.0), (43.0, 33.0)):
        ax.annotate("", xy=(15.2, upper_y + 0.5), xytext=(15.2, lower_y - 0.5),
                    arrowprops={"arrowstyle": "-|>", "color": muted,
                                "linewidth": 0.65, "mutation_scale": 5.5})

    pdf_out, png_out = io.BytesIO(), io.BytesIO()
    fig.savefig(pdf_out, format="pdf", metadata={"CreationDate": None,
                                                   "ModDate": None,
                                                   "Creator": "methodology workflow generator"})
    fig.savefig(png_out, format="png", dpi=DPI)
    plt.close(fig)
    pdf_bytes, png_bytes = pdf_out.getvalue(), png_out.getvalue()
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
        "width_pt": width_pt,
        "height_pt": height_pt,
        "body_font": "Arial",
        "body_font_pt": 6.4,
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
