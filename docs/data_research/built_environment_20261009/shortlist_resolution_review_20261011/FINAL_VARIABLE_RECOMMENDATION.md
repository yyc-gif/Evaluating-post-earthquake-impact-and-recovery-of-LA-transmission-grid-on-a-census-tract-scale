# Final Variable Recommendation

## Decision

Use **CORE3** as the preferred physical measurement specification:

1. `emc2022_total_built_land_fraction`: modeled building/built-surface ground occupancy, anchored to Sentinel-2 2022.
2. `housing_5plus_share`: the share of residential housing units in structures containing five or more units, ACS 2018-2022 five-year B25024.
3. `scag2020_classified_land_entropy`: eleven-class parcel-area diversity **within classified land**, using the audited ALU20 payload.

CORE2 (the first two variables) is the defensible minimum. CORE3 is preferred for this research question because land-use composition adds a distinct interpretation that coverage and residential configuration cannot provide. This is a measurement recommendation, not authorization to promote this round's labels or select its benchmark weights.

Keep these nonphysical measurements: `B_480_hr`, `Init_Supply`, `Grid_Degree`, `Grid_Impact`, `Grid_Betweenness`, `Redundancy_HHI`, `SOVI_SCORE`, `log1p(BUILDVALUE)`, and `ALR_NPCTL`. The comparison held their numerical values fixed against the saved D reference. B is cumulative normalized modeled service deficit over 0-480 hours; initial supply is a modeled service-availability proxy, not delivered MW. Stock is monetary building exposure; ALR is an unadjusted composite multi-hazard loss-rate percentile, not pure hazard or a second vulnerability score.

## Inclusion Reasons

**EMC coverage:** prefer the 2022 observation anchor and verified complete valid-land support over the mixed historical imagery underlying the LARIAC6 release. The used EMC product is R2025A V1.0 at 100 m, not a newly extracted 10 m dataset. Fractional cell/tract intersections allocate cell-average built surface at boundaries. That assumption cannot resolve subcell building positions. LARIAC rooflines offer finer boundaries, so EMC is not universally more accurate; no independent LA tract ground-truth experiment establishes an accuracy winner. For updated tract-scale occupancy, its temporal support is the stronger fit to the declared definition. It is not the percentage of all impervious surfaces or total urbanized land.

**ACS five-plus share:** directly represents housing-unit concentration in larger multi-unit structures. It uses B25024_006E through _009E divided by _001E; these are units, not a count or proportion of buildings. All 2,291 residential tracts have supported housing measurements, and the 2,287 spatially resolved reference tracts are retained regardless of MOE. The 80 variance replicates preserve numerator/denominator survey covariance. Median 90% MOE is 0.06748, with 158 boundary-model cases in the reference cohort. These boundary estimates and MOEs are retained; a large MOE is not evidence of a precise estimate. Its moderate SOVI association (r=0.20083 on 2,287) does not make it a social-vulnerability substitute. Selection follows its physical meaning, not that correlation.

The 80 saved-replicate fixed-center response changes a median 7.5 and at most 15 labels, but does not carry the modeled boundary variance completely. An independent simultaneous lower/upper boundary-MOE endpoint stress changes zero/one labels, respectively, with fixed centers and all other values unchanged. These two artificial endpoints are not a confidence interval, a worst-case bound or refitted clustering validation; the larger uncertainty limitation remains explicit.

**SCAG diversity:** adds parcel-area composition rather than housing type, building intensity or activity counts. Both vintages use the same exclusive eleven-class mapping and common land mask. On the identical 2,286 cross-source cohort, 2020-minus-2019 mean absolute entropy difference is 0.00522, although individual differences reach 0.20835. The newer snapshot is the preferred temporal alternative; it is not wholly independent new information. LU19 carry-forward constitutes 12.248% of county records and 36.806% of summed reported ACRES. Those are source-record statistics, not exclusive study-tract area percentages. Median classified-land support in 2,287 tracts is 0.75127 (10th percentile 0.66714). Hypothetical whole-land entropy bounds have median width 0.39371: the unclassified remainder prevents a claim about whole-tract diversity. Keep coverage alongside all profiles; do not silently impute unclassified land.

## Exclusions And Alternatives

