# GA search-budget sensitivity and figure interpretation — 2026-10-07

Base: `09fa6b08da4aaa0d88bde9b4bd62e4a567ccc6fe`, branch `revision/reviewer-driven-core-rebuild-v2`. Execution completed locally on 2026-10-08. This is a separate planning search-budget diagnostic, not formal strategy replacement.

The original 100-generation search retained Impact-first because it was the best initial incumbent and no candidate strictly improved it. Twenty 250-generation searches improved that incumbent in **16/20 seeds**. Best planning loss fell from **33.578302560 to 33.272768350 h**, an improvement of **0.305534210 h (0.909916%)**, seed **48**. The original result is therefore a finite-budget result. No formal policy order or evaluation result has been replaced.

## Objective and search implementation

Impact-first is one fixed-rule incumbent, not the fitness function. Let π be a full permutation of 92 stations; b indexes the 64 saved planning realizations; r indexes tracts; i indexes stations; P_r is tract population; W_ri is the unchanged dependency weight; m_r = Σ_i W_ri; and e_bi^π(t) is functionality credited only when the station meets the 0.5 functionality threshold and connects to an active Core source. The exact objective is

$$
J(\pi)=\frac{1}{64}\sum_{b=1}^{64}
\frac{\sum_r P_r\int_0^H [m_r-\sum_i W_{ri}e_{bi}^\pi(t)]\,dt}
{\sum_r P_r m_r},\qquad F(\pi)=-J(\pi).
$$

Lower J is better; the GA maximizes F. H = **2855.254013110100 h**, the same fixed pre-search bound as the formal planning run, not the 480 h evaluation horizon. Event integration, directed travel, earliest-release-crew scheduling, source gate and station population mass use the existing exact kernel. The chromosome contains every station once; its combinatorial domain is **92!**. DS>0 filtering is applied only when decoding each saved realization into damaged tasks.

The seven fixed orders—Centrality-first, Impact-first, Betweenness-first, Degree-first, Closeness-first, Hospital-first and the fixed Random order—are directly scored, inserted in the initial population, and complemented with random full permutations. The best incumbent initializes the archive before generation 0. The unchanged update is `if scored[idx] > archive_score`: equality never replaces it. The archive is preserved separately; it is not an elite forcibly reinserted in every offspring population. Operators remain ordered crossover probability 0.8, inversion mutation probability 0.2 and tournament size 3.

Baseline replay reproduces all original generation-best, generation-mean and archive histories for seeds 42–46 within 1e-9. The original CSV histories do not log candidate identities; unique/tie counts below come from instrumented exact baseline replay, not an inference from the old five flat archive curves. The wrapper logs objective calls and generations without changing RNG calls or operators. A shared exact-score memo avoids recomputing identical permutations between runs; each seed still follows its independent original RNG stream.

## Staged budget and stopping decision

| Stage | Population | Generations | Seeds | Completed result |
|---|---:|---:|---|---|
| Baseline | 100 | 100 | 42–46 | Five exact history replays; no improvement |
| A | 100 | 250 | 42–46 | Four seeds improved; first improvement in seed 42 |
| A, larger generation budgets | 100 | 500 / 1000 | Not run | Skipped under the requested early-improvement stop rule |
| B | 250 / 500 | 500 | Not run | Skipped under the same stop rule |
| C | 100 | 250 | 42–61 | Twenty independent seeds total; includes Stage A's five |

Thus 25 complete runs are recorded, without double-counting Stage A in Stage C. Larger budgets have not been tested and no claim is made about them.

## Original-budget candidate audit

| Seed | Unique permutations | Incumbent F | Generated best F | Generated ΔJ (h) | Exact ties | <1e-6 h | <1e-4 h | <1e-3 h | <1e-2 h | Generation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | 7776 | -33.578302560 | -33.984268591 | 0.405966031 | 0 | 0 | 0 | 0 | 0 | 96 |
| 43 | 8209 | -33.578302560 | -34.814553311 | 1.236250751 | 0 | 0 | 0 | 0 | 0 | 89 |
| 44 | 8253 | -33.578302560 | -34.274036558 | 0.695733998 | 0 | 0 | 0 | 0 | 0 | 80 |
| 45 | 7628 | -33.578302560 | -34.022506428 | 0.444203868 | 0 | 0 | 0 | 0 | 0 | 98 |
| 46 | 8202 | -33.578302560 | -34.101173692 | 0.522871132 | 0 | 0 | 0 | 0 | 0 | 95 |

## Expanded-budget candidate audit

