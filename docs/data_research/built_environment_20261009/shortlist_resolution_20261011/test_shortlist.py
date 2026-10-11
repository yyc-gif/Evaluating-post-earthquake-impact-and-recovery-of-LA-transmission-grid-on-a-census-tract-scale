from common import *
from controlled_shortlist import MODELS,SEEDS,domains,prepare
import numpy as np,pandas as pd
from sklearn.preprocessing import StandardScaler

def read(n):return pd.read_csv(lp(OUT/n),dtype={'tract_id':str})

def test_master_identity_and_no_imputation():
    m=read('SHORTLIST_FEATURE_MATRIX.csv');original=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_RESIDENTIAL_2291.csv')
    assert len(m)==2291 and m.tract_id.is_unique and m.tract_id.str.fullmatch(r'\d{11}').all()
    assert set(m.tract_id)==set(original.index) and m.primary2287.sum()==2287 and m.common2286.sum()==2286
    assert set(m.loc[~m.primary2287,'tract_id'])==set(UNRESOLVED)
    assert m.loc[m.tract_id.isin(UNRESOLVED),['emc2022_total_built_land_fraction','scag2020_classified_land_entropy','building_footprint_coverage']].isna().all().all()
    assert original.assessor2022_gross_floor_area_ratio.isna().all()

def test_whole_domain_accounting():
    f=read('FULL_DOMAIN_ACCOUNTING.csv');assert len(f)==2315 and f.tract_id.is_unique and f.residential_member.sum()==2291 and f.primary2287.sum()==2287

def test_scope_and_fit_ceiling():
    qa=json.loads(lp(OUT/'COMPARISON_COMPLETION_QA.json').read_text(encoding='utf-8'));s=json.loads(lp(OUT/'CONTROLLED_SHORTLIST_SPECIFICATION.json').read_text(encoding='utf-8'))
    assert qa['total_new_fits']==s['new_fit_ceiling']==460 and qa['reused_full']==qa['reused_spatial']==20
    assert s['KMeans']['n_clusters']==4 and s['KMeans']['n_init']==100 and s['seeds']==SEEDS and not s['additional_k_search']
    assert len(s['spatial_cases'])==20 and s['spatial_unique_deletion_sets']==17 and not s['final_domain_weights_selected']
    assert all('assessor2022_gross_floor_area_ratio' not in v and 'epa_household_job_activity_mix' not in v for v in MODELS.values())

def test_weights_scalers_centers_predictions_and_cases():
    f,blocks,cases,spec=prepare()
    for name,phys in MODELS.items():
        z=np.load(lp(OUT/'run_records'/(name+'.npz')));ids=z['tract_ids'];d=f.loc[ids];cols=z['feature_columns'].tolist();factors=z['coordinate_factors'];dom=domains(phys)
        assert len(d)==(2286 if name in ['CORE4','CORE3_AGE_COMMON'] else 2287)
        assert d[cols].notna().all().all() and np.isclose(np.square(factors).sum(),1)
        for fields in dom.values():assert np.isclose(sum(factors[cols.index(c)]**2 for c in fields),.2)
        scaler=StandardScaler().fit(d[cols]);assert np.allclose(scaler.mean_,z['scaler_mean'],rtol=1e-12,atol=1e-11) and np.allclose(scaler.scale_,z['scaler_scale'],rtol=1e-12,atol=1e-11)
        x=scaler.transform(d[cols])*factors
        for seed in SEEDS:
            labels=z[f's{seed}_labels'];cent=z[f's{seed}_centers'];pred=np.square(x[:,None,:]-cent[None,:,:]).sum(axis=2).argmin(axis=1)
            if name!='HIST':assert np.array_equal(pred,labels)
            else:
                meta=json.loads(lp(OUT/'run_records/HIST.json').read_text(encoding='utf-8'))
                assert meta['full_center_provenance']=='DESCRIPTIVE_PARTITION_MEANS_ORIGINAL_FULL_ESTIMATOR_CENTERS_UNAVAILABLE'
                for k in range(4):assert np.allclose(cent[k],x[labels==k].mean(axis=0))
            mask=~blocks.loc[ids].block_id.isin(cases[seed]).to_numpy();assert np.array_equal(mask,z[f's{seed}_train_mask'])
            sc=StandardScaler().fit(d.loc[mask,cols]);assert np.allclose(sc.mean_,z[f's{seed}_spatial_mean']) and np.allclose(sc.scale_,z[f's{seed}_spatial_scale'])
            xx=sc.transform(d[cols])*factors;pp=np.square(xx[:,None,:]-z[f's{seed}_spatial_centers'][None,:,:]).sum(axis=2).argmin(axis=1);assert np.array_equal(pp,z[f's{seed}_spatial_prediction'])

