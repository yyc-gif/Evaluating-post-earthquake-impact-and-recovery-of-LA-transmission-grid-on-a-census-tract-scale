# Next paper milestone: freeze and authorize an untouched physical-realization comparison

**Status: PROPOSAL ONLY — NO AUTHORIZATION TO GENERATE NEW PHYSICAL SAMPLES.**

Current scientific and optimizer evidence:
- Original formal GA sequence `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`, J64 = 32.997840773883 h, remains unchanged;
- Refined ILS challenger `75a1014c7f921c09b574eed4eebcaa412f86fcbc61487bf4a1277c4eb448ddbd`, J64 = 32.996137365389 h, independently production-path verified;
- Refined ILS wins 14/64 original planning states, loses 50/64, and excluding realization15 reverses the in-sample mean comparison; its smaller planning J cannot be called robust;
- GA-vs-ILS optimizer results on reused 64 states are close and have no resolved method-average superiority; LNS v1/v2 newly failed despite completing 160 equal-budget searches;
- The unchanged LNS event-route targeting has also failed bounded fixed-start proposal-transfer checks. Do not use validation results to choose a new optimizer.

## Existing final-validation authority, still pending author approval

`results/diagnostics/final_ga_method_20261009/FINAL_VALIDATION_PROTOCOL.json` and `FINAL_INDEPENDENT_VALIDATION_PROTOCOL.md`, anchored to the original `b1030f839d522fed4af21e424472e3f8b076797b`, explicitly say `PROPOSED; NO_AUTHORIZATION_TO_GENERATE_NEW_PHYSICAL_SAMPLES`. This addendum does **not** mutate the frozen files or authorize execution.

Unchanged prospective model: N=2,000 independent Monte Carlo physical realizations on the same 2pc50 hazard/C57_D1 resources. `numpy.default_rng(SeedSequence([202610091,3,2,r]))`, for r=0..1999. Call original fragility/repair sampling functions once, share exactly the same states across all fixed policies, halt on a canonical exact hash overlap with the saved64 or previously inspected1000. A new sample archive is separate. No use for further tuning, early stopping or sequence replacement. Principal endpoint is population-weighted integrated modeled service loss 0–480h; unchanged weights/gate, no silent endpoint truncation or normalization change.

Primary comparison stays **formally frozen GA minus Impact-first**. This avoids rewriting the principal research hypothesis after extensive optimization. Whole-physical-realization paired bootstrap at 20,000 resamples and a Monte Carlo SE, with bootstrap RNG frozen to `2026100901`. Describe secondary comparisons without unapproved confirmatory multiple claims.

## Explicit decisions to finalize **before** any new physical draw

1. Pin the existing official comparator list, repairing omitted original **Centrality-first** and **Closeness-first** sequences from `Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json`. The current `VALIDATION_COMPARATOR_SEQUENCES.json` includes 9 ordered policies plus unconstrained; adding these two gives 11 ordered plus unconstrained. Hash the canonical full 92-station orders and comparator source files and record their immutable identities.
2. Decide whether to add the independently verified, **fixed refined ILS** order as a **secondary diagnostic comparator** (making 12 ordered plus unconstrained = 13 policy conditions). This is strongly informative about training-sample overfitting but should not trigger ex-post switching of the primary GA outcome.
3. Decide which remaining exploratory GA sequences need to be evaluated as descriptive controls, not postvalidation candidates for replacement. Ensure no changing the comparator policy set after examining the physical results.
4. Freeze the outcome tables and subgroup descriptions (self/threshold/source, Q1–Q4, hospital-linked, T80, Gini) before sampling. Use the original provider source gate; source-linked dependency mass is a *topological service-availability proxy*, not measured delivered electric power or clinical service.
5. Author explicitly approves the **one-time sampling-and-evaluation procedure and locked policy list**. Without that approval, perform only read-only input/hash/storage/disk/memory preparatory checks.

## Important statistical distinction

The 2,000 fresh simulations are a credible independent *physical* check of fixed candidate-versus-Impact-first performance **conditional on the same mathematical model**, not empirical utility restoration validation. The old development study estimates an approximate 95% half-width near 0.024 h for GA-minus-Impact under an exploratory SD of 0.54 h, if that variance transfers.

Differences between GA and refined ILS on the training mean are only ~0.0017 h with per-original-realization sample difference SD ~0.305 h. At n=2000, a rough 95% half-width based on that SD is ~0.0134 h, substantially wider than 0.0017 h. Hence the study may fail to rank GA vs ILS precisely even if it establishes that both improve on Impact-first. Do not misreport this as proof of equal strategies or use validation to reoptimize.

Do not invest in identical more v1/v2 LNS sweeps. The only new optimizer-work reason would be a **fundamentally new proposal family** with a separately specified mechanism and matched controls, all completed before final-validation sampling. Continued tuning on the same64 cannot replace the independent validation evidence.

**No sampling, model change, formal candidate change or manuscript modification performed by this preparatory document.**
