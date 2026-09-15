# SCE Service-Layer Architecture Decision

Date: 2026-09-14

Manuscript: IJDRR-D-26-02276

Decision: **ARCHITECTURE B — two-layer service-access proxy**

Gate: **GO-SERVICE-LAYER-QA**

## Scope and frozen inputs

This round created a canonical SCE service-access layer and a logical upstream-attachment ledger. It did **not** rebuild the 310-node topology, activate a source set, run a source gate or baseline, sample damage or repair, dispatch crews, optimize a schedule, or run any recovery simulation.

The network layer remains the frozen R1 Set A/B. The SCE service layer is a separate set of official distribution-service candidates. An official circuit intersection establishes candidate membership; it does not establish customer-load shares, feeder capacity, a unique physical path, or delivered electricity.

The official planning GIS is a current public snapshot downloaded on 2026-09-14. The upstream R1 network remains a multi-epoch infrastructure proxy. The new logical attachments therefore support a transparent reference scenario, not a historical or current operating-system reconstruction.

Inputs used:

- `08_UtilitySpecific_SetC_20260914/SCE_CIRCUIT_SUBSTATION_CROSSWALK.csv`, SHA-256 `18afa885e439ad1b5962e028ea2a69e0e544cc934ccbceea8d5b1c127a80a8eb`.
- `08_UtilitySpecific_SetC_20260914/OFFICIAL_SERVICE_EVIDENCE.zip`, SHA-256 `8450c804063ba2af5fb2677332b27786fcbd250e36e1784695488293f295ba53`.
- `09_MappingArchitecture_20260914/EVIDENCE_TIER_COVERAGE.csv`, SHA-256 `1ab24b07b2f5cd7ecf97be280432c07f67e60afd769968b7efc60b21cdfa07c2`.
- Frozen R1 role, registration, and readiness ledgers from rounds 05, 06, and 08. No R1 identifier, edge, component, registration, or source flag was changed.

## Canonical 196-node service layer

The service-node key is `SCE-SVC-<normalized official name>`. Normalization uppercases the official name, removes punctuation/spacing and a terminal voltage suffix. Multiple circuit and bank records remain attached to one canonical node through their official IDs, raw names, coordinates, voltages, types, system name, and circuit IDs. This prevents bank/circuit records from being miscounted as distinct physical service facilities.

The resulting layer has 196 nodes, referenced by all 817 strict-SCE tracts and 2,041 tract–service-node candidate relations. Each tract has 1–7 candidates (median 2; mean 2.50). Node-level metadata and evidence are in `SCE_SERVICE_NODES_196.csv`.

## Attachment rules and result

Attachments were assigned without nearest-neighbor filling and without using recovery outcomes.

| Attachment class | Definition | Nodes | Population-weighted W1 mass |
|---|---|---:|---:|
| A — direct identity | Official service node and R1 node are the same physical facility under the frozen crosswalk | 113 | 79.8622% |
| B — named-system upstream proxy | No direct identity; official `sys_name` maps uniquely to one registered-compatible R1 system/interface by exact normalized R1 name or frozen CEC alias | 71 | 16.0535% |
| C — unresolved | No unique supported identity or named-system upstream attachment | 12 | 4.0843% |

The 18 official `sys_name` groups were processed once as groups. Fourteen map uniquely to registered-compatible R1 interfaces; all 71 eligible unmatched service nodes in those groups become Class B. Barre, Chino, Olinda, and Padua do not have an in-domain R1 upstream-system match, leaving their 12 service nodes in Class C. All 12 nodes without a usable system-level crosswalk remain unresolved after the bounded review.

Class B means **logical upstream supply dependency proxy**. It does not add a physical edge, prove terminal connectivity, define capacity, or establish a unique real supply path. Class C state remains missing/unsupported. It must not be set to zero and its W1 mass must not be reassigned or renormalized.

## Damage-role readiness and duplicate-state rule

