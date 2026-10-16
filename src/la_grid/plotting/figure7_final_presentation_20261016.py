"""Rebuild Figure 7 presentation panels from the verified P2/K3 table."""
from __future__ import annotations

import io
import hashlib
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import fitz
from PIL import Image, ImageDraw, ImageOps
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

import figure7_map_readability_20261015 as maps


PAGE_W = 7.2 * 72
LAYOUT_B_H = 10 * 72
LAYOUT_C_H = 650
FEATURES = ["Init_Supply", "Grid_Impact", "Redundancy_HHI", "B_Unconstrained",
            "MeanDelta", "SOVI_SCORE", "log1p_Population"]
LABELS = {
    "Init_Supply": "Initial service availability",
    "Grid_Impact": "Spectral network impact",
    "Redundancy_HHI": "Dependency concentration (HHI)",
    "B_Unconstrained": "Unconstrained service deficit",
    "MeanDelta": "Mean additional service deficit (five policies)",
    "SOVI_SCORE": "Social vulnerability score",
    "log1p_Population": "Tract population",
}
PANEL_A = ["Grid_Impact", "Redundancy_HHI", "B_Unconstrained", "MeanDelta",
           "SOVI_SCORE", "Population"]
PANEL_TITLES = {
    "Grid_Impact": "Spectral network impact",
    "Redundancy_HHI": "Dependency concentration (HHI)",
    "B_Unconstrained": "Unconstrained service deficit",
    "MeanDelta": "Mean additional service deficit (five policies)",
    "SOVI_SCORE": "Social vulnerability score",
    "Population": "Tract population",
}
UNITS = {
    "Grid_Impact": "Unitless",
    "Redundancy_HHI": "Unitless",
    "B_Unconstrained": "Equivalent deficit hours",
    "MeanDelta": "Equivalent deficit hours",
    "SOVI_SCORE": "Score (0-100)",
    "Population": "Persons",
}
LINE_STYLES = ["-", "--", ":"]
PROPOSED = {1: "#3C9198", 2: "#52699E", 3: "#C69EBA"}
DARKER_MAUVE = {1: "#3C9198", 2: "#52699E", 3: "#A87596"}


def _axes(fig, x, top, width, height, page_height):
    return fig.add_axes([x / PAGE_W, (page_height - top - height) / page_height,
                         width / PAGE_W, height / page_height])


def _fig_text(fig, x, top, value, *, size=7.5, weight="normal", align="left",
              page_height, rotation=0):
    fig.text(x / PAGE_W, 1 - top / page_height, value, fontsize=size,
             fontweight=weight, ha=align, va="top", rotation=rotation,
             color="#202020")


def _axis_limits(values):
    lo = float(np.min(values))
    hi = float(np.max(values))
    span = hi - lo
    pad = span * 0.025 if span else max(abs(lo), 1.0) * 0.025
    return lo - pad, hi + pad


def _format_population_axis(ax):
    values = ax.get_xticks()
    ax.set_xticks(values)
    ax.set_xticklabels([f"{v:,.0f}" if abs(v) >= 1000 else f"{v:g}" for v in values])


