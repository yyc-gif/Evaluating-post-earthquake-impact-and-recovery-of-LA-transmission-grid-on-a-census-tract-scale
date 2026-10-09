"""Distribution and policy visibility corrections from existing result tables.

No model, mapping, sampling, scheduling, trajectory, or formal result is changed.
"""
from pathlib import Path
import csv,hashlib,json,re,shutil,subprocess,tempfile
import fitz
import geopandas as gpd
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from la_grid.paths import REPO_ROOT
from la_grid.plotting import apply_coauthor_figure_feedback as common
from la_grid.plotting.apply_outcome_display_feedback import fonts,sha,text,update_csv
from la_grid.plotting.apply_map_metric_identity_feedback import packets
from la_grid.plotting.build_meeting_figure_collection import tract_geometry,map_points

ROOT=REPO_ROOT; REVIEW=ROOT/'results/figure_review'; MM=72/25.4
BASE='34e93cae76fb3c229909b4044b761d88265bfc18'
TEMP=Path(tempfile.gettempdir())/'la_distribution_strategy_20261008'
SUITE=ROOT/'results/revised_suite/LA_Grid_Revised_Suite_20260925'
GENERATOR=Path(__file__).relative_to(ROOT).as_posix()
CORE=['impact-first','hospital-first','degree-first','vulnerability-first']
OTHER=['centrality-first','betweenness-first','closeness-first','random']
common.BASE_COMMIT=BASE;common.TEMP=TEMP
plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],'font.size':7.5,
    'axes.titlesize':9.5,'axes.titleweight':'bold','axes.labelsize':8.5,
    'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,
    'axes.linewidth':.6,'pdf.fonttype':42,'figure.facecolor':'white'})


def source_record(p):
    return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}


def curves(ax,data,column,policies,horizon,ylabel=None,ylim=None):
    used=[]
    # Separate frames prevent the emphasized curves hiding other policies.
    for key in policies+['unconstrained']:
        q=data[data.strategy_id.eq(key)].sort_values('time_hr')
        assert not q.empty and not q.time_hr.duplicated().any()
        q=q[q.time_hr.le(horizon)]
        ax.plot(q.time_hr,q[column],color=common.COLORS[key],ls='-',
                lw=1.3 if key=='unconstrained' else 1.15 if key in CORE else 1.0,
                alpha=1.0,label=common.LABEL[key])
        used.append({'strategy':key,'column':column,'rows':len(q)})
    ax.set_xlim(0,horizon)
    if ylim is not None:ax.set_ylim(*ylim)
    if ylabel:ax.set_ylabel(ylabel)
    ax.spines[['top','right']].set_visible(False)
    ax.grid(color='#e6e6e6',lw=.4,zorder=0)
    return used


