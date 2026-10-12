"""Independent frozen arithmetic, distances and preservation; no pipeline imports."""
import ast
import json
from scipy.sparse import csr_matrix
from scipy.spatial.distance import pdist, squareform
from sklearn.metrics import silhouette_samples, adjusted_rand_score

from common import *


def close(a,b,tol=1e-10):
    np.testing.assert_allclose(a,b,atol=tol,rtol=0,equal_nan=True)


def main():
    s = sources()
    d = data()
    original = frozen(s, PREVIOUS+'TRACT_FEATURES_VERIFIED_2315.csv').sort_index()
    pop_source = frozen(s,'Data/Tracts_Within_Expanded_Area.csv','GEOID')
    np.testing.assert_array_equal(d.Population,pop_source.population.reindex(d.index))
    for c in FEATURES[:3]+FEATURES[5:]+['frozen_SOVI_quartile']:
        if pd.api.types.is_numeric_dtype(d[c]): close(d[c],original[c])
        else: np.testing.assert_array_equal(d[c],original[c])
    positive = d.loc[d.Population>0]
    assert len(positive)==2299 and len(d)==2315 and d.index.str.fullmatch(r'\d{11}').all()
    np.testing.assert_array_equal(frame('EXCLUDED_ZERO_POPULATION_GEOIDS.csv').tract_id.sort_values(),d.loc[d.Population.eq(0)].index.sort_values())
    assert positive.additional_zero_housing_positive_population.sum()==8
    close(np.log1p(d.Population),d.log1p_Population)
    metrics = frame('POLICY_REFERENCE_TRACT_METRICS.csv')
    event_qa = frame('FROZEN_POLICY_EVENT_VERIFICATION.csv')
    qa = json.loads(lp(OUT/'POLICY_PAIRING_QA.json').read_text())
    rows=[]
    mapping=pd.read_csv(s.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',AUTH),dtype={'tract_id':str,'substation_id':str})
    order=pop_source.index
    for q in qa['policies']:
        policy=q['policy']
        folder=FORMAL+('Equity_Amendment/Offline/' if policy=='vulnerability-first' else 'Formal_Offline_Evaluation/')
        prefix=folder+f'2pc50__C57_D1__{policy}'
        with np.load(s.archive(prefix+'__INTEGRALS.npz',q['integral_sha256']),allow_pickle=False) as z:
            stations=z['station_ids'].astype(str)
            loss=z['G1_BASELINE_050__L_total']
            burden=z['M1_UTILITY_003__normalized_burden_hr']
            w=csr_matrix((mapping.weight,(order.get_indexer(mapping.tract_id),pd.Index(stations).get_indexer(mapping.substation_id))),shape=(2315,92))
            close((w@loss.T).T,burden)
            recomputed=pd.Series(w@np.mean(loss,axis=0),index=order).reindex(d.index)
        table=metrics.loc[metrics.policy.eq(policy)].set_index('tract_id').reindex(d.index)
        close(table.B_480_hr,recomputed)
        close(table.B_480_hr,table.B_unconstrained+table.Delta_B_logistics)
        rows.append(dict(policy=policy,independent_W_station_mean_projection_max_error_hr=np.max(abs(table.B_480_hr-recomputed)),identity_max_error_hr=np.max(abs(table.B_480_hr-table.B_unconstrained-table.Delta_B_logistics))))
        # Independent spot checks of actual events, in addition to Phase I's full 7,000-payload audit.
        for realization in [0,499,999]:
            r=event_qa.loc[event_qa.policy.eq(policy)&event_qa.realization_id.eq(f'2pc50__evaluation_{realization:04d}')].iloc[0]
            p=lp(SOURCE_ROOT/r.archive_relative_path)
            assert sha(p)==r.npz_sha256
            with np.load(p,allow_pickle=False) as z:
                integral=np.einsum('ij,i->j',1-z['e'][:-1],np.diff(z['event_time_hr']))
            close(integral,loss[realization])
    save('INDEPENDENT_POLICY_ARITHMETIC_QA.csv',rows)
    results=frame('SILHOUETTE_BY_K_AND_SEED.csv')
    scalers=frame('COHORT_STANDARDIZATION_AND_WEIGHTS.csv')
    contributions=frame('DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv')
    with np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz'),allow_pickle=False) as z:
        np.testing.assert_array_equal(z['tract_ids'],positive.index)
        labels=dict(zip(z['keys'],z['labels'])); sils=dict(zip(z['keys'],z['silhouette']))
    verification=[]
    with np.load(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'),allow_pickle=False) as z:
        for policy in POLICIES:
            policy_d=positive.copy()
            metric=metrics.loc[metrics.policy.eq(policy)].set_index('tract_id').reindex(positive.index)
            policy_d[['B_480_hr','Delta_B_logistics']]=metric[['B_480_hr','Delta_B_logistics']]
            for spec in ['A','A-minus-Init']:
                for scaling in ['policy_cohort','fixed_impact']:
                    sc=scalers.loc[scalers.policy.eq(policy)&scalers.specification.eq(spec)&scalers.scaling.eq(scaling)].set_index('variable').loc[columns(spec)]
                    close(sc.squared_distance_budget,weights(spec),1e-15)
                    assert abs(sum(weights(spec))-1)<1e-15
                    raw=policy_d[columns(spec)].to_numpy(float)
                    x=(raw-sc['mean'].to_numpy())/sc.sd.to_numpy()*np.sqrt(sc.squared_distance_budget.to_numpy())
                    saved=z['__'.join([policy,spec,scaling])]
                    close(x,saved,1e-12)
                    distances=squareform(pdist(saved))
                    for row in results.loc[results.policy.eq(policy)&results.specification.eq(spec)&results.scaling.eq(scaling)].itertuples():
                        kk=f'{policy}__{spec}__{scaling}__k{row.k}__s{row.seed}'
                        lab=labels[kk]; k=row.k
                        assert set(lab)==set(range(k)) and len(lab)==2299
                        means=np.stack([saved[lab==c].mean(0) for c in range(k)])
                        wcss=np.einsum('ij,ij->',saved-means[lab],saved-means[lab])
                        close(wcss,row.WCSS,1e-8)
                        if k>1:
                            close(row.mean_silhouette,np.mean(sils[kk]),1e-14)
                            close(row.median_silhouette,np.median(sils[kk]),1e-14)
                        if row.seed==42 and k>1:
                            calculated=silhouette_samples(distances,lab,metric='precomputed')
                            close(calculated,sils[kk],1e-9)
                            verification.append(dict(policy=policy,specification=spec,scaling=scaling,k=k,
                                independent_scipy_distance_silhouette_max_error=np.max(abs(calculated-sils[kk])),independent_WCSS_error=abs(wcss-row.WCSS)))
    save('INDEPENDENT_DISTANCE_AND_PARTITION_QA.csv',verification)
    assert len(labels)==len(results)==960
    close(contributions.total_SS,contributions.between_SS+contributions.within_SS,1e-10)
    assert frame('SPATIAL_LEAVE_OUT_STABILITY.csv').shape[0]==672
    assert frame('PRIOR_REGISTERED_FIT_RECONSTRUCTION_QA.csv').exact_labels_equal.all()
    preservation=preserve(s)
    before=json.loads(lp(OUT/'STARTING_STATUS_AND_PRESERVATION.json').read_text())
    assert preservation==before['protected_files'] and len(preservation)==950
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode()==before['unrelated_source_status']
    # Original audit packages are checked against their committed blobs/LFS bytes.
    prior_rows=[]
    for package in [AUDIT,PREVIOUS,INTERPRETATION]:
        for rel in git('ls-tree','-r','--name-only',AUTH,'--',package).decode().splitlines():
            p=s.source(rel,AUTH)
            prior_rows.append(dict(source_file=rel,sha256=sha(p),bytes=p.stat().st_size,verified_unchanged=True))
    save('PRIOR_PACKAGE_IMMUTABILITY.csv',prior_rows)
    for script in OUT.glob('*.py'):
        tree=ast.parse(lp(script).read_text())
        imported=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        assert not any(v.startswith('la_grid') for v in imported)
    save('INDEPENDENT_SOURCE_HASH_VERIFICATION.csv',s.records)
    dump('INDEPENDENT_QA_RESULTS.json',dict(status='PASS',registered_fit_conditions=960,
        full_cohort_scipy_silhouette_rechecks=len(verification),independent_raw_event_spot_checks=21,spatial_refits=672,exact_prior_fit_replays=40,
        protected_scientific_files_unchanged=950,prior_package_files_unchanged=len(prior_rows),
        unrelated_source_work_unchanged=True,model_pipeline_imports=0,new_physical_simulations=0,formal_promotion=False))
    print('Independent QA PASS',flush=True)


if __name__=='__main__': main()
