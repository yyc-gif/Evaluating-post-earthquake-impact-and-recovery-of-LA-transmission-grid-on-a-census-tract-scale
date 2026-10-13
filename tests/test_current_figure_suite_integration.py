"""Integrity and scientific-invariance checks for the current numbered suite."""
from pathlib import Path
import csv, hashlib, json, re
import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review'
QA=ROOT/'docs/reproducibility/author_suite_final_layout_20261012'
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
    records={r['current_file']:r for r in audit()['figures']}
    for r in rows:
        assert sha(ROOT/r['current_source_file'])==r['sha256']==records[r['current_source_file']]['sha256']
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
    q=read(QA/'VISUAL_AND_PACKET_QA.json');assert q['Fig1_outside_Stage5_pixels_identical']
    d=fitz.open(lp(SUITE/'Main/Fig01.pdf'))
    t=d[0].get_textbox(fitz.Rect(94.5*72/25.4,164.2*72/25.4,182*72/25.4,217*72/25.4))
    assert all(x in t for x in ['Service loss','T80','Quartile gap','Gini','Community typology','Hotspot score'])
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


def test_s9_contains_only_unchanged_kmeans_diagnostics():
    t=fitz.open(lp(SUITE/'Supplement/FigS09.pdf'))[0].get_text()
    assert 'Inertia' in t and 'Silhouette coefficient' in t
    assert not any(x in t for x in ['PCA','PC1','PC2','Principal component'])
    assert not audit()['operator_edits']['Supplement/FigS09']['kmeans_fit_or_k_search_run']
    rows=list(csv.DictReader(open(lp(QA/'KMEANS_DISPLAY_VALUES.csv'),encoding='utf-8')))
    assert [int(r['k']) for r in rows]==list(range(1,11))
    assert abs(float(rows[4]['inertia'])-16659.582436298988)<1e-9
    assert abs(float(rows[4]['silhouette'])-.13916506976949464)<1e-12


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
    a=audit();sources=read(QA/'SOURCE_HASHES.json')
    assert len(a['updated_figures'])==6 and len(a['retained_figures'])==11
    for stem in a['retained_figures']:
        for ext in ['pdf','png']:
            rel='results/figure_review/'+stem+'.'+ext
            assert sha(ROOT/rel)==sources[a['baseline_commit']+':'+rel]['sha256']
    before=read(QA/'PRESERVATION_BEFORE.json');after=read(QA/'PRESERVATION_AFTER.json')
    assert before==after and before['protected_count']==950 and before['staged_count']==862
    assert not a['scientific_results_recomputed'] and not a['new_scientific_fits_or_evaluations'] and not a['manuscripts_modified']
    assert all(r['actual_packet_pixels_identical'] for r in read(QA/'VISUAL_AND_PACKET_QA.json')['packet_checks'])
