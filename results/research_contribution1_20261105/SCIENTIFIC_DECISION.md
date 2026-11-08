# Contribution 1: Mechanism Findings

**Conclusion: Yes, but narrowly.** In the frozen simulation, the largest component of baseline modeled service deficit is substation self-functionality loss, while the clearest local opportunity for changing loss through repair order is event-time source-path unlocking. This is a model-internal mechanism result for the tested network, source gate, damage samples, resources, and strategies; it is not empirical validation of customer outages or delivered power, nor a general repair recommendation.

## Frozen case and accounting

The primary comparison is `2pc50 / C57_D1 / M1_UTILITY_003 / G1_BASELINE_050`, 480 h, 92 stations, 2,315 mapped tracts, and 1,000 hash-matched physical realizations. All original population and dependency weights were retained. The seven archived schedules analyzed as event histories are Impact-first, Hospital-first, Degree-first, Betweenness-first, Centrality-first, Closeness-first, and Random. Unconstrained is the common no-scheduling baseline. Direct-community was not counted separately from its byte-identical Impact-first sequence. Vulnerability-first has frozen realization summaries, but not an event-time schedule archive suitable for the event reconstruction.

The production decomposition was checked as `L_total = L_self + L_threshold + L_source`. Maximum integrated additivity error was `3.55e-14 h`. The saved unconstrained means reproduce as 26.8872 h self loss, 0.8765 h threshold loss, 3.5740 h source-path loss, and 31.3378 h total. Self loss is 85.8% of this baseline total. That is an absolute-burden statement, not a measure of which mechanism is most responsive to sequencing.

## Repair-order responsiveness

The paired Degree-first minus Hospital-first difference across the same 1,000 realizations is:

| Component | Mean difference (h) | Paired bootstrap 95% CI (h) | 5th–95th realization range (h) |
|---|---:|---:|---:|
| Self loss | +2.9447 | [2.9165, 2.9727] | [2.2778, 3.7444] |
| Threshold loss | +0.1032 | [0.1019, 0.1045] | [0.0725, 0.1404] |
| Source-path loss | -1.6467 | [-1.7015, -1.5918] | [-3.1820, -0.3537] |
| Total | +1.4012 | [1.3442, 1.4574] | [-0.1755, 2.7844] |

Thus, a large source-path reduction offsets part, but not all, of higher self and threshold losses. The total is higher under Degree-first in 936/1,000 paired realizations. The realization range is not a confidence interval.

Impact-first versus Hospital-first is different: total is lower by 0.7128 h (paired bootstrap 95% CI [-0.7423, -0.6838]); self and threshold are lower by 0.7864 h and 0.0289 h, while source-path loss is 0.1026 h higher. The direction and component balance therefore depend on the strategy pair. Random exceeds Hospital-first by 5.0820 h on average. No single statement that “strategy improvements mainly reduce source loss” applies to every comparison.

Source loss is spatially broad in the frozen aggregation: 78 stations and 2,284 tracts have positive mean source loss. For Impact-first, the five stations with the largest station-attributed source loss account for 32.3%; the 100 highest source-loss tracts account for 16.9%. The effect is not solely a single-station or tiny-tract artifact, although concentration in the top stations remains material.

## Event-time evidence

Simultaneous completion timestamps were retained as batches; events were summarized by realization before uncertainty calculations. **For each of the seven event-reconstructed strategies**, the same 876 DS1-only completion batches (586 realizations with such batches) produced zero newly source-connected *other* stations. These stations were already at the G1 functionality threshold before repair, so increasing their own raw functionality did not newly enable their threshold status. In contrast, each strategy had 90,812 DS2–DS4 completion batches; external source unlocks occurred in 9.0%–13.3% of batches, depending on strategy. For Impact-first the realization-weighted fraction was 11.86% (95% realization-bootstrap interval 11.70%–12.01%). The definition requires other stations to remain threshold-eligible across the event while changing from not source-connected to source-connected. This is direct evidence of a topological pathway mechanism within the frozen gate model.

Selected pre/post examples in `FIG_EVENT_UNLOCK_ILLUSTRATIONS.pdf` were chosen as the single-station unlock event nearest the median positive indirect gain within Impact-first, Hospital-first, and Degree-first. They are explicitly illustrative, not representative effect estimates. The plotted network layout is schematic and is not a geographic map.

