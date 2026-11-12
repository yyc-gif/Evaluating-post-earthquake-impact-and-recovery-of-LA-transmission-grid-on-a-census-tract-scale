# Shared figure terminology

These definitions aid reuse of the study's existing scenario identifiers; they do not revise the model or the manuscript.

| Term | Meaning |
|---|---|
| `2pc50` | The 2%-in-50-year ground-motion case. This is not a probability of customer electricity failure. |
| `C57_D1` | The 57-crew reference resource configuration with baseline repair-duration scaling. |
| Unconstrained | Idealized parallel-repair reference without finite-crew/travel competition; damage, repair durations and service-evaluation mechanics remain modeled. |
| Modeled service availability | Dimensionless modeled tract or population-weighted service state, not measured delivered electricity. |
| Service loss / cumulative deficit | Integrated modeled availability deficit, expressed as equivalent full-service-deficit hours over the evaluation horizon. |
| T80 | Time to reach 80% modeled service availability for the specified tract or population-weighted curve. |
| Q1-Q4 | The original registered FEMA NRI social-vulnerability quartile groups; Q4 is highest. They are not recut for the clustering or export. |
| HHI | Herfindahl-Hirschman concentration of tract-substation dependency weights, not a count of independent electrical paths. |
| PGA / DS / GA | Peak ground acceleration / damage state / genetic algorithm. |
| CEC / SCE / LADWP | California Energy Commission / Southern California Edison / Los Angeles Department of Water and Power. |
| FEMA / NRI / SOVI | Federal Emergency Management Agency / National Risk Index / the registered social-vulnerability score. |
| Realization range | Empirical variation across modeled realizations. It is not a confidence interval for the mean. |
| Bootstrap confidence interval | Uncertainty interval for the specified mean effect; distinguish it from a realization range. |

Scenario-label sources: `src/la_grid/core/C257H_Project_Main.py`, `src/la_grid/plotting/Project_Visualizer.py`, `src/la_grid/revision/r1_equity_amendment_execute.py`, and `src/la_grid/revision/capacity/run_sce_capacity_supported_sensitivity.py`. The exact figure captions state which uncertainty definition applies; in the accepted master, Figure 6 uses realization ranges and Figure 7 uses bootstrap intervals for mean effects.
