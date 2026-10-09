"""Bounded co-author map, median, legend and sensitivity display corrections.

Reads only stored artwork and existing result tables. No mapping, trajectory,
scheduling, uncertainty estimation, clustering or other scientific stage runs.
"""
from pathlib import Path
from collections import defaultdict
import copy,csv,hashlib,json,re,shutil,subprocess
import fitz
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap,Normalize
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from pypdf.generic import ContentStream,DecodedStreamObject
from la_grid.paths import REPO_ROOT
from la_grid.plotting import apply_coauthor_figure_feedback as shared
from la_grid.plotting.apply_outcome_display_feedback import fonts,sha,text,update_csv
from la_grid.plotting.apply_map_metric_identity_feedback import CLUSTER_COLORS,packets
from la_grid.plotting.refine_policy_cluster_presentation import streams,rgb,near
from la_grid.plotting.build_meeting_figure_collection import tract_geometry

ROOT=REPO_ROOT
REVIEW=ROOT/'results/figure_review'
BASE='515024e19d060d283d85f2a8b3d74072e03b1c32'
TEMP=Path(shared.tempfile.gettempdir())/'la_coauthor_maps_20261008'
MM=72/25.4
GENERATOR=Path(__file__).relative_to(ROOT).as_posix()
shared.BASE_COMMIT=BASE
shared.TEMP=TEMP

def select_median_lines(doc):
    """Retain the largest feature-value median per axis; preserve KDE paths."""
    changes=[]
    for x in streams(doc):
        raw=doc.xref_stream(x)
        if len(raw)>250000 or b' d' not in raw:continue
        obj=DecodedStreamObject();obj.set_data(raw);cs=ContentStream(obj,None)
        state={'stroke':None,'clip':None,'dash':False};stack=[];path=[];rect=None;found=[]
        for i,(args,op) in enumerate(cs.operations):
            if op==b'q':stack.append(copy.deepcopy(state))
            elif op==b'Q':state=stack.pop() if stack else {'stroke':None,'clip':None,'dash':False}
            elif op==b'RG':state['stroke']=tuple(float(a) for a in args)
            elif op==b're':rect=tuple(float(a) for a in args)
            elif op in [b'W',b'W*']:state['clip']=rect
            elif op==b'd':state['dash']=len(args[0])>0
            if op==b'm':path=[(i,args,op)]
            elif op==b'l':path.append((i,args,op))
            if op==b'S' and len(path)==2 and state['dash']:
                a,b=[tuple(float(v) for v in p[1]) for p in path]
                cid=next((cid for cid,col in CLUSTER_COLORS.items() if near(state['stroke'],rgb(col))),None)
                if cid and abs(a[0]-b[0])<1e-6 and abs(a[1]-b[1])>15:
                    found.append({'x':a[0],'clip':state['clip'],'cluster':cid,
                                  'indices':[p[0] for p in path]+[i]})
            if op in [b'S',b's',b'n',b'f',b'f*',b'B',b'B*']:path=[]
        if not found:continue
        groups=defaultdict(list)
        for f in found:groups[f['clip']].append(f)
        assert len(groups)==6 and all(len(g)==5 for g in groups.values())
        deleted=set();retained=[]
        for clip,g in groups.items():
            winner=max(g,key=lambda f:f['x']);retained.append({'axis_clip':clip,'cluster':winner['cluster']})
            for f in g:
                if f is not winner:deleted.update(f['indices'])
        assert len(deleted)==72
        old=cs.operations;cs.operations=[op for i,op in enumerate(old) if i not in deleted]
        assert len(cs.operations)==len(old)-72
        # Every remaining operator is identical; no KDE vertex or value changes.
        doc.update_stream(x,cs.get_data())
        changes.append({'form_xref':x,'medians_before':30,'medians_after':6,'retained':retained})
    assert changes
    return changes

