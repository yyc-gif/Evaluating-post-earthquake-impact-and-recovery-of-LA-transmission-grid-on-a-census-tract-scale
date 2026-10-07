"""Author-requested supplement composition and display corrections.

Read saved offline summary rows; never execute mapping, trajectories or an
evaluation kernel. Reuse native PDF panels at their original physical scale.
"""
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from la_grid.paths import REPO_ROOT
from la_grid.plotting.refine_policy_cluster_presentation import streams, plain

ROOT=REPO_ROOT
REVIEW=ROOT/'results/figure_review'
HISTORY=ROOT/'provenance/figure_review_history/supplement_before_20261006'
MM=72/25.4
ARIAL='C:/Windows/Fonts/arial.ttf'
BOLD='C:/Windows/Fonts/arialbd.ttf'
KEYS=['impact-first','hospital-first','degree-first']
COLORS=['#ff7f00','#555555','#4daf4a']
LABELS=['Impact-first','Hospital-first','Degree-first']
MARKERS=['s','o','^']
GATES=['G0_NO_GATE','G1_BASELINE_050','G2_RELAXED_005','G3_STRICT_075']
METRIC='population_weighted_normalized_burden_hr'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def archive(key):
    p=REVIEW/'Supplement'/f'{key}.pdf'; saved=HISTORY/'Supplement'/p.name
    saved.parent.mkdir(parents=True,exist_ok=True)
    for suffix in ['.pdf','.png']:
        target=saved.with_suffix(suffix)
        if not target.exists():shutil.copy2(p.with_suffix(suffix),target)
    return saved

def place(page,doc,clip,x=0,y=0):
    r=fitz.Rect(*(v*MM for v in clip))
    page.show_pdf_page(fitz.Rect(x*MM,y*MM,x*MM+r.width,y*MM+r.height),doc,0,clip=r)

def text(page,label,x,y,size=9.5,bold=False,color=(0,0,0),center=False):
    page.insert_font(fontname='SuppArial',fontfile=ARIAL)
    page.insert_font(fontname='SuppArialBold',fontfile=BOLD)
    if center:x-=fitz.Font(fontfile=BOLD if bold else ARIAL).text_length(label,fontsize=size)/(2*MM)
    page.insert_text((x*MM,y*MM),label,fontsize=size,
                     fontname='SuppArialBold' if bold else 'SuppArial',color=color)

