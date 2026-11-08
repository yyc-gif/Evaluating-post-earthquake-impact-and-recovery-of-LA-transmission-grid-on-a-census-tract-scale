"""Patch only Figure 7B using the canonical profile renderer and saved values."""
from pathlib import Path
import io
import json
import sys

import fitz
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import build_current_suite_p2 as b
import figure7_final_presentation_20261016 as render

BASE='2621ca6eb39944892771759a4cb35c77a819e171'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'
MIRROR=ROOT/'results/figures_rq_aligned_20261101'
QA=Path(__file__).resolve().parent
REGION=fitz.Rect(0,264.5,render.PAGE_W,383)


def replacement(original,profile):
    plt.rcParams.update({'font.family':'Arial','font.size':7.5,'pdf.fonttype':42,
                         'ps.fonttype':42,'axes.unicode_minus':False,'savefig.facecolor':'white'})
    fig=plt.figure(figsize=(7.2,390/72),facecolor='white')
    render._draw_profiles(fig,profile,render.PROPOSED,layout='C')
    buffer=io.BytesIO()
    fig.savefig(buffer,format='pdf',metadata={'CreationDate':None,'ModDate':None})
    plt.close(fig)
    with fitz.open(stream=original,filetype='pdf') as doc,fitz.open(stream=buffer.getvalue(),filetype='pdf') as panel:
        doc[0].add_redact_annot(REGION,fill=(1,1,1))
        doc[0].apply_redactions(images=0,graphics=0)
        doc[0].show_pdf_page(REGION,panel,0,clip=REGION)
        return doc.tobytes(garbage=4,deflate=True,no_new_id=True)


def cells(page):
    spans=[s for block in page.get_text('dict')['blocks'] for line in block.get('lines',[]) for s in line['spans']]
    selected=[s for s in spans if 258<s['bbox'][0]<442 and 290<s['bbox'][1]<372
              and s['text'][:1] in ['+','-']]
    assert len(selected)==21,len(selected)
    return [s['text'] for s in sorted(selected,key=lambda s:(round(s['bbox'][1],1),s['bbox'][0]))]


