# Stage 4/5 Final Crew Calculation Book

## 1. Final status

Final integer Stage 4/5 scheduling input:

```text
C57_substation_ratio_main
STAGE45_CREW_TOTAL_MAIN = 57
```

Exact effective crew-equivalent estimate retained for audit:

```text
C56_9_substation_ratio_exact
TOTAL_EXACT = 56.905860
```

Final yard allocation label:

```text
C57_yard_allocation_no_deletion_tie_coherent_zero_low
```

This package uses the **no-deletion D01–D16 yard list**. A yard may receive `0` integer crews in this specific integer realization, but it is not deleted from the documented candidate-origin list.

## 2. Claim boundary

All values are **effective crew-equivalent model inputs** for Stage 4/5 scheduling. They are not observed emergency rosters, observed local crew counts, actual disaster dispatch assignments, or yard-level staffing records.

The yard allocation weights are utility-internal visual/source proxy weights. They are not measured repair capacity and are not crew-count evidence.

## 3. Common formula

```text
effective_crews
= weighted_denominator × active_conversion_fraction × study_area_allocation / crew_size
```

| Parameter | Value | Treatment |
|---|---:|---|
| active_conversion_fraction | 0.28 | 0.50 shift availability × 0.80 work-ready × 0.70 logistics availability |
| crew_size | 4.5 | persons per effective crew |
| LADWP allocation | 0.833333333 | 35 / 42, substation-only ratio |
| SCE allocation | 0.319293478 | 235 / 736, substation-only ratio |

## 4. Utility-level final crew calculation

| Utility | Weighted denominator | Active conversion | Study-area allocation | Crew size | Exact effective crews | Integer crews |
|---|---:|---:|---:|---:|---:|---:|
| LADWP | 902.400000 | 0.28 | 0.833333333 | 4.5 | 46.791111 | 47 |
| SCE | 509.119257 | 0.28 | 0.319293478 | 4.5 | 10.114749 | 10 |
| **Total** | — | — | — | — | **56.905860** | **57** |

The final integer input is therefore:

```text
LADWP = 47
SCE = 10
TOTAL = 57
```

## 5. LADWP denominator calculation

LADWP uses the updated FY2025–2026 L1 direct repair core weighted denominator.

| Row | Category | Source class rows | Raw positions | Role weight | Weighted personnel |
|---|---|---|---:|---:|---:|
| DWP-L1-01 | direct_substation_electrical_craft | Senior Electrical Mechanic 109 + Electrical Mechanic 318 | 427 | 1.00 | 427.000 |
| DWP-L1-02 | direct_substation_test | Electrical Test Technician 148 + Senior Electrical Test Technician 35 | 183 | 1.00 | 183.000 |
| DWP-L1-03 | direct_substation_electrical_supervision | Electrical Mechanic Supervisor 90 + Sr Electrical Mechanic Supervisor 252 + Electrical Test Tech Supervisor 19 + Electrical Repair Supervisor 1 + Sr Electrical Repair Supervisor 1 | 363 | 0.60 | 217.800 |
| DWP-L1-04 | direct_controls_instrument_craft | Instrument Mechanic 47 | 47 | 0.80 | 37.600 |
| DWP-L1-05 | direct_general_electrical_craft | Electrician 56 | 56 | 0.50 | 28.000 |
| DWP-L1-06 | direct_station_auxiliary_craft | Battery Technician 5 | 5 | 0.80 | 4.000 |
| DWP-L1-07 | direct_controls_instrument_supervision | Instrument Mechanic Supervisor 10 | 10 | 0.50 | 5.000 |
| **Total** | — | — | **1091** | — | **902.400** |

LADWP arithmetic:

```text
LADWP_weighted_denominator
= 427×1.00 + 183×1.00 + 363×0.60 + 47×0.80 + 56×0.50 + 5×0.80 + 10×0.50
= 902.400

LADWP_exact
= 902.400 × 0.28 × 0.833333333 / 4.5
= 46.791111

LADWP_integer = 47
```

## 6. SCE denominator calculation

SCE retains the SC&M row-weighted comparable denominator:

```text
SCE_weighted_denominator = 509.119257
A_SCE = 235 / 736 = 0.319293478
```

SCE arithmetic:

```text
SCE_exact
= 509.119257 × 0.28 × 0.319293478 / 4.5
= 10.114749

SCE_integer = 10
```

The SCE 288 transmission direct field workforce remains excluded from this substation-ratio main case unless a separate transmission-inclusive sensitivity is explicitly opened.

## 7. Yard allocation method

The final yard allocation uses:

```text
utility_integer_crews × yard_raw_weight / utility_raw_weight_sum
```

Then a tie-coherent integer allocation is applied.

Rules:

```text
1. LADWP and SCE are allocated separately.
2. D01–D16 are retained; no-deletion version.
3. Same raw-weight SCE low-weight yards are not arbitrarily split.
4. SCE raw-weight-1 yards are uniformly assigned 0 integer crews in this C57 realization.
5. Fractional allocations remain in the audit table even when integer crews = 0.
```

