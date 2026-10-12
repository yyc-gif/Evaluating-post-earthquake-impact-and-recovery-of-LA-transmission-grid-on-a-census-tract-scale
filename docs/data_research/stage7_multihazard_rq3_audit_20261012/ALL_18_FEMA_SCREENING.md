# All18FEMA hazards screened

AUTHOR REVIEW - NOT FORMAL STAGE 7

ALL_18_HAZARD_INVENTORY.csv records scientific screening and native frequency support for every category, not only earthquakes. ALL_18_HAZARD_FIELD_QA.csv records every AFREQ/EXP_AREA/EALT/EALS/ALR field's existence, finite/null/zero/negative values and distribution. ALL_18_HAZARD_APPLICABILITY_RATINGS.csv preserves source-defined applicability separately.

| hazard            |   valid_tracts |   positive_EAL_tracts |   pooled_share |
|:------------------|---------------:|----------------------:|---------------:|
| Avalanche         |              0 |                     0 |    nan         |
| Coastal flooding  |           2299 |                    90 |      1.603e-05 |
| Cold wave         |           2299 |                     0 |      0         |
| Drought           |           2299 |                    78 |      6.67e-06  |
| Earthquake        |           2299 |                  2299 |      0.9817    |
| Hail              |           2299 |                  2299 |      1.867e-05 |
| Heat wave         |           2299 |                  2299 |      0.001339  |
| Hurricane         |              0 |                     0 |    nan         |
| Ice storm         |              0 |                     0 |    nan         |
| Landslide         |           2299 |                   906 |      6.52e-05  |
| Lightning         |           2299 |                  2299 |      0.0001885 |
| Riverine flooding |           2299 |                   430 |      0.0006134 |
| Strong wind       |           2299 |                  2299 |      0.0001516 |
| Tornado           |           2299 |                  2299 |      0.004277  |
| Tsunami           |           2299 |                    69 |      9.311e-06 |
| Volcanic activity |              0 |                     0 |    nan         |
| Wildfire          |           2299 |                   292 |      0.01166   |
| Winter weather    |           2299 |                    31 |      2.883e-06 |

Avalanche, hurricane, ice storm and volcanic activity have no numeric EALT in this cohort's archived release. Their exact ratings are preserved, not imputed. Release-specific NotApplicable does not establish universal physical impossibility or account for events after the source's temporal reference. Cold-waveEAL is numeric zero, a different state from null applicability. Agriculture-only drought EAL does not measure all drought effects on residents. Positive historical earthquake-service burden is not a direct measurement of broader wind/fire/flood/heat exposure.

Version-specific evidence uses the March2023document, not the current v1.20 technical PDF. Table6(PDFp63,printed5-4) explains distinctevents, eventdays and nohistoricaleventcount for modeledhazards. PDFp44(printed3-6) distinguishes NotApplicable, InsufficientData and noEAL. Frequency/exposure excerpts and exact PDF are retained. All18hazards are measured on the same2299IDs; no score-driven hazard selection occurs.
