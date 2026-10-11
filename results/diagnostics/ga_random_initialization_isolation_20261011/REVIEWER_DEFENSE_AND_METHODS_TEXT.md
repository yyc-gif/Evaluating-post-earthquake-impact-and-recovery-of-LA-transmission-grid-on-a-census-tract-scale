# Reviewer Defense And Publication Methods

## Proposed Main Methods

Restoration priorities were encoded as permutations of the 92 substations. The initial population comprised 100 independently sampled random permutations. No previously optimized chromosome or engineered neighbor was supplied. Fitness was the negative mean population-weighted service-loss integral over the same 64 planning realizations, using the unchanged 57-crew scheduler, directed travel and source-connected functionality constraint. The GA used population size 100, ordered crossover with probability 0.80, swap mutation with probability 0.10, tournament size 3 and one generational elite. Best-observed retention included every scored improvement at the distinct-evaluation boundary. Adaptive mutation, restart and diversity replacement were disabled.

Independent searches used prespecified seeds 2026103100-2026103119 and 100,000 distinct scored permutations per seed. The first ten trajectories were reserved prospectively for continuation to 250,000 and 500,000 evaluations when the 100k initialization criterion remained unresolved. Parameters were fixed at a previously investigated reproducible reference setting; this study varied initialization alone. Finite-budget search performance is not a guarantee of global optimality.

## Proposed Supplementary Text

Initialization sensitivity compared 100 random chromosomes against replacement of position zero by Impact-first in a shared 100-permutation pool. Both configurations entered reproduction with the same post-initializer RNG state and independent empty caches and archives. No prior optimized information was injected. The replication unit was the optimizer seed; differences were PURE_RANDOM minus IMPACT_SEEDED loss. We report paired t intervals, 20,000 seed-block bootstrap intervals and familywise Bonferroni intervals for five declared endpoints. Reserved continuations are not additional independent searches. The prospective numerical tolerance was 0.001 equivalent full-service hours (3.6 s), a computational criterion rather than an established practical policy threshold.

| Budget   | Pairs   | Pure mean (h)   | Seeded mean (h)   | Pure - seeded (h)   | Simultaneous 95% CI (h)      | High quality, pure/seeded   |
|:---------|:--------|:----------------|:------------------|:--------------------|:-----------------------------|:----------------------------|
| 20000    | 20      | 33.028785947    | 33.010517324      | 0.018268623         | [0.009830590, 0.026706655]   | 0/0                         |
| 50000    | 20      | 33.000532750    | 33.001147925      | -0.000615175        | [-0.002325102, 0.001094753]  | 6/1                         |
| 100000   | 20      | 32.999093670    | 33.000381595      | -0.001287925        | [-0.002915146, 0.000339297]  | 10/5                        |
| 250000   | 10      | 32.997675976    | 33.000009277      | -0.002333300        | [-0.004482882, -0.000183718] | 8/3                         |
| 500000   | 10      | 32.997675976    | 33.000009277      | -0.002333300        | [-0.004482882, -0.000183718] | 8/3                         |

The recommended initialization is `PURE_RANDOM_GA`. Search contribution is improvement beyond the best actually scored generation-zero chromosome; the Impact seed's initial advantage is not counted as new GA discovery. Initial populations, complete orders and hashes, strict-improvement histories, duplicates, distinct work, generation boundaries, timings, RNG states and exact 64-state production checks accompany the results. Cost includes diagnostic bookkeeping and serialization, not solely intrinsic algorithm operations. Optimizer uncertainty is conditional on fixed planning realizations and does not establish out-of-sample policy performance. New sequences remain diagnostic.

The final initialization recommendation is a disclosed post-data methodological judgment, not the outcome of the registered automatic fallback. That fallback required two-sided numerical equivalence and 90% proximity to a selected reference, neither of which is claimed. The unchanged full 20-seed 100k upper difference bound is below the predeclared 0.001 h tolerance, while the reserved higher-budget contrasts favor pure random. Stronger reserved-subset performance is not attributed to budget alone. All registered comparisons and unsuccessful runs remain reported, and no formal strategy is replaced.

## Reviewer Boundaries

The historical 93.06% inherited-improvement figure described one selected continuation, not independent GA efficacy. This study tests that distinction without using validation outcomes. A heuristic seed is an independently computable initialization, not a previous optimization stage. Empty archives and reproduction parity are verified. A zero-crossing interval is not equivalence, occasional exact-score wins are not reliability, and a plateau is not proof of a global optimum. The existing manuscript and formal strategy remain unchanged. This file supplies proposed text only, not evidence that the formal method has been replaced.

## Fixed-Parameter Rationale And Evidence Limits

| Fixed choice | Reproducible rationale | Qualification |
| --- | --- | --- |
| Population 100 | A bounded reference that avoids changing both population and initializer composition in this test | Earlier 50/250/500 comparisons changed neighbor/random allocations; they do not prove 100 is best |
| Ordered crossover 0.80 | Existing permutation-preserving operator; 0.60/0.95 conditional contrasts did not resolve superiority | Not an initialization-specific optimum |
| Swap mutation 0.10 | Existing permutation-preserving move; prior operator and 0.05/0.20 conditional studies support a working reference | Exact probability and its interactions remain conditional |
| Tournament 3 | Earlier tournament 2 was materially worse; tournament 5 advantage did not resolve in higher-budget contrasts | Do not claim 3 universally beats 5 |
| One elite | Explicit current-population survival with separate passive best-observed retention | Fixed0/1/2/3 controls did not establish a unique elite-count optimum |
| No adaptation/restart/diversity replacement | Preserves the specified single GA and isolates initialization | Does not rule out untested enabled alternatives |
| 20 seeds, exact distinct budget | Registered independent optimizer replications and reproducible finite work | Conditional 64-state performance, not physical validation or global convergence |

Numerical source: `results/diagnostics/ga_ils_parameter_defense_20261010/GA_PARAMETER_DEFENSIBILITY_REPORT.md`, `ga_initialization_reconciliation_20261009/GA_INITIALIZATION_AND_PARAMETER_DECISION_20261009.md`, and their accompanying conditional contrast tables. The present new initialization does not retroactively validate every parameter under every starting distribution. Parameters were held fixed to avoid confounding the initialization intervention; no new tuning was performed. Initialization controls, source hashes and implementation parity are directly tested here.
