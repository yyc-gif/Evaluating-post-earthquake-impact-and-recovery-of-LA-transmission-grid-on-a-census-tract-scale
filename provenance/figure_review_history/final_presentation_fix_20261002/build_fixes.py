"""Bounded presentation fixes, using existing artwork and accepted display data.

No scientific-stage main(), simulation, bootstrap, dispatch, GA or clustering
is called. Output is an isolated review area; publication sources remain intact.
"""
from pathlib import Path
from collections import Counter
import importlib.util
import hashlib
import json
import re
import shutil
import subprocess

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
AUDIT = ROOT/'results/figure_review/promotion_readiness_4a4e9b5'
LAY = ROOT/'results/figure_review/candidate_v2.1_layout'
NEW = ROOT/'results/figure_review/fig06_resource_redesign_20261002'
SUITE = ROOT/'results/revised_suite/LA_Grid_Revised_Suite_20260925'
BASELINE = '5e7884610c40e5f3a0ea75b4f563756a31d1ba7b'
MM = 72/25.4
ARIAL = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
HAZARDS = ['LongBeach','SanFernando','Northridge','2pc50']
HN = dict(zip(HAZARDS,['Long Beach','San Fernando','Northridge','2pc50']))
HC = dict(zip(HAZARDS,['#366E9F','#9364A1','#9a7559','#a65628']))
HL = dict(zip(HAZARDS,['-','--','-.','-']))
ROWS = json.loads((AUDIT/'INVENTORY.json').read_text())
SOURCE = {r['figure']:ROOT/r['path'] for r in ROWS}
CAP = {r['figure']:r['caption'] for r in ROWS}
SOURCE_HASHES = {}; CHANGES = []; QA = []; PARITY = []


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def track(p):
    p=Path(p); SOURCE_HASHES[p.relative_to(ROOT).as_posix()]=sha(p); return p
def load(name, p):
    spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def styles():
    plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],
        'font.size':7.5,'axes.titlesize':9.5,'axes.labelsize':8.5,
        'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,
        'axes.linewidth':.6,'grid.linewidth':.4,'lines.linewidth':1.2,
        'patch.linewidth':.5,'pdf.fonttype':42,'ps.fonttype':42,
        'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})


def spans(page):
    return [(l,s) for b in page.get_text('dict')['blocks'] if 'lines' in b
            for l in b['lines'] for s in l['spans'] if s['text'].strip()]


def export_pdf(p):
    with fitz.open(p) as d:
        page=d[0]; ss=[s for _,s in spans(page)]
        bad=[s['text'] for s in ss if not page.rect.contains(fitz.Rect(s['bbox']))]
        assert not bad,(p.name,bad)
        assert min(s['size'] for s in ss)>=6.99,(p.name,min(s['size'] for s in ss))
        for dpi,suffix in [(600,''),(150,'_preview')]:
            px=page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
            px.set_dpi(dpi,dpi);px.save(str(p.with_name(p.stem+suffix+'.png')))
        view=fitz.open();v=view.new_page(width=210*MM,height=max(297*MM,page.rect.height+35*MM))
        v.insert_font(fontname='Arial',fontfile=ARIAL)
        v.insert_text((12.5*MM,10*MM),p.stem+' | native 185-mm review only',fontname='Arial',fontsize=8)
        v.show_pdf_page(fitz.Rect(12.5*MM,18*MM,197.5*MM,18*MM+page.rect.height),d,0)
        v.get_pixmap(matrix=fitz.Matrix(1.45,1.45),alpha=False).save(str(p.with_name(p.stem+'_page_preview.png')))
        view.close()
        resources=[]
        for f in d.get_page_fonts(0,full=True):
            name,ext,typ,data=d.extract_font(f[0]);resources.append((name,len(data)))
        assert all(n and size>0 and 'DejaVu' not in n for n,size in resources)
        QA.append({'file':p.name,'width_mm':page.rect.width/MM,'height_mm':page.rect.height/MM,
                   'minimum_font_pt':min(s['size'] for s in ss),'off_page_text':bad,
                   'fonts':sorted({s['font'] for s in ss}),'all_fonts_embedded':True,'sha256':sha(p)})


def save_fig(fig, key):
    p=OUT/(key+'.pdf');fig.savefig(p,dpi=600,facecolor='white');plt.close(fig);export_pdf(p);return p


def edit_pdf(key, select):
    """Replace selected text spans, retaining all graphical objects and values."""
    src=track(SOURCE[key]);dst=OUT/(key+'.pdf')
    with fitz.open(src) as d:
        p=d[0];edits=[]
        for line,s in spans(p):
            change=select(s,line,p)
            if change:
                edits.append((s,line,change));p.add_redact_annot(fitz.Rect(s['bbox']),fill=False)
        p.apply_redactions(images=0,graphics=0)
        p.insert_font(fontname='ArialFix',fontfile=ARIAL);p.insert_font(fontname='ArialFixBold',fontfile=BOLD)
        for s,l,c in edits:
            txt=c.get('text',s['text']);size=c.get('size',s['size'])
            bold=c.get('bold','Bold' in s['font']);fn='ArialFixBold' if bold else 'ArialFix'
            rgb=s['color'];color=c.get('color',((rgb>>16&255)/255,(rgb>>8&255)/255,(rgb&255)/255))
            angle=int(round(-np.degrees(np.arctan2(l['dir'][1],l['dir'][0]))))%360
            if c.get('exact_origin'):
                origin=s['origin']
            elif angle==0:
                b=fitz.Rect(s['bbox']);font=fitz.Font(fontfile=BOLD if bold else ARIAL)
                x=(b.x0+b.x1)/2-font.text_length(txt,fontsize=size)/2
                y=(b.y0+b.y1)/2+(font.ascender+font.descender)*size/2
                origin=(x,y)
            elif angle==90:
                b=fitz.Rect(s['bbox']);font=fitz.Font(fontfile=BOLD if bold else ARIAL)
                origin=((b.x0+b.x1)/2+(font.ascender+font.descender)*size/2,
                        (b.y0+b.y1)/2+font.text_length(txt,fontsize=size)/2)
            else:origin=s['origin']
            if '\n' in txt:
                # Explicit horizontal multiline replacement, no font shrink.
                lines=txt.split('\n');b=fitz.Rect(s['bbox']);font=fitz.Font(fontfile=BOLD if bold else ARIAL)
                cy=(b.y0+b.y1)/2+c.get('vertical_offset_mm',0)*MM;leading=size*1.13
                for i,t in enumerate(lines):
                    x=(b.x0+b.x1)/2-font.text_length(t,fontsize=size)/2
                    y=cy+(i-(len(lines)-1)/2)*leading+(font.ascender+font.descender)*size/2
                    p.insert_text((x,y),t,fontname=fn,fontsize=size,color=color)
            else:p.insert_text(origin,txt,fontname=fn,fontsize=size,color=color,rotate=angle)
        d.save(dst,garbage=4,deflate=True)
    export_pdf(dst);return dst


