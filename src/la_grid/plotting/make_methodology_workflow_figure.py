"""Render the current methodology workflow as compact, editable vector artwork.

The Stage 4 panel reads an archived priority order and frozen repair events;
it does not execute the scheduler or modify scientific results.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from matplotlib import font_manager, patches
import matplotlib.pyplot as plt
import hashlib
import io
import json
import os
import subprocess
from pathlib import Path
import fitz
import numpy as np

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


def build_stage4_process_panel(width_pt: float = 505.4,
                               height_pt: float = 132.0,
                               priority_map_pdf: bytes | None = None,
                               priority_map_source_sha256: str | None = None
                               ) -> tuple[bytes, bytes, dict]:
    """Render the full-width, three-operation Stage 4 method panel."""
    schedule_path = REPO_ROOT / "src/la_grid/revision/r1_realization_scheduling.py"
    ga_path = REPO_ROOT / "src/la_grid/revision/r1_ga_revision.py"
    resource_path = REPO_ROOT / "src/la_grid/revision/r1_final_matrix.py"
    schedule_source = schedule_path.read_text(encoding="utf-8")
    ga_source = ga_path.read_text(encoding="utf-8")
    resource_source = resource_path.read_text(encoding="utf-8")
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
    assert '"C57 pooled regional resource, 57 crews at frozen active origins"' in resource_source
    crew_count = 57

    width_pt = float(width_pt)
    height_pt = float(height_pt)
    assert width_pt == 505.4 and height_pt == 132.0
    priority_path = REPO_ROOT / "results/figure_review_s6_main4_20261107/Supplement/FigS07.pdf"
    if priority_map_pdf is None:
        import figure_presentation
        priority_source_bytes = priority_path.read_bytes()
        priority_map_pdf, _ = figure_presentation.priority_geography(
            priority_source_bytes,
            palette_stops=["#F3F4F1", "#DFE7E1", "#BED2C8", "#91B4A5", "#659587"],
            source_palette_stops=["#FFFFFF", "#E0D6E9", "#B69ACB", "#8B63AC", "#613A80"])
        priority_map_source_sha256 = hashlib.sha256(priority_source_bytes).hexdigest()
    schedule_rel = "Formal_Experiment_20260923/Formal_Schedule_Prepass/2pc50__C57_D1__impact-first"
    schedule_commit = "6cfccca37cde7a53b909067caaaadea256cfd226"
    def archived(suffix):
        return subprocess.check_output(
            ["git", "show", f"{schedule_commit}:{schedule_rel}.{suffix}"], cwd=REPO_ROOT)
    schedule_bytes = archived("npz")
    schedule_manifest = json.loads(archived("json"))
    sequence_bytes = subprocess.check_output(
        ["git", "show", f"{schedule_commit}:Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json"],
        cwd=REPO_ROOT)
    priority_order = json.loads(sequence_bytes)["2pc50"]["impact-first"]
    assert hashlib.sha256(schedule_bytes).hexdigest() == schedule_manifest["npz_sha256"]
    identity = schedule_manifest["identity"]
    assert (identity["hazard"], identity["resource_case"], identity["strategy"],
            identity["split"], schedule_manifest["schedule_count"]) == (
                "2pc50", "C57_D1", "impact-first", "evaluation", 1000)
    with np.load(io.BytesIO(schedule_bytes), allow_pickle=False) as saved:
        assert saved["completion"].shape == (1000, 92)
        ids = saved["station_ids"].astype(str)
        dispatch = saved["dispatch"][0]
        crew = saved["crew"][0]
        arrival = saved["arrival"][0]
        travel = saved["travel"][0]
        completion = saved["completion"][0]
        previous = saved["previous"][0]
    # These are the first five crews with repeated assignments in the saved
    # realization, making crew release and subsequent dispatch visible.
    displayed_crews = (4, 8, 11, 13, 16)
    events = []
    for crew_index in displayed_crews:
        for j in np.where(crew == crew_index)[0]:
            free = float(arrival[j] - travel[j])
            prior = int(previous[j])
            assert (prior < 0 and abs(free) < 1e-12) or (
                prior >= 0 and abs(free - completion[prior]) < 1e-10)
            assert 0 <= free < arrival[j] < completion[j]
            events.append({"crew_index": crew_index, "station_id": ids[j],
                           "dispatch_rank": int(dispatch[j]) + 1,
                           "free_hr": free, "travel_hr": float(travel[j]),
                           "arrival_hr": float(arrival[j]),
                           "repair_hr": float(completion[j] - arrival[j]),
                           "completion_hr": float(completion[j])})
    events.sort(key=lambda e: (e["crew_index"], e["free_hr"]))
    assert [sum(e["crew_index"] == c for e in events)
            for c in displayed_crews] == [2, 2, 3, 3, 2]
    assert [ids[j] for j in np.argsort(dispatch)[:5]] == priority_order[:5]
    doc = fitz.open()
    page = doc.new_page(width=width_pt, height=height_pt)
    arial = font_manager.findfont("Arial", fallback_to_default=False)
    bold = str(Path(arial).with_name("arialbd.ttf"))
    page.insert_font(fontname="Arial", fontfile=arial)
    page.insert_font(fontname="Arial-Bold", fontfile=bold)
    priority_source = fitz.open(stream=priority_map_pdf, filetype="pdf")
    with priority_source as priority:
        assert len(priority) == 1
        # Figure S7C is an Impact-first example, not a map of every rule.
        map_clip = fitz.Rect(52, 535, 302, 733)
        # Match the median visible map footprint in Stages 1-3 (about 138 x 104 px
        # at 150 dpi); preserve the full extent and station coordinates.
        map_target = fitz.Rect(49.0, 36.0, 128.5, 96.0)
        # Preserve the saved rank-marker centers while increasing their print-size legibility.
        words = priority[0].get_text("words", clip=map_clip)
        spans = [word for word in words if word[4] in {"1", "2", "3", "4", "5"}]
        rank_centers = {int(word[4]): ((word[0] + word[2]) / 2,
                                       (word[1] + word[3]) / 2)
                        for word in spans}
        assert set(rank_centers) == {1, 2, 3, 4, 5}
        for word in spans:
            priority[0].add_redact_annot(fitz.Rect(word[:4]), fill=None,
                                          cross_out=False)
        priority[0].apply_redactions(images=0, graphics=0)
        page.show_pdf_page(map_target, priority, 0, clip=map_clip,
                           keep_proportion=True)
        map_scale = min(map_target.width / map_clip.width,
                        map_target.height / map_clip.height)
        map_drawn_width = map_clip.width * map_scale
        map_x_offset = map_target.x0 + (map_target.width - map_drawn_width) / 2
        for rank, (sx, sy) in rank_centers.items():
            cx = map_x_offset + (sx - map_clip.x0) * map_scale
            cy = map_target.y0 + (sy - map_clip.y0) * map_scale
            priority_teal = (0.08, 0.36, 0.34)
            page.draw_circle((cx, cy), 4.1, color=priority_teal,
                             fill=priority_teal, width=0.25)
            page.insert_text((cx - 1.8, cy + 2.2), str(rank), fontname="Arial-Bold",
                             fontsize=8.0, color=(1, 1, 1))

    ink = (0.15, 0.19, 0.21)
    muted = (0.39, 0.45, 0.49)
    teal = (0.14, 0.53, 0.47)
    dark_teal = (0.08, 0.36, 0.34)
    travel_gray = (0.55, 0.58, 0.58)
    rule = (0.82, 0.85, 0.86)
    map_stops = ["#F3F4F1", "#DFE7E1", "#BED2C8", "#91B4A5", "#659587"]
    from matplotlib.colors import LinearSegmentedColormap
    population_key = LinearSegmentedColormap.from_list("PriorityMapKey", map_stops)

    def label(x, y, value, size=8.0, weight=False, color=ink):
        page.insert_text((x, y), value, fontname="Arial-Bold" if weight else "Arial",
                         fontsize=size, color=color)

    # Align the three operations as quiet, equal-weight columns.
    for x in (168.5, 337.0):
        page.draw_line((x, 6), (x, height_pt - 6), color=rule, width=0.65)
    label(9, 14, "Priority Rules", 9.0, True, color=ink)
    label(177, 14, "Repair Scheduling", 9.0, True, color=ink)
    label(346, 14, "Completion Events", 9.0, True, color=ink)
    for x in (161.5, 330.0):
        page.draw_line((x - 4, 11), (x + 3, 11), color=muted, width=0.8)
        page.draw_polyline([(x, 8.5), (x + 3, 11), (x, 13.5)], color=muted, width=0.8)

    label(9, 25, "Impact-first example", 7.5)
    # Compact population key; the logarithmic scale is defined in the caption.
    for i in range(32):
        x = 61.0 + i * 1.7
        color = tuple(float(v) for v in population_key((i + 0.5) / 32)[:3])
        page.draw_rect(fitz.Rect(x, 108, x + 1.8, 112), color=color,
                       fill=color, width=0)
    label(61, 124, "Tract population", 7.5)

    # A shared linear axis shows five real crew histories from the saved schedule.
    x0, x1, axis_max = 208.0, 324.0, 60.0
    scale = (x1 - x0) / axis_max
    row_positions = (42, 53, 64, 75, 86)
    crew_labels = (5, 9, 12, 14, 17)
    for crew_index, crew_label, y in zip(displayed_crews, crew_labels, row_positions):
        for event in (e for e in events if e["crew_index"] == crew_index):
            left = x0 + scale * event["free_hr"]
            arrival_x = x0 + scale * event["arrival_hr"]
            right = x0 + scale * event["completion_hr"]
            page.draw_line((left, y), (arrival_x, y), color=travel_gray, width=2.2)
            page.draw_rect(fitz.Rect(arrival_x, y - 2.5, right, y + 2.5),
                           color=teal, fill=teal, width=0.25)
            page.draw_line((right, y - 4.3), (right, y + 4.3), color=ink, width=0.65)
        label(174, y + 2.5, f"Crew {crew_label}", 7.5, True)
    for tick in (0, 15, 30, 45, 60):
        tx = x0 + scale * tick
        page.draw_line((tx, 94), (tx, 97), color=ink, width=0.55)
        tick_label = "60 h" if tick == 60 else str(tick)
        width = fitz.Font(fontfile=arial).text_length(tick_label, fontsize=7.8)
        label(tx - width / 2, 108, tick_label, 7.8)
    page.draw_line((x0, 95.5), (x1, 95.5), color=muted, width=0.6)
    page.draw_line((184, 122), (197, 122), color=travel_gray, width=2.2)
    label(201, 124.5, "Travel", 7.5)
    page.draw_rect(fitz.Rect(240, 119.5, 249, 125), color=teal, fill=teal, width=0.2)
    label(253, 124.5, "Repair", 7.5)

    # Completion is a real event: the crew becomes available, station raw
    # functionality is restored, and the updated station state feeds tract service.
    def arrow(start, end, y):
        page.draw_line((start, y), (end - 2.3, y), color=muted, width=0.75)
        page.draw_polyline([(end - 4.3, y - 2.0), (end - 2.0, y),
                            (end - 4.3, y + 2.0)], color=muted, width=0.75)

    # A completed repair interval anchors the sequence.
    page.draw_line((347, 60), (354, 60), color=travel_gray, width=2.2)
    page.draw_rect(fitz.Rect(354, 56.8, 375, 63.2), color=teal,
                   fill=teal, width=0.2)
    page.draw_line((375, 53), (375, 67), color=ink, width=0.7)
    label(350, 84, "Repair", 7.5, True)
    label(350, 94, "complete", 7.5, True)
    arrow(379, 392, 60)

    # Crew release and station restoration are concurrent consequences.
    crew_cx, station_cx, state_y = 403, 447, 60
    # Compact crew glyph: three workers, no implied crew count in the schedule.
    for cx in (crew_cx - 5, crew_cx, crew_cx + 5):
        page.draw_circle((cx, state_y - 4), 1.65, color=muted,
                         fill=muted, width=0.25)
        page.draw_line((cx, state_y - 1.5), (cx, state_y + 4.5),
                       color=muted, width=1.0)
        page.draw_line((cx - 2.4, state_y + 1), (cx + 2.4, state_y + 1),
                       color=muted, width=0.85)
    page.draw_circle((station_cx, state_y), 8.3, color=dark_teal,
                     fill=dark_teal, width=0.35)
    one_width = fitz.Font(fontfile=bold).text_length("1", fontsize=8.2)
    page.insert_text((station_cx - one_width / 2, state_y + 2.8), "1",
                     fontname="Arial-Bold", fontsize=8.2, color=(1, 1, 1))
    label(394, 84, "Crew", 7.5)
    label(388, 94, "released", 7.5)
    label(435, 84, "Station", 7.5)
    label(432, 94, "restored", 7.5)
    arrow(459, 467, 60)

    # A small tract-grid cue indicates the spatial service state passed onward.
    tract_cells = [
        (468, 52, 478, 60, (0.87, 0.91, 0.89)),
        (479, 52, 489, 60, (0.68, 0.81, 0.75)),
        (490, 52, 500, 60, (0.40, 0.66, 0.57)),
        (468, 61, 478, 69, (0.68, 0.81, 0.75)),
        (479, 61, 489, 69, (0.40, 0.66, 0.57)),
        (490, 61, 500, 69, (0.87, 0.91, 0.89)),
    ]
    for x0_cell, y0_cell, x1_cell, y1_cell, color in tract_cells:
        page.draw_rect(fitz.Rect(x0_cell, y0_cell, x1_cell, y1_cell),
                       color=(1, 1, 1), fill=color, width=0.55)
    label(474, 84, "Tract", 7.5)
    label(473, 94, "service", 7.5)
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
        "crew_count_source": "src/la_grid/revision/r1_final_matrix.py",
        "crew_count_source_sha256": hashlib.sha256(resource_path.read_bytes()).hexdigest(),
        "crews_in_model": crew_count,
        "crews_shown": [5, 9, 12, 14, 17],
        "crew_selection_rule": "first five crews in saved crew-index order with repeated assignments",
        "crew_event_counts": {str(c + 1): sum(e["crew_index"] == c for e in events)
                              for c in displayed_crews},
        "implementation_checks": implementation_checks,
        "separate_unconstrained_reference": True,
        "connected_operations": ["Priority rules", "Repair scheduling and execution",
                                 "Repair-completion events"],
        "priority_map_sha256": hashlib.sha256(priority_map_pdf).hexdigest(),
        "priority_map_source_sha256": priority_map_source_sha256,
        "priority_map_palette": map_stops,
        "priority_map_visible_target_pt": [map_target.width, map_target.height],
        "priority_map_target_rect_pt": list(map_target),
        "map_ranks_are_full_station_priority_ranks": True,
        "gantt_dispatch_numbers_removed_to_avoid_rank_ambiguity": True,
        "schedule_archive_sha256": hashlib.sha256(schedule_bytes).hexdigest(),
        "priority_sequence_sha256": hashlib.sha256(sequence_bytes).hexdigest(),
        "schedule_manifest": schedule_manifest,
        "schedule_commit": schedule_commit,
        "plotted_task_events": events,
        "uses_priority_map": True,
        "uses_saved_schedule": True,
        "source_graphics_labeled": True,
        "no_fabricated_task_events": True,
        "width_pt": width_pt,
        "height_pt": height_pt,
        "body_font": "Arial",
        "body_font_pt": 7.5,
        "rank_marker_font_pt": 8.0,
        "schedule_rank_label_pt": None,
        "source_map_rank_text_removed_before_relabel": True,
        "schedule_axis_hours": [0, 15, 30, 45, 60],
        "schedule_axis_max_hr": 60,
        "schedule_time_axis_range_hr": [0, 60],
        "schedule_end_hr": max(e["completion_hr"] for e in events),
        "all_task_completion_hours": [round(e["completion_hr"], 8) for e in events],
        "visual_operations": ["priority map", "crew Gantt", "completion-event state update"],
        "completion_visual_labels": ["Repair complete", "Crew released",
                                     "Station restored", "Tract service"],
        "population_map_display_scale": "logarithmic, described in caption",
        "no_recovery_curves_or_downstream_outcomes": True,
        "no_simulation_or_schedule_rerun": True,
        "panel_pdf_sha256": hashlib.sha256(pdf_bytes).hexdigest(),
        "panel_png_sha256": hashlib.sha256(png_bytes).hexdigest(),
    }
    with fitz.open(stream=pdf_bytes, filetype="pdf") as rendered:
        spans = [span for block in rendered[0].get_text("dict")["blocks"]
                 for line in block.get("lines", [])
                 for span in line.get("spans", []) if span["text"].strip()]
        audit["minimum_panel_text_pt"] = min(span["size"] for span in spans)
        assert audit["minimum_panel_text_pt"] >= 7.5
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
