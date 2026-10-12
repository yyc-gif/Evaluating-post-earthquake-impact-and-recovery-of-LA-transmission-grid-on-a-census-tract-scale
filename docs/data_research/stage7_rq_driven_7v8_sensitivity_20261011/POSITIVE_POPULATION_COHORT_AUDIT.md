# Positive-population cohort audit

**AUTHOR REVIEW - NOT FORMAL STAGE 7.** Eligibility is independently derived from the frozen formal population: `Population > 0`. Full domain: **2315**; positive-population primary: **2299**; excluded zero population: **16**. The secondary residential rule additionally requires archived `housing_total > 0`, giving **2291**. The eight added tracts contain **16,979 frozen residents** (0.187% of full positive population). All eight proposed coordinates are complete; no imputation, generic complete-case deletion, old CORE3 geometry exclusion or population substitution.

## Exact exclusions

06037277400, 06037980001, 06037980002, 06037980005, 06037980006, 06037980007, 06037980013, 06037980018, 06037980020, 06037980022, 06037980028, 06037980030, 06037980034, 06037980037, 06037980038, 06037980039.

Every eleven-digit identity and reason is retained in `TRACT_COHORT_AND_EXCLUSIONS.csv`. The old four CORE3 geometry exclusions are all retained. The full 2,315 service/distributional domain and existing vulnerability quartiles are untouched.

## Added tracts, in actual units

|    tract_id |   Population |   housing_total |   BUILDVALUE |   Init_Supply |   B_480_hr |   CDC2022_E_TOTPOP |   CDC2022_EP_GROUPQ |
|------------:|-------------:|----------------:|-------------:|--------------:|-----------:|-------------------:|--------------------:|
| 06037265301 |        12987 |               0 |   3190633584 |        0.0000 |    38.9191 |              12794 |            100.0000 |
| 06037402404 |         1642 |               0 |   1913133764 |        0.0000 |    29.5272 |               2088 |            100.0000 |
| 06037578100 |         2249 |               0 |   2615762106 |        0.0075 |    26.3237 |               2285 |            100.0000 |
| 06037980009 |            5 |               0 |    112660312 |        0.0000 |    34.5741 |                  5 |            100.0000 |
| 06037980012 |           20 |               0 |    492299038 |        0.0000 |    28.5073 |                 27 |            100.0000 |
| 06037980023 |           47 |               0 |      7243309 |        0.0000 |    42.3343 |                  0 |            nan      |
| 06037980026 |           15 |               0 |      9543550 |        0.0021 |    36.5723 |                 11 |            100.0000 |
| 06037980033 |           14 |               0 |    776369274 |        0.0026 |    39.7162 |                  7 |            100.0000 |

Seven have CDC 2022 group-quarters share 100%; 06037980023 has zero CDC 2022 population and unavailable group-quarters share, but **47 frozen formal residents**. CDC missing marker -999 is retained as missing, never zero. The CDC values are descriptive source evidence, not replacements for formal population or a complete authentication of institution types. The exact named institutions have not been verified, so no prison/university/hospital label is invented.

Five added records belong to the 9800-series special-land-use numbering range. The [Census tract reference](https://www2.census.gov/geo/pdfs/partnerships/psap/G-650.pdf) defines this range for special uses with little or no population/housing; it does not identify the precise local use. The added population count therefore improves represented scope, while log population has genuine low-end leverage: minimum cohort-standardized log population is about -13.11.

## Cohort sensitivity is k-dependent

| specification   |   k |    min |   median |    max |
|:----------------|----:|-------:|---------:|-------:|
| A               |   3 | 0.9518 |   0.9566 | 0.9598 |
| A               |   4 | 0.9465 |   0.9492 | 0.9614 |
| A               |   5 | 0.6510 |   0.9770 | 0.9825 |
| A               |   6 | 0.4177 |   0.4672 | 0.4742 |
| A-minus-Init    |   3 | 0.9151 |   0.9437 | 0.9666 |
| A-minus-Init    |   4 | 0.9801 |   0.9860 | 0.9895 |
| A-minus-Init    |   5 | 0.9554 |   0.9580 | 0.9638 |
| A-minus-Init    |   6 | 0.9288 |   0.9296 | 0.9307 |
| B               |   3 | 0.9888 |   0.9890 | 0.9921 |
| B               |   4 | 0.9769 |   0.9800 | 0.9913 |
| B               |   5 | 0.9833 |   0.9887 | 0.9895 |
| B               |   6 | 0.9464 |   0.9492 | 0.9504 |
| B-equal-RQ3     |   3 | 0.9873 |   0.9879 | 0.9886 |
| B-equal-RQ3     |   4 | 0.9715 |   0.9852 | 0.9961 |
| B-equal-RQ3     |   5 | 0.9741 |   0.9791 | 0.9831 |
| B-equal-RQ3     |   6 | 0.4934 |   0.5009 | 0.5018 |
| B-minus-Init    |   3 | 0.9837 |   0.9947 | 0.9963 |
| B-minus-Init    |   4 | 0.9838 |   0.9868 | 0.9883 |
| B-minus-Init    |   5 | 0.9836 |   0.9836 | 0.9844 |
| B-minus-Init    |   6 | 0.9809 |   0.9863 | 0.9895 |

At k=4, common-tract ARI is about 0.95 for A and 0.98 for B (median over five matched seeds). At k=6, A falls to about 0.47 and is also seed-sensitive. A and A-minus-Init at seed42/k6 isolate **12 low-population tracts**, five from the added cohort, with median population 43.5. They are valid observations but a tiny exposure-defined class, not proof of a new universal community type. B halves the population budget and does not form that 12-tract cluster in these registered fits. This comparison changes features and budgets together.

Representation improves without an added-only cluster at k3-5. It is **not** valid to claim the eight records never influence clustering or that k6 is universally robust. Keep all positive-population records and disclose these sensitivities instead of deleting them to improve the fit.

## Spatial support

All 2,315 frozen TIGER internal points are finite, and all archived WKT polygons are nonempty/valid. Spatial perturbations use those internal points on a common UTM11N support; no area/land mask or old built-environment geometry admission is needed. A leave-quadrant-out fit tests geographic training composition, not polygon uncertainty or formal prediction validation.
