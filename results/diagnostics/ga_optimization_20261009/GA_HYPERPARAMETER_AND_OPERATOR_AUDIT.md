# GA hyperparameter, operator and search audit — 2026-10-09

Base revision: `164f4564c0dabdeffdaf3870af000bbca725f71a`. New results are diagnostic. The original formal strategy set, scientific source tables, physical samples, repair durations, mapping, gate, schedules, evaluation trajectories and manuscript artwork are not replaced.

## Objective and exact original behavior

For station i, let m_i = sum_r P_r W_ri, F_bi(t)=I[f_bi(t)>=0.5], C_bi(t) denote connection to an active Core source, and e_bi=f_bi F_bi C_bi. The original objective is

$$J(\pi)=\frac1{64}\sum_{b=1}^{64}\frac{\sum_i m_i\int_0^{H_{plan}}[1-e^\pi_{bi}(t)]\,dt}{\sum_i m_i},\qquad fitness(\pi)=-J(\pi).$$

H_plan = 2855.254013110100 h is preserved. The existing PLANNING_HORIZON_AUDIT.json establishes an order-independent completion bound of 134.332550 h, below 480 h, and a Core source in every intact component. That proof establishes equivalence to 0-480 h integration on these planning realizations; the evaluator and objective were not replaced with a shorter-horizon surrogate. Impact-first is a deterministic reference, not the objective. Chromosomes span full 92-station permutations, a 92! decision space. DS0 stations are omitted only by the unchanged realization-specific scheduler.

Seven deterministic sequences enter the initial population and initialize the best-so-far archive. Only a strict higher fitness replaces that archive. Original ordered crossover=.80, inversion mutation=.20 and tournament size=3 are retained in the baseline; no generational elitism is present. Thus the original five coincident archives mean that tested candidates did not beat the injected incumbent, not that five searches independently rediscovered it.

Observation-only reproduction passed 20 actual history comparisons: five original 100-generation histories, five 250-generation histories, five extended P100/1,000-generation histories and five P500/1,000-generation histories. Maximum numerical discrepancy: 7.11e-15. Original archive sequence identities also match exactly. No unexpected expensive score was required in replay. Independent candidate/realization checks reproduce the independent pandas/NetworkX production path; see NEW_CANDIDATE_PRODUCTION_PARITY.csv. No implementation defect explaining P500 failure was detected in these tests.

## Q1 — Why P500 behaved worse

The initial deterministic fraction is 7% at P100 and 1.4% at P500. With tournament3, the probability a draw includes any deterministic position is 1-(1-7/P)^3. Expected selected deterministic positions are about 19.56 and 20.71 respectively, so the larger population does **not** simply have fewer absolute incumbent parent draws. Its good-lineage fraction is much lower, reproduction disrupts complete orders, and archive preservation does not preserve reproductive chromosomes.

Original replay profiles show incumbents leaving the evolving population early, while P500 retains high positional/adjacency diversity without useful improvement. Measured standardized selection intensity is not uniformly lower at P500, so tournament3 cannot be condemned from a generic population-size argument. The controlled interventions are stronger evidence: tournament5, explicit survival and their combinations substantially rescue P500. At equal expensive budgets, P100 also executes more generations; fixed-generation comparisons alone confound search dynamics and cost. These observations indicate reproducible parameter/population interactions, not intrinsic optimality of P100. ORIGINAL_SEARCH_DYNAMICS_SUMMARY.csv contains all five seeds and the successful-offspring, selected-parent and duplicate-call measurements.

## Controlled design and computational fairness

28 targeted configurations × five seeds at 50,000 distinct scores; eight focused combinations × five seeds at the same budget; three shortlisted configurations × twenty seeds at 100,000 scores. Nine operator variants × five seeds are followed by two twenty-seed confirmations. Each twenty-seed set includes five common screening seeds and fifteen additional seeds; NEW_RESTART_CONFIRMATION.csv reports these groups separately rather than calling all twenty an independent postselection validation. The original baseline and planning-only selected best confirmed configuration are extended to 500,000 queries for five common seeds, recording 50k/100k/250k/500k checkpoints. This is a staged design, not an exhaustive factorial. Initial pilot: 2,000 exact scores in 1.711 s, approximately 0.856 ms each; actual wall time additionally includes Python observations, cache and checkpoint costs.

