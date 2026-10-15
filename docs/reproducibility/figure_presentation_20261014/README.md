# Figure Presentation Correction - 2026-10-14

Scope: balance Figure 5 title/legend spacing; simplify Figure 7 titles and remove embedded explanatory footnotes. Supplementary Figure S8 also removes process-only labels and a redundant footer. The four Figure 7 panel titles use the same 9.5-point type. No chart is recalculated, smoothed or recolored.

The existing vector artwork is translated without scaling. Figure 5 has approximately 24-point row gaps; Figure 7 has approximately 20-point gaps. Original data labels and legend identities are retained. Native dimensions and 600-dpi exports are unchanged. All 14 other numbered PDF/PNG pairs are byte-identical to `b6e9e19bc990350f831f97444f375aa2d66cf43d`.

The current 17-figure suite, short captions, gallery, mirrors, previews and 21-page combined packet are synchronized. The seven-variable data authority, memberships, policy values and 950 original scientific files are unchanged. All analytical graphics remain vector-based; no AI-generated images are used.

Checked the standalone Figure 5 and Figure 7 pages and their actual assembled-packet pages at publication width: no clipping or overlapping titles; C1/C2/C3, N/A and the quartile/burden legends remain legible. Figure 7's source polygons, curves, heatmap values and color scales are retained. `INDEPENDENT_QA.json` records translated-region comparisons; the few map-edge antialiasing differences are bounded by 8/255 and affect less than 0.01% of color channels, with original vector paths unchanged. Figure 5 scientific regions are pixel-identical after translation.

Reproduce on the existing Windows/Arial production environment:

```powershell
python src/la_grid/plotting/build_current_figures.py --portable
python -m pytest tests/test_current_figure_suite_integration.py -q
python docs/reproducibility/figure_presentation_20261014/verify_presentation.py
```

For independent checks from a new clone, retrieve the comparison inputs first:

```powershell
git lfs fetch --include="results/figure_review/Main/Fig05.*,results/figure_review/Main/Fig07.*,results/figure_review/Supplement/FigS08.*" --exclude="" origin b6e9e19bc990350f831f97444f375aa2d66cf43d
```

`tests.xml` is the actual test-run record. `PRESENTATION_QA.json` records the source vector signatures and explicit translations; `INDEPENDENT_QA.json` checks the numerical authority, unaffected artwork and preserved inputs independently. Rebuilding checks output hashes for stability. No simulation, scheduling or clustering command is invoked.
