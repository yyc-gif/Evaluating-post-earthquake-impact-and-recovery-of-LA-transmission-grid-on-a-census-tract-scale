"""Fixed-k, fixed-budget comparisons after measurement gate; no formal outputs."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
from common import *
import numpy as np, pandas as pd, ast, time, itertools, sys
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score, pairwise_distances
from scipy.optimize import linear_sum_assignment
from threadpoolctl import threadpool_limits

S='candidate_admission_rebuild_20261010/'
SEEDS=list(range(42,62))
GRID=['Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']
EMC='emc2022_total_built_land_fraction';LAR='building_footprint_coverage';HOU='housing_5plus_share';SC20='scag2020_classified_land_entropy';SC19='land_use_entropy';AGE='assessor2022_actual_pre1970_main_area_share';HISTAGE='all_use2014_pre1970_area_share';ACSAGE='acs_residential_pre1970_share'
CORE3=[EMC,HOU,SC20]
MODELS={'HIST':[SC19,LAR,HISTAGE],'CORE2':[EMC,HOU],'CORE3':CORE3,'CORE4':CORE3+[AGE],'AGE_ACS':CORE3+[ACSAGE],'AGE_HIST':CORE3+[HISTAGE],'COVER_ALT':[LAR,HOU,SC20],'LAND_ALT':[EMC,HOU,SC19],'HOUSING_ALT':[EMC,'housing_detached_share',SC20],'HARDEN_EXT':CORE3+['nlcd_c12_2022_impervious_fraction'],'HEIGHT_HIST_EXT':CORE3+['outline_height_area_weighted_centroid_m'],'CORE3_AGE_COMMON':CORE3}
PARAMS=dict(n_clusters=4,n_init=100,max_iter=500,tol=1e-4,algorithm='lloyd')
BUDGET={k:.2 for k in ['recovery_service','grid','physical','social','loss_exposure']}

def idhash(ids):return hashlib.sha256('\n'.join(ids).encode()).hexdigest()

def domains(phys):return {'recovery_service':['B_480_hr','Init_Supply'],'grid':GRID,'physical':phys,'social':['SOVI_SCORE'],'loss_exposure':['log1p_BUILDVALUE','ALR_NPCTL']}

def design(f,phys,train=None):
    dom=domains(phys);cols=[c for v in dom.values() for c in v];factors=np.array([np.sqrt(.2/len(v)) for v in dom.values() for c in v]);sc=StandardScaler().fit(f[cols] if train is None else f.loc[train,cols]);return sc.transform(f[cols])*factors,cols,factors,sc

def align(base,pred,train):
    tab=np.zeros((4,4),int)
    for a,b in zip(base[train],pred[train]):tab[a,b]+=1
    a,b=linear_sum_assignment(-tab);mapping=dict(zip(b,a));return np.array([mapping[k] for k in pred]),tab,mapping

def prepare():
    gate=json.loads(lp(OUT/'MEASUREMENT_COHORT_QA.json').read_text(encoding='utf-8'));old=frame('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv');ids=old.index[old.primary_complete_case];f=frame(S+'CANDIDATE_VALUES_RESIDENTIAL_2291.csv').reindex(ids)
    # Exact saved numerical values for non-target coordinates, not recalc or update.
    for c in ['B_480_hr','Init_Supply']+GRID+['SOVI_SCORE','ALR_NPCTL']:assert np.allclose(f[c],old.loc[ids,c],atol=1e-11,rtol=1e-12);f[c]=old.loc[ids,c]
    assert np.allclose(f.log1p_BUILDVALUE,old.loc[ids,'log1p_NRI_BUILDVALUE'],atol=1e-12);f['log1p_BUILDVALUE']=old.loc[ids,'log1p_NRI_BUILDVALUE']
    for c in [SC19,LAR,HISTAGE]:assert np.allclose(f[c],old.loc[ids,c],atol=1e-12);f[c]=old.loc[ids,c]
    blocks=frame('final_feature_validation_20261010/TRACT_SPATIAL_BLOCKS.csv').reindex(ids);blocks['block_id']=blocks.block.map(lambda s:':'.join(map(str,ast.literal_eval(s))))
    spatial=pd.read_csv(source('final_feature_validation_20261010/SPATIAL_BLOCK_STABILITY.csv'));cases={int(seed):g.removed_blocks.iloc[0].split(';') for seed,g in spatial.groupby('seed')};assert set(cases)==set(SEEDS)
    spec=dict(baseline=BASELINE,measurement_gate_sha256=sha(OUT/'MEASUREMENT_COHORT_QA.json'),models=MODELS,ineligible_models={'EPA_ACTIVITY_EXT':'Different historical household/job activity construct with unresolved intra-donor allocation; retained as descriptive assumption evidence, not parcel-area substitution.','GROSS_FAR':'No certified measurement exists.'},seeds=SEEDS,KMeans=PARAMS,domain_budget=BUDGET,physical_coordinate_squared_weights={k:{c:.2/len(v) for c in v} for k,v in MODELS.items()},final_domain_weights_selected=False,weight_comparison='One benchmark only: inherited equal-five-domain .2 budgets. No new weights or k searches.',primary_GEOID_order=ids.tolist(),primary_n=len(f),conditional_age_pair_sample='CORE4 and CORE3_AGE_COMMON exclude the same one missing assessor-age tract; other models use primary2287',spatial_cases=cases,spatial_unique_deletion_sets=len(set(tuple(sorted(v)) for v in cases.values())),coverage_check='CORE3 refit on upper three quartiles of SCAG2020 classified-land coverage, seeds42-61, predict all2287; diagnostic sample deletion, not a coverage admission threshold',measurement_error_check='80 paired ACS VRE inputs predicted through fixed CORE3 seed42 scaler/centers; no reclustering, not 80 independent realizations',new_fit_ceiling=460,reused_HIST_fits=40,additional_k_search=False,no_model_selected_using_silhouette_or_ARI=True)
    p=lp(OUT/'CONTROLLED_SHORTLIST_SPECIFICATION.json')
    if p.exists():assert json.loads(p.read_text(encoding='utf-8'))==clean(spec)
    else:dump('CONTROLLED_SHORTLIST_SPECIFICATION.json',spec)
    return f,blocks,cases,spec

def fit_model(name,phys,f,blocks,cases,spec):
    if name in ['CORE4','CORE3_AGE_COMMON']:f=f.loc[f[AGE].notna()].copy()
    assert len(f)==(2286 if name in ['CORE4','CORE3_AGE_COMMON'] else 2287) and f[[c for v in domains(phys).values() for c in v]].notna().all().all()
    x,cols,factors,sc=design(f,phys);matrixhash=hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest();samplehash=idhash(f.index)
    folder=lp(OUT/'run_records');folder.mkdir(exist_ok=True);cp=folder/(name+'.npz');meta=folder/(name+'.json');signature=dict(model=name,matrix_sha256=matrixhash,sample_sha256=samplehash,specification_sha256=sha(OUT/'CONTROLLED_SHORTLIST_SPECIFICATION.json'),columns=cols)
    data={'tract_ids':f.index.to_numpy(dtype='U11'),'feature_columns':np.array(cols,dtype='U64'),'coordinate_factors':factors,'scaler_mean':sc.mean_,'scaler_scale':sc.scale_}
    rows=[];done=[]
    if cp.exists() and meta.exists():
        m=json.loads(meta.read_text(encoding='utf-8'));assert m['signature']==signature;z=np.load(cp);data={k:z[k] for k in z.files};rows=m['rows'];done=m['completed_seeds']
    hist=None;historic_rows=None
    if name=='HIST':
        hist=np.load(source('final_feature_validation_20261010/run_records/D__equal_five_domains.npz'))
        histmeta=json.loads(source('final_feature_validation_20261010/run_records/D__equal_five_domains.json').read_text(encoding='utf-8'))
        assert matrixhash==histmeta['matrix_sha256'] and samplehash==histmeta['rows'][0]['sample_sha256']
        historic_rows=histmeta['rows']
    with threadpool_limits(limits=1):
        dist=pairwise_distances(x)
        for seed in SEEDS:
            if seed in done:continue
            start=time.perf_counter();train=~blocks.loc[f.index].block_id.isin(cases[seed]).to_numpy()
            if name=='HIST':
                labels=hist[f's{seed}_k4'];metrics=next(v for v in historic_rows if v['seed']==seed and v['k']==4)
                centers=np.array([x[labels==k].mean(axis=0) for k in range(4)]);inertia=metrics['inertia'];iterations=metrics['iterations'];fullsource='REUSED_EXACT_HISTORICAL_FIT'
                z=np.load(source(f'spatial_k4_validation_20261010/run_records/D_s{seed}.npz'));mm=json.loads(source(f'spatial_k4_validation_20261010/run_records/D_s{seed}.json').read_text(encoding='utf-8'))
                assert np.array_equal(z['tract_ids'],f.index.to_numpy()) and np.array_equal(z['train_mask'],train) and np.array_equal(z['baseline_labels'],labels)
                assert np.array_equal(z['coordinate_factors'],factors)
                pred=z['raw_prediction'];ssmean=z['scaler_mean'];ssscale=z['scaler_scale'];sscent=z['cluster_centers'];spinertia=mm['inertia'];spiter=mm['iterations'];spsource='REUSED_EXACT_HISTORICAL_FIT'
            else:
                km=KMeans(**PARAMS,random_state=seed).fit(x);labels=km.labels_;centers=km.cluster_centers_;inertia=km.inertia_;iterations=km.n_iter_;fullsource='NEW_PREDECLARED_FIT'
                xx,_,_,ssc=design(f,phys,train);skm=KMeans(**PARAMS,random_state=seed).fit(xx[train]);pred=skm.predict(xx);ssmean=ssc.mean_;ssscale=ssc.scale_;sscent=skm.cluster_centers_;spinertia=skm.inertia_;spiter=skm.n_iter_;spsource='NEW_PREDECLARED_FIT'
            mapped,tab,mp=align(labels,pred,train)
            for k,v in {f's{seed}_labels':labels,f's{seed}_centers':centers,f's{seed}_train_mask':train,f's{seed}_spatial_prediction':pred,f's{seed}_spatial_mean':ssmean,f's{seed}_spatial_scale':ssscale,f's{seed}_spatial_centers':sscent}.items():data[k]=v
            rows.append(dict(model=name,seed=seed,cohort_n=len(f),full_inertia=inertia,full_iterations=iterations,silhouette=silhouette_score(dist,labels,metric='precomputed'),full_class_sizes=np.bincount(labels,minlength=4).tolist(),minimum_class_n=int(np.bincount(labels,minlength=4).min()),full_fit_source=fullsource,spatial_fit_source=spsource,spatial_inertia=spinertia,spatial_iterations=spiter,training_n=int(train.sum()),heldout_n=int((~train).sum()),removed_blocks=cases[seed],full_ARI=adjusted_rand_score(labels,pred),training_ARI=adjusted_rand_score(labels[train],pred[train]),heldout_ARI=adjusted_rand_score(labels[~train],pred[~train]) if (~train).sum()>1 else None,aligned_reassigned_n=int((labels!=mapped).sum()),no_training_support_classes=[k for k in range(4) if not (labels[train]==k).any()],elapsed_this_run_s=time.perf_counter()-start))
            done.append(seed);np.savez_compressed(cp,**data);meta.write_text(json.dumps(clean(dict(signature=signature,completed_seeds=done,rows=rows,full_center_provenance='DESCRIPTIVE_PARTITION_MEANS_ORIGINAL_FULL_ESTIMATOR_CENTERS_UNAVAILABLE' if name=='HIST' else 'SAVED_NEW_KMEANS_ESTIMATOR_CENTERS')),indent=2)+'\n',encoding='utf-8')
            if seed in [42,51,61]:log(f'{name} seed{seed}: full/spatial complete, N={len(f)}, ARI={rows[-1]["full_ARI"]:.4f}, minclass={rows[-1]["minimum_class_n"]}')
    return rows

def main():
    f,blocks,cases,spec=prepare();start=time.time();allrows=[]
    for name,phys in MODELS.items():allrows+=fit_model(name,phys,f,blocks,cases,spec)
    save('BOUNDED_RUN_RECORDS.csv',allrows)
    dump('FIT_EXECUTION_QA.json',dict(unique_specifications=len(MODELS),full_records=len(allrows),spatial_records=len(allrows),reused_full=20,reused_spatial=20,new_primary_and_spatial_fits=(len(MODELS)-1)*40,coverage_fits_planned=20,k=4,k_searches=0,n_init=100,seconds=time.time()-start,versions=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,scipy=__import__('scipy').__version__,sklearn=__import__('sklearn').__version__),formal_files_written=0))
    log('Bounded specification comparison completed.')

if __name__=='__main__':main()
