# Frozen-trajectory source-route requirement sensitivity

## Scope and identity

This is an offline diagnostic on the retained **92 stations, 318 edges, 14 Core sources, production M1 mapping, 0.5 functionality threshold, 480 h horizon**, using the four frozen 1,000-realization hazard sets. It reads 32,000 distinct baseline trajectories from the original formal archive plus 4,000 frozen vulnerability-first amendment trajectories. The `direct-community` duplicate of `impact-first` is excluded. No DS, repair duration, crew schedule, GA sequence, mapping, trajectory, or production source gate was regenerated or modified.

For each actual saved event state, the tested independent-route kernel counts routes from a functional non-source station to any active Core source. Intermediate substations and edges cannot be shared; routes may terminate at the same active source. A functional station that is itself an active source is treated as locally connected at every k, not as a remote route with sentinel -1. Diagnostic cases require at least 1, 2, or 3 independent routes for non-source stations; `e_i^(k)=f_i F_i C_i^(k)` and production M1 weights map this to tract service. All burdens use the frozen event intervals with left-state integration. This **does not** calibrate route count to delivered MW or replace the binary production gate.

## Required numerical checks

Across all 36,000 distinct policy trajectories, k=1 exactly reproduces frozen G1 station effective state and tract service (maximum absolute difference 0); its tract cumulative burden differs by at most **4.26e-14 h**, population burden by **1.42e-14 h**, and population T50/T80 by 0. Hospital burden, Q1–Q4 burden, signed/absolute gap, and population-weighted Gini also match their frozen G1 summaries within **2.84e-14** in their respective units. The independently saved route-composition archive yields k=2 burden as `480 h − local-source service-hours − multiple-route service-hours`; this matches the new k=2 integral within **1.42e-13 h**. These checks establish that the stricter cases change only the diagnostic connectivity requirement. Full validation values are in `Formal_Experiment_20260923/Formal_Reviewer_Results/ROUTE_REQUIREMENT_VALIDATION.json`.

## Structural feasibility, before damage or repair

| Requirement | Capable stations / 92 | Population-dependency mass on capable stations | Tracts structurally below 50% (population) | Below 80% (population) | Below 90% (population) |
|---|---:|---:|---:|---:|---:|
| k=1 | 92 | 100.00% | 0 (0) | 0 (0) | 0 (0) |
| k=2 | 84 | 92.53% | 172 (686,370) | 189 (750,743) | 317 (1,234,131) |
| k=3 | 73 | 77.99% | 530 (1,964,333) | 609 (2,264,299) | 755 (2,841,843) |

The study-domain population is 9,066,522. A tract whose intact-network maximum service is below a target cannot reach that target under any repair schedule. Its T80 is *unreached/NA*, never 480 h. The tract output carries `intact_maximum_service` and structural T50/T80-unreachable flags. At k=3, aggregate maximum population service is 77.99%, so population T80 is unreached in **100% of realizations for all hazards and policies**. This is an extreme topology stress test, not a realistic “slow repair” result.

## Aggregate recovery effects

Across the nine distinct baseline decisions per hazard (unconstrained plus eight scheduled policies), mean population cumulative burden (hours) is:

| Hazard | k=1 (production) | k=2 | k=3 |
|---|---:|---:|---:|
| Northridge | 9.53 | 45.56 | 111.65 |
| SanFernando | 3.99 | 40.98 | 109.03 |
| LongBeach | 4.73 | 40.79 | 110.26 |
| 2pc50 | 35.08 | 70.39 | 134.46 |

The large common increment is largely a structural service ceiling from the fixed 92-node graph, present even after all stations become functional. It must not be attributed solely to fragility or logistics. k=2 leaves aggregate T80 attainable and delays it; for 2pc50, impact-first mean T80 changes from 45.25 h (k=1) to 52.60 h (k=2). k=3 makes T80 structurally unattainable.

