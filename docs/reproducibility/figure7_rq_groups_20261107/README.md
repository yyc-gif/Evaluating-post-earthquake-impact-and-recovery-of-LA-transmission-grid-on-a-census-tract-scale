# Figure 7B research-question grouping - 2026-11-07

Baseline: `2621ca6eb39944892771759a4cb35c77a819e171`.

Only Panel B's RQ grouping is changed. Distant, unconnected RQ labels are replaced
with adjacent three-, two-, and two-row brackets. Horizontal group boundaries
extend across the parameter labels as well as the heatmap, making membership
explicit without adding a text block or changing colors or values.

| Group | Exact fitted fields |
|---|---|
| RQ1 | Init_Supply; Grid_Impact; Redundancy_HHI |
| RQ2 | B_Unconstrained; MeanDelta |
| RQ3 | SOVI_SCORE; log1p_Population |

The publication label Tract population still denotes the log1p population
coordinate in this standardized profile. No transformation or weight is changed.
The 21 displayed ordinary cohort-z class means are independently reconstructed
from the 2,299-tract source table and the saved population-SD standardizer, and
compared both with the saved numerical table and the previous PDF text.

`QA.json` records source hashes, the mapping above, unchanged printed cells,
deterministic reproduction, exact pixel identity outside the authorized B region,
and the byte identities of all fifteen other numbered PDF/PNG pairs.
Panels A/C/D, including the Q4/high-burden screen, are not regenerated.

The canonical implementation is `_draw_profiles` in
`src/la_grid/plotting/figure7_final_presentation_20261016.py`. The scoped updater
calls that same renderer and replaces only Panel B's rectangle. It synchronizes
the current figure, mirror, preview, caption, gallery, manifests and packets.

```powershell
& C:\Users\yinch\anaconda3\python.exe docs/reproducibility/figure7_rq_groups_20261107/refresh.py
& C:\Users\yinch\anaconda3\python.exe -m pytest -p no:cacheprovider tests/test_figure7_rq_groups_20261107.py tests/test_rq_aligned_figure_suite_20261101.py -q
```

The inspection crop is a local preview, excluded from LFS; the final PDF and
600-dpi PNG are the deliverable artwork. No model, manuscript or scientific
result table is modified.