def fig07():
    key='Main/Fig07';doc,before=shared.baseline(key)
    median=select_median_lines(doc);page=doc[0];fonts(page)
    # Rebuild only the two map display panels from existing membership/scores.
    stage=ROOT/'Formal_Experiment_20260923/Stage 7 Output_SOVI_Harmonized'
    status_path=stage/'stage7_full_domain_tract_status.csv'
    top_path=stage/'stage7_top10_slow_vulnerable_tracts.csv'
    status=pd.read_csv(status_path);top=pd.read_csv(top_path)
    status=status[status.scenario.eq('2pc50')].copy();top=top[top.scenario.eq('2pc50')].copy()
    for d in [status,top]:d['tract_id_norm']=d.tract_id.astype(str).str.zfill(11)
    geo=tract_geometry().to_crs('EPSG:3310').merge(status,on='tract_id_norm',validate='one_to_one')
    selected=geo[geo.tract_id_norm.isin(top.tract_id_norm)]
    assert len(geo)==2315 and geo.cluster.notna().sum()==2291 and len(selected)==10
    assert geo.cluster.isna().equals(geo.SlowVulnerable_Hotspot_Score.isna())
    fig=plt.figure(figsize=(185/25.4,86/25.4))
    axes=[fig.add_axes([9/185,18/86,76/185,60/86]),fig.add_axes([94/185,18/86,76/185,60/86])]
    for cid,col in CLUSTER_COLORS.items():
        geo[geo.cluster.eq(cid)].plot(ax=axes[0],color=col,edgecolor='white',lw=.08)
    missing=geo[geo.cluster.isna()]
    missing.plot(ax=axes[0],color='white',edgecolor='#d0d0d0',lw=.1)
    cmap=LinearSegmentedColormap.from_list('july_hotspots',
        ['#2C7BB6','#ABD9E9','#FFFFBF','#F46D43','#8B1E3F'])
    norm=Normalize(0,4)
    geo.plot(column='SlowVulnerable_Hotspot_Score',ax=axes[1],cmap=cmap,norm=norm,
        edgecolor='#eeeeee',lw=.05,missing_kwds={'color':'white','edgecolor':'#d0d0d0','linewidth':.1})
    region=gpd.GeoSeries([geo.geometry.union_all()],crs=geo.crs)
    for ax in axes:
        region.boundary.plot(ax=ax,color='#777777',lw=.8,zorder=7)
        ax.set_axis_off();xmin,ymin,xmax,ymax=geo.total_bounds
        ax.set_xlim(xmin-(xmax-xmin)*.025,xmax+(xmax-xmin)*.025)
        ax.set_ylim(ymin-(ymax-ymin)*.025,ymax+(ymax-ymin)*.025)
        ax.set_aspect('equal')
    selected.boundary.plot(ax=axes[1],color='black',lw=.6,zorder=8)
    fig.text(9/185,1-5/86,'C. Cluster membership',fontsize=9.5,fontweight='bold',va='top')
    fig.text(94/185,1-5/86,'D. Hotspot score',fontsize=9.5,fontweight='bold',va='top')
    cax=fig.add_axes([172/185,21/86,2.2/185,51/86])
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cax,ticks=range(5))
    cb.set_label('Hotspot score',fontsize=8.5,labelpad=2);cb.ax.tick_params(labelsize=7.5,length=2,width=.6)
    cb.outline.set_linewidth(.5)
    handles=[Patch(facecolor=col,label=f'C{cid}') for cid,col in CLUSTER_COLORS.items()]
    handles.append(Patch(facecolor='white',edgecolor='#777777',label='N/A (24)'))
    fig.legend(handles=handles,ncol=3,loc='lower center',bbox_to_anchor=(43/185,1/86),
        frameon=False,fontsize=7.5,handlelength=.9,handletextpad=.3,columnspacing=.7,labelspacing=.3)
    fig.legend(handles=[Line2D([],[],color='black',lw=.6,label='Top-10 hotspot boundary')],
        loc='lower center',bbox_to_anchor=(139/185,1/86),frameon=False,fontsize=7.5,handlelength=1.2,handletextpad=.35)
    map_path=TEMP/'Fig07_maps.pdf';fig.savefig(map_path);plt.close(fig)
    # Remove old map panels without moving or scaling panels A/B.
    page.add_redact_annot(fitz.Rect(0,167*MM,185*MM,page.rect.height),fill=(1,1,1))
    page.apply_redactions(images=2,graphics=2,text=0)
    with fitz.open(map_path) as maps:page.show_pdf_page(fitz.Rect(0,167*MM,185*MM,253*MM),maps,0)
    for hit in page.search_for('Cluster median'):
        page.add_redact_annot(hit,fill=(1,1,1))
    page.apply_redactions(images=0,graphics=0,text=0)
    fonts(page)
    text(page,122.55,90,'Highest cluster median',7.5)
    return shared.finish(doc,key,{'before_sha256':before,'median_selection':'Largest median feature value per axis, not highest KDE peak',
        'median_operator_changes':median,'all_KDE_curve_operators_preserved':True,
        'cluster_palette':CLUSTER_COLORS,'N_A_display':'White; no hatching','region_outline_pt':.8,'Top_10_outline_pt':.6,
        'map_source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [status_path,top_path]},
        'tract_count':2315,'eligible_tract_count':2291,'not_applicable_count':24,'top_10_count':len(selected)})

