# From Substation Damage to Community Recovery: Tract-Level Assessment of Post-Earthquake Power-Service Restoration in Los Angeles

This repository is the paper companion for a census-tract-scale study of
post-earthquake electric-power service disruption and restoration in the Los
Angeles study area. It contains the analysis scripts, documented inputs,
retained numerical results, and frozen paper assets used for the manuscript.

## Associated Publication

**Title:** *From Substation Damage to Community Recovery: Tract-Level
Assessment of Post-Earthquake Power-Service Restoration in Los Angeles*

**Authors:** Yinchen Yi, Yutong Li, and Marta C. González

The associated article has not yet received final journal bibliographic
metadata or a DOI. When citing this repository, please cite both the archived
software release and the associated article once its publication details are
available.

## Repository Maintainers

Repository maintainers: Yinchen Yi and Yutong Li

The publication author list and the repository maintainer list describe
different roles and should not be treated as interchangeable.

## Model Scope

The workflow combines a reduced transmission/substation topology,
scenario-based substation damage, tract-to-substation dependency weights,
active-source connectivity, road-network travel times, and rule-based or
genetic-algorithm restoration schedules.

The following scope limitations are central to interpreting the results:

- This is a graph-connectivity and service-propagation framework.
- It is not an AC/DC power-flow, voltage-stability, or generation-dispatch
  model.
- Tract service availability is a modeled proxy derived from tract-substation
  dependency weights and source-gated substation functionality.
- The travel network represents static pre-event road conditions and does not
  model earthquake-induced road disruption or time-varying congestion.
- Results depend on the fragility, source-gate, repair-duration, tract-mapping,
  crew, and scheduling assumptions documented in the manuscript.
- Recovery curves represent modeled power-service restoration rather than only
  physical repair completion.

## Repository Contents

- `run_pipeline.py`: stable entry point for the ordered manuscript workflow.
- `Topology_and_Weight.py`, `topology_outputs.py`, and
  `topology_visualization.py`: topology construction, export, and validation.
- `IDW.py`: scenario PGA interpolation to substations.
- `build_travel_matrices_osm.py`: road-network travel-time matrices.
- `C257H_Project_Main.py`: damage, service, recovery, scheduling, GA,
  sensitivity, metrics, and clustering analyses.
- `Project_Visualizer.py`: stage-level maps and plots.
- `make_manuscript_composites.py`: assembles or stages Figures 1-7 in
  `build/figures/` without writing to the frozen submission directory.
- `build_sensitivity_outputs.py`: sensitivity plots and tables used by the
  analysis stage.
- `Data/`: source-like study inputs and derived workflow inputs.
- `Stage 1 Output_expanded/` through `Stage 7 Output_expanded/`: retained
  numerical outputs supporting the manuscript findings.
- `Sensitivity Output_clean/Tables/`: retained sensitivity summaries.
- `Submission_Package/`: frozen manuscript-submission snapshot containing
  Figures 1-7, the supplementary PDF, and the currently retained editable
  manuscript file. Automated scripts do not overwrite this directory.
- `docs/DATA_SOURCES.md`: data provenance, terms, and redistribution notes.
- `REPRODUCIBILITY.md`: detailed reproduction procedure and expected outputs.
- `RELEASE_CHECKLIST.md`: steps for freezing and archiving a citable release.

Stage-level plots, row-level Monte Carlo records, caches, logs, one-off
mechanism experiments, and audit/debug outputs are excluded where they can be
regenerated. The 2pc50 graph-robustness trajectories are retained because they
are direct numerical inputs to Figure 5.

## Installation

The recorded environment uses Python 3.12. Large inputs and results are stored
with Git LFS.

```bash
git clone https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale.git
cd Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale
git lfs install
git lfs pull
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Geospatial packages may be easier to install in a Conda environment on
Windows. The pinned versions in `requirements.txt` record the manuscript
environment.

## Quick Start

Inspect the available workflow bounds:

```bash
python run_pipeline.py --help
```

Run the complete workflow:

```bash
python run_pipeline.py
```

The complete workflow is computationally intensive. Runtime depends strongly
on hardware and has not been re-timed for this publication-repository cleanup.

## Reproducing Manuscript Results

The six ordered workflow steps are:

1. `topology`
2. `pga`
3. `travel`
4. `analysis`
5. `figures`
6. `composites`

Run a contiguous portion of the workflow with, for example:

```bash
python run_pipeline.py --from-step analysis
python run_pipeline.py --from-step analysis --through-step composites
```

The final command stages reproduction versions of Figures 1-7 in the ignored
`build/figures/` directory. It does not overwrite the frozen files in
`Submission_Package/`. Detailed output mappings, reproducibility caveats, and
comparison instructions are provided in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).
Starting directly at `figures` or `composites` assumes that required analysis
and sensitivity source outputs already exist from an earlier run.

## Data Sources and Licensing

Major inputs include OpenStreetMap, California Energy Commission, California
Geological Survey, USGS, FEMA, U.S. Census Bureau, CDC/ATSDR, HIFLD, and City
of Los Angeles products. A repository copy or derivative does not change the
original provider's ownership, license, attribution, or redistribution terms.

See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) and
[Data/README.md](Data/README.md) before reusing or redistributing any data.

## Selected Methodological References

- Cheng, B., Nozick, L., Dobson, I., Davidson, R., Obiang, D., Dias, J., &
  Granados, M. (2024). Quantifying the earthquake risk to the electric power
  transmission system in Los Angeles at the census tract level. *IEEE Access*.
  <https://doi.org/10.1109/ACCESS.2024.3408797>
- Cagnan, Z., Davidson, R. A., & Guikema, S. D. (2006). Post-earthquake
  restoration planning for Los Angeles electric power. *Earthquake Spectra*,
  22(3), 589-608. <https://doi.org/10.1193/1.2222400>
- Xu, N., Guikema, S. D., Davidson, R. A., Nozick, L. K., Cagnan, Z., & Vaziri,
  K. (2007). Optimizing scheduling of post-earthquake electric power
  restoration tasks. *Earthquake Engineering & Structural Dynamics*, 36(3),
  265-284. <https://doi.org/10.1002/eqe.623>
- Cavdaroglu, B., Hammel, E., Mitchell, J. E., Sharkey, T. C., & Wallace, W. A.
  (2013). Integrating restoration and scheduling decisions for disrupted
  interdependent infrastructure systems. *Annals of Operations Research*,
  203(1), 279-294. <https://doi.org/10.1007/s10479-011-0959-3>

## Citation

Citation metadata are provided in [CITATION.cff](CITATION.cff). The file lists
the repository software contributors separately from the three authors of the
preferred article citation. Journal, DOI, volume, issue, and page metadata will
be added only after they are formally assigned.

## License

Original code in this repository is released under the
[MIT License](LICENSE).

The MIT License applies only to original repository code. It does not
automatically cover third-party government, OpenStreetMap, Census, USGS, FEMA,
CEC, CDC/ATSDR, HIFLD, or City of Los Angeles data. Those materials remain
subject to their original providers' licenses, attribution requirements, and
terms of use.

## Contact

For reproducibility questions or repository issues, please open an issue in
the [GitHub repository](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/issues).
