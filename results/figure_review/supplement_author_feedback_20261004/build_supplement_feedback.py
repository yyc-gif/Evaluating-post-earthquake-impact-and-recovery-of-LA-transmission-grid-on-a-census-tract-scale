"""Apply the author's supplementary-artwork feedback to the review collection.

Reads existing display tables/geometry and PDFs only. No scientific entrypoint,
sampling, scheduling, optimization, bootstrap or clustering is invoked.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import geopandas as gpd
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUNDLE = ROOT / 'results/figure_review/final_submission_candidate_20261002'
SUITE = ROOT / 'results/revised_suite/LA_Grid_Revised_Suite_20260925'
MM = 72 / 25.4
ARIAL = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
HAZARDS = ['LongBeach', 'SanFernando', 'Northridge', '2pc50']
HN = dict(zip(HAZARDS, ['Long Beach', 'San Fernando', 'Northridge', '2pc50']))
HC = dict(zip(HAZARDS, ['#366E9F', '#9364A1', '#9a7559', '#a65628']))
KEYS = ['impact-first', 'hospital-first', 'degree-first', 'vulnerability-first',
        'centrality-first', 'betweenness-first', 'closeness-first', 'random', 'unconstrained']
COLOR = dict(zip(KEYS, ['#ff7f00', '#555555', '#4daf4a', '#a65628',
                        '#e41a1c', '#b59a00', '#377eb8', '#9a9a9a', '#111111']))
LINE = dict(zip(KEYS, [':', (0,(2.2,1.4)), '--', '-', '-.',
                       (0,(5,1.5,1.2,1.5)), (0,(4,1.6)), '-', '--']))
LABEL = {k: k.capitalize() for k in KEYS}
LABEL.update({'random':'Random', 'unconstrained':'Unconstrained'})
INPUT_HASHES = {}
QA = []
PARITY = []
CAPTIONS = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def track(path):
    path = Path(path)
    INPUT_HASHES[path.relative_to(ROOT).as_posix()] = sha(path)
    return path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def style():
    plt.rcParams.update({'font.family':'Arial', 'font.sans-serif':['Arial'],
        'font.size':7.5, 'axes.titlesize':9.5, 'axes.labelsize':8.5,
        'xtick.labelsize':7.5, 'ytick.labelsize':7.5, 'legend.fontsize':7.5,
        'axes.linewidth':.6, 'grid.linewidth':.4, 'lines.linewidth':1.2,
        'patch.linewidth':.5, 'pdf.fonttype':42, 'ps.fonttype':42,
        'figure.facecolor':'white', 'axes.facecolor':'white'})


def spans(page):
    return [(line,s) for b in page.get_text('dict')['blocks'] if 'lines' in b
            for line in b['lines'] for s in line['spans'] if s['text'].strip()]


def plain(text):
    return text.replace('\u00a0',' ').replace('\u00ad','-')


def export(path):
    with fitz.open(path) as doc:
        page = doc[0]
        ss = [s for _,s in spans(page)]
        minimum = min(s['size'] for s in ss)
        assert minimum >= 6.99, (path.name, minimum)
        assert all(page.rect.contains(fitz.Rect(s['bbox'])) for s in ss), path.name
        resources = [doc.extract_font(f[0]) for f in doc.get_page_fonts(0, full=True)]
        assert all('DejaVu' not in r[0] and len(r[3]) > 0 for r in resources)
        for dpi,suffix in [(600,''), (150,'_preview')]:
            px = page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
            px.set_dpi(dpi,dpi)
            px.save(path.with_name(path.stem+suffix+'.png'))
        view = fitz.open()
        q = view.new_page(width=210*MM, height=max(297*MM,page.rect.height+30*MM))
        q.show_pdf_page(fitz.Rect(12.5*MM,15*MM,197.5*MM,15*MM+page.rect.height),doc,0)
        q.get_pixmap(matrix=fitz.Matrix(1.45,1.45),alpha=False).save(path.with_name(path.stem+'_page_preview.png'))
        view.close()
        QA.append({'file':path.name,'width_mm':page.rect.width/MM,
            'height_mm':page.rect.height/MM,'min_font_pt':minimum,
            'fonts':';'.join(sorted({s['font'] for s in ss})),
            'all_fonts_embedded':True,'off_page_text':0,'sha256':sha(path)})


def save(fig, key):
    path = OUT/(key+'.pdf')
    fig.savefig(path, dpi=600, facecolor='white')
    plt.close(fig)
    export(path)
    return path


def edit_text(source, destination, selector):
    """Replace specified text without altering any plot paths or data marks."""
    with fitz.open(source) as doc:
        p=doc[0]; edits=[]
        for line,s in spans(p):
            change=selector(s,line,p)
            if change is not None:
                edits.append((line,s,change))
                p.add_redact_annot(fitz.Rect(s['bbox']),fill=False)
        p.apply_redactions(images=0,graphics=0)
        p.insert_font(fontname='ArialEdit',fontfile=ARIAL)
        p.insert_font(fontname='ArialEditBold',fontfile=BOLD)
        for line,s,c in edits:
            txt=c.get('text',s['text'])
            if not txt: continue
            size=c.get('size',s['size']); bold=c.get('bold','Bold' in s['font'])
            font=fitz.Font(fontfile=BOLD if bold else ARIAL)
            name='ArialEditBold' if bold else 'ArialEdit'
            box=fitz.Rect(s['bbox'])
            angle=int(round(-np.degrees(np.arctan2(line['dir'][1],line['dir'][0]))))%360
            if angle==90:
                origin=((box.x0+box.x1)/2+(font.ascender+font.descender)*size/2,
                        (box.y0+box.y1)/2+font.text_length(txt,fontsize=size)/2)
            else:
                origin=(c.get('x',(box.x0+box.x1)/2-font.text_length(txt,fontsize=size)/2),
                        c.get('y',(box.y0+box.y1)/2+(font.ascender+font.descender)*size/2))
            p.insert_text(origin,txt,fontname=name,fontsize=size,rotate=angle)
        doc.save(destination,garbage=4,deflate=True)
    return destination


def s01():
    style(); parts=[]; outliers={}
    fig,ax=plt.subplots(figsize=(185/25.4,65.1/25.4))
    for h in HAZARDS:
        p=track(SUITE/'Stage 1 Output_expanded'/f'MC_Device_Damage_AvgDS_{h}.csv')
        values=pd.read_csv(p).avg_damage_state.to_numpy()
        assert len(values)==92
        lo,hi=np.quantile(values,[.25,.75]); iqr=hi-lo
        outliers[h]=int(((values<lo-1.5*iqr)|(values>hi+1.5*iqr)).sum())
        parts.append(pd.DataFrame({'hazard':h,'value':values}))
    data=pd.concat(parts,ignore_index=True)
    sns.boxplot(data=data,x='hazard',y='value',hue='hazard',order=HAZARDS,
        palette=HC,saturation=1,legend=False,width=.48,linewidth=.7,
        showfliers=False,ax=ax)
    for k,h in enumerate(HAZARDS):
        values=data.loc[data.hazard.eq(h),'value'].to_numpy()
        ax.scatter(k+.18*np.sin(np.arange(len(values))*2.399963),values,
            color='black',alpha=.22,s=1.8**2,zorder=3)
        PARITY.append({'figure':'FigS01','hazard':h,'station_values':len(values),
                       'all_points_retained':True,'value_hash':hashlib.sha256(values.tobytes()).hexdigest()})
    ax.set_xticks(range(4),[HN[h] for h in HAZARDS])
    ax.set(xlabel='Hazard scenario',ylabel='Mean damage state',ylim=(0,4.1))
    ax.grid(axis='y',alpha=.2)
    fig.subplots_adjust(left=.13,right=.985,bottom=.27,top=.95)
    save(fig,'FigS01')
    (OUT/'S01_DUPLICATE_FLIER_EXPLANATION.json').write_text(json.dumps(
        {'default_1_5_IQR_outliers':outliers,'cause':'Default boxplot fliers duplicate the all-station scatter layer.',
         'fix':'Disable only duplicate boxplot flier symbols; retain every station point.'},indent=2))
    CAPTIONS['S1']='Station-specific mean damage states under Long Beach, San Fernando, Northridge and 2pc50, each based on 1,000 evaluation realizations at 92 substations. Boxes show the median and interquartile range across station means; whiskers extend to the most extreme observations within 1.5 interquartile ranges of the box. All individual station means, including those beyond the whiskers, are shown with the same dot style; a separate flier layer is not added. These summaries describe between-station heterogeneity, not 5th–95th realization ranges or confidence intervals. Historical scenarios and 2pc50 use different fragility parameterizations, so differences do not isolate ground-motion intensity.'


def s02():
    # Reuse exact vector map panels and colorbar; remove the duplicated ECDF.
    src=track(ROOT/'results/figure_review/final_presentation_fix_20261002/FigS02.pdf')
    doc=fitz.open();q=doc.new_page(width=185*MM,height=137*MM)
    with fitz.open(src) as old:
        q.show_pdf_page(fitz.Rect(0,0,185*MM,137*MM),old,0,
                       clip=fitz.Rect(0,65*MM,185*MM,202*MM),keep_proportion=False)
    raw=OUT/'_S02_map_crop.pdf';doc.save(raw,garbage=4,deflate=True);doc.close()
    names={'B. Long Beach':'A. Long Beach','C. San Fernando':'B. San Fernando',
           'D. Northridge':'C. Northridge','E. 2pc50':'D. 2pc50'}
    path=OUT/'FigS02.pdf'
    edit_text(raw,path,lambda s,l,p:{'text':names[plain(s['text'])]} if plain(s['text']) in names else None)
    raw.unlink();export(path)
    CAPTIONS['S2']='Maps of tract mean initial modeled service availability for Long Beach (A), San Fernando (B), Northridge (C) and 2pc50 (D). Each tract mean is averaged over 1,000 realizations per hazard. All panels use the production utility-compatible tract–substation mapping and share the same geographic extent and 0–1 availability scale. The four spatial maps complement the initial-service distribution in Figure 3 without repeating that distribution. Availability is a dependency-weighted modeled service proxy, not delivered electricity or MW. Historical scenarios and 2pc50 have different fragility parameterizations; the comparison is not pure ground-motion-intensity sensitivity.'


def s03(meeting):
    style()
    for p in (ROOT/'Data/LA_Tracts_With_Population.shp',ROOT/'Data/LA_Tracts_With_Population.dbf',
              ROOT/'Data/LA_Tracts_With_Population.shx',ROOT/'Data/LA_Tracts_With_Population.prj',
              ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv'):track(p)
    tracts=meeting.tract_geometry()
    nodes=pd.read_csv(track(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv'),dtype={'id':str})
    bases=pd.read_csv(track(ROOT/'Data/stage45_active_crew_bases_C57.csv'))
    bases=bases.loc[bases.integer_crews.gt(0)].copy()
    assert len(nodes)==92 and bases.integer_crews.sum()==57
    points=meeting.map_points(nodes,tracts.crs)
    origins=gpd.GeoDataFrame(bases,geometry=gpd.points_from_xy(bases.longitude,bases.latitude),crs='EPSG:4326').to_crs(tracts.crs)
    fig,ax=plt.subplots(figsize=(185/25.4,116/25.4))
    meeting.draw_tract_base(ax,tracts)
    ax.scatter(points.geometry.x,points.geometry.y,s=3.0,c='#89939b',alpha=.65,
               edgecolors='white',linewidths=.15,zorder=3)
    colors={'LADWP':'#377eb8','SCE':'#d95f02'}
    for utility,group in origins.groupby('utility'):
        ax.scatter(group.geometry.x,group.geometry.y,s=8,c=colors[utility],
            edgecolors='white',linewidths=.2,zorder=4)
    ax.set_title('A. Origins',loc='left',fontweight='bold')
    handles=[Line2D([],[],marker='o',ls='none',color='#89939b',ms=2.2,label='Substations')]
    handles += [Line2D([],[],marker='o',ls='none',color=c,ms=3,label=u+' origin') for u,c in colors.items()]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.015),
               frameon=False,ncol=3,columnspacing=1.8,handletextpad=.5)
    fig.subplots_adjust(left=.04,right=.96,bottom=.08,top=.94)
    top=OUT/'_S03_origins.pdf';fig.savefig(top);plt.close(fig)
    source=track(ROOT/'results/figure_review/final_presentation_fix_20261002/FigS03.pdf')
    with fitz.open(source) as old:
        pp=old[0]
        title=next(s for _,s in spans(pp) if plain(s['text']).startswith('B. Directed'))
        y0=title['bbox'][1]-1.5*MM
        height=pp.rect.height-y0
        doc=fitz.open();q=doc.new_page(width=185*MM,height=116*MM+height)
        with fitz.open(top) as m:q.show_pdf_page(fitz.Rect(0,0,185*MM,116*MM),m,0)
        q.show_pdf_page(fitz.Rect(0,116*MM,185*MM,116*MM+height),old,0,
                       clip=fitz.Rect(0,y0,185*MM,pp.rect.height),keep_proportion=False)
        raw=OUT/'_S03_combined.pdf';doc.save(raw,garbage=4,deflate=True);doc.close()
    def choose(s,l,p):
        t=plain(s['text'])
        if re.search(r'(Origin|Destination) substation ID',t):
            return {'text':re.sub(r'\s*\([Nn]\s*=\s*92\)','',t)}
        if t=='Travel Time (Hours)':return {'text':'Travel time (h)'}
    path=OUT/'FigS03.pdf';edit_text(raw,path,choose)
    raw.unlink();top.unlink();export(path)
    PARITY.append({'figure':'FigS03','origins_from_allocation_table':len(origins),
        'origin_coordinates_unchanged':True,'matrix':'Exact vector crop, labels only edited'})
    CAPTIONS['S3']='(A) Crew origins from the reference allocation table, classified by LADWP and SCE, and substations on the study-area tract background. Origin positions are geographic inputs; marker size does not encode crew allocation. (B) Directed task-to-task road-travel times, with rows denoting origins and columns destinations; values are in hours. The reference allocation uses 57 crews. Crew origins and travel times are inputs to the logistics-constrained restoration model, rather than evidence of how outcomes respond to changes in crew resources.'


def s04():
    style();height=183
    fig=plt.figure(figsize=(185/25.4,height/25.4))
    def box(top,h):return fig.add_axes([24/185,(height-top-h)/height,155/185,h/height])
    a=box(12,36);b=box(82,34);c=box(139,31)
    attacks=[('impact','Network λ2 impact','#ff7f00',':'),('random','Random removal','#888888','-'),
        ('degree','Degree','#4daf4a','--'),('betweenness_centrality','Betweenness','#b59a00','-.'),
        ('closeness_centrality','Closeness','#377eb8',(0,(4,1.6)))]
    for key,label,color,line in attacks:
        name=f'percolation_curve_{key}.csv' if key in {'impact','random'} else f'exploratory_percolation_curve_{key}.csv'
        d=pd.read_csv(track(SUITE/'Stage 2 Output_expanded'/name))
        a.plot(d.nodes_removed,d.lcc_fraction,color=color,ls=line,lw=1,label=label)
    a.set(title='A. Static station-removal comparison',xlabel='Substations removed',
          ylabel='Largest connected\ncomponent fraction',ylim=(-.02,1.04))
    a.title.set_weight('bold');a.title.set_position((0,1));a.title.set_ha('left')
    a.legend(frameon=False,ncol=3,fontsize=7,loc='upper right')
    data=pd.read_csv(track(SUITE/'Stage 6 Output_expanded/NETWORK_TOPOLOGY_DISPLAY_CURVES_2pc50.csv'))
    handles=[]
    for key in KEYS:
        d=data[data.strategy_id.eq(key)].sort_values('time_hr')
        core=key in KEYS[:4] or key=='unconstrained'
        for ax,column in [(b,'mean_lcc_fraction'),(c,'mean_lcc_average_degree')]:
            ax.plot(d.time_hr,d[column],color=COLOR[key],ls=LINE[key],
                    lw=1.4 if core else 1.05,alpha=1 if core else .78)
        handles.append(Line2D([],[],color=COLOR[key],ls=LINE[key],lw=1.4 if core else 1.05,label=LABEL[key]))
    legend=fig.legend(handles=handles,frameon=False,ncol=3,loc='lower center',
            bbox_to_anchor=(.56,1-74/height),columnspacing=1.8,handletextpad=.5,fontsize=7.5)
    for text,key in zip(legend.get_texts(),KEYS):
        if key in KEYS[:4]:text.set_weight('bold')
    b.set_title('B. Largest connected component fraction',loc='left',fontweight='bold')
    b.set_ylabel('Largest connected\ncomponent fraction');b.set_ylim(-.02,1.04)
    c.set_title('C. Average degree within the largest component',loc='left',fontweight='bold')
    c.set(xlabel='Time after earthquake (h)',ylabel='Mean degree')
    for ax in [a,b,c]:ax.grid(alpha=.2)
    for ax in [b,c]:ax.set_xlim(0,120)
    save(fig,'FigS04')
    CAPTIONS['S4']='(A) Targeted and random substation-removal comparisons. The network λ2-impact attack metric describes topology impact and is distinct from the population-oriented Impact-first restoration policy; removal curves do not establish optimal repair sequences. (B/C) Mean largest-connected-component fraction and mean degree within that component during 2pc50 recovery with 57 crews and repair-duration multiplier 1.00. The fraction is component size divided by the full modeled station count. Curves cover 0–120 h for all eight scheduled policies and Unconstrained; no interval is encoded. B and C share one policy legend and the policy color/line identity used in Figure 4. Source-path service-loss outcomes are presented in the main figures rather than repeated here. Connectivity describes modeled network structure, not delivered MW or electrical adequacy.'


def s06(meeting):
    # Use the existing presentation function. Remove C and relocate old D only.
    def emit(fig,stem,**kwargs):
        a,b,old_c,c=fig.axes
        old_c.remove()
        fig.set_size_inches(185/25.4,129/25.4,forward=True)
        a.set_position([.115,.555,.345,.30]);b.set_position([.645,.555,.32,.30])
        c.set_position([.18,.12,.70,.265])
        for line in b.lines:
            if line.get_marker()=='o':line.set_color('#8d989f')
            elif line.get_marker()=='D':line.set_color('#386f8e');line.set_marker('o')
        b.set_yticks([2,1,0],['Any mapped\nsubstation','Highest-weight\nsubstation','Three highest-weight\nsubstations'],fontsize=7)
        b.set_title('')
        b.set_title('B. Match to public SCE sites',loc='left',fontweight='bold')
        for t in b.texts:t.set_color('#8d989f' if t.get_color()=='#28618a' else '#386f8e')
        for legend in list(fig.legends):legend.remove()
        fig.legend(handles=[Line2D([],[],marker='o',ls='none',color='#8d989f',ms=3.8,label='Distance-based baseline'),
            Line2D([],[],marker='o',ls='none',color='#386f8e',ms=3.8,label='Utility-compatible mapping')],
            frameon=False,loc='upper center',bbox_to_anchor=(.56,.985),ncol=2,fontsize=7.5)
        c.set_title('')
        c.set_title('C. Tract service-loss change caused by mapping (2pc50)',loc='left',fontweight='bold')
        c.set_xlabel('Absolute change in mean cumulative service loss (h)',fontsize=8.5)
        for t in c.texts:
            t.set_text('246 tracts have a change\ngreater than 1 h')
        return save(fig,'FigS06')
    for p in [ROOT/'provenance/reviewer_working/Supplement_Rebuild_20260925/Tables/S3_CUTOFF_HOSPITAL_FIRST_2PC50.csv',
              ROOT/'provenance/reviewer_working/Supplement_Rebuild_20260925/Tables/S3_SCE_337_CANDIDATE_BENCHMARK.csv',
              SUITE/'Sensitivity Output_clean/FORMAL_MAPPING_EFFECTS.csv',
              ROOT/'Formal_Experiment_20260923/Formal_Results/TRACT_MAPPING_SHIFT.parquet']:track(p)
    meeting.save_figure=emit
    meeting.plot_supp_fig06()
    CAPTIONS['S6']='(A) Hospital-first population-weighted cumulative service-loss changes under 2pc50 across mapping cutoffs, relative to the 3% production cutoff. (B) Distance-based baseline versus utility-compatible mapping agreement on the same 337 comparable SCE tracts: any positive-weight candidate agreement is 320/337 versus 329/337, highest-weight candidate agreement is 296/337 versus 302/337, and agreement among the three highest-weight candidates is 317/337 versus 324/337. Candidates are ranked by mapping weight, with agreement defined as at least one match to the public-site candidate set; this is not a general nearest-site definition. Agreement is supporting evidence, not accuracy, feeder validation or service-territory ground truth. (C) Magnitudes of changes in tract mean cumulative service loss when utility-compatible mapping replaces the distance-based baseline, under 2pc50 and Hospital-first. Absolute changes exceed 1 h for 246 of 2,315 tracts. This is mapping sensitivity, not policy benefit or statistical significance. Service-loss comparisons integrate 0–480 h.'


def s07(meeting):
    style();d=pd.read_csv(track(ROOT/'results/diagnostics/SOURCE_TERMINAL_DYNAMIC_SUMMARY_2PC50.csv'))
    d=d[d.time_hr.le(120)]
    height=191.2;fig=plt.figure(figsize=(185/25.4,height/25.4))
    a=fig.add_axes([.15,.755,.81,.19]);b=fig.add_axes([.15,.475,.81,.185])
    for key in ['impact-first','hospital-first']:
        x=d[d.strategy.eq(key)].sort_values('time_hr');marker='s' if key=='impact-first' else 'o'
        for column,line,quantity in [('population_dependency_weighted_R_conn','-','full network'),
            ('population_dependency_weighted_fixed_precomputed_best_path_connection','--','fixed path')]:
            a.plot(x.time_hr,x[column],color=COLOR[key],ls=line,lw=1.2,marker=marker,ms=2.2,
                   label=LABEL[key]+': '+quantity)
    a.set_title('A. Source connection: full network and fixed path',loc='left',fontweight='bold')
    a.set(ylabel='Probability of being functional\nand source-connected',ylim=(-.02,1.04))
    a.legend(frameon=False,loc='lower right',ncol=2,fontsize=7.2)
    for key in KEYS[:-1]:
        x=d[d.strategy.eq(key)].sort_values('time_hr')
        b.plot(x.time_hr,x.population_dependency_weighted_full_minus_fixed_precomputed_best_path,
            color=COLOR[key],ls=LINE[key],lw=1.25 if key in KEYS[:4] else 1.05,
            marker='s' if key=='impact-first' else 'o',ms=2,label=LABEL[key])
    b.set_title('B. Additional source connection from alternate routes',loc='left',fontweight='bold')
    b.set(xlabel='Time after earthquake (h)',ylabel='Increase in source-\nconnection probability',ylim=(-.005,.235))
    for ax in [a,b]:
        ax.set_xlim(0,120);ax.set_xticks([0,24,48,72,96,120]);ax.grid(alpha=.2)
        for t in [24,48]:ax.axvline(t,color='#b9b9b9',lw=.55,ls='--',zorder=0)
    handles=[Line2D([],[],color=COLOR[k],ls=LINE[k],lw=1.2,label=LABEL[k]) for k in KEYS[:-1]]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.55,.411),ncol=4,
               fontsize=7.2,frameon=False,columnspacing=1.3)
    for p in [ROOT/'Data/LA_Tracts_With_Population.shp',ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv']:track(p)
    tracts=meeting.tract_geometry()
    nodes=pd.read_csv(track(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv'),dtype={'id':str})
    edges=pd.read_csv(track(ROOT/'Data/substation_graph_CEC_edges_expanded.csv'),dtype={'u':str,'v':str})
    station=pd.read_csv(track(ROOT/'results/diagnostics/SOURCE_TERMINAL_STATION_RELIABILITY_2PC50.csv'),dtype={'station_id':str})
    points=meeting.map_points(nodes,tracts.crs).merge(station,left_on='id',right_on='station_id',validate='one_to_one')
    non=points[~points.is_core_source];core=points[points.is_core_source];lookup=points.set_index('id').geometry
    assert (len(nodes),len(edges),len(non),len(core))==(92,318,78,14)
    specs=[('R_path_full','C. Conditional source reachability','Blues',.27,'Conditional source-path reliability'),
           ('Delta_R_redundancy','D. Reliability gain from alternate routes','Reds',.24,'Additional source-path reliability')]
    for i,(col,title,cmap,start,scale) in enumerate(specs):
        ax=fig.add_axes([.015+i*.50,.074,.475,.258])
        meeting.draw_tract_base(ax,tracts)
        for e in edges.itertuples(index=False):
            u,v=lookup[e.u],lookup[e.v]
            ax.plot([u.x,v.x],[u.y,v.y],color='#aeb7bd',lw=.28,alpha=.24,zorder=2)
        palette=LinearSegmentedColormap.from_list(col,plt.get_cmap(cmap)(np.linspace(start,1,256)))
        s=ax.scatter(non.geometry.x,non.geometry.y,c=non[col],cmap=palette,
            vmin=0,vmax=float(non[col].max()),s=10,edgecolors='#59666e',linewidths=.18,zorder=3)
        ax.scatter(core.geometry.x,core.geometry.y,marker='^',s=12,
            facecolors='#26323b',edgecolors='white',linewidths=.28,zorder=4)
        ax.set_title(title,fontsize=9.5,fontweight='bold',pad=5)
        cax=fig.add_axes([.07+i*.50,.048,.37,.010])
        cb=fig.colorbar(s,cax=cax,orientation='horizontal')
        cb.set_label(scale,fontsize=7.1,labelpad=2)
        cb.ax.tick_params(labelsize=7,width=.5,length=2);cb.outline.set_linewidth(.5)
        PARITY.append({'figure':'FigS07','metric':col,'vmin':0,'vmax':float(non[col].max()),
            'normalization':'linear; unchanged 0–max limits','values_hash':hashlib.sha256(non[col].to_numpy().tobytes()).hexdigest()})
    fig.legend(handles=[Line2D([],[],marker='^',ls='none',color='#26323b',ms=3.5,label='Core source')],
        frameon=False,loc='lower center',bbox_to_anchor=(.5,-.002),fontsize=7.1)
    save(fig,'FigS07')
    CAPTIONS['S7']='(A/B) Dynamic results from 1,000 recovery realizations under 2pc50, 57 crews and repair-duration multiplier 1.00, displayed over 0–120 h. The plotted probabilities are averaged over stations using their population-dependency weights. The full-network quantity is the unconditional joint probability that a station is functional and connected to at least one active Core source, rather than a product of marginal probabilities. (A) Impact-first and Hospital-first comparisons: solid curves denote the full network and dashed curves the fixed precomputed most-reliable path. (B) Increase in joint connection probability contributed by alternate routes for all eight scheduled policies. The fixed path is selected from 2pc50 fragility before recovery, not reoptimized at each time. (C) Static conditional source reachability given that the target station is functional. (D) Static full-network reliability gain beyond the fixed most-reliable path. Static estimates combine the analytical fixed-path probability with a same-state Monte Carlo estimate of the full-connection event outside that path, using 100,000 independently sampled station states; they differ from the dynamic joint quantity. Zero estimated additional-route gain does not establish the absence of a true gain. Core sources use separate triangles and their own station operational probabilities; edges have no independent failure probability in this station-failure model. Both station color scales remain linear, from zero to the largest displayed value. These probabilities do not represent delivered MW, generation adequacy or electrical capacity.'


def s08():
    # Plot the identical provider loadings and closed increments; no closure run.
    style();track(ROOT/'results/capacity/CONNECTED_VS_ELECTRICAL_CONSTRAINT_BENCHMARK.csv')
    renderer=load('author_capacity_display',ROOT/'src/la_grid/plotting/render_source_gate_electrical_adequacy_figure.py')
    data=renderer._load_level_a()
    height=194.778;fig=plt.figure(figsize=(185/25.4,height/25.4))
    a=fig.add_axes([.185,.30,.775,.655]);b=fig.add_axes([.20,.065,.73,.165])
    y=np.arange(len(data));values=data.provider_loading_percent.to_numpy(float)
    olinda=data.facility.eq('OLINDA 66/12').to_numpy()
    a.hlines(y,0,values,color='#b9c7d5',lw=.65,zorder=1)
    voltage=sorted(data.low_side_kv.unique());markers=dict(zip(voltage,['o','s','^']))
    for v in voltage:
        mask=data.low_side_kv.eq(v).to_numpy() & ~olinda
        a.scatter(values[mask],y[mask],s=20,marker=markers[v],color='#377eb8',
                  edgecolor='white',linewidth=.4,zorder=3,label=f'{v:g} kV low-side')
    a.scatter(values[olinda],y[olinda],s=48,marker='*',color='#d95f02',
              edgecolor='white',linewidth=.5,zorder=4,label='OLINDA above planning limit')
    a.axvline(100,color='#555555',lw=1,ls='--',label='Provider-defined planning limit (100%)')
    oi=int(np.flatnonzero(olinda)[0])
    a.annotate('109.04%',(values[oi],y[oi]),xytext=(4,0),textcoords='offset points',
               ha='left',va='center',fontsize=7,fontweight='semibold',color='#b44700')
    a.set_yticks(y,data.display_station)
    a.set(xlim=(0,116),ylim=(-.8,len(data)-.1),xlabel='Provider-reported facility loading (%)',ylabel='SCE station')
    a.set_title('A. SCE facility loading relative to the planning limit',loc='left',fontweight='bold')
    a.grid(axis='x',color='#ddd',lw=.4)
    a.legend(loc='lower right',frameon=True,fontsize=7.2,borderpad=.5,handletextpad=.5)
    summary=pd.read_csv(track(ROOT/'results/capacity/SCE_CAPACITY_SENSITIVITY_SUMMARY.csv'))
    keys=['impact-first','hospital-first','vulnerability-first','degree-first']
    rows=summary[(summary.row_type=='policy')&(summary.Hazard=='2pc50')&summary.Policy.isin(keys)].set_index('Policy').loc[keys]
    assert len(rows)==4 and (rows.binding_station_count==1).all()
    for yy,key,value in zip(np.arange(4)[::-1],keys,rows.delta.to_numpy(float)):
        b.plot(value,yy,'o',ms=4.4,color=COLOR[key])
        b.annotate(f'{value:.3f} h',(value,yy),xytext=(5,0),textcoords='offset points',
                   ha='left',va='center',fontsize=7)
    b.set_yticks(np.arange(4)[::-1],[LABEL[k] for k in keys])
    b.set(xlim=(.118,.134),ylim=(-.5,3.5))
    b.set_title('B. Effect of applying planning capacity bounds (2pc50)',loc='left',fontweight='bold')
    b.set_xlabel('Increase in population-weighted cumulative service loss\n(h; expanded scale)',fontsize=8.5)
    b.grid(axis='x',alpha=.2)
    PARITY.append({'figure':'FigS08','provider_loading_values':values.tolist(),
        'capacity_increment_policies':keys,'closed_capacity_increments':rows.delta.to_numpy(float).tolist()})
    save(fig,'FigS08')
    CAPTIONS['S8']='(A) SCE 2026 Grid Needs Assessment (GNA) facility loading for 34 same-facility, voltage-level planning rows across 28 substations with simultaneous forecast demand and provider-defined limits. The legend identifies low-side voltage by marker shape; the 100% line is the provider-defined planning limit, not an earthquake failure or overload threshold. OLINDA 66/12 is the only internally consistent row above that limit, at 109.04%. (B) Increase in population-weighted cumulative modeled service loss when planning capacity bounds are applied to the source-connected service model, relative to that same model without these bounds. The comparison uses 2pc50, 57 crews, repair-duration multiplier 1.00 and a 0–480 h integration window. It is restricted to 19 one-to-one supported substations. Nine of the 28 matched substations are excluded because they have multiple facilities, leaving 73 of the 92 substations without an applicable bound. Supported dependencies cover 932 of 2,315 tracts and 25.34% of population-weighted dependency mass. Station service is bounded by the smaller of its modeled service and min(1, planning limit/forecast demand); demand and limit are in MW in this supported screen. Only OLINDA can impose a bound below one. Dots show mean capacity-bound-minus-baseline increments for four named policies; the labeled expanded axis emphasizes differences of approximately 0.120–0.126 h, not the total service loss. Planning evidence and this subset sensitivity are not post-earthquake load flow or validation of electrical adequacy across the entire network.'


def s13_label_only():
    source=track(ROOT/'results/figure_review/fig06_resource_redesign_20261002/Full_Duration_Absolute_Outcomes.pdf')
    p=OUT/'FigS13.pdf'
    edit_text(source,p,lambda s,l,q:{'text':'Repair-duration multiplier (reference crews)','size':8.5}
        if plain(s['text'])=='Repair-duration multiplier (57 crews)' else None)
    export(p)


def compile_bundle():
    p=BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md';md=p.read_text(encoding='utf-8')
    for key,body in CAPTIONS.items():
        pattern=rf'(?ms)(^## Supplementary Figure {key}\.[^\n]*\n\n).*?(?=^## |\Z)'
        md,n=re.subn(pattern,lambda m:m.group(1)+body+'\n\n',md,count=1)
        assert n==1,key
    p.write_text(md,encoding='utf-8')
    # Retain all seven main figures byte-for-byte, including their existing merge.
    main=[BUNDLE/f'Main/Fig{i:02d}.pdf' for i in range(1,8)]
    supp=[BUNDLE/f'Supplement/FigS{i:02d}.pdf' for i in range(1,14)]
    merged=fitz.open()
    for p in supp:
        with fitz.open(p) as d:merged.insert_pdf(d)
    merged.save(BUNDLE/'ALL_SUPPLEMENT_FIGURES.pdf',garbage=4,deflate=True);merged.close()
    matches=list(re.finditer(r'(?m)^## (.+)\n\n',md)); lookup={}
    for i,m in enumerate(matches):
        heading=m.group(1);body=md[m.end():matches[i+1].start() if i+1<len(matches) else len(md)].strip()
        if heading.startswith('Figure '):
            key='Main/Fig'+f"{int(heading.split('.')[0].replace('Figure ','')):02d}"+'.pdf'
        elif heading.startswith('Supplementary Figure S'):
            key='Supplement/FigS'+f"{int(heading.split('.')[0].replace('Supplementary Figure S','')):02d}"+'.pdf'
        else:continue
        lookup[key]=(heading,body)
    packet=fitz.open()
    for p in main+supp:
        key=p.relative_to(BUNDLE).as_posix();heading,body=lookup[key]
        with fitz.open(p) as d:packet.insert_pdf(d)
        q=packet.new_page(width=185*MM,height=350*MM)
        q.insert_font(fontname='ArialPacket',fontfile=ARIAL);q.insert_font(fontname='ArialPacketBold',fontfile=BOLD)
        q.insert_text((14*MM,20*MM),heading,fontname='ArialPacketBold',fontsize=9.5)
        assert q.insert_textbox(fitz.Rect(14*MM,29*MM,171*MM,333*MM),body,
            fontname='ArialPacket',fontsize=9.2,lineheight=1.22)>=0,heading
    packet.save(BUNDLE/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);packet.close()
    with fitz.open(BUNDLE/'ALL_FIGURES_WITH_CAPTIONS.pdf') as d:assert len(d)==40


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Guard the current contents, not an older HEAD; unrelated work is preserved.
    guards=json.loads((ROOT/'results/figure_review/promotion_readiness_4a4e9b5/READ_ONLY_GUARD.json').read_text())
    protected={p:sha(ROOT/p) for p in guards['scientific_hashes']}
    publication={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'results/figures').glob('*') if p.is_file()}
    preserved={str(p.relative_to(ROOT)):sha(p) for p in (list((BUNDLE/'Main').glob('*'))+
        [BUNDLE/'ALL_MAIN_FIGURES.pdf']+
        [BUNDLE/f'Supplement/FigS{k:02d}{ext}' for k in [5,9,10,11,12] for ext in ['.pdf','.png']])}
    # Existing reviewed sources are retained; only new derivatives are copied.
    meeting=load('author_supplement_meeting',ROOT/'src/la_grid/plotting/build_meeting_figure_collection.py')
    s01();s02();s03(meeting);s04();s06(meeting);s07(meeting);s08();s13_label_only()
    source_inputs=dict(INPUT_HASHES)
    assert all(sha(ROOT/p)==h for p,h in source_inputs.items())
    keys=[1,2,3,4,6,7,8,13]
    manifest=pd.read_csv(BUNDLE/'FIGURE_MANIFEST.csv',dtype=str).fillna('')
    for k in keys:
        for ext in ['.pdf','.png']:
            src=OUT/f'FigS{k:02d}{ext}';dst=BUNDLE/f'Supplement/FigS{k:02d}{ext}'
            shutil.copyfile(src,dst);assert sha(src)==sha(dst)
            idx=manifest.index[manifest.final_name.eq(dst.relative_to(BUNDLE).as_posix())]
            assert len(idx)==1
            record=next(r for r in QA if r['file']==f'FigS{k:02d}.pdf')
            manifest.loc[idx[0],['source_file','source_commit','sha256','size_mm','min_font_pt','status']]=[
                src.relative_to(ROOT).as_posix(),'ARTWORK_COMMIT_PENDING',sha(dst),
                f"{record['width_mm']:.3f} x {record['height_mm']:.3f}",
                f"{record['min_font_pt']:.3f}",'AUTHOR_REVIEW_UPDATE_NOT_PROMOTED']
    manifest.to_csv(BUNDLE/'FIGURE_MANIFEST.csv',index=False)
    compile_bundle()
    assert all(sha(ROOT/p)==h for p,h in protected.items()),'Scientific source changed'
    assert all(sha(ROOT/p)==h for p,h in publication.items()),'Publication artwork changed'
    assert all(sha(ROOT/p)==h for p,h in preserved.items()),'Unrequested review artwork changed'
    (OUT/'INPUT_AND_PRESERVATION_HASHES.json').write_text(json.dumps({'scientific_sources':protected,
        'read_inputs':source_inputs,'publication_files':publication,'unchanged_review_files':preserved},indent=2))
    pd.DataFrame(QA).to_csv(OUT/'OUTPUT_QA.csv',index=False)
    (OUT/'PLOT_PARITY.json').write_text(json.dumps(PARITY,indent=2))
    (OUT/'CAPTIONS.md').write_text('\n\n'.join('## '+k+'\n\n'+v for k,v in CAPTIONS.items())+'\n',encoding='utf-8')
    text=(BUNDLE/'README.md').read_text(encoding='utf-8')
    note='\nSupplement S01–S04/S06–S08 were updated for the author feedback of 2026-10-04. S13 has only a reference-crew axis-label correction. S05/S09 and all Main artwork are unchanged in this round. Use the paired files here and the combined caption packet; historical generation sources remain in their review folders.\n'
    if note.strip() not in text:(BUNDLE/'README.md').write_text(text.rstrip()+'\n'+note,encoding='utf-8')
    print(json.dumps({'updated_supplements':keys,'science_hash_changes':0,
        'publication_hash_changes':0,'S05_S09_changes':0,'main_artwork_changes':0,'qa':QA},indent=2))


if __name__=='__main__':main()
