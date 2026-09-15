# Dynamic Export Contract Test Report

Date: 2026-09-15

Decision: **PASS — DYNAMIC EXPORT CONTRACT VERIFIED**

## What exists now

`DYNAMIC_EFFECTIVE_STATE_PRODUCER = NOT CURRENTLY IMPLEMENTED`

The main model has dynamic source-gating calculations and returns time-indexed mean substation recovery dataframes, but it does not create the required one-scenario/one-realization/one-strategy R1-310 export object with an explicit identifiability mask. No dynamic producer, source gate, topology calculation, damage, repair, scheduling, or recovery trajectory was run in this round.

The new `r1_effective_state_exporter.py` is a standalone producer-side serialization boundary. It accepts already-computed state and mask matrices and cannot compute their scientific values.

## Static call-site findings

`apply_source_gate_to_substation_series(...)` is defined at `C257H_Project_Main.py:994`. Its main-module call at line 1116 is within `apply_source_gate_to_initial_functionality_samples(...)`, a Stage 1 Monte Carlo sample wrapper. A separate call at `06_R1_310_LocalClosure_20260914/local_closure.py:148` is a retained one-row dry-build audit. Neither is a dynamic recovery export point.

The actual Stage 3/4/5 recovery path uses the independent implementation in `simulate_recovery_mc_source_gated(...)`, defined at line 2164. Per-realization gated values are immediately added into `local_sum` at lines 2304–2306 and averaged at line 2333. The numeric `recovery_df` is returned at lines 2341–2347. Stage 3 receives it at line 2633 and propagates it at line 2673; Stage 4 receives the schedule result at line 3750 and propagates at line 3766; Stage 5 receives it at line 4237 and propagates at line 4262.

The future one-realization handoff must occur after a post-gate T × 310 effective-state matrix and its parallel mask are materialized, and before those values are accumulated into `local_sum`, averaged, or propagated to tracts/services. The current fused multiplication-and-accumulation statement does not expose such an object.

## Missingness finding

`CURRENT_GATE_OUTPUT_ALONE_IS_INSUFFICIENT_TO_RECONSTRUCT_STATE_IDENTIFIED_MASK`

At `C257H_Project_Main.py:1064`, `apply_source_gate_to_substation_series(...)` writes `0.0` to every non-kept cell and returns only a numeric dataframe. `simulate_recovery_mc_source_gated(...)` likewise returns no state-identifiability mask. The numeric output alone cannot distinguish an identified unavailable/source-disconnected zero from an unresolved state.

Future `state_identified` must be supplied by the producer from the governed registration/state-identifiability domain and carried alongside the state. The exporter never derives it from the numeric values.

## Export contract implemented

`export_r1_effective_state_trajectory(...)` accepts:

- T × 310 `effective_state`;
- T × 310 Boolean `state_identified`;
- T real `source_time` values;
- explicit `source_time_unit`;
- the exact frozen 310 R1 IDs;
- required trajectory-level provenance.

It returns canonical long form ordered by ordinal time and frozen ID. A masked NA or zero becomes serialized `0.0` plus `state_identified=False`. A masked nonzero fails. Identified values must be finite and in `[0,1]`.

The required semantic label is `post_source_component_gate_effective_network_state`. This label is accepted only from a producer already located at that handoff; the exporter does not establish the label by computation.

## Fixture tests

### Round 11 retained static fixture

The existing `SERVICE_NODE_BASELINE_QA.csv` was read without rerunning its generator.

| Check | Result |
|---|---:|
| Frozen station IDs | 310 / 310 |
| Identified states | 306 |
| Identified state = 1 | 304 |
| Identified state = 0 | 2 |
| Missing states | 4 |
| RINGMILL and UNKNOWN309598 | Retained as identified zero |
| RENO, UNKNOWN303265, HALLDALE, UNKNOWN305021 | Retained as missing |

Result: **310 / 310 cells preserved**.

### Round 13 five-step fixture

The existing Round 13 state and mask were pivoted to the dual-channel producer input. The exporter output was compared directly with the Round 15 adapter-restored canonical trajectory.

