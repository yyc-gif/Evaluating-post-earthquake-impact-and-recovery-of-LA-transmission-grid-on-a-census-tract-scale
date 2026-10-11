# Stage 7 construct and domain-weight final review

## Preferred scientific recommendation

Retain BE0's historical 2014 age coordinate in the **explicitly historical, descriptive reference specification**, with five equal conceptual domain budgets and D's separately interpretable economic stock/loss propensity. Its added historical-stock meaning is relevant to community characterization; it is not a building-damage predictor or a contemporaneous all-use measurement. Retention is a construct judgment, not a reward for preserving the four classes. BE1 is the meaningful physical-form/no-age comparator.

Reduce the four-class partition's manuscript role to a **weight-conditional exploratory joint profile analysis**. Do not present it as a unique or generally stable community taxonomy or assign universal archetype names. Put the continuous tract-level recovery/social relationship ahead of label-dependent conclusions. The diagnostic evidence is ready for author manuscript review under this restricted scope; an unqualified substantive four-archetype claim is not ready. This is one coherent recommendation, not a search for the empirically best intermediate weight.

## Execution and identity

Parent 13d2b8978a74246873e76c6c860ab9604100de8b; independent branch analysis/stage7-construct-weight-decision-20261010. Same 2287 complete residential GEOIDs in original saved order, within 2291 master records. The four unresolved records remain unclassified and unimputed. Fixed k=4, seeds 42-61,n_init = 100,max_iter = 500,tol = 1e-4,Lloyd; sklearn 1.5.1. D, raw-hour B, Init_Supply, grid features, SOVI and preprocessing are fixed. All 20 registered spatial cases reuse exact 20-km deletion sets; only 17 geographic sets are distinct. Spatial scalers use retained training tracts only; predictions include all 2287. Spatial class matching uses training overlap only and is never reselected using held-out tracts.

Completed exactly 240 missing intermediate fits; reused 160 endpoint runs. Intermediate-fit wall time 94.714 s. No earlier 880 fits repeated; no k search, source downloads, GIS, simulations, scheduling or GA. The four endpoint NPZ archives are copied byte-for-byte; original saved-label means remain explicitly identified where fitted full-cohort centers were absent. No baseline refit invents those centers. New intermediate actual fitted centers/scalers/labels are saved.

The decision rule was written before intermediate fits. Numerical, specification and spatial stability have separate denominators and no result-selected acceptance threshold. Empirical seed/deletion ranges are not confidence intervals or geographic accuracy. All 400 model runs are conditional computational cases, not 400 independent datasets.

## Building-age construct and measurement validity

BE0 combines classified-parcel land-use composition, observed ground-building coverage and the pre-1970 share of **valid-age building area in the original 2014 inventory**. BE1 deliberately omits historical stock composition. Historical age is not essential to predicting modeled electricity restoration, which does not simulate building damage; its contribution is descriptive characterization of community stock. That is relevant to the declared joint typology, provided the manuscript specifies the historical inventory instead of implying contemporary physical condition.

The modeled2pc50 recovery is a hazard/scenario model rather than a literal 2014 historical event. Other inputs are heterogeneous-vintage descriptors: SCAG 2019 classified parcels, a 2020 LARIAC release with older/mixed imagery, ACS 2018-2022 housing estimates, and FEMA v1.19 March 2023 exposure/loss scores. They do not form a synchronized contemporary census. Retaining age is temporally defensible only as a historical-stock coordinate. It is not appropriate for claims about current all-use age, current seismic fragility, post-event building damage, or causally explaining outage loss.

Median valid-age coverage is 95.251% of the original 2014 outlines. This supports observation of that inventory's valid-age stock, not correct construction years or representative contemporary coverage. Strict 2014-to 2020 transfer covers only 4.342% of 2020 footprint area on this cohort and cannot establish an all-use 2020 age measure. Missing age is nonrandom: the saved within-use pooled government area audit has 95.804% missing age, versus 1.031% residential; cross-use unions must not be added into one denominator. Valid-age conditioning underrepresents government/unknown-use stock and limits interpretation even when the overall median is high.

ACS 2018-2022 age uses residential housing-unit counts and survey estimates, while 2014 age uses observed all-use valid-age footprint area. Its newer vintage does not make it an interchangeable or more complete all-building substitute. The parent audit's ACS/bounds/coverage comparisons are retained, not repeated. SCAG median classified-land coverage is 75.107%; entropy describes only that classified area. Footprint coverage is ground/roof projection, not floor area or structural condition.