def s01():
    key='Supplement/FigS01';doc,before=common.baseline(key)
    hazards=['LongBeach','SanFernando','Northridge','2pc50']
    labels=['Long Beach','San Fernando','Northridge','2pc50']
    colors=['#366e9f','#00856a','#9a7559','#a65628']
    values=[];sources=[]
    for hazard in hazards:
        p=SUITE/'Stage 1 Output_expanded'/f'MC_Device_Damage_AvgDS_{hazard}.csv'
        v=pd.read_csv(p).avg_damage_state.to_numpy(float)
        assert len(v)==92 and np.isfinite(v).all() and (v>=0).all() and (v<=4).all()
        values.append(v);sources.append(source_record(p))
    fig,ax=plt.subplots(figsize=(185/25.4,66/25.4))
    fig.subplots_adjust(left=.13,right=.985,bottom=.23,top=.86)
    vplot=ax.violinplot(values,positions=range(4),widths=.62,showmeans=False,
                       showmedians=False,showextrema=False,bw_method='scott',points=160)
    quartiles=[]
    for i,(v,col,body) in enumerate(zip(values,colors,vplot['bodies'])):
        body.set_facecolor(col);body.set_edgecolor(col);body.set_alpha(.45);body.set_linewidth(.65)
        q1,med,q3=np.quantile(v,[.25,.5,.75]);low=float(v.min());high=float(v.max())
        ax.plot([i,i],[low,high],color=col,lw=.7)
        ax.plot([i,i],[q1,q3],color='#26343d',lw=1.4,solid_capstyle='butt')
        ax.plot([i-.055,i+.055],[med,med],color='white',lw=1.0)
        quartiles.append({'hazard':hazards[i],'station_count':len(v),'min':low,'q25':float(q1),'median':float(med),'q75':float(q3),'max':high})
    ax.set_ylim(-.05,4.15);ax.set_yticks(range(5));ax.set_xticks(range(4),labels)
    ax.set_ylabel('Mean substation damage state')
    ax.set_title('A. Distribution of substation damage severity',pad=6)
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',lw=.4,color='#e5e5e5')
    f=TEMP/'S01_violin.pdf';fig.savefig(f);plt.close(fig)
    p=doc[0];rect=fitz.Rect(0,0,185*MM,66*MM)
    p.add_redact_annot(rect,fill=(1,1,1));p.apply_redactions(images=2,graphics=2,text=0)
    with fitz.open(f) as d:p.show_pdf_page(rect,d,0)
    return common.finish(doc,key,{'before_sha256':before,'change':'Violin density of the same station-average values, median/IQR/range; initial-service maps unchanged.',
        'scientific_sources':sources,'distribution_domain':'92 station means per hazard, not pooled individual damage draws',
        'density_rule':'Scott bandwidth, display only; source values unchanged','quartiles':quartiles,'initial_service_maps_changed':False})


def fig04():
    key='Main/Fig04';doc,before=common.baseline(key)
    path=SUITE/'Stage 6 Output_expanded/ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv'
    data=pd.read_csv(path);data=data[data.hazard.eq('2pc50')]
    assert set(data.strategy_id.unique())==set(CORE+OTHER+['unconstrained'])
    fig=plt.figure(figsize=(185/25.4,86/25.4))
    fig.text(.5,.97,'A. Population-weighted service recovery',ha='center',va='top',fontsize=9.5,fontweight='bold')
    specs=[(.105,CORE,'Four focal policies'),(.59,OTHER,'Other scheduled policies')]
    used=[]
    for x,policies,title in specs:
        ax=fig.add_axes([x,.205,.375,.625])
        used+=curves(ax,data,'mean_population_availability_proxy',policies,100,
                     'Population-weighted\nservice availability' if x<.2 else None,(-.02,1.04))
        ax.set_xticks([0,25,50,75,100]);ax.set_yticks([0,.2,.4,.6,.8,1]);ax.set_title(title,fontsize=8.5,pad=6)
    fig.text(.535,.025,'Time after earthquake (h)',ha='center',fontsize=8.5)
    f=TEMP/'Fig04_separated_curves.pdf';fig.savefig(f);plt.close(fig)
    p=doc[0];rect=fitz.Rect(0,0,185*MM,86*MM)
    p.add_redact_annot(rect,fill=(1,1,1));p.apply_redactions(images=2,graphics=2,text=0)
    with fitz.open(f) as d:p.show_pdf_page(rect,d,0)
    fonts(p)
    keyrect=fitz.Rect(25*MM,89*MM,185*MM,112*MM)
    p.add_redact_annot(keyrect,fill=(1,1,1));p.apply_redactions(images=0,graphics=2,text=0);fonts(p)
    groups=[(35,'Infrastructure-based',['degree-first','centrality-first','betweenness-first','closeness-first']),
            (95,'Community / equity-informed',['impact-first','hospital-first','vulnerability-first']),
            (156,'Baselines',['unconstrained','random'])]
    for x,title,policies in groups:
        text(p,x,92.5,title,7.5,True)
        for i,k in enumerate(policies):
            col=tuple(int(common.COLORS[k][j:j+2],16)/255 for j in [1,3,5]);y=97+i*4
            p.draw_line((x*MM,(y-1)*MM),((x+6)*MM,(y-1)*MM),color=col,width=1.15)
            text(p,x+8,y,common.LABEL[k],7.5,k in CORE+['unconstrained'])
    return common.finish(doc,key,{'before_sha256':before,'scientific_sources':[source_record(path)],
        'displayed_series':used,'change':'Same-scale adjacent views: focal policies and other policies, each with Unconstrained; all solid and opaque.',
        'outcome_panel_B_changed':False,'all_eight_scheduled_policies_preserved':True})


