# R1 producer instrumentation observer contract

## Decision and boundary

This round defines an observer that can copy an already-computed scientific
segment into the Round 18 materializer without participating in the scientific
calculation or replacing the caller-owned segment.

The observer is not connected to `C257H_Project_Main.py`. The main model is
unchanged from Round 17 commit
`1bad6deb90315ea9e034bdda468e2587a0052587`.

`DYNAMIC_EFFECTIVE_STATE_PRODUCER = NOT CURRENTLY IMPLEMENTED`

## Observer API

`r1_effective_state_producer_observer.py` provides:

```python
create_r1_effective_state_producer_observer(
    enabled=False,
    materializer=None,
    provenance=None,
    authoritative_station_mask=None,
)

observe_precomputed_r1_segment(
    observer=...,
    time_start=...,
    time_stop=...,
    effective_state_segment=...,
    state_identified_segment=...,
)
```

Disabled creation ignores all optional inputs and returns an inactive observer
with no materializer, provenance, or mask. Disabled observation returns before
inspecting any payload.

Enabled observation:

1. requires one realization-scoped materializer and provenance;
2. requires full-width DataFrames with explicit station identity;
3. validates the explicit segment mask against the frozen station mask;
4. deep-copies both caller objects;
5. passes the copies to the Round 18 materializer;
6. records structural counters;
7. returns `None`.

It cannot supply a replacement array to `local_sum`. The caller retains and
accumulates its original `legacy_segment`.

## No scientific computation

The observer does not multiply, clip, gate, zero, fill, interpolate, sort,
threshold, average, or alter dtype. It never creates a scientific segment.
It does not infer the mask from zeros, NaNs, finite values, or connectivity.

If the future scientific producer concludes that an interval is zero, that
producer must explicitly supply the zero state segment and its authoritative
mask. No observer call means no materialized coverage; Round 18 finalize will
fail rather than convert silence to zero.

## Identifiability scope

The current Architecture B evidence supports:

`IDENTIFIABILITY_SCOPE = STATION_STATIC_WITHIN_TRAJECTORY`

Here, identifiability asks whether an R1 record belongs to the representable
network state domain. Round 6 froze four unresolved registrations. Round 11
kept those four records unidentifiable and kept two registered but
source-unreachable records as identified zeros. Round 13 preserved the same
306/4 mask at every one of its five time indices.

The four station-static missing IDs are:

- RENO `301479`;
- UNKNOWN303265 `303265`;
- HALLDALE `304137`;
- UNKNOWN305021 `305021`.

Damage, unrepaired status, source disconnection, and effective state zero do
not remove a registered station from this state domain. RINGMILL `306980` and
UNKNOWN309598 `309598` demonstrate the distinction: both are identified zeros.

The authoritative source is therefore the frozen registration/state-domain
ledger, represented by the retained Round 11 mask. A future scientific
producer may explicitly broadcast that 310-element vector to each segment.
The observer only verifies the supplied broadcast; it does not create it.

No retained evidence supports time-varying identifiability under the current
architecture. A future model that dynamically changes registration or the
state domain would require a new contract review rather than reuse this mask.

`keep_mask` is explicitly prohibited as an identifiability mask. It represents
functional source-connected membership. A registered source-disconnected node
has effective state zero and `state_identified=True`.

## Five current control-flow paths

Static inspection of `simulate_recovery_mc_source_gated._process_mc_range`
identifies five paths that a future producer must cover explicitly.

### P1 — gate disabled

Current behavior adds `curves_by_ds[ds_vec, :, sub_positions].T` for the full
timeline. The future producer must supply one explicit `[0,T)` segment and its
mask. The observer does not construct it.

### P2 — leading interval before first event

The current zero accumulator remains unchanged on `[0, first_event)`. A future
producer must explicitly create and observe an all-zero segment for this
interval. Producer silence is not valid coverage.

### P3 — event interval with at least one kept node

The current scientific expression is
`curves_by_ds[...] * keep_mask`. A future producer must compute this exactly
once, bind it as `legacy_segment`, and pass that same object to the observer
before accumulating the original object.

### P4 — event interval with no kept node

Current code performs no addition. A future producer must explicitly represent
that scientific control-flow decision as a full-width zero segment and mask.
The observer cannot create the zero.

### P5 — no event indices

The realization currently contributes only the initialized zeros. A future
producer must explicitly supply a complete `[0,T)` zero segment and mask.

## Future instrumentation shape

For a nonzero/event interval:

```python
# Scientific producer computes this exactly once.
legacy_segment = (
    curves_by_ds[ds_vec, time_start:time_stop, sub_positions].T * keep_mask
)

# Optional observational side path; returns None.
if producer_instrumentation_enabled:
    observer.observe(
        time_start=time_start,
        time_stop=time_stop,
        effective_state_segment=legacy_segment,
        state_identified_segment=identified_segment,
    )

# Scientific accumulation uses the original caller-owned object.
local_sum[time_start:time_stop, :] += legacy_segment
```

For a producer-decided zero interval:

```python
legacy_zero_segment = producer_explicit_zero_segment(...)
identified_segment = producer_explicit_mask_broadcast(...)
observer.observe(..., effective_state_segment=legacy_zero_segment,
                 state_identified_segment=identified_segment)
local_sum[time_start:time_stop, :] += legacy_zero_segment
```

The placeholder names describe future producer responsibilities. They are not
implemented in the observer or main model.

## Parallel contract

Each future realization must own an independent materializer, observer,
`realization_id`, and provenance record. Realizations and workers may not share
a materializer or trajectory object. The preferred later design is:

```text
worker materializes one object -> returns object/result to parent collector
```

Workers should not write a shared final artifact. No parallel execution was
performed in this round.

## Dependency boundary

The observer imports only `dataclasses`, `typing`, NumPy, pandas, and the Round
18 materializer. It does not import the main model, NetworkX, topology, source
loaders, damage, fragility, repair, crews, scheduling, GA, MC logic, service
propagation, exporter, or hook.

## Permitted next step

The next permitted step is default-disabled main-model instrumentation wiring:
name the already-computed `legacy_segment`, pass it observationally to this
observer, then accumulate the same original object. That work must still be
validated with retained/synthetic inputs and must not run real recovery or MC
without separate authorization.
