"""Author-requested hospital/resource presentation from saved outcome files.

No sampling, scheduling, simulation, optimization or bootstrap is performed.
Historical source figures and results/figures are never edited.
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
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUNDLE = ROOT/'results/figure_review/final_submission_candidate_20261002'
FORMAL = ROOT/'Formal_Experiment_20260923'
EQUITY = FORMAL/'Equity_Amendment'
MM = 72/25.4
METRICS = ['burden_Q4_hr', 'population_weighted_normalized_burden_hr',
           'absolute_Q4_minus_Q1_hr', 'hospital_mean_normalized_burden_hr']
CREW = ['C29_D1', 'C57_D1', 'C86_D1', 'C114_D1']
DURATION = ['C57_D075', 'C57_D1', 'C57_D125', 'C57_D150']
KEYS = ['impact-first', 'hospital-first', 'degree-first', 'vulnerability-first',
        'centrality-first', 'betweenness-first', 'closeness-first', 'random']
REFS = ['hospital-first', 'impact-first', 'degree-first']
REF_STYLE = {'hospital-first': ('#555555','o'), 'impact-first': ('#ff7f00','s'),
             'degree-first': ('#4daf4a','^')}
COLOR = dict(zip(KEYS, ['#ff7f00','#555555','#4daf4a','#a65628',
                        '#e41a1c','#b59a00','#377eb8','#9a9a9a']))
MARKER = dict(zip(KEYS, ['s','o','^','D','v','P','X','o']))
LABEL = {k:k.capitalize() for k in KEYS}
LABEL['random']='Random'
INPUTS = {}
CAPTIONS = {}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


helper=load_module('supplement_feedback_export',ROOT/
    'results/figure_review/supplement_author_feedback_20261004/build_supplement_feedback.py')
helper.OUT=OUT


def track(p):
    p=Path(p);INPUTS[p.relative_to(ROOT).as_posix()]=sha(p)
    return p


def read_outcomes():
    fields=['hazard','mapping','gate','resource_scenario','strategy_id','realization_id',*METRICS]
    paths=[FORMAL/'Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',
           EQUITY/'VULNERABILITY_PRIMARY_SUMMARY.parquet']
    d=pd.concat([pd.read_parquet(track(p),columns=fields) for p in paths],ignore_index=True)
    d=d[d.hazard.eq('2pc50') & d.mapping.eq('M1_UTILITY_003') &
        d.gate.eq('G1_BASELINE_050') & d.resource_scenario.isin(set(CREW+DURATION)) &
        d.strategy_id.isin(KEYS)].copy()
    assert not d.duplicated(['resource_scenario','strategy_id','realization_id']).any()
    counts=d.groupby(['resource_scenario','strategy_id']).realization_id.nunique()
    assert len(counts)==56 and counts.eq(1000).all()
    return d


def display_effects(d):
    old=ROOT/'results/figure_review/fig06_resource_redesign_20261002/FIG06_DISPLAYED_EFFECT_ROWS.csv'
    effects=pd.read_csv(track(old))
    assert len(effects)==63
    baseline=pd.read_csv(track(EQUITY/'VULNERABILITY_PAIRWISE_EFFECTS.csv'))
    resource=pd.read_csv(track(EQUITY/'VULNERABILITY_RESOURCE_EFFECTS.csv'))
    rows=pd.concat([baseline,resource],ignore_index=True,sort=False)
    rows=rows[rows.hazard.eq('2pc50') & rows.metric.eq(METRICS[3]) &
        rows.resource_scenario.isin(set(CREW+DURATION)) &
        rows.reference_strategy.isin(REFS[:2])].copy()
    assert len(rows)==14
    rows['effect_source']='VULNERABILITY_PAIRWISE_EFFECTS.csv / VULNERABILITY_RESOURCE_EFFECTS.csv; existing hospital contrasts'
    rows['interval_available']=True
    effects['interval_available']=True
    # Degree hospital means are deterministic display differences of saved
    # outcomes. No confidence interval is invented or newly bootstrapped.
    more=[]
    for case in sorted(set(CREW+DURATION)):
        q=d[d.resource_scenario.eq(case)]
        a=q[q.strategy_id.eq('vulnerability-first')].set_index('realization_id')[METRICS[3]].sort_index()
        b=q[q.strategy_id.eq('degree-first')].set_index('realization_id')[METRICS[3]].sort_index()
        assert a.index.equals(b.index) and len(a)==1000
        more.append({'hazard':'2pc50','resource_scenario':case,'strategy_id':'vulnerability-first',
            'reference_strategy':'degree-first','metric':METRICS[3],'n_realizations':1000,
            'paired_mean_difference':float((a-b).mean()), 'bootstrap_ci_low':np.nan,
            'bootstrap_ci_high':np.nan,'interval_available':False,
            'effect_source':'Saved realization summaries; displayed matched mean only, no new interval'})
    fields=['hazard','resource_scenario','strategy_id','reference_strategy','metric',
            'n_realizations','paired_mean_difference','bootstrap_ci_low','bootstrap_ci_high',
            'interval_available','effect_source']
    result=pd.concat([effects[fields],rows[fields],pd.DataFrame(more)[fields]],ignore_index=True)
    assert len(result)==84 and not result.duplicated(['resource_scenario','reference_strategy','metric']).any()
    old_check=result[result.metric.ne(METRICS[3])].reset_index(drop=True)
    for col in ['paired_mean_difference','bootstrap_ci_low','bootstrap_ci_high']:
        assert np.array_equal(old_check[col].to_numpy(),effects[col].to_numpy())
    result.to_csv(OUT/'FIG06_DISPLAYED_ROWS.csv',index=False)
    return result


def panel_style(ax):
    ax.axhline(0,color='#404040',lw=.7,ls='--',zorder=1)
    ax.grid(axis='y',color='#e5e5e5',lw=.4)
    ax.set_axisbelow(True)
    ax.spines[['top','right']].set_visible(False)
    ax.tick_params(width=.6,length=2.5)


def main_resource(effects):
    fig=plt.figure(figsize=(185/25.4,224/25.4))
    gs=fig.add_gridspec(4,2,left=.135,right=.985,bottom=.075,top=.85,hspace=.83,wspace=.30)
    fig.text(.5,.983,'Resource dependence of restoration-policy contrasts under 2pc50',
             ha='center',va='top',fontsize=9.5,fontweight='bold')
    fig.text(.5,.955,'Vulnerability-first compared with each named reference',ha='center',fontsize=8)
    handles=[Line2D([],[],marker=m,color=c,lw=0,ms=4.5,
        markerfacecolor='white' if k=='degree-first' else c,label=LABEL[k])
        for k,(c,m) in REF_STYLE.items()]
    fig.legend(handles=handles,ncol=3,loc='upper center',bbox_to_anchor=(.54,.940),
        frameon=False,columnspacing=1.5,handletextpad=.45)
    fig.text(.34,.879,'Crew availability',ha='center',fontsize=8.5,fontweight='bold')
    fig.text(.79,.879,'Repair duration',ha='center',fontsize=8.5,fontweight='bold')
    titles=['Highest-vulnerability quartile','All tracts, population-weighted',
            'Absolute Q4–Q1 separation','Hospital-linked tract mean']
    for i,metric in enumerate(METRICS):
        block=effects[effects.metric.eq(metric)]
        lo=min(0,block.bootstrap_ci_low.min(),block.paired_mean_difference.min())
        hi=max(0,block.bootstrap_ci_high.max(),block.paired_mean_difference.max())
        padding=max((hi-lo)*.12,.04)
        for j,cases in enumerate([CREW,DURATION]):
            ax=fig.add_subplot(gs[i,j]);panel_style(ax)
            ax.set_title(f'{chr(65+i*2+j)}. {titles[i]}',loc='left',fontsize=8.5,fontweight='bold',pad=5)
            ax.set_ylim(lo-padding,hi+padding)
            for k,ref in enumerate(REFS):
                color,mark=REF_STYLE[ref]
                for x,case in enumerate(cases):
                    r=block[block.resource_scenario.eq(case)&block.reference_strategy.eq(ref)].iloc[0]
                    y=r.paired_mean_difference
                    yerr=[[y-r.bootstrap_ci_low],[r.bootstrap_ci_high-y]] if r.interval_available else None
                    ax.errorbar(x+(k-1)*.16,y,yerr=yerr,fmt=mark,color=color,ms=4.4,
                        markerfacecolor='white' if ref=='degree-first' else color,
                        markeredgewidth=.8,elinewidth=.75,capsize=1.7,zorder=4)
            ticks=['0.51','1.00','1.51','2.00'] if j==0 else ['0.75','1.00','1.25','1.50']
            ax.set_xticks(range(4),ticks);ax.set_xlim(-.45,3.45)
            ax.set_xlabel('Crew-availability multiplier' if j==0 else 'Repair-duration multiplier',fontsize=7.5,labelpad=3)
            if j==0:ax.set_ylabel('Change in cumulative\nservice loss (h)' if i!=2 else 'Change in absolute\ngroup separation (h)',fontsize=7.5)
    fig.text(.5,.028,'Hospital-linked tract panels: Degree-first triangles show means only.',
        ha='center',fontsize=7)
    helper.save(fig,'Fig06')
    CAPTIONS['Figure 6. Resource dependence of restoration-policy contrasts under 2pc50']=(
        'Within each tested condition, points compare Vulnerability-first with Hospital-first (gray circles), '
        'Impact-first (orange squares), and Degree-first (open green triangles), using 1,000 matched physical realizations. '
        'The left column varies crew availability while repair duration is held at multiplier 1.00; '
        'the right column varies repair duration while crew availability is held at the reference level. '
        'Crew multipliers are 29/57, 1, 86/57 and 2, displayed as 0.51, 1.00, 1.51 and 2.00; '
        'duration multipliers are 0.75, 1.00, 1.25 and 1.50. '
        'Panels A/B show cumulative service loss in Q4, the highest social-vulnerability quartile; '
        'C/D show population-weighted cumulative service loss across all study tracts; '
        'E/F show the per-realization absolute Q4–Q1 separation, summarized over realizations; '
        'G/H show the equal-weight mean cumulative service loss in hospital-linked tracts. '
        'All loss integrals cover 0–480 h. Values are Vulnerability-first relative to the named reference: '
        'negative loss changes indicate lower modeled loss, while positive absolute-separation changes indicate '
        'greater between-group separation, not a change in Gini. '
        'Whiskers reproduce the 95% percentile-bootstrap confidence intervals for the mean matched difference '
        'from 10,000 resamples; they are not 5th–95th realization ranges. '
        'For Degree-first in G/H, only matched means are shown because no corresponding saved bootstrap '
        'interval is available; no interval is inferred from the other references. '
        'Both columns use the same hour scale within each outcome. Crew and duration are separate '
        'one-factor scenario families, without untested-level interpolation or crew-by-duration interaction estimates. '
        'Hospital-linked tract loss does not measure hospital electricity delivery or clinical capacity.')


def hospital_map():
    meeting=load_module('hospital_map_inputs',ROOT/'src/la_grid/plotting/build_meeting_figure_collection.py')
    mapping=pd.read_csv(track(ROOT/'Data/JULY_UTILITY_CONSTRAINED_92.csv'),dtype={'tract_id':str,'substation_id':str})
    hosp=pd.read_csv(track(ROOT/'Data/hospital_with_tract_expanded.csv'),dtype={'GEOID':str})
    rules=json.loads(track(FORMAL/'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())
    top=list(map(str,rules['2pc50']['hospital-first'][:5]))
    nodes=pd.read_csv(track(ROOT/'Data/substation_graph_CEC_nodes_expanded.csv'),dtype={'id':str})
    names=pd.read_csv(track(ROOT/'Data/Substations_PGA_IDW_CEC_expanded.csv'),dtype={'id':str})[['id','NAME']]
    assert names.id.is_unique
    hosp_ids=set(hosp.GEOID.str.replace(r'\.0$','',regex=True).str.zfill(11))
    mapping['tract_norm']=mapping.tract_id.str.replace(r'\.0$','',regex=True).str.zfill(11)
    eligible=set(mapping.loc[mapping.tract_norm.isin(hosp_ids),'substation_id'])
    for p in (ROOT/'Data').glob('LA_Tracts_With_Population.*'):track(p)
    tracts=meeting.tract_geometry();points=meeting.map_points(nodes,tracts.crs).merge(names,on='id',how='left')
    assert set(top).issubset(eligible)
    fig,ax=plt.subplots(figsize=(185/25.4,126/25.4))
    fig.subplots_adjust(left=.02,right=.98,bottom=.14,top=.93)
    meeting.draw_tract_base(ax,tracts,np.where(tracts.tract_id_norm.isin(hosp_ids),'#dfd2ef','#f8f8f8'))
    points.plot(ax=ax,color='#55758b',markersize=8,edgecolor='white',linewidth=.25,zorder=3)
    points[points.id.isin(eligible)].plot(ax=ax,color='#a65628',markersize=11,edgecolor='white',linewidth=.3,zorder=4)
    points[points.id.isin(top)].plot(ax=ax,color='#007c83',markersize=21,edgecolor='white',linewidth=.5,zorder=5)
    offsets={'301194':(-74,28),'310527':(-88,-2),'309042':(-75,-34),'300648':(27,21),'301541':(27,-17)}
    for key in top:
        p=points[points.id.eq(key)].iloc[0]
        ax.annotate(p.NAME,(p.geometry.x,p.geometry.y),xytext=offsets[key],textcoords='offset points',
            fontsize=7.5,color='#005d63',fontweight='bold',zorder=6,
            arrowprops={'arrowstyle':'-','color':'#637b7d','lw':.5},
            bbox={'facecolor':'white','edgecolor':'none','alpha':.88,'pad':.8})
    ax.set_title('Hospital-first repair priority',fontsize=9.5,fontweight='bold',pad=5)
    handles=[Patch(facecolor='#dfd2ef',label='Hospital-linked tracts'),
        Line2D([],[],marker='o',color='none',mfc='#55758b',mec='white',ms=4,label='Substations'),
        Line2D([],[],marker='o',color='none',mfc='#a65628',mec='white',ms=4,label='Hospital-priority substations'),
        Line2D([],[],marker='o',color='none',mfc='#007c83',mec='white',ms=5,label='First five priority substations')]
    fig.legend(handles=handles,ncol=2,loc='lower center',bbox_to_anchor=(.52,.024),
        frameon=False,columnspacing=1.8,handletextpad=.5)
    helper.save(fig,'FigS10')
    top_rows=points.set_index('id').loc[top,['NAME','lon','lat']].reset_index()
    top_rows.insert(0,'sequence_position',range(1,6));top_rows.to_csv(OUT/'HOSPITAL_PRIORITY_STATION_LABELS.csv',index=False)
    CAPTIONS['Supplementary Figure S10. Hospital-first priority construction']=(
        'Hospital-linked tracts and the substations receiving hospital priority in the production utility-compatible mapping. '
        'Hospital-first orders substation repair using hospital-linked tract counts, with mapped population as the tie-break; '
        'it does not repair tracts directly. The first five substations in the policy sequence are highlighted in teal '
        'and identified by station name: STATION G (ATWATER), MESA, ROSEMEAD, RIVER, and STATION A (ST. JOHN). '
        'These are substation identifiers, not hospital identifiers. The resulting hospital-linked tract '
        'cumulative service loss is compared across policies in Figure 4 and across resource conditions in Figure 6 '
        'and Supplementary Figures S12/S13. Those outcomes do not measure hospital electricity delivery or clinical capacity.')


def absolute_resources(d,kind):
    crew=kind=='crew';cases=CREW if crew else DURATION;stem='FigS12' if crew else 'FigS13'
    metrics=[METRICS[1],METRICS[0],METRICS[2],METRICS[3]]
    titles=['All tracts, population-weighted','Highest-vulnerability quartile',
            'Absolute Q4–Q1 separation','Hospital-linked tract mean']
    fig=plt.figure(figsize=(185/25.4,180/25.4))
    gs=fig.add_gridspec(2,2,left=.12,right=.985,top=.83,bottom=.12,hspace=.56,wspace=.30)
    fig.text(.5,.981,'Community outcomes across crew availability' if crew else
        'Community outcomes across repair durations',ha='center',va='top',fontsize=9.5,fontweight='bold')
    fig.text(.5,.949,'2pc50; all eight scheduled policies',ha='center',fontsize=8)
    handles=[Line2D([],[],marker=MARKER[k],color=COLOR[k],ms=4,lw=0,label=LABEL[k]) for k in KEYS]
    leg=fig.legend(handles=handles,ncol=4,loc='upper center',bbox_to_anchor=(.55,.927),
        frameon=False,columnspacing=1.1,handletextpad=.4)
    for text,key in zip(leg.texts,KEYS):
        if key in KEYS[:4]:text.set_fontweight('bold')
    display=[]
    offsets=np.linspace(-.29,.29,8)
    for i,metric in enumerate(metrics):
        ax=fig.add_subplot(gs[i//2,i%2]);ax.spines[['top','right']].set_visible(False)
        ax.set_title(f'{chr(65+i)}. {titles[i]}',loc='left',fontsize=8.5,fontweight='bold',pad=5)
        for k,key in enumerate(KEYS):
            for x,case in enumerate(cases):
                values=d[d.resource_scenario.eq(case)&d.strategy_id.eq(key)][metric].to_numpy(float)
                assert len(values)==1000 and np.isfinite(values).all()
                mean=float(np.mean(values));low,high=np.percentile(values,[5,95])
                ax.errorbar(x+offsets[k],mean,yerr=[[mean-low],[high-mean]],fmt=MARKER[key],
                    color=COLOR[key],ms=3.0 if k<4 else 2.8,elinewidth=.65,capsize=1.3,
                    markeredgewidth=.4,alpha=1 if k<4 else .78,zorder=4 if k<4 else 3)
                display.append({'figure':stem,'panel':chr(65+i),'resource_scenario':case,
                    'strategy_id':key,'metric':metric,'n_realizations':1000,
                    'mean':mean,'realization_p5':float(low),'realization_p95':float(high)})
        ax.set_xticks(range(4),['0.51','1.00','1.51','2.00'] if crew else ['0.75','1.00','1.25','1.50'])
        ax.set_xlim(-.55,3.45);ax.grid(axis='y',color='#e5e5e5',lw=.4);ax.set_axisbelow(True)
        ax.set_xlabel('Crew-availability multiplier' if crew else 'Repair-duration multiplier',fontsize=8)
        ax.set_ylabel('Cumulative service loss (h)' if i!=2 else 'Absolute group separation (h)',fontsize=8)
    fig.text(.5,.039,'Dots: means; whiskers: 5th–95th realization ranges',ha='center',fontsize=7.5)
    helper.save(fig,stem)
    pd.DataFrame(display).to_csv(OUT/(stem+'_DISPLAYED_ROWS.csv'),index=False)
    head='Supplementary Figure '+stem.replace('Fig','')+'. '+('Outcomes across crew availability' if crew else 'Outcomes across repair durations')
    CAPTIONS[head]=(
        'Results under 2pc50 for all eight scheduled policies. '+
        ('Crew-availability multipliers are 29/57, 1, 86/57 and 2, displayed as 0.51, 1.00, 1.51 and 2.00; '
         'repair duration is held at multiplier 1.00. ' if crew else
         'Repair-duration multipliers are 0.75, 1.00, 1.25 and 1.50; crew availability is held at the reference level of 57 crews. ')+
        'Panels A–D show population-weighted cumulative service loss across all tracts, highest-vulnerability-quartile '
        'cumulative service loss, per-realization absolute Q4–Q1 separation, and equal-weight mean cumulative '
        'service loss in hospital-linked tracts. All loss integrals cover 0–480 h. Q1 and Q4 denote the lowest '
        'and highest social-vulnerability quartiles. Dots are means and whiskers are 5th–95th realization ranges '
        'across 1,000 realizations per policy and condition, not confidence intervals. '
        'These absolute-outcome ranges complement the matched policy contrasts in Figure 6, '
        'and include the four other scheduled policies not used as its references. '
        'Conditions are discrete tests, without interpolation or crew-by-duration interaction estimates. '
        'Unconstrained is not a scheduled resource case, and Direct-community is represented once by Impact-first. '
        'Hospital-linked tract loss does not measure hospital electricity delivery or clinical capacity.')


def assemble_package():
    md=(BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    for heading,body in CAPTIONS.items():
        prefix=heading.split('.')[0]
        pat=r'(?ms)^## '+re.escape(prefix)+r'\..*?(?=^## |\Z)'
        md,n=re.subn(pat,'## '+heading+'\n\n'+body+'\n\n',md)
        assert n==1,heading
    (BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').write_text(md.rstrip()+'\n',encoding='utf-8')
    m=pd.read_csv(BUNDLE/'FIGURE_MANIFEST.csv',dtype=str).fillna('')
    for stem in ['Fig06','FigS10','FigS12','FigS13']:
        for ext in ['.pdf','.png']:
            source=OUT/(stem+ext);dest=BUNDLE/('Main' if stem=='Fig06' else 'Supplement')/(stem+ext)
            shutil.copyfile(source,dest);assert sha(source)==sha(dest)
            q=next(q for q in helper.QA if q['file']==stem+'.pdf')
            i=m.index[m.final_name.eq(dest.relative_to(BUNDLE).as_posix())];assert len(i)==1
            m.loc[i[0],['source_file','source_commit','sha256','size_mm','min_font_pt','status']]=[
                source.relative_to(ROOT).as_posix(),'ARTWORK_COMMIT_PENDING',sha(dest),
                f"{q['width_mm']:.3f} x {q['height_mm']:.3f}",str(q['min_font_pt']),
                'AUTHOR_REVIEW_UPDATE_NOT_PROMOTED']
    m.to_csv(BUNDLE/'FIGURE_MANIFEST.csv',index=False)
    main=[BUNDLE/f'Main/Fig{i:02d}.pdf' for i in range(1,8)]
    supp=[BUNDLE/f'Supplement/FigS{i:02d}.pdf' for i in range(1,14)]
    for name,paths in [('ALL_MAIN_FIGURES.pdf',main),('ALL_SUPPLEMENT_FIGURES.pdf',supp)]:
        book=fitz.open()
        for p in paths:
            with fitz.open(p) as src:book.insert_pdf(src)
        book.save(BUNDLE/name,garbage=4,deflate=True);book.close()
    matches=list(re.finditer(r'(?m)^## (.+)\n\n',md));caps={}
    for i,match in enumerate(matches):
        heading=match.group(1);body=md[match.end():matches[i+1].start() if i+1<len(matches) else len(md)].strip()
        if heading.startswith('Figure '):key='Main/Fig'+f"{int(heading.split('.')[0].replace('Figure ','')):02d}"+'.pdf'
        elif heading.startswith('Supplementary Figure S'):key='Supplement/FigS'+f"{int(heading.split('.')[0].replace('Supplementary Figure S','')):02d}"+'.pdf'
        else:continue
        caps[key]=(heading,body)
    packet=fitz.open()
    for p in main+supp:
        with fitz.open(p) as src:packet.insert_pdf(src)
        heading,body=caps[p.relative_to(BUNDLE).as_posix()]
        q=packet.new_page(width=185*MM,height=350*MM)
        q.insert_font(fontname='Arial',fontfile=helper.ARIAL)
        q.insert_font(fontname='ArialBold',fontfile=helper.BOLD)
        q.insert_text((14*MM,20*MM),heading,fontname='ArialBold',fontsize=9.5)
        assert q.insert_textbox(fitz.Rect(14*MM,29*MM,171*MM,333*MM),body,fontname='Arial',
                               fontsize=9.2,lineheight=1.22)>=0,heading
    assert len(packet)==40
    packet.save(BUNDLE/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);packet.close()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    guard_path=OUT/'BEFORE_HASH_GUARD.json'
    if not guard_path.exists():
        template=json.loads((ROOT/'results/figure_review/promotion_readiness_4a4e9b5/READ_ONLY_GUARD.json').read_text())
        science={p:sha(ROOT/p) for p in template['scientific_hashes']}
        publication={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'results/figures').glob('*') if p.is_file()}
        preserved={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Main','Supplement']
            for p in (BUNDLE/folder).glob('*') if p.is_file() and p.stem not in ['Fig06','FigS10','FigS12','FigS13']}
        guard_path.write_text(json.dumps({'science':science,'publication':publication,'other_review_artwork':preserved},indent=2))
    guard=json.loads(guard_path.read_text())
    helper.style()
    d=read_outcomes();effects=display_effects(d)
    main_resource(effects);hospital_map();absolute_resources(d,'crew');absolute_resources(d,'duration')
    assemble_package()
    for category,paths in guard.items():assert all(sha(ROOT/p)==h for p,h in paths.items()),category
    assert all(sha(ROOT/p)==h for p,h in INPUTS.items())
    pd.DataFrame(helper.QA).to_csv(OUT/'OUTPUT_QA.csv',index=False)
    (OUT/'READ_INPUT_HASHES.json').write_text(json.dumps(INPUTS,indent=2))
    (OUT/'CAPTIONS.md').write_text('\n\n'.join('## '+h+'\n\n'+b for h,b in CAPTIONS.items())+'\n',encoding='utf-8')
    print(json.dumps({'updated':['Fig06','FigS10','FigS12','FigS13'],'scientific_hash_changes':0,
        'publication_hash_changes':0,'other_review_artwork_hash_changes':0,'qa':helper.QA},indent=2))


if __name__=='__main__':main()
