# Consolidated GA optimization continuation

Status: **COMPLETE: outstanding batches reconciled and analyzed**.

Diagnostic branch only. Fetched starting HEAD: `5697f4f92fa1ac2863fbcb61e6f72e94ed9d418d`; prior baseline `13f8ef8e5d244c70a92a06a45540460c736c70f9`. No formal candidate promotion, physical resampling, objective change, revision-branch edit, or manuscript/artwork replacement.

## 1. Authority and experiment inventory

The unchanged model has 92 stations, 318 graph edges, 14 Core sources, C57_D1, 2,315 tract dependencies and 64 frozen 2pc50 planning states. J is the original population-dependency-weighted mean integrated effective-service loss; threshold 0.5 and original planning horizon 2855.254013110100 h are preserved. All new event accounting uses that original horizon. The independent production audit uses the original scheduler, pandas/NetworkX gate and production burden evaluator.

| batch | run_id | expected_seeds | present_seeds | configurations | budget_each | completed_final_runs | complete |
| --- | --- | --- | --- | --- | --- | --- | --- |
| factorial_20k | 38023902724 | 12 | 12 | 19 | 20000 | 228 | True |
| alternative_100k | 38023988574 | 20 | 20 | 3 | 100000 | 60 | True |
| confirmation_100k | 38024145330 | 20 | 20 | 11 | 100000 | 220 | True |
| neutral_100k | 38024876916 | 20 | 20 | 5 | 100000 | 100 | True |
| root_cause_100k | 38024927358 | 20 | 20 | 4 | 100000 | 80 | True |
| high_budget_500k | 38025814612 | 10 | 10 | 3 | 500000 | 30 | True |

Four-fold cross-fitting additionally has 20 fold/seed jobs, 40 searches at 50k on 48 training states, plus 20 deterministic reference records (not searches). All 4x5 jobs and disjoint 16-state held-out folds passed identity checks.

Run metadata, source commits, jobs, seeds, artifact IDs, original archive SHA-256 and every member hash are retained in `ACTIONS_RECONCILIATION_MANIFEST.json`. Every completed record has a validated 92-ID permutation, canonical newline-delimited SHA-256 and full budget. Per-case leaf copies and checkpoint observations are verified/retained but not counted as independent searches; see `RECONCILIATION_QA.json`.

### All requested and subsequent Actions runs

- [38023902724: GA deeper research - 16-way factorial and no-prior controls](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38023902724) - completed/success; commit `d98e69e27332797314d460824a2406304c6e84c1`; 12 artifacts.
- [38023988574: GA versus non-GA recovery sequence search](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38023988574) - completed/success; commit `eb6ae62593d36ebeb1089c7de3d8f9b529e233e1`; 20 artifacts.
- [38024145330: GA method interactions - 100k independently seeded confirmatory screen](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38024145330) - completed/success; commit `11ad63e1f216d5120fd660fb4df5e1e5e525a0f6`; 20 artifacts.
- [38024876916: GA plateau equivalence - neutral drift versus GA](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38024876916) - completed/success; commit `428288cb76e32add0a52b2f5b245cc2de355381c`; 20 artifacts.
- [38024927358: GA original failure and warm-start/elitism mechanism](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38024927358) - completed/success; commit `062b86eebaaf99eefe7e46aa32121087aab192c7`; 20 artifacts.
- [38025031722: Verify new local-search planning best against production evaluator](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025031722) - completed/failure; commit `fb3339d29b3db582668759d194129fc2eda69212`; 0 artifacts.
- [38025309567: Verify new local-search planning best against production evaluator](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025309567) - completed/success; commit `7da4f9cf673d8030d42bf0c4ac2eb4c23b4cce6a`; 1 artifacts.
- [38025468939: Audit ILS best with deterministic complete-neighborhood refinement](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025468939) - completed/success; commit `a3c066fdad7d90779a98328096188aad721e40b6`; 1 artifacts.
- [38025630104: Audit ILS-vs-GA influential planning sample through exact scheduler](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025630104) - completed/success; commit `30c1e12546ab1b1c50fa3e8ef807a37ff7330f59`; 1 artifacts.
- [38025701964: Cold-start GA vs ILS internal planning 48-16 crossfit](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025701964) - completed/success; commit `09c3f46dd66c4ebcee9b8a1f5bcd6c5f28b8605d`; 20 artifacts.
- [38025814612: GA selection pressure versus ILS at 500k distinct evaluations](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025814612) - completed/success; commit `dfae61bc0dfec039b08919e6a5a7b1a8612db19b`; 10 artifacts.
- [38025896534: Decompose ILS outlier into exact self threshold source service losses](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025896534) - completed/success; commit `3e5a33b3752f686b3ef8de7602c6c9fae476dd98`; 1 artifacts.
- [38026109750: Independent production parity for ILS-refined 32.996137 planning result](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38026109750) - completed/success; commit `5697f4f92fa1ac2863fbcb61e6f72e94ed9d418d`; 1 artifacts.

