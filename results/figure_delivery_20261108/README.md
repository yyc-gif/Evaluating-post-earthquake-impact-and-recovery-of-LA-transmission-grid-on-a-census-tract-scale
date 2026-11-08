# Figure package - 2026-11-08

Open `Individual_Figures/` to browse or download each figure separately. It contains eight main and eight supplementary figures, each as a separate caption-free PDF and PNG. Captions are in the standalone `FIGURE_CAPTIONS.md` file.

Download `LA_Grid_Figures_2026-11-08.zip` for a portable coauthor package with the same individual figures, separate captions, and the current combined `ALL_FIGURES_WITH_CAPTIONS.pdf`.

The loose `FIGURE_CAPTIONS.md` and `ALL_FIGURES_WITH_CAPTIONS.pdf` are identical to their archive copies. Each individual artwork file is copied from the separate review collection without modifying the graphic.

The current package is built from the refreshed S6-main4 author-review suite. Rebuild in this order:

```powershell
python src/la_grid/plotting/build_s6_main4_review.py
python docs/reproducibility/figure_delivery_20261108/package_delivery.py
```

Figure 1 Stage 4 includes the saved population-weighted Unconstrained and Impact-first service-availability trajectories. The package builder verifies every artwork against the active review manifest, checks archive CRCs and recomputes member hashes. See `PACKAGE_QA.json`.
