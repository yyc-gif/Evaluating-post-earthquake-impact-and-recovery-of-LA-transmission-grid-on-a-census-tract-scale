"""Compare FEMA NRI overall multi-hazard risk with earthquake-specific scores on same tracts."""
import json
import numpy as np
import pandas as pd
from scipy.stats import pearsonr,spearmanr
from feature_audit import build,NRI,ROOT,OUT

FIELDSET=["RISK_SCORE","EAL_SCORE","SOVI_SCORE","RESL_SCORE","BUILDVALUE",
          "ERQK_RISKS","ERQK_EALS","ERQK_EALT","ERQK_RISKV"]
def normalize(n):
    x=n.astype(str).str.strip().str.replace(r"\.0$","",regex=True)
    return x.str.extract(r"(\d+)$")[0].str.zfill(11).str[-11:]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    x=build()
    df=pd.read_csv(NRI,low_memory=False)
    idcol="TRACTFIPS" if "TRACTFIPS" in df else "NRI_ID"
    df["tract_id"]=normalize(df[idcol])
    fields=[f for f in FIELDSET if f in df]
    df=df.loc[df.tract_id.isin(set(x.tract_id)),["tract_id"]+fields].copy()
    if len(df)!=len(x) or df.tract_id.duplicated().any():raise RuntimeError("FEMA original tract identities not unique and complete")
    df=df.rename(columns={c:"original_"+c for c in fields})
    out=x.merge(df,on="tract_id",validate="one_to_one")
    if "original_ERQK_RISKS" not in out:raise RuntimeError("No earthquake-specific score in retained FEMA source")
    for name in fields:
        out["original_"+name]=pd.to_numeric(out["original_"+name],errors="coerce")
    out["log_housing_unit_density"]=np.log1p(out.housing_units_per_km2)
    out["log_population_density"]=np.log1p(out.Pop_Density)
    out["log_building_value"]=np.log1p(out.NRI_BUILDVALUE)
    comparisons=[
      "NRI_RISK_SCORE","original_EAL_SCORE","original_SOVI_SCORE","original_RESL_SCORE",
      "log_building_value","T80","Init_Supply","Pre_1970_Ratio","housing_5plus_share",
      "log_housing_unit_density","log_population_density","impervious_land_fraction"]
    rows=[]
    for candidate in comparisons:
        if candidate not in out:continue
        for target in ["original_ERQK_RISKS","NRI_RISK_SCORE","original_ERQK_EALS"]:
            if target not in out or candidate==target:continue
            valid=out[[target,candidate]].dropna()
            if len(valid)<2 or valid[target].nunique()<=1 or valid[candidate].nunique()<=1:continue
            rows.append(dict(target=target,compare=candidate,n=len(valid),
                pearson_r=float(pearsonr(valid[target],valid[candidate]).statistic),
                spearman_rho=float(spearmanr(valid[target],valid[candidate]).statistic)))
    table=pd.DataFrame(rows)
    table.to_csv(OUT/"QUAKE_RISK_CORRELATIONS.csv",index=False)
    delta={}
    for left,right in [("NRI_RISK_SCORE","RISK_SCORE"),("NRI_BUILDVALUE","BUILDVALUE"),("SOVI_SCORE","SOVI_SCORE")]:
        if "original_"+right in out:
            diff=np.abs(out[left]-out["original_"+right])
            delta[left]=dict(n_compared=int(diff.notna().sum()),max_abs_diff=float(diff.max()))
    meta={"n":len(out),"fields_present":fields,"n_earthquake_risk_nonmissing":int(out.original_ERQK_RISKS.notna().sum()),
          "n_earthquake_eal_nonmissing":int(out.original_ERQK_EALS.notna().sum()) if "original_ERQK_EALS" in out else 0,
          "mean_earthquake_risk":float(out.original_ERQK_RISKS.mean()),
          "original_vs_saved":delta,
          "note":"FEMA overall RISK_SCORE mixes 18 natural hazards; ERQK_RISKS is earthquake-specific; neither directly models this scenario's grid damage"}
    (OUT/"QUAKE_AUDIT.json").write_text(json.dumps(meta,indent=2)+"\n")
    out[["tract_id"]+[c for c in out if c.startswith("original_ERQK")]].to_csv(OUT/"NRI_QUAKE_ORIGINAL_TRACTS.csv",index=False)
    print("QUAKE_AUDIT_BEGIN");print(json.dumps({"meta":meta,"pairs":table.loc[table.target.eq("original_ERQK_RISKS")].to_dict("records")},indent=2));print("QUAKE_AUDIT_END")
if __name__=="__main__":main()