def grouped_key(fig,top_y_mm,height):
    groups=[(27,'Infrastructure-based',['degree-first','centrality-first','betweenness-first','closeness-first']),
        (89,'Community / equity-informed',['impact-first','hospital-first','vulnerability-first']),
        (153,'Baselines',['unconstrained','random'])]
    for x,title,policies in groups:
        fig.text(x/185,1-top_y_mm/height,title,fontsize=7.5,fontweight='bold',va='top')
        for i,k in enumerate(policies):
            y=1-(top_y_mm+5.0+i*4.0)/height
            fig.add_artist(Line2D([x/185,(x+6)/185],[y,y],transform=fig.transFigure,color=common.COLORS[k],lw=1.15))
            fig.text((x+8)/185,y,common.LABEL[k],fontsize=7.5,va='center',fontweight='bold' if k in CORE+['unconstrained'] else 'normal')


def s04():
    key='Supplement/FigS04';old,before=common.baseline(key)
    path=SUITE/'Stage 6 Output_expanded/NETWORK_TOPOLOGY_DISPLAY_CURVES_2pc50.csv'
    data=pd.read_csv(path);assert set(data.strategy_id.unique())==set(CORE+OTHER+['unconstrained'])
    lower_height=154
    fig=plt.figure(figsize=(185/25.4,lower_height/25.4));used=[]
    for row,(col,title,ylim,label) in enumerate([
        ('mean_lcc_fraction','B. Largest connected component fraction',(-.02,1.04),'Largest component\nfraction'),
        ('mean_lcc_average_degree','C. Average degree within the largest component',(-.15,7.3),'Mean degree')]):
        top=5+row*62
        fig.text(.5,1-top/lower_height,title,fontsize=9.5,fontweight='bold',ha='center',va='top')
        for x,policies in [(.105,CORE),(.59,OTHER)]:
            ax=fig.add_axes([x,1-(top+48)/lower_height,.375,36/lower_height])
            used+=curves(ax,data,col,policies,120,label if x<.2 else None,ylim)
            ax.set_xticks([0,30,60,90,120]);ax.set_xlabel('Time after earthquake (h)',fontsize=7.5,labelpad=3)
            if row==0:ax.set_title('Four focal policies' if x<.2 else 'Other scheduled policies',fontsize=7.5,pad=4)
    grouped_key(fig,130,lower_height)
    f=TEMP/'S04_separated_dynamic.pdf';fig.savefig(f);plt.close(fig)
    doc=fitz.open();p=doc.new_page(width=185*MM,height=216*MM)
    p.show_pdf_page(fitz.Rect(0,0,185*MM,62*MM),old,0,clip=fitz.Rect(0,0,185*MM,62*MM))
    with fitz.open(f) as d:p.show_pdf_page(fitz.Rect(0,62*MM,185*MM,216*MM),d,0)
    old.close()
    return common.finish(doc,key,{'before_sha256':before,'scientific_sources':[source_record(path)],'displayed_series':used,
        'static_panel_A_changed':False,'all_eight_scheduled_policies_preserved':True,
        'change':'B/C have identical-scale focal and other-policy views; solid opaque lines, common grouped policy key.'})


