# Revised Paired Pilot Report

## Scientific revision decision

**CORE FINDINGS CHANGED — REFRAME REQUIRED**

The paired evidence is stable enough for direct manuscript rewriting, but it does not preserve the old 92-node strategy narrative. The paper should be reframed around how fixed restoration sequences redistribute strict-SCE tract burden under paired physical uncertainty. No extra C29/C114 or duration sensitivity is indicated before that rewrite.

## Reviewer-facing scientific findings

1. **System/logistics tradeoff.** Hospital-first minimized population burden in all 32 paired realizations. GA-Balanced reduced mean makespan by `2.97 h` and Gini by `0.029`, but increased population burden by `7.08 h` and hospital-tract burden by `5.21 h`. Its travel difference was unresolved (`0.47 h`, 95% CI `-0.33` to `1.25`).
2. **Population burden.** Hospital-first had the lowest mean (`44.13 h`). GA-Balanced, GA-HospFirst, and GA-Efficiency increased paired burden by `7.08`, `15.70`, and `15.08 h`; all 95% paired bootstrap intervals excluded zero.
3. **Vulnerability distribution.** Mean signed Q4-Q1 gaps were `-9.95`, `-6.40`, `-12.87`, and `-1.39 h`. Negative means indicate lower modeled burden in Q4 than Q1, not an equity verdict. GA-Efficiency minimized the absolute gap in `87.5%` of realizations and had the lowest mean Gini, but at a large total-burden cost. GA-HospFirst pushed the signed gap further negative while increasing absolute disparity and Gini.
4. **Winners and losers.** Versus Hospital-first, GA-Balanced improved 179 tracts (`22.3%` of population) and worsened 574 (`69.6%`). GA-HospFirst improved/worsened shares were `19.5%` / `67.5%`; GA-Efficiency shares were `1.7%` / `80.1%`.
5. **Logistics cost.** GA-Balanced most often minimized makespan (`53.1%`), but travel leadership was split: Hospital-first `34.4%`, GA-Balanced `25.0%`, GA-HospFirst `18.8%`, GA-Efficiency `21.9%`.
6. **Hospital-first versus GA-HospFirst.** Hospital-first was better on mean population T80, population burden, hospital-tract burden, makespan, and travel, and scored `0.015712` higher on the declared GA-HospFirst surrogate. This is a finite-budget search limitation plus an objective-alignment warning, not evidence of a GA optimum.
7. **Ranking stability.** Population-burden ranking was completely stable for Hospital-first. Makespan, travel, and absolute-gap rankings varied by realization; there is no defensible composite winner.
8. **Physical uncertainty.** Paired uncertainty does not overturn the main burden conclusion. It leaves GA-Balanced population T80 and travel differences unresolved and makes logistics rankings realization-dependent.
9. **Claims to delete.** Delete old 92-node makespan, T80, rank, hotspot, GA-optimality, and SVI-weighted-T80-as-equity claims, plus the objective-mismatch-only GA-HospFirst story.
10. **New claims for abstract/conclusion.** Under D302/C57 and Architecture B, Hospital-first robustly lowered total resolved service-access burden; GA-Balanced exchanged burden for shorter makespan and lower inequality; GA-Efficiency reduced between-quartile disparity and Gini while delaying most residents; GA-HospFirst was neither a burden winner nor a demonstrated optimizer.

## Scope and burden definition

The pilot contains 32 paired 2pc50 physical realizations and four fixed ex-ante D302 strategies under C57. Each DS and positive on-site duration vector was drawn once per realization and reused across strategies. The 128 executions are 32 paired physical states, not 128 independent hazard draws. Every run used the event scheduler, completion-step raw functionality, frozen source/component gate, and Architecture B propagation.

Class C remained missing and W1 was never renormalized. Normalized burden integrates delay only over identifiable A/B mass. Twelve 100%-Class-C tracts (`51,770` residents) have `ResolvedMass=0` and burden `NA`, never zero. Population T80 is a modeled resolved service-access proxy, not actual electricity restoration and not equity.

## Strategy distributions

