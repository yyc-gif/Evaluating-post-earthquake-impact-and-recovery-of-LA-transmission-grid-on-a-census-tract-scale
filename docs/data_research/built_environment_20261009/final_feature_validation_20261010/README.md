# Joint Stage 7 candidate QA and controlled exploratory comparisons

Read STAGE7_FEATURE_DECISION_PACKET.md first. This directory contains new analysis only; it does not replace formal Stage7 results.

Reproduce with the Anaconda GIS/scikit-learn environment:

```text
python validate_stage7.py initialize
python validate_stage7.py landqa
python validate_stage7.py corrections
python validate_stage7.py features
python controlled_clustering.py
python summarize_and_verify.py additional
python summarize_and_verify.py spatial
python summarize_and_verify.py report
python -m pytest test_final_validation.py
python summarize_and_verify.py verify
```

The unchanged earlier extraction and FEMA audit are inherited on this analysis branch. Large raw source caches stay local and are referenced by exact hashes; no raw-source reacquisition is needed on this Windows checkout. The only fresh acquisition was18 Census2020 tract geometries for QA.

FINAL_CANDIDATE_FEATURE_MATRIX.csv keeps2291 rows with nulls; COMPLETE_CASE_FEATURE_MATRIX.csv contains2287 rows. LEGACY_2276_COMPLETE_CASE_FEATURE_MATRIX.csv is separately retained. run_records/ contains all20-seed,k2–8 labels and fit metrics. Original Stage7 labels were not used for feature selection or fitting.
