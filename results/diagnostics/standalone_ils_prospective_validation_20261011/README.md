# Fixed Standalone ILS Validation Package

Start with [the completed report](STANDALONE_ILS_PROSPECTIVE_VALIDATION_REPORT.md). This package contains exactly 2,000 new physical realizations evaluated under three frozen priority orders, with no optimizer, tuning, candidate reselection, or formal strategy promotion.

- `PAIRED_EFFECTS.csv`: fixed mean contrasts and uncertainty, including negative results.
- `POLICY_OUTCOMES.csv`: levels, distributions and descriptive tails.
- `REALIZATION_OUTCOMES.csv`: all 6,000 policy records.
- `FIXED2000_FULL_EVIDENCE.zip` / `FULL_EVIDENCE_MANIFEST.json`: full physical, schedule and trajectory evidence with every member hash.
- `EXECUTION_FREEZE.json` / `FIXED_STRATEGY_IDENTITIES.json`: original inputs, runtime, seeds and full 92-station orders.
- `NUMERICAL_AND_COHORT_QA.json` / `REPORT_NUMERICAL_QA.json`: production/kernel, reintegration and report checks.
- `PRESERVATION_VERIFIED.json`: original model, formal strategy, old samples and unrelated staged content preserved.
- `REMOTE_PUBLICATION_VERIFIED.json`: actual downloaded remote Git LFS payloads and data commit, after publication.

Negative differences favor ILS only for lower-is-better metrics. Signed quartile gaps and effective availability do not share that interpretation. Other endpoint intervals are descriptive pointwise, not a multivariate superiority test. Current scientific outputs and manuscript figures are unchanged.
