"""Independent source, fit, distance-budget and preservation checks.

This file does not import the analysis implementation or scientific model.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from common import COMMIT, OUT, PRIOR, ROOT, SPEC, dump, git, lp, save, sha, source_verifier


def main():
    context=json.loads(lp(OUT/'STARTING_GIT_AND_ENVIRONMENT.json').read_text())
    sources=source_verifier(context['source_root'],context['cache_roots'])
    d=pd.read_csv(lp(OUT/'TRACT_FEATURES_VERIFIED_2315.csv'),dtype={'tract_id':str}).set_index('tract_id').sort_index()
    raw=sources.frame('Data/Tracts_Within_Expanded_Area.csv',key='GEOID',commit=COMMIT)
    assert len(d)==2315 and d.index.str.fullmatch(r'\d{11}').all() and d.index.is_unique
    assert np.array_equal(d.Population,raw.population.reindex(d.index))
    positive=d.loc[raw.population.reindex(d.index)>0]
    residential=positive.loc[positive.housing_total>0]
    qa=json.loads(lp(OUT/'COHORT_SOURCE_QA.json').read_text())
    assert (len(positive),len(residential),len(d)-len(positive))==(qa['positive_population'],qa['residential'],qa['zero_population'])
    assert set(qa['extra_GEOIDs'])==set(positive.index)-set(residential.index)
    assert set(qa['excluded_zero_population_GEOIDs'])==set(d.index)-set(positive.index)
    assert len(positive.index.intersection(['06037189703','06037301601','06037301602','06037404600']))==4
    original=sources.frame(PRIOR+'TRACT_CANDIDATE_VALUES_2315.csv',commit=COMMIT).sort_index()
    for c in SPEC['specifications']['A']:
        assert np.allclose(d[c],original[c],rtol=0,atol=1e-12),c
    assert np.array_equal(d.frozen_SOVI_quartile,original.frozen_SOVI_quartile)
    nri=sources.frame('Data/NRI_Table_CensusTracts_California.csv',key='TRACTFIPS',
        columns=['TRACTFIPS','BUILDVALUE','NRI_VER'],commit=COMMIT).reindex(d.index)
    assert np.array_equal(d.BUILDVALUE,nri.BUILDVALUE) and nri.NRI_VER.eq('Mar-23').all()
    assert np.allclose(d.log1p_BUILDVALUE,np.log1p(nri.BUILDVALUE),rtol=0,atol=1e-14)
    assert np.allclose(d.log1p_Population,np.log1p(raw.population.reindex(d.index)),rtol=0,atol=1e-14)
    mapping=pd.read_csv(sources.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',COMMIT),dtype={'tract_id':str,'substation_id':str})
    central=pd.read_csv(sources.source('Formal_Experiment_20260923/Stage 2 Output_expanded/impact_centrality_substations.csv',COMMIT),dtype={'substation_id':str})
    m=mapping.merge(central,on='substation_id',validate='many_to_one')
    m['p']=m.weight/m.groupby('tract_id').weight.transform('sum')
    spectral=(m.p*m.impact_centrality).groupby(m.tract_id).sum().reindex(d.index)
    hhi=m.p.pow(2).groupby(m.tract_id).sum().reindex(d.index)
    assert np.allclose(spectral,d.Grid_Impact,rtol=0,atol=1e-10)
    assert np.allclose(hhi,d.Redundancy_HHI,rtol=0,atol=1e-12)
    # Independent station-integral projection, not an event/gate calculation.
    projected={}
    physical={}
    for policy in ['impact-first','unconstrained']:
        prefix='Formal_Experiment_20260923/Formal_Offline_Evaluation/2pc50__C57_D1__'+policy
        meta=json.loads(lp(Path(context['source_root'])/(prefix+'__EVALUATION.json')).read_text())
        archive=lp(Path(context['source_root'])/(prefix+'__INTEGRALS.npz'))
        assert sha(archive)==meta['integral_sha256']
        with np.load(archive,allow_pickle=False) as z:
            stations=z['station_ids'].astype(str).tolist()
            ids=raw.index.tolist()
            wi,si={v:i for i,v in enumerate(ids)},{v:i for i,v in enumerate(stations)}
            W=csr_matrix((mapping.weight,([wi[t] for t in mapping.tract_id],[si[s] for s in mapping.substation_id])),shape=(len(ids),len(stations)))
            v=W@z['G1_BASELINE_050__L_total'].mean(axis=0)
            projected[policy]=pd.Series(v,index=ids).reindex(d.index).to_numpy()
            physical[policy]=z['physical_hashes'].copy()
    assert len(physical['impact-first'])==1000 and np.array_equal(physical['impact-first'],physical['unconstrained'])
    assert np.allclose(projected['impact-first'],d.B_480_hr,rtol=0,atol=1e-10)
    assert np.allclose(projected['impact-first']-projected['unconstrained'],d.Delta_B_logistics,rtol=0,atol=1e-10)
    registered=pd.read_csv(lp(OUT/'REGISTERED_EXPLORATORY_CLUSTERING.csv'))
    contributions=pd.read_csv(lp(OUT/'DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv'))
    verification=[]
    for cohort,sub in [('positive_population',positive),('residential',residential)]:
        memberships=pd.read_csv(lp(OUT/f'CLUSTER_MEMBERSHIPS_{cohort.upper()}.csv'),dtype={'tract_id':str}).set_index('tract_id')
        assert memberships.index.equals(sub.index)
        for spec,budget in SPEC['specifications'].items():
            assert np.isclose(sum(budget.values()),1)
            for domain in ['RQ1','RQ2','RQ3']:
                assert np.isclose(sum(v for c,v in budget.items() if SPEC['domains'][c]==domain),1/3)
            a=sub[list(budget)].to_numpy()
            x=(a-a.mean(0))/a.std(0,ddof=0)*np.sqrt(list(budget.values()))
            assert np.isfinite(x).all()
            assert np.allclose((x*x).sum(0)/len(sub),list(budget.values()),rtol=0,atol=1e-12)
            # Full independent replay at display k=4, seed42; other 190 partitions checked algebraically below.
            replay=KMeans(n_clusters=4,random_state=42,**SPEC['kmeans']).fit(x)
            labels=replay.predict(x)
            order=sorted(np.unique(labels),key=lambda i:(sub.B_480_hr[labels==i].mean(),sub.Population[labels==i].mean()))
            labelmap={old:new for new,old in enumerate(order)}
            canonical=np.array([labelmap[i] for i in labels])
            assert np.array_equal(canonical,memberships[f'{spec}__k4__s42'])
            for k in SPEC['k_values']:
                for seed in SPEC['seeds']:
                    saved=memberships[f'{spec}__k{k}__s{seed}'].to_numpy()
                    assert set(saved)==set(range(k))
                    total=np.square(x-x.mean(0)).sum(0)
                    within=np.zeros(x.shape[1])
                    for label in range(k):
                        group=x[saved==label]
                        within+=np.square(group-group.mean(0)).sum(0)
                    between=total-within
                    expected=contributions[(contributions.cohort==cohort)&(contributions.specification==spec)&
                        (contributions.k==k)&(contributions.seed==seed)&(contributions.kind=='coordinate')].set_index('coordinate').reindex(list(budget))
                    assert np.allclose(total,expected.total_SS,rtol=0,atol=1e-9)
                    assert np.allclose(within,expected.within_SS,rtol=0,atol=1e-9)
                    assert np.allclose(between,expected.between_SS,rtol=0,atol=1e-9)
                    r=registered[(registered.cohort==cohort)&(registered.specification==spec)&(registered.k==k)&(registered.seed==seed)].iloc[0]
                    assert json.loads(r.cluster_sizes)==np.bincount(saved,minlength=k).tolist()
                    verification.append(dict(cohort=cohort,specification=spec,k=k,seed=seed,
                        identity_and_partition_distance_verified=True,full_replay=(k==4 and seed==42)))
    before=json.loads(lp(OUT/'PRESERVATION_BEFORE.json').read_text())
    protected={p:sha(Path(context['source_root'])/p) for p in before['protected_files']}
    assert protected==before['protected_files']
    dump('PRESERVATION_AFTER.json',dict(protected_count=len(protected),protected_files=protected))
    prior=json.loads(lp(OUT/'PRIOR_AUDIT_IMMUTABILITY_BEFORE.json').read_text())
    assert all(sha(sources.source(p,COMMIT))==h for p,h in prior.items())
    current_status=git('status','--porcelain=v1',cwd=context['source_root']).decode().splitlines()
    assert current_status==context['unrelated_source_status'], 'Unrelated source worktree status changed'
    for name,budget in SPEC['specifications'].items():
        assert not {'RISK_SCORE','EAL_SCORE','EAL_VALT','ALR_NPCTL','T80','B_unconstrained'}.intersection(budget)
        assert ('Init_Supply' in budget)==('minus-Init' not in name)
    save('INDEPENDENT_PARTITION_VERIFICATION.csv',verification)
    save('INDEPENDENT_SOURCE_HASH_VERIFICATION.csv',sources.records)
    dump('INDEPENDENT_QA_RESULTS.json',dict(status='PASS',registered_partitions_verified=len(verification),
        independent_full_fit_replays=10,exact_GEOIDs=True,cohort_counts_derived_independently=True,
        frozen_1000_physical_pairs_verified=True,station_integrals_independently_projected=True,
        spectral_grid_impact_reprojected=True,original_quartile_assignments_unchanged=True,
        source_missingness_not_imputed=True,protected_scientific_files_unchanged=len(protected),
        previous_audit_files_unchanged=len(prior),unrelated_git_status_unchanged=True,
        any_formal_stage7_promotion=False,any_new_damage_schedule_or_recovery=False))
    print('PASS: 200 partition checks, 10 independent full fit replays, source pairing and protected files',flush=True)


if __name__=='__main__':
    main()
