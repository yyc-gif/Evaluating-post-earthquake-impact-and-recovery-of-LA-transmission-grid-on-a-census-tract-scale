# Revised Stage 7 Supplementary Material

Proposed addition to the verified manuscript's supplement. Use the temporary identifier Figure S_STAGE7 until the author reconciles the existing supplementary inventory. The July Supplementary Materials.docx has two different Figure S6 captions and no demonstrated current formal-simulation update; it must not be silently renumbered or treated as a confirmed current supplement.

## Saved Candidate And Cohort

The D candidate uses twelve standardized coordinates across five equally weighted domains, k=4 and seed=42. Original settings were n_init=100, max_iter=500, tol=0.0001, algorithm=lloyd. The saved labels are used without refitting, predicting the four unresolved geometries, or introducing spatial-perturbation assignments into the manuscript. The label-array SHA-256 is 484be3b577c96ab960e5f044d82dcebec1ecfb160901f7b72276daa4e0e409a7; the saved weighted-matrix hash is 55c9b9ae634ac4d39dd311abb420b812118e8154112fdd2bcf41ab9739b64e97. These are array-byte hashes, distinct from NPZ and CSV file hashes in the source manifest.

The frozen residential cohort has 2,291 tracts and 9,049,543 mapped residents; 2,287 classified tracts contain 9,037,153 residents and four unclassified tracts contain 12,390. The electricity-model domain retains all 2,315 tracts and 9,066,522 residents. The 24 tracts outside the retained typology cohort contain 16,979 mapped residents in the formal population table, so exclusion does not mean absence of residents. No denominator was changed to reconcile the older map-legend shorthand. The review-only map corrects that legend to 'Outside cohort (24 tracts)' and leaves the frozen preview unchanged.

## Measurement Coverage And Versions

Mean classified-land coverage for C1-C4 is 0.7392, 0.7265, 0.7721, and 0.7512. Mean observed-age coverage on the original 2014 outlines is 0.9486, 0.8986, 0.9399, and 0.8963. These are distinct denominators and not completeness of all tract land or all buildings. SCAG ALU uses the archived 2019.1 service; an official portal metadata page also contains a 2019.2 purpose statement. This inconsistent portal version text does not authorize substitution for the hashed source service. LARIAC metadata describes mixed historical imagery and jurisdiction-dependent 64/400-square-foot capture practices; these do not establish a single universal detection threshold for the extracted 2020 payload. No new size cutoff was imposed. The original assessor YearBuilt1 observation and its admissibility rules are not retrofit, construction-code, effective-age, or fragility assumptions.

FEMA v1.19 values refer to 2022 USD and 2020 census geography. Unadjusted ALR_NPCTL is not ALR_VRA_NPCTL and does not include the Community Risk Factor adjustment. Nevertheless it depends on exposure, annualized frequency, historical-loss information, and EAL weighting, so separation from SOVI does not demonstrate statistical independence. The saved FEMA composition audit uses 2,291 identities: pooled earthquake EAL share 98.1563%, median tract share 99.2745%. Those figures are not silently reinterpreted as statistics on the 2,287 complete-case subset. ACS 2022 five-year B25024 and B25034 remain descriptive data outside the primary coordinates; five-plus-unit housing share is not added to the D model.

## Former Five-Class Crosswalk

| Stored old class | C1 | C2 | C3 | C4 |
| --- | ---: | ---: | ---: | ---: |
| 1 | 549 | 0 | 46 | 314 |
| 2 | 42 | 0 | 110 | 31 |
| 3 | 242 | 0 | 88 | 288 |
| 4 | 17 | 0 | 407 | 119 |
| 5 | 0 | 34 | 0 | 0 |

The table covers the 2,287 common classified identities. ARI is 0.216624 (Hubert and Arabie, 1985). Stored old class 5 and candidate C2 contain the same 34 tracts, but their interpretation changes with the measurement space. Older manuscript class names and numbering are not automatically equivalent to the harmonized stored classes. Neither a global five-to-four replacement nor old top-10-by-class statistics supplies valid new evidence.

## Spatial Checks

The saved k=4 analysis comprises 20 two-block deletion cases per model on a 20-km EPSG:3310 grid, with only 17 unique deletion sets. Full-cohort ARI compares saved case predictions to each model/seed's own full-cohort partition; these are not independently sampled validation data or classification accuracy estimates. Class matching uses maximum training overlap. Median full-cohort ARI is 0.9234 for D (minimum 0.7522) and 0.9458 for the EAL alternative (minimum 0.8666). EAL is a controlled alternative measurement specification, not a replacement primary model chosen solely for its larger ARI.

Under D, the main C1/C4 contrasts in classified-land entropy and observed age, and the large C3 versus C1/C4 contrasts in SOVI_SCORE and B_480_hr, have no direction reversals in the saved 20-case summaries. Minor C1/C4 degree and impact differences reverse in 12/20 cases; they do not determine class names. T80 is descriptive: some C2-versus-other T80 rankings can reverse, so the frozen lower C2 mean is not presented as an invariant spatial distinction. Class-stability summaries use seed-specific reference memberships, not an assertion that every seeded reference has the same counts as seed42.

In the seed54 case deleting blocks 7:-23 and 7:-24, only four of C2's original 34 tracts remain in training. All original members are retained in full-cohort predictions, but the D class expands to 92 tracts and the EAL class to 90. Purity is 36.96% and 37.78%, respectively. Retention, purity, Jaccard overlap, whole-partition ARI, and optimization-seed stability describe different properties. None establishes causality or external scientific validation.

Figure S_STAGE7. Saved spatial stability and small-class specificity. Panel A shows full-cohort ARI with individual cases and median/quartile summaries; Panel B shows median retention and Jaccard with minimum-maximum ranges, not confidence intervals. Class IDs refer to each model's own seed42 partition. Panel C separates original 34 members from added members in the sparse-support case. Panel D maps the D-class expansion, with blue original members and orange additional members; these colors encode membership provenance, not the main-map class palette. Source: FIG_STAGE7_SPATIAL_ROBUSTNESS.pdf, unchanged from the validated preview.
