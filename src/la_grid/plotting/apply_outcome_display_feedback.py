"""Apply the author's bounded Figure 1/4/5 display corrections.

Read native artwork only. No model, result table, trajectory, scheduling,
sampling, clustering or uncertainty-estimation module is imported or invoked.
Curve vertices and outcome coordinates are retained; only paint, framework
illustrations and the common Figure 5 comparison key are changed.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile

import fitz
from pypdf.generic import ArrayObject, ContentStream, DecodedStreamObject, FloatObject

from la_grid.paths import REPO_ROOT
from la_grid.plotting.refine_policy_cluster_presentation import streams

ROOT = REPO_ROOT
REVIEW = ROOT / "results/figure_review"
HISTORY = ROOT / "provenance/figure_review_history/outcome_display_before_20261007"
PREVIEW = Path(tempfile.gettempdir()) / "la_display_feedback_20261007"
MM = 72 / 25.4
ARIAL = "C:/Windows/Fonts/arial.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"
INK = (.125, .145, .169)
BLUE = (.18, .43, .62)
OCHRE = (.67, .43, .26)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text(page, x, y, label, size=7.5, bold=False, center=False, color=INK):
    font = fitz.Font(fontfile=BOLD if bold else ARIAL)
    if center:
        x -= font.text_length(label, fontsize=size) / (2 * MM)
    page.insert_text((x * MM, y * MM), label, fontsize=size, color=color,
                     fontname="DisplayArialBold" if bold else "DisplayArial")


def fonts(page):
    page.insert_font(fontname="DisplayArial", fontfile=ARIAL)
    page.insert_font(fontname="DisplayArialBold", fontfile=BOLD)


def record_source(key):
    target = REVIEW / "Main" / (key + ".pdf")
    original = HISTORY / "Main" / target.name
    original.parent.mkdir(parents=True, exist_ok=True)
    if not original.exists():
        shutil.copy2(target, original)
        shutil.copy2(target.with_suffix(".png"), original.with_suffix(".png"))
    return target, original


def finish(doc, key, stats):
    target = REVIEW / "Main" / (key + ".pdf")
    temporary = target.with_suffix(".display.pdf")
    doc.save(temporary, garbage=4, deflate=True)
    doc.close()
    temporary.replace(target)
    with fitz.open(target) as exported:
        p = exported[0]
        spans = [s for b in p.get_text("dict")["blocks"]
                 for line in b.get("lines", []) for s in line["spans"]]
        minimum = min(s["size"] for s in spans)
        assert minimum >= 6.99, (key, minimum)
        assert all(p.rect.contains(fitz.Rect(s["bbox"])) for s in spans)
        assert all("Arial" in s["font"] for s in spans)
        pix = p.get_pixmap(matrix=fitz.Matrix(600 / 72, 600 / 72), alpha=False)
        pix.set_dpi(600, 600)
        pix.save(target.with_suffix(".png"))
        p.get_pixmap(matrix=fitz.Matrix(1.8, 1.8)).save(PREVIEW / (key + "_after.png"))
        stats.update(file="Main/" + key + ".pdf", size_mm=[p.rect.width / MM, p.rect.height / MM],
                     minimum_font_pt=minimum, fonts=sorted({s["font"] for s in spans}),
                     pdf_sha256=sha(target), png_sha256=sha(target.with_suffix(".png")))
    return stats


def framework():
    target, original = record_source("Fig01")
    source = fitz.open(original)
    doc = fitz.open(original)
    background = doc[0]
    # The fifth card only: leave the first four stages and all connecting
    # methodology outside this card at their registered coordinates.
    card = fitz.Rect(94.8 * MM, 164.2 * MM, 181.7 * MM, 216.7 * MM)
    background.add_redact_annot(card, fill=(1, 1, 1))
    # Keep the surrounding nested vector artwork untouched. Redaction removes
    # old text and paints an opaque white card over its former illustrations.
    background.apply_redactions(images=0, graphics=0)
    print("  fifth-card text cleared", flush=True)
    # Typeset on a small, independent overlay before adding any nested map
    # resources, avoiding repeated recursive font scans of the original GIS.
    overlay = fitz.open()
    page = overlay.new_page(width=background.rect.width, height=background.rect.height)
    fonts(page)
    page.draw_rect(fitz.Rect(94.8 * MM, 164.2 * MM, 181.7 * MM, 169.0 * MM),
                   color=None, fill=(.91, .95, .98))
    page.draw_circle((97 * MM, 166.5 * MM), 1.6 * MM, color=None, fill=BLUE)
    text(page, 97, 167.5, "5", 9.5, True, True, (1, 1, 1))
    text(page, 99.5, 167.8, "Community Outcomes", 9.5, True)
    text(page, 138.25, 174, "Compare restoration priorities", 7.5, True, True)

    # A distribution sketch with continuous group position, avoiding an
    # unexplained quartet of labelled rectangles or metric abbreviations.
    xs = [128, 135.3, 142.7, 150]
    ys = [179.8, 181.5, 183, 184.2]
    page.draw_line((127 * MM, 186 * MM), (151 * MM, 186 * MM), color=(.65, .69, .72), width=.4)
    page.draw_polyline([(x * MM, y * MM) for x, y in zip(xs, ys)], color=BLUE, width=.7)
    for x, y in zip(xs, ys):
        page.draw_circle((x * MM, y * MM), .55 * MM, color=BLUE, fill=BLUE, width=.4)
    page.draw_polyline([(x * MM, (y + 2.2 - .35 * i) * MM)
                        for i, (x, y) in enumerate(zip(xs, ys))], color=OCHRE, width=.7)
    text(page, 127, 189.2, "Lower", 7)
    text(page, 151, 189.2, "Higher", 7, center=True)

    for cx, labels in [
        (110, ["Service loss and T80", "All tracts", "Hospital-linked tracts"]),
        (139, ["Vulnerability groups", "Group differences", "Inequality (Gini)"]),
        (168, ["Community typology", "Hotspot score"]),
    ]:
        for y, label in zip([193.0, 196.5, 200.0], labels):
            text(page, cx, y, label, 7, center=True)

    # Separate the tested resource families from the assumption checks. The
    # labels describe what is examined, instead of an undifferentiated footer.
    page.draw_line((98 * MM, 203 * MM), (179 * MM, 203 * MM), color=(.78, .83, .87), width=.4)
    page.draw_line((139 * MM, 205 * MM), (139 * MM, 215 * MM), color=(.78, .83, .87), width=.4)
    for cx, title, labels in [
        (118, "Resource dependence", ["Crew availability", "Repair duration"]),
        (159, "Model assumptions", ["Mapping and source gate", "SCE planning limits"]),
    ]:
        text(page, cx, 207, title, 7.5, True, True, BLUE)
        for y, label in zip([211, 214.5], labels):
            text(page, cx, y, label, 7, center=True)
    # Illustrate the outcome domains with existing native result artwork,
    # rather than grafting the deeply nested historical framework into itself.
    recovery = fitz.open(REVIEW / "Main/Fig04.pdf")
    typology = fitz.open(REVIEW / "Main/Fig07.pdf")
    tint_green(recovery)
    tint_green(typology)
    page.show_pdf_page(fitz.Rect(98*MM, 177*MM, 122*MM, 189*MM), recovery, 0,
                       clip=fitz.Rect(33*MM, 15*MM, 179*MM, 77*MM))
    page.show_pdf_page(fitz.Rect(157*MM, 177*MM, 179*MM, 189*MM), typology, 0,
                       clip=fitz.Rect(5*MM, 181*MM, 89*MM, 235*MM))
    # Use the same native graft operation as show_pdf_page, with a unique
    # root-level resource name. Its public wrapper recursively enumerates all
    # historical GIS resources solely to choose a name, which is unnecessary
    # for this explicitly named, single overlay.
    assert doc.xref_get_key(background.xref, "Resources/XObject/DisplayOutcomes20261007")[0] == "null"
    background.wrap_contents()
    background._show_pdf_page(overlay[0], overlay=True,
        matrix=(1, 0, 0, 1, 0, 0), clip=overlay[0].rect * ~overlay[0].transformation_matrix,
        graftmap=fitz.Graftmap(doc), _imgname="DisplayOutcomes20261007")
    recovery.close()
    typology.close()
    overlay.close()
    source.close()
    return finish(doc, "Fig01", {"change": "Fifth card: complete community outcome domains, blue identity and two distinct condition families",
                                "before_sha256": sha(original)})


def tint_green(doc):
    """Repaint green operators only in an in-memory framework illustration."""
    number = rb"([+-]?(?:\d{1,3}(?:\.\d{0,9})?|\.\d{1,9}))"
    operands = re.compile(rb"(?<![A-Za-z0-9.])" + number + rb"\s+" + number + rb"\s+" + number + rb"\s*$")
    for x in streams(doc):
        raw = doc.xref_stream(x)
        # Framework miniatures retain paths only; their labels are supplied
        # at normal finished size outside the illustration.
        raw = re.sub(rb"\bBT\b.*?\bET\b", b"", raw, flags=re.S)
        replacements = []
        for operator in re.finditer(rb"\b(?:RG|rg)\b", raw):
            window_start = max(0, operator.start()-75)
            m = operands.search(raw[window_start:operator.start()])
            if m:
                r, g, b = [float(m.group(i)) for i in [1, 2, 3]]
                if g > r+.04 and g > b+.02:
                    replacements.append((window_start+m.start(), operator.end(),
                        (" ".join(str(v) for v in BLUE)+" "+operator.group().decode()).encode()))
        if replacements:
            pieces, cursor = [], 0
            for start, end, replacement in replacements:
                pieces.extend([raw[cursor:start], replacement])
                cursor = end
            pieces.append(raw[cursor:])
            doc.update_stream(x, b"".join(pieces))
        else:
            doc.update_stream(x, raw)


def solid_policy_curves():
    target, original = record_source("Fig04")
    doc = fitz.open(original)
    affected = 0
    for x in streams(doc):
        raw = doc.xref_stream(x)
        if not raw:
            continue
        obj = DecodedStreamObject()
        obj.set_data(raw)
        cs = ContentStream(obj, None)
        out = []
        for args, op in cs.operations:
            # Reset every non-solid dash pattern, including the thinner
            # secondary policies and their legend samples. The existing grid
            # is already solid; all geometry, weights and opacity are retained.
            if op == b"d":
                if len(args[0]):
                    affected += 1
                args = [ArrayObject(), FloatObject(0)]
            out.append((args, op))
        # Prove that the only change is insertion of dash-reset operators.
        before = [(a, o) for a, o in cs.operations if o != b"d"]
        after = [(a, o) for a, o in out if o != b"d"]
        assert before == after
        cs.operations = out
        doc.update_stream(x, cs.get_data())
    assert affected >= 5, affected
    return finish(doc, "Fig04", {"change": "All nine recovery curves and corresponding line keys are solid; weights/colors/opacity retained",
                                "dash_resets": affected, "path_coordinates_changed": False,
                                "before_sha256": sha(original)})


def align_comparison_key():
    target, original = record_source("Fig05")
    doc = fitz.open(original)
    p = doc[0]
    # This rectangle contains only the common C/D key; plotted values, ticks,
    # intervals and map geometries are outside it.
    p.add_redact_annot(fitz.Rect(75, 288, 435, 305), fill=(1, 1, 1))
    p.apply_redactions(images=0, graphics=0)
    fonts(p)
    size = 7.5
    font = fitz.Font(fontfile=ARIAL)
    prefix = "Vulnerability-first compared with:"
    entries = [("Hospital-first", (.3333333,) * 3, "o"),
               ("Impact-first", (1, .4980392, 0), "s"),
               ("Degree-first", (.3019608, .6862745, .2901961), "^")]
    prefix_width = font.text_length(prefix, fontsize=size)
    widths = [font.text_length(label, fontsize=size) + 14 for label, _, _ in entries]
    total = prefix_width + 14 + sum(widths) + 12 * (len(entries) - 1)
    x = (p.rect.width - total) / 2
    baseline = 299.0
    p.insert_text((x, baseline), prefix, fontname="DisplayArial", fontsize=size, color=INK)
    x += prefix_width + 14
    for (label, color, shape), width in zip(entries, widths):
        cx, cy, r = x + 2, baseline - 2.8, 2
        if shape == "o":
            p.draw_circle((cx, cy), r, color=color, fill=color, width=.6)
        elif shape == "s":
            p.draw_rect(fitz.Rect(cx-r, cy-r, cx+r, cy+r), color=color, fill=color, width=.6)
        else:
            p.draw_polyline([(cx, cy-r), (cx-r, cy+r), (cx+r, cy+r), (cx, cy-r)],
                            color=color, fill=color, width=.6)
        p.insert_text((x + 11, baseline), label, fontname="DisplayArial", fontsize=size, color=INK)
        x += width + 12
    return finish(doc, "Fig05", {"change": "Single baseline, font size and centered layout for C/D reference key",
                                "reference_key_baseline_pt": baseline, "before_sha256": sha(original)})


def update_csv(path, fn):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    for row in rows:
        fn(row)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def integrate(records):
    generator = Path(__file__).relative_to(ROOT).as_posix()
    keys = {r["file"]: r for r in records}
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    def index(row):
        source = ROOT / row["source_path"]
        key = source.relative_to(REVIEW).with_suffix(".pdf").as_posix()
        if key not in keys:
            return
        shutil.copy2(source, ROOT / "results/figures" / row["file"])
        row.update(sha256_or_lfs_oid="sha256:" + sha(source), generator=generator,
                   notes="Author-requested framework, uniform recovery-curve strokes and aligned comparison-key correction; numerical results unchanged.")
    update_csv(ROOT / "results/figures/FIGURE_INDEX.csv", index)
    def manifest(row):
        key = Path(row["final_name"]).with_suffix(".pdf").as_posix()
        if key not in keys:
            return
        p = REVIEW / row["final_name"]
        old = HISTORY / row["final_name"]
        r = keys[key]
        row.update(source_file=p.relative_to(ROOT).as_posix(), current_source_file=p.relative_to(ROOT).as_posix(),
                   source_commit="OUTCOME_DISPLAY_UPDATE_20261007", parent_source_commit=source_commit,
                   parent_source_file=old.relative_to(ROOT).as_posix(), parent_sha256=sha(old), sha256=sha(p),
                   size_mm="%.3f x %.3f" % tuple(r["size_mm"]), min_font_pt="%.3f" % r["minimum_font_pt"],
                   status="AUTHOR_REQUESTED_CURRENT_DISPLAY")
    update_csv(REVIEW / "FIGURE_MANIFEST.csv", manifest)

    p = REVIEW / "MANUSCRIPT_FACING_CAPTIONS.md"
    content = p.read_text(encoding="utf-8")
    content = content.replace("Figure 1 wording and presentation were updated at the author's request on 2026-10-06; the previous artwork is retained as provenance.",
        "Figures 1, 4 and 5 display corrections reflect the author's feedback on 2026-10-07; previous artwork is retained as provenance.")
    content = content.replace("using population-weighted and hospital-linked tract service loss, Q1–Q4 service loss, the signed Q4–Q1 difference, the absolute Q4–Q1 difference within each realization, and population-weighted Gini.",
        "using population-weighted service loss across all tracts and within social-vulnerability groups, mean service loss in hospital-linked tracts, T80, the direction and magnitude of the highest–lowest vulnerability group difference within each realization, and population-weighted Gini.")
    content = content.replace("use stronger strokes; the remaining policies remain visible with lower opacity.",
        "use stronger strokes; the remaining policies remain visible with lower opacity. All nine recovery curves use solid lines, with Unconstrained shown in black.")
    while "All nine recovery curves use solid lines, with Unconstrained shown in black. All nine recovery curves use solid lines, with Unconstrained shown in black." in content:
        content = content.replace("All nine recovery curves use solid lines, with Unconstrained shown in black. All nine recovery curves use solid lines, with Unconstrained shown in black.",
            "All nine recovery curves use solid lines, with Unconstrained shown in black.")
    content = content.replace("the policy color/line identity used in Figure 4.",
        "the policy colors and visual emphasis used in Figure 4; line patterns are shown in the shared B/C key.")
    p.write_text(content, encoding="utf-8")

    main = fitz.open()
    for i in range(1, 8):
        with fitz.open(REVIEW / f"Main/Fig{i:02}.pdf") as d:
            main.insert_pdf(d)
    main.save(REVIEW / "ALL_MAIN_FIGURES.pdf", garbage=4, deflate=True)
    main.close()
    headings = list(re.finditer(r"(?m)^## (.+)\n\n", content))
    lookup = {}
    for i, m in enumerate(headings):
        title = m.group(1)
        body = content[m.end():headings[i+1].start() if i+1 < len(headings) else len(content)].strip()
        if title.startswith("Figure "):
            key = f'Main/Fig{int(title.split(".")[0].replace("Figure ", "")):02}.pdf'
        elif title.startswith("Supplementary Figure S"):
            key = f'Supplement/FigS{int(title.split(".")[0].replace("Supplementary Figure S", "")):02}.pdf'
        else:
            continue
        lookup[key] = (title, body)
    order = [f"Main/Fig{i:02}.pdf" for i in range(1, 8)] + [f"Supplement/FigS{i:02}.pdf" for i in [1] + list(range(3, 14))]
    book = fitz.open()
    for key in order:
        with fitz.open(REVIEW / key) as d:
            book.insert_pdf(d)
        title, body = lookup[key]
        page = book.new_page(width=185*MM, height=350*MM)
        fonts(page)
        assert page.insert_textbox(fitz.Rect(14*MM, 16*MM, 171*MM, 28*MM), title,
                                   fontname="DisplayArialBold", fontsize=9.5) >= 0
        assert page.insert_textbox(fitz.Rect(14*MM, 31*MM, 171*MM, 333*MM), body,
                                   fontname="DisplayArial", fontsize=9.2, lineheight=1.22) >= 0
    assert len(book) == 38
    book.save(REVIEW / "ALL_FIGURES_WITH_CAPTIONS.pdf", garbage=4, deflate=True)
    book.close()

    p = ROOT / "FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    data["current_code_files"] = [r for r in data["current_code_files"] if r["path"] != generator] + [
        {"path": generator, "sha256": sha(__file__), "tracked_in_current_git": True}]
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/reproducibility/OUTCOME_DISPLAY_FEEDBACK_20261007.json").write_text(
        json.dumps({"source_commit": source_commit, "figures": records,
                    "scientific_calculation_invoked": False}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    PREVIEW.mkdir(exist_ok=True)
    print("Updating Figure 1 outcomes card", flush=True)
    records = [framework()]
    print("Updating Figure 4 solid policy curves", flush=True)
    records.append(solid_policy_curves())
    print("Aligning Figure 5 C/D comparison key", flush=True)
    records.append(align_comparison_key())
    print("Synchronizing current figure copies and complete packet", flush=True)
    integrate(records)
    print(json.dumps(records, indent=2))
