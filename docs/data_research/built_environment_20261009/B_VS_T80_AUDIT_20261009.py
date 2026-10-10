"""Evaluate whether archived FORMAL Stage-7 T80 has a matched formal cumulative burden (B).
Never mix historical and formal records or use cross-policy inconsistent values.
"""
from pathlib import Path
import json, hashlib, math
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
STAGE=ROOT/"Formal_Experiment_20260923"
AUD=ROOT/"docs/data_research/built_environment_20261009"
FILES={
 "formal_stage7":STAGE/"Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv",
 "formal_kpis":STAGE/"Stage 5 Output_expanded/tract_kpis_2pc50.csv",
 "formal_supply":STAGE/"Stage 1 Output_expanded/MC_Tract_Supply_2pc50.csv",
 "legacy_kpis":ROOT/"provenance/legacy_outputs/stage3/tract_kpis_2pc50.csv",
 "legacy_stage5":ROOT/"provenance/legacy_outputs/stage5/tract_kpis_2pc50.csv",
 "resident_validation":AUD/"validation/RESIDENTIAL_VALIDATION_MATRIX.csv",
}
def hashfile(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
 return h.hexdigest()
def load(path):
 f=pd.read_csv(path,dtype={"tract_id":str},low_memory=False)
 if "tract_id" in f: f["tract_id"]=f.tract_id.astype(str).str.zfill(11)
 return f
def corr(frame,a,b):
 x=pd.to_numeric(frame[a],errors="coerce");y=pd.to_numeric(frame[b],errors="coerce")
 keep=np.isfinite(x)&np.isfinite(y)
 if keep.sum()<3 or x[keep].std()==0 or y[keep].std()==0: return {"n":int(keep.sum()),"r":None,"rho":None}
 return {"n":int(keep.sum()),"r":float(x[keep].corr(y[keep])),
         "rho":float(x[keep].corr(y[keep],method="spearman"))}
def main():
 report={"base":"031d2c675f8e7d58035d27448be040b809ced086","files":{}, "status":"not_yet_checked"}
 frames={}
 for k,p in FILES.items():
  info={"path":str(p.relative_to(ROOT)),"exists":p.exists()}
  if not p.exists(): report["files"][k]=info;continue
  info["bytes"]=p.stat().st_size
  if p.stat().st_size<200:
   info["hydrated"]=False
   report["files"][k]=info
   continue
  info["sha256"]=hashfile(p)
  f=load(p)
  info["hydrated"]=True;info["rows"]=len(f);info["columns"]=list(f.columns)
  info["tract_id_nunique"]=int(f.tract_id.nunique()) if "tract_id" in f else None
  frames[k]=f
  report["files"][k]=info
 a=frames["formal_stage7"]
 if len(a)!=2291: raise RuntimeError("Original model domain mismatch")
 if "formal_kpis" in frames:
  d=frames["formal_kpis"]
  if "tract_id" in d:
   both=a[["tract_id","T80","Init_Supply"]].merge(d,on="tract_id",validate="one_to_one",suffixes=("_formal","_kpi"))
   if "T80_kpi" in both:
    dv=np.abs(both.T80_formal-both.T80_kpi)
    report["stage7_formal_t80_vs_kpi"]={"n":len(both),"max_abs_diff":float(dv.max()),"num_exceed_1e-8":int((dv>1e-8).sum())}
 # Legacy AUC is never paired against formal T80, even if it has same study ID.
 source=frames.get("formal_kpis")
 status="FORMAL_MATCHED_B_ABSENT"
 if source is not None:
  matches=[x for x in source.columns if x in ["Burden_hr","normalized_burden_hr","restoration_burden_mass_hr","cumulative_loss_hr","B_hr","burden_hr"]]
  if matches and len(matches)==1 and report.get("stage7_formal_t80_vs_kpi",{}).get("max_abs_diff",math.inf)<1e-8:
   key=matches[0]
   both=a[["tract_id","T80","Init_Supply"]].merge(source[["tract_id",key]],on="tract_id",validate="one_to_one")
   report["metric_pairs"]={"B_vs_T80":corr(both,key,"T80"),"B_vs_Initial":corr(both,key,"Init_Supply"),
    "T80_vs_Initial":corr(both,"T80","Init_Supply")}
   status="FORMAL_MATCHED_B_CORRELATION_COMPLETED"
 report["status"]=status
 if "resident_validation" in frames:
  d=frames["resident_validation"]
  feats=["Pre_1970_Ratio","housing_5plus_share","housing_units_per_km2","Pop_Density","impervious_land_fraction"]
  if "housing_units_per_km2" not in d and {"housing_total","ALAND"}.issubset(d.columns):
   d["housing_units_per_km2"]=d.housing_total/(d.ALAND/1e6)
  q=[]
  for i,x in enumerate(feats):
   for y in feats[i+1:]:
    if x in d and y in d:
     v=corr(d,x,y);q.append({"a":x,"b":y,**v})
  report["physical_proxy_correlations"]=q
  # Separate demographic/economic correlation checks. These are NOT the same as
  # an R2 that predicts risk from both variables.
  if "NRI_BUILDVALUE" in d and "SOVI_SCORE" in d:
   d["log_NRI_BUILDVALUE"]=np.log1p(d["NRI_BUILDVALUE"].astype(float))
   report["social_economic_overlaps"]={
    "SOVI_vs_log_BUILDVALUE":corr(d,"SOVI_SCORE","log_NRI_BUILDVALUE"),
    "SOVI_vs_pre1970":corr(d,"SOVI_SCORE","Pre_1970_Ratio"),
    "SOVI_vs_5plus":corr(d,"SOVI_SCORE","housing_5plus_share"),
    "risk_vs_SOVI":corr(d,"NRI_RISK_SCORE","SOVI_SCORE"),
    "risk_vs_log_BUILDVALUE":corr(d,"NRI_RISK_SCORE","log_NRI_BUILDVALUE"),
   }
  if "housing_units_per_km2" in d:
   d["log_housing_units_per_km2"]=np.log1p(d["housing_units_per_km2"].astype(float))
   report["density_overlaps"]={"age_vs_log_housing_density":corr(d,"Pre_1970_Ratio","log_housing_units_per_km2"),
     "5plus_vs_log_housing_density":corr(d,"housing_5plus_share","log_housing_units_per_km2")}
  if "Pop_Density" in d and "housing_units_per_km2" in d:
   d["log_Pop_Density"]=np.log1p(d["Pop_Density"].astype(float))
   report.setdefault("density_overlaps",{})["log_pop_vs_log_housing_density"]=corr(d,"log_Pop_Density","log_housing_units_per_km2")
 out=AUD/"B_VS_T80_20261009_AUDIT.json"
 out.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
 print(json.dumps({"status":report["status"],
 "schemas":{k:{"rows":v.get("rows"),"columns":v.get("columns"),"hydrated":v.get("hydrated")} for k,v in report["files"].items()},
 "T80_identity":report.get("stage7_formal_t80_vs_kpi"),
 "pairs":report.get("metric_pairs"),"proxies":report.get("physical_proxy_correlations"), "social_economic":report.get("social_economic_overlaps"),"density":report.get("density_overlaps")},indent=2,allow_nan=False))
if __name__=="__main__":main()
