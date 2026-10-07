"""Apply author-requested policy and cluster display corrections to native PDFs.

No result calculation: coordinates, plotted values, intervals and map geometry
are retained. Only paint operators, reader-facing text and the Fig05 key move.
"""
from pathlib import Path
import copy
import csv
import hashlib
import json
import re
import shutil
import subprocess

import fitz
from pypdf.generic import ContentStream, DecodedStreamObject, FloatObject, ArrayObject
from la_grid.paths import REPO_ROOT

ROOT=REPO_ROOT
REVIEW=ROOT/'results/figure_review'
ARCHIVE=ROOT/'provenance/figure_review_history/policy_cluster_before_20261006'
MM=72/25.4
ARIAL='C:/Windows/Fonts/arial.ttf'
BOLD='C:/Windows/Fonts/arialbd.ttf'
DEGREE=(.30196078,.68627451,.29019608)
CLUSTER_OLD=['#303E4E','#C0A55B','#567E58','#BAD1DB','#724B63']
# ColorBrewer Set2 qualitative colors, explicitly assigned to cluster IDs 1–5.
CLUSTER_NEW=['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854']
RGB_PATTERN=re.compile(rb'([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s+([+-]?[0-9.]+)\s+(RG|rg)\b')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b):return a is not None and max(abs(x-y) for x,y in zip(a,b))<3e-5
def rgb(h):return tuple(int(h[i:i+2],16)/255 for i in [1,3,5])
def floats(a):return [FloatObject(x) for x in a]
def plain(s):return s.replace('\u00ad','-').replace('\u00a0',' ').replace('–','-').replace('−','-')

def streams(doc):
    return sorted({x for p in doc for x in p.get_contents()} |
                  {x for x in range(1,doc.xref_length()) if doc.xref_is_stream(x) and
                   doc.xref_get_key(x,'Subtype')[1]=='/Form'})

def paint(doc,key):
    """Fill existing Degree triangles without moving marker or interval vertices."""
    count=solid=0
    xrefs=streams(doc)
    triangle_names=set()
    for p in doc:
        for x,name,invoker,box in p.get_xobjects():
            raw=doc.xref_stream(x)
            if raw and len(raw)<400 and raw.count(b' l')==2 and re.search(rb'\bh\b',raw) and b' c' not in raw:
                triangle_names.add(name)
    for x in xrefs:
        raw=doc.xref_stream(x)
        # Parse only potentially affected chart streams, not large map paths.
        if not raw or not re.search(rb'0\.30196\d*\s+0\.68627',raw):continue
        obj=DecodedStreamObject();obj.set_data(raw);cs=ContentStream(obj,None)
        state={'stroke':None,'fill':None,'clip':None}; stack=[]; path=[]; output=[];changed=False;last_rectangle=None
        for args,op in cs.operations:
            if op==b'q':stack.append(copy.deepcopy(state))
            elif op==b'Q':state=stack.pop() if stack else {'stroke':None,'fill':None,'clip':None}
            elif op in [b'RG',b'rg']:
                state['stroke' if op==b'RG' else 'fill']=tuple(float(v) for v in args)
            elif op in [b'G',b'g']:
                state['stroke' if op==b'G' else 'fill']=(float(args[0]),)*3
            elif op in [b'm',b'l',b'c',b're']:
                if op==b'm':path=[]
                path.append(op)
                if op==b're' and key=='Fig05':last_rectangle=tuple(float(v) for v in args)
            if op==b'd' and key=='Fig05' and last_rectangle:
                xx,yy,ww,hh=last_rectangle
                # In native Matplotlib streams the dash operator precedes the
                # new curve color. Panel B contains exactly the four policies.
                if xx>300 and yy>450 and hh>80:
                    if len(args[0]):args=[ArrayObject(),FloatObject(0)];changed=True;solid+=1
            is_triangle=(op==b'Do' and str(args[0]).lstrip('/') in triangle_names) or (
                op in [b'B',b'B*',b'f',b'f*'] and path.count(b'm')==1 and path.count(b'l')==2 and b'c' not in path)
            if is_triangle and near(state['stroke'],DEGREE) and near(state['fill'],(1,1,1)):
                output.append((floats(DEGREE),b'rg'));state['fill']=DEGREE;count+=1;changed=True
            output.append((args,op))
            if op in [b'B',b'B*',b'f',b'f*',b'S',b's',b'n']:path=[]
        if changed:
            cs.operations=output;doc.update_stream(x,cs.get_data())
    return {'filled_degree_markers':count,'quartile_lines_made_solid':solid}