## 8. Final yard-level allocation

| Yard | Utility | Facility | Raw weight | Fractional crews | Integer crews | Evidence boundary |
|---|---|---|---:|---:|---:|---|
| D01 | LADWP | Substations Regional Center / Palmetto | 2.000 | 1.446154 | 1 | A-caveated / manual_review |
| D02 | LADWP | Central District Headquarters / Wall St. | 15.000 | 10.846154 | 11 | B-caveated / manual_review |
| D03 | LADWP | Boylston | 1.000 | 0.723077 | 1 | B-low / manual_review |
| D04 | LADWP | Valley Center / Saticoy | 30.000 | 21.692308 | 22 | A-caveated / manual_review |
| D05 | LADWP | Central Service Center | 2.000 | 1.446154 | 1 | B-low / C-high |
| D06 | LADWP | Main Street | 15.000 | 10.846154 | 11 | A-caveated |
| D07 | SCE | Dominguez Hills Service Center | 5.000 | 2.173913 | 3 | B-caveated |
| D08 | SCE | Pomona / CRE Pomona Garage | 1.000 | 0.434783 | 0 | B-caveated; visual weak |
| D09 | SCE | Alhambra | 6.000 | 2.608696 | 3 | B-caveated context |
| D10 | SCE | Santa Monica | 2.000 | 0.869565 | 1 | C / B-low |
| D11 | SCE | Montebello / 1000 Potrero Grande Dr | 1.000 | 0.434783 | 0 | C |
| D12 | SCE | Whittier / Santa Fe Springs | 3.000 | 1.304348 | 2 | C-high / B-low |
| D13 | SCE | South Bay | 2.000 | 0.869565 | 1 | C-high / B-low |
| D14 | SCE | Covina / San Dimas | 1.000 | 0.434783 | 0 | A-caveated if transmission/job evidence retained |
| D15 | SCE | Monrovia | 1.000 | 0.434783 | 0 | C / manual_review |
| D16 | SCE | Long Beach | 1.000 | 0.434783 | 0 | C / B-low |

Integer allocation vector:

```text
D01 = 1
D02 = 11
D03 = 1
D04 = 22
D05 = 1
D06 = 11
D07 = 3
D08 = 0
D09 = 3
D10 = 1
D11 = 0
D12 = 2
D13 = 1
D14 = 0
D15 = 0
D16 = 0

TOTAL = 57
```

## 9. Notes on zero-crew retained yards

D08, D11, D14, D15, and D16 are not deleted. They remain documented candidate origins with fractional proxy allocations. They receive `0` integer crews in this specific C57 scheduling input because SCE has only 10 integer crews and the final tie-coherent proportional allocation avoids arbitrary splitting among equal raw-weight-1 yards.

## 10. Legacy status

| Prior value / option | Current status |
|---|---|
| C56_9_substation_ratio_exact | retained as exact audit value |
| C57_substation_ratio_main | final integer scheduling input |
| C57_min1_all_active | rejected; would give every SCE yard 1 and erase proportional weighting |
| C57_tie_coherent_zero_low | accepted final yard allocation |
| SCE 288 transmission field workforce | excluded from current main; sensitivity only |
| 394 SC&M residual | excluded from current main; sensitivity/context only |

## 11. QA summary

| Check | Computed | Expected / formula | Pass |
|---|---:|---|---|
| LADWP raw row sum | 1091 | 427+183+363+47+56+5+10=1091 | TRUE |
| LADWP weighted denominator | 902.400000 | 427*1+183*1+363*0.6+47*0.8+56*0.5+5*0.8+10*0.5=902.400 | TRUE |
| LADWP allocation ratio | 0.833333333 | 35/42=0.833333333 | TRUE |
| LADWP exact crews | 46.791111 | 902.400*0.28*(35/42)/4.5=46.791111 | TRUE |
| SCE allocation ratio | 0.319293478 | 235/736=0.319293478 | TRUE |
| SCE exact crews | 10.114749 | 509.119257*0.28*(235/736)/4.5=10.114749 | TRUE |
| Exact total | 56.905860 | 46.791111+10.114749=56.905860 | TRUE |
| Integer utility total | 57 | 47+10=57 | TRUE |
| Yard integer sum | 57 | sum D01-D16 integer crews=57 | TRUE |
| LADWP yard integer sum | 47 | sum LADWP yard crews=47 | TRUE |
| SCE yard integer sum | 10 | sum SCE yard crews=10 | TRUE |

## 12. Paper-safe wording

The Stage 4/5 scheduling model uses a rounded effective crew-equivalent input of 57 crews. This value is derived from public-evidence-informed LADWP and SCE workforce denominators, common event-availability assumptions, 4.5 persons per effective crew, and utility-specific 66kV+ substation allocation ratios. The result is a model input, not an observed emergency roster or actual utility dispatch plan.

Yard-level crew placement is allocated using utility-internal visual/source proxy weights on the retained D01–D16 yard list. The allocation should be described as a source-traceable proxy allocation rather than an observed facility-level crew assignment.
