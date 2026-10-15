# Final revised-paper workflow

Current branch: `publication/p2-seven-variable`. Stage 08 now uses the adopted seven-variable P2/K3 authority in `results/stage7/P2_K3_2299/`; K4 is sensitivity only. The current figure suite has 17 numbered figures and a 21-page concise packet. Full-workflow validation still requires the original manifest-bound external archives; this consolidation does not newly certify an empty-machine physical rerun.

The historical PASS rows below refer to the previously frozen workflow. This consolidation rechecks the current P2 Stage 08 and figure authority, not a new full physical run. `FINAL_RUN_MANIFEST.json` makes that distinction explicit and points to the original full-run record in Git history.

Run the authoritative validation/reuse path:

```bash
python FINAL_REVISION_RUN_SEQUENCE/run_all.py --resume
```

`--resume` is the currently certified mode. `--from-scratch` is **NOT YET CERTIFIED**.

| Stage | Entrypoint | Purpose | Status |
|---|---|---|---|
| 01 | `01_VALIDATE_INPUTS/run_01_validate.py` | Verify frozen configuration, input identities, code authority and protected archive identity | PASS_VALIDATE |
| 02 | `02_MAPPING_AND_PHYSICAL_SAMPLES/run_02_mapping_and_physical.py` | Validate and reuse the production mapping and frozen physical/planning samples | PASS_REUSE |
| 03 | `03_GA_AND_STRATEGY_FREEZE/run_03_strategy_freeze.py` | Validate frozen rule sequences, GA provenance, incumbent and final strategy registry | PASS_REUSE |
| 04 | `04_SCHEDULE_AND_TRAJECTORIES/run_04_trajectories.py` | Validate and reuse the frozen formal and Vulnerability-first event archives | PASS_REUSE |
| 05 | `05_SERVICE_AND_TRACT_EVALUATION/run_05_service_evaluation.py` | Validate frozen offline evaluations and accepted service/distribution results | PASS_REUSE |
| 06 | `06_SOURCE_AND_NETWORK_DIAGNOSTICS/run_06_source_network_diagnostics.py` | Validate retained source-connectivity and dynamic network diagnostic outputs | PASS_REUSE |
| 07 | `07_DISTRIBUTIONAL_AND_VULNERABILITY/run_07_distributional_vulnerability.py` | Validate final Q1–Q4 and vulnerability-targeting results | PASS_REUSE |
| 08 | `08_FINAL_STAGE7_TYPOLOGY/run_08_stage7_typology.py` | Validate the adopted seven-variable P2/K3 authority; no fitting | Saved reuse |
| 09 | `09_CAPACITY_ROBUSTNESS/run_09_capacity_robustness.py` | Validate the closed SCE-supported capacity sensitivity outputs | PASS_REUSE |
| 10 | `10_FINAL_RESULTS_AND_FIGURES/run_10_final_outputs.py` | Validate the current P2 figures, exact mirrors and packet | Saved reuse |

Each stage entrypoint calls the same `stage_runner.py` implementation used by `run_all.py`. Every entrypoint requires `--resume` and fails if a prerequisite manifest or frozen artifact is missing; no stage wrapper falls back to scientific computation.

The complete adopted figure collection is `results/figures/` (open `FIGURE_REVIEW_GALLERY.html`); its authoritative artwork and captions are in `results/figure_review/`. Scientific implementation is in `src/la_grid/`; numerical result collections and archive pointers are under `results/`. Large local/external archives are listed in `EXTERNAL_ARCHIVE_MANIFEST.json`.
