# Deterministic Service-Layer Integration Event Report

Date: 2026-09-14

Target: CENTER, R1 ID 300232

Event definition: **synthetic deterministic availability toggle**

Decision: **PASS — EVENT PROPAGATION VERIFIED**

## Scope

This round tested only the handoff:

`R1 effective network state → SCE service-node state → tract availability interval`.

It did not recalculate the source gate, remove a node or edge, propagate a topology failure, sample damage/PGA/fragility, sample or execute repair, assign crews, route travel, schedule tasks, run GA/Monte Carlo, or produce a recovery conclusion.

The event driver is `deterministic_event_test.py` in this directory. It reads the frozen T0 effective-state vector produced by round 11. T1 is a deep copy in which only `EffectiveNetworkState[300232]` is set from 1 to 0. T2 changes that one value back to 1. No source-connectivity or topology function is called.

## Frozen-input gates

The test refused to run unless the exact frozen source scenario contained 21 IDs and its sorted, newline-terminated UTF-8 hash equaled:

`c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3`.

Additional frozen identities were checked:

| Input identity | Count / SHA-256 |
|---|---|
| R1 IDs | 310; ID-list hash `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5` |
| Service IDs | 196; ID-list hash `1c2533ea1ba4efd7894910e49c322654c90ec0eca6047908249a4c6e1b5d2f46` |
| Attachment ledger | `b1a7ad8e6f162bed06fb88694a0393aa0d1fc7d4ef515ba628ede242e809ed9e` |
| W1 | `a21b583338a4583e2362aba70667ac8c443abe0cf3a732b98f022175cf4f6221` |
| Tract/population input | `4658c4f439a1ae41d77a5d5d14e6a8cbb950f1f71f123f2edd9190fa7a992f8b` |
| Frozen topology edges | `e2dd039ec40336ea800adc29aa6cf790ae3d89553c1491c149096b3be6377090` |
| Frozen T0 node baseline | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Frozen T0 tract intervals | `e285c9bbc8a1ecb9dd7057060ef4f5453edea42f70ffb4b7d42d9c0975e3ed9a` |

All input hashes were identical before and after execution. The source membership, topology, 310 network IDs, 196 service IDs, attachment ledger, W1, population values, tier labels, and 12-node Class C set were not modified.

## Analytic expectation calculated before propagation

The target set was derived from the frozen service-node table using:

`upstream_R1_id = 300232` and `attachment class ∈ {A, B}`.

No count or name was hard-coded. The resulting seven service nodes are:

| Service node | Attachment | Tract candidate relations | Population-weighted W1 mass |
|---|---|---:|---:|
| CENTER | A direct identity | 25 | 44,276.533333318 |
| DAELEY PT | B named-system proxy | 1 | 885.250000000 |
| DOWNEY | B named-system proxy | 12 | 18,347.266666655 |
| FLORADAY | B named-system proxy | 6 | 9,995.116666665 |
| PASSONS | B named-system proxy | 19 | 34,999.449999988 |
| RIVERA | B named-system proxy | 11 | 15,133.049999993 |
| RONNIE PT | B named-system proxy | 2 | 2,654.000000000 |

Totals: **7 nodes = 1 A + 6 B**, with 76 tract-candidate relations. Because several candidates occur in the same tract, the union contains 51 affected tracts.

From the frozen W1 and tract population, rather than the previously rounded report value:

- `CENTER_POP_WEIGHTED_MASS = 126,290.666666619` population-weighted W1 units.
- Normalized strict-SCE share = `0.03535422531477355`.

For each tract, `CenterMass_r` is the sum of W1 over those seven nodes. Before executing T1, the expected values were calculated as:

- `ExpectedLower_T1 = Lower_T0 − CenterMass`.
- `ExpectedUpper_T1 = Upper_T0 − CenterMass`.
- `ExpectedWidth_T1 = UnresolvedMass = Width_T0`.

## Three executed states

### T0 — frozen reference baseline

The 310-node network vector and all service/tract values reproduce the round-11 static QA within `1e-12`:

- A: 113 available.
- B: 71 available.
- C: 12 missing.
- Population-weighted interval: `[0.959156949834627, 0.999999999999710]` from the executed frozen CSV values.

The few `~4×10−15` differences between analytic and executed aggregates reflect floating-point summation order and are far below the acceptance tolerance.

