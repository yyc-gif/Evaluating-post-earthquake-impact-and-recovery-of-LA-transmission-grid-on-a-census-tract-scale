# Stage7 shortlist resolution

Read FINAL_VARIABLE_RECOMMENDATION.md first: it selects CORE3 and explains all inclusion/exclusion decisions. FINAL_CANDIDATE_CONSTRUCT_DECISION.md contains the evidence and fixed-k4 limitations. DOMAIN_WEIGHT_REQUIREMENTS.md states the remaining domain-budget decision.

Measurement tables use actual validated values and exact GEOIDs. SHORTLIST_FEATURE_MATRIX.csv retains all2,291 residential records; primary comparisons use2,287 and the conditional age pair2,286. FINAL_SHORTLIST_DISPOSITIONS.csv accounts for all64 registered candidates. Source alternatives, composition dependence, coverage bounds and source-allocation stress tests are kept distinct.

BOUNDED_MODEL_COMPARISON.csv summarizes12 eligible/conditional comparison specifications; BOUNDED_RUN_RECORDS.csv and run_records contain full seed/scaler/center/prediction records. Contingencies, profiles, class retention/purity, source coverage and ACS measurement sensitivity are separate auditable tables. The20 deletion cases comprise17 unique geographic sets and are not independent validation. k stays4. No weight search or final clustering promotion occurred.

Reproduce in the verified Anaconda Python3.12.3/scikit-learn1.5.1 environment. Run common.py once for preservation; measurement_resolution.py reuses source payloads and cached attributes; additional_measurement.py supplies conditional/bounds evidence; controlled_shortlist.py reuses verified complete checkpoints; summarize_comparisons.py reuses completed coverage runs; write_decision.py generates the memos. source_lineage.py makes only a few official metadata requests. test_shortlist.py checks consequential numerical/identity invariants. Paths, byte hashes and versions are retained. No bulk GIS extraction or download was repeated.

Formal Stage7 labels/PCA, manuscript, figures, simulations, schedules and GA are untouched. The package is an isolated research recommendation, not authorization to replace them.
