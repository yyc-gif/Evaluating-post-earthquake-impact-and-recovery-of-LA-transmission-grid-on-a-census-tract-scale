from common import *
import numpy as np,pandas as pd,itertools
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score
from scipy.optimize import linear_sum_assignment

def read(n):return pd.read_csv(lp(OUT/n),dtype={'tract_id':str})
def records(w):return np.load(lp(OUT/'run_records'/(w+'.npz')))
def inputarray():return np.load(lp(OUT/'CORE3_EXACT_INPUTS.npz'))
def independent_mapping(a,b,mask):
    counts=np.array([[int(((a==i)&(b==j)&mask).sum()) for j in range(4)] for i in range(4)]);i,j=linear_sum_assignment(-counts);mp=dict(zip(j,i));return np.array([mp[k] for k in b]),mp

def test_exact_input_membership_and_master_nulls():
    master,f,blocks,cases,spec=inputs();z=inputarray();m=read('CORE3_MASTER_2291.csv')
    assert len(m)==2291 and m.tract_id.is_unique and m.tract_id.str.fullmatch(r'\d{11}').all()
    assert len(z['tract_ids'])==2287 and np.array_equal(z['tract_ids'],f.index) and np.array_equal(z['values'],f[COLS].to_numpy())
    missing=m.classification_status.eq('UNCLASSIFIED_GEOMETRY');assert set(m.loc[missing,'tract_id'])==set(UNRESOLVED)
    assert m.loc[missing,['emc2022_total_built_land_fraction','scag2020_classified_land_entropy']].isna().all().all()
    # ACS is not a geometry measurement: retain observed residential values.
    actual=m.set_index('tract_id').loc[UNRESOLVED,'housing_5plus_share']
    expected=master.loc[UNRESOLVED,'housing_5plus_share']
    assert np.allclose(actual,expected,rtol=1e-14,equal_nan=True)
    assert z['feature_columns'].tolist()==COLS and len(COLS)==12

def test_preregistered_only_five_schemes_and_budget():
    s=json.loads(lp(OUT/'PREREGISTERED_SPECIFICATION.json').read_text());assert list(s['schemes'])==['W1','W2','W3','W4','W5']
    assert s['KMeans']==PARAMS and s['seeds']==list(range(42,62)) and s['new_fit_ceiling']==160 and not s['new_k_search'] and not s['new_variable_selection']
    prescribed=[[.2,.2,.2,.2,.1,.1],[1/6]*6,[2/11,4/11,2/11,1/11,1/11,1/11],[.2,.2,.2,.2,.05,.15],[.2,.2,.2,.2,.15,.05]]
    w=read('CORE3_WEIGHT_VECTORS.csv')
    for k,v in zip(s['schemes'],prescribed):
        q=w.loc[w.scheme.eq(k)];assert len(q)==12 and np.isclose(q.coordinate_squared_weight.sum(),1)
        for dom,budget in zip(DOMAIN_COLUMNS,v):assert np.isclose(q.loc[q.domain.eq(dom),'coordinate_squared_weight'].sum(),budget)
        assert np.allclose(np.square(q.standardized_multiplier),q.coordinate_squared_weight,atol=1e-15)
    assert s['software']['sklearn']=='1.5.1' and s['software']['numpy']=='1.26.4'

def test_w1_saved_actual_estimator_bytes_reused():
    assert sha(OUT/'run_records/W1.npz')==sha(source(REVIEW+'run_records/CORE3.npz'))
    m=json.loads(lp(OUT/'run_records/W1.json').read_text());old=json.loads(source(REVIEW+'run_records/CORE3.json').read_text())
    assert m['signature']['weighted_matrix_sha256']==old['signature']['matrix_sha256'] and m['completed_seeds']==SEEDS
    assert m['center_provenance']=='ACTUAL_SAVED_ESTIMATOR_CENTERS'
    q=json.loads(lp(OUT/'FIT_COMPLETION_QA.json').read_text());assert q['total_new_fits']==160 and q['existing_W1_fits_reused']==40

def test_all_actual_estimators_scalers_and_predictions():
    z=inputarray();values=z['values'];ids=z['tract_ids'];blocks=z['block_ids'];spec=json.loads(lp(OUT/'PREREGISTERED_SPECIFICATION.json').read_text());sc=StandardScaler().fit(values)
    _,frame,_,_,_=inputs()
    for w in WEIGHTS:
        a=records(w);meta=json.loads(lp(OUT/'run_records'/(w+'.json')).read_text());assert meta['signature']['preregistration_sha256']==sha(OUT/'PREREGISTERED_SPECIFICATION.json')
        assert np.array_equal(a['tract_ids'],ids) and np.array_equal(a['scaler_mean'],sc.mean_) and np.array_equal(a['scaler_scale'],sc.scale_)
        f=a['coordinate_factors'];assert np.array_equal(f,factors(w));x=sc.transform(values)*f
        for seed in SEEDS:
            train=~np.isin(blocks,spec['spatial_cases'][str(seed)]);assert np.array_equal(train,a[f's{seed}_train_mask'])
            # Use the original DataFrame layout for a bitwise scaling check.
            # Advanced NumPy indexing changes reduction order at approximately 1e-13.
            ss=StandardScaler().fit(frame.loc[train,COLS]);assert np.array_equal(ss.mean_,a[f's{seed}_spatial_mean']) and np.array_equal(ss.scale_,a[f's{seed}_spatial_scale'])
            pred=np.square(x[:,None,:]-a[f's{seed}_centers'][None,:,:]).sum(axis=2).argmin(axis=1);assert np.array_equal(pred,a[f's{seed}_labels'])
            xx=ss.transform(frame[COLS])*f;spred=np.square(xx[:,None,:]-a[f's{seed}_spatial_centers'][None,:,:]).sum(axis=2).argmin(axis=1);assert np.array_equal(spred,a[f's{seed}_spatial_prediction'])

