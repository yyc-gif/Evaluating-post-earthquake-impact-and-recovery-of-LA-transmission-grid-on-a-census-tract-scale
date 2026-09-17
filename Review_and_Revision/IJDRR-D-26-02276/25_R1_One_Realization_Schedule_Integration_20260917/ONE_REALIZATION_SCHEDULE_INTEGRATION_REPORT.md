# One-Realization Schedule Integration Report

## Decision

**FAIL — REVISED ONE-REALIZATION END-TO-END INTEGRATION NOT VERIFIED**

- `EXECUTION_ENGINE_PRODUCTION_INTEGRATED = NO`
- `SCIENTIFIC_EXECUTIONS = 1`
- `GA_EXECUTIONS = 0`
- `MONTE_CARLO_EXECUTIONS = 0`
- `LEGACY_STAGE4_STAGE5_EXECUTIONS = 0`
- `PAPER_RECOVERY_RESULTS_CREATED = NO`

The only authorized deterministic D302 realization was executed once. The run
stopped during post-execution QA and was not repeated. No parameter, task, source,
graph, travel, priority, or service mapping was changed in response to the failure.

## Pre-scientific import failure

An earlier command failed before the scheduler, gate, or any scientific-state
calculation because the isolated runner loader did not expose the repository root
while importing the frozen main module (`ModuleNotFoundError: strategy_names`). It
produced no manifest or scientific output. The runner loader was corrected to
temporarily expose only the imported file's parent directory. Frozen scientific code
and inputs were not changed.

## Frozen realization actually executed

The input manifest was written before execution and records:

- full R1 domain: 310 records
- primary scheduling domain: D302
- test tasks: 80
- damage counts: DS0=222 and DS1=DS2=DS3=DS4=20
- crews: frozen C57 pooled roster
- ordering: frozen Round 23 Hospital-first 302-ID ex-ante sequence
- task selection: first 80 IDs after sorting
  `SHA256("R25_INTEGRATION|" + R1_ID)`
- duration fixture: open-unit hash mapping plus positive-conditioned Normal inverse CDF
- graph: frozen 310-node / 1040-edge checkpoint
- sources: frozen 21-node reference source-availability scenario
- functionality threshold: 0.5
- Architecture B: frozen 196 service nodes, attachment ledger, W1, and 817 tracts

Manifest SHA-256:
`a56607dfc43af6460b15446e8c522156c2d2309e06a2ee639d725b15e5ca10b1`

## What completed before the QA failure

The production calls completed in this order:

1. Round 24 event-based scheduler;
2. completion-event raw-functionality evaluator;
3. frozen source/component gate;
4. Round 16 exporter;
5. Round 14 Architecture B production service interface.

The following scheduler assertions passed before the failure:

- exactly 80 unique tasks;
- filtered queue exactly matched Hospital-first with DS0 removed;
- all 80 realized durations were preserved exactly;
- all 80 completion times equaled arrival plus duration exactly;
- 57 Base-to-Task legs and 23 Task-to-Task legs;
- all 57 crews used;
- each crew's next availability equaled its preceding task completion.

These observations establish that the scheduler path executed, but they do not close
the end-to-end gate because the raw/network/service/tract invariants later in the QA
sequence were not reached.

## Failure

The schedule event table was merged with the deterministic fixture ledger for QA.
Both tables contain `damage_state`, so pandas produced `damage_state_x` and
`damage_state_y`. The completion-transition loop then attempted to access the
nonexistent field `damage_state`:

```text
AttributeError: 'Pandas' object has no attribute 'damage_state'.
Did you mean: 'damage_state_x'?
```

Failure location:
`R1_REVISED_REALIZATION_RUNNER.py`, completion-transition QA following the single
scientific execution.

This is a runner QA field-name defect. It is not evidence of a scientific-equation,
scheduler, source-gate, or Architecture B mismatch. Because the run had already
executed the scientific chain, the authorization prohibited patching and rerunning it
within this round.

## Artifacts intentionally absent

`ONE_REALIZATION_SCHEDULE_EVENTS.csv` and
`ONE_REALIZATION_END_TO_END_EVIDENCE.npz` were not written: persistence occurs only
after all end-to-end invariants pass. No partial schedule or unverified service/tract
trajectory is presented as a successful result.

## Integrity

- `C257H_Project_Main.py` SHA-256 remains
  `90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145`.
- Frozen graph, D302, Hospital-first priorities, travel matrices, C57 roster,
  scheduler, exporter, service interface, attachment ledger, W1, and tract metadata
  hashes matched the input manifest at execution start.
- Main legacy Stage 4/5 were not called.
- No GA, Monte Carlo, T50/T80/T90/AUC, policy comparison, hospital outcome, SVI,
  population burden, or equity analysis was executed.

## Required next step

Continue STOP. Do not begin GA reproducibility or the revised paired pilot. A separately
authorized failure-repair run must first correct the QA merge-field handling and repeat
this same frozen deterministic realization without changing scientific inputs. Only a
fully verified PASS can set `EXECUTION_ENGINE_PRODUCTION_INTEGRATED = YES`.
