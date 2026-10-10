"""Source-partition, estimand and preservation checks; no model fitting."""
from pathlib import Path
import hashlib,json
import fitz
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.metrics import adjusted_rand_score

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
SOURCE=HERE.parent/'final_feature_validation_20261010'

def frame(name):return pd.read_csv(HERE/name,dtype={'tract_id':str})

def test_saved_membership_and_exclusion():
    l=frame('STAGE7_CANDIDATE_LABELS_2291.csv');d=frame('CLASSIFIED_FEATURE_VALUES_2287.csv')
    z=np.load(SOURCE/'run_records/D__equal_five_domains.npz')['s42_k4']
    assert len(l)==2291 and l.tract_id.is_unique and l.tract_id.str.fullmatch(r'\d{11}').all()
    assert len(d)==2287 and np.array_equal(l.set_index('tract_id').loc[d.tract_id,'source_raw_cluster'].to_numpy(),z)
    unknown=l[l.classification_status=='UNCLASSIFIED_GEOMETRY']
    assert len(unknown)==4 and unknown.candidate_cluster.isna().all() and unknown.source_raw_cluster.isna().all()
    original=pd.read_csv(SOURCE/'FINAL_CANDIDATE_FEATURE_MATRIX.csv',dtype={'tract_id':str})
    assert l.tract_id.tolist()==original.tract_id.tolist()

def test_preprocessing_recovery_and_domain_budget():
    j=json.loads((HERE/'STAGE7_CANDIDATE_FREEZE.json').read_text());p=np.load(HERE/'STAGE7_CANDIDATE_PARAMETERS.npz')
    assert j['new_KMeans_fits']==0 and j['formal_files_written']==0
    assert hashlib.sha256(np.ascontiguousarray(p['weighted_standardized_matrix']).tobytes()).hexdigest()==j['matrix_sha256']
    assert hashlib.sha256('\n'.join(p['tract_id']).encode()).hexdigest()==j['tract_order_sha256']
    factors=p['coordinate_factors'];start=0
    for domain in j['domains'].values():
        n=len(domain['features']);assert np.isclose(np.square(factors[start:start+n]).sum(),.2);start+=n
    assert np.isclose(np.square(factors).sum(),1)
    closest=np.square(p['weighted_standardized_matrix'][:,None]-p['label_mean_centers'][None]).sum(2).argmin(1)
    assert np.array_equal(closest,p['labels'])

def test_profiles_are_unweighted_and_population_is_explicit():
    d=frame('CLASSIFIED_FEATURE_VALUES_2287.csv');p=frame('STAGE7_CLUSTER_PROFILES.csv').set_index('candidate_cluster')
    assert p.n_tracts.sum()==2287 and p.population_sum.sum()==d.formal_population.sum()
    for c,v in d.groupby('candidate_cluster'):
        assert p.loc[c,'n_tracts']==len(v)
        for col in ['B_480_hr','T80','Init_Supply','SOVI_SCORE','land_use_entropy','building_footprint_coverage','all_use2014_pre1970_area_share','NRI_BUILDVALUE','ALR_NPCTL']:
            assert np.isclose(p.loc[c,col+'_mean'],v[col].mean(),atol=1e-12)
            assert np.isclose(p.loc[c,col+'_median'],v[col].median(),atol=1e-12)
        assert np.isclose(p.loc[c,'B_480_hr_population_weighted_mean'],np.average(v.B_480_hr,weights=v.formal_population))
    assert np.isclose(frame('UNCLASSIFIED_TRACT_CHARACTERISTICS.csv').formal_population.sum(),12390)

def test_crosswalk_no_row_order_assumption():
    x=frame('STAGE7_OLD_NEW_CROSSWALK.csv');l=frame('CLASSIFIED_FEATURE_VALUES_2287.csv')
    old=pd.read_csv(REPO/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/clusters_labels_final.csv',dtype={'tract_id':str})
    old.tract_id=old.tract_id.str.zfill(11);joined=l[['tract_id','candidate_cluster']].merge(old[['tract_id','cluster']],on='tract_id',validate='one_to_one')
    assert len(x)==20 and x.n_intersection.sum()==2287
    assert np.allclose(x.ARI,adjusted_rand_score(joined.cluster,joined.candidate_cluster))
    assert np.allclose(x.groupby('original_cluster').fraction_of_original.sum(),1)
    assert np.allclose(x.groupby('candidate_cluster').fraction_of_candidate.sum(),1)
    assert x.loc[(x.original_cluster==5)&(x.candidate_cluster=='C2'),'n_intersection'].iloc[0]==34

def test_actual_pdf_text_and_resolution():
    for name in ['FIG_STAGE7_TYPOLOGY_MAP','FIG_STAGE7_CLUSTER_PROFILE','FIG_STAGE7_SPATIAL_ROBUSTNESS']:
        doc=fitz.open(HERE/(name+'.pdf'));assert len(doc)==1
        assert abs(doc[0].rect.width/72*25.4-185)<.01
        spans=[s for b in doc[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
        assert spans and min(s['size'] for s in spans)>=7
        assert all('Arial' in s['font'] for s in spans)
        assert not doc[0].get_images()  # Native vector geometries and heatmap mesh.
        assert all(doc[0].rect.contains(fitz.Rect(s['bbox'])) for s in spans)
        with Image.open(HERE/(name+'.png')) as im:
            assert abs(im.width/(185/25.4)-600)<1

def test_no_scientific_runners_in_preview_scripts():
    for n in ['build_preview.py','render_preview.py','write_drafts.py']:
        t=(HERE/n).read_text();assert 'KMeans(' not in t and 'fit_predict(' not in t
