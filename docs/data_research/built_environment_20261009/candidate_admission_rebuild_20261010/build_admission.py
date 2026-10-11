"""Source-bounded candidate measurement admission; no clustering or simulation."""
from common import *
import pandas as pd, numpy as np, zipfile, itertools, shutil, platform
from scipy import stats

UNRESOLVED=['06037189703','06037301601','06037301602','06037404600']
SCAG=['residential','commercial_office','industrial','institutional_public','transportation_utility','open_space_recreation','vacant_undeveloped','agriculture','mixed_use','under_construction','protected_undevelopable']
SOURCES={
 'SCAG':('https://rdp.scag.ca.gov/mapping/rest/services/Housing/2019_Annual_Land_Use/MapServer/0','ALU 2019.1; LU19 snapshot, current service updates not observation years','exclusive parcel intersection EPSG3310','local_joint_feature_extraction_20261009/SCAG_GEOMETRY_QA.json'),
 'SCAG2020':('https://rdp.scag.ca.gov/mapping/rest/services/Housing/2020_Annual_Land_Use/MapServer/0','2020 ALU snapshot; later context layers do not update observed ALU20','parcel ALU20; actual geometry/coverage not yet audited','SCAG_ALTERNATIVE_VERSION_CHECK.json'),
 'LARIAC6':('https://apps.gis.lacounty.gov/static/hub/lariac_documents/LARIAC6/LARIAC6_Buildings_2020.gdb.zip','2020 inventory release; mixed image dates, predominantly older imagery','individual roofline polygons, HEIGHT feet','local_joint_feature_extraction_20261009/LARIAC2020_HEIGHT_QA.json'),
 'LARIAC4':('https://services.arcgis.com/RmCCgQtiZLDCtblq/arcgis/rest/services/Countywide_Building_Outlines/FeatureServer/1','2014 inventory; valid observed YearBuilt1','historical outline stock','local_joint_feature_extraction_20261009/BUILDING_AGE_2014_QA.json'),
 'ACS':('https://www.census.gov/programs-surveys/acs/data/variance-tables.html','ACS 2018-2022 five-year; 2022 VRE 80 replicates','2020 tract; housing units','validation/ACS_TRACT_VALIDATION.csv'),
 'EMC':('https://data.jrc.ec.europa.eu/dataset/4cd8ccee-bfd1-48c5-9047-61c0343c41e9','EMC-BUILT R2025A V1.0; Sentinel-2 2022','100 m equal-area; m2 built per pixel','JRC_ACQUISITION.json'),
 'ANBH':('https://data.jrc.ec.europa.eu/dataset/85005901-3a49-48dd-9d19-6261354f56fe','GHS-BUILT-H R2023A; 2018 Sentinel-2, SRTM 2000, AW3D30 2006-2011','100 m net built-height model; m','RASTER_METADATA_AND_QA.json'),
 'ASSESSOR':('https://data.lacounty.gov/datasets/assessor-parcel-data-rolls-2021-2025','single RollYear 2022; roll year does not date all observations','parcel point and assessment main square footage','ASSESSOR_MEASUREMENT_QA.json'),
 'NLCD':('https://www.usgs.gov/centers/eros/science/usgs-eros-archive-land-cover-annual-nlcd-collection-12-fractional-impervious','Annual NLCD Collection 1.2; mapping year 2022; 2026 release','30 m fractional impervious 0-100%; official numeric archive','NLCD_C12_MEASUREMENT_QA.json'),
 'NLCD_PILOT':('https://www.mrlc.gov/data','numeric 2022 C1.0 ESRI pilot; NOT verified as C1.2','30 m numeric pilot only','validation/NLCD_ACQUISITION.json'),
 'EPA':('https://www.epa.gov/smartgrowth/smart-location-mapping','SLD v3; 2017 LODES jobs, 2014-2018 households','2010 block groups; no validated 2020 tract quantity crosswalk','pilot/EPA_SLD_V3_LA_BG_SOURCE.csv'),
 'FEMA':('https://dam.assets.ohio.gov/image/upload/ema.ohio.gov/mip/links/2023/ema-sohmp-AppendixJ.pdf','archived FEMA NRI v1.19 March 2023; 2022 dollar framework','published tract fields; national percentiles vs values','nri_eal_redundancy_audit_20261009/FEMA_FIELD_DEFINITIONS_AND_COMPOSITION.md'),
 'CONCEPT':('','concept boundary; not an acquired primary measure','','')}

def read(p):return pd.read_csv(p,dtype={'tract_id':str}).set_index('tract_id')
def idhash(ids):return hashlib.sha256(('\n'.join(sorted(ids))+'\n').encode()).hexdigest()

