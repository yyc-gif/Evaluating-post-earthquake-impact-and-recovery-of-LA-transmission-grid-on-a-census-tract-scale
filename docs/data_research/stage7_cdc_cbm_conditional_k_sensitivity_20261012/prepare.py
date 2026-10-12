"""Register before fitting; verify cohort, archives, national ranks and old matrices."""
import zipfile
from common import *


def main():
    git('merge-base','--is-ancestor',AUTH,'HEAD')
    core_only='--core-only' in sys.argv
    changed=git('diff','--name-only').decode().splitlines()
    assert all(p.startswith(OUT.relative_to(ROOT).as_posix()+'/') for p in changed)
    s=sources()
    old=json.loads(lp(s.source(CB+'STARTING_STATE_AND_PROTECTION.json',AUTH)).read_text())
    protected=old['protected_files'] if core_only else {p:sha(SOURCE_ROOT/p) for p in old['protected_files']}
    assert protected==old['protected_files'] and len(protected)==950
    dump('STARTING_STATE_AND_PROTECTION.json',dict(starting_commit=AUTH,branch=git('branch','--show-current').decode().strip(),
         status=git('status','--porcelain').decode(),protected_files=protected,prior_git_blobs=prior_blobs(),
         original_archive_preservation_verified=not core_only,
         source_status=None if core_only else git('status','--porcelain',cwd=SOURCE_ROOT).decode(),
         source_staged_diff_sha256=None if core_only else hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest()))
    dump('REGISTERED_ANALYSIS.json',dict(label=WARN,authority=AUTH,authorization='Published-as-is exploratory fitting expressly authorized; formal source gate remains unresolved',
         cohort='2299 frozen positive-population tracts; 16 zero-population exclusions; 8 zero-housing positives retained',
         frozen=['2pc50','C57_D1','M1_UTILITY_003','G1_BASELINE_050','480 hours','1000 frozen evaluations'],
         specifications=['P2','H1','H2'],K=[1,*KS],seeds=SEEDS,kmeans=PARAMS,
         standardization='Cohort mean and population SD, then sqrt squared-distance budgets',
         P2_reuse='Require exact weighted matrix, scaler and IDs; recompute inertia/silhouettes and compare old labels',
         elbow='Endpoint chord K1-6, K1-7, K1-8; smooth bends not automatic selections',
         component_removals=REMOVALS,national_universe='Same 83509 complete nationally eligible CDC CBM records; min-rank/(N-1)',
         component_fit_range='K3/4/5 plus endpoint-chord and maximum-mean-silhouette Ks of H1/H2; seeds42-46, not unrestricted search',
         spatial='Four frozen median-split UTM quadrants, leave one out; training-only scaling; seed42, K2-8',
         policy='Five LOO sets and five-plus-Random; equal descriptive policy weights; seed42 K2-8; cohort and fixed-main5 scaling',
         perturbation_seed_limit='Component-removal uses all five seeds; policy/geographic comparisons seed42, as bounded prior perturbation protocol',
         Init_ablation='H1/H2 K3/4/5 seed42; redistribute RQ1 to Impact/HHI; algebra separately removes Init at fixed remaining weights',
         limitations='No fabricated flags or updated CDC values; no physical or formal Stage7 change; no provider contact'))
    dump('P2_VS_P2_CBM_FEATURE_WEIGHTS.json',dict(label=WARN,specifications={sp:dict(coordinates=cols(sp),squared_distance_budgets=w,
         coordinate_multipliers=np.sqrt(w)) for sp,w in BUDGETS.items()},notice='H1/H2 add CBM and reallocate RQ3 budgets; weights are not optimized'))
    full=frozen(s,CB+'FROZEN_P2_AND_COHORT.csv').sort_index()
    assert len(full)==2315 and full.index.is_unique and full.index.str.fullmatch(r'\d{11}').all()
    d=full.loc[full.Population.gt(0)].copy()
    assert len(d)==2299 and int(d.additional_zero_housing_positive_population.sum())==8
    assert int(d.Population.sum())==9066522
    descriptor=frozen(s,MP+'VERIFIED_DESCRIPTORS_2315.csv').reindex(d.index)
    assert np.array_equal(d.Population,descriptor.Population)
    for col in descriptor:
        if col not in d: d[col]=descriptor[col]
    for col in P2:
        if col in descriptor:
            np.testing.assert_allclose(d[col],descriptor[col],rtol=0,atol=1e-12)
            d[col]=descriptor[col]
    v=frozen(s,MP+'MULTIPOLICY_RQ2_TRACT_VALUES.csv')
    v=v.loc[v.policy_set.eq('main5')].reindex(d.index)
    for col in ['B_Unconstrained','MeanDelta','PolicySD','MeanTotalBurden']:
        if col in d: np.testing.assert_allclose(d[col],v[col],rtol=0,atol=1e-12)
        d[col]=v[col]
    cdc=frozen(s,CB+'CDC_2024_MATCHED_ORIGINAL_VALUES.csv').reindex(d.index)
    assert cdc.GEOID_2020.astype(str).equals(pd.Series(d.index,index=d.index,name='GEOID_2020'))
    assert cdc.RPL_CBM.between(0,1).all() and (cdc.F_HRCN==1).all() and (cdc.E_BURN==0).sum()==2251
    for col in ['RPL_CBM','RPL_CBM_DOM1','RPL_CBM_DOM2','RPL_CBM_DOM3','E_RFLD','E_BURN','E_NEHD']+['EPL_'+c for c in CODES]: d[col]=cdc[col]
    zpath=s.source(CB+'sources/EJI_2024_United_States_CSV.zip',AUTH)
    member_hash=json.loads(lp(s.source(CB+'OFFICIAL_ARCHIVE_MEMBER_HASHES.json',AUTH)).read_text())
    with zipfile.ZipFile(zpath) as z:
        for name,rec in member_hash.items():
            b=z.read(name); assert hashlib.sha256(b).hexdigest()==rec['sha256'] and len(b)==rec['bytes']
        with z.open('EJI_2024_United_States.csv') as f: national=pd.read_csv(f,dtype={'GEOID':str,'GEOID_2020':str},low_memory=False)
    eligible=national.RPL_CBM.between(0,1)&national[['EPL_'+c for c in CODES]].ge(0).all(axis=1)
    n=national.loc[eligible].set_index('GEOID'); assert len(n)==83509 and n.index.is_unique
    summed=n[['EPL_'+c for c in CODES]].sum(axis=1)
    assert np.max(np.abs(summed-n.SPL_CBM))<1e-12
    national_rank=(n.SPL_CBM.rank(method='min')-1)/(len(n)-1)
    err=np.max(np.abs(national_rank-n.RPL_CBM)); assert err<=.0000501
    np.testing.assert_allclose(n.loc[d.index,'RPL_CBM'],d.RPL_CBM,atol=2e-16,rtol=0)
    d['RPL_CBM']=n.loc[d.index,'RPL_CBM']
    ranks=pd.DataFrame(index=d.index); rows=[]
    top0=set(d.sort_values(['RPL_CBM'],ascending=False,kind='stable').head(230).index)
    oldr=frozen(s,CB+'CBM_RESEARCHER_LEAVEOUT_TRACT_RANKS.csv')
    for name,drop in REMOVALS.items():
        # Published EPLs have four decimal places; integer ticks preserve exact ties.
        score=(n[['EPL_'+c for c in CODES if c not in drop]]*10000).round().astype('int64').sum(axis=1)
        rank=(score.rank(method='min')-1)/(len(n)-1)
        ranks[name]=rank.reindex(d.index)
        oldcol='researcher_national_leaveout_'+('Wildfire' if name=='no_wildfire' else drop[0])
        previous_float_sum_max_shift=(ranks[name]-oldr[oldcol].reindex(d.index)).abs().max()
        diff=ranks[name]-d.RPL_CBM
        top=set(ranks[name].sort_values(ascending=False,kind='stable').head(230).index)
        local_delta=ranks[name].rank(method='average')-d.RPL_CBM.rank(method='average')
        rows.append(dict(diagnostic=name,removed=';'.join(drop),national_valid=len(n),tracts=2299,Pearson=d.RPL_CBM.corr(ranks[name]),
             Spearman=d.RPL_CBM.corr(ranks[name],method='spearman'),mean_abs_national_rank_shift=diff.abs().mean(),
             p90_abs_national_rank_shift=diff.abs().quantile(.9),max_abs_national_rank_shift=diff.abs().max(),
             mean_abs_local_order_shift=local_delta.abs().mean(),top230_retention=len(top&top0)/230,
             top230_changed_population=int(d.loc[list(top^top0),'Population'].sum()),
             changed_top230_tracts=len(top^top0),official_CDC_alternative=False))
        rows[-1]['prior_unrounded_sum_max_shift']=previous_float_sum_max_shift
    oldmat=np.load(s.source(MP+'VERIFIED_WEIGHTED_MATRICES.npz',AUTH))
    oldfits=np.load(s.source(MP+'REGISTERED_FIT_ARRAYS.npz',AUTH))
    np.testing.assert_array_equal(oldmat['tract_ids'],d.index)
    np.testing.assert_array_equal(oldfits['tract_ids'],d.index)
    x,mu,sd=matrix(d,'P2'); oldx=oldmat['P2__main5__cohort']
    np.testing.assert_array_equal(x,oldx)
    scale=pd.read_csv(s.source(MP+'COHORT_STANDARDIZATION_AND_WEIGHTS.csv',AUTH)).query("specification=='P2' and policy_set=='main5' and scaling=='cohort'")
    assert list(scale.variable)==P2
    np.testing.assert_allclose(scale['mean'],mu,rtol=0,atol=1e-13)
    np.testing.assert_allclose(scale.population_sd,sd,rtol=0,atol=1e-13)
    save('VERIFIED_COHORT_AND_DESCRIPTORS.csv',d.reset_index())
    save('EXCLUDED_ZERO_POPULATION_GEOIDS.csv',full.loc[full.Population.eq(0),['Population']].reset_index())
    save('NATIONAL_COMPONENT_REMOVAL_TRACT_RANKS.csv',ranks.reset_index())
    save('CBM_COMPONENT_REMOVAL_RANK_QA.csv',rows)
    save('SOURCE_HASH_VERIFICATION_PREPARE.csv',s.records)
    dump('SOURCE_RECONSTRUCTION_QA.json',dict(status='PASS',label=WARN,national_rows=len(national),national_eligible=len(n),
         max_official_rank_error=err,P2_matrix_bitwise_identical=True,original_population_and_quartiles_unchanged=True,
         source_flags_missing=['F_NEHD','F_SMOKE','F_BURN'],burn_zero_unresolved=2251,hurricane_F1_count=2299,
         formal_admission_passed=False,physical_models_rerun=False))
    print('Prepared: 950 protected files; national reranks and exact P2 matrix verified',flush=True)


if __name__=='__main__': main()
