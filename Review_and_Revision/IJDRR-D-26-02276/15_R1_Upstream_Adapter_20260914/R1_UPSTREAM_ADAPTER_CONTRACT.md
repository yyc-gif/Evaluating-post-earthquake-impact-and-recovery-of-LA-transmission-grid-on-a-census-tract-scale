# R1 Upstream Adapter Contract

Version: 1.0

Frozen: 2026-09-14

Applies to: read-only transfer of an already-produced R1 effective network state into the Architecture B production service-layer interface

## Selected existing upstream artifact

The selected artifact is:

`Review_and_Revision/IJDRR-D-26-02276/11_TwoLayer_Static_QA_20260914/SERVICE_NODE_BASELINE_QA.csv`

SHA-256:

`a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384`

It contains 506 typed rows. Exactly 310 rows have `record_type=R1_NETWORK_ASSET`; those rows contain 310 unique explicit `record_id` values and no duplicate ID. The other 196 rows are service-layer QA records and are outside the native upstream selection.

This artifact is a single static no-damage reference snapshot, not a recovery trajectory. It has no native time column. Its outer time provenance is therefore frozen as:

- `time_index=0`;
- `source_time=reference_no_damage_snapshot`;
- `source_time_unit=static_snapshot`.

These labels preserve the artifact's documented static meaning. They are not hours, earthquake time, repair time, or the Round 13 dimensionless QA sequence.

## State semantics

The native state field is `effective_no_damage_network_state`. The retained generator assigned raw no-damage functionality 1 to every R1 record, evaluated whether a registered R1 asset's frozen component contained one of the frozen 21 reference-source nodes, and wrote:

- `1` for registered and source-component reachable;
- `0` for registered and source-component unreachable;
- an empty field for unresolved registration whose network state was not identifiable.

The generator evidence is retained locally at:

`C:/ABAQUS/temp/sce_service_layer_20260914/build_static_qa.py`

SHA-256:

`2096c0081e2c21b74cd910114eae42c2319fc6f332166a5c5fab91321f386ae4`

Relevant implementation is at lines 70–81 (frozen component/source validation), 100–139 (effective-state construction), and 398–403 (non-overwriting export). The repository report `11_TwoLayer_Static_QA_20260914/TWO_LAYER_STATIC_QA_REPORT.md`, lines 23–51, records the same source scenario, equation, counts, and output identity.

This state is semantically compatible with the service-layer input because it is the post-source/component-gate R1 effective state prepared for downstream service propagation. It is not raw asset functionality, damage state, repair completion, a standalone connectivity flag, or tract service. For this no-damage snapshot, raw functionality is one, so the effective value equals the identifiable source-reachability gate. The adapter reads the already-written effective field and does not recompute that relationship.

## Native schema

Schema name: `R1_STATIC_EFFECTIVE_STATE_SNAPSHOT_V1`

Required native fields:

| Field | Contract |
|---|---|
| `record_type` | Select exactly `R1_NETWORK_ASSET` rows. |
| `record_id` | Explicit R1 station identity; must equal the frozen 310-ID set. |
| `effective_no_damage_network_state` | Already-computed effective R1 state; numeric `[0,1]` or explicitly empty/missing. |

Other retained columns are provenance and QA metadata. They are neither inputs to the state value nor modified by the adapter.

The native file is a static snapshot. A multi-snapshot sequence uses an outer envelope with:

- `native_snapshot_time_index`;
- `source_time`;
- `source_time_unit`.

The envelope changes representation only. The inner native identity and state fields remain unchanged.

## Missing and zero

An empty field or dataframe NA in `effective_no_damage_network_state` is native missing. Numeric zero is an identified unavailable state. Missingness is never inferred from zero.

The standard production trajectory requires a finite serialized value on every row. The adapter stores `0.0` as the inert serialized placeholder for a native-missing row and sets `state_identified=False`. The production loader therefore restores the semantic state to NA. The placeholder must never be interpreted without its mask.

Literal tokens such as `NA`, `unknown`, `null`, or `missing` are rejected as ambiguous native sentinels. Other nonnumeric values are rejected. The adapter does not guess their meaning.

## Identity and order

Station identity uses only `record_id`. Station names, coordinates, row position, and nearest matching are prohibited.

Every snapshot must contain the exact frozen 310-ID set once. The canonical output order is:

1. strictly increasing `time_index`;
2. the caller-supplied frozen R1 ID order used by the production contract.

The adapter does not depend on native row order.

## Adapter responsibilities

`r1_effective_state_adapter.py` may:

- select native R1 rows by `record_type`;
- normalize `record_id` to string;
- convert the explicit native missing encoding to `state_identified`;
- serialize the state and mask into the production long form;
- attach explicit outer time provenance;
- validate schema, identities, ordering, values, and missingness;
- sort deterministically.

It must not compute or modify source connectivity, topology, components, damage, fragility, repair, interpolation, resampling, smoothing, thresholds, clipping, filling, normalization, or station correspondence.

## Production handoff

Adapter output contains:

- `time_index`;
- `R1_station_id`;
- `effective_state_value`;
- `state_identified`;
- `source_time`;
- `source_time_unit`.

The first four fields are consumed by `load_validate_r1_effective_state_trajectory(...)`. The last two preserve original time provenance and are not interpreted by the service layer.

The real retained artifact is used only for read-only schema acceptance in this round. It is not propagated to new service or tract outputs.

## Golden native-schema fixture

`GOLDEN_NATIVE_SCHEMA_FIXTURE.csv` is a test-only outer envelope. Its 1,550 rows are the unchanged 310 × 5 Round 13 state/mask cells serialized into the selected native identity/state fields. `source_time` retains the Round 13 index and `source_time_unit=dimensionless_qa_index`.

The serializer exists only in `test_upstream_adapter_regression.py`. It is not a production function. The regression requires the adapter to recover the original Round 13 trajectory element by element before the existing production golden comparisons are run.

## Fail-fast behavior

The adapter rejects missing or unknown stations, duplicate station/time rows, duplicate or unordered time blocks, values outside `[0,1]`, ambiguous missing sentinels, nonnumeric states, missing ID fields, inconsistent time provenance, and any station set different from the frozen 310 IDs. It never repairs these inputs.