| Damage role | Meaning in this round | Nodes | Population-weighted W1 mass |
|---|---|---:|---:|
| D1 | Same physical asset as an R1 network node | 113 | 79.8622% |
| D2 | Official coordinate, D/A service type, and voltage metadata could feed the existing voltage-class rule | 19 | 7.8238% |
| D3 | Valid service-mapping interface, but separate damage-bearing asset is outside the supported scope | 64 | 12.3140% |
| D4 | Service role and asset metadata unresolved | 0 | 0% |

D2 is a static feasibility flag. It does not validate applying the existing HAZUS substation fragility model to SCE distribution-station types, and it does not create a repair task. Of the 71 Class B nodes, 9 are D2 and 62 are D3. Of the 12 Class C nodes, 10 are D2 and 2 are D3.

Future state propagation under the selected Architecture B is defined as follows:

1. **Direct identity (A/D1):** `ServiceState_j(t) = EffectiveNetworkState_i(t)`. The service role references the R1 asset. No second damage draw, fragility evaluation, or repair task is created.
2. **Named-system proxy (B/D2 or B/D3):** `ServiceState_j(t) = UpstreamAvailability_j(t)`. The service node inherits the frozen upstream-interface state. Its own distribution-substation damage is outside the modeled scope.
3. **Unresolved attachment (C):** state is unsupported/missing until evidence closes the attachment. It is not interpreted as failed service and is not replaced by a nearby node.
4. **Independent service asset, if ever promoted in a later model:** `ServiceState_j(t) = OwnFunctionality_j(t) × UpstreamAvailability_j(t)`. This rule is not activated here.

## Complete official-candidate W1

`SCE_TRACT_SERVICE_W1.csv` contains the full 817 × 196 matrix. For tract `r` and its official candidate set `O_r`:

`W_service(r,j) = 1 / |O_r|` for `j` in `O_r`, and zero otherwise.

The matrix uses no legacy R1 weight, network distance, source reachability, nearest fill, or result-dependent choice. Equal share records candidate-membership uncertainty; it is not an estimate of customer-load share. All 817 rows have at least one candidate, all weights are finite and nonnegative, every row sum is exactly 1 within written precision, and the matrix has 2,041 nonzero entries.

## Attachment coverage by tract

The tract-level QA ledger preserves the distinction between candidate mass and population in tracts affected by unresolved candidates.

| Tier | Definition | Tracts | Population | Population share | Pop.-weighted SOVI mean | Hospital tracts | Pop.-weighted PGA (g) |
|---|---|---:|---:|---:|---:|---:|---:|
| S1 | 100% Class A | 444 | 1,936,737 | 54.22% | 70.74 | 28 | 0.8881 |
| S2 | 100% Class A+B, no C | 318 | 1,384,566 | 38.76% | 69.42 | 17 | 0.8941 |
| S3 | Partial Class C mass | 43 | 199,079 | 5.57% | 60.48 | 2 | 0.9222 |
| S4 | 100% Class C | 12 | 51,770 | 1.45% | 81.52 | 0 | 0.9005 |

Classes A+B account for 95.9157% of population-weighted candidate mass. Fifty-five tracts containing 250,849 people have some unresolved candidate mass; this is not the same quantity as the 145,897.6 population-weighted candidate mass assigned to Class C. S3 has lower SOVI and somewhat higher PGA than S1/S2, while S4 has higher SOVI. Missing attachment is therefore not demonstrably random and must remain visible in any subsequent analysis.

## Bounded review of unresolved exposure

The ten highest unresolved nodes account for 99.3206% of Class C population-weighted W1 mass. The review used only the retained upstream inventory and frozen study boundary; it did not expand to a 196-node provenance search.

