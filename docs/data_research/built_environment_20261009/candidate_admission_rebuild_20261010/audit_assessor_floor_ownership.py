"""Audit assessment identities and shared parcel geometry without inventing buildings."""
from common import *
import pandas as pd,numpy as np,geopandas as gpd,shapely,gzip,requests,time
from shapely import STRtree
from measure_vectors import tracts,assign
from measure_scag2020 import geometry as rings_geometry
URL='https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Parcels_2022Roll/FeatureServer/0'

def records():
 cache=RAW/'assessor2022_assigned_nonpersonal.pkl'
 if cache.exists():
  q=json.loads((OUT/'ASSESSOR_ASSIGNED_CACHE_QA.json').read_text(encoding='utf-8'))
  assert sha(cache)==q['cache_sha256']
  assert sha(OUT/'ASSESSOR_CHUNK_HASHES.csv')==q['source_manifest_sha256']
  d=pd.read_pickle(cache);assert d.AIN.is_unique and len(d)==q['rows']
  return d
 t=tracts();ids=t.index.to_numpy();tree=STRtree(t.geometry.to_numpy());chunks=[]
 manifest=pd.read_csv(OUT/'ASSESSOR_CHUNK_HASHES.csv').set_index('chunk_start')
 for i,p in enumerate(sorted((RAW/'assessor2022_v2').glob('[0-9]*.json.gz'))):
  k=int(p.stem.split('.')[0]);assert sha(p)==manifest.loc[k,'compressed_sha256']
  with gzip.open(p,'rb') as f:raw=f.read()
  assert hashlib.sha256(raw).hexdigest()==manifest.loc[k,'payload_sha256']
  j=json.loads(raw);d=pd.DataFrame([x['attributes'] for x in j['features']])
  assert d.RollYear.eq('2022').all()
  points=gpd.GeoSeries(gpd.points_from_xy(d.CENTER_LON,d.CENTER_LAT),crs=4326).to_crs(3310)
  hit=assign(points.to_numpy(),tree,ids);a=d.iloc[hit[0]].copy();a['tract_id']=ids[hit[1]];chunks.append(a)
  if i%200==0:log(f'Assessor cached identity audit chunks {i}/{len(manifest)}')
 d=pd.concat(chunks,ignore_index=True);assert d.AIN.is_unique
 d.to_pickle(cache)
 dump('ASSESSOR_ASSIGNED_CACHE_QA.json',{'source_manifest_sha256':sha(OUT/'ASSESSOR_CHUNK_HASHES.csv'),'cache_sha256':sha(cache),'rows':len(d),'personal_fields':False})
 return d

