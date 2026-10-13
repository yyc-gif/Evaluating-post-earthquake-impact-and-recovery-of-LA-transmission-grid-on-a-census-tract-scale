"""Pre-fit construct gates, raw-factor QA and no-data-preserving sensitivity vectors."""
from itertools import combinations
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, GroupKFold, cross_val_predict
from sklearn.metrics import r2_score
from threadpoolctl import threadpool_limits
from audit_sources import HAZARDS, NHI, normalize
from common import *


def main():
    d=frame('FROZEN_COHORT_AND_COMPARATORS.csv','tract_id')
    v=frame('CANDIDATE_TRACT_VALUES.csv','tract_id').reindex(d.index)
    nc=frame('FEMA_NCV_NORMALIZED_COMPONENTS.csv','tract_id').reindex(d.index)
    definition=json.loads(lp(OUT/'FEMA_NCV_ADAPTATION_REGISTRATION.json').read_text())
    hazards=definition['hazards'];assert len(hazards)==14
    assert np.isfinite(v.FEMA_NCV14_CA_v119).all() and nc[hazards].notna().all().all()
    geographic=frame('COLUMBIA_NHI_2010_TO_2020_GEOGRAPHY_QA.csv','tract_id').reindex(d.index)
    coverage=frame('COLUMBIA_SOURCE_COVERAGE_BY_TARGET.csv','tract_id').reindex(d.index)
    missing_geo=geographic.official_land_supported_fraction.lt(1-1e-8)
    admission=[dict(candidate='Columbia_NHI14_dominant_land_source',status='EXPLORATORY_ONLY',
        valid_published_or_transferred_numbers=2299,full_physical_support=False,earthquake_included=True,
        barrier='Null/no-hazard conflation; no target has all14 non-null components; 11 targets have uncovered source land; earthquake ordinal saturation',
        fit_authorized_by_gate=False),
      dict(candidate='FEMA_NCV14_CA_v119',status='PASS_NATIVE_FULL_COHORT',
        valid_published_or_transferred_numbers=2299,full_physical_support=False,earthquake_included=True,
        barrier='Qualified modeled-input coverage only. Four source-null hazards omitted. 14-hazard CA-normalized tract adaptation; not faithful nine-hazard national county replication.',
        fit_authorized_by_gate=True),
      dict(candidate='Williams2024_exact_nine_hazard_NCV',status='FAIL_SOURCE_RECONSTRUCTION',
        valid_published_or_transferred_numbers=0,full_physical_support=False,earthquake_included=True,
        barrier='Paper says nine but lists18 and does not enumerate aggregate nine, missing/constant rules or exact sample/extrema; no author county result table acquired',fit_authorized_by_gate=False),
      dict(candidate='CDC_RPL_CBM',status='FAIL_CONSTRUCT',valid_published_or_transferred_numbers=2299,
        full_physical_support=False,earthquake_included=False,barrier='Climate-only comparator; does not meet new earthquake-inclusive requirement',fit_authorized_by_gate=False)]
    save('EIGHTH_COORDINATE_COHORT_ADMISSION.csv',admission)
    dump('PRE_FIT_ADMISSION_AND_PROTOCOL.json',dict(review_status=WARN,authority=AUTH,
        admitted_new_primary='FEMA_NCV14_CA_v119',published_as_official_FEMA=False,
        exact_Williams_nine_replication=False,admission_definition='Complete actual modeled source inputs for the selected14 hazards on every target. Does not certify complete observed18-hazard coverage.',
        Columbia_fit=False,CBM_reused_only=True,P2_reused_only=True,
        main_K=list(range(1,9)),main_seeds=SEEDS,parameters=PARAMS,squared_distance_budgets=BUDGET,
        registered_auxiliary_K=[3,4,5],auxiliary_seed=42,
        sensitivities=['All14 individual leaveouts','LA-only component normalization with constant CWAV omitted','all non-earthquake combined; no earthquake','earthquake-only descriptor, not an admitted multihazard model','omit Init and redistribute remaining RQ1 to1/6 each'],
        policy_and_geography='Same four prior quadrants and six declared ensemble subsets includingRandom; both cohort and fixed baseline scaling for policy features',
        no_tuned_weights=True,no_new_physical_or_scheduling_run=True))
    # Actual FEMA decomposition shows that removing CRF recovers loss, not a hazard-only score.
    n=pd.read_csv(lp(OUT/'sources/FEMA_NRI_v119_CA_FROZEN.csv'),dtype={'TRACTFIPS':str},float_precision='round_trip').set_index('TRACTFIPS')
    raw=frame('FEMA_NCV_HAZARD_COMPONENT_VALUES.csv','tract_id')
    study=n.loc[d.index]
    rows=[]
    recovered=study.RISK_VALUE/study.CRF_VALUE
    rel=(recovered-study.EAL_VALT).abs()/study.EAL_VALT.replace(0,np.nan)
    rows.append(dict(check='RISK_VALUE/CRF_VALUE equals EAL_VALT; not hazard-only',n=len(study),maximum_relative_error=rel.max(),
        excluded_from_NCV=True,meaning='Recovered EAL still includes exposed stock, population and historical/modelled consequences'))
    save('FEMA_SOCIAL_FACTOR_REMOVAL_NUMERICAL_QA.csv',rows)
    examples=[]
    for h in ['ERQK','WFIR','RFLD','HWAV']:
        eligible=raw.loc[raw[h+'_NCV_raw'].gt(0)].sort_index()
        tract=eligible.index[0];row=eligible.iloc[0]
        af=row[h+'_AFREQ']; exp=row[h+'_EXP_AREA_sqmi'];total=study.loc[tract,'AREA']
        examples.append(dict(tract_id=tract,hazard=h,AFREQ_as_released=af,impacted_sqmi=exp,total_sqmi=total,
            NCV=af*exp/total,saved_NCV=row[h+'_NCV_raw'],arithmetic_absolute_error=abs(af*exp/total-row[h+'_NCV_raw']),
            replication='Documented real v1.19 source calculation, not a reproduced paper county result'))
    save('WILLIAMS_FACTOR_REAL_SOURCE_EXAMPLES.csv',examples)
    # Same-cohort conditional linear and fixed CV information, not causal validation.
    information=[];pairs=[]
    group=(d.utm_x_m.ge(d.utm_x_m.median()).astype(int)*2+d.utm_y_m.ge(d.utm_y_m.median()).astype(int)).to_numpy()
    for candidate in v.columns:
        if candidate=='tract_id':continue
        y=v[candidate]
        if not pd.api.types.is_numeric_dtype(y) or y.isna().any():continue
        X=d[P2].to_numpy(); model=LinearRegression().fit(X,y);linear=model.score(X,y)
        forest=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=12,max_features=1.,random_state=42,n_jobs=1)
        random=cross_val_predict(forest,X,y,cv=KFold(5,shuffle=True,random_state=42))
        spatial=cross_val_predict(forest,X,y,cv=GroupKFold(4),groups=group)
        information.append(dict(candidate=candidate,n=2299,conditional_linear_R2=linear,VIF=1/(1-linear),
            random5fold_nonlinear_R2=r2_score(y,random),four_quadrant_nonlinear_R2=r2_score(y,spatial),
            mean=y.mean(),sd=y.std(ddof=0),p10=y.quantile(.1),median=y.median(),p90=y.quantile(.9),
            min=y.min(),max=y.max(),no_causal_independence_claim=True))
        for col in P2:
            pairs.append(dict(candidate=candidate,comparison=col,Pearson=y.corr(d[col]),Spearman=y.corr(d[col],method='spearman')))
    save('HAZARD_INDEX_INCREMENTAL_INFORMATION.csv',information)
    save('HAZARD_INDEX_PAIRWISE_ASSOCIATIONS.csv',pairs)
    contribution=[];score=nc[hazards].sum(1);variance=score.var(ddof=0)
    for h in hazards:
        x=nc[h]
        contribution.append(dict(hazard=h,sum_of_normalized_values=x.sum(),mean_normalized=x.mean(),normalized_sd=x.std(ddof=0),
            covariance_share=np.mean((x-x.mean())*(score-score.mean()))/variance,
            Pearson_with_sum=x.corr(score),Spearman_with_sum=x.corr(score,method='spearman'),
            unique_native=raw[h+'_NCV_raw'].nunique(),zero_native=int(raw[h+'_NCV_raw'].eq(0).sum()),
            earthquake=h=='ERQK',uncorrected_provider_defaults=True))
    save('FEMA_NCV_EFFECTIVE_HAZARD_CONTRIBUTIONS.csv',contribution)
    shares=np.array([r['covariance_share'] for r in contribution]);positive=np.maximum(shares,0);positive/=positive.sum()
    loo=pd.DataFrame(index=d.index);leave=[]
    for h in hazards:
        alternative=score-nc[h]
        loo['no_'+h]=alternative
        leave.append(dict(candidate='FEMA_NCV14_CA_v119',removed_hazard=h,
            removed_local_sd=nc[h].std(ddof=0),Pearson_with_original=alternative.corr(score),Spearman_with_original=alternative.corr(score,method='spearman'),
            top230_overlap=len(set(alternative.nlargest(230).index)&set(score.nlargest(230).index))/230,
            role='Frozen CA per-hazard extrema unchanged; final affine normalization unnecessary before cohort standardization'))
    loo['non_earthquake_only']=score-nc.ERQK;loo['earthquake_only']=nc.ERQK
    save('HAZARD_LEAVE_ONE_OUT_VECTORS.csv',loo.reset_index())
    save('HAZARD_LEAVE_ONE_OUT_RANK_SENSITIVITY.csv',leave)
    dump('EFFECTIVE_HAZARD_DIVERSITY.json',dict(review_status=WARN,
        hazards=hazards,local_varying_components=int((nc[hazards].std(ddof=0)>1e-12).sum()),
        positive_covariance_participation_ratio=1/np.sum(positive**2),
        positive_covariance_entropy_effective=np.exp(-np.sum(positive[positive>0]*np.log(positive[positive>0]))),
        earthquake_covariance_share=shares[hazards.index('ERQK')],
        CA_vs_LA_normalization_Pearson=v.FEMA_NCV14_CA_v119.corr(v.FEMA_NCV13_LA_v119_regional_sensitivity),
        CA_vs_LA_normalization_Spearman=v.FEMA_NCV14_CA_v119.corr(v.FEMA_NCV13_LA_v119_regional_sensitivity,method='spearman'),
        caution='Contribution diagnostics, not independent hazard counts or probabilities. Mixed native units and common weather-process sources remain.',
        NHI_land_incomplete_tracts=int(missing_geo.sum()),NHI_land_incomplete_population=int(d.loc[missing_geo,'Population'].sum()),
        NHI_all14_complete_targets=int(coverage.hazards_with_no_source_null_area.eq(14).sum())))
    print('PRE-FIT GATE: qualified FEMA_NCV14_CA_v119 adaptation admitted; original Columbia14 and exact paper9 NOT admitted',flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=1):main()
