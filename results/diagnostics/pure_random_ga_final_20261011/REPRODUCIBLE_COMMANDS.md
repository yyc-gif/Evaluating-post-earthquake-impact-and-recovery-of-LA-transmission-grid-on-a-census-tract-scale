# Reproducibility and execution boundaries

Run from the isolated worktree `_gaf12`, on branch `diagnostics/pure-random-ga-final-freeze-validation-20261011`. Python is `C:\Users\yinch\anaconda3\python.exe`. Original source/runtime and input bytes are verified against the completed study and the verified validation executor; LF/CRLF byte differences are documented separately in EXECUTION_FREEZE.json. Payload hydration occurs only in this isolated worktree and is not staged as a science change.

```powershell
$env:PYTHONPATH = Join-Path (Get-Location) 'src'
$env:NUMBA_CACHE_DIR = Join-Path $env:TEMP 'gaf12_numba'
$env:OMP_NUM_THREADS = '1'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$py = 'C:\Users\yinch\anaconda3\python.exe'
$script = 'results/diagnostics/pure_random_ga_final_20261011/finalize.py'
& $py -B $script setup
& $py -B $script engineering
& $py -B results/diagnostics/pure_random_ga_final_20261011/verify_package.py preflight
```

`setup` reads already completed search receipts and refuses to overwrite a freeze. It does not execute the GA. Engineering uses existing planning cases and one synthetic late-completion fixture, never a genuine new draw. A Windows-spawn test verifies that the reused worker sees the new fixed candidate and directory rather than the previous study's constants.

After explicit new candidate-specific authorization and a committed preregistration receipt:

```powershell
& $py -B $script authorize
& $py -B $script execute
& $py -B $script analyze
& $py -B $script package
```

Authorization is a human scope confirmation, not implied by running a command. Do not run the authorize phase without that confirmation. Execution reuses the original saved-once sampler and paired three-policy executor, analysis reuses the verified event-integral and paired bootstrap code. The reused internal candidate slot is named `ILS` in the old generic adapter, but is explicitly configured here to `GA-pure-random`; no ILS search is called or represented as the candidate. Legacy physical case identifier text is only a saved-record identifier, not an optimizer label. The actual strategy names and permutation hashes govern identity.

A completed cohort cannot be redrawn or reevaluated. No outcome-dependent tuning, early stopping or candidate reselection is permitted. Retain negative results. A 20,000-resample realization-level paired bootstrap uses a newly reserved seed and simultaneous two-population-contrast intervals; hospital and equity results remain descriptive pointwise.

Only the two new package directories are staged. Existing formal files, source files, manuscripts, prior raw evidence and the original staged index are excluded. `verify_package.py remote` reuses actual remote Git LFS byte downloads and SHA/size checks, not just pointer checks.
