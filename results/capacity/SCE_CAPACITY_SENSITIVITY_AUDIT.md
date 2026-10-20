# SCE Capacity Sensitivity Audit

## Closure status

This is the closed Reviewer 1 Comment 2 capacity sensitivity. It is post-processing only. No sampling, damage state, repair duration, dispatch, priority sequence, GA, source gate, tract mapping, or restoration schedule is recomputed. Vulnerability-first is read only from the saved station trajectories at C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision\Formal_Experiment_20260923\Equity_Amendment\T\2pc50\C57_D1. direct-community is excluded after verifying that its frozen sequence hash is identical to Impact-first.

Every baseline realization is reconciled before the capacity ceiling is applied. Original policies are checked against Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet and Vulnerability-first against Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet. The tolerance is 1.0e-09 h for population burden, T80, and hospital burden.

## Coverage and formula

- Supported station factors: 19/92.
- Numeric-evidence retained SCE stations: 28; 9 are multi-facility and receive no station factor.
- Unsupported retained stations: 73, asserted to satisfy e_cap=e exactly.
- Tracts with supported dependency: 932/2315.
- Population-weighted supported dependency mass: 0.2534.
- W_r^sup P25/P50/P75: 0.000000, 0.000000, 0.260429.
- Only OLINDA 306279 has K/D<1 in the supported subset.
- Actual binding stations in the evaluated cases: 1 (306279 (OLINDA 66/12)).
- Tracts with positive capacity-induced burden in at least one case: 25.

Production service remains e_i(t)=f_i(t)F_i(t)C_i(t). For supported stations, a_i=min(1,K_i/D_i) and e_i^cap(t)=min[e_i(t),a_i]. Unsupported stations retain e_i^cap=e_i. Tract service remains A_r^cap(t)=sum_i w_ri e_i^cap(t). FACILITY_LOADING is QA only. The three rows exceeding the earlier 0.05 percentage-point D/K-versus-provider-loading QA tolerance remain in the evidence audit rather than being deleted: COLORADO 66/4.16 (+0.07704 pp), GANESHA 12/4.16 (-0.05190 pp), and REPETTO 66/4.16 (+0.06551 pp). They are excluded from station-level capacity factors only because their retained stations are multi-facility and SCE provides no public aggregation rule.

Hard assertions require 19 supported stations, 9 multi-facility exclusions, K/D<1 only at OLINDA 306279, 73 unsupported stations unchanged, e_cap<=e on supported stations, strict loss accounting including L_capacity, exactly eight distinct scheduled 2pc50 policies plus Unconstrained, no direct-community output, and inclusion of vulnerability-first.

## Baseline reconciliation

- Northridge / hospital-first: max abs difference population burden=3.553e-15, T80=0.000e+00, hospital burden=7.105e-15.
- SanFernando / hospital-first: max abs difference population burden=1.776e-15, T80=0.000e+00, hospital burden=3.553e-15.
- LongBeach / hospital-first: max abs difference population burden=1.776e-15, T80=0.000e+00, hospital burden=3.553e-15.
- 2pc50 / hospital-first: max abs difference population burden=1.421e-14, T80=0.000e+00, hospital burden=2.132e-14.
- 2pc50 / centrality-first: max abs difference population burden=2.132e-14, T80=0.000e+00, hospital burden=2.842e-14.
- 2pc50 / impact-first: max abs difference population burden=1.421e-14, T80=0.000e+00, hospital burden=2.132e-14.
- 2pc50 / betweenness-first: max abs difference population burden=2.132e-14, T80=0.000e+00, hospital burden=2.132e-14.
- 2pc50 / degree-first: max abs difference population burden=1.421e-14, T80=0.000e+00, hospital burden=2.842e-14.
- 2pc50 / closeness-first: max abs difference population burden=1.421e-14, T80=0.000e+00, hospital burden=2.132e-14.
- 2pc50 / random: max abs difference population burden=1.421e-14, T80=0.000e+00, hospital burden=4.974e-14.
- 2pc50 / vulnerability-first: max abs difference population burden=1.421e-14, T80=0.000e+00, hospital burden=2.132e-14.
- 2pc50 / Unconstrained: max abs difference population burden=1.421e-14, T80=0.000e+00, hospital burden=1.776e-14.

Frozen 2pc50 anchors reproduce as reported: Hospital-first 34.306 / 45.971 / 33.367 h; Impact-first 33.594 / 45.251 / 33.059; Vulnerability-first 34.258 / 46.437 / 33.939.

