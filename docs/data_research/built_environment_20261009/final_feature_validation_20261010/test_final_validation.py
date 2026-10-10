"""Independent numerical and scientific-boundary tests for new analysis only."""
import json,hashlib,itertools
import numpy as np,pandas as pd
from scipy.stats import entropy as scipy_entropy
from sklearn.metrics import adjusted_rand_score,silhouette_score,pairwise_distances
from validate_stage7 import ROOT,OUT,OLD,read,CLASSES
from controlled_clustering import variants,design,SEEDS,KS
def test_exact_sample_and_null_preservation():
 f=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);original=read('clusters_labels_final.csv',ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized');assert f.index.tolist()==original.index.tolist();assert len(f)==2291 and f.index.is_unique
 assert f.primary_complete_case.sum()==2287 and f.legacy2276_complete_case.sum()==2276
 assert set(f.index[~f.primary_complete_case])=={'06037189703','06037301601','06037301602','06037404600'}
 for c in ['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share']:assert f.loc[~f.primary_complete_case,c].isna().all()
 for c in ['T80','Init_Supply','SOVI_SCORE','NRI_BUILDVALUE']+['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']:assert np.allclose(f[c],original[c],atol=1e-10,rtol=1e-11)
def test_mask_dispositions_and_correction_arithmetic():
 q=read('LANDMASK_18_TRACT_RESOLUTION.csv',OUT);assert len(q)==18 and q.residential_member.sum()==15
 assert q.status.str.startswith('CORRECTED').sum()==4 and q.status.str.startswith('RESOLVED').sum()==8 and q.status.str.startswith('UNRESOLVED').sum()==6
 assert q.recomputed_vs_cached_land_error_m2.abs().max()<1e-6
 assert np.allclose(q.after_relative_error,q.after_land_area_m2/q.census_ALAND_m2-1,atol=1e-13)
 assert q.loc[q.status.str.startswith('CORRECTED'),'after_relative_error'].abs().max()<2e-6
 r=read('CORRECTED_TRACT_INTERSECTIONS.csv',OUT)
 assert np.allclose(r[[c+'_area_m2' for c in CLASSES]].sum(axis=1),r.land_use_classified_area_m2,atol=1e-7)
 assert (r.building_footprint_union_area_m2<=r.land_geometry_area_m2).all()
 for _,row in r.iterrows():assert abs(scipy_entropy(row[[c+'_area_m2' for c in CLASSES]].to_numpy(float))/np.log(11)-row.land_use_entropy)<1e-12
def test_entropy_allocation_bounds_and_scale_invariance():
 d=pd.read_csv(OUT/'SCAG_ENTROPY_SENSITIVITY.csv')
 assert len(d)==2315*4 and not d[['tract_id','scenario']].duplicated().any()
 p=d.loc[d.scenario.eq('missing_proportional')];assert p.change.abs().max()<1e-12
 assert np.all(d.entropy>=d.entropy_unconstrained_lower_bound-1e-12) and np.all(d.entropy<=d.entropy_unconstrained_upper_bound+1e-12)
 assert np.all(d.entropy.between(0,1))
def test_age_missing_bounds_are_not_imputations():
 d=read('BUILDING_AGE_SENSITIVITY.csv',OUT);a=d.all_use2014_footprint_union_area_m2;v=d.all_use2014_valid_age_area_m2;p=d.all_use2014_pre1970_area_m2
 assert np.allclose(d.all_use2014_pre1970_area_share,p/v,atol=1e-12)
 assert np.allclose(d.all_use2014_pre1970_lower_bound,p/a,atol=1e-12)
 assert np.allclose(d.all_use2014_pre1970_upper_bound,(p+a-v)/a,atol=1e-12)
 assert np.all(d.all_use2014_pre1970_lower_bound<=d.all_use2014_pre1970_area_share+1e-12)
 assert np.all(d.all_use2014_pre1970_upper_bound>=d.all_use2014_pre1970_area_share-1e-12)
 assert d.strict_2020_transfer_age_coverage_diagnostic.median()<.05
def test_frozen_recovery_integral_and_order():
 full=read('RECOVERY_B_T80_INIT_COMPARISON.csv');p=ROOT/'Formal_Experiment_20260923/Formal_Offline_Evaluation/2pc50__C57_D1__direct-community__INTEGRALS.npz'
 with np.load(p,allow_pickle=False) as n:
  vals=n['M1_UTILITY_003__normalized_burden_hr'];assert vals.shape==(1000,2315);assert np.allclose(vals.mean(axis=0),full.B_480_hr,atol=1e-10)
 f=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);assert np.allclose(f.B_480_hr,full.loc[f.index,'B_480_hr'],atol=1e-10)
 assert np.allclose(full.AUC_480,1-full.B_480_hr/480,atol=1e-12)
