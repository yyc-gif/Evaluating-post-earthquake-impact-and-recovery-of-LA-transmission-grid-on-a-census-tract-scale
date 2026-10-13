"""Integrity and scientific-invariance checks for the current numbered suite."""
from pathlib import Path
import csv, hashlib, json, re, io, subprocess, os
import fitz
from PIL import Image
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review'
QA=ROOT/'docs/reproducibility/author_suite_final_layout_20261012'
CURRENT=ROOT/'docs/reproducibility/figure_suite_ncv14_h2_k3_d3_20261013'
EXPECTED=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in [1,*range(3,12)]]


def lp(p):
    s=str(p.resolve());return s if s.startswith('\\\\?\\') else '\\\\?\\'+s


def sha(p):return hashlib.sha256(open(lp(p),'rb').read()).hexdigest()
def read(p):return json.load(open(lp(p),encoding='utf-8'))
def audit():return read(QA/'INTEGRATION_QA.json')


def test_all_active_artifacts_and_mirrors_match_the_manifest():
    rows=list(csv.DictReader(open(lp(SUITE/'FIGURE_MANIFEST.csv'),encoding='utf-8-sig')))
    assert len(rows)==34
    assert {r['final_name'] for r in rows}=={s+'.'+e for s in EXPECTED for e in ['pdf','png']}
    for r in rows:
        assert sha(ROOT/r['current_source_file'])==r['sha256']
        assert sha(ROOT/r['mirror_file'])==r['sha256']
        if r['change_in_this_update']=='UPDATED':assert sha(ROOT/r['presentation_generator'])==r['presentation_generator_sha256']