def palette(doc):
    counts=[0]*5
    for x in streams(doc):
        raw=doc.xref_stream(x)
        def change(m):
            color=tuple(float(m.group(i)) for i in [1,2,3])
            for i,old in enumerate(CLUSTER_OLD):
                if near(color,rgb(old)):
                    counts[i]+=1
                    return (' '.join(f'{v:.7f}' for v in rgb(CLUSTER_NEW[i]))+' '+m.group(4).decode()).encode()
            return m.group(0)
        new=RGB_PATTERN.sub(change,raw)
        if new!=raw:doc.update_stream(x,new)
    assert all(counts),counts
    return counts

def text_edits(doc,key):
    page=doc[0];edits=[];original_spans=[]
    centers={'A.':60,'B.':146,'C.':91.5,'D.':163,'E.':92.5}
    titles06={'A.':'A. Population-weighted service loss','B.':'B. Population-weighted service loss',
        'C.':'C. Q4 population-weighted service loss','D.':'D. Q4 population-weighted service loss',
        'E.':'E. High–low vulnerability service-loss gap','F.':'F. High–low vulnerability service-loss gap',
        'G.':'G. Hospital-linked mean service loss','H.':'H. Hospital-linked mean service loss'}
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            for s in line['spans']:
                original_spans.append((s,line))
                old=plain(s['text']);new=None;center=None;prefix=old[:2]
                if key=='Fig05' and prefix in centers:
                    new=s['text'];center=centers[prefix]*MM
                elif key=='Fig06' and prefix in titles06:
                    new=titles06[prefix];center=(59 if prefix in ['A.','C.','E.','G.'] else 149)*MM
                elif key in ['FigS12','FigS13'] and prefix in titles06:
                    new={'A.':'A. Population-weighted service loss','B.':'B. Q4 population-weighted service loss',
                         'C.':'C. High–low vulnerability service-loss gap','D.':'D. Hospital-linked mean service loss'}.get(prefix)
                elif key=='FigS11' and old=='C. Highest-vulnerability quartile':new='C. Q4 population-weighted'
                elif key=='FigS11' and old=='D. Hospital-linked tract mean':new='D. Hospital-linked mean'
                elif key=='FigS11' and old=='cumulative service loss':new='service loss'
                elif key=='FigS11' and old=='Long Beach':new='Long\nBeach';center=(s['bbox'][0]+s['bbox'][2])/2
                elif key=='FigS11' and old=='San Fernando':new='San\nFernando';center=(s['bbox'][0]+s['bbox'][2])/2
                elif key=='Fig04' and old=='All tracts:':new='Population-weighted'
                elif key=='Fig04' and old=='population-weighted':new='service'
                elif key=='Fig04' and old=='service loss (h)' and s['bbox'][1]>530:new='loss (h)'
                elif key=='Fig04' and old=='Highest-vulnerability':new='Q4 population-weighted'
                elif key=='Fig04' and old=='quartile service':new='service'
                elif key=='Fig04' and old=='tract mean service':new='mean service'
                elif key=='Fig04' and old=='Hospital-linked':new=old
                elif old.startswith('All-tract population-weighted'):new='Population-weighted'
                elif old=='All tracts':new='Population-weighted'
                elif old=='(population-weighted)':new='service loss'
                elif old=='Highest-vulnerability':new='Q4 population-weighted'
                elif old=='quartile service loss (h)':new='service loss (h)'
                elif old=='quartile (Q4)':new='service loss'
                elif old=='Hospital-linked':new='Hospital-linked mean'
                elif old=='tract mean':new='service loss'
                elif old=='Absolute Q4-Q1':new='High–low vulnerability'
                elif old=='separation':new='service-loss gap'
                elif old=='Absolute group-gap':new='High–low vulnerability gap'
                elif old in ['Absolute Q4-Q1 service-loss gap (h)','Absolute group separation (h)']:
                    new='High–low service-loss gap (h)'
                if new is not None:
                    edits.append((s,line,new,center))
    # Repaint text at its registered baseline instead of PDF redaction, which
    # can shift an unrelated text run in some composed Matplotlib pages.
    replacement={(s['text'],tuple(s['bbox'])):(label,center) for s,line,label,center in edits}
    for x in streams(doc):
        raw=doc.xref_stream(x)
        new=re.sub(rb'\bBT\b.*?\bET\b',b'',raw,flags=re.S)
        if new!=raw:doc.update_stream(x,new)
    page.insert_font(fontname='PolicyArial',fontfile=ARIAL);page.insert_font(fontname='PolicyArialBold',fontfile=BOLD)
    for s,line in original_spans:
        if key=='Fig05' and (s['bbox'][3]<21*MM or s['text'] in ['Hospital-first','Impact-first','Degree-first'] and 290<s['bbox'][1]<304):continue
        label,center=replacement.get((s['text'],tuple(s['bbox'])),(s['text'],None))
        bold='Bold' in s['font'];font=fitz.Font(fontfile=BOLD if bold else ARIAL)
        origin=fitz.Point(s['origin']);rotation=90 if line['dir'][1]<-.5 else 270 if line['dir'][1]>.5 else 0
        if key=='FigS11' and plain(label)=='Hazard scenario':origin.y+=9
        if center is not None:origin.x=center-max(font.text_length(t,fontsize=s['size']) for t in label.split('\n'))/2
        elif key=='Fig04' and rotation==0 and s['bbox'][1]>530:
            origin.x=(s['bbox'][0]+s['bbox'][2]-font.text_length(label,fontsize=s['size']))/2
        elif key=='Fig05' and rotation==0 and 315<s['bbox'][1]<410 and s['bbox'][2]<151:
            origin.x=s['bbox'][2]-font.text_length(label,fontsize=s['size'])
        if rotation and label!=s['text']:
            rect=fitz.Rect(s['bbox']);origin.y=rect.y1-(rect.height-font.text_length(label,fontsize=s['size']))/2
        color=tuple(((s['color']>>shift)&255)/255 for shift in [16,8,0])
        if '\n' in label:
            for i,t in enumerate(label.split('\n')):
                pt=fitz.Point(center-font.text_length(t,fontsize=s['size'])/2,origin.y+i*s['size']*1.15)
                page.insert_text(pt,t,fontname='PolicyArialBold' if bold else 'PolicyArial',fontsize=s['size'],color=color)
        else:
            page.insert_text(origin,label,fontname='PolicyArialBold' if bold else 'PolicyArial',
                             fontsize=s['size'],rotate=rotation,color=color)
    if key in ['FigS12','FigS13']:
        label='Crew-availability multiplier' if key=='FigS12' else 'Repair-duration multiplier'
        candidates=[s for s,l in original_spans if s['text']==label]
        if len(candidates)==3:
            lower=min(candidates,key=lambda s:-s['origin'][1]);right=max(candidates,key=lambda s:s['origin'][0])
            page.insert_text((right['origin'][0],lower['origin'][1]),label,fontname='PolicyArial',fontsize=right['size'])
    return len(edits)

