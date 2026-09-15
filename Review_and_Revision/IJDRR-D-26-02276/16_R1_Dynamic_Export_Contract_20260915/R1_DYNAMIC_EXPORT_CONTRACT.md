# R1 Dynamic Effective-State Export Contract

Version: `R1_EFFECTIVE_STATE_EXPORT_V1`

Frozen: 2026-09-15

## Decision boundary

`DYNAMIC_EFFECTIVE_STATE_PRODUCER = NOT CURRENTLY IMPLEMENTED`

The existing main model contains source-gating calculations and produces time-indexed mean R1/substation recovery dataframes, but it does not produce the contract object defined here: one scenario, one realization, and one strategy trajectory with an explicit state-identifiability mask for the frozen R1-310 IDs.

This contract defines the producer-to-exporter boundary before such a producer is wired or executed. The standalone exporter validates and serializes state already computed by a future producer. It does not compute that state.

## Current-code call-site audit

The static audit used `C257H_Project_Main.py` SHA-256 `49b22de669239a17c000d9f92c5c340078315c0e07e085f803e964c40fbe1f38`.

### `apply_source_gate_to_substation_series(...)`

The function is defined at `C257H_Project_Main.py:994`. It thresholds each row, constructs the functional subgraph, retains components containing an active source, and writes zero to every non-kept numeric cell at line 1064.

Its only call in the main module is at line 1116 inside `apply_source_gate_to_initial_functionality_samples(...)`, defined at line 1090. That wrapper transposes a substation × Monte Carlo sample matrix into sample × substation form, applies the gate, and transposes it back. It is Stage 1 sample gating, not a dynamic recovery trajectory handoff.

One additional call exists in the retained Round 6 audit script `06_R1_310_LocalClosure_20260914/local_closure.py:148`. That script extracts the function and applies it once to an all-one no-damage dry-build frame. It is a static QA use, not a production trajectory call site.

No direct call to `apply_source_gate_to_substation_series(...)` produces the Stage 3/4/5 recovery time series.

### Dynamic recovery path

`simulate_recovery_mc_source_gated(...)`, defined at line 2164, contains a separate inline gate implementation. Within `_process_mc_range`, line 2304 immediately multiplies each realization's recovery segment by `keep_mask` and adds the result into `local_sum`. Line 2333 divides this accumulated state by the Monte Carlo count. Lines 2341–2347 construct and return `recovery_df`.

Current uses are:

- Stage 3 calls it at line 2633, receives `R_sub_mean_df`, and propagates that mean to tracts at line 2673.
- `simulate_rule_schedule(...)` calls it at line 3478. Stage 4 receives the resulting `R_sub_df` at line 3750 and propagates it at line 3766.
- Stage 5 receives the resulting `R_sub` at line 4237 and propagates it at line 4262.
- The sensitivity mechanism calls it at line 4852; sensitivity cases use `simulate_rule_schedule(...)` and propagate at line 4906.

These are dynamic, post-gate numeric dataframes, but they are means across Monte Carlo realizations and contain no producer-side `state_identified` mask. They therefore do not satisfy the one-realization export contract.

## Future handoff location

The natural conceptual boundary is:

`raw/damaged/repaired functionality for one realization and strategy`

→ `source/component gate for that realization and time`

→ `EffectiveNetworkState_i(t) plus StateIdentified_i(t)`

→ `R1_EFFECTIVE_STATE_EXPORT_V1`

→ Architecture B service propagation.

In the current code, the closest location is inside `simulate_recovery_mc_source_gated._process_mc_range`, after the gated realization state represented by `curves_by_ds[...] * keep_mask` at lines 2304–2306 and before it is added to `local_sum` and averaged at line 2333. The current statement fuses gating with accumulation; it does not materialize an exportable one-realization T × 310 object.

Future wiring specification:

- `INSERT_EXPORT_AFTER = materialization of one realization/strategy post-source-component-gate T × 310 effective-state matrix and its producer-authoritative T × 310 identified mask`
- `INSERT_EXPORT_BEFORE = addition to Monte Carlo local_sum, averaging across realizations, or any tract/service-layer propagation`

The already-returned `recovery_df` at lines 2341–2347 is a valid conceptual handoff only for an explicitly labeled mean trajectory. It must not be relabeled as one realization, and it still lacks the required mask.

No call site is modified in this round.

## Current missingness gap

`CURRENT_GATE_OUTPUT_ALONE_IS_INSUFFICIENT_TO_RECONSTRUCT_STATE_IDENTIFIED_MASK`

`apply_source_gate_to_substation_series(...)` writes `0.0` at line 1064 for every cell outside the kept source-connected functional components. The returned dataframe has no parallel mask. Its numeric zero can represent an identified unavailable/source-disconnected state, but the dataframe alone cannot represent or recover an unresolved registration/state-identifiability condition.

