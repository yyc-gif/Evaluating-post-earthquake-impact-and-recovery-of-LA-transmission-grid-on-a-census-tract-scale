# CDC climate module: author decision
AUTHOR REVIEW - NOT FORMAL STAGE 7

## Recommendation
**Keep the seven-variable P2 candidate; use standalone CBM and domain maps as climate-context descriptors. Do not add an eighth coordinate yet. K remains undecided.**

1. **Direct social adjustment? No.** Official standalone RPL_CBM sums nine climate indicator percentiles and nationally ranks the sum. It contains no direct household, social vulnerability, resilience or building-value factors. RPL_EJI_CBM does contain the other EJI modules and is not eligible. This is arithmetic separation, not proof of geographic/statistical independence.
2. **Coverage? 2,299/2,299 valid published ranks, all exact eleven-digit 2020 GEOIDs.** The full 2,315 study domain, 16 zero-population exclusions and eight special-use tracts remain unchanged. CDC's own ACS population is not substituted; tract 06037980023 has CDC population zero but frozen population 47 and remains.
3. **Source-null/flags? All 2,299 have hurricane F=1 (9,066,522 residents).** That is source-null/excluded-to-zero, not observed absence; the cause is not separately coded. It is locally constant and not the variation driver. F_NEHD/F_SMOKE/F_BURN are absent even in both bulk archives/dictionary and raw service. The 2,251 burned-area zeros lack released zero/null discrimination; this is unresolved, not a claim they are all missing. The 13 national heat interpolation IDs are unavailable.
4. **Local components? Primarily riverine frequency plus heat.** Riverine rank contributes 69.248% of local SPL variance and correlates 0.918 with CBM. Heat contributes 12.215%, wildfire 10.310%, coastal 8.106%. Hurricane is constant; drought/strong-wind/tornado rank variation contributes almost nothing. These are local covariance shares, not official weights or causal contributions. National multi-indicator coverage does not imply locally balanced nine-hazard information.
5. **Meaningful multi-hazard information? Some, but limited.** Heat strongly affects fine rank order; wildfire/coastal identify subsets. No new synthesized physical index is created. Complete ranks do not cure source-support gaps by themselves.
6. **Incremental information? Yes statistically, not established as mandatory construct.**

| variable_a       |   Pearson |   Spearman |
|:-----------------|----------:|-----------:|
| Init_Supply      |  0.083017 |  -0.067599 |
| Grid_Impact      |  0.14085  |   0.26605  |
| Redundancy_HHI   | -0.11532  |  -0.10828  |
| B_Unconstrained  |  0.058821 |  -0.024668 |
| MeanDelta        |  0.18497  |   0.2985   |
| SOVI_SCORE       | -0.13283  |  -0.081518 |
| log1p_Population | -0.10257  |  -0.054294 |

Seven-feature conditional linear R2 = 0.07238, VIF = 1.07803; fixed random-fold nonlinear R2 = 0.16471, 15-km-block R2 = 0.05731. Thus non-admission is not based on linear duplication. Predictive overlap is not causality or full independence.

7. **Physical geographic correspondence? Partial support, not intensity validation.**

| CDC_variable   | physical_variable                 |    n |   Pearson |   Spearman |
|:---------------|:----------------------------------|-----:|----------:|-----------:|
| E_NEHD         | Historical_heat_days_2018_2022    | 2299 |  1        |   1        |
| E_BURN         | Wildfire_high_land_fraction       | 2200 |  0.25658  |   0.2784   |
| E_SMOKE        | Wildfire_high_land_fraction       | 2200 |  0.17785  |   0.1742   |
| E_RFLD         | Flood_SFHA_land_fraction_complete | 2088 |  0.42597  |   0.94406  |
| E_CFLD         | Flood_coastal_V_land_fraction     | 2299 |  0.16316  |   0.61947  |
| RPL_CBM        | tract_seismic_PGA                 | 2294 | -0.047451 |  -0.26137  |
| RPL_CBM        | Wildfire_high_land_fraction       | 2200 |  0.0503   |  -0.044112 |
| RPL_CBM        | Flood_SFHA_land_fraction_complete | 2088 |  0.46966  |   0.65019  |

Riverine frequency aligns with mapped SFHA support on 2,088 complete NFHL tracts (Spearman 0.944); historical burn versus CAL FIRE severity is weaker (0.278 on 2,200). Heat exactly matches the prior *same CDC source*, not independently acquired temperature evidence. Coastal V fractions are lower-bound intersections on partial mapped support, not full hazard certainty. Earthquake PGA is not a CBM input. Polygon area is not exposed resident count.

8. **Admission? Not yet: unresolved mandatory source flags/zero semantics and local construct concentration.** No tracts are dropped or imputed to force eligibility.
9. **K/silhouette/ARI effects? Not evaluated.** Admission stopped before any new fit; no eight-coordinate Elbow/Silhouette/stability claim. H1/H2 budgets are predeclared, not fitted or optimized. Existing rare STATION Q group is untouched and is not reinterpreted by this audit.
10. **Manuscript choice? P2 plus standalone context maps is the defensible current candidate.** Formal Stage7, manuscript, numbered figures, physical realizations and schedules are unchanged. Author must approve any later measurement admission, policy set, budget and K. CDC clarification of omitted flags and source processing is the specific missing evidence.

## Reproduction and limitations
Original national/state archives, dictionaries, raw/map query payloads and SHA256s are retained. Independent QA verifies ranks, identities, arithmetic, associations, preservation and repeatability. All 950 protected files and previous diagnostic objects are checked. No MC, GA, repair, service-trajectory or K-means computation is authorized or run. Manifest-bound local frozen source/archive dependencies remain required for source-level baseline reconstruction where absent from Git; saved verified P2/physical CSVs support this diagnostic's core calculations. Six vector review figures have 600 dpi previews and publication-size renders. Remote delivery is verified separately using real LFS bytes, not pointers.