| strategy | metric | mean | sd | median | q25 | q75 |
| --- | --- | --- | --- | --- | --- | --- |
| Hospital-first | population_resolved_T80_hr | 62.0001 | 5.8038 | 62.3301 | 59.2538 | 65.0000 |
| Hospital-first | population_normalized_burden_hr | 44.1308 | 4.7351 | 44.2167 | 39.9176 | 48.0061 |
| Hospital-first | hospital_mean_normalized_burden_hr | 43.4415 | 5.2845 | 42.6501 | 40.5498 | 47.0344 |
| Hospital-first | Q4_minus_Q1_burden_gap_hr | -9.9456 | 3.0701 | -9.8294 | -11.7685 | -9.1352 |
| Hospital-first | burden_gini | 0.2187 | 0.0485 | 0.2270 | 0.1800 | 0.2468 |
| Hospital-first | makespan_hr | 165.5518 | 8.0827 | 163.6718 | 160.0651 | 170.2060 |
| Hospital-first | total_travel_hr | 121.1607 | 1.9560 | 121.0085 | 119.9751 | 122.4856 |
| Hospital-first | absolute_Q4_minus_Q1_burden_gap_hr | 9.9456 | 3.0701 | 9.8294 | 9.1352 | 11.7685 |
| GA-Balanced | population_resolved_T80_hr | 62.1057 | 4.2102 | 62.0104 | 60.1968 | 65.2753 |
| GA-Balanced | population_normalized_burden_hr | 51.2069 | 4.6567 | 51.8170 | 49.0430 | 52.8772 |
| GA-Balanced | hospital_mean_normalized_burden_hr | 48.6560 | 4.8851 | 48.8693 | 45.3908 | 50.9256 |
| GA-Balanced | Q4_minus_Q1_burden_gap_hr | -6.4039 | 3.6302 | -6.1187 | -9.0569 | -3.7035 |
| GA-Balanced | burden_gini | 0.1902 | 0.0539 | 0.1901 | 0.1466 | 0.2320 |
| GA-Balanced | makespan_hr | 162.5846 | 6.7911 | 161.1753 | 158.5402 | 167.4883 |
| GA-Balanced | total_travel_hr | 121.6274 | 1.8945 | 121.7587 | 120.4496 | 123.1985 |
| GA-Balanced | absolute_Q4_minus_Q1_burden_gap_hr | 6.5846 | 3.2796 | 6.1187 | 3.7035 | 9.0569 |
| GA-HospFirst | population_resolved_T80_hr | 85.0577 | 7.5133 | 83.9331 | 79.6215 | 88.0084 |
| GA-HospFirst | population_normalized_burden_hr | 59.8278 | 3.1389 | 59.6842 | 57.4485 | 61.9685 |
| GA-HospFirst | hospital_mean_normalized_burden_hr | 48.1392 | 3.3119 | 47.5385 | 46.1227 | 51.1866 |
| GA-HospFirst | Q4_minus_Q1_burden_gap_hr | -12.8724 | 3.7928 | -12.7343 | -15.8231 | -10.1752 |
| GA-HospFirst | burden_gini | 0.2770 | 0.0311 | 0.2783 | 0.2552 | 0.2907 |
| GA-HospFirst | makespan_hr | 168.8181 | 7.7084 | 169.2213 | 165.2622 | 172.4545 |
| GA-HospFirst | total_travel_hr | 122.5762 | 2.3233 | 122.7356 | 120.7693 | 124.4126 |
| GA-HospFirst | absolute_Q4_minus_Q1_burden_gap_hr | 12.8724 | 3.7928 | 12.7343 | 10.1752 | 15.8231 |
| GA-Efficiency | population_resolved_T80_hr | 73.7897 | 10.2303 | 71.6982 | 65.2118 | 80.7062 |
| GA-Efficiency | population_normalized_burden_hr | 59.2065 | 4.8666 | 58.7857 | 55.7593 | 61.4854 |
| GA-Efficiency | hospital_mean_normalized_burden_hr | 55.6858 | 5.4142 | 55.9339 | 52.1497 | 58.8561 |
| GA-Efficiency | Q4_minus_Q1_burden_gap_hr | -1.3876 | 3.0628 | -1.3660 | -3.2183 | 1.0063 |
| GA-Efficiency | burden_gini | 0.1765 | 0.0397 | 0.1756 | 0.1555 | 0.2021 |
| GA-Efficiency | makespan_hr | 165.5542 | 8.2614 | 164.6072 | 159.0954 | 172.1780 |
| GA-Efficiency | total_travel_hr | 122.2251 | 2.5968 | 121.9669 | 120.9570 | 123.6809 |
| GA-Efficiency | absolute_Q4_minus_Q1_burden_gap_hr | 2.6663 | 2.0074 | 2.2859 | 1.2185 | 3.4272 |

