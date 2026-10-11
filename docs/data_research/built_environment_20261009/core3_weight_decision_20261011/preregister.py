"""Freeze the five author-specified schemes before fitting new models."""
from common import *
import numpy as np,sys,pandas as pd
from sklearn.preprocessing import StandardScaler

def main():
    preservation=snapshot();assert preservation['protected_count']==950 and preservation['staged_count']==862;dump('PRESERVATION_BEFORE.json',preservation)
    master,f,blocks,cases,old=inputs();z=np.load(source(REVIEW+'run_records/CORE3.npz'));meta=json.loads(source(REVIEW+'run_records/CORE3.json').read_text())
    qa=json.loads(source(REVIEW+'INDEPENDENT_REVIEW_QA.json').read_text());assert qa['status']=='PASS'
    for n in ['FINAL_VARIABLE_RECOMMENDATION.md','FINAL_CANDIDATE_CONSTRUCT_DECISION.md','DOMAIN_WEIGHT_REQUIREMENTS.md','BOUNDED_MODEL_COMPARISON.csv','CLUSTER_PROFILE_VALUES.csv','SPATIAL_PROFILE_STABILITY.csv','D34_REFERENCE_IDENTITY.json']:source(REVIEW+n)
    scaler=StandardScaler().fit(f[COLS]);x=scaler.transform(f[COLS])*factors('W1');hashx=hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
    assert hashx==meta['signature']['matrix_sha256'],('Reconstructed matrix is not byte-identical',hashx,meta['signature'])
    assert hashids(f.index)==meta['signature']['sample_sha256'] and np.array_equal(z['tract_ids'],f.index.to_numpy()) and np.array_equal(z['feature_columns'],COLS)
    assert np.array_equal(z['coordinate_factors'],factors('W1')) and np.array_equal(z['scaler_mean'],scaler.mean_) and np.array_equal(z['scaler_scale'],scaler.scale_)
    for seed in SEEDS:
        mask=~blocks.block_id.isin(cases[seed]).to_numpy();assert np.array_equal(mask,z[f's{seed}_train_mask'])
        ssc=StandardScaler().fit(f.loc[mask,COLS]);xx=ssc.transform(f[COLS])*factors('W1')
        assert np.array_equal(ssc.mean_,z[f's{seed}_spatial_mean']) and np.array_equal(ssc.scale_,z[f's{seed}_spatial_scale'])
        assert np.array_equal(np.square(xx[:,None,:]-z[f's{seed}_spatial_centers'][None,:,:]).sum(axis=2).argmin(axis=1),z[f's{seed}_spatial_prediction'])
        assert np.array_equal(np.square(x[:,None,:]-z[f's{seed}_centers'][None,:,:]).sum(axis=2).argmin(axis=1),z[f's{seed}_labels'])
    rows=[]
    for scheme,weights in WEIGHTS.items():
        assert np.isclose(sum(weights),1,rtol=0,atol=1e-15)
        for dom,w in zip(DOMAIN_COLUMNS,weights):
            for c in DOMAIN_COLUMNS[dom]:rows.append(dict(scheme=scheme,domain=dom,feature=c,domain_squared_budget=w,coordinates_in_domain=len(DOMAIN_COLUMNS[dom]),coordinate_squared_weight=w/len(DOMAIN_COLUMNS[dom]),standardized_multiplier=np.sqrt(w/len(DOMAIN_COLUMNS[dom]))))
        assert np.isclose(np.square(factors(scheme)).sum(),1)
    save('CORE3_WEIGHT_VECTORS.csv',rows)
    spec=dict(starting_commit=BASELINE,features=COLS,feature_domains=DOMAIN_COLUMNS,schemes=WEIGHTS,KMeans=PARAMS,seeds=SEEDS,tract_ids=f.index.tolist(),GEOID_order_sha256=hashids(f.index),raw_feature_matrix_sha256=hashlib.sha256(np.ascontiguousarray(f[COLS].to_numpy()).tobytes()).hexdigest(),spatial_cases=cases,unique_deletion_sets=17,W1_verified_matrix_sha256=hashx,W1_reused_full_fits=20,W1_reused_spatial_fits=20,new_fit_ceiling=160,new_k_search=False,new_variable_selection=False,new_weight_schemes_allowed=False,reference_decision_rule='Conceptual representation and evidence-qualified interpretation; never optimize ARI, silhouette, balance or retention of the 34-tract group.',software=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=__import__('scipy').__version__,sklearn=__import__('sklearn').__version__))
    target=lp(OUT/'PREREGISTERED_SPECIFICATION.json')
    if target.exists():assert json.loads(target.read_text())==clean(spec)
    else:dump('PREREGISTERED_SPECIFICATION.json',spec)
    save('CORE3_MASTER_2291.csv',master[COLS+['NRI_BUILDVALUE','formal_population','T80','scag2020_classified_land_coverage']].assign(classification_status=np.where(master.index.isin(f.index),'COMPLETE_CANDIDATE','UNCLASSIFIED_GEOMETRY')),index=True)
    np.savez_compressed(lp(OUT/'CORE3_EXACT_INPUTS.npz'),tract_ids=f.index.to_numpy(dtype='U11'),feature_columns=np.array(COLS),values=f[COLS].to_numpy(),block_ids=blocks.block_id.to_numpy(dtype='U16'))
    dump('INPUT_AND_W1_REUSE_QA.json',dict(all_actual_source_bytes_verified=True,primary_n=2287,master_n=2291,unclassified_GEOIDs=UNRESOLVED,exact_W1_matrix_match=True,exact_W1_scaler_factor_seed_case_prediction_match=True,full_centers='ACTUAL_SAVED_ESTIMATOR_CENTERS',raw_matrix_sha256=spec['raw_feature_matrix_sha256'],W1_matrix_sha256=hashx,settings=PARAMS,version=spec['software']))
    textfile('CORE3_WEIGHT_PREREGISTRATION.md','''# CORE3 domain-weight preregistration

CORE3 measurement choice is closed. Exactly twelve saved coordinates and 2,287 complete residential GEOIDs are retained, with four geometry-unclassified records retained in the 2,291-row master. No imputation, additional variables, k search, PCA or model-physical calculation is allowed.

Five schemes are registered before new fits: W1 [0.20,0.20,0.20,0.20,0.10,0.10]; W2 [1/6]*6; W3 [2/11,4/11,2/11,1/11,1/11,1/11]; W4 [0.20,0.20,0.20,0.20,0.05,0.15]; W5 [0.20,0.20,0.20,0.20,0.15,0.05]. Order: recovery, grid, physical, social, stock, ALR. Each vector sums to one. Coordinates are StandardScaler z values multiplied by sqrt(domain budget / domain coordinate count), not by the squared-distance budget itself. Each domain is internally equally split.

W1 groups asset stock and loss propensity into one economic/exposure-and-loss parent while keeping both measurements visible. W2 makes each a separate parent and increases their combined share to one-third. W3 inherits strong grid emphasis. W4/W5 vary only the stock/ALR split of the economic parent's unchanged 20 percent. This is a comparison of declared scientific representation assumptions, not estimates of uniquely correct weights.

Fixed k=4, n_init=100, max_iter=500, tol=1e-4, Lloyd and seeds42-61. W1's 20 full-cohort plus20 spatial fits will be reused only after exact source-byte, weighted-matrix, scaler, settings, seed and case verification. W2-W5 permit 160 new fits total. The same20 spatial deletion cases represent17 unique geographic sets, not20 independent validation replicates. Spatial scalers and clusters are fitted only on retained training tracts; full-cohort prediction uses those fitted estimators. One-to-one spatial label matching uses training overlap only. Raw contingency tables expose merges/splits; unsupported training classes are flagged.

The five decision questions are separate: measurement validity (already resolved), construct validity (meaning of parents), weight justification (representation assumption), partition stability (seeds, weights, spatial deletion), and interpretability (descriptive, specification-qualified differences). W1 may be recommended as a transparent balanced reference if its conceptual rationale remains defensible; its recommendation cannot be based on an ARI/silhouette/size ranking. No post-result scheme or acceptance threshold will be invented. Materially incompatible taxonomies will be described as specification-conditional rather than repaired by weight tuning.

Diagnostics will report all seed pairs; same-seed W1 contrasts; full raw class transitions; original-unit profiles; full/train/held-out spatial ARI; retention/purity/Jaccard; TSS=BSS+WSS by coordinate/domain; and the exact saved34-tract group's destinations and absorption. Empirical ranges and lower tails are descriptive, not confidence intervals. Profile contrasts use W1 seed42 overlap labels for display but own-seed baselines for stability statistics. The34-tract group is never forced to survive, and cannot justify weight selection. Recovery inputs are not independent causal validation.

Weak grid separation will be assessed through BSS/TSS, within-class spread, original-unit differences, shared linear information with recovery, and the prespecified grid-budget contrast. No weight will be increased to force a domain contribution. Stock is monetary exposure; unadjusted ALR is multi-hazard expected-loss propensity, not pure hazard.
''')
    log('Five schemes preregistered; W1 exact matrix/scalers/factors/predictions verified; 950 protected files and 862 staged items recorded. No new fit yet.')
if __name__=='__main__':main()
