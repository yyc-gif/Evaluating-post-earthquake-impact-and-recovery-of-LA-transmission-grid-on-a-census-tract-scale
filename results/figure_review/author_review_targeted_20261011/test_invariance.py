"""Checks tailored to the authorized regions, source identity and scientific scope."""
from common import *
import numpy as np
from PIL import Image

def unchanged_pixels(before,after,rect_mm):
    a=fitz.open(lp(PKG/before));b=fitz.open(lp(PKG/after));clip=fitz.Rect(*(v*MM for v in rect_mm))
    one=a[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=clip,alpha=False)
    two=b[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=clip,alpha=False)
    assert one.width==two.width and one.height==two.height
    assert one.samples==two.samples,f'Unrelated rendered region changed: {after}, {rect_mm}'

def test_original_authority_and_source_hashes():
    records=json.load(open(lp(PKG/'SOURCE_HASHES.json'),encoding='utf-8'))
    for rel,r in records.items():
        assert source(rel)[1]==r['sha256']
    before=json.load(open(lp(PKG/'qa/BASELINE_INSPECTION.json'),encoding='utf-8'))
    for key,r in before.items():assert sha(PKG/'before'/(key.split('/')[-1]+'.pdf'))==r['source_sha256']

def test_fig03_other_panels_and_colorbar_values_unchanged():
    unchanged_pixels('before/Fig03.pdf','Fig03_Low_End_Palette.pdf',[0,0,185,140])
    unchanged_pixels('before/Fig03.pdf','Fig03_Low_End_Palette.pdf',[0,140,90,216])
    a=fitz.open(lp(PKG/'before/Fig03.pdf'));b=fitz.open(lp(PKG/'Fig03_Low_End_Palette.pdf'))
    assert a[0].get_text()==b[0].get_text()
    ai=a[0].get_images()[0][0];bi=b[0].get_images()[0][0]
    assert a.xref_stream(ai)==b.xref_stream(bi) # scalar colorbar pixel indices

def test_fig05_other_panels_and_reference_maps_preserved():
    unchanged_pixels('before/Fig05.pdf','Fig05_Q4_Context_Candidate.pdf',[0,0,185,174])
    a=fitz.open(lp(PKG/'before/Fig05.pdf'));b=fitz.open(lp(PKG/'Fig05_Q4_Context_Candidate.pdf'))
    def norm(s):return s.replace('\xa0',' ').replace('\xad','-')
    assert norm(a[0].get_text()).strip() in norm(b[0].get_text())
    assert abs(a[0].rect.height-b[0].rect.height)<.001
    qa=json.load(open(lp(PKG/'QUARTILE_AND_DEGREE_PROVENANCE.json')))
    assert qa['domain_tracts']==2315 and sum(qa['quartile_counts'].values())==2315
    assert qa['quartile_counts']['Q4']==579
    assert abs(qa['degree_population_weighted_change_hr']-qa['degree_saved_summary_change_hr'])<1e-9

def test_fig07_heatmap_hotspot_and_statistical_text_preserved():
    unchanged_pixels('before/Fig07.pdf','Fig07_Cluster_Color_Candidate.pdf',[0,96,185,167])
    unchanged_pixels('before/Fig07.pdf','Fig07_Cluster_Color_Candidate.pdf',[93,172,185,253])
    a=fitz.open(lp(PKG/'before/Fig07.pdf'));b=fitz.open(lp(PKG/'Fig07_Cluster_Color_Candidate.pdf'))
    assert a[0].get_text()==b[0].get_text()
    assert '#7b828f'==json.load(open(lp(PKG/'ARTWORK_EDIT_RECORDS.json')))['Fig07_recommended']['edits']['new']

def test_s09_pca_loadings_and_support_diagnostics_preserved():
    unchanged_pixels('before/FigS09.pdf','FigS09_Palette_Synchronization.pdf',[100,0,185,174])
    unchanged_pixels('before/FigS09.pdf','FigS09_Palette_Synchronization.pdf',[0,89,185,174])
    a=fitz.open(lp(PKG/'before/FigS09.pdf'));b=fitz.open(lp(PKG/'FigS09_Palette_Synchronization.pdf'))
    assert a[0].get_text()==b[0].get_text()

def test_framework_preserves_topology_connections_and_replaces_only_requested_words():
    d=fitz.open(lp(PKG/'Fig01_Author_Review.pdf'));s=d[0].get_text().replace('\xa0',' ').replace('\xad','-')
    assert 'Service loss (0-480 h)' not in s and 'All + hospital tracts' not in s
    for label in ['Cumulative service loss','hospital-linked tracts','Schematic','Gap','Q1','Q2','Q3','Q4',
        'Tested conditions','Resources (Fig6): crews and repair duration','Assumptions (S6, S8): mapping, gates and planning limits']:
        assert label in s,label
    r=json.load(open(lp(PKG/'ARTWORK_EDIT_RECORDS.json')))['Fig01']['edits']
    assert len(r['marker_forms'])==12 and r['linear_marker_reduction_percent']==25
    assert all(c['scale']==.75 for f in r['inline_circle_edits'] for c in f['circles'])
    assert r['marker_origins_and_Do_invocations_preserved'] and r['stage_positions_connections_preserved']

def test_native_sizes_dpi_fonts_and_no_added_rasterization():
    for name in ['Fig01_Author_Review','Fig03_Low_End_Palette','Fig05_Q4_Context_Candidate','Fig07_Cluster_Color_Candidate','FigS09_Palette_Synchronization']:
        d=fitz.open(lp(PKG/(name+'.pdf')));p=d[0]
        assert abs(p.rect.width/MM-185)<.001
        assert all(p.rect.contains(fitz.Rect(s['bbox'])) for s in spans(p))
        assert min(s['size'] for s in spans(p))>=6.99
        im=Image.open(lp(PKG/(name+'.png')))
        assert all(abs(dpi-600)<1 for dpi in im.info['dpi'])
    d=fitz.open(lp(PKG/'Fig05_Q4_Context_Candidate.pdf'));assert len(d[0].get_images())==0

def test_review_packet_fonts_and_native_full_figure_width():
    def canonical(t):return re.sub(r'\s+',' ',t.replace('\xa0',' ').replace('\xad','-').replace('\u037e',';'))
    d=fitz.open(lp(PKG/'NATIVE_BEFORE_AFTER_CONTACT_SHEETS.pdf'))
    assert len(d)==7
    for p in d:
        assert 'Each figure: 185 mm; print 100%.' in canonical(p.get_text())
        assert abs(p.rect.width/MM-400)<.001
    review=fitz.open(lp(PKG/'AUTHOR_REVIEW_FIGURES_AND_CAPTIONS.pdf'))
    assert len(review)==12
    for i,p in enumerate(review):
        assert abs(p.rect.width/MM-(185 if i%2==0 else 210))<.001
        if i%2==1:assert all(p.rect.contains(fitz.Rect(s['bbox'])) for s in spans(p))
    assert 'The Q1-Q4 bars' in canonical(review[1].get_text())
    assert 'Thin dark outlines in E' in canonical(review[7].get_text())

