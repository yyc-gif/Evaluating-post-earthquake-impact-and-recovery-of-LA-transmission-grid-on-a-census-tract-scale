# Restoration priority metrics and recovery dynamics

Methods reference for the July manuscript revision. It documents the implemented rules and recovery dynamics; it does not change a strategy, sequence, simulation, or result.

## Strategy names

`centrality-first` remains the internal strategy ID in the frozen schedules and evaluation records. Its publication-facing name is **Spectral-connectivity-first**. The display mapping changes no sequence values or ordering logic. The other display names are Impact-first, Betweenness-first, Degree-first, Closeness-first, Hospital-first, Vulnerability-first, and Random.

## Priority metrics

Let the frozen station graph be the undirected `MultiGraph` built from the CEC edge list. The production graph stores edge length, but the priority metrics below do not use that length as a shortest-path weight.

**Spectral connectivity impact.** Let `L0` be the largest connected component of the original graph, and let `lambda2(G)` be the second-smallest eigenvalue of the unweighted graph Laplacian. For a station `s` in `L0`,

`I_lambda(s) = max(lambda2(L0) - lambda2(L0 - s), 0) / max(lambda2(L0), 1e-9)`.

If the base `lambda2` is nonpositive, the implementation returns zero scores; stations outside the original largest component also receive zero. The spectral calculation collapses parallel edges to a simple graph before forming the adjacency matrix, so edge multiplicity and `length_km` do not affect this metric. Spectral-connectivity-first orders tasks by decreasing `I_lambda`, then decreasing betweenness centrality, then decreasing degree. The internal strategy ID and these tie-breakers are unchanged.

**Population impact.** For tract `r` with frozen population `P_r` and normalized dependency weight `W[r,s]`, mapped population at station `s` is `M_s = sum_r P_r W[r,s]`. After removing `s`, let `LCC(G-s)` be the remaining largest connected component. The implemented score is

`I_pop(s) = sum_{u not in LCC(G-s)} M_u / sum_u M_u`.

Mapped population outside the remaining largest component is treated as lost from the main energized island. Impact-first sorts this fraction in descending order. This is a network/mapping proxy, not a load-flow or electricity-demand calculation.

**Betweenness centrality.** NetworkX betweenness is computed on the station graph with default normalization and no edge-weight argument. If the graph has more than 1,000 nodes, the implementation samples up to 200 source nodes using the configured fixed random seed; otherwise it computes the exact NetworkX measure. The betweenness-first rule sorts by decreasing betweenness, then decreasing degree.

**Degree.** `G.degree()` is the raw degree on the production `MultiGraph`; parallel edges count with their multiplicity. It is not normalized degree centrality and does not use edge length. Degree-first sorts by decreasing degree, then decreasing betweenness.

**Closeness centrality.** NetworkX `closeness_centrality(G)` is called with its defaults (`distance=None`, `wf_improved=True`). It therefore uses unweighted hop distances and the default disconnected-graph correction; `length_km` is not used. Closeness-first sorts by decreasing closeness, then decreasing degree. Betweenness and closeness traverse distinct neighboring stations, so parallel links do not create shorter hop distances or separate node paths in these unweighted calculations.

**Hospital-first.** For each station, the primary score is the count of its mapping rows whose tract is in the frozen hospital-linked tract set. The secondary score is the sum of the `population` values on that station's mapping rows. Stations are sorted descending on both values. This is an association-based station ranking; it is not hospital electricity demand, the number of electrically served hospitals, or clinical capacity.

**Vulnerability-first.** With frozen SOVI quartile assignments and tract dependency weights,

`V_s = sum_{r in Q4} Population_r * W[r,s]`

and `P_s = sum_r Population_r * W[r,s]`. The sequence sorts by decreasing `V_s`, then decreasing `P_s`, then ascending station ID. Quartiles are supplied frozen inputs and are not recalculated.

**Random.** The implementation copies the passed task-station list and shuffles it with `numpy.random.default_rng(cfg.RNG_SEED)`. Reproducing the permutation requires the same seed and input-list order.

| Strategy display name | Primary ordering metric | Tie-breakers |
|---|---|---|
| Spectral-connectivity-first | Relative clipped loss in unweighted `lambda2` after station removal | Betweenness descending; degree descending |
| Impact-first | Mapped population fraction outside the remaining largest component after station removal | None specified beyond the metric sort |
| Betweenness-first | NetworkX betweenness | Degree descending |
| Degree-first | Raw multigraph degree | Betweenness descending |
| Closeness-first | NetworkX unweighted closeness | Degree descending |
| Hospital-first | Count of hospital-linked tract mapping rows | Sum of mapped-row population |
| Vulnerability-first | Q4 population mapped to station | Total mapped population; station ID ascending |
| Random | Seeded permutation | Input order and fixed seed |

`Redundancy_HHI` remains a tract-level concentration summary of tract-to-substation dependency weights in the community typology. It is not a restoration-priority metric and does not count independent electrical paths.

## Repair duration and recovery state

For a damaged station in damage state `DS`, repair duration is sampled by rejection sampling from `Normal(mu_DS, sigma_DS^2)` until a finite value strictly greater than zero is obtained. `DS0` has zero duration. A sampled duration is an input to scheduling; a mean duration is not substituted for that realization's sample.

In the current formal restoration simulation, station functionality does not follow a normal-CDF curve during repair. Before its scheduled completion event, a station retains its sampled damage-state residual functionality. At completion, raw station functionality changes as a step to `1.0`. The source-connectivity gate is then reevaluated, and tract service availability is updated from the resulting functional, source-connected station state and frozen dependency mapping. The completion event already incorporates the assigned crew's availability, dispatch order, travel, and sampled duration; no independent restoration clock starts after completion.

Within-realization functionality is event-based and stepwise. Smooth-looking realization-mean trajectories arise by averaging different sampled completion events across realizations, not by interpolating a continuous within-repair functionality curve.

## Scope

Functional-network recovery panels describe time-dependent graph topology among stations satisfying the model's functionality threshold. They do not represent physical power flow, delivered electricity, or customer outage observations. Static node-removal percolation calculations and their historical outputs remain available in the research archive but are not shown in active Supplementary Figure S3.
