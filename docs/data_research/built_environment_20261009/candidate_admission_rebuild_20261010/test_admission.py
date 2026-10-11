"""Data-identity and scientific measurement gates; no model or simulation tests."""
from common import *
from build_admission import UNRESOLVED,SCAG
import pandas as pd,numpy as np

def frames():
 return pd.read_csv(OUT/'CANDIDATE_VALUES_2315.csv',dtype={'tract_id':str}).set_index('tract_id'),pd.read_csv(OUT/'CANDIDATE_VALUES_RESIDENTIAL_2291.csv',dtype={'tract_id':str}).set_index('tract_id')

def test_master_identity_and_preserved_science():
 f,r=frames();old=pd.read_csv(source('local_joint_feature_extraction_20261009/TRACT_FEATURE_CANDIDATES.csv'),dtype={'tract_id':str}).set_index('tract_id');res=pd.read_csv(source('final_feature_validation_20261010/FINAL_CANDIDATE_FEATURE_MATRIX.csv'),dtype={'tract_id':str}).set_index('tract_id')
 assert len(f)==2315 and len(r)==2291 and f.index.is_unique and r.index.is_unique
 assert f.index.str.fullmatch(r'06037\d{6}').all() and f.index.tolist()==old.index.tolist() and r.index.tolist()==res.index.tolist()
 for c in ['B_480_hr','T80','Init_Supply','SOVI_SCORE','formal_population','Grid_Degree','Grid_Impact','Grid_Betweenness','Redundancy_HHI']:
  assert np.allclose(f[c],old[c],rtol=1e-12,atol=1e-12,equal_nan=True),c
 assert not any('cluster' in c or 'PGA' in c for c in f)

def test_unresolved_geometry_does_not_erase_tabular_values():
 f,_=frames()
 for c in ['building_footprint_coverage','land_use_entropy','all_use2014_pre1970_area_share','emc2022_total_built_land_fraction','jrc_anbh_positive_surface_mean_m','outline_count_per_km2_centroid','nlcd_c10_pilot_impervious_land_fraction','nlcd_c12_2022_impervious_fraction','assessor2022_main_area_per_land','epa_household_job_activity_mix','scag2020_classified_land_entropy']:
  assert f.loc[UNRESOLVED,c].isna().all(),c
 for c in ['housing_5plus_share','housing_detached_share','BUILDVALUE','EAL_SCORE','ALR_NPCTL','assessor2022_actual_pre1970_main_area_share']:
  assert f.loc[UNRESOLVED,c].notna().all(),c

def test_pending_and_reject_not_falsely_admitted():
 f,_=frames();reg=pd.read_csv(OUT/'CANDIDATE_REGISTER.csv').fillna('')
 assert reg.candidate_id.is_unique and reg.disposition.isin(['ADMIT','CONDITIONAL','DESCRIPTIVE_ONLY','PENDING_DATA','REJECT']).all()
 for name in reg.loc[reg.disposition.eq('PENDING_DATA'),'candidate_id']:assert f[name].isna().all()
 assert reg.set_index('candidate_id').loc['all_use_pre1970_area_share','disposition']=='REJECT'
 for row in reg.itertuples():
  assert row.admission_condition_or_exclusion_reason and row.construct and row.definition
  if row.disposition=='ADMIT':assert row.valid_residential_2291>0

def test_acs_exact_replicates_and_denominators():
 f,_=frames();old=pd.read_csv(source('validation/ACS_TRACT_VALIDATION.csv'),dtype={'tract_id':str}).set_index('tract_id').loc[f.index]
 for c in ['housing_5plus_share','housing_5plus_share_moe90','housing_5plus_share_boundary_model','housing_5plus_share_zero_replicate_denominators']:
  assert np.allclose(f[c],old[c],rtol=1e-12,atol=1e-12,equal_nan=True)
 assert f.loc[f.housing_total.eq(0),'housing_detached_share'].isna().all()
 assert np.allclose(f.housing_detached_share+f.housing_attached_share,f.housing_single_unit_share,equal_nan=True,atol=1e-12)
 assert (f.housing_detached_share_moe90.dropna()>=0).all()

