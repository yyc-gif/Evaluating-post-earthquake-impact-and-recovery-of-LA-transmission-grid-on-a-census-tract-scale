# Final GA Initialization Decision

**Recommend exactly one: `PURE_RANDOM_GA`.** This is an independently executable initialization recommendation, not a replacement of the validated formal sequence or configuration. All newly found chromosomes remain diagnostic.

## Completed Registered Evidence

Registration ca4d49e preceded main computation. Forty main searches comprise 20 paired fresh seeds and 4,000,000 distinct original 64-state mean evaluations. The extension decision and its prespecified rule are in EXTENSION_DECISION.json. The first 10 pairs continued their original RNG, population, archive and private cache to 250k and 500k: 8,000,000 incremental evaluations, not new replicates. The five-endpoint Bonferroni family was reserved before data. Pointwise paired t and 20,000 seed-block bootstrap intervals, medians, SDs, wins/ties, cost and all raw sequences are retained in accompanying tables. These intervals measure optimizer randomness conditional on 64 planning states, not physical uncertainty.

## Registered Rule And Post-Data Decision Audit

The immutable preregistered automatic rule yields `IMPACT_SEEDED_GA`. The primary scientific recommendation is `PURE_RANDOM_GA`. This is an explicitly disclosed post-data deviation from that automatic selection rule. Seeds, source identities, numerical margin, paired estimand, interval family, continuation trigger and all budgets were kept unchanged. No data or unsuccessful run was removed.

The original automatic fallback required BOTH a two-sided interval inside +/-0.001 h and 90% proximity to a development-selected minimum before allowing pure random. An interval extending below that band in favor of pure random is not a harmful disadvantage, and the proximity gate can fail in both modes. The full 20-seed 100k upper simultaneous disadvantage bound is 0.000339297 h, below the prospectively fixed 0.001 h numerical tolerance; this supports a bounded numerical comparison, not equivalence or physical noninferiority. Reserved ten-pair higher-budget results and methodological simplicity support the post-data judgment. Their stronger contrast must NOT be attributed to additional budget without checking the same ten pairs at 100k. The strict proximity success-rate failure remains disclosed; the recommendation does not certify 90% near-winner reliability.

Positive PURE_RANDOM-minus-IMPACT_SEEDED favors the seeded control:

| Budget   | Pairs   | Pure mean (h)   | Seeded mean (h)   | Pure - seeded (h)   | Simultaneous 95% CI (h)      | High quality, pure/seeded   |
|:---------|:--------|:----------------|:------------------|:--------------------|:-----------------------------|:----------------------------|
| 20000    | 20      | 33.028785947    | 33.010517324      | 0.018268623         | [0.009830590, 0.026706655]   | 0/0                         |
| 50000    | 20      | 33.000532750    | 33.001147925      | -0.000615175        | [-0.002325102, 0.001094753]  | 6/1                         |
| 100000   | 20      | 32.999093670    | 33.000381595      | -0.001287925        | [-0.002915146, 0.000339297]  | 10/5                        |
| 250000   | 10      | 32.997675976    | 33.000009277      | -0.002333300        | [-0.004482882, -0.000183718] | 8/3                         |
| 500000   | 10      | 32.997675976    | 33.000009277      | -0.002333300        | [-0.004482882, -0.000183718] | 8/3                         |

Initial-population and subsequent-search contribution at 100k:

| mode             |   initial_best_mean |   final_mean |   ga_gain_mean |
|:-----------------|--------------------:|-------------:|---------------:|
| IMPACT_SEEDED_GA |        33.578302560 | 33.000381595 |    0.577920965 |
| PURE_RANDOM_GA   |        36.359463146 | 32.999093670 |    3.360369476 |

## Required Questions

A. A previously optimized chromosome is not a prerequisite for competitive search: both new configurations explicitly contain none, and all 20 pure-random searches substantially improve on Impact-first. This does not guarantee attaining the selected formal minimum in every seed. The historical 93.06% fraction was continuation bookkeeping, not intrinsic GA capability.

B. Pure random reaches the preregistered J<=32.998840773883 h criterion in 10/20 main searches at 100k and 8/10 reserved searches at 500,000. It does not meet the registered 90% empirical rate. The seeded control reaches this criterion in 5/20 at 100k and 3/10 at the final budget. Exact formal-score wins are distinct from approaching within 0.001 h; neither a selected minimum nor an observed success fraction proves out-of-sample reliability.

C. One Impact-first seed provides a clear early advantage at 20k: pure-minus-seeded mean loss is +0.018268623 h, with simultaneous interval [0.009830590, 0.026706655] h. At 100k, the full 20-pair interval includes zero and does not establish a directional advantage. At the final reserved budget, pure-minus-seeded mean loss is -0.002333300 h; simultaneous interval [-0.004482882, -0.000183718] h. The interval excludes zero in favor of pure random. Earlier-budget differences must be read separately, not pooled. The numerical 0.001 h margin is an engineering tolerance, not a physically validated policy threshold.

D. The seeded advantage observed at 20k disappears by 50k in the full paired cohort. For the same ten reserved pairs, the initialization contrast changes from -0.002335537 h at 100k to -0.002333300 h at 500k (change 0.000002237 h; pointwise 95% interval [-0.000034721, 0.000039194]). This is a secondary within-seed budget contrast, not 20 versus 10 independent means. The mean change is only 0.008053 equivalent service seconds, below the 0.001 h numerical margin; it does not demonstrate a consequential late-budget reduction. The absolute observed contrast decreases by this tiny amount, not by a meaningful late-budget gain. No continued trajectory improves its best loss between 250k and 500k. Same-seed marginal gains and changes in initialization contrast are in BUDGET_CONVERGENCE_AND_DUPLICATION.csv and BUDGET_DIFFERENCE_REDUCTION.csv. Late plateau evidence applies only to tested trajectories, not global convergence.

E. Yes. Either configuration can be described as one standalone GA with no prior optimization stage. The recommended `PURE_RANDOM_GA` uses only 100 random permutations, no inherited optimized prior or engineered neighbors.

F. Recommend `PURE_RANDOM_GA` for an independently executable single-GA manuscript, subject to separate authorization before any formal change. The full 20-seed numerical bound, stronger reserved-pair performance and removal of an unnecessary heuristic dependency support this explicitly post-data methodological judgment. Do not describe the strict proximity or equivalence gates as passed.

## Interpretation And Limitations

No independent-validation cohort, new physical realization, alternative objective, ILS, local refinement, hybrid or parameter grid enters this experiment. All non-initialization search mechanics, 92 stations/318 edges/Core sources, 57-crew directed-travel scheduler, physical samples, mapping and source gate remain fixed. Important best and median runs pass all 64-state original production evaluations. Complete per-seed populations, changes, caches, state boundaries and objective timings are saved. Archive protection is not inherited-information injection. No seed was chosen for the extension on the basis of its result.

The formal candidate was selected using earlier optimization and need not equal a typical independent-search result. High-quality thresholds and practical comparisons are conditional numerical judgments, not new physical-validation claims. An interval crossing zero does not establish equivalence; meeting a numerical margin does not prove physical generalization. The recommendation is based on repeated-seed evidence, the unchanged prespecified numerical tolerance and an explicitly post-data methodological judgment, not the best single run or a passed preregistered adoption rule.