def replace_text(doc,replacements):
    spans=[(s,l) for b in doc[0].get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
    for x in streams(doc):
        raw=doc.xref_stream(x);new=re.sub(rb'\bBT\b.*?\bET\b',b'',raw,flags=re.S)
        if new!=raw:doc.update_stream(x,new)
    page=doc[0]
    page.insert_font(fontname='SuppArial',fontfile=ARIAL);page.insert_font(fontname='SuppArialBold',fontfile=BOLD)
    for s,l in spans:
        label=replacements.get(plain(s['text']),s['text'])
        rotation=90 if l['dir'][1]<-.5 else 270 if l['dir'][1]>.5 else 0
        col=tuple(((s['color']>>shift)&255)/255 for shift in [16,8,0])
        page.insert_text(s['origin'],label,fontsize=s['size'],rotate=rotation,color=col,
                         fontname='SuppArialBold' if 'Bold' in s['font'] else 'SuppArial')

def save(doc,key):
    p=REVIEW/'Supplement'/f'{key}.pdf';doc.save(p,garbage=4,deflate=True);doc.close()
    with fitz.open(p) as d:
        page=d[0];spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans']]
        assert min(s['size'] for s in spans)>=6.999,p
        assert all(page.rect.contains(fitz.Rect(s['bbox'])) for s in spans),p
        pix=page.get_pixmap(matrix=fitz.Matrix(600/72,600/72),alpha=False);pix.set_dpi(600,600);pix.save(p.with_suffix('.png'))
        preview=Path('C:/ABAQUS/temp/AppData/Local/Temp/la_supplement_spacing_20261006')/(key+'_after.png')
        preview.parent.mkdir(parents=True,exist_ok=True);page.get_pixmap(matrix=fitz.Matrix(1.9,1.9)).save(preview)
        return {'file':f'Supplement/{key}.pdf','sha256':sha(p),'size_mm':[185,round(page.rect.height/MM,2)],'min_font_pt':min(s['size'] for s in spans)}

def combined_hazard():
    damage=fitz.open(archive('FigS01'));service=fitz.open(archive('FigS02'))
    replace_text(service,{'A. Long Beach':'Long Beach','B. San Fernando':'San Fernando','C. Northridge':'Northridge','D. 2pc50':'2pc50'})
    out=fitz.open();p=out.new_page(width=185*MM,height=214*MM)
    place(p,damage,(0,0,185,65.1),y=6)
    text(p,'A. Substation damage severity',92.5,5,bold=True,center=True)
    text(p,'B. Initial modeled tract service availability',92.5,75,bold=True,center=True)
    place(p,service,(0,0,185,137),y=77)
    damage.close();service.close();return save(out,'FigS01')

def assumption_panels():
    """Display differences of existing summary rows, not a new evaluation."""
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial'],'font.size':7.5,
        'axes.titlesize':9.5,'axes.titleweight':'bold','axes.labelsize':8.5,'xtick.labelsize':7.5,
        'ytick.labelsize':7.5,'axes.linewidth':.6,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(185/25.4,85/25.4))
    fig.subplots_adjust(left=.16,right=.975,bottom=.26,top=.88,wspace=.76)
    shown=[];sources=[]
    for i,key in enumerate(KEYS):
        source=ROOT/f'Formal_Experiment_20260923/Formal_Offline_Evaluation/2pc50__C57_D1__{key}__SUMMARY.parquet'
        sources.append({'path':source.relative_to(ROOT).as_posix(),'sha256':sha(source)})
        d=pd.read_parquet(source);d=d[(d['mapping']=='M1_UTILITY_003')&(d.comparison_domain=='mapping_native_domain')]
        table=d.pivot(index='realization_id',columns='gate',values=METRIC)
        assert len(table)==1000 and set(GATES).issubset(table.columns)
        for gate,ax,offset,marker in [('G0_NO_GATE',axes[0],0,MARKERS[i]),('G2_RELAXED_005',axes[1],-.13,'o'),('G3_STRICT_075',axes[1],.13,'s')]:
            values=(table[gate]-table['G1_BASELINE_050']).to_numpy();mean=float(values.mean());lo,hi=np.quantile(values,[.05,.95]);y=i+offset
            ax.plot([lo,hi],[y,y],color=COLORS[i],lw=1.15)
            ax.scatter([mean],[y],c=COLORS[i],marker=marker,s=20,zorder=3,linewidths=.5)
            shown.append({'policy':key,'gate':gate,'reference':'G1_BASELINE_050','mean_h':mean,'p05_h':float(lo),'p95_h':float(hi),'n':1000})
        for ax in axes:ax.set_yticks(range(len(KEYS)),LABELS);ax.set_ylim(len(KEYS)-.4,-.6)
    axes[0].set_title('C. Service-requirement sensitivity',pad=8)
    axes[1].set_title('D. Functionality-threshold sensitivity',pad=8)
    for ax in axes:
        ax.axvline(0,color='#555555',lw=.65,zorder=0);ax.grid(axis='x',lw=.4,alpha=.25)
        ax.set_xlabel('Change in population-weighted\nservice loss (h)',labelpad=6)
    axes[1].legend(handles=[plt.Line2D([],[],marker='o',ls='none',color='#555555',ms=4,label='Threshold 0.05'),
        plt.Line2D([],[],marker='s',ls='none',color='#555555',ms=4,label='Threshold 0.75')],
        loc='lower center',bbox_to_anchor=(.5,-.42),ncol=2,frameon=False,fontsize=7.5,columnspacing=1,handletextpad=.4)
    axes[0].text(.5,-.4,'Threshold and source requirement removed',transform=axes[0].transAxes,ha='center',fontsize=7)
    temporary=Path('C:/ABAQUS/temp/AppData/Local/Temp/la_supplement_assumption_panels.pdf');fig.savefig(temporary);plt.close(fig)
    return temporary,shown,sources

