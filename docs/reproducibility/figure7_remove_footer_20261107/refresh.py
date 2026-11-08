"""Remove the entire Figure 7 annotation footer; preserve the maps and keys."""
from pathlib import Path
import io
import json
import sys

import fitz
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import consolidate_current_figure_suite as u
import build_current_suite_p2 as b
import figure7_final_presentation_20261016 as render

BASE='b3bf69a7334cfcea595994250bb873d7263a8393'
SUITE=ROOT/'results/figure_review_rq_aligned_20261101'
MIRROR=ROOT/'results/figures_rq_aligned_20261101'
QA=Path(__file__).resolve().parent


def remove_footer(raw):
    with fitz.open(stream=raw,filetype='pdf') as doc:
        page=doc[0]
        page.add_redact_annot(fitz.Rect(0,650,page.rect.width,page.rect.height),fill=None)
        page.apply_redactions(images=0,graphics=0)
        return doc.tobytes(garbage=4,deflate=True,no_new_id=True)


def run():
    old=u.payload(BASE,'results/figure_review_rq_aligned_20261101/Main/Fig07.pdf')
    new=remove_footer(old)
    assert new==remove_footer(old)
    with fitz.open(stream=old,filetype='pdf') as a,fitz.open(stream=new,filetype='pdf') as z:
        assert a[0].rect==z[0].rect
        aa=a[0].get_pixmap(dpi=150,alpha=False)
        zz=z[0].get_pixmap(dpi=150,alpha=False)
        before=np.frombuffer(aa.samples,dtype=np.uint8).reshape(aa.height,aa.width,3)
        after=np.frombuffer(zz.samples,dtype=np.uint8).reshape(zz.height,zz.width,3)
        edge=int(650*150/72)
        assert np.array_equal(before[:edge],after[:edge]),'A/B/C/D or legends changed'
        assert np.all(after[edge+2:]==255),'Footer is not empty'
        remaining=[span['text'] for block in z[0].get_text('dict')['blocks']
            for line in block.get('lines',[]) for span in line['spans'] if span['bbox'][1]>=650]
        assert remaining==[]
        png=z[0].get_pixmap(dpi=600,alpha=False).tobytes('png')
        u.write(QA/'Legend_and_empty_footer.png',z[0].get_pixmap(dpi=200,
            clip=fitz.Rect(0,622,z[0].rect.width,684),alpha=False).tobytes('png'))
    table_raw=u.payload(b.BASE,b.PB+'FROZEN_P2_TRACT_TABLE_2315.csv')
    weights_raw=u.payload(b.BASE,b.PB+'P2_STANDARDIZER_AND_WEIGHTS.csv')
    full=pd.read_csv(io.BytesIO(table_raw),dtype={'tract_id':str},float_precision='round_trip').sort_values('tract_id')
    table=full[full.Population.gt(0)].copy()
    weights=pd.read_csv(io.BytesIO(weights_raw),float_precision='round_trip')
    profile=render.profile_means(table,weights)
    numerical=render.display_qa(table,profile)
    assert numerical['screen']['joint_tracts']==94
    assert numerical['screen']['joint_population']==350799
    assert len(numerical['profile_rows'])==21 and len(numerical['ecdf_rows'])==18
    u.dump(SUITE/'QA/FIG07_DISPLAY_QA.json',numerical)
    manifest=u.csv_rows((SUITE/'FIGURE_MANIFEST.csv').read_bytes())
    baseline={row['final_name']:row['sha256'] for row in manifest}
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
            row['notes']='Map and legends only: no bottom explanatory text; numerical screening statistics remain in QA.'
    u.write_csv(MIRROR/'FIGURE_INDEX.csv',index)
    palette=json.loads((SUITE/'CURRENT_CLUSTER_PALETTE.json').read_text(encoding='utf-8'))
    palette['Figure7_layout']='7.2 x 9.5 in; map-forward layout; maps and legends only'
    palette['Figure7_summary_line_count']=0
    u.dump(SUITE/'CURRENT_CLUSTER_PALETTE.json',palette)
    for path in [SUITE/'README.md',MIRROR/'README.md']:
        text=path.read_text(encoding='utf-8').replace(
            'Figure 7 states the verified Q4/P75 overlap and prevalence.',
            'Figure 7 uses maps and legends only; numerical screening statistics remain in QA.')
        u.write(path,text)
    note=('\n## 2026-11-07 - Figure 7 explanatory footer removed\n\n'
          'Deleted the complete bottom annotation block and its generation calls. '
          'No replacement prose is added. Maps, legends, profile values and all other figures are unchanged. '
          'Scientific checks are retained separately in FIG07_DISPLAY_QA.json.\n')
    log=(SUITE/'UPDATE_LOG.md').read_text(encoding='utf-8')
    if note.strip() not in log:
        u.write(SUITE/'UPDATE_LOG.md',log+note)
    b.DEST,b.MIRROR_DEST=SUITE,MIRROR
    captions=u.captions((SUITE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8'))
    supplementary=(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf').read_bytes()
    b.packets(list(captions.items()),SUITE/'QA/COMPACT_PACKET_PAGE_REGISTRY.csv',{'Main/Fig07'})
    u.write(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf',supplementary)
    preserved={}
    for row in manifest:
        if not row['final_name'].startswith('Main/Fig07.'):
            assert u.sha(ROOT/row['current_source_file'])==baseline[row['final_name']]
            assert u.sha(ROOT/row['mirror_file'])==baseline[row['final_name']]
            preserved[row['final_name']]=baseline[row['final_name']]
    with fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as packet:
        assert len(packet)==16
        # The captions are separate; the artwork rectangle itself must be empty.
        assert not packet[6].get_textbox(fitz.Rect(0,650,518.4,684)).strip()
    u.dump(QA/'QA.json',dict(baseline=BASE,summary_line_count=0,
        footer_empty=True,other_figure7_pixels_identical=True,
        legends_preserved=True,preserved_artwork_sha256=preserved,
        deterministic_renderer=True,scientific_files_modified=False,
        source_table_sha256=u.digest(table_raw),source_weights_sha256=u.digest(weights_raw),
        new_figure_sha256=u.digest(new),packet_pages=16))
    print('PASS: entire footer deleted; maps, profiles and legends unchanged; packet updated.')


if __name__=='__main__':
    run()
