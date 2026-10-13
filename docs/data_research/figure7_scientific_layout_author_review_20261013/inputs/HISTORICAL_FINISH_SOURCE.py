"""Bounded vector/display changes from pinned current artwork and saved tables.

No scientific stage, trajectory evaluator, scheduling, sampling, GA or model
fit is invoked. Resource panels reuse original vector marks, not new statistics.
"""
from pathlib import Path
import inspect, io, json, re, subprocess, sys
import fitz
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgb
import consolidate_current_figure_suite as u
from integrate_final_s05_and_suite_review_20261012 import streams, pdf_info
from simplify_s05_figure_text_20261012 import plain_font, TEXT

ROOT=u.ROOT; DEST=u.DEST; MM=u.MM
BASE='37e71b3e15b0f4e1be3a651344e3f9e6475dc24b'
QA=ROOT/'docs/reproducibility/author_suite_final_layout_20261012'
PRIOR=ROOT/'docs/reproducibility/s05_plain_figure_labels_20261012'
GENERATOR='src/la_grid/plotting/finish_author_figure_suite_20261012.py'
ACTIVE=[f'Main/Fig{i:02d}' for i in range(1,8)]+[f'Supplement/FigS{i:02d}' for i in [1,*range(3,12)]]
RETIRE=['Supplement/FigS12','Supplement/FigS13']
SOURCE_HASHES={}; EDITS={}
NUM=rb'[-+]?(?:\d+(?:\.\d*)?|\.\d+)'
RGB=re.compile(rb'('+NUM+rb')\s+('+NUM+rb')\s+('+NUM+rb')\s+(rg|RG)\b')
PATH=re.compile(rb'(?<!\S)'+NUM+rb'\s+'+NUM+rb'\s+m(?:\s+(?:'+NUM+rb'\s+'+NUM+rb'\s+[ml]|'+NUM+rb'(?:\s+'+NUM+rb'){5}'+rb'\s+c|h))*\s+h\s+B\b')


def source(rel):
    data=u.payload(BASE,rel)
    SOURCE_HASHES[BASE+':'+rel]={'sha256':u.digest(data),'bytes':len(data)}
    return data


def native(stem):
    return fitz.open(stream=source('results/figure_review/'+stem+'.pdf'),filetype='pdf')


def text(page,x,y,value,size=8.5,bold=False,center=False,rotate=0,color=(0,0,0)):
    name='AuthorBold' if bold else 'AuthorArial'
    path='C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'
    font=fitz.Font(fontfile=path)
    if center:x-=font.text_length(value,fontsize=size)/2
    page.insert_text((x,y),value,fontname=name,fontsize=size,rotate=rotate,color=color)


def fonts(page,doc):
    plain_font(page,doc,'AuthorArial','C:/Windows/Fonts/arial.ttf')
    plain_font(page,doc,'AuthorBold','C:/Windows/Fonts/arialbd.ttf')


def graphics_only(doc):
    checks=[]
    for x in streams(doc):
        raw=doc.xref_stream(x); changed=TEXT.sub(b'',raw)
        if changed!=raw:
            assert TEXT.sub(b'',raw)==changed
            doc.update_stream(x,changed)
            checks.append({'source_xref':x,'unchanged_graphics_sha256':u.digest(changed)})
    return checks


def dbf_geoids(data):
    """Read the existing DBF row identities; no geometry extraction or GIS fit."""
    n=int.from_bytes(data[4:8],'little');header=int.from_bytes(data[8:10],'little')
    record_length=int.from_bytes(data[10:12],'little');offset=1;geo=None
    pos=32
    while data[pos]!=13:
        desc=data[pos:pos+32];name=desc[:11].split(b'\0')[0].decode('ascii')
        width=desc[16]
        if name=='GEOID':geo=(offset,width)
        offset+=width;pos+=32
    assert geo is not None and header>=pos+1 and len(data)>=header+n*record_length
    start,width=geo
    rows=[]
    for i in range(n):
        r=data[header+i*record_length:header+(i+1)*record_length]
        if r[:1]!=b'*':
            value=r[start:start+width].decode('ascii').strip().zfill(11)
            assert len(value)==11 and value.isdigit()
            rows.append(value)
    return rows


def export(doc,stem):
    data=doc.tobytes(garbage=4,deflate=True)
    info=pdf_info(doc);doc.close()
    u.write(DEST/(stem+'.pdf'),data)
    renderer=ROOT/'docs/reproducibility/official_figure_suite_review_20261012/render_one.py'
    subprocess.run([sys.executable,str(renderer),str(DEST/(stem+'.pdf')),
        str(DEST/(stem+'.png')),str(DEST/'Page_Previews'/('Fig'+stem.split('Fig')[-1]+'.png'))],check=True)
    return info


