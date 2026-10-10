"""Independent same-version FEMA NRI v1.19 multi-hazard EAL redundancy audit.

Scientific guardrails: SOVI_SCORE stays mandatory; no earthquake-only substitution,
no cluster-label-driven feature choice, no edits to Stage 7 scientific outputs.
"""
from __future__ import annotations
import json,hashlib,itertools,re
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent/"results"
NRI=ROOT/"Data/NRI_Table_CensusTracts_California.csv"
OLD=ROOT/"Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv"
EXPECTED={
 "Data/NRI_Table_CensusTracts_California.csv":
    "5248639b400f46e85d1fa751e257afcc27b43f1575aa2f9fd986d3eedd6df310",
 "Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv":
    "2117360be90914f1584e4ea3d7e1db120638225180fc3a17e669a9d227ff8228"
}
FIELDS=["RISK_SCORE","RISK_VALUE","EAL_SCORE","EAL_VALT","EAL_VALB","EAL_VALP",
        "EAL_VALPE","EAL_VALA","SOVI_SCORE","RESL_SCORE","BUILDVALUE",
        "ALR_VALB","ALR_VALP","ALR_VALA","ALR_NPCTL","ALR_VRA_NPCTL",
        "POPULATION"]
RAW_PAIRED=["SOVI_SCORE","BUILDVALUE","EAL_SCORE","EAL_VALT","RISK_SCORE",
    "RESL_SCORE","EAL_VALB","EAL_VALPE","EAL_VALA","ALR_NPCTL"]
