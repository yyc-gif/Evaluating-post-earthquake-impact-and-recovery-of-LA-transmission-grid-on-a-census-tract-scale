"""Independent frozen integral arithmetic and transparent review summaries."""
from scipy import sparse
from common import *


def main():
    s=sources(); d=frame('VERIFIED_COHORT_AND_DESCRIPTORS.csv')
    z=np.load(s.source(MP+'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz',AUTH))
    qa=json.loads(lp(s.source(MP+'POLICY_ENSEMBLE_QA.json',AUTH)).read_text())
    assert sha(s.source(MP+'FROZEN_STATION_INTEGRALS_AND_MAPPING.npz',AUTH))==qa['snapshot_sha256']
    w=sparse.csr_matrix((z['mapping_data'],z['mapping_indices'],z['mapping_indptr']),shape=z['mapping_shape'])
    mass=np.asarray(w.sum(1)).ravel(); order=pd.Index(z['tract_ids']); policies=list(z['policies'])
    assert len(order)==2315 and z['station_loss'].shape[1]==1000
    burden=np.stack([(w@station.T).T/mass for station in z['station_loss']])
    u=burden[policies.index('unconstrained')]
    primary=['impact-first','hospital-first','degree-first','betweenness-first','vulnerability-first']
    sets={'main5':primary,**{'without_'+p:[q for q in primary if q!=p] for p in primary},'plus_random':primary+['random']}
    v=frozen(s,MP+'MULTIPOLICY_RQ2_TRACT_VALUES.csv'); maxerr=0
    for name,ps in sets.items():
        selected=burden[[policies.index(p) for p in ps]]
        delta=(selected-u).mean(1)
        expected={'B_Unconstrained':u.mean(0),'MeanDelta':delta.mean(0),'PolicySD':delta.std(0,ddof=0),'MeanTotalBurden':selected.mean((0,1))}
        actual=v.loc[v.policy_set.eq(name)].reindex(order)
        for col,a in expected.items():
            err=np.max(np.abs(actual[col]-a)); maxerr=max(maxerr,err); assert err<1e-10
    fit=pd.read_csv(lp(OUT/'P2_VS_P2_CBM_K_DIAGNOSTICS.csv'))
    per=pd.read_csv(lp(OUT/'PER_CLUSTER_SILHOUETTE_AND_SIZE.csv'))
    seed=pd.read_csv(lp(OUT/'SEED_STABILITY.csv'))
    robust=pd.read_csv(lp(OUT/'POLICY_SET_AND_GEOGRAPHIC_STABILITY.csv'))
    comp=pd.read_csv(lp(OUT/'P2_VS_P2_CBM_MEMBERSHIP_COMPARISONS.csv'))
    cc=pd.read_csv(lp(OUT/'DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv'))
    elbow=pd.read_csv(lp(OUT/'ELBOW_ENDPOINT_DIAGNOSTICS.csv'))
    summary=[]
    for (sp,k),part in fit.query("condition=='published' and k>1").groupby(['specification','k']):
        r=robust.loc[robust.specification.eq(sp)&robust.k.eq(k)]
        geographic=r.loc[r.test.eq('geographic')]
        loo=r.loc[r.test.eq('policy_set')&r.condition.str.contains('without_')&r.scaling.eq('cohort')]
        fixed=r.loc[r.test.eq('policy_set')&r.condition.str.contains('without_')&r.scaling.eq('fixed_main5')]
        rand=r.loc[r.condition.eq('policy_plus_random__cohort')]
        pc=per.loc[per.specification.eq(sp)&per.condition.eq('published')&per.k.eq(k)&per.seed.eq(42)]
        shares=cc.loc[cc.specification.eq(sp)&cc.condition.eq('published')&cc.k.eq(k)&cc.seed.eq(42)].groupby('domain').between_fraction_of_all.sum()
        summary.append(dict(specification=sp,k=k,mean_WCSS=part.WCSS.mean(),mean_silhouette=part.mean_silhouette.mean(),
             silhouette_min=part.mean_silhouette.min(),silhouette_max=part.mean_silhouette.max(),
             mean_negative_fraction=part.negative_silhouette_fraction.mean(),
             seed_min_ARI=seed.loc[seed.specification.eq(sp)&seed.k.eq(k),'ARI'].min(),
             geographic_min_ARI=geographic.ARI.min(),geographic_median_ARI=geographic.ARI.median(),
             policy_LOO_min_ARI=loo.ARI.min(),policy_LOO_mean_ARI=loo.ARI.mean(),policy_LOO_fixed_scaling_min_ARI=fixed.ARI.min(),
             plus_Random_ARI=rand.ARI.iloc[0],smallest_seed42_class=pc.n_tracts.min(),
             smallest_seed42_population_share=pc.population_share.min(),
             RQ1_between_share=shares['RQ1'],RQ2_between_share=shares['RQ2'],RQ3_between_share=shares['RQ3'],
             bends_K1_6=int(elbow.query('specification==@sp and endpoint==6').bend_candidate.iloc[0]),
             bends_K1_7=int(elbow.query('specification==@sp and endpoint==7').bend_candidate.iloc[0]),
             bends_K1_8=int(elbow.query('specification==@sp and endpoint==8').bend_candidate.iloc[0])))
    save('K_EVIDENCE_MATRIX.csv',summary)
    archive=np.load(lp(OUT/'REGISTERED_FIT_ARRAYS.npz')); keys={k:i for i,k in enumerate(archive['keys'])}
    profiles=pd.read_csv(lp(OUT/'PER_CLUSTER_CBM_AND_RQ_PROFILES.csv'))
    rename=profiles.condition.str.startswith('component_')&profiles.variable.eq('RPL_CBM')
    profiles.loc[rename,'variable']='researcher_climate_rank'
    profiles=profiles.loc[~profiles.variable.isin(['log1p_Population','Published_RPL_CBM'])].copy()
    extra=[]; climate=[]
    top=set(d.RPL_CBM.sort_values(ascending=False,kind='stable').head(230).index)
    for key,position in keys.items():
        if not key.endswith('__s42'): continue
        condition=key.split('__',1)[1].rsplit('__k',1)[0]
        if condition!='published' and not condition.startswith('component_'): continue
        sp=key.split('__')[0]; k=int(key.rsplit('__k',1)[1].split('__')[0])
        if k==1: continue
        lab=archive['labels'][position]
        for c in range(k):
            selected=lab==c; part=d.loc[selected]
            for col,source in [('log1p_Population','log1p_Population'),('Published_RPL_CBM','RPL_CBM')]:
                a=part[source]
                extra.append(dict(specification=sp,condition=condition,k=k,cluster=c,variable=col,
                    n_tracts=len(part),population=int(part.Population.sum()),population_share=part.Population.sum()/d.Population.sum(),
                    mean=a.mean(),median=a.median(),p10=a.quantile(.1),p90=a.quantile(.9),minimum=a.min(),maximum=a.max(),
                    cohort_mean=d[source].mean(),cohort_median=d[source].median(),valid_count=len(a),
                    fitted_coordinate=(col=='log1p_Population')))
            if condition=='published':
                climate.append(dict(specification=sp,k=k,cluster=c,n_tracts=len(part),population=int(part.Population.sum()),
                    top230_CBM_members=int(part.index.isin(top).sum()),top230_capture=part.index.isin(top).sum()/230,
                    riverine_positive=int(part.E_RFLD.gt(0).sum()),riverine_positive_fraction=part.E_RFLD.gt(0).mean(),
                    burn_positive=int(part.E_BURN.gt(0).sum()),mean_published_CBM=part.RPL_CBM.mean()))
    save('PER_CLUSTER_CBM_AND_RQ_PROFILES.csv',pd.concat([profiles,pd.DataFrame(extra)],ignore_index=True))
    save('CLIMATE_CONTEXT_CLUSTER_COVERAGE.csv',climate)
    physical=frozen(s,CB+'INDEPENDENT_PHYSICAL_MATCHED_VALUES.csv').reindex(d.index)
    physical_cols=['Wildfire_high_land_fraction','Flood_SFHA_land_fraction_complete','Historical_heat_days_2018_2022','tract_seismic_PGA']
    phrows=[]; logprofiles=[]
    for sp in BUDGETS:
        for k in [3,4,5]:
            lab=archive['labels'][keys[f'{sp}__published__k{k}__s42']]
            for c in range(k):
                selected=lab==c; part=d.loc[selected]
                for col in physical_cols:
                    a=physical.loc[selected,col]
                    phrows.append(dict(specification=sp,k=k,cluster=c,physical_measure=col,n_class=int(selected.sum()),
                        valid_count=a.notna().sum(),missing_support=a.isna().sum(),mean_valid=a.mean(),median_valid=a.median(),
                        p10_valid=a.quantile(.1),p90_valid=a.quantile(.9),cohort_valid_mean=physical[col].mean(),
                        same_source_not_independent=(col=='Historical_heat_days_2018_2022'),
                        positive_valid_fraction=a.dropna().gt(0).mean()))
                a=part.log1p_Population
                logprofiles.append(dict(specification=sp,condition='published',k=k,cluster=c,variable='log1p_Population',
                    n_tracts=len(part),population=int(part.Population.sum()),population_share=part.Population.sum()/d.Population.sum(),
                    mean=a.mean(),median=a.median(),p10=a.quantile(.1),p90=a.quantile(.9),minimum=a.min(),maximum=a.max(),
                    cohort_mean=d.log1p_Population.mean(),cohort_median=d.log1p_Population.median(),valid_count=len(a),fitted_coordinate=True))
    save('CLIMATE_CONTEXT_PHYSICAL_CROSSCHECK.csv',phrows)
    save('LOG_POPULATION_ORIGINAL_PROFILES.csv',logprofiles)
    # Original-unit and national ranking separation, not additional fitted coordinates.
    high=d.E_RFLD.gt(0).to_numpy(); a=d.RPL_CBM.to_numpy(); pred=np.where(high,a[high].mean(),a[~high].mean())
    riverine_r2=1-np.sum((a-pred)**2)/np.sum((a-a.mean())**2)
    quality=frozen(s,CB+'CBM_2299_GEOID_COVERAGE.csv')
    assert quality.index.equals(d.index) and quality.exact_match.all()
    dump('FROZEN_PAIRING_AND_INFORMATION_QA.json',dict(label=WARN,status='PASS',physical_realizations=1000,
         unchanged_full_domain=2315,policy_sets=7,frozen_snapshot_sha256=qa['snapshot_sha256'],
         maximum_recomputed_ensemble_error_hr=maxerr,published_CBM_riverine_binary_R2=riverine_r2,
         limitation='Reproduces exact published frozen station-integral extract. Full raw event/damage provenance still needs manifest-bound local archive; no new source propagation.',
         CDC_source_quality_gate_passed=False))
    save('SOURCE_HASH_VERIFICATION_EVIDENCE.csv',s.records)
    print(pd.DataFrame(summary).to_string(index=False),flush=True)


if __name__=='__main__': main()
