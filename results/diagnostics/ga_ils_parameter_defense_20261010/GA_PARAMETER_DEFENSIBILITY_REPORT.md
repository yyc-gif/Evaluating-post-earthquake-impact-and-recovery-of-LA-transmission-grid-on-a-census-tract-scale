# GA Parameter Defensibility Report

## Authority and Scientific Boundary

Starting commit `e7d05e2649f3be2ccfbf9398d86e0612407dd5ea`, isolated branch `diagnostics/ga-ils-reviewer-parameter-defense-20261010`. All new findings are postvalidation exploratory for the manuscript. Within this diagnostic study, the committed fixed contrasts and independent confirmation seeds are prospective; selecting two settings from the separate eight-seed engineering screen is explicitly recorded. No 2,000-realization outcomes were loaded for algorithm selection and no physical realizations were generated. The frozen formal GA configuration and sequence remain unchanged.

Negative paired differences favor the first-named method/setting. The replication unit is the optimizer seed, conditional on the same 64 planning states. Tables retain paired means, medians, SD, wins/losses/ties, pointwise t intervals, 20,000 seed-block bootstrap intervals and Bonferroni simultaneous intervals. These intervals concern optimizer variability, not physical population uncertainty. No equivalence margin was invented, and an interval containing zero is not evidence of equivalence.


The frozen objective is mean population-dependency-weighted service-loss hours across the original 64 2pc50/C57_D1 planning realizations. Station availability includes its own restoration, the 0.5 functionality threshold and connection to an active Core source. Directed travel, realization-specific damage and repair durations, crews, graph and population mapping are unchanged. The original compiled horizon remains 2855.2540131100995 h; the pre-existing planning horizon audit establishes zero post-480 loss for these fixed inputs, so this does not redefine the manuscript integral. This is not delivered MW, a capacity model, or a new fragility model.

## Parameter Decisions

| parameter             | selected_value                 | classification                | supports                                                                           |
|:----------------------|:-------------------------------|:------------------------------|:-----------------------------------------------------------------------------------|
| Representation        | 92-station permutation         | SUPPORTED                     | Valid encoding; not global optimality.                                             |
| Population            | 100                            | DEFENSIBLE WITH QUALIFICATION | Reasonable fixed reference, not uniquely best.                                     |
| Crossover operator    | ordered                        | SUPPORTED                     | Appropriate valid operator, not proven best.                                       |
| Crossover probability | 0.80                           | DEFENSIBLE WITH QUALIFICATION | Tested operating range, not optimum.                                               |
| Mutation operator     | swap                           | SUPPORTED                     | Conditional empirical operator support.                                            |
| Mutation probability  | 0.10                           | DEFENSIBLE WITH QUALIFICATION | Reasonable tested probability; not uniquely optimal.                               |
| Selection             | tournament, k=3                | DEFENSIBLE WITH QUALIFICATION | Avoid weak k2; k3 is defensible, not uniquely best.                                |
| Generational elitism  | 1                              | DEFENSIBLE WITH QUALIFICATION | Direct comparison now available; exact count remains qualified.                    |
| Initialization        | 7/1/25/67                      | DEFENSIBLE WITH QUALIFICATION | Transparent reproducible composition, not mathematical optimality.                 |
| Best-so-far retention | strict archive + query-best    | SUPPORTED                     | Correct incumbent protection, not evidence of independent discovery.               |
| Adaptive mutation     | disabled                       | DEFENSIBLE WITH QUALIFICATION | Defensible fixed omission; superiority over all enabled alternatives insufficient. |
| Restart               | disabled                       | DEFENSIBLE WITH QUALIFICATION | Defensible fixed omission; superiority over all enabled alternatives insufficient. |
| Diversity replacement | disabled                       | DEFENSIBLE WITH QUALIFICATION | Defensible fixed omission; superiority over all enabled alternatives insufficient. |
| Budget/stopping       | 20 x 100k + 5 continued x 500k | SUPPORTED                     | Finite reproducible allocation, not global convergence.                            |

The full matrix includes ten required audit dimensions per selection. SUPPORTED means support for an appropriate design/operator under tested conditions; it does not mean a universal optimum. Exact probabilities, population, composition, tournament size and elite count remain qualified fixed choices.

## Population and Selection

The same-budget 100k studies do not establish superiority of 100 over 50/250/500. Their initial compositions differ (heuristic/prior/neighbors/random): 7/1/12/30, 7/1/25/67, 7/1/62/180 and 7/1/125/367. Population comparisons therefore concern those packages, not pure population effects. At fixed distinct work, larger populations also execute fewer generations.

The older five-seed, 50k-query P100 inversion/no-elite screen had mean loss 33.126443 h at mutation 0.20, versus 33.572881 at 0.40 and 33.577103 at 0.60. These high-rate failures are retained as historical setting-specific evidence. They are not tests of final swap mutation at those probabilities. Similarly, early crossover 0.60/0.95 screens also changed mutation and cannot establish a pure crossover effect. The later nine-variant, fresh 20-seed 100k comparison isolates crossover 0.60/0.95 and swap mutation 0.05/0.20 against their reference probabilities; full effects and simultaneous intervals are in the matrix and HISTORICAL_PAIRED_STATISTICS.csv.

Tournament-2 deterioration is materially larger than unresolved small setting differences: +0.026100 h with nine-family simultaneous interval approximately [0.014669, 0.037531] at 100k. Tournament-5 beat 3 in the 20k factorial screen but not conclusively in fresh 100k or 500k contrasts. The independent 100k interaction estimates are population x tournament -0.000224304, tournament x mutation +0.000149262, and neighbor allocation x tournament +0.000182864 h; their intervals all cross zero. At 500k k5-minus-k3 is +0.000693217 h, interval [-0.000966832, 0.002353265]. Retaining k3 is defensible, not proof that k5 is inferior.

