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
"LARIAC6_2020_BUILDING_OUTLINES":"https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines_%282020%29/FeatureServer/0",
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
    # Source-specific schema and coverage questions, not full spatial overlay.
    for name,base in SOURCES.items():
        extra=[]
        if "SCAG_ALU_2019" in name:
            extra=[("stacked_count","COUNTY_ID='037' AND STACK>1"),
                   ("geoid_missing","COUNTY_ID='037' AND GEOID20 IS NULL"),
                   ("unknown_use","COUNTY_ID='037' AND LU19 IN ('9999','7777')")]
        elif name=="LARIAC4_2014_BUILDING_OUTLINES":
            extra=[("yearbuilt_valid","YearBuilt1>=1800 AND YearBuilt1<=2014"),
                   ("yearbuilt_null","YearBuilt1 IS NULL"),
                   ("yearbuilt_0","YearBuilt1=0")]
            q=fetch(base+"/query",{"f":"json","where":"1=1","outFields":"YearBuilt1,UseType,UseCode,HEIGHT,AIN,APN",
                    "returnGeometry":"false","resultRecordCount":5})
            result[name]["sample_query_ok"]=q["ok"]
            if q["ok"]:result[name]["sample_rows"]=[p.get("attributes",{}) for p in q["data"].get("features",[])]
        for metric,where in extra:
            q=fetch(base+"/query",{"f":"json","where":where,"returnCountOnly":"true"})
            result[name][metric+"_query_ok"]=q["ok"]
            if q["ok"]:result[name][metric]=q["data"].get("count")
            else:result[name][metric+"_error"]=q.get("error")
    def group_counts(base, field, where):
        q=fetch(base+"/query",{"f":"json","where":where,"returnGeometry":"false",
            "groupByFieldsForStatistics":field,
            "outStatistics":json.dumps([{"statisticType":"count",
                "onStatisticField":"OBJECTID","outStatisticFieldName":"n"}])})
        if not q["ok"]:return {"ok":False,"error":q.get("error")}
        return {"ok":True,"values":[v.get("attributes",{}) for v in q["data"].get("features",[])],
                "transfer_limit":q["data"].get("exceededTransferLimit",False)}
    base=SOURCES["LARIAC4_2014_BUILDING_OUTLINES"]
    result["LARIAC4_2014_BUILDING_OUTLINES"]["use_type_totals"]=group_counts(base,"UseType","1=1")
    result["LARIAC4_2014_BUILDING_OUTLINES"]["use_type_valid_age"]=group_counts(
        base,"UseType","YearBuilt1>=1800 AND YearBuilt1<=2014")
    result["SCAG_ALU_2019_legacy"]["land_use_class_counts"]=group_counts(
        SOURCES["SCAG_ALU_2019_legacy"],"LU19_CLASS","COUNTY_ID='037'")
    result["LACOUNTY_ASSESSOR_2021_ROLL"]["roll_year_counts"]=group_counts(
        SOURCES["LACOUNTY_ASSESSOR_2021_ROLL"],"RollYear","1=1")
    lariac_item_url="https://www.arcgis.com/sharing/rest/content/items/e6a1e375e12a4fe6849d896a26ec028a"
    z=fetch(lariac_item_url,{"f":"json"})
    result["LARIAC6_2020_ITEM"]={"ok":z["ok"],"url":lariac_item_url,
        "item_type":z.get("data",{}).get("type"),"service_url":z.get("data",{}).get("url"),
        "access":z.get("data",{}).get("access"),"error":z.get("error")}
    (OUT/"SOURCE_SERVICE_PROBES.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("PROBES_BEGIN")
    print(json.dumps({n:{"ok":v["ok"],"nfields":len(v.get("all_field_names",[])),
                         "query_count":v.get("query_count"),"sample":v.get("sample_rows",[])[:2],
                         "error":v.get("error")} for n,v in result.items()},indent=2))
    print("PROBES_END")
if __name__=="__main__":run()
