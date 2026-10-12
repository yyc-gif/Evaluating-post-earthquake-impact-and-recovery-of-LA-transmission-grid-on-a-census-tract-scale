# RQ-driven typology interpretation, 20261012

**AUTHOR REVIEW - NOT FORMAL STAGE 7.**

Start with `K_SELECTION_AUTHOR_DECISION.md`, then the full original-unit comparison and source audit. This package does not replace Stage7. Diagnostic class IDs are model-specific saved zero-based IDs (display D1=0). All GEOIDs retain eleven digits. Archived authority is `b2ed86401ad7ac98ed7a7bef5c83ddd08e4f23dc`.

## Reproduction

Use Python 3.12 and `pip install -r requirements-diagnostics.txt` (actual installed versions used for this review). Set `LA_GRID_FROZEN_SOURCE_ROOT` to the read-only archive containing authenticated `Formal_Experiment_20260923` trajectories/integrals and Git metadata. The local fallback is recorded in `common.py`; it is not an upstream scientific data path. `common.py` resolves exact Git blobs/LFS bytes and existing read-only caches; obtain retained inputs with Git LFS first. No archive download or regeneration is attempted if bytes are absent.

From this package directory run `python analyze_saved.py`, `python interpret_reports.py`, `python make_review_figures.py`, and `python verify_independent.py`. Analysis extracts existing station states and projects them linearly; it performs no new source gate, recovery or K-means. Report/figure steps use the verified extracts, not the model. Old seed/spatial stress results are reused. Independent QA asserts numerical identities, labels, physical hashes, exact cohorts, weights and preservation. Remote verification is separate, after scoped push. PDF review previews are rendered at 7.2-inch publication width and recorded in `VISUAL_QA.json`.

## Definitions and sources

Source/hash records list authoritative blobs and actual payload bytes. The prior package's frozen feature table, labels, preprocessing/weight JSON and stress tables are retained. Physical source records are 1,000 per-realization NPZ/JSON pairs authenticated against the frozen manifest and physical DS archive; the extracted NPZ is not a new simulation. `src/la_grid/revision/r1_source_gate.py` and `r1_realization_scheduling.py` define frozen semantics and are never executed here. Station IDs/coordinates/names/Core role and W come from frozen Data tables. B means realization-averaged normalized deficit hours over 0-480; Delta is matched Impact-first minus Unconstrained. Grid_Impact is W-weighted spectral connectivity loss, not the population-impact scheduling score. BUILDVALUE is NRI v1.19 total building stock, 2022 USD. SOVI uses frozen FEMA/CDC2020 percentile representation; original Q1-Q4 groups are preserved. Population upstream release remains unresolved.

The bulk per-realization trajectory/integral archive is not Git-tracked; a clean clone is insufficient for source-level extraction replay. This package retains authenticated initial-state extracts, profiles, labels for the 34 tracts and hash records so the interpretation can be inspected without silently regenerating missing source bytes. Full verification needs the original manifest-bound archive.

Every PDF/PNG is author-review diagnostics only. Profiles in actual-unit plots show means and P10-P90, not confidence intervals or independently validated community types. Geographic points do not imply neighborhood boundaries. No manuscript, numbered figure or formal simulation files are edited.