The unsuccessful earlier parity run 38025031722 produced no comparison artifact and is not counted as a successful evaluation. Its stale input-identity receipt failure was corrected without changing the physical model; runs 38025309567 and 38026109750 are the subsequent successful original and refined audits. No completed batch was rerun to reconstruct available records.

## 2. Independently verified candidates and influence

Frozen GA J = 32.997840773883 h; refined ILS compiled J = 32.996137365389 h, independently verified production J = 32.996137365388 h. Maximum per-realization production/compiled discrepancy = 3.44e-12 h. Improvement = 0.001703408494 h (0.005162%). The formal GA file remains unchanged.

Canonical permutation hashes:

- FrozenGA: `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`.
- FirstILS: `bb3492142cee275f948247a5d289fa54fbc1bba67133de6e1bc598cb571052e3`.
- RefinedILS: `75a1014c7f921c09b574eed4eebcaa412f86fcbc61487bf4a1277c4eb448ddbd`.
- alternative_100k_annealed_local_seed310: `b14f54cb83464d711ec8739e55e740e6f4687fb863de219c27c178edab76c511`.
- alternative_100k_ga_baseline_seed313: `35d00e2a45ccd69e38667f00c1c3a3204d559f0394a30c6d67e38b2c4a3029af`.
- alternative_100k_iterated_local_seed304: `bb3492142cee275f948247a5d289fa54fbc1bba67133de6e1bc598cb571052e3`.
- neutral_100k_ga_baseline_seed504: `38701d8ae0ff99ea49b3eecdd17f01ad59e4220d9ef1a493c06c6db811b928bc`.
- neutral_100k_neutral_0.00_seed504: `3760311dcbb19874db97be06d62cea46f3580a344fd3c297aaf11eb98c97c285`.
- neutral_100k_neutral_0.10_seed517: `e8cd37e448e44e198ac44b7f174dbdc6b50d20699fb9a4e7fe72638d9f77ac3f`.
- neutral_100k_neutral_0.50_seed502: `f04ebd563df7bef0628f1deb664957cfe6dd29be042ff68b00abb335301088bf`.
- neutral_100k_neutral_1.00_seed509: `b3fd3e466b966ad0a4ef1976e8e01a871ffd370f5b3a6fdcaf981f8c060bc66d`.
- high_budget_500k_ga_k3_seed702: `d40e3e949be1f7e3b2db0315c420560bc2f4e05eb732602a9ca0f985ae23af7d`.
- high_budget_500k_ga_k5_seed701: `695b044516eec00f0b1ebc7cdc38b0d87c3a6873ec4756195c93a7e3e290aa6a`.
- high_budget_500k_iterated_local_seed705: `5715993ffb94a7e8af690010cb26461cd13a5baf6c2efa3199ff1914fd11b85f`.

Complete permutations are in `IMPORTANT_CANDIDATES.json`; every experimental final permutation is in the raw artifacts and `ALL_FINAL_SEQUENCES_BY_SHA256.json`. These are candidate records, not policy promotion.

### FirstILS minus FrozenGA

Mean -0.000719622211 h; median +0.047005527761 h; 13/64 better and 51/64 worse. Omitting realization 15 gives +0.032324883056 h. Omitting the five most beneficial states gives +0.061907163191 h.

Per-state difference SD 0.307095133 h; middle 50% [+0.012618677, +0.074250419] h. Both quartiles are positive even though the original mean is negative: a small beneficial tail outweighs mostly unfavorable differences.

| omitted_count | subsets | ga_better_count | ils_better_count | mean_delta_min_hr | mean_delta_max_hr |
| --- | --- | --- | --- | --- | --- |
| 1 | 64 | 9 | 55 | -0.008631508 | 0.032324883 |
| 2 | 2016 | 401 | 1615 | -0.015364197 | 0.043760663 |
| 3 | 41664 | 9633 | 32031 | -0.019333724 | 0.052843294 |

### RefinedILS minus FrozenGA

Mean -0.001703408494 h; median +0.050059686525 h; 14/64 better and 50/64 worse. Omitting realization 15 gives +0.030758169262 h. Omitting the five most beneficial states gives +0.061424486664 h.

Per-state difference SD 0.305007835 h; middle 50% [+0.006221088, +0.077464033] h. Both quartiles are positive even though the original mean is negative: a small beneficial tail outweighs mostly unfavorable differences.

| omitted_count | subsets | ga_better_count | ils_better_count | mean_delta_min_hr | mean_delta_max_hr |
| --- | --- | --- | --- | --- | --- |
| 1 | 64 | 7 | 57 | -0.009604610 | 0.030758169 |
| 2 | 2016 | 319 | 1697 | -0.016440009 | 0.042703237 |
| 3 | 41664 | 7880 | 33784 | -0.020059633 | 0.052180577 |

