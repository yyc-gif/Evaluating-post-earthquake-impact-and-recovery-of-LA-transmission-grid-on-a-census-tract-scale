# Construct and shortlist decision

Starting commit: `94faefd30273dec8318197de443f2f992fa29e5c`. The scientific selection is **CORE3**, with **CORE2** as its restricted minimal version. CORE4, AGE_ACS and AGE_HIST are age sensitivities, not mandatory upgrades. COVER_ALT, LAND_ALT and HOUSING_ALT replace measurements of a defined coordinate; HARDEN_EXT and HEIGHT_HIST_EXT change the set of physical constructs. HIST is historical reference only. Gross FAR and EPA_ACTIVITY_EXT are ineligible in this comparison for the stated definitions, not silently zero-filled.

## Identical-GEOID source comparisons

| family                             |    n |   pearson |   spearman |   mean_difference |   mean_absolute_difference |   p90_absolute_difference | units    |
|:-----------------------------------|-----:|----------:|-----------:|------------------:|---------------------------:|--------------------------:|:---------|
| coverage                           | 2286 |   0.94922 |    0.93062 |           0.03496 |                    0.03730 |                   0.06569 | fraction |
| land_use                           | 2286 |   0.99491 |    0.99580 |          -0.00091 |                    0.00522 |                   0.01388 | fraction |
| housing_contrast_not_same_quantity | 2286 |  -0.90016 |   -0.91500 |           0.15022 |                    0.51899 |                   0.93358 | fraction |
| age_different_denominator          | 2286 |   0.94153 |    0.94350 |          -0.09150 |                    0.09592 |                   0.18830 | fraction |
| age_different_population           | 2286 |   0.80375 |    0.77951 |           0.02783 |                    0.10134 |                   0.21647 | fraction |
| height_different_support           | 2286 |   0.78575 |    0.71595 |           2.17385 |                    2.66321 |                   4.17667 | m        |

Coverage difference is EMC minus LARIAC: about 3.50 percentage points. This is a source/time/model difference, not measured accuracy. Prefer2022 support for the updated occupancy coordinate; keep detailed vector outlines as the substitute. Neither product has independent LA tract accuracy certification.100m EMC boundary intersections assume the pixel's modeled density within a partial cell. LARIAC has precise roofline boundaries but mixed imagery dates and minimum-detection/segmentation limitations. The County official metadata documents earlier imagery and different capture thresholds; the2020 release name is not a uniformly2020 observation date.

SCAG2020 has actual ALU20 codes and the same11-class exclusive-area convention as2019. LU19 carry-forward represents 12.25% of county records and 36.81% of summed reported ACRES. Those are source-record diagnostics, not nonoverlapping study-land proportions. Updated code/source records and carried-forward land coexist. Mean absolute entropy change is 0.00522; most differences are small but maximum 0.20835 is material. Temporal agreement is not independent measurement validation. SOURCE_CLASSIFICATION_DIFFERENCES.csv separates actual area-composition changes from entropy summaries.

ACS5+ is preferred for a direct concentration-of-units-in-multi-unit-structures construct; detached share is a coherent substitute for detached orientation. Their Pearson correlation is -0.9002. They are not exact complements.80-replicate median90% MOEs are 0.0675 and 0.0725; large uncertainty and boundary cases remain in the sample.

Assessor2022 versus LARIAC2014 age correlation is 0.9415, with mean difference -0.0915. Parcel-linked tax-roll enrichment means these are not safely independent observations. Official LARIAC schema includes AIN, YearBuilt1, Roll_Year and assessment-value fields; exact historic join/year cardinality is not documented by the inspected metadata. Do not claim an independent age-validation study. Main Square Footage is not certified floor area. The multiple-line/condominium/restricted-stock analysis and government zero-year/zero-area patterns weaken a complete all-use age claim despite high internal valid-year coverage.

## EPA allocation evidence

| scenario                             |    n |   mean_absolute_change |   p90_absolute_change |   maximum_absolute_change |   n_absolute_change_gt_005 |   count_conservation_error_max |
|:-------------------------------------|-----:|-----------------------:|----------------------:|--------------------------:|---------------------------:|-------------------------------:|
| uniform_land                         | 2287 |                0.00000 |               0.00000 |                   0.00000 |                          0 |                        0.00000 |
| less_concentrated                    | 2287 |                0.01937 |               0.05165 |                   0.43487 |                        235 |                        0.00000 |
| more_concentrated                    | 2287 |                0.00264 |               0.00424 |                   0.33481 |                         20 |                        0.00000 |
| households_concentrated_jobs_diffuse | 2287 |                0.02098 |               0.05290 |                   0.41882 |                        250 |                        0.00000 |
| households_diffuse_jobs_concentrated | 2287 |                0.00804 |               0.01716 |                   0.34080 |                         63 |                        0.00000 |