def _draw_ecdf(ax, data, variable, palette, cohort):
    for class_id, linestyle in zip((1, 2, 3), LINE_STYLES):
        values = np.sort(data.loc[data.P2_K3_class.eq(class_id), variable].to_numpy(dtype=float))
        y = np.arange(1, values.size + 1, dtype=float) / values.size
        ax.step(values, y, where="post", color=palette[class_id], linestyle=linestyle,
                linewidth=1.05, solid_capstyle="butt")
        ax.plot(np.median(values), 0.5, marker="o", markersize=3.0,
                color=palette[class_id], linestyle="none", zorder=4)
    values = cohort[variable].to_numpy(dtype=float)
    ax.set_xlim(*_axis_limits(values))
    ax.set_ylim(0, 1)
    ax.set_yticks([0, 0.5, 1])
    ax.set_yticklabels(["0", "0.5", "1"], fontsize=7.5)
    ax.axhline(0.5, color="#9A9A9A", linewidth=0.45, zorder=0)
    ax.set_xlabel(UNITS[variable], fontsize=7.5, labelpad=1.5)
    ax.set_title(PANEL_TITLES[variable], fontsize=7.5, pad=3.0, color="#202020")
    ax.tick_params(axis="x", labelsize=7.5, length=2.2, width=0.45, pad=1.5)
    ax.tick_params(axis="y", length=2.2, width=0.45, pad=1.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#8E8E8E")
        ax.spines[side].set_linewidth(0.55)
    if variable == "Population":
        _format_population_axis(ax)


def _draw_profiles(fig, profile, palette, *, layout):
    if layout == "B":
        title_top, grid_top, grid_height = 267, 292, 100
        left, grid_width, colorbar_x = 258, 184, 462
        page_height = 410
    else:
        title_top, grid_top, grid_height = 270, 290, 82
        left, grid_width, colorbar_x = 258, 184, 462
        page_height = 390
    _fig_text(fig, PAGE_W / 2, title_top, "B. Standardized cluster profiles",
              size=9.5, weight="bold", align="center", page_height=page_height)
    ax = _axes(fig, left, grid_top, grid_width, grid_height, page_height)
    values = profile.loc[["C1", "C2", "C3"], FEATURES].to_numpy(dtype=float).T
    norm = TwoSlopeNorm(vmin=-1.5, vcenter=0, vmax=1.5)
    image = ax.pcolormesh(np.arange(4), np.arange(8), values,
                          cmap="RdBu_r", norm=norm, edgecolors="white",
                          linewidth=0.25, shading="flat", rasterized=False)
    ax.set_xlim(0, 3)
    ax.set_ylim(7, 0)
    ax.set_xticks(np.arange(3) + 0.5, ["C1", "C2", "C3"])
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", length=0, pad=2.5, labelsize=7.5)
    for tick, class_id in zip(ax.get_xticklabels(), (1, 2, 3)):
        tick.set_color(palette[class_id])
        tick.set_fontweight("bold")
    ax.set_yticks(np.arange(7) + 0.5, [LABELS[name] for name in FEATURES])
    ax.tick_params(axis="y", length=0, pad=4, labelsize=7.5)
    ax.set_yticklabels([LABELS[name] for name in FEATURES], fontsize=7.5)
    ax.set_frame_on(False)
    for row in range(7):
        for col in range(3):
            value = values[row, col]
            ax.text(col + 0.5, row + 0.5, f"{value:+.2f}", ha="center", va="center",
                    fontsize=7.5, color="white" if abs(value) > 1 else "#202020")
    for y in (3, 5):
        ax.axhline(y, color="#242424", linewidth=0.75, clip_on=False)
    row_centers = [grid_top + grid_height * (1.5 / 7),
                   grid_top + grid_height * (4 / 7),
                   grid_top + grid_height * (6 / 7)]
    for group, top in zip(("RQ1", "RQ2", "RQ3"), row_centers):
        _fig_text(fig, 70, top - 4.0, group, size=7.5, weight="bold",
                  align="right", page_height=page_height)
    cax = _axes(fig, colorbar_x, grid_top, 10, grid_height, page_height)
    cmap = plt.get_cmap("RdBu_r")
    bins = 256
    for i in range(bins):
        y0 = -1.5 + 3 * i / bins
        cax.add_patch(Rectangle((0, y0), 1, 3 / bins + 0.001,
                                facecolor=cmap((i + 0.5) / bins), edgecolor="none",
                                linewidth=0, antialiased=False))
    cax.set_xlim(0, 1)
    cax.set_ylim(-1.5, 1.5)
    cax.set_xticks([])
    cax.set_yticks([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])
    cax.yaxis.tick_right()
    cax.tick_params(axis="y", labelsize=7.5, length=2, width=0.45, pad=2)
    cax.set_ylabel("Class mean z-score", fontsize=7.5, labelpad=4)
    cax.yaxis.set_label_position("right")
    for side in ("left", "top", "bottom"):
        cax.spines[side].set_visible(False)
    cax.spines["right"].set_color("#333333")
    cax.spines["right"].set_linewidth(0.5)


def build_top_panel(data, profile, palette, *, layout):
    """Create vector-only Panels A/B; `data` is the 2,299-row frozen cohort."""
    if layout not in {"B", "C"}:
        raise ValueError(layout)
    page_height = 410 if layout == "B" else 390
    matplotlib.rcParams.update({
        "font.family": "Arial",
        "font.size": 7.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.unicode_minus": False,
        "savefig.facecolor": "white",
    })
    fig = plt.figure(figsize=(7.2, page_height / 72), facecolor="white")
    _fig_text(fig, PAGE_W / 2, 15, "A. Feature distributions", size=9.5,
              weight="bold", align="center", page_height=page_height)
    legend_handles = [Line2D([], [], color=palette[c], linestyle=LINE_STYLES[c - 1],
                             linewidth=1.15, label=f"C{c} (n={int(data.P2_K3_class.eq(c).sum()):,})")
                      for c in (1, 2, 3)]
    fig.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, 1 - 31/page_height),
               ncol=3, frameon=False, fontsize=7.5, handlelength=2.2,
               columnspacing=2.0, handletextpad=0.7, borderaxespad=0)
    if layout == "B":
        x_positions = [39, 207, 375]
        width = 132
        rows = [74, 175]
        height = 58
        placements = [(x, top) for top in rows for x in x_positions]
    else:
        x_positions = [41, 268]
        width = 209
        rows = [58, 132, 206]
        height = 37.5
        placements = [(x, top) for top in rows for x in x_positions]
        _fig_text(fig, 16, 156 if layout == "B" else page_height / 2,
              "Cumulative fraction", size=7.5, align="center",
              page_height=page_height, rotation=90)
    cohort = data.loc[data.Population.gt(0)]
    for variable, (x, top) in zip(PANEL_A, placements):
        ax = _axes(fig, x, top, width, height, page_height)
        _draw_ecdf(ax, data, variable, palette, cohort)
    _draw_profiles(fig, profile, palette, layout=layout)
    output = io.BytesIO()
    fig.savefig(output, format="pdf", metadata={"Title": "Figure 7 panels A and B",
                "Creator": "Figure 7 presentation builder", "CreationDate": None,
                "ModDate": None})
    plt.close(fig)
    return output.getvalue()