def s03():
    key='Supplement/FigS03';doc,before=shared.baseline(key);p=doc[0]
    # Identify the current visible native mesh cells after the older embedded Form.
    cells=[d for d in p.get_drawings() if d['fill'] and 3.4<d['rect'].width<3.6
           and 3.1<d['rect'].height<3.25 and d['rect'].y0>320 and d['rect'].x1<410][-8464:]
    assert len(cells)==92**2
    x0=min(d['rect'].x0 for d in cells);y0=min(d['rect'].y0 for d in cells)
    x1=max(d['rect'].x1 for d in cells);y1=max(d['rect'].y1 for d in cells)
    dx=(x1-x0)/92;dy=(y1-y0)/92
    # Hide strictly upper-triangle display cells; retain the full directed input.
    # A single stair-step polygon avoids antialiased seams between masks.
    points=[(x0+dx,y0),(x1,y0),(x1,y0+91*dy)]
    for i in range(90,-1,-1):
        points.extend([(x0+(i+1)*dx,y0+(i+1)*dy),(x0+(i+1)*dx,y0+i*dy)])
    shape=p.new_shape();shape.draw_polyline(points)
    shape.finish(color=None,fill=(1,1,1),closePath=True);shape.commit(overlay=True)
    source=ROOT/'data/travel/travel_task_to_task.csv'
    values=pd.read_csv(source,index_col=0).to_numpy(float);assert values.shape==(92,92)
    return shared.finish(doc,key,{'before_sha256':before,'change':'Only the lower triangle and diagonal displayed',
        'hidden_cells':92*91//2,'visible_cells':92*93//2,'input_file':source.relative_to(ROOT).as_posix(),
        'input_sha256':sha(source),'directed_input_symmetrized':False,
        'max_directional_difference_h':float(np.abs(values-values.T).max()),'all_lower_triangle_native_cells_preserved':True})

def s04():
    key='Supplement/FigS04';doc,before=shared.baseline(key);p=doc[0];fonts(p)
    p.add_redact_annot(fitz.Rect(0,178*MM,185*MM,199*MM),fill=(1,1,1))
    p.apply_redactions(images=0,graphics=2,text=0)
    fonts(p)
    groups=[(29,'Infrastructure-based',['degree-first','centrality-first','betweenness-first','closeness-first']),
        (91,'Community / equity-informed',['impact-first','hospital-first','vulnerability-first']),
        (155,'Baselines',['unconstrained','random'])]
    for x,title,keys in groups:
        text(p,x,181.7,title,7.5,True)
        for i,k in enumerate(keys):
            col=rgb(shared.COLORS[k]);y=186+i*4
            if k not in shared.CORE:col=tuple(.45*c+.55 for c in col)
            p.draw_line((x*MM,(y-1)*MM),((x+6)*MM,(y-1)*MM),color=col,width=1.2 if k in shared.CORE else .7)
            text(p,x+8,y,shared.LABEL[k],7.5,k in shared.CORE)
    return shared.finish(doc,key,{'before_sha256':before,'change':'B/C shared policy legend uses the same three groups as Figure 4A',
        'static_attack_legend_changed':False,'all_curve_geometry_unchanged':True})

