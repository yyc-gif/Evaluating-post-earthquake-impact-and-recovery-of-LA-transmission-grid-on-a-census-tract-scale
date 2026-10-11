# Reproduction And Execution Boundaries

Run from the isolated checkout at this package's branch. Python is `C:\Users\yinch\anaconda3\python.exe`. Set `PYTHONPATH=src`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, and `NUMBA_NUM_THREADS=1`. Windows extended-length paths are used by the diagnostic wrappers.

## Actual Prospective Execution

```powershell
python -B -m la_grid.diagnostics.standalone_ils_20261010 setup
```

The design, fixed fresh seeds, implementation, initial seven-test receipt and preservation baseline were committed at `2817b06` before smoke and main confirmation. Setup refuses to overwrite existing registration. The exact full commit is recorded in `PREREGISTRATION_COMMIT.json`.

```powershell
python -B -m la_grid.diagnostics.standalone_ils_20261010 smoke --workers 8
python -B -m la_grid.diagnostics.standalone_ils_analysis_20261010 smoke
```

Smoke completion and independent production parity were committed at `56e9cce` before main launch; no configuration or seed selection changed from smoke outcomes.

```powershell
python -B -m la_grid.diagnostics.standalone_ils_20261010 main --workers 12
python -B -m la_grid.diagnostics.standalone_ils_analysis_20261010 summarize
python -B -m la_grid.diagnostics.standalone_ils_analysis_20261010 verify
python -B -m la_grid.diagnostics.standalone_ils_analysis_20261010 replay
python -B -m la_grid.diagnostics.standalone_ils_literature_20261010
python -B -m la_grid.diagnostics.standalone_ils_report_20261010 evidence
python -B -m la_grid.diagnostics.standalone_ils_report_20261010 report --recommendation ILS
python -B -m la_grid.diagnostics.standalone_ils_report_20261010 qa
```

The recommendation argument records an author-review methodological decision after completed analysis; it is not an automatic scientific promotion command. Search wrappers continue existing state. Do not run a completed batch merely to reconstruct information already retained in its archive. Reanalysis/verification do not generate physical samples, but have explicit individually counted sample-level evaluator calls.

## Tests

```powershell
python -B -c "import la_grid.paths as p; from pathlib import Path; p.REPO_ROOT=Path('\\?\'+str(p.REPO_ROOT)); import pytest; raise SystemExit(pytest.main(['-q','tests/test_standalone_ils_20261010.py','tests/test_r1_source_gate.py','tests/test_r1_realization_scheduling.py','tests/test_ga_ils_parameter_defense_20261010.py','--basetemp','_testtmp3']))"
```

The initial seven tests were run before computation; the supplemental 26-test receipt distinguishes later 92-item and horizon-clipping checks. Synthetic exact replay does not consume physical samples or search budgets.

## Evidence And Cost

`RAW_SEARCH_AND_RESUME_EVIDENCE.zip` contains every smoke/main raw file, including all final 92-station permutations, initializer receipts, best-improvement histories, restart histories, cached evaluations and exact RNG/checkpoint states. `RAW_EVIDENCE_MANIFEST.json` lists each member's size and SHA-256. Raw directories are ignored only to avoid duplicating the archive in Git, not omitted from the delivered evidence.

Continuation normally overwrites each run's checkpoint payload; intermediate checkpoint digests remain in boundary receipts, but their original timer/gzip bytes are not separately retained. Final state/cache payloads are retained. The additional production-size ILS cache replay verifies all 20 trajectories, ordered cached keys, every saved budget-prefix best sequence/counter and final RNG/logical state. It reads saved scores without calling the physical evaluator or creating new optimizer replications; its CPU/wall cost is reported separately. Synthetic GA checkpoint/resume tests and actual GA continuation receipts remain the GA replay evidence.

No replayed prefix is counted twice as computation. Twenty seed pairs have 100k budgets; ten prespecified pairs continue to 500k. The 250k and 500k records are dependent observations of those same searches. Distinct scoring calls include the initial candidate, with one additional JIT/setup score per initialized worker counted separately. Smoke, main, verification and archive overhead have separate receipts. GA diagnostic population instrumentation differs from ILS, so wall comparisons are implementation-specific.

## Horizon And Preservation

The planning authority integrates to 2855.2540131100995 hours. The manuscript and archived independent-validation endpoint is 480 hours. The new event audit independently checks zero post-480 loss for the selected ILS, frozen GA and Impact on all 64 planning states. No planning objective is changed and no equivalence for future samples is presumed.

The original revision checkout, staging and formal/validation records are hash-checked before and after. Hydrating historical LFS pointers inside this isolated checkout can appear as unrelated modified files under inherited attributes; those paths are never staged, edited semantically or pushed. Temporary pytest files are also excluded. No reset, clean, stash or force-push is used.

```powershell
python -B -m la_grid.diagnostics.standalone_ils_publish_20261010
```

Publication scopes the committed diff, uses non-forced push and verifies remote HEAD plus streamed full LFS bytes and SHA-256. Its receipt is committed/pushed separately. The formal policy, original manuscript/figures and completed 2,000-state physical validation stay unchanged. The prospective new validation plan is preparation only, not executed by any command above.
