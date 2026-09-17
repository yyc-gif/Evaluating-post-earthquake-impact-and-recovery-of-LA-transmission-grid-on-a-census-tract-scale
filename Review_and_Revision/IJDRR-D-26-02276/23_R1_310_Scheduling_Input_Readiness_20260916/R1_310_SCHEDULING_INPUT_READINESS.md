# R1-310 Scheduling Input Readiness

**Decision: PASS — SCHEDULING INPUTS READY; ENGINE PENDING**

- `LEGACY_STAGE4_STAGE5_SCHEDULER_APPROVED_FOR_REVISED_PILOT = NO`
- `PRIMARY_SCHEDULING_ASSET_DOMAIN = D302`
- `INPUT_READY = YES`
- `EXECUTION_ENGINE_READY = NO`
- `FUTURE_FIRST_PILOT_CREW_SCENARIO = C57_REFERENCE`
- `32x4_AUTHORIZED = NO`

No damage realization, repair-duration realization, source gate, recovery, dispatch,
schedule, GA optimization, or 32×4 run was executed. This round contains static
joins, directed-road routing, deterministic roster scaling, formulas, and unit
fixtures only.

## Legacy Stage 4/5 audit

The existing implementation remains valid for its old contract but is not approved
for the revised pilot. `select_repair_tasks` selects by mean repair time ≥1 h;
the revised realization rule is `DS>0`. `simulate_rule_schedule` uses representative
durations and then drives a continuous repair CDF; the revision uses one paired
positive realized on-site action duration and restores raw functionality at task
completion. `order_substations` and Stage 5 derive priorities from legacy mapping/W,
whereas the primary revision requires Architecture B W1. `load_travel_matrices`
permits Haversine/virtual-velocity generation, and schedule lookups can fall back to
24 h; both are prohibited here.

## Scheduling information set

Known at scheduling start: DS, the `DS>0` task set, frozen ex-ante policy order or
objective, strict road times, and crew origins. Hidden realized durations, future
service outcomes, future T80/AUC, and other policy results cannot select priority.
DS, stored realized durations, travel matrices, and crew roster are paired across
all strategies within a realization.

## Task-capable domain

| Domain | Stations | Sources | A/B targets | Road-ready | Defined state? |
|---|---:|---:|---:|---:|---|
| D310 | 310 | 21 | 117 | 309 | no |
| D306 | 306 | 21 | 117 | 305 | yes |
| D304 | 304 | 21 | 117 | 303 | yes |
| D302 | 302 | 20 | 117 | 302 | yes |

D302 is frozen because it is the main modeled component and contains all
117 unique Architecture B Class A/B upstream targets. D310 contains
four unresolved state-domain records; D306 adds two identified source-less isolates;
D304 also includes component 2 (`303547`, `307683`), which has a reference source
but no strict-SCE A/B attachment target. Scheduling those eight records cannot alter
the primary service proxy and would consume resources outside its modeled outcome.
Their R1 inventory membership remains unchanged.

Owner composition and excluded IDs are:

| Domain | LADWP | SCE | Other | Unknown | IDs excluded from D310 |
|---|---:|---:|---:|---:|---|
| D310 | 35 | 234 | 17 | 24 | none |
| D306 | 34 | 233 | 17 | 22 | 301479, 303265, 304137, 305021 |
| D304 | 34 | 232 | 16 | 22 | D306 exclusions plus 306980, 309598 |
| D302 | 34 | 230 | 16 | 22 | D304 exclusions plus 303547, 307683 |

Eligibility is `DS>0` within D302; DS0 consumes no crew. Every policy has a full
302-ID sequence, and a realization removes DS0 without re-ranking.

## Duration and completion contract

- DS1: Normal(1, 0.5) conditioned on T>0
- DS2: Normal(6, 3) conditioned on T>0
- DS3: Normal(12, 4) conditioned on T>0
- DS4: Normal(36, 12) conditioned on T>0

These are scenario-based on-site restoration action durations. They are not
empirical, calibrated, utility-recommended, or actual LA repair times, and they
exclude road travel, mobilization, material wait, and permanent reconstruction.
Completion is arrival plus realized duration. Crew release and raw-functionality
restoration to 1 occur at completion; before completion raw functionality remains
the DS residual. Source/component gating remains separate. A small unit fixture
confirmed repeatability by realization ID, shared stored durations across strategies,
no DS0 duration, and positive task durations. It is not a simulation draw.

## Road access and strict travel

D302 is 302/302 road-ready. Four in-domain flags use one uniform representation:
projection to an existing directed road edge plus an explicit centroid-to-road
connector at the design speed 15 km/h. Existing direction and travel time are
preserved; no road edge is invented. SHELLWATT and HAYNES are primarily road-vertex
spacing cases. HILGEN uses a transparent access proxy to Crossroads Parkway South.
UNKNOWN302923/Chevron Central uses a transparent access proxy to East El Segundo
Boulevard. Neither proxy claims a mapped internal facility road.

