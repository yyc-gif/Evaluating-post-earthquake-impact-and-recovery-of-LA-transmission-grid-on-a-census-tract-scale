"""Registered statistical diagnostics and exploratory K-means only.

Read the verified tract table; write exclusively beside this script.
No model, damage, scheduling, gate, trajectory or formal Stage 7 execution.
"""
from itertools import combinations
import json
import time

import numpy as np
import pandas as pd
import scipy
from scipy import stats
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score, r2_score
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler
import sklearn

from common import OUT, SPEC, cohorts, distribution, dump, frame, lp, save, sha

PROFILE_VARIABLES = [*SPEC['specifications']['B'], 'Population', 'BUILDVALUE', 'T80',
                     'Pop_Density', 'housing_total', 'CDC2022_EP_GROUPQ']


def spline_r2(x, y):
    model = make_pipeline(StandardScaler(), SplineTransformer(n_knots=5, degree=3, include_bias=False),
                          StandardScaler(), Ridge(alpha=1))
    cv = KFold(5, shuffle=True, random_state=42)
    return r2_score(y, cross_val_predict(model, np.asarray(x), np.asarray(y), cv=cv))


def information_audit(d):
    rows, matrix, condition, tails = [], [], [], []
    input_cols = list(SPEC['specifications']['B'])
    diagnostics = ['Population', 'BUILDVALUE', 'Pop_Density', 'EAL_SCORE', 'EAL_VALT', 'ALR_NPCTL']
    for cohort, sub in cohorts(d).items():
        for a, b in combinations(input_cols + diagnostics, 2):
            valid = sub[[a, b]].dropna()
            assert len(valid) == len(sub), 'Diagnostic missingness must be handled explicitly'
            matrix.append(dict(cohort=cohort, variable_a=a, variable_b=b, n=len(valid),
                pearson=valid[a].corr(valid[b]), spearman=valid[a].corr(valid[b], method='spearman')))
        y = sub.log1p_BUILDVALUE.to_numpy()
        for c in [x for x in input_cols+diagnostics if x not in ['BUILDVALUE', 'log1p_BUILDVALUE']]:
            x = sub[[c]].to_numpy()
            row = dict(cohort=cohort, kind='pairwise', target='log1p_BUILDVALUE', predictor=c, n=len(sub),
                pearson=sub.log1p_BUILDVALUE.corr(sub[c]), spearman=sub.log1p_BUILDVALUE.corr(sub[c], method='spearman'),
                linear_R2=LinearRegression().fit(x,y).score(x,y), spline_random_tract_CV_R2=spline_r2(x,y),
                mutual_information_nats=mutual_info_regression(x,y,n_neighbors=5,random_state=42)[0])
            rows.append(row)
        for c in input_cols:
            other = [x for x in input_cols if x != c]
            x, y_c = sub[other].to_numpy(), sub[c].to_numpy()
            r2 = LinearRegression().fit(x,y_c).score(x,y_c)
            row = dict(cohort=cohort, kind='conditional_all_other_primary', target=c,
                       predictor=json.dumps(other), n=len(sub), linear_R2=r2,
                       VIF=1/(1-r2), spline_random_tract_CV_R2=spline_r2(x,y_c))
            condition.append(row)
            if c == 'log1p_BUILDVALUE':
                rows.append(row)
        for control in [['log1p_Population'], ['log1p_Population','SOVI_SCORE'],
                        ['log1p_Population','SOVI_SCORE','log1p_Pop_Density']]:
            x = sub[control].to_numpy()
            r2 = LinearRegression().fit(x,y).score(x,y)
            rows.append(dict(cohort=cohort, kind='declared_construct_controls', target='log1p_BUILDVALUE',
                            predictor=json.dumps(control), n=len(sub), linear_R2=r2, VIF=1/(1-r2),
                            spline_random_tract_CV_R2=spline_r2(x,y)))
        cutoff = sub.BUILDVALUE.quantile(.99)
        top = sub.BUILDVALUE.ge(cutoff)
        for flag, selected in [('all', sub), ('below_asset_P99', sub.loc[~top]), ('asset_P99_tail', sub.loc[top])]:
            tails.append(dict(cohort=cohort, subset=flag, n=len(selected),
                asset_share=selected.BUILDVALUE.sum()/sub.BUILDVALUE.sum(),
                population_share=selected.Population.sum()/sub.Population.sum(),
                **{('BUILDVALUE_'+k):v for k,v in distribution(selected.BUILDVALUE).items()},
                pearson_log_assets_log_population=selected.log1p_BUILDVALUE.corr(selected.log1p_Population),
                pearson_log_assets_SOVI=selected.log1p_BUILDVALUE.corr(selected.SOVI_SCORE)))
    save('BUILDVALUE_INCREMENTAL_INFORMATION.csv', rows)
    save('SAME_COHORT_ASSOCIATION_MATRIX.csv', matrix)
    save('CONDITIONAL_R2_AND_VIF.csv', condition)
    save('BUILDVALUE_EXTREME_AND_TAIL_SENSITIVITY.csv', tails)


