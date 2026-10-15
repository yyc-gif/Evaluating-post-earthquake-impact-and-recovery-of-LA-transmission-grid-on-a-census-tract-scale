"""Current P2 adoption invariants; historical suite tests remain in Git history."""
from pathlib import Path
import csv
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

import fitz
import numpy as np
import pandas as pd
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review'
AUTH=ROOT/'results/stage7/P2_K3_2299'
QA=ROOT/'docs/reproducibility/p2_final_adoption_20261014'
PB=ROOT/'docs/data_research/stage7_path_b_p2_integration_review_20261014'
BASE='937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f'
FEATURES=['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','log1p_Population']
BUDGET=np.array([1/9,1/9,1/9,1/6,1/6,1/6,1/6])
ACTIVE=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in range(1,11)]
sys.path.insert(0,str(ROOT/'src'))


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def df(p):return pd.read_csv(p,dtype={'tract_id':str},float_precision='round_trip')
def features():return df(AUTH/'tract_features.csv')
def rows():return list(csv.DictReader((SUITE/'FIGURE_MANIFEST.csv').open(encoding='utf-8-sig')))
def caps():return (SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))


def source(path):
    blob=git('show',BASE+':'+path)
    m=re.search(rb'oid sha256:([a-f0-9]{64})\nsize (\d+)',blob)
    if not m:return blob
    oid=m[1].decode()
    common=Path(git('rev-parse','--path-format=absolute','--git-common-dir').decode().strip())
    for candidate in [ROOT/path,common/'lfs/objects'/oid[:2]/oid[2:4]/oid]:
        if candidate.is_file() and sha(candidate)==oid:
            data=candidate.read_bytes();assert len(data)==int(m[2]);return data
    raise AssertionError('Missing hash-bound source payload: '+path)


def test_exact_17_numbered_pairs():
    assert {r['final_name'] for r in rows()}=={s+'.'+e for s in ACTIVE for e in ['pdf','png']}
    assert len(rows())==34


def test_manifest_matches_actual_artwork():
    for r in rows():assert sha(ROOT/r['current_source_file'])==r['sha256']


def test_every_mirror_is_byte_identical():
    for r in rows():assert sha(ROOT/r['mirror_file'])==r['sha256']


def test_exactly_15_unaffected_artwork_pairs():
    changes=df(QA/'FIGURE_CHANGE_MANIFEST.csv')
    assert int(changes.unchanged.sum())==30
    for r in changes.itertuples():
        if r.unchanged:assert sha(SUITE/r.figure)==r.baseline_sha256==r.current_sha256
    assert set(changes.loc[~changes.unchanged,'figure'])=={s+'.'+e for s in ['Main/Fig07','Supplement/FigS08'] for e in ['pdf','png']}


def test_s05_and_merged_resource_artwork_preserved():
    changes=df(QA/'FIGURE_CHANGE_MANIFEST.csv').set_index('figure')
    for s in ['Main/Fig01','Main/Fig05','Supplement/FigS04','Supplement/FigS05','Supplement/FigS10']:
        for e in ['pdf','png']:assert bool(changes.loc[s+'.'+e,'unchanged'])


def test_no_extra_numbered_artwork_or_retired_numbering():
    for folder in ['Main','Supplement']:
        actual={str(p.relative_to(SUITE)).replace('\\','/') for p in (SUITE/folder).iterdir() if p.suffix in ['.pdf','.png']}
        assert actual=={r['final_name'] for r in rows() if r['final_name'].startswith(folder+'/')}
    assert not any((SUITE/'Supplement'/f'FigS{n:02d}.pdf').exists() for n in [11,12,13])


def test_publication_pngs_and_native_dimensions():
    for stem in ACTIVE:
        with fitz.open(SUITE/(stem+'.pdf')) as art,Image.open(SUITE/(stem+'.png')) as im:
            assert im.width>=4320
            assert abs(im.width/im.height-art[0].rect.width/art[0].rect.height)<.002
            assert abs(art[0].rect.width-(7.2*72 if stem in ['Main/Fig07','Supplement/FigS08'] else 185*72/25.4))<.2


