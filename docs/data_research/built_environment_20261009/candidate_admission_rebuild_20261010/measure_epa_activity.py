"""EPA counts transferred through the actual SLD donor polygons, not FIPS prefixes."""
from common import *
import requests,gzip,time
import pandas as pd,numpy as np,geopandas as gpd,shapely
from shapely import STRtree
from measure_vectors import tracts
from measure_rasters import geometry as land,UNRESOLVED
from measure_scag2020 import geometry as rings_geometry,areal,overlay

URL='https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer/7'
COUNTS=['HH','E5_Ret','E5_Off','E5_Ind','E5_Svc','E5_Ent']
CACHE=RAW/'epa_sld_geometry';CACHE.mkdir(exist_ok=True)

def request(params):
 for attempt in range(4):
  try:
   r=requests.post(URL+'/query',data={'f':'json',**params},timeout=(15,90));r.raise_for_status();j=r.json()
   if 'error' in j:raise RuntimeError(j['error'])
   return r,j
  except Exception:
   if attempt==3:raise
   time.sleep(2**attempt)

def entropy(a,fixed=False):
 a=np.asarray(a,float);s=a.sum(axis=1);p=np.divide(a,s[:,None],out=np.zeros_like(a),where=s[:,None]>0)
 term=np.zeros_like(p);positive=p>0;term[positive]=p[positive]*np.log(p[positive]);n=(a>0).sum(axis=1)
 h=np.divide(-term.sum(axis=1),np.log(np.maximum(2,6 if fixed else n)))
 h[(s<=0)|~np.isfinite(s)]=np.nan
 return h

