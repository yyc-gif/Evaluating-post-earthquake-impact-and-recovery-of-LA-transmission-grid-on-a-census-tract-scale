# Final Figure Style Compliance Audit — 2026-09-29

**Scope of this record.** The 44-figure counts and companion measurement CSVs
below document the earlier artwork-remediation snapshot. A separate, unapproved
meeting-preparation collection now contains 16 proposed groups (7 Main, 9
Supplement) at `provenance/artwork_drafts/`. Its 16 PDFs use embedded Arial,
have visible text of at least 7.0 pt, and contain no out-of-page text; its 16
PNG previews declare 600 dpi. All 32 draft files match their draft index hashes.
The current publication-facing authority remains `results/figures/`; the draft
collection has not replaced it or the protected July submission.
After updating the current code identity, canonical `run_all.py --resume`
passed Stages 01–10 against the unchanged publication-facing collection;
`python -m pytest -q` passed 49 tests. Neither check promotes the draft figures.

**Label-only result-table check.** The existing uncommitted change to
`results/vulnerability/EFFICIENCY_DISTRIBUTION_TRADEOFF_2PC50.csv` was compared
with the HEAD version's actual Git LFS content (old SHA-256
`49e3bbd7c1b4d48925aa01b5a66de11ac4e4103c2ae32ef1d4229615e2e40bdf`;
current SHA-256
`d077c346c58af9f3dfaccb20e6ab1c5b661b85cd31333d09ce4305a7043851d2`).
All 3 strategy IDs and all 15 numeric cells across `n`, population-weighted
burden, Q4 burden, absolute Q4–Q1 gap, and Gini match exactly as decimal values.
Only the display labels changed: `Impact first` → `Impact-first`, `Hospital
first` → `Hospital-first`, and `Vulnerability first` → `Vulnerability-first`.
This is presentation terminology cleanup, not a changed scientific result.

## Executive result

| Check | Result | Actual-output basis |
|---|---|---|
| JULY_VISUAL_IDENTITY | **PASS** | Central hierarchy/width tiers, white background, July muted strategy colors and linetypes are retained; final labels are canonical. |
| ACTUAL_OUTPUT_FONT_COMPLIANCE | **PASS for the audited snapshot and 16 new drafts** | The 44 audited PDFs and 16 new draft PDFs contain embedded Arial subsets; DejaVu Sans resources = 0 within those sets. The existing publication-facing collection is a separate authority. |
| ELSEVIER_ARTWORK_COMPLIANCE | **PASS** | Finished text, absolute line range, page bounds and hybrid raster resolutions measured from final files. The sole sub-7 text span is a 6.02 pt math subscript, above the 6 pt minimum. |
| FINAL_SUBMISSION_FILE_FORMAT_READINESS | **PASS for the audited snapshot; draft review pending** | Every figure in the 16-group draft has a PDF and 600-dpi PNG. These drafts are not yet designated as submission authority. |

The pre-consolidation remediation snapshot contained **44 unique figures** and **89 files** (44 PDF, 44 PNG, 1 SVG): **11 Main** and **33 Supplement** candidates.

## July and Elsevier standards

Protected July `Project_Visualizer.py` at `182686868cffe962739804f6bc0ccecaed73d601` was compared directly with the current shared renderer. Both use title/panel 9.5 pt, axis 8.5 pt, tick/legend/colorbar 7.5 pt, annotation 7.0 pt, axes 0.6 pt, grid 0.4 pt, default data line 1.2 pt, patch 0.5 pt, 600 dpi PNG export, TrueType PDF embedding and editable SVG text. The central nominal widths remain 89/132/185 mm.

Elsevier's official general targets are 90/140/190 mm; its sizing page calls these target sizes and advises finished normal text about 7 pt and subscripts/superscripts >=6 pt. Artwork types specifies 0.10–1.5 pt vector lines, embedded recommended fonts and vector PDF/EPS; the FAQ calls 0.25 pt recommended and 0.10 pt the absolute minimum. The IJDRR Guide for Authors endpoint was restricted during this check; no journal-specific size rule could be confirmed. The retained tiers therefore receive **PASS / Elsevier target-size compatible**, not a width-only failure.

