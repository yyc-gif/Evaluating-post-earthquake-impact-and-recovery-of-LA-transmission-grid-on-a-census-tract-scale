## October 2026 revision

The current working version is on `revision/reviewer-driven-core-rebuild-v2`.

**Current figure review: [results/figure_review/](results/figure_review/)** — one current set, with all figures and captions in [ALL_FIGURES_WITH_CAPTIONS.pdf](results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf).

`main` and `archive/ijdrr-submission-20260722` retain the July history. Earlier experimental branches are preserved as archive tags.

---

# Evaluating Post-Earthquake Impact and Recovery of the LA Transmission Grid

**Authors:** Yinchen Yi and Yutong Li

This repository contains the scripts, required data, and generated results for a
census-tract-scale study of post-earthquake electric-power service disruption
and restoration in the Los Angeles study area. The model combines a reduced
transmission/substation topology, scenario-based substation damage, tract-to-
substation dependency weights, active-source connectivity, road-network travel
times, and rule-based or genetic-algorithm restoration schedules.

Final reviewer-revision workflow:
FINAL_REVISION_RUN_SEQUENCE/00_README.md

Run the final reviewer-revision workflow:
```bash
python FINAL_REVISION_RUN_SEQUENCE/run_all.py --resume
```

Run or validate an individual stage (example):
```bash
python FINAL_REVISION_RUN_SEQUENCE/09_CAPACITY_ROBUSTNESS/run_09_capacity_robustness.py --resume
```

Current complete figure gallery: `results/figures/FIGURE_REVIEW_GALLERY.html`
Scientific implementation: `src/la_grid/`
Final numerical results: `results/`

`--resume` is the currently certified reproduction mode. Full `--from-scratch`
reproduction is not yet certified because several frozen trajectory and offline
archives are maintained externally and are validated through the canonical
external-archive manifest.

> **Model scope:** Network robustness and service propagation are represented
> with graph-connectivity proxies. The workflow is not an AC/DC power-flow,
> voltage-stability, or generation-dispatch model.

Tracked large files use Git LFS; registered trajectory/offline archives and the revised viewing suite are local external archives rather than Git objects. After cloning, retrieve tracked LFS objects and restore the external archives listed in the canonical manifest:

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

## Legacy / Original July Manuscript Workflow

The five `*_expanded.py` files describe the original July manuscript workflow.
They are retained under `src/la_grid/core/legacy_entrypoints/` for history and
are not the canonical entry point for the final reviewer revision. Their shared
implementations are under `src/la_grid/core/`.

Shared July implementation modules are in `src/la_grid/core/`; plotting tools are in `src/la_grid/plotting/`.

## Repository Contents

- `FINAL_REVISION_RUN_SEQUENCE/`: sole canonical reviewer-revision validation/reuse entry point.
- `src/la_grid/`: package containing core, revision, diagnostics, plotting, and utility code.
- `config/parent_frozen_design/`: unchanged parent frozen experiment matrix.
- `Data/`: PATH_FROZEN model inputs plus the ignored local-only `external_validation/` evidence directory.
- `Formal_Experiment_20260923/`: PATH_FROZEN mixed formal archive; logical result indexes are under `results/formal/`, `results/vulnerability/`, and `results/stage7/`.
- `results/formal/`, `results/revised_suite/`, `results/figures/`, `results/capacity/`, and `results/diagnostics/`: organized formal archives and final result collections.
- `data/travel/`: the two active frozen directed travel matrices; historical stage outputs are under `provenance/legacy_outputs/`.
- `docs/`: methodology, reviewer, data-research, meeting, and reproducibility records.
- `provenance/`: legacy and reviewer-working records retained for traceability.
- `tests/`: reviewer-revision tests.

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
