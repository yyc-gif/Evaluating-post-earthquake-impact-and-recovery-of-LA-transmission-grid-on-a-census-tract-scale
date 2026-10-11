# Prospective Standalone ILS Specification

Authority: starting commit `62f0c2be4f1e37f25e3db8d0d042cd5d0cfcfd3f`; diagnostic branch only. No formal strategy promotion or manuscript edits.

## Search

- Initial current permutation and best-ever archive: the original deterministic Impact-first ordering only. No other reference is evaluated by the model loader. Loading the original authority JSON to verify sample hashes/horizon does not inject its sequence.
- Representation: all original 92 station IDs exactly once. The original 57-crew C57_D1 decoder and objective are unchanged.
- Proposal: Python `random.Random(seed).sample(range(92), 2)` selects two distinct positions uniformly, then swaps them. Exactly one neighborhood.
- Acceptance: current changes only when fitness improves by more than `1e-12` normalized loss hours. Fitness is negative original mean service loss. This tolerance follows the previous parameter-defense implementation, not a new tuning step.
- Archive: exact best observed fitness, including a sub-tolerance observation; never worsens. Exact objective ties within a run keep the first observed permutation. This small distinction is explicit: the archive minimum and the tolerance-based local current need not coincide.
- Stagnation: 2,000 consecutive non-improving local proposals, including cache hits. A strict accepted local improvement resets it.
- Perturbation: copy the best-ever permutation and make 2, 4, then 8 successive swaps cyclically. Evaluate only the final perturbed permutation, not the intermediate permutations. The current state accepts this restart regardless of its score; the best archive remains protected. Reset stagnation after each perturbation.
- Record every perturbation's positions, intermediate keys, final cancellation, and final cache revisit. Cancellation does not trigger an extra uncounted retry.
- No certified local optimum, exhaustive refinement, population, crossover, tournament, mixed neighborhood, LNS, or GA-derived starting information.

## Accounting And Resume

Every complete permutation lookup is an attempted objective call. Only a cache miss invokes the original 64-realization evaluator and consumes one distinct-evaluation unit. Cache is private to a run. Initial Impact-first costs one declared unit. There are no shared scored prefixes. Each worker separately makes one disclosed Impact-first JIT/setup score, not used in any search cache or archive.

Safety cap: ILS 60 times requested distinct budget; GA retains its original engine cap of 50 times. A capped run is explicitly incomplete and is not represented as an equal-budget completion. GA's attempted count includes population re-scoring for reproduction, unlike ILS proposal attempts; this overhead is retained and reported.

Budget boundaries occur after a completed state transition. ILS serializes current, archive, RNG, cache, stagnation, restart phase, improvement history and counters. GA uses its existing checkpoint engine without changing operators. Extension is state continuation, not replay of a newly initialized prefix. No new expensive calls outside the budget except separately recorded setup and independent verification.

## Registered Experiment

See `EXPERIMENT_DESIGN_AND_SEEDS.json`. Smoke: eight fresh seeds, 20k each. Main: twenty different fresh seeds, ILS and fair GA at 100k. The first ten main seeds, registered before any outcome, continue to 250k and 500k. Record 20k/50k checkpoints. The fixed GA parameters remain P=100, ordered crossover=0.8, swap mutation=0.1, tournament=3, elites=1; only initialization is changed to Impact-first plus 99 random permutations, with no seven-reference archive or prior neighbors.

Candidate pool excludes smoke and includes only the twenty main ILS searches and their ten prescribed extensions. Select lowest exact original mean planning loss; exact ties resolve by ascending sequence SHA256, then seed, then budget. The frozen GA is a separately evaluated reference, never injected into either optimizer.

Paired seed comparisons estimate optimizer variation conditional on the same 64 development states. They are not generalization evidence. Report pointwise paired t/bootstrap intervals and five-endpoint Bonferroni t intervals; 250k/500k have ten paired seeds, not twenty. No prospective noninferiority margin is specified, so competitive judgment must not be called a formal equivalence test.

The previously completed 2,000-realization cohort is preserved by hash only and is not parsed or used. No new physical samples are authorized. A replacement recommendation is conditional on a frozen future confirmation plan and separate author authorization.
