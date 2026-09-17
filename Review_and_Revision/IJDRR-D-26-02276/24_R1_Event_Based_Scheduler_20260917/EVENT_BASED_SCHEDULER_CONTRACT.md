# Revised R1 Event-Based Scheduler Contract

## Status

- `SCHEMA = R1_EVENT_BASED_SCHEDULER_V1`
- `PRIMARY_PRODUCTION_DOMAIN = D302` when later integrated
- `EXECUTION_ENGINE_UNIT_READY = YES`
- `EXECUTION_ENGINE_PRODUCTION_INTEGRATED = NO`
- `32x4_AUTHORIZED = NO`

This module is an independent, deterministic dispatch-logistics engine. It has not
been connected to `C257H_Project_Main.py`, Stage 4, Stage 5, the source gate, the
service layer, or any recovery calculation.

## Public interface

```python
execute_event_based_schedule(
    *,
    domain_ids,
    full_priority_sequence,
    damage_states,
    realized_duration_hr,
    base_to_task_hr,
    task_to_task_hr,
    crew_roster,
) -> R1EventScheduleResult
```

The result contains only:

- `task_events`
- `task_start_hr`
- `task_completion_hr`
- `task_crew_index`
- `task_travel_hr`
- `filtered_task_sequence`
- `crew_final_available_hr`

It contains no network, source, service, tract, functionality, or recovery state.

## Explicit identity contract

`domain_ids` is a nonempty, stable sequence of unique, nonempty string IDs. Every
station-indexed input must have an explicit station-ID index and exactly the same
membership. Input row order may differ because safe reindexing uses explicit IDs;
positional anonymous arrays are rejected. No name, coordinate, nearest-neighbor, or
automatic ID matching is permitted.

`full_priority_sequence` is a full permutation of the domain. The scheduler never
sorts or re-ranks it. The realization queue is exactly:

```text
full_priority_sequence with DS0 IDs removed
```

Full-domain priority rank is preserved in every event record.

## Damage and duration contract

`damage_states` covers the full domain and contains integer values in 0–4:

- DS0: no task and duration must equal 0
- DS1–DS4: task and duration must be finite and strictly positive

The scheduler does not calculate damage, sample duration, condition a distribution,
clip a value, or substitute a mean. Duration may affect task completion and which
crew is released first. It cannot affect queue membership beyond the DS rule, queue
order, or next-task identity.

## Crew contract

The roster contains `crew_index`, `crew_id`, and `origin_key`. Crew indices are the
unique contiguous integers 0 through N−1; crew IDs are unique strings; every origin
exists in the Base→Task matrix. All crews are pooled and available at t=0. The event
calendar key is `(available_time, crew_index)`, so an exact time tie selects the
lower crew index. No utility eligibility restriction is applied.

## Strict travel contract

Base→Task has explicit origin rows and every domain ID as columns. Task→Task has the
domain as both row and column IDs. Both matrices must be numeric, finite, and
nonnegative; Task→Task has an exact zero diagonal. Directionality is preserved by
looking up `task_to_task[previous_task, next_task]`. Symmetry is neither required nor
enforced.

There is no Haversine, geodesic, virtual speed, nearest, mean, or 24 h fallback.
Missing or invalid lookup inputs fail before dispatch.

## Event algorithm

1. Remove DS0 IDs from the frozen full priority sequence without re-ranking.
2. Initialize one calendar event `(0, crew_index, previous_task=None)` per crew.
3. For the next task in the filtered static queue, pop the earliest crew event.
4. Use Base→Task travel for a crew's first task; otherwise use directed
   Task→Task travel from its previous task.
5. Set `arrival = available + travel` and
   `completion = arrival + realized_duration`.
6. Record the event and return the crew at its completion time.
7. Continue until the static queue is empty.

The scientific task segment is therefore a fixed queue; duration influences the
event calendar, never priority.

## Output and missing semantics

Each scheduled task appears once in `task_events`, with a continuous dispatch rank,
its full-domain priority rank, crew identity, previous task, travel, arrival,
duration, and completion. A DS0 station has missing start, completion, crew, and
travel fields. It is not represented by a zero-time pseudo-task.

An all-DS0 input is valid: events and filtered sequence are empty and every crew
remains available at zero. If tasks are fewer than crews, only the required lowest
tied crew indices are dispatched; no dummy task is created.

## Side-effect and dependency boundary

The module is pure and in-memory. It copies validated caller inputs, returns a new
result, writes no files, and uses no random generator. It imports only standard
library modules plus NumPy and pandas. It does not import the main model, NetworkX,
geopy, SciPy, source/damage/fragility/repair logic, the service layer, DEAP/GA,
travel generation, or plotting.

## Next gate

This unit may next be used only in a separately authorized one-realization schedule
integration with D302, C57, one deterministic test-only DS vector, one stored
positive duration vector, the frozen Hospital-first sequence, and the strict travel
matrices. That integration must then verify completion-to-raw-functionality event
semantics. This contract does not authorize GA, Monte Carlo, or 32×4.
