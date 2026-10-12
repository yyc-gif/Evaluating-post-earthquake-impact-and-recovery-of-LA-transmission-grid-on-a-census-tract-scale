"""Reuse archived land masks to distinguish water clipping from geographic disagreement."""
from common import *
from audit_values import corr,CANDIDATES,CONTEXT
import pandas as pd,geopandas as gpd,shapely,shutil,itertools

def archived_land():
    record=json.loads(src('candidate_admission_rebuild_20261010/LAND_GEOMETRY_REUSE.json').read_text())
    dest=lp(OUT/'sources/ARCHIVED_STUDY_LAND.gpkg')
    if not dest.exists():
        for root in [ROOT.parent/x for x in ['_ca10','_sr11','_ad11']]+[ORIGINAL]:
            q=lp(root/PREFIX/'candidate_admission_rebuild_20261010/raw_cache/study_land.gpkg')
            if q.exists() and sha(q)==record['output_sha256']:
                shutil.copyfile(q,dest);break
    assert dest.exists() and sha(dest)==record['output_sha256']
    dump('ARCHIVED_LAND_REUSE.json',dict(source_record_commit=BASELINE,source_record='candidate_admission_rebuild_20261010/LAND_GEOMETRY_REUSE.json',sha256=sha(dest),bytes=dest.stat().st_size,source_water_vintage=2020,source_tract_geometry='031d2c675f8e7d58035d27448be040b809ced086:Data/LA_Tracts_With_Population.shp',new_geometry_extraction=False,unresolved_four=UNRESOLVED))
    return gpd.read_file(dest).set_index('tract_id')