def test_native_packets_and_readable_captions_are_complete():
    full=fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'));assert len(full)==38
    caps=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    headings=re.findall(r'^## (.+)',caps,re.M);assert len(headings)==17
    for i,(stem,title) in enumerate(zip(EXPECTED,headings)):
        source=fitz.open(lp(SUITE/(stem+'.pdf')))
        assert tuple(source[0].rect)==tuple(full[2*i].rect)
        assert abs(source[0].rect.width-185*72/25.4)<.15
        assert full[2*i].get_text()==source[0].get_text()
        page=full[2*i+1]
        assert ' '.join(title.split()) in ' '.join(page.get_text().split())
        spans=[s for b in page.get_text('dict',flags=0)['blocks'] for line in b.get('lines',[]) for s in line['spans']]
        assert min(s['size'] for s in spans)>=9.99
        assert all(page.rect.contains(fitz.Rect(s['bbox'])) for s in spans)
    assert len(fitz.open(lp(SUITE/'ALL_MAIN_FIGURES.pdf')))==7
    assert len(fitz.open(lp(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf')))==10


def test_publication_resolution_and_native_previews():
    for stem in EXPECTED:
        d=fitz.open(lp(SUITE/(stem+'.pdf')))
        with Image.open(lp(SUITE/(stem+'.png'))) as im:
            assert im.width>=4360
            assert abs(im.width/im.height-d[0].rect.width/d[0].rect.height)<.002
        assert (SUITE/'Page_Previews'/(Path(stem).name+'.png')).is_file()


def test_framework_edit_stays_in_community_outcomes():
    q=read(CURRENT/'FIG01_LABEL_PIXEL_QA.json');assert q['outside_label_pixels_identical']
    d=fitz.open(lp(SUITE/'Main/Fig01.pdf'))
    t=d[0].get_textbox(fitz.Rect(94.5*72/25.4,164.2*72/25.4,182*72/25.4,217*72/25.4))
    t=t.replace('\u00ad','-').replace('\u00a0',' ')
    assert all(x in t for x in ['Service loss','T80','Quartile gap','Gini','Community typology','Spatial service-deficit','patterns'])
    assert 'Hotspot score' not in t
    assert all(x not in t for x in ['Tested conditions','Vulnerability-first effects','All tracts and','time to 80%'])


def test_fig5_strict_clipping_preserves_every_map_identity():
    e=audit()['operator_edits']['Main/Fig05']
    assert e['strict_color_limits_h']==[-20,20] and e['colorbar_ticks_h']==[-20,-10,0,10,20]
    assert e['normalization_clip'] and e['old_paint_checked_against_every_exact_saved_tract_value']
    assert e['polygon_path_count']==6945 and e['three_map_values_and_GEOIDs_unchanged']
    assert sum(r['below_minus20']+r['above_plus20'] for r in e['endpoint_saturation_counts'].values())>0
    assert read(QA/'VISUAL_AND_PACKET_QA.json')['Fig5_A_to_D_pixels_identical']


def test_threshold_comparisons_hold_source_connectivity_fixed():
    e=audit()['operator_edits']['Supplement/FigS06']
    assert e['displayed_gate_cases']==['G2_RELAXED_005','G3_STRICT_075']
    assert e['source_connectivity_fixed'] and not e['source_only_control_available']
    assert e['joint_removal_panel_removed_from_numbered_figure']
    rows=list(csv.DictReader(open(lp(QA/'THRESHOLD_DISPLAY_VALUES.csv'),encoding='utf-8')))
    assert len(rows)==6 and {r['gate'] for r in rows}==set(e['displayed_gate_cases'])
    assert 'Only the functionality threshold changes' in open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()


def test_s9_uses_authentic_eight_variable_k_curves_and_k3_only():
    t=fitz.open(lp(SUITE/'Supplement/FigS09.pdf'))[0].get_text()
    assert 'inertia' in t.lower() and 'silhouette coefficient' in t.lower()
    assert not any(x in t for x in ['PCA','PC1','PC2','Principal component'])
    q=read(CURRENT/'FIGS09_K3_DIAGNOSTIC_QA.json')
    assert not q['kmeans_fit_or_k_search_run'] and not q['K4_classification_displayed']
    assert q['classification_k']==3 and q['stability_k']==[3]
    rows=list(csv.DictReader(open(lp(CURRENT/'inputs/K_DIAGNOSTICS.csv'),encoding='utf-8')))
    assert [int(r['k']) for r in rows]==list(range(1,9))
    assert abs(float(rows[0]['mean_WCSS'])-2299)<1e-9
    assert abs(float(rows[2]['mean_silhouette'])-.2337372038511557)<1e-6
    assert not q['K3_is_silhouette_maximum']
    assert all(x in t for x in ['K3','partition stability','class silhouette'])
    c='0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
    authoritative=pd.read_csv(io.BytesIO(source_payload(c,'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/inputs/EXISTING_K_EVIDENCE.csv')),float_precision='round_trip').drop(columns='review_status')
    current=pd.read_csv(lp(CURRENT/'inputs/K_DIAGNOSTICS.csv'),float_precision='round_trip')
    pd.testing.assert_frame_equal(current,authoritative,check_exact=True)


def test_s10_population_and_priority_identity_are_preserved():
    e=audit()['operator_edits']['Supplement/FigS10']
    assert e['C_metric']=='tract population' and e['C_palette'].startswith('YlOrBr')
    assert e['priority_color_all_panels']=='#20272e'
    assert e['population_norm_range_geometry_and_rank_identity_unchanged'] and len(e['colorbar_scalar_indices'])==1
    d=fitz.open(lp(SUITE/'Supplement/FigS10.pdf'))
    ranks=[s for b in d[0].get_text('dict',flags=0)['blocks'] for line in b.get('lines',[]) for s in line['spans'] if s['text'] in ['1','2','3','4','5']]
    assert ranks and all(s['color']!=0x007c83 for s in ranks)


def test_resource_merge_reuses_eight_original_vector_panels():
    e=audit()['operator_edits']['Supplement/FigS11']
    assert e['eight_original_resource_panels_reused'] and e['no_means_ranges_or_trajectories_recomputed']
    assert len(e['layout_records'])==8
    assert {r['source'] for r in e['layout_records']}=={'Supplement/FigS12','Supplement/FigS13'}
    d=fitz.open(lp(SUITE/'Supplement/FigS11.pdf'));assert len(d[0].get_images())==0
    spans=[s for b in d[0].get_text('dict',flags=0)['blocks'] for line in b.get('lines',[]) for s in line['spans']]
    assert min(s['size'] for s in spans)>=7.99
    assert all(d[0].rect.contains(fitz.Rect(s['bbox'])) for s in spans)
    assert all(chr(65+i)+'.' in d[0].get_text() for i in range(8))


def test_retired_figures_and_s02_have_no_current_placeholders():
    for n in ['FigS02','FigS12','FigS13']:
        assert not (SUITE/'Supplement'/(n+'.pdf')).exists()
        assert not (SUITE/'Page_Previews'/(n+'.png')).exists()
    caps=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    assert not re.search(r'^## Supplementary Figure S(?:2|12|13)\.',caps,re.M)
    index=list(csv.DictReader(open(lp(ROOT/'results/figures/FIGURE_INDEX.csv'),encoding='utf-8-sig')))
    assert len(index)==34 and not {r['figure_number'] for r in index}&{'FigS02','FigS12','FigS13'}


def test_previous_heatmap_is_the_exact_fig4_reference_subtraction():
    rows=list(csv.DictReader(open(lp(QA/'S11_FIG4_NUMERICAL_IDENTITY.csv'),encoding='utf-8')))
    assert len(rows)==24 and max(abs(float(r['identity_error_h'])) for r in rows)<1e-10
    assert not audit()['S11_Fig4_identity']['new_scientific_estimates']


def test_unrelated_artwork_and_original_staged_science_are_unchanged():
    rows=list(csv.DictReader(open(lp(CURRENT/'FIGURE_CHANGE_MANIFEST.csv'),encoding='utf-8')))
    assert len([r for r in rows if r['status']=='CHANGED'])==6
    assert len([r for r in rows if r['status']=='BYTE_IDENTICAL'])==28
    for r in rows:
        if r['status']=='BYTE_IDENTICAL':
            assert sha(SUITE/(r['figure']+'.'+r['format']))==r['baseline_sha256']==r['current_sha256']
    before=read(CURRENT/'PRESERVATION_BEFORE.json');after=read(CURRENT/'PRESERVATION_AFTER.json')
    assert before==after and before['protected_count']==950 and before['staged_count']==862
    q=read(CURRENT/'COMPLETE_PACKET_AND_MIRROR_QA.json')
    assert not q['scientific_fits_or_evaluations_run']
    assert all(r['actual_packet_pixels_identical'] for r in q['packet_checks'])


def source_payload(commit, rel):
    env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0'
    def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],env=env)
    blob=git('show',commit+':'+rel)
    m=re.search(rb'oid sha256:([a-f0-9]{64})\nsize (\d+)',blob)
    if not m:return blob
    h=m[1].decode();common=Path(git('rev-parse','--path-format=absolute','--git-common-dir').decode().strip())
    b=open(lp(common/'lfs/objects'/h[:2]/h[2:4]/h),'rb').read()
    assert hashlib.sha256(b).hexdigest()==h and len(b)==int(m[2])
    return b


def test_frozen_feature_labels_budgets_and_hazard_vector_match_exactly():
    c='0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
    prefix='docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/candidate/'
    authoritative=np.load(io.BytesIO(source_payload(c,prefix+'FROZEN_PREPROCESSING_AND_LABELS.npz')))
    z=np.load(lp(CURRENT/'inputs/K3_FROZEN_ARRAYS.npz'))
    for field in ['tract_ids','raw','weighted_matrix','budgets','K3_labels']:
        np.testing.assert_allclose(z[field],authoritative[field],atol=1e-12,rtol=0) if z[field].dtype.kind=='f' else np.testing.assert_array_equal(z[field],authoritative[field])
    np.testing.assert_array_equal(z['raw'],authoritative['raw'])
    np.testing.assert_array_equal(z['feature_names'],authoritative['feature_names'])
    np.testing.assert_allclose(z['budgets'],[1/9,1/9,1/9,1/6,1/6,1/6,1/12,1/12],atol=1e-16,rtol=0)
    assert all('__k3__' in k for k in z['keys'])
    assert 'K4_labels' not in z.files


def test_cohort_and_every_saved_k3_membership_population_and_quartile():
    f=pd.read_csv(lp(CURRENT/'inputs/EIGHT_VARIABLE_FROZEN_TABLE.csv'),dtype={'tract_id':str},float_precision='round_trip')
    m=pd.read_csv(lp(CURRENT/'inputs/K3_CLUSTER_MEMBERSHIP.csv'),dtype={'tract_id':str})
    all_tracts=pd.read_csv(lp(CURRENT/'inputs/FULL_2315_COHORT_STATUS.csv'),dtype={'tract_id':str})
    assert len(f)==len(m)==2299 and len(all_tracts)==2315
    assert f.tract_id.str.fullmatch(r'\d{11}').all() and f.tract_id.is_unique
    assert f.tract_id.equals(m.tract_id) and (f.K3_class==m.K3_class).all()
    assert (all_tracts.Frozen_Formal_Population==0).sum()==16
    assert all_tracts.K3_class.isna().sum()==16
    assert (f.Population>0).all() and f.Population.sum()==9066522
    assert f.groupby('K3_class').size().tolist()==[1242,475,582]
    assert f.groupby('K3_class').Population.sum().tolist()==[5101704,1897838,2066980]
    assert f.additional_zero_housing_positive_population.sum()==8
    assert f.loc[f.additional_zero_housing_positive_population,'K3_class'].notna().all()
    assert f.frozen_SOVI_quartile.eq('Q4').sum()==579
    assert f.frozen_SOVI_quartile.equals(m.frozen_SOVI_quartile)
    c='0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
    a=pd.read_csv(io.BytesIO(source_payload(c,'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/candidate/K3_CLUSTER_MEMBERSHIP.csv')),dtype={'tract_id':str})
    np.testing.assert_array_equal(f.K3_class,a.candidate_display_cluster)
    np.testing.assert_array_equal(f.frozen_SOVI_quartile,a.frozen_SOVI_quartile)
    np.testing.assert_array_equal(f.Population,a.Population)


def test_d3_is_continuous_exact_five_policy_deficit_without_threshold():
    f=pd.read_csv(lp(CURRENT/'inputs/EIGHT_VARIABLE_FROZEN_TABLE.csv'),dtype={'tract_id':str},float_precision='round_trip')
    p=pd.read_csv(lp(CURRENT/'inputs/FROZEN_POLICY_TRACT_MEANS_2315.csv'),dtype={'tract_id':str},float_precision='round_trip').set_index('tract_id').loc[f.tract_id]
    scheduled=['B_'+s for s in ['impact-first','hospital-first','degree-first','betweenness-first','vulnerability-first']]
    np.testing.assert_allclose(f.MeanTotalDeficit_5,p[scheduled].mean(axis=1),atol=1e-12,rtol=0)
    np.testing.assert_allclose(f.MeanTotalDeficit_5,f.B_Unconstrained+f.MeanDelta,atol=1e-12,rtol=0)
    t=fitz.open(lp(SUITE/'Main/Fig07.pdf'))[0].get_text()
    assert all(x in t for x in ['C1','C2','C3','1,242','475','582','5,101,704','1,897,838','2,066,980','Q4 boundary','full-service-deficit hours'])
    assert not any(x in t for x in ['Top-10','Hotspot','P75','K4','C4','C5','PCA','BUILDVALUE'])
    assert len(fitz.open(lp(SUITE/'Main/Fig07.pdf'))[0].get_images())==0
    palette=read(SUITE/'CURRENT_CLUSTER_PALETTE.json')
    assert palette['figure_cluster_count']==3 and palette['colors']=={'1':'#147f98','2':'#d07734','3':'#7a5899'}


def test_all_current_captions_registry_and_entrypoint_are_consistent():
    t=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    assert not any(x in t.lower() for x in ['2,291','five-class','eleven-feature','hotspot score','top-10'])
    assert all(x in t for x in ['2,299','FEMA_NCV14_CA_v119','California reference scaling','K3','0.2444','0.2337'])
    assert 'no K4 classification is presented or adopted' in t
    assert 'build_current_suite_k3.py' in open(lp(SUITE/'README.md'),encoding='utf-8').read()
    q=read(CURRENT/'BUILD_CHECKPOINT.json')
    assert sha(ROOT/'src/la_grid/plotting/build_current_suite_k3.py')==q['generator_sha256']
    assert all(sha(ROOT/rel)==h for rel,h in q['output_hashes'].items())
    p=read(CURRENT/'COMPLETE_PACKET_AND_MIRROR_QA.json')
    assert p['numbered_figures']==17 and p['packet_pages']['complete']==38


def test_historical_entrypoints_default_to_current_version_without_deleting_history():
    for name in ['consolidate_current_figure_suite.py','apply_author_figure_details_20261012.py',
                 'integrate_final_s05_and_suite_review_20261012.py','finish_author_figure_suite_20261012.py']:
        code=open(lp(ROOT/'src/la_grid/plotting'/name),encoding='utf-8').read()
        tail=code[code.rindex("if __name__"):]
        assert '--historical' in tail and 'from build_current_suite_k3 import main as current_main' in tail
        assert 'current_main()' in tail


def test_frozen_scenario_authority_and_exact_current_artwork_set():
    c='0c5365cc39e2717e0fab4aa3b5d05b445d427eb6'
    spec=json.loads(source_payload(c,'docs/data_research/stage7_natural_hazard_k3_k4_integration_review_20261012/candidate/FROZEN_CANDIDATE_SPECIFICATION.json'))
    assert {k:spec[k] for k in ['hazard','resources','mapping','gate','horizon_hr','realizations']}=={
        'hazard':'2pc50','resources':'C57_D1','mapping':'M1_UTILITY_003','gate':'G1_BASELINE_050','horizon_hr':480,'realizations':1000}
    assert spec['policies']==['Impact-first','Hospital-first','Degree-first','Betweenness-first','Vulnerability-first']
    rows=list(csv.DictReader(open(lp(SUITE/'FIGURE_MANIFEST.csv'),encoding='utf-8-sig')))
    actual={str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'results/figures').iterdir() if p.suffix in ['.pdf','.png']}
    assert actual=={r['mirror_file'] for r in rows}
    for kind in ['Main','Supplement']:
        actual={str(p.relative_to(SUITE)).replace('\\','/') for p in (SUITE/kind).iterdir() if p.suffix in ['.pdf','.png']}
        assert actual=={r['final_name'] for r in rows if r['final_name'].startswith(kind+'/')}