All 64 leave-one-out values, exhaustive leave-two/leave-three reversal counts and targeted leave-1/2/3/5/10 results are retained. Omission checks are influence diagnostics, not a replacement objective or a license to discard difficult samples. Selected-candidate sample intervals would be postselection descriptive, not independent expected-performance evidence. The larger median disadvantage and the sign reversal after removing a small number of favorable states diagnose physical-training-sample leverage, not numerical parity failure.

## 3. Exact physical/scheduling mechanism

### FirstILS: signed component changes

| scope | L_self | L_threshold | L_source | L_total |
| --- | --- | --- | --- | --- |
| realization15 | 0.189305441 | 0.007410950 | -2.279239845 | -2.082523454 |
| all64mean | 0.084797224 | 0.003435060 | -0.088951906 | -0.000719622 |

### RefinedILS: signed component changes

| scope | L_self | L_threshold | L_source | L_total |
| --- | --- | --- | --- | --- |
| realization15 | 0.133278288 | 0.004986446 | -2.185047541 | -2.046782807 |
| all64mean | 0.060199119 | 0.002378997 | -0.064281524 | -0.001703408 |

L_self integrates 1-f; L_threshold integrates f(1-F); L_source integrates fF(1-C). These nonnegative losses sum exactly to L_total=1-fFC. All 192 station/event integrations reproduce the compiled sample objective within 1e-8 h; no surrogate timeseries or trapezoidal approximation is used.

For the first ILS realization-15 schedule, total directed crew travel rises by 1.142998168 h, 22 stations finish earlier and 22 later, and mean damaged-station completion is 0.050290139 h later. The 2.082523454 h benefit comes from source connectivity, not uniformly faster repairs: source loss falls by 2.279239845 h, offset by worse self and threshold loss.

FirstILS: station 301745 (not a source) finishes at 19.043563694 h, crew 20, dispatch rank 20, unchanged duration 18.652012960 h.

- At 19.043563694 h, completion 301745 coincides with 21 newly source-connected stations and 2320857.337 population-dependency mass; active sources 307373, 308581, 310199.

RefinedILS: station 301745 (not a source) finishes at 19.043563694 h, crew 20, dispatch rank 20, unchanged duration 18.652012960 h.

- At 19.043563694 h, completion 301745 coincides with 21 newly source-connected stations and 2320857.337 population-dependency mass; active sources 307373, 308581, 310199.

FrozenGA: station 301745 (not a source) finishes at 26.643710537 h, crew 31, dispatch rank 61, unchanged duration 18.652012960 h.

- At 25.242654999 h, completion 303371 coincides with 25 newly source-connected stations and 2675320.346 population-dependency mass; active sources 308581, 310199.
- At 26.335434734 h, completion 309042 coincides with 4 newly source-connected stations and 655778.199 population-dependency mass; active sources 308581, 310199.

The first ILS event at 19.043563694 h reconnects 21 stations with 2,320,857.337 dependency mass. The frozen GA large reconnection occurs at 25.242654999 h with completion of 303371 (25 stations), then at 26.335434734 h with completion of 309042 (4 stations). Between 19.166689187 and 21.042918991 h, effective service is 0.322390551 for ILS versus 0.017620177 for GA; this interval contributes -0.571819258 h. Full component memberships, active sources, newly connected IDs, completion events, crew assignment and dependency masses are retained in the SAMPLE15 event JSONs.

### Feasible controlled priority interventions

Three full permutations move only station 301745 between original full priority indices 21/62, retaining all other relative priorities and the original physical samples, source gate, crew scheduler and mean-loss evaluator. Each was independently checked through all64 native production evaluations (maximum parity error below 1e-8 h). These are diagnostic counterfactuals, not an optimization batch or new formal policies.

| label | sample15_station_completion_hr | sample15_delta_hr | mean_counterfactual_minus_parent_hr | improved_realizations | worsened_realizations |
| --- | --- | --- | --- | --- | --- |
| FrozenGA_move_301745_62_to_21 | 19.043563694 | -0.022576075 | 0.072395103 | 10 | 54 |
| FirstILS_move_301745_21_to_62 | 28.458918196 | 1.691373767 | 0.057921825 | 14 | 50 |
| RefinedILS_move_301745_21_to_62 | 28.704767104 | 1.652978878 | 0.059327454 | 11 | 53 |

Moving 301745 forward in FrozenGA makes it finish at the same 19.043563694 h as FirstILS, yet improves sample15 by only 0.022576075 h rather than reproducing the full 2.082523454 h benefit. It worsens the original64 mean by 0.072395103 h. Conversely delaying 301745 in FirstILS loses 1.691373767 h on sample15; delaying it in RefinedILS loses 1.652978878 h. This asymmetric feasible intervention demonstrates dependence on the surrounding order, not one universally beneficial station move.

The representative active ILS source path for 301745 is `301745 -> 306623 -> 304073 -> 307373`. Core source 307373 completes at 15.320528259 h in FirstILS versus 28.435441828 h in FrozenGA and the early-301745 counterfactual. Station 301637 completes at 15.197339881 h in FirstILS versus 22.282564468 h in FrozenGA and 22.772295802 h in the early counterfactual. Those two stations are inactive on retained representative ILS paths in the early-GA intervention at 19.043563694 h; FirstILS has 28 connected stations versus 3 there. `SAMPLE15_CONTROLLED_SOURCE_PATHS.json` retains the explicit station/source paths and inactive-node timings. Shortest-hop paths are descriptive reachability witnesses, not unique electrical flows or proof that all alternate routes require the same nodes.

