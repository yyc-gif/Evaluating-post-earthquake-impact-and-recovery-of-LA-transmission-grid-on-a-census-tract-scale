"""Independent checks and hash manifest for the Figure 1 / S5 correction."""
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import build_s6_main4_review as builder

START_HEAD='5e10f48bbc2b8dc873cc9bda4ad575f8d683cd41'
SUITE=ROOT/'results/figure_review_s6_main4_20261107'
MIRROR=ROOT/'results/figures_s6_main4_20261107'
OUT=Path(__file__).resolve().parent
POINTER=re.compile(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n?')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(spec):
    return subprocess.check_output(['git','show',spec],cwd=ROOT)


def baseline_identity(path):
    raw=git_bytes(f'{START_HEAD}:{path}')
    match=POINTER.fullmatch(raw)
    if match:
        return match.group(1).decode(),int(match.group(2))
    return sha(raw),len(raw)


def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    manifest=rows(SUITE/'FIGURE_MANIFEST.csv')
    expected={f'{stem}.{ext}' for stem in builder.NEW for ext in ('pdf','png')}
    assert len(manifest)==32
    assert {row['final_name'] for row in manifest}==expected
    change_rows=[]
    for row in manifest:
        current=ROOT/row['current_source_file']
        mirror=ROOT/row['mirror_file']
        current_bytes=current.read_bytes()
        mirror_bytes=mirror.read_bytes()
        final_sha=sha(current_bytes)
        base_sha,base_size=baseline_identity(row['current_source_file'])
        assert mirror_bytes==current_bytes
        assert final_sha==row['sha256']
        change_rows.append({
            'figure':row['final_name'],'baseline_sha256':base_sha,
            'baseline_bytes':base_size,'final_sha256':final_sha,
            'final_bytes':len(current_bytes),'changed':str(final_sha!=base_sha).lower(),
            'mirror_sha256':sha(mirror_bytes),'mirror_matches':'true',
        })
    changed={r['figure'] for r in change_rows if r['changed']=='true'}
    expected_changed={
        'Main/Fig01.pdf','Main/Fig01.png',
        'Supplement/FigS05.pdf','Supplement/FigS05.png',
    }
    assert changed==expected_changed,sorted(changed)

    with fitz.open(SUITE/'Main/Fig01.pdf') as doc:
        fig1=doc[0]
        text=' '.join(fig1.get_text().replace('\u00ad','-').replace('\ufffd','-').split())
        required=(
            'Restoration Strategies and Execution','Unconstrained reference',
            'Priority rules and GA search','Fixed priorities include Vulnerability-first.',
            'GA search uses service-burden objective.','Finite crews schedule DS-specific tasks.',
            'Repair durations vary by damage state.','Directed road travel links tasks.',
            'Schedules set repair-completion times.','Raw station functionality set to 1',
            'Re-evaluate source connectivity','Update tract service through W',
        )
        assert all(value in text for value in required)
        assert abs(fig1.rect.width*25.4/72-185)<.01
        assert abs(fig1.rect.height*25.4/72-220)<.01
        region=[]
        for block in fig1.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line.get('spans',[]):
                    box=span['bbox']
                    if 481.7<box[1]<614.7 and 9.5<box[0]<256.3:
                        region.append(span)
                        assert box[0]>=9.5 and box[2]<=256.3 and box[3]<614.7
        region_text=' '.join(span['text'] for span in region).lower()
        assert 'modeled service availability curves' not in region_text
        assert 'time after earthquake' not in region_text
        fig1_pdf_png_equal=(fig1.get_pixmap(dpi=600,alpha=False).tobytes('png')==
                            (SUITE/'Main/Fig01.png').read_bytes())
        assert fig1_pdf_png_equal

    qa=json.loads((SUITE/'QA/NUMERICAL_AND_PRESERVATION_QA.json').read_text(encoding='utf-8'))
    assert qa['figure1_stage4_audit']['outside_stage4_pixels_identical']
    assert qa['figure1_stage4_audit']['illustrative_curves_removed']

    s5_pdf=SUITE/'Supplement/FigS05.pdf'
    s5_png=SUITE/'Supplement/FigS05.png'
    s5_preview=SUITE/'Page_Previews/FigS05.png'
    with fitz.open(s5_pdf) as doc:
        page=doc[0]
        assert abs(page.rect.width*25.4/72-185)<.01
        assert abs(page.rect.height*25.4/72-210)<.01
        s5_text=' '.join(page.get_text().split())
        for value in ('Impact-first','Hospital-first','Degree-first','Vulnerability-first',
                      'A. Mapping-weight cutoff','B. Source-connectivity gate',
                      'C. Functionality threshold'):
            assert value in s5_text
        assert page.get_pixmap(dpi=600,alpha=False).tobytes('png')==s5_png.read_bytes()
        assert page.get_pixmap(dpi=150,alpha=False).tobytes('png')==s5_preview.read_bytes()
        s5_images=len(page.get_images(full=True))
        s5_fonts=sorted({font[3] for font in page.get_fonts(full=True)})
    with Image.open(s5_png) as source_image:
        raster=np.asarray(source_image.convert('RGB'))
    visible=np.any(raster<248,axis=2)
    ys,xs=np.where(visible)
    margins={
        'dpi':600,'width_px':int(raster.shape[1]),'height_px':int(raster.shape[0]),
        'left_mm':float(185*xs.min()/raster.shape[1]),
        'right_mm':float(185*(raster.shape[1]-1-xs.max())/raster.shape[1]),
        'top_mm':float(210*ys.min()/raster.shape[0]),
        'bottom_mm':float(210*(raster.shape[0]-1-ys.max())/raster.shape[0]),
        'rgb_threshold':248,
    }
    assert abs(margins['left_mm']-margins['right_mm'])<1.0

    with fitz.open(SUITE/'ALL_MAIN_FIGURES.pdf') as main_book, \
         fitz.open(SUITE/'ALL_SUPPLEMENT_FIGURES.pdf') as supp_book, \
         fitz.open(SUITE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as complete, \
         fitz.open(s5_pdf) as art:
        assert (len(main_book),len(supp_book),len(complete))==(8,8,16)
        clip=fitz.Rect(0,0,art[0].rect.width,art[0].rect.height)
        page=complete[builder.NEW.index('Supplement/FigS05')]
        packet_identical=(page.get_pixmap(dpi=150,clip=clip,alpha=False).samples==
                          art[0].get_pixmap(dpi=150,alpha=False).samples)
        assert packet_identical
        assert 'A. Mapping-weight cutoff' in ' '.join(page.get_text().split())

    plot_rel='results/figure_review_s6_main4_20261107/QA/S5_VULNERABILITY_PLOT_DATA.json'
    committed=json.loads(git_bytes(f'{START_HEAD}:{plot_rel}'))
    plot_data=json.loads((ROOT/plot_rel).read_text(encoding='utf-8'))
    assert plot_data==committed
    audit=json.loads((SUITE/'QA/S5_VULNERABILITY_ARCHIVE_AUDIT.json').read_text(encoding='utf-8'))
    assert audit['plot_data_sha256']==sha((SUITE/'QA/S5_VULNERABILITY_PLOT_DATA.json').read_bytes())
    assert audit['status']=='PASS_FROZEN_EVENT_STATE_REANALYSIS'
    assert audit['condition']['physical_realizations_per_policy']==1000
    assert qa['s5_vulnerability_plot_audit']['no_recovery_model_or_schedule_rerun']

    identities=json.loads((SUITE/'QA/SOURCE_IDENTITIES.json').read_text(encoding='utf-8'))
    implementation={}
    for rel,item in identities['implementation_files'].items():
        current=(ROOT/rel).read_bytes()
        assert sha(current)==item['sha256']
        implementation[rel]=item['sha256']

    out={'starting_head':START_HEAD,'source_commit':identities['baseline'],
         'changed_artwork_pairs':sorted(changed),'all_other_artwork_pairs_unchanged':True,
         'figure1':{'page_mm':[185.0,220.0],'pdf_png_render_identical_600dpi':fig1_pdf_png_equal,
            'non_moduleD_content_pixel_identical_at_120dpi':True,
            'new_moduleD_text_and_bounds_verified':True,'illustrative_recovery_curves_removed':True},
         'supplement_s5':{'page_mm':[185.0,210.0],'pdf_png_render_identical_600dpi':True,
            'preview_matches_pdf_150dpi':True,'actual_600dpi_visible_margins':margins,
            'horizontal_margin_difference_mm':abs(margins['left_mm']-margins['right_mm']),
            'packet_figure_region_pixel_identical_at_150dpi':packet_identical,
            'embedded_fonts':s5_fonts,'raster_images':s5_images,
            'four_policies_and_three_panels_verified':True,
            'plot_data_value_structure_equal_to_starting_commit':True,
            'plot_data_sha256':sha((SUITE/'QA/S5_VULNERABILITY_PLOT_DATA.json').read_bytes()),
            'audit_sha256':sha((SUITE/'QA/S5_VULNERABILITY_ARCHIVE_AUDIT.json').read_bytes())},
         'figure_packet_pages':{'main':8,'supplement':8,'complete':16},
         'manifest_pairs':len(manifest),'mirrors_byte_identical':True,
         'generator_implementation_sha256':implementation,
         'scientific_models_or_schedules_rerun':False}
    (OUT/'FIGURE_SUITE_QA.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    (OUT/'ARTWORK_CHANGE_MANIFEST.json').write_text(
        json.dumps(change_rows,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,indent=2))


if __name__=='__main__':
    main()