def s10():
    key='Supplement/FigS10';old,before=common.baseline(key);old.close()
    paths=[ROOT/'Data/substation_graph_CEC_nodes_expanded.csv',ROOT/'Data/Substations_PGA_IDW_CEC_expanded.csv',
        ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv',ROOT/'Data/hospital_with_tract_expanded.csv',
        ROOT/'provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv',
        ROOT/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json',
        ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_FIRST_SEQUENCE.json']
    geo=tract_geometry().to_crs('EPSG:3310');assert len(geo)==2315
    nodes=pd.read_csv(paths[0],dtype={'id':str});names=pd.read_csv(paths[1],dtype={'id':str})[['id','NAME']]
    pts=map_points(nodes,geo.crs).merge(names,on='id',validate='one_to_one');assert len(pts)==92
    m=pd.read_csv(paths[2],dtype={'tract_id':str,'substation_id':str});m['tract_norm']=m.tract_id.str.replace(r'\.0$','',regex=True).str.zfill(11)
    h=pd.read_csv(paths[3],dtype={'GEOID':str});hids=set(h.GEOID.str.replace(r'\.0$','',regex=True).str.zfill(11))
    eligible=set(m.loc[m.tract_norm.isin(hids)&m.weight.gt(0),'substation_id']) if 'weight' in m else set(m.loc[m.tract_norm.isin(hids),'substation_id'])
    meta=pd.read_csv(paths[4],dtype={'tract_id':str});q4=set(meta.loc[meta.SOVI_quartile.eq('Q4'),'tract_id'])
    rules=json.loads(paths[5].read_text())['2pc50'];v=json.loads(paths[6].read_text());assert len(q4)==v['Q4_tract_count']==579
    specs=[('hospital-first',rules['hospital-first'],hids,'A. Hospital-first'),
           ('vulnerability-first',v['ordered_station_ids'],q4,'B. Vulnerability-first'),
           ('impact-first',rules['impact-first'],set(),'C. Impact-first')]
    fig=plt.figure(figsize=(185/25.4,264/25.4));records=[];bounds=geo.total_bounds
    xmin,ymin,xmax,ymax=bounds;dx=xmax-xmin;dy=ymax-ymin
    assert geo.population.ge(0).all()
    positive=geo[geo.population.gt(0)];norm=LogNorm(vmin=max(1,float(positive.population.min())),vmax=float(positive.population.max()))
    pop_cmap=LinearSegmentedColormap.from_list('population_context',plt.get_cmap('Blues')(np.linspace(.1,.65,256)))
    for i,(policy,sequence,highlight,title) in enumerate(specs):
        rowtop=6+i*88
        fig.text(.5,1-rowtop/264,title,ha='center',va='top',fontsize=9.5,fontweight='bold')
        ax=fig.add_axes([.035,1-(rowtop+75)/264,.60,66/264])
        if i<2:geo.plot(ax=ax,color=np.where(geo.tract_id_norm.isin(highlight),'#e0d6e9','#f8f8f8'),edgecolor='#d2d2d2',lw=.08)
        else:
            geo.plot(ax=ax,color='#d4d4d4',edgecolor='#eeeeee',lw=.06)
            positive.plot(ax=ax,column='population',cmap=pop_cmap,norm=norm,edgecolor='#eeeeee',lw=.06)
        ax.scatter(pts.geometry.x,pts.geometry.y,s=7,c='#89959c',edgecolors='white',lw=.2,zorder=3)
        if i==0:
            q=pts[pts.id.isin(eligible)];ax.scatter(q.geometry.x,q.geometry.y,s=9,c='#a65628',edgecolors='white',lw=.2,zorder=4)
        top=list(map(str,sequence[:5]));assert len(sequence)==len(set(sequence))==92
        selected=pts[pts.id.isin(top)];assert len(selected)==5
        accent='#007c83';ax.scatter(selected.geometry.x,selected.geometry.y,s=18,c=accent,edgecolors='white',lw=.4,zorder=5)
        ax.set_xlim(xmin-dx*.025,xmax+dx*.025);ax.set_ylim(ymin-dy*.025,ymax+dy*.025);ax.set_aspect('equal');ax.set_axis_off()
        fig.canvas.draw();placed=[]
        tablex=.685
        fig.text(tablex,1-(rowtop+14)/264,'Rank   Substation',fontsize=8.5,fontweight='bold')
        for j,station in enumerate(top):
            q=pts[pts.id.eq(station)].iloc[0];point=ax.transData.transform((q.geometry.x,q.geometry.y))
            offsets=[(8,8),(-8,8),(8,-8),(-8,-8),(0,14),(14,0),(0,-14),(-14,0)]
            def dist(offset):
                center=point+np.asarray(offset)*fig.dpi/72
                return min([np.linalg.norm(center-z) for z in placed] or [1000])
            chosen=max(offsets,key=dist);placed.append(point+np.asarray(chosen)*fig.dpi/72)
            ax.annotate(str(j+1),(q.geometry.x,q.geometry.y),xytext=chosen,textcoords='offset points',
                ha='center',va='center',fontsize=7.5,fontweight='bold',color='white',
                bbox={'boxstyle':'circle,pad=.16','fc':accent,'ec':'white','lw':.4},
                arrowprops={'arrowstyle':'-','color':accent,'lw':.5,'shrinkA':3,'shrinkB':1},zorder=6)
            name=str(q.NAME).replace('TARZANA(STATION U)','TARZANA (STATION U)')
            fig.text(tablex,1-(rowtop+24+j*9)/264,str(j+1),fontsize=8,color=accent,fontweight='bold')
            fig.text(tablex+.035,1-(rowtop+24+j*9)/264,name,fontsize=7.5,color='#26343d')
            records.append({'policy':policy,'rank':j+1,'station_id':station,'name':str(q.NAME),'label_offset_pt':chosen})
        handles=[Line2D([],[],marker='o',ls='none',color='#89959c',ms=3,label='Substations'),
                 Line2D([],[],marker='o',ls='none',color=accent,ms=4,label='First five priorities')]
        if i<2:handles.insert(0,Patch(facecolor='#e0d6e9',label='Hospital-linked tracts' if i==0 else 'Highest-vulnerability quartile'))
        if i==0:handles.append(Line2D([],[],marker='o',ls='none',color='#a65628',ms=3,label='Hospital-priority substations'))
        fig.legend(handles=handles,ncol=2 if i==0 else 3,frameon=False,loc='upper center',
            bbox_to_anchor=(.37,1-(rowtop+75)/264),fontsize=7.5,handlelength=.8,columnspacing=.8,handletextpad=.3,labelspacing=.3)
        if i==2:
            cax=fig.add_axes([.70,1-(rowtop+69)/264,.255,3.2/264]);cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=pop_cmap),cax=cax,orientation='horizontal')
            ticks=[v for v in [1,10,100,1000,10000] if norm.vmin<=v<=norm.vmax];cb.set_ticks(ticks);cb.set_ticklabels([f'{v:,}' for v in ticks]);cb.minorticks_off()
            cb.set_label('Tract population (log scale)',fontsize=7.5,labelpad=2);cb.ax.tick_params(labelsize=7.0,length=2);cb.outline.set_linewidth(.5)
    f=TEMP/'S10_projected_maps.pdf';fig.savefig(f);plt.close(fig)
    return common.finish(fitz.open(f),key,{'before_sha256':before,'scientific_sources':[source_record(p) for p in paths],
        'display_crs':'EPSG:3310','equal_aspect':True,'same_extent_all_panels':True,'station_orders_changed':False,
        'top_five_stations':records,'maximum_label_offset_pt':14,'long_cross_map_leaders_removed':True,
        'impact_background':'Existing tract population, continuous log color scale; context, not the Impact-first score.'})


