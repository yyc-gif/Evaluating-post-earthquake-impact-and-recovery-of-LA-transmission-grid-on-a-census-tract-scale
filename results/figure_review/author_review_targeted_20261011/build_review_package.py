"""Native-size review sheets and narrow caption proposals; no model work."""
from common import *
import shutil,csv
from common import text as artwork_text
def text(*args,**kwargs):
    # Distinct packet fonts avoid collisions with embedded source font names.
    return artwork_text(*args,**kwargs,font_prefix='ReviewPacket20261011')

def paragraphs(doc,heading,body):
    p=doc.new_page(width=210*MM,height=297*MM)
    p.insert_font(fontname='ReviewHeading20261011',fontfile='C:/Windows/Fonts/arialbd.ttf')
    title_remaining=p.insert_textbox(fitz.Rect(12*MM,12*MM,198*MM,30*MM),heading,
        fontname='ReviewHeading20261011',fontsize=12,lineheight=1.2)
    assert title_remaining>=0,heading
    p.insert_font(fontname='CaptionArial',fontfile='C:/Windows/Fonts/arial.ttf')
    # Author-review prose only. The figure itself is never shrunk to fit.
    remaining=p.insert_textbox(fitz.Rect(12*MM,34*MM,198*MM,280*MM),body,fontname='CaptionArial',fontsize=10,lineheight=1.4)
    assert remaining>=0,(heading,remaining)
    return p

def compare(book,left,right,leftlabel,rightlabel,note):
    a=fitz.open(lp(PKG/left));b=fitz.open(lp(PKG/right))
    h=max(a[0].rect.height,b[0].rect.height)/MM
    p=book.new_page(width=400*MM,height=(h+35)*MM)
    text(p,102.5,12,leftlabel,11,True,True);text(p,297.5,12,rightlabel,11,True,True)
    for x,d in [(10,a),(205,b)]:
        p.show_pdf_page(fitz.Rect(x*MM,20*MM,(x+185)*MM,20*MM+d[0].rect.height),d,0)
    text(p,10,h+29,note,9)
    return p