Historical age gains a separate stock-composition descriptor without claiming damage prediction. This gain warrants BE0 as the historically qualified exploratory reference; it does not warrant strengthening the four-class scientific claim. If the author requires contemporaneous all-use stock, BE0 fails that meaning and BE1 must be used instead; no validated modern all-use replacement is available. This condition is about the claimed construct, not a post hoc ARI preference.

Same-weight age inclusion/exclusion effects:

|   lambda_value |   n_seeds |   ARI_median |   reassigned_median |   reassigned_min |   reassigned_max |
|---------------:|----------:|-------------:|--------------------:|-----------------:|-----------------:|
|         0.0000 |   20.0000 |       0.8445 |            121.0000 |         111.0000 |         128.0000 |
|         0.2500 |   20.0000 |       0.8556 |            112.0000 |         105.0000 |         122.0000 |
|         0.5000 |   20.0000 |       0.8563 |            111.0000 |         106.0000 |         120.0000 |
|         0.7500 |   20.0000 |       0.8558 |            112.0000 |         101.0000 |         125.0000 |
|         1.0000 |   20.0000 |       0.2514 |           1038.5000 |         104.0000 |        1081.0000 |

Every tested age contrast changes memberships; that is not evidence the age coordinate is causally important or that BE0 is truer. Parent fixed-coordinate controls show median 121 reassignments when the equal physical 20% budget is redistributed, versus 78.5 when surviving physical weights remain. Content and redistribution both contribute. Original-unit age/profile changes are in BE0_BE1_CONSTRUCT_COMPARISON.csv; denominator/vintage limits remain unchanged.

## Weight sensitivity: boundaries, mergers and geographic identity

| model    |   lambda_value |   seed_ARI_median |   seed_ARI_min |   spatial_ARI_median |   spatial_ARI_p05 |   spatial_ARI_min |   target34_purity_min |
|:---------|---------------:|------------------:|---------------:|---------------------:|------------------:|------------------:|----------------------:|
| BE0_L000 |         0.0000 |            0.9958 |         0.9797 |               0.9234 |            0.8278 |            0.7522 |                0.3696 |
| BE0_L025 |         0.2500 |            0.9986 |         0.9876 |               0.9514 |            0.7686 |            0.6557 |                0.0000 |
| BE0_L050 |         0.5000 |            0.9896 |         0.9692 |               0.9280 |            0.6695 |            0.6330 |                0.0000 |
| BE0_L075 |         0.7500 |            0.9550 |         0.8890 |               0.7971 |            0.2676 |            0.2394 |                0.0000 |
| BE0_L100 |         1.0000 |            0.9320 |         0.2549 |               0.3405 |            0.2216 |            0.1881 |                0.0000 |
| BE1_L000 |         0.0000 |            0.9972 |         0.9917 |               0.9352 |            0.8217 |            0.6571 |                0.0000 |
| BE1_L025 |         0.2500 |            0.9808 |         0.9595 |               0.9295 |            0.7248 |            0.6119 |                0.0000 |
| BE1_L050 |         0.5000 |            1.0000 |         0.9812 |               0.9377 |            0.6781 |            0.6392 |                0.0000 |
| BE1_L075 |         0.7500 |            0.9616 |         0.9139 |               0.7820 |            0.3878 |            0.2334 |                0.0000 |
| BE1_L100 |         1.0000 |            1.0000 |         0.9950 |               0.8660 |            0.3488 |            0.1571 |                0.0000 |

Neighbor-step results are listed in DOMAIN_WEIGHT_RATIONALE.md and NEIGHBOR_WEIGHT_STEP_SUMMARY.csv. Early predefined steps move tens of tracts, but the 0.75-to 1 step reorganizes hundreds to over 1000. BE0 neighbor median ARI is .2400 with 1043.5 reassignments; BE1 is .4460 with 564. The equal/inherited BE0 endpoint median ARI is .212286. This is a large partition reorganization, not a consequence of moving only 34 tracts.

After removing the original 34 only from the endpoint comparison (no new fitting), median ARI is 0.1980 for BE0 and 0.3622 for BE1. Median reassignments among the other 2253 are 1053.0 and 675.0. Raw seed 42 class flows:

