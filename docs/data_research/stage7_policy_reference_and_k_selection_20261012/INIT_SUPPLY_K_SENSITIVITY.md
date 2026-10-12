# Initial-state sensitivity within K selection
AUTHOR REVIEW - NOT FORMAL STAGE 7

Init_Supply is retained in the primary A. On 2,299 tracts, 1,533 exact zeros (66.6812%) and the 23 largest observations account for 62.4799% of its original variance. Standardization places the maximum near +9.73 SD. This is real frozen modeled information, but a sparse fractional service state, not observed electrical resilience.

The original 34 GEOIDs are kept fixed. Their previously authenticated mechanism is strong W dependence on station 308581 (STATION Q), a retained Core-source proxy. Q contributes 97.1891% of their aggregate initial modeled availability, which averages only 1.8153%. Its 40/1,000 threshold-eligible initial samples are source-qualified by that role; each rare tract's sample median availability is zero. This is not independent generation, feeder-service or power-flow evidence. The original physical audit is referenced, not regenerated.

Across policies, the small state recurs at K4-5, sometimes with 1-4 extra members; Vulnerability-first and Random already isolate a 36/38-tract state at K3. Thus sparse-state extraction partly explains why a policy can favor a different K. Every original rare member's policy/sample initial state is identical, but which other tracts join its class depends on recovery inputs and scaling.

Impact-first rare-class influence:

|   k |   rare_class_n |   rare_class_mean_silhouette |   nonrare_mean_silhouette |   all_mean_silhouette |   rare_composition_effect_on_mean |   centroid_Init_fraction |
|----:|---------------:|-----------------------------:|--------------------------:|----------------------:|----------------------------------:|-------------------------:|
|   4 |             34 |                       0.5999 |                    0.2632 |                0.2682 |                            0.005  |                   0.8911 |
|   5 |             34 |                       0.601  |                    0.2775 |                0.2823 |                            0.0048 |                   0.8911 |

About 89.11% of its centroid separation comes from Init, but its 34 members are only 1.48% of tracts / 1.369% of residents. Its effect on the *overall mean* silhouette is only around 0.005, so the K5 maximum cannot be attributed solely to giving a very small class a high silhouette. The nonrare mean still supports substantive distinctions. However, extracting that rare state consumes a class and changes the remaining partition; the composition calculation does not isolate that whole optimization effect.

Minus-Init preferences under policy-specific scaling:

| policy              |   endpoint_chord_elbow_candidate |   maximum_mean_silhouette_k |   maximum_mean_silhouette |
|:--------------------|---------------------------------:|----------------------------:|--------------------------:|
| betweenness-first   |                                3 |                           3 |                    0.3366 |
| degree-first        |                                3 |                           3 |                    0.3587 |
| hospital-first      |                                4 |                           3 |                    0.3543 |
| impact-first        |                                4 |                           3 |                    0.3169 |
| random              |                                3 |                           2 |                    0.2926 |
| vulnerability-first |                                4 |                           3 |                    0.3458 |

Most minus-Init policies favor K3 silhouette (Random favors K2). The small Q state no longer forms a high-purity independent class under these registered alternatives; membership is distributed according to other features. The effect includes both deleting the initial-state construct and increasing Grid_Impact/HHI budgets from 1/9 to 1/6. INIT_ALGEBRAIC_DISTANCE_DIAGNOSTICS.csv holds the original partitions fixed: remove Init's squared centroid distance, then separately add 50% of Impact/HHI squared distances. This distinguishes presence from reallocation algebraically without fitting an unauthorized alternative model. No clipping, tail trimming, zero replacement, winsorization or jitter was performed.

Retain Init only with the rare-state/Core-proxy interpretation and ablation caveat. A statistical preference for K3 after deletion is not authorization to drop this scientifically distinct initial-disruption coordinate. Four-quadrant holdouts show that rare precision can fail even when all rare observations remain eligible; seed stability alone is insufficient.