## Paired GA-minus-Hospital-first differences

Negative values favor the GA for T80, burden, Gini, makespan, and travel. For signed Q4-Q1, the sign identifies which quartile carries more burden; closeness to zero is the absolute-gap metric. Intervals use 10,000 paired bootstrap resamples with the frozen seed.

| strategy | metric | mean_paired_difference | median_paired_difference | fraction_delta_lt_0 | bootstrap_ci_low | bootstrap_ci_high |
| --- | --- | --- | --- | --- | --- | --- |
| GA-Balanced | population_resolved_T80_hr | 0.1056 | -0.2094 | 0.5312 | -2.0193 | 2.3056 |
| GA-Balanced | population_normalized_burden_hr | 7.0760 | 6.1312 | 0.0000 | 5.8164 | 8.3753 |
| GA-Balanced | hospital_mean_normalized_burden_hr | 5.2145 | 4.5507 | 0.1250 | 3.6838 | 6.7954 |
| GA-Balanced | Q4_minus_Q1_burden_gap_hr | 3.5417 | 3.7249 | 0.1875 | 2.3400 | 4.8120 |
| GA-Balanced | burden_gini | -0.0285 | -0.0126 | 0.6250 | -0.0493 | -0.0088 |
| GA-Balanced | makespan_hr | -2.9672 | -4.4009 | 0.7188 | -5.3568 | -0.4968 |
| GA-Balanced | total_travel_hr | 0.4668 | 0.7999 | 0.4062 | -0.3258 | 1.2475 |
| GA-Balanced | absolute_Q4_minus_Q1_burden_gap_hr | -3.3610 | -3.4988 | 0.7812 | -4.6831 | -2.1269 |
| GA-HospFirst | population_resolved_T80_hr | 23.0576 | 22.8771 | 0.0000 | 20.0364 | 26.1662 |
| GA-HospFirst | population_normalized_burden_hr | 15.6970 | 16.1931 | 0.0000 | 14.1712 | 17.1449 |
| GA-HospFirst | hospital_mean_normalized_burden_hr | 4.6977 | 4.5562 | 0.1250 | 3.0018 | 6.3211 |
| GA-HospFirst | Q4_minus_Q1_burden_gap_hr | -2.9268 | -3.1524 | 0.8125 | -4.0956 | -1.7115 |
| GA-HospFirst | burden_gini | 0.0583 | 0.0508 | 0.0000 | 0.0452 | 0.0726 |
| GA-HospFirst | makespan_hr | 3.2663 | 5.4354 | 0.3438 | 0.5243 | 5.8385 |
| GA-HospFirst | total_travel_hr | 1.4155 | 1.4709 | 0.2812 | 0.4737 | 2.3243 |
| GA-HospFirst | absolute_Q4_minus_Q1_burden_gap_hr | 2.9268 | 3.1524 | 0.1875 | 1.7448 | 4.1122 |
| GA-Efficiency | population_resolved_T80_hr | 11.7896 | 11.1174 | 0.0625 | 8.2931 | 15.3212 |
| GA-Efficiency | population_normalized_burden_hr | 15.0757 | 15.7155 | 0.0000 | 13.9552 | 16.1686 |
| GA-Efficiency | hospital_mean_normalized_burden_hr | 12.2443 | 12.3825 | 0.0000 | 10.9455 | 13.4830 |
| GA-Efficiency | Q4_minus_Q1_burden_gap_hr | 8.5580 | 9.3366 | 0.0000 | 7.6668 | 9.4532 |
| GA-Efficiency | burden_gini | -0.0423 | -0.0377 | 0.9062 | -0.0531 | -0.0316 |
| GA-Efficiency | makespan_hr | 0.0024 | -1.5375 | 0.5312 | -2.3770 | 2.5129 |
| GA-Efficiency | total_travel_hr | 1.0644 | 1.1429 | 0.3125 | 0.0233 | 2.0770 |
| GA-Efficiency | absolute_Q4_minus_Q1_burden_gap_hr | -7.2793 | -7.7432 | 0.9375 | -8.3712 | -6.0488 |

