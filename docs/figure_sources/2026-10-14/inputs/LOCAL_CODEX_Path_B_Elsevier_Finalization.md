# LOCAL TASK — PATH B (SEVEN VARIABLES) + ELSEVIER ARTWORK

**Author decision: FINAL primary design is the seven-variable P2 model.** Use saved P2/K3/seed42 for main text; retain P2/K4 as mandatory sensitivity, with K4's stronger geographic agreement explicitly disclosed. Do not add NCV14 to clustering. NCV14 is supplementary environmental-hazard context only. This instruction supersedes exploratory eight-variable and legacy five-class Figure 7 specifications.

## Target and boundaries

Repository: `yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale`

Review authority: `ecf431ce9487fcfd822e36259f56d61dfec4f180`, branch `review/stage7-path-b-p2-figure7-20261013`.

Primary data: `docs/data_research/stage7_path_b_p2_integration_review_20261014/`.

Current 7.2 x 9.0 inch proof set: `docs/reproducibility/path_b_pre_migration_publication_gate_20261014/`.

**Local work only. Do not commit, push, merge, overwrite active Figure 7/S8, touch the frozen policy/simulation/GA calculations, refit K-means, change original quartiles, delete historical evidence, or change the original source checkout/index.** Preserve the 950 protected science files, 17 current numbered figure pairs and their mirrors. Work in a separate local checkout or a new review-only folder; record source hashes before any edit.

## 1 — Seven-variable scientific authority

Fit specification (reuse saved arrays and label identities):

- RQ1: `Init_Supply`, `Grid_Impact`, `Redundancy_HHI` (each squared-distance weight `1/9`).
- RQ2: `B_Unconstrained`, `MeanDelta` (each `1/6`).
- RQ3: `SOVI_SCORE`, `log1p(Population)` (each `1/6`).

Keep 2,299 positive-population eligible tracts (including eight zero-housing tracts), 16 zero-population N/A and the full 2,315-tract service model. P2/K3 class counts must be **1,235 / 428 / 636**. P2/K4 is supplementary with 37 / 1,217 / 429 / 616. Report minimum held-out geographic ARI K3 **0.418931** vs K4 **0.805674**. Do not claim K3 is statistically superior; K3 is selected for parsimonious interpretation. Reuse the frozen five-policy mean burden `B_Unconstrained + MeanDelta` and the 1,000 physical identities. Exact joint Q4/P75 result: **94 tracts**, **350,799 residents**, threshold **38.38135467381475 equivalent h**. This is descriptive co-occurrence, not a statistically significant hotspot or intervention priority.

## 2 — Elsevier formatting fixes (review-only)

Use official general instructions, while keeping journal-specific requirements unresolved until the target journal is confirmed:

- Sizing: https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing
- Format/fonts: https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-overview
- Line work and accessibility: https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-faq
- Captions and separated artwork: https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-formats-checklist

Preserve the 7.2 x 9.0 inch working figure size (182.88 x 228.6 mm) pending journal-specific confirmation. Do not claim that 9.0 inches is Elsevier's universal maximum. All normal figure lettering at finished size must be >=7 pt, with a 7.5-pt conservative working minimum; sub/superscript at least approximately 6 pt. Keep Arial or other official recommended fonts **embedded** (`pdf.fonttype=42` where supported). Output vector PDF with no rasterized map or fonts; keep a 600-dpi preview for author QA, not as a replacement for vector submission. Keep linework >=0.10 pt absolute, preferably >=0.25 pt for lines that need to be clearly seen; recognize the 2,299-tract interior boundary density and do not thicken every polygon indiscriminately. Preserve 94 joint-high black outlines as visually prominent.

**Color accessibility:** Candidate B remains the preferred color rendering, with identical recovery-burden luminance mapping across frozen Q1–Q4. It is not grayscale accessible because quartile hues merge. Preserve candidate A as the textured/monochrome-oriented alternate; **also evaluate** a clean black-and-white two-map appendix (service deficit grayscale and vulnerability quartiles/patterns shown separately, same EPSG:3310 extent) if the journal's printed grayscale requirement or small-tract hatching makes A insufficient. The appendix is an accessibility aid, not a new risk score. Clearly record print-size limitations; do not call the color map universally accessible. Never replace continuous burden by a quartile-specific relative scale.

Generate a clean submission-style copy from the 7.2 x 9.0 inch print-fit candidate, **without** the banner `PATH B AUTHOR REVIEW - NOT FORMAL STAGE 7`; preserve all plotted scientific content and vector paths. Do not remove the banner from the archived review artifact itself. The attached `local_figure7_elsevier_preflight.py` can verify both archived proof inputs and export non-destructive copies. Examine its JSON warnings before considering any release.

Verify in actual PDF rendering (not only source Matplotlib): page dimensions, fonts embedded, normal text>=7.5pt, line widths, no cropping/overlap, no raster objects, exact contour/colorbar meanings, distinct 16 N/A tracts, consistency with figures 1–6, and legibility of dense polygons. Render full color, grayscale, protanopia, deuteranopia and tritanopia and inspect at expected publication size. Confirm target journal's maximum height and figure/caption placement before final acceptance.

## 3 — Word documents in the user's PART V style

Two ready-to-review Word files are provided with this task:

- `PART_V_Path_B_Seven_Variable_Figure_Structure.docx` — follows the uploaded `PART V — CURRENT FIGURE` structure (main figure table and supplementary figure table), corrected for P2/K3 and current S1–S10 numbering.
- `Path_B_Elsevier_Figure_Captions.docx` — separate seven-main/ten-supplementary caption document, corresponding to Elsevier's separate-caption guidance.

Use these as review sources. Do not paste the old 5-class / 2,291-tract / Top-10 hotspot text or outdated skipped-S2 / S1–S13 numbering back into the manuscript. Current **S8** is the clustering diagnostics number; current **S9** is the priority-geography figure. Proposed Figure 7 and S8 text must be installed together with P2 artwork only after explicit promotion authority. Existing Figure 4–6 caption statistical definitions (realization percentile ranges vs bootstrap CIs) must be preserved.

## 4 — Deliverables and checks

Create only within a new `local_elsevier_review_outputs/` directory:

1. Clean B color vector PDF and its printed-size preview; exact source hashes and font/stroke/size preflight JSON.
2. Clean A texture-oriented PDF, plus (if warranted) an independently readable grayscale pairing, preserving underlying frozen tract values.
3. A/B/CVD/grayscale contact sheet reviewed at 7.2 × 9.0 inches.
4. A short, source-grounded paragraph on why P2/K3 is primary and K4 remains mandatory, including the numerical geographic-ARI contrast.
5. The two Word documents checked for table boundaries, pages, figure numbering, and caption consistency.
6. A file/sha256 manifest; explicit statement that formal Figure 7/S8, numerical outputs, simulation, and original index were NOT modified.

Stop before merging. Return final paths plus a concise QA decision and any unresolved journal-specific conditions. Do not use generic green 'PASS' language to conceal unresolved accessibility or figure-height issues.
