# Candidate definitions and measurement boundaries

Candidate registration is broader than model admission. No saved cluster label, silhouette or recovery correlation was used to admit a measurement. ADMIT does not mean independent or finally selected.

## Denominators and time

The full study universe has 2,315 GEOIDs and the residential master has 2,291. Four unresolved land masks are null for geometry-based variables. ACS and assessor parcel-point attributes remain available where their own support is valid. A common analysis subset is explicitly identified per comparison, never assumed to be the old 2,287 cases.

SCAG entropy uses 11 exclusive classes of classified land, including open/undeveloped categories. Area shares with tract-land denominators are retained alongside classified-land shares. Water, parcel gaps, ambiguous cross-class overlaps and unknowns remain separate. The actual LU19 cache and class map are reused; STACK>1 is not indiscriminately dropped. The official 2020 ALU20 alternative now has actual county numeric records and an exclusive tract-land overlay using the same eleven-class convention. It is CONDITIONAL on classified-land coverage and historical snapshot support; it does not automatically replace 2019.1. The Housing catalog contains 2019 and 2020 ALU services, not a verified 2022 parcel release.

LARIAC union coverage clips to source-qualified tract land. Whole-outline count/size/height diagnostics use centroid assignment and Census ALAND; they are not clipped footprint fragments. Parcel ages use assessment points. These boundary/denominator conventions must not be mixed in algebraic identities.

EMC values are modeled built surface m2 within 100m equal-area cells supported by 2022 Sentinel-2. Fractional cell/land intersections aggregate actual numeric TIFF values. NoData and valid unbuilt zero differ. NRES is a binary modeled non-residential surface, not an 11-class land-use survey.

ANBH is positive-cell net height at100m, with 2018 Sentinel-2 and older SRTM2000/AW3D30 2006-2011. The tract average weights positive cells by land intersection, not building footprint. Neither 2023 release nor current website year is observation year.

Assessor actual year and effective year are kept separate. Valid actual years1700-2022 are an explicit plausibility rule, not an independent validation. SQFTmain is Main Square Footage in the exact current official dictionary; it has not been established as complete gross floor area. AIN deduplication does not resolve shared condominium buildings or multiple building data lines. The follow-up audits shared coordinates, repeated attributes, restricted main-area support and a bounded 2022 cadastral geometry sample; none supplies a certified physical-building identity or gross-floor-area accounting rule. Year/missing-area coverage is observed assessment stock, not complete county all-use coverage.

ACS structure/age denominators are housing units, including vacant units. B25024 5+ =orders6,7,8,9 over1; detached=2 over1, attached=3 over1. B25034 pre1970=orders8-11 over1. SE=sqrt((4/80)*sum((replicate ratio-full estimate ratio)^2)); Census published boundary model uses average weight16 and p*=min(0.5,2.3*16/N); 90% MOE=1.645SE. Zero unit denominators are undefined, never0. Replicate zero-denominator and boundary flags are retained. Exact earlier corrected ratios/MOEs are reused, detached/attached use the same80-replicate calculation.

## Candidate-by-candidate definitions

### land_use_entropy — CONDITIONAL

Construct: land-use composition diversity. Formula: `-sum(p_i log(p_i))/log(11); p_i=exclusive classified class area/total exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: primary candidate. Alternative: none designated.

Admission: Classified parcel land only; preserve missing/ambiguous/gap area. Not full-tract composition.

### residential_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive residential area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### commercial_office_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive commercial_office area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### industrial_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive industrial area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### institutional_public_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive institutional_public area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### transportation_utility_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive transportation_utility area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### open_space_recreation_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive open_space_recreation area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### vacant_undeveloped_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive vacant_undeveloped area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### agriculture_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive agriculture area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### mixed_use_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive mixed_use area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### under_construction_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive under_construction area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### protected_undevelopable_classified_share — CONDITIONAL

Construct: land-use composition. Formula: `exclusive protected_undevelopable area / exclusive classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: composition alternative. Alternative: land_use_entropy.

Admission: Compositional component, shares sum to one; not independent of entropy or other shares.

### scag_nonresidential_classified_share — CONDITIONAL

Construct: residential/non-residential land-use composition. Formula: `sum(non-residential exclusive class area)/classified land`. Units: 0-1. Source: [SCAG](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0)

