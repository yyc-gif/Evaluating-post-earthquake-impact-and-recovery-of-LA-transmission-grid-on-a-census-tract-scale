"""Exact fractional-cell aggregation of official numeric raster support."""
from common import *
import sys,zipfile,time
sys.path.insert(0,str(ROOT/'_vendor').removeprefix('\\\\?\\'))
import rasterio, numpy as np, pandas as pd, geopandas as gpd, shapely
from rasterio.windows import Window,from_bounds

UNRESOLVED=['06037189703','06037301601','06037301602','06037404600']

def geometry():
 cache=RAW/'study_land.gpkg'
 if cache.exists():return gpd.read_file(str(cache).removeprefix('\\\\?\\')).set_index('tract_id')
 p=RESEARCH/'local_joint_feature_extraction_20261009/sources/study_tract_land_3310.gpkg'
 g=gpd.read_file(str(p).removeprefix('\\\\?\\')).set_index('tract_id')
 t=gpd.read_file(str(ORIGINAL/'Data/LA_Tracts_With_Population.shp').removeprefix('\\\\?\\'));t['tract_id']=t.GEOID.astype(str).str.zfill(11);t=t.set_index('tract_id').to_crs(3310)
 water=RESEARCH/'local_joint_feature_extraction_20261009/sources/tl_2020_06037_areawater.zip'
 w=gpd.read_file('/vsizip/'+str(water).removeprefix('\\\\?\\').replace('\\','/')).to_crs(3310)
 for key in ['06037106112','06037460401']:
  hit=w.loc[w.intersects(t.loc[key].geometry)&w.AWATER.gt(0)]
  g.loc[key,'geometry']=t.loc[key].geometry.difference(shapely.union_all(hit.geometry.to_numpy()))
 for key in ['06037311601','06037311700']:g.loc[key,'geometry']=t.loc[key].geometry
 g['land_geometry_area_m2']=g.geometry.area
 g['geometry_status']=np.where(g.index.isin(UNRESOLVED),'UNRESOLVED_GEOMETRY','VALIDATED_OR_SOURCE_VERSION_QUALIFIED')
 g.reset_index().to_file(str(cache).removeprefix('\\\\?\\'),driver='GPKG')
 dump('LAND_GEOMETRY_REUSE.json',{'source':str(p),'source_sha256':sha(p),'water_source':str(water),'water_sha256':sha(water),'corrected_four': ['06037106112','06037460401','06037311601','06037311700'],'unresolved_four':UNRESOLVED,'output_sha256':sha(cache),'rescaled_to_Census_ALAND':False})
 return g

def raster_sources():
 rec=[]
 for p in RAW.glob('*.zip'):
  if not p.name.startswith(('EMC_BUILT','GHS_BUILT_H')):continue
  with zipfile.ZipFile(p) as z:
   member=next(x for x in z.namelist() if x.endswith('.tif'));dest=RAW/Path(member).name
   if not dest.exists():
    with z.open(member) as a,dest.open('wb') as b:
     import shutil;shutil.copyfileobj(a,b,1024*1024)
   rec.append((p,dest))
 return rec

def aggregate(path,land,kind):
 rows=[]
 with rasterio.open(str(path).removeprefix('\\\\?\\')) as src:
  g=land.to_crs(src.crs)
  meta={'file':str(path),'sha256':sha(path),'shape':list(src.shape),'crs':src.crs.to_string(),'resolution':list(src.res),'nodata':src.nodata,'dtype':src.dtypes,'transform':list(src.transform),'tags':src.tags(),'units':'m' if kind=='height' else 'm2 per 100m pixel','zero_treatment':'valid unbuilt zero; net-height positive support separately','fractional_intersection':True}
  for key,row in g.iterrows():
   if key in UNRESOLVED:continue
   geo=row.geometry.intersection(shapely.box(*src.bounds))
   if geo.is_empty:continue
   w=from_bounds(*geo.bounds,transform=src.transform);c0=max(0,int(np.floor(w.col_off)));r0=max(0,int(np.floor(w.row_off)));c1=min(src.width,int(np.ceil(w.col_off+w.width)));r1=min(src.height,int(np.ceil(w.row_off+w.height)))
   if c1<=c0 or r1<=r0:continue
   data=src.read(1,window=Window(c0,r0,c1-c0,r1-r0))
   rr,cc=np.indices(data.shape);x0=src.transform.c+(cc.ravel()+c0)*src.transform.a;y1=src.transform.f+(rr.ravel()+r0)*src.transform.e
   boxes=shapely.box(x0,y1+src.transform.e,x0+src.transform.a,y1)
   a=shapely.area(shapely.intersection(boxes,geo));v=data.ravel().astype(float)
   valid=np.isfinite(v)&(v!=src.nodata);positive=valid&(v>0)&(a>0)
   validarea=float(a[valid].sum());total=float(a.sum())
   assert np.all(v[valid]>=0)
   if kind!='height':assert np.all(v[valid]<=(100 if kind=='impervious' else 10000))
   weighted=float((v[positive]*a[positive]).sum()) if kind=='height' else float((v[valid]*a[valid]/(100 if kind=='impervious' else abs(src.transform.a*src.transform.e))).sum())
   rows.append({'tract_id':key,'tile':path.name,'land_area_in_raster_crs_m2':row.geometry.area,'tile_intersection_area_m2':total,'valid_area_m2':validarea,'nodata_area_m2':total-validarea,'positive_area_m2':float(a[positive].sum()),'weighted_sum':weighted,'zero_area_m2':float(a[valid&(v==0)].sum()),'positive_cell_count':int(positive.sum()),'positive_min':float(v[positive].min()) if positive.any() else np.nan,'positive_max':float(v[positive].max()) if positive.any() else np.nan})
 return pd.DataFrame(rows),meta

