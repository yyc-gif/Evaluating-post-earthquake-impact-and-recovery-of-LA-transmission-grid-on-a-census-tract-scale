"""Promote the complete saved S6 to main Figure 4 in an isolated review suite.

Copies hash-verified artwork unchanged. No scientific model or plot is rerun.
"""
from pathlib import Path
import argparse
import io
import json
import re

import fitz
import numpy as np
import pandas as pd
from reportlab import rl_config

import consolidate_current_figure_suite as u
import figure_presentation
import make_methodology_workflow_figure as workflow_figure
from short_current_captions_20261013 import brief_caption_page

ROOT=u.ROOT
BASE='75cd19d4a0249d006efa00d4532762d0ee406c5a'
WORKFLOW_GENERATOR='src/la_grid/plotting/make_methodology_workflow_figure.py'
SCHEDULER_SOURCE='src/la_grid/revision/r1_realization_scheduling.py'
GA_SOURCE='src/la_grid/revision/r1_ga_revision.py'
SOURCE='results/figure_review_rq_aligned_20261101'
SOURCE_MIRROR='results/figures_rq_aligned_20261101'
DEST=ROOT/'results/figure_review_s6_main4_20261107'
MIRROR=ROOT/'results/figures_s6_main4_20261107'
GEN='src/la_grid/plotting/build_s6_main4_review.py'
OLD=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in range(1,10)]
ORDER=OLD[:3]+['Supplement/FigS06']+OLD[3:7]+[s for s in OLD[7:] if s!='Supplement/FigS06']
NEW=[f'Main/Fig{i:02d}' for i in range(1,9)]+[f'Supplement/FigS{i:02d}' for i in range(1,9)]
MAPPING=dict(zip(ORDER,NEW))
TITLE='Figure 4. Network-dependent source connectivity during recovery'
CAPTION=(
    '(A) Recovery of population-dependency-weighted joint functionality and source connection through the full network '
    '(solid) or a fixed precomputed path (dashed). (B) Their difference shows restoration-sequence-dependent '
    'alternative-route support. (C) Station source access conditional on station functionality; (D) additional '
    'conditional reliability beyond the fixed path. Triangles mark Core sources. A/B are dynamic recovery '
    'comparisons; C/D are fragility-based station diagnostics. These topological measures are not delivered electricity.'
)
INPUTS=[
    'docs/reproducibility/SOURCE_RELIABILITY_FIGURE_NOTES.md',
    'results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv',
    'results/diagnostics/SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv',
    'src/la_grid/plotting/render_source_reliability_figures.py',
    'src/la_grid/plotting/selected_strategy_source_travel.py',
    'src/la_grid/plotting/selected_strategy_panels.py',
    'src/la_grid/plotting/build_meeting_figure_collection.py',
    'src/la_grid/plotting/figure_presentation.py',
    'src/la_grid/plotting/build_current_suite_p2.py',
    SOURCE+'/CURRENT_CLUSTER_PALETTE.json',
]

def source(path):
    return u.payload(BASE,path)

def label(stem):
    name=Path(stem).name
    return f'Supplementary Figure S{int(name[4:])}' if name.startswith('FigS') else f'Figure {int(name[3:])}'

def references(text):
    """Simultaneous mapping avoids cascading old 4->5->6 replacements."""
    def main(match):
        prefix=match[1]
        nums=re.sub(r'\d+',lambda m:str(int(m[0])+1 if int(m[0])>=4 else int(m[0])),match[2])
        return prefix+nums
    text=re.sub(r'(?<!Supplementary )(Figures?\s+)(\d+(?:\s*(?:-|\u2013|,|and)\s*\d+)*)',main,text)
    def supp(match):
        n=int(match[1])
        return 'Figure 4' if n==6 else 'Supplementary Figure S'+str(n-1 if n>6 else n)
    return re.sub(r'Supplementary Figure S(\d+)\b',supp,text)

