> AUTHOR REVIEW - NOT FORMAL STAGE 7

# RECOMMENDED FIGURE 7D: D3

Use continuous five-policy mean total equivalent service-deficit hours, with the original frozen Q4 extent outlined. Do not use a new threshold in the main panel. Keep D2 as explicitly policy-conditioned supplementary description, and D1 unchanged as a historical reference. This recommendation does not approve formal promotion.

## Exact original intersection

All 94 original eleven-digit GEOIDs and 350,799 frozen residents are reproduced. The cohort remains 2,299 positive-population tracts / 9,066,522 residents, including eight zero-housing tracts. The frozen Q4 count is 579. The original P75 cutoff is 38.381354673814748 h; direct source-array recomputation differs by less than 1e-10 h. NumPy linear/type-7 quantiles and >= are used. The exact list is VERIFIED_ORIGINAL_94_GEOIDS.csv, not a new ranking.

| cell           |   n_tracts |   frozen_population |
|:---------------|-----------:|--------------------:|
| Q4_high        |         94 |              350799 |
| Q4_not_high    |        485 |             2048907 |
| nonQ4_high     |        481 |             1764128 |
| nonQ4_not_high |       1239 |             4902688 |

Q4 high-deficit prevalence is 16.2349%, versus 27.9651% for non-Q4. The difference is -11.7302 percentage points, prevalence ratio 0.580541, descriptive odds ratio 0.499243. Equal-tract marginal independence predicts 144.8130 intersections; 94 is only 64.91% of this benchmark. These calculations contain no spatial significance test.

Resident-weighted prevalence is 14.6184% versus 26.4613%, difference -11.8429 pp, ratio 0.552445. These are fractions of frozen residents represented by selected tracts, not actual customers without electricity or people exposed to every natural hazard. Expected represented population under weighted marginal independence is 559773.97, not a causal counterfactual.

## Policy and threshold dependence

Removing Vulnerability-first does not reverse the whole-cohort direction: four-policy R-P75 intersection is 105 / 396,205 residents, difference -9.1909 pp and ratio 0.663653. Impact-first alone gives 116 / 437,049, difference -6.6515 pp and ratio 0.750750. Hospital-first's upper-tail difference is much smaller. The magnitude is policy-dependent even when the direction survives.

| comparator                   | protocol   |   cutoff_hr |   n_high |   n_joint |   population_joint |   tract_prevalence_difference_pp |   tract_prevalence_ratio |   resident_prevalence_difference_pp |
|:-----------------------------|:-----------|------------:|---------:|----------:|-------------------:|---------------------------------:|-------------------------:|------------------------------------:|
| Five_policy_mean             | F          |    38.3814  |      575 |        94 |             350799 |                       -11.7302   |                 0.580541 |                           -11.8429  |
| Five_policy_mean             | R          |    38.3814  |      575 |        94 |             350799 |                       -11.7302   |                 0.580541 |                           -11.8429  |
| Four_policy_no_Vulnerability | F          |    38.3814  |      552 |       103 |             388330 |                        -8.31536  |                 0.681461 |                            -8.65733 |
| Four_policy_no_Vulnerability | R          |    38.1828  |      575 |       105 |             396205 |                        -9.19087  |                 0.663653 |                            -9.64044 |
| Impact_first                 | F          |    38.3814  |      519 |       112 |             417254 |                        -4.31909  |                 0.817473 |                            -4.47625 |
| Impact_first                 | R          |    37.8612  |      575 |       116 |             437049 |                        -6.6515   |                 0.75075  |                            -6.4693  |
| Hospital_first               | F          |    38.3814  |      634 |       146 |             574539 |                        -3.1562   |                 0.888757 |                            -2.98505 |
| Hospital_first               | R          |    38.7471  |      575 |       140 |             551500 |                        -1.11108  |                 0.956068 |                            -1.16335 |
| Degree_first                 | F          |    38.3814  |      684 |       152 |             554320 |                        -4.67807  |                 0.848754 |                            -6.69692 |
| Degree_first                 | R          |    39.8009  |      575 |       114 |             414373 |                        -7.11321  |                 0.734605 |                            -8.23114 |
| Betweenness_first            | F          |    38.3814  |      590 |       113 |             422983 |                        -8.21615  |                 0.703736 |                            -8.99942 |
| Betweenness_first            | R          |    38.5335  |      575 |       111 |             415851 |                        -7.80576  |                 0.710649 |                            -8.51232 |
| Vulnerability_first          | F          |    38.3814  |      660 |        94 |             350799 |                       -16.6721   |                 0.493357 |                           -16.6359  |
| Vulnerability_first          | R          |    39.3093  |      575 |        89 |             327733 |                       -12.8845   |                 0.544006 |                           -13.2504  |
| Unconstrained                | F          |    38.3814  |      255 |        47 |             177981 |                        -3.97558  |                 0.67125  |                            -3.94543 |
| Unconstrained                | R          |    35.0823  |      575 |       111 |             427851 |                        -7.80576  |                 0.710649 |                            -6.96086 |
| MeanDelta_five               | F          |    38.3814  |        0 |         0 |                  0 |                         0        |               nan        |                             0       |
| MeanDelta_five               | R          |     5.38613 |      575 |       111 |             448826 |                        -7.80576  |                 0.710649 |                            -7.78626 |
| MeanDelta_four               | F          |    38.3814  |        0 |         0 |                  0 |                         0        |               nan        |                             0       |
| MeanDelta_four               | R          |     5.74334 |      575 |       141 |             569377 |                        -0.880227 |                 0.965115 |                            -1.13639 |

