"""Bounded official metadata verification; no source payload downloads."""
from common import *
import requests

URLS={
 'LARIAC4_layer':'https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1?f=pjson',
 'EMC_product':'https://human-settlement.emergency.copernicus.eu/emc_built_s.php'
}

if __name__=='__main__':
    folder=lp(OUT/'source_evidence');folder.mkdir(exist_ok=True);rows=[]
    # Use actual layer item ID when provided; do not infer a dataset from an invented ID.
    for key,url in list(URLS.items()):
        p=folder/(key+'.txt')
        try:
            if not p.exists():
                r=requests.get(url,timeout=(10,30));r.raise_for_status();p.write_bytes(r.content)
            data=p.read_bytes();j=json.loads(data) if key=='LARIAC4_layer' else None
            if j and 'error' in j:raise RuntimeError(j['error'])
            rows.append(dict(source=key,url=url,bytes=len(data),sha256=sha(p),description=j.get('description') if j else None,fields=[(x['name'],x.get('alias')) for x in j.get('fields',[])] if j else None,item_id=j.get('serviceItemId') if j else None,status='ACTUAL_OFFICIAL_METADATA'))
            if j and j.get('serviceItemId'):
                itemurl='https://www.arcgis.com/sharing/rest/content/items/'+j['serviceItemId']+'?f=json';q=folder/'LARIAC4_actual_item.json'
                if not q.exists():rr=requests.get(itemurl,timeout=(10,30));rr.raise_for_status();q.write_bytes(rr.content)
                item=json.loads(q.read_text(encoding='utf-8'));rows.append(dict(source='LARIAC4_actual_item',url=itemurl,sha256=sha(q),bytes=q.stat().st_size,status='ACTUAL_ITEM_FOR_LAYER',description=item.get('description')))
        except Exception as e:rows.append(dict(source=key,url=url,status='METADATA_ROUTE_FAILED',error=str(e)))
    dump('OFFICIAL_LINEAGE_VERIFICATION.json',rows)
    for r in rows:print(r['source'],r['status'],(r.get('description') or '')[:800],flush=True)
