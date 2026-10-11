"""Render native Word exports for actual page inspection, without altering DOCX."""
import fitz
from common import *
render=ROOT/'_render'
lp(OUT/'Manuscript_CORE3_W1_Author_Review.pdf').write_bytes((render/'review.pdf').read_bytes())
records=[]
for kind in ['source','review']:
 d=fitz.open(render/(kind+'.pdf'));folder=render/kind;folder.mkdir(exist_ok=True)
 for i,p in enumerate(d):
  path=folder/f'page-{i+1:02d}.png';p.get_pixmap(matrix=fitz.Matrix(1.65,1.65),alpha=False).save(path)
  txt=p.get_text();assert txt.strip(),(kind,i)
  out=[]
  for b in p.get_text('dict')['blocks']:
   for line in b.get('lines',[]):
    for s in line['spans']:
     x0,y0,x1,y1=s['bbox']
     if x0<-.5 or y0<-.5 or x1>p.rect.width+.5 or y1>p.rect.height+.5:out.append(s['text'])
  records.append(dict(document=kind,page=i+1,width_pt=p.rect.width,height_pt=p.rect.height,chars=len(txt),text_outside_page=out,image_path=str(path),actual_visual_inspection='pending'))
 d.close()
dump('WORD_RENDER_QA.json',dict(renderer='Microsoft Word ExportAsFixedFormat; read-only copies; Close(SaveChanges=0)',native_export_pdf_sha256=sha(render/'review.pdf'),packaged_renderer_attempt='failed: unavailable soffice and Windows long-path support; no LibreOffice substitution or installation',pages=records))
log('Rendered source S19 (15 pages) and CORE3/W1 review (19 pages) with native Word; actual per-page inspection pending.')
