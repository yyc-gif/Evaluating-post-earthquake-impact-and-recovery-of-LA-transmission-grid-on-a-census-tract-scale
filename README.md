# Post-Earthquake Power Service Recovery in Los Angeles: Linking Substation Damage, Restoration Logistics, and Tract-Level Disparities

**Paper authors:** Yinchen Yi, Yutong Li, and Marta C. González.

**Repository maintainers:** Yinchen Yi and Yutong Li.

Code, necessary data, frozen numerical results and publication figures for the associated study. The current branch is **`publication/p2-seven-variable`**. `main` is retained unchanged as historical work; all other research branches are consolidated in [BRANCH_HISTORY_SUMMARY.md](BRANCH_HISTORY_SUMMARY.md).

## Adopted Community Typology

The sole primary specification is **seven-variable P2 / saved K3**, with 2,299 positive-population tracts, including eight zero-housing tracts. The 16 zero-population tracts are N/A for clustering; all 2,315 tracts remain in the service model. K4 is retained only as disclosed sensitivity evidence, not a competing primary classification.

- RQ1: `Init_Supply`, spectral `Grid_Impact`, `Redundancy_HHI`.
- RQ2: `B_Unconstrained`, five-policy `MeanDelta`.
- RQ3: FEMA `SOVI_SCORE`, `log1p(Population)`.

The frozen authority is [results/stage7/P2_K3_2299/](results/stage7/P2_K3_2299/); [config/current_stage7.json](config/current_stage7.json) selects it. NCV14 is supplementary environmental-hazard context, **not** a fitted coordinate. This is a graph-based service-recovery workflow, not an electrical power-flow model.

## Installation

Python 3.12 and Git LFS are required:

```bash
git clone --branch publication/p2-seven-variable https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git
cd Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale
git lfs install
git lfs pull
python -m pip install -r requirements.txt
```

## Validate and Reproduce

Validate the adopted saved typology, without fitting or running simulations:

```bash
python src/la_grid/revision/current_stage7.py --verify
python FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/run_08_stage7_typology.py --resume
```

Rebuild the current 17-figure suite, concise captions, mirrors, gallery and 21-page combined packet:

```bash
python src/la_grid/plotting/build_current_suite_k3.py --portable
python -m pytest tests/test_current_figure_suite_integration.py -q
```

Start with [ALL_FIGURES_WITH_CAPTIONS.pdf](results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf) or the [figure gallery](results/figures/FIGURE_REVIEW_GALLERY.html). Figure 7 uses the saved P2/K3 memberships and the approved continuous five-policy burden / frozen vulnerability-quartile display. No composite hotspot score is calculated.

The historical full workflow remains under `FINAL_REVISION_RUN_SEQUENCE/`; Stages 1-7 and 9 still rely on their frozen original inputs and manifest-bound external archives. Full clean-room physical simulation reproduction is not newly certified by this consolidation. Current commands reuse saved results and do not run Monte Carlo, scheduling, GA or K-means.

## Contents

```text
config/current_stage7.json        Sole current typology selector
results/stage7/P2_K3_2299/         Seven-feature authority and saved memberships
results/figure_review/            Current 17 figures and concise combined packet
results/figures/                  Byte-identical mirrors, index and gallery
src/la_grid/                     Scientific, verification and figure-production code
Data/                            Frozen inputs; third-party terms still apply
docs/                            Source documentation and historical diagnostics
BRANCH_HISTORY_SUMMARY.md         One register of retired branch decisions and recovery
```

## Data, License and Citation

See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) and `Data/README.md` for provenance and third-party terms. The [MIT License](LICENSE) covers original repository code only; government, OSM, Census, USGS, FEMA, CEC, CDC and HIFLD data are not automatically relicensed. Cite this fixed commit or a subsequently archived release together with the associated paper using [CITATION.cff](CITATION.cff). No DOI is asserted before one is issued.

**Contact:** Yinchen Yi or Yutong Li through the repository's GitHub issues.
