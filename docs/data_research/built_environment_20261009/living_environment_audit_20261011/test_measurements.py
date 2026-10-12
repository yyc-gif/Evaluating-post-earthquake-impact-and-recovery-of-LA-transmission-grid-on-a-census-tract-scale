"""Independent byte, identity, ratio, uncertainty and exact-sample checks."""
from common import *
import pandas as pd,zipfile,fitz
from scipy import stats

def values():return pd.read_csv(lp(OUT/'LIVING_ENVIRONMENT_VALUES_2315.csv'),dtype={'tract_id':str},float_precision='round_trip').set_index('tract_id')
def test_cohort_identity_and_unchanged_context():
    f=values();ids=np.load(lp(OUT/'COHORT_IDENTITIES.npz'))
    parent=frame('candidate_admission_rebuild_20261010/CANDIDATE_VALUES_2315.csv')
    assert f.index.equals(parent.index) and len(f)==2315 and not f.index.duplicated().any()
    assert f.index.str.fullmatch(r'\d{11}').all()
    for c in ['formal_population','residential_member','Pop_Density','Pop_Density_per_km2','SOVI_SCORE','emc2022_total_built_land_fraction','housing_5plus_share','housing_5plus_share_moe90']:
        np.testing.assert_allclose(f[c],parent[c],rtol=0,atol=0,equal_nan=True)
    for name,n in [('residential_ids',2291),('reference_ids',2287)]:
        assert len(ids[name])==n
        suffix='RESIDENTIAL_2291' if n==2291 else 'REFERENCE_2287'
        df=pd.read_csv(lp(OUT/f'LIVING_ENVIRONMENT_VALUES_{suffix}.csv'),dtype={'tract_id':str})
        assert np.array_equal(df.tract_id.to_numpy(),ids[name])
    assert set(ids['residential_ids'])-set(ids['reference_ids'])==set(UNRESOLVED)
    assert f.loc[UNRESOLVED,['electric_heating_share','housing_5plus_share','canopy_2022_fraction','parks_all_published_fraction']].notna().all().all()
    assert not any(c.lower() in ['cluster','cluster_id','label','pc1','pc2'] for c in f.columns)

def test_acquired_source_bytes_and_failed_route_separation():
    records=json.loads(lp(OUT/'ACQUISITION_RECORDS.json').read_text());last={r['file']:r for r in records}
    for name,r in last.items():assert sha(OUT/'sources'/name)==r['sha256']
    assert b'html' in lp(OUT/'sources/ACS_B25040_LA.json').read_bytes()[:500].lower()
    catalog=pd.read_csv(lp(OUT/'SOURCE_URLS_AND_CHECKSUMS.csv'))
    for name in ['ACS_B25040_LA.json','CDC_SVI2020_CA_VALID.csv','CDC_SVI2020_CA.csv','PARKS_API_METADATA.payload','CANOPY_RASTER_ITEM_DATA.json']:
        assert not catalog.loc[catalog.file.eq('sources/'+name),'numeric_measurement_used'].iloc[0]
    with zipfile.ZipFile(lp(OUT/'sources/B25040_06.csv.zip')) as z:assert len(z.namelist())>0

def test_canopy_units_matches_and_geometry_qualifications():
    f=values();ref=f.loc[f.reference2287]
    np.testing.assert_allclose(f.canopy_2022_fraction,f.canopy_PctCan22/100,atol=1e-14,equal_nan=True)
    np.testing.assert_allclose((f.canopy_CanoAcr22/f.canopy_AREA22).dropna(),.00024711,rtol=1e-8)
    assert ref.canopy_2022_fraction.between(0,1).all()
    assert set(f.index[~f.canopy_source_match])=={'06037980020','06037980026'}
    assert (ref.canopy_land_geometry_IoU<.9).sum()==21
    assert (ref.canopy_whole_tract_geometry_IoU<.9).sum()==42
    assert (ref.canopy_implied_analysis_to_source_tract_area<.99).sum()==22
    q=json.loads(lp(OUT/'CANOPY_GEOGRAPHY_INTERPRETATION_QA.json').read_text())
    assert q['geometry_remapping_performed']==False

