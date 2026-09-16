# Disabled main-model producer instrumentation contract

## Decision and scope

This round installs the Round 19 observer at the actual segment-accumulation location in `simulate_recovery_mc_source_gated(...)`. The wiring is disabled unless an explicit controller with `enabled=True` is supplied. It materializes only an in-memory, one-realization copy of the scientific contribution already produced by the caller.

It does not authorize or execute a source gate, recovery calculation, damage or repair sampling, dispatch, scheduling, GA, Monte Carlo experiment, exporter, service-layer propagation, or file write. No scientific run was used to validate this wiring.

## Main-model seam

`C257H_Project_Main.py` adds one final optional argument:

```python
r1_producer_instrumentation: Any = None
```

All retained call sites omit the argument. The default path therefore creates no controller session, materializer, observer, mask broadcast, explicit-zero segment, realization object, or output file.

The enabled path requires the external controller to validate:

- exactly 310 ordered R1 IDs matching `sub_index`;
- the unchanged `t_grid` as explicit `source_time`;
- an explicit `source_time_unit` provided by the caller;
- a structured `scenario_id` and `strategy_id`;
- a frozen, ID-indexed Boolean station mask with 306 identified and 4 unidentified stations;
- `trajectory_scope = realization`;
- configured `MC_SOURCE_GATE_N_JOBS == 1`.

The mask is authoritative registration/state-domain metadata. It is not computed from state values, `keep_mask`, graph membership, or runtime registration logic. Broadcasting this station-static 310-vector across a segment changes representation only.

## Per-realization ownership

Each `mc_idx` receives a separate session and deterministic realization identity `mc_XXXXXX`. The session owns one Round 18 materializer and one Round 19 observer. Finalized objects are collected only in memory under:

```text
(scenario_id, strategy_id, realization_id)
```

Duplicate started or finalized keys fail. The scientific function return type and `return_gate_diagnostics` output remain unchanged.

## Five control-flow paths

The wiring represents every current legacy contribution path without changing its accumulator behavior.

| Path | Existing scientific behavior | Enabled observational behavior | Scientific accumulator |
|---|---|---|---|
| P1: gate disabled | Add full `curves_by_ds[...]` trajectory | Observe the same caller-owned full segment, then finalize | Adds that same segment once |
| P2: before first event | No addition; accumulator remains zero | Explicitly materialize `[0, first_event)` as zero with authoritative mask | No zero addition is introduced |
| P3: event interval with any kept node | Add `curves_by_ds[...] * keep_mask` | Compute `legacy_segment` once, observe it, add that same array | Scientific expression is evaluated once |
| P4: event interval with no kept node | No addition | Explicitly materialize that interval as zero | No zero addition is introduced |
| P5: no event indices | No addition for `[0,T)` | Explicitly materialize a full zero trajectory, then finalize | No addition is introduced |

The explicit zeros in P2/P4/P5 are produced only by the main scientific control flow's already-established zero-contribution decision. The observer never invents zeros, fills gaps, or decides scientific state. Round 18 coverage validation makes any omitted interval fail at finalization.

## Scientific-state separation

`keep_mask` remains the source-connected functional-membership mask used by the legacy scientific expression. `state_identified` remains the station-static representation mask. A station may therefore have:

```text
keep_mask = False
effective_state = 0
state_identified = True
```

The controller passes a deep-labeled copy to the observer. `local_sum` always consumes the original caller-owned segment. The observer returns `None`; neither observer nor materializer can supply a replacement value to the accumulator.

## Export boundary

The Round 17 `effective_state_export_hook` remains fail-closed and disconnected. The main model imports neither the exporter, the export hook module, nor the service-layer interface. This round stops at:

```text
scientific segment -> observer -> materializer -> in-memory realization
```

No files are written and no materialized object is returned in the scientific result tuple.

## Parallel boundary

Enabled instrumentation is serial-only. The controller rejects any configured job count other than one before a realization session begins. Disabled instrumentation leaves the retained parallel normalization, ranges, workers, accumulation, and averaging behavior unchanged.

## Allowed next gate

Passing this contract establishes code readiness only. The next possible action is a separately authorized **ONE-REALIZATION SCIENTIFIC INTEGRATION TEST** using one scenario, one strategy, one realization, serial execution, and enabled instrumentation. That future run must compare the in-memory materialized trajectory with the exact scientific contribution entering `local_sum` in the same run.

This round does not authorize that run. It also does not authorize 32x4, 29 crews, 114 crews, GA, broader Monte Carlo, repair-duration sensitivity, exporter wiring, service-layer propagation, or manuscript result updates.
