"""Bounded official-source snapshots, with request identities and hashes."""
import argparse
from html.parser import HTMLParser
import time
from urllib.parse import urljoin
import requests
import geopandas as gpd
from common import *

S=OUT/'sources'
RECORDS=[]


def fetch(name,url,params=None):
    p=lp(S/name);p.parent.mkdir(parents=True,exist_ok=True)
    request=dict(name=name,url=url,params=params or {})
    if p.exists():
        old=json.loads(lp(OUT/'OFFICIAL_SOURCE_ACQUISITION.json').read_text())
        entry=next(x for x in old if x['name']==name and x.get('status')=='ACQUIRED')
        assert entry['url']==url and entry['params']==request['params'] and sha(p)==entry['sha256']
        if entry not in RECORDS:RECORDS.append(entry)
        return p
    for attempt in range(3):
        try:
            r=requests.get(url,params=params,timeout=(20,180));r.raise_for_status()
            data=r.content
            if params and params.get('f') in ['json','pjson','geojson']:
                j=r.json()
                if 'error' in j:raise ValueError(j['error'])
            p.write_bytes(data)
            entry={**request,'status':'ACQUIRED','sha256':sha(p),'bytes':len(data),
                'client_access_date':'2026-10-12','response_last_modified':r.headers.get('Last-Modified'),
                'resolved_url':r.url}
            RECORDS.append(entry);dump('OFFICIAL_SOURCE_ACQUISITION.json',RECORDS)
            return p
        except Exception as e:
            if attempt<2:time.sleep(2**attempt)
            else:
                RECORDS.append({**request,'status':'UNAVAILABLE','error':str(e)})
                dump('OFFICIAL_SOURCE_ACQUISITION.json',RECORDS)
                raise


def api(name,url,params=None):
    return json.loads(fetch(name,url,params or {'f':'pjson'}).read_text())