Every fresh GA run has a separate cache. Attempted calls include duplicate rescoring; distinct queries count actual expensive calls, including reference and initialization scores. Seven-incumbent checks plus the saved-quality check during loader setup are outside the search budget and recorded separately. A budget boundary can stop inside a generation; best-observed includes all evaluated valid candidates and is explicitly separate from the archive after the last complete generation. Safety-capped runs are not represented as complete equal-budget runs. Parent frequencies are recorded by population-position fitness rank; diversity uses sixteen deterministic chromosome-pair probes plus positional entropy. Observations use no extra GA random draws.

Wall times describe searches run concurrently on this host, not standalone hardware benchmarks. Peak working-set memory is collected in isolated GA job processes. Hybrid reuses the recorded GA prefix: joint logical budget counts its prefix once plus local queries; actual new local calls are separately distinguished, preventing the same prefix being counted twice as newly executed computation. The initial local-only run did not meter peak RSS; it is unavailable rather than inferred from final cache size.

## Q2/Q3 — Operating region and practical influences

The original setting is not a uniformly good operating region. Low tournament pressure and crossover .95 can retain the incumbent without productive improvement; high mutation .40/.60 is generally worse here. Effects depend on population and other mechanisms. Do not extrapolate monotonic trends or declare one seed's minimum optimal.

| config_id        |   seeds |   mean_hr |   std_hr |    min_hr |   success_vs_impact |   success_vs_previous |
|:-----------------|--------:|----------:|---------:|----------:|--------------------:|----------------------:|
| p100_quality_mix |       5 | 33.036259 | 0.001552 | 33.034598 |            1.000000 |              0.800000 |
| p500_quality_mix |       5 | 33.036772 | 0.001136 | 33.034981 |            1.000000 |              0.800000 |
| p100_e1          |       5 | 33.052164 | 0.007696 | 33.042428 |            1.000000 |              0.000000 |
| p100_e3          |       5 | 33.068702 | 0.017138 | 33.051448 |            1.000000 |              0.000000 |
| original_p50     |       5 | 33.086821 | 0.014394 | 33.073177 |            1.000000 |              0.000000 |
| p100_c0.6_m0.1   |       5 | 33.089872 | 0.042146 | 33.045493 |            1.000000 |              0.000000 |
| p100_m0.1        |       5 | 33.094393 | 0.058679 | 33.043616 |            1.000000 |              0.000000 |
| p100_k5          |       5 | 33.096025 | 0.052394 | 33.040091 |            1.000000 |              0.000000 |
| p100_c0.6_m0.4   |       5 | 33.102255 | 0.026296 | 33.082413 |            1.000000 |              0.000000 |
| p100_m0.05       |       5 | 33.105375 | 0.025355 | 33.065472 |            1.000000 |              0.000000 |
| p100_diverse     |       5 | 33.124730 | 0.023054 | 33.093795 |            1.000000 |              0.000000 |
| original_p100    |       5 | 33.126443 | 0.048496 | 33.073883 |            1.000000 |              0.000000 |
| p500_k5          |       5 | 33.145718 | 0.047782 | 33.084771 |            1.000000 |              0.000000 |
| p500_e3          |       5 | 33.262503 | 0.041483 | 33.212128 |            1.000000 |              0.000000 |
| p500_e1          |       5 | 33.487611 | 0.041494 | 33.447473 |            1.000000 |              0.000000 |
| original_p250    |       5 | 33.523559 | 0.122409 | 33.304587 |            0.200000 |              0.000000 |
| p500_m0.4        |       5 | 33.569383 | 0.019945 | 33.533704 |            0.200000 |              0.000000 |
| p100_m0.4        |       5 | 33.572881 | 0.012122 | 33.551197 |            0.200000 |              0.000000 |
| p100_m0.6        |       5 | 33.577103 | 0.002683 | 33.572302 |            0.200000 |              0.000000 |
| p500_m0.1        |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| p500_m0.05       |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| p100_c0.95_m0.4  |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| original_p500    |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| p500_m0.6        |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| p100_c0.95_m0.1  |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| p100_k2          |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| p500_k2          |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |
| p500_diverse     |       5 | 33.578303 | 0.000000 | 33.578303 |            0.000000 |              0.000000 |

| factor                      |   observed_conditional_rank |   largest_absolute_mean_conditional_effect_hr | comparison                                                           |
|:----------------------------|----------------------------:|----------------------------------------------:|:---------------------------------------------------------------------|
| initialization              |                           1 |                                      0.541531 | P500: quality_mix minus legacy                                       |
| crossover                   |                           2 |                                      0.483910 | crossover0.95 minus .8 at mutation0.1                                |
| population                  |                           3 |                                      0.451859 | P500 minus P100                                                      |
| selection                   |                           4 |                                      0.451859 | P100: tournament2 minus3                                             |
| mutation                    |                           5 |                                      0.450659 | P100: mutation 0.6 minus .2                                          |
| elitism                     |                           6 |                                      0.315799 | P500: elite3 minus archive-only                                      |
| objective-evaluation budget |                           7 |                                      0.041263 | budget_extension/original_p100: 500,000 minus50,000 distinct queries |