| Seed | Unique permutations | Incumbent F | Generated best F | Generated ΔJ (h) | Exact ties | <1e-6 h | <1e-4 h | <1e-3 h | <1e-2 h | Generation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 42 | 15983 | -33.578302560 | -33.398853585 | -0.179448975 | 0 | 0 | 0 | 0 | 97 | 250 |
| 43 | 19369 | -33.578302560 | -34.001644858 | 0.423342298 | 0 | 0 | 0 | 0 | 0 | 246 |
| 44 | 17251 | -33.578302560 | -33.459962570 | -0.118339990 | 0 | 0 | 0 | 2 | 54 | 249 |
| 45 | 14387 | -33.578302560 | -33.442045012 | -0.136257548 | 0 | 0 | 2 | 13 | 131 | 246 |
| 46 | 16757 | -33.578302560 | -33.534548069 | -0.043754491 | 0 | 0 | 0 | 0 | 0 | 250 |
| 47 | 18263 | -33.578302560 | -33.378814227 | -0.199488333 | 0 | 0 | 0 | 5 | 58 | 247 |
| 48 | 13764 | -33.578302560 | -33.272768350 | -0.305534210 | 0 | 0 | 4 | 25 | 228 | 250 |
| 49 | 14010 | -33.578302560 | -33.335713215 | -0.242589345 | 0 | 0 | 0 | 5 | 73 | 245 |
| 50 | 18176 | -33.578302560 | -33.523596349 | -0.054706211 | 0 | 0 | 2 | 31 | 308 | 248 |
| 51 | 14029 | -33.578302560 | -33.454026802 | -0.124275758 | 0 | 0 | 4 | 38 | 397 | 248 |
| 52 | 14217 | -33.578302560 | -33.332358520 | -0.245944040 | 0 | 0 | 0 | 4 | 45 | 250 |
| 53 | 14539 | -33.578302560 | -33.443903678 | -0.134398882 | 0 | 0 | 3 | 10 | 115 | 247 |
| 54 | 16141 | -33.578302560 | -33.546994540 | -0.031308020 | 0 | 0 | 0 | 7 | 350 | 250 |
| 55 | 17896 | -33.578302560 | -33.734069884 | 0.155767324 | 0 | 0 | 0 | 0 | 0 | 246 |
| 56 | 16743 | -33.578302560 | -33.552451063 | -0.025851497 | 0 | 0 | 1 | 7 | 439 | 250 |
| 57 | 14167 | -33.578302560 | -33.553799468 | -0.024503092 | 0 | 0 | 0 | 0 | 0 | 246 |
| 58 | 15889 | -33.578302560 | -33.390535815 | -0.187766745 | 0 | 0 | 0 | 0 | 79 | 245 |
| 59 | 20151 | -33.578302560 | -33.894914762 | 0.316612202 | 0 | 0 | 0 | 0 | 0 | 1 |
| 60 | 14919 | -33.578302560 | -33.482594542 | -0.095708018 | 0 | 0 | 3 | 14 | 169 | 250 |
| 61 | 19306 | -33.578302560 | -33.869136881 | 0.290834321 | 0 | 0 | 0 | 0 | 0 | 250 |

Counts refer to unique permutations within each run. Exact/near ties exclude all seven deterministic incumbent permutations; thresholds are absolute differences from Impact-first J and are cumulative. Fitness has the opposite sign to service loss. Full sequence SHA-256, all 92 IDs, first generation, rank correlation, displaced stations and top-10 overlap appear in `GA_SEARCH_BUDGET_SENSITIVITY.csv` and each `RUN.json`.

## Best candidate and planning-realization interpretation

Seed 48 found its best generated sequence at generation 250. It displaces 88 stations, has rank correlation 0.815437 with Impact-first and top-10 overlap 6/10. Its sequence identity is `17a3313cdd9a6d26bc73ba27daf185dd6fb6971459d31b9ca58b240fed63e69e`.

On the same 64 planning realizations, mean new-minus-Impact-first change is **-0.305534210 h** and median is **-0.209837306 h**. Loss is lower in 54, higher in 10 and identical in 0 realizations. The minimum/maximum changes are -1.250860/0.180151 h. All 64 individual differences are saved. These are planning comparisons, not 1,000-realization generalization evidence.

All 20 extended runs have distinct best non-incumbent sequence identities. The largest reduction is less than 1% of the incumbent planning loss, with varied realization effects. It warrants consideration as a separate search-budget result; it does not justify automatic replacement or a claim of global optimality. Re-freezing and independent evaluation would require the author's explicit approval.

## Objective landscape and effective ordering

325,824 distinct full permutations were scored across the 25 runs. **No generated non-incumbent tied Impact-first exactly**. Near-equivalent values exist at the reported tolerances. `OBJECTIVE_LANDSCAPE_AUDIT.csv` separately counts identical floating-point fitness values among different permutations; identical objectives need not imply identical task order.

Across the 64 saved planning samples, DS0 excludes only 0–2 tasks per sample. Many samples include all 92 stations as damaged tasks. Consequently, the joint 64-sample effective-order signature has **zero collisions between distinct full permutations** in every run. DS>0 filtering cannot explain a broad joint-order plateau here. Some individual samples collapse a few orders, and some distinct orders produce equal objectives, but an exact plateau at Impact-first is not supported. Improved candidates at 250 generations demonstrate that the 100-generation archive did not establish an optimum.

## Figure S04: manuscript/meeting interpretation