def main():
 land=geometry();tables={};metadata=[];allrows=[];start=time.time()
 if (OUT/'RASTER_METADATA_AND_QA.json').exists():
  old=json.loads((OUT/'RASTER_METADATA_AND_QA.json').read_text(encoding='utf8'))
  assert old['land_geometry_sha256']==sha(RAW/'study_land.gpkg'),'Raster checkpoint land geometry changed'
  for m in old['metadata']:assert sha(Path(m['file']))==m['sha256'],'Raster checkpoint source bytes changed'
 for archive,path in raster_sources():
  kind='height' if path.name.startswith('GHS') else ('nres' if 'NRES' in path.name else 'total')
  checkpoint=OUT/'RASTER_TILE_TRACT_SUPPORT.csv'
  if checkpoint.exists():
   saved=pd.read_csv(checkpoint,dtype={'tract_id':str});d=saved.loc[saved.tile.eq(path.name)].copy()
  else:d=pd.DataFrame()
  if len(d):
   with rasterio.open(str(path).removeprefix('\\\\?\\')) as src:
    m={'file':str(path),'sha256':sha(path),'shape':list(src.shape),'crs':src.crs.to_string(),'resolution':list(src.res),'nodata':src.nodata,'dtype':src.dtypes,'transform':list(src.transform),'tags':src.tags(),'units':'m' if kind=='height' else 'm2 per 100m pixel','checkpoint_reused':True}
  else:d,m=aggregate(path,land,kind)
  metadata.append(m);d['product']=kind;allrows.append(d);log('Fractional raster aggregation complete: '+path.name)
 pd.concat(allrows).to_csv(OUT/'RASTER_TILE_TRACT_SUPPORT.csv',index=False)
 result=pd.DataFrame(index=land.index)
 for kind in ['total','nres','height']:
  d=pd.concat([x for x in allrows if len(x) and x['product'].iloc[0]==kind]);s=d.groupby('tract_id')[['valid_area_m2','nodata_area_m2','positive_area_m2','weighted_sum','zero_area_m2','positive_cell_count']].sum();den=d.groupby('tract_id').land_area_in_raster_crs_m2.first();coverage=s.valid_area_m2/den
  result[f'jrc_{kind}_valid_land_coverage']=coverage
  if kind=='height':
   result['jrc_anbh_positive_surface_mean_m']=s.weighted_sum/s.positive_area_m2.replace(0,np.nan)
   result['jrc_anbh_positive_cell_land_fraction']=s.positive_area_m2/den
  else:result[f'emc2022_{kind}_built_land_fraction']=s.weighted_sum/den
 result['emc2022_nonresidential_built_share']=result.emc2022_nres_built_land_fraction/result.emc2022_total_built_land_fraction.replace(0,np.nan)
 result['raster_geometry_status']=land.geometry_status
 result.reset_index().to_csv(OUT/'JRC_TRACT_MEASUREMENTS.csv',index=False,float_format='%.15g')
 dump('RASTER_METADATA_AND_QA.json',{'metadata':metadata,'seconds':time.time()-start,'land_geometry_sha256':sha(RAW/'study_land.gpkg'),'unresolved_geometry':UNRESOLVED,'ANBH_aggregation':'land-area-weighted mean over positive net-height cells; not footprint-weighted mean and not 2022 height; 2018 support and 2000/2006-2011 DEM','EMC_aggregation':'pixel built-up m2 * fraction of pixel inside tract land / tract land area, not record counts','NRES_not_multiclass_entropy':True})

if __name__=='__main__':main()