def framework():
    """Reflow original illustrated elements; every original word/edge retained."""
    original=track(SOURCE['Fig01']);src=fitz.open(original);p=src[0]
    old_words=Counter(re.findall(r'\S+',p.get_text().replace('\u00ad','-')))
    for _,s in spans(p):p.add_redact_annot(fitz.Rect(s['bbox']),fill=False)
    p.apply_redactions(images=0,graphics=0)
    # Original arrows are redrawn at their reflowed locations below. Clear
    # only their exact original gray paths to avoid clipped arrow fragments.
    arrow_rgb=(.3490196,.3882353,.4352941)
    connector_boxes=[v['rect'] for v in p.get_drawings() if v.get('color') and
                     all(abs(a-b)<.001 for a,b in zip(v['color'],arrow_rgb))]
    for r in connector_boxes:
        p.draw_rect(r+(-.12*MM,-.12*MM,.12*MM,.12*MM),color=None,fill=(1,1,1))
    d=fitz.open();q=d.new_page(width=185*MM,height=220*MM)
    q.insert_font(fontname='Arial',fontfile=ARIAL);q.insert_font(fontname='ArialBold',fontfile=BOLD)
    def text(x,y,t,size=7,bold=False,color=(.125,.145,.169),center=False):
        font=fitz.Font(fontfile=BOLD if bold else ARIAL)
        if center:x-=font.text_length(t,fontsize=size)/(2*MM)
        q.insert_text((x*MM,y*MM),t,fontname='ArialBold' if bold else 'Arial',fontsize=size,color=color)
    def clip(old,new,keep=True):q.show_pdf_page(fitz.Rect(*[x*MM for x in new]),src,0,clip=fitz.Rect(*[x*MM for x in old]),keep_proportion=keep)
    def card(rect,num,title,tint):
        r=fitz.Rect(*[x*MM for x in rect]);q.draw_rect(r,color=(.53,.58,.62),width=.6)
        q.draw_rect(fitz.Rect(r.x0,r.y0,r.x1,r.y0+5*MM),color=None,fill=tint)
        badge_colors=[(.18,.43,.62),(.72,.36,.29),(.48,.31,.56),(.137,.533,.475),(.30,.55,.37)]
        q.draw_circle(fitz.Point((rect[0]+2.5)*MM,(rect[1]+2.5)*MM),1.6*MM,
                      color=None,fill=badge_colors[int(num)-1])
        text(rect[0]+2.5,rect[1]+3.5,num,9.5,True,color=(1,1,1),center=True)
        text(rect[0]+5,rect[1]+3.8,title,9.5,True)
    def arrow(a,b,via=None):
        pts=[a]+(via or [])+[b]
        for u,v in zip(pts,pts[1:]):q.draw_line(fitz.Point(u[0]*MM,u[1]*MM),fitz.Point(v[0]*MM,v[1]*MM),color=(.35,.40,.44),width=.7)
        u=pts[-2];vx,vy=b[0]-u[0],b[1]-u[1];norm=(vx*vx+vy*vy)**.5;vx/=norm;vy/=norm
        end=np.array(b);side=np.array([-vy,vx]);base=end-np.array([vx,vy])*1.15
        tri=[end,base+side*.58,base-side*.58,end]
        q.draw_polyline([fitz.Point(x*MM,y*MM) for x,y in tri],color=(.35,.40,.44),fill=(.35,.40,.44),width=.5,closePath=True)
    # Original five stages and all internal/data-flow links, not a new diagram.
    q.draw_rect(fitz.Rect(3*MM,2*MM,182*MM,20*MM),color=(.53,.58,.62),width=.6)
    q.draw_rect(fitz.Rect(3*MM,2*MM,182*MM,7*MM),color=None,fill=(.92,.95,.97))
    text(5,6,'Data Inputs',9.5,True)
    clip([52,4,65.5,14],[28,7.2,43,19])
    for x,y,t,c,shape in [(47,10.2,'Transmission + substations',(.18,.43,.62),'o'),
        (117,10.2,'Scenario PGA fields',(.72,.36,.29),'o'),
        (47,17,'Roads + repair yards',(.78,.47,.12),'star'),
        (109,17,'Hospitals',(.48,.31,.56),'+'),(138,17,'Tract vulnerability',(.3,.55,.37),'s')]:
        if shape=='o':q.draw_circle(fitz.Point(x*MM,(y-.8)*MM),.55*MM,color=None,fill=c)
        elif shape=='s':q.draw_rect(fitz.Rect((x-.5)*MM,(y-1.3)*MM,(x+.5)*MM,(y-.3)*MM),color=None,fill=c)
        elif shape=='+':
            q.draw_line(fitz.Point((x-.6)*MM,(y-.8)*MM),fitz.Point((x+.6)*MM,(y-.8)*MM),color=c,width=1.0)
            q.draw_line(fitz.Point(x*MM,(y-1.4)*MM),fitz.Point(x*MM,(y-.2)*MM),color=c,width=1.0)
        else:
            for ang in [0,72,144,216,288]:
                q.draw_line(fitz.Point(x*MM,(y-.8)*MM),fitz.Point((x+.65*np.cos(np.deg2rad(ang)))*MM,(y-.8+.65*np.sin(np.deg2rad(ang)))*MM),color=c,width=.6)
        text(x+1.2,y,t,7.5)
    card([3,27,90.5,84],'1','Topology and Dependency Construction',(.91,.95,.97))
    card([94.5,27,182,84],'2','Seismic Damage Simulation',(.98,.94,.93))
    arrow([92.5,20],[46.75,27],[[92.5,23.5],[46.75,23.5]])
    arrow([92.5,20],[138.25,27],[[92.5,23.5],[138.25,23.5]])
    clip([20,24,43,38.5],[9,38,40,64]);clip([59,24,86.5,38.5],[49,38,82,64])
    for cx,t1,t2 in [(24.5,'LA direct-link topology','and source substations'),(65.5,'Tract–substation','dependency weights')]:
        text(cx,71,t1,center=True);text(cx,75,t2,center=True)
    clip([99,23.5,119.5,39],[98,42,122,68]);clip([123.5,25.5,135.7,37.2],[123.5,44,138.5,64])
    text(110,74,'Scenario PGA at',center=True);text(110,78,'substations',center=True)
    text(131,75.5,'Fragility functions',center=True)
    text(152.5,38,'Residual',center=True,color=(.35,.39,.44));text(152.5,42,'functionality',center=True,color=(.35,.39,.44))
    clip([146.6,27.1,159.4,37],[146.5,47,160,68],keep=False)
    for i in range(5):text(140.4,49.6+i*4.1,'DS'+str(i),color=(.35,.39,.44))
    text(172,38,'Repair-duration',center=True,color=(.35,.39,.44));text(172,42,'samples',center=True,color=(.35,.39,.44))
    clip([166.5,27.2,179.5,36],[168,47,180.5,68],keep=False)
    for i,ds in enumerate([4,3,2,1]):text(161.9,50.7+i*5.17,'DS'+str(ds),color=(.35,.39,.44))
    text(160,78,'Damage-conditioned outputs',center=True)
    card([3,94,182,153],'3','Damage-to-Service Translation',(.95,.93,.97))
    arrow([46.75,84],[46.75,94]);arrow([138.25,84],[138.25,94])
    text(8,105,'source topology + tract–substation weights',7,True,(.18,.43,.62))
    text(104,105,'damage states + functionality + repair durations',7,True,(.72,.36,.29))
    for old,new in [([4,53.5,27,73.5],[6,109,31,136]),([31,54,60,74],[40,109,65,136]),
                    ([64,53.5,89,74],[73,109,99,136]),([96.5,52,125.5,73],[111,109,137,136]),
                    ([140,53,178,74],[147,109,179,136])]:clip(old,new)
    for a,b in [(31,38),(65,71),(99,109),(137,145)]:arrow([a,122],[b,122])
    for cx,ys,ts in [(18.5,[145],['Damage states']),(52.5,[145],['Residual functionality']),
        (86,[142,146],['Source-gated functional','topology']),(124,[142,146],['Tract–substation','dependency weights']),
        (163,[145],['Tract-level service proxy'])]:
        for y,t in zip(ys,ts):text(cx,y,t,center=True)
    card([3,164,90.5,217],'4','Recovery Modeling',(.91,.96,.95))
    card([94.5,164,182,217],'5','Outputs and Interpretation',(.93,.97,.94))
    arrow([92.5,153],[46.75,164],[[92.5,158],[46.75,158]])
    arrow([90.5,190],[94.5,190])
    clip([4.5,87.5,28.5,105.5],[7,175,32,202]);text(11,182,'T80',7,color=(.72,.36,.29))
    clip([40,87.5,47.5,95.5],[43,175,53,187]);clip([31.5,96.4,55,105],[38,188,60,202])
    clip([58,87.5,83.5,105],[63,175,87,202]);arrow([32,189],[37,189]);arrow([60,189],[63,189])
    for cx,t1,t2 in [(19.5,'Unconstrained','baseline'),(49,'Crew/yard scheduling','+ priority strategies'),(75,'Logistics-aware','recovery')]:
        text(cx,208,t1,center=True);text(cx,212,t2,center=True)
    clip([94,87.5,121,106],[98,175,121,201])
    text(109.5,208,'Population- and',center=True);text(109.5,212,'SVI-weighted recovery',center=True)
    text(124,176,'sensitivity drivers',7,True,color=(.35,.39,.44))
    for y,t in zip([182,187,192,197],['crew availability','repair-time scale','IDW threshold','source-gate threshold']):text(124,y,t)
    clip([144,90.5,150.5,103.5],[149,180,154.5,199])
    text(139,210,'Sensitivity analysis',center=True)
    clip([157,86,179,105],[157,175,179,202])
    text(169,208,'Recovery-vulnerability',center=True);text(169,212,'typology / hotspots',center=True)
    # Exact wording multiset, excluding whitespace-only reflow: no new method.
    new_words=Counter(re.findall(r'\S+',q.get_text().replace('\u00ad','-')))
    assert old_words==new_words,{'deleted':old_words-new_words,'added':new_words-old_words}
    target=OUT/'Fig01_Submission_Layout_Candidate.pdf';d.save(target,garbage=4,deflate=True);d.close();src.close();export_pdf(target)
    relation_edges=['Inputs→1','Inputs→2','1→3','2→3','3→4','4→5',
                    'Damage→Residual','Residual→Source-gated','Source-gated→Weights','Weights→Tract service',
                    'Unconstrained→Crew/yard','Crew/yard→Logistics-aware']
    (OUT/'FIG01_WORDING_AND_EDGE_PARITY.json').write_text(json.dumps({'word_multiset_identical':True,'original_words':sum(old_words.values()),'minimum_candidate_font_pt':7,'arrows_same_relations':relation_edges,'illustrations':'Exact vector/image clips from protected July artwork; no new scientific illustration'},indent=2))
    pair=fitz.open();q=pair.new_page(width=420*MM,height=297*MM);q.insert_font(fontname='Arial',fontfile=ARIAL)
    with fitz.open(original) as a,fitz.open(target) as b:
        for x,doc,title in [(15,a,'Exact July reference: original 4.9-pt minimum'),(220,b,'Independent submission-layout candidate: 7-pt minimum')]:
            q.insert_text((x*MM,15*MM),title,fontsize=9.5,fontname='Arial')
            q.show_pdf_page(fitz.Rect(x*MM,22*MM,(x+185)*MM,22*MM+doc[0].rect.height),doc,0)
    pair.save(OUT/'FIG01_EXACT_ORIGINAL_VS_LAYOUT.pdf',garbage=4,deflate=True)
    q.get_pixmap(matrix=fitz.Matrix(1.45,1.45),alpha=False).save(str(OUT/'FIG01_EXACT_ORIGINAL_VS_LAYOUT.png'));pair.close()
    CAP['Fig01']='The exact July analytical framework, with identical wording, illustrated content and twelve directed relationships, reflowed into an independent 185-mm submission-layout candidate with normal text at least 7 pt. The exact original remains the unchanged provenance/reference artwork. No method is added or removed; this candidate is not promoted.'
    CHANGES.append(['Fig01','Original illustrations/wording/arrow relations reflowed; small type enlarged to 7 pt; independent candidate only.'])
    return target


