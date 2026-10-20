# Reproduction

Run from the `1021` worktree root with the project Anaconda interpreter:

```powershell
& 'C:\Users\yinch\anaconda3\python.exe' src/la_grid/plotting/build_current_figures.py --portable
& 'C:\Users\yinch\anaconda3\python.exe' docs/reproducibility/figure7_map_readability_20261015/verify_figure7_map_suite.py
& 'C:\Users\yinch\anaconda3\python.exe' -m pytest tests/test_current_figure_suite_integration.py -q
& 'C:\Users\yinch\anaconda3\python.exe' docs/reproducibility/figure7_map_readability_20261015/verify_remote_lfs_payloads.py --no-write
```

The canonical builder verifies the saved seven-variable P2/K3 authority and uses the pinned continuous-map vector paths. It does not fit K-means or regenerate physical/recovery simulations. The independent verifier checks the cohort split, class and screening counts, vector map output, PDF/PNG mirror hashes, packet pages, baseline artwork hashes, and the explicit changed-path allowlist.

Review comparisons are in `results/diagnostics/1021/figure7_readability_20261015/`; these unnumbered outputs do not replace the numbered Figure 7.

The remote LFS check downloads only objects referenced by the update into a new temporary store and compares actual payload SHA-256 values and byte counts with the committed pointer files. `REMOTE_LFS_PAYLOAD_VERIFICATION.json` records the first successful remote byte check.
