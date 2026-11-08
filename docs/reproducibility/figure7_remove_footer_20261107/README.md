# Figure 7: remove the entire bottom annotation block

Baseline: `b3bf69a7334cfcea595994250bb873d7263a8393`.

Both bottom explanatory lines are deleted in full, not just their headings.
No alternative prose or statistics block replaces them. The legends, map keys,
panels A/B/C/D, profile values, geometry, colors and page dimensions are unchanged.

The two text-generation calls and their display-only calculation block were
removed from canonical `compose_figure` in
`src/la_grid/plotting/figure7_final_presentation_20261016.py`. Numerical screening
verification is retained in `QA/FIG07_DISPLAY_QA.json`, outside the artwork.
It includes the unchanged 94-tract / 350,799-resident screen, exact threshold,
21 profile values and 18 ECDF records from the registered feature table.

The Figure 7 science regression now reads this compact, reproducible JSON rather
than unavailable historical process CSVs. All original science assertions are
retained; the artwork assertion is reversed to require absence of the unwanted
statistics. An additional regression rejects any text below the legends and
checks that the canonical compositor has no direct narrative text calls.

The current PDF, 600-dpi PNG, mirror, preview, manifests and main/combined packets
are synchronized. Captions and the supplementary packet are unchanged. All
fifteen other numbered PDF/PNG pairs are byte-identical. No physical model,
clustering fit, manuscript or scientific result table is modified.

```powershell
& C:\Users\yinch\anaconda3\python.exe docs/reproducibility/figure7_remove_footer_20261107/refresh.py
& C:\Users\yinch\anaconda3\python.exe -m pytest -p no:cacheprovider tests/test_figure7_no_footer_20261107.py tests/test_rq_aligned_figure_suite_20261101.py -q
```

The local inspection PNG is excluded from Git/LFS; the final suite artwork is
the delivered image. `QA.json` records deterministic reproduction and exact
pixel identity above the removed footer.
