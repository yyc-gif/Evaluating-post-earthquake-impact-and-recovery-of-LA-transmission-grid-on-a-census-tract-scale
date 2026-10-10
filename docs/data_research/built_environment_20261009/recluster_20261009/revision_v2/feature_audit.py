"""Outcome-inclusive Stage 7 revision: independently inspect overlap before feature admission.

This audit NEVER chooses candidates according to the five historic cluster labels.
"""
from pathlib import Path
import json, hashlib, itertools
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"
REPO=ROOT.parents[4]
FORMAL=REPO/"Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv"
ACS=REPO/"docs/data_research/built_environment_20261009/validation/ACS_TRACT_VALIDATION.csv"
NLCD=REPO/"docs/data_research/built_environment_20261009/validation/NLCD_TRACT_EXTRACTION.csv"
NRI=REPO/"Data/NRI_Table_CensusTracts_California.csv"
ALL_ORIGINAL=["T80","Init_Supply","Grid_Degree","Grid_Impact","Grid_Betweenness",
              "Redundancy_HHI","Pre_1970_Ratio","Pop_Density","NRI_RISK_SCORE",
              "NRI_BUILDVALUE","SOVI_SCORE"]
CANDIDATES=["housing_5plus_share","housing_10plus_share","housing_single_unit_share",
            "housing_units_per_km2","impervious_land_fraction"]
REQUIRED=ALL_ORIGINAL+CANDIDATES

def digest(f):
    h=hashlib.sha256()
    with f.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def load(f):
    if f.stat().st_size<200:raise RuntimeError(f"Unhydrated LFS pointer: {f}")
    x=pd.read_csv(f,dtype={"tract_id":str},low_memory=False)
    x["tract_id"]=x["tract_id"].str.zfill(11)
    if x.tract_id.isna().any() or x.tract_id.duplicated().any():raise RuntimeError(f"duplicate/missing IDs: {f}")
    return x

def build():
    base=load(FORMAL)
    if len(base)!=2291:raise RuntimeError("Unexpected residential tract universe")
    acs=load(ACS)
    raster=load(NLCD)
    x=base.merge(acs[["tract_id","housing_5plus_share","housing_10plus_share",
       "housing_single_unit_share","housing_total","housing_5plus_share_moe90"]],
       on="tract_id",how="left",validate="one_to_one")
    x=x.merge(raster[["tract_id","ALAND","impervious_land_fraction"]],
              on="tract_id",how="left",validate="one_to_one")
    if x[["housing_total","ALAND"]].isna().any().any():raise RuntimeError("unmatched denominator")
    if (x.ALAND<=0).any() or (x.housing_total<=0).any():raise RuntimeError("bad ALAND/housing")
    x["housing_units_per_km2"]=x.housing_total/(x.ALAND/1e6)
    for c in REQUIRED:
        x[c]=pd.to_numeric(x[c],errors="raise")
        if not np.isfinite(x[c]).all():raise RuntimeError(f"Nonfinite {c}")
    return x

def corr_table(x,cols):
    out=[]
    for a,b in itertools.combinations(cols,2):
        ya=x[a].to_numpy(dtype=float);yb=x[b].to_numpy(dtype=float)
        pr=pearsonr(ya,yb);sr=spearmanr(ya,yb)
        out.append(dict(a=a,b=b,n=len(x),pearson_r=float(pr.statistic),
                        spearman_rho=float(sr.statistic)))
    return pd.DataFrame(out)

def transformed(x):
    d=x[REQUIRED].copy()
    for c in ["Pop_Density","NRI_BUILDVALUE","housing_units_per_km2"]:
        if (d[c]<0).any():raise RuntimeError("negative log input")
        d[c]=np.log1p(d[c])
    return d

def target_associations(x,target,cols):
    raw=corr_table(x,[target]+[c for c in cols if c!=target])
    raw=raw.loc[raw.a.eq(target)].copy()
    raw["abs_r"]=raw.pearson_r.abs()
    return raw.sort_values("abs_r",ascending=False)

def r2_from(x,y,features):
    arr=x[features].to_numpy(float)
    val=x[y].to_numpy(float)
    model=LinearRegression().fit(arr,val)
    return float(model.score(arr,val)),float(np.linalg.cond(StandardScaler().fit_transform(arr))) if len(features)>1 else None

def residual_overlap(x):
    models={
      "RISK | SOVI_SCORE": ["SOVI_SCORE"],
      "RISK | SOVI_SCORE + log BUILDVALUE": ["SOVI_SCORE","NRI_BUILDVALUE"],
      "RISK | other 10 original features":["T80","Init_Supply","Grid_Degree","Grid_Impact","Grid_Betweenness","Redundancy_HHI","Pre_1970_Ratio","Pop_Density","NRI_BUILDVALUE","SOVI_SCORE"],
      "RISK | original features except outcomes":["Grid_Degree","Grid_Impact","Grid_Betweenness","Redundancy_HHI","Pre_1970_Ratio","Pop_Density","NRI_BUILDVALUE","SOVI_SCORE"],
      "FIVEPLUS | log pop density":["Pop_Density"],
      "FIVEPLUS | log housing density":["housing_units_per_km2"],
      "FIVEPLUS | age + log population density":["Pre_1970_Ratio","Pop_Density"],
      "FIVEPLUS | age + log housing density":["Pre_1970_Ratio","housing_units_per_km2"],
      "FIVEPLUS | age + both densities":["Pre_1970_Ratio","Pop_Density","housing_units_per_km2"],
      "FIVEPLUS | age + both densities + impervious PILOT":["Pre_1970_Ratio","Pop_Density","housing_units_per_km2","impervious_land_fraction"],
    }
    rows=[]
    for name,controls in models.items():
        y="NRI_RISK_SCORE" if name.startswith("RISK") else "housing_5plus_share"
        r,c=r2_from(x,y,controls)
        rows.append(dict(model=name,target=y,controls=";".join(controls),r2=r,
                         unexplained_fraction=1-r,conditional_vif=1/(1-r) if r<1 else None,
                         condition_number=c,impervious_pilot=("impervious" in name)))
    return pd.DataFrame(rows)