## Effect sizes

- Northridge / hospital-first: population burden delta=0.134426 h; T80 delta=0.029159 h; hospital burden delta=0.028665 h; binding stations=1; binding tracts=25; affected population=117102.
- SanFernando / hospital-first: population burden delta=0.134730 h; T80 delta=0.012997 h; hospital burden delta=0.028730 h; binding stations=1; binding tracts=25; affected population=117102.
- LongBeach / hospital-first: population burden delta=0.134302 h; T80 delta=0.009410 h; hospital burden delta=0.028639 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / hospital-first: population burden delta=0.121886 h; T80 delta=0.012760 h; hospital burden delta=0.025991 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / centrality-first: population burden delta=0.125425 h; T80 delta=0.009391 h; hospital burden delta=0.026746 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / impact-first: population burden delta=0.121475 h; T80 delta=0.002114 h; hospital burden delta=0.025903 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / betweenness-first: population burden delta=0.125554 h; T80 delta=0.014233 h; hospital burden delta=0.026773 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / degree-first: population burden delta=0.125572 h; T80 delta=0.020718 h; hospital burden delta=0.026777 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / closeness-first: population burden delta=0.125506 h; T80 delta=0.009359 h; hospital burden delta=0.026763 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / random: population burden delta=0.124831 h; T80 delta=0.009432 h; hospital burden delta=0.026619 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / vulnerability-first: population burden delta=0.120107 h; T80 delta=0.005182 h; hospital burden delta=0.025612 h; binding stations=1; binding tracts=25; affected population=117102.
- 2pc50 / Unconstrained: population burden delta=0.125765 h; T80 delta=0.009708 h; hospital burden delta=0.026818 h; binding stations=1; binding tracts=25; affected population=117102.

Across the nine 2pc50 cases, population-burden increments range from 0.120107 to 0.125765 h.

### Required pairwise contrasts

- impact-first - hospital-first: population burden -0.712779 -> -0.713190 h (change -0.000411 h; sign flipped=no); T80 -0.719445 -> -0.730090 h; hospital burden -0.307361 -> -0.307448 h.
- degree-first - hospital-first: population burden +1.401244 -> +1.404930 h (change +0.003686 h; sign flipped=no); T80 +3.539142 -> +3.547100 h; hospital burden +2.364318 -> +2.365104 h.
- vulnerability-first - hospital-first: population burden -0.048616 -> -0.050395 h (change -0.001779 h; sign flipped=no); T80 +0.466293 -> +0.458716 h; hospital burden +0.572389 -> +0.572009 h.

## Reviewer 1 Comment 2 response

1. Source-gate interpretation. C_i(t) represents surviving source-path availability only. e_i(t) is a modeled service-availability proxy, not delivered MW. The model does not solve AC/DC power flow and does not represent branch loading, voltage, reactive power, generation/import dispatch, or load shedding.

2. External-data-constrained stress test. SCE public planning data provide facility-level forecast peak demand D and loading limit K. For the 19/92 retained stations with a strict one-to-one facility interpretation, we imposed the static planning-peak ceiling e_i^cap(t)=min[e_i(t),K_i/D_i]. The supported subset intersects 932/2315 tracts and has population-weighted supported dependency mass 0.2534. Nine additional numeric-evidence stations have multiple facility rows and were not aggregated.

3. Result and boundary. Within the strictly supported subset, only OLINDA is capacity-binding. The four-hazard Hospital-first population-burden increment is about 0.12-0.13 h; the complete 2pc50 strategy range and the three direct pairwise contrasts are reported above. The principal strategy comparisons are therefore not strongly driven by this particular class of documented SCE facility planning-capacity constraints within the supported subset. This test cannot establish adequacy for unsupported facilities, source-generation availability, branch-flow feasibility, voltage, reactive power, dispatch, or load shedding.

> Within the subset of retained facilities for which public SCE data support a strict one-to-one interpretation, imposing provider-defined planning capacity ceilings produced only small changes in modeled recovery outcomes. The principal strategy comparisons therefore were not strongly driven by this class of documented facility-capacity constraint. However, the stress test covers only part of the modeled network and does not establish adequacy for unsupported facilities, source-generation availability, branch flow, voltage, reactive power, dispatch, or load-shedding feasibility.
