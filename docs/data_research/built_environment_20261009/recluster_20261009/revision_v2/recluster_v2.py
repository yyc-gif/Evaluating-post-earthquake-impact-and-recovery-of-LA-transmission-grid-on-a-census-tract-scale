"""Stage 7 v2 exploratory JOINT restoration-community typology.

All variant configurations contain T80 (recovery) AND Init_Supply (immediate service).
Built environment measures are chosen conceptually, not by historic cluster separation.
Land-use geometry not yet independently verified: NO model here is final for the paper.
"""
from pathlib import Path
import itertools,json
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score,adjusted_rand_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from feature_audit import build,transformed,ROOT,OUT
SEED=42
KVALUES=list(range(2,9))
ORIGINAL=["T80","Init_Supply","Grid_Degree","Grid_Impact","Grid_Betweenness",
          "Redundancy_HHI","Pre_1970_Ratio","Pop_Density","NRI_RISK_SCORE",
          "NRI_BUILDVALUE","SOVI_SCORE"]
RECOVERY=["T80","Init_Supply"]
GRID=["Grid_Degree","Grid_Impact","Grid_Betweenness","Redundancy_HHI"]
BUILDING=["Pre_1970_Ratio","housing_5plus_share","housing_units_per_km2"]
CONTEXT=["SOVI_SCORE","NRI_BUILDVALUE"]
PILOT="impervious_land_fraction"

def cfg(building=BUILDING,include_risk=True,impervious=False,equal_columns=False):
    b=list(building)+([PILOT] if impervious else [])
    social=list(CONTEXT)+(["NRI_RISK_SCORE"] if include_risk else [])
    domains={"recovery":RECOVERY,"electric_grid":GRID,
             "built_environment_proxy":b,"social_economic_hazard":social}
    return {"cols":sum(domains.values(),[]),"domains":domains if not equal_columns else None,
            "uses_pilot_nlcd":impervious}

MODELS={
 "archived_11_feature_exact_scaling":{"cols":ORIGINAL,"domains":None,"uses_pilot_nlcd":False},
 "joint_v2_with_nri":cfg(),
 "joint_v2_without_nri":cfg(include_risk=False),
 "joint_v2_population_density_with_nri":cfg(building=["Pre_1970_Ratio","housing_5plus_share","Pop_Density"]),
 "joint_v2_without_fiveplus_with_nri":cfg(building=["Pre_1970_Ratio","housing_units_per_km2"]),
 "joint_v2_without_residential_age_with_nri":cfg(building=["housing_5plus_share","housing_units_per_km2"]),
 "joint_v2_pilot_impervious_with_nri":cfg(impervious=True),
 "joint_v2_equal_coordinate_with_nri":cfg(equal_columns=True),
}
def matrix(x,c):
    cols=c["cols"];blocks=c["domains"]
    if len(cols)!=len(set(cols)):raise ValueError(f"Duplicate model features: {cols}")
    if ("T80" not in cols or "Init_Supply" not in cols):raise ValueError("Recovery and initial supply required")
    d=transformed(x)
    v=StandardScaler().fit_transform(d[cols].to_numpy(float))
    if not np.isfinite(v).all():raise ValueError("nonfinite standardized data")
    if blocks:
        if len(set(sum(blocks.values(),[])))!=len(cols) or set(sum(blocks.values(),[]))!=set(cols):
            raise ValueError("Domain weights do not partition feature columns")
        for members in blocks.values():
            for name in members:
                v[:,cols.index(name)]/=np.sqrt(len(blocks)*len(members))
    return v
def fitted(z,k,seed=SEED,n_init=40):
    return KMeans(n_clusters=k,random_state=seed,n_init=n_init,max_iter=500).fit(z)
def diagnostics(z,name):
    rows=[];labels={}
    for k in KVALUES:
        km=fitted(z,k)
        q=km.labels_
        sizes=np.bincount(q,minlength=k)
        score=float(silhouette_score(z,q))
        rows.append(dict(model=name,k=k,silhouette=score,
                         min_cluster=int(sizes.min()),max_cluster=int(sizes.max()),
                         small_fraction=float(sizes.min()/len(q)),inertia=float(km.inertia_)))
        labels[k]=q
    d=pd.DataFrame(rows)
    pool=d.loc[d.small_fraction>=0.02]
    if not len(pool):pool=d
    selected=pool.sort_values(["silhouette","k"],ascending=[False,True]).iloc[0]
    return d,int(selected.k),labels[int(selected.k)]
def resample(z,y,k):
    rng=np.random.default_rng(9102026)
    tests=[]
    for i in range(12):
        idx=rng.choice(len(z),int(.8*len(z)),replace=False)
        q=fitted(z[idx],k,seed=2000+i,n_init=15).predict(z)
        tests.append(dict(seed=2000+i,n_train=len(idx),
             ari_full=adjusted_rand_score(y,q),ari_train=adjusted_rand_score(y[idx],q[idx])))
    return pd.DataFrame(tests)
