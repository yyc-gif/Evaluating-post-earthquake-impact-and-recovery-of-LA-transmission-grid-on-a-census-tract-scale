# Bounded higher-budget parameter evidence

Nine one-factor variants, twenty GA seeds (100-119), 100, 000 distinct expensive objective evaluations per run. The twenty controls are reused from Actions 38006365076, with exact initial-population hash parity and evaluator/model source parity verified. Five additional historical seed controls (42-46) were replayed to 20k from their saved local objective caches, with zero new fitness evaluations: all reproduced the cloud best-sequence identity and objective error was at most 1.422e-13 h. This supports comparability for those five checks, not a claim of bitwise local replay of all 100k controls 100-119. Baseline: population 100, ordered crossover 0.80, swap mutation 0.10, tournament 3, one surviving elite, seven heuristic seeds, one exact inherited chromosome, 25 inversion neighbors and 67 random permutations. The inherited chromosome and 64 original planning samples retain their identities. The kernel retains H_plan = 2855.2540131100995 h; the existing order-independent planning-horizon audit establishes zero post-480 loss for these fixed inputs, so the endpoint is equivalent to 0-480 h here. Neither the kernel horizon nor the objective was changed.

`PARAMETER_FOLLOWUP_DESIGN.json` was committed at 62459f947e978fa3c6ce81e929dfa06f1abf5b14 before any new parameter result. The maximum five-seed 20k screening SD predicts a pointwise half-width of 0.003740 h at twenty seeds, against a predeclared 0.004 h optimizer-estimation precision target. The target resolves roughly one tenth of the previously observed post-warm-start gain; it is not a scientific equivalence margin. Pilot variance is imprecise and may not transfer to 100k. Actual precision is reported below; twenty seeds are not automatically sufficient.

## Final fixed-budget effects

Variant minus same-seed reference, h; negative favors the variant. Intervals concern expected GA search outcome conditional on the same repeatedly used 64 planning realizations. Bootstrap uses 50, 000 whole GA-seed resamples. Bonferroni t intervals cover nine final-budget contrasts. The 20k/50k checkpoints are repeated-budget descriptions, not new independent seeds, and their intervals are not simultaneous bands across all budgets.

| case | mean_loss_hr | mean_initial_change_hr | mean_postinitialization_gain_change_hr | mean_change_hr | t95_low_hr | t95_high_hr | bootstrap95_low_hr | bootstrap95_high_hr | bonferroni95_low_hr | bonferroni95_high_hr | pointwise_halfwidth_hr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| crossover060 | 33.000265 | -0.000000 | -0.000080 | 0.000080 | -0.001015 | 0.001174 | -0.000913 | 0.001079 | -0.001555 | 0.001715 | 0.001094 |
| crossover095 | 33.000110 | -0.000000 | 0.000075 | -0.000075 | -0.001003 | 0.000854 | -0.000893 | 0.000794 | -0.001462 | 0.001312 | 0.000929 |
| mutation005 | 33.000526 | -0.000000 | -0.000341 | 0.000341 | -0.000666 | 0.001349 | -0.000572 | 0.001258 | -0.001164 | 0.001846 | 0.001008 |
| mutation020 | 32.999960 | -0.000000 | 0.000225 | -0.000225 | -0.001233 | 0.000782 | -0.001119 | 0.000712 | -0.001730 | 0.001279 | 0.001007 |
| tournament2 | 33.026285 | -0.000000 | -0.026100 | 0.026100 | 0.018448 | 0.033753 | 0.018731 | 0.032531 | 0.014669 | 0.037531 | 0.007652 |
| tournament5 | 32.999668 | -0.000000 | 0.000517 | -0.000517 | -0.001428 | 0.000395 | -0.001345 | 0.000330 | -0.001879 | 0.000845 | 0.000911 |
| population50 | 32.999698 | -0.000000 | 0.000487 | -0.000487 | -0.001472 | 0.000499 | -0.001360 | 0.000432 | -0.001959 | 0.000986 | 0.000986 |
| population250 | 33.000350 | -0.000000 | -0.000165 | 0.000165 | -0.000808 | 0.001139 | -0.000703 | 0.001067 | -0.001289 | 0.001619 | 0.000973 |
| population500 | 33.000535 | -0.000034 | -0.000385 | 0.000350 | -0.000681 | 0.001382 | -0.000586 | 0.001299 | -0.001190 | 0.001891 | 0.001031 |

| case | effect_hr | simultaneous_low_hr | simultaneous_high_hr | status |
| --- | --- | --- | --- | --- |
| crossover060 | 0.000080 | -0.001555 | 0.001715 | Unresolved; neither superiority nor equivalence established |
| crossover095 | -0.000075 | -0.001462 | 0.001312 | Unresolved; neither superiority nor equivalence established |
| mutation005 | 0.000341 | -0.001164 | 0.001846 | Unresolved; neither superiority nor equivalence established |
| mutation020 | -0.000225 | -0.001730 | 0.001279 | Unresolved; neither superiority nor equivalence established |
| tournament2 | 0.026100 | 0.014669 | 0.037531 | Higher mean on fixed planning objective; not preferred at this budget |
| tournament5 | -0.000517 | -0.001879 | 0.000845 | Unresolved; neither superiority nor equivalence established |
| population50 | -0.000487 | -0.001959 | 0.000986 | Unresolved; neither superiority nor equivalence established |
| population250 | 0.000165 | -0.001289 | 0.001619 | Unresolved; neither superiority nor equivalence established |
| population500 | 0.000350 | -0.001190 | 0.001891 | Unresolved; neither superiority nor equivalence established |

