"""Independent review checks and deterministic replay, without plotting science."""
from pathlib import Path
import json
import subprocess
import sys

import fitz
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src/la_grid/plotting'))
import build_s6_main4_review as b
import consolidate_current_figure_suite as u
QA=Path(__file__).resolve().parent

def output_hashes():
    return {p.relative_to(ROOT).as_posix():u.sha(p) for folder in [b.DEST,b.MIRROR] for p in folder.rglob('*') if p.is_file()}

def run():
    before=output_hashes()
    b.main()
    after=output_hashes()
    assert before==after,'Review rebuild is not byte-stable'
    source_checks=[]
    manifest=u.csv_rows(b.source(b.SOURCE+'/FIGURE_MANIFEST.csv'))
    for row in manifest:
        for key in ['current_source_file','mirror_file']:
            assert u.sha(ROOT/row[key])==row['sha256']
            source_checks.append({'path':row[key],'sha256':row['sha256']})
    panel_qa=[]
    with fitz.open(b.DEST/'Main/Fig04.pdf') as doc:
        page=doc[0]
        with fitz.open(stream=b.source(b.SOURCE+'/Supplement/FigS06.pdf'),filetype='pdf') as original:
            for name,rect in [
                ('A',fitz.Rect(0,0,page.rect.width,240)),
                ('B',fitz.Rect(0,240,page.rect.width,400)),
                ('C',fitz.Rect(0,400,page.rect.width/2,page.rect.height)),
                ('D',fitz.Rect(page.rect.width/2,400,page.rect.width,page.rect.height))]:
                left=page.get_pixmap(dpi=150,clip=rect).samples
                right=original[0].get_pixmap(dpi=150,clip=rect).samples
                assert left==right,name
                panel_qa.append({'panel':name,'source_crop_sha256':u.digest(right),'review_crop_sha256':u.digest(left),'pixel_identical':True})
        spans=[s for block in page.get_text('dict')['blocks'] if block['type']==0 for line in block['lines'] for s in line['spans']]
        bounds=[s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))]
        assert not bounds,bounds
        info={'width_mm':page.rect.width*25.4/72,'height_mm':page.rect.height*25.4/72,
            'minimum_font_pt':min(s['size'] for s in spans),'vector_drawings':len(page.get_drawings()),
            'embedded_fonts':all(row[1] not in ('n/a','') for row in page.get_fonts()),
            'fonts':sorted({r[3] for r in page.get_fonts()}),'text_outside_page':bounds}
        page.get_pixmap(dpi=150).save(QA/'Figure4_native_preview.png')
    with fitz.open(b.DEST/'ALL_FIGURES_WITH_CAPTIONS.pdf') as doc:
        doc[3].get_pixmap(dpi=110).save(QA/'Figure4_packet_preview.png')
        sheet=Image.new('RGB',(1600,4*520),'#eeeeee');draw=ImageDraw.Draw(sheet)
        for i,page in enumerate(doc):
            pix=page.get_pixmap(dpi=42)
            img=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
            img.thumbnail((390,485))
            x=(i%4)*400+(400-img.width)//2;y=(i//4)*520+25
            sheet.paste(img,(x,y));draw.text(((i%4)*400+12,(i//4)*520+6),b.label(b.NEW[i]),fill='black')
        sheet.save(QA/'Complete_packet_contact.png')
    results={'source_commit':b.BASE,'deterministic_rebuild':before==after,
        'reproduced_output_count':len(after),'original_artwork_files_unchanged':source_checks,
        'panel_render_comparison':panel_qa,'figure4_vector_and_fonts':info,
        'output_hashes':after,
        'publication_source_modified':False,'models_or_simulations_executed':False}
    u.dump(QA/'VERIFICATION.json',results)
    print(json.dumps({k:v for k,v in results.items() if k not in ['output_hashes','original_artwork_files_unchanged']},indent=2))

if __name__=='__main__':run()
