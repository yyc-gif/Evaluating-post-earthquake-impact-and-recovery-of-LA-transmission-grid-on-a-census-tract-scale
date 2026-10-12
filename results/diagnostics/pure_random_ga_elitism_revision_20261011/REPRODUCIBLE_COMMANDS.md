# Commands and boundaries

Run from this isolated worktree with the Anaconda interpreter, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1 and PYTHONDONTWRITEBYTECODE=1. `study.py engineering`, then `setup`, then `baseline` precede the registered commit. The20paired100k studies use `study.py main`. `study.py continuation` freezes the gate; only if execute=true use `study.py 250k`, then `study.py 500k` (same saved states).

After all searches: `analysis.py summarize`, `shadow`, `production`, `decision`, `qa`. `publication.py manifest` records every scoped payload; commit and push before `publication.py remote`. Commit the remote-byte receipt separately and verify final remote HEAD. The original cached legacy replay is100k logical lookups, not new physical draws or fresh training samples. It reproduces the authoritative seed rather than searching for a favorable baseline.

All raw score maps and RNG states are preserved inside per-seed/budget ZIPs. Budget continuation restores CHECKPOINT.pkl.gz in the same ignored runtime directory. If restoring onto another machine, recover the original scientific repository checkout identified by frozen source hashes, unpack the previous endpoint into that directory, and run the next fixed budget. No sequence from a previous strategy or independent validation is injected.

Direct API use: `run_search(..., elitism_mode=POST_EVALUATION_WORST_OFFSPRING_ELITISM)` versus `LEGACY_LAST_POSITION_ELITISM`; scientific objective remains injected unchanged. Root source is the authorized diagnostic engine only. Historical r1_ga_revision.py is not edited.

Windows testing uses short `_elitism_tmp`; the longer pytest fixture prefix exceeds MAX_PATH. Scientific/payload paths use the existing extended-length path helper. Temporary test and runtime files are not staged.
