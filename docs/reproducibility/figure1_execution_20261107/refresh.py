"""Refresh Figure 1 and its packets only, using the canonical stage renderer."""
from pathlib import Path
import io
import json
import subprocess
import sys

import fitz
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import build_current_suite_p2 as builder
import figure_presentation

BASE='70a063bf9ff4d39a84090aa297aa3ac0e737b091'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'
MIRROR=ROOT/'results/figures_rq_aligned_20261101'
QA=Path(__file__).resolve().parent


def run():
    # Hydrate pointers only; never overwrite unrelated, modified artwork.
    tracked=u.git('ls-tree','-r','--name-only',BASE,'results/figure_review_rq_aligned_20261101',
                  'results/figures_rq_aligned_20261101').decode().splitlines()
    for rel in tracked:
        path=ROOT/rel
        if path.is_file() and path.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
            try:
                raw=u.payload(BASE,rel)
            except FileNotFoundError:
                print('Fetching saved artwork: '+rel,flush=True)
                pointer=u.git('show',f'{BASE}:{rel}')
                raw=subprocess.check_output(['git','lfs','smudge','--',rel],
                                            input=pointer,cwd=ROOT,timeout=180)
                expected=pointer.decode().split('oid sha256:')[1].splitlines()[0]
                assert u.digest(raw)==expected
            u.write(path,raw)
    before={r['final_name']:r for r in u.csv_rows(u.payload(BASE,str(SUITE.relative_to(ROOT)/'FIGURE_MANIFEST.csv').replace('\\','/')))}
    old=u.payload(BASE,str((SUITE/'Main/Fig01.pdf').relative_to(ROOT)).replace('\\','/'))
    source=builder.source('results/figure_review/Main/Fig01.pdf',builder.CURRENT_SUITE_BASE)
    new,audit=figure_presentation.restoration_workflow(source)
    existing=(SUITE/'Main/Fig01.pdf').read_bytes()
    if u.digest(existing)!=u.digest(old):
        repeated=existing
    else:
        repeated,_=figure_presentation.restoration_workflow(source)
    assert new==repeated
    with fitz.open(stream=old,filetype='pdf') as a,fitz.open(stream=new,filetype='pdf') as b:
        x=a[0].get_pixmap(dpi=150,alpha=False)
        y=b[0].get_pixmap(dpi=150,alpha=False)
        aa=np.frombuffer(x.samples,dtype=np.uint8).reshape(x.height,x.width,3)
        bb=np.frombuffer(y.samples,dtype=np.uint8).reshape(y.height,y.width,3)
        mask=np.ones(aa.shape[:2],dtype=bool)
        scale=150/72
        mask[round(464*scale):round(616*scale),round(8*scale):round(258*scale)]=False
        assert np.array_equal(aa[mask],bb[mask]),'Content outside Stage 4 changed'
        spans=figure_presentation.spans(b[0])
        selected=[s for s in spans if 481.7<s['bbox'][1] and s['bbox'][3]<614.7
                  and 9.5<s['bbox'][0] and s['bbox'][2]<256.3]
        assert len(selected)==9
        assert all(abs(s['size']-7.5)<1e-5 and 'Arial' in s['font'] for s in selected)
        png=((SUITE/'Main/Fig01.png').read_bytes() if existing==new else
             b[0].get_pixmap(dpi=600,alpha=False).tobytes('png'))
        u.write(QA/'Figure1_native_preview.png',b[0].get_pixmap(dpi=150,alpha=False).tobytes('png'))
        crop=fitz.Rect(9.5,465.2,256.3,614.7)
        u.write(QA/'Stage4_detail.png',b[0].get_pixmap(dpi=300,clip=crop,alpha=False).tobytes('png'))
        dimensions=list(b[0].rect)
    manifest=u.csv_rows((SUITE/'FIGURE_MANIFEST.csv').read_bytes())
    index=u.csv_rows((MIRROR/'FIGURE_INDEX.csv').read_bytes())
    for row in manifest:
        if row['final_name'] in ['Main/Fig01.pdf','Main/Fig01.png']:
            raw=new if row['final_name'].endswith('.pdf') else png
            u.write(ROOT/row['current_source_file'],raw)
            u.write(ROOT/row['mirror_file'],raw)
            row.update(sha256=u.digest(raw),presentation_generator_sha256=u.sha(ROOT/builder.PRESENTATION),
                       status='STAGE4_EXECUTION_FONT_AND_CONTENT_CORRECTION',change_in_this_update='UPDATED')
    for row in index:
        if row['figure_number']=='Fig01':
            row['sha256']=u.sha(MIRROR/row['file'])
            row['notes']='Stage 4: parallel versus crew-constrained execution; completion-event service updates. No illustrative recovery plots.'
    u.write_csv(SUITE/'FIGURE_MANIFEST.csv',manifest)
    u.write_csv(MIRROR/'FIGURE_INDEX.csv',index)
    builder.DEST=SUITE
    builder.MIRROR_DEST=MIRROR
    captions=u.captions((SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8'))
    registry=SUITE/'QA/COMPACT_PACKET_PAGE_REGISTRY.csv'
    supp=(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf').read_bytes()
    builder.packets(list(captions.items()),registry)
    # The supplementary packet is unrelated, including its PDF serialization.
    u.write(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf',supp)
    preserved=[]
    for row in manifest:
        if not row['final_name'].startswith('Main/Fig01.'):
            assert u.sha(ROOT/row['current_source_file'])==before[row['final_name']]['sha256']
            assert u.sha(ROOT/row['mirror_file'])==before[row['final_name']]['sha256']
            preserved.append(row['final_name'])
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as packet:
        assert len(packet)==16
        assert 'Repair completion: station functionality = 1' in packet[0].get_text().replace('\xa0',' ')
    audit.update(baseline=BASE,source_sha256=u.digest(source),before_sha256=u.digest(old),
                 after_sha256=u.digest(new),outside_stage4_pixels_identical=True,
                 body_labels=len(selected),body_sizes_pt=sorted({s['size'] for s in selected}),
                 preserved_artwork=preserved,deterministic_renderer=True,
                 packet_pages=16,pdf_dimensions_pt=dimensions,scientific_files_modified=False)
    u.dump(QA/'QA.json',audit)
    print(json.dumps(audit,indent=2))


if __name__=='__main__':
    run()
