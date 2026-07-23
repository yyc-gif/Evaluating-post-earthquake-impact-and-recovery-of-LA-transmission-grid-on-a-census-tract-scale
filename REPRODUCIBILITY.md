# Reproducibility Guide

## Tested Environment

The manuscript workflow was run with Python 3.12. Install the pinned Python
dependencies from `requirements.txt`.

```bash
python -m pip install -r requirements.txt
```

Large data, results, and paper assets are tracked with Git LFS. After cloning,
install Git LFS and retrieve the objects before running any stage:

```bash
git lfs install
git lfs pull
```

## Workflow Entry Point

The complete entry point is:

```bash
python run_pipeline.py
```

The workflow executes six ordered stages:

| Step | Script | Main purpose |
|---|---|---|
| `topology` | `Topology_and_Weight.py` | Build and validate the physical and reduced substation topology and tract dependency mapping |
| `pga` | `IDW.py` | Interpolate scenario PGA fields to substations |
| `travel` | `build_travel_matrices_osm.py` | Build crew-base-to-task and task-to-task travel-time matrices |
| `analysis` | `C257H_Project_Main.py` | Run damage, source-gated recovery, restoration strategies, GA, sensitivity analysis, metrics, and tract clustering |
| `figures` | `Project_Visualizer.py` | Generate stage-level source figures |
| `composites` | `make_manuscript_composites.py` | Assemble or stage numbered paper figures in `build/figures/` |

Use `--from-step` and `--through-step` to execute a contiguous subset:

```bash
python run_pipeline.py --from-step analysis
python run_pipeline.py --from-step travel --through-step figures
python run_pipeline.py --from-step analysis --through-step composites
```

`--from-step` must not come after `--through-step` in the ordered list above.
Starting at `figures` or `composites` is valid only when the required analysis,
sensitivity, and source-figure files already exist from an earlier run.

## Computational Scope and Randomness

The complete workflow includes 1,000 Monte Carlo samples per scenario and
genetic-algorithm optimization. Runtime depends strongly on hardware and has
not been re-timed during publication-repository preparation.

The analysis configuration uses a fixed base random seed (`RNG_SEED = 42`).
Worker-level Monte Carlo seeds and policy/scenario GA seeds are derived
deterministically from that base. Small numerical differences may still arise
from parallel execution, numerical-library or platform differences, and
changes in third-party network data or geospatial libraries.

The normal travel-matrix stage reads the retained pre-event road graph from
`Data/la_drive.graphml`; it does not download a new OSM graph. Network access is
required to clone the repository and retrieve Git LFS objects. Rebuilding the
road graph from a newer OpenStreetMap snapshot is outside the current workflow
and may change travel times.

## Principal Validation Outputs

The following retained files provide the main numerical checks behind the
manuscript:

- `Data/substation_graph_CEC_nodes_expanded.csv`
- `Data/substation_graph_CEC_edges_expanded.csv`
- `Data/tract_to_substation_mapping_CEC_expanded.csv`
- `Stage 2 Output_expanded/impact_centrality_substations.csv`
- `Stage 3 Output_expanded/tract_kpis_*.csv`
- `Stage 4 Output_expanded/rule_kpis_pop_*.csv`
- `Stage 4 Output_expanded/rule_kpis_svi_*.csv`
- `Stage 5 Output_expanded/GA_Schedule_*.csv`
- `Stage 5 Output_expanded/tract_kpis_*.csv`
- `Stage 6 Output_expanded/recovery_curves_all_system.csv`
- `Stage 6 Output_expanded/recovery_kpis_all_system.csv`
- `Stage 7 Output_expanded/clusters_labels_final.csv`
- `Stage 7 Output_expanded/stage7_cluster_profiles_raw_values.csv`
- `Sensitivity Output_clean/Tables/Table_Sensitivity_Summary_2pc50.csv`

## Paper Figures

The complete workflow writes reproduction assets to the ignored directory:

```text
build/figures/
    Figure_1.pdf
    Figure_2.png
    Figure_3.png
    Figure_4.png
    Figure_5.png
    Figure_6.png
    Figure_7.png
```

Figure 1 is staged from the frozen workflow diagram. Figures 2, 3, 5, and 6
are assembled from current generated panels. Figure 4 is copied from the
current Stage 4 crew-base map, and Figure 7 is copied from the current
sensitivity-analysis figure. These copy operations do not alter image content.

`Submission_Package/` contains the frozen submission versions. No workflow
script writes to or overwrites that directory.

To compare a new build with the frozen files, first check that all expected
files exist, then compare cryptographic hashes for byte-identical files:

```python
from hashlib import sha256
from pathlib import Path

root = Path(".")
for frozen in sorted((root / "Submission_Package").glob("Figure_[1-7].*")):
    built = root / "build" / "figures" / frozen.name
    if not built.exists():
        print(f"MISSING: {built}")
        continue
    frozen_hash = sha256(frozen.read_bytes()).hexdigest()
    built_hash = sha256(built.read_bytes()).hexdigest()
    print(f"{frozen.name}: {'identical' if frozen_hash == built_hash else 'review'}")
```

A non-identical image is not automatically a failed reproduction. Rendering
backends, fonts, platform libraries, and metadata can change file bytes or
individual pixels. The repository does not promise pixel-for-pixel identity;
the key numerical summaries, qualitative curves, and strategy ordering should
remain consistent with the frozen manuscript results.

## Safe Reproduction Practice

1. Start from a clean checkout of a tagged release.
2. Run `git lfs pull` and confirm required files are not LFS pointer text.
3. Record the Python version, platform, dependency versions, commit SHA, and
   command used.
4. Run only the stages needed for the intended check.
5. Keep generated outputs separate from `Submission_Package/`.
6. Compare key CSV statistics and strategy rankings before comparing figure
   rendering details.
