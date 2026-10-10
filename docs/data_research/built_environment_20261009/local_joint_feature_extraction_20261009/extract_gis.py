"""Equal-area spatial feature extraction using read-only authoritative sources."""
import os,sys,json,time,zipfile,shutil,requests,hashlib,warnings,gzip,pickle,gc
import numpy as np,pandas as pd,geopandas as gpd,pyogrio,shapely
from shapely import STRtree
from scipy.spatial import cKDTree
from pyproj import Transformer
from source_audit import ROOT,OUT,sha,dump
from acquire_sources import download
S=OUT/'sources'
def tracts():
 ids=pd.read_csv(OUT/'RECOVERY_B_T80_INIT_COMPARISON.csv',dtype={'tract_id':str}).tract_id
 g=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp');g['tract_id']=g.GEOID.astype(str).str.zfill(11);g=g.set_index('tract_id').reindex(ids);assert len(g)==2315 and g.geometry.notna().all();return g.to_crs(3310)
def land():
 p=S/'tl_2020_06037_areawater.zip'
 if not p.exists():download('https://www2.census.gov/geo/tiger/TIGER2020/AREAWATER/tl_2020_06037_areawater.zip',p,200_000_000)
 cache=S/'study_tract_land_3310.gpkg'
 if cache.exists():return gpd.read_file(cache).set_index('tract_id')
 t=tracts();w=gpd.read_file('zip://'+str(p)).to_crs(3310);invalid=int((~w.geometry.is_valid).sum());w.geometry=w.geometry.make_valid();tree=STRtree(w.geometry.to_numpy());areas=[];shapes=[]
 for key,row in t.iterrows():
  hit=tree.query(row.geometry,predicate='intersects');water=shapely.union_all(w.geometry.iloc[hit].to_numpy());geo=shapely.difference(row.geometry,water);shapes.append(geo);areas.append({'tract_id':key,'geometry_area_m2':row.geometry.area,'land_geometry_area_m2':geo.area,'mapped_water_area_m2':row.geometry.area-geo.area,'census_ALAND_m2':row.ALAND,'census_AWATER_m2':row.AWATER,'land_area_relative_difference':geo.area/row.ALAND-1 if row.ALAND>0 else np.nan})
 df=pd.DataFrame(areas).set_index('tract_id');df['geometry']=shapes;result=gpd.GeoDataFrame(df,geometry='geometry',crs=3310);result.reset_index().to_file(cache,driver='GPKG');df.drop(columns='geometry').to_csv(OUT/'TRACT_GEOMETRY_LAND_WATER_QA.csv');dump('TRACT_GEOMETRY_LAND_WATER_QA.json',{'water_source':str(p),'water_sha256':sha(p),'water_vintage':2020,'water_records':len(w),'invalid_water_repaired':invalid,'tract_invalid':int((~t.geometry.is_valid).sum()),'land_area_max_relative_difference':float(np.nanmax(np.abs(df.land_area_relative_difference))),'land_area_median_relative_difference':float(df.land_area_relative_difference.median()),'denominator':'EPSG3310 tract polygon minus TIGER2020 area-water geometry; Census ALAND retained as independent check'})
 return result

