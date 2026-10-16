"""Vector-only Figure 7 map variants from the pinned P2/K3 inputs."""
from __future__ import annotations

import io
import json
from pathlib import Path

import fitz
import numpy as np
import pandas as pd


PAGE_W = 518.4000244140625
PAGE_A_H = 648.0
PAGE_B_H = 720.0
TITLE_C = "C.\u00a0Community\u00a0types"
TITLE_D = "D.\u00a0Recovery\u00a0burden\u00a0and\u00a0social\u00a0vulnerability"
P75 = 38.38135467381475
COLORS = {1: "#147f98", 2: "#d07734", 3: "#7a5899"}
NA_STROKE = (0.20, 0.20, 0.20)
SCREEN_STROKE = (0.0666819289, 0.0666819289, 0.0666819289)
BLUE_AMBER = "blue_amber"
SEAM_OVERLAP_PT = 0.12


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _lab_to_linear(lab):
    white = np.array([0.9504559271, 1.0, 1.0890577508])
    primaries = np.array([[0.64 / 0.33, 0.30 / 0.60, 0.15 / 0.06],
                          [1.0, 1.0, 1.0],
                          [(1 - 0.64 - 0.33) / 0.33,
                           (1 - 0.30 - 0.60) / 0.60,
                           (1 - 0.15 - 0.06) / 0.06]])
    rgb_to_xyz = primaries @ np.diag(np.linalg.solve(primaries, white))
    xyz_to_rgb = np.linalg.inv(rgb_to_xyz)
    L, a, b = np.moveaxis(np.asarray(lab), -1, 0)
    fy = (L + 16) / 116
    f = np.stack([fy + a / 500, fy, fy - b / 200], axis=-1)
    xyz = np.where(f > 6 / 29, f ** 3,
                   3 * (6 / 29) ** 2 * (f - 4 / 29)) * white
    return xyz @ xyz_to_rgb.T


def _linear_to_srgb(rgb):
    return np.where(rgb <= 0.0031308, 12.92 * rgb,
                    1.055 * np.maximum(rgb, 0) ** (1 / 2.4) - 0.055)


def continuous_rgb(burden_u, sovi_v, specification):
    design = specification["designs"][BLUE_AMBER]
    low = np.asarray(design["ab_at_SOVI_0"], dtype=float)
    high = np.asarray(design["ab_at_SOVI_100"], dtype=float)
    scale = np.asarray(design["common_chroma_factors_at_257_burden_knots"], dtype=float)
    burden_u, sovi_v = np.broadcast_arrays(np.asarray(burden_u), np.asarray(sovi_v))
    factor = np.interp(burden_u, np.linspace(0, 1, len(scale)), scale)
    ab = (low + (high - low) * sovi_v[..., None]) * factor[..., None]
    lab = np.concatenate([(91 - 49 * burden_u)[..., None], ab], axis=-1)
    rgb = _linear_to_srgb(_lab_to_linear(lab))
    if rgb.min() < -1e-10 or rgb.max() > 1 + 1e-10:
        raise ValueError("Pinned CIELAB mapping exceeded the sRGB gamut")
    return rgb


def _point(point, transform):
    x, y = point
    sx, sy, tx, ty = transform
    return sx * x + tx, sy * y + ty


