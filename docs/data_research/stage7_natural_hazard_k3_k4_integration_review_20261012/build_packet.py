"""Qualified Methods, scientific K decision and non-promoted integration candidate."""
from common import *


def main():
    d=frame('inputs/FROZEN_COHORT.csv','tract_id')
    v=frame('inputs/NCV_VECTOR.csv','tract_id').reindex(d.index);d['FEMA_NCV14_CA_v119']=v.FEMA_NCV14_CA_v119
    gates=json.loads(lp(OUT/'ANALYSIS_COMPLETION_AND_PHASE_GATES.json').read_text())
    assert gates['stage3_allowed_as_author_review_only'] and gates['no_new_fits']
    fits=np.load(lp(OUT/'inputs/SAVED_LABELS_AND_SILHOUETTES.npz'));ix={k:i for i,k in enumerate(fits['keys'])}
    matrices=np.load(lp(OUT/'inputs/SAVED_WEIGHTED_MATRICES.npz'));x=matrices['main']
    def labels(k):return fits['labels'][ix[f'NCV14__main__k{k}__s42']]
    reg=dict(review_status=WARN,authority=AUTH,source_fit='NCV14__main__k3__s42',primary_K=3,sensitivity_K=4,K5_reused_not_refitted=True,choice_is_author_review_recommendation=True,source_vector='FEMA_NCV14_CA_v119',hazard_gate='Qualified native release-defined screening construct; not independent physical-hazard verification',cohort_rule='Frozen_Formal_Population >0',n_tracts=2299,population=9066522,excluded_zero_population=16,retained_positive_zero_housing=8,full_service_domain=2315,first7_frozen=True,hazard='2pc50',resources='C57_D1',mapping='M1_UTILITY_003',gate='G1_BASELINE_050',horizon_hr=480,realizations=1000,policies=['Impact-first','Hospital-first','Degree-first','Betweenness-first','Vulnerability-first'],coordinates=FEATURES,squared_distance_budgets=BUDGET,domain_budgets={'RQ1':1/3,'RQ2':1/3,'RQ3':1/3},standardization='Cohort mean and population SD; sqrt budget multipliers',observations_equally_weighted=True,initialization='k-means++',n_init=50,max_iter=500,tol=1e-4,algorithm='lloyd',seed=42,registered_seeds=[42,43,44,45,46],new_Kmeans_fits=0,formal_promotion=False,manuscript_overwritten=False,review_completed_client_date='2026-10-13')
    dump('candidate/FROZEN_CANDIDATE_SPECIFICATION.json',reg)
    transformed=d[FEATURES].to_numpy(float);means=transformed.mean(0);sd=transformed.std(0)
    np.testing.assert_allclose((transformed-means)/sd*np.sqrt(BUDGET),x,rtol=0,atol=1e-14)
    save('candidate/COHORT_STANDARDIZER_AND_WEIGHTS.csv',[dict(variable=f,domain='RQ1' if j<3 else 'RQ2' if j<5 else 'RQ3',cohort_mean=means[j],population_SD=sd[j],squared_distance_budget=BUDGET[j],Euclidean_multiplier=np.sqrt(BUDGET[j]),transformation='log1p frozen population' if f=='log1p_Population' else 'none;provider min-max adaptation already in hazard coordinate' if j==7 else 'none') for j,f in enumerate(FEATURES)])
    save('candidate/EIGHT_VARIABLE_FROZEN_TABLE.csv',d[FEATURES+['Population','frozen_SOVI_quartile','hospital_tract','additional_zero_housing_positive_population']].reset_index())
    ids=d.index.to_numpy(dtype='U11')
    np.savez_compressed(dest('candidate/FROZEN_PREPROCESSING_AND_LABELS.npz'),tract_ids=ids,feature_names=np.array(FEATURES),raw=transformed,cohort_mean=means,population_SD=sd,budgets=BUDGET,weighted_matrix=x,K3_labels=labels(3),K4_labels=labels(4))
    registry=[]
    for k,role in [(3,'PRIMARY_REVIEW_CANDIDATE'),(4,'SENSITIVITY_REVIEW_CANDIDATE')]:
        lab=labels(k);membership=d[['Population','frozen_SOVI_quartile','hospital_tract']].copy();membership['saved_model_class']=lab;membership['candidate_display_cluster']=lab+1;membership['candidate_role']=role
        save(f'candidate/K{k}_CLUSTER_MEMBERSHIP.csv',membership.reset_index())
        for c in range(k):registry.append(dict(k=k,saved_model_class=c,candidate_display_cluster=c+1,label=f'C{c+1}',role=role,ID_meaning='Within-model ascending five-policy total-deficit centroid;not old formal cluster ID'))
    save('candidate/CLASS_ID_REGISTRY.csv',registry)
    # Explicit proposal only: a bivariate co-occurrence flag, not a new weighted hotspot score.
    cutoff=d.MeanTotalBurden.quantile(.75);high=d.MeanTotalBurden.ge(cutoff);q4=d.frozen_SOVI_quartile.eq('Q4')
    context=d[['Population','frozen_SOVI_quartile','SOVI_SCORE','MeanTotalBurden','B_Unconstrained','MeanDelta','FEMA_NCV14_CA_v119','hospital_tract']].copy()
    context['Q4_flag']=q4;context['high_five_policy_burden_flag']=high;context['proposed_Q4_high_burden_cooccurrence']=q4&high;context['candidate_display_category']=q4.astype(int)+2*high.astype(int);context['candidate_display_cluster']=labels(3)+1
    save('candidate/PROPOSED_DESCRIPTIVE_COOCCURRENCE_TABLE.csv',context.reset_index())
    save('candidate/PROPOSED_COOCCURRENCE_TRACTS.csv',context.loc[q4&high].reset_index())
    dump('candidate/PROPOSED_COOCCURRENCE_DEFINITION.json',dict(review_status=WARN,author_approval_required=True,not_existing_formal_hotspot=True,not_clustering_input=True,no_weighted_score=True,no_top10_or_intervention_ranking=True,vulnerability='Original frozen Q4 only; quartiles never recomputed',recovery='At or aboveP75 of five-policy mean total service deficit within2299 positive-population cohort',cutoff_equivalent_deficit_hours=cutoff,n_high_burden=int(high.sum()),n_Q4=int(q4.sum()),n_joint=int((q4&high).sum()),population_joint=int(d.loc[q4&high,'Population'].sum()),map_categories={0:'Neither',1:'Frozen Q4 only',2:'High service deficit only',3:'Joint Q4/high deficit'},natural_hazard='Displayed in profiles and table;no hazard threshold is added to co-occurrence rule'))
    # Tables for the entire domain retain excluded zero-population records as unassigned.
    excluded=frame('inputs/EXCLUDED_ZERO_POPULATION_GEOIDS.csv')
    full=pd.DataFrame({'tract_id':list(d.index)+list(excluded.tract_id)}).set_index('tract_id')
    assert excluded.Population.eq(0).all()
    full['Frozen_Formal_Population']=d.Population.reindex(full.index)
    full.loc[excluded.tract_id,'Frozen_Formal_Population']=excluded.set_index('tract_id').Population
    assert full.Frozen_Formal_Population.notna().all()
    full['Frozen_Formal_Population']=full.Frozen_Formal_Population.astype(int)
    assert set(full.index)-set(d.index)==set(excluded.tract_id)
    full['clustering_eligible']=full.index.isin(d.index);full['K3_candidate_cluster']=pd.Series(labels(3)+1,index=d.index).reindex(full.index);full['K4_candidate_cluster']=pd.Series(labels(4)+1,index=d.index).reindex(full.index)
    full['exclusion_reason']=np.where(full.clustering_eligible,'','Frozen formal population is0;no clustering assignment')
    save('candidate/FULL_2315_COHORT_STATUS.csv',full.reset_index())
    distributions=frame('K3_K4_ORIGINAL_UNIT_PROFILES.csv');group=frame('K3_K4_QUARTILE_POPULATION_HOSPITAL.csv')
    old=frame('inputs/FORMAL_OLD_STAGE7.csv','tract_id');legacy=[]
    for name in ['T80','Pre_1970_Ratio','NRI_RISK_SCORE','SlowVulnerable_Hotspot_Score','cluster','PC1']:
        legacy.append(dict(old_item=name,candidate_action='Retire from fitted input;do not transfer old cluster/PCA IDs' if name in ['cluster','PC1'] else 'Not a fitted coordinate;no silent migration of old weighted hotspot score',formal_file_unchanged=True))
    save('candidate/LEGACY_MIGRATION_CHECKLIST.csv',legacy)
    save('candidate/CLASS_PROFILES_AND_QUARTILE_HOSPITAL_COUNTS.csv',group.loc[group.condition.eq('main')])
    save('candidate/ORIGINAL_UNIT_PROFILE_DISTRIBUTIONS.csv',distributions.loc[distributions.condition.eq('main')])
    eq=frame('EARTHQUAKE_COMPONENT_DISTRIBUTIONS.csv').set_index('variable')
    pair=frame('EARTHQUAKE_NRI_CGS_SPATIAL_RANK_COMPARISON.csv')
    weather=frame('WEATHER_PAIRWISE_DEPENDENCE.csv')
    influence=frame('HAZARD_SET_AND_NORMALIZATION_EFFECTIVE_INFLUENCE.csv')
    k_ev=frame('inputs/EXISTING_K_EVIDENCE.csv').set_index('k')
    station=frame('Q34_FROZEN_STATION_CONTRIBUTION_TRACE.csv')
    qshare=station.loc[station.substation_id.astype(str).eq('308581'),'share_of_Q34_initial_contribution'].iloc[0]
    leverage=frame('K3_K4_DISTANCE_AND_DOMAIN_LEVERAGE.csv')
    initshare=leverage.loc[leverage.k.eq(4)&leverage.model_class.eq(0)&leverage.variable.eq('Init_Supply'),'centroid_squared_share'].iloc[0]
    md('01_NATURAL_HAZARD_FINAL_DEFINITION_AND_EVIDENCE.md',f"""# Qualified eighth-variable decision

Retain the exact previously calculated FEMA_NCV14_CA_v119 as a **selected14-hazard frequency-area geographic screening index**. It is not a comprehensive all-hazards risk index, an observed tract disaster-frequency measurement, an electrical-outage model or an official FEMA composite field. This gate passes for a transparently qualified release-based screening construct, not for independently validated physical intensity or14 statistically independent observations.

## Exact definition suitable for Methods

For tract r and retained hazard h, define x_rh = AFREQ_rh * EXP_AREA_rh / AREA_r, using compatible square-mile areas and the released nonnegative frequency factor. Independently normalize x_rh with its valid frozen California minimum a_h and maximum b_h: u_rh=(x_rh-a_h)/(b_h-a_h). Sum the14 u_rh equally, then min-max the sum against California records with all14 actual factors. Frozen a_h,b_h and cohort values are supplied in inputs and candidate tables; no target source unknown is set to zero. The final0-1 index is a relative geographic screen, not a literal probability. Constant local CWAV is retained in the main source-defined set; its local separation contribution is0.

The selected hazards are CFLD,CWAV,DRGT,ERQK,HAIL,HWAV,LNDS,LTNG,RFLD,SWND,TRND,TSUN,WFIR,WNTW. AVLN,HRCN,ISTM,VLCN have entirely null target factors and are omitted explicitly, not declared physically impossible. Selection followed complete compatible source factors on all2299 targets before clustering, not fitted memberships or optimal silhouette. The first seven coordinates and H2 squared-distance budgets are unchanged.

Released AFREQ is itself often spatially area-weighted. The additional exposure fraction is therefore a published-method screening transformation, not a separately identified or independent occurrence-times-exposure probability. It may apply another footprint-dependent attenuation. Do not claim it reconstructs a physical impacted area or a calibrated loss probability. ERQK exposure-area construction was not independently rebuilt; the released geographical field is used as-is rather than certified as pure susceptibility.

## Why earthquake differentiates weakly

The original ERQK factor uses a USGS100-year minor-damage shaking probability surrogate and release-defined area, not PGA at2% exceedance in50 years. Original raster/model and released field annualization conventions were not reconstructed; multiplying by100 must not be used here to fabricate a validated100-year probability. Source probabilities can have limited regional contrast, but source saturation is an interpretation consistent with the released range, not a new raster-level proof.

Released AFREQ has CV{eq.loc['ERQK_AFREQ','CV']:.4f}, whereas the frequency-area product has CV{eq.loc['ERQK_frequency_area_factor','CV']:.4f}. Coastal tracts with unusually large AFREQ often have small exposed fractions; multiplying the two attenuates those extreme values. The product's P10-P90 is{eq.loc['ERQK_frequency_area_factor','p10']:.8f}-{eq.loc['ERQK_frequency_area_factor','p90']:.8f}. Its California-scaled mean is{eq.loc['ERQK_CA_normalized','mean']:.4f}, SD{eq.loc['ERQK_CA_normalized','sd']:.4f}. Earthquake gives a high normalized background but little local variance, not absence of earthquake hazard.

Independent CGS MS48(2025) land-area PGA has2294 valid comparisons and5 partial-support records left missing. Its estimand is2%-in50-year shaking intensity, with2023 NSHM/site-response inputs. ERQK raw/product spatial ordering is not concordant with this PGA ordering (Spearman approximately-0.052/-0.038). Different severity thresholds, vintages and support prevent interpreting this as a validation failure or as interchangeability. The PGA centroid diagnostic supports all2299 but does not replace the five missing land-area measurements or become a fitted coordinate. All2299 still enter the typology.

## Weather-source gate

Hail and strong wind share NOAA/NWS SPC event reporting,1986-2019 source sections,80-km point buffers and49-km fishnet aggregation with national event-count scaling. Thus small tract-level numerical differences do not imply independently monitored local hazards. Hail also has report-size threshold changes and reporting/urban-location bias. Heat uses a different NWS-warning/IEM pipeline, warning-day and forecast-zone geometry,2005-2022 reference window and a5% block-intersection rule; it is not an independently measured temperature grid.

No explicit minimum-frequency substitution was located in these three acquired hazard sections. All three target factors are non-null/nonzero; this does NOT prove every tract directly experienced a recorded event. Shared buffering, forecast zones and national scaling remain provider model choices, not observed spatial detail. Hail/wind frequency-area Pearson is0.9233 but Spearman0.1949: common upper-tail/geographic patterns and ties must not be described as identical hazard ordering. Heat/hail Pearson0.6978; heat/wind0.4488. Direct asset/social variables are not used by our operator, but reporting and source geography are not demographically neutral by proof.

March2023 text has inconsistent StrongWind period descriptions: section18.1.1 says34 years while18.6 prints70; Heat published tract count/frequency ratios also do not consistently reproduce the printed16.9-year period. Area-weighted counts, source/version details and text inconsistencies remain unresolved. A uniform positive frequency scale cancels exactly in component min-max, as verified algebraically, so a constant unit/period conversion alone cannot explain the spatial ordering. Spatially inconsistent source processing would matter and is not ruled out.

## Effective influence and normalization

{table(influence[['hazard','local_range_fraction_of_CA_range','local_normalized_sd','signed_covariance_share']])}

Heat/hail/strongwind account for about89.5% of local summed-score variance by signed covariance attribution. This combines source heterogeneity, regional hazard variation and California reference ranges; it is NOT89.5% of physical risk or a prescribed hazard probability weight. Hail/wind share source processes, so14 nominal hazards are not14 independent dimensions. Per-hazard California ranges create implicit relative scaling despite equal summation coefficients. The final affine score normalization cancels under cohort z-scoring, whereas changing individual reference ranges does not.

Existing hazard leaveout and LA-normalization fits are reused unchanged. For K4, heat deletionARI=.9777, hail=.9904, wind=.9879, earthquake=.9959, and LA component normalization=.9830. K3 remains similarly stable to these hazard choices; K5 is much less stable to heat deletion/normalization. This supports keeping the registered vector for the K3/K4 comparison; it does not establish physical validity or justify weight tuning. The eight-variable typology remains earthquake-conditioned recovery with a selected multi-hazard context, not multi-hazard electrical-system simulation.

## Three separate authorities

1. FEMA March2023 v1.19: actual released hazard-specific fields and source processing. Not our composite, not newer NRI substituted.
2. Williams, Summers and Harwell(2024), DOI10.3390/su162310778: frequency-area operator, per-hazard min-max and normalized summation in a county implementation. The acquired paper does not unambiguously enumerate the aggregate-nine set or supply exact national extrema/public numeric workbook. No exact full county-nine replication is claimed.
3. Our extension: native2020 tract application, declared14 compatible hazards, frozen California reference,2299 positive-population cohort and H2 clustering budget. These are study-specific choices requiring author approval, not official FEMA/provider endorsement.

Sources: [FEMA v1.19 documentation](https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf), [Williams2024](https://doi.org/10.3390/su162310778), [CGS MS48](https://www.conservation.ca.gov/cgs/publications/ms48). Exact archived evidence, input hashes and page references are retained. No provider is contacted.
""")
    trans=frame('K3_TO_K4_EXACT_MEMBERSHIP.csv')
    summary=group.loc[group.condition.eq('main')]
    md('02_K3_K4_FINAL_SCIENTIFIC_AUTHOR_DECISION.md',f"""# Recommend K3 primary; K4 sensitivity

This is a scientific-purpose decision within the qualified eight-variable NCV14/H2 reference, not a statistical claim that K3 is the universal optimum. No new fits were performed. K4 has better silhouette(.24443 versus.23374) and fewer negative silhouettes, and marginally stronger minimum geographic agreement(.59183 versus.57233). K3 does not win every numerical criterion. Elbow endpoints support3 or4 rather than a sharp unique bend.

## What K4 adds

K3 andK4 have label-invariantARI{gates['K3_K4_ARI']:.6f}. The main new information is isolation of38 of the475-tract K3 parent group; all38 come from that parent. The other primary patterns mostly remain:1234 of the1242 high-SOVI parent remain together;578 of582 higher-baseline-burden tracts remain together. This is a localized refinement, not four newly discovered recovery mechanisms.

{table(trans)}

The38 group represents136453 residents(1.505% of cohort population), contains34 prior Q-linked tracts, and has no positive-population zero-housing tract. Therefore it is not an artificial institutional-tract class. Prior frozen station evidence attributes{qshare:.2%} of the34 group's initial modeled availability to STATION Q(308581), a retained Core supply proxy. The new frozen-mapping trace of all38 independently verifies{gates['Q38_positive_Q_dependency']} positive Q dependencies and aQ contribution share of{gates['Q38_initial_service_Q_share']:.2%}. The additional four have zero Q weight and are chiefly served in the initial model by HAYNES(307373) and ALAMITOS(307039), other retained Core proxies. They must not be relabeled Q-dependent. This is linear post-processing of existing station initial means, not a new connectivity simulation. Source designation, its sampled operability, source gate and mapping are model premises, not independent validation of delivered electricity. Mean initial service of the38 is1.7306%, still near-total loss. Init accounts for{initshare:.2%} of its centroid's squared displacement. Other raw-unit differences (lower unconstrained burden and grid impact; larger additional constraint burden) are real frozen-model patterns, but do not establish a distinct real-world restoration mechanism.

## Init sensitivity and substantive profiles

Registered removal also raises grid impact/HHI budgets from1/9 to1/6. K3 ARI=.65536 versusK4 .29425. In K3,1236 of1242 high-SOVI tracts remain together after removal; other recovery groups mix materially. Thus it is inaccurate to say the entire original typology persists without Init. The38-tract K4 group disperses into three minus-Init groups(12/12/14); it is not independently recovered from the remaining coordinates. Presence and budget redistribution cannot be causally separated by these fits alone; algebraic distances and prior sensitivity disclose both.

K3 gives three regional joint patterns: C1 combines low spectral importance, moderate baseline deficit, low extra constraint burden, and relatively high SOVI; C2 combines lower baseline deficit with the highest average additional constraint burden; C3 combines higher spectral importance and the largest baseline deficit, with intermediate additional burden. HHI differences are modest, and all initial states are very low in absolute units. These descriptions do not imply actual electrical resilience, delivery adequacy or clinical recovery.

{table(summary[['k','proposed_display_ID','n_tracts','population','population_share','Q1_n','Q2_n','Q3_n','Q4_n','hospital_tracts','positive_zero_housing']])}

K3 C1 contains407 of579 frozen Q4 tracts and64 of103 hospital-linked tracts, while representing56.27% of residents. Quartile composition shares the input SOVI and is not independent validation. Hospital presence is a contextual tract indicator, not patient dependence or restored hospital load; Hospital-first also contributes to the five-policy RQ2 inputs, so it is not wholly procedurally independent. T80 is retained as a descriptor of the frozen Impact-first reference, not a milestone of a hypothetical averaged-policy trajectory.

K3 seed partitions coincide in saved fits; K4 minimum seedARI=.9732. Minimum policy-LOO cohort-scaledARI is.6129(K3) versus.5942(K4). Geographic mean agreement favorsK4; both remain sample/policy dependent. Existing K5 results are archived only, not searched again.

## Reason for primary resolution

Use K3 in the main integration candidate because it preserves the three broad disruption/recovery/vulnerability patterns without elevating a strongly source-premise-dependent exception to the same interpretive level as regional community types. Show K4 explicitly in S9 and the robustness figure to disclose the rare initial state and statistical preference for4. This choice is based on source-grounded scientific interpretability and the intended community-level claim, not the number of RQs or resemblance to old figures. Author approval remains required; the official Stage7 and IDs stay untouched.
""")
    primary=group.loc[group.condition.eq('main')&group.k.eq(3)]
    def value(c,field,stat='mean'):
        return frame('K3_K4_ORIGINAL_UNIT_PROFILES.csv').loc[lambda z:z.condition.eq('main')&z.k.eq(3)&z.model_class.eq(c)&z.variable.eq(field),stat].iloc[0]
    result=[]
    for c in range(3):
        row=primary.loc[primary.model_class.eq(c)].iloc[0]
        result.append(dict(cluster='C'+str(c+1),n_tracts=row.n_tracts,population=row.population,population_share=row.population_share,mean_Unconstrained_deficit_hr=value(c,'B_Unconstrained'),mean_constraint_increment_hr=value(c,'MeanDelta'),mean_SOVI=value(c,'SOVI_SCORE'),median_population=value(c,'Population','median'),mean_hazard_screen=value(c,'FEMA_NCV14_CA_v119'),mean_initial_service_pct=100*value(c,'Init_Supply')))
    save('candidate/RESULTS_TEXT_SUPPORT_TABLE.csv',result)
    md('candidate/METHODS_REPLACEMENT_DRAFT.md',"""# Proposed Stage7 Methods replacement

Community typology was characterized using eight tract-level coordinates organized into three research-question domains. RQ1 included initial modeled service availability, dependency-weighted spectral network impact, and dependency concentration(HHI). RQ2 included equivalent full-service-deficit hours over0-480h under Unconstrained recovery and the equally weighted mean additional deficit across five predefined scheduled priorities: Impact-first, Hospital-first, Degree-first, Betweenness-first and Vulnerability-first. The policy weights are descriptive experimental weights, not adoption probabilities, and no average physical repair schedule was simulated. RQ3 included frozen FEMA v1.19 SOVI_SCORE, log1p of frozen formal tract population, and a selected fourteen-hazard geographic screening coordinate.

The hazard coordinate adapts the frequency-area operator of Williams et al.(2024): x_rh=AFREQ_rh(EXP_AREA_rh/AREA_r), using frozen FEMA NRI March2023 v1.19 fields. Each compatible hazard factor was independently min-max normalized using its valid California records, equally summed and the sum min-max normalized among complete fourteen-component California records. Earthquake, coastal and riverine flooding, cold wave, drought, hail, heat wave, landslide, lightning, strong wind, tornado, tsunami, wildfire and winter weather were retained. Avalanche, hurricane, ice storm and volcanic activity had source-null target factors and were omitted without treating unknown as zero. This is a researcher-derived tract-scale extension, not an official FEMA composite or exact replication of the original county-nine implementation. It contains mixed released frequency/probability proxies and geographic conventions and is interpreted as a relative screening context, not multi-hazard occurrence probability, monetary risk or multi-hazard simulation of electricity restoration. Direct SOVI, building-value, resilience, EAL and historical-loss-ratio fields do not enter the hazard operator. Its local variation is strongly influenced by heat/hail/wind source models; source-scale and normalization limitations are documented in supplementary notes.

Many released frequency fields already include area-weighted spatial aggregation. The additional footprint fraction follows the published screening operator and should not be interpreted as an independently measured exposure probability. California reference scaling and the selected hazard set are study-specific conventions, not objectively optimal weights.

The clustering cohort comprised all2299 tracts with positive frozen formal population, including eight tracts without conventional housing units. Only16 zero-population tracts were excluded from clustering; all2315 tracts remained in study-wide service/distributional calculations. No housing or geometry-based exclusion was inherited. Exact GEOIDs, population values, original vulnerability quartiles and1000 frozen physical realizations were unchanged. Features were standardized using the same cohort mean and population SD. Each RQ received one-third squared-distance budget; coordinate budgets were(1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12), applied through square-root multipliers before equal-tract Euclidean K-means.

Saved fits used K-means++,50 initializations,Lloyd,max_iter500,tol1e-4 and seeds42-46. Existing elbow, full-cohort silhouette, initialization, geographic and policy-set sensitivity evidence supported review ofK3 andK4. K3 was retained as the primary candidate for its regional joint profiles; K4, despite higher silhouette, was retained as sensitivity because its added small group chiefly isolates a Q-proxy-driven initial condition. Seed42 labels are the deterministic integration snapshot, not an optimized best-seed selection. No new damage, schedule, source propagation or K search was run for this final selection. Candidate class IDs are newly documented within-model labels, not the previous formal five-class IDs.

The proposed hotspot display is separate from clustering: it identifies co-occurrence of original frozenQ4 membership and a five-policy total deficit at or above the eligible-cohortP75. It does not add a clustering coordinate, a weighted risk score, spatial-significance test, Top10 ranking or repair recommendation. This display rule requires separate author approval; the old pre1970/NRI-risk/T80/SVI sum is not silently carried forward.
""")
    md('candidate/RESULTS_REPLACEMENT_DRAFT.md',f"""# Proposed community-typology Results

The eight-coordinate candidate partitions2299 positive-population tracts into three regional types. C1 contains1242 tracts and56.27% of the represented population. It has low spectral network impact, an average Unconstrained deficit of30.33h, a comparatively small mean additional restoration-constraint deficit of1.61h, and the highest mean SOVI(77.05). C2 contains475 tracts and20.93% of residents; it combines a lower average Unconstrained deficit(27.65h) with the largest mean additional constrained deficit(6.96h). C3 contains582 tracts and22.80% of residents, with higher spectral impact and the largest average Unconstrained deficit(37.58h), plus an intermediate additional deficit(4.15h). The mean hazard-screening values are.6556,.5902 and.6201 forC1-C3, respectively; they do not follow a simple ranking of modeled earthquake recovery. All classes have very low absolute initial service. These are conditional model/type summaries, not actual customer-outage or electrical-capacity predictions.

C1 contains407 of579 frozenQ4 tracts and64 of103 hospital-linked tracts, but its mean additional constraint burden is lower than the other candidate classes. Social vulnerability and modeled recovery burden therefore need not rank identically. This composition is descriptive: quartiles share the SOVI input, and hospital-linked location does not quantify clinical electricity dependence or restored service.

K4 has a higher mean silhouette(.2444 versus.2337) but mainly isolates38 tracts(136453 residents) from the475-tract C2 parent. Thirty-four are Q-associated, and approximately78.7% of the rare group's centroid separation is attributable to Init_Supply. The average initial service is only1.73%. This is a frozen-model source/gate/mapping exception, not independently verified resilience. K3/K4 agreement isARI=.9632;K4 is therefore shown as a sensitivity refinement rather than a separate four-mechanism regional conclusion. Registered Init deletion reassigns the rare group and materially changes other recovery classes; the ablation also redistributesRQ1 weights, as disclosed in S9.

The proposed separate co-occurrence screen uses frozenQ4 and aP75 cutoff of{cutoff:.4f} equivalent deficit hours. It flags{int((q4&high).sum())} tracts representing{int(d.loc[q4&high,'Population'].sum()):,} residents. This is not a validated spatial hotspot or repair priority, and is not the previous four-term composite ranking. Author approval is required before this paragraph or map is adopted.

{table(result)}
""")
    md('candidate/FIGURE7_AND_S9_CAPTIONS_DRAFT.md',"""# Proposed captions

## Figure7. Research-question-driven community recovery typology and descriptive burden co-occurrence

(A) Tract counts and frozen resident population represented by each primaryK3 class. (B) Class means in original units for the eight-coordinate specification; dashed lines mark the full2299-tract mean. Population is shown in persons although log1p population is the fitted coordinate. Deficits are equivalent full-service-deficit hours over0-480h, not schedule makespan or delivered electricity. The natural-hazard value is the California-relative selected14-hazard FEMA-input screening extension, not an official FEMA risk score. (C) K3 candidate memberships, withC1-C3 color identities shared across panels. Sixteen zero-population study tracts are unassigned and gray; the eight positive-population zero-housing tracts are included. (D) Proposed descriptive co-occurrence of original frozenQ4 and upper-quartile five-policy total deficit, with separate colors for each condition and their intersection. This screen is not a spatial significance test, weighted hotspot score, Top10 or repair ranking. The full study-wide service domain remains2315; clustering eligibility is positive frozen population. All panels are author-review candidates and do not replace the official Stage7.

## Supplementary FigureS9. K3/K4 selection and conditional classification robustness

(A/B) Existing weighted-space WCSS and full-cohort mean silhouette for the saved eight-variableH2-NCV14 fits across registeredK, without a new search. Shading highlights3/4, not statistical confidence intervals. The silhouette maximum is4; elbow choice depends on endpoint and does not establish a unique optimum. (C) Saved seed/geographic/policy-set/Init-ablation agreement forK3/K4, using label-invariantARI. Init removal also redistributesRQ1 budgets; four geographic blocks are sensitivity checks, not external validation. (D) Exact K3-to-K4 tract transition counts; IDs are model-specific and the38-tract Q-related initial-state class is identified explicitly. These diagnostics replace the old five-component/PCA and five-class residential-caption proposal only after author approval. No PCA reduction is used for the new fit and no old eigenvalue>1 rule is inherited.

## Additional robustness figure. Membership sensitivity without changing the frozen experiment

Side-by-sideK3/K4 and registered minus-Init candidate maps use the exact same2299 tract cohort and complete domain geometry. Classes are model-specific; palette matching is used only for display, while ARI is label-invariant. Geographic and policy-set sensitivity ranges come from saved fits, not resampled physical realizations. Class profiles and the Q exception are internal frozen-model descriptions, not independent validation.
""")
    md('candidate/SUPPLEMENTARY_NOTES_DRAFT.md',"""# Supplementary notes proposal

The exact14-hazard source set, frozen California extrema, nine-column original-unit profile distributions, standardizer, budgets, saved memberships, quartile/hospital counts and excluded16 GEOIDs are supplied. The formal population and quartiles were not replaced by NRI/CDC population or recomputed. The eight institutional/zero-housing positive-population records remain. Five partial CGS land-mean PGA supports remain missing only in the independent source comparison; they do not restrict typology eligibility.

FEMA frequency-area factors mix event counts,event-days and modeled surrogates. Hail and wind use reporting buffers/fishnets; heat uses warning/forecast-zone support. Shared generation and reporting may couple these measures. Numerical tract uniqueness is not observational resolution. StrongWind record-period text is internally inconsistent, and raw field/block processing was not rebuilt; uniform scale cancellation under min-max was verified but does not resolve spatial processing validity. ERQK is not PGA and its exposure area is release-defined rather than independently reconstructed physical susceptibility. No literal annual earthquake probability is asserted. Earthquake has limited local variance and weak spatial-rank agreement with independent CGS intensity because estimands/vintages differ.

California min-max is study-specific, not national original-method scaling. All equal hazard weights remain fixed; no hazard orRQ weight was selected by silhouette. Existing leave-hazard and LA-normalization results are retained. The proposed eight-variable matrix changes exposure-sub-budget relative to the seven-coordinate baseline; it is not a pure isolated feature addition.

K3 is the proposed main interpretation, not the maximum-silhouette model. K4 better separates the rare initial-condition state but does not prove a universal community mechanism. The Q proxy, gate and station fragility remain model premises. Init deletion removes a construct and increases the remainingRQ1 weights; it does not test a physically different source scenario. Quartile membership shares fitted SOVI; hospital presence and T80 are contextual same-study descriptors, not fully independent validation. Vulnerability-first's procedural use ofQ4 also remains in MeanDelta. No vulnerability targeting or restoration policy was rerun.

Legacy residential2291, five-class, eleven-input and PCA-five-component descriptions should be retired in the proposed replacement text, without deleting their historical files or editing the current manuscript. Candidate figure numbering7/S9 is consistent with the inspected current caption registry; no official figure is overwritten. Proposed co-occurrence display is a new explicitly disclosed two-condition screen requiring author approval, not a silent recomputation of the old housing/risk composite.
""")
    md('03_INTEGRATION_AUTHOR_APPROVAL_AND_PROMOTION_BOUNDARY.md',"""# One author approval packet, no promotion

Recommend approving the qualified NCV14 geographic screening definition, eight-coordinateH2 matrix and K3 as primary, withK4 sensitivity. Inspect Figure7,S9 and the separate robustness/source figures. Approve or reject the proposed Q4/high-total-deficit display separately; it is not the old hotspot score. The candidate contains frozen table,standardizer,budgets,memberships,model-specificIDregistry,all2315 domain status,original-unit profiles,proposedMethods/Results/captions/supplementary notes and exact source/QA records.

Approval items:
- Accept the source-defined14-hazard/California screening construct and its weather-dominated, coarse-source limitations; do not label it validated physical risk.
- SelectK3 main/K4 sensitivity for community interpretation while disclosing higherK4 silhouette and Q-source dependence.
- Keep original frozenSOVI quartiles and vulnerability-first policy; approve the positive-population cohort rule including eight zero-housing tracts.
- Approve the explicitly proposed two-condition co-occurrence panel or request that it be omitted; no new weighted risk/intervention score is authorized by these files.
- Approve proposed narrative/figure/caption replacements before any official script,path or manuscript edits.

No formalmembership,numberedfigure,manuscript,simulation,resource definition or previous audit is overwritten. This directory is the only output target. There is no automated promotion command. A later separately authorized integration must first back up formal targets, check all source hashes and replace coordinated assets/text together; these operations are not performed now.
""")
    md('README.md',"""# Final source,K3/K4 and integration author-review packet

Start with01_NATURAL_HAZARD_FINAL_DEFINITION_AND_EVIDENCE.md and02_K3_K4_FINAL_SCIENTIFIC_AUTHOR_DECISION.md. The recommendation is qualifiedNCV14/H2 withK3 primary andK4 sensitivity.03_INTEGRATION_AUTHOR_APPROVAL_AND_PROMOTION_BOUNDARY.md lists explicit adoption choices. candidate/contains frozen tabular/label/weight assets and proposed manuscript fragments only. figures/contains data-generated PDF/PNG review artwork; no formal asset is overwritten.

Reproduction: Python3.12 with the existing scientific stack. Run prepare.py,analyze.py,build_packet.py,figures.py and independent_qa.py. Analysis reuses saved K3/K4 and ablation labels; no K-means fit,MonteCarlo,scheduling,GA or source propagation is run. GitLFS and the pinned earlier packages are required; source-level checks additionally require the manifest-bound local frozen archive. Exact hashes and package versions are recorded. Native7.2-inch PDFs and600dpi PNGs are inspected, not generated by AI. Old diagnostics and950 scientific files remain preserved.
""")
    print('PrimaryreviewK3,sensitivityK4;candidatefreezecomplete;proposedcooccurrence',int((q4&high).sum()),'tracts;noformalpromotion',flush=True)

if __name__=='__main__':main()
