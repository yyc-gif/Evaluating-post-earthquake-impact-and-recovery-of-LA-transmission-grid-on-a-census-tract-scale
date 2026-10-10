# FEMA v1.19 fields and composition

Source data are the archived Data/NRI_Table_CensusTracts_California.csv, 9,106 rows, every NRI_VER = Mar-23. All analyses use the exact 2,291 saved residential tract identities. Published percentile scores are retained without recomputing ranks in California or Los Angeles. RISK_SCORE, BUILDVALUE and SOVI_SCORE reproduce the saved Stage7 columns within recorded floating-point tolerance; see SAVED_STAGE7_SOURCE_REPRODUCTION.csv.

## Version-specific documentation

FEMA National Risk Index Technical Documentation, March2023, specifically v1.19.0, was retrieved as the FEMA document preserved by Ohio Emergency Management in its 2023 state-plan appendix: https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf . Its exact PDF, page text, SHA256 and URL are retained. The generic current FEMA technical-document URL now describes v1.20 and was not used to define this release. The live data-dictionary endpoint returned a non-document response; this limitation is recorded rather than substituting a newer dictionary. Version-specific equations and the actual archived field identities supply the required verification.

## Composition

For tract i and applicable hazards h and consequence types c:

EAL_ihc = exposed_value_ihc × annualized_frequency_ih × historic_loss_ratio_ihc,

with hazard-specific implementations, including the probabilistic earthquake method. Composite EAL sums the hazard losses. EAL_VALT = EAL_VALB + EAL_VALPE + EAL_VALA. EAL_VALPE = 11,600,000 × EAL_VALP in 2022 USD. It monetizes fatalities and injuries, not all population disruption or electric-service losses.

EAL_SCORE = 100 × (national rank(EAL_VALT) − minimum rank)/(maximum rank − minimum rank).

This published percentile is neither dollars nor hazard occurrence probability. A score difference is a percentile difference, not a proportional loss change. EAL_VALT is a monetary loss estimate. RISK_VALUE = EAL_VALT × CRF_VALUE. CRF maps the social-vulnerability/resilience ratio to a triangular distribution bounded0.5-2 with mode1. RISK_SCORE nationally ranks the adjusted risk value. Adding RISK_SCORE beside SOVI_SCORE mechanically embeds social vulnerability twice; actual correlation is a different, empirical issue.

SOVI and RESL are not direct multipliers in the unadjusted EAL calculation. Nevertheless, population/building/agricultural exposure, hazard geography and loss history can correlate with socioeconomic conditions. Absence of the CRF does not establish statistical or causal independence from social vulnerability. Building exposure uses the same Hazus stock underlying BUILDVALUE, with hazard-specific exposed portions; EAL is not merely BUILDVALUE, nor an exposure-free hazard measure.

ALR_VALB = EAL_VALB / BUILDVALUE; ALR_VALP = EAL_VALP / POPULATION; ALR_VALA = EAL_VALA / AGRIVALUE where the denominator exists. FEMA cautions against an all-consequence total dollar-rate quotient. ALR_NPCTL instead nationally ranks an EAL-weighted average of the separate consequence-rate national percentiles. It reduces total-stock scaling but retains consequence composition and EAL-derived weights. ALR_VRA_NPCTL further introduces the Community Risk Factor and must not be treated as independent of SOVI.

All component sums, population monetization, risk adjustment and available rates reconcile numerically within rounding tolerance; see EAL_NUMERICAL_COMPOSITION_QA.csv. National percentile formulas cannot be independently reconstructed from the California-only archive, so national scores are verified by release/source identity and monotone correspondence, not recomputed locally.

## Values, scores and ratings

Values have their stated dollar, population or index units. Scores are published national percentile positions for comparable geography. RISK/EAL ratings are five nationally derived k-means/natural-breaks categories, not fixed20-point score bins; SOVI/RESL ratings use national quintile boundaries. State percentiles (SPCTL) are different from national SCORE. Ratings and state scores are retained for audit and not treated as continuous substitute measurements.

