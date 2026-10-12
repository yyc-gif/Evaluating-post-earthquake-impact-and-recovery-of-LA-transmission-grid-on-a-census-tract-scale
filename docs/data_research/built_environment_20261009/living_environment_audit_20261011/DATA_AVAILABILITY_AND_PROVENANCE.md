# Living-environment measurements: availability and provenance

This package audits measurements only. CORE3/W1 is an archived reference and is not an approved final feature set. No clustering, weight selection, recovery computation, manuscript editing or promotion was performed. The isolated branch is analysis/stage7-living-environment-audit-20261011, based on e4497dcf2182535ef1eda9612ca45c43704c1a6f.

## Exact cohorts and inherited inputs

The unchanged model universe contains 2,315 GEOIDs, the residential master 2,291, and the complete archived reference 2,287. Every comparison joins on an11-digit string GEOID. Ordered memberships are in COHORT_IDENTITIES.npz and BASELINE_IDENTITY_QA.json. The four geometry-unresolved residential records remain in the master and have their published non-geometric values preserved: 06037189703, 06037301601, 06037301602, 06037404600. Their old geometry exclusion status is not removed and no class labels are assigned. New published canopy values for them do not validate their existing physical land masks.

Reused parent values and source SHA-256:

- candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv: e69f06c5ac64bcecb75c9b3b33814e456480463b8c1c58e8908a8545279912c7. Housing configuration, EMC2022, frozen SOVI and original population/density remain numerically unchanged.
- final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv: 340f7fc2d50ecae003379b7c1c2d6b075859e31b6456b48db8d3e95ab85ed853. Used only for residential and complete-reference identities; cluster labels and recovery outcomes were not read for admission.
- validation/sources/B25024_06.csv.zip: 4ceecc607150978ce95e846cc3f9d6fb67e1249523cab87c737251343efdeb3d; official cached2022 ACS California tract VRE, not downloaded again.
- validation/ACS_TRACT_VALIDATION.csv: 7464ca9a0299cb1771ec00c690ccd632f900907aa18cad6f1cea4030741a18f0; original housing estimates, boundary rules and MOEs reproduced within 1e-13.

Full original and new source byte hashes, URLs, request parameters and timestamps are in INPUT_HASHES.json, SOURCE_URLS_AND_CHECKSUMS.csv and ACQUISITION_RECORDS.json. HTTP success is recorded separately from numerical validity. Software versions are in SOFTWARE_VERSIONS.json.

## A. Published2022 urban tree canopy

