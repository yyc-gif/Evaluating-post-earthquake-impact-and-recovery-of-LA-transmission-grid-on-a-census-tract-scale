"""Independent numerical arithmetic checks; no sklearn fitting or service simulation."""
import json
from itertools import combinations
from scipy.spatial.distance import cdist
from scipy import sparse
from common import *


def main():
    start=json.loads(lp(OUT/'STARTING_STATUS_AND_PRESERVATION.json').read_text())
    assert {p:sha(SOURCE_ROOT/p) for p in start['protected_files']}==start['protected_files']
    s=sources()
    assert {p:sha(s.source(p,AUTH)) for p in start['prior_package_files']}==start['prior_package_files']
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode()==start['unrelated_source_status']
    full=frame('VERIFIED_DESCRIPTORS_2315.csv').set_index('tract_id')
    values=frame('MULTIPOLICY_RQ2_TRACT_VALUES.csv')
    z=np.load(lp(OUT/'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'))
    order=pd.Index(z['tract_ids'],name='tract_id')
    assert len(order)==2315 and order.is_unique and order.str.fullmatch(r'\d{11}').all()
    np.testing.assert_array_equal(order,full.index)
    w=sparse.csr_matrix((z['mapping_data'],z['mapping_indices'],z['mapping_indptr']),shape=z['mapping_shape'])
    mass=np.asarray(w.sum(1)).ravel()
    np.testing.assert_allclose(mass,1,rtol=0,atol=1e-12)
    totals=np.stack([(w@x.T).T/mass for x in z['station_loss']])
    pidx={p:i for i,p in enumerate(z['policies'])}
    old=frame('VERIFIED_DESCRIPTORS_2315.csv')
    maxerr=0
    for name,ps in SETS.items():
        selected=totals[[pidx[p] for p in ps]]
        mean=selected.mean(1)
        u=totals[pidx['unconstrained']].mean(0)
        # Separate arithmetic order from the construction code.
        delta=mean-u[None,:]
        md=delta.sum(0)/len(ps)
        sd=np.sqrt(((delta-md)**2).sum(0)/len(ps))
        within=np.mean(np.sqrt(((selected-selected.mean(0))**2).sum(0)/len(ps)),axis=0)
        row=values.query('policy_set==@name').set_index('tract_id').reindex(order)
        for v,expected in [('B_Unconstrained',u),('MeanDelta',md),('PolicySD',sd),('MeanTotalBurden',mean.mean(0)),('MeanWithinRealizationPolicySD',within)]:
            e=np.max(np.abs(row[v].to_numpy()-expected)); maxerr=max(maxerr,e)
            assert e<1e-10,(name,v,e)
        assert (within+1e-10>=sd).all()
    np.testing.assert_allclose(w@z['initial_station_e_mean']/mass,full.Init_Supply,rtol=0,atol=1e-12)
    qa=json.loads(lp(OUT/'POLICY_ENSEMBLE_QA.json').read_text())
    assert sha(OUT/'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz')==qa['snapshot_sha256']
    raw_checks=[]
    for p in POLICIES:
        pre=FORMAL+('Equity_Amendment/Offline/' if p=='vulnerability-first' else 'Formal_Offline_Evaluation/')+f'2pc50__C57_D1__{p}'
        meta=json.loads(s.archive(pre+'__EVALUATION.json').read_text())
        with np.load(s.archive(pre+'__INTEGRALS.npz',meta['integral_sha256'])) as zz:
            np.testing.assert_array_equal(z['physical_hashes'],zz['physical_hashes'])
            np.testing.assert_array_equal(z['station_ids'],zz['station_ids'].astype(str))
            np.testing.assert_array_equal(z['station_loss'][pidx[p]],zz['G1_BASELINE_050__L_total'])
            for m in [0,499,999]:
                manual=np.array([np.dot(w.getrow(i).toarray().ravel(),zz['G1_BASELINE_050__L_total'][m])/mass[i] for i in [0,1157,2314]])
                np.testing.assert_allclose(manual,zz['M1_UTILITY_003__normalized_burden_hr'][m,[0,1157,2314]],rtol=0,atol=1e-10)
                raw_checks.append(dict(policy=p,realization_id=z['realization_ids'][m],manual_three_tract_check='PASS'))
    save('INDEPENDENT_RAW_ARCHIVE_SPOT_CHECKS.csv',raw_checks)
    fits=frame('A_VS_P2_VS_P3_CLUSTERING_RESULTS.csv')
    labels=np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz')); mats=np.load(lp(OUT/'VERIFIED_WEIGHTED_MATRICES.npz'))
    d=dataset(); np.testing.assert_array_equal(labels['tract_ids'],d.index)
    np.testing.assert_array_equal(mats['tract_ids'],d.index)
    keys={k:i for i,k in enumerate(labels['keys'])}; checked=0; maxsil=0
    for (sp,name,scaling),part in fits.groupby(['specification','policy_set','scaling'],sort=False):
        dd=dataset(name); cs=columns(sp); ref=dataset() if scaling=='fixed_main5' else dd
        raw=dd[cs].to_numpy(float); reference=ref[cs].to_numpy(float)
        budgets=weights(sp)
        for domain in [RQ1,RQ3,[v for v in cs if v not in RQ1+RQ3]]:
            assert abs(budgets[[v in domain for v in cs]].sum()-1/3)<1e-14
        x=(raw-reference.mean(0))/reference.std(0,ddof=0)*np.sqrt(budgets)
        np.testing.assert_array_equal(x,mats[f'{sp}__{name}__{scaling}'])
        distances=cdist(x,x); np.fill_diagonal(distances,0)
        for row in part.itertuples():
            idx=keys[key(sp,name,scaling,row.k,row.seed)]; lab=labels['labels'][idx]
            assert np.array_equal(np.unique(lab),np.arange(row.k))
            centers=np.vstack([x[lab==c].mean(0) for c in range(row.k)])
            wcss=sum(np.square(x[i]-centers[lab[i]]).sum() for i in range(len(x)))
            assert abs(wcss-row.WCSS)<1e-9
            assert hashlib.sha256(x.astype('<f8').tobytes()).hexdigest()==row.matrix_sha256
            if row.k>1:
                sizes=np.bincount(lab)
                av=np.column_stack([distances[:,lab==c].sum(1)/sizes[c] for c in range(row.k)])
                ii=np.arange(len(lab)); own=av[ii,lab]*sizes[lab]/np.maximum(sizes[lab]-1,1)
                av[ii,lab]=np.inf; other=av.min(1)
                sil=(other-own)/np.maximum(other,own); sil[sizes[lab]==1]=0
                error=np.max(np.abs(sil-labels['silhouette'][idx])); maxsil=max(maxsil,error)
                assert error<1e-10 and abs(sil.mean()-row.mean_silhouette)<1e-10
            checked+=1
        print('independent cdist silhouette QA',sp,name,scaling,flush=True)
    spatial=np.load(lp(OUT/'SPATIAL_REFIT_LABELS.npz'))
    np.testing.assert_array_equal(spatial['tract_ids'],d.index)
    blocks=((d.utm_x_m>=d.utm_x_m.median()).astype(int)+2*(d.utm_y_m>=d.utm_y_m.median()).astype(int)).to_numpy()
    centers_saved={}
    from sklearn.cluster import KMeans
    from scipy.optimize import linear_sum_assignment
    for kk,pred in zip(spatial['keys'],spatial['labels']):
        sp,name,scaling,kpart,bpart=kk.split('__'); k=int(kpart[1:]); block=int(bpart[5:]); train=blocks!=block
        xx=dataset(name)[columns(sp)].to_numpy(float)
        xx=(xx-xx[train].mean(0))/xx[train].std(0)*np.sqrt(weights(sp))
        # Lloyd may stop at tolerance before final assigned means equal its saved centers.
        # Replay the exact registered fit to verify the actual prediction centers.
        replay=KMeans(n_clusters=k,random_state=42,**PARAMS).fit(xx[train])
        raw_labels=replay.predict(xx)
        contingency=np.zeros((k,k),int)
        np.add.at(contingency,(pred,raw_labels),1)
        aa,bb=linear_sum_assignment(-contingency)
        remap=dict(zip(bb,aa))
        np.testing.assert_array_equal(np.array([remap[c] for c in raw_labels]),pred)
        centers=np.empty_like(replay.cluster_centers_)
        for c in range(k):centers[remap[c]]=replay.cluster_centers_[c]
        centers_saved[kk]=centers
        np.testing.assert_array_equal(cdist(xx,centers).argmin(1),pred)
    np.savez_compressed(lp(OUT/'VERIFIED_SPATIAL_REFIT_CENTERS.npz'),**centers_saved)
    assert full.Population.gt(0).sum()==2299 and full.Population.eq(0).sum()==16
    assert full.loc[full.Population.gt(0),'additional_zero_housing_positive_population'].sum()==8
    dump('INDEPENDENT_QA_RESULTS.json',dict(status='PASS',independently_checked_fits=checked,
        full_cdist_silhouette_max_error=maxsil,ensemble_arithmetic_max_error_hr=maxerr,
        independently_checked_spatial_predictions=len(spatial['keys']),raw_integral_spot_checks=len(raw_checks),
        spatial_verification='Exact deterministic replay of registered fits; scipy nearest saved-center checks. No new fit specification.',
        protected_scientific_files_unchanged=len(start['protected_files']),prior_package_files_unchanged=len(start['prior_package_files']),
        unrelated_source_git_status_unchanged=True,source_archive_pairing_reverified=qa['verified_event_payloads'],
        no_new_physical_simulation=True,no_formal_stage7_promotion=True))
    save('SOURCE_HASH_VERIFICATION_INDEPENDENT.csv',s.records)


if __name__=='__main__': main()