def fig05(layout):
    def emit(fig,stem):
        layout.layout_05(fig);layout.common_style(fig)
        a,b=fig.axes[:2]
        for col,key in zip(b.collections,layout.v.STRATEGY_ORDER):
            if key not in layout.v.CORE_POLICIES and key!='unconstrained':col.set_alpha(.72)
        for k,cont in enumerate(a.containers):
            dx=(-.12,-.04,.04,.12)[k]
            line,caps,cols=cont.lines;line.set_xdata(np.asarray(line.get_xdata(),float)+dx)
            for cap in caps:cap.set_xdata(np.asarray(cap.get_xdata(),float)+dx)
            for col in cols:
                segs=col.get_segments()
                for s in segs:s[:,0]+=dx
                col.set_segments(segs)
        a.set_xlim(.70,4.30)
        g=fig.axes[6];layout.box(fig,g,158,121,21,24)
        g.set_yticklabels(['Impact','Hospital','Degree']);g.set_xlabel('Vulnerability-first\nminus reference\n(unitless)',fontsize=7.5)
        # Establish the latest candidate geometry before identity-only edits.
        before=layout.data_signature(fig)
        for lg in list(fig.legends):lg.remove()
        order=layout.v.STRATEGY_ORDER
        handles=layout.policy_handles(order)
        lg=layout.legend(fig,handles,105,4,ncol=3)
        for k,t in zip(order,lg.get_texts()):t.set_fontweight('bold' if k in layout.v.CORE_POLICIES else 'normal')
        fig.text(8/185,1-7/218,'Panel B key:\nall policies',fontsize=7,ha='left',va='top')
        # Short, explicit subset note inside existing title/legend white space.
        fig.text(46/185,1-19/218,'Panel A: Impact / Hospital / Degree / Vulnerability',fontsize=7,ha='left',va='bottom')
        refs=['impact-first','hospital-first','degree-first'];symbols=['s','o','^']
        c=fig.axes[5]
        for k,cont in enumerate(c.containers):
            j=k%3;cont.lines[0].set_marker(symbols[j])
            if j==2:
                cont.lines[0].set_markerfacecolor('white');cont.lines[0].set_markersize(3.1)
        for j,cont in enumerate(g.containers):
            cont.lines[0].set_marker(symbols[j])
            if j==2:cont.lines[0].set_markerfacecolor('white')
        rh=[]
        for ref,symbol in zip(refs,symbols):
            color=layout.v.STYLE[ref][0]
            rh.append(Line2D([],[],color=color,marker=symbol,lw=0,markersize=3.5,
                markerfacecolor='white' if ref=='degree-first' else color,
                label=layout.v.POLICY_LABEL[ref]+(' (additional)' if ref=='degree-first' else '')))
        # C/D reference key uses exactly the existing 109-mm row, not A/B.
        layout.legend(fig,rh,49,109,ncol=3,loc='upper left')
        assert layout.data_signature(fig)==before
        PARITY.append({'figure':'Fig05','plotted_values_geometry_identical_after_identity_fix':True})
        return save_fig(fig,'Fig05')
    layout.v.save_figure=emit
    layout.v.build_fig05(layout.base.read_eval(),layout.base.map_domain())
    CAP['Fig05'] += (' Panel A contains only Impact-first, Hospital-first, Degree-first and Vulnerability-first; the nine-policy key is explicitly for B. '
        'The C/D reference legend serves only C/D: Hospital-first is gray circle and Impact-first orange square, matching Fig06. '
        'Degree-first is an open green triangle, an additional reference-sensitivity comparator, not a predeclared primary reference. Gini changes remain unitless.')
    CHANGES.append(['Fig05','A/B legend applicability made explicit; C/D gray circle/orange square; additional Degree reference open triangle; all data/ranges unchanged.'])