def canonical(labels, d):
    profiles = d.assign(label=labels).groupby('label')[['B_480_hr','Population']].mean()
    order = profiles.sort_values(['B_480_hr','Population']).index.tolist()
    return np.array([{old:new for new,old in enumerate(order)}[c] for c in labels], dtype=np.int16)


def fit(d, budgets, k, seed, training=None):
    if training is None:
        training = np.ones(len(d), dtype=bool)
    cols = list(budgets)
    scaler = StandardScaler().fit(d.loc[training, cols])
    assert (scaler.scale_ > 0).all()
    z = scaler.transform(d[cols])
    x = z * np.sqrt(list(budgets.values()))
    model = KMeans(n_clusters=k, random_state=seed, **SPEC['kmeans']).fit(x[training])
    labels = canonical(model.predict(x), d)
    return labels, x, z, scaler, model


def alignment(a,b,k):
    contingency = np.zeros((k,k), dtype=int)
    np.add.at(contingency,(a,b),1)
    r,c = linear_sum_assignment(-contingency)
    map_b = dict(zip(c,r))
    aligned = np.array([map_b[v] for v in b])
    return aligned, contingency


def comparison(a,b,k):
    aligned, table = alignment(a,b,k)
    return dict(ARI=adjusted_rand_score(a,b), NMI=normalized_mutual_info_score(a,b),
                matched_agreement=float(np.mean(a==aligned)), changed_count=int(np.sum(a!=aligned)))


def decomposition(d, x, labels, budgets, context):
    total = np.square(x-x.mean(0)).sum(0)
    between = np.zeros(x.shape[1])
    for label in np.unique(labels):
        points = x[labels==label]
        between += len(points)*np.square(points.mean(0)-x.mean(0))
    within = total-between
    rows = []
    for i,c in enumerate(budgets):
        rows.append(dict(**context, kind='coordinate', coordinate=c, domain=SPEC['domains'][c],
            squared_distance_budget=budgets[c], total_SS=total[i], between_SS=between[i], within_SS=within[i],
            between_fraction_of_total=between[i]/total.sum(), fraction_of_between=between[i]/between.sum(),
            fraction_of_within=within[i]/within.sum(), coordinate_explained_fraction=between[i]/total[i]))
    for domain in ['RQ1','RQ2','RQ3']:
        idx = [i for i,c in enumerate(budgets) if SPEC['domains'][c]==domain]
        rows.append(dict(**context, kind='domain', coordinate=domain, domain=domain,
            squared_distance_budget=sum(budgets[c] for c in budgets if SPEC['domains'][c]==domain),
            total_SS=total[idx].sum(), between_SS=between[idx].sum(), within_SS=within[idx].sum(),
            between_fraction_of_total=between[idx].sum()/total.sum(), fraction_of_between=between[idx].sum()/between.sum(),
            fraction_of_within=within[idx].sum()/within.sum(), coordinate_explained_fraction=between[idx].sum()/total[idx].sum()))
    return rows, total.sum(), between.sum(), within.sum()


