"""Display-only corrections from existing tables, priority sequences and PDFs.

No simulation, scheduling, optimization, bootstrap, classification or capacity
calculation is executed. Source artwork and scientific tables are read only.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import subprocess
import shutil
from urllib.request import urlopen

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
BUNDLE=ROOT/'results/figure_review/final_submission_candidate_20261002'
MM=72/25.4

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
    return obj

h=load('native_supplement_export',ROOT/'results/figure_review/supplement_author_feedback_20261004/build_supplement_feedback.py')
h.OUT=OUT
meeting=load('existing_geometry_display',ROOT/'src/la_grid/plotting/build_meeting_figure_collection.py')
pack=load('existing_single_review_bundle',ROOT/'results/figure_review/supplement_legibility_author_feedback_20261004/build_supplement_legibility.py')
pack.OUT=OUT;pack.h=h
STEMS=['Fig04','Fig07','FigS03','FigS04','FigS07','FigS08','FigS10','FigS12','FigS13']
CAPTIONS={}
PARITY=[]

def source_records():
    for name in ['FIGURE_MANIFEST.csv','MANUSCRIPT_FACING_CAPTIONS.md']:
        dst=OUT/('SOURCE_BEFORE_'+name)
        if not dst.exists() or dst.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
            content=subprocess.check_output(['git','show',
                '8cfd3927fc6f31467827e0ac2febab3124bacd8a:'+BUNDLE.relative_to(ROOT).as_posix()+'/'+name],cwd=ROOT)
            if content.startswith(b'version https://git-lfs.github.com/spec/v1'):
                oid=re.search(rb'oid sha256:([0-9a-f]{64})',content).group(1).decode()
                env=subprocess.check_output(['git','lfs','env'],cwd=ROOT,text=True)
                media=Path(re.search(r'(?m)^LocalMediaDir=(.+)$',env).group(1).strip())
                if not media.is_absolute():media=ROOT/media
                obj=media/oid[:2]/oid[2:4]/oid
                if obj.exists():content=obj.read_bytes()
                else:
                    url='https://media.githubusercontent.com/media/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/8cfd3927fc6f31467827e0ac2febab3124bacd8a/'+BUNDLE.relative_to(ROOT).as_posix()+'/'+name
                    with urlopen(url,timeout=45) as response:content=response.read()
                assert hashlib.sha256(content).hexdigest()==oid
            dst.write_bytes(content)
    return pd.read_csv(OUT/'SOURCE_BEFORE_FIGURE_MANIFEST.csv',dtype=str).fillna('')

def source_artwork(stem):
    records=source_records();row=records[records.final_name.str.endswith('/'+stem+'.pdf')].iloc[0]
    path=h.track(ROOT/row.source_file);assert h.sha(path)==row.sha256
    return path

def captions_before():return (OUT/'SOURCE_BEFORE_MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')

def safe_text(source,destination,selector):
    # Unique resource names avoid reusing a pre-existing subset's character map.
    with fitz.open(source) as doc:
        page=doc[0];edits=[]
        for line,s in h.spans(page):
            change=selector(s,line,page)
            if change is None:continue
            edits.append((line,s,change));page.add_redact_annot(fitz.Rect(s['bbox']),fill=False)
        page.apply_redactions(images=0,graphics=0)
        for fontname,path in [('ArialAuthorRegular',h.ARIAL),('ArialAuthorBold',h.BOLD)]:page.insert_font(fontname=fontname,fontfile=path)
        for line,s,c in edits:
            text=c.get('text',s['text']);size=c.get('size',s['size']);bold=c.get('bold','Bold' in s['font'])
            font=fitz.Font(fontfile=h.BOLD if bold else h.ARIAL);box=fitz.Rect(s['bbox'])
            angle=int(round(-np.degrees(np.arctan2(line['dir'][1],line['dir'][0]))))%360
            if angle==90:
                origin=((box.x0+box.x1)/2+(font.ascender+font.descender)*size/2,
                    (box.y0+box.y1)/2+font.text_length(text,fontsize=size)/2)
            else:
                origin=(c.get('x',(box.x0+box.x1)/2-font.text_length(text,fontsize=size)/2),
                    c.get('y',(box.y0+box.y1)/2+(font.ascender+font.descender)*size/2))
            page.insert_text(origin,text,fontname='ArialAuthorBold' if bold else 'ArialAuthorRegular',fontsize=size,rotate=angle)
        doc.save(destination,garbage=4,deflate=True)

def remove_empty_stripe(source,destination,lo_mm,hi_mm):
    with fitz.open(source) as doc:
        page=doc[0];start,end=lo_mm*MM,hi_mm*MM
        clip=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(0,start,page.rect.width,end),alpha=False)
        pixels=np.frombuffer(clip.samples,dtype=np.uint8).reshape(clip.height,clip.width,clip.n)
        assert not (pixels[:,:,:3]<240).any(),'Stripe contains content: '+str(source)
        new=fitz.open();q=new.new_page(width=page.rect.width,height=page.rect.height-(end-start))
        q.show_pdf_page(fitz.Rect(0,0,page.rect.width,start),doc,0,clip=fitz.Rect(0,0,page.rect.width,start),keep_proportion=False)
        q.show_pdf_page(fitz.Rect(0,start,page.rect.width,q.rect.height),doc,0,
            clip=fitz.Rect(0,end,page.rect.width,page.rect.height),keep_proportion=False)
        new.save(destination,garbage=4,deflate=True);new.close()

def guard():
    p=OUT/'BEFORE_HASH_GUARD.json'
    if p.exists():return json.loads(p.read_text())
    old=json.loads((ROOT/'results/figure_review/clarity_author_feedback_20261004/BEFORE_HASH_GUARD.json').read_text())
    records={
        'science':{k:h.sha(ROOT/k) for k in old['science']},
        'publication':{k:h.sha(ROOT/k) for k in old['publication']},
        'other_review_artwork':{p.relative_to(ROOT).as_posix():h.sha(p)
            for folder in ['Main','Supplement'] for p in (BUNDLE/folder).glob('*')
            if p.is_file() and p.stem not in STEMS},
    }
    p.write_text(json.dumps(records,indent=2));return records

def s07():
    data=pd.read_csv(h.track(ROOT/'results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv'))
    data=data[data.time_hr.le(120)]
    height=233
    fig=plt.figure(figsize=(185/25.4,height/25.4))
    def axis(top,hh):return fig.add_axes([28/185,(height-top-hh)/height,151/185,hh/height])
    a=axis(13,37);b=axis(66,37)
    for key in ['impact-first','hospital-first']:
        d=data[data.strategy.eq(key)].sort_values('time_hr')
        for col,ls,meaning in [
            ('population_dependency_weighted_R_conn','-','full network'),
            ('population_dependency_weighted_fixed_precomputed_best_path_connection','--','fixed path')]:
            a.plot(d.time_hr,d[col],color=h.COLOR[key],ls=ls,lw=1.3,
                label=h.LABEL[key]+': '+meaning)
    a.set_title('A. Source connection: full network and fixed path',loc='left',fontweight='bold')
    a.set(ylabel='Probability of being functional\nand source-connected',ylim=(-.02,1.04))
    a.legend(frameon=False,loc='lower right',ncol=2,fontsize=7.5,
        handlelength=2.4,handletextpad=.4,columnspacing=1.1)
    for key in h.KEYS[:-1]:
        d=data[data.strategy.eq(key)].sort_values('time_hr');core=key in h.KEYS[:4]
        b.plot(d.time_hr,d.population_dependency_weighted_full_minus_fixed_precomputed_best_path,
            color=h.COLOR[key],ls=h.LINE[key],lw=1.5 if core else .75,
            alpha=1 if core else .30,zorder=5 if core else 2)
    b.set_title('B. Additional source connection from alternate routes',loc='left',fontweight='bold')
    b.set(xlabel='Time after earthquake (h)',ylabel='Increase in source-\nconnection probability',ylim=(-.005,.235))
    for ax in [a,b]:
        ax.set_xlim(0,120);ax.set_xticks([0,24,48,72,96,120]);ax.grid(alpha=.20)
        for t in [24,48]:ax.axvline(t,color='#b9b9b9',lw=.5,ls='--',zorder=0)
    for keys,top in [(h.KEYS[:4],117),(h.KEYS[4:-1],125)]:
        handles=[Line2D([],[],color=h.COLOR[k],ls=h.LINE[k],lw=1.5 if k in h.KEYS[:4] else .75,
            alpha=1 if k in h.KEYS[:4] else .45,label=h.LABEL[k]) for k in keys]
        key=fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,1-top/height),
            frameon=False,ncol=4,fontsize=7.5,handlelength=2.4,handletextpad=.4,columnspacing=1.2)
        if top==126:
            for t in key.texts:t.set_weight('bold')
    for p in (ROOT/'Data').glob('LA_Tracts_With_Population.*'):h.track(p)
    tracts=meeting.tract_geometry()
    nodes=pd.read_csv(h.track(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv'),dtype={'id':str})
    edges=pd.read_csv(h.track(ROOT/'Data/substation_graph_CEC_edges_expanded.csv'),dtype={'u':str,'v':str})
    station=pd.read_csv(h.track(ROOT/'results/diagnostics/SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv'),dtype={'station_id':str})
    points=meeting.map_points(nodes,tracts.crs).merge(station,left_on='id',right_on='station_id',validate='one_to_one')
    non=points[~points.is_core_source];core=points[points.is_core_source];lookup=points.set_index('id').geometry
    assert (len(non),len(core),len(edges))==(78,14,318)
    specifications=[('R_path_full','C. Conditional source reachability','Blues',.45,'Conditional source-path reliability'),
        ('Delta_R_redundancy','D. Reliability gain from alternate routes','OrRd',.45,'Additional source-path reliability')]
    for i,(col,title,name,start,scale) in enumerate(specifications):
        ax=fig.add_axes([(.015+i*.50),(height-139-63)/height,.475,63/height])
        meeting.draw_tract_base(ax,tracts)
        # GIS tract boundaries are background, while graph connections remain visible.
        for coll in ax.collections:coll.set_linewidth(.14);coll.set_edgecolor('#d5d9db')
        for e in edges.itertuples(index=False):
            u,v=lookup[e.u],lookup[e.v]
            ax.plot([u.x,v.x],[u.y,v.y],color='#718a98',lw=.4,alpha=.64,zorder=2)
        cmap=LinearSegmentedColormap.from_list(col,plt.get_cmap(name)(np.linspace(start,1,256)))
        maximum=float(non[col].max())
        dots=ax.scatter(non.geometry.x,non.geometry.y,c=non[col],cmap=cmap,vmin=0,vmax=maximum,
            s=17,edgecolors='#314957',linewidth=.22,zorder=3)
        ax.scatter(core.geometry.x,core.geometry.y,marker='^',s=21,
            facecolors='#202c34',edgecolors='white',linewidth=.35,zorder=4)
        ax.set_title(title,fontsize=9.5,fontweight='bold',pad=5)
        cax=fig.add_axes([.07+i*.50,(height-206-2.5)/height,.37,2.5/height])
        cb=fig.colorbar(dots,cax=cax,orientation='horizontal')
        cb.set_label(scale,fontsize=7.5,labelpad=2)
        cb.ax.tick_params(labelsize=7.5,width=.5,length=2);cb.outline.set_linewidth(.5)
        PARITY.append({'figure':'FigS07','metric':col,'normalization':'linear; unchanged 0–max',
            'vmin':0,'vmax':maximum,'station_values_sha256':hashlib.sha256(non[col].to_numpy().tobytes()).hexdigest()})
    fig.legend(handles=[Line2D([],[],marker='^',ls='none',color='#202c34',ms=4,
        markeredgecolor='white',markeredgewidth=.35,label='Core source')],
        frameon=False,loc='upper center',bbox_to_anchor=(.5,1-216/height),fontsize=7.5)
    h.save(fig,'FigS07')
    # Crop only the unused bottom canvas, with every element already moved up.
    path=OUT/'FigS07.pdf';temporary=OUT/'_S07_bottom.pdf'
    with fitz.open(path) as old_doc:
        result=fitz.open();q=result.new_page(width=185*MM,height=224*MM)
        q.show_pdf_page(q.rect,old_doc,0,clip=fitz.Rect(0,0,185*MM,224*MM),keep_proportion=False)
        result.save(temporary,garbage=4,deflate=True);result.close()
    temporary.replace(path)
    remove_empty_stripe(path,temporary,200,204);temporary.replace(path);h.export(path)
    old=captions_before()
    match=re.search(r'(?ms)^## Supplementary Figure S7\.([^\n]*)\n\n(.*?)(?=^## |\Z)',old);assert match
    CAPTIONS['Supplementary Figure S7.'+match.group(1)]=match.group(2).strip()+(
        ' Policy keys use the same line styles as their curves; no marker denotes a policy in A/B. '
        'In A, solid and dashed lines instead distinguish full-network and fixed-path quantities. '
        'Four explanatory policies are emphasized in B; all four other scheduled policies remain visible. '
        'Graph connections in C/D join the same station coordinates; Core sources are the triangles shown in their separate key.')
    PARITY.append({'figure':'FigS07','scheduled_policies_retained':h.KEYS[:-1],
        'dynamic_values_unchanged':True,'decorative_policy_markers':False,'graph_edges_retained':318})

def s08():
    original=h.save
    def emit(fig,stem):
        height=214;fig.set_size_inches(185/25.4,height/25.4)
        a,b=fig.axes
        a.set_position([34.225/185,(height-9-129)/height,143.375/185,129/height])
        b.set_position([37/185,(height-160-30)/height,135.05/185,30/height])
        labels=[t.get_text() for t in a.get_yticklabels()]
        a.set_yticklabels(['OLINDA 66/12' if x=='OLINDA' else x for x in labels])
        a.set_xlabel('2026 provider-reported facility loading (%)')
        b.set_title('B. Effect of the OLINDA planning bound',loc='left',fontweight='bold')
        b.set_xlabel('Added population-weighted service loss (h; expanded scale)',fontsize=8.5)
        b.grid(axis='y',visible=False)
        for key,line in zip(['impact-first','hospital-first','vulnerability-first','degree-first'],b.lines):
            mark={'impact-first':'s','hospital-first':'o','vulnerability-first':'D','degree-first':'^'}[key]
            line.set_marker(mark);line.set_markerfacecolor('white' if key=='degree-first' else h.COLOR[key])
        return original(fig,stem)
    h.save=emit
    try:h.s08()
    finally:h.save=original
    CAPTIONS['Supplementary Figure S8. Facility planning limits and the OLINDA-bound sensitivity']=(
        '(A) SCE 2026 Grid Needs Assessment facility loading for 34 same-facility, voltage-level '
        'planning rows across 28 substations with simultaneous forecast demand and provider-defined limits. '
        'Marker shapes identify low-side voltage. The 100% line is the provider-defined planning limit, '
        'not an earthquake failure or overload threshold. OLINDA 66/12 is the only internally consistent '
        'row above the limit, at 109.04%. '
        '(B) Increase in population-weighted modeled service loss after applying the OLINDA planning '
        'bound, compared with the same source-connected model without the bound. The screen applies '
        'bounds to 19 one-to-one supported substations; nine multi-facility stations are excluded, '
        'leaving 73 of the 92 substations without an applicable bound. Supported dependencies cover '
        '932 of 2,315 tracts and 25.34% of population-weighted dependency mass. Station service is '
        'bounded by the smaller of modeled service and min(1, planning limit/forecast demand); '
        'demand and limit are in MW in this supported screen. Only OLINDA has a ratio below one, '
        'so only its bound can reduce otherwise available modeled service. Points show means across '
        '1,000 matched 2pc50 realizations per policy, under 57 crews and repair-duration multiplier '
        '1.00, with service loss integrated over 0–480 h. The expanded axis resolves increments '
        'of approximately 0.120–0.126 h, rather than total service loss. This planning-condition '
        'subset check is not post-earthquake load flow, an estimate of earthquake overload, or '
        'validation of electrical adequacy across the full network.')

def s10():
    # Preserve the reviewed hospital map at native scale as the first panel.
    source=h.track(ROOT/'results/figure_review/hospital_resource_author_feedback_20261004/FigS10.pdf')
    a_path=OUT/'_S10_hospital.pdf'
    safe_text(source,a_path,lambda s,l,q:{'text':'A. Hospital-first repair priority'}
        if h.plain(s['text'])=='Hospital-first repair priority' else None)
    condensed=OUT/'_S10_hospital_compact.pdf'
    remove_empty_stripe(a_path,condensed,105.5,110.5);condensed.replace(a_path)
    for p in (ROOT/'Data').glob('LA_Tracts_With_Population.*'):h.track(p)
    tracts=meeting.tract_geometry()
    nodes=pd.read_csv(h.track(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv'),dtype={'id':str})
    names=pd.read_csv(h.track(ROOT/'Data/Substations_PGA_IDW_CEC_expanded.csv'),dtype={'id':str})[['id','NAME']]
    meta=pd.read_csv(h.track(ROOT/'provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv'),dtype={'tract_id':str})
    vuln=json.loads(h.track(ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_FIRST_SEQUENCE.json').read_text())
    rules=json.loads(h.track(ROOT/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']
    q4=set(meta.loc[meta.SOVI_quartile.eq('Q4'),'tract_id']);assert len(q4)==vuln['Q4_tract_count']==579
    points=meeting.map_points(nodes,tracts.crs).merge(names,on='id',validate='one_to_one')
    specs=[('vulnerability-first',vuln['ordered_station_ids'],'B. Vulnerability-first repair priority',
        {'309569':(.12,.92,'left'),'310527':(.98,.76,'right'),'309042':(.02,.58,'left'),
         '304073':(.02,.38,'left'),'303169':(.98,.19,'right')}),
        ('impact-first',rules['impact-first'],'C. Impact-first repair priority',
        {'303620':(.01,.93,'left'),'300429':(.98,.91,'right'),'303099':(.02,.39,'left'),
         '305984':(.98,.69,'right'),'300558':(.98,.25,'right')})]
    fig=plt.figure(figsize=(185/25.4,81/25.4))
    ranked=[]
    for i,(key,sequence,title,positions) in enumerate(specs):
        assert len(sequence)==92 and len(set(sequence))==92
        top=list(map(str,sequence[:5]));selected=points[points.id.isin(top)]
        assert len(selected)==5
        ax=fig.add_axes([.02+i*.50,(81-12-52)/81,.46,52/81])
        colors=np.where(tracts.tract_id_norm.isin(q4),'#dfd2ef','#f8f8f8') if i==0 else '#f8f8f8'
        meeting.draw_tract_base(ax,tracts,colors)
        ax.scatter(points.geometry.x,points.geometry.y,s=8,color='#70828d',edgecolors='white',linewidth=.25,zorder=3)
        ax.scatter(selected.geometry.x,selected.geometry.y,s=20,color=h.COLOR[key],edgecolors='white',linewidth=.4,zorder=5)
        for rank,station in enumerate(top,1):
            row=points[points.id.eq(station)].iloc[0];x,y,ha=positions[station]
            ax.annotate(row.NAME,(row.geometry.x,row.geometry.y),xytext=(x,y),textcoords='axes fraction',
                ha=ha,va='center',fontsize=7.5,color='#65442f' if i==0 else '#944a00',fontweight='bold',
                arrowprops={'arrowstyle':'-','color':'#6b797e','lw':.5},
                bbox={'facecolor':'white','edgecolor':'none','alpha':.88,'pad':.65},zorder=6)
            ranked.append({'policy':key,'sequence_position':rank,'station_id':station,'station_name':row.NAME,
                'longitude':row.lon,'latitude':row.lat,'sequence_source':'VULNERABILITY_FIRST_SEQUENCE.json' if i==0 else 'FULL_RULE_SEQUENCES.json'})
        ax.set_title(title,fontsize=9.5,fontweight='bold',pad=5)
    fig.legend(handles=[Patch(facecolor='#dfd2ef',label='Highest-vulnerability quartile (B)'),
        Line2D([],[],marker='o',ls='none',color='#70828d',ms=3.5,label='Substations'),
        Line2D([],[],marker='o',ls='none',color=h.COLOR['vulnerability-first'],ms=4.5,label='First five: Vulnerability-first'),
        Line2D([],[],marker='o',ls='none',color=h.COLOR['impact-first'],ms=4.5,label='First five: Impact-first')],
        frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.5,1-67/81),fontsize=7.5,
        columnspacing=1.1,handletextpad=.4)
    lower=OUT/'_S10_other_priorities.pdf';fig.savefig(lower);plt.close(fig)
    with fitz.open(a_path) as a,fitz.open(lower) as low:
        result=fitz.open();page=result.new_page(width=185*MM,height=(121+81)*MM)
        page.show_pdf_page(fitz.Rect(0,0,185*MM,121*MM),a,0)
        page.show_pdf_page(fitz.Rect(0,121*MM,185*MM,202*MM),low,0)
        result.save(OUT/'FigS10.pdf',garbage=4,deflate=True);result.close()
    a_path.unlink();lower.unlink();h.export(OUT/'FigS10.pdf')
    pd.DataFrame(ranked).to_csv(OUT/'PRIORITY_MAP_STATION_IDENTITIES.csv',index=False)
    PARITY.append({'figure':'FigS10','hospital_map_scale_unchanged':True,
        'sequence_and_station_coordinates_unchanged':True,'new_priority_maps':['vulnerability-first','impact-first']})
    CAPTIONS['Supplementary Figure S10. Hospital, vulnerability and population-impact repair priorities']=(
        '(A) Hospital-linked tracts and substations receiving Hospital-first priority. '
        'The first five fixed sequence positions are named and highlighted in teal; priority is determined '
        'by hospital-linked tract counts, with mapped population as the tie-break. '
        '(B) Vulnerability-first highlights tracts in Q4, the highest social-vulnerability quartile, and names '
        'the first five stations in its fixed sequence. Its station score is the mapped population dependency '
        'of Q4 tracts; ties use total mapped population and station ID. '
        '(C) Impact-first names the first five stations in the population-impact sequence. This rule ranks '
        'the mapped population fraction affected by each station removal in the intact-graph scoring model; '
        'it is not simply a ranking of the population directly mapped to a station, nor proof of a globally '
        'optimal cumulative service-loss sequence. All three maps show substation priority construction, '
        'not tract repair. Named stations refer to positions in the full fixed orders; actual task queues '
        'filter those orders to damaged substations in each realization. Coordinates, mapping, quartile '
        'membership and the three orders are identical to those used in the corresponding policy evaluations. '
        'Outcome comparisons appear in Figures 4–6 and Supplementary Figures S12/S13; hospital-linked tract '
        'loss does not measure hospital electricity delivery or clinical capacity.')

def resources(stem):
    src=source_artwork(stem)
    # The removed stripe contains no data, labels or paths; plots remain native-scale vectors.
    with fitz.open(src) as d:
        page=d[0];start,end=90.5*MM,99.5*MM
        clip=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(0,start,page.rect.width,end),alpha=False)
        pixels=np.frombuffer(clip.samples,dtype=np.uint8).reshape(clip.height,clip.width,clip.n)
        assert not (pixels[:,:,:3]<240).any(),'Requested stripe is not empty: '+stem
        new=fitz.open();q=new.new_page(width=page.rect.width,height=page.rect.height-(end-start))
        q.show_pdf_page(fitz.Rect(0,0,page.rect.width,start),d,0,clip=fitz.Rect(0,0,page.rect.width,start),keep_proportion=False)
        q.show_pdf_page(fitz.Rect(0,start,page.rect.width,q.rect.height),d,0,
            clip=fitz.Rect(0,end,page.rect.width,page.rect.height),keep_proportion=False)
        temporary=OUT/('_'+stem+'_reflow.pdf');new.save(temporary,garbage=4,deflate=True);new.close()
    def replace(s,line,page):
        text=h.plain(s['text'])
        if text.startswith('C. Absolute Q4') and text.endswith('separation'):
            return {'text':'C. High–low vulnerability service-loss gap','x':22.2*MM}
        if text=='Absolute group separation (h)':return {'text':'Absolute Q4–Q1 service-loss gap (h)'}
        if text=='Cumulative service loss (h)':return {'text':'Modeled service loss (h)'}
        return None
    safe_text(temporary,OUT/(stem+'.pdf'),replace);temporary.unlink();h.export(OUT/(stem+'.pdf'))
    md=captions_before()
    match=re.search(r'(?ms)^## Supplementary Figure '+stem.replace('Fig','')+r'\.([^\n]*)\n\n(.*?)(?=^## |\Z)',md);assert match
    body=match.group(2).strip().replace('per-realization absolute Q4–Q1 separation','per-realization absolute Q4–Q1 service-loss gap')
    body+=(' In C, the gap is the absolute difference between Q4 and Q1 group-mean service-loss integrals '
        'within each realization, taken before averaging over realizations. It measures the size of the '
        'between-group difference, without identifying which group has higher loss. It is distinct from '
        'the signed Q4–Q1 difference and from population-weighted Gini. Higher values indicate a larger '
        'high–low vulnerability service-loss gap; Panel B shows the Q4 loss level itself.')
    CAPTIONS['Supplementary Figure '+stem.replace('Fig','')+'.'+match.group(1)]=body
    PARITY.append({'figure':stem,'removed_empty_stripe_mm':9,'plot_scale_unchanged':True,
        'displayed_means_and_realization_ranges_unchanged':True,'gap_definition':'mean of within-realization abs(Q4–Q1), not abs of ensemble means'})

def spacing_audit(label):
    if label=='BEFORE' and (OUT/'PANEL_SPACING_BEFORE.csv').exists():
        return pd.read_csv(OUT/'PANEL_SPACING_BEFORE.csv').to_dict('records')
    records=[]
    for folder in ['Main','Supplement']:
        for file in sorted((BUNDLE/folder).glob('*.pdf')):
            with fitz.open(file) as doc:
                page=doc[0];pixels=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
                rgb=np.frombuffer(pixels.samples,dtype=np.uint8).reshape(pixels.height,pixels.width,pixels.n)
                # Horizontal blank bands, excluding external margins. Map background
                # whites are not equivalent to wasted panel space; inspect flagged bands.
                occupied=(rgb[:,:,:3].min(axis=2)<240).sum(axis=1)>5
                ink=np.flatnonzero(occupied);runs=[]
                if len(ink):
                    boundaries=np.flatnonzero(np.diff(ink)>1)
                    for k in boundaries:
                        lo,hi=ink[k]+1,ink[k+1];size=(hi-lo)/2/MM
                        if size>=3:runs.append({'top_mm':round(lo/2/MM,2),'bottom_mm':round(hi/2/MM,2),'gap_mm':round(size,2)})
                records.append({'figure':file.stem,'width_mm':page.rect.width/MM,'height_mm':page.rect.height/MM,
                    'maximum_internal_blank_band_mm':max((x['gap_mm'] for x in runs),default=0),
                    'bands_ge_3_mm':json.dumps(runs),'measurement':'native-PDF raster at 144 dpi; blank horizontal bands; excludes outer margins'})
    pd.DataFrame(records).to_csv(OUT/('PANEL_SPACING_'+label+'.csv'),index=False)
    return records

def main():
    before=guard();source_records();h.style();spacing_audit('BEFORE')
    for name,fun in [('S07',s07),('S08',s08),('S10',s10),('S12',lambda:resources('FigS12')),('S13',lambda:resources('FigS13'))]:
        print('Rendering '+name,flush=True);fun()
    for stem,lo,hi in [('Fig04',112.5,119.5),('Fig07',166,172),('FigS03',102,106.5),('FigS04',62,70)]:
        print('Removing empty spacing in '+stem,flush=True)
        remove_empty_stripe(source_artwork(stem),OUT/(stem+'.pdf'),lo,hi);h.export(OUT/(stem+'.pdf'))
        PARITY.append({'figure':stem,'removed_empty_stripe_mm':hi-lo,'native_plot_map_and_text_scale_unchanged':True})
    manifest=pd.read_csv(BUNDLE/'FIGURE_MANIFEST.csv',dtype=str).fillna('')
    for stem in [s for s in STEMS if not s.startswith('FigS')]:
        with fitz.open(OUT/(stem+'.pdf')) as doc:
            page=doc[0];size=f'{page.rect.width/MM:.3f} x {page.rect.height/MM:.3f}'
            minimum=min(s['size'] for _,s in h.spans(page))
        for extension in ['.pdf','.png']:
            source=OUT/(stem+extension);dest=BUNDLE/'Main'/(stem+extension)
            shutil.copyfile(source,dest);assert h.sha(source)==h.sha(dest)
            mask=manifest.final_name.eq(dest.relative_to(BUNDLE).as_posix());assert mask.sum()==1
            manifest.loc[mask,['source_file','source_commit','sha256','size_mm','min_font_pt','status']]=[
                source.relative_to(ROOT).as_posix(),'ARTWORK_COMMIT_PENDING',h.sha(dest),size,f'{minimum:.3f}',
                'AUTHOR_REVIEW_UPDATE_NOT_PROMOTED']
    manifest.to_csv(BUNDLE/'FIGURE_MANIFEST.csv',index=False)
    pack.STEMS=[s for s in STEMS if s.startswith('FigS')];pack.CAPTIONS=CAPTIONS;pack.package()
    merged=fitz.open()
    for i in range(1,8):
        with fitz.open(BUNDLE/f'Main/Fig{i:02d}.pdf') as doc:merged.insert_pdf(doc)
    merged.save(BUNDLE/'ALL_MAIN_FIGURES.pdf',garbage=4,deflate=True);merged.close()
    spacing_audit('AFTER')
    for category,records in before.items():
        assert all(h.sha(ROOT/path)==value for path,value in records.items()
            if category!='other_review_artwork' or Path(path).stem not in STEMS),category
    # Resource sources are bundle files intentionally replaced; verify other read inputs.
    for path,value in h.INPUT_HASHES.items():
        if path.endswith(('Supplement/FigS12.pdf','Supplement/FigS13.pdf')):continue
        assert h.sha(ROOT/path)==value,path
    pd.DataFrame(h.QA).drop_duplicates('file',keep='last').to_csv(OUT/'OUTPUT_QA.csv',index=False)
    (OUT/'DISPLAY_PARITY.json').write_text(json.dumps(PARITY,indent=2))
    (OUT/'READ_INPUT_HASHES.json').write_text(json.dumps(h.INPUT_HASHES,indent=2))
    print('PRESENTATION_COMPLETE_SCIENTIFIC_HASH_CHANGES_0',flush=True)

if __name__=='__main__':main()
