# Final Single-Optimizer Decision

**RECOMMEND STANDALONE ILS AS THE REPLACEMENT CANDIDATE**

This is a methodological recommendation, not promotion authorization. The formal GA, current manuscript, scientific model and earlier independent-validation evidence remain unchanged. The manuscript should describe ONE optimizer after author approval and required independent confirmation, not a GA/ILS hybrid or operational comparison framework. The preceding parameter-defense package's Scope A/B presentation proposal is superseded for this task: the present investigation tests genuine Impact-only independence and makes one method recommendation, without editing the preceding report or claiming new physical validation.

## Completed Computation

Starting authority: `62f0c2be4f1e37f25e3db8d0d042cd5d0cfcfd3f`. Study registration commit: `2817b069c604578103d5b71587eacbd1ab0099bb`. Eight smoke runs x20k completed; 20 fresh paired main seeds x100k completed; the first10 predeclared pairs continued the same search states to250k and500k. This is40 main searches, not80 independent searches; the latter number counts final-budget observations. Exactly 12,160,000 new search calls evaluated the unchanged64-state mean. Setup and independent parity work are separately charged. No negative run was omitted, no attempt-capped case occurred in this experiment, and no physical samples were generated.

## Fair Cold-Start Evidence

| method   |   budget |   n |      mean_hr |    median_hr |       sd_hr |      best_hr |     worst_hr |
|:---------|---------:|----:|-------------:|-------------:|------------:|-------------:|-------------:|
| ILS      |    20000 |  20 | 33.001443127 | 33.001262277 | 0.002750717 | 32.998468658 | 33.008191212 |
| GA       |    20000 |  20 | 33.010686096 | 33.009823973 | 0.003748764 | 33.004962967 | 33.018505384 |
| ILS      |    50000 |  20 | 32.998856296 | 32.998823809 | 0.001365707 | 32.996276583 | 33.002700033 |
| GA       |    50000 |  20 | 33.001866921 | 33.001918390 | 0.001845461 | 32.998627020 | 33.005177714 |
| ILS      |   100000 |  20 | 32.997852134 | 32.998384878 | 0.001463864 | 32.995522414 | 33.000770951 |
| GA       |   100000 |  20 | 33.001006984 | 33.000877361 | 0.001795422 | 32.997922256 | 33.003967072 |
| ILS      |   250000 |  10 | 32.996074227 | 32.995990414 | 0.000756185 | 32.995220412 | 32.997893107 |
| GA       |   250000 |  10 | 33.000569304 | 33.000520669 | 0.001529434 | 32.998550124 | 33.003023049 |
| ILS      |   500000 |  10 | 32.995607561 | 32.995547891 | 0.000211316 | 32.995220412 | 32.995992846 |
| GA       |   500000 |  10 | 33.000569304 | 33.000520669 | 0.001529434 | 32.998550124 | 33.003023049 |

Paired difference is ILS minus fair cold GA; negative favors ILS. Intervals concern optimizer seeds conditional on the same development states. The five-budget family has simultaneous Bonferroni t intervals; bootstrap intervals are pointwise, not simultaneous. No formal equivalence/noninferiority margin was registered.

|           budget |            n |   mean_delta_hr |   simultaneous95_low_hr |   simultaneous95_high_hr |         wins |      losses |   mean_wall_ratio |
|-----------------:|-------------:|----------------:|------------------------:|-------------------------:|-------------:|------------:|------------------:|
|  20000.000000000 | 20.000000000 |    -0.009242969 |            -0.012352438 |             -0.006133499 | 20.000000000 | 0.000000000 |       0.672875111 |
|  50000.000000000 | 20.000000000 |    -0.003010625 |            -0.004423933 |             -0.001597316 | 18.000000000 | 2.000000000 |       0.661656468 |
| 100000.000000000 | 20.000000000 |    -0.003154850 |            -0.004670465 |             -0.001639234 | 18.000000000 | 2.000000000 |       0.678188092 |
| 250000.000000000 | 10.000000000 |    -0.004495077 |            -0.006161976 |             -0.002828179 | 10.000000000 | 0.000000000 |       0.657118761 |
| 500000.000000000 | 10.000000000 |    -0.004961743 |            -0.006539973 |             -0.003383514 | 10.000000000 | 0.000000000 |       0.648433609 |

Full paired medians/SDs, pointwise t/bootstrap intervals and seed values remain in `FAIR_COLD_START_GA_COMPARISON.csv` and `BUDGET_CONVERGENCE_AND_COST.csv`; no uncertainty result is discarded to shorten the table.

Both algorithms start with only the original Impact-first heuristic information. GA additionally receives99 random initial permutations, not a previous optimized prior, inversion neighbors or other heuristic archive. Equal budgets count distinct scored permutations. RNG consumption differs by method; fairness is common prior information, evaluator and budget, not identical proposals.

## Fixed Historical GA Reference