## Paired local priority perturbations

The predeclared 128-realization sample (IDs drawn without replacement from 0008–0999; seed 20261105) was tested under Impact-first and Hospital-first. Each of four target categories was moved 1, 3, or 5 places earlier in the actual full priority permutation, preserving the relative order of other tasks; the exact decoder and frozen DS/duration draws were reused. A separate zero-travel diagnostic was retained. There are 6,144 paired rows; uncertainty resamples realization IDs (10,000 bootstrap replicates, seed 20261107).

Moving a low-direct-mass, pre-event dynamic-unlock-potential target earlier reduced mean total deficit in both tested baseline sequences. At five positions earlier, the estimates were -0.1348 h for Impact-first (95% paired bootstrap interval [-0.1807, -0.0935]) and -0.0981 h for Hospital-first ([-0.1331, -0.0667]). The outcome-informed high-observed-unlock target also reduced burden, by -0.0967 h and -0.0800 h at five positions earlier, respectively. These changes are small relative to the 33.6–34.3 h strategy means, and target selection is conditional on the frozen model’s topology and (for the first category) observed event outcomes.

Moving the high-direct-self-loss target earlier yielded near-zero effects; moving it five positions earlier under Impact-first slightly increased deficit (+0.000516 h; interval [+0.000112, +0.001024]). Random-control moves were near zero or mildly harmful. The contrast supports greater local actionability of selected connectivity bottlenecks than of the largest direct-mass station, not a blanket claim that reordering reduces total loss.

In the zero-travel diagnostic, the targeted-unlock reductions remained similar in direction and scale. This argues against directed travel alone explaining those selected gains. It does **not** identify a pure travel-delay effect: moving a task changes the dispatch sequence, crew clocks, and precedence interactions, and no controlled duration/crew regression was established.

## Controls and scope

The no-gate calculation is a mathematical ablation. As expected, it removes threshold and source-path components; the Degree-first minus Hospital-first gap becomes the self-loss difference (+2.9447 h), compared with +1.4012 h under G1. This shows that the strategy contrast depends materially on the source-connectivity accounting. G2 (0.05 threshold) and G3 (0.75 threshold) aggregate strategy gaps remain close to G1, so the tested threshold choices do not reverse the broad paired result.

Frozen resource summaries show wide strategy separation at `C29_D1` (Impact-first 44.85 h, Hospital-first 46.95 h, Degree-first 54.63 h, Random 64.63 h) and near-convergence at `C114_D1` (31.684–31.710 h for these strategies). This is consistent with sequencing being more consequential under tighter crew availability, but these cross-scenario summaries are descriptive, not a randomized causal crew experiment. Frozen Long Beach, Northridge, and San Fernando comparisons are reported as context only; they do not isolate shaking intensity because scenario fragility inputs differ.

The results support H1 (DS2–DS4 event-time topological unlocking) and a qualified H3 (large self-loss baseline, little response to the selected direct-mass reorderings). H2 is only partly resolved: travel diagnostics do not erase the selected unlocking effects, but duration, dispatch time, and travel have not been disentangled as separate causal mechanisms. H4 is partly supported: component labels and strategy contrasts are conditional on the sequential source-gate decomposition, although the numerical identity itself is exact. Findings are model-derived and conditional on one frozen mapping, source representation, hazard benchmark, resource setup, and service proxy.

## What is not verified

- The local checkout has no matching realization-paired GA held-out outcome table or trajectory archive for the cited 2,000-realization validation. GA contrasts are therefore not recomputed or reported as verified results.
- Vulnerability-first has 1,000 frozen realization-level outcomes, but no event-time prepass archive; it is excluded from event-unlocking claims.
- The event archive stores indirect counts and mapped-mass changes, not persistent connected-station ID lists. The three example states are reconstructed from exact frozen schedules and event identities; an exhaustive station-by-event identity table is not exported.
- This study does not validate real outage duration, power flow, megawatts delivered, or customer service.

## Decision

Contribution 1 is scientifically defensible as a **bounded mechanism finding**: under the specified frozen model, the dominant component of unconstrained loss differs from a demonstrated, but small and target-dependent, repair-order opportunity mediated by source-connected network unlocking. It is not yet a validated general-purpose repair-priority rule, and it should not be presented as a real-world customer-outage mechanism without external service data.
