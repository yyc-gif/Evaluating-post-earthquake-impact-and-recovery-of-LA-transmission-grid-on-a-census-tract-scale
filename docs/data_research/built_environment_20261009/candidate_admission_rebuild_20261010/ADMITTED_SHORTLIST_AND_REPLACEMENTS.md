# Admitted shortlist and replacements

The64-row registry is a measurement pool, not an instruction to fit every coordinate. Current dispositions: {'CONDITIONAL': 32, 'DESCRIPTIVE_ONLY': 13, 'ADMIT': 9, 'REJECT': 9, 'PENDING_DATA': 1}. Prior BE0/BE1/D are reference calculations only. No candidate was preferred for retaining previous clusters.

## Small proposed measurement sets

**Definition-qualified core:** `emc2022_total_built_land_fraction` + one ACS residential-configuration summary (`housing_5plus_share`, or `housing_detached_share` as a same-family alternative). These capture ground coverage and residential unit configuration separately. EMC has2,311 full-domain/2,287 residential valid geometric measurements; ACS has2,292/2,291 valid positive-housing denominators. Valid zeros are preserved. This core has no claim of comprehensive all-use morphology.

**Preferred expanded, explicitly conditional set:** add `land_use_entropy` for classified-land composition, then `assessor2022_actual_pre1970_main_area_share` for observed2022 assessment-stock age. This four-construct proposal is not forced to three coordinates. SCAG coverage median=0.751074; entropy represents classified land only. Assessor age is available on2290 residential tracts, valid-year main-area coverage median=0.999786. Do not call it complete area-weighted all-building construction age. If that conditional age construct is not scientifically acceptable, OMIT age from the initial candidate set rather than imply a complete measure exists. Retain three age alternatives for a prespecified measurement comparison.

**Ground-hardening candidate:** `nlcd_c12_2022_impervious_fraction` is admitted from the official2022 C1.2 numeric product. It measures buildings AND roads/other hard surfaces. Choose it instead of building-only coverage only if the declared coordinate is whole-surface hardening; do not treat the two as identical or automatically stack both. Their common-sample overlap is reported.

**Optional vertical-form extension:** `outline_height_area_weighted_centroid_m`, conditional on mixed historical LARIAC support and continuous valid-height coverage. This measures a distinct vertical coordinate and is not a prerequisite for every model. Historical ANBH is the independent-source alternative; its positive-cell weighting and older source dates are explicit. Outline median area or CV can be tested as size/segmentation alternatives ONLY if building-size structure is an intended coordinate. Do not add count density, mean area and their coverage product as independent evidence.

## Same-construct alternative designs

| Proposed measurement | Alternative | Why one may replace the other; required restriction |
| --- | --- | --- |
| EMC2022 total coverage | LARIAC clipped-union coverage |2022 remotely modeled surface versus older mixed-image vector rooflines; compare exactly same GEOIDs, do not co-include coverage duplicates.|
| SCAG classified entropy | SCAG residential classified share |diversity versus composition direction; same raw classes, not independent evidence. EPA activity mix is now a conditional historical household/job-count allocation on actual 2018 SLD polygons, followed by tract-level entropy; it measures a different construct. SCAG2020 entropy is a conditional temporal alternative with the same eleven-class convention.|
| Assessor2022 actual-year main-area share | LARIAC2014 historical valid-age footprint share |different time, assessed support and denominator; conditional alternatives, not equivalent measurements.|
| All-use age candidate | ACS2022 housing-unit pre1970 share |residential unit age only; cannot be relabeled all-use age.|
| LARIAC weighted height | ANBH2018 positive-cell land mean |historic vector rooflines versus historic modeled net-height cells; denominator/date differences retained.|
| ACS5+ housing share | detached share |same residential composition family; do not include its full partition merely to add coordinates.|
| log1pBUILDVALUE+ALR_NPCTL | ALR_NPCTL only or EAL_SCORE |separate stock/propensity versus propensity alone or combined exposure-bearing expected losses; scientific coordinate choice, not performance ranking.|

## Excluded/held measurements and their destination

