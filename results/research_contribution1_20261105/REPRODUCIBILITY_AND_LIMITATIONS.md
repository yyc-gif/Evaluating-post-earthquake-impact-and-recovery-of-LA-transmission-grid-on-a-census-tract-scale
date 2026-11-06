# Reproducibility and Limitations

## Authority and frozen inputs

- Issue: [#4, Contribution 1](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/issues/4)
- Detailed instructions: `docs/research/CONTRIBUTION1_REPAIR_SEQUENCING_MECHANISM_TEST_20261105.md`, GitHub blob `13795e3c4c715e1f5e5cb70b9d995c4f19e5a1f5`.
- Branch baseline: `7704f766a648f6631acc474a8b02eb6e357adbc2`.
- Protocol was committed before the substantive paired perturbation run (`1531051`); the subsequent protocol clarification is `1d71936`.
- Input hashes, station/tract counts, scenario identities, schedule/sequence hashes and the external summary dependency are recorded in `FROZEN_INPUT_REGISTRY.json`.
- Key source hashes include frozen 2pc50 physical inputs `fa40cc26567c22e7d8195e04949e2ef7dbc960a9751f4b9af3d687edf542cdcb`, M1 mapping `472aaa865e74b0d613e60e480e8da46d13604056048b90ba1f1f429060489446`, source graph `1a3073240a6dca3e902e0bf5c2b975c67ff100892d85f007270e9855250bd225`, and production source gate `8d325397f42780b485f6ce093a867647eb4faadafe9a134c635f69dd5a804c44`.

The 52,767,419-byte formal realization summary is locally materialized at `results/research_contribution1_20261105/.cache/formal_realization_summary.parquet` because the archived LFS path is too long for this Windows checkout. Its SHA-256 is `840b826f036822bf03fec21367dc5ab3850a9a4c757d718883f439b645ba565d`. It is not duplicated in the branch. Re-run requires the same frozen archive payload locally.

## Independent checks

- 1,000 physical realization hashes and ordered station identities verified.
- Seven saved policy schedules checked against their manifest-bound sequence and physical hashes; 126 completion/arrival/travel/crew/dispatch array checks matched exactly.
- 16 single-state comparisons between an equivalent graph traversal and the production source-gate implementation matched exactly for F, C, and service availability.
- The event-history pass used the production completion-step service gate and checked each policy-realization integrated component burden against the saved realization summary with a `<1e-10 h` stop condition. The successful earlier pass did not persist the exact maximum error value; the current checkpoint revalidates all 641,816 event keys and physical sample hashes. Consequently `max_reconstructed_vs_archived_burden_difference_hr` is intentionally null in `NUMERICAL_QA.json`, not imputed.
- Integrated component additivity maximum error: `3.552713678800501e-14 h`.
- The final event-checkpoint run reproduced 6,144 paired perturbation rows for 128 realization IDs and regenerates both primary figures plus the three-event illustration.
- Eight tests passed across `tests/test_c1_mechanism_actionability.py`, `tests/test_r1_source_gate.py`, `tests/test_r1_formal_schedule.py`, and `tests/test_r1_formal_offline.py`. The initial broad collection failed because the sparse worktree omitted tracked `src/la_grid/paths.py`; the exact file was temporarily materialized from the frozen commit for the successful run and then removed, leaving the sparse worktree unchanged.
- The three final PDFs were inspected for vector content and embedded fonts; the event illustration contains vector drawing paths and no raster images. PNGs are high-resolution previews, not the analytical source.

## Runtime note

Repeated hypothetical single-state checks through the existing Numba-compiled `_connected_monotone` path caused a Windows access violation in the source-gate module. Production frozen event histories were not replaced: they continue to use the production gate. Only the repeated one-state target-potential scan uses a pure graph traversal, and its exact equivalence was tested against the production gate on 16 states. The Numba kernel itself was not edited.

## Data-retention note

The executable script writes full process-level CSV outputs and a 38 MB compressed event table locally. Under the project’s storage rule, intermediate CSV/event dumps are not uploaded. The committed package therefore contains the reproducible script, protocol, compact JSON QA/summary, explanatory report, tests, and final PDF/PNG figures; rerunning with the frozen local sources regenerates the omitted process tables.

## Reproduction

From repository root with the registered frozen inputs available:

```powershell
$env:NUMBA_DISABLE_JIT = '1'
python src/la_grid/diagnostics/c1_mechanism_actionability.py `
  --summary results/research_contribution1_20261105/.cache/formal_realization_summary.parquet `
  --reuse-event-history
python -m pytest tests/test_c1_mechanism_actionability.py -q
```

Adjacent source-gate and schedule regression tests:

```powershell
python -m pytest tests/test_r1_source_gate.py tests/test_r1_formal_schedule.py -q
```

For a fresh full event reconstruction, omit `--reuse-event-history`; this only post-processes existing completion arrays and does not rerun earthquake, damage, restoration scheduling, or optimization models.
