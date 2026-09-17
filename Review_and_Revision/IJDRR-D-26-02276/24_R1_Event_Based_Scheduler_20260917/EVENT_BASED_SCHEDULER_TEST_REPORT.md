# Event-Based Scheduler Unit Test Report

## Decision

**PASS — EVENT-BASED SCHEDULER UNIT VERIFIED**

- `EXECUTION_ENGINE_UNIT_READY = YES`
- `EXECUTION_ENGINE_PRODUCTION_INTEGRATED = NO`
- `ROUND23_REAL_D302_SCHEDULE_EXECUTIONS = 0`
- `SOURCE_GATE_RECOVERY_GA_EXECUTIONS = 0`
- `32x4_AUTHORIZED = NO`

The standalone scheduler was executed only on synthetic fixtures. Round 23 D302,
travel, roster, and Hospital-first artifacts were read only for identity, hash, shape,
finite-value, diagonal, and roster-total validation. They were never supplied with a
damage vector or passed to the scheduler.

## Production unit

`r1_event_based_scheduler.py` exports:

- `execute_event_based_schedule(...)`
- `R1EventScheduleResult`

The engine validates and copies explicit inputs, filters DS0 from the caller's full
priority sequence, and dispatches the next pending task to the earliest released
crew. Exact release-time ties are resolved by ascending `crew_index`. Initial travel
uses Base→Task; subsequent travel uses the directed
`Task→Task[previous_task, next_task]` cell. Arrival is crew availability plus travel,
and completion/release is arrival plus the supplied realized duration.

It does not generate damage or duration, calculate priority, mutate an input, write a
file, apply a source gate, create functionality state, evaluate recovery, propagate
service/tract state, or import GA logic.

## Synthetic fixture results

### A — independent hand oracle

The six-station, two-crew fixture has one DS0 station and five tasks. The independent
CSV oracle fixes every task ID, full and dispatch rank, crew, previous task, travel,
arrival, duration, and completion before the production unit is called.

All five events matched exactly. Canonical production event-table SHA-256:

`c5879eef66c98f80557c5b8b1e924da1bfada84cd70cf6c6c6e3e553019f3377`

`EVENT_SEMANTICS_MATCH_PAIRED_PILOT = YES` for static-list filtering,
earliest-release crew choice, base/previous-task travel, completion, and crew release.
No old paired-pilot driver was imported or executed.

### B–F and edge cases

- Crew tie: crews 0 and 1 tied at t=0; a later exact release tie also selected crew 0.
- Direction: the fixture has A→B=1 h and B→A=9 h; the engine used A→B=1 h.
- DS0 filtering: full order A,B,C,D with B,D=DS0 produced A,C, preserving full ranks 1,3.
- Duration foresight: changing supplied durations changed crew releases/assignments but not the filtered queue or dispatch task order.
- Single crew: each next arrival equaled prior completion plus directed previous→next travel.
- Empty task set: returned empty events, missing station assignments/times, and all crews available at zero.
- Tasks fewer than crews: two tasks used crews 0 and 1; three remaining crews stayed at zero; no dummy task was created.

DS0 start, completion, crew, and travel outputs are semantic missing values, not zeros.

## Fail-fast and determinism QA

Twenty-two malformed cases were rejected: incomplete/duplicate/unknown
priority; missing, invalid, or noninteger DS; DS0 nonzero duration; nonpositive or
nonfinite damaged duration; missing/duplicate crew identity; unknown origin;
incomplete, nonfinite, negative, or nonzero-diagonal travel; and domain mismatch.
Anonymous positional station inputs were also rejected.

Two identical executions produced exact-equal event tables, start/completion series,
crew assignments, travel series, and final crew availability. Deep equality checks
showed that priority, DS, duration, matrices, and roster inputs remained unchanged.

Final test command:

```text
python -m pytest -q -p no:cacheprovider test_r1_event_based_scheduler.py
34 passed
```

## Round 23 read-only readiness regression

- D302: 302 unique IDs.
- Hospital-first: 302 unique IDs with exact D302 membership.
- Base→Task: 11×302 numeric finite cells.
- Task→Task: 302×302 numeric finite cells with exact zero diagonal.
- C29/C57/C114: exact totals 29/57/114; deterministic expanded crew indices can be formed and every origin exists in Base→Task.
- Frozen input hashes matched the Round 23 values.

No real or random DS vector was created, and `execute_event_based_schedule` was not
called with these artifacts.

## Dependency and code-boundary audit

AST inspection found only `dataclasses`, `heapq`, `typing`, NumPy, and pandas imports.
The module has no main-model, NetworkX, geopy, SciPy, random, damage, source,
service-layer, DEAP/GA, travel-generation, plotting, or file-output dependency.

`C257H_Project_Main.py` remains unchanged with SHA-256:

`90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145`

## Artifact hashes

- production module: `8096fa7ad72d5f7a5cb9c6f186d65adef2ab8f7fc336938f0dba396ed31ee43f`
- test module: `cae9742edccde14f4d76225f28e9f217139157c55c47e0e6387ac6c1df6670c3`
- independent oracle: `5a2ffe0f131000d5429fd20bcc826b1bb2530203ed05db99395e6a94a29e765b`
- contract: `c23495db31dc017612265e630731c4b3a9221471b18967b6e81838eb10ac6bce`

## Direct answers

1. **Does the scheduler generate damage or duration?** No. Both are authoritative caller inputs.
2. **Is the task rule strictly DS>0?** Yes.
3. **Does DS0 enter the schedule?** No; its scheduling outputs remain missing.
4. **Is priority only full-sequence DS0 filtering?** Yes; there is no re-ranking.
5. **Does realized duration affect only completion/release?** Yes. It can change which crew frees next but cannot change pending task order.
6. **Crew tie-break:** earliest available time, then ascending `crew_index`.
7. **Directed travel correct?** Yes; previous→next lookup was independently tested against a 1 h versus 9 h asymmetric pair.
8. **Any fallback?** No.
9. **Synthetic oracle exact?** Yes, all five events and every event field.
10. **Did duration changes preserve filtered priority?** Yes, exactly.
11. **Were Round 23 D302/travel/rosters schema-only?** Yes; no schedule was executed with them.
12. **Main model modified?** No; its frozen SHA matches.
13. **Any source gate, recovery, service, tract, or GA execution?** No.
14. **`EXECUTION_ENGINE_UNIT_READY`:** YES.
15. **`EXECUTION_ENGINE_PRODUCTION_INTEGRATED`:** NO.
16. **32×4 allowed?** NO.

## Next gate

The only next permissible step is a separately authorized
`ONE-REALIZATION SCHEDULE INTEGRATION` using D302, C57, one deterministic test-only
DS vector, one deterministic stored positive duration vector, the frozen
Hospital-first sequence, and frozen strict travel matrices. That gate must verify
task-completion to raw-functionality event semantics. It does not include GA,
Monte Carlo, or 32×4.
