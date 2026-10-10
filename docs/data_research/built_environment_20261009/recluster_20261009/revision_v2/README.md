# Stage 7 joint recovery/community typology — corrected feature audit

Date: 2026-10-09. Base revision: 031d2c675f8e7d58035d27448be040b809ced086. This is an **exploratory** analytic branch and does NOT supersede the paper's formal Stage 7, figures, recovery archive or manuscript.

## Research question

The goal is a joint electricity recovery, initial supply, grid dependence, socioeconomic and built-environment typology, NOT merely a housing-density map. Accordingly both **T80** and **Init_Supply** appear in EVERY new joint model. Those values must not be stripped out. Because recovery outcomes participate in group formation, comparing those groups' T80 later describes the constructed typology; it cannot establish that physical urban form caused T80.

Urban built environment must be defined independently from historic cluster labels. Candidate constructs are parcel **land-use composition and diversity**, **urban development density and building footprint/intensity**, **physical street form**, **all-use building age/stock**, and optionally residential configuration. Neither old cluster effect sizes nor recovery associations determine whether a physical variable represents built environment.

## Original data independently checked

Re-read actual archived Git LFS Census ACS 80 replicate tables and FEMA NRI v1.19 California original source. Same 2,291 residential tracts:
- Archived NRI_RISK_SCORE vs source RISK_SCORE max absolute difference 1.42e-14; NRI_BUILDVALUE matches exactly; SOVI_SCORE max difference 4.83e-9.
- Census five-plus share and MOE source recomputation differences approximately 1e-16; 211 tracts have >10 percentage point 90% MOE.
- Original 11-coordinate Stage 7 at fixed k=5 exactly reproduces saved labels (adjusted Rand index 1.000).
- Original land-area DBF and retained NLCD zonal ALAND match all 2,315 tracts, max 0 m².

## Key empirical correlation audit

- Overall NRI_RISK_SCORE vs log1p NRI_BUILDVALUE: Pearson r=0.61137.
- Overall NRI_RISK_SCORE vs SOVI_SCORE: r=0.38049.
- OLS R² overall NRI risk from SOVI and log NRI building value: 0.74824 (conditional VIF 3.97).
- OLS R² from other ten existing coordinates: 0.77413 (VIF 4.43).
- FEMA original earthquake-specific ERQK_RISKS is defined in ALL 2,291 tracts; overall vs earthquake risk r=0.97808 and Spearman rho=0.99046. DO NOT add both as independent risk dimensions. FEMA total risk includes expected annual loss, vulnerability and resilience; earthquake risk and earthquake EAL are different candidate scientific constructs from scenario earthquake grid failures.
- 5+ housing-unit fraction vs log housing-unit density: r=0.63115, versus log population density r=0.49343. Age + log housing density explains 55.05% of five-plus share variance. Thus it is not identical to density, but it is a **residential** configuration dimension, not a complete built environment measure.
- Log population density vs log housing unit density: r=0.93723; avoid double-weighting them as two independent density measures.
- CDC 2020 SVI social vulnerability includes 10+ unit housing share among its component characteristics. Archived five-plus vs ten-plus share r=0.95556: a composite can double-count configuration at the level of constructs even if marginal correlation to its overall score is only 0.20.

## Live authoritative source checks

### SCAG parcel land use (2019 snapshot, geography caveats)

Queried the live 2019 Annual Land Use layers, 2,406,373 LA records in each 2019 service variant, with LU19, ACRES, GEOID20, STACK and BF_SQFT. The observed GEOID20 example is a 15-digit 2020 Census **block** ID (not merely a tract); it may support a tract pilot through first 11 digits, but exact spatial area allocation is NOT verified. No null GEOID20 records in this queried county filter. **336,496 STACK>1**, 13.98% of records, indicates overlapping/stacked parcel entries; 2,621 have unknown/specific-plan LU19 (9999/7777). Cannot sum all 2.4m parcel ACRES and call it true classified tract area or entropy. Need true 2019 source/build, geometry-level deduplication, polygon intersections, mixed-use categories and rights-of-way coverage. SCAG 2024 land-use source is a different geometry vintage and is not an automatic historical substitute.

Legacy 2019 layer: https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0
Verified downloadable 2019 ALU v2019.1 historical geodatabase: https://maps.scag.ca.gov/helpr/helpr.gdb.zip

### Building density, coverage and height

Official LARIAC6 **2020** Countywide Building Outlines provide footprint AREA and HEIGHT plus BLD_ID. They are closer in year to 2020 tract geography than 2014 outlines. The 2020 service **does not provide YearBuilt**, so don't imply a complete 2020 all-building age variable from these footprints alone.
2020 authoritative layer: https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0

