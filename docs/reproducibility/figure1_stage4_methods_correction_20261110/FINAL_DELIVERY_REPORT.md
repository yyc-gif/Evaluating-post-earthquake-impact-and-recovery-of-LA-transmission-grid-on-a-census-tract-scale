# Figure 1 Stage 4 correction — delivery

The Stage 4 recovery-results curves were removed from the workflow module. Stage 4 now shows an implementation-derived methods sequence: priority rules and GA task-order planning → DS > 0 repair scheduling with finite crews, realized damage-state repair durations and directed travel → repair-completion events that release crews, restore raw station functionality to 1, and pass the updated state to source-connectivity and tract-service evaluation. Unconstrained is shown separately as a parallel reference.

The corrected Figure 1 PDF is `results/figure_review_s6_main4_20261107/Main/Fig01.pdf`; its 600-dpi PNG is `results/figure_review_s6_main4_20261107/Main/Fig01.png`. The canonical sources are `src/la_grid/plotting/make_methodology_workflow_figure.py`, `src/la_grid/plotting/figure_presentation.py`, and both suite builders: `src/la_grid/plotting/build_s6_main4_review.py` and `src/la_grid/plotting/build_current_suite_p2.py`.

The Figure 1 page remains 185 × 220 mm. Stage 4 now uses the saved priority map and crew-origin/task-travel graphics, with a completion-event glyph and separate Unconstrained lane. The maps retain vector geometry; the existing travel matrix remains raster within the source PDF. At 120 dpi, every rendered pixel outside the authorized Stage 4 region is identical to the starting figure. The complete review packet remains 16 pages (8 main, 8 supplementary). Supplementary Figure S5 PDF, PNG and preview are byte-identical to the starting HEAD.

Visual comparisons: `FIG01_BEFORE_AFTER.pdf` compares the full page; `FIG01_STAGE4_DETAIL_BEFORE_AFTER.pdf` and `.png` show the old curves next to the corrected method flow. `FIG01_STAGE4_FINAL_600DPI.png` is the final native-size detail, and `FIG01_COMPLETE_PAGE_FINAL_150DPI.png` is the complete page preview.

Source implementation checks, hashes, vector checks, pixel preservation, S5 hashes, and packet counts are recorded in `FIGURE1_STAGE4_NUMERICAL_AND_PRESERVATION_QA.json`. All 15 suite and P2-builder tests passed. No simulations, restoration schedules, GA searches or scientific results were regenerated.
