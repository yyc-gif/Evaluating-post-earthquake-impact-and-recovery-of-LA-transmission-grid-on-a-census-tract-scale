# Adopted methodology: executable path and affected outputs

Start: `6f9fb3da89fcfb56677f238a8679866deda854a8`. This record concerns
the current revision only; the July archive and frozen physical/event archives
were not edited.

| Adopted method | Actual current call/data path | This turn |
|---|---|---|
| Production mapping | `ExpandedConfig.MAP_TRACT_SUB_CSV` → `run_stage_0` → `W_mat` → saved service evaluations. Formal offline primary views select `M1_UTILITY_003` and G1; M0 remains paired mapping sensitivity. | Already correct; unchanged. |
| Paired repair clock | `run_stage_1_revision` retains per-realization DS/duration; the formal decoder filters DS0 and uses directed travel plus realized duration; completion releases crew and updates raw station functionality at the same event. | Already correct; unchanged. |
| Direct GA objective | `run_formal_ga_planning` → `_run_stage_5_formal_planning` → exact direct planning kernel, cross-checked against `evaluate_direct_population_burden_aggregate`; all seven fixed rules are incumbents and best-so-far is retained. | Already correct; legacy surrogate remains separately named and is not the formal fitness. |
| Distributional evaluation | `r1_formal_offline.evaluate_exact_event_arrays` computes Q1–Q4 absolute burdens, signed and **per-realization absolute** Q4–Q1 gaps, and per-realization population-weighted Gini. `r1_formal_results` pairs by realization. | Added absolute-gap metric to current paired builder; removed the retired ±1 h class production from current results builder. `FORMAL_ABSOLUTE_GAP_PAIRED_EFFECTS.csv` is a read-only pairing of frozen primary/amendment rows for eight distinct decisions. Frozen legacy classification CSV remains provenance only. |
| Stage 7 | Formal `--phase stage7` and dedicated `--verify-existing` now select and verify `Stage 7 Output_SOVI_Harmonized` (2,315 full-domain rows; 2,291 residential clusters; 24 explicitly not applicable). | Formal entry no longer reruns or silently selects the older CDC-theme Stage 7. `render_revised_suite.py --stage7-only` refreshes only affected Stage 7 panels/tables and the existing index; `Project_Visualizer.vis_stage7` distinguishes non-applicable residential typology from absent SVI. |

## Existing source-propagation result chain

The formal G1 `FORMAL_GATE_COMPONENTS.csv` separates self, threshold, and
source-path burden. `FORMAL_SOURCE_LOSS_BY_STATION.csv` attributes the saved
source-path integral to stations and population dependency weights;
`FORMAL_SOURCE_LOSS_BY_TRACT.csv` applies the unchanged M1 mapping to identify
tract cumulative source loss. `FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv` links the
same realization/strategy source loss to prior path fragility and source-loss
clearance time. Those tables already connect **what lost service**, **how long
the disconnection lasted under each priority**, and **which tracts accumulated
the burden**; no new static-connectivity run was needed.
Across the saved summary rows, self + threshold + source differs from total
by at most `1.42e-14 h`; summed station attribution differs from aggregate
source loss by at most `6.22e-15 h`. The tract source-loss table covers all
2,315 tract IDs.

For 2pc50/C57, source-path burden is 4.065 h under Hospital-first. It is
2.418 h under Degree-first and 4.1677 h under Impact-first; the corresponding
mean source-loss clearance times are 59.98, 53.91, and 58.65 h. The Station D
(Fairfax), Station T, and Station H (Hollywood) rows are among the largest
population-weighted station contributors under Hospital-first. The tract
table, rather than station rank alone, identifies where these losses enter
community burden. These are model-internal source-path effects, **not** a
claim that t=0 forced-station importance is a dynamic optimal repair order.

## Presentation refresh and remaining scientific interpretation

Twelve Stage 7 PNG/PDF panel pairs, three suite tables, five candidate panel
copies, and the existing one-panel-per-page figure index were refreshed from
the frozen harmonized Stage 7 CSVs. The full study boundary appears on the
cluster and hotspot maps; 24 tracts are explicitly shown as residential
typology not applicable. No new clustering, damage, scheduling, GA, or recovery
trajectory calculation occurred.

The remaining author-level choices are how prominently to present the
residential-only typology alongside 2,315-tract service results, and whether
binary source connectivity remains the availability representation in the
paper or is accompanied by the existing route-composition diagnostic. The
available data do not turn route count into delivered MW or establish a new
repair-priority ranking.
