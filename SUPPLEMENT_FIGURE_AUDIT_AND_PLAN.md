# Supplement figure audit and plan

The supplement is organized by scientific topic, not reviewer number. It uses the July 92-station/318-edge model and frozen `Formal_Experiment_20260923` results. Plotting-only scripts generated 20 paired PNG/PDF figures and 26 source/summary table files in `Supplement_Rebuild_20260925/`; no DS draw, scheduler, GA, or recovery trajectory was run. `SUPPLEMENT_FIGURE_INVENTORY.csv` gives each proposed item, path, status, dependencies, and manuscript relevance. `SUPPLEMENT_CAPTIONS_DRAFT.md` gives draft captions.

| Section | Recommended material | State |
| --- | --- | --- |
| S1 Damage and initial conditions | Four-hazard DS severity (S1); initial service CDF/spatial panels | Ready. Four-hazard initial tract values were projected from the 4,000 frozen unconstrained event archives and frozen M1 weights, with no model rerun. |
| S2 Restoration setup | 92×92 directed travel matrix (S2a); historical unconstrained T80 maps | Ready. T80 maps are conditional means among realizations reaching the threshold; unreached fractions remain in the source table. |
| S3 Mapping methodology and robustness | 337-tract conditional SCE public-candidate benchmark (S3a), M1−M0 paired outcome (S3b), cutoff/common320 tables (S3c), cutoff figure (S3d) | Ready. 480 strict-SCE tracts without directly representable official candidates remain a coverage limitation. External consistency is not feeder-truth accuracy. |
| S4 Source-gate and dynamic paths | Self/threshold/source-path burden (S4a), source-loss concentration plus full dynamic topology table (S4b), no-threshold equivalence (S4c) | Ready. These are source-connected service-proxy/topological diagnostics, not power-flow validation. |
| S5 GA reproducibility | Five-seed retained-fitness curves and incumbent table (S5) | Ready. The direct-community sequence equals impact-first; no separate GA improvement is claimed. |
| S6 Full strategies/resources | 36,000 baseline-trajectory, all-hazard/all-strategy table (S6a); OFAT resource effects (S6b) | Ready. Additional vulnerability-first results are shown in S7; do not mistake nine baseline trajectories for nine independent decisions. |
| S7 Distributional and equity-informed comparator | Existing frozen equity-efficiency, quartile absolute burden, tract effects, resource sensitivity figures plus paired/group/classification tables | Ready. Vulnerability-first is targeted, not equity-optimal; show absolute quartile outcomes alongside gap/Gini. |
| S8 Typology, PCA, clustering, hotspots | Formal PCA scree/loadings, K-means elbow, cluster map, hotspot-screen map, profiles/robustness tables | Ready. These are descriptive; neither map establishes causal mechanisms. |

There is no identified `SCIENCE_RERUN_REQUIRED` supplement figure. The S1/S2 figures use actual frozen 1,000-realization trajectories, not the small 2pc50 `MC_Tract_Supply_2pc50.csv` as a substitute for four hazards. No new percolation, legacy GA-Balanced, or SVI-weighted-equity panels are proposed.

Before final assembly, decide which of the 20 ready figures are in main text versus supplement to avoid duplicates; the inventory marks candidates. Tables may be condensed for typesetting, but the CSV source values should remain unchanged. Each generated PDF should be visually checked at final journal page size. Contact sheets and the three newly projected maps/CDF were inspected for clipping and gross layout defects.
