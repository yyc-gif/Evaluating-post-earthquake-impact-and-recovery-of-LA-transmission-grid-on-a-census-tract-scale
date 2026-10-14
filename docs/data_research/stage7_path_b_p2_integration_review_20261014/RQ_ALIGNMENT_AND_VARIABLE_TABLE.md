# Path B research-question alignment - proposed manuscript text

RQ1: How do earthquake ground motion and network dependency shape modeled tract-level electricity-service disruption?

RQ2: Under finite repair resources and travel constraints, how do restoration priorities change overall and critical-service recovery?

RQ3: How are modeled recovery burdens and restoration-policy effects distributed across communities, and where do high cumulative service deficits co-occur with social vulnerability and other pre-existing risk-relevant conditions?

RQ3 is broader than a single social-vulnerability score. Its primary fitted measurements remain composite SOVI and population magnitude; environmental-hazard context is assessed separately. This wording does not imply that health dependence, income, all vulnerability dimensions or actual outage damages have been independently measured. Cumulative deficit includes depth and duration: it is not simply an outage-duration threshold.

| RQ   | variable        | units                                                     | transformation   | squared_distance_budget   |
|:-----|:----------------|:----------------------------------------------------------|:-----------------|:--------------------------|
| RQ1  | Init_Supply     | Fraction (0-1)                                            | None             | 1/9                       |
| RQ1  | Grid_Impact     | Unitless spectral descriptor                              | None             | 1/9                       |
| RQ1  | Redundancy_HHI  | Unitless concentration (not independent electrical paths) | None             | 1/9                       |
| RQ2  | B_Unconstrained | Equivalent full-service-deficit hours                     | None             | 1/6                       |
| RQ2  | MeanDelta       | Equivalent full-service-deficit hours                     | None             | 1/6                       |
| RQ3  | SOVI_SCORE      | National percentile score, 0-100                          | None             | 1/6                       |
| RQ3  | Population      | Persons                                                   | log1p            | 1/6                       |

RQ1 distinguishes initial modeled state, spectral structure and dependency concentration. RQ2 separates common frozen baseline recovery from additional finite-resource/dispatch/travel burden across a declared policy set. RQ3 describes residents and composite vulnerability, with supplementary screening geography rather than another fitted hazard coordinate. Grid_Impact is not the population-impact repair priority. HHI is not feeder redundancy. Population is not power demand. NCV14 is not vulnerability, total risk or modeled recovery.
