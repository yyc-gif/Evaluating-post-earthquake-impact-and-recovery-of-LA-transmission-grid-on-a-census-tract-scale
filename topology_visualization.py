"""Visualization helpers for the topology preprocessing workflow."""

import json
import logging
import os

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import pandas as pd
import seaborn as sns
from shapely.geometry import LineString


def _node_xy(node):
    """Return the physical x/y coordinate for a graph node."""
    return (float(node[0]), float(node[1]))

# Publication-style panel settings copied from the Stage 2 reference panel.
# ---------------------------------------------------------------------------

CM_PER_INCH = 2.54
EXPORT_DPI = 300
EXPORT_PAD_INCHES = 0.04

FS_LABEL = 8.5
FS_TICK = 7.5
FS_LEGEND = 7.5

PANEL_MAP_TALL = {"width_cm": 8.9, "height_cm": 11.8}
VALIDATION_MAP_LAYOUT_CM = {"width_cm": 13.2, "height_cm": 8.9}

PUBLICATION_RCPARAMS = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "axes.labelsize": FS_LABEL,
    "xtick.labelsize": FS_TICK,
    "ytick.labelsize": FS_TICK,
    "legend.fontsize": FS_LEGEND,
    "legend.title_fontsize": FS_LEGEND,
    "figure.dpi": 150,
    "savefig.dpi": EXPORT_DPI,
    "axes.unicode_minus": False,
    "axes.linewidth": 0.6,
    "grid.linewidth": 0.4,
    "grid.color": "#d9d9d9",
    "lines.linewidth": 1.2,
    "patch.linewidth": 0.5,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 3.0,
    "ytick.major.size": 3.0,
    "axes.titlepad": 4.0,
}

# The legend text in this panel is materially longer than the Stage 2 labels,
# so it needs a modest compaction to fit as a single row inside the same-width
# manuscript panel.
COMPANION_LEGEND_FONT = 6.9
COMPANION_LEGEND_HANDLELENGTH = 1.0
COMPANION_LEGEND_HANDLETEXTPAD = 0.20
COMPANION_LEGEND_COLUMNSPACING = 0.32


def cm_to_inch(*values):
    """Convert centimeters to inches for matplotlib figsize use."""
    if len(values) == 1 and isinstance(values[0], (tuple, list)):
        values = tuple(values[0])
    converted = tuple(v / CM_PER_INCH for v in values)
    return converted[0] if len(converted) == 1 else converted


def style_axis_publication(ax, xlabel: str | None = None, ylabel: str | None = None):
    """Apply the Stage 2 manuscript axis typography."""
    if xlabel is not None:
        ax.set_xlabel(xlabel, fontsize=FS_LABEL)
    if ylabel is not None:
        ax.set_ylabel(ylabel, fontsize=FS_LABEL)
    ax.tick_params(axis="both", which="major", labelsize=FS_TICK, width=0.6, length=3)
    return ax


def format_publication_legend(legend, fontsize: float) -> None:
    """Format legend text to the requested manuscript size."""
    if legend is None:
        return
    frame = legend.get_frame()
    if frame is not None:
        frame.set_facecolor("white")
        frame.set_edgecolor("#c8c8c8")
        frame.set_linewidth(0.6)
        frame.set_alpha(0.95)
    for text in legend.get_texts():
        text.set_fontsize(fontsize)


# ---------------------------------------------------------------------------

def _get_visual_bounds_wgs(subs_proj, tracts_proj):
    """Return WGS84 plotting layers and validation-map bounds."""
    subs_wgs = subs_proj.to_crs(epsg=4326)

    city_wgs = None
    if tracts_proj is not None and not tracts_proj.empty:
        city_wgs = tracts_proj.to_crs(epsg=4326).dissolve().reset_index(drop=True)
        xmin, ymin, xmax, ymax = city_wgs.total_bounds
    else:
        xmin, ymin, xmax, ymax = [-118.67, 33.70, -118.15, 34.34]

    return subs_wgs, city_wgs, xmin, ymin, xmax, ymax


