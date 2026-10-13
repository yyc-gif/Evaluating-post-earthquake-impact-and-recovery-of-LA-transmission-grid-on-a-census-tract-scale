> EXPLORATORY EIGHT-VARIABLE AUTHOR REVIEW — NOT FORMAL STAGE 7

# Seven-versus-eight ablation

The primary design candidate is H2-CBM; P2 is the seven-variable ablation. H1 is weighting sensitivity.
Main fits K1-8/seeds42-46, four geographic quadrants and policy perturbations are reused exactly at `5eeaa02ca4dec99f27a6ee3eb470a441007e6f6b`. No unrestricted search or primary refit occurred.

H2 preserves SOVI's 1/6 budget, halves population's budget from 1/6 to 1/12, and adds CBM at 1/12. Consequently P2-to-H2 is **not pure feature addition**. Exact fixed-pair distance algebra separates added hazard and removed population contributions. Average contributions cancel because both are standardized, not because individual distances/memberships are unchanged. The fixed-partition BSS decomposition is separately retained.

H2-to-P2 mean ARI is about 0.906 at K3 and 0.934 at K4; Hungarian-displayed reassigned population is about 2.37% and 1.66%. At K5 the P2 seed solutions themselves compete, so larger changes are not solely a CBM effect. H1 alters SOVI as well as population budgets and changes more assignments at K3/4. Cross-space Silhouette is not a common out-of-sample physical-quality score.

## H2 quantitative evidence

|   k |   mean_silhouette |   seed_min_ARI |   geographic_min_ARI |   policy_LOO_min_ARI |   policy_LOO_mean_ARI |   smallest_seed42_class |
|----:|------------------:|---------------:|---------------------:|---------------------:|----------------------:|------------------------:|
|   3 |          0.243907 |       1        |             0.637733 |             0.64709  |              0.682098 |                     446 |
|   4 |          0.250675 |       0.99602  |             0.58335  |             0.579853 |              0.717578 |                      38 |
|   5 |          0.2512   |       0.980893 |             0.578249 |             0.563043 |              0.749599 |                      38 |

K4 is the **leading detailed author-review candidate**, not a promoted final selection: it is the K1-8 chord-bend candidate and nearly ties K5 mean Silhouette while being more seed-consistent and less subdivided. K3 is the defensible parsimonious alternative, with stronger worst-case geographic agreement but a mixed logistics group whose seed42 mean silhouette is only about 0.004 (47.8% negative). K5 adds a 219-tract high-spectral-impact subtype at seed42, a real structural interpretation, but mean silhouette improves only 0.000524; it does not produce a clear new climate-context community class. Policy robustness is mixed, not categorically better for K4: K5 has higher average LOO agreement but a slightly lower worst case. No composite ranking score is used.

The H2 Elbow is smooth, not sharp. K1-6 and K1-7 chord bends support K3; K1-8 supports K4. Mean Silhouette peaks at K5, with overlapping K4/5 seed ranges. K2 is too coarse for the distinct burden/constraint patterns; K6-8 lose much Silhouette and can isolate very-low-population classes. No K is selected because of the number of RQs.

K4/5 retain 38 tracts containing all 34 frozen STATION Q-linked tracts. Their mean Init is about 1.731%, not strong resilience; Init supplies about 80.1% of their centroid separation. The registered minus-Init sensitivity redistributes RQ1 weights and dissolves this rare class. It is a source-proxy/model-initial-condition exception, not an institutional-tract artifact: this 38-class contains no <=100-resident or zero-housing tract. Separate fixed-budget algebra preserves the deletion/reallocation distinction.
