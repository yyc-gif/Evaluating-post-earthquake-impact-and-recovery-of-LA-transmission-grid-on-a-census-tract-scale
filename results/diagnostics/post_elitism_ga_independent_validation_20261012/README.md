# Frozen post-evaluation GA physical validation

This diagnostic package executes exactly 2,000 new physical realizations and three fixed policies. No optimizer, parameter selection, physical-model revision, manuscript edit, Stage7 edit or formal strategy replacement is permitted.

The human authorization, full permutations, model/runtime hashes and prospective statistical rules are in `AUTHORIZATION_AND_EXECUTION_FREEZE.json`. `EXECUTION_FREEZE.json` locks executable files and the prior10,064-state identity registry. Engineering checks use saved planning states and a deterministic late-completion transformation, with physical samplers disabled; their16 production calls are separate from the6,000 new-cohort evaluations.

The existing native execution and bootstrap engines are reused from the hash-locked `_gaf12/src` checkout, not copied or modified. The runtime requires that sibling source checkout. Full provenance records permit reconstruction from the listed immutable source commits. The bootstrap includes two population-loss contrasts with Bonferroni simultaneous95 intervals; all other intervals are descriptive pointwise95. The frozen author-review decision rule is explicit and does not assert equivalence when an interval includes zero.

Execution, in this isolated worktree:

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:GIT_OPTIONAL_LOCKS='0'
$env:NUMBA_CACHE_DIR="$env:TEMP\gev15-numba"
$python='C:\Users\yinch\anaconda3\python.exe'
$p='results/diagnostics/post_elitism_ga_independent_validation_20261012'
& $python "$p/study.py" setup
& $python "$p/study.py" engineering
# Commit the preregistration BEFORE any draw; record its immutable commit receipt.
& $python "$p/study.py" execute
& $python "$p/analyze.py" analyze
& $python "$p/analyze.py" package
# Commit and push this package only, then download and verify actual LFS bytes.
& $python "$p/publish.py"
```

Setup refuses to overwrite a frozen study, completed execution refuses to rerun, and an uncommitted random draw stops for review rather than being redrawn. Every new physical receipt is retained in the losslessly verified full evidence ZIP, along with raw task schedules, native event trajectories and tract integrals. Downloaded remote LFS evidence is a temporary redundant copy, not a new scientific result.

The prior external manuscript-path exception is disclosed separately. No backup is restored or designated authoritative. Existing950 protected scientific files,862 staged items, all formal strategies and previous physical-validation records remain unchanged.
