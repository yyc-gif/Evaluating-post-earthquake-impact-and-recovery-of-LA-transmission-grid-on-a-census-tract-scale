# R1 producer-side materialization contract

## Decision and scope

This round defines a standalone unit that assembles already-computed,
post-source/component-gate realization segments into one complete T x 310
state/mask object.

The materializer performs no scientific calculation. It does not calculate
functionality, connectivity, threshold crossings, damage, repair,
identifiability, or any gate. It does not call the exporter or hook and performs
no file I/O.

`DYNAMIC_EFFECTIVE_STATE_PRODUCER = NOT CURRENTLY IMPLEMENTED`

`C257H_Project_Main.py` is unchanged from Round 17 commit
`1bad6deb90315ea9e034bdda468e2587a0052587`.

## Default inactive factory

The public factory is:

```python
create_r1_realization_materializer(
    enabled=False,
    frozen_r1_ids=None,
    source_time=None,
    source_time_unit=None,
    provenance=None,
)
```

With the default `enabled=False`, it returns `None` before validating or
allocating state, mask, or coverage arrays. Fixture tests explicitly set
`enabled=True`; production remains inactive and unconnected.

## Active materializer input

An explicitly enabled instance requires:

- exactly 310 unique, explicit frozen R1 IDs;
- a nonempty, unique, strictly increasing `source_time` sequence;
- an explicit `source_time_unit`;
- provenance containing nonempty `scenario_id`, `strategy_id`,
  `realization_id`, `trajectory_scope=realization`, `source_time_unit`, and the
  matching ordered frozen-ID hash.

Aggregate scopes such as `mc_mean` or `aggregate` are rejected. A retained
mean recovery frame cannot be relabeled as a realization object.

## Segment API

```python
append_segment(
    time_start,
    time_stop,
    effective_state_segment,
    state_identified_segment,
)
```

Both segments must be pandas DataFrames with:

- shape `(time_stop - time_start) x 310`;
- explicit station-ID columns exactly matching the frozen set;
- row identities exactly matching `source_time[time_start:time_stop]`;
- identical state/mask row identity and length.

Column order may differ and is safely restored by explicit ID. Positional
arrays, subsets, unknown IDs, duplicate IDs, name matching, nearest matching,
and automatic station creation are rejected.

## Strict coverage and order

Segments must form one contiguous sequence:

- the first starts at 0;
- every next start equals the prior stop;
- every interval satisfies `0 <= start < stop <= T`;
- final coverage ends at T.

The materializer never sorts segments. Gaps, overlaps, duplicates, reverse
order, zero-length intervals, and out-of-range intervals fail immediately.

Three independent internal arrays are maintained:

1. `effective_state`, initialized to NaN;
2. `state_identified`, initialized to False;
3. `coverage_written`, initialized to False.

Only a validated `append_segment` sets `coverage_written=True`. Therefore an
unwritten cell cannot be interpreted as an identified zero or semantic
missing value. `finalize()` fails if any cell remains unwritten.

## State and mask semantics

The caller-provided mask is authoritative.

For `state_identified=True`, state must be numeric, finite, and in `[0, 1]`.
For `state_identified=False`, state may be NaN or exactly zero; a nonzero or
nonfinite numeric value is rejected. The materializer never uses zero or NaN
to infer the mask.

The following remain distinct throughout materialization:

- identified zero;
- identified one;
- identified fractional value;
- unidentified state with NaN or inert zero storage.

## Finalization

`finalize()` is permitted exactly once after full explicit coverage. It returns
a `R1MaterializedRealization` containing deep state/mask DataFrames, immutable
source-time and R1-ID tuples, the time unit, and a copied provenance mapping.

After finalization, further append and repeated finalize calls fail. This
prevents silent mutation or history-dependent output.

## Dependency boundary

The module imports only:

- `dataclasses`, `hashlib`, and `typing`;
- NumPy and pandas.

It does not import `C257H_Project_Main`, NetworkX, topology, source loaders,
damage, fragility, repair, routing, crews, scheduling, GA, MC logic, service
propagation, the Round 16 exporter, or the Round 17 hook.

## Permitted future step

The next permitted work is design and fixture-only validation of future
producer instrumentation: how the scientific producer would supply explicit
segments numerically identical to its existing `local_sum` contributions while
carrying an authoritative mask. That instrumentation must remain disabled and
must not run real recovery, gate, or MC calculations without separate
authorization.