### T1 — CENTER synthetic unavailable

Exactly seven service nodes changed from 1 to 0: the direct CENTER node and the six named-system proxies listed above.

- Other A/B changes: 0.
- Class C conversions to 0 or 1: 0.
- Cascading B-to-B propagation: 0.
- Network-vector changes other than CENTER: 0.
- W1 renormalization or reassignment: 0.

Observed population-weighted T1 interval:

`[0.923802724519854, 0.964645774684936]`.

Both aggregate bounds fell by `0.035354225314774`, matching the independently calculated CENTER mass within `1e-12`. The population-weighted interval width remained `0.040843050165083`.

### T2 — CENTER restored

Setting only CENTER back to 1 produced exact restoration:

- Network vector exactly equals T0.
- Service vector, including all Class C `NA` values, exactly equals T0.
- All 817 tract lower, upper, and width values exactly equal T0.
- Aggregate bounds exactly equal the executed T0 aggregates.

No event-history residual remains.

## Tract-level acceptance checks

The 51 affected tracts contain 243,790 people and four hospital tracts. Their tier composition is:

| Tier | Affected tracts |
|---|---:|
| S1 | 9 |
| S2 | 42 |
| S3 | 0 |
| S4 | 0 |

Among affected tracts, `CenterMass` has minimum 0.2, median 0.5, and maximum 1.0.

For all 817 tracts:

- Observed `ΔLower = −CenterMass` within `1e-12`.
- Observed `ΔUpper = −CenterMass` within `1e-12`.
- T1 interval width equals T0 within `1e-12`.
- T1 interval width also matches T0 by exact floating-point equality for all 817 rows.
- Unaffected tracts have identical T0/T1/T2 intervals.
- S4 remains `[0,1]` throughout.

`TRACT_EVENT_INTERVAL_QA.csv` preserves the analytic expectation, observed values, deltas, width checks, and restore checks for every tract.

## Duplicate-state check

The direct CENTER service node performs one lookup of `EffectiveNetworkState[300232]`. It is not calculated as `CENTER network state × CENTER service state`.

Each of the six Class B nodes independently performs one lookup of the same upstream CENTER state. This represents seven community-mapping roles sharing one physical upstream state, not seven physical damage events. No service-node fragility, damage state, repair task, or second state multiplier exists in this test.

All 184 A/B service nodes have exactly one R1 lookup per event state; all 12 Class C nodes have zero lookups and remain missing. Duplicate-state QA passes.

## Acceptance decision

**PASS — EVENT PROPAGATION VERIFIED.** The two-layer architecture propagates one known upstream state change exactly as predicted, preserves the Class C interval width, does not modify W1, and returns exactly to T0 after restoration.

This test says nothing about earthquake behavior, physical failure propagation, repair, scheduling, strategy performance, customer outages, or policy effects.

## Next allowed test

The next single allowed test is a **minimal deterministic time-indexed interface test using an externally supplied R1 effective-state trajectory**. Its purpose would be to verify time indexing and repeated `network state → service state → tract interval` accounting. It should still bypass damage, repair, source-gate recomputation, topology propagation, scheduling, GA, and Monte Carlo. Any move to 32×4 or crew experiments requires a later explicit gate.

## Direct answers

1. **CENTER attachments:** seven service nodes: one Class A and six Class B.
2. **Exact frozen-CSV CENTER mass:** 126,290.666666619 population-weighted W1 units, or 0.03535422531477355 of strict-SCE population.
3. **Affected tracts:** 51; population 243,790; four hospital tracts.
4. **T1 service changes:** only the expected seven nodes changed 1→0; no unintended changes.
5. **Tract deltas:** all 817 observed `ΔLower` and `ΔUpper` match `−CenterMass` within `1e-12`.
6. **Interval width:** unchanged for all 817 tracts, including exact floating-point equality.
7. **Aggregate decline:** both lower and upper fall by the independently calculated normalized CENTER mass.
8. **T2 restoration:** exact for network, service, tract intervals, and aggregate bounds.
9. **Duplicate state:** pass; one R1-state lookup per A/B service node and no service-node damage state.
10. **Gate:** PASS — EVENT PROPAGATION VERIFIED.
11. **Next allowed work:** one deterministic time-indexed external-state trajectory QA only; no recovery or stochastic computation.
