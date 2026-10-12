"""Interpret saved labels and frozen station records; no fits or simulations."""
from itertools import combinations
import hashlib
import json
import platform
import sys

import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score

from common import *

UNITS = dict(Init_Supply='modeled service fraction (0-1)', Grid_Impact='W-weighted relative spectral lambda2 loss',
    Redundancy_HHI='sum of squared normalized dependency weights (0-1)', B_480_hr='normalized deficit hours over 480 h',
    Delta_B_logistics='matched Impact-first minus Unconstrained deficit hours', SOVI_SCORE='FEMA v1.19 national percentile (0-100)',
    log1p_Population='ln(1 + frozen persons)', log1p_BUILDVALUE='ln(1 + building stock in 2022 USD)',
    Population='frozen persons', BUILDVALUE='building stock, 2022 USD', T80='first 0.8 crossing of frozen mean service, hours',
    B_unconstrained='Unconstrained normalized deficit hours', self_loss_hr='own-functionality deficit hours',
    threshold_loss_hr='threshold-excluded residual functionality deficit hours', source_loss_hr='source-disconnection deficit hours')


def profile_tables(d, labels, spec):
    profiles, communities, transitions = [], [], []
    diagnostics = ['Init_Supply', 'Population', 'BUILDVALUE', 'T80', 'B_unconstrained',
                   'self_loss_hr', 'threshold_loss_hr', 'source_loss_hr']
    xy = d[['utm_x_m', 'utm_y_m']].to_numpy() / 1000
    mx, my = np.median(xy, axis=0)
    blocks = ((xy[:, 0] >= mx).astype(int) + 2 * (xy[:, 1] >= my)).astype(int)
    for model in SPECS:
        coordinates = list(spec['specifications'][model])
        for k in KS:
            for seed in SEEDS:
                lab = labels[f'{model}__k{k}__s{seed}'].to_numpy()
                for c in range(k):
                    part = d.loc[lab == c]
                    for variable in list(dict.fromkeys(coordinates + diagnostics)):
                        v, allv = part[variable], d[variable]
                        profiles.append(dict(specification=model, k=k, seed=seed, diagnostic_cluster=c,
                            variable=variable, is_input=variable in coordinates, units=UNITS[variable], n=len(v),
                            mean=v.mean(), median=v.median(), p10=v.quantile(.1), p90=v.quantile(.9),
                            minimum=v.min(), maximum=v.max(), sd=v.std(ddof=0),
                            cohort_mean=allv.mean(), cohort_median=allv.median(), cohort_p10=allv.quantile(.1),
                            cohort_p90=allv.quantile(.9), cluster_median_cohort_percentile=(allv <= v.median()).mean(),
                            mean_z=(v.mean()-allv.mean())/allv.std(ddof=0)))
                    pos = xy[lab == c]
                    radii = np.linalg.norm(pos-np.median(pos, axis=0), axis=1)
                    row = dict(specification=model, k=k, seed=seed, diagnostic_cluster=c, n_tracts=len(part),
                        population=part.Population.sum(), population_share=part.Population.sum()/d.Population.sum(),
                        median_tract_population=part.Population.median(), hospital_tracts=part.hospital_tract.sum(),
                        hospital_incidence=part.hospital_tract.mean(), exact_zero_Init_fraction=part.Init_Supply.eq(0).mean(),
                        added_zero_housing_tracts=part.additional_zero_housing_positive_population.sum(),
                        median_lat=part.INTPTLAT.median(), median_lon=part.INTPTLON.median(),
                        median_radius_km=np.median(radii), p90_radius_km=np.quantile(radii,.9),
                        maximum_quadrant_share=np.bincount(blocks[lab==c],minlength=4).max()/len(part))
                    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                        mask = part.frozen_SOVI_quartile.eq(q)
                        row[q+'_tracts'] = int(mask.sum())
                        row[q+'_tract_share'] = mask.mean()
                        row[q+'_population_share'] = part.loc[mask,'Population'].sum()/part.Population.sum()
                    communities.append(row)
                pairs = [('A','B')] if model == 'A' else []
                for a,b in pairs:
                    transitions.extend(match_transition(labels[f'{a}__k{k}__s{seed}'],labels[f'{b}__k{k}__s{seed}'],
                        a,b,k,k,seed,d))
        for k1,k2 in [(3,4),(4,5)]:
            for seed in SEEDS:
                transitions.extend(match_transition(labels[f'{model}__k{k1}__s{seed}'],
                    labels[f'{model}__k{k2}__s{seed}'],model,model,k1,k2,seed,d))
    save('CLUSTER_ORIGINAL_UNIT_PROFILES.csv', profiles)
    save('CLUSTER_POPULATION_AND_QUARTILE_PROFILES.csv', communities)
    save('MEMBERSHIP_TRANSITIONS_AND_CLASS_MATCHING.csv', transitions)


