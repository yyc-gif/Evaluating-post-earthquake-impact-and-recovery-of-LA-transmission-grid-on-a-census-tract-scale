"""Complete resumable LA ALU20 acquisition; no model fitting."""
from common import *
import requests, gzip, shutil, time
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = 'https://rdp.scag.ca.gov/mapping/rest/services/Housing/2020_Annual_Land_Use/MapServer/0'
CACHE = RAW/'scag2020_chunks'
CACHE.mkdir(exist_ok=True)
FIELDS = ['OBJECTID','PID20','APN20','APN20_P','STACK','APN_DUP','ALU20',
          'ALU20_SRC','BF_SQFT','ACRES','GEOID20','YEAR']

def query(params):
    for attempt in range(4):
        try:
            r=requests.post(URL+'/query',data={'f':'json',**params},timeout=(15,90))
            r.raise_for_status(); j=r.json()
            if 'error' in j: raise RuntimeError(j['error'])
            return r,j
        except Exception:
            if attempt==3: raise
            time.sleep(2**attempt)

def main():
    metadata=OUT/'source_evidence/SCAG2020_layer_current.json'
    if not metadata.exists():
        r=requests.get(URL,params={'f':'pjson'},timeout=(15,90));r.raise_for_status()
        metadata.write_bytes(r.content)
    if (OUT/'SCAG2020_ACQUISITION_COMPLETE.json').exists():
        prior=json.loads((OUT/'SCAG2020_ACQUISITION_COMPLETE.json').read_text(encoding='utf-8'))
        assert sha(metadata)==prior['metadata_sha256']
    for name,params in [('SCAG2020_count.json',{'returnCountOnly':'true'}),
                        ('SCAG2020_ids_probe.json',{'returnIdsOnly':'true'})]:
        if not (RAW/name).exists():
            response,j=query({'where':"COUNTY = 'Los Angeles'",**params})
            (RAW/name).write_bytes(response.content)
    count=json.loads((RAW/'SCAG2020_count.json').read_text(encoding='utf-8'))['count']
    data=json.loads((RAW/'SCAG2020_ids_probe.json').read_text(encoding='utf-8'))
    ids=sorted(data['objectIds'])
    assert len(ids)==len(set(ids))==count and not data.get('exceededTransferLimit',False)
    _,live=query({'where':"COUNTY = 'Los Angeles'",'returnCountOnly':'true'})
    assert live['count']==count
    n=(len(ids)+1999)//2000
    def one(k):
        selected=ids[k*2000:(k+1)*2000]; p=CACHE/f'{k:04d}.json.gz'
        if p.exists():
            with gzip.open(p,'rb') as f: raw=f.read()
            reused=True
        else:
            assert shutil.disk_usage(str(CACHE).removeprefix('\\\\?\\')).free>1_000_000_000
            r,j=query({'objectIds':','.join(map(str,selected)),
                       'outFields':','.join(FIELDS),'returnGeometry':'true','outSR':3310})
            raw=r.content
            with gzip.open(p,'wb',compresslevel=3) as f:f.write(raw)
            reused=False
        j=json.loads(raw); actual=[x['attributes']['OBJECTID'] for x in j['features']]
        assert len(actual)==len(set(actual))==len(selected) and set(actual)==set(selected)
        assert not j.get('exceededTransferLimit',False)
        return {'chunk':k,'count':len(actual),'response_sha256':hashlib.sha256(raw).hexdigest(),
                'gzip_sha256':sha(p),'response_bytes':len(raw),'gzip_bytes':p.stat().st_size,
                'reused':reused}
    records=[];start=time.time()
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(one,k) for k in range(n)]
        for f in as_completed(futures):
            records.append(f.result())
            if len(records)%50==0:log(f'SCAG2020 chunks {len(records)}/{n}; {time.time()-start:.1f}s')
    records.sort(key=lambda x:x['chunk'])
    assert sum(x['count'] for x in records)==count
    import pandas as pd
    pd.DataFrame(records).to_csv(OUT/'SCAG2020_CHUNK_HASHES.csv',index=False)
    dump('SCAG2020_ACQUISITION_COMPLETE.json',{'url':URL,'query_fields':FIELDS,
         'where':"COUNTY = 'Los Angeles'",'count':count,'chunks':n,
         'id_list_sha256':sha(RAW/'SCAG2020_ids_probe.json'),
         'metadata_sha256':sha(OUT/'source_evidence/SCAG2020_layer_current.json'),
         'seconds':time.time()-start,'observed_classification_year':2020,
         'current_service_metadata_is_not_observation_year':True})
    log('SCAG2020 county geometry acquisition reconciled by exact OBJECTID sets.')

if __name__=='__main__':main()