Official access evidence retained in the QA ledger: [LACSD Puente Hills MRF](https://www.lacsd.org/services/solid-waste/facilities/puente-hills-materials-recovery-facility-mrf), [LACSD landfill-gas facility](https://www.lacsd.org/services/solid-waste/energy-recovery-and-fueling-facilities/landfill-gas-to-energy-facilities/puente-hills-landfill-gas-to-energy-facility), and [California Water Boards Chevron El Segundo permit](https://www.waterboards.ca.gov/losangeles/board_decisions/tentative_orders/individual/npdes/Chevron_El_Segundo/CA0000337_Revised_Tentative_Requirements.pdf).

NAVY MOLE remains physically unresolved and receives no connector. It is outside
D302, so its scheduling decision is closed by domain exclusion. WESTHILL retains
the Round 6 same-SCC decision. All other tasks use the frozen Round 6 same-SCC node
plus an explicit connector; the 11 depot locations remain origin proxies.

- Base→Task: 11×302, all finite, SHA-256 `16177e57cd7e77ea2075e347318c3b7698937af6b0b7dc702f18b9da65662690`
- Task→Task: 302×302, all finite, exact zero diagonal, SHA-256 `68c03537853bad92544f13688ade89247e135e829b989c71c96be2f8ef45a6de`

No Haversine-generated cell, 24 h sentinel, NaN, infinity, or undirected substitution
occurs. The directed task matrix is not required to be symmetric.

## Crew scenarios

C57 is the retained `C57_substation_ratio_main` / `C57_yard_allocation_no_deletion_tie_coherent_zero_low` allocation proxy. It is a pooled regional restoration-resource scenario, not verified post-earthquake
staffing. It has 57 crews at 11 origin proxies (47 LADWP, 10 SCE). There is no
utility-specific task restriction. The 11 active depot proxies are suitable for D302 routing because every depot-to-task OD is finite; this does not validate their staffing counts or physical emergency availability. C29 and C114 are definitions only: scale each
frozen C57 integer depot count by target/57, floor, assign remainders by descending
fraction and yard-ID tie. Totals are exactly 29/57/114. Only C57 is designated for
a future first pilot, and no crew was dispatched.

## Architecture B priorities

Population uses `sum Population_r*W1_rj`; hospital uses one binary indicator per
strict-SCE hospital tract; SOVI uses `Population*(SOVI_SCORE+shift)`. Service-node
mass is aggregated only through Class A/B selected upstream R1 IDs. Class C stays
unassigned and is never redistributed or renormalized. `SOVI_SCORE` is NRI-derived,
not CDC SVI. Missing SOVI count is 0, minimum is
1.809999943, and shift is 0. The strict domain contains
47 hospital tracts and 53 retained hospital
records; multiple records do not amplify a tract indicator.

Unassigned Class C mass:

- population candidate mass: 145897.583333300281
- hospital candidate mass: 0.666666666666
- vulnerability-weighted candidate mass: 9848051.565813224763

Components are min-max normalized over D302 with a deterministic zero vector for a
constant component. Hospital-first sorts hospital score descending, population score
descending, then R1 ID ascending. All 302 IDs occur once; sequence SHA-256
`0fe713a254af2a7922e7a246e272368caedf5ec1b4e1fb65e1aef47a066973ab`.

## GA readiness without a GA run

Balanced, HospFirst, and Efficiency retain the existing numeric objective weights
only as policy-design/optimization coefficients; they are not empirical or calibrated.
`W_SVI=1` has the same status. `NETWORK_IMPORTANCE_TERM = DROP`: eta=.20 and the
role/voltage/line 0.70/0.20/0.10 blend are a separate subjective construct with weak
provenance. Removing it keeps the revision interpretable as Architecture B service
priority plus makespan; no outcome motivated this choice.

A future chromosome is a 302-ID full permutation. DS0 is filtered without re-ranking.
If makespan needs duration, only `E[T_i]=sum_d P(DS_i=d)E[T_d|T_d>0]` may enter;
realized duration is hidden. The formula and conditioned means are frozen; the numeric
expected-workload vector waits for an explicitly selected pilot hazard. All three
policy input definitions and priority components are finite and READY. No DEAP run or
GA sequence was generated.

## Decision and direct answers

1. Final task domain: **D302**, 302 stations, for the primary-component and service-target reasons above.
2. Future task rule: **`DS>0`**; DS0 consumes no crew.
3. Duration: positive-conditioned reference scenario, labeled uncalibrated on-site action duration.
4. Crew release and raw restoration both occur at task completion.
5. Road flags: four in-domain proxies resolved; NAVY MOLE remains physically unresolved outside D302. No final-domain access is unresolved.
6. Haversine/24 h fallback: **none**.
7. Matrices: complete directed 11×302 and 302×302.
8. C57: scenario resource budget, not actual staffing.
9. C29/C114: deterministic proportional largest-remainder scaling with yard-ID tie.
10. Population priority: strict-SCE population × W1, then A/B aggregation and D302 normalization.
11. Hospital priority: binary hospital tract × W1, then A/B aggregation; no record-count amplification.
12. SOVI priority: population × shifted NRI SOVI_SCORE × W1, then A/B aggregation.
13. Class C mass: unassigned; never redistributed.
14. Hospital-first sequence: complete 302-ID permutation.
15. GA dimension: **302**.
16. GA information set: ex-ante full sequence, then realization DS0 filtering.
17. Network importance: **DROP** for provenance and interpretability.
18. GA policy inputs: READY as definitions/components; no optimization or sequence run.
19. `INPUT_READY = YES`.
20. `EXECUTION_ENGINE_READY = NO` because current scheduler still has legacy duration/CDF semantics.
21. Next work: implement and fixture-test a revised event-based scheduler production unit.
22. 32×4 allowed: **NO**.

## Integrity

- Parent commit: `1459f86b91bcefc0140b319db89ba452ff01f762`
- Ordered R1 ID hash: `d29ba6b34f362c8c00c3fdd4bc5f8b518f3022022fc68c8e1444a4635ab9e3f5`
- Reference source hash: `c104dbbb15c710a4e72ca04992be6eb7b8dffd5f655c67b3e5ca4dfca827e7b3`
- Road graph SHA-256: `6bdde162da4945b4710f5f9708c9f07e6d1b18488ba23b79c2de725c858d251b`
- Main model SHA-256: `90743cde45fe14de9e113ad39111c2a8507dd90099002a1eae06832aba208145`
- No production scientific code was modified.