def supp01(meeting):
    styles();parts=[]
    for h in HAZARDS:
        p=track(SUITE/'Stage 1 Output_expanded'/f'MC_Device_Damage_AvgDS_{h}.csv')
        d=pd.read_csv(p);assert len(d)==92
        parts.append(pd.DataFrame({'hazard':h,'value':d.avg_damage_state}))
    data=pd.concat(parts,ignore_index=True)
    fig,ax=plt.subplots(figsize=(185/25.4,65.1/25.4))
    sns.boxplot(data=data,x='hazard',y='value',hue='hazard',order=HAZARDS,palette=HC,saturation=1,legend=False,
                width=.48,linewidth=.7,fliersize=2,ax=ax)
    # Plot all existing station values; deterministic display offsets only.
    for k,h in enumerate(HAZARDS):
        vals=data[data.hazard.eq(h)].value.to_numpy();offset=.18*np.sin(np.arange(len(vals))*2.399963)
        ax.scatter(k+offset,vals,color='black',alpha=.22,s=1.8**2,zorder=3)
        PARITY.append({'figure':'FigS01','hazard':h,'station_values_count':len(vals),'source_file':str(p) if False else 'MC_Device_Damage_AvgDS_'+h+'.csv','value_hash':hashlib.sha256(vals.tobytes()).hexdigest()})
    ax.set_xticks(range(4),[HN[h] for h in HAZARDS]);ax.set_xlabel('Hazard scenario');ax.set_ylabel('Mean damage state')
    ax.set_ylim(0,4.1);ax.grid(axis='y',alpha=.2);fig.subplots_adjust(left=.13,right=.985,bottom=.27,top=.95)
    save_fig(fig,'FigS01')
    CAP['FigS01']='Station-specific mean damage states under Long Beach, San Fernando, Northridge and 2pc50. Each plotted station mean uses the accepted 1,000 evaluation damage realizations; each hazard contains 92 stations. Boxes show the station-value median and interquartile range; whiskers use the default 1.5-IQR rule, with fliers and all station points displayed. These describe between-station heterogeneity, not 5th–95th realization intervals or confidence intervals. Order, names and colors follow Fig03. Historical scenarios and 2pc50 use different adopted fragility parameterizations; differences are not pure PGA effects.'
    CHANGES.append(['FigS01','Hazard order/name/palette matches Fig03; same station means and default 1.5-IQR boxes; caption states statistical object.'])


