"""Render and assemble the Stage 2 topology and robustness manuscript figure."""

from dataclasses import replace
from pathlib import Path
import re
import shutil
import sys
import tempfile

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from PIL import Image
from shapely.geometry import LineString

import Project_Visualizer_expanded as expanded_visualizer
import Topology_and_Weight as topology_base
import Topology_and_Weight_expanded as expanded_topology
import topology_visualization


CM_PER_INCH = 2.54
EXPORT_DPI = 600
FIGURE_WIDTH_CM = 18.5
HALF_PANEL_WIDTH_CM = 8.9
HORIZONTAL_GAP_CM = 0.7
VERTICAL_GAP_CM = 0.55
TOP_LABEL_MARGIN_CM = 0.38
MAP_PANEL_HEIGHT_CM = 6.6
ROBUSTNESS_PANEL_HEIGHT_CM = 6.9

PROJECT_ROOT = Path(__file__).resolve().parent
MANUSCRIPT_DIR = PROJECT_ROOT / "Manuscript_Figures"

OUTPUT_STEM = MANUSCRIPT_DIR / "topology_abstraction_and_robustness_composite"


def cm_to_inch(value: float) -> float:
    return value / CM_PER_INCH


def load_panel(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Required panel not found: {path}")
    with Image.open(path) as image:
        return image.convert("RGB").copy()


def image_size_cm(image: Image.Image) -> tuple[float, float]:
    dpi = image.info.get("dpi", (EXPORT_DPI, EXPORT_DPI))
    dpi_x = float(dpi[0]) if dpi and dpi[0] else EXPORT_DPI
    dpi_y = float(dpi[1]) if dpi and dpi[1] else EXPORT_DPI
    return (
        image.width / dpi_x * CM_PER_INCH,
        image.height / dpi_y * CM_PER_INCH,
    )


def render_panel_a(temp_root: Path) -> Path:
    """Render the accepted direct-link topology at its final half-panel width."""
    output_dir = temp_root / "panel_a"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_png = output_dir / "direct_links.png"

    topology_visualization.VALIDATION_MAP_LAYOUT_CM = {
        "width_cm": HALF_PANEL_WIDTH_CM,
        "height_cm": MAP_PANEL_HEIGHT_CM,
    }

    cfg = replace(
        expanded_topology.EXPANDED_PATHS,
        OUTPUT_MAPPING_CSV=str(output_dir / "mapping.csv"),
        OUTPUT_UNTHRESHOLDED_MAPPING_CSV=str(output_dir / "mapping_unthresholded.csv"),
        OUTPUT_GRAPH_EDGES_CSV=str(output_dir / "edges.csv"),
        OUTPUT_GRAPH_NODES_CSV=str(output_dir / "nodes.csv"),
        OUTPUT_PLOT_PNG=str(output_png),
        OUTPUT_INTERACTIVE_HTML=str(output_dir / "validation.html"),
        OUTPUT_SUPPRESSED_THRESHOLD_CSV=str(output_dir / "suppressed.csv"),
        OUTPUT_LINE_SPLIT_AUDIT_CSV=str(output_dir / "line_split_audit.csv"),
        OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_AUDIT_CSV=str(
            output_dir / "projection_anchor_audit.csv"
        ),
        OUTPUT_DIRECT_LINK_PROJECTION_ANCHOR_DEBUG_CSV=str(
            output_dir / "projection_anchor_debug.csv"
        ),
    )
    topology_base.main(cfg)
    if not output_png.exists():
        raise RuntimeError("Half-width direct-link topology panel was not generated.")
    return output_png


def render_panel_b(temp_root: Path) -> Path:
    """Render the simplified topology at its final half-panel width."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    output_root = temp_root / "panel_b_root"
    stage_dir = output_root / "Stage 2 Output_expanded"
    stage_dir.mkdir(parents=True, exist_ok=True)

    boundary_path = temp_root / "expanded_boundary.geojson"
    expanded_visualizer.EXPANDED_BOUNDARY_PATH = boundary_path
    boundary_path = expanded_visualizer.ensure_expanded_boundary_geojson()

    output_png = stage_dir / "vis_stage2_topology_with_tracts_latlon.png"

    def canonical_substation_key(value) -> str:
        text = str(value).strip()
        try:
            number = float(text)
            if np.isfinite(number) and number.is_integer():
                return str(int(number))
        except Exception:
            pass
        digits = re.sub(r"\D", "", text)
        return digits.lstrip("0") if digits else text

    devices = pd.read_csv(
        PROJECT_ROOT / "Data" / "working_area_substations_with_fragility.csv"
    )
    edges = pd.read_csv(
        PROJECT_ROOT / "Data" / "substation_graph_CEC_edges_expanded.csv"
    )
    city = gpd.read_file(boundary_path).to_crs(epsg=4326)
    cec_lines = gpd.read_file(
        PROJECT_ROOT / "Data" / "TransmissionLine_CEC.shp"
    ).to_crs(epsg=4326)

    edge_ids = set(edges["u"].map(canonical_substation_key))
    priority_columns = ["HIFLD_ID", "substation_id", "OBJECTID", "id"]
    candidate_columns = priority_columns + [
        column for column in devices.columns if column not in priority_columns
    ]
    overlaps = {
        column: len(
            edge_ids.intersection(
                set(devices[column].map(canonical_substation_key))
            )
        )
        for column in candidate_columns
        if column in devices.columns
    }
    best_column = max(overlaps, key=overlaps.get)

    devices = devices.copy()
    devices["id_match"] = devices[best_column].map(canonical_substation_key)
    latitude_column = next(
        column
        for column in ["lat", "Latitude", "Lat", "LAT", "LATITUDE"]
        if column in devices.columns
    )
    longitude_column = next(
        column
        for column in ["lon", "Longitude", "Lon", "LON", "LONGITUDE"]
        if column in devices.columns
    )
    devices[latitude_column] = pd.to_numeric(
        devices[latitude_column], errors="coerce"
    )
    devices[longitude_column] = pd.to_numeric(
        devices[longitude_column], errors="coerce"
    )
    devices = devices.dropna(subset=[latitude_column, longitude_column])

    latitude_lookup = dict(zip(devices["id_match"], devices[latitude_column]))
    longitude_lookup = dict(zip(devices["id_match"], devices[longitude_column]))
    edges = edges.copy()
    edges["u_clean"] = edges["u"].map(canonical_substation_key)
    edges["v_clean"] = edges["v"].map(canonical_substation_key)
    edges["lat_u"] = edges["u_clean"].map(latitude_lookup)
    edges["lon_u"] = edges["u_clean"].map(longitude_lookup)
    edges["lat_v"] = edges["v_clean"].map(latitude_lookup)
    edges["lon_v"] = edges["v_clean"].map(longitude_lookup)
    edges = edges.dropna(subset=["lat_u", "lon_u", "lat_v", "lon_v"])

    nodes_gdf = gpd.GeoDataFrame(
        devices,
        geometry=gpd.points_from_xy(
            devices[longitude_column], devices[latitude_column]
        ),
        crs="EPSG:4326",
    )
    edges_gdf = gpd.GeoDataFrame(
        edges,
        geometry=[
            LineString(
                [
                    (row.lon_u, row.lat_u),
                    (row.lon_v, row.lat_v),
                ]
            )
            for row in edges.itertuples()
        ],
        crs="EPSG:4326",
    )

    xmin, ymin, xmax, ymax = city.total_bounds
    cec_lines = cec_lines.cx[xmin:xmax, ymin:ymax]
    dx, dy = xmax - xmin, ymax - ymin

    publication_style = {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "axes.labelsize": 8.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.0,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
    with plt.rc_context(publication_style):
        fig, ax = plt.subplots(
            figsize=(
                cm_to_inch(HALF_PANEL_WIDTH_CM),
                cm_to_inch(MAP_PANEL_HEIGHT_CM),
            )
        )
        city.plot(
            ax=ax,
            facecolor="none",
            edgecolor="#bdbdbd",
            linewidth=1.0,
            zorder=0,
        )
        if not cec_lines.empty:
            cec_lines.plot(
                ax=ax,
                color="#737373",
                linewidth=0.65,
                alpha=0.92,
                zorder=1,
            )
        edges_gdf.plot(
            ax=ax,
            color="#1f77b4",
            linewidth=0.58,
            alpha=0.50,
            zorder=2,
        )
        nodes_gdf.plot(
            ax=ax,
            marker="x",
            color="#e6550d",
            markersize=24,
            linewidth=0.9,
            zorder=3,
        )

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.tick_params(axis="both", labelsize=7.5, width=0.6, length=3)
        ax.set_aspect("equal", "box")
        ax.set_anchor("C")
        ax.set_xlim(xmin - 0.02 * dx, xmax + 0.02 * dx)
        ax.set_ylim(ymin - 0.02 * dy, ymax + 0.02 * dy)
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_color("#c8c8c8")
            spine.set_linewidth(0.6)

        legend_handles = [
            Line2D([0], [0], color="#737373", linewidth=0.8, label="CEC transmission lines"),
            Line2D([0], [0], color="#1f77b4", linewidth=0.8, alpha=0.65, label="Simplified topology"),
            Line2D(
                [0],
                [0],
                marker="x",
                linestyle="None",
                color="#e6550d",
                markersize=4.6,
                label="CEC substations",
            ),
        ]
        fig.subplots_adjust(left=0.13, right=0.985, top=0.975, bottom=0.30)
        ax.legend(
            handles=legend_handles,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.245),
            ncol=2,
            frameon=False,
            fontsize=6.7,
            handlelength=1.25,
            handletextpad=0.3,
            columnspacing=0.7,
            borderaxespad=0,
        )
        output_png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            output_png,
            dpi=EXPORT_DPI,
            facecolor="white",
            edgecolor="none",
            bbox_inches=None,
            pad_inches=0,
        )
        plt.close(fig)

    return output_png


def render_panel_c(temp_root: Path) -> Path:
    """Render the robustness comparison from the Stage 2 CSV outputs."""
    output_png = temp_root / "robustness_comparison.png"
    stage2 = PROJECT_ROOT / "Stage 2 Output_expanded"
    series = [
        (
            stage2 / "percolation_curve_impact.csv",
            "Impact lambda2-targeted",
            "#b22222",
            "o",
            "-",
        ),
        (
            stage2 / "percolation_curve_random.csv",
            "Random baseline",
            "#888888",
            "s",
            "--",
        ),
        (
            stage2 / "exploratory_percolation_curve_degree.csv",
            "Degree-targeted",
            "#2ca25f",
            "^",
            "-",
        ),
        (
            stage2 / "exploratory_percolation_curve_betweenness_centrality.csv",
            "Betweenness-targeted",
            "#d95f02",
            "D",
            "-",
        ),
        (
            stage2 / "exploratory_percolation_curve_closeness_centrality.csv",
            "Closeness-targeted",
            "#3182bd",
            "v",
            "-",
        ),
    ]
    style = {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 8.0,
        "axes.labelsize": 8.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.0,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
    with plt.rc_context(style):
        fig, ax = plt.subplots(
            figsize=(
                cm_to_inch(FIGURE_WIDTH_CM),
                cm_to_inch(ROBUSTNESS_PANEL_HEIGHT_CM),
            )
        )
        for path, label, color, marker, linestyle in series:
            data = pd.read_csv(path)
            ax.plot(
                pd.to_numeric(data["nodes_removed"], errors="coerce"),
                pd.to_numeric(data["lcc_fraction"], errors="coerce"),
                color=color,
                linestyle=linestyle,
                linewidth=1.0,
                marker=marker,
                markersize=3.2,
                markeredgewidth=0.35,
                markevery=1,
                label=label,
            )
        ax.set_xlim(-1, 92)
        ax.set_ylim(-0.02, 1.03)
        ax.set_xlabel("Number of substations removed")
        ax.set_ylabel("Largest connected component fraction")
        ax.grid(True, color="#d9d9d9", alpha=0.72, linewidth=0.45)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color("#bdbdbd")
            spine.set_linewidth(0.6)
        ax.tick_params(direction="out", color="#4d4d4d")
        handles, labels = ax.get_legend_handles_labels()
        fig.legend(
            handles,
            labels,
            loc="upper center",
            bbox_to_anchor=(0.53, 0.975),
            ncol=3,
            frameon=False,
            fontsize=7.0,
            handlelength=1.7,
            handletextpad=0.4,
            columnspacing=1.0,
            labelspacing=0.35,
        )
        fig.subplots_adjust(left=0.105, right=0.985, top=0.79, bottom=0.17)
        fig.savefig(
            output_png,
            dpi=EXPORT_DPI,
            facecolor="white",
            edgecolor="none",
            bbox_inches=None,
            pad_inches=0,
        )
        plt.close(fig)
    return output_png


def main() -> None:
    MANUSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="topology_composite_"))
    try:
        panel_paths = {
            "a": render_panel_a(temp_root),
            "b": render_panel_b(temp_root),
            "c": render_panel_c(temp_root),
        }
        panels = {key: load_panel(path) for key, path in panel_paths.items()}

        panel_sizes = {key: image_size_cm(image) for key, image in panels.items()}
        top_height_cm = max(panel_sizes["a"][1], panel_sizes["b"][1])
        bottom_height_cm = panel_sizes["c"][1]
        figure_height_cm = (
            bottom_height_cm
            + VERTICAL_GAP_CM
            + top_height_cm
            + TOP_LABEL_MARGIN_CM
        )

        rc_params = {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }

        with plt.rc_context(rc_params):
            fig = plt.figure(
                figsize=(
                    cm_to_inch(FIGURE_WIDTH_CM),
                    cm_to_inch(figure_height_cm),
                ),
                facecolor="white",
            )

            top_y_cm = bottom_height_cm + VERTICAL_GAP_CM
            axes_rect_cm = {
                "a": (0.0, top_y_cm, HALF_PANEL_WIDTH_CM, panel_sizes["a"][1]),
                "b": (
                    HALF_PANEL_WIDTH_CM + HORIZONTAL_GAP_CM,
                    top_y_cm,
                    HALF_PANEL_WIDTH_CM,
                    panel_sizes["b"][1],
                ),
                "c": (0.0, 0.0, FIGURE_WIDTH_CM, bottom_height_cm),
            }

            for key, (x_cm, y_cm, width_cm, height_cm) in axes_rect_cm.items():
                ax = fig.add_axes(
                    [
                        x_cm / FIGURE_WIDTH_CM,
                        y_cm / figure_height_cm,
                        width_cm / FIGURE_WIDTH_CM,
                        height_cm / figure_height_cm,
                    ]
                )
                ax.imshow(panels[key], interpolation="none")
                ax.set_axis_off()

            label_y_top = top_y_cm + top_height_cm + 0.02
            labels = {
                "a": (0.02, label_y_top),
                "b": (HALF_PANEL_WIDTH_CM + HORIZONTAL_GAP_CM + 0.02, label_y_top),
                "c": (0.02, bottom_height_cm + 0.04),
            }
            for key, (x_cm, y_cm) in labels.items():
                fig.text(
                    x_cm / FIGURE_WIDTH_CM,
                    y_cm / figure_height_cm,
                    key.upper(),
                    ha="left",
                    va="bottom",
                    fontsize=9.5,
                    fontweight="bold",
                    color="#111111",
                )

            png_path = OUTPUT_STEM.with_suffix(".png")
            pdf_path = OUTPUT_STEM.with_suffix(".pdf")
            fig.savefig(
                png_path,
                dpi=EXPORT_DPI,
                facecolor="white",
                edgecolor="none",
                bbox_inches=None,
                pad_inches=0,
            )
            fig.savefig(
                pdf_path,
                format="pdf",
                facecolor="white",
                edgecolor="none",
                bbox_inches=None,
                pad_inches=0,
            )
            plt.close(fig)

        print(f"Saved: {png_path}")
        print(f"Saved: {pdf_path}")
        print(
            "Final size: "
            f"{FIGURE_WIDTH_CM:.1f} x {figure_height_cm:.2f} cm at {EXPORT_DPI} dpi"
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