def run():
    f=pd.read_csv(lp(OUT/'LIVING_ENVIRONMENT_VALUES_2315.csv'),dtype={'tract_id':str},float_precision='round_trip').set_index('tract_id')
    ids=np.load(lp(OUT/'COHORT_IDENTITIES.npz'))
    g=archived_land().reindex(f.index)
    fs=[]
    for offset in [0,1000,2000]:fs+=json.loads(lp(OUT/f'sources/CANOPY_LA_{offset}.geojson').read_text())['features']
    a=gpd.GeoDataFrame.from_features(fs,crs=4326).to_crs(3310).set_index('FIPS').reindex(f.index)
    rows=[]
    for tract in f.index:
        x=g.loc[tract].geometry;y=a.loc[tract].geometry
        row=dict(tract_id=tract,reference2287=bool(f.loc[tract,'reference2287']),residential_member=bool(f.loc[tract,'residential_member']),land_mask_unresolved=tract in UNRESOLVED,formal_population=f.loc[tract,'formal_population'])
        if x is not None and y is not None and x.is_valid and y.is_valid and tract not in UNRESOLVED:
            row.update(archived_land_area_m2=x.area,canopy_geometry_area_m2=y.area,land_geometry_IoU=x.intersection(y).area/x.union(y).area,land_centroid_distance_m=x.centroid.distance(y.centroid),canopy_implied_to_archived_land_area=f.loc[tract,'canopy_implied_analysis_area_m2']/x.area)
        rows.append(row)
    land=pd.DataFrame(rows).set_index('tract_id');save('CANOPY_LAND_GEOMETRY_COMPARISON.csv',land.reset_index())
    old=pd.read_csv(lp(OUT/'CANOPY_GEOMETRY_COMPARISON.csv'),dtype={'tract_id':str}).set_index('tract_id')
    audit=old.join(land[['land_geometry_IoU','land_centroid_distance_m','land_mask_unresolved','canopy_implied_to_archived_land_area']]).join(f[['reference2287','formal_population','Pop_Density_per_km2','canopy_implied_analysis_to_source_tract_area']])
    audit['whole_geometry_IoU_below_0_90_diagnostic']=audit.geometry_IoU<.9
    audit['land_geometry_IoU_below_0_90_diagnostic']=audit.land_geometry_IoU<.9
    save('CANOPY_GEOGRAPHIC_SUPPORT_FLAGS.csv',audit.reset_index())
    f['canopy_land_geometry_IoU']=land.land_geometry_IoU
    f['canopy_whole_tract_geometry_IoU']=old.geometry_IoU
    f['canopy_implied_to_archived_land_area']=land.canopy_implied_to_archived_land_area
    ref=f.loc[f.reference2287]
    summary=dict(reference_n=len(ref),whole_tract_IoU_lt_0_9_n=int((ref.canopy_whole_tract_geometry_IoU<.9).sum()),land_IoU_lt_0_9_n=int((ref.canopy_land_geometry_IoU<.9).sum()),land_IoU_quantiles=ref.canopy_land_geometry_IoU.quantile([0,.01,.05,.5,.95,1]).to_dict(),source_analysis_fraction_lt_0_99_n=int((ref.canopy_implied_analysis_to_source_tract_area<.99).sum()),land_analysis_fraction_lt_0_99_n=int((ref.canopy_implied_to_archived_land_area<.99).sum()),whole_difference_not_automatically_boundary_vintage_error=True,IoU_0_90_is_diagnostic_not_admission_threshold=True,geometry_remapping_performed=False)
    dump('CANOPY_GEOGRAPHY_INTERPRETATION_QA.json',summary)
    rows=pd.read_csv(lp(OUT/'CANDIDATE_REDUNDANCY.csv')).to_dict('records');sets=json.loads(lp(OUT/'COMPARISON_GEOID_SETS.json').read_text())
    for tag,mask in [('source_analysis_area_ge_99pct',ref.canopy_implied_analysis_to_source_tract_area>=.99),('land_geometry_IoU_ge_0_90',ref.canopy_land_geometry_IoU>=.9),('land_geometry_and_source_support', (ref.canopy_land_geometry_IoU>=.9)&(ref.canopy_implied_analysis_to_source_tract_area>=.99))]:
        for x,y in itertools.combinations(CANDIDATES+CONTEXT,2):
            d=ref.loc[mask,[x,y]].dropna();pr,sr=corr(d[x],d[y]);key=idhash(d.index);sets[key]=d.index.tolist()
            rows.append(dict(kind='measurement_support_sensitivity_'+tag,candidate_a=x,candidate_b=y,n=len(d),GEOID_order_sha256=key,Pearson=pr,Spearman=sr,interval='none; diagnostic subset, no values excluded from master'))
    # Idempotent reuse: repeated calls replace, rather than duplicate, these observation kinds.
    r=pd.DataFrame(rows).drop_duplicates(['kind','candidate_a','candidate_b'],keep='last')
    save('CANDIDATE_REDUNDANCY.csv',r);dump('COMPARISON_GEOID_SETS.json',sets)
    save('LIVING_ENVIRONMENT_VALUES_2315.csv',f.reset_index())
    save('LIVING_ENVIRONMENT_VALUES_RESIDENTIAL_2291.csv',f.loc[ids['residential_ids']].reset_index())
    save('LIVING_ENVIRONMENT_VALUES_REFERENCE_2287.csv',f.loc[ids['reference_ids']].reset_index())
    q=json.loads(lp(OUT/'SVI_COMPONENT_SCOPE_QA.json').read_text())
    q['mechanical_overlap']='SVI2020 EP_MUNIT = (DP04_0012E + DP04_0013E) / E_HU *100: 10+ units from 2016-2020 ACS DP04. Housing5plus uses B25024 orders6-9 /order1, 2018-2022 ACS. Nested housing configuration constructs and overlapping survey years, not identical coordinates.'
    dump('SVI_COMPONENT_SCOPE_QA.json',q)
    log('Archived land-mask check distinguishes water exclusions from residual geographic mismatch; no source or formal geometry changed.')
    print(summary)
if __name__=='__main__':run()
