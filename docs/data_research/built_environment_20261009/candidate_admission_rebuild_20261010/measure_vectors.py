"""Read-only outline size/height inventory and single-year parcel diagnostics."""
from common import *
import pandas as pd, numpy as np, geopandas as gpd, shapely, pyogrio, gzip, time,gc
from shapely import STRtree
from measure_rasters import geometry,UNRESOLVED

def tracts():
 t=gpd.read_file(str(ORIGINAL/'Data/LA_Tracts_With_Population.shp').removeprefix('\\\\?\\'))
 t['tract_id']=t.GEOID.astype(str).str.zfill(11)
 return t.set_index('tract_id').to_crs(3310)

def assign(points,tree,ids):
 pairs=tree.query(points,predicate='intersects');order=np.lexsort((ids[pairs[0]],pairs[1])) if False else np.lexsort((ids[pairs[1]],pairs[0]))
 p=pairs[:,order];keep=np.r_[True,p[0,1:]!=p[0,:-1]] if p.shape[1] else np.array([],dtype=bool)
 return p[:,keep]

def outlines():
 p=RESEARCH/'local_joint_feature_extraction_20261009/sources/LARIAC6_Buildings_2020.gdb.zip'
 expected=json.loads(source('local_joint_feature_extraction_20261009/ACQUISITION_LOG.json').read_text())['LARIAC6']['sha256'];assert sha(p)==expected
 u='/vsizip/'+str(p).removeprefix('\\\\?\\').replace('\\','/')+'/LARIAC6_Buildings_2020.gdb'
 t=tracts();ids=t.index.to_numpy();tree=STRtree(t.geometry.to_numpy());info=pyogrio.read_info(u,layer='LARIAC6_BUILDINGS_2020');sizes=[[] for _ in ids];height=[[] for _ in ids];seen={};conflicts=set();source_counts={};dates={};n=0;duplicate=0;bad=0;allseen=[];start=time.time();multipart=np.zeros(len(ids),int)
 for offset in range(0,info['features'],100000):
  d=pyogrio.read_dataframe(u,layer='LARIAC6_BUILDINGS_2020',skip_features=offset,max_features=100000,columns=['CODE','HEIGHT','DATE_','SOURCE','BLD_ID','AREA'])
  d=d.loc[d.CODE.eq('Building')].copy();bad+=int((~d.geometry.is_valid).sum());d.geometry=d.geometry.make_valid();hs=[hashlib.sha256(x).digest() for x in shapely.to_wkb(shapely.normalize(d.geometry.to_numpy()))];keep=[]
  for j,(h,v) in enumerate(zip(hs,d.HEIGHT)):
   if h in seen:
    duplicate+=1
    if not (v==seen[h] or (pd.isna(v) and pd.isna(seen[h]))):conflicts.add(h)
   else:seen[h]=v;keep.append(j)
  d=d.iloc[keep].copy();hs=np.array(hs,dtype=object)[keep];d=d.to_crs(3310);a=d.geometry.area.to_numpy();h=d.HEIGHT.to_numpy(float)*.3048
  pairs=assign(d.geometry.centroid.to_numpy(),tree,ids)
  for bi,ti in zip(*pairs):
   if a[bi]>0 and np.isfinite(a[bi]):sizes[ti].append(float(a[bi]));height[ti].append((hs[bi],float(h[bi]),float(a[bi])))
   multipart[ti]+=int(d.geometry.iloc[bi].geom_type=='MultiPolygon')
  for k,v in d.SOURCE.value_counts(dropna=False).items():source_counts[str(k)]=source_counts.get(str(k),0)+int(v)
  for k,v in d.DATE_.value_counts(dropna=False).items():dates[str(k)]=dates.get(str(k),0)+int(v)
  n+=len(d)
  if offset%500000==0:log(f'LARIAC cached outline measurement {offset+len(d)} / {info["features"]}; {time.time()-start:.1f} s')
  del d;gc.collect()
 rows=[]
 for i,key in enumerate(ids):
  a=np.array(sizes[i]);v=np.array([(x,b) for code,x,b in height[i] if code not in conflicts and np.isfinite(x) and x>0]);valid_area=v[:,1].sum() if len(v) else 0;total=a.sum()
  rows.append({'tract_id':key,'outline_centroid_count':len(a),'outline_area_sum_m2':total,'outline_area_mean_m2':a.mean() if len(a) else np.nan,'outline_area_median_m2':np.median(a) if len(a) else np.nan,'outline_area_p10_m2':np.quantile(a,.1) if len(a) else np.nan,'outline_area_p90_m2':np.quantile(a,.9) if len(a) else np.nan,'outline_area_iqr_m2':np.quantile(a,.75)-np.quantile(a,.25) if len(a) else np.nan,'outline_area_cv':a.std(ddof=0)/a.mean() if len(a) else np.nan,'outline_multipart_count':int(multipart[i]),'outline_valid_height_area_fraction_centroid':valid_area/total if total>0 else np.nan,'outline_height_area_weighted_centroid_m':np.dot(v[:,0],v[:,1])/valid_area if valid_area>0 else np.nan,'outline_volume_per_land_m_centroid':np.dot(v[:,0],v[:,1])/t.ALAND.iloc[i] if valid_area>0 and t.ALAND.iloc[i]>0 else np.nan,'outline_count_per_km2_centroid':len(a)/(t.ALAND.iloc[i]/1e6) if t.ALAND.iloc[i]>0 else np.nan,'outline_area_fraction_centroid_sum':total/t.ALAND.iloc[i] if t.ALAND.iloc[i]>0 else np.nan})
 result=pd.DataFrame(rows);measurecols=[c for c in result if c!='tract_id'];result.loc[result.tract_id.isin(UNRESOLVED),measurecols]=np.nan
 result.to_csv(OUT/'LARIAC_SIZE_AND_HEIGHT_MEASUREMENTS.csv',index=False,float_format='%.15g')
 dump('LARIAC_SIZE_AND_SEGMENTATION_QA.json',{'source_sha256':expected,'records':info['features'],'unique_building_outlines':n,'exact_duplicates':duplicate,'conflicting_duplicate_height_geometries':len(conflicts),'invalid_geometry_repaired':bad,'source_counts':source_counts,'date_counts':dates,'count_convention':'whole deduplicated outline assigned by centroid; exact boundary ties smallest GEOID','size_convention':'whole projected EPSG3310 outline area, not clipped fragments','volume_scope':'centroid-assigned area-height product on positive finite nonconflicting heights; geometric overlap not unioned; not independent of factors and not whole-land union volume','physical_building_identity':'source rooflines may split a physical building or include annexes; no independent physical-building segmentation ground truth','seconds':time.time()-start})
 log('Outline size and centroid-supported height/volume diagnostics complete')

