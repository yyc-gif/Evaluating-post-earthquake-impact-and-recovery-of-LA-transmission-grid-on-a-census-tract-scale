# Incremental information is not admission by itself

AUTHOR REVIEW - NOT FORMAL STAGE 7

| target                            |   n_common_complete_cases |   all_other_core_conditional_linear_R2 |   VIF |   fivefold_nonlinear_predictive_R2 |   fivefold_15km_block_nonlinear_R2 |   P2_only_R2_on_common_cohort |
|:----------------------------------|--------------------------:|---------------------------------------:|------:|-----------------------------------:|-----------------------------------:|------------------------------:|
| tract_seismic_PGA                 |                      2032 |                                0.3389  | 1.513 |                            0.7611  |                            0.4094  |                       0.2639  |
| Wildfire_high_land_fraction       |                      2032 |                                0.1135  | 1.128 |                            0.3649  |                            0.07736 |                       0.08853 |
| Flood_SFHA_land_fraction_complete |                      2032 |                                0.07508 | 1.081 |                            0.07864 |                            0.02104 |                       0.06442 |
| Historical_heat_days_2018_2022    |                      2032 |                                0.4677  | 1.879 |                            0.7554  |                            0.3657  |                       0.4166  |

Full pairwise-count and common2032cohort Pearson/Spearman matrices are exported. Common-cohort conditional linearR2/VIF and fixed ExtraTrees diagnostics quantify predictive overlap, not causality or independent validation. RandomCV can exploit spatial shared patterns;15kmblockCV is reported separately. No parameters are tuned to make a candidate eligible. Missingness can affect these comparisons: fulleligible and completecase counts are never conflated.

Wildfire and flood have low pairwise linear association with each other(r=-0.0029on2032tracts), and historicalheat has weak marginal association with SOVI(r=-0.0625on2299). Thus non-earthquake context is demonstrably not identical to SOVI, Population or PGA. PGA/heat nevertheless have shared geography and meaningful overlap with existing recovery inputs: earthquake-PGA versus B_Unconstrained Pearson0.4433(n2294), heat versus B_Unconstrained -0.4164(n2299), heat versus MeanDelta0.3715. These are empirical frozen-model associations, not causal heat effects on earthquake restoration.

Known-flood SFHA area is extremely concentrated: its highest1%accountsfor75.71%of standardized variance; zmax14.44. This is a physical-area distribution and requires sensitivity awareness, not clipping or automatic rejection for poor cluster quality. It does not justify inserting a forced equal-rank composite. Original-unit distributions, exactzero fractions and standardized leverage are reported separately.

No multi-hazardHcoordinate is constructed. Ordinal long-term fireseverity, designfloodzone fractions, probabilisticPGA and relative-threshold historicalheat are not a common probability/time horizon. A transparent relative screening index could be defined with author-approved semantics, but normalization alone does not establish a coherent construct; incomplete federal/fire and undeterminedflood geography cannot be interpreted as zero. The predeclared equal-hazard percentilerank option was conditional and is not executed. No exact H-specific influence/leave-hazard-out clustering is claimed because there is no admitted Hcoordinate.

FamilyEprovides a separate actual contribution diagnostic: earthquake pooled share 98.165356%, wildfire 1.165852%, tornado 0.427680%; remaining contributions are exported. EAL leave-one-hazard-out shows the loss-based composition's sensitivity and is explicitly not a physical-composite normalization experiment. ALR_NPCTL reduces stock scaling but retains expected-loss weights; neither EAL nor ALR is promoted as a substitute Hmeasurement. RISK_SCORE remains excluded.
