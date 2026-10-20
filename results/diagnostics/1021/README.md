# 1021 independent clustering validation

Start with [SCIENTIFIC_DECISION.md](SCIENTIFIC_DECISION.md) and the separate
[MANUSCRIPT_IMPACT.md](MANUSCRIPT_IMPACT.md). Nothing here replaces the October
14 publication, memberships, figures or manuscript.

## Reproduce

Python 3.12. The exact analysis environment is recorded in outputs/RUN_MANIFEST.json;
additional installed plotting/test versions are in IMPLEMENTATION_QA.json.
No external physical-simulation archive is needed for this matrix-level task.
The unchanged upstream matrices and geography are tracked Git LFS payloads.

```powershell
python -m pip install -r results/diagnostics/1021/requirements-validation.txt
git lfs pull --include="results/stage7/2026-10-14/*,results/diagnostics/1021/*"
python -m pytest results/diagnostics/1021/test_validation.py -q
python results/diagnostics/1021/validate.py
python results/diagnostics/1021/summarize.py
python results/diagnostics/1021/independent_qa.py --portable
```

For an economical clean clone, use GIT_LFS_SKIP_SMUDGE=1, clone the explicit
branch `refs/heads/1021`, sparse-checkout these two directories, then pull only
their LFS files. There is also a historical tag named 1021, so use explicit
`refs/heads/1021` in Git delivery commands to avoid refname ambiguity.

Use `independent_qa.py` WITHOUT --portable only on the original machine with
the preserved `_final_p2` worktree and 950-file research archive. Portable mode
verifies all numerical outputs and tracked-file scope, but explicitly does not
claim to inspect an unavailable external worktree/archive. Do not rerun
preflight.py in a clean clone to overwrite the historical input registry.

The registered scripts freeze full-cohort preprocessing, even in split tests;
results are conditional on this supplied geometry, not a pipeline that learns
new preprocessing from each training split. They do not run the physical model.

## Output guide

- PROTOCOL.md: pushed before experiments; BASELINE_STATE_NOTE.md: external,
  byte-identical packet rename noticed after the initial clean check.
- FROZEN_INPUT_REGISTRY.json: exact input/source/index identities and GEOIDs hash.
- outputs/ALL_FITTED_ARRAYS.npz: full labels/centers, all resampling indices,
  null-fit labels, Ward tree, silhouettes and geographic holdout predictions.
- outputs/GAP_*: 1,024 individual null fits and both registered one-SE summaries.
- outputs/PREDICTION_STRENGTH_*: directions, cluster pair numerators/denominators,
  bidirectional summaries and weakest-class/rare-set support diagnostics.
- outputs/BOOTSTRAP_*: all unique-in-bag and separately all-tract-prediction
  Jaccards, dissolution and recovery frequencies; 100 replicates for each K2-6.
- outputs/OBSERVED_INDICES.csv, PER_CLUSTER_SILHOUETTE.csv and
  CONVENTIONAL_INDEX_SUMMARY.csv: all K1-8/seeds and defined internal indices.
- outputs/ORIGINAL_UNIT_PROFILES.csv: means/medians/ranges, counts, population,
  quartile composition and special-use representation. Recovery is in equivalent
  full-service-deficit hours; Init is availability fraction, SOVI is 0-100,
  spectral impact and HHI are dimensionless, log population is natural log1p.
- outputs/HISTORICAL_K4_37_TRACTS.csv: exact historical rare-set GEOIDs.
- outputs/REFERENCE_FIT_REGISTRY.csv: minimum-WCSS seed per K. Numeric labels
  are local to each diagnostic fit and not official class IDs or color registry.
- outputs/WARD_COMPARISONS.csv, INIT_COORDINATE_PROJECTION.csv and
  SPATIAL_LEAVE_QUADRANT_OUT.csv: registered algorithm/feature/geographic tests.
- outputs/PRIOR_POLICY_SET_STABILITY.csv: unchanged prior sensitivity evidence;
  filter comparison=policy_set and distinguish cohort versus fixed scaling.
  Other rows are archived prior ablation/feature comparisons, not new fits.

The pilot used two references/splits/bootstrap replicates and is not evidence
for the final conclusions; pilot/ is ignored. Full results are separately
marked FULL_REGISTERED_ANALYSIS. An exact replay repeats the same seeds/draws,
not extra independent repetitions. REPLAY_QA.json documents byte comparison.

## Figures

01_RESOLUTION_EVIDENCE: Gap (bars are one-SE-rule simulation spread, not MCSE),
prediction strength (bands P10-P90 across splits, not confidence intervals),
mean silhouette across five seeds, and minimum-WCSS inertia.

02_REPRODUCIBILITY_AND_SENSITIVITY: cluster-wise bootstrap mean/P10-P90;
four held-out quadrant ARIs; Ward agreement and minimum initialization ARI;
historical rare-set full-prediction match (band is min-max) versus Init projection.

03_WITHIN_CLASS_OVERLAP: selected original-unit ECDFs for diagnostic K3/K4,
unweighted by residents and unsmoothed. This is in-sample description, not
external validation. Different rows have different model-specific IDs.

All three PDFs are vector, 7.2 inches wide; previews are provided. These are
independent diagnostics, not numbered publication figures. Native-size visual
checks and PDF structure are documented in VISUAL_QA.md/PDF_STRUCTURE_QA.json.

## Source and delivery limits

The integrated baseline is b307e6de, not the older 937fa2b1 review. Scientific
input lineage also records the original 81c3452e saved P2 fits. Original
trajectories were not reintegrated or reverified from 1,000 physical realizations:
the target is validation of the frozen, already-audited feature space.
Thread-limited floating-point arithmetic is needed for exact PCA draw hashes.
Different BLAS/platform versions may differ numerically; pin the recorded
environment for byte-level replay. Runtime is hardware-dependent; this
machine's full registered analysis took about four minutes per execution.

Statistical definitions and primary references are in PROTOCOL.md. There is
no new weighted decision score, new physical simulation, formal promotion or
merge. Remote delivery is independently checked using a fresh LFS object store.