The formally selected GA remains SHA256 `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`, planning J32.997840773882714h. The full seed/budget comparison is `FROZEN_GA_REFERENCE_COMPARISON.csv`; historical100k/500k distributions are retained separately, with source hashes. They have a different initializer and selection history and are not a matched causal optimizer comparison.

Historical formally selected swap-GA protocol, seeds42-61 at100k; seeds42-46 are continuations at500k, not five additional replicates:

|           budget |        count |         mean |       median |         std |          min |          max |
|-----------------:|-------------:|-------------:|-------------:|------------:|-------------:|-------------:|
| 100000.000000000 | 20.000000000 | 32.999625244 | 32.999215517 | 0.001300140 | 32.997904329 | 33.002987520 |
| 500000.000000000 |  5.000000000 | 32.998867141 | 32.999203252 | 0.000610946 | 32.997840774 | 32.999264459 |

These source records were filtered to `operator_swap` alone, not pooled with original inversion-GA, mixed operators, or other shortlist configurations. The archived final configuration pins P100, crossover0.8, swap mutation0.1, tournament3, elite1. The two original controlled mutation0.2 bridge configurations are not its formal100k/500k distribution.

Selected standalone ILS: seed2026102108, budget250,000, J=32.995220412412h, SHA256 `17705a83a7607862d05ec9d6b607d58e31ff644712ceb0d0652ce7e59642499f`. It comes only from the preregistered main-pool rule, without extra refinement. Full92-station order and exact originating receipt are in `SELECTED_STANDALONE_ILS_CANDIDATE.json`. Its minimum is selected development performance, not an unbiased expected optimizer result. Each repeated seed's result is retained, including those above frozenGA.

## Physical-Sample Influence And Production Parity

All64 development states for ILS, frozenGA and Impact passed the independent pandas/NetworkX production path and native event decomposition:192 production sample calls and192 compiled sample calls; maximum discrepancy 2.9e-12h. The native scheduler/source gate and population dependency mass are unchanged.

ILS-minus-Impact mean -0.583082147587h, median -0.396640250584, better/worse states56/8; omit15 mean -0.560555273060h. ILS-minus-frozenGA mean -0.002620361470h, median +0.055004456440, better/worse states13/51. State15 delta -2.022687988408h; omit15 mean +0.029444204036h. 5 of64 single omissions reverse its mean ranking. Removing influential states is a diagnostic only, never a new objective or selection rule.

Exact mean whole-schedule changes relative to frozenGA: self +0.093264654287h, threshold +0.003865408037h, source -0.099750423795h. State15: self +0.130351320765h, threshold +0.004415725088h, source -2.157455034262h. The source/threshold accounting explains how aggregate gains can coexist with worse typical samples; it does not establish a causal effect of an individual station move. Native state15 crew schedules, source-connected components and dependency masses are preserved.

Definitions: self=1-f; threshold=f(1-F); source=fF(1-C); total=1-fFC. Integrate at actual completion events over the unchanged original planning horizon 2855.254013110100h, mass weighted and normalized. The original manuscript/independent-validation endpoint is480h, not this numerical planning upper bound. Reintegrating all192 native traces at480h gives maximum absolute post480 loss 2.7e-13h: they are equivalent for these fixed planning states and sequences only. Future physical samples must retain480h truncation/censoring explicitly, not presume zero tails. These are equivalent population-weighted service-loss hours, not person-hours, MW, energy or restoration time for every household.

## Decision Grounds

| Required criterion | Evidence and boundary | Assessment |
|---|---|---|
| Independence | Impact-first only; no optimized prior, other heuristic archive or extra refinement | PASS |
| Complete-workflow simplicity | One swap mechanism; no previous optimizer dependency, population/crossover/selection machinery | PASS; still parameterized |
| Optimization quality |18/20 paired100k and10/10 paired500k wins; all five simultaneous seed intervals favor ILS | Supported conditionally; no formal equivalence test |
| Reliability | All48 smoke/main searches complete; twenty full ILS cache replays exact; ten registered extensions | PASS on this planning model |
| Parameter defensibility | Verified original methodology, retained negative/positive historical sensitivity, independent Impact-only package test | Defensible engineering package, not unique optimum |
| Scientific integrity | No new physical samples or old validation-outcome selection; selected-sequence influence disclosed; new confirmation frozen but not executed | PASS for replacement-candidate recommendation, not policy promotion |

Standalone ILS passes independence: current and initial archive contain only Impact-first; every scored permutation is valid; no GA prior or deterministic refinement enters its search. It genuinely removes the previous-run dependency. It also removes population size, crossover probability/operator, mutation probability and tournament/elitism mechanisms. This is a complete independently executable workflow simplification, while preserving the nontrivial original scheduling/physical evaluator. It still requires documented stagnation, restart, tolerance, seeds and budget; it is not parameter-free.