def framework():
    d=native('Main/Fig01');p=d[0]
    box=fitz.Rect(94.5*MM,164.2*MM,182*MM,217*MM)
    p.add_redact_annot(box,fill=(1,1,1));p.apply_redactions(images=0,graphics=0,text=0)
    fonts(p,d)
    p.draw_rect(box,color=(.56,.63,.68),fill=(1,1,1),width=.6)
    p.draw_rect(fitz.Rect(94.5*MM,164.2*MM,182*MM,169*MM),color=None,fill=(.91,.95,.98))
    p.draw_circle((97*MM,166.5*MM),1.6*MM,color=None,fill=(.18,.43,.62))
    text(p,97*MM,167.5*MM,'5',9.5,bold=True,center=True,color=(1,1,1))
    text(p,99.5*MM,167.8*MM,'Community Outcomes',9.5,bold=True)
    for cx,label in [(110,'Recovery outcomes'),(139,'Distributional effects'),(168,'Spatial patterns')]:
        text(p,cx*MM,174*MM,label,8,bold=True,center=True)
    for stem,clip,target in [
        ('Main/Fig04',(21,41,88,100),(97.5,178.5,122.5,194)),
        ('Main/Fig07',(5,178,90,238),(157,178.5,179,195)),
    ]:
        icon=native(stem);graphics_only(icon)
        p.show_pdf_page(fitz.Rect(*(v*MM for v in target)),icon,0,
            clip=fitz.Rect(*(v*MM for v in clip)),keep_proportion=stem.endswith('07'))
        icon.close()
    # Explicitly schematic, as in the existing framework; no numerical axis.
    text(p,139*MM,177.5*MM,'Schematic',8,center=True)
    h=[.90,.67,.72,.48]
    for j,height in enumerate(h):
        x=(128.3+j*6)*MM
        color=(.39,.55,.64) if j<3 else (.71,.42,.25)
        p.draw_rect(fitz.Rect(x,(192-height*11.5)*MM,x+3.3*MM,192*MM),color=None,fill=color)
        text(p,(130+j*6)*MM,195.4*MM,'Q'+str(j+1),8,center=True)
    p.draw_polyline([(151.1*MM,183*MM),(152*MM,183*MM),(152*MM,189*MM),(151.1*MM,189*MM)],color=(.2,.2,.2),width=.55)
    for cx,labels in [(110,['Service loss','T80']),
                      (139,['Q1-Q4 service loss','Quartile gap','Gini']),
                      (168,['Service-loss changes','Community typology','Hotspot score'])]:
        for y,label in zip([200,206,212],labels):text(p,cx*MM,y*MM,label,8,center=True)
    EDITS['Main/Fig01']={'changed_region_mm':[94.5,164.2,182,217],
        'removed':['selective all/hospital list','percent definition in graphic','Vulnerability-first effects metric row','Tested conditions block'],
        'Recovery_labels':['Service loss','T80'],
        'Distribution_labels':['Q1-Q4 service loss','Quartile gap','Gini'],
        'Spatial_labels':['Service-loss changes','Community typology','Hotspot score'],
        'schematic_only':True,'stages_1_to_4_scientific_content_unchanged':True}
    return export(d,'Main/Fig01')


def cap_maps():
    d=native('Main/Fig05')
    vp='Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_TRACT_EFFECTS.parquet'
    dp='Formal_Experiment_20260923/Formal_Results/TRACT_PAIRED_EFFECTS.parquet'
    v=pd.read_parquet(io.BytesIO(source(vp)));v=v[v.hazard.eq('2pc50')]
    a=pd.read_parquet(io.BytesIO(source(dp)))
    a=a[a.hazard.eq('2pc50')&a.resource_scenario.eq('C57_D1')&a.strategy_id.eq('degree-first')&a.reference_strategy.eq('hospital-first')]
    def ids(frame):return frame.tract_id.astype(str).str.zfill(11)
    a=a.assign(tract_id=ids(a));v=v.assign(tract_id=ids(v))
    values={ref:v[v.reference_strategy.eq(ref)].set_index('tract_id').mean_paired_delta_burden_hr
            for ref in ['hospital-first','impact-first']}
    values['degree-first']=values['hospital-first']-a.set_index('tract_id').paired_mean_delta_burden_hr
    assert all(len(s)==2315 and s.notna().all() for s in values.values())
    order=[gid for gid in dbf_geoids(source('Data/LA_Tracts_With_Population.dbf')) if gid in values['hospital-first'].index]
    assert len(order)==len(set(order))==2315
    vals=np.concatenate([values[r].reindex(order).to_numpy() for r in ['hospital-first','impact-first','degree-first']])
    limit=float(max(abs(s).max() for s in values.values()))
    assert abs(limit-24.018302801579285)<1e-9
    cmap=LinearSegmentedColormap.from_list('service_loss_blue_orange',['#2166ac','#80b4d4','#c4c4c4','#f4ae62','#d96518'],N=256)
    old_rgb=cmap(Normalize(-limit,limit)(vals))[:,:3]
    new_rgb=cmap(Normalize(-20,20,clip=True)(vals))[:,:3]
    candidates=[x for x in streams(d) if len(PATH.findall(d.xref_stream(x)))==6945]
    assert len(candidates)==1,candidates
    x=candidates[0];raw=d.xref_stream(x);matches=list(PATH.finditer(raw))
    colors=list(RGB.finditer(raw)); ci=0; output=[];end=0;geometry_hashes=[]
    for j,m in enumerate(matches):
        while ci+1<len(colors) and colors[ci+1].start()<m.start():ci+=1
        assert colors[ci][4]==b'rg'
        actual=np.array([float(colors[ci][k]) for k in [1,2,3]])
        assert np.max(abs(actual-old_rgb[j]))<3e-6,(j,actual,old_rgb[j])
        output.append(raw[end:m.start()])
        paint=('q %.9f %.9f %.9f rg '%tuple(new_rgb[j])).encode()
        output.extend([paint,m[0],b' Q']);end=m.end()
        geometry_hashes.append(u.digest(m[0]))
    output.append(raw[end:]);updated=b''.join(output)
    # All original geometry path bytes survive; only new per-path paint is added.
    assert [u.digest(m[0]) for m in PATH.finditer(updated)]==geometry_hashes
    d.update_stream(x,updated)
    p=d[0];fonts(p,d)
    p.draw_rect(fitz.Rect(32*MM,234.5*MM,153*MM,249.3*MM),color=None,fill=(1,1,1))
    x0,x1,y0,y1=35*MM,150*MM,236*MM,238.5*MM
    for i in range(256):
        col=tuple(cmap(i/255)[:3]);left=x0+(x1-x0)*i/256;right=x0+(x1-x0)*(i+1)/256
        # Slight overlap prevents antialias seams between adjacent vector bands.
        p.draw_rect(fitz.Rect(left,y0,min(x1,right+.15),y1),color=None,fill=col,width=0)
    p.draw_rect(fitz.Rect(x0,y0,x1,y1),color=(0,0,0),width=.5)
    for tick in [-20,-10,0,10,20]:
        xpos=x0+(tick+20)/40*(x1-x0)
        p.draw_line((xpos,y1),(xpos,y1+2),color=(0,0,0),width=.6)
        text(p,xpos,242.4*MM,str(tick),8,center=True)
    text(p,(x0+x1)/2,246.4*MM,'Tract service-loss change (h)',8,center=True)
    counts={r:{'below_minus20':int((values[r]<-20).sum()),'above_plus20':int((values[r]>20).sum())} for r in values}
    EDITS['Main/Fig05']={'strict_color_limits_h':[-20,20],'colorbar_ticks_h':[-20,-10,0,10,20],
        'normalization_clip':True,'three_map_values_and_GEOIDs_unchanged':True,
        'polygon_path_count':6945,'polygon_geometry_sequence_sha256':u.digest('\n'.join(geometry_hashes).encode()),
        'old_paint_checked_against_every_exact_saved_tract_value':True,'endpoint_saturation_counts':counts,
        'panels_A_to_D_and_Q4_outlines_unchanged':True,'value_order_SHA256':u.digest('\n'.join(order).encode())}
    return export(d,'Main/Fig05')