def _path_stream(drawing, fill=None, stroke=None, width=None, transform=(1, 1, 0, 0)):
    commands = []
    last = None
    for item in drawing["items"]:
        op = item[0]
        if op == "l":
            a, b = (_point(p, transform) for p in item[1:])
            if last is None or tuple(a) != tuple(last):
                commands.append(f"{a[0]:.8f} {a[1]:.8f} m")
            commands.append(f"{b[0]:.8f} {b[1]:.8f} l")
            last = b
        elif op == "c":
            a, b, c, end = (_point(p, transform) for p in item[1:])
            if last is None or tuple(a) != tuple(last):
                commands.append(f"{a[0]:.8f} {a[1]:.8f} m")
            commands.append(" ".join(f"{v:.8f}" for p in (b, c, end) for v in p) + " c")
            last = end
        elif op == "re":
            rect = item[1]
            points = [(rect[0], rect[1]), (rect[2], rect[1]),
                      (rect[2], rect[3]), (rect[0], rect[3])]
            if len(item) > 2 and item[2] < 0:
                points.reverse()
            pts = [_point(p, transform) for p in points]
            commands.append(f"{pts[0][0]:.8f} {pts[0][1]:.8f} m")
            commands.extend(f"{x:.8f} {y:.8f} l" for x, y in pts[1:])
            commands.append("h")
            last = None
        else:
            raise ValueError(f"Unsupported vector path operator: {op}")
    if drawing.get("closePath"):
        commands.append("h")
    setup = [f"{(drawing.get('width', 0) if width is None else width):.8f} w",
             f"{int(drawing.get('lineJoin', 0))} j",
             f"{int(drawing.get('lineCap', [0])[0])} J",
             drawing.get("dashes", "[] 0") + " d"]
    if stroke is not None:
        setup.append(" ".join(f"{x:.10f}" for x in stroke) + " RG")
    if fill is not None:
        setup.append(" ".join(f"{x:.10f}" for x in fill) + " rg")
    operator = ("B" if stroke is not None else "f") if fill is not None else "S"
    if drawing.get("even_odd") and fill is not None:
        operator += "*"
    return "q\n" + "\n".join(setup + commands + [operator, "Q"]) + "\n"


def _append(page, raw):
    doc = page.parent
    xref = doc.get_new_xref()
    doc.update_object(xref, "<< >>")
    doc.update_stream(xref, raw.encode("ascii"))
    old = page.get_contents()
    doc.xref_set_key(page.xref, "Contents",
                     "[" + " ".join(f"{xref0} 0 R" for xref0 in [*old, xref]) + "]")


def _clip_transform(clip, center_x, scale, top_y):
    x0, y0, x1, y1 = clip
    tx = center_x * (1 - scale)
    ty = top_y - scale * y0
    return [scale * x0 + tx, top_y, scale * x1 + tx,
            top_y + scale * (y1 - y0)], (scale, scale, tx, ty)


def _variant_paths(paths, panel, scale=1.0, top_y=None, center_x=None):
    dclip = paths["map_clip"]
    if panel == "D":
        base_clip = list(dclip)
        base_transform = (1.0, 1.0, 0.0, 0.0)
    else:
        base_clip = [dclip[0] - 254.016, dclip[1] - 15.0,
                     dclip[2] - 254.016, dclip[3] - 15.0]
        base_transform = (1.0, 1.0, -254.016, -15.0)
    if top_y is None:
        top_y = base_clip[1]
    base_center = (base_clip[0] + base_clip[2]) / 2
    target_center = base_center if center_x is None else center_x
    tx = target_center - scale * base_center
    ty = top_y - scale * base_clip[1]
    clip = [scale * base_clip[0] + tx, top_y,
            scale * base_clip[2] + tx, top_y + scale * (base_clip[3] - base_clip[1])]
    sx, sy, bx, by = base_transform
    transform = (scale * sx, scale * sy, scale * bx + tx, scale * by + ty)
    return clip, transform