def lariac():
 start=time.time();landg=land();t=tracts();cache=S/'lariac6_tract_clips';cache.mkdir(exist_ok=True);assert not any(cache.iterdir()),'Existing clip cache retained; use a separate cache path for rerun';tree=STRtree(t.geometry.to_numpy());geos=[[] for _ in range(len(t))];heights=[[] for _ in range(len(t))];counts=np.zeros(len(t),dtype=int);height_area=np.zeros(len(t));valid_area=np.zeros(len(t));all_area=np.zeros(len(t));invalid_count=0;dup_ids=0;empty_count=0;seen=set();seen_geometry={};geometry_duplicates=0;conflicting_duplicate_heights=0;duplicate_id_examples=[];codecounts={};datecounts={};n=0;cross_boundary=0;count_outside=0;repaired=[];area_ratios=[]
 p=S/'LARIAC6_Buildings_2020.gdb.zip';u='/vsizip/'+str(p).replace(chr(92),'/')+'/LARIAC6_Buildings_2020.gdb';info=pyogrio.read_info(u,layer='LARIAC6_BUILDINGS_2020')
 for offset in range(0,info['features'],100000):
  d=pyogrio.read_dataframe(u,layer='LARIAC6_BUILDINGS_2020',skip_features=offset,max_features=100000,columns=['CODE','BLD_ID','HEIGHT','AREA','SOURCE','DATE_'],fid_as_index=True)
  for k,v in d.CODE.value_counts(dropna=False).items():codecounts[str(k)]=codecounts.get(str(k),0)+int(v)
  d=d.loc[d.CODE.eq('Building')].copy()
  for k,v in d.DATE_.value_counts(dropna=False).items():datecounts[str(k)]=datecounts.get(str(k),0)+int(v)
  dup=d.BLD_ID.notna()&(d.BLD_ID.isin(seen)|d.BLD_ID.duplicated());dup_ids+=int(dup.sum());duplicate_id_examples+=d.loc[dup,['BLD_ID','SOURCE']].head(20).to_dict('records');seen.update(d.BLD_ID.dropna());bad=~d.geometry.is_valid;invalid_count+=int(bad.sum());repaired+=d.index[bad].tolist();d.loc[bad,'geometry']=d.geometry[bad].make_valid();empty=d.geometry.is_empty|d.geometry.isna();empty_count+=int(empty.sum());d=d.loc[~empty].copy()
  dedup=[]
  for position,(wkb,h) in enumerate(zip(shapely.to_wkb(shapely.normalize(d.geometry.to_numpy())),d.HEIGHT)):
   key=hashlib.sha256(wkb).digest()
   if key in seen_geometry:
    geometry_duplicates+=1;previous=seen_geometry[key];conflicting_duplicate_heights+=int(not (h==previous or (pd.isna(h) and pd.isna(previous))));dedup.append(position)
   else:seen_geometry[key]=h
  if dedup:d=d.drop(d.index[dedup])
  area_ratios.extend((d.AREA/d.geometry.area).dropna().tolist());d=d.to_crs(3310);cent=d.geometry.centroid.to_numpy();pairs=tree.query(cent,predicate='intersects');hits={}
  for bi,ti in zip(*pairs):hits.setdefault(int(bi),[]).append(int(ti))
  for bi,ts in hits.items():
   ti=min(ts,key=lambda k:t.index[k]);counts[ti]+=1;h=d.HEIGHT.iloc[bi]
   if np.isfinite(h) and h>0:heights[ti].append(float(h)*.3048)
  count_outside+=len(d)-len(hits);pairs=tree.query(d.geometry.to_numpy(),predicate='intersects');numhits=np.bincount(pairs[0],minlength=len(d));cross_boundary+=int((numhits>1).sum());n+=len(d)
  for ti in np.unique(pairs[1]):
   bi=pairs[0,pairs[1]==ti];sh=d.geometry.iloc[bi].to_numpy();clips=shapely.intersection(sh,landg.geometry.iloc[ti]);positive=shapely.area(clips)>0;clips=clips[positive];bi=bi[positive];
   with gzip.open(cache/(str(t.index[ti])+'.pkl.gz'),'ab',compresslevel=3) as f:pickle.dump(shapely.to_wkb(clips).tolist(),f,protocol=4)
   a=shapely.area(clips);h=d.HEIGHT.iloc[bi].to_numpy(float)*.3048;valid=np.isfinite(h)&(h>0);height_area[ti]+=float(np.sum(a[valid]*h[valid]));valid_area[ti]+=float(a[valid].sum());all_area[ti]+=float(a.sum())
  gc.collect();print('LARIAC_READ',offset+len(d),'raw',min(offset+100000,info['features']),'sec',round(time.time()-start,1),flush=True)
 rows=[];exact_duplicate_clips=0
 for ti,key in enumerate(t.index):
  raw=[];cp=cache/(str(key)+'.pkl.gz')
  if cp.exists():
   with gzip.open(cp,'rb') as f:
    while True:
     try:raw.extend(pickle.load(f))
     except EOFError:break
  raw=shapely.from_wkb(raw);area=shapely.area(raw) if len(raw) else np.array([]);union=shapely.union_all(raw);union_area=float(union.area);validfraction=valid_area[ti]/all_area[ti] if all_area[ti]>0 else np.nan
  # Median uses one building centroid per tract. Weighted height uses clipped outline areas, not inferred floor area.
  rows.append({'tract_id':key,'building_footprint_union_area_m2':union_area,'building_footprint_coverage':union_area/landg.land_geometry_area_m2.iloc[ti] if landg.land_geometry_area_m2.iloc[ti]>0 else np.nan,'building_count':counts[ti],'building_count_density':counts[ti]/(landg.land_geometry_area_m2.iloc[ti]/1e6) if landg.land_geometry_area_m2.iloc[ti]>0 else np.nan,'building_height_median_m':float(np.median(heights[ti])) if heights[ti] else np.nan,'building_height_p10_m':float(np.quantile(heights[ti],.1)) if heights[ti] else np.nan,'building_height_p90_m':float(np.quantile(heights[ti],.9)) if heights[ti] else np.nan,'building_height_area_weighted_m':height_area[ti]/valid_area[ti] if valid_area[ti]>0 else np.nan,'building_height_valid_area_fraction':validfraction,'building_height_valid_centroid_count':len(heights[ti]),'outline_overlap_removed_m2':all_area[ti]-union_area,'land_geometry_area_m2':landg.land_geometry_area_m2.iloc[ti],'lariac_status':'OBSERVED_2020_ROOFLINES_WITH_MIXED_ACQUISITION_DATES','height_unit_status':'feet converted to m; LARIAC data dictionary and original feet CRS/AREA consistency','detection_limit_status':'NO_DOCUMENTED_MINIMUM_DETECTABLE_FOOTPRINT'})
  geos[ti]=[]
  if ti%200==0:print('LARIAC_UNION',ti,flush=True)
 result=pd.DataFrame(rows)
 if conflicting_duplicate_heights:
  for column in ['building_height_median_m','building_height_p10_m','building_height_p90_m','building_height_area_weighted_m']:result[column]=np.nan
  result['height_unit_status']='WITHHELD_CONFLICTING_DUPLICATE_OUTLINE_ATTRIBUTES'
 assert result.building_footprint_coverage.between(0,1+1e-8).all();result.to_csv(OUT/'LARIAC2020_TRACT_URBAN_FORM.csv',index=False,na_rep='',float_format='%.15g');dump('LARIAC2020_GEOMETRY_QA.json',{'source_sha256':sha(p),'feature_class':'LARIAC6_BUILDINGS_2020','raw_records':info['features'],'code_counts':codecounts,'building_records':n,'duplicate_BLD_ID':dup_ids,'duplicate_id_examples':duplicate_id_examples,'duplicate_geometry_removed':geometry_duplicates,'duplicate_geometry_conflicting_heights':conflicting_duplicate_heights,'invalid_repaired':invalid_count,'repaired_OBJECTIDs':repaired,'empty':empty_count,'source_date_counts':datecounts,'cross_tract_outline_count':cross_boundary,'centroids_outside_study':count_outside,'AREA_vs_original_geometry_ratio_quantiles':np.quantile(area_ratios,[0,.01,.5,.99,1]).tolist(),'total_overlap_removed_m2':float(result.outline_overlap_removed_m2.sum()),'crs':info['crs'],'analysis_crs':'EPSG3310','centroid_tie_rule':'lexicographically smallest GEOID for exact boundary ties','height_weighting':'positive HEIGHT converted feet to m, clipped polygon area; BLD_ID repeats do not erase distinct outlines; exact normalized geometry duplicates removed and conflicting heights withhold height candidates; geometric overlap is quantified, union used for coverage; height is outline-area weighted, not floor-area weighted','seconds':time.time()-start,'zero_building_tracts':result.loc[result.building_count.eq(0),'tract_id'].tolist(),'minimum_detectable_footprint':'not documented; no arbitrary small-outline exclusion'})

if __name__=='__main__':{'land':land,'lariac':lariac}[sys.argv[1]]()
