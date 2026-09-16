# Producer materialization test report

## Result

**PASS — PRODUCER MATERIALIZATION UNIT VERIFIED**

The unit assembles explicit retained/synthetic segments only. It is not wired
to the main model and no source gate, damage, repair, scheduling, GA, MC, or
recovery function was executed.

## Implementation

`r1_effective_state_materializer.py` provides:

- `create_r1_realization_materializer(...)`, default `enabled=False`;
- `R1RealizationMaterializer.append_segment(...)`;
- `R1RealizationMaterializer.finalize()`;
- the returned `R1MaterializedRealization` producer object.

The active object preallocates separate state, mask, and `coverage_written`
arrays. It accepts only contiguous, full-width, explicitly identified segments
and never fills an unwritten interval with zero.

## Verification results

Ten test groups passed.

### Round 13 segmented transport

The frozen five-index fixture was deliberately split into three intervals:

- `[0, 1)`;
- `[1, 3)`, with station columns reversed to test explicit-ID reordering;
- `[3, 5)`.

The finalized object passed through:

```text
materializer -> Round 17 hook -> Round 16 exporter -> production loader
```

All 1,550/1,550 state/mask cells were exact. Station IDs, source times, and
`dimensionless_qa_index` were exact. No complete trajectory was supplied in a
single append.

### Round 11 static semantic fixture

The T=1 representation retained exactly:

- 306 identified states;
- 4 missing states;
- 304 identified ones;
- 2 identified zeros.

The identified zeros remained RINGMILL (`306980`) and UNKNOWN309598 (`309598`).
The missing states remained RENO (`301479`), UNKNOWN303265 (`303265`), HALLDALE
(`304137`), and UNKNOWN305021 (`305021`). The downstream exporter/loader chain
preserved the same zero/missing distinction.

### Explicit completeness failures

Eight segment-coverage cases failed fast:

1. missing initial segment;
2. missing middle segment;
3. missing final segment at finalize;
4. overlap;
5. duplicate interval;
6. out-of-order interval;
7. zero-length interval;
8. interval exceeding T.

This verifies that producer silence cannot become a scientific zero.

### Station and schema failures

Ten station/schema cases failed fast, covering a missing station, unknown
station, duplicate station ID, mismatched state/mask station sets, mismatched
row counts, mismatched time identity, unsafe positional state input, unsafe
positional mask input, a wrong 310-ID set detected through the frozen-ID hash,
and fewer than 310 frozen IDs.

### Value and mask failures

Seven value/mask cases failed fast:

- identified NaN;
- identified infinity;
- identified negative value;
- identified value above one;
- identified ambiguous string;
- masked nonzero value;
- nonboolean mask.

A separate positive fixture retained identified zero, identified one,
identified `0.375`, and unidentified zero as four distinct state/mask cases.

### Finalization and boundaries

- Append after finalize failed.
- Repeated finalize failed.
- Aggregate and incomplete realization provenance failed.
- Duplicate/nonmonotonic/missing source time failed.
- AST inspection confirmed the dependency boundary.
- The main-model SHA-256 stayed
  `b9efcd0487b1e9f115876a3c6f2b45dc342e20c7a516cd491846d4f9557654df`.
- `git diff 1bad6deb90315ea9e034bdda468e2587a0052587 -- C257H_Project_Main.py`
  returned no difference.

Final test output:

```text
Ran 10 tests in 0.572s
OK
PASS_PRODUCER_MATERIALIZATION_UNIT_VERIFIED
round13_cells = 1550
round11_identified = 306
round11_missing = 4
segment_completeness_cases = 8
station_schema_cases = 10
value_mask_cases = 7
scientific_runs = 0
```

## Direct answers

1. **Does the materializer compute scientific state?** No. It only validates
   and copies already-computed state/mask segments.
2. **Is the main model unchanged?** Yes, byte hash and Git diff both confirm
   the Round 17 version remains unchanged.
3. **Is the default disabled?** Yes. The factory returns `None` before input
   validation or allocation.
4. **Does incomplete segment coverage always fail?** Yes. Ordering failures
   fail at append; missing final coverage fails at finalize.
5. **Is there implicit zero fill?** No. `coverage_written` independently tracks
   every cell, and finalize rejects unwritten cells.
6. **Are zero and missing lossless?** Yes, through materializer, hook, exporter,
   and production loader.
7. **Did Round 11 retain 306 identified and 4 missing?** Yes, including exact
   station identities for two zeros and four missing states.
8. **Did Round 13 restore all 1,550 cells exactly?** Yes.
9. **Did malformed segment/schema/value cases fail fast?** Yes, all tested
   cases failed before final output.
10. **Can finalized state mutate?** No. Append and repeated finalize fail after
    the first finalize.
11. **May the next round design producer instrumentation?** Yes, limited to
    disabled, retained/synthetic fixture work.
12. **What remains prohibited?** Real source-gate or topology execution,
    damage, fragility, repair, dispatch, crews, routing, scheduling, GA, MC,
    32x4, 29-crews, 114-crews, and any real recovery trajectory or export.

## File hashes

| Object | SHA-256 |
|---|---|
| Round 11 fixture | `a60ec21fd8cc5b940eca86c20ae28d09cf015db83b4dc3985efb044edf59c384` |
| Round 13 fixture | `b899563515672690106e6886f6db310efab315bedf1866e2d6a205d816a2ddc6` |
| Round 16 exporter | `79ddac0980e4553b15d881471a414c8215fdd71ce49f5065fab0085bda0dc59b` |
| Round 17 hook | `e3eb5228be0b17580f7313cac7d234f326f7e00c2a7fd027ba853ef6d01f4bf2` |
| Production loader | `d32189231cceb0a13833fd608a08ca823d10dab07c8a8f92e2db9d97d5517514` |
| Unchanged main model | `b9efcd0487b1e9f115876a3c6f2b45dc342e20c7a516cd491846d4f9557654df` |
| Materializer | `ce95b971cadac9bc6f07d24832fcd8d817904395abfa2b447b86c4f3774da77d` |
| Test driver | `5d798d711868ca5686e742196e22399fdac006f524adac3d37f73415b28d9258` |
