"""Distribution, complete-case associations and conditional overlap; no clustering."""
from itertools import combinations
from scipy.stats import pearsonr,spearmanr
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold,GroupKFold,cross_val_predict
from sklearn.metrics import r2_score
from common import *
from audit_fema import describe,HAZARDS

PHYSICAL=['tract_seismic_PGA','Wildfire_high_land_fraction','Flood_SFHA_land_fraction_complete','Historical_heat_days_2018_2022']


def csv(name):return pd.read_csv(lp(OUT/name),dtype={'tract_id':str}).set_index('tract_id')


def association(frame,name):
    complete=frame.dropna()
    assert np.isfinite(complete).all().all()
    save(name+'_COHORT.csv',pd.DataFrame({'tract_id':complete.index}))
    rows=[]
    for a,b in combinations(frame.columns,2):
        pair=frame[[a,b]].dropna()
        if pair[a].nunique()>1 and pair[b].nunique()>1:
            pear=pearsonr(pair[a],pair[b]).statistic;spear=spearmanr(pair[a],pair[b]).statistic
        else:pear=spear=np.nan
        joint=complete[[a,b]]
        pj=pearsonr(joint[a],joint[b]).statistic if joint[a].nunique()>1 and joint[b].nunique()>1 else np.nan
        sj=spearmanr(joint[a],joint[b]).statistic if joint[a].nunique()>1 and joint[b].nunique()>1 else np.nan
        rows.append(dict(variable_a=a,variable_b=b,pairwise_n=len(pair),pairwise_Pearson=pear,pairwise_Spearman=spear,
            same_complete_cohort_n=len(complete),same_cohort_Pearson=pj,same_cohort_Spearman=sj))
    save(name+'_PAIRWISE.csv',rows)
    complete.corr(method='pearson').to_csv(lp(OUT/(name+'_PEARSON_MATRIX.csv')),index_label='variable')
    complete.corr(method='spearman').to_csv(lp(OUT/(name+'_SPEARMAN_MATRIX.csv')),index_label='variable')
    return complete


