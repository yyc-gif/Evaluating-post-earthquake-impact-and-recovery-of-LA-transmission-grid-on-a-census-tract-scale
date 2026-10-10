# Manuscript Revision Changelog

Author-confirmed S19 source; clean independent copy, not tracked changes. Original abstract, conclusions, 108 unaffected source paragraphs, all three original tables, style definitions, metadata, headers/footers and six original figure payloads are preserved. No silent reference/figure renumbering. Original page flow can change because of inserted text; actual rendering must be reviewed. One existing framework reference issue number is corrected using publisher metadata.

## S19 P0002

Action: REVISE. Qualify new Stage7 dates; retain independent scientific baseline

Before:

Resubmission reconstruction from the retained July 23, 2026 manuscript. Coauthor review draft; all numerical findings below are from the frozen September 2026 formal experiment unless explicitly identified as external evidence.

After:

Resubmission reconstruction from the retained July 23, 2026 manuscript. Coauthor review copy with Stage 7 integration dated October 10, 2026. Unaffected network and restoration findings retain their frozen September 2026 scope; the descriptive four-class candidate is supplied for author review, not formal promotion.

## S19 P0009

Action: REVISE. Make the third question's Stage7 measurement terminology precise

Before:

Three questions organize the study. First, how do station damage and source-path connectivity propagate to spatially different tract service deficits? Second, how do scarce crews, travel, task duration, and fixed repair priorities alter system and community recovery under identical physical realizations? Third, where do long recovery burdens coincide with vulnerability, built-environment exposure, risk, and modeled grid dependency, and who benefits or loses when restoration priority changes? The network is an abstraction and tract assignments are dependency proxies. These boundaries motivate the external candidate benchmark, mapping and gate contrasts, and explicit loss decomposition rather than claims of feeder-level validation or delivered electricity.

After:

Three questions organize the study. First, how do station damage and source-path connectivity propagate to spatially different tract service deficits? Second, how do scarce crews, travel, task duration, and fixed repair priorities alter system and community recovery under identical physical realizations? Third, where do long recovery burdens coincide with vulnerability, built form, economic stock, multi-hazard expected loss, and modeled grid dependency, and who benefits or loses when restoration priority changes? The network is an abstraction and tract assignments are dependency proxies. These boundaries motivate the external candidate benchmark, mapping and gate contrasts, and explicit loss decomposition rather than claims of feeder-level validation or delivered electricity.

## S19 P0023

Action: REVISE. Preserve independent quartile/paired estimands; replace only obsolete Stage7 tail

Before:

The fixed NRI-derived SOVI_SCORE quartiles label Q1 lowest and Q4 highest vulnerability. For each sequence and physical realization we calculate absolute population-weighted normalized burden in each quartile, signed Q4−Q1 gap, its absolute value, population-weighted tract burden Gini, and paired tract differences relative to a named rule. Improved, near-zero, and worsened tracts use a predeclared ±1 h practical threshold on paired mean effects; unresolved tracts remain separate. This threshold is not statistical significance. Bootstrap and direction-frequency comparisons resample physical realizations, not tracts. The retained Stage 7 PCA/K-means and hotspot screening examine co-occurrence among recovery, vulnerability, built environment, risk, and grid-dependency attributes. They are descriptive typologies and do not establish causal mechanisms.

After:

The fixed NRI-derived SOVI_SCORE quartiles label Q1 lowest and Q4 highest vulnerability. For each sequence and physical realization we calculate absolute population-weighted normalized burden in each quartile, signed Q4−Q1 gap, its absolute value, population-weighted tract burden Gini, and paired tract differences relative to a named rule. Improved, near-zero, and worsened tracts use a predeclared ±1 h practical threshold on paired mean effects; unresolved tracts remain separate. This threshold is not statistical significance. Bootstrap and direction-frequency comparisons resample physical realizations, not tracts.

## After The fixed NRI-derived SOVI_SCORE quartiles label Q

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

