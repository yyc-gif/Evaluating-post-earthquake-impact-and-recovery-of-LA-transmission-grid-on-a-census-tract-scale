"""Numerical tie correction only; preserve published and policy/geographic fits."""
import zipfile
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances,silhouette_samples
from threadpoolctl import threadpool_limits
from common import *


def main():
    s=sources(); d0=frame('VERIFIED_COHORT_AND_DESCRIPTORS.csv'); pop=d0.Population.to_numpy()
    z=zipfile.ZipFile(s.source(CB+'sources/EJI_2024_United_States_CSV.zip',AUTH))
    n=pd.read_csv(z.open('EJI_2024_United_States.csv'),dtype={'GEOID':str},low_memory=False)
    n=n.loc[n.RPL_CBM.between(0,1)].set_index('GEOID'); assert len(n)==83509
    ticks=np.rint(n[['EPL_'+c for c in CODES]].to_numpy()*10000).astype(np.int64)
    assert np.max(np.abs(ticks/10000-n[['EPL_'+c for c in CODES]].to_numpy()))<2e-16
    before=frame('NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv'); fixed=pd.DataFrame(index=d0.index)
    records=[]; top0=set(d0.RPL_CBM.sort_values(ascending=False,kind='stable').head(230).index)
    for name,drop in REMOVALS.items():
        scores=ticks[:,[i for i,c in enumerate(CODES) if c not in drop]].sum(1)
        rank=pd.Series((np.searchsorted(np.sort(scores),scores,side='left'))/(len(n)-1),index=n.index)
        fixed[name]=rank.reindex(d0.index)
        diff=(fixed[name]-before[name]).abs()
        records.append(dict(diagnostic=name,max_tie_correction=diff.max(),changed_rank_count=int(diff.gt(1e-10).sum())))
    save('NUMERICAL_TIE_RANK_CORRECTION.csv',records)
    dump('NUMERICAL_TIE_HANDLING_AMENDMENT.json',dict(label=WARN,
        reason='Independent exact-decimal audit found artificial sub-ULP ties in unrounded float sums',
        published_source_unchanged=True,main_and_policy_and_spatial_fits_unchanged=True,
        correction='Sum published four-decimal EPLs as integer ticks, then min rank/(N-1) on the same83509 records',
        fitted_scope='Only existing registered component K3/4/5 seeds42-46; no new search or weights',
        before_rank_sha256=sha(OUT/'NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv'),differences=records))
    save('NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv',fixed.reset_index())
    rows=[]
    for name,drop in REMOVALS.items():
        a=fixed[name]; diff=a-d0.RPL_CBM; local=a.rank()-d0.RPL_CBM.rank()
        top=set(a.sort_values(ascending=False,kind='stable').head(230).index)
        rows.append(dict(diagnostic=name,removed=';'.join(drop),national_valid=83509,tracts=2299,
            Pearson=d0.RPL_CBM.corr(a),Spearman=d0.RPL_CBM.corr(a,method='spearman'),
            mean_abs_national_rank_shift=diff.abs().mean(),p90_abs_national_rank_shift=diff.abs().quantile(.9),
            max_abs_national_rank_shift=diff.abs().max(),mean_abs_local_order_shift=local.abs().mean(),
            top230_retention=len(top&top0)/230,top230_changed_population=int(d0.loc[list(top^top0),'Population'].sum()),
            changed_top230_tracts=len(top^top0),official_CDC_alternative=False,prior_unrounded_sum_max_shift=(a-before[name]).abs().max()))
    save('CBM_COMPONENT_REMOVAL_RANK_QA.csv',rows)
    f=np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz')); keys=f['keys'].copy(); labels=f['labels'].copy(); silhouettes=f['silhouette'].copy()
    pos={key:i for i,key in enumerate(keys)}
    m=np.load(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz')); mats={key:m[key].copy() for key in m.files if key!='tract_ids'}
    filenames={'fit':'P2_VS_P2_CBM_K_DIAGNOSTICS.csv','per':'PER_CLUSTER_SILHOUETTE_AND_SIZE.csv',
        'pro':'PER_CLUSTER_CBM_AND_RQ_PROFILES.csv','group':'CLUSTER_QUARTILE_HOSPITAL_GEOGRAPHY.csv',
        'con':'DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv','scale':'COHORT_STANDARDIZATION_AND_WEIGHTS.csv',
        'algebra':'INIT_DISTANCE_ALGEBRA.csv','comp':'P2_VS_P2_CBM_MEMBERSHIP_COMPARISONS.csv','trans':'COMPONENT_MEMBERSHIP_TRANSITIONS.csv'}
    base={}; new={name:[] for name in filenames}
    for name,file in filenames.items():
        df=pd.read_csv(lp(OUT/file))
        keep=~df['condition'].str.startswith('component_') if 'condition' in df else ~df.comparison.eq('component') if 'comparison' in df else ~df.alternative.str.startswith('component_')
        base[name]=df.loc[keep].copy()
    rare=d0.index.isin(frozen(s,TI+'THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').index)
    blocks=((d0.utm_x_m>=d0.utm_x_m.median()).astype(int)+2*(d0.utm_y_m>=d0.utm_y_m.median()).astype(int)).to_numpy()
    descriptors=P2[:6]+['Population','RPL_CBM','RPL_CBM_DOM1','RPL_CBM_DOM2','RPL_CBM_DOM3','E_RFLD','E_BURN','E_NEHD','EPL_RFLD','MeanTotalBurden','PolicySD','T80','BUILDVALUE']
    comparisons=[]
    for sp in ['H1','H2']:
        for name in REMOVALS:
            condition='component_'+name; d=d0.copy(); d['RPL_CBM']=fixed[name]
            x,mu,sd=matrix(d,sp); mats[sp+'__'+condition]=x; total=((x-x.mean(0))**2).sum(0)
            dist=pairwise_distances(x); np.fill_diagonal(dist,0)
            for v,a,b,w in zip(cols(sp),mu,sd,BUDGETS[sp]): new['scale'].append(dict(specification=sp,condition=condition,variable=v,mean=a,population_sd=b,squared_distance_budget=w))
            for k in [3,4,5]:
                for seed in SEEDS:
                    key=f'{sp}__{condition}__k{k}__s{seed}'; index=pos[key]; oldlab=labels[index].copy()
                    model=KMeans(n_clusters=k,random_state=seed,**PARAMS).fit(x); lab=canon(model.labels_,d)
                    sil=silhouette_samples(dist,lab,metric='precomputed'); labels[index]=lab; silhouettes[index]=sil
                    centers=np.stack([x[lab==c].mean(0) for c in range(k)]); sizes=np.bincount(lab)
                    new['fit'].append(dict(specification=sp,condition=condition,k=k,seed=seed,WCSS=np.sum((x-centers[lab])**2),
                        mean_silhouette=sil.mean(),median_silhouette=np.median(sil),negative_silhouette_fraction=(sil<0).mean(),
                        smallest_cluster_tracts=sizes.min(),largest_cluster_tracts=sizes.max(),reused_P2=False,matrix_sha256=hashlib.sha256(x.astype('<f8').tobytes()).hexdigest()))
                    comparisons.append(dict(specification=sp,condition=condition,k=k,seed=seed,unrounded_vs_exact_ties_ARI=adjusted_rand_score(oldlab,lab)))
                    between=np.zeros(x.shape[1])
                    for c in range(k):
                        mask=lab==c; part=d.loc[mask]; sv=sil[mask]; distance=(centers[c]-x.mean(0))**2; between+=mask.sum()*distance
                        new['per'].append(dict(specification=sp,condition=condition,k=k,seed=seed,cluster=c,n_tracts=int(mask.sum()),population=int(part.Population.sum()),population_share=part.Population.sum()/pop.sum(),
                            mean_silhouette=sv.mean(),median_silhouette=np.median(sv),p10_silhouette=np.quantile(sv,.1),p90_silhouette=np.quantile(sv,.9),negative_fraction=(sv<0).mean(),
                            rare34_members=int((mask&rare).sum()),rare34_capture=(mask&rare).sum()/34,rare34_precision=(mask&rare).sum()/mask.sum(),
                            Init_centroid_distance_fraction=distance[0]/distance.sum(),CBM_centroid_distance_fraction=distance[-1]/distance.sum(),
                            positive_riverine_fraction=part.E_RFLD.gt(0).mean(),burn_positive_fraction=part.E_BURN.gt(0).mean(),low_population_100_or_less=part.Population.le(100).sum(),
                            zero_housing_positive_count=part.additional_zero_housing_positive_population.sum(),largest_quadrant_fraction=np.bincount(blocks[mask],minlength=4).max()/mask.sum()))
                        if seed==42:
                            for v in descriptors:
                                a=part[v]; new['pro'].append(dict(specification=sp,condition=condition,k=k,cluster=c,variable='researcher_climate_rank' if v=='RPL_CBM' else v,
                                    n_tracts=len(part),population=int(part.Population.sum()),population_share=part.Population.sum()/pop.sum(),mean=a.mean(),median=a.median(),p10=a.quantile(.1),p90=a.quantile(.9),
                                    minimum=a.min(),maximum=a.max(),cohort_mean=d[v].mean(),cohort_median=d[v].median(),valid_count=a.notna().sum(),fitted_coordinate=v in cols(sp)))
                            new['group'].append(dict(specification=sp,condition=condition,k=k,cluster=c,n_tracts=len(part),population=int(part.Population.sum()),hospital_tracts=int(part.hospital_tract.sum()),
                                **{q+'_tracts':int(part.frozen_SOVI_quartile.eq(q).sum()) for q in ['Q1','Q2','Q3','Q4']},**{f'block{b}_tracts':int((blocks[mask]==b).sum()) for b in range(4)}))
                            new['algebra'].append(dict(specification=sp,condition=condition,k=k,cluster=c,n_tracts=len(part),rare34_members=int((mask&rare).sum()),centroid_total_squared_distance=distance.sum(),
                                Init_squared_distance=distance[0],CBM_squared_distance=distance[-1],remove_Init_fixed_budgets=distance[1:].sum(),remove_Init_RQ1_reallocated=distance[1:].sum()+.5*distance[1:3].sum()))
                    for v,t,b,w in zip(cols(sp),total,between,BUDGETS[sp]): new['con'].append(dict(specification=sp,condition=condition,k=k,seed=seed,variable=v,domain='RQ1' if v in P2[:3] else 'RQ2' if v in P2[3:5] else 'RQ3',assigned_squared_distance_budget=w,total_SS=t,between_SS=b,within_SS=t-b,between_fraction_of_all=b/between.sum()))
                    baseline=labels[pos[f'{sp}__published__k{k}__s{seed}']]; row,aligned,_=match(baseline,lab,pop)
                    new['comp'].append(dict(comparison='component',specification=sp,alternative=condition,k=k,seed=seed,**row))
                    if seed==42:
                        save('membership_'+sp+'_'+condition+f'_K{k}.csv',pd.DataFrame(dict(tract_id=d.index,baseline_cluster=baseline,alternative_cluster=lab,aligned_alternative_cluster=aligned,changed=aligned!=baseline,Population=pop)))
                        for a in range(k):
                            for b in range(k): new['trans'].append(dict(specification=sp,alternative=condition,k=k,cluster_baseline=a,cluster_aligned_alternative=b,n_tracts=int(((baseline==a)&(aligned==b)).sum()),population=int(pop[(baseline==a)&(aligned==b)].sum())))
            print('Corrected exact-decimal component fits',sp,name,flush=True)
    np.savez_compressed(lp(OUT/'REGISTERED_FIT_ARRAYS.npz'),tract_ids=d0.index.to_numpy(str),keys=keys,labels=labels,silhouette=silhouettes)
    np.savez_compressed(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'),tract_ids=d0.index.to_numpy(str),**mats)
    for name,file in filenames.items(): save(file,pd.concat([base[name],pd.DataFrame(new[name])],ignore_index=True))
    save('NUMERICAL_TIE_FIT_CORRECTION.csv',comparisons)
    save('SOURCE_HASH_VERIFICATION_TIE_CORRECTION.csv',s.records)


if __name__=='__main__':
    with threadpool_limits(limits=1): main()
