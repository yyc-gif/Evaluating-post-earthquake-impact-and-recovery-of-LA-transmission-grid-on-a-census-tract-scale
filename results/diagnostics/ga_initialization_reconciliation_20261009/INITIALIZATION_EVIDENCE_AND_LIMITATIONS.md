# Initialization evidence and remaining uncertainty

Revision source: `031d2c675f8e7d58035d27448be040b809ced086`. Diagnostic source: `9142b9994b34ff023edd47bf18b90d36a6743c69`. This analysis uses the completed cloud artifacts, not reruns of their GA batches. Lower planning service loss is better. All estimates concern GA randomness conditional on the same 64 saved 2pc50 planning realizations and the unchanged evaluator, scheduler, mapping and source gate. They are not uncertainty estimates for a new earthquake cohort. The original H_plan = 2855.2540131100995 h is retained; the existing planning-horizon audit establishes equivalence to the 0-480 h endpoint for these fixed inputs, and no new horizon or normalization is imposed.

## Reconciliation and observation unit

Actions [38006187607](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38006187607) contains 17 configurations for each of seeds 100-129 at 20, 000 distinct queries: 510 runs. Actions [38006365076](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38006365076) contains five configurations for each of seeds 100-119 at 100, 000 queries: 100 runs. All 50 artifact archives match their GitHub SHA-256 digests. `CLOUD_ARTIFACT_MANIFEST.json` records immutable source commits, IDs, archive hashes and members.

There are 610 unique final-budget run observations. The 610 per-case JSON copies and 543 previously committed partial-chunk records repeat these observations and are excluded from the analytic dataset. Their immutable sources remain available. The 100 repeated 20k prefixes have identical initial-population hashes; 90 objectives agree bitwise and ten differ by at most 2.274e-13 h (comparison tolerance 1e-10 h). Their prefix records are not counted as additional replicates. The high-budget source asserts both 100k expensive calls and 100k cache entries before exporting each record. Its field named `completed_generations` actually exports the current state generation, which may be partial; the reconciled table flags this and does not claim to know the last fully completed generation.

There are 30 distinct seed identities; the 20 higher-budget seeds are a subset, not 20 additional independent identities. Thirty plus twenty is not a 50-seed study. Actual search-query cost was 20.2 million per-run distinct objective calls; 2.0 million are paid replays of the 20k prefixes. Removing those prefixes leaves 18.2 million query-path entries, not a claim of globally unique permutations across runs.

## What was changed

| case | heuristics | exact_prior_copies | inversion_neighbors | prior_derived_neighbors | impact_derived_neighbors | random_permutations |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_7h_1w_25n | 7 | 1 | 25 | 13 | 12 | 67 |
| heuristics_0 | 0 | 1 | 25 | 13 | 12 | 74 |
| heuristics_1_impact | 1 | 1 | 25 | 13 | 12 | 73 |
| heuristics_3_top | 3 | 1 | 25 | 13 | 12 | 71 |
| heuristics_6_no_fixed_random | 6 | 1 | 25 | 13 | 12 | 68 |
| warm_copies_0 | 7 | 0 | 25 | 13 | 12 | 68 |
| warm_copies_3 | 7 | 3 | 25 | 13 | 12 | 65 |
| warm_copies_5 | 7 | 5 | 25 | 13 | 12 | 63 |
| neighbors_0 | 7 | 1 | 0 | 0 | 0 | 92 |
| neighbors_10 | 7 | 1 | 10 | 5 | 5 | 82 |
| neighbors_50 | 7 | 1 | 50 | 25 | 25 | 42 |
| neighbors_75 | 7 | 1 | 75 | 38 | 37 | 17 |
| neighbors_25_prior_only | 7 | 1 | 25 | 25 | 0 | 67 |
| neighbors_25_impact_only | 7 | 1 | 25 | 0 | 25 | 67 |
| neighbors_25_prior_25pct | 7 | 1 | 25 | 6 | 19 | 67 |
| neighbors_25_prior_75pct | 7 | 1 | 25 | 19 | 6 | 67 |
| heuristics_only | 7 | 0 | 0 | 0 | 0 | 93 |

All cases preserve ordered crossover 0.80, swap mutation 0.10, tournament size 3, one surviving elite, population 100, and a separately preserved heuristic incumbent archive. Each chromosome is a complete 92-station permutation. The seven original heuristic seeds include the saved Random rule as one deterministic seeded sequence; it differs from newly sampled uniform random permutations. The three-heuristic case seeds Impact-first, Hospital-first and Closeness-first. Changes to counts replace slots that would otherwise contain random permutations. Neighbor-source changes also alter the exact initialization and subsequent RNG stream.

The neighbor-source labels 25% and 75% are nominal: rounding gives 6/25 = 24% and 19/25 = 76% prior-derived neighbors. The alternating baseline gives 13/25 = 52%, not exactly 50%. Exact counts in the table govern reproduction.