Dependency mass is sum_r P_r W_ri, not delivered MW, station demand, or exclusive customer counts. Event/station contributions describe the complete feasible schedules. The controlled intervention effect concerns the specified full feasible priority edit, including all scheduler cascades; it is not an isolated restoration-time causal effect or a claim that 301745 explains the entire between-strategy difference.

## 4. Parameter interactions and initialization

| batch | contrast | mean_delta_hr | simultaneous95_low_hr | simultaneous95_high_hr |
| --- | --- | --- | --- | --- |
| factorial_20k | population | 0.000261215 | -0.001081324 | 0.001603754 |
| factorial_20k | tournament | -0.001815597 | -0.002796128 | -0.000835066 |
| factorial_20k | mutation | -0.000753391 | -0.002584666 | 0.001077885 |
| factorial_20k | neighbors | 0.000015733 | -0.001140015 | 0.001171482 |
| factorial_20k | populationÃ—tournament | -0.001274250 | -0.003600865 | 0.001052365 |
| factorial_20k | populationÃ—mutation | 0.000509565 | -0.002344149 | 0.003363280 |
| factorial_20k | populationÃ—neighbors | -0.001146723 | -0.003279765 | 0.000986318 |
| factorial_20k | tournamentÃ—mutation | 0.000321209 | -0.003406430 | 0.004048848 |
| factorial_20k | tournamentÃ—neighbors | 0.000206198 | -0.002001169 | 0.002413566 |
| factorial_20k | mutationÃ—neighbors | 0.000782347 | -0.000887948 | 0.002452641 |
| confirmation_100k_mechanisms | population100_minus50_x_tournament5_minus3 | -0.000224304 | -0.002132892 | 0.001684285 |
| confirmation_100k_mechanisms | tournament5_minus3_x_mutation20_minus10 | 0.000149262 | -0.001954978 | 0.002253501 |
| confirmation_100k_mechanisms | neighborquarter_minusnone_x_tournament5_minus3 | 0.000182864 | -0.002165033 | 0.002530762 |
| confirmation_100k_mechanisms | warm_minus_no_quality_nnone_final_loss | 0.000501468 | -0.001089061 | 0.002091996 |
| confirmation_100k_mechanisms | warm_minus_no_quality_nnone_initial_loss | -0.540170817 | -0.540170817 | -0.540170817 |
| confirmation_100k_mechanisms | warm_x_search_gain | -0.540672284 | -0.542262812 | -0.539081756 |

High-minus-low main effects and explicit difference-in-differences are computed within the same optimizer seed. Screening has 12 independently allocated seeds; confirmation has 20 different seeds. Main/two-factor screening terms form a 10-contrast family. Six confirmatory mechanism contrasts form a separate family; ten case-to-baseline confirmation comparisons are retained separately. All intervals are Bonferroni simultaneous 95% paired t intervals, conditional on the reused planning collection; no post hoc equivalence tolerance is asserted.

Population P50/P100 with quarter allocation changes neighbors 12/25, deterministic-reference fractions 7/50 vs 7/100, and random-fill counts as well as population/generations. The population interaction therefore concerns the tested population-plus-initialization package, not isolated P. Crossover stays .8, mutation operator swap, elite count one in these factorial contrasts.

The exact warm start is the earlier 33.03813174326729 h sequence (`3bfeafdd1adf950749e63fdbbe3b7efc21b1efd04c3b3d64c28c3d118717bbed`), not the frozen 32.997840773882714 h best. Warm/no-quality comparisons use zero neighbors and the same seven references, removing prior-best influence from both initialization and archive in the no-quality control. A larger cold-start search gain partly reflects its worse starting score; it is not by itself evidence of a better final optimizer.

The 20k tournament5 screening benefit is not automatically carried forward as a final default. Independently seeded 100k interaction contrasts and the 500k comparison determine its supported scope. Unresolved intervals identify limited seed precision at very small effects, tested-composition dependence and budget dependence; they do not prove equal performance or justify endless repetitions of the same comparison.

The 100k population-by-tournament, tournament-by-mutation and neighbors-by-tournament contrasts are approximately -0.000224, +0.000149 and +0.000183 h, respectively; all six-family simultaneous intervals include zero. This does not reproduce a general tournament5 benefit from the short-budget screen. Warm initialization improves the initial best by 0.540171 h, but warm-minus-no-quality final loss is +0.000501 h with an interval crossing zero. The cold-start controls catch up through search; preserving a strong initial archive is useful protection but not demonstrated to improve final search quality under this tested 100k package.

## 5. Does GA add value?

