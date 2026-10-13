"""Independent source arithmetic, geographic, matrix, silhouette and preservation checks."""
from datetime import datetime, timezone
from decimal import Decimal
from itertools import combinations
import importlib.metadata
import platform
import ast
import geopandas as gpd
import fitz
from PIL import Image
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import adjusted_rand_score
from threadpoolctl import threadpool_limits
from common import *


def main():
    checks=[]
    def check(name,detail):
        checks.append(dict(check=name,status='PASS',detail=detail));print('PASS',name,flush=True)
    state=json.loads(lp(OUT/'STARTING_STATE_AND_PROTECTION.json').read_text())
    s=reader();d=frame('FROZEN_COHORT_AND_COMPARATORS.csv','tract_id')
    original=read(s,EH+'VERIFIED_EIGHT_VARIABLE_COHORT.csv','tract_id').reindex(d.index)
    assert len(d)==2299 and d.index.is_unique and d.index.str.fullmatch(r'\d{11}').all()
    assert d.Population.gt(0).all() and d.Population.sum()==9066522 and d.additional_zero_housing_positive_population.sum()==8
    np.testing.assert_array_equal(d[P2].to_numpy(),original[P2].to_numpy())
    np.testing.assert_array_equal(d.frozen_SOVI_quartile,original.frozen_SOVI_quartile)
    assert len(frame('EXCLUDED_ZERO_POPULATION_GEOIDS.csv'))==16
    check('cohort_first7_population_quartile_identity','2299 /9066522;8 positive zero-housing;16 exclusions;exact11-digitIDs')
    acq=json.loads(lp(OUT/'OFFICIAL_SOURCE_ACQUISITION_AND_HASHES.json').read_text())['records']
    for row in acq:
        if row.get('file'):assert sha(OUT/row['file'])==row['sha256']
    byname={r['name']:r for r in acq}
    records=[]
    for row in acq:
        if row['name'].startswith('COLUMBIA_LA_GEOJSON_B100_'):
            payload=json.loads(lp(OUT/row['file']).read_bytes());assert not payload.get('exceededTransferLimit',False)
            records.extend(z['properties'] for z in payload['features'])
    inv=json.loads(lp(OUT/byname['COLUMBIA_LA_OBJECT_IDS']['file']).read_bytes())['objectIds']
    assert len(records)==len(inv)==2343 and {r['OBJECTID_1'] for r in records}==set(inv)
    saved=frame('COLUMBIA_SOURCE_ATTRIBUTE_RECORDS.csv','source_2010_GEOID')
    for row in records:
        values=[row[h+'_hazcat5'] for h in ['wind','tor','hail','cfh','wf','tsu','hi','vol','ls','eq','ww','hu','dr','fl']]
        assert sum(Decimal(str(v)) for v in values if v is not None)==Decimal(str(row['hazsum5']))
        for h in ['wind','tor','hail','cfh','wf','tsu','hi','vol','ls','eq','ww','hu','dr','fl']:
            assert (row[h+'_hazcat5'] is None)==pd.isna(saved.loc[row['FIPS'],h+'_hazcat5'])
    check('raw_payload_hash_OID_and_NHI_sum','All acquired/failed payload hashes;2343 unique OIDs;Decimal sum;NULL preservation')
    relation=pd.read_csv(lp(OUT/byname['CENSUS_RELATION_CA']['file']),sep='|',dtype=str)
    geo=frame('COLUMBIA_NHI_2010_TO_2020_GEOGRAPHY_QA.csv','tract_id')
    for tract in d.index:
        rr=relation.loc[relation.GEOID_TRACT_20.eq(tract)]
        lands=rr.AREALAND_PART.astype(float)
        support=lands[rr.GEOID_TRACT_10.isin(saved.index)].sum()/float(rr.AREALAND_TRACT_20.iloc[0])
        assert abs(support-geo.loc[tract,'official_land_supported_fraction'])<1e-12
    gap=geo.official_land_supported_fraction.lt(1-1e-8)
    assert gap.sum()==11 and d.loc[gap,'Population'].sum()==46455
    target=gpd.read_file(lp(OUT/'TARGET_2020_GEOMETRY.gpkg')).set_index('tract_id').reindex(d.index)
    donor=gpd.read_file(lp(OUT/'COLUMBIA_2010_GEOMETRY.gpkg')).set_index('FIPS')
    pairs=frame('COLUMBIA_GEOMETRIC_OVERLAP_PAIRS.csv')
    # Independently recompute actual polygon intersection areas for every donor pair on gap targets.
    for r in pairs.loc[pairs.tract_id.isin(d.index[gap])].itertuples():
        actual=target.loc[r.tract_id,'geometry'].intersection(donor.loc[r.source_2010_GEOID,'geometry']).area
        assert abs(actual-r.overlap_m2)<max(1e-5,actual*1e-10)
    assert target.geometry.is_valid.all() and donor.geometry.is_valid.all()
    check('Census_land_relation_and_gap_geometry','2299 independent official land fractions;11 gaps/46455residents;all gap polygon-pair overlaps recomputed')
    n=pd.read_csv(lp(OUT/'sources/FEMA_NRI_v119_CA_FROZEN.csv'),dtype={'TRACTFIPS':str},float_precision='round_trip').set_index('TRACTFIPS')
    assert sha(OUT/'sources/FEMA_NRI_v119_CA_FROZEN.csv')==sha(s.source('Data/NRI_Table_CensusTracts_California.csv',AUTH))
    assert len(n)==9106 and set(n.NRI_VER)=={'Mar-23'}
    reg=json.loads(lp(OUT/'FEMA_NCV_ADAPTATION_REGISTRATION.json').read_text())
    all18=['AVLN','CFLD','CWAV','DRGT','ERQK','HAIL','HWAV','HRCN','ISTM','LNDS','LTNG','RFLD','SWND','TRND','TSUN','VLCN','WFIR','WNTW']
    normalized={};factor={};sr=frame('FEMA_NCV_HAZARD_COMPONENT_VALUES.csv','tract_id')
    for h in all18:
        fraction=n[h+'_EXP_AREA']/n.AREA
        valid=n.AREA.gt(0)&n[h+'_AFREQ'].ge(0)&n[h+'_EXP_AREA'].ge(0)&fraction.le(1+1e-9)
        value=(n[h+'_AFREQ']*fraction).where(valid);factor[h]=value
        np.testing.assert_allclose(value.loc[d.index],sr[h+'_NCV_raw'],atol=1e-12,rtol=1e-14,equal_nan=True)
        assert not (fraction.loc[d.index]>1+1e-9).any()
        if h in reg['hazards']:normalized[h]=(value-value.min())/(value.max()-value.min())
    assert [h for h in all18 if factor[h].loc[d.index].notna().all()]==reg['hazards']
    for h in ['AVLN','HRCN','ISTM','VLCN']:assert factor[h].loc[d.index].isna().all()
    total=pd.DataFrame(normalized).sum(1,min_count=14)
    independently=(total-total.min())/(total.max()-total.min())
    v=frame('FEMA_NCV_CANDIDATE_VECTORS.csv','tract_id').reindex(d.index)
    np.testing.assert_allclose(independently.loc[d.index],v.FEMA_NCV14_CA_v119,rtol=1e-14,atol=1e-14)
    assert total.notna().sum()==reg['final_sum_CA_complete14_reference_count']
    examples=frame('WILLIAMS_FACTOR_REAL_SOURCE_EXAMPLES.csv')
    for r in examples.itertuples():
        dec=Decimal(str(r.AFREQ_as_released))*Decimal(str(r.impacted_sqmi))/Decimal(str(r.total_sqmi))
        assert abs(float(dec)-r.NCV)<1e-12
    check('FEMA_source18_formula_and_CA_normalization','Originalv1.19 bytes;18 factors;fourNULLs remainNULL;14 valid without clipping;Decimal examples')
    information=frame('HAZARD_INDEX_INCREMENTAL_INFORMATION.csv')
    candidates=frame('CANDIDATE_TRACT_VALUES.csv','tract_id').reindex(d.index)
    design=np.column_stack([np.ones(len(d)),d[P2].to_numpy(float)])
    for row in information.itertuples():
        y=candidates[row.candidate].to_numpy(float)
        prediction=design@np.linalg.lstsq(design,y,rcond=None)[0]
        r2=1-np.square(y-prediction).sum()/np.square(y-y.mean()).sum()
        assert abs(r2-row.conditional_linear_R2)<1e-8 and abs(1/(1-r2)-row.VIF)<1e-8
    check('information_independent_linear_R2_VIF','NumPy least-squares cross-check;random and spatial nonlinear folds preserved as conditional diagnostics')
    fit=np.load(lp(OUT/'REGISTERED_CONDITIONAL_FIT_ARRAYS.npz'))
    mats=np.load(lp(OUT/'REGISTERED_CONDITIONAL_MATRICES.npz'))
    centers=np.load(lp(OUT/'REGISTERED_MODEL_CENTERS.npz'))
    f=frame('CONDITIONAL_K_AND_STABILITY_RESULTS.csv')
    oldmat=np.load(lp(OUT/'FROZEN_COMPARATOR_WEIGHTED_MATRICES.npz'))
    np.testing.assert_array_equal(mats['main'][:,:7],oldmat['H2__published'][:,:7])
    np.testing.assert_allclose(mats['main'],weighted(d,v.FEMA_NCV14_CA_v119),atol=1e-14,rtol=0)
    assert len(fit['keys'])==len(f)==204 and list(fit['tract_ids'])==list(d.index)
    blocks=(d.utm_x_m.ge(d.utm_x_m.median()).astype(int)*2+d.utm_y_m.ge(d.utm_y_m.median()).astype(int)).to_numpy()
    results=[];distances={};maxsil=0.;maxinertia=0.
    for i,key in enumerate(fit['keys']):
        row=f.iloc[i];condition=row.condition;assert int(key.rsplit('__s',1)[1])==row.seed
        x=mats[condition];lab=fit['labels'][i];center=centers[key];k=len(center)
        train=blocks!=int(condition[-1]) if condition.startswith('geographic_block') else np.ones(len(d),bool)
        np.testing.assert_array_equal(cdist(x,center,'sqeuclidean').argmin(1),lab)
        inertia=np.square(x[train]-center[lab[train]]).sum();maxinertia=max(maxinertia,abs(inertia-row.WCSS))
        assert abs(inertia-row.WCSS)<1e-8
        if k>1:
            if condition not in distances:
                distances.clear()
                distances[condition]=cdist(x,x,'euclidean')
            dist=distances[condition];a=np.zeros(len(d));b=np.full(len(d),np.inf)
            for c in range(k):
                mask=lab==c;ct=mask.sum();summ=dist[:,mask].sum(1)
                a[mask]=summ[mask]/(ct-1) if ct>1 else 0
                b[~mask]=np.minimum(b[~mask],summ[~mask]/ct)
            independent=(b-a)/np.maximum(a,b)
            maxsil=max(maxsil,float(np.max(np.abs(independent-fit['silhouette'][i]))))
            np.testing.assert_allclose(independent,fit['silhouette'][i],atol=2e-7,rtol=0)
            assert abs(independent.mean()-row.mean_silhouette)<2e-7
        results.append(dict(key=key,inertia_error=abs(inertia-row.WCSS),silhouette_checked=k>1))
    # Pairwise distance caches are temporary memory only, never repository outputs.
    distances.clear()
    check('all204_matrices_labels_inertia_silhouette',dict(maximum_inertia_error=maxinertia,maximum_silhouette_error=maxsil,method='SciPy independent distances; per-class summation formula'))
    keyindex={k:i for i,k in enumerate(fit['keys'])}
    sensitivity=frame('HAZARD_LEAVE_ONE_OUT_SENSITIVITY.csv')
    for row in sensitivity.itertuples():
        a=fit['labels'][keyindex[f'NCV14__main__k{row.k}__s42']]
        b=fit['labels'][keyindex[f'NCV14__hazard_{row.condition}__k{row.k}__s42']]
        assert abs(adjusted_rand_score(a,b)-row.ARI)<1e-14
        ct=np.zeros((row.k,row.k),int);np.add.at(ct,(a,b),1)
        ri,ci=linear_sum_assignment(-ct);mapping=dict(zip(ci,ri));changed=a!=np.array([mapping[z] for z in b])
        assert changed.sum()==row.reassigned_tracts and d.Population.to_numpy()[changed].sum()==row.reassigned_population
    check('hazard_sensitivity_independent_ARI_and_alignment','All45 hazard/normalization comparisons;tract/resident reassignment;no formal IDs')
    qa_fig=[]
    manifest=json.loads(lp(OUT/'FIGURE_MANIFEST.json').read_text())
    visual=json.loads(lp(OUT/'VISUAL_INSPECTION.json').read_text())
    for rec in visual['figures']:
        assert rec['pdf_sha256']==sha(OUT/'figures'/ (rec['figure']+'.pdf'))
    assert len(manifest['figures'])==8 and not manifest['AI_images_used']
    for rec in manifest['figures']:
        with fitz.open(str(lp(OUT/rec['pdf']))) as doc:
            assert len(doc)==1
            text=doc[0].get_text();assert 'NOT FORMAL STAGE 7' in text
            assert abs(doc[0].rect.width-7.2*72)<.05
            outside=[]
            for block in doc[0].get_text('dict')['blocks']:
                if 'lines' not in block:continue
                for line in block['lines']:
                    for span in line['spans']:
                        box=fitz.Rect(span['bbox'])
                        if not doc[0].rect.contains(box):outside.append(span['text'])
            assert not outside, (rec['name'],outside)
        with Image.open(lp(OUT/rec['png'])) as im:
            assert im.width>=4300 and abs(im.info['dpi'][0]-600)<.1
            qa_fig.append(dict(name=rec['name'],width=im.width,height=im.height,dpi=im.info['dpi'],text_within_page=True))
    check('eight_vector_PDFs_and600dpi_preview_dimensions','8 native7.2-inch pages;alltext in page bounds;AI=false;manual visual QA recorded separately')
    for path in lp(OUT).glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
    for rel,digest in state['protected_files'].items():assert sha(SOURCE_ROOT/rel)==digest,rel
    assert len(state['protected_files'])==950
    assert hashlib.sha256(git('status','--porcelain',cwd=SOURCE_ROOT)).hexdigest()==state['original_status_sha256']
    assert hashlib.sha256(git('diff','--cached','--binary',cwd=SOURCE_ROOT)).hexdigest()==state['original_staged_diff_sha256']
    current=tree();assert all(current.get(p)==oid for p,oid in state['authoritative_git_blobs'].items())
    check('950_files_prior_packages_original_staging_preserved','950 actualSHA256;allauthorityGitblobs;originaldirty/stagedstatusbytes;package-only writing')
    versions={name:importlib.metadata.version(name) for name in ['numpy','pandas','geopandas','shapely','scikit-learn','scipy','matplotlib','PyMuPDF','Pillow','requests','threadpoolctl']}
    dump('INDEPENDENT_NUMERICAL_AND_PRESERVATION_QA.json',dict(review_status=WARN,authority=AUTH,checks=checks,all_checks_passed=True,python=platform.python_version(),versions=versions,completed_UTC=datetime.now(timezone.utc).isoformat(),figure_checks=qa_fig,limitations=['Selected modeled source completeness is not validation of all physical layers','Geography sensitivity usesfour blocks','Exactpublishednine aggregate andnationalfrozen normalization unavailable']))
    save('INDEPENDENT_FIT_CHECKS.csv',results)
    save('SOURCE_HASH_VERIFICATION_INDEPENDENT.csv',s.records)
    files={}
    for path in lp(OUT).rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(lp(OUT)).as_posix()
        if rel.startswith('tmp/') or '__pycache__' in Path(rel).parts or rel in ['DERIVED_FILE_HASHES.json','REMOTE_DELIVERY_VERIFICATION.json']:continue
        files[rel]=dict(sha256=sha(path),bytes=path.stat().st_size)
    dump('DERIVED_FILE_HASHES.json',dict(review_status=WARN,files=files))
    print('INDEPENDENT QA COMPLETE',len(checks),'checks',len(files),'hashes',flush=True)


if __name__=='__main__':
    with threadpool_limits(limits=1):main()