def compose_figure(top_pdf, data, display, paths, specification, palette, *, layout):
    """Place new vector A/B above the pinned vector C/D map layers."""
    page_height = 720 if layout == "B" else LAYOUT_C_H
    top_height = 410 if layout == "B" else 390
    map_top = 429 if layout == "B" else 408
    title_baseline = 421.3027 if layout == "B" else 400.0
    output = maps.fitz.open()
    page = output.new_page(width=PAGE_W, height=page_height)
    with maps.fitz.open(stream=top_pdf, filetype="pdf") as top:
        page.show_pdf_page(maps.fitz.Rect(0, 0, PAGE_W, top_height), top, 0,
                           clip=maps.fitz.Rect(0, 0, PAGE_W, top_height), keep_proportion=False)
    maps._fonts(page)
    maps._title(page, maps.TITLE_C, 145.0, baseline=title_baseline)
    maps._title(page, maps.TITLE_D, 394.0, baseline=title_baseline)
    lookup = data.set_index("tract_id")
    color_lookup = {row.tract_id: (row.blue_amber_R, row.blue_amber_G, row.blue_amber_B)
                    for row in display.itertuples()}
    maps.COLORS = dict(palette)
    maps._map_content(page, paths, "C", lookup, color_lookup, specification,
                      outline_width=0.25, scale=1.25, top_y=map_top, center_x=133.488)
    maps._map_content(page, paths, "D", lookup, color_lookup, specification,
                      outline_width=0.25, scale=1.25, top_y=map_top, center_x=387.504)
    if layout == "B":
        maps._class_legend(page, 613, scale=1.25)
        maps._bivariate_legend(page, specification, (318, 615, 493, 657))
        maps._screening_keys(page, 710, 0.25, n_a_x=448)
    else:
        maps._class_legend(page, 588, scale=1.25)
        maps._bivariate_legend(page, specification, (318, 584, 493, 614))
        maps._screening_keys(page, 638, 0.25, n_a_x=132, q4_x=20)
    output.set_metadata({"title": "Figure 7. Community recovery types and social vulnerability",
                         "subject": "P2/K3 classes; continuous SOVI and five-policy recovery burden"})
    return output