The ranking measures the largest absolute observed conditional contrast at the tested levels, including harmful changes; it is not a universal importance ordering. Initialization includes prior-quality advantage, while the budget row deliberately changes compute and is not part of equal-budget comparisons.

CONTROLLED_FACTOR_EFFECTS.csv gives five-common-seed paired effects and difference-in-differences for population×mutation, population×selection, population×elitism and crossover×mutation. Seed-bootstrap intervals there describe exploratory variability, are not physical-realization CIs and are not adjusted for many comparisons. Crossed factors are identified only at tested levels; unsampled interactions remain unresolved. The largest practical mechanisms are retaining productive chromosomes, suitable selection/crossover, and high-quality initialization. Initialization includes prior scientific search effort and must not be mistaken for a new operator discovery. The following ranking is of observed conditional contrasts, not universal variance attribution across an untested factorial. Operator changes have their own replicated confirmation and budget comparison.

| factor                 | contrast                                                         |   mean_effect_hr |   std_across_seed_effect_hr |
|:-----------------------|:-----------------------------------------------------------------|-----------------:|----------------------------:|
| initialization         | P500: quality_mix minus legacy                                   |        -0.541531 |                    0.001136 |
| crossover              | crossover0.95 minus .8 at mutation0.1                            |         0.483910 |                    0.058679 |
| crossover x mutation   | crossover0.95 minus .8 differential effect .4 versus .1 mutation |        -0.478489 |                    0.055466 |
| crossover              | crossover0.6 minus .8 at mutation0.4                             |        -0.470626 |                    0.024791 |
| crossover x mutation   | crossover0.6 minus .8 differential effect .4 versus .1 mutation  |        -0.466106 |                    0.091464 |
| population x mutation  | P500 minus P100 differential effect of mutation0.4               |        -0.455358 |                    0.060691 |
| population x selection | P500 minus P100 differential effect of tournament2               |        -0.451859 |                    0.048496 |
| population             | P500 minus P100                                                  |         0.451859 |                    0.048496 |
| selection              | P100: tournament2 minus3                                         |         0.451859 |                    0.048496 |
| mutation               | P100: mutation 0.6 minus .2                                      |         0.450659 |                    0.046919 |
| population x mutation  | P500 minus P100 differential effect of mutation0.6               |        -0.450659 |                    0.046919 |
| mutation               | P100: mutation 0.4 minus .2                                      |         0.446438 |                    0.052844 |

| config_id                   |   generation0_best_hr |   final_hr |   post_initialization_improvement_hr |
|:----------------------------|----------------------:|-----------:|-------------------------------------:|
| focused_p100_quality_m01_e1 |             33.038130 |  33.034888 |                             0.003242 |
| original_p100               |             33.578303 |  33.095551 |                             0.482752 |
| p100_e1                     |             33.578303 |  33.066947 |                             0.511355 |

Twenty-seed confirmation at a common 100,000 queries:

| phase                 | config_id                   |   seeds |   mean_hr |   median_hr |   std_hr |    min_hr |   success_vs_previous |   mean_elapsed_seconds |   max_peak_rss_mb |
|:----------------------|:----------------------------|--------:|----------:|------------:|---------:|----------:|----------------------:|-----------------------:|------------------:|
| operator_confirmation | operator_swap               |      20 | 32.999625 |   32.999216 | 0.001300 | 32.997904 |              1.000000 |             206.965912 |        325.542969 |
| operator_confirmation | operator_mixed              |      20 | 33.001318 |   33.001315 | 0.002765 | 32.997841 |              1.000000 |             222.945791 |        325.398438 |
| shortlist             | focused_p100_quality_m01_e1 |      20 | 33.034888 |   33.034598 | 0.000847 | 33.032970 |              1.000000 |             164.653080 |        321.429688 |
| shortlist             | p100_e1                     |      20 | 33.066947 |   33.069693 | 0.020041 | 33.038268 |              0.000000 |             153.586951 |        314.351562 |
| shortlist             | original_p100               |      20 | 33.095551 |   33.096587 | 0.047548 | 33.030147 |              0.150000 |             147.656477 |        315.183594 |