| Measurement | Final role | Reason |
| --- | --- | --- |
| LARIAC6 footprint coverage | Same-family coverage substitution, not joint primary input | Detailed roofline geometry, but mixed image dates. r=0.94922 with EMC; mean EMC-minus-LARIAC difference 0.03496 and MAE 0.03730. One occupancy budget must not be counted twice. |
| SCAG2019 entropy | Vintage substitution / historical reference | r=0.99491 with ALU20 on common GEOIDs. Same categories and conditional-area construct; do not weight both vintages independently. |
| ACS detached share | Residential configuration substitution | B25024_002E / _001E. Shares use one housing-unit composition; r=-0.90016 with five-plus. They are not exact complements because attached, 2-4-unit and mobile/other categories remain. |
| Assessor2022 pre-1970 Main Square Footage share | Conditional observed-stock age sensitivity only | Recorded assessment stock, not a complete all-use building census. Scalar year, multiple building lines, condominiums/shared parcel identities and exempt/government support remain unresolved. Main Square Footage is not certified gross floor area. |
| LARIAC2014 valid-age footprint share | Historical age sensitivity / description | Older footprint inventory with parcel-linked assessment attributes. r=0.94153 with Assessor age is not independent validation; exact historical roll/join cardinality remains unresolved. |
| ACS residential pre-1970 unit share | Residential-age sensitivity / description | Well-defined residential survey construct, but a different denominator/population from all-use stock age. Not required for the coverage/configuration/composition core. |
| NLCD C1.2 2022 fractional imperviousness | Optional hardening extension, supplementary | Roads, parking and other constructed surfaces give a distinct construct. r=0.85098 with EMC does not make it identical. HARDEN_EXT was compared; adding it is not necessary to answer the declared three-construct target. |
| Historical LARIAC roof height | Conditional vertical-form extension, supplementary | Distinct vertical form with numeric/support QA, but mixed old observations and no synchronized 2022 height inventory or independent local accuracy certification. Height is not floors or gross FAR. |
| JRC ANBH positive-surface mean height | Alternative historical height summary, supplementary | Different modeled-cell support. Do not jointly add multiple summaries as independent vertical dimensions. |
| EPA household/job activity mix | Descriptive historical activity only | Household/job counts, not parcel-area composition. Uniform donor-land allocation conserves counts but does not certify target locations. Sensitivity alternatives change entropy by up to 0.435. |
| Certified gross FAR | Ineligible, PENDING_DATA | No certified floor-area denominator or resolved building identity/condominium accounting. Do not manufacture FAR from Main Square Footage or height. |

No age coordinate enters the preferred primary model. This is a scope-and-support decision, not a claim that age is unimportant. The Assessor single-line/noncondo/nonshared restriction retains a median 0.751 of recorded area, with a 90th-percentile absolute age-share change about 0.130. That restriction does not deduplicate buildings and is not a replacement census. CORE4 is eligible only when explicitly named an **observed assessment-area age** diagnostic; it fails the stronger complete all-use-age interpretation. Its missing tract, 06037115103, requires a paired 2,286-tract no-age comparator.

Every one of the original 64 entries has a bounded disposition in `FINAL_SHORTLIST_DISPOSITIONS.csv`. Other count/size/volume summaries, social or occupancy variables do not enter merely because they are available. Exact derived identities require identical supports, and low VIF cannot establish a new construct.

## Stock And Expected Loss

Retain `log1p(BUILDVALUE)` and `ALR_NPCTL` separately once the physical set is fixed. They represent asset amount and exposure-normalized multi-hazard loss propensity. On the same 2,286 tracts r=0.2457, Spearman=0.2343 and marginal five-fold spline R-squared=0.0623. Conditional diagnostics controlling CORE3 and SOVI are supplied, not used as an automatic admission threshold. ALR's component/loss weighting and the archived LA earthquake dominance remain part of its interpretation. It is neither pure hazard nor EAL divided by BUILDVALUE. Do not add RISK_SCORE or vulnerability-adjusted ALR beside SOVI, or reintroduce EAL to duplicate a stock/loss combination.

## Comparison Limitations And Remaining Decision

CORE3 seed42 sizes are 650, 802, 801 and 34; these are diagnostic raw labels, not the old published class IDs. Against HIST, 292/2,287 change class after overlap matching (ARI=0.65502). Its median seed-pair ARI is 1.0000, but spatial median ARI is 0.87922, minimum 0.69293, with up to 255 reassignments. The 34-member group can expand to 92, retaining its members while purity falls to 36.96%. Accurate feature measurements and stable optimization do not establish a uniquely valid four-class taxonomy.

Decide the **domain hierarchy and squared-distance budgets**, not another open variable search: whether coverage/configuration/composition share one physical parent budget, whether stock and loss propensity share a parent or receive separate budgets, and how recovery, grid and social domains balance against them. This round's five equal 20% parent budgets are a controlled comparison benchmark only. See `DOMAIN_WEIGHT_REQUIREMENTS.md`. Do not select those budgets to maximize silhouette, reproduce old labels, or preserve the minority class.
