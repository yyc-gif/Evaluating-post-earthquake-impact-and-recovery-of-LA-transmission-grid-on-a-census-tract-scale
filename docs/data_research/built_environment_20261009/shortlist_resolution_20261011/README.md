# Stage7 shortlist resolution

Read FINAL_VARIABLE_RECOMMENDATION.md first: it selects CORE3 and explains all inclusion/exclusion decisions. FINAL_CANDIDATE_CONSTRUCT_DECISION.md contains the evidence and fixed-k4 limitations. DOMAIN_WEIGHT_REQUIREMENTS.md states the remaining domain-budget decision.

Measurement tables use actual validated values and exact GEOIDs. SHORTLIST_FEATURE_MATRIX.csv retains all 2,291 residential records; primary comparisons use 2,287 and the conditional age pair 2,286. FINAL_SHORTLIST_DISPOSITIONS.csv accounts for all 64 registered candidates. Source alternatives, composition dependence, coverage bounds and source-allocation stress tests are kept distinct.

BOUNDED_MODEL_COMPARISON.csv summarizes 12 eligible/conditional comparison specifications; BOUNDED_RUN_RECORDS.csv and run_records contain full seed/scaler/center/prediction records. Contingencies, profiles, class retention/purity, source coverage and ACS measurement sensitivity are separate auditable tables. The 20 deletion cases comprise 17 unique geographic sets and are not independent validation. k stays 4. No weight search or final clustering promotion occurred.

Reproduce in the verified Anaconda Python3.12.3/scikit-learn1.5.1 environment. Run common.py once for preservation; measurement_resolution.py reuses source payloads and cached attributes; additional_measurement.py supplies conditional/bounds evidence; controlled_shortlist.py reuses verified complete checkpoints; summarize_comparisons.py reuses completed coverage runs; write_decision.py generates the memos. source_lineage.py makes only a few official metadata requests. test_shortlist.py checks consequential numerical/identity invariants. Paths, byte hashes and versions are retained. No bulk GIS extraction or download was repeated.

HIST full-cohort labels are copied exactly from the original saved fits. The original full-cohort estimator centers were not saved; its exported full-cohort centers are descriptive means of the saved partition, not recovered prediction-estimator centers. The original spatial-run estimator centers are available and reused exactly. All newly fitted models retain their actual estimator centers. CENTROID_PROVENANCE_QA.csv records this distinction and nearest-center disagreements without altering any historical labels.

The prior BE0/BE1 records use historical SCAG entropy and LARIAC coverage, with or without historical age. They do not match the updated EMC/ACS specifications. The exactly matching historical D full and spatial records were reused; no other matching updated fit was found.

Formal Stage7 labels/PCA, manuscript, figures, simulations, schedules and GA are untouched. The package is an isolated research recommendation, not authorization to replace them.
