"""Create a source-bounded editorial package and a separate clean DOCX review copy."""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import zipfile
from copy import deepcopy
from pathlib import Path

import docx
import pandas as pd
import pypdfium2 as pdfium
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from lxml import etree
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, TextStringObject
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

BASE = "docs/data_research/built_environment_20261009"
PREVIEW = BASE + "/manuscript_integration_preview_20261010"
NAME = "manuscript_reconciliation_20261010"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def csv_write(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def body_paragraphs(path):
    text = path.read_text(encoding="utf-8").split("\n\n")
    return [p.replace("\n", " ") for p in text if p.startswith(("We ", "The ", "Land-", "Each ", "C1 ", "C2 ", "C3 ", "The four-"))]


def fix_map_legend(src, out):
    original = src / "FIG_STAGE7_TYPOLOGY_MAP.pdf"
    reader = PdfReader(original)
    page = reader.pages[0]
    stream = ContentStream(page["/Contents"], reader)
    replacements = 0
    # Remove the incorrect text operator, not a white-box redaction of scientific content.
    for operands, operator in stream.operations:
        if operator == b"TJ":
            txt = "".join(str(v) for v in operands[0] if isinstance(v, TextStringObject))
            if txt == "No residents (24 tracts)":
                for i, v in enumerate(operands[0]):
                    if isinstance(v, TextStringObject):
                        operands[0][i] = TextStringObject("")
                replacements += 1
    assert replacements == 1, "Expected exactly one map legend label"
    page[qn_pdf("/Contents")] = stream
    doc = pdfium.PdfDocument(str(original))
    tp = doc[0].get_textpage()
    start, count = tp.search("No residents (24 tracts)").get_next()
    boxes = [tp.get_charbox(i) for i in range(start, start + count)]
    # Arial is the frozen figure font. Keep existing text baseline and size.
    pdfmetrics.registerFont(TTFont("ReviewArial", r"C:\Windows\Fonts\arial.ttf"))
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(float(page.mediabox.width), float(page.mediabox.height)))
    c.setFont("ReviewArial", 7.5)
    new_label = "Outside cohort (24 tracts)"
    x0 = min(b[0] for b in boxes) - .6155
    assert x0 + pdfmetrics.stringWidth(new_label, "ReviewArial", 7.5) < float(page.mediabox.width) - 3
    c.drawString(x0, 346.8183, new_label)
    c.save()
    page.merge_page(PdfReader(buf).pages[0])
    writer = PdfWriter()
    writer.add_page(page)
    dest = out / "FIG_STAGE7_TYPOLOGY_MAP_REVIEW.pdf"
    with dest.open("wb") as f:
        writer.write(f)
    assert "No residents" not in PdfReader(dest).pages[0].extract_text()
    assert "Outside cohort" in PdfReader(dest).pages[0].extract_text()
    d = pdfium.PdfDocument(str(dest))
    d[0].render(scale=300 / 72).to_pil().save(out / "FIG_STAGE7_TYPOLOGY_MAP_REVIEW.png", dpi=(300, 300))
    dump(out / "FIGURE_LEGEND_CORRECTION.json", {"source": str(original), "source_sha256": sha(original),
         "review_sha256": sha(dest), "old": "No residents (24 tracts)", "new": "Outside cohort (24 tracts)",
         "text_operators_removed": replacements, "scope": "Only one legend text operator replaced; original vector paths, labels, palette and geometry retained; original preview untouched",
         "reason": "24 outside-cohort tracts contain 16,979 formal mapped residents; no eligibility or population was changed"})
    return dest


def qn_pdf(value):
    from pypdf.generic import NameObject
    return NameObject(value)


