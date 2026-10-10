# Stage 7 fixed-k=4 spatial validation decision — 2026-10-10

This is a bounded exploratory validation of two already specified, equal-five-domain, four-class models. It is not a new feature search, k search, formal Stage 7 replacement, or causal analysis. Parent commit: `50df10481815f3dd94c46dc9443f93cfdb1c5014`. Exactly 40 new KMeans fits reuse the 20 existing deletion sets, same seeds 42–61, n_init=100, and the same 2,287 complete residential tracts. All 2,291 original residential records remain in the source table; four unresolved geometry cases receive no imputation or labels. No source acquisition or physical/recovery/GA calculation was performed.

## Overall partition sensitivity

| model   |   full_ARI_median |   full_ARI_p05 |   full_ARI_min |   training_ARI_median |   heldout_ARI_median |   changed_n_median |   changed_n_max |
|:--------|------------------:|---------------:|---------------:|----------------------:|---------------------:|-------------------:|----------------:|
| D       |            0.9234 |         0.8278 |         0.7522 |                0.9234 |               0.9274 |            58.0000 |             225 |
| EAL     |            0.9458 |         0.8728 |         0.8666 |                0.9524 |               0.9393 |            41.5000 |             130 |

ARI is chance-adjusted partition agreement, not the percentage classified correctly. Ranges across these 20 fixed spatial perturbations are descriptive, not confidence intervals or independent validation. All comparisons use each seed own saved full-data k=4 labels. Seed 42 alignment is for presentation only. Label matching uses retained training tracts and is not reoptimized on heldout tracts. Full/training/heldout cross-tables remain available to show splitting and mixing hidden by an assigned name. No numerical pass threshold was chosen after seeing these results.

## Six required scientific judgments

**1. D maintains its main groups in most tested deletions, with a concrete weak case.** Its three large display groups have median Jaccard values shown below. Worst D seed 54 changes 225 tract assignments after training-based alignment; that is 9.84% of 2,287 records, distinct from its ARI 0.7522. This is not wholesale loss of all group structure, but it is too substantial to call geographic membership invariant.

| model   |   display_seed42_cluster |   retention_median |   retention_minimum |   purity_median |   purity_minimum |   jaccard_median |   jaccard_minimum |   majority_incoming_count |
|:--------|-------------------------:|-------------------:|--------------------:|----------------:|-----------------:|-----------------:|------------------:|--------------------------:|
| D       |                        1 |             0.9706 |              0.8543 |          0.9716 |           0.9020 |           0.9411 |            0.7963 |                         0 |
| D       |                        2 |             1.0000 |              1.0000 |          1.0000 |           0.3696 |           1.0000 |            0.3696 |                         1 |
| D       |                        3 |             0.9916 |              0.9247 |          0.9855 |           0.9502 |           0.9684 |            0.9107 |                         0 |
| D       |                        4 |             0.9660 |              0.9043 |          0.9708 |           0.8845 |           0.9396 |            0.8212 |                         0 |
| EAL     |                        1 |             0.9917 |              0.9221 |          0.9760 |           0.9169 |           0.9533 |            0.8858 |                         0 |
| EAL     |                        2 |             1.0000 |              1.0000 |          1.0000 |           0.3778 |           1.0000 |            0.3778 |                         1 |
| EAL     |                        3 |             0.9793 |              0.9369 |          0.9939 |           0.9652 |           0.9672 |            0.9063 |                         0 |
| EAL     |                        4 |             0.9951 |              0.9269 |          0.9925 |           0.9670 |           0.9815 |            0.9210 |                         0 |

**2. Lower-tail agreement is associated with particular geographic deletions, not simply how many records are removed.** D lowest run is seed 54, removing blocks 7:-23 and 7:-24 (480 records). Seed 45 removes 498 yet has ARI 0.8318; the largest deletion, seed 48 (534), has ARI 0.8682. Identical sets can recur under different seeds:42/47 and 53/57, for example. They remain 20 prescribed algorithm/deletion cases, not 20 unique independent geographic experiments. BASELINE_CLASS_SPATIAL_SUPPORT.csv and the run cross-tables identify exactly which baseline communities occupy each block.

Lowest runs in each model:

