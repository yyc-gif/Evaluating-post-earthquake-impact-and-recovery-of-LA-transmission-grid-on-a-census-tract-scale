# Upstream Adapter Regression Report

Date: 2026-09-14

Scope: read-only R1 upstream adapter and unchanged Architecture B production regression

Decision: **PASS — UPSTREAM ADAPTER CONTRACT VERIFIED**

## Existing R1 upstream artifact

The selected existing artifact is:

`Review_and_Revision/IJDRR-D-26-02276/11_TwoLayer_Static_QA_20260914/SERVICE_NODE_BASELINE_QA.csv`

SHA-256:

`a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384`

This file was already produced during the Round 11 static two-layer QA. It contains 506 typed rows and 21 columns. The adapter selects the 310 rows where `record_type=R1_NETWORK_ASSET`.

| Native artifact property | Observed |
|---|---:|
| Total rows | 506 |
| R1 upstream rows | 310 |
| Unique explicit R1 IDs | 310 |
| Native time count | 1 implicit static snapshot |
| Identified states | 306 |
| Identified state = 1 | 304 |
| Identified state = 0 | 2 |
| Missing states | 4 |
| Identified minimum / maximum | 0 / 1 |
| Duplicate R1 IDs | 0 |

The two identified zeros are RINGMILL `306980` and UNKNOWN309598 `309598`. The four native-missing states are RENO `301479`, UNKNOWN303265 `303265`, HALLDALE `304137`, and UNKNOWN305021 `305021`.

The artifact has no native time column because it is one static no-damage reference snapshot. The read-only acceptance call preserves that meaning as `time_index=0`, `source_time=reference_no_damage_snapshot`, and `source_time_unit=static_snapshot`. No hour, earthquake time, repair time, or QA time was inferred.

## State semantic decision

The chosen field is `effective_no_damage_network_state`. It is the state after the retained upstream source/component condition, ready to be consumed by the downstream service layer.

The original retained generator is:

`C:/ABAQUS/temp/sce_service_layer_20260914/build_static_qa.py`

SHA-256:

`2096c0081e2c21b74cd910114eae42c2319fc6f332166a5c5fab91321f386ae4`

Lines 70–81 validate the frozen component/source relation. Lines 100–139 set raw no-damage functionality to one and write effective state as one for a registered source-component-reachable node, zero for a registered source-component-unreachable node, and missing for unresolved registration. Lines 398–403 export the artifact without overwriting an existing output directory. The same logic and counts are recorded in the committed Round 11 report at lines 23–51.

Therefore the selected state is not raw functionality, damage state, repair state, repair completion, a standalone connectivity flag, or tract service. In this single no-damage snapshot, raw functionality is one, so the effective value numerically equals the identifiable source-reachability condition. The adapter reads `effective_no_damage_network_state` directly and does not recalculate it from the auxiliary fields.

This artifact is a real existing effective-state output, but it is static. It does not demonstrate that a dynamic recovery exporter already exists.

## Native schema and missingness

The frozen schema is `R1_STATIC_EFFECTIVE_STATE_SNAPSHOT_V1`.

Required native columns are:

- `record_type`, with the selector `R1_NETWORK_ASSET`;
- `record_id`, used as the only station identity;
- `effective_no_damage_network_state`, used as the already-computed state.

An empty field or dataframe NA is missing. Numeric zero is identified unavailable. The adapter never infers missingness from zero. For the production long-form serialization, a missing state receives the inert finite placeholder `0.0` together with `state_identified=False`; the production loader restores the semantic state to NA.

Literal missing tokens such as `NA`, `unknown`, or `null` are rejected because their semantics are not part of the retained native contract. Other nonnumeric values are also rejected.

The native static file has no time field. Multi-snapshot test data therefore use a separate outer envelope containing `native_snapshot_time_index`, `source_time`, and `source_time_unit`. The inner station ID and state fields remain in the native schema.

## Adapter implementation

`r1_effective_state_adapter.py` exposes:

1. `load_native_r1_effective_state_csv(...)` for one retained native CSV;
2. `adapt_native_r1_effective_state_table(...)` for one in-memory snapshot;
3. `adapt_native_r1_effective_state_snapshots(...)` for explicitly timed snapshots;
4. `adapt_native_r1_effective_state_envelope(...)` for a serialized multi-snapshot envelope;
5. `native_schema_sha256()` for the canonical schema identity.

The canonical output is ordered by increasing `time_index` and then by the caller-supplied frozen 310-ID order. Identity is never obtained from station name, coordinate, row number, or positional order.

The adapter only selects, renames, reshapes, validates, orders, and serializes missing masks. It performs no gate, topology, component, source, damage, repair, interpolation, smoothing, resampling, thresholding, clipping, filling, normalization, or station matching.

## Real artifact schema acceptance

