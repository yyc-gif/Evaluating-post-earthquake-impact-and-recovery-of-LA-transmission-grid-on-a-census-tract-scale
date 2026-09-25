# Formal July92 reviewer-oriented scientific results

## 1. Executive findings

This report uses only `JULY92_REVIEWER_REVISION_FINAL_V1`: four hazards, 1,000 fixed evaluation physical realizations per hazard, the retained 92-station/318-edge graph, 14 Core source points, C57 baseline, and the common 480 h event horizon. All strategy comparisons are paired on damage, realized repair durations, roads, crews, graph, sources, and mapping. The 64 independent 2pc50 planning samples were used only to select the direct-community sequence. No new physical samples, schedules, GA search, or scientific trajectories were generated for this report.

The revised utility-compatible mapping improves *conditional public-candidate agreement* in the 337 strict-SCE tracts where an official direct candidate is representable in July92: any match rises from 320 to 329, top-1 from 296 to 302, and top-3 from 317 to 324. Another 480 strict-SCE tracts have no directly representable official candidate. This is an external consistency benchmark, not verified feeder assignment. On formal outcomes, the M1 minus M0 population burden changes by +0.358 h (Northridge), +0.231 h (San Fernando), +0.031 h (Long Beach), and −0.519 h (2pc50) for hospital-first. Local effects can be much larger: in 2pc50, 246/2,315 tracts have absolute mean paired shifts over 1 h, representing 932,194 people. Mapping therefore matters more for local attribution than a small aggregate difference might suggest.

The production source gate adds two distinct losses to station self-damage. Under 2pc50/C57/hospital-first, population-weighted cumulative self loss is 29.278 h, threshold loss 0.963 h, and source-path loss 4.065 h, totaling 34.306 h. Thus no-gate versus production-gate 5.028 h is **not** all source disconnection. The source-path share of total modeled burden is 14.9% in Northridge, 8.7% in San Fernando, 4.3% in Long Beach, and 11.8% in 2pc50 for that strategy.

The direct-community sequence is exactly the predeclared impact-first incumbent: five fixed-budget GA seeds did not improve it on the independent planning set. Across all 10,000 paired formal archives, direct-community and impact-first event arrays are bytewise-value identical. Under 2pc50/C57, impact-first has 0.713 h less modeled population burden than hospital-first, but 0.103 h **more** source-path burden; its aggregate improvement is mainly shorter local station self-loss. Network-centrality rules reduce source-path loss more, while their total and hospital burdens are worse. These are model-conditional sequence effects, not observed customer restoration or proof of an efficiency–equity frontier.

## 2. Mapping revision: external validation

The production M1 mapping changes only candidate eligibility for strict SCE and strict LADWP tracts; mixed or ambiguous tracts retain the July general eligibility. The July centroid, nearest eligible access station, network shortest-path distance, inverse-square weights, 0.03 sparsification and renormalization remain. M0 is the retained July mapping. Both use the same 92 station IDs and graph. The SCE circuit/substation data supply candidate evidence, not customer-level load shares or true feeder membership.

| Representable strict-SCE tracts (n=337) | July M0 | Utility-compatible M1 |
|---|---:|---:|
| Any official candidate in mapped set | 320 (94.96%) | 329 (97.63%) |
| Top-1 mapped station supported | 296 (87.83%) | 302 (89.61%) |
| Top-3 includes supported candidate | 317 (94.07%) | 324 (96.14%) |

The 337-tract denominator is conditional on official candidate crosswalk to July92; 480 additional strict-SCE tracts lack such representation and cannot be counted as correct or incorrect matches. In the predeclared cutoff comparison, 0.03 removes 41/411 (9.98%) publicly supported SCE station relations under M1; 0.01 removes 12/411 (2.92%). The LAX–RS-N candidate has a pre-cutoff July weight around 1.20%, so the production 3% cutoff discards it. This documents a real cost of sparsification; it does not justify assigning a special case weight to LAX.

## 3. Mapping revision: outcome sensitivity

For 1,000 paired physical samples per hazard, M1 minus M0 under hospital-first gives the following mean changes. Positive burden means more modeled service-access deficit under M1; a negative T80 means earlier crossing of the modeled population availability threshold.