def test_updated_manifest_source_paths_resolve_in_their_declared_frozen_commits():
    rows=list(csv.DictReader(open(lp(SUITE/'FIGURE_MANIFEST.csv'),encoding='utf-8-sig')))
    index=list(csv.DictReader(open(lp(ROOT/'results/figures/FIGURE_INDEX.csv'),encoding='utf-8-sig')))
    for row in rows:
        if row['change_in_this_update']!='UPDATED':continue
        b=source_payload(row['source_commit'],row['source_file'])
        ix=next(r for r in index if r['source_path']==row['current_source_file'])
        assert ix['source_data_path']==row['source_file']
        assert ix['source_authority']==row['source_commit']
        assert hashlib.sha256(b).hexdigest()==ix['source_data_sha256']


def test_s10_active_cross_reference_registry_and_packet_page():
    rows=list(csv.DictReader(open(lp(SUITE/'FIGURE_MANIFEST.csv'),encoding='utf-8-sig')))
    active={r['final_name'].split('/')[-1].split('.')[0] for r in rows}
    assert 'FigS11' in active and not active&{'FigS02','FigS12','FigS13'}
    text=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    captions=dict(re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)',text,re.M|re.S))
    heading=next(h for h in captions if h.startswith('Supplementary Figure S10.'))
    expected='Outcome comparisons appear in Figures 4\u20136 and Supplementary Figure S11'
    assert expected in captions[heading]
    assert 'Supplementary Figures S12/S13' not in captions[heading]
    # All supplementary references in active captions must resolve, including multi-reference sentences.
    assert {'FigS'+n.zfill(2) for n in re.findall(r'\bS(\d{1,2})\b',text)}<=active
    main_refs=re.findall(r'(?<!Supplementary )\bFigures? (\d+)',text)
    assert {'Fig'+n.zfill(2) for n in main_refs}<=active
    full=fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(full)==38
    assert expected in ' '.join(full[31].get_text().split())
    assert 'Supplementary Figures S12/S13' not in full[31].get_text()