def clustering(d):
    memberships, registered, profiles, contrib, clusters, scalers, seed_stability = {}, [], [], [], [], [], []
    objects = {}
    start = time.perf_counter()
    for cohort, sub in cohorts(d).items():
        table = {'tract_id':sub.index}
        init_top = sub.Init_Supply.ge(sub.Init_Supply.quantile(.99)).to_numpy()
        asset_top = sub.BUILDVALUE.ge(sub.BUILDVALUE.quantile(.99)).to_numpy()
        extra = sub.additional_zero_housing_positive_population.to_numpy()
        for spec, budgets in SPEC['specifications'].items():
            for k in SPEC['k_values']:
                for seed in SPEC['seeds']:
                    ctx = dict(cohort=cohort, specification=spec, k=k, seed=seed)
                    labels,x,z,scaler,model = fit(sub,budgets,k,seed)
                    key = (cohort,spec,k,seed)
                    objects[key] = labels
                    table[f'{spec}__k{k}__s{seed}'] = labels
                    rows,total,bss,wss = decomposition(sub,x,labels,budgets,ctx)
                    contrib.extend(rows)
                    counts = np.bincount(labels,minlength=k)
                    center_sse = np.square(x-model.cluster_centers_[model.predict(x)]).sum()
                    assert abs(center_sse-model.inertia_) < 1e-8
                    registered.append(dict(**ctx,n_tracts=len(sub),population=int(sub.Population.sum()),
                        n_features=len(budgets),n_init=SPEC['kmeans']['n_init'],n_iter=model.n_iter_,
                        cluster_sizes=json.dumps(counts.tolist()),min_cluster_size=counts.min(),max_cluster_size=counts.max(),
                        inertia=model.inertia_,partition_centroid_SS=wss,
                        stored_center_vs_partition_centroid_gap=model.inertia_-wss,
                        total_SS=total,between_SS=bss,within_SS=wss,
                        explained_distance_fraction=bss/total))
                    for pos,c in enumerate(budgets):
                        scalers.append(dict(**ctx,variable=c,mean=scaler.mean_[pos],sd_ddof0=scaler.scale_[pos],
                            squared_distance_budget=budgets[c],euclidean_multiplier=np.sqrt(budgets[c]),
                            z_min=z[:,pos].min(),z_max=z[:,pos].max()))
                    for label in range(k):
                        mask=labels==label
                        part=sub.loc[mask]
                        clusters.append(dict(**ctx,diagnostic_cluster=label,n_tracts=len(part),
                            population=int(part.Population.sum()),population_fraction=part.Population.sum()/sub.Population.sum(),
                            BUILDVALUE_sum=part.BUILDVALUE.sum(),BUILDVALUE_fraction=part.BUILDVALUE.sum()/sub.BUILDVALUE.sum(),
                            Init_nonzero_count=int(part.Init_Supply.gt(0).sum()),
                            Init_P99_count=int(init_top[mask].sum()),asset_P99_count=int(asset_top[mask].sum()),
                            extra_zero_housing_count=int(extra[mask].sum()),
                            Init_P99_fraction=init_top[mask].mean(),asset_P99_fraction=asset_top[mask].mean(),
                            Init_mean=part.Init_Supply.mean(),Init_max=part.Init_Supply.max(),
                            B_mean=part.B_480_hr.mean(),Delta_mean=part.Delta_B_logistics.mean(),
                            SOVI_mean=part.SOVI_SCORE.mean(),Population_median=part.Population.median(),
                            BUILDVALUE_median=part.BUILDVALUE.median()))
                        for c in PROFILE_VARIABLES:
                            profiles.append(dict(**ctx,diagnostic_cluster=label,variable=c,**distribution(part[c])))
                for a,b in combinations(SPEC['seeds'],2):
                    la,lb=objects[(cohort,spec,k,a)],objects[(cohort,spec,k,b)]
                    seed_stability.append(dict(cohort=cohort,specification=spec,k=k,kind='seed_pair',
                        seed_a=a,seed_b=b,**comparison(la,lb,k)))
                print(f'{cohort} {spec} k={k} complete; {time.perf_counter()-start:.1f}s',flush=True)
        memberships[cohort]=pd.DataFrame(table)
    save('REGISTERED_EXPLORATORY_CLUSTERING.csv',registered)
    save('CLUSTER_PROFILE_DISTRIBUTIONS.csv',profiles)
    save('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv',contrib)
    save('CLUSTER_SIZE_POPULATION_AND_EXTREMES.csv',clusters)
    save('COHORT_STANDARDIZATION_AND_WEIGHTS.csv',scalers)
    save('CLUSTER_MEMBERSHIPS_POSITIVE_POPULATION.csv',memberships['positive_population'])
    save('CLUSTER_MEMBERSHIPS_RESIDENTIAL.csv',memberships['residential'])
    compare_rows,transitions,cohort_rows = [], [], []
    comparisons=[('A','B'),('A','A-minus-Init'),('B','B-minus-Init'),
                 ('A-minus-Init','B-minus-Init'),('B','B-equal-RQ3')]
    for cohort,sub in cohorts(d).items():
        for k in SPEC['k_values']:
            for seed in SPEC['seeds']:
                for a,b in comparisons:
                    la,lb=objects[(cohort,a,k,seed)],objects[(cohort,b,k,seed)]
                    compare_rows.append(dict(cohort=cohort,specification_a=a,specification_b=b,k=k,seed=seed,**comparison(la,lb,k)))
                    aligned,_=alignment(la,lb,k)
                    for ca in range(k):
                        for cb in range(k):
                            mask=(la==ca)&(aligned==cb)
                            transitions.append(dict(cohort=cohort,specification_a=a,specification_b=b,k=k,seed=seed,
                                aligned_cluster_a=ca,aligned_cluster_b=cb,n_tracts=int(mask.sum()),population=int(sub.Population[mask].sum())))
    common=cohorts(d)['residential'].index
    positive_ids=cohorts(d)['positive_population'].index
    positive_pos=positive_ids.get_indexer(common)
    extra_pos=np.flatnonzero(cohorts(d)['positive_population'].additional_zero_housing_positive_population)
    for spec in SPEC['specifications']:
        for k in SPEC['k_values']:
            for seed in SPEC['seeds']:
                a=objects[('positive_population',spec,k,seed)]
                b=objects[('residential',spec,k,seed)]
                cohort_rows.append(dict(specification=spec,k=k,seed=seed,n_common=len(common),
                    extra_population=int(d.loc[positive_ids[extra_pos],'Population'].sum()),
                    extra_cluster_counts=json.dumps(np.bincount(a[extra_pos],minlength=k).tolist()),
                    **comparison(a[positive_pos],b,k)))
    save('CLUSTER_MEMBERSHIP_COMPARISONS.csv',compare_rows)
    save('CLUSTER_MEMBERSHIP_TRANSITIONS.csv',transitions)
    save('COHORT_SENSITIVITY.csv',cohort_rows)
    return objects, seed_stability


