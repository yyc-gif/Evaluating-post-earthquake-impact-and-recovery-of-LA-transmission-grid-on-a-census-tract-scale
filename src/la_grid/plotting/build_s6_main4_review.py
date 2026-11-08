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
from short_current_captions_20261013 import brief_caption_page

ROOT=u.ROOT
BASE='75cd19d4a0249d006efa00d4532762d0ee406c5a'
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
    'provenance/legacy_outputs/stage6/recovery_curves_all_system.csv',
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
    dynamic=pd.read_csv(io.BytesIO(source(INPUTS[1])))
    station=pd.read_csv(io.BytesIO(source(INPUTS[2])),dtype={'station_id':str})
    recovery_curve_path=INPUTS[-2]
    palette_path=INPUTS[-1]
    recovery_curves=source(recovery_curve_path)
    palette_bytes=source(INPUTS[-1])
    palette=json.loads(palette_bytes)
    assert palette['colors']=={'1':'#3C9198','2':'#52699E','3':'#C69EBA'}
    stage4_pdf,stage4_audit=figure_presentation.restoration_workflow_with_results(
        source(SOURCE+'/Main/Fig01.pdf'),recovery_curves)
    with fitz.open(stream=source(SOURCE+'/Main/Fig01.pdf'),filetype='pdf') as before_doc, \
         fitz.open(stream=stage4_pdf,filetype='pdf') as after_doc:
        before_pix=before_doc[0].get_pixmap(dpi=120,alpha=False)
        after_pix=after_doc[0].get_pixmap(dpi=120,alpha=False)
        before_rgb=np.frombuffer(before_pix.samples,dtype=np.uint8).reshape(
            before_pix.height,before_pix.width,3)
        after_rgb=np.frombuffer(after_pix.samples,dtype=np.uint8).reshape(
            after_pix.height,after_pix.width,3)
        assert before_rgb.shape==after_rgb.shape
        scale=120/72
        outside=np.ones(before_rgb.shape[:2],dtype=bool)
        outside[round(481.7*scale)-2:round(614.7*scale)+2,
                round(9.5*scale)-2:round(256.3*scale)+2]=False
        stage4_audit['outside_stage4_pixels_identical']=bool(
            np.array_equal(before_rgb[outside],after_rgb[outside]))
        assert stage4_audit['outside_stage4_pixels_identical']
    with fitz.open(stream=stage4_pdf,filetype='pdf') as stage4_doc:
        stage4_png=stage4_doc[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        stage4_preview=stage4_doc[0].get_pixmap(dpi=150,alpha=False).tobytes('png')
    figure8_legend_audit=None
    figure8_pdf=figure8_png=figure8_preview=None
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
            body=('Five-stage workflow from network and tract mapping through seismic damage, restoration execution, and community outcomes. '
                  'Stage 4 shows the saved population-weighted service-availability trajectories for Unconstrained and Impact-first; '
                  'Stage 5 summarizes derived service-loss and recovery-time measures.')
        if new=='Main/Fig08':
            old_rule='outlines mark frozen Q4 and the cohort P75'
            new_rule='outlined tracts are in the highest social-vulnerability quartile and have service deficit >=38.4 h (the cohort upper quartile)'
            assert old_rule in body
            body=body.replace(old_rule,new_rule)
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
                 figure8_png if new=='Main/Fig08' and ext=='png' else source_raw)
            ix=next(r.copy() for r in source_index if r['source_path']==row['current_source_file'])
            suffix=Path(row['mirror_file']).name.split('_',1)[1]
            new_path=dest/(new+'.'+ext)
            mirror_path=mirror/(Path(new).name+'_'+suffix)
            u.write(new_path,raw);u.write(mirror_path,raw)
            row.update(final_name=new+'.'+ext,sha256=u.digest(raw),
                current_source_file=new_path.relative_to(ROOT).as_posix(),
                mirror_file=mirror_path.relative_to(ROOT).as_posix(),source_commit=BASE,
                source_file=f'{SOURCE}/{old}.{ext}',
                status=('UPDATED_STAGE4_RESULT_CURVE' if new=='Main/Fig01' else
                        'UPDATED_SHARED_MAP_LEGEND' if new=='Main/Fig08' else
                        'RENUMBERED_REVIEW_ARTWORK_UNCHANGED'),
                promotion_generator=GEN,promotion_generator_sha256=u.sha(ROOT/GEN),
                previous_figure=old,
                change_in_this_update=('RESULT_CURVE_ADDED_TO_STAGE4' if new=='Main/Fig01' else
                                       'SHARED_LEGEND_AND_THRESHOLD_CLARIFIED' if new=='Main/Fig08' else
                                       'NUMBERING_AND_CAPTION_ONLY'))
            if new=='Main/Fig01':
                row.update(additional_source_file=recovery_curve_path,
                           additional_source_sha256=stage4_audit['source_sha256'])
            if new=='Main/Fig08':
                row.update(legend_source_file=f'{SOURCE}/{old}.pdf',
                           legend_source_sha256=u.digest(source_raw),
                           palette_source_file=palette_path,
                           palette_source_sha256=u.digest(palette_bytes))
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
                ix.update(notes='Stage 4 includes the saved 2pc50 population-weighted Unconstrained and Impact-first availability curves; no T80 is displayed in this stage.')
            if new=='Main/Fig08':
                ix.update(notes='One aligned legend identifies C1-C3, N/A, and tracts in the highest social-vulnerability quartile with service deficit >=38.4 h.')
            rows.append(row);indices.append(ix)
            preservation.append({'previous_figure':old,'new_figure':new,'format':ext,
                'source_sha256':u.digest(raw),'output_sha256':u.sha(new_path),'byte_identical':raw==new_path.read_bytes()})
    u.write_csv(dest/'FIGURE_MANIFEST.csv',rows)
    u.write_csv(mirror/'FIGURE_INDEX.csv',indices)
    u.write(dest/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+
        '\n\n'.join('## '+title+'\n\n'+body for title,body in new_caps)+'\n')
    palette={k.replace('Figure7_','Figure8_'):v for k,v in palette.items()}
    palette['screening_rule']='Highest social-vulnerability quartile and five-policy service deficit >=38.38135467381475 equivalent hours (cohort upper quartile)'
    palette['screening_legend_label']='Highest social-vulnerability quartile + upper-quarter service deficit (≥38.4 h)'
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
    u.dump(dest/'QA/SOURCE_IDENTITIES.json',{'baseline':BASE,'source_files':source_hashes,
        'original_notes_describe_separate_candidates_not_exact_current_S6':True})
    u.dump(dest/'QA/PACKET_PAGE_REGISTRY.json',page_rows)
    u.dump(dest/'QA/NUMBERING_MAP.json',MAPPING)
    qa={'source_commit':BASE,
        'figure1_updated_only_with_frozen_result_curve':True,
        'unaffected_14_artwork_pairs_byte_identical':all(r['byte_identical'] for r in preservation if r['previous_figure'] not in ['Main/Fig01','Main/Fig07']),
        'figure8_shared_map_legend_updated':True,
        'figure8_legend_audit':figure8_legend_audit,
        'figure1_source_curve_audit':stage4_audit,
        'main_figures':8,'supplementary_figures':8,'complete_packet_pages':16,
        'all_four_promoted_panels_preserved':True,'static_station_records':len(station),
        'static_core_source_records':int(station.is_core_source.sum()),'dynamic_summary_records':len(dynamic),
        'dynamic_full_minus_fixed_identity_max_abs_error':float(difference.abs().max()),
        'scientific_models_rerun':False,'original_suite_written':False,
        'editable_manuscript_tracked':False,'manuscript_integration':'Separate insertion text and simultaneous reference mapping supplied; original manuscript not edited.'}
    u.dump(dest/'QA/NUMERICAL_AND_PRESERVATION_QA.json',qa)
    readme=(
        '# Figure promotion review - 2026-11-07\n\n'
        'Complete former Supplementary Figure S6 is Main Figure 4. All four panels are retained, with exact source PDF/PNG bytes. '
        'Main 4-7 become 5-8; former Supplement S7-S9 become S6-S8; Supplement S1-S5 remain unchanged. '
        'The collection contains eight main plus eight supplementary figures. Combined packet: 16 pages, each artwork followed immediately by its concise caption on the same page.\n\n'
        'This is a separate author-review collection. The source suite, manuscripts, simulation data, restoration results and clustering are unchanged. '
        'Figure 1 Stage 4 includes saved 2pc50 mean service-availability curves. Figure 8 uses one aligned map-legend row, one N/A entry, and plain-language upper-quartile screening criteria with the 38.4 h cutoff; the other 14 numbered artwork pairs are byte-identical to their pinned sources. '
        'No simulation or scientific model is rerun; only frozen result outputs are plotted. '
        'The source notes describe older candidate layouts. The actual promoted figure uses dynamic A/B curves for six scheduled strategies plus Unconstrained and static conditional C/D maps.\n\n'
        'Place Main Figure 4 after Section 4.2 and before the Section 4.3 heading. See MANUSCRIPT_INTEGRATION.md for the bridge and figure-reference substitutions. '
        'No editable manuscript document is tracked in this checkout, so manuscript placement is prepared, not falsely claimed as edited.\n\n'
        'Reproduce: `python src/la_grid/plotting/build_s6_main4_review.py`. '
        'The builder reads pinned actual source payloads and never invokes model, scheduling, or plotting analysis. '
        'Current older-suite builders remain available and do not target this separate collection.\n')
    u.write(dest/'README.md',readme);u.write(mirror/'README.md',readme)
    u.write(dest/'UPDATE_LOG.md','# 2026-11-07\n\nPromoted complete S6 to Main Figure 4; renumbered remaining figures, captions, previews, inventory, palette metadata and gallery.\n\n# 2026-11-08\n\nAdded saved mean service-availability curves to Figure 1 Stage 4. Figure 8 now has one aligned map-legend row, one N/A entry, and plain-language screening criteria with the 38.4 h cutoff. No simulation was rerun; the other 14 numbered artwork pairs remain byte-identical to their pinned sources.\n')
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