def test_raster_support_and_composition_limits():
 f,_=frames();valid=~f.index.isin(UNRESOLVED)
 for c in ['jrc_total_valid_land_coverage','jrc_nres_valid_land_coverage','jrc_height_valid_land_coverage']:assert np.allclose(f.loc[valid,c],1,atol=1e-6)
 assert f.emc2022_total_built_land_fraction.dropna().between(0,1).all()
 assert (f.emc2022_nres_built_land_fraction<=f.emc2022_total_built_land_fraction+1e-12).loc[valid].all()
 assert np.allclose(f.loc[valid,'nlcd_c12_valid_land_coverage'],1,atol=1e-6)
 assert f.nlcd_c12_2022_impervious_fraction.dropna().between(0,1).all()
 s=f[[c+'_classified_share' for c in SCAG]].dropna().sum(axis=1);assert np.allclose(s,1,atol=1e-6)
 q=json.loads((OUT/'ALGEBRAIC_DEPENDENCY_QA.json').read_text());assert q['centroid_sum_density_mean_identity_max_abs_error']<1e-10 and q['centroid_supported_volume_identity_max_abs_error']<1e-10

def test_fema_components_and_zero_exposure():
 f,_=frames()
 assert np.allclose(f.EAL_VALT,f.EAL_VALB+f.EAL_VALPE+f.EAL_VALA,rtol=1e-8,atol=.1)
 assert np.allclose(f.EAL_VALPE,11600000*f.EAL_VALP,rtol=1e-8,atol=.1)
 assert f.loc[f.AGRIVALUE.eq(0),'ALR_VALA'].isna().all()
 for c in ['BUILDVALUE','EAL_SCORE','EAL_VALT','ALR_NPCTL']:assert f[c].notna().all()

def test_acquisition_identity_and_single_year():
 a=json.loads((OUT/'ASSESSOR_ACQUISITION_COMPLETE.json').read_text());q=json.loads((OUT/'ASSESSOR_MEASUREMENT_QA.json').read_text());assert a['records']==a['expected']==2413689 and a['same_roll_only']
 assert q['unique_roll_year']==['2022'] and q['nonpersonal_fields_only']
 assert not any('Owner' in s or 'Mail' in s for s in a['fields'])
 for rec in json.loads((OUT/'JRC_ACQUISITION.json').read_text()):assert sha(Path(rec['path']))==rec['sha256']
 n=json.loads((OUT/'NLCD_C12_ACQUISITION.json').read_text());assert n['mapping_year']==2022 and n['collection']=='1.2' and n['archive_bytes']==962491880
 assert sha(OUT/'source_evidence/NLCD_C12_2022_STUDY_CLIP.tif')==json.loads((OUT/'NLCD_C12_MEASUREMENT_QA.json').read_text())['study_clip_sha256']

def test_statistics_have_real_samples_and_ids():
 p=pd.read_csv(OUT/'DEPENDENCY_AND_REDUNDANCY.csv');assert p.N.gt(4).all() and p.GEOID_set_sha256.str.fullmatch('[0-9a-f]{64}').all()
 assert p.scope.isin(['full2315','residential2291','SCAG_low_coverage_quartile','SCAG_high_coverage_quartile','assessor_low_multiline_share','assessor_high_multiline_share']).all()

def test_protection_record():
 a=json.loads((OUT/'PRESERVATION_BEFORE.json').read_text());b=json.loads((OUT/'PRESERVATION_AFTER.json').read_text())
 assert a['original_head']==b['original_head'] and a['logical_index_sha256']==b['logical_index_sha256'] and a['status_sha256']==b['status_sha256']
 assert a['protected_files']==b['protected_files'] and a['staged_count']==b['staged_count']

def test_pending_completion_dispositions_are_source_qualified():
 f,r=frames();reg=pd.read_csv(OUT/'CANDIDATE_REGISTER.csv').set_index('candidate_id')
 assert reg.loc['epa_household_job_activity_mix','disposition']=='CONDITIONAL'
 assert reg.loc['scag2020_classified_land_entropy','disposition']=='CONDITIONAL'
 assert reg.loc['assessor2022_gross_floor_area_ratio','disposition']=='PENDING_DATA'
 assert f.assessor2022_gross_floor_area_ratio.isna().all()
 assert 'ESTIMATED' in reg.loc['epa_household_job_activity_mix','numeric_status']
 assert reg.loc['scag2020_classified_land_entropy','valid_tracts_2315']==f.scag2020_classified_land_entropy.notna().sum()
 assert len(r)==2291 and len(f)==2315

def test_scag2020_exclusive_areas_and_actual_entropy():
 f,_=frames();d=f.loc[~f.index.isin(UNRESOLVED)]
 a=d[['scag2020_'+c+'_area_m2' for c in SCAG]]
 assert (a>=0).all().all()
 total=a.sum(axis=1);assert np.allclose(total,d.scag2020_classified_area_m2,atol=1e-6)
 assert (total<=d.scag2020_land_geometry_area_m2+1e-4).all()
 p=a.div(total.replace(0,np.nan),axis=0)
 h=-(p.where(p>0)*np.log(p.where(p>0))).sum(axis=1)/np.log(11)
 assert np.allclose(h.where(total>0),d.scag2020_classified_land_entropy,equal_nan=True,atol=1e-12)
 assert np.allclose(total/d.scag2020_land_geometry_area_m2,d.scag2020_classified_land_coverage,atol=1e-12)
 q=json.loads((OUT/'SCAG2020_GEOMETRY_AND_COVERAGE_QA.json').read_text())
 m=pd.read_csv(OUT/'SCAG2020_CHUNK_HASHES.csv')
 assert q['raw_records']==2093407==m['count'].sum()
 assert q['entropy_K']==11 and q['stack_gt1_records']>0
 assert not set(q['dictionary_missing_codes'])-{-1}