def main(output_dir=None,mirror_dir=None):
    dest=Path(output_dir).resolve() if output_dir else DEST
    mirror=Path(mirror_dir).resolve() if mirror_dir else MIRROR
    protected=[ROOT/SOURCE,ROOT/SOURCE_MIRROR]
    for path in (dest,mirror):
        assert not any(path==p or path.is_relative_to(p) for p in protected)
    manifest=u.csv_rows(source(SOURCE+'/FIGURE_MANIFEST.csv'))
    source_index=u.csv_rows(source(SOURCE_MIRROR+'/FIGURE_INDEX.csv'))
    old_caps=list(u.captions(source(SOURCE+'/MANUSCRIPT_FACING_CAPTIONS.md').decode('utf-8')).items())
    assert len(old_caps)==16
    caps={stem:old_caps[i] for i,stem in enumerate(OLD)}
    new_caps=[];rows=[];indices=[];preservation=[];page_rows=[];source_hashes={}
    for path in INPUTS:
        raw=source(path)
        source_hashes[path]={'commit':BASE,'sha256':u.digest(raw),'bytes':len(raw)}
    s5_plot_data_path=dest/'QA/S5_VULNERABILITY_PLOT_DATA.json'
    s5_audit_path=dest/'QA/S5_VULNERABILITY_ARCHIVE_AUDIT.json'
    if not s5_plot_data_path.is_file() or not s5_audit_path.is_file():
        raise FileNotFoundError('Run audit_s5_vulnerability_extension.py before the canonical figure build.')
    s5_plot_data=s5_plot_data_path.read_bytes()
    s5_audit=json.loads(s5_audit_path.read_text(encoding='utf-8'))
    assert s5_audit['status']=='PASS_FROZEN_EVENT_STATE_REANALYSIS'
    assert s5_audit['plot_data_sha256']==u.digest(s5_plot_data)
    source_hashes['derived/S5_VULNERABILITY_PLOT_DATA.json']={
        'commit':'generated from manifest-bound local frozen archive',
        'sha256':u.digest(s5_plot_data),'bytes':len(s5_plot_data)}
    dynamic=pd.read_csv(io.BytesIO(source(INPUTS[1])))
    station=pd.read_csv(io.BytesIO(source(INPUTS[2])),dtype={'station_id':str})
    palette_path=SOURCE+'/CURRENT_CLUSTER_PALETTE.json'
    palette_bytes=source(palette_path)
    palette=json.loads(palette_bytes)
    assert palette['colors']=={'1':'#3C9198','2':'#52699E','3':'#C69EBA'}
    source_figure1=source(SOURCE+'/Main/Fig01.pdf')
    stage4_panel_pdf,stage4_panel_png,stage4_generator_audit=(
        workflow_figure.build_stage4_process_panel())
    stage4_pdf,stage4_audit=figure_presentation.restoration_workflow(
        source_figure1,stage4_panel_pdf,stage4_generator_audit)
    stage4_audit['stage4_generator_audit']=stage4_generator_audit
    stage4_audit['starting_figure1_sha256']=u.digest(source_figure1)
    with fitz.open(stream=stage4_pdf,filetype='pdf') as figure1:
        stage4_png=figure1[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        stage4_preview=figure1[0].get_pixmap(dpi=150,alpha=False).tobytes('png')
    for path in (WORKFLOW_GENERATOR,SCHEDULER_SOURCE,GA_SOURCE):
        raw=(ROOT/path).read_bytes()
        source_hashes[path]={'commit':'local working tree at build time',
                             'sha256':u.digest(raw),'bytes':len(raw),
                             'locally_executed_source':True}
    source_hashes['generated/Fig01_Stage4_Method_Panel.pdf']={
        'commit':'generated by '+WORKFLOW_GENERATOR,
        'sha256':u.digest(stage4_panel_pdf),'bytes':len(stage4_panel_pdf)}
    source_hashes['generated/Fig01_Stage4_Method_Panel.png']={
        'commit':'generated by '+WORKFLOW_GENERATOR,
        'sha256':u.digest(stage4_panel_png),'bytes':len(stage4_panel_png)}
    u.write(dest/'QA/FIG01_STAGE4_METHOD_PANEL.pdf',stage4_panel_pdf)
    u.write(dest/'QA/FIG01_STAGE4_METHOD_PANEL.png',stage4_panel_png)
    figure8_legend_audit=None
    figure8_pdf=figure8_png=figure8_preview=None
    s5_pdf,s5_png,s5_preview,s5_plot_audit=figure_presentation.supplementary5_four_policy(s5_plot_data)
    difference=(dynamic.population_dependency_weighted_R_conn-
                dynamic.population_dependency_weighted_fixed_precomputed_best_path_connection-
                dynamic.population_dependency_weighted_full_minus_fixed_precomputed_best_path)
    assert difference.abs().max()<1e-12
    assert len(station)==92 and station.station_id.nunique()==92
    assert int(station.is_core_source.sum())==14
    assert not dynamic.duplicated(['strategy','time_hr']).any()
    for old,new in zip(ORDER,NEW):
        old_title,body=caps[old]
        title=label(new)+'.'+old_title.split('.',1)[1]
        body=references(body)
        if new=='Main/Fig01':
            body=('Stage 4 links an Impact-first priority-map example to an actual two-crew repair schedule from '
                  'evaluation realization 0. Gray intervals are directed travel; teal intervals are repair. '
                  'Completion releases the crew and restores raw station functionality before source-gated tract-service evaluation. '
                  'Other rule-based strategies and GA supply alternative orders; Unconstrained repair is the parallel reference.')
        if new=='Main/Fig08':
            old_rule='outlines mark frozen Q4 and the cohort P75'
            new_rule=('outlined tracts are in frozen FEMA NRI v1.19 SOVI quartile Q4 (the highest social-vulnerability quartile) '
                      'and have five-policy mean total service deficit at or above 38.38135467381475 equivalent '
                      'full-service-deficit hours over 0-480 h (the positive-population cohort 75th percentile)')
            assert old_rule in body
            body=body.replace(old_rule,new_rule)
        if new=='Supplement/FigS05':
            body=('(A) Change in population-weighted normalized service deficit when the M1 mapping cutoff is relaxed from 3% to 0% or 1%. '
                  '(B) Change when source connectivity is removed while the 0.50 functionality threshold is retained. '
                  '(C) Change under 0.05 or 0.75 functionality thresholds, with source connectivity reevaluated. '
                  'Points are means of paired differences across 1,000 frozen physical realizations; bars show empirical 5th-95th percentile '
                  'ranges, not confidence intervals. No damage samples or repair schedules were regenerated.')
        if new=='Main/Fig04':title,body=TITLE,CAPTION
        new_caps.append((title,body))
        if new=='Main/Fig08':
            pdf_row=next(r for r in manifest if r['final_name']==old+'.pdf')
            pdf_source=source(pdf_row['current_source_file'])
            assert u.digest(pdf_source)==pdf_row['sha256']
            figure8_pdf,figure8_png,figure8_preview,figure8_legend_audit=(
                figure_presentation.figure8_shared_map_legend(pdf_source,palette['colors']))
        preview=(stage4_preview if new=='Main/Fig01' else
                 figure8_preview if new=='Main/Fig08' else
                 s5_preview if new=='Supplement/FigS05' else
                 source(f'{SOURCE}/Page_Previews/{Path(old).name}.png'))
        u.write(dest/f'Page_Previews/{Path(new).name}.png',preview)
        for ext in ('pdf','png'):
            row=next(r.copy() for r in manifest if r['final_name']==old+'.'+ext)
            row.setdefault('legend_source_file','')
            row.setdefault('legend_source_sha256','')
            row.setdefault('palette_source_file','')
            row.setdefault('palette_source_sha256','')
            source_raw=source(row['current_source_file'])
            assert u.digest(source_raw)==row['sha256']
            assert source(row['mirror_file'])==source_raw
            raw=(stage4_pdf if new=='Main/Fig01' and ext=='pdf' else
                 stage4_png if new=='Main/Fig01' and ext=='png' else
                 figure8_pdf if new=='Main/Fig08' and ext=='pdf' else
                 figure8_png if new=='Main/Fig08' and ext=='png' else
                 s5_pdf if new=='Supplement/FigS05' and ext=='pdf' else
                 s5_png if new=='Supplement/FigS05' and ext=='png' else source_raw)
            ix=next(r.copy() for r in source_index if r['source_path']==row['current_source_file'])
            suffix=Path(row['mirror_file']).name.split('_',1)[1]
            new_path=dest/(new+'.'+ext)
            mirror_path=mirror/(Path(new).name+'_'+suffix)
            u.write(new_path,raw);u.write(mirror_path,raw)
            row.update(final_name=new+'.'+ext,sha256=u.digest(raw),
                current_source_file=new_path.relative_to(ROOT).as_posix(),
                mirror_file=mirror_path.relative_to(ROOT).as_posix(),source_commit=BASE,
                source_file=f'{SOURCE}/{old}.{ext}',
                status=('UPDATED_WORKFLOW_GENERATED_METHOD_PROCESS' if new=='Main/Fig01' else
                        'UPDATED_SEPARATE_MAP_LEGENDS' if new=='Main/Fig08' else
                        'UPDATED_FOUR_POLICY_SENSITIVITY' if new=='Supplement/FigS05' else
                        'RENUMBERED_REVIEW_ARTWORK_UNCHANGED'),
                promotion_generator=GEN,promotion_generator_sha256=u.sha(ROOT/GEN),
                previous_figure=old,
                change_in_this_update=('STAGE4_PRIORITY_SCHEDULING_COMPLETION_FLOW' if new=='Main/Fig01' else
                                       'SEPARATE_PANEL_C_AND_D_LEGENDS' if new=='Main/Fig08' else
                                       'VULNERABILITY_FIRST_ADDED_TO_VERIFIED_SENSITIVITY_COMPARISONS' if new=='Supplement/FigS05' else
                                       'NUMBERING_AND_CAPTION_ONLY'))
            if new=='Main/Fig08':
                row.update(legend_source_file=f'{SOURCE}/{old}.pdf',
                           legend_source_sha256=u.digest(source_raw),
                           palette_source_file=palette_path,
                           palette_source_sha256=u.digest(palette_bytes))
            if new=='Supplement/FigS05':
                row.update(additional_source_file='results/figure_review_s6_main4_20261107/QA/S5_VULNERABILITY_PLOT_DATA.json',
                           additional_source_sha256=u.digest(s5_plot_data))
            if new=='Main/Fig01':
                row.update(source_file=SOURCE+'/Main/Fig01.pdf',source_commit=BASE,
                           stage4_generator=WORKFLOW_GENERATOR,
                           stage4_generator_sha256=u.sha(ROOT/WORKFLOW_GENERATOR),
                           stage4_panel_sha256=u.digest(stage4_panel_pdf),
                           stage4_scheduler_source=SCHEDULER_SOURCE,
                           stage4_scheduler_source_sha256=u.sha(ROOT/SCHEDULER_SOURCE),
                           stage4_ga_source=GA_SOURCE,
                           stage4_ga_source_sha256=u.sha(ROOT/GA_SOURCE))
            for key in ['notes','main_message','scientific_content','scientific_question']:
                if key in ix:ix[key]=references(ix[key])
            ix.update(figure_number=Path(new).name,file=mirror_path.name,
                role='Main' if new.startswith('Main/') else 'Supplement',
                main_or_supplement='main' if new.startswith('Main/') else 'supplement',
                source_path=new_path.relative_to(ROOT).as_posix(),sha256=u.digest(raw),sha256_or_lfs_oid=u.digest(raw),
                current_status='SEPARATE_AUTHOR_REVIEW',submission_status='Separate promotion review; source suite retained',
                promotion_generator=GEN,previous_figure=old)
            if new=='Main/Fig04':
                ix.update(scientific_question='How do source connectivity and alternative paths recover under different restoration sequences?',
                    main_message='Dynamic full-network/fixed-path comparisons and conditional station maps retain all four panels.',
                    notes='Complete former S6, byte-identical artwork; insert between Sections 4.2 and 4.3.')
            if new=='Main/Fig01':
                ix.update(source_authority=BASE,source_data_path=SCHEDULER_SOURCE,
                    source_data_sha256=u.sha(ROOT/SCHEDULER_SOURCE),
                    generator=WORKFLOW_GENERATOR,
                    notes='Stage 4 separates the Unconstrained reference from priority rules, DS > 0 scheduling, directed travel and repair-completion service updates. No downstream recovery curves are shown.')
            if new=='Main/Fig08':
                ix.update(notes='Panel C and Panel D have separate aligned legends; the exact Q4 and service-deficit screen definitions are in the caption.')
            if new=='Supplement/FigS05':
                ix.update(notes='Four-policy paired mapping, source-connectivity and functionality-threshold comparisons, including Vulnerability-first.')
            rows.append(row);indices.append(ix)
            preservation.append({'previous_figure':old,'new_figure':new,'format':ext,
                'source_sha256':u.digest(source_raw),'output_sha256':u.sha(new_path),
                'byte_identical':source_raw==new_path.read_bytes()})
    u.write_csv(dest/'FIGURE_MANIFEST.csv',rows)
    u.write_csv(mirror/'FIGURE_INDEX.csv',indices)
    u.write(dest/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+
        '\n\n'.join('## '+title+'\n\n'+body for title,body in new_caps)+'\n')
    palette={k.replace('Figure7_','Figure8_'):v for k,v in palette.items()}
    palette['screening_rule']='Highest social-vulnerability quartile and five-policy service deficit >=38.38135467381475 equivalent hours (cohort upper quartile)'
    palette['screening_legend_label']='Outlined: Q4 + deficit ≥38.4 h'
    u.dump(dest/'CURRENT_CLUSTER_PALETTE.json',palette)
    u.write(dest/'STRATEGY_DISPLAY_NAMES.json',source(SOURCE+'/STRATEGY_DISPLAY_NAMES.json'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    rl_config.invariant=1
    book,main_book,supp_book=fitz.open(),fitz.open(),fitz.open()
    for i,(stem,(title,body)) in enumerate(zip(NEW,new_caps)):
        with fitz.open(dest/(stem+'.pdf')) as art:
            (main_book if i<8 else supp_book).insert_pdf(art)
            w,h=art[0].rect.width,art[0].rect.height
            with brief_caption_page(title,body,w) as cap:
                page=book.new_page(width=w,height=h+cap[0].rect.height)
                page.show_pdf_page(fitz.Rect(0,0,w,h),art,0)
                page.show_pdf_page(fitz.Rect(0,h,w,page.rect.height),cap,0)
                page_rows.append({'figure':stem,'page':i+1,'figure_height_pt':h,
                    'caption_height_pt':cap[0].rect.height,'title':title,'caption':body})
    for name,doc in [('ALL_MAIN_FIGURES.pdf',main_book),('ALL_SUPPLEMENT_FIGURES.pdf',supp_book),('ALL_FIGURES_WITH_CAPTIONS.pdf',book)]:
        u.write(dest/name,doc.tobytes(garbage=4,deflate=True,no_new_id=True));doc.close()
    html=['<!doctype html><meta charset="utf-8"><title>Figure promotion review - 2026-11-07</title>',
        '<style>body{font:16px Arial;margin:24px;max-width:1000px}img{max-width:100%;height:auto}section{margin-bottom:40px}</style>',
        '<h1>Figure promotion review - 2026-11-07</h1><p>Eight main and eight supplementary figures. Source suite retained unchanged.</p>']
    for stem,(title,body) in zip(NEW,new_caps):
        row=next(r for r in rows if r['final_name']==stem+'.png')
        name=Path(row['mirror_file']).name
        html.extend([f'<section><h2>{u.escape(title)}</h2>',
            f'<a href="{u.escape(name[:-4]+".pdf")}">Vector PDF</a>',
            f'<img src="{u.escape(name)}" alt="{u.escape(title)}"><p>{u.escape(body)}</p></section>'])
    u.write(mirror/'FIGURE_REVIEW_GALLERY.html','\n'.join(html))
    u.dump(dest/'QA/ARTWORK_PRESERVATION.json',preservation)
    implementation_files=[GEN,'src/la_grid/plotting/figure_presentation.py',
        'src/la_grid/plotting/consolidate_current_figure_suite.py',
        'src/la_grid/plotting/short_current_captions_20261013.py',
        WORKFLOW_GENERATOR,SCHEDULER_SOURCE,GA_SOURCE]
    implementation={path:{'commit':'local implementation at build time',
        'sha256':u.sha(ROOT/path),'bytes':(ROOT/path).stat().st_size}
        for path in implementation_files}
    u.dump(dest/'QA/SOURCE_IDENTITIES.json',{'baseline':BASE,'source_files':source_hashes,
        'implementation_files':implementation,
        'stage4_method_panel':{
            'generator':WORKFLOW_GENERATOR,
            'panel_pdf_sha256':u.digest(stage4_panel_pdf),
            'panel_png_sha256':u.digest(stage4_panel_png),
            'scheduler_source':SCHEDULER_SOURCE,
            'ga_source':GA_SOURCE,
            'implementation_checks':stage4_generator_audit['implementation_checks'],
            'recovery_curves_all_system_used':False}})
    u.dump(dest/'QA/PACKET_PAGE_REGISTRY.json',page_rows)
    u.dump(dest/'QA/NUMBERING_MAP.json',MAPPING)
    qa={'source_commit':BASE,
        'figure1_updated_with_method_process_panel':True,
        'figure1_stage4_audit':stage4_audit,
        'figure1_stage4_generator_audit':stage4_generator_audit,
        'figure1_no_downstream_result_plot_in_stage4':True,
        'unaffected_13_artwork_pairs_byte_identical':all(r['byte_identical'] for r in preservation if r['previous_figure'] not in ['Main/Fig01','Main/Fig07','Supplement/FigS05']),
        'figure8_separate_map_legends_updated':True,
        'figure8_legend_audit':figure8_legend_audit,
        's5_vulnerability_plot_audit':s5_plot_audit,
        's5_compact_height_mm':s5_plot_audit['height_mm'],
        's5_vulnerability_archive_audit_sha256':u.digest(s5_audit_path.read_bytes()),
        's5_vulnerability_plot_data_sha256':u.digest(s5_plot_data),
        'main_figures':8,'supplementary_figures':8,'complete_packet_pages':16,
        'all_four_promoted_panels_preserved':True,'static_station_records':len(station),
        'static_core_source_records':int(station.is_core_source.sum()),'dynamic_summary_records':len(dynamic),
        'dynamic_full_minus_fixed_identity_max_abs_error':float(difference.abs().max()),
        'scientific_models_rerun':False,'original_suite_written':False,
        'editable_manuscript_tracked':False,'manuscript_integration':'Separate insertion text and simultaneous reference mapping supplied; original manuscript not edited.'}
    u.dump(dest/'QA/NUMERICAL_AND_PRESERVATION_QA.json',qa)
    s5_rows=s5_plot_data_json=json.loads(s5_plot_data)
    audit=s5_audit
    controls={}
    for panel in ('A','B','C'):
        for row in s5_rows['series']:
            if row['panel']!=panel:
                continue
            controls.setdefault(panel,[]).append(
                f"| {row['policy_name']} | {row['control']} | {row['mean_gap_h']:.4f} | "
                f"{row['p05_gap_h']:.4f} | {row['p95_gap_h']:.4f} |")
    s5_qa_md=(
        '# Supplementary Figure S5: frozen four-policy verification\n\n'
        'Vulnerability-first is included alongside Impact-first, Hospital-first and Degree-first. '
        'Each policy uses the same 1,000 `2pc50` / `C57_D1` evaluation realization IDs and the same physical, '
        'damage-state and repair-duration hashes. Mapping is `M1_UTILITY_003`; the reference source gate is '
        '`G1_BASELINE_050` (functionality threshold 0.50); horizon is 480 h. The M1 matrix, graph, Core source '
        'set and directed-travel identities match the formal archive.\n\n'
        'Impact-first, Hospital-first and Degree-first controls reproduce their saved offline outputs: baseline '
        'event-integral error is below 1.5e-14 h; mapping 0%/1% controls and 0.05/0.75 threshold controls '
        'match saved results within 3e-14 h and exactly, respectively. Vulnerability-first has saved baseline '
        'G1 integrals, but its 0%/1% mapping and G2/G3 threshold counterfactual files are unavailable; those '
        'contrasts are therefore reconstructed from its 1,000 archived event-state files and are explicitly '
        'not described as previously saved outputs. No damage samples, repair schedules or service trajectories were regenerated.\n\n'
        'Panel A changes only mapping cutoff, applying the exact production threshold-renormalization and '
        'fallback rule to the unthresholded M1 weights; the 3% outcome is the reference. Panel B removes only '
        'source-connectivity factor C while retaining functionality threshold 0.50 (`e_off=fF`). Panel C '
        'recomputes functionality and source reachability at thresholds 0.05 and 0.75 on the same saved `f` '
        'event states; it does not reschedule repairs. Displayed intervals are empirical paired 5th-95th '
        'percentile ranges, not confidence intervals.\n\n'
        'The four strategies share physical sample hash chain `'+audit['frozen_identity']['formal_physical_hashes_sha256']+'`. '
        'The Vulnerability-first sequence hash is `'+audit['frozen_identity']['vulnerability_sequence_sha256']+'`; '
        'physical manifest SHA256 is `'+audit['frozen_identity']['physical_manifest_sha256']+'`. '
        'The source-level event archives are manifest-bound local dependencies and are absent from a clean Git clone.\n\n'
        '## Paired contrasts (h)\n\n'
        '| Panel | Strategy | Control | Mean | P05 | P95 |\n|---|---|---|---:|---:|---:|\n'
        + '\n'.join(line.replace('| ','| '+panel+' | ',1) for panel,lines in controls.items() for line in lines)
        + '\n')
    u.write(dest/'QA/S5_VULNERABILITY_FIRST_METHODS_QA.md',s5_qa_md)
    readme=(
        '# Figure promotion review - 2026-11-07\n\n'
        'Complete former Supplementary Figure S6 is Main Figure 4. All four panels are retained, with exact source PDF/PNG bytes. '
        'Main 4-7 become 5-8; former Supplement S7-S9 become S6-S8; Supplement S1-S5 remain unchanged. '
        'The collection contains eight main plus eight supplementary figures. Combined packet: 16 pages, each artwork followed immediately by its concise caption on the same page.\n\n'
        'This is a separate author-review collection. The source suite, manuscripts, simulation data, restoration results and clustering are unchanged. '
        'Figure 1 Stage 4 is generated from the implemented restoration-priority, DS > 0 crew-scheduling and repair-completion process. The parallel Unconstrained reference is separate; recovery curves and downstream outcomes do not appear in Stage 4. Figure 8 has separate Panel C and Panel D legends, with exact definitions in its caption. Supplementary Figure S5 includes Vulnerability-first comparisons calculated from its saved event-state archive; see `QA/S5_VULNERABILITY_FIRST_METHODS_QA.md` for pairing checks and estimates. The other 13 artwork pairs are byte-identical to their pinned sources. '
        'S5 is centered using the full visible bounds, including strategy labels, axes, tick labels and legends, in a 185 x 145 mm layout. '
        'No simulation or scientific model is rerun; only frozen result outputs are plotted. '
        'The source notes describe older candidate layouts. The actual promoted figure uses dynamic A/B curves for six scheduled strategies plus Unconstrained and static conditional C/D maps.\n\n'
        'Place Main Figure 4 after Section 4.2 and before the Section 4.3 heading. See MANUSCRIPT_INTEGRATION.md for the bridge and figure-reference substitutions. '
        'No editable manuscript document is tracked in this checkout, so manuscript placement is prepared, not falsely claimed as edited.\n\n'
        'Reproduce: `python src/la_grid/plotting/build_s6_main4_review.py`. '
        'The builder reads pinned actual source payloads and never invokes model, scheduling, or plotting analysis. '
        'Current older-suite builders remain available and do not target this separate collection.\n')
    u.write(dest/'README.md',readme);u.write(mirror/'README.md',readme)
    u.write(dest/'UPDATE_LOG.md','# 2026-11-07\n\nPromoted complete S6 to Main Figure 4; renumbered remaining figures, captions, previews, inventory, palette metadata and gallery.\n\n# 2026-11-08\n\nFigure 8 received separate aligned Panel C and Panel D legends, with exact Q4 and 38.38135467381475 h definitions in its caption. Supplementary Figure S5 adds Vulnerability-first mapping, source-connectivity and functionality-threshold comparisons from matched frozen event states. No simulations, schedules or GA outputs were regenerated.\n\n# 2026-11-09\n\nFigure 1 Stage 4 was temporarily changed to display downstream recovery curves. This was a scientific placement error and is superseded by the correction below. Supplementary Figure S5 was compacted to 185 x 145 mm with the full visible composition centered; all three panels and frozen comparisons are retained.\n\n# 2026-11-10\n\nStage 4 now shows three implementation-derived operations: priority rules, DS > 0 crew scheduling with realized damage-state repair durations and directed travel, and repair-completion updates. Unconstrained is shown separately as a parallel reference. The generator and builder no longer use `recovery_curves_all_system.csv` or the Figure 1 artwork from `ea692f4`.\n')
    u.write(dest/'MANUSCRIPT_INTEGRATION.md',manuscript_integration())
    print(json.dumps(qa,indent=2))

def manuscript_integration():
    lines=['# Manuscript placement and reference synchronization',
        '', '## Placement', '',
        'Insert the complete Figure 4 and its caption at the end of Section 4.2, immediately before Section 4.3. Do not split or omit A-D.',
        '', 'Proposed bridge:', '',
        '> Source-path loss depends on the availability of the surrounding network, not only on the repaired station. Figure 4 compares recovery through the full network with a fixed precomputed path, shows how alternative-route support changes with restoration sequencing, and locates conditional station-level access and reliability gains. These connectivity measures provide the network-mechanism context for the restoration-strategy performance comparisons in Section 4.3 (Figure 5).',
        '', '## Simultaneous reference substitutions', '',
        '| Previous reference | Review reference |', '|---|---|']
    lines += [f'| {label(old)} | {label(new)} |' for old,new in MAPPING.items()]
    lines += ['', 'Apply the mapping simultaneously, not as cascading text replacements. Main Figures 4-7 become 5-8; Supplementary Figures S7-S9 become S6-S8; the old S6 reference becomes main Figure 4. For example, the priority-geography caption now cites Figures 5-7 and Supplementary Figure S8.',
        '', '## Manuscript scope and availability', '',
        'No manuscript DOCX, main TEX, QMD or RMD is tracked in this checkout (the two retained TEX files are historical sensitivity tables). Therefore original manuscript files are neither overwritten nor claimed to be synchronized. Apply this exact mapping to the author-controlled manuscript copy, in-text citations, list of figures, captions and section-placement anchors during review. Historical research reports, old captions and archived code keep their original numbering.',
        '', 'The revised collection, captions, index, gallery and packet are internally synchronized. A numbering change is not a change in model assumptions or recovery results.', '']
    return '\n'.join(lines)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir');parser.add_argument('--mirror-dir')
    args=parser.parse_args();main(args.output_dir,args.mirror_dir)
