"""Rebuild the population palette only, retaining vector geometry and data."""
from pathlib import Path
import sys
import fitz
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import build_current_suite_p2 as b
import figure_presentation as render

BASE='e611e93cea95e5c7296c47bbe1dc0777fe97e31a'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'
MIRROR=ROOT/'results/figures_rq_aligned_20261101'
QA=Path(__file__).resolve().parent

def run():
    old=u.payload(BASE,'results/figure_review_rq_aligned_20261101/Supplement/FigS08.pdf')
    original=u.payload(b.CURRENT_SUITE_BASE,'results/figure_review/Supplement/FigS08.pdf')
    new,audit=render.priority_geography(original)
    assert new==render.priority_geography(original)[0]
    with fitz.open(stream=old,filetype='pdf') as a,fitz.open(stream=new,filetype='pdf') as z:
        assert a[0].rect==z[0].rect
        def text_spans(page):
            return [s for v in page.get_text('dict')['blocks'] if v['type']==0 for line in v['lines'] for s in line['spans']]
        assert text_spans(a[0])==text_spans(z[0])
        aa=a[0].get_pixmap(dpi=150,alpha=False)
        zz=z[0].get_pixmap(dpi=150,alpha=False)
        before=np.frombuffer(aa.samples,np.uint8).reshape(aa.height,aa.width,3)
        after=np.frombuffer(zz.samples,np.uint8).reshape(zz.height,zz.width,3)
        assert np.array_equal(before[:int(525*150/72)],after[:int(525*150/72)])
        assert len(a[0].get_drawings())==len(z[0].get_drawings())
        for x,y in zip(a[0].get_drawings(),z[0].get_drawings()):
            assert {k:v for k,v in x.items() if k!='fill'}=={k:v for k,v in y.items() if k!='fill'}
        png=z[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        u.write(QA/'full_preview.png',z[0].get_pixmap(dpi=110,alpha=False).tobytes('png'))
        u.write(QA/'panel_C_preview.png',z[0].get_pixmap(dpi=200,clip=fitz.Rect(0,520,z[0].rect.width,z[0].rect.height),alpha=False).tobytes('png'))
    manifest=u.csv_rows((SUITE/'FIGURE_MANIFEST.csv').read_bytes())
    preserved={}
    for row in manifest:
        if row['final_name'].startswith('Supplement/FigS08.'):
            data=new if row['final_name'].endswith('.pdf') else png
            u.write(ROOT/row['current_source_file'],data)
            u.write(ROOT/row['mirror_file'],data)
            row.update(sha256=u.digest(data),presentation_generator=b.PRESENTATION,
                       presentation_generator_sha256=u.sha(ROOT/b.PRESENTATION))
        else:
            assert u.sha(ROOT/row['current_source_file'])==row['sha256']
            assert u.sha(ROOT/row['mirror_file'])==row['sha256']
            preserved[row['final_name']]=row['sha256']
    u.write_csv(SUITE/'FIGURE_MANIFEST.csv',manifest)
    index=u.csv_rows((MIRROR/'FIGURE_INDEX.csv').read_bytes())
    for row in index:
        if row['figure_number']=='FigS08':
            row.update(sha256=u.sha(MIRROR/row['file']),generator=b.PRESENTATION,
                       notes='White-purple population palette; data, ranks, geometry and log scale unchanged.')
    u.write_csv(MIRROR/'FIGURE_INDEX.csv',index)
    path=SUITE/'MANUSCRIPT_FACING_CAPTIONS.md'
    text=path.read_text(encoding='utf-8')
    caps=u.captions(text)
    title=next(t for t in caps if t.startswith('Supplementary Figure S8.'))
    old_body=caps[title]
    new_body=old_body.replace('blue-green','white-purple')
    u.write(path,text.replace(old_body,new_body))
    gallery=MIRROR/'FIGURE_REVIEW_GALLERY.html'
    u.write(gallery,gallery.read_text(encoding='utf-8').replace(u.escape(old_body),u.escape(new_body)))
    for path in [SUITE/'README.md',MIRROR/'README.md']:
        u.write(path,path.read_text(encoding='utf-8').replace('muted blue-green population scale','white-purple population scale'))
    panel_audit=SUITE/'QA/RQ_ALIGNMENT_AND_PANEL_AUDIT.md'
    u.write(panel_audit,panel_audit.read_text(encoding='utf-8').replace('Population background changed to muted blue-green','White-purple population background'))
    log=SUITE/'UPDATE_LOG.md'
    addition='\n## 2026-11-07 - Figure S8 white-purple population shading\n\nChanged only Panel C population fills and the matching colorbar. Logarithmic population normalization, priorities, text, vector paths and Panels A/B are unchanged.\n'
    if addition.strip() not in log.read_text(encoding='utf-8'):
        u.write(log,log.read_text(encoding='utf-8')+addition)
    b.DEST,b.MIRROR_DEST=SUITE,MIRROR
    main=(SUITE/'ALL_MAIN_FIGURES.pdf').read_bytes()
    caps=u.captions((SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8'))
    b.packets(list(caps.items()),SUITE/'QA/COMPACT_PACKET_PAGE_REGISTRY.csv',{'Supplement/FigS08'})
    u.write(SUITE/'ALL_MAIN_FIGURES.pdf',main)
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as doc:
        assert len(doc)==16
        assert 'white-purple' in doc[14].get_text()
    audit.update(baseline=BASE,source_sha256=u.digest(original),previous_sha256=u.digest(old),
        output_sha256=u.digest(new),panels_A_B_pixels_identical=True,
        text_and_positions_identical=True,all_nonfill_drawing_properties_identical=True,
        preserved_artwork_sha256=preserved,deterministic_renderer=True,packet_pages=16,
        main_packet_sha256=u.digest(main),scientific_files_modified=False)
    u.dump(QA/'QA.json',audit)
    u.dump(SUITE/'QA/FIGS08_POPULATION_COLOR_QA.json',audit)
    print('PASS: white-purple palette; A/B pixels, all text, geometry, and other 15 figure pairs unchanged.')

if __name__=='__main__':run()
