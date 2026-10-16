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
AUTH=ROOT/'results/stage7/2026-10-14'
QA=ROOT/'docs/reproducibility/p2_final_adoption_20261014'
MAP_QA=ROOT/'docs/reproducibility/figure7_map_readability_20261015'
PB=ROOT/'docs/data_research/stage7_path_b_p2_integration_review_20261014'
BASE='937fa2b1ab9953d8411a08fbbd0400cf3b52bd8f'
CURRENT_SUITE_BASE='0f67aa1f2758fcf1d35c112c36eb04e6d8a5dd68'
FEATURES=['Init_Supply','Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','log1p_Population']
BUDGET=np.array([1/9,1/9,1/9,1/6,1/6,1/6,1/6])
ACTIVE=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in range(1,10)]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as suite_utils


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def payload_bytes(p):
    raw=p.read_bytes()
    if raw.startswith(b'version https://git-lfs.github.com/spec/v1'):
        return suite_utils.payload(CURRENT_SUITE_BASE,p.relative_to(ROOT).as_posix())
    return raw
def read(p):return json.loads(payload_bytes(p))
def df(p):return pd.read_csv(io.BytesIO(payload_bytes(p)),dtype={'tract_id':str},float_precision='round_trip')
def features():return df(AUTH/'tract_features.csv')
def rows():return list(csv.DictReader((SUITE/'FIGURE_MANIFEST.csv').open(encoding='utf-8-sig')))
def caps():return (SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))


def source(path):
    return suite_utils.payload(BASE,path)


def test_exact_16_numbered_pairs():
    assert {r['final_name'] for r in rows()}=={s+'.'+e for s in ACTIVE for e in ['pdf','png']}
    assert len(rows())==32


def test_manifest_matches_actual_artwork():
    for r in rows():assert sha(ROOT/r['current_source_file'])==r['sha256']


def test_every_mirror_is_byte_identical():
    for r in rows():assert sha(ROOT/r['mirror_file'])==r['sha256']


def test_unchanged_and_updated_artwork_are_explicitly_recorded():
    changes=df(MAP_QA/'FIGURE_CHANGE_MANIFEST.csv')
    assert len(changes)==32
    for r in changes.itertuples():
        if r.unchanged:assert sha(SUITE/r.figure)==r.baseline_sha256==r.current_sha256
    assert set(changes.loc[changes.unchanged,'figure'])=={s+'.'+e for s in ACTIVE if s!='Main/Fig07' for e in ['pdf','png']}
    assert set(changes.loc[~changes.unchanged,'figure'])=={'Main/Fig07.pdf','Main/Fig07.png'}


def test_independent_main_results_and_merged_resource_artwork_preserved():
    changes=df(MAP_QA/'FIGURE_CHANGE_MANIFEST.csv').set_index('figure')
    for s in ['Main/Fig01','Main/Fig04','Main/Fig05','Main/Fig06','Supplement/FigS09']:
        for e in ['pdf','png']:assert bool(changes.loc[s+'.'+e,'unchanged'])


def test_no_extra_numbered_artwork_or_retired_numbering():
    for folder in ['Main','Supplement']:
        actual={str(p.relative_to(SUITE)).replace('\\','/') for p in (SUITE/folder).iterdir() if p.suffix in ['.pdf','.png']}
        assert actual=={r['final_name'] for r in rows() if r['final_name'].startswith(folder+'/')}
    assert not any((SUITE/'Supplement'/f'FigS{n:02d}.pdf').exists() for n in [10,11,12,13])


def test_publication_pngs_and_native_dimensions():
    for stem in ACTIVE:
        with fitz.open(SUITE/(stem+'.pdf')) as art,Image.open(SUITE/(stem+'.png')) as im:
            assert im.width>=4320
            assert abs(im.width/im.height-art[0].rect.width/art[0].rect.height)<.002
            assert abs(art[0].rect.width-(7.2*72 if stem=='Main/Fig07' else 185*72/25.4))<.2


def test_all_native_previews_exist():
    assert all((SUITE/'Page_Previews'/(Path(stem).name+'.png')).is_file() for stem in ACTIVE)


