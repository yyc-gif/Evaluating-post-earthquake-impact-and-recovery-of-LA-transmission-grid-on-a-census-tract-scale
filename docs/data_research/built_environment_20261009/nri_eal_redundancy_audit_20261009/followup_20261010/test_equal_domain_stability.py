"""Independent higher-restart B/D stability in equal-domain budgets at k=4/5."""
import os
os.environ.setdefault("OPENBLAS_NUM_THREADS","1");os.environ.setdefault("MKL_NUM_THREADS","1")
from pathlib import Path
import itertools,json
import numpy as np,pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
from test_initialization_stability import load,model_input,SETS,DOMAIN,ORIGINAL,WEIGHTS,OUT

SEEDS=list(range(42,62))
N_INIT=[10,100]
K_VALUES=[4,5]
def equal_matrix(frame,model):
 z=model_input(frame,model)
 cols=ORIGINAL+SETS[model]
 for domain,features in {**DOMAIN,"loss_exposure":SETS[model]}.items():
  multiplier=np.sqrt(.2/WEIGHTS[domain])
  for name in features:
   z[:,cols.index(name)]*=multiplier
 assert np.allclose(np.var(z,axis=0).sum(),1,atol=1e-12)
 return z

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 frame=load();raw=[];summary=[];results={}
 with threadpool_limits(limits=1):
  for model in SETS:
   z=equal_matrix(frame,model)
   for k in K_VALUES:
    per={};trials=[]
    for n_init in N_INIT:
     for seed in SEEDS:
      fitted=KMeans(n_clusters=k,random_state=seed,n_init=n_init,max_iter=300,tol=1e-4,algorithm="lloyd").fit(z)
      labels=fitted.labels_
      per[(n_init,seed)]=labels
      trials.append({"model":model,"k":k,"n_init":n_init,"seed":seed,"inertia":float(fitted.inertia_),
        "min_size":int(np.bincount(labels).min())})
      print("EQUAL",model,k,n_init,seed,round(fitted.inertia_,7),flush=True)
    best=min(trials,key=lambda x:x["inertia"]);reference=per[(best["n_init"],best["seed"])]
    results[(model,k)]={n:[per[(n,s)] for s in SEEDS] for n in N_INIT}
    for n_init in N_INIT:
     sub=[t for t in trials if t["n_init"]==n_init]
     labels=[per[(n_init,s)] for s in SEEDS]
     pair=np.array([adjusted_rand_score(a,b) for a,b in itertools.combinations(labels,2)])
     vals=np.array([adjusted_rand_score(a,reference) for a in labels])
     gaps=np.array([(t["inertia"]-best["inertia"])/best["inertia"] for t in sub])
     summary.append({"model":model,"k":k,"n_init":n_init,"n_seeds":len(SEEDS),
       "best_inertia":best["inertia"],"median_inertia_gap_percent":float(np.median(gaps)*100),
       "worst_inertia_gap_percent":float(gaps.max()*100),
       "min_pairwise_ari":float(pair.min()),"median_pairwise_ari":float(np.median(pair)),
       "max_pairwise_ari":float(pair.max()),"min_ari_to_best":float(vals.min()),
       "median_ari_to_best":float(np.median(vals))})
    raw.extend(trials)
 cross=[]
 for k in K_VALUES:
  for n in N_INIT:
   pair=[adjusted_rand_score(a,b) for a,b in zip(results[("B",k)][n],results[("D",k)][n])]
   cross.append({"k":k,"n_init":n,"median_B_D_ARI":float(np.median(pair)),
     "min_B_D_ARI":float(min(pair)),"max_B_D_ARI":float(max(pair))})
 pd.DataFrame(raw).to_csv(OUT/"EQUAL_DOMAINS_RUNS.csv",index=False)
 pd.DataFrame(summary).to_csv(OUT/"EQUAL_DOMAINS_SUMMARY.csv",index=False)
 pd.DataFrame(cross).to_csv(OUT/"EQUAL_DOMAINS_B_D_ARI.csv",index=False)
 out={"scope":"20 seeds, equal five-domain budgets, k=4 and fixed k=5, original Stage7 features, n_init 10/100",
   "summary":summary,"B_D_ARI":cross}
 (OUT/"EQUAL_DOMAINS_SUMMARY.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
 print("EQUAL_RESULTS_BEGIN",json.dumps(out,indent=2),"EQUAL_RESULTS_END",flush=True)
if __name__=="__main__":main()