Alternatives use donor-land weights raised to0.5 or2, with household and job concentration changed jointly or separately. These are declared allocation stress tests, not observed alternatives, accuracy estimates, or confidence intervals. Counts are conserved including outside-study residual geography. Variation therefore demonstrates the limits of conservation as spatial validation. Historical2017 jobs/2014–2018 households on2018 donors are not synchronized2022 physical-form measurements.

## Bounded comparison

| model            |   cohort_n |   full_seed_pair_ARI_median |   spatial_ARI_median |   spatial_ARI_p05 |   spatial_ARI_min |   reassigned_n_max |   D34_purity_min |
|:-----------------|-----------:|----------------------------:|---------------------:|------------------:|------------------:|-------------------:|-----------------:|
| HIST             |       2287 |                     0.99584 |              0.92345 |           0.82779 |           0.75222 |                225 |          0.36957 |
| CORE2            |       2287 |                     0.99721 |              0.94692 |           0.78251 |           0.72831 |                220 |          0.36957 |
| CORE3            |       2287 |                     1.00000 |              0.87922 |           0.71523 |           0.69293 |                255 |          0.36957 |
| CORE4            |       2286 |                     0.99595 |              0.89201 |           0.81877 |           0.64889 |                300 |          0.36957 |
| AGE_ACS          |       2287 |                     0.96853 |              0.88264 |           0.81160 |           0.80783 |                175 |          0.36957 |
| AGE_HIST         |       2287 |                     1.00000 |              0.90226 |           0.81583 |           0.66602 |                284 |          0.36957 |
| COVER_ALT        |       2287 |                     0.99035 |              0.90420 |           0.63016 |           0.57216 |                633 |          0.02136 |
| LAND_ALT         |       2287 |                     0.98789 |              0.87190 |           0.70152 |           0.69340 |                255 |          0.36957 |
| HOUSING_ALT      |       2287 |                     1.00000 |              0.91319 |           0.75641 |           0.71671 |                234 |          0.36957 |
| HARDEN_EXT       |       2287 |                     0.98400 |              0.91704 |           0.69380 |           0.66479 |                283 |          0.36957 |
| HEIGHT_HIST_EXT  |       2287 |                     0.99501 |              0.92092 |           0.71312 |           0.70277 |                246 |          0.36957 |
| CORE3_AGE_COMMON |       2286 |                     0.99721 |              0.87795 |           0.69352 |           0.68855 |                259 |          0.36957 |

All use fixed k4,n_init100,seeds42–61 and the existing20 spatial-deletion cases (17 distinct geographic sets). StandardScaler is refit only on retained training tracts. ARI is partition agreement, not accuracy; ranges are descriptive and do not treat repeated deletion sets as independent replications. HIST's20 full and20 spatial fits were reused exactly.440 new model/spatial fits and20 declared coverage fits were completed; no k search. One assessor-age-null tract,06037115103, is excluded from CORE4 and its CORE3_AGE_COMMON comparator only. Other models retain2,287. All2,291 master rows remain, including the original four geometry-unclassified tracts.

Most physical substitutions preserve the34-member full-data class, but spatial support can lead to absorption rather than disappearance. In COVER_ALT the D34 group can merge into a much larger group; that result is a fixed-k/source-sensitivity warning, not evidence that vector geometry is intrinsically inferior. Full raw contingency tables expose splitting/merging hidden by a matched class name. No-training-support cases are explicitly flagged. Original-unit profile changes distinguish fixed members after deletion from replacement members after reclustering. Minor profile rankings can reverse and must not be promoted to universal archetypes.

CORE3 coverage-only restriction trains on 1715 tracts and predicts the full2,287, yielding median ARI 0.8790 and maximum 98 changed tracts. This excludes the bottom coverage quartile as a diagnostic, not as a new admission threshold. Fixed-centroid ACS replicate predictions change a median 7.5 and maximum 15 assignments. They do not refit clusters or propagate all special boundary-model uncertainty; they are not cluster confidence intervals. SCAG_CLASSIFIED_LAND_SUPPORT_BOUNDS.csv gives feasible missing-land entropy bounds, not imputed observations.

Measurement recommendation, domain weights and final partition approval remain different decisions. The preferred set adds interpretable concepts but does not resolve the demonstrated fixed-k4 spatial limitations. Formal Stage7, manuscript, figures, physical model, schedules, trajectories and GA remain unchanged.
