# Built-environment source and geometry audit

Scientific baseline: 031d2c675f8e7d58035d27448be040b809ced086. All outputs here are measurements/candidate diagnostics; no variable selection or clustering was performed.

| source | official location | version |
|---|---|---|
| SCAG2019 | https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0 | ALU2019.1, updated February2021 |
| LARIAC6 | https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0 | 2020 release; mixed source capture dates |
| LARIAC4 | https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1 | 2014 outlines; associated assessor Roll_Year retained |
| CGS MS48 | https://www.conservation.ca.gov/cgs/Pages/Publications/MS48.aspx | 2025 MS48 / USGS NSHM2023 / Vs30 July2022 |
| TIGER water | https://www2.census.gov/geo/tiger/TIGER2020/AREAWATER/tl_2020_06037_areawater.zip | 2020 county area-water polygons |

## Domain and land denominator

The original 2,315 GEOID11 universe and exact 2,291 residential membership are preserved. Study polygons are transformed to EPSG3310. Land is polygon area minus unioned TIGER2020 county water; Census ALAND is an independent check. Eighteen tracts differ by more than 0.5%; candidate polygon-dependent shares, entropy and primary PGA are withheld there, while raw measured diagnostics and discrepancy values remain. land_mask_area_check_pass means area agreement within0.5%, not independent spatial validation of the water mask. The maximum discrepancy is44.84%; this is an unresolved land-area definition/geometry discrepancy, not a proven absence of water. Building counts and housing-unit densities use Census ALAND directly.

## SCAG2019

All 2,406,373 LA records and 336,496 STACK>1 records were acquired, with exact OBJECTID reconciliation across 1,204 response chunks. Actual equal-area intersections allocate parcels spanning tracts; GEOID20 is never assumed to be a tract key. 315,495 duplicate geometries are counted once. Same-geometry conflicting classes and different-geometry cross-class overlaps are withheld as ambiguous area; STACK>1 is not a blanket deletion rule. 39 invalid geometries were repaired and 0 missing geometries retained in the QA count.

Classified land coverage quantiles: {'0.0': 0.2291817449720642, '0.01': 0.5609519544816424, '0.5': 0.7514669122693111, '0.99': 0.9535705331969866, '1.0': 0.996990709467607}. Total ambiguous overlap is 2.948 km² and parcel gaps 688.831 km². Unknown LU codes, geometry gaps, SCAG water and overlap are separately reported. Broad-code allocation is explicit in SCAG_SOURCE_CODE_MAPPING.csv. Mixed-use records remain mixed-use rather than guessed residential/commercial fractions.

Entropy = -sum(p_i ln p_i)/ln(11), with p_i exclusive class area divided by all exclusive classified land. It covers all eleven prespecified land categories, including agriculture/vacant/protected land, and excludes unknown/water/ambiguous area. It is not entropy of parcel counts or only developed land. Classification coverage and ambiguity must accompany interpretation. Boundary lines/points have zero area and are removed before overlays; any failed numerical overlay uses a recorded 0.1-mm precision repair, not blanket geometry quantization.

## LARIAC6 urban form

The official GDB contains 3,293,177 records: {'Building': 3115967, 'Courtyard': 34364, 'Free Standing Solar Structure': 142846}. Only actual Building outlines enter the footprint/count measures. 3 exact-geometry duplicates are removed; distinct outlines with repeated BLD_ID remain. 149 invalid geometries are repaired. Unioned footprint coverage is clipped to tract land; 3716.324 m² of overlap is removed. Count assignment uses the outline centroid, with the lowest GEOID for an exact boundary tie; crossing outlines are not multiply counted.

AREA is ft² in the native EPSG6424 feet geometry, confirmed by near-one source-area/native-geometry ratios. Official County LARIAC dictionary specifies HEIGHT in feet; the inherited LARIAC6 schema is converted by 0.3048 to metres. Median heights use centroid-assigned observed buildings; area-weighted heights use clipped outline area. Two conflicting duplicate heights are excluded locally, not all height observations. Missing/nonpositive heights remain undefined. Heights do not establish stories; footprint is roof projection, not floor area. No arbitrary small-building cutoff is added, and a minimum detectable footprint is not documented. The 2020 release contains substantial earlier imagery, including 2008; it is not a complete new 2020 survey.

## Age and inventory boundary

BUILDING_AGE_COMPLETENESS_AND_SENSITIVITY.md separates original2014 age measurements from strict 2014-to-2020 linkage. R2D_BRAILS_INVENTORY_AUDIT.md finds school portfolios only, not a representative all-use county inventory. No NSI/BRAILS school attribute is propagated to county buildings.

## Pure hazard and pilot imperviousness

The original CGS PGA CSV is byte-identical to the official MS48 download. Its station interpolation reproduces all 92 frozen inputs within 2.22e-16 g. Primary tract PGA is an area-weighted piecewise-constant 0.01-degree cell representation of the same geographical PGA field, not a mapping-weighted station value. Units are g. Five tracts have less than99% grid support and primary PGA is withheld; partial-area and centroid-IDW diagnostic values remain. TIGER land-mask discrepancies are additionally flagged/withheld. FEMA total/earthquake risk remains diagnostic and is not admitted as pure hazard.

Impervious fraction is the existing numeric ESRI AnnualNLCD2022 Collection1.0 pilot. Direct USGS source/version correspondence is not verified; this remains a pilot candidate, not an authoritative USGS measurement.

Original source archives and full SCAG response geometries remain locally available. Completed temporary overlay caches were hash-recorded and removed to recover disk space; see REMOVED_TEMPORARY_CACHE_MANIFEST.csv. SOURCE_CACHE_MANIFEST.csv records their exact hashes; metadata, acquisition logs and scripts are committed. Large raw archives are not uploaded or used as a substitute for validated tract data.