We describe community co-occurrence using the frozen D-model joint typology rather than using community attributes to predict additional earthquake damage. The electricity-model domain contains 2,315 tracts. We retain the existing 2,291-tract residential-typology cohort, of which 2,287 have complete primary coordinates; four tracts with unresolved geometry remain unclassified without imputation. The primary space has five analytical domains: recovery and initial service (B_480_hr and Init_Supply); mapped grid dependence (degree, algebraic-connectivity impact, betweenness, and dependency concentration HHI); built environment (classified-land entropy, roof-outline coverage, and observed pre-1970 building-area share); social vulnerability (SOVI_SCORE); and economic stock and multi-hazard loss (log1p building value and ALR_NPCTL).

## After We describe community co-occurrence using the froz

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The recovery coordinates come from the saved 1,000-realization 2pc50 direct-community sequence at the reference C57_D1 condition with mapping M1 and gate G1. B_480_hr is mean normalized modeled service deficit integrated over 0-480 h, in equivalent complete-service-loss hours. Init_Supply is mean initial modeled service availability, not delivered MW. T80 is reported descriptively as the 80% crossing time of the mean tract trajectory; it is not a primary coordinate or the mean of realization-specific crossing times.

## After The recovery coordinates come from the saved 1,000

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Land-use entropy is derived from the archived SCAG 2019 Annual Land Use service (ALU 2019.1, updated February 2021): -sum(p_j log p_j)/log(11), with p_j the area fraction of each of 11 predeclared exclusive classified-land categories. Unknown classifications, water, gaps, and ambiguous overlaps are outside this denominator, with classified-land coverage reported separately. Building footprint coverage is the union area of archived LARIAC6 2020 roof outlines divided by tract land area; it is not floor area or impervious cover. The age coordinate uses the original LARIAC4 2014 outlines and associated assessor YearBuilt1, dividing valid observed pre-1970 outline area by all valid observed-age outline area. Missing ages are not treated as newer buildings. Mixed acquisition dates, jurisdiction-dependent outline capture, and incomplete age coverage preclude interpreting these records as a complete 2020 building-age census (SCAG, 2021; Los Angeles County, 2014, 2020).

## After Land-use entropy is derived from the archived SCAG

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The archived FEMA National Risk Index is version 1.19, March 2023 (FEMA, 2023). Building value is economic building-stock value in 2022 USD, not physical form, household wealth, seismic capacity, or electrical demand. ALR_NPCTL nationally ranks an expected-loss-weighted composite of consequence-specific annual-loss-rate percentiles. It is unadjusted for the Community Risk Factor but remains a multi-hazard expected-loss measure, not pure hazard or a simple total-loss/total-exposure quotient. We retain SOVI_SCORE as the separate social domain. The earlier RISK_SCORE incorporated expected annual loss, social vulnerability, and community resilience and is not retained as an urban-form coordinate.

## After The archived FEMA National Risk Index is version 1

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Each coordinate is standardized using the saved classified-cohort mean and population standard deviation (ddof=0). Only building value is log1p-transformed in the primary model; burden remains in raw hours. Within a domain with p coordinates, each standardized coordinate is multiplied by sqrt(0.20/p), giving every domain 20% of the squared-distance weighting budget. We use the exact saved k=4, seed=42 K-means labels, with original n_init=100 and the Lloyd algorithm (MacQueen, 1967; Lloyd, 1982). No PCA reduction defines this partition. Population density, ACS residential housing age and five-plus-unit share, T80, and EAL_SCORE are descriptive or sensitivity measurements outside the primary space. Cluster summaries weight tracts equally unless population weighting is explicitly identified.

## After Each coordinate is standardized using the saved cl

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The saved spatial deletion analysis evaluates partition agreement, class retention, purity, and profile-direction stability, not predictive accuracy (Hubert and Arabie, 1985). The joint typology includes modeled recovery outcomes among its inputs, so between-class recovery differences are descriptive and not independent evidence that community attributes caused recovery differences. The new classes do not update the former hotspot score or establish a restoration priority; vulnerability-quartile policy comparisons remain separate from cluster membership.

## S19 P0040

Action: REVISE. Keep independent Q4 resource contrasts; withdraw old five-class/transform/hotspot result

Before:

The Q4 targeting tradeoff depends on resources. At C29, vulnerability-first lowers Q4 burden by 6.385 h relative to hospital-first, but adds 1.710 h to population burden, 6.255 h to T80, and 15.268 h to absolute group separation. At C86/C114, policy differences approach zero. Under the three historical hazards, Q4 gains relative to hospital-first are only 0.004–0.015 h; the larger 2pc50 effect cannot be generalized to every hazard. The Stage 7 descriptive typology retains recovery, vulnerability, built environment, risk, and dependency variables. Its 2,291 analyzed tracts form five clusters in the formal log-transformed specification; 24 tracts are excluded from the clustering input rather than silently assigned. Cluster membership is sensitive to raw versus log-tailed exposure features (adjusted Rand index 0.484), although the top-ten slow-vulnerable hotspot overlap is complete. These clusters screen co-occurring tract attributes; they do not attribute individual recovery times causally to vulnerability or housing.

After:

The Q4 targeting tradeoff depends on resources. At C29, vulnerability-first lowers Q4 burden by 6.385 h relative to hospital-first, but adds 1.710 h to population burden, 6.255 h to T80, and 15.268 h to absolute group separation. At C86/C114, policy differences approach zero. Under the three historical hazards, Q4 gains relative to hospital-first are only 0.004–0.015 h; the larger 2pc50 effect cannot be generalized to every hazard.

## After The Q4 targeting tradeoff depends on resources. At

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The four-class joint typology classifies 2,287 residential tracts: C1 contains 850, C2 34, C3 651, and C4 752. Their mapped populations are 3,387,008, 124,158, 2,440,001, and 3,085,986, respectively, totaling 9,037,153. Four residential tracts remain unclassified because of unresolved geometry: 06037189703, 06037301601, 06037301602, and 06037404600, with 12,390 mapped residents. The spatial distribution and standardized joint profiles are shown in Figures 7 and 8; Table 4 retains original units. C1-C4 are membership identifiers, not a priority order.

## After The four-class joint typology classifies 2,287 res

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

C1 and C4 both have high mean social vulnerability (SOVI_SCORE 79.16 and 82.87), but differ in classified-land mix and observed building age. Their mean normalized land-use entropies are 0.283 and 0.489, and mean observed pre-1970 building-area shares are 0.840 and 0.691. Mean roof-outline coverage is 0.265 and 0.277. C1 has mean cumulative service loss of 32.42 h and T80 of 43.71 h, compared with 33.89 h and 44.77 h in C4. These are co-occurring profiles, not estimated built-environment effects on restoration.

## After C1 and C4 both have high mean social vulnerability

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

C3 has the highest mean cumulative service loss (36.34 h) and mean tract T80 (46.78 h), while its mean SOVI_SCORE is substantially lower (31.06) than in C1 and C4. Thus the class with the greatest mean modeled loss is not the class with the highest mean social vulnerability. Its mean classified-land entropy, roof-outline coverage, and observed pre-1970 share are 0.335, 0.231, and 0.688. Its median building stock is approximately 659.0 million 2022 USD, an economic quantity rather than a capacity or damage-resistance measurement.

## After C3 has the highest mean cumulative service loss (3

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

C2 has relatively greater mean initial modeled availability (0.01815, or 1.815%) and lower cumulative service loss (23.60 h), with mean T80 of 38.50 h. Initial availability nevertheless remains very low in absolute terms, and this 34-member class must not be described as universally resilient. Its mean SOVI_SCORE is 67.99 but its median is 85.04, illustrating heterogeneity that a class mean can conceal. In Figure 8 its initial-service standardized mean is +7.15, beyond the +/-1.5 color saturation limit; the annotation and Table 4 preserve that magnitude.

## After C2 has relatively greater mean initial modeled ava

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The saved spatial checks support C3's higher cumulative loss and lower social vulnerability relative to C1/C4, and the C1/C4 contrasts in classified-land mix and observed age. They do not support every minor distinction: C1/C4 degree and impact rankings reverse in 12 of 20 deletion cases, and the small C3/C4 age difference reverses in seven. Median full-cohort ARI is 0.9234 for D and 0.9458 for the EAL alternative; the 20 cases include only 17 unique deletion sets. In the most adverse D case, C2 retains all original 34 members but expands to 92 tracts, with 36.96% purity. Retention therefore does not establish a stable small-class boundary. Supplementary Figure S_STAGE7 documents these distinctions. Agreement with the former five-class partition is low (ARI 0.216624); its old interpretations and cluster-specific hotspot findings are not transferred to the new classes.

