"""Inspect recorded Stage7 built-environment correlations, completeness and joint VIF.
This is source-identity-checked descriptive analysis, NOT selection by old cluster labels.
"""
from pathlib import Path
import json,hashlib,itertools
import numpy as np,pandas as pd
from scipy.stats import pearsonr,spearmanr
ROOT=Path(__file__).resolve().parents[4]
SRC=ROOT/"docs/data_research/built_environment_20261009/local_joint_feature_extraction_20261009"
FEMA=ROOT/"docs/data_research/built_environment_20261009/nri_eal_redundancy_audit_20261009/MATCHED_FEMA_STAGE7_FEATURES.csv"
OUT=Path(__file__).resolve().parent/"results"
INPUTS={
 "RESIDENTIAL_2291_FEATURE_MATRIX.csv":"eea230dd2f1e6be857bc35470a77d62a867ce9c47b471416cb57dc21e1aec973",
 "FEATURE_CORRELATION_MATRIX.csv":"1013d1bee407da444f5ca380ccdec2bc1a605083b5f49e416854f453fa3b4682",
 "FEATURE_COVERAGE_QA.csv":"0d1104866f69a95f9dd34db22210f9d7dfc27d08da77648f93b3fc376ab14e5e"
}
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
 return h.hexdigest()
def pair(d,a,b):
 x=d[[a,b]].copy()
 x[a]=pd.to_numeric(x[a],errors="coerce");x[b]=pd.to_numeric(x[b],errors="coerce")
 x=x.replace([np.inf,-np.inf],np.nan).dropna()
 if len(x)<10 or any(x[c].nunique()<2 for c in [a,b]):return {"a":a,"b":b,"n":len(x),"r":None,"rho":None}
 p=float(pearsonr(x[a],x[b]).statistic)
 s=float(spearmanr(x[a],x[b]).statistic)
 return {"a":a,"b":b,"n":len(x),"r":p,"rho":s}
def vif(d,cols):
 x=d[cols].replace([np.inf,-np.inf],np.nan).dropna()
 z=x.to_numpy(float);z=(z-z.mean(axis=0))/z.std(axis=0)
 if not np.isfinite(z).all():return {"n":len(x),"status":"nonfinite"}
 out={}
 for j,c in enumerate(cols):
  other=np.delete(z,j,axis=1)
  if len(cols)<=1:out[c]=1.;continue
  k=np.c_[np.ones(len(other)),other];beta=np.linalg.lstsq(k,z[:,j],rcond=None)[0]
  residue=z[:,j]-k@beta
  r2=1-float(np.sum(residue**2)/np.sum(z[:,j]**2))
  out[c]={"vif":float(1/(1-r2)) if r2<.999999999 else None,"r2":r2}
 return {"n":len(x),"scope":cols,"max_vif":max(v["vif"] for v in out.values() if isinstance(v,dict) and v["vif"] is not None),"vif":out}