The inherited sequence is the previous p100/g2000/seed 46 result, J = 33.03813174326729 h, SHA-256 `3bfeafdd1adf950749e63fdbbe3b7efc21b1efd04c3b3d64c28c3d118717bbed`. Its earlier discovery cost is inherited development effort and is not included in these new run budgets. The seven-heuristic archive begins with Impact-first, J = 33.57830255999924 h.

## Control limitations

- `heuristics_0` removes the heuristic chromosomes from the evolving initial population. All seven heuristics are still evaluated and the best heuristic is retained in the archive. Twelve Impact-derived neighbors also remain. This is not removal of heuristic information.
- `warm_copies_0` removes only the exact prior-best chromosome. Thirteen inversion neighbors of that chromosome remain. This is not removal of all inherited GA information.
- `heuristics_only` removes the exact inherited sequence and all local neighbors, including Impact-derived neighbors; seven heuristic chromosomes and 93 uniform random permutations remain, with the same heuristic archive. It is a joint package comparison, not a clean isolated estimate of the exact warm-copy effect.
- `neighbors_0` retains the exact inherited sequence and all seven heuristics. It tests whether these local neighbors help at a given budget, not whether warm starts help.
- Repeated warm copies consume population slots but do not multiply expensive objective calls for the identical permutation because of caching.

These are one-factor composition contrasts conditional on a fixed population size. They do not identify independent additive contributions of all counts or their interactions. Same seed pairs provide a valid comparison across search realizations, but do not guarantee identical post-initialization random draws.

## Paired effects, not a lowest-mean contest

Variant minus 7/1/25/67 baseline, h; negative favors the variant. Pointwise intervals are paired GA-seed t intervals. The CSV also contains 50, 000-resample percentile-bootstrap intervals, familywise Bonferroni t intervals, medians and seed-level differences. The family contains 16 contrasts at 20k and four at 100k. These comparisons remain conditional and exploratory; the experiment was not preregistered with a scientific equivalence margin.

| budget | case | mean_change_hr | t95_low_hr | t95_high_hr | bootstrap95_low_hr | bootstrap95_high_hr | bonferroni95_low_hr | bonferroni95_high_hr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20000 | heuristics_0 | -0.000670 | -0.001962 | 0.000623 | -0.001880 | 0.000562 | -0.002707 | 0.001367 |
| 20000 | heuristics_1_impact | -0.000694 | -0.002082 | 0.000695 | -0.001986 | 0.000636 | -0.002883 | 0.001496 |
| 20000 | heuristics_3_top | 0.000793 | -0.000384 | 0.001970 | -0.000316 | 0.001882 | -0.001062 | 0.002648 |
| 20000 | heuristics_6_no_fixed_random | -0.000845 | -0.002303 | 0.000613 | -0.002127 | 0.000607 | -0.003143 | 0.001453 |
| 20000 | heuristics_only | 0.007447 | 0.005322 | 0.009572 | 0.005437 | 0.009434 | 0.004098 | 0.010796 |
| 20000 | neighbors_0 | -0.000268 | -0.001689 | 0.001154 | -0.001603 | 0.001071 | -0.002508 | 0.001973 |
| 20000 | neighbors_10 | -0.000148 | -0.001748 | 0.001452 | -0.001634 | 0.001386 | -0.002670 | 0.002374 |
| 20000 | neighbors_25_impact_only | -0.000220 | -0.001290 | 0.000849 | -0.001238 | 0.000774 | -0.001906 | 0.001465 |
| 20000 | neighbors_25_prior_25pct | -0.000396 | -0.001477 | 0.000686 | -0.001404 | 0.000627 | -0.002100 | 0.001309 |
| 20000 | neighbors_25_prior_75pct | -0.000968 | -0.002256 | 0.000320 | -0.002180 | 0.000250 | -0.002998 | 0.001062 |
| 20000 | neighbors_25_prior_only | -0.000466 | -0.001864 | 0.000932 | -0.001776 | 0.000853 | -0.002670 | 0.001737 |
| 20000 | neighbors_50 | -0.000205 | -0.001138 | 0.000728 | -0.001083 | 0.000678 | -0.001675 | 0.001266 |
| 20000 | neighbors_75 | 0.000195 | -0.000973 | 0.001362 | -0.000857 | 0.001342 | -0.001645 | 0.002034 |
| 20000 | warm_copies_0 | -0.000397 | -0.001663 | 0.000870 | -0.001583 | 0.000788 | -0.002393 | 0.001599 |
| 20000 | warm_copies_3 | 0.000183 | -0.001119 | 0.001485 | -0.001054 | 0.001391 | -0.001869 | 0.002235 |
| 20000 | warm_copies_5 | -0.000523 | -0.002024 | 0.000978 | -0.001927 | 0.000908 | -0.002889 | 0.001843 |
| 100000 | heuristics_0 | -0.000014 | -0.000835 | 0.000807 | -0.000765 | 0.000743 | -0.001096 | 0.001068 |
| 100000 | heuristics_only | 0.001609 | 0.000111 | 0.003107 | 0.000271 | 0.003022 | -0.000365 | 0.003583 |
| 100000 | neighbors_0 | -0.000603 | -0.001637 | 0.000431 | -0.001517 | 0.000360 | -0.001965 | 0.000759 |
| 100000 | neighbors_50 | -0.000294 | -0.001257 | 0.000670 | -0.001151 | 0.000613 | -0.001563 | 0.000976 |