def main():
 start=time.time();src=pd.read_csv(source('pilot/EPA_SLD_V3_LA_BG_SOURCE.csv'))
 for c in ['GEOID10','GEOID20']:src[c]=src[c].astype('int64').astype(str).str.zfill(12)
 assert len(src)==6425 and src.GEOID10.is_unique
 where="STATEFP='06' AND COUNTYFP='037'"
 _,c=request({'where':where,'returnCountOnly':'true'})
 _,ids=request({'where':where,'returnIdsOnly':'true'})
 ids=sorted(ids['objectIds']);assert len(set(ids))==len(ids)==c['count']
 fields=['OBJECTID','GEOID10','GEOID20','HH','TotEmp','E5_Ret','E5_Off','E5_Ind','E5_Svc','E5_Ent','D2A_EPHHM']
 features=[];records=[]
 for k in range(0,len(ids),2000):
  p=CACHE/f'{k:05d}.json.gz';selected=ids[k:k+2000]
  if p.exists():
   with gzip.open(p,'rb') as f:raw=f.read()
  else:
   r,j=request({'objectIds':','.join(map(str,selected)),'outFields':','.join(fields),
                'returnGeometry':'true','outSR':3310})
   raw=r.content
   with gzip.open(p,'wb',compresslevel=3) as f:f.write(raw)
  j=json.loads(raw);assert j['spatialReference']['wkid']==3310
  actual=[next(v for n,v in x['attributes'].items() if n.lower()=='objectid') for x in j['features']]
  assert set(actual)==set(selected) and len(actual)==len(selected)
  features.extend(j['features']);records.append({'file':p.name,'count':len(actual),'payload_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p)})
 pd.DataFrame(records).to_csv(OUT/'EPA_DONOR_GEOMETRY_HASHES.csv',index=False)
 renamed=[];gs=[];invalid=0
 lookup={c.lower():c for c in fields}
 for f in features:
  a={lookup[k.lower()]:v for k,v in f['attributes'].items()}
  for c in ['GEOID10','GEOID20']:a[c]=str(int(a[c])).zfill(12)
  g=rings_geometry(f['geometry']['rings'])
  if not g.is_valid:invalid+=1;g=areal(shapely.make_valid(g))
  gs.append(g);renamed.append(a)
 actual=pd.DataFrame(renamed).set_index('GEOID10')
 assert actual.index.is_unique and set(actual.index).issubset(set(src.GEOID10))
 missing=src.loc[~src.GEOID10.isin(actual.index)].copy()
 missing.to_csv(OUT/'EPA_SOURCE_RECORDS_WITHOUT_DONOR_POLYGON.csv',index=False)
 print('EPA records without donor polygon:',missing.to_dict('records'),flush=True)
 assert missing[COUNTS+['TotEmp']].eq(0).all().all(),'Nonzero donor counts cannot be silently omitted.'
 baseline=src.set_index('GEOID10').loc[actual.index]
 assert actual.GEOID20.equals(baseline.GEOID20)
 numeric=COUNTS+['TotEmp','D2A_EPHHM']
 dif=(actual[numeric]-baseline[numeric]).abs().max()
 assert (dif<=1e-8).all(),dif.to_dict()
 # Source polygon order follows features; align it explicitly by GEOID.
 donor=gpd.GeoDataFrame(renamed,geometry=gs,crs=3310).set_index('GEOID10').loc[baseline.index]
 assert np.allclose(baseline[COUNTS[1:]].sum(axis=1),baseline.TotEmp)
 source_h=entropy(baseline[COUNTS]);supported=baseline[COUNTS].gt(0).sum(axis=1).ge(2)
 source_entropy_max=float(np.max(np.abs(source_h[supported]-baseline.loc[supported,'D2A_EPHHM'])))
 assert source_entropy_max<1e-7
 t=tracts();l=land()
 assert t.index.is_unique and l.index.is_unique and set(l.index).issubset(set(t.index))
 # Use the retained 2020 Census water polygons to define a declared common land support.
 water=RESEARCH/'local_joint_feature_extraction_20261009/sources/tl_2020_06037_areawater.zip'
 w=gpd.read_file('/vsizip/'+str(water).removeprefix('\\\\?\\').replace('\\','/')).to_crs(3310)
 w=w.loc[w.AWATER.gt(0)];wtree=STRtree(w.geometry.to_numpy())
 targettree=STRtree(t.geometry.to_numpy())
 cross=[];donorqa=[];donorlands=[]
 for i,(key,row) in enumerate(donor.iterrows()):
  g=row.geometry;hit=wtree.query(g,predicate='intersects')
  gl=areal(g.difference(shapely.union_all(w.geometry.to_numpy()[hit]))) if len(hit) else g
  donorlands.append(gl)
  den=gl.area;total=0
  for ti in targettree.query(gl,predicate='intersects'):
   intersection=overlay(gl,t.geometry.iloc[ti],'intersection',key);a=intersection.area
   if a<=0:continue
   fraction=a/den if den>0 else np.nan;total+=a
   cross.append({'donor_geoid10':key,'donor_geoid2018':row.GEOID20,'tract_id':t.index[ti],
                 'intersection_land_m2':a,'donor_land_m2':den,'allocation_fraction':fraction})
  residual=1-total/den if den>0 else np.nan
  assert residual>=-1e-6,(key,residual)
  donorqa.append({'donor_geoid10':key,'donor_geoid2018':row.GEOID20,'donor_land_m2':den,
                  'target_fraction':total/den if den>0 else np.nan,'outside_target_fraction':max(0,residual) if np.isfinite(residual) else np.nan,
                  'source_households':row.HH,'source_jobs':row.TotEmp})
  if i%1000==0:log(f'EPA donor-land overlay {i}/{len(donor)}')
 x=pd.DataFrame(cross);dq=pd.DataFrame(donorqa)
 assert x.groupby('donor_geoid10').allocation_fraction.sum().le(1+1e-6).all()
 countrows=x.merge(baseline[COUNTS].reset_index(),left_on='donor_geoid10',right_on='GEOID10',validate='many_to_one')
 for c in COUNTS:countrows[c]=countrows[c]*countrows.allocation_fraction
 agg=countrows.groupby('tract_id')[COUNTS].sum()
 # Coverage must use the SAME target land mask in numerator and denominator.
 # Count weights still use whole donor land and actual target tract boundaries.
 donor_union=areal(shapely.union_all(donorlands))
 coverage=pd.Series({key:overlay(row.geometry,donor_union,'intersection',key).area/row.land_geometry_area_m2
                     if row.land_geometry_area_m2>0 else np.nan for key,row in l.iterrows()})
 summed_area=x.groupby('tract_id').intersection_land_m2.sum()
 support=pd.DataFrame({'summed_donor_land_in_tract_m2':summed_area,
                      'target_land_mask_m2':l.land_geometry_area_m2,
                      'union_donor_land_on_target_land_m2':coverage*l.land_geometry_area_m2})
 support['summed_intersection_over_target_mask_fraction']=support.summed_donor_land_in_tract_m2/support.target_land_mask_m2
 support.to_csv(OUT/'EPA_TARGET_LAND_SUPPORT_DIAGNOSTICS.csv',index_label='tract_id')
 assert coverage.loc[~coverage.index.isin(UNRESOLVED)].max()<1+1e-6
 totals=baseline[COUNTS].sum()
 unassigned=baseline[COUNTS].mul(dq.set_index('donor_geoid10').outside_target_fraction,axis=0).sum()
 recovered=agg.sum()+unassigned
 assert np.allclose(totals,recovered,atol=1e-5,rtol=1e-7)
 master=pd.read_csv(OUT/'CANDIDATE_VALUES_2315.csv',usecols=['tract_id'],dtype=str).tract_id.tolist()
 result=pd.DataFrame(index=pd.Index(master,name='tract_id')).join(agg)
 result['epa_activity_total']=result[COUNTS].sum(axis=1,min_count=6)
 result['epa_household_job_activity_mix']=entropy(result[COUNTS])
 result['epa_activity_mix_fixed_six']=entropy(result[COUNTS],fixed=True)
 result['epa_activity_categories_positive']=result[COUNTS].gt(0).sum(axis=1)
 result['epa_donor_land_coverage']=coverage
 result['epa_donor_count']=x.groupby('tract_id').donor_geoid10.nunique()
 split=x.groupby('donor_geoid10').tract_id.nunique().gt(1)
 # Report tiny boundary slivers separately, without deleting or renormalizing them.
 material_split=x.loc[x.allocation_fraction.ge(.01)].groupby('donor_geoid10').tract_id.nunique().gt(1)
 splitrows=countrows.loc[countrows.donor_geoid10.map(split)]
 result['epa_activity_from_split_donors_fraction']=splitrows.groupby('tract_id')[COUNTS].sum().sum(axis=1)/result.epa_activity_total
 result['epa_activity_from_split_donors_fraction']=result.epa_activity_from_split_donors_fraction.fillna(0).where(result.epa_activity_total>0)
 result['epa_measurement_status']='CONDITIONAL_HISTORICAL_COUNTS_LAND_AREA_ALLOCATION'
 result.loc[UNRESOLVED,[c for c in result if c!='epa_measurement_status']]=np.nan
 result.loc[UNRESOLVED,'epa_measurement_status']='UNRESOLVED_TARGET_LAND_GEOMETRY'
 result.rename(columns={c:'epa_allocated_'+c for c in COUNTS},inplace=True)
 result.to_csv(OUT/'EPA_TRACT_ACTIVITY_MIX.csv',float_format='%.15g')
 x.to_csv(OUT/'EPA_DONOR_TO_TRACT_CROSSWALK.csv',index=False,float_format='%.15g')
 dq.to_csv(OUT/'EPA_DONOR_ALLOCATION_QA.csv',index=False,float_format='%.15g')
 dump('EPA_ACTIVITY_CROSSWALK_QA.json',{'donors':len(donor),'cached_source_records':len(src),
   'source_records_without_donor_polygon':len(missing),'missing_polygon_counts':missing[COUNTS].sum().to_dict(),
   'invalid_donor_geometries_repaired':invalid,
   'source_numeric_match_max_differences':dif.to_dict(),'source_entropy_reproduction_max_difference':source_entropy_max,
   'source_GE0ID10_vs_2018_ID_changes':int((donor.index!=donor.GEOID20).sum()),
   'donor_land_overlap_m2':sum(g.area for g in donorlands)-donor_union.area,
   'donor_land_sum_m2':sum(g.area for g in donorlands),'donor_land_union_m2':donor_union.area,
   'coverage_definition':'union of actual donor land intersect identical target land mask / target land mask area; not summed whole-tract donor intersections over a different mask',
   'crosswalk_rows':len(x),'split_donors':int(split.sum()),
   'donors_with_at_least_two_one_percent_intersections':int(material_split.sum()),
   'one_percent_used_only_to_describe_slivers_not_to_change_weights':True,
   'county_source_totals':totals.to_dict(),'county_target_plus_outside_totals':recovered.to_dict(),
   'full_valid':int(result.epa_household_job_activity_mix.notna().sum()),
   'residential_valid':int(result.loc[pd.read_csv(OUT/'CANDIDATE_VALUES_RESIDENTIAL_2291.csv',usecols=['tract_id'],dtype=str).tract_id,'epa_household_job_activity_mix'].notna().sum()),
   'target_land_coverage_quantiles':result.epa_donor_land_coverage.quantile([0,.01,.1,.5,.9,.99,1]).to_dict(),
   'split_activity_fraction_quantiles':result.epa_activity_from_split_donors_fraction.quantile([0,.1,.5,.9,1]).to_dict(),
   'method':'source HH and five job counts multiplied by actual 2018 SLD-donor land intersection / whole donor land; aggregate counts then recompute entropy; no source entropy averaging or prefix matching',
   'time':'2017 LODES jobs, 2014-2018 ACS household estimates; actual 2018 donor polygons; 2020 water support and target tracts',
   'uncertainty':'uniform within-donor land allocation is an estimation assumption, not observed tract activities or validated local accuracy; source survey/location errors remain',
   'outside_target_counts_retained':True,'uncovered_area_not_renormalized':True,'seconds':time.time()-start})
 log('EPA actual-donor geographic allocation and count-conservation QA complete.')

if __name__=='__main__':main()
