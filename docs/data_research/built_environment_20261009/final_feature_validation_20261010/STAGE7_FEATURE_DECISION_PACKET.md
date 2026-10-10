# Stage 7 candidate feature decision packet — 2026-10-10

This package is an exploratory joint recovery–service–grid–built-environment–social–multi-hazard loss comparison. It does not replace stored Stage 7 labels, manuscript inputs, or figures. The candidate matrix preserves all 2,291 original residential GEOIDs and all 2,315 full-domain source identities. Scientific baseline: `031d2c675f8e7d58035d27448be040b809ced086`; independently reviewed feature-gate parent: `bd913b91c9c73d0b92fa327c28660d74197b6259`; prior FEMA evidence: `65f388f9710566ffa845808bd7b10503de4da608`.

## Land-mask disposition

Four demonstrable mask errors were corrected by actual SCAG/LARIAC reintersection of cached source geometries. Eight cases were explained by the 2020 statistical-water definition versus archived tract ALAND/AWATER versions, retaining exact existing numerators/denominators and recording that difference. Six full-domain cases remain spatially unresolved, including four residential members. Projection and cached-area arithmetic do not account for these discrepancies. No polygon was rescaled to ALAND and no Census field was changed.

|    tract_id | residential_member   | status                                               |   before_relative_error |   after_relative_error |   after_vs_census2020_relative_error |
|------------:|:---------------------|:-----------------------------------------------------|------------------------:|-----------------------:|-------------------------------------:|
| 06037404600 | True                 | UNRESOLVED_MIXED_WATER_FEATURE                       |                -0.00604 |               -0.00604 |                             -0.00604 |
| 06037980031 | True                 | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                 0.00503 |                0.00503 |                             -0.00000 |
| 06037980023 | False                | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                -0.44842 |               -0.44842 |                              0.00000 |
| 06037106112 | True                 | CORRECTED_PURE_STATISTICAL_LAND_REMOVAL              |                -0.02274 |               -0.00000 |                             -0.00000 |
| 06037189703 | True                 | UNRESOLVED_MIXED_WATER_FEATURE                       |                -0.00840 |               -0.00840 |                             -0.00838 |
| 06037311601 | True                 | CORRECTED_ZERO_WATER_TRACT                           |                -0.01314 |                0.00000 |                              0.00000 |
| 06037121010 | True                 | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                -0.05357 |               -0.05357 |                             -0.00115 |
| 06037122000 | True                 | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                -0.07195 |               -0.07195 |                              0.00074 |
| 06037980009 | False                | UNRESOLVED_MIXED_WATER_FEATURE                       |                -0.00861 |               -0.00861 |                             -0.00924 |
| 06037301601 | True                 | UNRESOLVED_MIXED_WATER_FEATURE                       |                -0.01252 |               -0.01252 |                             -0.01252 |
| 06037301602 | True                 | UNRESOLVED_MIXED_WATER_FEATURE                       |                -0.01065 |               -0.01065 |                             -0.01065 |
| 06037311700 | True                 | CORRECTED_ZERO_WATER_TRACT                           |                -0.00594 |                0.00000 |                              0.00000 |
| 06037460401 | True                 | CORRECTED_PURE_STATISTICAL_LAND_REMOVAL              |                -0.08241 |                0.00000 |                             -0.00095 |
| 06037577504 | True                 | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                 0.01679 |                0.01679 |                             -0.00000 |
| 06037621204 | True                 | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                 0.02169 |                0.02169 |                             -0.00000 |
| 06037980006 | False                | UNRESOLVED_MIXED_WATER_FEATURE                       |                -0.02211 |               -0.02211 |                             -0.02228 |
| 06037576602 | True                 | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                 0.04961 |                0.04961 |                             -0.00000 |
| 06037577501 | True                 | RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE |                 0.00686 |                0.00686 |                              0.00001 |

The unresolved cases contain mixed land/water within named river hydrography; whole-feature ALAND/AWATER attributes do not locate the statistical-land portion. Even a close total-area fit from deleting a complete river is insufficient spatial evidence. Their land entropy, footprint fraction and original2014 age candidate remain null. Specific feature intersections, river names, both Census attribute versions and boundary symmetric differences appear in LANDMASK_18_TRACT_RESOLUTION.csv and LANDMASK_HYDRO_FEATURE_INTERSECTIONS.csv. Pure AWATER=0 hydrography and tracts reported as AWATER=0 in both versions are the only geometry corrections.