def _map_content(page, paths, panel, lookup, color_lookup, specification,
                 outline_width=0.35, scale=1.0, top_y=None, center_x=None,
                 monochrome=None):
    clip, transform = _variant_paths(paths, panel, scale, top_y, center_x)
    streams = []
    for drawing in paths["positive"]:
        tract = drawing["tract_id"]
        if monochrome is None:
            if panel == "C":
                fill = hex_rgb(COLORS[int(lookup.at[tract, "P2_K3_class"])])
            else:
                fill = color_lookup[tract]
        else:
            row = lookup.loc[tract]
            if monochrome == "SOVI":
                u = float(row.SOVI_SCORE) / 100.0
            else:
                lo = specification["burden_normalization"]["minimum_hr"]
                hi = specification["burden_normalization"]["maximum_hr"]
                u = (float(row.MeanTotal5) - lo) / (hi - lo)
            linear = _lab_to_linear(np.array([91 - 49 * u, 0.0, 0.0]))
            fill = tuple(_linear_to_srgb(linear).tolist())
        # Same-color edge overprint closes raster antialias seams without drawing a
        # contrasting boundary or changing any source polygon coordinates.
        streams.append(_path_stream(drawing, fill=fill, stroke=fill,
                                    width=SEAM_OVERLAP_PT, transform=transform))
    for drawing in paths["NA"]:
        streams.append(_path_stream(drawing, fill=(1.0, 1.0, 1.0),
                                    stroke=NA_STROKE, width=0.45, transform=transform))
    for drawing in paths["high_high"]:
        streams.append(_path_stream(drawing, stroke=SCREEN_STROKE,
                                    width=outline_width, transform=transform))
    x0, y0, x1, y1 = clip
    content = (f"q 1 0 0 -1 0 {page.rect.height:.8f} cm "
               f"{x0:.8f} {y0:.8f} {x1 - x0:.8f} {y1 - y0:.8f} re W n\n" +
               "".join(streams) + "Q\n")
    _append(page, content)
    return clip


def _fonts(page):
    page.insert_font(fontname="ArialBody", fontfile="C:/Windows/Fonts/arial.ttf")
    page.insert_font(fontname="ArialBold", fontfile="C:/Windows/Fonts/arialbd.ttf")


def _text(page, x, y, value, size=7.5, bold=False, rotate=0, align="left"):
    fontfile = "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    name = "ArialBold" if bold else "ArialBody"
    if align == "center":
        metrics = fitz.Font(fontfile=fontfile)
        x -= metrics.text_length(value, fontsize=size) / 2
    page.insert_text((x, y), value, fontname=name, fontsize=size, rotate=rotate,
                     color=(0.08, 0.08, 0.08))


def _title(page, title, center_x, baseline=421.3027):
    _text(page, center_x, baseline, title, size=9.5, bold=True, align="center")


def _shading(page, rect, rgb, name="BivariateKey"):
    doc = page.parent
    n = rgb.shape[0]
    function = doc.get_new_xref()
    doc.update_object(function,
                      f"<< /FunctionType 0 /Domain [0 1 0 1] /Range [0 1 0 1 0 1] "
                      f"/Size [{n} {n}] /BitsPerSample 16 /Order 1 "
                      f"/Encode [0 {n-1} 0 {n-1}] /Decode [0 1 0 1 0 1] >>")
    doc.update_stream(function, np.rint(rgb * 65535).astype(">u2").tobytes())
    shading = doc.get_new_xref()
    doc.update_object(shading,
                      f"<< /ShadingType 1 /ColorSpace /DeviceRGB /Domain [0 1 0 1] "
                      f"/Function {function} 0 R /AntiAlias true >>")
    resources = page.parent.xref_get_key(page.xref, "Resources")
    if resources[0] != "xref":
        raise ValueError("Expected page resource dictionary")
    resource_id = int(resources[1].split()[0])
    page.parent.xref_set_key(resource_id, "Shading/" + name, f"{shading} 0 R")
    x0, y0, x1, y1 = rect
    _append(page, f"q {x1-x0:.8f} 0 0 {y1-y0:.8f} {x0:.8f} "
            f"{page.rect.height-y1:.8f} cm /{name} sh Q")


