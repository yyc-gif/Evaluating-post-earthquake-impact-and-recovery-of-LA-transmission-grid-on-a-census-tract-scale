# Final Candidate Construct Decision

## Source And Execution Authority

The measurement baseline is commit `94faefd30273dec8318197de443f2f992fa29e5c`; its remote candidate-admission branch was fetched and verified. This review uses an isolated branch from that exact commit. A completed matching local shortlist study was discovered in `_cs11` and read without modifying it. Its outputs/scripts were frozen byte-for-byte, with source HEAD, uncommitted status and hashes recorded in `REUSE_PROVENANCE.json` and `REUSED_RUN_BYTE_MANIFEST.csv`. Reuse is explicit, not represented as newly performed fits or a new prospective registration.

The reused study completed 440 new full/spatial KMeans fits plus 20 coverage diagnostic fits and reused 40 exact historical fits. This independent review performed **zero further KMeans fits, zero GIS overlays and zero physical simulations**. It recomputed standardization, weights, fitted predictions, new-model inertia, all/train/held-out ARIs, reassignment counts, 1,320 model-pair contingency tables and original-unit source differences. All 12 model records and 240 paired seed/spatial cases passed. HIST full centers are descriptive partition means because original full-estimator centers are unavailable; its archived labels are verified exactly, not refitted or reconstructed from those means. Original HIST spatial-estimator predictions were verified exactly.

## Construct Gates

| Family | Preferred / eligible definition | Gate and decision |
| --- | --- | --- |
| Ground occupancy | EMC2022 total built-land fraction | Preferred updated measurement; actual 100m built-m2 data, fractional boundary support, valid-land coverage verified. No claim of superior local ground-truth accuracy. LARIAC is a historical vector substitute. |
| Land-use diversity | SCAG2020 eleven-class exclusive classified-parcel-area entropy | Eligible only as classified-land diversity. Coverage and LU19 carry-forward are explicit. SCAG2019 is a temporal substitute, not another dimension. |
| Residential configuration | ACS2022 five-plus housing-unit share | Preferred contrast; positive denominators and 80 variance replicates. Detached share is an alternative compositional contrast, not a second independent configuration input. |
| Observed age | Assessor2022 recorded Main Square Footage / LARIAC2014 valid-age footprints / ACS residential units | Distinct support definitions. All-use completeness and independent lineage are not established. Qualified sensitivity models only; no-age CORE3 is preferred. |
| Hardening | NLCD C1.2 2022 impervious fraction | Eligible separate construct including roads/parking; bounded optional extension, not primary automatic addition. |
| Vertical form | Historical roof-height summary | Numeric/support QA supports a conditional historical extension, not a synchronized 2022 height census or inferred floor area. |
| Activity mix | EPA historical allocated households and jobs | Distinct from parcel composition, but unresolved within-donor allocation accuracy. Descriptive only in this shortlist. |
| Gross FAR | Certified total floor area / compatible land | Failed availability/identity gate; PENDING_DATA and ineligible. No surrogate was fabricated. |

CORE4 is not admitted as complete all-use age: that interpretation fails its source gate. It was compared under the narrower observed assessment-area age definition. AGE_ACS and AGE_HIST similarly retain their residential/historical meanings. Conditional diagnostics cannot be used to disguise a failed stronger construct.

## Paired Measurement Evidence

All following pairs use the **same 2,286 GEOIDs**, with exact membership/order hashes; missing data were not imputed. Each paired difference and all broad SCAG composition differences are saved.

| Comparison (new minus old) | Pearson | Spearman | Mean difference | MAE | P90 absolute difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| EMC minus LARIAC coverage | 0.94922 | 0.93062 | 0.03496 | 0.03730 | 0.06569 |
| SCAG2020 minus SCAG2019 entropy | 0.99491 | 0.99580 | -0.00091 | 0.00522 | 0.01388 |
| Assessor minus LARIAC age share | 0.94153 | 0.94350 | -0.09150 | 0.09592 | 0.18830 |

Coverage sources describe one occupancy family, not identical error-free truths. Age sources do not share denominators and may share assessment lineage. Housing five-plus/detached r=-0.90016 does not make them exact complements. Partial correlations, nonlinear five-fold spline overlap and residual-variance diagnostics are in the source comparison tables; low VIF never suffices to declare independent constructs.

### Source Support And Error Sensitivity