def sensitivity():
    previous=fitz.open(archive('FigS06'));path,values,sources=assumption_panels();lower=fitz.open(path)
    out=fitz.open();p=out.new_page(width=185*MM,height=157*MM)
    place(p,previous,(0,0,185,71.5));place(p,lower,(0,0,185,85),y=72)
    previous.close();lower.close();stats=save(out,'FigS06');stats.update(displayed_summary=values,source_tables=sources)
    return stats

def smaller_station_circles():
    doc=fitz.open(archive('FigS07'));changed=[]
    # The circular Form is repeated at the two maps' station coordinates. It
    # is distinct from the triangular Core-source Form and curve operators.
    for x in sorted({x for p in doc for x,n,i,b in p.get_xobjects()}):
        raw=doc.xref_stream(x)
        if raw and len(raw)<1200 and raw.count(b' c')>=4 and b' l' not in raw:
            box=doc.xref_get_key(x,'BBox')[1];numbers=[float(v) for v in re.findall(r'-?\d+\.?\d*',box)]
            if len(numbers)==4 and max(abs(v) for v in numbers)<5:
                doc.update_stream(x,b'q\n0.8 0 0 0.8 0 0 cm\n'+raw+b'\nQ');changed.append(x)
    assert changed,'Station circle Form not found; refuse an unrelated marker change'
    stats=save(doc,'FigS07');stats['circular_station_diameter_factor']=.8;stats['circle_forms']=changed;return stats

def capacity_spacing():
    source=fitz.open(archive('FigS08'));out=fitz.open();p=out.new_page(width=185*MM,height=241.0*MM)
    place(p,source,(0,0,185,149))
    text(p,'B. Capacity-induced service loss within SCE-supported geography',34.22,154.6,bold=True)
    place(p,source,(0,162,185,245),y=158)
    source.close();return save(out,'FigS08')

def pca_alignment():
    source=fitz.open(archive('FigS09'));out=fitz.open();p=out.new_page(width=185*MM,height=174*MM)
    place(p,source,(0,8,100,87),y=8)
    place(p,source,(100,8,185,84.6),x=100,y=10.08)
    place(p,source,(0,87,185,174),y=87)
    palette=['#66c2a5','#fc8d62','#8da0cb','#e78ac3','#a6d854']
    for i,col in enumerate(palette):
        color=tuple(int(col[j:j+2],16)/255 for j in [1,3,5]);x=32+12*i
        p.draw_circle((x*MM,4.2*MM),1.8,color=color,fill=color,width=.4)
        text(p,f'C{i+1}',x+2,5.15,size=7.5)
    source.close();return save(out,'FigS09')

def run():
    audit=[combined_hazard(),sensitivity(),smaller_station_circles(),capacity_spacing(),pca_alignment()]
    p=ROOT/'docs/reproducibility/SUPPLEMENT_ASSUMPTIONS_LAYOUT_UPDATE_20261006.json'
    p.write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8');return audit

