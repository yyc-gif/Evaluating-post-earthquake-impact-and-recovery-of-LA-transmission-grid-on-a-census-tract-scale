from weight_path import *

def test_exact_cohort_and_exclusions():
 master,d,_,_=inputs();spec=json.loads((OUT/'PREDECLARED_RUN_SPECIFICATION.json').read_text())
 assert len(d)==2287 and len(master)==2291
 assert hashlib.sha256('\n'.join(d.index).encode()).hexdigest()==spec['sample_sha256']
 assert master.loc[EXCLUDED,PHYS].isna().all().all()

def test_weight_path_and_nonphysical_identity():
 _,d,_,_=inputs()
 for lam in LAMBDAS:
  xa,ca,da,sa,fa,wa=design(d,'BE0',lam);xb,cb,db,sb,fb,wb=design(d,'BE1',lam)
  assert np.array_equal(wa,(1-lam)*EQ+lam*INH) and np.array_equal(wa,wb)
  assert abs(sum(fa**2)-1)<1e-14 and abs(sum(fb**2)-1)<1e-14
  for c in ca:
   if c not in PHYS:assert np.array_equal(xa[:,ca.index(c)],xb[:,cb.index(c)])

def test_reused_endpoints_and_budget_accounting():
 spec=json.loads((OUT/'PREDECLARED_RUN_SPECIFICATION.json').read_text());r=json.loads((OUT/'FIT_EXECUTION_RECORD.json').read_text())
 assert r['new_fits']==240 and r['reused_endpoint_runs']==160 and r['total_unique_runs']==400
 assert len(spec['models'])==10 and len(SEEDS)==20 and len(LAMBDAS)==5
 for m in spec['models']:
  if m['endpoint_source']:assert sha(OUT/'run_records'/f"{m['name']}.npz")==sha(AUD/'run_records'/f"{m['endpoint_source']}.npz")
  meta=json.loads((OUT/'run_records'/f"{m['name']}.json").read_text());assert meta['payload_sha256']==sha(OUT/'run_records'/f"{m['name']}.npz")
 assert json.loads((AUD/'CONTROLLED_COMPARISON_SPECIFICATION.json').read_text())['KMeans']==PARAMS

def test_saved_predictions_use_training_scalers_and_centers():
 _,d,blocks,cases=inputs();spec=json.loads((OUT/'PREDECLARED_RUN_SPECIFICATION.json').read_text())
 for m in spec['models']:
  z=np.load(OUT/'run_records'/f"{m['name']}.npz")
  assert np.array_equal(z['tract_ids'],d.index)
  for seed in SEEDS:
   mask=~blocks.block_id.isin(cases[seed]['removed_blocks']);assert np.array_equal(mask,z[f'train_s{seed}'])
   x,cols,_,sc,f,_=design(d,m['be'],m['lambda_value'],mask)
   assert np.array_equal(sc.mean_,z[f'spatial_mean_s{seed}']) and np.array_equal(sc.scale_,z[f'spatial_scale_s{seed}'])
   cc=z[f'spatial_centers_s{seed}'];nearest=((x[:,None,:]-cc[None,:,:])**2).sum(axis=2).argmin(axis=1)
   assert np.array_equal(nearest,z[f'spatial_s{seed}'])

def test_training_only_matching_and_class_accounting():
 cls=pd.read_csv(OUT/'CLASS_MEMBERSHIP_AND_MATCHING.csv');cts=pd.read_csv(OUT/'RAW_CLASS_TRANSITIONS.csv')
 assert len(cls)==1600
 for model in cls.model.unique():
  z=np.load(OUT/'run_records'/f'{model}.npz')
  for seed in SEEDS:
   mp,al,t=align(z[f'full_s{seed}'],z[f'spatial_s{seed}'],z[f'train_s{seed}'])
   got=cls.loc[(cls.model==model)&(cls.seed==seed)&(cls.comparison=='own_full_to_spatial')]
   assert got.baseline_n.sum()==2287
   for row in got.itertuples():assert row.prediction_class==mp.get(row.reference_class,-1)

def test_domain_variance_denominators():
 c=pd.read_csv(OUT/'DOMAIN_DISTANCE_CONTRIBUTIONS.csv')
 assert np.allclose(c.total_SS,c.between_SS+c.within_SS)
 assert np.allclose(c.groupby(['model','seed']).between_fraction.sum(),1)
 assert np.allclose(c.groupby(['model','seed']).total_SS.sum(),2287)
 for _,g in c.loc[c.model=='BE0_L000'].groupby('seed'):
  assert abs(g.loc[g.domain=='grid'].total_SS.sum()/g.total_SS.sum()-.2)<1e-12
 q=json.loads((OUT/'BETWEEN_CLASS_DECOMPOSITION_VERIFICATION.json').read_text());assert q['max_source_absolute_error']<1e-12

def test_interpretation_counts_and_minority_trace():
 c=pd.read_csv(OUT/'CLASS_INTERPRETATION_ROBUSTNESS.csv');large=c.loc[c.finding=='large_group_recovery_SOVI_contrast']
 assert large.scope.value_counts().to_dict()=={'full':200,'spatial':200}
 actual=(large.loss_difference_hr>0)&(large.SOVI_difference<0)
 assert np.array_equal(actual,large.supports_joint_direction)
 z=np.load(OUT/'run_records/BE0_L000.npz');small=z['full_s42']==np.flatnonzero(np.bincount(z['full_s42'])==34)[0]
 assert small.sum()==34 and (small&z['train_s54']).sum()==4
 d=pd.read_csv(OUT/'MINORITY_DOMINANT_DESTINATION_TRACE.csv');r=d.loc[(d.model=='BE0_L000')&(d.seed==54)&(d.scope=='spatial')].iloc[0]
 assert r.intersection==34 and r.predicted_n==92 and abs(r.purity-34/92)<1e-12

def test_all_verified_input_bytes_unchanged():
 for entry in json.loads((OUT/'SOURCE_BYTE_VERIFICATION.json').read_text()):assert sha(WT/entry['file'])==entry['sha256']
