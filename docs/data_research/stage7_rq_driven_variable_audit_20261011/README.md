# Final three-RQ Stage 7 variable audit (2026-10-11)

Isolated diagnostic package. No scientific baseline, formal Stage 7 output, manuscript, figure, sample, schedule or previous diagnostic is modified. No clustering/weighted feature matrix is fitted. Primary decisions remain proposals for author approval.

## Start here

- `PROPOSED_FEATURE_AND_WEIGHT_DECISION.md`: concise feature/construct/cohort/budget decision and unresolved actions.
- `THREE_RQ_CANDIDATE_REGISTER.csv`: definitions, provenance, coverage, same-residential-cohort distributions, zeros/extremes and dispositions.
- `RQ3_ROUTE_A_SOCIAL_AND_POPULATION_AUDIT.md`: single SVI, population and optional heating evidence.
- `RQ2_2PC50_HAZARD_AND_POLICY_PROVENANCE.md`: original PGA, exact metric/policy/sample/censoring identity.
- `RQ1_GRID_METRIC_REDUNDANCY.csv`, `RQ2_RECOVERY_METRIC_REDUNDANCY.csv`, `CROSS_DOMAIN_INFORMATION_AUDIT.csv`: pairwise linear/rank/nonlinear evidence.
- `CONDITIONAL_EXPLAINED_VARIANCE_AND_VIF.csv`: conditional explained variance and VIF; identity blocks intentionally singular.
- `TRACT_COHORT_AND_MISSINGNESS.csv`, `MISSING_VALUE_LEDGER.csv`: every exact GEOID and exclusion/missing reason; no hidden four-geometry filter.
- `SVI_COMPOSITE_SOURCE_COMPARISON.csv`: earlier harmonization results reproduced, frozen Q groups not changed.
- `SOURCE_HASH_VERIFICATION.csv`, `FROZEN_REALIZATION_VERIFICATION.csv`, `INDEPENDENT_THREE_POLICY_ARCHIVE_VERIFICATION.csv`: actual payload provenance, not LFS pointer-only checks.
- `PRESERVATION_BEFORE.json` and `PRESERVATION_AFTER.json`: identical protected universe of 950 prior files.

## Reproduction

Python 3.12.3; isolated statistical dependencies are pinned in `requirements-audit.txt`, not installed or changed automatically. Get Git LFS payloads. Main Git baseline and separate heating-package commit are fixed in `AUDIT_SPECIFICATION.json`. Worktree checkout can be sparse; `--cache-root` searches additional actual-source checkouts or the shared LFS object store and admits only committed hashes (text CRLF-only equivalence explicitly recorded).

From this directory:

```powershell
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python audit.py --source-root 'PATH_TO_AUTHORITATIVE_FROZEN_ARCHIVE' --cache-root 'PATH_TO_HEATING_COMMIT_CHECKOUT' --comments 'PATH_TO_ORIGINAL_COMMENTS_DOCX'
python write_reports.py
python verify_independently.py --source-root 'PATH_TO_AUTHORITATIVE_FROZEN_ARCHIVE'
python validate_package.py
```

Audit.py performs source metric reconstruction and regression diagnostics only, not model simulation. Original comments are optional for numerical reconstruction; report generation expects the retained source quote record if that optional file is not accessible. The source archive must include the frozen offline integral arrays and 1,000 existing event records per policy. Those bulk files are not all Git-tracked: a clean clone alone cannot reproduce their source-level verification. Existing package CSVs allow independent numerical/association tests without that archive. No new raw medical-need data or current-year population is invented.

Independent verification uses separate archive integration/identity code, checks all 3,000 event payloads and reproduces conditional linear R-squared separately. `validate_package.py` runs package-only compileall (Windows extended paths where needed), pytest and a changed-path scope check, then records the commands and derived payload hashes. The tests check cohort identity, missingness, exact recovery identities, source comparisons, censoring semantics, no clustering imports and protected hashes. The source comments document is not copied into this package.

Distributions use valid individual values on the declared 2,291 residential cohort; primary and extended correlation matrices both use the same complete 2,291 GEOIDs. Zero/near-zero fraction and |z|>3 flags are descriptive only. Non-estimable construct-level exclusions have blank numeric statistics rather than invented zero values. An infinite VIF in the deliberately included arithmetic identity block is expected, not a model defect. Source qualification and construct admission are different decisions.
