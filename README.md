# Evaluating Post-Earthquake Impact and Recovery of the LA Transmission Grid

**Team:** Yinchen Yi, Yutong Li

This repository contains a census-tract-scale modeling pipeline for evaluating post-earthquake impact and recovery of the Los Angeles transmission grid. The workflow simulates earthquake-induced substation damage, propagates disruption to tract-level service through a tract-substation weighting matrix, and compares restoration strategies under network, population, and equity-aware objectives.

The current project version uses an expanded Los Angeles study area and a source-gated recovery model. Large data files and generated outputs are tracked with Git LFS.

```bash
git lfs pull
```

> Scope note: robustness metrics are graph-connectivity proxies. They do not enforce AC/DC power-flow feasibility, voltage constraints, or dispatch feasibility unless those modules are added separately.

## Workflow

1. Construct the substation-level transmission topology from transmission line and substation data using endpoint snapping, line splitting at substations, attribute-compatible line joins, and graph extraction of direct substation links.
2. Build the tract-substation weighting matrix (`W`) using inverse-distance weighting and tract-substation mapping exports.
3. Interpolate scenario PGA fields to substations.
4. Run scenario-based stress tests for Northridge, San Fernando, Long Beach, and a 2%-in-50-years probabilistic ground-motion scenario.
5. Sample probabilistic substation damage states using lognormal fragility curves and Monte Carlo simulation.
6. Estimate tract-level service through the `W` matrix with active-source-gate connectivity logic.
7. Simulate recovery under baseline, rule-based, and GA-based logistics-aware restoration policies.
8. Compare strategies using service restoration, connectivity robustness, scheduling, and equity-aware metrics.
9. Run PCA and K-means clustering to identify tract resilience typologies from recovery, network, and socioeconomic features.

## Repository Structure

- `Topology_and_Weight.py` and `Topology_and_Weight_expanded.py` - Build the transmission topology, validate direct substation links, and export substation graph plus tract-substation mapping files.
- `topology_outputs.py` - Topology export helpers.
- `topology_visualization.py` - Static and interactive topology validation plotting helpers.
- `IDW.py` and `IDW_expanded.py` - Interpolate PGA scenario grids to substations.
- `build_travel_matrices_osm.py` and `build_travel_matrices_osm_expanded.py` - Build depot-to-task and task-to-task travel-time matrices from the OSM road graph.
- `C257H_Project_Main.py` and `C257H_Project_Main_expanded.py` - End-to-end impact, recovery, scheduling, GA, KPI, and clustering pipeline.
- `Project_Visualizer.py` and `Project_Visualizer_expanded.py` - Generate maps, recovery curves, Gantt charts, logistics heatmaps, KPI plots, and Stage 7 clustering figures.
- `Data/` - Required input data and intermediate mapping/topology files.
- `Stage 1 Output_expanded/` through `Stage 7 Output_expanded/` - Expanded-area pipeline outputs.
- `Sensitivity Output_clean/` - Validated `2pc50`-only sensitivity figures and tables.

## Quickstart

Run the expanded workflow in this order:

```bash
python Topology_and_Weight_expanded.py
python IDW_expanded.py
python build_travel_matrices_osm_expanded.py
python C257H_Project_Main_expanded.py
python Project_Visualizer_expanded.py
```

The non-expanded scripts are retained for the original baseline workflow, but the expanded scripts are the current main entry points.

## Inputs

The repository expects the required datasets in `Data/`. Main data sources include:

- OpenStreetMap contributors, road network data: <https://www.openstreetmap.org/>
- California Energy Commission GIS transmission lines: <https://gis.data.ca.gov/datasets/CAEnergy::california-electric-transmission-lines-1/about>
- California Energy Commission GIS electric substations: <https://hub.arcgis.com/datasets/c2d4e65fe7b84c67a94e98ff9555c3ac_0>
- California Geological Survey Map Sheet 48, 2%-in-50-years ground motion: <https://www.conservation.ca.gov/cgs/publications/ms48>
- USGS ShakeMap PGA scenarios: <https://earthquake.usgs.gov/data/shakemap/>
- FEMA National Risk Index: <https://www.fema.gov/flood-maps/products-tools/national-risk-index>
- US Census TIGER/Line tract boundaries: <https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html>
- US Census ACS 5-year estimates: <https://api.census.gov/data.html>
- CDC/ATSDR Social Vulnerability Index: <https://www.atsdr.cdc.gov/place-health/php/svi/index.html>
- HIFLD electric substations: <https://catalog.data.gov/dataset/electric-substations>
- City of Los Angeles GeoHub boundary layers: <https://geohub.lacity.org/>

## Outputs

Depending on the enabled stages, the pipeline exports:

- substation-level PGA and damage-state Monte Carlo outputs,
- tract-level initial service and recovery trajectories,
- source-gated recovery curves and system KPIs,
- substation graph edges/nodes and topology diagnostics,
- network centrality, percolation, and robustness outputs,
- travel-time matrices for multi-depot and multi-crew scheduling,
- rule-based and GA repair schedules,
- Gantt charts and logistics heatmaps,
- population-weighted and SVI-weighted recovery comparisons,
- PCA, K-means, cluster-label, and tract-typology outputs,
- publication-oriented maps and summary figures.

## Limitations

- The transmission network is represented as a topology graph, not a full power-flow model.
- Tract service estimates depend on the tract-substation weighting matrix and its distance-decay assumptions.
- Restoration curves represent supply/functionality recovery, not only physical repair completion.
- Logistics-aware scheduling uses road-network travel-time matrices and simplified crew/task abstractions.
- Results are sensitive to fragility parameters, recovery-curve assumptions, active-source definitions, and repair-task filtering thresholds.

## Citation

- Cheng, B., Nozick, L., Dobson, I., Davidson, R., Obiang, D., Dias, J., & Granados, M. (2024). Quantifying the earthquake risk to the electric power transmission system in Los Angeles at the census tract level. *IEEE Access*. <https://doi.org/10.1109/ACCESS.2024.3408797>
- Cagnan, Z., Davidson, R. A., & Guikema, S. D. (2006). Post-earthquake restoration planning for Los Angeles electric power. *Earthquake Spectra*, 22(3), 589-608. <https://doi.org/10.1193/1.2222400>
- Xu, N., Guikema, S. D., Davidson, R. A., Nozick, L. K., Cagnan, Z., & Vaziri, K. (2007). Optimizing scheduling of post-earthquake electric power restoration tasks. *Earthquake Engineering & Structural Dynamics*, 36(3), 265-284. <https://doi.org/10.1002/eqe.623>
- Cavdaroglu, B., Hammel, E., Mitchell, J. E., Sharkey, T. C., & Wallace, W. A. (2013). Integrating restoration and scheduling decisions for disrupted interdependent infrastructure systems. *Annals of Operations Research*, 203(1), 279-294. <https://doi.org/10.1007/s10479-011-0959-3>
