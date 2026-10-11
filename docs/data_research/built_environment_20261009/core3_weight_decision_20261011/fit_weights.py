"""Only the four new prespecified weight schemes; immutable checkpoints."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
from common import *
import numpy as np,time,shutil
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score
from scipy.optimize import linear_sum_assignment
from threadpoolctl import threadpool_limits

def align(a,b,mask):
    table=np.zeros((4,4),int);np.add.at(table,(a[mask],b[mask]),1)
    i,j=linear_sum_assignment(-table);mapping=dict(zip(j,i));return np.array([mapping[k] for k in b]),mapping,table

def main():
    spec=json.loads(lp(OUT/'PREREGISTERED_SPECIFICATION.json').read_text());master,f,blocks,cases,_=inputs()
    assert spec['schemes']==WEIGHTS and spec['KMeans']==PARAMS and spec['tract_ids']==f.index.tolist()
    oldmeta=json.loads(source(REVIEW+'run_records/CORE3.json').read_text());source_npz=source(REVIEW+'run_records/CORE3.npz');zold=np.load(source_npz)
    folder=lp(OUT/'run_records');folder.mkdir(exist_ok=True);allrows=[];start=time.perf_counter();new_count=0;reused=0
    with threadpool_limits(limits=1):
        for scheme in WEIGHTS:
            sc=StandardScaler().fit(f[COLS]);fac=factors(scheme);x=sc.transform(f[COLS])*fac
            signature=dict(scheme=scheme,weighted_matrix_sha256=hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest(),GEOID_order_sha256=hashids(f.index),preregistration_sha256=sha(OUT/'PREREGISTERED_SPECIFICATION.json'),features=COLS,settings=PARAMS)
            cp=folder/(scheme+'.npz');meta=folder/(scheme+'.json');data=dict(tract_ids=f.index.to_numpy(dtype='U11'),feature_columns=np.array(COLS,dtype='U64'),coordinate_factors=fac,scaler_mean=sc.mean_,scaler_scale=sc.scale_);rows=[];done=[]
            if cp.exists() and meta.exists():
                m=json.loads(meta.read_text());assert m['signature']==signature;zz=np.load(cp);data={k:zz[k] for k in zz.files};rows=m['rows'];done=m['completed_seeds']
            if scheme=='W1':
                assert signature['weighted_matrix_sha256']==oldmeta['signature']['matrix_sha256']
                shutil.copyfile(source_npz,cp);data={k:zold[k] for k in zold.files}
            for seed in SEEDS:
                if seed in done:continue
                t=time.perf_counter();train=~blocks.block_id.isin(cases[seed]).to_numpy();ssc=StandardScaler().fit(f.loc[train,COLS]);xx=ssc.transform(f[COLS])*fac
                if scheme=='W1':
                    old=next(r for r in oldmeta['rows'] if r['seed']==seed);labels=zold[f's{seed}_labels'];cent=zold[f's{seed}_centers'];pred=zold[f's{seed}_spatial_prediction'];spcent=zold[f's{seed}_spatial_centers'];inertia=old['full_inertia'];iterations=old['full_iterations'];spinertia=old['spatial_inertia'];spiterations=old['spatial_iterations'];origin='REUSED_ACTUAL_CORE3_ESTIMATOR';reused+=2
                    assert np.array_equal(train,zold[f's{seed}_train_mask']) and np.array_equal(ssc.mean_,zold[f's{seed}_spatial_mean'])
                else:
                    km=KMeans(**PARAMS,random_state=seed).fit(x);labels=km.labels_;cent=km.cluster_centers_;inertia=km.inertia_;iterations=km.n_iter_
                    sp=KMeans(**PARAMS,random_state=seed).fit(xx[train]);pred=sp.predict(xx);spcent=sp.cluster_centers_;spinertia=sp.inertia_;spiterations=sp.n_iter_;origin='NEW_PREREGISTERED_WEIGHT_FIT';new_count+=2
                aligned,mp,tab=align(labels,pred,train)
                for k,v in {f's{seed}_labels':labels,f's{seed}_centers':cent,f's{seed}_train_mask':train,f's{seed}_spatial_prediction':pred,f's{seed}_spatial_mean':ssc.mean_,f's{seed}_spatial_scale':ssc.scale_,f's{seed}_spatial_centers':spcent}.items():data[k]=v
                rows.append(dict(scheme=scheme,seed=seed,cohort_n=len(f),full_inertia=inertia,full_iterations=iterations,full_class_sizes=np.bincount(labels,minlength=4).tolist(),spatial_inertia=spinertia,spatial_iterations=spiterations,training_n=int(train.sum()),heldout_n=int((~train).sum()),removed_blocks=cases[seed],spatial_ARI_all=adjusted_rand_score(labels,pred),spatial_ARI_training=adjusted_rand_score(labels[train],pred[train]),spatial_ARI_heldout=adjusted_rand_score(labels[~train],pred[~train]),aligned_reassigned_n=int((labels!=aligned).sum()),unsupported_training_classes=[k for k in range(4) if not (labels[train]==k).any()],training_label_mapping=mp,fit_origin=origin,elapsed_this_execution_s=time.perf_counter()-t))
                done.append(seed)
                if scheme!='W1':np.savez_compressed(cp,**data)
                dump('run_records/'+scheme+'.json',dict(signature=signature,completed_seeds=done,rows=rows,center_provenance='ACTUAL_SAVED_ESTIMATOR_CENTERS',W1_source_file=str(source_npz) if scheme=='W1' else None,W1_source_sha256=sha(source_npz) if scheme=='W1' else None))
                if seed in [42,51,61]:log(f'{scheme} seed {seed}: full/spatial complete; ARI={rows[-1]["spatial_ARI_all"]:.4f}, sizes={rows[-1]["full_class_sizes"]}')
            assert len(done)==20;allrows+=rows
    assert new_count<=160
    save('CORE3_RUN_SUMMARY.csv',allrows)
    dump('FIT_COMPLETION_QA.json',dict(schemes=5,full_records=100,spatial_records=100,new_fits_this_execution=new_count,reused_fits_this_execution=reused,total_new_fits=160,existing_W1_fits_reused=40,elapsed_s=time.perf_counter()-start,preregistration_sha256=sha(OUT/'PREREGISTERED_SPECIFICATION.json'),no_extra_schemes=True,no_k_search=True,all_complete=True))
    log('Five schemes complete. 40 W1 fits reused; 160 new fits total. No further fits authorized.')
if __name__=='__main__':main()