The empirical repeated-search distributions, not a few thousandths in a selected minimum, support competitive planning quality. Cost records show attempted-query overhead separately from objective time. Instrumented GA records population diagnostics; ILS does not, so measured wall advantage is implementation-specific and cannot all be attributed to intrinsic algorithm complexity.

| method   |   budget |   n |   mean_wall_seconds |   mean_objective_seconds |   mean_attempts |   mean_cache_hits |
|:---------|---------:|----:|--------------------:|-------------------------:|----------------:|------------------:|
| ILS      |    20000 |  20 |              27.451 |                   26.749 |       21486.100 |          1486.100 |
| GA       |    20000 |  20 |              40.793 |                   27.090 |      158945.000 |        138945.000 |
| ILS      |    50000 |  20 |              69.381 |                   67.603 |       54101.650 |          4101.650 |
| GA       |    50000 |  20 |             104.895 |                   68.480 |      417476.500 |        367476.500 |
| ILS      |   100000 |  20 |             138.821 |                  135.252 |      108821.650 |          8821.650 |
| GA       |   100000 |  20 |             205.052 |                  135.888 |      791976.800 |        691976.800 |
| ILS      |   250000 |  10 |             352.673 |                  343.527 |      273476.600 |         23476.600 |
| GA       |   250000 |  10 |             536.740 |                  347.680 |     2060728.200 |       1810728.200 |
| ILS      |   500000 |  10 |             708.079 |                  689.710 |      546391.700 |         46391.700 |
| GA       |   500000 |  10 |            1094.946 |                  683.052 |     4482713.400 |       3982713.400 |

Main batch wall 2068.017s, summed recorded worker CPU 21392.891s, worker model/JIT setup 4.064s across12 workers. Setup objective calls total 20 across smoke/main. Worker CPU covers ILS search loops and GA wrapper intervals; setup/ILS checkpoint serialization/analysis/archive are not all included in that subtotal. ILS search wall excludes gzip checkpoint serialization; GA engine wall includes in-engine diagnostic checkpoint work, and incremental GA wrapper wall also includes final exports. Batch wall includes worker setup, concurrent scheduling and final exports. Full raw receipts retain these separate clocks; none is a universal hardware-independent speed estimate.

Strict accepted local moves, restart ranges, complete-cancellation counts, final cached restarts and repeated intermediate-permutation counts are retained in `ILS_OPERATOR_ACCOUNTING.csv` and the seed-level records. A compound restart does not necessarily change exactly 2/4/8 distinct stations and is not charged for its unscored intermediate permutations. No cancellation/revisit triggers an uncounted retry. Every cached full permutation in every final main state has been checked against the same complete 92-ID universe.

All20 complete production-size ILS trajectories also passed deterministic replay from their saved fitness caches: ordered keys, budget-prefix sequences/counters and final logical/RNG states match exactly. The audit read 6,000,000 saved fitness values, used 111.234s CPU/113.173s wall and made zero new physical objective calls. It is a reproducibility audit, not20 more search replicates or additional optimization. Intermediate checkpoint timer/gzip bytes were overwritten during continuation, so their observed digests are retained without pretending those exact intermediate payloads remain available; final states and exact logical replay are archived.

Verification completed all192 production/event comparisons, then JSON serialization failed on a NumPy integer leave-one-out count. The report was finalized from already saved round-trip numerical tables after casting that count, with zero repeated physical scoring. The first verification's whole-loop timer was not preserved before the exception and is explicitly unavailable; finalization time and all call counts are retained. A missing timer is not replaced by an estimate or silently counted as zero.

Historical swap/mixed and swap/2000-package results justify the reduced operator set conditionally. They do not establish a universal optimum or transfer warm-start effect sizes to Impact-only. The original200/800/2000 and1/2/4,2/4/8,4/8/16 screens and independent confirmations are reused, not repeated. General ILS literature supports the architecture; our exact constants remain engineering choices tested in this application.

The remaining scientific limitation is serious: a selected candidate's tiny advantage over frozenGA is influential-state sensitive and most planning states can worsen. That is not the reason for recommending a simpler algorithm and must not be presented as universal recovery superiority. This development collection was already inspected in previous work. Independent optimizer seeds are not fresh physical validation, and historical internal cross-fitting is diagnostic rather than untouched validation.

## Required Before Formal Replacement

Freeze this exact sequence, code, model hashes and selection procedure; obtain separate author authorization; run genuinely new paired physical confirmation under the prospective plan; assess modeled benefit versus Impact and comparative risk versus frozenGA; secure author approval for promotion. Until then the validated formalGA remains the operational authority. Do not reuse the completed2000-state cohort as untouched validation, silently replace official strategy files, or modify manuscript figures in this diagnostic branch.

The new prospective plan is preparation only. No new physical validation was executed. The previous frozenGA/old refinedILS validation pertains to those exact sequences, not this standalone procedure. See the concise one-algorithm proposedMethods and separate reviewer/supplemental audit; this study does not mandate two optimizers in the paper.
