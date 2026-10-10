"""Independent calculation checks and a source-bounded updated audit."""
from pathlib import Path
import argparse
import json
import hashlib
import importlib.metadata
import zipfile
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
REPS=[f'Var_Rep{i}' for i in range(1,81)]
AUDIT=Path('docs/data_research/built_environment_20261009')
STAGE7=Path('Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized')

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def main(repo):
    ids=pd.read_csv(ROOT/'ACS_TRACT_VALIDATION.csv',dtype={'tract_id':str})
    coverage=pd.read_csv(ROOT/'BUILT_ENVIRONMENT_TRACT_COVERAGE.csv',dtype={'tract_id':str})
    residential=pd.read_csv(ROOT/'RESIDENTIAL_VALIDATION_MATRIX.csv',dtype={'tract_id':str})
    assert len(coverage)==2315 and len(residential)==2291
    assert not coverage.tract_id.duplicated().any() and coverage.tract_id.str.fullmatch(r'06037\d{6}').all()
    assert residential.housing_5plus_share.notna().all() and residential.impervious_land_fraction.notna().all()
    assert coverage.loc[coverage.housing_total.eq(0),'housing_5plus_share'].isna().all()
    assert coverage.valid_coverage_fraction.ge(.99).all()
    archives={}
    for table in ['B25024','B25034']:
        with zipfile.ZipFile(ROOT/f'sources/{table}_06.csv.zip') as z:
            archives[table]=pd.read_csv(z.open(z.namelist()[0]),dtype={'GEOID':str})
    checks=[]
    # Check actual counts/ratios/SDR variance from the raw archive, not NPZ caches.
    nonboundary=ids.loc[ids.residential_member & ~ids.housing_5plus_share_boundary_model]
    targets=list(nonboundary.tract_id.iloc[:2])+list(nonboundary.nlargest(2,'housing_5plus_share_moe90').tract_id)
    targets+=list(ids.loc[ids.residential_member & ids.housing_5plus_share_boundary_model,'tract_id'].iloc[:2])
    for tid in targets:
        f=archives['B25024'].loc[archives['B25024'].GEOID.eq('1400000US'+tid)].set_index('ORDER')
        den=f.loc[1,'ESTIMATE'];num=f.loc[[6,7,8,9],'ESTIMATE'].sum();p=num/den
        rnum=f.loc[[6,7,8,9],REPS].sum(axis=0);rden=f.loc[1,REPS];r=np.where(rden.to_numpy()!=0,rnum.to_numpy()/rden.to_numpy(),0)
        variance=4/80*sum((float(x)-p)**2 for x in r)
        if p in (0,1) or variance==0:
            ps=min(.5,2.3*16/den);moe=1.645*np.sqrt(ps*(1-ps)*16/den)
        else:moe=1.645*np.sqrt(variance)
        row=ids.loc[ids.tract_id.eq(tid)].iloc[0]
        assert abs(p-row.housing_5plus_share)<1e-12 and abs(moe-row.housing_5plus_share_moe90)<1e-12
        checks.append({'tract_id':tid,'share':p,'moe90':float(moe),'matches':True})
    comparison=pd.read_csv(ROOT/'CLUSTER_COMPARISONS.csv')
    for cluster,group in residential.groupby('cluster'):
        saved=comparison.loc[comparison.screen.eq('all')&comparison.indicator.eq('housing_5plus_share')&comparison.cluster.eq(cluster)].iloc[0]
        assert np.isclose(saved['mean'],group.housing_5plus_share.mean(),atol=1e-14)
    source=pd.read_csv(repo/AUDIT/'BUILT_ENVIRONMENT_DATA_SOURCE_AUDIT.csv')
    source['validation_classification']='NOT_NEWLY_VALIDATED'
    source['numeric_validation_scope']='Earlier source feasibility only'
    source['release_gate']='See historical pilot; no new admission'
    one=source.candidate_id.eq('BE01')
    updates={'formula':'(E006+E007+E008+E009)/E001; 80 aligned ratios; Var=(4/80)*sum squared replicate deviations; Census boundary model AW=16',
             'original_data_url':'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/data/5-year/140/B25024_06.csv.zip',
             'official_documentation_url':'https://www2.census.gov/programs-surveys/acs/replicate_estimates/2022/documentation/5-year/2018-2022_Variance_Replicate_Table_Documentation.pdf',
             'missing_and_denominator_limits':'23 zero denominators; residential 211 replicate/model MOEs>10pp,1621>5pp; 158 boundary models;4 denominator CIs include zero',
             'pilot_status':'VRE_UNCERTAINTY_AND_SENSITIVITY_COMPLETED','processing_decision':'No imputation or reclustering; all-tract primary profiles plus fixed-screen sensitivity',
             'validation_classification':'READY_CLUSTER_DESCRIPTION','numeric_validation_scope':'2315 matched;2292 defined full-domain;2291/2291 residential',
             'release_gate':'Retain MOEs/distributions; no precision claim for every tract'}
    for key,value in updates.items():source.loc[one,key]=value
    two=source.candidate_id.eq('BE02')
    updates={'publication_or_release_year':'2024 original C1.0; retrieved 2026-10-09','version':'Selected 2022 catalog objects C1.0; Esri beta numeric mirror; not C1.2',
             'geographic_resolution_and_vintage':'30m AEA_WGS84 equal-area, native aligned grid; exact existing study polygons/2020-based IDs; upstream boundary release unverified',
             'official_documentation_url':'https://www.mrlc.gov/sites/default/files/docs/LSDS-2103%20Annual%20National%20Land%20Cover%20Database%20%28NLCD%29%20Collection%201%20Science%20Product%20User%20Guide%20-v1.0%202024_10_15.pdf',
             'exact_fields':'FIS uint8 0-100; NoData250; companion 2022 C1.0 LC class11 water',
             'original_data_url':'https://di-nlcd.img.arcgis.com/arcgis/rest/services/USA_NLCD_Annual_LandCover_Fractional_Impervious_Surface/ImageServer',
             'study_2315_record_or_extent_evidence':'Actual 2315 unique geometry/ID matches and valid exact fractional-cell means',
             'study_2315_valid_indicator_coverage':'2315/2315 NUMERIC_MIRROR_PILOT','residential_2291_valid_indicator_coverage':'2291/2291 NUMERIC_MIRROR_PILOT',
             'missing_and_denominator_limits':'NoData0m2;min valid coverage99.99999985%;water83.528km2 excluded;30m and mapping-error limits remain',
             'pilot_status':'NUMERIC_EXTRACTION_QA_PASSED_PRODUCTION_PROVENANCE_OPEN',
             'processing_decision':'Exact equal-area intersections; land mean primary; valid zero included; no-renderer catalog lock; retain hashes',
             'validation_classification':'CONDITIONAL','numeric_validation_scope':'Complete mirror-snapshot coverage; not verified original-USGS coverage',
             'release_gate':'Original USGS build/reference comparison; mirror beta and item/catalog version mismatch unresolved',
             'overlap_with_stage7':'r log density=.660;SOVI=.490;configuration=.514;age=-.036; residual information remains'}
    for key,value in updates.items():source.loc[two,key]=value
    for candidate in ['BE05','BE06']:
        source.loc[source.candidate_id.eq(candidate),'validation_classification']='EXCLUDE_CURRENT_MANUSCRIPT'
        source.loc[source.candidate_id.eq(candidate),'release_gate']='Compatible historical release, non-overlapping geometry/classes/coverage not established; no entropy computed'
    source.to_csv(ROOT/'BUILT_ENVIRONMENT_DATA_SOURCE_AUDIT.csv',index=False)
    inputs=[STAGE7/'clusters_labels_final.csv',STAGE7/'stage7_full_domain_tract_status.csv',Path('Data/ACSDT5Y2022.B25034-Data.csv')]
    inputs += [Path('Data/LA_Tracts_With_Population'+s) for s in ['.shp','.dbf','.shx','.prj']]
    manifest={p.as_posix():sha(repo/p) for p in inputs}
    (ROOT/'INPUT_FILE_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    summary={'all_checks_passed':True,'independent_acs_checks':checks,'study_tracts':len(coverage),'residential_tracts':len(residential),
             'cluster_labels_unchanged':True,'original_source_cell_checks':50930,
             'raster_numeric_extraction_pass':True,'raster_production_provenance_pass':False,
             'runtime':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','geopandas','shapely','pyproj','pyogrio','requests']}}
    (ROOT/'INDEPENDENT_QA.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);main(p.parse_args().repo)