In 2pc50, impact-first population burden is 33.59, 69.73, and 134.11 h for k=1/2/3; hospital-first is 34.31, 70.21, and 134.78 h. Their paired impact-minus-hospital differences remain negative: **−0.713 h** (95% paired-bootstrap CI −0.745 to −0.682), **−0.484 h** (−0.515 to −0.455), and **−0.672 h** (−0.700 to −0.647). Thus impact-first remains better than hospital-first for this particular aggregate burden in all three diagnostic gates. But the *best of the eight scheduled policies* changes at k=3: degree-first reaches 133.57 h versus impact-first 134.11 h, a 0.54 h difference. k=2 still ranks impact-first first. Historical-hazard policy differences are much smaller than the structural k increment; small rank swaps should not be elevated into strong claims.

The Q4 targeting contrast is also gate-sensitive. For 2pc50, vulnerability-first versus hospital-first Q4 mean burden changes from 32.02 versus 33.62 h (k=1), to 59.27 versus 60.62 h (k=2), to 108.18 versus 109.77 h (k=3); Q4 benefit persists. Q1 burden under vulnerability-first is 37.49 versus 36.22 h at k=1 and 81.22 versus 80.35 h at k=2. The k=3 structural ceiling dominates absolute group burden and signed group gaps; this cannot be read as a calibrated equity outcome. Complete paired effects, unreached fractions, Gini, hospital burden, and continuous tract shifts are in the accompanying CSV/parquet outputs.

## Relationship to existing diagnostics and Reviewer 1 #2

The existing 100k initial-state analysis estimates how **already-used station fragility** propagates into source/route reliability (`R_path`, `R_conn`, and route-count probabilities). The existing frozen-trajectory decomposition measures how much production-connected service is supported by local source, one route, or multiple routes over recovery. This new k sensitivity asks a distinct counterfactual question: what happens to the same saved community outcomes if *availability* requires more independent routes? Their k=2 arithmetic agreement is a consistency check, not a reason to delete either analysis.

The test shows the production k=1 gate is a consequential assumption for absolute burden and community attribution. It also shows that some relative policy conclusions (for example impact-first versus hospital-first aggregate burden in 2pc50) survive k=2/3, while the best policy identity changes under extreme k=3. It does **not** establish that two or three routes are physically necessary to serve load. Without bus injections, edge/transformer ratings, switching, and power flow, route redundancy remains topological robustness rather than delivered electricity. A future continuous reliability model would need a probability for *additional conditional failures not already sampled in the frozen DS states*, for example physically sourced transmission-edge failures conditional on shaking and component state. Multiplying current `e_i` by `R_path_i` or `R_conn_i` derived from the same station fragility would reuse the same uncertainty and can double count it. No edge failure probability or continuous service multiplier was invented here.

## Frozen files read and outputs

Inputs actually read by the scripts: `Data/Substations_PGA_IDW_CEC_expanded.csv` (fragility audit); `Data/substation_graph_CEC_edges_expanded.csv`; `Data/source_nodes_core_expanded.csv`; `Data/JULY_UTILITY_CONSTRAINED_92.csv`; `R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv`; all four `Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_<hazard>.npz` for station identity; the 32,000 selected baseline `Formal_Trajectories/<hazard>/C57_D1/<strategy>/<realization>.npz`; 4,000 `Equity_Amendment/T/<hazard>/C57_D1/<realization>.npz`; 36 G1 `Formal_Offline_Evaluation`/`Equity_Amendment/Offline` `__INTEGRALS.npz` and `__SUMMARY.parquet` shards; and the prior `Formal_Reviewer_Results/FORMAL_CONNECTIVITY_REALIZATION_SUMMARY.parquet` for k=2 cross-validation. `Data/working_area_substations_with_fragility.csv` and the protected July version were separately inspected for table/history provenance; `FINAL_EXPERIMENT_MATRIX.json` remained the frozen design authority but was not parsed by this new evaluator. No raw 100k states were needed for k sensitivity.

Outputs: `ROUTE_REQUIREMENT_FEASIBILITY.csv`, `ROUTE_REQUIREMENT_SENSITIVITY_SUMMARY.csv`, `ROUTE_REQUIREMENT_STRATEGY_EFFECTS.csv`, `ROUTE_REQUIREMENT_TRACT_EFFECTS.parquet`, plus compact realization-level `Formal_Reviewer_Results/ROUTE_REQUIREMENT_REALIZATIONS.parquet` and validation JSON. The main fragility audit and per-station DS parity data are separate at project root. Formal source event archives remain local and uncommitted; these compact outputs are sufficient to review this diagnostic.
