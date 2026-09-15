# Two-Layer Static QA Report

Date: 2026-09-14

Manuscript: IJDRR-D-26-02276

Architecture: **B — two-layer service-access proxy**

Decision: **PASS — SERVICE LAYER STATICALLY COHERENT**

## Scope

This round performed one no-damage, static connectivity QA. It did not rebuild the frozen 310-node topology, modify registrations or sources, sample damage or repair, activate service-node damage, route crews, schedule repairs, run GA/Monte Carlo, or calculate recovery outcomes.

The static model has three linked representations:

1. Frozen R1 network infrastructure: 310 records and frozen facility edges/components.
2. SCE service-access layer: 196 canonical official service nodes.
3. Strict-SCE tract layer: 817 tracts linked by the complete official-candidate W1 matrix.

Class A is an identity reference to one existing R1 asset. Class B is a logical upstream dependency on one named R1 system/interface. Class C has no attachment and remains missing. No attachment was turned into a physical edge.

## Frozen 21-node reference source scenario

The source list was read from `08_UtilitySpecific_SetC_20260914/R1_SERVICE_ROLE_CROSSWALK.csv` where `SOURCE_SCENARIO_REFERENCE=True`. Before calculation, the sorted, newline-terminated UTF-8 ID list was required to match:

`c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3`

The exact 21 IDs are:

`300232, 301318, 302376, 302865, 303473, 303547, 306001, 306365, 306450, 306473, 306489, 307039, 307373, 307512, 307693, 308540, 308581, 309553, 309569, 309703, 310199`.

The frozen ledger classifies 18 as generation-role proxies and three as external-import proxies. All 21 are `registered_compatible`. Twenty lie in component 1 (302 nodes); SERFGEN 303547 lies in component 2 (two nodes). The source scenario was used only as a static reference boundary and was not written back to the frozen source ledger.

## Static network availability

Every R1 asset was assigned raw no-damage functionality 1. For a registered asset, effective no-damage state is 1 if its frozen component contains at least one of the 21 reference sources and 0 otherwise. An unresolved registration remains unidentifiable rather than being coerced to zero.

| Network result | Count |
|---|---:|
| R1 records | 310 |
| Registered compatible | 306 |
| Reference-source reachable | 304 |
| Registered but source-unreachable | 2 |
| Registration unresolved | 4 |

The two registered source-unreachable nodes are RINGMILL 306980 and UNKNOWN309598/Montrose. They remain frozen source-boundary/component limitations, not attachment failures. The four unresolved registrations are RENO 301479, UNKNOWN303265, HALLDALE 304137, and UNKNOWN305021. No Class A or B SCE service node depends on any of these six records.

The reference scenario therefore reaches 304/306 electrically represented R1 nodes (99.35%) and 304/310 inventory records (98.06%). It does not make the six remaining records electrically represented or source-available, but those gaps do not propagate into the A/B portion of the current strict-SCE service layer.

`SERVICE_NODE_BASELINE_QA.csv` contains 506 typed rows: all 310 R1 network records and all 196 SCE service nodes. This preserves the requested per-network-node audit without adding another output file.

## Architecture B state propagation

The implemented static rules are:

- A/D1: `ServiceState_j = EffectiveNetworkState_i`. The service node makes one reference to the corresponding R1 state. It is not multiplied by a duplicate service-node state.
- B/D2 or B/D3: `ServiceState_j = EffectiveNetworkState_upstream(i)`. D2 remains metadata readiness only; no service-node fragility, damage, repair task, or crew assignment is activated.
- C: `ServiceState_j = NA`. Missing is not zero, one, a nearest node, or a redistributed weight.

Static service-node results are:

| Attachment | Available | Unavailable | Missing | Total |
|---|---:|---:|---:|---:|
| A direct identity | 113 | 0 | 0 | 113 |
| B named-system proxy | 71 | 0 | 0 | 71 |
| C unresolved | 0 | 0 | 12 | 12 |

All 184 identified A/B service states resolve to component 1 and equal 1. The two source-unreachable registered R1 nodes and four registration-unresolved R1 records are not hidden; they simply are not attachment targets in this service-layer definition.

## Tract availability intervals

For each tract `r`:

- `ResolvedMass_r` is W1 mass on Class A+B nodes.
- `UnresolvedMass_r` is W1 mass on Class C nodes.
- `KnownAvailableMass_r` sums W1 multiplied by identified A/B service states.
- `BaselineLower_r = KnownAvailableMass_r`.
- `BaselineUpper_r = KnownAvailableMass_r + UnresolvedMass_r`.
- `ConditionalResolvedAvailability_r = KnownAvailableMass_r / ResolvedMass_r` when resolved mass is positive.

All 817 rows satisfy `ResolvedMass + UnresolvedMass = 1` within `1e-12`. The conditional value is retained only for QA and is not a community-service outcome.

| Tier | Required static condition | Result |
|---|---|---|
| S1, 444 tracts | Lower = Upper = 1 | 444 pass; 0 fail |
| S2, 318 tracts | Lower = Upper = 1 | 318 pass; 0 fail |
| S3, 43 tracts | resolved portion conditional availability = 1; interval `[1−C mass, 1]` | 43 pass; 0 additional upstream failures |
| S4, 12 tracts | fully unidentified interval `[0,1]` | 12 retained as unknown |

The population-weighted interval is:

