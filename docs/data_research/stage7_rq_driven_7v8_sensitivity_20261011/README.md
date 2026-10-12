# Registered Stage 7 seven/eight-variable exploration

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** Only this isolated package is new. No formal model, parameter, trajectory, manuscript, original figure or previous audit is changed. Author decides the candidate; this is not a new official typology.

Start with `SEVEN_VS_EIGHT_VARIABLE_DECISION.md`, then the cohort, source and initial-service reports. `FEATURE_SPECIFICATIONS_AND_WEIGHTS.json` was written before fitting and fixes both cohorts, all budgets, k3-6, five seeds, n_init50 and the separate tail/spatial stress tests. The eight-variable extension and initial ablations also reallocate internal domain budgets; differences are not pure coordinate-addition/removal effects.

## Reproduction

Python 3.12; versions recorded in `ANALYSIS_EXECUTION.json` and `requirements-diagnostics.txt`. Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to 1 for the registered replay. Run inside this package:

```text
python prepare.py --source-root <frozen-research-worktree> --cache-root <verified-data-worktree>
python analyze.py
python verify_independently.py
python write_reports.py
python make_plots.py
python verify_package.py
```

After `make_plots.py`, inspect all five PDF pages using the publication-size review renders. Only after this visual inspection, set `visual_review_status` in `PDF_RENDER_AND_BOUNDARY_QA.json` to `PASS_ALL_FIVE_PDFS_AT_PUBLICATION_SIZE` before the final package check. This is a manual visual-QA attestation, not an automatic claim. The heatmap color scale is clipped at +/-2 standard deviations for display only; cell annotations retain the actual, unclipped means.

For a deterministic numerical replay, run `python verify_package.py --capture-replay`, rerun `python analyze.py`, then run `python verify_package.py --verify-replay`. The archived replay comparison checks 18 numerical CSVs byte-for-byte; PDF metadata timestamps and elapsed-time records are not expected to be byte-identical.

For a Git/LFS clone containing this and the prior audit, `analyze.py` reproduces statistical diagnostics and exploratory fits directly from `TRACT_FEATURES_VERIFIED_2315.csv`. Source-level `prepare.py` and independent archive rechecks additionally require the original manifest-bound local frozen integral archives, which are not all published in Git. Do not substitute new trajectories. The pinned prior audit's source verifier is reused only for byte verification; no scientific model module is imported.

## Outputs

- `TRACT_COHORT_AND_EXCLUSIONS.csv`: all 2,315 exact identities and explicit admission reasons.
- `CLUSTER_MEMBERSHIPS_*.csv`: all 100 registered diagnostic label columns per cohort.
- `REGISTERED_EXPLORATORY_CLUSTERING.csv`: 200 fit records, no selected winner.
- `CLUSTER_PROFILE_DISTRIBUTIONS.csv`: actual/transformed units, moments, percentiles, extrema for every fit/cluster.
- `DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv`: declared squared-distance budgets and empirical total/within/between SS.
- `CLUSTER_LEVEL_COORDINATE_SEPARATION.csv`: coordinate shares of each cluster centroid's separation.
- `CLUSTER_MEMBERSHIP_COMPARISONS.csv`, transitions and `COHORT_SENSITIVITY.csv`: label-invariant and matched-label comparisons, never selection targets.
- `SPATIAL_AND_SEED_STABILITY.csv`: 400 seed-pair rows plus 120 tail/spatial stress comparisons. `STRESS_TEST_MEMBERSHIPS.csv` preserves all predictions and heldout flags.
- `BUILDVALUE_INCREMENTAL_INFORMATION.csv`, association/VIF files, distributions and source hashes: construct and source audit.
- `INDEPENDENT_QA_RESULTS.json`: independent source projections, 10 full replays, 200 distance checks, 950 protected-file preservation and prior-audit immutability.
- `figures/`: five Matplotlib PDF/PNG diagnostic figures with actual-size review renders; no AI-generated artwork. All k4 illustrations are predeclared display examples, not a chosen formal k.

`B_480_hr` is mean normalized full-service-deficit hours over 480 h under fixed Impact-first/C57_D1/M1/G1 and 1,000 existing realizations. DeltaB is paired constrained-minus-Unconstrained deficit. T80 is descriptive; no mean trajectory is unreached here. BUILDVALUE is 2022 USD building stock, not outage damage. Original vulnerability quartiles and group-level strategy outcomes remain authoritative.