The existing Round 11 artifact was read through `load_native_r1_effective_state_csv(...)`, then passed only to `load_validate_r1_effective_state_trajectory(...)`.

Result: **REAL_UPSTREAM_SCHEMA_ACCEPTED**.

- 310/310 frozen R1 IDs were present exactly once.
- One explicit static time envelope was accepted.
- 306 states were identified.
- Four states remained semantically missing.
- The two real zeros remained identified zeros.
- Identified values were finite and within `[0,1]`.
- The input dataframe and file hash were unchanged.

The real artifact was not propagated to service nodes or tracts. No new scientific output was produced from it.

## Golden native-schema round trip

The test-only serializer in `test_upstream_adapter_regression.py` converted the original Round 13 T0–T4 trajectory to `GOLDEN_NATIVE_SCHEMA_FIXTURE.csv`. It copied the existing state and identified mask into five native snapshot envelopes and did not calculate an upstream state.

The checked-in fixture contains 1,550 rows: 310 R1 IDs × 5 time indices. The adapter restored:

- all 1,550 time/ID cells;
- all 1,550 state values;
- all 1,550 identified/missing mask values;
- all source-time values and the `dimensionless_qa_index` unit.

Every comparison was exact. The restored output also passed the frozen production trajectory loader.

## Production golden regression through the adapter

Pipeline tested:

`Round 13 golden trajectory → test-only native serializer → R1 adapter → frozen service_layer_interface.py → golden comparisons`

| Regression check | Result |
|---|---:|
| Service-node/time states | 980 / 980 matched within `1e-12` |
| Class C missing mask | Exact |
| Tract/time interval rows | 4,085 / 4,085 matched within `1e-12` |
| Population aggregate indices | 5 / 5 matched within `1e-12` |
| T4 tract return to T0 | Exact |
| Adapter run 1 versus run 2 | Exact |
| Production outputs run 1 versus run 2 | Exact |
| Frozen inputs after regression | Hashes unchanged |

The real static artifact was not compared numerically with Round 13 because they represent different state inputs. The golden comparison tests representation preservation, not equality between the real snapshot and the synthetic T0–T4 fixture.

## Fail-fast tests

Nine malformed native inputs were tested, and each raised `R1EffectiveStateAdapterError`:

1. missing station;
2. unknown station;
3. duplicate station/time row;
4. unordered time blocks;
5. duplicate discontiguous time block;
6. state outside `[0,1]`;
7. ambiguous literal missing sentinel;
8. nonnumeric state;
9. missing station-ID field.

Result: **9 / 9 correctly failed fast**. No automatic repair was attempted.

## Dependency boundary

An AST import check confirms that the adapter imports only `dataclasses`, `hashlib`, `json`, `pathlib`, `typing`, `numpy`, and `pandas`, in addition to `__future__`. It does not import the main model or any topology, source, damage, fragility, repair, routing, crew, scheduling, GA, Monte Carlo, or service-propagation module.

The production service module remained unchanged at SHA-256:

`d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514`

## Provenance hashes

| Object | SHA-256 |
|---|---|
| Existing real upstream artifact | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Original retained generator | `2096c0081e2c21b74cd910114eae42c2319fc6f332166a5c5fab91321f386ae4` |
| Native schema definition | `5174371f1b40796133246c02797b3ec5f17d1ae8209857140fc68156a6b069c7` |
| Golden native-schema fixture | `b52605805f02cf12a959df50bee2fa7a34f5f1d6e8333015a79d74b4a2965249` |
| Adapter-restored golden trajectory, canonical serialization | `48d4317225e64fa80daf9ccaf286335d45978b7c2d27ac4a46c72325813eaff7` |
| Original Round 13 trajectory | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Frozen production service module | `d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514` |
| Adapter module | `7815704771fbe61b18f057a7ee49d061edd13aee1f85daa37c83781fa21a1f9f` |
| Adapter contract | `c355e1fc8f114fe08441d0092d6c4afe459a7f00a52a6be7e5ac3503ee63517c` |

## Decision and next gate

**PASS — UPSTREAM ADAPTER CONTRACT VERIFIED.**

The last representation boundary from the retained native R1 effective-state format to the frozen Architecture B production contract is lossless, deterministic, read-only, and fail-fast. Missing and real-zero states remain distinct. Adding the adapter does not alter the verified service or tract results of the Round 13 golden fixture.

The next and only permitted step is to define and statically test an explicit upstream export contract at the point where a future R1 process has already computed `EffectiveNetworkState_i(t)`. That work may test serialization using retained fixtures, but it must not run or change source-gate, topology, damage, repair, scheduling, GA, Monte Carlo, 32×4, or 29-crews logic. Because the accepted real artifact is only one static snapshot, a dynamic recovery export must not be claimed until such an exporter exists and is separately verified.