def profile_means(data, standardizer):
    values = data[FEATURES].to_numpy(dtype=float)
    means = standardizer.cohort_mean.to_numpy(dtype=float)
    sd = standardizer.population_SD.to_numpy(dtype=float)
    z = (values - means) / sd
    result = pd.DataFrame(z, columns=FEATURES, index=data.index)
    result["class_id"] = data.P2_K3_class.to_numpy()
    return result.groupby("class_id", sort=True)[FEATURES].mean().set_axis(["C1", "C2", "C3"])


def ecdf_qa(data):
    rows = []
    for class_id in (1, 2, 3):
        for variable in PANEL_A:
            values = np.sort(data.loc[data.P2_K3_class.eq(class_id), variable].to_numpy(dtype=np.float64))
            rows.append({"class_id": f"C{class_id}", "variable": variable,
                         "tracts": int(values.size), "median": float(np.median(values)),
                         "minimum": float(values.min()), "maximum": float(values.max()),
                         "zero_count": int(np.count_nonzero(values == 0)),
                         "sorted_values_sha256": __import__("hashlib").sha256(values.tobytes()).hexdigest(),
                         "empirical_step": True, "smoothed": False, "clipped": False})
    return rows


def _linear(rgb):
    rgb = np.asarray(rgb, dtype=float)
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def _encode(rgb):
    rgb = np.asarray(rgb, dtype=float)
    return np.clip(np.where(rgb <= 0.0031308, 12.92 * rgb,
                            1.055 * np.maximum(rgb, 0) ** (1 / 2.4) - 0.055), 0, 1)


def _rgb(hex_value):
    return np.array([int(hex_value[i:i + 2], 16) for i in (1, 3, 5)], dtype=float) / 255


def _hex(rgb):
    return "#" + "".join(f"{int(v):02X}" for v in np.rint(np.clip(rgb, 0, 1) * 255))


