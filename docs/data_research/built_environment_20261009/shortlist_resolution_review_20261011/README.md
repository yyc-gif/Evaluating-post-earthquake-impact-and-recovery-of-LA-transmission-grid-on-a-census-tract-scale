# Stage7 Shortlist Resolution: Independently Reviewed Package

Baseline: `94faefd30273dec8318197de443f2f992fa29e5c`.
Branch: `analysis/stage7-shortlist-independent-review-20261011`.

The decision is **CORE3: EMC2022 coverage + ACS2022 five-plus housing-unit share + SCAG2020 classified-land entropy**, with explicit source/support qualifications. See `FINAL_VARIABLE_RECOMMENDATION.md`, `FINAL_CANDIDATE_CONSTRUCT_DECISION.md` and `DOMAIN_WEIGHT_REQUIREMENTS.md`. This closes measurement selection; final domain weighting and formal promotion are separate decisions.

## Computation And Reuse

A matching completed local diagnostic study was frozen rather than rerun. `REUSE_PROVENANCE.json` identifies its uncommitted status; `REUSED_RUN_BYTE_MANIFEST.csv` records all copied bytes, and `reused_narratives/` preserves its original recommendation documents. The reviewed root documents supersede those narratives. Copied `EXECUTION_LOG.md`, fit receipts and original `PRESERVATION_*.json` describe the reused study; `REVIEW_*` and `INDEPENDENT_*` describe this independent round. Nothing was written to the source study.

The original study has 460 new fits and 40 reused historical fits. This review adds zero fits. Actual independent computations verify 12 specifications, 240 paired seed/spatial cases, 1,320 model-pair tables, exact unchanged nonphysical coordinates, source substitutions and 950-file/862-staged-item preservation. Results are not inferred from a successful script or file existence.

## Reproduce The Review

Use the recorded Anaconda Python/scikit-learn environment and a checkout with actual LFS payloads. From the analysis worktree:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
& 'C:\Users\yinch\anaconda3\python.exe' -B 'docs/data_research/built_environment_20261009/shortlist_resolution_review_20261011/independent_review.py' review
& 'C:\Users\yinch\anaconda3\python.exe' -B -m pytest 'docs/data_research/built_environment_20261009/shortlist_resolution_review_20261011/test_shortlist.py' -q -p no:cacheprovider --basetemp './_review_pytest_tmp'
```

The review finds archived source payloads by commit-verified hashes, including the sibling `_ca10` checkout used locally. Original preservation tests require the original worktree and its protected-file inventory; adapt only those local locations for another machine. The copied full calculation scripts document the earlier measurement/fitting procedure; do not launch them to reconstruct already available results. `controlled_shortlist.py` checkpoints and historical fit provenance remain intact. No new k or weight search is preregistered by this package.

## Contents

All eight requested named deliverables are at this directory's top level. The matrix retains 2,291 residential GEOIDs and explicit sample masks; full-domain accounting retains 2,315. Model predictions, original-unit profiles, class matching/retention/purity, covariance-aware ACS replicate evidence, EPA allocation stress tests and source lineage/support records are preserved. No imputation fills the four unresolved geometries or the one conditional Assessor-age denominator failure.

Formal Stage7 outputs, labels, manuscripts, artwork, physics, recovery simulations, schedules and GA outputs remain untouched. Numerical decision summaries do not authorize class renaming or model promotion. File manifests, independent QA, test receipts, original-tree preservation and remote LFS byte verification accompany publication of this package.
