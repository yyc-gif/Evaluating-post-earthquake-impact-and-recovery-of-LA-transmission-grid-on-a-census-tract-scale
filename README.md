# Evaluating Post-Earthquake Impact and Recovery of the LA Transmission Grid

**Authors:** Yinchen Yi and Yutong Li

This repository contains the scripts, required data, and retained results for a
census-tract-scale study of post-earthquake electric-power service disruption
and restoration in the Los Angeles study area. The model combines a reduced
transmission/substation topology, scenario-based substation damage, tract-to-
substation dependency weights, active-source connectivity, road-network travel
times, and rule-based or genetic-algorithm restoration schedules.

> **Model scope:** Network robustness and service propagation are represented
> with graph-connectivity proxies. The workflow is not an AC/DC power-flow,
> voltage-stability, or generation-dispatch model.

Large data and result files are stored with Git LFS. After cloning, retrieve
them before running the workflow:

```bash
git lfs pull
```

## Environment

The project was run with Python 3.12. Install the recorded dependencies with:

```bash
python -m pip install -r requirements.txt
```

For geospatial packages, a Conda environment may be easier on Windows. The
versions in `requirements.txt` record the environment used for the manuscript
results.

## Quick Start

The complete manuscript workflow has one public entry point:

```bash
python run_pipeline.py
```

The workflow is computationally intensive. To resume at a later step, use:

```bash
python run_pipeline.py --from-step analysis
python run_pipeline.py --from-step figures --through-step composites
```

The ordered steps are `topology`, `pga`, `travel`, `analysis`, `figures`, and
`composites`. The integrated analysis step includes the sensitivity runs.

## Workflow Files

The repository contains one manuscript workflow. Its stages can also be run
individually:

```bash
python Topology_and_Weight.py
python IDW.py
python build_travel_matrices_osm.py
python C257H_Project_Main.py
python Project_Visualizer.py
```

The stages perform the following tasks:

1. Build and validate the reduced substation topology and tract dependency map.
2. Interpolate scenario PGA fields to substations.
3. Build crew-base-to-task and task-to-task road travel-time matrices.
4. Run damage, source-gated recovery, restoration scheduling, sensitivity, and
   tract clustering analyses.
5. Regenerate stage-level visualizations and final manuscript composites.

Numbered reproduction figures are generated in the ignored `build/figures/`
directory with:

```bash
python make_manuscript_composites.py
```

## Repository Layout

- `run_pipeline.py`: single entry point for the complete workflow.
- `Topology_and_Weight.py`, `topology_outputs.py`, and
  `topology_visualization.py`: topology construction, export, and validation.
- `IDW.py`: PGA interpolation.
- `build_travel_matrices_osm.py`: OSM travel-time matrix construction.
- `C257H_Project_Main.py`: damage, service, recovery, scheduling, GA, metrics,
  sensitivity, and clustering calculations.
- `Project_Visualizer.py`: stage-level maps and plots.
- `strategy_names.py`: canonical strategy IDs and display labels.
- `build_sensitivity_outputs.py`: Figure 7 and sensitivity-table outputs.
- `make_manuscript_composites.py`: assembles numbered reproduction figures in
  `build/figures/` without overwriting the frozen submission files.
- `Data/`: required inputs and processed topology/mapping files.
- `Stage 1 Output_expanded/` through `Stage 7 Output_expanded/`: retained
  numerical results used to check the manuscript findings.
- `Sensitivity Output_clean/Tables/`: retained sensitivity summaries.
- `Submission_Package/`: the single authoritative, frozen location for the
  manuscript, Figures 1-7, and the supplementary PDF prepared for submission.

Stage-level plots, Gantt images, row-level Monte Carlo records, caches, logs,
one-off mechanism experiments, and audit/debug files are reproducible and
intentionally excluded from version control. The 2pc50 graph-robustness
trajectories are retained because they are direct numerical inputs to Figure 5;
other graph-robustness intermediates remain excluded. The final paper figures
are available in `Submission_Package/`.

## Main Data Sources

- [OpenStreetMap road network](https://www.openstreetmap.org/)
- [California Energy Commission transmission lines](https://gis.data.ca.gov/datasets/CAEnergy::california-electric-transmission-lines-1/about)
- [California Energy Commission substations](https://hub.arcgis.com/datasets/c2d4e65fe7b84c67a94e98ff9555c3ac_0)
- [California Geological Survey Map Sheet 48](https://www.conservation.ca.gov/cgs/publications/ms48)
- [USGS ShakeMap](https://earthquake.usgs.gov/data/shakemap/)
- [FEMA National Risk Index](https://www.fema.gov/flood-maps/products-tools/national-risk-index)
- [US Census TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)
- [US Census ACS](https://api.census.gov/data.html)
- [CDC/ATSDR Social Vulnerability Index](https://www.atsdr.cdc.gov/place-health/php/svi/index.html)
- [HIFLD electric substations](https://catalog.data.gov/dataset/electric-substations)
- [City of Los Angeles GeoHub](https://geohub.lacity.org/)

## Important Limitations

- Tract service availability depends on the tract-substation weighting model
  and its distance-decay and threshold assumptions.
- Recovery curves represent modeled service restoration, not only physical
  repair completion.
- Travel times use a static pre-event road network and simplified crew/task
  abstractions.
- Results depend on fragility, restoration-time, active-source, and repair-task
  assumptions documented in the associated manuscript.

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