def match_transition(a,b,sa,sb,ka,kb,seed,d):
    table = np.zeros((ka,kb),int)
    np.add.at(table,(a,b),1)
    r,c = linear_sum_assignment(-table)
    match = dict(zip(c,r))
    return [dict(specification_a=sa,specification_b=sb,k_a=ka,k_b=kb,seed=seed,
        source_cluster=i,target_cluster=j,target_matched_to_source=match.get(j,-1),n_tracts=int(table[i,j]),
        source_retention_fraction=table[i,j]/(a==i).sum(),
        population=d.loc[(a==i)&(b==j),'Population'].sum()) for i in range(ka) for j in range(kb)]


def rare_stability(d, labels, rare, stress):
    rows=[]
    for model in SPECS:
        for k in KS:
            for seed in SEEDS:
                a = labels[f'{model}__k{k}__s{seed}']
                rows.append(best_match(a,rare,dict(kind='registered',specification=model,k=k,seed=seed,block=-1)))
    for keys,g in stress.groupby(['specification','k','kind','block']):
        model,k,kind,block=keys
        if model not in SPECS or k not in KS: continue
        a=g.set_index('tract_id').perturbed_cluster
        rows.append(best_match(a,rare,dict(kind=kind,specification=model,k=k,seed=42,block=block)))
    save('THIRTYFOUR_TRACT_IDENTITY_AND_STABILITY.csv',rows)
    exported=d.loc[rare].copy()
    for model in SPECS:
        for k in KS:
            for seed in SEEDS:
                exported[f'{model}__k{k}__s{seed}']=labels.loc[rare,f'{model}__k{k}__s{seed}']
    save('THIRTYFOUR_EXACT_GEOIDS_AND_SAVED_LABELS.csv',exported.reset_index())


def best_match(a,rare,context):
    group_ids={c:set(a.index[a.eq(c)]) for c in sorted(a.unique())}
    ref=set(rare)
    selected=max(group_ids,key=lambda c:len(ref & group_ids[c])/len(ref | group_ids[c]))
    members=group_ids[selected]
    return dict(**context,matched_cluster=int(selected),n_matched_cluster=len(members),
        retained=len(ref & members),lost=len(ref-members),added=len(members-ref),
        retention_fraction=len(ref & members)/len(ref),purity=len(ref & members)/len(members),
        Jaccard=len(ref & members)/len(ref | members),
        retained_GEOIDs=json.dumps(sorted(ref & members)),lost_GEOIDs=json.dumps(sorted(ref-members)),
        newly_added_GEOIDs=json.dumps(sorted(members-ref)))