def supp02():
    styles();p=track(SUITE/'Stage 1 Output_expanded/S1_S2_FROZEN_TRACT_INITIAL_AND_T80.csv');data=pd.read_csv(p)
    fig,ax=plt.subplots(figsize=(185/25.4,67/25.4))
    for h in HAZARDS:
        val=np.sort(data.loc[data.hazard.eq(h),'mean_initial_service_proxy'].to_numpy());assert len(val)==2315
        ax.plot(val,np.arange(1,len(val)+1)/len(val),color=HC[h],ls=HL[h],lw=1.4 if h=='2pc50' else 1.2,label=HN[h],zorder=5,clip_on=False if h=='2pc50' else True)
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean modeled tract service availability (0–1)',ylabel='Cumulative share of tracts')
    ax.set_title('A. Initial modeled tract service',loc='left',fontweight='bold')
    ax.spines['left'].set_position(('outward',3));ax.spines['left'].set_zorder(0)
    ax.legend(frameon=False,loc='lower right');ax.grid(alpha=.2);fig.subplots_adjust(left=.13,right=.985,bottom=.24,top=.89)
    upper=OUT/'_S02_upper.pdf';fig.savefig(upper);plt.close(fig)
    doc=fitz.open();q=doc.new_page(width=185*MM,height=202*MM)
    with fitz.open(upper) as a:q.show_pdf_page(fitz.Rect(0,0,185*MM,67*MM),a,0)
    with fitz.open(track(SOURCE['FigS02'])) as old:
        # Keep original map geometries and 0-1 scale, merely rearrange hazards.
        for clip,dest in [([1,137,83,201],[1,70,83,134]),([86,70,160,134],[86,70,160,134]),
                          ([1,70,83,134],[1,137,83,201]),([86,137,160,201],[86,137,160,201]),
                          ([162,92,185,175],[162,92,185,175])]:
            q.show_pdf_page(fitz.Rect(*[v*MM for v in dest]),old,0,clip=fitz.Rect(*[v*MM for v in clip]),keep_proportion=False)
    # Replace only map/cbar titles, preserving numeric scale and map paths.
    edits=[]
    for line,s in spans(q):
        t=s['text']
        names={'Long Beach':'B. Long Beach','San Fernando':'C. San Fernando','Northridge':'D. Northridge','2%-in-50 yr':'E. 2pc50'}
        if (t in names and s['bbox'][1]>67*MM) or 'tract-level supply' in t:
            edits.append((line,s,names.get(t,'Mean modeled tract service availability (0–1)')))
            q.add_redact_annot(fitz.Rect(s['bbox']),fill=False)
    q.apply_redactions(images=0,graphics=0);q.insert_font(fontname='Arial',fontfile=ARIAL);q.insert_font(fontname='ArialBold',fontfile=BOLD)
    for line,s,t in edits:
        b=fitz.Rect(s['bbox']);f=fitz.Font(fontfile=ARIAL);size=8.5 if 'availability' in t else 9.5
        if line['dir'][0]==0:
            pos=((b.x0+b.x1)/2+(f.ascender+f.descender)*size/2,(b.y0+b.y1)/2+f.text_length(t,fontsize=size)/2);angle=90
        else:
            f=fitz.Font(fontfile=BOLD)
            centers={'B. Long Beach':(43,72.5),'C. San Fernando':(123,72.5),'D. Northridge':(43,139.5),'E. 2pc50':(123,139.5)}
            cx,cy=centers[t];pos=(cx*MM-f.text_length(t,fontsize=size)/2,cy*MM);angle=0
        q.insert_text(pos,t,fontname='Arial' if angle else 'ArialBold',fontsize=size,rotate=angle)
    dst=OUT/'FigS02.pdf';doc.save(dst,garbage=4,deflate=True);doc.close();upper.unlink();export_pdf(dst)
    CAP['FigS02']='Initial modeled tract service availability under four hazard scenarios, with order/color/line identity following Fig03. A is the ECDF across 2,315 tract-level means over 1,000 saved realizations per hazard; B–E show the corresponding tract-level mean maps. All panels use the unchanged production utility-compatible mapping JULY_UTILITY_CONSTRAINED_92 and all maps use the same extent and 0–1 service scale. Availability is a modeled dependency-weighted service proxy, not delivered electricity or MW. Historical hazards and 2pc50 have different adopted fragility parameterizations; this is not pure PGA sensitivity. No physical realization or mapping was regenerated.'
    CHANGES.append(['FigS02','Fig03 hazard order/palette/dashes applied; supplied wording replaced by modeled service availability; map geometry and common scale preserved.'])


def supp03():
    def choose(s,l,p):
        if s['size']>=13:
            t=('A. Crew origins (57 modeled crews)' if 'Crew origins' in s['text'] else 'B. Directed task-to-task travel')
            return {'text':t,'size':9.5,'bold':True}
        if s['size']>=11:return {'size':8.5}
        if s['size']>=9:return {'size':7.5}
    edit_pdf('FigS03',choose)
    CAP['FigS03']='Model input context. A shows the existing 57-crew origin allocation and 92 substations on the study-area tract background. B displays the saved directed task-to-task road travel matrix; rows are origins, columns destinations, and time is in hours. Crew origins and travel are inputs to the logistics model, not estimates of the resource-response outcomes. Geometry, travel entries and crew allocation are unchanged.'
    CHANGES.append(['FigS03','Global A/B added; native graphics retained; typography aligned to 9.5/8.5/7.5-pt hierarchy.'])