`[0.9591569498, 1.0000000000]`.

The lower-bound gap, 0.0408430502, is exactly the previously bounded Class C population-weighted candidate mass within floating-point tolerance. Population-weighted additional deficit on resolved A/B mass is numerically zero (`−3.2e−19`, roundoff). Architecture B therefore introduces no extra no-damage baseline deficit beyond the declared Class C uncertainty.

The lower bound must not be called baseline outage or delivered-service fraction. It is the minimum identifiable modeled upstream availability when unresolved Class C states are allowed to range from 0 to 1.

## Duplicate-state QA

All 113 Class A service nodes reference exactly one R1 asset, and the 113 references are to 113 unique R1 IDs. No Class A row creates a second state, second damage draw, second repair task, or multiplicative state term.

The 71 Class B service nodes share 13 named upstream R1 interfaces. Shared logical dependencies are permitted. They represent modeled dependency concentration, not power capacity, customer loading, or a verified unique feeder path. No physical edge, topology edit, or source change was created.

Duplicate-state QA passes.

## Static dependency concentration

Service-node W1 concentration remains dispersed:

| Service-node concentration | Share of strict-SCE population-weighted candidate mass |
|---|---:|
| Maximum one node | 2.6806% |
| Top 5 | 10.2654% |
| Top 10 | 17.3586% |
| Top 20 | 29.5522% |

After aggregating A/B service nodes to their upstream R1 attachments:

| Upstream concentration | Share of total strict-SCE population-weighted candidate mass |
|---|---:|
| Maximum one interface | 3.5354% |
| Top 5 | 15.8301% |
| Top 10 | 26.1038% |
| Top 20 | 40.5523% |

The largest upstream concentrations are:

| Upstream R1 interface | Attached service nodes | Candidate relations | W1 population mass | Share of total |
|---|---:|---:|---:|---:|
| CENTER 300232 | 7 | 76 | 126,290.7 | 3.5354% |
| MESA 301541 | 11 | 84 | 119,703.1 | 3.3510% |
| LIGHTPIPE 303169 | 8 | 68 | 119,026.1 | 3.3321% |
| RIO HONDO 305984 | 5 | 56 | 104,702.6 | 2.9311% |
| CUDAHY 310167 | 1 | 48 | 95,754.2 | 2.6806% |
| DEL AMO 302187 | 15 | 58 | 80,715.9 | 2.2596% |
| WALNUT 300105 | 3 | 26 | 79,520.7 | 2.2261% |

The largest Class B-only group is MESA with 11 service nodes and 119,703.1 W1 population mass, followed by CENTER with six B nodes and 82,014.1, and LIGHTPIPE with seven B nodes and 78,307.4. The aggregation increases concentration as expected, but no single proxy interface dominates the primary domain. These values must be retained as a sensitivity concern for later event tests; they are not evidence of actual electrical loading.

## QA checks and evidence level

The following checks passed:

- The exact 21-source membership and ID-list hash matched before evaluation.
- All 21 reference sources are registered; no source was added or removed.
- Frozen edge endpoints remain within their recorded components.
- All 113 A and 71 B upstream IDs resolve uniquely.
- A/B service state uses one upstream R1 state lookup only.
- All C states remain missing and all C W1 mass remains in place.
- All tract mass and interval invariants pass at `1e-12` tolerance.
- S1/S2 have no deficit; S3 has no deficit outside its Class C mass.

This is a code-executed static QA over retained CSV outputs. It is not a power-flow validation, capacity check, customer-load allocation, damage simulation, or empirical outage validation.

## Decision and next allowed test

**PASS — SERVICE LAYER STATICALLY COHERENT.** All represented A+B candidate mass is source-reachable in the no-damage reference scenario. The only tract-level uncertainty is the already declared 4.0843% Class C population-weighted candidate mass.

The next and only allowed test is a **first no-damage deterministic service-layer integration event test** that exercises the frozen propagation chain:

`R1 network state → service-node state → tract availability interval`.

That test should use one controlled, deterministic network-state change to verify event propagation and interval accounting. It should not sample damage or repair, schedule tasks, run GA/MC, or run 32×4/29-crews scenarios.

## Direct answers

1. **A/B/C baseline:** A=113/113 available; B=71/71 available; C=12/12 missing, not failed.
2. **S1/S2:** all 444 S1 and all 318 S2 tracts are `[1,1]`.
3. **S3:** all 43 have conditional resolved availability 1; their remaining interval width is only Class C mass.
4. **Additional baseline deficit:** none beyond Class C uncertainty.
5. **Population-weighted bound:** `[0.9591569498, 1.0]`.
6. **Largest upstream proxy concentrations:** CENTER, MESA, LIGHTPIPE, RIO HONDO, CUDAHY, DEL AMO, and WALNUT; maximum share 3.5354%.
7. **Reference 21-source scenario:** sufficient and internally consistent for this service-layer QA; all 21 are registered, and all A/B targets are reachable. It does not energize every R1 record.
8. **Duplicate state:** pass; 113 direct nodes use one unique R1 state each, and B nodes inherit one upstream state without creating damage-bearing duplicates.
9. **Gate:** PASS — SERVICE LAYER STATICALLY COHERENT.
10. **Next test:** one controlled no-damage deterministic service-layer integration event test; all stochastic recovery and optimization calculations remain prohibited.