def nri_source_inspection(x):
    frame=pd.read_csv(NRI,low_memory=False)
    fields=[c for c in frame.columns if
            any(k in c.upper() for k in ["RISK_SCORE","EAL_SCORE","SOVI_SCORE",
                "RESL_SCORE","BUILDVALUE","RISK_VAL","EAL_VAL"])]
    # Inspection of available original FEMA compound domains, never assert absent fields are verified.
    out={"rows":len(frame),"columns":len(frame.columns),"matched_field_names":fields}
    # NRI_ID often starts with T; TRACTFIPS is numeric when available.
    idcol="TRACTFIPS" if "TRACTFIPS" in frame else "NRI_ID" if "NRI_ID" in frame else None
    if idcol is None:
        out["join_status"]="No row identity for original NRI"
        return out,None
    rawids=frame[idcol].astype(str).str.strip().str.replace(r"\.0$","",regex=True)
    # Pandas may have inferred TRACTFIPS as an integer and dropped its leading zero.
    digits=rawids.str.extract(r"(\d+)$")[0].str.zfill(11)
    ids=digits.str[-11:]
    out["source_id_field"]=idcol
    frame["tract_id"]=ids
    frame=frame.loc[frame.tract_id.isin(set(x.tract_id))].copy()
    out["matched_residential_rows"]=len(frame)
    out["unique_residential_rows"]=frame.tract_id.nunique()
    if len(frame)!=len(x) or frame.tract_id.duplicated().any():
        out["join_status"]="NRI source not unique/complete"
        return out,None
    out["join_status"]="unique_complete_tract_join"
    for left,right in [("NRI_RISK_SCORE","RISK_SCORE"),("NRI_BUILDVALUE","BUILDVALUE"),("SOVI_SCORE","SOVI_SCORE")]:
        if right in frame:
            lookup=x[["tract_id",left]].merge(frame[["tract_id",right]],on="tract_id",validate="one_to_one")
            lhs=pd.to_numeric(lookup[left],errors="coerce")
            rhs=pd.to_numeric(lookup[right],errors="coerce")
            out[f"max_abs_saved_minus_original_{left}"]=float(np.nanmax(np.abs(lhs-rhs)))

    cols=[c for c in fields if c not in ("NRI_ID",)]
    if cols:
        a=x[["tract_id"]].merge(frame[["tract_id"]+cols],on="tract_id",validate="one_to_one")
        for c in cols:
            a[c]=pd.to_numeric(a[c],errors="coerce")
        good=[c for c in cols if a[c].notna().all() and np.isfinite(a[c]).all() and a[c].nunique()>1]
        if len(good)>1:
            components=corr_table(a,good)
            out["usable_nri_columns"]=good
            return out,components
    return out,None

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x=build()
    d=transformed(x)
    allcorr=corr_table(d,REQUIRED)
    allcorr.to_csv(OUT/"all_pair_correlations_transformed.csv",index=False)
    nr=target_associations(d,"NRI_RISK_SCORE",REQUIRED)
    nr.to_csv(OUT/"nri_risk_correlations.csv",index=False)
    hc=target_associations(d,"housing_5plus_share",REQUIRED)
    hc.to_csv(OUT/"housing_configuration_correlations.csv",index=False)
    subset=["Pop_Density","housing_units_per_km2","housing_5plus_share","housing_10plus_share","Pre_1970_Ratio","impervious_land_fraction"]
    corr_table(x,subset).to_csv(OUT/"density_raw_correlations.csv",index=False)
    corrs=corr_table(d,subset)
    corrs.to_csv(OUT/"density_log_correlations.csv",index=False)
    overlap=residual_overlap(d)
    overlap.to_csv(OUT/"conditional_overlap.csv",index=False)
    detail,nrcomp=nri_source_inspection(x)
    (OUT/"nri_original_source_schema.json").write_text(json.dumps(detail,indent=2)+"\n")
    if nrcomp is not None:nrcomp.to_csv(OUT/"nri_source_components.csv",index=False)
    x[["tract_id"]+REQUIRED+["housing_total","ALAND","housing_5plus_share_moe90"]].to_csv(
        OUT/"feature_matrix_audit.csv",index=False)
    info={"base_snapshot":"031d2c675f8e7d58035d27448be040b809ced086",
          "n_tracts":len(x),"input_sha256":{str(f.relative_to(REPO)):digest(f) for f in [FORMAL,ACS,NLCD,NRI]},
          "nri_source":detail,
          "nri_corr":nr[["b","pearson_r","spearman_rho"]].to_dict("records"),
          "housing_corr":hc[["b","pearson_r","spearman_rho"]].to_dict("records"),
          "selected_density_corr":corrs.loc[((corrs.a=="Pop_Density")&(corrs.b=="housing_units_per_km2"))|((corrs.a=="housing_units_per_km2")&(corrs.b=="housing_5plus_share"))].to_dict("records"),
          "conditional":overlap[["model","r2","conditional_vif"]].to_dict("records"),
          "strictly_held_from_admission":"preexisting cluster assignments, historical cluster effect sizes"}
    (OUT/"AUDIT_SUMMARY.json").write_text(json.dumps(info,indent=2,allow_nan=False)+"\n")
    print("FEATURE_AUDIT_BEGIN");print(json.dumps(info,indent=2,allow_nan=False));print("FEATURE_AUDIT_END")
if __name__=="__main__": main()
