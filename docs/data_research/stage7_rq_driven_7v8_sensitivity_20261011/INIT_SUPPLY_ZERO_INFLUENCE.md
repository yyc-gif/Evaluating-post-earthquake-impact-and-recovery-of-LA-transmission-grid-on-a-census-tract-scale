# Initial-supply sensitivity

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** The coordinate is the frozen 2pc50 mean modeled initial tract service state after the existing gate, not observed customer supply and not a new gate calculation.

Exact zeros: **1533/2299 (66.681%)**. Near-zero absolute <=1e-8 count is the same. Full-cohort median is zero; P75=0.00003887; P90=0.00080550; maximum=0.02450000 (2.45%). Nonzero-only quantiles and moments are retained separately in `FEATURE_ORIGINAL_UNIT_DISTRIBUTIONS.csv`. No zeros are changed, jittered or imputed.

The standardized range is **-0.23671 to 9.73336**. The top 1%, **23 tracts**, contributes **62.48%** of initial-service SS and **6.94%** of all A standardized weighted total SS. All nonzero records contribute about 96.26% of this coordinate's SS. Its overall distance budget nevertheless stays 1/9; tail leverage is not an unlimited increase in total budget.

## Rare-state cluster

A/B/B-equal-RQ3 at k4-6 repeatedly retain **34 tracts** with mean initial service **0.018153** and mean B **23.601 h**. At A/k4/seed42, the initial coordinate accounts for **89.11%** of that cluster centroid's distance from the global centroid; it contributes **22.42%** of all between-cluster SS. All 23 Init-P99 tracts are in this group. None of the eight added zero-housing records is in it, and none is an asset-P99 observation. It is not an institutional/asset-tail artifact.

This is a real difference in the frozen modeled state and is associated with lower cumulative service deficit. But isolating the group is strongly amplified by z scaling. It cannot be called independent confirmation of superior electrical connectivity, a real-life outage class or a robust universal community type. The input-profile relation to B is shared frozen model evidence, not independent validation. `SMALL_CLUSTER_DEPENDENCY_PROFILES.csv` describes fixed W contributions without interpreting them as capacity or rerunning any physics.

## Registered ablation

| specification_a   | specification_b   |   ARI_median |   changed_median |
|:------------------|:------------------|-------------:|-----------------:|
| A                 | A-minus-Init      |       0.1796 |        1075.0000 |
| A                 | B                 |       0.6014 |         296.0000 |
| A-minus-Init      | B-minus-Init      |       0.2376 |         942.0000 |
| B                 | B-equal-RQ3       |       0.5003 |         392.0000 |
| B                 | B-minus-Init      |       0.6646 |         417.0000 |

At k4, A versus A-minus-Init median ARI is about 0.18, while B versus B-minus-Init is about 0.66. The 34-tract class disappears in the ablations, but this also raises each remaining RQ1 coordinate from 1/9 to 1/6. Differences therefore cannot be attributed to a pure removal alone. A-minus-Init/k4 assigns roughly 57.8% of separation to grid impact/HHI and only 4.1% to RQ3; dropping Init does not automatically produce a better balanced community typology.

## Recommendation

**Retain Init conditionally in the registered seven/eight-variable reference** if initial disruption is an intended RQ1 construct, and show the minus-Init comparison prominently. Do not drop it simply because its original range is small, or retain it merely because the resulting rare group is seed-stable. There is no scientifically justified transformed/trimmed replacement evaluated here. Author approval is needed on whether a rare favorable initial-service regime deserves its own community type, versus being a descriptive initial-condition indicator. This audit does not choose or promote a formal answer.
