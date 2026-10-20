# Solution quality and generalization

## Q6 — What transfers and what remains unvalidated

No new physical samples were generated. The original objective always retains its 64 samples for full-comparison searches. Four fixed folds (split seed19371) use 48 training and 16 held-out samples; each fold has five seeds for predeclared legacy/archive-only and one-elite configurations, 25,000 distinct training scores. Held-out values never score candidates or select sequences. These fixed-algorithm diagnostics are not unbiased validation of all hyperparameters subsequently tuned on the full64.

|   elites |   training_mean_change |   training_seed_fold_sd |   heldout_mean_change |   heldout_seed_fold_sd |
|---------:|-----------------------:|------------------------:|----------------------:|-----------------------:|
| 0.000000 |              -0.295582 |                0.123352 |             -0.198019 |               0.105086 |
| 1.000000 |              -0.482257 |                0.048328 |             -0.383590 |               0.081203 |

Training improvement exceeds held-out improvement, demonstrating selection optimism. Fold/seed values share samples and are descriptive, not forty independent validation cohorts. Subset-ranking stability on500 32-of64 subsets is explicitly postselection, not out-of-sample evidence. Extensive tuning on64 can overfit those samples; more objective queries do not increase physical sample information.

The previous exploratory candidate02 minus candidate01 on the already inspected1,000 cohort changes all-tract loss by -0.025409591 h (median -0.023321762, empirical5–95 range [-0.194931556, 0.121926210], 95% bootstrap mean CI [-0.033731078, -0.016776106]). Thus the planning ranking did not transfer unchanged. This cohort is no longer an untouched test.

Three new sequences were fixed by the predeclared planning-only rule and their hashes stored before reuse. Their new schedules and event arrays are confined to the diagnostic namespace. The reused1,000 cohort provides exploratory transport evidence; it cannot support an unbiased final performance claim after extensive author inspection. No evaluation-guided reselection is performed. All three selected orders tie at the best planning objective and have identical planning completion arrays. FIXED_CANDIDATE_PAIR_COMPARISONS.csv quantifies their small reused-cohort differences; their distinct full permutations do not represent three independently superior planning solutions. A genuinely independent final assessment would require a separately authorized new sample or other independent data, a fixed algorithm/selection rule, immutable sequence hashes, then one assessment. No such sampling was undertaken here.

## Q7 — Defensible quality statement

Best found planning loss: 32.997840773883 h. Rigorous unlimited-crew/zero-travel relaxation lower bound, conservatively rounded down from exact rational integration: **31.360999855 h**. The relaxation preserves the same damage/durations, threshold, Core-source connectivity and population dependency. Any feasible completion occurs no earlier than its saved duration; earlier station restoration increases raw functionality, threshold eligibility and source-connected service monotonically. Nonnegative weights make every relaxed loss integral a lower bound. RATIONAL_RELAXATION_BOUND.json records an exact fraction for the encoded inputs and downward rounding; RELAXATION_LOWER_BOUND.csv gives corresponding double-precision per-sample values.

The fixed-input mathematical optimum lies between this lower bound and the best feasible order. Remaining bound gap 1.636840919 h, or 4.960% of the best objective. This is a bound on the mathematical model, not an out-of-sample certificate. The lower-bound schedule relaxes logistics and is not operationally feasible. Full92 exact optimization is not claimed. All720 arrangements in a six-position conditional problem are enumerated with other86 positions fixed; that exact restricted minimum is a feasible upper bound, not a global lower bound.

Finite search and tested-neighborhood local stability do not prove global optimality or uniqueness. The strongest statement is a new best feasible sequence, replicated search distributions, diminishing/inconsistent budget improvements, neighborhood-qualified local optimality where a complete scan passed, and a valid nonzero global-bound gap. No policy is called globally optimal.

## Q8 — Restoration and community consequences

Planning-only selected candidate1 compared with Impact-first on the reused evaluation cohort:

| metric                                      |   mean_change |   median_change |       p05 |      p95 |   bootstrap_mean_ci95_low |   bootstrap_mean_ci95_high |
|:--------------------------------------------|--------------:|----------------:|----------:|---------:|--------------------------:|---------------------------:|
| All-tract service loss (h)                  |     -0.514705 |       -0.404362 | -1.535443 | 0.146760 |                 -0.548354 |                  -0.481162 |
| Population T80 (h)                          |     -0.238176 |       -0.093418 | -2.724453 | 1.510777 |                 -0.323653 |                  -0.156127 |
| Hospital-tract service loss (h)             |     -0.291562 |       -0.182743 | -1.387431 | 0.383957 |                 -0.326466 |                  -0.257174 |
| Population-weighted Gini                    |      0.008594 |        0.007013 | -0.003752 | 0.026861 |                  0.007997 |                   0.009191 |
| Signed Q4-Q1 service-loss difference (h)    |     -0.203685 |       -0.197001 | -0.979374 | 0.550240 |                 -0.233636 |                  -0.173422 |
| High-low vulnerability service-loss gap (h) |      0.173757 |        0.151678 | -0.550386 | 0.976535 |                  0.144110 |                   0.203695 |
| Q4 tract service loss (h)                   |     -0.660909 |       -0.514629 | -1.881644 | 0.033761 |                 -0.698038 |                  -0.623936 |

Means, medians and5–95 ranges are realization-level quantities; the95% confidence intervals resample full physical realization differences10,000 times (seed641209). Optimization success refers only to aggregate planning loss. Quartile outcomes, signed Q4−Q1, mean realization-level |Q4−Q1|, Gini, hospital-linked loss, T80 and component losses are distinct outcomes and can disagree. In particular E|Q4−Q1| is not |E(Q4−Q1)|. Q4 is the highest social-vulnerability quartile, not an income category. Hospital-linked loss is an equal-tract modeled-service measure, not hospital electricity delivery or clinical capacity. Source-connected availability is dimensionless, not MW or full electrical adequacy.

Full comparisons retain Impact/Hospital/Degree/Betweenness/Vulnerability/Random/Unconstrained and both existing exploratory candidates. Station execution records distinguish fixed rank from damaged-task dispatch, completion and travel. Priority changes are descriptive algorithm outcomes, not isolated causal benefits of individual station movements. Candidate trajectories retain raw f, threshold F, connectivity C and effective e; all component/event outputs and task records are saved. Formal scientific results are unchanged.

## Manuscript-ready interpretation

Under the existing64-realization planning objective, search quality depended on selection, survival, initialization and their interactions with population size, rather than generation count alone. Controlled elitism and selection improved search efficiency, while refinement of previously found orders yielded additional reductions in modeled community service loss. Planning gains and reused-cohort effects are reported separately; aggregate improvement does not imply reductions in every group disparity or inequality measure. These finite searches and local-neighborhood checks identify improved feasible orders, not a globally optimal or unique restoration sequence.