def _bivariate_legend(page, specification, rect, text_size=7.5):
    x0, y0, x1, y1 = rect
    uu, vv = np.meshgrid(np.linspace(0, 1, 129), np.linspace(0, 1, 129))
    # The display equation is evaluated at the same continuous axes as the pinned legend.
    rgb = continuous_rgb(uu, vv, specification)
    _shading(page, rect, rgb)
    page.draw_rect(fitz.Rect(rect), color=(0.2, 0.2, 0.2), width=0.35)
    lo = specification["burden_normalization"]["minimum_hr"]
    hi = specification["burden_normalization"]["maximum_hr"]
    x_ticks = [25, 35, 45, 50]
    for value in x_ticks:
        px = x0 + (value - lo) / (hi - lo) * (x1 - x0)
        page.draw_line((px, y1), (px, y1 + 2), color=(0.2, 0.2, 0.2), width=0.35)
        _text(page, px, y1 + 9, str(value), size=text_size, align="center")
    for value in [0, 50, 100]:
        py = y1 - value / 100 * (y1 - y0)
        page.draw_line((x0 - 2, py), (x0, py), color=(0.2, 0.2, 0.2), width=0.35)
        _text(page, x0 - 5 - fitz.Font(fontfile="C:/Windows/Fonts/arial.ttf").text_length(
            str(value), fontsize=text_size), py + 2.6, str(value), size=text_size)
    label = "SOVI score (0-100)"
    length = fitz.Font(fontfile="C:/Windows/Fonts/arial.ttf").text_length(label, fontsize=text_size)
    _text(page, x0 - (30 if text_size <= 7.5 else 35),
          (y0 + y1 + length) / 2, label, size=text_size, rotate=90)
    _text(page, (x0 + x1) / 2, y1 + (19 if text_size <= 7.5 else 25),
          "Equivalent service-deficit hours", size=text_size, align="center")


def _class_legend(page, y, scale=1.0, detail=False):
    if detail:
        starts = [100, 200, 300, 390]
        label_y = y + 11
        size = 9
        sw = 10
    else:
        starts = [24, 57, 90, 124] if scale < 1.1 else [43, 94, 145, 196]
        label_y = y + 8.5
        size = 7.5
        sw = 8
    for i, label in enumerate(["C1", "C2", "C3", "N/A (16)"]):
        x = starts[i]
        fill = (1, 1, 1) if i == 3 else hex_rgb(COLORS[i + 1])
        stroke = NA_STROKE if i == 3 else None
        page.draw_rect(fitz.Rect(x, y, x + sw, y + (7 if not detail else 9)),
                       color=stroke, fill=fill,
                       width=0.45 if i == 3 else 0)
        _text(page, x + sw + 4, label_y, label, size=size)


def _screening_keys(page, y, line_width, n_a_x=466, label_size=7.5):
    page.draw_rect(fitz.Rect(276.5, y - 7, 285.5, y - 1),
                   color=SCREEN_STROKE, width=line_width)
    _text(page, 290, y, "Q4 + burden >= P75", size=label_size)
    page.draw_rect(fitz.Rect(n_a_x, y - 7, n_a_x + 9, y - 1),
                   color=NA_STROKE, fill=(1, 1, 1), width=0.45)
    _text(page, n_a_x + 13, y, "N/A (16)", size=label_size)


def _layout_legend(page, specification, layout, outline_width):
    if layout == "A":
        _class_legend(page, 577)
        _bivariate_legend(page, specification, (326, 577, 487, 610))
        _screening_keys(page, 642.5, outline_width)
    else:
        _class_legend(page, 613, scale=1.25)
        _bivariate_legend(page, specification, (318, 615, 493, 657))
        _screening_keys(page, 710, outline_width, n_a_x=448)


def _page_from_source(source_pdf, height):
    output = fitz.open()
    page = output.new_page(width=PAGE_W, height=height)
    with fitz.open(stream=source_pdf, filetype="pdf") as original:
        page.show_pdf_page(fitz.Rect(0, 0, PAGE_W, 410), original, 0,
                           clip=fitz.Rect(0, 0, PAGE_W, 410), keep_proportion=False)
    _fonts(page)
    _title(page, TITLE_C, 145.0)
    _title(page, TITLE_D, 394.0)
    return output