def legend05(page):
    # Replace the existing top key, not the underlying scatter data.
    page.draw_rect(fitz.Rect(0,0,page.rect.width,21*MM),color=None,fill=(1,1,1))
    page.insert_font(fontname='PolicyArial',fontfile=ARIAL);page.insert_font(fontname='PolicyArialBold',fontfile=BOLD)
    rows=[(['Impact-first','Hospital-first','Degree-first','Vulnerability-first','Unconstrained'],5,True),
          (['Centrality-first','Betweenness-first','Closeness-first','Random'],15,False)]
    colors=['#ff7f00','#555555','#4daf4a','#a65628','#000000']
    for labels,y,bold in rows:
        widths=[fitz.Font(fontfile=BOLD if bold else ARIAL).text_length(label,fontsize=7.5)+22 for label in labels]
        start=(page.rect.width-sum(widths))/2
        for i,(label,width) in enumerate(zip(labels,widths)):
            secondary=['#e41a1c','#b59a00','#377eb8','#9a9a9a']
            col=rgb(colors[i]) if bold else tuple(.38*v+.62 for v in rgb(secondary[i]))
            cx=start+4;cy=y*MM-2;radius=2.1
            if bold and i==2:
                page.draw_polyline([(cx,cy-radius),(cx-radius,cy+radius),(cx+radius,cy+radius),(cx,cy-radius)],color=col,fill=col,width=.6)
            elif bold and i in [0,3]:
                if i==3:page.draw_polyline([(cx,cy-radius),(cx-radius,cy),(cx,cy+radius),(cx+radius,cy),(cx,cy-radius)],color=col,fill=col,width=.6)
                else:page.draw_rect(fitz.Rect(cx-radius,cy-radius,cx+radius,cy+radius),color=col,fill=col,width=.6)
            elif not bold and i==0:
                page.draw_polyline([(cx,cy+radius),(cx-radius,cy-radius),(cx+radius,cy-radius),(cx,cy+radius)],color=col,fill=col,width=.6)
            elif not bold and i in [1,2,3]:
                if i==1:
                    page.draw_line((cx-radius,cy),(cx+radius,cy),color=col,width=1.5)
                    page.draw_line((cx,cy-radius),(cx,cy+radius),color=col,width=1.5)
                else:
                    page.draw_line((cx-radius,cy-radius),(cx+radius,cy+radius),color=col,width=1.4 if i==2 else .7)
                    page.draw_line((cx-radius,cy+radius),(cx+radius,cy-radius),color=col,width=1.4 if i==2 else .7)
            else:page.draw_circle((cx,cy),radius,color=col,fill=col,width=.6)
            page.insert_text((start+12,y*MM),label,fontname='PolicyArialBold' if bold else 'PolicyArial',fontsize=7.5)
            start+=width
    # Explicitly redraw the common C/D reference key at its original location.
    page.draw_rect(fitz.Rect(248,291,432,304),color=None,fill=(1,1,1))
    for label,x,col,shape in [('Hospital-first',263.7,'#555555','o'),('Impact-first',328.2,'#ff7f00','s'),('Degree-first',388.2,'#4daf4a','^')]:
        c=rgb(col);cx=x-8;cy=297;z=2
        if shape=='o':page.draw_circle((cx,cy),z,color=c,fill=c,width=.6)
        elif shape=='s':page.draw_rect(fitz.Rect(cx-z,cy-z,cx+z,cy+z),color=c,fill=c,width=.6)
        else:page.draw_polyline([(cx,cy-z),(cx-z,cy+z),(cx+z,cy+z),(cx,cy-z)],color=c,fill=c,width=.6)
        page.insert_text((x,300),label,fontname='PolicyArial',fontsize=7.5)

