"""Predeclared exploratory fits only; frozen service data are never regenerated."""
from itertools import combinations
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, pairwise_distances, silhouette_samples
from common import *


def matching(a,b,pop):
    k=max(a.max(),b.max())+1
    table=np.zeros((k,k),int)
    np.add.at(table,(a,b),1)
    i,j=linear_sum_assignment(-table)
    remap=dict(zip(j,i))
    aligned=np.array([remap[v] for v in b])
    changed=aligned!=a
    return dict(ARI=adjusted_rand_score(a,b),aligned_changed_tracts=int(changed.sum()),
        aligned_changed_population=int(pop[changed].sum()),aligned_changed_population_share=pop[changed].sum()/pop.sum()),table,remap


def main():
    assert json.loads(lp(OUT/'INFORMATION_AUDIT_COMPLETION.json').read_text())['status']=='PASS'
    s=sources(); d0=dataset(); pop=d0.Population.to_numpy()
    rare_ids=frozen(s,INTERPRETATION+'THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').index
    rare=d0.index.isin(rare_ids); assert rare.sum()==34
    blocks=((d0.utm_x_m>=d0.utm_x_m.median()).astype(int)+2*(d0.utm_y_m>=d0.utm_y_m.median()).astype(int)).to_numpy()
    old=np.load(s.source(POLICY_AUDIT+'REGISTERED_FIT_ARRAYS.npz',AUTH))
    np.testing.assert_array_equal(old['tract_ids'],d0.index)
    oldkeys={v:i for i,v in enumerate(old['keys'])}
    oldmat=np.load(s.source(POLICY_AUDIT+'VERIFIED_WEIGHTED_MATRICES.npz',AUTH))
    labels,sils,matrices,scalers,dsets,spatial_labels={},{},{},[],{},{}
    fits,clusters,profiles,groups,contrib,seedrows,spatial,comparisons,transitions,algebra=[],[],[],[],[],[],[],[],[],[]
    conditions=[('A','main5','cohort')]+[(sp,name,'cohort') for sp in ['P2','P3'] for name in SETS]
    conditions += [(sp,name,'fixed_main5') for sp in ['P2','P3'] for name in SETS if name!='main5']
    conditions += [(sp+'-minus-Init','main5','cohort') for sp in ['P2','P3']]
    descriptors=list(dict.fromkeys(RQ1+['B_Unconstrained','MeanDelta','PolicySD','MeanTotalBurden','B_480_hr','Delta_B_logistics','SOVI_SCORE','Population','T80','BUILDVALUE']))
    for spec,name,scaling in conditions:
        d=dataset(name); np.testing.assert_array_equal(d.index,d0.index)
        assert np.array_equal(d[RQ1+RQ3],d0[RQ1+RQ3])
        dsets[(spec,name,scaling)]=d
        x,mu,sd=matrix(d,spec,d0 if scaling=='fixed_main5' else None)
        cond=f'{spec}__{name}__{scaling}'
        matrices[cond]=x
        for v,m,t,w in zip(columns(spec),mu,sd,weights(spec)):
            scalers.append(dict(specification=spec,policy_set=name,scaling=scaling,variable=v,mean=m,population_sd=t,squared_distance_budget=w,coordinate_multiplier=np.sqrt(w)))
        dist=pairwise_distances(x); np.fill_diagonal(dist,0)
        these_ks=[1,3,4,5] if spec.endswith('-minus-Init') else KS if scaling=='fixed_main5' else [1,*KS]
        seeds=[42] if scaling=='fixed_main5' else SEEDS
        if spec=='A': np.testing.assert_allclose(x,oldmat['impact-first__A__policy_cohort'],rtol=0,atol=1e-13)
        total=((x-x.mean(0))**2).sum(0)
        for k in these_ks:
            for seed in seeds:
                kk=key(spec,name,scaling,k,seed)
                if spec=='A':
                    oi=oldkeys[f'impact-first__A__policy_cohort__k{k}__s{seed}']
                    lab=old['labels'][oi].copy(); sil=old['silhouette'][oi].copy()
                    if k>1: np.testing.assert_allclose(sil,silhouette_samples(dist,lab,metric='precomputed'),rtol=0,atol=1e-12)
                else:
                    model=KMeans(n_clusters=k,random_state=seed,**PARAMS).fit(x)
                    lab=canon(model.labels_,d,spec)
                    sil=silhouette_samples(dist,lab,metric='precomputed') if k>1 else np.full(len(d),np.nan)
                labels[kk]=lab; sils[kk]=sil
                centers=np.stack([x[lab==c].mean(0) for c in range(k)])
                wcss=((x-centers[lab])**2).sum()
                sizes=np.bincount(lab,minlength=k)
                fits.append(dict(specification=spec,policy_set=name,scaling=scaling,k=k,seed=seed,WCSS=wcss,
                    mean_silhouette=np.mean(sil) if k>1 else np.nan,median_silhouette=np.median(sil) if k>1 else np.nan,
                    negative_silhouette_fraction=(sil<0).mean() if k>1 else np.nan,min_cluster_tracts=sizes.min(),max_cluster_tracts=sizes.max(),
                    matrix_sha256=hashlib.sha256(x.astype('<f8').tobytes()).hexdigest(),saved_authoritative_A_reused=(spec=='A')))
                between=np.zeros(x.shape[1])
                for c in range(k):
                    selected=lab==c; part=d.loc[selected]; sv=sil[selected]
                    distance=(centers[c]-x.mean(0))**2; bss=selected.sum()*distance; between+=bss
                    init_share=distance[0]/distance.sum() if 'Init_Supply' in columns(spec) and distance.sum()>0 else np.nan
                    clusters.append(dict(specification=spec,policy_set=name,scaling=scaling,k=k,seed=seed,diagnostic_cluster=c,
                        n_tracts=len(part),population=part.Population.sum(),population_share=part.Population.sum()/pop.sum(),
                        mean_silhouette=sv.mean() if k>1 else np.nan,median_silhouette=np.median(sv) if k>1 else np.nan,
                        p10_silhouette=np.quantile(sv,.1) if k>1 else np.nan,p90_silhouette=np.quantile(sv,.9) if k>1 else np.nan,
                        negative_fraction=(sv<0).mean() if k>1 else np.nan,rare_34_members=(selected&rare).sum(),
                        rare_34_precision=(selected&rare).sum()/selected.sum(),rare_34_capture=(selected&rare).sum()/34,
                        centroid_Init_distance_share=init_share,centroid_PolicySD_distance_share=distance[columns(spec).index('PolicySD')]/distance.sum() if 'PolicySD' in columns(spec) and distance.sum()>0 else np.nan,
                        Q4_fraction=part.frozen_SOVI_quartile.eq('Q4').mean(),zero_housing_positive_tracts=part.additional_zero_housing_positive_population.sum(),
                        largest_quadrant_share=np.bincount(blocks[selected],minlength=4).max()/selected.sum()))
                    if seed==42 and k>1 and scaling=='cohort':
                        for v in descriptors:
                            a=part[v]
                            profiles.append(dict(specification=spec,policy_set=name,k=k,diagnostic_cluster=c,variable=v,
                                fitted_coordinate=(v in columns(spec)),n_tracts=len(part),population=part.Population.sum(),population_share=part.Population.sum()/pop.sum(),
                                mean=a.mean(),median=a.median(),p10=a.quantile(.1),p25=a.quantile(.25),p75=a.quantile(.75),p90=a.quantile(.9),minimum=a.min(),maximum=a.max(),
                                cohort_mean=d[v].mean(),cohort_median=d[v].median(),valid_count=a.notna().sum()))
                        groups.append(dict(specification=spec,policy_set=name,k=k,diagnostic_cluster=c,n_tracts=len(part),population=part.Population.sum(),
                            population_share=part.Population.sum()/pop.sum(),median_population=part.Population.median(),hospital_tracts=part.hospital_tract.sum(),
                            T80_unreached_tracts=part.T80_unreached.sum(),zero_housing_positive_tracts=part.additional_zero_housing_positive_population.sum(),
                            mean_lat=part.INTPTLAT.mean(),mean_lon=part.INTPTLON.mean(),
                            **{q+'_tracts':int(part.frozen_SOVI_quartile.eq(q).sum()) for q in ['Q1','Q2','Q3','Q4']},
                            **{f'block{b}_tracts':int((blocks[selected]==b).sum()) for b in range(4)}))
                        if 'Init_Supply' in columns(spec):
                            remaining=distance[1:].sum()
                            algebra.append(dict(specification=spec,policy_set=name,k=k,diagnostic_cluster=c,n_tracts=len(part),rare_members=(selected&rare).sum(),
                                centroid_squared_distance=distance.sum(),Init_squared_distance=distance[0],
                                omit_Init_fixed_other_budgets=remaining,omit_Init_RQ1_redistributed=remaining+.5*distance[1:3].sum()))
                for v,t,b in zip(columns(spec),total,between):
                    contrib.append(dict(specification=spec,policy_set=name,scaling=scaling,k=k,seed=seed,variable=v,
                        domain='RQ1' if v in RQ1 else 'RQ3' if v in RQ3 else 'RQ2',total_SS=t,between_SS=b,within_SS=t-b,
                        between_fraction_of_all=b/between.sum() if between.sum()>0 else np.nan))
        if scaling=='cohort':
            for k in [3,4,5] if spec.endswith('-minus-Init') else KS:
                for sa,sb in combinations(SEEDS,2):
                    seedrows.append(dict(specification=spec,policy_set=name,k=k,seed_a=sa,seed_b=sb,
                        ARI=adjusted_rand_score(labels[key(spec,name,scaling,k,sa)],labels[key(spec,name,scaling,k,sb)])))
                if not spec.endswith('-minus-Init'):
                    base=labels[key(spec,name,scaling,k,42)]
                    raw=d[columns(spec)].to_numpy(float)
                    for block in range(4):
                        train=blocks!=block
                        xx=(raw-raw[train].mean(0))/raw[train].std(0)*np.sqrt(weights(spec))
                        model=KMeans(n_clusters=k,random_state=42,**PARAMS).fit(xx[train])
                        pred=model.predict(xx)
                        _,_,remap=matching(base,pred,pop)
                        pred=np.array([remap[v] for v in pred],dtype=np.int16)
                        spatial_labels[f'{cond}__k{k}__block{block}']=pred
                        rc=np.bincount(pred[rare],minlength=k).argmax()
                        spatial.append(dict(specification=spec,policy_set=name,k=k,left_out_block=block,
                            full_ARI=adjusted_rand_score(base,pred),held_out_ARI=adjusted_rand_score(base[~train],pred[~train]),
                            training_tracts=train.sum(),held_out_tracts=(~train).sum(),rare_capture=(pred[rare]==rc).mean(),
                            rare_class_size=(pred==rc).sum(),rare_precision=(pred[rare]==rc).sum()/(pred==rc).sum()))
        print('registered fits completed',spec,name,scaling,flush=True)
    for sp in ['P2','P3']:
        for k in KS:
            for name in SETS:
                if name=='main5': continue
                for scaling in ['cohort','fixed_main5']:
                    for seed in SEEDS if scaling=='cohort' else [42]:
                        a=labels[key(sp,'main5','cohort',k,seed)]; b=labels[key(sp,name,scaling,k,seed)]
                        row,tab,remap=matching(a,b,pop)
                        comparisons.append(dict(comparison='policy_set',specification=sp,alternative_specification=sp,policy_set=name,scaling=scaling,k=k,seed=seed,**row))
                        if seed==42:
                            for ca in range(k):
                                for cb in range(k):
                                    transitions.append(dict(comparison='policy_set',specification=sp,alternative_specification=sp,policy_set=name,scaling=scaling,k=k,
                                        cluster_main=ca,cluster_alternative=cb,aligned_alternative_cluster=remap[cb],n_tracts=tab[ca,cb],
                                        population=pop[(a==ca)&(b==cb)].sum()))
            for seed in SEEDS:
                a=labels[key(sp,'main5','cohort',k,seed)]; b=labels[key('A','main5','cohort',k,seed)]
                row,_,_=matching(b,a,pop)
                comparisons.append(dict(comparison='A_vs_multi',specification='A',alternative_specification=sp,policy_set='main5',scaling='cohort',k=k,seed=seed,**row))
        for k in [3,4,5]:
            for seed in SEEDS:
                a=labels[key(sp,'main5','cohort',k,seed)]; b=labels[key(sp+'-minus-Init','main5','cohort',k,seed)]
                row,_,_=matching(a,b,pop)
                comparisons.append(dict(comparison='Init_ablation',specification=sp,alternative_specification=sp+'-minus-Init',policy_set='main5',scaling='cohort',k=k,seed=seed,**row))
    for k in KS:
        for seed in SEEDS:
            a=labels[key('P2','main5','cohort',k,seed)]; b=labels[key('P3','main5','cohort',k,seed)]
            row,tab,remap=matching(a,b,pop)
            comparisons.append(dict(comparison='P2_vs_P3',specification='P2',alternative_specification='P3',policy_set='main5',scaling='cohort',k=k,seed=seed,**row))
            if seed==42:
                for ca in range(k):
                    for cb in range(k):
                        transitions.append(dict(comparison='P2_vs_P3',specification='P2',alternative_specification='P3',policy_set='main5',scaling='cohort',k=k,
                            cluster_main=ca,cluster_alternative=cb,aligned_alternative_cluster=remap[cb],n_tracts=tab[ca,cb],population=pop[(a==ca)&(b==cb)].sum()))
    for fn,rows in [('A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv',fits),('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv',clusters),
        ('CLUSTER_ORIGINAL_UNIT_PROFILES.csv',profiles),('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv',groups),
        ('COHORT_STANDARDIZATION_AND_WEIGHTS.csv',scalers),('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv',contrib),
        ('SEED_STABILITY.csv',seedrows),('SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv',spatial),
        ('POLICY_SET_CLUSTER_STABILITY.csv',comparisons),('MATCHED_MEMBERSHIP_TRANSITIONS.csv',transitions),
        ('INIT_ALGEBRAIC_DISTANCE_DIAGNOSTICS.csv',algebra)]: save(fn,rows)
    fit=pd.DataFrame(fits); elbow=[]
    for (sp,name,scaling),part in fit.query("scaling=='cohort'").groupby(['specification','policy_set','scaling']):
        if sp.endswith('-minus-Init'): continue
        means=part.groupby('k').WCSS.mean(); norm=(means[1]-means)/(means[1]-means[8]); gap=norm-(means.index-1)/7
        for k in means.index:
            selected=part.loc[part.k.eq(k)]
            elbow.append(dict(specification=sp,policy_set=name,k=k,mean_WCSS=means[k],min_WCSS=selected.WCSS.min(),max_WCSS=selected.WCSS.max(),
                relative_reduction=(means[k-1]-means[k])/means[k-1] if k>1 else np.nan,fraction_K1_removed=1-means[k]/means[1],
                normalized_endpoint_reduction=norm[k],chord_gap=gap[k],endpoint_chord_candidate=int(gap.idxmax()),
                mean_silhouette=selected.mean_silhouette.mean(),median_seed_silhouette=selected.mean_silhouette.median(),
                min_seed_silhouette=selected.mean_silhouette.min(),max_seed_silhouette=selected.mean_silhouette.max()))
    save('ELBOW_AND_SILHOUETTE_COMPARISON.csv',elbow)
    np.savez_compressed(lp(OUT/'REGISTERED_FIT_ARRAYS.npz'),tract_ids=d0.index.to_numpy(str),keys=np.array(list(labels)),labels=np.stack(list(labels.values())),silhouette=np.stack(list(sils.values())))
    np.savez_compressed(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'),tract_ids=d0.index.to_numpy(str),**matrices)
    np.savez_compressed(lp(OUT/'SPATIAL_REFIT_LABELS.npz'),tract_ids=d0.index.to_numpy(str),keys=np.array(list(spatial_labels)),labels=np.stack(list(spatial_labels.values())))
    save('SOURCE_HASH_VERIFICATION_FITS.csv',s.records)
    dump('REGISTERED_FIT_COMPLETION.json',dict(status='PASS',individual_fits=len(labels),spatial_refits=len(spatial),
        authoritative_A_reused=40,full_cohort_silhouette=True,physical_models_rerun=False,
        registration_sha256=sha(OUT/'REGISTERED_ANALYSIS.json'),feature_specification_sha256=sha(OUT/'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json')))


if __name__=='__main__': main()