def _projection_connector_mask(gdf: gpd.GeoDataFrame) -> pd.Series:
    """Return True for synthetic substation-to-projection connector rows."""
    if "_is_projection_connector" not in gdf.columns:
        return pd.Series(False, index=gdf.index)

    values = gdf["_is_projection_connector"]
    if pd.api.types.is_bool_dtype(values):
        return values.fillna(False)

    return values.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def _prepare_background_lines_wgs(lines_clipped):
    """Prepare deduplicated real-network segments in WGS84 for validation plotting."""
    background_lines = lines_clipped.explode(index_parts=False).reset_index(drop=True).copy()
    background_lines = background_lines[
        background_lines.geometry.notna() & ~background_lines.geometry.is_empty
    ].copy()
    background_lines = background_lines[~_projection_connector_mask(background_lines)].copy()
    background_lines["_geom_wkb"] = background_lines.geometry.apply(
        lambda geom: geom.normalize().wkb
    )
    background_lines = background_lines.drop_duplicates(subset=["_geom_wkb"]).drop(
        columns="_geom_wkb"
    )
    return background_lines.to_crs(epsg=4326)


def _collect_direct_link_segments(direct_links):
    """
    Reconstruct direct-link path segments from path_nodes and drop repeated segments.

    Returns:
        (segments, duplicate_count)
    """
    direct_link_segments = []
    seen_direct_segments = set()
    duplicate_direct_segments = 0

    for link in direct_links:
        path_nodes = link["path_nodes"]
        for start, end in zip(path_nodes, path_nodes[1:]):
            start_xy = _node_xy(start)
            end_xy = _node_xy(end)
            start_key = (round(float(start_xy[0]), 6), round(float(start_xy[1]), 6))
            end_key = (round(float(end_xy[0]), 6), round(float(end_xy[1]), 6))
            if start_key == end_key:
                continue

            segment_key = tuple(sorted((start_key, end_key)))
            if segment_key in seen_direct_segments:
                duplicate_direct_segments += 1
                continue

            seen_direct_segments.add(segment_key)
            direct_link_segments.append(LineString([start_xy, end_xy]))

    return direct_link_segments, duplicate_direct_segments


def _build_direct_link_paths_wgs(direct_links):
    """
    Build per-link WGS84 path geometries from the actual path_nodes sequence.

    Each direct link is represented by its full along-network path, not a
    straight-line chord between source and target substations.
    """
    rows = []
    for link in direct_links:
        raw_nodes = link.get("path_nodes", [])
        clean_nodes = []
        for node in raw_nodes:
            node_xy = _node_xy(node)
            if not clean_nodes or node_xy != clean_nodes[-1]:
                clean_nodes.append(node_xy)

        if len(clean_nodes) < 2:
            continue

        rows.append(
            {
                "src": str(link["src"]),
                "tgt": str(link["tgt"]),
                "length_km": float(link["length_km"]),
                "length_km_label": f"{float(link['length_km']):.2f}",
                "path_nodes_count": len(clean_nodes),
                "path_segments_count": len(clean_nodes) - 1,
                "geometry": LineString(clean_nodes),
            }
        )

    if not rows:
        return gpd.GeoDataFrame(
            {
                "src": pd.Series(dtype=str),
                "tgt": pd.Series(dtype=str),
                "length_km": pd.Series(dtype=float),
                "length_km_label": pd.Series(dtype=str),
                "path_nodes_count": pd.Series(dtype=int),
                "path_segments_count": pd.Series(dtype=int),
            },
            geometry=gpd.GeoSeries([], crs="EPSG:4326"),
            crs="EPSG:4326",
        )

    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:3310").to_crs(epsg=4326)


def _classify_substation_ids(G, sub_id_to_node):
    """Split substations into largest-component versus disconnected/island sets."""
    if len(G) <= 0:
        return [], []

    comps = list(nx.connected_components(G))
    if not comps:
        return [], []

    main_comp = max(comps, key=len)
    main_ids = [
        sid for sid, node in sub_id_to_node.items()
        if node in main_comp
    ]
    island_ids = [
        sid for sid, node in sub_id_to_node.items()
        if node not in main_comp
    ]
    return main_ids, island_ids