def threshold_only():
    old=native('Supplement/FigS06');out=fitz.open();p=out.new_page(width=185*MM,height=145*MM)
    p.show_pdf_page(fitz.Rect(0,0,185*MM,62*MM),old,0,clip=fitz.Rect(0,0,185*MM,62*MM))
    p.show_pdf_page(fitz.Rect(0,66*MM,185*MM,139*MM),old,0,clip=fitz.Rect(0,132*MM,185*MM,205*MM))
    fonts(p,out)
    p.draw_rect(fitz.Rect(3*MM,67*MM,182*MM,76.8*MM),color=None,fill=(1,1,1))
    text(p,61.4*MM,73.26*MM,'B. Functionality threshold: 0.05',9,bold=True,center=True)
    text(p,147.9*MM,73.26*MM,'C. Functionality threshold: 0.75',9,bold=True,center=True)
    record=json.loads(source('docs/reproducibility/SUPPLEMENT_ASSUMPTIONS_LAYOUT_UPDATE_20261006.json'))
    record=next(r for r in record if r['file']=='Supplement/FigS06.pdf')
    for r in record['source_tables']:
        # The offline tables are frozen local archives, not Git-tracked files.
        # The committed display record supplies their expected byte hashes.
        path=u.ORIGINAL/r['path']
        actual=u.sha(path);assert actual==r['sha256']
        SOURCE_HASHES['verified_local_frozen_archive:'+r['path']]={
            'sha256':actual,'bytes':Path(u.lp(path)).stat().st_size,
            'expected_hash_authority':'docs/reproducibility/SUPPLEMENT_ASSUMPTIONS_LAYOUT_UPDATE_20261006.json'}
    kept=[r for r in record['displayed_summary'] if r['gate']!='G0_NO_GATE']
    joint=[r for r in record['displayed_summary'] if r['gate']=='G0_NO_GATE']
    u.write_csv(QA/'THRESHOLD_DISPLAY_VALUES.csv',kept)
    u.write_csv(QA/'JOINT_GATE_ARCHIVED_VALUES.csv',joint)
    EDITS['Supplement/FigS06']={'displayed_gate_cases':['G2_RELAXED_005','G3_STRICT_075'],
        'source_connectivity_fixed':True,'source_only_control_available':False,
        'joint_removal_panel_removed_from_numbered_figure':True,'means_and_5th_95th_ranges_reused_without_recalculation':kept,
        'source_A_and_threshold_graphics_reused_at_native_scale':True}
    old.close();return export(out,'Supplement/FigS06')