| Hazard | Population T80 (h) | Population burden (h) | Hospital-tract burden (h) | Q4−Q1 signed gap (h) |
|---|---:|---:|---:|---:|
| Northridge | +0.980 | +0.358 | +0.102 | +0.222 |
| San Fernando | +0.086 | +0.231 | +0.085 | +0.201 |
| Long Beach | +0.045 | +0.031 | +0.126 | +0.035 |
| 2pc50 | −0.789 | −0.519 | −0.387 | −0.561 |

The full per-hazard, per-strategy metrics, medians and direction fractions are in `Formal_Reviewer_Results/FORMAL_MAPPING_EFFECTS.csv`. The paired 2pc50 hospital-first M1−M0 tract shift has median 0, 95th percentile absolute shift 4.397 h, maximum absolute shift 15.114 h. Classification applies the predeclared ±1 h practical threshold to each tract's **1,000-realization mean paired effect**. M1 improves 193 tracts (747,293 people), leaves 2,069 near zero (8,134,328), and worsens 53 (184,901); the denominator is 9,066,522 mapped people. These are not per-earthquake frequencies or significance tests. Mapping changes source-loss attribution too: for 2pc50/hospital-first the population-weighted source component rises 0.243 h from M0 to M1 even while total burden falls 0.519 h; 190 tracts shift by over 1 h in the source component alone. `FORMAL_SOURCE_MAPPING_SHIFT_BY_TRACT.csv` separates source and total effects.

At 2pc50/C57/hospital-first, removing the cutoff raises M1 burden by 0.543 h relative to M1/0.03, while 0.01 raises it by 0.153 h. This tests the consequence of retaining low-weight candidates; neither alternative is a new calibrated production model. The SCE public-candidate-supported mapping is only evaluated on the validation subset. On the common 320 positive-mass tracts, hospital-first mean burden is 30.619 h (M0), 30.611 h (M1), and 30.396 h (supported-only). Seventeen of the 337 native subset tracts remain unresolved, not zero burden. The subset comparison cannot establish full-region robustness or real service shares.

## 4. Source-gate contribution decomposition

At every saved station event state, the production definition obeys `e=fFC` with `F=1[f>=0.5]` and `C` indicating a path to an active Core source. The accounting identity is exact: `1−e = (1−f) + f(1−F) + fF(1−C)`. Event-left-rectangle integration followed by M1 tract weights yields separate station self, threshold, and source-path components. The decomposition is additive for cumulative deficit, **not** for T50/T80.

| Hazard, C57 hospital-first | Self (h) | Threshold (h) | Source path (h) | Total (h) | Source fraction |
|---|---:|---:|---:|---:|---:|
| Northridge | 7.776 | 0.320 | 1.416 | 9.512 | 14.9% |
| San Fernando | 3.487 | 0.160 | 0.347 | 3.994 | 8.7% |
| Long Beach | 4.337 | 0.193 | 0.205 | 4.734 | 4.3% |
| 2pc50 | 29.278 | 0.963 | 4.065 | 34.306 | 11.8% |

The denominator here is the full 2,315-tract population of 9,066,522; the July92 mapping has no unresolved mass in this formal analysis. Burden hours describe the availability **proxy**, not measured household outage hours. The station- and tract-level decompositions are in `FORMAL_SOURCE_LOSS_BY_STATION.csv` and `FORMAL_SOURCE_LOSS_BY_TRACT.csv`.

## 5. Dynamic network propagation and redundancy

Dynamic diagnostics are read from all 84,000 formal event archives. They cover 6,960,198 event states, of which 6,061,473 are the first state of a run or differ functionally from the preceding event. Each distinct functional-station/source bitmask is evaluated exactly once within a physical sample and then referenced by each event; 5,249,914 state-cache hits (75.43%) avoided duplicate exact calculations, with 1,710,284 misses. The resulting station `L_source` integrals match the independently retained formal offline integrals with maximum absolute difference **0 h**. Per-state records include F, local active-source flag, C, reachable source count, edge-disjoint paths/minimum edge cut, internally node-disjoint paths, bridge/articulation dependence, single-path and disconnected indicators. A station that is itself an active source has local supply and its own zero-length path is **not** counted as an independent upstream route. These are undirected graph-path diagnostics, not power flow or physical line contingency ratings.