def test_caption_only_followup_preserves_all_approved_artwork_bytes():
    baseline='8f2dcb3b9762137b9f2686609c34480334f5d44e'
    manifest=list(csv.DictReader(io.StringIO(source_payload(baseline,'results/figure_review/FIGURE_MANIFEST.csv').decode())))
    assert len(manifest)==34
    for r in manifest:
        assert sha(ROOT/r['current_source_file'])==r['sha256']==sha(ROOT/r['mirror_file'])
        assert hashlib.sha256(source_payload(baseline,r['current_source_file'])).hexdigest()==r['sha256']
    for name in ['ALL_MAIN_FIGURES.pdf','ALL_SUPPLEMENT_FIGURES.pdf','CURRENT_CLUSTER_PALETTE.json']:
        rel='results/figure_review/'+name
        assert sha(ROOT/rel)==hashlib.sha256(source_payload(baseline,rel)).hexdigest()


def test_canonical_caption_rule_changes_only_s10_and_is_idempotent():
    import ast
    path=ROOT/'src/la_grid/plotting/build_current_suite_k3.py'
    tree=ast.parse(open(lp(path),encoding='utf-8').read())
    nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(
        isinstance(t,ast.Name) and t.id.startswith('S10_') for t in n.targets)]
    nodes+=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='correct_s10_reference']
    namespace={}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
    transform=namespace['correct_s10_reference']
    parse=lambda text:{h:b.strip() for h,b in re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)',text,re.M|re.S)}
    baseline='8f2dcb3b9762137b9f2686609c34480334f5d44e'
    source=parse(source_payload(baseline,'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    current=parse(open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read())
    assert len(source)==len(current)==17 and list(source)==list(current)
    for h,b in source.items():
        assert current[h]==transform(h,b)==transform(h,transform(h,b))
    assert sum(source[h]!=current[h] for h in source)==1
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    assert 'correct_s10_reference' in ast.unparse(main)
