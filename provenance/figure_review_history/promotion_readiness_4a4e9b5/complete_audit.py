"""Assemble a read-only, native-size review packet after actual image inspection.

No plotting/scientific module is imported or executed. Source PDFs are embedded
unchanged; only review pages and audit records are created in this directory.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import subprocess

import fitz
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
MM = 72 / 25.4
BASELINE = "4a4e9b5fc026cfb86cfcbc25a11268db0fe1bb4d"
READY = "READY_FOR_AUTHOR_PROMOTION"
FIX = "NEEDS_PRESENTATION_FIX"
OLD = "SUPERSEDED — DO NOT USE"

# These are observations from fresh native/page renders viewed in this turn,
# not decisions copied from an earlier verification report.
DECISIONS = {
    "Fig01": (FIX,
        "Exact July chain preserved, but 4.9-pt normal text is unreadable at native size. No cropping; adequate page height.",
        "Restoration of July artwork is not explicit acceptance of a small-font submission exception. Original diagram does not explicitly depict every accepted revision addition.",
        "Author must explicitly accept the lettering exception or authorize a separate presentation-only re-layout candidate. Do not redraw or promote automatically."),
    "Fig02": (READY,
        "174-mm balanced 2x2; A/B geographic content retained. C eligibility pools and D value labels readable. No legend or point/value collision.",
        "337 comparable tracts; any/top-1/top-3 public-site agreement, not accuracy. 342 is a different earlier set (316 shared; 26 old-only; 21 current-only). C is eligibility context, not verified utility territory.",
        "Use this candidate rather than the 293-mm old stack. Align S06 mapping colors to this reference identity before promoting the complete set."),
    "Fig03": (FIX,
        "216-mm artwork fits native A4 body with caption on a following page. T80 map is large enough; four-stage hierarchy is readable. Hazard colors/lines distinguishable here, but conflict with S01/S02.",
        "Baseline decomposition is Unconstrained, not Hospital-first. Map source is mean of realization-specific tract T80 conditional on that tract reaching T80 in each realization, not T80 of the mean curve. Current caption 'among reached tracts' is imprecise. A uses station 5th-95th whiskers, not realization uncertainty.",
        "Clarify the map estimand and station-box whiskers in the caption; unify S01/S02 hazard identity. Do not alter data, map size, or 216-mm layout merely because it is tall."),
    "Fig04": (READY,
        "Improved secondary-policy lines are visible without dominating the four core comparators. All eight scheduled policies plus black Unconstrained are visible. 205-mm height and outcome labels readable; legend outside data.",
        "Current caption correctly separates 0-100-h display from 0-480-h integration. Mean dots with 5th-95th realization ranges, not CIs. Hospital-linked metric is a tract proxy, not clinical delivery. Source-path component adds mechanism beyond aggregate outcomes.",
        "Use the latest readable candidate. Retain complete outcome distributions in supporting results; no ninth Direct-community policy."),
    "Fig05": (FIX,
        "Quartile dodge now separates intervals; C/D axes have readable real scales; map remains readable at 218 mm. Top nine-policy legend can imply A contains nine policies although A contains four. C/D references all use circles; Fig06 uses Hospital gray circle and Impact orange square.",
        "C/D references are named, but Degree-first must be described as additional reference sensitivity, not a predeclared primary reference. E is mean tract paired effect, not significance or per-realization helped population. Gini is unitless and separate from group separation.",
        "Make A/B legend applicability explicit and share C/D reference shapes with Fig06. Clarify Degree-first reference status in caption. Keep all numerical positions and interval definitions."),
    "Fig06": (READY,
        "185x166 mm; native 7.5-pt minimum. Hospital gray circles / Impact orange squares clear. Shared hour scale preserves large C29 separation; high-crew near-zero effects compress but direction and broad relative magnitude remain visible. Duration row remains legible.",
        "Two separate OFAT families, not a calibrated continuous capacity variable. Whiskers are saved 95% bootstrap CIs of mean matched contrasts, not realization ranges. Approved finding is generally diminishing leverage, not strict monotonicity. Absolute separation is group disparity, not Gini.",
        "No further iteration requested. Keep common main scales. S16 is an optional near-zero review aid only; it cannot replace this main scale."),
    "Fig07": (READY,
        "229-mm reflow preserves native map size and 7.5-pt minimum. Cluster legend stays below its map; top-10 outlines readable. Six profile curves plus heatmap remain dense but readable. FigS09 cluster-ID colors match.",
        "2,291 eligible residential typology members versus 2,315 full-domain tracts; 24 N/A tracts hatched, not assigned zero. Six displayed descriptive features are not all eleven clustering inputs. Hotspot score is descriptive screening, not repair/intervention priority.",
        "Requires a near-full-page body allocation; caption belongs separately or on adjoining text page. Preserve cluster-ID palette and top-10 outlines."),
    "FigS01": (FIX,
        "Station points/boxes readable, but older hazard colors and labels conflict with Fig03. Northridge/San Fernando/Long Beach/2% in 50 yrs order differs. No overlap.",
        "The saved renderer feeds formal 92-station mean DS tables into July plotting. Default box whiskers are 1.5 IQR plus all station points, unlike Fig03's 5th-95th station range. Registered note is too short to define this.",
        "Unify hazard palette/names and write the box/point interpretation. Do not treat station heterogeneity as MC uncertainty or interpret hazard contrast as pure PGA sensitivity."),
    "FigS02": (FIX,
        "All four service maps use consistent extent and 0-1 scale and are readable at 202 mm. Old scenario palette conflicts with Fig03; all-solid ECDF and 2pc50 curve on the axis are less distinguishable. Composite panel hierarchy is not explicit.",
        "'Supply' can imply delivered electricity; use modeled tract service availability. Caption must define per-tract mean over saved realizations, the common mapping, and scenario parameterization limits.",
        "Unify palette/line identity, reader-facing service wording and panel letters. Keep map values/extent/scale unchanged."),
    "FigS03": (FIX,
        "Crew locations and travel matrix legible; old Retained station wording is removed. 229-mm stack uses noticeably larger type than main figures (minimum 9.95 pt); no consistent A/B lettering.",
        "These are 57-crew origins and directed task travel inputs, not evidence of resource-response outcomes. Caption now says this correctly.",
        "Align title hierarchy and A/B panel labels. A full supplementary page is feasible, but avoid treating this input figure as Fig06's response evidence."),
    "FigS04": (FIX,
        "244-mm four-section stack is long but fits an A4 body when caption is separate. Global panel lettering inconsistent; stacked source panels reuse local A/B. Dynamic policy styles differ from Fig04; some pale thin lines compete poorly.",
        "Static 'Impact' attack label is lambda2 network impact, not population-oriented Impact-first. Static percolation is not optimal repair ordering. Current caption note omits interval, model, horizon and dynamic contrast definitions.",
        "Coordinate global panel lettering, explain lambda2 attack identity, synchronize policy styles, and supply a complete caption. Resolve page allocation before promotion; do not shrink whole stack."),
    "FigS05": (READY,
        "Five generation-mean search curves actually vary and are legible; Impact-first incumbent reference and planning objective comparison readable at 155 mm. No legend overlap.",
        "64 independent planning realizations, five seeds; generation means are search diagnostics, not evaluation uncertainty. No seed beats retained incumbent; identical retained sequence is Impact-first. Finite search does not prove global optimality.",
        "Retain this GA evidence candidate. It is not an extra scheduled policy and does not restore the withdrawn old figure number automatically."),
    "FigS06": (FIX,
        "115-mm 2x2 and Selected Cutoff 3% readable. Public-site point values spaced clearly, but baseline/revised colors and shapes differ from Fig02 D. Metric wording and hazard label spacing inconsistent.",
        "Same 337 comparable tracts: baseline 320/296/317 and utility-compatible 329/302/324 for any/top-1/top-3. Top-1/top-3 rank retained positive candidates by weight, not necessarily nearest geographic sites. 246 >1-h shifts are mapping sensitivity, not policy-benefit categories.",
        "Use the same mapping identity as Fig02; correct 'Nearest site' shorthand to ranked candidate definitions; expand the caption with denominators/filter rules and integration horizon."),
    "FigS07": (FIX,
        "191-mm dynamic-plus-map composite has legible source triangles and station labels. Dynamic alternate-route curves use policy line styles inconsistent with Fig04. Static low-probability pale map is an honest scale, not a reason to brighten numerical values.",
        "Registered caption is only a short note. Must distinguish dynamic joint source-connected mass from static conditional target-functional reliability; fixed path is precomputed before recovery, not reoptimized each time. No delivered-MW interpretation.",
        "Supply full caption and align policy styles where linestyle is not already reserved for full versus fixed paths. Keep all source probabilities and common map scales."),
    "FigS08": (FIX,
        "194.8-mm chart preserves 34 facilities and readable voltage-class markers. OLINDA 109.04% and 100% planning line clear. Expanded-scale capacity increments have explicit ticks and numbers. Missing global A/B letters.",
        "34 voltage-facility planning rows across 28 stations are different from the 19 one-to-one bound-supported stations (9 multi-facility excluded; 73 unsupported). Current short caption does not state both domains or 2026 planning vintage. Not post-earthquake load flow/full-network adequacy.",
        "Add A/B letters and complete domain/unit/vintage caption: 19/92, 932/2315 and 25.34% dependency support. Preserve planning-vs-earthquake distinction and expanded point scale."),
    "FigS09": (READY,
        "174-mm four panels with increased scatter opacity and separate cluster legend readable. Category colors match Fig07 by cluster ID. Loading heatmap has a distinguishable diverging scale; map category palette need not apply to numerical loadings.",
        "2,291 eligible typology tracts; PCA/loadings/inertia/silhouette are descriptive method support, not external validation or intervention ranking. Caption states accepted transformed/standardized space.",
        "Use this latest visibility version with Fig07's palette; do not substitute earlier scatter colors."),
    "FigS10": (FIX,
        "Hospital-priority map/boxplot readable at 105 mm. Numbered circles are substation repair ranks, not hospital IDs. Legend clear. B repeats one outcome also summarized in Fig04, justified here only as definition-to-outcome support.",
        "Current plot_box uses default 1.5-IQR whiskers and displays fliers, not Fig04's 5th-95th ranges. Short caption does not explain this. 'Cumulative burden' and 'Hospital-linked burden' should specify modeled tract service loss, not hospital electrical/clinical output.",
        "Clarify caption whiskers and metric names. Do not claim statistical-display uniformity until this is explicitly explained. Keep map as supplementary policy-definition evidence."),
    "FigS11": (FIX,
        "All eight policies x four hazards present in four readable heatmaps. Black text on darkest red Random cells has poor native contrast (e.g. large +8 to +9-h cells). Separate hour colorbars are explicit.",
        "Within-hazard mean matched contrasts use Unconstrained reference; no intervals drawn despite source ranges being available. Different historical/2pc50 fragilities preclude pure-intensity claims. Specify C57_D1 in caption.",
        "Use contrast-aware annotation lettering and state the resource case. Do not change values or reinterpret positive scheduled losses as universal priority rankings."),
    "FigS12": (READY,
        "180-mm four-panel absolute crew outcomes readable; 29/57/86/114 categories discrete. High-resource convergence and pale Random points are visible, though small differences cannot be resolved as finely as in matched contrasts.",
        "All eight scheduled policies; means and 5th-95th realization ranges, not CIs. No continuous curve or crew-duration interaction. Absolute outcomes complement Fig06 contrasts rather than duplicate the same estimand.",
        "Retain complete crew evidence. No implication of interpolated levels; near-zero comparisons may use S16 separately."),
    "FigS13": (READY,
        "180-mm four-panel duration outcomes readable with the same policy identity as S12. All four duration multipliers present; legends outside data.",
        "C57 with tested 0.75/1/1.25/1.50 multipliers; means and 5th-95th realization ranges. Separate OFAT family, not factorial sensitivity. No untested multipliers.",
        "Retain full duration outcomes with current caption; do not label this a calibrated continuous response."),
    "FigS14": (FIX,
        "Native gate/threshold bars readable and start at zero, but internal G0/G2/G3/G4 wording and generic burden labels remain. No registered caption. Local-only source is not in the requested pushed baseline.",
        "Single Hospital-first/2pc50 gate-threshold context, not all-policy robustness. Dataset provenance must be explicitly registered before promotion; merely existing locally is insufficient.",
        "Resolve executable/result authority, reader-facing configuration names, integration horizon and caption. Include for completeness of review only, not as verified pushed submission artwork."),
    "FigS15": (FIX,
        "Log-log full-versus-fixed scatter and top-gain dots readable overall, but log exponents reach 5.25 pt, below the 6-pt script floor. No registered caption. Local-only source is not in pushed baseline.",
        "Conditional target-functional source reachability; best fixed path includes source survival. Not electrical adequacy. Register exact accepted static table and corrected MC estimator provenance before promotion.",
        "Raise exponent lettering without changing log scale/data; complete caption/provenance. Preserve as optional scientific diagnostic, not silently discarded."),
    "FigS16": (READY,
        "Review-only high-crew separation detail is readable with gray circles/orange squares and visible zero. 90-mm height, same saved endpoints as Fig06.",
        "Only 86/114-crew near-zero effects shown with saved bootstrap CIs; different zoom is explicit and does not replace main common scales. It is not new evidence or a new inference.",
        "Author may retain as an optional Supplement/review aid; never promote it in place of full Fig06."),
}

OLD_NOTES = {
    "Old-Fig01": (FIX, "Same exact July native artwork: 4.9-pt lettering remains unreadable. Original caption note is incomplete.", "No explicit author acceptance of the small-type exception exists.", "Same Fig01 author decision; not a corrected alternative."),
    "Old-Fig02": (OLD, "293-mm stack exceeds A4 body height; original maps are legible but would become too small if whole figure were shrunk. C is mapped-station count; public-site comparison absent.", "Mapped-station count is dependency structure, not mapping validation.", "Compare against the 174-mm 2x2 candidate; preserve all source artwork."),
    "Old-Fig03": (OLD, "68.9-mm compact T80 histogram/map are readable but lack the hazard/loss baseline chain.", "Population-realization T80 and reached-conditional tract mean remain distinct estimands.", "Panels are retained in newer Fig03; do not duplicate the baseline figure solely to preserve numbering."),
    "Old-Fig04": (OLD, "190-mm curve plus three repeated large boxplot rows; secondary lines faint and boxplot repetition dominates.", "5th-95th whiskers differ from Hospital definition figure's default IQR whiskers; short note lacks full integration/statistical definitions.", "Use latest all-policy comparison candidate; source distributions remain available."),
    "Old-Fig06": (OLD, "Old four-panel equity figure C has independent row scales and no numeric ticks. Map is readable, but hour effects are not visually comparable across rows.", "Only Hospital-first reference; generic 95% interval note does not identify interval type. This is equity content, not current Fig06 resource evidence.", "New Fig05 retains/extends this evidence with actual hour/Gini scales and explicit multiple references."),
    "Old-Fig07": (OLD, "147.5-mm compact profile/maps legible but category colors differ from current accepted cluster-ID palette; top-10 boundaries not clearly conveyed.", "Short caption omits residential/full-domain distinction and screening limitation.", "Use the current 229-mm reflow candidate; no clustering change."),
    "Old-FigS03": (OLD, "229-mm original input stack retains forbidden Retained station wording; no global A/B letters and title hierarchy oversized.", "Inputs are not resource-response outcomes.", "Current wording version is preferable, though it still needs lettering/panel hierarchy alignment."),
    "Old-FigS05": (OLD, "91.7-mm withdrawn GA candidate has visible search curves and incumbent, but older figure was formally cancelled. Scientific evidence is not discarded.", "Mean candidate search and fixed incumbents are not evaluation uncertainty or global optimality proof.", "New 155-mm GA reproducibility candidate restores this evidence; no automatic restoration of withdrawn numbering."),
    "Old-FigS08": (OLD, "Old planning loading title retains Retained wording; capacity increments clear but no global panel labels.", "Very short caption conflates planning row set with bounded station subset unless expanded.", "Latest planning-wording candidate is preferable; further caption/panel fixes still required."),
    "Old-FigS09": (OLD, "131-mm older PC scatter has very pale overlapping categories and inconsistent legend treatment; new opacity/reflow improves visibility.", "Do not confuse the older publication Fig07 palette with current official cluster-ID palette.", "Use new visibility candidate; original numerical clustering remains unchanged."),
    "Old-two-level-Fig06": (OLD, "Four absolute 29-versus-57 plots are readable but omit 86/114 and all duration cases. No main-policy leverage contrasts.", "This is a crude two-case sensitivity comparison, not a response curve or complete tested resource evidence.", "Author rejected as Main Fig06. Full four-level absolute outcomes remain in S12/S13."),
    "Old-layout-Fig04": (OLD, "Earlier 205-mm candidate has pale secondary policies that are difficult to follow. Latest candidate raises visibility.", "Older caption mentions 0-120 h while actual view is 0-100 h; current caption corrects this.", "Use latest readable Fig04; no outcome changed."),
    "Old-layout-Fig05": (OLD, "Undodged quartile intervals overlap heavily; newer candidate separates them. Reference-circle issue persists in newer candidate and remains an open fix.", "Same scientific data and reference comparisons as current Fig05; no evidence removed.", "Do not promote old undodged version."),
    "Old-layout-Fig07": (OLD, "267.6-mm stack leaves no comfortable A4 caption space. Maps are visible but the heatmap/profile section is too tall for main allocation.", "Same clustering and descriptive hotspot evidence as reflow; old size is not a scientific difference.", "229-mm native-font reflow is preferable; never shrink the whole old figure to force fit."),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_read_only():
    guard = json.loads((OUT / "READ_ONLY_GUARD.json").read_text())
    checked = {}
    for family in ("scientific_hashes", "publication_hashes", "source_artwork_hashes"):
        hashes = guard.get(family, {})
        errors = [p for p, h in hashes.items() if digest(ROOT / p) != h]
        assert not errors, (family, errors)
        checked[family] = {"checked": len(hashes), "changed": 0}
    assert subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=ROOT).hex() == guard["index_before_hex"]
    checked["unrelated_index_changed"] = False
    checked["baseline"] = BASELINE
    checked["guard_origin_head"] = guard.get("head")
    checked["guard_note"] = "Scientific/publication guard inherited from previous review; all listed bytes rechecked now. Source artwork/index captured fresh in this audit. No source module executed."
    checked["july_ref"] = subprocess.check_output(["git", "rev-parse", "archive/ijdrr-submission-20260722"], cwd=ROOT, text=True).strip()
    assert checked["july_ref"] == "182686868cffe962739804f6bc0ccecaed73d601"
    return checked


def paragraph_page(title, sections):
    doc = fitz.open()
    font_files = {"Arial": "C:/Windows/Fonts/arial.ttf", "ArialBold": "C:/Windows/Fonts/arialbd.ttf"}
    fonts = {name: fitz.Font(fontfile=path) for name, path in font_files.items()}
    styles = {"title": ("ArialBold", 13, 17), "heading": ("ArialBold", 10, 13), "body": ("Arial", 9.5, 13)}
    page = None
    y = 0
    def new_page():
        nonlocal page, y
        page = doc.new_page(width=210 * MM, height=297 * MM)
        for name, path in font_files.items(): page.insert_font(fontname=name, fontfile=path)
        y = 20 * MM
    new_page()
    def para(text, style):
        nonlocal y
        name, size, leading = styles[style]
        for paragraph in text.split("\n"):
            # Exact font measurement; wrap long provenance paths without shrinking.
            words = paragraph.split(" ")
            lines = []; line = ""
            for word in words:
                trial = (line + " " + word).strip()
                if fonts[name].text_length(trial, fontsize=size) <= 185 * MM:
                    line = trial; continue
                if line: lines.append(line)
                line = ""
                for ch in word:
                    if fonts[name].text_length(line + ch, fontsize=size) > 185 * MM:
                        lines.append(line); line = ""
                    line += ch
            if line: lines.append(line)
            for line in lines:
                if y + leading > 277 * MM: new_page()
                page.insert_text((12.5 * MM, y), line, fontname=name, fontsize=size)
                y += leading
        y += 4 * MM
    para(title, "title")
    for head, body in sections:
        para(head, "heading"); para(body, "body")
    return doc


def packet(rows):
    d = fitz.open()
    with paragraph_page("Complete Main and Supplement Figure Review", [
        ("Scope and baseline", "Read-only audit of actual artwork at commit " + BASELINE + ". Seven main candidates, sixteen Supplement/review candidates, and fourteen older alternatives. FigS10-FigS16 are provisional review labels, not manuscript numbering decisions."),
        ("How to use this packet", "Every artwork page embeds the actual source PDF at 185 mm wide, preserving native text and vector paths. Each is immediately followed by its currently registered caption/note and separate audit observations. No figure, scientific result or caption source was changed. Captions that are incomplete or absent are not silently repaired here."),
        ("Tall artwork", "Figures retain native height. The 293-mm old Fig02 needs an extended review page, explicitly flagged as a manuscript layout problem; it is not shrunk. Fig03 (216 mm), Fig05 (218 mm), Fig07 (229 mm) and S04 (244 mm) are shown at native size. Caption pages are separate, not squeezed into artwork."),
        ("Decision boundaries", "READY_FOR_AUTHOR_PROMOTION means the audit found no blocking individual-artwork issue; it does not mean author acceptance or automatic promotion. Cross-figure corrections listed in the report still gate a coherent set. No author small-font exception is presumed for Fig01. FigS14/FigS15 are actual local-only backup candidates absent from the requested pushed baseline and are explicitly marked."),
    ]) as q:
        d.insert_pdf(q)
    toc = [[1, "Preferred Main candidates", len(d) + 1]]
    for n, row in enumerate(rows):
        if row["figure"] == "FigS01": toc.append([1, "Supplement and review candidates", len(d) + 1])
        if row["figure"] == "Old-Fig01": toc.append([1, "Older publication/review alternatives", len(d) + 1])
        row["packet_artwork_page"] = len(d) + 1
        toc.append([2, row["figure"], len(d) + 1])
        height = max(297 * MM, (row["height_mm"] + 35) * MM)
        p = d.new_page(width=210 * MM, height=height)
        p.insert_font(fontname="Arial", fontfile="C:/Windows/Fonts/arial.ttf")
        label = row["figure"] + " | 185 mm native artwork | REVIEW ONLY"
        if row.get("not_in_baseline"): label += " | LOCAL-ONLY SOURCE"
        p.insert_text((12.5 * MM, 10 * MM), label, fontsize=8, fontname="Arial")
        with fitz.open(ROOT / row["path"]) as src:
            scaled_h = src[0].rect.height * (185 * MM / src[0].rect.width)
            p.show_pdf_page(fitz.Rect(12.5 * MM, 18 * MM, 197.5 * MM, 18 * MM + scaled_h), src, 0)
        p.insert_text((12.5 * MM, height - 8 * MM),
                      f"Actual artwork: {row['width_mm']:.1f} x {row['height_mm']:.1f} mm; min text {row['min_font']:.2f} pt. Caption follows.",
                      fontsize=8, fontname="Arial")
        row["packet_caption_page"] = len(d) + 1
        current = row["caption"] or "NO REGISTERED MANUSCRIPT CAPTION. This local source is reviewed for completeness, not certified for submission."
        with paragraph_page(row["figure"] + " — current caption and audit", [
            ("Current caption / registered note (verbatim)", current),
            ("Recommended status (not an author decision)", row["recommended_status"]),
            ("Actual visual observations", row["visual_issues"]),
            ("Scientific wording / estimand checks", row["scientific_wording_issues"]),
            ("Required action / scope", row["action"]),
            ("Source file", row["path"] + "\nSHA-256: " + row["sha256"]),
        ]) as q:
            d.insert_pdf(q)
    d.set_toc(toc)
    d.set_metadata({"title": "Complete Main and Supplement Figure Review", "author": "LA Grid figure review", "subject": "Native-size, read-only promotion-readiness audit; no promotion"})
    target = OUT / "COMPLETE_MAIN_AND_SUPPLEMENT_FIGURE_REVIEW.pdf"
    d.save(target, garbage=4, deflate=True)
    page_count = len(d)
    d.close()
    return target, page_count


def write_report(rows, checks, page_count):
    counts = Counter(r["recommended_status"] for r in rows if r["kind"] == "preferred")
    text = ["# Complete figure-set promotion-readiness audit", "",
        f"Baseline: `{BASELINE}`. Actual files were opened via fresh native PDF renders and unshrunk 185-mm page previews in this audit. Earlier PASS reports were not used as visual acceptance.", "",
        f"**No promotion or artwork changes.** {len(rows)} actual source PDFs inspected: 7 main candidates, 16 Supplement/review candidates and 14 older alternatives. The review packet has {page_count} pages, with each artwork immediately followed by its current caption/note and audit observations.", "",
        "## Decision meaning and set-level result", "",
        "The complete set is **not ready for one-step promotion**. Individually ready candidates are not author-approved. No `READY_WITH_EXPLICIT_AUTHOR_EXCEPTION` is assigned because no explicit submission-sized small-font exception has been accepted. No confirmed formula/data error was found requiring the scientific/claim category; incomplete captions/provenance remain explicit presentation gates rather than invented scientific failures.", "",
        "Preferred/review candidates: " + "; ".join(f"{n} {s}" for s, n in counts.items()) + ".", "",
        "### Blocking cross-figure corrections", "",
        "1. **Fig01:** exact July artwork still reaches 4.9-pt normal type. Restoring original artwork did not authorize a small-lettering exception. Ask author to explicitly accept that exception or authorize a separate re-layout candidate; do neither automatically.",
        "2. **Hazard identity:** Fig03 versus S01/S02 uses different color/order/label systems. Uniform names plus color/line redundancy are required; preserve the underlying hazard definitions. Historical versus 2pc50 differences are not pure PGA sensitivity.",
        "3. **Policy/reference identity:** Fig05 C/D references are circles, while Fig06 Hospital is gray-circle and Impact orange-square. S04/S07 dynamic policy line styles also differ from the main policy key. Quantity coding (solid full versus dashed fixed path) may justify a local override, but policy identity must stay identifiable.",
        "4. **Mapping identity:** S06 uses a different baseline/utility-compatible color/shape key from Fig02 D. Its nearest-site wording must be reconciled with top-weight retained candidate definitions, using the same 337-tract denominator.",
        "5. **Intervals:** Fig04 and Fig05 A/C/D use realization 5th-95th ranges; Fig06 uses saved bootstrap CIs of mean matched contrasts. S01 uses default 1.5-IQR station boxes; Hospital S10 uses default 1.5-IQR realization boxes and fliers. These are not one statistical object. Captions must state each explicitly.",
        "6. **Captions and panel hierarchy:** S01/S02/S04/S06/S07/S08/S10 currently have short registered notes rather than complete captions. S03/S04/S08 need global panel lettering/hierarchy. S11 dark-cell annotation contrast needs correction.",
        "7. **Supplementary provenance:** S14/S15 artwork paths are not present in the requested pushed baseline (alternate copies are also currently staged/local, not committed in that baseline). They were viewed, but must be registered with their accepted result authority before promotion. S15 logarithmic scripts are 5.25 pt.", "",
        "## Per-figure decision table", "",
        "`SUPERSEDED — DO NOT USE` below applies to a particular artwork version, not permission to delete scientific evidence or frozen source files. Optional S14-S16 labels do not select manuscript inclusion.", "",
        "| Figure | Candidate file | Intended role | Actual size (mm) | Minimum font (pt) | Actual visual issues | Scientific wording issues | Recommended status |",
        "|---|---|---|---:|---:|---|---|---|"]
    for r in rows:
        vals = [r["figure"], f"`{r['path']}`", r["role"], f"{r['width_mm']:.1f} × {r['height_mm']:.1f}", f"{r['min_font']:.2f}", r["visual_issues"], r["scientific_wording_issues"], r["recommended_status"]]
        text.append("| " + " | ".join(str(v).replace("|", "/").replace("\n", " ") for v in vals) + " |")
    text += ["", "## Specific height and native-size assessment", "",
        "All artwork is 185 mm wide. The page review uses 210-mm paper and 12.5-mm side margins; no submission figure is reduced to fit. Main Fig03 (216 mm) is dense but its T80 map remains a substantial panel. Fig05 (218 mm) is readable after dodge, although legend/reference issues remain. Fig07 (229 mm) needs near-full-page body allocation; legends stay under their own maps and top-10 outlines remain visible. S04 (244 mm) fits the review page only with caption separate and has global hierarchy problems. Old Fig02 (293 mm) exceeds ordinary A4 body space; its review page is extended, not artificially shrunk. None of these height judgments alone grants author acceptance of placement.", "",
        "## Scientific interpretation checks (read-only trace)", "",
        "- Fig03 D-right reads `mean_T80_hr_when_reached` from the saved S1/S2 table. `provenance/reviewer_working/Supplement_Rebuild_20260925/plot_initial_and_historical.py` accumulates each tract's first event reaching 0.8 in each realization and divides by that tract's reached count. It is a mean of realization-specific hitting times conditional on reaching; this is distinct from population T80 distribution (D-left) and T80 of an ensemble-mean curve. No calculation was rerun.",
        "- `src/la_grid/plotting/render_revised_suite.py` supplies formal evaluation DS arrays (92 x 1,000) and saved initial-tract summaries to the July-style Stage 1 renderer. S01 and Fig03 box whisker differences are display summaries, not evidence that one scenario uses a different station universe. S01 is not newly observed earthquake damage.",
        "- The saved 337-tract public-site table contains 320/337 versus 329/337 any-match, 296/337 versus 302/337 top-1, and 317/337 versus 324/337 top-3. Top-k is retained positive candidates ranked by descending weight; 'nearest site' is not a sufficient general definition. This is public-site support/agreement, not feeder/service-territory ground truth.",
        "- Hospital S10 boxplot calls `plot_box()` with default 1.5-IQR whiskers and fliers; the old Fig04 distribution code explicitly uses 5th-95th whiskers. Current main Fig04 uses dot/range summaries instead. The definition map prioritizes substations using hospital-linked tract counts and population tie-break, not tracts or delivered hospital power.",
        "- Fig06 uses the approved two separate OFAT scenario families and saved bootstrap uncertainty, with Hospital-first/Impact-first references. Fig05 adds Degree-first as reference sensitivity; it must not be relabeled as an originally predeclared primary reference. No smoothing/interpolation, bootstrap or new scientific computation was performed.",
        "- Fig07/S09 official cluster-ID palettes match by actual output inspection. Full-domain N/A tracts and 2,291 typology members remain distinct. Hotspot ranking is descriptive and does not validate intervention benefit or optimal repair order.",
        "- S08 separates 2026 facility planning loading from capacity post-processing on frozen 2pc50 service. 34 Level-A rows / 28 stations do not equal the 19 one-to-one bound-supported stations. One OLINDA facility is binding-capable; these data do not establish adequacy of all 92 stations.", "",
        "## Completeness and boundaries", "",
        "The packet includes every current numbered publication PDF, preferred v2.1/layout main candidate, the latest corrected review candidates, withdrawn GA evidence, full four-level crew/duration evidence, cross-hazard policy effects, hospital construction, and available gate/static-reliability backup candidates. All 37 were viewed afresh at native/page size. The old alternatives remain as comparison pages, not deleted files.", "",
        "Multi-page metric-review browsers (`metric_tradeoff_review/ALL_METRIC_RELATIONSHIPS_REVIEW.pdf`, saved paired effects, quartile redistribution, spatial effects, vulnerability-definition and measure/targeting review books), `ALL_SUMMARY_METRICS_REVIEW.pdf`, contact sheets and previous v2/v2.1 review packets are retained research/review containers, not individually numbered submission artworks. Their hundreds of pages are **not** certified as visually audited by this report. A future author choice of a specific browser page as a submission panel needs a fresh native-size audit; this report does not silently declare those metrics unimportant. Pure July/failed/debug/provenance outputs outside the current candidate indices are not a second final figure set.", "",
        "## File identity, fonts and read-only guard", "",
        "35 of the 37 actual PDFs match SHA-256 against the requested commit's LFS OID. S14/S15 are explicitly local-only backup artwork. All inspected text resources are Arial/Arial-Bold subsets, with no DejaVu text resources found; raster-embedded labels are not measured as PDF text and are judged only through actual visuals. Minimum font numbers are extracted native PDF spans; they are evidence, not substitutes for looking at each page.", "",
        f"Rechecked: {checks['scientific_hashes']['checked']} numerical authority files, {checks['publication_hashes']['checked']} publication files and {checks['source_artwork_hashes']['checked']} audited source PDFs: **zero byte/hash changes**. The inherited scientific guard originates at `{checks['guard_origin_head']}`; it is not falsely described as a new full archive rehash. No trajectory/archive rewrite or scientific source execution occurred. Existing unrelated staged entries were preserved byte-for-byte before this audit's scoped staging. Protected July ref remains `{checks['july_ref']}`.", "",
        "Deliverables: `COMPLETE_MAIN_AND_SUPPLEMENT_FIGURE_REVIEW.pdf`, `PROMOTION_DECISION_TABLE.csv`, `ACTUAL_FILE_MEASUREMENTS.csv`, `ACTUAL_INSPECTION_LOG.csv`, `INVENTORY.json`, fresh `native_views/` and `page_views/`, and `READ_ONLY_VERIFICATION.json`. No promotion or automatic fixes were made."]
    (OUT / "COMPLETE_FIGURE_PROMOTION_READINESS.md").write_text("\n".join(text) + "\n", encoding="utf-8")


def main():
    checks = validate_read_only()
    rows = json.loads((OUT / "INVENTORY.json").read_text())
    assert {r["figure"] for r in rows} == set(DECISIONS) | set(OLD_NOTES)
    for r in rows:
        status, visual, science, action = (DECISIONS | OLD_NOTES)[r["figure"]]
        r.update(recommended_status=status, visual_issues=visual, scientific_wording_issues=science, action=action,
                 native_pdf_viewed=True, fresh_185mm_page_viewed=True,
                 inspection_basis="Fresh native PDF-render image and native-width page-preview image opened in current audit; no reliance on previous PASS.")
    target, count = packet(rows)
    write_report(rows, checks, count)
    pd.DataFrame(rows).to_csv(OUT / "PROMOTION_DECISION_TABLE.csv", index=False)
    pd.DataFrame([{k: r[k] for k in ("figure", "path", "native_pdf_viewed", "fresh_185mm_page_viewed", "inspection_basis", "packet_artwork_page", "packet_caption_page", "sha256")} for r in rows]).to_csv(OUT / "ACTUAL_INSPECTION_LOG.csv", index=False)
    checks = validate_read_only()
    checks.update(packet_pages=count, packet_sha256=digest(target), source_pdf_count=len(rows), baseline_lfs_identity_matches=sum(r["lfs_matches_baseline"] for r in rows), promotion=False, scientific_execution=False)
    (OUT / "READ_ONLY_VERIFICATION.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps({"packet": str(target), "pages": count, "preferred_status_counts": dict(Counter(r["recommended_status"] for r in rows if r["kind"] == "preferred")), "science_hash_changes": 0}))


if __name__ == "__main__":
    main()
