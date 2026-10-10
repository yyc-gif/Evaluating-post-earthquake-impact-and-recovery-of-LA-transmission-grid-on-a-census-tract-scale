# Stage 7 Manuscript Reconciliation

## Start Here

The author confirmed the complete `LA_grid_manuscript_rebuild/LA_Grid_Manuscript_Resubmission_Rebuild.docx` as the working source. Its SHA-256 is `a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253`, identical to Git3466ba2. The legacy IJDRR manuscript was not adopted by default. Journal selection is still unresolved.

Read `Manuscript_Stage7_Integration_REVIEW.docx` or the native-Word-exported companion PDF, then `MANUSCRIPT_RECONCILIATION_DECISION.md`. This clean review copy has no tracked changes. The exact before/after ledger is `MANUSCRIPT_PARAGRAPH_CHANGE_LEDGER.csv` and `MANUSCRIPT_REVISION_CHANGELOG.md`.

The package integrates saved D/five-domain/k4/seed42 membership, not a refit. It withdraws old five-class/PCA/hotspot interpretations, adds Figures7-8 and Table4, and keeps original Figures1-6, Tables1-3, abstract, conclusions, 108 unaffected paragraphs and unrelated scientific content unchanged. The map legend alone is corrected in a review-only derivative; outside-cohort does not mean no residents.

## Audit Records

- `MANUSCRIPT_SOURCE_AUDIT.md`, inventory JSON/CSV and `source_extracts/`: 41 plausible manuscript/supplement/plan paths and historical versions, exact hashes, contents and provenance.
- `MANUSCRIPT_CLAIM_RECONCILIATION.csv`: 231 paragraph/table-cell claim records across distinct scientific states and relevant plans. Actions apply to the identified Stage7-dependent claims, not blanket deletion of unrelated clauses in the same paragraph. Identical-byte copies inherit the unique version disposition.
- `FIGURE_AND_TABLE_INTEGRATION_MAP.md`: actual current numbering, provisional supplementary placement and inherited figures that must not be confused with July figure numbers.
- `HOTSPOT_AND_INTERVENTION_DEPENDENCY_AUDIT.md`: cluster-independent policy findings versus conclusions requiring separate hotspot revalidation.
- `REFERENCE_VERIFICATION.csv`: official version-specific dataset definitions, original clustering/framework publications, and explicitly partial/unresolved bibliographic checks.
- `REVISED_STAGE7_METHODS.md`, `REVISED_STAGE7_RESULTS.md`, `REVISED_STAGE7_DISCUSSION.md`, `REVISED_STAGE7_SUPPLEMENTARY.md`: manuscript-compatible replacement sections and full original-unit tables.
- `NUMERICAL_QA.json`, profile/direction/cohort CSVs, `DOCUMENT_STRUCTURE_QA.json`, `DOCUMENT_RENDER_QA.json`, `FIGURE_RENDER_QA.json`, `DELIVERY_QA.json`: independent saved-value checks, rounded Word-table checks, OOXML preservation and actual page inspection.
- `PRESERVATION_BEFORE.json` / `PRESERVATION_AFTER.json`: unchanged original index/staged diff, 862 staged items, 950 protected scientific payloads and source manuscripts.
- `OUTPUT_HASHES.csv`: package hashes excluding itself, remote verification and ignored temporary raster/log files. `REMOTE_VERIFICATION.json` records remote HEAD and actual retrieved Git LFS payloads after push.

## Reproducibility

Run from the isolated worktree rooted at the validated preview commit84d7ac6. Use the bundled document runtime, not the simulation environment. The supporting commands do not fit clustering or evaluate recovery.

```powershell
$Python = 'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$Package = '.\docs\data_research\built_environment_20261009\manuscript_reconciliation_20261010'
& $Python "$Package\verify_frozen_results.py" --repo .
& $Python "$Package\build_reconciliation.py" --repo .
& "$Package\export_word_qa.ps1" -Package $Package -Scratch '.\_qa7'
& $Python "$Package\inspect_rendered_document.py" --package $Package --scratch '.\_qa7'
# Inspect every newly rendered review page before invoking --confirm-pages.
& $Python "$Package\inspect_rendered_document.py" --package $Package --scratch '.\_qa7' --confirm-pages
& $Python "$Package\preserve_and_verify.py" --repo 'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision' --package $Package --verify
& $Python "$Package\finalize_delivery.py" --repo .
# After the isolated branch has been committed and pushed:
& $Python "$Package\verify_remote_payloads.py" --repo .
```

Source discovery/history extraction is reproducible using `audit_sources.py --help`; its inventory is frozen because local versions can evolve. Do not overwrite a preservation baseline after original files change. `build_reconciliation.py` rewrites only generated package outputs. Rebuilding requires repeating actual rendering/inspection and manifest generation.

## Execution And Limitations

The canonical document renderer was attempted but could not run with the long Windows paths and absent soffice executable. A hidden Microsoft Word16.0 instance opened short-path scratch copies read-only and exported the actual PDF instead. PDFium rendered pages at160dpi. The final review has20 pages; all were visually inspected. The original15-page PDF is a reference render, not represented as a separately completed full-page visual audit. Original preview figures were inspected at185mm and provisional178mm; new Word figures at172.72mm. The final journal has not approved these dimensions.

New Table4 is kept on one page. Figure8 retains +7.15 despite color saturation at +/-1.5 and is accompanied by original-unit values. Existing mathematical notation, Greek symbols, fonts, styles and original artwork were preserved; no global formatting pass was performed. Temporary PNGs and short-path scratch copies are not committed.

Readiness is for author examination only. Before promotion, resolve the September/October GA experimental scope, old hotspot dependencies, final supplementary numbering and journal, and partial/reference-version caveats. There is no new hotspot score, restoration sequence, capacity result, simulation, PCA, clustering, GIS extraction or validation sample collection in this package. No formal Stage7/GA candidate was replaced.
