# Complete Workflow Complexity

| Dimension | Existing validated GA | Truly standalone ILS |
|---|---|---|
| Numeric search controls excluding shared seeds/budget | P100, crossover0.8, mutation0.1, tournament3, elites1; plus25 neighbors | tolerance1e-12, stagnation2000, cycle2/4/8 |
| Search operators | ordered crossover + swap mutation + parent tournament + population elitism | swap only; perturbation repeats same operation |
| Initial information | seven heuristic policies, optimized prior and prior/Impact inversion neighbors | only fixed Impact-first |
| Prior optimizer dependency | actual formal workflow includes earlier optimized prior | none |
| Extra refinement | not needed for formal GA | forbidden and absent |
| State required for exact resume | population/scores, generation phase, offspring, parent metadata, RNG, archive/cache | current/score, RNG, archive/cache, stagnation/perturb phase |
| Empirical calibration | original population/operator/initialization/pressure evidence | historical conditional neighborhood/restart evidence + fresh Impact-only package test |
| Reproduction overhead | cached population scans and duplicate offspring | cached swapped permutations and restart evaluations |
| Independent future validation | previous fixed candidate already confirmed | genuinely new physical confirmation still needed |

Counting scalar fields alone is misleading: the ILS cycle has three values, both need a numerical acceptance/tie convention, cache, safety cap, initializer, seed protocol and selection rule. The reduction is fewer mechanisms and no external optimized starting information. The fixed scheduling decoder and source gate remain equally complex in both workflows; none of that physics is removed.

Measured distributions/costs: `OPTIMIZER_DISTRIBUTIONS.csv`; full paired seed/budget values: `BUDGET_CONVERGENCE_AND_COST.csv`. Instrumentation differs, so wall ratios are not universal speedup claims. Archive/checkpoint storage is diagnostic reproducibility overhead, not another optimizer. Variability is reported as SD/range over independent optimizer seeds, not variation over physical populations.

Primary recommendation: **RECOMMEND STANDALONE ILS AS THE REPLACEMENT CANDIDATE**. ILS independence, simpler complete workflow and conditional optimization reliability are distinct from independent physical generalization. More calibration is not automatically required to claim unique optimum; no such optimum is claimed.
