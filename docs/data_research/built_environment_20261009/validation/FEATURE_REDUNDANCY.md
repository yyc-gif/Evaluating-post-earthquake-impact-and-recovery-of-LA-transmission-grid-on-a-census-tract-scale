# Redundancy and Incremental Description

All results use the unchanged **2,291 residential tract IDs and five saved clusters**, scenario 2pc50. Existing eleven coordinates: recovery `T80`, `Init_Supply`; network/dependency `Grid_Degree`, `Grid_Impact`, `Grid_Betweenness`, `Redundancy_HHI`; development history `Pre_1970_Ratio`; urban/social context `Pop_Density`, `SOVI_SCORE`; composite hazard-risk `NRI_RISK_SCORE`; economic inventory `NRI_BUILDVALUE`. Density and building value use the original log1p transformations for Pearson/OLS comparisons. Spearman is invariant to those monotone transforms.

NRI risk is a multi-hazard composite incorporating expected annual loss, social vulnerability and community resilience. Its score is not a physical-form measure independent of hazard/social context. NRI building value is an economic stock-value quantity, not observed building area, height, material strength or seismic capacity. The local NRI vintage remains March 2023, not today's release. See the original source audit and [FEMA NRI methodology](https://hazards.fema.gov/nri/determining-risk). No new hazard/loss/demand fields were added.

| Pair | Pearson r | Spearman rho |
| --- | ---: | ---: |
| 5+ configuration / housing age | -0.449 | -0.468 |
| 5+ / log population density | 0.493 | 0.546 |
| 5+ / SOVI | 0.200 | 0.285 |
| 5+ / 10+ configuration | 0.956 | 0.963 |
| 5+ / one-unit share | -0.943 | -0.945 |
| Impervious pilot / housing age | -0.036 | -0.153 |
| Impervious pilot / log density | 0.660 | 0.615 |
| Impervious pilot / SOVI | 0.490 | 0.474 |
| Impervious pilot / 5+ | 0.514 | 0.544 |

The 10+ variable duplicates the main configuration signal and more directly overlaps the multi-unit component of social vulnerability. One-unit share is almost its compositional inverse. Do not add all three as separate independent descriptors or clustering coordinates. Selecting one-unit share solely for its larger cluster eta-squared would be outcome-driven variable selection.

Under the replicate <=10-pp screen, configuration correlations remain moderate: r(age)=-0.464 and r(log density)=0.546. The 5-pp selected sample gives -0.472 and 0.624. `INDICATOR_CORRELATION_SENSITIVITY.csv` keeps both replicate and original-approximation screens distinct; changed correlations in heavily selected samples are not evidence that the underlying full population changed.

| Candidate | Raw cluster eta2 | R2 from age + log density + SOVI | Unexplained fraction | Conditional VIF | Residual cluster eta2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5+ configuration | 0.06596 | 0.43719 | 0.56281 | 1.77681 | 0.02101 |
| Impervious pilot | 0.21599 | 0.47531 | 0.52469 | 1.90587 | 0.04329 |

Adding configuration to the three impervious controls raises R2 to **0.53390**, leaving **46.61%** unexplained. Age plus density alone explains 43.67% of configuration and 43.65% of imperviousness. Neither candidate is an interchangeable copy of housing age/density; imperviousness describes constructed ground cover rather than persons or residential units.

However, controlling for **all eleven existing features** explains **51.71%** of configuration and **55.80%** of imperviousness; residual cluster eta2 falls to **0.00107** and **0.00746**. These indicators add physical interpretive context but do **not** establish a substantially new independent partition of the existing communities. That distinction is especially important because saved labels were themselves constructed from the existing features.

Impervious C1-C4 difference is **15.96 pp**, g **1.166**, Cliff delta **0.539**; C3-C4 g **1.017**. Most other pilot impervious contrasts are much smaller. Configuration's larger C2-C3/C4 contrasts have g about **0.75-0.77**, while C3-C4 is only **0.066**. Whole-distribution overlap and precision matter more than counting contrasts with intervals excluding zero.

OLS R2 and `1/(1-R2)` are descriptive conditional redundancy diagnostics, not causal models or held-out predictive validation. Pearson/Spearman correlations and effect sizes use point estimates; full errors-in-variables correction is not available for all original social/composite inputs. No p-values, invented raster accuracy intervals or new PCA/K-means are used to choose indicators.
