# Scientific interpretation of the fixed CORE3 weight comparison

## Measurement, constructs, weights, stability and interpretation

Measurement validity is held fixed at the independently reviewed CORE3 package. Construct validity concerns how named measurements form parents; weight justification concerns a declared research emphasis; partition stability concerns the reproducibility of membership under seeds/weights/geographic deletion; interpretability concerns which joint descriptions survive. Neither stability nor low correlation identifies a unique conceptual weight. W1 is recommended for balanced parent representation; it is not selected for an ARI, silhouette, class-size or minority-retention maximum.

All five schemes use the same twelve exact input coordinates, same 2,287 GEOIDs/order, fixed k=4, n_init=100 and seeds42-61. Scaling in spatial fits uses training only. W1's 20 full and 20 spatial models were reused after exact byte/matrix/scaler/factor/prediction verification, including actual saved estimator centers. W2-W5 added exactly 160 fits. No new variable selection, k search, PCA, GIS extraction, physical simulation, scheduling or GA occurred.

## Major membership and meaning changes

| scheme   |   seed_pair_ARI_median |   seed_pair_ARI_min |   W1_same_seed_ARI_median |   reassigned_fraction_median |   spatial_ARI_median |   spatial_ARI_p05 |   spatial_ARI_min |
|:---------|-----------------------:|--------------------:|--------------------------:|-----------------------------:|---------------------:|------------------:|------------------:|
| W1       |                 1.0000 |              0.9987 |                    1.0000 |                       0.0000 |               0.8792 |            0.7152 |            0.6929 |
| W2       |                 0.9987 |              0.9701 |                    0.6623 |                       0.1233 |               0.9125 |            0.5369 |            0.5050 |
| W3       |                 0.9832 |              0.7039 |                    0.3040 |                       0.3450 |               0.7086 |            0.2854 |            0.1092 |
| W4       |                 0.9960 |              0.9878 |                    0.8252 |                       0.0599 |               0.9413 |            0.8206 |            0.8070 |
| W5       |                 0.9937 |              0.9797 |                    0.4601 |                       0.2387 |               0.9387 |            0.3729 |            0.3691 |

At seed 42, W3 sends 272/802 (33.9%) of W1 class1 into the class matched to W1 class0 and 213/650 (32.8%) of W1 class0 into the class matched to class2. This is substantial mixing of the large groups. W5 sends 305/802 (38.0%) of W1 class1 into the class matched to class2; its stock emphasis changes the separation of the two higher-SOVI groups. W4 is less disruptive at this seed but still changes memberships and profiles. No alignment is treated as scientific class equivalence.

Under W1 seed 42, original-unit class means are:

|   W1_seed42_display_class |   B_480_hr |   Init_Supply |   SOVI_SCORE |   emc2022_total_built_land_fraction |   housing_5plus_share |   scag2020_classified_land_entropy |
|--------------------------:|-----------:|--------------:|-------------:|------------------------------------:|----------------------:|-----------------------------------:|
|                         0 |   36.24881 |       0.00038 |     31.14078 |                             0.24215 |               0.28484 |                            0.33861 |
|                         1 |   35.20912 |       0.00023 |     84.16085 |                             0.33071 |               0.50614 |                            0.45326 |
|                         2 |   31.09270 |       0.00034 |     77.50606 |                             0.30052 |               0.21424 |                            0.30131 |
|                         3 |   23.60115 |       0.01815 |     67.98618 |                             0.27647 |               0.31859 |                            0.37548 |

Display IDs0-3 are diagnostic W1 seed 42 IDs, not published formal labels. Class0 has greater modeled loss and lower SOVI than classes1/2; class1 has greater five-plus share, classified entropy and built coverage than class2. These directions do not reverse in W1's 20 registered spatial perturbations. This does not mean all members persist, all dimensions are stable, or physical setting causes recovery. Across the 100 full fits, the highest-mean loss class is never the highest-mean SOVI class. This broad ordinal statement differs from a claim that the highest-loss class is always low-vulnerability: its mean SOVI shifts from 31.14 in W1 seed 42 to 56.23 in W3.

The class1-versus-class2 mean loss contrast is approximately +4.12 h under W1 but -0.64 h under W5 (median across seeds). Their SOVI contrast changes from +6.65 to -1.78 score points. This is a change in descriptive class meaning, not just boundary membership. W5 spatially reverses those within-specification loss/SOVI orders in 5/20 and 3/20 cases, respectively. Class numbering is aligned only for display and cannot fix this scientific dependence on the chosen budget.

## Nominal versus actual influence

Under W1, social vulnerability contributes a median39.98% of between-class variation, recovery/service29.15%, physical11.07%, ALR11.44%, stock5.99% and grid2.38%. These differ from nominal weights. Each coordinate's TSS/BSS/WSS is audited, and TSS=BSS+WSS uses partition means rather than pretending fitted centers exactly equal them after numerical convergence tolerance.

Only 4.16% of grid-domain variance lies between W1 classes; 95.84% remains within them. Thus weak grid separation reflects small mean contrasts relative to within-class dispersion. Recovery shares some network information: regressing B on the four grid coordinates gives in-sample linear R-squared 0.3806; degree on B/Init gives 0.3303, whereas impact/betweenness/HHI on B/Init give 0.0739/0.0199/0.0400. Shared information is partial and does not prove the grid descriptors are wholly redundant or causally unimportant.

