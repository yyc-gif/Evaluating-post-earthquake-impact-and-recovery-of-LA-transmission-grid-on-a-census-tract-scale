# Evaluating Post-Earthquake Impact and Recovery of the LA Transmission Grid

**Authors:** Yinchen Yi and Yutong Li

This repository contains the scripts, required data, and generated results for a
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

## Official Workflow

The five `*_expanded.py` files are the manuscript entry points. The files
without `_expanded` are their shared implementations and must remain beside
them; they are not duplicate obsolete workflows.

Run the pipeline from the repository root in this order:

```bash
python Topology_and_Weight_expanded.py
python IDW_expanded.py
python build_travel_matrices_osm_expanded.py
python C257H_Project_Main_expanded.py
python Project_Visualizer_expanded.py
```

The stages perform the following tasks:

1. Build and validate the reduced substation topology and tract dependency map.
2. Interpolate scenario PGA fields to substations.
3. Build crew-base-to-task and task-to-task road travel-time matrices.
4. Run damage, source-gated recovery, restoration scheduling, sensitivity, and
   tract clustering analyses.
5. Regenerate stage-level visualizations.

Final manuscript composites are regenerated separately with:

```bash
python make_manuscript_composites.py
```

## Repository Contents

- `Topology_and_Weight.py`, `topology_outputs.py`, and
  `topology_visualization.py`: topology construction, export, and validation.
- `IDW.py`: PGA interpolation.
- `build_travel_matrices_osm.py`: OSM travel-time matrix construction.
- `C257H_Project_Main.py`: damage, service, recovery, scheduling, GA, metrics,
  sensitivity, and clustering calculations.
- `Project_Visualizer.py`: stage-level maps and plots.
- `*_expanded.py`: manuscript configuration wrappers and official entry points.
- `strategy_names.py`: canonical strategy IDs and display labels.
- `build_sensitivity_outputs.py`: Figure 7 and sensitivity-table outputs.
- `make_methodology_workflow_figure.py` and
  `make_manuscript_composites.py`: final manuscript figure assembly.
- `Data/`: required inputs and processed topology/mapping files.
- `Stage 1 Output_expanded/` through `Stage 7 Output_expanded/`: retained
  numerical and graphical results from the manuscript workflow.
- `Sensitivity Output_clean/`: retained sensitivity figures and tables.
- `Manuscript_Figures/`: final composite manuscript figures.

Generated caches, logs, one-off mechanism experiments, audit/debug files,
downloaded literature PDFs, and intermediate composite panels are intentionally
excluded from version control.

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
