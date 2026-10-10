"""Stage 7 controlled KMeans initialization study: B vs D. Never changes scientific data."""
from pathlib import Path
import hashlib,json,itertools,os
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("OMP_NUM_THREADS","1")
os.environ.setdefault("MKL_NUM_THREADS","1")
import numpy as np,pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits

ROOT=Path(__file__).resolve().parents[5]
DIR=Path(__file__).resolve().parent
OUT=DIR/"results"
MATCHED=ROOT/"docs/data_research/built_environment_20261009/nri_eal_redundancy_audit_20261009/MATCHED_FEMA_STAGE7_FEATURES.csv"
STAGE=ROOT/"Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv"
ORIGINAL=["T80","Init_Supply","Grid_Degree","Grid_Impact","Grid_Betweenness","Redundancy_HHI","Pre_1970_Ratio","Pop_Density","SOVI_SCORE"]
DOMAIN={"recovery":["T80","Init_Supply"],"grid":["Grid_Degree","Grid_Impact","Grid_Betweenness","Redundancy_HHI"],
    "built":["Pre_1970_Ratio","Pop_Density"],"social":["SOVI_SCORE"]}
SETS={"B":["EAL_SCORE"],"D":["NRI_BUILDVALUE","ALR_NPCTL"]}
WEIGHTS={"recovery":2/11,"grid":4/11,"built":2/11,"social":1/11,"loss_exposure":2/11}
N_INIT=[10,50,150]
SEEDS=list(range(42,62))
K=5

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for chunk in iter(lambda:f.read(2**20),b""):h.update(chunk)
 return h.hexdigest()
def load():
 for p in [MATCHED,STAGE]:
  if not p.exists() or p.stat().st_size<200:
   raise ValueError("Unhydrated Git LFS input: "+str(p))
 df=pd.read_csv(MATCHED,dtype={"tract_id":str},low_memory=False)
 old=pd.read_csv(STAGE,dtype={"tract_id":str})
 assert len(df)==len(old)==2291 and df.tract_id.equals(old.tract_id)
 assert df.tract_id.is_unique
 assert "cluster" in df and np.isfinite(df[ORIGINAL].to_numpy(dtype=float)).all()
 for c in ORIGINAL:
  assert np.allclose(df[c],old[c],atol=1e-11,rtol=1e-12)
 return df

def model_input(df,model):
 blocks={**DOMAIN,"loss_exposure":SETS[model]}
 columns=ORIGINAL+SETS[model]
 x=df[columns].copy()
 x["Pop_Density"]=np.log1p(x.Pop_Density)
 if "NRI_BUILDVALUE" in x:x["NRI_BUILDVALUE"]=np.log1p(x.NRI_BUILDVALUE)
 assert np.isfinite(x.to_numpy(float)).all()
 z=StandardScaler().fit_transform(x)
 for name,cols in blocks.items():
  factor=np.sqrt(WEIGHTS[name]/len(cols))
  for col in cols:z[:,columns.index(col)]*=factor
 assert np.allclose(np.var(z,axis=0).sum(),1.,atol=1e-12)
 return z

def run():
 OUT.mkdir(exist_ok=True,parents=True)
 frame=load()
 records=[];stored={}
 with threadpool_limits(limits=1):
  for model in SETS:
   z=model_input(frame,model)
   for restarts in N_INIT:
    for seed in SEEDS:
     fit=KMeans(n_clusters=K,random_state=seed,n_init=restarts,max_iter=300,tol=1e-4,algorithm="lloyd").fit(z)
     key=(model,restarts,seed)
     labels=fit.labels_.copy()
     stored[key]=labels
     records.append({"model":model,"n_init":restarts,"seed":seed,"k":K,
        "inertia":float(fit.inertia_),"iterations":int(fit.n_iter_),
        "min_size":int(np.bincount(labels).min()),
        "ari_to_old":float(adjusted_rand_score(frame.cluster,labels))})
     print("FIT",model,restarts,seed,round(fit.inertia_,10),flush=True)
 per=pd.DataFrame(records)
 per.to_csv(OUT/"RUNS.csv",index=False)
 summaries=[];clusters=[];cross=[]
 for model in SETS:
  select=per[per.model.eq(model)]
  best=select.loc[select.inertia.idxmin()]
  reference=stored[(model,int(best.n_init),int(best.seed))]
  best_inertia=best.inertia
  for restarts in N_INIT:
   sub=select[select.n_init.eq(restarts)]
   arr=[stored[(model,restarts,seed)] for seed in SEEDS]
   pair=[adjusted_rand_score(a,b) for a,b in itertools.combinations(arr,2)]
   baselines=[adjusted_rand_score(a,reference) for a in arr]
   gaps=(sub.inertia.to_numpy()-best_inertia)/best_inertia
   summaries.append({"model":model,"n_init":restarts,"n_seeds":len(SEEDS),
     "best_global_inertia":float(best_inertia),
     "mean_inertia":float(sub.inertia.mean()),
     "min_inertia":float(sub.inertia.min()),"max_inertia":float(sub.inertia.max()),
     "median_inertia_gap_pct":float(np.median(gaps)*100),
     "max_inertia_gap_pct":float(np.max(gaps)*100),
     "pairwise_min_ari":float(np.min(pair)),"pairwise_median_ari":float(np.median(pair)),
     "pairwise_max_ari":float(np.max(pair)),
     "median_ari_to_best":float(np.median(baselines)),
     "min_ari_to_best":float(np.min(baselines)),
     "n_ari_to_best_above_0_95":int(np.sum(np.array(baselines)>.95)),
     "n_ari_to_best_above_0_99":int(np.sum(np.array(baselines)>.99)),
     "best_selected_n_init":int(best.n_init),"best_selected_seed":int(best.seed)})
  clusters.append(pd.DataFrame({"tract_id":frame.tract_id,"model":model,
      "best_cluster":reference+1,"best_from_seed":int(best.seed),
      "best_n_init":int(best.n_init)}))
 a,b=SETS.keys()
 for n in N_INIT:
  vals=[adjusted_rand_score(stored[(a,n,seed)],stored[(b,n,seed)]) for seed in SEEDS]
  cross.append({"n_init":n,"n_seeds":len(SEEDS),"B_vs_D_mean_ARI":float(np.mean(vals)),
    "B_vs_D_median_ARI":float(np.median(vals)),"B_vs_D_min_ARI":float(min(vals)),
    "B_vs_D_max_ARI":float(max(vals))})
 pd.DataFrame(summaries).to_csv(OUT/"INITIALIZATION_SUMMARY.csv",index=False)
 pd.concat(clusters,ignore_index=True).to_csv(OUT/"BEST_LABELS.csv",index=False)
 pd.DataFrame(cross).to_csv(OUT/"B_VS_D_ARI.csv",index=False)
 output={"repository_snapshot":"65f388f9710566ffa845808bd7b10503de4da608",
  "k":K,"sample_count":len(frame),"source_sha256":{str(p.relative_to(ROOT)):sha(p) for p in [MATCHED,STAGE]},
  "convention":"Original domain budgets, log Pop_Density and log NRI_BUILDVALUE, fixed k5. Compare 10/50/150 restarts, 20 seeds. No outcomes, geography or features adjusted post hoc.",
  "summary":summaries,"B_D_ARI":cross}
 (OUT/"SUMMARY.json").write_text(json.dumps(output,indent=2,allow_nan=False)+"\n")
 print("STABILITY_SUMMARY_BEGIN",json.dumps(output,indent=2),"STABILITY_SUMMARY_END",flush=True)

if __name__=="__main__":run()
