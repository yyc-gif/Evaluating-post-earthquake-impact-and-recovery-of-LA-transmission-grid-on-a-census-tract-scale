"""Resumable, complete LA SCAG2019 geometry snapshot by exact object IDs."""
import requests,gzip,json,hashlib,time,shutil,concurrent.futures
from source_audit import ROOT,OUT,dump,sha
U='https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0/query';D=OUT/'sources/scag_la_chunks';D.mkdir(exist_ok=True)
ids=json.loads((OUT/'sources/SCAG_LA_OBJECT_IDS.json').read_text(encoding='utf-8'))['objectIds'];assert len(ids)==2406373 and len(set(ids))==len(ids)
def fetch(i):
 selected=ids[i*2000:(i+1)*2000];p=D/f'{i:04d}.json.gz'
 if p.exists():
  with gzip.open(p,'rb') as f:raw=f.read()
 else:
  assert shutil.disk_usage(D).free>600_000_000,'Disk reserve reached; resumable snapshot retained'
  params={'f':'json','objectIds':','.join(map(str,selected)),'outFields':'OBJECTID,PID19,APN19,STACK,ACRES,GEOID20,LU19,LU19_CLASS,LU19_SRC,BF_SQFT','outSR':'3310','returnGeometry':'true'}
  for attempt in range(3):
   try:
    q=requests.post(U,data=params,timeout=(15,60));q.raise_for_status();raw=q.content;x=json.loads(raw);assert 'error' not in x,x.get('error');assert not x.get('exceededTransferLimit');break
   except Exception:
    if attempt==2:raise
    time.sleep(2**attempt)
  with gzip.open(p,'wb',compresslevel=3) as f:f.write(raw)
 x=json.loads(raw);actual=[r['attributes']['OBJECTID'] for r in x['features']];assert set(actual)==set(selected) and len(actual)==len(selected)
 return {'chunk':i,'count':len(actual),'response_bytes':len(raw),'gzip_bytes':p.stat().st_size,'response_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p)}
if __name__=='__main__':
 start=time.time();n=(len(ids)+1999)//2000;first=fetch(0);estimate=first['gzip_bytes']*n;print('SCAG_ESTIMATE',n,estimate,first,flush=True);dump('SCAG_ACQUISITION_PLAN.json',{'chunks':n,'estimated_gzip_bytes_first_chunk':estimate,'disk_free':shutil.disk_usage(D).free,'maximum_concurrency':4})
 assert shutil.disk_usage(D).free>estimate+600_000_000,'First-chunk storage estimate exceeds disk reserve'
 records=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures={pool.submit(fetch,i):i for i in range(n)}
  for f in concurrent.futures.as_completed(futures):
   try:records.append(f.result())
   except Exception as e:
    dump('SCAG_ACQUISITION_PARTIAL.json',{'completed':records,'failed_chunk':futures[f],'error':str(e)});raise
   if len(records)%50==0:print('SCAG_CHUNKS',len(records),'/',n,'sec',round(time.time()-start,1),flush=True)
 dump('SCAG_ACQUISITION_COMPLETE.json',{'source_url':U,'records':sorted(records,key=lambda x:x['chunk']),'total_features':sum(r['count'] for r in records),'seconds':time.time()-start})