def build_full_figure(source_pdf, table, paths, display, specification,
                      layout="B", outline_width=0.35):
    height = PAGE_A_H if layout == "A" else PAGE_B_H
    doc = _page_from_source(source_pdf, height)
    page = doc[0]
    lookup = table.set_index("tract_id")
    color_lookup = {r.tract_id: (r.blue_amber_R, r.blue_amber_G, r.blue_amber_B)
                    for r in display.itertuples()}
    if layout == "A":
        _map_content(page, paths, "C", lookup, color_lookup, specification,
                     outline_width=outline_width)
        _map_content(page, paths, "D", lookup, color_lookup, specification,
                     outline_width=outline_width)
        _layout_legend(page, specification, "A", outline_width)
    else:
        scale = 1.25
        _map_content(page, paths, "C", lookup, color_lookup, specification,
                     outline_width=outline_width, scale=scale, top_y=429.0, center_x=133.488)
        _map_content(page, paths, "D", lookup, color_lookup, specification,
                     outline_width=outline_width, scale=scale, top_y=429.0, center_x=387.504)
        _layout_legend(page, specification, "B", outline_width)
    doc.set_metadata({"title": "Figure 7. Community recovery types and social vulnerability",
                      "subject": "P2/K3 classes; continuous social vulnerability and recovery burden"})
    return doc


def build_details(table, paths, display, specification, output_dir, outline_width=0.35):
    lookup = table.set_index("tract_id")
    color_lookup = {r.tract_id: (r.blue_amber_R, r.blue_amber_G, r.blue_amber_B)
                    for r in display.itertuples()}
    details = fitz.open()
    for panel, title in [("C", "Community recovery types (map enlargement)"),
                         ("D", "Recovery burden and social vulnerability (map enlargement)")]:
        page = details.new_page(width=PAGE_W, height=540)
        _fonts(page)
        _text(page, PAGE_W / 2, 30, title, size=11, bold=True, align="center")
        base = paths["map_clip"]
        if panel == "C":
            base = [base[0] - 254.016, base[1] - 15, base[2] - 254.016, base[3] - 15]
        _map_content(page, paths, panel, lookup, color_lookup, specification,
                     outline_width=outline_width, scale=2.0, top_y=68,
                     center_x=PAGE_W / 2)
        if panel == "C":
            _class_legend(page, 363, detail=True)
        else:
            _bivariate_legend(page, specification, (112, 366, 406, 426), text_size=9)
            _screening_keys(page, 491, outline_width, n_a_x=405, label_size=8.5)
    details.set_metadata({"title": "Figure 7 unnumbered map enlargements",
                          "subject": "Review-only geography; no changed tract values"})
    return details


def build_outline_comparison(table, paths, display, specification):
    doc = fitz.open()
    lookup = table.set_index("tract_id")
    color_lookup = {r.tract_id: (r.blue_amber_R, r.blue_amber_G, r.blue_amber_B)
                    for r in display.itertuples()}
    for width in [0.25, 0.35, 0.40]:
        page = doc.new_page(width=PAGE_W, height=440)
        _fonts(page)
        _text(page, PAGE_W / 2, 28, f"Q4 and upper-quartile burden outlines: {width:.2f} pt",
              size=11, bold=True, align="center")
        _map_content(page, paths, "D", lookup, color_lookup, specification,
                     outline_width=width, scale=2.3, top_y=70, center_x=PAGE_W / 2)
    return doc


def build_accessibility_reference(table, paths, specification, outline_width=0.35):
    doc = fitz.open()
    page = doc.new_page(width=PAGE_W, height=420)
    _fonts(page)
    _text(page, PAGE_W / 2, 25, "Continuous social vulnerability and recovery burden",
          size=11, bold=True, align="center")
    lookup = table.set_index("tract_id")
    display = {tract: (1.0, 1.0, 1.0) for tract in lookup.index}
    for panel, cx, label in [("D", 133.5, "SOVI score (0-100)"),
                             ("D", 387.5, "Five-policy deficit (hours)")]:
        # A side-by-side, neutral lightness view isolates each continuous quantity.
        _text(page, cx, 51, label, size=9, bold=True, align="center")
        _map_content(page, paths, panel, lookup, display, specification,
                     outline_width=outline_width, scale=1.15, top_y=72,
                     center_x=387.504 if cx > 250 else 133.488,
                     monochrome="SOVI" if cx < 250 else "burden")
        x0, x1 = cx - 67, cx + 67
        ramp = np.tile(np.linspace(0, 1, 129), (129, 1))
        neutral = _linear_to_srgb(_lab_to_linear(np.stack(
            [91 - 49 * ramp, np.zeros_like(ramp), np.zeros_like(ramp)], axis=-1)))
        _shading(page, (x0, 275, x1, 286), neutral,
                 name="SOVIRamp" if cx < 250 else "BurdenRamp")
        page.draw_rect(fitz.Rect(x0, 275, x1, 286), color=(0.2, 0.2, 0.2), width=0.35)
        if cx < 250:
            tick_labels = ["0", "50", "100"]
        else:
            lo = specification["burden_normalization"]["minimum_hr"]
            hi = specification["burden_normalization"]["maximum_hr"]
            tick_labels = [f"{lo:g}", f"{(lo + hi) / 2:g}", f"{hi:g}"]
        for frac, text_value in zip([0, 0.5, 1], tick_labels):
            x = x0 + frac * (x1 - x0)
            page.draw_line((x, 286), (x, 289), color=(0.2, 0.2, 0.2), width=0.35)
            _text(page, x, 298, text_value, size=7.5, align="center")
        _text(page, cx, 312, label, size=7.5, align="center")
    _screening_keys(page, 344, outline_width, n_a_x=405, label_size=8)
    return doc


