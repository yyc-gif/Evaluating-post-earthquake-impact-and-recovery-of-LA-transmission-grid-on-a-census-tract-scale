# Completed 20-seed matched-budget comparison: GA, ILS, and annealing

The independent optimizer diagnostic run **38023988574** completed successfully: 20 newly allocated common search seeds 300–319, three algorithms per seed, 100,000 distinct objective evaluations per method. All 60 final 92-station permutations and canonical SHA256 identities verified from retained Github Actions artifacts. There are **6 million** counted expensive objective evaluations (plus separately accounted load/setup overhead). Original 64 planning realizations remain unchanged; this is **not independent physical validation**.

## GA versus non-GA optimizers (100k)

| Contrast | Mean (h) | 95% simultaneous interval (h) | Wins / n |
|---|---:|---:|---:|
| annealed_local | +0.037407 | [+0.036446, +0.038367] | 0/20 |
| iterated_local | +0.001298 | [-0.000133, +0.002730] | 6/20 |

### Absolute optimization and work accounting

| Algorithm | Mean J (h) | SD (h) | Best (h) | Avg proposed calls | Avg run wall (s) |
|---|---:|---:|---:|---:|---:|
| annealed_local | 33.037395 | 0.001547 | 33.031963 | 100012 | 123.2 |
| ga_baseline | 32.999988 | 0.001543 | 32.997841 | 833761 | 184.0 |
| iterated_local | 33.001286 | 0.002004 | 32.997121 | 100990 | 123.6 |

#### Scientific interpretation

The ILS−GA paired mean difference is **+0.001298 h**, with two-comparison Bonferroni simultaneous 95% interval **[−0.000133, +0.002730] h**. This does not show ILS mean performance superiority, nor prove equivalence. GA made ~834k attempted calls to reach 100k distinct, while ILS made ~101k; ILS mean wall time is ~124 s versus GA ~184 s on the cloud runners. Different implementation overheads and algorithm operators prevent turning this into a universal hardware-efficiency claim.

A single ILS seed **304** reached **32.9971211516713 h**, lower than the frozen reported GA planning loss **32.997840773882714 h**. The complete 92-ID permutation and SHA are retained separately as `ILS_BEST_SEED304_PLANNING_CANDIDATE.json`. This is an exploratory best feasible planning score, not a claim of better expected ILS performance or an authorized formal policy change. Production-path parity must pass before scientific promotion.

The naive calibrated annealing implementation underperformed; it is **not** proof that optimally tuned simulated annealing or other advanced non-GA optimizers cannot compete. Stronger plateau-aware and deterministic neighborhood searches remain to be tested.

Every result was compared at fixed distinct-evaluation budget; attempted calls and wall time are separately reported. No validation data guided methods or chromosome selection.