def station_archive(s,d,mapping,rare):
    physical_path=s.source(FORMAL+'Stage 1 Output_expanded/physical_inputs_2pc50.npz',AUTH)
    with np.load(physical_path,allow_pickle=False) as z:
        stations=z['station_ids'].astype(str)
        assert z['evaluation_ds'].shape==(92,1000)
        ds=z['evaluation_ds'].T.copy()  # Frozen archive stores station x realization.
    assert ds.shape==(1000,92)
    manifest=frozen(s,FORMAL+'Stage 1 Output_expanded/PHYSICAL_SAMPLE_MANIFEST.csv',key='realization_id')
    manifest=manifest.loc[manifest.scenario.eq('2pc50')&manifest.split.eq('evaluation')].sort_index()
    verification=frozen(s,AUDIT+'FROZEN_REALIZATION_VERIFICATION.csv',key='realization_id')
    previous_pair=json.loads(s.source(AUDIT+'RECOVERY_PAIRING_QA.json',AUTH).read_text())
    nodeinfo=frozen(s,'Data/working_area_substations_with_fragility.csv',key='ID').reindex(stations)
    source_info=frozen(s,'Data/source_nodes_core_expanded.csv',key='ID')
    core=set(source_info.index[source_info.level.eq('Core')])
    edges=pd.read_csv(s.source('Data/substation_graph_CEC_edges_expanded.csv',AUTH),dtype={'u':str,'v':str})
    graph=nx.from_pandas_edgelist(edges,'u','v')
    assert set(stations)==set(graph) and len(core)==14 and core.issubset(graph)
    raw,eligible,connected,effective,identities,certificates=[],[],[],[],[],[]
    chain=hashlib.sha256()
    initial_by_ds=np.array([1.,.5,.09,.04,.03])
    for i,(rid,row) in enumerate(manifest.iterrows()):
        folder=FORMAL+'Formal_Trajectories/2pc50/C57_D1/direct-community/'
        jpath=s.archive(folder+rid+'.json',verification.loc[rid,'manifest_sha256'])
        jbytes=jpath.read_bytes();meta=json.loads(jbytes)
        chain.update(hashlib.sha256(jbytes).digest())
        assert meta['identity']['physical_sample_hash']==row.physical_input_hash
        path=s.archive(folder+rid+'.npz',meta['npz_sha256'])
        with np.load(path,allow_pickle=False) as z:
            assert np.array_equal(z['station_ids'].astype(str),stations) and z['event_time_hr'][0]==0
            f,F,C,e=[z[k][0].copy() for k in ['f','F','C','e']]
        assert np.array_equal(f,initial_by_ds[ds[i]])
        assert np.array_equal(F,f>=.5) and np.array_equal(e,f*F*C)
        assert not np.any(C.astype(bool)&~F.astype(bool))
        active=core & set(stations[F.astype(bool)])
        # Certificates inspect saved positive reachability only; no new gate is run.
        subgraph=graph.subgraph(stations[F.astype(bool)])
        for j in np.flatnonzero(C):
            paths=[nx.shortest_path(subgraph,stations[j],source) for source in sorted(active)
                   if nx.has_path(subgraph,stations[j],source)]
            assert paths,'Saved reachability has no functional path to a retained Core source'
            path_ids=min(paths,key=lambda p:(len(p),p))
            certificates.append(dict(realization_id=rid,substation_id=stations[j],Core_source=path_ids[-1],
                path_hops=len(path_ids)-1,path_station_ids=json.dumps(path_ids)))
        raw.append(f);eligible.append(F);connected.append(C);effective.append(e)
        identities.append(dict(realization_id=rid,physical_hash=row.physical_input_hash,
            manifest_sha256=sha(jpath),npz_sha256=sha(path),active_Core_count=len(active),
            positive_effective_stations=int((e>0).sum())))
        if i%250==0:print('read-only frozen initial states',i,flush=True)
    assert chain.hexdigest()==previous_pair['manifest_chain_sha256']
    f,F,C,e=map(np.asarray,[raw,eligible,connected,effective])
    np.savez_compressed(lp(OUT/'FROZEN_INITIAL_STATION_STATES.npz'),f=f,F=F,C=C,e=e,ds=ds,
        station_ids=stations,realization_ids=manifest.index.to_numpy(dtype=str))
    save('FROZEN_INITIAL_ARCHIVE_VERIFICATION.csv',identities)
    save('SAVED_POSITIVE_SOURCE_PATH_CERTIFICATES.csv',certificates)
    stats=[]
    for j,sid in enumerate(stations):
        nF=F[:,j].sum();nC=C[:,j].sum()
        stats.append(dict(substation_id=sid,name=nodeinfo.loc[sid,'NAME'],owner=nodeinfo.loc[sid,'Owner'],
            is_Core=sid in core,mean_raw_initial=f[:,j].mean(),eligible_count=int(nF),
            eligible_fraction=nF/1000,source_connected_count=int(nC),source_connected_fraction=nC/1000,
            source_connection_given_eligible=nC/nF if nF else np.nan,mean_effective_initial=e[:,j].mean(),
            **{f'DS{x}_count':int((ds[:,j]==x).sum()) for x in range(5)}))
    station=pd.DataFrame(stats).set_index('substation_id')
    m=mapping.copy();m['normalized_weight']=m.weight/m.groupby('tract_id').weight.transform('sum')
    m=m.merge(station.reset_index(),on='substation_id',validate='many_to_one')
    m['initial_service_contribution']=m.normalized_weight*m.mean_effective_initial
    tract_initial=m.groupby('tract_id').initial_service_contribution.sum().reindex(d.index)
    assert np.allclose(tract_initial,d.Init_Supply,rtol=0,atol=1e-12)
    rare_rows=m[m.tract_id.isin(rare)].copy()
    save('THIRTYFOUR_TRACT_STATION_DEPENDENCY.csv',rare_rows)
    save('STATION_INITIAL_STATE_AND_DAMAGE_SUMMARY.csv',station.reset_index())
    global_stats=[]
    for label,ids in [('rare34',rare),('other_nonzero',d.index[(d.Init_Supply>0)&~d.index.isin(rare)]),
                      ('other_tracts',d.index[~d.index.isin(rare)])]:
        part=m[m.tract_id.isin(ids)].groupby('substation_id').agg(
            dependency_mass=('normalized_weight','sum'),initial_mass=('initial_service_contribution','sum'),
            dependent_tract_count=('tract_id','nunique'))
        part['mean_dependency_weight']=part.dependency_mass/len(ids)
        part['initial_service_share']=part.initial_mass/part.initial_mass.sum()
        for sid,row in part.iterrows():global_stats.append(dict(group=label,substation_id=sid,
            name=station.loc[sid,'name'],is_Core=station.loc[sid,'is_Core'],**row.to_dict()))
    save('STATION_CONTRIBUTIONS_RARE_AND_OTHER_TRACTS.csv',global_stats)
    small=[]
    for tid,part in rare_rows.groupby('tract_id'):
        top=part.sort_values('normalized_weight',ascending=False).iloc[0]
        pos=part[part.initial_service_contribution>0].sort_values('initial_service_contribution',ascending=False)
        small.append(dict(tract_id=tid,assigned_station_count=len(part),top_weight_station=top.substation_id,
            top_dependency_weight=top.normalized_weight,HHI=(part.normalized_weight**2).sum(),
            Grid_Impact=d.loc[tid,'Grid_Impact'],Init_Supply=part.initial_service_contribution.sum(),
            positive_contributing_stations=len(pos),largest_service_contributor=pos.iloc[0].substation_id,
            largest_service_contribution_share=pos.iloc[0].initial_service_contribution/pos.initial_service_contribution.sum()))
    save('THIRTYFOUR_TRACT_NETWORK_SUMMARY.csv',small)
    # Exact realization-level linear projection of saved station e(0), not simulation.
    W=m.pivot(index='tract_id',columns='substation_id',values='normalized_weight').fillna(0).reindex(index=d.index,columns=stations)
    initial=e@W.to_numpy().T
    rare_idx=np.flatnonzero(d.index.isin(rare))
    save('THIRTYFOUR_REALIZATION_INITIAL_SERVICE.csv',[
        dict(realization_id=rid,tract_id=d.index[j],initial_service=initial[i,j])
        for i,rid in enumerate(manifest.index) for j in rare_idx])
    dump('FROZEN_INITIAL_SOURCE_QA.json',dict(samples=1000,stations=92,core_sources=14,
        manifest_chain_sha256=chain.hexdigest(),tract_projection_max_error=float(abs(tract_initial-d.Init_Supply).max()),
        raw_initial_DS_values=initial_by_ds,any_new_gate=False,any_new_recovery=False,
        saved_positive_paths_certified=len(certificates),realizations_with_any_initial_service=int((e>0).any(1).sum()),
        new_station_or_damage_sampling=False))
    return m


