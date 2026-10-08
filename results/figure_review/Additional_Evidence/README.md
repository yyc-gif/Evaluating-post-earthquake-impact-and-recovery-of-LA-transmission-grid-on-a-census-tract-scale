# Additional metric and spatial evidence

Open **METRIC_EXPLORER.html** locally in Chrome/Edge. It is self-contained: every available policy, condition, 23 outcome fields and all 1,000 realization rows are embedded without point thinning.

| Review book | Question answered |
|---|---|
| [SCE supported-geography results](../../capacity/SCE_SUPPORTED_GEOGRAPHY/README.md) | What is the capacity-induced service loss on strict-SCE supported and OLINDA-affected tracts? Integrated into the current complete figure set as S8; numerical domain tables are in results/capacity/. |
| ALL_METRIC_RELATIONSHIPS.pdf | How do all 253 metric pairs relate across policies? Baseline means in PDF; all contexts/raw realizations in explorer. |
| SAVED_PAIRED_EFFECTS.pdf | How do mean, median, empirical improvement frequency and existing bootstrap intervals differ with reference/hazard/resource/duration? |
| QUARTILE_REDISTRIBUTION.pdf | Who improves or waits longer under every executed policy, and do signed gap, absolute gap and Gini disagree? |
| SPATIAL_EFFECTS.pdf | Where do mean effects occur, how often does a tract improve, and how is population distributed? All 68 saved spatial comparisons. |
| VULNERABILITY_DEFINITIONS.pdf | Are outcomes sensitive to the six saved grouping definitions, under the same executed policies? |
| MEASURE_AND_TARGETING.pdf | Do vulnerability measures agree on score/groups/ranks, and what are the saved within-Q4 spatial distributions? |

Every book is 185 mm wide with Arial text at least 7 pt; first-page PNGs are 600 dpi previews. REVIEW_CONTACT_SHEET.pdf renders EVERY book page, four per page. It is an overview, not the readable scientific authority.

METRIC_DIRECTION_COVERAGE.csv and PANEL_SOURCE_INDEX.csv identify coverage and exact page/panel. METRIC_DEFINITIONS.md explains weighting and intervals. EVIDENCE_AVAILABILITY.md identifies actual gaps without filling them. ALL_SUMMARY_METRICS_REVIEW.pdf covers every saved primary outcome field in 23 pages; SUMMARY_METRIC_REVIEW_INDEX.csv and ALL_SUMMARY_COLUMN_COVERAGE.csv identify the fields and available cases.

Nothing here selects a Main/Supplement set or promotes figures. The 20 numbered figures are in ../Main/ and ../Supplement/; this directory preserves additional information directions rather than alternate layouts. Source/index hashes and scientific-file guards are in QA_MANIFEST.json. Regenerate only this review presentation with `python results/figure_review/Additional_Evidence/build_review.py`.

Q4_Q1_Definitions.pdf explains signed versus within-realization absolute group gaps. The additional evidence is retained because relationships between metrics, alternative grouping definitions and all saved spatial comparisons are not exhausted by the numbered figures.

## Complete cross-hazard policy contrasts

[Cross_Hazard_Policy_Contrasts.pdf](Cross_Hazard_Policy_Contrasts.pdf) retains the complete four-scenario policy evidence formerly shown in S11. The numbered S11 provides a compact 2pc50 view; no historical-scenario result was deleted. Refer to the S11 caption for the estimands and limits on cross-hazard interpretation.