def hashfile(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()
def read_study():
    for p in [NRI,OLD]:
        if not p.exists() or p.stat().st_size<200:
            raise FileNotFoundError(f"Unhydrated LFS input: {p}")
        key=str(p.relative_to(ROOT))
        value=hashfile(p)
        if value !=EXPECTED[key]:
            raise ValueError(f"Frozen source file hash mismatch: {key} {value}")
    old=pd.read_csv(OLD,dtype={"tract_id":str},low_memory=False)
    if len(old)!=2291 or old.tract_id.duplicated().any():raise ValueError("Original Stage 7 residential universe has changed")
    old["tract_id"]=old.tract_id.str.zfill(11)
    raw=pd.read_csv(NRI,dtype={"TRACTFIPS":str,"NRI_ID":str},low_memory=False)
    if len(raw)!=9106:raise ValueError(f"Original NRI 2023 dataset row count differs: {len(raw)}")
    orig_id=raw["TRACTFIPS"].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
    raw["tract_id"]=orig_id.str.extract(r"(\d{10,11})$")[0].str.zfill(11)
    raw=raw.loc[raw.tract_id.isin(set(old.tract_id))].copy()
    if len(raw)!=len(old) or raw.tract_id.duplicated().any():
        raise ValueError("FEMA original source did not exactly match 2291 archived tracts")
    hazard_fields=sorted(c for c in raw.columns if re.fullmatch(r"[A-Z]{4}_EALT",c))
    original_fields=[x for x in FIELDS if x in raw.columns]+hazard_fields
    source_frame=raw[["tract_id"]+original_fields].rename(columns={"SOVI_SCORE":"FEMA_SOVI_SCORE"})
    available=[("FEMA_SOVI_SCORE" if x=="SOVI_SCORE" else x) for x in original_fields]
    matched=old[["tract_id","SOVI_SCORE","NRI_BUILDVALUE","NRI_RISK_SCORE","Pop_Density"]].merge(
        source_frame,on="tract_id",how="inner",validate="one_to_one")
    for x in available:
        matched[x]=pd.to_numeric(matched[x],errors="coerce")
    checks={}
    for archived,official in [("SOVI_SCORE","FEMA_SOVI_SCORE"),("NRI_BUILDVALUE","BUILDVALUE"),
                              ("NRI_RISK_SCORE","RISK_SCORE")]:
        if archived in matched and official in matched:
            delta=(matched[archived]-matched[official]).abs()
            checks[archived]={"max_abs_difference":float(delta.max()),
                              "n_compared":int(delta.notna().sum())}
    # Retain source FEMA social score as a single canonical input.
    if "FEMA_SOVI_SCORE" not in matched:raise KeyError("Original FEMA SOVI missing")
    matched["SOVI_SCORE"]=matched["FEMA_SOVI_SCORE"]
    if "EAL_SCORE" not in matched:raise ValueError("Archived FEMA EAL_SCORE missing")
    return matched,available,checks

def series_summary(a):
    x=pd.to_numeric(a,errors="coerce")
    x=x.replace([np.inf,-np.inf],np.nan)
    y=x.dropna()
    if not len(y):return {"n":0}
    return {"n":int(len(y)),"missing":int(x.isna().sum()),"zeros":int((y==0).sum()),
            "negative":int((y<0).sum()),"min":float(y.min()),"median":float(y.median()),
            "p95":float(y.quantile(.95)),"max":float(y.max()),"unique":int(y.nunique())}
def cpair(a,b):
    valid=pd.concat([pd.to_numeric(a,errors="coerce"),
                     pd.to_numeric(b,errors="coerce")],axis=1).replace([np.inf,-np.inf],np.nan).dropna()
    if len(valid)<4 or valid.iloc[:,0].nunique()<2 or valid.iloc[:,1].nunique()<2:
        return {"n":int(len(valid)),"pearson_r":None,"spearman_rho":None}
    v=valid.to_numpy(dtype=float)
    return {"n":len(valid),"pearson_r":float(pearsonr(v[:,0],v[:,1]).statistic),
            "spearman_rho":float(spearmanr(v[:,0],v[:,1]).statistic)}
def within_set(frame,cols):
    data=frame[cols].apply(pd.to_numeric,errors="coerce").replace([np.inf,-np.inf],np.nan).dropna()
    v=data.to_numpy(float)
    if len(v)<20 or (np.std(v,axis=0)==0).any():
        return {"n":int(len(v)),"status":"constant_or_insufficient"}
    standardized=(v-v.mean(axis=0))/(v.std(axis=0))
    rows={}
    for i,col in enumerate(cols):
        X=np.column_stack([np.ones(len(v)),np.delete(standardized,i,axis=1)])
        y=standardized[:,i]
        beta=np.linalg.lstsq(X,y,rcond=None)[0]
        residual=y-X@beta
        r2=1-float(np.sum(residual**2))/float(np.sum((y-y.mean())**2))
        rows[col]={"r2_on_other_inputs":r2,"vif":float(1/(1-r2)) if r2<.999999 else None}
    s=np.linalg.svd(standardized,full_matrices=False)[1]
    return {"n":len(v),"status":"ok","features":cols,
            "condition_number":float(s[0]/s[-1]),"per_input":rows}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x,fields,checks=read_study()
    # Use source-defined SOVI unchanged; avoid adding a duplicate score.
    if "SOVI_SCORE" not in x:raise RuntimeError("Social vulnerability missing")
    x["log_BUILDVALUE"]=np.log1p(x["BUILDVALUE"]) if (x["BUILDVALUE"]>=0).all() else np.nan
    for field in ["EAL_VALT","EAL_VALB","EAL_VALPE","EAL_VALA","RISK_VALUE"]:
        if field in x:
            v=x[field]
            x["log_"+field]=np.log1p(v.where(v>=0))
    if "POPULATION" in x:
        x["log_POPULATION"]=np.log1p(x["POPULATION"].where(x["POPULATION"]>=0))
    x["log_Pop_Density"]=np.log1p(x["Pop_Density"].where(x["Pop_Density"]>=0))
    combinations=[
      ["SOVI_SCORE","log_BUILDVALUE","RISK_SCORE"],  # A: 2023 original
      ["SOVI_SCORE","EAL_SCORE"],                   # B: author's main hypothesis
      ["SOVI_SCORE","log_BUILDVALUE","EAL_SCORE"], # C: preserve both constructs
      ["SOVI_SCORE","log_BUILDVALUE","ALR_NPCTL"], # D: if present
      ["SOVI_SCORE","log_EAL_VALT"],               # E: loss-value scale
      ["SOVI_SCORE","log_BUILDVALUE","log_EAL_VALT"],
    ]
    def label(cols):
        return " + ".join(cols)
    vif_rows=[]
    for cols in combinations:
        if all(c in x for c in cols):
            stat=within_set(x,cols)
            vif_rows.append({"features":cols,**stat})
    # Report pairwise transformed and raw source values rather than choosing one.
    measures=[c for c in dict.fromkeys(
      ["SOVI_SCORE","log_BUILDVALUE","BUILDVALUE","EAL_SCORE","EAL_VALT",
       "log_EAL_VALT","RISK_SCORE","RISK_VALUE","RESL_SCORE",
       "log_Pop_Density","EAL_VALB","EAL_VALPE","EAL_VALA","ALR_NPCTL","ALR_VRA_NPCTL"]
    ) if c in x]
    rows=[]
    for a,b in itertools.combinations(measures,2):
        rows.append({"measure_a":a,"measure_b":b,**cpair(x[a],x[b])})
    pairs=pd.DataFrame(rows)
    pairs.to_csv(OUT/"PAIRWISE_CORRELATIONS.csv",index=False)
    hazard_composition=None
    hazard_cols=sorted(c for c in x.columns if re.fullmatch(r"[A-Z]{4}_EALT",c))
    if hazard_cols and "EAL_VALT" in x:
        hazard=x[hazard_cols].apply(pd.to_numeric,errors="coerce")
        total=x["EAL_VALT"]
        valid=total.gt(0)&total.notna()
        hazsum=hazard.sum(axis=1,min_count=1)
        residual=hazsum-total
        shares=hazard.div(total,axis=0).where(valid, np.nan)
        top1=shares.max(axis=1)
        top3=np.sort(shares.fillna(0).to_numpy(float),axis=1)[:,-3:].sum(axis=1)
        hhi=np.square(shares.fillna(0)).sum(axis=1).where(valid,np.nan)
        hazard_composition={
          "n_source_hazard_columns":len(hazard_cols),
          "all_columns":hazard_cols,
          "sum_hazard_eal_minus_total_max_abs":float(residual.abs().max()),
          "sum_hazard_eal_minus_total_median_abs":float(residual.abs().median()),
          "mean_dominant_hazard_share":float(top1[valid].mean()),
          "median_dominant_hazard_share":float(top1[valid].median()),
          "median_top_three_share":float(np.median(top3[valid.to_numpy()])),
          "median_effective_hazards":(float(np.nanmedian((1/hhi.replace(0,np.nan)).to_numpy())) if hhi.gt(0).any() else None),
          "mean_hazard_share":{
             c:(float(shares[c].mean()) if np.isfinite(shares[c].mean()) else None)
             for c in hazard_cols
          },
          "aggregate_expected_loss_share":{
             c:float(hazard[c].fillna(0).sum()/total[valid].sum()) for c in hazard_cols
          },
          "n_hazards_nonzero_by_tract":{
             "median":float(hazard.gt(0).sum(axis=1).median()),
             "minimum":int(hazard.gt(0).sum(axis=1).min()),
             "maximum":int(hazard.gt(0).sum(axis=1).max())
          }
        }
        pd.DataFrame({"tract_id":x["tract_id"],"EAL_VALT":total,"dominant_hazard_share":top1,
           "top3_hazard_share":top3,"effective_hazard_count":1/hhi}).to_csv(
            OUT/"TRACT_HAZARD_CONCENTRATION.csv",index=False)
        pd.DataFrame([{"hazard_column":c,"mean_tract_share":shares[c].mean(),
              "share_of_total_monetary_eal":hazard_composition["aggregate_expected_loss_share"][c]}
              for c in hazard_cols]).to_csv(OUT/"EAL_HAZARD_COMPOSITION.csv",index=False)
    delta_composition=None
    if all(t in x for t in ["EAL_VALT","EAL_VALB","EAL_VALPE","EAL_VALA"]):
        diff=x["EAL_VALT"]-(x["EAL_VALB"]+x["EAL_VALPE"]+x["EAL_VALA"])
        delta_composition={"n":int(diff.notna().sum()),
                           "max_abs_delta_dollars":float(diff.abs().max()),
                           "median_abs_delta_dollars":float(diff.abs().median())}
    diag={c:series_summary(x[c]) for c in measures}
    full_summary={"source_version":"FEMA v1.19 March 2023, 2291 residential tracts",
      "n":len(x),"source_sha256":EXPECTED,"original_source_field_names":fields,
      "identity_checks":checks,"field_diagnostics":diag,
      "pairwise_key":{},
      "vif_models":vif_rows,"component_sum_check":delta_composition,
      "hazard_composition":hazard_composition,
      "method":"Pearson and Spearman on same exact tract IDs, monetary values log1p only when nonnegative",
      "decision_status":"DIAGNOSTIC_ONLY; keep SOVI mandatory; no completed model selection"}
    keypairs=[
      ("SOVI_SCORE","log_BUILDVALUE"),("SOVI_SCORE","EAL_SCORE"),
      ("SOVI_SCORE","log_EAL_VALT"),("EAL_SCORE","log_BUILDVALUE"),
      ("EAL_SCORE","RISK_SCORE"),("EAL_SCORE","RESL_SCORE"),
      ("EAL_SCORE","log_EAL_VALT"),("EAL_SCORE","ALR_NPCTL"),
      ("log_EAL_VALT","log_BUILDVALUE"),("RISK_SCORE","SOVI_SCORE"),
      ("RISK_SCORE","log_BUILDVALUE"),("EAL_SCORE","log_Pop_Density"),
      ("ALR_NPCTL","log_BUILDVALUE"),("ALR_NPCTL","SOVI_SCORE")
    ]
    for a,b in keypairs:
        if a in x and b in x:
            full_summary["pairwise_key"][a+" | "+b]=cpair(x[a],x[b])
    # All raw values and diagnostics remain independent of previous cluster labels.
    (OUT/"EAL_AUDIT_SUMMARY.json").write_text(json.dumps(full_summary,indent=2,allow_nan=False)+"\n")
    (OUT/"CANDIDATE_SET_VIF.json").write_text(json.dumps(vif_rows,indent=2,allow_nan=False)+"\n")
    x[["tract_id"]+[c for c in [
        "SOVI_SCORE","NRI_BUILDVALUE","NRI_RISK_SCORE","EAL_SCORE","EAL_VALT",
        "EAL_VALB","EAL_VALP","EAL_VALPE","EAL_VALA","RESL_SCORE","BUILDVALUE",
        "ALR_NPCTL","ALR_VALB","ALR_VALP","ALR_VALA","log_BUILDVALUE","log_EAL_VALT"
    ] if c in x]].to_csv(OUT/"SAME_TRACT_SOURCE_VALUES.csv",index=False)
    print("EAL_AUDIT_BEGIN")
    print(json.dumps({"identity_checks":checks,"pairwise_key":full_summary["pairwise_key"],
       "vif_models":vif_rows,"component_sum_check":delta_composition,
       "hazard_composition":hazard_composition,
       "field_names":fields},indent=2,allow_nan=False))
    print("EAL_AUDIT_END")
if __name__=="__main__":main()
