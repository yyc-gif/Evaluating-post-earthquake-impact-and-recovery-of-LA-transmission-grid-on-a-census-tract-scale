# Sequence, schedule and recovery equivalence

| candidate       | sequence_sha256                                                  |   planning_loss_hr |   damaged_order_class |   operational_class |   crew_relabelled_route_class |   recovery_class |
|:----------------|:-----------------------------------------------------------------|-------------------:|----------------------:|--------------------:|------------------------------:|-----------------:|
| ga-optimized-01 | 8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab |       32.997840774 |                     3 |                   1 |                             1 |                1 |
| ga-optimized-02 | ff09a54ce2daffd5b46df92059e7c02b13c49d7991ac54221f05b3ddf44bc424 |       32.997840774 |                     2 |                   3 |                             1 |                1 |
| ga-optimized-03 | 9b44115354ad6199d5e5cd2004d3830f150bf7e891b3c485c075d4e203dff902 |       32.997840774 |                     1 |                   2 |                             1 |                1 |

Three distinct full permutations form 3 joint DS>0-filtered queue classes. At least one planning row contains all 92 damaged stations, making the joint filtered representation injective; equal loss cannot be attributed solely to DS0 removal across all 64 samples.

The exact decoder comparison checks station completion/arrival/travel, crew assignment, predecessor, global dispatch rank and final crew clocks separately. It identifies **3 operational-schedule classes** (arrival/completion/travel/crew/predecessor/clocks; global dispatch rank is recorded separately). Thus completion equality alone does not establish equality of complete operational schedules. Canonical route identity additionally checks each station's crew origin and predecessor plus origin-grouped final-clock multisets while ignoring interchangeable crew labels. It yields **1 route-equivalence class**. All 64 rows preserve arrival, travel and predecessor; differences in crew IDs/dispatch rank alone need not describe different restoration behavior. SEQUENCE_EQUIVALENCE_PER_REALIZATION.csv records each field for every 64-row comparison against candidate 1; class hashes are in SEQUENCE_EQUIVALENCE_CLASSES.csv.

There is **1 planning recovery-equivalence class**. With the same DS and station completion times, completion-step f, threshold F, source connectivity C and effective e are identical at all event times under the same graph/gate. This deterministic implication establishes recovery equivalence rather than merely a rounded scalar tie. All three losses equal 32.997840773883 h. Different crew labels/dispatch orders can coexist with the same station recovery behavior. These classes concern these three candidates on 64 saved realizations; they do not certify identity across all possible damage/duration states. Previously inspected 1,000 outcomes exhibit small differences, reported without reselection.

The prior bounded tie-pool checks of 100 near-best chromosomes are not an exhaustive partition of 92! or every searched candidate. Alternative representations of one planning recovery behavior must not be counted as three independent scientific improvements.

## Solution quality

Best feasible J=32.997840773883 h; conservatively downward-rounded valid fixed-model relaxation lower bound 31.360999855 h. Remaining gap **1.636840919 h**, **4.960% of the feasible value**; dividing by the lower bound instead gives 5.219%. State the denominator.

The relaxation eliminates crew competition/travel while preserving saved duration, threshold and source connectivity. It bounds the mathematical model conditional on fixed inputs, not out-of-sample performance. Pair swaps, insertion, inversion and tested block moves establish neighborhood-qualified local stability at tolerance 1e-9 only. Other combined changes lie outside those neighborhoods. Finite search, a plateau or exact six-slot restricted enumeration does not prove full 92-station global optimality or uniqueness.
