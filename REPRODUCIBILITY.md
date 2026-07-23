# Reproducibility

## Environment

The recorded environment uses Python 3.12 and the package versions in
`requirements.txt`.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
git lfs install
git lfs pull
```

## Workflow

Run the full workflow with:

```bash
python run_pipeline.py
```

The six ordered stages are:

| Stage | Script |
|---|---|
| `topology` | `Topology_and_Weight.py` |
| `pga` | `IDW.py` |
| `travel` | `build_travel_matrices_osm.py` |
| `analysis` | `C257H_Project_Main.py` |
| `figures` | `Project_Visualizer.py` |
| `composites` | `make_manuscript_composites.py` |

Run a contiguous range with `--from-step` and `--through-step`:

```bash
python run_pipeline.py --from-step travel --through-step figures
python run_pipeline.py --from-step analysis --through-step composites
```

The analysis configuration uses `RNG_SEED = 42`; worker and policy seeds are
derived from that base value. The complete workflow is computationally
intensive, and runtime depends strongly on hardware.

## Key Paths

Required and derived inputs are under `Data/`. The retained numerical outputs
used for verification include:

```text
Data/substation_graph_CEC_nodes_expanded.csv
Data/substation_graph_CEC_edges_expanded.csv
Data/tract_to_substation_mapping_CEC_expanded.csv
Stage 2 Output_expanded/impact_centrality_substations.csv
Stage 3 Output_expanded/tract_kpis_*.csv
Stage 4 Output_expanded/rule_kpis_*.csv
Stage 5 Output_expanded/GA_Schedule_*.csv
Stage 5 Output_expanded/tract_kpis_*.csv
Stage 6 Output_expanded/recovery_curves_all_system.csv
Stage 6 Output_expanded/recovery_kpis_all_system.csv
Stage 7 Output_expanded/clusters_labels_final.csv
Sensitivity Output_clean/Tables/Table_Sensitivity_Summary_2pc50.csv
```

Check that key CSV files exist and can be parsed:

```bash
python -c "import pandas as pd; from pathlib import Path; files=['Data/substation_graph_CEC_nodes_expanded.csv','Data/substation_graph_CEC_edges_expanded.csv','Stage 6 Output_expanded/recovery_kpis_all_system.csv','Stage 7 Output_expanded/clusters_labels_final.csv']; [print(f, pd.read_csv(Path(f)).shape) for f in files]"
```

The retained road graph is `Data/la_drive.graphml`. Normal workflow execution
uses this local file after `git lfs pull`.

## Figure Check

The `composites` stage writes Figures 1-7 to `build/figures/` and does not
modify `Submission_Package/`. The latter contains the retained final figures.

Compare the generated and retained files with SHA-256 hashes:

```python
from hashlib import sha256
from pathlib import Path

root = Path(".")
for retained in sorted((root / "Submission_Package").glob("Figure_[1-7].*")):
    generated = root / "build" / "figures" / retained.name
    if not generated.exists():
        print(f"MISSING: {generated}")
        continue
    same = sha256(retained.read_bytes()).digest() == sha256(generated.read_bytes()).digest()
    print(f"{retained.name}: {'identical' if same else 'review'}")
```

Rendering libraries, fonts, and metadata may prevent byte-for-byte equality.
When hashes differ, inspect the figures and compare their supporting CSV
values.