def stress_tests(d,objects,stability):
    assignments=[]
    for cohort,sub in cohorts(d).items():
        cutoff=sub.BUILDVALUE.quantile(.99)
        train=sub.BUILDVALUE.lt(cutoff).to_numpy()
        for spec,budgets in SPEC['specifications'].items():
            for k in SPEC['k_values']:
                labels,*_=fit(sub,budgets,k,42,train)
                ref=objects[(cohort,spec,k,42)]
                row=dict(cohort=cohort,specification=spec,k=k,kind='asset_P99_leaveout',seed_a=42,seed_b=42,
                    n_training=int(train.sum()),n_heldout=int((~train).sum()),**comparison(ref,labels,k))
                row['heldout_ARI']=adjusted_rand_score(ref[~train],labels[~train])
                row['training_ARI']=adjusted_rand_score(ref[train],labels[train])
                stability.append(row)
                assignments.extend(dict(cohort=cohort,specification=spec,k=k,kind='asset_P99_leaveout',block=-1,
                    tract_id=t,heldout=not train[i],reference_cluster=int(ref[i]),perturbed_cluster=int(labels[i]))
                    for i,t in enumerate(sub.index))
    sub=cohorts(d)['positive_population']
    block=(sub.utm_x_m.ge(sub.utm_x_m.median()).astype(int)+2*sub.utm_y_m.ge(sub.utm_y_m.median()).astype(int)).to_numpy()
    save('SPATIAL_SUPPORT_AND_BLOCKS.csv',sub[['INTPTLAT','INTPTLON','utm_x_m','utm_y_m','source_polygon_valid']].assign(block=block).reset_index())
    for spec,budgets in SPEC['specifications'].items():
        for k in SPEC['k_values']:
            ref=objects[('positive_population',spec,k,42)]
            for held in range(4):
                train=block!=held
                labels,*_=fit(sub,budgets,k,42,train)
                row=dict(cohort='positive_population',specification=spec,k=k,kind='spatial_leave_quadrant_out',
                    block=held,seed_a=42,seed_b=42,n_training=int(train.sum()),n_heldout=int((~train).sum()),
                    **comparison(ref,labels,k),heldout_ARI=adjusted_rand_score(ref[~train],labels[~train]),
                    training_ARI=adjusted_rand_score(ref[train],labels[train]))
                stability.append(row)
                assignments.extend(dict(cohort='positive_population',specification=spec,k=k,kind='spatial_leave_quadrant_out',
                    block=held,tract_id=t,heldout=not train[i],reference_cluster=int(ref[i]),perturbed_cluster=int(labels[i]))
                    for i,t in enumerate(sub.index))
            print(f'stress tests {spec} k={k} complete',flush=True)
    save('SPATIAL_AND_SEED_STABILITY.csv',stability)
    save('STRESS_TEST_MEMBERSHIPS.csv',assignments)


