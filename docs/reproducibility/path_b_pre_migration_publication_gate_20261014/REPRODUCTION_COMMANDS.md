# Bounded reproduction

Use Python 3.12 from the existing project environment. The scripts append the bundled ReportLab directory only if needed; they do not prepend a different NumPy environment.

From the Path B worktree, first run `review_publication_gate.py proofs` and `review_publication_gate.py qa` in this directory. The scripts use the archived compact inputs and import the existing figure plotting functions; they never call K-means or the physical pipeline. On Windows, deeply nested paths may need the `\\?\` prefix or `runpy.run_path` with that extended absolute path.

Run `finalize_gate.py` for a forced canonical caption rebuild, exact proof-byte replay, preservation comparison and the complete figure-suite test suite. It records the exact invocation in REBUILD_IDEMPOTENCE_QA.json and TEST_RESULTS.json. Reproduction is presentation-only.

The primary package's `independent_qa.py --archived-inputs` checks exact source hashes and frozen numerical arithmetic without modifying historical acquisition-method receipts. Live original-worktree preservation is checked separately by `review_publication_gate.py preservation`. The original source acquisition receipt is preserved even if the same bytes are now available from the shared LFS store.

`freeze` is an initial-state command, not a reproduction step: it refuses to replace an existing snapshot. No formal migration, manuscript edit or suite replacement is part of this gate. Read FINAL_PRE_MIGRATION_DECISION.md before any later author-authorized promotion.
