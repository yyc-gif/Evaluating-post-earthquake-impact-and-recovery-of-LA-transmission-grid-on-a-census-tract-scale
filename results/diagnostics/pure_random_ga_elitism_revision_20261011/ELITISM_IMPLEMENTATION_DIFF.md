# Actual execution path and change

The frozen pure-random path is the original ga_variant_engine.run_search plus the zero-incumbent guard/100-random initializer in ga_random_initialization_isolation_20261011/study.py. This isolated source makes the same empty-incumbent guard directly executable; paired_random_pool already uses the exact random.sample initializer. r1_ga_revision.py is imported only for unchanged OX/inversion helpers and is not edited.

Prior elite: unique current-generation chromosomes ranked by negative loss descending, then chromosome lexicographically ascending. Legacy overwrites child index99 BEFORE evaluation regardless of fitness; it only knows that child's score if the run-local cache already contains it. Passive best_seen retains every actually evaluated strict improvement, with first exact score tie retained. The completed-generation archive is separately observed and never inserted as an additional prior.

Default remains LEGACY_LAST_POSITION_ELITISM. New explicit keyword elitism_mode=POST_EVALUATION_WORST_OFFSPRING_ELITISM evaluates the complete proposal before survival. Parent selection, OX, swap, ranking, maximization objective, random draws, independent caches and100k distinct stopping remain unchanged. Initial pool/RNG and first unmodified proposal are recorded and paired. A top-of-loop guard makes repeating a fully completed budget idempotent without changing uninterrupted baseline search.

Checkpoints retain mode, previous elite, full/partial score prefix, next_index, finalization flag, counters, elite event keys, complete private cache, exact RNG and trace history. A mode mismatch cannot resume. Older checkpoints without a mode identify legacy. Cached trailing children may finish a generation at the budget, but no additional unique child is scored. Conditional survival and generation observation occur once, only on complete scoring.

Original source SHA256: 9613ed38642c46a4cb92f20d93434bfa8059ed30eb5e2adc8f670998b21a29e4. Authorized development source SHA256: 38bd92b4a8fc71e55e5ebd2f4fea6a23dd5f0e09c49f6a1e51b0ce13685ea503. No scientific evaluator or physical file changes.
