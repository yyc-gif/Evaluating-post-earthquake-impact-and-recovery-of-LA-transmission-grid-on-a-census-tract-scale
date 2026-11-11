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
            assert qa['figure1_updated_with_method_process_panel']
            assert qa['figure1_no_downstream_result_plot_in_stage4']
            assert qa['figure1_stage4_audit']['full_width_stage4']
            assert all(r['pixel_identical'] for r in
                       qa['figure1_stage4_audit']['top_modules_unscaled_and_preserved'])
        elif record['final_name'] in {'Supplement/FigS05.pdf','Supplement/FigS05.png'}:
            assert current!=expected
            qa=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
            assert qa['s5_vulnerability_plot_audit']['four_policies_in_all_three_panels']
            assert qa['s5_vulnerability_plot_audit']['no_recovery_model_or_schedule_rerun']
        elif record['final_name'] in {'Main/Fig08.pdf','Main/Fig08.png'}:
            assert current!=expected
            qa=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
            assert qa['figure8_separate_map_legends_updated']
            if record['final_name'].endswith('.pdf'):
                with fitz.open(stream=current,filetype='pdf') as page_doc:
                    page=page_doc[0]
                    text=clean_pdf_text(page.get_text())
                    assert text.count('N/A (16)')==1
                    assert 'Outlined: Q4 + deficit ≥38.4 h' in text
                    drawings=page.get_drawings()
                    assert sum(1 for d in drawings if fitz.Rect(20,365,259,600).intersects(d['rect']))>1000
                    assert sum(1 for d in drawings if fitz.Rect(260,365,515,600).intersects(d['rect']))>1000
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

