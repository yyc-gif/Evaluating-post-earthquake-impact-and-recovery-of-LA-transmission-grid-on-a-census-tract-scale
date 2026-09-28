# SCE Capacity Sensitivity Audit

## Data definition

The sensitivity uses only the 28 retained SCE stations with numeric 2026 `CUMULATIVE_DEMAND` and `FAC_LOAD_LIMIT` evidence, and only the 19 stations with one numeric provider facility row are assigned a station-level capacity ceiling. `CUMULATIVE_DEMAND` is used as D (MW) and `FAC_LOAD_LIMIT` as K (MW), following the SCE GNA/DUPR public definitions. Provider `FACILITY_LOADING` is QA only and never enters the sensitivity equation. The 19-row input is `SCE_CAPACITY_SUPPORTED_STATIONS.csv`.

The earlier 0.05-percentage-point loading-consistency screen is not used as an eligibility test. The three retained numeric facility rows above that QA discrepancy threshold are COLORADO 66/4.16 (+0.07704 pp), GANESHA 12/4.16 (-0.05190 pp), and REPETTO 66/4.16 (+0.06551 pp). All three belong to multi-facility retained stations. They are retained as QA discrepancies; their stations are excluded from station-level capacity assignment solely because a one-to-one station-facility interpretation is unavailable, not because of the discrepancy.

## 19-station coverage

- Supported retained stations: 19 of 92.
- Numeric-evidence retained SCE stations: 28; the remaining 9 are multi-facility.
- Tracts with positive weight on at least one supported station: 932 of 2315.
- Tracts with zero supported-station weight: 1383 of 2315.
- Population-weighted mean supported dependency mass: 0.253420.
- `W_r^sup` P25/P50/P75 across all 2315 tracts: 0.000000, 0.000000, 0.260429.
- Stations for which the capacity ceiling actually binds in at least one evaluated realization/case: 1 (306279 (OLINDA 66/12)).
- Tracts with a positive capacity-induced burden change in at least one evaluated case: 25.

These coverage statistics describe where public SCE evidence permits the perturbation. Unsupported stations remain at baseline service in the sensitivity; they are not classified as capacity-adequate.

## Formula

Production service is unchanged: `e_i(t)=f_i(t)F_i(t)C_i(t)`. For each of the 19 supported stations, `a_i=min(1,K_i/D_i)` and the sensitivity service is `e_i^cap(t)=min(e_i(t),a_i)`. Equivalently, `P_i^base(t)=D_i e_i(t)`, `P_i^served(t)=min(P_i^base(t),K_i)`, and `e_i^cap(t)=P_i^served(t)/D_i`. Unsupported stations use `e_i^cap(t)=e_i(t)`.

Tract service uses the frozen production weights: `A_r^cap(t)=sum_i w_ri e_i^cap(t)`. The capacity loss term is `L_capacity=e-e_cap`, and the existing formal exact-event evaluator is used for cumulative burden, population T80, and hospital burden with `L_total=1-e_cap`. No multiplicative derating and no new metric definition are used. Positive differences in the output tables mean capacity-bounded burden minus baseline burden.

## Why 9 multi-facility stations do not enter

The 28 numeric-evidence retained stations contain 37 numeric voltage-level facility rows: 19 stations have one facility row and 9 stations have two. SCE's public definitions provide facility-level demand and facility loading limits but no official rule for summing, averaging, minimizing, maximizing, or otherwise aggregating multiple facility rows into one retained-station capacity. The 9 multi-facility stations therefore receive no station-level capacity factor in this sensitivity.

## Frozen inputs

Batch A is the four hazards (`Northridge`, `SanFernando`, `LongBeach`, `2pc50`) under `hospital-first`. Batch B is `2pc50` under the eight frozen scheduled policies (`hospital-first`, `impact-first`, `degree-first`, `closeness-first`, `betweenness-first`, `centrality-first`, `random`, `direct-community`) plus `Unconstrained`. The overlapping `2pc50 / hospital-first` case is evaluated once, giving 12 distinct hazard-policy cases.

Every case uses the frozen 1000 evaluation realizations, damage states, repair durations, 57-crew C57_D1 schedule completions for scheduled policies, baseline 0.5 source gate with 14 Core sources, production `JULY_UTILITY_CONSTRAINED_92` tract mapping, and common 480-h exact-event horizon. The script verifies the formal hashes for the physical files, schedule shards, graph, source table, and production mapping before evaluation. No GA is run, no policy is reoptimized, and no schedule is redispatched. Formal matrix ID: `JULY92_REVIEWER_REVISION_FINAL_V1`; matrix SHA-256: `798189a92123a6f111170ffe6b620e2bd2ca710f35df33004ef1a0093efc36fe`; physical executable identity: `e934affb4b4c242d8e770070de684e7ab471c691`.

`binding_hours` in the station table is the mean exact-event duration per realization for which baseline `e_i(t)>a_i`; `binding_realization_fraction` is the fraction of the 1000 paired realizations with positive binding duration. `affected_population` is the population in tracts with positive mean paired capacity-induced burden for that hazard-policy case.

## Effect sizes

- Northridge / hospital-first: population burden Δ=0.134426 h; T80 Δ=0.029159 h; hospital burden Δ=0.028665 h; binding stations=1; binding tracts=25; affected population=117102.
- SanFernando / hospital-first: population burden Δ=0.134730 h; T80 Δ=0.012997 h; hospital burden Δ=0.028730 h; binding stations=1; binding tracts=25; affected population=117102.
- LongBeach / hospital-first: population burden Δ=0.134302 h; T80 Δ=0.009410 h; hospital burden Δ=0.028639 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / hospital-first: population burden Δ=0.121886 h; T80 Δ=0.012760 h; hospital burden Δ=0.025991 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / impact-first: population burden Δ=0.121475 h; T80 Δ=0.002114 h; hospital burden Δ=0.025903 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / degree-first: population burden Δ=0.125572 h; T80 Δ=0.020718 h; hospital burden Δ=0.026777 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / closeness-first: population burden Δ=0.125506 h; T80 Δ=0.009359 h; hospital burden Δ=0.026763 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / betweenness-first: population burden Δ=0.125554 h; T80 Δ=0.014233 h; hospital burden Δ=0.026773 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / centrality-first: population burden Δ=0.125425 h; T80 Δ=0.009391 h; hospital burden Δ=0.026746 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / random: population burden Δ=0.124831 h; T80 Δ=0.009432 h; hospital burden Δ=0.026619 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / direct-community: population burden Δ=0.121475 h; T80 Δ=0.002114 h; hospital burden Δ=0.025903 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / Unconstrained: population burden Δ=0.125765 h; T80 Δ=0.009708 h; hospital burden Δ=0.026818 h; binding stations=1; binding tracts=25; affected population=117102.

The sensitivity answers only how much modeled recovery outcomes change when provider-defined planning capacity ceilings are imposed on the retained facilities for which public SCE data support an unambiguous one-to-one station-facility interpretation. It does not validate a complete capacity model or a Los Angeles AC/DC power-flow model.
