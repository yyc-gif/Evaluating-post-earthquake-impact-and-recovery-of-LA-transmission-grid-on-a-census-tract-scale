"""Assemble manuscript composites from existing generated PNG figures.

This script does not redraw analytical results. It only crops exterior white
margin, scales and positions complete source figures, and adds panel letters.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


CM_PER_INCH = 2.54
EXPORT_DPI = 600
FIGURE_WIDTH_CM = 18.5
NA_TRACT_RGB = np.array([85, 85, 85], dtype=np.uint8)

ROOT = Path(__file__).resolve().parent
MANUSCRIPT_DIR = ROOT / "Manuscript_Figures"

RC = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 9.0,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.facecolor": "white",
}


def cm(value: float) -> float:
    return value / CM_PER_INCH


def load_panel(
    relative_path: str,
    *,
    crop_padding_px: int = 12,
    darken_na: bool = False,
) -> np.ndarray:
    path = ROOT / relative_path
    image = np.asarray(Image.open(path).convert("RGB"))

    content = np.any(image < 248, axis=2)
    rows, columns = np.where(content)
    if rows.size:
        left = max(0, int(columns.min()) - crop_padding_px)
        right = min(image.shape[1], int(columns.max()) + crop_padding_px + 1)
        top = max(0, int(rows.min()) - crop_padding_px)
        bottom = min(image.shape[0], int(rows.max()) + crop_padding_px + 1)
        image = image[top:bottom, left:right].copy()
    else:
        image = image.copy()

    if darken_na:
        channel_range = image.max(axis=2) - image.min(axis=2)
        channel_mean = image.mean(axis=2)
        na_fill = (
            (channel_range <= 4)
            & (channel_mean >= 198)
            & (channel_mean <= 220)
        )
        image[na_fill] = NA_TRACT_RGB

    return image


def place_panel(
    fig: plt.Figure,
    rect: tuple[float, float, float, float],
    relative_path: str,
    *,
    darken_na: bool = False,
) -> plt.Axes:
    ax = fig.add_axes(rect)
    ax.imshow(load_panel(relative_path, darken_na=darken_na))
    ax.set_axis_off()
    ax.set_anchor("C")
    return ax


def panel_label(
    fig: plt.Figure,
    x: float,
    y: float,
    label: str,
) -> None:
    fig.text(
        x,
        y,
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
    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(7.2)))
        place_panel(
            fig,
            (0.035, 0.12, 0.365, 0.81),
            "Stage 3 Output_expanded/vis_stage3_hist_T80_2pc50.png",
        )
        place_panel(
            fig,
            (0.425, 0.055, 0.555, 0.895),
            "Stage 3 Output_expanded/vis_stage3_map_T80_2pc50.png",
        )
        panel_label(fig, 0.012, 0.965, "A")
        panel_label(fig, 0.405, 0.965, "B")
        save_pair(fig, "t80_distribution_and_spatial_pattern_composite")


def make_recovery_composite() -> None:
    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(24.5)))
        place_panel(
            fig,
            (0.035, 0.695, 0.93, 0.285),
            "Stage 6 Output_expanded/vis_stage6_recovery_curve_2pc50_population.png",
        )
        place_panel(
            fig,
            (0.105, 0.365, 0.79, 0.305),
            "Stage 6 Output_expanded/vis_stage6_t80_counterpart_dumbbell_2pc50.png",
        )
        place_panel(
            fig,
            (0.05, 0.012, 0.90, 0.37),
            "Stage 6 Output_expanded/vis_stage6_topology_dual_2pc50.png",
        )
        panel_label(fig, 0.012, 0.988, "A")
        panel_label(fig, 0.078, 0.678, "B")
        panel_label(fig, 0.025, 0.382, "C")
        panel_label(fig, 0.505, 0.382, "D")
        save_pair(fig, "recovery_strategy_and_topology_composite")


def make_typology_composite() -> None:
    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(14.3)))
        place_panel(
            fig,
            (0.025, 0.55, 0.48, 0.425),
            "Stage 7 Output_expanded/vis_stage7_kde_profiles.png",
        )
        place_panel(
            fig,
            (0.53, 0.56, 0.445, 0.405),
            "Stage 7 Output_expanded/vis_stage7_heatmap.png",
        )
        place_panel(
            fig,
            (0.03, 0.035, 0.43, 0.47),
            "Stage 7 Output_expanded/vis_stage7_map_clusters.png",
            darken_na=True,
        )
        place_panel(
            fig,
            (0.47, 0.035, 0.505, 0.47),
            "Stage 7 Output_expanded/vis_stage7_map_hotspot_score.png",
            darken_na=True,
        )
        panel_label(fig, 0.008, 0.985, "A")
        panel_label(fig, 0.512, 0.985, "B")
        panel_label(fig, 0.008, 0.515, "C")
        panel_label(fig, 0.455, 0.515, "D")
        save_pair(fig, "recovery_vulnerability_typology_composite")


def make_topology_composite() -> None:
    with mpl.rc_context(RC):
        fig = plt.figure(figsize=(cm(FIGURE_WIDTH_CM), cm(13.8)))
        place_panel(
            fig,
            (0.025, 0.53, 0.45, 0.445),
            "Data/topology_final_validation_expanded.png",
        )
        place_panel(
            fig,
            (0.49, 0.53, 0.485, 0.445),
            "Stage 2 Output_expanded/vis_stage2_topology_with_tracts_latlon.png",
        )
        place_panel(
            fig,
            (0.025, 0.035, 0.95, 0.44),
            "Stage 2 Output_expanded/vis_stage2_percolation_compare_targeted_attacks.png",
        )
        panel_label(fig, 0.005, 0.99, "A")
        panel_label(fig, 0.475, 0.99, "B")
        panel_label(fig, 0.005, 0.495, "C")
        save_pair(fig, "topology_abstraction_and_robustness_composite")


def main() -> None:
    make_t80_composite()
    make_recovery_composite()
    make_typology_composite()
    make_topology_composite()


if __name__ == "__main__":
    main()
