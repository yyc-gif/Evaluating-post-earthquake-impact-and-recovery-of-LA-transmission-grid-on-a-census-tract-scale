# Disabled export wiring test report

## Result

**PASS — DISABLED EXPORT WIRING SEAM VERIFIED**

The seam is installed but unpowered. No dynamic producer exists, no exporter
is called from the main model, and no scientific computation was run.

## What changed

### New hook module

`r1_effective_state_export_hook.py` provides a frozen default-disabled hook and
one transport function. The transport returns immediately when the hook is
absent or disabled. When enabled, it requires a complete dual-channel producer
object and realization identity before invoking the supplied callback.

### Minimal main-model diff

`C257H_Project_Main.py` changed only at the following locations:

| Lines | Change | Effect |
|---:|---|---|
| 2176 | Added final optional parameter `effective_state_export_hook: Any = None` | Existing callers remain unchanged. |
| 2185–2191 | Added fail-closed guard | `None` and explicit disabled hooks proceed; enabled or invalid hooks are rejected because no producer exists. |
| 2312–2317 | Added `R1_DYNAMIC_EXPORT_SEAM` comment | Marks the future post-gate/pre-accumulation location without invoking the hook. |

The existing accumulation remains exactly:

```python
local_sum[time_start:time_stop, :] += (
    curves_by_ds[ds_vec, time_start:time_stop, sub_positions].T * keep_mask
)
```

No scientific equation, mask, curve, accumulation order, mean, source, graph,
parallel range, call-site argument, or return type changed.

## Tests executed

`test_disabled_export_wiring.py` ran eight fixture/static tests:

1. The default hook is `enabled=False`, `callback=None`.
2. A disabled hook produced zero callback calls, no files, no input mutation,
   and bitwise-identical synthetic accumulation relative to the legacy fixture.
3. Enabled calls missing both channels, missing the mask, or missing the state
   failed closed. An enabled hook without a callback also failed.
4. The frozen Round 13 five-index fixture traveled through the hook, Round 16
   exporter, and production loader with all 1,550 state/mask/ID/time cells
   exact.
5. `mc_mean`, `aggregate`, missing realization ID, and empty realization ID
   provenance were rejected.
6. Two enabled fixture calls produced exactly identical output and provenance.
7. AST and textual checks confirmed the hook dependency boundary and absence
   of scientific-model calls.
8. AST checks confirmed the optional parameter, default `None`, marker,
   unchanged accumulation expression, absence of export calls, and unchanged
   existing call sites.

Test output:

```text
Ran 8 tests in 0.298s
OK
PASS_DISABLED_EXPORT_WIRING_SEAM_VERIFIED
round13_cells = 1550
disabled_callback_calls = 0
scientific_runs = 0
```

## Direct answers

1. **Where is the seam?** Immediately before `local_sum` accumulation inside
   `_process_mc_range(...)`, marked at lines 2312–2317. The optional parameter
   and fail-closed guard are at lines 2176 and 2185–2191.
2. **Is default behavior an absolute no-op?** Yes. Existing call sites pass no
   argument. No trajectory or mask is built, no callback is called, no file is
   written, and the accumulation statement is unchanged.
3. **Does a real producer currently exist?** No:
   `DYNAMIC_EFFECTIVE_STATE_PRODUCER = NOT CURRENTLY IMPLEMENTED`.
4. **Who must provide state when enabled?** The future producer located after
   source/component gating and before aggregation.
5. **Who must provide the mask?** The same producer must explicitly carry the
   authoritative registration/state-identifiability mask. The hook and
   exporter cannot infer it.
6. **Can an MC mean be misconnected as a realization?** No. The wiring layer
   requires `trajectory_scope=realization` and nonempty scenario, strategy, and
   realization IDs. Aggregate scopes fail closed.
7. **Was fixture transport lossless?** Yes, 1,550/1,550 cells, IDs, masks, and
   times were exact through hook, exporter, and loader.
8. **Was disabled regression exact?** Yes. Callback count was zero, no files
   appeared, inputs were unchanged, and synthetic accumulation was bitwise
   equal.
9. **Did any scientific equation or accumulation change?** No.
10. **May the next round implement a producer-side materialization unit?** Yes,
    but only as a disabled, fixture-tested unit until separately authorized.
11. **What remains prohibited?** Real source-gate execution, topology
    propagation, damage, fragility, repair, dispatch, crew routing, scheduling,
    GA, MC, 32x4, 29-crews, 114-crews, or any real recovery trajectory/export.

## Frozen-input and code hashes

| Object | SHA-256 |
|---|---|
| Round 11 static fixture | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Round 13 five-index fixture | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Round 16 exporter | `79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b` |
| Production service interface | `d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514` |
| Updated main model | `b9efcd0487b1e9f115876a3c6f2b45dc342e20c7a516cd491846d4f9557654df` |
| Hook module | `e3eb5228be0b17580f7313cac7d234f326f7e00c2a7fd027ba853ef6d01f4bf2` |
| Test driver | `edeeaa5629bb88824b4a882595a0d3788cb74909393049a2ceac00a0e7f3a493` |
