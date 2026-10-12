# Statistical and robustness evidence for K
AUTHOR REVIEW - NOT FORMAL STAGE 7

## Registered analysis

Common 2,299-tract positive-frozen-population cohort; six paired policies; seven-variable A and registered six-variable minus-Init. K=1 inertia, K=2-8 partitions; five fixed seeds (42-46), k-means++, n_init=50, Lloyd, max_iter=500, tol=1e-4. Standardization uses cohort mean/population SD and square-root squared-distance budgets. All silhouettes use the full 2,299 observations and weighted Euclidean distances. 960 individual fit records include 80 exact aliases for Impact-first's identical scaling rules: 880 distinct fits, plus 672 spatial training perturbation fits. All labels and per-tract silhouettes are saved.

The primary rule is per-policy scaling; a separate fixed Impact-first scaler test keeps the affine metric fixed. Its fixed coefficients still follow the declared budgets, but policies with larger RQ2 variance contribute more realized distance under that scaler. Therefore its WCSS/silhouette values cannot be read as evidence that a policy/scaler is scientifically better. All source data and RQ1/RQ3 coordinates remain fixed.

## Elbow

The normalized endpoint-chord diagnostic uses g(K)=(I1-IK)/(I1-I8)-(K-1)/7. Its maximum is a reproducible bend candidate, not an automatic selection or a significance test. It depends on the registered endpoint range. The curve is smooth; there is no sharply separated universal elbow.

Impact-first A:

|   k |   mean_WCSS |   relative_reduction_from_previous |   fraction_K1_inertia_removed |   chord_gap |
|----:|------------:|-----------------------------------:|------------------------------:|------------:|
|   1 |    2299     |                           nan      |                        0      |      0      |
|   2 |    1866.72  |                             0.188  |                        0.188  |      0.1567 |
|   3 |    1614.54  |                             0.1351 |                        0.2977 |      0.1885 |
|   4 |    1406.46  |                             0.1289 |                        0.3882 |      0.1898 |
|   5 |    1239.33  |                             0.1188 |                        0.4609 |      0.1628 |
|   6 |    1082.11  |                             0.1269 |                        0.5293 |      0.1289 |
|   7 |     946.425 |                             0.1254 |                        0.5883 |      0.08   |
|   8 |     855.718 |                             0.0958 |                        0.6278 |      0      |

K4 has the largest chord gap (0.18984), but K3 is almost equal (0.18853); a gap difference of only about 0.00131 does not sharply establish K4. K4->5 still reduces WCSS by 11.88%. The second-stage K5->6 reduction is 12.69%, so the curve does not justify claiming a definitive plateau at K4.

## Silhouette and disagreement

Policy-specific primary A preferences:

| policy              |   endpoint_chord_elbow_candidate |   maximum_mean_silhouette_k |   maximum_mean_silhouette | elbow_and_silhouette_agree   |
|:--------------------|---------------------------------:|----------------------------:|--------------------------:|:-----------------------------|
| betweenness-first   |                                3 |                           2 |                    0.3063 | False                        |
| degree-first        |                                3 |                           2 |                    0.3425 | False                        |
| hospital-first      |                                3 |                           5 |                    0.2859 | False                        |
| impact-first        |                                4 |                           5 |                    0.2829 | False                        |
| random              |                                3 |                           3 |                    0.2975 | True                         |
| vulnerability-first |                                2 |                           3 |                    0.3295 | False                        |

Fixed Impact-first scaling:

| policy              |   endpoint_chord_elbow_candidate |   maximum_mean_silhouette_k |   maximum_mean_silhouette |
|:--------------------|---------------------------------:|----------------------------:|--------------------------:|
| betweenness-first   |                                3 |                           4 |                    0.3601 |
| degree-first        |                                2 |                           3 |                    0.4479 |
| hospital-first      |                                3 |                           2 |                    0.4084 |
| impact-first        |                                4 |                           5 |                    0.2829 |
| random              |                                2 |                           2 |                    0.3809 |
| vulnerability-first |                                3 |                           2 |                    0.3177 |

