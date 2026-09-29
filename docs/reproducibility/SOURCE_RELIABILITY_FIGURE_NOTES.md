# Source-connectivity operational reliability figure notes

All three figures use the retained July publication style from `Project_Visualizer.py` (Arial, manuscript width 18.5 cm, embedded Type 42 text in vector PDF, and 600-dpi PNG). They are rendered by `render_source_reliability_figures.py` from existing reliability CSVs only. The map also reads the retained 92-node/318-edge geometry, 14 Core-source identities, and expanded tract boundary. No fragility, Monte Carlo, damage, repair, scheduler, GA, mapping, or recovery analysis is rerun. Canonical versioned exports are in `Manuscript_Figures/`; presentation copies are in the existing `LA_Grid_Revised_Suite_20260925/Stage 3 Output_expanded/` and candidate Main/Supplement folders. Figure numbering remains open.

## `vis_source_reliability_full_vs_best_path_2pc50` — Main candidate

**Question.** How much does access to the full functional network improve conditional source-terminal reliability over reliance on one fixed, most-reliable single path under 2pc50 station fragility?

**Data.** `SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv`; 78 non-source stations only. Panel A displays `R_best_path` versus `R_path_full` on explicitly labeled logarithmic probability axes with a 1:1 line; the full data span is shown (approximately 10^-11 to 10^-1), without truncating low-probability stations. Marker size varies mildly with population dependency. Panel B lists the seven largest absolute `Delta_R_redundancy` values as dots, avoiding a 78-station bar chart.

**Supported reading.** Some non-source stations lie visibly above the fixed-path reference. WILMINGTON (STATION C) has the largest estimated absolute alternative-route gain (0.02644), followed by HINSON (0.01236). The log–log panel shows the wide probability range; the dot panel preserves the absolute scale of the gain. A plotted zero residual at a rare station is a finite-100k Monte Carlo result, not proof of no alternative path.

**Not supported.** These are not actual delivered-power reliabilities, customer outage probabilities, capacity estimates, or verified electricity routes. Source diversity and alternative-route gains overlap and cannot be added.

**Caption draft.** *Full-network source-terminal reliability versus a fixed most-reliable single-path reference under 2pc50 station fragility. Each point is a non-source station. The diagonal indicates equality; stations above it receive a modeled reliability gain from alternative source paths. The right panel shows the seven largest absolute gains. Both probabilities are conditional on the target station being functional. The source paths belong to the retained abstract topology and do not represent verified feeder or power-flow routes.*

## `vis_source_reliability_dynamic_redundancy_2pc50` — Main candidate

**Question.** How does the contribution of alternative routes re-form through the frozen recovery process, and how does its timing differ across restoration rules?

**Data.** `SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv` and `SOURCE_TERMINAL_DYNAMIC_STATION_2PC50.csv` for schema/NA verification. Panel A shows Impact-first and Hospital-first: solid is population-dependency-weighted joint full-network source connection, dashed is operation of each station's **fixed precomputed best-path reference**, chosen from 2pc50 fragility before recovery and never re-optimized at time *t*. Panel B shows the full-minus-fixed-path joint probability for all eight distinct scheduled policies. Symbols mark the available sampled display times; connecting lines are display guides, not a re-integration or smoothing of event-exact trajectories. The vertical guides mark 24 and 48 h.

**Supported reading.** At 48 h, Impact-first full/fixed is 0.8489/0.6680 and Hospital-first is 0.8334/0.6253. The gap is appreciable during recovery and declines as paths are restored. The eight-policy panel shows policy-dependent timing of modeled alternative-route support.

**Not supported.** The curves do not rank overall community burden or delivered electricity. The fixed path is not the optimal path recalculated at each time. The underlying station probabilities are jointly estimated from the same frozen physical realizations; no independent marginal product is used.

**Caption draft.** *Recovery of modeled source connectivity and alternative-route support for the 2pc50 scenario. (A) Population-dependency-weighted joint source-connection probability for Impact-first and Hospital-first, compared with each station's fixed precomputed most-reliable path. (B) Full-network minus fixed-path connection probability for all eight distinct scheduled policies. Points are estimates at selected display times from 1,000 frozen evaluation realizations per policy; lines join those points for readability. The paths are abstract topological connections, not transmission capacity or delivered-power estimates.*

## `vis_source_reliability_station_map_2pc50` — Supplement candidate

**Question.** Where in the retained station graph are conditional full-network source reachability and the fixed-path comparison gain located?

**Data.** `SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv`; `Data/substation_graph_CEC_nodes_expanded.csv`; `Data/substation_graph_CEC_edges_expanded.csv`; `Data/source_nodes_core_expanded.csv`; and the July expanded tract footprint from `Data/LA_Tracts_With_Population.shp` matched to `Data/Tracts_Within_Expanded_Area.csv`. Both panels show the same full study extent. Non-source stations carry the respective continuous value; all 14 local Core sources are separate white triangular markers. The 318 retained abstract links form a light gray background. Three high-gain station names are marked.

**Supported reading.** The mapped conditional reachability and estimated alternative-route gains vary spatially among modeled substations. The map can identify specific stations for interpreting the abstract network result.

**Not supported.** Node colors do not map actual electric service territories, feeder assignments, delivered load, or line-flow paths. Core source markers are not colored with non-source conditional reliability because a functional source is locally connected by definition.

**Caption draft.** *Spatial distribution of station-only source-terminal reliability under 2pc50 fragility on the retained 92-station/318-edge model. (A) Full-network source reachability conditional on the target station being functional. (B) Additional conditional reliability relative to the fixed most-reliable path. Triangles identify the retained 14 Core sources, and light gray lines are the model's abstract links. The study-area boundary follows the expanded July tract footprint. This is a topological diagnostic, not a map of actual feeder service or delivered electricity.*

## Export inspection

The three PNGs and companion vector PDFs were opened and checked at their final 18.5-cm width. The PDFs each have one page, embedded Arial text, and no text span outside the page. The log probability range and 1:1 line are visible; all eight scheduled policies appear in Panel B; 24/48 h guides and legend line types are readable; both maps use the same expanded extent and distinguish Core source markers. No panel text or station label is clipped.