| be   |   reference_class |   baseline_n |   predicted_n |   intersection |   retention |   purity |   jaccard |   largest_destination_fraction | destinations       | origins            |
|:-----|------------------:|-------------:|--------------:|---------------:|------------:|---------:|----------:|-------------------------------:|:-------------------|:-------------------|
| BE0  |                 0 |          850 |          1205 |            727 |      0.8553 |   0.6033 |    0.5474 |                         0.8553 | [49, 74, 0, 727]   | [727, 0, 123, 355] |
| BE0  |                 1 |           34 |            40 |             34 |      1.0000 |   0.8500 |    0.8500 |                         1.0000 | [0, 0, 34, 0]      | [0, 34, 6, 0]      |
| BE0  |                 2 |          651 |           211 |            123 |      0.1889 |   0.5829 |    0.1664 |                         0.6129 | [123, 399, 6, 123] | [49, 0, 123, 39]   |
| BE0  |                 3 |          752 |           831 |            358 |      0.4761 |   0.4308 |    0.2922 |                         0.4761 | [39, 358, 0, 355]  | [74, 0, 399, 358]  |
| BE1  |                 0 |          645 |           641 |            336 |      0.5209 |   0.5242 |    0.3537 |                         0.5209 | [83, 336, 223, 3]  | [336, 176, 129, 0] |
| BE1  |                 1 |          847 |           871 |            629 |      0.7426 |   0.7222 |    0.5776 |                         0.7426 | [42, 176, 629, 0]  | [223, 629, 19, 0]  |
| BE1  |                 2 |          761 |           738 |            613 |      0.8055 |   0.8306 |    0.6919 |                         0.8055 | [613, 129, 19, 0]  | [83, 42, 613, 0]   |
| BE1  |                 3 |           34 |            37 |             34 |      1.0000 |   0.9189 |    0.9189 |                         1.0000 | [0, 0, 0, 34]      | [3, 0, 0, 34]      |

These raw destination/origin counts expose mergers/splits despite optimal one-to-one display matching. Many large-class boundaries change; it is not just an isolated minority-class merger. Neighbor row split entropy and full counts are saved for everyseed. Geographic block-count distributions and total-variation changes identify where matched groups expand/contract without downloading or inventing new geography. Those are member-count distributions across registered blocks, not tract physical area.

The 34-member reference set has a sparse-support problem under specific deletions. BE0lambda 0 seed 54 retains only 4 target training tracts and expands to 92, retaining all 34 but purity 36.96%. Hungarian matching failures under alternatives are explicitly distinct from disappearance: raw destination counts and a separate dominant-destination trace show where originals actually went. Some predicted groups absorb hundreds of other tracts. No weight setting establishes a generally specific 34-tract archetype. Original-member retention alone cannot support that claim.

## What the classes represent and why grid separation is low

For coordinatex_j in weighted standardized space, TSS_j=sum_i(x_ij-mean_j)^2; BSS_j=sum_c n_c(mean_cj-mean_j)^2; WSS_j=TSS_j-BSS_j. Domain contribution=sum_j_in_domain BSS_j/sum_all_j BSS_j. Units here are squared scaled distances; all tracts are equally counted. This is neither nominal budget nor population-weighted variance nor causal variable importance. Source reproduction maximum absolute error is 3.66 e-15.

| model    | domain           |   nominal_domain_weight |   between_fraction_mean |   domain_variance_explained_mean |   within_domain_fraction_mean |
|:---------|:-----------------|------------------------:|------------------------:|---------------------------------:|------------------------------:|
| BE0_L000 | grid             |                  0.2000 |                  0.0168 |                           0.0288 |                        0.9712 |
| BE0_L000 | loss_exposure    |                  0.2000 |                  0.2009 |                           0.3444 |                        0.6556 |
| BE0_L000 | physical         |                  0.2000 |                  0.1058 |                           0.1813 |                        0.8187 |
| BE0_L000 | recovery_service |                  0.2000 |                  0.2695 |                           0.4622 |                        0.5378 |
| BE0_L000 | social           |                  0.2000 |                  0.4071 |                           0.6980 |                        0.3020 |
| BE0_L100 | grid             |                  0.3636 |                  0.3841 |                           0.2867 |                        0.7133 |
| BE0_L100 | loss_exposure    |                  0.1818 |                  0.1261 |                           0.1882 |                        0.8118 |
| BE0_L100 | physical         |                  0.1818 |                  0.0520 |                           0.0775 |                        0.9225 |
| BE0_L100 | recovery_service |                  0.1818 |                  0.3890 |                           0.5805 |                        0.4195 |
| BE0_L100 | social           |                  0.0909 |                  0.0488 |                           0.1458 |                        0.8542 |
| BE1_L000 | grid             |                  0.2000 |                  0.0167 |                           0.0294 |                        0.9706 |
| BE1_L000 | loss_exposure    |                  0.2000 |                  0.1894 |                           0.3328 |                        0.6672 |
| BE1_L000 | physical         |                  0.2000 |                  0.1404 |                           0.2467 |                        0.7533 |
| BE1_L000 | recovery_service |                  0.2000 |                  0.2582 |                           0.4539 |                        0.5461 |
| BE1_L000 | social           |                  0.2000 |                  0.3953 |                           0.6947 |                        0.3053 |
| BE1_L100 | grid             |                  0.3636 |                  0.1960 |                           0.1514 |                        0.8486 |
| BE1_L100 | loss_exposure    |                  0.1818 |                  0.1854 |                           0.2864 |                        0.7136 |
| BE1_L100 | physical         |                  0.1818 |                  0.1450 |                           0.2239 |                        0.7761 |
| BE1_L100 | recovery_service |                  0.1818 |                  0.4410 |                           0.6812 |                        0.3188 |
| BE1_L100 | social           |                  0.0909 |                  0.0325 |                           0.1004 |                        0.8996 |

