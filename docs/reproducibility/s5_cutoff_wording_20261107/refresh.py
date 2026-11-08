"""Update only two S5 labels and their dependent publication artifacts."""
from pathlib import Path
import json
import re
import sys

import fitz
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import build_current_suite_p2 as b
import figure_presentation as render

BASE='56bace172c5af1891d12cf6f7fde8735a334a431'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'
MIRROR=ROOT/'results/figures_rq_aligned_20261101'
QA=Path(__file__).resolve().parent


def run():
    old=u.payload(BASE,'results/figure_review_rq_aligned_20261101/Supplement/FigS05.pdf')
    assert old==u.payload(b.CURRENT_SUITE_BASE,'results/figure_review/Supplement/FigS05.pdf')
    new,audit=render.mapping_cutoff_labels(old)
    assert new==render.mapping_cutoff_labels(old)[0]
    with fitz.open(stream=old,filetype='pdf') as a,fitz.open(stream=new,filetype='pdf') as z:
        before=a[0].get_pixmap(dpi=150,alpha=False)
        after=z[0].get_pixmap(dpi=150,alpha=False)
        aa=np.frombuffer(before.samples,dtype=np.uint8).reshape(before.height,before.width,3)
        zz=np.frombuffer(after.samples,dtype=np.uint8).reshape(after.height,after.width,3)
        mask=np.ones(aa.shape[:2],dtype=bool)
        for record in audit['label_changes']:
            x0,y0,x1,y1=record['old_bbox']
            mask[int(y0*150/72)-2:int(y1*150/72)+3,int(x0*150/72)-2:int(x1*150/72)+3]=False
        assert np.array_equal(aa[mask],zz[mask]),'Plot content outside the two labels changed'
        text=' '.join(z[0].get_text().replace('\xa0',' ').split())
        assert '3% cutoff' in text and 'Change from 3% cutoff (h)' in text
        assert 'production' not in text.lower()
        assert '+0.543' in text and '+0.153' in text
        png=z[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        u.write(QA/'S5_preview.png',z[0].get_pixmap(dpi=150,alpha=False).tobytes('png'))
    manifest=u.csv_rows((SUITE/'FIGURE_MANIFEST.csv').read_bytes())
    baseline={r['final_name']:r['sha256'] for r in manifest}
    for row in manifest:
        if row['final_name'].startswith('Supplement/FigS05.'):
            output=new if row['final_name'].endswith('.pdf') else png
            u.write(ROOT/row['current_source_file'],output)
            u.write(ROOT/row['mirror_file'],output)
            row.update(sha256=u.digest(output),presentation_generator=b.PRESENTATION,
                       presentation_generator_sha256=u.sha(ROOT/b.PRESENTATION),status='PUBLICATION_CUTOFF_LABELS')
    u.write_csv(SUITE/'FIGURE_MANIFEST.csv',manifest)
    index=u.csv_rows((MIRROR/'FIGURE_INDEX.csv').read_bytes())
    for row in index:
        if row['figure_number']=='FigS05':
            row.update(sha256=u.sha(MIRROR/row['file']),generator=b.PRESENTATION,
                       notes='Cutoff labels only; numerical results and plot geometry unchanged.')
    u.write_csv(MIRROR/'FIGURE_INDEX.csv',index)
    b.DEST,b.MIRROR_DEST=SUITE,MIRROR
    main=(SUITE/'ALL_MAIN_FIGURES.pdf').read_bytes()
    captions=u.captions((SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8'))
    b.packets(list(captions.items()),SUITE/'QA/COMPACT_PACKET_PAGE_REGISTRY.csv',{'Supplement/FigS05'})
    u.write(SUITE/'ALL_MAIN_FIGURES.pdf',main)
    preserved={}
    text_audit={}
    for row in manifest:
        if not row['final_name'].startswith('Supplement/FigS05.'):
            assert u.sha(ROOT/row['current_source_file'])==baseline[row['final_name']]
            assert u.sha(ROOT/row['mirror_file'])==baseline[row['final_name']]
            preserved[row['final_name']]=baseline[row['final_name']]
        if row['final_name'].endswith('.pdf'):
            with fitz.open(ROOT/row['current_source_file']) as doc:
                count=sum(len(re.findall(r'\bproduction\b',p.get_text(),flags=re.I)) for p in doc)
                assert count==0,row['final_name']
                text_audit[row['final_name']]=count
    audit.update(baseline=BASE,source_sha256=u.digest(old),output_sha256=u.digest(new),
                 outside_label_pixels_identical=True,preserved_artwork_sha256=preserved,
                 active_figure_word_audit=text_audit,deterministic_renderer=True,
                 captions_unchanged=True,scientific_files_modified=False)
    u.dump(QA/'QA.json',audit)
    print('PASS: two labels corrected; all 16 artwork PDFs audited; other 15 figure pairs unchanged.')


if __name__=='__main__':
    run()