def verify_inputs(table, display, paths, specification, expected_geoids):
    table = table.copy()
    table["tract_id"] = table.tract_id.astype(str)
    display = display.copy()
    display["tract_id"] = display.tract_id.astype(str)
    assert len(table) == 2299 and table.tract_id.is_unique
    assert table.tract_id.str.fullmatch(r"\d{11}").all()
    assert int(table.Population.sum()) == 9066522
    assert table.P2_K3_class.value_counts().sort_index().tolist() == [1235, 428, 636]
    assert len(paths["positive"]) == 2303
    assert len({p["tract_id"] for p in paths["positive"]}) == 2299
    assert len(paths["NA"]) == 16 and len(paths["high_high"]) == 94
    assert {p["tract_id"] for p in paths["positive"]} == set(table.tract_id)
    assert {p["tract_id"] for p in paths["NA"]} == set(expected_geoids["NA"])
    independently_selected = set(table.loc[
        table.frozen_SOVI_quartile.eq("Q4") & table.MeanTotal5.ge(P75), "tract_id"])
    assert len(independently_selected) == 94
    assert independently_selected == set(expected_geoids["high_high"])
    assert {p["tract_id"] for p in paths["high_high"]} == independently_selected
    population_by_geoid = table.set_index("tract_id").Population
    assert int(population_by_geoid.loc[list(independently_selected)].sum()) == 350799
    assert set(display.tract_id) == set(table.tract_id)
    aligned = table.set_index("tract_id").loc[display.tract_id]
    np.testing.assert_array_equal(display.SOVI_SCORE, aligned.SOVI_SCORE)
    np.testing.assert_array_equal(display.MeanTotal5, aligned.MeanTotal5)
    np.testing.assert_array_equal(display.frozen_SOVI_quartile, aligned.frozen_SOVI_quartile)
    lo = specification["burden_normalization"]["minimum_hr"]
    hi = specification["burden_normalization"]["maximum_hr"]
    np.testing.assert_allclose(display.burden_u, (display.MeanTotal5 - lo) / (hi - lo), atol=1e-13, rtol=0)
    np.testing.assert_allclose(display.vulnerability_v, display.SOVI_SCORE / 100, atol=1e-14, rtol=0)
    actual = continuous_rgb(display.burden_u.to_numpy(), display.vulnerability_v.to_numpy(), specification)
    stored = display[["blue_amber_R", "blue_amber_G", "blue_amber_B"]].to_numpy()
    assert float(np.max(np.abs(actual - stored))) < 2e-6
    assert np.isfinite(table["MeanTotal5"]).all()
    return table, display


def write_pdf(path, doc):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(doc.tobytes(garbage=4, deflate=True, no_new_id=True))


def export_png(pdf_path, png_path, dpi=600):
    with fitz.open(pdf_path) as doc:
        doc[0].get_pixmap(dpi=dpi, alpha=False).save(str(png_path))
