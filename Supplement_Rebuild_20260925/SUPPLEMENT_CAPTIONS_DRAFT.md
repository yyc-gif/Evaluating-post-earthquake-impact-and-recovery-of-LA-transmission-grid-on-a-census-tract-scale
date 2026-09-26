# Supplement caption drafts

**S1. Damage-state severity across four hazards.** Mean counts of stations in DS0–DS4 across the 1,000 frozen evaluation realizations per hazard. These are model draws, not observed earthquake damage. Source: `Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_*.npz`; `Supplement_Rebuild_20260925/Tables/S1_DAMAGE_STATE_COUNTS.csv`.

**S3a. SCE public-candidate consistency on 337 comparable tracts.** Agreement with public SCE circuit/substation candidate evidence, conditional on 337 strict-SCE tracts whose direct official candidate is representable among the July 92 stations. The other 480 strict-SCE tracts are a coverage limitation. Candidate evidence is not customer-feeder ground truth. Source: `R1_Comment1_2_External_Evidence_20260922/SCE_MAPPING_BENCHMARK_SUMMARY.csv`; `Supplement_Rebuild_20260925/Tables/S3_SCE_337_CANDIDATE_BENCHMARK.csv`.

**S3b. Paired M1 minus M0 outcomes by hazard.** Mean within-realization difference under Hospital-first, holding frozen station states and schedules fixed. Bars compare production utility-compatible M1 with submitted July M0; positive means a larger modeled metric under M1. Source: `Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_MAPPING_EFFECTS.csv`; `Supplement_Rebuild_20260925/Tables/S3_M1_MINUS_M0_HOSPITAL_FIRST.csv`.

**S4a. Self, threshold, and source-path loss by hazard.** Hospital-first, C57, M1, G1 means over 1,000 paired physical realizations per hazard. Components sum to the modeled cumulative service-loss proxy; they are not MW or observed outage hours. Source: `Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_GATE_COMPONENTS.csv`; `Supplement_Rebuild_20260925/Tables/S4_GATE_COMPONENTS_HOSPITAL_FIRST.csv`.

**S4b. Dynamic source-path loss concentration.** Concentration of modeled source-path loss for Hospital-first under C57. The companion table preserves reachable-source, disjoint-path, cut, bridge, articulation, and single-path summaries. These are topological diagnostics, not power-flow or capacity validation. Source: `Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv`; `Supplement_Rebuild_20260925/Tables/S4_DYNAMIC_TOPOLOGY_HOSPITAL_FIRST.csv`.

**S5. Five-seed direct-objective search and incumbent.** Retained direct-community fitness by generation on 64 independent 2pc50 planning realizations. All five seeds retained the impact-first deterministic incumbent; direct-community is the same 92-station sequence, not a new GA improvement. Source: `Formal_Experiment_20260923/Stage 5 Output_expanded/GA_HISTORY_2pc50_42–46.csv`; `Supplement_Rebuild_20260925/Tables/S5_GA_FIVE_SEED_SUMMARY.csv`.

**S7a. Equity–efficiency tradeoff.** Frozen 1,000-realization formal evaluation, reproduced without rerunning scheduling or recovery. Vulnerability-first is a deterministic equity-informed comparator, not an equity-optimal policy. See source CSV for plotted values. Source: `Formal_Experiment_20260923/Equity_Amendment/Figures/FIGURE_A_EQUITY_EFFICIENCY.pdf`; `Supplement_Rebuild_20260925/Tables/S7_FIGURE_A_EQUITY_EFFICIENCY_SOURCE.csv`.

**S7b. Q1–Q4 absolute burden.** Frozen 1,000-realization formal evaluation, reproduced without rerunning scheduling or recovery. Vulnerability-first is a deterministic equity-informed comparator, not an equity-optimal policy. See source CSV for plotted values. Source: `Formal_Experiment_20260923/Equity_Amendment/Figures/FIGURE_B_QUARTILE_ABSOLUTE_BURDEN.pdf`; `Supplement_Rebuild_20260925/Tables/S7_FIGURE_B_QUARTILE_ABSOLUTE_BURDEN_SOURCE.csv`.

**S7c. Vulnerability-first tract effects.** Frozen 1,000-realization formal evaluation, reproduced without rerunning scheduling or recovery. Vulnerability-first is a deterministic equity-informed comparator, not an equity-optimal policy. See source CSV for plotted values. Source: `Formal_Experiment_20260923/Equity_Amendment/Figures/FIGURE_C_TRACT_EFFECT_MAP.pdf`; `Supplement_Rebuild_20260925/Tables/S7_FIGURE_C_TRACT_EFFECT_MAP_SOURCE.csv`.

