# Reviewer 1 Comment #1 — July 92 utility-constraint analysis

## Scope and decision boundary

This analysis keeps the July submission model unchanged: 92 stations, 318 edges, tract polygon centroid, nearest eligible access station, shortest-path distance on the frozen 92-node graph, inverse-distance weighting with power 2, minimum weight cutoff 0.03, and row renormalization. It does not use the later 310-node network, build a new network-informed mapping, modify topology, replace the production mapping, or execute damage, scheduling, source-gate, recovery, or GA code.

Two names are used throughout:

- `JULY_BASELINE_92`: the submitted July mapping formula with all 92 stations eligible.
- `JULY_UTILITY_CONSTRAINED_92`: the same formula, with tract utility compatibility applied before choosing the nearest access station and candidate targets. Strict SCE tracts use the 58 July stations whose retained `Owner` is SCE; strict LADWP tracts use the 30 stations whose owner is LADWP; 650 mixed/ambiguous tracts retain the original 92-station candidate logic. Shortest paths continue to use the unchanged 92-node graph.

The analysis reconstructed the submitted mapping file exactly to numerical precision: maximum absolute cell error `3.33e-16`, with zero cells differing by more than `1e-12`. This establishes that the comparison changes only station eligibility. The production file `Data/tract_to_substation_mapping_CEC_expanded.csv` was not changed.

## Step 1 — Utility-constrained July mapping

The frozen full-region domain contains 2,315 tracts: 817 strict SCE, 848 strict LADWP, and 650 mixed/ambiguous. The constraint changed at least one mapping weight in 945 tracts and changed the top-weight station in 225 tracts.

| Tract group | Tracts | Rows with a weight change | Top-1 changed | Mean total-variation shift | Population-weighted total-variation shift |
|---|---:|---:|---:|---:|---:|
| All | 2,315 | 945 | 225 (9.72%) | 0.1260 | 0.1208 |
| SCE | 817 | 338 | 70 (8.57%) | 0.1178 | 0.1166 |
| LADWP | 848 | 607 | 155 (18.28%) | 0.2305 | 0.2297 |
| Mixed/ambiguous | 650 | 0 | 0 | 0 | 0 |

These values describe changes in dependency weights, not changes in restoration outcomes. The larger LADWP shift reflects how frequently the unrestricted July formula had assigned weight to stations outside the retained LADWP owner set; it is not evidence about true customer-feeder assignment.

## Step 2 — SCE external candidate benchmark

The retained public SCE circuit/substation crosswalk is treated as `SCE_external_candidate_evidence`, not ground truth. Of 817 strict SCE tracts, 794 have at least one crosswalked public candidate in the retained evidence. Only 342 have at least one such candidate represented among the July 92 station IDs; all membership, rank, and distance metrics below therefore use the same 342-tract denominator. The result cannot evaluate official candidates absent from the July inventory.

Candidate sets are the positive-weight stations after the 0.03 cutoff. “Precision-like” is the share of mapped candidates contained in the represented official set; “recall-like” is the share of represented official candidates contained in the mapped set. Top-1/top-3 use the mapped weight rank. These are consistency diagnostics, not predictive-validation statistics.

| Metric | `JULY_BASELINE_92` | `JULY_UTILITY_CONSTRAINED_92` | Change |
|---|---:|---:|---:|
| Any-candidate match | 94.74% | 96.78% | +2.05 percentage points |
| Top-1 agreement | 88.01% | 89.47% | +1.46 percentage points |
| Top-3 agreement | 93.86% | 95.32% | +1.46 percentage points |
| Mean precision-like overlap | 0.5093 | 0.5158 | +0.0065 |
| Mean recall-like overlap | 0.8938 | 0.9245 | +0.0307 |
| Average candidate count | 2.640 | 2.731 | +0.091 |
| Average maximum weight | 0.8554 | 0.8614 | +0.0060 |
| Average HHI | 0.7677 | 0.7744 | +0.0066 |
| Average effective candidate count | 1.4108 | 1.3958 | -0.0150 |
| Mean top-1 distance to nearest represented official candidate | 0.4999 km | 0.4568 km | -0.0431 km |

The utility constraint improves every candidate-consistency measure in this bounded benchmark, but the improvements are modest. It also changes concentration only slightly. This supports utility compatibility as a transparent refinement; it does not validate service shares, customer assignments, circuit switching, or outage propagation.

## Step 3 — Outcome sensitivity boundary

The requested outcome comparison cannot be calculated faithfully from retained July strategy outputs without executing the final scientific runs again. The retained files have already applied `JULY_BASELINE_92`:

- Stage 3 retains mean tract trajectories after mapping.
- Stage 4/5 retain population/SVI aggregate curves, schedules, graph summaries, and limited tract KPI files.
- They do not retain the time-indexed, source-gated 92-station state trajectory for each fixed physical realization and strategy.

Changing a mapping after tract aggregation is not possible. Inverting the baseline matrix would introduce a new estimator and would not recover the original per-realization station states exactly, so this analysis did not do it. Consequently, the following requested quantities remain explicitly unavailable offline: population T80, population cumulative burden, hospital burden, Q1–Q4 absolute burdens, signed and absolute Q4−Q1 gaps, population-weighted Gini, tract burden shifts, and improved/near-zero/worsened/unresolved population.

The structural comparison nevertheless shows that local attribution is potentially sensitive: 40.82% of tract rows have a changed weight and 9.72% have a changed top-weight station, with larger shifts in strict LADWP tracts. That is sufficient to reject a claim that tract attribution is invariant, but it is not sufficient to claim that aggregate or tract burden results materially change. A valid future outcome sensitivity requires retaining the identical physical realizations, schedules, strategies, crews, and source-gated 92-station trajectories and applying both maps only at the tract-evaluation layer.

## Direct answers

1. **Does the utility constraint improve SCE candidate consistency?** Yes, modestly, on the 342 strict SCE tracts where public candidates are representable in the July 92 inventory. Any-match rises from 94.74% to 96.78%, top-1 from 88.01% to 89.47%, top-3 from 93.86% to 95.32%, and mean top-1 distance falls by 0.043 km.
2. **Does the change significantly alter aggregate results?** This cannot be determined from the retained July outputs. They lack the unmapped time-indexed 92-station state trajectories needed for an evaluation-only remap. No scientific chain was rerun, and no aggregate robustness claim is made.
3. **Is tract-level/community attribution sensitive?** The mapping attribution is structurally sensitive: 945 of 2,315 tract rows change and 225 change their top-weight station. Outcome-level community sensitivity remains undetermined until the same upstream trajectories are evaluated under both mappings.

## Files

- `JULY_UTILITY_CONSTRAINED_92.csv`: analysis-only constrained mapping.
- `SCE_CANDIDATE_BENCHMARK_TRACTS.csv` and `SCE_CANDIDATE_BENCHMARK_SUMMARY.csv`: tract and summary benchmark results.
- `MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv` and `MAPPING_STRUCTURE_SENSITIVITY_SUMMARY.csv`: full-region structural shifts.
- `OUTCOME_SENSITIVITY_AVAILABILITY.csv`: metric-by-metric retained-output boundary.
- `ANALYSIS_MANIFEST.json`: input/output hashes and frozen parameter record.

`PRODUCTION_DEFAULT_MAPPING_MODIFIED = NO`

`SCIENTIFIC_PIPELINE_EXECUTIONS = 0`