def kmeans_only():
    path='Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/kmeans_k_diagnostics.csv'
    q=pd.read_csv(io.BytesIO(source(path)))
    assert q.k.tolist()==list(range(1,11))
    plt.rcParams.update({'font.family':'Arial','font.size':8.5,'pdf.fonttype':42,'axes.linewidth':.6})
    fig,axes=plt.subplots(1,2,figsize=(185/25.4,95/25.4))
    fig.subplots_adjust(left=.115,right=.975,bottom=.21,top=.83,wspace=.37)
    for ax,field,color,title,ylabel in zip(axes,['inertia','silhouette'],['#405b69','#a85827'],
        ['A. Within-cluster sum of squares','B. Silhouette coefficient'],['Inertia','Silhouette coefficient']):
        valid=q[field].notna();shown=q[valid]
        ax.plot(shown.k,shown[field],color=color,marker='o',ms=3.8,lw=1.25)
        ax.set_title(title,fontsize=9.5,fontweight='bold',pad=8)
        ax.set_xlabel('Number of clusters (k)',fontsize=8.5);ax.set_ylabel(ylabel,fontsize=8.5)
        ax.set_xticks(shown.k);ax.tick_params(labelsize=8.5)
        ax.spines[['top','right']].set_visible(False);ax.grid(color='#e6e6e6',lw=.4)
    b=io.BytesIO();fig.savefig(b,format='pdf');plt.close(fig)
    out=fitz.open(stream=b.getvalue(),filetype='pdf')
    u.write_csv(QA/'KMEANS_DISPLAY_VALUES.csv',q.to_dict('records'))
    EDITS['Supplement/FigS09']={'source_table':path,'PCA_panels_removed':True,
        'kmeans_fit_or_k_search_run':False,'saved_inertia_and_silhouette_values_unchanged':True}
    return export(out,'Supplement/FigS09')


def population_contrast():
    d=native('Supplement/FigS10')
    old=plt.get_cmap('YlGnBu')(np.linspace(.15,.85,256))[:,:3]
    new=plt.get_cmap('YlOrBr')(.07+.73*np.linspace(0,1,256)**3)[:,:3]
    teal=np.array(to_rgb('#007c83'));black=np.array(to_rgb('#20272e'))
    populations=0;priorities=0;proof=[]
    for x in streams(d):
        raw=d.xref_stream(x)
        def replace(m):
            nonlocal populations,priorities
            col=np.array([float(m[k]) for k in [1,2,3]])
            if max(abs(col-teal))<1e-6:
                priorities+=1;return ('%.9f %.9f %.9f '%tuple(black)).encode()+m[4]
            if m[4]==b'rg':
                dist=np.max(abs(old-col),axis=1);i=int(dist.argmin())
                if dist[i]<2e-6:
                    populations+=1;return ('%.9f %.9f %.9f rg'%tuple(new[i])).encode()
            return m[0]
        changed=RGB.sub(replace,raw)
        if changed!=raw:
            assert RGB.sub(b'PAINT',raw)==RGB.sub(b'PAINT',changed)
            proof.append(u.digest(RGB.sub(b'PAINT',raw)))
            d.update_stream(x,changed)
    assert populations>2000 and priorities>15,(populations,priorities)
    images=[]
    for x in range(1,d.xref_length()):
        if d.xref_get_key(x,'Subtype')[1]!='/Image':continue
        cs=d.xref_get_key(x,'ColorSpace')[1];m=re.search(r'<([0-9A-Fa-f]+)>',cs)
        if not m:continue
        colors=np.frombuffer(bytes.fromhex(m[1]),dtype=np.uint8).reshape(-1,3)/255
        mapped=[]
        for col in colors:
            dist=np.max(abs(old-col),axis=1);i=int(dist.argmin());assert dist[i]<.01
            mapped.append(np.rint(new[i]*255).astype(np.uint8))
        indices=u.digest(d.xref_stream(x))
        d.xref_set_key(x,'ColorSpace',cs[:m.start(1)]+np.array(mapped,dtype=np.uint8).tobytes().hex()+cs[m.end(1):])
        assert u.digest(d.xref_stream(x))==indices
        images.append({'scalar_index_sha256':indices})
    assert len(images)==1
    EDITS['Supplement/FigS10']={'C_metric':'tract population','C_palette':'YlOrBr t=0.07+0.73*u^3, lighter middle colors',
        'priority_color_all_panels':'#20272e','priority_labels_and_keys_synchronized':True,
        'noncolor_stream_hashes':proof,'population_color_operators':populations,'priority_color_operators':priorities,
        'population_norm_range_geometry_and_rank_identity_unchanged':True,'colorbar_scalar_indices':images}
    return export(d,'Supplement/FigS10')


