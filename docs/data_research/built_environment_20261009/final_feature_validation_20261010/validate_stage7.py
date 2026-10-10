"""Isolated source QA and controlled exploratory Stage 7 comparisons."""
from pathlib import Path
import os, sys, json, hashlib, subprocess, time, itertools, shutil
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from pyproj import Geod
from scipy.stats import spearmanr, pearsonr
ROOT=Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
BASE=ROOT/'docs/data_research/built_environment_20261009'
OLD=BASE/'local_joint_feature_extraction_20261009'
OUT=BASE/'final_feature_validation_20261010'
PARENT='bd913b91c9c73d0b92fa327c28660d74197b6259'
SCIENCE='031d2c675f8e7d58035d27448be040b809ced086'
CLASSES=['residential','commercial_office','industrial','institutional_public','transportation_utility','open_space_recreation','vacant_undeveloped','agriculture','mixed_use','under_construction','protected_undevelopable']
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def dump(n,v): (OUT/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
def read(n,folder=OLD,id='tract_id'):
 d=pd.read_csv(folder/n,dtype={id:str});d[id]=d[id].str.zfill(11);assert d[id].is_unique and d[id].str.fullmatch(r'\d{11}').all();return d.set_index(id)
def save(n,d,index=False):d.to_csv(OUT/n,index=index,na_rep='',float_format='%.15g',lineterminator='\n')
def initialize():
 OUT.mkdir(exist_ok=True);(OUT/'sources').mkdir(exist_ok=True)
 (OUT/'.gitignore').write_text('original_state/\npublish_state/\n__pycache__/\n.pytest_cache/\ncheckpoints/\n*.log\n!*.csv\n',encoding='utf-8',newline='\n')
 (OUT/'.gitattributes').write_text('*.md text eol=lf\n*.py text eol=lf\n*.json text eol=lf\n*.txt text eol=lf\nsources/** -text -diff\n',encoding='utf-8',newline='\n')
 state=OUT/'original_state';state.mkdir(exist_ok=True)
 indexpath=Path(git('rev-parse','--git-path','index').decode().strip())
 if not indexpath.is_absolute():indexpath=ROOT/indexpath
 if not (OUT/'PRESERVATION_BASELINE.json').exists():
  (state/'index.bin').write_bytes(git('ls-files','--stage','-z'))
  (state/'index_file.bin').write_bytes(indexpath.read_bytes())
  (state/'status.bin').write_bytes(git('status','--porcelain=v1','-z'))
  prior=json.loads((OLD/'PRESERVATION_BASELINE.json').read_text(encoding='utf-8'))
  protected={k:sha(ROOT/k) for k in prior['protected_files']}
  assert protected==prior['protected_files']
  dump('PRESERVATION_BASELINE.json',{'head':git('rev-parse','HEAD').decode().strip(),'branch':git('branch','--show-current').decode().strip(),'protected_files':protected,'staged_count':len(git('diff','--cached','--name-only').splitlines()),'index_sha256':sha(indexpath)})
 for name in ['NEXT_STAGE7_GATE.md','analyze.py','results/FEATURE_GATE_SUMMARY.json']:
  data=git('show',PARENT+':docs/data_research/built_environment_20261009/physical_feature_gate_20261010/'+name)
  (OUT/'sources'/('gate_'+Path(name).name)).write_bytes(data)
 print('ISOLATED',OUT,flush=True)
def landqa():
 import requests
 q=read('TRACT_GEOMETRY_LAND_WATER_QA.csv');bad=q.loc[q.land_area_relative_difference.abs()>.005]
 f=read('TRACT_FEATURE_CANDIDATES.csv');sc=read('SCAG_TRACT_LAND_USE.csv');lar=read('LARIAC2020_TRACT_URBAN_FORM.csv')
 t=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp');t['tract_id']=t.GEOID.astype(str).str.zfill(11);t=t.set_index('tract_id').loc[q.index]
 tp=t.to_crs(3310);wg=gpd.read_file('zip://'+str(OLD/'sources/tl_2020_06037_areawater.zip'));w=wg.to_crs(3310)
 print('WATER_CLASSES',w.groupby(['MTFCC']).agg(n=('AWATER','size'),land=('ALAND','sum'),water=('AWATER','sum')).to_string(),flush=True)
 url='https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Tracts_Blocks/MapServer/0'
 source=OUT/'sources/CENSUS2020_18_TRACTS.geojson'
 if not source.exists():
  where='GEOID IN ('+','.join("'"+k+"'" for k in bad.index)+')'
  response=requests.get(url+'/query',params={'f':'geojson','where':where,'outFields':'*','returnGeometry':'true','outSR':4269},timeout=(15,60));response.raise_for_status();j=response.json();assert 'error' not in j and len(j['features'])==18
  source.write_bytes(response.content);dump('CENSUS2020_GEOMETRY_ACQUISITION.json',{'url':response.url,'bytes':len(response.content),'sha256':sha(source),'count':18,'reason':'Only discrepant tract boundary comparison, no mass data reacquisition'})
 old=gpd.read_file(source);old['tract_id']=old.GEOID.astype(str);old=old.set_index('tract_id').to_crs(3310)
 rows=[];hydro=[];geod=Geod(ellps='GRS80')
 for key,b in bad.iterrows():
  geo=tp.loc[key].geometry;hit=w[w.intersects(geo)].copy();hit['clip_area_m2']=hit.intersection(geo).area
  for _,h in hit.iterrows():hydro.append({'tract_id':key,**h.drop(labels='geometry').to_dict()})
  union=shapely.union_all(hit.geometry.to_numpy());per=hit.loc[hit.AWATER.gt(0) & hit.ALAND.eq(0)]
  perunion=shapely.union_all(per.geometry.to_numpy());land=geo.difference(union);censusland=geo.difference(perunion)
  ga=abs(geod.geometry_area_perimeter(shapely.orient_polygons(t.loc[key].geometry))[0])
  r={'tract_id':key,'residential_member':bool(f.loc[key,'residential_member']),'census_ALAND_m2':b.census_ALAND_m2,'census_AWATER_m2':b.census_AWATER_m2,'original_projected_polygon_area_m2':geo.area,'original_geodesic_polygon_area_m2':ga,'polygon_total_relative_error':geo.area/(b.census_ALAND_m2+b.census_AWATER_m2)-1,'projection_relative_error':geo.area/ga-1,'before_land_area_m2':land.area,'before_relative_error':land.area/b.census_ALAND_m2-1,'recomputed_vs_cached_land_error_m2':land.area-b.land_geometry_area_m2,'nonwater_hydro_area_m2':censusland.area-land.area,'perennial_only_land_area_m2':censusland.area,'perennial_only_relative_error':censusland.area/b.census_ALAND_m2-1,'2020_polygon_area_m2':old.loc[key].geometry.area,'2020_boundary_symmetric_difference_m2':geo.symmetric_difference(old.loc[key].geometry).area,'SCAG_classified_area_m2':sc.loc[key,'land_use_classified_area_m2'],'SCAG_unclassified_area_m2':sc.loc[key,'unclassified_land_area_m2'],'SCAG_ambiguous_area_m2':sc.loc[key,'ambiguous_overlap_land_area_m2'],'SCAG_water_area_m2':sc.loc[key,'scag_mapped_water_area_m2'],'SCAG_gap_area_m2':sc.loc[key,'parcel_gap_area_m2'],'LARIAC_existing_union_m2':lar.loc[key,'building_footprint_union_area_m2'],'hydro_features':len(hit),'hydro_land_features':int(hit.ALAND.gt(0).sum()),'hydro_names':'; '.join(hit.FULLNAME.dropna().astype(str).unique()),'hydro_MTFCCs':';'.join(sorted(hit.MTFCC.unique()))}
  r['census2020_ALAND_m2']=float(old.loc[key,'AREALAND']);r['census2020_AWATER_m2']=float(old.loc[key,'AREAWATER'])
  r['mask_vs_census2020_relative_error']=land.area/r['census2020_ALAND_m2']-1
  r['after_land_area_m2']=land.area;r['after_relative_error']=r['before_relative_error'];r['status']='UNRESOLVED_MIXED_WATER_FEATURE';r['cause']='Mixed statistical land/water inside a named river polygon; source does not locate its land portion'
  if key in ['06037106112','06037460401']:
   # AWATER==0 identifies the complete hydrography polygon as statistical land.
   use=hit.loc[hit.AWATER.gt(0)];newland=geo.difference(shapely.union_all(use.geometry.to_numpy()))
   r['after_land_area_m2']=newland.area;r['status']='CORRECTED_PURE_STATISTICAL_LAND_REMOVAL';r['cause']='Old mask removed hydrography with AWATER=0 and positive ALAND; retain those explicitly statistical-land polygons'
  elif key in ['06037311601','06037311700']:
   assert r['census_AWATER_m2']==0 and r['census2020_AWATER_m2']==0
   newland=geo;r['after_land_area_m2']=geo.area;r['status']='CORRECTED_ZERO_WATER_TRACT';r['cause']='Both tract source versions explicitly have AWATER=0; river hydrography intersection represents statistical land here'
  elif abs(r['mask_vs_census2020_relative_error'])<.005:
   r['status']='RESOLVED_SOURCE_VERSION_DIFFERENCE_NO_NUMERIC_CHANGE';r['cause']='2020 water mask agrees with 2020 Census land definition; archived tract ALAND/AWATER differs from 2020 attributes'
  r['after_relative_error']=r['after_land_area_m2']/b.census_ALAND_m2-1
  r['after_vs_census2020_relative_error']=r['after_land_area_m2']/r['census2020_ALAND_m2']-1
  r['feature_disposition']='WITHHOLD_POLYGON_CANDIDATES' if r['status'].startswith('UNRESOLVED') else ('REINTERSECT_CACHED_SCAG_LARIAC' if r['status'].startswith('CORRECTED') else 'RESTORE_EXISTING_MEASUREMENT_WITH_SOURCE_VERSION_FLAG')
  r['projection_cause_rejected']=abs(r['projection_relative_error'])<1e-4
  rows.append(r)
 result=pd.DataFrame(rows);save('LANDMASK_18_TRACT_RESOLUTION.csv',result);save('LANDMASK_HYDRO_FEATURE_INTERSECTIONS.csv',pd.DataFrame(hydro));print(result[['tract_id','before_relative_error','perennial_only_relative_error','nonwater_hydro_area_m2','2020_boundary_symmetric_difference_m2']].to_string(index=False),flush=True)
 dump('LANDMASK_QA.json',{'18_cases':len(result),'15_residential':int(result.residential_member.sum()),'max_recomputed_cache_error_m2':float(result.recomputed_vs_cached_land_error_m2.abs().max()),'water_filter_explanation':'ALAND-positive hydrography feature polygons include statistical land; examine individually before correction','geodesic_comparison':'GRS80 original tract polygons; EPSG3310 area distortion compared separately'})
def corrections():
 """Reintersect four demonstrably corrected masks, using existing raw caches."""
 import gzip,pyogrio
 sys.path.insert(0,str(OLD))
 from extract_scag import geometry,broad,overlay,areal
 q=read('LANDMASK_18_TRACT_RESOLUTION.csv',OUT);ids=q.index[q.status.str.startswith('CORRECTED')].tolist();assert len(ids)==4
 t=gpd.read_file(ROOT/'Data/LA_Tracts_With_Population.shp');t['tract_id']=t.GEOID.astype(str);t=t.set_index('tract_id').loc[ids].to_crs(3310)
 w=gpd.read_file('zip://'+str(OLD/'sources/tl_2020_06037_areawater.zip')).to_crs(3310)
 masks={}
 for key,row in t.iterrows():
  if row.AWATER==0:masks[key]=row.geometry
  else:masks[key]=row.geometry.difference(shapely.union_all(w.loc[w.AWATER.gt(0)&w.intersects(row.geometry)].geometry.to_numpy()))
  assert abs(masks[key].area-q.loc[key,'after_land_area_m2'])<1e-5
 keys=ids;bounds=np.asarray([t.loc[k].geometry.bounds for k in keys]);selected={};counts=0;start=time.time();checkpoint=OUT/'checkpoints';checkpoint.mkdir(exist_ok=True)
 cache=checkpoint/'scag_four_reintersections.pkl'
 if cache.exists():
  import pickle
  selected=pickle.loads(cache.read_bytes())
 else:
  for ci,p in enumerate(sorted((OLD/'sources/scag_la_chunks').glob('*.json.gz'))):
   with gzip.open(p,'rb') as stream:data=json.load(stream)
   for f in data['features']:
    if not f.get('geometry'):continue
    rings=f['geometry']['rings'];pts=np.asarray([xy for ring in rings for xy in ring]);lo=pts.min(axis=0);hi=pts.max(axis=0)
    candidates=np.where((hi[0]>=bounds[:,0])&(lo[0]<=bounds[:,2])&(hi[1]>=bounds[:,1])&(lo[1]<=bounds[:,3]))[0]
    if not len(candidates):continue
    geo=geometry(rings);geo=shapely.make_valid(geo) if not geo.is_valid else geo
    if geo.area<=0:continue
    if not any(geo.intersects(t.loc[keys[x]].geometry) for x in candidates):continue
    h=hashlib.sha256(shapely.to_wkb(shapely.normalize(geo))).hexdigest();a=f['attributes'];v=pd.to_numeric(a['LU19'],errors='coerce');c=broad(int(v) if pd.notna(v) else -1)
    if h in selected:selected[h][1].add(c)
    else:selected[h]=[shapely.to_wkb(geo),{c}]
   counts+=len(data['features'])
   if ci%100==0:print('SCAG_FOUR_CACHE_SCAN',ci,counts,len(selected),round(time.time()-start,1),flush=True)
  import pickle
  cache.write_bytes(pickle.dumps(selected));assert counts==2406373
 rows=[]
 for key in ids:
  by={c:[] for c in CLASSES+['water','unclassified','stack_conflict']}
  for binary,cs in selected.values():
   geo=shapely.from_wkb(binary)
   if geo.intersects(t.loc[key].geometry):by[next(iter(cs)) if len(cs)==1 else 'stack_conflict'].append(geo)
  unions={c:overlay(shapely.union_all(v),t.loc[key].geometry,'intersection',key) for c,v in by.items()};seen=shapely.Polygon();conflict=unions['stack_conflict']
  for c in CLASSES+['water','unclassified']:
   conflict=areal(shapely.union_all([conflict,overlay(seen,unions[c],'intersection',key)]));seen=areal(shapely.union_all([seen,unions[c]]))
  areas={c:overlay(overlay(unions[c],conflict,'difference',key),masks[key],'intersection',key).area for c in CLASSES};a=sum(areas.values());pp=np.array(list(areas.values()))/a
  row={'tract_id':key,'land_geometry_area_m2':masks[key].area,'land_use_entropy':-np.sum(pp[pp>0]*np.log(pp[pp>0]))/np.log(11),'land_use_classified_area_m2':a,'land_use_classified_land_coverage':a/masks[key].area,'unclassified_land_area_m2':unions['unclassified'].intersection(masks[key]).area,'ambiguous_overlap_land_area_m2':conflict.intersection(masks[key]).area}
  for c in CLASSES:row[c+'_area_m2']=areas[c]
  # Spatial subset reads from the unchanged full local geodatabases.
  for vintage,src,layer,cols in [('2020',OLD/'sources/LARIAC6_Buildings_2020.gdb.zip','LARIAC6_BUILDINGS_2020',['CODE']),('2014',OLD/'sources/LARIAC4_BUILDINGS_2014.zip','LARIAC4_BUILDINGS_2014',['CODE','YearBuilt1','UseType','Roll_Year'])]:
   u='/vsizip/'+str(src).replace('\\','/')+('/LARIAC6_Buildings_2020.gdb' if vintage=='2020' else '/LARIAC4_BUILDINGS_2014/LARIAC4_BUILDINGS_2014.gdb')
   info=pyogrio.read_info(u,layer=layer);box=gpd.GeoSeries([t.loc[key].geometry],crs=3310).to_crs(info['crs']).total_bounds
   d=pyogrio.read_dataframe(u,layer=layer,bbox=tuple(box),columns=cols);d=d.loc[d.CODE.eq('Building')&d.geometry.notna()].copy();d.geometry=d.geometry.make_valid();d['_hash']=[hashlib.sha256(x).hexdigest() for x in shapely.to_wkb(shapely.normalize(d.geometry.to_numpy()))]
   if vintage=='2014':
    year=pd.to_numeric(d.YearBuilt1,errors='coerce');roll=pd.to_numeric(d.Roll_Year,errors='coerce');valid=year.between(1800,2014)&year.mod(1).eq(0)&(roll.isna()|year.le(roll));d['_year']=year.where(valid);d['_attrs']=list(zip(d['_year'].fillna(-1),d.UseType.fillna('None')));conf=d.groupby('_hash')._attrs.nunique();d.loc[d._hash.isin(conf[conf>1].index),'_year']=np.nan
   d=d.drop_duplicates('_hash').to_crs(3310);clips=shapely.intersection(d.geometry.to_numpy(),masks[key]);allarea=shapely.union_all(clips).area
   if vintage=='2020':row['building_footprint_union_area_m2']=allarea;row['building_footprint_coverage']=allarea/masks[key].area
   else:
    va=shapely.union_all(clips[d['_year'].notna()]).area;pa=shapely.union_all(clips[d['_year'].lt(1970)]).area
    row.update(all_use2014_footprint_union_area_m2=allarea,all_use2014_valid_age_area_m2=va,all_use2014_pre1970_area_m2=pa,all_use2014_missing_age_area_m2=allarea-va,all_use2014_pre1970_area_share=pa/va,all_use2014_age_coverage=va/allarea,all_use2014_pre1970_lower_bound=pa/allarea,all_use2014_pre1970_upper_bound=(pa+allarea-va)/allarea)
   print('REINTERSECT',key,vintage,len(d),round(time.time()-start,1),flush=True)
  rows.append(row)
 result=pd.DataFrame(rows);save('CORRECTED_TRACT_INTERSECTIONS.csv',result)
 prior=read('TRACT_FEATURE_CANDIDATES.csv');audit=[]
 for _,row in result.iterrows():
  for field in ['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share','land_use_classified_land_coverage','all_use2014_age_coverage']:
   oldfield=field+'_geometry_diagnostic' if field in ['land_use_entropy','building_footprint_coverage'] else field
   audit.append({'tract_id':row.tract_id,'field':field,'old_value':prior.loc[row.tract_id,oldfield],'new_value':row[field],'change':row[field]-prior.loc[row.tract_id,oldfield],'change_scope':'new candidate extraction only; original outputs unchanged'})
 save('CORRECTED_INDICATOR_BEFORE_AFTER.csv',pd.DataFrame(audit));dump('CORRECTED_INTERSECTIONS_QA.json',{'tracts':ids,'raw_SCAG_cache_records':2406373,'SCAG_target_unique_geometries':len(selected),'source_geometries_reacquired':0,'mask_rescaled_to_ALAND':False,'actual_union_and_intersections':True,'seconds':time.time()-start})
def entropy(a):
 p=np.asarray(a,dtype=float);p=p/p.sum();v=p[p>0];return float(-np.sum(v*np.log(v))/np.log(11))
def entropy_max_alloc(a,total):
 # Water filling maximizes Shannon entropy subject to observed class lower bounds.
 a=np.asarray(a,dtype=float);lo=0.;hi=total
 for _ in range(80):
  mid=(lo+hi)/2
  if np.maximum(a,mid).sum()>total:hi=mid
  else:lo=mid
 return entropy(np.maximum(a,(lo+hi)/2))
def features():
 f=read('TRACT_FEATURE_CANDIDATES.csv');q=read('LANDMASK_18_TRACT_RESOLUTION.csv',OUT);correct=read('CORRECTED_TRACT_INTERSECTIONS.csv',OUT);sc=read('SCAG_TRACT_LAND_USE.csv');age=read('BUILDING_AGE_2014_ORIGINAL_TRACTS.csv')
 # Restore measurements only where source identity resolves the prior flag.
 f['landmask_disposition']='ORIGINAL_MASK_CHECK_PASS'
 for key,row in q.iterrows():
  f.loc[key,'landmask_disposition']=row.status
  if row.status.startswith('RESOLVED'):
   f.loc[key,'land_use_entropy']=sc.loc[key,'land_use_entropy'];f.loc[key,'building_footprint_coverage']=f.loc[key,'building_footprint_coverage_geometry_diagnostic']
  elif row.status.startswith('CORRECTED'):
   for c in correct.columns:
    f.loc[key,c]=correct.loc[key,c]
    if c in sc:sc.loc[key,c]=correct.loc[key,c]
    if c in age:age.loc[key,c]=correct.loc[key,c]
  else:f.loc[key,['land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share']]=np.nan
 nri=read('NRI_Table_CensusTracts_California.csv',ROOT/'Data',id='TRACTFIPS');f['ALR_NPCTL']=nri.ALR_NPCTL;f['EAL_SCORE']=nri.EAL_SCORE;f['log1p_NRI_BUILDVALUE']=np.log1p(f.NRI_BUILDVALUE);f['log1p_B_480_hr']=np.log1p(f.B_480_hr);f['log1p_Pop_Density']=np.log1p(f.Pop_Density)
 e=[]
 for key,row in sc.iterrows():
  a=row[[c+'_area_m2' for c in CLASSES]].to_numpy(float);classified=a.sum();total=float(row.land_geometry_area_m2);missing=max(0,total-classified);base=entropy(a);dominant=int(a.argmax());coverage=classified/total
  scenarios={'observed_classified':a,'missing_to_transport':a.copy(),'missing_to_dominant':a.copy(),'missing_proportional':a*(total/classified)}
  scenarios['missing_to_transport'][4]+=missing;scenarios['missing_to_dominant'][dominant]+=missing
  for name,aa in scenarios.items():
   h=entropy(aa);e.append({'tract_id':key,'residential_member':bool(f.loc[key,'residential_member']),'scenario':name,'landmask_disposition':f.loc[key,'landmask_disposition'],'eligible_candidate':not f.loc[key,'landmask_disposition'].startswith('UNRESOLVED'),'classified_land_coverage':coverage,'classified_area_m2':classified,'not_classified_area_m2':missing,'observed_entropy':base,'entropy':h,'change':h-base,'dominant_observed_category':CLASSES[dominant],'interpretation':'OBSERVED_CLASSIFIED_ONLY' if name=='observed_classified' else 'HYPOTHETICAL_MISSING_LAND_ALLOCATION_NOT_OBSERVED','entropy_unconstrained_lower_bound':min(entropy(a+np.eye(11)[i]*missing) for i in range(11)),'entropy_unconstrained_upper_bound':entropy_max_alloc(a,total)})
 er=pd.DataFrame(e);sr=[];resids=f.index[f.residential_member]
 for name,g in er.groupby('scenario'):
  idx=g.tract_id.isin(resids)&g.eligible_candidate;v=g.loc[idx].copy();v['rank_observed']=v.observed_entropy.rank(pct=True);v['rank_scenario']=v.entropy.rank(pct=True);v['rank_change']=v.rank_scenario-v.rank_observed
  er.loc[v.index,'rank_observed']=v.rank_observed;er.loc[v.index,'rank_scenario']=v.rank_scenario;er.loc[v.index,'rank_change']=v.rank_change
  sr.append({'scenario':name,'n':len(v),'median_coverage':v.classified_land_coverage.median(),'spearman_vs_observed':spearmanr(v.observed_entropy,v.entropy).statistic,'pearson_vs_observed':pearsonr(v.observed_entropy,v.entropy).statistic,'median_abs_entropy_change':v.change.abs().median(),'p95_abs_entropy_change':v.change.abs().quantile(.95),'median_abs_percentile_rank_change':v.rank_change.abs().median(),'p95_abs_percentile_rank_change':v.rank_change.abs().quantile(.95),'share_moved_over20_percentile_points':v.rank_change.abs().gt(.2).mean(),'hypothetical':name!='observed_classified'})
 save('SCAG_ENTROPY_SENSITIVITY.csv',er);save('SCAG_ENTROPY_SCENARIO_SUMMARY.csv',pd.DataFrame(sr))
 for name in ['missing_to_transport','missing_to_dominant','missing_proportional']:
  v=er.loc[er.scenario.eq(name)].set_index('tract_id');f['entropy_'+name]=v.entropy;f.loc[f.landmask_disposition.str.startswith('UNRESOLVED'),'entropy_'+name]=np.nan
 ar=age.copy();ar['residential_member']=f.residential_member;ar['ACS_residential_housing_unit_age_share']=f.residential_pre1970_housing_share;ar['ACS_age_moe90']=f.Pre_1970_Ratio_moe90;ar['strict_2020_transfer_age_coverage_diagnostic']=f.all_use_age_coverage;ar['landmask_disposition']=f.landmask_disposition;ar['missing_age_bound_width']=ar.all_use2014_pre1970_upper_bound-ar.all_use2014_pre1970_lower_bound;ar['interpretation']='2014 valid observed all-use footprint age; bounds assume all unknown age new/old, not CI or imputation'
 save('BUILDING_AGE_SENSITIVITY.csv',ar,index=True)
 f['age_lower_bound']=ar.all_use2014_pre1970_lower_bound;f['age_upper_bound']=ar.all_use2014_pre1970_upper_bound
 use=pd.read_csv(OLD/'BUILDING_AGE_2014_BY_USE_COVERAGE.csv',dtype={'tract_id':str});use['scope']='ORIGINAL_2014_MASK_BY_USE_DIAGNOSTIC';save('BUILDING_AGE_USE_MISSINGNESS.csv',use)
 required=['B_480_hr','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share','SOVI_SCORE','log1p_NRI_BUILDVALUE','ALR_NPCTL']
 original=read('clusters_labels_final.csv',ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized');r=f.loc[original.index].copy();assert len(r)==2291
 r['primary_complete_case']=r[required].notna().all(axis=1);r['legacy2276_complete_case']=r.primary_complete_case & r.land_mask_area_check_pass
 assert r.legacy2276_complete_case.sum()==2276
 r['missing_primary_fields']=r[required].isna().apply(lambda x:';'.join(x.index[x]),axis=1)
 save('FINAL_CANDIDATE_FEATURE_MATRIX.csv',r,index=True);save('COMPLETE_CASE_FEATURE_MATRIX.csv',r.loc[r.primary_complete_case],index=True);save('LEGACY_2276_COMPLETE_CASE_FEATURE_MATRIX.csv',r.loc[r.legacy2276_complete_case],index=True)
 r['complete_case_exclusion_reason']=np.where(r.primary_complete_case,'NONE',r.landmask_disposition)
 save('TRACT_SAMPLE_ACCOUNTING.csv',r[['primary_complete_case','legacy2276_complete_case','missing_primary_fields','complete_case_exclusion_reason']],index=True)
 # Sources are explicitly pinned; no final feature choice from cluster labels.
 paths=[OLD/n for n in ['TRACT_FEATURE_CANDIDATES.csv','TRACT_GEOMETRY_LAND_WATER_QA.csv','GEOMETRY_DISCREPANT_TRACTS.csv','FEATURE_ASSEMBLY_QA.json','SCAG_TRACT_LAND_USE.csv','BUILDING_AGE_2014_ORIGINAL_TRACTS.csv','BUILDING_AGE_2014_BY_USE_COVERAGE.csv','LARIAC2020_TRACT_URBAN_FORM.csv','RECOVERY_B_T80_INIT_COMPARISON.csv']]+[ROOT/'Data/NRI_Table_CensusTracts_California.csv',ROOT/'Data/LA_Tracts_With_Population.shp',ROOT/'Data/LA_Tracts_With_Population.dbf',ROOT/'Data/LA_Tracts_With_Population.shx',OLD/'sources/tl_2020_06037_areawater.zip',OLD/'sources/LARIAC4_BUILDINGS_2014.zip',OLD/'sources/LARIAC6_Buildings_2020.gdb.zip',ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv']
 dump('INPUT_HASHES.json',{p.relative_to(ROOT).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in paths})
 meta=[]
 for c in required+['T80','log1p_B_480_hr','EAL_SCORE','residential_pre1970_housing_share','Pop_Density','housing_5plus_share']:
  if c in ['B_480_hr','T80','Init_Supply','log1p_B_480_hr']:source='formal saved 1000-realization 2pc50/C57_D1/direct-community/M1/G1/H480';vintage='2026 formal experiment';unit='h' if c!='Init_Supply' else 'fraction';flag='EXACT_FORMAL_OUTPUT';transform='log1p then z score' if c.startswith('log1p') else 'z score'
  elif c.startswith(('Grid_','Redundancy')):source='existing production mapping and frozen station topology';vintage='formal M1';unit='mapping-weighted graph metric';flag='EXACT_EXISTING_DESCRIPTOR';transform='z score'
  elif c.startswith('land_use'):source='SCAG2019 11 exclusive classified-land classes';vintage='2019 ALU2019.1';unit='normalized entropy';flag='PARTIAL_CLASSIFIED_LAND_WITH_SCENARIO_SENSITIVITY';transform='z score'
  elif c.startswith('building_footprint'):source='LARIAC6 2020 release union footprints clipped to tract land';vintage='cumulative outlines, predominantly 2008 imagery, 2020 release';unit='area fraction';flag='MIXED_ACQUISITION_VINTAGE';transform='z score'
  elif c.startswith('all_use2014'):source='LARIAC4 original2014 observed assessor-associated YearBuilt1';vintage='2014 outlines';unit='known-age footprint area fraction';flag='PARTIAL_VALID_YEAR_COVERAGE_NOT_2020_AGE';transform='z score'
  elif c in ['residential_pre1970_housing_share','housing_5plus_share']:source='ACS2022 5-year B25034/B25024';vintage='2018-2022';unit='housing unit fraction';flag='ESTIMATE_WITH_MOE_NOT_ALL_USE_BUILDINGS';transform='z score'
  elif c=='Pop_Density':source='original CDC California.csv';vintage='original Stage7 archived source';unit='persons per sq mi';flag='DEMOGRAPHIC_EXPOSURE_SENSITIVITY_ONLY';transform='log1p then z score'
  else:source='archived FEMA NRI v1.19 March2023';vintage='March2023';unit='national percentile' if c in ['ALR_NPCTL','EAL_SCORE'] else ('published social-vulnerability score' if c=='SOVI_SCORE' else 'log1p USD stock');flag='PUBLISHED_SCORE_RETAINED_BEFORE_STANDARDIZATION';transform='log1p then z score' if c.startswith('log1p') else 'z score'
  meta.append({'feature':c,'source':source,'vintage':vintage,'units':unit,'transformation':transform,'quality_flag':flag,'n_residential':2291,'observed':int(r[c].notna().sum()),'missing':int(r[c].isna().sum()),'zero_count':int(r[c].eq(0).sum()),'primary':c in required})
 save('FINAL_FEATURE_DEFINITIONS_AND_QA.csv',pd.DataFrame(meta));dump('FEATURE_MATRIX_QA.json',{'full_domain':2315,'residential':2291,'candidate_complete':int(r.primary_complete_case.sum()),'legacy_complete':2276,'unresolved_residential':r.index[~r.primary_complete_case].tolist(),'required':required,'no_zero_or_median_imputation':True,'fixed_source_recovery_identity':'B mean integral, T80 threshold of mean trajectory, initial mean service; no new trajectories','geoids_exact_saved_order':True})
 print('MATRICES',2291,int(r.primary_complete_case.sum()),2276,flush=True)
if __name__=='__main__':
 {'initialize':initialize,'landqa':landqa,'corrections':corrections,'features':features}[sys.argv[1]]()