def burden_context(s,d,mapping):
    metadata=json.loads(s.source(PREVIOUS+'FROZEN_RECOVERY_SOURCE_RECHECK.json',AUTH).read_text())
    names=['L_self','L_threshold','L_source','L_total']
    for policy in ['impact-first','unconstrained']:
        stem=FORMAL+'Formal_Offline_Evaluation/2pc50__C57_D1__'+policy
        meta=s.archive(stem+'__EVALUATION.json')
        obj=json.loads(meta.read_text());assert obj['identity']==metadata['identities'][policy]
        with np.load(s.archive(stem+'__INTEGRALS.npz',obj['integral_sha256']),allow_pickle=False) as z:
            stations=z['station_ids'].astype(str)
            W=mapping.pivot(index='tract_id',columns='substation_id',values='weight').fillna(0).reindex(index=d.index,columns=stations)
            for name in names:
                values=W.to_numpy()@z['G1_BASELINE_050__'+name].mean(0)
                if policy=='impact-first': d[dict(L_self='self_loss_hr',L_threshold='threshold_loss_hr',L_source='source_loss_hr',L_total='B_reprojected')[name]]=values
                elif name=='L_total':assert np.allclose(values,d.B_unconstrained,rtol=0,atol=1e-10)
    assert np.allclose(d.B_reprojected,d.B_480_hr,rtol=0,atol=1e-10)
    assert np.allclose(d[['self_loss_hr','threshold_loss_hr','source_loss_hr']].sum(1),d.B_480_hr,rtol=0,atol=1e-10)