def test_variance_decomposition_and_realized_budgets():
    values=inputarray()['values'];zs=StandardScaler().fit_transform(values);q=read('CORE3_FEATURE_DISTANCE_CONTRIBUTIONS.csv');d=read('CORE3_DOMAIN_SEPARATION.csv')
    for w in WEIGHTS:
        a=records(w);x=zs*a['coordinate_factors'];tss=np.square(x-x.mean(axis=0)).sum(axis=0)
        for seed in SEEDS:
            y=a[f's{seed}_labels'];bss=np.zeros(12);wss=np.zeros(12)
            for k in range(4):
                block=x[y==k];mean=block.mean(axis=0);bss+=len(block)*np.square(mean-x.mean(axis=0));wss+=np.square(block-mean).sum(axis=0)
            r=q.loc[q.scheme.eq(w)&q.seed.eq(seed)].set_index('feature').loc[COLS]
            assert np.allclose(r.TSS,tss,atol=1e-10) and np.allclose(r.BSS,bss,atol=1e-10) and np.allclose(r.WSS,wss,atol=1e-10) and np.allclose(tss,bss+wss,atol=1e-10)
            dr=d.loc[d.scheme.eq(w)&d.seed.eq(seed)]
            assert np.isclose(dr.domain_between_fraction.sum(),1) and np.allclose(dr.TSS,2287*dr.nominal_squared_budget,atol=1e-9)
            assert np.allclose(dr.domain_explained_fraction,dr.BSS/dr.TSS) and np.allclose(dr.domain_between_fraction,dr.BSS/dr.BSS.sum())

def test_full_transitions_and_reassignment():
    q=read('CORE3_WEIGHT_CLASS_TRANSITIONS.csv');c=read('CORE3_SAME_SEED_W1_COMPARISONS.csv');assert len(q)==5*20*16
    for (w,seed),g in q.groupby(['scheme','seed']):
        assert g.n.sum()==2287;labels=records(w)[f's{seed}_labels'];ref=records('W1')[f's{seed}_labels'];mapped,mp=independent_mapping(ref,labels,np.ones(2287,bool));r=c.loc[c.scheme.eq(w)&c.seed.eq(seed)].iloc[0]
        assert r.reassigned_n==int((mapped!=ref).sum()) and np.isclose(r.ARI_vs_W1,adjusted_rand_score(ref,labels))
        for _,row in g.iterrows():assert row.n==int(((ref==row.W1_same_seed_raw_class)&(labels==row.scheme_raw_class)).sum())

def test_spatial_ari_tables_and_training_only_matching():
    q=read('CORE3_WEIGHT_SPATIAL_STABILITY.csv');ct=read('CORE3_SPATIAL_RAW_CONTINGENCIES.csv');metrics=read('CORE3_SPATIAL_CLASS_METRICS.csv');assert len(ct)==5*20*3*16
    for w in WEIGHTS:
        a=records(w)
        for seed in SEEDS:
            y=a[f's{seed}_labels'];p=a[f's{seed}_spatial_prediction'];train=a[f's{seed}_train_mask'];mapped,mp=independent_mapping(y,p,train);r=q.loc[q.scheme.eq(w)&q.seed.eq(seed)].iloc[0]
            for scope,mask,key in [('all',np.ones(2287,bool),'spatial_ARI_all'),('training',train,'spatial_ARI_training'),('heldout',~train,'spatial_ARI_heldout')]:
                assert np.isclose(r[key],adjusted_rand_score(y[mask],p[mask]));t=ct.loc[ct.scheme.eq(w)&ct.seed.eq(seed)&ct.scope.eq(scope)];assert t.n.sum()==mask.sum()
                for _,v in metrics.loc[metrics.scheme.eq(w)&metrics.seed.eq(seed)&metrics.scope.eq(scope)].iterrows():
                    k=int(v.baseline_raw_class);old=(y==k)&mask;new=(mapped==k)&mask;inter=int((old&new).sum());assert v.intersection==inter and v.baseline_n==old.sum() and v.predicted_n==new.sum()
                    assert v.training_supported==bool((y[train]==k).any())
                    if old.sum():assert np.isclose(v.retention,inter/old.sum())
                    if new.sum():assert np.isclose(v.purity,inter/new.sum())

