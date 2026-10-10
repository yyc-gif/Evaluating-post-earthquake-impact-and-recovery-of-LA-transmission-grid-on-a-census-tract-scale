"""Independent Census VRE-to-Stage7 source QA (independent from validation/validate.py)."""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from dbfread import DBF

REPO=Path(__file__).resolve().parents[4]
ROOT=Path(__file__).resolve().parent
V=REPO/"docs/data_research/built_environment_20261009/validation"
OUT=ROOT/"results"
R=[f"Var_Rep{i}" for i in range(1,81)]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def vre(table,orders):
    path=V/f"sources/{table}_06.csv.zip"
    with zipfile.ZipFile(path) as z:
        csv=z.namelist()[0]
        a=pd.read_csv(z.open(csv),dtype={"GEOID":str})
    a=a.loc[a.GEOID.str.startswith("1400000US06037",na=False)].copy()
    a["tract_id"]=a.GEOID.str[-11:]
    a["ORDER"]=a.ORDER.astype(int)
    a=a.loc[a.ORDER.isin([1,*orders])].copy()
    if a.duplicated(["tract_id","ORDER"]).any():raise ValueError("Duplicated VRE cells")
    denom=a.loc[a.ORDER.eq(1)].set_index("tract_id").sort_index()
    numerator=a.loc[a.ORDER.isin(orders)].groupby("tract_id")[["ESTIMATE",*R]].sum().sort_index()
    if not numerator.index.equals(denom.index):raise ValueError("Unaligned Census records")
    n=numerator.ESTIMATE.to_numpy(float)
    d=denom.ESTIMATE.to_numpy(float)
    value=np.divide(n,d,out=np.full_like(d,np.nan,dtype=float),where=d>0)
    numer_reps=numerator[R].to_numpy(float)
    denom_reps=denom[R].to_numpy(float)
    repl=np.divide(numer_reps,denom_reps,out=np.zeros_like(numer_reps),where=denom_reps!=0)
    se=np.sqrt((4/80)*np.sum((repl-value[:,None])**2,axis=1))
    boundary=((value==0)|(value==1)|(se==0))&(d>0)
    avg=16.
    pseudo=np.minimum(.5,np.divide(2.3*avg,d,out=np.zeros_like(d),where=d>0))
    boundary_se=np.sqrt(pseudo*(1-pseudo)*np.divide(avg,d,out=np.zeros_like(d),where=d>0))
    se=np.where(boundary,boundary_se,se)
    return pd.DataFrame({"tract_id":denom.index,"estimate":value,"moe90":se*1.645,
                         "total":d,"boundary":boundary})
def main():
    OUT.mkdir(exist_ok=True,parents=True)
    manifest=json.loads((V/"PACKAGE_MANIFEST.json").read_text())
    targets=["sources/B25024_06.csv.zip","sources/B25034_06.csv.zip",
             "ACS_TRACT_VALIDATION.csv","NLCD_TRACT_EXTRACTION.csv"]
    actual={}
    for x in targets:
        p=V/x
        h=sha(p)
        if h!=manifest["members"][x]["sha256"]:raise ValueError(f"Official retained input hash mismatch: {x}")
        actual[x]=h
    orig=pd.read_csv(REPO/"Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv",dtype={"tract_id":str})
    orig["tract_id"]=orig.tract_id.str.zfill(11)
    old=pd.read_csv(V/"ACS_TRACT_VALIDATION.csv",dtype={"tract_id":str})
    old["tract_id"]=old.tract_id.str.zfill(11)
    original_area_file=REPO/"Data/LA_Tracts_With_Population.dbf"
    expected_area=json.loads((V/"INPUT_FILE_MANIFEST.json").read_text())["Data/LA_Tracts_With_Population.dbf"]
    if sha(original_area_file)!=expected_area:
        raise AssertionError("Archived Census area DBF hash mismatch")
    geom=pd.DataFrame(iter(DBF(str(original_area_file),encoding="latin-1",char_decode_errors="ignore")))
    if not {"GEOID","ALAND"}.issubset(geom.columns):
        raise ValueError("Source DBF missing GEOID/ALAND")
    geom["tract_id"]=geom["GEOID"].astype(str).str.zfill(11)
    land=pd.read_csv(V/"NLCD_TRACT_EXTRACTION.csv",dtype={"tract_id":str})
    land["tract_id"]=land.tract_id.str.zfill(11)
    target=land.merge(geom[["tract_id","ALAND"]],on="tract_id",how="left",validate="one_to_one",suffixes=("_validated","_original"))
    if len(target)!=2315:raise ValueError("Land area domain mismatch")
    maxland=float(np.abs(target.ALAND_validated.astype(float)-target.ALAND_original.astype(float)).max())
    if not np.isfinite(maxland) or maxland>0:raise AssertionError("ALAND source mismatch")
    config=vre("B25024",[6,7,8,9]).set_index("tract_id").loc[orig.tract_id]
    ages=vre("B25034",[8,9,10,11]).set_index("tract_id").loc[orig.tract_id]
    from_old=old.set_index("tract_id").loc[orig.tract_id]
    val=np.asarray(config.estimate)
    oldval=np.asarray(from_old.housing_5plus_share)
    err=np.max(np.abs(val-oldval))
    moerr=np.max(np.abs(np.asarray(config.moe90)-np.asarray(from_old.housing_5plus_share_moe90)))
    ageerr=np.max(np.abs(np.asarray(ages.estimate)-np.asarray(orig.Pre_1970_Ratio)))
    if not np.isfinite([err,moerr,ageerr]).all() or err>1e-12 or moerr>1e-10 or ageerr>1e-12:
        raise AssertionError(f"Source QA discrepancy: {err}, {moerr}, {ageerr}")
    result={"n_recomputed":len(val),
            "max_abs_config_share_difference":float(err),
            "max_abs_config_moe90_difference":float(moerr),
            "max_abs_pre1970_share_difference":float(ageerr),
            "recomputed_moe_gt10pp":int(np.sum(np.asarray(config.moe90)>.1)),
            "boundary_model_n":int(config.boundary.sum()),
            "recomputed_median_moe_pp":float(np.median(config.moe90)*100),
            "max_abs_aland_source_difference_m2":maxland,
            "n_area_records_checked":len(target),
            "source_hashes":actual,
            "readme":"Recomputed from archived original California ACS B25024/B25034 2018-2022 Census 80 replicate ZIPs. This does not independently certify impervious rasters."}
    if result["recomputed_moe_gt10pp"]!=211 or result["boundary_model_n"]!=158:raise AssertionError("ACS VRE discrepancy")
    result["source_hashes"]["Data/LA_Tracts_With_Population.dbf"]=expected_area
    (OUT/"SOURCE_QA.json").write_text(json.dumps(result,indent=2)+"\n")
    print("SOURCE_QA",json.dumps({k:v for k,v in result.items() if k!="source_hashes"}))
if __name__=="__main__":main()
