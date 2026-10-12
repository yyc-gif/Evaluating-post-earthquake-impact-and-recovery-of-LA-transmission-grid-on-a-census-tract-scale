"""Pre-fit construct, dependency and policy-set influence audit."""
from itertools import combinations
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler
from common import *


def main():
    assert json.loads(lp(OUT/'POLICY_ENSEMBLE_QA.json').read_text())['status']=='PASS'
    d=dataset()
    assert len(d)==2299 and d.index.is_unique
    features=list(dict.fromkeys(COLS['A']+COLS['P3']))
    assert np.isfinite(d[features]).all().all()
    dist=[]
    for v in features+['Population','MeanTotalBurden','MeanWithinRealizationPolicySD']:
        x=d[v]; z=(x-x.mean())/x.std(ddof=0)
        ss=z**2
        dist.append(dict(variable=v,n=len(x),missing=x.isna().sum(),zero_count=x.eq(0).sum(),near_zero_1e_8_count=x.abs().le(1e-8).sum(),
            mean=x.mean(),sd=x.std(ddof=0),minimum=x.min(),p10=x.quantile(.1),p25=x.quantile(.25),median=x.median(),
            p75=x.quantile(.75),p90=x.quantile(.9),p99=x.quantile(.99),maximum=x.max(),
            standardized_min=z.min(),standardized_max=z.max(),abs_z_gt3_count=z.abs().gt(3).sum(),
            upper1percent_share_of_variance=ss.loc[x.nlargest(int(np.ceil(len(x)*.01))).index].sum()/ss.sum()))
    save('ORIGINAL_UNIT_FEATURE_DISTRIBUTIONS.csv',dist)
    assoc=[]
    for a,b in combinations(features,2):
        assoc.append(dict(variable_a=a,variable_b=b,pearson=pearsonr(d[a],d[b]).statistic,
            spearman=spearmanr(d[a],d[b]).statistic,shared_exact_identity='B_Impact = B_Unconstrained + Delta_Impact' if {a,b}<={'B_480_hr','B_Unconstrained','Delta_B_logistics'} else ''))
    save('SAME_COHORT_PAIRWISE_ASSOCIATIONS.csv',assoc)
    rows=[]
    folds=KFold(5,shuffle=True,random_state=42)
    for spec in ['A','P2','P3']:
        cs=columns(spec)
        for v in cs:
            rest=[c for c in cs if c!=v]
            x=d[rest].to_numpy(float); y=d[v].to_numpy(float)
            r2=LinearRegression().fit(x,y).score(x,y)
            pred=cross_val_predict(make_pipeline(StandardScaler(),SplineTransformer(n_knots=5,degree=3),Ridge(alpha=1)),x,y,cv=folds)
            nonlinear=r2_score(y,pred)
            domain='RQ1' if v in RQ1 else 'RQ3' if v in RQ3 else 'RQ2'
            same=[c for c in rest if ('RQ1' if c in RQ1 else 'RQ3' if c in RQ3 else 'RQ2')==domain]
            cross=[c for c in rest if c not in same]
            within_r2=LinearRegression().fit(d[same],y).score(d[same],y) if same else 0
            cross_r2=LinearRegression().fit(d[cross],y).score(d[cross],y)
            rows.append(dict(specification=spec,variable=v,domain=domain,conditional_linear_R2=r2,VIF=1/(1-r2),
                nonlinear_out_of_fold_R2=nonlinear,within_domain_linear_R2=within_r2,cross_domain_linear_R2=cross_r2,
                squared_distance_budget=weights(spec)[cs.index(v)],new_construct='Policy-set sensitivity, not physical uncertainty' if v=='PolicySD' else ''))
    save('POLICY_VARIABILITY_INFORMATION_AUDIT.csv',rows)
    sensitivity=[]
    for name in SETS:
        alt=dataset(name)
        assert np.array_equal(d.index,alt.index)
        for v in ['MeanDelta','PolicySD']:
            diff=alt[v]-d[v]
            rel=diff/d[v].where(d[v].ne(0))
            for tid in d.index:
                sensitivity.append(dict(tract_id=tid,policy_set=name,variable=v,main5_hr=d.loc[tid,v],alternative_hr=alt.loc[tid,v],
                    change_hr=diff.loc[tid],relative_change=rel.loc[tid],Population=d.loc[tid,'Population'],frozen_SOVI_quartile=d.loc[tid,'frozen_SOVI_quartile'],
                    INTPTLAT=d.loc[tid,'INTPTLAT'],INTPTLON=d.loc[tid,'INTPTLON']))
    sensitivity=pd.DataFrame(sensitivity)
    save('LEAVE_ONE_POLICY_OUT_FEATURE_SENSITIVITY.csv',sensitivity)
    summary=[]
    for (name,v), part in sensitivity.groupby(['policy_set','variable'],sort=False):
        xx=part.change_hr.abs()
        summary.append(dict(policy_set=name,variable=v,pearson_with_main5=pearsonr(part.main5_hr,part.alternative_hr).statistic,
            spearman_with_main5=spearmanr(part.main5_hr,part.alternative_hr).statistic,
            mean_change_hr=part.change_hr.mean(),median_absolute_change_hr=xx.median(),p90_absolute_change_hr=xx.quantile(.9),max_absolute_change_hr=xx.max(),
            median_abs_relative_change=part.relative_change.abs().median(),zero_denominator_count=part.relative_change.isna().sum()))
    save('POLICY_SET_FEATURE_SENSITIVITY_SUMMARY.csv',summary)
    contributions=frame('POLICY_VARIANCE_CONTRIBUTIONS.csv')
    contributions=contributions.loc[contributions.tract_id.isin(d.index)]
    high=d.PolicySD.ge(d.PolicySD.quantile(.9))
    row=[]
    for p in PRIMARY:
        q=contributions.query('policy==@p').set_index('tract_id').reindex(d.index)
        fraction=q.contribution_to_policy_variance_hr2.sum()/d.PolicySD.pow(2).sum()
        row.append(dict(policy=p,share_of_total_policy_variance=fraction,
            largest_squared_deviation_tracts=q.largest_squared_deviation.sum(),
            high_PolicySD_largest_deviation_tracts=q.loc[high,'largest_squared_deviation'].sum(),
            high_PolicySD_variance_share=q.loc[high,'contribution_to_policy_variance_hr2'].sum()/d.loc[high,'PolicySD'].pow(2).sum(),
            positive_deviation_fraction=q.deviation_from_MeanDelta_hr.gt(0).mean()))
    save('POLICY_VARIANCE_INFLUENCE_SUMMARY.csv',row)
    blocks=(d.utm_x_m>=d.utm_x_m.median()).astype(int)+2*(d.utm_y_m>=d.utm_y_m.median()).astype(int)
    coverage=[]
    for group in ['ALL','Q1','Q2','Q3','Q4','block0','block1','block2','block3']:
        selected=np.ones(len(d),bool) if group=='ALL' else blocks.eq(int(group[-1])).to_numpy() if group.startswith('block') else d.frozen_SOVI_quartile.eq(group).to_numpy()
        part=d.loc[selected]; upper=high.loc[selected]
        coverage.append(dict(group=group,n_tracts=len(part),population=part.Population.sum(),high_PolicySD_tracts=upper.sum(),
            high_PolicySD_population=part.loc[upper,'Population'].sum(),mean_PolicySD=part.PolicySD.mean(),median_PolicySD=part.PolicySD.median(),
            mean_MeanDelta=part.MeanDelta.mean(),median_MeanDelta=part.MeanDelta.median()))
    save('HIGH_POLICY_SD_GEOGRAPHIC_AND_QUARTILE_COVERAGE.csv',coverage)
    save('HIGH_POLICY_SD_TRACTS.csv',d.loc[high,['Population','PolicySD','MeanDelta','SOVI_SCORE','frozen_SOVI_quartile','INTPTLAT','INTPTLON','hospital_tract']].reset_index())
    circular=[]
    excluded=dataset('without_vulnerability-first')
    for name,part in [('main5',d),('without_vulnerability-first',excluded)]:
        for v in ['MeanDelta','PolicySD']:
            circular.append(dict(policy_set=name,variable=v,pearson_SOVI=pearsonr(part[v],part.SOVI_SCORE).statistic,
                spearman_SOVI=spearmanr(part[v],part.SOVI_SCORE).statistic,
                mean_Q1=part.loc[part.frozen_SOVI_quartile.eq('Q1'),v].mean(),mean_Q4=part.loc[part.frozen_SOVI_quartile.eq('Q4'),v].mean()))
    save('VULNERABILITY_FIRST_INFLUENCE_NUMERICS.csv',circular)
    save('POLICY_SD_ESTIMAND_COMPARISON.csv',d[['PolicySD','MeanWithinRealizationPolicySD']].reset_index())
    specs={sp:dict(coordinates=columns(sp),squared_distance_budgets=dict(zip(columns(sp),weights(sp)))) for sp in ['A','P2','P3','P2-minus-Init','P3-minus-Init']}
    dump('FEATURE_SPECIFICATIONS_AND_WEIGHTS.json',dict(cohort_count=2299,policy_sets=SETS,specifications=specs,
        z_score_sd_ddof=0,policy_SD_ddof=0,observation_weights='Equal tract weights',euclidean_application='Multiply z scores by square roots of budgets',
        P2_to_P3='Coordinate inclusion and internal RQ2 budget redistribution both change',ablation='RQ1 budget redistribution also changes'))
    dump('INFORMATION_AUDIT_COMPLETION.json',dict(status='PASS',cohort=2299,all_primary_features_finite=True,
        exact_identity_excluded_from_fitted_coordinates=True,fit_not_started=True,
        registration_sha256=sha(OUT/'REGISTERED_ANALYSIS.json'),five_plus_five_LOO_plus_Random_unique_sets=len(SETS)))
    print('Pre-fit information audit PASS',flush=True)


if __name__=='__main__': main()
