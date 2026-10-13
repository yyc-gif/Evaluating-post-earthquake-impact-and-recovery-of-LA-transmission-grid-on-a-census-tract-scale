"""Preserve the authority and reuse exact fitted evidence, before any new analysis."""
from common import *

TABLES = {
 'K_EVIDENCE_MATRIX.csv':'EIGHT_VARIABLE_K_EVIDENCE.csv',
 'P2_VS_P2_CBM_K_DIAGNOSTICS.csv':'ALL_REGISTERED_K_AND_SEED_DIAGNOSTICS.csv',
 'P2_VS_P2_CBM_MEMBERSHIP_COMPARISONS.csv':'SEVEN_VS_EIGHT_MEMBERSHIP_COMPARISONS.csv',
 'PER_CLUSTER_CBM_AND_RQ_PROFILES.csv':'EIGHT_VARIABLE_CLUSTER_PROFILES.csv',
 'POLICY_SET_AND_GEOGRAPHIC_STABILITY.csv':'POLICY_AND_SPATIAL_STABILITY.csv',
 'PER_CLUSTER_SILHOUETTE_AND_SIZE.csv':'PER_CLUSTER_SILHOUETTE_AND_SIZE.csv',
 'DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv':'DOMAIN_AND_COORDINATE_CONTRIBUTIONS.csv',
 'RQ3_ADDITION_VS_REALLOCATION_ALGEBRA.csv':'SEVEN_VS_EIGHT_DISTANCE_ALGEBRA.csv',
 'INIT_ABLATION_RESULTS.csv':'REGISTERED_INIT_ABLATION_RESULTS.csv',
 'CLUSTER_QUARTILE_HOSPITAL_GEOGRAPHY.csv':'QUARTILE_HOSPITAL_GEOGRAPHY_PROFILES.csv',
 'ELBOW_ENDPOINT_DIAGNOSTICS.csv':'ELBOW_ENDPOINT_DIAGNOSTICS.csv',
 'SEED_STABILITY.csv':'SEED_STABILITY.csv',
 'CLIMATE_CONTEXT_PHYSICAL_CROSSCHECK.csv':'PHYSICAL_CONTEXT_CROSSCHECK.csv',
}


def main():
    git('merge-base','--is-ancestor',AUTH,'HEAD')
    s=source_reader()
    prior=json.loads(lp(s.source(CK+'STARTING_STATE_AND_PROTECTION.json',AUTH)).read_text())
    hashes={p:sha(SOURCE_ROOT/p) for p in prior['protected_files']}
    assert hashes==prior['protected_files'] and len(hashes)==950
    snap=OUT/'STARTING_STATE_AND_PROTECTION.json'
    if not lp(snap).exists():
        dump(snap.name,dict(review_status=WARN,authority=AUTH,branch=git('branch','--show-current').decode().strip(),
             starting_status=git('status','--porcelain').decode(),protected_files=hashes,prior_git_blobs=prior_blobs(),
             original_status=git('status','--porcelain',cwd=SOURCE_ROOT).decode(),
             original_staged_diff_sha256=hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest()))
    dump('REGISTERED_ANALYSIS.json',dict(review_status=WARN,authority=AUTH,
         objective='Eight-coordinate author-review candidate; P2 is ablation only; no formal promotion',
         sources='Frozen published CDC 2024 ranks; focused official/peer-reviewed alternative search',
         reuse='Exact prior 492 fit labels/matrices; no main-model refit',
         component_extension='H2 only K3/4/5 seed42 for six remaining individual indicator removals and Extreme Events domain; researcher sensitivity only',
         national_rerank='All nine individual indicators plus three domains; exact integer 1e-4 EPL ticks; unchanged 83509 eligible records; minimum rank/(N-1)',
         nonlinear='Reuse independently verified CB audit conditional R2/VIF and fixed random/spatial CV; recompute pairwise correlations',
         kmeans=PARAMS,seeds=[42,43,44,45,46],K=list(range(1,9)),
         no_new_physical_realizations=True,no_formal_stage7_change=True,no_provider_contact=True))
    d=read(s,CK+'VERIFIED_COHORT_AND_DESCRIPTORS.csv','tract_id')
    assert len(d)==2299 and d.index.is_unique and d.index.str.fullmatch(r'\d{11}').all()
    assert (d.Population>0).all() and int(d.Population.sum())==9066522
    assert int(d.additional_zero_housing_positive_population.sum())==8
    full=read(s,CB+'FROZEN_P2_AND_COHORT.csv','tract_id')
    np.testing.assert_array_equal(d.Population,full.loc[d.index,'Population'])
    np.testing.assert_array_equal(d.frozen_SOVI_quartile,full.loc[d.index,'frozen_SOVI_quartile'])
    save('VERIFIED_EIGHT_VARIABLE_COHORT.csv',d.reset_index())
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv',full.loc[full.Population.eq(0),['Population']].reset_index())
    a=np.load(s.source(CK+'VERIFIED_WEIGHTED_MATRICES.npz',AUTH))
    f=np.load(s.source(CK+'REGISTERED_FIT_ARRAYS.npz',AUTH))
    np.testing.assert_array_equal(a['tract_ids'],d.index)
    for sp in BUDGETS: np.testing.assert_array_equal(matrix(d,sp),a[sp+'__published'])
    np.savez_compressed(destination('REUSED_MAIN_FIT_ARRAYS.npz'),tract_ids=f['tract_ids'],keys=f['keys'],labels=f['labels'],silhouette=f['silhouette'])
    np.savez_compressed(destination('REUSED_WEIGHTED_MATRICES.npz'),**{k:a[k] for k in a.files})
    for old,new in TABLES.items():
        x=read(s,CK+old);x['source_authority']=AUTH;save(new,x)
    for name in ['CBM_NINE_INDICATOR_SOURCE_REGISTER.csv','CBM_FLAGGED_TRACT_AND_POPULATION_COUNTS.csv']:
        save(name,read(s,CB+name))
    save('OFFICIAL_CDC_MATCHED_VALUES.csv',read(s,CB+'CDC_2024_MATCHED_ORIGINAL_VALUES.csv'))
    save('FOCUSED_SEARCH_SOURCE_HASHES_PREPARE.csv',s.records)
    dump('EIGHT_VARIABLE_FEATURE_AND_WEIGHT_SPECIFICATION.json',dict(review_status=WARN,authority=AUTH,
         primary_candidate='H2-CBM',features=P2+['RPL_CBM'],squared_distance_budgets=BUDGETS['H2'],
         euclidean_coordinate_multipliers=np.sqrt(BUDGETS['H2']),sensitivity=BUDGETS['H1'],ablation=BUDGETS['P2'],
         cohort_count=2299,full_service_domain=2315,population=9066522,zero_population_exclusions=16,retained_zero_housing=8,
         standardization='Cohort mean and population SD; multiply by square root budgets; equal tract observations',
         frozen_setup=['2pc50','C57_D1','M1_UTILITY_003','G1_BASELINE_050','480 hours','1000 matched frozen physical evaluations'],
         policy_ensemble=['Impact-first','Hospital-first','Degree-first','Betweenness-first','Vulnerability-first'],
         hazard_field='CDC EJI 2024 standalone RPL_CBM, published-as-is; selected climate-hazard burden; no earthquake',
         K_author_review='Evidence remains open; detailed K3/4/5 and full K2-8 provided; not promoted',
         formal_admission=False))
    print('950 payloads preserved; exact cohort and three main matrices verified; prior labels reused',flush=True)


if __name__=='__main__': main()
