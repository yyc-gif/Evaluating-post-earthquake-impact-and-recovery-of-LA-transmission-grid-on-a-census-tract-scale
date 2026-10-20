> AUTHOR REVIEW CANDIDATE - NOT FORMAL STAGE 7

# Qualified eighth-variable decision

Retain the exact previously calculated FEMA_NCV14_CA_v119 as a **selected14-hazard frequency-area geographic screening index**. It is not a comprehensive all-hazards risk index, an observed tract disaster-frequency measurement, an electrical-outage model or an official FEMA composite field. This gate passes for a transparently qualified release-based screening construct, not for independently validated physical intensity or14 statistically independent observations.

## Exact definition suitable for Methods

For tract r and retained hazard h, define x_rh = AFREQ_rh * EXP_AREA_rh / AREA_r, using compatible square-mile areas and the released nonnegative frequency factor. Independently normalize x_rh with its valid frozen California minimum a_h and maximum b_h: u_rh=(x_rh-a_h)/(b_h-a_h). Sum the 14 u_rh equally, then min-max the sum against California records with all 14 actual factors. Frozen a_h,b_h and cohort values are supplied in inputs and candidate tables; no target source unknown is set to zero. The final0-1 index is a relative geographic screen, not a literal probability. Constant local CWAV is retained in the main source-defined set; its local separation contribution is0.

The selected hazards are CFLD,CWAV,DRGT,ERQK,HAIL,HWAV,LNDS,LTNG,RFLD,SWND,TRND,TSUN,WFIR,WNTW. AVLN,HRCN,ISTM,VLCN have entirely null target factors and are omitted explicitly, not declared physically impossible. Selection followed complete compatible source factors on all 2,299 targets before clustering, not fitted memberships or optimal silhouette. The first seven coordinates and H2 squared-distance budgets are unchanged.

Released AFREQ is itself often spatially area-weighted. The additional exposure fraction is therefore a published-method screening transformation, not a separately identified or independent occurrence-times-exposure probability. It may apply another footprint-dependent attenuation. Do not claim it reconstructs a physical impacted area or a calibrated loss probability. ERQK exposure-area construction was not independently rebuilt; the released geographical field is used as-is rather than certified as pure susceptibility.

## Why earthquake differentiates weakly

The original ERQK factor uses a USGS100-year minor-damage shaking probability surrogate and release-defined area, not PGA at2% exceedance in50 years. Original raster/model and released field annualization conventions were not reconstructed; multiplying by100 must not be used here to fabricate a validated100-year probability. Source probabilities can have limited regional contrast, but source saturation is an interpretation consistent with the released range, not a new raster-level proof.

Released AFREQ has CV0.2748, whereas the frequency-area product has CV0.0377. Coastal tracts with unusually large AFREQ often have small exposed fractions; multiplying the two attenuates those extreme values. The product's P10-P90 is0.00891805-0.00980300. Its California-scaled mean is0.9395, SD0.0387. Earthquake gives a high normalized background but little local variance, not absence of earthquake hazard.

Independent CGS MS48(2025) land-area PGA has 2294 valid comparisons and5 partial-support records left missing. Its estimand is2%-in50-year shaking intensity, with 2023 NSHM/site-response inputs. ERQK raw/product spatial ordering is not concordant with this PGA ordering (Spearman approximately-0.052/-0.038). Different severity thresholds, vintages and support prevent interpreting this as a validation failure or as interchangeability. The PGA centroid diagnostic supports all 2,299 but does not replace the five missing land-area measurements or become a fitted coordinate. All2299 still enter the typology.

## Weather-source gate

Hail and strong wind share NOAA/NWS SPC event reporting,1986-2019 source sections,80-km point buffers and49-km fishnet aggregation with national event-count scaling. Thus small tract-level numerical differences do not imply independently monitored local hazards. Hail also has report-size threshold changes and reporting/urban-location bias. Heat uses a different NWS-warning/IEM pipeline, warning-day and forecast-zone geometry,2005-2022 reference window and a5% block-intersection rule; it is not an independently measured temperature grid.