def test_epa_count_conservation_and_geometry_identity():
 q=json.loads((OUT/'EPA_ACTIVITY_CROSSWALK_QA.json').read_text())
 assert q['cached_source_records']==6425 and q['donors']==6421 and q['source_records_without_donor_polygon']==4
 assert all(v==0 for v in q['missing_polygon_counts'].values())
 assert all(v==0 for k,v in q['source_numeric_match_max_differences'].items() if k!='D2A_EPHHM')
 assert q['source_entropy_reproduction_max_difference']<1e-7
 for c,v in q['county_source_totals'].items():assert np.isclose(v,q['county_target_plus_outside_totals'][c],atol=1e-5,rtol=1e-7)
 x=pd.read_csv(OUT/'EPA_DONOR_TO_TRACT_CROSSWALK.csv',dtype={'donor_geoid10':str,'donor_geoid2018':str,'tract_id':str})
 assert x.donor_geoid10.str.len().eq(12).all() and x.tract_id.str.len().eq(11).all()
 assert np.allclose(x.intersection_land_m2/x.donor_land_m2,x.allocation_fraction,atol=1e-12)
 assert x.groupby('donor_geoid10').allocation_fraction.sum().le(1+1e-6).all()
 f,_=frames();counts=['epa_allocated_'+c for c in ['HH','E5_Ret','E5_Off','E5_Ind','E5_Svc','E5_Ent']]
 from measure_epa_activity import entropy
 assert np.allclose(entropy(f[counts]),f.epa_household_job_activity_mix,atol=1e-12,equal_nan=True)
 assert f.epa_donor_land_coverage.dropna().between(0,1+1e-6).all()
 assert f.loc[f.epa_activity_total.eq(0),'epa_household_job_activity_mix'].isna().all()

def test_assessor_floor_identity_does_not_invent_building_dedup():
 q=json.loads((OUT/'ASSESSOR_FLOOR_AREA_AND_OWNERSHIP_QA.json').read_text())
 assert q['unique_AIN']==q['county_assignment_records']==2413687
 assert q['disposition']=='PENDING_DATA' and q['no_coordinate_or_attribute_deduplication_rule_adopted']
 assert len(q['missing_required_evidence'])==4
 d=pd.read_csv(OUT/'ASSESSOR2022_FLOOR_IDENTITY_DIAGNOSTICS.csv')
 assert (d.assessor2022_restricted_singleline_noncondo_nonshared_main_area_m2<=d.assessor2022_positive_main_area_m2+1e-6).all()
 assert d.assessor2022_restricted_main_area_support_fraction.dropna().between(0,1).all()
 p=pd.read_csv(OUT/'ASSESSOR2022_PARCEL_GEOMETRY_IDENTITY_SAMPLE.csv')
 assert len(p)==40 and p.roll_years.astype(str).eq('2022').all()
 assert (p.unique_returned_ain<=p.cached_assessment_ain).all()

def test_followup_protects_original_worktree():
 a=json.loads((OUT/'PENDING_COMPLETION_PROTECTION_BEFORE.json').read_text())
 b=json.loads((OUT/'PENDING_COMPLETION_PROTECTION_AFTER.json').read_text())
 for key in ['original_head','logical_index_sha256','status_sha256','protected_files','staged_count']:
  assert a[key]==b[key],key

def test_followup_delivery_hashes_and_summary_are_actual():
 hashes=json.loads((OUT/'PENDING_COMPLETION_DERIVED_HASHES.json').read_text())
 assert all(sha(OUT/name)==expected for name,expected in hashes.items())
 summary=pd.read_csv(OUT/'PENDING_DATA_COMPLETION_SUMMARY.csv').set_index('candidate')
 reg=pd.read_csv(OUT/'CANDIDATE_REGISTER.csv').set_index('candidate_id')
 for key in summary.index:
  assert summary.loc[key,'disposition']==reg.loc[key,'disposition']
  assert summary.loc[key,'valid_full_2315']==reg.loc[key,'valid_tracts_2315']
  assert summary.loc[key,'valid_residential_2291']==reg.loc[key,'valid_residential_2291']
