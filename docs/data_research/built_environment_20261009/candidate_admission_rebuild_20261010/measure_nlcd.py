"""Exact fractional-land aggregation of official C1.2 and existing C1.0 numeric pilot."""
from common import *
from measure_rasters import geometry,aggregate,UNRESOLVED
import rasterio,pandas as pd,numpy as np
from rasterio.windows import from_bounds,Window

def main():
 land=geometry();a=json.loads((OUT/'NLCD_C12_ACQUISITION.json').read_text());full=Path(a['tif_path']);evidence=OUT/'source_evidence';evidence.mkdir(exist_ok=True);clip=evidence/'NLCD_C12_2022_STUDY_CLIP.tif'
 if not clip.exists():
  with rasterio.open(str(full).removeprefix('\\\\?\\')) as src:
   g=land.to_crs(src.crs);w=from_bounds(*g.total_bounds,transform=src.transform);c0=int(np.floor(w.col_off));r0=int(np.floor(w.row_off));c1=int(np.ceil(w.col_off+w.width));r1=int(np.ceil(w.row_off+w.height));w=Window(c0,r0,c1-c0,r1-r0);p=src.profile.copy();p.update(width=int(w.width),height=int(w.height),transform=src.window_transform(w),compress='deflate',tiled=True)
   data=src.read(1,window=w)
   with rasterio.open(str(clip).removeprefix('\\\\?\\'),'w',**p) as dst:dst.write(data,1);dst.update_tags(source_collection='Annual NLCD C1.2',mapping_year='2022',parent_sha256=a['numeric_raster_sha256'],unit='percent fractional impervious 0-100; roads included')
 log('Official NLCD study clip created; beginning fractional30m pixel/land measurement')
 old=source('validation/sources/Annual_NLCD_2022_fis_study_clip.tif');rows=[];metadata=[];result=pd.DataFrame(index=land.index)
 for label,path in [('c12',clip),('c10_pilot_same_geometry',old)]:
  checkpoint=OUT/f'NLCD_{label}_TRACT_SUPPORT.csv'
  if checkpoint.exists():
   d=pd.read_csv(checkpoint,dtype={'tract_id':str});m={'checkpoint_reused':True,'file':str(path),'sha256':sha(path)}
  else:d,m=aggregate(path,land,'impervious');d.to_csv(checkpoint,index=False)
  m['units']='percent fractional impervious (0-100)';metadata.append(m)
  d=d.set_index('tract_id');cov=d.valid_area_m2/d.land_area_in_raster_crs_m2;measure=d.weighted_sum/d.land_area_in_raster_crs_m2
  result[f'nlcd_{label}_valid_land_coverage']=cov;result[f'nlcd_{label}_impervious_fraction']=measure.where(cov.ge(1-1e-6));log(f'NLCD {label} complete: {measure.notna().sum()} tract measurements')
 result['nlcd_c12_minus_c10_fraction']=result.nlcd_c12_impervious_fraction-result.nlcd_c10_pilot_same_geometry_impervious_fraction;result.index.name='tract_id';result.to_csv(OUT/'NLCD_OFFICIAL_AND_PILOT_COMPARISON.csv',float_format='%.15g')
 result=result.rename(columns={'nlcd_c12_impervious_fraction':'nlcd_c12_2022_impervious_fraction'});result.to_csv(OUT/'NLCD_C12_TRACT_MEASUREMENTS.csv',float_format='%.15g')
 dump('NLCD_C12_MEASUREMENT_QA.json',{'official_parent':a,'metadata':metadata,'study_clip_sha256':sha(clip),'same_land_geometry_sha256':sha(RAW/'study_land.gpkg'),'full_valid_n':int(result.nlcd_c12_2022_impervious_fraction.notna().sum()),'difference_summary':result.nlcd_c12_minus_c10_fraction.describe(percentiles=[.01,.1,.5,.9,.99]).to_dict(),'NoData_not_zero':True,'includes_roads_not_building_footprints':True,'local_accuracy_not_established':True,'old_pilot_not_identical_version':True,'four_unresolved':UNRESOLVED})
if __name__=='__main__':main()