def s06():
    key='Supplement/FigS06';doc,before=shared.baseline(key)
    saved=ROOT/'docs/reproducibility/SUPPLEMENT_ASSUMPTIONS_LAYOUT_UPDATE_20261006.json'
    record=next(r for r in json.loads(saved.read_text()) if r['file']=='Supplement/FigS06.pdf')
    # Means/ranges read literally from the existing display record; no recomputation.
    shown=record['displayed_summary'];assert len(shown)==9
    for r in record['source_tables']:assert sha(ROOT/r['path'])==r['sha256']
    output=fitz.open();p=output.new_page(width=185*MM,height=205*MM)
    # Native cutoff panel keeps its physical size and all its vertices/text.
    p.show_pdf_page(fitz.Rect(0,0,185*MM,62*MM),doc,0,clip=fitz.Rect(0,0,185*MM,62*MM))
    fig=plt.figure(figsize=(185/25.4,143/25.4))
    settings=[('G0_NO_GATE','B. Threshold and source requirement removed',[.22,.63,.74,.28]),
              ('G2_RELAXED_005','C. Lower threshold (0.05)',[.165,.14,.335,.30]),
              ('G3_STRICT_075','D. Higher threshold (0.75)',[.635,.14,.335,.30])]
    for gate,title,box in settings:
        ax=fig.add_axes(box)
        for i,key_policy in enumerate(['impact-first','hospital-first','degree-first']):
            r=next(r for r in shown if r['policy']==key_policy and r['gate']==gate)
            col=shared.COLORS[key_policy]
            ax.plot([r['p05_h'],r['p95_h']],[i,i],color=col,lw=1.15)
            ax.scatter([r['mean_h']],[i],c=col,marker={'impact-first':'s','hospital-first':'o','degree-first':'^'}[key_policy],
                       s=20,zorder=3,lw=.5)
        ax.set_yticks(range(3),['Impact-first','Hospital-first','Degree-first'])
        ax.set_ylim(2.5,-.5);ax.set_title(title,pad=8)
        ax.axvline(0,color='#555555',lw=.65,zorder=0);ax.grid(axis='x',lw=.4,alpha=.25)
        ax.spines[['top','right']].set_visible(False)
        if gate=='G0_NO_GATE':ax.set_xlim(-8,.25);ax.set_xlabel('Change in all-tract service loss (h)',labelpad=6)
        else:
            ax.set_xlim(-.17,.05);ax.set_xticks([-.15,-.10,-.05,0,.05])
            ax.set_xlabel('Change in all-tract\nservice loss (h)',fontsize=7.5,labelpad=5)
    temp=TEMP/'S06_assumption_panels.pdf';fig.savefig(temp);plt.close(fig)
    with fitz.open(temp) as d:p.show_pdf_page(fitz.Rect(0,62*MM,185*MM,205*MM),d,0)
    doc.close()
    return shared.finish(output,'Supplement/FigS06',{'before_sha256':before,
        'change':'Split the two threshold cases into C/D, with identical hour limits and zero references',
        'mean_and_range_values_reused_exactly':shown,'source_display_record':saved.relative_to(ROOT).as_posix(),
        'source_display_record_sha256':sha(saved),'source_table_sha256_verified':record['source_tables'],
        'no_interval_or_objective_recalculation':True})

def s07_caption_evidence():
    path=ROOT/'results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv'
    data=pd.read_csv(path)
    q=data[data.strategy.isin(['impact-first','hospital-first']) & data.time_hr.isin([0,24,48,72,120])]
    cols=['strategy','time_hr','population_dependency_weighted_R_conn',
          'population_dependency_weighted_fixed_precomputed_best_path_connection']
    return {'source_file':path.relative_to(ROOT).as_posix(),'source_sha256':sha(path),
            'displayed_curves_changed':False,'caption_source_values':q[cols].to_dict('records')}

