# Final variable recommendation

**Prefer CORE3:** `emc2022_total_built_land_fraction` + `housing_5plus_share` + `scag2020_classified_land_entropy` for the physical coordinates. This is a limited three-construct set: built-surface occupancy, residential unit configuration, and classified parcel-area composition. It is not a comprehensive all-building or built-environment census.

Keep the nonphysical coordinates fixed: `B_480_hr`, `Init_Supply`, `Grid_Degree`, `Grid_Impact`, `Grid_Betweenness`, `Redundancy_HHI`, `SOVI_SCORE`, `log1p(BUILDVALUE)` and `ALR_NPCTL`. This recommendation concerns measurements, not final weights, labels or formal promotion.

## Why each coordinate enters

| variable                          | inclusion_reason                                                                                                                   |
|:----------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------|
| emc2022_total_built_land_fraction | Current modeled built-surface occupancy, with2022 observation support; use one coverage coordinate.                                |
| housing_5plus_share               | Residential unit concentration in multi-unit structures; explicit housing denominator,80 VRE, moderate SOVI overlap.               |
| scag2020_classified_land_entropy  | Adds classified parcel-area composition, not density or residential structure; actual2020 numeric overlay and lineage/coverage QA. |

The preferred minimal set is CORE2 (EMC+ACS5+). CORE3 adds a genuinely different land-use composition coordinate with an explicit classified-land support restriction. The recommendation adds composition because the research target includes community land uses, not because its k4 clusters look cleaner. The residual variance fractions after controlling the other core coordinates, SOVI and log stock are 0.619, 0.758 and 0.742. These statistics support distinguishability but do not prove independence.

## Why alternatives do not enter together

| variable                    | decision                 | reason                                                                                                                      |
|:----------------------------|:-------------------------|:----------------------------------------------------------------------------------------------------------------------------|
| building_footprint_coverage | substitute, not co-input | Detailed clipped vector rooflines; historical/mixed imagery substitute for EMC, not independent second coverage.            |
| land_use_entropy            | substitute, not co-input | SCAG2019 same-construct temporal substitute; do not co-weight with2020.                                                     |
| housing_detached_share      | substitute, not co-input | Alternative contrast within the same housing-unit composition; not exactly1 minus5+ because intermediate/other types exist. |

| variable                                    | decision             | reason                                                                                                                                                                                           |
|:--------------------------------------------|:---------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| assessor2022_actual_pre1970_main_area_share | age sensitivity only | Conditional recorded-assessment stock only. Main Square Footage, shared condominium identities, scalar year on multiple lines and exempt-stock completeness do not support complete all-use age. |
| all_use2014_pre1970_area_share              | age sensitivity only | Historical valid-age footprint stock; older mixed imagery and parcel-linked assessment fields, not independent confirmation of2022 age.                                                          |
| acs_residential_pre1970_share               | age sensitivity only | Residential housing-unit age; different population/denominator and survey uncertainty, not all-use stock.                                                                                        |

| variable                                | decision                              | reason                                                                                                                                                             |
|:----------------------------------------|:--------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| nlcd_c12_2022_impervious_fraction       | optional separately labeled extension | Verified different hardening construct includes roads. Useful explicit extension, not necessary for the declared building-coverage/configuration/composition core. |
| outline_height_area_weighted_centroid_m | optional separately labeled extension | Distinct vertical roof-height form but older mixed support and unvalidated heights; conditional historical extension only.                                         |
| jrc_anbh_positive_surface_mean_m        | optional separately labeled extension | Historical modeled height on positive cells with different support and substantial paired differences; not a second primary height coordinate.                     |

Age is omitted from the preferred primary specification. This is not a finding that age is unimportant: the all-use source population and denominator are incomplete or historical, and residential age would change the target population. The Assessor age coverage is internal to recorded main assessment area. Removing multiple-line, condominium and shared-coordinate records is a restriction diagnostic, not valid building deduplication; it retains a median 0.751 of recorded area and changes the observed-age share by as much as 0.130 at the90th percentile.

EPA stays descriptive. It measures historical household/job activity, not parcel-area composition; the tested allocation assumptions preserve totals while altering target entropy. Certified FAR is ineligible. Building count, mean area and their product are not independent coverage evidence; other housing shares share one composition; vegetation, occupancy, population density and building monetary value are not automatically physical-form coordinates. Every one of the64 entries has a disposition in FINAL_SHORTLIST_DISPOSITIONS.csv.

## Retain asset stock and loss propensity separately

Retain `log1p(BUILDVALUE)` and `ALR_NPCTL`. Asset amount and exposure-normalized multi-hazard expected-loss propensity are different research coordinates. On the common2,286 sample their Pearson correlation is 0.2457, Spearman 0.2343; marginal nonlinear overlap is 0.0623 cross-validated R². EMC/ACS/composition do not express monetary stock. EAL would intentionally combine exposure and expected losses and would remove a separately interpretable stock coordinate. ALR is not pure hazard and still reflects consequence composition/loss weighting. Do not add RISK_SCORE or the vulnerability-adjusted ALR beside mandatory SOVI.

## What remains a real decision

Decide the conceptual domain hierarchy and squared-distance budgets **before** the next comparison. Do the three physical constructs share one budget, and do stock and loss propensity share one parent budget or have separate budgets? Recovery/initial service, grid dependency and social vulnerability also require declared budgets. The current five×0.2 setting is a comparison benchmark only. See DOMAIN_WEIGHT_REQUIREMENTS.md.

## Fixed-k4 limitation

CORE3 optimization seeds are highly reproducible (pairwise median ARI 1.0000, minimum 0.9987), but spatial deletion median ARI is 0.8792, lower-tail5th percentile 0.7152, and minimum 0.6929. Up to 255 tracts change after training-overlap label alignment. The34-tract group can expand to 92 predicted members with purity 36.96%. Thus the measurements are recommended; the current equal-budget k4 partition is not established as a universally stable final typology. Do not preserve a class by changing weights or deleting Init_Supply. Any later finalist-only k check requires a separate preregistration. No further fits were launched.
