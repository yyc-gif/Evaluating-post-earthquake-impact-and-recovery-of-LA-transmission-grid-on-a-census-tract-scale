"""Acquire public tract data/metadata with byte hashes, resumable cached responses and explicit failures."""
from common import *
import requests,re,zipfile,io
import html
def anchors(body):
    return [(html.unescape(url),re.sub('<[^>]+>','',label).strip()) for url,label in re.findall(r'<a\b[^>]*href=["\x27]([^"\x27]+)["\x27][^>]*>(.*?)</a>',body,re.I|re.S)]
SESSION=requests.Session()
SESSION.headers['User-Agent']='LA-grid academic measurement audit; public source verification'
CANOPY='https://services1.arcgis.com/gGHDlz6USftL5Pau/ArcGIS/rest/services/Statistics_by_Census_Tract_wCalES4/FeatureServer'
PARKS='https://la.myneighborhooddata.org/2023/03/parks-access/'
VRE='https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/'
def get(name,url,params=None):
    p=lp(OUT/'sources'/name);p.parent.mkdir(parents=True,exist_ok=True)
    ledger=lp(OUT/'ACQUISITION_RECORDS.json');rows=json.loads(ledger.read_text(encoding='utf-8')) if ledger.exists() else []
    old=next((r for r in rows if r['file']==name and r.get('success')),None)
    if old and p.exists() and sha(p)==old['sha256']:return p
    row=dict(file=name,url=url,params=params,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        r=SESSION.get(url,params=params,timeout=(20,120));row.update(status_code=r.status_code,final_url=r.url,content_type=r.headers.get('Content-Type'),last_modified=r.headers.get('Last-Modified'))
        p.write_bytes(r.content);row.update(bytes=len(r.content),sha256=sha(p));r.raise_for_status();row['success']=True
    except Exception as e:row.update(success=False,error=str(e));log('Source failure '+name+': '+str(e))
    rows.append(row);dump('ACQUISITION_RECORDS.json',rows)
    if not row['success']:return None
    log('Acquired '+name+': '+str(row['bytes'])+' bytes');return p
def js(name,url,params=None):
    p=get(name,url,params)
    try:d=json.loads(p.read_text(encoding='utf-8')) if p else None
    except ValueError:
        log('No JSON payload '+name);return None
    if d and 'error' in d:log('API error '+name+': '+str(d['error']));return None
    return d
def initial():
    if not lp(OUT/'PRESERVATION_BEFORE.json').exists():dump('PRESERVATION_BEFORE.json',snapshot())
    dump('MEASUREMENT_AUDIT_SPECIFICATION.json',dict(baseline=BASELINE,no_clustering=True,no_weight_optimization=True,no_cluster_outcome_admission=True,cohorts=[2315,2291,2287],uncertainty_diagnostic_flags={'MOE90_gt_0.05':'more than 5 percentage points','MOE90_gt_0.10':'more than 10 percentage points','CV_gt_0.30':'relative standard error greater than 30%, positive estimates only'},flags_are_not_exclusion_rules=True,correlation_samples='reference2287, pairwise exact intersection with stored GEOID hashes/lists; identical complete-data subset sensitivity',new_physical_sampling=False))
def canopy():
    meta=js('CANOPY_SERVICE.json',CANOPY,{'f':'pjson'});js('CANOPY_LAYER.json',CANOPY+'/0',{'f':'pjson'})
    if meta and meta.get('serviceItemId'):
        item=meta['serviceItemId'];js('CANOPY_ITEM.json','https://www.arcgis.com/sharing/rest/content/items/'+item,{'f':'pjson'});get('CANOPY_ITEM_METADATA.xml','https://www.arcgis.com/sharing/rest/content/items/'+item+'/info/metadata/metadata.xml')
    count=js('CANOPY_LA_COUNT.json',CANOPY+'/0/query',{'where':"STCOFIPS='06037'",'returnCountOnly':'true','f':'json'})
    if count:
        for offset in range(0,count['count'],1000):js('CANOPY_LA_'+str(offset)+'.geojson',CANOPY+'/0/query',{'where':"STCOFIPS='06037'",'outFields':'*','returnGeometry':'true','outSR':4326,'orderByFields':'OBJECTID','resultOffset':offset,'resultRecordCount':1000,'f':'geojson'})
    get('CANOPY_RASTER_SERVICE.json','https://tiles.arcgis.com/tiles/gGHDlz6USftL5Pau/arcgis/rest/services/UrbanTreeCanopy_CA2022/MapServer',{'f':'pjson'})
def parks():
    p=get('PARKS_DOCUMENTATION.html',PARKS)
    if p:
        links=[u for u,t in anchors(p.read_text(encoding='utf-8')) if 'Download the Dataset' in t]
        dump('PARKS_DOWNLOAD_LINKS.json',links)
        for i,url in enumerate(dict.fromkeys(links)):get('PARKS_DOWNLOAD_'+str(i)+'.payload',url)
def acs():
    get('ACS_B25040_LA.json','https://api.census.gov/data/2022/acs/acs5',{'get':'NAME,B25040_001E,B25040_001M,B25040_004E,B25040_004M','for':'tract:*','in':'state:06 county:037'})
    get('ACS_B25040_GROUP.json','https://api.census.gov/data/2022/acs/acs5/groups/B25040.json')
    p=get('ACS_VRE_140_INDEX.html',VRE+'data/5-year/140/')
    if p:
        found=[u for u,t in anchors(p.read_text(encoding='utf-8')) if u=='B25040_06.csv.zip'];dump('B25040_VRE_AVAILABILITY.json',dict(directory=VRE+'data/5-year/140/',exact_file_present=bool(found)))
        if found:get('B25040_06.csv.zip',VRE+'data/5-year/140/'+found[0])
    get('ACS_VRE_DOCUMENTATION.pdf',VRE+'documentation/5-year/2018-2022_Variance_Replicate_Table_Documentation.pdf')
def supporting():
    js('CANOPY_RELATED_ITEMS.json','https://www.arcgis.com/sharing/rest/search',{'q':'orgid:gGHDlz6USftL5Pau ("urban canopy" OR "UrbanTreeCanopy" OR "Urban Areas")','num':100,'f':'json'})
    get('PARKS_COUNTY_HOME.html','https://lacountyparkneeds.org/pnaplus-home/')
    get('PARKS_API_METADATA.payload','https://usc-ndsc-apim-prod.azure-api.net/map/api/datasets/59')
    get('CANOPY_CALFIRE_LAUNCH.pdf','https://cdnverify.bof.fire.ca.gov/media/xs2oiyts/full-8-may-2025-director-s-report.pdf')
    # A 200 HTTP status can still be an unavailable API data response.
    p=lp(OUT/'sources/ACS_B25040_LA.json')
    if p.exists():
        try:json.loads(p.read_text(encoding='utf-8'))
        except ValueError:dump('ACS_API_SEMANTIC_FAILURE.json',dict(file=p.name,http_status=200,reason='Census API redirected to Missing Key HTML, not estimates JSON',replacement='Official 2022 California tract B25040 variance-replicate archive includes the original ESTIMATE, MOE and all 80 replicates; no API authentication bypass attempted'))
if __name__=='__main__':initial();canopy();parks();acs()