Protocol F retains the original numeric P75 cutoff; R recomputes the same cohort's percentile within each comparator. Four-policy intersections are 103 (F) versus 105 (R); Impact is 112 (F) versus 116 (R). F answers an absolute-cutoff question; R answers a relative-rank question. MeanDelta is an additional-burden construct, not total burden: its meaningful quartiles are its own R cutoffs. F applied to MeanDelta is retained only as an explicitly incommensurate audit (no tract reaches the total-burden cutoff), not substantive evidence of absence of logistics burden.

Prespecified P70/P80 results preserve the negative aggregate five- and four-policy direction; magnitudes and memberships change. Four-policy P70 selects 705 rather than 690 due to tied values. Thresholds must not be forced to exact group sizes. Alternative quantile definitions/inclusivity and 3/6/12-digit rounding are separately audited, rather than rounded before classification.

## Baseline, quartile and geographic composition

Five-policy Q4 minus Q1 mean deficit is -2.9473 h. It decomposes into an Unconstrained difference of -1.4878 h plus a mean constraint-increment difference of -1.4596 h. Excluding Vulnerability-first weakens but does not remove the mean difference. Q3 and Q4 are not perfectly monotone, and an average difference is not a statement about every tract.

Geographic composition is a major limitation. Within mixed-group 5-km common-support blocks, the standardized difference is slightly positive; at 10 km it is near zero/slightly negative. These calculations cover different subsets (1,075 / 1,723 tracts), use common block weights, and are not causal adjustments or full-cohort replacements.

| grouping    | weighting   |   common_support_tracts |   common_support_population |   standardized_difference_pp |   standardized_prevalence_ratio |
|:------------|:------------|------------------------:|----------------------------:|-----------------------------:|--------------------------------:|
| block_5000  | tract       |                    1075 |                     4142777 |                     0.631666 |                        1.0347   |
| block_5000  | resident    |                    1075 |                     4142777 |                     0.496584 |                        1.03043  |
| block_10000 | tract       |                    1723 |                     6720531 |                    -0.282949 |                        0.987432 |
| block_10000 | resident    |                    1723 |                     6720531 |                    -0.86231  |                        0.958396 |

The global five-policy burden has descriptive Moran I=0.8843; frozen SOVI I=0.5745, using symmetric 8NN internal-point support with row-standardization. No IID tests, spatial p-values or hotspot inference are asserted. Global direction after leaving individual geographic blocks out is a descriptive robustness check, not proof that local associations have the same direction.

| grouping     | test                                     |   min_difference_pp |   max_difference_pp |   comparisons |
|:-------------|:-----------------------------------------|--------------------:|--------------------:|--------------:|
| block_10000  | leave_group_out_F_original_numeric       |            -13.9558 |            -9.76085 |            47 |
| block_10000  | leave_group_out_R_full_comparator_cutoff |            -13.9558 |            -9.76085 |            47 |
| block_10000  | leave_group_out_R_recomputed_remaining   |            -16.1072 |            -8.05014 |            47 |
| block_5000   | leave_group_out_F_original_numeric       |            -14.29   |           -10.6878  |           150 |
| block_5000   | leave_group_out_R_full_comparator_cutoff |            -14.29   |           -10.6878  |           150 |
| block_5000   | leave_group_out_R_recomputed_remaining   |            -14.0812 |           -10.1043  |           150 |
| broad_region | leave_group_out_F_original_numeric       |            -19.1658 |            -7.08636 |            10 |
| broad_region | leave_group_out_R_full_comparator_cutoff |            -19.1658 |            -7.08636 |            10 |
| broad_region | leave_group_out_R_recomputed_remaining   |            -17.511  |            -5.68886 |            10 |

K3 C1 contains no high-deficit tract at this cutoff and many Q4 tracts. Of the 94 intersections, 93 are in C3 and one in C2. Within C3 the Q4 high-deficit prevalence is higher, whereas within C2 it is lower. This is a composition-dependent reversal, not independent validation of K3: SOVI and recovery are already fitted coordinates. The K4 38-tract initial-state exception contains no selected high-deficit tract and does not explain the negative association by itself.

## Decision and remaining approval

D3 communicates continuous modeled burden and vulnerability geography without converting a source-/policy-dependent association into a binary priority rule. It remains conditional on the frozen hazard, network, mapping, resources and finite five-policy set, including Vulnerability-first. Equal policy weights are descriptive design weights, not future adoption probabilities, and the arithmetic mean is not a physical average schedule. D2 remains valid descriptive supplementary evidence but is not an unusually high overlap, a significant spatial hotspot, a composite risk score or an intervention priority. Author approval of D3, NCV14/H2/K3 with K4 sensitivity, and the active manuscript path is still required.