def supp04(layout):
    styles();fig=plt.figure(figsize=(185/25.4,244.4/25.4))
    def axbox(top,height,left=24,width=155):return fig.add_axes([left/185,(244.4-top-height)/244.4,width/185,height/244.4])
    a=axbox(16,37);b=axbox(92,34);c=axbox(145,34);d=axbox(195,37,left=35,width=142)
    attack=[('impact','Network λ2 impact','#ff7f00',':'),('random','Random removal','#888888','-'),
            ('degree','Degree','#4daf4a','--'),('betweenness_centrality','Betweenness','#b59a00','-.'),('closeness_centrality','Closeness','#377eb8',(0,(4,1.6)))]
    for stem,label,color,ls in attack:
        p=track(SUITE/'Stage 2 Output_expanded'/((f'percolation_curve_{stem}.csv') if stem in {'impact','random'} else f'exploratory_percolation_curve_{stem}.csv'))
        v=pd.read_csv(p);a.plot(v.nodes_removed,v.lcc_fraction,color=color,ls=ls,lw=1,label=label)
    a.set(xlabel='Stations removed',ylabel='Largest-component fraction',ylim=(-.02,1.04));a.grid(alpha=.2)
    a.set_title('A. Static station-removal criticality',loc='left',fontweight='bold')
    a.legend(frameon=False,ncol=3,fontsize=7,loc='upper right')
    p=track(SUITE/'Stage 6 Output_expanded/NETWORK_TOPOLOGY_DISPLAY_CURVES_2pc50.csv');network=pd.read_csv(p)
    keys=layout.v.STRATEGY_ORDER
    handles=[]
    for key in keys:
        v=network[network.strategy_id.eq(key)].sort_values('time_hr');color,ls=layout.v.STYLE[key]
        for ax,col in [(b,'mean_lcc_fraction'),(c,'mean_lcc_average_degree')]:ax.plot(v.time_hr,v[col],color=color,ls=ls,lw=1.2 if key in layout.v.CORE_POLICIES else .95,alpha=1 if key in layout.v.CORE_POLICIES or key=='unconstrained' else .75)
        handles.append(Line2D([],[],color=color,ls=ls,label=layout.v.POLICY_LABEL[key],lw=1.2))
    fig.legend(handles=handles,frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.55,1-66/244.4),fontsize=7.5)
    for ax,title,ylabel in [(b,'B. Largest connected component','LCC size / 92 stations'),(c,'C. Active-network average degree','Mean degree within LCC')]:
        ax.set_title(title,loc='left',fontweight='bold');ax.set(xlim=(0,120),ylabel=ylabel);ax.grid(alpha=.2)
    b.set_ylim(-.02,1.04);c.set_xlabel('Time after earthquake (h)')
    p=track(SUITE/'Stage 6 Output_expanded/SOURCE_PATH_PAIRED_EFFECT_DISPLAY.csv');data=pd.read_csv(p);data=data[data.hazard.eq('2pc50')].set_index('strategy_id')
    names=[k for k in keys if k not in {'hospital-first','unconstrained'}]
    for i,key in enumerate(names):
        r=data.loc[key];color=layout.v.STYLE[key][0];y=len(names)-1-i
        d.hlines(y,r.p05_paired_delta_hr,r.p95_paired_delta_hr,color=color,lw=1.1)
        d.plot(r.mean_paired_delta_hr,y,marker='s' if key=='impact-first' else 'o',color=color,ls='none',ms=3.5)
    d.axvline(0,color='#666666',lw=.65,ls='--');d.set_yticks(range(len(names)),[layout.v.POLICY_LABEL[k] for k in names[::-1]])
    d.set_title('D. Source-path-related cumulative loss',loc='left',fontweight='bold')
    d.set_xlabel('Change relative to Hospital-first (h), 5–95% realization range');d.grid(axis='x',alpha=.2)
    save_fig(fig,'FigS04')
    CAP['FigS04']='Network mechanism support under the existing model. A shows static targeted-versus-random station removal: Network λ2 impact refers to the topology-impact attack metric, not the population-oriented Impact-first repair policy; removal curves are not optimal repair sequences. B/C show the saved mean functional-network largest-connected-component fraction (normalized by 92) and average degree within that component during 2pc50 recovery, over the displayed 0–120 h, for all eight distinct scheduled policies plus Unconstrained under C57_D1. They are mean display curves, with no interval encoded. D uses the accepted 0–480 h integrated source-path-related loss component: dots are mean candidate-minus-Hospital-first differences, and horizontal intervals are 5th–95th matched-realization ranges over the same 1,000 damage/duration realizations, not confidence intervals. Colors and policy line styles follow Fig04; source reachability is not delivered MW or electrical adequacy. Direct-community is sequence-equivalent to Impact-first and not separately reported.'
    CHANGES.append(['FigS04','Unique A–D hierarchy; λ2 attack distinguished from repair policy; dynamic policy lines match main identity; saved curves and paired interval endpoints retained.'])


def supp06(meeting,layout):
    def emit(fig,stem,**kwargs):
        before=layout.data_signature(fig);ax=fig.axes[1]
        for line in ax.lines:
            if line.get_marker()=='o':line.set_color('#8d989f')
            elif line.get_marker()=='D':line.set_color('#386f8e');line.set_marker('o')
        ax.set_yticks([2,1,0],['Any candidate','Top-1 candidate','Top-3 candidates'])
        for txt in ax.texts:
            txt.set_color('#8d989f' if txt.get_color()=='#28618a' else '#386f8e')
        for lg in list(fig.legends):lg.remove()
        fig.legend(handles=[Line2D([],[],marker='o',color='none',markerfacecolor='#8d989f',markeredgecolor='#8d989f',ms=3.8,label='Distance-based baseline'),
            Line2D([],[],marker='o',color='none',markerfacecolor='#386f8e',markeredgecolor='#386f8e',ms=3.8,label='Utility-compatible')],
            frameon=False,loc='upper center',bbox_to_anchor=(.5,.99),fontsize=7,ncol=2)
        assert layout.data_signature(fig)==before
        PARITY.append({'figure':'FigS06','data_coordinates_and_geometry_identical_after_mapping_identity_fix':True})
        return save_fig(fig,'FigS06')
    meeting.save_figure=emit;meeting.plot_supp_fig06()
    CAP['FigS06']='Mapping sensitivity and public-site support. A shows the accepted Hospital-first/2pc50 cutoff comparison relative to the 3% production cutoff; no new mapping is created. B compares the distance-based baseline and utility-compatible production mapping over exactly the same 337 comparable SCE tracts: any-match 320/337 versus 329/337; top-1 296/337 versus 302/337; top-3 317/337 versus 324/337. Top-k means retained positive station candidates ranked by mapping weight, with a match to at least one public-site candidate among the stated k; it is not a general nearest-site definition. These are public-site agreement/support, not accuracy, feeder validation or service-territory ground truth. C shows accepted four-hazard aggregate mapping effects. D shows absolute tract mean mapping-effect magnitudes under 2pc50/Hospital-first: 246 of 2,315 exceed 1 h. That count describes mapping sensitivity, not policy benefits or statistical significance. Numerical contrasts integrate over 0–480 h.'
    CHANGES.append(['FigS06','Mapping gray-circle/blue-circle identity matches Fig02 D; retained-weight top-k labels and caption definitions corrected; 337/246 counts unchanged.'])