def main():
 OUT.mkdir(exist_ok=True,parents=True)
 d={}
 for name,expected in INPUTS.items():
  p=SRC/name
  if p.stat().st_size<200:raise ValueError("Git LFS not hydrated "+str(p))
  got=digest(p)
  if got!=expected:raise ValueError("Frozen source hash discrepancy "+name+" "+got)
  d[name]=pd.read_csv(p,dtype={"tract_id":str},low_memory=False)
 frame=d["RESIDENTIAL_2291_FEATURE_MATRIX.csv"]
 assert len(frame)==2291 and frame.tract_id.is_unique
 a=pd.read_csv(FEMA,dtype={"tract_id":str},low_memory=False)
 assert len(a)==2291 and a.tract_id.is_unique and set(a.tract_id)==set(frame.tract_id)
 for c in ["EAL_SCORE","ALR_NPCTL"]:
  assert c in a, f"{c} absent from archived original FEMA source"
 frame=frame.merge(a[["tract_id","EAL_SCORE","ALR_NPCTL"]],on="tract_id",how="left",validate="one_to_one")
 fields=["land_use_entropy","land_use_classified_land_coverage","building_footprint_coverage",
   "building_count_density","building_height_area_weighted_m",
   "all_use2014_pre1970_area_share","all_use2014_age_coverage",
   "all_use_pre1970_area_share","all_use_age_coverage",
   "residential_pre1970_housing_share","housing_5plus_share",
   "Pop_Density","NRI_BUILDVALUE","SOVI_SCORE","B_480_hr","T80",
   "Init_Supply","EAL_SCORE","ALR_NPCTL","impervious_land_fraction"]
 for c in fields:assert c in frame, f"Missing {c}"
 for c in ["building_count_density","Pop_Density","NRI_BUILDVALUE","B_480_hr"]:
  frame["log_"+c]=np.log1p(pd.to_numeric(frame[c],errors="coerce").where(frame[c]>=0))
 contrasts=[
 ("land_use_entropy","building_footprint_coverage"),
 ("land_use_entropy","log_building_count_density"),
 ("land_use_entropy","all_use2014_pre1970_area_share"),
 ("building_footprint_coverage","all_use2014_pre1970_area_share"),
 ("building_footprint_coverage","log_building_count_density"),
 ("building_footprint_coverage","log_Pop_Density"),
 ("log_building_count_density","log_Pop_Density"),
 ("all_use2014_pre1970_area_share","residential_pre1970_housing_share"),
 ("all_use2014_pre1970_area_share","land_use_classified_land_coverage"),
 ("housing_5plus_share","building_footprint_coverage"),
 ("housing_5plus_share","log_building_count_density"),
 ("land_use_entropy","SOVI_SCORE"),("land_use_entropy","EAL_SCORE"),
 ("building_footprint_coverage","SOVI_SCORE"),("building_footprint_coverage","EAL_SCORE"),
 ("all_use2014_pre1970_area_share","SOVI_SCORE"),
 ("all_use2014_pre1970_area_share","EAL_SCORE"),
 ("B_480_hr","T80"),("B_480_hr","Init_Supply")
 ]
 corrs=[pair(frame,x,y) for x,y in contrasts]
 pd.DataFrame(corrs).to_csv(OUT/"KEY_PHYSICAL_CORRELATIONS.csv",index=False)
 coverage=[]
 for c in fields:
  v=frame[c].replace([np.inf,-np.inf],np.nan)
  nonnull=v.dropna()
  coverage.append({"feature":c,"n":len(v),"observed":int(v.notna().sum()),"missing":int(v.isna().sum()),
   "fraction":float(v.notna().mean()),
   "median":float(nonnull.median()) if pd.api.types.is_numeric_dtype(nonnull) and len(nonnull) else None,
   "p10":float(nonnull.quantile(.1)) if pd.api.types.is_numeric_dtype(nonnull) and len(nonnull) else None})
 pd.DataFrame(coverage).to_csv(OUT/"KEY_FEATURE_COVERAGE.csv",index=False)
 flag=frame.land_mask_area_check_pass
 assert flag.dtype==bool or set(flag.dropna().astype(str).unique()).issubset({"True","False","true","false"})
 if flag.dtype!=bool:flag=flag.astype(str).str.lower().eq("true")
 strata={}
 for name,mask in {
  "all":np.ones(len(frame),bool),
  "landmask_pass":flag.to_numpy(),
  "landmask_and_SCAG_coverage_ge_70pct":(flag & frame.land_use_classified_land_coverage.ge(.7)).to_numpy(),
  "landmask_and_SCAG_coverage_ge_85pct":(flag & frame.land_use_classified_land_coverage.ge(.85)).to_numpy(),
  "landmask_and_SCAG_coverage_ge_90pct":(flag & frame.land_use_classified_land_coverage.ge(.90)).to_numpy(),
  "landmask_and_original2014_age_coverage_ge_80pct":(flag & frame.all_use2014_age_coverage.ge(.8)).to_numpy(),
  "landmask_and_SCAG85_original2014age80":(flag & frame.land_use_classified_land_coverage.ge(.85) &
       frame.all_use2014_age_coverage.ge(.8)).to_numpy(),
 }.items():
  x=frame.loc[mask].copy()
  three=["land_use_entropy","building_footprint_coverage","all_use2014_pre1970_area_share"]
  stratum_corr=[pair(x,aa,bb) for aa,bb in itertools.combinations(three,2)]
  strata[name]={"n":len(x),"pairs":stratum_corr,"three_observed":int(x[three].notna().all(axis=1).sum()),
   "mean_age":float(x.all_use2014_pre1970_area_share.mean()),
   "mean_entropy":float(x.land_use_entropy.mean()),
   "mean_footprint":float(x.building_footprint_coverage.mean())}
 # Full-domain observed overlap for primary selections, e.g. 2014-vintage age not 2020 strict link.
 models={
  "built_entropy_footprint_age2014": ["land_use_entropy","building_footprint_coverage","all_use2014_pre1970_area_share"],
  "built_entropy_footprint": ["land_use_entropy","building_footprint_coverage"],
  "built_footprint_age2014": ["building_footprint_coverage","all_use2014_pre1970_area_share"],
  "built_entropy_count_age2014":["land_use_entropy","log_building_count_density","all_use2014_pre1970_area_share"],
  "core_B_EAL": ["log_B_480_hr","Init_Supply","Grid_Degree","Grid_Impact","Grid_Betweenness",
    "Redundancy_HHI","land_use_entropy","building_footprint_coverage","all_use2014_pre1970_area_share",
    "SOVI_SCORE","EAL_SCORE"],
  "core_B_D": ["log_B_480_hr","Init_Supply","Grid_Degree","Grid_Impact","Grid_Betweenness",
    "Redundancy_HHI","land_use_entropy","building_footprint_coverage","all_use2014_pre1970_area_share",
    "SOVI_SCORE","log_NRI_BUILDVALUE","ALR_NPCTL"]
 }
 vv={}
 for name,cols in models.items():vv[name]=vif(frame,cols)
 result={"sources_verified":INPUTS,"fema_hash":digest(FEMA),"n":len(frame),
   "pairs":corrs,"coverage":coverage,"strata":strata,"joint_vif":vv,
   "interpretation":"Descriptive tract data only. 2014 original building age is year-specific, not observed 2020 age. SCAG entropy uses classified area only. Census ALAND mask divergences remain. Historical cluster labels were not used."}
 (OUT/"FEATURE_GATE_SUMMARY.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
 print("FEATURE_GATE_RESULT_BEGIN")
 print(json.dumps({"n":len(frame),"pairs":corrs,"strata":strata,
  "vif_summary":{k:{"n":v["n"],"max_vif":v["max_vif"]} for k,v in vv.items()}},
  indent=2,allow_nan=False))
 print("FEATURE_GATE_RESULT_END")
if __name__=="__main__":main()