def integrate(audit):
    """Update the single author packet and its exact-copy publication index."""
    generator=Path(__file__).relative_to(ROOT).as_posix()
    changed={r['file'] for r in audit}
    def update_csv(path,fn):
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
        out=[]
        for row in rows:
            result=fn(row)
            if result is not None:out.append(result)
        with path.open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    def index(row):
        if row['figure_number']=='FigS02':return None
        source=ROOT/row['source_path'];rel=source.relative_to(REVIEW).as_posix()
        if Path(rel).with_suffix('.pdf').as_posix() in changed:
            shutil.copy2(source,ROOT/'results/figures'/row['file'])
            row.update(sha256_or_lfs_oid='sha256:'+sha(source),generator=generator,
                notes='Author-requested native-panel composition and display corrections; source scientific tables unchanged.')
            if rel.startswith('Supplement/FigS01'):
                row.update(scientific_question='How do station damage and initial community service vary across the four scenarios?',
                    scientific_content='Station damage severity and spatial initial modeled tract service availability',main_message='Damage and dependency-mediated service are distinct levels of the same hazard-to-community chain.')
            if rel.startswith('Supplement/FigS06'):
                row.update(scientific_question='What supports the production mapping, and how do cutoff and service assumptions affect modeled outcomes?',
                    scientific_content='Mapping cutoff, SCE-record agreement, threshold/source requirement and functionality-threshold sensitivities',
                    main_message='External mapping support is separate from sensitivity of modeled service to its assumptions.')
        return row
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    for retired in [REVIEW/'Supplement/FigS02.pdf',REVIEW/'Supplement/FigS02.png',
        ROOT/'results/figures/FigS02_Initial_Service.pdf',ROOT/'results/figures/FigS02_Initial_Service.png']:
        if retired.exists():
            original=HISTORY/'Supplement'/('FigS02'+retired.suffix)
            assert original.exists() and sha(retired)==sha(original),retired
            retired.unlink()
    def manifest(row):
        if row['final_name'].startswith('Supplement/FigS02'):return None
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key in changed:
            source=REVIEW/row['final_name'];before=HISTORY/row['final_name']
            row.update(parent_source_file=before.relative_to(ROOT).as_posix(),parent_source_commit='5bf3a86314eb0e028727b29382364a73ed773579',parent_sha256=sha(before),
                source_file=source.relative_to(ROOT).as_posix(),current_source_file=source.relative_to(ROOT).as_posix(),
                source_commit='SUPPLEMENT_DISPLAY_UPDATE_20261006',sha256=sha(source),status='AUTHOR_REQUESTED_CURRENT_DISPLAY')
            with fitz.open(source.with_suffix('.pdf')) as d:
                row['size_mm']=f'185 x {d[0].rect.height/MM:.2f}'
                row['min_font_pt']=f'{min(s["size"] for b in d[0].get_text("dict")["blocks"] for l in b.get("lines",[]) for s in l["spans"]):.2f}'
        return row
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    caption_path=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';content=caption_path.read_text(encoding='utf-8')
    for sentence in ['The four policy means are connected by solid lines, with filled markers.',
        'Cluster IDs 1–5 use the same explicit qualitative color mapping in A, C and Supplementary Figure S9.']:
        while (sentence+' '+sentence) in content:content=content.replace(sentence+' '+sentence,sentence)
    replacements={
        'Supplementary Figure S1.':'Supplementary Figure S1. Earthquake damage and initial modeled tract service',
        'Supplementary Figure S6.':'Supplementary Figure S6. Mapping support and service-assumption sensitivity'}
    parts=list(re.finditer(r'(?m)^## (.+)\n\n',content));sections=[]
    for i,m in enumerate(parts):
        title=m.group(1);body=content[m.end():parts[i+1].start() if i+1<len(parts) else len(content)].strip()
        if title.startswith('Supplementary Figure S2.'):continue
        if title.startswith('Supplementary Figure S1.'):
            title=replacements['Supplementary Figure S1.']
            body='(A) Station-specific mean damage states under Long Beach, San Fernando, Northridge and 2pc50, each based on 1,000 evaluation realizations. Boxes show the median and interquartile range across station means; whiskers extend to the most extreme observations within 1.5 interquartile ranges. All station means, including those beyond the whiskers, use the same dot style. This describes between-station heterogeneity, not a realization percentile range or confidence interval. (B) Initial modeled tract service availability averaged over the 1,000 realizations for each scenario, using the production utility-compatible tract–substation mapping. The four maps share their geographic extent and 0–1 service scale. Station damage and tract service describe different levels of the hazard-to-community chain: modeled tract service also depends on station functionality and source connectivity. Availability is not delivered electricity or MW. Historical scenarios and 2pc50 use different fragility parameterizations; the comparison does not isolate ground-motion intensity.'
        if title.startswith('Supplementary Figure S6.'):
            title=replacements['Supplementary Figure S6.']
            body='(A) Hospital-first population-weighted service-loss differences across mapping-weight cutoffs, relative to the 3% production cutoff. (B) Comparison with public SCE substation records for 337 comparable tracts. Distance-based baseline versus utility-compatible agreement is 320/337 versus 329/337 for any positive-weight assignment; 296/337 versus 302/337 for the highest-weight assignment; and 317/337 versus 324/337 for the three highest-weight assignments. Top assignments are ranked by positive mapping weight. This is supporting agreement, not accuracy, feeder validation or service-territory ground truth; the baseline is an external comparison, not a second production mapping. (C) Population-weighted service-loss changes when both the functionality threshold and the source-connectivity requirement are removed, relative to the production threshold of 0.5 with 14 Core sources. (D) Changes when the functionality threshold is 0.05 (circles) or 0.75 (squares), relative to 0.5; the same 14-source requirement is maintained. C/D use the production mapping, 2pc50, the reference crew allocation and repair-duration multiplier 1.00, and the same 1,000 realization identifiers within each policy. Dots show mean within-realization differences; lines show their 5th–95th realization ranges, not confidence intervals. Zero denotes no change. Loss integrals cover 0–480 h. C/D show Impact-first, Hospital-first and Degree-first, for which the saved formal gate summaries are available; the Vulnerability-first additions do not provide this gate grid. Crew and repair-duration scenario families are shown separately in Supplementary Figures S12 and S13.'
        if title.startswith('Supplementary Figure S9.'):
            body=body.replace('(A) PCA scores colored by the same cluster-ID palette as Figure 7.','(A) PCA scores colored by the same cluster-ID palette as Figure 7; C1–C5 in the panel key denote cluster IDs 1–5.')
        sections.append((title,body))
    prefix=content[:parts[0].start()]
    caption_path.write_text(prefix+'\n\n'.join('## '+title+'\n\n'+body for title,body in sections)+'\n',encoding='utf-8')
    lookup={}
    for title,body in sections:
        if title.startswith('Figure '):key=f'Main/Fig{int(title.split(".")[0].replace("Figure ","")):02}.pdf'
        elif title.startswith('Supplementary Figure S'):key=f'Supplement/FigS{int(title.split(".")[0].replace("Supplementary Figure S","")):02}.pdf'
        else:continue
        lookup[key]=(title,body)
    keys=[f'Main/Fig{i:02}.pdf' for i in range(1,8)]+[f'Supplement/FigS{i:02}.pdf' for i in [1]+list(range(3,14))]
    for name,folder in [('ALL_MAIN_FIGURES.pdf','Main'),('ALL_SUPPLEMENT_FIGURES.pdf','Supplement')]:
        if folder=='Main':continue # Every main artwork byte remains unchanged.
        book=fitz.open()
        for key in keys:
            if key.startswith(folder+'/'):
                with fitz.open(REVIEW/key) as d:book.insert_pdf(d)
        book.save(REVIEW/name,garbage=4,deflate=True);book.close()
    book=fitz.open()
    for key in keys:
        with fitz.open(REVIEW/key) as d:book.insert_pdf(d)
        title,body=lookup[key];p=book.new_page(width=185*MM,height=350*MM)
        p.insert_font(fontname='PacketArial',fontfile=ARIAL);p.insert_font(fontname='PacketArialBold',fontfile=BOLD)
        assert p.insert_textbox(fitz.Rect(14*MM,16*MM,171*MM,28*MM),title,fontname='PacketArialBold',fontsize=9.5)>=0,title
        assert p.insert_textbox(fitz.Rect(14*MM,31*MM,171*MM,333*MM),body,fontname='PacketArial',fontsize=9.2,lineheight=1.22)>=0,title
    assert len(book)==38
    book.save(REVIEW/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()
    authority=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';data=json.loads(authority.read_text(encoding='utf-8'))
    data['current_code_files']=[r for r in data['current_code_files'] if r['path']!=generator]+[{'path':generator,'sha256':sha(__file__),'tracked_in_current_git':True}]
    authority.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':integrate(run())
