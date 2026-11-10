"""Review-only figure promotion preserves the source suite and S6 content."""
import csv
import hashlib
import importlib.util
import json
import re
import sys
import subprocess
from pathlib import Path

import fitz

ROOT=Path(__file__).resolve().parents[1]
SUITE=ROOT/'results/figure_review_s6_main4_20261107'
MIRROR=ROOT/'results/figures_s6_main4_20261107'
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
spec=importlib.util.spec_from_file_location('promotion',ROOT/'src/la_grid/plotting/build_s6_main4_review.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def clean_pdf_text(text):
    return ' '.join(text.replace('\xa0',' ').replace('\xad','-').replace('\ufffd','-').split())

def test_exact_numbering_and_inventory():
    manifest=rows(SUITE/'FIGURE_MANIFEST.csv')
    assert len(manifest)==32
    assert {r['final_name'] for r in manifest}=={s+'.'+e for s in builder.NEW for e in ['pdf','png']}
    assert len(list((SUITE/'Main').glob('*.pdf')))==8
    assert len(list((SUITE/'Supplement').glob('*.pdf')))==8
    assert builder.MAPPING['Supplement/FigS06']=='Main/Fig04'
    assert builder.MAPPING['Main/Fig07']=='Main/Fig08'
    assert builder.MAPPING['Supplement/FigS09']=='Supplement/FigS08'
    assert set(builder.MAPPING.values())==set(builder.NEW)

def test_every_artwork_and_mirror_matches_actual_source_bytes():
    for record in rows(SUITE/'FIGURE_MANIFEST.csv'):
        expected=builder.source(record['source_file'])
        current=(ROOT/record['current_source_file']).read_bytes()
        mirror=(ROOT/record['mirror_file']).read_bytes()
        assert mirror==current
        assert hashlib.sha256(current).hexdigest()==record['sha256']
        if record['final_name'] in {'Main/Fig01.pdf','Main/Fig01.png'}:
            assert current!=expected
            qa=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
            assert qa['figure1_workflow_generated_artifact_reused']
            assert qa['figure1_stage4_audit']['workflow_generation_record_verified']
        elif record['final_name'] in {'Supplement/FigS05.pdf','Supplement/FigS05.png'}:
            assert current!=expected
            qa=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
            assert qa['s5_vulnerability_plot_audit']['four_policies_in_all_three_panels']
            assert qa['s5_vulnerability_plot_audit']['no_recovery_model_or_schedule_rerun']
        elif record['final_name'] in {'Main/Fig08.pdf','Main/Fig08.png'}:
            assert current!=expected
            qa=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
            assert qa['figure8_separate_map_legends_updated']
            assert qa['figure8_legend_audit']['bivariate_colorbar_and_tract_geometry_unchanged']
        else:
            assert current==expected
    index=rows(MIRROR/'FIGURE_INDEX.csv')
    assert len(index)==32
    assert {r['figure_number'] for r in index}=={Path(s).name for s in builder.NEW}
    for row in index:assert digest(MIRROR/row['file'])==row['sha256']==row['sha256_or_lfs_oid']

def test_preservation_registry_compares_frozen_inputs_to_actual_outputs():
    records=json.loads((SUITE/'QA/ARTWORK_PRESERVATION.json').read_text(encoding='utf-8'))
    changed={'Main/Fig01','Main/Fig07','Supplement/FigS05'}
    assert len(records)==32
    for row in records:
        assert row['output_sha256']==digest(SUITE/(row['new_figure']+'.'+row['format']))
        assert row['byte_identical']==(row['source_sha256']==row['output_sha256'])
        if row['previous_figure'] in changed:
            assert not row['byte_identical']
        else:
            assert row['byte_identical']

def test_figure1_uses_hash_verified_workflow_generated_curves():
    import inspect
    import figure_presentation
    import build_current_suite_p2

    artifact_commit=builder.WORKFLOW_ARTIFACT_COMMIT
    pdf=builder.u.payload(artifact_commit,builder.WORKFLOW_ARTIFACT_PDF)
    png=builder.u.payload(artifact_commit,builder.WORKFLOW_ARTIFACT_PNG)
    preview=builder.u.payload(artifact_commit,builder.WORKFLOW_ARTIFACT_PREVIEW)
    curves=builder.source(builder.WORKFLOW_CURVES)
    record=json.loads(builder.u.payload(artifact_commit,builder.WORKFLOW_GENERATION_RECORD))
    checked_pdf,checked_png,checked_preview,audit=(
        figure_presentation.verify_restoration_workflow_artifact(
            curves,pdf,png,preview,record))
    assert (SUITE/'Main/Fig01.pdf').read_bytes()==checked_pdf
    assert (SUITE/'Main/Fig01.png').read_bytes()==checked_png
    assert (SUITE/'Page_Previews/Fig01.png').read_bytes()==checked_preview
    assert audit['source_rows']==9601
    assert audit['points_plotted_per_series']==2001
    assert audit['series_columns']=={
        'Unconstrained':'2pc50 | S3_Mean | Population',
        'Impact-first':'2pc50 | Impact population first | Population'}
    assert audit['outside_stage4_pixels_identical']
    generator_source=inspect.getsource(builder.main)
    assert 'verify_restoration_workflow_artifact' in generator_source
    assert 'restoration_workflow(' not in generator_source
    assert 'draw_rect' not in inspect.getsource(figure_presentation.restoration_workflow)
    p2_builder_source=inspect.getsource(build_current_suite_p2.main)
    assert 'verify_restoration_workflow_artifact' in p2_builder_source
    assert "source(FIG1_CURVE_SOURCE,CURRENT_SUITE_BASE)" in p2_builder_source
    assert 'restoration_workflow(original_f1)' not in p2_builder_source
    p2_caption=build_current_suite_p2.captions()[0][1]
    assert 'saved Unconstrained and Impact-first service-availability trajectories' in p2_caption
    captions=(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    fig1=captions.split('## Figure 1.',1)[1].split('\n## ',1)[0]
    for phrase in ('saved population-weighted service-availability trajectories',
                   'Unconstrained and Impact-first','finite crews','sampled repair durations',
                   'directed travel','At each completion','source-gated tract service',
                   'not averaged schedules'):
        assert phrase in fig1
    manifest=rows(SUITE/'FIGURE_MANIFEST.csv')
    row=next(r for r in manifest if r['final_name']=='Main/Fig01.pdf')
    assert row['workflow_artifact_commit']==artifact_commit
    assert row['workflow_artifact_sha256']==hashlib.sha256(pdf).hexdigest()
    assert row['workflow_curve_source_sha256']==hashlib.sha256(curves).hexdigest()


def test_s5_actual_pdf_png_packet_and_visual_centering():
    from PIL import Image
    import numpy as np
    import figure_presentation

    pdf_path=SUITE/'Supplement/FigS05.pdf'
    png_path=SUITE/'Supplement/FigS05.png'
    preview_path=SUITE/'Page_Previews/FigS05.png'
    with fitz.open(pdf_path) as doc:
        page=doc[0]
        assert abs(page.rect.width*25.4/72-185.0)<.01
        assert abs(page.rect.height*25.4/72-145.0)<.01
        text=clean_pdf_text(page.get_text())
        for value in ('Impact-first','Hospital-first','Degree-first','Vulnerability-first',
                      'A. Mapping-weight cutoff','B. Source-connectivity gate',
                      'C. Functionality threshold','0% cutoff','1% cutoff','0.05','0.75'):
            assert value in text
        spans=[s for block in page.get_text('dict')['blocks']
               for line in block.get('lines',[]) for s in line.get('spans',[])
               if s['text'].strip()]
        assert min(s['size'] for s in spans)>=7.0
        assert {s['font'] for s in spans}=={'ArialMT','Arial-BoldMT'}
        assert page.get_pixmap(dpi=600,alpha=False).tobytes('png')==png_path.read_bytes()
        assert page.get_pixmap(dpi=150,alpha=False).tobytes('png')==preview_path.read_bytes()

    image=np.asarray(Image.open(png_path).convert('RGB'))
    ink=np.any(image<248,axis=2)
    ys,xs=np.where(ink)
    left=185.0*xs.min()/image.shape[1]
    right=185.0*(image.shape[1]-1-xs.max())/image.shape[1]
    assert abs(left-right)<=1.0, (left,right)

    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as packet, \
         fitz.open(pdf_path) as art:
        assert len(packet)==16
        page=packet[12]
        rect=fitz.Rect(0,0,art[0].rect.width,art[0].rect.height)
        assert page.get_pixmap(dpi=150,clip=rect,alpha=False).samples==art[0].get_pixmap(dpi=150,alpha=False).samples
        assert all(value in clean_pdf_text(page.get_text()) for value in (
            'A. Mapping-weight cutoff','B. Source-connectivity gate',
            'C. Functionality threshold'))

    manifest=rows(SUITE/'FIGURE_MANIFEST.csv')
    rec=next(r for r in manifest if r['final_name']=='Supplement/FigS05.pdf')
    assert digest(pdf_path)==rec['sha256']
    assert (ROOT/rec['mirror_file']).read_bytes()==pdf_path.read_bytes()
    audit=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
    margins=audit['s5_vulnerability_plot_audit']['complete_visible_composition_centering']
    assert audit['s5_compact_height_mm']==145.0
    assert abs(margins['after_visible_left_mm']-margins['after_visible_right_mm'])<.15
    assert margins['includes_strategy_labels_axis_titles_and_legends']
    raster=audit['s5_vulnerability_plot_audit']['independent_600dpi_png_visible_bounds']
    assert abs(raster['visible_left_mm']-left)<.02
    assert abs(raster['visible_right_mm']-right)<.02

    plot_data=(SUITE/'QA/S5_VULNERABILITY_PLOT_DATA.json').read_bytes()
    series=json.loads(plot_data)['series']
    assert len(series)==20
    assert {panel:sum(row['panel']==panel for row in series)
            for panel in ('A','B','C')}=={'A':8,'B':4,'C':8}
    for panel in ('A','B','C'):
        assert {row['policy'] for row in series if row['panel']==panel}=={
            'impact-first','hospital-first','degree-first','vulnerability-first'}
    replay_pdf,replay_png,replay_preview,replay_audit=(
        figure_presentation.supplementary5_four_policy(plot_data))
    assert replay_pdf==pdf_path.read_bytes()
    assert replay_png==png_path.read_bytes()
    assert replay_preview==preview_path.read_bytes()
    assert replay_audit['source_plot_data_sha256']==audit['s5_vulnerability_plot_data_sha256']

    plot_rel='results/figure_review_s6_main4_20261107/QA/S5_VULNERABILITY_PLOT_DATA.json'
    committed=json.loads(subprocess.check_output(['git','show',
        '5e10f48bbc2b8dc873cc9bda4ad575f8d683cd41:'+plot_rel],cwd=ROOT))
    current=json.loads((ROOT/plot_rel).read_text(encoding='utf-8'))
    assert current==committed

def test_all_four_promoted_panels_and_vector_contents_are_unchanged():
    raw=builder.source(builder.SOURCE+'/Supplement/FigS06.pdf')
    with fitz.open(stream=raw,filetype='pdf') as old,fitz.open(SUITE/'Main/Fig04.pdf') as new:
        assert old[0].rect==new[0].rect
        assert old[0].get_text('rawdict')==new[0].get_text('rawdict')
        # Compare original vector operators directly, avoiding expansion of
        # tens of thousands of repeated map paths into Python drawing objects.
        assert old.xref_length()==new.xref_length()
        for xref in range(1,old.xref_length()):
            assert old.xref_object(xref)==new.xref_object(xref)
            if old.xref_is_stream(xref):assert old.xref_stream(xref)==new.xref_stream(xref)
        assert old[0].get_images(full=True)==new[0].get_images(full=True)
        text=new[0].get_text().replace('\xa0',' ')
        for label in ['A. Source connection: full network and fixed path',
                      'B. Additional source connection from alternate routes',
                      'C. Source access from a functional station',
                      'D. Reliability gain from alternate routes']:
            assert label in text
        for strategy in ['Impact-first','Hospital-first','Degree-first','Vulnerability-first','Betweenness-first','Random','Unconstrained']:
            assert strategy in text
        vector_qa=json.loads((ROOT/'docs/reproducibility/s6_main4_promotion_20261107/VERIFICATION.json').read_text())
        assert vector_qa['figure4_vector_and_fonts']['vector_drawings']>100
        assert new[0].get_pixmap(dpi=100).samples==old[0].get_pixmap(dpi=100).samples

def test_packet_sequence_captions_and_native_scale():
    for name,count in [('ALL_MAIN_FIGURES.pdf',8),('ALL_SUPPLEMENT_FIGURES.pdf',8),('ALL_FIGURES_WITH_CAPTIONS.pdf',16)]:
        with fitz.open(SUITE/name) as doc:assert len(doc)==count
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as doc:
        for i,stem in enumerate(builder.NEW):
            assert builder.label(stem)+'.' in doc[i].get_text()
            with fitz.open(SUITE/(stem+'.pdf')) as art:
                assert doc[i].rect.width==art[0].rect.width
                assert doc[i].rect.height>art[0].rect.height
        with fitz.open(SUITE/'Main/Fig04.pdf') as art:
            rect=art[0].rect
            assert doc[3].get_pixmap(dpi=100,clip=rect).samples==art[0].get_pixmap(dpi=100).samples
            assert 'fragility-based station diagnostics' in doc[3].get_text()
            assert 'These topological measures are not delivered electricity' in ' '.join(doc[3].get_text().split())
        assert 'Outlined: Q4 + deficit ≥38.4 h' in clean_pdf_text(doc[7].get_text())

def test_figure8_panel_legends_are_separate_aligned_and_explained_in_caption():
    path=SUITE/'Main/Fig08.pdf'
    with fitz.open(path) as doc:
        page=doc[0]
        text=clean_pdf_text(page.get_text())
        assert text.count('N/A (16)')==1
        assert 'P75' not in text
        assert 'Outlined: Q4 + deficit ≥38.4 h' in text
        rule=[s for b in page.get_text('dict')['blocks'] for line in b.get('lines',[])
              for s in line['spans'] if clean_pdf_text(s['text']).startswith('Outlined: Q4')]
        assert len(rule)==1 and rule[0]['size']==7.5
        audit=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))['figure8_legend_audit']
        assert audit['old_NA_entries']==2 and audit['new_NA_entries']==1
        assert audit['C_and_D_legends_separate_and_aligned']
        assert audit['all_legend_entries_share_baseline']
        assert len({item['baseline'] for item in audit['shared_legend_positions']})==1
        assert audit['screening_symbol']=='thin gray line'
        assert clean_pdf_text(audit['screening_rule_text']) in text
        groups={item['group'] for item in audit['shared_legend_positions']}
        assert groups=={'C','D'}
        assert max(x['x1'] for x in audit['shared_legend_positions'] if x['group']=='C')<254
        assert min(x['x0'] for x in audit['shared_legend_positions'] if x['group']=='D')>264
        assert audit['bivariate_colorbar_and_tract_geometry_unchanged']
    caption=(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    assert 'frozen FEMA NRI v1.19 SOVI quartile Q4' in caption
    assert '38.38135467381475 equivalent full-service-deficit hours' in caption
    assert 'positive-population cohort 75th percentile' in caption
    assert 'cohort P75' not in caption
    index=rows(MIRROR/'FIGURE_INDEX.csv')
    fig8=next(row for row in index if row['figure_number']=='Fig08')
    assert 'separate aligned legends' in fig8['notes']
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as packet:
        assert clean_pdf_text(audit['screening_rule_text']) in clean_pdf_text(packet[7].get_text())

def test_caption_references_and_simultaneous_renumbering():
    text=(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    assert len(re.findall(r'^## ',text,re.M))==16
    assert 'Figures 5-7 and Supplementary Figure S8' in text
    assert 'Supplementary Figure S9' not in text
    assert builder.references('Figure 4 and Figure 7; Supplementary Figure S6; Figures 4-6; Supplementary Figure S9')==(
        'Figure 5 and Figure 8; Figure 4; Figures 5-7; Supplementary Figure S8')
    for n in re.findall(r'Supplementary Figure S(\d+)',text):assert 1<=int(n)<=8
    for n in re.findall(r'(?<!Supplementary )Figure (\d+)',text):assert 1<=int(n)<=8
    assert (SUITE/'MANUSCRIPT_INTEGRATION.md').is_file()
    assert 'immediately before Section 4.3' in (SUITE/'MANUSCRIPT_INTEGRATION.md').read_text()

def test_palette_and_source_science_preserved():
    expected=json.loads(builder.source(builder.SOURCE+'/CURRENT_CLUSTER_PALETTE.json'))
    actual=json.loads((SUITE/'CURRENT_CLUSTER_PALETTE.json').read_text(encoding='utf-8'))
    expected={k.replace('Figure7_','Figure8_'):v for k,v in expected.items()}
    expected['screening_rule']='Highest social-vulnerability quartile and five-policy service deficit >=38.38135467381475 equivalent hours (cohort upper quartile)'
    expected['screening_legend_label']='Outlined: Q4 + deficit ≥38.4 h'
    assert expected==actual
    q=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
    assert q['all_four_promoted_panels_preserved']
    assert q['figure1_workflow_generated_artifact_reused']
    assert q['figure1_curve_source_sha256']=='b4a0889e12ed855f1f681b73dbb429306f513585fd00afe058480e6aa5a43922'
    assert q['unaffected_13_artwork_pairs_byte_identical']
    assert q['figure8_separate_map_legends_updated']
    assert q['dynamic_full_minus_fixed_identity_max_abs_error']<1e-12
    assert q['static_station_records']==92 and q['static_core_source_records']==14
    for path,record in json.loads((SUITE/'QA/SOURCE_IDENTITIES.json').read_text())['source_files'].items():
        if not path.startswith('derived/'):
            assert hashlib.sha256(builder.u.payload(record['commit'],path)).hexdigest()==record['sha256']

def test_s5_four_policy_sensitivity_contains_verified_vulnerability_first():
    with fitz.open(SUITE/'Supplement/FigS05.pdf') as doc:
        text=clean_pdf_text(doc[0].get_text())
        for value in ('A. Mapping-weight cutoff','B. Source-connectivity gate',
                      'C. Functionality threshold','Impact-first','Hospital-first',
                      'Degree-first','Vulnerability-first','0% cutoff','1% cutoff',
                      'Gate off minus baseline burden (h)','0.05','0.75'):
            assert value in text
        assert len(doc[0].get_drawings())>100
    qa=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
    audit=json.loads((SUITE/'QA/S5_VULNERABILITY_ARCHIVE_AUDIT.json').read_text(encoding='utf-8'))
    assert audit['status']=='PASS_FROZEN_EVENT_STATE_REANALYSIS'
    assert audit['condition']['physical_realizations_per_policy']==1000
    assert audit['frozen_identity']['all_1000_realization_ids_and_physical_DS_duration_hashes_match_across_policies']
    baseline_errors=audit['frozen_identity']['saved_baseline_event_integral_crosschecks_max_abs_error_h']
    assert max(baseline_errors.values())<1e-12
    assert audit['frozen_identity']['source_only_integral_identity_max_abs_error_h']['vulnerability-first']<1e-12
    assert qa['s5_vulnerability_plot_data_sha256']==audit['plot_data_sha256']
    assert qa['s5_vulnerability_plot_audit']['four_policies_in_all_three_panels']

def test_source_suite_files_are_not_overwritten():
    manifest=builder.u.csv_rows(builder.source(builder.SOURCE+'/FIGURE_MANIFEST.csv'))
    for row in manifest:
        current=builder.source(row['current_source_file'])
        mirror=builder.source(row['mirror_file'])
        assert hashlib.sha256(current).hexdigest()==row['sha256']
        assert hashlib.sha256(mirror).hexdigest()==row['sha256']
        if (ROOT/row['current_source_file']).is_file():
            assert digest(ROOT/row['current_source_file'])==row['sha256']
        if (ROOT/row['mirror_file']).is_file():
            assert digest(ROOT/row['mirror_file'])==row['sha256']
    source_caption=builder.SOURCE+'/MANUSCRIPT_FACING_CAPTIONS.md'
    committed=subprocess.check_output(['git','show','5e10f48bbc2b8dc873cc9bda4ad575f8d683cd41:'+source_caption],cwd=ROOT)
    assert committed==builder.source(source_caption)


def test_local_renderer_implementation_hashes_are_recorded():
    impl=json.loads((SUITE/'QA/SOURCE_IDENTITIES.json').read_text(encoding='utf-8'))['implementation_files']
    for rel,record in impl.items():
        assert digest(ROOT/rel)==record['sha256']
