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
EXPECTED=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in range(1,11)]
AUTHOR=ROOT/'docs/reproducibility/figure_suite_author_clarity_numbering_20261013'
CONCISE=ROOT/'docs/reproducibility/figure_suite_concise_captions_20261013'


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
    full=fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'));assert len(full)==21
    caps=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    headings=re.findall(r'^## (.+)',caps,re.M);assert len(headings)==17
    registry=list(csv.DictReader(open(lp(CONCISE/'COMPACT_PACKET_PAGE_REGISTRY.csv'),encoding='utf-8')))
    for i,(stem,title) in enumerate(zip(EXPECTED,headings)):
        source=fitz.open(lp(SUITE/(stem+'.pdf')))
        page=full[i];region=source[0].rect
        assert page.rect.width==region.width and page.rect.height>region.height
        assert abs(source[0].rect.width-185*72/25.4)<.15
        assert page.get_pixmap(dpi=72,clip=region).samples==source[0].get_pixmap(dpi=72).samples
        capregion=fitz.Rect(0,region.height,page.rect.width,page.rect.height)
        assert ' '.join(title.split()) in ' '.join(page.get_textbox(capregion).split())
        # Clip-unaware PDF extraction also returns historical hidden source text.
        # Verify the actual caption Form, not those nonrendered figure labels.
        record=registry[i]
        candidates=[full.xref_stream(x[0]) for x in page.get_xobjects()]
        actual=[b for b in candidates if hashlib.sha256(b).hexdigest()==record['caption_stream_sha256']]
        assert len(actual)>=1 and float(record['caption_min_font_pt'])>=9.99
        assert record['caption_bounds_valid']=='True'
        assert all(float(n)>=9.99 for n in re.findall(rb'([0-9.]+)\s+Tf\b',actual[0]))
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
    assert all(x in t for x in ['Service loss','Time to 80% service','T80','|Q4-Q1| loss gap','Gini','Community typology','High vulnerability +','slow-recovery hotspots'])
    assert 'Hotspot score' not in t
    assert 'Schematic' not in t
    new=read(AUTHOR/'FIG01_WORDING_QA.json');assert new['stage5_body_font_pt']==7.5
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
    t=fitz.open(lp(SUITE/'Supplement/FigS08.pdf'))[0].get_text()
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
    cool=read(AUTHOR/'POPULATION_PALETTE_QA.json')
    assert cool['palette'].startswith('Blues') and cool['population_values_log_normalization_ticks_geometry_rank_labels_unchanged']
    assert cool['dark_priority_markers_unchanged']
    d=fitz.open(lp(SUITE/'Supplement/FigS09.pdf'))
    ranks=[s for b in d[0].get_text('dict',flags=0)['blocks'] for line in b.get('lines',[]) for s in line['spans'] if s['text'] in ['1','2','3','4','5']]
    assert ranks and all(s['color']!=0x007c83 for s in ranks)


def test_resource_merge_reuses_eight_original_vector_panels():
    e=audit()['operator_edits']['Supplement/FigS11']
    assert e['eight_original_resource_panels_reused'] and e['no_means_ranges_or_trajectories_recomputed']
    assert len(e['layout_records'])==8
    assert {r['source'] for r in e['layout_records']}=={'Supplement/FigS12','Supplement/FigS13'}
    d=fitz.open(lp(SUITE/'Supplement/FigS10.pdf'));assert len(d[0].get_images())==0
    spans=[s for b in d[0].get_text('dict',flags=0)['blocks'] for line in b.get('lines',[]) for s in line['spans']]
    assert min(s['size'] for s in spans)>=7.99
    assert all(d[0].rect.contains(fitz.Rect(s['bbox'])) for s in spans)
    assert all(chr(65+i)+'.' in d[0].get_text() for i in range(8))