def run(keys=None):
    ARCHIVE.mkdir(parents=True,exist_ok=True)
    audit=[]
    for p in sorted(list((REVIEW/'Main').glob('*.pdf'))+list((REVIEW/'Supplement').glob('*.pdf'))):
        if keys is not None and p.stem not in keys:continue
        key=p.stem;rel=p.relative_to(REVIEW);saved=ARCHIVE/rel
        original=saved if saved.exists() else p
        doc=fitz.open(original);stats=paint(doc,key)
        if key in ['Fig07','FigS09']:stats['cluster_color_operator_counts']=palette(doc)
        if key in ['Fig04','Fig05','Fig06','FigS11','FigS12','FigS13']:stats['text_edits']=text_edits(doc,key)
        if key=='Fig05':legend05(doc[0]);stats['legend_regrouped']=True
        if any(stats.values()):
            saved.parent.mkdir(parents=True,exist_ok=True)
            if not saved.exists():shutil.copy2(p,saved);shutil.copy2(p.with_suffix('.png'),saved.with_suffix('.png'))
            stats.update(file=rel.as_posix(),before_sha256=sha(original))
            temporary=p.with_suffix('.editing.pdf');doc.save(temporary,garbage=4,deflate=True);doc.close();temporary.replace(p)
            with fitz.open(p) as rendered:
                page=rendered[0];spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
                assert all(page.rect.contains(fitz.Rect(s['bbox'])) for s in spans),p
                px=page.get_pixmap(matrix=fitz.Matrix(600/72,600/72),alpha=False);px.set_dpi(600,600);px.save(p.with_suffix('.png'))
                page.get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(Path('C:/ABAQUS/temp/AppData/Local/Temp')/(key+'_after_policy_cluster.png'))
                stats['min_font_pt']=min(s['size'] for s in spans)
            stats['after_sha256']=sha(p);audit.append(stats)
            print(json.dumps(stats),flush=True)
        else:doc.close()
    audit_path=ROOT/'docs/reproducibility/POLICY_CLUSTER_DISPLAY_UPDATE_20261006.json'
    if keys is not None and audit_path.exists():
        replaced={r['file'] for r in audit}
        audit=[r for r in json.loads(audit_path.read_text()) if r['file'] not in replaced]+audit
    audit_path.write_text(json.dumps(audit,indent=2)+'\n')
    return audit

