"""Apply author terminology to the current review files; no result computation.

Only native PDF text, captions, display labels and review indexes are edited.
Scientific source files and embedded browser observations remain unchanged.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import re
import subprocess
import tempfile
import tokenize

import fitz
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
REVIEW = ROOT / "results/figure_review"
TEMP = Path(tempfile.gettempdir()) / "la_grid_reader_terminology_20261004"
REGULAR = "C:/Windows/Fonts/arial.ttf"
BOLD = "C:/Windows/Fonts/arialbd.ttf"
ITALIC = "C:/Windows/Fonts/ariali.ttf"
MM = 72 / 25.4
RETIRED = re.compile(r"\bmatched\b|\bburdens?\b", re.I)
CHANGES = []
PDF_EDITS = []


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def wording(text):
    rules = [
        (r"Comparable tracts matched \(%\)", "Comparable tract agreement (%)"),
        (r"Saved matched comparisons", "Distributional effects"),
        (r"Saved matched-mean bootstrap", "Distributional effects: bootstrap CI"),
        (r"Mean matched change", "Mean distributional effect"),
        (r"Median matched change", "Median distributional effect"),
        (r"mean matched tract-level service-loss changes", "mean tract-level distributional effects on service loss"),
        (r"matched physical realizations", "physical realizations shared across policies"),
        (r"matched mean difference", "mean distributional effect"),
        (r"mean matched difference", "mean distributional effect"),
        (r"matched-mean", "mean distributional-effect"),
        (r"matched mean effects", "mean distributional effects"),
        (r"matched means", "mean distributional effects"),
        (r"matched raw distributions", "distributions of effects across realizations"),
        (r"Tract-burden inequality", "Tract service-loss inequality"),
        (r"equal tract burden", "equal tract service loss"),
        (r"unequal tract burden", "unequal tract service loss"),
        (r"integrated burden", "integrated service loss"),
        (r"\bburdens\b", "service losses"),
        (r"\bburden\b", "service loss"),
        (r"\bmatched\b", "distributional effects"),
    ]
    for old, new in rules:
        text = re.sub(old, new, text, flags=re.I)
    return text


def record(path, before, detail):
    CHANGES.append({"file": path.relative_to(ROOT).as_posix(),
                    "before_sha256": before, "after_sha256": sha(path),
                    "change": detail})


def pdf_wording(path):
    before = sha(path)
    original = fitz.open(path)
    numeric_before = re.findall(r"[+-]?\d+(?:\.\d+)?", "".join(p.get_text() for p in original))
    local_edits = []
    for number, page in enumerate(original):
        edits = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    old = span["text"]
                    if not RETIRED.search(old):
                        continue
                    new = wording(old)
                    # A shorter heading preserves the original text size/space.
                    new = new.replace("Uncertainty and reference dependence |", "Uncertainty and references |")
                    size = span["size"]
                    bold = "Bold" in span["font"]
                    italic = "Italic" in span["font"]
                    fontfile = BOLD if bold else ITALIC if italic else REGULAR
                    font = fitz.Font(fontfile=fontfile)
                    width = font.text_length(new, fontsize=size)
                    box = fitz.Rect(span["bbox"])
                    direction = line["dir"]
                    angle = 90 if direction[1] < -.5 else 270 if direction[1] > .5 else 0
                    origin = fitz.Point(span["origin"])
                    if angle == 0:
                        # Book titles and panel titles keep their existing center;
                        # footnotes retain left alignment.
                        centered = box.y0 < 90 and not old.startswith("Intervals")
                        if centered:
                            origin.x = (box.x0 + box.x1 - width) / 2
                        assert origin.x >= 0 and origin.x + width <= page.rect.width, (path, new, width)
                    else:
                        center = (box.y0 + box.y1) / 2
                        origin.y = center + width / 2 if angle == 90 else center - width / 2
                    # Leave paths, images, and adjacent text intact.
                    inset = .4
                    rect = fitz.Rect(box.x0 + inset, box.y0 + inset, box.x1 - inset, box.y1 - inset)
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    edits.append((origin, new, size, fontfile, bold, italic, angle, span["color"], old))
        if not edits:
            continue
        page.apply_redactions(images=0, graphics=0)
        for origin, new, size, fontfile, bold, italic, angle, color, old in edits:
            name = "ArialAuthorTermsBold" if bold else "ArialAuthorTermsItalic" if italic else "ArialAuthorTermsRegular"
            page.insert_font(fontname=name, fontfile=fontfile)
            rgb = tuple(((color >> shift) & 255) / 255 for shift in (16, 8, 0))
            page.insert_text(origin, new, fontname=name, fontsize=size, rotate=angle, color=rgb)
            local_edits.append({"file": path.relative_to(ROOT).as_posix(), "page": number + 1,
                                "before": old, "after": new, "font_pt_unchanged": size})
    if not local_edits:
        original.close()
        return
    temporary = TEMP / path.name
    original.save(temporary, garbage=4, deflate=True)
    original.close()
    with fitz.open(temporary) as after:
        assert not RETIRED.search("".join(p.get_text() for p in after)), path
        numeric_after = re.findall(r"[+-]?\d+(?:\.\d+)?", "".join(p.get_text() for p in after))
        assert sorted(numeric_before) == sorted(numeric_after), (path, "PDF numbers changed")
        for page in after:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line["spans"]:
                        assert fitz.Rect(span["bbox"]).x0 >= -.1 and fitz.Rect(span["bbox"]).x1 <= page.rect.width + .1
    path.write_bytes(temporary.read_bytes())
    PDF_EDITS.extend(local_edits)
    record(path, before, "native vector text only; font sizes, axes, numeric text preserved")
    # Update the existing preview, not a second author-facing artwork version.
    preview = path.with_suffix(".png") if path.parent.name == "Supplement" else path.with_name(path.stem + "_600dpi.png")
    if preview.exists():
        old_sha = sha(preview)
        with fitz.open(path) as doc:
            doc[0].get_pixmap(matrix=fitz.Matrix(600 / 72, 600 / 72), alpha=False).save(preview)
            doc[0].get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False).save(TEMP / (path.stem + "_native.png"))
        record(preview, old_sha, "600-dpi preview of wording edit")
    with fitz.open(path) as doc:
        changed_pages = sorted({x["page"] for x in local_edits})
        for i in changed_pages:
            if i in [1, 4, 17, 24, 56] or len(changed_pages) <= 3:
                doc[i - 1].get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False).save(TEMP / (path.stem + f"_p{i:02d}.png"))


def edit_readable_text():
    for path in REVIEW.rglob("*.md"):
        old = path.read_text(encoding="utf-8")
        new = wording(old)
        # This sentence defines the estimand without resurrecting retired names.
        new = re.sub(r"[“\"]Service loss[”\"] and [“\"]cumulative service loss[”\"] refer[^\n]*", "Service loss denotes the modeled service-deficit integral over the stated evaluation horizon.", new, flags=re.I)
        if old != new:
            before = sha(path)
            path.write_text(new, encoding="utf-8")
            record(path, before, "reader-facing terminology only")
    for path in (REVIEW / "Additional_Evidence").glob("*.csv"):
        if path.name == "ACTUAL_PDF_MEASUREMENTS.csv":
            continue
        old = path.read_text(encoding="utf-8")
        new = wording(old)
        if old != new:
            # String-level edits leave every numeric CSV cell/identifier intact.
            oldrows = list(csv.reader(io.StringIO(old)))
            newrows = list(csv.reader(io.StringIO(new)))
            assert len(oldrows) == len(newrows)
            for a, b in zip(oldrows, newrows):
                assert len(a) == len(b)
                for x, y in zip(a, b):
                    if not RETIRED.search(x):
                        assert x == y
            before = sha(path)
            path.write_text(new, encoding="utf-8")
            record(path, before, "display descriptions only; identifiers and numeric cells unchanged")
    path = REVIEW / "Additional_Evidence/build_review.py"
    old = path.read_text(encoding="utf-8")
    tokens = []
    for token in tokenize.generate_tokens(io.StringIO(old).readline):
        if token.type == tokenize.STRING and RETIRED.search(token.string):
            # Single-word mode keys and all underscored result-field IDs remain.
            if not re.fullmatch(r"['\"]matched['\"]", token.string):
                token = token._replace(string=wording(token.string))
        tokens.append(token)
    new = tokenize.untokenize(tokens)
    if new != old:
        compile(new, str(path), "exec")
        before = sha(path)
        path.write_text(new, encoding="utf-8")
        record(path, before, "presentation strings only; scientific expressions unchanged")


def edit_browser():
    for name in ["METRIC_EXPLORER.html", "explorer_template.html"]:
        path = REVIEW / "Additional_Evidence" / name
        old = path.read_text(encoding="utf-8")
        parts = old.splitlines(keepends=True)
        newparts = []
        for line in parts:
            # Do not touch the embedded observations or Plotly library.
            if len(line) > 12000:
                newparts.append(line)
                continue
            if line.lstrip().startswith("<"):
                line = wording(line)
            else:
                line = re.sub(r"(['\"])(.*?)(?<!\\)\1", lambda m: m.group(1) + (wording(m.group(2)) if " " in m.group(2) or "-" in m.group(2) else m.group(2)) + m.group(1), line)
            line = line.replace("const fmt=x=>", "const readerTerm=s=>String(s).replace(/Tract-burden inequality/gi,'Tract service-loss inequality').replace(/\\bburdens\\b/gi,'service losses').replace(/\\bburden\\b/gi,'service loss').replace(/\\bmatched\\b/gi,'distributional effects');\nconst fmt=x=>")
            line = line.replace("const label=k=>D.metrics[k]", "const label=k=>readerTerm(D.metrics[k])")
            line = line.replace("const metricKeys=()=>Object.keys(D.metrics);const M=k=>metricKeys().indexOf(k);const label=k=>D.metrics[k]", "const metricKeys=()=>Object.keys(D.metrics);const M=k=>metricKeys().indexOf(k);const label=k=>readerTerm(D.metrics[k])")
            line = line.replace("return {policy:cname(p)", "return {policy:cname(p)")
            line = line.replace("c.textContent=fmt(r[k])", "c.textContent=(k==='metric'&&D.metrics[r[k]])?readerTerm(D.metrics[r[k]]):readerTerm(fmt(r[k]))")
            line = line.replace("Object.entries(D.metrics)", "Object.entries(D.metrics).map(([k,v])=>[k,readerTerm(v)])")
            newparts.append(line)
        new = "".join(newparts)
        # The large compressed data/library lines must remain byte-identical.
        assert [x for x in parts if len(x) > 12000] == [x for x in new.splitlines(keepends=True) if len(x) > 12000]
        new = new.replace("adopted integrated burden", "time-integrated service loss")
        if new != old:
            before = sha(path)
            path.write_text(new, encoding="utf-8")
            record(path, before, "display text only; compressed observation payload unchanged")


def collections():
    path = REVIEW / "ALL_SUPPLEMENT_FIGURES.pdf"
    before = sha(path)
    book = fitz.open()
    for i in range(1, 14):
        with fitz.open(REVIEW / f"Supplement/FigS{i:02d}.pdf") as doc:
            book.insert_pdf(doc)
    book.save(path, garbage=4, deflate=True)
    book.close()
    record(path, before, "collection updated with the same 13 figures")
    captions = (REVIEW / "MANUSCRIPT_FACING_CAPTIONS.md").read_text(encoding="utf-8")
    titles = list(re.finditer(r"(?m)^## (.+)\n\n", captions))
    lookup = {}
    for i, match in enumerate(titles):
        title = match.group(1)
        body = captions[match.end():titles[i + 1].start() if i + 1 < len(titles) else len(captions)].strip()
        if title.startswith("Figure "):
            key = f"Main/Fig{int(title.split('.')[0].replace('Figure ', '')):02d}.pdf"
        elif title.startswith("Supplementary Figure S"):
            key = f"Supplement/FigS{int(title.split('.')[0].replace('Supplementary Figure S', '')):02d}.pdf"
        else:
            continue
        lookup[key] = (title, body)
    book = fitz.open()
    for key in [f"Main/Fig{i:02d}.pdf" for i in range(1, 8)] + [f"Supplement/FigS{i:02d}.pdf" for i in range(1, 14)]:
        with fitz.open(REVIEW / key) as doc:
            book.insert_pdf(doc)
        title, body = lookup[key]
        page = book.new_page(width=185 * MM, height=350 * MM)
        page.insert_font(fontname="ArialPacketTerms", fontfile=REGULAR)
        page.insert_font(fontname="ArialPacketTermsBold", fontfile=BOLD)
        page.insert_text((14 * MM, 20 * MM), title, fontname="ArialPacketTermsBold", fontsize=9.5)
        assert page.insert_textbox(fitz.Rect(14 * MM, 29 * MM, 171 * MM, 333 * MM), body, fontname="ArialPacketTerms", fontsize=9.2, lineheight=1.22) >= 0, title
    path = REVIEW / "ALL_FIGURES_WITH_CAPTIONS.pdf"
    before = sha(path)
    assert len(book) == 40
    book.save(path, garbage=4, deflate=True)
    book.close()
    record(path, before, "same figure order and caption semantics; author vocabulary applied")


def contact_sheet():
    target = REVIEW / "Additional_Evidence/REVIEW_CONTACT_SHEET.pdf"
    before = sha(target)
    out = fitz.open()
    cell = 0
    for path in sorted(target.parent.glob("*.pdf")):
        if path == target:
            continue
        with fitz.open(path) as doc:
            for number, page in enumerate(doc):
                if cell % 4 == 0:
                    cp = out.new_page(width=595, height=842)
                    cp.insert_font(fontname="ArialContactTerms", fontfile=REGULAR)
                x = 10 + (cell % 2) * 290
                y = 25 + ((cell % 4) // 2) * 405
                cp = out[-1]
                cp.insert_text((x, y - 6), path.stem[:36] + f" p{number + 1}", fontsize=9, fontname="ArialContactTerms")
                cp.insert_image(fitz.Rect(x, y, x + 276, y + 382), pixmap=page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False), keep_proportion=True)
                cell += 1
    out.save(target, garbage=4, deflate=True)
    out.close()
    record(target, before, "four-page-per-sheet overview reflects current reader terminology")


def main():
    TEMP.mkdir(parents=True, exist_ok=True)
    fitz.TOOLS.set_small_glyph_heights(True)
    for path in [REVIEW / "Supplement/FigS06.pdf"] + [REVIEW / "Additional_Evidence" / name for name in ["SAVED_PAIRED_EFFECTS.pdf", "VULNERABILITY_DEFINITIONS.pdf", "ALL_METRIC_RELATIONSHIPS.pdf"]]:
        print("Editing native text:", path.name, flush=True)
        pdf_wording(path)
    edit_readable_text()
    edit_browser()
    collections()
    contact_sheet()
    manifest = REVIEW / "FIGURE_MANIFEST.csv"
    before = sha(manifest)
    frame = pd.read_csv(manifest, dtype=str).fillna("")
    for ext in ["pdf", "png"]:
        mask = frame.final_name.eq("Supplement/FigS06." + ext)
        assert mask.sum() == 1
        for column in ["source_file", "source_commit", "sha256", "current_source_file"]:
            if "parent_" + column not in frame:
                frame["parent_" + column] = ""
            frame.loc[mask, "parent_" + column] = frame.loc[mask, column]
        current = REVIEW / ("Supplement/FigS06." + ext)
        relative = current.relative_to(ROOT).as_posix()
        frame.loc[mask, ["source_file", "source_commit", "sha256", "current_source_file", "status"]] = [relative, "ARTWORK_COMMIT_PENDING", sha(current), relative, "AUTHOR_WORDING_UPDATE_NOT_PROMOTED"]
    frame.to_csv(manifest, index=False)
    record(manifest, before, "wording-edit hashes and original artwork lineage")
    # Source observations and previous pending changes are checked independently
    # by the calling audit before staging; this file never writes scientific data.
    (TEMP / "WORDING_CHANGES.json").write_text(json.dumps(CHANGES, indent=2))
    (TEMP / "PDF_TEXT_EDITS.json").write_text(json.dumps(PDF_EDITS, indent=2))
    print("WORDING_COMPLETE_NO_SCIENTIFIC_COMPUTATION", len(PDF_EDITS), flush=True)


if __name__ == "__main__":
    main()
