# Production Interface Regression Report

Date: 2026-09-14

Scope: Architecture B production-interface freeze only

Decision: **PASS — PRODUCTION INTERFACE CONTRACT FROZEN**

## What was done

The already verified Architecture B propagation logic was extracted into the standalone production module `service_layer_interface.py`. The module consumes an external R1 effective-state trajectory, maps it to the frozen SCE service layer, and aggregates service states to tract availability intervals. It contains no logic that generates or interprets the upstream states.

The original Round 13 T0–T4 trajectory and its verified service-node and tract outputs were used in place as the regression fixture and golden references. The golden files were not copied, regenerated, or modified.

No source gate, topology propagation, damage, fragility, repair, routing, crew, scheduling, optimization, Monte Carlo, or recovery calculation was run.

## Production interfaces

The module exposes four public processing functions and one single entry point:

1. `load_validate_r1_effective_state_trajectory(...)` validates and standardizes an externally supplied time × R1 effective-state trajectory.
2. `validate_service_attachment_ledger(...)` enforces exactly one upstream R1 ID for every Class A/B service node and no upstream ID for Class C.
3. `propagate_network_state_to_service_layer(...)` performs the frozen A/B lookup and preserves Class C as missing.
4. `aggregate_service_states_to_tract_intervals(...)` applies the complete W1 matrix without renormalization and returns tract and population-weighted intervals.
5. `evaluate_service_layer_trajectory(...)` is the single production entry point joining those operations without reading other project inputs.

## Frozen contract

### Upstream input

The module only consumes `EffectiveNetworkState_i(t)`. It neither determines nor assumes whether that state came from a manual fixture, source/connectivity process, earthquake model, repair model, or another upstream process. It never generates an upstream state.

Every time index must contain exactly the frozen 310 R1 IDs. Time indices must be unique and strictly increasing; time/R1 rows must not be duplicated; serialized state values must be finite and in `[0,1]`; and the identified/missing mask must be constant and match the supplied frozen T0 mask.

### Missing state

An unresolved R1 upstream state remains missing. An A/B service node that references it also becomes missing. Class C is always missing. Missing state is never converted to zero, one, a nearest node, or a carried-forward value.

### Attachments

- Class A: `ServiceState_j(t) = EffectiveNetworkState_i(t)` for the same physical R1 asset.
- Class B: `ServiceState_j(t) = EffectiveNetworkState_upstream(i,t)` for its one named-system upstream proxy.
- Class C: `ServiceState_j(t) = NA`.

The module creates no second Class A damage state and applies no second multiplication. Multiple Class B service nodes may read the same upstream state, but each reads it once.

### W1 and intervals

Every strict-SCE tract retains its complete official-candidate W1 row. State missingness does not alter the weights. The output is:

- `ResolvedMass`: W1 mass with an identified service state;
- `UnresolvedMass`: W1 mass with a missing service state;
- `KnownAvailableMass`: W1-weighted identified state;
- `Lower = KnownAvailableMass`;
- `Upper = KnownAvailableMass + UnresolvedMass`;
- `ConditionalResolvedAvailability`: diagnostic only when resolved mass is positive.

The frozen W1 CSV stores 12 significant digits. Two six-candidate rows differ from unit sum by approximately `2.0e-12`; production validation therefore uses an explicit `5e-12` serialization tolerance without changing any weight. Comparisons with the verified golden outputs retain the requested `1e-12` tolerance.

## Frozen identity checks

| Object | Verified identity |
|---|---:|
| Reference source scenario | 21 IDs; `c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3` |
| R1 IDs | 310; `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5` |
| Service IDs | 196; `1c2533ea1ba4efd7894910e49c322654c90ec0eca6047908249a4c6e1b5d2f46` |
| Attachment ledger | `b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e` |
| W1 | `a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221` |
| Tract metadata file | `4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b` |
| Canonical tract ID/population rows | `e2af72b613cec85e35834aca4785b782c433d981b4969fd87c761cccb7b529e8` |
| Frozen T0 network/service state | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Frozen T0 tract intervals | `e285c9bbc8a1ecb9dd7057060ef4f5453edea42f70ffb4b7d42d9c0975e3ed9a` |
| Round 13 T0–T4 trajectory | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Golden service output | `8d7b55f660717753c1a715a4792dde2f429faf4d42b567a03eb68ec2aa6a95cb` |
| Golden tract output | `5cf3fb759bea519f6f3fbaee4cdffb422261b1a9a4157c296c8be7bd58c3009d` |

All file hashes were rechecked before and after the test run and remained unchanged.

## Golden regression results

| Check | Result |
|---|---:|
| Original Round 13 trajectory read directly | PASS |
| Service-node/time elements compared | 980 / 980 |
| A/B numerical agreement with golden | PASS, absolute tolerance `1e-12` |
| Class C missing mask | Exact match |
| Tract/time rows compared | 4,085 / 4,085 |
| Lower agreement | PASS, absolute tolerance `1e-12` |
| Upper agreement | PASS, absolute tolerance `1e-12` |
| Width agreement | PASS, absolute tolerance `1e-12` |
| Population-weighted aggregate time indices | 5 / 5 matched within `1e-12` |
| Interval width across T0–T4 | Exact invariant per tract |
| T4 network vector return to T0 | Exact |
| T4 service states return to T0 | Exact, including missing mask |
| T4 tract output return to T0 | Exact |
| Run 1 versus run 2 | Exact for all returned data frames |
| Non-CENTER/MESA upstream fixture states | Exact T0 values at every index |
| Frozen input files after run | Exact hashes unchanged |

The production output has no event-history residual and does not depend on execution order. Repeating the same input creates equality-identical network, mask, service, tract, and aggregate data frames.

## Fail-fast contract tests

Seven malformed-input cases were tested. Each raised `ServiceLayerContractError` before a production result was accepted:

1. one missing R1 ID;
2. one duplicate time/R1 ID;
3. an A/B attachment referencing an unknown R1 ID;
4. an A/B service node assigned two upstream IDs;
5. a W1 row whose mass no longer sums to one;
6. an effective-state value outside `[0,1]`;
7. a Class C service node assigned an upstream ID.

Result: **7 / 7 correctly failed fast**.

## Dependency boundary

An AST import check confirms that the production module imports only `dataclasses`, `re`, `typing`, `numpy`, and `pandas` in addition to `__future__`. It does not import any project source, topology, damage, fragility, repair, travel, crew, scheduling, GA, or Monte Carlo module. It performs no file discovery and cannot activate or change the 21-node source scenario, topology, W1, or attachment ledger.

## Decision and next gate

**PASS — PRODUCTION INTERFACE CONTRACT FROZEN.**

The Architecture B software boundary now preserves the verified A/B/C semantics, missing-state interval treatment, and Round 13 T0–T4 behavior. The golden references remain external to the production implementation, so later changes cannot silently redefine expected output.

The next and only permitted step is to build a thin, read-only upstream adapter/schema check that converts one already-produced R1 `EffectiveNetworkState(t)` table into this contract and reruns the same golden regression. That step must not generate new upstream states or invoke source, topology, damage, repair, scheduling, or recovery logic. Recovery simulation, 32×4, 29-crews, GA, MC, new mapping, source sensitivity, and W1 sensitivity remain prohibited.
