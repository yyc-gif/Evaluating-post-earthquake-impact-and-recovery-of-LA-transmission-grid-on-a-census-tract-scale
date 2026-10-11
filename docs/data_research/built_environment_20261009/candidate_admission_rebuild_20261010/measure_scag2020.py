"""ALU20 exclusive-area overlay using the reviewed historical-area convention."""
from common import *
import gzip,pickle,time,json,gc
import pandas as pd,numpy as np,shapely
from shapely.geometry import Polygon,MultiLineString
from shapely import STRtree
from measure_rasters import geometry as land,UNRESOLVED
from measure_vectors import tracts
CLASSES=['residential','commercial_office','industrial','institutional_public','transportation_utility','open_space_recreation','vacant_undeveloped','agriculture','mixed_use','under_construction','protected_undevelopable']
OVERLAY_REPAIRS=[]
def broad(code):
 code=int(code)
 if 1100<=code<1200:return 'residential'
 if code in [1272,1275]:return 'vacant_undeveloped'
 if code in [1273,1276]:return 'transportation_utility'
 if 1240<=code<1300:return 'institutional_public'
 if 1200<=code<1240:return 'commercial_office'
 if 1300<=code<1400:return 'industrial'
 if 1400<=code<1500:return 'transportation_utility'
 if 1500<=code<1700:return 'mixed_use'
 if 1700<=code<1800:return 'under_construction'
 if 1800<=code<1900:return 'open_space_recreation'
 if code==1900 or 3000<=code<4000:return 'vacant_undeveloped'
 if 2000<=code<3000:return 'agriculture'
 if 4000<=code<5000:return 'water'
 if code==8888:return 'protected_undevelopable'
 return 'unclassified'

def geometry(rings):
 if len(rings)==1:return Polygon(rings[0])
 return shapely.build_area(MultiLineString(rings))

def areal(g):
 if g.is_empty or g.area<=0:return shapely.Polygon()
 if g.geom_type in ['Polygon','MultiPolygon']:return g
 parts=[]
 for part in shapely.get_parts(g):
  if part.geom_type in ['Polygon','MultiPolygon']:parts.append(part)
  elif part.geom_type=='GeometryCollection':
   a=areal(part)
   if a.area>0:parts.append(a)
 return shapely.union_all(parts) if parts else shapely.Polygon()

def overlay(a,b,operation,tract_id):
 try:return areal(getattr(shapely,operation)(areal(a),areal(b)))
 except shapely.errors.GEOSException as e:
  # Only a failed overlay uses sub-millimetre precision; record the area perturbation.
  aa=shapely.set_precision(shapely.make_valid(areal(a)),grid_size=0.0001)
  bb=shapely.set_precision(shapely.make_valid(areal(b)),grid_size=0.0001)
  OVERLAY_REPAIRS.append({'tract_id':tract_id,'operation':operation,'grid_m':.0001,'input_a_area_change_m2':aa.area-a.area,'input_b_area_change_m2':bb.area-b.area,'error':str(e)})
  return areal(getattr(shapely,operation)(aa,bb))