def test_retired_figures_and_s02_have_no_current_placeholders():
    for n in ['FigS11','FigS12','FigS13']:
        assert not (SUITE/'Supplement'/(n+'.pdf')).exists()
        assert not (SUITE/'Page_Previews'/(n+'.png')).exists()
    caps=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    assert not re.search(r'^## Supplementary Figure S(?:11|12|13)\.',caps,re.M)
    index=list(csv.DictReader(open(lp(ROOT/'results/figures/FIGURE_INDEX.csv'),encoding='utf-8-sig')))
    assert len(index)==34 and not {r['figure_number'] for r in index}&{'FigS11','FigS12','FigS13'}
    baseline='3c7899f0f328d37b99d2b022f1650c5288a4a664'
    assert sha(SUITE/'Supplement/FigS02.pdf')==hashlib.sha256(source_payload(baseline,'results/figure_review/Supplement/FigS03.pdf')).hexdigest()


def test_previous_heatmap_is_the_exact_fig4_reference_subtraction():
    rows=list(csv.DictReader(open(lp(QA/'S11_FIG4_NUMERICAL_IDENTITY.csv'),encoding='utf-8')))
    assert len(rows)==24 and max(abs(float(r['identity_error_h'])) for r in rows)<1e-10
    assert not audit()['S11_Fig4_identity']['new_scientific_estimates']


def test_unrelated_artwork_and_original_staged_science_are_unchanged():
    rows=list(csv.DictReader(open(lp(AUTHOR/'NUMBERING_AND_ARTWORK_CHANGES.csv'),encoding='utf-8')))
    assert len([r for r in rows if r['content_change']=='True'])==8
    assert len([r for r in rows if r['content_change']=='False'])==26
    for r in rows:
        if r['content_change']=='False':
            assert sha(SUITE/(r['current_figure']+'.'+r['format']))==r['baseline_SHA256']==r['current_SHA256']
    before=read(CURRENT/'PRESERVATION_BEFORE.json');after=read(CURRENT/'PRESERVATION_AFTER.json')
    assert before==after and before['protected_count']==950 and before['staged_count']==862
    q=read(CURRENT/'COMPLETE_PACKET_AND_MIRROR_QA.json')
    assert not q['scientific_fits_or_evaluations_run']
    assert all(r['actual_packet_pixels_identical'] for r in q['packet_checks'])
    assert read(AUTHOR/'PRESERVATION_BEFORE.json')==read(AUTHOR/'PRESERVATION_AFTER.json')


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
    caption=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    assert all(x in t for x in ['C1','C2','C3','1,242','475','582','Q4 boundary','full-service-deficit hours'])
    assert f.groupby('K3_class').Population.sum().tolist()==[5101704,1897838,2066980]
    assert all(x in caption for x in ['eight fitted coordinates','NCV14/H2/K3','five-policy'])
    assert not any(x in t for x in ['Top-10','Hotspot','P75','K4','C4','C5','PCA','BUILDVALUE'])
    assert len(fitz.open(lp(SUITE/'Main/Fig07.pdf'))[0].get_images())==0
    palette=read(SUITE/'CURRENT_CLUSTER_PALETTE.json')
    assert palette['figure_cluster_count']==3 and palette['colors']=={'1':'#147f98','2':'#d07734','3':'#7a5899'}


