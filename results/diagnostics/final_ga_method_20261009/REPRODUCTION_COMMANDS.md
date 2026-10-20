# Reproducing the completed diagnostics

Use the recorded Python/NumPy/Numba environment, set PYTHONPATH to src, and set OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to 1. Verify FREEZE_RECEIPT.json and source/input hashes before execution.

The completed bounded attribution comparisons can be regenerated with:

`python -m la_grid.diagnostics.final_ga_method_20261009`

Existing verified RUN.json files are reused. This command executes only the two missing configurations recorded in CONTROLLED_COMPARISON_DESIGN.json, five seeds each, using saved planning inputs. It does not generate physical samples or change formal results.

The report and exact method/sequence/validation freeze can be regenerated from those results with:

`python -m la_grid.diagnostics.final_ga_method_report_20261009`

This reconstructs schedules only for the three saved planning candidates to compare equivalence, and derives tables and documents. It does not launch another GA search or draw physical samples.

For a fresh reproduction of the recommended search, construct Variant from FINAL_GA_CONFIG_CANDIDATE.json and call the pinned ga_variant_engine.run_search with the same ordered station IDs, seven incumbent sequences, prior-best quality sequence, kernel.score and seeds. Stage A uses 100000 distinct queries per seed 42-61. Retain its resume checkpoint; Stage B calls the same function and folder for fixed seeds 42-46 with max_evaluations=500000. The cache and RNG must continue. Checkpoints are 50000/100000/250000/500000; report actual generation counts. A from-scratch 500000 run is a deterministic replay, with extra prefix costs disclosed, not a cost-free continuation. Do not pass a generation stop or reuse objective lookups as free calls.

No executor for new physical validation is launched by either command. The independent validation plan requires separate author approval.