def test_all_native_previews_exist():
    assert all((SUITE/'Page_Previews'/(Path(stem).name+'.png')).is_file() for stem in ACTIVE)


def test_packet_page_counts():
    assert len(fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))==21
    assert len(fitz.open(SUITE/'ALL_MAIN_FIGURES.pdf'))==7
    assert len(fitz.open(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf'))==10


def test_packet_embeds_each_actual_artwork_at_native_size():
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as book:
        for i,stem in enumerate(ACTIVE):
            with fitz.open(SUITE/(stem+'.pdf')) as art:
                rect=art[0].rect
                assert book[i].rect.width==rect.width and book[i].rect.height>rect.height
                assert book[i].get_pixmap(clip=rect).samples==art[0].get_pixmap().samples


def test_all_caption_forms_are_short_and_legible():
    registry=list(csv.DictReader((QA/'COMPACT_PACKET_PAGE_REGISTRY.csv').open(encoding='utf-8')))
    assert len(registry)==17
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as book:
        for i,r in enumerate(registry):
            p=book[i];rect=fitz.Rect(0,float(r['figure_height_pt']),p.rect.width,p.rect.height)
            text=' '.join(p.get_text(clip=rect).split())
            assert ' '.join(r['title'].split()) in text
            assert ' '.join(r['caption'].split()) in text
            assert len(r['caption'].split())<=115
            assert float(r['caption_min_font_pt'])>=10
            assert 'proposal' not in r['title'].lower()


def test_realization_ranges_are_distinct_from_mean_effect_confidence_intervals():
    text=caps();parts=dict(re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)',text,re.M|re.S))
    four=next(b for h,b in parts.items() if h.startswith('Figure 4.'))
    six=next(b for h,b in parts.items() if h.startswith('Figure 6.'))
    assert 'realization ranges' in four and 'not confidence intervals' in four
    assert '95% bootstrap confidence intervals for mean effects' in six


def test_active_cross_references_and_continuous_supplement_numbering():
    text=caps()
    assert [int(n) for n in re.findall(r'^## Supplementary Figure S(\d+)\.',text,re.M)]==list(range(1,11))
    assert not re.search(r'\bS(?:11|12|13)\b',text)
    assert 'Supplementary Figures S12/S13' not in text
    assert 'Supplementary Figure S10' in text


def test_sole_current_selector_is_p2_seven_variables():
    p=read(ROOT/'config/current_stage7.json');s=read(AUTH/'feature_schema_and_identity.json')
    assert p['version']=='P2_K3_2299' and p['fitted_feature_count']==7
    assert s['feature_names']==FEATURES and s['primary_K']==3 and s['sensitivity_K']==4
    assert 'FEMA_NCV14_CA_v119' not in s['feature_names']


def test_every_primary_feature_is_finite_and_exactly_saved():
    f=features();frozen=df(PB/'FROZEN_P2_TRACT_TABLE_2315.csv').query('Population>0')
    assert len(f)==2299 and np.isfinite(f[FEATURES]).all().all()
    np.testing.assert_array_equal(f[FEATURES],frozen[FEATURES])
    np.testing.assert_array_equal(f.tract_id,frozen.tract_id)


def test_every_saved_k3_membership_and_class_identity():
    f=features();saved=np.load(PB/'inputs/REGISTERED_FIT_ARRAYS.npz')
    idx=list(saved['keys']).index('P2__main5__cohort__k3__s42')
    np.testing.assert_array_equal(f.K3_class,saved['labels'][idx]+1)
    np.testing.assert_array_equal(f.tract_id,saved['tract_ids'])
    assert f.K3_class.value_counts().sort_index().tolist()==[1235,428,636]
    assert f.groupby('K3_class').Population.sum().astype(int).tolist()==[5184036,1695501,2186985]


def test_population_cohort_exclusions_and_zero_housing_inclusion():
    f=features();full=df(AUTH/'stage7_full_domain_tract_status.csv')
    assert len(full)==2315 and len(f)==2299 and f.Population.sum()==9066522
    assert full.Population.eq(0).sum()==16 and full.K3_class.isna().sum()==16
    assert f.additional_zero_housing_positive_population.sum()==8
    assert f.loc[f.additional_zero_housing_positive_population,'K3_class'].notna().all()
    assert f.tract_id.str.fullmatch(r'\d{11}').all() and f.tract_id.is_unique


def test_original_population_and_quartiles_are_unchanged():
    f=features();saved=df(PB/'FROZEN_P2_TRACT_TABLE_2315.csv').query('Population>0')
    np.testing.assert_array_equal(f.Population,saved.Population)
    np.testing.assert_array_equal(f.frozen_SOVI_quartile,saved.frozen_SOVI_quartile)
    assert f.frozen_SOVI_quartile.eq('Q4').sum()==579


def test_exact_squared_distance_budgets_and_domain_totals():
    weights=df(AUTH/'standardizer_and_weights.csv')
    assert weights.variable.tolist()==FEATURES
    np.testing.assert_allclose(weights.squared_distance_budget,BUDGET,atol=1e-16,rtol=0)
    np.testing.assert_allclose(weights.coordinate_multiplier,np.sqrt(BUDGET),atol=1e-16,rtol=0)
    assert all(abs(weights.squared_distance_budget.iloc[lo:hi].sum()-1/3)<1e-15 for lo,hi in [(0,3),(3,5),(5,7)])


def test_frozen_population_sd_standardization():
    f=features();w=df(AUTH/'standardizer_and_weights.csv');raw=f[FEATURES].to_numpy()
    np.testing.assert_allclose(raw.mean(0),w.cohort_mean,atol=1e-12,rtol=1e-13)
    np.testing.assert_allclose(raw.std(0),w.population_SD,atol=1e-12,rtol=1e-13)
    np.testing.assert_allclose(np.log1p(f.Population),f.log1p_Population,atol=1e-14,rtol=0)


def test_weighted_matrix_is_the_original_registered_p2_matrix():
    current=np.load(AUTH/'preprocessing_and_labels.npz')
    frozen=np.load(PB/'inputs/VERIFIED_WEIGHTED_MATRICES.npz')
    np.testing.assert_array_equal(current['weighted_matrix'],frozen['P2__main5__cohort'])
    np.testing.assert_array_equal(current['feature_names'],FEATURES)


def test_all_21_profile_cells_are_ordinary_cohort_z_means():
    f=features();w=df(AUTH/'standardizer_and_weights.csv');profile=pd.read_csv(AUTH/'ordinary_cohort_z_class_means.csv',float_precision='round_trip')
    z=(f[FEATURES].to_numpy()-w.cohort_mean.to_numpy())/w.population_SD.to_numpy()
    for c in range(1,4):np.testing.assert_allclose(z[f.K3_class.eq(c)].mean(0),profile.iloc[c-1][FEATURES].to_numpy(dtype=float),atol=1e-12,rtol=0)
    assert profile.shape==(3,8)


def test_figure7_is_exact_approved_p2_artwork():
    for ext in ['pdf','png']:
        assert (SUITE/('Main/Fig07.'+ext)).read_bytes()==source('local_elsevier_review_outputs/FIG07_P2_K3_B_COLOR_NO_REVIEW_BANNER.'+ext)


def test_panel_a_has_six_descriptive_distributions_b_has_seven_fitted_coordinates():
    text=fitz.open(SUITE/'Main/Fig07.pdf')[0].get_text()
    assert 'Seven-coordinate' in text and 'Population exposure' in text
    assert 'Cumulative fraction' in text and 'cohort' in text
    assert 'NCV14 clustering coordinate' in text
    assert 'Six empirical feature distributions' in caps() and 'all seven P2 variables' in caps()
    assert not any(x in text for x in ['C4','C5','K4','PCA','Top-10','Hotspot score'])


def test_five_policy_mean_is_exact_and_not_a_new_schedule():
    f=features();p=df(PB/'inputs/FROZEN_POLICY_TRACT_MEANS_2315.csv').set_index('tract_id').loc[f.tract_id]
    fields=['B_'+name for name in ['impact-first','hospital-first','degree-first','betweenness-first','vulnerability-first']]
    np.testing.assert_allclose(f.MeanTotal5,p[fields].mean(axis=1),atol=1e-12,rtol=0)
    np.testing.assert_allclose(f.MeanTotal5,f.B_Unconstrained+f.MeanDelta,atol=1e-12,rtol=0)


def test_joint94_screen_keeps_original_threshold_and_no_composite_score():
    f=features();threshold=float(np.percentile(f.MeanTotal5,75))
    assert abs(threshold-38.38135467381475)<1e-12
    high=f.MeanTotal5.ge(threshold);joint=high&f.frozen_SOVI_quartile.eq('Q4')
    assert high.sum()==575 and joint.sum()==94 and f.loc[joint,'Population'].sum()==350799
    assert 'not a composite risk score' in caps() and 'statistically significant hotspot' in caps()
    assert not any('Hotspot_Score' in x for x in f.columns)


def test_palette_ids_and_white_na_match_approved_registry():
    p=read(SUITE/'CURRENT_CLUSTER_PALETTE.json')
    assert p['model_version']=='P2_K3_2299'
    assert p['colors']=={'1':'#147f98','2':'#d07734','3':'#7a5899'}
    assert p['NA_fill']=='#FFFFFF' and p['NA_count']==16 and p['NA_outline_width_pt']==.45


def test_s8_uses_p2_not_ncv14_diagnostics():
    t=fitz.open(SUITE/'Supplement/FigS08.pdf')[0].get_text()
    assert 'P2 seven-variable' in t and 'K3 primary' in t and 'K4 sensitivity' in t
    assert not any(x in t for x in ['NCV14','PCA','PC1','PC2'])
    assert (SUITE/'Supplement/FigS08.pdf').read_bytes()==source('local_elsevier_review_outputs/FigS08_P2_K3_K4_Saved_Diagnostics.pdf')


def test_authentic_full_k_curve_without_claiming_k3_maximizes_silhouette():
    d=df(AUTH/'saved_K_evidence.csv');saved=df(PB/'P2_REGISTERED_K_EVIDENCE.csv')
    pd.testing.assert_frame_equal(d,saved,check_exact=True)
    assert sorted(d.k.unique())==list(range(1,9)) and sorted(d.seed.unique())==list(range(42,47))
    means=d.groupby('k').mean_silhouette.mean();assert means.idxmax()==5
    assert abs(means.loc[3]-.248720)<1e-6 and abs(means.loc[4]-.253050)<1e-6


def test_k4_geographic_advantage_is_retained_as_sensitivity():
    d=df(AUTH/'geographic_stability.csv');k3=d.loc[d.k.eq(3),'held_out_ARI'];k4=d.loc[d.k.eq(4),'held_out_ARI']
    assert abs(k3.min()-.4189314331)<1e-9 and abs(k4.min()-.805674)<1e-6
    assert k4.min()>k3.min()
    assert 'K4 is mandatory sensitivity and has stronger held-out geographic agreement' in caps()
    m=df(AUTH/'K4_sensitivity_membership.csv');assert m.K4_sensitivity_class.value_counts().sort_index().tolist()==[37,1217,429,616]


def test_all_authority_artifacts_are_hash_verified():
    tracked=set(git('ls-files','-z','results/stage7/P2_K3_2299').decode().split('\0'))
    for path,h in read(AUTH/'ARTIFACT_HASHES.json').items():
        assert sha(AUTH/path)==h
        assert 'results/stage7/P2_K3_2299/'+path in tracked
    from la_grid.revision.current_stage7 import verify_current_stage7
    assert verify_current_stage7(ROOT)['status']=='PASS_SAVED_P2_REUSE'


def test_frozen_physical_scenario_and_five_policy_design():
    s=read(AUTH/'feature_schema_and_identity.json')
    assert [s[k] for k in ['hazard','resources','mapping','gate','horizon_hr','realizations']]==['2pc50','C57_D1','M1_UTILITY_003','G1_BASELINE_050',480,1000]
    assert len(s['policies'])==5 and 'random' not in s['policies']
    assert s['no_refitting_or_scientific_generation']


def test_current_entrypoint_routes_only_to_adopted_p2():
    import ast
    path=ROOT/'src/la_grid/plotting/build_current_suite_k3.py'
    tree=ast.parse(path.read_text(encoding='utf-8'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    assert 'build_current_suite_p2' in ast.unparse(main)
    code=(ROOT/'src/la_grid/plotting/build_current_suite_p2.py').read_text(encoding='utf-8')
    assert 'KMeans(' not in code and '.fit(' not in code


def test_every_generator_checkpoint_output_is_current():
    q=read(QA/'BUILD_CHECKPOINT.json')
    assert q['fitted_feature_count']==7 and q['model']=='P2' and q['primary_K']==3
    assert q['packet_pages']==21 and q['numbered_figures']==17
    assert sha(ROOT/'src/la_grid/plotting/build_current_suite_p2.py')==q['generator_sha256']
    assert all(sha(ROOT/p)==h for p,h in q['output_hashes'].items())


def test_current_gallery_index_and_manifest_are_synchronized():
    index=list(csv.DictReader((ROOT/'results/figures/FIGURE_INDEX.csv').open(encoding='utf-8')))
    assert len(index)==34
    for r in index:assert sha(ROOT/'results/figures'/r['file'])==r['sha256_or_lfs_oid']
    assert (ROOT/'results/figures/FIGURE_REVIEW_GALLERY.html').read_text(encoding='utf-8').count('<img ')==17


def test_current_readme_and_citation_identify_one_final_model():
    text=(ROOT/'README.md').read_text(encoding='utf-8')
    assert 'publication/p2-seven-variable' in text and '**seven-variable P2 / saved K3**' in text
    assert 'Marta C.' in text and 'MIT License' in (ROOT/'LICENSE').read_text()
    assert 'Post-Earthquake Power Service Recovery in Los Angeles' in (ROOT/'CITATION.cff').read_text(encoding='utf-8')


def test_stage8_read_only_validator_routes_to_adopted_authority():
    path=ROOT/'FINAL_REVISION_RUN_SEQUENCE/run_all.py'
    spec=importlib.util.spec_from_file_location('current_resume_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.EXPECTED_BRANCH=='publication/p2-seven-variable'
    assert module.validate_stage7()['authority']=='results/stage7/P2_K3_2299'


def test_all_retired_tip_commits_remain_reachable():
    text=(ROOT/'BRANCH_HISTORY_SUMMARY.md').read_text(encoding='utf-8')
    commits=set(re.findall(r'\| `([a-f0-9]{40})` \|',text))
    assert len(commits)>50
    for c in commits:assert subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',c,'HEAD'],capture_output=True).returncode==0


def test_current_figures_have_embedded_fonts_and_vector_typology():
    for stem in ['Main/Fig07','Supplement/FigS08']:
        with fitz.open(SUITE/(stem+'.pdf')) as d:
            assert not d[0].get_images()
            assert all(d.extract_font(f[0])[3] for f in d[0].get_fonts())
            spans=[s for b in d[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
            assert min(s['size'] for s in spans)>=7.49


def test_formal_and_original_stage7_entries_reuse_current_p2():
    import ast
    path=ROOT/'src/la_grid/core/C257H_Project_Main.py'
    tree=ast.parse(path.read_text(encoding='utf-8'))
    for name in ['run_stage_7','run_formal_stage_7']:
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert 'verify_current_stage7' in ast.unparse(node)


def test_old_composite_and_stage7_render_defaults_cannot_restore_obsolete_figures():
    import ast
    for name in ['make_manuscript_composites.py','render_revised_stage7.py']:
        tree=ast.parse((ROOT/'src/la_grid/plotting'/name).read_text(encoding='utf-8'))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        assert 'build_current_suite_p2' in ast.unparse(node)
