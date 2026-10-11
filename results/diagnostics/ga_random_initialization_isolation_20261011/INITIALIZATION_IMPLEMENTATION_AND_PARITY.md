# Initialization Implementation And Parity

Authority: f9734afa09bd0a0e59b2b1d81d43599062d4c258, with remote diagnostic references 62f0c2be4f1e37f25e3db8d0d042cd5d0cfcfd3f and 740f941f3614e51b15bcf6c91b3aff3afec9f2ea. The protected engine and all production sources are unchanged. `study.py` compiles a private AST copy of `ga_variant_engine.py`, placing its four incumbent-ranking/archive assignment statements under `if inc`. No dummy incumbent is introduced. All remaining scoring, reproduction, tournament ties, OX, swap mutation, elite overwrite, cache accounting, and partial-generation budget behavior are reused unchanged.

Both modes pass an empty incumbent dictionary. The initial archive and run cache are empty; the first actually evaluated chromosome is the first observed best. A completed initial generation establishes the completed-generation archive. Best-observed output also includes scores at a budget boundary inside a generation; completed-generation archive identity is retained separately. In the seeded mode Impact-first occupies population position zero and is evaluated normally, not externally inserted into cache.

A Python `random.Random(seed)` generates all 100 independent permutations in both modes. PURE_RANDOM_GA uses the entire pool. IMPACT_SEEDED_GA replaces fixed position zero with Impact-first without drawing another random number. Initial sequences, every hash, original common pool, and post-initializer RNG hash are retained per run. This intentionally differs from historical controls that drew only 99 random permutations after pre-scoring Impact-first.

## Completed Engineering Checks

`ENGINEERING_QA.json` records two engineering seeds, both modes, each split at 333 distinct evaluations and continued to 1,000. Uninterrupted counterparts agree in ordered private caches, RNG state, attempted calls, population, scores, generation, phase, archive, and best sequence. All cached permutations are valid92-station orders. No lookup objective, restart, adaptive mutation or diversity replacement is enabled. The shared99 and post-initializer RNG match across modes.

An additional synthetic92-station objective compares the private engine against the unmodified engine with the original initializer and a nonempty incumbent: complete cache values, best sequence, and attempt counts agree. This confirms unchanged reproduction rather than relying only on a source diff. Three production-state checks per engineering mode/seed agree with the exact kernel below1e-8h; full64 checks are required later for prespecified important main candidates.

One pre-main engineering launch failed before scoring because the private dataclass module was not registered in `sys.modules`. Registration was added only in the isolated adapter, then all checks passed. This did not alter operators, physics, seeds, comparison rules or results. Engineering accounting: 8,000 physical mean-objective calls, 256 compiled individual-state checks,12 production individual-state checks, and2,000 synthetic parity objective calls. These are excluded from main search budgets.

## Freeze And Preservation

The design commits main seeds2026103100-2026103119, reserves their first10 for conditional continuation, holds100k/250k/500k distinct-permutation budgets, and defines the numerical margin and extension rule before main data. Each run has its own empty cache. Existing independent-validation cohorts are not parsed or used. The original planning NPZ contains an archived evaluation partition, but only its `planning_ds` and `planning_duration` arrays are accessed; no new samples are generated.

Required local input hydration copies SHA-verified Git LFS objects into this new checkout only. Apparent hydrated-file Git status differences are not staged. Original950-file hashes, revision HEAD/branch, staged binary diff and logical index identity are snapshotted. No reset, clean, stash, formal sequence replacement, manuscript editing or original worktree change is authorized.
