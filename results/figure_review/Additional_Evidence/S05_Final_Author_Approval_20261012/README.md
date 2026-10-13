# Final S05 author-approval review

**READY_FOR_AUTHOR_APPROVAL.** The proposed four-panel PDF/PNG were inspected with MuPDF and Poppler at native 185-mm PDF width. The figure needs **no correction** and remains byte-identical to the prior verified candidate. Only this new isolated review package is added; no official figure, candidate sequence, manuscript, statistical result or scientific model is changed.

## Start here

- `FINAL_S05_AUTHOR_APPROVAL_PACKET.pdf`: two pages, exact 185-mm vector artwork followed by the 312-word caption and three author decisions.
- `S05_FINAL_VISUAL_REVIEW.md`: actual panel-by-panel observations and readiness boundaries.
- `S05_CONCISE_MANUSCRIPT_CAPTION.md`: copy-ready caption, including post-data adoption, failed 90% criterion and adverse equity findings.
- `GA_MANUSCRIPT_CONSISTENCY_AUDIT.md`: precise current-caption/summary and provisional backup-manuscript wording ledger.
- `GA_METHODS_RESULTS_DISCUSSION_PROPOSED_EDITS.md`: narrowly scoped copy-ready amendments, not a rewritten manuscript.
- `S05_PUBLICATION_INTEGRATION_PLAN.md`: exact official figure, mirror, caption, index and packet targets, with author-approval gates.

Unchanged figure source: `../Final_Pure_Random_GA_S05_20261012/FigS05_GA_Final_Candidate.pdf` and `.png`, pinned to `34c49469036354453c7b1f7fcef9cd92d14e8a3d`. The original existing-versus-proposed comparison is retained there. No redundant candidate PDF/PNG is created by this review.

## Important boundary

The previously confirmed external full working DOCX is missing. Its verified backup is inspected only for provisional locations, not restored or declared current. This is disclosed in the audit and approval packet. Actual current repository captions, Methods summary and packets are audited at revision remote `c0a11ffb4df523111efe6c8e65cfe86eadffec3c`. Final full-DOCX integration requires an accessible author-confirmed version; successful figure review does not resolve that exception.

## Reproducibility

`review.py` performs only source reading, hashing, PDF text extraction/rendering, vector packet assembly and preservation/remote-byte checks. It executes no optimizer, sampler, production evaluator or bootstrap. Archived numerical QA and all 86 immutable source payloads were hash-verified; the previous scientific tests were not rerun. Exact source identities, extracted paragraph/page locations, native dimensions, renderer versions, visual-review attestations and output hashes are recorded in the adjacent JSON files.

With Anaconda Python and the bundled Poppler available, from the review worktree:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/S05_Final_Author_Approval_20261012/review.py inspect
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/S05_Final_Author_Approval_20261012/review.py suite
# Run the PDF skill's operation-start marker before first packet authoring.
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/S05_Final_Author_Approval_20261012/review.py packet
# Visually open both complete-page renderer outputs before attesting review.
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/S05_Final_Author_Approval_20261012/review.py finish
# Only after scoped commit/push:
& C:\Users\yinch\anaconda3\python.exe results/figure_review/Additional_Evidence/S05_Final_Author_Approval_20261012/review.py remote
```

The script uses the existing `_s05r16` source worktree and read-only `_gaf12` preservation helper; external original-checkout/backup paths are recorded, not silently replaced. Reproduction outside this workspace should hydrate the pinned source review package and supply the protected-checkout paths, or skip only local preservation snapshots explicitly; do not substitute different scientific inputs. `inspect` is intended for the recorded clean base and live branch verification, not for pretending later source revisions are identical.

Runtime source/render intermediates are ignored. Their hashes and actual inspection decisions remain in the review receipts. New PDF and ordinary documents are verified against actual immutable remote bytes after publication. The publication receipt necessarily refers to the earlier payload commit; final remote HEAD is checked after committing that receipt and reported separately.