| candidate_id | disposition | admission_condition_or_exclusion_reason |
| --- | --- | --- |
| nlcd_c10_pilot_impervious_land_fraction | DESCRIPTIVE_ONLY | Shared2022 numeric pixels and tract means equal official C1.2; release provenance still distinct. Reproduction record only, not a second independent coordinate; includes roads. |
| outline_area_mean_m2 | DESCRIPTIVE_ONLY | Roofline segmentation affects count and size. Median/IQR/CV are distribution summaries, not new constructs. |
| assessor2022_gross_floor_area_ratio | PENDING_DATA | Cached 2022 unique-AIN records and bounded same-year parcel geometry samples audited. Main Square Footage does not certify gross floor area. Missing structure/building-line area IDs, condo unit/common-area accounting, gross-area inclusion convention and exempt/government coverage. Shared coordinates, parcel geometry or identical attributes do not justify building deduplication. No certified FAR produced. |
| assessor2022_main_area_per_land | DESCRIPTIVE_ONLY | Main assessment area; not certified gross FAR or footprint area. Multiple data lines/condos and exemptions are explicit coverage limitations. |
| outline_volume_per_land_m_centroid | DESCRIPTIVE_ONLY | Product of centroid-sum coverage, valid height support and weighted height; no union volume or floor area. Not independent of all factors. |
| housing_attached_share | DESCRIPTIVE_ONLY | Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion. |
| housing_single_unit_share | DESCRIPTIVE_ONLY | Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion. |
| housing_2to4_share | DESCRIPTIVE_ONLY | Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion. |
| housing_mobile_other_share | DESCRIPTIVE_ONLY | Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion. |
| housing_10plus_share | DESCRIPTIVE_ONLY | Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion. |
| assessor2022_effective_pre1970_main_area_share | DESCRIPTIVE_ONLY | Effective year can reflect improvement/assessment; not original construction year. |
| all_use_pre1970_area_share | REJECT | About4% matched-age footprint coverage in prior verified audit; not representative complete 2020 all-use age. Retain values only as coverage diagnostic. |
| building_spacing | REJECT | No prespecified independent recovery-community construct beyond density/size; source boundary/segmentation definition unresolved. |
| street_intersection_density | REJECT | Connectivity/access is distinct transport context, not automatically building morphology; no authorized road topology definition/validated source here. |
| block_scale | REJECT | Shared density/layout information; no prespecified independent conceptual need or verified polygon definition. |
| vegetation_fraction | REJECT | Vegetation is land cover, not building physical morphology; may be context, not an automatic BE coordinate. |
| residential_occupancy | REJECT | Housing occupancy is household utilization, not building morphology; no new primary inclusion. |
| stories_from_roof_height | REJECT | Reject arbitrary story-height assumption; no actual observed floor count. |
| total_EAL_divided_BUILDVALUE | REJECT | Wrong denominator for total building+population+agriculture loss; not official ALR. |
| Pop_Density_per_km2 | DESCRIPTIVE_ONLY | Population is people, not all-use building form. Preserve as overlap diagnostic, not automatic BE coordinate. |
| ALR_VALA | DESCRIPTIVE_ONLY | Zero agricultural exposure remains undefined; sparse regional coverage. |
| RISK_SCORE | DESCRIPTIVE_ONLY | Mechanically combines social vulnerability and resilience; overlaps mandatory separately retained SOVI. |
| ALR_VRA_NPCTL | REJECT | Mechanically reintroduces social/resilience adjustment alongside mandatory SOVI; preserve as diagnostic comparator. |

## Remaining genuine gaps

Official Annual NLCD2022 C1.2 was acquired through the public legacy ScienceBase route after manager/API/WCS failures. Its numeric TIFF and continuous valid-land coverage were checked and it is admitted as ground hardening; the C1.0 pilot stays descriptive. Same-geometry C1.2 versus C1.0 differences are reported in NLCD_OFFICIAL_AND_PILOT_COMPARISON.csv. Ground hardening includes roads and is not building footprint coverage. EPA tract activity mix now has an explicit actual-donor land-intersection crosswalk, numeric identity and conservation checks, with uniform within-donor activity allocation declared as estimation. SCAG2020 now has actual numeric overlay, duplicate/conflict treatment and continuous coverage QA. Both are CONDITIONAL, rather than complete synchronized 2022 measurements. Certified2022 all-use gross FAR remains PENDING_DATA: the inspected Main Square Footage dictionary, shared parcel identities and public building-line fields do not establish gross-floor-area inclusion, unit/common-area attribution or exempt-stock completeness. These are missing evidence, not zero measurements. No complete contemporaneous all-use age census is claimed.

Official C1.2 versus retained C1.0 numeric identity: same native30m grid, 6,916,982 common valid pixels, zero value/mask differences, and zero differences in all2,311 same-geometry tract means. Release provenance remains separate; no duplicate measurement is added. See NLCD_PIXEL_AND_TRACT_IDENTITY_QA.json.


Follow-up measurement evidence: PENDING_DATA_COMPLETION_AUDIT.md and the three source-specific QA notes. EPA values are spatially allocated estimates, SCAG2020 is measured classified parcel land, and Assessor gross FAR remains unmeasured. No automatic feature substitution or weight change is adopted.
