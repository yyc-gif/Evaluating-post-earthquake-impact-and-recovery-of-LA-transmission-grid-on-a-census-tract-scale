# P2 K3/K4 scientific decision

Recommendation: saved P2/K3 as the parsimonious main-text candidate; saved P2/K4 as sensitivity. Primary P2 is author-approved, but this review does not execute formal K or Stage 7 promotion.

|      k |   mean_silhouette |   seed_min_ARI |   geographic_full_median_ARI |   geographic_heldout_min_ARI |   leave_one_policy_out_min_ARI |   leave_one_policy_out_max_ARI |   min_class_tracts |
|-------:|------------------:|---------------:|-----------------------------:|-----------------------------:|-------------------------------:|-------------------------------:|-------------------:|
| 3.0000 |            0.2487 |         0.9926 |                       0.7610 |                       0.4189 |                         0.6187 |                         0.7916 |           428.0000 |
| 4.0000 |            0.2530 |         0.9884 |                       0.8613 |                       0.8057 |                         0.5722 |                         0.8094 |            37.0000 |
| 5.0000 |            0.2633 |         0.6251 |                       0.6656 |                       0.2818 |                         0.5051 |                         0.7599 |            12.0000 |

K3 preserves a large high-SOVI/lower-increment class, a smaller low-baseline/high-increment class and a higher-spectral-impact/high-baseline class. RQ3 remains interpretable: 429/50/100 frozen Q4 tracts are distributed across C1/C2/C3. Hospital-linked incidence and quartiles are descriptive context, not independent validation of features derived from the same SOVI and modeled service data.

K4 provides slightly higher silhouette and stronger median geographic agreement, but adds a 37-tract class (130,518 residents) strongly associated with the frozen Core-source proxy. The exact historical 34 Q-linked tracts occur in P2 classes as follows: K3 {2: 34}; K4 {1: 34}. Their mean initial availability is 0.018153, only 1.815% in absolute terms. Stable detection is not physical verification of resilient supply. The scalar ablation and fixed-budget distance diagnostics are retained in CSVs; deletion and redistribution are not interchangeable effects.

K5 has the highest internal mean silhouette but competing seeds, weaker geographic agreement and a twelve-tract/754-person low-population class in the saved seed42 fit. No tract is discarded to improve geometry. A modest numerical gain alone is not sufficient to prefer K4 or K5 for regional interpretation.

    The policy ensemble removes reliance on one incumbent policy but does not make labels policy-independent. K3 leave-one-policy-out ARIs are approximately 0.619-0.792 at seed42. The lowest geographic held-out agreement is only 0.419 for K3, versus 0.806 for K4; K4 has a real geographic-stability advantage in this registered design. Four median-quadrant leave-outs are sensitivity, not independent spatial validation. K3 is therefore a conditional parsimony recommendation, not a dominance claim. Authors should review the K3 main/K4 sensitivity trade-off after viewing both map candidates. No universal optimal K is established.
