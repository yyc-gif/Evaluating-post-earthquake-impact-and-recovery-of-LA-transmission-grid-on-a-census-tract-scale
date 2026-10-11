import json,hashlib
import numpy as np,pandas as pd
from controlled_audit import OUT,BASE,SP,inputs,specs,design,PARAMS,SEEDS,sha,mapping

def test_exact_cohort_and_exclusions():
 master,d,blocks,sets=inputs()
 assert len(master)==2291 and len(d)==2287 and len(sets)==20
 spec=json.loads((OUT/'CONTROLLED_COMPARISON_SPECIFICATION.json').read_text())
 assert hashlib.sha256('\n'.join(d.index).encode()).hexdigest()==spec['sample_sha256']
 assert spec['maximum_new_fits']==880 and not spec['k_search']

def test_weights_and_protected_coordinates():
 _,d,_,_=inputs();reference=specs()[0];x0,c0,dom0,sc0,w0=design(d,reference)
 for s in specs():
  x,cols,dom,sc,w=design(d,s)
  if s['physical_weight_mode']=='redistribute':
   assert np.isclose(sum(w[cols.index(c)]**2 for c in dom['physical']),.2 if s['budget']=='equal' else 2/11)
  else:assert all(np.isclose(w[cols.index(c)]**2,.2/3) for c in dom['physical'])
  assert dom['recovery_service']==['B_480_hr','Init_Supply']
  assert dom['social']==['SOVI_SCORE'] and dom['grid']==dom0['grid']
  if s['budget']=='equal' and s['risk']=='D':
   for c in [c for v in dom0.values() for c in v if c not in dom0['physical']]:assert np.array_equal(x[:,cols.index(c)],x0[:,c0.index(c)])

def test_saved_baselines_reused_and_new_predictions_reproducible():
 _,d,blocks,sets=inputs()
 for s in specs():
  cp=OUT/'run_records'/f"{s['name']}.npz";meta=json.loads(cp.with_suffix('.json').read_text());z=np.load(cp)
  assert sha(cp)==meta['payload_sha256']
  x,cols,dom,sc,w=design(d,s);assert z['tract_ids'].tolist()==d.index.tolist()
  if s['saved_full_source']:
   orig=np.load(BASE/'run_records'/f"{s['saved_full_source']}.npz")
   for seed in SEEDS:assert np.array_equal(z[f'full_s{seed}'],orig[f's{seed}_k4'])
  for seed in SEEDS:
   mask=z[f'train_s{seed}'];expected=~blocks.block_id.isin(sets[seed]['removed_blocks']).to_numpy();assert np.array_equal(mask,expected)
   xp,_,_,ss,_=design(d,s,pd.Series(mask,index=d.index));assert np.array_equal(ss.mean_,z[f'spatial_mean_s{seed}']) and np.array_equal(ss.scale_,z[f'spatial_scale_s{seed}'])
   cc=z[f'spatial_centers_s{seed}'];dist=((xp[:,None,:]-cc[None,:,:])**2).sum(axis=2)
   assert np.allclose(dist[np.arange(len(d)),z[f'spatial_s{seed}']],dist.min(axis=1),atol=1e-12,rtol=1e-12)
   if s['saved_spatial_source']:
    orig=np.load(SP/'run_records'/f"{s['saved_spatial_source']}_s{seed}.npz")
    assert np.array_equal(z[f'spatial_s{seed}'],orig['raw_prediction'])

def test_counter_limits_and_distinct_records():
 run=json.loads((OUT/'FIT_EXECUTION_RECORD.json').read_text());assert run['new_fits_this_invocation']==880 and run['reused_saved_runs']==280
 for name in ['BUILT_ENV_ABLATION_RESULTS.csv','BUILT_ENV_SPATIAL_SENSITIVITY.csv']:
  f=pd.read_csv(OUT/name);assert len(f)==580 and not f.duplicated(['model','seed']).any()
 assert run['simulation_runs']==run['GA_runs']==run['GIS_extractions']==run['k_searches']==0

def test_mapping_uses_training_only_and_preserves_raw_membership():
 _,d,_,_=inputs();r=pd.read_csv(OUT/'BUILT_ENV_SPATIAL_SENSITIVITY.csv')
 for s in specs():
  z=np.load(OUT/'run_records'/f"{s['name']}.npz")
  for seed in SEEDS:
   y,p,mask=z[f'full_s{seed}'],z[f'spatial_s{seed}'],z[f'train_s{seed}'];mp,aligned,tab=mapping(y,p,mask)
   assert tab.sum()==mask.sum()
   row=r.loc[r.model.eq(s['name'])&r.seed.eq(seed)].iloc[0]
   assert row.aligned_reassigned_n==(aligned!=y).sum()
 m=pd.read_csv(OUT/'SMALL_34_GROUP_SENSITIVITY.csv');row=m.loc[m.model.eq('BE0')&m.seed.eq(54)&m.scope.eq('spatial')].iloc[0]
 assert row.training_target_n==4 and row.predicted_n==92 and row.intersection==34
 assert np.isclose(row.purity,34/92) and row.retention==1

def test_source_payloads_unchanged():
 from controlled_audit import WT
 records=pd.read_csv(OUT/'SOURCE_HASHES.csv')
 for _,r in records.iterrows():assert sha(WT/r.file)==r.sha256