def test_packet_page_counts():
    assert len(fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))==20
    assert len(fitz.open(SUITE/'ALL_MAIN_FIGURES.pdf'))==7
    assert len(fitz.open(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf'))==9


def test_packet_embeds_each_actual_artwork_at_native_size():
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as book:
        for i,stem in enumerate(ACTIVE):
            with fitz.open(SUITE/(stem+'.pdf')) as art:
                rect=art[0].rect
                assert book[i].rect.width==rect.width and book[i].rect.height>rect.height
                assert book[i].get_pixmap(clip=rect).samples==art[0].get_pixmap().samples


def test_all_caption_forms_are_short_and_legible():
    registry=list(csv.DictReader((MAP_QA/'COMPACT_PACKET_PAGE_REGISTRY.csv').open(encoding='utf-8')))
    assert len(registry)==16
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
    assert [int(n) for n in re.findall(r'^## Supplementary Figure S(\d+)\.',text,re.M)]==list(range(1,10))
    assert not re.search(r'\bS(?:10|11|12|13)\b',text)
    assert 'Supplementary Figures S12/S13' not in text
    assert 'Supplementary Figure S9' in text


def test_sole_current_selector_is_p2_seven_variables():
    p=read(ROOT/'config/current_stage7.json');s=read(AUTH/'feature_schema_and_identity.json')
    assert p['version']=='2026-10-14' and p['fitted_feature_count']==7
    assert s['feature_names']==FEATURES and s['primary_K']==3 and s['sensitivity_K']==4
    assert 'FEMA_NCV14_CA_v119' not in s['feature_names']


def test_every_primary_feature_is_finite_and_exactly_saved():
    f=features();frozen=df(PB/'FROZEN_P2_TRACT_TABLE_2315.csv').query('Population>0')
    assert len(f)==2299 and np.isfinite(f[FEATURES]).all().all()
    np.testing.assert_array_equal(f[FEATURES],frozen[FEATURES])
    np.testing.assert_array_equal(f.tract_id,frozen.tract_id)


def test_every_saved_k3_membership_and_class_identity():
    f=features();saved=np.load(io.BytesIO(payload_bytes(PB/'inputs/REGISTERED_FIT_ARRAYS.npz')))
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
    current=np.load(io.BytesIO(payload_bytes(AUTH/'preprocessing_and_labels.npz')))
    frozen=np.load(io.BytesIO(payload_bytes(PB/'inputs/VERIFIED_WEIGHTED_MATRICES.npz')))
    np.testing.assert_array_equal(current['weighted_matrix'],frozen['P2__main5__cohort'])
    np.testing.assert_array_equal(current['feature_names'],FEATURES)


def test_all_21_profile_cells_are_ordinary_cohort_z_means():
    f=features();w=df(AUTH/'standardizer_and_weights.csv');profile=df(AUTH/'ordinary_cohort_z_class_means.csv')
    z=(f[FEATURES].to_numpy()-w.cohort_mean.to_numpy())/w.population_SD.to_numpy()
    for c in range(1,4):np.testing.assert_allclose(z[f.K3_class.eq(c)].mean(0),profile.iloc[c-1][FEATURES].to_numpy(dtype=float),atol=1e-12,rtol=0)
    assert profile.shape==(3,8)


def test_figure7_preserves_top_panels_and_uses_vector_only_maps():
    baseline=fitz.open(ROOT/'results/diagnostics/1021/figure7_readability_20261015/FIG07_BASELINE.pdf')
    current=fitz.open(SUITE/'Main/Fig07.pdf')
    assert current[0].rect.width==baseline[0].rect.width
    clip=fitz.Rect(0,0,baseline[0].rect.width,410)
    assert current[0].get_pixmap(clip=clip,dpi=72,alpha=False).samples==baseline[0].get_pixmap(clip=clip,dpi=72,alpha=False).samples
    assert not current[0].get_images()
    assert abs(current[0].rect.height/72-10)<1e-8
    q=read(MAP_QA/'PRESENTATION_QA.json')['figures']['Main/Fig07']
    assert q['positive_GEOIDs']==2299 and q['NA_polygon_count']==16
    assert q['high_high_outline_count']==94 and q['high_high_population']==350799
    assert q['contrasting_internal_tract_boundaries'] is False
    assert q['same_fill_edge_overprint_pt']==.12 and q['chosen_outline_width_pt']==.25


def test_panel_a_has_six_descriptive_distributions_b_has_seven_fitted_coordinates():
    text=fitz.open(SUITE/'Main/Fig07.pdf')[0].get_text().replace('\u00a0',' ')
    assert 'B. Profiles' in text and 'Population exposure' in text
    assert 'Cumulative fraction' in text and 'Class mean z-score' in text
    assert 'Six empirical feature distributions' in caps() and 'all seven fitted variables' in caps()
    assert not any(s.lower() in text.lower() for s in ['saved','frozen','P2/','Seven-coordinate','Exact empirical CDFs;','Ordinary feature z means,','no NCV14'])
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
    assert 'not a composite score' in caps() and 'inferential hotspot test' in caps()
    assert not any('Hotspot_Score' in x for x in f.columns)


def test_palette_ids_and_white_na_match_approved_registry():
    p=read(SUITE/'CURRENT_CLUSTER_PALETTE.json')
    assert p['model_version']=='2026-10-14' and p['map_version']=='2026-10-15'
    assert p['colors']=={'1':'#147f98','2':'#d07734','3':'#7a5899'}
    assert p['NA_fill']=='#FFFFFF' and p['NA_count']==16 and p['NA_outline_width_pt']==.45
    assert p['map_regular_tract_outlines'] is False and p['screening_outline_width_pt']==.25


def test_s8_now_shows_repair_priorities_not_removed_clustering_diagnostics():
    t=fitz.open(SUITE/'Supplement/FigS08.pdf')[0].get_text().replace('\u00a0',' ').replace('\u00ad','-')
    assert 'Hospital-first repair priority' in t and 'Impact-first repair priority' in t
    assert 'Clustering diagnostics' not in t and 'K4 sensitivity' not in t
    assert not any(x in t for x in ['NCV14','PCA','PC1','PC2'])
    assert not re.search(r'\b(?:P2|saved|frozen)\b',t,re.I)


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
    assert 'K4 remains a saved sensitivity result' in (SUITE/'README.md').read_text()
    m=df(AUTH/'K4_sensitivity_membership.csv');assert m.K4_sensitivity_class.value_counts().sort_index().tolist()==[37,1217,429,616]


def test_all_authority_artifacts_are_hash_verified():
    tracked=set(git('ls-files','-z','results/stage7/2026-10-14').decode().split('\0'))
    for path,h in read(AUTH/'ARTIFACT_HASHES.json').items():
        assert hashlib.sha256(payload_bytes(AUTH/path)).hexdigest()==h
        assert 'results/stage7/2026-10-14/'+path in tracked
    from la_grid.revision.current_stage7 import verify_current_stage7
    assert verify_current_stage7(ROOT)['status']=='PASS_SAVED_P2_REUSE'


def test_frozen_physical_scenario_and_five_policy_design():
    s=read(AUTH/'feature_schema_and_identity.json')
    assert [s[k] for k in ['hazard','resources','mapping','gate','horizon_hr','realizations']]==['2pc50','C57_D1','M1_UTILITY_003','G1_BASELINE_050',480,1000]
    assert len(s['policies'])==5 and 'random' not in s['policies']
    assert s['no_refitting_or_scientific_generation']


def test_current_entrypoint_routes_only_to_adopted_p2():
    import ast
    path=ROOT/'src/la_grid/plotting/build_current_figures.py'
    tree=ast.parse(path.read_text(encoding='utf-8'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    assert 'build_current_suite_p2' in ast.unparse(main)
    code=(ROOT/'src/la_grid/plotting/build_current_suite_p2.py').read_text(encoding='utf-8')
    assert 'KMeans(' not in code and '.fit(' not in code


def test_every_generator_checkpoint_output_is_current():
    q=read(MAP_QA/'BUILD_CHECKPOINT.json')
    assert q['fitted_feature_count']==7 and q['model']=='P2' and q['primary_K']==3
    assert q['packet_pages']==20 and q['numbered_figures']==16
    assert sha(ROOT/'src/la_grid/plotting/build_current_suite_p2.py')==q['generator_sha256']
    assert sha(ROOT/'src/la_grid/plotting/figure_presentation.py')==q['presentation_sha256']
    assert all(sha(ROOT/p)==h for p,h in q['output_hashes'].items())


def test_current_gallery_index_and_manifest_are_synchronized():
    index=list(csv.DictReader((ROOT/'results/figures/FIGURE_INDEX.csv').open(encoding='utf-8')))
    assert len(index)==32
    for r in index:assert sha(ROOT/'results/figures'/r['file'])==r['sha256_or_lfs_oid']
    assert (ROOT/'results/figures/FIGURE_REVIEW_GALLERY.html').read_text(encoding='utf-8').count('<img ')==16


def test_current_readme_and_citation_identify_one_final_model():
    text=(ROOT/'README.md').read_text(encoding='utf-8')
    assert '2026-10-14' in text and '## Version 2026-10-14' in text
    assert 'Marta C.' in text and 'MIT License' in (ROOT/'LICENSE').read_text()
    assert 'Post-Earthquake Power Service Recovery in Los Angeles' in (ROOT/'CITATION.cff').read_text(encoding='utf-8')


def test_stage8_read_only_validator_routes_to_adopted_authority():
    path=ROOT/'FINAL_REVISION_RUN_SEQUENCE/run_all.py'
    spec=importlib.util.spec_from_file_location('current_resume_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.EXPECTED_BRANCH=='2026-10-14'
    assert module.validate_stage7()['authority']=='results/stage7/2026-10-14'


def test_all_retired_tip_commits_remain_reachable():
    text=(ROOT/'BRANCH_HISTORY_SUMMARY.md').read_text(encoding='utf-8')
    commits=set(re.findall(r'\| `([a-f0-9]{40})` \|',text))
    assert len(commits)>50
    for c in commits:assert subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',c,'HEAD'],capture_output=True).returncode==0


def test_current_figures_have_embedded_fonts_and_vector_typology():
    for stem in ['Main/Fig07','Supplement/FigS05']:
        with fitz.open(SUITE/(stem+'.pdf')) as d:
            assert not d[0].get_images()
            assert all(d.extract_font(f[0])[3] for f in d[0].get_fonts())
            spans=[s for b in d[0].get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans']]
            assert min(s['size'] for s in spans)>=(6.99 if stem.endswith('S05') else 7.49)


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


def test_version_names_are_dates_not_feature_specification_names():
    p=read(ROOT/'config/current_stage7.json')
    assert p['version']=='2026-10-14' and p['authority']=='results/stage7/2026-10-14'
    assert 'git clone --branch 2026-10-14 ' in (ROOT/'README.md').read_text(encoding='utf-8')
    assert not (ROOT/'src/la_grid/plotting/build_current_suite_k3.py').exists()
    assert (ROOT/'src/la_grid/plotting/build_current_figures.py').is_file()


def test_current_tree_excludes_retired_drafts_and_run_level_archives():
    tracked=set(git('ls-files','-z').decode().split('\0'))
    assert not any(p.endswith(('.doc','.docx')) for p in tracked)
    assert not any(p.startswith(('provenance/artwork_drafts/', 'local_elsevier_review_outputs/',
                                'docs/data_research/built_environment_20261009/')) for p in tracked)
    old=[p for p in tracked if p.startswith('provenance/figure_review_history/')]
    assert old==['provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv']
    for folder in ['ga_optimization_20261009','extended_ga_20261008','ga_search_budget_20261007']:
        assert not any(p.startswith('results/diagnostics/'+folder+'/') and len(p.split('/'))>4 for p in tracked)


def test_caption_replay_no_longer_depends_on_editable_word_drafts():
    spec=importlib.util.spec_from_file_location('dated_figure_builder',ROOT/'src/la_grid/plotting/build_current_suite_p2.py')
    sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    current=dict(re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)',caps(),re.M|re.S))
    assert module.captions()==[(title,body.strip()) for title,body in current.items()]


def test_figure5_scientific_panels_are_render_identical_after_translation():
    expected=suite_utils.payload(CURRENT_SUITE_BASE,'results/figure_review/Main/Fig05.pdf')
    assert sha(SUITE/'Main/Fig05.pdf')==hashlib.sha256(expected).hexdigest()


def test_figure5_has_consistent_row_title_gaps():
    with fitz.open(SUITE/'Main/Fig05.pdf') as d:
        ss=[s for b in d[0].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
    tt={s['text'][0]:s for s in ss if re.match(r'^[A-E]\. ',s['text'].replace('\u00a0',' '))}
    assert len(tt)==5 and all(abs(s['size']-9.5)<.01 for s in tt.values())
    ab=max(s['bbox'][3] for s in ss if 80<s['bbox'][1]<250)
    cd=max(s['bbox'][3] for s in ss if 281<s['bbox'][1]<451)
    gaps=[tt['C']['bbox'][1]-ab,tt['E']['bbox'][1]-cd]
    assert all(23.5<g<24.5 for g in gaps) and abs(gaps[0]-gaps[1])<.3
    assert abs(tt['A']['bbox'][1]-64)<.05


def test_figure7_has_consistent_title_spacing_without_embedded_explanations():
    with fitz.open(SUITE/'Main/Fig07.pdf') as d:
        ss=[s for b in d[0].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
    for s in ss:s['text']=s['text'].replace('\u00a0',' ')
    tt={s['text'][0]:s for s in ss if re.match(r'^[A-D]\. ',s['text'])}
    assert [tt[c]['text'] for c in 'ABCD']==['A. Feature distributions','B. Profiles','C. Community types',
                                                            'D. Recovery burden and social vulnerability']
    assert all(abs(s['size']-9.5)<.01 for s in tt.values())
    a=max(s['bbox'][3] for s in ss if 50<s['bbox'][1]<265)
    b=max(s['bbox'][3] for s in ss if 290<s['bbox'][1]<405)
    gaps=[tt['B']['bbox'][1]-a,tt['C']['bbox'][1]-b]
    assert all(19.5<g<20.5 for g in gaps) and abs(gaps[0]-gaps[1])<.3
    text='\n'.join(s['text'] for s in ss)
    assert not any(s in text for s in ['Exact empirical CDFs;','Ordinary feature z means,',
                                      'Finite five-policy comparison.','Descriptive co-occurrence;','model IDs;'])
    assert 'C1' in text and '(n=1,235)' in text and 'N/A' in text


def test_no_internal_process_names_in_current_publication_artwork_or_captions():
    forbidden=re.compile(r'\b(?:frozen|saved|P2)\b|Seven-coordinate',re.I)
    for stem in ACTIVE:
        with fitz.open(SUITE/(stem+'.pdf')) as d:assert not forbidden.search(d[0].get_text()),stem
    assert not forbidden.search(caps())


def test_travel_title_is_task_to_task_without_extra_qualifier():
    text=fitz.open(SUITE/'Supplement/FigS02.pdf')[0].get_text().replace('\u00a0',' ').replace('\u00ad','-')
    assert 'B. Task-to-task travel' in text and 'Directed task-to-task' not in text


def test_static_percolation_is_distinct_from_time_dependent_recovery():
    text=fitz.open(SUITE/'Supplement/FigS03.pdf')[0].get_text().replace('\u00a0',' ').replace('\u00ad','-')
    for t in ['A. Static percolation','B. Recovery of largest-component fraction',
              'C. Recovery of mean degree in the largest component','Time after earthquake (h)']:
        assert t in text
    expected=suite_utils.payload(CURRENT_SUITE_BASE,'results/figure_review/Supplement/FigS03.pdf')
    assert sha(SUITE/'Supplement/FigS03.pdf')==hashlib.sha256(expected).hexdigest()
    with fitz.open(SUITE/'Supplement/FigS03.pdf') as d:
        axes=[v['rect'] for v in d[0].get_drawings() if abs(v['rect'].x0-57.685)<.02
              and abs(v['rect'].width-188.787)<.02 and abs(v['rect'].height-102.047)<.02]
    assert any(abs(r.y0-239.7716)<.02 for r in axes)
    assert any(abs(r.y0-434.7697)<.02 for r in axes)
    assert abs((434.7697-387)-(239.7716-192))<.01


def test_ga_initial_and_final_orders_are_both_per_run():
    text=fitz.open(SUITE/'Supplement/FigS04.pdf')[0].get_text().replace('\u00a0',' ')
    assert all(t in text for t in ['Best initial order','100 orders per run','Best final order','At run completion'])
    assert 'Initial best' not in text and 'Final minimum' not in text
    assert 'Each run\'s best initial order' in caps()


def test_service_gate_panel_has_three_clear_titles_and_no_explanatory_footer():
    with fitz.open(SUITE/'Supplement/FigS05.pdf') as d:
        ss=[s for b in d[0].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
    titles=[s for s in ss if re.match(r'^[A-D]\. ',s['text'].replace('\u00a0',' '))]
    assert len(titles)==3 and all(abs(s['size']-9.5)<.01 for s in titles)
    assert all(abs((s['bbox'][0]+s['bbox'][2])/2-185*72/25.4/2)<.1 for s in titles)
    text='\n'.join(s['text'] for s in ss)
    assert 'Threshold 0.05' in text and 'Threshold 0.75' in text
    assert 'C and D retain' not in text and 'Mean and 5th' not in text
    assert '(C) Functionality thresholds 0.05 and 0.75' in caps()


def test_all_nine_service_gate_display_values_match_saved_source():
    original=df(ROOT/'docs/reproducibility/figure_suite_author_clarity_numbering_20261013/SOURCE_AND_THRESHOLD_DISPLAY_VALUES.csv')
    assert len(original)==9 and set(original.policy)=={'impact-first','hospital-first','degree-first'}
    assert set(original.threshold)=={.05,.5,.75} and original.n.eq(1000).all()
    assert original.loc[original.threshold.eq(.5),'source_gate'].eq('disabled').all()
    assert original.loc[original.threshold.ne(.5),'source_gate'].eq('retained').all()
    expected=suite_utils.payload(CURRENT_SUITE_BASE,'results/figure_review/Supplement/FigS05.pdf')
    assert sha(SUITE/'Supplement/FigS05.pdf')==hashlib.sha256(expected).hexdigest()


def test_priority_population_scale_is_neutral_without_geometry_change():
    expected=suite_utils.payload(CURRENT_SUITE_BASE,'results/figure_review/Supplement/FigS08.pdf')
    assert sha(SUITE/'Supplement/FigS08.pdf')==hashlib.sha256(expected).hexdigest()
    with fitz.open(SUITE/'Supplement/FigS08.pdf') as d:
        fills=[v['fill'] for v in d[0].get_drawings() if v['fill'] and v['rect'].y0>525]
    # Only station markers retain their muted blue-gray identity.
    assert not any(c[2]-c[0]>.15 and c[2]>c[1] for c in fills)


def test_saved_scientific_authority_matches_this_rounds_initial_snapshot():
    q=read(ROOT/'results/diagnostics/1021/figure7_readability_20261015/PRESERVATION_BEFORE.json')
    files=q['stage7_2026_10_14_blob_ids']
    assert len(files)==17
    for path,blob_id in files.items():
        assert git('rev-parse',q['source_commit']+':'+path).decode().strip()==blob_id
        worktree=ROOT.joinpath(*path.split('/')).read_bytes()
        expected=suite_utils.payload(q['source_commit'],path)
        assert hashlib.sha256(worktree).digest()==hashlib.sha256(expected).digest()


def test_threshold_errorbar_coordinates_independently_match_saved_values():
    values=df(ROOT/'docs/reproducibility/figure_suite_author_clarity_numbering_20261013/SOURCE_AND_THRESHOLD_DISPLAY_VALUES.csv')
    with fitz.open(SUITE/'Supplement/FigS05.pdf') as d:
        width=d[0].rect.width;drawings=d[0].get_drawings()
    for row in values.itertuples():
        i=['impact-first','hospital-first','degree-first'].index(row.policy)
        lo,hi,top,offset=(-7.3,.3,232,0) if row.threshold==.5 else (-.17,.06,450,.14 if row.threshold==.05 else -.14)
        xp=lambda v:.23*width+(v-lo)/(hi-lo)*.70*width
        y=top+(i+.5-offset)*36
        wanted=sorted([xp(row.p05_gap_h),xp(row.p95_gap_h)])
        found=False
        for drawing in drawings:
            for item in drawing['items']:
                if item[0]=='l':
                    a,b=item[1:]
                    if abs(a.y-y)<.02 and abs(b.y-y)<.02 and max(abs(a-b) for a,b in zip(sorted([a.x,b.x]),wanted))<.02:
                        found=True
        assert found,(row.case,row.policy,wanted,y)


def test_centered_panel_titles_use_one_font_size_within_each_figure():
    for stem in ACTIVE:
        with fitz.open(SUITE/(stem+'.pdf')) as d:
            ss=[s for b in d[0].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
            titles=[s for s in ss if re.match(r'^[A-H]\. ',s['text'].replace('\u00a0',' '))]
            if titles:assert max(s['size'] for s in titles)-min(s['size'] for s in titles)<.02,stem
            for s in titles:assert d[0].rect.contains(fitz.Rect(s['bbox'])),(stem,s['text'])


def test_damage_state_y_label_is_not_clipped_by_title_alignment():
    sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
    import consolidate_current_figure_suite as u
    raw=u.payload('96297fb12fceb8e61137b456648d2655a5909b6b','results/figure_review/Main/Fig03.pdf')
    with fitz.open(stream=raw,filetype='pdf') as a,fitz.open(SUITE/'Main/Fig03.pdf') as b:
        rect=fitz.Rect(40,25,56,195)
        assert a[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=rect).samples==b[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=rect).samples
