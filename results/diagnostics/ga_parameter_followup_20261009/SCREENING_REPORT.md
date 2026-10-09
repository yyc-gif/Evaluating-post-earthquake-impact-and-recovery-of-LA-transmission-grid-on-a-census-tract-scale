# GA initialization and hyperparameter screening — 2026-10-09

Scope: 90 successful runs, seeds 42–46, 20,000 distinct objective evaluations per run on the same frozen 64-sample 2pc50/C57_D1 planning objective. Source branch based on `b1030f839d522fed4af21e424472e3f8b076797b`. All tests use final ordered-crossover / swap-mutation / one-elite / tournament-3 baseline, varying only the designated factor.

[GitHub Actions run](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38004501590) | Full per-seed records: [SCREENING_DATA.json](SCREENING_DATA.json).

**No new physical samples were generated. No formal strategy, planning evaluator or original scientific file was modified.** These are exploratory 20k-budget comparisons, not optimal-hyperparameter certificates.

## Initialization

| Initialization case | Population | Neighbors | Mean generation-0 best (h) | Mean final (h) | SD final (h) | Paired difference vs current (h) | SD of paired difference (h) |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 100 | 25 | 33.038124 | 33.003593 | 0.003611 | 0.000000 | 0.000000 |
| no_warm_no_neighbors | 100 | 0 | 33.578303 | 33.010791 | 0.003190 | 0.007198 | 0.005073 |
| warm_only | 100 | 0 | 33.038132 | 33.005630 | 0.005081 | 0.002036 | 0.003359 |
| neighbors_without_warm | 100 | 25 | 33.038124 | 33.004597 | 0.003628 | 0.001004 | 0.000697 |
| neighbor10_split | 100 | 10 | 33.038132 | 33.004167 | 0.004631 | 0.000573 | 0.001918 |
| neighbor50_split | 100 | 50 | 33.038124 | 33.003613 | 0.002177 | 0.000019 | 0.003503 |
| neighbor75_split | 100 | 75 | 33.038124 | 33.004383 | 0.003927 | 0.000790 | 0.001849 |
| neighbor25_prior | 100 | 25 | 33.038124 | 33.005160 | 0.003096 | 0.001567 | 0.001830 |
| neighbor25_impact | 100 | 25 | 33.038132 | 33.005503 | 0.003519 | 0.001909 | 0.000616 |

### Initialization attribution

The current baseline is `7` fixed heuristic sequences, `1` inherited prior best, `13` inversions around that best, `12` inversions around Impact-first, and `67` random permutations. `no_warm_no_neighbors` omits all inherited GA information but retains the seven fixed heuristic sequences. `neighbors_without_warm` retains near-best neighbors; therefore it is NOT a test of removing prior-quality information altogether.

- Removing both inherited quality and neighbors worsens mean final objective by 0.007198 h at 20k queries. Its generation-0 mean best is 33.578303 h rather than 33.038124 h.
- Removing the 25 neighbors but retaining the inherited sequence worsens final mean by 0.002036 h. This is not a reliable proof that 25 neighbors are essential given five-seed variability.
- Fifty mixed neighbors differ from 25 by 0.000019 h, small relative to paired SD; extra neighbor seeding has no supported advantage here.
- Neighbor source and count differences are conditional effects at this budget. An optimal neighbor mix is not established.

## Conditional hyperparameter screen

| Parameter case | Population | Mean final (h) | SD final (h) | Paired difference vs current (h) | SD paired diff (h) | Mean attempts | Mean run wall (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 100 | 33.003593 | 0.003611 | 0.000000 | 0.000000 | 190125 | 39.0 |
| crossover060 | 100 | 33.007099 | 0.005566 | 0.003506 | 0.007992 | 227341 | 39.8 |
| crossover095 | 100 | 33.006780 | 0.005875 | 0.003187 | 0.003629 | 153285 | 37.4 |
| mutation005 | 100 | 33.006453 | 0.002114 | 0.002860 | 0.003716 | 318594 | 48.6 |
| mutation020 | 100 | 33.003411 | 0.003625 | -0.000182 | 0.005696 | 113215 | 33.3 |
| tournament2 | 100 | 33.037806 | 0.000680 | 0.034212 | 0.003485 | 51047 | 28.7 |
| tournament5 | 100 | 33.004688 | 0.003983 | 0.001094 | 0.005410 | 211582 | 40.7 |
| population50 | 50 | 33.003895 | 0.001678 | 0.000301 | 0.004216 | 225335 | 43.6 |
| population250 | 250 | 33.006452 | 0.003641 | 0.002858 | 0.003533 | 166159 | 36.5 |

## Interpretation and reporting constraints

- The only large and consistent unfavorable change under the final configuration is tournament size `2` versus `3` in this screen (all five paired seeds worse).
- Crossover probabilities `.60` and `.95` are both worse on five-seed mean than `.80`, but small samples and wide paired SD do not establish a precise optimum.
- Mutation probability `.20` has essentially equal mean final objective to `.10` at 20k queries. `.20` also uses substantially fewer attempted evaluations to accumulate 20k distinct permutations; the 50k study favored `.10` slightly. Do not assert `.10` is universally best.
- Population `50` and `250`, tournament `5`, and changes in neighbor count exhibit small conditional effects relative to seed-level variation.
- Generation-zero quality, improvement after initialization, attempted versus distinct scores, and actual wall times are preserved in the raw JSON. Compute overhead outside the 20k objective budget is separate.
- The 64 planning realizations have been reused for algorithm development; no final out-of-sample performance claim follows from these tests. The planned untouched validation cohort must not be used for additional parameter selection.
- The inference is that the current settings are defensible defaults under the tested model and budgets, **not** a guarantee that reviewers cannot question them. Stronger claims require replication at the manuscript's 100k/500k budgets and/or a genuinely independent optimizer comparison.
