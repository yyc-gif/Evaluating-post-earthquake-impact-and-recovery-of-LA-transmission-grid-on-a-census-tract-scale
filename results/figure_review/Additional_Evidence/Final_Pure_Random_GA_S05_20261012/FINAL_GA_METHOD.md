# Final legacy pure-random GA: reconciled method and candidate

## Retained Execution Procedure

| Item | Finalized value |
|---|---|
| Initial population | 100 independent uniform random permutations of the identical 92 station IDs |
| Population | 100 |
| Crossover | OX; probability 0.80 per selected parent pair |
| Mutation | Swap; probability 0.10 per child |
| Tournament | Size 3; exact fitness ties retain the first sampled contender |
| Generational elite | One previous-generation best; legacy replacement of the final generated child before that child's scoring |
| Elite fitness ties | Lexicographically smallest station-ID tuple |
| Passive archive | Best actually evaluated chromosome; strict score improvements only; exact ties retain first observation |
| Replication | Seeds 2026103100 through 2026103119; 20 independent runs |
| Budget | 100,000 distinct scored permutations per run; run-local initially empty exact-permutation caches |
| Planning objective | Unchanged mean population-weighted normalized service-loss hours over 64 fixed physical realizations |
| Final selection | Minimum planning loss among these 20 final100k receipts only; within 1e-9 h of minimum use lowest seed |
| Excluded selection evidence | Impact-seeded controls, 250k/500k continuations, all physical-validation outcomes |
| Disabled mechanisms | Heuristic/warm-start insertion, inherited optimized orders, adaptation, restarts, diversity replacement |

The actual search path is the archived `ga_random_initialization_isolation_20261011/study.py` private engine/initializer with `ga_variant_engine.py`. Its immutable source identity and both source hashes are retained in the JSON record and source manifest. The initializer draws each chromosome using `random.Random(seed).sample(domain,92)`, with no incumbent dictionary and an empty archive before the first actual score. All 20 saved pools contain 100 unique valid permutations. Their original receipts and RNG-state hashes are archived, not regenerated. Reference/preflight Impact-first scoring outside the search is not incumbent injection or inheritance and is not counted as a distinct search-cache query.

Fitness maximizes negative service loss. The generation archive and passive best-observed archive are not generation-mean fitness, and the returned sequence is the passive best-observed one, including evaluated candidates in an incomplete final generation. The legacy last-position operation is retained deliberately as the method actually used to produce and validate this candidate. It is not relabeled as the later post-evaluation worst-offspring correction.

## Exact Candidate

- Seed: `2026103108`; budget: `100000` distinct evaluations.
- Planning loss: `32.99552241352315 h`.
- Full newline-joined 92-ID permutation SHA-256: `edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a`.
- Full sequence: `FINAL_GA_CONFIGURATION_AND_CANDIDATE.json`, field `candidate.sequence`; original source bytes are also in `SOURCE_EVIDENCE.zip`.
- Original first best observation: evaluation `98756`; selected pool's initial best: `36.08101107593356 h`.
- Reused independent production QA: all 64 planning cases passed; maximum absolute per-case kernel/production difference `3.439026841078885e-12 h`, native mean `32.99552241352189 h`. No new evaluation was performed.

The selection rule reproduces the archived chosen candidate exactly; it does not select again using validation outcomes. All 20 saved final sequences remain in the lossless evidence archive.

## Required Disclosures

Pure-random initialization is a supported **post-data method choice**. The original automatic adoption rule did not pass: strict proximity to `32.99884077388271 h` was achieved by 10/20 main100k runs, not the registered 90%. Twenty-run selection may be reported; reliable near-optimal single-run convergence may not.

The later corrected-elitism sequence was a different diagnostic candidate. Its prospective validation recommended retaining this prior pure-random sequence: revised-minus-prior mean loss `+0.008821754060 h`, simultaneous95 interval `[+0.006140493711,+0.011305551263] h`. That finding supports keeping candidate identities separate; it does not demonstrate that legacy elitism is universally the better optimizer. Engineering correctness, optimizer-seed performance and fixed-policy physical outcomes remain distinct. No later-cohort outcomes enter S05 C/D.

The original 64-state planning horizon is `2855.2540131100995 h`. Existing completion-bound evidence establishes equivalence to the 480 h integral on those planning states; independent validation explicitly uses 0-480 h. Model, scheduler, station set, network, source gate, travel, mapping, durations and normalization are unchanged.

This package finalizes the **method description and proposed S05 only**. Formal strategy files and manuscript figures remain untouched. No new search, physical sample, production evaluation or bootstrap resampling occurred.
