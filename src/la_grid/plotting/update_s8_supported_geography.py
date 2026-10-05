"""Author-authorized S8 update from the completed geography review tables.

Preserves the existing facility-loading panel as native vector artwork.
Does not evaluate science; only composes artwork and updates its caption/index.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil

import fitz
import pandas as pd

from la_grid.paths import REPO_ROOT as ROOT

REVIEW = ROOT / "results/figure_review"
DATA = ROOT / "results/capacity/SCE_SUPPORTED_GEOGRAPHY"
ARCHIVE = ROOT / "provenance/figure_review_history/s8_full_geography_before_20261004"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run():
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    targets = [REVIEW / "Supplement/FigS08.pdf", REVIEW / "Supplement/FigS08.png",
        ROOT / "results/figures/FigS08_Capacity_Sensitivity.pdf",
        ROOT / "results/figures/FigS08_Capacity_Sensitivity.png"]
    old_hashes = {}
    for i, p in enumerate(targets):
        backup = ARCHIVE / (("review_" if i < 2 else "publication_") + p.name)
        if backup.exists():
            raise FileExistsError(f"S8 already archived: {backup}")
        shutil.copy2(p, backup)
        old_hashes[p.relative_to(ROOT).as_posix()] = sha(p)
    caption_file = REVIEW / "MANUSCRIPT_FACING_CAPTIONS.md"
    shutil.copy2(caption_file, ARCHIVE / caption_file.name)
    original = fitz.open(ARCHIVE / "review_FigS08.pdf")
    increment = fitz.open(ROOT / "provenance/figure_review_history/s8_supported_geography_draft_20261004/PROPOSED_FigS08B_SUPPORTED_GEOGRAPHY.pdf")
    width = original[0].rect.width
    out = fitz.open()
    # A is byte-identical visual content, clipped below its own xlabel; the
    # former full-study effect panel is replaced, not overpainted.
    upper_height = 425
    lower_top = 441
    page = out.new_page(width=width, height=lower_top + increment[0].rect.height)
    page.show_pdf_page(fitz.Rect(0, 0, width, upper_height), original, 0,
                       clip=fitz.Rect(0, 0, width, upper_height))
    page.show_pdf_page(fitz.Rect(0, lower_top, width, page.rect.height), increment, 0)
    # Add the header after panel imports, with an independent font resource.
    page.insert_font(fontname="ArialS8Final", fontfile="C:/Windows/Fonts/arial.ttf")
    page.insert_text((97, 438), "B. Capacity-induced service loss within SCE-supported geography",
                     fontname="ArialS8Final", fontsize=9.5)
    out.save(targets[0], garbage=4, deflate=True)
    out.close()
    with fitz.open(targets[0]) as d:
        d[0].get_pixmap(matrix=fitz.Matrix(600/72, 600/72), alpha=False).save(targets[1])
        min_font = min(s["size"] for b in d[0].get_text("dict")["blocks"] if "lines" in b
                       for l in b["lines"] for s in l["spans"])
        size = f"185.000 x {d[0].rect.height*25.4/72:.3f}"
        assert min_font >= 7 - 1e-5
    shutil.copy2(targets[0], targets[2])
    shutil.copy2(targets[1], targets[3])
    caption = (
        "(A) SCE 2026 Grid Needs Assessment facility loading for 34 same-facility, voltage-level planning rows across 28 substations "
        "with simultaneous forecast demand and provider-defined limits. Marker shapes identify low-side voltage. The 100% line is the "
        "provider-defined planning limit, not an earthquake failure or overload threshold. OLINDA 66/12 is the only internally consistent "
        "row above this limit, at 109.04%. (B) Capacity-induced modeled service loss under 2pc50, 57 crews and repair-duration multiplier 1.00, "
        "integrated over 0–480 h using the same 1,000 physical realizations per policy. The left panel uses the primary evidence-supported "
        "domain: 676 tracts classified as strict SCE in the utility metadata, with positive original mapping dependency on at least one of "
        "19 one-to-one capacity-supported SCE substations (population 2,971,782). The right panel uses the independently recomputed local "
        "binding domain: 25 tracts with positive OLINDA-induced loss (population 117,102); all four policies identify the same set. "
        "Points show population-weighted mean increments, computed with each domain's population denominator; lines show the 5th–95th "
        "realization range, not a confidence interval. The two panels use different hour scales, both beginning at zero. Original tract weights "
        "are not renormalized or reassigned; unsupported station contributions remain identical and cancel in the difference. Station service "
        "is bounded by min[modeled service, min(1, planning limit/forecast demand)]. Nine multi-facility stations are excluded from the bound; "
        "73 of the 92 stations have no applicable bound. Only OLINDA 66/12 has a binding-capable ratio: planning limit 26.09 MW divided by "
        "forecast demand 28.45 MW. Mean increments span 0.366–0.383 h on the primary domain and 9.299–9.722 h on the local domain. "
        "Applying the ceiling does not reverse the Impact-first, Degree-first or Vulnerability-first service-loss contrast relative to "
        "Hospital-first within either domain. This does not imply that domain-specific strategy rankings equal those for the full study area. "
        "The broader 932-tract dependency set and the 337-tract public-record comparison set are diagnostic coverage sets, not the "
        "primary effect denominator. The former approximately 0.12 h estimate averaged over all 2,315 tracts and is retained only as provenance. "
        "This planning-ceiling sensitivity is not post-earthquake load flow, an estimate of earthquake overload, or evidence of full-network electrical adequacy."
    )
    text = caption_file.read_text(encoding="utf-8")
    text, count = re.subn(r"(## Supplementary Figure S8\.[^\n]*\n\n).*?(?=\n\n## |\Z)",
                         lambda m: m.group(1) + caption, text, flags=re.S)
    assert count == 1
    caption_file.write_text(text, encoding="utf-8")
    manifest_file = REVIEW / "FIGURE_MANIFEST.csv"
    m = pd.read_csv(manifest_file, dtype=str).fillna("")
    for ext, target in [("pdf", targets[0]), ("png", targets[1])]:
        mask = m.final_name.eq("Supplement/FigS08." + ext)
        assert mask.sum() == 1
        for c in ["source_file", "source_commit", "sha256", "current_source_file"]:
            m.loc[mask, "parent_" + c] = m.loc[mask, c]
        rel = target.relative_to(ROOT).as_posix()
        m.loc[mask, ["source_file", "source_commit", "sha256", "current_source_file", "size_mm", "min_font_pt", "status"]] = [
            rel, "ARTWORK_COMMIT_PENDING", sha(target), rel, size, f"{min_font:.3f}", "AUTHOR_AUTHORIZED_SCE_DOMAIN_UPDATE"]
    m.to_csv(manifest_file, index=False)
    index_file = ROOT / "results/figures/FIGURE_INDEX.csv"
    f = pd.read_csv(index_file, dtype=str).fillna("")
    for target in targets[2:]:
        mask = f.file.eq(target.name)
        assert mask.sum() == 1
        rel = target.relative_to(ROOT).as_posix()
        for c in ["source_authority", "source_path"]: f.loc[mask, c] = rel
        f.loc[mask, "sha256_or_lfs_oid"] = "sha256:" + sha(target)
        f.loc[mask, "generator"] = "src/la_grid/plotting/update_s8_supported_geography.py"
        f.loc[mask, "main_message"] = "Capacity-induced service loss is 0.366–0.383 h within strict-SCE supported geography; OLINDA-local effects are reported separately."
        f.loc[mask, "scientific_content"] = "2026 planning facility loading and evidence-supported geographic capacity sensitivity"
        f.loc[mask, "current_status"] = "author-authorized supported-geography update"
        f.loc[mask, "notes"] = "Original full-study estimate archived; original mapping and frozen trajectories unchanged."
        data = DATA / "POLICY_DOMAIN_SUMMARY.csv"
        f.loc[mask, "source_data_path"] = data.relative_to(ROOT).as_posix()
        f.loc[mask, "source_data_sha256"] = "sha256:" + sha(data)
    f.to_csv(index_file, index=False)
    # Rebuild the existing author packet from its current native figure pages.
    # Caption text is supplied in a separate page immediately after each figure.
    from la_grid.plotting.apply_review_terminology import collections
    collections()
    log = {"old_artwork_sha256": old_hashes, "new_artwork_sha256": {
        p.relative_to(ROOT).as_posix(): sha(p) for p in targets}, "size_mm": size,
        "minimum_font_pt": min_font, "caption_sha256": sha(caption_file),
        "panel_a_visual_content_changed": False, "science_source_tables_changed": False,
        "source_summary_sha256": sha(DATA / "POLICY_DOMAIN_SUMMARY.csv")}
    (DATA / "S8_UPDATE.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    (ARCHIVE / "README.md").write_text("# Previous S8 full-study denominator artwork\n\n"
        "Preserved before the author-authorized supported-geography update. The approximately 0.12 h effect uses all 2,315 tracts. "
        "Current S8 uses the strict-SCE supported denominator and separately reports OLINDA-local effects. Original capacity CSVs remain unchanged.\n", encoding="utf-8")


if __name__ == "__main__":
    run()