def _write_canvas_validation_map_html(
    background_lines_wgs,
    direct_link_paths_wgs,
    subs_wgs,
    main_ids,
    island_ids,
    xmin,
    ymin,
    xmax,
    ymax,
    output_path,
):
    """Write a self-contained interactive canvas-based validation map HTML."""
    dx = max(float(xmax - xmin), 1e-6)
    dy = max(float(ymax - ymin), 1e-6)
    pad_x = 0.02 * dx
    pad_y = 0.02 * dy
    xmin_p, xmax_p = float(xmin - pad_x), float(xmax + pad_x)
    ymin_p, ymax_p = float(ymin - pad_y), float(ymax + pad_y)
    dx_p = max(xmax_p - xmin_p, 1e-6)
    dy_p = max(ymax_p - ymin_p, 1e-6)

    svg_width = 1200.0
    svg_height = max(820.0, svg_width * (dy_p / dx_p))

    def project_xy(lon, lat):
        """Project lon/lat coordinates into the fixed validation-canvas frame."""
        x = ((float(lon) - xmin_p) / dx_p) * svg_width
        y = svg_height - (((float(lat) - ymin_p) / dy_p) * svg_height)
        return x, y

    def iter_line_parts(geometry):
        """Yield drawable line parts from a line or multiline geometry."""
        if geometry is None or geometry.is_empty:
            return []
        if geometry.geom_type == "LineString":
            return [geometry]
        if geometry.geom_type == "MultiLineString":
            return list(geometry.geoms)
        return []

    real_lines = []
    for geom in background_lines_wgs.geometry:
        for part in iter_line_parts(geom):
            coords = list(part.coords)
            if len(coords) < 2:
                continue
            projected = [[round(x, 2), round(y, 2)] for x, y in (project_xy(lon, lat) for lon, lat in coords)]
            real_lines.append(projected)

    direct_links_data = []
    for _, row in direct_link_paths_wgs.iterrows():
        for part in iter_line_parts(row.geometry):
            coords = list(part.coords)
            if len(coords) < 2:
                continue
            projected = [[round(x, 2), round(y, 2)] for x, y in (project_xy(lon, lat) for lon, lat in coords)]
            xs = [pt[0] for pt in projected]
            ys = [pt[1] for pt in projected]
            direct_links_data.append(
                {
                    "src": str(row["src"]),
                    "tgt": str(row["tgt"]),
                    "length_km": str(row["length_km_label"]),
                    "path_segments_count": int(row["path_segments_count"]),
                    "path_nodes_count": int(row["path_nodes_count"]),
                    "coords": projected,
                    "bbox": [
                        round(min(xs), 2),
                        round(min(ys), 2),
                        round(max(xs), 2),
                        round(max(ys), 2),
                    ],
                }
            )

    main_nodes = []
    main_df = subs_wgs[subs_wgs["id"].astype(str).isin(main_ids)]
    for _, row in main_df.iterrows():
        sid = str(row["id"])
        x, y = project_xy(row.geometry.x, row.geometry.y)
        main_nodes.append({"id": sid, "x": round(x, 2), "y": round(y, 2)})

    island_nodes = []
    island_df = subs_wgs[subs_wgs["id"].astype(str).isin(island_ids)]
    for _, row in island_df.iterrows():
        sid = str(row["id"])
        x, y = project_xy(row.geometry.x, row.geometry.y)
        island_nodes.append({"id": sid, "x": round(x, 2), "y": round(y, 2)})

    map_payload = {
        "width": round(svg_width, 2),
        "height": round(svg_height, 2),
        "real_lines": real_lines,
        "direct_links": direct_links_data,
        "main_nodes": main_nodes,
        "island_nodes": island_nodes,
    }

    html_text = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Topology Interactive Validation</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --panel: rgba(255, 255, 255, 0.96);
      --line-real: #7a7a7a;
      --line-direct: #1f77b4;
      --node-main: #e6550d;
      --node-island: #b2182b;
      --text: #17212b;
      --muted: #5c6773;
      --border: #d7dde4;
      --shadow: 0 14px 34px rgba(23, 33, 43, 0.12);
    }}
    html, body {{
      margin: 0;
      height: 100%;
      background: linear-gradient(180deg, #eef3f8 0%, #f8fafc 100%);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 320px 1fr;
      height: 100vh;
    }}
    .sidebar {{
      padding: 18px 18px 14px;
      background: var(--panel);
      border-right: 1px solid var(--border);
      box-shadow: var(--shadow);
      overflow-y: auto;
      z-index: 2;
    }}
    .sidebar h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      line-height: 1.2;
    }}
    .sidebar p {{
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    .controls {{
      display: grid;
      gap: 10px;
      margin-bottom: 16px;
    }}
    .layer-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
    }}
    .swatch {{
      width: 14px;
      height: 14px;
      border-radius: 999px;
      flex: 0 0 auto;
      border: 1px solid rgba(0, 0, 0, 0.08);
    }}
    .swatch.real {{
      background: var(--line-real);
      opacity: 0.5;
    }}
    .swatch.direct {{
      background: var(--line-direct);
    }}
    .swatch.main {{
      background: var(--node-main);
    }}
    .swatch.island {{
      background: var(--node-island);
    }}
    .button-row {{
      display: flex;
      gap: 8px;
      margin: 14px 0 18px;
    }}
    button {{
      border: 1px solid var(--border);
      background: white;
      color: var(--text);
      padding: 8px 12px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 13px;
    }}
    button:hover {{
      background: #f3f6f9;
    }}
    .stats {{
      font-size: 12px;
      color: var(--muted);
      display: grid;
      gap: 6px;
    }}
    .map-wrap {{
      position: relative;
      overflow: hidden;
      padding: 12px;
    }}
    .map-panel {{
      position: relative;
      height: calc(100vh - 24px);
      background: white;
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    canvas {{
      width: 100%;
      height: 100%;
      background:
        radial-gradient(circle at top left, rgba(214, 226, 240, 0.35), transparent 24%),
        linear-gradient(180deg, #fbfdff 0%, #f5f8fb 100%);
      cursor: grab;
      touch-action: none;
      user-select: none;
    }}
    canvas.dragging {{
      cursor: grabbing;
    }}
    .tooltip {{
      position: absolute;
      display: none;
      max-width: 280px;
      padding: 10px 12px;
      border-radius: 10px;
      background: rgba(20, 29, 37, 0.94);
      color: white;
      font-size: 12px;
      line-height: 1.45;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.28);
      pointer-events: none;
      z-index: 3;
      white-space: pre-line;
    }}
    @media (max-width: 900px) {{
      .layout {{
        grid-template-columns: 1fr;
        grid-template-rows: auto 1fr;
      }}
      .sidebar {{
        border-right: none;
        border-bottom: 1px solid var(--border);
      }}
      .map-panel {{
        height: calc(100vh - 320px);
      }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <h1>Topology Validation Map</h1>
      <p>
        Interactive validation view for the clipped CEC transmission network,
        extracted direct substation links, and substation nodes. Use the
        checkboxes to toggle layers, drag to pan, and use the mouse wheel to zoom.
      </p>
      <div class="controls">
        <label class="layer-row">
          <input type="checkbox" class="layer-toggle" data-target="layer-real" checked>
          <span class="swatch real"></span>
          <span>Real transmission lines</span>
        </label>
        <label class="layer-row">
          <input type="checkbox" class="layer-toggle" data-target="layer-direct" checked>
          <span class="swatch direct"></span>
          <span>Direct substation links</span>
        </label>
        <label class="layer-row">
          <input type="checkbox" class="layer-toggle" data-target="layer-main" checked>
          <span class="swatch main"></span>
          <span>Main Grid substations</span>
        </label>
        <label class="layer-row">
          <input type="checkbox" class="layer-toggle" data-target="layer-island" checked>
          <span class="swatch island"></span>
          <span>Disconnected substations</span>
        </label>
      </div>
      <div class="button-row">
        <button type="button" id="zoom-in">+</button>
        <button type="button" id="zoom-out">-</button>
        <button type="button" id="reset-view">Reset view</button>
      </div>
      <div class="stats">
        <div>Background segments: {len(real_lines)}</div>
        <div>Direct link paths: {len(direct_link_paths_wgs)}</div>
        <div>Main Grid substations: {len(main_ids)}</div>
        <div>Disconnected substations: {len(island_ids)}</div>
      </div>
    </aside>
    <main class="map-wrap">
      <div class="map-panel">
        <canvas id="topology-map"></canvas>
        <div id="tooltip" class="tooltip"></div>
      </div>
    </main>
  </div>
  <script>
    const payload = {json.dumps(map_payload, separators=(",", ":"))};
    const canvas = document.getElementById("topology-map");
    const ctx = canvas.getContext("2d");
    const tooltip = document.getElementById("tooltip");
    const layerState = {{
      real: true,
      direct: true,
      main: true,
      island: true,
    }};
    const originalView = {{
      x: 0,
      y: 0,
      scale: 1,
    }};
    let view = {{ ...originalView }};
    let dragState = null;
    let redrawPending = false;

    function resizeCanvas() {{
      const ratio = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(1, Math.round(rect.width * ratio));
      canvas.height = Math.max(1, Math.round(rect.height * ratio));
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      scheduleDraw();
    }}

    function worldToScreen(pt) {{
      return {{
        x: (pt[0] + view.x) * view.scale,
        y: (pt[1] + view.y) * view.scale
      }};
    }}

    function screenToWorld(clientX, clientY) {{
      const rect = canvas.getBoundingClientRect();
      const x = (clientX - rect.left) / view.scale - view.x;
      const y = (clientY - rect.top) / view.scale - view.y;
      return {{
        x,
        y
      }};
    }}

    function scheduleDraw() {{
      if (redrawPending) {{
        return;
      }}
      redrawPending = true;
      requestAnimationFrame(() => {{
        redrawPending = false;
        draw();
      }});
    }}

    function drawPolyline(coords, strokeStyle, lineWidth, dashArray, alpha) {{
      if (!coords || coords.length < 2) {{
        return;
      }}
      ctx.save();
      ctx.strokeStyle = strokeStyle;
      ctx.lineWidth = lineWidth;
      ctx.globalAlpha = alpha;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.setLineDash(dashArray);
      ctx.beginPath();
      const start = worldToScreen(coords[0]);
      ctx.moveTo(start.x, start.y);
      for (let i = 1; i < coords.length; i += 1) {{
        const p = worldToScreen(coords[i]);
        ctx.lineTo(p.x, p.y);
      }}
      ctx.stroke();
      ctx.restore();
    }}

    function drawNode(node, fillStyle, radius) {{
      const p = worldToScreen([node.x, node.y]);
      ctx.save();
      ctx.beginPath();
      ctx.fillStyle = fillStyle;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.5;
      ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }}

    function draw() {{
      const rect = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);

      if (layerState.real) {{
        for (const line of payload.real_lines) {{
          drawPolyline(line, "#7a7a7a", 1.0, [5, 5], 0.35);
        }}
      }}
      if (layerState.direct) {{
        for (const link of payload.direct_links) {{
          drawPolyline(link.coords, "#1f77b4", 2.8, [], 0.92);
        }}
      }}
      if (layerState.main) {{
        for (const node of payload.main_nodes) {{
          drawNode(node, "#e6550d", 5);
        }}
      }}
      if (layerState.island) {{
        for (const node of payload.island_nodes) {{
          drawNode(node, "#b2182b", 6.5);
        }}
      }}
    }}

    function pointSegmentDistance(px, py, ax, ay, bx, by) {{
      const dx = bx - ax;
      const dy = by - ay;
      if (dx === 0 && dy === 0) {{
        return Math.hypot(px - ax, py - ay);
      }}
      const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)));
      const cx = ax + t * dx;
      const cy = ay + t * dy;
      return Math.hypot(px - cx, py - cy);
    }}

    function findHoverTarget(evt) {{
      const world = screenToWorld(evt.clientX, evt.clientY);
      const worldThreshold = 10 / Math.max(view.scale, 0.001);

      if (layerState.main) {{
        for (const node of payload.main_nodes) {{
          if (Math.hypot(world.x - node.x, world.y - node.y) <= worldThreshold) {{
            return `Substation id: ${{node.id}}`;
          }}
        }}
      }}

      if (layerState.island) {{
        for (const node of payload.island_nodes) {{
          if (Math.hypot(world.x - node.x, world.y - node.y) <= worldThreshold) {{
            return `Substation id: ${{node.id}}`;
          }}
        }}
      }}

      if (layerState.direct) {{
        for (const link of payload.direct_links) {{
          const bbox = link.bbox;
          if (
            world.x < bbox[0] - worldThreshold || world.x > bbox[2] + worldThreshold ||
            world.y < bbox[1] - worldThreshold || world.y > bbox[3] + worldThreshold
          ) {{
            continue;
          }}
          for (let i = 1; i < link.coords.length; i += 1) {{
            const a = link.coords[i - 1];
            const b = link.coords[i];
            if (pointSegmentDistance(world.x, world.y, a[0], a[1], b[0], b[1]) <= worldThreshold) {{
              return [
                `Source substation: ${{link.src}}`,
                `Target substation: ${{link.tgt}}`,
                `Length (km): ${{link.length_km}}`,
                `Path segments: ${{link.path_segments_count}}`,
                `Path nodes: ${{link.path_nodes_count}}`
              ].join("\\n");
            }}
          }}
        }}
      }}

      return "";
    }}

    function updateTooltip(evt, text) {{
      if (!text) {{
        tooltip.style.display = "none";
        return;
      }}
      tooltip.style.display = "block";
      tooltip.textContent = text;
      tooltip.style.left = `${{evt.clientX + 16}}px`;
      tooltip.style.top = `${{evt.clientY + 16}}px`;
    }}

    document.querySelectorAll(".layer-toggle").forEach((checkbox) => {{
      checkbox.addEventListener("change", () => {{
        if (checkbox.dataset.target === "layer-real") layerState.real = checkbox.checked;
        if (checkbox.dataset.target === "layer-direct") layerState.direct = checkbox.checked;
        if (checkbox.dataset.target === "layer-main") layerState.main = checkbox.checked;
        if (checkbox.dataset.target === "layer-island") layerState.island = checkbox.checked;
        scheduleDraw();
      }});
    }});

    function zoomAtCanvasPoint(scaleFactor, sx, sy) {{
      const wx = sx / view.scale - view.x;
      const wy = sy / view.scale - view.y;
      const nextScale = Math.max(0.25, Math.min(18, view.scale * scaleFactor));
      view.x = sx / nextScale - wx;
      view.y = sy / nextScale - wy;
      view.scale = nextScale;
      scheduleDraw();
    }}

    function zoomFromButton(scaleFactor) {{
      const rect = canvas.getBoundingClientRect();
      zoomAtCanvasPoint(scaleFactor, rect.width / 2, rect.height / 2);
    }}

    document.getElementById("reset-view").addEventListener("click", () => {{
      view = {{ ...originalView }};
      scheduleDraw();
    }});

    document.getElementById("zoom-in").addEventListener("click", () => {{
      zoomFromButton(1.18);
    }});

    document.getElementById("zoom-out").addEventListener("click", () => {{
      zoomFromButton(0.85);
    }});

    canvas.addEventListener("wheel", (evt) => {{
      evt.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const sx = evt.clientX - rect.left;
      const sy = evt.clientY - rect.top;
      const scaleFactor = evt.deltaY < 0 ? 1.12 : 0.89;
      zoomAtCanvasPoint(scaleFactor, sx, sy);
      updateTooltip(evt, findHoverTarget(evt));
    }}, {{ passive: false }});

    canvas.addEventListener("pointerdown", (evt) => {{
      dragState = {{
        startClientX: evt.clientX,
        startClientY: evt.clientY,
        startX: view.x,
        startY: view.y
      }};
      canvas.classList.add("dragging");
      canvas.setPointerCapture(evt.pointerId);
    }});

    canvas.addEventListener("pointermove", (evt) => {{
      if (dragState) {{
        const dx = (evt.clientX - dragState.startClientX) / view.scale;
        const dy = (evt.clientY - dragState.startClientY) / view.scale;
        view.x = dragState.startX + dx;
        view.y = dragState.startY + dy;
        scheduleDraw();
      }}
      updateTooltip(evt, findHoverTarget(evt));
    }});

    function endDrag(evt) {{
      dragState = null;
      canvas.classList.remove("dragging");
      try {{
        canvas.releasePointerCapture(evt.pointerId);
      }} catch (err) {{
      }}
    }}

    canvas.addEventListener("pointerup", endDrag);
    canvas.addEventListener("pointerleave", (evt) => {{
      tooltip.style.display = "none";
      endDrag(evt);
    }});
    canvas.addEventListener("pointercancel", endDrag);
    window.addEventListener("resize", resizeCanvas);

    resizeCanvas();
  </script>
</body>
</html>
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_text)


