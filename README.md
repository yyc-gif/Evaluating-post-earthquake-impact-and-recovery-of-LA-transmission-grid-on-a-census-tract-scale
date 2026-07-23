# Post-Earthquake Power Service Recovery in Los Angeles: Linking Substation Damage, Restoration Logistics, and Tract-Level Disparities

This repository contains the code, necessary data, retained numerical outputs,
and final figures associated with the paper.

**Paper authors:** Yinchen Yi, Yutong Li, and Marta C. González

**Repository maintainers:** Yinchen Yi and Yutong Li

This repository provides a graph-based service-recovery workflow and does not
implement electrical power-flow analysis.

## Installation

The recorded environment uses Python 3.12. Large files are managed with Git
LFS.

```bash
git clone https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git
cd Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale
git lfs install
git lfs pull
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running The Workflow

Show the available stages:

```bash
python run_pipeline.py --help
```

Run all six stages:

```bash
python run_pipeline.py
```

Run a contiguous subset:

```bash
python run_pipeline.py --from-step analysis
python run_pipeline.py --from-step analysis --through-step composites
```

The ordered stage names are `topology`, `pga`, `travel`, `analysis`, `figures`,
and `composites`. Operational details and output checks are in
[REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Repository Structure

```text
Data/                         Required and derived workflow data
Stage 1 Output_expanded/      Retained stage outputs
...
Stage 7 Output_expanded/      Retained stage outputs
Sensitivity Output_clean/     Retained sensitivity summaries
Submission_Package/           Final Figures 1-7
docs/DATA_SOURCES.md           Data attribution and reuse notes
run_pipeline.py                Workflow entry point
requirements.txt               Pinned Python dependencies
```

Reproduction figures are written to `build/figures/`; automated scripts do not
write to `Submission_Package/`.

## Data And Licensing

Data sources, attribution, provider terms, and redistribution notes are listed
in [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) and
[Data/README.md](Data/README.md).

Original code is released under the [MIT License](LICENSE). The license does
not replace or override the terms that apply to third-party data.

## Citation

Citation metadata are provided in [CITATION.cff](CITATION.cff). No publication
DOI or final journal metadata are asserted before formal assignment.

## Contact

For reproducibility questions, open an issue in the
[GitHub repository](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/issues).
