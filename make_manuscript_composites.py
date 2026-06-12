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

from matplotlib import colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
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

STAGE7_CLUSTER_COLORS = {
    "C1": "#607D9E",
    "C2": "#B99B4A",
    "C3": "#5E8B61",
    "C4": "#86AFC0",
    "C5": "#92607F",
    "C6": "#B97070",
}
STAGE7_NA_COLOR = "#D9D9D9"
STAGE7_HOTSPOT_COLOR = "#222222"
STAGE7_HOTSPOT_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "stage7_hotspot_score",
    ["#2C7BB6", "#ABD9E9", "#FFFFBF", "#F46D43", "#8B1E3F"],
)


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


def prepare_map_body_panel(
    relative_path: str,
    *,
    suffix: str,
    ignore_right_after: float | None = None,
    ignore_bottom_after: float = 0.88,
    crop_padding_px: int = 18,
) -> PanelAsset:
    """Crop a Stage 7 map to its map body so legends can be rebuilt uniformly."""
    cache_key = f"{relative_path}|{suffix}|body"
    cached = _PANEL_CACHE.get(cache_key)
    if cached is not None:
        return cached

    source_path = ROOT / relative_path
    source = Image.open(source_path)
    dpi = source.info.get("dpi", (EXPORT_DPI, EXPORT_DPI))
    dpi_x = float(dpi[0]) if dpi and dpi[0] else float(EXPORT_DPI)
    dpi_y = float(dpi[1]) if dpi and dpi[1] else float(EXPORT_DPI)
    rgb = np.asarray(source.convert("RGB"))
    h, w, _ = rgb.shape

    content = np.any(rgb < 245, axis=2)
    content[int(h * ignore_bottom_after) :, :] = False
    if ignore_right_after is not None:
        content[:, int(w * ignore_right_after) :] = False
    rows, columns = np.where(content)
    if not rows.size:
        return prepare_panel(relative_path)

    left = max(0, int(columns.min()) - crop_padding_px)
    right = min(w, int(columns.max()) + crop_padding_px + 1)
    top = max(0, int(rows.min()) - crop_padding_px)
    bottom = min(h, int(rows.max()) + crop_padding_px + 1)
    cropped = source.convert("RGB").crop((left, top, right, bottom))
    asset = PanelAsset(
        relative_path=cache_key,
        prepared_path=source_path,
        image=np.asarray(cropped),
        width_cm=cropped.width / dpi_x * CM_PER_INCH,
        height_cm=cropped.height / dpi_y * CM_PER_INCH,
    )
    _PANEL_CACHE[cache_key] = asset
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


