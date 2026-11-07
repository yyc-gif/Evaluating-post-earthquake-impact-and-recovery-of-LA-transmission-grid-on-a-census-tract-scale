# Figure 4 scope and spacing correction - 2026-11-07

Starting current suite: `d65f82ced0b9e9e01cd42f9d2f5e3b9261961da1`.
Earlier A/B artwork: `0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68`,
`results/figure_review/Main/Fig04.pdf`.

## What was originally present?

The earlier figure contained A, population-weighted recovery trajectories, and
B, service loss and population T80 for seven displayed strategies. It did not
have a component-decomposition panel C. Commit
`f2a7ce41df9c4beda4814b9c0ec1ab27426ae3bf` added the RQ-aligned third panel.
Its generator hard-coded Degree-first minus Hospital-first on matched realization
rows. This is a valid descriptive pair contrast, not an all-strategy mechanism
comparison, and is not an explanation of GA versus Impact-first.

## Correction

Restore the original A/B scientific scope. Keep all seven displayed strategies:
Impact-first, Hospital-first, Degree-first, Vulnerability-first,
Betweenness-first, Random and Unconstrained. This is not a claim that the
figure displays every strategy ever evaluated in the study.

Panel A reuses the actual saved vector trajectories and legends with translations
only, not resampling or redraws. Panel B retains the current saved mean losses,
population T80 and 5th-95th realization ranges exactly. The single-pair numerical
rows are retained in QA and their original artwork remains in Git history and
the existing Contribution 1 diagnostics; no historical evidence is deleted.

Both titles are centered Arial Bold 9.5 pt. The title-to-legend text clearance is
12 pt in both panels (measured tolerance 0.05 pt). The previous panel's x-axis
label to the next panel title clearance is approximately 21.8 pt. Uncertainty
definitions belong in the concise caption, not another annotation row.

Only Figure 4 artwork changes. Figure 1's execution correction, Figure 7, the
other thirteen numbered figures, scientific inputs and manuscript are preserved.
The current main/combined packets, Figure 4 caption, manifest, index and gallery
are synchronized. The supplementary packet remains byte-identical.

## Reproduction

```powershell
& C:\Users\yinch\anaconda3\python.exe docs/reproducibility/figure4_scope_spacing_20261107/refresh.py
& C:\Users\yinch\anaconda3\python.exe -m pytest -p no:cacheprovider tests/test_figure4_scope_spacing_20261107.py tests/test_rq_aligned_figure_suite_20261101.py -q
```

See `QA.json` for exact source hashes, all saved outcome rows, spacing measurements,
deterministic replay and the thirty preserved PDF/PNG hashes. Inspection previews
remain local; only final figure artwork is uploaded to LFS.
