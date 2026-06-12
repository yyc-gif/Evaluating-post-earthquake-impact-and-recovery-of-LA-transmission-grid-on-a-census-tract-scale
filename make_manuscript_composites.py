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
FULL_ROW_MARGIN_CM = 0.25
FULL_ROW_WIDTH_CM = FIGURE_WIDTH_CM - 2.0 * FULL_ROW_MARGIN_CM

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


def native_width(asset: PanelAsset, *, max_width_cm: float = FULL_ROW_WIDTH_CM) -> float:
    """Use the source figure's physical width unless it must be downscaled."""
    return min(asset.width_cm, max_width_cm)


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

    gap_cm = 0.50
    hist_width_cm = native_width(histogram)
    map_width_cm = native_width(map_panel)
    hist_scale = hist_width_cm / histogram.width_cm
    map_scale = map_width_cm / map_panel.width_cm
    hist_height_cm = hist_width_cm / histogram.aspect
    map_height_cm = map_width_cm / map_panel.aspect
    figure_height_cm = hist_height_cm + map_height_cm + gap_cm + 0.70

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(figure_height_cm)))
        center_x = FIGURE_WIDTH_CM / 2.0
        bottom_b_cm = 0.25
        bottom_a_cm = bottom_b_cm + map_height_cm + gap_cm
        place_asset(
            fig,
            histogram,
            figure_height_cm=figure_height_cm,
            center_x_cm=center_x,
            bottom_cm=bottom_a_cm,
            width_cm=hist_width_cm,
        )
        place_asset(
            fig,
            map_panel,
            figure_height_cm=figure_height_cm,
            center_x_cm=center_x,
            bottom_cm=bottom_b_cm,
            width_cm=map_width_cm,
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.12,
            y_cm=bottom_a_cm + hist_height_cm - 0.08,
            label="A",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.12,
            y_cm=bottom_b_cm + map_height_cm - 0.08,
            label="B",
        )
        print(f"T80 panel scales: A={hist_scale:.3f}, B={map_scale:.3f}")
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

    gap_cm = 0.48
    widths_cm = [native_width(panel) for panel in panels]
    scales = [width / panel.width_cm for width, panel in zip(widths_cm, panels)]
    heights_cm = [width / panel.aspect for width, panel in zip(widths_cm, panels)]
    figure_height_cm = sum(heights_cm) + 2.0 * gap_cm + 0.80

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
            + ", ".join(f"{label}={scale:.3f}" for label, scale in zip("ABC", scales))
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

    row_gap_cm = 0.55
    bottom_gap_cm = 0.35
    # The hotspot panel includes a vertical colorbar, so its full image needs
    # a modest width boost for the two map bodies to read at similar scale.
    hotspot_to_cluster_width = 1.22
    kde_width_cm = native_width(kde)
    heatmap_width_cm = native_width(heatmap)
    cluster_width_cm = (
        FULL_ROW_WIDTH_CM - bottom_gap_cm
    ) / (1.0 + hotspot_to_cluster_width)
    hotspot_width_cm = cluster_width_cm * hotspot_to_cluster_width
    cluster_height_cm = cluster_width_cm / cluster_map.aspect
    hotspot_height_cm = hotspot_width_cm / hotspot_map.aspect
    bottom_height_cm = max(cluster_height_cm, hotspot_height_cm)
    scales = [
        kde_width_cm / kde.width_cm,
        heatmap_width_cm / heatmap.width_cm,
        cluster_width_cm / cluster_map.width_cm,
        hotspot_width_cm / hotspot_map.width_cm,
    ]
    heights_cm = [
        kde_width_cm / kde.aspect,
        heatmap_width_cm / heatmap.aspect,
        cluster_height_cm,
        hotspot_height_cm,
    ]
    figure_height_cm = heights_cm[0] + heights_cm[1] + bottom_height_cm + 2.0 * row_gap_cm + 0.70

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(figure_height_cm)))
        center_x = FIGURE_WIDTH_CM / 2.0
        left_center_cm = FULL_ROW_MARGIN_CM + cluster_width_cm / 2.0
        right_center_cm = (
            FULL_ROW_MARGIN_CM
            + cluster_width_cm
            + bottom_gap_cm
            + hotspot_width_cm / 2.0
        )
        bottom_row_bottom_cm = 0.25
        cluster_bottom_cm = bottom_row_bottom_cm + (bottom_height_cm - cluster_height_cm) / 2.0
        hotspot_bottom_cm = bottom_row_bottom_cm + (bottom_height_cm - hotspot_height_cm) / 2.0
        heatmap_bottom_cm = bottom_row_bottom_cm + bottom_height_cm + row_gap_cm
        kde_bottom_cm = heatmap_bottom_cm + heights_cm[1] + row_gap_cm

        place_asset(
            fig,
            kde,
            figure_height_cm=figure_height_cm,
            center_x_cm=center_x,
            bottom_cm=kde_bottom_cm,
            width_cm=kde_width_cm,
        )
        place_asset(
            fig,
            heatmap,
            figure_height_cm=figure_height_cm,
            center_x_cm=center_x,
            bottom_cm=heatmap_bottom_cm,
            width_cm=heatmap_width_cm,
        )
        place_asset(
            fig,
            cluster_map,
            figure_height_cm=figure_height_cm,
            center_x_cm=left_center_cm,
            bottom_cm=cluster_bottom_cm,
            width_cm=cluster_width_cm,
        )
        place_asset(
            fig,
            hotspot_map,
            figure_height_cm=figure_height_cm,
            center_x_cm=right_center_cm,
            bottom_cm=hotspot_bottom_cm,
            width_cm=hotspot_width_cm,
        )

        label_specs = [
            ("A", 0.10, kde_bottom_cm + heights_cm[0] - 0.04),
            ("B", 0.10, heatmap_bottom_cm + heights_cm[1] - 0.04),
            ("C", FULL_ROW_MARGIN_CM - 0.08, bottom_row_bottom_cm + bottom_height_cm - 0.04),
            ("D", FULL_ROW_MARGIN_CM + cluster_width_cm + bottom_gap_cm - 0.08, bottom_row_bottom_cm + bottom_height_cm - 0.04),
        ]
        for label, x_cm, y_cm in label_specs:
            panel_label(fig, figure_height_cm=figure_height_cm, x_cm=x_cm, y_cm=y_cm, label=label)
        print(
            "Typology panel scales: "
            + ", ".join(f"{label}={scale:.3f}" for label, scale in zip("ABCD", scales))
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

    gap_cm = 0.48
    widths_cm = [native_width(panel) for panel in panels]
    scales = [width / panel.width_cm for width, panel in zip(widths_cm, panels)]
    heights_cm = [width / panel.aspect for width, panel in zip(widths_cm, panels)]
    figure_height_cm = sum(heights_cm) + 2.0 * gap_cm + 0.70

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
                f"{label}={scale:.3f}" for label, scale in zip("ABC", scales)
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