def algebraic_scaling(d,labels,spec,rare):
    rows=[]
    mask=d.index.isin(rare)
    for model in ['A','B']:
        budget=spec['specifications'][model]
        z=(d[list(budget)]-d[list(budget)].mean())/d[list(budget)].std(ddof=0)
        for variant in ['registered','drop_Init_fixed_other_budgets','drop_Init_RQ1_redistributed']:
            b=budget.copy()
            if variant!='registered': b.pop('Init_Supply')
            if variant=='drop_Init_RQ1_redistributed':
                b['Grid_Impact']=b['Redundancy_HHI']=1/6
            for c,w in b.items():
                rare_z=z.loc[mask,c];other_z=z.loc[~mask,c]
                total=((z[c]-z[c].mean())**2).sum()*w
                within_rare=((rare_z-rare_z.mean())**2).sum()*w
                center_global=len(rare_z)*rare_z.mean()**2*w
                rows.append(dict(specification=model,algebraic_variant=variant,coordinate=c,
                    squared_distance_budget=w,total_SS=total,within_rare_SS=within_rare,
                    rare_centroid_global_between_SS=center_global,
                    rare_vs_rest_centroid_squared_distance=(rare_z.mean()-other_z.mean())**2*w,
                    raw_rare_mean=d.loc[mask,c].mean(),raw_other_mean=d.loc[~mask,c].mean(),
                    raw_mean_difference=d.loc[mask,c].mean()-d.loc[~mask,c].mean(),
                    cohort_SD=d[c].std(ddof=0),standardized_mean_difference=rare_z.mean()-other_z.mean()))
    save('INIT_ALGEBRAIC_DISTANCE_DECOMPOSITION.csv',rows)
    save('RARE_GROUP_NON_INIT_ORIGINAL_UNIT_CONTRAST.csv',[
        dict(variable=c,units=UNITS[c],rare_mean=d.loc[mask,c].mean(),rare_median=d.loc[mask,c].median(),
            other_mean=d.loc[~mask,c].mean(),other_median=d.loc[~mask,c].median(),
            cohort_median=d[c].median(),rare_mean_z=(d.loc[mask,c].mean()-d[c].mean())/d[c].std(ddof=0))
        for c in list(dict.fromkeys(list(spec['specifications']['B'])+['Population','BUILDVALUE','T80']))])


