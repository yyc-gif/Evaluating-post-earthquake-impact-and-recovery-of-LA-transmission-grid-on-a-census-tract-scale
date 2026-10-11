# Authorized Standalone ILS Prospective Validation

The human author's 2026-10-11 request authorizes exactly one new cohort and three fixed sequences. The immutable parent is `740f941f3614e51b15bcf6c91b3aff3afec9f2ea`; its `FUTURE_VALIDATION_FREEZE.json` is incorporated byte-hashed in `EXECUTION_FREEZE.json`. This is not authorization to promote a strategy, alter the manuscript or run any optimizer.

## Fixed Protocol

- Standalone ILS SHA256: `17705a83a7607862d05ec9d6b607d58e31ff644712ceb0d0652ce7e59642499f`.
- Formal GA SHA256: `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`.
- Impact-first retains its original full 92-station order and hash.
- Exactly 2,000 new 2pc50 physical states; original damage/positive-normal repair samplers, 57 C57_D1 crews, directed travel, 92-station network, 14 Core sources, 0.5 gate, M1 population mapping and 2,315 tracts unchanged.
- Independent per-index PCG64 streams: `default_rng(SeedSequence([2026110100,r]))`, r=0..1999. This concretizes the previously reserved seed and namespace before any draw. Old streams use a different prefix; all 64 planning, 1,000 original 2pc50 evaluation and 2,000 prior validation physical-pair identities are checked for exact overlap. A collision or interrupted uncommitted draw stops for review, not an automatic redraw.
- Every new DS/duration pair is saved once and shared by all three policies. All draws finish before evaluation; evaluation completion progress is printed without effects. Checkpoints retain original pairs; no interim outcome-based stopping or expansion.
- Exact 0-480 h normalized population-weighted service-deficit integration; full dispatch/completion events, including late completions, remain archived. T80 is the crossing time of each modeled aggregate trajectory; unreached cases are null/censored and restricted to 480 h, never deleted.
- Primary: ILS-minus-Impact mean loss, two-sided pointwise 95% percentile bootstrap; upper limit below zero supports modeled benefit. Secondary: ILS-minus-formal-GA mean and distribution. Both population-loss contrasts additionally receive Bonferroni 97.5% individual percentile intervals for a simultaneous 95% two-contrast family.
- 20,000 whole-realization paired bootstrap resamples, seed 2026110200; the same resample bank for all policies/endpoints. Other endpoint intervals are descriptive pointwise only. No unregistered equivalence margin, new objective or retrospective sample exclusions.
- Keep all negative results. Comparison of means, medians, quantiles, improved/worsened fractions and self/threshold/source losses does not imply a causal effect of an individual station movement or field accuracy.
- Freeze and commit executable code, authorization, seeds, sequence identities and engineering QA before any new physical draw. No tuning, candidate reselection, validation reuse or additional optimization stages.

## Commands

Run in the isolated `_vils7` worktree using the pinned Anaconda Python and original scientific libraries:

```powershell
$env:PYTHONPATH = 'src'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
$env:NUMBA_NUM_THREADS = '1'
$env:NUMBA_CACHE_DIR = Join-Path $env:TEMP 'vils7-numba'
& C:\Users\yinch\anaconda3\python.exe -B -m pytest tests/test_standalone_ils_validation_20261011.py tests/test_independent_validation_ready_20261010.py tests/test_r1_realization_scheduling.py tests/test_r1_source_gate.py -q --basetemp=_testval
& C:\Users\yinch\anaconda3\python.exe -B -m la_grid.diagnostics.standalone_ils_validation_20261011 verify
& C:\Users\yinch\anaconda3\python.exe -B -m la_grid.diagnostics.standalone_ils_validation_20261011 execute
& C:\Users\yinch\anaconda3\python.exe -B -m la_grid.diagnostics.standalone_ils_validation_analysis_20261011 analyze
& C:\Users\yinch\anaconda3\python.exe -B -m la_grid.diagnostics.standalone_ils_validation_analysis_20261011 package
```

Preparation was performed using `setup --source ../_ils6 --old-validation ../_val4` and `engineering`. Preparation/engineering made zero new physical draws; sampler ASTs/constants were checked against the original executable commit. Seventeen guard/scheduler/gate tests passed. Sixteen successful engineering production/kernel calls used three original planning states plus one late-completion synthetic fixture; a previous failed JIT-cache attempt completed one additional old-state production call. The Windows cache path was shortened without changing scientific code. An initial scenario-registry assertion was fixed before sampling. These engineering attempts are disclosed separately from the 6,000 prospective policy evaluations.

The earlier independent validation is read only for physical identities, entropy and byte-hash preservation, never for its policy outcomes. Exact runtime source bytes and Git LF/CRLF provenance are recorded separately; restoration of immutable input payloads is restricted to this new checkout. The original revision and staging, parent ILS study, original formal GA and complete old validation evidence are preserved.

The full raw cohort is ignored as loose files and delivered as `FIXED2000_FULL_EVIDENCE.zip` with every member's SHA256 and verified archive round-trip. Summary tables, numerical QA, authorization, hashes, report and reproducible scripts are committed separately. Git LFS is verified by actual downloaded bytes after publication, not pointers alone.