def main():
    inputhash=json.load(open(lp(PKG/'SOURCE_HASHES.json'),encoding='utf-8'))
    rel='results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md';path,h=source(rel)
    current=open(lp(path),encoding='utf-8').read();inputhash[rel]={'commit':BASE,'sha256':h}
    for rel in ['results/figure_review/FIGURE_MANIFEST.csv','results/figure_review/Main/Fig04.pdf',
        'src/la_grid/plotting/clarify_outcome_measure_identity.py','src/la_grid/plotting/apply_map_metric_identity_feedback.py',
        'src/la_grid/plotting/refine_policy_cluster_presentation.py','src/la_grid/plotting/apply_coauthor_map_legend_feedback.py',
        'src/la_grid/revision/r1_vulnerability_first.py','src/la_grid/revision/r1_equity_amendment_execute.py']:
        p,h=source(rel);inputhash[rel]={'commit':BASE,'sha256':h}
    dump('SOURCE_HASHES.json',inputhash)
    headings=list(re.finditer(r'(?m)^## (.+)\n\n',current));caps={}
    for i,m in enumerate(headings):caps[m.group(1)]=current[m.end():headings[i+1].start() if i+1<len(headings) else len(current)].strip()
    keys=[next(k for k in caps if k.startswith(prefix)) for prefix in ['Figure 1.','Figure 3.','Figure 4.','Figure 5.','Figure 7.','Supplementary Figure S9.']]
    additions={keys[0]:'The Q1-Q4 bars in the distributional-effects illustration are schematic; their heights and the gap bracket are not estimated group means or numerical policy effects. Hospital-linked tracts may overlap the vulnerability quartiles.',
        keys[3]:'Thin dark outlines in E delimit Q4 areas using the frozen FEMA NRI v1.19 SOVI quartiles; internal boundaries between adjoining Q4 tracts are omitted for clarity. Vulnerability-first orders substation repair tasks using population-weighted Q4 tract dependency. It does not directly repair tract polygons or guarantee that every Q4 tract has lower service loss.'}
    proposed={k:caps[k]+(' '+additions[k] if k in additions else '') for k in keys}
    caption_text='# Proposed figure captions\n\n'+ '\n\n'.join('## '+k+'\n\n'+v for k,v in proposed.items())+'\n'
    with open(lp(PKG/'PROPOSED_CAPTIONS.md'),'w',encoding='utf-8',newline='\n') as f:f.write(caption_text)
    with open(lp(PKG/'CAPTION_CHANGE_LEDGER.md'),'w',encoding='utf-8',newline='\n') as f:
        f.write('# Caption changes\n\nOnly the additions below are proposed. Existing scientific qualifications and all numerical definitions are retained.\n\n')
        for k,v in additions.items():f.write('## '+k+'\n\nAppend: '+v+'\n\n')
        f.write('Figure 3, Figure 4, Figure 7 and S9 captions require no scientific wording change for these display edits. Their current text is reproduced in PROPOSED_CAPTIONS.md for review.\n')
    # Focused palette comparison: each E panel retains its native 95-mm crop.
    d=fitz.open();p=d.new_page(width=210*MM,height=112*MM)
    for x,path,label in [(5,'before/Fig03.pdf','Current'),(110,'Fig03_Low_End_Palette.pdf','Proposed: darker low end')]:
        src=fitz.open(lp(PKG/path));text(p,x+47.5,10,label,9,True,True)
        p.show_pdf_page(fitz.Rect(x*MM,16*MM,(x+95)*MM,95*MM),src,0,clip=fitz.Rect(90*MM,137*MM,185*MM,216*MM))
    text(p,5,105,'Native panel size; same values, normalization, ticks and tract geometries.',8)
    d.save(lp(PKG/'Fig03E_Palette_Comparison.pdf'),deflate=True,garbage=4)
    preview(d,'Fig03E_Palette_Comparison.png',600);preview(d,'qa/Fig03E_Palette_Comparison.png')
    # Complete comparisons: each full figure is physically 185 mm wide.
    sheets=fitz.open()
    pairs=[('before/Fig01.pdf','Fig01_Author_Review.pdf','Figure 1: current','Figure 1: author-review candidate','25% smaller markers; Stage5 schematic and coverage wording.'),
        ('before/Fig03.pdf','Fig03_Low_End_Palette.pdf','Figure 3: current','Figure 3: low-end palette candidate','Only the lowest quarter of the existing sequential palette changes.'),
        ('before/Fig05.pdf','Fig05_Q4_Context_Candidate.pdf','Figure 5: current','Figure 5: recommended Q4 context','Effect scales and A-D retained; Q4-area outlines add geographic context.'),
        ('before/Fig05.pdf','alternatives/Fig05_Quartile_Locator.pdf','Figure 5: current','Figure 5: locator alternative','Locator avoids overlays but increases total height to310 mm; not recommended.'),
        ('before/Fig07.pdf','alternatives/Fig07_Color_A.pdf','Figure 7: current','Figure 7: muted teal A','C4 only: #68a9b5 to #648890; other categorical and hotspot colors retained.'),
        ('before/Fig07.pdf','Fig07_Cluster_Color_Candidate.pdf','Figure 7: current','Figure 7: recommended slate-blue B','C4 only: #68a9b5 to #7b828f; same five formal clusters.'),
        ('before/FigS09.pdf','FigS09_Palette_Synchronization.pdf','S9: current','S9: synchronized C4','C4 matches Figure 7A/C; PCA coordinates and Panels B-D are unchanged.')]
    for a,b,la,lb,n in pairs:compare(sheets,a,b,la,lb,n+' Each figure: 185 mm; print 100%.')
    sheets.save(lp(PKG/'NATIVE_BEFORE_AFTER_CONTACT_SHEETS.pdf'),deflate=True,garbage=4)
    for i,p in enumerate(sheets):
        pix=p.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False);pix.save(lp(PKG/f'qa/Contact_{i+1:02}.png'))
    review=fitz.open()
    for file,k in zip(['Fig01_Author_Review.pdf','Fig03_Low_End_Palette.pdf','before/Fig04.pdf','Fig05_Q4_Context_Candidate.pdf','Fig07_Cluster_Color_Candidate.pdf','FigS09_Palette_Synchronization.pdf'],keys):
        src=fitz.open(lp(PKG/file));review.insert_pdf(src)
        paragraphs(review,k,proposed[k])
    review.save(lp(PKG/'AUTHOR_REVIEW_FIGURES_AND_CAPTIONS.pdf'),deflate=True,garbage=4)
    for i,p in enumerate(review):
        pix=p.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False);pix.save(lp(PKG/f'qa/Review_{i+1:02}.png'))
    records=json.load(open(lp(PKG/'ARTWORK_EDIT_RECORDS.json')))
    rows=[]
    for key,r in records.items():rows.append({'candidate':r['file'],'sha256':r['sha256'],
        'size_mm':' x '.join(f'{v:.3f}' for v in r['size_mm']),'minimum_font_pt':r['min_font_pt'],
        'baseline_commit':BASE,'status':'AUTHOR_REVIEW_ONLY'})
    with open(lp(PKG/'CANDIDATE_MANIFEST.csv'),'w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print('Native comparisons, captions and review packet created',flush=True)

if __name__=='__main__':main()
