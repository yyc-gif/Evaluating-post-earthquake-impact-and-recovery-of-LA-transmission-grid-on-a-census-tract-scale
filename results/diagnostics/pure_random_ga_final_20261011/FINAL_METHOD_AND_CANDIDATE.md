# Final GA execution and candidate freeze

Use 100 independent uniformly random permutations, OX0.80, swap0.10, tournament3, elite1. Execute independent runs for seeds2026103100-2026103119, each with100,000 distinct evaluations and its own initially empty cache/archive. No heuristic, prior optimized chromosome, adaptive mutation or restart is injected. Passive retention preserves the best actually observed chromosome. The combined budget is2,000,000 per-run distinct mean-objective evaluations (64 unchanged planning states each), not2,000,000 globally unique permutations.

Select the lowest original64-state mean loss among the20 completed PURE100k final receipts; candidates within1e-9h of the observed minimum tie by lowest seed. There is no actual tied minimum. Existing within-run exact tie rules are documented in FINAL_GA_EXECUTION_PROTOCOL.json. Reserve250k/500k records and controls do not enter candidate selection. No search was launched for this freeze.

The selected92-station permutation is seed2026103108, planning loss32.99552241352315h, SHA256 `edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a`. All92 IDs are in FINAL_RANDOM_GA_CANDIDATE.json. The saved100k checkpoint contains the same best-observed chromosome; its first strict improvement appearance is evaluation98756. The100 random initial permutations and empty archive are checked directly. The original production evaluator previously checked all64 states with maximum error3.44e-12h; that complete record is reused without rescoring.

## Required methodological disclosure

Random-only initialization is a supported **post-data methodological judgment**, approved in the current user request. It did not pass the original automatic adoption rule, whose fallback was Impact-seeded. At100k, only10/20 random-only runs reached the strict formal-best+0.001h cutoff; the reserved continuation had8/10 at250k/500k. Neither attained the prespecified90% single-run requirement. A20-run procedure is adopted, not a guarantee that every run finds the same quality. No independent20-run-block success probability is estimated from this one20-seed collection. Method,100k-budget and across-run selection freeze occur after observing these planning searches, before new physical validation.

## Validation and preservation

The proposed fresh2,000-realization protocol fixes the new candidate, Impact-first and legacy formal GA. The previous validation remains attached to its original sequences and cannot be transferred. Execution is authorization-gated; no new physical samples exist at this freeze. The original objective, physics, scheduler, graph, sources, crews, mapping and durations are unchanged. Formal legacy candidate/results and950 protected scientific files/862 staged items are preserved. Candidate-specific validation will be a separate reviewable package, not an overwrite of old science.