## Tract winners and losers

Classification uses each tract's mean paired burden difference and the preregistered ±1 h threshold. Negative is lower burden than Hospital-first.

| strategy | group | tract_count | population | value | population_percent |
| --- | --- | --- | --- | --- | --- |
| GA-Balanced | improved | 179.0000 | 795507.0000 | -11.0496 | 22.2697 |
| GA-Balanced | near_zero | 64.0000 | 289001.0000 | 0.0955 | 8.0904 |
| GA-Balanced | worsened | 574.0000 | 2487644.0000 | 13.5380 | 69.6399 |
| GA-Efficiency | improved | 14.0000 | 62257.0000 | -3.8612 | 1.7428 |
| GA-Efficiency | near_zero | 140.0000 | 649657.0000 | 0.3588 | 18.1867 |
| GA-Efficiency | worsened | 663.0000 | 2860238.0000 | 18.5642 | 80.0704 |
| GA-HospFirst | improved | 154.0000 | 697130.0000 | -14.4361 | 19.5157 |
| GA-HospFirst | near_zero | 105.0000 | 464623.0000 | -0.0490 | 13.0068 |
| GA-HospFirst | worsened | 558.0000 | 2410399.0000 | 27.1090 | 67.4775 |

## Metric-specific ranking uncertainty

Lowest frequencies split exact ties. Signed-gap ranking identifies the most Q4-favoring sequence; absolute-gap ranking measures closeness to zero. No composite score is reported.

| metric | strategy | lowest_frequency |
| --- | --- | --- |
| population_normalized_burden_hr | Hospital-first | 1.0000 |
| population_normalized_burden_hr | GA-Balanced | 0.0000 |
| population_normalized_burden_hr | GA-HospFirst | 0.0000 |
| population_normalized_burden_hr | GA-Efficiency | 0.0000 |
| makespan_hr | Hospital-first | 0.1875 |
| makespan_hr | GA-Balanced | 0.5312 |
| makespan_hr | GA-HospFirst | 0.0625 |
| makespan_hr | GA-Efficiency | 0.2188 |
| total_travel_hr | Hospital-first | 0.3438 |
| total_travel_hr | GA-Balanced | 0.2500 |
| total_travel_hr | GA-HospFirst | 0.1875 |
| total_travel_hr | GA-Efficiency | 0.2188 |
| Q4_minus_Q1_burden_gap_hr | Hospital-first | 0.1875 |
| Q4_minus_Q1_burden_gap_hr | GA-Balanced | 0.0000 |
| Q4_minus_Q1_burden_gap_hr | GA-HospFirst | 0.8125 |
| Q4_minus_Q1_burden_gap_hr | GA-Efficiency | 0.0000 |
| absolute_Q4_minus_Q1_burden_gap_hr | Hospital-first | 0.0312 |
| absolute_Q4_minus_Q1_burden_gap_hr | GA-Balanced | 0.0938 |
| absolute_Q4_minus_Q1_burden_gap_hr | GA-HospFirst | 0.0000 |
| absolute_Q4_minus_Q1_burden_gap_hr | GA-Efficiency | 0.8750 |

## Manuscript action

Proceed directly to manuscript rewriting and reviewer response. Do not preserve the old strategy story. No additional simulation batch is automatically authorized; C29/C114, duration multiplier, source, and mapping sensitivities were not run.
