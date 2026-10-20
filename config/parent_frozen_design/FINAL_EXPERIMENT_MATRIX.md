# July92 Reviewer Revision — Frozen Final Experiment Matrix

**Status: frozen before formal sampling or GA.** Machine-readable authority: `FINAL_EXPERIMENT_MATRIX.json`. This freeze uses revision branch `revision/reviewer-driven-core-rebuild-v2`, with implementation baseline `b88ccbfb19dae5860225dd06c4385de110dcf43f`. The protected July submission commit `182686868cffe962739804f6bc0ccecaed73d601` is untouched. The separate freeze commit is identified by Git history; a commit cannot contain its own SHA. Every future trajectory records the actual executable-code commit SHA.

The study domain remains the retained July **92 stations, 318 edges and 2,315 tracts**. Production uses `JULY_UTILITY_CONSTRAINED_92` with the retained 3% cutoff, the original **14 Core** sources and functionality threshold **0.5**, C57 pooled crews, directed retained road travel without fallback, DS>0 tasks, realized positive DS-specific durations, completion-event restoration and left-rectangle integration. These scientific choices are not to be tuned after inspecting formal results. The gate is a source-connected availability proxy, not delivered electric power.

## Physical samples and strategy design

| Item | Frozen value |
|---|---|
| Hazards | Northridge; SanFernando; LongBeach; 2pc50, in this seed-index order |
| Evaluation | 1,000 **physical** realizations per hazard; independent `SeedSequence([42, hazard_index, 1, realization_index])` streams |
| GA planning | 64 separate 2pc50 physical realizations only; `SeedSequence([42, 3, 0, realization_index])`; never evaluated as final samples |
| Each physical sample | One ordered 92-station DS vector and one positive duration per DS>0 task; DS0 has zero duration and no task; ID and canonical hash saved |
| Paired condition | DS, durations, graph, source set, mapping, directed travel and crew roster identical across strategies within a sample; only full priority sequence changes |
| Non-crew reference | Unconstrained recovery with the same physical sample, completion-state interpretation and production source gate |
| Scheduled strategies | `hospital-first`, `impact-first`, `degree-first`, `closeness-first`, `betweenness-first`, `centrality-first`, `random`, `direct-community` |
| Paired strategy reference | `hospital-first`; unconstrained is reported separately as the no-crew-competition reference |

The full rule sequences remain ex ante, with DS0 removed per realization and no damaged-subset re-ranking. The single `direct-community` sequence selected on 2pc50 planning samples is applied unchanged to **all four hazards**. If it equals a rule incumbent, retain its label and record that it is the same decision, not an independent GA gain. Legacy Balanced/HospFirst/Efficiency surrogate GA runs are not formal strategies. Baseline evaluation therefore has 4 × 1,000 × (1 + 8) = **36,000 trajectories**, but only 4,000 independent evaluation damage draws.

## Direct GA search

Five independent seeds **42–46**, each with population **100**, **100 fixed generations**, ordered crossover probability **0.8**, inversion mutation probability **0.2**, tournament size **3**. The chromosome is a full 92-ID permutation. For every seed, the seven deterministic rule sequences are scored on the **same 64 planning samples** and retained as incumbents. The objective maximizes the negative mean population-times-resolved-mass cumulative tract service burden. Every candidate is decoded through DS>0 task filtering, event crew scheduling, completion functionality, the production source gate and production mapping, then integrated on exact events. The old station-completion surrogate is excluded.

Save generation best, generation mean, best-so-far, incumbent score, best generation, final-candidate source and five-seed convergence. Select the highest retained fitness; exact fitness ties use the smallest seed. If search does not improve the best deterministic incumbent, freeze that incumbent and say so. Do not extend the budget to obtain improvement. The 64 planning samples are never used to estimate final comparative effects.

The candidate objective uses one **planning-only fixed horizon**: before search, `H_plan = max(480 h, max_planning_sample [sum of positive task durations + task_count × largest finite directed travel cell])`. This conservative bound is independent of candidate order and of evaluation samples; it prevents a candidate-specific truncated objective. The same event integration applies to every candidate.

## Resource and evaluation robustness