def test_all_current_captions_registry_and_entrypoint_are_consistent():
    t=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    assert not any(x in t.lower() for x in ['2,291','five-class','eleven-feature','hotspot score','top-10'])
    assert all(x in t for x in ['eight fitted coordinates','NCV14/H2/K3','K3 is not the silhouette maximum'])
    assert 'calibrated' not in t
    assert 'build_current_suite_k3.py' in open(lp(SUITE/'README.md'),encoding='utf-8').read()
    q=read(CONCISE/'BUILD_CHECKPOINT.json')
    assert sha(ROOT/'src/la_grid/plotting/build_current_suite_k3.py')==q['routing_sha256']
    assert sha(ROOT/'src/la_grid/plotting/short_current_captions_20261013.py')==q['generator_sha256']
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
        # Keep the previous Fig01/FigS09 source checks even though their artwork is retained this round.
        if row['final_name'] not in ['Main/Fig01.pdf','Main/Fig01.png','Main/Fig07.pdf','Main/Fig07.png','Supplement/FigS08.pdf','Supplement/FigS08.png']:continue
        b=source_payload(row['source_commit'],row['source_file'])
        ix=next(r for r in index if r['source_path']==row['current_source_file'])
        assert ix['source_data_path']==row['source_file']
        assert ix['source_authority']==row['source_commit']
        assert hashlib.sha256(b).hexdigest()==ix['source_data_sha256']


APPROVED=ROOT/'docs/reproducibility/figure7_candidateA_approved_integration_20261013'
ACCEPTED='3c7899f0f328d37b99d2b022f1650c5288a4a664'


def test_s10_active_cross_reference_registry_and_packet_page():
    rows=list(csv.DictReader(open(lp(SUITE/'FIGURE_MANIFEST.csv'),encoding='utf-8-sig')))
    active={r['final_name'].split('/')[-1].split('.')[0] for r in rows}
    assert 'FigS10' in active and 'FigS02' in active and not active&{'FigS11','FigS12','FigS13'}
    text=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    captions=dict(re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)',text,re.M|re.S))
    heading=next(h for h in captions if h.startswith('Supplementary Figure S9.'))
    expected='Outcome comparisons appear in Figures 4\u20136 and Supplementary Figure S10'
    assert expected in captions[heading] and 'Supplementary Figures S12/S13' not in captions[heading]
    assert {'FigS'+n.zfill(2) for n in re.findall(r'\bS(\d{1,2})\b',text)}<=active
    assert {'Fig'+n.zfill(2) for n in re.findall(r'(?<!Supplementary )\bFigures? (\d+)',text)}<=active
    full=fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(full)==21 and expected in ' '.join(full[15].get_text().split())
    assert 'Supplementary Figures S12/S13' not in full[15].get_text()


def test_followup_preserves_author_untouched_artwork_including_figure7_and_k3():
    manifest=list(csv.DictReader(io.StringIO(source_payload(ACCEPTED,'results/figure_review/FIGURE_MANIFEST.csv').decode())))
    assert len(manifest)==34
    unchanged=0
    for r in manifest:
        old=r['final_name'].rsplit('.',1)[0]
        if old not in ['Main/Fig01','Supplement/FigS05','Supplement/FigS06','Supplement/FigS10']:
            if old.startswith('Supplement/'):
                number=int(old.split('FigS')[1]);number=number if number==1 else number-1
                rel=f'Supplement/FigS{number:02d}.'+r['final_name'].rsplit('.',1)[1]
            else:rel=r['final_name']
            assert sha(SUITE/rel)==r['sha256']
            assert hashlib.sha256(source_payload(ACCEPTED,r['current_source_file'])).hexdigest()==r['sha256']
            unchanged+=1
    assert unchanged==26
    current=list(csv.DictReader(open(lp(SUITE/'FIGURE_MANIFEST.csv'),encoding='utf-8-sig')))
    assert {r['final_name'] for r in current if r['change_in_this_update']=='UPDATED'}=={s+'.'+e for s in ['Main/Fig01','Supplement/FigS04','Supplement/FigS05','Supplement/FigS09'] for e in ['pdf','png']}
    q=read(APPROVED/'FIG07_NUMERICAL_QA.json')
    assert q['exact_raw_feature_and_membership_match'] and not q['new_fits_or_simulations']