def integrate(records,trend):
    changed={r['file']:r for r in records}
    def idx(row):
        source=ROOT/row['source_path'];key=source.relative_to(REVIEW).with_suffix('.pdf').as_posix()
        if key in changed:
            shutil.copy2(source,ROOT/'results/figures'/row['file'])
            row.update(sha256_or_lfs_oid='sha256:'+sha(source),generator=GENERATOR,
                       notes='Co-author-requested median emphasis, map outlines, grouped policy key, lower-triangle display and separate threshold panels.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',idx)
    def manifest(row):
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key in changed:
            r=changed[key];p=REVIEW/row['final_name']
            row.update(source_file=p.relative_to(ROOT).as_posix(),current_source_file=p.relative_to(ROOT).as_posix(),
                       source_commit='COAUTHOR_MAP_AND_LEGEND_UPDATE_20261008',sha256=sha(p),
                       parent_source_commit=BASE,parent_source_file=p.relative_to(ROOT).as_posix(),
                       parent_sha256=shared.baseline_digest('results/figure_review/'+row['final_name']),
                       size_mm='%.3f x %.3f'%tuple(r['size_mm']),min_font_pt=f"{r['min_font_pt']:.3f}",
                       status='COAUTHOR_PRESENTATION_UPDATE')
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    p=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';c=subprocess.check_output(['git','show',BASE+':results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md'],cwd=ROOT).decode('utf-8')
    c=c.replace('dashed lines mark cluster medians.',
                'the single dashed line in each feature plot marks the highest cluster median, while all cluster distributions remain shown.')
    c=c.replace('including 24 not-applicable tracts shown as N/A rather than as zero or low vulnerability.',
                'including 24 not-applicable tracts shown in white as N/A rather than as zero or low vulnerability. Gray outlines delineate the study region; black outlines identify Top-10 hotspots on D only.')
    c=c.replace('(B) Directed task-to-task road-travel times, with rows denoting origins and columns destinations; values are in hours.',
                '(B) Lower-triangle display of directed task-to-task road-travel times, with rows denoting origins and columns destinations; values are in hours. The opposite direction is not assumed equal: upper-triangle entries are omitted for display only, while the complete directed matrix remains the model input.')
    start=c.index('## Supplementary Figure S4.');end=c.index('## Supplementary Figure S5.',start)
    block=c[start:end].rstrip()+' The grouped policy legend applies jointly to B/C and uses the same infrastructure-based, community/equity-informed and baseline groups as Figure 4A.\n\n'
    c=c[:start]+block+c[end:]
    c=c.replace('(C) Functionality thresholds 0.05 and 0.75 relative to the production value 0.50, with the same 14 Core sources. B/C display',
        '(C/D) Functionality thresholds 0.05 and 0.75 are displayed separately, each relative to the production value 0.50 with the same 14 Core sources; both panels share the same hour scale and zero reference. B/C/D display')
    start=c.index('## Supplementary Figure S7.');end=c.index('## Supplementary Figure S8.',start)
    block=c[start:end].rstrip()+(' In A, source-connected availability begins near zero and rises earlier with the full network than with the fixed path. '
        'At 24 h, the full-network means are about 0.25-0.27 versus 0.13 with the fixed path; at 48 h, they are about 0.83-0.85 versus 0.63-0.67. '
        'The gap narrows by 72 h, and both approaches reach 1 by 120 h. These are connectivity-weighted modeled availability values, not electricity-delivery fractions.\n\n')
    c=c[:start]+block+c[end:];p.write_text(c,encoding='utf-8');packets(c)
    authority=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';a=json.loads(authority.read_text())
    a['current_code_files']=[r for r in a['current_code_files'] if r['path']!=GENERATOR]+[
        {'path':GENERATOR,'sha256':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),
         'tracked_in_current_git':True}]
    authority.write_text(json.dumps(a,indent=2)+'\n')
    report={'base_commit':BASE,'figures':records,'S07_trend_caption':trend,
            'scientific_stage_invoked':False,'scientific_source_tables_changed':False}
    (ROOT/'docs/reproducibility/COAUTHOR_MAP_LEGEND_FEEDBACK_20261008.json').write_text(json.dumps(report,indent=2)+'\n')

def main():
    TEMP.mkdir(exist_ok=True)
    records=[]
    for fn in [fig07,s03,s04,s06]:
        print('Applying',fn.__name__,flush=True);records.append(fn())
    integrate(records,s07_caption_evidence())
    print('Complete display set and captions updated; no scientific stage run.',flush=True)

if __name__=='__main__':main()