| Node | Unresolved population-weighted W1 mass | Decision |
|---|---:|---|
| FRANCIS | 36,961.1 | Matching upstream inventory record is outside frozen R1 geometry; no in-domain attachment |
| SANANTONIO | 27,116.8 | Matching record is outside frozen R1 geometry; no in-domain attachment |
| TROPHY | 26,277.7 | R1 name exists, but archived crosswalk has a 271.86 m identity-coordinate conflict; no direct identity |
| POMONA | 23,665.1 | No exact retained upstream record; 12/4 kV service record; Chino system unresolved |
| PARKWOOD | 17,117.9 | Matching record is outside frozen R1 geometry; no in-domain attachment |
| PEYTON | 5,574.5 | Matching record is outside frozen R1 geometry; no in-domain attachment |
| LAHABRA | 2,586.4 | Matching record is outside frozen R1 geometry; no in-domain attachment |
| OLINDA | 2,586.4 | Relevant 230/66 kV record is outside frozen R1 geometry; same-name Shasta record rejected |
| MARION | 1,807.3 | Retained inventory says `STATUS=NOT AVAILABLE`, creating a period/status conflict |
| BREA | 1,213.3 | Matching record is outside frozen R1 geometry; no in-domain attachment |

PADUA and MOABPT contribute the remaining 0.6794%. Neither has a supported in-domain upstream attachment. The review resolves damage-readiness metadata for several nodes but does not resolve their upstream attachment.

## Architecture decision

**Architecture B is selected.** It is consistent with the manuscript's defensible scope: restoration of a modeled upstream transmission/subtransmission network and propagation of upstream availability to independently evidenced distribution-service candidates.

Architecture A is not supported now. Only 19 unmatched nodes are even statically feasible as independent assets, 64 are mapping-only interfaces, and the current fragility model has not been validated for these official service-station types. Activating D2 would add a new asset class, damage states, repair tasks, travel, and scheduling decisions, producing a materially different model.

Architecture C is rejected as the primary design. Restricting to S1 would retain only 444/817 tracts, 1,936,737/3,572,152 people, and 28/47 hospital tracts. The omitted domain also differs in SOVI and PGA. Its apparent purity would create a large evidence-based selection of communities.

The primary outcome must be named **modeled upstream availability at official SCE distribution-service candidates** or **distribution-service-access proxy**. It cannot be described as actual delivered electricity, customer outage, complete distribution-system restoration, or validated customer-to-substation dependency.

## Gate decision and next allowed step

The architecture meets **GO-SERVICE-LAYER-QA** because canonicalization and W1 are complete, 95.9157% of population-weighted candidate mass has an A/B upstream representation, unresolved mass is bounded and retained, and duplicate-state semantics are explicit.

The next allowed computation is one static two-layer service-graph QA using the frozen R1 topology and a separately authorized, frozen reference source-availability scenario. That QA must report unresolved service-state mass as missing, test all row/mass invariants, and must not coerce unresolved candidates to zero or redistribute them.

Recovery simulation, damage or repair sampling, dispatch, GA, Monte Carlo, 32×4, 29 crews, road-matrix work, topology rebuild, source-set modification, and source activation remain prohibited in this round.

## Direct answers

1. **A/B/C node counts:** 113 / 71 / 12.
2. **D1/D2/D3/D4 counts:** 113 / 19 / 64 / 0.
3. **The 71 `sys_name` candidates:** all 71 map uniquely through 14 supported system groups to a registered-compatible R1 upstream candidate.
4. **The 12 without a supported system crosswalk:** all 12 remain attachment-unresolved; the bounded top-ten review does not justify a forced link.
5. **S1/S2/S3/S4:** 444 / 318 / 43 / 12 tracts; populations 1,936,737 / 1,384,566 / 199,079 / 51,770.
6. **Tier composition:** shown in the attachment-coverage table; unresolved tiers are not compositionally identical to S1/S2.
7. **Unresolved W1 mass:** 4.0843% of population-weighted candidate mass.
8. **Largest unresolved contributors:** FRANCIS, SANANTONIO, TROPHY, POMONA, and PARKWOOD; the top ten account for 99.3206%.
9. **Recommended architecture:** B, two-layer service-access proxy.
10. **Proceed to static two-layer QA:** yes, subject to the frozen definitions above; this is not authorization for recovery simulation.
11. **Still prohibited:** all recovery, source-gate/baseline activation in this round, damage, repair, dispatch, GA, MC, 32×4, 29 crews, topology/source changes, nearest attachment, legacy-W filling, and unresolved-mass renormalization.
