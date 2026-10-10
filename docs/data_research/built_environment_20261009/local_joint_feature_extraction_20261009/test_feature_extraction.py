"""Focused scientific-identity, cohort, missingness and geometry-accounting checks."""
import json,hashlib
import numpy as np,pandas as pd
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[3]
CLASSES=['residential','commercial_office','industrial','institutional_public','transportation_utility','open_space_recreation','vacant_undeveloped','agriculture','mixed_use','under_construction','protected_undevelopable']
def table(n):return pd.read_csv(O/n,dtype={'tract_id':str}).set_index('tract_id')
def meta(n):return json.loads((O/n).read_text(encoding='utf-8-sig'))
def test_cohorts_and_no_selected_labels():
 f=table('TRACT_FEATURE_CANDIDATES.csv');s=table('RESIDENTIAL_2291_FEATURE_MATRIX.csv')
 assert len(f)==2315 and f.index.is_unique and f.index.str.fullmatch(r'\d{11}').all()
 assert len(s)==2291 and s.index.is_unique
 ids=pd.read_csv(R/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv',dtype={'tract_id':str}).tract_id.str.zfill(11)
 assert list(s.index)==list(ids)
 assert not any(k in f for k in ['cluster','PC1','PC2','Hotspot_SVI_Score'])
 pd.testing.assert_frame_equal(s,f.loc[s.index],check_dtype=False)
def test_formal_recovery_identity():
 d=table('RECOVERY_B_T80_INIT_COMPARISON.csv')
 assert d.B_480_hr.between(0,480).all() and d.Init_Supply.between(0,1+1e-12).all()
 assert np.allclose(d.AUC_480,1-d.B_480_hr/480,rtol=0,atol=1e-14)
 assert d.T80.notna().all() and d.T80.le(480).all()
 q=meta('RECOVERY_EXTRACTION_QA.json')
 assert '1000' in json.dumps(q)
 e=meta('FEATURE_ASSEMBLY_QA.json')['original_feature_max_errors']
 assert max(e.values())<1e-8
def test_missing_housing_and_land_are_explicit():
 f=table('TRACT_FEATURE_CANDIDATES.csv');q=meta('FEATURE_ASSEMBLY_QA.json')
 zero=f.housing_total.eq(0)
 assert zero.sum()>0
 assert f.loc[zero,['Pre_1970_Ratio','residential_pre1970_housing_share','housing_5plus_share']].isna().all().all()
 bad=~f.land_mask_area_check_pass
 assert int(bad.sum())==18
 assert f.loc[bad,['building_footprint_coverage','land_use_entropy','tract_seismic_PGA']].isna().all().all()
 assert f.loc[bad,'building_footprint_coverage_geometry_diagnostic'].notna().all()
def test_scag_area_entropy_and_source_accounting():
 d=table('SCAG_TRACT_LAND_USE.csv');q=meta('SCAG_GEOMETRY_QA.json')
 assert q['raw_records']==2406373 and q['stack_gt1_records']==336496
 area=d[[k+'_area_m2' for k in CLASSES]].sum(axis=1)
 assert np.allclose(area,d.land_use_classified_area_m2,rtol=1e-12,atol=1e-5)
 assert (area<=d.land_geometry_area_m2+1e-4).all()
 shares=d[[k+'_area_share' for k in CLASSES]].sum(axis=1)
 assert np.allclose(shares,d.land_use_classified_land_coverage,rtol=1e-10,atol=1e-10)
 p=d[[k+'_classified_share' for k in CLASSES]].to_numpy()
 entropy=-np.sum(np.where(p>0,p*np.log(np.where(p>0,p,1)),0),axis=1)/np.log(11)
 assert np.allclose(entropy,d.land_use_entropy,equal_nan=True,atol=1e-12)
 assert d.land_use_entropy.dropna().between(0,1+1e-12).all()
def test_footprints_counts_and_height():
 d=table('LARIAC2020_TRACT_URBAN_FORM.csv')
 assert d.building_footprint_coverage.between(0,1+1e-8).all()
 assert np.equal(d.building_count,np.floor(d.building_count)).all()
 assert d.building_height_valid_area_fraction.between(0,1+1e-8).all()
 assert d.building_height_median_m.dropna().gt(0).all()
 assert meta('LARIAC2020_GEOMETRY_QA.json')['raw_records']==3293177
 assert meta('LARIAC2020_HEIGHT_QA.json')['duplicate_geometry_height_conflicts']==2
 land=table('TRACT_GEOMETRY_LAND_WATER_QA.csv');f=table('TRACT_FEATURE_CANDIDATES.csv')
 assert np.allclose(d.building_count_density,d.building_count/(land.census_ALAND_m2/1e6),rtol=1e-12,atol=1e-10)
 assert np.allclose(d.building_count_density,f.building_count_density,rtol=1e-12,atol=1e-10)
def test_age_bounds_and_scope():
 for filename,prefix in [('BUILDING_AGE_ALL_USE_TRACTS.csv','all_use'),('BUILDING_AGE_2014_ORIGINAL_TRACTS.csv','all_use2014')]:
  d=table(filename);cov=d[prefix+'_age_coverage'];lo=d[prefix+'_pre1970_lower_bound'];hi=d[prefix+'_pre1970_upper_bound'];share=d[prefix+'_pre1970_area_share']
  assert cov.dropna().between(0,1+1e-8).all()
  assert np.allclose(hi-lo,1-cov,equal_nan=True,atol=1e-12)
  assert (share[share.notna()]>=lo[share.notna()]-1e-12).all()
  assert (share[share.notna()]<=hi[share.notna()]+1e-12).all()
  assert share[cov.eq(0)].isna().all()
 assert not meta('BUILDING_AGE_QA.json')['share_is_complete_all_buildings']
 assert meta('BUILDING_AGE_2014_CACHE_QA.json')['all_expected_source_intersections_match']
 assert meta('UNION_AREA_EQUIVALENCE_QA.json')['all_sampled_areas_match_direct_GEOS']
def test_pga_source_and_partial_support():
 f=table('TRACT_FEATURE_CANDIDATES.csv');q=meta('TRACT_SEISMIC_HAZARD_QA.json');ids=q['tracts_partial_support']
 assert q['official_download_exact_byte_match'] and q['station_source_max_error_g']<1e-12 and q['units']=='g'
 assert f.loc[ids,'tract_seismic_PGA'].isna().all()
 assert f.tract_seismic_PGA.dropna().gt(0).all()
 assert f.impervious_source_status.str.contains('UNVERIFIED').all()
def test_correlations_exact_matched_sets():
 f=table('RESIDENTIAL_2291_FEATURE_MATRIX.csv')
 for k in ['B_480_hr','NRI_BUILDVALUE','Pop_Density','building_count_density','housing_units_per_km2','building_height_area_weighted_m']:
  f['log1p_'+k]=np.log1p(f[k].where(f[k]>=0))
 c=pd.read_csv(O/'FEATURE_CORRELATION_MATRIX.csv')
 for row in c.itertuples():
  ids=f[[row.feature_a,row.feature_b]].dropna().index
  assert row.n==len(ids) and row.pairwise_missing==2291-len(ids)
  assert row.matched_tract_sha256==hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest()
 b=c[(c.feature_a=='B_480_hr')&(c.feature_b=='T80')].iloc[0]
 assert b.n==2291 and abs(b.pearson_r-.9121500907)<1e-8
def test_preservation_gate():
 q=meta('PRESERVATION_FINAL_QA.json')
 assert q['original_protected_count']==212 and q['protected_files_checked']==950
 assert q['scientific_files_changed']==0 and not q['protected_file_hash_changes'] and not q['formal_input_hash_changes']
 assert q['original_staging_unchanged'] and q['preexisting_staged_files']==862