def test_parks_original_values_roundoff_and_undefined_denominators():
    f=values();p=pd.read_csv(lp(OUT/'sources/PARKS_DOWNLOAD_0.payload'),dtype={'geoid':str,'geoid20':str})
    p['tract_id']=p.geoid.str[-11:];p=p.set_index('tract_id').reindex(f.index)
    assert (p.geoid20.str.zfill(11)==f.index).all()
    for c,raw,count in [('parks_all_published_fraction','park_access_pct','park_access_count'),('parks_good_published_fraction','good_park_access_pct','good_park_access_count')]:
        valid=p.denom_total_pop>0
        np.testing.assert_allclose(f.loc[valid,c],p.loc[valid,raw]/100,atol=1e-15)
        assert f.loc[~valid,c].isna().all()
        assert np.nanmax(abs(p[raw]-100*p[count]/p.denom_total_pop))<1e-4
    assert (f.parks_good_published_fraction<=f.parks_all_published_fraction+1e-5).fillna(True).loc[f.parks_all_published_fraction.notna()].all()
    assert f.loc[f.reference2287,'parks_all_published_fraction'].notna().all()
    q=json.loads(lp(OUT/'PARKS_NUMERICAL_QA.json').read_text());assert not q['population_weighting_verified'] and not q['area_weighting_verified']

def test_heating_uncertainty_independent_raw_calculation():
    f=values();cols=[f'Var_Rep{i}' for i in range(1,81)]
    with zipfile.ZipFile(lp(OUT/'sources/B25040_06.csv.zip')) as z:x=pd.read_csv(z.open(z.namelist()[0]),dtype={'GEOID':str})
    x=x.loc[x.GEOID.str.startswith('1400000US06037',na=False)].copy();x['tract_id']=x.GEOID.str[-11:]
    d=x.loc[x.ORDER.eq(1)].set_index('tract_id').reindex(f.index);n=x.loc[x.ORDER.eq(4)].set_index('tract_id').reindex(f.index)
    ok=d.ESTIMATE>0;p=n.ESTIMATE/d.ESTIMATE
    np.testing.assert_allclose(f.loc[ok,'electric_heating_share'],p[ok],atol=1e-14)
    nr=n[cols].to_numpy();dr=d[cols].to_numpy();r=np.divide(nr,dr,out=np.zeros_like(nr),where=dr!=0)
    se=np.sqrt(.05*np.sum((r-p.to_numpy()[:,None])**2,axis=1));boundary=ok.to_numpy()&((p==0)|(p==1)|(se==0))
    dw=d.ESTIMATE.to_numpy();aw=np.divide(16,dw,out=np.full(len(dw),np.nan),where=dw>0);pstar=np.minimum(.5,2.3*aw);bs=np.sqrt(pstar*(1-pstar)*aw);se[boundary]=bs[boundary]
    np.testing.assert_allclose(f.loc[ok,'electric_heating_share_moe90'],1.645*se[ok],rtol=1e-12,atol=1e-14)
    assert f.loc[~ok,'electric_heating_share'].isna().all() and (~ok).sum()==24
    assert (f.loc[f.reference2287,'electric_heating_share_moe90']>.1).sum()==568
    assert (f.loc[f.reference2287,'housing_5plus_share_moe90']>.1).sum()==211

def test_exact_sample_correlations_and_conditional_variance():
    f=values();r=pd.read_csv(lp(OUT/'CANDIDATE_REDUNDANCY.csv'));sets=json.loads(lp(OUT/'COMPARISON_GEOID_SETS.json').read_text())
    for _,row in r.loc[r.kind.eq('pairwise_reference')].iterrows():
        ids=sets[row.GEOID_order_sha256];assert len(ids)==row.n and idhash(ids)==row.GEOID_order_sha256
        a=f.loc[ids,row.candidate_a];b=f.loc[ids,row.candidate_b]
        assert np.isclose(stats.pearsonr(a,b).statistic,row.Pearson,atol=1e-12)
        assert np.isclose(stats.spearmanr(a,b).statistic,row.Spearman,atol=1e-12)
    row=r.loc[r.kind.eq('residual_variance_existing_controls')&r.candidate_a.eq('electric_heating_share')].iloc[0]
    ids=sets[row.GEOID_order_sha256];X=np.c_[np.ones(len(ids)),f.loc[ids,row.controls.split(';')].to_numpy()];y=f.loc[ids,'electric_heating_share'].to_numpy()
    residual=y-X@np.linalg.lstsq(X,y,rcond=None)[0]
    assert np.isclose(np.var(residual)/np.var(y),row.residual_variance_fraction)
    assert row.n==2287

def test_pdf_native_width_text_and_page_counts():
    expected={'LIVING_ENVIRONMENT_DISTRIBUTIONS.pdf':1,'LIVING_ENVIRONMENT_GEOGRAPHIC_COVERAGE.pdf':4,'LIVING_ENVIRONMENT_REDUNDANCY.pdf':2}
    for name,n in expected.items():
        doc=fitz.open(lp(OUT/'figures'/name));assert len(doc)==n
        for page in doc:
            assert abs(page.rect.width*25.4/72-185)<.01
            spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
            assert min(s['size'] for s in spans)>=7.5
            assert all(s['bbox'][0]>=-0.5 and s['bbox'][2]<=page.rect.width+.5 for s in spans)
