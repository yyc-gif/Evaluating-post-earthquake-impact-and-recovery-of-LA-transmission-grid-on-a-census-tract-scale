# Final revised-paper workflow

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
| 08 | `08_FINAL_STAGE7_TYPOLOGY/run_08_stage7_typology.py` | Validate the harmonized Stage 7 authority and its saved products | PASS_REUSE |
| 09 | `09_CAPACITY_ROBUSTNESS/run_09_capacity_robustness.py` | Validate the closed SCE-supported capacity sensitivity outputs | PASS_REUSE |
| 10 | `10_FINAL_RESULTS_AND_FIGURES/run_10_final_outputs.py` | Validate the revised suite archive and complete figure review collection | PASS_REUSE |

Each stage entrypoint calls the same `stage_runner.py` implementation used by `run_all.py`. Every entrypoint requires `--resume` and fails if a prerequisite manifest or frozen artifact is missing; no stage wrapper falls back to scientific computation.

The complete figure review collection is `results/figures/` (open `FIGURE_REVIEW_GALLERY.html`; no manuscript figure selection has been made). Scientific implementation is in `src/la_grid/`; numerical result collections and archive pointers are under `results/`. Large local/external archives are listed in `EXTERNAL_ARCHIVE_MANIFEST.json`.
