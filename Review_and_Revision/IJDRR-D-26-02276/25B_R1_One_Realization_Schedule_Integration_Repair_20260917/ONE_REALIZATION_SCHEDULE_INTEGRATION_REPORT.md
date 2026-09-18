# One-Realization Schedule Integration Report

## Decision

**PASS — REVISED ONE-REALIZATION END-TO-END INTEGRATION VERIFIED**

- `EXECUTION_ENGINE_PRODUCTION_INTEGRATED = YES`
- `ROUND25B_SCIENTIFIC_EXECUTIONS = 1`
- `CUMULATIVE_R25_AND_R25B_SCIENTIFIC_EXECUTIONS = 2`
- `DAMAGE_OR_DURATION_RANDOM_DRAWS = 0`
- `GA_MC_KPI_EXECUTIONS = 0`
- `MAIN_LEGACY_STAGE4_STAGE5_EXECUTIONS = 0`

The original Round 25 FAIL remains unchanged at commit
`bebbae266c659998c5322d91f0f34dc795f2699f`. Round 25B changed only the
post-execution merge QA: scheduler and fixture damage/duration fields receive explicit
suffixes, are compared independently, and are canonicalized only after equality.
The scientific kernel and every frozen scientific input are unchanged.

This is a test-only deterministic architecture integration. It is not a paper result
and is not interpreted as a recovery, policy, hospital, population, or equity finding.

## Frozen inputs and mechanical fixture

The run used D302, the frozen C57 pooled roster, the Round 23 Hospital-first full
sequence, strict directed 11×302 and 302×302 travel matrices, the frozen 310-node /
1040-edge graph, and the 21-node reference source-availability scenario.

The 80 task IDs were selected only by ascending
`SHA256("R25_INTEGRATION|" + R1_ID)`. Damage states cycle DS1–DS4 by hash rank,
giving 20 tasks per state and 222 DS0 assets. Each task duration is the positive-
conditioned Normal inverse CDF of the open-unit value derived from
`SHA256("R25_DURATION|" + R1_ID)`. Repeated fixture construction was exact. The
complete vectors and all 80 hash records are frozen in the manifest/evidence.

- DS vector SHA-256: `ee1298c321f3e0ab9152ec4889008b5975cec137a4c41e30a473002c1c82620f`
- duration vector SHA-256: `2e21c1dcb51035517ddde4d8d7b5d2dca53f80ad612c7ba9a257de794a3b6f4e`
- failure-repair manifest SHA-256: `cf9f7efaa3dff1b8aefbf9c7beb8ae562e9030803d2ba5d0609b605c21b85f73`
- parent failed manifest SHA-256: `a56607dfc43af6460b15446e8c522156c2d2309e06a2ee639d725b15e5ca10b1`
- exact scientific-input equality with Round 25: PASS

## Actual event schedule

- scheduled tasks: 80, each exactly once
- crews available: 57; crews used: 57
- Base→Task legs: 57
- Task→Task legs: 23
- filtered order: exact Hospital-first full sequence with DS0 removed
- damage-state preservation: 80/80 exact
- duration preservation: 80/80 exact
- completion equation: 80/80 exact `arrival + duration`
- crew release: every next crew availability equals its previous completion
- integration-only makespan: 57.747620263779 h

The makespan is retained only as dispatch QA and has no policy interpretation.

## Raw functionality and source/component gate

The event grid contains t=0 plus every unique completion time; the final horizon is
the maximum completion. No dense 0.05 h grid was generated. All 80 tasks retained
their DS residual at the preceding event and changed to raw=1 at their exact
completion event. Crew release, task completion, and raw restoration therefore share
the same event time for 80/80 tasks.

The frozen source/component gate was executed over every event using threshold 0.5
and the unchanged 21-node reference scenario. It is a source-connected upstream
availability proxy, not power flow.

- raw-increase completions: 80
- task completions with simultaneous own effective-state increase: 80
- raw restored while own effective state did not increase: 0
- identified R1 states varying over time: 88
- raw monotonicity: PASS
- effective-state monotonicity: PASS

An unchanged effective state at completion is valid when source connectivity still
does not support the asset.

The eight non-task R1 records retain frozen representation semantics: four unresolved
registrations (`301479`, `303265`, `304137`, `305021`) use inert numeric zero with
`state_identified=False`; `306980` and `309598` are identified, fixed raw=1 isolates
and remain source-unreachable; `303547` and `307683` are identified component-2
records fixed at raw=1 and are never repair tasks.

## Architecture B propagation

The complete effective trajectory passed through the frozen Round 16 exporter and
Round 14 production interface. No mapping logic was added.

- Class A/B service lookup mismatches: 0
- Class C missing-state violations: 0
- A/B service nodes varying over time: 55
- tract lower bounds varying over time: 456
- unresolved R1 states remain missing: PASS
- effective states within [0,1] where identified: PASS
- W1 file unchanged and never renormalized: PASS
- maximum `|resolved + unresolved - 1|`: 1.999955756559757e-12
- tract `lower <= upper`: PASS

Actual service/tract aggregate values and all recovery KPIs are deliberately omitted.

## Execution boundary and integrity

- revised scheduler calls: 1
- source/component gate calls: 1 trajectory call covering all event times
- exporter calls: 1
- Architecture B production-interface calls: 1
- GA calls: 0
- Monte Carlo calls: 0
- T50/T80/T90/AUC calculations: 0
- legacy Stage 4/5 calls: 0
- frozen input hash changes: 0
- `C257H_Project_Main.py` modified: NO

Artifacts:

- schedule events SHA-256: `2285c56527229bf8cf4c1c400e1ef8c57e56b05ff6ccde25d3cce93a1b6be534`
- end-to-end evidence SHA-256: `40faa9dba28d2322356aec5700e3ca0e3b441d82357a90acae8a9aeca4dc4269`
- runner SHA-256: `f8ee9c6a1f4217deb044f6eff194311b09e76af3cd6fbc6999ab4ab0fe747cfe`

## Conclusion

The revised execution architecture is connected end to end:

`D302 deterministic fixture → C57 event scheduler → completion-step raw state → frozen source gate → frozen exporter → Architecture B service states → 817 tract intervals`.

`EXECUTION_ENGINE_PRODUCTION_INTEGRATED = YES`.

Engineering QA stops here. The next work is **GA reproducibility + revised paired
pilot**: freeze the 2pc50 hazard, generate Architecture-B GA inputs, run multi-seed
convergence for the three GA policies, freeze their 302-ID ex-ante sequences, and
then execute the paired 32×4 C57 pilot with realization-level outputs.