def main():
    s=sources()
    dump('STARTING_STATUS_AND_PRESERVATION.json',dict(starting_commit=git('rev-parse','HEAD').decode().strip(),
        branch=git('branch','--show-current').decode().strip(),diagnostic_status=git('status','--porcelain').decode().splitlines(),
        unrelated_source_status=git('status','--porcelain',cwd=SOURCE_ROOT).decode().splitlines(),
        source_root=str(SOURCE_ROOT),source_worktree_HEAD=git('rev-parse','HEAD',cwd=SOURCE_ROOT).decode().strip(),
        protected_files=preserve(s),python=sys.version,platform=platform.platform(),authoritative_commit=AUTH))
    prior_paths=git('ls-tree','-r','--name-only',AUTH,'--',PREVIOUS,AUDIT).decode().splitlines()
    dump('PRIOR_PACKAGE_IMMUTABILITY.json',{p:sha(s.source(p,AUTH)) for p in prior_paths})
    d,labels,spec=inputs(s)
    rare=d.index[labels['A__k4__s42'].eq(0)]
    assert len(rare)==34
    mapping=pd.read_csv(s.source('Data/JULY_UTILITY_CONSTRAINED_92.csv',AUTH),dtype={'tract_id':str,'substation_id':str})
    assert np.allclose(mapping.groupby('tract_id').weight.sum(),1,rtol=0,atol=1e-12)
    station_archive(s,d,mapping,rare)
    burden_context(s,d,mapping)
    save('VERIFIED_INTERPRETATION_TRACT_VALUES.csv',d.reset_index())
    profile_tables(d,labels,spec)
    stress=frozen(s,PREVIOUS+'STRESS_TEST_MEMBERSHIPS.csv').reset_index()
    stress=stress[stress.cohort.eq('positive_population')]
    rare_stability(d,labels,rare,stress)
    algebraic_scaling(d,labels,spec,rare)
    stability=pd.read_csv(s.source(PREVIOUS+'SPATIAL_AND_SEED_STABILITY.csv',AUTH))
    selected=stability[stability.cohort.eq('positive_population')&stability.specification.isin(SPECS)&stability.k.isin(KS)]
    save('K_SEED_AND_GEOGRAPHIC_STABILITY.csv',selected)
    save('SOURCE_HASH_VERIFICATION.csv',s.records)
    dump('ANALYSIS_SCOPE.json',dict(authoritative_commit=AUTH,cohort=2299,specifications=SPECS,k_values=KS,seeds=SEEDS,
        any_new_KMeans_fit=False,any_new_weight_optimization=False,any_formal_promotion=False,
        frozen_specification_hash=sha(s.source(PREVIOUS+'FEATURE_SPECIFICATIONS_AND_WEIGHTS.json',AUTH)),
        protected_files_after=preserve(s),number_original_registered_conditions=60))
    print('Saved-result interpretation and frozen initial-state extraction completed',flush=True)


if __name__=='__main__':main()