- EMC valid-land support is essentially 1.0 for all 2,287 resolved residential reference tracts; global product validation does not certify tract-specific accuracy. LARIAC union/intersection supplies finer physical boundaries but a mixed-image inventory.
- SCAG2020 classified-land coverage has median 0.75127 and P10 0.66714. Hypothetical missing-land entropy bounds have median width 0.39371 and P90 0.49487. These are feasible support bounds, not errors, estimates or confidence intervals. The same conditional interpretation applies to ALU19.
- LU19 carry-forward was read from cached ALU20 attributes: 12.248% of county records, 36.806% of summed reported parcel ACRES. County record acres cannot be equated with mutually exclusive study-tract land. No new overlay was performed.
- ACS median five-plus MOE90 is 0.06748; detached 0.07245. All valid point estimates and 80 replicates remain; 158/59 boundary-model cases are retained. Fixed CORE3-center predictions under the 80 joint survey replicates change a median 7.5 tracts and at most 15. They are neither independent simulated surveys nor refitted clustering uncertainty. The review independently recomputed all raw count ratios and regular/boundary MOEs, then added two fixed-centroid boundary-MOE endpoint stresses: lower changes zero labels, upper one. They do not capture all possible measurement errors or constitute a probabilistic interval.
- EPA donor power-allocation scenarios include the outside-study remainder and conserve every household/job total. Less-concentrated allocation changes target entropy by MAE 0.01937, P90 0.05165 and maximum 0.43487; 235 tracts move by more than 0.05. Different household/job allocations similarly preserve totals while altering target mix. Conservation does not establish location accuracy.
- Assessor identity QA covers 2,413,687 unique AIN records, 157,429 multiline records, 315,122 condo-coded records, 20,789 shared positive-area coordinate groups and 40 bounded cadastral identity probes. The latter are not a representative accuracy sample. Multiple AINs/shared geometries are not independent buildings. Restriction diagnostics do not resolve common/unit area or exempt/government completeness.
- The enriched historical LARIAC schema contains AIN, YearBuilt1, Roll_Year and assessment-value fields, supporting an assessment-lineage inference. The exact historic roll and join cardinality remain unresolved. Correlation cannot certify independent age observations.

## Bounded Model Comparison

All fixed-k4 fits use KMeans n_init=100, max_iter=500, tol=1e-4, Lloyd, seeds42-61; the same 20 saved spatial cases contain 17 unique deletion sets. Spatial standardization is fitted on retained training tracts only, with full-cohort predictions. Hungarian label matching uses retained training overlap for spatial comparisons, not held-out labels. Repeat deletion sets are not counted as independent geographic experiments.

The full 2,315-tract accounting table contains 2,291 residential members. Four unresolved-geometry GEOIDs remain in the master matrix and unclassified. Ten three/four-coordinate specifications use 2,287; CORE4 and its matched CORE3_AGE_COMMON use 2,286, excluding only 06037115103. Model-pair comparisons identify when training samples differ; the conditional-age comparison uses the identical reduced cohort. No MOE or low-coverage deletion defines the primary sample.

| Model | Scientific role | N | Median seed ARI | Median spatial ARI | Minimum spatial ARI | Maximum reassigned |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| HIST | Reused historical reference | 2287 | 0.99584 | 0.92345 | 0.75222 | 225 |
| CORE2 | Preferred restricted minimum | 2287 | 0.99721 | 0.94692 | 0.72831 | 220 |
| CORE3 | Preferred three-construct specification | 2287 | 1.00000 | 0.87922 | 0.69293 | 255 |
| CORE4 | Conditional observed assessment-area age | 2286 | 0.99595 | 0.89201 | 0.64889 | 300 |
| AGE_ACS | Residential-unit age sensitivity | 2287 | 0.96853 | 0.88264 | 0.80783 | 175 |
| AGE_HIST | Historical observed-footprint age sensitivity | 2287 | 1.00000 | 0.90226 | 0.66602 | 284 |
| COVER_ALT | Coverage source substitution | 2287 | 0.99035 | 0.90420 | 0.57216 | 633 |
| LAND_ALT | Classified-land vintage substitution | 2287 | 0.98789 | 0.87190 | 0.69340 | 255 |
| HOUSING_ALT | Detached-unit contrast substitution | 2287 | 1.00000 | 0.91319 | 0.71671 | 234 |
| HARDEN_EXT | Separate hardening extension | 2287 | 0.98400 | 0.91704 | 0.66479 | 283 |
| HEIGHT_HIST_EXT | Conditional historical vertical extension | 2287 | 0.99501 | 0.92092 | 0.70277 | 246 |
| CORE3_AGE_COMMON | Matched no-age conditional-age control | 2286 | 0.99721 | 0.87795 | 0.68855 | 259 |