For every source-loss interval, the analysis records the station's current disconnected state, last source-connected redundancy class, and whether only the static full-function graph is available as fallback. In this monotone repair-only model, **100% of source-loss intervals at a station precede its first connected event**. Consequently, the last-connected class for these intervals is *always the static full-function reference*, not an observed pre-failure dynamic class. The dynamic metrics are still exact for every actual event and show the condition as restoration progresses; they cannot identify a distinct immediately-prior dynamic path that never occurred in the saved trajectory. A source-connected station with one path but no current loss contributes vulnerability context, not `L_source`. The pre-existing static full-function graph has eight single-path stations: 301214, 303303, 304040, 305780, 305885, 306365, 306694 (COLORADO), and 308991. Their contribution describes source loss **located at those stations**, not damage they caused to every downstream station. In this graph the single-edge source cut/bridge and internal articulation flags overlap for those eight in the source-loss attribution; one should not sum these categories or claim distinct causal failure modes from their equal fractions.

Under C57/hospital-first, mean per-realization top-1/top-5/top-8 shares of population-weighted source-path loss are 36.4/88.7/98.1% (Northridge), 62.5/97.2/99.6% (San Fernando), 59.8/98.2/99.7% (Long Beach), and 17.5/56.1/72.1% (2pc50). Their top-1 95th-percentile shares are 62.9/100.0/100.0/27.2%, respectively. This supports concentration in a few stations for the lower-loss historical scenarios, but **not** an all-hazard claim that one station dominates. The eight static single-path stations account for 43.3/59.2/52.2/23.8% of each realization's source loss, respectively; COLORADO accounts for 5.9/1.4/6.9/3.5%. Mean *population-weighted* source-path loss is 1.416/0.347/0.205/4.065 h, with medians 1.227/0.238/0.167/3.871 h and 95th percentiles 3.230/1.028/0.533/6.673 h. The RS-K→COLORADO adjacency is an abstract retained CEC-derived model edge, not independently verified unique electrical feed. In 2pc50 hospital-first the COLORADO station has 15.174 h mean station-level source loss, of which 11.996 h (79.1%) coincides with RS-K being nonfunctional; the remaining 3.178 h occurs while RS-K is functional but its upstream source path is absent. The corresponding coincidence fractions are 99.5%, 98.9%, and 100% in Northridge, San Fernando, and Long Beach. This diagnoses the **model edge's behavior**, not actual RS-K-to-COLORADO supply. The figures are in `FORMAL_COLORADO_RS_K_ASSOCIATION.csv`; realization distributions and 95th percentiles are in `FORMAL_DYNAMIC_TOPOLOGY_SUMMARY.csv` and `FORMAL_SOURCE_LOSS_CONCENTRATION.csv`.

For hospital-first, only 33/45/11/0 tracts in Northridge/San Fernando/Long Beach/2pc50 have mean source-path deficit exceeding mean station self-deficit; their populations are 120,443/171,008/46,628/0. This is a tract-level *mean component* comparison, distinct from the fraction of realizations with source>self retained in the tract table. The final source-loss interval ends, on average, at 38.96/23.82/21.20/59.98 h, respectively (medians 40.44/17.34/15.71/59.18 h; 95th percentiles 59.25/54.95/48.98/79.91 h). This is last modeled loss clearance, not full power restoration.

## 6. Strategy effects

All values below are 2pc50/C57/M1/G1 and are differences from hospital-first on the same 1,000 evaluation realizations. `direct-community` is identical to `impact-first`, not a separate decision or GA gain.

| Strategy | Δ population burden (h) | Δ source-path burden (h) | Δ T80 (h) | Interpretation |
|---|---:|---:|---:|---|
| Impact/direct-community | −0.713 | +0.103 | −0.719 | Overall gain comes from self/threshold changes, not reduced source loss |
| Degree-first | +1.401 | −1.647 | +3.539 | Protects modeled path availability better, but worsens total burden |
| Centrality-first | +1.819 | −1.207 | +2.471 | Lower network loss and worse community/hospital burden coexist |
| Random | +5.082 | +0.283 | +6.892 | Worse burden and source loss |
| Unconstrained | −2.969 | −0.491 | −2.571 | Counterfactual without crew competition, not a dispatch policy |