def source_audit(out, inventory):
    s = next(r for r in inventory if r["source_id"] == "S19")
    prose = """# Manuscript Source Audit

## Authority Decision

The authoritative current working manuscript is S19, LA_Grid_Manuscript_Resubmission_Rebuild.docx. The author explicitly confirmed this exact source in the current chat and authorized a separate review copy. The content is a complete manuscript, with abstract, six Methods subsections, four Results subsections, Discussion, Conclusions, declarations, bibliography, three tables and six figures. It describes the 92-station/318-edge formal model, M1/G1 source-gated event recovery, SOVI quartiles and paired policy comparisons. This is not the unrelated gusset-plate or heat-treatment paper.

Its bytes match Git commit 3466ba2's retained rebuild document. Git history records reconstruction on September 25, 2026 (9156f14, followed by 3466ba2). The July manuscript is its declared parent. File modification date was not used as authority. The DOCX's 2013 template metadata is not a manuscript creation date.

The legacy IJDRR submission DOCX is an earlier July scientific state and is not the current working manuscript. Newer September 29/October 4 documents are reviewer/manuscript plans rather than full replacements. The September 19 REVISED_MANUSCRIPT in older Git branches is a complete alternative, but the later reconstruction restores the July research questions and organization; the author's explicit confirmation resolves that ambiguity. No available project evidence establishes an approved final target journal. IJDRR/SEPS/RESS targeting documents are discussions or older submission evidence, not approval.

## Search Scope And Evidence

The inventory covers 41 plausible complete manuscripts, course reports, slides/storyboards, reviewer-response material, supplements, journal plans and unique historical Git documents. It searches the LA project deliverables, manuscript-rebuild directory, reviewer revision checkout, this project, LA-named Downloads documents, and historical refs 3466ba2, 63e8ace, b95ef8a, 84e7865, HEAD and 84d7ac6. It does not claim an exhaustive scan of every personal drive, cloud document, or unmounted device. No .bib/.ris/.enl reference-manager library was located in the scoped LA project/manuscript working directories. Full extracted paragraph/table locators are in source_extracts; hashes and document metadata are in MANUSCRIPT_SOURCE_INVENTORY.csv/JSON. Git provenance is in MANUSCRIPT_GIT_HISTORY.json.

## Important Differences

- S11/S13: July working versions include five-class interpretations, old PCA diagnostics, NRI risk/ACS age/density and cluster-specific hotspot recommendations. Their numbering and archetypes are not interchangeable with the later harmonized formal labels.
- S22: legacy submission package; same bytes as S17/S18/S20/S23. It is preserved and audited as legacy, not used to manufacture a current review draft.
- S24: June Downloads manuscript, earlier model and interpretation.
- S38-S41: September 19 historical full rewrites, with different framing and larger alternative text; Git dates and scientific state are recorded, not treated as current merely because they are repository artifacts.
- S19: September 25 complete reconstruction, shorter and organized around formal event-based recovery and quartile comparisons. Stage 7 survives in P0023/P0040/P0047 but still refers to old classes/transforms/hotspots. Independent network/recovery findings and GA prose require separate epoch reconciliation, not automatic changes in this task.
- S15: July supplement; duplicate Figure S6 identifiers and old SVI wording. Its current authority is unresolved. New supplementary material uses a temporary noncolliding S_STAGE7 identifier.
- S21/S26/S35-S37: reviewer/meeting/revision plans, not complete current manuscripts. Planned Fig07/FigS09 do not supersede actual S19 figures.
- S27: journal-targeting discussion, not confirmation of a journal decision.

## Exact Source Inventory

Rows below enumerate every plausible file/version. Identical-byte copies remain explicit. Dates are filesystem/document metadata or Git provenance, not authority by themselves.

"""
    prose += "Author-confirmed source path: `" + s["path"] + "`\n\nSHA-256: `" + s["sha256"] + "`\n\n"
    for r in inventory:
        meta = json.dumps(r.get("metadata", {}), ensure_ascii=True)
        prose += "### " + r["source_id"] + "\n\n"
        prose += "Path: `" + r["path"] + "`\n\nSHA-256: `" + r["sha256"] + "`\n\n"
        prose += "Title/content: " + r.get("title", "Not identified") + "\n\n"
        prose += "Metadata: `" + meta + "`. Filesystem mtime: `" + str(r.get("filesystem_mtime", "Git object")) + "`.\n\n"
        prose += "Content size: " + str(r.get("words", "unknown")) + " words; " + str(r.get("body_paragraphs", "NA")) + " body paragraphs; " + str(r.get("tables", "NA")) + " tables. Identical-byte sources: " + str(r.get("identical_byte_sources", [])) + ".\n\n"
    (out / "MANUSCRIPT_SOURCE_AUDIT.md").write_text(prose, encoding="utf-8")