| model   |   seed | removed_blocks   |   n_training |   n_heldout |   full_ARI |   aligned_changed_n |
|:--------|-------:|:-----------------|-------------:|------------:|-----------:|--------------------:|
| D       |     54 | 7:-23;7:-24      |         1807 |         480 |     0.7522 |                 225 |
| D       |     45 | 8:-23;9:-22      |         1789 |         498 |     0.8318 |                 133 |
| D       |     59 | 8:-23;9:-23      |         1834 |         453 |     0.8503 |                 118 |
| D       |     60 | 6:-21;7:-23      |         1864 |         423 |     0.8593 |                 109 |
| EAL     |     54 | 7:-23;7:-24      |         1807 |         480 |     0.8666 |                 130 |
| D       |     48 | 6:-22;7:-22      |         1753 |         534 |     0.8682 |                 102 |
| EAL     |     59 | 8:-23;9:-23      |         1834 |         453 |     0.8731 |                  97 |
| EAL     |     45 | 8:-23;9:-22      |         1789 |         498 |     0.8968 |                  81 |
| EAL     |     47 | 6:-22;9:-23      |         2073 |         214 |     0.9212 |                  59 |
| EAL     |     42 | 6:-22;9:-23      |         2073 |         214 |     0.9291 |                  53 |

**3. The 34-member group never lacks training support and never loses its original members, but can be strongly contaminated.** D seed 42 zero-based NPZ label 1 (display C2) is identified from saved membership, not hard-coded. EAL seed 42 independently has the same 34 members (its other groups differ). Each deletion leaves 4–34 of those members in training. All 34 are retained in the corresponding full-population predicted class in every run. However, deleting 7:-23/7:-24 leaves only 4 training members; the D matched class expands to 92 with 58 incoming records (purity 34/92=0.3696), and EAL to 90 with 56 incoming (purity 0.3778). Therefore there are zero no-training-support cases; the weakness is dilution despite remaining support, not disappearance or forced preservation. Every raw cross-table and original-member destination count is retained.

| model   | feature     |   baseline_mean |      mean |   mean_change_standardized_full_cohort |
|:--------|:------------|----------------:|----------:|---------------------------------------:|
| D       | B_480_hr    |       23.601147 | 29.111084 |                               1.074106 |
| D       | Init_Supply |        0.018153 |  0.010640 |                              -3.055815 |
| D       | SOVI_SCORE  |       67.986176 | 65.427609 |                              -0.094972 |
| EAL     | B_480_hr    |       23.601147 | 28.988883 |                               1.050284 |
| EAL     | Init_Supply |        0.018153 |  0.010768 |                              -3.003808 |
| EAL     | SOVI_SCORE  |       67.986176 | 65.422556 |                              -0.095159 |

These values show substantive composition change: D small-group mean service loss rises from 23.601 to 29.111 h, and Init_Supply falls from 0.018153 to 0.010640. Init_Supply is modeled normalized initial availability, not delivered electricity. The 4-member retained-training subset and the 92-member reassigned class are separate profiles, so deletion-induced compositional change is not confused with reassignment. The high-initial-service/low-service-loss description persists in relative direction, but exact size, membership specificity and magnitudes require qualification.

**4. EAL has higher agreement on these same cases, but shares the small-group weakness.** Its median full ARI 0.9458 and minimum 0.8666 exceed D0.9234 and 0.7522; this is evidence about this fixed spatial design, not a scientific reason to collapse economic stock and loss propensity into one variable. EAL has the same 34-member special group, while seed 42 large classes are 718/919/616 rather than D 850/651/752. They are not interchangeable community taxonomies.

**5. Most reassignment occurs near descriptive class boundaries, with an important class-meaning exception.** Distance margins use full-data standardized/weighted distances to saved-label member means; the original full-data KMeans centers were not saved. They are not recovered algorithm decision margins or probabilities.

| model   |   changed_in_lowest_margin_quartile |   changed_in_highest_margin_quartile |   changed_margin_median |   unchanged_margin_median |
|:--------|------------------------------------:|-------------------------------------:|------------------------:|--------------------------:|
| D       |                              0.9596 |                               0.0000 |                  0.0355 |                    0.4632 |
| EAL     |                              0.9639 |                               0.0000 |                  0.0336 |                    0.5114 |

The seed 54 small-class expansion is more than ordinary swapping of a few boundary records: its profile changes by about +1.07 full-cohort SD in service loss and −3.06 SD in initial service (D). Full standardized center shifts, every original-unit profile, and member changes are exported. A high overall ARI cannot conceal this minority-group failure mode.

**6. Several broad descriptors persist, but fine rankings and the small-class specificity remain exploratory.** Low-SOVI versus high-SOVI large-group differences, the lowest-service-loss/high-initial-service small group, and older-building versus more mixed-land-use contrasts can be considered for manuscript integration review, using the raw profiles and direction comparisons. They are descriptive joint patterns. They do not establish that built environment causes recovery differences. Fine differences frequently reverse, particularly where their initial magnitude is small:

