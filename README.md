# Post-Earthquake Power Service Recovery in Los Angeles: Linking Substation Damage, Restoration Logistics, and Tract-Level Disparities

**Paper authors:** Yinchen Yi, Yutong Li, and Marta C. González.

**Repository maintainers:** Yinchen Yi and Yutong Li.

## Version 2026-10-14

Code, necessary inputs, retained results and publication figures for the paper. The current version is the **`2026-10-14`** branch; `main` is retained unchanged for historical reference.

The adopted community typology uses seven variables and three classes: initial supply, spectral grid impact, dependency HHI, Unconstrained deficit, five-policy MeanDelta, SOVI and log population. It covers 2,299 positive-population tracts, including eight zero-housing tracts. All 2,315 tracts remain in the service model. K4 is sensitivity evidence only; NCV14 is supplementary environmental context, not a clustering coordinate. This is a graph-based service-recovery workflow, not electrical power-flow analysis.

## Install

Python 3.12 and Git LFS:

```bash
git clone --branch 2026-10-14 https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git
cd Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale
git lfs install
git lfs pull
python -m pip install -r requirements.txt
```

## Check and Build

```bash
python src/la_grid/revision/current_stage7.py --verify
python src/la_grid/plotting/build_current_figures.py --portable
python -m pytest tests/test_current_figure_suite_integration.py -q
```

These commands reuse frozen results; they do not fit clusters or run simulations. The [combined figures and short captions](results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf) contain 17 numbered figures and four retained evidence pages, 21 pages total. A [figure gallery](results/figures/FIGURE_REVIEW_GALLERY.html) is also available.

## Files

| Path | Contents |
| --- | --- |
| `src/la_grid/` | Calculation, verification and figure code |
| `Data/` | Input data and source notes |
| `Formal_Experiment_20260923/` | Frozen experiment records and retained numerical outputs |
| `results/stage7/2026-10-14/` | Current feature table, saved memberships and checksums |
| `results/figure_review/` | Current figures, captions and combined PDF |
| `results/figures/` | Matching artwork copies, index and gallery |
| `FINAL_REVISION_RUN_SEQUENCE/` | Stage commands and original archive requirements |
| `docs/` | Data provenance, necessary source audits and verification records |

The original full workflow requires manifest-bound external archives and has not been newly certified on an empty machine. See [the run sequence](FINAL_REVISION_RUN_SEQUENCE/00_README.md). Historical drafts and repeated search outputs are no longer part of the current tree; their commits and recovery are recorded in [BRANCH_HISTORY_SUMMARY.md](BRANCH_HISTORY_SUMMARY.md). See [the cleanup record](docs/REPOSITORY_ORGANIZATION.md) for the current scope.

## Data, License and Citation

See [data sources and terms](docs/DATA_SOURCES.md) and [input notes](Data/README.md). The [MIT License](LICENSE) covers original code only, not third-party data. Cite this fixed version together with the associated paper using [CITATION.cff](CITATION.cff); no DOI is claimed before one is issued.

**Contact:** Yinchen Yi or Yutong Li through GitHub issues.