def references(out, s):
    def old(key):
        return next((r["text"] for r in s["records"] if key in r["text"] and r["section"] == "References"), "No existing citation")
    rows = []
    def add(claim, existing, source, url, year, change, status, evidence, doi=""):
        rows.append(dict(claim_or_dataset=claim, existing_manuscript_citation=existing, verified_authoritative_source=source,
                         original_url=url, doi=doi, publication_or_release_year=year, required_bibliography_change=change,
                         verification_status=status, evidence_and_limitations=evidence, checked_date="2026-10-10"))
    fema = "https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf"
    add("NRI release / SOVI / risk / EAL / stock / ALR", old("National Risk Index"), "FEMA National Risk Index Technical Documentation v1.19.0, March 2023, archived by Ohio EMA", fema, "2023", "Specify March 2023 v1.19 and the archived technical documentation; retain generic dataset entry but do not present current documentation as this version", "VERIFIED_ARCHIVED_ORIGINAL", "PDF SHA 23f09170a909cd1cafcbbc61b3228ccd7bda3ed5714378bf7993d3fd25a48ab9; printed pp3-1/4-5 risk,4-6/4-7 EAL,5-9 stock,5-34..36 ALR; California table NRI_VER=Mar-23. Live dictionary access failed; national percentiles not reranked locally.")
    add("SCAG classified-land entropy", "No SCAG entry in S19", "SCAG 2019 Annual Land Use, ALU2019.1 service; updated February 2021", "https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0", "2019 data / February 2021 update", "Add SCAG corporate dataset citation, LU19 classification and processing archive", "VERIFIED_SERVICE_WITH_PORTAL_VERSION_CAVEAT", "Official service and archived JSON identify 2019.1. Portal metadata ea9fda878c1947d2afac5142fd5cb658 abstract says2019.1, purpose says2019.2; do not substitute. Entropy is project aggregation, not a precomputed SCAG field.")
    add("SCAG portal caveat", "No existing citation", "SCAG official item metadata", "https://www.arcgis.com/sharing/rest/content/items/ea9fda878c1947d2afac5142fd5cb658/info/metadata/metadata.xml?format=default&output=html", "Metadata 2022-02-09; data update February2021", "Record contradictory version text in supplement/provenance, not an invented unambiguous release", "VERIFIED_VERSION_TEXT_CONFLICT", "LU19 categories/source dictionary; no parcel gaps/unknown codes presumed complete; BF_SQFT is not the chosen LARIAC source.")
    add("Observed original 2014 all-use building age", "No LARIAC entry in S19", "County of Los Angeles / LARIAC4 Countywide Building Outlines, publication2014", "https://www.arcgis.com/sharing/rest/content/items/57f5fc977d6a427a978003a6229ab5e7/info/metadata/metadata.xml?format=default&output=html", "2014 publication; 2020-06-25 metadata", "Add corporate dataset citation and associated YearBuilt1/valid-age-area denominator; no claim of complete2020 ages", "VERIFIED_METADATA_AND_ARCHIVED_SCHEMA", "2008 stereo imagery updated2014; city-dependent historical capture64/400sqft. Associated assessor fields are archived at Countywide_Building_Outlines/FeatureServer/1; construction dates not equal acquisition or retrofit dates.")
    add("LARIAC6 physical roof coverage", "No LARIAC entry in S19", "County of Los Angeles LARIAC6_BUILDINGS_2020 layer0", "https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0", "2020 dataset label; mixed acquisition dates", "Add exact layer and archived extraction hashes; do not call all outlines 2020 acquisition", "VERIFIED_LAYER_AND_ARCHIVED_SOURCE", "Official polygon layer and DATE_/SOURCE schema verified; live service edited2026, so frozen cache is authority. Roof fraction is project union/land aggregation, not floors or seismic capacity.")
    for table in ["B25024", "B25034"]:
        add("ACS2022 five-year " + table + " descriptive fields", old("American Community Survey"), "U.S. Census Bureau ACS2022 ACS5 variable definitions", "https://api.census.gov/data/2022/acs/acs5/groups/" + table + ".html", "2022 five-year vintage", "Specify actual table/vintage instead of generic API; these are not primary D inputs", "VERIFIED_OFFICIAL_FIELDS", "Estimates E and margins M with total001. B25024 five-plus numerator006..009; B25034 pre1970 numerator008..011. Do not confuse housing-unit age with all-use2014 roof-area age; no new retrieval or clustering.")
    add("2020 tract/land-water geography", old("TIGER/Line"), "U.S. Census Bureau TIGER/Line2020", "https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_06_tract.zip", "2020", "Specify archived tract/water products and exact GEOIDs in data statement", "VERIFIED_ARCHIVED_SOURCE_IDENTITY", "Exact study polygons/land masks are already hashed in preview source manifest; geometry failures retained unclassified, no new GIS extraction.")
    add("K-means foundational method", old("MacQueen"), "MacQueen J., Proceedings Fifth Berkeley Symposium VolI, pp281-297; UC Berkeley Library / Project Euclid", "https://digicoll.lib.berkeley.edu/record/113015?v=pdf", "1967 proceedings; conference1965/1966", "Retain existing1967 entry; distinguish conference dates in library metadata from proceedings year; no DOI invented", "VERIFIED_ARCHIVE_TITLE_PAGES", "Original university archive title/creator/pages and symposium volume identified; Project Euclid landing requires iframe. No new primary fit.")
    add("Lloyd iterative algorithm", old("Lloyd"), "IEEE Transactions on Information Theory article1056489", "https://ieeexplore.ieee.org/document/1056489", "1982", "Retain existing bibliographic entry; publisher full metadata access requires robot check", "PARTIAL_PUBLISHER_ACCESS_BLOCKED", "Existing DOI/title/pages preserved; not falsely described as a new full-text verification", "10.1109/TIT.1982.1056489")
    add("Legacy elbow reference", old("Thorndike"), "Robert L. Thorndike, Who belongs in the family?, Psychometrika18:267-276", "https://link.springer.com/article/10.1007/BF02289263", "1953", "Retain bibliography; remove implication current k4 is an automatic elbow optimum", "VERIFIED_PUBLISHER_METADATA", "Publisher title/author/year/pages and DOI verified; not independent support for this scientific partition", "10.1007/BF02289263")
    add("Adjusted Rand partition agreement", "No Hubert-Arabie entry in S19", "Hubert L. and Arabie P., Comparing partitions, Journal of Classification2:193-218", "https://link.springer.com/article/10.1007/BF01908075", "1985", "Add verified ARI citation", "VERIFIED_PUBLISHER_METADATA", "Chance-adjusted partition agreement, not accuracy against observed truth", "10.1007/BF01908075")
    add("Silhouette diagnostic, if legacy diagnostics retained", "No Rousseeuw entry in S19", "Rousseeuw P.J., Silhouettes, Journal of Computational and Applied Mathematics20:53-65", "https://www.sciencedirect.com/science/article/pii/0377042787901257", "1987", "Supplementary-only reference if silhouette discussed; do not claim new score or primary selection", "VERIFIED_PUBLISHER_METADATA", "Publisher title/year/pages and DOI verified; no new silhouette computation", "10.1016/0377-0427(87)90125-7")
    add("LA electric restoration framework", old("Post-earthquake restoration planning"), "Cagnan, Davidson and Guikema, Earthquake Spectra22(3):589-608", "https://journals.sagepub.com/doi/10.1193/1.2222400", "2006", "Retain verified reference; modeled study results do not validate our proxy against actual outages", "VERIFIED_PUBLISHER_METADATA_ABSTRACT", "Publisher authors/title/year/pages and discrete-event scope verified; no claim of feeder-level or MW calibration", "10.1193/1.2222400")
    add("LA task scheduling literature", old("Optimizing scheduling"), "Xu et al., Earthquake Engineering and Structural Dynamics36(2):265-284", "https://onlinelibrary.wiley.com/doi/abs/10.1002/eqe.623", "2007 issue / 2006 online publication", "Correct source bibliography issue36(3) to publisher-verified36(2); keep2007 issue year", "VERIFIED_PUBLISHER_METADATA_ABSTRACT", "Publisher confirms authors/issue/pages and DOI; original stochastic task problem is not evidence that this GA improved its own formal incumbent", "10.1002/eqe.623")
    add("Current electricity-service equations / frozen recovery", "S19 Sections2.2-2.4", "Protected031d2c model and preview source hashes / original manuscript", "https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/tree/031d2c675f8e7d58035d27448be040b809ced086", "September2026 protected baseline / October2026 reconciliation", "Use exact commit/data statement; distinguish internal reproducibility from external validation", "VERIFIED_PROJECT_PROVENANCE_NOT_EXTERNAL_VALIDATION", "No changes to gate/evaluator/mapping/scheduler/physical samples; current source GA assertions retained but epoch conflicts flagged for separate author review")
    csv_write(out / "REFERENCE_VERIFICATION.csv", rows)
    return rows


