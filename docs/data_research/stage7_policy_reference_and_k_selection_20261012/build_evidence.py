"""Summarize registered evidence and original frozen group descriptions."""
from scipy.stats import pearsonr, spearmanr
from common import *


def main():
    fit=frame('SILHOUETTE_BY_K_AND_SEED.csv')
    elbow=frame('ELBOW_INERTIA_BY_K.csv')
    clusters=frame('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv')
    seed=frame('SEED_STABILITY.csv')
    spatial=frame('SPATIAL_LEAVE_OUT_STABILITY.csv')
    comparisons=frame('POLICY_CONDITIONAL_MEMBERSHIP_COMPARISONS.csv')
    evidence=[]
    for (policy,spec,scaling,k), group in fit.loc[fit.k.gt(1)].groupby(['policy','specification','scaling','k']):
        e=elbow.loc[elbow.policy.eq(policy)&elbow.specification.eq(spec)&elbow.scaling.eq(scaling)&elbow.k.eq(k)].iloc[0]
        cs=clusters.loc[clusters.policy.eq(policy)&clusters.specification.eq(spec)&clusters.scaling.eq(scaling)&clusters.k.eq(k)]
        se=seed.loc[seed.policy.eq(policy)&seed.specification.eq(spec)&seed.scaling.eq(scaling)&seed.k.eq(k)]
        sp=spatial.loc[spatial.policy.eq(policy)&spatial.specification.eq(spec)&spatial.scaling.eq(scaling)&spatial.k.eq(k)]
        other=comparisons.loc[comparisons.comparison.eq('policy')&comparisons.specification.eq(spec)&comparisons.scaling.eq(scaling)&comparisons.k.eq(k)&(comparisons.policy_a.eq(policy)|comparisons.policy_b.eq(policy))]
        rare=cs.loc[cs.rare_34_capture.ge(.8)&cs.rare_34_precision.ge(.8)]
        evidence.append(dict(policy=policy,specification=spec,scaling=scaling,k=k,
            mean_WCSS=e.mean_WCSS,relative_WCSS_reduction=e.relative_reduction_from_previous,chord_gap=e.chord_gap,
            chord_elbow_candidate=e.endpoint_chord_elbow_candidate,
            silhouette_mean=group.mean_silhouette.mean(),silhouette_min=group.mean_silhouette.min(),silhouette_max=group.mean_silhouette.max(),
            silhouette_median_mean=group.median_silhouette.mean(),negative_fraction_mean=group.negative_silhouette_fraction.mean(),
            seed_ARI_min=se.ARI.min(),seed_ARI_median=se.ARI.median(),
            spatial_full_ARI_min=sp.full_ARI.min(),spatial_full_ARI_median=sp.full_ARI.median(),
            spatial_heldout_ARI_min=sp.held_out_ARI.min(),spatial_heldout_ARI_median=sp.held_out_ARI.median(),
            policy_pair_ARI_min=other.ARI.min(),policy_pair_ARI_median=other.ARI.median(),
            min_class_tracts=cs.n_tracts.min(),min_class_population_share=cs.population_share.min(),
            rare_isolated_in_seeds=rare.seed.nunique(),rare_class_size_min=rare.n_tracts.min(),rare_class_size_max=rare.n_tracts.max(),
            rare_centroid_Init_share_median=rare.centroid_separation_Init_share.median()))
    save('K_SELECTION_EVIDENCE_MATRIX.csv',evidence)
    summaries=[]
    for (p,s,sc),g in pd.DataFrame(evidence).groupby(['policy','specification','scaling']):
        best=g.loc[g.silhouette_mean.idxmax()]
        summaries.append(dict(policy=p,specification=s,scaling=sc,endpoint_chord_elbow_candidate=best.chord_elbow_candidate,
            maximum_mean_silhouette_k=int(best.k),maximum_mean_silhouette=best.silhouette_mean,
            elbow_and_silhouette_agree=bool(best.chord_elbow_candidate==best.k)))
    save('ELBOW_SILHOUETTE_PREFERENCE_SUMMARY.csv',summaries)
    d=data().query('Population > 0')
    init=d.Init_Supply.to_numpy(float)
    deviations=(init-init.mean())**2
    save('INIT_SUPPLY_DISTRIBUTION.csv',[dict(n=len(init),exact_zero=int((init==0).sum()),
        zero_fraction=(init==0).mean(),mean=init.mean(),median=np.median(init),sd=init.std(),maximum=init.max(),
        standardized_minimum=(init.min()-init.mean())/init.std(),standardized_maximum=(init.max()-init.mean())/init.std(),
        top23_variance_fraction=np.sort(deviations)[-23:].sum()/deviations.sum())])
    m=frame('POLICY_REFERENCE_TRACT_METRICS.csv')
    profiles, influence, dependence, changes=[] ,[],[],[]
    with np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz'),allow_pickle=False) as z:
        labels=dict(zip(z['keys'],z['labels']));sil=dict(zip(z['keys'],z['silhouette']))
        assert np.array_equal(z['tract_ids'],d.index)
    with np.load(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'),allow_pickle=False) as weighted:
        for policy in POLICIES:
            dm=m.loc[m.policy.eq(policy)].set_index('tract_id').reindex(d.index)
            dependence.append(dict(policy=policy,B_Delta_pearson=pearsonr(dm.B_480_hr,dm.Delta_B_logistics).statistic,
                B_Delta_spearman=spearmanr(dm.B_480_hr,dm.Delta_B_logistics).statistic,
                B_Unconstrained_pearson=pearsonr(dm.B_480_hr,dm.B_unconstrained).statistic))
            for sc in ['policy_cohort','fixed_impact']:
                for k in KS:
                    x=weighted['__'.join([policy,'A',sc])]
                    lab=labels[f'{policy}__A__{sc}__k{k}__s42']
                    for c in range(k):
                        part=d.loc[lab==c]
                        row=dict(policy=policy,scaling=sc,k=k,diagnostic_cluster=c,n_tracts=len(part),population=part.Population.sum(),
                            population_share=part.Population.sum()/d.Population.sum(),median_tract_population=part.Population.median(),
                            hospital_tract_fraction=part.hospital_tract.mean(),added_zero_housing_tracts=int(part.additional_zero_housing_positive_population.sum()),
                            original_group_data_are_descriptive_not_independent_validation=True)
                        for q in ['Q1','Q2','Q3','Q4']:
                            row[q+'_n']=int(part.frozen_SOVI_quartile.eq(q).sum())
                            row[q+'_population_share']=part.loc[part.frozen_SOVI_quartile.eq(q),'Population'].sum()/part.Population.sum()
                        profiles.append(row)
                    for seed in SEEDS:
                        kk=f'{policy}__A__{sc}__k{k}__s{seed}'
                        cs=clusters.loc[clusters.policy.eq(policy)&clusters.specification.eq('A')&clusters.scaling.eq(sc)&clusters.k.eq(k)&clusters.seed.eq(seed)]
                        rare=cs.loc[cs.rare_34_capture.ge(.8)&cs.rare_34_precision.ge(.8)]
                        if len(rare):
                            rare_c=int(rare.iloc[0].diagnostic_cluster);mask=labels[kk]==rare_c
                            influence.append(dict(policy=policy,scaling=sc,k=k,seed=seed,rare_class_n=int(mask.sum()),
                                rare_class_mean_silhouette=sil[kk][mask].mean(),nonrare_mean_silhouette=sil[kk][~mask].mean(),
                                all_mean_silhouette=sil[kk].mean(),rare_composition_effect_on_mean=sil[kk].mean()-sil[kk][~mask].mean(),
                                centroid_Init_fraction=rare.iloc[0].centroid_separation_Init_share))
    save('CLUSTER_POPULATION_AND_FROZEN_GROUP_PROFILES.csv',profiles)
    save('INIT_RARE_GROUP_SILHOUETTE_COMPOSITION.csv',influence)
    save('RQ2_WITHIN_POLICY_REDUNDANCY.csv',dependence)
    # Registered K3->K4->K5 transitions, without implying shared class IDs.
    for policy in POLICIES:
        for k1,k2 in [(3,4),(4,5)]:
            a=labels[f'{policy}__A__policy_cohort__k{k1}__s42'];b=labels[f'{policy}__A__policy_cohort__k{k2}__s42']
            for ca in range(k1):
                for cb in range(k2):
                    use=(a==ca)&(b==cb)
                    changes.append(dict(policy=policy,k_a=k1,k_b=k2,cluster_a=ca,cluster_b=cb,
                        n_tracts=int(use.sum()),population=int(d.loc[use,'Population'].sum()),fraction_of_parent=use.sum()/(a==ca).sum()))
    save('K3_K4_K5_MEMBERSHIP_TRANSITIONS.csv',changes)
    print('Evidence matrix and original-group profiles completed.',flush=True)


if __name__=='__main__':main()
