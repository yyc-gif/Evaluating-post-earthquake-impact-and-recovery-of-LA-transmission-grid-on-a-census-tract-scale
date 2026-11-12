"""Artwork/export invariants; no simulations or model fitting."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

import fitz
import numpy as np
from PIL import Image
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src/la_grid/plotting'))
spec=importlib.util.spec_from_file_location('artwork',ROOT/'src/la_grid/plotting/publication_artwork.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
TMP=a.DEST/'tmp/unit_tests'


def fixture_pdf(name='fixture.pdf'):
    TMP.mkdir(parents=True,exist_ok=True)
    target=TMP/name
    with fitz.open(a.original('Fig01')) as source:
        font=a.font_program(source,'ArialMT')
    with fitz.open() as d:
        p=d.new_page(width=180,height=100)
        a.insert_publication_font(p,'Arial',font,'Availability 0.03 -> 1.00')
        p.insert_text((12,24),'Availability 0.03 -> 1.00',fontsize=10,fontname='Arial')
        p.draw_line((12,70),(160,70),color=(.14,.53,.47),width=.7)
        d.save(target,no_new_id=True)
    return target


def test_unit_lossless_optimization_and_rejection_of_changed_geometry():
    source=fixture_pdf()
    x=TMP/'optimized_a.pdf';y=TMP/'optimized_b.pdf'
    a.optimize(source,x)
    a.optimize(source,y)
    assert x.read_bytes()==y.read_bytes()
    result=a.equivalent(source,x)
    assert result['drawing_stream_set_identical'] and result['font_embedding_preserved']
    with fitz.open(x) as d:
        d[0].draw_line((15,65),(140,65),color=(1,0,0),width=1)
        d.save(TMP/'changed.pdf',no_new_id=True)
    with pytest.raises(AssertionError):a.equivalent(source,TMP/'changed.pdf')


def test_unit_real_lossless_tiff_roundtrip_and_repeatability():
    source=fixture_pdf('raster_source.pdf')
    p=TMP/'first.tif';q=TMP/'second.tif'
    result=a.export_raster(source,p,dpi=300)
    a.export_raster(source,q,dpi=300)
    assert p.read_bytes()==q.read_bytes()
    with Image.open(p) as im:
        assert im.format=='TIFF' and im.mode=='RGB'
        assert im.tag_v2[259]==5
        assert im.info['dpi']==(300.,300.)
        assert hashlib.sha256(im.tobytes()).hexdigest()==result['rendered_rgb_sha256']


def test_unit_filename_and_master_write_guards():
    source=fixture_pdf('guard_source.pdf')
    with pytest.raises(ValueError,match='extension'):
        a.export_raster(source,TMP/'fake.pdf',fmt='tiff')
    with pytest.raises(ValueError,match='read-only'):
        a.export_raster(source,a.original('Fig05'))
    with pytest.raises(ValueError,match='reduce text'):
        a.export_raster(source,TMP/'tiny.tif',width_mm=5)


def test_unit_vector_placement_matches_public_wrapper():
    source=fixture_pdf('placement_source.pdf')
    with fitz.open(source) as src, fitz.open() as public, fitz.open() as fast:
        crop=fitz.Rect(6,5,174,93)
        target=fitz.Rect(10,10,178,98)
        p=public.new_page(width=190,height=110)
        q=fast.new_page(width=190,height=110)
        p.show_pdf_page(target,src,0,clip=crop,keep_proportion=False)
        a.place_vector(q,target,src,clip=crop)
        assert np.array_equal(np.array(a.render_image(p,600)),np.array(a.render_image(q,600)))
        assert p.get_text()==q.get_text()
        assert not q.get_images()


def test_unit_embedded_font_has_numeric_and_caption_coverage():
    with fitz.open(a.original('Fig01')) as doc:
        for name in ['ArialMT','Arial-BoldMT']:
            font=fitz.Font(fontbuffer=a.font_program(doc,name))
            assert all(font.has_glyph(i) for i in range(32,127))
    with fitz.open(fixture_pdf('font_coverage.pdf')) as doc:
        assert doc[0].get_text().strip()=='Availability 0.03 -> 1.00'


def test_unit_off_strip_pruning_retains_vector_geometry_and_pixels():
    leaf=fixture_pdf('strip_leaf.pdf')
    with fitz.open(leaf) as asset, fitz.open() as source:
        p=source.new_page(width=200,height=250)
        p.show_pdf_page(fitz.Rect(10,10,190,110),asset,0)
        p.show_pdf_page(fitz.Rect(10,140,190,240),asset,0)
        expected=np.array(a.render_image(p,600))
        sections=[dict(source_y=[0,120],target_y=[0,120],scale=1),
                  dict(source_y=[132,250],target_y=[120,238],scale=1)]
        data,stats,media=a.strip_source_document(source.tobytes(),sections)
        assert stats['omitted_outside_form_calls']>=2
        with fitz.open(stream=data,filetype='pdf') as strips, fitz.open() as result:
            q=result.new_page(width=200,height=238)
            for i,s in enumerate(sections):
                top,bottom=s['source_y'];lo,hi=s['target_y']
                placement=a.place_vector(q,fitz.Rect(0,lo,200,hi),strips,
                    clip=fitz.Rect(0,top,200,bottom),pno=i)
                s['resource_name']=placement['resource_name']
            output=TMP/'pruned_geometry.pdf'
            result.save(output,no_new_id=True)
        a.canonicalize_strip_transforms(output,sections,media)
        with fitz.open(output) as result:
            actual=np.array(a.render_image(result[0],600))
            assert not result[0].get_images()
        assert np.array_equal(expected[1:999],actual[1:999])
        assert np.array_equal(expected[1101:2083],actual[1001:1983])


def test_all_32_accepted_artwork_payloads_match_starting_commit():
    expected={r['name']:r['oid'] for r in json.loads(subprocess.check_output(
        ['git','lfs','ls-files','--json',a.BASE],cwd=ROOT,text=True))['files']}
    for path in a.source_files():
        for p in [path,path.with_suffix('.png')]:
            assert a.sha(p.read_bytes())==expected[a.relative(p)]
    assert len(a.source_files())==16


def test_master_registry_retains_every_scientific_identity_and_verified_delivery():
    records=a.registry()
    assert list(records)==[key for _,key in a.ITEMS]
    assert len(records)==16 and len(set(r['master_number'] for r in records.values()))==16
    for r in records.values():
        assert a.sha((ROOT/r['accepted_source']).read_bytes())==r['source_sha256']
        assert a.sha((ROOT/r['pdf']).read_bytes())==r['pdf_sha256']
        assert r['verification']['pixel_identical_dpi']==[150,600]
        assert r['verification']['drawing_stream_set_identical']
        assert r['verification']['text_operators_and_unicode_maps_identical']
        assert r['verification']['unembedded_font_names']==[]
    s5=records['mapping_gate_sensitivity']
    assert s5['pdf']==s5['accepted_source']


def test_object_inventory_quantifies_actual_workflow_size():
    records=json.loads((a.DEST/'qa/OBJECT_PREFLIGHT.json').read_text())['figures']
    assert len(records)==16
    f=records[0]
    assert f['bytes']==37843115
    assert f['stream_bytes']['form']==35232026 and f['stream_bytes']['image']==14635
    assert f['stream_bytes']['form']/f['bytes']>.9
    assert f['potential_raw_duplicate_bytes']<f['bytes']*.04
    assert all(not r['unembedded_fonts'] and not r['clipped_text'] for r in records)


def test_compact_layout_is_translation_not_global_scaling():
    qa=json.loads((a.DEST/'qa/COMPACT_LAYOUT_QA.json').read_text())
    assert qa['no_plot_map_or_schedule_scaled']
    assert qa['geometry_preserved_with_bounded_edge_antialiasing']
    assert qa['pixel_comparison']['significant_off_edge_changes']==0
    assert qa['pixel_comparison']['max_channel_delta']<=32
    assert qa['pixel_comparison']['changed_fraction']<=.001
    assert qa['pixel_comparison']['mean_absolute_rgb_delta']<=.005
    assert qa['exact_decimal_unit_translations']
    assert qa['off_strip_form_pruning']['omitted_outside_form_calls']>0
    assert qa['source_text_inventory_preserved_except_reference_changes']
    assert qa['reference_changes']=={}
    assert all(s['scale']==1 for s in qa['sections'])
    assert qa['minimum_text_pt']>=7.49
    assert qa['compact_mm'][0]==pytest.approx(185,abs=.01)
    assert qa['original_mm'][1]-qa['compact_mm'][1]>20
    assert len(qa['text_raised_from_7_to_7_5pt'])==10
    assert a.sha((ROOT/qa['output']).read_bytes())==qa['output_sha256']


def test_candidate_numbering_is_bijective_and_does_not_change_masters():
    data=json.loads((a.DEST/'IJDRS/FIGURE_REFERENCE_CROSSWALK.json').read_text())['figures']
    assert len(data)==16 and len({r['identity'] for r in data})==16
    assert sum(r['role']=='Main' for r in data)==5
    assert sum(r['role']=='Supplement_Proposed' for r in data)==11
    mapping={r['master_number']:r['ijdrs_label'] for r in data}
    assert mapping['Fig04']=='Figure 3'
    assert mapping['Fig08']=='Supplementary Figure S3'
    assert a.rewrite_references('Figure 5 and Figure 8')=='Figure 4 and Supplementary Figure S3'
    assert a.rewrite_references('Figures 5-7 and Supplementary Figure S8')=='Figures 4-5 and Supplementary Figures S2 and S11'
    cfg=json.loads((a.DEST/'IJDRS/CONFIGURATION.json').read_text())
    assert cfg['master_collection_preserved'] and not cfg['supplementary_limit_verified']
    assert not cfg['original_manuscript_modified']


def test_all_sixteen_tiffs_are_real_600dpi_rgb_and_have_bound_pixel_checks():
    rows=json.loads((a.DEST/'IJDRS/EXPORT_MANIFEST.json').read_text())['figures']
    assert len(rows)==16
    for row in rows:
        p=ROOT/row['output']
        assert a.sha(p.read_bytes())==row['sha256']
        with Image.open(p) as im:
            assert im.format=='TIFF' and im.mode=='RGB'
            assert im.info['dpi']==(600.,600.) and im.tag_v2[259]==5
            assert a.sha(im.info['icc_profile'])==row['icc_sha256']
            assert a.sha(im.tobytes())==row['rendered_rgb_sha256']
            assert list(im.size)==row['pixels']
        assert row['roundtrip_rgb_pixels_identical'] and row['min_printed_text_pt']>=6.99
        if row['identity']!='workflow':
            source=ROOT/a.registry()[row['identity']]['png']
            with Image.open(source) as im:assert a.sha(im.convert('RGB').tobytes())==row['rendered_rgb_sha256']


def test_workflow_candidate_only_changes_profile_specific_cross_references():
    qa=json.loads((a.DEST/'qa/IJDRS_WORKFLOW_REFERENCE_QA.json').read_text())
    assert qa['reference_changes']=={'strategies in Figure 5':'strategies in Figure 4',
        'See Figure 8 for class key':'See Supplementary Fig. S3 for class key'}
    assert qa['geometry_preserved_with_bounded_edge_antialiasing']
    assert qa['pixel_comparison']['significant_off_edge_changes']==0
    assert qa['pixel_comparison']['max_channel_delta']<=32
    assert qa['pixel_comparison']['changed_fraction']<=.001
    assert qa['pixel_comparison']['mean_absolute_rgb_delta']<=.005
    assert qa['no_plot_map_or_schedule_scaled']
    assert qa['source_sha256']==a.registry()['workflow']['source_sha256']


def test_caption_reference_ranges_are_valid_in_the_candidate():
    text=(a.DEST/'IJDRS/CAPTIONS.md').read_text(encoding='utf-8')
    assert len(re.findall(r'^## ',text,re.M))==16
    for m in re.finditer(r'(?<!Supplementary )Figure (\d+)',text):assert 1<=int(m[1])<=5
    for m in re.finditer(r'Supplementary Figure S(\d+)',text):assert 1<=int(m[1])<=11
    assert 'Figure 8' not in text and 'five of 57 crew histories' in text


def test_packets_have_the_correct_five_and_eleven_page_counts():
    for name,n in [('MAIN_WITH_CAPTIONS.pdf',5),('SUPPLEMENT_PROPOSAL_WITH_CAPTIONS.pdf',11)]:
        with fitz.open(a.DEST/'IJDRS'/name) as doc:assert len(doc)==n
    data=json.loads((a.DEST/'qa/IJDRS_PACKET_REGISTRY.json').read_text())
    assert [r['identity'] for r in data['main']]==a.PRIMARY


def test_optional_svg_is_never_delivered_after_a_failed_appearance_gate():
    qa=json.loads((a.DEST/'qa/SVG_EXAMPLE_QA.json').read_text())
    assert qa['raster_objects']==0 and qa['text_is_outlined'] and not qa['fully_editable_text']
    approved=qa['mean_absolute_rgb_delta_600dpi']<=1 and qa['fraction_pixels_delta_gt20']<=.005
    assert qa['approved_for_production']==approved
    if approved:
        assert a.sha((ROOT/qa['svg']).read_bytes())==qa['sha256']
        assert '<image' not in (ROOT/qa['svg']).read_text(encoding='utf-8')
    else:
        assert qa['svg'] is None and qa['sha256'] is None
        assert not (a.DEST/'universal/vector_example/strategy_performance.svg').exists()


def test_no_unverified_journal_guarantees_or_master_deletion():
    profiles=json.loads((a.DEST/'EXPORT_PROFILES.json').read_text())
    assert profiles['primary_target']=='International Journal of Disaster Risk Science (Springer Nature)'
    assert not profiles['profiles']['ijdrs_mixed_600']['portal_certified']
    assert not profiles['profiles']['requested_line_1200']['automatic_bulk_generation']
    changed=subprocess.check_output(['git','diff','--name-only',a.BASE],cwd=ROOT,text=True).splitlines()
    assert all(x=='.gitattributes' or x.startswith(('src/la_grid/plotting/publication_artwork.py',
        'src/la_grid/plotting/publication_caption_definitions.py',
        'tests/test_publication_artwork_20261111.py','results/publication_artwork_20261111/')) for x in changed)