def features(name,url,bounds,fields='*',where='1=1'):
    meta=api(name+'_METADATA.json',url)
    query=dict(f='json',geometry=','.join(map(str,bounds)),geometryType='esriGeometryEnvelope',
        inSR=4326,spatialRel='esriSpatialRelIntersects',where=where,returnIdsOnly='true')
    ids=api(name+'_IDS.json',url+'/query',query)
    oid=ids['objectIdFieldName'];expected=sorted(ids.get('objectIds') or [])
    out=[]
    for i in range(0,len(expected),100):
        filename=name+f'_PART_{i//100:03d}.geojson'
        step=100 if lp(S/filename).exists() or name!='NFHL_ZONES' else 10
        for sub in range(i,min(i+100,len(expected)),step):
            partname=filename if step==100 else name+f'_SMALLPART_{sub:05d}.geojson'
            j=api(partname,url+'/query',
                dict(f='geojson',objectIds=','.join(map(str,expected[sub:min(sub+step,i+100)])),outFields=fields,
                    outSR=4326,returnGeometry='true'))
            assert not j.get('exceededTransferLimit',False)
            out.extend(j['features'])
        print(name,'features',len(out),'/',len(expected),flush=True)
    actual=sorted(int(v['properties'][oid]) for v in out)
    assert actual==expected and len(actual)==len(set(actual))
    dump('sources/'+name+'_COMPLETE.geojson',dict(type='FeatureCollection',features=out))
    dump('sources/'+name+'_QUERY_QA.json',dict(url=url,bounds_4326=bounds,where=where,
        expected_features=len(expected),retrieved_features=len(out),id_field=oid,exact_ID_match=True,
        spatial_reference=meta.get('extent',{}).get('spatialReference')))


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href')
            if href:self.links.append(href)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['metadata','geometry','heat'],default='metadata');args=parser.parse_args()
    global RECORDS
    if lp(OUT/'OFFICIAL_SOURCE_ACQUISITION.json').exists():RECORDS=json.loads(lp(OUT/'OFFICIAL_SOURCE_ACQUISITION.json').read_text())
    s=sources();full,d=dataset(s)
    for ext in ['shp','shx','dbf','prj']:s.source('Data/LA_Tracts_With_Population.'+ext,AUTH)
    g=gpd.read_file(s.source('Data/LA_Tracts_With_Population.shp',AUTH));g['tract_id']=g.GEOID.astype(str)
    g=g.set_index('tract_id').reindex(full.index).to_crs(4326)
    assert g.geometry.notna().all() and len(g)==2315
    bounds=(g.total_bounds+np.array([-.01,-.01,.01,.01])).tolist()
    if args.phase=='metadata':
        for name,url in [
            ('CALFIRE_LRA_ITEM.json','https://www.arcgis.com/sharing/rest/content/items/018035e18cdc4778afcbe06185c01426'),
            ('CALFIRE_SRA_ITEM.json','https://www.arcgis.com/sharing/rest/content/items/6000aebca6f24b3892ecb01b598f7545'),
            ('CALFIRE_LRA_METADATA.json','https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0'),
            ('CALFIRE_SRA_METADATA.json','https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSZSRA_23_3/FeatureServer/0'),
            ('CALFIRE_RESPONSIBILITY_METADATA.json','https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/State_Responsibility_Area/FeatureServer/0'),
            ('NFHL_ZONES_METADATA.json','https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28'),
            ('NFHL_AVAILABILITY_METADATA.json','https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/0'),
            ('CDC_HEAT_MAP_METADATA.json','https://onemap.cdc.gov/onemapservices/rest/services/EJI/CBM_Heat_ExtremeHeatDays_2024/MapServer/0')]:
            j=api(name,url);print(name,[(v['name'],v.get('alias')) for v in j.get('fields',[])][:8],flush=True)
        for name,url in [
            ('CDC_EJI_DATA_DOWNLOAD.html','https://www.atsdr.cdc.gov/place-health/php/eji/eji-data-download.html'),
            ('CDC_EJI_CLIMATE_INDICATORS.html','https://www.atsdr.cdc.gov/place-health/php/eji/eji-indicators-climate-burden-module.html'),
            ('CDC_EJI_TECHNICAL.pdf','https://www.atsdr.cdc.gov/place-health/media/pdfs/2024/10/EJI_2024_Technical_Documentation.pdf'),
            ('CALFIRE_FHSZ.html','https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones'),
            ('NFHL_SERVICE_DESCRIPTION.html','https://www.fema.gov/flood-maps/national-flood-hazard-layer'),
            ('CDPH_PROJECTED_HEAT.html','https://www.cdph.ca.gov/Programs/OHE/Pages/Climate-Health-Equity/Health-Vulnerability-Indicators-Narratives/Extreme-Heat-Days.aspx')]:
            try:
                p=fetch(name,url)
                if name.endswith('.html'):
                    links=Links();links.feed(p.read_text(encoding='utf-8',errors='replace'))
                    useful=[urljoin(url,u) for u in links.links if any(v in u.lower() for v in ['csv','zip','xlsx','dictionary','faq','technical','data-download'])]
                    dump('sources/'+name.replace('.html','_LINKS.json'),useful);print(name,useful[:20],flush=True)
            except Exception as e:print('DOCUMENT_UNAVAILABLE',name,str(e),flush=True)
    if args.phase=='geometry':
        for name,url in [
            ('CALFIRE_LRA','https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSALRA25_v1_All/FeatureServer/0'),
            ('CALFIRE_SRA','https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/FHSZSRA_23_3/FeatureServer/0'),
            ('CALFIRE_RESPONSIBILITY','https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/State_Responsibility_Area/FeatureServer/0'),
            ('NFHL_ZONES','https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28'),
            ('NFHL_AVAILABILITY','https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/0')]:
            for attempt in range(3):
                try:
                    features(name,url,bounds);break
                except Exception as e:
                    print('LAYER_UNAVAILABLE',name,'pass',attempt+1,str(e),flush=True)
                    if attempt<2:time.sleep(15)
    if args.phase=='heat':
        url='https://onemap.cdc.gov/onemapservices/rest/services/EJI/EJI_2024_Data_Service/MapServer/0'
        meta=api('CDC_EJI_RAW_METADATA.json',url)
        where="STATEFP='06' AND COUNTYFP='037'"
        ids=api('CDC_EJI_HEAT_IDS.json',url+'/query',dict(f='json',where=where,returnIdsOnly='true'))
        expected=sorted(ids['objectIds']);oid=ids['objectIdFieldName'];rows=[]
        names=[x['name'] for x in meta['fields']]
        fields=[oid,'GEOID','GEOID_2020','E_NEHD','EPL_NEHD']
        fields += [n for n in names if n.startswith('F_') and 'NEHD' in n]
        for i in range(0,len(expected),100):
            j=api(f'CDC_EJI_HEAT_PART_{i//100:03d}.json',url+'/query',dict(f='json',
                objectIds=','.join(map(str,expected[i:i+100])),outFields=','.join(fields),returnGeometry='false'))
            assert not j.get('exceededTransferLimit',False)
            rows.extend(x['attributes'] for x in j['features'])
        assert sorted(x[oid] for x in rows)==expected
        save('sources/CDC_EJI_HEAT_RAW_LA.csv',rows)
        dump('sources/CDC_EJI_HEAT_QUERY_QA.json',dict(url=url,where=where,fields=fields,
            expected_features=len(expected),retrieved_features=len(rows),exact_ID_match=True,
            heat_missingness_flag_available=any(n.startswith('F_') and 'NEHD' in n for n in names)))
    save('SCIENTIFIC_INPUT_HASHES_ACQUISITION.csv',s.records)
    unique={json.dumps([x['name'],x.get('status'),x.get('params',{})],sort_keys=True):x for x in RECORDS}
    dump('OFFICIAL_SOURCE_ACQUISITION.json',list(unique.values()))


if __name__=='__main__':main()
