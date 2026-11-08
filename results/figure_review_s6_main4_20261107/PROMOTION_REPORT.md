# Complete four-panel S6 promoted to main Figure 4

## Changes

- Former S6 becomes main Figure 4, immediately after Figure 3.
- Former main Figures 4-7 become Figures 5-8.
- Supplementary S1-S5 remain unchanged. Former S7-S9 become S6-S8, leaving no numbering gap.
- The revised collection has eight main and eight supplementary figures. The complete figure/caption packet remains 16 pages, one figure and its concise caption per page.
- Captions, artwork filenames, mirrors, previews, inventories, gallery, palette figure keys, packets and manuscript reference mapping use the new numbering.

The original suite at `results/figure_review_rq_aligned_20261101/` and its original mirrors remain untouched. This is a separate author-review collection, not an overwrite of the source suite.

## Scientific preservation

The promoted Figure 4 has all four original panels, not an excerpt or a simplified reconstruction. In the later Figure 1 Stage 4 update, that one artwork pair was changed to include saved recovery-result curves; the other 15 PDF/PNG pairs remain byte-identical to their source files from commit `75cd19d4a0249d006efa00d4532762d0ee406c5a`:

- A: dynamic joint station-functionality/source-connection probability for the full network versus a fixed precomputed path.
- B: dynamic full-minus-fixed-path source-connection probability under the displayed restoration sequences.
- C: fragility-based station source access, conditional on station functionality.
- D: additional conditional reliability from alternative routes.

A/B retain the six scheduled strategies and Unconstrained displayed in the source. C/D retain the station geography, 14 Core-source markers, color scales and original conditioning. The fixed path is precomputed, not optimized again at each display time. Dynamic joint probabilities and static conditional probabilities must not be silently interchanged. These are topological model diagnostics, not delivered electricity or capacity adequacy.

The older `SOURCE_RELIABILITY_FIGURE_NOTES.md` describes several separate candidate figures, including a full-network/fixed-path scatter and an earlier two-strategy dynamic layout. Those descriptions were not substituted for the actual four-panel S6. The source plotting code and the frozen station/dynamic tables were inspected and hash-registered; the four-panel PDF itself is the immutable artwork authority.

Figure 1 Stage 4 now plots the saved population-weighted mean service-availability series for Unconstrained and Impact-first under `2pc50`, from 0 to 100 hours. The source is `provenance/legacy_outputs/stage6/recovery_curves_all_system.csv` (SHA-256 `b4a0889e12ed855f1f681b73dbb429306f513585fd00afe058480e6aa5a43922`). These are frozen modeled outputs, not a synthetic average schedule. No simulation or restoration calculation was rerun. The surrounding Figure 1 artwork was verified pixel-identical outside the Stage 4 replacement region.

The stored full-minus-fixed identity holds across all 81 dynamic summary records to a maximum absolute discrepancy of `2.220446049250313e-16`. The static table contains 92 unique stations, including 14 Core sources. No Monte Carlo, scheduling, restoration, GA or clustering calculation was rerun.

## Publication and numerical QA

Figure 4 retains its 185 x 227 mm page, embedded Arial-family fonts and minimum substantive text size of 7.5 pt. Its companion PNG is 4,371 x 5,363 pixels at approximately 600 dpi. It retains 89,336 vector drawing records and the same original image resources; maps and curves were not rasterized or redrawn.

Independent 150-dpi render comparisons of A, B, C and D are pixel-identical to the original S6. Figure 4 in the assembled caption packet retains the same scale and rendered artwork. The native-proportion figure page, packet page and full 16-page contact sheet were visually inspected: labels, legends, colorbars and geographic panels are intact, and no caption overlaps the artwork. The caption accurately distinguishes dynamic joint probabilities from static conditional station diagnostics. No text extends outside the promoted figure page.

The canonical review builder and coauthor-package builder were rerun deterministically. See `QA/NUMERICAL_AND_PRESERVATION_QA.json`, `results/figure_delivery_20261108/PACKAGE_QA.json`, and the targeted regression tests. Complete source/output artwork hashes, mapping and page registry are under this collection's `QA/` directory.

## Manuscript handoff

`MANUSCRIPT_INTEGRATION.md` supplies the insertion between Sections 4.2 and 4.3, a concise scientific bridge, and the complete simultaneous old-to-new citation mapping. The new Figure 4 caption is included in the synchronized caption registry.

No editable manuscript DOCX, main TEX, QMD or RMD is tracked in this checkout. Consequently, direct placement in the author-controlled manuscript and in-text reference replacement are prepared but not falsely reported as completed. All historical reports retain their original figure numbering. No manuscript, source data, existing scientific artifact or original figure suite is modified.
