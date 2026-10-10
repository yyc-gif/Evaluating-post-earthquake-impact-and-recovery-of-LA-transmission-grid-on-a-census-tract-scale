"""Geographic PGA extraction from verified CGS grid, not station dependencies."""
import json,time,hashlib,requests
import pandas as pd,numpy as np,geopandas as gpd,shapely
from shapely.geometry import box
from shapely import STRtree
from pyproj import Transformer
from scipy.spatial import cKDTree
from source_audit import ROOT,OUT,sha,dump
from extract_gis import tracts,land

def idw(points,gridxy,values):
 tree=cKDTree(gridxy);dist,ind=tree.query(points,k=8,distance_upper_bound=11000);result=np.full(len(points),np.nan)
 for i,(d,idx) in enumerate(zip(dist,ind)):
  use=np.isfinite(d)&(idx<len(values));d=d[use];idx=idx[use]
  if len(d):
   if (d==0).any():result[i]=values[idx[np.flatnonzero(d==0)[0]]]
   else:
    w=1/d**2;result[i]=np.exp(np.sum(w*np.log(values[idx]))/sum(w))
 return result

def run():
 source=ROOT/'Data/MS_048_CA_pt01_MMI_GM_datafiles/CA_pt01_GM_maps.csv';acq=json.loads((OUT/'ACQUISITION_LOG.json').read_text(encoding='utf-8'));assert acq['CGS']['exact_match'] and acq['CGS']['grid_official_sha256']==sha(source)
 meta_url='https://www.arcgis.com/sharing/rest/content/items/b506577c7a0b4b259fd0a87c8ffcf15f';meta=requests.get(meta_url,params={'f':'json'},timeout=30).json();(OUT/'sources/CGS_PGA_PORTAL_ITEM.json').write_text(json.dumps(meta,indent=2),encoding='utf-8');assert '2025' in meta['title'] and 'PGA' in meta['title'] and ' g' in meta['description']
 d=pd.read_csv(source,skipinitialspace=True);d.columns=d.columns.str.strip();assert d[['Lat','long']].duplicated().sum()==0 and d['PGA-2pc50'].gt(0).all();g=tracts();l=land();bounds=g.to_crs(4326).total_bounds;use=d.long.between(bounds[0]-.15,bounds[2]+.15)&d.Lat.between(bounds[1]-.15,bounds[3]+.15);sub=d.loc[use].copy();x,y=Transformer.from_crs(4326,3310,always_xy=True).transform(sub.long.to_numpy(),sub.Lat.to_numpy());xy=np.c_[x,y];z=sub['PGA-2pc50'].to_numpy();cent=g.centroid.to_numpy();points=np.array([[p.x,p.y] for p in cent]);centroid=idw(points,xy,z)
 cells=gpd.GeoSeries([box(lon-.005,lat-.005,lon+.005,lat+.005) for lon,lat in zip(sub.long,sub.Lat)],crs=4326).to_crs(3310);tree=STRtree(cells.to_numpy());rows=[]
 for i,(key,row) in enumerate(l.iterrows()):
  hit=tree.query(row.geometry,predicate='intersects');clips=shapely.intersection(cells.iloc[hit].to_numpy(),row.geometry);a=shapely.area(clips);covered=float(a.sum());coverage=covered/row.land_geometry_area_m2 if row.land_geometry_area_m2>0 else np.nan;value=float(np.dot(a,z[hit])/covered) if covered>0 else np.nan
  rows.append({'tract_id':key,'tract_seismic_PGA':value,'tract_seismic_PGA_unit':'g','PGA_land_grid_coverage':coverage,'PGA_centroid_IDW_g':centroid[i],'PGA_min_grid_g':float(z[hit][a>0].min()) if (a>0).any() else np.nan,'PGA_max_grid_g':float(z[hit][a>0].max()) if (a>0).any() else np.nan,'PGA_positive_intersection_cells':int((a>0).sum()),'hazard_vintage':'CGS MS48 2025 / USGS NSHM2023 / Vs30 July2022','hazard_definition':'PGA with 2% exceedance probability in 50 years','hazard_aggregation':'land-area weighted arithmetic mean of original 0.01-degree grid-point Voronoi cells clipped to TIGER2020-water-excluded tract; partial support flagged','hazard_status':'VERIFIED_PURE_PGA_FIELD' if np.isfinite(coverage) and coverage>=.99 else 'PARTIAL_GRID_SUPPORT'})
 out=pd.DataFrame(rows);out['PGA_partial_support_estimate_g']=out.tract_seismic_PGA.where(out.hazard_status.ne('VERIFIED_PURE_PGA_FIELD'));out.loc[out.hazard_status.ne('VERIFIED_PURE_PGA_FIELD'),'tract_seismic_PGA']=np.nan;out.to_csv(OUT/'TRACT_SEISMIC_HAZARD.csv',index=False,float_format='%.15g',na_rep='')
 stations=pd.read_csv(ROOT/'Data/Substations_PGA_IDW_CEC_expanded.csv',dtype={'ID':str});cols=stations.columns.tolist();lon=next(c for c in cols if c.lower() in ['longitude','lon','long']);lat=next(c for c in cols if c.lower() in ['latitude','lat']);sx,sy=Transformer.from_crs(4326,3310,always_xy=True).transform(stations[lon].to_numpy(),stations[lat].to_numpy());computed=idw(np.c_[sx,sy],xy,z);comparison=pd.DataFrame({'station_id':stations.ID,'frozen_PGA_g':stations.PGA_2pc50,'reconstructed_from_original_grid_g':computed,'error_g':computed-stations.PGA_2pc50});comparison.to_csv(OUT/'FROZEN_STATION_PGA_SOURCE_CHECK.csv',index=False)
 dump('TRACT_SEISMIC_HAZARD_QA.json',{'source_sha256':sha(source),'official_download_exact_byte_match':True,'grid_records':len(d),'original_grid_spacing_degrees':.01,'grid_subset_records':len(sub),'units':'g','vintage':out.hazard_vintage.iloc[0],'no_risk_or_fragility_features_used':True,'station_source_max_error_g':float(comparison.error_g.abs().max()),'tract_count':len(out),'grid_coverage_quantiles':out.PGA_land_grid_coverage.quantile([0,.01,.5,.99,1]).to_dict(),'tracts_partial_support':out.loc[out.hazard_status.ne('VERIFIED_PURE_PGA_FIELD'),'tract_id'].tolist(),'centroid_IDW':'diagnostic only: original log(g) IDW with k8, power2, 11km; primary area mean uses grid support, not station-PGA interpolation','land_mask':'Census TIGER2020 county area-water geometry','source':'https://www.conservation.ca.gov/cgs/Pages/Publications/MS48.aspx'})
 print('PGA_QA',out.hazard_status.value_counts().to_dict(),comparison.error_g.abs().max(),flush=True)
if __name__=='__main__':run()