def visualize_topology(
    G,
    lines_clipped,
    subs_proj,
    tracts_proj,
    sub_id_to_node,
    direct_links,
    output_path,
):
    """
    Final visualization:
      1) clipped physical transmission lines
      2) direct substation links
      3) substations classified by membership in the largest connected component

    Plotting presentation is aligned to the accepted publication layout:
      - compact landscape lon/lat canvas
      - city-bounds framing with 2% padding
      - visible axis typography
      - legend pulled close to the map body
    """
    logger = logging.getLogger()
    logger.info("Generating final visualization (physical lines + direct links)...")

    # ---------------------------------------------------------------------
    # 1) Convert plotting layers to WGS84 and derive city-style bounds
    # ---------------------------------------------------------------------
    subs_wgs, city_wgs, xmin, ymin, xmax, ymax = _get_visual_bounds_wgs(
        subs_proj,
        tracts_proj,
    )

    dx, dy = xmax - xmin, ymax - ymin

    publication_style = dict(sns.axes_style("whitegrid"))
    publication_style.update(PUBLICATION_RCPARAMS)

    with plt.rc_context(publication_style):
        fig, ax = plt.subplots(
            figsize=cm_to_inch(
                VALIDATION_MAP_LAYOUT_CM["width_cm"],
                VALIDATION_MAP_LAYOUT_CM["height_cm"],
            )
        )
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # -----------------------------------------------------------------
        # 2) Physical transmission lines
        # -----------------------------------------------------------------
        background_lines = lines_clipped.explode(index_parts=False).reset_index(drop=True).copy()
        background_lines = background_lines[
            background_lines.geometry.notna() & ~background_lines.geometry.is_empty
        ].copy()
        background_lines = background_lines[~_projection_connector_mask(background_lines)].copy()
        background_lines["_geom_wkb"] = background_lines.geometry.apply(
            lambda geom: geom.normalize().wkb
        )
        duplicate_bg_segments = int(background_lines.duplicated(subset=["_geom_wkb"]).sum())
        if duplicate_bg_segments:
            logger.info(
                "Dropping %d duplicate background transmission segments for plotting.",
                duplicate_bg_segments,
            )
        background_lines = background_lines.drop_duplicates(subset=["_geom_wkb"]).drop(
            columns="_geom_wkb"
        )

        background_lines = background_lines.to_crs(epsg=4326)

        if city_wgs is not None and not city_wgs.empty:
            city_wgs.plot(
                ax=ax,
                facecolor="none",
                edgecolor="#bdbdbd",
                linewidth=1.2,
                zorder=0,
            )

        background_lines.plot(
            ax=ax,
            color="#7a7a7a",
            linewidth=0.78,
            linestyle="--",
            alpha=0.38,
            zorder=1,
        )

        # -----------------------------------------------------------------
        # 3) Direct substation links
        # -----------------------------------------------------------------
        if direct_links:
            direct_link_segments, duplicate_direct_segments = _collect_direct_link_segments(
                direct_links
            )

            if duplicate_direct_segments:
                logger.info(
                    "Dropping %d duplicate direct-link segments for plotting.",
                    duplicate_direct_segments,
                )

            if direct_link_segments:
                gpd.GeoSeries(direct_link_segments, crs="EPSG:3310").to_crs(
                    epsg=4326
                ).plot(
                    ax=ax,
                    color="#1f77b4",
                    linewidth=1.35,
                    linestyle="-",
                    alpha=0.9,
                    zorder=2,
                    label="Direct substation links",
                )

        # -----------------------------------------------------------------
        # 4) Substation connectivity status (largest connected component)
        # -----------------------------------------------------------------
        main_ids, island_ids = _classify_substation_ids(G, sub_id_to_node)

        if main_ids:
            subs_wgs[subs_wgs["id"].isin(main_ids)].plot(
                ax=ax,
                color="#e6550d",
                markersize=18,
                edgecolor="white",
                linewidth=0.8,
                zorder=3,
                label=f"Main Grid ({len(main_ids)} substations)",
            )

        if island_ids:
            subs_wgs[subs_wgs["id"].isin(island_ids)].plot(
                ax=ax,
                color="#b2182b",
                markersize=30,
                marker="X",
                edgecolor="white",
                linewidth=0.8,
                zorder=4,
                label=f"Disconnected ({len(island_ids)})",
            )

        # -----------------------------------------------------------------
        # 5) Final plot settings + save
        # -----------------------------------------------------------------
        style_axis_publication(ax, xlabel="Longitude", ylabel="Latitude")
        ax.set_aspect("equal", "box")
        ax.set_anchor("C")
        ax.set_xlim(xmin - 0.02 * dx, xmax + 0.02 * dx)
        ax.set_ylim(ymin - 0.02 * dy, ymax + 0.02 * dy)
        ax.grid(False)

        legend_handles = [
            Line2D(
                [0], [0],
                color="#7a7a7a",
                linewidth=0.78,
                linestyle="--",
                alpha=0.38,
                label="CEC transmission lines",
            ),
            Line2D(
                [0], [0],
                color="#1f77b4",
                linewidth=1.35,
                linestyle="-",
                alpha=0.9,
                label="Direct substation links",
            ),
        ]

        if main_ids:
            legend_handles.append(
                Line2D(
                    [0], [0],
                    marker="o",
                    linestyle="None",
                    markerfacecolor="#e6550d",
                    markeredgecolor="white",
                    markersize=5.0,
                    label=f"Main Grid ({len(main_ids)} substations)",
                )
            )

        fig.subplots_adjust(left=0.09, right=0.985, top=0.985, bottom=0.19)
        if legend_handles:
            legend = ax.legend(
                handles=legend_handles,
                loc="upper center",
                bbox_to_anchor=(0.5, -0.135),
                ncol=3,
                frameon=False,
                fontsize=COMPANION_LEGEND_FONT,
                borderpad=0.12,
                labelspacing=0.18,
                handletextpad=COMPANION_LEGEND_HANDLETEXTPAD,
                borderaxespad=0.0,
                columnspacing=0.45,
                handlelength=COMPANION_LEGEND_HANDLELENGTH,
            )
            format_publication_legend(legend, fontsize=COMPANION_LEGEND_FONT)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(
            output_path,
            dpi=EXPORT_DPI,
            format="png",
            bbox_inches="tight",
            pad_inches=EXPORT_PAD_INCHES,
            facecolor="white",
            edgecolor="none",
        )
        plt.close(fig)
    logger.info(f"Validation plot saved to: {output_path}")


