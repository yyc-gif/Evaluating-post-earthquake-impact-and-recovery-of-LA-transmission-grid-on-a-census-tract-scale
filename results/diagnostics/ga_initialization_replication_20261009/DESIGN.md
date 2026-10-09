# Preregistered GA initialization allocation robustness study

This document and the two execution scripts were committed **before** observing any of the fresh seeds 100–129. The starting authority is commit `b1030f839d522fed4af21e424472e3f8b076797b`; scientific evaluator, 64 2pc50/C57_D1 planning realizations, 92-station domain, objective, solver, and validation datasets are unchanged. This is **algorithm random-seed** robustness, **not physical-realization generalization**.

## Primary diagnostic and estimand

Compare each alternate initialization against the exact pinned final-GA initializer (7 heuristics + 1 prior best + 25 inversion neighbors, comprising 13 prior-best and 12 Impact-first neighbors + 67 new random permutations), using **30 fresh GA seeds 100–129** and **20,000 distinct objective evaluations per seed and allocation**. Same seeds and objective budget across all 17 allocations. Outcomes: final best planning loss (primary for these diagnostics), generation-zero best, evolution-only improvement, number of attempted/duplicate evaluations, generation-zero diversity and wall time.

A seed's outcomes are paired across allocations, but changed initialization consumes different random draws, so identical seed numbers do not mean identical downstream random streams. Report across-seed means, medians and dispersion; paired contrast vs pinned baseline with an interval (bootstrap resampling complete GA seeds) and win fractions, plus unadjusted exploratory / multiplicity-aware analyses as appropriate. Never claim the ratios are global or universal optima. Do not treat related contrasts as independent additive causal contributions.

## Frozen 17-level screening table

| Case | Heuristics | Prior-best exact copies | Inversion neighbors | Source of neighbors | New uniformly random |
|---|---:|---:|---:|---|---:|
| baseline_7h_1w_25n | 7 | 1 | 25 | 13 prior, 12 Impact | 67 |
| heuristics_0 | 0 | 1 | 25 | split | 74 |
| heuristics_1_impact | 1 | 1 | 25 | split | 73 |
| heuristics_3_top | 3 | 1 | 25 | split | 71 |
| heuristics_6_no_fixed_random | 6 | 1 | 25 | split | 68 |
| warm_copies_0 | 7 | 0 | 25 | split | 68 |
| warm_copies_3 | 7 | 3 | 25 | split | 65 |
| warm_copies_5 | 7 | 5 | 25 | split | 63 |
| neighbors_0 | 7 | 1 | 0 | none | 92 |
| neighbors_10 | 7 | 1 | 10 | split | 82 |
| neighbors_50 | 7 | 1 | 50 | split | 42 |
| neighbors_75 | 7 | 1 | 75 | split | 17 |
| neighbors_25_prior_only | 7 | 1 | 25 | 25 prior | 67 |
| neighbors_25_impact_only | 7 | 1 | 25 | 25 Impact | 67 |
| neighbors_25_prior_25pct | 7 | 1 | 25 | 6 prior, 19 Impact | 67 |
| neighbors_25_prior_75pct | 7 | 1 | 25 | 19 prior, 6 Impact | 67 |
| heuristics_only | 7 | 0 | 0 | none | 93 |

"Split" refers to alternating sources in the original order. The three "top" fixed heuristics were preselected from existing historical 64-sample planning losses: Impact-first, Hospital-first, Closeness-first; the complete seven also include a *fixed* Random heuristic, distinct from new RNG draws.

**Compositional identifiability:** Total population is held at 100. Increasing one component necessarily replaces uniformly random chromosomes; estimates are conditional substitution effects, not independent percent-point causal effects of a full factorial.

The original GA engine evaluates the seven incumbent reference sequences before filling any evolving population. Those reference scores remain available to the archive even if an ablation omits one or all heuristic chromosomes from the evolving population; this is explicitly part of the estimator and avoids changing the scientific incumbent authority.

## Cross-budget check

A separate **20-seed, 100,000-distinct-evaluation** study for seeds 100–119, with five *preselected* cases baseline, heuristics_only, neighbors_0, neighbors_50 and heuristics_0, is committed before analyzing the new 30-seed 20k results. The same seed values at 20k and 100k allow budget-level comparisons but are **not independent seed cohorts**. All 100k runs restart from scratch and pay their prefix cost again; zero-cost continuation is not claimed.

## Limitations and decision boundaries

- Observed parameter invariance over tested ranges is a sensitivity result, not mathematical optimality, and a missing measurable difference is not proof of equivalence.
- 30 GA seeds are not a universally sufficient number: confidence precision depends on effect variance and the scientific tolerance of interest.
- These results concern the fixed 64 optimization realizations only. Do not inspect untouched 2000-realization physical validation for method selection.
- Never promote a different formal GA sequence or reselect candidate based on this diagnostic without a revised and separately documented protocol.
- All diagnostic code and summaries remain on the isolated `diagnostics/ga-initialization-and-hyperparameters-20261009` branch. Original formal, manuscript, artwork and protected files are unchanged.
