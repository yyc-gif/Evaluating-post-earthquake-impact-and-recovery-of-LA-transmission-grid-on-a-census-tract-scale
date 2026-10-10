# Built-Environment Validation, 2026-10-09

**Decision: B for the present manuscript; A remains conditional.** Retain housing age and add the share of housing units in structures with 5+ units to descriptions of the existing clusters. Numeric NLCD extraction succeeded, but its public mirror has a beta/non-production notice. It is not an approved final manuscript input yet. No clusters, manuscript text, figures, restoration simulations or GA outputs were changed.

This package extends, and where stated corrects, the five earlier documents in the parent directory. Those earlier files remain historical snapshots. In particular, their A/B/C definitions differ from the new request: here A = age + configuration + imperviousness; B = age + configuration; C = current descriptions only. Their provisional NLCD Collection 1.2 recommendation was **not** the raster version actually retrieved here.

## Read First

- `ACS_UNCERTAINTY_AND_SENSITIVITY.md`: actual replicate-based uncertainty, cluster contrasts and screening bias.
- `NLCD_EXTRACTION_AND_VERIFICATION.md`: numeric extraction, water/boundary checks and remaining provenance gate.
- `FEATURE_REDUNDANCY.md`: correlations, effect sizes and limits of incremental interpretation.
- `STAGE7_RECOMMENDATION.md`: READY/CONDITIONAL/EXCLUDE decisions and release criteria.
- `PROPOSED_MANUSCRIPT_LANGUAGE.md`: separate draft language, not edits to the manuscript.
- `EXECUTION_LOG.md`, `PACKAGE_MANIFEST.json`, `REPRODUCTION_CHECK.json`: execution, retained-file hashes and independent offline repeat evidence.
- `BUILT_ENVIRONMENT_DATA_SOURCE_AUDIT.csv` and `BUILT_ENVIRONMENT_TRACT_COVERAGE.csv`: updated source and 2,315-tract accounting.
- `CLUSTER_COMPARISONS.csv`, `CLUSTER_PAIRWISE_EFFECTS.csv`, `CLUSTER_EFFECT_SIZES.csv`, `ACS_SCREENING_BIAS.csv`, `ACS_PRECISION_WEIGHTING.csv`: numeric results. Fractions are 0-1; multiply by 100 for percentages/percentage points. Quantiles describe tract heterogeneity, not confidence intervals.
- `INDICATOR_CORRELATIONS.csv`, `INDICATOR_CORRELATION_SENSITIVITY.csv`, `INDICATOR_INCREMENTAL_INFORMATION.csv`, `RESIDENTIAL_VALIDATION_MATRIX.csv`: reproducible descriptive comparisons, not a new clustering matrix.

## Reproduction

Use Python 3.12 with the versions in `requirements.txt`. Run in a separate copy of this validation directory so new audit results do not overwrite the archived evidence. Set `REPO` to the actual Git checkout, not the older IDE directory. Source geometries and labels remain in the checkout; their paths/hashes are recorded in the preservation baseline and input manifest.

```powershell
$REPO = 'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision'
python validate.py --repo "$REPO" --phase acs
python nlcd.py --repo "$REPO" --phase aggregate
python validate.py --repo "$REPO" --phase compare
python qa.py --repo "$REPO"
```

These steps use retained Census ZIPs and numeric raster clips, require no network, and never invoke the scientific pipeline. Temporary `_*.npz`, `_*.tif` and LA-wide replicate CSV caches are regenerated and are not research deliverables. `validate.py --phase baseline` is deliberately restricted to the stated starting HEAD `dab9761`; reproducing the calculations does not require creating a new preservation baseline.

Alternatively, `python reproduce.py --repo "$REPO" --out "PATH_TO_NEW_DIRECTORY"` performs all four phases in a fresh directory, checks the existing input hashes before/after, and requires byte-identical outputs for 18 result files. `REPRODUCTION_CHECK.json` records the completed test. The offline authoritative-file route was also self-tested with the pilot clips: 2,315 differences were exactly zero. This tests the route, **not** independent USGS provenance.

Optional acquisition: `python acquire.py --phase sources` retrieves original Census files/documentation; `python nlcd.py --repo "$REPO" --phase mirror` re-downloads the version-checked numeric mirror; `--phase repeat` checks a fresh subwindow against the clip. Live services may change. Retained bytes plus SHA-256 manifests define this audit's reproducible snapshot, not perpetual service availability. `probe.py` records the failed official WCS alternatives. See the NLCD document for the authoritative-file acquisition route required before publication.

## Preservation

Starting HEAD: `dab976173dcb5da7fdbd4a2c91d879317a797331`, branch `revision/reviewer-driven-core-rebuild-v2`. The original 212 protected files, all original audit files and the pre-existing staged-change digest are checked separately. Only this new `validation/` package is included in its commit. Labels are held unchanged for the analysis; this is **not** a claim that Stage 7 is scientifically final or beyond further review.