def assessor():
 t=tracts();ids=t.index.to_numpy();tree=STRtree(t.geometry.to_numpy());chunks=[];start=time.time();cache=RAW/'assessor2022_v2'
 for k,p in enumerate(sorted(cache.glob('*.json.gz'))):
  with gzip.open(p,'rb') as f:j=json.load(f)
  d=pd.DataFrame([x['attributes'] for x in j['features']]);assert d.RollYear.eq('2022').all()
  geo=gpd.GeoSeries(gpd.points_from_xy(d.CENTER_LON,d.CENTER_LAT),crs=4326).to_crs(3310)
  pairs=assign(geo.to_numpy(),tree,ids);a=d.iloc[pairs[0]].copy();a['tract_id']=ids[pairs[1]];chunks.append(a)
  if k%200==0:log(f'Assessor point assignment {k} cached chunks; {time.time()-start:.1f} s')
 d=pd.concat(chunks,ignore_index=True);dup=d.duplicated('AIN',keep=False)
 conflict=d.loc[dup].groupby('AIN')[['YearBuilt','EffectiveYearBuilt','SQFTmain','UseType','totBuildingDataLines','CENTER_LAT','CENTER_LON']].nunique(dropna=False).max(axis=1).gt(1)
 badids=set(conflict[conflict].index);d=d.loc[~d.AIN.isin(badids)].drop_duplicates('AIN').copy()
 for field in ['YearBuilt','EffectiveYearBuilt']:
  v=pd.to_numeric(d[field],errors='coerce');d[field+'_valid']=v.between(1700,2022)&v.eq(np.floor(v));d[field+'_numeric']=v.where(d[field+'_valid'])
 d['area_m2']=pd.to_numeric(d.SQFTmain,errors='coerce')*.09290304;d['positive_area']=d.area_m2.gt(0);d['valid_age_area']=d.area_m2.where(d.positive_area & d.YearBuilt_valid,0);d['pre1970_area']=d.valid_age_area.where(d.YearBuilt_numeric.lt(1970),0);d['effective_valid_area']=d.area_m2.where(d.positive_area & d.EffectiveYearBuilt_valid,0);d['effective_pre1970_area']=d.effective_valid_area.where(d.EffectiveYearBuilt_numeric.lt(1970),0)
 d['single_line']=d.totBuildingDataLines.eq(1);d['multi_line']=d.totBuildingDataLines.gt(1);d['condo_use']=d.UseType.eq('CND')
 # Unique AIN is an assessment identity; shared locations are not silently deduplicated buildings.
 condo=d.loc[d.condo_use];shared=condo.groupby(['CENTER_LAT','CENTER_LON'],dropna=False).size();shared_keys=set(shared[shared>1].index)
 d['shared_condo_location']=[(a,b) in shared_keys for a,b in zip(d.CENTER_LAT,d.CENTER_LON)]
 rows=[];use=[]
 grouped=dict(tuple(d.groupby('tract_id',sort=False)));empty=d.iloc[:0]
 for key in ids:
  a=grouped.get(key,empty);valid=a.loc[a.positive_area];area=valid.area_m2.sum();aged=valid.valid_age_area.sum();single=valid.loc[valid.single_line];sa=single.area_m2.sum();sv=single.valid_age_area.sum();ea=valid.effective_valid_area.sum()
  rows.append({'tract_id':key,'assessor2022_parcel_records':len(a),'assessor2022_main_area_m2':area,'assessor2022_main_area_per_land':area/t.ALAND.loc[key] if t.ALAND.loc[key]>0 else np.nan,'assessor2022_actual_age_main_area_coverage':aged/area if area>0 else np.nan,'assessor2022_actual_pre1970_main_area_share':valid.pre1970_area.sum()/aged if aged>0 else np.nan,'assessor2022_effective_pre1970_main_area_share':valid.effective_pre1970_area.sum()/ea if ea>0 else np.nan,'assessor2022_single_line_age_coverage':sv/sa if sa>0 else np.nan,'assessor2022_single_line_pre1970_main_area_share':single.pre1970_area.sum()/sv if sv>0 else np.nan,'assessor2022_multi_line_area_share':valid.loc[valid.multi_line].area_m2.sum()/area if area>0 else np.nan,'assessor2022_condo_area_share':valid.loc[valid.condo_use].area_m2.sum()/area if area>0 else np.nan,'assessor2022_zero_or_missing_area_records':int((~a.positive_area).sum()),'assessor2022_invalid_actual_year_records':int((~a.YearBuilt_valid).sum()),'assessor2022_coordinate_assignment':'PARCEL_POINT_NOT_BUILDING_INTERSECTION'})
  for name,v in valid.groupby('UseType',dropna=False):
   den=v.area_m2.sum();num=v.valid_age_area.sum();use.append({'tract_id':key,'use_type':str(name),'records':len(v),'main_area_m2':den,'valid_actual_year_area_m2':num,'actual_year_area_coverage':num/den if den>0 else np.nan,'observed_pre1970_share':v.pre1970_area.sum()/num if num>0 else np.nan})
 r=pd.DataFrame(rows);r.loc[r.tract_id.isin(UNRESOLVED),'assessor2022_main_area_per_land']=np.nan
 r.to_csv(OUT/'ASSESSOR2022_TRACT_MEASUREMENTS.csv',index=False,float_format='%.15g');pd.DataFrame(use).to_csv(OUT/'ASSESSOR2022_TRACT_USE_COVERAGE.csv',index=False)
 dump('ASSESSOR_MEASUREMENT_QA.json',{'records_in_county_tract_assignment_before_dedup':sum(len(x) for x in chunks),'deduplicated_county_parcels':len(d),'aggregation_tracts_county':len(ids),'final_model_subset':2315,'duplicate_AIN_records':int(dup.sum()),'conflicting_AIN_withheld':len(badids),'unique_roll_year':['2022'],'use_counts':d.UseType.fillna('UNKNOWN').value_counts().to_dict(),'classification_counts':d.ParcelClassification.fillna('UNKNOWN').value_counts().to_dict(),'taxability_counts':d.isTaxableParcel.fillna('UNKNOWN').value_counts().to_dict(),'valid_actual_year_records':int(d.YearBuilt_valid.sum()),'multi_building_data_line_records':int(d.multi_line.sum()),'condominium_CND_records':int(d.condo_use.sum()),'condominium_shared_point_groups':len(shared_keys),'condominium_records_at_shared_points':int(condo.set_index(['CENTER_LAT','CENTER_LON']).index.isin(shared_keys).sum()),'nonpersonal_fields_only':True,'age_validity_interval':[1700,2022],'position':'parcel location point; not footprint intersection; no cross-vintage footprint transfer','area_definition':'Main Square Footage in official roll dictionary; insufficient definition for certified gross floor area/FAR','government_exempt_stock_completeness':'not independently established; tax roll is not complete all-use census','seconds':time.time()-start})
 log('Assessor 2022 tract and use-level measurement audit complete')

if __name__=='__main__':{'outlines':outlines,'assessor':assessor}[__import__('sys').argv[1]]()