def main():
 start=time.time();complete=json.loads((OUT/'SCAG2020_ACQUISITION_COMPLETE.json').read_text(encoding='utf-8'));manifest=pd.read_csv(OUT/'SCAG2020_CHUNK_HASHES.csv')
 assert manifest['count'].sum()==complete['count']
 ids=pd.read_csv(OUT/'CANDIDATE_VALUES_2315.csv',usecols=['tract_id'],dtype=str).tract_id.tolist();t=tracts().loc[ids];l=land().loc[ids]
 meta=json.loads((OUT/'source_evidence/SCAG2020_layer_current.json').read_text(encoding='utf-8'));codes={int(x['code']):x['name'] for x in next(x for x in meta['fields'] if x['name']=='ALU20')['domain']['codedValues'] if str(x['code']).strip().isdigit()}
 mapping=pd.DataFrame([{'ALU20':k,'source_description':v,'broad_class':broad(k),'source':'official ALU20 coded domain','mixed_use':'retained as mixed_use, not split'} for k,v in sorted(codes.items())]);mapping.to_csv(OUT/'SCAG2020_SOURCE_CODE_MAPPING.csv',index=False)
 cache=RAW/'scag2020_tract_clips';cache.mkdir(exist_ok=True)
 resume=(cache/'GEOMETRY_COMPLETE.json').exists()
 if not resume:assert not any(cache.iterdir()),'Retain partial cache; inspect before resume.'
 tree=STRtree(t.geometry.to_numpy());seen={};counts={'raw_records':0,'stack_gt1_records':0,'exact_geometry_duplicates':0,'different_ALU20_duplicates':0,'different_code_same_broad_class':0,'invalid_repaired':0,'empty_geometry':0,'missing_geometry':0};observed={};years={};sources={}
 for rec in manifest.itertuples():
  p=RAW/'scag2020_chunks'/f'{rec.chunk:04d}.json.gz';assert sha(p)==rec.gzip_sha256
  with gzip.open(p,'rb') as f:data=f.read()
  assert hashlib.sha256(data).hexdigest()==rec.response_sha256
  j=json.loads(data)
  for f in j['features']:
   a=f['attributes'];counts['raw_records']+=1;counts['stack_gt1_records']+=int((a.get('STACK') or 0)>1);raw=a.get('ALU20');c=int(raw) if raw and str(raw).isdigit() else -1;b=broad(c);observed[c]=observed.get(c,0)+1
   for dic,key in [(years,'YEAR'),(sources,'ALU20_SRC')]:v=str(a.get(key));dic[v]=dic.get(v,0)+1
   if not f.get('geometry'):counts['missing_geometry']+=1;continue
   g=geometry(f['geometry']['rings'])
   if not g.is_valid:counts['invalid_repaired']+=1;g=shapely.make_valid(g)
   if g.is_empty or g.area<=0:counts['empty_geometry']+=1;continue
   h=hashlib.sha256(shapely.to_wkb(shapely.normalize(g))).digest()
   if h in seen:
    counts['exact_geometry_duplicates']+=1;oldbs,oldc=seen[h]
    if oldc!=c:counts['different_ALU20_duplicates']+=1;counts['different_code_same_broad_class']+=int(b in oldbs)
    oldbs.add(b);continue
   seen[h]=(set([b]),c)
   if not resume:
    wkb=shapely.to_wkb(g)
    for ti in tree.query(g,predicate='intersects'):
     with gzip.open(cache/(str(t.index[ti])+'.pkl.gz'),'ab',compresslevel=3) as z:pickle.dump((h,wkb),z,protocol=4)
  if rec.chunk%100==0:log(f'SCAG2020 geometry {counts["raw_records"]}/{complete["count"]}; {time.time()-start:.1f}s')
 assert counts['raw_records']==complete['count']
 if not resume:(cache/'GEOMETRY_COMPLETE.json').write_text(json.dumps({'source_manifest_sha256':sha(OUT/'SCAG2020_CHUNK_HASHES.csv')}))
 else:assert json.loads((cache/'GEOMETRY_COMPLETE.json').read_text(encoding='utf-8'))['source_manifest_sha256']==sha(OUT/'SCAG2020_CHUNK_HASHES.csv')
 rows=[]
 for ti,key in enumerate(t.index):
  cp=cache/(str(key)+'.pkl.gz');entries=[];by={k:[] for k in CLASSES+['water','unclassified','stack_conflict']}
  if cp.exists():
   with gzip.open(cp,'rb') as z:
    while True:
     try:h,wkb=pickle.load(z);entries.append((seen[h][0],shapely.from_wkb(wkb)))
     except EOFError:break
  for cs,g in entries:by[next(iter(cs)) if len(cs)==1 else 'stack_conflict'].append(g)
  unions={k:overlay(shapely.union_all([areal(g) for g in v]),t.geometry.iloc[ti],'intersection',key) for k,v in by.items()}
  whole=areal(shapely.union_all(list(unions.values())));cross=shapely.Polygon();previous=shapely.Polygon()
  for k in CLASSES+['water','unclassified']:
   cross=areal(shapely.union_all([cross,overlay(previous,unions[k],'intersection',key)]));previous=areal(shapely.union_all([previous,unions[k]]))
  conflict=areal(shapely.union_all([unions['stack_conflict'],cross]));effective={k:overlay(overlay(unions[k],conflict,'difference',key),l.geometry.iloc[ti],'intersection',key) for k in CLASSES};areas={k:g.area for k,g in effective.items()};classified=sum(areas.values());landarea=l.land_geometry_area_m2.iloc[ti]
  pp=np.array(list(areas.values()))/classified if classified>0 else np.full(len(CLASSES),np.nan)
  row={'tract_id':key,'scag2020_classified_land_entropy':-float(np.sum(pp[pp>0]*np.log(pp[pp>0])))/np.log(11) if classified>0 else np.nan,'scag2020_classified_area_m2':classified,'scag2020_classified_land_coverage':classified/landarea if landarea>0 else np.nan,'scag2020_unclassified_land_area_m2':overlay(unions['unclassified'],l.geometry.iloc[ti],'intersection',key).area,'scag2020_ambiguous_land_area_m2':overlay(conflict,l.geometry.iloc[ti],'intersection',key).area,'scag2020_mapped_water_area_m2':unions['water'].area,'scag2020_parcel_gap_area_m2':max(0,t.geometry.iloc[ti].area-whole.area),'scag2020_land_geometry_area_m2':landarea,'scag2020_unique_geometries':len(entries),'scag2020_geometry_status':'UNRESOLVED_GEOMETRY' if key in UNRESOLVED else 'QUALIFIED_CLASSIFIED_LAND_MEASUREMENT'}
  for k,a in areas.items():row['scag2020_'+k+'_area_m2']=a;row['scag2020_'+k+'_land_share']=a/landarea if landarea>0 else np.nan;row['scag2020_'+k+'_classified_share']=a/classified if classified>0 else np.nan
  assert classified<=landarea+1e-4
  if key in UNRESOLVED:
   for c,v in row.items():
    if c not in ['tract_id','scag2020_geometry_status']:row[c]=np.nan
  rows.append(row)
  if ti%200==0:log(f'SCAG2020 exclusive overlay {ti}/{len(t)}')
 result=pd.DataFrame(rows);result.to_csv(OUT/'SCAG2020_TRACT_LAND_USE.csv',index=False,float_format='%.15g')
 counts.update({'source_year_counts':years,'ALU20_source_counts':sources,'dictionary_missing_codes':sorted(set(observed)-set(codes)),'classified_coverage_quantiles':result.scag2020_classified_land_coverage.quantile([0,.01,.1,.5,.9,.99,1]).to_dict(),'ambiguous_land_area_m2':result.scag2020_ambiguous_land_area_m2.sum(),'parcel_gap_area_m2':result.scag2020_parcel_gap_area_m2.sum(),'full_domain':len(result),'residential_domain':2291,'unresolved_land_geometry':UNRESOLVED,'entropy_K':11,'stack_rule':'same normalized geometry one broad class counted once; broad-class conflicts withheld; all remaining class unions made exclusive','cross_class_rule':'overlap withheld from every competing category','denominator':'exclusive classified parcel land for entropy; independently established tract land for coverage','overlay_repairs':OVERLAY_REPAIRS,'seconds':time.time()-start})
 pd.DataFrame([{'ALU20':c,'records':n,'broad_class':broad(c),'in_dictionary':c in codes} for c,n in sorted(observed.items())]).to_csv(OUT/'SCAG2020_OBSERVED_CODE_COUNTS.csv',index=False)
 dump('SCAG2020_GEOMETRY_AND_COVERAGE_QA.json',counts);log('SCAG2020 exclusive classification and coverage QA complete.')
if __name__=='__main__':main()
