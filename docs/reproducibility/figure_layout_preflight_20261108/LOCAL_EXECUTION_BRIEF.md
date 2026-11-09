# Local task — publication artwork margin, spacing, and print-fit preflight (all 16 figures)

## Scope and source of truth
Work on a dedicated local worktree/branch based on **`review/s6-main4-20261107`**, not the repository default branch or the 2026-10-14 archived suite. Current authoritative individual PDFs/PNGs are `results/figure_review_s6_main4_20261107/{Main,Supplement}/` (8 main and 8 supplementary figures). Audit the original individual artwork, **not just the caption packet**. `results/figure_delivery_20261108/` may be stale and must not be used as the artifact authority. Preserve the existing figure suite and produce a separate candidate layout collection for author review.

The user has identified **Supplementary Figure S7 (Restoration-priority geography)** as having inconsistent white margins and **Supplementary Figure S5 (four-policy sensitivity)** as visually off-center. These are priority corrections, but **audit all 16 figures** rather than applying isolated fixes. On the current registry, S7 is 185 × 264 mm, S5 is 185 × 210 mm; 264 mm is unusually tall and merits an explicit check of wasted whitespace, print size, and map-panel arrangement. PDF page-size consistency alone is NOT a valid margin audit.

## Publisher requirements: verify and distinguish
1. Confirm the actual **target journal** before declaring publisher compliance. The previously selected *International Journal of Disaster Risk Science (IJDRS)* is a **Springer** journal, not Elsevier. Its journal-specific instructions supersede generic publisher guidelines. Do not falsely claim Elsevier compliance is required by IJDRS.
2. User specifically requests comparison to **Elsevier's official artwork guidance**:
   - https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing
   - https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-types
   - https://www.elsevier.com/en-gb/about/policies-and-standards/author/artwork-and-media-instructions/artwork-faq
   - https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-formats-checklist
   General illustrative widths: 90 / 140 / 190 mm. Text usually ~7 pt at final printed size (Elsevier: 6 pt minimum for subscripts/superscripts as rule of thumb); embedded standard fonts; legible lines/symbols; tightly cropped bitmap artwork; vector preferred for figures; line work 0.10–1.5 pt and usually >=0.25 pt for reliable reproduction; raster effective resolution by type (300 dpi halftone, 500 combination, 1000 pure bitmap line art). **There is no official universal left/right/top/bottom numerical margin or fixed panel gap. Do not invent one and call it an Elsevier requirement.**
3. For the actual Springer target, check current journal-specific instructions and https://www.springer.com/kr/authors-editors/journal-author/journal-author-helpdesk/manuscript-preparation/1260 ; Springer general guidance gives typical 39 / 84 / 129 / 174 mm figure widths and maximum ~234 mm height for most journals, but verify applicability to IJDRS; do not conflate generic and journal-specific policies.
4. Record `standard_source_url`, `rule`, `journal_applicability`, and `pass/fail/not-applicable` in the report. Readability and equalized optical margins are production-quality objectives, not invented publisher mandates.

## Mandatory measurement (every figure)
Use real native PDFs from local Git LFS materialization, not pointers or old preview images. Inspect at native size using PyMuPDF/PDF geometry AND independent 150/200-dpi rendered inspection. For each figure and **each panel**:
- MediaBox/CropBox physical size; actual nonwhite visible-artwork bounds, ink bounds, all text/legend/colorbar/annotation bounds; left/right/top/bottom white margins in mm; center offset in mm.
- Panel graphics bounds versus panel title, axis tick and axis labels, tick lengths, legends, symbols, colorbars, inset, map frames, edge of each multi-panel grouping.
- Vertical/horizontal gutters between adjacent panel content including text; detect uneven rows/columns, unexplained whitespace, clipping/overlaps, and legend/plot collisions.
- Native font faces, embedded fonts, min and median **finished-size** lettering, line weights, thin/low-contrast details; vector-versus-raster coverage and effective bitmap DPI. Verify after reflow/cropping at the intended article column width, not merely at 185-mm native size.
- Produce a visual comparison montage using common display width. **Do not treat empty/transparent path bounds as visible ink.** Inspect raster page visually; PDF drawing-bbox heuristics can be misleading. Where figure content itself is intentionally asymmetric (geography, right-side legend), distinguish justified asymmetry from stray outer whitespace.
- Provide a comparable cross-figure summary (actual margins, gutters, visual center offsets) and mark exceptions with a concrete reason. Harmonize layout/gutters across similar figures, without forcing identical internal grids across unrelated plot types.