| batch | configuration | seeds | mean_loss_hr | sd_loss_hr | best_loss_hr | mean_attempted_calls | mean_wall_seconds | mean_duplicate_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alternative_100k | annealed_local | 20 | 33.037394567 | 0.001546911 | 33.031963325 | 100011.950000000 | 123.174378311 | 0.000119484 |
| alternative_100k | ga_baseline | 20 | 32.999987899 | 0.001542921 | 32.997840774 | 833761.200000000 | 184.004657042 | 0.879764071 |
| alternative_100k | iterated_local | 20 | 33.001286164 | 0.002004399 | 32.997121152 | 100989.500000000 | 123.565171538 | 0.009797689 |
| high_budget_500k | ga_k3 | 10 | 32.999132080 | 0.000942540 | 32.997936879 | 4570582.800000000 | 950.073863341 | 0.890027690 |
| high_budget_500k | ga_k5 | 10 | 32.999825296 | 0.001566681 | 32.998285903 | 4628757.300000000 | 955.672037340 | 0.891808230 |
| high_budget_500k | iterated_local | 10 | 32.998030855 | 0.001420788 | 32.996457713 | 504979.800000000 | 621.122396339 | 0.009861333 |
| neutral_100k | ga_baseline | 20 | 32.999951671 | 0.001652829 | 32.998405326 | 794320.050000000 | 188.788500767 | 0.873727318 |
| neutral_100k | neutral_0.00 | 20 | 33.000409294 | 0.001865040 | 32.997823939 | 101012.000000000 | 130.280252495 | 0.010018033 |
| neutral_100k | neutral_0.10 | 20 | 33.000343193 | 0.001846948 | 32.996597958 | 100448.150000000 | 130.154241577 | 0.004461451 |
| neutral_100k | neutral_0.50 | 20 | 33.000894329 | 0.002393935 | 32.997022437 | 100145.800000000 | 129.882055755 | 0.001455865 |
| neutral_100k | neutral_1.00 | 20 | 33.000305753 | 0.001952642 | 32.996854938 | 100079.750000000 | 129.789103581 | 0.000796859 |

| batch | contrast | mean_delta_hr | simultaneous95_low_hr | simultaneous95_high_hr |
| --- | --- | --- | --- | --- |
| alternative_100k | iterated_local minus ga_baseline | 0.001298265 | -0.000133470 | 0.002729999 |
| alternative_100k | annealed_local minus ga_baseline | 0.037406668 | 0.036446193 | 0.038367142 |
| neutral_100k | neutral_0.00 minus ga_baseline | 0.000457624 | -0.001076224 | 0.001991471 |
| neutral_100k | neutral_0.10 minus ga_baseline | 0.000391522 | -0.001161661 | 0.001944706 |
| neutral_100k | neutral_0.50 minus ga_baseline | 0.000942658 | -0.001118572 | 0.003003888 |
| neutral_100k | neutral_1.00 minus ga_baseline | 0.000354082 | -0.001016455 | 0.001724618 |
| high_budget_500k | ga_k5 minus ga_k3 | 0.000693216 | -0.000966832 | 0.002353265 |
| high_budget_500k | iterated_local minus ga_k3 | -0.001101224 | -0.002591758 | 0.000389309 |

Distinct expensive evaluations are matched within each experiment. Attempted calls additionally measure repeated permutation queries and can be much larger for GA. Checkpoint trajectories at fixed boundaries are repeated measurements of the same search, not independent runs; convergence and marginal gains must use within-seed deltas. Wall times describe these cloud implementations/runners, not universal hardware performance. Sum of concurrent job times is compute accounting, not elapsed project time.

ILS is a substantive non-GA comparator: swap/insertion/inversion proposals, strict local acceptance and fixed cyclic 2/4/8 perturbations after stagnation. Tested annealing underperformance does not disqualify stronger annealing implementations. The neutral drift grid tests equality acceptance probabilities 0/.1/.5/1 at fixed 1e-9 h equality tolerance, not an arbitrary new default. The older joint-budget GA/local hybrid, variable perturbation sizes and the completed deterministic swap/insertion/inversion/adjacent-block(2/3/4) certificate are stronger search mechanisms already investigated; their results do not prove every possible hybrid/VNS/LNS ineffective.

### Matched 500k quality, variability and efficiency

| configuration | seeds | mean_loss_hr | sd_loss_hr | best_loss_hr | seeds_better_than_ga_k3 | seeds_better_than_formal | mean_attempts_per_distinct | paired_mean_wall_ratio_to_ga_k3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ga_k3 | 10 | 32.999132080 | 0.000942540 | 32.997936879 | 0 | 0 | 9.141165600 | 1.000000000 |
| ga_k5 | 10 | 32.999825296 | 0.001566681 | 32.998285903 | 4 | 0 | 9.257514600 | 1.004121156 |
| iterated_local | 10 | 32.998030855 | 0.001420788 | 32.996457713 | 7 | 5 | 1.009959600 | 0.653750458 |