These are outcome diagnostics, not measurement quality ranks. CORE2 has better median spatial agreement but omits the distinct parcel-composition construct requested by the research target. CORE3 is chosen for that content, not higher silhouette or resemblance to HIST. New-variable comparisons redistribute the fixed physical parent budget, as documented separately.

### Meaningful Patterns And Minority Classes

CORE3 seed42 has diagnostic raw classes 0/1/2/3 with 650/802/801/34 tracts. Do not transfer manuscript class IDs or names. The highest mean B (36.2488 h, raw0) coexists with lower mean SOVI (31.1408) than raw1/raw2 (84.1608/77.5061). Raw1 versus raw2 differs strongly in five-plus share (0.50614 versus 0.21424) and classified entropy (0.45326 versus 0.30131). The directions of these recovery/social and housing/composition contrasts do not reverse in the 20 saved perturbations. This is descriptive preservation, not a causal explanation. Minor differences reverse: raw0/raw2 initial supply, raw0/raw2 five-plus share and raw2/raw3 EMC occupancy each reverse once; they should not determine class names.

Across all twelve seed42 specifications, the class with maximum mean B is not the class with maximum mean SOVI. This within-model ordinal statement survives source/specification substitution without transferring raw class IDs. CORE2's highest-loss group's SOVI is 78.13, versus 31.14 under CORE3: therefore the stronger claim that the highest-loss group is always low-vulnerability does **not** survive all specifications. `CROSS_SPECIFICATION_PATTERN_AUDIT.csv` distinguishes those statements.

The small group's initial availability is relatively high (0.01815), still only about 1.8% in absolute modeled terms. Under an adverse deletion the 34 original members remain but predicted membership expands to 92, yielding 36.96% purity. COVER_ALT can match it to a substantially broader group (minimum D34 purity 2.136%). Retention, purity and ARI have different meanings; none is classification accuracy or scientific validation.

CORE3 versus HIST reassigns 292 tracts at seed42; CORE2-to-CORE3 reassigns 457; CORE3-to-LAND_ALT 30, to-COVER_ALT 94 and to-HOUSING_ALT 74. Even high source correlation can alter a partition. That instability does not by itself disqualify a source. The predeclared lower-coverage quartile diagnostic trains on 1,715 and predicts all 2,287; median agreement is about 0.879 with at most 98 reassignments. It is not a new exclusion threshold.

## Final Ranked Choice

1. CORE3, under its restricted and explicitly named support definitions.
2. CORE2 if the intended analysis declines conditional classified-land information; it describes two physical dimensions, not the entire built environment.
3. LAND_ALT, COVER_ALT or HOUSING_ALT only as same-family source/contrast sensitivities, not extra primary coordinates.
4. Qualified age/hardening/height extensions remain supplementary comparison results. EPA remains descriptive. Certified FAR is ineligible.

Keep monetary stock and unadjusted ALR as distinct coordinates. Resolve domain hierarchy/budgets next with the measurement set frozen, not by reopening 64 candidates or tuning to attractive k4 groups. No final weights, k, class names or formal label promotion were selected here.

## Official Documentation

- [JRC EMC-BUILT R2025A product](https://human-settlement.emergency.copernicus.eu/emc_built_s.php) and DOI [10.2905/4cd8ccee-bfd1-48c5-9047-61c0343c41e9](https://doi.org/10.2905/4cd8ccee-bfd1-48c5-9047-61c0343c41e9).
- [ACS variance replicate documentation](https://www.census.gov/programs-surveys/acs/data/variance-tables.html); the saved 2022 B25024 payload, not the current site's default release, supplies the 80 replicates.
- [SCAG ALU20 service and original field descriptions](https://rdp.scag.ca.gov/mapping/rest/services/Housing/2020_Annual_Land_Use/MapServer/0?f=pjson); the audited payload's ALU20 fields are used, not later fire/equity/context fields.
- [USGS Annual NLCD C1.2 fractional impervious surface](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-land-cover-annual-nlcd-collection-12-fractional-impervious).
- [EPA Smart Location Database](https://www.epa.gov/smartgrowth/smart-location-mapping), with archived v3 donor counts and geometries hash-verified in the admission package.
- [LA County parcel-roll item](https://www.arcgis.com/home/item.html?id=70d93266f45a4080a97b285a471493cd) and [enriched LARIAC2014 layer metadata](https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1?f=pjson).

Original versions, definitions, URLs, byte hashes, support limitations and reuse decisions remain in the source comparison tables, official metadata files and authoritative admission package. No live metadata refresh replaces a scientific input.
