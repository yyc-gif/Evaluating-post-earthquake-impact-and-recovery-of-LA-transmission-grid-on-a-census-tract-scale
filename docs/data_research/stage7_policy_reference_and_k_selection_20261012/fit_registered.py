"""Registered controlled K-means only, on verified frozen post-processed metrics."""
from itertools import combinations
import hashlib
import json

from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, pairwise_distances, silhouette_samples

from common import *

PARAMS = dict(init='k-means++', n_init=50, algorithm='lloyd', max_iter=500, tol=1e-4)


def key(policy, spec, scaling, k, seed):
    return f'{policy}__{spec}__{scaling}__k{k}__s{seed}'


def dataset(fixed, metrics, policy):
    d = fixed.copy()
    selected = metrics.loc[metrics.policy.eq(policy)].set_index('tract_id').reindex(d.index)
    d[['B_480_hr', 'Delta_B_logistics']] = selected[['B_480_hr', 'Delta_B_logistics']]
    assert not d[FEATURES].isna().any().any()
    return d


def matching(a, b, population):
    k = max(a.max(), b.max()) + 1
    tab = np.zeros((k, k), dtype=int)
    np.add.at(tab, (a, b), 1)
    i, j = linear_sum_assignment(-tab)
    remap = dict(zip(j, i))
    aligned = np.array([remap[v] for v in b])
    changed = aligned != a
    return dict(ARI=adjusted_rand_score(a, b), aligned_changed_tracts=int(changed.sum()),
        aligned_changed_population=int(population[changed].sum()), aligned_changed_population_share=population[changed].sum()/population.sum()), tab, remap


