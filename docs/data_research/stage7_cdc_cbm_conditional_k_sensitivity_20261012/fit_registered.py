"""Bounded registered K-means; no recovery or physical model calls."""
from itertools import combinations
from threadpoolctl import threadpool_limits
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances, silhouette_samples
from common import *


def main():
    assert json.loads(lp(OUT/'SOURCE_RECONSTRUCTION_QA.json').read_text())['status']=='PASS'
    s=sources(); d0=frame('VERIFIED_COHORT_AND_DESCRIPTORS.csv'); pop=d0.Population.to_numpy()
    ids=frozen(s,TI+'THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').index
    rare=d0.index.isin(ids); assert rare.sum()==34
    blocks=((d0.utm_x_m>=d0.utm_x_m.median()).astype(int)+2*(d0.utm_y_m>=d0.utm_y_m.median()).astype(int)).to_numpy()
    old=np.load(s.source(MP+'REGISTERED_FIT_ARRAYS.npz',AUTH)); oi={v:i for i,v in enumerate(old['keys'])}
    om=np.load(s.source(MP+'VERIFIED_WEIGHTED_MATRICES.npz',AUTH))
    osp=np.load(s.source(MP+'SPATIAL_REFIT_LABELS.npz',AUTH)); osi={v:i for i,v in enumerate(osp['keys'])}
    for z in [old,om,osp]: np.testing.assert_array_equal(z['tract_ids'],d0.index)
    ranks=frame('NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv')
    pq=frozen(s,MP+'MULTIPOLICY_RQ2_TRACT_VALUES.csv')
    fitrows,clrows,profiles,groups,contrib,scalers,comparisons,transitions,stability,seedrows,algebra=[],[],[],[],[],[],[],[],[],[],[]
    labs,sils,matrices,preds={},{},{},{}
    descriptors=P2[:6]+['Population','RPL_CBM','RPL_CBM_DOM1','RPL_CBM_DOM2','RPL_CBM_DOM3','E_RFLD','E_BURN','E_NEHD',
                 'EPL_RFLD','MeanTotalBurden','PolicySD','T80','BUILDVALUE']

    def fitting(spec,condition,d,ks,seeds,reference=None):
        x,mu,sd=matrix(d,spec,reference); cond=spec+'__'+condition
        matrices[cond]=x
        for v,m,t,w in zip(cols(spec),mu,sd,BUDGETS[spec]):
            scalers.append(dict(specification=spec,condition=condition,variable=v,mean=m,population_sd=t,squared_distance_budget=w))
        dist=pairwise_distances(x); np.fill_diagonal(dist,0)
        total=((x-x.mean(0))**2).sum(0)
        oldcondition='main5__cohort' if condition=='published' else condition.replace('policy_','')
        if spec=='P2': np.testing.assert_array_equal(x,om['P2__'+oldcondition])
        for k in ks:
            for seed in seeds:
                key=f'{cond}__k{k}__s{seed}'
                if spec=='P2':
                    pos=oi[f'P2__{oldcondition}__k{k}__s{seed}']; lab=old['labels'][pos].copy()
                    sil=silhouette_samples(dist,lab,metric='precomputed') if k>1 else np.full(len(d),np.nan)
                    np.testing.assert_allclose(sil,old['silhouette'][pos],atol=1e-12,rtol=0,equal_nan=True)
                else:
                    model=KMeans(n_clusters=k,random_state=seed,**PARAMS).fit(x)
                    lab=canon(model.labels_,d)
                    sil=silhouette_samples(dist,lab,metric='precomputed') if k>1 else np.full(len(d),np.nan)
                labs[key]=lab; sils[key]=sil
                centers=np.stack([x[lab==c].mean(0) for c in range(k)])
                inertia=np.sum((x-centers[lab])**2)
                sizes=np.bincount(lab,minlength=k)
                fitrows.append(dict(specification=spec,condition=condition,k=k,seed=seed,WCSS=inertia,
                    mean_silhouette=sil.mean() if k>1 else np.nan,median_silhouette=np.median(sil) if k>1 else np.nan,
                    negative_silhouette_fraction=(sil<0).mean() if k>1 else np.nan,
                    smallest_cluster_tracts=sizes.min(),largest_cluster_tracts=sizes.max(),reused_P2=(spec=='P2'),
                    matrix_sha256=hashlib.sha256(x.astype('<f8').tobytes()).hexdigest()))
                between=np.zeros(len(cols(spec)))
                for c in range(k):
                    mask=lab==c; part=d.loc[mask]; sv=sil[mask]
                    distance=(centers[c]-x.mean(0))**2; bss=mask.sum()*distance; between+=bss
                    clrows.append(dict(specification=spec,condition=condition,k=k,seed=seed,cluster=c,n_tracts=int(mask.sum()),
                        population=int(part.Population.sum()),population_share=part.Population.sum()/pop.sum(),
                        mean_silhouette=sv.mean() if k>1 else np.nan,median_silhouette=np.median(sv) if k>1 else np.nan,
                        p10_silhouette=np.quantile(sv,.1) if k>1 else np.nan,p90_silhouette=np.quantile(sv,.9) if k>1 else np.nan,
                        negative_fraction=(sv<0).mean() if k>1 else np.nan,rare34_members=int((mask&rare).sum()),
                        rare34_capture=(mask&rare).sum()/34,rare34_precision=(mask&rare).sum()/mask.sum(),
                        Init_centroid_distance_fraction=distance[0]/distance.sum() if distance.sum()>0 else np.nan,
                        CBM_centroid_distance_fraction=distance[-1]/distance.sum() if spec!='P2' and distance.sum()>0 else 0,
                        positive_riverine_fraction=part.E_RFLD.gt(0).mean(),burn_positive_fraction=part.E_BURN.gt(0).mean(),
                        low_population_100_or_less=part.Population.le(100).sum(),
                        zero_housing_positive_count=part.additional_zero_housing_positive_population.sum(),
                        largest_quadrant_fraction=np.bincount(blocks[mask],minlength=4).max()/mask.sum()))
                    if seed==42 and k>1 and (condition=='published' or condition.startswith('component_')):
                        for v in descriptors:
                            a=part[v]
                            profiles.append(dict(specification=spec,condition=condition,k=k,cluster=c,
                                variable='researcher_climate_rank' if v=='RPL_CBM' and condition.startswith('component_') else v,
                                n_tracts=len(part),population=int(part.Population.sum()),population_share=part.Population.sum()/pop.sum(),
                                mean=a.mean(),median=a.median(),p10=a.quantile(.1),p90=a.quantile(.9),minimum=a.min(),maximum=a.max(),
                                cohort_mean=d[v].mean(),cohort_median=d[v].median(),valid_count=a.notna().sum(),fitted_coordinate=v in cols(spec)))
                        groups.append(dict(specification=spec,condition=condition,k=k,cluster=c,n_tracts=len(part),
                            population=int(part.Population.sum()),hospital_tracts=int(part.hospital_tract.sum()),
                            **{q+'_tracts':int(part.frozen_SOVI_quartile.eq(q).sum()) for q in ['Q1','Q2','Q3','Q4']},
                            **{f'block{b}_tracts':int((blocks[mask]==b).sum()) for b in range(4)}))
                        algebra.append(dict(specification=spec,condition=condition,k=k,cluster=c,n_tracts=len(part),
                            rare34_members=int((mask&rare).sum()),centroid_total_squared_distance=distance.sum(),
                            Init_squared_distance=distance[0],CBM_squared_distance=distance[-1] if spec!='P2' else 0,
                            remove_Init_fixed_budgets=distance[1:].sum(),remove_Init_RQ1_reallocated=distance[1:].sum()+.5*distance[1:3].sum()))
                for v,t,b,w in zip(cols(spec),total,between,BUDGETS[spec]):
                    contrib.append(dict(specification=spec,condition=condition,k=k,seed=seed,variable=v,
                        domain='RQ1' if v in P2[:3] else 'RQ2' if v in P2[3:5] else 'RQ3',
                        assigned_squared_distance_budget=w,total_SS=t,between_SS=b,within_SS=t-b,
                        between_fraction_of_all=b/between.sum() if between.sum()>0 else np.nan))
        print('Completed',cond,'K='+str(ks),flush=True)

    for spec in BUDGETS: fitting(spec,'published',d0,[1,*KS],SEEDS)
    fits=pd.DataFrame(fitrows); elbow=[]; supported=set([3,4,5])
    for spec in BUDGETS:
        m=fits.loc[fits.specification.eq(spec)].groupby('k').WCSS.mean()
        for endpoint in [6,7,8]:
            norm=(m[1]-m.loc[:endpoint])/(m[1]-m[endpoint]); gap=norm-(norm.index-1)/(endpoint-1)
            candidate=int(gap.idxmax())
            if spec!='P2': supported.add(candidate)
            for k in norm.index: elbow.append(dict(specification=spec,endpoint=endpoint,k=k,normalized_reduction=norm[k],chord_gap=gap[k],bend_candidate=candidate))
        silmax=int(fits.loc[fits.specification.eq(spec)&fits.k.gt(1)].groupby('k').mean_silhouette.mean().idxmax())
        if spec!='P2': supported.add(silmax)
    dump('BOUNDED_COMPONENT_K_REGISTRATION.json',dict(label=WARN,rule='K3/4/5 plus main H1/H2 silhouette maxima and K1-6/7/8 endpoint bends',
        component_K=sorted(supported),main_diagnostics_sha256=hashlib.sha256(fits.to_csv(index=False).encode()).hexdigest(),
        seeds=SEEDS,no_unrestricted_component_K_search=True))
    for spec in ['H1','H2']:
        for name in REMOVALS:
            d=d0.copy(); d['RPL_CBM']=ranks[name]
            fitting(spec,'component_'+name,d,sorted(supported),SEEDS)
    sets=list(pq.policy_set.unique())
    for spec in BUDGETS:
        for name in sets:
            if name=='main5': continue
            d=d0.copy(); v=pq.loc[pq.policy_set.eq(name)].reindex(d.index)
            for col in ['B_Unconstrained','MeanDelta','MeanTotalBurden','PolicySD']: d[col]=v[col]
            for scaling in ['cohort','fixed_main5']:
                fitting(spec,f'policy_{name}__{scaling}',d,KS,[42],reference=d0 if scaling=='fixed_main5' else None)
    for spec in BUDGETS:
        raw=d0[cols(spec)].to_numpy()
        for k in KS:
            base=labs[f'{spec}__published__k{k}__s42']
            for block in range(4):
                train=blocks!=block
                xx=(raw-raw[train].mean(0))/raw[train].std(0)*np.sqrt(BUDGETS[spec])
                if spec=='P2': pred=osp['labels'][osi[f'P2__main5__cohort__k{k}__block{block}']].copy()
                else:
                    model=KMeans(n_clusters=k,random_state=42,**PARAMS).fit(xx[train]); pred=model.predict(xx)
                row,aligned,_=match(base,pred,pop)
                preds[f'{spec}__k{k}__block{block}']=aligned
                rc=np.bincount(aligned[rare],minlength=k).argmax()
                stability.append(dict(specification=spec,test='geographic',condition=f'block{block}',scaling='training_cohort',k=k,seed=42,
                    held_out_ARI=adjusted_rand_score(base[~train],pred[~train]),held_out_tracts=int((~train).sum()),
                    rare34_capture=(aligned[rare]==rc).mean(),rare_cluster_size=int((aligned==rc).sum()),**row))
        for k in KS:
            for a,b in combinations(SEEDS,2):
                seedrows.append(dict(specification=spec,k=k,seed_a=a,seed_b=b,ARI=adjusted_rand_score(labs[f'{spec}__published__k{k}__s{a}'],labs[f'{spec}__published__k{k}__s{b}'])))

    for key,lab in labs.items():
        spec,tail=key.split('__',1)
        condition=tail.rsplit('__k',1)[0]; k=int(key.rsplit('__k',1)[1].split('__')[0]); seed=int(key.rsplit('__s',1)[1])
        if condition=='published': continue
        base=labs[f'{spec}__published__k{k}__s{seed}']; row,aligned,tab=match(base,lab,pop)
        comparisons.append(dict(comparison='component' if condition.startswith('component') else 'policy',specification=spec,
            alternative=condition,k=k,seed=seed,**row))
        if condition.startswith('policy'):
            stability.append(dict(specification=spec,test='policy_set',condition=condition,scaling=condition.split('__')[-1],k=k,seed=seed,**row))
        if seed==42 and condition.startswith('component'):
            save('membership_'+spec+'_'+condition+f'_K{k}.csv',pd.DataFrame(dict(tract_id=d0.index,baseline_cluster=base,alternative_cluster=lab,aligned_alternative_cluster=aligned,changed=aligned!=base,Population=pop)))
            for c in range(k):
                for b in range(k):
                    transitions.append(dict(specification=spec,alternative=condition,k=k,cluster_baseline=c,cluster_aligned_alternative=b,
                        n_tracts=int(((base==c)&(aligned==b)).sum()),population=int(pop[(base==c)&(aligned==b)].sum())))
    for k in KS:
        for seed in SEEDS:
            for a,b in [('P2','H1'),('P2','H2'),('H1','H2')]:
                row,aligned,tab=match(labs[f'{a}__published__k{k}__s{seed}'],labs[f'{b}__published__k{k}__s{seed}'],pop)
                comparisons.append(dict(comparison='feature_specification',specification=a,alternative=b,k=k,seed=seed,**row))
                if seed==42:
                    base=labs[f'{a}__published__k{k}__s{seed}']
                    save(f'membership_{a}_vs_{b}_K{k}.csv',pd.DataFrame(dict(tract_id=d0.index,baseline_cluster=base,alternative_cluster=labs[f'{b}__published__k{k}__s{seed}'],aligned_alternative_cluster=aligned,changed=aligned!=base,Population=pop)))
    # Fixed-budget algebra isolates coordinate addition and budget redistribution without extra fitted models.
    z=(d0[P2+['RPL_CBM']].to_numpy()-d0[P2+['RPL_CBM']].mean().to_numpy())/d0[P2+['RPL_CBM']].std(ddof=0).to_numpy()
    covariance=z.T@z/len(z); ar=[]
    for spec in ['H1','H2']:
        for k in [3,4,5]:
            lab=labs[f'{spec}__published__k{k}__s42']; means=np.stack([z[lab==c].mean(0) for c in range(k)])
            between=np.sum(np.bincount(lab)[:,None]*means**2,axis=0)
            w=np.array(BUDGETS[spec]); oldw=np.array(BUDGETS['P2'])
            ar.append(dict(specification=spec,k=k,partition='Fixed new partition, no refit',
                old_seven_budget_BSS=np.dot(between[:7],oldw),climate_added_BSS=between[7]*w[7],
                reallocation_SOVI_BSS=between[5]*(w[5]-oldw[5]),reallocation_population_BSS=between[6]*(w[6]-oldw[6]),
                new_total_BSS=np.dot(between,w)))
    ablations=[]
    for spec in ['H1','H2']:
        for k in [3,4,5]:
            x,_,_=matrix(d0,spec); x=x[:,1:]; x[:,:2]*=np.sqrt(1.5)
            mod=KMeans(n_clusters=k,random_state=42,**PARAMS).fit(x); lab=canon(mod.labels_,d0)
            base=labs[f'{spec}__published__k{k}__s42']; row,_,_=match(base,lab,pop)
            preds[f'{spec}__minus_Init__k{k}']=lab
            rc=np.bincount(lab[rare],minlength=k).argmax()
            ablations.append(dict(specification=spec,k=k,seed=42,rare34_capture=(lab[rare]==rc).mean(),rare_class_size=int((lab==rc).sum()),
                notice='Removing initial construct ALSO raises remaining RQ1 budgets 1/9 to 1/6',**row))
    for name,data in [('P2_VS_P2_CBM_K_DIAGNOSTICS.csv',fitrows),('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv',clrows),
        ('PER_CLUSTER_CBM_AND_RQ_PROFILES.csv',profiles),('CLUSTER_QUARTILE_HOSPITAL_GEOGRAPHY.csv',groups),
        ('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv',contrib),('COHORT_STANDARDIZATION_AND_WEIGHTS.csv',scalers),
        ('P2_VS_P2_CBM_MEMBERSHIP_COMPARISONS.csv',comparisons),('POLICY_SET_AND_GEOGRAPHIC_STABILITY.csv',stability),
        ('SEED_STABILITY.csv',seedrows),('ELBOW_ENDPOINT_DIAGNOSTICS.csv',elbow),('COMPONENT_MEMBERSHIP_TRANSITIONS.csv',transitions),
        ('RQ3_ADDITION_VS_REALLOCATION_ALGEBRA.csv',ar),('INIT_DISTANCE_ALGEBRA.csv',algebra),('INIT_ABLATION_RESULTS.csv',ablations)]: save(name,data)
    np.savez_compressed(lp(OUT/'REGISTERED_FIT_ARRAYS.npz'),tract_ids=d0.index.to_numpy(str),keys=np.array(list(labs)),labels=np.stack(list(labs.values())),silhouette=np.stack(list(sils.values())))
    np.savez_compressed(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'),tract_ids=d0.index.to_numpy(str),**matrices)
    np.savez_compressed(lp(OUT/'PERTURBATION_LABELS.npz'),tract_ids=d0.index.to_numpy(str),keys=np.array(list(preds)),labels=np.stack(list(preds.values())))
    save('SOURCE_HASH_VERIFICATION_FITS.csv',s.records)
    dump('REGISTERED_FIT_COMPLETION.json',dict(label=WARN,status='PASS',saved_fits=len(labs),new_physical_runs=0,
        P2_reused=sum(r['reused_P2'] for r in fitrows),component_K=sorted(supported),spatial_predictions=84,formal_promotion=False))


if __name__=='__main__':
    with threadpool_limits(limits=1): main()
