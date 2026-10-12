"""Independent identities and arithmetic, without importing analysis or models."""
import ast
import hashlib
import json
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from common import *


def close(x,y,tolerance=1e-10):
    assert np.allclose(x,y,rtol=0,atol=tolerance,equal_nan=True),float(np.nanmax(np.abs(np.asarray(x)-np.asarray(y))))


def main():
    s=sources()
    authority=frozen(s,PREVIOUS+'TRACT_FEATURES_VERIFIED_2315.csv').sort_index()
    raw=frozen(s,'Data/Tracts_Within_Expanded_Area.csv',key='GEOID')
    assert len(authority)==2315 and authority.index.is_unique
    assert np.array_equal(authority.Population,raw.population.reindex(authority.index))
    positive=authority.loc[raw.population.reindex(authority.index)>0]
    excluded=authority.index.difference(positive.index)
    assert len(positive)==2299 and len(excluded)==16
    assert positive.index.str.fullmatch(r'\d{11}').all()
    assert positive.index.intersection(['06037189703','06037301601','06037301602','06037404600']).size==4
    d=frame('VERIFIED_INTERPRETATION_TRACT_VALUES.csv').set_index('tract_id')
    assert d.index.equals(positive.index)
    for col in authority.columns:
        if pd.api.types.is_bool_dtype(positive[col]):assert np.array_equal(d[col],positive[col]),col
        elif pd.api.types.is_numeric_dtype(positive[col]):
            # Round-trip CSV parsing can differ by a few ULPs for large values.
            scale=float(positive[col].abs().max())
            close(d[col],positive[col],max(1e-10,4*np.spacing(scale)))
        else:assert d[col].fillna('').equals(positive[col].fillna('')),col
    assert not d.T80_unreached.any() and d.T80.lt(480).all()
    assert d.additional_zero_housing_positive_population.sum()==8
    spec=json.loads(s.source(PREVIOUS+'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json',AUTH).read_text())
    labels=frozen(s,PREVIOUS+'CLUSTER_MEMBERSHIPS_POSITIVE_POPULATION.csv').reindex(d.index)
    for name in SPECS:
        b=spec['specifications'][name]
        for domain in ['RQ1','RQ2','RQ3']:
            assert np.isclose(sum(v for c,v in b.items() if spec['domains'][c]==domain),1/3)
        assert d[list(b)].notna().all().all() and np.isfinite(d[list(b)]).all().all()
        assert not {'T80','B_unconstrained','EAL_SCORE','EAL_VALT','RISK_SCORE'}.intersection(b)
    nri=frozen(s,'Data/NRI_Table_CensusTracts_California.csv',key='TRACTFIPS').reindex(d.index)
    assert np.array_equal(d.BUILDVALUE,nri.BUILDVALUE) and nri.NRI_VER.eq('Mar-23').all()
    close(np.log1p(d.BUILDVALUE),d.log1p_BUILDVALUE,1e-14)
    close(np.log1p(d.Population),d.log1p_Population,1e-14)
    with np.load(lp(OUT/'FROZEN_INITIAL_STATION_STATES.npz'),allow_pickle=False) as z:
        ids=z['station_ids'].astype(str);rids=z['realization_ids'].astype(str)
        f,F,C,e,ds=[z[key].copy() for key in ['f','F','C','e','ds']]
    assert all(v.shape==(1000,92) for v in [f,F,C,e,ds])
    with np.load(s.source(FORMAL+'Stage 1 Output_expanded/physical_inputs_2pc50.npz',AUTH),allow_pickle=False) as z:
        assert np.array_equal(ids,z['station_ids'].astype(str))
        assert np.array_equal(ds,z['evaluation_ds'].T)
        durations=z['evaluation_duration'].copy()
    manifest=frozen(s,FORMAL+'Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv',key='realization_id')
    manifest=manifest.loc[manifest.scenario.eq('2pc50')&manifest.split.eq('evaluation')].sort_index()
    assert np.array_equal(rids,manifest.index.to_numpy())
    fm=json.loads(s.source(FORMAL+'Stage 1 Output_expanded/PHYSICAL_INPUTS_FROZEN.json',AUTH).read_text())
    state_records=frame('FROZEN_INITIAL_ARCHIVE_VERIFICATION.csv').set_index('realization_id')
    prior_verification=frozen(s,AUDIT+'FROZEN_REALIZATION_VERIFICATION.csv',key='realization_id')
    chain=hashlib.sha256()
    for i,rid in enumerate(rids):
        ph=hashlib.sha256(('\n'.join(ids)+'\n').encode()+ds[i].astype('<i8').tobytes()+durations[:,i].astype('<f8').tobytes()).hexdigest()
        assert ph==manifest.loc[rid,'physical_input_hash']==fm['sample_hashes'][rid]
        rec=state_records.loc[rid]
        assert rec.physical_hash==ph and rec.manifest_sha256==prior_verification.loc[rid,'manifest_sha256']
        stem=FORMAL+'Formal_Trajectories/2pc50/C57_D1/'
        jp=s.archive(stem+'direct-community/'+rid+'.json',rec.manifest_sha256)
        jb=jp.read_bytes();chain.update(hashlib.sha256(jb).digest());meta=json.loads(jb)
        assert meta['identity']['physical_sample_hash']==ph
        npz=s.archive(stem+'direct-community/'+rid+'.npz',meta['npz_sha256'])
        with np.load(npz,allow_pickle=False) as archive:
            assert archive['event_time_hr'][0]==0 and np.array_equal(archive['station_ids'].astype(str),ids)
            for key,arr in [('f',f),('F',F),('C',C),('e',e)]:assert np.array_equal(archive[key][0],arr[i])
        # Confirm the applicable Impact-first record is the identical existing payload.
        imp=json.loads(s.archive(stem+'impact-first/'+rid+'.json').read_text())
        assert imp['identity']['physical_sample_hash']==ph
        assert imp['npz_sha256']==meta['npz_sha256']
        s.archive(stem+'impact-first/'+rid+'.npz',imp['npz_sha256'])
        if i%250==0:print('independent frozen sample verification',i,flush=True)
    previous=json.loads(s.source(AUDIT+'RECOVERY_PAIRING_QA.json',AUTH).read_text())
    assert chain.hexdigest()==previous['manifest_chain_sha256']
    assert np.array_equal(f,np.array([1,.5,.09,.04,.03])[ds])
    assert np.array_equal(F,f>=.5) and np.array_equal(e,f*F*C)
    assert not np.any(C.astype(bool)&~F.astype(bool))
    core=frozen(s,'Data/source_nodes_core_expanded.csv',key='ID')
    core_ids=set(core.index[core.level.eq('Core')])
    edges=pd.read_csv(s.source('Data/substation_graph_CEC_edges_expanded.csv',AUTH),dtype={'u':str,'v':str})
    edge_set=set(tuple(sorted(x)) for x in edges[['u','v']].itertuples(index=False,name=None))
    rid_index={rid:i for i,rid in enumerate(rids)};sid_index={sid:i for i,sid in enumerate(ids)}
    cert=frame('SAVED_POSITIVE_SOURCE_PATH_CERTIFICATES.csv')
    assert len(cert)==int(C.sum())
    for _,row in cert.iterrows():
        path=json.loads(row.path_station_ids);i=rid_index[row.realization_id]
        assert path[0]==row.substation_id and path[-1] in core_ids
        assert all(F[i,sid_index[sid]] for sid in path)
        assert all(tuple(sorted(pair)) in edge_set for pair in zip(path,path[1:]))
        assert C[i,sid_index[path[0]]] and len(path)-1==row.path_hops
    mapping=pd.read_csv(s.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',AUTH),dtype={'tract_id':str,'substation_id':str})
    ti={v:i for i,v in enumerate(d.index)}
    mm=mapping.loc[mapping.tract_id.isin(d.index)].copy()
    W=csr_matrix((mm.weight,([ti[t] for t in mm.tract_id],[sid_index[x] for x in mm.substation_id])),shape=(2299,92))
    close(np.asarray(W.sum(1)).ravel(),np.ones(2299),1e-12)
    close(W@e.mean(0),d.Init_Supply,1e-12)
    central=frozen(s,FORMAL+'Stage 2 Output_expanded/impact_centrality_substations.csv',key='substation_id')
    close(W@central.impact_centrality.reindex(ids),d.Grid_Impact)
    close(np.asarray(W.multiply(W).sum(1)).ravel(),d.Redundancy_HHI,1e-12)
    integrals={}
    for policy in ['impact-first','unconstrained','direct-community']:
        stem=FORMAL+'Formal_Offline_Evaluation/2pc50__C57_D1__'+policy
        meta=json.loads(s.archive(stem+'__EVALUATION.json').read_text())
        archive=s.archive(stem+'__INTEGRALS.npz',meta['integral_sha256'])
        with np.load(archive,allow_pickle=False) as z:
            assert np.array_equal(z['station_ids'].astype(str),ids)
            assert np.array_equal(z['physical_hashes'].astype(str),manifest.physical_input_hash.to_numpy())
            integrals[policy]=W@z['G1_BASELINE_050__L_total'].mean(0)
            if policy=='impact-first':
                for key,col in [('L_self','self_loss_hr'),('L_threshold','threshold_loss_hr'),('L_source','source_loss_hr')]:
                    close(W@z['G1_BASELINE_050__'+key].mean(0),d[col])
    close(integrals['impact-first'],d.B_480_hr)
    close(integrals['unconstrained'],d.B_unconstrained)
    close(integrals['impact-first']-integrals['unconstrained'],d.Delta_B_logistics)
    assert np.array_equal(integrals['impact-first'],integrals['direct-community'])
    close(d[['self_loss_hr','threshold_loss_hr','source_loss_hr']].sum(1),d.B_480_hr)
    rare=d.index[labels.A__k4__s42.eq(0)]
    listed=frame('THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv').set_index('tract_id')
    assert len(rare)==34 and set(listed.index)==set(rare)
    assert set(d.Init_Supply.nlargest(23).index).issubset(rare)
    assert not d.loc[rare,'additional_zero_housing_positive_population'].any()
    identity=frame('THIRTYFOUR_TRACT_IDENTITY_AND_STABILITY.csv')
    stress=pd.read_csv(s.source(PREVIOUS+'STRESS_TEST_MEMBERSHIPS.csv',AUTH),dtype={'tract_id':str})
    for _,row in identity.iterrows():
        if row.kind=='registered':y=labels[f'{row.specification}__k{int(row.k)}__s{int(row.seed)}']
        else:
            take=stress[(stress.cohort=='positive_population')&(stress.specification==row.specification)&
                (stress.k==row.k)&(stress.kind==row.kind)&(stress.block==row.block)]
            y=take.set_index('tract_id').perturbed_cluster
        members=set(y.index[y.eq(row.matched_cluster)]);ref=set(rare)
        assert set(json.loads(row.retained_GEOIDs))==ref&members
        assert set(json.loads(row.lost_GEOIDs))==ref-members
        assert set(json.loads(row.newly_added_GEOIDs))==members-ref
        close(row.Jaccard,len(ref&members)/len(ref|members),1e-14)
        assert row.retained==len(ref&members) and row.n_matched_cluster==len(members)
    dep=frame('THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv')
    m=mm[mm.tract_id.isin(rare)].copy()
    m['effective']=m.substation_id.map(pd.Series(e.mean(0),index=ids))
    m['contribution']=m.weight*m.effective
    total=m.contribution.sum();qpart=m[m.substation_id.eq('308581')]
    assert m.groupby('tract_id').apply(lambda x:x.sort_values('weight').iloc[-1].substation_id,include_groups=False).eq('308581').all()
    expected_q=dep.loc[dep.substation_id.eq('308581'),'initial_service_contribution'].sum()/dep.initial_service_contribution.sum()
    close(qpart.contribution.sum()/total,expected_q,1e-12)
    j=sid_index['308581'];assert F[:,j].sum()==40 and C[:,j].sum()==40
    assert np.array_equal(np.bincount(ds[:,j],minlength=5),[9,31,78,510,372])
    close(e[:,j].mean(),.0245,1e-14)
    ri=np.array([ti[t] for t in rare]);initial=W[ri]@e.T
    assert np.median(initial,axis=1).max()==0
    rows=frame('THIRTYFOUR_REALIZATION_INITIAL_SERVICE.csv').pivot(index='tract_id',columns='realization_id',values='initial_service').reindex(index=rare,columns=rids)
    close(rows,initial,1e-12)
    profiles=frame('CLUSTER_ORIGINAL_UNIT_PROFILES.csv')
    communities=frame('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv')
    variation=frame('DOMAIN_AND_COORDINATE_OBSERVED_VARIATION.csv')
    scaler=frozen(s,PREVIOUS+'COHORT_STANDARDIZATION_AND_WEIGHTS.csv',key='variable')
    verified=[]
    for model in SPECS:
        b=spec['specifications'][model];cols=list(b)
        x=(d[cols]-d[cols].mean())/d[cols].std(ddof=0)*np.sqrt(list(b.values()))
        for k in KS:
            for seed in SEEDS:
                y=labels[f'{model}__k{k}__s{seed}']
                assert set(y)==set(range(k))
                pp=profiles[(profiles.specification==model)&(profiles.k==k)&(profiles.seed==seed)]
                cc=communities[(communities.specification==model)&(communities.k==k)&(communities.seed==seed)].set_index('diagnostic_cluster')
                within=np.zeros(len(cols))
                for cl in range(k):
                    group=d.loc[y.eq(cl)]
                    v=x.loc[y.eq(cl)].to_numpy();within+=np.square(v-v.mean(0)).sum(0)
                    assert cc.loc[cl,'n_tracts']==len(group) and cc.loc[cl,'population']==group.Population.sum()
                    for quart in ['Q1','Q2','Q3','Q4']:assert cc.loc[cl,quart+'_tracts']==group.frozen_SOVI_quartile.eq(quart).sum()
                    for _,row in pp[pp.diagnostic_cluster==cl].iterrows():
                        val=group[row.variable]
                        close([row['mean'],row['median'],row.p10,row.p90],[val.mean(),val.median(),val.quantile(.1),val.quantile(.9)],1e-6 if row.variable=='BUILDVALUE' else 1e-10)
                total=np.square(x).sum(0)
                vv=variation[(variation.specification==model)&(variation.k==k)&(variation.seed==seed)].set_index('coordinate').reindex(cols)
                close(total,vv.total_SS,1e-9);close(within,vv.within_SS,1e-9);close(total-within,vv.between_SS,1e-9)
                saved=scaler[(scaler.cohort=='positive_population')&(scaler.specification==model)&(scaler.k==k)&(scaler.seed==seed)].reindex(cols)
                close(saved['mean'],d[cols].mean(),1e-12);close(saved.sd_ddof0,d[cols].std(ddof=0),1e-12)
                if model in ['A','B'] and k in [4,5]:assert set(d.index[y.eq(0)])==set(rare)
                verified.append(dict(specification=model,k=k,seed=seed,partition_profiles_and_distances_verified=True,new_fit=False))
    alg=frame('INIT_ALGEBRAIC_DISTANCE_DECOMPOSITION.csv')
    for model in ['A','B']:
        z=(d[list(spec['specifications'][model])]-d[list(spec['specifications'][model])].mean())/d[list(spec['specifications'][model])].std(ddof=0)
        for variant in alg.algebraic_variant.unique():
            gg=alg[(alg.specification==model)&(alg.algebraic_variant==variant)]
            for _,row in gg.iterrows():
                expected=34*z.loc[rare,row.coordinate].mean()**2*row.squared_distance_budget
                close(row.rare_centroid_global_between_SS,expected,1e-9)
    for path in [OUT/'analyze_saved.py',OUT/'interpret_reports.py',OUT/'make_review_figures.py']:
        tree=ast.parse(lp(path).read_text(encoding='utf-8'))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        assert not any(isinstance(n.func,ast.Attribute) and n.func.attr in ['fit','fit_predict','run_pipeline'] for n in calls)
    before=json.loads(lp(OUT/'STARTING_STATUS_AND_PRESERVATION.json').read_text())
    assert preserve(s)==before['protected_files'] and len(before['protected_files'])==950
    old=json.loads(lp(OUT/'PRIOR_PACKAGE_IMMUTABILITY.json').read_text())
    assert all(sha(s.source(path,AUTH))==h for path,h in old.items())
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode().splitlines()==before['unrelated_source_status']
    save('INDEPENDENT_PARTITION_PROFILE_VERIFICATION.csv',verified)
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv',[dict(tract_id=t,reason='Frozen formal population = 0',population=0) for t in excluded])
    save('INDEPENDENT_SOURCE_HASH_VERIFICATION.csv',s.records)
    dump('INDEPENDENT_QA_RESULTS.json',dict(status='PASS',cohort=2299,excluded_zero_population=16,
        verified_saved_partitions=len(verified),frozen_samples_independently_verified=1000,
        Impact_first_direct_community_payload_equality=True,all_tract_Init_reprojected=True,
        spectral_impact_HHI_and_burden_components_reprojected=True,physical_hashes_verified=True,
        rare34_exact=True,rare_stress_retained_added_lost_sets_verified=True,rare_Q_contribution_share=float(expected_q),original_quartiles_unchanged=True,source_path_certificates_verified=len(cert),
        protected_scientific_files_unchanged=950,prior_packages_unchanged=len(old),unrelated_source_git_status_unchanged=True,
        new_fits=0,new_damage_scheduling_GA_source_gate_or_recovery_runs=0,formal_promotion=False))
    print('PASS: 60 saved partitions, 1000 samples, source/mapping arithmetic and 950 protected files.',flush=True)


if __name__=='__main__':main()
