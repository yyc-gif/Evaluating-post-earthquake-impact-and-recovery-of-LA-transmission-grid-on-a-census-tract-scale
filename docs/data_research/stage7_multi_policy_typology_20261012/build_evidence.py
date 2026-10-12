"""Transparent evidence summaries, not an optimized decision score."""
from scipy.stats import spearmanr
from common import *


def main():
    assert json.loads(lp(OUT/'REGISTERED_FIT_COMPLETION.json').read_text())['status']=='PASS'
    fits=frame('A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv')
    elbow=frame('ELBOW_AND_SILHOUETTE_COMPARISON.csv')
    seed=frame('SEED_STABILITY.csv'); spatial=frame('SPATIAL_LEAVE_BLOCK_OUT_STABILITY.csv')
    sets=frame('POLICY_SET_CLUSTER_STABILITY.csv'); clusters=frame('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv')
    d=dataset(); arrays=np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz'))
    bykey={k:i for i,k in enumerate(arrays['keys'])}
    summary=[]
    for sp in ['A','P2','P3']:
        for k in KS:
            part=fits.query('specification==@sp and policy_set=="main5" and scaling=="cohort" and k==@k')
            q=elbow.query('specification==@sp and policy_set=="main5" and k==@k').iloc[0]
            ss=seed.query('specification==@sp and policy_set=="main5" and k==@k')
            ge=spatial.query('specification==@sp and policy_set=="main5" and k==@k')
            lo=sets.query('comparison=="policy_set" and specification==@sp and scaling=="cohort" and k==@k and policy_set.str.startswith("without_")',engine='python')
            fx=sets.query('comparison=="policy_set" and specification==@sp and scaling=="fixed_main5" and k==@k and policy_set.str.startswith("without_")',engine='python')
            rnd=sets.query('comparison=="policy_set" and specification==@sp and scaling=="cohort" and k==@k and policy_set=="plus_random"')
            cl=clusters.query('specification==@sp and policy_set=="main5" and scaling=="cohort" and k==@k and seed==42')
            rare=cl.sort_values(['rare_34_capture','rare_34_precision'],ascending=False).iloc[0]
            summary.append(dict(specification=sp,k=k,mean_silhouette=part.mean_silhouette.mean(),seed_silhouette_min=part.mean_silhouette.min(),
                seed_silhouette_max=part.mean_silhouette.max(),mean_WCSS=q.mean_WCSS,chord_gap=q.chord_gap,
                elbow_candidate=q.endpoint_chord_candidate,seed_min_ARI=ss.ARI.min(),seed_median_ARI=ss.ARI.median(),
                geographic_min_ARI=ge.full_ARI.min(),geographic_median_ARI=ge.full_ARI.median(),geographic_max_ARI=ge.full_ARI.max(),
                LOO_min_ARI=lo.ARI.min(),LOO_mean_ARI=lo.ARI.mean(),LOO_max_ARI=lo.ARI.max(),fixed_scaling_LOO_min_ARI=fx.ARI.min(),
                plus_Random_mean_ARI=rnd.ARI.mean(),smallest_class_tracts=cl.n_tracts.min(),
                smallest_class_population_share=cl.population_share.min(),rare_class_tracts=rare.n_tracts,
                rare_34_capture=rare.rare_34_capture,rare_34_precision=rare.rare_34_precision,
                rare_Init_centroid_share=rare.centroid_Init_distance_share))
    save('K_SCIENTIFIC_EVIDENCE_MATRIX.csv',summary)
    summaries=pd.DataFrame(summary); preferred=[]
    for sp in ['A','P2','P3']:
        q=summaries.query('specification==@sp')
        preferred.append(dict(specification=sp,endpoint_chord_candidate=int(q.elbow_candidate.iloc[0]),
            maximum_mean_silhouette_K=int(q.loc[q.mean_silhouette.idxmax(),'k']),maximum_mean_silhouette=q.mean_silhouette.max()))
    save('K_DIAGNOSTIC_PREFERENCES.csv',preferred)
    rare=[]
    from scipy.optimize import linear_sum_assignment
    for row in clusters.query('scaling=="cohort"').itertuples():
        rare.append(dict(specification=row.specification,policy_set=row.policy_set,k=row.k,seed=row.seed,diagnostic_cluster=row.diagnostic_cluster,
            n_tracts=row.n_tracts,rare_members=row.rare_34_members,rare_capture=row.rare_34_capture,rare_precision=row.rare_34_precision,
            distinct_rare_state=(row.rare_34_capture>=.8 and row.rare_34_precision>=.8),centroid_Init_share=row.centroid_Init_distance_share))
    save('RARE_Q_GROUP_MEMBERSHIP_AUDIT.csv',rare)
    # Explicit comparison to the previous A/K5, including different K by label-invariant ARI.
    a=arrays['labels'][bykey[key('A','main5','cohort',5,42)]]
    transitions=[]; comparison=[]
    from sklearn.metrics import adjusted_rand_score
    for sp in ['P2','P3']:
        for k in [3,4,5]:
            b=arrays['labels'][bykey[key(sp,'main5','cohort',k,42)]]
            comparison.append(dict(prior='A_K5_seed42',candidate=sp,k=k,ARI=adjusted_rand_score(a,b)))
            for ca in range(5):
                for cb in range(k):
                    sel=(a==ca)&(b==cb)
                    transitions.append(dict(prior_A_K5_cluster=ca,candidate=sp,k=k,candidate_cluster=cb,n_tracts=sel.sum(),population=d.loc[sel,'Population'].sum()))
    save('A_K5_TO_MULTIPOLICY_COMPARISONS.csv',comparison)
    save('A_K5_TO_MULTIPOLICY_TRANSITIONS.csv',transitions)
    special=[]
    for sp in ['A','P2','P3']:
        for k in [3,4,5]:
            lab=arrays['labels'][bykey[key(sp,'main5','cohort',k,42)]]
            for tid in d.index[d.additional_zero_housing_positive_population]:
                i=d.index.get_loc(tid); c=lab[i]
                special.append(dict(tract_id=tid,specification=sp,k=k,diagnostic_cluster=int(c),cluster_tracts=int((lab==c).sum()),
                    Population=d.loc[tid,'Population'],population_z=(d.loc[tid,'log1p_Population']-d.log1p_Population.mean())/d.log1p_Population.std(ddof=0),
                    PolicySD=d.loc[tid,'PolicySD'],Init_Supply=d.loc[tid,'Init_Supply']))
    save('EIGHT_POSITIVE_POPULATION_ZERO_HOUSING_TRACTS.csv',special)
    dump('EVIDENCE_COMPLETION.json',dict(status='PASS',no_composite_rank_score=True,no_k_promoted=True,
        no_specification_promoted=True,actual_profile_reference='Full cohort original-unit means/medians included in profile table'))


if __name__=='__main__':main()