def initial_influence(d):
    rows=[]
    for cohort,sub in cohorts(d).items():
        a=sub.Init_Supply.to_numpy()
        z=(a-a.mean())/a.std(ddof=0)
        p99=np.quantile(a,.99)
        for subset,mask in [('all',np.ones(len(a),bool)),('exact_zero',a==0),('nonzero',a>0),('Init_P99',a>=p99)]:
            rows.append(dict(cohort=cohort,subset=subset,n=int(mask.sum()),
                fraction_of_Init_total_SS=np.square(z[mask]).sum()/np.square(z).sum(),
                fraction_of_entire_A_total_SS=(1/9)*np.square(z[mask]).sum()/len(a),
                z_min=z[mask].min(),z_max=z[mask].max(),Init_mean=a[mask].mean(),Init_max=a[mask].max()))
    save('INIT_SUPPLY_DISTANCE_LEVERAGE.csv',rows)


def main():
    begin=time.perf_counter()
    d=frame('TRACT_FEATURES_VERIFIED_2315.csv').set_index('tract_id').sort_index()
    for name,budgets in SPEC['specifications'].items():
        assert abs(sum(budgets.values())-1)<1e-12
        assert all(abs(sum(w for c,w in budgets.items() if SPEC['domains'][c]==q)-1/3)<1e-12 for q in ['RQ1','RQ2','RQ3'])
    print('source-verified input and registered budgets accepted',flush=True)
    information_audit(d)
    initial_influence(d)
    objects,stability=clustering(d)
    stress_tests(d,objects,stability)
    dump('ANALYSIS_EXECUTION.json',dict(status='completed exploratory diagnostics only',
        preregistration_sha256=sha(OUT/'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json'),
        input_sha256=sha(OUT/'TRACT_FEATURES_VERIFIED_2315.csv'),
        registered_fits=len(cohorts(d))*len(SPEC['specifications'])*len(SPEC['k_values'])*len(SPEC['seeds']),
        stress_fits=40+80,elapsed_seconds=time.perf_counter()-begin,
        numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,
        any_new_physical_simulation=False,formal_stage7_promoted=False))
    print(f'All diagnostics completed in {time.perf_counter()-begin:.1f}s',flush=True)


if __name__=='__main__':
    main()