## Population initialization counts

| Population | Heuristics | Exact prior copies | Prior neighbors | Impact neighbors | Random | Elites |
| --- | --- | --- | --- | --- | --- | --- |
| 50 | 7 | 1 | 6 | 6 | 30 | 1 |
| 100 | 7 | 1 | 13 | 12 | 67 | 1 |
| 250 | 7 | 1 | 31 | 31 | 180 | 1 |
| 500 | 7 | 1 | 63 | 62 | 367 | 1 |

Neighbor count follows the existing floor(population/4) rule. Seven heuristic chromosomes and one exact inherited copy remain fixed counts; random permutations fill the remainder. Heuristic, exact-copy and elite percentages therefore decrease with population size. These are conditional population-plus-composition effects, not a pure population effect at fixed percentages. The initialization experiments do not justify this allocation as optimal; it remains the explicit common comparison recipe.

## Cost and budget stability

| case | seed_count | distinct_evaluations | total_attempts | duplicate_call_fraction | min_generations | median_generations | max_generations | cpu_seconds | mean_run_wall_seconds | max_peak_rss_mb |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| crossover060 | 20 | 2000000 | 20189626 | 0.900939 | 4579 | 5047.000000 | 5473 | 3770.390625 | 188.794733 | 299.316406 |
| crossover095 | 20 | 2000000 | 14056557 | 0.857718 | 3174 | 3502.500000 | 3854 | 5295.796875 | 265.334285 | 290.921875 |
| mutation005 | 20 | 2000000 | 29497330 | 0.932197 | 6406 | 7393.000000 | 9024 | 6199.562500 | 310.384580 | 317.015625 |
| mutation020 | 20 | 2000000 | 9940449 | 0.798802 | 2277 | 2480.500000 | 2656 | 4649.062500 | 232.885828 | 284.925781 |
| population250 | 20 | 2000000 | 12733373 | 0.842932 | 1068 | 1260.500000 | 1442 | 4379.968750 | 219.571505 | 287.027344 |
| population50 | 20 | 2000000 | 29691069 | 0.932640 | 12820 | 14835.000000 | 17522 | 5964.296875 | 298.283558 | 349.996094 |
| population500 | 20 | 2000000 | 12457643 | 0.839456 | 545 | 615.000000 | 702 | 4938.609375 | 247.676096 | 288.445312 |
| tournament2 | 20 | 2000000 | 6688794 | 0.700992 | 1270 | 1280.500000 | 3498 | 4521.687500 | 226.682858 | 289.621094 |
| tournament5 | 20 | 2000000 | 16673998 | 0.880053 | 3688 | 4136.500000 | 4554 | 4844.218750 | 242.611346 | 294.835938 |

All 180 new searches completed 100k distinct queries: 18, 000, 000 expensive search evaluations, plus 1, 440 documented setup-parity scores outside the budgets. Cached attempts still incur overhead. Cloud-control and local-worker wall times are from different hardware/concurrency and are not a controlled hardware-efficiency comparison. Actual completed/partial generation counts are recorded; no common generation count is invented.

The first coordinator used six workers. Additional twelve-worker, six-worker and four-worker coordinators accelerated the same fixed jobs with atomic process claims. There were at most twenty-eight allocated process slots; some slots only waited on an owner or reused a completed record, so this is not a measured peak active-compute count. An overlapping process waits or reuses the completed observation; it does not repeat its search. Coordinator process counts must not be summed as new scientific observations. Per-run deduplicated records are the cost authority.

Pointwise precision target met for 8/9 contrasts; simultaneous precision target met for 8/9. No seed count was enlarged in response to a p-value. `PARAMETER_BUDGET_STABILITY.csv` reports higher-minus-lower-budget changes in variant-control effects within the same twenty seeds.

## Recommendation scope

The decision table can favor or disfavor tested conditional one-factor packages on this planning objective at 100k. It does not justify combining individually favorable settings without a joint test, extrapolating across budgets, or claiming exact initialization percentages are optimal. A nonzero effect is not necessarily scientifically consequential; no prospective scientific tolerance was approved. For unresolved contrasts, retain the existing comparison setting rather than picking the lowest mean. No new setting is promoted automatically.

Population 100 / crossover 0.80 / swap 0.10 / tournament 3 / one elite remains the stable reporting reference, with initialization disclosed as a working recipe. A reproducibly favorable conditional alternative is reported as a diagnostic option, with its interval and variability. Method/candidate replacement requires author approval. New operators, interactions, true no-prior/archive controls and physical-sample generalization were not tested here.

All selected-permutation identities remain diagnostic. No new physical samples, proposed independent validation, formal strategy replacement or manuscript-artwork change occurred.
