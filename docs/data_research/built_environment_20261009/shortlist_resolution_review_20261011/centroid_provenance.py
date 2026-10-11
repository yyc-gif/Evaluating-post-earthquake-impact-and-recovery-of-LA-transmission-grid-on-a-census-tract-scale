"""Audit recovered partition means separately from saved estimator centers."""
from common import *
from controlled_shortlist import MODELS,SEEDS,prepare
import numpy as np

if __name__=='__main__':
    f,_,_,_=prepare();rows=[]
    for name in MODELS:
        p=lp(OUT/'run_records'/(name+'.npz'));z=np.load(p);d=f.loc[z['tract_ids']];cols=z['feature_columns'].tolist();x=(d[cols].to_numpy()-z['scaler_mean'])/z['scaler_scale']*z['coordinate_factors']
        meta=p.with_suffix('.json');j=json.loads(meta.read_text(encoding='utf-8'));j['full_center_provenance']='DESCRIPTIVE_PARTITION_MEANS_ORIGINAL_FULL_ESTIMATOR_CENTERS_UNAVAILABLE' if name=='HIST' else 'SAVED_NEW_KMEANS_ESTIMATOR_CENTERS';meta.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
        for seed in SEEDS:
            centers=z[f's{seed}_centers'];lab=z[f's{seed}_labels'];dist=np.square(x[:,None,:]-centers[None,:,:]).sum(axis=2);nearest=dist.argmin(axis=1);changed=nearest!=lab
            rows.append(dict(model=name,seed=seed,center_provenance=j['full_center_provenance'],partition_labels_exactly_preserved=True,nearest_center_disagreement_n=int(changed.sum()),maximum_distance_excess_if_disagreement=float(np.max(dist[np.arange(len(lab)),lab]-dist.min(axis=1))),centers_are_available_for_new_model_prediction=name!='HIST'))
            if name!='HIST':assert not changed.any(),(name,seed)
    save('CENTROID_PROVENANCE_QA.csv',rows)
    log('Historical full-fit labels retained exactly. HIST centers are descriptive partition means, not recovered estimator centers; all new-model centers reproduce saved predictions.')