def test_complete_run_accounting_and_weights():
 r=pd.read_csv(OUT/'CONTROLLED_CLUSTERING_COMPARISON.csv');specs=variants();assert len(r)==len(specs)*20*7
 assert not r[['model','seed','k']].duplicated().any();assert r.n_init.eq(100).all()
 for name,g in r.groupby('model'):
  assert set(g.seed)==set(SEEDS) and set(g.k)==set(KS);assert g.groupby('seed').selected_run.sum().eq(1).all()
 weights=pd.read_csv(OUT/'CLUSTER_DOMAIN_WEIGHTS.csv');assert np.allclose(weights.groupby('model').coordinate_squared_weight.sum(),1)
 for budget in ['inherited','equal_five_domains']:
  a=weights.loc[weights.model.eq('D__'+budget)&weights.domain.eq('loss_exposure'),'coordinate_squared_weight'].sum();b=weights.loc[weights.model.eq('EAL__'+budget)&weights.domain.eq('loss_exposure'),'coordinate_squared_weight'].sum();assert abs(a-b)<1e-12
def test_saved_ari_and_silhouette_reproduce():
 f=read('FINAL_CANDIDATE_FEATURE_MATRIX.csv',OUT);d=f.loc[f.primary_complete_case];s=variants()[0];matrix,*_=design(d,s)
 n=np.load(OUT/'run_records/D__inherited.npz');r=pd.read_csv(OUT/'CONTROLLED_CLUSTERING_COMPARISON.csv');row=r.loc[r.model.eq('D__inherited')&r.seed.eq(42)&r.k.eq(5)].iloc[0]
 assert abs(silhouette_score(matrix,n['s42_k5'])-row.silhouette)<1e-10
 p=pd.read_csv(OUT/'CLUSTER_WITHIN_MODEL_PAIRWISE_ARI.csv');row=p.loc[p.model.eq('D__inherited')&p.role.eq('fixed_k5')&p.seed_a.eq(42)&p.seed_b.eq(43)].iloc[0];assert abs(adjusted_rand_score(n['s42_k5'],n['s43_k5'])-row.ari)<1e-12
def test_spatial_block_and_profile_accounting():
 sp=pd.read_csv(OUT/'SPATIAL_BLOCK_STABILITY.csv');assert len(sp)==80 and set(sp.seed)==set(SEEDS);assert sp.groupby('model').size().eq(20).all();assert (sp.n_training+sp.n_heldout).eq(2287).all();assert sp.full_prediction_ARI.between(-1,1).all()
 p=pd.read_csv(OUT/'CLUSTER_STABILITY_AND_PROFILES.csv');x=p.loc[p.record_type.eq('DESCRIPTIVE_PROFILE')&p.feature.eq('B_480_hr')];r=pd.read_csv(OUT/'CONTROLLED_CLUSTERING_COMPARISON.csv')
 for (model,role),g in x.groupby(['model','role']):assert g.n_cluster.sum()==r.loc[r.model.eq(model),'n'].iloc[0]
