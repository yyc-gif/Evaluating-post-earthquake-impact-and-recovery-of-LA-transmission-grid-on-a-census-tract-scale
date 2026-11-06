# Contribution 1 mechanism test: registered execution protocol

**Branch:** `research/c1-mechanism-actionability-20261105`  
**Protocol baseline:** `7704f766a648f6631acc474a8b02eb6e357adbc2`  
**Status:** fixed before paired counterfactual experiments.

## Question and alternatives

Test why frozen repair sequencing changes source-path service loss. The registered alternatives are: (H1) a completed repair newly connects already-functional downstream substations; (H2) apparent leverage is governed by repair duration, crew-clock position, and directed travel; (H3) self-functionality loss is large in absolute terms but less responsive to order because repair durations and task distribution constrain how early it can be removed; (H4) component differences are sensitive to the sequential accounting/gate definition; and (H0) the available frozen model does not distinguish these mechanisms robustly. The analysis may support none, one, or several alternatives. It does not test real customer outages or physical power flow.

## Frozen scope

Primary case is `2pc50 / C57_D1 / M1_UTILITY_003 / G1_BASELINE_050 / 480 h`, with all 1,000 evaluation realization identities and the existing 92 ordered substations, 14 Core sources, graph, crew-origin roster, directed travel matrices, mapping weights, and repair durations. The paired scheduled set is Impact-first, Hospital-first, Degree-first, Betweenness-first, Vulnerability-first, Random, and Centrality-first where archived. Unconstrained is evaluated from the same physical samples without a constrained schedule. Direct-community is not counted as independent where its sequence duplicates Impact-first. Northridge, San Fernando, and Long Beach are secondary context checks only; between-hazard contrasts are not interpreted as pure shaking-intensity effects. Resource sensitivity is secondary and is run only after primary identity and additivity gates pass.

No damage sampling, fragility calculation, source-gate recalibration, repair-duration sampling, GA optimization, or formal trajectory generation is authorized. The existing exact schedule decoder may be used for paired sequence perturbations on the same frozen DS/duration vectors.

## Estimands and checks

For each realization and schedule, use the production completion-step functionality and source gate. Integrate `L_self = 1-f`, `L_threshold = f(1-F)`, `L_source = fF(1-C)`, and `L_total = 1-fFC` over exact completion-event intervals through 480 h. The realization-level population-weighted burden is computed from the frozen tract-to-station weights and formal population denominator. Require eventwise and integrated component additivity with maximum absolute error below `1e-10 h`; require exact pairing by physical-input hash, ordered station IDs, DS hash, and duration hash. Reproduce the saved unconstrained component means and Degree-first minus Hospital-first paired effects before interpreting mechanisms. Bootstrap uncertainty resamples realization IDs as paired units; the saved 5th–95th realization range is never called a confidence interval.

For event unlocking, simultaneous completions at identical timestamps are one event batch. Report direct changes at repaired stations separately from gains at other stations whose threshold eligibility did not change but which become source-connected. Summarize event records by realization and strategy before uncertainty calculations; event rows are not independent replicates. Report pre-event topology and crew-clock descriptors as descriptive predictors, not causal effects.

## Paired local sequence perturbations

First run an identity/runtime smoke pilot on realization IDs 0000–0007; these eight are excluded from the registered perturbation estimate. The main sample is 128 realization IDs drawn without replacement from 0–999 with `numpy.random.default_rng(20261105)`. Save the full ordered ID list. On each selected realization, use the exact frozen sequence and decoder, and move a damaged target earlier by 1, 3, or 5 positions in the full station permutation while preserving the relative order of all other stations. Analyze the same selected IDs under Impact-first and Hospital-first baseline orders.

Select four target categories per baseline realization: (1) station at the baseline event with largest observed indirect source-connected availability gain (explicitly outcome-informed descriptive category); (2) largest direct mapped-population-weighted initial self-loss mass; (3) highest pre-event hypothetical external unlock potential among stations at or below the median direct mass; and (4) a uniformly selected damaged station using a separate fixed seed `20261106`. Record overlaps and unavailable categories; do not replace missing categories with a more favorable station. The dynamic-potential calculation sets only the target station to its post-completion functionality in the recorded pre-event state, leaves all other states unchanged, and measures newly connected non-target mapped mass.

Outcomes are paired change in total and each component burden, target completion time, crew assignment/travel, and first connection time. Use 10,000 paired bootstrap resamples of realization IDs with seed `20261107`. Report the full sign distribution and estimates; no minimum practically important effect threshold is imposed because no externally justified threshold is registered in the source materials. Do not convert statistical significance into engineering importance.

## Controls and interpretation rules

Re-run the same frozen completion histories through the production `no_gate` identity-gate mode as a mathematical accounting ablation only. It is not a feasible-service scenario. Keep baseline burden distinct from paired policy responsiveness; do not divide one by the other and call it elasticity. Show self, threshold, and source components in hours as well as shares. Report the 480-h horizon and state explicitly that availability is a topological service proxy, not MW or customer outage data.

H1 requires replicated event-level external gains plus paired local movement evidence with both beneficial and harmful examples; an algebraic decomposition alone is insufficient. H2 requires explicit association with duration/crew-clock/travel and a labeled travel diagnostic; it is not inferred from dispatch rank alone. H3 is assessed from absolute baseline burden and paired responsiveness separately. H4 is assessed by component changes under the no-gate control and by preserving the exact sequential decomposition. If estimates are weak, contradictory, subset-sensitive, or fail identity checks, conclude that the mechanism is unresolved. No composite evidence score or retrospective threshold selection is allowed.

## Reproducibility and outputs

All inputs are hash-registered before execution. The analysis script must be deterministic, preserve source files, write only under `results/research_contribution1_20261105/`, and emit machine-readable realization-level, event-level, perturbation, and QA outputs. Figures use realization-clustered uncertainty and label the simulation quantities as modeled. A clean rerun must reproduce output hashes except for explicitly documented environment metadata.