| model   |   display_class_a |   display_class_b | feature                        |   reversal_count |   replicates |   baseline_standardized_difference_min |   baseline_standardized_difference_max |
|:--------|------------------:|------------------:|:-------------------------------|-----------------:|-------------:|---------------------------------------:|---------------------------------------:|
| D       |                 1 |                 4 | Grid_Impact                    |               12 |           20 |                                -0.0025 |                                 0.0236 |
| D       |                 1 |                 4 | Grid_Degree                    |               12 |           20 |                                -0.0133 |                                 0.0290 |
| EAL     |                 1 |                 3 | T80                            |               11 |           20 |                                -0.0129 |                                 0.0103 |
| EAL     |                 2 |                 3 | all_use2014_pre1970_area_share |                9 |           20 |                                -0.0037 |                                 0.0120 |
| D       |                 3 |                 4 | all_use2014_pre1970_area_share |                7 |           20 |                                -0.0178 |                                -0.0128 |
| EAL     |                 1 |                 3 | building_footprint_coverage    |                7 |           20 |                                -0.0007 |                                 0.0155 |
| EAL     |                 1 |                 3 | B_480_hr                       |                6 |           20 |                                 0.0020 |                                 0.0238 |
| D       |                 1 |                 3 | housing_5plus_share            |                5 |           20 |                                -0.0685 |                                -0.0498 |
| D       |                 3 |                 4 | Redundancy_HHI                 |                3 |           20 |                                 0.0086 |                                 0.0310 |
| D       |                 1 |                 4 | Redundancy_HHI                 |                3 |           20 |                                -0.0447 |                                -0.0132 |
| EAL     |                 1 |                 4 | Init_Supply                    |                2 |           20 |                                 0.0104 |                                 0.0158 |
| D       |                 1 |                 3 | Redundancy_HHI                 |                2 |           20 |                                -0.0533 |                                -0.0399 |

Do not turn differences such as EAL C1/C3 service-loss ranking (6/20 reversals) into stable archetype labels. D C1/C4 degree and network-impact rankings reverse 12/20 times; EAL C2/C3 age ranking reverses 9/20 times. A direction change with a tiny baseline effect should not be equated with a wholesale semantic reversal; both signed standardized magnitude and membership diagnostics must be read together.

## Profile definitions and limitations

SPATIAL_K4_PROFILE_STABILITY.csv separately records (A) retained original-class training members,(B) the matched predicted class on all 2,287 tracts, and (C) the matched predicted training class. It reports mean/median/p10/p90/observedN/zero fraction, raw mean changes and changes in units of the full-cohort SD. Training total mean change decomposes into original-member deletion change plus reclassification change. Center shifts use a common full-baseline coordinate system with sqrt(0.2/domain coordinate count) weights, not changing training-scale coordinates. T80, population density and housing 5+ are descriptions only. Profile quantiles describe members, not confidence intervals.

Original baseline matrix and sample hashes reproduce exactly. Some saved full-data algorithm inertias are slightly higher than inertia about final-label means (each discrepancy is recorded in INPUT_AND_BASELINE_QA.json). This is consistent with tolerance stopping followed by final label reassignment; original centers were not saved, so the exact earlier stopping path cannot be verified. No complete baseline was refitted to erase that distinction. All new perturbations save their actual scaler mean/variance/scale, factors, KMeans centers, raw labels, baseline labels, train mask, IDs, parameters and software versions.

## Recommendation and adoption gates

Both fixed-k=4 models can enter manuscript integration review with the complete class-level and spatial limitations disclosed. This is not approval for final adoption or label replacement. D remains the provisional construct-driven specification because separate building stock and unadjusted multi-hazard loss propensity are interpretable; EAL is a compact combined expected-loss/exposure sensitivity. This choice is not an ARI/silhouette/VIF ranking. SOVI, Init_Supply and original model definitions are retained.

Substantive remaining issues are (1) geographic contamination of the 34-member class under sparse training support,(2) fine feature/order descriptions that reverse,(3) inherited measurement uncertainty in unclassified SCAG land and missing-age area,(4) explicit 2,287 complete-case rather than 2,291 full-label accounting. The last four mask cases were not a launch condition and are not recalculated here. Author review must decide whether the documented complete-case domain and qualified group descriptions are acceptable. Do not claim an invariant four-community taxonomy, unique optimal k, independent final validation, or causal built-environment effects. No algorithm, variable, weight or extra run was added to try to pass.