def test_exact_reference34_and_destination_split_counts():
    ids=inputarray()['tract_ids'];target=np.isin(ids,json.loads(source(REVIEW+'D34_REFERENCE_IDENTITY.json').read_text())['tract_ids']);assert target.sum()==34
    q=read('CORE3_34TRACT_AUDIT.csv');assert len(q)==5*20*4
    for w in WEIGHTS:
        a=records(w)
        for seed in SEEDS:
            y=a[f's{seed}_labels'];train=a[f's{seed}_train_mask'];mapped,mp=independent_mapping(y,a[f's{seed}_spatial_prediction'],train);dominant=int(np.bincount(y[target],minlength=4).argmax())
            for scope,labels,mask in [('full_fit',y,np.ones(2287,bool)),('spatial_all',mapped,np.ones(2287,bool)),('spatial_training',mapped,train),('spatial_heldout',mapped,~train)]:
                r=q.loc[q.scheme.eq(w)&q.seed.eq(seed)&q.scope.eq(scope)].iloc[0];counts=np.bincount(labels[target&mask],minlength=4);assert json.loads(r.destination_counts_in_own_full_class_ids)==counts.tolist()
                assert r.reference_group_training_n==int((target&train).sum()) and r.number_of_destination_classes==(counts>0).sum()
                largest=int(counts.argmax());assert r.largest_destination_original_members==counts[largest] and r.largest_destination_total_n==int(((labels==largest)&mask).sum())
                assert r.dominant_intersection==int(((labels==dominant)&target&mask).sum())
    worst=q.loc[q.scheme.eq('W1')&q.seed.eq(54)&q.scope.eq('spatial_all')].iloc[0];assert worst.reference_group_training_n==4 and worst.predicted_dominant_class_n==92 and worst.dominant_intersection==34 and np.isclose(worst.purity,34/92)

def test_profile_original_units_and_population_accounting():
    _,f,_,_,_=inputs();q=read('CORE3_CLASS_PROFILES.csv');sizes=read('CORE3_CLASS_SIZES_AND_POPULATION.csv')
    for w in WEIGHTS:
        a=records(w)
        for seed in SEEDS:
            y=a[f's{seed}_labels'];p=q.loc[q.scheme.eq(w)&q.seed.eq(seed)];s=sizes.loc[sizes.scheme.eq(w)&sizes.seed.eq(seed)];assert s.n.sum()==2287 and np.isclose(s.population.sum(),f.formal_population.sum())
            for k in range(4):
                d=f.loc[y==k];r=p.loc[p.raw_class.eq(k)].set_index('feature')
                for c in COLS+['NRI_BUILDVALUE']:assert np.isclose(r.loc[c,'mean'],d[c].mean(),rtol=1e-12) and np.isclose(r.loc[c,'median'],d[c].median(),rtol=1e-12)
    effects=read('CORE3_STOCK_ALR_WEIGHT_EFFECTS.csv');assert np.allclose(effects.loc[effects.scheme.eq('W1'),'mean_change'],0)

def test_summary_empirical_ranges_and_seed_counts():
    q=read('CORE3_WEIGHT_COMPARISONS.csv');r=read('CORE3_RUN_SUMMARY.csv');seed=read('CORE3_SEED_PAIR_ARI.csv');assert len(seed)==5*190 and len(r)==100
    for _,row in q.iterrows():
        v=r.loc[r.scheme.eq(row.scheme),'spatial_ARI_all'];assert np.isclose(row.spatial_ARI_median,v.median()) and np.isclose(row.spatial_ARI_p05,v.quantile(.05)) and np.isclose(row.spatial_ARI_min,v.min())
    s=json.loads(lp(OUT/'PREREGISTERED_SPECIFICATION.json').read_text());assert len(s['spatial_cases'])==20 and len(set(tuple(sorted(v)) for v in s['spatial_cases'].values()))==17
    p=read('CORE3_PROFILE_REVERSAL_SUMMARY.csv');assert p.cases.eq(20).all()

def test_source_hashes_and_preservation():
    h=json.loads(lp(OUT/'INPUT_HASHES.json').read_text())
    for r in h.values():assert sha(r['path'])==r['sha256'] and lp(r['path']).stat().st_size==r['bytes']
    before=json.loads(lp(OUT/'PRESERVATION_BEFORE.json').read_text());after=json.loads(lp(OUT/'PRESERVATION_AFTER.json').read_text());assert before==after and before['protected_count']==950 and before['staged_count']==862

def test_reference_decision_and_pdf_sizes():
    cfg=json.loads(lp(OUT/'CORE3_REFERENCE_WEIGHT_SPECIFICATION.json').read_text());assert cfg['reference_scheme']=='W1' and not cfg['formal_promotion']
    import fitz
    for p in lp(OUT).glob('FIG_*.pdf'):
        doc=fitz.open(p);assert len(doc)==1 and abs(doc[0].rect.width*25.4/72-185)<.001;spans=[s for b in doc[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()];assert min(s['size'] for s in spans)>=7;doc.close()
    assert len(list(lp(OUT).glob('FIG_*.pdf')))==4