def test_figure1_stage4_is_implementation_derived_method_flow():
    import inspect
    import figure_presentation
    import build_current_suite_p2

    panel_pdf,panel_png,panel_audit=builder.workflow_figure.build_stage4_process_panel()
    source_pdf=builder.source(builder.SOURCE+'/Main/Fig01.pdf')
    figure8_row=next(r for r in builder.u.csv_rows(
        builder.source(builder.SOURCE+'/FIGURE_MANIFEST.csv'))
        if r['final_name']=='Main/Fig07.pdf')
    figure8_source=builder.source(figure8_row['current_source_file'])
    colors=json.loads(builder.source(builder.SOURCE+'/CURRENT_CLUSTER_PALETTE.json'))['colors']
    community_map=figure_presentation.figure8_shared_map_legend(
        figure8_source,colors)[0]
    expected_pdf,audit=figure_presentation.restoration_workflow(
        source_pdf,panel_pdf,panel_audit,community_typology_pdf=community_map)
    with fitz.open(stream=expected_pdf,filetype='pdf') as doc:
        expected_png=doc[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        expected_preview=doc[0].get_pixmap(dpi=150,alpha=False).tobytes('png')
        final_text=clean_pdf_text(doc[0].get_text())
    with fitz.open(stream=panel_pdf,filetype='pdf') as panel:
        stage_text=clean_pdf_text(panel[0].get_text())
    assert (SUITE/'Main/Fig01.pdf').read_bytes()==expected_pdf
    assert (SUITE/'Main/Fig01.png').read_bytes()==expected_png
    assert (SUITE/'Page_Previews/Fig01.png').read_bytes()==expected_preview
    assert audit['full_width_stage4']
    assert audit['stage4_map_footprint_qa']['within_10_percent_each_dimension']
    assert audit['stage5_reflowed_from_original_vector_result_graphics']
    assert audit['stage5_legacy_layer_is_clipped_and_covered_by_current_panels']
    assert all(r['pixel_identical'] for r in audit['top_modules_unscaled_and_preserved'])
    assert audit['no_recovery_curves_or_downstream_outcomes']
    for phrase in ('Priority Rules', 'Impact-first example', 'Tract population',
                   'Repair Scheduling', 'Crew 5', 'Crew 9', 'Crew 12',
                   'Crew 14', 'Crew 17', 'Travel', 'Repair', '60 h',
                   'Completion Events', 'complete', 'Crew', 'released',
                   'Station', 'restored', 'Tract', 'service'):
        assert phrase in stage_text
    for retired in ('Map numbers:', 'Blue-gray fill', '2 of 57 crews',
                    'saved event excerpt', 'Recorded task finish',
                    'source gate', 'Stage 3 tract service'):
        assert retired not in stage_text
    for phrase in ('Population-weighted service availability',
                   'T80: time to 80% modeled availability',
                   'Community recovery types'):
        assert phrase in final_text
    with fitz.open(stream=expected_pdf,filetype='pdf') as doc:
        assert abs(doc[0].rect.width*25.4/72-185.0)<0.02
        assert abs(doc[0].rect.height*25.4/72-265.2889)<0.02
    assert panel_audit['uses_priority_map'] and panel_audit['uses_saved_schedule']
    assert panel_audit['no_fabricated_task_events']
    assert panel_audit['schedule_archive_sha256'] == panel_audit['schedule_manifest']['npz_sha256']
    assert panel_audit['crews_in_model'] == 57
    assert panel_audit['crews_shown'] == [5, 9, 12, 14, 17]
    assert panel_audit['schedule_axis_hours'] == [0, 15, 30, 45, 60]
    assert panel_audit['schedule_axis_max_hr'] == 60
    assert panel_audit['body_font_pt'] >= 7.5
    assert panel_audit['rank_marker_font_pt'] == 8.0
    assert panel_audit['schedule_rank_label_pt'] is None
    assert panel_audit['map_ranks_are_full_station_priority_ranks']
    assert panel_audit['gantt_dispatch_numbers_removed_to_avoid_rank_ambiguity']
    assert panel_audit['minimum_panel_text_pt'] >= 7.5
    assert panel_audit['source_map_rank_text_removed_before_relabel']
    assert abs(max(e['completion_hr'] for e in panel_audit['plotted_task_events'])
               - 57.75698225552637) < 1e-9
    assert len(panel_audit['plotted_task_events']) == 12
    assert panel_audit['priority_map_palette'] == [
        '#F3F4F1', '#DFE7E1', '#BED2C8', '#91B4A5', '#659587']
    assert all(e['travel_hr'] > 0 and e['repair_hr'] > 0
               for e in panel_audit['plotted_task_events'])
    for phrase in ('availability curves','Impact-first service-availability',
                   'T80','cumulative service loss'):
        assert phrase.lower() not in stage_text.lower()
    generator_source=inspect.getsource(builder.main)
    assert 'supplementary5_four_policy(s5_plot_data)' not in generator_source
    assert "Supplement/FigS05.pdf').read_bytes()" in generator_source
    assert 'build_stage4_process_panel' in generator_source
    assert 'restoration_workflow(' in generator_source
    builder_module=inspect.getsource(builder)
    assert 'FIG1_CURVE_SOURCE' not in builder_module
    assert 'FIG1_WORKFLOW_COMMIT' not in builder_module
    assert "source(FIG1_CURVE_SOURCE" not in generator_source
    assert "source(FIG1_WORKFLOW_DIR" not in generator_source
    assert 'verify_restoration_workflow_artifact' not in generator_source
    assert 'show_pdf_page' in inspect.getsource(figure_presentation.restoration_workflow)
    p2_builder_source=inspect.getsource(build_current_suite_p2.main)
    assert 'build_stage4_process_panel' in p2_builder_source
    assert 'restoration_workflow(' in p2_builder_source
    assert 'recovery_curves_all_system.csv' not in p2_builder_source
    assert 'ea692f4dd6d1763a91b4b8f5c11e45ce6a8a1f15' not in p2_builder_source
    p2_caption=build_current_suite_p2.captions()[0][1]
    assert 'full station priority ranks' in p2_caption
    assert 'separate parallel-repair reference' in p2_caption
    captions=(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    fig1=captions.split('## Figure 1.',1)[1].split('\n## ',1)[0]
    for phrase in ('Impact-first example', 'five crew histories',
                   '2pc50/C57_D1 evaluation realization 0', '5 of 57 crews',
                   'saved directed travel and damage-state-specific repair intervals',
                   'crews are released',
                   'Unconstrained is a separate parallel-repair reference',
                   'population-weighted service availability',
                   'T80 (time to 80% modeled service availability)',
                   'community recovery types'):
        assert phrase in fig1
    manifest=rows(SUITE/'FIGURE_MANIFEST.csv')
    row=next(r for r in manifest if r['final_name']=='Main/Fig01.pdf')
    assert row['stage4_generator']==builder.WORKFLOW_GENERATOR
    assert row['stage4_panel_sha256']==hashlib.sha256(panel_pdf).hexdigest()
    assert row['stage4_scheduler_source_sha256']==hashlib.sha256(
        (ROOT/builder.SCHEDULER_SOURCE).read_bytes()).hexdigest()
    assert row['stage4_ga_source_sha256']==hashlib.sha256(
        (ROOT/builder.GA_SOURCE).read_bytes()).hexdigest()
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as packet:
        assert len(packet)==16
        packet_text=clean_pdf_text(packet[0].get_text())
        assert 'Figure 1. Analytical framework' in packet_text
        assert 'Impact-first example' in packet_text


def test_supplementary_s5_remains_unchanged_by_figure1_correction():
    baseline='8d7d458b9e85bb72c4c25cd927815137bd916bbc'
    for rel in ('results/figure_review_s6_main4_20261107/Supplement/FigS05.pdf',
                'results/figure_review_s6_main4_20261107/Supplement/FigS05.png',
                'results/figure_review_s6_main4_20261107/Page_Previews/FigS05.png'):
        assert (ROOT/rel).read_bytes()==builder.u.payload(baseline,rel)


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
        spans=[s for b in page.get_text('dict')['blocks'] for line in b.get('lines',[])
               for s in line['spans']]
        def span_for(label):
            found=[s for s in spans if clean_pdf_text(s['text'])==label
                   and (label.startswith('Outlined:') or s['bbox'][1]>600)]
            assert len(found)==1,(label,len(found))
            return found[0]
        c_entries=[span_for(label) for label in ('C1','C2','C3','N/A (16)')]
        d_entry=span_for('Outlined: Q4 + deficit ≥38.4 h')
        legend_y=[s['bbox'][3] for s in c_entries+[d_entry]]
        assert max(legend_y)-min(legend_y)<0.02
        assert max(s['bbox'][2] for s in c_entries)<d_entry['bbox'][0]
        drawings=page.get_drawings()
        assert sum(1 for d in drawings if fitz.Rect(20,365,259,600).intersects(d['rect']))>1000
        assert sum(1 for d in drawings if fitz.Rect(260,365,515,600).intersects(d['rect']))>1000
    caption=(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    assert 'frozen FEMA NRI v1.19 SOVI quartile Q4' in caption
    assert '38.38135467381475 equivalent full-service-deficit hours' in caption
    assert 'positive-population cohort 75th percentile' in caption
    assert 'cohort P75' not in caption
    index=rows(MIRROR/'FIGURE_INDEX.csv')
    fig8=next(row for row in index if row['figure_number']=='Fig08')
    assert 'separate aligned legends' in fig8['notes']
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as packet:
        assert 'Outlined: Q4 + deficit ≥38.4 h' in clean_pdf_text(packet[7].get_text())

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
    assert q['figure1_updated_with_method_process_panel']
    assert q['figure1_no_downstream_result_plot_in_stage4']
    assert 'figure1_curve_source_sha256' not in q
    assert q['figure1_stage4_generator_audit']['no_recovery_curves_or_downstream_outcomes']
    assert q['unaffected_13_artwork_pairs_byte_identical']
    assert q['figure8_separate_map_legends_updated']
    assert q['dynamic_full_minus_fixed_identity_max_abs_error']<1e-12
    assert q['static_station_records']==92 and q['static_core_source_records']==14
    for path,record in json.loads((SUITE/'QA/SOURCE_IDENTITIES.json').read_text())['source_files'].items():
        if record.get('locally_executed_source'):
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==record['sha256']
        elif path.startswith('generated/'):
            artifact=path.rsplit('/',1)[-1]
            assert hashlib.sha256((SUITE/'QA'/artifact).read_bytes()).hexdigest()==record['sha256']
        elif not path.startswith('derived/'):
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