def s11():
    key='Supplement/FigS11';old,before=common.baseline(key);old.close()
    p=ROOT/'provenance/figure_review_history/candidate_v2.1/CROSS_HAZARD_POLICY_EFFECTS.csv';data=pd.read_csv(p)
    metrics=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr','population_T80_hr']
    labels=['All-tract\nservice loss','Q4 tract\nservice loss','Hospital-tract\nservice loss','Time to 80%\nservice']
    order=CORE+OTHER;values=np.empty((8,4))
    for i,k in enumerate(order):
        for j,m in enumerate(metrics):
            q=data[data.hazard.eq('2pc50')&data.strategy_id.eq(k)&data.metric.eq(m)]
            assert len(q)==1 and int(q.n_paired.iloc[0])==1000
            values[i,j]=q.mean_paired_difference.iloc[0]
    limit=float(abs(values).max());fig=plt.figure(figsize=(185/25.4,118/25.4));ax=fig.add_axes([.245,.20,.60,.66])
    cmap=plt.get_cmap('RdBu_r');im=ax.imshow(values,cmap=cmap,vmin=-limit,vmax=limit,aspect='auto');ax.grid(False)
    ax.set_xticks(range(4),labels);ax.set_yticks(range(8),[common.LABEL[k] for k in order]);ax.tick_params(length=0,pad=5)
    fig.text(.5,.97,'2pc50 policy changes relative to Unconstrained',fontsize=9.5,fontweight='bold',ha='center',va='top')
    # This rule separates the time-to-threshold column from integral outcomes.
    ax.axvline(2.5,color='white',lw=1.5)
    for i,k in enumerate(order):
        ax.get_yticklabels()[i].set_fontweight('bold' if k in CORE else 'normal')
        for j in range(4):
            c=cmap((values[i,j]+limit)/(2*limit))[:3];lum=sum(w*v for w,v in zip([.2126,.7152,.0722],c))
            ax.text(j,i,f'{values[i,j]:+.2f}',ha='center',va='center',fontsize=7.5,color='white' if lum<.45 else '#15232a')
    cb=fig.colorbar(im,cax=fig.add_axes([.875,.20,.028,.66]));cb.set_label('Mean change (h)',fontsize=8.5);cb.ax.tick_params(labelsize=7.5)
    fig.text(.525,.025,'Service loss: 0-480 h integral; recovery time: first reaching 80% service',ha='center',fontsize=7.5)
    f=TEMP/'S11_metric_roles.pdf';fig.savefig(f);plt.close(fig)
    return common.finish(fitz.open(f),key,{'before_sha256':before,'scientific_sources':[source_record(p)],
        'change':'Parallel service-loss labels; time-to-80% column explicitly distinct from integrals; same saved values and common hour color scale.',
        'metrics':metrics,'display_values':values.tolist(),'metric_relationship_review':'docs/reproducibility/DISTRIBUTION_STRATEGY_METRIC_REVIEW_20261008.json'})


