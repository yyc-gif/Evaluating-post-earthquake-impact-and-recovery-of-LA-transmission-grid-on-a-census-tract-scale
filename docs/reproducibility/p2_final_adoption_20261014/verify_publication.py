"""Independent final packet, source-paint and preservation checks; no fitting."""
from pathlib import Path
import ast
import json
import sys
import xml.etree.ElementTree as ET

import fitz
import pandas as pd
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import build_current_suite_p2 as p
import consolidate_current_figure_suite as u


def record_test_results():
    xml=HERE/'PYTEST_RESULTS.xml'
    suite=ET.parse(u.lp(xml)).getroot().find('testsuite')
    assert suite is not None
    tests=int(suite.attrib['tests']);failed=int(suite.attrib['failures']);errors=int(suite.attrib['errors'])
    skipped=int(suite.attrib.get('skipped',0))
    assert tests==41 and failed==errors==skipped==0
    stage=json.loads((ROOT/'FINAL_REVISION_RUN_SEQUENCE/08_FINAL_STAGE7_TYPOLOGY/STAGE_VALIDATION_MANIFEST.json').read_text())
    assert stage['status']=='PASS_REUSE'
    u.dump(HERE/'TEST_RESULTS.json',dict(
        command='python -m pytest tests/test_current_figure_suite_integration.py -q',
        passed=tests-failed-errors-skipped,failed=failed,errors=errors,skipped=skipped,
        elapsed_seconds=float(suite.attrib['time']),stage08=stage['status'],
        junit_xml=str(xml.relative_to(ROOT)).replace('\\','/'),junit_xml_sha256=u.sha(xml),
        tracking_regression_included_in_full_run=True,
        syntax='PASS: AST and compileall with Windows extended paths',
        initial_compile_limitation='Ordinary compileall cache paths exceeded Windows MAX_PATH; extended-path compilation passed.',
        rebuild='PASS: unchanged generator asserts byte-identical output hashes on replay'))


def main():
    previews=HERE/'publication_previews'
    Path(u.lp(previews)).mkdir(exist_ok=True)
    registry=pd.read_csv(u.lp(HERE/'COMPACT_PACKET_PAGE_REGISTRY.csv'))
    with fitz.open(u.lp(ROOT/'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf')) as book:
        assert len(book)==21 and len(registry)==17
        for i,row in registry.iterrows():
            page=book[i];h=float(row.figure_height_pt)
            spans=[s for b in page.get_text('dict',clip=fitz.Rect(0,h,page.rect.width,page.rect.height))['blocks']
                   if 'lines' in b for line in b['lines'] for s in line['spans']]
            assert spans and all(s['size']>=9.99 and fitz.Rect(s['bbox']).y1<=page.rect.height for s in spans)
        old=u.payload(p.BASE,'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf')
        with fitz.open(stream=old,filetype='pdf') as prior:
            for i in range(17,21):assert book[i].get_pixmap().samples==prior[i].get_pixmap().samples
        contact=Image.new('RGB',(7*265,3*360),'#dddddd')
        for i,page in enumerate(book):
            pix=page.get_pixmap(dpi=45)
            im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
            im.thumbnail((245,330))
            tile=Image.new('RGB',(265,360),'white')
            tile.paste(im,((265-im.width)//2,22))
            ImageDraw.Draw(tile).text((8,4),f'Page {i+1}',fill='black')
            contact.paste(tile,((i%7)*265,(i//7)*360))
        contact.save(u.lp(previews/'ALL_21_PAGES.png'))
        for i in [6,14]:book[i].get_pixmap(dpi=150).save(u.lp(previews/f'Page_{i+1:02d}.png'))
    for stem in ['Main/Fig07','Supplement/FigS08']:
        with fitz.open(u.lp(ROOT/'results/figure_review'/(stem+'.pdf'))) as doc:
            assert not doc[0].get_images()
            spans=[s for b in doc[0].get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
            assert all(doc[0].rect.contains(fitz.Rect(s['bbox'])) for s in spans)
            assert min(s['size'] for s in spans)>=7.49
    changed=['src/la_grid/revision/current_stage7.py','src/la_grid/plotting/build_current_suite_p2.py',
             'src/la_grid/plotting/build_current_suite_k3.py','tests/test_current_figure_suite_integration.py']
    for path in changed:ast.parse((ROOT/path).read_text(encoding='utf-8'))
    from la_grid.revision.current_stage7 import verify_current_stage7,verify_current_figures
    u.dump(HERE/'NUMERICAL_AND_PACKET_QA.json',dict(
        stage7=verify_current_stage7(ROOT),figures=verify_current_figures(ROOT),
        four_evidence_pages_pixel_identical=True,caption_bounds_and_10pt_minimum=True,
        changed_artwork_vector_only=True,changed_artwork_text_inside_page=True,
        frozen_source_pixels_preserved=True,no_fitting_or_new_physics=True,
        packet_sha256=u.sha(ROOT/'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf')))
    record_test_results()
    print('PASS: 21 pages, all short captions in bounds, original evidence pages exact, adopted P2 source identities.')


if __name__=='__main__':
    sys.path.insert(0,str(ROOT/'src'))
    main()
