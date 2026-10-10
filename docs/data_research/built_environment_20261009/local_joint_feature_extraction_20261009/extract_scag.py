"""Non-overlapping SCAG historical land-use areas; stacked records are audited."""
import gzip,json,hashlib,re,time,pickle,gc,sys
from html.parser import HTMLParser
import pandas as pd,numpy as np,shapely
from shapely.geometry import Polygon,MultiLineString
from shapely import STRtree
from source_audit import ROOT,OUT,dump,sha
from extract_gis import tracts,land
CLASSES=['residential','commercial_office','industrial','institutional_public','transportation_utility','open_space_recreation','vacant_undeveloped','agriculture','mixed_use','under_construction','protected_undevelopable']
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
class Text(HTMLParser):
 def __init__(self):super().__init__();self.data=[]
 def handle_data(self,s):self.data.append(s)
def geometry(rings):
 if len(rings)==1:return Polygon(rings[0])
 return shapely.build_area(MultiLineString(rings))
OVERLAY_REPAIRS=[]
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
def run():
 start=time.time();complete=json.loads((OUT/'SCAG_ACQUISITION_COMPLETE.json').read_text(encoding='utf-8'));assert complete['total_features']==2406373
 meta=json.loads((OUT/'sources/SCAG2019_metadata.json').read_text(encoding='utf-8'));parser=Text();parser.feed(meta['description']);codes={}
 for text in parser.data:
  match=re.match(r'^\s*(\d{4})\s+(.+)',text)
  if match:codes[int(match[1])]=match[2]
 pd.DataFrame([{'LU19':k,'SCAG_description':v,'broad_class':broad(k),'mixed_use_allocation':('unresolved mixture retained as mixed_use, not split into guessed shares' if broad(k)=='mixed_use' else 'not applicable; source code assigned to the stated broad class'),'source':'SCAG2019 layer data dictionary'} for k,v in sorted(codes.items())]).to_csv(OUT/'SCAG_SOURCE_CODE_MAPPING.csv',index=False)
 mapping=pd.read_csv(OUT/'SCAG_SOURCE_CODE_MAPPING.csv');mapping['internal_bucket']=mapping.LU19;mapping=pd.concat([mapping,pd.DataFrame([{'LU19':None,'SCAG_description':'Missing or nonnumeric source LU19; blank raw attribute retained','broad_class':'unclassified','mixed_use_allocation':'not classified; no invented land use','source':'SCAG2019 actual source records','internal_bucket':-1}])],ignore_index=True);mapping.to_csv(OUT/'SCAG_SOURCE_CODE_MAPPING.csv',index=False,na_rep='')
 l=land();t=tracts();cache=OUT/'sources/scag_tract_geometries_v2';cache.mkdir(exist_ok=True);resume='--resume-geometry' in sys.argv;assert resume or not any(cache.iterdir()),'Existing cache retained; pass --resume-geometry';tree=STRtree(t.geometry.to_numpy());buckets=[{} for _ in range(len(t))];seen={};observed={};invalid=0;empty=0;missing=0;stacked=0;duplicate=0;diffcode=0;same_broad_diffcode=0;unrecognized=set();rawcount=0
 for chunk in complete['records']:
  p=OUT/'sources/scag_la_chunks'/f"{chunk['chunk']:04d}.json.gz"
  with gzip.open(p,'rb') as f:data=json.load(f)
  for f in data['features']:
   rawcount+=1;a=f['attributes'];stacked+=int(a['STACK']>1);value=pd.to_numeric(a['LU19'],errors='coerce');c=int(value) if pd.notna(value) else -1;b=broad(c);observed[c]=observed.get(c,0)+1
   if c not in codes:unrecognized.add(c)
   if not f.get('geometry'):missing+=1;continue
   g=geometry(f['geometry']['rings'])
   if not g.is_valid:invalid+=1;g=shapely.make_valid(g)
   if g.is_empty or g.area<=0:empty+=1;continue
   h=hashlib.sha256(shapely.to_wkb(shapely.normalize(g))).digest()
   if h in seen:
    duplicate+=1;oldb,oldc,idx=seen[h]
    if oldc!=c:diffcode+=1;same_broad_diffcode+=int(b in oldb)
    oldb.add(b)
    continue
   hit=[] if resume else tree.query(g,predicate='intersects');idx=[]
   for ti in hit:
    # Keep whole geometry for union; clip to the exact tract at aggregation.

    with gzip.open(cache/(str(t.index[ti])+'.pkl.gz'),'ab',compresslevel=3) as file:pickle.dump((h,shapely.to_wkb(g)),file,protocol=4)
    idx.append((int(ti),h))
   seen[h]=(set([b]),c,idx)
  if chunk['chunk']%100==0:print('SCAG_GEOMETRY',rawcount,'sec',round(time.time()-start,1),flush=True)
 rows=[]
 for ti,key in enumerate(t.index):
  by={k:[] for k in CLASSES+['water','unclassified','stack_conflict']}
  cp=cache/(str(key)+'.pkl.gz');entries=[]
  if cp.exists():
   with gzip.open(cp,'rb') as file:
    while True:
     try:h,wkb=pickle.load(file);entries.append((seen[h][0],shapely.from_wkb(wkb)))
     except EOFError:break
  for cs,g in entries:
   group=next(iter(cs)) if len(cs)==1 else 'stack_conflict';by[group].append(g)
  unions={k:overlay(shapely.union_all([areal(g) for g in v]),t.geometry.iloc[ti],'intersection',key) for k,v in by.items()}
  raw_area=float(shapely.area(shapely.intersection(np.array([g for _,g in entries],dtype=object),t.geometry.iloc[ti])).sum()) if entries else 0.;whole=shapely.union_all(list(unions.values()));conflict=unions['stack_conflict'];cross=shapely.GeometryCollection()
  # An area claimed by different broad categories is not assigned arbitrarily.
  seen_union=shapely.GeometryCollection()
  for k in CLASSES+['water','unclassified']:
   cross=areal(shapely.union_all([cross,overlay(seen_union,unions[k],'intersection',key)]));seen_union=areal(shapely.union_all([seen_union,unions[k]]))
  conflict=areal(shapely.union_all([conflict,cross]));effective={k:overlay(overlay(unions[k],conflict,'difference',key),l.geometry.iloc[ti],'intersection',key) for k in CLASSES};areas={k:g.area for k,g in effective.items()};classified=sum(areas.values());land_area=l.land_geometry_area_m2.iloc[ti];ps=np.array(list(areas.values()))/classified if classified>0 else np.full(len(CLASSES),np.nan);entropy=-float(np.sum(ps[ps>0]*np.log(ps[ps>0])))/np.log(len(CLASSES)) if classified>0 else np.nan
  row={'tract_id':key,'land_use_entropy':entropy,'land_use_entropy_K':len(CLASSES),'land_use_classified_area_m2':classified,'land_use_classified_land_coverage':classified/land_area if land_area>0 else np.nan,'parcel_union_tract_area_m2':whole.area,'unique_geometry_overlap_area_m2':max(0,raw_area-whole.area),'parcel_gap_area_m2':max(0,t.geometry.iloc[ti].area-whole.area),'unclassified_land_area_m2':shapely.intersection(unions['unclassified'],l.geometry.iloc[ti]).area,'ambiguous_overlap_land_area_m2':shapely.intersection(conflict,l.geometry.iloc[ti]).area,'scag_mapped_water_area_m2':unions['water'].area,'land_geometry_area_m2':land_area,'parcel_unique_geometries_intersecting':len(entries),'land_use_status':'OBSERVED_HISTORICAL_AREA_CLASSIFICATION_WITH_COVERAGE_LIMITS','entropy_domain':'all 11 predeclared exclusive classified LAND categories; unknown, water and ambiguous overlap excluded'}
  for k,a in areas.items():row[k+'_area_m2']=a;row[k+'_area_share']=a/land_area if land_area>0 else np.nan;row[k+'_classified_share']=a/classified if classified>0 else np.nan
  assert classified<=land_area+1e-4
  rows.append(row);buckets[ti]={}
  if ti%200==0:print('SCAG_UNION',ti,flush=True)
 result=pd.DataFrame(rows);result.to_csv(OUT/'SCAG_TRACT_LAND_USE.csv',index=False,na_rep='',float_format='%.15g');pd.DataFrame([{'LU19':c,'records':n,'broad_class':broad(c),'in_dictionary':c in codes} for c,n in sorted(observed.items())]).to_csv(OUT/'SCAG_OBSERVED_CODE_COUNTS.csv',index=False)
 dump('SCAG_GEOMETRY_QA.json',{'raw_records':rawcount,'stack_gt1_records':stacked,'exact_normalized_geometry_duplicate_records':duplicate,'duplicate_with_different_LU19':diffcode,'different_code_same_broad_class':same_broad_diffcode,'invalid_repaired':invalid,'empty_geometry':empty,'missing_geometry':missing,'codes_missing_dictionary':sorted(unrecognized),'all_area_categories':CLASSES,'entropy_K':len(CLASSES),'entropy_definition':'-sum(p_i log(p_i))/log(11); p_i = exclusive class land area / all exclusive classified land area. Includes undeveloped categories; not developed-only, no record counts.','stack_rule':'identical geometry same broad class counted once; conflicting broad classes withheld as ambiguous area, not discarded indiscriminately; non-identical STACK>1 polygons retained and unioned','cross_class_overlap_rule':'all conflicting geographic area removed from exclusive categories and reported separately','cross_tract_rule':'equal-area EPSG3310 geometry intersection, never GEOID20 prefix allocation','classified_coverage_quantiles':result.land_use_classified_land_coverage.quantile([0,.01,.5,.99,1]).to_dict(),'ambiguous_overlap_total_m2':float(result.ambiguous_overlap_land_area_m2.sum()),'parcel_gaps_total_m2':float(result.parcel_gap_area_m2.sum()),'overlay_numeric_repairs':OVERLAY_REPAIRS,'non_areal_intersections':'boundary lines and points excluded before area overlays','seconds':time.time()-start})
if __name__=='__main__':run()
