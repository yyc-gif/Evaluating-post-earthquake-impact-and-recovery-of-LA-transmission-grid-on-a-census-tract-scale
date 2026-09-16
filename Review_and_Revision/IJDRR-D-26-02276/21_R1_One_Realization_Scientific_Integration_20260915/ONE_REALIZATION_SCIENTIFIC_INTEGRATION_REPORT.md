# One-realization scientific integration report

## Verdict

**PASS — ONE-REALIZATION SCIENTIFIC INTEGRATION VERIFIED**

This was a software integration test of the R1 scientific producer. It is explicitly labeled `TEST_ONLY_DETERMINISTIC_DAMAGE_REALIZATION`. It is not a paper result and supports no interpretation of recovery speed, T50/T80, community effects, equity, hospitals, strategies, or policy.

The current `simulate_recovery_mc_source_gated(...)` function was executed exactly twice for the same fixed realization:

1. instrumentation OFF;
2. instrumentation ON.

The source/component gate was genuinely executed in both calls. No damage sampling, repair sampling, dispatch, routing, scheduling, GA, tract propagation, service-layer propagation, plotting, or paper metric was run.

## Pre-run freeze

The manifest was written and reviewed before either scientific execution. Its SHA-256 is:

```text
d7a99586bab333139008469f135b297a95334a288191966572dec6d55782111a
```

Both calls used this same manifest and the same in-memory scientific inputs.

| Frozen object | Identity |
|---|---|
| Main-model commit | `c358b660caa6cc6327f8485892e4b7e080d6b37a` |
| `C257H_Project_Main.py` SHA-256 | `90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145` |
| Frozen graph checkpoint | `06_R1_310_LocalClosure_20260914/R1_310_EDGES.csv` |
| Graph checkpoint SHA-256 | `e2dd039ec40336ea800adc29aa6cf790ae3d89553c1491c149096b3be6377090` |
| Read-only graph identity | 310 nodes / 1,040 undirected direct edges |
| Component sizes | 302 / 2 / 1 / 1 / 1 / 1 / 1 / 1 |
| Ordered 310-ID hash | `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5` |
| Reference-source count/hash | 21 / `c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3` |
| Authoritative mask | 306 identified / 4 unidentified |
| Functional threshold | 0.5, unchanged |
| Source gate | enabled |
| Jobs | 1 |
| Time grid | 0, 1, 3, 6, 12, 24, 48, 72 hours since event |
| Repair formulation | current `normal`, scale 1.0 |
| Start times | 310 explicit zeros; integration-only simultaneous start |
| Scenario / strategy IDs | `INTEGRATION_TEST_R1` / `INTEGRATION_ZERO_START` |

The graph was not rebuilt. The retained edge checkpoint was deserialized read-only, with all frozen 310 IDs added as nodes, and its component membership was checked against the retained station connection ledger. No station registration, edge, source, component, projection, or topology input was changed.

## Mechanical damage-vector construction

Candidate filtering used only:

```text
registration_status = registered_compatible
component = 1
station not in frozen 21-source set
```

The 282 eligible candidates were sorted by numeric R1 ID. The first four were selected mechanically:

| Order | R1 ID | Name | Assigned state |
|---:|---|---|---:|
| 1 | 300008 | NOLA | DS1 |
| 2 | 300105 | WALNUT | DS2 |
| 3 | 300144 | STATION 11 | DS3 |
| 4 | 300167 | UNKNOWN300167 | DS4 |

All other 306 stations were assigned DS0. The resulting `310 x 1` vector hash is:

```text
a322a8ba6013d82f313778180939b0f18217dcea243690bd90f29e54bd736e93
```

Population, W, SCE service relations, hospitals, centrality, prior recovery results, and strategy performance were not read to choose these stations.

## Scientific A/B parity

The OFF and ON dataframes had the same index, columns, shape, and per-column dtypes. Their canonical numeric SHA-256 values were identical:

```text
OFF = edc1959e0fa347e41ccce05a9b662723b295387096776b67198ca40c73c60b70
ON  = edc1959e0fa347e41ccce05a9b662723b295387096776b67198ca40c73c60b70
```

| Check | Result |
|---|---:|
| OFF vs ON exact cells | 2,480 / 2,480 |
| Unequal cells | 0 |
| Maximum absolute difference | 0.0 |
| Canonical numeric bytes | exact |
| Collector objects | exactly 1: `mc_000000` |

Instrumentation therefore did not alter the returned scientific trajectory.

## Materialized realization parity

With `n_mc = 1`, the returned trajectory equals the one realization contribution. The in-memory materialized `effective_state` matched the ON scientific dataframe exactly:

| Check | Result |
|---|---:|
| Materialized vs ON exact cells | 2,480 / 2,480 |
| Unequal cells | 0 |
| Maximum absolute difference | 0.0 |
| Materialized-state SHA-256 | `e6472fefbf9ce5c10239d823036ea50f0ee221a1e3c40a4db3b99ffc07bd59dc` |

The mask comparison was independent of numeric state:

| Mask class | Expected | Observed |
|---|---:|---:|
| Identified | 8 x 306 = 2,448 | 2,448 |
| Unidentified | 8 x 4 = 32 | 32 |
| Exact mask cells | 2,480 | 2,480 |

The four unresolved IDs `301479`, `303265`, `304137`, and `305021` remained `state_identified=False` at all eight times. Their serialized numeric placeholders were zero but retained missing semantics through the mask.

RINGMILL `306980` and Montrose `309598` remained `state_identified=True` at all eight times while their effective values were zero. They are identified zeros, not missing states.

## Actual control-flow coverage

The real run observed four P3 intervals:

```text
[0,3), [3,4), [4,6), [6,8)
```

Actual path flags were:

| Path | Triggered |
|---|---|
| P1 gate disabled | No; gate was enabled |
| P2 leading zero | No |
| P3 event interval with kept nodes | Yes, four intervals |
| P4 event interval with no kept node | No |
| P5 no event indices | No |

No input was adjusted to obtain this coverage. P1/P2/P4/P5 remain covered by the prior fixture tests.

For each P3 interval, the enabled main-model branch assigned the scientific expression once to `legacy_segment`, passed that same caller-owned object to the observer, and then added that object to `local_sum`. The integration harness recorded one observation per interval; it did not recalculate `curves_by_ds * keep_mask`.

## Execution ledger and boundaries

An initial test-harness invocation failed while importing NetworkX from the bundled Python environment. That failure occurred before manifest generation, before loading the scientific function, and before any scientific execution. The harness was then run with the project's Anaconda environment, which already provided the retained scientific dependencies. No model parameter or scientific input changed.

The successful run performed exactly two scientific calls: one OFF and one ON. There was no third call, no different realization, and no retry after either call produced a trajectory.

The Round 17 export hook remained `None`. The exporter, service-layer interface, and tract propagation modules were not imported or called. No service-node, tract, population, SVI, hospital, T50/T80, AUC, or community result was calculated.

After both calls, the main model, controller, observer, materializer, graph checkpoint, station ledger, source ledger, and authoritative-mask ledger retained their pre-run hashes. `C257H_Project_Main.py` has no test-induced diff.

## Evidence files

- `ONE_REALIZATION_INPUT_MANIFEST.json`: frozen inputs and pre-run hashes.
- `ONE_REALIZATION_PARITY_QA.csv`: element-level parity and invariant checks; SHA-256 `2b05cc2318d08b67bcc1ec101591d7cde60f60d234334ea338dff596aadfe3f9`.
- `ONE_REALIZATION_INTEGRATION_EVIDENCE.npz`: ordered IDs, time grid, damage vector, start times, sources, mask, OFF/ON arrays, materialized state/mask, and observer event ledger; SHA-256 `5cfcd01fc2aa5853833a3083acee3b4b466c7974f8bfd9df3b5a7e06611b046e`.

## Direct answers

1. **Was the source/component gate actually executed?** Yes, in both approved calls, using the frozen graph and 21-node reference source scenario.
2. **Was only one deterministic realization used?** Yes. OFF and ON used byte/value-identical scientific inputs for the same `310 x 1` vector.
3. **How many scientific-function executions occurred?** Exactly two: OFF once and ON once.
4. **OFF vs ON exactness:** 2,480/2,480 cells exact; zero unequal cells; maximum absolute difference 0.0; numeric bytes exact.
5. **Materialized vs scientific trajectory:** 2,480/2,480 cells exact; maximum absolute difference 0.0.
6. **Mask:** exactly 2,448 identified and 32 unidentified cells.
7. **306980 and 309598:** both retained identified-zero semantics at all eight times.
8. **Four unresolved IDs:** all remained missing through `state_identified=False` at all eight times.
9. **Actual paths:** P3 only, in four intervals; P2, P4, and P5 did not trigger.
10. **Did instrumentation change a scientific result?** No.
11. **Exporter/service layer:** remained uncalled.
12. **Was any paper-usable recovery result produced?** **NO.** This is test-only integration evidence.
13. **Post-test code/input hashes:** unchanged.
14. **Next gate:** the producer has met the code and semantic conditions for a separately authorized `ONE-REALIZATION SERVICE-LAYER INTEGRATION`. No such service-layer run is authorized or performed here; all broader simulation remains stopped.