def merge_resources():
    out=fitz.open();p=out.new_page(width=185*MM,height=231*MM);fonts(p,out)
    text(p,92.5*MM,5.5*MM,'Service-loss outcomes across resource conditions',10,bold=True,center=True)
    colors={'degree-first':'#4daf4a','betweenness-first':'#b59a00','impact-first':'#ff7f00',
            'hospital-first':'#555555','vulnerability-first':'#a65628','random':'#9a9a9a'}
    groups=[(20,'Infrastructure-based',['degree-first','betweenness-first']),
            (82,'Community / equity-informed',['impact-first','hospital-first','vulnerability-first']),
            (150,'Baseline and symbols',['random'])]
    for x,label,keys in groups:
        text(p,x*MM,11.5*MM,label,8.5,bold=True)
        for j,k in enumerate(keys):
            xx=(x+3)*MM;yy=(17+j*5)*MM;col=to_rgb(colors[k])
            if k=='degree-first':
                points=[(xx,yy-2),(xx-2,yy+1.7),(xx+2,yy+1.7),(xx,yy-2)]
                p.draw_polyline(points,color=col,fill=col,closePath=True,width=.4)
            elif k=='impact-first':p.draw_rect(fitz.Rect(xx-1.8,yy-1.8,xx+1.8,yy+1.8),color=col,fill=col,width=.4)
            elif k=='vulnerability-first':p.draw_polyline([(xx-2,yy),(xx,yy-2),(xx+2,yy),(xx,yy+2),(xx-2,yy)],color=col,fill=col,closePath=True,width=.4)
            elif k=='betweenness-first':
                p.draw_line((xx-2,yy),(xx+2,yy),color=col,width=1.4);p.draw_line((xx,yy-2),(xx,yy+2),color=col,width=1.4)
            else:p.draw_circle((xx,yy),1.8,color=col,fill=col,width=.4)
            text(p,(x+8)*MM,yy+2.5,k.capitalize(),8.5,bold=k not in ['betweenness-first','random'])
    p.draw_circle((153*MM,22*MM),1.5,color=(.2,.2,.2),fill=(.2,.2,.2),width=.4)
    text(p,158*MM,23*MM,'Mean',8.5)
    p.draw_line((153*MM,25.5*MM),(153*MM,28.5*MM),color=(.2,.2,.2),width=.6)
    text(p,158*MM,28*MM,'5th-95th percentiles',8)
    text(p,47*MM,35.5*MM,'Crew availability',9,bold=True,center=True)
    text(p,139*MM,35.5*MM,'Repair duration',9,bold=True,center=True)
    titles=['All-tract service loss','Q4 tract service loss','High-low vulnerability service-loss gap','Hospital-tract service loss']
    crops=[(8,35,90,100),(100,35,183,100),(8,102,90,165),(100,102,183,165)]
    records=[]
    for col,stem in enumerate(['Supplement/FigS12','Supplement/FigS13']):
        original=native(stem);clean=fitz.open(stream=original.tobytes(),filetype='pdf');checks=graphics_only(clean)
        graphics_bytes=clean.tobytes();clean.close()
        spans=[(s,line['dir']) for b in original[0].get_text('dict',flags=0)['blocks']
               for line in b.get('lines',[]) for s in line['spans']]
        for row,clip_mm in enumerate(crops):
            clip=fitz.Rect(*(v*MM for v in clip_mm))
            target=fitz.Rect((2+col*93)*MM,(42+row*46)*MM,(88.5+col*93)*MM,(82+row*46)*MM)
            sx=target.width/clip.width;sy=target.height/clip.height
            clean=fitz.open(stream=graphics_bytes,filetype='pdf')
            glyphs=[]
            for x in streams(clean):
                if clean.xref_get_key(x,'Subtype')[1]!='/Form':continue
                coords=re.findall(r'[-+]?[0-9.]+',clean.xref_get_key(x,'BBox')[1])
                if len(coords)!=4:continue
                box=fitz.Rect(*(float(v) for v in coords))
                if box.width>=25 or box.height>=25:continue
                raw=clean.xref_stream(x)
                # Counter the panel's anisotropic reflow only for marker glyphs.
                # Squares remain squares, circles remain circular; centers and
                # all original numerical curve/errorbar vertices are untouched.
                prefix=f'q {1/sx:.12f} 0 0 {1/sy:.12f} 0 0 cm '.encode()
                clean.update_stream(x,prefix+raw+b' Q')
                scaled=[box.x0/sx,box.y0/sy,box.x1/sx,box.y1/sy]
                clean.xref_set_key(x,'BBox','['+' '.join(f'{v:.12f}' for v in scaled)+']')
                glyphs.append({'original_glyph_geometry_sha256':u.digest(raw),'counter_scale':[1/sx,1/sy]})
            assert len(glyphs)==5
            p.show_pdf_page(target,clean,0,clip=clip,keep_proportion=False);clean.close()
            text(p,(target.x0+target.x1)/2,(43+row*46)*MM,chr(65+2*row+col)+'. '+titles[row],8.5,bold=True,center=True)
            for s,direction in spans:
                origin=fitz.Point(s['origin']);bbox=fitz.Rect(s['bbox'])
                if not clip.contains(origin) or not clip.intersects(bbox):continue
                value=s['text'].replace('\xad','-').replace('\xa0',' ')
                if re.match(r'^[ABCD]\.',value):continue
                if value in ['Crew-availability multiplier','Repair-duration multiplier'] and row<3:continue
                xx=target.x0+(origin.x-clip.x0)*sx;yy=target.y0+(origin.y-clip.y0)*sy
                if value in ['Crew-availability multiplier','Repair-duration multiplier']:yy+=2*MM
                if direction[1]<-.5:
                    label='Service-loss gap (h)' if row==2 else 'Service loss (h)'
                    f=fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf')
                    cy=target.y0+((bbox.y0+bbox.y1)/2-clip.y0)*sy
                    yy=cy+f.text_length(label,fontsize=8.5)/2
                    text(p,xx,yy,label,8.5,rotate=90)
                else:
                    # Keep tick labels centered over their original positions.
                    f=fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf')
                    cx=target.x0+((bbox.x0+bbox.x1)/2-clip.x0)*sx
                    text(p,cx,yy,value,8.5,center=True)
            records.append({'source':stem,'source_clip_mm':clip_mm,
                            'target_mm':[v/MM for v in target],'all_original_graphics_after_text_removal':checks,
                            'marker_aspect_compensation':glyphs})
        original.close()
    EDITS['Supplement/FigS11']={'merged_sources':['Supplement/FigS12','Supplement/FigS13'],
        'eight_original_resource_panels_reused':True,'no_means_ranges_or_trajectories_recomputed':True,
        'layout_records':records,'policy_keys_cover_exactly_six_plotted_policies':True,
        'former_S11_baseline_heatmap_retired_after_Fig4_identity_check':True}
    return export(out,'Supplement/FigS11')