def create_docx(out, src, s):
    source = Path(s["path"])
    d = docx.Document(str(source))
    original_paragraphs = list(d.paragraphs)
    original_tables = list(d.tables)
    ledger = []

    def edit(n, text, reason):
        p = original_paragraphs[n - 1]
        before = p.text
        props = deepcopy(p._p.pPr)
        for child in list(p._p):
            if child.tag != qn("w:pPr"):
                p._p.remove(child)
        p.add_run(text)
        ledger.append({"source_location": "S19 P" + str(n).zfill(4), "action": "REVISE", "before": before, "after": text, "reason": reason})
        return p

    def after(anchor, text):
        element = OxmlElement("w:p")
        element.append(deepcopy(original_paragraphs[22]._p.pPr)) if original_paragraphs[22]._p.pPr is not None else None
        anchor._p.addnext(element)
        p = docx.text.paragraph.Paragraph(element, anchor._parent)
        p.add_run(text)
        ledger.append({"source_location": "After " + anchor.text[:50], "action": "INSERT", "before": "", "after": text, "reason": "Frozen Stage7 integration"})
        return p

    edit(2, "Resubmission reconstruction from the retained July 23, 2026 manuscript. Coauthor review copy with Stage 7 integration dated October 10, 2026. Unaffected network and restoration findings retain their frozen September 2026 scope; the descriptive four-class candidate is supplied for author review, not formal promotion.", "Qualify new Stage7 dates; retain independent scientific baseline")
    edit(9, original_paragraphs[8].text.replace("built-environment exposure, risk,", "built form, economic stock, multi-hazard expected loss,"), "Make the third question's Stage7 measurement terminology precise")
    methods = body_paragraphs(out / "REVISED_STAGE7_METHODS.md")
    assert len(methods) == 6
    prefix = original_paragraphs[22].text.split("The retained Stage 7 PCA/K-means")[0]
    p = edit(23, prefix.rstrip(), "Preserve independent quartile/paired estimands; replace only obsolete Stage7 tail")
    for para in methods:
        p = after(p, para)
    results = body_paragraphs(out / "REVISED_STAGE7_RESULTS.md")
    assert len(results) == 5
    before40 = original_paragraphs[39].text
    marker = "The retained five"
    cut = before40.find(marker)
    if cut < 0:
        cut = before40.find("The five")
    if cut < 0:
        # The exact retained old Stage7 sentence is located by its five-cluster token.
        sentences = re.split(r"(?<=\.)\s+", before40)
        prefix40 = " ".join(sentences[:4])
    else:
        prefix40 = before40[:cut].rstrip()
    p = edit(40, prefix40, "Keep independent Q4 resource contrasts; withdraw old five-class/transform/hotspot result")
    for para in results:
        p = after(p, para)
    table_caption = after(p, "Table 4. Frozen four-class original-unit profiles. Panel A reports equal-tract recovery means and mapped population totals. Panel B reports physical/social means and economic/loss-rate medians; stock is million 2022 USD. Fractions use the separate denominators in Methods. These summaries are not intervention priorities.")
    table_caption.paragraph_format.page_break_before = True
    table_caption.paragraph_format.keep_with_next = True
    profiles = pd.read_csv(src / "STAGE7_CLUSTER_PROFILES.csv").set_index("candidate_cluster")
    for panel, headers, fields in [
        ("A", ["Class", "Tracts", "Mapped population", "B mean (h)", "T80 mean (h)", "Initial mean (%)"],
         ["n_tracts", "population_sum", "B_480_hr_mean", "T80_mean", "Init_Supply_mean"]),
        ("B", ["Class", "SOVI mean", "Entropy mean", "Roof fraction mean", "Pre-1970 fraction mean", "Stock median", "ALR median"],
         ["SOVI_SCORE_mean", "land_use_entropy_mean", "building_footprint_coverage_mean", "all_use2014_pre1970_area_share_mean", "NRI_BUILDVALUE_median", "ALR_NPCTL_median"])
    ]:
        label = after(table_caption, "Panel " + panel)
        label.paragraph_format.keep_with_next = True
        t = d.add_table(rows=1, cols=len(headers))
        t.style = original_tables[0].style
        t.autofit = False
        for col in t.columns:
            col.width = Inches(6.8 / len(headers))
        for cell, h in zip(t.rows[0].cells, headers):
            cell.text = h
        header_repeat = OxmlElement("w:tblHeader")
        t.rows[0]._tr.get_or_add_trPr().append(header_repeat)
        for c in ["C1", "C2", "C3", "C4"]:
            cells = t.add_row().cells
            cells[0].text = c
            for cell, field in zip(cells[1:], fields):
                v = profiles.loc[c, field]
                if field in ["n_tracts", "population_sum"]:
                    cell.text = format(int(v), ",")
                elif field == "Init_Supply_mean":
                    cell.text = format(v * 100, ".5f")
                elif field == "NRI_BUILDVALUE_median":
                    cell.text = format(v / 1e6, ".1f")
                elif "fraction" in field or "coverage" in field or "entropy" in field or "area_share" in field:
                    cell.text = format(v, ".3f")
                else:
                    cell.text = format(v, ".2f")
        for row in t.rows:
            no_split = OxmlElement("w:cantSplit")
            row._tr.get_or_add_trPr().append(no_split)
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.space_after = Pt(3)
                    for run in para.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(8.5)
        label._p.addnext(t._tbl)
        element = OxmlElement("w:p")
        t._tbl.addnext(element)
        table_caption = docx.text.paragraph.Paragraph(element, label._parent)
    discussion = body_paragraphs(out / "REVISED_STAGE7_DISCUSSION.md")
    assert len(discussion) == 3
    p = edit(47, original_paragraphs[46].text.replace("Cluster and hotspot outputs are descriptive screening.", "The four-class typology is descriptive; the old hotspot conclusions require separate revalidation."), "Retain calibration/repair/Q4 limitations; qualify only Stage7 screening")
    for para in discussion:
        p = after(p, para)
    after(original_paragraphs[57], "The Stage 7 review candidate is traceable to the frozen October 10 integration preview (84d7ac6410a00c83ec01913674f0167ad07551be), feature validation (50df10481815f3dd94c46dc9443f93cfdb1c5014), spatial validation (ecf98c6cbda280914962582a819943fabfa41132), and FEMA version audit (65f388f9710566ffa845808bd7b10503de4da608). Saved GEOID membership, original-unit profiles, source payload hashes and transformation/domain-weight definitions are retained without new simulation or clustering; source geometry failures remain unclassified.")
    additions = [
        "Federal Emergency Management Agency. (2023). National Risk Index Technical Documentation (Version 1.19.0, March 2023). Archived original publication: https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf",
        "Hubert, L., & Arabie, P. (1985). Comparing partitions. Journal of Classification, 2, 193-218. https://doi.org/10.1007/BF01908075",
        "Los Angeles County. (2014). Countywide Building Outlines (LARIAC4_BUILDINGS_2014), associated assessor attributes. https://www.arcgis.com/sharing/rest/content/items/57f5fc977d6a427a978003a6229ab5e7/info/metadata/metadata.xml?format=default&output=html",
        "Los Angeles County. (2020). Countywide Building Outlines (LARIAC6_BUILDINGS_2020, layer 0; mixed acquisition dates). https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0",
        "Southern California Association of Governments (SCAG). (2021). 2019 Annual Land Use (archived ALU 2019.1 service, updated February 2021). https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0"
    ]
    # Keep every pre-existing reference paragraph in order; insert additions at their alphabetical positions.
    after(original_paragraphs[71], additions[0])
    after(original_paragraphs[74], additions[1])
    anchor = original_paragraphs[84]
    anchor = after(anchor, additions[2])
    after(anchor, additions[3])
    after(original_paragraphs[91], additions[4])
    edit(100, original_paragraphs[99].text.replace("36(3)", "36(2)"), "Correct publisher-verified issue number for the existing Xu2007 framework citation")
    captions = (src / "FIGURE_CAPTIONS.md").read_text().split("\n\n")
    cap_a = next(p for p in captions if p.startswith("Four-class joint"))
    cap_b = next(p for p in captions if p.startswith("Tract-unweighted"))
    for number, image, caption in [(7, out / "FIG_STAGE7_TYPOLOGY_MAP_REVIEW.png", cap_a),
                                    (8, src / "FIG_STAGE7_CLUSTER_PROFILE.png", cap_b)]:
        p = d.add_paragraph()
        p.paragraph_format.page_break_before = True
        p.add_run().add_picture(str(image), width=Inches(6.8))
        c = d.add_paragraph("Figure " + str(number) + ". " + caption)
        c.paragraph_format.keep_with_next = False
        ledger.append({"source_location": "After original Figure6", "action": "INSERT", "before": "", "after": c.text,
                       "reason": "New Stage7 figure only; original Figure1-6 identifiers/media preserved"})
    for p in d.paragraphs:
        if p.text.startswith("Figure 7.") or p.text.startswith("Figure 8."):
            p.paragraph_format.space_before = Pt(3)
    temporary = io.BytesIO()
    d.save(temporary)
    review = out / "Manuscript_Stage7_Integration_REVIEW.docx"
    # Preserve the original package byte-for-byte except the parts needed for added text/images.
    modified_parts = {"word/document.xml", "word/_rels/document.xml.rels", "[Content_Types].xml"}
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(temporary) as new, zipfile.ZipFile(review, "w", zipfile.ZIP_DEFLATED) as z:
        for name in old.namelist():
            z.writestr(name, new.read(name) if name in modified_parts else old.read(name))
        for name in new.namelist():
            if name not in old.namelist():
                z.writestr(name, new.read(name))
    qa = {"source_sha256": sha(source), "review_sha256": sha(review), "tracked_changes": False,
          "original_tables_preserved": [], "original_paragraphs_preserved": [], "unchanged_package_parts": [], "edited_source_paragraphs": [2, 9, 23, 40, 47, 100],
          "source_abstract_conclusions_unchanged": True, "new_figures": [7, 8], "new_table": "4, panels A/B", "actual_rendering": "PENDING"}
    revised = docx.Document(str(review))
    canonical = lambda el: etree.tostring(el, method="c14n")
    revised_nodes = [canonical(p._p) for p in revised.paragraphs]
    for i, p in enumerate(original_paragraphs, 1):
        if i not in qa["edited_source_paragraphs"]:
            assert canonical(p._p) in revised_nodes, "Lost original paragraph " + str(i)
            qa["original_paragraphs_preserved"].append(i)
    for i, t in enumerate(original_tables, 1):
        assert canonical(t._tbl) in [canonical(x._tbl) for x in revised.tables]
        qa["original_tables_preserved"].append(i)
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(review) as new:
        for name in old.namelist():
            if name not in modified_parts:
                assert old.read(name) == new.read(name), name
                qa["unchanged_package_parts"].append(name)
    assert all(not p.text.startswith("Figure 9.") for p in revised.paragraphs)
    dump(out / "DOCUMENT_STRUCTURE_QA.json", qa)
    csv_write(out / "MANUSCRIPT_PARAGRAPH_CHANGE_LEDGER.csv", ledger)
    content = "# Manuscript Revision Changelog\n\nAuthor-confirmed S19 source; clean independent copy, not tracked changes. Original abstract, conclusions, 108 unaffected source paragraphs, all three original tables, style definitions, metadata, headers/footers and six original figure payloads are preserved. No silent reference/figure renumbering. Original page flow can change because of inserted text; actual rendering must be reviewed. One existing framework reference issue number is corrected using publisher metadata.\n\n"
    for row in ledger:
        content += "## " + row["source_location"] + "\n\nAction: " + row["action"] + ". " + row["reason"] + "\n\nBefore:\n\n" + (row["before"] or "[No existing paragraph]") + "\n\nAfter:\n\n" + row["after"] + "\n\n"
    content += "## Unchanged Findings Requiring Separate Author Review\n\nS19 P0004/P0021/P0043/P0049 report a September GA search that retained Impact-first. Later October optimization research uses different search budgets and contains better diagnostic candidates. These statements are retained, not silently reconciled by replacing a formal sequence. The author must explicitly scope experimental epochs or authorize a separate GA/manuscript update before submission. Older supplementary SVI/source-gate results and duplicate S6 numbers are also outside this Stage7 edit.\n"
    (out / "MANUSCRIPT_REVISION_CHANGELOG.md").write_text(content, encoding="utf-8")
    return ledger


