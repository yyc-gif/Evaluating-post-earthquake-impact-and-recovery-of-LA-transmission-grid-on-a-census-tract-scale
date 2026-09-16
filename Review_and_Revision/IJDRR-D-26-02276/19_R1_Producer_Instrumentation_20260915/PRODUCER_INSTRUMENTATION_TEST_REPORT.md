# Producer instrumentation observer test report

## Result

**PASS — PRODUCER INSTRUMENTATION CONTRACT VERIFIED**

The observer copied retained/synthetic precomputed segments only. It did not
run the source gate, topology, recovery, damage, repair, scheduling, GA, or MC,
and it remains disconnected from the main model.

## What was verified

### Disabled no-op

The disabled observer returned before inspecting deliberately explosive
payload objects. It retained no materializer or mask. A synthetic control
accumulation and the same accumulation with a disabled observe call were
bitwise identical.

### Explicit five-path fixtures

A T=8 fixture explicitly supplied:

- `[0,2)` all-zero leading interval;
- `[2,4)` precomputed fractional interval;
- `[4,6)` all-zero interval representing no kept nodes;
- `[6,8)` precomputed mixed interval.

Separate full-width fixtures supplied one explicit `[0,T)` zero realization
for the no-event case and one complete `[0,T)` precomputed realization for the
gate-disabled case. The observer received only caller-supplied segments and
created no zeros.

For every fixture:

```text
control:  local_sum += segment
observed: observe(segment, mask); local_sum += same segment
```

produced bitwise-identical accumulators. State and mask hashes were unchanged
before and after observation, and every observe call returned `None`.

### Aliasing and mutation

After observation, the test deliberately overwrote the caller's state and mask
DataFrames. The finalized materialized object still equaled the pre-observation
snapshot exactly. Observer/materializer operations likewise left caller inputs
unchanged.

### Round 13 transport

The five-index fixture was supplied through three precomputed segments and the
full chain:

```text
observer -> Round 18 materializer -> Round 17 hook
-> Round 16 exporter -> production loader
```

All 1,550/1,550 state/mask cells were exact. IDs, time, and missing semantics
were unchanged. Observer counters recorded three segments and 1,550 cells.

### Round 11 mask evidence

Round 11 retained 306 identified and four unidentified R1 records. Round 13
used exactly this mask at all five time indices. RINGMILL `306980` and
UNKNOWN309598 `309598` remained identified zeros; the four unresolved
registration IDs remained missing. This supports the current
`STATION_STATIC_WITHIN_TRAJECTORY` contract.

### Expression parity

For synthetic `float64` arrays containing zeros, fractions, and a mixed Boolean
keep vector, these forms had equal dtype, shape, product bytes, and accumulator
bytes:

```python
local_sum += curves * keep

legacy_segment = curves * keep
local_sum += legacy_segment
```

This verifies the proposed naming step without executing the model. It does
not authorize main-model instrumentation in this round.

### Fail-fast and dependency checks

The tested failures included:

- enabled observer without materializer;
- missing state segment;
- missing mask segment;
- `mc_mean` scope;
- `aggregate` scope;
- state/mask shape mismatch;
- station mismatch;
- time mismatch;
- station subset;
- anonymous positional state array;
- masked nonzero;
- identified value above one.

AST inspection confirmed the observer imports only its allowed dependencies
and contains no gate, graph, source-loading, curves, damage, fragility, repair,
crew, schedule, GA, MC, accumulation, service-layer, exporter, or hook logic.

The main model SHA-256 remains
`b9efcd0487b1e9f115876a3c6f2b45dc342e20c7a516cd491846d4f9557654df`,
and its diff from Round 17 commit `1bad6deb...` is empty.

Final test output:

```text
Ran 9 tests in 0.356s
OK
PASS_PRODUCER_INSTRUMENTATION_CONTRACT_VERIFIED
control_flow_cases = 5
round13_cells = 1550
round11_identified = 306
round11_missing = 4
observer_fail_fast_cases = 12
scientific_runs = 0
```

## Direct answers

1. **Does the observer compute scientific state?** No. It validates and
   deep-copies caller-precomputed segments only.
2. **Does it generate any zero?** No. Every zero interval must be explicitly
   supplied by the future scientific producer.
3. **What is the authoritative mask source?** The frozen R1
   registration/state-domain ledger, represented by the retained Round 11
   306/4 mask.
4. **Is the mask static or time-varying?** Under the current Architecture B
   semantics it is station-static within each trajectory. Round 13 confirms
   the same mask at all five indices; no retained evidence supports temporal
   changes.
5. **Can `keep_mask` be used as the identified mask?** No. It represents
   source-connected functional membership, not state-domain identifiability.
6. **How are the five legacy paths materialized?** P1 supplies one complete
   ungated segment; P2 explicitly supplies the leading zero interval; P3
   observes the exact computed event segment; P4 explicitly supplies a zero
   interval; P5 supplies a complete zero trajectory.
7. **Can the observer change the caller segment?** No. Inputs remain unchanged,
   and later caller mutation cannot alter the stored snapshot.
8. **Is factor-expression parity bitwise exact?** Yes for the synthetic
   float64 zero/fraction/mixed-mask fixture.
9. **Are Round 11 and Round 13 still lossless?** Yes: Round 11 preserves the
   exact 306/4 and zero/missing semantics; Round 13 preserves 1,550/1,550 cells.
10. **Is the main model unchanged?** Yes, hash and Git diff confirm zero
    modification.
11. **May the next round implement disabled main-model instrumentation?** Yes,
    while retaining fixture-only validation and unchanged scientific
    accumulation.
12. **What real runs remain prohibited?** Source gate, topology propagation,
    damage, fragility, repair, dispatch, crews, routing, scheduling, GA, MC,
    32x4, 29-crews, 114-crews, and any real recovery trajectory or export.

## File hashes

| Object | SHA-256 |
|---|---|
| Round 11 fixture | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Round 13 fixture | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Production loader | `d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514` |
| Round 16 exporter | `79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b` |
| Round 17 hook | `e3eb5228be0b17580f7313cac7d234f326f7e00c2a7fd027ba853ef6d01f4bf2` |
| Round 18 materializer | `ce95b971cadac9bc6f07d24832fcd8d817904395abfa2b447b86c4f3774da77d` |
| Unchanged main model | `b9efcd0487b1e9f115876a3c6f2b45dc342e20c7a516cd491846d4f9557654df` |
| Observer | `ac0c395e95d81975e80830cae63e67bd2b161eec8141e61a3fa9301e14b3ac9c` |
| Test driver | `a782282d1f1ab205fd97ed5363cc4e356e98836b9bcb7d4ee1b28bd1ce553201` |