def baseline_identity():
    r='Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet'
    d=pd.read_parquet(io.BytesIO(source(r)))
    v=pd.read_parquet(io.BytesIO(source('Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet')))
    q=pd.concat([d,v],ignore_index=True)
    q=q[q.hazard.eq('2pc50')&q.resource_scenario.eq('C57_D1')&q.mapping.eq('M1_UTILITY_003')&q.gate.eq('G1_BASELINE_050')]
    old=pd.read_csv(io.BytesIO(source('provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv')))
    rows=[]
    fields=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr','population_T80_hr']
    for k in ['impact-first','hospital-first','degree-first','vulnerability-first','betweenness-first','random']:
        for f in fields:
            policy=q.loc[q.strategy_id.eq(k),f].mean();ref=q.loc[q.strategy_id.eq('unconstrained'),f].mean()
            saved=old.loc[old.hazard.eq('2pc50')&old.strategy_id.eq(k)&old.metric.eq(f),'mean_paired_difference'].item()
            error=policy-ref-saved;assert abs(error)<1e-10
            rows.append({'policy':k,'metric':f,'Fig4_mean':policy,'Unconstrained_mean':ref,
                         'previous_S11_saved_mean_difference':saved,'identity_error_h':error})
    u.write_csv(QA/'S11_FIG4_NUMERICAL_IDENTITY.csv',rows)
    return {'verified_existing_mean_identities':24,'maximum_absolute_error_h':max(abs(r['identity_error_h']) for r in rows),
            'new_scientific_estimates':False}


