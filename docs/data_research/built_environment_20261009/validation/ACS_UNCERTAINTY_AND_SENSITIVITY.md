# ACS Configuration Validation

## Definitions and Verification

Primary descriptor: `(B25024_006E + 007E + 008E + 009E) / B25024_001E`, housing units in structures with 5-9, 10-19, 20-49 and 50+ units, divided by **all housing units**, including vacant units, mobile homes and other housing types. This is not a building count, height measure or fragility variable. [Census 2022 table fields](https://api.census.gov/data/2022/acs/acs5/groups/B25024.html).

Diagnostic alternatives, not additional recommended descriptors: 10+ share (`007+008+009`); one-unit share (`002+003`, detached + attached). The 2-4 share (`004+005`) and mobile/other share (`010+011`) are used only to examine screening composition. Existing age is pre-1970 share (`B25034_008E` through `011E` / `001E`). Both tables are ACS **2018-2022 five-year**, released in 2023, and align to the study's 2020 tract-ID universe. All 2,315 IDs match; 50,930 B25024 estimate/MOE cells agree between the prior extraction and the VRE source. All study totals agree with B25034; all 2,291 existing age ratios are reproduced. There are 23 zero-housing full-domain tracts and one positive-housing tract excluded from the residential typology for zero formal population, not missing configuration data.

Original Census California files and [2022 variance-replicate documentation](https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/documentation/5-year/2018-2022_Variance_Replicate_Table_Documentation.pdf) are retained. For each derived ratio, sum the relevant counts within each of the 80 aligned replicates, divide by that replicate's total, and use `Var(theta) = (4/80) sum_r (theta_r - theta)^2`; `MOE90 = 1.645 sqrt(Var)`. Numerator/denominator and across-tract covariance are carried through these aligned replicates, **not** assumed independent.

Zero/100-percent or otherwise zero-variance, non-controlled ratios need the Census boundary model: `p* = min(0.5, 2.3 AW / D)` and `SE = sqrt(p*(1-p*) AW/D)`, with California `AW=16`. This applies to 158 residential 5+ shares. Four denominators have published 90% intervals including zero; no residential replicate denominator is zero. If one were zero, the guide's replacement of the undefined replicate ratio with zero is implemented; that rule is not imputation of a missing tract estimate. Retain unbounded MOEs; bounded display intervals alone do not establish precision.

## Actual Uncertainty and Cluster Profiles

The previous **868 above 10 pp** were approximate derived MOEs, not directly published Census MOEs for this custom share. The replicate/boundary calculation gives **211 above 10 pp**, **1,621 above 5 pp**, median **6.748 pp**, p90 **9.882 pp**. Coverage and precision are different questions.

| Cluster | n | Mean 5+ % | Median % | IQR % | Median tract MOE90, pp | Mean uncertainty margin, pp | n above 10 pp |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 1 | 910 | 40.25 | 33.85 | 11.89-67.74 | 7.02 | 0.40 | 91 |
| 2 | 183 | 47.35 | 42.86 | 22.72-72.49 | 7.43 | 0.67 | 23 |
| 3 | 619 | 27.56 | 21.68 | 7.66-39.50 | 6.68 | 0.49 | 55 |
| 4 | 545 | 25.82 | 14.43 | 2.26-39.76 | 5.69 | 1.62 | 39 |
| 5 | 34 | 31.86 | 32.67 | 11.77-47.56 | 7.83 | 1.47 | 3 |

Means equally weight tracts. Their intervals are conditional on the saved labels and fixed screening sets: use SDR for the cluster mean plus `sum(SE_boundary)/n` as a conservative triangle-bound SE supplement for boundary estimates whose replicates omit modeled uncertainty. Mean +/- 1.645 times this augmented SE is an **approximate measurement-uncertainty interval**, not an official Census cluster interval, a spatial bootstrap interval, or uncertainty about cluster assignments. Pairwise differences use aligned mean replicates and boundary supplements from both groups. Tables retain the unsupplemented SE separately.

C2-C4 = **21.52 pp**, augmented 90% interval **19.50-23.55 pp**, Hedges g **0.753**. C2-C3 = **19.78 pp**, g **0.773**. C3-C4 = **1.74 pp**, interval **-0.17 to 3.65 pp**, g **0.066**: do not describe these as distinct configuration classes. Nine of ten exploratory mean contrasts exclude zero, but several effects are small and IQRs overlap widely. These are not multiple-testing-adjusted claims of natural cluster separation. Overall configuration eta-squared is **0.06596**.

Housing-unit-weighted pooled shares are also calculated directly from summed counts/replicates: C1-C5 **44.50, 49.25, 30.27, 30.65, 31.26%**. They describe housing stock rather than an average tract; C3/C4 ordering changes slightly. Do not confuse the two estimands.

## Screening and Weighting

| Screen on 5+ MOE | Retained C1/C2/C3/C4/C5 | Means C1/C2/C3/C4/C5, % |
| --- | --- | --- |
| All | 910/183/619/545/34 | 40.25/47.35/27.56/25.82/31.86 |
| Replicate MOE <=10 pp | 819/160/564/506/31 | 39.70/46.55/26.86/24.72/32.60 |
| Replicate MOE <=5 pp | 216/38/169/242/5 | 35.06/51.38/12.99/12.53/2.46 |

The 10-pp screen retains 2,080/2,291 (90.79%), preserves the mean ordering and changes means by at most **1.109 pp**. The 5-pp screen retains 670 (29.25%); C5 loses 29/34 tracts and its mean falls **29.40 pp**. It is a materially different selected population, not an unbiased improved estimate of the original cluster.

With the 5-pp screen, single-unit-dominant tracts retain **35.25%**, 5+-dominant tracts **18.06%**, and 2-4-dominant tracts **0/24**. Retention varies from 14.71% in C5 to 44.40% in C4. C5 retained/removed SOVI means are **32.12/74.17**; configuration means **2.46/36.93%**. Screening changes social and physical composition. Full retained/removed age, density, housing-count and SOVI profiles are in `ACS_SCREENING_BIAS.csv`.

The original approximation screens are retained as separate diagnostics. Approximate <=10 pp retains only 1,423, disproportionately retaining 81.61% of single-unit-dominant versus 22.58% of 5+-dominant tracts. It must not be confused with the new replicate-based screen. A housing-total >=100 screen removes 11 tracts, all in C4, changing its mean by only 0.144 pp.

Unqualified inverse-variance pooling is not justified for heterogeneous neighborhoods and changes the estimand. A **descriptive** random-effects precision sensitivity uses DerSimonian-Laird moment tau-squared and `1/(SE_i^2+tau^2)` weights, not a replacement representative cluster estimate. The resulting means are **40.22, 47.34, 27.47, 25.46, 31.58%**; largest change is **0.364 pp**. It has no inferential CI: spatial covariance and uncertainty in estimated weights/tau are not modeled. Primary reporting retains all tracts, distributions, cluster uncertainty and the 10-pp sensitivity; the 5-pp results disclose selection bias rather than becoming the default sample.