def acs_additions(ids):
 p=source('validation/sources/B25024_06.csv.zip')
 with zipfile.ZipFile(p) as z:f=pd.read_csv(z.open(z.namelist()[0]),dtype={'GEOID':str})
 f=f.loc[f.GEOID.str.startswith('1400000US06037',na=False)].copy();f['tract_id']=f.GEOID.str[-11:];reps=[f'Var_Rep{i}' for i in range(1,81)]
 den=f.loc[f.ORDER.eq(1)].set_index('tract_id').loc[ids];D=den.ESTIMATE.to_numpy();out=pd.DataFrame(index=ids)
 for name,order in [('housing_detached_share',2),('housing_attached_share',3)]:
  n=f.loc[f.ORDER.eq(order)].set_index('tract_id').loc[ids];p=np.divide(n.ESTIMATE.to_numpy(),D,out=np.full(len(D),np.nan),where=D>0)
  dr=den[reps].to_numpy();r=np.divide(n[reps].to_numpy(),dr,out=np.zeros_like(dr,dtype=float),where=dr!=0)
  se=np.sqrt(4/80*np.square(r-p[:,None]).sum(axis=1));boundary=(p==0)|(p==1)|(se==0);pstar=np.minimum(.5,np.divide(2.3*16,D,out=np.zeros_like(D,dtype=float),where=D>0));bse=np.sqrt(pstar*(1-pstar)*np.divide(16,D,out=np.zeros_like(D,dtype=float),where=D>0));se=np.where(boundary,bse,se)
  out[name]=p;out[name+'_moe90']=1.645*se;out[name+'_boundary_model']=boundary&(D>0);out[name+'_zero_replicate_denominators']=(dr==0).sum(axis=1)
  out[name+'_ci90_low']=np.maximum(0,p-1.645*se);out[name+'_ci90_high']=np.minimum(1,p+1.645*se)
 out.to_csv(OUT/'ACS_DETACHED_ATTACHED_VRE.csv',float_format='%.15g')
 return out

