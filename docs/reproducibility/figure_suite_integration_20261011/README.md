# Current-suite integration verification

The author-facing entry remains `results/figure_review/` on `revision/reviewer-driven-core-rebuild-v2`. This directory holds verification records, not a competing figure set.

The scientific/artwork baseline is 031d2c675f8e7d58035d27448be040b809ced086. Exact selected presentation files come from the already completed review commit 5f099e651de751f91553d2df920dca9cbc02eea6. Ten numbered figures change; the other nine retain their baseline bytes. Nineteen PDF/PNG pairs and the results/figures mirrors are checked by SHA-256. The manifest records each exact source.

Reproduction: run `src/la_grid/plotting/consolidate_current_figure_suite.py` in a checkout with the pinned source commits and actual LFS payloads available. Dependencies are PyMuPDF, ReportLab and Arial TrueType fonts. This Windows run used Anaconda Python with the existing Codex bundled ReportLab package appended to the import path. No simulation, estimator, map extraction, quartile calculation, cluster fit or scientific plot regeneration is invoked.

Run `python -m pytest tests/test_current_figure_suite_integration.py -q` for the integrated-file checks. Five tests passed. A caption merge regression caused by CRLF source text was caught and corrected before delivery; explicit expected heading counts prevent silent omissions.

`INTEGRATION_QA.json` identifies all payloads and native metrics. `reviewed_source_qa/` preserves the existing two rounds' numerical-invariance evidence. `PRESERVATION_BEFORE.json` and `PRESERVATION_AFTER.json` are identical: all 950 protected files, the original index bytes, staged-name list and 862 staged entries remain unchanged. Formal five-cluster Stage 7 and existing GA scientific results remain intact.

`VISUAL_QA.md` records actual PDF render inspection. `OUTPUT_HASHES.json` identifies the delivered suite and metadata. After pushing, run `verify_delivery.py` to verify revision remote HEAD, all numbered files and mirrors, and downloaded GitHub LFS payload bytes. The resulting receipt is committed separately; it refers to the payload commit, whose artwork remains unchanged in the receipt commit.
