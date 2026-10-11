from controlled_audit import *
import subprocess,fitz
NORMAL_WT=Path(str(WT).replace('\\\\?\\',''))
TMP=NORMAL_WT/'_qa';TMP.mkdir(exist_ok=True)
POP=Path(r'C:\Users\yinch\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe')
rows=[]
for name in ['BUILT_ENV_MEASUREMENT_DIAGNOSTICS','CONTROLLED_FEATURE_COMPARISONS']:
 p=OUT/(name+'.pdf');doc=fitz.open(p)
 for num,page in enumerate(doc):
  spans=[s for b in page.get_text('dict')['blocks'] if b['type']==0 for l in b['lines'] for s in l['spans']]
  clipped=[s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))]
  rows.append({'file':p.name,'page':num+1,'width_mm':page.rect.width/72*25.4,'height_mm':page.rect.height/72*25.4,'minimum_font_pt':min(s['size'] for s in spans),'font_names':sorted({s['font'] for s in spans}),'raster_images':len(page.get_images()),'outside_page_text':clipped,'font_records':page.get_fonts(full=True)})
 subprocess.run([str(POP),'-r','150','-png',str(p),str(TMP/name)],check=True)
jdump('PDF_RENDER_AND_FONT_QA.json',{'pages':rows,'actual_visual_review_required':True,'no_formal_figures_edited':True})
print(json.dumps(rows,indent=2),flush=True)
