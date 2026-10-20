# Repository Cleanup - 2026-10-14

The current branch is named `2026-10-14`. The former name `publication/p2-seven-variable` is retired; `main` is unchanged. Scientific model identifiers in source records remain intact for provenance; they are not extra version names.

## Current Assets

Retained: all input data, frozen formal experiments, current seven-variable/three-class authority, K4 sensitivity, final policy summaries, current 17-figure suite, tests, source records and legal/citation files. The current Stage 7 directory is `results/stage7/2026-10-14/`.

The canonical figure command is `python src/la_grid/plotting/build_current_figures.py --portable`. Frozen scientific arrays, memberships, all 34 numbered artwork files and the combined 21-page PDF are unchanged by this cleanup.

## Retired from the Current Tree

Removed 4,397 obsolete tracked files from the 6,250-file baseline, including 3,431 per-run search records, 805 superseded artwork/review files, 106 built-environment audit files and 16 one-off plotting scripts. Retained figure-source records now live under `docs/figure_sources/2026-10-14/`, rather than a separate root-level local review package. Editable Word drafts and the old submission package are no longer tracked.

- Repeated per-run GA search files; retain final summaries, approved method records and underlying formal results.
- Superseded figure-review copies and artwork drafts; retain the numeric cross-hazard table still used by figure readers.
- The rejected built-environment exploratory package.
- Duplicate local review packets, contact sheets, previews and editable document drafts.
- Sixteen one-off presentation scripts whose consumers are also retired; retain current builders and shared dependencies.

This is a current-tree cleanup, not a history rewrite. No original data or local scientific file was deleted. Before untracking, a verified Git bundle and an exact retired-path/blob register were saved outside the checkout in `_repository_cleanup_backup_20261014/`. Hydrated local files remain ignored in place. Historical scripts and their complete inputs should be used at their original commit, not mixed into the current version.

The source snapshot before cleanup is `aecc9adadd04edc4c5f64de64f79ed4c34c1f69c`. To inspect a retired file, use `git show aecc9adadd04edc4c5f64de64f79ed4c34c1f69c:path/to/file`. For old binary payloads use `git lfs fetch origin aecc9adadd04edc4c5f64de64f79ed4c34c1f69c`. The existing LFS cache and remote objects are not pruned. A Git bundle stores LFS pointers, not the payload bytes themselves.

Removing files from the current tree reduces clone checkout clutter; it does not shrink retained Git history or promise a corresponding disk-space saving. Archived worktree directories and other projects are outside this cleanup.

Verification: [checks.json](reproducibility/2026-10-14/checks.json) records independent artwork, numerical-authority and 950-file preservation checks; [tests.xml](reproducibility/2026-10-14/tests.xml) records the full 44-test result. The current builder was replayed successfully with unchanged artwork and packet hashes.