def main():
    previous=QA/'SOURCE_HASHES.json'
    if previous.exists():SOURCE_HASHES.update(json.load(open(u.lp(previous),encoding='utf-8')))
    verified=QA/'SOURCE_INPUT_VALIDATION.json'
    if verified.exists():
        inputs=json.load(open(u.lp(verified),encoding='utf-8'))['pinned_cached_sources']
        for rel,record in inputs.items():SOURCE_HASHES[BASE+':'+rel]={'sha256':record['sha256'],'bytes':record['bytes']}
    reference=json.load(open(u.lp(PRIOR/'PRESERVATION_AFTER_PUSH.json'),encoding='utf-8'))
    before=u.protected_snapshot(reference);assert before==reference
    u.dump(QA/'PRESERVATION_BEFORE.json',before)
    old_manifest=u.csv_rows(source('results/figure_review/FIGURE_MANIFEST.csv'))
    old_index=u.csv_rows(source('results/figures/FIGURE_INDEX.csv'))
    caps=u.captions(source('results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode())
    identity=baseline_identity()
    info={}
    for stem,fn in [('Main/Fig01',framework),('Main/Fig05',cap_maps),('Supplement/FigS06',threshold_only),
                    ('Supplement/FigS09',kmeans_only),('Supplement/FigS10',population_contrast),('Supplement/FigS11',merge_resources)]:
        checkpoint=QA/('RENDER_CHECKPOINT_'+stem.replace('/','_')+'.json')
        function_hash=u.digest(inspect.getsource(fn).encode())
        record=json.load(open(u.lp(checkpoint),encoding='utf-8')) if checkpoint.exists() else None
        if record and record['input_commit']==BASE and record['function_hash']==function_hash and all(
            u.sha(ROOT/rel)==sha for rel,sha in record['output_hashes'].items()):
            source('results/figure_review/'+stem+'.pdf')
            info[stem]=record['info'];EDITS[stem]=record['edit'];print(stem,'completed render reused',flush=True)
        else:
            info[stem]=fn()
            u.dump(checkpoint,{'input_commit':BASE,'function_hash':function_hash,'info':info[stem],'edit':EDITS[stem],
                'output_hashes':{rel:u.sha(ROOT/rel) for rel in ['results/figure_review/'+stem+'.pdf',
                    'results/figure_review/'+stem+'.png','results/figure_review/Page_Previews/'+Path(stem).name+'.png']}})
            print(stem,'updated',flush=True)
    s6=next(h for h in caps if h.startswith('Supplementary Figure S6.'))
    caps[s6]=('Dependency mapping and station functionality-threshold sensitivity under 2pc50, reference crew availability and repair-duration multiplier 1.00. '
        '(A) Mapping-weight cutoffs of zero, 1% and the production 3% are compared using the same modeled recovery inputs. '
        '(B/C) Thresholds 0.05 and 0.75 are each compared with the production threshold 0.50 while retaining the same source-connectivity requirement and 14 Core sources. '
        'Only the functionality threshold changes in these comparisons. Impact-first, Hospital-first and Degree-first are the three evaluated policies shown. '
        'Points are mean changes in all-tract population-weighted service loss, and horizontal intervals are 5th-95th realization-difference ranges across the same 1,000 physical realizations, not confidence intervals. '
        'Service loss integrates one minus modeled service availability over 0-480 h. Source connectivity is a modeled service requirement, not electrical-delivery adequacy.')
    s9=next(h for h in caps if h.startswith('Supplementary Figure S9.'))
    caps[s9]=('K-means diagnostics for the 2pc50 residential community typology, using 2,291 eligible tracts and the common standardized feature representation. '
        '(A) Inertia, the within-cluster sum of squared distances, across k=1-10. (B) Silhouette coefficient across k=2-10; the statistic is undefined for one cluster. '
        'The curves provide descriptive support for examining cluster count. Neither a lower inertia nor a local silhouette maximum establishes a unique or universally valid community taxonomy. '
        'These plots do not change the five-class membership shown in Figure 7 or define restoration priorities.')
    s11=next(h for h in caps if h.startswith('Supplementary Figure S11.'))
    caps[s11]=('Service-loss outcomes under 2pc50 for the six scheduled manuscript policies across the tested resource conditions. '
        'Left-column panels A/C/E/G vary crew availability at repair-duration multiplier 1.00; right-column panels B/D/F/H vary repair duration at reference crew availability. '
        'Rows show all-tract population-weighted service loss, Q4 population-weighted service loss, the high-low vulnerability service-loss gap and hospital-linked equal-tract mean service loss. '
        'Crew multipliers are 29/57, 1, 86/57 and 2, displayed as 0.5, 1.0, 1.5 and 2.0. Repair-duration multipliers are 0.75, 1.00, 1.25 and 1.50. '
        'Dots are means and whiskers are 5th-95th realization ranges over 1,000 realizations per policy and condition, not confidence intervals. '
        'The loss integral covers 0-480 h. Q1 and Q4 are the lowest and highest FEMA NRI v1.19 social-vulnerability quartiles. '
        'The gap is the absolute Q4-Q1 group-mean loss difference within each realization before averaging, so it measures separation rather than direction. '
        'Hospital-linked tract service loss is not hospital electricity delivery or clinical capacity. These are discrete, separate crew and duration comparisons, not a crew-by-duration interaction experiment. '
        'The reference-resource absolute outcomes and population T80 are shown in Figure 4. The final GA sequence in Supplementary Figure S5 is not included in these original six-policy resource comparisons.')
    renamed={s6:'Supplementary Figure S6. Dependency mapping and functionality-threshold sensitivity',
             s9:'Supplementary Figure S9. K-means diagnostics',
             s11:'Supplementary Figure S11. Service-loss outcomes across resource conditions'}
    f5=next(h for h in caps if h.startswith('Figure 5.'))
    caps[f5]+=' The E color limits are fixed at -20 and +20 h, exactly at the endpoint tick labels; values below or above those limits use the corresponding endpoint color without changing their stored numerical values.'
    f1=next(h for h in caps if h.startswith('Figure 1.'))
    caps[f1]=caps[f1].replace('Tested crew/duration conditions are shown in Figure 6;','Crew/duration conditions are shown separately in Figure 6;')
    caps={renamed.get(h,h):b for h,b in caps.items() if not h.startswith(('Supplementary Figure S12.','Supplementary Figure S13.'))}
    for h in caps:
        if h.startswith('Supplementary Figure S10.'):
            caps[h]=caps[h].replace('sequential tract population shading','warm sequential tract population shading')
            caps[h]+=' Dark priority markers with white labels contrast with the warm population scale in C; the same first-five-priority marker color is used in all three maps and keys.'
        if h.startswith('Figure 6.'):
            caps[h]=caps[h].replace('Supplementary Figures S12 and S13','Supplementary Figure S11').replace('Figures S12 and S13','Figure S11')
    assert len(caps)==17
    u.write(DEST/'MANUSCRIPT_FACING_CAPTIONS.md','# Manuscript-facing figure captions\n\n'+'\n\n'.join('## '+h+'\n\n'+b for h,b in caps.items())+'\n')
    manifest=[];index=[]
    for row in old_manifest:
        row=row.copy();stem,ext=row['final_name'].rsplit('.',1)
        if stem in RETIRE:
            for rel in [row['current_source_file'],row['mirror_file']]:
                p=ROOT/rel
                assert p.is_relative_to(ROOT)
                if p.exists():
                    assert u.sha(p)==row['sha256']
                    Path(u.lp(p)).unlink()
            preview=DEST/'Page_Previews'/(Path(stem).name+'.png')
            if preview.exists():Path(u.lp(preview)).unlink()
            continue
        row['change_in_this_update']='UPDATED' if stem in info else 'RETAINED'
        if stem in info:
            row.update(parent_source_file=row['current_source_file'],parent_source_commit=BASE,parent_sha256=row['sha256'],
                source_file=row['current_source_file'],source_commit=BASE,sha256=u.sha(ROOT/row['current_source_file']),
                size_mm=' x '.join(f'{v:.3f}' for v in info[stem]['size_mm']),min_font_pt=f"{info[stem]['min_font_pt']:.3f}",
                presentation_generator=GENERATOR,presentation_generator_sha256=u.sha(__file__))
            if stem=='Supplement/FigS11':
                row['source_file']=';'.join('results/figure_review/'+s+'.'+ext for s in ['Supplement/FigS12','Supplement/FigS13'])
            elif stem=='Supplement/FigS09':
                row['source_file']='Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized/kmeans_k_diagnostics.csv'
            if stem in ['Supplement/FigS06','Supplement/FigS11']:
                old_mirror=ROOT/row['mirror_file']
                if old_mirror.exists():
                    assert u.sha(old_mirror) in [row['sha256'],row['parent_sha256']]
                    Path(u.lp(old_mirror)).unlink()
                mirror_name='FigS06_Dependency_and_Threshold_Sensitivity' if stem.endswith('06') else 'FigS11_Resource_Outcomes'
                row['mirror_file']='results/figures/'+mirror_name+'.'+ext
            u.write(ROOT/row['mirror_file'],open(u.lp(ROOT/row['current_source_file']),'rb').read())
        else:assert u.sha(ROOT/row['current_source_file'])==row['sha256'];source(row['current_source_file'])
        idx=next(r.copy() for r in old_index if r['source_path']==row['current_source_file'])
        idx['sha256_or_lfs_oid']=row['sha256']
        idx['file']=Path(row['mirror_file']).name
        if stem in info:idx.update(generator=GENERATOR,notes='Current author-requested figure-only revision; see UPDATE_LOG.md.')
        if stem.endswith('FigS06'):idx.update(scientific_question='How do mapping cutoff and functionality threshold affect service loss with source connectivity held fixed?',scientific_content='Mapping and threshold comparisons; no source-only effect is inferred.')
        if stem.endswith('FigS09'):idx.update(scientific_question='What do the saved K-means inertia and silhouette show across cluster counts?',main_message='K-means diagnostics only; five-class membership unchanged.',scientific_content='Original saved K-means diagnostics; no PCA panels or new clustering.',source_authority=BASE,source_data_path=row['source_file'],source_data_sha256=SOURCE_HASHES[BASE+':'+row['source_file']]['sha256'])
        if stem.endswith('FigS11'):
            ledger='docs/reproducibility/author_suite_final_layout_20261012/RENDER_CHECKPOINT_Supplement_FigS11.json'
            idx.update(scientific_question='How do service-loss outcomes vary across crew availability and repair duration?',main_message='Original S12/S13 combined by outcome row and resource column.',scientific_content='Eight original vector resource panels; baseline policy means are already shown in Fig4.',source_authority=BASE,source_data_path=ledger,source_data_sha256=u.sha(ROOT/ledger))
        manifest.append(row);index.append(idx)
    assert len(manifest)==34
    u.write_csv(DEST/'FIGURE_MANIFEST.csv',manifest);u.write_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    palette=json.loads(source('results/figure_review/CURRENT_CLUSTER_PALETTE.json'))
    palette['applies_to']=['Fig07 A/C'];u.dump(DEST/'CURRENT_CLUSTER_PALETTE.json',palette)
    u.pdfmetrics.registerFont(u.TTFont('SuiteArial','C:/Windows/Fonts/arial.ttf'))
    u.pdfmetrics.registerFont(u.TTFont('SuiteBold','C:/Windows/Fonts/arialbd.ttf'))
    books=[fitz.open(),fitz.open(),fitz.open()]
    for stem,(heading,body) in zip(ACTIVE,caps.items()):
        with fitz.open(u.lp(DEST/(stem+'.pdf'))) as fig:
            books[0 if stem.startswith('Main/') else 1].insert_pdf(fig);books[2].insert_pdf(fig)
        cap=u.caption_pdf(heading,body);books[2].insert_pdf(cap);cap.close()
    old=fitz.open(stream=source('results/figure_review/ALL_FIGURES_WITH_CAPTIONS.pdf'),filetype='pdf')
    books[2].insert_pdf(old,from_page=38,to_page=41);old.close()
    for name,book in zip(['ALL_MAIN_FIGURES','ALL_SUPPLEMENT_FIGURES','ALL_FIGURES_WITH_CAPTIONS'],books):
        u.write(DEST/(name+'.pdf'),book.tobytes(garbage=4,deflate=True));book.close()
    after=u.protected_snapshot(reference);assert before==after
    u.dump(QA/'PRESERVATION_AFTER.json',after);u.dump(QA/'SOURCE_HASHES.json',SOURCE_HASHES)
    u.dump(QA/'INTEGRATION_QA.json',{'baseline_commit':BASE,'active_figures':ACTIVE,
        'figures':[{'current_file':r['current_source_file'],'source_file':r['source_file'],'source_commit':r['source_commit'],'sha256':r['sha256'],'mirror_file':r['mirror_file']} for r in manifest],
        'updated_figures':list(info),'retained_figures':[s for s in ACTIVE if s not in info],
        'retired_numbered_figures':RETIRE,'operator_edits':EDITS,'S11_Fig4_identity':identity,
        'packet_pages':{'main':7,'supplement':10,'with_captions':38},'scientific_results_recomputed':False,
        'new_scientific_fits_or_evaluations':False,'original_worktree_unchanged':before==after,
        'manuscripts_modified':False,'S02_has_no_artwork_caption_or_placeholder':True})
    print('17 numbered figures; one merged resource figure; all science and original staged work preserved.',flush=True)


if __name__=='__main__':main()