- 1,550 / 1,550 state cells were exact.
- 1,550 / 1,550 mask cells were exact.
- Time, R1 IDs, `source_time`, and `source_time_unit` were exact.
- The exported result passed the frozen production trajectory loader.

No service, tract, or recovery output was generated.

### Zero/missing collision fixture

The four-row `ZERO_MISSING_COLLISION_FIXTURE.csv` was verified as a bounded CSV artifact and embedded into one 310-ID synthetic contract matrix.

| Fixture role | Serialized value | Mask | Semantic result |
|---|---:|---:|---|
| Identified zero | 0 | True | 0 |
| Identified one | 1 | True | 1 |
| Identified fractional | 0.375 | True | 0.375 |
| Missing with zero placeholder | 0 | False | NA |

Result: **zero/missing collision preserved without ambiguity**.

## Malformed-input tests

Fifteen malformed cases all failed before export:

1. state matrix missing a station;
2. mask matrix missing a station;
3. unknown station;
4. duplicate station;
5. state/mask shape mismatch;
6. station labels that cannot be safely aligned;
7. identified state with NaN;
8. identified state below zero;
9. identified state above one;
10. masked state with nonzero value;
11. source-time length different from T;
12. nonmonotonic source time;
13. missing source-time unit;
14. duplicate trajectory time label;
15. station identity set not equal to the frozen 310.

Explicit station labels allow safe mask-column reordering; this was tested separately. No row-position alignment or automatic repair is used.

Result: **15 / 15 fail-fast tests passed**.

## Dependency and modification checks

The exporter imports only `dataclasses`, `hashlib`, `json`, `typing`, NumPy, and pandas. It does not import the main model, topology, source, damage, fragility, repair, routing, crew, scheduling, GA, Monte Carlo, service propagation, or the Round 15 adapter.

`C257H_Project_Main.py` remained unchanged at SHA-256:

`49b22de669239a17c000d9f92c5c340078315c0e07e085f803e964c40fbe1f38`

Two identical export calls produced exact-equality trajectories and provenance. Frozen Round 11, Round 13, Round 15, adapter, and production-module hashes remained unchanged.

## Test summary

| Test | Result |
|---|---:|
| Static current-code handoff/missingness inspection | PASS |
| Round 11 static cells | 310 / 310 |
| Round 13 state/mask cells | 1,550 / 1,550 exact |
| Collision roles | 4 / 4 |
| Malformed inputs | 15 / 15 failed fast |
| Explicit-ID safe reordering | PASS |
| Exporter dependency boundary | PASS |
| Main model unchanged | PASS |
| Run 1 / run 2 determinism | Exact |

## Provenance hashes

| Object | SHA-256 |
|---|---|
| Round 11 retained fixture | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Round 13 five-step fixture | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Round 15 native-form fixture | `b52605805f02cf12a959df50bee2fa7a34f5f1d6e8333015a79d74b4a2965249` |
| Round 15 adapter | `7815704771fbe61b18f057a7ee49d061edd13aee1f85daa37c83781fa21a1f9f` |
| Frozen production module | `d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514` |
| Main model | `49b22de669239a17c000d9f92c5c340078315c0e07e085f803e964c40fbe1f38` |
| Exporter module | `79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b` |
| Collision fixture | `c320573608501da0b738708a3754697bd171b170dd474f3fa51fbac88a93aa63` |

## Decision and next gate

**PASS — DYNAMIC EXPORT CONTRACT VERIFIED.**

The producer-to-exporter semantic boundary is frozen before a dynamic run occurs. The exporter is ready to be wired in the future, but no compatible R1-310 dynamic producer exists yet.

The next and only permitted step is a code-only wiring design or guarded implementation that makes a future per-realization R1 producer explicitly materialize both the post-gate effective-state matrix and its authoritative identified mask at the stated handoff. That step must remain disabled and must be tested only with retained or synthetic fixtures until separately authorized.

Source gate execution, topology, damage, fragility, repair, dispatch, crews, scheduling, GA, Monte Carlo, 32×4, 29-crews, and any recovery trajectory remain prohibited.
