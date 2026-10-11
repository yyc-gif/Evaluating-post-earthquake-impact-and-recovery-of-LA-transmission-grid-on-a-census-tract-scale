"""Coverage/error inventories from cached source attributes; no new measurements fitted."""
from common import *
import pandas as pd,numpy as np,gzip,pyogrio

def main():
 rows=[]
 for p in sorted((RAW/'assessor2022_v2').glob('*.json.gz')):
  with gzip.open(p,'rb') as h:j=json.load(h)
  d=pd.DataFrame([x['attributes'] for x in j['features']]);assert d.RollYear.eq('2022').all()
  y=pd.to_numeric(d.YearBuilt,errors='coerce');a=pd.to_numeric(d.SQFTmain,errors='coerce')*.09290304;valid=y.between(1700,2022)&y.eq(np.floor(y));d['positive_main_area']=a.where(a>0,0);d['valid_age_main_area']=a.where((a>0)&valid,0);d['valid_actual_year']=valid;d['zero_actual_year']=y.eq(0);d['negative_actual_year']=y.lt(0);d['missing_actual_year']=y.isna();d['invalid_nonzero_actual_year']=(~valid)&y.notna()&y.ne(0);d['multi_line']=d.totBuildingDataLines.gt(1)
  for grouping in ['UseType','ParcelClassification','isTaxableParcel']:
   s=d.groupby(grouping,dropna=False).agg(records=('AIN','size'),positive_main_area_m2=('positive_main_area','sum'),valid_age_main_area_m2=('valid_age_main_area','sum'),valid_actual_year_records=('valid_actual_year','sum'),zero_actual_year=('zero_actual_year','sum'),negative_actual_year=('negative_actual_year','sum'),missing_actual_year=('missing_actual_year','sum'),invalid_nonzero_actual_year=('invalid_nonzero_actual_year','sum'),multi_line_records=('multi_line','sum')).reset_index().rename(columns={grouping:'category'});s['grouping']=grouping;rows.append(s)
 s=pd.concat(rows).groupby(['grouping','category'],dropna=False).sum(numeric_only=True).reset_index();s['valid_actual_year_area_coverage']=s.valid_age_main_area_m2/s.positive_main_area_m2.replace(0,np.nan);s['scope']='complete acquired2022 bbox record population, not independent all-building census';s.to_csv(OUT/'ASSESSOR2022_USE_EXEMPTION_AND_AGE_QA.csv',index=False)
 p=RESEARCH/'local_joint_feature_extraction_20261009/sources/LARIAC6_Buildings_2020.gdb.zip';u='/vsizip/'+str(p).removeprefix('\\\\?\\').replace('\\','/')+'/LARIAC6_Buildings_2020.gdb'
 d=pyogrio.read_dataframe(u,layer='LARIAC6_BUILDINGS_2020',columns=['CODE','HEIGHT','AREA','DATE_','SOURCE'],read_geometry=False);d=d.loc[d.CODE.eq('Building')];h=pd.to_numeric(d.HEIGHT,errors='coerce')*.3048;positive=h[h>0]
 dump('LARIAC_RAW_HEIGHT_VALIDITY.json',{'source_sha256':sha(p),'scope':'county Building source records, before exact geometry dedup','records':len(d),'height_zero':int(h.eq(0).sum()),'height_negative':int(h.lt(0).sum()),'height_missing':int(h.isna().sum()),'height_positive_finite':int((h.gt(0)&np.isfinite(h)).sum()),'positive_height_quantiles_m':positive.quantile([0,.01,.1,.5,.9,.99,.999,1]).to_dict(),'height_gt100m_descriptive_count':int(h.gt(100).sum()),'high_heights_not_automatically_deleted':True,'AREA_is_source_outline_area_not_floor_area':True,'native_HEIGHT_feet_to_m':.3048,'independent_height_validation':'not established; conditional candidates, not inferred floors'})
 log('Cached raw height, actual-year and exemption/use completeness audited')
if __name__=='__main__':main()