The matched 500k ILS-minus-GAk3 mean is -0.001101224 h, simultaneous interval [-0.002591758, +0.000389309]. ILS wins 7/10 paired seeds and beats the formal selected GA score in 5 searches. Its average within-seed wall-time ratio is 0.654, and attempted-call ratio 0.111. The benefit is small in absolute mean-loss units, but the tested ILS is a competitive optimizer with much lower repeated-call overhead; GA superiority is not supported by this evidence.

Tournament5-minus3 at 500k is +0.000693216 h, simultaneous interval [-0.000966832, +0.002353265]. The final default cannot be justified from the 20k marginal screen alone. Both tested GA methods retain repeated-genotype overhead, separate from scheduler-equivalent distinct permutations.

### Late-budget convergence

| configuration | seeds | earlier_evaluations | later_evaluations | mean_within_seed_gain_hr | median_within_seed_gain_hr | seeds_with_strict_gain |
| --- | --- | --- | --- | --- | --- | --- |
| ga_k3 | 10 | 50000 | 100000 | 0.000917552 | 0.000192883 | 8 |
| ga_k3 | 10 | 100000 | 250000 | 0.000149859 | 0.000000000 | 3 |
| ga_k3 | 10 | 250000 | 500000 | 0.000000000 | 0.000000000 | 0 |
| ga_k5 | 10 | 50000 | 100000 | 0.000426374 | 0.000198440 | 7 |
| ga_k5 | 10 | 100000 | 250000 | 0.000000000 | 0.000000000 | 0 |
| ga_k5 | 10 | 250000 | 500000 | 0.000000000 | 0.000000000 | 0 |
| iterated_local | 10 | 50000 | 100000 | 0.001922028 | 0.001283848 | 9 |
| iterated_local | 10 | 100000 | 250000 | 0.002788896 | 0.002423545 | 8 |
| iterated_local | 10 | 250000 | 500000 | 0.000473178 | 0.000332314 | 7 |

These are gains inside each same seeded 500k search, not a comparison of separately seeded 100k and 500k batches. They distinguish a method that continues finding useful priorities from a method that spends later budget generating repeated or non-improving candidates. Full boundary means and the other batches are in WITHIN_SEED_CONVERGENCE.csv. The current GA engine does not retain complete per-offspring lineage histories; the historical observation-only replays supply those mechanism measurements. Final hashes/checkpoints cannot establish that every distinct later candidate is scheduling-equivalent.

In the completed ten-seed batch, GA tournament3 improves in only 3/10 searches between 100k and 250k and in 0/10 thereafter; tournament5 improves in 0/10 after 100k. ILS improves in 8/10 between 100k and 250k (mean gain 0.002789 h), then 7/10 between 250k and 500k (mean gain 0.000473 h). Thus simply multiplying the current GA budget is inefficient here, whereas the tested local-search perturbations still expose useful priorities. Neither GA500k variant beats the formal selected score in any of ten searches; ILS does in five. Its best 32.996457713 h remains worse than the independently verified refined candidate 32.996137365 h. There is no new best requiring another candidate promotion decision.

### Neutral traversal evidence

| configuration | neutral_proposals | accepted_neutral_moves | accepted_strict_moves | restarts | loss_hr |
| --- | --- | --- | --- | --- | --- |
| neutral_0.00 | 7545.600000000 | 0.000000000 | 1465.250000000 | 10.450000000 | 33.000409294 |
| neutral_0.10 | 7541.800000000 | 762.500000000 | 1489.200000000 | 10.350000000 | 33.000343193 |
| neutral_0.50 | 7500.700000000 | 3754.350000000 | 1557.500000000 | 10.250000000 | 33.000894329 |
| neutral_1.00 | 7507.700000000 | 7507.700000000 | 1551.050000000 | 9.600000000 | 33.000305753 |

Neutral traversal really occurred in the positive-probability variants; it was not an unexercised flag. The retained paired final-loss intervals show no reliable improvement over the GA comparator for these tested probabilities. Accepted neutral moves measure plateau exploration, not independently beneficial objective changes. The strict and neutral transition counts are per-search summaries; checkpoint observations and transitions are not additional independent optimizer runs.

### Stronger local and hybrid mechanisms already tested

