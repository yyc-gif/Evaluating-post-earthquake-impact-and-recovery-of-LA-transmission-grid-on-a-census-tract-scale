# GA and ILS Parameter Defense

Start with [FINAL_RESEARCH_DECISION.md](FINAL_RESEARCH_DECISION.md). This package is an isolated postvalidation methodological audit, not a replacement of the formal GA strategy or physical model.

## Reports

- [GA parameter defense](GA_PARAMETER_DEFENSIBILITY_REPORT.md)
- [ILS parameter defense](ILS_PARAMETER_DEFENSIBILITY_REPORT.md)
- [Method-choice decision](GA_ILS_METHOD_CHOICE_DECISION.md)
- [Seventeen reviewer questions](REVIEWER_OBJECTIONS_AND_EVIDENCE.md)
- [Methods and Supplement text](METHODS_AND_SUPPLEMENT_READY_TEXT.md)

## Evidence

`EXPERIMENT_INVENTORY.csv` reconciles historical and new runs, continued stages and deterministic references. Parameter matrices distinguish design support from an exact optimum. Controlled-results, paired-contrast and seed-difference tables retain unsuccessful and incomplete cases as well as favorable results. `IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json` contains complete verified 92-station orders and their planning-state influence; none is promoted.

`EXPERIMENT_DESIGN_AND_SEEDS.json`, `PARAMETER_SELECTION_REGISTER.json` and the pre-execution commits document the design. `EXECUTION_ACCOUNTING.json` separates new expensive scores, cache hits, attempted queries, deterministic refinement, cached-prefix replay, setup and production checks.

## Retrieval and Verification

Run `git lfs pull` after checkout. The ZIP preserves all raw search histories, initializer fingerprints, final permutations, refinement checkpoints and GA prefix caches without duplicate uncompressed storage in Git. Verify its SHA-256 and members against `RAW_EVIDENCE_ARCHIVE_MANIFEST.json` before extraction. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for reanalysis commands and path-safety rules.

`REPRODUCIBILITY_AND_PRESERVATION_QA.json` discloses tests, numerical and visual checks, including the historical Windows line-ending hash exception. `REMOTE_PUBLICATION_VERIFIED.json` records actual downloaded remote LFS hashes and the data commit. Original revision staging, protected scientific files, physical samples, formal strategies, manuscript and artwork are unchanged.