Legacy P500 underperformance cannot be attributed solely to weak tournament pressure or insufficient diversity. Its measured standardized parent intensity is approximately 0.804 versus 0.564 at P100, final positional entropy 0.835 versus 0.312, and effective parent count 179.09 versus 37.42. Larger raw diversity did not imply useful order exploration. The original reference chromosomes left the evolving population early while the passive best archive persisted. Subsequent quality initialization, survival and operator changes materially altered that behavior. Source: historical ORIGINAL_HISTORY_MECHANISM_SUMMARY.csv; new per-seed evidence NEW_GA_SEARCH_HISTORY_MECHANISMS.csv.

## Direct Elite-Count Experiment

The former no/one/three-elite screens partly changed other settings. The missing fixed-configuration 0/1/2/3 intervention was therefore executed: eight 20k seeds, then twenty independent 100k seeds. Initial-population fingerprints and post-initializer RNG states agree across all elite counts in every confirmation seed. Elite survival overwrites the offspring tail after the same reproduction draws; later trajectories can diverge. The archive itself does not inject a parent when restart is disabled.

| contrast                  |   mean_delta_hr |   simultaneous95_low_hr |   simultaneous95_high_hr |   wins |   losses |   ties |
|:--------------------------|----------------:|------------------------:|-------------------------:|-------:|---------:|-------:|
| ga_elite0 minus ga_elite1 |        0.000137 |               -0.001495 |                 0.001768 |     10 |        9 |      1 |
| ga_elite2 minus ga_elite1 |        0.000135 |               -0.001107 |                 0.001376 |     10 |       10 |      0 |
| ga_elite3 minus ga_elite1 |        0.000153 |               -0.000958 |                 0.001265 |      8 |       12 |      0 |

No-elite final output remains protected by best-observed retention. That is not evidence the evolving population retained or improved the archived chromosome. Conversely, better output with an injected prior does not establish that evolutionary reproduction independently discovered it. Generational survival and passive retention have different causal roles in the algorithm.

## Initialization versus Search

Impact-first J=33.57830255999924 h; prior optimized J=33.03813174326729; frozen selected J=32.997840773882714. The inherited prior gain is 0.540170816732 h; the selected post-prior gain is 0.040290969385 h; total 0.580461786117 h. Thus 93.06% of that aggregate gain already existed in the supplied prior. This decomposition is relative to the exact prior, not a claim that all neighboring generation-zero populations equal it; original per-seed initial bests are retained.

The seven references are centrality, Impact (population), betweenness, degree, closeness, hospital and the retained random-reference sequence. The prior is one independently documented older optimized chromosome. Even-numbered neighbors use that prior (13), odd-numbered neighbors use Impact (12), with one inclusive inversion each. Random fill uses 67 fresh permutations. Initializer duplicates are allowed and counted. The older prior's search cost is not part of the final 100k/500k budget and must not be described as free end-to-end optimization.

The prior-discovery record is extended_ga_20261008/p100_g2000_s46/RUN.json: 81,187 distinct candidates and 138.831 s for that run. This is only one component of prior development, not its total screening/selection cost. It is already represented in the historical inventory and must not be added a second time. Historical shared memoization, continuations and missing CPU counters retain their original qualifications rather than being relabeled as new local work.

Removing the exact prior copy alone leaves prior-derived neighbors. Removing prior and all its neighbors changes random fill and RNG consumption, not merely a Boolean injection. The preserved ablations show a substantial 20k disadvantage of removal (+0.007447 h) that weakens at 100k (+0.001609; simultaneous interval [-0.000365, 0.003583]). Cold searches may catch up. The exact 7/1/25/67 composition is a reproducible mixture, not a calibrated mathematical optimum.

## Budget, Duplication and Stochastic Selection

Formal protocol: twenty seeds 42-61 at 100k, with fixed 42-46 continued to 500k. There are 20 independent seeds, not 25; nominal distinct work is 4 million, not 4.5 million. Best-observed chromosomes at exact query boundaries are distinguished from the completed-generation archive. Fixed extensions do not use validation to select seeds or stopping.

Historical 500k GA k3 gained on only 3/10 seeds between 100k and 250k (mean 0.000149859 h), and 0/10 between 250k and 500k. ILS gained on 8/10 and 7/10 (mean 0.002788896 and 0.000473178 h). Flat GA traces establish tested-budget saturation, not global optimality. Higher attempted-query and bookkeeping overhead remains an important weakness of the tested GA.

The minimum across multiple searches is a selected development result. Seed distributions and conditional uncertainty quantify stochastic search variation; they do not remove winner selection or physical-sample sensitivity. The fixed sequence's completed independent validation supports its reported performance, not exact parameter optimality.

## Scope and Remaining Limits

The original GA remains a defensible reproducible finite-budget reference; universal superiority, global optimum, exact hyperparameter optimum, and independently discovered total gain are unsupported. PMX/cycle, adaptive mutation, restart and crowding have only background-specific pilot evidence, not exhaustive powered comparisons under every final setting. Pure population effects holding initializer count and RNG schedule fixed remain unresolved. Archive-copy and retained-reference counts measure exact-sequence survival, not full descendant genealogy; no unrecorded lineage claim is inferred. Nothing in this diagnostic package retroactively promotes a new configuration.

Numerical sources: GA_PARAMETER_EVIDENCE_MATRIX.csv, HISTORICAL_PAIRED_STATISTICS.csv, original parameter/initialization seed tables, new GA_PARAMETER_CONTROLLED_RESULTS.csv and PAIRED_PARAMETER_CONTRASTS.csv. Reproduction: REPRODUCIBILITY.md and source-hash manifests.
