"""Compare optimized exact union areas with direct GEOS on observed source geometries."""
import gzip,pickle,json,time
import pandas as pd,numpy as np,shapely
from source_audit import OUT,dump
from geometry_union_area import UnionArea
start=time.time();files=sorted((OUT/'sources/age2014_tract_clips_v3').glob('*.pkl.gz'));positions=np.linspace(0,len(files)-1,40).astype(int);rows=[]
for i in positions:
 gs=[];p=files[i]
 with gzip.open(p,'rb') as f:
  while True:
   try:h,w=pickle.load(f);gs.append(shapely.from_wkb(w))
   except EOFError:break
 a=UnionArea(gs)
 for label,subset in [('all',gs),('even_indices',gs[::2]),('first_half',gs[:len(gs)//2]),('last_third',gs[len(gs)*2//3:])]:
  exact=shapely.union_all(subset).area;candidate=a.area(subset);rows.append({'tract_id':p.name.split('.')[0],'subset':label,'n_geometries':len(subset),'direct_GEOS_union_area_m2':exact,'component_union_area_m2':candidate,'absolute_error_m2':abs(candidate-exact),'relative_error':abs(candidate-exact)/exact if exact>0 else 0})
 print('UNION_EQUIVALENCE',len(rows),flush=True)
r=pd.DataFrame(rows);r.to_csv(OUT/'UNION_AREA_EQUIVALENCE_AUDIT.csv',index=False,float_format='%.15g');ok=np.allclose(r.direct_GEOS_union_area_m2,r.component_union_area_m2,rtol=1e-11,atol=1e-6)
dump('UNION_AREA_EQUIVALENCE_QA.json',{'all_sampled_areas_match_direct_GEOS':bool(ok),'actual_source_tracts':40,'tested_subsets':len(r),'max_absolute_error_m2':float(r.absolute_error_m2.max()),'max_relative_error':float(r.relative_error.max()),'method':'sum union areas of disconnected positive-overlap components; all real overlaps unioned, no epsilon exclusion','seconds':time.time()-start});assert ok
print('UNION_AREA_EQUIVALENCE_COMPLETE',r.absolute_error_m2.max(),flush=True)
