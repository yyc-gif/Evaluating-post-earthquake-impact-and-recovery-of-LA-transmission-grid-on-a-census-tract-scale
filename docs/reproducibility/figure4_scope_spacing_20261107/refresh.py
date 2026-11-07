"""Refresh only Figure 4, its caption, registries and dependent packets."""
from pathlib import Path
import io
import json
import sys

import fitz
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import build_current_suite_p2 as b
import rq_aligned_figure_updates as render

BASE='d65f82ced0b9e9e01cd42f9d2f5e3b9261961da1'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'
MIRROR=ROOT/'results/figures_rq_aligned_20261101'
QA=Path(__file__).resolve().parent


def run():
    manifest=u.csv_rows((SUITE/'FIGURE_MANIFEST.csv').read_bytes())
    old={r['final_name']:r['sha256'] for r in manifest}
    original=u.payload(b.CURRENT_SUITE_BASE,'results/figure_review/Main/Fig04.pdf')
    paths=[
        'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',
        'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet',
        'Formal_Experiment_20260923/Formal_Reviewer_Results/FORMAL_GATE_COMPONENTS.csv']
    inputs=[u.payload(b.BASE,p) for p in paths]
    primary,vulnerability=[pd.read_parquet(io.BytesIO(raw)) for raw in inputs[:2]]
    gates=pd.read_csv(io.BytesIO(inputs[2]))
    new,audit=render.make_figure4(primary,vulnerability,gates,original)
    repeated,_=render.make_figure4(primary,vulnerability,gates,original)
    assert new==repeated
    previous=json.loads(u.payload(BASE,'results/figure_review_rq_aligned_20261101/QA/FIG04_MECHANISM_AND_OUTCOME_QA.json'))
    assert previous['service_loss_and_T80_rows']==audit['service_loss_and_T80_rows']
    assert previous['paired_component_rows']==audit['paired_component_rows']
    with fitz.open(stream=new,filetype='pdf') as doc:
        page=doc[0]
        spans=[s for block in page.get_text('dict')['blocks'] for line in block.get('lines',[]) for s in line['spans']]
        for span in spans:
            span['text']=span['text'].replace('\xa0',' ').replace('\u00ad','-')
        title_a=next(s for s in spans if s['text'].startswith('A. Population'))
        title_b=next(s for s in spans if s['text'].startswith('B. Service'))
        legend_a=next(s for s in spans if s['text']=='Infrastructure-based')
        legend_b=next(s for s in spans if s['text']=='All-tract service loss')
        gaps=[legend_a['bbox'][1]-title_a['bbox'][3],legend_b['bbox'][1]-title_b['bbox'][3]]
        assert abs(gaps[0]-gaps[1])<0.05,gaps
        assert title_a['size']==title_b['size']==9.5
        end_a=max(s['bbox'][3] for s in spans if s['text']=='Time after earthquake (h)')
        interpanel=title_b['bbox'][1]-end_a
        assert 18<interpanel<23,interpanel
        assert 'C. Why' not in page.get_text()
        png=page.get_pixmap(dpi=600,alpha=False).tobytes('png')
        u.write(QA/'Figure4_native.png',page.get_pixmap(dpi=150,alpha=False).tobytes('png'))
        size_mm=f'{page.rect.width*25.4/72:.3f} x {page.rect.height*25.4/72:.3f}'
    for row in manifest:
        if row['final_name'] not in ['Main/Fig04.pdf','Main/Fig04.png']:
            continue
        raw=new if row['final_name'].endswith('.pdf') else png
        u.write(ROOT/row['current_source_file'],raw)
        u.write(ROOT/row['mirror_file'],raw)
        row.update(sha256=u.digest(raw),size_mm=size_mm,status='SEVEN_STRATEGY_OVERVIEW_TWO_PANEL',
                   presentation_generator_sha256=u.sha(ROOT/'src/la_grid/plotting/rq_aligned_figure_updates.py'))
    u.write_csv(SUITE/'FIGURE_MANIFEST.csv',manifest)
    index=u.csv_rows((MIRROR/'FIGURE_INDEX.csv').read_bytes())
    for row in index:
        if row['figure_number']=='Fig04':
            row.update(sha256=u.sha(MIRROR/row['file']),
                main_message='Compares recovery trajectories, service loss and recovery time across seven strategies.',
                scientific_content='Compares recovery trajectories, service loss and recovery time across seven strategies.',
                notes='A/B cover all seven displayed strategies. The single-pair decomposition remains diagnostic evidence, not a main panel.')
    u.write_csv(MIRROR/'FIGURE_INDEX.csv',index)
    captions=u.captions((SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8'))
    key=next(k for k in captions if k.startswith('Figure 4.'))
    old_caption=captions[key]
    captions[key]=b.captions()[3][1]
    u.write(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+
            '\n\n'.join('## '+k+'\n\n'+v for k,v in captions.items())+'\n')
    gallery=(MIRROR/'FIGURE_REVIEW_GALLERY.html').read_text(encoding='utf-8')
    if u.escape(old_caption)!=u.escape(captions[key]):
        assert gallery.count(u.escape(old_caption))==1
        gallery=gallery.replace(u.escape(old_caption),u.escape(captions[key]))
    u.write(MIRROR/'FIGURE_REVIEW_GALLERY.html',gallery)
    b.DEST,b.MIRROR_DEST=SUITE,MIRROR
    supplementary=(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf').read_bytes()
    b.packets(list(captions.items()),SUITE/'QA/COMPACT_PACKET_PAGE_REGISTRY.csv',{'Main/Fig04'})
    u.write(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf',supplementary)
    preserved=[]
    for row in manifest:
        if row['final_name'].startswith('Main/Fig04.'):
            continue
        assert u.sha(ROOT/row['current_source_file'])==old[row['final_name']]
        assert u.sha(ROOT/row['mirror_file'])==old[row['final_name']]
        preserved.append(row['final_name'])
    audit.update(baseline=BASE,original_layout_commit=b.CURRENT_SUITE_BASE,
        original_panels=['A','B'],pair_panel_added_by='f2a7ce41df9c4beda4814b9c0ec1ab27426ae3bf',
        source_hashes={p:u.digest(raw) for p,raw in zip(paths,inputs)},
        saved_outcome_rows_identical=True,saved_component_rows_identical=True,
        deterministic_renderer=True,title_legend_gaps_pt=gaps,
        previous_plot_to_next_title_pt=interpanel,preserved_artwork=preserved,
        preserved_artwork_sha256={name:old[name] for name in preserved},
        title_font_size_pt=9.5,new_sha256=u.digest(new),scientific_files_modified=False)
    u.dump(SUITE/'QA/FIG04_MECHANISM_AND_OUTCOME_QA.json',audit)
    u.dump(QA/'QA.json',audit)
    note=('\n## 2026-11-07 - Figure 4 scope and spacing correction\n\n'
          'The earlier Figure 4 had A/B only. Restored the seven-strategy overview; '
          'the November 1 single-pair mechanism panel remains archived diagnostic evidence. '
          'Saved trajectories, outcome values and realization ranges are unchanged. '
          'Title/legend clearances are matched; all other numbered figures are byte-identical.\n')
    log=(SUITE/'UPDATE_LOG.md').read_text(encoding='utf-8')
    if note.strip() not in log:
        u.write(SUITE/'UPDATE_LOG.md',log+note)
    for path in [SUITE/'README.md',MIRROR/'README.md']:
        text=path.read_text(encoding='utf-8').replace(
            'Figure 4 adds realization-level outcome and component comparisons;',
            'Figure 4 compares recovery and realization-level outcomes across seven strategies;')
        u.write(path,text)
    print(json.dumps({k:audit[k] for k in ['title_legend_gaps_pt','previous_plot_to_next_title_pt',
                                          'deterministic_renderer','saved_outcome_rows_identical']},indent=2))


if __name__=='__main__':
    run()