def values():
 f=read(source('local_joint_feature_extraction_20261009/TRACT_FEATURE_CANDIDATES.csv'));v=read(source('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv'))
 assert len(f)==2315 and len(v)==2291 and set(v.index)==set(f.index[f.residential_member.astype(bool)])
 keep=[c for c in f if not (c.startswith(('PGA','tract_seismic','hazard_','NRI_ERQK')) or 'geometry_diagnostic' in c or c in ['AUC_480'])]
 f=f[keep].copy()
 for c in f.columns.intersection(v.columns):f.loc[v.index,c]=v[c]
 f=f.rename(columns={'impervious_land_fraction':'nlcd_c10_pilot_impervious_land_fraction','Pre_1970_Ratio':'acs_residential_pre1970_share','Pre_1970_Ratio_moe90':'acs_residential_pre1970_share_moe90'})
 ac=read(source('validation/ACS_TRACT_VALIDATION.csv'))
 for c in ac:
  if c in ['cluster','dominant_configuration','approx_plus_ratio_fallback','housing_5plus_share_approx_moe90']:continue
  target=c.replace('Pre_1970_Ratio','acs_residential_pre1970_share');f[target]=ac[c]
 f=f.join(acs_additions(f.index))
 for filename in ['JRC_TRACT_MEASUREMENTS.csv','LARIAC_SIZE_AND_HEIGHT_MEASUREMENTS.csv','ASSESSOR2022_TRACT_MEASUREMENTS.csv']:
  f=f.join(read(OUT/filename),validate='one_to_one')
 if (OUT/'NLCD_C12_TRACT_MEASUREMENTS.csv').exists():
  f=f.join(read(OUT/'NLCD_C12_TRACT_MEASUREMENTS.csv'),validate='one_to_one')
  f['nlcd_c10_pilot_impervious_legacy_geometry_fraction']=f.nlcd_c10_pilot_impervious_land_fraction
  f['nlcd_c10_pilot_impervious_land_fraction']=f.nlcd_c10_pilot_same_geometry_impervious_fraction
  f['impervious_valid_coverage_fraction']=f.nlcd_c10_pilot_same_geometry_valid_land_coverage
 fp=ORIGINAL/'Data/NRI_Table_CensusTracts_California.csv';raw=pd.read_csv(fp,dtype={'TRACTFIPS':str});raw['tract_id']=raw.TRACTFIPS.str.zfill(11);assert not raw.tract_id.duplicated().any();raw=raw.set_index('tract_id').loc[f.index]
 assert raw.NRI_VER.eq('Mar-23').all()
 fields=['BUILDVALUE','EAL_SCORE','EAL_VALT','EAL_VALB','EAL_VALP','EAL_VALPE','EAL_VALA','ALR_VALB','ALR_VALP','ALR_VALA','ALR_NPCTL','ALR_VRA_NPCTL','RISK_SCORE','RISK_VALUE','SOVI_SCORE','RESL_SCORE','CRF_VALUE','POPULATION','AGRIVALUE']
 assert np.allclose(raw.BUILDVALUE,f.NRI_BUILDVALUE,rtol=1e-12,equal_nan=True) and np.allclose(raw.SOVI_SCORE,f.SOVI_SCORE,rtol=1e-10,equal_nan=True)
 for c in fields:
  if c=='SOVI_SCORE':f['FEMA_SOVI_SCORE_archived']=raw[c]
  else:f[c]=raw[c]
 for c in ['BUILDVALUE','EAL_VALT','EAL_VALB','EAL_VALPE','EAL_VALA']:f['log1p_'+c]=np.log1p(f[c].where(f[c]>=0))
 f['ALR_VALA']=f.ALR_VALA.where(f.AGRIVALUE>0);f['ALR_VALP']=f.ALR_VALP.where(f.POPULATION>0);f['ALR_VALB']=f.ALR_VALB.where(f.BUILDVALUE>0)
 f['fema_agricultural_rate_status']=np.where(f.AGRIVALUE>0,'DEFINED','ZERO_EXPOSURE_UNDEFINED')
 f['scag_nonresidential_classified_share']=f[[c+'_classified_share' for c in SCAG if c!='residential']].sum(axis=1,min_count=len(SCAG)-1)
 f['geometry_status']=np.where(f.index.isin(UNRESOLVED),'UNRESOLVED_GEOMETRY','VALIDATED_OR_VERSION_QUALIFIED')
 geometric=[c for c in f if not c.startswith('assessor2022_') and (c.startswith(('outline_','emc2022_','jrc_','building_footprint','building_height','land_use','all_use2014','all_use_pre1970','residential2014','nlcd_c10_pilot')) or c.endswith(('_area_share','_classified_share'))) and pd.api.types.is_numeric_dtype(f[c])]
 f.loc[UNRESOLVED,geometric]=np.nan
 f.loc[UNRESOLVED,[c+'_area_m2' for c in SCAG]]=np.nan
 f.index.name='tract_id';f.to_csv(OUT/'CANDIDATE_VALUES_2315.csv',float_format='%.15g');f.loc[v.index].to_csv(OUT/'CANDIDATE_VALUES_RESIDENTIAL_2291.csv',float_format='%.15g')
 dump('VALUE_ASSEMBLY_QA.json',{'full_n':len(f),'residential_n':len(v),'full_GEOID_set_sha256':idhash(f.index),'residential_GEOID_set_sha256':idhash(v.index),'full_order_sha256':hashlib.sha256(('\n'.join(f.index)+'\n').encode()).hexdigest(),'residential_order_sha256':hashlib.sha256(('\n'.join(v.index)+'\n').encode()).hexdigest(),'four_unresolved':UNRESOLVED,'four_have_ACS':f.loc[UNRESOLVED,'housing_5plus_share'].notna().all().item(),'four_have_Assessor_age':f.loc[UNRESOLVED,'assessor2022_actual_pre1970_main_area_share'].notna().all().item(),'source_FEMA_sha256':sha(fp),'FEMA_version':'Mar-23 v1.19','preserved_SOVI_vs_archive_rounding_max':float((f.SOVI_SCORE-raw.SOVI_SCORE).abs().max()),'no_clustering':True,'no_weights_changed':True})
 return f,v.index

