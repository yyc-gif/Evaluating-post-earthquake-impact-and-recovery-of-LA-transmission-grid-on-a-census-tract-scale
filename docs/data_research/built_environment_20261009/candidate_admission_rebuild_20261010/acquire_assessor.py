"""Single-roll-year public query; strictly nonpersonal attribute whitelist."""
from common import *
import requests, pandas as pd, numpy as np, gzip, time, concurrent.futures

URL='https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcel_Data_2021_Table/FeatureServer/0/query'
FIELDS=['OBJECTID','AIN','RollYear','UseType','UseCode','totBuildingDataLines','YearBuilt','EffectiveYearBuilt','SQFTmain','Units','ParcelClassification','isTaxableParcel','CENTER_LAT','CENTER_LON']
CACHE=RAW/'assessor2022_v2';CACHE.mkdir(exist_ok=True)

def query(params):
 for attempt in range(4):
  try:
   r=requests.get(URL,params={'f':'json',**params},timeout=(15,90));r.raise_for_status();j=r.json()
   if 'error' in j:raise RuntimeError(j['error'])
   return r,j
  except Exception:
   if attempt==3:raise
   time.sleep(2*(attempt+1))

def main():
 import geopandas as gpd
 t=gpd.read_file(str(ORIGINAL/'Data/LA_Tracts_With_Population.shp').removeprefix('\\\\?\\')).to_crs(4326)
 xmin,ymin,xmax,ymax=t.total_bounds
 where=f"RollYear = '2022' AND CENTER_LON >= {xmin-1e-7} AND CENTER_LON <= {xmax+1e-7} AND CENTER_LAT >= {ymin-1e-7} AND CENTER_LAT <= {ymax+1e-7}"
 f=CACHE/'ids.json'
 if not f.exists():
  # The service truncates returnIdsOnly at 1,000,000. Partition first,
  # verify each partition against an independent count, then deduplicate.
  allids=[];parts=[]
  for a,b in zip(np.linspace(xmin-1e-7,xmax+1e-7,17)[:-1],np.linspace(xmin-1e-7,xmax+1e-7,17)[1:]):
   w=f"RollYear = '2022' AND CENTER_LON >= {a} AND CENTER_LON < {b} AND CENTER_LAT >= {ymin-1e-7} AND CENTER_LAT <= {ymax+1e-7}"
   r,part=query({'where':w,'returnIdsOnly':'true'});_,c=query({'where':w,'returnCountOnly':'true'})
   assert len(part.get('objectIds',[]))==c['count'] and not part.get('exceededTransferLimit',False)
   allids.extend(part.get('objectIds',[]));parts.append({'where':w,'count':c['count']})
  _,c=query({'where':where,'returnCountOnly':'true'})
  assert len(set(allids))==len(allids)==c['count']
  j={'objectIds':allids,'partitions':parts,'verified_count':c['count']};f.write_text(json.dumps(j),encoding='utf-8')
 else:j=json.loads(f.read_text())
 ids=sorted(j['objectIds']);assert len(set(ids))==len(ids)
 r,count=query({'where':"RollYear = '2022'",'returnCountOnly':'true'});(CACHE/'county_count.json').write_bytes(r.content)
 dump('ASSESSOR_ACQUISITION_SPECIFICATION.json',{'url':URL,'where':where,'fields':FIELDS,'roll_year':2022,'county_records':count['count'],'bbox_records':len(ids),'personal_attributes_requested':False,'ids_sha256':sha(f),'chunk_size':2000,'bounds_wgs84':[xmin,ymin,xmax,ymax]})
 def one(k):
  subset=ids[k:k+2000];p=CACHE/f'{k:08d}.json.gz'
  if p.exists():
   with gzip.open(p,'rb') as s: data=s.read()
   v=json.loads(data)
  else:
   r,v=query({'where':where+f' AND OBJECTID >= {subset[0]} AND OBJECTID <= {subset[-1]}','outFields':','.join(FIELDS),'returnGeometry':'false','orderByFields':'OBJECTID','resultRecordCount':2000})
   data=r.content
   with gzip.open(p,'wb') as s:s.write(data)
  got=[x['attributes']['OBJECTID'] for x in v['features']]
  assert sorted(got)==subset, (k,len(got),len(subset),got[:2],subset[:2])
  assert all(x['attributes']['RollYear']=='2022' for x in v['features'])
  return {'chunk_start':k,'records':len(got),'compressed_sha256':sha(p),'payload_sha256':hashlib.sha256(data).hexdigest(),'compressed_bytes':p.stat().st_size}
 records=[];start=time.time()
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
  for r in ex.map(one,range(0,len(ids),2000)):
   records.append(r)
   if len(records)%50==0:log(f'Assessor 2022 verified {sum(x["records"] for x in records)} / {len(ids)} public nonpersonal records; {time.time()-start:.1f} s')
 pd.DataFrame(records).to_csv(OUT/'ASSESSOR_CHUNK_HASHES.csv',index=False)
 dump('ASSESSOR_ACQUISITION_COMPLETE.json',{'records':sum(x['records'] for x in records),'chunks':len(records),'seconds':time.time()-start,'fields':FIELDS,'expected':len(ids),'same_roll_only':True})
 log('Assessor 2022 acquisition complete')

if __name__=='__main__':main()
