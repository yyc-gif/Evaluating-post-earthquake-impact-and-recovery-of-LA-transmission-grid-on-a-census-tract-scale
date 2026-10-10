# Reproducible Commands

Run in the diagnostic checkout, with the pinned Anaconda Python runtime.

```powershell
$env:PYTHONPATH = 'src'
$env:NUMBA_CACHE_DIR = Join-Path $env:TEMP 'val4-20261010-numba'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMBA_NUM_THREADS = '1'
& C:\Users\yinch\anaconda3\python.exe -m la_grid.diagnostics.independent_validation_20261010 verify
& C:\Users\yinch\anaconda3\python.exe -m la_grid.diagnostics.independent_validation_20261010 dry-run
```

The dry run reads only saved physical cases and synthetic engineering transformations; it never calls a physical sampler. Reproduces checks, receipts, tables, figures and same-state crash/resume tests. Exact commands for input hydration/freeze appear in SETUP_COMMAND.json. Recreating prepare after a code change intentionally creates a different freeze; it must be reviewed before authorization.

## Future Execution Only After Explicit Author Approval

No authorization file is supplied by this preparation. After approval, record the actual author name, UTC timestamp and verbatim request in an external authorization JSON with fields:

```json
{
  "authorization_type": "EXPLICIT_AUTHOR_APPROVAL_FOR_FIXED_2000_VALIDATION",
  "author": "ACTUAL_AUTHOR",
  "authorized_at_utc": "ACTUAL_APPROVAL_TIMESTAMP",
  "verbatim_author_request": "ACTUAL_EXPLICIT_APPROVAL",
  "freeze_sha256": "45d157c0a3b9460d7c29e389b649afef0f0e6bc568bfba8eb773f9b5b974ae15",
  "sample_size": 2000,
  "allow_policy_reselection": false
}
```

These placeholders are documentation, not permission. The executor checks the receipt and authorization, pinned runtime/code/inputs, readiness QA and capacity before invoking sampling. Use a new external dedicated archive, never a formal-results or manuscript path. An archive inside this repository is allowed only beneath results/diagnostics/independent_validation_ready_20261010/authorized_validation:

```powershell
& C:\Users\yinch\anaconda3\python.exe -m la_grid.diagnostics.independent_validation_20261010 execute --authorization C:\PATH\ACTUAL_AUTHOR_APPROVAL.json --archive C:\PATH\independent_validation_fixed_2000
```

Resume using the exact same command and authorization. Completed cases are verified and reused; no optional sample-count flags exist. A completed run rechecks and republishes evidence without redrawing. Do not delete physical receipts or redefine RUN_IDENTITY to restart. If a crash leaves RUN.lock, verify recorded process is dead on the recorded host before removing only that stale lock. A DRAW_STARTED marker without DRAW.json or an ABORT_OVERLAP receipt is a stop-for-review condition, not an invitation to regenerate. No intermediate effect tables are produced before all 2,000 cases finish.

Final exports: PRIMARY_PAIRED_EFFECT.csv; PAIRED_EFFECTS.csv; POLICY_OUTCOMES.csv; T80_CENSORING.csv; REALIZATION_OUTCOMES.csv; GA_REFINED_ILS_REALIZATION_CHANGES.csv; RECOVERY_DISPARITY_CURVES.csv; RECOVERY.png; DISPARITY.png; EXPORT_RECEIPT.json; REPRODUCIBILITY_RECEIPT.json. Per-realization archives contain shared physical vectors/hashes, exact f/F/C/e and loss-component arrays, station/tract integrals, complete dispatch/crew/origin/travel/arrival/completion records, event times and policy identities. Per-draw receipts include PCG64 before/after state and canonical byte hashes.