The same gap exists in `simulate_recovery_mc_source_gated(...)`: it returns a numeric `recovery_df` and no mask. Once missingness is flattened to numeric zero, an exporter cannot infer which zero was unidentified.

The future producer must therefore carry a registration/state-identifiability mask beside the state throughout the handoff. It may obtain that mask from the already-governed upstream registration/state domain or generate it explicitly as part of the future producer. The exporter must never derive the mask from state values.

## Export object scope

One export object represents exactly:

- one scenario;
- one realization;
- one strategy trajectory.

Realization, strategy, and scenario identity belong in `trajectory_id` and the producer's provenance. Multiple realization or strategy trajectories must be exported separately.

## Dual-channel producer input

The standalone API is:

`export_r1_effective_state_trajectory(effective_state, state_identified, source_time, source_time_unit, frozen_r1_ids, provenance)`

### `effective_state`

- Shape: T × 310.
- Type: pandas dataframe with explicit R1 station-ID columns and unique producer time labels.
- Identified cells must be numeric, finite, and within `[0,1]`.

### `state_identified`

- Shape: T × 310.
- Type: Boolean dataframe with explicit R1 station-ID columns and the same time identity/order as `effective_state`.
- This is the authoritative semantic channel.

If `state_identified=True`, the state must be valid and identified. If `state_identified=False`, semantic state is missing; the producer cell may contain NA or the inert numeric placeholder zero. A masked nonzero or nonfinite numeric value fails fast because it signals an inconsistent producer state/mask pair.

The exporter never applies either of these forbidden inferences:

- `state == 0` → missing;
- `NaN` → identified zero.

### Station identity

`frozen_r1_ids` must contain exactly the frozen 310 IDs. Both matrices must have exactly that set of explicit station labels. Column order differences are accepted only when the explicit IDs permit exact label alignment. Names, coordinates, row positions, and nearest matching are not allowed.

### Time

The output `time_index` is a zero-based strictly increasing ordinal generated from the already ordered producer rows. It has no physical unit.

`source_time` preserves the real upstream timeline and must have T unique, strictly increasing, nonmissing values. `source_time_unit` must be explicitly supplied by the producer, such as `hours_since_event`; the exporter never guesses it. No interpolation, sorting of unordered time, resampling, or time completion occurs.

## Canonical output

The exporter returns the same six fields consumed or retained by the frozen service contract:

- `time_index`;
- `R1_station_id`;
- `effective_state_value`;
- `state_identified`;
- `source_time`;
- `source_time_unit`.

Rows are ordered by ordinal `time_index` and then by the caller-supplied frozen R1 ID order. Masked rows serialize the inert value `0.0`; downstream semantic state is restored exclusively through `state_identified=False`.

## Provenance sidecar

Every export requires:

- `schema_version`;
- `trajectory_id`;
- `producer_file`;
- `producer_function`;
- `effective_state_semantics`;
- `frozen_R1_ID_hash`;
- `source_time_unit`;
- `source_scenario_identifier`;
- `producer_code_hash`.

`schema_version` must equal `R1_EFFECTIVE_STATE_EXPORT_V1`. `effective_state_semantics` must equal `post_source_component_gate_effective_network_state`. The R1 ID hash and source-time unit must match the call inputs. The exporter adds the canonical trajectory hash, time count, and station count.

The provenance records who computed the state. It does not imply that the exporter computed, validated physically, or interpreted the scientific state.

## Exporter dependency boundary

`r1_effective_state_exporter.py` imports only standard-library modules, NumPy, and pandas. It does not import the main model, source or topology code, damage/fragility/repair logic, travel, crews, scheduling, GA, Monte Carlo, the service layer, or the legacy adapter.

It validates, aligns by explicit ID, orders, serializes, and hashes. It cannot call a gate, inspect topology, load sources, or alter state.

## Fixture interpretation

- Round 11 is an existing one-time effective-state semantic fixture. It is not regenerated.
- Round 13 is the existing five-index state/mask fixture. It validates 1,550 producer cells without becoming a recovery run.
- `ZERO_MISSING_COLLISION_FIXTURE.csv` supplies four unit-test roles: identified zero, identified one, identified fractional state, and missing with numeric-zero placeholder.

The collision fixture is embedded into a 310-ID test matrix only to exercise the frozen 310-ID production contract. It does not represent a physical event.

## Fail-fast requirements

The exporter rejects state or mask station-set omissions, unknown or duplicate IDs, duplicate time labels, state/mask shape or time-identity mismatch, unsafe station alignment, invalid identified values, masked nonzero values, invalid source-time length/order, missing time unit, non-310 frozen identity, and incomplete or inconsistent provenance. It performs no automatic repair.
