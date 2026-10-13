> EXPLORATORY EIGHT-VARIABLE AUTHOR REVIEW — NOT FORMAL STAGE 7

# Final eight-variable author-review decision

**RECOMMENDED EIGHTH VARIABLE: CDC/ATSDR EJI 2024 standalone `RPL_CBM`.**

**Recommended specification: H2-CBM, eight coordinates, equal three-RQ budgets. Provisional detailed review resolution: K4; K3 parsimonious and K5 network-detail alternatives remain defensible. No formal promotion.**

## 1. Scientific definition, coverage and alternative search

Use the official nationally ranked sum of nine selected climate-indicator percentiles exactly as published. Hazards are heat; wildfire smoke and burned area; coastal/riverine flooding; drought; hurricane; strong winds; tornado. Earthquakes are excluded but already condition the frozen recovery model. Label the coordinate **selected climate-hazard burden**, not all-natural-hazard risk, expected loss, actual outage exposure or economic damage.

All 2,299 positive-population tracts have finite 0-1 ranks, including all eight zero-housing tracts; only the 16 frozen zero-population tracts remain outside clustering. Frozen population totals 9,066,522. The complete 2,315-tract service domain is untouched.

No independently verified alternative improves both construct and full-cohort support here. NASA NDH is a serious seismic/nonseismic hazard-decile alternative, but its migrated payload requires Earthdata authentication (verified HTTP401), so local support and zero rules are unresolved in this task. EPA PRISM's actual exposure table matches only 1,879 IDs and misses 420 (1,392,465 residents); current boundary identity is also unverified. The prior physical composite covers only 2032 tracts jointly. No missing values are invented or additional tracts removed. This is a bounded source-search conclusion, not a universal claim of best available hazard measurement.

## 2. What actually determines the local hazard coordinate?

Riverine percentile covariance supplies 69.25% of local published sum-score variance; the binary split between positive and zero published riverine-frequency values explains 84.33% of published rank variance. This binary split does not certify physical absence of flooding. Heat contributes about 12.21%, burned area 8.53%, coastal flooding 8.11%, smoke 1.78%; several other hazards contribute almost no local variation. Positive-covariance participation ratio is 1.967 at indicator level and 1.603 after grouping smoke/burn and the two flood measures into hazard families. These are descriptive concentration measures, **not counts of independent physical hazards**. Negative/shared covariance is explicitly retained in the source table.

The coordinate is strongly flood-influenced, not nine balanced local hazards, but is not solely one binary field: within-riverine-stratum climate variation and all-indicator/domain leaveouts are reported. Four previously verified major-removal fits are reused; six remaining individual removals and the Extreme Events domain receive narrowly registered H2 K3/4/5 seed42 comparisons. Removing a locally constant hurricane indicator can still change national rerank spacing; any resulting membership change is national calibration/geometry, not local hurricane information.

## 3. Incremental information and weighting

CBM has conditional linear R2=0.0724, VIF=1.0780; fixed random-fivefold nonlinear R2=0.1647 and spatial-block R2=0.0573. Pairwise associations are modest, but this is not causal independence or source-quality validation. It adds a distinct climate-context construct while contributing only about 1.4-2.1% of H2 K3-5 observed between-class separation. Small contribution is not a license to tune its weight upwards.

Keep H2 squared-distance budgets: RQ1 each1/9, RQ2 each1/6, SOVI1/6, log population1/12, CBM1/12. Square roots multiply standardized values. H1 remains sensitivity only. Fixed-distance and fixed-partition algebra separates hazard addition from population-budget reduction; reassignment cannot be attributed entirely to hazard information. Equal domains are defensible declared design budgets, not optimized, not equally realized separation. No weight revision is required to achieve the author's eight-variable design.

## 4. K evidence and action

|   k |   mean_silhouette |   seed_min_ARI |   geographic_min_ARI |   policy_LOO_min_ARI |   policy_LOO_mean_ARI |   smallest_seed42_class |
|----:|------------------:|---------------:|---------------------:|---------------------:|----------------------:|------------------------:|
|   3 |          0.243907 |       1        |             0.637733 |             0.64709  |              0.682098 |                     446 |
|   4 |          0.250675 |       0.99602  |             0.58335  |             0.579853 |              0.717578 |                      38 |
|   5 |          0.2512   |       0.980893 |             0.578249 |             0.563043 |              0.749599 |                      38 |

Mean Silhouette favors K5 (0.251200); K4 (0.250675) is nearly tied, with overlapping seed ranges. Smooth endpoint-sensitive chord bends favor K3 on K1-6/7 and K4 on K1-8. Thus neither statistic establishes a universal optimum. K4 is the proposed **detailed author-review** resolution because it reconciles the full-range bend, near-maximal silhouette, very high seed consistency and interpretable explicit initial-state exception without K5's additional structural split. Geographic/policy agreement remains moderate; K4 is not certified geographically optimal. K3 better supports a simpler regional three-pattern account and has stronger worst-case geographic agreement; K5 adds a meaningful high-spectral-impact subgroup if finer network differentiation is the desired resolution. These trade-offs are explicit author decisions, not three-RQ counting.

