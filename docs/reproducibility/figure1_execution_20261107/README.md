# Figure 1 execution-stage correction - 2026-11-07

Baseline: `70a063bf9ff4d39a84090aa297aa3ac0e737b091`.

Stage 4 previously used two identical illustrative step curves, 6.8-7.2 pt labels,
and all-capital mode headings that did not match the adjacent 7.5 pt artwork.
The replacement removes both curves and uses Arial 7.5 pt for every Stage 4 body
label, with regular body text and bold mode headings matching Stage 5. The stage
heading retains Arial Bold 9.5 pt.

The replacement distinguishes parallel, sampled-duration Unconstrained repairs
from priority-ordered, finite-crew repairs with directed travel. Repair completion
sets raw station functionality to one; source gating and tract aggregation then
produce modeled service-availability curves. Metrics remain in Stage 5. No curve
has been fabricated, and no physical calculation, order or result is changed.

The canonical renderer is `restoration_workflow` in
`src/la_grid/plotting/figure_presentation.py`, used directly by
`src/la_grid/plotting/build_current_suite_p2.py`.

Scoped reproduction (Figure 1, its mirror, preview, manifests and packets only):

```powershell
& C:\Users\yinch\anaconda3\python.exe docs/reproducibility/figure1_execution_20261107/refresh.py
& C:\Users\yinch\anaconda3\python.exe -m pytest -p no:cacheprovider tests/test_figure1_execution_20261107.py tests/test_rq_aligned_figure_suite_20261101.py -q
```

`QA.json` records exact source/output hashes, deterministic renderer replay,
pixel identity outside Stage 4, typography and the thirty unchanged artwork
files (fifteen other numbered PDF/PNG pairs). The supplementary packet retains
its original bytes. The full packet retains sixteen figure-and-caption pages.
Missing LFS payloads are fetched and hash checked; source data are never generated.

The current active deliverables remain under
`results/figure_review_rq_aligned_20261101/` and
`results/figures_rq_aligned_20261101/`. Archived figures and manuscript files are
not modified.