USGS Annual NLCD 2022 imperviousness has numeric extraction for all 2,315 domain tracts in the retained pilot. BUT the Esri public mirror is beta/non-production, Collection 1.0; the original authoritative USGS Collection 1.2 release has not been compared. Thus imperviousness remains CONDITIONAL despite numeric reproducibility, and it is not building footprint coverage.

### All-use age, not just residential ACS age

Official LA County LARIAC4 2014 building outline service covers **3,118,973** outline records with building height, area, parcel identifiers, UseType, UseCode, and **YearBuilt1**. Querying actual source gives **2,958,436** values between 1800 and 2014 (94.85% of records); 145,242 are null. One verified example has UseType=Industrial and YearBuilt1=1989. This disproves the assertion that all-use building ages are unavailable. However 2014 vintage, incomplete/miscoded year values, building-to-parcel relationships and current stock mismatch require QA, especially when joining to 2020 outlines. The multi-year assessor roll also has YearBuilt and UseCode, but it counts tax assessment observations, not unique buildings.
2014 outlines: https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1
Assessor roll: https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2021_Table/FeatureServer

### Further candidates

EPA SLD provides development density, land-use **activity** mix, street intersection density and job/transit accessibility. It has a different historical block-group geography and older activity years. Employment-household entropy computed from counts is not parcel-land-use entropy; to combine with 2020 tracts, extensive donor counts must be reallocated and entropy recomputed. Street intersection density is conceptually distinct from ELECTRICAL substation topology.
EPA source: https://www.epa.gov/smartgrowth/smart-location-mapping

## Actual outcome-inclusive exploratory clustering

All models use the same 2,291 residential tracts and both required T80 and Init_Supply. K-means Euclidean, standardized transformed coordinates (log1p density/building value), k=2..8, minimum 2% group, 40 restarts, 12 random 80%-training refits. Joint alternatives use equal total squared-distance budgets for recovery, grid, built/urban and social/hazard blocks. Historic labels NEVER used to choose new features/k.

| Model | Selected k | Silhouette | Sizes |
| --- | ---: | ---: | --- |
| Archived 11 original coordinates (new k selection) | 3 | 0.16377 | 212/1333/746 |
| Built/urban housing proxy + NRI risk in joint typology | 2 | 0.14933 | 1441/850 |
| Same without NRI risk | 2 | 0.17269 | 834/1457 |
| Population instead of housing density | 2 | 0.13897 | 1419/872 |
| Exclude 5+ housing share | 2 | 0.14823 | 910/1381 |
| Exclude residential age | 2 | 0.17724 | 1482/809 |
| Impervious pilot added (NOT source-verified) | 2 | 0.13335 | 1416/875 |

Risk-present vs risk-absent labels ARI **−0.00261**: NRI choice materially changes the scientific partition. Do not use higher silhouette alone as a reason to keep/drop NRI. Original saved k=5 remains reproducible and is not supplanted merely because the separate k-search picks three.

Init_Supply distribution is severely skewed: 1,529/2,291 exact zero, median 0, p95 0.0025, p99 0.01733, max 0.0245. The user's requirement to RETAIN initial service is respected, but rare nonzeros may influence z-score K-means; requires an explicit transformation sensitivity, not deletion.

## What is decided and what is not

1. YES: T80 and Init_Supply remain in ALL new joint-clustering inputs.
2. YES: NRI risk was independently verified against the original FEMA source and jointly assessed for correlation; both inclusion/exclusion variants were actually clustered; additionally both earthquake-only risk and quake EAL original values are available for every residential tract.
3. YES: housing five-plus is non-identical but substantially associated with density; it must NOT be treated as the principal urban-form indicator or as land-use diversity.
4. YES: actual 2019 SCAG land-use data, LARIAC 2020 footprint and historical all-use building age sources exist; previous failure to search them was an incomplete research audit.
5. NO: the paper's final **built-environment domain** has NOT yet passed parcel geometry and building-footprint QA; the proposed joint 2-cluster partitions are *exploratory only*. Final promotion requires measured land-use composition and a defensible physical density (footprint/urbanized) input. It also needs a stated domain-budget design and sensitivity to skewed Init_Supply.
6. NO: no existing formal Stage 7 tables, manuscript figures, protected originals or restoration simulations have been overwritten. All outputs here are on an isolated research branch.

See feature_audit.py, quake_risk_audit.py, source_probe.py, recluster_v2.py and results/ for input SHA-256s, exact calculations, new labels, k diagnostics, model sensitivity, full profiles and stage-specific executable logs. CSV products use Git LFS.
