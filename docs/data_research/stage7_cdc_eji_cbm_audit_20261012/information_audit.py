"""Conditional information and composition diagnostics, not cluster selection."""
from itertools import combinations
from scipy.stats import pearsonr, spearmanr
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold, GroupKFold, cross_val_predict
from audit_cdc import CODES, DOMAINS, EPL, INDICATORS, read_bulk, safe_assoc
from common import *


def load(name):
    return pd.read_csv(lp(OUT/name),dtype={'tract_id':str,'GEOID':str}).set_index('tract_id')


def overlap(frame, target):
    x = frame.drop(columns=target)
    y = frame[target]
    assert np.isfinite(frame).all().all()
    linear = LinearRegression().fit(x,y)
    r2 = linear.score(x,y)
    full = load('FROZEN_P2_AND_COHORT.csv').reindex(frame.index)
    xy = full[['utm_x_m','utm_y_m']]
    blocks = (xy.utm_x_m//15000).astype(int).astype(str)+'_'+(xy.utm_y_m//15000).astype(int).astype(str)
    estimator = ExtraTreesRegressor(n_estimators=150,min_samples_leaf=20,max_features=1.,random_state=42,n_jobs=1)
    predicted = cross_val_predict(estimator,x,y,cv=KFold(5,shuffle=True,random_state=42),n_jobs=1)
    spatial = cross_val_predict(estimator,x,y,cv=GroupKFold(5),groups=blocks,n_jobs=1)
    foldrows = []
    for fold, (train,test) in enumerate(GroupKFold(5).split(x,y,blocks)):
        foldrows.append(dict(target=target,fold=fold,train_n=len(train),test_n=len(test),
                             spatial_prediction_R2=r2_score(y.iloc[test],spatial[test]),
                             train_block_count=blocks.iloc[train].nunique(),test_block_count=blocks.iloc[test].nunique()))
    return dict(target=target,n=len(y),conditional_linear_R2=r2,VIF=1/(1-r2),
                random5fold_nonlinear_R2=r2_score(y,predicted),spatial15km_5fold_nonlinear_R2=r2_score(y,spatial),
                interpretation='Fixed predictive overlap, not independence, causal effect or external validation'), foldrows


def main():
    full = load('FROZEN_P2_AND_COHORT.csv')
    d = full.loc[full.Population.gt(0)]
    cdc = load('CDC_2024_MATCHED_ORIGINAL_VALUES.csv').reindex(d.index)
    x = d[P2].join(cdc[['RPL_CBM']])
    assert len(x)==2299 and x.notna().all().all()
    save('CBM_PLUS_P2_VERIFIED_FEATURE_VALUES.csv',x.reset_index())
    assoc = []
    for a,b in combinations(x.columns,2):
        assoc.append(dict(variable_a=a,variable_b=b,**safe_assoc(x[a],x[b])))
    save('CBM_P2_SAME_COHORT_ASSOCIATIONS.csv',assoc)
    x.corr().to_csv(lp(OUT/'CBM_P2_PEARSON_MATRIX.csv'),index_label='variable')
    x.corr(method='spearman').to_csv(lp(OUT/'CBM_P2_SPEARMAN_MATRIX.csv'),index_label='variable')
    conditional=[]
    folds=[]
    for target in x:
        row,fr=overlap(x,target)
        conditional.append(row)
        folds.extend(fr)
        print('Information audit',target,clean(row),flush=True)
    save('CBM_VS_P2_REDUNDANCY_AND_INFORMATION.csv',conditional)
    save('SPATIAL_BLOCK_PREDICTIVE_OVERLAP.csv',folds)
    distributions=[]
    for col in x:
        v=x[col]
        z=(v-v.mean())/v.std(ddof=0)
        top=v.nlargest(int(np.ceil(.01*len(v)))).index
        distributions.append(dict(variable=col,**describe(v),standardized_min=z.min(),standardized_max=z.max(),
            upper1pct_variance_share=(z.loc[top]**2).sum()/(z**2).sum()))
    for col in ['SPL_CBM','RPL_CBM_DOM1','RPL_CBM_DOM2','RPL_CBM_DOM3']+['E_'+c for c in CODES]+EPL:
        distributions.append(dict(variable=col,**describe(cdc[col])))
    save('CBM_ALL_COORDINATE_DISTRIBUTIONS.csv',distributions)
    score=cdc.SPL_CBM
    variance=score.var(ddof=0)
    baseR2=LinearRegression().fit(cdc[EPL],cdc.RPL_CBM).score(cdc[EPL],cdc.RPL_CBM)
    contribution=[]
    for codes,name,kind in [([c],c,'indicator') for c in CODES]+[(c,k,'domain') for k,c in DOMAINS.items()]:
        fields=['EPL_'+c for c in codes]
        values=cdc[fields].sum(axis=1)
        others=cdc[[c for c in EPL if c not in fields]]
        fullcov=np.mean((values-values.mean())*(score-score.mean()))/variance
        reducedR2=LinearRegression().fit(others,cdc.RPL_CBM).score(others,cdc.RPL_CBM)
        residual_y=cdc.RPL_CBM-LinearRegression().fit(others,cdc.RPL_CBM).predict(others)
        residual_x=values-LinearRegression().fit(others,values).predict(others)
        partial=pearsonr(residual_x,residual_y).statistic if residual_x.std()>1e-10 else np.nan
        contribution.append(dict(component=name,type=kind,number_of_indicator_ranks=len(fields),
            declared_indicator_budget_fraction=len(fields)/9,**{**describe(values),**safe_assoc(values,cdc.RPL_CBM)},
            covariance_share_of_local_SPL_variance=fullcov,full_indicator_linear_R2_for_published_rank=baseR2,
            incremental_linear_R2_for_published_rank=baseR2-reducedR2,partial_Pearson_rank_control_other_components=partial,
            interpretation='Composition diagnostics, not causal contribution or independent validation; covariance shares include shared geographic variation'))
    save('CBM_DOMAIN_AND_INDICATOR_CONTRIBUTIONS.csv',contribution)
    # National rerank of remaining published indicator percentiles, not new CDC indices.
    national=read_bulk('United_States').set_index('GEOID')
    valid=national.RPL_CBM.between(0,1)&national[EPL].ge(0).all(axis=1)
    national=national.loc[valid]
    alternative=[]
    loo_values=pd.DataFrame(index=d.index)
    top=set(cdc.RPL_CBM.nlargest(230).index)
    for codes,name,kind in [([c],c,'indicator') for c in CODES]+[(c,k,'domain') for k,c in DOMAINS.items()]:
        remaining=[c for c in EPL if c not in ['EPL_'+v for v in codes]]
        rank=(national[remaining].sum(axis=1).rank(method='min')-1)/(len(national)-1)
        v=rank.reindex(d.index)
        loo_values['researcher_national_leaveout_'+name]=v
        alternative.append(dict(excluded=name,type=kind,national_ranking_n=len(national),**safe_assoc(v,cdc.RPL_CBM),
            mean_abs_rank_change=(v-cdc.RPL_CBM).abs().mean(),max_abs_rank_change=(v-cdc.RPL_CBM).abs().max(),
            top230_membership_retention=len(top & set(v.nlargest(230).index))/230,
            note='Researcher diagnostic on same national CBM-valid cohort; no official CDC rank overwritten'))
    save('CBM_RESEARCHER_LEAVEOUT_RANK_DIAGNOSTICS.csv',alternative)
    save('CBM_RESEARCHER_LEAVEOUT_TRACT_RANKS.csv',loo_values.reset_index())
    cdc[EPL].corr().to_csv(lp(OUT/'CBM_INDICATOR_PEARSON_MATRIX.csv'),index_label='indicator')
    cdc[EPL].corr(method='spearman').to_csv(lp(OUT/'CBM_INDICATOR_SPEARMAN_MATRIX.csv'),index_label='indicator')
    # Flag influence: no truly unflagged composite group exists because hurricane F=1 for every tract.
    q=load('CBM_TRACT_QUALITY_COUNTS.csv')
    groups=[]
    for label,mask in [('at_least_one_source_null',q.source_null_or_excluded_indicator_count.gt(0)),
                       ('no_source_null_flags',q.source_null_or_excluded_indicator_count.eq(0)),
                       ('unflagged_burn_zero',cdc.E_BURN.eq(0)),('positive_burn',cdc.E_BURN.gt(0)),
                       ('special_use_8',d.additional_zero_housing_positive_population.astype(bool))]:
        idx=d.index[mask.reindex(d.index)]
        groups.append(dict(group=label,Population=d.loc[idx,'Population'].sum(),**describe(cdc.loc[idx,'RPL_CBM']),
            note='No flag-free full-composite comparison possible; burn groups are not observed-versus-missing strata'))
    save('CBM_FLAG_INFLUENCE_SUBGROUPS.csv',groups)
    s=sources()
    physical=frozen(s,MH+'PHYSICAL_HAZARD_TRACT_VALUES.csv').set_index('tract_id').reindex(d.index)
    comparisons=[]
    pairs=[('E_NEHD','Historical_heat_days_2018_2022','Same CDC source snapshot; agreement is reproducibility, not independent validation'),
           ('E_BURN','Wildfire_high_land_fraction','Historical burned-area percentage versus current high/very-high land severity; different constructs'),
           ('E_SMOKE','Wildfire_high_land_fraction','Regional smoke cover is not local land fire severity'),
           ('E_RFLD','Flood_SFHA_land_fraction_complete','Historical/minimum event-day frequency is not NFHL probability-area fraction'),
           ('E_CFLD','Flood_coastal_V_land_fraction','NRI coastal modeled frequency versus V/VE wave-hazard area'),
           ('RPL_CBM','tract_seismic_PGA','Context association only; earthquake not a CBM component'),
           ('RPL_CBM','Wildfire_high_land_fraction','Standalone climate rank versus independently mapped fire severity'),
           ('RPL_CBM','Flood_SFHA_land_fraction_complete','Standalone climate rank versus known SFHA area coverage')]
    for a,b,note in pairs:
        if b not in physical:
            matches=[c for c in physical if 'coastal' in c.lower()]
            print('AVAILABLE_COASTAL_FIELDS',matches,flush=True)
            continue
        stat=safe_assoc(cdc[a],physical[b])
        pair=pd.concat([cdc[a],physical[b]],axis=1).dropna()
        comparisons.append(dict(CDC_variable=a,physical_variable=b,**stat,
            max_abs_difference=(pair[a]-pair[b]).abs().max() if a=='E_NEHD' else np.nan,
            definition_distinction=note))
    save('CBM_VS_OFFICIAL_PHYSICAL_HAZARDS.csv',comparisons)
    save('INDEPENDENT_PHYSICAL_MATCHED_VALUES.csv',physical.reset_index())
    save('SCIENTIFIC_INPUT_HASHES_INFORMATION.csv',s.records)
    # Algebraic distance accounting only. No weighted matrix is fitted at this stage.
    z=(x-x.mean())/x.std(ddof=0)
    budgets={'P2':[1/9,1/9,1/9,1/6,1/6,1/6,1/6,0],
             'H1':[1/9,1/9,1/9,1/6,1/6,1/9,1/9,1/9],
             'H2':[1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12]}
    distances=[]
    for spec,w in budgets.items():
        per=z.pow(2)*w
        for col in x:
            distances.append(dict(specification=spec,coordinate=col,squared_distance_budget=w[list(x).index(col)],
                summed_squared_distance_from_mean=per[col].sum(),fraction=per[col].sum()/per.sum().sum(),
                qualifier='Algebraic distance allocation only; not a fit or validation'))
    save('REGISTERED_ALGEBRAIC_DISTANCE_BUDGETS.csv',distances)
    print('Composition, physical correspondence and information audit complete; no K-means fits',flush=True)


if __name__=='__main__':
    main()