def run():
    feature_path=b.PB+'FROZEN_P2_TRACT_TABLE_2315.csv'
    weight_path=b.PB+'P2_STANDARDIZER_AND_WEIGHTS.csv'
    raw=u.payload(b.BASE,feature_path)
    weights_raw=u.payload(b.BASE,weight_path)
    full=pd.read_csv(io.BytesIO(raw),dtype={'tract_id':str},float_precision='round_trip').sort_values('tract_id')
    table=full[full.Population.gt(0)].copy()
    weights=pd.read_csv(io.BytesIO(weights_raw),float_precision='round_trip')
    assert len(table)==2299 and int(table.Population.sum())==9066522
    assert table.P2_K3_class.value_counts().sort_index().tolist()==[1235,428,636]
    profile=render.profile_means(table,weights)
    source_profile=pd.read_csv(io.BytesIO(u.payload(b.BASE,b.PB+'P2_ORDINARY_COHORT_Z_CLASS_MEANS.csv')),
                               float_precision='round_trip').set_index('class_id')
    np.testing.assert_allclose(profile[render.FEATURES],source_profile.loc[profile.index,render.FEATURES],atol=1e-12,rtol=0)
    old=u.payload(BASE,'results/figure_review_rq_aligned_20261101/Main/Fig07.pdf')
    new=replacement(old,profile)
    assert new==replacement(old,profile)
    with fitz.open(stream=old,filetype='pdf') as before,fitz.open(stream=new,filetype='pdf') as after:
        assert cells(before[0])==cells(after[0])
        expected=[f'{profile.loc[c,feature]:+.2f}' for feature in render.FEATURES for c in ['C1','C2','C3']]
        assert cells(after[0])==expected
        a=before[0].get_pixmap(dpi=150,alpha=False)
        z=after[0].get_pixmap(dpi=150,alpha=False)
        aa=np.frombuffer(a.samples,dtype=np.uint8).reshape(a.height,a.width,3)
        zz=np.frombuffer(z.samples,dtype=np.uint8).reshape(z.height,z.width,3)
        mask=np.ones(aa.shape[:2],dtype=bool)
        mask[int(REGION.y0*150/72)-1:int(REGION.y1*150/72)+2,:]=False
        assert np.array_equal(aa[mask],zz[mask]),'A/C/D changed'
        u.write(QA/'PanelB_detail.png',after[0].get_pixmap(dpi=300,clip=REGION,alpha=False).tobytes('png'))
        png=after[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
    manifest=u.csv_rows((SUITE/'FIGURE_MANIFEST.csv').read_bytes())
    baseline={r['final_name']:r['sha256'] for r in manifest}
    for row in manifest:
        if row['final_name'].startswith('Main/Fig07.'):
            output=new if row['final_name'].endswith('.pdf') else png
            u.write(ROOT/row['current_source_file'],output)
            u.write(ROOT/row['mirror_file'],output)
            row.update(sha256=u.digest(output),
                presentation_generator='src/la_grid/plotting/figure7_final_presentation_20261016.py',
                presentation_generator_sha256=u.sha(ROOT/'src/la_grid/plotting/figure7_final_presentation_20261016.py'))
    u.write_csv(SUITE/'FIGURE_MANIFEST.csv',manifest)
    index=u.csv_rows((MIRROR/'FIGURE_INDEX.csv').read_bytes())
    for row in index:
        if row['figure_number']=='Fig07':
            row['sha256']=u.sha(MIRROR/row['file'])
    u.write_csv(MIRROR/'FIGURE_INDEX.csv',index)
    captions=u.captions((SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8'))
    key=next(k for k in captions if k.startswith('Figure 7.'))
    old_caption=captions[key]
    captions[key]=old_caption.replace('B shows standardized means for all seven fitted variables;',
                                     'B shows standardized means for all seven fitted variables, grouped by research question;')
    u.write(SUITE/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+
            '\n\n'.join('## '+k+'\n\n'+v for k,v in captions.items())+'\n')
    gallery=(MIRROR/'FIGURE_REVIEW_GALLERY.html').read_text(encoding='utf-8')
    if old_caption!=captions[key]:
        assert gallery.count(u.escape(old_caption))==1
        gallery=gallery.replace(u.escape(old_caption),u.escape(captions[key]))
    u.write(MIRROR/'FIGURE_REVIEW_GALLERY.html',gallery)
    b.DEST,b.MIRROR_DEST=SUITE,MIRROR
    supp=(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf').read_bytes()
    b.packets(list(captions.items()),SUITE/'QA/COMPACT_PACKET_PAGE_REGISTRY.csv',{'Main/Fig07'})
    u.write(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf',supp)
    preserved={}
    for row in manifest:
        if not row['final_name'].startswith('Main/Fig07.'):
            assert u.sha(ROOT/row['current_source_file'])==baseline[row['final_name']]
            assert u.sha(ROOT/row['mirror_file'])==baseline[row['final_name']]
            preserved[row['final_name']]=baseline[row['final_name']]
    u.dump(QA/'QA.json',dict(baseline=BASE,source_commit=b.BASE,
        source_hashes={feature_path:u.digest(raw),weight_path:u.digest(weights_raw)},
        RQ_groups={k:list(v) for k,v in render.RQ_GROUPS},
        eligible_tracts=len(table),represented_population=int(table.Population.sum()),
        class_counts=table.P2_K3_class.value_counts().sort_index().tolist(),
        ordinary_class_z_means=profile[render.FEATURES].to_dict(),
        printed_cells=expected,all_21_profile_values_unchanged=True,
        A_C_D_pixels_identical=True,preserved_artwork_sha256=preserved,
        deterministic_renderer=True,models_refitted=False,scientific_files_changed=False,
        authorized_region_pt=list(REGION),new_figure_sha256=u.digest(new)))
    note=('\n## 2026-11-07 - Figure 7B research-question groups\n\n'
          'RQ1 brackets the three initial-service/network features; RQ2 brackets the two recovery-deficit features; '
          'RQ3 brackets social vulnerability and population. Group boundaries span both labels and cells. '
          'All 21 profile values, A/C/D, and the other fifteen numbered figures are unchanged.\n')
    log=(SUITE/'UPDATE_LOG.md').read_text(encoding='utf-8')
    if note.strip() not in log:
        u.write(SUITE/'UPDATE_LOG.md',log+note)
    print('PASS: 21 values unchanged; A/C/D pixels identical; 15 other artwork pairs unchanged.',flush=True)


if __name__=='__main__':
    run()