Recommended next-stage configuration from these planning-only replicated results: `operator_swap` with `{"adaptive": false, "crossover": 0.8, "crossover_operator": "ordered", "diversity_replacement": false, "elites": 1, "initialization": "quality_mix", "mutation": 0.1, "mutation_operator": "swap", "population": 100, "restart": false, "tournament": 3}`. Mean planning loss 32.999625244 h, across-seed SD 0.001300140 h. This recommendation is conditional on the existing model, sample and tested budgets, not an optimal hyperparameter certificate. Most follow-up effort should use this configuration and deterministic local refinement, retaining a small baseline allocation. Operator variants that do not show replicated benefit are not recommended merely because they are sophisticated.

## Q4 — Explicit elitism

The same independent archive is used with and without elitism. Controlled one-/three-elite tests change chromosomes surviving in the evolving population, not the definition of the reported archive. Their improved expensive-budget outcomes demonstrate an actual search effect. One elite was generally more effective than three at P100 in this screen; at P500, selection and mutation interactions matter. There is no universal elite-count rule.

## Q5 — New planning improvements and local/hybrid search

Best new recorded planning loss: **32.997840773883 h**, improvement over previous best **0.040290969385 h**. The previous best was 33.03813174326729 h and Impact-first 33.57830255999924 h. Source run: `results/diagnostics/ga_optimization_20261009/budget_extension/operator_swap_s43/RUN.json`, sequence hash `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`. Local-only refinement reached 32.998626840923 h after 464,141 distinct scores and 28 strictly improving moves. Each move has before/after objective and full sequence in ACCEPTED_MOVES.json; no physical samples or scheduling definition were changed.

The staged local path accepts the best tested improving neighbor if its budget truncates a scan, then restarts from that accepted order when extended. It is therefore not claimed to be identical to uninterrupted steepest descent. The final complete swap/insertion/inversion/adjacent-short-block scan has local-optimal status `True` at a 1e-9 h threshold. That statement is limited to these neighborhoods. Hybrid uses 50,000 GA queries plus local refinement through a joint 100,000-query cache. Its twenty-seed mean was 33.018973583 h (SD 0.001260725), worse than the confirmed swap variant at the same joint 100,000-query budget. Local refinement of the mixed-operator best 32.997840773883 h order used 16,643 queries and accepted no move; the complete tested neighborhood was locally stable at 1e-9 h. All accepted changes and the paired 64-realization outcomes are recorded; equality across chromosomes is allowed.

## Operator variants and landscape

Swap, insertion, mixed mutation, single-random-cycle and PMX crossover, adaptive mutation, stagnation restart and deterministic crowding are labeled variants. They do not constitute exact replays. Adaptive mutation ramps the base probability with 10,000-query stagnation toward .60; restart replaces approximately half the population after 10,000 stagnant queries; crowding compares offspring with the nearest selected parental pair by positional distance. All leave the evaluator unchanged.

CANDIDATE_LANDSCAPE.csv reports generated candidates excluding injected deterministic references, best score/identity/generation, exact ties and near ties at 1e-6/1e-4/1e-3/1e-2 h. A joint DS>0 order signature is injective because at least one planning sample has all 92 damaged stations; therefore filtering alone cannot collapse complete permutations across all samples. SCHEDULE_PHENOTYPE_DIAGNOSTICS.csv separately checks a bounded sample of equal/near-equal objectives for identical completion arrays. The fifty sampled near-best chromosomes in each of the shortlist and operator-confirmation checks had one completion-array identity. The three planning-selected full permutations likewise share the exact sixty-four completion arrays (SELECTED_PLANNING_SCHEDULE_IDENTITIES.csv). This establishes a schedule-induced plateau for these sampled orders, despite distinct joint damaged-task order signatures. Other equal objectives need not imply identical schedules, and none establish uniqueness of an optimum. Flat archives are not convergence certificates.

## Protected scope and outputs

All new numerical results and records are under results/diagnostics/ga_optimization_20261009. New review artwork is under results/figure_review/Additional_Evidence/GA_Optimization_20261009. Neither current Main/Supplement files nor results/figures are overwritten. The separate station/network/community mechanism should remain a companion to optimization evidence: S04 answers static criticality/dynamic LCC structure, whereas the companion traces f → fFC → population-dependent loss; these are related but distinct. S07 measures Core-source connectivity/redundancy, not delivered MW. S11 retains four-hazard context with historical/2pc50 parameterization limits; it is not a pure hazard-intensity experiment.

The prior 20261008 evaluation is complete (EVALUATION.json and SUMMARY.csv for both orders). SEARCH_DECISION.json's evaluation_started=false is a dated planning-selection snapshot, not current pending-work status, and is preserved as history. Current records point to completed exploratory evaluation. Formal replacement remains unapproved.
