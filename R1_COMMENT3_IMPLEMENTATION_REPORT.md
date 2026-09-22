# Reviewer 1 Comment 3 — Realization-Specific Scheduling

## July behavior

Stage 1 retained station-by-realization damage states and repair-time draws, but Stage 3 averaged durations. Stage 4/5 selected tasks with `select_repair_tasks(mean_repair_times, ...)`, booked crews with representative durations, and shifted a separate continuous repair CDF from scheduled arrival. Realization-specific task membership and duration uncertainty therefore did not pass through the crew queue, and crew completion did not define functionality restoration.

## Revised behavior

`r1_realization_scheduling.py` adds the revised path while retaining July functions for reproduction:

- `realization_inputs_from_stage3()` extracts one aligned `DS_i,r` and matching `T_i,r` without averaging.
- `task_i,r = (DS_i,r > 0)`: DS0 is removed; DS1–DS4 are tasks.
- `execute_realization_schedule()` uses `completion = crew_available + directed travel + T_i,r`; the crew is released at completion.
- `evaluate_completion_step_functionality()` uses one clock: DS residual functionality for `t < completion`, and 1 at `t >= completion`.
- `simulate_paired_realization_strategies()` fixes DS, duration, travel and crews across strategies; only the priority permutation changes.
- The unchanged July source gate is supplied after raw functionality. Its topology, threshold and source-component logic were not edited.

Stage 1 repair draws now use `draw_positive_normal()` with the existing DS-specific Normal parameters conditioned on `T>0`. DS0 remains zero; no repair parameter changed.

## Definitions

- **Task:** station with realized DS>0.
- **Duration:** one positive DS-specific repair-action duration shared by every strategy in that realization.
- **Schedule:** static priority sequence filtered to realized tasks; earliest-free crew; directed travel; completion releases the crew.
- **Recovery clock:** that same completion event restores raw functionality. The revised path has no second independent CDF clock.
- **Pairing:** identical DS, duration, travel and crew inputs; only order differs.

## Changed files/functions

- `r1_realization_scheduling.py`: realization extraction, event scheduling, completion-step functionality and paired strategy evaluation.
- `C257H_Project_Main.py::damage_to_functionality_and_repair`: positive-conditioned draws using the existing parameters.
- `t.py`: fixed synthetic unit verification.

## Verification

The four-station fixture verifies DS0 exclusion, DS>0 inclusion, exact realized-duration use, completion/release equations, duration-sensitive crew release without priority re-ranking, paired physical inputs, completion-step restoration and post-restoration gate invocation. Fixed-seed positive draws repeat exactly.

## Untouched

No mapping, topology/domain, source-gate equation, crew scenario, travel generation, priority rule, GA, tract propagation, typology, manuscript, figure or retained result changed. No full pipeline or publication experiment ran.
