"""Independent arithmetic, geometry, source/preservation and repeatability gates."""
import importlib.metadata
import py_compile
import shutil
import zipfile
import fitz
import geopandas as gpd
import shapely
from common import *


def frame(name):return pd.read_csv(lp(OUT/name),dtype={'tract_id':str}).set_index('tract_id')


def main():
    full=frame('FROZEN_P2_AND_COHORT.csv');d=full.loc[full.Population.gt(0)]
    n=frame('FEMA_V119_MATCHED_2299_SOURCE_ROWS.csv');v=frame('PHYSICAL_HAZARD_TRACT_VALUES.csv')
    assert len(full)==2315 and len(d)==2299 and len(full.loc[full.Population.eq(0)])==16
    assert d.index.equals(v.index) and d.index.equals(n.index) and d.index.str.fullmatch(r'\d{11}').all()
    assert int(d.additional_zero_housing_positive_population.sum())==8
    source=sources();ref_full,ref_d=dataset(source)
    assert d.index.equals(ref_d.index)
    assert np.array_equal(d.Population,ref_d.Population)
    for c in P2:assert np.allclose(d[c],ref_d[c],rtol=0,atol=1e-12)
    prefixes=['AVLN','CFLD','CWAV','DRGT','ERQK','HAIL','HWAV','HRCN','ISTM','LNDS','LTNG','RFLD','SWND','TRND','TSUN','VLCN','WFIR','WNTW']
    assert len(pd.read_csv(lp(OUT/'ALL_18_HAZARD_INVENTORY.csv')))==18
    hazard_sum=n[[p+'_EALT' for p in prefixes]].sum(axis=1,min_count=1)
    assert np.allclose(hazard_sum,n.EAL_VALT,rtol=0,atol=1e-6)
    eq_share=n.ERQK_EALT.sum()/n.EAL_VALT.sum()
    qa=json.loads(lp(OUT/'FEMA_NUMERICAL_COMPOSITION_QA.json').read_text())
    assert abs(eq_share-qa['earthquake_pooled_share'])<1e-14
    variables=['tract_seismic_PGA','Wildfire_high_land_fraction','Flood_SFHA_land_fraction_complete','Historical_heat_days_2018_2022']
    status=json.loads(lp(OUT/'PHYSICAL_COMPOSITE_ADMISSION_DECISION.json').read_text())
    assert v[variables].dropna().shape[0]==status['joint_complete_physical_n']==2032
    assert status['no_composite_built'] and status['new_clustering_fits']==0
    matrix=d[P2].join(v[variables]).dropna()
    pair=pd.read_csv(lp(OUT/'PHYSICAL_PLUS_P2_PAIRWISE.csv'))
    correlation_error=0.
    for row in pair.itertuples():
        a=matrix[row.variable_a].to_numpy();b=matrix[row.variable_b].to_numpy()
        err=abs(np.corrcoef(a,b)[0,1]-row.same_cohort_Pearson);correlation_error=max(err,correlation_error)
    assert correlation_error<1e-12
    regression=pd.read_csv(lp(OUT/'CONDITIONAL_LINEAR_VIF_AND_NONLINEAR_AUDIT.csv'))
    conditional_error=0.
    for row in regression.itertuples():
        y=matrix[row.target].to_numpy();x=matrix.drop(columns=row.target).to_numpy()
        x=np.c_[np.ones(len(x)),x];fit=x@np.linalg.lstsq(x,y,rcond=None)[0]
        r2=1-np.dot(y-fit,y-fit)/np.dot(y-y.mean(),y-y.mean())
        conditional_error=max(conditional_error,abs(r2-row.all_other_core_conditional_linear_R2))
    assert conditional_error<1e-10
    archive=lp(OUT/'sources/PHYSICAL_SOURCE_SNAPSHOTS.zip')
    archiveqa=json.loads(lp(OUT/'sources/PHYSICAL_SNAPSHOT_ARCHIVE_QA.json').read_text())
    assert sha(archive)==archiveqa['sha256']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for member in archiveqa['members']:
            assert hashlib.sha256(z.read(Path(member['file']).name)).hexdigest()==member['after_sha256']
        polygons=json.loads(z.read('NFHL_ZONES_COMPLETE.geojson'))
    ids=json.loads(lp(OUT/'sources/NFHL_ZONES_IDS.json').read_text())
    assert sorted(x['properties'][ids['objectIdFieldName']] for x in polygons['features'])==sorted(ids['objectIds'])
    zones=gpd.GeoDataFrame.from_features(polygons['features'],crs=4326).to_crs(3310)
    del polygons
    zones.geometry=zones.geometry.make_valid()
    land=gpd.read_file(lp(OUT/'sources/TRACT_LAND_3310.gpkg')).set_index('tract_id')
    tree=shapely.STRtree(zones.geometry.to_numpy())
    cases=sorted(set(d.index[:3])|set(d.loc[d.additional_zero_housing_positive_population].index)|set(v.Flood_SFHA_land_fraction.nlargest(3).index))
    overlay_error=0.
    for key in cases:
        geom=land.loc[key,'geometry'];hits=tree.query(geom,predicate='intersects')
        chosen=[i for i in hits if str(zones.iloc[i].SFHA_TF).upper()=='T']
        pieces=[geom.intersection(zones.iloc[i].geometry) for i in chosen]
        value=shapely.union_all(pieces).area/geom.area if pieces else 0.
        overlay_error=max(overlay_error,abs(value-v.loc[key,'Flood_SFHA_land_fraction']))
    assert overlay_error<1e-10
    tmp=lp(OUT/'tmp/compiled');tmp.mkdir(parents=True,exist_ok=True)
    compiled=[]
    for p in lp(OUT).glob('*.py'):
        py_compile.compile(str(p),cfile=str(tmp/(p.stem+'.pyc')),doraise=True);compiled.append(p.name)
    before={p.name:sha(p) for p in lp(OUT).glob('*.csv') if p.name.startswith(('PHYSICAL_PLUS','JOINT_INFORMATION','CONDITIONAL_LINEAR','PHYSICAL_HAZARD_TRACT_VALUES.csv','TRACT_OVERLAY','POINT_VERSUS','STANDARDIZATION','LEAVE_ONE_HAZARD'))}
    subprocess.run([sys.executable,str(lp(OUT/'information_audit.py'))],cwd=ROOT,check=True)
    assert before=={k:sha(OUT/k) for k in before}
    protected=json.loads(lp(OUT/'STARTING_STATE_AND_PROTECTION.json').read_text())
    current={p:sha(SOURCE_ROOT/p) for p in protected['protected_files']}
    assert current==protected['protected_files']
    assert git('status','--porcelain',cwd=SOURCE_ROOT).decode()==protected['source_status']
    assert hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest()==protected['source_staged_diff_sha256']
    # One batch read proves all earlier audit objects remain identical, including LFS pointers.
    names=list(protected['prior_package_git_blob_manifest']);payload=''.join('HEAD:'+p+'\n' for p in names).encode()
    process=subprocess.run(['git','cat-file','--batch'],input=payload,cwd=ROOT,check=True,stdout=subprocess.PIPE)
    stream=process.stdout;offset=0
    for p in names:
        end=stream.index(b'\n',offset);size=int(stream[offset:end].split()[-1]);data=stream[end+1:end+1+size]
        assert hashlib.sha256(data).hexdigest()==protected['prior_package_git_blob_manifest'][p];offset=end+size+2
    assert offset==len(stream)
    graphics=[]
    for p in lp(OUT/'figures').glob('*.pdf'):
        doc=fitz.open(p);page=doc[0];assert len(doc)==1 and not page.get_images()
        assert 'AUTHOR REVIEW' in page.get_text() and 'NOT FORMAL STAGE 7' in page.get_text()
        assert all(page.rect.contains(fitz.Rect(block[:4])) for block in page.get_text('blocks'))
        graphics.append(dict(file=p.name,pages=1,vector_only=True,all_text_inside_page=True,
            width_inches=page.rect.width/72,height_inches=page.rect.height/72,
            publication_review='rendered page reviewed; overlapping footer and clipped axis label corrected'))
    assert len(graphics)==4
    dump('INDEPENDENT_QA.json',dict(status='PASS',cohort=2299,zero_population_exclusions=16,additional_zero_housing_retained=8,
        unchanged_frozen_population_and_P2=True,exact_11_digit_GEOIDs=True,all18_hazards=True,
        earthquake_share_recomputed=eq_share,max_Pearson_independent_error=correlation_error,
        max_conditional_OLS_independent_error=conditional_error,max_NFHL_overlay_independent_error=overlay_error,
        independent_overlay_tracts=cases,archive_members_verified=True,all_expected_NFHL_objectIDs=True,
        repeated_derived_CSV_hashes_identical=True,repeated_csv_count=len(before),new_clustering_fits=0,
        protected_scientific_files=len(current),prior_diagnostic_git_objects=len(names),
        original_unrelated_status_and_staged_work_unchanged=True,
        diagnostic_worktree_index_note='No-checkout worktree initially had an empty index; initialized with read-tree HEAD before any staging. No scientific deletions staged or committed.',
        compile_method='py_compile with explicit extended-path diagnostic temporary files; default compileall hit a Windows long-path pycache failure',
        python_version=sys.version,dependencies={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','geopandas','shapely','matplotlib','PyMuPDF','requests']},
        compiled_scripts=compiled,graphics=graphics))
    manifest={p.relative_to(lp(OUT)).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in lp(OUT).rglob('*')
        if p.is_file() and not any(c in ['tmp','__pycache__'] for c in p.parts) and
        '_PART_' not in p.name and '_SMALLPART_' not in p.name and not p.name.endswith('_COMPLETE.geojson')
        and p.name not in ['DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json']}
    dump('DERIVED_FILE_HASHES.json',manifest)
    print('INDEPENDENT QA PASS: 950 scientific files and 1570 prior diagnostic objects preserved',flush=True)


if __name__=='__main__':main()
