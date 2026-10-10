"""Independent numerical checks of saved fits; never runs KMeans.fit."""
import json,itertools
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from spatial_k4 import ROOT,BASE,OUT,PARENT,SEEDS,MODELS,PROFILES,sha,frame,git,mapping
Q=json.loads((OUT/'INPUT_AND_BASELINE_QA.json').read_text())
F=frame('FINAL_CANDIDATE_FEATURE_MATRIX.csv');D=F.loc[F.primary_complete_case]
R=pd.read_csv(OUT/'SPATIAL_K4_RUNS.csv')
MATCH=pd.read_csv(OUT/'SPATIAL_K4_CLUSTER_MATCHING.csv')
PROFILE=pd.read_csv(OUT/'SPATIAL_K4_PROFILE_STABILITY.csv')
def observations():
 for model in MODELS:
  for seed in SEEDS:
   yield model,seed,np.load(OUT/f'run_records/{model}_s{seed}.npz'),json.loads((OUT/f'run_records/{model}_s{seed}.json').read_text())
def test_identity_and_no_imputation():
 assert len(F)==2291 and len(D)==2287 and F.index.str.fullmatch(r'\d{11}').all()
 assert F.index[~F.primary_complete_case].tolist()==Q['unresolved_residential']
 assert F.loc[Q['unresolved_residential'],['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share']].isna().all().all()
 assert all(sha(ROOT/r['file'])==r['sha256'] for r in Q['source_files'])
def test_budget_and_saved_baseline():
 ledger=json.loads((OUT/'FIT_EXECUTION_RECORD.json').read_text());assert ledger['total_unique_fits']==40 and ledger['new_fits_this_invocation']==40 and ledger['full_sample_baseline_refits']==0 and ledger['k_search_fits']==0
 assert len(R)==40 and not R.duplicated(['model','seed']).any()
 for model,seed,z,meta in observations():
  assert meta['spec']['KMeans']==dict(n_clusters=4,n_init=100,max_iter=500,tol=1e-4,algorithm='lloyd',random_state=seed)
  assert z['tract_ids'].tolist()==D.index.tolist()
  assert np.array_equal(z['baseline_labels'],np.load(BASE/f'run_records/{model}__equal_five_domains.npz')[f's{seed}_k4'])
  assert meta['spec']['removed_blocks']==Q['spatial_deletion_sets'][str(seed)]['removed_blocks']
def test_scalers_weights_centers_and_predictions():
 for model,seed,z,meta in observations():
  fields=z['feature_columns'].tolist();train=z['train_mask'];raw=D.loc[z['tract_ids'],fields].to_numpy()
  assert np.allclose(z['scaler_mean'],raw[train].mean(axis=0),rtol=1e-12,atol=1e-12)
  assert np.allclose(z['scaler_var'],raw[train].var(axis=0),rtol=1e-11,atol=1e-12)
  for domain,cols in meta['spec']['domains'].items():
   ix=[fields.index(c) for c in cols];assert np.isclose((z['coordinate_factors'][ix]**2).sum(),.2)
  x=(raw-z['scaler_mean'])/z['scaler_scale']*z['coordinate_factors'];dist=((x[:,None,:]-z['cluster_centers'][None,:,:])**2).sum(axis=2)
  assert np.array_equal(dist.argmin(axis=1),z['raw_prediction'])
  assert np.isclose(dist[np.flatnonzero(train),z['raw_prediction'][train]].sum(),meta['inertia'],rtol=1e-11,atol=1e-9)
def test_training_only_optimal_mapping_and_metrics():
 for model,seed,z,meta in observations():
  y=z['baseline_labels'];p=z['raw_prediction'];t=z['train_mask'];ct=np.zeros((4,4),int);np.add.at(ct,(y[t],p[t]),1)
  chosen=MATCH.loc[MATCH.model.eq(model)&MATCH.seed.eq(seed)&MATCH.scope.eq('full')].sort_values('baseline_seed_cluster')
  pairs={int(r.baseline_seed_cluster)-1:int(r.matched_prediction_raw_cluster)-1 for r in chosen.itertuples() if r.training_support=='SUPPORTED'}
  score=sum(ct[a,b] for a,b in pairs.items());assert score==max(sum(ct[a,perm[a]] for a in range(4)) for perm in itertools.permutations(range(4)))
  for scope,mask in [('training',t),('heldout',~t),('full',np.ones(len(y),bool))]:
   rows=MATCH.loc[MATCH.model.eq(model)&MATCH.seed.eq(seed)&MATCH.scope.eq(scope)]
   for r in rows.itertuples():
    a=r.baseline_seed_cluster-1;assert int(r.matched_prediction_raw_cluster)-1==pairs[a]
    b=pairs[a];base=(y==a)&mask;pr=(p==b)&mask;inter=(base&pr).sum();union=(base|pr).sum()
    assert r.baseline_n==base.sum() and r.predicted_n==pr.sum() and r.intersection==inter and r.union==union
    for actual,expect in [(r.retention,inter/base.sum() if base.sum() else np.nan),(r.purity,inter/pr.sum() if pr.sum() else np.nan),(r.jaccard,inter/union if union else np.nan)]:assert np.isclose(actual,expect,equal_nan=True)