def _format_composite_legend(legend) -> None:
    if legend is None:
        return
    legend.get_frame().set_linewidth(0.0)
    for text in legend.get_texts():
        text.set_fontsize(7.5)
    title = legend.get_title()
    if title is not None:
        title.set_fontsize(7.5)


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

    gap_cm = 0.35
    shared_scale = min(
        1.0,
        (FULL_ROW_WIDTH_CM - gap_cm) / (histogram.width_cm + map_panel.width_cm),
    )
    hist_width_cm = histogram.width_cm * shared_scale
    map_width_cm = map_panel.width_cm * shared_scale
    hist_scale = hist_width_cm / histogram.width_cm
    map_scale = map_width_cm / map_panel.width_cm
    hist_height_cm = hist_width_cm / histogram.aspect
    map_height_cm = map_width_cm / map_panel.aspect
    content_height_cm = max(hist_height_cm, map_height_cm)
    figure_height_cm = content_height_cm + 0.60

    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(figure_height_cm)))
        bottom_cm = 0.28
        left_x_cm = FULL_ROW_MARGIN_CM + hist_width_cm / 2.0
        right_x_cm = (
            FULL_ROW_MARGIN_CM
            + hist_width_cm
            + gap_cm
            + map_width_cm / 2.0
        )
        hist_bottom_cm = bottom_cm + (content_height_cm - hist_height_cm) / 2.0
        map_bottom_cm = bottom_cm + (content_height_cm - map_height_cm) / 2.0
        place_asset(
            fig,
            histogram,
            figure_height_cm=figure_height_cm,
            center_x_cm=left_x_cm,
            bottom_cm=hist_bottom_cm,
            width_cm=hist_width_cm,
        )
        place_asset(
            fig,
            map_panel,
            figure_height_cm=figure_height_cm,
            center_x_cm=right_x_cm,
            bottom_cm=map_bottom_cm,
            width_cm=map_width_cm,
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=0.12,
            y_cm=hist_bottom_cm + hist_height_cm - 0.08,
            label="A",
        )
        panel_label(
            fig,
            figure_height_cm=figure_height_cm,
            x_cm=FULL_ROW_MARGIN_CM + hist_width_cm + gap_cm - 0.03,
            y_cm=map_bottom_cm + map_height_cm - 0.08,
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
    cluster_map = prepare_map_body_panel(
        "Stage 7 Output_expanded/vis_stage7_map_clusters.png",
        suffix="mapbody",
    )
    hotspot_map = prepare_map_body_panel(
        "Stage 7 Output_expanded/vis_stage7_map_hotspot_score.png",
        suffix="mapbody",
        ignore_right_after=0.86,
    )

    row_gap_cm = 0.55
    bottom_gap_cm = 0.55
    legend_height_cm = 0.95
    cbar_pad_cm = 0.22
    cbar_width_cm = 0.30
    cbar_text_allowance_cm = 0.90
    kde_width_cm = native_width(kde)
    heatmap_width_cm = native_width(heatmap)
    map_body_height_cm = (
        FULL_ROW_WIDTH_CM
        - bottom_gap_cm
        - cbar_pad_cm
        - cbar_width_cm
        - cbar_text_allowance_cm
    ) / (cluster_map.aspect + hotspot_map.aspect)
    cluster_width_cm = map_body_height_cm * cluster_map.aspect
    hotspot_width_cm = map_body_height_cm * hotspot_map.aspect
    bottom_height_cm = map_body_height_cm + legend_height_cm
    scales = [
        kde_width_cm / kde.width_cm,
        heatmap_width_cm / heatmap.width_cm,
        cluster_width_cm / cluster_map.width_cm,
        hotspot_width_cm / hotspot_map.width_cm,
    ]
    heights_cm = [
        kde_width_cm / kde.aspect,
        heatmap_width_cm / heatmap.aspect,
        map_body_height_cm,
        map_body_height_cm,
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
        legend_bottom_cm = bottom_row_bottom_cm + 0.05
        map_bottom_cm = bottom_row_bottom_cm + legend_height_cm
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
            bottom_cm=map_bottom_cm,
            width_cm=cluster_width_cm,
        )
        place_asset(
            fig,
            hotspot_map,
            figure_height_cm=figure_height_cm,
            center_x_cm=right_center_cm,
            bottom_cm=map_bottom_cm,
            width_cm=hotspot_width_cm,
        )

        cluster_handles = [
            Patch(facecolor=STAGE7_CLUSTER_COLORS[f"C{i}"], edgecolor="none", label=f"C{i}")
            for i in range(1, 7)
        ]
        cluster_handles.append(Patch(facecolor=STAGE7_NA_COLOR, edgecolor="none", label="N/A"))
        cluster_handles.append(
            Line2D(
                [0],
                [0],
                color=STAGE7_HOTSPOT_COLOR,
                linewidth=1.2,
                label="Top-10 hotspots",
            )
        )
        cluster_legend = fig.legend(
            handles=cluster_handles,
            loc="lower center",
            bbox_to_anchor=(
                left_center_cm / FIGURE_WIDTH_CM,
                (legend_bottom_cm + 0.04) / figure_height_cm,
            ),
            bbox_transform=fig.transFigure,
            frameon=False,
            ncol=4,
            columnspacing=0.70,
            handlelength=0.82,
            handletextpad=0.28,
            borderpad=0.0,
            labelspacing=0.18,
        )
        _format_composite_legend(cluster_legend)

        hotspot_handles = [
            Patch(facecolor=STAGE7_NA_COLOR, edgecolor="none", label="N/A"),
            Line2D(
                [0],
                [0],
                color=STAGE7_HOTSPOT_COLOR,
                linewidth=1.2,
                label="Top-10 hotspot boundary",
            ),
        ]
        hotspot_legend = fig.legend(
            handles=hotspot_handles,
            loc="lower center",
            bbox_to_anchor=(
                right_center_cm / FIGURE_WIDTH_CM,
                (legend_bottom_cm + 0.04) / figure_height_cm,
            ),
            bbox_transform=fig.transFigure,
            frameon=False,
            ncol=2,
            columnspacing=0.95,
            handlelength=1.20,
            handletextpad=0.35,
            borderpad=0.0,
        )
        _format_composite_legend(hotspot_legend)

        cbar_left_cm = (
            right_center_cm
            + hotspot_width_cm / 2.0
            + cbar_pad_cm
        )
        cax = fig.add_axes(
            (
                cbar_left_cm / FIGURE_WIDTH_CM,
                map_bottom_cm / figure_height_cm,
                cbar_width_cm / FIGURE_WIDTH_CM,
                map_body_height_cm / figure_height_cm,
            )
        )
        sm = mpl.cm.ScalarMappable(
            cmap=STAGE7_HOTSPOT_CMAP,
            norm=mcolors.Normalize(vmin=0.0, vmax=4.0),
        )
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax, ticks=np.arange(0.0, 4.1, 1.0))
        cbar.ax.tick_params(labelsize=7.5, width=0.6, length=2.5)
        cbar.outline.set_linewidth(0.5)
        cbar.set_label(
            "Recovery-vulnerability hotspot score (0-4)",
            fontsize=7.5,
            labelpad=6,
        )

        label_specs = [
            ("A", 0.10, kde_bottom_cm + heights_cm[0] - 0.04),
            ("B", 0.10, heatmap_bottom_cm + heights_cm[1] - 0.04),
            ("C", FULL_ROW_MARGIN_CM - 0.08, map_bottom_cm + map_body_height_cm - 0.04),
            ("D", FULL_ROW_MARGIN_CM + cluster_width_cm + bottom_gap_cm - 0.08, map_bottom_cm + map_body_height_cm - 0.04),
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