At equal BE0, recovery/initial service contributes 26.9525%, grid 1.6790%, physical 10.5757%, social 40.7068%, stock/loss 20.0860%. The earlier rounded 26.95/1.67/10.56/40.73/20.08 figures are close but not exactly the same 20-seed aggregation; the values above independently reproduce the actual source with the stated denominator. At inherited BE0, grid rises to 38.4090% and social falls to 4.8848%. Weighting changes which dimensions define class boundaries.

Grid's low equal-weight separation is primarily weak class-mean contrasts with substantial within-class variation, not an accidentally omitted budget. Standardization gives the grid exactly 20% of TSS. Only about 2.879% of grid-domain variance is between these classes; the remainder stays within them. Coordinate-level explained fractions are saved, along with the following descriptive associations:

| feature          |   R2_from_other_domains_in_sample |   largest_absolute_other_domain_correlation | strongest_other_feature   | interpretation                                                                  |
|:-----------------|----------------------------------:|--------------------------------------------:|:--------------------------|:--------------------------------------------------------------------------------|
| Grid_Degree      |                            0.3514 |                                      0.5367 | B_480_hr                  | linear descriptive association, not independent validation or causal redundancy |
| Grid_Impact      |                            0.1003 |                                      0.2693 | B_480_hr                  | linear descriptive association, not independent validation or causal redundancy |
| Grid_Betweenness |                            0.0752 |                                      0.1327 | Init_Supply               | linear descriptive association, not independent validation or causal redundancy |
| Redundancy_HHI   |                            0.0612 |                                      0.1727 | B_480_hr                  | linear descriptive association, not independent validation or causal redundancy |

Degree has moderate association with service loss, while the remaining grid coordinates have weaker linear overlap with the other domains. Thus some shared information exists, but the low BSS is not evidence that all grid descriptors are redundant. Continuous grid variation need not define discrete community boundaries. Increasing grid weights changes the partition, but cannot validate that change. Recovery and initial service are clustering inputs: their resulting class contrasts are not independent validation.

The equal-weight reference is best called **joint recovery/community profiles dominated by social vulnerability and initial service, with secondary physical/exposure variation**. Across the whole path, the safer label is **a weight-dependent descriptive partition**. Distinct, stable multidimensional archetypes is too strong.

## Manuscript-level finding checks

The large-group rule selects the highest/lowest mean service-loss classes among reference groups with at least 10% of cohort membership. That threshold only defines this descriptive comparison; it is not a model-admission criterion. Reference raw class labels are{'high_loss': 2, 'low_loss': 0}. Full-class display matching uses reference overlap; spatial matching is derived from own-model training overlap only. Case counts are:

| scope   |   n_tested |   supporting_n |   contradicting_n |
|:--------|-----------:|---------------:|------------------:|
| full    |        200 |            200 |                 0 |
| spatial |        200 |            193 |                 7 |

The loss/SOVI opposing direction holds in all 200 complete-cohort model-seed cases;193 of 200 spatial cases support it and 7 contradict it. Explicit contradictory cases:

| model    | scope   |   seed |   loss_difference_hr |   SOVI_difference |
|:---------|:--------|-------:|---------------------:|------------------:|
| BE0_L100 | spatial |     44 |               0.5416 |           11.9463 |
| BE0_L100 | spatial |     45 |              -2.7132 |          -14.1905 |
| BE0_L100 | spatial |     52 |               0.6462 |            9.0001 |
| BE0_L100 | spatial |     57 |               0.6639 |            8.9202 |
| BE0_L100 | spatial |     58 |               0.8013 |            8.7705 |
| BE0_L100 | spatial |     60 |               1.1660 |            9.2771 |
| BE1_L100 | spatial |     45 |               3.9036 |           26.3146 |