Only 2pc50 receives resource sensitivity, reusing its same 1,000 evaluation physical samples. This is **one factor at a time**: crew scales 0.5/1/1.5/2 with duration scale 1; duration scales 0.75/1/1.25/1.5 with crew scale 1. The retained deterministic depot-scaling rule gives crew totals **29/57/86/114**. Duration scales multiply the *saved* durations; no DS or duration redraw. Baseline 1/1 is reused. The six nonbaseline cases add 1,000 × 8 scheduled strategies × 6 = **48,000 scheduled trajectories**. There is no crew-by-duration Cartesian product, and no separate no-crew run for crew-scale changes.

Every four-hazard baseline station trajectory is evaluated under both `M0_JULY_003` and production `M1_UTILITY_003`, with production `G1_BASELINE_050`. For **2pc50/C57 only**, evaluate all seven predefined mappings (`M0/M1` at 3%, no cutoff and 1%, plus `M3_SCE_SUPPORTED`) crossed with G0 ungated, G1 0.5, G2 0.05 and G3 0.75. These are offline views of **the same station trajectories**; no policy redesign or resampling. M3 reports all 337 comparable SCE tracts, including 17 unresolved rows, and the common 320 positive-mass tracts separately. Neither candidate evidence nor missing mass is reassigned to another station. No two-path production gate or alternate source subset is introduced.

At every station and event, retain `f`, `F`, `C`, `e`, and `L_self=1-f`, `L_threshold=f(1-F)`, `L_source=fF(1-C)`, `L_total=1-e`; verify additive conservation within `1e-12`. Propagate each component through M1 and integrate it. T50/T80 are nonlinear and are **not** additively decomposed. Dynamic topology records reachable sources, independent-path/min-cut measures where defined, bridge/articulation and single-path dependence; assess the eight static single-path stations, COLORADO, and tracts where modeled source loss exceeds local damage loss. These remain abstract-network diagnostics.

## Common horizon and result definitions

First decode all frozen evaluation sequences and OFAT schedules. **Before tract integration**, choose one common `H_eval = max(480 h, ceil(maximum task completion over all four hazards, 1,000 samples, eight scheduled strategies and six extra resource cases))`. Use it for every evaluation comparison; never truncate a >480 h completion silently or give a strategy its own horizon. T50/T80/T90 not reached by that horizon are `NA`.

For each hazard × strategy at baseline C57, retain population T50/T80, cumulative burden, represented population and mass, hospital-tract burden, Q1–Q4 **absolute** burdens, signed and absolute Q4−Q1 gaps, and population-weighted burden Gini. Save tract normalized burden, strategy-paired differences, M1−M0 differences and the three cumulative loss components. Keep both denominators distinct: `Σ(pop × normalized tract burden)/Σ(pop)` over resolved tracts, and `Σ(pop × burden mass)/Σ(pop × resolved mass)` over resolved tracts. Zero resolved mass is unresolved/NA, never zero burden or recovery.

Relative to `hospital-first`, report paired mean/median differences, direction probability and percentile 95% interval from **10,000 realization-level paired bootstrap resamples**, seed 42. For tract effect labels use ±1 h as a practical threshold, not a significance test; retain improved, near-zero, worsened and unresolved counts and populations. Do not treat tracts as independent earthquakes.

After the formal 1,000-sample results, rerun the retained Stage 7 vulnerability, built-environment, risk, service/recovery and grid/dependency typology, PCA/K-means diagnostics and descriptive hotspots. A feature is excluded only if it is still constant in the formal results, with that exclusion recorded. Clusters and hotspots are descriptive, not causal.

## Identity, sequence and execution boundary

Every archived trajectory must carry hazard, physical ID, planning/evaluation split, strategy, resource case, DS/duration hashes, graph/source/mapping identifiers, crew/travel hashes, common event horizon and actual code commit SHA. Paired comparisons fail if relevant physical/context identity differs. Save the physical samples once; freeze the GA sequence before evaluation; then execute the 36,000 baseline and six OFAT cases, offline mapping/gate views, Stage 6 maps/summaries and Stage 7. Resume may reuse the same frozen inputs; it may not redraw them or alter the matrix after seeing results.

**This commit freezes design only.** The current small-trial entrypoint still has trial values and a 480-hour rejection. Before formal sampling, its execution configuration must be aligned with this matrix: 1,000 evaluation and 64 planning samples, planning **only** for 2pc50, five seeds, fixed planning/common evaluation horizons, formal archive identity, and revised event-based OFAT resource cases. Those are implementations of the already frozen design, not invitations to revise its hazard, topology, mapping, gate, objective or sample counts. No formal sample generation, GA search or scientific trajectory is authorized to be described as completed by this freeze commit.
