# Story-evidence matrix - candidate v2

This is an evidence map for author review, not a final Main/Supplement decision. Candidate v2 is derived only from frozen accepted results. Existing `results/figures/` remains unchanged.

| Evidence topic | Current evidence location | Candidate-v2 evidence | Main candidate direct evidence | Existing/supporting supplement evidence | Duplication or omission note |
|---|---|---|---|---|---|
| System representation | Fig02 A-B; retained graph inputs | Fig02 A-B | Yes, Fig02 A-B | Existing network criticality figures | Preserve July GIS/network content; current Fig02 was tall |
| Tract dependency / mapping validation | Fig02 C; FigS06; SCE benchmark CSV | Fig02 C-D | Yes, dependency and 337 public-site match | FigS06 mapping/cutoff robustness | Map count is not validation; 342 and 337 sets differ |
| Hazard damage | FigS01; Stage 1 damage tables | Fig03 A | Yes | Full hazard damage maps remain supporting | Box summarizes station means, not realization uncertainty; historical-vs-2pc50 differences also reflect different adopted fragility parameter sets |
| Initial service | FigS02; frozen tract initial-service table | Fig03 B | Yes, four-hazard tract ECDF | Four-hazard maps remain FigS02 source | ECDF is across tract means |
| Local / threshold / source-path loss | FigS04; loss decomposition tables | Fig03 C | Yes, four-hazard integrated decomposition | Dynamic route details remain FigS04/FigS07 sources | Dynamic time-varying mechanism is not in the main candidate; see gap audit below |
| Unconstrained recovery | Fig03 current; Stage 3 outputs | Fig03 D | Yes | Historical-hazard T80 remains in source suite | Population T80 distribution and mean tract T80 are distinct |
| Full eight-policy recovery | Current Fig04; recovery curve CSV | Fig04 A-B | Yes, all eight plus Unconstrained | Full strategy results by hazard remain tables/source suite | No strategy omitted; direct-community duplicate not separately plotted |
| Aggregate burden | Current Fig04 B | Fig04 B and Fig05 B | Yes | Full hazard/resource tables retained | Fig04/Fig05 no longer duplicate hospital burden panels |
| T80 | Current Fig04 D; formal parquet | Fig04 B, Fig03 D | Yes | All strategy/hazard distributions remain source tables | No imputation for unreached outcomes |
| Hospital-linked burden | Current Fig04 C and Fig05 B | Fig04 B once | Yes, once with the same 5-95 range convention | Existing Hospital-priority construction candidate may remain a review reference | Meaning is tract service burden, not hospital supply/clinical capacity |
| Q1-Q4 absolute burden | Current Fig06 A; formal and equity parquets | Fig05 A | Yes, four explicit policy contrasts | Full policies/hazards in frozen tables | Degree-first is added to absolute comparison |
| Signed / absolute Q4-Q1 | Current Fig06 B/C; frozen metrics | Fig05 C | Yes, matched changes vs three references | Full Q1-Q4 result tables remain supporting | Signed and absolute separation are shown as different metrics |
| Population-weighted Gini | Current Fig06 C | Fig05 C (separately scaled with ticks) | Yes | Full result tables retained | Not treated as the sole equity measure |
| Tract paired effects | Current Fig06 D; VULNERABILITY_TRACT_EFFECTS.parquet | Fig05 D | Yes, continuous mean map for VF-Hospital | Full tract effect table retained | Mean sign is not significance nor per-run affected-population mean |
| Resource dependence | Current FigS08/Sensitivity files | Fig06 A-D | Yes, C29 vs C57 for four policies and four outcomes | Other C86/C114 and duration cases remain frozen source suite | 2pc50 D1 comparison only; no universal direction claim |
| GA reproducibility | Current FigS05 and Stage 5 logs/manifests | FigS05 A-C | Supporting candidate | Five-seed archive and manifest | Clarifies convergence/incumbent evidence; not a global-optimum claim |
| Mapping / gate robustness | Current FigS06 and sensitivity tables | Not redrawn in Fig01-Fig07 | No | Existing FigS06 and frozen robustness tables | Must remain in supporting evidence chain |
| Source redundancy | Current FigS07 | Not redrawn in main candidates | No | Existing FigS07 and source diagnostics | Reachability reliability is not delivered MW |
| Capacity sensitivity | Current FigS08 and capacity closure outputs | Not redrawn in main candidates | No | Existing FigS08 and closure tables | 19 bounded stations, not full 92-station adequacy |
| Stage 7 typology / hotspots | Current Fig07/FigS09 and harmonized outputs | Fig07 A-C | Yes | FigS09 remains source diagnostic | Cluster profile, cluster map and screening map are separate measures |
| Cross-hazard strategy effects | Current tables/source suite | Strategy context in Fig03 only | Not fully | Frozen 4-hazard strategy summaries | `STORY_EVIDENCE_GAP` for claims that policy effects/rankings remain consistent across hazards, resources, and durations; do not generalize 2pc50 Fig04-Fig06 |
| Logistics / repair duration | Current FigS03 and Stage 4 files | Not main | No | Existing crew/travel and duration/resource results | Bases/travel are inputs; response result is Fig06 |

## Explicit claim-scope audit

No `STORY_EVIDENCE_GAP` remains for the three core questions when claims are scoped to the panels and scenarios shown below. A broader claim that strategy effects or rankings are consistent across all four hazards, crew counts, and duration cases would be a `STORY_EVIDENCE_GAP` in these main candidates: the frozen results exist in `PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet`, but must be cited in a table or separately reviewed supporting figure rather than inferred from 2pc50 panels. Similarly, Fig02-D is public-site agreement only, not feeder ground truth or validation of the full service model.

## Core-question coverage audit

| Core question | Direct candidate evidence | Current supporting evidence | Status |
|---|---|---|---|
| 1. How do hazard and network dependency produce tract service disruption? | Fig02 B-C; Fig03 A-C; Fig03 D baseline | FigS02 initial maps; FigS04 dynamic topology/source-loss diagnostics; FigS07 source reliability | Directly supported at the integrated-outcome scale; dynamic path timing is in supporting FigS04/FigS07, so Fig03 C alone should not be read as time-resolved restoration evidence. |
| 2. Under logistics/resource constraints, how do priorities change overall and critical-service recovery? | Fig04 A-B; Fig06 A-D | Existing crew/travel inputs and full resource/duration tables | Directly supported for 2pc50, 57 crews and the 29-vs-57 crew D1 contrast. `STORY_EVIDENCE_GAP` for generalization across all hazards/resource/duration combinations; those results need a supporting table or additional reviewed figure. |
| 3. How are burdens redistributed across vulnerability groups and places? | Fig05 A-D; Fig06 B-C; Fig07 A-C descriptive context | Existing complete tract and quartile tables; FigS09 diagnostics | Directly supported for the shown 2pc50 comparisons; no single scalar fairness claim is made. |