def register(f):
 rows=[]
 def add(name,concept,formula,unit,src,status,reason,coverage='',replace='',role='primary candidate',pendingfield=None):
  url,vintage,resolution,qa=SOURCES[src];col=name if pendingfield is None else pendingfield;available=col in f
  vals=pd.to_numeric(f[col],errors='coerce') if available else pd.Series(np.nan,index=f.index)
  rows.append(dict(candidate_id=name,construct=concept,definition=formula,unit=unit,research_use=role,alternative_to=replace,primary_source=src,source_url=url,source_commit=BASELINE if src in ['SCAG','LARIAC4','ACS','NLCD_PILOT','EPA','FEMA'] else 'new official acquisition in this branch',alternative_source={'LARIAC6':'EMC; assessor','EMC':'LARIAC6','ANBH':'LARIAC6','ASSESSOR':'LARIAC4; ACS','SCAG':'EPA (different construct)','ACS':'assessor (different population)'}.get(src,''),vintage=vintage,resolution=resolution,numeric_status='TRACT_VALUES_VERIFIED' if vals.notna().any() else ('RAW_BG_VALUES_ONLY' if src=='EPA' else 'NO_ADMISSIBLE_TRACT_VALUES'),value_column=col if available else '',valid_tracts_2315=int(vals.notna().sum()),valid_residential_2291=int(vals.loc[f.index[f.residential_member.astype(bool)]].notna().sum()),disposition=status,admission_condition_or_exclusion_reason=reason,coverage_column=coverage,source_qa=qa))
 add('land_use_entropy','land-use composition diversity','-sum(p_i log(p_i))/log(11); p_i=exclusive classified class area/total exclusive classified land','0-1','SCAG','CONDITIONAL','Classified parcel land only; preserve missing/ambiguous/gap area. Not full-tract composition.','land_use_classified_land_coverage')
 for c in SCAG:add(c+'_classified_share','land-use composition',f'exclusive {c} area / exclusive classified land','0-1','SCAG','CONDITIONAL','Compositional component, shares sum to one; not independent of entropy or other shares.','land_use_classified_land_coverage',replace='land_use_entropy',role='composition alternative')
 add('scag_nonresidential_classified_share','residential/non-residential land-use composition','sum(non-residential exclusive class area)/classified land','0-1','SCAG','CONDITIONAL','Complement of residential_classified_share; do not include both as independent inputs.','land_use_classified_land_coverage',replace='residential_classified_share')
 add('epa_household_job_activity_mix','household/job activity balance','EPA D2A_EPHHM employment+household mix, following SLD dictionary','published mix index','EPA','PENDING_DATA','Actual 6425 BG rows exist; count-preserving 2010-BG to 2020-tract geographic allocation not validated. Prefix matches are not a crosswalk.',replace='land_use_entropy (different measurement)')
 add('scag2020_classified_land_entropy','land-use composition diversity','exclusive ALU20 class area entropy under separately verified class definition','0-1','SCAG2020','PENDING_DATA','Official 2020 layer and ALU20 fields confirmed; actual numeric overlay/stack/coverage not completed. Potential temporal alternative, no automatic replacement of 2019.1.',replace='land_use_entropy')
 add('building_footprint_coverage','building ground coverage','area(union(deduplicated Building footprints intersect tract land))/tract land','fraction','LARIAC6','CONDITIONAL','Valid ground coverage for mixed older imagery/2020 inventory; not 2022 synchronized building census.','land_mask_relative_difference',replace='emc2022_total_built_land_fraction')
 add('emc2022_total_built_land_fraction','building ground coverage','sum(pixel built m2 * pixel land-intersection fraction)/tract land area','fraction','EMC','ADMIT','2022 observation support; actual 100m tiles, valid zero/NoData and complete valid-area support checked. Remote classification is not local ground-truth accuracy.','jrc_total_valid_land_coverage',replace='building_footprint_coverage')
 add('emc2022_nres_built_land_fraction','non-residential built surface','sum(non-residential built m2 * pixel land-intersection fraction)/tract land','fraction','EMC','CONDITIONAL','Binary modeled non-residential surface, not complete parcel use composition.','jrc_nres_valid_land_coverage',replace='SCAG non-residential area (different denominator)')
 add('emc2022_nonresidential_built_share','non-residential built surface','modeled non-residential built m2 / all modeled built m2','fraction','EMC','CONDITIONAL','Derived ratio shares source and numerator with total/NRES; no multi-class entropy.','jrc_nres_valid_land_coverage',replace='emc2022_nres_built_land_fraction')
 available='nlcd_c12_2022_impervious_fraction' in f
 add('nlcd_c12_2022_impervious_fraction','ground hardening','area-weighted fractional impervious percentage /100, mapping year2022','fraction','NLCD','ADMIT' if available else 'PENDING_DATA','Official C1.2 numerical archive retrieved through public legacy ScienceBase route; year/version/units/NoData and full land support verified. Includes roads and other hard surfaces; not building coverage.' if available else 'Official numerical access not yet complete; old C1.0 pilot not substituted.',coverage='nlcd_c12_valid_land_coverage')
 add('nlcd_c10_pilot_impervious_land_fraction','ground hardening','C1.0 pilot reaggregated on exactly the current land geometry','fraction','NLCD_PILOT','DESCRIPTIVE_ONLY','Shared2022 numeric pixels and tract means equal official C1.2; release provenance still distinct. Reproduction record only, not a second independent coordinate; includes roads.','impervious_valid_coverage_fraction',replace='nlcd_c12_2022_impervious_fraction')
 add('outline_count_per_km2_centroid','outline frequency','deduplicated CODE=Building centroid count/(Census ALAND/1e6)','outlines/km2','LARIAC6','CONDITIONAL','Physical buildings can be split rooflines/annexes; exact geometry dedup only; boundary ties smallest GEOID.',replace='building_count_density')
 for name,desc in [('outline_area_mean_m2','mean'),('outline_area_median_m2','median'),('outline_area_iqr_m2','75th-25th percentile'),('outline_area_cv','population SD/mean')]:
  add(name,'outline size and segmentation',f'{desc} of whole EPSG3310 outline area, centroid assigned','dimensionless' if name.endswith('cv') else 'm2','LARIAC6','DESCRIPTIVE_ONLY' if name.endswith('mean_m2') else 'CONDITIONAL','Roofline segmentation affects count and size. Median/IQR/CV are distribution summaries, not new constructs.',replace='other outline size summaries',role='size alternative; mean is identity diagnostic')
 add('outline_height_area_weighted_centroid_m','vertical morphology','sum(positive finite nonconflicting HEIGHT_m * whole outline area)/valid-height outline area','m','LARIAC6','CONDITIONAL','Historical/mixed inventory roofline height, feet converted to m; no floor-count inference.','outline_valid_height_area_fraction_centroid',replace='jrc_anbh_positive_surface_mean_m')
 for name in ['building_height_median_m','building_height_p10_m','building_height_p90_m']:add(name,'vertical morphology','centroid-supported positive finite source HEIGHT distribution','m','LARIAC6','CONDITIONAL','Historical height support; distribution alternatives, not independent coordinates.','building_height_valid_area_fraction',replace='outline_height_area_weighted_centroid_m')
 add('jrc_anbh_positive_surface_mean_m','vertical morphology','land-area-weighted mean of positive 100m ANBH cells','m','ANBH','CONDITIONAL','Net-height model with 2018 imagery and older DEMs; positive-cell land weighting is not footprint-area weighting and not 2022 building height.','jrc_height_valid_land_coverage',replace='outline_height_area_weighted_centroid_m')
 add('assessor2022_gross_floor_area_ratio','floor-space intensity','documented gross floor area / tract land','m2/m2','ASSESSOR','PENDING_DATA','SQFTmain dictionary says Main Square Footage; gross-floor-area definition, multi-building line attribution and condominium duplicate coverage unresolved. No certified FAR produced.')
 add('assessor2022_main_area_per_land','assessment main-area intensity','sum(positive SQFTmain*.09290304 for unique AIN parcel points)/Census ALAND','m2/m2','ASSESSOR','DESCRIPTIVE_ONLY','Main assessment area; not certified gross FAR or footprint area. Multiple data lines/condos and exemptions are explicit coverage limitations.')
 add('outline_volume_per_land_m_centroid','roof-height volume proxy','sum(valid-height whole outline area*height)/Census ALAND','m3/m2','LARIAC6','DESCRIPTIVE_ONLY','Product of centroid-sum coverage, valid height support and weighted height; no union volume or floor area. Not independent of all factors.','outline_valid_height_area_fraction_centroid')
 for name in ['housing_5plus_share','housing_detached_share','housing_attached_share','housing_single_unit_share','housing_2to4_share','housing_mobile_other_share','housing_10plus_share']:
  add(name,'residential unit configuration','specified B25024 housing-unit counts / B25024_001E; exact 80 variance replicates','fraction','ACS','ADMIT' if name in ['housing_5plus_share','housing_detached_share'] else 'DESCRIPTIVE_ONLY','Residential units, not buildings; housing denominator>0. Preserve source MOE/CI/boundary-model and uncertainty without precision-biased tract exclusion.',coverage='housing_total',replace='other ACS configuration shares',role='same composition family; choose at most one primary summary')
 add('assessor2022_actual_pre1970_main_area_share','observed assessment-stock age','sum(positive main area with actual YearBuilt<1970)/positive main area with valid actual YearBuilt','fraction','ASSESSOR','CONDITIONAL','2022 parcel point stock; valid year1700-2022; multiple-building lines/condos/exempt stock prevent complete all-building interpretation.','assessor2022_actual_age_main_area_coverage',replace='all_use2014_pre1970_area_share')
 add('assessor2022_single_line_pre1970_main_area_share','observed assessment-stock age','same age share restricted to exactly one building data line','fraction','ASSESSOR','CONDITIONAL','Single-line restricted coverage diagnostic; not countywide all-use completeness.','assessor2022_single_line_age_coverage',replace='assessor2022_actual_pre1970_main_area_share')
 add('assessor2022_effective_pre1970_main_area_share','effective assessment-stock age','positive main area with EffectiveYearBuilt<1970 / valid effective-year main area','fraction','ASSESSOR','DESCRIPTIVE_ONLY','Effective year can reflect improvement/assessment; not original construction year.',replace='actual YearBuilt (different construct)')
 add('acs_residential_pre1970_share','residential unit age','B25034_008E+009E+010E+011E divided by001E;80 VRE','fraction','ACS','ADMIT','2018-2022 residential housing units; neither all-use construction year nor area-weighted physical buildings.','housing_total',replace='all-use age (different population)')
 add('all_use2014_pre1970_area_share','historical observed building-stock age','valid-age footprint union area pre1970 / historical valid-age footprint union area','fraction','LARIAC4','CONDITIONAL','2014 historical valid observed-age area; government-age missingness and vintage mismatch; preserve coverage and lower/upper bounds.','all_use2014_age_coverage',replace='assessor2022_actual_pre1970_main_area_share')
 add('all_use_pre1970_area_share','cross-vintage transferred stock age','2014 age transferred only where 2014/2020 outlines satisfy source geometry match','fraction','LARIAC4','REJECT','About4% matched-age footprint coverage in prior verified audit; not representative complete 2020 all-use age. Retain values only as coverage diagnostic.','all_use_2014_2020_match_area_coverage',replace='all_use2014_pre1970_area_share')
 for name,concept,why in [('building_spacing','layout','No prespecified independent recovery-community construct beyond density/size; source boundary/segmentation definition unresolved.'),('street_intersection_density','layout','Connectivity/access is distinct transport context, not automatically building morphology; no authorized road topology definition/validated source here.'),('block_scale','layout','Shared density/layout information; no prespecified independent conceptual need or verified polygon definition.'),('vegetation_fraction','vegetation','Vegetation is land cover, not building physical morphology; may be context, not an automatic BE coordinate.'),('residential_occupancy','household utilization','Housing occupancy is household utilization, not building morphology; no new primary inclusion.'),('stories_from_roof_height','floor-space intensity','Reject arbitrary story-height assumption; no actual observed floor count.'),('total_EAL_divided_BUILDVALUE','multi-hazard loss propensity','Wrong denominator for total building+population+agriculture loss; not official ALR.')]:
  add(name,concept,'not extracted; see verified construct boundary','', 'CONCEPT','REJECT',why,role='excluded this round')
 add('Pop_Density_per_km2','population concentration','formal population/Census land area km2','persons/km2','CONCEPT','DESCRIPTIVE_ONLY','Population is people, not all-use building form. Preserve as overlap diagnostic, not automatic BE coordinate.')
 for name,concept,formula,unit,status,why in [
  ('BUILDVALUE','economic asset stock','published aggregate building exposure value','2022 USD','ADMIT','Economic stock, not physical morphology or expected loss.'),
  ('EAL_SCORE','multi-hazard expected loss with exposure','national percentile rank of EAL_VALT','0-100 percentile','ADMIT','Includes building/population/agricultural exposure, frequency and historic loss ratio; not pure hazard, not independent of socioeconomic context.'),
  ('EAL_VALT','multi-hazard expected loss with exposure','EAL_VALB+EAL_VALPE+EAL_VALA','2022 USD/year','ADMIT','Same construct as EAL_SCORE, value alternative only; raw/log1p compared, never both primary coordinates.'),
  ('ALR_NPCTL','multi-hazard normalized loss propensity','official composite national percentile of EAL-weighted component loss-rate percentiles','0-100 percentile','ADMIT','Unadjusted for community social/resilience factors; exposure-normalized component rates, not pure hazard or totalEAL/BUILDVALUE.'),
  ('ALR_VALB','building annual loss rate','EAL_VALB/BUILDVALUE for positive exposure','year-1','CONDITIONAL','Building consequences only; does not represent population/agriculture/all consequences.'),
  ('ALR_VALP','population annual loss rate','EAL_VALP/POPULATION for positive exposure','year-1','CONDITIONAL','Population consequences only; not population-equivalent dollar loss divided by people.'),
  ('ALR_VALA','agricultural annual loss rate','EAL_VALA/AGRIVALUE for positive exposure','year-1','DESCRIPTIVE_ONLY','Zero agricultural exposure remains undefined; sparse regional coverage.'),
  ('RISK_SCORE','social-adjusted multi-hazard risk','national rank of EAL_VALT times community risk factor','0-100 percentile','DESCRIPTIVE_ONLY','Mechanically combines social vulnerability and resilience; overlaps mandatory separately retained SOVI.'),
  ('ALR_VRA_NPCTL','social-adjusted loss propensity','community-adjusted official composite loss-rate percentile','0-100 percentile','REJECT','Mechanically reintroduces social/resilience adjustment alongside mandatory SOVI; preserve as diagnostic comparator.')]:add(name,concept,formula,unit,'FEMA',status,why)
 r=pd.DataFrame(rows);r.to_csv(OUT/'CANDIDATE_REGISTER.csv',index=False);return r

