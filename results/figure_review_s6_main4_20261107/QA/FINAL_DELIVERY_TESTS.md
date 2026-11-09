# Figure-suite delivery verification

## Scope

Starting branch: `review/s6-main4-20261107`

Starting HEAD: `cca25c78ec43d44e2e70696a3980f4217b8f0ff4`

Canonical review builder: `src/la_grid/plotting/build_s6_main4_review.py`

The builder was run after the final Figure 1, Figure 8, and Supplementary Figure S5 changes. Figure 1 was inspected as a rendered page at its native 185-mm width. The four execution steps fit in the existing Stage 4 area; the process text is Arial 7 pt. The builder's pixel check confirms all Figure 1 content outside that authorized panel is unchanged.

## Artwork and packet checks

- Updated artwork: Figure 1 Stage 4 process schematic; Figure 8 separate Panel C and D legends; Supplementary Figure S5 four-policy sensitivity comparisons.
- The 13 other numbered artwork pairs are byte-identical to their pinned source payloads. `ARTWORK_PRESERVATION.json` records source and output SHA256 separately for all 32 PDF/PNG files; the three changed pairs are explicitly non-identical.
- Figure 8 has one `N/A (16)` key under Panel C and a gray line key under Panel D. The exact frozen Q4 definition and full 38.38135467381475-hour cutoff definition are in the caption.
- The complete suite contains eight main and eight supplementary figures; the main, supplement, and combined figure-caption packets contain 8, 8, and 16 pages.
- PDFs remain vector outputs. Figure 4, promoted from S6, is byte-identical at the PDF object/stream and rendered-pixel levels.

## S5 scientific checks

`S5_VULNERABILITY_FIRST_METHODS_QA.md`, `S5_VULNERABILITY_ARCHIVE_AUDIT.json`, and `S5_VULNERABILITY_PLOT_DATA.json` record the realization pairing, source hashes, numerical identities, counterfactual definitions, and plotted values. All four compared strategies use the same 1,000 frozen physical realization identities and the same damage-state and duration hashes. Vulnerability-first's unavailable mapping-cutoff and threshold counterfactual result files were reconstructed from its frozen event-state records; no damage, schedule, or service simulation was rerun. The empirical P05-P95 bars are paired realization ranges, not confidence intervals.

The event archive is a manifest-bound local dependency outside a clean Git clone. Its exact path and source hashes are recorded in the archive audit; the generated data and methods QA are included here.

## Tests

`python -m pytest tests/test_s6_main4_promotion_20261107.py -q`: **11 passed**.

An additional run of `tests/test_current_figure_suite_integration.py` produced 34 passed and 41 failed. That legacy suite targets a different current-suite directory and pinned baseline (including absent paths under `results/figure_review/`); it does not target this isolated S6/Main-Figure-4 review package. No tests were removed or weakened. The branch-specific tests validate this package's inventory, source/output hashes, Figure 1 process, Figure 8 legends, S5 pairing, captions, and packet counts.

No simulation, restoration schedule, optimization, or clustering fit was run. No manuscript or formal scientific result was edited.
