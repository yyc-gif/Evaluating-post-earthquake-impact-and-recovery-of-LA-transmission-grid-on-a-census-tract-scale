"""Verify every saved 2014 per-tract cache count/area against original source intersections."""
import hashlib,gzip,pickle,time,gc
import numpy as np,pandas as pd,pyogrio,shapely
from shapely import STRtree
from source_audit import OUT,dump
from extract_gis import tracts,land
S=OUT/'sources';t=tracts();l=land();tree=STRtree(t.geometry.to_numpy());u='/vsizip/'+str(S/'LARIAC4_BUILDINGS_2014.zip').replace(chr(92),'/')+'/LARIAC4_BUILDINGS_2014/LARIAC4_BUILDINGS_2014.gdb';info=pyogrio.read_info(u,layer='LARIAC4_BUILDINGS_2014');seen=set();expected_count=np.zeros(len(t),dtype=int);expected_area=np.zeros(len(t));start=time.time()
for offset in range(0,info['features'],100000):
 d=pyogrio.read_dataframe(u,layer='LARIAC4_BUILDINGS_2014',skip_features=offset,max_features=100000,columns=['CODE']);d=d.loc[d.CODE.eq('Building')&d.geometry.notna()].copy();d.geometry=d.geometry.make_valid();hs=[hashlib.sha256(w).digest() for w in shapely.to_wkb(shapely.normalize(d.geometry.to_numpy()))];keep=[]
 for i,h in enumerate(hs):
  if h not in seen:seen.add(h);keep.append(i)
 d=d.iloc[keep].to_crs(3310);pairs=tree.query(d.geometry.to_numpy(),predicate='intersects')
 for ti in np.unique(pairs[1]):
  bi=pairs[0,pairs[1]==ti];a=shapely.area(shapely.intersection(d.geometry.iloc[bi].to_numpy(),l.geometry.iloc[ti]));expected_count[ti]+=int((a>0).sum());expected_area[ti]+=a[a>0].sum()
 gc.collect()
 if offset%500000==0:print('AGE2014_CACHE_VERIFY',offset,round(time.time()-start,1),flush=True)
rows=[]
for ti,key in enumerate(t.index):
 cp=S/'age2014_tract_clips_v3'/f'{key}.pkl.gz';n=0;area=0
 if cp.exists():
  with gzip.open(cp,'rb') as f:
   while True:
    try:h,w=pickle.load(f);n+=1;area+=shapely.from_wkb(w).area
    except EOFError:break
 rows.append({'tract_id':key,'expected_records':expected_count[ti],'cache_records':n,'expected_clipped_area_sum_m2':expected_area[ti],'cache_clipped_area_sum_m2':area,'record_count_matches':n==expected_count[ti],'area_abs_error_m2':abs(area-expected_area[ti])})
r=pd.DataFrame(rows);r.to_csv(OUT/'BUILDING_AGE_2014_CACHE_COMPLETENESS.csv',index=False,na_rep='',float_format='%.15g');ok=r.record_count_matches.all() and np.allclose(r.expected_clipped_area_sum_m2,r.cache_clipped_area_sum_m2,rtol=1e-11,atol=1e-5)
dump('BUILDING_AGE_2014_CACHE_QA.json',{'all_expected_source_intersections_match':bool(ok),'tracts':len(r),'expected_cache_records':int(r.expected_records.sum()),'observed_cache_records':int(r.cache_records.sum()),'maximum_area_error_m2':float(r.area_abs_error_m2.max()),'source_records':info['features'],'seconds':time.time()-start});assert ok,'Cache completeness failed; do not admit original2014 candidate'
print('AGE2014_CACHE_COMPLETE',len(r),r.area_abs_error_m2.max(),flush=True)
