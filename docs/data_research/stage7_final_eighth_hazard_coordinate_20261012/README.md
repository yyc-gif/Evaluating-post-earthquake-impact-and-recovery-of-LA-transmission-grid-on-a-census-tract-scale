> EXPLORATORY EIGHT-VARIABLE AUTHOR REVIEW — NOT FORMAL STAGE 7

# Eight-variable author-review candidate

Primary: H2-CBM with official `RPL_CBM`; P2 is ablation. Provisional detailed review K4, with K3/K5 evidence retained. No formal promotion.

Entry report: `FINAL_EIGHT_VARIABLE_AUTHOR_DECISION.md`. Source search: `EIGHTH_COORDINATE_SOURCE_SEARCH.md`. CSV tables have the review-status column; numerical NPZ arrays are identified by the labeled registration and hash ledger. Original fetched bytes retain their original content with labeled provenance ledger.

## Reproduction (Python3.12)

From this package: `python prepare.py`, `python acquire_search_sources.py`, `python analyze.py`, `python reports.py`, `python figures.py`, `python verify_independent.py`.
All writes are package-scoped. Source payloads must match `5eeaa02ca4dec99f27a6ee3eb470a441007e6f6b` and need Git LFS. `prepare.py`/preservation checks additionally require the manifest-bound original frozen archive at `LA_GRID_FROZEN_SOURCE_ROOT` (see `common.py`). No frozen damage/schedule/recovery calculation runs. Prior fit labels/matrices are reused; only narrowly registered researcher component leaveouts are fitted. Source fetches use original URLs, preserve hashes and log access failures; if official sources move, retain the archived bytes rather than silently replace them.

`verify_remote_delivery.py` runs after push and hashes actual remote LFS bytes. The final proof is a separate provenance-only commit. Figure rebuilding uses commit-bound prior geometry and does not regenerate model results; no old four-tract geometry exclusions apply.

Registered component fits retain `tol=1e-4`. Returned model-center inertia and final-membership centroid WCSS are separately stored where early tolerance stopping produces a small difference; labels, parameters and initializations are not adjusted to remove it.

Main tables: candidate comparison, incremental information, K evidence, full original-unit profiles, hazard component sensitivity, geographic/policy stability. Source quality remains unresolved; numerical QA is not scientific certification.
