# Disabled R1 effective-state export wiring contract

## Decision

The code now contains a default-disabled, fail-closed seam for a future
one-realization R1 effective-state producer. It does not implement that
producer and does not export from the current recovery calculation.

`DYNAMIC_EFFECTIVE_STATE_PRODUCER = NOT CURRENTLY IMPLEMENTED`

The seam is an unpowered interface. No recovery, gate, damage, repair,
scheduling, or Monte Carlo computation was run to establish it.

## Frozen current dynamic location

`C257H_Project_Main.py` defines `simulate_recovery_mc_source_gated(...)` at
line 2164. Within `_process_mc_range(...)`, the current source-gated state is
still formed only as the expression at lines 2318–2319:

```python
curves_by_ds[ds_vec, time_start:time_stop, sub_positions].T * keep_mask
```

That expression is immediately added to `local_sum`. No complete
one-realization T x 310 trajectory is materialized. The returned
`recovery_df` remains an MC mean and is not an eligible realization export.

The future insertion marker is immediately before the unchanged accumulation
statement. Its contract is:

```text
one complete realization post-source/component-gate state
+ producer-authoritative identified mask
-> Round 17 hook
-> Round 16 exporter
-> before local_sum, MC averaging, or tract/service propagation
```

The marker is not a callback invocation. Current code cannot energize it.

## Main-model seam

The only executable main-model changes are:

1. `simulate_recovery_mc_source_gated(...)` has a final optional parameter,
   `effective_state_export_hook: Any = None`, at line 2176.
2. Lines 2185–2191 allow `None` or an object whose `enabled` attribute is
   exactly `False`. An enabled or structurally invalid hook raises before any
   scientific work, because the producer does not exist.
3. Lines 2312–2317 contain the future insertion marker.

All existing call sites omit the new argument. The gate equation, `keep_mask`,
recovery curves, `local_sum` update, mean calculation, parallel ranges,
sources, threshold, call arguments, and return type are unchanged.

## Hook contract

`r1_effective_state_export_hook.py` exposes:

```python
R1EffectiveStateExportHook(enabled=False, callback=None)

maybe_export_r1_effective_state(
    *,
    hook,
    effective_state,
    state_identified,
    source_time,
    source_time_unit,
    frozen_r1_ids,
    provenance,
)
```

Disabled execution returns before inspecting any producer input. It allocates
no trajectory, constructs no mask, invokes no callback, and performs no I/O.

Enabled execution requires the producer to supply all six payload inputs. The
hook does not construct, gate, average, fill, interpolate, or otherwise alter
them. The callback is intended to be the frozen Round 16 exporter.

## Producer responsibility

The future producer, rather than this seam, must provide:

- a complete T x 310 post-source/component-gate `effective_state`;
- a complete, same-identity T x 310 `state_identified` mask;
- explicit source times and units;
- the frozen ordered R1 IDs;
- complete trajectory and producer provenance.

The mask remains authoritative. Numeric zero cannot be used to infer missing,
and the hook cannot create the mask from registration, topology, connectivity,
or state values.

## Realization-only guard

Before calling its callback, the hook requires nonempty:

- `scenario_id`;
- `strategy_id`;
- `realization_id`;
- `trajectory_scope = realization`.

`trajectory_scope = mc_mean`, `aggregate`, a missing realization identity, or
an empty identity is rejected. This keeps `mean_recovery`, `recovery_df`,
`R_sub_mean_df`, Stage 3/4/5 averaged frames, and other MC aggregates outside
the realization exporter.

The structured identity requirement extends the wiring-layer validation while
leaving the Round 16 canonical trajectory schema unchanged.

## Future parallel-write rule

The current seam performs no file I/O. Future parallel export must obey all of
the following before it is enabled:

- the tuple `(scenario_id, strategy_id, realization_id)` is globally unique;
- the tuple determines a deterministic filename or parent-collection key;
- overwrite is prohibited;
- writes are atomic, or workers return objects to a single parent-controlled
  collector;
- duplicate realization IDs fail before serialization;
- output ordering is established by identity, not worker completion order.

No worker export or parallel recovery execution was used in this round.

## Dependency boundary

The hook imports only `dataclasses` and `typing` from the standard library. It
does not import the main model, topology, NetworkX, source loaders, damage,
fragility, repair, travel, crews, scheduling, GA, MC logic, or service
propagation. It has no file-writing API.

## Permitted next step

The next permissible implementation is a producer-side materialization unit
that creates the complete post-gate realization state and authoritative mask
at the marked boundary. It must first be tested with retained or synthetic
fixtures while export remains disabled. Real recovery execution remains
prohibited until that unit receives separate review and authorization.