The exact tables include all seven rules, median effects, realization-level direction frequencies, and paired uncertainty from the existing formal result package. Under 2pc50 the last source-loss interval clears at mean 59.98 h for hospital-first versus 48.37/48.55/53.91 h for betweenness/centrality/degree-first and 63.70 h for random. Network-oriented rules reduce `L_source` most under 2pc50, but the reduction does not outweigh their longer local task burden. In the three historical hazards the absolute source-path strategy differences are much smaller (roughly hundredths of an hour), so a 2pc50 mechanism should not be universalized. Hospital-first has lower 2pc50 hospital-tract burden than centrality-first (by 2.460 h) but 1.207 h more source-path loss; it does not dominate every mechanism.

## 7. Resource and logistics effects

The 2pc50 OFAT uses the same 1,000 physical samples: crew 29/57/86/114 with duration scale 1, and duration scales 0.75/1/1.25/1.5 with C57. Under hospital-first, C29 raises total burden from 34.306 to 46.951 h; self-loss rises 11.187 h and source-path loss 1.049 h. C86 and C114 give 31.679 and 31.687 h; the tiny non-monotonicity reflects discrete depot rosters and priority dispatch, not a calibrated staffing optimum. With C57, duration ×0.75/1.25/1.5 gives total 25.832/42.781/51.255 h and source-path 3.049/5.081/6.097 h, versus 4.065 h at baseline. Scarcity mainly prolongs local repair exposure but also extends network disconnection. The *fraction* attributable to source paths does not rise monotonically with crew scarcity or for every rule; therefore resource effects require absolute and proportional reporting together.

## 8. Distributional and community effects

For 2pc50/C57/M1/G1, hospital-first Q1–Q4 absolute modeled burden is 36.225, 34.309, 33.295, and 33.618 h. Impact-first gives 35.332, 33.714, 32.807, and 32.733 h: all four groups improve, but the signed Q4−Q1 gap is nearly unchanged (−2.607 versus −2.599 h). Centrality-first gives 37.094, 36.558, 35.276, 35.695 h: **all four groups worsen** even though its Gini is lower (0.185 versus hospital-first 0.189). A lower Gini or narrower gap alone is not evidence that vulnerable communities recovered faster. The SOVI measure is NRI-derived, not CDC SVI, and Q labels are fixed across strategies.

Per-tract improved/near-zero/worsened/unresolved classification uses ±1 h as a practical difference, not a significance cutoff. Paired uncertainty uses the earthquake realization as the resampling unit, never 2,315 tracts as independent shocks. The mean paired-tract classification and per-realization classification are different summaries and must not be interchanged. The Stage 7 PCA/K-means/hotspot products remain descriptive screening of co-occurrence, not causal explanation. `FORMAL_DISTRIBUTIONAL_EFFECTS.csv`, existing `Formal_Results/TRACT_CLASSIFICATION_POPULATION.csv`, and the Stage 7 archive contain the detailed values.

## 9. Gate and mapping robustness together

The mapping comparisons hold physical realizations, schedules, raw station trajectories, and gate fixed. Gate comparisons likewise hold these and mapping fixed. Under 2pc50/C57/hospital-first/M1, ungated G0 has burden 29.278 h, production G1 34.306 h, threshold .05 G2 34.280 h, and threshold .75 G3 34.310 h. The G1−G0 difference of 5.028 h decomposes into 0.963 threshold and 4.065 source-path hours. Threshold perturbations in this range affect cumulative burden by only −0.027/+0.004 h relative to G1 for this case; they do not establish robustness to omitted line capacity, power balance, or source dispatch. The main source-path mechanism is therefore distinct from a mere threshold artifact under tested thresholds.

Across G0/G1/G2/G3 in 2pc50, impact-first/direct-community remain lowest in mean population burden among the scheduled sequences, hospital-first next, and random highest. The intermediate closeness/betweenness ordering swaps between G1 and G2, showing that very small near-tie ranks are assumption-sensitive even when the main contrast is not. Across full-domain M0 and M1, the 2pc50 impact–hospital–random ordering is likewise retained. On the common 320 SCE positive-mass tracts, M0/M1/M3 all put impact-first first and random last among the scheduled sequences, but this is a *subset outcome* and does not validate missing candidate relationships elsewhere. The 2pc50 cutoff and SCE supported-candidate checks in Section 3 are fixed-decision *evaluation* sensitivity. They do not test how different mappings would change planning priorities or the selected GA sequence. Aggregate strategy directions and local tract attribution must be assessed separately; a stable population mean does not imply stable tract identities. The full cross-condition values are in `FORMAL_MAPPING_EFFECTS.csv` and the retained offline summary shards.

