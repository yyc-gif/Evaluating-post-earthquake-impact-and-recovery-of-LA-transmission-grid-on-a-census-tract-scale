# Controlled Stage7 feature and weight audit

Start with BUILT_ENV_REDUNDANCY_DECISION.md. No formal labels, manuscript material or existing figures are replaced.

Required comparisons are complete: building stock+ALR versus ALR-only versus EAL; inherited/equal parent-domain weights; all-use2014/ACS/no-age; equal-domain SCAG missing-land allocation; BE0-BE8 ablation and nonredistributed deletion controls. All comparisons use2287 complete GEOIDs, k4, seeds42-61 and n_init100. No new k selection or physical-model runs.

The two diagnostic PDFs are actual185-mm vector files with Arial text. Captions are in FIGURE_CAPTIONS.md. CONTROLLED_FEATURE_COMPARISONS has three pages; PNGs preserve each page separately.

BUILT_ENV_ABLATION_RESULTS reports both frozen-seed42 and same-seed BE0 references; default reassignment uses same-seed BE0. WITHIN_WEIGHT_SPECIFICATION_EFFECTS isolates content changes within the same parent budgets. WEIGHT_SCHEME_EFFECTS holds content fixed. PHYSICAL_REDISTRIBUTION_EFFECTS isolates surviving-coordinate amplification. Spatial ARI always uses each specification's own full-cohort baseline, and class matching is trained only on retained members. CSV feature names are provenance keys, not proposed axis wording.

run_records contains29 compressed NPZ archives and JSON metadata, including20 full and20 spatial cases per archive. Reused full centers are label-member means, not original fitted centers. Proportional missing-land scenarios are aliases, not independent observations. No statistical pool of these cases is treated as independent replication.

Reproduce from the parent commit with NumPy1.26.4, pandas2.2.2, scikit-learn1.5.1 and SciPy as recorded in CONTROLLED_COMPARISON_SPECIFICATION.json. Hydrate source LFS files. Run controlled_audit.py --fit --analyze, finish_audit.py, write_decision.py, diagnostic_figures.py and pytest test_controlled_audit.py. Existing input-identical archives are reused; remove only this new package's checkpoints deliberately if a refit is intended. Do not invoke any formal stage runner. Checkpoint counters in FIT_EXECUTION_RECORD describe the original audited execution, not a later cache-only invocation.