The full-cohort persistence does not mean identical class membership or unchanged archetype meaning. Continuously measured B and SOVI have Pearson r=-0.2189, Spearman r=-0.1821. At the respective sample 75 th percentiles,580 tracts have high loss,572 high SOVI,116 overlap;464 high-loss tracts are outside high SOVI and 456 high SOVI outside high loss. Ties are retained with>=, so high-loss membership exceeds one quarter. This is direct tract-level descriptive evidence of noncoincidence, independent of cluster weights, not a causal or universally negative social effect.

Physical class-pair direction checks:

| scope   | finding                                                 |   n_tested |   supporting_n |   contradicting_n |
|:--------|:--------------------------------------------------------|-----------:|---------------:|------------------:|
| full    | all_use2014_pre1970_area_share_pairwise_class_mean_sign |       1200 |           1057 |               143 |
| full    | building_footprint_coverage_pairwise_class_mean_sign    |       1200 |           1043 |               157 |
| full    | land_use_entropy_pairwise_class_mean_sign               |       1200 |           1180 |                20 |
| spatial | all_use2014_pre1970_area_share_pairwise_class_mean_sign |       1200 |           1043 |               157 |
| spatial | building_footprint_coverage_pairwise_class_mean_sign    |       1200 |           1030 |               170 |
| spatial | land_use_entropy_pairwise_class_mean_sign               |       1200 |           1147 |                53 |

These counts use sixreference class-pairs times 20 seeds times 10 specifications (1200 perfeature/scope). They describe sign consistency only. PHYSICAL_PROFILE_DIFFERENTIATION.csv provides actual original-unit class-mean ranges for everycase; a nonzero difference or a persistent sign alone does not establish substantive importance. Equal BE0 entropy/footprint contribute to descriptive differentiation, but neither their precise rankings nor age-based class interpretations are invariant over weights and geographic cases.

No test here validates built environment as a cause of service loss. No global stability threshold is retrofitted. Optimization reproducibility, source validity and specification validity remain separate.

## Five validity judgments

|Criterion|Judgment|
|---|---|
|Measurement validity|Inputs are credible only with classified-land, mixed-vintage footprint and valid-age 2014 limits; contemporary all-use age is not supported.|
|Construct validity|BE0 suits historically qualified joint profiles; neither BE0 norBE1 is comprehensive built environment or a damage predictor.|
|Numerical stability|Most medians are high, but lower-tail seed cases vary; optimizer repeatability does not resolve weighting.|
|Specification stability|A major endpoint reorganization occurs under both age definitions; universal four-class taxonomy is not supported.|
|Spatial stability|Large reference contrast usually persists, but7 direction reversals and minority-class expansion/merging prevent general geographic archetype claims.|

## Final answers

1. **Age:** retain 2014 age in the explicitly historical exploratory reference. It need not be a contemporary main interpretive claim; report its source/denominator and sensitivity. Do not replace it with ACS as the same measurement.
2. **BE0 versusBE1:** BE0 more fully describes joint community stock composition when historical scope is accepted. BE1 answers a narrower physical-form question and is the primary no-age comparison, not a proven scientific improvement.
3. **Equal weights:** defensible as equal conceptual-domain budgets; not objective optimality, equal empirical separation or independence. Disclose greater SOVI and lower grid emphasis relative to inherited weights and the full path sensitivity.
4. **Four classes:** conditionally interpretable at a named specification, not substantively invariant across reasonable weight choices. Avoid stable archetype names, especially the 34-tract group.
5. **Readiness:** ready for restricted manuscript integration review as exploratory supporting joint profiles; not ready for an unqualified unique/stable four-class substantive finding. Prefer the continuous recovery/social noncoincidence as the stronger descriptive result.
6. **Exact text changes:** Methods must state historical scopes, fixed cohort exclusions, Ddefinitions, formula/weights and training-only spatial matching. Results must name the reference specification, quantify reorganization and distinguish retention/purity, with continuous evidence before archetypes. Discussion must state weight dependence, vintage/missingness limits and noncausality. Supplement must contain all predefined path results, age deletion/redistribution controls and full spatial lower tails. Text proposals are in MANUSCRIPT_DECISION_OPTIONS.md; no manuscript has been edited.

There is no missing numerical input preventing this restricted decision. The unresolved scientific blocker is the stronger taxonomy claim itself, not a request for more optimization. Four source geometries remain unresolved and unclassified; contemporary all-use age remains unavailable. No promotion or formal-source changes are authorized or performed.
