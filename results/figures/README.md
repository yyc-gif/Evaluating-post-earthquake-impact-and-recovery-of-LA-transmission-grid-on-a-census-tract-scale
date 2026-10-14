# Current publication figure suite

17 numbered figures: Main Fig01-Fig07 and Supplement FigS01, FigS03-FigS11. FigS02 remains integrated into S01; S12/S13 remain consolidated into S11.

The current figure representation is author-approved NCV14/H2/K3 on 2,299 positive-population tracts. Figure 7D displays continuous five-policy mean total service deficit with frozen SOVI Q4 outlines. No K4 classification, hotspot ranking or new model fit is published. Archived formal Stage 7 science and manuscript files are unchanged.

Canonical build: `python src/la_grid/plotting/build_current_suite_k3.py`. Historical dated builders reproduce historical presentations and are not current entrypoints.

Run `python -m pytest tests/test_current_figure_suite_integration.py`. Figure-only sources, hashes and checks are in `docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013/`. Pinned Git commits and actual LFS payloads are required for a fresh rebuild; fetch instructions are in REPRODUCTION_COMMANDS.md.

The PDF artwork is native 185 mm wide, with 600 dpi PNG mirrors and publication-size page previews. Complete packet: 38 pages, including 17 figure/caption pairs and four unchanged complementary-evidence pages. Manifest and figure index each contain 34 PDF/PNG rows.

Artwork here mirrors the authoritative `results/figure_review/` bytes exactly. Open FIGURE_REVIEW_GALLERY.html for the current gallery.

## Approved Figure 7 Candidate A

Current Fig07 is 185 x 253 mm: six exact class ECDF distributions (A), eight ordinary frozen cohort-z means (B), saved K3 geography (C), and continuous five-policy deficit with frozen Q4 outlines (D). C/D are translated down 8 mm without scaling; only the 16 N/A polygons per map and their swatches have white fill / dark 0.45-pt outlines. All other 16 numbered artwork pairs and the Supplement-only packet retain their approved bytes. The separately approved S10-to-S11 caption correction from 7795638 is explicitly carried forward, without merging that branch.

Reproduce with `python src/la_grid/plotting/build_current_suite_k3.py --portable`; use `--rebuild` to force deterministic frozen-source rendering. Current QA: `docs/reproducibility/figure7_candidateA_approved_integration_20261013/`. No scientific model, formal Stage 7 input, manuscript or historical review output is changed.
