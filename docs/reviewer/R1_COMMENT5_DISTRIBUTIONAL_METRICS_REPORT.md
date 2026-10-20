# Reviewer 1 Comment 5 — Distributional Community Metrics

## Scope

This phase adds evaluation of existing paired tract trajectories. It changes no damage, network, source gate, mapping, scheduler, strategy, vulnerability measure, manuscript or retained result.

## Definitions

For tract `r`, `ResolvedMass_r` is the service-candidate mass represented by the unchanged mapping and `KnownAvailableMass_r(t)` is the represented available mass in the trajectory.

`RestorationBurdenMass_r = integral [ResolvedMass_r - KnownAvailableMass_r(t)] dt`

`NormalizedBurden_r = RestorationBurdenMass_r / ResolvedMass_r`

The first has mass-hours; the second has hours. If `ResolvedMass=0`, both burden and direction remain NA and status is `unresolved`; missing is neither failed nor recovered. A resolved tract containing missing time cells fails validation rather than being filled.

## Population denominators

`summarize_distribution()` reports both:

1. population-weighted tract normalized burden: weights are full tract population among resolved tracts;
2. population×resolved-mass weighted burden: numerator is population×burden-mass and denominator is population×resolved mass.

These answer different questions and are not interchanged.

## Distributional outputs

- fixed vulnerability quartiles Q1–Q4 assigned once from the paper's existing tract vulnerability measure, with tract ID as stable tie-break;
- absolute population-weighted normalized burden for every quartile;
- signed `Q4-Q1` and its absolute magnitude;
- population-weighted Gini of tract normalized burden, reported as inequality rather than an equity score;
- candidate-minus-reference tract effects classified as improved, near-zero, worsened or unresolved with the retained ±1 h practical threshold; the threshold is not statistical significance;
- paired mean/median difference, direction frequency and fixed-seed bootstrap interval, resampling realizations rather than tracts.

Existing T50/T80, AUC, population-weighted and SVI-weighted recovery remain valid separate summaries. None alone is relabeled as equity.

## Implementation

- `r1_distributional_metrics.py`: burden integration, fixed quartiles, group summaries, weighted Gini, tract effects and paired-realization bootstrap.
- `test_r1_distributional_metrics.py`: small deterministic calculations.

The test example integrates `[0, 0.5, 1]` over 0–2 h to 1 burden-hour, preserves an all-missing tract as unresolved/NA, checks the equal-weight two-point Gini of 0.5, verifies fixed quartile absolute burdens and effect labels, and confirms deterministic realization-level bootstrap output.
