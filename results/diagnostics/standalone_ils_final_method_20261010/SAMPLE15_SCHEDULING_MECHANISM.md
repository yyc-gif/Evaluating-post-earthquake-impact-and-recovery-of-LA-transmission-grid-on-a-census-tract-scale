# Realization 15: Whole-Schedule Event Accounting

Selected standalone ILS minus frozen GA loss: -2.022687988408 h. Exact changes: self +0.130351320765, threshold +0.004415725088, source -2.157455034262 h. This is the same physical state and duration vector, not new sampling or a modified objective.

Station completion: 22 earlier, 21 later, 47 unchanged. Mean completion change -0.104490247 h over stations with finite completion values. Total directed travel: ILS 27.544654731 h, frozen GA 27.231613637 h. These station/crew summaries do not weight source reconnection or dependency masses in the same way as the objective.

Largest beneficial intervals, cut at the union of both exact completion clocks:

|     start_hr |       end_hr |   ILS_minus_GA_loss_hr |   ILS_effective_service |   GA_effective_service |   ILS_only_dependency_mass |   GA_only_dependency_mass |
|-------------:|-------------:|-----------------------:|------------------------:|-----------------------:|---------------------------:|--------------------------:|
| 19.490491662 | 21.042918991 |           -0.473133857 |             0.322390551 |            0.017620177 |          2763207.297874207 |               0.000000000 |
| 23.685222631 | 24.671898419 |           -0.327853997 |             0.357072951 |            0.024791566 |          3012636.487296705 |               0.000000000 |
| 22.418409470 | 23.136553474 |           -0.229836634 |             0.344834110 |            0.024791566 |          2966692.319011470 |           65019.555004953 |
| 21.597853411 | 22.282564468 |           -0.224046998 |             0.344834110 |            0.017620177 |          2966692.319011470 |               0.000000000 |
| 24.671898419 | 25.242654999 |           -0.189651787 |             0.357072951 |            0.024791566 |          3012636.487296705 |               0.000000000 |
| 21.116681051 | 21.597853411 |           -0.153496872 |             0.336626181 |            0.017620177 |          2892274.952124963 |               0.000000000 |
| 23.136553474 | 23.587183688 |           -0.144220840 |             0.344834110 |            0.024791566 |          2966692.319011470 |           65019.555004953 |
| 19.166689187 | 19.490491662 |           -0.098685401 |             0.322390551 |            0.017620177 |          2763207.297874207 |               0.000000000 |

Each interval contribution is duration times (frozen-GA effective service minus ILS effective service). Their complete sum matches the independently verified loss difference. Full source IDs, exclusively source-connected station sets and their dependency masses are in `SAMPLE15_EXACT_INTERVAL_DIFFERENCES.csv`; native graph-component membership and newly connected dependency masses are in the two source event JSONs. Full 92-station completion/crew/travel differences are retained separately.

Dependency mass is the fixed population-mapping contribution carried by stations, not mutually exclusive geographically identified customers or delivered electrical load. Positive/negative intervals can coexist; a lower mean does not imply every station or community improves. These comparisons describe two complete schedules. They are not a controlled single-station-edit counterfactual and do not prove that a particular station movement caused the source benefit. No new optimization or physical sampling was performed to produce this accounting.
