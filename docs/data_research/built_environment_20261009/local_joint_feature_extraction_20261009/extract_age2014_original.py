"""Age statistics on the original observed 2014 outlines, separate from age transfer to 2020."""
import time,gc,hashlib,gzip,pickle,sys
import numpy as np,pandas as pd,pyogrio,shapely
from shapely import STRtree
from source_audit import OUT,sha,dump
from extract_gis import tracts,land
from geometry_union_area import UnionArea
start=time.time();S=OUT/'sources';source=S/'LARIAC4_BUILDINGS_2014.zip';u='/vsizip/'+str(source).replace(chr(92),'/')+'/LARIAC4_BUILDINGS_2014/LARIAC4_BUILDINGS_2014.gdb';info=pyogrio.read_info(u,layer='LARIAC4_BUILDINGS_2014');t=tracts();l=land();tree=STRtree(t.geometry.to_numpy());cache=S/'age2014_tract_clips_v3';cache.mkdir(exist_ok=True);resume='--resume-cache' in sys.argv;assert resume or not any(cache.iterdir());seen={};conflicts=set();by_use={};invalid=0;missing_geometry=0;dups=0;count=0
for offset in range(0,info['features'],100000):
 d=pyogrio.read_dataframe(u,layer='LARIAC4_BUILDINGS_2014',skip_features=offset,max_features=100000,columns=['CODE','BLD_ID','YearBuilt1','UseType','Roll_Year'])
 d=d.loc[d.CODE.eq('Building')].copy();missing_geometry+=int(d.geometry.isna().sum());d=d.loc[d.geometry.notna()].copy();invalid+=int((~d.geometry.is_valid).sum());d.geometry=d.geometry.make_valid()
 years=pd.to_numeric(d.YearBuilt1,errors='coerce');roll=pd.to_numeric(d.Roll_Year,errors='coerce');valid=years.between(1800,2014)&years.mod(1).eq(0)&(roll.isna()|years.le(roll))
 hs=[hashlib.sha256(w).digest() for w in shapely.to_wkb(shapely.normalize(d.geometry.to_numpy()))];keep=[]
 for i,h in enumerate(hs):
  attr=(float(years.iloc[i]) if valid.iloc[i] else None,str(d.UseType.iloc[i]))
  if h in seen:
   dups+=1
   if seen[h]!=attr:conflicts.add(h)
  else:seen[h]=attr;keep.append(i)
 count+=len(keep)
 if resume:
  if offset%500000==0:print('AGE2014_METADATA',offset,round(time.time()-start,1),flush=True)
  continue
 d=d.iloc[keep].to_crs(3310);hh=[hs[i] for i in keep];pairs=tree.query(d.geometry.to_numpy(),predicate='intersects')
 for ti in np.unique(pairs[1]):
  bi=pairs[0,pairs[1]==ti];clips=shapely.intersection(d.geometry.iloc[bi].to_numpy(),l.geometry.iloc[ti]);areas=shapely.area(clips)
  with gzip.open(cache/(str(t.index[ti])+'.pkl.gz'),'ab',compresslevel=6) as f:
   for j,g,a in zip(bi,clips,areas):
    if a>0:pickle.dump((hh[j],shapely.to_wkb(g)),f,protocol=4)
 gc.collect()
 if offset%500000==0:print('AGE2014',offset,round(time.time()-start,1),flush=True)
dump('AGE2014_AGGREGATION_CHECKPOINT.json',{'source_records':info['features'],'unique_geometry_metadata':count,'raw_geometry_cache_reused':resume,'missing_geometry':missing_geometry,'status':'metadata recovered; tract unions pending'})
rows=[];use_rows=[]
for ti,key in enumerate(t.index):
 if ti%50==0:print('AGE2014_UNION',ti,round(time.time()-start,1),flush=True)
 allg=[];validg=[];pre=[];res=[];resvalid=[];respre=[];useg={};cp=cache/(str(key)+'.pkl.gz');records=[]
 if cp.exists():
  with gzip.open(cp,'rb') as f:
   while True:
    try:h,w=pickle.load(f);g=shapely.from_wkb(w);records.append((h,g))
    except EOFError:break
 for h,g in records:
  allg.append(g)
  if h in conflicts:continue
  year,use=seen[h];useg.setdefault(use,[[],[],[]])[0].append(g)
  if use=='Residential':res.append(g)
  if year is not None:
   validg.append(g);useg[use][1].append(g)
   if use=='Residential':resvalid.append(g)
   if year<1970:
    pre.append(g);useg[use][2].append(g)
    if use=='Residential':respre.append(g)
 # Use geographic union areas, so overlapping duplicate outlines do not inflate area.
 union=UnionArea(allg);a=union.area(allg);v=union.area(validg);p=union.area(pre);r=union.area(res);rv=union.area(resvalid);rp=union.area(respre)
 rows.append({'tract_id':key,'all_use2014_pre1970_area_share':p/v if v>0 else np.nan,'all_use2014_age_coverage':v/a if a>0 else np.nan,'all_use2014_footprint_union_area_m2':a,'all_use2014_valid_age_area_m2':v,'all_use2014_pre1970_area_m2':p,'all_use2014_missing_age_area_m2':a-v,'all_use2014_pre1970_lower_bound':p/a if a>0 else np.nan,'all_use2014_pre1970_upper_bound':(p+a-v)/a if a>0 else np.nan,'residential2014_pre1970_area_share':rp/rv if rv>0 else np.nan,'residential2014_age_coverage':rv/r if r>0 else np.nan,'age2014_status':'OBSERVED_2014_ASSOCIATED_ASSESSOR_YEAR_WITH_MISSING_AGE_AREA','age2014_scope':'2014 outlines only, no transfer to 2020 and no claim of complete all-building ages'})
 if ti%50==0:pd.DataFrame(rows).to_csv(OUT/'BUILDING_AGE_2014_RESUMED_PARTIAL.csv',index=False,na_rep='',float_format='%.15g')
 for use,(ag,vg,pg) in useg.items():
  aa=union.area(ag);vv=union.area(vg);pp=union.area(pg)
  use_rows.append({'tract_id':key,'use':use,'outline_union_area_m2':aa,'valid_age_union_area_m2':vv,'pre1970_union_area_m2':pp,'valid_age_area_coverage':vv/aa if aa>0 else np.nan})
d=pd.DataFrame(rows);d.to_csv(OUT/'BUILDING_AGE_2014_ORIGINAL_TRACTS.csv',index=False,na_rep='',float_format='%.15g');pd.DataFrame(use_rows).to_csv(OUT/'BUILDING_AGE_2014_BY_USE_COVERAGE.csv',index=False)
dump('BUILDING_AGE_2014_QA.json',{'source_sha256':sha(source),'unique_building_geometries':count,'exact_geometry_duplicates_removed':dups,'conflicting_age_or_use_geometries_withheld':len(conflicts),'invalid_repaired':invalid,'missing_geometry_excluded_from_area':missing_geometry,'vintage':2014,'area_union_implementation':'exact union areas of disjoint positive-overlap components; independent GEOS equivalence audit required','area_union_rule':'all, valid-age and pre1970 unions clipped to tract land; exact-geometry age/use conflicts withheld from known-age numerator','coverage_quantiles':d.all_use2014_age_coverage.quantile([0,.01,.5,.99,1]).to_dict(),'missing_age_imputed':False,'not_2020_age_transfer':True,'seconds':time.time()-start})
print('AGE2014_COMPLETE',len(d),d.all_use2014_age_coverage.median(),flush=True)