def test_zero_training_support_is_not_assigned():
 y=np.array([0,0,1,1,2,2,3,3]);p=np.array([2,2,0,0,1,1,3,3]);t=np.array([1,1,1,1,1,1,0,0],bool)
 mp,ct=mapping(y,p,t);assert 3 not in mp and set(mp)=={0,1,2} and not ct[3].any()
def test_ari_reference_and_cross_tables():
 cross=pd.read_csv(OUT/'SPATIAL_K4_CROSSTABS.csv')
 for model,seed,z,meta in observations():
  y=z['baseline_labels'];p=z['raw_prediction'];t=z['train_mask'];row=R.loc[R.model.eq(model)&R.seed.eq(seed)].iloc[0]
  assert np.isclose(row.full_ARI,adjusted_rand_score(y,p)) and np.isclose(row.heldout_ARI,adjusted_rand_score(y[~t],p[~t])) and np.isclose(row.training_ARI,adjusted_rand_score(y[t],p[t]))
  for scope,mask in [('full',np.ones(len(y),bool)),('training',t),('heldout',~t)]:
   expected=np.zeros((4,4),int);np.add.at(expected,(y[mask],p[mask]),1);c=cross.loc[cross.model.eq(model)&cross.seed.eq(seed)&cross.scope.eq(scope)].pivot(index='baseline_seed_cluster',columns='prediction_raw_cluster',values='n');assert np.array_equal(c.to_numpy(),expected)
def test_profile_decomposition_and_original_units():
 for model,seed,z,meta in observations():
  y=z['baseline_labels'];p=z['raw_prediction'];t=z['train_mask'];pairs=MATCH.loc[MATCH.model.eq(model)&MATCH.seed.eq(seed)&MATCH.scope.eq('full')]
  for rr in pairs.itertuples():
   a=rr.baseline_seed_cluster-1;b=int(rr.matched_prediction_raw_cluster)-1;rows=PROFILE.loc[PROFILE.model.eq(model)&PROFILE.seed.eq(seed)&PROFILE.baseline_seed_cluster.eq(a+1)]
   for field in ['B_480_hr','Init_Supply','SOVI_SCORE','land_use_classified_land_coverage','all_use2014_age_coverage']:
    values=D[field].to_numpy();base=values[y==a];fixed=values[(y==a)&t];full=values[p==b];tr=values[(p==b)&t]
    for group,v in [('fixed_original_members_retained_training',fixed),('reclassified_matched_full_population',full),('reclassified_matched_training_population',tr)]:
     row=rows.loc[rows.feature.eq(field)&rows.profile_population.eq(group)].iloc[0]
     assert np.isclose(row.baseline_mean,np.nanmean(base)) and np.isclose(row['mean'],np.nanmean(v))
     assert np.isclose(row.p10,np.nanquantile(v,.1)) and np.isclose(row.p90,np.nanquantile(v,.9))
     assert np.isclose(row.fixed_members_deletion_mean_change+row.training_reclassification_mean_change,np.nanmean(tr)-np.nanmean(base))
def test_small_members_and_tract_accounting():
 labels=np.load(BASE/'run_records/D__equal_five_domains.npz')['s42_k4'];cid=np.flatnonzero(np.bincount(labels)==34);assert len(cid)==1
 members=set(D.index[labels==cid[0]]);assert members==set(Q['small_D_seed42_members'])
 a=pd.read_csv(OUT/'SMALL_CLUSTER_34_AUDIT.csv');pred=pd.read_csv(OUT/'SPATIAL_K4_TRACT_PREDICTIONS.csv',dtype={'tract_id':str});assert len(pred)==40*2287 and not pred.duplicated(['model','seed','tract_id']).any() and pred.tract_id.str.fullmatch(r'\d{11}').all()
 assert not set(pred.tract_id)&set(Q['unresolved_residential'])
 for model,seed,z,meta in observations():
  mask=D.index.isin(members);row=a.loc[a.model.eq(model)&a.seed.eq(seed)&a.target.eq('D_SEED42_34')].iloc[0]
  assert row.training_target_n==(mask&z['train_mask']).sum()
  assert row.original_members_in_match==((z['raw_prediction']==row.matched_raw_prediction_cluster-1)&mask).sum()
def test_protected_files_and_index():
 b=json.loads((OUT/'PRESERVATION_BASELINE.json').read_text());assert all(sha(ROOT/k)==h for k,h in b['protected_files'].items())
 assert git('ls-files','--stage','-z')==(OUT/'original_state/index.bin').read_bytes()
 assert git('rev-parse','HEAD').decode().strip()==b['head']
