# Built-Environment Indicator Research

Audit date: 2026-10-09. Repository: `yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale`.
Latest verified HEAD: `b1030f839d522fed4af21e424472e3f8b076797b`; branch: `revision/reviewer-driven-core-rebuild-v2`. Initial preservation snapshot was taken at `73ef343f21e998eb9c9ccf7797d1aa0119d15c04`; the intervening GA-method commit leaves all inspected Stage 7 code/data and protected figures unchanged.

## Scope and Evidence Boundary

The target is pre-event residential configuration, constructed-surface intensity and land-use composition, not another earthquake damage or loss model. No fragility, PGA/MMI, damage probability, retrofit assumption, liquefaction, fault-distance, electric-demand or station-capacity indicator is introduced. The 2022 reference year matches the existing ACS housing-age input, not the date of the historical earthquake scenario.

The inspected formal Stage 7 export is `Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/`: 2,315 study tracts, including 2,291 residential-typology tracts and 24 excluded from residential classification. The saved feature matrix uses the single `2pc50` scenario: T80 comes from saved Stage 5 tract KPIs and Init_Supply from Stage 1 initial supply. Counts and correlations below are from an independent pilot against these saved IDs and labels, not a rerun of Stage 7 or an average of four scenarios. Older expanded-script logs with 14 or 16 variables are not the current matrix.

Actual numerical tract extraction was completed for ACS B25024. EPA source records and a geographic relationship feasibility check were retrieved, but no EPA tract activity indicator was calculated. NLCD numeric raster and SCAG parcel overlays were not extracted. Documentation coverage, source-record presence, geographic overlap and valid-indicator coverage are reported separately.

## 1. Residential Development Configuration

### Source, Formula and Meaning