Time/support: ALU 2019.1; LU19 snapshot, current service updates not observation years. Spatial support: exclusive parcel intersection EPSG3310. Use: primary candidate. Alternative: residential_classified_share.

Admission: Complement of residential_classified_share; do not include both as independent inputs.

### epa_household_job_activity_mix — CONDITIONAL

Construct: household/job activity balance. Formula: `-sum(p_i log(p_i))/log(N positive activities); p_i from donor-land allocated households and five job classes; counts aggregated before entropy`. Units: 0-1. Source: [EPA](https://www.epa.gov/smartgrowth/smart-location-mapping)

Time/support: SLD v3; 2017 LODES jobs, ACS 2014-2018 households; actual 2018 donor polygons. Spatial support: donor-land area allocation to 2020 study tracts; estimated counts. Use: primary candidate. Alternative: land_use_entropy (different measurement).

Admission: Historical household/job activity, not parcel land use. Actual 2018 SLD donor polygons are overlaid on 2020 tract/water support. Uniform within-donor land allocation estimates counts; boundary/vintage and source errors remain. Missing donor records and outside-target counts are explicitly audited. No source entropy averaging, prefix allocation or uncovered-area renormalization.

### scag2020_classified_land_entropy — CONDITIONAL

Construct: land-use composition diversity. Formula: `-sum(p_i log(p_i))/log(11); p_i=exclusive ALU20 classified area / total exclusive classified land`. Units: 0-1. Source: [SCAG2020](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2020_Annual_Land_Use/MapServer/0)

Time/support: 2020 ALU snapshot; later context layers do not update observed ALU20. Spatial support: exclusive ALU20 parcel-land intersections EPSG3310. Use: primary candidate. Alternative: land_use_entropy.

Admission: Actual 2020 ALU20 parcel geometry and coded domain verified. Same-geometry same-class duplicates collapsed; conflicting classifications and cross-class overlap withheld; nonidentical stacked geometries retained. Classified land only, continuous gap/unknown/conflict/water coverage retained. Temporal alternative, no automatic replacement of 2019.1.

### building_footprint_coverage — CONDITIONAL

Construct: building ground coverage. Formula: `area(union(deduplicated Building footprints intersect tract land))/tract land`. Units: fraction. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: primary candidate. Alternative: emc2022_total_built_land_fraction.

Admission: Valid ground coverage for mixed older imagery/2020 inventory; not 2022 synchronized building census.

### emc2022_total_built_land_fraction — ADMIT

Construct: building ground coverage. Formula: `sum(pixel built m2 * pixel land-intersection fraction)/tract land area`. Units: fraction. Source: [EMC](https://data.jrc.ec.europa.eu/dataset/4cd8ccee-bfd1-48c5-9047-61c0343c41e9)

Time/support: EMC-BUILT R2025A V1.0; Sentinel-2 2022. Spatial support: 100 m equal-area; m2 built per pixel. Use: primary candidate. Alternative: building_footprint_coverage.

Admission: 2022 observation support; actual 100m tiles, valid zero/NoData and complete valid-area support checked. Remote classification is not local ground-truth accuracy.

### emc2022_nres_built_land_fraction — CONDITIONAL

Construct: non-residential built surface. Formula: `sum(non-residential built m2 * pixel land-intersection fraction)/tract land`. Units: fraction. Source: [EMC](https://data.jrc.ec.europa.eu/dataset/4cd8ccee-bfd1-48c5-9047-61c0343c41e9)

Time/support: EMC-BUILT R2025A V1.0; Sentinel-2 2022. Spatial support: 100 m equal-area; m2 built per pixel. Use: primary candidate. Alternative: SCAG non-residential area (different denominator).

Admission: Binary modeled non-residential surface, not complete parcel use composition.

### emc2022_nonresidential_built_share — CONDITIONAL

Construct: non-residential built surface. Formula: `modeled non-residential built m2 / all modeled built m2`. Units: fraction. Source: [EMC](https://data.jrc.ec.europa.eu/dataset/4cd8ccee-bfd1-48c5-9047-61c0343c41e9)

Time/support: EMC-BUILT R2025A V1.0; Sentinel-2 2022. Spatial support: 100 m equal-area; m2 built per pixel. Use: primary candidate. Alternative: emc2022_nres_built_land_fraction.

Admission: Derived ratio shares source and numerator with total/NRES; no multi-class entropy.

### nlcd_c12_2022_impervious_fraction — ADMIT

Construct: ground hardening. Formula: `area-weighted fractional impervious percentage /100, mapping year2022`. Units: fraction. Source: [NLCD](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-land-cover-annual-nlcd-collection-12-fractional-impervious)

Time/support: Annual NLCD Collection 1.2; mapping year 2022; 2026 release. Spatial support: 30 m fractional impervious 0-100%; official numeric archive. Use: primary candidate. Alternative: none designated.

Admission: Official C1.2 numerical archive retrieved through public legacy ScienceBase route; year/version/units/NoData and full land support verified. Includes roads and other hard surfaces; not building coverage.

### nlcd_c10_pilot_impervious_land_fraction — DESCRIPTIVE_ONLY

Construct: ground hardening. Formula: `C1.0 pilot reaggregated on exactly the current land geometry`. Units: fraction. Source: [NLCD_PILOT](https://www.mrlc.gov/data)

Time/support: numeric 2022 C1.0 ESRI pilot; NOT verified as C1.2. Spatial support: 30 m numeric pilot only. Use: primary candidate. Alternative: nlcd_c12_2022_impervious_fraction.

Admission: Shared2022 numeric pixels and tract means equal official C1.2; release provenance still distinct. Reproduction record only, not a second independent coordinate; includes roads.

### outline_count_per_km2_centroid — CONDITIONAL

Construct: outline frequency. Formula: `deduplicated CODE=Building centroid count/(Census ALAND/1e6)`. Units: outlines/km2. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: primary candidate. Alternative: building_count_density.

Admission: Physical buildings can be split rooflines/annexes; exact geometry dedup only; boundary ties smallest GEOID.

### outline_area_mean_m2 — DESCRIPTIVE_ONLY

Construct: outline size and segmentation. Formula: `mean of whole EPSG3310 outline area, centroid assigned`. Units: m2. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: size alternative; mean is identity diagnostic. Alternative: other outline size summaries.

Admission: Roofline segmentation affects count and size. Median/IQR/CV are distribution summaries, not new constructs.

### outline_area_median_m2 — CONDITIONAL

Construct: outline size and segmentation. Formula: `median of whole EPSG3310 outline area, centroid assigned`. Units: m2. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: size alternative; mean is identity diagnostic. Alternative: other outline size summaries.

Admission: Roofline segmentation affects count and size. Median/IQR/CV are distribution summaries, not new constructs.

### outline_area_iqr_m2 — CONDITIONAL

Construct: outline size and segmentation. Formula: `75th-25th percentile of whole EPSG3310 outline area, centroid assigned`. Units: m2. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: size alternative; mean is identity diagnostic. Alternative: other outline size summaries.

Admission: Roofline segmentation affects count and size. Median/IQR/CV are distribution summaries, not new constructs.

### outline_area_cv — CONDITIONAL

Construct: outline size and segmentation. Formula: `population SD/mean of whole EPSG3310 outline area, centroid assigned`. Units: dimensionless. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: size alternative; mean is identity diagnostic. Alternative: other outline size summaries.

Admission: Roofline segmentation affects count and size. Median/IQR/CV are distribution summaries, not new constructs.

### outline_height_area_weighted_centroid_m — CONDITIONAL

Construct: vertical morphology. Formula: `sum(positive finite nonconflicting HEIGHT_m * whole outline area)/valid-height outline area`. Units: m. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: primary candidate. Alternative: jrc_anbh_positive_surface_mean_m.

Admission: Historical/mixed inventory roofline height, feet converted to m; no floor-count inference.

### building_height_median_m — CONDITIONAL

Construct: vertical morphology. Formula: `centroid-supported positive finite source HEIGHT distribution`. Units: m. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: primary candidate. Alternative: outline_height_area_weighted_centroid_m.

Admission: Historical height support; distribution alternatives, not independent coordinates.

### building_height_p10_m — CONDITIONAL

Construct: vertical morphology. Formula: `centroid-supported positive finite source HEIGHT distribution`. Units: m. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: primary candidate. Alternative: outline_height_area_weighted_centroid_m.

Admission: Historical height support; distribution alternatives, not independent coordinates.

### building_height_p90_m — CONDITIONAL

Construct: vertical morphology. Formula: `centroid-supported positive finite source HEIGHT distribution`. Units: m. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: primary candidate. Alternative: outline_height_area_weighted_centroid_m.

Admission: Historical height support; distribution alternatives, not independent coordinates.

### jrc_anbh_positive_surface_mean_m — CONDITIONAL

Construct: vertical morphology. Formula: `land-area-weighted mean of positive 100m ANBH cells`. Units: m. Source: [ANBH](https://data.jrc.ec.europa.eu/dataset/85005901-3a49-48dd-9d19-6261354f56fe)

Time/support: GHS-BUILT-H R2023A; 2018 Sentinel-2, SRTM 2000, AW3D30 2006-2011. Spatial support: 100 m net built-height model; m. Use: primary candidate. Alternative: outline_height_area_weighted_centroid_m.

Admission: Net-height model with 2018 imagery and older DEMs; positive-cell land weighting is not footprint-area weighting and not 2022 building height.

### assessor2022_gross_floor_area_ratio — PENDING_DATA

Construct: floor-space intensity. Formula: `documented gross floor area / tract land`. Units: m2/m2. Source: [ASSESSOR](https://data.lacounty.gov/datasets/assessor-parcel-data-rolls-2021-2025)

Time/support: single RollYear 2022; roll year does not date all observations. Spatial support: parcel point and assessment main square footage. Use: primary candidate. Alternative: none designated.

Admission: Cached 2022 unique-AIN records and bounded same-year parcel geometry samples audited. Main Square Footage does not certify gross floor area. Missing structure/building-line area IDs, condo unit/common-area accounting, gross-area inclusion convention and exempt/government coverage. Shared coordinates, parcel geometry or identical attributes do not justify building deduplication. No certified FAR produced.

### assessor2022_main_area_per_land — DESCRIPTIVE_ONLY

Construct: assessment main-area intensity. Formula: `sum(positive SQFTmain*.09290304 for unique AIN parcel points)/Census ALAND`. Units: m2/m2. Source: [ASSESSOR](https://data.lacounty.gov/datasets/assessor-parcel-data-rolls-2021-2025)

Time/support: single RollYear 2022; roll year does not date all observations. Spatial support: parcel point and assessment main square footage. Use: primary candidate. Alternative: none designated.

Admission: Main assessment area; not certified gross FAR or footprint area. Multiple data lines/condos and exemptions are explicit coverage limitations.

### outline_volume_per_land_m_centroid — DESCRIPTIVE_ONLY

Construct: roof-height volume proxy. Formula: `sum(valid-height whole outline area*height)/Census ALAND`. Units: m3/m2. Source: [LARIAC6](https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip)

Time/support: 2020 inventory release; mixed image dates, predominantly older imagery. Spatial support: individual roofline polygons, HEIGHT feet. Use: primary candidate. Alternative: none designated.

Admission: Product of centroid-sum coverage, valid height support and weighted height; no union volume or floor area. Not independent of all factors.

### housing_5plus_share — ADMIT

Construct: residential unit configuration. Formula: `specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: same composition family; choose at most one primary summary. Alternative: other ACS configuration shares.

Admission: Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.

### housing_detached_share — ADMIT

Construct: residential unit configuration. Formula: `specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: same composition family; choose at most one primary summary. Alternative: other ACS configuration shares.

Admission: Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.

### housing_attached_share — DESCRIPTIVE_ONLY

Construct: residential unit configuration. Formula: `specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: same composition family; choose at most one primary summary. Alternative: other ACS configuration shares.

Admission: Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.

### housing_single_unit_share — DESCRIPTIVE_ONLY

Construct: residential unit configuration. Formula: `specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: same composition family; choose at most one primary summary. Alternative: other ACS configuration shares.

Admission: Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.

### housing_2to4_share — DESCRIPTIVE_ONLY

Construct: residential unit configuration. Formula: `specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: same composition family; choose at most one primary summary. Alternative: other ACS configuration shares.

Admission: Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.

### housing_mobile_other_share — DESCRIPTIVE_ONLY

Construct: residential unit configuration. Formula: `specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: same composition family; choose at most one primary summary. Alternative: other ACS configuration shares.

Admission: Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.

### housing_10plus_share — DESCRIPTIVE_ONLY

Construct: residential unit configuration. Formula: `specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: same composition family; choose at most one primary summary. Alternative: other ACS configuration shares.

Admission: Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.

### assessor2022_actual_pre1970_main_area_share — CONDITIONAL

Construct: observed assessment-stock age. Formula: `sum(positive main area with actual YearBuilt<1970)/positive main area with valid actual YearBuilt`. Units: fraction. Source: [ASSESSOR](https://data.lacounty.gov/datasets/assessor-parcel-data-rolls-2021-2025)

Time/support: single RollYear 2022; roll year does not date all observations. Spatial support: parcel point and assessment main square footage. Use: primary candidate. Alternative: all_use2014_pre1970_area_share.

Admission: 2022 parcel point stock; valid year1700-2022; multiple-building lines/condos/exempt stock prevent complete all-building interpretation.

### assessor2022_single_line_pre1970_main_area_share — CONDITIONAL

Construct: observed assessment-stock age. Formula: `same age share restricted to exactly one building data line`. Units: fraction. Source: [ASSESSOR](https://data.lacounty.gov/datasets/assessor-parcel-data-rolls-2021-2025)

Time/support: single RollYear 2022; roll year does not date all observations. Spatial support: parcel point and assessment main square footage. Use: primary candidate. Alternative: assessor2022_actual_pre1970_main_area_share.

Admission: Single-line restricted coverage diagnostic; not countywide all-use completeness.

### assessor2022_effective_pre1970_main_area_share — DESCRIPTIVE_ONLY

Construct: effective assessment-stock age. Formula: `positive main area with EffectiveYearBuilt<1970 / valid effective-year main area`. Units: fraction. Source: [ASSESSOR](https://data.lacounty.gov/datasets/assessor-parcel-data-rolls-2021-2025)

Time/support: single RollYear 2022; roll year does not date all observations. Spatial support: parcel point and assessment main square footage. Use: primary candidate. Alternative: actual YearBuilt (different construct).

Admission: Effective year can reflect improvement/assessment; not original construction year.

### acs_residential_pre1970_share — ADMIT

Construct: residential unit age. Formula: `B25034_008E+009E+010E+011E divided by001E;80 VRE`. Units: fraction. Source: [ACS](https://www.census.gov/programs-surveys/acs/data/variance-tables.html)

Time/support: ACS 2018-2022 five-year; 2022 VRE 80 replicates. Spatial support: 2020 tract; housing units. Use: primary candidate. Alternative: all-use age (different population).

Admission: 2018-2022 residential housing units; neither all-use construction year nor area-weighted physical buildings.

### all_use2014_pre1970_area_share — CONDITIONAL

Construct: historical observed building-stock age. Formula: `valid-age footprint union area pre1970 / historical valid-age footprint union area`. Units: fraction. Source: [LARIAC4](https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1)

Time/support: 2014 inventory; valid observed YearBuilt1. Spatial support: historical outline stock. Use: primary candidate. Alternative: assessor2022_actual_pre1970_main_area_share.

Admission: 2014 historical valid observed-age area; government-age missingness and vintage mismatch; preserve coverage and lower/upper bounds.

### all_use_pre1970_area_share — REJECT

Construct: cross-vintage transferred stock age. Formula: `2014 age transferred only where 2014/2020 outlines satisfy source geometry match`. Units: fraction. Source: [LARIAC4](https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1)

Time/support: 2014 inventory; valid observed YearBuilt1. Spatial support: historical outline stock. Use: primary candidate. Alternative: all_use2014_pre1970_area_share.

Admission: About4% matched-age footprint coverage in prior verified audit; not representative complete 2020 all-use age. Retain values only as coverage diagnostic.

### building_spacing — REJECT

Construct: layout. Formula: not extracted; see verified construct boundary.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: excluded this round. Alternative: none designated.

Admission: No prespecified independent recovery-community construct beyond density/size; source boundary/segmentation definition unresolved.

### street_intersection_density — REJECT

Construct: layout. Formula: not extracted; see verified construct boundary.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: excluded this round. Alternative: none designated.

Admission: Connectivity/access is distinct transport context, not automatically building morphology; no authorized road topology definition/validated source here.

### block_scale — REJECT

Construct: layout. Formula: not extracted; see verified construct boundary.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: excluded this round. Alternative: none designated.

Admission: Shared density/layout information; no prespecified independent conceptual need or verified polygon definition.

### vegetation_fraction — REJECT

Construct: vegetation. Formula: not extracted; see verified construct boundary.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: excluded this round. Alternative: none designated.

Admission: Vegetation is land cover, not building physical morphology; may be context, not an automatic BE coordinate.

### residential_occupancy — REJECT

Construct: household utilization. Formula: not extracted; see verified construct boundary.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: excluded this round. Alternative: none designated.

Admission: Housing occupancy is household utilization, not building morphology; no new primary inclusion.

### stories_from_roof_height — REJECT

Construct: floor-space intensity. Formula: not extracted; see verified construct boundary.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: excluded this round. Alternative: none designated.

Admission: Reject arbitrary story-height assumption; no actual observed floor count.

### total_EAL_divided_BUILDVALUE — REJECT

Construct: multi-hazard loss propensity. Formula: not extracted; see verified construct boundary.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: excluded this round. Alternative: none designated.

Admission: Wrong denominator for total building+population+agriculture loss; not official ALR.

### Pop_Density_per_km2 — DESCRIPTIVE_ONLY

Construct: population concentration. Formula: formal population/Census land area km2.

Time/support: concept boundary; not an acquired primary measure. Spatial support: . Use: primary candidate. Alternative: none designated.

Admission: Population is people, not all-use building form. Preserve as overlap diagnostic, not automatic BE coordinate.

### BUILDVALUE — ADMIT

Construct: economic asset stock. Formula: `published aggregate building exposure value`. Units: 2022 USD. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Economic stock, not physical morphology or expected loss.

### EAL_SCORE — ADMIT

Construct: multi-hazard expected loss with exposure. Formula: `national percentile rank of EAL_VALT`. Units: 0-100 percentile. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Includes building/population/agricultural exposure, frequency and historic loss ratio; not pure hazard, not independent of socioeconomic context.

### EAL_VALT — ADMIT

Construct: multi-hazard expected loss with exposure. Formula: `EAL_VALB+EAL_VALPE+EAL_VALA`. Units: 2022 USD/year. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Same construct as EAL_SCORE, value alternative only; raw/log1p compared, never both primary coordinates.

### ALR_NPCTL — ADMIT

Construct: multi-hazard normalized loss propensity. Formula: `official composite national percentile of EAL-weighted component loss-rate percentiles`. Units: 0-100 percentile. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Unadjusted for community social/resilience factors; exposure-normalized component rates, not pure hazard or totalEAL/BUILDVALUE.

### ALR_VALB — CONDITIONAL

Construct: building annual loss rate. Formula: `EAL_VALB/BUILDVALUE for positive exposure`. Units: year-1. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Building consequences only; does not represent population/agriculture/all consequences.

### ALR_VALP — CONDITIONAL

Construct: population annual loss rate. Formula: `EAL_VALP/POPULATION for positive exposure`. Units: year-1. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Population consequences only; not population-equivalent dollar loss divided by people.

### ALR_VALA — DESCRIPTIVE_ONLY

Construct: agricultural annual loss rate. Formula: `EAL_VALA/AGRIVALUE for positive exposure`. Units: year-1. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Zero agricultural exposure remains undefined; sparse regional coverage.

### RISK_SCORE — DESCRIPTIVE_ONLY

Construct: social-adjusted multi-hazard risk. Formula: `national rank of EAL_VALT times community risk factor`. Units: 0-100 percentile. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Mechanically combines social vulnerability and resilience; overlaps mandatory separately retained SOVI.

### ALR_VRA_NPCTL — REJECT

Construct: social-adjusted loss propensity. Formula: `community-adjusted official composite loss-rate percentile`. Units: 0-100 percentile. Source: [FEMA](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf)

Time/support: archived FEMA NRI v1.19 March 2023; 2022 dollar framework. Spatial support: published tract fields; national percentiles vs values. Use: primary candidate. Alternative: none designated.

Admission: Mechanically reintroduces social/resilience adjustment alongside mandatory SOVI; preserve as diagnostic comparator.

Official C1.2 versus retained C1.0 numeric identity: same native30m grid, 6,916,982 common valid pixels, zero value/mask differences, and zero differences in all2,311 same-geometry tract means. Release provenance remains separate; no duplicate measurement is added. See NLCD_PIXEL_AND_TRACT_IDENTITY_QA.json.


Follow-up measurement evidence: PENDING_DATA_COMPLETION_AUDIT.md and the three source-specific QA notes. EPA values are spatially allocated estimates, SCAG2020 is measured classified parcel land, and Assessor gross FAR remains unmeasured. No automatic feature substitution or weight change is adopted.
