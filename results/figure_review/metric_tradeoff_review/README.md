# Complete metric and trade-off review (no manuscript selection)

Open **METRIC_EXPLORER.html** locally in Chrome/Edge. It is self-contained: every available policy, condition, 23 outcome fields and all 1,000 realization rows are embedded without point thinning.

| Review book | Question answered |
|---|---|
| ALL_METRIC_RELATIONSHIPS.pdf | How do all 253 metric pairs relate across policies? Baseline means in PDF; all contexts/raw realizations in explorer. |
| SAVED_PAIRED_EFFECTS.pdf | How do mean, median, empirical improvement frequency and existing bootstrap intervals differ with reference/hazard/resource/duration? |
| QUARTILE_REDISTRIBUTION.pdf | Who improves or waits longer under every executed policy, and do signed gap, absolute gap and Gini disagree? |
| SPATIAL_EFFECTS.pdf | Where do mean effects occur, how often does a tract improve, and how is population distributed? All 68 saved spatial comparisons. |
| VULNERABILITY_DEFINITIONS.pdf | Are outcomes sensitive to the six saved grouping definitions, under the same executed policies? |
| MEASURE_AND_TARGETING.pdf | Do vulnerability measures agree on score/groups/ranks, and what are the saved within-Q4 spatial distributions? |

Every book is 185 mm wide with Arial text at least 7 pt; first-page PNGs are 600 dpi previews. REVIEW_CONTACT_SHEET.pdf renders EVERY book page, four per page. It is an overview, not the readable scientific authority.

METRIC_DIRECTION_COVERAGE.csv and PANEL_SOURCE_INDEX.csv identify coverage and exact page/panel. METRIC_DEFINITIONS.md explains weighting and intervals. EVIDENCE_AVAILABILITY.md identifies actual gaps without filling them. The earlier 23-page individual-metric browser is retained at ../candidate_v2.1_layout/ALL_SUMMARY_METRICS_REVIEW.pdf.

Nothing here selects a Main/Supplement set or promotes figures. Existing results/figures and candidate layouts are unchanged. Source/index hashes and scientific-file guards are in QA_MANIFEST.json. Regenerate only this review presentation with `python results/figure_review/metric_tradeoff_review/build_review.py`.