def visualize_topology_interactive(
    G,
    lines_clipped,
    subs_proj,
    tracts_proj,
    sub_id_to_node,
    direct_links,
    output_path,
):
    """
    Export an interactive HTML validation map for the real network, direct links,
    and substation nodes. The map is written as a local HTML file and does not
    require a web server.
    """
    logger = logging.getLogger()
    logger.info("Generating interactive topology validation map...")

    subs_wgs, _, xmin, ymin, xmax, ymax = _get_visual_bounds_wgs(subs_proj, tracts_proj)
    background_lines_wgs = _prepare_background_lines_wgs(lines_clipped)
    direct_link_paths_wgs = _build_direct_link_paths_wgs(direct_links)
    main_ids, island_ids = _classify_substation_ids(G, sub_id_to_node)
    classified_ids = set(main_ids) | set(island_ids)
    unsnapped_ids = [
        sid for sid in subs_wgs["id"].astype(str).tolist()
        if sid not in classified_ids
    ]
    if unsnapped_ids:
        island_ids = list(dict.fromkeys(list(island_ids) + unsnapped_ids))

    # Use the lightweight canvas renderer by default. In practice this is much
    # more responsive than folium/Leaflet or plotly for large LA network layers,
    # especially during repeated zoom operations.
    _write_canvas_validation_map_html(
        background_lines_wgs=background_lines_wgs,
        direct_link_paths_wgs=direct_link_paths_wgs,
        subs_wgs=subs_wgs,
        main_ids=main_ids,
        island_ids=island_ids,
        xmin=xmin,
        ymin=ymin,
        xmax=xmax,
        ymax=ymax,
        output_path=output_path,
    )
    logger.info(
        "Interactive validation map saved to: %s (backend=embedded-canvas)",
        output_path,
    )


# ---------------------------------------------------------------------------