At 20k, the package without inherited GA information and local neighbors performs worse by 0.007447 h on average, with pointwise 95% interval [0.005322, 0.009572] h and simultaneous interval [0.004098, 0.010796] h. Initial best loss is worse by 0.540171 h, while evolutionary improvement after initialization is greater by 0.532724 h. Most of the initial advantage is recovered during search; the final advantage is much smaller than the generation-zero difference.

At 100k, the same package difference shrinks to 0.001609 h: pointwise interval [0.000111, 0.003107], bootstrap [0.000271, 0.003022], simultaneous interval [-0.000365, 0.003583] h. Report all three; the familywise result does not establish a residual package effect at this budget. It also does not establish equivalence. In the same twenty seeds, this contrast shrinks by 0.006069 h from 20k to 100k, with pointwise interval [-0.008856, -0.003281] h.

Removing the exact warm copy while retaining its neighbors initially raises mean loss by 0.007430 h. Its final 20k change is -0.000397 h, interval [-0.001663, 0.000870]. Changing heuristic counts, exact-copy counts, neighbor counts or neighbor sources produces unresolved small final effects. No result identifies 7/1/25/67, 25% neighbors, one copy or a particular neighbor-source split as optimal. The best 20k mean belongs to the nominal 75%-prior-neighbor case (19 of 25 neighbors), but that observation alone is not a reproducible selection rule.

## Computational-budget dependence

The following 100k values use the same twenty seeds at each checkpoint, not the thirty-seed 20k aggregate.

| case | initial_mean_hr | final_mean_hr | final_sd_hr | best_hr | mean_minus_20k_same_seeds_hr |
| --- | --- | --- | --- | --- | --- |
| baseline_7h_1w_25n | 33.038132 | 33.000185 | 0.001307 | 32.998492 | -0.003998 |
| heuristics_0 | 33.038132 | 33.000171 | 0.001525 | 32.998492 | -0.003206 |
| heuristics_only | 33.578303 | 33.001794 | 0.003060 | 32.997748 | -0.010067 |
| neighbors_0 | 33.038132 | 32.999582 | 0.001370 | 32.997723 | -0.003884 |
| neighbors_50 | 33.038132 | 32.999891 | 0.001531 | 32.997841 | -0.004099 |

The baseline mean falls from 33.004183 h at 20k to 33.000503 h at 50k and 33.000185 h at 100k. Initialization-package advantage declines with more search, whereas other allocation differences remain unresolved. The higher-budget experiment covers only five initialization cases; claims about warm-copy counts and the remaining source fractions at 100k are unsupported.

The best individual higher-budget observation is 32.997722786 h (`neighbors_0`), below the currently recorded formal method candidate value. This is an exploratory initialization-search observation, not an authorized replacement. A single best seed is neither a mean-performance comparison nor independent physical validation.

## What thirty seeds establish

The widest pointwise mean-effect half-width is 0.002125 h at 20k and 0.001498 h at 100k. Precision varies by contrast, and larger-budget evidence has fewer seeds. `PRACTICAL_TOLERANCE_PRECISION.csv` tests descriptive containment in +/-0.0005, 0.001, 0.002, 0.005 and 0.010 h, for pointwise and simultaneous intervals. No such margin was prospectively approved as scientifically negligible, so `equivalence_established` is false throughout.

At a hypothetical +/-0.001 h tolerance, the 100k interval for `heuristics_0` lies inside the margin pointwise but its simultaneous interval extends outside it; the neighbor-count contrasts are unresolved at that margin. An author-specified, scientifically defended tolerance and an appropriate equivalence design would be required for an equivalence claim. Failure to reject zero is not evidence of equality, and thirty seeds do not certify future-seed reliability or generalization beyond the planning inputs.

## Initialization recommendation

Use the existing 7/1/25/67 mixture as a documented comparison reference while the separate parameter study is completed, not as a newly validated optimum. Preserve the exact prior-best input identity and disclose its discovery history. The 20k evidence supports a finite-budget advantage of the inherited-information package; exact allocation percentages are indistinguishable or unresolved at the achieved precision. No tuning used the proposed independent physical-validation cohort. No new physical samples, formal strategy or manuscript artwork were changed.