Use **ACS 2018-2022 five-year Detailed Table B25024, Units in Structure**, published December 7, 2023. Its universe is housing units, including occupied and vacant units. The indicator is the fraction of units located in structures containing at least five units, not the fraction of buildings, occupied households, floors or tract area. It does not identify height, construction material, code compliance or seismic capacity. [Census field dictionary](https://api.census.gov/data/2022/acs/acs5/groups/B25024.html), [2022 release documentation](https://www.census.gov/programs-surveys/acs/news/data-releases/2022/release.html).

| Component | Estimate | Corresponding 90% MOE | Category |
| --- | --- | --- | --- |
| Denominator D | B25024_001E | B25024_001M | Total housing units |
| Numerator bin | B25024_006E | B25024_006M | 5-9 units |
| Numerator bin | B25024_007E | B25024_007M | 10-19 units |
| Numerator bin | B25024_008E | B25024_008M | 20-49 units |
| Numerator bin | B25024_009E | B25024_009M | 50 or more units |

`N = E006 + E007 + E008 + E009`; `S_5plus = N / D`, defined only when `D > 0` and all components are valid. Retain the total denominator, including single-unit structures, 2-4-unit structures, mobile homes and other housing categories; do not normalize over only apartments. Group quarters are not ordinary housing units.

Approximate uncertainty: `M_N = sqrt(M006^2 + M007^2 + M008^2 + M009^2)`; `M_S = sqrt(M_N^2 - S_5plus^2 * M001^2) / D`. When the radicand is negative, use the Census ratio fallback with a plus instead of a minus and flag that choice. Multiply the share and its MOE by 100 for percentage/percentage-point display. These are approximate **90% sampling MOEs**, not comprehensive errors; component covariance is unavailable in this pilot. Retain the original analytic MOE even when it exceeds 1; displayed interval endpoints can be bounded to [0,1] without concealing the unreliability flag. [Census ACS handbook, chapter 8, equations 1, 6 and 7](https://www.census.gov/content/dam/Census/library/publications/2018/acs/acs_general_handbook_2018.pdf).

### Actual Coverage and Compatibility

The Census API data request returned a missing-key HTML response, so extraction used the official public [2022 table-based Summary File](https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acsdt5y2022-b25024.dat), not an unofficial substitute. Summary-file names such as `B25024_E006` are mapped to API-style `B25024_006E`. The preserved LA subset contains 2,498 tract records; all 2,315 study IDs matched uniquely.

| Check | Actual result |
| --- | --- |
| Study source-record presence | 2,315 / 2,315 |
| Study defined housing share | 2,292 / 2,315 |
| Residential defined housing share | 2,291 / 2,291 |
| Zero housing denominator | 23 study tracts; missing share, not zero |
| Positive housing but outside residential typology | 06037277400: 15 units; zero formal population |
| Missing estimate/MOE cells in study extract | 0 |
| B25024 total versus existing B25034 housing total | 0 mismatches across 2,315 |
| Sum of ten structure bins versus total | Exact equality for every study tract |

Both housing tables use the same ACS five-year period and housing-unit universe. The current age numerator sums B25034_008E through B25034_011E (pre-1970); its denominator is B25034_001E. Matching IDs and totals establish compatibility of this extract, not a blanket guarantee for other ACS vintages or independently acquired geometries. [B25034 dictionary](https://api.census.gov/data/2022/acs/acs5/groups/B25034.html).

For the 2,291 residential tracts, the median 5+ share is **25.52%**, with an interquartile range of **8.69%-55.08%**. The median share MOE is **8.65 percentage points**; 868 tracts (37.89%) exceed 10 points and 27 exceed 20 points. Eleven have fewer than 100 housing units; four have denominator confidence intervals including zero; three have share MOEs above 1; two use the ratio fallback. All are retained and flagged, not silently imputed or removed. These counts apply to the residential universe, not the full-domain subset.

Effort: low after downloading the approximately 48 MB national table. Tract joining and all pilot calculations take seconds locally; no spatial overlay is required. Its overlap with housing age and population density is moderate, and the existing social composite contains a related 10+ unit variable. See the redundancy report. It is ready for **descriptive cluster profiles with uncertainty**, not automatically ready for an additional unweighted clustering coordinate.

## 2. Urbanized Land-Cover Intensity

### Source and Definition

Preferred source: **USGS Annual NLCD Collection 1.2, Fractional Impervious Surface, mapping year 2022**. The current release is June 30, 2026 and spans 1985-2025. Distinguish the 2022 observation year, original Annual NLCD suite release in 2024, and collection version released in 2026. Pin the actual downloaded version rather than citing an unversioned viewer. [USGS product archive](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-land-cover-annual-nlcd-collection-1-fractional-impervious), [product DOI](https://doi.org/10.5066/P14D8CJB).

The product estimates constructed impervious surface fraction, 0-100%, within 30 m pixels. Roads, parking, paved yards and rooftops contribute; vegetation in developed land remains distinct. It is **not building footprint coverage, building density, floor area, structural vulnerability or earthquake exposure**. USGS distributes GeoTIFFs on an Albers Equal Area Conic grid using WGS84; tiled bundles include all mapping years. [USGS Annual NLCD product suite](https://www.usgs.gov/centers/eros/science/annual-nlcd-product-suite), [USGS data-access options](https://www.usgs.gov/centers/eros/science/annual-nlcd-data-access).

Proposed tract measure:

`I_t = sum_p(a_tp * f_p / 100) / sum_p(a_tp)`

Here `a_tp` is the exact intersection area of tract land with valid pixel p, and `f_p` is its percentage value. Include valid zero-impervious land, not only pixels classified as developed. This measures overall tract urbanization; restricting the denominator to developed land would instead measure intensity conditional on development and must have a different name.

Before extraction, define a spatial land mask, not just the tract's scalar ALAND attribute; exclude open-water area consistently and disclose whether a companion NLCD land-cover water mask or verified tract/water polygons define land. Inspect actual GeoTIFF NoData and special-value metadata. Do not assume that masked/non-developed cells are valid zero without confirming product encoding. Report valid land area / tract land area, minimum coverage, invalid pixels and small-tract sensitivity. Use native equal-area pixel intersections; neither an unweighted center-pixel average nor all-touched counting is equivalent.

### Availability, Quality and Effort

Official CONUS extent includes LA. Retrieved USGS WMS capabilities advertise a time dimension including 2022, but WMS is a visualization interface: rendered image colors are not numerical impervious observations. An attempted S3 bucket listing returned HTTP 403; this does **not** establish that the published product is inaccessible. No GeoTIFF subset or tract mean was retrieved in this bounded pilot. Coverage for both tract universes is therefore **NOT CHECKED**, not 100%.

Expected effort is moderate once a numeric raster is obtained: county bounding-box clipping, a few million 30 m pixels, water/mask QA and fractional zonal statistics over 2,315 polygons. The tested Python runtime lacks rasterio/exactextract, so installation or a verified GIS raster runtime is still needed. Acquisition through official download/clip options may take longer than aggregation. No credential or email-submission workaround was used. Annual land-cover thematic accuracy is not an interchangeable accuracy estimate for fractional impervious values.

This indicator adds a genuinely physical surface dimension beyond persons/km2 and housing-unit configuration. Correlation with population density is plausible but **not measured here**. Empty residential tracts can have high impervious values from infrastructure, an informative distinction. It is a strong second candidate conditional on actual raster coverage and QA.

## 3. Land-Use Diversity: EPA Versus SCAG

### EPA Smart Location Database v3.0

Publication: 2021; guide updated June 2021. Source activity counts combine 2014-2018 ACS household estimates and 2017 LEHD LODES workplace jobs, not a 2022 land-use survey. The guide's main geography description specifies **2019 TIGER/Line block groups**; its introductory footnote/table also references 2018, an internal documentation inconsistency to resolve against actual polygons. Either is pre-2020 geography. Crucially, the service's `GEOID20` means updated **2019** IDs, not 2020 Census block groups. [EPA technical guide, geography section and Table 5](https://www.epa.gov/system/files/documents/2023-10/epa_sld_3.0_technicaldocumentationuserguide_may2021_0.pdf), [EPA official data page](https://www.epa.gov/smartgrowth/smart-location-mapping), [retrieved service](https://services1.arcgis.com/IqEe3YDHhqT8n4KU/ArcGIS/rest/services/EPA_SmartLocationDatabase_V3_Jan_2021_Final/FeatureServer/0).

`D2A_EPHHM` is employment/household entropy over six activity counts: HH and E5_Ret, E5_Off, E5_Ind, E5_Svc, E5_Ent. For each category, `p_i = count_i / (HH + TotEmp)`; `H_activity = -sum(p_i ln p_i) / ln(N_observed_positive_categories)`. Use the zero-term limit for `p_i=0`; total activity zero is undefined, and N<=1 needs an explicit convention rather than dividing by ln(1). `D2B_E8MIXA` is eight-sector employment entropy with fixed denominator `ln(8)`, excludes residences and requires eight underlying counts to recompute. The two normalizations are not interchangeable.

These are **activity-mix proxies**. Jobs and households are counts of different kinds, not residential/commercial land area or observed electricity demand. Trip-weighted entropy and the National Walkability Index additionally impose transport-model weights, making them less suitable for this narrow physical description.

Actual pilot: all **6,425 LA source block groups** were downloaded through paginated service queries with server count verification. Selected activity/entropy fields contain no missing cells, the five job sectors sum exactly to TotEmp, and supplied entropies are within [0,1]. Twelve groups have zero households plus jobs; fourteen have at most one positive activity category. Thus valid-looking published entropy values do not eliminate denominator/convention limitations.

The official [2010-to-2020 California block-group relationship file](https://www2.census.gov/geo/docs/maps-data/data/rel2020/blkgrp/tab20_blkgrp20_blkgrp10_st06.txt) was used only to test geographic feasibility. Truncating old GEOID10 to an 11-digit tract code matches only **1,899 of 2,315** target IDs, missing 416. Positive land intersections reach all 2,315, but 541 donor groups overlap multiple target tracts (maximum five); two LA source IDs differ between GEOID10 and GEOID20. Six target tracts have source-covered relationship land below 99.9%, minimum 98.49%. The cause of each small gap has not been independently adjudicated.

This is not a production 2019-to-2020 crosswalk or proof of valid mix for 2,291 residential tracts. Confirm actual donor geometry and the two identifier changes first. Allocate **extensive HH/job-sector counts**, aggregate to target tracts, then recompute entropy; do not average block-group entropy. Household allocation should use compatible housing/population evidence; job allocation needs workplace evidence, not household weights. Census relationship files provide geometric relationships, not household/job allocation. Area-only allocation can be a disclosed sensitivity case, not a presumed accurate employment crosswalk. [Census relationship-file documentation](https://www.census.gov/geographies/reference-files/time-series/geo/relationship-files.2020.html).

Effort: low to retrieve tabular counts; moderate/high to produce a defensible crosswalk. Older activity years, geographic mismatch and proxy semantics make EPA a fallback rather than the preferred physical land-use indicator.

### SCAG Existing Parcel Land Use

SCAG supplies regional parcel classifications for Southern California including LA County, but current and historical services are materially different:

| Service inspected | Actual vintage and meaning |
| --- | --- |
| [2019 Annual Land Use / HELPR service](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0) | ALU v2019.1, updated February 2021, PID19/APN19, LU19; not automatically the final reviewed 2019 product released in 2024 |
| [Current LA Existing Land Use](https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_LA/MapServer) | 2024 parcels released March 2025; Annual Land Use released June 2025; LU19 migrated onto 2024 geometry plus LU24 updates |

The current service is not a frozen 2019 spatial snapshot simply because it retains an LU19 field. For 2022-compatible descriptions, obtain and pin the final 2019 product and metadata, or explicitly disclose using the older v2019.1 pilot. Do not substitute the 2024 layer without a temporal decision.

Use existing-use fields, not zoning/general-plan/specific-plan designations. The service taxonomy distinguishes residential 11xx, commercial/services 12xx, industrial 13xx, transportation/communications/utilities 14xx, mixed commercial/industrial 15xx, mixed residential/commercial 16xx, open space/recreation 18xx, vacant 19xx, agriculture 2xxx, non-developed 3xxx and water 4xxx. A reproducible code-to-class table must retain relevant detailed subcategories, mixed uses, unknown 9999, blank codes, specific-plan 7777 and undevelopable/protected 8888; generic prefix recoding alone is not a verified actual-use classification.

Pilot service queries used the actual string field `COUNTY_ID='037'` and returned **2,406,373 LA parcel records**, not unique non-overlapping parcels. LU19_SRC includes 1,815,058 ASSESSOR records (75.43%) and **574,359 LU16 carry-forward records (23.87%)**. Blank LU19 appears in 1,015 records and 9999 in 2,293. Record counts are not area fractions or spatial coverage guarantees.

The published v2019.1 dictionary says STACK=0 means no duplicate geometry, but actual STACK values range **1-600**, with 2,069,877 records at 1 and **336,496 (13.98%) above 1**. APN_DUP is 0 for 2,396,695 records and null for 9,678. A naive STACK>0 rejection would remove every record. This metadata/data inconsistency and stacked tax/condominium records require geometry-level QA; even APN_DUP=0 is not proof of unique geometry. The newer layer explicitly describes STACK=1 as no duplicates and has PARENT_INDEX and secondary-use fields, which cannot be backported as an assumed historical rule.

Proposed area composition: intersect verified, non-overlapping parcel footprints with tract land in an equal-area CRS; `A_tc = classified intersection area in class c`; `p_tc = A_tc / sum_c(A_tc)`; `H_landuse = -sum_c(p_tc ln p_tc) / ln(K)` with a fixed, prespecified K. Zero classified area is undefined. Report classified area / tract land area, unclassified area, slivers, overlaps, rights-of-way and water decisions. Do not sum every tax record's ACRES or use parcel-centroid assignment. Keep mixed-use as an explicit class unless verified secondary-use fractions permit splitting. A three-category residential/commercial/industrial conditional entropy excludes other uses and must be labeled as such, not entropy of the entire tract.

No parcel geometry overlay was done; **valid indicator coverage remains NOT CHECKED for 2,315 and 2,291**. Effort is highest among the candidates: acquire the correctly versioned county layer, resolve overlapping/stacked geometries and class mapping, then overlay millions of records. SCAG is physically closer to true land-use composition than EPA activity counts, but its QA cost is substantive, not an excuse to assume completeness.

## Secondary Candidates

**Housing occupancy:** ACS 2022 B25002_002E / B25002_001E, with corresponding M fields and the same subset-proportion MOE handling. Vacancy is _003E / _001E. This distinguishes housing utilization, not building form; it is not commercial vacancy or observed energy demand. Relevant totals can be zero, and seasonal/group-quarter tracts need care. Official [B25002 fields](https://api.census.gov/data/2022/acs/acs5/groups/B25002.html) were verified but values were not retrieved, so actual coverage is untested. Low processing effort, but comparatively weak additional physical information and overlap with social/household context: do not prioritize.

**Intersection density:** a possible local street-grain measure is unique, consolidated at-grade intersections with at least three street branches per km2 of tract land. It requires buffering, grade separation, roundabout/divided-road consolidation and deduplication; road segments or directed edge counts are not intersections. EPA D3b is a weighted pedestrian-oriented intersection measure from older HERE data, not this simple definition. The existing restoration travel network already represents road connectivity/accessibility, although its travel matrices are not a direct intersection-density variable. Without an incremental-information test, do not add another road/access coordinate. No new intersection extraction or coverage claim was made.

## Summary Decision

The complementary first pair is **B25024 5+ housing-unit share** (configuration) and **2022 Annual NLCD mean impervious fraction** (surface intensity). A third, conditional measure is **SCAG area-based land-use entropy**, after vintage and geometric/classification QA; EPA activity mix is a fallback, not an additional fourth variable and not equivalent to parcel composition. No new source embeds earthquake shaking or damage, provided SCAG's hazard-overlay attributes are deliberately excluded.

The strongest immediate design is option **A**, keep housing age and describe existing clusters with the new variables. It preserves published classifications, separates explanation from model construction and does not silently increase the built-environment block's clustering weight. Options B/C and the current matrix's mixed constructs are addressed in the accompanying recommendation and redundancy reports.

## Audit Files and Reproduction

- `BUILT_ENVIRONMENT_DATA_SOURCE_AUDIT.csv`: source versions, exact formulas, status, overlap and feasibility decisions.
- `BUILT_ENVIRONMENT_TRACT_COVERAGE.csv`: 2,315 ID rows, original estimates/MOEs, denominator and uncertainty flags, residential membership and explicit non-extraction statuses.
- `pilot/`: LA ACS and EPA source subsets, correlation tables, existing-label profiles, relationship feasibility tables, metadata/query snapshots and SHA256 download manifest.
- `PRESERVATION_BASELINE.json` and `PRESERVATION_VERIFICATION.json`: hashes protecting inspected scientific inputs, Stage 7 outputs and figure files; existing staged changes preserved.

`pilot_audit.py` takes an explicit `--repo` and writes only into its own `--out` audit directory. With pandas/numpy installed, phases are `fetch`, `secondary`, `audit`, `crosswalk`, `reliability`; `snapshot`/`verify` are preservation checks. Run `fetch` and `secondary` sequentially because they update the download manifest. The national ACS table, large FEMA PDF, statewide relationship table and full service pages are not all committed; their original URLs/hashes are recorded, and county subsets are retained. Public services can change: use the retained subsets for this audit's exact values and revalidate any later extraction.

No PCA, K-means, hotspot ranking, restoration simulation or existing figure generation was executed or changed.
