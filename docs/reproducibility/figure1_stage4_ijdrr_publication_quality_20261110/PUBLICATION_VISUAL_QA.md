# Figure 1 Stage 4 Publication Review

## Scope

This is a presentation-only update on `review/s6-main4-20261107`, starting from `c4cbc842c605067654511cf3a4461890dea523ef`. Stages 1-3 remain in their original positions and are pixel-identical in the generator's 80-dpi comparison. Stage 4 is expanded to a full-width row; Stage 5 is reflowed below using its three original result graphics as vector crops. Figure S5 and all scientific inputs are preserved.

## Printed-Size Review

- Figure 1 page: 185.0 x 265.29 mm; the PDF is one page. The width is within Elsevier's general 190-mm double-column artwork width. The height uses most of a portrait page; no maximum height was available from the retrieved general guide, so confirm final page-fit with the journal's typesetting workflow.
- Stage 4 panel: 505.4 x 132 pt (about 178.2 x 46.6 mm), placed across the full 185-mm figure width.
- Stage 4 minimum extracted text: 7.5 pt; map rank markers: 8 pt. Stage 1-3 retained text has a 7-pt minimum; reflowed Stage 5 text has a 7.5-pt minimum. Figure text uses Arial.
- Full-page export: 4371 x 6267 px at 600 dpi. The separate Stage 4 preview is 4212 x 1100 px at 600 dpi. The PDF retains vector page content; the PNG is the requested raster review/submission companion.
- The full page and the Stage 4 detail were inspected at the 185-mm print width. The Impact-first map's five rank markers are distinguishable. The Gantt shows two labeled crews, four task bars, directed-travel marks, repair bars, completion labels, and 0/15/30/45-hour ticks. Short travel durations remain short on the shared time scale but are separately keyed in gray. The completion-event branch explicitly shows crew release, raw station functionality restored to 1, and downstream source-gate and tract-service updating.
- Stage 4 and Stage 5 have comparable vertical allocations (132 pt and 120 pt of body area, respectively). No labels are clipped in the inspected full-page render.

## Figure Logic and Frozen Events

Stage 4 follows `Priority Rules -> Repair Scheduling -> Completion Events`. The map is an authentic Impact-first example from Supplementary Figure S7; its five rank positions are unchanged and the labels are redrawn at 8 pt. Other network/community rules, Vulnerability-first and the GA supply station priority orders; Unconstrained remains a separate parallel reference.

The schedule excerpt is from the saved `2pc50/C57_D1`, evaluation realization 0 record. It shows crews 5 and 9, two of the 57 modeled crews. The scheduler filters to DS>0 tasks and uses crew availability, directed travel, and realized DS-specific repair duration. It is not a newly run schedule. Saved completion times shown are 18.154886, 30.628466, 17.870646, and 42.936823 h; the axis extends to 45 h. The completion-state logic is from `src/la_grid/revision/r1_realization_scheduling.py`; the priority/GA context is from `src/la_grid/revision/r1_ga_revision.py`.

Saved schedule archive: commit `6cfccca37cde7a53b909067caaaadea256cfd226`, `Formal_Experiment_20260923/Formal_Schedule_Prepass/2pc50__C57_D1__impact-first.npz`, SHA256 `43fcd2150510a4823f899f59f1446edc47abfe8fb1caadc740a81a2114381222`. The builder independently checks the archive manifest, 1,000 schedules, priority sequence, modeled 57-crew resource record and completion arithmetic. No simulation or schedule was rerun.

## Publisher Guidance

Elsevier's [general artwork-sizing guidance](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-sizing) says normal text should generally finish at 7 pt, keys and details must be discernible, and lists 190 mm as double-column width. Its [artwork overview](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-overview) recommends PDF for artwork and Arial/Helvetica among preferred fonts. The Figure 1 PDF is the vector master; the 600-dpi PNG accompanies it. These general recommendations are not a declaration of journal-specific compliance. The [IJDRR Guide for Authors](https://www.sciencedirect.com/journal/international-journal-of-disaster-risk-reduction/publish/guide-for-authors) endpoint returned HTTP 403 in this audit, so any additional journal-specific page-height or file rules remain unverified.

## Outputs

- Final vector figure: `results/figure_review_s6_main4_20261107/Main/Fig01.pdf`
- Final 600-dpi PNG: `results/figure_review_s6_main4_20261107/Main/Fig01.png`
- Full-page 150-dpi print preview: `results/figure_review_s6_main4_20261107/Page_Previews/Fig01.png`
- Stage 4 vector detail and 600-dpi PNG: `results/figure_review_s6_main4_20261107/QA/FIG01_STAGE4_METHOD_PANEL.pdf` and `.png`
- Before/after comparison: `results/figure_review_s6_main4_20261107/QA/FIG01_BEFORE_AFTER_COMPARISON.pdf` and `.png`
- Rebuilt figure-and-caption packet: `results/figure_review_s6_main4_20261107/ALL_FIGURES_WITH_CAPTIONS.pdf` (16 pages in this review suite)
- Machine-readable generator, source, numerical and preservation audits: `results/figure_review_s6_main4_20261107/QA/NUMERICAL_AND_PRESERVATION_QA.json` and `SOURCE_IDENTITIES.json`

## Preservation and Tests

Compared with the starting commit's Git LFS object SHA256 values, only `Main/Fig01.pdf` and `Main/Fig01.png` changed among the 16 numbered PDF/PNG artwork pairs. Figure S5 PDF, PNG and page preview match their starting hashes exactly. The supplementary packet hash is unchanged. No manuscript, simulation, restoration schedule, or scientific result file was changed.

The branch-specific Figure 1 test `test_figure1_stage4_is_implementation_derived_method_flow` passed. A combined run of this branch's S6 promotion tests and `test_current_figure_suite_integration.py` reported 21 passed and 58 failed. Those failures are in the latter test file, which hard-codes the absent `results/figure_review/` suite and unrelated `results/diagnostics/1021/` paths; it is not routed to this branch's `results/figure_review_s6_main4_20261107/`. The full current-suite test file therefore remains an unresolved routing mismatch, not a passing validation claim.

Rebuild command:

```powershell
python src/la_grid/plotting/build_s6_main4_review.py
```

The builder reuses S5's existing PDF, PNG and preview bytes and skips writes when output bytes already match. It generates Stage 4 from the workflow builder and frozen schedule archive.