def test_canonical_legacy_s10_caption_rule_and_new_numbering_are_idempotent():
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
    source=parse(source_payload(ACCEPTED,'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    current=parse(open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read())
    assert len(source)==len(current)==17
    for h,b in source.items():
        assert transform(h,b)==transform(h,transform(h,b))
    h=next(h for h in current if h.startswith('Figure 7.'))
    frozen=parse(source_payload('3c7899f0f328d37b99d2b022f1650c5288a4a664','results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    assert current[h]!=frozen[h] and len(current[h].split())<=90
    assert 'eight fitted coordinates' in current[h] and 'NCV14/H2/K3' in current[h]
    assert [int(n) for n in re.findall(r'^## Supplementary Figure S(\d+)\.',open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read(),re.M)]==list(range(1,11))
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    assert 'short_current_captions_20261013' in ast.unparse(main)


def test_all_eighteen_ecdfs_preserve_exact_observations_zeros_and_ties():
    features=['Grid_Impact','Redundancy_HHI','B_Unconstrained','MeanDelta','SOVI_SCORE','FEMA_NCV14_CA_v119']
    f=pd.read_csv(lp(CURRENT/'inputs/EIGHT_VARIABLE_FROZEN_TABLE.csv'),float_precision='round_trip')
    points=pd.read_csv(lp(APPROVED/'ECDF_POINTS.csv'),float_precision='round_trip')
    medians=pd.read_csv(lp(APPROVED/'ECDF_MEDIANS.csv'),float_precision='round_trip')
    assert set(points.variable)==set(features) and len(points.groupby(['variable','class']))==18
    for (field,c),group in points.groupby(['variable','class']):
        values=f.loc[f.K3_class.eq(int(c[1:])),field].to_numpy()
        unique,counts=np.unique(values,return_counts=True)
        np.testing.assert_array_equal(group.value,unique)
        np.testing.assert_array_equal(group.value_count,counts)
        np.testing.assert_array_equal(group.cumulative_fraction,np.cumsum(counts)/len(values))
        assert int(group.value_count.sum())==len(values)
        row=medians.loc[medians.variable.eq(field)&medians['class'].eq(c)].iloc[0]
        assert row['median']==np.median(values) and row.marker_y==.5
        assert row.zero_count==(values==0).sum()


def test_twentyfour_profile_cells_use_frozen_cohort_standardization_not_centroid_scaling():
    f=pd.read_csv(lp(CURRENT/'inputs/EIGHT_VARIABLE_FROZEN_TABLE.csv'),float_precision='round_trip')
    weights=pd.read_csv(lp(CURRENT/'inputs/COHORT_STANDARDIZER_AND_WEIGHTS.csv'),float_precision='round_trip').set_index('variable')
    rows=pd.read_csv(lp(APPROVED/'PROFILE_CELLS.csv'),float_precision='round_trip',dtype={'printed_value':str})
    assert len(rows)==24 and rows.variable.nunique()==8
    for _,row in rows.iterrows():
        w=weights.loc[row.variable]
        values=(f.loc[f.K3_class.eq(int(row['class'][1:])),row.variable]-w.cohort_mean)/w.population_SD
        assert abs(row.ordinary_z_mean-values.mean())<1e-12
        assert row.printed_value==f'{values.mean():+.2f}'
    q=read(APPROVED/'FIG07_NUMERICAL_QA.json')
    assert q['cohort_SD_ddof']==0 and q['Init_zero_count']==1533
    assert q['class_counts']==[1242,475,582] and q['represented_population']==9066522
    assert q['D3_identity_maximum_error_h']<1e-12


def test_approved_native_layout_white_na_vector_changes_and_no_review_warning():
    d=fitz.open(lp(SUITE/'Main/Fig07.pdf'));p=d[0]
    assert abs(p.rect.width*25.4/72-185)<1e-4 and abs(p.rect.height*25.4/72-253)<1e-4
    assert not p.get_images()
    t=p.get_text()
    assert 'LAYOUT PROPOSAL' not in t
    assert 'Feature distributions' in t and 'Standardized eight-coordinate' in t
    # PDF Form reuse retains nonrendered source provenance outside its C/D clip.
    # Actual A/B pixels, not clipping-unaware text extraction, must match Candidate A.
    pixel=read(APPROVED/'CD_VECTOR_AND_ALIGNED_PIXEL_QA.json')
    assert pixel['approved_candidate_AB_pixels_identical_except_removed_review_warning']
    assert pixel['outside_authorized_NA_path_masks_changed_pixels']==0
    q=read(APPROVED/'NA_VECTOR_PAINT_QA.json')
    assert q['authorized_NA_drawings']==34 and q['map_polygons']==32 and q['legend_swatches']==2
    assert q['fill']=='#FFFFFF' and q['outline']=='#777777' and q['outline_width_pt']==.45
    assert q['path_geometry_and_all_other_vector_properties_exact'] and q['non_NA_vectors_exact']
    assert all(r['original_stream_sha256']==r['stripped_revised_stream_sha256'] for r in q['content_streams'])
    palette=read(SUITE/'CURRENT_CLUSTER_PALETTE.json')
    assert palette['NA_fill']=='#FFFFFF' and palette['NA_outline_width_pt']==.45
    move=read(APPROVED/'CD_TRANSLATION_QA.json')
    assert move['translation_mm']==[0,8] and move['scale']==1 and not move['geometry_regenerated']


def test_candidate_a_protection_and_independent_packet_qa():
    before=read(APPROVED/'PRESERVATION_BEFORE.json');after=read(APPROVED/'PRESERVATION_AFTER.json')
    assert before==after and before['protected']['protected_count']==950
    assert before['protected']['staged_count']==862
    q=read(APPROVED/'INDEPENDENT_QA.json')
    assert q['ecdfs_independently_reconstructed']==18 and q['standardized_profile_cells_independently_reconstructed']==24
    assert q['unchanged_numbered_artwork_pairs']==16 and q['packet_pages']==38
    assert q['all_unaffected_packet_pages_identical'] and q['all_packet_figure_pixels_identical_to_actual_artwork']


def test_source_only_control_retains_threshold_and_matches_every_frozen_sample():
    q=read(AUTHOR/'SOURCE_GATE_AND_THRESHOLD_QA.json')
    assert q['independent_source_only_control_available']
    assert q['functionality_threshold']==.5 and q['source_connectivity_fixed_in_threshold_tests']
    assert q['all_1000_realization_ids_matched'] and q['physical_sample_hashes_identical']
    assert q['no_damage_scheduling_ga_sampling_or_trajectory_generation']
    rows=pd.read_csv(lp(AUTHOR/'SOURCE_ONLY_REALIZATION_VALUES.csv'),float_precision='round_trip')
    assert len(rows)==3000 and rows.source_gate.eq('disabled').all()
    assert rows.functionality_threshold.eq(.5).all() and rows.horizon_hr.eq(480).all()
    assert rows.mapping.eq('M1_UTILITY_003').all()
    np.testing.assert_allclose(rows.source_off_loss_h,rows.baseline_loss_h-rows.source_path_loss_h,atol=1e-10,rtol=0)
    np.testing.assert_allclose(rows.service_loss_gap_h,-rows.source_path_loss_h,atol=1e-10,rtol=0)
    identity=None
    for policy, group in rows.groupby('policy'):
        assert group.realization_id.tolist()==[f'2pc50__evaluation_{i:04d}' for i in range(1000)]
        if identity is None:identity=group.physical_sample_sha256.to_numpy()
        else:np.testing.assert_array_equal(group.physical_sample_sha256,identity)
    # Independently reconstruct the new control with mapped tract rather than station population sums.
    inputs=AUTHOR/'source_control_inputs'
    tracts=pd.read_csv(lp(inputs/'TRACTS.csv'),dtype={'tract_id':str})
    mapping=pd.read_csv(lp(inputs/'MAPPING.csv'),dtype={'tract_id':str,'substation_id':str})
    for policy in rows.policy.unique():
        z=np.load(lp(inputs/(policy+'_INTEGRALS.npz')))
        w=mapping.pivot(index='tract_id',columns='substation_id',values='weight').fillna(0)
        w=w.reindex(index=tracts.tract_id,columns=z['station_ids'].astype(str),fill_value=0).to_numpy()
        values=(z['G1_BASELINE_050__L_self']+z['G1_BASELINE_050__L_threshold'])@w.T
        independently=(values@tracts.population.to_numpy())/tracts.population.sum()
        np.testing.assert_allclose(independently,rows.loc[rows.policy.eq(policy),'source_off_loss_h'],atol=1e-10,rtol=0)
    t=fitz.open(lp(SUITE/'Supplement/FigS05.pdf'))[0].get_text()
    assert all(s in t for s in ['A. Effect','B. Source connectivity disabled','threshold fixed at 0.50',
        'C. Functionality threshold: 0.05','D. Functionality threshold: 0.75'])
    assert not any(s in t for s in ['G0','no gate','confidence interval'])
    estimates=pd.read_csv(lp(AUTHOR/'SOURCE_AND_THRESHOLD_DISPLAY_VALUES.csv'),float_precision='round_trip')
    old=pd.read_csv(lp(QA/'THRESHOLD_DISPLAY_VALUES.csv'))
    for _, r in old.iterrows():
        new=estimates.loc[estimates.policy.eq(r.policy)&estimates.case.eq(r.gate)].iloc[0]
        assert abs(new.mean_gap_h-r.mean_h)<1e-12


def test_ga_wording_keeps_frozen_search_and_validation_distinct():
    q=read(AUTHOR/'GA_LABEL_AND_ESTIMAND_QA.json')
    assert q['GA_runs']==20 and q['initial_random_orders_per_run']==100
    assert q['optimization_realizations']==64 and q['validation_realizations']==2000
    assert q['evaluation_budget_per_run']==100000 and q['CI_inset_removed_from_display']
    t=fitz.open(lp(SUITE/'Supplement/FigS04.pdf'))[0].get_text()
    assert all(s in t for s in ['Repair sequences evaluated','Minimum service loss','20 GA runs',
        'Independent validation','2,000 validation realizations','Mean: -0.533 h','Substation-damage loss'])
    assert not any(s in t for s in ['Distinct objective','Best planning','paired validation','Simultaneous 95%',
        'Paired mean','Self loss'])


def test_actual_current_packet_has_identical_figure_pixels_and_continuous_numbering():
    full=fitz.open(lp(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf'))
    assert len(full)==21
    for i,stem in enumerate(EXPECTED):
        actual=fitz.open(lp(SUITE/(stem+'.pdf')))
        assert full[i].get_pixmap(dpi=72,clip=actual[0].rect).samples==actual[0].get_pixmap(dpi=72).samples
    baseline=fitz.open(stream=source_payload(ACCEPTED,'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf')
    for i in range(4):
        assert full[17+i].get_pixmap(dpi=72).samples==baseline[34+i].get_pixmap(dpi=72).samples


def test_concise_captions_do_not_change_numbered_artwork_or_sneak_in_path_b():
    q=read(CONCISE/'CAPTION_QA.json')
    assert q['old_total_words']==4219 and q['new_total_words']<=1000
    assert q['maximum_caption_words']<=90 and not q['figure_rescaling']
    assert not q['PathB_artwork_promoted'] and q['artwork_pairs_byte_identical']==17
    parent='5fbdf5a33cb8cee4790f81e896776b8b6fb4f9ae'
    rows=list(csv.DictReader(io.StringIO(source_payload(parent,'results/figure_review/FIGURE_MANIFEST.csv').decode())))
    for r in rows:
        assert sha(ROOT/r['current_source_file'])==r['sha256']==sha(ROOT/r['mirror_file'])
    caps=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    assert not any(x in caps for x in ['-0.532675','1,741','350,799','0.2444','5,101,704','7.5-point'])


PUBLICATION_GATE=ROOT/'docs/reproducibility/path_b_pre_migration_publication_gate_20261014'
PATH_B_REVIEW=ROOT/'docs/data_research/stage7_path_b_p2_integration_review_20261014'


def test_short_captions_distinguish_realization_ranges_and_mean_effect_confidence_intervals():
    text=open(lp(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'),encoding='utf-8').read()
    caps=dict(re.findall(r'^## (.+?)\n\n(.*?)(?=^## |\Z)',text,re.M|re.S))
    for number in [4,5]:
        body=next(b for h,b in caps.items() if h.startswith(f'Figure {number}.'))
        assert '5th-95th realization ranges, not confidence intervals' in body
    f4=next(b for h,b in caps.items() if h.startswith('Figure 4.'))
    assert 'service-loss bars show means without whiskers' in f4
    f6=next(b for h,b in caps.items() if h.startswith('Figure 6.'))
    assert '95% bootstrap confidence intervals for mean effects' in f6
    assert 'Degree-first hospital comparisons show means only' in f6
    q=read(PUBLICATION_GATE/'INDEPENDENT_FOLLOWUP_QA.json')
    assert q['caption_source_matches_export'] and q['visible_caption_text_matches']
    assert q['other_current_captions_exact']==14 and q['packet_pages']==21


def test_path_b_caption_and_conditional_k3_choice_do_not_promote_new_memberships():
    draft=open(lp(PATH_B_REVIEW/'FIGURE7_AND_S9_CAPTION_DRAFTS.md'),encoding='utf-8').read()
    assert draft.count('Six descriptive empirical feature distributions')==2
    assert draft.count('all seven fitted P2 variables')==2
    decision=open(lp(PATH_B_REVIEW/'K3_K4_AUTHOR_DECISION.md'),encoding='utf-8').read()
    assert 'accepted as the conditional' in decision and 'must remain as sensitivity' in decision
    k=pd.read_csv(lp(PATH_B_REVIEW/'K3_K4_K5_DECISION_EVIDENCE.csv')).set_index('k')
    assert k.loc[4,'geographic_full_median_ARI']>k.loc[3,'geographic_full_median_ARI']
    assert k.loc[4,'geographic_heldout_min_ARI']>k.loc[3,'geographic_heldout_min_ARI']
    q=read(PUBLICATION_GATE/'INDEPENDENT_FOLLOWUP_QA.json')
    assert q['models_fitted']==0 and not q['official_Fig07_promoted']


def test_path_b_print_proofs_are_vector_readable_size_reviews_not_official_artwork():
    q=read(PUBLICATION_GATE/'INDEPENDENT_FOLLOWUP_QA.json')
    for r in q['print_fit_figures']:
        path=PUBLICATION_GATE/r['file']
        assert sha(path)==r['sha256'] and r['min_font_pt']>=7.49
        with fitz.open(lp(path)) as doc:
            assert abs(doc[0].rect.width/72-7.2)<1e-6
            assert abs(doc[0].rect.height/72-9)<1e-6
            assert not doc[0].get_images()
    sizes=read(PUBLICATION_GATE/'PUBLICATION_SIZE_ASSUMPTIONS.json')
    assert not sizes['journal_specific_height_confirmed'] and sizes['print_fit_is_review_only']
    assert sizes['print_fit_min_at_8p5in_pt']>=7
    before=read(PUBLICATION_GATE/'STARTING_STATE.json')
    for p,h in before['immutable_hashes'].items():
        assert sha(ROOT/p)==h
    invariant=read(PUBLICATION_GATE/'PRINT_FIT_SCIENTIFIC_AND_VECTOR_QA.json')
    assert all(r['values_exact'] and r['curves_exact']==18 and r['printed_cohort_z_cells']==21 for r in invariant)