def _lab(rgb):
    matrix = np.array([[0.4124564, 0.3575761, 0.1804375],
                       [0.2126729, 0.7151522, 0.0721750],
                       [0.0193339, 0.1191920, 0.9503041]])
    xyz = _linear(rgb) @ matrix.T / np.array([0.95047, 1.0, 1.08883])
    delta = 6 / 29
    f = np.where(xyz > delta ** 3, np.cbrt(xyz), xyz / (3 * delta ** 2) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


SIMULATIONS = {
    "protanopia": np.array([[.152286, 1.052583, -.204868],
                            [.114503, .786281, .099216],
                            [-.003882, -.048116, 1.051998]]),
    "deuteranopia": np.array([[.367322, .860646, -.227968],
                              [.280085, .672501, .047413],
                              [-.01182, .04294, .968881]]),
    "tritanopia": np.array([[1.255528, -.076749, -.178779],
                            [-.078411, .930809, .147602],
                            [.004733, .691367, .3039]]),
}


def write_palette_metrics(directory):
    rows = []
    distance_rows = []
    designs = {"proposed": PROPOSED, "darker_mauve": DARKER_MAUVE}
    for design, palette in designs.items():
        transformed = {"normal": {c: _rgb(v) for c, v in palette.items()}}
        linear_values = {c: _linear(value) for c, value in transformed["normal"].items()}
        gray_y = {c: float(value @ np.array([0.2126, 0.7152, 0.0722]))
                  for c, value in linear_values.items()}
        transformed["grayscale"] = {
            c: np.repeat(_encode(np.repeat(gray_y[c], 3)), 1) for c in palette
        }
        for mode, matrix in SIMULATIONS.items():
            transformed[mode] = {c: _encode(linear_values[c] @ matrix.T) for c in palette}
        for mode, colors in transformed.items():
            for class_id, color in colors.items():
                rgb = np.asarray(color)
                rows.append({"design": design, "class_id": f"C{class_id}",
                             "source_hex": palette[class_id], "view": mode,
                             "simulated_hex": _hex(rgb),
                             "relative_luminance": gray_y[class_id],
                             "cie76_Lab_L": float(_lab(rgb)[0])})
            for a, b in ((1, 2), (1, 3), (2, 3)):
                distance_rows.append({"design": design, "view": mode,
                    "class_pair": f"C{a}-C{b}",
                    "deltaE76": float(np.linalg.norm(_lab(colors[a]) - _lab(colors[b]))),
                    "luminance_difference": abs(gray_y[a] - gray_y[b])})
    pd.DataFrame(rows).to_csv(Path(directory) / "PALETTE_COLOR_VISION_VALUES.csv", index=False,
                              float_format="%.8g", lineterminator="\n")
    pd.DataFrame(distance_rows).to_csv(Path(directory) / "PALETTE_PAIRWISE_DISTANCES.csv", index=False,
                                       float_format="%.8g", lineterminator="\n")


def _simulated_image(image, mode):
    image = image.convert("RGB")
    if mode == "grayscale":
        return ImageOps.grayscale(image).convert("RGB")
    arr = np.asarray(image, dtype=np.float32) / 255
    linear = _linear(arr)
    simulated = _encode(linear @ SIMULATIONS[mode].T)
    return Image.fromarray(np.rint(simulated * 255).astype(np.uint8), "RGB")


def _render_preview(doc, dpi=150):
    pix = doc[0].get_pixmap(dpi=dpi, alpha=False)
    return Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")


def write_accessibility_previews(candidate_b, candidate_c, candidate_alt, directory):
    directory = Path(directory)
    for prefix, doc in (("LAYOUT_C", candidate_c),
                        ("LAYOUT_B_DARKER_MAUVE", candidate_alt)):
        image = _render_preview(doc, dpi=150)
        for mode in ("grayscale", *SIMULATIONS):
            _simulated_image(image, mode).save(directory / f"{prefix}_{mode.upper()}.png")
        if prefix == "LAYOUT_C":
            image.save(directory / "LAYOUT_C_NATIVE_150DPI.png")
    # Inspect the C1-C3 fills as map patches as well as their legend swatches.
    page = _render_preview(candidate_b, dpi=150)
    page.save(directory / "LAYOUT_B_NATIVE_150DPI.png")


def write_narrow_width_previews(candidate_c, directory):
    for width_mm in (140, 90):
        target_px = width_mm / 25.4 * 150
        scale = target_px / PAGE_W
        pix = candidate_c[0].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        pix.save(str(Path(directory) / f"LAYOUT_C_AT_{width_mm}MM_150DPI.png"))


def write_layout_contact_sheet(reference_pdf, candidate_b, candidate_c, directory):
    images = []
    with fitz.open(stream=reference_pdf, filetype="pdf") as doc:
        images.append(_render_preview(doc, dpi=100))
    images.extend([_render_preview(candidate_b, dpi=100), _render_preview(candidate_c, dpi=100)])
    labels = ["Current reference", "Layout B: 7.2 x 10.0 in", "Layout C: 7.2 x 9.03 in"]
    header, gap = 32, 16
    sheet = Image.new("RGB", (sum(img.width for img in images) + 2 * gap,
                                max(img.height for img in images) + header), "white")
    draw = ImageDraw.Draw(sheet)
    x = 0
    for label, image in zip(labels, images):
        draw.text((x + 5, 7), label, fill="#202020")
        sheet.paste(image, (x, header))
        x += image.width + gap
    sheet.save(Path(directory) / "FIG07_LAYOUT_COMPARISON_CONTACT_SHEET.png")
