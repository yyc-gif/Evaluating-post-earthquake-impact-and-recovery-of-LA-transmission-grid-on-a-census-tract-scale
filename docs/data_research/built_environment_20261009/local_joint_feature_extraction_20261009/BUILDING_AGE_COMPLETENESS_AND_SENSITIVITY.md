# Building-age completeness and sensitivity

Two distinct measurements are supplied; neither is a silently imputed all-building age.

| scope | source | valid-age coverage median | tracts with defined pre1970 share |
|---|---|---:|---:|
| Original 2014 outlines | associated assessor YearBuilt1 on LARIAC4 | 0.952180 | 2315 |
| Strict linkage to 2020 outlines | unique BLD_ID and geometric IoU>=0.90 | 0.044016 | 2030 |

The original2014 statistic uses unioned observed footprints clipped to tract land. Its numerator is pre1970 area and denominator is valid-age area. Coverage divides valid-age area by all 2014 outline area. It spans actual available uses and is explicitly a2014 candidate; it is not evidence of the construction-age distribution of all 2020 buildings.

Strict2020 transfer accepts 36,341 county outlines and rejects 2,632,364 same-ID geometry mismatches. This conservative linked statistic has very low coverage and must not be described as representative all-use building age. A deterministic20,000-record convenience audit found median centroid displacement about1.25m despite near-identical outline areas, explaining sensitivity to geometry overlap. It does not prove the cause of the displacement or authorize coordinate correction. No transfer tolerance was relaxed and no government years were filled.

Years must be finite integer1800–2014 and not exceed the recorded assessor Roll_Year where present. YearBuilt1 is an associated assessor attribute, not independent validation of actual construction year. Conflicting duplicate geometry attributes are withheld. Residential-only statistics are separate. County record-level validity by use is in LARIAC4_COUNTYWIDE_AGE_BY_USE.csv; high county validity does not certify tract coverage or individual years.

For either scope, lower bound = known pre1970 area / all area; upper bound = (known pre1970 area + missing-age area) / all area. These are missing-age sensitivity bounds, not probabilistic confidence intervals or imputations. Width directly reveals insufficient information. The strict2020 and original2014 measures must not be pooled as if their footprints/vintages matched.

Government validity is approximately4.29%, industrial85.22%, institutional92.57%, commercial94.04%, residential98.86% at county record level. Observed tract-use area coverage and missing area are exported. ACS housing age is an independent residential-unit estimate with MOE, not a general non-residential age measure.