def supp07(layout):
    styles();data=pd.read_csv(track(ROOT/'results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv'));data=data[data.time_hr.le(120)]
    fig=plt.figure(figsize=(185/25.4,118/25.4));a=fig.add_axes([.15,.63,.81,.28]);b=fig.add_axes([.15,.19,.81,.28])
    for key in ['impact-first','hospital-first']:
        d=data[data.strategy.eq(key)].sort_values('time_hr');color=layout.v.STYLE[key][0];marker='s' if key=='impact-first' else 'o';name=layout.v.POLICY_LABEL[key]
        for col,ls,quantity in [('population_dependency_weighted_R_conn','-','full network'),('population_dependency_weighted_fixed_precomputed_best_path_connection','--','fixed path')]:
            a.plot(d.time_hr,d[col],color=color,ls=ls,lw=1.2,marker=marker,ms=2.2,label=name+': '+quantity)
    a.set_title('A. Full source access and fixed-path reference',loc='left',fontweight='bold')
    a.set_ylabel('Joint source-connected probability\n(population-dependency weighted)',fontsize=8.5);a.set_ylim(-.02,1.04)
    a.legend(frameon=False,loc='lower right',ncol=2,fontsize=7.2)
    for key in layout.v.SCHEDULED:
        d=data[data.strategy.eq(key)].sort_values('time_hr');color,ls=layout.v.STYLE[key]
        b.plot(d.time_hr,d.population_dependency_weighted_full_minus_fixed_precomputed_best_path,color=color,ls=ls,lw=1.15,
               marker='s' if key=='impact-first' else 'o',ms=2.0,label=layout.v.POLICY_LABEL[key])
    b.set_title('B. Alternative-route contribution during recovery',loc='left',fontweight='bold')
    b.set(xlabel='Time after earthquake (h)',ylabel='Population-dependency-weighted\nalternative-route contribution',ylim=(-.005,.235))
    for ax in [a,b]:
        ax.set_xlim(0,120);ax.set_xticks([0,24,48,72,96,120]);ax.grid(alpha=.2)
        for t in [24,48]:ax.axvline(t,color='#b9b9b9',lw=.55,ls='--',zorder=0)
    b.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.37),ncol=4,fontsize=7.2)
    upper=OUT/'_S07_upper.pdf';fig.savefig(upper);plt.close(fig)
    d=fitz.open();q=d.new_page(width=185*MM,height=191.2*MM)
    with fitz.open(upper) as top:q.show_pdf_page(fitz.Rect(0,0,185*MM,118*MM),top,0)
    with fitz.open(track(SOURCE['FigS07'])) as src:q.show_pdf_page(fitz.Rect(0,118*MM,185*MM,191.2*MM),src,0,clip=fitz.Rect(0,118*MM,185*MM,191.2*MM),keep_proportion=False)
    target=OUT/'FigS07.pdf';d.save(target,garbage=4,deflate=True);d.close();upper.unlink();export_pdf(target)
    CAP['FigS07']='Source-connectivity support under 2pc50. A/B read the saved states from 1,000 frozen recovery realizations: the dynamic full-network quantity is population-dependency-weighted unconditional joint station-functional-and-source-connected mass. It is not a product of station marginal probabilities. A compares Impact-first and Hospital-first; solid denotes full network, dashed the fixed precomputed most-reliable path, a quantity-specific linestyle override; orange square/gray circle retain reference identity. B shows the additional joint connection contribution from alternate routes for all eight scheduled policies, with policy color/line identity following Fig04. The fixed comparator was selected from 2pc50 fragility before recovery and is not reoptimized at each time. C maps static conditional source reachability given the target station functional; D maps full-network reliability gain beyond the fixed best path. Static quantities use the accepted corrected common-event reliability estimator and differ from the dynamic joint quantity. Core sources use separate triangles. Edges have no independent failure probability in this station-only connectivity model. These probabilities are not delivered MW, network capacity or electrical adequacy.'
    CHANGES.append(['FigS07','Dynamic policy dashes/colors aligned; full/fixed quantity override explicit; original static maps preserved byte-derived vector clips; conditional/joint caption clarified.'])


def supp08():
    def choose(s,l,p):
        t=s['text'].replace('\u00a0',' ').replace('\u00ad','-')
        if t.startswith('SCE planning loading at'):return {'text':'A. '+t,'size':9.5,'bold':True}
        if t.startswith('2pc50: additional population'):return {'text':'B. '+t,'size':9.5,'bold':True}
    edit_pdf('FigS08',choose)
    CAP['FigS08']='Planning evidence and a bounded capacity post-processing check. A plots SCE 2026 GNA planning loading for 34 same-facility voltage-level rows across 28 retained stations with simultaneous demand and provider-defined limits. Marker shapes encode the low-side voltage; 100% is the provider-defined planning limit, not a seismic overload/failure threshold. OLINDA 66/12 is the only internally consistent Level-A row above it, at 109.04%. B is a separate 2pc50 service-trajectory post-processing domain: 19 one-to-one bound-supported stations; 9 multi-facility stations excluded, and 73 of 92 stations unsupported by this bound. Supported dependencies cover 932 of 2,315 tracts and 25.34% population-weighted dependency mass. The bound a=min(1,planning limit/forecast demand) is applied to unchanged modeled station service, and only OLINDA is binding-capable. Dots show the already closed capacity-minus-baseline population-weighted cumulative service-loss increments (0–480 h), on an explicitly labeled expanded scale; this panel displays four named comparators, not all policies. Planning demand/limits are MW in this supported screen. Neither panel is post-earthquake load flow or evidence of full-network electrical adequacy for all 92 stations.'
    CHANGES.append(['FigS08','Global A/B title letters only; caption separates 34/28 planning rows/stations from 19 supported bounds and states vintage/coverage.'])


