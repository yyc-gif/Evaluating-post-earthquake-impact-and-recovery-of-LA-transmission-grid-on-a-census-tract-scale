# Research task C1 — What makes a service-loss mechanism responsive to repair sequencing?

**Status:** execution brief for the local research agent, not an experimental result.
**Starting point:** `review/1021-rq-aligned-results`, isolated working branch `research/c1-mechanism-actionability-20261105`.
**Priority:** actual reproducible mechanism investigation; not manuscript rewriting or figure styling.

## Scientific question and falsifiable alternatives

Observed in the saved analysis: asset-functionality loss contributes most of total unconstrained loss, while improvements between some constrained restoration policies occur mainly through source-path loss. **The mere arithmetic observation is not a contribution.** Investigate **why** repair-order changes preferentially alter some loss mechanisms, and under what damage, topology, and crew conditions this relationship holds.

Candidate explanations to test, not assume:
- **H1, topological unlocking:** a repaired station changes access to upstream sources for a large dependent population, producing indirect service gains outside its own tract dependency mass.
- **H2, repair-duration/crew-clock leverage:** source-path gains concentrate in early, short or strategically positioned repair completions; apparent topological leverage disappears after controlling for task duration, scheduling time, and crew travel.
- **H3, limited actionability of self loss:** substantial self loss persists even with advantageous sequencing because damage-specific repair durations and distributed tasks limit how much earlier the contributing stations can be restored.
- **H4, accounting artifact:** the apparent difference reflects the sequential partition `1-fFC=(1-f)+f(1-F)+fF(1-C)`, the chosen source gate/threshold, or mixing unconstrained baseline shares with constrained-policy deltas, not a robust effect of topology on marginal scheduling opportunities.
- **H0:** no robust mechanism pattern beyond these definitions; report a null result and do not claim Contribution 1 as established.

## Frozen evidence to reproduce *before* new analysis

From `results/figure_review_rq_aligned_20261101/QA/FIG03_COMPONENT_SHARE_QA.json`, 2pc50 **unconstrained** / 1,000 realizations: `L_self=26.88724724 h`, `L_threshold=0.87649177 h`, `L_source=3.57403797 h`, `L_total=31.33777698 h`; shares 85.798%, 2.797%, 11.405%. These are averages of source-component integrals, *not* shares for an Impact-first or GA schedule.

From `.../QA/FIG04_MECHANISM_AND_OUTCOME_QA.json`, 2pc50/C57_D1/1,000 **paired** Degree-first minus Hospital-first: self **+2.94470195 h**, threshold **+0.10323440 h**, source **−1.64669241 h**, total **+1.40124395 h**. Saved 5–95% whiskers are realization ranges, NOT confidence intervals.

From saved final GA diagnostics, GA minus Impact-first independent validation: source about **−0.8208 h**, self **+0.2775 h**, threshold **+0.0106 h**, total **−0.5327 h** (separate 2,000 held-out realizations; confirm identity and provenance locally). Do **not** conflate these three populations/designs, or divide a policy delta by an unconstrained baseline share and call it a sensitivity.

Before analysis, reproduce the published QA numbers with exact realization keys and reconstruct the mathematical loss identity to numerical precision.

## Authoritative existing implementation and archives

