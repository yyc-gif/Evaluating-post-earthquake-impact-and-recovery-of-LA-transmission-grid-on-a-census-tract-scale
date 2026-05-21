# Evaluating Post-Earthquake Impact and Recovery of the LA Transmission Grid

This repository contains the full project workspace for evaluating post-earthquake impact and recovery of the Los Angeles transmission grid on a census-tract scale.

The repository includes:

- topology construction and validation scripts,
- PGA interpolation and tract-to-substation mapping,
- Monte Carlo fragility and source-gated recovery simulation,
- rule-based and GA repair scheduling experiments,
- expanded-area outputs and visualization products,
- data files required by the current workflow.

Large data and generated output files are tracked with Git LFS. After cloning, run:

```bash
git lfs pull
```

Main entry points:

```bash
python Topology_and_Weight_expanded.py
python IDW_expanded.py
python build_travel_matrices_osm_expanded.py
python C257H_Project_Main_expanded.py
python Project_Visualizer_expanded.py
```