def qa(f,r,resids):
 rows=[]
 for row in r.to_dict('records'):
  c=row['value_column'];s=pd.to_numeric(f[c],errors='coerce') if c else pd.Series(np.nan,index=f.index)
  cov=pd.to_numeric(f[row['coverage_column']],errors='coerce') if row['coverage_column'] in f else pd.Series(np.nan,index=f.index)
  for scope,ids in [('full2315',f.index),('residential2291',resids)]:
   z=s.loc[ids];a=cov.loc[ids];valid=z.notna();quant=z.dropna().quantile([0,.1,.5,.9,1]);cq=a.dropna().quantile([0,.1,.5,.9,1]);record={'candidate':row['candidate_id'],'scope':scope,'n_total':len(ids),'n_valid':int(valid.sum()),'n_missing':int((~valid).sum()),'zero_fraction_valid':float(z.eq(0).sum()/valid.sum()) if valid.any() else np.nan,'negative_count':int(z.lt(0).sum()),'valid_GEOID_set_sha256':idhash(z.index[valid]),'coverage_definition':row['coverage_column'],'disposition':row['disposition'],'source_vintage':row['vintage'],'uncertainty_or_limit':row['admission_condition_or_exclusion_reason']}
   record.update({f'value_{q}':quant.get(p,np.nan) for q,p in [('min',0),('p10',.1),('median',.5),('p90',.9),('max',1)]});record.update({f'coverage_{q}':cq.get(p,np.nan) for q,p in [('min',0),('p10',.1),('median',.5),('p90',.9),('max',1)]});rows.append(record)
 pd.DataFrame(rows).to_csv(OUT/'CANDIDATE_MEASUREMENT_QA.csv',index=False)
 return pd.DataFrame(rows)