def main():
 start=time.time();d=records();d['area_m2']=pd.to_numeric(d.SQFTmain,errors='coerce')*.09290304
 d['positive_area']=d.area_m2.gt(0);d['multi_line']=d.totBuildingDataLines.gt(1)
 d['shared_point']=d.duplicated(['CENTER_LAT','CENTER_LON'],keep=False)
 # Point equality is a screening flag; it is not a building deduplication key.
 positive=d.loc[d.positive_area].copy()
 groups=positive.groupby(['CENTER_LAT','CENTER_LON'],dropna=False)
 g=groups.agg(records=('AIN','size'),ain_unique=('AIN','nunique'),
              area_sum_m2=('area_m2','sum'),area_max_m2=('area_m2','max'),
              area_distinct=('SQFTmain','nunique'),units_sum=('Units','sum'),
              use_types=('UseType',lambda x:';'.join(sorted(set(x.dropna())))),
              tract_id=('tract_id','first'),tracts=('tract_id','nunique'))
 g['point_collapse_omitted_area_m2']=g.area_sum_m2-g.area_max_m2
 d['exact_nonidentity_attribute_repeat']=d.duplicated(
  ['CENTER_LAT','CENTER_LON','UseType','UseCode','SQFTmain','YearBuilt','EffectiveYearBuilt','Units','totBuildingDataLines'],keep=False)
 rows=[]
 master=pd.read_csv(OUT/'CANDIDATE_VALUES_2315.csv',usecols=['tract_id'],dtype=str).tract_id
 for key in master:
  a=d.loc[d.tract_id.eq(key)];v=a.loc[a.positive_area];den=v.area_m2.sum()
  # This restricted assessment subset is explicitly not a complete FAR estimate.
  strict=v.loc[v.totBuildingDataLines.eq(1)&~v.UseType.eq('CND')&~v.shared_point]
  sub=g.loc[g.tract_id.eq(key)]
  rows.append({'tract_id':key,'assessor2022_positive_main_area_m2':den,
   'assessor2022_identity_unique_ain':len(a),'assessor2022_shared_point_record_fraction':a.shared_point.mean() if len(a) else np.nan,
   'assessor2022_shared_point_main_area_fraction':v.loc[v.shared_point].area_m2.sum()/den if den>0 else np.nan,
   'assessor2022_condo_main_area_fraction':v.loc[v.UseType.eq('CND')].area_m2.sum()/den if den>0 else np.nan,
   'assessor2022_multiline_main_area_fraction':v.loc[v.multi_line].area_m2.sum()/den if den>0 else np.nan,
   'assessor2022_exact_attribute_repeat_main_area_fraction':v.loc[v.exact_nonidentity_attribute_repeat].area_m2.sum()/den if den>0 else np.nan,
   'assessor2022_restricted_singleline_noncondo_nonshared_main_area_m2':strict.area_m2.sum(),
   'assessor2022_restricted_main_area_support_fraction':strict.area_m2.sum()/den if den>0 else np.nan,
   'assessor2022_naive_pointcollapse_removed_main_area_fraction':sub.point_collapse_omitted_area_m2.sum()/den if den>0 else np.nan,
   'assessor2022_floor_area_status':'NO_CERTIFIED_GROSS_FLOOR_AREA_OR_STRUCTURE_ID',
   'assessor2022_duplicate_assignment_status':'AIN_UNIQUE_SHARED_POINTS_NOT_DEDUPLICATED_AS_BUILDINGS'})
 pd.DataFrame(rows).to_csv(OUT/'ASSESSOR2022_FLOOR_IDENTITY_DIAGNOSTICS.csv',index=False,float_format='%.15g')
 shared=g.loc[g.records.gt(1)].copy()
 shared['group_id']=[hashlib.sha256(f'{a:.10f},{b:.10f}'.encode()).hexdigest() for a,b in shared.index]
 shared.reset_index(drop=True).to_csv(OUT/'ASSESSOR2022_SHARED_LOCATION_GROUPS.csv',index=False,float_format='%.15g')
 # Bounded deterministic verification sample: 20 largest condo groups plus 20 sampled others.
 c=shared.loc[shared.use_types.str.contains('CND')].copy()
 big=c.sort_values(['records','group_id'],ascending=[False,True]).head(20)
 remainder=c.loc[~c.group_id.isin(big.group_id)].sort_values('group_id')
 selected=pd.concat([big,remainder.sample(n=min(20,len(remainder)),random_state=20261010)])
 CACHE=RAW/'assessor2022_parcel_identity_samples';CACHE.mkdir(exist_ok=True)
 samples=[];payloads=[]
 for n,((lat,lon),row) in enumerate(selected.iterrows()):
  members=d.loc[d.CENTER_LAT.eq(lat)&d.CENTER_LON.eq(lon)].AIN.tolist()
  features=[]
  for k in range(0,len(members),500):
   subset=members[k:k+500];p=CACHE/f'{row.group_id}_{k:05d}.json.gz'
   if p.exists():
    with gzip.open(p,'rb') as f:raw=f.read()
   else:
    where='AIN IN ('+','.join("'"+x+"'" for x in subset)+')'
    r=requests.post(URL+'/query',data={'f':'json','where':where,'outFields':'AIN,APN,Roll_Year',
               'outSR':3310,'returnGeometry':'true','resultRecordCount':2000},timeout=(15,90))
    r.raise_for_status();raw=r.content
    with gzip.open(p,'wb',compresslevel=3) as f:f.write(raw)
   j=json.loads(raw);assert 'error' not in j,j.get('error');assert not j.get('exceededTransferLimit',False)
   features+=j['features'];payloads.append({'file':p.name,'payload_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'requested_ain':len(subset),'returned_rows':len(j['features'])})
  hashes=[];returned=[];rolls=set();apns=set()
  for f in features:
   a=f['attributes'];returned.append(a['AIN']);apns.add(a.get('APN'));rolls.add(str(a.get('Roll_Year')))
   if f.get('geometry'):
    gg=rings_geometry(f['geometry']['rings'])
    hashes.append(hashlib.sha256(shapely.to_wkb(shapely.normalize(shapely.make_valid(gg)))).hexdigest())
  assert set(returned).issubset(set(members))
  samples.append({'group_id':row.group_id,'selection':'largest20' if row.group_id in set(big.group_id) else 'fixed_seed_sample20',
   'cached_assessment_ain':len(members),'returned_parcel_rows':len(returned),'unique_returned_ain':len(set(returned)),
   'unique_apn':len(apns),'unique_normalized_parcel_geometries':len(set(hashes)),
   'roll_years':';'.join(sorted(rolls)),'main_area_sum_m2':row.area_sum_m2,
   'interpretation':'shared cadastral geometry is not a physical-building ID or proof of duplicate floor area'})
  if n%10==0:log(f'Assessor2022 exact parcel identity sample {n}/{len(selected)}')
 pd.DataFrame(samples).to_csv(OUT/'ASSESSOR2022_PARCEL_GEOMETRY_IDENTITY_SAMPLE.csv',index=False)
 pd.DataFrame(payloads).to_csv(OUT/'ASSESSOR2022_PARCEL_SAMPLE_HASHES.csv',index=False)
 metadata=json.loads((OUT/'source_evidence/Assessor_layer.json').read_text(encoding='utf-8'))
 floorfields=[x for x in metadata['fields'] if any(a in x['name'].lower() for a in ['sqft','building','year','units'])]
 dump('ASSESSOR_FLOOR_AREA_AND_OWNERSHIP_QA.json',{'county_assignment_records':len(d),'unique_AIN':d.AIN.nunique(),
  'shared_coordinate_groups':len(shared),'same_nonidentity_attribute_repeat_records':int(d.exact_nonidentity_attribute_repeat.sum()),
  'multiline_records':int(d.multi_line.sum()),'condo_records':int(d.UseType.eq('CND').sum()),
  'parcel_geometry_sample_groups':len(samples),'sample_shared_geometry_groups':sum(x['unique_normalized_parcel_geometries']<x['unique_returned_ain'] for x in samples),
  'actual_roll_area_fields':floorfields,'missing_required_evidence':['2022 structure/building-line identifiers and areas','certified gross-floor-area inclusion/exclusion convention','unit versus shared/common building-area accounting','complete government/exempt stock coverage'],
  'disposition':'PENDING_DATA','candidate_values':'gross FAR remains null; measured Main Square Footage and restricted subsets are diagnostics only',
  'no_coordinate_or_attribute_deduplication_rule_adopted':True,'geometry_samples_do_not_validate_countywide_building_ownership':True,'seconds':time.time()-start})
 log('Assessor floor semantics and shared-identity diagnostics complete; gross FAR not forced into admission.')

if __name__=='__main__':main()
