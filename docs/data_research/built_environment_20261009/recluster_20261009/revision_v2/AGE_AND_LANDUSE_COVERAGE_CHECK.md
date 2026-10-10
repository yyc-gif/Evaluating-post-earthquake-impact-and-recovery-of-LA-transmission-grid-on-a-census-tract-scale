# Land-use and all-building age: direct source queries (2026-10-09)

This is a **source-field and record-level** audit, NOT tract polygon area extraction. The source response with exact statistics is retained in `results/SOURCE_SERVICE_PROBES.json`. The baseline full-domain spatial accounting remains 2,315 tracts; residential typology covers 2,291.

## Actual 2014 LARIAC4 building-year coverage, by use

Live FeatureServer: https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1

Source condition for recorded range: `1800 <= YearBuilt1 <= 2014` (only **numerically plausible**, not individually authenticated as construction year).

| UseType | All building records | Plausible YearBuilt1 records | Availability |
|---|---:|---:|---:|
| Residential | 2,801,374 | 2,769,391 | 98.86% |
| Commercial | 108,725 | 102,241 | 94.04% |
| Industrial | 67,430 | 57,464 | 85.22% |
| Institutional | 22,253 | 20,600 | 92.57% |
| Government | 56,254 | 2,414 | **4.29%** |
| Recreational | 5,276 | 4,329 | 82.05% |
| Irrigated Farm | 3,187 | 945 | 29.65% |
| Miscellaneous | 5,249 | 799 | 15.22% |
| Missing UseType | 49,225 | 253 | 0.51% |
| **All** | **3,118,973** | **2,958,436** | **94.85%** |

**Interpretation:** the all-building source has meaningful non-residential coverage in commercial/industrial/institutional types, but Government and other uses are severely underobserved. Consequently computing a naive countywide or tract-wide average building age by dropping missing values is not an unbiased all-building-age descriptor. Audit record-level assignment, per-tract building coverage, age nonresponse by class, and the relation of 2014 buildings to the 2020 stock. These percentages should not be mistaken for spatial coverage across the 2,315 study tracts. The observed industrial building with YearBuilt1 1989 demonstrates that age is not exclusive to ACS residential housing.

## 2020 building-outline source

Live LARIAC6 Countywide Building Outlines (2020): https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0

Direct count query returned **3,293,177** 2020 building records. Fields include AREA and HEIGHT but **no directly usable year built**. This is the more appropriate physical urban intensity input for census-tract-based building footprint/height indicators once actual geometry intersections, date, units, completeness, accuracy and boundary QA pass. Avoid inferring floor area from height without a substantiated floor-count model.

## SCAG 2019 land use is real but geometrically unresolved

Live historical ALU service: https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0

Direct LA County query returned **2,406,373** records, **zero null GEOID20** records, **336,496 with STACK >1**, and **2,621 with LU19 9999/7777**. GeoID20 samples are **15-digit 2020 census block IDs**, not tract IDs. This may support a block-to-tract pilot, but does not establish unique/complete area allocation.

A server `groupByFieldsForStatistics=LU19_CLASS` query returned the following *record counts* (NOT area-weighted tract shares):

| SCAG source class | Record count |
|---|---:|
| Single Family Residential | 1,491,775 |
| Multi-Family Residential | 527,605 |
| Commercial and Services | 68,264 |
| General Office | 42,479 |
| Industrial | 52,473 |
| Facilities | 28,148 |
| Education | 9,733 |
| Transportation, Communications, and Utilities | 14,234 |
| Mixed Residential and Commercial | 11,278 |
| Vacant | 114,327 |
| Open Space and Recreation | 17,190 |
| Other categories | see archived JSON |

These count values are not land-use entropy or land area, particularly because stacked properties are material and rights-of-way may be excluded. A production indicator requires documented historical version, polygon geometry dedup/overlap rules, classification map and mixed-use definition, intersections with census tract land, and reporting valid area and unclassified/no-parcel coverage. Do not silently substitute 2024 release geometry.

## Decision rule for a rigorous joint recovery–built-environment typology

1. Restore both T80 and Init_Supply as mandatory K-means inputs: done in the outcome-inclusive `recluster_v2.py` variants.
2. Treat physical built environment as a construct requiring **land-use composition (SCAG)** and **building footprint intensity (LARIAC 2020)** with independently validated tract aggregation; add impervious fraction when official USGS build is verified.
3. Population density is an exposure/demographic descriptor and shares r=0.937 with gross housing-unit density: do not treat both as independent urban physical density signals.
4. Pre-1970 ACS share is **residential** only. LARIAC4 can potentially expand age across uses after missingness/cross-year QA; Government/non-standard categories presently make all-use age estimation vulnerable to severe bias. Do not promote all-use age by extrapolating from valid records.
5. Housing 5+ is an optional residential configuration signal (r=0.631 with log housing density, r=0.956 with 10+ share underlying social vulnerability) rather than a substitute for mixed-use morphology.
6. FEMA NRI overall and earthquake-specific risk correlate r=0.978, so never treat both as distinct dimensions; preserve include/exclude risk sensitivities until the hazard-domain construct is decided, particularly as they overlap social and economic scores.

**Nothing in this source probe satisfies the land-use and footprint *tract-level* admission gate.** Experimental joint cluster labels in `results/JOINT_SUMMARY.json` must therefore remain exploratory, not relabeled as a finished full built-environment scientific result.
