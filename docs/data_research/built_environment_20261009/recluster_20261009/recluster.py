"""New ex-ante Stage 7 typology. No event simulation; never overwrites formal outputs.
Selection of columns and blocks is construct-driven, independent of old labels/outcomes.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, silhouette_score)
from sklearn.preprocessing import StandardScaler

REPO = Path(__file__).resolve().parents[4]
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results"
STAGE7 = REPO / "Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv"
ACS = REPO / "docs/data_research/built_environment_20261009/validation/ACS_TRACT_VALIDATION.csv"
NLCD = REPO / "docs/data_research/built_environment_20261009/validation/NLCD_TRACT_EXTRACTION.csv"
NETWORK = ["Grid_Degree","Grid_Impact","Grid_Betweenness","Redundancy_HHI"]
BUILT = ["Pre_1970_Ratio","housing_5plus_share"]
CONTEXT = ["Pop_Density"]
SOCIOECON = ["SOVI_SCORE","NRI_BUILDVALUE"]
HELDOUT = ["T80","Init_Supply"]
BASELINE = ["T80","Init_Supply",*NETWORK,"Pre_1970_Ratio",
            "Pop_Density","NRI_RISK_SCORE","NRI_BUILDVALUE","SOVI_SCORE"]
PRIMARY = [*BUILT,*CONTEXT,*NETWORK,*SOCIOECON]
BLOCKS = {"housing_urban_context":[*BUILT,*CONTEXT],
          "electrical_topology":NETWORK,
          "social_economic":SOCIOECON}
SEED = 42
KS = list(range(2,9))

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def read(path):
    x=pd.read_csv(path,dtype={"tract_id":str})
    if "tract_id" not in x: raise ValueError(f"No tract_id: {path}")
    x["tract_id"]=x["tract_id"].str.zfill(11)
    if x.tract_id.isna().any() or x.tract_id.duplicated().any():
        raise ValueError(f"Invalid/duplicate tract ids: {path}")
    return x

def normalized(x,cols,blocks=None):
    x=x[cols].astype(float).copy()
    for name in ["Pop_Density","NRI_BUILDVALUE"]:
        if name in x:
            if (x[name]<0).any(): raise ValueError(f"Negative input for log1p: {name}")
            x[name]=np.log1p(x[name])
    arr=x.to_numpy(float)
    if not np.isfinite(arr).all(): raise ValueError("Missing or infinite modeling input")
    z=StandardScaler().fit_transform(arr)
    if blocks is not None:
        if set(sum(blocks.values(),[]))!=set(cols):
            raise ValueError("Blocks must partition the selected coordinates")
        if len(sum(blocks.values(),[]))!=len(cols):
            raise ValueError("Repeated coordinate across blocks")
        for members in blocks.values():
            weight=(len(blocks)*len(members))**(-.5)
            for col in members: z[:,cols.index(col)]*=weight
    return z

def evaluate_k(z,model_name):
    rows=[]
    for k in KS:
        km=KMeans(n_clusters=k,random_state=SEED,n_init=20,max_iter=500)
        labels=km.fit_predict(z)
        sizes=np.bincount(labels,minlength=k)
        rows.append(dict(model=model_name,k=k,silhouette=float(silhouette_score(z,labels)),
            calinski_harabasz=float(calinski_harabasz_score(z,labels)),
            davies_bouldin=float(davies_bouldin_score(z,labels)),
            inertia=float(km.inertia_),min_n=int(sizes.min()),max_n=int(sizes.max()),
            min_fraction=float(sizes.min()/len(z))))
    d=pd.DataFrame(rows)
    acceptable=d.loc[d.min_fraction>=.02]
    pool=acceptable if len(acceptable) else d
    pick=pool.sort_values(["silhouette","k"],ascending=[False,True]).iloc[0]
    return d,int(pick.k),bool(len(acceptable))

def kfit(z,k):
    return KMeans(n_clusters=k,random_state=SEED,n_init=30,max_iter=500).fit(z)

def sensitivity(z,reference,k):
    rows=[]
    rng=np.random.default_rng(20261009)
    for i in range(12):
        sample=rng.choice(len(z),size=int(.8*len(z)),replace=False)
        km=KMeans(n_clusters=k,random_state=1000+i,n_init=10,max_iter=500)
        km.fit(z[sample])
        predicted=km.predict(z)
        rows.append(dict(resample=i,train_n=len(sample),
            ari_all=adjusted_rand_score(reference,predicted),
            ari_training=adjusted_rand_score(reference[sample],predicted[sample])))
    return pd.DataFrame(rows)

def profiles(frame,name,labels,columns):
    g=frame.copy()
    g["new_cluster"]=labels
    rows=[]
    describe=[*dict.fromkeys([*columns,*HELDOUT,"NRI_RISK_SCORE"])]
    for cluster,chunk in g.groupby("new_cluster",sort=True):
        d={"model":name,"new_cluster":int(cluster),"n":len(chunk)}
        for col in describe:
            if col not in chunk: continue
            x=chunk[col].astype(float)
            d[col+"_mean"]=float(x.mean())
            d[col+"_median"]=float(x.median())
            d[col+"_p25"]=float(x.quantile(.25))
            d[col+"_p75"]=float(x.quantile(.75))
        rows.append(d)
    return pd.DataFrame(rows)

def compare(a,b):
    return float(adjusted_rand_score(a,b))

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    for p in [STAGE7,ACS,NLCD]:
        if not p.exists() or p.stat().st_size<200:
            raise FileNotFoundError(f"Real Git LFS data required, not pointer: {p}")
    old=read(STAGE7)
    acs=read(ACS)
    raster=read(NLCD)
    if (len(old),len(acs),len(raster))!=(2291,2315,2315):
        raise ValueError("Domain sizes differ from source snapshot")
    m=old.merge(acs[["tract_id","housing_5plus_share","housing_5plus_share_moe90",
                     "housing_total"]],on="tract_id",how="left",validate="one_to_one")
    m=m.merge(raster[["tract_id","impervious_land_fraction"]],on="tract_id",
              how="left",validate="one_to_one")
    required=[*dict.fromkeys([*BASELINE,*PRIMARY,"impervious_land_fraction"])]
    if not np.isfinite(m[required].to_numpy(float)).all():
        raise ValueError("Required values missing after source GEOID joins")
    if (m.housing_total<=0).any(): raise ValueError("Residential tract with zero housing")
    if not m.housing_5plus_share.between(0,1).all(): raise ValueError("ACS configuration fraction out of bounds")
    if not m.impervious_land_fraction.between(0,1).all(): raise ValueError("Raster fraction out of bounds")
    if (m.tract_id.str.len()!=11).any() or not m.tract_id.str.startswith("06037").all():
        raise ValueError("Unexpected tract identifiers")
    baseline_z=normalized(m,BASELINE)
    baseline_fit=kfit(baseline_z,5)
    old_ari=compare(m.cluster.to_numpy(),baseline_fit.labels_)
    # Original comparison is QA, not feature/k selection. sklearn version may affect exact labels.
    models={
        "primary_equal_domain":(PRIMARY,BLOCKS,"PRIMARY_VERIFIED"),
        "primary_equal_coordinate":(PRIMARY,None,"WEIGHT_SENSITIVITY"),
        "primary_plus_nri":([*PRIMARY,"NRI_RISK_SCORE"],
          {**BLOCKS,"multi_hazard_composite":["NRI_RISK_SCORE"]},"RISK_SENSITIVITY"),
        "housing_only":(BUILT,None,"REDUCED_HOUSING_ONLY"),
        "pilot_plus_impervious":([*PRIMARY,"impervious_land_fraction"],
          {**BLOCKS,"housing_urban_context":[*BUILT,*CONTEXT,"impervious_land_fraction"]},
          "PILOT_UNVERIFIED_NLCD"),
    }
    diagnostics=[]
    members=[]
    profile_tables=[]
    k5_tables=[]
    model_summary=[]
    prepared={}
    for name,(cols,blocks,status) in models.items():
        x=normalized(m,cols,blocks)
        diag,k,accepted=evaluate_k(x,name)
        diagnostics.append(diag)
        fitted=kfit(x,k)
        labels=fitted.labels_+1
        stab=sensitivity(x,fitted.labels_,k)
        stab.to_csv(OUT/(name+"_stability.csv"),index=False)
        for tract,label in zip(m.tract_id,labels):
            members.append(dict(tract_id=tract,model=name,cluster=int(label)))
        prof=profiles(m,name,labels,cols)
        profile_tables.append(prof)
        k5=kfit(x,5)
        k5_tables.append(pd.DataFrame({"tract_id":m.tract_id,"model":name,
                                      "k5_cluster":k5.labels_+1}))
        score_sil=float(diag.loc[diag.k.eq(k),"silhouette"].iloc[0])
        model_summary.append(dict(model=name,status=status,n=len(m),p=len(cols),
            selected_k=k,passed_min_cluster_2pct=accepted,
            silhouette=score_sil,smallest_cluster=int(np.bincount(fitted.labels_).min()),
            bootstrap_median_ari=float(stab.ari_all.median()),
            bootstrap_min_ari=float(stab.ari_all.min()),
            ari_vs_original_old_labels=compare(m.cluster,labels),
            ari_k5_vs_old_labels=compare(m.cluster,k5.labels_),
            features=cols,blocks=blocks))
        prepared[name]=(x,labels)
    result=pd.DataFrame(members)
    result.to_csv(OUT/"new_cluster_assignments.csv",index=False)
    pd.concat(diagnostics,ignore_index=True).to_csv(OUT/"k_selection_diagnostics.csv",index=False)
    pd.concat(profile_tables,ignore_index=True).to_csv(OUT/"cluster_profiles_with_heldout_outcomes.csv",index=False)
    pd.concat(k5_tables,ignore_index=True).to_csv(OUT/"fixed_k5_comparison_labels.csv",index=False)
    # Same-tract comparison, no outcomes in any new distance.
    model_names=list(models)
    pairwise=[dict(model_a=a,model_b=b,
                   ari=compare(prepared[a][1],prepared[b][1]))
              for i,a in enumerate(model_names) for b in model_names[i+1:]]
    pd.DataFrame(pairwise).to_csv(OUT/"model_pairwise_ari.csv",index=False)
    # PCA diagnostic on the actually weighted KMeans feature space only.
    x,labels=prepared["primary_equal_domain"]
    pcs=PCA().fit(x)
    pd.DataFrame({"pc":np.arange(1,x.shape[1]+1),
                  "explained_variance_ratio":pcs.explained_variance_ratio_,
                  "cumulative_ratio":np.cumsum(pcs.explained_variance_ratio_)}).to_csv(OUT/"primary_pca_variance.csv",index=False)
    pd.DataFrame(pcs.components_.T,index=PRIMARY,
                 columns=["PC"+str(i+1) for i in range(len(PRIMARY))]).to_csv(OUT/"primary_pca_loadings.csv")
    # Factor uncertainty affects inputs: preserve all tracts and report MOE tiers;
    # do not select screened tracts for the main solution.
    share=m.housing_5plus_share_moe90
    primary_labels=prepared["primary_equal_domain"][1]
    core_sensitivity=[]
    for flag,mask in {"all":np.ones(len(m),bool),"acs_moe_le10pp":share.le(.10).to_numpy(),
                      "acs_moe_le5pp":share.le(.05).to_numpy()}.items():
        for c in sorted(np.unique(primary_labels)):
            s=(primary_labels==c)&mask
            core_sensitivity.append(dict(screen=flag,cluster=int(c),n=int(s.sum()),
                fraction_retained=float(s.sum()/(primary_labels==c).sum()),
                housing5plus_mean=float(m.loc[s,"housing_5plus_share"].mean()) if s.any() else None))
    pd.DataFrame(core_sensitivity).to_csv(OUT/"primary_acs_uncertainty_screening.csv",index=False)
    m[["tract_id","cluster","T80","Init_Supply","housing_5plus_share",
       "housing_5plus_share_moe90","impervious_land_fraction"]].to_csv(
          OUT/"input_audit_and_heldout.csv",index=False)
    summary={"provenance":{"base_commit":"031d2c675f8e7d58035d27448be040b809ced086",
        "source_sha256":{str(p.relative_to(REPO)):digest(p) for p in [STAGE7,ACS,NLCD]},
        "original_stage7_k5_ari_reproduction":old_ari,
        "n_original_clusters":int(m.cluster.nunique()),"n_residential":len(m),
        "n_acs_moe_gt10pp":int(share.gt(.1).sum()),
        "impervious_status":"PILOT_ONLY_ESRI_MIRROR_NOT_AUTHORITATIVE"},
        "rule":"Choose highest whole-sample silhouette among k=2..8 with >=2% of tracts per cluster; if none, highest silhouette with failure flag. Stability and held-out outcomes are not selection criteria.",
        "models":model_summary,"comparisons":pairwise}
    (OUT/"SUMMARY.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    print("RESULT_BEGIN")
    print(json.dumps({"baseline_old_ari":old_ari,"models":[{k:v for k,v in d.items()
          if k not in ("features","blocks")} for d in model_summary],
          "pairwise":pairwise,
          "primary_cluster_profiles":profiles(m,"primary_equal_domain",primary_labels,PRIMARY)[
              ["new_cluster","n","Pre_1970_Ratio_mean","housing_5plus_share_mean",
               "Pop_Density_mean","SOVI_SCORE_mean","T80_mean","Init_Supply_mean"]].to_dict("records")},
          indent=2,allow_nan=False))
    print("RESULT_END")
if __name__=="__main__": run()