def main():
    full=csv('FROZEN_P2_AND_COHORT.csv');d=full.loc[full.Population.gt(0)]
    n=csv('FEMA_V119_MATCHED_2299_SOURCE_ROWS.csv');v=csv('PHYSICAL_HAZARD_TRACT_VALUES_BASE.csv')
    flood=csv('PHYSICAL_HAZARD_TRACT_VALUES_FLOOD.csv');v=v.join(flood)
    assert v.index.equals(d.index) and n.index.equals(d.index)
    save('PHYSICAL_HAZARD_TRACT_VALUES.csv',v.reset_index())
    x=d[P2].join(v[PHYSICAL+['PGA_centroid_IDW_g']])
    x['ALR_NPCTL']=n.ALR_NPCTL;x['EAL_SCORE']=n.EAL_SCORE;x['log1p_EAL_VALT']=np.log1p(n.EAL_VALT)
    association(x,'JOINT_INFORMATION')
    # Pairwise values use stated counts; all conditional comparisons use identical joint complete cases.
    core=d[P2].join(v[PHYSICAL]);common=association(core,'PHYSICAL_PLUS_P2')
    overlap=[]
    cv=KFold(n_splits=5,shuffle=True,random_state=42)
    for target in common:
        y=common[target];predictors=common.drop(columns=target)
        model=LinearRegression().fit(predictors,y);r2=model.score(predictors,y)
        yp=cross_val_predict(ExtraTreesRegressor(n_estimators=150,min_samples_leaf=20,max_features=1.,
            random_state=42,n_jobs=1),predictors,y,cv=cv,n_jobs=1)
        base=d[P2].join(v[[target]]) if target not in P2 else d[P2]
        base=base.dropna();cols=[c for c in P2 if c!=target]
        br2=LinearRegression().fit(base[cols],base[target]).score(base[cols],base[target])
        same_base_r2=LinearRegression().fit(common[cols],y).score(common[cols],y)
        xy=d.loc[common.index,['utm_x_m','utm_y_m']]
        groups=((xy.utm_x_m//15000).astype(int).astype(str)+'_'+(xy.utm_y_m//15000).astype(int).astype(str))
        spatial_pred=cross_val_predict(ExtraTreesRegressor(n_estimators=150,min_samples_leaf=20,max_features=1.,
            random_state=42,n_jobs=1),predictors,y,cv=GroupKFold(5),groups=groups,n_jobs=1)
        overlap.append(dict(target=target,n_common_complete_cases=len(common),
            all_other_core_conditional_linear_R2=r2,VIF=1/(1-r2) if r2<1 else np.inf,
            fivefold_nonlinear_predictive_R2=r2_score(y,yp),fivefold_15km_block_nonlinear_R2=r2_score(y,spatial_pred),
            P2_only_conditional_R2=br2,P2_only_R2_on_common_cohort=same_base_r2,
            P2_only_n=len(base),nonlinear_protocol='ExtraTrees 150 trees leaf20, five random folds seed42; no tuning; not causal or spatially independent validation'))
        print('conditional overlap',target,flush=True)
    save('CONDITIONAL_LINEAR_VIF_AND_NONLINEAR_AUDIT.csv',overlap)
    register=[]
    definitions={
        'tract_seismic_PGA':('H','g; no transform','CGS MS48 2025 / NSHM2023 / Vs30 July2022','Land-area grid-supported mean 2pc50 PGA; original extraction, five partial supports retained as null','99% grid-coverage threshold inherited from documented extraction; area not population exposure'),
        'PGA_centroid_IDW_g':('H','g; no transform','Same CGS source','Geometric-centroid log-IDW8 estimate within11km, diagnostic only','Not residence geography; cannot silently replace the polygon construct'),
        'Wildfire_high_land_fraction':('H','fraction of tract land','CAL FIRE SRA effective2024 / LRA recommended2025','Union fraction in High or Very High FHSZ; valid only when classification covers land within 1e-6','Severity categories not annual probability; NonWildland is classification, not no-fire safety; FRA/gaps unknown'),
        'Flood_SFHA_land_fraction_complete':('H','fraction of tract land','Current official NFHL snapshot, see source record','Union SFHA fraction, valid only when known flood-zone coverage covers land within1e-6','A-family cannot uniquely separate riverine/nonwave coastal; V is coastal wave hazard; D/unmapped not zero'),
        'Historical_heat_days_2018_2022':('H','days/year','CDC EJI2024; Tracking2018-2022','Mean number above tract-specific95th-percentile temperature threshold','Official2010-to2020crosswalk; 13national source interpolations not identified; not future heat or absolute heat severity'),
        'ALR_NPCTL':('L','national percentile0-100','FEMA NRI v1.19 Mar-23','EAL-weighted consequence-specific annual-loss-rate percentile','Retains loss and model assumptions; cannot substitute for physical exposure'),
        'EAL_SCORE':('E','national percentile0-100','FEMA NRI v1.19 Mar-23','National percentile of modeled annual losses','Earthquake dominated; not balanced multi-hazard exposure'),
        'log1p_EAL_VALT':('E','log1p(2022USD/year)','FEMA NRI v1.19 Mar-23','Log of total modeled expected annual loss','Model includes asset/population consequences, not power-outage loss')}
    for field,(fam,units,source,definition,limitation) in definitions.items():
        values=x[field]
        register.append(dict(family=fam,variable=field,definition=definition,units_and_transform=units,
            source_vintage=source,measurement='external derived source measurement',
            **describe(values),population_with_valid_measurement=d.Population.loc[values.notna()].sum(),
            recommendation='DESCRIPTIVE_ONLY; physical composite admission gate not passed' if fam=='H' else 'DESCRIPTIVE_ONLY loss comparator',
            scientific_limitation=limitation))
    save('PHYSICAL_HAZARD_MEASUREMENT_REGISTER.csv',register)
    missing=[]
    for key in d.index:
        missing.append(dict(tract_id=key,Population=d.loc[key,'Population'],
            additional_zero_housing_positive_population=d.loc[key,'additional_zero_housing_positive_population'],
            **{c+'_valid':bool(pd.notna(v.loc[key,c])) for c in PHYSICAL},
            missing_physical_fields=';'.join(c for c in PHYSICAL if pd.isna(v.loc[key,c])),
            wildfire_mapped_land_fraction=v.loc[key,'Wildfire_FHSZ_mapped_land_fraction'],
            flood_known_land_fraction=v.loc[key,'Flood_known_zones_land_fraction'],
            fire_FRA_land_fraction=v.loc[key,'Fire_responsibility_FRA_land_fraction']))
    save('TRACT_OVERLAY_AND_MISSINGNESS_QA.csv',missing)
    points=[]
    for a,b,label in [('tract_seismic_PGA','PGA_centroid_IDW_g','PGA polygon versus centroid'),
        ('Wildfire_high_land_fraction','Wildfire_high_centroid_flag','Wildfire high-area versus centroid classification'),
        ('Flood_SFHA_land_fraction_complete','Flood_SFHA_centroid_flag','Flood SFHA-area versus centroid intersection')]:
        pair=v[[a,b]].dropna();points.append(dict(comparison=label,n=len(pair),Pearson=pearsonr(pair[a],pair[b]).statistic,
            Spearman=spearmanr(pair[a],pair[b]).statistic,mean_abs_difference=np.abs(pair[a]-pair[b]).mean(),
            area_positive_point_zero=int((pair[a].gt(1e-6)&pair[b].eq(0)).sum()),
            meaning='point is not residents; binary flag and area fraction have different units except PGA'))
    save('POINT_VERSUS_POLYGON_COMPARISONS.csv',points)
    concentration=[]
    for c in PHYSICAL:
        valid=v[c].dropna();z=(valid-valid.mean())/valid.std(ddof=0);top=valid.nlargest(max(1,int(np.ceil(.01*len(valid))))).index
        concentration.append(dict(variable=c,n=len(valid),standardized_min=z.min(),standardized_max=z.max(),
            upper_1pct_variance_share=(z.loc[top]**2).sum()/(z**2).sum(),
            upper_decile_tracts=int(valid.ge(valid.quantile(.9)).sum()),
            upper_decile_population_in_these_tracts=d.loc[valid.index[valid.ge(valid.quantile(.9))],'Population'].sum(),
            qualifier='population represented by selected tracts, NOT residents exposed within hazard polygons'))
    save('STANDARDIZATION_AND_EXTREME_VALUE_LEVERAGE.csv',concentration)
    # This is loss-composition sensitivity, not a new physical-hazard composite.
    eal=n[[p+'_EALT' for p,*_ in HAZARDS]]
    total=eal.sum(axis=1,min_count=1);loo=[]
    for p,name,*_ in HAZARDS:
        if eal[p+'_EALT'].notna().any():
            remainder=eal.drop(columns=p+'_EALT').sum(axis=1,min_count=1)
            loo.append(dict(excluded_hazard=name,remaining_pooled_loss_USD=remainder.sum(),
                Pearson_with_full_EAL=pearsonr(total,remainder).statistic,
                Spearman_with_full_EAL=spearmanr(total,remainder).statistic,
                excluded_pooled_share=eal[p+'_EALT'].sum()/total.sum(),measurement_family='E only; not physical screening weights'))
    save('LEAVE_ONE_HAZARD_OUT_EXPECTED_LOSS_DIAGNOSTIC.csv',loo)
    status=dict(cohort_size=2299,joint_complete_physical_n=len(common),
        complete_count={c:int(v[c].notna().sum()) for c in PHYSICAL},
        eight_special_use_tracts_retained=int(d.additional_zero_housing_positive_population.sum()),
        admission='FAIL_FOR_COMPLETE_2299_PHYSICAL_COMPOSITE',new_clustering_fits=0,
        no_composite_built=True,no_imputation=True,no_exclusions_added=True)
    assert any(v[c].isna().any() for c in PHYSICAL)
    dump('PHYSICAL_COMPOSITE_ADMISSION_DECISION.json',status)
    save('SEVEN_VERSUS_EIGHT_CONDITIONAL_COMPARISON.csv',[dict(specification='P2 seven variables',status='Preserved existing baseline; no new fit'),
        dict(specification='P2 plus physical multi-hazard coordinate',status='NOT FIT: incomplete physical support and unresolved construct aggregation; no candidate promoted')])
    print(json.dumps(status),flush=True)


if __name__=='__main__':main()
