# Scheduling-aware LNS negative-outcome audit

All 160 case-seed outcomes retained from completed original GitHub Actions artifacts; none rerun. Exact candidate SHA-256, 92-element permutation, seed, budget and program completion verified.

**Not a new-physics/generalization test. Both algorithms were developed using the same 64 planning states. Lower loss is better.**

## V1: run 38033702030

| Method | Mean loss (h) | SD (h) | Min loss (h) | Mean wall (s) | Mean attempts | Improved prior warm |
|---|---:|---:|---:|---:|---:|---:|
| ga_baseline | 32.999892304 | 0.001471825 | 32.997904329 | 173.0 | 792411 | 20/20 |
| iterated_local | 33.000315359 | 0.002279715 | 32.996257553 | 118.5 | 101022 | 20/20 |
| lns_event_route | 33.038041659 | 0.000288106 | 33.036989694 | 179.4 | 123330 | 2/20 |
| lns_random_bundle | 33.037878468 | 0.000780495 | 33.034780990 | 157.0 | 100102 | 3/20 |

| Pair (first − second) | Mean delta (h) | Bonferroni 95% interval (h) | First wins | Second wins |
|---|---:|---:|---:|---:|
| lns_event_route − lns_random_bundle | +0.000163191 | [-0.000341830, +0.000668212] | 2 | 3 |
| lns_event_route − ga_baseline | +0.038149355 | [+0.037269544, +0.039029166] | 0 | 20 |
| lns_event_route − iterated_local | +0.037726300 | [+0.036402789, +0.039049812] | 0 | 20 |
| lns_random_bundle − iterated_local | +0.037563109 | [+0.036107075, +0.039019143] | 0 | 20 |
| iterated_local − ga_baseline | +0.000423055 | [-0.000654801, +0.001500911] | 8 | 12 |

### Mechanistic counters

**lns_event_route**: strict_moves_mean: 1711.95; neutral_moves_mean: 450.1; event_bank_refreshes_mean: 242.9; source_reconnection_events_sampled_mean: 65248.75; event_bundle_proposals_mean: 123296.6; random_proposal_fallbacks_mean: 550.6; runs_with_zero_global_best_improvements: 18; bundle_size_counts: {'4': 385915, '3': 700007, '2': 907877, '5': 229576, '8': 46322, '6': 154944, '7': 41291}

**lns_random_bundle**: strict_moves_mean: 933.6; neutral_moves_mean: 70.45; event_bank_refreshes_mean: 136.9; source_reconnection_events_sampled_mean: 36763.05; event_bundle_proposals_mean: 100083.2; random_proposal_fallbacks_mean: 7.3; runs_with_zero_global_best_improvements: 17; bundle_size_counts: {'4': 316583, '2': 732679, '3': 563561, '5': 183921, '6': 129327, '8': 39080, '7': 36513}

## V2: run 38034064901

| Method | Mean loss (h) | SD (h) | Min loss (h) | Mean wall (s) | Mean attempts | Improved prior warm |
|---|---:|---:|---:|---:|---:|---:|
| ga_baseline | 32.999799415 | 0.001536988 | 32.997936879 | 179.0 | 812545 | 20/20 |
| iterated_local | 33.001203353 | 0.002079812 | 32.997418074 | 121.6 | 101007 | 20/20 |
| lns_repair_route | 33.037022548 | 0.001965334 | 33.030630856 | 132.5 | 108133 | 12/20 |
| lns_repair_random | 33.032375723 | 0.004803416 | 33.023460118 | 131.6 | 100060 | 20/20 |

| Pair (first − second) | Mean delta (h) | Bonferroni 95% interval (h) | First wins | Second wins |
|---|---:|---:|---:|---:|
| lns_repair_route − lns_repair_random | +0.004646825 | [+0.002093024, +0.007200627] | 2 | 18 |
| lns_repair_route − ga_baseline | +0.037223134 | [+0.035726933, +0.038719335] | 0 | 20 |
| lns_repair_route − iterated_local | +0.035819196 | [+0.034363335, +0.037275056] | 0 | 20 |
| lns_repair_random − iterated_local | +0.031172370 | [+0.028118527, +0.034226213] | 0 | 20 |
| iterated_local − ga_baseline | +0.001403938 | [-0.000078207, +0.002886084] | 7 | 13 |

### Mechanistic counters

**lns_repair_route**: accepted_strict_repairs_mean: 233.4; accepted_neutral_repairs_mean: 143.7; route_macros_mean: 3585.25; conventional_local_macros_mean: 1557.9; event_snapshot_refreshes_mean: 50.05; event_candidates_built_mean: 13393.55; actual_repair_candidates_evaluated_mean: 108120.7; runs_with_zero_global_best_improvements: 8; bundle_size_counts: {'2': 25951, '5': 6510, '4': 11572, '3': 20443, '6': 4583, '8': 1355, '7': 1291}

**lns_repair_random**: accepted_strict_repairs_mean: 220.7; accepted_neutral_repairs_mean: 39.2; route_macros_mean: 4134.45; conventional_local_macros_mean: 1782.65; event_snapshot_refreshes_mean: 47.35; event_candidates_built_mean: 12742.2; actual_repair_candidates_evaluated_mean: 100048.4; runs_with_zero_global_best_improvements: 0; bundle_size_counts: {'2': 30378, '3': 22939, '4': 13015, '6': 5461, '7': 1464, '8': 1658, '5': 7774}

## Interpretation and next action

- Source-event route proposal targeting is **not competitive as implemented**; LNS v1 and v2 should be published as negative diagnostics rather than promoted to a formal policy.
- v2 random-bundle control's advantage over event-route LNS is evidence that the *current source-path bundling/repair proposal* is ineffective, not proof that network-aware LNS is intrinsically unsuitable.
- Because objective is the average over the reused 64 training states, selecting proposal bundles based on source reconnection in four sampled individual states can lead to negative cross-realization transfer. This is a **hypothesis**, not established by final scores alone.
- Accepted current-solution improvements need not improve the global best. Inspect strict-improvement trajectories separately.
- Before new optimizer runs, perform a bounded *proposal-level* comparison from a fixed common sequence: event-sample benefit versus mean64 benefit and route-vs-random bundles with identical repair candidates/budgets.
- Do not spend additional budget on the unchanged v1/v2, infer equivalent performance from unresolved contrasts, or inspect the untouched 2000-realization independent cohort for method selection.
- No original GA candidate, objective function, physical samples or manuscript outputs changed.