Read actual execution paths, not AI summaries:
- `src/la_grid/revision/r1_realization_scheduling.py`: C57 earliest-available-crew dispatch, DS0 filtering, directed travel, DS-specific realized durations, completion-step functionality.
- `src/la_grid/revision/r1_source_gate.py`: `f`, `F`, `C`, `e=fFC`, and `L_self=1-f`, `L_threshold=f(1-F)`, `L_source=fF(1-C)`, `L_total=1-e`.
- `src/la_grid/revision/r1_ga_exact_kernel.py`, `src/la_grid/diagnostics/r1_formal_mechanism_results.py`, and dynamic connectivity diagnostics in `src/la_grid/diagnostics/r1_dynamic_topology_kernel.py`.
- Frozen arrays under `Formal_Experiment_20260923/Stage 1 Output_expanded/`, `Formal_Experiment_20260923/Formal_Trajectories/<hazard>/C57_D1/<policy>/`, `Formal_Experiment_20260923/Formal_Offline_Evaluation/`, and `Formal_Experiment_20260923/Formal_Reviewer_Results/`. Use the paths actually present locally; do not silently substitute placeholders or legacy outputs.
- `Data/JULY_UTILITY_CONSTRAINED_92.csv` (M1 map), `Data/substation_graph_CEC_edges_expanded.csv`, and `Data/source_nodes_core_expanded.csv`.
- `docs/methodology/METHODOLOGY_CODE_SYNC_AUDIT.md`, `docs/methodology/FRAGILITY_CONNECTIVITY_AUDIT.md`, and `docs/reproducibility/SOURCE_CONNECTIVITY_ROUTE_REQUIREMENT_REPORT.md`.

**Freeze:** 2pc50 first; C57_D1, M1_UTILITY_003, G1_SOURCE_GATE_050, original 92-station graph, 14 Core sources, 480 h horizon, exactly the same DS/duration/crew origins/travel matrix/tract mapping across paired policies. The model is a **topological service-availability proxy**, not AC/DC flow or actual delivered MW. Preserve original sample IDs, hashes, policy sequences, GA validation distinctions, and existing Figure 1–7/S1–S9 assets. Some remote data are LFS pointers; verify locally materialized payload before running.

## Work package A — audited matched-pair contribution table

For Impact-first, Hospital-first, Degree-first, Vulnerability-first, and the retained GA candidate (where available), evaluate **on the same frozen realization population**:
1. Report absolute population-weighted integrated loss for `self, threshold, source, total` (not only percentages).
2. Compute `Δ_c(r,policy A→B)=L_c(r,B)-L_c(r,A)` for identical physical realization `r`. Give mean, paired 95% bootstrap CI, 5–95% individual-realization range, and count of sign reversals **with distinct labels**.
3. For source vs self changes, distinguish differences in *baseline burden* from differences in *policy responsiveness*. Compare within each common resource regime; do not infer a causal elasticity from cross-regime averages.
4. Show change in tract- and station-attributed source loss using existing source-loss tables. Identify whether gain comes from a few highly dependent locations or is broadly distributed.

Start with 2pc50 1,000 realizations and existing independently validated GA subset, then spot-check Northridge, SanFernando and LongBeach; their anchored/unanchored fragility parameters differ across scenarios, so **do not interpret between-hazard contrasts as a pure shaking-intensity experiment**.

## Work package B — event-level network unlocking (mechanism, not illustration)

On each recorded repair completion event, use left/right station states, threshold eligibility, active-source connectivity, and unchanged tract mass:
- Report immediate change in weighted modeled service `ΔS` at the event, and its station-level direct and indirect parts.
- For a single repaired station j, separate improvement at j from gains at **other** stations that become connected to any active source. Identify indirect gains only when their F status did not itself change in that event. If multiple completions have identical timestamps, report as a batch; never arbitrarily credit one station.
- Record damaged-node DS, duration, start/end time, crew, travel delay, whether node newly passes F=0.5 threshold, and newly source-connected station counts and population-dependency mass.
- Compare large indirect-unlock events with station source-path centrality, pre-event active component, bridging or alternative route count, and local tract mass; **do not equate static degree/betweenness with event-time marginal benefit**.
- Explicitly investigate DS1 (= already eligible with f=.50) versus DS2–DS4 repairs: a DS1 completion can increase its own f without newly enabling a source path, whereas a newly eligible bottleneck can unlock other functional stations.

Deliver a ranked, provenance-backed event table with a few visualized pre/post induced-subgraph examples. Label descriptive associations as descriptive.

## Work package C — matched local scheduling counterfactuals

