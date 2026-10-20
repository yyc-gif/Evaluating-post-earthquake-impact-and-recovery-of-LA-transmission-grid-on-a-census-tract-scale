# Code authority

## Decision

The repository-local `results/revised_suite/LA_Grid_Revised_Suite_20260925` contains presentation outputs but no executable source files. The rendering and validation code required by the final workflow is already in this Git branch. The canonical workflow uses repository code only; it does not depend on an absolute Windows sibling path. The suite folder is a required external output collection for Stage 10 resume validation and is resolved by repository-relative path or `LA_GRID_REVISED_SUITE_DIR`.

## Verified sources

Exact source-file SHA-256 values and historical executable commit presence are recorded in `CODE_AUTHORITY.json` and checked by `run_all.py --resume`. Phase-specific historic executable SHAs remain in their original identity files and are not replaced by the current HEAD.

| Purpose | Existing authority code |
|---|---|
| Frozen matrix/input validation | `r1_final_matrix.py`, `C257H_Project_Main_expanded.py` (validation-only phase; canonical resume does not invoke result-producing phases) |
| Physical sample identity | frozen Stage 1 records and `C257H_Project_Main_expanded.py` |
| GA/strategy provenance | `r1_ga_revision.py`, `run_formal_ga_planning.py` where present, frozen sequence records |
| Scheduling and frozen trajectory handling | `r1_formal_schedule.py`, `C257H_Project_Main_expanded.py` |
| Offline service and tract results | `r1_formal_offline.py`, `r1_formal_results.py`, `r1_equity_amendment_results.py` |
| Source/network diagnostics | `r1_formal_mechanism_results.py`, `r1_formal_dynamic_topology.py`, `route_requirement_sensitivity.py`, `source_terminal_operational_reliability.py`, `substation_connectivity_reliability.py` |
| Final Stage 7 read-only validation | `r1_stage7_harmonized.py`, `run_stage7_sovi_harmonization.py` (verifier only in resume) |
| SCE capacity closure provenance | `run_sce_capacity_supported_sensitivity.py`, `sce_capacity_closure.py` (outputs validated; closure not run) |
| Figure/output organization | `build_revised_result_suite.py`, `render_revised_suite.py`, `render_revised_suite_comparisons.py`, `render_revised_stage7.py`, July `Project_Visualizer.py`; audited presentation refreshers: `r1_equity_amendment_figures.py`, `render_efficiency_distribution_tradeoff.py`, `render_sce_capacity_sensitivity_figure.py`, `render_source_reliability_figures.py` |

The 2026-09-29 artwork remediation keeps the protected July central size/font system and records its local Arial publication renderers in the current code identity list. It changes presentation only: the concise workflow redraw, canonical strategy display labels, overlap-free legends, color/line-style accessibility, and figure-specific page clearance. No plotted values changed. `render_final_artwork_remediation.py` is the presentation-only renderer for the frozen Stage 7 loadings display and selected candidates; the generated figure index records its function and frozen source table.

The suite inventory found zero code-like files. There is no missing executable source that needs to be copied into this repository. The canonical validator consumes the local externally maintained result collection, not code from another checkout.

## Historical identities and scratch status

The design, GA, scheduling, trajectory, offline, Stage 7, Vulnerability-first and reporting steps were executed at different historical commits. Those SHAs and their local frozen artifacts are preserved as provenance. Because some execution code and large archives are local-only, `--from-scratch` is **NOT YET CERTIFIED**. Resume fails on missing archives; it never regenerates them as fallback.

The 2026-10-08 selected-policy display round right-aligns Stage7 profile labels and reads saved degree/betweenness metrics for new supplementary evidence. Six scheduled policies are displayed, while original formal strategies and their authority records remain intact. New GA budget extensions and planning-selected independent evaluation are separate exploratory diagnostics under `results/diagnostics/extended_ga_20261008/`; canonical resume validates and reuses the original formal strategy set.
