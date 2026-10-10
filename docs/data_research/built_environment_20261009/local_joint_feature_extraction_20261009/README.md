# Joint tract feature extraction for author review

Scientific baseline: 031d2c675f8e7d58035d27448be040b809ced086. Analysis reference: d5d51c6ad1659c82c3b6717ab14a31f3e5cd78c7. These are candidate measurements and descriptive redundancy evidence; no final variable selection or clustering was performed.

- TRACT_FEATURE_CANDIDATES.csv: all 2,315 tracts with GEOID11, nulls and source/coverage flags.
- RESIDENTIAL_2291_FEATURE_MATRIX.csv: the exact saved 2,291 residential members.
- FEATURE_CORRELATION_MATRIX.csv: 1,081 Pearson/Spearman comparisons, each with actual N, missingness and a hash of its matched tract set. Log alternatives are diagnostic.
- FEATURE_VIF.csv and FEATURE_CONDITIONAL_REDUNDANCY.csv: explicit complete-case samples, controls and composition constraints; no indicator is selected.
- FEATURE_COVERAGE_QA.csv and FEATURE_DEFINITIONS.csv: source, vintage, units, completeness and reliability.
- RECOVERY_METRIC_QA.md: exact B/T80/initial-service definitions, horizon and reconstruction checks.
- BUILT_ENVIRONMENT_SOURCE_AND_GEOMETRY_AUDIT.md, BUILDING_AGE_COMPLETENESS_AND_SENSITIVITY.md and R2D_BRAILS_INVENTORY_AUDIT.md: actual source scope and limitations.
- INPUT_SOURCE_HASHES.json, SOURCE_CACHE_MANIFEST.csv, REMOVED_TEMPORARY_CACHE_MANIFEST.csv and PRESERVATION_FINAL_QA.json: traceability and preservation.

| dataset | actual completion status |
|---|---|
| B/T80/initial service | Same 1,000 saved formal realizations; all 2,315 values verified |
| SCAG 2019 | All 2,406,373 LA records processed; median classified land coverage 75.1%; ambiguous area and gaps retained |
| LARIAC 2020 | Observed union footprints, centroid counts and positive heights extracted; release contains earlier imagery |
| Original 2014 building age | Separately dated all-use candidate; median valid-age area coverage 95.2%, not complete all-building age |
| Age transferred to 2020 | Strict ID/geometry linkage; median valid-age area coverage 4.4%; unsuitable for a complete all-use interpretation |
| R2D/BRAILS | 884-record school portfolios only; not a representative county structural inventory |
| Pure tract PGA | Original official geographical field verified; 2,294 primary values after support/land-mask checks, partial diagnostics retained |
| Imperviousness | Existing numeric pilot retained; direct USGS source/version correspondence unverified |

B is mean normalized service deficit integrated over 0-480 h. T80 crosses 0.8 on the mean service trajectory, not the mean of realization T80. On the exact residential subset, B/T80 Pearson = 0.912150 and Spearman = 0.929190. AUC_480 = 1 - B/480 is an exact complement. None of these findings selects an outcome or transform.

Use the installed Anaconda Python. Scripts resolve repository paths from this directory. Original scientific files are read only. This extraction uses original sources, not new damage, scheduling, GA or clustering.

For a fresh source extraction, the order is source_audit.py probe; acquire_sources.py; acquire_scag.py; extract_gis.py land; extract_gis.py lariac; extract_height.py; extract_age.py; extract_age2014_original.py; audit_age2014_cache_complete.py; audit_union_area_equivalence.py; extract_hazard.py; extract_scag.py; extract_recovery.py; assemble_features.py; finalize_audit.py. audit_r2d.py documents local inventories. Reuse existing sources rather than downloading again. When reusing the complete 2014 geometry cache, invoke extract_age2014_original.py --resume-cache. The source snapshot intentionally records entry-state protection; do not overwrite it after starting work. publish_research_branch.py is for this task's scoped branch, not a general-purpose publishing command.

Large original archives and SCAG response geometries remain local with hashes. Completed temporary overlay caches were removed after hash recording to recover disk space; they can be reconstructed from retained original sources. Partial checkpoint tables remain local and are not proposed data products. The branch contains validated tables, scripts, metadata and audits.

See REMAINING_BLOCKERS.md before feature selection. Undefined housing age is null; government building ages are not imputed. No existing figure, manuscript, stored cluster, formal GA result or restoration archive was changed.
