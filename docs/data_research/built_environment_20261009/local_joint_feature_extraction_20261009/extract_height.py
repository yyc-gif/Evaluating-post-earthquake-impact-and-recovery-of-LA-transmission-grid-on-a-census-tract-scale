"""Resolve the two conflicting duplicate heights locally, retaining all other observations."""
import time,hashlib,json,gc
import numpy as np,pandas as pd,pyogrio,shapely
from shapely import STRtree
from source_audit import OUT,sha,dump
from extract_gis import tracts,land
S=OUT/'sources';t=tracts();l=land();tree=STRtree(t.geometry.to_numpy());p=S/'LARIAC6_Buildings_2020.gdb.zip';u='/vsizip/'+str(p).replace(chr(92),'/')+'/LARIAC6_Buildings_2020.gdb';info=pyogrio.read_info(u,layer='LARIAC6_BUILDINGS_2020');seen={};conflicts=set();med=[[] for _ in range(len(t))];weighted=[[] for _ in range(len(t))];start=time.time()
for offset in range(0,info['features'],100000):
 d=pyogrio.read_dataframe(u,layer='LARIAC6_BUILDINGS_2020',skip_features=offset,max_features=100000,columns=['CODE','HEIGHT']);d=d.loc[d.CODE.eq('Building')].copy();d.geometry=d.geometry.make_valid();hs=[hashlib.sha256(w).digest() for w in shapely.to_wkb(shapely.normalize(d.geometry.to_numpy()))];keep=[]
 for i,(key,h) in enumerate(zip(hs,d.HEIGHT)):
  if key in seen:
   old=seen[key]
   if not (old==h or (pd.isna(old) and pd.isna(h))):conflicts.add(key)
  else:seen[key]=h;keep.append(i)
 d=d.iloc[keep].to_crs(3310);hs=np.array(hs,dtype=object)[keep];height=d.HEIGHT.to_numpy(float);valid=np.isfinite(height)&(height>0);d=d.loc[valid];hs=hs[valid];height=height[valid]*.3048;cent=d.geometry.centroid.to_numpy();pairs=tree.query(cent,predicate='intersects');assigned={}
 for bi,ti in zip(*pairs):assigned.setdefault(int(bi),[]).append(int(ti))
 for bi,ts in assigned.items():ti=min(ts,key=lambda k:t.index[k]);med[ti].append((hs[bi],height[bi]))
 pairs=tree.query(d.geometry.to_numpy(),predicate='intersects')
 for ti in np.unique(pairs[1]):
  bi=pairs[0,pairs[1]==ti];clips=shapely.intersection(d.geometry.iloc[bi].to_numpy(),l.geometry.iloc[ti]);area=shapely.area(clips);weighted[ti].extend([(hs[j],height[j],a) for j,a in zip(bi,area) if a>0])
 gc.collect();print('HEIGHT',min(offset+100000,info['features']),round(time.time()-start,1),flush=True)
result=pd.read_csv(OUT/'LARIAC2020_TRACT_URBAN_FORM.csv',dtype={'tract_id':str}).set_index('tract_id').loc[t.index];qa=[]
for i,key in enumerate(t.index):
 values=np.array([h for code,h in med[i] if code not in conflicts]);arr=np.array([(h,a) for code,h,a in weighted[i] if code not in conflicts]);valid_area=arr[:,1].sum() if len(arr) else 0.;total_area=result.building_footprint_union_area_m2.iloc[i]+result.outline_overlap_removed_m2.iloc[i]
 for name,q in [('building_height_median_m',.5),('building_height_p10_m',.1),('building_height_p90_m',.9)]:result.loc[key,name]=np.quantile(values,q) if len(values) else np.nan
 result.loc[key,'building_height_area_weighted_m']=np.sum(arr[:,0]*arr[:,1])/valid_area if valid_area>0 else np.nan;result.loc[key,'building_height_valid_area_fraction']=valid_area/total_area if total_area>0 else np.nan;result.loc[key,'building_height_valid_centroid_count']=len(values);result.loc[key,'height_unit_status']='LARIAC feet schema converted to m; conflicting duplicate outlines excluded locally'
 qa.append({'tract_id':key,'excluded_conflicting_height_centroid_records':sum(code in conflicts for code,h in med[i]),'excluded_conflicting_height_area_m2':sum(a for code,h,a in weighted[i] if code in conflicts)})
result.to_csv(OUT/'LARIAC2020_TRACT_URBAN_FORM.csv',na_rep='',float_format='%.15g');pd.DataFrame(qa).to_csv(OUT/'LARIAC2020_HEIGHT_CONFLICT_AUDIT.csv',index=False);dump('LARIAC2020_HEIGHT_QA.json',{'source_sha256':sha(p),'duplicate_geometry_height_conflicts':len(conflicts),'height_records_withheld':sum(r['excluded_conflicting_height_centroid_records'] for r in qa),'withheld_area_m2':sum(r['excluded_conflicting_height_area_m2'] for r in qa),'height_unit_source':'County official LARIAC data dictionary page18: HEIGHT in feet; LARIAC6 original feet CRS and inherited schema, no number-of-stories inference','height_is_floor_area':False,'minimum_height_filter':'positive finite source HEIGHT only; missing/nonpositive retained as missing height','seconds':time.time()-start});print('HEIGHT_FINISHED',len(conflicts),flush=True)
