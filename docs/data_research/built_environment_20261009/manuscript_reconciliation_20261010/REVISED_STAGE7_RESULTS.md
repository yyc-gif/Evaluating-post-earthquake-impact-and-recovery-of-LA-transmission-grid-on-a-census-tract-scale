# Revised Stage 7 Results

Insertion: in S19 P0040, retain the four sentences reporting the independent Q4/resource contrasts. Replace the remaining old five-class/transform/hotspot account with the following. Figures 7-8 and Table 4 are new identifiers in this review copy only; original Figures 1-6 and Tables 1-3 retain their identifiers.

The four-class joint typology classifies 2,287 residential tracts: C1 contains 850, C2 34, C3 651, and C4 752. Their mapped populations are 3,387,008, 124,158, 2,440,001, and 3,085,986, respectively, totaling 9,037,153. Four residential tracts remain unclassified because of unresolved geometry: 06037189703, 06037301601, 06037301602, and 06037404600, with 12,390 mapped residents. The spatial distribution and standardized joint profiles are shown in Figures 7 and 8; Table 4 retains original units. C1-C4 are membership identifiers, not a priority order.

C1 and C4 both have high mean social vulnerability (SOVI_SCORE 79.16 and 82.87), but differ in classified-land mix and observed building age. Their mean normalized land-use entropies are 0.283 and 0.489, and mean observed pre-1970 building-area shares are 0.840 and 0.691. Mean roof-outline coverage is 0.265 and 0.277. C1 has mean cumulative service loss of 32.42 h and T80 of 43.71 h, compared with 33.89 h and 44.77 h in C4. These are co-occurring profiles, not estimated built-environment effects on restoration.

C3 has the highest mean cumulative service loss (36.34 h) and mean tract T80 (46.78 h), while its mean SOVI_SCORE is substantially lower (31.06) than in C1 and C4. Thus the class with the greatest mean modeled loss is not the class with the highest mean social vulnerability. Its mean classified-land entropy, roof-outline coverage, and observed pre-1970 share are 0.335, 0.231, and 0.688. Its median building stock is approximately 659.0 million 2022 USD, an economic quantity rather than a capacity or damage-resistance measurement.

C2 has relatively greater mean initial modeled availability (0.01815, or 1.815%) and lower cumulative service loss (23.60 h), with mean T80 of 38.50 h. Initial availability nevertheless remains very low in absolute terms, and this 34-member class must not be described as universally resilient. Its mean SOVI_SCORE is 67.99 but its median is 85.04, illustrating heterogeneity that a class mean can conceal. In Figure 8 its initial-service standardized mean is +7.15, beyond the +/-1.5 color saturation limit; the annotation and Table 4 preserve that magnitude.

The saved spatial checks support C3's higher cumulative loss and lower social vulnerability relative to C1/C4, and the C1/C4 contrasts in classified-land mix and observed age. They do not support every minor distinction: C1/C4 degree and impact rankings reverse in 12 of 20 deletion cases, and the small C3/C4 age difference reverses in seven. Median full-cohort ARI is 0.9234 for D and 0.9458 for the EAL alternative; the 20 cases include only 17 unique deletion sets. In the most adverse D case, C2 retains all original 34 members but expands to 92 tracts, with 36.96% purity. Retention therefore does not establish a stable small-class boundary. Supplementary Figure S_STAGE7 documents these distinctions. Agreement with the former five-class partition is low (ARI 0.216624); its old interpretations and cluster-specific hotspot findings are not transferred to the new classes.

## Original-Unit Companion Table

Table 4a. Equal-tract recovery means and mapped population totals.

| Class | Tracts | Mapped population | B_480_hr mean (h) | T80 mean (h) | Initial availability mean (%) |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1 | 850 | 3,387,008 | 32.42 | 43.71 | 0.03379 |
| C2 | 34 | 124,158 | 23.60 | 38.50 | 1.81534 |
| C3 | 651 | 2,440,001 | 36.34 | 46.78 | 0.03663 |
| C4 | 752 | 3,085,986 | 33.89 | 44.77 | 0.02421 |

Table 4b. Equal-tract physical/social means and economic/loss-rate medians.

| Class | SOVI mean | Entropy mean | Roof fraction mean | Observed pre-1970 fraction mean | Stock median (million 2022 USD) | ALR_NPCTL median |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | 79.16 | 0.283 | 0.265 | 0.840 | 324.2 | 75.66 |
| C2 | 67.99 | 0.384 | 0.243 | 0.714 | 389.6 | 69.55 |
| C3 | 31.06 | 0.335 | 0.231 | 0.688 | 659.0 | 79.14 |
| C4 | 82.87 | 0.489 | 0.277 | 0.691 | 542.5 | 89.36 |

B is cumulative normalized deficit, not crossing time. T80 crosses the mean tract trajectory. Fractions have the distinct denominators in Methods. Stock and ALR use medians; remaining profile entries use means. Populations are totals from the formal mapping, not FEMA exposure population. Full precision, medians, p10/p90, zeros, and coverage remain in STAGE7_CLUSTER_PROFILES.csv and STAGE7_CLUSTER_PROFILES_LONG.csv in the frozen preview package.