Figure S04 compares structural fragmentation under station removal with structural recovery under the evaluated restoration policies. (A) Static station-removal curves start from the intact 92-node graph and measure the largest connected component after targeted or random removals. Network λ2 impact is the spectral topology-impact removal metric, not the population-impact ranking used by the restoration policy Impact-first. Targeted orders are ranked once in the intact graph; the Random curve uses the saved single random order, not a Monte Carlo interval. These attack curves diagnose structural criticality; they do not identify an optimal repair order. (B/C) Recovery curves use 1,000 2pc50 realizations per policy, 57 crews and repair-duration multiplier 1.00, displayed over 0–120 h. For each realization and time, the functional network is the induced subgraph of stations with modeled functionality at least 0.5; edges join functional endpoints. B is the mean of |LCC|/92, with the original 92-station count as denominator. C is the mean of 2E_LCC/N_LCC, where E_LCC counts edges with both endpoints in that realization’s largest component. Empty networks contribute zero, and a singleton has degree zero. The means are taken after calculating each realization’s component; they are not metrics of an average network. No confidence interval or realization range is encoded. The curves converge toward the intact graph, whose mean degree is 636/92 = 6.913. Unconstrained develops its largest component sooner, while scheduled policies differ in the evolution of component size and internal degree. Structural connectivity alone does not establish community service-loss ordering, optimal restoration, delivered MW or electrical adequacy. Unlike S04, S07 asks whether functional stations can reach an active Core source and how alternate routes improve source reachability relative to a fixed precomputed path. A large component in S04 need not contain an active Core source. S04 therefore describes network structure, while S07 describes source-connected service and route redundancy.

Formally, the plotted quantities are `mean_b(|LCC_b(t)|/92)` and `mean_b(2E_LCC,b(t)/N_LCC,b(t))`, not a source-connected fraction or mean degree over every functional component. All policies use the same physical realization family and graph; only fixed repair order differs. The display table is `results/revised_suite/LA_Grid_Revised_Suite_20260925/Stage 6 Output_expanded/NETWORK_TOPOLOGY_DISPLAY_CURVES_2pc50.csv`; its creation logic is `src/la_grid/plotting/render_revised_suite.py`, functional-mask/LCC display section. Panel A uses the saved Stage 2 percolation curves. The complete PDF was actually opened before and after the stroke correction.

**Figure S04 shows how station removal fragments the network and how the largest functional component and its internal degree recover under the evaluated policies.**

## Figure S05: corrected interpretation

Genetic algorithm (GA) searches used the same 64 2pc50 planning realizations and direct population-weighted service-loss objective. (A) Best generated candidate excluding all seven fixed-rule incumbent permutations, by generation, for seeds 42–46 at population 100 and 100 generations. (B) Final best generated candidates from population 100 and 250 generations for 20 seeds (42–61); original 100-generation results are also shown for seeds 42–46. The black dashed reference is Impact-first (33.578 h). The initial population includes the seven incumbent sequences, and the archive is initialized with the best incumbent before generation 0. The archive is replaced only by a strictly better candidate. Thus the identical retained sequence in the original five searches means that no tested candidate improved Impact-first within that budget; it does not mean the searches independently rediscovered its permutation. Extending to 250 generations yielded strict improvements in 16 of 20 seeds, with best reduction 0.306 h (0.91%). Generated candidates and retained archives are different: a worse generated result does not displace the incumbent. Planning loss uses the same pre-search horizon of 2,855.254 h, distinct from the 480 h evaluation window. Seed points encode individual search results, without an uncertainty interval. The original retained Impact-first order remains the order used in the policy evaluation; expanded-budget sequences have not been evaluated on its 1,000-realization set. These finite-budget comparisons do not establish global optimality.

## Figure S06: unified scope

Title: **Dependency mapping and service-gate sensitivity**. Narrative scope: **dependency and service-model assumptions**.

Supplementary Figure S6 tests dependency and service-model assumptions, including the tract–substation mapping-weight cutoff, agreement with public SCE assignments for 337 comparable tracts, source-connectivity gating, and the station functionality threshold. The public-record comparison provides supporting agreement, not feeder validation or service-territory ground truth. Sensitivity contrasts retain the production mapping and physical realizations except for the stated assumption; they do not create another production mapping.

## Records, identity and boundary

`results/diagnostics/ga_search_budget_20261007/` contains input identities, planning-sample hashes, stopping decision, full CSV summary and every complete run. Each run contains `RUN.json`, generation history, all unique candidate permutations/fitness/first generation in `CANDIDATES.npz`, and 64 realization-specific comparisons. The generated-candidate diagnostic is `GA_SEARCH_BUDGET_DIAGNOSTIC.pdf/.png`, also integrated into current S05.

Formal GA outputs, physical samples, mapping, source gate, evaluation schedules/trajectories, equity and capacity numerical results are preserved. New numerical files belong only to this explicitly authorized planning diagnostic. Presentation corrections also address the author's pending map, metric, legend, station-point and equal-priority-map requests; they do not change source values or cluster IDs. Verification results are recorded separately after testing and canonical resume.
