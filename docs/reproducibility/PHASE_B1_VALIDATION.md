# Phase B1/B2/B3 validation record

B1 moved tracked code, tests, research documentation, selected reviewer-working records, and the parent frozen matrix into the `src/la_grid`, `tests`, `docs`, `provenance`, and `config` layout. Path-sensitive scientific input and result directories were not moved in this phase.

- Tracked file rename records in the Git index after B1: 179.
- Python package: `src/la_grid/` with subpackages for core, revision, diagnostics, plotting, utilities, formal routines, and capacity closure.
- Import/path updates: legacy top-level imports now resolve through `la_grid.*`; one centralized `run_all.py` bootstrap points to `src/`; shared repository-root resolution is in `la_grid.paths`. No scientific function body was redesigned.
- Parent frozen matrix: moved to `config/parent_frozen_design/`; JSON SHA-256 remains `798189a92123a6f111170ffe6b620e2bd2ca710f35df33004ef1a0093efc36fe`.
- Test command: `python` was not on this Windows shell PATH; the configured interpreter `C:\Users\yinch\anaconda3\python.exe -m pytest` collected 49 tests and passed all 49.
- Canonical validation: `FINAL_REVISION_RUN_SEQUENCE/run_all.py --resume` completed with Stage 01 `PASS_VALIDATE`, Stages 02–10 `PASS_REUSE`, and `PASS_ALL_STAGES_REUSE_OR_VALIDATE`.
- `git diff --check`: PASS (exit code 0). Git emitted only configured LF-to-CRLF normalization notices.
- Scientific output diff: none. B1 changed file locations/import/path references and canonical path/identity registries only; no files under `Data/`, `Formal_Experiment_20260923/`, Stage outputs, `Manuscript_Figures/`, `Sensitivity Output_clean/`, or `External_Validation_Data/` were changed or moved.
- Protected July archive ref remains `182686868cffe962739804f6bc0ccecaed73d601`.

## Final Phase B physical reorganization validation

- Tracked file moves recorded by staged Git renames: 423.
- Git LFS audit: 472 LFS pointer files remain in the staged Git tree; 286 moved pointer files were compared old-to-new and all 286 OIDs are unchanged (0 mismatches). Details are in `LFS_MOVE_AUDIT.md`.
- Path-frozen root exceptions: `Data/` and `Formal_Experiment_20260923/`. Moving the mixed Formal archive deeper caused normal Windows Python traversal to omit deep paths; it was restored to its historical root. The canonical manifest now uses that physical authority. `run_all.py` uses extended-length paths for the relocated suite.
- Results moved: revised suite to `results/revised_suite/`, manuscript figures to `results/manuscript/figures/`, capacity outputs to `results/capacity/`, diagnostic outputs to `results/diagnostics/`; old stage outputs and submission/sensitivity bundles to `provenance/legacy_outputs/`.
- Local-only external evidence is at `Data/external_validation/` and ignored by Git. Registered trajectory/offline archives remain in the root Formal archive and are also ignored as local external archives; tracked authority files remain tracked.
- `python -m pytest`: 49 passed.
- `python FINAL_REVISION_RUN_SEQUENCE/run_all.py --resume`: Stage 01 `PASS_VALIDATE`, Stages 02–10 `PASS_REUSE`; final status `PASS_ALL_STAGES_REUSE_OR_VALIDATE`. This verifies registered archive and result hashes; it does not generate scientific output.
- `git diff --check`: PASS (exit code 0 after final path/config edits).
- Scientific output hashes changed: 0. Canonical Stage 01–10 manifests and the 575-file/558-row Revised Suite identity all validated. No sampling, scheduling, GA, clustering, analysis, or figure generation was run.
- Protected July ref remains `182686868cffe962739804f6bc0ccecaed73d601`.