| field         | definition                                                         | units                     | qualification                                                                                                                  | v119_printed_pages   |
|:--------------|:-------------------------------------------------------------------|:--------------------------|:-------------------------------------------------------------------------------------------------------------------------------|:---------------------|
| RISK_VALUE    | CRF-adjusted composite multi-hazard risk value                     | annual-dollar convention  | EAL_VALT multiplied by Community Risk Factor; not unadjusted expected loss                                                     | 3-1, 4-5             |
| RISK_SCORE    | National percentile of composite risk value                        | 0-100                     | National tract comparison, not a probability, rating, or dollar loss                                                           | 3-1 to 3-3           |
| EAL_SCORE     | National percentile of composite expected annual loss              | 0-100                     | Ranking of EAL_VALT over the national tract universe; not local re-ranking                                                     | 4-7                  |
| EAL_VALT      | Total multi-hazard expected annual loss                            | 2022 USD/year             | Sum of building, monetized population-equivalent and agriculture expected loss over applicable hazards                         | 4-6 to 4-7           |
| EAL_VALB      | Building expected annual loss                                      | 2022 USD/year             | Hazard-specific exposed building stock times annual frequency and historic loss ratio, with documented hazard-specific methods | 4-6, 5-9             |
| EAL_VALP      | Population expected annual loss                                    | fatality-equivalents/year | Fatalities plus one-tenth injuries, not number of electricity customers losing service                                         | 4-6                  |
| EAL_VALPE     | Population-equivalent expected annual loss                         | 2022 USD/year             | EAL_VALP times 11.6 million USD value of statistical life                                                                      | 4-6, 5-9             |
| EAL_VALA      | Agricultural expected annual loss                                  | 2022 USD/year             | Crops/livestock exposure and relevant hazard losses; not all consequence types apply to every hazard                           | 4-6, 5-9             |
| BUILDVALUE    | Total building exposure stock                                      | 2022 USD                  | Hazus 6.0 2022 valuations associated with 2020 Census geography; not annual loss, land value or tract income                   | 5-9                  |
| POPULATION    | Population used in FEMA exposure calculation                       | people                    | Archived Hazus exposure population; do not substitute study population in archived-rate reproduction                           | 5-9                  |
| AGRIVALUE     | Agricultural exposure stock                                        | 2022 USD                  | USDA 2017 Census of Agriculture source, inflation-adjusted, geography allocated by documented agriculture method               | 5-9 to 5-12          |
| SOVI_SCORE    | National percentile social vulnerability                           | 0-100                     | Mandatory separate social dimension; v1.19 uses CDC/ATSDR SVI inputs, not income quartiles                                     | 4-1 to 4-3           |
| RESL_SCORE    | National percentile community resilience                           | 0-100                     | HVRI BRIC county-level value assigned to tracts; constant 15.44 in this study subset                                           | 4-3 to 4-4           |
| RESL_VALUE    | Underlying community resilience index value                        | index                     | Underlying source value, distinct from nationally ranked RESL_SCORE                                                            | 4-3 to 4-4           |
| CRF_VALUE     | Community Risk Factor                                              | dimensionless             | Social-vulnerability/resilience ratio mapped to triangular distribution bounded 0.5-2, mode1; multiplies EAL to form risk      | 4-5                  |
| ALR_VALB      | Composite expected annual building-loss rate                       | fraction/year             | EAL_VALB / BUILDVALUE, across applicable hazards                                                                               | 5-34                 |
| ALR_VALP      | Composite expected annual population-loss rate                     | fraction/year             | EAL_VALP / POPULATION, using population-equivalent loss in people units                                                        | 5-34                 |
| ALR_VALA      | Composite expected annual agricultural-loss rate                   | fraction/year             | EAL_VALA / AGRIVALUE where agriculture exposure is positive; zero-exposure zero is not a measured rate                         | 5-34                 |
| ALR_NPCTL     | Unadjusted composite expected-annual-loss-rate national percentile | 0-100                     | National rank of EAL-weighted component-rate national percentiles; not a simple total-EAL/total-exposure quotient              | 5-35 to 5-36         |
| ALR_VRA_NPCTL | Social-vulnerability/resilience-adjusted loss-rate percentile      | 0-100                     | Rate adjusted by CRF before percentile transformation; excluded from candidate D because it reintroduces the social factor     | 5-36                 |

## Scope of multi-hazard coverage

The archive contains all18 hazard EAL fields. Non-applicable hazard values remain null with their archived rating; they are not represented as observed zero losses. Present hazard values reconcile the total. Across these residential tracts, earthquake contributes98.1563% of pooled EAL; median tract share99.2745%. This is a multi-hazard calculation with a geographically earthquake-dominated composition, not an earthquake-only variable and not balanced evidence for equal importance of every hazard. Buildings contribute69.8545%, monetized population30.1443%, agriculture0.0011% of pooled EAL. These are shares of modeled annual losses, not socioeconomic or power-recovery causal effects.
