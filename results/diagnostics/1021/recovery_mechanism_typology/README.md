# Recovery-mechanism exploration,1021

Start with `SCIENTIFIC_DECISION.md`; manuscript implications are proposed only
in `MANUSCRIPT_IMPACT.md`. `PROTOCOL.md` was committed and pushed before new
feature extraction or fitting. No official publication artifact is modified.

## Figures

1. `01_ACTUAL_RECOVERY_TRAJECTORIES.pdf`: exact mean event-step availability;
   K2/K3 illustrate the parsimonious split and addition of a third group in
   each representation. Main axes show0-96h; insets retain the full480h horizon.
   Group numbers/colors are local to each fit, not formal P2 classes. These
   training curves describe fitted groups and are not validation.
2. `02_RESOURCE_AND_WITHHELD_RESPONSES.pdf`: equal-tract class mean total deficit
   under29,57 and114 crews, all Impact-first. Open57-crew markers identify the
   reference condition; filled29/114 markers are unused resource conditions.
   Connecting lines link experimental conditions, not time trajectories.
   Bottom panels show held-out tract MAE averaged equally over the registered
   70%/85% draws; continuous curves are prespecified additive models, not
   groupings. All seven unused-context endpoints and three contrasts are in CSV.
3. `03_VULNERABILITY_AND_REPRODUCIBILITY.pdf`: unsmoothed SOVI ECDFs; mean full-
   cohort membership ARI for random/spatial refits; incremental SOVI prediction
   from adding class indicators to continuous recovery plus a fixed geographic
   basis. The dotted2-point line is a preregistered reporting convention, not
   a significance threshold. Social context is descriptive, not outage validation.

All plots are isolated diagnostics. Full K1..6 results are retained; showing
K2/K3 response curves is not selection of K3. Ward and K4..6 disagreement is
reported rather than hidden. PNG exports and actual-PDF renders are provided.

## Evidence map

- Inputs: `FROZEN_INPUT_REGISTRY.json`, `FROZEN_SOURCE_HASHES.csv`,
  `FEATURE_EXTRACTION_QA.json`, `EVENT_INTEGRAL_QA.csv`.
- Exact derived response data: `RECOVERY_MATRICES.npz`, `RECOVERY_FEATURES.csv`,
  `PLOTTED_EXACT_CLASS_MEAN_CURVES.csv`, `CONTEXT_AND_SPATIAL_BLOCKS.csv`.
- All labels/centers/preprocessing/train indices: `ALL_FITTED_ARRAYS.npz`;
  convenient reference assignments: `TRACT_CLASSIFICATIONS.csv`.
- Separation and algorithms: `FULL_FIT_RESULTS.csv`, `PER_CLUSTER_SILHOUETTE.csv`,
  `K_EVIDENCE_SUMMARY.csv`, `ALGORITHM_SEED_AND_P2_AGREEMENT.csv`.
- Membership/profile robustness: `RESAMPLING_MEMBERSHIP.csv`, `CLUSTER_JACCARD.csv`,
  `MEMBERSHIP_STABILITY_SUMMARY.csv`, `CLUSTER_STABILITY_SUMMARY.csv`,
  `MEMBERSHIP_CORES.csv`, `RECOVERY_SHAPE_RESAMPLING.csv`,
  `RESAMPLED_OUTCOME_PROFILE_SHIFTS.csv`.
- Withheld evidence: `HELD_OUT_ENGINEERING_SCORES.csv`, `ENGINEERING_SCORE_SUMMARY.csv`,
  `PAIRED_BENCHMARK_COMPARISONS.csv`, `WITHHELD_CONTRAST_PERSISTENCE.csv`,
  `CONTRAST_PERSISTENCE_SUMMARY.csv`, `QUANTILE_BENCHMARK_CUTS.csv`.
- Interpretation: `ORIGINAL_UNIT_PROFILES.csv`, `CROSS_K_MEMBERSHIP.csv`,
  `REFERENCE_PARTITION_COMPARISONS.csv`, `CROSS_REPRESENTATION_SHARED_SUBSET_PROFILES.csv`,
  `COORDINATE_DISTANCE_CONTRIBUTIONS.csv`, `B_INITIAL_COORDINATE_ALGEBRA.csv`,
  `Q_SOURCE_PROXY_OVERLAP.csv`, `MECHANISM_AND_CONTEXT_ASSOCIATIONS.csv`,
  `SOCIAL_AND_GEOGRAPHIC_CONTEXT.csv`, `SOCIAL_CONTEXT_INCREMENTAL_SCORES.csv`,
  `SOCIAL_CONTEXT_SCORE_SUMMARY.csv`, `TRAJECTORY_PCA_LOADINGS.csv`.
- QA/delivery: `INDEPENDENT_QA.json`, `TEST_RESULTS.json`, `tests.xml`,
  `PDF_STRUCTURE_QA.json`, `VISUAL_QA.md`, `PACKAGE_HASHES.json`,
  `REMOTE_DELIVERY_VERIFICATION.json`.

## Reproduction

Use Python3.12 with the repository environment and the versions recorded in
`TEST_RESULTS.json`. Set BLAS threads to1 (analysis scripts do this themselves).
Run from the repository root, with `$D` equal to this experiment directory:

```powershell
$D = 'results/diagnostics/1021/recovery_mechanism_typology'
python "$D/extract_features.py"
python "$D/analyze_recovery.py"
python "$D/summarize_evidence.py"
python "$D/plot_recovery.py"
python "$D/verify_recovery.py"
python -m pytest "$D/test_recovery.py" -q
```

`register_sources.py` is the original pre-experiment check, bound to the starting
commit; do not overwrite its registry on replay. Extracting features requires
the original manifest-bound local event/integral archive, configured through
`LA_GRID_FROZEN_SOURCE_ROOT`. There is no fallback physical regeneration.
Later steps reuse delivered derived matrices and the unchanged prior1021
engineering package. Actual LFS payloads must be downloaded, not pointer files.

Sparse worktrees require `git add --sparse` for delivery. No external provider
was contacted. The hospital table needed a targeted LFS retrieval; a Windows
long-cache-path fallback is confined to `support.py`, not historical helpers.
Algebraic PCA checks allow1e-14 rounding from alternate centering order; saved
labels and deterministic fitted reconstructions are checked exactly.
