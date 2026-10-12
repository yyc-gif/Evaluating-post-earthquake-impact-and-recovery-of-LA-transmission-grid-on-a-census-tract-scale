# Pure-random GA elitism revision: completed diagnostic package

Read `FINAL_ELITISM_DECISION.md` first. The recommendation is **ADOPT POST-EVALUATION WORST-OFFSPRING ELITISM** for future explicitly configured use, without claiming demonstrated stochastic optimization superiority or promoting a new formal restoration sequence.

## Evidence map

- Implementation: `src/la_grid/diagnostics/ga_variant_engine.py`, explicit legacy and post-evaluation modes; `ELITISM_IMPLEMENTATION_DIFF.md` and `POST_EVALUATION_ELITISM_SPECIFICATION.md`.
- Engineering: eight synthetic tests in `test_elitism.py`; `ALGORITHM_UNIT_TEST_RESULTS.json`; exact cached legacy replay in `LEGACY_REPRODUCTION_PARITY.json`.
- Prospective design: `EXPERIMENT_DESIGN_AND_SEEDS.json`, committed at `50d7318` before searches; frozen runtime source hash and the subsequent Git-only line-ending normalization at `e4cef14`.
- Actual experiments: `runs/`, three `RUN_RESULTS_*.csv`, 80 `raw_evidence/*.zip` with member-hash manifests. Forty fresh runs form twenty pairs; the first ten pairs continue to 250k and 500k. No endpoint is treated as an extra independent seed.
- Paired inference and costs: `PAIRED_SEED_LEVEL_RESULTS.csv`, `PAIRED_OBJECTIVE_EFFECTS.csv`, `METHOD_DESCRIPTIVE_STATISTICS.csv`, `BUDGET_AND_COMPUTATIONAL_COST.csv`, `BUDGET_EXTENSION_MARGINAL_GAINS.csv` and convergence tables.
- Survival mechanics: `ELITE_REPLACEMENT_EVENT_COUNTS.csv`, `OFFSPRING_DISCARD_ANALYSIS.csv` and both event-detail tables. Retrospective legacy discarded-child scores never enter search selection, caches or candidate choice.
- Native production check: `IMPORTANT_CANDIDATE_PRODUCTION_QA.json`, per-realization CSV and `POST_DEVELOPMENT_CANDIDATE_FREEZE.json`; nine unique sequences checked on all 64 original planning states.
- Preservation and publication: `REPRODUCIBILITY_AND_PRESERVATION_QA.json`, `OUTPUT_HASH_MANIFEST.json`, remote-byte receipts and `TOTAL_COMPUTATION_ACCOUNTING.json`.
- Failed attempts: unit-test MAX_PATH fixture failures and two post-search audit terminations are disclosed, not erased. The persistent audit ledger prevents replaying completed retry scores; the first unpersisted attempt has bounded, not exact, additional computation accounting.

## Reproduction prerequisites

This package deliberately reuses the existing production and statistical machinery. Place verified repository worktrees as siblings:

| Directory | Commit / purpose |
|---|---|
| `_ger14` | This diagnostic branch; executed GA source and this package |
| `_gpc13` | `3da06ca6b9d5bb55d179ff1ff7bdcae583b2f231`; prior utilities and read-only parameter evidence |
| `_gaf12` | `f539e3fe6015122d73e5656109e751770550bb70`; unchanged production modules, fixed physical planning samples and legacy candidate lineage |
| `_gri11` | Historical initialization evidence referenced by the prior package; use its recorded preservation identity rather than guessing a newer revision |

Restore actual Git LFS payloads, not pointer files. `PRESERVATION_BASELINE.json`, `EXPERIMENT_DESIGN_AND_SEEDS.json` and `FIXED_PLANNING_MODEL_IDENTITY.json` identify exact archived inputs. The preservation phase additionally needs the original protected revision checkout; it is read-only and must not be reconstructed by resetting an existing worktree.

Sequence SHA-256 is computed from UTF-8 station IDs joined by newline with one trailing newline. Cache keys are 92-byte permutations of indices 0..91 into the station order recorded in `FIXED_PLANNING_MODEL_IDENTITY.json`. Raw checkpoint score maps preserve every actual distinct evaluation and its insertion order, exact RNG state, pending/completed generation state, population, counters and archives.

From `_ger14`, using the recorded Anaconda environment and all three numerical thread limits set to 1:

```powershell
$pkg = 'results/diagnostics/pure_random_ga_elitism_revision_20261011'
& 'C:/Users/yinch/anaconda3/python.exe' "$pkg/analysis.py" summarize
& 'C:/Users/yinch/anaconda3/python.exe' "$pkg/analysis.py" production
& 'C:/Users/yinch/anaconda3/python.exe' "$pkg/analysis.py" decision
```

Inspect the committed event tables instead of repeating the completed retrospective audit. `REPRODUCIBLE_COMMANDS.md` records the original execution order and exact continuation boundary. Reconstructing a search requires a fresh diagnostic runtime directory or restoring its archived checkpoint, not overwriting the original completed state. Raw checkpoints were serialized with the original `Variant` configuration represented as a dictionary, so legacy class-pickle dependencies are not required for those new checkpoints.

## Scientific boundary

The objective horizon is the original fixed planning horizon, approximately 2855.254013 h, not Stage 7's 480 h descriptor. No new physical realization, manuscript, official figure, Stage 7 coordinate/label, scheduler, source gate, crew model, mapping or formal restoration output was generated or modified. The proposed independent-validation specification is not execution authorization. Old candidate validation cannot be transferred to the diagnostic POST candidate.