def integrate(records):
    changed={r['file']:r for r in records}
    def index(row):
        p=ROOT/row['source_path'];key=p.relative_to(REVIEW).with_suffix('.pdf').as_posix()
        if key in changed:
            shutil.copy2(p,ROOT/'results/figures'/row['file'])
            row.update(generator=GENERATOR,sha256_or_lfs_oid='sha256:'+sha(p),notes='Violin distributions, separated policy views, projected parallel priority maps and distinct metric roles.')
    update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
    def manifest(row):
        key=Path(row['final_name']).with_suffix('.pdf').as_posix()
        if key in changed:
            p=REVIEW/row['final_name'];v=changed[key]
            row.update(source_commit='DISTRIBUTION_STRATEGY_UPDATE_20261008',sha256=sha(p),
                source_file=p.relative_to(ROOT).as_posix(),current_source_file=p.relative_to(ROOT).as_posix(),
                parent_source_commit=BASE,parent_source_file=p.relative_to(ROOT).as_posix(),
                parent_sha256=common.baseline_digest('results/figure_review/'+row['final_name']),
                size_mm='%.3f x %.3f'%tuple(v['size_mm']),min_font_pt=f"{v['min_font_pt']:.3f}",status='AUTHOR_REQUESTED_CURRENT_DISPLAY')
    update_csv(REVIEW/'FIGURE_MANIFEST.csv',manifest)
    p=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';c=subprocess.check_output(['git','show',BASE+':results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md'],cwd=ROOT).decode('utf-8')
    at=c.index('## Figure 4.');end=c.index('## Figure 5.',at)
    block=c[at:end].rstrip()+(' Panel A uses two adjacent views with identical axes: Impact-first, Hospital-first, Degree-first and Vulnerability-first in the left view, and Centrality-first, Betweenness-first, Closeness-first and Random in the right. Unconstrained is shown in both as the same reference. Every scheduled policy remains visible; solid opaque curves and separated views prevent secondary policies from being hidden beneath the focal comparisons.\n\n')
    c=c[:at]+block+c[end:]
    at=c.index('## Supplementary Figure S1.');end=c.index('## Supplementary Figure S3.',at)
    block=c[at:end]
    block=re.sub(r'\(A\).*?(?=\(B\))',
        '(A) Violin distributions of the average damage-state value for each substation in each scenario. The width is a smoothed density across station averages, not a distribution pooled over individual damage draws. The dark central segment is the interquartile range, the white median mark gives the median, and the thin line spans the observed station-average range. No horizontal jitter or station point cloud is used. ',block,flags=re.S)
    c=c[:at]+block+c[end:]
    at=c.index('## Supplementary Figure S4.');end=c.index('## Supplementary Figure S5.',at)
    block=c[at:end].rstrip()+(' B and C each separate the four focal policies from the four other scheduled policies, with identical left/right axes and the same Unconstrained reference in both. No policy is omitted or made nearly transparent. Curves show realization-mean network metrics without an uncertainty interval.\n\n')
    c=c[:at]+block+c[end:]
    at=c.index('## Supplementary Figure S10.');end=c.index('## Supplementary Figure S11.',at)
    block=('## Supplementary Figure S10. Hospital, vulnerability and population-impact repair priorities\n\n'
        '(A) Hospital-linked tracts and substations receiving hospital priority. (B) Q4 tracts, the highest social-vulnerability quartile. (C) Tract population provides continuous geographic context on a logarithmic scale; it is not the Impact-first station score or a thresholded highest-population set. Numbered short station locators correspond to the adjacent rank-and-name list of the first five stations in each fixed sequence. All three maps use the same EPSG:3310 projection, equal physical aspect and common extent. Hospital-first ranks hospital-linked tract counts, with mapped population as the tie-break. Vulnerability-first uses Q4 mapped population dependency; ties use total mapped population and station ID. Impact-first ranks the mapped population fraction affected by a station removal in the intact-graph scoring model, including network/source-path effects; it does not simply rank directly mapped tract population. The repaired objects are substations, not tracts. Actual task queues filter each full fixed sequence to damaged substations. Outcome comparisons appear in Figures 4-6 and Supplementary Figures S12/S13; hospital-linked tract service loss is not hospital electricity delivery or clinical capacity.\n\n')
    c=c[:at]+block+c[end:]
    at=c.index('## Supplementary Figure S11.');end=c.index('## Supplementary Figure S12.',at)
    block=c[at:end].replace('and population T80.','and time to 80% modeled population-weighted service.').replace('T80 is the time to 80% modeled population-weighted service availability.',
        'Time to 80% service is a threshold-crossing time, not a service-loss integral; it is the same T80 estimand shown separately in Figure 4. The white divider identifies this distinct time outcome.')
    c=c[:at]+block+c[end:];p.write_text(c,encoding='utf-8',newline='\n');packets(c)
    a_path=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';a=json.loads(a_path.read_text())
    a['current_code_files']=[r for r in a['current_code_files'] if r['path']!=GENERATOR]+[{'path':GENERATOR,
        'sha256':hashlib.sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'tracked_in_current_git':True}]
    a_path.write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8',newline='\n')
    relationship=json.loads((TEMP/'metric_relationship.json').read_text())
    relationship.update(base_commit=BASE,figures=records,formal_scientific_result_changed=False,
        decision='Retain T80 as a distinct threshold outcome; preserve all eight policies; S12/S13 remain complete outcome supplements to Fig06.')
    (ROOT/'docs/reproducibility/DISTRIBUTION_STRATEGY_METRIC_REVIEW_20261008.json').write_text(json.dumps(relationship,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    TEMP.mkdir(exist_ok=True);records=[]
    for fn in [s01,fig04,s04,s10,s11]:
        print('Updating',fn.__name__,flush=True);records.append(fn())
    integrate(records);print('All scoped presentation corrections complete; no scientific stage invoked.',flush=True)


if __name__=='__main__':main()