def test_historical_fits_reused_exactly():
    z=np.load(lp(OUT/'run_records/HIST.npz'));old=np.load(source('final_feature_validation_20261010/run_records/D__equal_five_domains.npz'))
    for seed in SEEDS:
        assert np.array_equal(z[f's{seed}_labels'],old[f's{seed}_k4'])
        sp=np.load(source(f'spatial_k4_validation_20261010/run_records/D_s{seed}.npz'));assert np.array_equal(z[f's{seed}_spatial_prediction'],sp['raw_prediction'])
    rows=read('BOUNDED_RUN_RECORDS.csv');h=rows.loc[rows.model.eq('HIST')];assert h.full_fit_source.eq('REUSED_EXACT_HISTORICAL_FIT').all() and h.spatial_fit_source.eq('REUSED_EXACT_HISTORICAL_FIT').all()

def test_conditional_age_common_sample():
    a=np.load(lp(OUT/'run_records/CORE4.npz'));b=np.load(lp(OUT/'run_records/CORE3_AGE_COMMON.npz'));c=np.load(lp(OUT/'run_records/CORE3.npz'))
    assert np.array_equal(a['tract_ids'],b['tract_ids']) and set(c['tract_ids'])-set(a['tract_ids'])=={'06037115103'}

def test_complete_cross_tables_and_class_metrics():
    x=read('SPATIAL_RAW_CONTINGENCIES.csv');runs=read('BOUNDED_RUN_RECORDS.csv').set_index(['model','seed']);assert len(x)==12*20*3*16
    for (model,seed,scope),g in x.groupby(['model','seed','scope']):
        r=runs.loc[(model,seed)];expected=r.cohort_n if scope=='full' else r.training_n if scope=='training' else r.heldout_n;assert g.n.sum()==expected
    m=read('SPATIAL_CLUSTER_MATCHING.csv');assert (m.intersection<=m.baseline_n).all() and (m.intersection<=m.predicted_n).all()
    assert np.allclose(m.loc[m.baseline_n.gt(0),'retention'],m.loc[m.baseline_n.gt(0),'intersection']/m.loc[m.baseline_n.gt(0),'baseline_n'])
    assert np.allclose(m.loc[m.predicted_n.gt(0),'purity'],m.loc[m.predicted_n.gt(0),'intersection']/m.loc[m.predicted_n.gt(0),'predicted_n'])
    assert np.allclose(m.Jaccard,m.intersection/m.union,equal_nan=True)

def test_epa_stress_test_preserves_baseline_and_totals():
    s=read('EPA_ALLOCATION_SENSITIVITY_SUMMARY.csv');assert len(s)==5 and s.count_conservation_error_max.max()<1e-6
    x=read('EPA_ALLOCATION_SENSITIVITY.csv');assert len(x)==5*2291 and not x.duplicated(['scenario','tract_id']).any()
    baseline=x.loc[x.scenario.eq('uniform_land')];assert baseline.difference_from_uniform_land.abs().max()<1e-10
    assert x.loc[x.tract_id.isin(UNRESOLVED),'activity_mix'].isna().all()

def test_survey_replicates_and_no_precision_deletion():
    z=np.load(lp(OUT/'ACS_CONFIGURATION_REPLICATES.npz'));q=read('ACS_CONFIGURATION_UNCERTAINTY.csv');assert z['housing_5plus_share'].shape==z['housing_detached_share'].shape==(2287,80)
    assert q.no_precision_exclusion.all() and q.zero_rep_denominator_tract_n.eq(0).all() and q.moe90_max.max()>1

def test_feasible_missing_land_bounds():
    x=read('SCAG_CLASSIFIED_LAND_SUPPORT_BOUNDS.csv');valid=x.dropna(subset=['possible_whole_land_entropy_lower','possible_whole_land_entropy_upper']);assert len(valid)==2*2287
    assert valid.possible_whole_land_entropy_lower.ge(-1e-10).all() and valid.possible_whole_land_entropy_upper.le(1+1e-10).all()
    assert valid.bound_width.ge(-1e-10).all()

def test_recommendation_and_all_register_dispositions():
    d=read('FINAL_SHORTLIST_DISPOSITIONS.csv');assert len(d)==64 and d.candidate_id.is_unique
    assert set(d.loc[d.shortlist_decision.eq('PREFERRED_PRIMARY'),'candidate_id'])=={'emc2022_total_built_land_fraction','housing_5plus_share','scag2020_classified_land_entropy'}
    assert d.loc[d.candidate_id.eq('assessor2022_gross_floor_area_ratio'),'shortlist_decision'].iloc[0]=='INELIGIBLE'
    for n in ['FINAL_VARIABLE_RECOMMENDATION.md','FINAL_CANDIDATE_CONSTRUCT_DECISION.md','DOMAIN_WEIGHT_REQUIREMENTS.md']:
        assert lp(OUT/n).stat().st_size>2000

def test_input_byte_hashes():
    h=json.loads(lp(OUT/'INPUT_HASHES.json').read_text(encoding='utf-8'))
    for r in h.values():assert sha(r['path'])==r['sha256'] and lp(r['path']).stat().st_size==r['bytes']

def test_original_worktree_preservation():
    b=json.loads(lp(OUT/'PRESERVATION_BEFORE.json').read_text(encoding='utf-8'));a=json.loads(lp(OUT/'PRESERVATION_AFTER.json').read_text(encoding='utf-8'));assert a==b