To test whether an event or topological indicator predicts actionable recovery, perturb the *actual static full priority sequence* for the **same** DS and realized-duration draw:
- Preserve the set of tasks, original station IDs, time horizon, functionality law, crew origins, and directed travel. Implement moves of one damaged target earlier by 1 rank and by 3–5 ranks (where valid), retaining relative order of others. Re-run the exact C57 earliest-release decoder, not a surrogate.
- Select candidate targets by predefined categories: (i) high observed downstream-unlock, (ii) high own population mass / direct loss, (iii) topological bottleneck with low direct demand, and (iv) random/matched control. Avoid cherry-picking only successful swaps.
- Record per-realization counterfactual difference in total and each loss component, station completion changes, total travel, and first-source-connection times. Some moves will be harmful; include them.
- First run a **small fixed-seed pilot**, verify all identities and runtime, then cover a predeclared sample of 2pc50 realizations; extend only if reproducibility gates pass. A policy shift can change crew assignment and travel time, so use a separate labeled no-travel or fixed-travel ablation to distinguish route effects from sequencing effects; neither ablation replaces production results.
- Repeat strategically selected perturbations across baseline policies to determine whether topology-mediated benefits depend on where the sequence already places the same station.

**Decision criterion:** show a reproducible association between a *pre-event* actionable predictor (e.g., accessible dependency mass unlocked by repairing one node, dynamic source-cut position, or repair-clock context) and paired reduction in cumulative community loss, over a valid mix of positive/negative examples. An algebraic decomposition or selected anecdote is NOT sufficient.

## Work package D — controls, identifiability, and sensitivity

1. Run the same completion histories through `no_gate` **only as a mathematical ablation**, not a claim of feasible electricity service; compare ranking and decomposition behavior.
2. Inspect whether the sequential accounting convention assigns part of one physical episode to a different named component when thresholds or connectivity settings change. No unqualified causal attribution from `L_self`, `L_threshold`, `L_source` alone.
3. Use the existing frozen-source-reliability and k-independent-route diagnostics as checks. Do NOT claim k=2/3 routes physically required; the repository already shows k=3 creates structural unmet-service ceilings.
4. For station/tract/realization dependence, report aggregation level clearly; do not treat the thousands of event rows from one realization as statistically independent. Prefer realization-level paired uncertainty and grouped event analyses.
5. Check sensitivity to repair-duration regime and crew count **only after** baseline mechanism test. Do not change fragility assumptions or post hoc optimize a new policy merely to make a finding stronger.

## Files to produce in this *new* branch, once locally executed

- Executable diagnostic under `src/la_grid/diagnostics/` or `research/`, with README and deterministic invocation; no edits to original production kernels.
- `results/research_contribution1_20261105/PAIRED_COMPONENT_EFFECTS.csv`
- `results/research_contribution1_20261105/REPAIR_EVENT_UNLOCKS.parquet` (or CSV), with provenance fields.
- `results/research_contribution1_20261105/LOCAL_PRIORITY_PERTURBATIONS.parquet` (or CSV)
- `results/research_contribution1_20261105/FIG_MECHANISM_UNLOCK.pdf` and `FIG_MARGINAL_REPAIR_BENEFIT.pdf` with readable axes and honest uncertainty.
- `docs/research/CONTRIBUTION1_MECHANISM_FINDINGS_20261105.md` distinguishing **observed, diagnostic, inferred, and unverified** claims, with exact inputs, sample counts, confidence method, limitations, and a *yes/no* decision on scientific novelty.
- A PR from this branch with tests, result hashes, and exactly what changed.

## Non-negotiable quality gates

- All input files and historical results are read-only; no silent recalibration, reoptimization, resampling, figure replacement, or manuscript edits.
- Preserve expected 2pc50 QA; `L_self+L_threshold+L_source=L_total` at event and integrated scales (target max error <1e-10 h).
- If the preserved model cannot recreate baseline findings or exact local data are missing, stop and report the precise blocking paths. **Do not invent data or substitute AI-produced summaries.**
- A negative or weak finding is acceptable and should be stated clearly. If H1–H3 cannot be distinguished from accounting artifacts or scheduling side effects, Contribution 1 remains a research question, not a claim.
- This work must produce actual scientific test results, not merely another plan or a revised contribution paragraph.
