"""Small authoritative-source probes, no invented tract-level coverage or raster values."""
from pathlib import Path
import json,requests,time
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"
SOURCES={
"SCAG_ALU_2019_legacy":"https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0",
"SCAG_ALU_2019_NAD83":"https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use_NAD83/MapServer/0",
"SCAG_LDX_2024_LA":"https://maps.scag.ca.gov/scaggis/rest/services/LDX/Existinglanduse_poly_LA/MapServer/0",
"LACOUNTY_ASSESSOR_2021_ROLL":"https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2021_Table/FeatureServer/0",
"LARIAC4_2014_BUILDING_OUTLINES":"https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1",
"EPA_SLD_2021":"https://services1.arcgis.com/IqEe3YDHhqT8n4KU/ArcGIS/rest/services/EPA_SmartLocationDatabase_V3_Jan_2021_Final/FeatureServer/0",
}
KEYS={"GEOID20","LU19","LU24","STACK","ACRES","BF_SQFT","YEAR","YEARBUILT","YearBuilt","Year_Built","Property Use Code","Property Use Type","HEIGHT","LARIAC_BUILDINGS_2014_AREA","BLD_ID","Number of Buildings"}
def fetch(url,params):
    try:
        r=requests.get(url,params=params,timeout=25,headers={"User-Agent":"Stage7-Research-Audit/1.0"})
        d=r.json()
        if "error" in d:return {"ok":False,"status":r.status_code,"error":d["error"]}
        return {"ok":True,"status":r.status_code,"data":d}
    except Exception as e:return {"ok":False,"error":str(e)[:260]}
def run():
    OUT.mkdir(exist_ok=True,parents=True)
    result={}
    for name,base in SOURCES.items():
        r=fetch(base,{"f":"json"})
        item={"source":base,"ok":r["ok"],"status":r.get("status"),"error":r.get("error")}
        if r["ok"]:
            d=r["data"];fields=d.get("fields",[])
            names=[f.get("name") for f in fields]
            item.update(name=d.get("name"),rows_declared=d.get("recordCount"),
                        max_record_count=d.get("maxRecordCount"),
                        all_field_names=names,
                        likely_relevant_fields=[f for f in names if any(k.lower() in f.lower() for k in ["geoid","lu19","lu24","stack","acres","footprint","height","year","built","use","code","area","ain","apn","sqft"])])
            where="COUNTY_ID='037'" if "SCAG" in name else "1=1"
            query=fetch(base+"/query",{"f":"json","where":where,
                 "returnCountOnly":"true"})
            item["query_count_status"]={"ok":query["ok"],"status":query.get("status"),"error":query.get("error")}
            if query["ok"]:item["query_count"]=query["data"].get("count")
            if "SCAG_ALU_2019" in name:
                q=fetch(base+"/query",{"f":"json","where":"COUNTY_ID='037'",
                       "outFields":"GEOID20,LU19,STACK,ACRES,APN19,BF_SQFT","returnGeometry":"false",
                       "resultRecordCount":4})
                item["sample_query_ok"]=q["ok"]
                item["sample_query_error"]=q.get("error")
                if q["ok"]:item["sample_rows"]=[f.get("attributes",{}) for f in q["data"].get("features",[])]
        result[name]=item
    (OUT/"SOURCE_SERVICE_PROBES.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("PROBES_BEGIN")
    print(json.dumps({n:{"ok":v["ok"],"nfields":len(v.get("all_field_names",[])),
                         "query_count":v.get("query_count"),"sample":v.get("sample_rows",[])[:2],
                         "error":v.get("error")} for n,v in result.items()},indent=2))
    print("PROBES_END")
if __name__=="__main__":run()
