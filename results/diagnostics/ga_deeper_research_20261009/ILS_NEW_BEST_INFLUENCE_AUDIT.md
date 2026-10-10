# Independent production-path audit and influence analysis of seed304 ILS candidate

**PASS:** GitHub Actions run [38025309567](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025309567) completed successfully. Its artifact `ga-new-best-production-parity` contains full per-realization results for all 64 frozen 2pc50 planning samples, separately evaluated with the original pandas/NetworkX production evaluator and independently with the Numba exact planning kernel. Maximum per-realization cross-implementation absolute discrepancy **3.453237695794087e-12 h**. Source graph, sources and directed-travel hashes match frozen identities.

The earlier run [38025031722](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025031722) failed *before running the parity comparison* because a stale historical `INPUT_IDENTITY.json` receipt rejected the new checkout. This was repaired by calling the existing 4-return-value current pinned loader, **without modifying model code**, and the successful run above executed the complete 64-sample audit.

## Verified result

| Statistic | ILS-new-best vs frozen GA |
|---|---:|
| New ILS sample-average planning loss | 32.9971211516702 h |
| Frozen GA sample-average planning loss | 32.99784077388156 h |
| Mean paired difference, ILS − GA | **−0.000719622211366 h** |
| Percent of baseline aggregate | −0.0021808161% |
| Samples improved under ILS | 13 of 64 |
| Samples worsened under ILS | **51 of 64** |
| Median paired difference (ILS − GA) | **+0.047005527761 h** |
| First/third quartiles of paired difference | +0.01261868 / +0.07425042 h |
| Across-sample SD of paired difference | 0.3070951330 h |
| Pointwise exploratory t 95% CI of paired mean | [−0.0774297041, +0.0759904596] h |
| Descriptive 30,000-resample bootstrap 95% percentile interval of paired mean | [−0.08664073, +0.06016739] h |
| Most influential realization | 15, difference **−2.082523454063 h** |
| Mean difference without realization 15 | **+0.032324883056 h** |
| Mean difference without five largest ILS improvements | **+0.061907163191 h** |

Full 92-station sequence and SHA-256 `bb3492142cee275f948247a5d289fa54fbc1bba67133de6e1bc598cb571052e3` are pinned in `ILS_BEST_SEED304_PLANNING_CANDIDATE.json`. The former selected frozen GA sequence has hash `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`.

The aggregate best score is **highly sensitive to a small number of previously optimized planning realizations**. On the 64 previously inspected/trained samples, this new ILS solution improves the unweighted mean while making loss worse in a large majority of individual cases. The single realization 15 is so influential that omitting it reverses the ranking. This is not proof the new sequence is worse out of sample, just compelling evidence against promoting a smaller training-set mean as a robust scientific advantage.

### Inference limitations

- The 64 samples are **not** an untouched test set: extensive algorithm development selected candidates using all 64. The listed t/bootstrap intervals describe the shape of the observed paired differences; **they are not valid post-selection confidence intervals for independent future physical realizations**, and a binomial sign test on this adaptively selected candidate would not have a defensible confirmatory interpretation.
- The original fitness minimizes the **mean** modeled population-weighted service loss. Thus a lower mean is a valid *in-sample optimization* improvement even when most realizations worsen. Reporting the median/worsening count provides sensitivity context, not a retrospective change in the objective.
- No revised risk-averse objective, new sequence promotion, additional sampling, or use of the proposed 2,000-realization validation cohort was performed.
- Further algorithm comparison must report not just lowest observed J but per-sample difference distributions, influence and cross-fitting diagnostics, preserving the same 64 training sample authority. Fresh holdout physical sampling remains a distinct author-approved step.

Production-parity observation source: [GitHub Actions verified artifact](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38025309567). Hashes and raw 64-row paired outcomes are preserved in its ZIP, not regenerated.


## Conditional analysis by DS0 task filtering (exploratory)

The original 64 planning sample schedules contain 90–92 damaged tasks, so the same priority permutation is filtered differently whenever an undamaged DS0 station is omitted. Grouping paired ILS−GA losses *without changing or reweighting the optimization objective*:

| DS0 tasks omitted | Planning realizations | Mean ILS−GA loss (h) | Median (h) |
|---:|---:|---:|---:|
| 0 | 46 | +0.033296 | +0.047006 |
| 1 | 14 | +0.036091 | +0.054451 |
| 2 | 4 | −0.520732 | −0.034825 |

The extreme realization 15 omits two DS0 tasks, and supplies −2.082523 h paired benefit. The other three two-DS0 realizations are #25 (−0.078629 h), #41 (+0.069245 h) and #52 (+0.008980 h). Of the 60 realizations with zero or one DS0 station, ILS has a worse mean loss; the full mean reverses largely due to the 2-DS0 outlier.

This is an important interaction between the realization-specific task filter, directed travel/crew decoding, and the source-connected gate. **It does not prove that DS0 omission causes the outlier**: the 64 realizations also differ in DS1–DS4 states and repair durations. Small group sizes, especially only four 2-DS0 samples, preclude generalized conditional claims. A separate exact event-time gate-component check was launched to explain whether changed Core-source reachability actually contributes to the large benefit.