def describe(x,name,y,c):
    cols=list(dict.fromkeys([*c["cols"],"Pop_Density","housing_units_per_km2",PILOT]))
    data=x.copy();data["new_label"]=y
    out=[]
    for label,t in data.groupby("new_label"):
        row=dict(model=name,cluster=int(label),n=len(t))
        for feature in cols:
            p=t[feature].astype(float)
            row[feature+"_mean"]=float(p.mean())
            row[feature+"_median"]=float(p.median())
            row[feature+"_p10"]=float(p.quantile(.1))
            row[feature+"_p90"]=float(p.quantile(.9))
        out.append(row)
    return pd.DataFrame(out)
def main():
    x=build()
    raw=transformed(x)
    OUT.mkdir(exist_ok=True,parents=True)
    diag=[];summary=[];assignments=[];profiles=[];prepped={}
    for name,spec in MODELS.items():
        z=matrix(x,spec)
        d,k,labels=diagnostics(z,name)
        d["selected_k"]=k
        diag.append(d)
        y=labels+1
        baseline=x.cluster.to_numpy()
        ari=float(adjusted_rand_score(baseline,y))
        stab=resample(z,labels,k)
        stab.to_csv(OUT/(name+"_resampling.csv"),index=False)
        prof=describe(x,name,y,spec)
        profiles.append(prof)
        assignments.extend(dict(model=name,tract_id=str(t),new_cluster=int(q)) for t,q in zip(x.tract_id,y))
        counts=np.bincount(labels)
        summary.append(dict(model=name,features=spec["cols"],blocks=spec["domains"],
            num_domains=len(spec["domains"]) if spec["domains"] else None,
            included_recovery="T80" in spec["cols"],included_initial="Init_Supply" in spec["cols"],
            uses_unverified_nlcd=spec["uses_pilot_nlcd"],n=len(x),k=k,p=z.shape[1],
            silhouette=float(d.loc[d.k.eq(k),"silhouette"].iloc[0]),
            sizes=list(map(int,counts)),resample_median_ari=float(stab.ari_full.median()),
            resample_min_ari=float(stab.ari_full.min()),
            ari_to_archived_historical_clusters=ari))
        prepped[name]=y
    if not all(o["included_recovery"] and o["included_initial"] for o in summary):
        raise RuntimeError("Incorrectly excluded obligatory outcome coordinate")
    pd.concat(diag,ignore_index=True).to_csv(OUT/"K_DIAGNOSTICS.csv",index=False)
    pd.concat(profiles,ignore_index=True).to_csv(OUT/"CLUSTER_PROFILES.csv",index=False)
    pd.DataFrame(assignments).to_csv(OUT/"NEW_LABELS.csv",index=False)
    comparisons=[]
    for a,b in itertools.combinations(MODELS,2):
        comparisons.append(dict(model_a=a,model_b=b,ARI=float(adjusted_rand_score(prepped[a],prepped[b]))))
    pd.DataFrame(comparisons).to_csv(OUT/"CROSS_MODEL_ARI.csv",index=False)
    initial=x.Init_Supply.to_numpy(float)
    initial_summary={"zero_n":int(np.count_nonzero(initial==0)),
                     "nonzero_n":int(np.count_nonzero(initial!=0)),
                     "min":float(initial.min()),"median":float(np.median(initial)),
                     "p95":float(np.percentile(initial,95)),"p99":float(np.percentile(initial,99)),
                     "max":float(initial.max()),"std":float(initial.std()),
                     "n_distinct":int(np.unique(initial).size)}
    t80=x.T80.to_numpy(float)
    output={"n":len(x),"baseline":"031d2c675f8e7d58035d27448be040b809ced086",
            "k_range":KVALUES,"k_admission":"max silhouette with min cluster >=2 percent",
            "none_are_paper_ready_without_land_use_geometry":True,
            "initial_supply_distribution":initial_summary,
            "t80_distribution":{"min":float(t80.min()),"p50":float(np.median(t80)),
                                "p95":float(np.percentile(t80,95)),"max":float(t80.max())},
            "models":summary,"comparisons":comparisons,
            "old_labels_reproduction_k5_ARI":float(adjusted_rand_score(x.cluster,
                                        fitted(matrix(x,MODELS["archived_11_feature_exact_scaling"]),5).labels_))}
    (OUT/"JOINT_SUMMARY.json").write_text(json.dumps(output,indent=2,allow_nan=False)+"\n")
    print("JOINT_RECLUSTER_BEGIN")
    print(json.dumps({"model_results":[{k:v for k,v in m.items() if k not in ["features","blocks"]} for m in summary],
        "init":initial_summary,"old_k5_ari":output["old_labels_reproduction_k5_ARI"],
        "nri_vs_no_nri_ARI":next((p["ARI"] for p in comparisons
             if {p["model_a"],p["model_b"]}=={"joint_v2_with_nri","joint_v2_without_nri"}),None)},indent=2))
    print("JOINT_RECLUSTER_END")
if __name__=="__main__":main()
