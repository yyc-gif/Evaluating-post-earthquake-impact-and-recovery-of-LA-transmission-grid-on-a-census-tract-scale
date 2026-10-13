> EXPLORATORY MULTI-HAZARD INDEX AUDIT — NOT FORMAL STAGE 7

# What is removed and what is retained

NRI's final risk combines expected losses with a community factor based on social vulnerability/resilience. Risk score is a ranking of that construct. Numerical division RISK_VALUE/CRF_VALUE reproduces EAL_VALT within release rounding tolerance (FEMA_SOCIAL_FACTOR_REMOVAL_NUMERICAL_QA.csv): it does not remove asset, population or loss-model inputs. EAL still encodes exposed building/population/agricultural stock and historical/modelled consequence assumptions. ALR_NPCTL is not a pure occurrence-frequency measure.

The new screening operator uses only each released *_AFREQ, *_EXP_AREA and AREA. It does not read SOVI, RESL, CRF, BUILDVALUE, POPULATION, EAL, HLR or Risk in constructing the hazard coordinate. Frozen study population is used only as the separate seventh coordinate and for post-fit resident coverage. No monetary building exposure or modeled service outcome enters the eighth coordinate.

Geographic EXP_AREA nevertheless inherits FEMA's widespread, susceptible or representative footprint conventions, and block/fishnet/county spatial aggregation. AFREQ can be an observed-event model, event-day estimate, minimum default or modeled probability surrogate. Independence from direct monetary/social adjustment does not establish physical measurement validity or independence among hazard processes.

Earthquake is special: March2023 documentation PDF151-155 describes a USGS100-year minor-damage probability surface, numerical conversion and area aggregation. This released surrogate is not CGS PGA-2pc50, a historical event count or a independently verified annual station-failure probability. Earthquake EAL instead uses Hazus P366 methodology; it is not reconstructed by substituting the frequency-area factor. The exact raw source raster was not acquired for pixel-level validation.
