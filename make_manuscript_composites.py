"""Assemble manuscript composites from complete generated source figures.

The source figures are never redrawn or overwritten. This script only trims
exterior white margin, preserves each panel's aspect ratio, applies controlled
physical scaling, and adds consistently sized panel letters.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


CM_PER_INCH = 2.54
EXPORT_DPI = 600
FIGURE_WIDTH_CM = 18.5

ROOT = Path(__file__).resolve().parent
MANUSCRIPT_DIR = ROOT / "Manuscript_Figures"
PREP_DIR = MANUSCRIPT_DIR / "composite_ready_panels"

RC = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 9.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.facecolor": "white",
}


@dataclass(frozen=True)
class PanelAsset:
    relative_path: str
    prepared_path: Path
    image: np.ndarray
    width_cm: float
    height_cm: float

    @property
    def aspect(self) -> float:
        return self.image.shape[1] / self.image.shape[0]


_PANEL_CACHE: dict[str, PanelAsset] = {}


def cm(value: float) -> float:
    return value / CM_PER_INCH


def _crop_exterior_white(
    image: Image.Image,
    *,
    crop_padding_px: int = 12,
) -> Image.Image:
    rgb = np.asarray(image.convert("RGB"))
    content = np.any(rgb < 248, axis=2)
    rows, columns = np.where(content)
    if not rows.size:
        return image.convert("RGB")

    left = max(0, int(columns.min()) - crop_padding_px)
    right = min(rgb.shape[1], int(columns.max()) + crop_padding_px + 1)
    top = max(0, int(rows.min()) - crop_padding_px)
    bottom = min(rgb.shape[0], int(rows.max()) + crop_padding_px + 1)
    return image.convert("RGB").crop((left, top, right, bottom))


def prepare_panel(relative_path: str) -> PanelAsset:
    cached = _PANEL_CACHE.get(relative_path)
    if cached is not None:
        return cached

    source_path = ROOT / relative_path
    source = Image.open(source_path)
    dpi = source.info.get("dpi", (EXPORT_DPI, EXPORT_DPI))
    dpi_x = float(dpi[0]) if dpi and dpi[0] else float(EXPORT_DPI)
    dpi_y = float(dpi[1]) if dpi and dpi[1] else float(EXPORT_DPI)
    cropped = _crop_exterior_white(source)

    PREP_DIR.mkdir(parents=True, exist_ok=True)
    source_name = Path(relative_path)
    source_key = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:8]
    prepared_name = f"{source_name.stem}_{source_key}{source_name.suffix}"
    prepared_path = PREP_DIR / prepared_name
    cropped.save(prepared_path, dpi=(dpi_x, dpi_y))

    width_cm = cropped.width / dpi_x * CM_PER_INCH
    height_cm = cropped.height / dpi_y * CM_PER_INCH
    asset = PanelAsset(
        relative_path=relative_path,
        prepared_path=prepared_path,
        image=np.asarray(cropped),
        width_cm=width_cm,
        height_cm=height_cm,
    )
    _PANEL_CACHE[relative_path] = asset
    return asset


def place_asset(
    fig: plt.Figure,
    asset: PanelAsset,
    *,
    figure_height_cm: float,
    center_x_cm: float,
    bottom_cm: float,
    width_cm: float,
) -> tuple[plt.Axes, float]:
    height_cm = width_cm / asset.aspect
    left_cm = center_x_cm - width_cm / 2.0
    ax = fig.add_axes(
        (
            left_cm / FIGURE_WIDTH_CM,
            bottom_cm / figure_height_cm,
            width_cm / FIGURE_WIDTH_CM,
            height_cm / figure_height_cm,
        )
    )
    ax.imshow(asset.image)
    ax.set_axis_off()
    ax.set_anchor("C")
    return ax, height_cm


def panel_label(
    fig: plt.Figure,
    *,
    figure_height_cm: float,
    x_cm: float,
    y_cm: float,
    label: str,
) -> None:
    fig.text(
        x_cm / FIGURE_WIDTH_CM,
        y_cm / figure_height_cm,
        label,
        ha="left",
        va="top",
        fontsize=9.5,
        fontweight="bold",
        color="#111111",
    )


def save_pair(fig: plt.Figure, stem: str) -> None:
    MANUSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        MANUSCRIPT_DIR / f"{stem}.png",
        dpi=EXPORT_DPI,
        bbox_inches=None,
        pad_inches=0,
    )
    fig.savefig(
        MANUSCRIPT_DIR / f"{stem}.pdf",
        format="pdf",
        bbox_inches=None,
        pad_inches=0,
    )
    plt.close(fig)
    print(f"Saved {stem}.png and {stem}.pdf")


def make_t80_composite() -> None:
    histogram = prepare_panel(
        "Stage 3 Output_expanded/vis_stage3_hist_T80_2pc50.png"
    )
    map_panel = prepare_panel(
        "Stage 3 Output_expanded/vis_stage3_map_T80_2pc50.png"
    )

    side_margin_cm = 0.55
    gap_cm = 0.60
    scale = (
        FIGURE_WIDTH_CM - 2.0 * side_margin_cm - gap_cm
    ) / (histogram.width_cm + map_panel.width_cm)
    hist_width_cm = histogram.width_cm * scale
    map_width_cm = map_panel.width_cm * scale
    hist_height_cm = histogram.height_cm * scale
    map_height_cm = map_panel.height_cm * scale
    figure_height_cm = max(hist_height_cm, map_height_cm) + 1.05

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(figure_height_cm)))
        row_bottom_cm = 0.35
        hist_center = side_margin_cm + hist_width_cm / 2.0
        map_center = (
            side_margin_cm
            + hist_width_cm
            + gap_cm
            + map_width_cm / 2.0
        )
        place_asset(
            fig,
            histogram,
            figure_height_cm=figure_height_cm,
            center_x_cm=hist_center,
            bottom_cm=row_bottom_cm
            + (max(hist_height_cm, map_height_cm) - hist_height_cm) / 2.0,
            width_cm=hist_width_cm,
        )
        place_asset(
            fig,
            map_panel,
            figure_height_cm=figure_height_cm,
            center_x_cm=map_center,
            bottom_cm=row_bottom_cm
            + (max(hist_height_cm, map_height_cm) - map_height_cm) / 2.0,
            width_cm=map_width_cm,
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.12,
            y_cm=figure_height_cm - 0.10,
            label="A",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=side_margin_cm + hist_width_cm + gap_cm - 0.18,
            y_cm=figure_height_cm - 0.10,
            label="B",
        )
        print(f"T80 panel scale: A={scale:.3f}, B={scale:.3f}")
        save_pair(fig, "t80_distribution_and_spatial_pattern_composite")


def make_recovery_composite() -> None:
    recovery = prepare_panel(
        "Stage 6 Output_expanded/vis_stage6_recovery_curve_2pc50_population.png"
    )
    dumbbell = prepare_panel(
        "Stage 6 Output_expanded/vis_stage6_t80_counterpart_dumbbell_2pc50.png"
    )
    topology_dual = prepare_panel(
        "Stage 6 Output_expanded/vis_stage6_topology_dual_2pc50.png"
    )
    panels = [recovery, dumbbell, topology_dual]

    side_margin_cm = 0.45
    gap_cm = 0.55
    available_width_cm = FIGURE_WIDTH_CM - 2.0 * side_margin_cm
    scale = min(available_width_cm / panel.width_cm for panel in panels)
    widths_cm = [panel.width_cm * scale for panel in panels]
    heights_cm = [panel.height_cm * scale for panel in panels]
    figure_height_cm = sum(heights_cm) + 2.0 * gap_cm + 0.80

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(figure_height_cm)))
        top_cm = figure_height_cm - 0.30
        row_tops: list[float] = []
        for panel, width, height in zip(panels, widths_cm, heights_cm):
            row_tops.append(top_cm)
            bottom_cm = top_cm - height
            place_asset(
                fig,
                panel,
                figure_height_cm=figure_height_cm,
                center_x_cm=FIGURE_WIDTH_CM / 2.0,
                bottom_cm=bottom_cm,
                width_cm=width,
            )
            top_cm = bottom_cm - gap_cm

        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.10,
            y_cm=row_tops[0],
            label="A",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.10,
            y_cm=row_tops[1],
            label="B",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.10,
            y_cm=row_tops[2],
            label="C",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=FIGURE_WIDTH_CM / 2.0 + 0.05,
            y_cm=row_tops[2],
            label="D",
        )
        print(
            "Recovery panel scales: "
            + ", ".join(f"{label}={scale:.3f}" for label in "ABC")
        )
        save_pair(fig, "recovery_strategy_and_topology_composite")


def make_typology_composite() -> None:
    kde = prepare_panel("Stage 7 Output_expanded/vis_stage7_kde_profiles.png")
    heatmap = prepare_panel("Stage 7 Output_expanded/vis_stage7_heatmap.png")
    cluster_map = prepare_panel(
        "Stage 7 Output_expanded/vis_stage7_map_clusters.png"
    )
    hotspot_map = prepare_panel(
        "Stage 7 Output_expanded/vis_stage7_map_hotspot_score.png"
    )

    side_margin_cm = 0.45
    gap_cm = 0.55
    available_width_cm = FIGURE_WIDTH_CM - 2.0 * side_margin_cm - gap_cm
    top_scale = available_width_cm / (kde.width_cm + heatmap.width_cm)
    bottom_scale = available_width_cm / (
        cluster_map.width_cm + hotspot_map.width_cm
    )

    kde_width_cm = kde.width_cm * top_scale
    heatmap_width_cm = heatmap.width_cm * top_scale
    cluster_width_cm = cluster_map.width_cm * bottom_scale
    hotspot_width_cm = hotspot_map.width_cm * bottom_scale
    top_height_cm = max(
        kde.height_cm * top_scale,
        heatmap.height_cm * top_scale,
    )
    bottom_height_cm = max(
        cluster_map.height_cm * bottom_scale,
        hotspot_map.height_cm * bottom_scale,
    )
    row_gap_cm = 0.65
    figure_height_cm = top_height_cm + bottom_height_cm + row_gap_cm + 0.75

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(figure_height_cm)))
        bottom_row_y_cm = 0.25
        top_row_y_cm = bottom_row_y_cm + bottom_height_cm + row_gap_cm

        kde_center = side_margin_cm + kde_width_cm / 2.0
        heatmap_center = (
            side_margin_cm + kde_width_cm + gap_cm + heatmap_width_cm / 2.0
        )
        cluster_center = side_margin_cm + cluster_width_cm / 2.0
        hotspot_center = (
            side_margin_cm
            + cluster_width_cm
            + gap_cm
            + hotspot_width_cm / 2.0
        )

        place_asset(
            fig,
            kde,
            figure_height_cm=figure_height_cm,
            center_x_cm=kde_center,
            bottom_cm=top_row_y_cm
            + (top_height_cm - kde.height_cm * top_scale) / 2.0,
            width_cm=kde_width_cm,
        )
        place_asset(
            fig,
            heatmap,
            figure_height_cm=figure_height_cm,
            center_x_cm=heatmap_center,
            bottom_cm=top_row_y_cm
            + (top_height_cm - heatmap.height_cm * top_scale) / 2.0,
            width_cm=heatmap_width_cm,
        )
        place_asset(
            fig,
            cluster_map,
            figure_height_cm=figure_height_cm,
            center_x_cm=cluster_center,
            bottom_cm=bottom_row_y_cm
            + (bottom_height_cm - cluster_map.height_cm * bottom_scale) / 2.0,
            width_cm=cluster_width_cm,
        )
        place_asset(
            fig,
            hotspot_map,
            figure_height_cm=figure_height_cm,
            center_x_cm=hotspot_center,
            bottom_cm=bottom_row_y_cm
            + (bottom_height_cm - hotspot_map.height_cm * bottom_scale) / 2.0,
            width_cm=hotspot_width_cm,
        )

        top_label_y = figure_height_cm - 0.10
        bottom_label_y = bottom_row_y_cm + bottom_height_cm + 0.12
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.10,
            y_cm=top_label_y,
            label="A",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=side_margin_cm + kde_width_cm + gap_cm - 0.18,
            y_cm=top_label_y,
            label="B",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.10,
            y_cm=bottom_label_y,
            label="C",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=side_margin_cm + cluster_width_cm + gap_cm - 0.18,
            y_cm=bottom_label_y,
            label="D",
        )
        print(
            "Typology panel scales: "
            f"A/B={top_scale:.3f}, C/D={bottom_scale:.3f}"
        )
        save_pair(fig, "recovery_vulnerability_typology_composite")


def make_topology_composite() -> None:
    direct_links = prepare_panel("Data/topology_final_validation_expanded.png")
    topology = prepare_panel(
        "Stage 2 Output_expanded/vis_stage2_topology_with_tracts_latlon.png"
    )
    robustness = prepare_panel(
        "Stage 2 Output_expanded/"
        "vis_stage2_percolation_compare_targeted_attacks.png"
    )
    panels = [direct_links, topology, robustness]

    side_margin_cm = 0.45
    gap_cm = 0.55
    available_width_cm = FIGURE_WIDTH_CM - 2.0 * side_margin_cm
    common_scale = min(available_width_cm / panel.width_cm for panel in panels)
    widths_cm = [panel.width_cm * common_scale for panel in panels]
    heights_cm = [panel.height_cm * common_scale for panel in panels]
    figure_height_cm = sum(heights_cm) + 2.0 * gap_cm + 0.75

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(figure_height_cm)))
        top_cm = figure_height_cm - 0.25
        row_tops: list[float] = []
        for panel, width, height in zip(panels, widths_cm, heights_cm):
            row_tops.append(top_cm)
            bottom_cm = top_cm - height
            place_asset(
                fig,
                panel,
                figure_height_cm=figure_height_cm,
                center_x_cm=FIGURE_WIDTH_CM / 2.0,
                bottom_cm=bottom_cm,
                width_cm=width,
            )
            top_cm = bottom_cm - gap_cm

        for label, row_top in zip("ABC", row_tops):
            panel_label(
                fig,
                figure_height_cm=figure_height_cm,
                x_cm=0.10,
                y_cm=row_top,
                label=label,
            )
        print(
            "Topology panel scales: "
            + ", ".join(
                f"{label}={common_scale:.3f}" for label in "ABC"
            )
        )
        save_pair(fig, "topology_abstraction_and_robustness_composite")


def main() -> None:
    make_t80_composite()
    make_recovery_composite()
    make_typology_composite()
    make_topology_composite()


if __name__ == "__main__":
    main()