For Impact-first, silhouette favors K5 (0.28294), not K3 (0.24972) or K4 (0.26831). These are modest separations, not evidence of natural universally separated types. Elbow prioritizes diminishing total distance reduction; silhouette favors compactness and nearest competing-class separation. Sparse initial-state isolation, skewed logistics burdens and policy-specific covariance can make their preferences differ. The reference/scaler choice changes both preferences.

## Impact-first transparent evidence matrix

|   k |   silhouette_mean |   negative_fraction_mean |   seed_ARI_min |   spatial_full_ARI_min |   spatial_full_ARI_median |   policy_pair_ARI_median |   min_class_tracts |
|----:|------------------:|-------------------------:|---------------:|-----------------------:|--------------------------:|-------------------------:|-------------------:|
|   2 |            0.267  |                   0.1509 |         1      |                 0.7896 |                    0.9126 |                   0.284  |                808 |
|   3 |            0.2497 |                   0.107  |         1      |                 0.5966 |                    0.7053 |                   0.416  |                141 |
|   4 |            0.2683 |                   0.1356 |         0.9903 |                 0.6161 |                    0.728  |                   0.4821 |                 34 |
|   5 |            0.2829 |                   0.0679 |         0.9937 |                 0.516  |                    0.701  |                   0.5374 |                 34 |
|   6 |            0.2728 |                   0.0574 |         0.638  |                 0.5978 |                    0.7353 |                   0.5255 |                 12 |
|   7 |            0.2268 |                   0.0484 |         0.9971 |                 0.3762 |                    0.7298 |                   0.5487 |                 12 |
|   8 |            0.2297 |                   0.0545 |         0.9991 |                 0.7428 |                    0.8061 |                   0.5703 |                 12 |

The complete matrix includes every policy, specification, scaler and K2-8. Spatial testing uses the same frozen TIGER internal-point UTM quadrants, all tracts retained for prediction, seed42, and scaler refitting only on training tracts for the policy-cohort rule. Four coarse leave-out tests are sensitivity checks, not independent geographic validation or spatial bootstrap confidence intervals. Fixed-scaler tests intentionally retain the full Impact scaler. Geographic source points are consistent for all 2,299 tracts; no old geometry exclusions are inherited.

## Scientific readings of K2-8 under Impact-first

| K | Scientific reading and limitation |
|---|---|
| 2 | Broad lower/higher burden contrast; strong coarse spatial agreement, but merges the high-logistics-burden group and heterogeneous structural/vulnerability patterns. One class has many negative silhouettes. Too coarse for the requested joint interpretation. |
| 3 | Parsimonious majority high-SOVI/lower-deficit class, structurally higher-impact/lower-SOVI class, and high-extra-logistics-deficit class. Useful coarse operational summary; not the statistical optimum and does not expose the extreme spectral-impact class separately. |
| 4 | Mostly extracts the 34-tract Q-dependent initial-state group from K3. Weak elbow advantage; a large heterogeneous class still has poor silhouette. Its extra type is conditional on a Core proxy and strong standardization leverage. |
| 5 | Adds a substantially high-spectral-impact class while separating low-SOVI tracts from the high-SOVI majority; retains the high-logistics class and Q rare state. Highest Impact silhouette, strong initialization stability. Spatial and policy memberships remain conditional. |
| 6 | Further subdivisions include a 12-tract extreme class; five-seed minimum ARI falls to 0.638. No overall silhouette improvement over K5. Does not justify a primary six-type selection. |
| 7 | More subdivisions, lower silhouette, a 12-tract class and weakest tested Impact spatial minimum (0.376). No demonstrated added joint-RQ construct. |
| 8 | More finely partitioned groups and improved coarse spatial agreement versus K7, but silhouette remains lower than K5 and a 12-tract class remains. No new scientific construct requires these extra subdivisions. |

Class means/medians/P10/P90, represented population and all frozen Q1-Q4 compositions are supplied for every primary K and policy. These are descriptions of inputs/shared frozen outputs, not independent validation. No formal class IDs or old manuscript narrative are acceptance criteria.