The [prior operator/local/hybrid audit](../../ga_optimization_20261009/GA_HYPERPARAMETER_AND_OPERATOR_AUDIT.md#q5--new-planning-improvements-and-localhybrid-search) records a twenty-seed hybrid with 50k GA queries followed by local refinement in the same joint 100k cache: mean 33.018973583 h, SD 0.001260725 h, worse than its confirmed swap-GA comparator at the same total budget. Its GA prefix is counted once, not added again as fresh compute. Local-only refinement of the older warm start used 464,141 distinct queries and 28 accepted moves, reaching 32.998626841 h. Refinement of the then-selected GA/mixed best used 16,643 queries with zero accepted moves. These are prior evidence, not additional newly reconciled Actions searches or matched-hardware cost claims.

The new seed304 multi-neighborhood refinement breaks that earlier local plateau from a different ILS basin: seven improving moves and 132,545 distinct queries, ending at 32.996137365 h. Together with the 500k late gains and actually accepted neutral transitions, this addresses basin dependence and variable-neighborhood/perturbation behavior rather than assuming GA is indispensable. A new scheduling-aware large-neighborhood destroy/reinsert algorithm has not been benchmarked; cyclic 2/4/8 random perturbations must not be mislabeled as a comprehensive LNS comparison. No evidence supports ruling out every stronger hybrid or local-search implementation.

## 6. Original GA failure and actual search history

| contrast | mean_delta_hr | simultaneous95_low_hr | simultaneous95_high_hr |
| --- | --- | --- | --- |
| legacy_plus_warm minus legacy_original | -0.049658119 | -0.071776359 | -0.027539880 |
| legacy_plus_warm_and_elite minus legacy_plus_warm | -0.001488216 | -0.003246050 | 0.000269618 |
| final_swap_without_elite minus final_swap_with_elite | 0.000334657 | -0.001237736 | 0.001907050 |
| final_swap_with_elite minus legacy_plus_warm_and_elite | -0.034598889 | -0.036146406 | -0.033051372 |

Original GA has a best-so-far incumbent archive but no surviving elite chromosome. Archive retention guarantees output preservation, not reproductive lineage survival or rediscovery. Twenty observation-only histories match original native histories (maximum error 7.11e-15, zero new expensive replay calls); full observed incumbent disappearance, archive copies, diversity, selection and offspring statistics are summarized in ORIGINAL_HISTORY_MECHANISM_SUMMARY.csv.

- extended: mean final position entropy 0.506816, mean final unique population 276.20, mean crossover-only parent-improvement fraction 0.045041, mutation-only 0.091702; first no-incumbent generation range 1 to 5.
- original: mean final position entropy 0.378381, mean final unique population 75.50, mean crossover-only parent-improvement fraction 0.066037, mutation-only 0.106246; first no-incumbent generation range 2 to 5.

Root controls distinguish warm-start plus its neighbor composition, then explicit generational elitism at fixed inversion mutation .2; final swap .1 with/without elitism is another controlled comparison. Final swap .1 versus inversion .2 is a mutation-operator-plus-probability package, not a clean isolated operator effect. Previously controlled operator studies supply the fixed-probability evidence. High population diversity without improvement is observed in failed P500 histories; a flat archive is not a global-optimality or convergence proof.

Current final-chromosome audit: 718 search outcomes, 702 distinct chromosomes, but only 605 exact all64 completion-array phenotypes. All archived scores reproduce to a maximum error of 2.06e-13 h. This is an audit of final outcomes, not the entire unretained new search trajectories. Identical final chromosomes across distinct seed/configuration searches remain separate stochastic outcomes in means and uncertainty estimates; only duplicate artifact/checkpoint observations are excluded.

Near-best scheduling-equivalent permutations were demonstrated in the prior bounded phenotype audit despite injective joint damaged-task-order signatures. DS0 filtering alone cannot collapse all full orders because some planning states damage all 92. Equal objective values alone do not imply equal schedules. Current duplicate-call rates distinguish repeated genotype generation from that separate scheduler-induced plateau.

## 7. Internal cross-fitting and generalization

| fold | train_ils_minus_ga_hr | held_ils_minus_ga_hr | held_ga_minus_impact_hr | held_ils_minus_impact_hr |
| --- | --- | --- | --- | --- |
| 0 | -0.013639116 | 0.044376181 | -0.485770183 | -0.441394003 |
| 1 | -0.010771262 | 0.038014231 | -0.384645942 | -0.346631711 |
| 2 | -0.011316681 | 0.020905276 | -0.493436211 | -0.472530935 |
| 3 | 0.002527354 | -0.011790080 | -0.562176061 | -0.573966141 |

Individual fold/seed pairs have 16/20 training-versus-held-out GA/ILS ranking reversals. Three of four fold-average comparisons favor ILS in training but GA on held-out states; fold3 favors GA in training but ILS on held-out states. Neither method receives the previously optimized all-64 incumbent.

| contrast | n | mean_delta_hr | simultaneous95_low_hr | simultaneous95_high_hr |
| --- | --- | --- | --- | --- |
| held_ils_minus_ga_hr | 5 | 0.022876402 | -0.012810277 | 0.058563081 |
| held_ga_minus_impact_hr | 5 | -0.481507099 | -0.510012966 | -0.453001232 |
| held_ils_minus_impact_hr | 5 | -0.458630697 | -0.474805350 | -0.442456045 |

Uncertainty uses five independent optimizer-seed blocks after averaging the four dependent folds within each seed, with a three-comparison simultaneous interval family. These intervals describe search randomness conditional on this fixed four-fold partition, not four independent physical validations or twenty independent external datasets. Training sets overlap, and method development already saw the 64-state collection. No proposed 2,000 fresh physical states were accessed for tuning, candidate selection or repeated testing.

## 8. Computation and explicit research decision

| batch | completed_searches | distinct_evaluations | attempted_calls | summed_search_wall_seconds | kernel_planning_sample_evaluations |
| --- | --- | --- | --- | --- | --- |
| alternative_100k | 60 | 6000000 | 20695253 | 8614.884137823 | 384000000 |
| confirmation_100k | 220 | 22000000 | 193660332 | 39696.062896859 | 1408000000 |
| factorial_20k | 228 | 4560000 | 38301783 | 7899.273797748 | 291840000 |
| high_budget_500k | 30 | 15000000 | 97043199 | 25268.682970189 | 960000000 |
| neutral_100k | 100 | 10000000 | 23920115 | 14177.883083496 | 640000000 |
| root_cause_100k | 80 | 8000000 | 48767635 | 13792.827951926 | 512000000 |
| crossfit_50k | 40 | 2000000 | 9535166 | not recorded | 96000000 |

The deterministic refined-ILS certificate adds 132,545 distinct and 136,040 attempted local queries, seven accepted improvements, with a complete final tested-neighborhood scan. Its incremental gain over first ILS is 0.000983786283 h; the artifact's `improvement_vs_previous_hr` field measures gain over the older inherited 33.038131743 h seed, not that incremental refinement. Its 500k cap was not fully consumed; do not portray it as a 500k matched-method run. Loader parity/setup reference calls and final best-score/production checks are outside metered search and identified separately, not zero-cost science. Cold-start crossfit did not retain wall timings; this is unavailable, not reconstructed by rerunning it.

New continuation work performs 192 event-exact component integrations, 192 native production plus 192 compiled sample counterfactual evaluations, and 702 retained final-chromosome mean-score checks plus 44928 native sample-schedule decodes. None are newly executed optimizer budgets. All optimizer batch budgets above were retrieved, not reexecuted.

Scientific decision: retain the formal GA candidate pending explicit authorization. Do not claim GA universal superiority, tournament3 exact optimality, tournament5 confirmation from a 20k screen, or robust physical improvement from one selected best. The principal reliability issue is now conditional source-reconnection timing and influential planning-state leverage, not a failed evaluator or absence of feasible better chromosomes. Replicated search, archive protection, explicit initialization accounting, exact distinct budgets and independently audited candidates are defensible method requirements.

The existing experiments already test neutral plateau traversal, variable perturbations, deterministic multi-neighborhood refinement, cold-start search and a joint-budget hybrid. This continuation additionally verifies every retained final candidate and tests feasible priority interventions rather than merely repeating a plateau. Additional identical parameter repetitions are not warranted just to shrink a CI. Any next stronger hybrid/large-neighborhood comparison requires a declared new mechanism, joint budget and independent optimizer seeds; it cannot use the proposed fresh physical validation cohort for development. Candidate robustness remains a separate question from preserving the mean-loss optimization authority.

All specified outstanding batches have finished and passed final seed/configuration/budget/sequence reconciliation. No further identical GA-budget or neutral-probability sweep is justified by these results. The immediate decision is to retain the formal policy and treat ILS plus deterministic multi-neighborhood refinement as a credible challenger, not automatically promote a tiny selected mean gain. Scheduling-aware LNS remains an untested method family, not a pending launched job; only a prospectively specified mechanism comparison would warrant new development compute. The most consequential limitation is physical-sample generalization. That cannot be cured by repeatedly selecting on these same64 states; keep future validation untouched until the method and candidate-selection procedure are prospectively locked.

## 9. Reproduction and preservation

Run on this diagnostic branch with Python3.12, numba0.60.0, NumPy/pandas/NetworkX/SciPy and single BLAS/Numba threads. Retained artifact source commits and workflow files give exact cloud commands, runtime pins and matrix seeds. Do not rerun completed searches merely to regenerate evidence.

```powershell
$env:PYTHONPATH='src'
$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'ga-research-20261009-numba'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
python -m la_grid.diagnostics.ga_research_collect_20261009 --local-only
python -m la_grid.diagnostics.ga_research_mechanism_20261009
python -m la_grid.diagnostics.ga_research_priority_counterfactual_20261009
python -m la_grid.diagnostics.ga_research_gate_paths_20261009
python -m la_grid.diagnostics.ga_research_report_20261009 --prepare-only
python -m la_grid.diagnostics.ga_research_phenotypes_20261009
python -m la_grid.diagnostics.ga_research_report_20261009
```

Collector without --local-only refreshes authenticated official Actions metadata/downloads; it never launches calculations. ga_research_preserve_20261009 hydrates exact checked-in LFS bytes in the isolated checkout from verified local object hashes and records/compares the untouched revision checkout. Windows long-path runtime-cache handling changes only cache location, not evaluator code. CONTINUATION_PRESERVATION_BASELINE/VERIFIED cover the revision HEAD/branch, unrelated staged diff and 950 source/result/artwork files. MODEL_IDENTITY.json retains original file/context and all64 sample hashes. Scientific inputs/evaluator/scheduler/source gate/formal permutations remain unchanged.