def integrate(audit):
    """Synchronize the existing author collection and its provenance records."""
    changed={row['file'] for row in audit}
    generator=Path(__file__).relative_to(ROOT).as_posix()
    def csv_update(path,change):
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
        for row in rows:change(row)
        with path.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    def index(row):
        source=ROOT/row['source_path'];rel=source.relative_to(REVIEW).as_posix()
        if str(Path(rel).with_suffix('.pdf')).replace('\\','/') not in changed:return
        shutil.copy2(source,ROOT/'results/figures'/row['file'])
        row.update(sha256_or_lfs_oid='sha256:'+sha(source),generator=generator,
                   notes='Author-requested marker, label and categorical-color corrections; scientific source unchanged.')
    csv_update(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    def manifest(row):
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key not in changed:return
        source=REVIEW/row['final_name']
        row.update(source_file=source.relative_to(ROOT).as_posix(),current_source_file=source.relative_to(ROOT).as_posix(),
                   source_commit='AUTHOR_REQUESTED_DISPLAY_UPDATE_20261006',sha256=sha(source),
                   status='AUTHOR_REQUESTED_CURRENT_DISPLAY')
    csv_update(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    path=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';content=path.read_text(encoding='utf-8')
    content=content.replace('open green triangles','filled green triangles')
    content=content.replace('The first key row contains the four emphasized policies shared by A/B; the second contains the five additional policies shown in A only.',
        'The first key row contains the four emphasized scheduled policies and the Unconstrained reference. The second contains the four other scheduled policies. Panel A includes all nine; Panel B includes only the four emphasized scheduled policies.')
    content=content.replace('for the four policies in the first key row','for the four emphasized scheduled policies in the first key row')
    content=content.replace('not boxplots, standard deviations or confidence intervals.',
        'not boxplots, standard deviations or confidence intervals. The four policy means are connected by solid lines, with filled markers.')
    content=content.replace('Absolute Q4–Q1 separation','The high–low vulnerability service-loss gap')
    content=content.replace('absolute Q4–Q1 separation','high–low vulnerability service-loss gap')
    content=content.replace('absolute-separation changes','high–low-gap changes')
    content=content.replace('per-realization absolute Q4–Q1 service-loss gap','high–low vulnerability service-loss gap within each realization')
    content=content.replace('per-realization absolute Q4–Q1 service-loss gap','high–low vulnerability service-loss gap within each realization')
    content=content.replace('community cluster under 2pc50;','community cluster under 2pc50;')
    content=content.replace('(C) Cluster membership for 2,291 eligible residential tracts.',
        '(C) Cluster membership for 2,291 eligible residential tracts. Cluster IDs 1–5 use the same explicit qualitative color mapping in A, C and Supplementary Figure S9.')
    path.write_text(content,encoding='utf-8')
    # Retain native figure widths and page dimensions in every collection.
    for name,folder,count in [('ALL_MAIN_FIGURES.pdf','Main',7),('ALL_SUPPLEMENT_FIGURES.pdf','Supplement',13)]:
        book=fitz.open()
        for i in range(1,count+1):
            stem=f'Fig{i:02}' if folder=='Main' else f'FigS{i:02}'
            with fitz.open(REVIEW/folder/(stem+'.pdf')) as doc:book.insert_pdf(doc)
        book.save(REVIEW/name,garbage=4,deflate=True);book.close()
    headings=list(re.finditer(r'(?m)^## (.+)\n\n',content));lookup={}
    for i,m in enumerate(headings):
        title=m.group(1);body=content[m.end():headings[i+1].start() if i+1<len(headings) else len(content)].strip()
        if title.startswith('Figure '):key=f'Main/Fig{int(title.split(".")[0].replace("Figure ","")):02}.pdf'
        elif title.startswith('Supplementary Figure S'):key=f'Supplement/FigS{int(title.split(".")[0].replace("Supplementary Figure S","")):02}.pdf'
        else:continue
        lookup[key]=(title,body)
    book=fitz.open()
    for key in [f'Main/Fig{i:02}.pdf' for i in range(1,8)]+[f'Supplement/FigS{i:02}.pdf' for i in range(1,14)]:
        with fitz.open(REVIEW/key) as doc:book.insert_pdf(doc)
        title,body=lookup[key];p=book.new_page(width=185*MM,height=350*MM)
        p.insert_font(fontname='PacketArial',fontfile=ARIAL);p.insert_font(fontname='PacketArialBold',fontfile=BOLD)
        assert p.insert_textbox(fitz.Rect(14*MM,16*MM,171*MM,28*MM),title,fontname='PacketArialBold',fontsize=9.5)>=0,title
        assert p.insert_textbox(fitz.Rect(14*MM,31*MM,171*MM,333*MM),body,fontname='PacketArial',fontsize=9.2,lineheight=1.22)>=0,title
    assert len(book)==40
    book.save(REVIEW/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()
    authority=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json'
    data=json.loads(authority.read_text(encoding='utf-8'));entry={'path':generator,'sha256':sha(__file__),'tracked_in_current_git':True}
    data['current_code_files']=[r for r in data['current_code_files'] if r['path']!=generator]+[entry]
    authority.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':integrate(run())