Actual primary complete cases: **2287**. Also delivered: the explicitly named **2,276-row legacy complete-case** cohort and its controlled partition comparison. Four remaining residential records are not imputed or assigned new exploratory cluster labels.

Census documentation explains that intermittent water, swamps and glaciers may count as statistical land, while area hydrography includes those features. [Census glossary, Area Measurement](https://cdn.www.census.gov/programs-surveys/geography/about/glossary.html), [2020 TIGER/Line technical documentation, section4.10 and AppendixJ](https://www2.census.gov/geo/pdfs/maps-data/data/tiger/tgrshp2020/TGRSHP2020_TechDoc.pdf). Only18 official [2020 tract geometries](https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Tracts_Blocks/MapServer/0) were retrieved for boundary comparison. No SCAG/LARIAC source records were downloaded again.

## Land-use measurement uncertainty

Entropy is eleven-class normalized **classified-land entropy**, not a complete all-land measure. Median classified coverage on the current complete cohort is 75.107%. Missing-to-transport, dominant-category and proportional scenarios are hypothetical allocations, never observed classifications. Formal unconstrained lower/upper entropy bounds allow any allocation over the eleven categories; they are not confidence intervals.

| scenario             |    n |   spearman_vs_observed |   median_abs_entropy_change |   p95_abs_entropy_change |   p95_abs_percentile_rank_change |
|:---------------------|-----:|-----------------------:|----------------------------:|-------------------------:|---------------------------------:|
| missing_proportional | 2287 |                1.00000 |                     0.00000 |                  0.00000 |                          0.00000 |
| missing_to_dominant  | 2287 |                0.98620 |                     0.05430 |                  0.10735 |                          0.10131 |
| missing_to_transport | 2287 |                0.96808 |                     0.12798 |                  0.20263 |                          0.14346 |
| observed_classified  | 2287 |                1.00000 |                     0.00000 |                  0.00000 |                          0.00000 |

Proportional allocation preserves entropy mathematically. Concentrating missing area in the dominant category lowers it; assigning transport can raise or lower it. Strong rank correlation does not remove coverage uncertainty. The explicit lowest-coverage-quartile exclusion is a diagnostic sample perturbation, not an adopted threshold, and has its own sample hash. An85% primary cutoff was not imposed.

## Building age

Primary candidate: original2014 all-use valid-age footprint area share, never the sparse 2014-to-2020 transfer. Residential median valid-age coverage is **95.251%**; median missing-age bound width is **0.047**. Strict2020 transfer median coverage is **4.352%**. Lower bound = known pre1970 area / all footprint area; upper = (known pre1970 + unknown-age area) / all area. These represent unknown-age scenarios, not estimated construction years or CI. ACS is housing-unit weighted residential age, a scientifically different construct.

| use            |   tracts |   pooled_missing_area_fraction |
|:---------------|---------:|-------------------------------:|
| Commercial     |     2232 |                        0.05277 |
| Government     |     2099 |                        0.95804 |
| Industrial     |     1818 |                        0.05627 |
| Institutional  |     1912 |                        0.07223 |
| Irrigated Farm |       71 |                        0.19119 |
| Miscellaneous  |      878 |                        0.75019 |
| Recreational   |      826 |                        0.10307 |
| Residential    |     2291 |                        0.01031 |
| nan            |     1823 |                        0.98704 |

Government missingness is not treated as residential or zero. By-use unions cannot be added as though mutually exclusive overall areas. Age lower/upper, ACS replacement and no-age comparisons all preserve the remaining coordinate values and common primary tract sample.

## Controlled input and weighting

Primary candidate D retains raw B_480_hr, mandatory Init_Supply, four unchanged grid descriptors, classified-land entropy, union footprint coverage, original2014 all-use observed-age share, SOVI_SCORE, log1p building stock and ALR_NPCTL. EAL alternative replaces stock and rate with EAL_SCORE under exactly the same total loss/exposure budget. Published FEMA scores stay on their original scales before standardization. SOVI remains in every configuration. Neither ALR nor EAL is pure hazard; applicable multi-hazard FEMA losses are locally earthquake-dominated. The previous FEMA interpretation is reused, not recomputed as a new release.

Inherited five parent-domain budgets: recovery+initial service2/11, grid4/11, physical2/11, social1/11, loss/exposure2/11. Equal-domain alternative assigns0.2 to each of those same five parent domains. The three physical constructs share the physical total equally. Coordinate multiplier is sqrt(domain budget / coordinate count). Omitting age redistributes that fixed physical budget; it does not weaken the whole physical domain. This comparison is explicitly equal **five parent domains**, not equal weight to nine conceptual constructs. Housing5+ remains diagnostic. Population density is a separate demographic sensitivity receiving half the existing exposure-domain budget; it is not silently another physical-density feature.

B is mean realization-normalized deficit integrated0–480h; T80 is first crossing of80% by the mean tract service trajectory, not the average realization T80. AUC480=1−B/480 is redundant and excluded. Raw versus log1p B is a preprocessing sensitivity. Source/units/vintage/transformation and quality flags are listed per coordinate in FINAL_FEATURE_DEFINITIONS_AND_QA.csv.

## Optimization stability versus scientific sensitivity

20 models, each20 independent seeds42–61, n_init100, direct weighted-coordinate KMeans for every k2–8. Each seed selects k by the normalized endpoint-chord elbow, never maximum silhouette. Fixed k5 is separately retained. No PCA or old labels enter this exploratory method. Each model/seed/k record is unique; proportional entropy is a same-definition diagnostic, not extra independent replication. Seed ranges are optimization variability and are not tract-sampling confidence intervals.

| model                             |          n |   ari_median |   ari_min |   silhouette_mean |   minimum_cluster_size |
|:----------------------------------|-----------:|-------------:|----------:|------------------:|-----------------------:|
| D__inherited                      | 2287.00000 |      0.97372 |   0.88381 |           0.14109 |               34.00000 |
| EAL__inherited                    | 2287.00000 |      0.98187 |   0.92354 |           0.15819 |               35.00000 |
| D_T80__inherited                  | 2287.00000 |      0.99712 |   0.98687 |           0.13811 |               34.00000 |
| D_logB__inherited                 | 2287.00000 |      0.96619 |   0.86330 |           0.13925 |               34.00000 |
| D_ACS_age__inherited              | 2287.00000 |      0.99353 |   0.97993 |           0.14149 |               34.00000 |
| D_no_age__inherited               | 2287.00000 |      0.95716 |   0.90388 |           0.15199 |               34.00000 |
| D__equal_five_domains             | 2287.00000 |      1.00000 |   0.99903 |           0.14837 |               34.00000 |
| EAL__equal_five_domains           | 2287.00000 |      0.99699 |   0.99405 |           0.16283 |               34.00000 |
| D_T80__equal_five_domains         | 2287.00000 |      1.00000 |   1.00000 |           0.12750 |               34.00000 |
| D_logB__equal_five_domains        | 2287.00000 |      0.98422 |   0.95261 |           0.13718 |               34.00000 |
| D_ACS_age__equal_five_domains     | 2287.00000 |      0.98567 |   0.96436 |           0.14524 |               34.00000 |
| D_no_age__equal_five_domains      | 2287.00000 |      0.99592 |   0.98357 |           0.14835 |               34.00000 |
| D_entropy_transport__inherited    | 2287.00000 |      0.88273 |   0.83773 |           0.14178 |               34.00000 |
| D_entropy_dominant__inherited     | 2287.00000 |      0.98133 |   0.92424 |           0.14215 |               34.00000 |
| D_entropy_proportional__inherited | 2287.00000 |      0.97372 |   0.88381 |           0.14109 |               34.00000 |
| D_age_lower_bound__inherited      | 2287.00000 |      0.98447 |   0.95997 |           0.14333 |               34.00000 |
| D_age_upper_bound__inherited      | 2287.00000 |      0.95724 |   0.87275 |           0.13998 |               34.00000 |
| D_pop_density__inherited          | 2287.00000 |      0.98339 |   0.96936 |           0.14034 |               34.00000 |
| D_legacy2276__inherited           | 2276.00000 |      0.94996 |   0.87895 |           0.14125 |               34.00000 |
| D_lowcoverage__inherited          | 1715.00000 |      0.99225 |   0.88156 |           0.13667 |               18.00000 |

Between-model results (same seed, common tract IDs):

| model                             |   n_common |   ari_median |   ari_min |
|:----------------------------------|-----------:|-------------:|----------:|
| D_ACS_age__equal_five_domains     |       2287 |      0.93024 |   0.91848 |
| D_ACS_age__inherited              |       2287 |      0.78183 |   0.75633 |
| D_T80__equal_five_domains         |       2287 |      0.65928 |   0.65928 |
| D_T80__inherited                  |       2287 |      0.65907 |   0.64649 |
| D_age_lower_bound__inherited      |       2287 |      0.89780 |   0.86233 |
| D_age_upper_bound__inherited      |       2287 |      0.95109 |   0.86168 |
| D_entropy_dominant__inherited     |       2287 |      0.88628 |   0.87589 |
| D_entropy_proportional__inherited |       2287 |      1.00000 |   1.00000 |
| D_entropy_transport__inherited    |       2287 |      0.81826 |   0.79700 |
| D_legacy2276__inherited           |       2276 |      0.96679 |   0.87659 |
| D_logB__equal_five_domains        |       2287 |      0.68740 |   0.65540 |
| D_logB__inherited                 |       2287 |      0.94161 |   0.87260 |
| D_lowcoverage__inherited          |       1715 |      0.89502 |   0.85301 |
| D_no_age__equal_five_domains      |       2287 |      0.71819 |   0.71684 |
| D_no_age__inherited               |       2287 |      0.71935 |   0.68904 |
| D_pop_density__inherited          |       2287 |      0.21795 |   0.20931 |
| EAL__equal_five_domains           |       2287 |      0.64745 |   0.64344 |
| EAL__inherited                    |       2287 |      0.63451 |   0.61956 |

The fixed-k5 D optimization median pairwise ARI is 0.97372. Scientific stability is assessed separately through measurement, risk construct, weights, k, age definition and spatial sample changes. Twenty spatial block deletions yield D/inherited full-cohort prediction ARI median **0.75906**, minimum **0.30045**. The identical20 deletion sets are also evaluated for EAL and both domain budgets (80 fits total).20km projected centroid blocks remove10% of occupied blocks, refit scaling and clustering on retained tracts, and predict the entire complete cohort. This is a spatial sensitivity diagnostic, not new independent data or spatially representative validation. Descriptive profile quantiles are across tracts, not CI.

Simultaneous-coordinate VIF maxima: D **2.2338**, EAL **2.2087**. VIF diagnoses redundancy, not scientific validity.

## Recommendation and remaining author decisions

Use the specified D input as the provisional construct-driven primary candidate: it keeps economic stock and normalized multi-hazard loss distinct, retains the mandated social and immediate-service dimensions, and combines land-use mix, physical coverage and all-use2014 age rather than a residential-density typology. Retain EAL as a combined loss/exposure sensitivity. The raw B coordinate is interpretable in equivalent complete-service-loss hours; T80 and log1p B remain mandatory comparison evidence. This recommendation is not based on old labels or silhouette ranking.

Do not yet publish a complete2291-label replacement. Resolve the four remaining residential river masks or explicitly approve the documented complete-case domain. Classified coverage and all-use age incompleteness remain substantive uncertainty even when optimizer seeds are stable. Author decisions are required for inherited versus equal parent-domain weights, selected k, all-use2014 age versus ACS/no-age, and treatment of coverage uncertainty. Disagreement among these partitions is evidence of construct sensitivity, not a failure to search long enough. No cluster archetypes or causal claims were selected from the results.

All original physical inputs, schedules, trajectories, GA results, source tables, formal Stage7 labels, manuscript and figures remain unchanged. New calculations are candidate feature corrections and exploratory clustering only. Hash preservation and tests are reported in PRESERVATION_FINAL_QA.json and VERIFICATION_RESULTS.json.
