"""Incremental information and narrowly registered component sensitivity, not simulation."""
import zipfile
from itertools import combinations
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.metrics import adjusted_rand_score, silhouette_samples
from threadpoolctl import threadpool_limits
from common import *

DOMAIN_CODES={'Heat':['NEHD'],'Wildfire':['SMOKE','BURN'],
              'Extreme_Events':['CFLD','DRGT','RFLD','HRCN','SWND','TRND']}
OLD_REMOVALS={'RFLD':'no_riverine','BURN':'no_burn','NEHD':'no_heat','Wildfire':'no_wildfire'}


def compare(a,b,pop):
    k=max(a.max(),b.max())+1;tab=np.zeros((k,k),int);np.add.at(tab,(a,b),1)
    i,j=linear_sum_assignment(-tab);mapping=dict(zip(j,i));aligned=np.array([mapping[c] for c in b]);changed=aligned!=a
    return dict(ARI=adjusted_rand_score(a,b),reassigned_tracts=int(changed.sum()),
                reassigned_population=int(pop[changed].sum()),reassigned_population_share=pop[changed].sum()/pop.sum())


def main():
    s=source_reader();d=frame('VERIFIED_EIGHT_VARIABLE_COHORT.csv','tract_id')
    f=np.load(lp(OUT/'REUSED_MAIN_FIT_ARRAYS.npz'));idx={k:i for i,k in enumerate(f['keys'])}
    mats=np.load(lp(OUT/'REUSED_WEIGHTED_MATRICES.npz'))
    np.testing.assert_array_equal(d.index,f['tract_ids'])
    # Same-cohort associations and conditional information use all eight coordinates.
    x=d[P2+['RPL_CBM']];old=read(s,CB+'CBM_VS_P2_REDUNDANCY_AND_INFORMATION.csv').set_index('target')
    rows=[]
    for col in x:
        y=x[col];r2=LinearRegression().fit(x.drop(columns=col),y).score(x.drop(columns=col),y)
        assert abs(r2-old.loc[col,'conditional_linear_R2'])<1e-10
        rows.append(dict(variable=col,valid_count=len(y),missing_count=int(y.isna().sum()),zero_count=int(y.eq(0).sum()),
          mean=y.mean(),population_sd=y.std(ddof=0),p10=y.quantile(.1),p25=y.quantile(.25),median=y.median(),p75=y.quantile(.75),p90=y.quantile(.9),
          minimum=y.min(),maximum=y.max(),conditional_linear_R2=r2,VIF=1/(1-r2),
          nonlinear_random5fold_R2=old.loc[col,'random5fold_nonlinear_R2'],nonlinear_spatial15km_5fold_R2=old.loc[col,'spatial15km_5fold_nonlinear_R2'],
          nonlinear_source=AUTH+':'+CB+'CBM_VS_P2_REDUNDANCY_AND_INFORMATION.csv',nonlinear_reused=True,
          Pearson_with_CBM=y.corr(d.RPL_CBM),Spearman_with_CBM=y.corr(d.RPL_CBM,method='spearman')))
    save('EIGHTH_COORDINATE_INCREMENTAL_INFORMATION.csv',rows)
    save('EIGHT_VARIABLE_PAIRWISE_ASSOCIATIONS.csv',[dict(variable_a=a,variable_b=b,Pearson=x[a].corr(x[b]),Spearman=x[a].corr(x[b],method='spearman')) for a,b in combinations(x.columns,2)])

    # Genuine alternative: official EPA 2015 PRISM. Identifier matches do not prove geometry identity.
    prism=pd.read_excel(lp(OUT/'sources/EPA_PRISM_WORKBOOK.xlsx'),dtype={'TR_GEOID':str})
    prism.TR_GEOID=prism.TR_GEOID.str.zfill(11)
    assert prism.TR_GEOID.is_unique and prism.TR_GEOID.str.fullmatch(r'\d{11}').all()
    assert (prism.Hazard_Exp-prism.Proport_Exp-1).abs().max()==0
    joined=prism.set_index('TR_GEOID').reindex(d.index)
    cohort=d[['Population','additional_zero_housing_positive_population']].join(joined[['Hazard_Exp','Proport_Exp']])
    cohort['identifier_match']=cohort.Hazard_Exp.notna()
    cohort['same_geometry_verified']=False
    save('EPA_PRISM_2015_TO_FROZEN_2020_GEOID_AUDIT.csv',cohort.reset_index())
    pvalid=joined.Proport_Exp.notna();subset=d.loc[pvalid]
    save('EPA_PRISM_INCOMPLETE_COHORT_DIAGNOSTICS.csv',[dict(variable=c,n_identifier_matched=int(pvalid.sum()),
          Pearson=joined.loc[pvalid,'Proport_Exp'].corr(subset[c]),Spearman=joined.loc[pvalid,'Proport_Exp'].corr(subset[c],method='spearman'),
          limitation='Only exact identifier intersection; not full-cohort eligibility or unchanged-geometry proof') for c in x])
    dump('EPA_PRISM_SOURCE_AND_COVERAGE_QA.json',dict(review_status=WARN,national_records=len(prism),duplicates=0,
         identifier_matches=int(pvalid.sum()),unmatched=int((~pvalid).sum()),unmatched_population=int(d.loc[~pvalid,'Population'].sum()),
         retained_special_use_matches=int(pvalid[d.additional_zero_housing_positive_population.astype(bool)].sum()),
         exact_identity='Hazard_Exp = 1 + Proport_Exp across every original record',
         source_geography='2015 Census/ACS geography, not automatically frozen 2020 boundaries',
         full_cohort_admission=False,missing_imputed=False,clustering_fits=0,
         source_quality='Underlying individual hazard counts/flags not in aggregate workbook; paper includes natural and technological sources; cannot certify natural-only subset from this workbook'))

    with zipfile.ZipFile(s.source(CB+'sources/EJI_2024_United_States_CSV.zip',AUTH)) as z:
        with z.open('EJI_2024_United_States.csv') as file:
            national=pd.read_csv(file,dtype={'GEOID':str,'GEOID_2020':str},low_memory=False)
    epl=['EPL_'+c for c in CODES]
    eligible=national.RPL_CBM.between(0,1)&national[epl].ge(0).all(axis=1)
    n=national.loc[eligible].set_index('GEOID');assert len(n)==83509
    ticks=(n[epl]*10000).round().astype('int64')
    assert np.max(np.abs(ticks.to_numpy()/10000-n[epl].to_numpy()))<1e-12
    np.testing.assert_array_equal(n.loc[d.index,'RPL_CBM'].to_numpy(),d.RPL_CBM.to_numpy())
    cdc=read(s,CB+'CDC_2024_MATCHED_ORIGINAL_VALUES.csv','tract_id').reindex(d.index)
    score=cdc[epl].sum(axis=1);var=score.var(ddof=0)
    qrows=[]
    for code in CODES:
        y=cdc['EPL_'+code];raw=cdc['E_'+code];flag='F_'+code
        cov=np.mean((y-y.mean())*(score-score.mean()))/var
        flag_values=cdc[flag].value_counts().to_dict() if flag in cdc else None
        qrows.append(dict(indicator=code,domain=next(k for k,v in DOMAIN_CODES.items() if code in v),valid_published_count=raw.between(0,np.inf).sum(),
             missing_published_raw=int(raw.isna().sum()+raw.lt(0).sum()),zero_raw_count=int(raw.eq(0).sum()),
             zero_percentile_count=int(y.eq(0).sum()),unique_raw=raw.nunique(),unique_percentile=y.nunique(),
             raw_mean=raw.mean(),raw_median=raw.median(),raw_p10=raw.quantile(.1),raw_p90=raw.quantile(.9),
             published_percentile_sd=y.std(ddof=0),covariance_share_of_local_SPL=cov,
             flag_field=flag if flag in cdc else 'NOT_PUBLISHED_UNRESOLVED',flag_counts=json.dumps(clean(flag_values)),
             physical_zero_certification='No new certification; original F semantics preserved',earthquake_component=False))
    save('MULTIHAZARD_COMPONENT_AND_COVERAGE_QA.csv',qrows)
    shares=np.array([q['covariance_share_of_local_SPL'] for q in qrows]);positive=np.maximum(shares,0);positive/=positive.sum()
    family_groups={'Heat':['NEHD'],'Wildfire':['SMOKE','BURN'],'Flood':['CFLD','RFLD'],'Drought':['DRGT'],'Hurricane':['HRCN'],'Wind':['SWND'],'Tornado':['TRND']}
    family=np.array([sum(max(shares[CODES.index(c)],0) for c in codes) for codes in family_groups.values()]);family/=family.sum()
    high=d.E_RFLD.gt(0);y=d.RPL_CBM;pred=np.where(high,y[high].mean(),y[~high].mean())
    riverine_R2=1-np.sum((y-pred)**2)/np.sum((y-y.mean())**2)
    groups=[]
    for value in [False,True]:
        part=d.loc[high.eq(value)]
        groups.append(dict(riverine_positive=value,n=len(part),population=int(part.Population.sum()),CBM_mean=part.RPL_CBM.mean(),
             CBM_sd=part.RPL_CBM.std(ddof=0),CBM_p10=part.RPL_CBM.quantile(.1),CBM_p90=part.RPL_CBM.quantile(.9),
             Spearman_heat_CBM=part.RPL_CBM.corr(part.EPL_NEHD,method='spearman'),Spearman_wildfire_CBM=part.RPL_CBM.corr(part.EPL_SMOKE+part.EPL_BURN,method='spearman')))
    save('WITHIN_RIVERINE_STRATUM_MULTICLIMATE_INFORMATION.csv',groups)
    dump('EFFECTIVE_LOCAL_HAZARD_CONTENT.json',dict(review_status=WARN,
         positive_covariance_indicator_participation_ratio=1/np.sum(positive**2),
         positive_covariance_indicator_entropy_effective=np.exp(-sum(v*np.log(v) for v in positive if v>0)),
         hazard_family_positive_covariance_participation_ratio=1/np.sum(family**2),
         hazard_family_shares=dict(zip(family_groups,family)),signed_indicator_covariance_shares=dict(zip(CODES,shares)),
         riverine_binary_published_rank_R2=riverine_R2,
         caution='Descriptive participation ratios, not counts of independent measured hazards. Correlated contributions, national ties, and source-zero rules remain.',
         informative_non_earthquake_content=True,equal_effective_hazards=False))

    # National leave-one-indicator ranks keep the original eligible universe and exact ties.
    removals={**{c:[c] for c in CODES},**DOMAIN_CODES}
    ranks=pd.DataFrame(index=d.index);rankrows=[];fitrows=[];newkeys=[];newlab=[];newsil=[];newmatrix={};newcenters={};reused=0
    top=set(d.RPL_CBM.sort_values(ascending=False,kind='stable').head(230).index)
    oldrank=read(s,CK+'NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv','tract_id')
    for name,drop in removals.items():
        retained=[c for c in CODES if c not in drop]
        sums=ticks[['EPL_'+c for c in retained]].sum(axis=1)
        rr=(sums.rank(method='min')-1)/(len(n)-1);ranks[name]=rr.reindex(d.index)
        if name in OLD_REMOVALS: np.testing.assert_array_equal(ranks[name],oldrank[OLD_REMOVALS[name]])
        changed_top=set(ranks[name].sort_values(ascending=False,kind='stable').head(230).index)
        rankrows.append(dict(removed=name,removed_indicators=';'.join(drop),same_national_eligible=83509,
             Pearson=d.RPL_CBM.corr(ranks[name]),Spearman=d.RPL_CBM.corr(ranks[name],method='spearman'),
             mean_abs_rank_shift=(ranks[name]-d.RPL_CBM).abs().mean(),max_abs_rank_shift=(ranks[name]-d.RPL_CBM).abs().max(),
             top230_retention=len(top&changed_top)/230,
             local_removed_percentile_variance=cdc[['EPL_'+c for c in drop]].sum(axis=1).var(ddof=0),
             official_CDC_alternative=False))
        # Heat-domain is identical to removing NEHD; no duplicate independent test.
        if name=='Heat': continue
        if name in OLD_REMOVALS:
            oldname=OLD_REMOVALS[name]
            for k in [3,4,5]:
                key=f'H2__component_{oldname}__k{k}__s42';base=f'H2__published__k{k}__s42'
                lab=f['labels'][idx[key]];value=compare(f['labels'][idx[base]],lab,d.Population.to_numpy())
                fitrows.append(dict(removed=name,k=k,seed=42,fit_source='REUSED_EXACT_AUTHORITY_LABELS',**value))
                reused+=1
            continue
        col=ranks[name].to_numpy();newx=mats['H2__published'].copy()
        newx[:,-1]=(col-col.mean())/col.std()*np.sqrt(1/12)
        newmatrix[name]=newx
        dist=None
        for k in [3,4,5]:
            model=KMeans(n_clusters=k,random_state=42,**PARAMS).fit(newx)
            lab=model.labels_.astype('int16');sil=silhouette_samples(newx,lab,metric='euclidean')
            base=f['labels'][idx[f'H2__published__k{k}__s42']]
            value=compare(base,lab,d.Population.to_numpy());key=f'H2__remove_{name}__k{k}__s42'
            newcenters[key]=model.cluster_centers_
            final_means=np.stack([newx[lab==c].mean(0) for c in range(k)])
            centroid_WCSS=np.sum((newx-final_means[lab])**2)
            newkeys.append(key);newlab.append(lab);newsil.append(sil)
            fitrows.append(dict(removed=name,k=k,seed=42,fit_source='NEW_NARROW_REGISTERED_COMPONENT_DIAGNOSTIC',WCSS=model.inertia_,
                final_membership_centroid_WCSS=centroid_WCSS,model_vs_final_membership_centroid_WCSS_gap=model.inertia_-centroid_WCSS,
                n_iter=model.n_iter_,mean_silhouette=sil.mean(),**value))
            print('Component diagnostic',name,k,'ARI',value['ARI'],flush=True)
    save('ALL_COMPONENT_REMOVAL_NATIONAL_RANKS.csv',ranks.reset_index())
    save('ALL_COMPONENT_REMOVAL_RANK_SENSITIVITY.csv',rankrows)
    save('HAZARD_COMPONENT_SENSITIVITY.csv',fitrows)
    np.savez_compressed(destination('NEW_COMPONENT_FIT_ARRAYS.npz'),tract_ids=d.index.to_numpy(),keys=np.array(newkeys),labels=np.array(newlab),silhouette=np.array(newsil))
    np.savez_compressed(destination('NEW_COMPONENT_WEIGHTED_MATRICES.npz'),**newmatrix)
    np.savez_compressed(destination('NEW_COMPONENT_MODEL_CENTERS.npz'),**newcenters)
    dump('REGISTERED_REUSE_AND_EXTENSION_QA.json',dict(review_status=WARN,reused_main_and_sensitivity_fits=len(f['keys']),
         previous_H2_component_seed42_fits_reused=reused,new_component_diagnostic_fits=len(newkeys),no_new_primary_fit=True,
         no_alternative_hazard_fit_without_complete_source=True,no_new_physical_or_recovery_simulation=True))
    # Algebraic distance comparison explicitly separates hazard addition from population reallocation.
    alg=[]
    from scipy.spatial.distance import squareform
    zp=(d.log1p_Population-d.log1p_Population.mean())/d.log1p_Population.std(ddof=0)
    zh=(d.RPL_CBM-d.RPL_CBM.mean())/d.RPL_CBM.std(ddof=0)
    base=pdist(mats['P2__published'],metric='sqeuclidean');haz=pdist(zh.to_numpy()[:,None],metric='sqeuclidean')/12
    reallocation=-pdist(zp.to_numpy()[:,None],metric='sqeuclidean')/12
    total=pdist(mats['H2__published'],metric='sqeuclidean');err=np.max(np.abs(base+haz+reallocation-total));assert err<1e-11
    alg.append(dict(contrast='P2 to H2 fixed-pair squared distances; no fitted-label attribution',pairs=len(base),
         mean_old_distance=base.mean(),mean_hazard_added=haz.mean(),mean_population_reallocation=reallocation.mean(),mean_new_distance=total.mean(),
         algebra_max_error=err,notice='Mean effects cancel due standardization; individual pairs and resulting partitions still change'))
    save('HAZARD_ADDITION_VS_POPULATION_REALLOCATION_PAIR_ALGEBRA.csv',alg)
    save('SOURCE_HASH_VERIFICATION_ANALYSIS.csv',s.records)
    print('Analysis complete: eight-variable candidate retained; EPA alternative fails full cohort',flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=1): main()
