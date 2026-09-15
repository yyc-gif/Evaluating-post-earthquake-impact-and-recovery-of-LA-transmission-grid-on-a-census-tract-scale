# Architecture B Production Service-Layer Interface Contract

Version: 1.0

Frozen: 2026-09-14

Applies to: strict-SCE primary domain only

## Purpose

`service_layer_interface.py` is the stable software boundary between any upstream R1 process and the Architecture B community service-access proxy.

The module consumes an externally supplied time series of `EffectiveNetworkState_i(t)`. It does not determine why a state has a particular value. The upstream state may originate from a manual fixture or a separately governed upstream process; source availability, connectivity, damage, repair, and scheduling are outside this module.

The production module must remain free of project-specific source, topology, damage, fragility, repair, routing, crew, scheduling, and optimization imports.

## Public interfaces

### `load_validate_r1_effective_state_trajectory(...)`

Input is a long-form table with:

- `time_index`
- `R1_station_id`
- `effective_state_value`
- `state_identified`

The loader requires every time index to contain exactly the frozen R1 ID set, with no duplicate or missing IDs. Time-index blocks must be unique and strictly increasing. Serialized state values must be finite and in `[0,1]`. The identified/missing mask must remain constant and, when supplied, exactly match the frozen T0 mask.

The finite serialized value for a row with `state_identified=False` is not a state estimate. The standardized semantic state is `NA`.

The output contains time × R1 tables for serialized values, the identified mask, and semantic effective states.

### `propagate_network_state_to_service_layer(...)`

The frozen attachment contract is:

- Class A: `ServiceState_j(t) = EffectiveNetworkState_i(t)` for the same physical R1 asset.
- Class B: `ServiceState_j(t) = EffectiveNetworkState_upstream(i,t)` for the one named-system upstream proxy.
- Class C: `ServiceState_j(t) = NA`.

Every Class A/B service node must have exactly one known R1 upstream ID. Zero or multiple A/B upstream IDs are rejected. Every Class C node must have no upstream ID; an assigned Class C upstream is rejected.

Missing upstream state propagates as missing service state. The function does not fill, multiply, gate, route, or retain event history.

### `aggregate_service_states_to_tract_intervals(...)`

The complete official-candidate W1 matrix is validated before use. Every tract row must be finite, nonnegative, and sum to 1 within a frozen CSV serialization tolerance of `5e-12`. The retained 12-significant-digit W1 has two six-candidate rows with about `2.0e-12` deviation; the validator accepts that representation without changing any value. Golden output comparisons retain the stricter `1e-12` tolerance. Missing service states never cause W1 renormalization.

For each tract and time:

- `ResolvedMass` is W1 mass whose service state is identified.
- `UnresolvedMass` is W1 mass whose service state is missing.
- `KnownAvailableMass` is W1-weighted identified service state.
- `Lower = KnownAvailableMass`.
- `Upper = KnownAvailableMass + UnresolvedMass`.
- `ConditionalResolvedAvailability = KnownAvailableMass / ResolvedMass`, when defined, is diagnostic only.

This interval is a modeled upstream/service-access proxy. It is not actual delivered electricity or customer outage.

### `evaluate_service_layer_trajectory(...)`

This is the single production entry point. It accepts data frames and explicit expected ID/missingness contracts and returns:

- standardized semantic network trajectory;
- network identified mask;
- service-state trajectory;
- tract interval trajectory;
- population-weighted aggregate interval trajectory.

It performs no file discovery and reads no scientific input itself. The calling wrapper owns file loading and frozen-hash verification.

## Frozen identity contract for the golden regression

The Round 13 fixture and golden outputs are reused in place; they are not copied or regenerated.

| Identity | Golden value |
|---|---|
| Source scenario | 21 IDs; sorted-ID hash `c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3` |
| R1 IDs | 310; sorted-ID hash `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5` |
| Service IDs | 196; sorted-ID hash `1c2533ea1ba4efd7894910e49c322654c90ec0eca6047908249a4c6e1b5d2f46` |
| Attachment ledger | `b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e` |
| W1 | `a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221` |
| Tract/population input | `4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b` |
| Frozen T0 state file | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Frozen T0 tract intervals | `e285c9bbc8a1ecb9dd7057060ef4f5453edea42f70ffb4b7d42d9c0975e3ed9a` |
| T0–T4 trajectory | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Golden service-time output | `8d7b55f660717753c1a715a4792dde2f429faf4d42b567a03eb68ec2aa6a95cb` |
| Golden tract-time output | `5cf3fb759bea519f6f3fbaee4cdffb422261b1a9a4157c296c8be7bd58c3009d` |

The tract/population canonical identity is additionally hashed from sorted UTF-8 rows `tract_id,population\n`; its value is recorded by the regression report.

## Regression acceptance

The production implementation must:

1. Read the original Round 13 external trajectory.
2. Match all 980 golden service states within `1e-12`, with an exact Class C missing mask.
3. Match lower, upper, and width for all 4,085 golden tract-time rows within `1e-12`.
4. Match all five population-weighted aggregate intervals within `1e-12`.
5. Preserve T0/T4 exact equality.
6. Produce bitwise/equality-identical data-frame outputs on two consecutive calls with the same inputs.
7. Leave attachment, W1, fixture, and golden files unchanged.
8. Reject the specified malformed schema cases before propagation.

Golden files must not be edited to accommodate production output.

## Prohibited behavior

The module must not generate upstream states, call a source gate, analyze connectivity, alter topology, calculate shortest paths, import or execute damage/fragility/repair/crew/travel/scheduling/GA/Monte Carlo code, modify source membership, change attachments, fill Class C, or renormalize W1 after missing states are known.