def main():
    qa = json.loads(lp(OUT / 'POLICY_PAIRING_QA.json').read_text())
    assert qa['status'] == 'PASS' and len(qa['policies']) == 7
    registration = json.loads(lp(OUT / 'REGISTERED_ANALYSIS.json').read_text())
    s = sources()
    fixed = data().query('Population > 0')
    assert len(fixed) == 2299
    metrics = frame('POLICY_REFERENCE_TRACT_METRICS.csv')
    baseline = dataset(fixed, metrics, 'impact-first')
    rare_ids = frozen(s, INTERPRETATION + 'THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').index
    rare = fixed.index.isin(rare_ids)
    assert rare.sum() == 34
    old = frozen(s, PREVIOUS + 'CLUSTER_MEMBERSHIPS_POSITIVE_POPULATION.csv').reindex(fixed.index)
    spatial_source = frozen(s, PREVIOUS + 'SPATIAL_SUPPORT_AND_BLOCKS.csv').reindex(fixed.index)
    blocks = spatial_source.block.to_numpy(int)
    xy = fixed[['utm_x_m', 'utm_y_m']].to_numpy()
    np.testing.assert_array_equal(blocks, (xy[:,0] >= np.median(xy[:,0])).astype(int) + 2*(xy[:,1] >= np.median(xy[:,1])).astype(int))
    save('SPATIAL_SUPPORT_AND_BLOCKS.csv', spatial_source.reset_index())
    fit_rows, cluster_rows, profiles, scaler_rows, contribution_rows = [], [], [], [], []
    labels, sil_values, matrices, datasets, centroids = {}, {}, {}, {}, {}
    replay_rows = []
    for policy in POLICIES:
        d = dataset(fixed, metrics, policy)
        datasets[policy] = d
        for spec in ['A', 'A-minus-Init']:
            for scaling in ['policy_cohort', 'fixed_impact']:
                ref = baseline if scaling == 'fixed_impact' else None
                x, mu, sd = matrix(d, spec, ref)
                condition = (policy, spec, scaling)
                matrices[condition] = x
                for v, m, t, budget in zip(columns(spec), mu, sd, weights(spec)):
                    scaler_rows.append(dict(policy=policy, specification=spec, scaling=scaling, variable=v, mean=m, sd=t, squared_distance_budget=budget))
                distances = pairwise_distances(x, metric='euclidean')
                np.fill_diagonal(distances, 0)
                ss = ((x - x.mean(0))**2).sum(0)
                for k in [1, *KS]:
                    for seed in SEEDS:
                        kk = key(policy, spec, scaling, k, seed)
                        # Impact-first's two scaling rules are exactly identical.
                        alias = key(policy, spec, 'policy_cohort', k, seed)
                        if scaling == 'fixed_impact' and policy == 'impact-first':
                            lab, sil = labels[alias].copy(), sil_values[alias].copy()
                        else:
                            model = KMeans(n_clusters=k, random_state=seed, **PARAMS).fit(x)
                            lab = canon(model.labels_, d)
                            sil = silhouette_samples(distances, lab, metric='precomputed') if k > 1 else np.full(len(d), np.nan)
                        labels[kk], sil_values[kk] = lab, sil
                        means = np.stack([x[lab == c].mean(0) for c in range(k)])
                        centroids[kk] = means
                        wcss = ((x - means[lab])**2).sum()
                        clusters = np.bincount(lab, minlength=k)
                        fit_rows.append(dict(policy=policy, specification=spec, scaling=scaling, k=k, seed=seed, WCSS=wcss,
                            mean_silhouette=np.nanmean(sil) if k>1 else np.nan, median_silhouette=np.nanmedian(sil) if k>1 else np.nan,
                            negative_silhouette_fraction=(sil<0).mean() if k>1 else np.nan,
                            min_cluster_tracts=clusters.min(), max_cluster_tracts=clusters.max(),
                            matrix_sha256=hashlib.sha256(x.astype('<f8').tobytes()).hexdigest()))
                        if policy == 'impact-first' and scaling == 'policy_cohort' and k in [3,4,5,6]:
                            expected = old[f'{spec}__k{k}__s{seed}'].to_numpy(int)
                            replay_rows.append(dict(specification=spec, k=k, seed=seed, exact_labels_equal=bool(np.array_equal(lab, expected)), ARI=adjusted_rand_score(lab, expected)))
                            assert np.array_equal(lab, expected)
                        between = np.zeros(len(columns(spec)))
                        for c in range(k):
                            selected = lab == c
                            part = d.loc[selected]
                            values = sil[selected]
                            bss = selected.sum() * (means[c] - x.mean(0))**2
                            between += bss
                            init_share = bss[0]/bss.sum() if spec == 'A' and bss.sum()>0 else np.nan
                            cluster_rows.append(dict(policy=policy, specification=spec, scaling=scaling, k=k, seed=seed,
                                diagnostic_cluster=c, n_tracts=len(part), population=part.Population.sum(), population_share=part.Population.sum()/d.Population.sum(),
                                mean_silhouette=np.mean(values) if k>1 else np.nan, median_silhouette=np.median(values) if k>1 else np.nan,
                                p10_silhouette=np.quantile(values,.1) if k>1 else np.nan, p90_silhouette=np.quantile(values,.9) if k>1 else np.nan,
                                negative_fraction=(values<0).mean() if k>1 else np.nan,
                                rare_34_members=int((selected & rare).sum()), rare_34_capture=(selected & rare).sum()/34,
                                rare_34_precision=(selected & rare).sum()/selected.sum(),
                                centroid_separation_Init_share=init_share,
                                zero_Init_fraction=part.Init_Supply.eq(0).mean(),
                                added_zero_housing_tracts=part.additional_zero_housing_positive_population.sum(),
                                Q4_fraction=part.frozen_SOVI_quartile.eq('Q4').mean(),
                                mean_lat=part.INTPTLAT.mean(), mean_lon=part.INTPTLON.mean(),
                                largest_spatial_quadrant_share=np.bincount(blocks[selected], minlength=4).max()/selected.sum()))
                            if seed == 42 and k > 1:
                                for v in FEATURES + ['Population', 'B_unconstrained']:
                                    a = part[v]
                                    profiles.append(dict(policy=policy, specification=spec, scaling=scaling, k=k, diagnostic_cluster=c, variable=v,
                                        n_tracts=len(part), population=part.Population.sum(), population_share=part.Population.sum()/d.Population.sum(),
                                        mean=a.mean(), median=a.median(), p10=a.quantile(.1), p90=a.quantile(.9), minimum=a.min(), maximum=a.max(),
                                        cohort_mean=d[v].mean(), cohort_median=d[v].median()))
                        for v, total, b in zip(columns(spec), ss, between):
                            domain = 'RQ1' if v in FEATURES[:3] else 'RQ2' if v in FEATURES[3:5] else 'RQ3'
                            contribution_rows.append(dict(policy=policy, specification=spec, scaling=scaling, k=k, seed=seed, variable=v, domain=domain,
                                total_SS=total, between_SS=b, within_SS=total-b, between_fraction_of_all= b/between.sum() if between.sum()>0 else np.nan))
                print('registered fits', policy, spec, scaling, flush=True)
    save('SILHOUETTE_BY_K_AND_SEED.csv', fit_rows)
    save('PER_CLUSTER_SILHOUETTE_AND_SIZE.csv', cluster_rows)
    save('CLUSTER_ORIGINAL_UNIT_PROFILES.csv', profiles)
    save('COHORT_STANDARDIZATION_AND_WEIGHTS.csv', scaler_rows)
    save('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv', contribution_rows)
    save('PRIOR_REGISTERED_FIT_RECONSTRUCTION_QA.csv', replay_rows)
    fit = pd.DataFrame(fit_rows)
    elbow = []
    for condition, group in fit.groupby(['policy','specification','scaling']):
        means = group.groupby('k').WCSS.mean()
        norm = (means.iloc[0] - means)/(means.iloc[0]-means.iloc[-1])
        gap = norm.to_numpy() - np.linspace(0,1,8)
        knee = int(means.index[np.argmax(gap)])
        for k in means.index:
            elbow.append(dict(policy=condition[0], specification=condition[1], scaling=condition[2], k=k, mean_WCSS=means[k],
                min_WCSS=group.loc[group.k.eq(k),'WCSS'].min(), max_WCSS=group.loc[group.k.eq(k),'WCSS'].max(),
                relative_reduction_from_previous=(means[k-1]-means[k])/means[k-1] if k>1 else np.nan,
                fraction_K1_inertia_removed=1-means[k]/means[1], normalized_endpoint_reduction=norm[k],
                chord_gap=gap[k-1], endpoint_chord_elbow_candidate=knee))
    save('ELBOW_INERTIA_BY_K.csv', elbow)
    np.savez_compressed(lp(OUT/'REGISTERED_FIT_ARRAYS.npz'), tract_ids=fixed.index.to_numpy(str), keys=np.array(list(labels)),
        labels=np.stack(list(labels.values())), silhouette=np.stack(list(sil_values.values())))
    np.savez_compressed(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'), tract_ids=fixed.index.to_numpy(str),
        **{'__'.join(c): x for c,x in matrices.items()})
    seed_rows, compare_rows, transition_rows, spatial_rows, algebra = [], [], [], [], []
    pop = fixed.Population.to_numpy()
    for policy in POLICIES:
        for spec in ['A','A-minus-Init']:
            for scaling in ['policy_cohort','fixed_impact']:
                d = datasets[policy]
                x = matrices[(policy,spec,scaling)]
                for k in KS:
                    for seed_a, seed_b in combinations(SEEDS,2):
                        seed_rows.append(dict(policy=policy,specification=spec,scaling=scaling,k=k,seed_a=seed_a,seed_b=seed_b,
                            ARI=adjusted_rand_score(labels[key(policy,spec,scaling,k,seed_a)],labels[key(policy,spec,scaling,k,seed_b)])))
                    base = labels[key(policy,spec,scaling,k,42)]
                    for block in range(4):
                        train = blocks != block
                        if scaling == 'policy_cohort':
                            raw = d[columns(spec)].to_numpy(float)
                            mu, sd = raw[train].mean(0), raw[train].std(0)
                            x_all = (raw-mu)/sd * np.sqrt(weights(spec))
                        else: x_all = x
                        model = KMeans(n_clusters=k,random_state=42,**PARAMS).fit(x_all[train])
                        predicted = model.predict(x_all)
                        rc = np.bincount(predicted[rare],minlength=k).argmax()
                        spatial_rows.append(dict(policy=policy,specification=spec,scaling=scaling,k=k,left_out_block=block,
                            training_tracts=int(train.sum()), held_out_tracts=int((~train).sum()),
                            full_ARI=adjusted_rand_score(base,predicted), held_out_ARI=adjusted_rand_score(base[~train],predicted[~train]),
                            rare_majority_capture=(predicted[rare]==rc).mean(), rare_majority_class_size=int((predicted==rc).sum()),
                            rare_majority_precision=(predicted[rare]==rc).sum()/(predicted==rc).sum()))
                    if spec == 'A':
                        for c in range(k):
                            selected = base==c
                            delta = x[selected].mean(0)-x.mean(0)
                            no_init = (delta[1:]**2).sum()
                            redistributed = no_init + .5*(delta[1:3]**2).sum()
                            algebra.append(dict(policy=policy,scaling=scaling,k=k,diagnostic_cluster=c,
                                rare_members=int((selected&rare).sum()), n_tracts=int(selected.sum()),
                                centroid_squared_distance=(delta**2).sum(), Init_squared_distance=delta[0]**2,
                                omit_Init_fixed_remaining_budgets=no_init,
                                omit_Init_RQ1_redistributed_budgets=redistributed))
                print('spatial checks', policy, spec, scaling, flush=True)
    for spec in ['A','A-minus-Init']:
        for scaling in ['policy_cohort','fixed_impact']:
            for k in KS:
                for seed in SEEDS:
                    for a,b in combinations(POLICIES,2):
                        la,lb = labels[key(a,spec,scaling,k,seed)],labels[key(b,spec,scaling,k,seed)]
                        row, tab, remap = matching(la,lb,pop)
                        compare_rows.append(dict(comparison='policy',policy_a=a,policy_b=b,specification=spec,scaling=scaling,k=k,seed=seed,**row))
                        if a=='impact-first' and seed==42:
                            for ca in range(k):
                                cb = next(c for c,r in remap.items() if r==ca)
                                intersection, union = tab[ca,cb], (la==ca).sum()+(lb==cb).sum()-tab[ca,cb]
                                transition_rows.append(dict(policy_a=a,policy_b=b,specification=spec,scaling=scaling,k=k,cluster_a=ca,matched_cluster_b=cb,
                                    common_tracts=intersection,jaccard=intersection/union,
                                    Q4_members_a=int(((la==ca)&fixed.frozen_SOVI_quartile.eq('Q4').to_numpy()).sum()),
                                    Q4_members_b=int(((lb==cb)&fixed.frozen_SOVI_quartile.eq('Q4').to_numpy()).sum())))
    for policy in POLICIES:
        for k in KS:
            for seed in SEEDS:
                for spec in ['A','A-minus-Init']:
                    a,b = labels[key(policy,spec,'policy_cohort',k,seed)],labels[key(policy,spec,'fixed_impact',k,seed)]
                    row,_,_ = matching(a,b,pop)
                    compare_rows.append(dict(comparison='scaling',policy_a=policy,policy_b=policy,specification=spec,scaling='policy_cohort_vs_fixed_impact',k=k,seed=seed,**row))
                for scaling in ['policy_cohort','fixed_impact']:
                    a,b = labels[key(policy,'A',scaling,k,seed)],labels[key(policy,'A-minus-Init',scaling,k,seed)]
                    row,_,_ = matching(a,b,pop)
                    compare_rows.append(dict(comparison='Init_ablation',policy_a=policy,policy_b=policy,specification='A_vs_A-minus-Init',scaling=scaling,k=k,seed=seed,**row))
    save('SEED_STABILITY.csv',seed_rows)
    save('SPATIAL_LEAVE_OUT_STABILITY.csv',spatial_rows)
    save('POLICY_CONDITIONAL_MEMBERSHIP_COMPARISONS.csv',compare_rows)
    save('MATCHED_CLASS_TRANSITIONS.csv',transition_rows)
    save('INIT_ALGEBRAIC_DISTANCE_DIAGNOSTICS.csv',algebra)
    save('SOURCE_HASH_VERIFICATION_FITS.csv',s.records)
    dump('REGISTERED_FIT_COMPLETION.json',dict(status='PASS',models=len(labels),spatial_refits=len(spatial_rows),full_silhouette=True,
        registration_sha256=sha(OUT/'REGISTERED_ANALYSIS.json'),pairing_qa_sha256=sha(OUT/'POLICY_PAIRING_QA.json'),no_new_physical_simulation=True))


if __name__=='__main__': main()
