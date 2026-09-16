# Disabled main-model instrumentation test report

## Verdict

**PASS — DISABLED MAIN-MODEL PRODUCER WIRING VERIFIED**

The observer is connected at the real segment-accumulation location, but remains inactive by default. Tests used only static source inspection and retained/synthetic fixtures. They did not call `simulate_recovery_mc_source_gated(...)`, `_process_mc_range`, either source-gate helper, Stage 1/3/4/5, sensitivity, damage, repair, scheduling, GA, or any Monte Carlo workflow.

## Exact main-model changes

Baseline commit: `cc83cdeae7ce9afc58c88c100463ae6ee7466585`.

`C257H_Project_Main.py` changed only inside `simulate_recovery_mc_source_gated(...)`:

1. Added final optional parameter `r1_producer_instrumentation: Any = None`.
2. Preserved the configured job count separately so enabled instrumentation can reject anything other than one before the retained job normalization/capping logic.
3. Added an enabled-only `validate_run_context(...)` call using the ordered `columns_norm`, unchanged `t_grid`, and configured job count.
4. Added one enabled-only session per `mc_idx`.
5. Added P1 full-trajectory observation and enabled-only finalization.
6. Added P5 full-zero observation and finalization when `event_idxs` is empty.
7. Added P2 leading-zero observation when the first event begins after index zero.
8. Added P3 single-evaluation `legacy_segment` observation and accumulation in the enabled branch; the disabled branch retains the original expression.
9. Added P4 explicit-zero observation when `keep_mask` has no true entry.
10. Added enabled-only finalization after all event intervals.

No recovery curve, functionality threshold, crossing index, `keep_mask` algorithm, source definition, graph/component operation, `local_sum` dtype, mean calculation, chunk range, diagnostic schema, existing call-site argument, or return value was changed.

## Controller behavior

The controller module exposes:

- `create_r1_main_model_producer_instrumentation(...)`;
- `R1MainModelProducerInstrumentation.validate_run_context(...)`;
- `R1MainModelProducerInstrumentation.start_realization(...)`;
- `R1ProducerInstrumentationSession.observe_precomputed_segment(...)`;
- `R1ProducerInstrumentationSession.observe_explicit_zero_segment(...)`;
- `R1ProducerInstrumentationSession.finalize()`.

It imports only standard-library metadata utilities, NumPy/Pandas, the Round 18 materializer, and the Round 19 observer. It has no NetworkX, topology, source, damage, fragility, repair, routing, crew, scheduler, GA, exporter, export-hook, service-propagation, or file-I/O dependency.

## Fixture and static-test results

Command:

```text
C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe test_disabled_main_model_instrumentation.py
```

The command was run from the Round 20 directory through a temporary short drive mapping because the repository's absolute Windows path exceeds the interpreter's path handling limit. The mapping changed no repository content and was removed after verification.

Result:

```text
Ran 10 tests in 0.324s
OK
DISABLED_MAIN_INSTRUMENTATION_TEST_SUMMARY={"control_flow_cases": 5, "fail_fast_cases": 14, "real_scientific_runs": 0, "result": "PASS_DISABLED_MAIN_MODEL_PRODUCER_WIRING_VERIFIED", "round11_identified": 306, "round11_missing": 4, "round13_cells": 1550, "tests": 10}
```

Verified outcomes:

- Default controller is fully inactive and carries no materializer, observer, collector, mask, or time state.
- P1–P5 fixture accumulators are bitwise identical between control and observed paths.
- P3's counted synthetic scientific expression is evaluated exactly once.
- P2/P4/P5 explicit-zero side paths never add zero arrays to the scientific accumulator.
- Round 13 transport through controller -> observer -> materializer -> test-only hook/exporter/loader preserved 1,550/1,550 states and masks exactly.
- Round 11 retained evidence preserved 306 identified / 4 unidentified: RINGMILL `306980` and UNKNOWN309598 are identified zeros; `301479`, `303265`, `304137`, and `305021` remain unidentified.
- All retained main-model call sites omit the new optional parameter.
- Main-model static inspection confirms the retained threshold, crossing logic, `keep_mask` call, accumulator dtype, ranges, averaging expression, and return structure remain present.
- The main model does not import the exporter, export hook module, or service-layer interface.
- Frozen Round 11/13 and Round 14/16/17/18/19 implementation fixtures were unchanged during testing.

## Fail-fast coverage

Fourteen contract failures were exercised:

1. enabled without structured context;
2. missing scenario ID;
3. missing strategy ID;
4. missing source-time unit;
5. aggregate trajectory scope;
6. station missing from the authoritative mask;
7. non-Boolean mask;
8. unknown station in the mask;
9. main `sub_index` order/identity mismatch;
10. station count other than 310;
11. configured parallel job count greater than one;
12. duplicate realization key;
13. incomplete materialization coverage;
14. enabled controller whose materializer/observer creation is disabled or absent.

No case is automatically repaired.

## Hash ledger

| Object | SHA-256 |
|---|---|
| Modified `C257H_Project_Main.py` | `90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145` |
| Controller | `b88e49aa2f7cda0af775e838dd692906e8806a36a6ee378672a5230333cc0069` |
| Test driver | `f00a2bff5e640c028d465bc3787ca2c225d931d0d935b9e86ac4b47658c0b8e5` |
| Round 11 static fixture | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Round 13 trajectory | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Round 14 production interface | `d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514` |
| Round 16 exporter | `79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b` |
| Round 17 export hook | `e3eb5228be0b17580f7313cac7d234f326f7e00c2a7fd027ba853ef6d01f4bf2` |
| Round 18 materializer | `ce95b971cadac9bc6f07d24832fcd8d817904395abfa2b447b86c4f3774da77d` |
| Round 19 observer | `ac0c395e95d81975e80830cae63e67bd2b161eec8141e61a3fa9301e14b3ac9c` |

The two Round 20 source hashes above are pre-report hashes. The report files themselves are not inputs to the regression.

## Direct answers

1. **Main-model lines changed:** only the function signature, job-count capture and enabled validation, session start, P1/P2/P3/P4/P5 observational branches, and enabled finalization inside `simulate_recovery_mc_source_gated(...)`.
2. **Default path inactive:** yes. Existing calls pass no instrumentation argument; no instrumentation object is allocated by the main model.
3. **P1–P5 materialization:** all five have complete, gap-free paths.
4. **P3 single evaluation:** yes; the enabled branch computes one caller-owned `legacy_segment`, observes it, and accumulates it.
5. **Zero side path:** P2/P4/P5 do not alter `local_sum`; fixture accumulation is bitwise exact.
6. **Mask source:** only the explicit frozen 306/4 authoritative ledger; `keep_mask` is not reused.
7. **Serial restriction:** enabled instrumentation rejects configured jobs other than one.
8. **Independent sessions:** yes, one materializer/observer/provenance object per deterministic `mc_idx` identity.
9. **Exporter/hook:** not connected from the main model; collection ends in memory.
10. **Fixture accumulation:** bitwise exact.
11. **Round 13:** 1,550/1,550 state/mask cells exact.
12. **Scientific equations:** none changed.
13. **Real scientific path run:** none.
14. **Readiness:** the code is ready for a separately authorized one-realization scientific integration test. This PASS does not authorize that run.

All recovery simulation, source-gate execution, damage/repair sampling, dispatch, scheduling, GA, 32x4, 29-crew, 114-crew, broader Monte Carlo, exporter wiring, and service-layer scientific output remain prohibited.