def supp10():
    def choose(s,l,p):
        if s['text']=='B. Hospital-linked burden':return {'text':'B. Mean modeled service loss\nin hospital-linked tracts','size':9.5,'bold':True,'vertical_offset_mm':-1.8}
        if s['text']=='Cumulative burden (h)':return {'text':'Mean modeled service loss (h)','size':8.5}
    edit_pdf('FigS10',choose)
    CAP['FigS10']='Hospital-first construction and its hospital-linked tract outcome under 2pc50, 57 crews and the baseline repair-duration condition. A highlights hospital-linked tracts and substations receiving hospital priority; numbered circles are substation priority ranks, not hospital identifiers. Hospital-first prioritizes substation repair using the existing hospital-linked tract count and population tie-break, not tracts directly. B compares Impact-first, Hospital-first, Vulnerability-first and Degree-first over the same 1,000 saved physical realizations. The metric is the equal-weight mean modeled cumulative service loss in hospital-linked tracts, integrated over 0–480 h. Boxes show median/interquartile range, default 1.5-IQR whiskers and fliers; these are not the 5th–95th ranges in Fig04. This policy-construction-to-outcome evidence is not hospital electricity delivery or clinical capacity.'
    CHANGES.append(['FigS10','Hospital outcome titles/axis clarified; original boxes and map preserved; caption explicitly distinguishes default IQR/fliers from Fig04 ranges.'])


def supp11():
    contrast_records=[]
    def choose(s,l,p):
        if not re.fullmatch(r'[+−-]?\d+\.\d+',s['text']):return
        box=fitz.Rect(s['bbox']);center=(box.tl+box.br)/2
        # Heatmap fills in the unchanged PDF are raster objects, while text
        # remains vector. Sample the actual fill immediately beside the text.
        pix=p.get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(box.x0-3,center.y-1,box.x0-2,center.y+1),alpha=False)
        rgb=tuple(np.frombuffer(pix.samples,dtype=np.uint8).reshape(-1,3).mean(axis=0)/255)
        lin=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb];lum=.2126*lin[0]+.7152*lin[1]+.0722*lin[2]
        color=(1,1,1) if (1.05/(lum+.05))>((lum+.05)/.05) else (0,0,0)
        contrast_records.append({'text':s['text'],'background_rgb':rgb,'new_text_rgb':color,'contrast_ratio':max(1.05/(lum+.05),(lum+.05)/.05)})
        return {'color':color,'exact_origin':True}
    edit_pdf('FigS11',choose)
    assert sum(r['new_text_rgb']==(1,1,1) for r in contrast_records)>=4
    (OUT/'S11_ANNOTATION_CONTRAST.json').write_text(json.dumps(contrast_records,indent=2))
    CAP['FigS11']='Within-hazard policy contrasts under the common 57-crew, baseline-duration condition C57_D1. Each heatmap cell is the saved mean matched difference between the named scheduled policy and Unconstrained within the same hazard-specific 1,000 physical realizations. A shows population-weighted cumulative service loss; B population T80; C highest-vulnerability quartile cumulative service loss; D hospital-linked tract mean cumulative service loss. Loss integrals use 0–480 h. The source table contains 5th–95th matched-realization ranges, but uncertainty is not drawn in these mean heatmaps. Each panel has its own labeled symmetric hour scale centered on zero. Historical hazards and 2pc50 use different adopted fragility parameterizations, so this is cross-scenario robustness evidence, not pure hazard-intensity sensitivity. Direct-community is sequence-equivalent to Impact-first and omitted. Numeric cells use automatic black/white contrast lettering; values are unchanged.'
    CHANGES.append(['FigS11','Only cell annotation contrast changed; caption adds C57_D1/reference/horizon and absence of drawn uncertainty.'])


def main():
    OUT.mkdir(exist_ok=True);styles()
    assert subprocess.run(['git','merge-base','--is-ancestor',BASELINE,'HEAD'],cwd=ROOT).returncode==0
    guard=json.loads((AUDIT/'READ_ONLY_GUARD.json').read_text())
    original_guard={family:{p:sha(ROOT/p) for p in guard[family]} for family in ['scientific_hashes','publication_hashes','source_artwork_hashes']}
    (OUT/'BEFORE_STATE.json').write_text(json.dumps({'baseline':BASELINE,'hashes':original_guard,'index_hex':subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).hex()},indent=2))
    for r in ROWS:
        assert sha(ROOT/r['path'])==r['sha256'],r['path']
        track(ROOT/r['path'])
    layout=load('bounded_layout_source',LAY/'build_layout_candidates.py')
    meeting=load('bounded_meeting_source',ROOT/'src/la_grid/plotting/build_meeting_figure_collection.py')
    styles()
    framework()
    # Fig03 artwork already defines hazard identity; caption only is requested.
    shutil.copyfile(track(SOURCE['Fig03']),OUT/'Fig03.pdf');export_pdf(OUT/'Fig03.pdf')
    CAP['Fig03']=CAP['Fig03'].replace('Mean tract T80 among reached tracts','mean of realization-specific tract T80 values conditional on that tract reaching T80')
    CAP['Fig03']+=' Panel A box whiskers are the 5th–95th range of the station-specific means, describing station heterogeneity, not realization uncertainty. This figure is the cross-figure hazard color/line/order authority.'
    CHANGES.append(['Fig03','Caption estimand corrected; artwork byte-identical, used as hazard identity authority.'])
    fig05(layout);supp01(meeting);supp02();supp03();supp04(layout);supp06(meeting,layout);supp07(layout);supp08();supp10();supp11()
    for family,values in original_guard.items():assert all(sha(ROOT/p)==h for p,h in values.items()),family
    assert all(sha(ROOT/p)==h for p,h in SOURCE_HASHES.items())
    assert subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).hex()==json.loads((OUT/'BEFORE_STATE.json').read_text())['index_hex']
    pd.DataFrame(QA).to_csv(OUT/'ACTUAL_OUTPUT_QA.csv',index=False)
    pd.DataFrame(CHANGES,columns=['figure','presentation_change']).to_csv(OUT/'PRESENTATION_CHANGES.csv',index=False)
    (OUT/'CAPTIONS.json').write_text(json.dumps(CAP,indent=2),encoding='utf-8')
    (OUT/'PARITY.json').write_text(json.dumps(PARITY,indent=2))
    (OUT/'SOURCE_HASHES.json').write_text(json.dumps(SOURCE_HASHES,indent=2))
    (OUT/'CAPTIONS.md').write_text('\n\n'.join('## '+k+'\n\n'+CAP[k] for k in ['Fig01','Fig02','Fig03','Fig04','Fig05','Fig06','Fig07',*[f'FigS{i:02}' for i in range(1,14)]])+'\n',encoding='utf-8')
    print(json.dumps({'fixed_artworks':len(QA),'science_hash_changes':0,'ready_artworks_unchanged':True}))


if __name__=='__main__':main()