[USFS/CALFIRE tract layer](https://services1.arcgis.com/gGHDlz6USftL5Pau/ArcGIS/rest/services/Statistics_by_Census_Tract_wCalES4/FeatureServer/0) supplies FIPS, PctCan22, CanoAcr22, AREA22 and PctCan18. Its2,486 LA records have unique11-digit GEOIDs. The [2022 raster service](https://tiles.arcgis.com/tiles/gGHDlz6USftL5Pau/arcgis/rest/services/UrbanTreeCanopy_CA2022/MapServer) and official CALFIRE launch material identify0.6-m2022 NAIP imagery and a deep convolutional model, analyzed for2020 Census urban areas. Publication/update dates in2025 are not observation years. The related2012 viewer and a different UFIA urban-area service were investigated but excluded. Field aliases contain inconsistencies; field identities and actual arithmetic, rather than an alias alone, define the values.

The exported value is PctCan22/100. Numerically CanoAcr22/AREA22 =0.00024711 (the source's approximate acre-per-m2 conversion), so AREA22 is canopy-class area, not the total tract denominator. Inferring the analysis denominator as AREA22/(PctCan22/100) agrees closely with source polygon area in most records, but 22 of 2,287 reference records have a ratio below0.99. This is a diagnostic, not a new admission cutoff. The exact urban clipping/zone rule and LA-specific classification error are not supplied by the inspected metadata. Census 2020 urban geometry provides a support check, not proof of every denominator; observed edge discrepancies remain in CANOPY_ANALYSIS_SUPPORT_AUDIT.csv. No canopy pixels were reclassified or substituted.

Comparing source polygons with original whole-tract geometry gives 42 reference records below0.90 IoU. Much of this comparison includes water in the frozen polygon. Reusing the exact previously validated land-mask bytes reduces that count to 21; land IoU median = 0.995450, minimum = 0.797333. Residual differences are explicitly retained, not labeled automatically as new-vintage boundary changes. CANOPY_GEOGRAPHIC_SUPPORT_FLAGS.csv gives exact GEOIDs, geometry overlap, displacement and population. No geometry, mapping or existing environmental measurement changed.

All 2,291 residential GEOIDs have published canopy values. The two absent full-domain records are06037980020 and06037980026, outside the residential cohort. Urban-analysis/whole-tract canopy remains an ecological area measurement. It does not identify where residents live, shade along pedestrian routes, or personal shade exposure. Large unoccupied areas and partial urban coverage can change its denominator and interpretation.

## B. Published parks proximity

[USC NDSC2022 Parks Access](https://la.myneighborhooddata.org/2023/03/parks-access/) has a working download link. The actual CSV contains 2,498 unique LA2020 tract identities, year2022, population denominator, fractional all/good access counts and corresponding percentages. geoid20 lost one leading zero in its serialized numeric form; restoration to11 digits reproduces the complete GEOID field exactly. The population denominator matches the canopy layer's2020 Census population exactly on 2,313/2,313 comparable model records. This is not the frozen restoration weighting population, which remains untouched.

Published percentages reproduce100*access_count/denom_total_pop within 0.00000822 percentage points. Tiny float-storage overshoots above100 are retained and flagged (all parks:151; good parks:29 full-domain records), rather than silently clipped. Five zero-population full-domain tracts have undefined proportions; all residential/reference tracts have usable published values.

The documentation calls the result a percentage of residents within half a mile, but describes only park buffers overlaid on tracts. Neither the download nor retrieved county reports specify block/population-surface weighting or an exact area-based allocation formula. Fractional counts and a population denominator cannot distinguish genuine population weighting from tract population multiplied by a buffered-area fraction. Consequently the exported variable is named published_fraction, not verified resident access. No substitute park-access calculation was constructed. A geometric half-mile buffer is not half-mile pedestrian-network accessibility. Good Parks additionally depends on condition ratings whose rule, date and objectivity are not established for this download; it remains separate and descriptive.

## C/D. ACS heating and housing configuration

Both represent2018-2022 ACS 5-year estimates on 2020 tract geography, not a single2022 census of buildings. Electric heating = B25040_004E/B25040_001E, electricity as principal heating fuel divided by occupied housing units. Housing5+ = sum(B25024_006E...009E)/B25024_001E, units in5+unit structures divided by all housing units. Their denominators differ; neither is a fraction of physical buildings.

The Census point-estimate API redirected to Missing Key HTML despite HTTP200. Its bytes are recorded as a failed numerical route. The official [B25040 VRE archive](https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25040_06.csv.zip) was successfully retrieved and contains original ESTIMATE/MOE fields and80 corresponding variance replicates. The [official 2022 VRE documentation](https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/documentation/5-year/2018-2022_Variance_Replicate_Table_Documentation.pdf) supports covariance-aware derived-ratio uncertainty. Existing housing VRE estimates were independently reproduced and retained.

For valid ratio p=N/D, SDR variance = (4/80)*sum_r(p_r-p)^2, with the same indexed numerator/denominator replicates. Undefined replicate denominators follow the official rule p_r=0. For p=0, p=1 or zero replicate SE, official boundary variance is used: p*=min(0.5,2.3*AW/D), SE=sqrt[p_ast*(1-p_ast)*AW/D], with archived California average weight AW=16. MOE90=1.645*SE. Display confidence bounds are truncated to[0,1] only for presentation; raw estimates, SE and MOE remain unchanged. No approximation that ignores ratio covariance replaces the original housing method.

| candidate              |    n |   median_MOE90_pp |   P90_MOE90_pp |   MOE90_gt_5pp_n |   MOE90_gt_10pp_n |   MOE90_gt_10pp_percent |   CV_gt_30percent_n |   undefined_CV_zero_estimate_n |   boundary_variance_n |   denominator_CI90_includes_zero_n |   zero_replicate_denominator_n |
|:-----------------------|-----:|------------------:|---------------:|-----------------:|------------------:|------------------------:|--------------------:|-------------------------------:|----------------------:|-----------------------------------:|-------------------------------:|
| electric_heating_share | 2287 |            8.4818 |        11.7253 |             2175 |               568 |                 24.8360 |                 259 |                              3 |                     5 |                                  4 |                              0 |
| housing_5plus_share    | 2287 |            6.7482 |         9.8896 |             1618 |               211 |                  9.2261 |                 585 |                            153 |                   158 |                                  4 |                              0 |

Five-/ten-percentage-point MOE and30% CV flags are transparent diagnostic thresholds, not exclusion gates. No high-MOE observation is deleted. CV is undefined when p=0; such cases remain in the master. Full-domain zero denominators produce24 undefined heating and23 undefined housing fractions, mostly special nonresidential9800 tracts, with every exact GEOID in MISSING_INVALID_GEOIDS.csv. No null was replaced by zero.

Heating measures dependence on electricity for principal residential heating only. It is not total electricity dependence, cooling prevalence, backup-power availability, current demand or an outage consequence. Housing5+ describes residential unit configuration, not comprehensive built environment.

## Shared sources and SOVI components

Frozen FEMA v1.19 SOVI remains unchanged. Its CDC 2020 source includes housing/transportation information. [CDC 2020 dictionary](https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/08/SVI2020Documentation_08.05.22.pdf) defines EP_MUNIT=(DP04_0012E+DP04_0013E)/E_HU*100, the10+unit share from 2016-2020 ACS. The5+measure uses a nested housing category and an overlapping later survey period. This is conceptual and source overlap, not an exact algebraic duplicate across releases.

The current official CDC public download API provided actual California 2020 data after the old static URL failed. Only raw housing/transportation components are used diagnostically. California RPL rankings are state percentiles and are not substituted for frozen national SOVI. Component uncertainty is not estimated by treating the two releases as independent samples. The80 ACS replicate correlations are measurement-sensitivity results, not80 independent tract cohorts or a confidence interval for spatially dependent tract correlations.

## Failures and unresolved evidence

- Census B25040 point API: HTTP200 Missing Key HTML; replaced by official VRE numerical file without bypassing authentication.
- Old CDC static route:404; another route returned HTML; neither was parsed as data. Official public webapi supplied actual CSV.
- USC guessed dataset metadata endpoint:404. Primary numeric download works, but spatial apportionment and Good Parks rating details remain unresolved.
- Optional ArcGIS item/data was empty; unrelated old services were not numerical substitutes.
- Canopy partial-area definition, residual land geometry differences and local classification uncertainty remain qualified. Count/coverage is not validation accuracy.

No source acquisition failure was converted into a fabricated measurement. The audit is complete as a measurement decision package; the specific unresolved definitions prevent unconditional admission of park proximity and canopy as resident-level primary coordinates.