| Standard | July | Current | Elsevier | Actual/status |
|---|---|---|---|---|
| Single width | 89 mm | 89 mm | 90 mm target | PASS / target-size compatible |
| Medium width | 132 mm | 132 mm | 140 mm target | PASS / target-size compatible |
| Full width | 185 mm | 185 mm | 190 mm target | PASS / target-size compatible |
| Lettering | 9.5/8.5/7.5/7.5/7.5/9.5/10/7 pt | same shared hierarchy | normal ~7 pt; sub/superscript >=6 pt | minimum 6.02 pt; only sub-7 is math subscript |
| Fonts | Arial-first | local Windows Arial, PDF font programs embedded | Arial/Helvetica preferred | 44/44 PDF subsets Arial; DejaVu 0 |
| Stroke widths | axes/grid/data/patch 0.6/0.4/1.2/0.5 pt | same; map borders use 0.10 pt | 0.10–1.5 pt; FAQ recommends 0.25 pt | 0.100–1.450 pt; no out-of-range selected strokes |
| Bitmap/vector | 600 dpi preview; vector PDF where possible | PDF submission authority; 600 dpi PNG preview | 300/500/1000 dpi by type; vector PDF/EPS preferred | 44 PDFs; 11 hybrid, min embedded 600 dpi; rest vector/text |

Official sources checked 2026-09-29: [Elsevier artwork sizing](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing), [artwork types](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-types), [artwork FAQ](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-faq).

Machine-readable standard rows: [standard comparison CSV](FINAL_FIGURE_STYLE_STANDARD_COMPARISON_20260929.csv).

## Workflow figure

Before remediation, the PDF had 46 text spans below 7 pt (45 below 6 pt), minimum about 4.9 pt, and 9,260 segments down to about 0.035 pt. The revised concise workflow retains the July damage → recovery → community chain and visibly includes utility-compatible mapping, realization-specific station damage/repair, source-path availability, community-burden GA, distributional outcomes, Vulnerability-first and robustness/capacity checks. Long explanation is left to the caption.

The earlier remediation snapshot measured `methodology_workflow_IJDRR.pdf` at
185.00 × 88.00 mm with 7.00-pt minimum font and 0.55-pt minimum stroke. The
subsequent tiered July-structure draft at `provenance/artwork_drafts/` measures
185.00 × 112.00 mm, 7.10-pt minimum font, and 0.55-pt minimum stroke. It
retains native vector text/path, embedded Arial, a 600-dpi preview, and an
editable SVG source derivative.

## Superseded and refreshed art

- Removed from the publication collection; source copies retained: `formal_2pc50_recovery_curves.png` (superseded by all-strategy recovery) and `formal_2pc50_mapping_burden_shift_map.png` (superseded by M1–M0 mapping-shift candidate).
- Replaced the old low-resolution `formal_2pc50_tract_T80_map.png` collection copy with `vis_formal_2pc50_impact_first_tract_T80_map.pdf` and its 600 dpi preview from frozen tract KPI/geography; `Candidate_S4_Unconstrained_T80_Map` remains separate.
- Refreshed `formal_population_burden_by_hazard` from frozen results as vector PDF + 600 dpi preview, with the complete eight strategies plus Unconstrained and no duplicated right-column labels.
- Excluded the four low-resolution embedded-panel composites: `recovery_strategy_and_topology_composite`, `recovery_vulnerability_typology_composite`, `t80_distribution_and_spatial_pattern_composite`, `topology_abstraction_and_robustness_composite`. Source/provenance copies remain; the current collection uses standalone vector/hybrid candidates.
- Excluded the obsolete GA reproducibility figure. No 180 dpi image was upsampled.

The T80/population display redraws read frozen tables only; plotted scientific values and strategy sequences did not change.

## Labels, legend and Stage 7 color access