## After The saved spatial checks support C3's higher cumul

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Table 4. Frozen four-class original-unit profiles. Panel A reports equal-tract recovery means and mapped population totals. Panel B reports physical/social means and economic/loss-rate medians; stock is million 2022 USD. Fractions use the separate denominators in Methods. These summaries are not intervention priorities.

## After Table 4. Frozen four-class original-unit profiles.

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Panel A

## After

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Panel B

## S19 P0047

Action: REVISE. Retain calibration/repair/Q4 limitations; qualify only Stage7 screening

Before:

The positive repair-duration parameters and pooled C57 crews are scenarios rather than observed earthquake staffing or calibrated task times. Historical earthquake fields are hazard contexts, not validation against historical restoration milestones. The distributional results are normalized modeled service deficits, not resident hours without electricity. The vulnerability-first policy tests one transparent Q4-targeted decision and does not isolate a complete efficiency–equity frontier. Cluster and hotspot outputs are descriptive screening. These boundaries are material to application: a future operational study would need utility feeder/customer links, switching and demand, crew records, and observed outages before recommending a specific field dispatch order.

After:

The positive repair-duration parameters and pooled C57 crews are scenarios rather than observed earthquake staffing or calibrated task times. Historical earthquake fields are hazard contexts, not validation against historical restoration milestones. The distributional results are normalized modeled service deficits, not resident hours without electricity. The vulnerability-first policy tests one transparent Q4-targeted decision and does not isolate a complete efficiency–equity frontier. The four-class typology is descriptive; the old hotspot conclusions require separate revalidation. These boundaries are material to application: a future operational study would need utility feeder/customer links, switching and demand, crew records, and observed outages before recommending a specific field dispatch order.

## After The positive repair-duration parameters and pooled

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The four-class joint typology separates different combinations of modeled recovery, grid dependence, built environment, social vulnerability, and economic stock/multi-hazard expected loss. C1 and C4 share relatively high social vulnerability while differing in classified-land mix and observed age; C3 combines the greatest mean cumulative modeled service loss with substantially lower mean social vulnerability. This descriptive distinction cautions against using either social vulnerability or a single recovery statistic as a complete community characterization. Because recovery enters the clustering space, these differences do not validate a predictive model or identify a causal effect of age, urban form, or vulnerability on recovery.

## After The four-class joint typology separates different

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The equal-domain budget is a transparent analytical convention, not an empirically estimated importance weight. Spatial checks support the principal large-class descriptions but expose sensitivity of small-class specificity and minor grid rankings. C2's 1.815% mean initial availability is only relatively higher, and full retention of its original members can coexist with a 92-member expanded class and 36.96% purity. Neutral C1-C4 identifiers avoid overstating stable archetypes. Land-use entropy is conditional on classified land, roof coverage is not floor area, and 2014 observed building age is incomplete and temporally distinct from 2020 geometry. Although ALR_NPCTL is multi-hazard, earthquakes account for 98.1563% of pooled FEMA expected annual loss in the archived 2,291-tract audit; this is neither a hazard-only measure nor evidence of balanced multi-hazard exposure.

## After The equal-domain budget is a transparent analytica

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The old five-class hotspot-by-cluster findings require separate revalidation. Neither new membership nor class-level loss establishes an intervention rank, repair allocation, or optimal priority. The fixed SOVI quartiles and paired restoration-policy comparisons remain independent analyses and are not relabeled as cluster effects. Before making location-specific intervention recommendations, any retained hotspot procedure must be audited against its own saved inputs, geography, and scoring definition; that analysis is outside this manuscript-integration task.

## After The code, processed and derived data, and retained

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

The Stage 7 review candidate is traceable to the frozen October 10 integration preview (84d7ac6410a00c83ec01913674f0167ad07551be), feature validation (50df10481815f3dd94c46dc9443f93cfdb1c5014), spatial validation (ecf98c6cbda280914962582a819943fabfa41132), and FEMA version audit (65f388f9710566ffa845808bd7b10503de4da608). Saved GEOID membership, original-unit profiles, source payload hashes and transformation/domain-weight definitions are retained without new simulation or clustering; source geometry failures remain unclassified.

## After Federal Emergency Management Agency. (2013). Multi

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Federal Emergency Management Agency. (2023). National Risk Index Technical Documentation (Version 1.19.0, March 2023). Archived original publication: https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf

## After Homeland Infrastructure Foundation-Level Data. (n.

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Hubert, L., & Arabie, P. (1985). Comparing partitions. Journal of Classification, 2, 193-218. https://doi.org/10.1007/BF01908075

## After Loni, A., & Asadi, S. (2024). A data-driven approa

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Los Angeles County. (2014). Countywide Building Outlines (LARIAC4_BUILDINGS_2014), associated assessor attributes. https://www.arcgis.com/sharing/rest/content/items/57f5fc977d6a427a978003a6229ab5e7/info/metadata/metadata.xml?format=default&output=html

## After Los Angeles County. (2014). Countywide Building Ou

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Los Angeles County. (2020). Countywide Building Outlines (LARIAC6_BUILDINGS_2020, layer 0; mixed acquisition dates). https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0

## After Soleimani, N., Davidson, R. A., Davis, C., O’Rourk

Action: INSERT. Frozen Stage7 integration

Before:

[No existing paragraph]

After:

Southern California Association of Governments (SCAG). (2021). 2019 Annual Land Use (archived ALU 2019.1 service, updated February 2021). https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0

## S19 P0100

Action: REVISE. Correct publisher-verified issue number for the existing Xu2007 framework citation

Before:

Xu, N., Guikema, S. D., Davidson, R. A., Nozick, L. K., Çağnan, Z., & Vaziri, K. (2007). Optimizing scheduling of post-earthquake electric power restoration tasks. Earthquake Engineering & Structural Dynamics, 36(3), 265-284. https://doi.org/10.1002/eqe.623

After:

Xu, N., Guikema, S. D., Davidson, R. A., Nozick, L. K., Çağnan, Z., & Vaziri, K. (2007). Optimizing scheduling of post-earthquake electric power restoration tasks. Earthquake Engineering & Structural Dynamics, 36(2), 265-284. https://doi.org/10.1002/eqe.623

## After original Figure6

Action: INSERT. New Stage7 figure only; original Figure1-6 identifiers/media preserved

Before:

[No existing paragraph]

After:

Figure 7. Four-class joint typology of 2,287 complete residential tracts under 2pc50, the reference 57-crew/unit-duration condition and direct-community recovery sequence. Classes use the five equal analytical domains in the Methods; C1-C4 denote saved seed-42 membership and imply no ranking. Four residential tracts with unresolved physical-feature geometry are gray and unclassified. The 24 tracts outside the residential domain are white. Boundaries are archived census-tract polygons within the exact 2,315-tract electricity-model domain, projected in California Albers (EPSG:3310); the outer outline is the study-tract union, not an invented utility boundary. The scale bar is in km and the arrow follows geographic north at its mapped position. This is descriptive spatial classification, not causal attribution or validated intervention priority.

## After original Figure6

Action: INSERT. New Stage7 figure only; original Figure1-6 identifiers/media preserved

Before:

[No existing paragraph]

After:

Figure 8. Tract-unweighted means of the 12 primary coordinates after standardization across the same 2,287 classified tracts (whole-cohort mean zero, population standard deviation one). Five grouped row blocks represent recovery/initial service, grid dependency, built environment, social vulnerability and economic stock/multi-hazard loss. The heatmap shows unweighted coordinate z scores for visual comparison, not the sqrt-domain-weighted values used for clustering. Cell annotations retain actual standardized means; colors saturate outside +/-1.5 standard deviations, indicated by colorbar extensions, including the C2 initial-service mean (+7.15). Building stock is log1p-transformed before standardization. Labels identify the underlying measurements; the color scale is dimensionless, not hours, fractions or dollars. Raw means, medians, units and observation coverage are in the companion profile tables. T80 and population density are descriptions outside the primary coordinates.

## Unchanged Findings Requiring Separate Author Review

S19 P0004/P0021/P0043/P0049 report a September GA search that retained Impact-first. Later October optimization research uses different search budgets and contains better diagnostic candidates. These statements are retained, not silently reconciled by replacing a formal sequence. The author must explicitly scope experimental epochs or authorize a separate GA/manuscript update before submission. Older supplementary SVI/source-gate results and duplicate S6 numbers are also outside this Stage7 edit.