def correlations(f,r,resids):
 cols=[x for x in r.value_column if x and pd.api.types.is_numeric_dtype(f[x])]+['SOVI_SCORE','B_480_hr','Init_Supply','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI','log1p_BUILDVALUE','log1p_EAL_VALT']
 cols=list(dict.fromkeys(cols));rows=[]
 strata={'residential2291':f.index.isin(resids),'full2315':np.ones(len(f),bool)}
 # Continuous coverage retained; these sample strata are diagnostics, not admission cutoffs.
 q=f.land_use_classified_land_coverage.quantile([.25,.75]);strata['SCAG_low_coverage_quartile']=f.index.isin(resids)&f.land_use_classified_land_coverage.le(q.iloc[0]);strata['SCAG_high_coverage_quartile']=f.index.isin(resids)&f.land_use_classified_land_coverage.ge(q.iloc[1])
 strata['assessor_low_multiline_share']=f.index.isin(resids)&f.assessor2022_multi_line_area_share.le(f.assessor2022_multi_line_area_share.median());strata['assessor_high_multiline_share']=f.index.isin(resids)&f.assessor2022_multi_line_area_share.gt(f.assessor2022_multi_line_area_share.median())
 for scope,mask in strata.items():
  for a,b in itertools.combinations(cols,2):
   d=f.loc[mask,[a,b]].replace([np.inf,-np.inf],np.nan).dropna();n=len(d)
   if n<5 or min(d.nunique())<2:continue
   pear=stats.pearsonr(d[a],d[b]);spear=stats.spearmanr(d[a],d[b]);rows.append({'analysis':'pair','scope':scope,'x':a,'y':b,'N':n,'GEOID_set_sha256':idhash(d.index),'pearson_r':pear.statistic,'spearman_r':spear.statistic,'pearson_p':pear.pvalue,'spearman_p':spear.pvalue,'sample_exclusions':len(f.loc[mask])-n,'interpretation':'measurement overlap only; no admission based on correlation'})
 result=pd.DataFrame(rows);result.to_csv(OUT/'DEPENDENCY_AND_REDUNDANCY.csv',index=False,float_format='%.12g')
 # Same construct/source alternatives compared on exactly common residential cases.
 sets={'coverage':['building_footprint_coverage','emc2022_total_built_land_fraction'],'vertical':['outline_height_area_weighted_centroid_m','jrc_anbh_positive_surface_mean_m'],'outline_frequency_size':['outline_count_per_km2_centroid','outline_area_mean_m2','outline_area_median_m2','outline_area_cv'],'age_distinct_support':['assessor2022_actual_pre1970_main_area_share','all_use2014_pre1970_area_share','acs_residential_pre1970_share'],'risk_stock_propensity':['BUILDVALUE','ALR_NPCTL'],'risk_stock_propensity_log':['log1p_BUILDVALUE','ALR_NPCTL'],'risk_combined_loss':['SOVI_SCORE','EAL_SCORE'],'risk_stock_plus_loss':['SOVI_SCORE','log1p_BUILDVALUE','EAL_SCORE']}
 vif=[];samples=[]
 for name,cs in sets.items():
  d=f.loc[resids,cs].dropna();x=(d-d.mean())/d.std(ddof=0)
  for i,c in enumerate(cs):
   y=x[c].to_numpy();z=np.column_stack([np.ones(len(d)),x.drop(columns=c).to_numpy()]);fit=z@np.linalg.lstsq(z,y,rcond=None)[0];r2=1-np.square(y-fit).sum()/np.square(y-y.mean()).sum();vif.append({'set':name,'coordinate':c,'N':len(d),'VIF':1/(1-r2) if r2<1 else np.inf,'condition_number':np.linalg.cond(x.to_numpy()),'GEOID_set_sha256':idhash(d.index),'note':'simultaneous diagnostic inputs only; no clustering weights'})
  missing=f.loc[resids,cs].isna().any(axis=1)
  for key in f.loc[resids].index[missing]:samples.append({'comparison':name,'excluded_GEOID':key,'missing_fields':';'.join(c for c in cs if pd.isna(f.loc[key,c]))})
 pd.DataFrame(vif).to_csv(OUT/'SAME_CONSTRUCT_AND_RISK_VIF.csv',index=False);pd.DataFrame(samples).to_csv(OUT/'COMMON_SAMPLE_EXCLUSIONS.csv',index=False)
 # Formal algebra on matching centroid support only. These identities do not apply to union coverage.
 d=f.loc[resids];derived=d.outline_count_per_km2_centroid*d.outline_area_mean_m2/1e6;volume=d.outline_area_fraction_centroid_sum*d.outline_valid_height_area_fraction_centroid*d.outline_height_area_weighted_centroid_m
 dump('ALGEBRAIC_DEPENDENCY_QA.json',{'centroid_sum_density_mean_identity_max_abs_error':float((derived-d.outline_area_fraction_centroid_sum).abs().max()),'centroid_supported_volume_identity_max_abs_error':float((volume-d.outline_volume_per_land_m_centroid).abs().max()),'union_coverage_not_identical_support':True,'FAR_not_computed':True})
 # Nonlinear/log relationship diagnostics using common pairs, no ranking of candidates.
 nl=[]
 for a,b in [('outline_count_per_km2_centroid','outline_area_mean_m2'),('BUILDVALUE','EAL_VALT'),('assessor2022_main_area_per_land','emc2022_total_built_land_fraction')]:
  d=f.loc[resids,[a,b]].dropna();d=d.loc[d.ge(0).all(axis=1)];x=np.log1p(d[a]);y=np.log1p(d[b]);rr=stats.pearsonr(x,y);nl.append({'x':a,'y':b,'transform':'log1p both nonnegative values','N':len(d),'GEOID_set_sha256':idhash(d.index),'pearson_log1p_r':rr.statistic})
 pd.DataFrame(nl).to_csv(OUT/'NONLINEAR_MEASUREMENT_DIAGNOSTICS.csv',index=False)
 return result

def main():
 f,ids=values();r=register(f);qa(f,r,ids);correlations(f,r,ids)
 validity=pd.DataFrame(index=f.index)
 for row in r.to_dict('records'):
  c=row['value_column'];validity[row['candidate_id']]=np.where(f[c].notna(),row['disposition']+'_MEASURED','MISSING_OR_INVALID') if c else 'NOT_MEASURED_'+row['disposition']
 validity.to_csv(OUT/'CANDIDATE_VALUE_VALIDITY.csv')
 for c in r.loc[r.disposition.eq('PENDING_DATA'),'candidate_id']:
  if c not in f:f[c]=np.nan
 f.to_csv(OUT/'CANDIDATE_VALUES_2315.csv',float_format='%.15g');f.loc[ids].to_csv(OUT/'CANDIDATE_VALUES_RESIDENTIAL_2291.csv',float_format='%.15g')
 dump('EXECUTION_ENVIRONMENT.json',{'python':sys.version if 'sys' in globals() else platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':__import__('scipy').__version__,'operation':'measurement extraction and admission only; no model fits','baseline':BASELINE})
 log(f'Candidate pool frozen: {len(r)} constructs/alternative measurements; dispositions {r.disposition.value_counts().to_dict()}')
if __name__=='__main__':main()
