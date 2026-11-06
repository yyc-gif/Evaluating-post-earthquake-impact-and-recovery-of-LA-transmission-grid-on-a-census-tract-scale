# GA versus Impact-first: Mechanism Closure

## Finding

On the exact saved 2,000-case independent validation cohort, the fixed `ga-final-method-candidate` order (sequence SHA-256 `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`) reduced the 0-480 h total population-weighted normalized modeled service deficit by **0.501902 h** relative to Impact-first (GA minus Impact mean `-0.501902 h`; paired realization-bootstrap 95% interval `[-0.524975, -0.479472] h`). The component changes were self-functionality `+0.203762 h`, threshold `+0.007820 h`, and source-path `-0.713484 h`. The total was lower under GA in 1,810/2,000 cases; source-path deficit was lower in 1,948/2,000.

## What accounts for the source-path difference?

Exact event accounting separates the source-path change into:

| Event component | GA minus Impact-first |
|---|---:|
| Repaired stations' own source-loss states | `-12.943337 h` |
| Other stations' source-connection states | `+12.229853 h` |
| Net source-path change | `-0.713484 h` |

Thus, changes at repaired stations create the gross favorable source-path term; changed source connections at other stations offset **94.5%** of it. GA does **not** gain through a larger number of downstream unlocks overall: compared with Impact-first it has `-0.7580` completion events with any other-station unlock and `-1.5825` other-station transitions per realization, with `-254,040` M1-mapped person-equivalent dependency mass per realization. These masses are fractional mapping weights, not counts of distinct people.

Some GA completion groups nevertheless produce favorable downstream changes. Illustrative largest favorable event groups are station 301614 (mean completion 23.49 h under GA versus 41.94 h under Impact-first; external source-loss contribution `-1.464885 h`), Station Q/HARBOR 308581 (mean completion approximately 21.67 h under both; `216` versus `150` downstream unlock transitions; external contribution `-1.435771 h`), Haynes 307373 (40.10 versus 45.96 h; `-1.263166 h`), and Nichols Canyon 308206 (completion approximately 28.85 h under both; `-1.046869 h`). Their leading connected-station contributions are enumerated in `GA_IMPACT_STATION_EVENT_ATTRIBUTION.json`. These favorable events are outweighed in the aggregate external term by adverse completion groups, led by 301105 (`+3.776762 h`), 310179 (`+1.487345 h`), and 301100 (`+1.453145 h`).

The event attribution accounts for **100%** of the paired source-path difference (maximum per-case direct-plus-external identity error `1.95e-13 h`; event-to-downstream identity error `2.62e-14 h`). This is exact decomposition of the saved step trajectories, **not causal credit assigned to individual repair tasks**. Repair order changes crews, travel, completion times, and the network state at simultaneous events jointly. Source connection is the model's binary Core-source proxy, not power-flow or delivered-electricity evidence.

## Provenance and limits

The archived validation ZIP SHA-256 is `74d83734549c83b7bcb57270a07db3ab4c696d4384c5a851461184cfcb28947d`. All 2,000 draw records match the registered `SeedSequence([202610091,3,2,r])`, are unique, and have no overlap with the 64 planning plus 1,000 original evaluation physical hashes. Four predeclared records (`r=0,1,1000,1999`) were regenerated bitwise from the frozen production samplers only as identity checks. The paired run checks 8,000 case payload hashes, the frozen 92-station order, 2,315-tract M1 mapping, saved gate state, task durations, and source-path integrals.

This sequence is the hashed October 9 `ga-final-method-candidate`, selected from planning loss without evaluation-based selection and executed in the saved 2,000-case archive. The approximate `-0.533 h` / `(-0.821,+0.277,+0.011) h` tuple quoted in PR #5 is **not** reproduced. The exact GA sequence and sample identities behind that historical Figure S4 comparison were not located in the checked source/artifact provenance. The active figure caption identifies S4 as static network criticality and dynamic functional-network recovery; the GA diagnostic is a separate exploratory artifact. Accordingly, these results answer the paired mechanism question for the identified fixed GA candidate and cohort, not a claim to reproduce the historical Figure S4 estimate.

The 1-hour mean source-loss difference reaches `-0.03233` near hour 17 and returns close to zero by 72 h; the reported integral uses the exact archived event times over 0-480 h. The validation is conditional on frozen simulated damage, duration, network, mapping, source assumptions, and dispatch model. It is not empirical customer-outage validation, and no individual source station should be described as delivering power.

## Reproduction

1. Verify the archived sample identities with `src/la_grid/diagnostics/verify_ga_validation_samples_20261106.py`.
2. Reproduce the paired event accounting with `src/la_grid/diagnostics/ga_impact_event_mechanism_20261106.py` and the existing materialized LFS archive, validation receipt, sequence, M1 mapping, graph, and source table.
3. Run `python -m pytest -p no:cacheprovider tests/test_ga_impact_event_mechanism_20261106.py -q` (2 tests passed in the final run).

Detailed commands and source hashes are in `GA_IMPACT_EVENT_MECHANISM_REPORT.md` and `GA_IMPACT_EVENT_MECHANISM.json`. Per-realization outcomes are in `GA_IMPACT_PAIRED_REALIZATION_EFFECTS.json`; event-trigger and downstream-station attribution is in `GA_IMPACT_STATION_EVENT_ATTRIBUTION.json`.
