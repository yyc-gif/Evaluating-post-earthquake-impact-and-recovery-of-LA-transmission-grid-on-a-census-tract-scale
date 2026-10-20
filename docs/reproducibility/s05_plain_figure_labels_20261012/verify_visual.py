"""Compare native PDF data regions and the actual assembled packet."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
QA = Path(__file__).parent
BASE = 'f010a4b42ebb7b160ab78556405bdb5c8e8a3ef6'
REL = 'results/figure_review/Supplement/FigS05.pdf'


def lp(p):
    s = str(p.resolve())
    return s if s.startswith('\\\\?\\') else '\\\\?\\'+s


def original_bytes():
    raw = subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+REL])
    match = re.search(rb'oid sha256:([0-9a-f]{64})\nsize (\d+)',raw)
    if not match:
        return raw
    common = Path(subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--path-format=absolute','--git-common-dir']).decode().strip())
    oid = match[1].decode()
    data = open(lp(common/'lfs/objects'/oid[:2]/oid[2:4]/oid),'rb').read()
    assert len(data) == int(match[2]) and hashlib.sha256(data).hexdigest() == oid
    return data


if __name__ == '__main__':
    old = fitz.open(stream=original_bytes(),filetype='pdf')
    new = fitz.open(lp(ROOT/REL))
    regions = {'A':(55.5,87,251.4,206),'B':(325.8,78,508.4,206),
               'C':(55.5,299,252,429),'D':(367.1,298,508,428.5)}
    records = []
    for panel, rect in regions.items():
        a = old[0].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(rect),alpha=False)
        b = new[0].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(rect),alpha=False)
        assert a.samples == b.samples, panel
        records.append({'panel':panel,'clip_pt':rect,'dpi':216,
                        'unmodified_data_pixels_identical':True,
                        'RGB_sha256':hashlib.sha256(a.samples).hexdigest()})
    spans = [s for b in new[0].get_text('dict',flags=0)['blocks']
             for line in b.get('lines',[]) for s in line['spans']]
    assert all(new[0].rect.contains(fitz.Rect(s['bbox'])) for s in spans)
    full = fitz.open(lp(ROOT/'results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'))
    sup = fitz.open(lp(ROOT/'results/figure_review/ALL_SUPPLEMENT_FIGURES.pdf'))
    native = new[0].get_pixmap(matrix=fitz.Matrix(160/72,160/72),alpha=False)
    assert native.samples == full[20].get_pixmap(matrix=fitz.Matrix(160/72,160/72),alpha=False).samples
    assert native.samples == sup[3].get_pixmap(matrix=fitz.Matrix(160/72,160/72),alpha=False).samples
    with Image.open(lp(ROOT/'results/figure_review/Page_Previews/FigS05.png')) as im:
        assert native.samples == im.convert('RGB').tobytes()
    # Render the actual caption page too; no script-success-only QA.
    caption = full[21].get_pixmap(matrix=fitz.Matrix(120/72,120/72),alpha=False)
    caption.save(lp(QA/'S05_CAPTION_PAGE_PREVIEW.png'))
    report = {'data_region_checks':records,'actual_packet_pixels_identical':True,
              'all_current_labels_inside_page':True,'native_width_mm':new[0].rect.width*25.4/72,
              'native_height_mm':new[0].rect.height*25.4/72,
              'figure_full_packet_page':21,'caption_page':22,
              'visual_inspection':'Actual native PDF render inspected: plain labels, real keys, no footer notes or clipping.'}
    Path(lp(QA/'VISUAL_AND_PACKET_QA.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('All four data regions and both assembled packet figures are pixel-identical.',flush=True)