**S7d. Resource sensitivity of equity tradeoff.** Frozen 1,000-realization formal evaluation, reproduced without rerunning scheduling or recovery. Vulnerability-first is a deterministic equity-informed comparator, not an equity-optimal policy. See source CSV for plotted values. Source: `Formal_Experiment_20260923/Equity_Amendment/Figures/FIGURE_D_RESOURCE_EQUITY_SENSITIVITY.pdf`; `Supplement_Rebuild_20260925/Tables/S7_FIGURE_D_RESOURCE_EQUITY_SENSITIVITY_SOURCE.csv`.

**S8a. Formal Stage 7 PCA scree.** PCA diagnostic for the frozen formal Stage 7 feature matrix. The plotted ratios are from the formal output and do not rerun PCA or clustering. Source: `Formal_Experiment_20260923/Stage 7 Output_expanded/pca_stats_with_eigenvalues.csv`; `Supplement_Rebuild_20260925/Tables/S8_PCA_STATS.csv`.

**S8b. Formal Stage 7 K-means elbow.** Inertia across pre-evaluated k values in the formal Stage 7 analysis. Clusters are descriptive community typology, not causal classes. Source: `Formal_Experiment_20260923/Stage 7 Output_expanded/kmeans_k_diagnostics.csv`; `Supplement_Rebuild_20260925/Tables/S8_KMEANS_K_DIAGNOSTICS.csv`.

**S8c. Formal Stage 7 PCA loading structure.** Formal PCA loadings by feature and component; sign denotes direction in the standardized descriptive feature space. Source: `Formal_Experiment_20260923/Stage 7 Output_expanded/pca_loadings.csv`; `Supplement_Rebuild_20260925/Tables/S8_PCA_LOADINGS.csv`.

**S2a. Directed task-to-task road travel.** The frozen 92 × 92 directed road-travel matrix used by the event scheduler. Matrix entries need not be symmetric; this plot does not assert actual post-earthquake road conditions. Source: `Stage 4 Output_expanded/travel_task_to_task.csv`; `Stage 4 Output_expanded/travel_task_to_task.csv`.

**S3d. Cutoff robustness in 2pc50.** Hospital-first mean paired burden change under 1% or no cutoff, relative to each mapping’s 3% cutoff, using unchanged frozen 2pc50 physical and station-state trajectories. Cutoff sensitivity is not external feeder validation. Source: `Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_MAPPING_EFFECTS.csv`; `Supplement_Rebuild_20260925/Tables/S3_CUTOFF_HOSPITAL_FIRST_2PC50.csv`.

**S8e. Formal descriptive community clusters.** Formal Stage 7 cluster labels joined by 11-digit tract GEOID to retained tract geometry. Clusters describe joint features and do not establish causal community types. Source: `Formal_Experiment_20260923/Stage 7 Output_expanded/clusters_labels_final.csv`; `Formal_Experiment_20260923/Stage 7 Output_expanded/clusters_labels_final.csv`.

**S8f. Slow-vulnerable hotspot screening.** Descriptive Stage 7 top-decile slow/vulnerable screening tracts in red; this is not a causal or observed-outage hotspot map. Source: `Formal_Experiment_20260923/Stage 7 Output_expanded/clusters_labels_final.csv`; `Supplement_Rebuild_20260925/Tables/S8_stage7_top10_slow_vulnerable_tracts.csv`.

**S1b. Initial tract service CDF across four hazards.** Empirical CDF across 2,315 tracts of mean initial modeled service availability, projected from each hazard’s 1,000 frozen unconstrained event archives using frozen M1. This is a service proxy, not delivered electricity. Source: `Formal_Experiment_20260923/Formal_Trajectories/*/C57_D1/unconstrained/*.npz`; `Supplement_Rebuild_20260925/Tables/S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv`.

**S1c. Initial tract service maps.** Spatial mean initial modeled service availability across 1,000 frozen realizations per hazard. All panels use the same 0–1 color scale; no event simulation was rerun. Source: `Formal_Experiment_20260923/Formal_Trajectories/*/C57_D1/unconstrained/*.npz`; `Supplement_Rebuild_20260925/Tables/S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv`.

**S2b. Historical unconstrained tract T80 maps.** Per-tract mean time to 80% modeled service availability among realizations that reached it under frozen unconstrained event trajectories. Unreached cases remain NA in the source table; these maps do not imply observed restoration times. Source: `Formal_Experiment_20260923/Formal_Trajectories/*/C57_D1/unconstrained/*.npz`; `Supplement_Rebuild_20260925/Tables/S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv`.
