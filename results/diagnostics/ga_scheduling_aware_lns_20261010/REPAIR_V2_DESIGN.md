# Schedule-aware LNS v2 — genuine destroy/reinsert repair search

Status: Design fixed **after** observing four v1 20k engineering smoke runs; **before** any v2 result. Results cannot be claimed as blind independent optimizer-method validation after adapting the algorithm to previous data. Original 64 planning states remain the only optimization data.

## Why a second mechanism

The v1 event-route LNS is a *random block relocation*, not the usual local optimization repair stage of Large Neighborhood Search. In the four successful 20k implementation checks (seeds 800–803), it failed to beat its inherited older best of 33.038131743267 h in every case. The random damaged-bundle control also failed to improve materially. Those negative exploratory outcomes are retained, not discarded or replaced. The 20-seed 100k v1 experiment is already underway and should finish independently and be reported.

V2 changes one substantive algorithmic mechanism: for each event-route block selected from actual source-reconnect scheduling events, **destroy** the original positions of the bundle and evaluate up to twelve different insertion ranks by three possible within-bundle priority orders (at most 36 distinct feasible repaired permutations) before selecting a repaired candidate. The exact 64-state planning loss kernel remains the **only** objective and every evaluation counts toward the budget. A random bundle drawn from the *same sample's damaged task pool* is independently repaired with the exact same process, acceptance/restarts/budget.

Include 30% classical local proposals with the same probability in both LNS arms, to distinguish inadequate local exploration from route-bundle candidate selection. The v2 results therefore measure a combined LNS proposal/repair method, not a pure single parameter intervention relative to v1.

## New fixed cohorts and comparisons

Engineering screen: seeds 900–903, 20,000 distinct objective evaluations per method; 4 seeds × 4 methods.

Reproducible 100k method comparison: seeds 920–939, 100,000 distinct expensive evaluations per method; 20 seeds × 4 methods.

Four method arms: original published GA P100/OX.8/swap.1/tournament3/elite1, existing ILS from same previously optimized warm start, v2 source-event route destroy-and-repair, v2 matched random-bundle destroy-and-repair. No changes to formal policy.

The planned primary effects are route LNS minus ILS, route LNS minus GA and route LNS minus random-bundle LNS. Lower loss is better. Report same-seed mean differences and 95% paired t/bootstrap intervals, three-comparison simultaneous Bonferroni intervals, wins, attempts/distinct ratio, wall time, and 20k/50k/100k within-seed trajectories. Do not pool v1 and v2 seeds as independent trials of one unchanged algorithm.

Motivation for event bundles is original earliest-free-crew dispatch and actual source-connected network components; route witnesses are not physical power flows, measured MW, or unique repair bottlenecks. The method is a training-data-dependent heuristic. Do not use the future 2000-realization independent cohort for tuning; report leave-one-out and sample15 sensitivity for any newly selected best candidate on the already-trained 64 realization set.

These are method-development experiments. Do not promote a single lucky best chromosome, change risk objective, claim global optimality, or call failure to reject zero evidence of equivalence. Every job should return valid 92-ID permutations and hashes, actual expensive distinct/attempted counts, and no new physical data.
