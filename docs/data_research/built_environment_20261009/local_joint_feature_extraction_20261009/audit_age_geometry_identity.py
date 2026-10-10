"""Investigate geometry agreement without relaxing the age-transfer rule."""
import time,json
import pandas as pd,numpy as np,pyogrio,shapely
from source_audit import OUT,dump
S=OUT/'sources';u6='/vsizip/'+str(S/'LARIAC6_Buildings_2020.gdb.zip').replace(chr(92),'/')+'/LARIAC6_Buildings_2020.gdb'
new=pyogrio.read_dataframe(u6,layer='LARIAC6_BUILDINGS_2020',max_features=20000,columns=['BLD_ID','CODE','SOURCE','DATE_','STATUS']).query("CODE == 'Building'").to_crs(3310)
new.BLD_ID=new.BLD_ID.astype('string').str.strip()
u4='/vsizip/'+str(S/'LARIAC4_BUILDINGS_2014.zip').replace(chr(92),'/')+'/LARIAC4_BUILDINGS_2014/LARIAC4_BUILDINGS_2014.gdb'
old=pyogrio.read_dataframe(u4,layer='LARIAC4_BUILDINGS_2014',columns=['BLD_ID','CODE','SOURCE','DATE_']).query("CODE == 'Building'")
old.BLD_ID=old.BLD_ID.astype('string').str.strip();dup=old.BLD_ID.duplicated(keep=False);old=old.loc[~dup & old.BLD_ID.isin(new.BLD_ID)].to_crs(3310).set_index('BLD_ID');selected=old.reindex(new.BLD_ID);mask=selected.geometry.notna().to_numpy();new=new.loc[mask];selected=selected.loc[mask]
a=shapely.make_valid(new.geometry.to_numpy());b=shapely.make_valid(selected.geometry.to_numpy());intersection=shapely.area(shapely.intersection(a,b));ar=shapely.area(a);br=shapely.area(b)
d=pd.DataFrame({'BLD_ID':new.BLD_ID.to_numpy(),'IoU':intersection/(ar+br-intersection),'centroid_distance_m':shapely.distance(shapely.centroid(a),shapely.centroid(b)),'new_old_area_ratio':ar/br,'new_source':new.SOURCE.to_numpy(),'old_source':selected.SOURCE.to_numpy(),'new_date':new.DATE_.to_numpy(),'old_date':selected.DATE_.to_numpy(),'new_status':new.STATUS.to_numpy()})
d.to_csv(OUT/'BUILDING_AGE_GEOMETRY_IDENTITY_SAMPLE.csv',index=False)
dump('BUILDING_AGE_GEOMETRY_IDENTITY_DIAGNOSTIC.json',{'sampling':'first20000 source2020 records, deterministic convenience sample, not representative county estimator','matched_records':len(d),'quantiles':{k:d[k].quantile([0,.01,.1,.5,.9,.99,1]).to_dict() for k in ['IoU','centroid_distance_m','new_old_area_ratio']},'IoU_lt_0_9_count':int((d.IoU<.9).sum()),'no_transfer_threshold_changed':True})
print('AGE_IDENTITY_DIAGNOSTIC',len(d),d[['IoU','centroid_distance_m','new_old_area_ratio']].median().to_dict(),flush=True)