PDF text extraction across all selected figures found none of the descriptive legacy aliases and no Direct-community. Final labels use Centrality-first, Impact-first, Betweenness-first, Degree-first, Closeness-first, Hospital-first, Random, Vulnerability-first and Unconstrained.

The Q1–Q4 all-strategy legend is above the plotting region. S18 now uses a shared three-item legend above the panels instead of point annotations that entered neighboring panels. No selected labels, legends, station names, suptitles or colorbars are clipped.

Stage 7 has five active clusters in the frozen labels file; N/A remains neutral. The normal/protanopia/deuteranopia/grayscale contact sheet is saved outside the repository at `C:\Users\yinch\.codex\visualizations\2026\09\13\01a09874-3f66-7e92-9907-bd2d73958fb9\stage7_cluster_palette_cvd_final.png`. The muted palette remains distinguishable with the labeled C1–C5 key and tract boundaries; C1/C5 are the closest simulated protanopia pair. No extra palette change or cluster change was made.

## Per-figure readiness and exceptions

- Selected outputs: 44/44 PDFs have embedded Arial subsets; DejaVu Sans resources = 0.
- Below 7 pt: Candidate_Figure_All_Strategy_Recovery.pdf: 6.02 pt: pop.
- Vector strokes: 0.100–1.450 pt; no selected stroke below 0.10 or above 1.50 pt. Workflow minimum is 0.55 pt.
- Embedded raster: 11 hybrid PDF(s); minimum effective resolution 600 dpi. Remaining PDFs are vector/text. PNG previews are [600] dpi metadata.
- PDF physical widths observed: [89.0, 128.0, 132.0, 185.0, 188.61, 188.87] mm; retained tiers are target-size compatible at finished scale.
- PDF text spans beyond page bounds: 0.
- The co-author reliability station map keeps distinct Core-source triangle markers and readable station labels; full-network/fixed-path log plot retains its 1:1 line and Supplement role; dynamic redundancy figure retains 24/48 h guides, strategy colors/linestyles and fixed-path terminology; the facility chart keeps 34 rows, low-side marker legend, 100% line and 109.04% OLINDA; capacity and S18 panels were checked without overlap/clipping.

The capacity figure's Panel C uses full canonical strategy names in a horizontal dot plot; the plotted capacity increments and burden differences are unchanged. The Q1–Q4 figure keeps all eight scheduled policies with the legend above the data region. The two contact sheets (11 Main and 33 Supplement candidates) and the selected individual previews were opened at review size; no legend/data collisions, clipped annotations, or unintended whitespace were found.

Caption handoff: keep labels short in the artwork and define D/K, Q1–Q4, SOVI, T80, Core source, full network, fixed best path, ΔR, C57, 2pc50, MW, and h in the corresponding manuscript captions.

One non-numeric artifact identity note: results/vulnerability/EFFICIENCY_DISTRIBUTION_TRADEOFF_2PC50.csv has a changed LFS object hash because its three strategy display labels were normalized to the hyphenated forms used in the figures. The three rows' numeric fields match the prior LFS object exactly; no numerical result changed. This label-only table update is separate from the artwork files.

The Stage 7 loading heatmap was rendered from the frozen pca_loadings.csv; the referenced local presentation renderer is present in the current uncommitted worktree. No PCA or clustering was rerun.

No selected renderer has an unexplained noncompliant override. Excluded legacy composite code is not a submission render route.

Detailed tables: [per-figure audit](FINAL_FIGURE_STYLE_PER_FIGURE_20260929.csv), [per-file PDF/PNG/SVG measurements](FINAL_FIGURE_STYLE_MEASUREMENTS_20260929.csv), [renderer classification](FINAL_FIGURE_RENDERER_CLASSIFICATION_20260929.csv).

## Scientific scope

Only plotting/presentation code, publication-facing figures/index, this artwork audit and canonical validation identities changed. No damage/reliability Monte Carlo, scheduling, GA, Stage 7 clustering, capacity computation or recovery experiment was rerun. Frozen physical samples, schedules, trajectories, offline numerical results, Stage 7 numeric tables, equity numbers and capacity CSV values are unchanged.
