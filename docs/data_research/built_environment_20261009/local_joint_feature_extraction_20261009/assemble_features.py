"""Assemble candidates and descriptive redundancy evidence; no feature selection."""
import json,hashlib,itertools,time
import numpy as np,pandas as pd
from scipy import stats
from source_audit import ROOT,OUT,sha,dump
from extract_scag import CLASSES
FORMAL=ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized';V=ROOT/'docs/data_research/built_environment_20261009/validation';inputs={}
def read(p,id='tract_id'):
 inputs[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size};d=pd.read_csv(p,dtype={id:str});d[id]=d[id].str.zfill(11);assert d[id].str.fullmatch(r'\d{11}').all() and d[id].is_unique;return d.set_index(id)
def save(n,d):d.to_csv(OUT/n,index=True,na_rep='',float_format='%.15g')
def model_vif(frame,features,label,omitted=''):
 x=frame[features].dropna();rows=[];varying=[k for k in features if x[k].std()>0]
 for k in features:
  predictors=[j for j in varying if j!=k];a=x[predictors].to_numpy(float);y=x[k].to_numpy(float);valid=len(x)>len(features)+2 and y.std()>0 and (a.std(axis=0)>0).all()
  if valid:
   a=(a-a.mean(axis=0))/a.std(axis=0);z=np.c_[np.ones(len(x)),a];coef=np.linalg.lstsq(z,y,rcond=None)[0];res=y-z@coef;r2=1-float(res@res)/float((y-y.mean())@(y-y.mean()));vif=1/(1-r2) if 1-r2>1e-12 else np.inf;status='STRUCTURAL_OR_NEAR_EXACT_LINEAR_DEPENDENCY' if not np.isfinite(vif) else 'DESCRIPTIVE_ONLY'
  else:vif=np.nan;r2=np.nan;status='INSUFFICIENT_OR_CONSTANT'
  rows.append({'model':label,'feature':k,'n':len(x),'vif':vif,'auxiliary_R2':r2,'status':status,'omitted_composition_reference':omitted,'constant_features_excluded_from_predictors':';'.join(k for k in features if k not in varying),'matched_tract_sha256':hashlib.sha256('\n'.join(sorted(x.index)).encode()).hexdigest()})
 return rows

