"""Write specific decisions from completed numerical evidence, without new fits."""
from common import *
import pandas as pd,numpy as np,re

def read(n):return pd.read_csv(lp(OUT/n),dtype={'tract_id':str})
def put(n,t):lp(OUT/n).write_text(t.strip()+'\n',encoding='utf-8',newline='\n')
def table(f):return f.to_markdown(index=False,floatfmt='.5f')

def main():
    compare=read('BOUNDED_MODEL_COMPARISON.csv');pairs=read('SAME_CONSTRUCT_SOURCE_SUBSTITUTIONS.csv');q=read('SHORTLIST_MEASUREMENT_QA.csv');mat=read('SHORTLIST_FEATURE_MATRIX.csv');epa=read('EPA_ALLOCATION_SENSITIVITY_SUMMARY.csv');acs=read('ACS_CONFIGURATION_UNCERTAINTY.csv');inc=read('INCREMENTAL_CONSTRUCT_INFORMATION.csv');cov=read('COVERAGE_SAMPLE_SENSITIVITY.csv');vr=read('ACS_FIXED_MODEL_MEASUREMENT_SENSITIVITY.csv');small=read('MINORITY_CLASS_STABILITY.csv');between=read('BETWEEN_MODEL_COMPARISONS.csv');profiles=read('CLUSTER_PROFILE_VALUES.csv');rev=read('PROFILE_DIRECTION_REVERSAL_SUMMARY.csv');g=compare.set_index('model').loc['CORE3'];gate=json.loads(lp(OUT/'MEASUREMENT_COHORT_QA.json').read_text(encoding='utf-8'))
    reg=frame('candidate_admission_rebuild_20261010/CANDIDATE_REGISTER.csv');assert len(reg)==64
    primary={'emc2022_total_built_land_fraction':'Current modeled built-surface occupancy, with2022 observation support; use one coverage coordinate.','housing_5plus_share':'Residential unit concentration in multi-unit structures; explicit housing denominator,80 VRE, moderate SOVI overlap.','scag2020_classified_land_entropy':'Adds classified parcel-area composition, not density or residential structure; actual2020 numeric overlay and lineage/coverage QA.'}
    substitutes={'building_footprint_coverage':'Detailed clipped vector rooflines; historical/mixed imagery substitute for EMC, not independent second coverage.','land_use_entropy':'SCAG2019 same-construct temporal substitute; do not co-weight with2020.','housing_detached_share':'Alternative contrast within the same housing-unit composition; not exactly1 minus5+ because intermediate/other types exist.'}
    age={'assessor2022_actual_pre1970_main_area_share':'Conditional recorded-assessment stock only. Main Square Footage, shared condominium identities, scalar year on multiple lines and exempt-stock completeness do not support complete all-use age.','all_use2014_pre1970_area_share':'Historical valid-age footprint stock; older mixed imagery and parcel-linked assessment fields, not independent confirmation of2022 age.','acs_residential_pre1970_share':'Residential housing-unit age; different population/denominator and survey uncertainty, not all-use stock.'}
    optional={'nlcd_c12_2022_impervious_fraction':'Verified different hardening construct includes roads. Useful explicit extension, not necessary for the declared building-coverage/configuration/composition core.','outline_height_area_weighted_centroid_m':'Distinct vertical roof-height form but older mixed support and unvalidated heights; conditional historical extension only.','jrc_anbh_positive_surface_mean_m':'Historical modeled height on positive cells with different support and substantial paired differences; not a second primary height coordinate.'}
    decisions=[]
    for r in reg.to_dict('records'):
        c=r['candidate_id'];status=r['disposition']
        if c in primary:choice='PREFERRED_PRIMARY';reason=primary[c]
        elif c in substitutes:choice='SOURCE_OR_CONFIGURATION_SUBSTITUTE';reason=substitutes[c]
        elif c in age:choice='AGE_SENSITIVITY_ONLY';reason=age[c]
        elif c in optional:choice='OPTIONAL_EXPLICIT_CONSTRUCT';reason=optional[c]
        elif c=='epa_household_job_activity_mix':choice='DESCRIPTIVE_ALLOCATION_SENSITIVITY';reason='Historical activity counts and estimated donor allocation; different construct, not parcel-area entropy. Concentration stress tests expose target allocation uncertainty.'
        elif c in ['BUILDVALUE','log1p_BUILDVALUE','ALR_NPCTL']:choice='SEPARATE_ECONOMIC_COORDINATES';reason='Keep one log-stock representation and the official unadjusted multi-hazard loss-rate percentile; do not double-weight raw/log versions.'
        elif c=='assessor2022_gross_floor_area_ratio':choice='INELIGIBLE';reason='PENDING_DATA. No certified gross floor area or structure/condominium accounting. Must not be fitted.'
        elif c in ['EAL_SCORE','EAL_VALT']:choice='RISK_DEFINITION_ALTERNATIVE_NOT_THIS_EXPERIMENT';reason='Combined expected-loss/exposure rank or dollar representation; changes the research coordinate and is not equivalent to independent asset stock plus propensity. Score and value are not independent.'
        elif c in ['ALR_VALB','ALR_VALP','ALR_VALA']:choice='CONSEQUENCE_SPECIFIC_DESCRIPTIVE';reason='Component-specific rates do not replace the overall multi-hazard/all-consequence coordinate; undefined agricultural denominators remain missing.'
        elif status in ['REJECT','PENDING_DATA']:choice='INELIGIBLE';reason=r['admission_condition_or_exclusion_reason']
        else:choice='DESCRIPTIVE_OR_DEPENDENT_NOT_PRIMARY';reason=r['admission_condition_or_exclusion_reason']+' No separate primary construct is justified here.'
        decisions.append(dict(candidate_id=c,measurement_admission=status,shortlist_decision=choice,reason=reason))
    save('FINAL_SHORTLIST_DISPOSITIONS.csv',decisions)
    # Attach definitions and dates to the actual pairwise numerical comparison.
    stat=read('CANDIDATE_SOURCE_COMPARISON.csv');lookup=q.set_index('feature')
    for side in ['a','b']:
        for field in ['construct','definition','unit','vintage','source_url','source_commit']:
            stat['source_'+side+'_'+field]=stat['feature_'+side].map(lookup[field])
    save('CANDIDATE_SOURCE_COMPARISON.csv',stat)
    source=getattr(pairs,'pearson');line=read('SCAG2020_RECORD_LINEAGE.csv').set_index('source_origin').loc['LU19'];ageqa=read('ASSESSOR_AGE_SUPPORT_SENSITIVITY.csv');ar=ageqa.loc[ageqa.restriction.eq('single_line_noncondo_nonshared')];r=stat.loc[stat.feature_a.eq('log1p_BUILDVALUE')&stat.feature_b.eq('ALR_NPCTL')].iloc[0]
    put('FINAL_VARIABLE_RECOMMENDATION.md',f'''
# Final variable recommendation

**Prefer CORE3:** `emc2022_total_built_land_fraction` + `housing_5plus_share` + `scag2020_classified_land_entropy` for the physical coordinates. This is a limited three-construct set: built-surface occupancy, residential unit configuration, and classified parcel-area composition. It is not a comprehensive all-building or built-environment census.

Keep the nonphysical coordinates fixed: `B_480_hr`, `Init_Supply`, `Grid_Degree`, `Grid_Impact`, `Grid_Betweenness`, `Redundancy_HHI`, `SOVI_SCORE`, `log1p(BUILDVALUE)` and `ALR_NPCTL`. This recommendation concerns measurements, not final weights, labels or formal promotion.

## Why each coordinate enters

{table(pd.DataFrame([dict(variable=k,inclusion_reason=v) for k,v in primary.items()]))}

The preferred minimal set is CORE2 (EMC+ACS5+). CORE3 adds a genuinely different land-use composition coordinate with an explicit classified-land support restriction. The recommendation adds composition because the research target includes community land uses, not because its k4 clusters look cleaner. The residual variance fractions after controlling the other core coordinates, SOVI and log stock are {inc.set_index('feature').loc['emc2022_total_built_land_fraction','residual_variance_fraction']:.3f}, {inc.set_index('feature').loc['housing_5plus_share','residual_variance_fraction']:.3f} and {inc.set_index('feature').loc['scag2020_classified_land_entropy','residual_variance_fraction']:.3f}. These statistics support distinguishability but do not prove independence.

## Why alternatives do not enter together

{table(pd.DataFrame([dict(variable=k,decision='substitute, not co-input',reason=v) for k,v in substitutes.items()]))}

{table(pd.DataFrame([dict(variable=k,decision='age sensitivity only',reason=v) for k,v in age.items()]))}

{table(pd.DataFrame([dict(variable=k,decision='optional separately labeled extension',reason=v) for k,v in optional.items()]))}

Age is omitted from the preferred primary specification. This is not a finding that age is unimportant: the all-use source population and denominator are incomplete or historical, and residential age would change the target population. The Assessor age coverage is internal to recorded main assessment area. Removing multiple-line, condominium and shared-coordinate records is a restriction diagnostic, not valid building deduplication; it retains a median {ar.recorded_area_retained_fraction.median():.3f} of recorded area and changes the observed-age share by as much as {ar.difference_from_all_recorded.abs().quantile(.9):.3f} at the90th percentile.

EPA stays descriptive. It measures historical household/job activity, not parcel-area composition; the tested allocation assumptions preserve totals while altering target entropy. Certified FAR is ineligible. Building count, mean area and their product are not independent coverage evidence; other housing shares share one composition; vegetation, occupancy, population density and building monetary value are not automatically physical-form coordinates. Every one of the64 entries has a disposition in FINAL_SHORTLIST_DISPOSITIONS.csv.

## Retain asset stock and loss propensity separately

Retain `log1p(BUILDVALUE)` and `ALR_NPCTL`. Asset amount and exposure-normalized multi-hazard expected-loss propensity are different research coordinates. On the common2,286 sample their Pearson correlation is {r.pearson:.4f}, Spearman {r.spearman:.4f}; marginal nonlinear overlap is {r.nonlinear_5fold_spline_R2:.4f} cross-validated R². EMC/ACS/composition do not express monetary stock. EAL would intentionally combine exposure and expected losses and would remove a separately interpretable stock coordinate. ALR is not pure hazard and still reflects consequence composition/loss weighting. Do not add RISK_SCORE or the vulnerability-adjusted ALR beside mandatory SOVI.

## What remains a real decision

Decide the conceptual domain hierarchy and squared-distance budgets **before** the next comparison. Do the three physical constructs share one budget, and do stock and loss propensity share one parent budget or have separate budgets? Recovery/initial service, grid dependency and social vulnerability also require declared budgets. The current five×0.2 setting is a comparison benchmark only. See DOMAIN_WEIGHT_REQUIREMENTS.md.

## Fixed-k4 limitation

CORE3 optimization seeds are highly reproducible (pairwise median ARI {g.full_seed_pair_ARI_median:.4f}, minimum {g.full_seed_pair_ARI_min:.4f}), but spatial deletion median ARI is {g.spatial_ARI_median:.4f}, lower-tail5th percentile {g.spatial_ARI_p05:.4f}, and minimum {g.spatial_ARI_min:.4f}. Up to {int(g.reassigned_n_max)} tracts change after training-overlap label alignment. The34-tract group can expand to {int(g.D34_prediction_n_max)} predicted members with purity {g.D34_purity_min:.2%}. Thus the measurements are recommended; the current equal-budget k4 partition is not established as a universally stable final typology. Do not preserve a class by changing weights or deleting Init_Supply. Any later finalist-only k check requires a separate preregistration. No further fits were launched.
''')
    put('FINAL_CANDIDATE_CONSTRUCT_DECISION.md',f'''
# Construct and shortlist decision

Starting commit: `{BASELINE}`. The scientific selection is **CORE3**, with **CORE2** as its restricted minimal version. CORE4, AGE_ACS and AGE_HIST are age sensitivities, not mandatory upgrades. COVER_ALT, LAND_ALT and HOUSING_ALT replace measurements of a defined coordinate; HARDEN_EXT and HEIGHT_HIST_EXT change the set of physical constructs. HIST is historical reference only. Gross FAR and EPA_ACTIVITY_EXT are ineligible in this comparison for the stated definitions, not silently zero-filled.

## Identical-GEOID source comparisons

{table(pairs[['family','n','pearson','spearman','mean_difference','mean_absolute_difference','p90_absolute_difference','units']])}

Coverage difference is EMC minus LARIAC: about {pairs.loc[pairs.family.eq('coverage'),'mean_difference'].iloc[0]*100:.2f} percentage points. This is a source/time/model difference, not measured accuracy. Prefer2022 support for the updated occupancy coordinate; keep detailed vector outlines as the substitute. Neither product has independent LA tract accuracy certification.100m EMC boundary intersections assume the pixel's modeled density within a partial cell. LARIAC has precise roofline boundaries but mixed imagery dates and minimum-detection/segmentation limitations. The County official metadata documents earlier imagery and different capture thresholds; the2020 release name is not a uniformly2020 observation date.

SCAG2020 has actual ALU20 codes and the same11-class exclusive-area convention as2019. LU19 carry-forward represents {line.record_fraction:.2%} of county records and {line.reported_acres_fraction:.2%} of summed reported ACRES. Those are source-record diagnostics, not nonoverlapping study-land proportions. Updated code/source records and carried-forward land coexist. Mean absolute entropy change is {pairs.loc[pairs.family.eq('land_use'),'mean_absolute_difference'].iloc[0]:.5f}; most differences are small but maximum {pairs.loc[pairs.family.eq('land_use'),'maximum_absolute_difference'].iloc[0]:.5f} is material. Temporal agreement is not independent measurement validation. SOURCE_CLASSIFICATION_DIFFERENCES.csv separates actual area-composition changes from entropy summaries.

ACS5+ is preferred for a direct concentration-of-units-in-multi-unit-structures construct; detached share is a coherent substitute for detached orientation. Their Pearson correlation is {pairs.loc[pairs.family.eq('housing_contrast_not_same_quantity'),'pearson'].iloc[0]:.4f}. They are not exact complements.80-replicate median90% MOEs are {acs.set_index('feature').loc['housing_5plus_share','moe90_median']:.4f} and {acs.set_index('feature').loc['housing_detached_share','moe90_median']:.4f}; large uncertainty and boundary cases remain in the sample.

Assessor2022 versus LARIAC2014 age correlation is {pairs.loc[pairs.family.eq('age_different_denominator'),'pearson'].iloc[0]:.4f}, with mean difference {pairs.loc[pairs.family.eq('age_different_denominator'),'mean_difference'].iloc[0]:.4f}. Parcel-linked tax-roll enrichment means these are not safely independent observations. Official LARIAC schema includes AIN, YearBuilt1, Roll_Year and assessment-value fields; exact historic join/year cardinality is not documented by the inspected metadata. Do not claim an independent age-validation study. Main Square Footage is not certified floor area. The multiple-line/condominium/restricted-stock analysis and government zero-year/zero-area patterns weaken a complete all-use age claim despite high internal valid-year coverage.

## EPA allocation evidence

{table(epa[['scenario','n','mean_absolute_change','p90_absolute_change','maximum_absolute_change','n_absolute_change_gt_005','count_conservation_error_max']])}

Alternatives use donor-land weights raised to0.5 or2, with household and job concentration changed jointly or separately. These are declared allocation stress tests, not observed alternatives, accuracy estimates, or confidence intervals. Counts are conserved including outside-study residual geography. Variation therefore demonstrates the limits of conservation as spatial validation. Historical2017 jobs/2014–2018 households on2018 donors are not synchronized2022 physical-form measurements.

## Bounded comparison

{table(compare[['model','cohort_n','full_seed_pair_ARI_median','spatial_ARI_median','spatial_ARI_p05','spatial_ARI_min','reassigned_n_max','D34_purity_min']])}

All use fixed k4,n_init100,seeds42–61 and the existing20 spatial-deletion cases (17 distinct geographic sets). StandardScaler is refit only on retained training tracts. ARI is partition agreement, not accuracy; ranges are descriptive and do not treat repeated deletion sets as independent replications. HIST's20 full and20 spatial fits were reused exactly.440 new model/spatial fits and20 declared coverage fits were completed; no k search. One assessor-age-null tract,06037115103, is excluded from CORE4 and its CORE3_AGE_COMMON comparator only. Other models retain2,287. All2,291 master rows remain, including the original four geometry-unclassified tracts.

Most physical substitutions preserve the34-member full-data class, but spatial support can lead to absorption rather than disappearance. In COVER_ALT the D34 group can merge into a much larger group; that result is a fixed-k/source-sensitivity warning, not evidence that vector geometry is intrinsically inferior. Full raw contingency tables expose splitting/merging hidden by a matched class name. No-training-support cases are explicitly flagged. Original-unit profile changes distinguish fixed members after deletion from replacement members after reclustering. Minor profile rankings can reverse and must not be promoted to universal archetypes.

CORE3 coverage-only restriction trains on {int(cov.training_n.iloc[0])} tracts and predicts the full2,287, yielding median ARI {cov.full_ARI.median():.4f} and maximum {int(cov.changed_n.max())} changed tracts. This excludes the bottom coverage quartile as a diagnostic, not as a new admission threshold. Fixed-centroid ACS replicate predictions change a median {vr.changed_n.median():.1f} and maximum {int(vr.changed_n.max())} assignments. They do not refit clusters or propagate all special boundary-model uncertainty; they are not cluster confidence intervals. SCAG_CLASSIFIED_LAND_SUPPORT_BOUNDS.csv gives feasible missing-land entropy bounds, not imputed observations.

Measurement recommendation, domain weights and final partition approval remain different decisions. The preferred set adds interpretable concepts but does not resolve the demonstrated fixed-k4 spatial limitations. Formal Stage7, manuscript, figures, physical model, schedules, trajectories and GA remain unchanged.
''')
    put('DOMAIN_WEIGHT_REQUIREMENTS.md','''
# Domain-weight decision required after measurement selection

Preferred physical variables: EMC2022 occupancy, ACS5+ residential configuration, SCAG2020 classified-parcel composition. These are three constructs and have different populations/support. They must not be called interchangeable density indicators. Age is not a preferred primary construct with the current sources.

Retained coordinates: B_480_hr and Init_Supply; unchanged grid degree/impact/betweenness/HHI; SOVI; log building stock; unadjusted multi-hazard ALR. Stock measures amount of monetary assets, ALR measures loss propensity after exposure normalization and component aggregation. Neither is pure hazard or interchangeable with physical coverage.

The unresolved decisions are:
1. Whether the three physical constructs intentionally share one parent-domain budget or receive distinct construct budgets.
2. Whether monetary stock and expected-loss propensity intentionally share a parent budget or have separate exposure/loss budgets.
3. The declared total budgets for recovery/initial service, grid dependence and mandatory social vulnerability relative to those domains.
4. If a separately justified hardening/height extension is considered later, whether its budget is taken from physical form or is additional at the expense of explicitly named domains. It must not gain weight merely by adding columns.

This round used only an equal-five-parent benchmark:0.2 each for recovery/service,grid,physical,social,stock/loss. Within each, standardized coordinates share squared-distance weight. CORE2 receives0.1 per physical coordinate, CORE3 receives0.0666666667, CORE4/age/optional four-coordinate variants0.05. B and Init receive0.1 each, grid0.05 each, SOVI0.2, stock and ALR0.1 each. Standardized values are multiplied by the square root of these weights. DOMAIN_COORDINATE_CONTRIBUTIONS.csv reports actual coefficients and observed separation contributions separately.

The added-variable comparisons therefore combine a new measurement with a declared redistribution of the unchanged physical budget. They are not zero-cost incremental additions and not pure feature effects at fixed individual-coordinate weights. No second weight scheme, interpolation, optimization, PCA or k sweep was executed. Five historical domains each20% are not selected as the final scientific hierarchy.

The next study must preregister hierarchy/budgets from the intended representation, keep this measurement set and common GEOIDs fixed, and distinguish content from weighting. Do not tune budgets for silhouette, old-label agreement, preserving the34-member class or making four groups look clean. This package gives a measurement selection now; it does not leave the candidate pool open indefinitely.
''')
    put('SOURCE_LINEAGE_AND_DEPENDENCIES.md','''
# Source lineage and deterministic dependence

Coverage:2022 Sentinel-2 modeled built surface →100m EMC built m² → fractional cell/tract-land aggregation → total built-land fraction. Historical/mixed-image stereo rooflines → clipped geometric union → LARIAC footprint fraction. They measure one occupancy family through different sources; neither can be treated as independent causal confirmation of the other.

Land use: source ALU19/ALU20 codes → explicit11-class mapping → geometric unions/conflict removal/tract-land intersections → exclusive area proportions → entropy / log11. Entropy is derived from these proportions. Jointly adding all proportions and their entropy would weight the same source information repeatedly.2020 includes explicit LU19 carry-forward; temporal alternatives are not independent observations. EPA households/jobs → historical donor-land allocation → target counts → entropy normalized by positive category count is a different activity construct. Its count conservation does not validate target locations.

Housing: ACS B25024 category counts / housing units → shares. All categories share a denominator and sum to one; detached and5+ are not exact complements because attached,2–4 and mobile/other units remain. The80 variance replicates preserve joint survey covariance. Point estimates alone do not describe uncertainty.

Age: LARIAC2014 roof geometry + parcel/AIN-linked YearBuilt1/tax-roll attributes → valid-age footprint share;2022 assessment AIN/point + scalar actual year and Main Square Footage → recorded-main-area share; ACS B25034 housing-unit counts → residential age share. Source family/denominator/time are different. The official enriched LARIAC layer contains tax-roll fields alongside YearBuilt1; this supports a shared assessment lineage inference. Exact old roll year/join cardinality was not recovered, so no independent-source validation is claimed. Different condominium AINs and shared parcel/point geometry do not establish one physical building; no deduplication is inferred. Scalar year on multiple building-data lines is a further attribution limitation.

On an identical nonoverlapping outline set and land/count convention, summed footprint fraction = count per km² × mean footprint m² /1,000,000. The existing clipped-union fraction and centroid-assigned count/area use different sets and overlap handling, so that exact identity cannot be imposed across those fields. Volume/land = valid-set footprint fraction × footprint-area-weighted height only with identical supports. Mean/median/CV/IQR describe different summaries, not new sources. FAR requires actual floor area/floors and compatible support; it is not fabricated here.

Risk: BUILDVALUE is monetary stock. EAL_SCORE and EAL_VALT are percentile/value views of one expected-loss construct. ALR_NPCTL is the official unadjusted composite loss-rate percentile, not EAL_TOTAL/BUILDVALUE. RISK_SCORE and adjusted ALR reintroduce community factors beside SOVI. Shared source variables, algebraic dependence, statistical association and construct equivalence are explicitly different. Partial correlations/VIF/spline R² are diagnostics, not admission thresholds or causal proof.
''')
    # Actual class-composition changes on the same common cohort.
    f=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_RESIDENTIAL_2291.csv');ids=mat.loc[mat.common2286,'tract_id'];d=f.loc[ids];classes=['residential','commercial_office','industrial','institutional_public','transportation_utility','open_space_recreation','vacant_undeveloped','agriculture','mixed_use','under_construction','protected_undevelopable'];rows=[]
    for c in classes:
        delta=d['scag2020_'+c+'_classified_share']-d[c+'_classified_share'];rows.append(dict(broad_class=c,n=len(d),old_mean=d[c+'_classified_share'].mean(),new_mean=d['scag2020_'+c+'_classified_share'].mean(),mean_difference=delta.mean(),median_difference=delta.median(),mean_absolute_difference=delta.abs().mean(),p90_absolute_difference=delta.abs().quantile(.9),maximum_absolute_difference=delta.abs().max()))
    save('SOURCE_CLASSIFICATION_DIFFERENCES.csv',rows)
    put('README.md','''
# Stage7 shortlist resolution

Read FINAL_VARIABLE_RECOMMENDATION.md first: it selects CORE3 and explains all inclusion/exclusion decisions. FINAL_CANDIDATE_CONSTRUCT_DECISION.md contains the evidence and fixed-k4 limitations. DOMAIN_WEIGHT_REQUIREMENTS.md states the remaining domain-budget decision.

Measurement tables use actual validated values and exact GEOIDs. SHORTLIST_FEATURE_MATRIX.csv retains all2,291 residential records; primary comparisons use2,287 and the conditional age pair2,286. FINAL_SHORTLIST_DISPOSITIONS.csv accounts for all64 registered candidates. Source alternatives, composition dependence, coverage bounds and source-allocation stress tests are kept distinct.

BOUNDED_MODEL_COMPARISON.csv summarizes12 eligible/conditional comparison specifications; BOUNDED_RUN_RECORDS.csv and run_records contain full seed/scaler/center/prediction records. Contingencies, profiles, class retention/purity, source coverage and ACS measurement sensitivity are separate auditable tables. The20 deletion cases comprise17 unique geographic sets and are not independent validation. k stays4. No weight search or final clustering promotion occurred.

Reproduce in the verified Anaconda Python3.12.3/scikit-learn1.5.1 environment. Run common.py once for preservation; measurement_resolution.py reuses source payloads and cached attributes; additional_measurement.py supplies conditional/bounds evidence; controlled_shortlist.py reuses verified complete checkpoints; summarize_comparisons.py reuses completed coverage runs; write_decision.py generates the memos. source_lineage.py makes only a few official metadata requests. test_shortlist.py checks consequential numerical/identity invariants. Paths, byte hashes and versions are retained. No bulk GIS extraction or download was repeated.

Formal Stage7 labels/PCA, manuscript, figures, simulations, schedules and GA are untouched. The package is an isolated research recommendation, not authorization to replace them.
''')
    log('Scientific shortlist recommendation and domain-weight requirements written from actual numerical evidence.')

if __name__=='__main__':main()
