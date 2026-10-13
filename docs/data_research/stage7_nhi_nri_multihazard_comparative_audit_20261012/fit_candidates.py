"""Registered conditional K-means only; no physical or restoration simulation."""
from itertools import combinations
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_samples
from threadpoolctl import threadpool_limits
from common import *


def alignment(a,b,pop):
    k=max(a.max(),b.max())+1;table=np.zeros((k,k),int);np.add.at(table,(a,b),1)
    row,col=linear_sum_assignment(-table);mapping=dict(zip(col,row));aligned=np.array([mapping[v] for v in b]);changed=a!=aligned
    return dict(ARI=adjusted_rand_score(a,b),reassigned_tracts=int(changed.sum()),
        reassigned_population=int(pop[changed].sum()),reassigned_population_share=pop[changed].sum()/pop.sum())


def main():
    gate=frame('EIGHTH_COORDINATE_COHORT_ADMISSION.csv').set_index('candidate')
    assert gate.loc['FEMA_NCV14_CA_v119','fit_authorized_by_gate']
    assert not gate.loc['Columbia_NHI14_dominant_land_source','fit_authorized_by_gate']
    d=frame('FROZEN_COHORT_AND_COMPARATORS.csv','tract_id');v=frame('FEMA_NCV_CANDIDATE_VECTORS.csv','tract_id').reindex(d.index)
    hazard=v.FEMA_NCV14_CA_v119.to_numpy()
    oldmat=np.load(lp(OUT/'FROZEN_COMPARATOR_WEIGHTED_MATRICES.npz'))
    old=np.load(lp(OUT/'FROZEN_COMPARATOR_FIT_ARRAYS.npz'));oi={k:i for i,k in enumerate(old['keys'])}
    s=reader();rare=read(s,'docs/data_research/stage7_rq_typology_interpretation_20261012/THIRTYFOUR_TRACT_NETWORK_SUMMARY.csv','tract_id')
    assert len(rare)==34 and set(rare.index).issubset(d.index)
    raremask=d.index.isin(rare.index);pop=d.Population.to_numpy();burden=d.MeanTotalBurden.to_numpy()
    prototype=oldmat['H2__published'].copy()
    prototype[:,-1]=(hazard-hazard.mean())/hazard.std()*np.sqrt(1/12)
    np.testing.assert_allclose(prototype,weighted(d,hazard),atol=1e-14,rtol=0)
    np.testing.assert_array_equal(prototype[:,:7],oldmat['H2__published'][:,:7])
    matrices={'main':prototype};keys=[];labels=[];silhouettes=[];centers={};records=[];profiles=[];clusters=[];contributions=[]
    comparisons=[];stability=[];transitions=[]
    def fit(condition,x,k,seed,train=None):
        if train is None:train=np.ones(len(d),bool)
        model=KMeans(n_clusters=k,random_state=seed,**PARAMS).fit(x[train])
        lab=model.predict(x)
        order=sorted(range(k),key=lambda c:(burden[lab==c].mean(),c))
        remap={old:new for new,old in enumerate(order)}
        lab=np.array([remap[c] for c in lab],dtype='int16');center=model.cluster_centers_[order]
        key=f'NCV14__{condition}__k{k}__s{seed}'
        sil=silhouette_samples(x,lab) if k>1 else np.full(len(d),np.nan)
        inertia=np.sum((x[train]-center[lab[train]])**2)
        assert abs(inertia-model.inertia_)<1e-8
        final=np.stack([x[train& (lab==c)].mean(0) for c in range(k)])
        centroid_WCSS=np.sum((x[train]-final[lab[train]])**2)
        keys.append(key);labels.append(lab);silhouettes.append(sil);centers[key]=center
        records.append(dict(model='H2-FEMA_NCV14_CA_v119',condition=condition,k=k,seed=seed,train_count=int(train.sum()),
            WCSS=model.inertia_,final_membership_centroid_WCSS=centroid_WCSS,
            mean_silhouette=np.nanmean(sil) if k>1 else np.nan,median_silhouette=np.nanmedian(sil) if k>1 else np.nan,
            negative_silhouette_fraction=np.mean(sil<0) if k>1 else np.nan,n_iter=model.n_iter_,
            matrix_sha256=hashlib.sha256(x.tobytes()).hexdigest(),class_ID_definition='Model-specific ascending mean frozen main5 total burden'))
        if condition=='main':
            rawcols=P2+['FEMA_NCV14_CA_v119'];original=d[P2].copy();original['FEMA_NCV14_CA_v119']=hazard
            descriptors=original.copy();descriptors['Population']=pop;descriptors['CDC_RPL_CBM']=d.RPL_CBM;descriptors['T80_Impact_reference']=d.T80
            for c in range(k):
                mask=lab==c
                clusters.append(dict(model='H2-FEMA_NCV14_CA_v119',condition=condition,k=k,seed=seed,cluster=c,n_tracts=int(mask.sum()),
                    population=int(pop[mask].sum()),population_share=pop[mask].sum()/pop.sum(),
                    mean_silhouette=np.nanmean(sil[mask]) if k>1 else np.nan,median_silhouette=np.nanmedian(sil[mask]) if k>1 else np.nan,
                    negative_fraction=np.mean(sil[mask]<0) if k>1 else np.nan,p10_silhouette=np.nanquantile(sil[mask],.1) if k>1 else np.nan,
                    p90_silhouette=np.nanquantile(sil[mask],.9) if k>1 else np.nan,rare34_members=int(np.sum(mask&raremask)),
                    low_population100_or_less=int(np.sum(mask&(pop<=100))),zero_housing_positive=int(d.loc[mask,'additional_zero_housing_positive_population'].sum()),
                    hospital_fraction=d.loc[mask,'hospital_tract'].mean(),quartile_counts=json.dumps(d.loc[mask,'frozen_SOVI_quartile'].value_counts().to_dict())))
                if seed==42:
                    for col in descriptors:
                        values=descriptors.loc[mask,col]
                        profiles.append(dict(model='H2-FEMA_NCV14_CA_v119',k=k,seed=seed,cluster=c,variable=col,n_tracts=int(mask.sum()),
                            population=int(pop[mask].sum()),population_share=pop[mask].sum()/pop.sum(),
                            mean=values.mean(),median=values.median(),p10=values.quantile(.1),p90=values.quantile(.9),min=values.min(),max=values.max(),
                            cohort_mean=descriptors[col].mean(),cohort_median=descriptors[col].median(),
                            units='equivalent full-service-deficit hours' if col in ['B_Unconstrained','MeanDelta'] else 'persons' if col=='Population' else '0-100 national social-vulnerability score' if col=='SOVI_SCORE' else '0-1 California-relative screening score' if col=='FEMA_NCV14_CA_v119' else 'definition in source register'))
            means=np.stack([x[lab==c].mean(0) for c in range(k)]);overall=x.mean(0)
            total=np.sum((x-overall)**2,axis=0);within=np.sum((x-means[lab])**2,axis=0);between=total-within
            for j,col in enumerate(rawcols):
                contributions.append(dict(model='H2-FEMA_NCV14_CA_v119',k=k,seed=seed,variable=col,domain='RQ1' if j<3 else 'RQ2' if j<5 else 'RQ3',
                    assigned_squared_distance_budget=BUDGET[j],total_SS=total[j],within_SS=within[j],between_SS=between[j],
                    between_fraction_of_total=between[j]/between.sum() if between.sum()>0 else np.nan))
        print('FIT',condition,k,seed,flush=True)
        return lab
    main_labels={}
    for k in range(1,9):
        for seed in SEEDS:
            lab=fit('main',prototype,k,seed);main_labels[(k,seed)]=lab
            if k>1:
                for other,oldsp in [('P2_seven_ablation','P2'),('H2_CBM_comparator','H2')]:
                    base=old['labels'][oi[f'{oldsp}__published__k{k}__s{seed}']]
                    result=alignment(base,lab,pop)
                    comparisons.append(dict(comparison=other,k=k,seed=seed,**result))
                    if seed==42 and k in [3,4,5]:
                        table=pd.crosstab(base,lab)
                        for c in table.index:
                            for c2 in table.columns:
                                mask=(base==c)&(lab==c2)
                                transitions.append(dict(reference=other,k=k,seed=42,source_model_cluster=int(c),NCV_model_cluster=int(c2),
                                    n_tracts=int(mask.sum()),population=int(pop[mask].sum()),IDs_are_unaligned=True))
    for k in range(2,9):
        for seed1,seed2 in combinations(SEEDS,2):
            stability.append(dict(test='seed',condition=f'{seed1}_vs_{seed2}',k=k,ARI=adjusted_rand_score(main_labels[k,seed1],main_labels[k,seed2])))
    # Prior verified policy matrices preserve exact non-hazard coordinates and matched physical authority.
    for oldkey in oldmat.files:
        if not oldkey.startswith('H2__policy_'):continue
        condition=oldkey.split('H2__',1)[1];x=oldmat[oldkey].copy();x[:,-1]=prototype[:,-1];matrices[condition]=x
        np.testing.assert_array_equal(x[:,:7],oldmat[oldkey][:,:7])
        for k in range(2,9):
            lab=fit(condition,x,k,42);stability.append(dict(test='policy',condition=condition,k=k,**alignment(main_labels[k,42],lab,pop)))
    group=(d.utm_x_m.ge(d.utm_x_m.median()).astype(int)*2+d.utm_y_m.ge(d.utm_y_m.median()).astype(int)).to_numpy()
    raw=d[P2].copy();raw['hazard']=hazard;arr=raw.to_numpy()
    for block in range(4):
        train=group!=block;condition='geographic_block'+str(block)
        x=(arr-arr[train].mean(0))/arr[train].std(0)*np.sqrt(BUDGET);matrices[condition]=x
        for k in range(2,9):
            lab=fit(condition,x,k,42,train)
            stability.append(dict(test='geographic',condition=condition,k=k,heldout_count=int((~train).sum()),
                heldout_ARI=adjusted_rand_score(main_labels[k,42][~train],lab[~train]),**alignment(main_labels[k,42],lab,pop)))
    # Registered Init deletion also redistributes RQ1's budget; no numerical trimming.
    weights=np.array([1/6,1/6,1/6,1/6,1/6,1/12,1/12]);arr_minus=arr[:,1:]
    x=(arr_minus-arr_minus.mean(0))/arr_minus.std(0)*np.sqrt(weights);matrices['minus_Init']=x
    for k in range(2,9):
        lab=fit('minus_Init',x,k,42);stability.append(dict(test='Init_ablation',condition='minus_Init_RQ1_redistributed',k=k,**alignment(main_labels[k,42],lab,pop)))
    variants=frame('HAZARD_LEAVE_ONE_OUT_VECTORS.csv','tract_id').reindex(d.index)
    variant_names=['no_'+h for h in json.loads(lp(OUT/'FEMA_NCV_ADAPTATION_REGISTRATION.json').read_text())['hazards']]
    variants=variants[variant_names].copy()
    variants['LA_component_normalization']=v.FEMA_NCV13_LA_v119_regional_sensitivity
    sensitivity=[]
    for name in variants:
        col=variants[name].to_numpy();x=prototype.copy();x[:,-1]=(col-col.mean())/col.std()*np.sqrt(1/12)
        condition='hazard_'+name;matrices[condition]=x
        for k in [3,4,5]:
            lab=fit(condition,x,k,42)
            sensitivity.append(dict(test='hazard_or_normalization',condition=name,k=k,**alignment(main_labels[k,42],lab,pop)))
    save('CONDITIONAL_K_AND_STABILITY_RESULTS.csv',records)
    save('PER_CLUSTER_SILHOUETTE_AND_POPULATION.csv',clusters)
    save('ORIGINAL_UNIT_CLUSTER_PROFILES.csv',profiles)
    save('DOMAIN_AND_COORDINATE_SEPARATION.csv',contributions)
    save('CANDIDATE_MEMBERSHIP_COMPARISONS.csv',comparisons)
    save('CLUSTER_MEMBERSHIP_TRANSITIONS.csv',transitions)
    save('POLICY_SPATIAL_SEED_INIT_STABILITY.csv',stability)
    save('HAZARD_LEAVE_ONE_OUT_SENSITIVITY.csv',sensitivity)
    np.savez_compressed(dest('REGISTERED_CONDITIONAL_FIT_ARRAYS.npz'),keys=np.array(keys),tract_ids=d.index.to_numpy(dtype='U11'),labels=np.array(labels),silhouette=np.array(silhouettes))
    np.savez_compressed(dest('REGISTERED_CONDITIONAL_MATRICES.npz'),**matrices)
    np.savez_compressed(dest('REGISTERED_MODEL_CENTERS.npz'),**centers)
    save('SOURCE_HASH_VERIFICATION_FITTING.csv',s.records)
    print('Conditional fits complete',len(keys),'all 2299 retained; no Columbia14 fitting; no formal science promotion',flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=1):main()