## 10. What the model represents physically

The July92 graph represents abstracted station adjacency. Station functionality above a threshold and an available path to one of 14 retained Core upstream points yield a source-connected availability proxy; event-based repairs can restore raw functionality while the gate still prevents effective availability. The dynamic path diagnostics quantify how that proxy depends on source routes and where service-access burden is amplified by disconnected upstream paths. They do not estimate MW delivered, voltage, feeder switching, hospital operation, or measured customer outage.

The 14 Core nodes have a documented identity/role crosswalk, but no independent per-node dispatch or Pmax is established. The local Level-1 evidence screen identifies matched SCE planning facilities with load/limit context. For example, the OLINDA 66/12 planning record has cumulative demand 28.45 versus facility load limit 26.09 in the same source convention (ratio 1.090, reported loading 109.04%). That is evidence that **connected can coexist with capacity concern** in planning data; it is neither observed earthquake overload nor a 92-edge thermal rating. Other matched records are in `Revision_Mapping_Gate/CAPACITY_SCREEN_FINDINGS.json`.

## 11. What remains outside the model

| Reviewer physical concern | Final treatment and boundary |
|---|---|
| Power balance | No real bus generation/load balance; source connection does not prove supply adequacy. |
| Transmission capacity | Level-1 facility planning/load context only; no fabricated 92-edge thermal limits. |
| Line loading | No real line X, ratings, and injections; no all-edge flows. |
| Generation availability | Fourteen Core identities audited; actual dispatch/Pmax not supplied. |
| Voltage constraints | No AC R/X/Q/tap/shunt/voltage case. |
| Load shedding | No constrained dispatch or load-shedding solution. |
| Source connectivity | Implemented, decomposed, mapped, and tested across four hazards, strategies, resources, and thresholds as reported above. |

A DC/AC comparison would require a separate real bus/branch/transformer case, generation/load and limits. It should not be invented by assigning impedance or capacity to the retained 318 abstract edges. None of the present external evidence by itself requires replacing a specific July92 edge: the RS-K–COLORADO relationship remains a model uncertainty needing an independently identified electrical connection before editing topology.

## 12. Direct answers to Reviewer 1 comments

| Comment | Evidence-based answer | Manuscript boundary |
|---|---|---|
| #1 tract–station dependency | Utility-compatible production mapping improves conditional SCE public-candidate overlap, but 480 strict-SCE tracts have no direct July92 candidate. Formal M0/M1 contrasts quantify aggregate and tract impacts; cutoff and supported-candidate subset expose sensitivity. | Call it dependency proxy and external consistency, never verified customer feeder/share. |
| #2 electrical physics | The source gate contributes 4.3–14.9% of baseline hospital-first modeled burden across hazards; dynamic path/concentration and local capacity evidence give concrete physical context. | Power balance, line flows, voltage, dispatch and load shedding remain unmodeled. |
| #3 uncertainty/scheduling | The frozen evaluation uses 4,000 physical DS/duration draws, paired across strategies; task set is DS>0 and completion-event repair uses the same realized duration/crew clock. | No actual earthquake repair durations or observed restoration time validation. |
| #4 repair/source assumptions | Retained positive-duration scenario, 14-source identity audit, gate and resource OFAT quantify their modeled influence; historical events are hazard contexts. | Scenario parameters and Core availability are assumptions, not empirically calibrated dispatch. |
| #5 vulnerability/equity | Q1–Q4 absolute burden, gap, Gini, tract winners/losers, and missing treatment show that a lower Gini can coincide with all groups worsening. | These are distributional model outcomes, not causal equity improvement. |
| #6 GA transparency | Five predeclared seeds, fixed 100×100 budget, best-so-far and incumbent retention, independent 64-sample planning set. All retain impact-first incumbent. | Do not claim a new GA improvement or global optimality. |
| #7 Hospital-first versus GA | Direct-community is the impact-first incumbent; its own planning objective, final community metrics, and hospital rule can rank differently. In 2pc50 impact has lower population but only modestly lower hospital burden than hospital-first. | Do not compare fitness across distinct objectives or force a GA-win narrative. |

The source tables in `Formal_Reviewer_Results/` derive only from the frozen formal archive. The independent candidate benchmark, source identity and capacity records are earlier retained external evidence, clearly separate from the 1,000-sample outcome robustness.
