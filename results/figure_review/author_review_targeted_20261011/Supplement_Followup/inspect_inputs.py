from pathlib import Path
import sys, json, shutil
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import common as c
P=Path(__file__).resolve().parent
c.PKG=P
records={}
for name in ['FigS03','FigS06','FigS07','FigS10','FigS11']:
    rel='results/figure_review/Supplement/'+name+'.pdf'
    p,h=c.source(rel)
    (P/'before').mkdir(exist_ok=True)
    shutil.copyfile(c.lp(p),c.lp(P/'before'/p.name))
    d=c.fitz.open(c.lp(P/'before'/p.name));page=d[0]
    c.preview(d,'qa/'+name+'_before.png',160)
    records[name]={'source':rel,'sha256':h,'size_mm':[page.rect.width/c.MM,page.rect.height/c.MM],
       'text':page.get_text(),'spans':c.spans(page),'images':page.get_images(),
       'drawings':len(page.get_drawings()),'forms':page.get_xobjects()}
    (P/'qa'/(name+'_streams.txt')).write_text('\n\n'.join(str(x)+'\n'+d.xref_stream(x).decode('latin1') for x in c.streams(d)),encoding='utf-8')
c.dump('INPUT_PDF_INSPECTION.json',records)
print(json.dumps({k:{'size_mm':v['size_mm'],'text':v['text']} for k,v in records.items()},indent=2))