W3 increases nominal grid budget from 0.20 to 4/11 while reducing SOVI to 1/11. Grid between-class contribution rises to22.57% and grid explained fraction to17.14%; social contribution falls to3.51%. The partition therefore changes with the research emphasis. This is not a justification to raise grid weight merely to manufacture a larger contribution.

## Stock and ALR

Stock and unadjusted ALR remain scientifically different coordinates. On this exact 2,287 primary cohort Pearson r is 0.24734 and Spearman rho is 0.23530, independently recomputed rather than assumed from the previous 2,286 cross-source cohort. W2 gives them a combined one-third budget, W4/W5 retain combined 0.20 but favor ALR/Stock. Relative to W1 these materially change membership, economic profiles and spatial lower tails. Their low correlation cannot determine their conceptual importance.

Original-unit seed 42 class medians:

|           |   ALR_NPCTL |   NRI_BUILDVALUE |
|:----------|------------:|-----------------:|
| ('W1', 0) |       79.24 |     667141054.50 |
| ('W1', 1) |       89.04 |     484266649.00 |
| ('W1', 2) |       75.19 |     350336465.00 |
| ('W1', 3) |       69.55 |     389575077.50 |
| ('W2', 0) |       78.37 |     676474150.50 |
| ('W2', 1) |       89.57 |     541363192.00 |
| ('W2', 2) |       75.64 |     322667237.00 |
| ('W2', 3) |       69.55 |     389575077.50 |
| ('W3', 0) |       83.82 |     498326914.00 |
| ('W3', 1) |       88.57 |     521604167.00 |
| ('W3', 2) |       73.09 |     393216422.50 |
| ('W3', 3) |       73.32 |     370682911.00 |
| ('W4', 0) |       79.36 |     649666393.00 |
| ('W4', 1) |       88.74 |     459672316.00 |
| ('W4', 2) |       74.38 |     372273393.00 |
| ('W4', 3) |       69.55 |     389575077.50 |
| ('W5', 0) |       78.37 |     648789462.00 |
| ('W5', 1) |       89.24 |     621563025.00 |
| ('W5', 2) |       78.71 |     311169068.00 |
| ('W5', 3) |       69.55 |     389575077.50 |

NRI_BUILDVALUE is archived source dollars; ALR_NPCTL is the unadjusted multi-hazard loss-rate percentile, not a pure hazard measure. For W1 display class1, median stock changes from about $484million to $622million under W5, while class2 changes from$350million to $311million. This is membership sorting under the stock emphasis. It does not indicate changed economic values, better measurement or a more truthful clustering.

## Spatial lower tails and the 34-tract group

W1's worst overall case is seed 56, blocks 7:-22/8:-21, with ARI 0.6929 and 255 reassignments. W3's worst is seed 45, blocks 8:-23/9:-22: ARI 0.1092, 1117 reassignments. W2/W5 have relatively high medians yet adverse cases 0.5050/0.3691 and 768/829 reassignments. These cases cannot be hidden by only reporting median ARI. Block-level changed counts, standardized center shifts and margin distributions separate large reorganizations from small boundary changes without a post-result boundary threshold.

At seed 54 the shared deletion of blocks 7:-24 and 7:-23 leaves four reference members in training:

| scheme   |   reference_group_training_n |   predicted_dominant_class_n |   retention |   purity |   number_of_destination_classes |   largest_destination_original_members |   largest_destination_total_n |   largest_destination_purity |
|:---------|-----------------------------:|-----------------------------:|------------:|---------:|--------------------------------:|---------------------------------------:|------------------------------:|-----------------------------:|
| W1       |                            4 |                           92 |     1.00000 |  0.36957 |                               1 |                                     34 |                            92 |                      0.36957 |
| W2       |                            4 |                          635 |     0.00000 |  0.00000 |                               3 |                                     24 |                           648 |                      0.03704 |
| W3       |                            4 |                          203 |     0.00000 |  0.00000 |                               2 |                                     32 |                           813 |                      0.03936 |
| W4       |                            4 |                           92 |     1.00000 |  0.36957 |                               1 |                                     34 |                            92 |                      0.36957 |
| W5       |                            4 |                          516 |     0.00000 |  0.00000 |                               3 |                                     19 |                           688 |                      0.02762 |

W1/W4 retain all 34 original members in a 92-member predicted class (purity 36.96%), absorbing 58 other tracts. Under W2/W3/W5 the training-aligned counterpart has zero original members, while the reference members have predictions in 3/2/3 other destination classes. Their largest destinations contain 24/648, 32/813 and 19/688 original/total tracts. Zero matched retention does not mean records vanished; the raw destination counts show splitting/merging and the one-to-one alignment limitation. No case lacks every member's training support: these failures occur despite four remaining members, not because support is entirely absent. No held-out rematching was used to improve these statistics.

Do not assign the 34-member group a stable archetype name. Its relatively higher Init_Supply is only about 0.01815 (1.8%) in the original full partition; it is not continuous power, independently established resilience or a verified service class.

## Boundary of the recommendation

W1 supports specification-qualified descriptions of three large groups and an explicitly fragile small subgroup. Across reasonable budgets, major membership and some meaning change substantially; the four-class taxonomy is not universally stable. SCAG diversity remains conditional on classified land, EMC remains 100 m modeled built surface, ACS retains survey/boundary uncertainty, ALR retains consequence/exposure composition, and four geometries remain unclassified. Joint clustering uses modeled recovery and cannot provide causal attribution. No independent predictive validation is claimed. Stop here: choose the declared W1 reference convention and report sensitivities; do not search new weights or k values to remove these limitations.
