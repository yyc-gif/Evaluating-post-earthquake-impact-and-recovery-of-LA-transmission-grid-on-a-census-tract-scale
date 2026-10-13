# Caption-only reproduction

Use Python 3.12 with the repository's figure-production dependencies and actual Git LFS objects, including PyMuPDF, ReportLab and the existing plotting stack. On Windows the existing suite uses installed Arial fonts.

```powershell
git lfs pull
python src/la_grid/plotting/build_current_suite_k3.py --portable
python -m pytest tests/test_current_figure_suite_integration.py -q
python src/la_grid/plotting/build_current_suite_k3.py --portable
```

The accepted source commit `8f2dcb3b9762137b9f2686609c34480334f5d44e` must be available in Git history; shallow clones may require fetching that history. Missing accepted LFS payloads cause an explicit error, not an artwork reconstruction from old five-class data.

`--rebuild` forces reconstruction of the caption packet from the accepted 38-page source, not a redraw of any numbered artwork. The other 37 source pages and the two figure-only packets are preserved. Default replay uses the checked output hashes and is byte-idempotent.

Independent before/after QA:

```powershell
python docs/reproducibility/figure_suite_s10_crossref_fix_20261013/verify.py before
python docs/reproducibility/figure_suite_s10_crossref_fix_20261013/verify.py after
```

Run `before` only in a fresh isolated follow-up, before the production build. It records original author-worktree hashes and indexes, so it requires the declared local original worktree. A clean clone can run the canonical replay and 22 integration tests without that original local archive. No preservation claim is fabricated for an absent original worktree.

This workstation uses `C:\Users\yinch\anaconda3\python.exe`. ReportLab is supplied by the bundled runtime by appending its `dependencies/python/Lib/site-packages` directory to `sys.path` before invoking `runpy.run_path` on the canonical entrypoint. Appending avoids replacing Anaconda's NumPy/GIS binaries. The invoked entrypoint and `--portable` behavior are unchanged.