def claims(out, inventory, ledger):
    rows = []
    changed = {r["source_location"]: r for r in ledger if r["source_location"].startswith("S19 P")}
    patterns = re.compile(r"cluster|typolog|hotspot|PCA|K.means|NRI_RISK|BUILDVALUE|built.environment|building.age|pre.1970|population density|land.use", re.I)
    reviewed = ["S19", "S11", "S13", "S15", "S22", "S24", "S38", "S40", "S21", "S27", "S35", "S37"]
    for s in inventory:
        if s["source_id"] not in reviewed:
            continue
        for r in s["records"]:
            text = r["text"]
            n = r["location"].split(" / ")[0]
            key = s["source_id"] + " " + n
            if not patterns.search(text) and key not in changed and not (s["source_id"] == "S19" and n in ["P0004", "P0021", "P0043", "P0049", "P0058"]):
                continue
            action, valid, priority = "VERIFY", "Version-specific support required", "MEDIUM"
            replacement = "Retain only source-supported descriptive language; use frozen five-domain definitions, not old archetypes."
            evidence = PREVIEW + "/STAGE7_CANDIDATE_FREEZE.json"
            dependency = "NO_NEW_PRIORITY_INFERENCE"
            if key in changed:
                action, valid, priority = "REVISE", "Old Stage7 tail superseded in clean review copy; unaffected clauses retained", "HIGH"
                replacement = changed[key]["after"] + " [Inserted paragraphs: MANUSCRIPT_PARAGRAPH_CHANGE_LEDGER.csv]"
            elif s["source_id"] == "S19" and n in ["P0004", "P0021", "P0043", "P0049"]:
                action, valid, priority = "VERIFY", "Stage7-independent; GA experimental epoch requires separate reconciliation", "HIGH"
                replacement = "Keep unchanged for this Stage7 task; reconcile September formal versus October diagnostic search explicitly before submission."
                evidence = "S19 / frozen031d2c scientific scope / later GA diagnostic records; no formal candidate replacement"
            elif "hotspot" in text.lower():
                action, valid, priority = "REMOVE", "Not transferred to four-class typology", "HIGH"
                replacement = "Withdraw old top10-by-cluster, hotspot-centrality overlap and allocation inference unless separately revalidated against the original score definition."
                evidence = PREVIEW + "/STAGE7_OLD_NEW_CROSSWALK.csv; HOTSPOT_AND_INTERVENTION_DEPENDENCY_AUDIT.md"
                dependency = "REQUIRES_SEPARATE_HOTSPOT_REVALIDATION"
            elif re.search(r"five.cluster|five communities|five distinct|cluster [1-5]|clusters [1-5]|PCA|K.means", text, re.I) and r["section"] != "References":
                action, valid, priority = "REPLACE", "Not valid for saved D/seed42/k4 partition", "HIGH"
                replacement = "Use revised Methods/Results and exact C1-C4 counts/profiles. No primary PCA; no direct archetype/name/color transfer."
                evidence = PREVIEW + "/STAGE7_CLUSTER_PROFILES.csv; STAGE7_OLD_NEW_CROSSWALK.csv; STAGE7_CANDIDATE_FREEZE.json"
            elif r["section"] == "References":
                action, valid = "VERIFY", "Bibliographic entry, not a scientific class claim"
                replacement = "Compare REFERENCE_VERIFICATION.csv; retain unrelated references."
            elif s["source_id"] == "S19":
                action, valid = "KEEP", "Independent recovery/framework statement; no old numerical class dependency"
                replacement = "Retain unchanged; community co-occurrence is descriptive."
            if s["source_id"] in ["S21", "S27", "S35", "S37"]:
                valid = "Planning document, not authoritative manuscript text; " + valid
            rows.append(dict(source_id=s["source_id"], source_manuscript=s["path"], source_sha256=s["sha256"],
                             section=r["section"], exact_location=r["location"], current_claim=text, supporting_evidence=evidence,
                             validity=valid, required_action=action, proposed_replacement=replacement, exact_numerical_source=evidence,
                             priority=priority, hotspot_dependency=dependency))
    # Explicitly preserve every actual source figure and original table, independent of keyword matching.
    s = next(x for x in inventory if x["source_id"] == "S19")
    for r in s["records"]:
        if re.match(r"Figure [1-6]\.", r["text"]):
            rows.append(dict(source_id="S19", source_manuscript=s["path"], source_sha256=s["sha256"], section=r["section"],
                             exact_location=r["location"], current_claim=r["text"], supporting_evidence="Original S19 formal artwork, preserved bytes",
                             validity="Independent of Stage7 membership; formal simulation audit outside this edit", required_action="KEEP",
                             proposed_replacement="No figure/caption/identifier change", exact_numerical_source="Original source manuscript and protected formal outputs",
                             priority="LOW", hotspot_dependency="NONE"))
    csv_write(out / "MANUSCRIPT_CLAIM_RECONCILIATION.csv", rows)
    dump(out / "CLAIM_AUDIT_COUNTS.json", {"rows": len(rows), "source_versions_audited": reviewed,
         "scope": "Every matching visible paragraph/table-cell claim in distinct scientific manuscript states and relevant plans; exact before/after edits in separate ledger",
         "actions": {k: sum(r["required_action"] == k for r in rows) for k in ["KEEP", "REVISE", "REPLACE", "REMOVE", "VERIFY"]},
         "duplicate_versions": "All41 paths/hashes inventoried; identical-byte copies inherit the unique version disposition, not independent evidence"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    a = ap.parse_args()
    repo = a.repo.resolve()
    if os.name == "nt":
        repo = Path("\\\\?\\" + str(repo))
    out = repo / BASE / NAME
    src = repo / PREVIEW
    inventory = json.loads((out / "MANUSCRIPT_SOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    s = next(x for x in inventory if x["source_id"] == "S19")
    assert s["sha256"] == "a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253"
    assert sha(Path(s["path"])) == s["sha256"]
    source_audit(out, inventory)
    references(out, s)
    fix_map_legend(src, out)
    ledger = create_docx(out, src, s)
    claims(out, inventory, ledger)
    dump(out / "AUTHOR_SOURCE_CONFIRMATION.json", {"source_id": "S19", "source_path": s["path"], "source_sha256": s["sha256"],
         "direct_user_answer": "Yes, use this source to generate a separate review copy (Chinese confirmation in this chat)",
         "scope": "Source authority and separate review copy only; no formal Stage7/GA promotion or journal approval", "date": "2026-10-10"})
    print("Created clean review DOCX and editorial inventory; actual rendering still required.")


if __name__ == "__main__":
    main()