No explicit minimum-frequency substitution was located in these three acquired hazard sections. All three target factors are non-null/nonzero; this does NOT prove every tract directly experienced a recorded event. Shared buffering, forecast zones and national scaling remain provider model choices, not observed spatial detail. Hail/wind frequency-area Pearson is0.9233 but Spearman0.1949: common upper-tail/geographic patterns and ties must not be described as identical hazard ordering. Heat/hail Pearson0.6978; heat/wind0.4488. Direct asset/social variables are not used by our operator, but reporting and source geography are not demographically neutral by proof.

March2023 text has inconsistent StrongWind period descriptions: section18.1.1 says34 years while18.6 prints70; Heat published tract count/frequency ratios also do not consistently reproduce the printed16.9-year period. Area-weighted counts, source/version details and text inconsistencies remain unresolved. A uniform positive frequency scale cancels exactly in component min-max, as verified algebraically, so a constant unit/period conversion alone cannot explain the spatial ordering. Spatially inconsistent source processing would matter and is not ruled out.

## Effective influence and normalization

| hazard   |   local_range_fraction_of_CA_range |   local_normalized_sd |   signed_covariance_share |
|:---------|-----------------------------------:|----------------------:|--------------------------:|
| CFLD     |                         1          |           0.0322893   |               0.00535885  |
| CWAV     |                         0          |           0           |               0           |
| DRGT     |                         0.668637   |           0.0457471   |               0.0396965   |
| ERQK     |                         0.207959   |           0.0386956   |              -0.0130793   |
| HAIL     |                         0.283098   |           0.0926943   |               0.310726    |
| HWAV     |                         0.392287   |           0.112185    |               0.337346    |
| LNDS     |                         1          |           0.0360759   |               0.0145672   |
| LTNG     |                         0.205617   |           0.0298257   |               0.0409818   |
| RFLD     |                         0.416431   |           0.0206529   |              -0.000670096 |
| SWND     |                         0.234797   |           0.0849558   |               0.247129    |
| TRND     |                         0.00765722 |           0.000391172 |               0.000417552 |
| TSUN     |                         0.426404   |           0.0117274   |              -0.00137063  |
| WFIR     |                         0.209967   |           0.0100975   |               0.00701379  |
| WNTW     |                         0.313063   |           0.0162873   |               0.0118841   |

Heat/hail/strongwind account for about 89.5% of local summed-score variance by signed covariance attribution. This combines source heterogeneity, regional hazard variation and California reference ranges; it is NOT89.5% of physical risk or a prescribed hazard probability weight. Hail/wind share source processes, so14 nominal hazards are not14 independent dimensions. Per-hazard California ranges create implicit relative scaling despite equal summation coefficients. The final affine score normalization cancels under cohort z-scoring, whereas changing individual reference ranges does not.

Existing hazard leaveout and LA-normalization fits are reused unchanged. For K4, heat deletionARI=.9777, hail=.9904, wind=.9879, earthquake=.9959, and LA component normalization=.9830. K3 remains similarly stable to these hazard choices; K5 is much less stable to heat deletion/normalization. This supports keeping the registered vector for the K3/K4 comparison; it does not establish physical validity or justify weight tuning. The eight-variable typology remains earthquake-conditioned recovery with a selected multi-hazard context, not multi-hazard electrical-system simulation.

## Three separate authorities

1. FEMA March2023 v1.19: actual released hazard-specific fields and source processing. Not our composite, not newer NRI substituted.
2. Williams, Summers and Harwell(2024), DOI10.3390/su162310778: frequency-area operator, per-hazard min-max and normalized summation in a county implementation. The acquired paper does not unambiguously enumerate the aggregate-nine set or supply exact national extrema/public numeric workbook. No exact full county-nine replication is claimed.
3. Our extension: native2020 tract application, declared14 compatible hazards, frozen California reference,2,299 positive-population cohort and H2 clustering budget. These are study-specific choices requiring author approval, not official FEMA/provider endorsement.

Sources: [FEMA v1.19 documentation](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf), [Williams2024](https://doi.org/10.3390/su162310778), [CGS MS48](https://www.conservation.ca.gov/cgs/publications/ms48). Exact archived evidence, input hashes and page references are retained. No provider is contacted.
