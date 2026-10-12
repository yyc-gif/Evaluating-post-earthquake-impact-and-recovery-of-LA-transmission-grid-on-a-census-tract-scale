"""Verify frozen physical authority and derive ensemble features, never trajectories."""
import hashlib
import json
import platform
from scipy import sparse
from common import *


def prefix(policy):
    return FORMAL + ('Equity_Amendment/Offline/' if policy=='vulnerability-first' else 'Formal_Offline_Evaluation/') + f'2pc50__C57_D1__{policy}'


def main():
    s = sources()
    protected = json.loads(s.source(PREVIOUS+'PRESERVATION_AFTER.json', AUTH).read_text())['protected_files']
    assert {p:sha(SOURCE_ROOT/p) for p in protected} == protected
    priors = {}
    for folder in [AUDIT, PREVIOUS, INTERPRETATION, POLICY_AUDIT]:
        for rel in git('ls-tree','-r','--name-only',AUTH,'--',folder).decode().splitlines():
            priors[rel] = sha(s.source(rel, AUTH))
    dump('STARTING_STATUS_AND_PRESERVATION.json', dict(commit=AUTH, branch=git('branch','--show-current').decode().strip(),
         worktree_status=git('status','--porcelain').decode(), source_head=git('rev-parse','HEAD',cwd=SOURCE_ROOT).decode().strip(),
         unrelated_source_status=git('status','--porcelain',cwd=SOURCE_ROOT).decode(),
         protected_files=protected, prior_package_files=priors, python=platform.python_version()))
    full = frozen(s, PREVIOUS+'TRACT_FEATURES_VERIFIED_2315.csv')
    pop = frozen(s, 'Data/Tracts_Within_Expanded_Area.csv','GEOID').population
    full = full.reindex(pop.index)
    full.index.name = 'tract_id'
    np.testing.assert_array_equal(full.Population, pop)
    assert len(full)==2315 and full.index.is_unique and full.index.str.fullmatch(r'\d{11}').all()
    pos = full.Population.gt(0)
    assert pos.sum()==2299 and (~pos).sum()==16
    assert full.loc[pos,'additional_zero_housing_positive_population'].sum()==8
    retain = list(dict.fromkeys(COLS['A']+['Population','T80','T80_unreached','BUILDVALUE','B_unconstrained','frozen_SOVI_quartile',
        'INTPTLAT','INTPTLON','utm_x_m','utm_y_m','hospital_tract','residential_member','additional_zero_housing_positive_population']))
    save('VERIFIED_DESCRIPTORS_2315.csv', full[retain].reset_index())
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv', full.loc[~pos,['Population']].reset_index())
    phy = pd.read_csv(s.source(FORMAL+'Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv',AUTH))
    phy = phy.query("scenario=='2pc50' and split=='evaluation'").sort_values('realization_id')
    with np.load(s.source(FORMAL+'Stage 1 Output_expanded/physical_inputs_2pc50.npz',AUTH)) as z:
        stations, ds, duration = z['station_ids'].astype(str), z['evaluation_ds'], z['evaluation_duration']
    assert ds.shape==duration.shape==(92,1000)
    for m,row in enumerate(phy.itertuples()):
        h = hashlib.sha256(('\n'.join(stations)+'\n').encode()+ds[:,m].astype('<i8').tobytes()+duration[:,m].astype('<f8').tobytes()).hexdigest()
        assert h==row.physical_input_hash and row.realization_id==f'2pc50__evaluation_{m:04d}'
    mapping = pd.read_csv(s.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',AUTH),dtype={'tract_id':str,'substation_id':str})
    assert set(mapping.tract_id)==set(full.index)
    w = sparse.csr_matrix((mapping.weight,(full.index.get_indexer(mapping.tract_id),pd.Index(stations).get_indexer(mapping.substation_id))),shape=(2315,92))
    mass = np.asarray(w.sum(1)).ravel()
    np.testing.assert_allclose(mass,1,rtol=0,atol=1e-12)
    prior = frozen(s,POLICY_AUDIT+'POLICY_REFERENCE_TRACT_METRICS.csv').reset_index()
    prior_event = pd.read_csv(s.source(POLICY_AUDIT+'FROZEN_POLICY_EVENT_VERIFICATION.csv',AUTH)).set_index(['policy','realization_id'])
    initial = np.load(s.source(INTERPRETATION+'FROZEN_INITIAL_STATION_STATES.npz',AUTH))
    e0 = initial['e']
    np.testing.assert_allclose(w@e0.mean(0)/mass,full.Init_Supply,rtol=0,atol=1e-12)
    b, losses, records, event_records, identities = {}, [], [], [], {}
    for p in POLICIES:
        stem = prefix(p)
        meta = json.loads(s.archive(stem+'__EVALUATION.json').read_text())
        ident=meta['identity']
        assert ident['hazard']=='2pc50' and ident['resource_case']=='C57_D1' and ident['H_eval_hr']==480
        assert meta['realization_count']==1000 and 'M1_UTILITY_003' in ident['mapping_cases'] and 'G1_BASELINE_050' in ident['gate_cases']
        with np.load(s.archive(stem+'__INTEGRALS.npz',meta['integral_sha256'])) as z:
            np.testing.assert_array_equal(z['station_ids'].astype(str),stations)
            np.testing.assert_array_equal(z['physical_hashes'],phy.physical_input_hash)
            loss=z['G1_BASELINE_050__L_total'].copy()
            observed=z['M1_UTILITY_003__normalized_burden_hr'].copy()
        projected=(w@loss.T).T/mass
        np.testing.assert_allclose(projected,observed,rtol=0,atol=1e-10)
        assert projected.shape==(1000,2315) and np.isfinite(projected).all() and projected.min()>=0 and projected.max()<=480
        summary=pd.read_parquet(s.archive(stem+'__SUMMARY.parquet',meta['summary_sha256']))
        summary=summary.query("mapping=='M1_UTILITY_003' and gate=='G1_BASELINE_050' and comparison_domain=='mapping_native_domain'").sort_values('realization_id')
        np.testing.assert_array_equal(summary.realization_id,phy.realization_id)
        err_pop=np.max(np.abs(projected@full.Population.to_numpy()/full.Population.sum()-summary.population_weighted_normalized_burden_hr))
        assert err_pop<1e-10 and (summary.horizon_hr==480).all()
        events = FORMAL+('Equity_Amendment/T/2pc50/C57_D1/' if p=='vulnerability-first' else f'Formal_Trajectories/2pc50/C57_D1/{p}/')
        maxevent=0
        for m,row in enumerate(phy.itertuples()):
            rel=events+row.realization_id
            mp=lp(SOURCE_ROOT/(rel+'.json'))
            record=json.loads(mp.read_text())
            ri=record['identity']
            expected=dict(realization_id=row.realization_id,physical_sample_hash=row.physical_input_hash,DS_hash=row.DS_hash,
                duration_hash=row.duration_hash,hazard='2pc50',resource_scenario='C57_D1',event_horizon_hr=480,
                mapping_method_id='M1_UTILITY_003',split='evaluation',strategy=p)
            for k,v in expected.items(): assert ri[k]==v
            common={k:ri[k] for k in ['physical_sample_hash','DS_hash','duration_hash','graph_hash','source_set_hash','crew_roster_hash','directed_travel_hash','matrix_id','event_horizon_hr','mapping_method_id']}
            if p=='unconstrained': identities[row.realization_id]=common
            else: assert common==identities[row.realization_id]
            npz=lp(SOURCE_ROOT/(rel+'.npz'))
            assert sha(mp)==prior_event.loc[(p,row.realization_id),'manifest_sha256']
            assert sha(npz)==record['npz_sha256']==prior_event.loc[(p,row.realization_id),'npz_sha256']
            with np.load(npz) as z:
                t,e=z['event_time_hr'],z['e']
                np.testing.assert_array_equal(z['station_ids'].astype(str),stations)
                np.testing.assert_array_equal(e[0],e0[m])
                assert t[0]==0 and t[-1]==480 and (np.diff(t)>0).all()
                err=np.max(np.abs(((1-e[:-1])*np.diff(t)[:,None]).sum(0)-loss[m]))
                assert err<1e-10
                maxevent=max(maxevent,err)
            event_records.append(dict(policy=p,realization_id=row.realization_id,physical_hash=row.physical_input_hash,
                manifest_sha256=sha(mp),npz_sha256=record['npz_sha256'],archive_relative_path=rel+'.npz',integration_error_hr=err))
        expected=prior.query('policy==@p').set_index('tract_id').reindex(full.index)
        np.testing.assert_allclose(projected.mean(0),expected.B_480_hr,rtol=0,atol=1e-10)
        b[p]=projected
        losses.append(loss)
        records.append(dict(policy=p,integral_sha256=meta['integral_sha256'],summary_sha256=meta['summary_sha256'],
            projection_max_error_hr=np.max(np.abs(observed-projected)),event_max_error_hr=maxevent,population_summary_max_error_hr=err_pop,
            population_weighted_B_hr=float(summary.population_weighted_normalized_burden_hr.mean()),identity=ident))
        print('independent frozen policy QA',p,flush=True)
    dm=json.loads(s.archive(prefix('direct-community')+'__EVALUATION.json').read_text())
    assert dm['integral_sha256']==records[1]['integral_sha256']
    s.archive(prefix('direct-community')+'__INTEGRALS.npz',dm['integral_sha256'])
    np.savez_compressed(lp(OUT/'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'),policies=np.array(POLICIES),
        station_ids=stations,tract_ids=full.index.to_numpy(str),realization_ids=phy.realization_id.to_numpy(str),
        physical_hashes=phy.physical_input_hash.to_numpy(str),station_loss=np.stack(losses),
        mapping_data=w.data,mapping_indices=w.indices,mapping_indptr=w.indptr,mapping_shape=np.array(w.shape),
        initial_station_e_mean=e0.mean(0))
    save('FROZEN_EVENT_VERIFICATION.csv',event_records)
    values, contributions, maxidentity=[],[],0
    u=b['unconstrained']; um=u.mean(0)
    for p in PRIMARY+['random']:
        delta=(b[p]-u).mean(0)
        maxidentity=max(maxidentity,np.max(np.abs(b[p].mean(0)-um-delta)))
        expected=prior.query('policy==@p').set_index('tract_id').reindex(full.index)
        np.testing.assert_allclose(delta,expected.Delta_B_logistics,rtol=0,atol=1e-10)
    for name,ps in SETS.items():
        meanburden=np.stack([b[p].mean(0) for p in ps])
        deltas=np.stack([(b[p]-u).mean(0) for p in ps])
        mean=deltas.mean(0); sd=deltas.std(0,ddof=0)
        np.testing.assert_allclose(sd,meanburden.std(0),rtol=0,atol=1e-10)
        # Different estimand: policy variation inside each matched physical realization.
        within=np.stack([b[p] for p in ps]).std(0,ddof=0).mean(0)
        assert (within+1e-10>=sd).all()
        for i,tid in enumerate(full.index):
            values.append(dict(tract_id=tid,policy_set=name,eligible_positive_population=bool(pos.iloc[i]),
                B_Unconstrained=um[i],MeanDelta=mean[i],PolicySD=sd[i],MeanTotalBurden=um[i]+mean[i],
                MeanWithinRealizationPolicySD=within[i],within_minus_between_policy_SD=within[i]-sd[i]))
            if name=='main5':
                for j,p in enumerate(ps):
                    contributions.append(dict(tract_id=tid,policy=p,Delta_hr=deltas[j,i],deviation_from_MeanDelta_hr=deltas[j,i]-mean[i],
                        contribution_to_policy_variance_hr2=(deltas[j,i]-mean[i])**2/len(ps),
                        largest_squared_deviation=(j==np.argmax((deltas[:,i]-mean[i])**2))))
        print('verified ensemble set',name,flush=True)
    save('MULTIPOLICY_RQ2_TRACT_VALUES.csv',values)
    save('POLICY_VARIANCE_CONTRIBUTIONS.csv',contributions)
    save('SOURCE_HASH_VERIFICATION.csv',s.records)
    dump('POLICY_ENSEMBLE_QA.json',dict(status='PASS',study_tracts=2315,positive_population_tracts=2299,zero_population_tracts=16,
        positive_population_zero_housing_tracts=8,physical_realizations=1000,policies=records,identity_max_error_hr=maxidentity,
        verified_event_payloads=len(event_records),protected_files=len(protected),prior_package_files=len(priors),
        physical_input_npz_sha256=sha(s.source(FORMAL+'Stage 1 Output_expanded/physical_inputs_2pc50.npz',AUTH)),
        mapping_sha256=sha(s.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',AUTH)),
        snapshot_sha256=sha(OUT/'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz'),direct_community_duplicate_verified=True,
        local_archive_required_for_full_event_reaudit=True,no_new_physical_simulation=True))


if __name__=='__main__': main()