def run():
 rec=read(OUT/'RECOVERY_B_T80_INIT_COMPARISON.csv');assert len(rec)==2315;res=read(FORMAL/'clusters_labels_final.csv');assert len(res)==2291;full=read(FORMAL/'stage7_full_domain_tract_status.csv');nri=read(ROOT/'Data/NRI_Table_CensusTracts_California.csv','TRACTFIPS');cdc=read(ROOT/'Data/California.csv','FIPS');acs=read(V/'ACS_TRACT_VALIDATION.csv');nlcd=read(V/'NLCD_TRACT_EXTRACTION.csv');land=read(OUT/'TRACT_GEOMETRY_LAND_WATER_QA.csv');scag=read(OUT/'SCAG_TRACT_LAND_USE.csv');lar=read(OUT/'LARIAC2020_TRACT_URBAN_FORM.csv');age=read(OUT/'BUILDING_AGE_ALL_USE_TRACTS.csv');age2014=read(OUT/'BUILDING_AGE_2014_ORIGINAL_TRACTS.csv');pga=read(OUT/'TRACT_SEISMIC_HAZARD.csv')
 f=rec.copy();f['SOVI_SCORE']=full.SOVI_SCORE;f['formal_population']=full.formal_population;f['NRI_BUILDVALUE']=nri.BUILDVALUE.replace(-999,np.nan);f['NRI_RISK_SCORE_diagnostic']=nri.RISK_SCORE.replace(-999,np.nan);f['NRI_ERQK_RISKS_diagnostic']=nri.ERQK_RISKS.replace(-999,np.nan);f['Pop_Density']=cdc.E_TOTPOP.replace(-999,np.nan)/cdc.AREA_SQMI.where(cdc.AREA_SQMI>0);f['Pop_Density_per_km2']=f.Pop_Density/2.589988110336;f['residential_member']=f.index.isin(res.index)
 m=pd.read_csv(ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str,'substation_id':str});m.tract_id=m.tract_id.str.zfill(11);c=pd.read_csv(ROOT/'Formal_Experiment_20260923/Stage 2 Output_expanded/impact_centrality_substations.csv',dtype={'substation_id':str});inputs['Data/JULY_UTILITY_CONSTRAINED_92.csv']={'sha256':sha(ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv')};inputs['Formal_Experiment_20260923/Stage 2 Output_expanded/impact_centrality_substations.csv']={'sha256':sha(ROOT/'Formal_Experiment_20260923/Stage 2 Output_expanded/impact_centrality_substations.csv')};m=m.merge(c,on='substation_id',how='left',validate='many_to_one');assert m.degree.notna().all();shares=m.weight/m.groupby('tract_id').weight.transform('sum')
 for name,col in [('Grid_Degree','degree'),('Grid_Impact','impact_centrality'),('Grid_Betweenness','betweenness_centrality')]:f[name]=(m[col]*shares).groupby(m.tract_id).sum()
 f['Redundancy_HHI']=(shares**2).groupby(m.tract_id).sum()
 errors={}
 for name in ['T80','Init_Supply','SOVI_SCORE','NRI_BUILDVALUE','Pop_Density','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']:
  a=f.loc[res.index,name];b=res[name];assert a.isna().eq(b.isna()).all();error=float((a-b).abs().max());assert np.allclose(a,b,rtol=1e-11,atol=1e-10,equal_nan=True),(name,error);errors[name]=error
 for k in ['housing_total','housing_5plus_share','housing_5plus_share_moe90','housing_5plus_share_ci90_low','housing_5plus_share_ci90_high','housing_10plus_share','housing_single_unit_share','housing_2to4_share','housing_mobile_other_share','Pre_1970_Ratio','Pre_1970_Ratio_moe90','acs_status']:f[k]=acs[k]
 a=acs.Pre_1970_Ratio.reindex(res.index);b=res.Pre_1970_Ratio;assert np.allclose(a,b,rtol=1e-11,atol=1e-10,equal_nan=True),'ACS age differs from formal original';errors['Pre_1970_Ratio']=float((a-b).abs().max());f['residential_pre1970_housing_share']=acs.Pre_1970_Ratio;f.loc[f.housing_total.eq(0),'residential_pre1970_housing_share']=np.nan;f.loc[f.housing_total.eq(0),'Pre_1970_Ratio']=np.nan
 f['housing_units_per_km2']=f.housing_total/(land.census_ALAND_m2/1e6);f['impervious_land_fraction']=nlcd.impervious_land_fraction;f['impervious_source_status']='PILOT_UNVERIFIED_USGS_VERSION_ESRI_ANNUAL_NLCD_C1_2022';f['impervious_valid_coverage_fraction']=nlcd.valid_coverage_fraction;f['census_ALAND_m2']=land.census_ALAND_m2;f['land_mask_relative_difference']=land.land_area_relative_difference;f['land_mask_area_check_pass']=land.land_area_relative_difference.abs().le(.005)
 for source in [scag,lar,age,age2014,pga]:
  assert set(source.index)==set(f.index)
  keep=[k for k in source.columns if k not in f]
  f=pd.concat([f,source[keep]],axis=1)
 f=f.copy()
 # Water-mask discrepancy is measured, not silently presumed solved. Raw measured ratios retained as diagnostics.
 for k in ['building_footprint_coverage','land_use_entropy','tract_seismic_PGA']+[k+'_area_share' for k in CLASSES]:
  f[k+'_geometry_diagnostic']=f[k];f.loc[~f.land_mask_area_check_pass,k]=np.nan
 f['PGA_partial_support_estimate_g']=pga.PGA_partial_support_estimate_g;f.loc[pga.hazard_status.ne('VERIFIED_PURE_PGA_FIELD'),'tract_seismic_PGA']=np.nan
 # Use Census ALAND for count/unit densities. Unlike polygon coverage, these do not require an exact land-mask shape.
 f['building_count_density']=f.building_count/(f.census_ALAND_m2/1e6)
 for k in ['building_height_median_m','building_height_p10_m','building_height_p90_m','building_height_area_weighted_m']:
  f[k+'_geometry_diagnostic']=f[k];f.loc[~f.land_mask_area_check_pass,k]=np.nan
 f['all_use_age_status']=age.building_age_status;f['grid_feature_status']='EXISTING_MAPPING_WEIGHTED_STATION_METRICS';f['recovery_source_status']='VERIFIED_SAVED_FORMAL_2PC50_C57_D1_DIRECT_COMMUNITY_M1_G1_H480';f['population_density_units']='persons per square mile, exact original CDC field';f['all_use_age_measure_scope']='observed valid-age area only, not complete all buildings'
 save('TRACT_FEATURE_CANDIDATES.csv',f);resf=f.loc[res.index].copy();save('RESIDENTIAL_2291_FEATURE_MATRIX.csv',resf)
 features=['B_480_hr','T80','Init_Supply','SOVI_SCORE','NRI_BUILDVALUE','Pop_Density','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','land_use_entropy']+[k+'_area_share' for k in CLASSES]+['building_footprint_coverage','building_count_density','building_height_median_m','building_height_area_weighted_m','housing_units_per_km2','all_use_pre1970_area_share','all_use_age_coverage','all_use2014_pre1970_area_share','all_use2014_age_coverage','residential_pre1970_area_share','residential_age_coverage','residential2014_pre1970_area_share','residential2014_age_coverage','residential_pre1970_housing_share','housing_5plus_share','impervious_land_fraction','tract_seismic_PGA','NRI_RISK_SCORE_diagnostic','NRI_ERQK_RISKS_diagnostic']
 analysis=resf[features].copy();logs=['B_480_hr','NRI_BUILDVALUE','Pop_Density','building_count_density','housing_units_per_km2','building_height_area_weighted_m']
 for k in logs:analysis['log1p_'+k]=np.log1p(analysis[k].where(analysis[k]>=0))
 correlations=[]
 for a,b in itertools.combinations(analysis.columns,2):
  x=analysis[[a,b]].dropna();valid=len(x)>2 and x[a].std()>0 and x[b].std()>0;pr=stats.pearsonr(x[a],x[b]) if valid else None;sr=stats.spearmanr(x[a],x[b]) if valid else None
  correlations.append({'feature_a':a,'feature_b':b,'cohort':'exact original residential2291','n':len(x),'missing_a':int(analysis[a].isna().sum()),'missing_b':int(analysis[b].isna().sum()),'pairwise_missing':2291-len(x),'pearson_r':pr.statistic if pr else np.nan,'pearson_p_descriptive':pr.pvalue if pr else np.nan,'spearman_rho':sr.statistic if sr else np.nan,'spearman_p_descriptive':sr.pvalue if sr else np.nan,'matched_tract_sha256':hashlib.sha256('\n'.join(sorted(x.index)).encode()).hexdigest(),'status':'DESCRIPTIVE_SPATIALLY_DEPENDENT_TRACTS' if valid else 'INSUFFICIENT_OR_CONSTANT','transform_note':'log1p compresses positive physical intensity/value/loss; no transform or feature selected'})
 pd.DataFrame(correlations).to_csv(OUT/'FEATURE_CORRELATION_MATRIX.csv',index=False,na_rep='',float_format='%.15g')
 qa=[]
 for k in features:
  v=f[k].dropna();status='OBSERVED_OR_FORMAL_MODEL_OUTPUT'
  if k=='impervious_land_fraction':status='PILOT_UNVERIFIED_USGS_SOURCE_VERSION'
  elif k.startswith(('all_use_','all_use2014_')):status='PARTIAL_OBSERVED_AGE_COVERAGE'
  elif k in ['NRI_RISK_SCORE_diagnostic','NRI_ERQK_RISKS_diagnostic']:status='COMPOSITE_RISK_DIAGNOSTIC_NOT_PURE_HAZARD'
  elif k in ['residential_pre1970_area_share','residential_age_coverage','residential2014_pre1970_area_share','residential2014_age_coverage']:status='PARTIAL_OBSERVED_RESIDENTIAL_BUILDING_AGE'
  elif k.startswith('housing_') or k=='residential_pre1970_housing_share':status='ACS_ESTIMATE_WITH_MOE'
  qa.append({'feature':k,'full_n':2315,'full_observed':len(v),'full_missing':int(f[k].isna().sum()),'residential_n':2291,'residential_observed':int(resf[k].notna().sum()),'residential_missing':int(resf[k].isna().sum()),'min':v.min() if len(v) else np.nan,'max':v.max() if len(v) else np.nan,'q01':v.quantile(.01) if len(v) else np.nan,'q50':v.quantile(.5) if len(v) else np.nan,'q99':v.quantile(.99) if len(v) else np.nan,'zero_fraction_observed':float(v.eq(0).mean()) if len(v) else np.nan,'reliability':status,'range_flag':'PASS' if np.isfinite(v).all() else 'NONFINITE','source_and_vintage':source_label(k)})
 pd.DataFrame(qa).to_csv(OUT/'FEATURE_COVERAGE_QA.csv',index=False,na_rep='')
 # VIF is model-dependent; the all-component composition is structurally closed.
 controls=['log1p_Pop_Density','SOVI_SCORE','log1p_NRI_BUILDVALUE'];base=['land_use_entropy','building_footprint_coverage','log1p_building_count_density','building_height_area_weighted_m','all_use_pre1970_area_share','housing_5plus_share','tract_seismic_PGA'];vif=model_vif(analysis,base+controls,'predeclared candidate block, diagnostic not feature selection');base2014=[k if k!='all_use_pre1970_area_share' else 'all_use2014_pre1970_area_share' for k in base];vif+=model_vif(analysis,base2014+controls,'same block with original2014 age scope, diagnostic only')
 composition=[k+'_classified_share' for k in CLASSES];comp=resf[composition].copy();comp.loc[~resf.land_mask_area_check_pass,:]=np.nan;vif+=model_vif(comp,composition,'full composition with intercept; structural dependence expected');reference='vacant_undeveloped_classified_share';vif+=model_vif(comp,[k for k in composition if k!=reference],'composition with one prespecified reference omitted',reference);pd.DataFrame(vif).to_csv(OUT/'FEATURE_VIF.csv',index=False,na_rep='')
 pairs=[('land_use_entropy','building_footprint_coverage'),('land_use_entropy','log1p_building_count_density'),('land_use_entropy','all_use_pre1970_area_share'),('land_use_entropy','all_use2014_pre1970_area_share'),('building_footprint_coverage','all_use2014_pre1970_area_share'),('log1p_building_count_density','all_use2014_pre1970_area_share'),('building_footprint_coverage','all_use_pre1970_area_share'),('log1p_building_count_density','all_use_pre1970_area_share'),('housing_5plus_share','building_footprint_coverage'),('housing_5plus_share','log1p_building_count_density'),('B_480_hr','T80'),('B_480_hr','Init_Supply'),('tract_seismic_PGA','SOVI_SCORE'),('tract_seismic_PGA','log1p_NRI_BUILDVALUE'),('tract_seismic_PGA','NRI_RISK_SCORE_diagnostic')];pairs += [(k+'_area_share',other) for k in CLASSES for other in ['building_footprint_coverage','log1p_building_count_density','all_use_pre1970_area_share','all_use2014_pre1970_area_share']];pairs=list(dict.fromkeys(pairs));conditional=[]
 for a,b in pairs:
  cs=[c for c in controls if c not in [a,b]];x=analysis[[a,b]+cs].dropna();z=np.c_[np.ones(len(x)),x[cs].to_numpy(float)];rank=np.linalg.matrix_rank(z);r=[]
  for name in [a,b]:y=x[name].to_numpy(float);r.append(y-z@np.linalg.lstsq(z,y,rcond=None)[0])
  ok=len(x)>rank+2 and all(y.std()>1e-12 for y in r);rr=stats.pearsonr(*r).statistic if ok else np.nan;rx=x.rank();rz=np.c_[np.ones(len(x)),rx[cs].to_numpy(float)];rank_res=[rx[name].to_numpy(float)-rz@np.linalg.lstsq(rz,rx[name].to_numpy(float),rcond=None)[0] for name in [a,b]];rs=stats.pearsonr(*rank_res).statistic if ok and all(y.std()>1e-12 for y in rank_res) else np.nan;conditional.append({'a':a,'b':b,'controls':';'.join(cs),'n':len(x),'control_design_rank':rank,'partial_pearson_r':rr,'partial_spearman_rank_residual_r':rs,'residual_shared_variance':rr**2,'status':'LINEAR_CONDITIONAL_REDUNDANCY_ONLY' if ok else 'INSUFFICIENT_OR_CONSTANT','matched_tract_sha256':hashlib.sha256('\n'.join(sorted(x.index)).encode()).hexdigest()})
 pd.DataFrame(conditional).to_csv(OUT/'FEATURE_CONDITIONAL_REDUNDANCY.csv',index=False,na_rep='');dump('FEATURE_ASSEMBLY_QA.json',{'full_count':len(f),'residential_count':len(resf),'no_labels_or_PCA_in_candidate_matrix':not any(c in f for c in ['cluster','PC1','PC2','Hotspot_SVI_Score']),'original_feature_max_errors':errors,'landmask_discrepancy_gt0_5pct_tracts':f.index[~f.land_mask_area_check_pass].tolist(),'zero_housing_undefined_share_tracts':f.index[f.housing_total.eq(0)].tolist(),'n_correlations':len(correlations),'variable_selection_performed':False,'final_clustering_performed':False});dump('FEATURE_INPUT_HASHES.json',inputs);print('FEATURES_COMPLETE',f.shape,resf.shape,len(correlations),flush=True)
def source_label(k):
 if k.startswith(('B_','T80','Init')):return 'Formal evaluation 2pc50/C57_D1/direct-community/M1/G1,1000 realizations,480h'
 if k.startswith('Grid_') or k=='Redundancy_HHI':return 'Formal Stage2 and frozen M1 mapping, baseline031d2c6'
 if k.startswith('land_use') or any(k.startswith(c) for c in CLASSES):return 'SCAG ALU2019.1 updated February2021, exclusive geometry areas'
 if k.startswith('building_'):return 'LARIAC6 2020 observed roof outlines, mixed2008/2014/2017/2020 capture dates; TIGER2020 landmask'
 if k.startswith('all_use2014_'):return 'LARIAC4 2014 original building outlines and associated assessor YearBuilt1; separate from 2020 strict linkage'
 if k.startswith('all_use_'):return 'LARIAC4 2014 associated assessor YearBuilt1/Roll_Year linked to LARIAC6 2020 by uniqueID+IoU>=.90'
 if k in ['residential_pre1970_area_share','residential_age_coverage']:return 'Residential-use2014 assessor years linked to2020 outlines, partial observed age area'
 if k.startswith('residential2014_'):return 'Residential-use original2014 outlines and associated assessor years, partial observed age area'
 if k.startswith('housing_') or k=='residential_pre1970_housing_share':return 'ACS2022 five-year B25024/B25034, prior validated extraction, MOE retained'
 if k.startswith('impervious'):return 'ESRI numeric AnnualNLCD Collection1.0 2022 pilot; USGS linkage not independently verified'
 if k=='tract_seismic_PGA':return 'CGS MS48 2025, NSHM2023 and Vs30July2022; exact original 0.01deg PGA grid'
 if k=='Pop_Density':return 'original CDC SVI California.csv E_TOTPOP/AREA_SQMI, exact Stage7 convention'
 return 'FEMA NRI v1.19 original source; risk fields diagnostic only'
if __name__=='__main__':run()