H2-to-P2 ARI is approximately0.906 (K3) and0.934 (K4); about2.37% and1.66% resident population is reassigned after display alignment. H2 K4 is seed-stable (minimumARI 0.996) but geographically moderate (minimum 0.583) and policy-set sensitive (LOO minimum 0.580, mean 0.718). H2 K5 has somewhat better average policy LOO agreement, not a uniformly worse robustness result. No claims of policy-neutral types are made.

## 5. Original-unit H2 K4 profiles (seed42)

|   H2_K4_display_class |   n_tracts |   population |   population_share |   Init_Supply |   Grid_Impact |   Redundancy_HHI |   B_Unconstrained |   MeanDelta |   SOVI_SCORE |   Population |   Published_RPL_CBM |
|----------------------:|-----------:|-------------:|-------------------:|--------------:|--------------:|-----------------:|------------------:|------------:|-------------:|-------------:|--------------------:|
|                     1 |    38.0000 |  136453.0000 |             0.0151 |        0.0173 |        0.0257 |           0.5752 |           21.8430 |      8.1030 |      62.1932 |    3590.8684 |              0.3671 |
|                     2 |  1228.0000 | 5059760.0000 |             0.5581 |        0.0003 |        0.0078 |           0.6478 |           30.2257 |      1.6336 |      78.1875 |    4120.3257 |              0.2325 |
|                     3 |   440.0000 | 1755500.0000 |             0.1936 |        0.0008 |        0.1220 |           0.6269 |           28.3720 |      6.8243 |      49.4149 |    3989.7727 |              0.3567 |
|                     4 |   593.0000 | 2114809.0000 |             0.2333 |        0.0000 |        0.3267 |           0.6375 |           37.5107 |      4.0714 |      55.2822 |    3566.2884 |              0.3418 |

Display IDs are H2/K4-specific, not formal Stage7 IDs; clusters are ordered by mean frozen total burden. Full distributions, counts, original quartile composition and hospital incidence are separate CSVs. Clustering-input profiles are descriptive, not independent validation.

- C1:38 tracts,1.51% residents, elevated relative initial service (~1.731% absolute), lower baseline deficit but high constraint increment. All34 frozen Q-linked tracts are present. Its separation is about80.1% Init; no zero-housing or <=100-resident tract is in this small class. This is a retained Core-source proxy/initial-condition exception, **not electrical resilience**.
- C2:1,228 tracts,55.81% residents, low spectral grid impact and constraint increment, near-regional baseline deficit, SOVI mean78.19 versus cohort mean reported in the profile CSV, and lower local CBM. High SOVI does not mechanically produce high modeled recovery burden.
- C3:440 tracts,19.36% residents, relatively large constraint increment (~6.82 deficit hours) and lower unconstrained burden (~28.37h); SOVI49.41 and CBM0.357. This is a logistics-sensitive pattern, not a quantified causal travel-delay class.
- C4:593 tracts,23.33% residents, larger unconstrained burden (~37.51h), spectral impact (~0.327) and moderate constraint increment (~4.07h), SOVI55.28/CBM0.342. HHI varies less among these class means; no need to force an extreme in every coordinate.

Reference percentile ranges and exact means/medians/P10/P90 are supplied, avoiding unsupported high/low narrative labels. K5 splits an additional high-spectral-impact class (219 tracts,8.39% residents), not a new independent multi-hazard impact mechanism.

## 6. Remaining scientific limitations and approvals

The standalone formula lacks direct social/asset/resilience adjustment, but source-quality gate remains unresolved: missing F_NEHD/F_SMOKE/F_BURN;2,251 burned-area zeros of uncertain physical/source-null provenance;13 unidentified national heat interpolations;hurricane source-null-to-zero;drought units discrepancy. Removing burned area has small membership effects but does not certify those zeros. Mixed source periods, nationally tied ranks and riverine support can dominate local climate geography. Independent CAL FIRE/NFHL comparison is partial and construct-dependent; the archived CDC heat measure is same-source, not independent validation.

Vulnerability-first uses frozen Q4 in the ensemble's priority construction. Prior evidence shows procedural SOVI dependence despite modest marginal correlations; these RQ domains are not independent causal mechanisms. Geographic tests use four coarse leave-out quadrants and seed42; policy perturbations use seed42. No formal uncertainty intervals or clean-clone raw-archive reproducibility are inferred from these diagnostics. Full physical-source preservation needs the manifest-bound local archive absent from clean Git clones; published matrices and fits can be independently verified from committed LFS payloads.

Author must approve: (1) the **climate-hazard context**, not comprehensive hazard-risk, interpretation; (2) published-as-is source-limit acceptance; (3)H2 domain/internal budgets; (4)K4 detailed review versus K3 parsimonious/K5 structural-detail resolution; (5) separate formal Stage7 promotion. The seven-variable P2 is now ablation only. No model, frozen simulation, quartile, manuscript or numbered figure changed, and no CDC/provider email was sent.