## Priority repairs
### S7
Determine the exact cause of its unequal white margins, including any blank strips from the 185 × 264-mm page, multi-panel map ratios, population colorbar, legends, and annotations. Refactor the **source generator**, not just a PDF crop override, to use a compact, optically centered layout. Preserve map aspect ratios, original station ranks, community population background, cartographic extent/identity, priority markers and all other scientific content. Crop only genuinely dead whitespace; reflow multi-panel elements where needed. If the 264-mm height is necessary, document why; otherwise reduce it consistent with printability and readability. Check top, bottom, left and right, and inter-panel gutters independently.

### S5
The current plotting code in `src/la_grid/plotting/figure_presentation.py` function `supplementary5_four_policy` uses all three `fig.add_axes([.305, ..., .66, .195])` panel axes (their **axes frames** center at 63.5% of page width, ~25 mm right of page center). This alone does not prove the full labeled composition is off-center; measure inclusive actual text and tick-label bounds. Reposition **the entire graphic, including policy labels, titles, uncertainty bars and legends**, to achieve balanced visible margins at native print size. Keep the 4 policy rows, all three scientific panels, and all realization-level numbers intact.

### All other 14 figures
Make targeted layout fixes for objectively identified violations only, preserving all panels and scientific content. Do not resize all graphics indiscriminately or alter aspect ratios to mimic a particular template.

## Preservation and handoff
- **Do not run** damage simulations, Monte Carlo, crews/scheduling, optimization, or clustering. No changes to input data, model, policy order, source gate, numeric curves, mapped geography, captions' quantitative statements, color-scale semantics, or network metrics.
- Rebuild individual vector PDFs plus publication-grade PNGs, main/supplement/combined caption packets, figures index/manifest, and presentation mirror/gallery **only after layout QA**. Keep generated candidate separate from existing review suite until explicitly approved; do not overwrite other running work.
- Create `FIGURE_LAYOUT_AUDIT.csv` or JSON with one row per figure/panel and fields: file, native width/height mm, visible L/R/T/B margins mm, content center offset mm, horizontal/vertical gutter mm, smallest rendered font pt, line weight min pt, bitmap effective dpi, source standard/rule, status, recommended fix, actual change, exception rationale.
- Export S7 and S5 **before-versus-after** at identical physical scale, a 16-figure contact sheet at fixed display width, and a concise `FIGURE_LAYOUT_AUDIT.md` listing all issues and outcomes. Inspect every rendered page at realistic print width.
- Ensure no visual/semantic regression: panels preserved; text/legend/colorbar/titles readable and not overlapping; all scientific data and colors same. Use vector object and numeric records to check identity, and visible pixel differences to confirm only authorized layout changes.
- Deliver actual files, hashes, test outputs, and links. **Do not claim compliance or finished correction based only on a successful script run, equal PDF page widths, or a QA flag.** Explicitly report any unsatisfied criterion.

## Acceptance criteria
1. S7 outer whitespace is visually balanced and needless 264-mm height/empty bands are removed or explicitly justified.
2. S5's complete label-plus-plot composition—not just the axes—appears centered; three panels align to one consistent grid.
3. All 16 figures checked and documented against cited applicable standards (journal-specific requirements first).
4. No reduced or missing panels, no altered results, no clipping, no figure-caption-numbering errors, and no disruption to other workstreams.
5. The user can compare *native-size* before/after visualizations and inspect a complete corrected figure set.
