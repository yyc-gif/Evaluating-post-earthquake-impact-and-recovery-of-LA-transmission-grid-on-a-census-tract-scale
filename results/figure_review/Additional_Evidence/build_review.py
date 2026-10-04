"""Uncurated review of SAVED metrics, matched effects and grouping sensitivity.

Presentation only: read accepted tables; never import scientific execution code.
No bootstrap/resampling, trajectories, scheduling, optimization or model changes.
PDFs are review books, NOT selected manuscript figures. The offline explorer
retains all realizations and selectable metric/reference/condition combinations.
"""
from pathlib import Path
import ast, base64, gzip, hashlib, io, itertools, json, os, subprocess, textwrap, sys
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.backends.backend_pdf import PdfPages
import fitz
from plotly.offline import get_plotlyjs

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
F=ROOT/'Formal_Experiment_20260923/Formal_Results'
E=ROOT/'Formal_Experiment_20260923/Equity_Amendment'
V=ROOT/'results/vulnerability'

def literal_constants(path, names):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    return {n.targets[0].id:ast.literal_eval(n.value) for n in tree.body
            if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)
            and n.targets[0].id in names}

C=literal_constants(ROOT/'provenance/figure_review_history/candidate_v2/build_candidate_v2.py',
                    ['STRATEGY_ORDER','LABEL','STYLE','HAZARDS','HAZARD_LABEL'])
POLICIES=C['STRATEGY_ORDER']; LABEL=C['LABEL']; STYLE=C['STYLE']
HAZARDS=C['HAZARDS']; HL=C['HAZARD_LABEL']
METRICS={
 'population_weighted_normalized_burden_hr':'Population-weighted cumulative service loss (h)',
 'population_resolved_mass_weighted_burden_hr':'Population/dependency-mass-weighted cumulative service loss (h)',
 'hospital_mean_normalized_burden_hr':'Hospital-linked tract mean cumulative service loss (h)',
 **{f'burden_Q{q}_hr':f'Q{q} population-weighted cumulative service loss (h)' for q in range(1,5)},
 'signed_Q4_minus_Q1_hr':'Signed Q4 minus Q1 cumulative-loss difference (h)',
 'absolute_Q4_minus_Q1_hr':'Absolute Q4 minus Q1 cumulative-loss difference (h)',
 'burden_gini':'Tract-burden inequality (population-weighted Gini)',
 **{f'population_T{t}_hr':f'Population-weighted time to {t}% service (h)' for t in [50,80,90]},
 'L_self_population_mass_weighted_hr':'Local-damage cumulative service loss (h)',
 'L_threshold_population_mass_weighted_hr':'Threshold-related cumulative service loss (h)',
 'L_source_population_mass_weighted_hr':'Source-path-related cumulative service loss (h)',
 'L_total_population_mass_weighted_hr':'Total dependency-mass-weighted cumulative service loss (h)',
 'L_self_fraction':'Local-damage share of cumulative loss (fraction)',
 'L_threshold_fraction':'Threshold-loss share of cumulative loss (fraction)',
 'L_source_fraction':'Source-path-loss share of cumulative loss (fraction)',
 'task_count':'Damaged repair tasks (count)',
 'makespan_hr':'Last crew task completion time (h)',
 'total_travel_hr':'Total crew travel time (h)'}
MARKERS=dict(zip(POLICIES,['o','s','^','D','v','P','X','*','h']))
CASES=[(h,'C57_D1') for h in HAZARDS]+[('2pc50',r) for r in
 ['C29_D1','C86_D1','C114_D1','C57_D075','C57_D125','C57_D150']]
SHORT={'C57_D1':'57 crews / duration 1x','C29_D1':'29 crews / duration 1x',
 'C86_D1':'86 crews / duration 1x','C114_D1':'114 crews / duration 1x',
 'C57_D075':'57 crews / duration 0.75x','C57_D125':'57 crews / duration 1.25x',
 'C57_D150':'57 crews / duration 1.50x'}
CASE_LABEL=[HL[h]+' | '+SHORT[r] for h,r in CASES]
MEASURE_LABEL={'FROZEN_SOVI_Q':'Adopted vulnerability quartiles',
 'NRI_SOVI_SCORE':'NRI social-vulnerability score',
 'CDC_RPL_THEMES':'CDC overall vulnerability percentile',
 'STAGE7_THEME_MEAN':'Mean CDC theme percentile'}
GROUP_LABEL={'frozen':'Adopted quartiles','study_equal_count':'Study-area equal-count quartiles',
 'fixed_external_percentile_bands_0_25_50_75':'Fixed external percentile bands'}
plt.rcParams.update({'font.family':'Arial','font.sans-serif':['Arial'],
 'font.size':7.5,'axes.titlesize':9.5,'axes.labelsize':8.5,
 'xtick.labelsize':7.2,'ytick.labelsize':7.2,'legend.fontsize':7.2,
 'axes.linewidth':.6,'lines.linewidth':1.2,'patch.linewidth':.5,
 'grid.linewidth':.4,'figure.facecolor':'white','axes.facecolor':'white',
 'pdf.fonttype':42,'ps.fonttype':42})
SOURCES={}; PAGE_ROWS=[]; COVER=[]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def read(p):
    SOURCES[rel(p)]=sha(p)
    return pd.read_parquet(p) if p.suffix=='.parquet' else pd.read_csv(p)
def wrap(s,n=33): return '\n'.join(textwrap.wrap(s,n,break_long_words=False))
def case_slice(d,case):return d[d.hazard.eq(case[0])&d.resource_scenario.eq(case[1])]
def figure(title,legend=False):
    fig,axs=plt.subplots(2,2,figsize=(185/25.4,214/25.4))
    fig.subplots_adjust(left=.14,right=.955,top=.88,bottom=.16 if legend else .12,
                        hspace=.7,wspace=.56)
    fig.suptitle(wrap(title,77),y=.974,fontsize=10,weight='bold')
    for ax in axs.flat:ax.grid(alpha=.16);ax.set_axisbelow(True)
    if legend:
        hs=[Line2D([],[],color=STYLE[p][0],marker=MARKERS[p],ls=STYLE[p][1],
                   label=LABEL[p],ms=4) for p in POLICIES]
        fig.legend(handles=hs,ncol=3,loc='lower center',bbox_to_anchor=(.52,.045),
                   frameon=False,columnspacing=.8,handlelength=1.6)
    return fig,list(axs.flat)
def finish(pdf,fig,book,panels,note=''):
    page=pdf.get_pagecount()+1
    fig.text(.07,.018,wrap(note,117),fontsize=7,va='bottom')
    pdf.savefig(fig)
    for letter,desc in zip('ABCD',panels):
        PAGE_ROWS.append({'book':book,'page':page,'panel':letter,**desc})
    plt.close(fig)
def title(ax,letter,s):ax.set_title(letter+'. '+wrap(s,33),loc='left',weight='bold',pad=5)
def numeric_clean(obj):
    if isinstance(obj,dict):return {k:numeric_clean(v) for k,v in obj.items()}
    if isinstance(obj,(list,tuple)):return [numeric_clean(v) for v in obj]
    if isinstance(obj,np.ndarray):return numeric_clean(obj.tolist())
    if isinstance(obj,(np.floating,float)):return float(obj) if np.isfinite(obj) else None
    if isinstance(obj,np.integer):return int(obj)
    return obj
def cover(direction,source,expected,shown,location,notes=''):
    COVER.append(dict(information_direction=direction,source=source,
        expected_count=expected,shown_count=shown,visual_location=location,
        status='AVAILABLE_AND_DISPLAYED' if shown==expected else 'EVIDENCE_GAP',notes=notes))

def protect_snapshot():
    # Metadata guard for ALL existing scientific artifacts, not just read tables.
    roots=['Data','Formal_Experiment_20260923','results/capacity','results/vulnerability',
           'results/diagnostics','results/stage7','results/formal','results/figures']
    snapshot={}
    for root in roots:
        for folder,dirs,files in os.walk(ROOT/root):
            dirs[:]=[x for x in dirs if x not in ['__pycache__','.pytest_cache']]
            for name in files:
                p=Path(folder)/name;s=p.stat();snapshot[rel(p)]=(s.st_size,s.st_mtime_ns)
    return snapshot

def load():
    raw=pd.concat([read(F/'PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet'),
                   read(E/'VULNERABILITY_PRIMARY_SUMMARY.parquet')],ignore_index=True)
    d=raw[raw.mapping.eq('M1_UTILITY_003')&raw.gate.eq('G1_BASELINE_050')&raw.strategy_id.isin(POLICIES)].copy()
    assert not d.duplicated(['hazard','resource_scenario','strategy_id','realization_id']).any()
    assert len(d)==84000,len(d)
    for case in CASES:
        g=case_slice(d,case)
        assert set(g.strategy_id)==set(POLICIES if case[1]=='C57_D1' else POLICIES[:-1])
        ids=None
        for p,t in g.groupby('strategy_id'):
            cur=np.sort(t.realization_id.to_numpy());assert len(cur)==1000
            if ids is None:ids=cur
            assert np.array_equal(cur,ids),'Unmatched realization identity'
    # Retained historical GA output is not another policy: verify equivalence.
    dc=raw[raw.strategy_id.eq('direct-community')&raw.mapping.eq('M1_UTILITY_003')&raw.gate.eq('G1_BASELINE_050')]
    im=d[d.strategy_id.eq('impact-first')]
    joined=dc.merge(im,on=['hazard','resource_scenario','realization_id'],suffixes=('_dc','_impact'),validate='one_to_one')
    assert len(joined)==len(im)
    for m in METRICS:assert np.allclose(joined[m+'_dc'],joined[m+'_impact'],equal_nan=True,rtol=0,atol=1e-12),m
    effects=pd.concat([read(F/'PAIRED_STRATEGY_EFFECTS.csv'),read(E/'VULNERABILITY_PAIRWISE_EFFECTS.csv'),
                       read(E/'VULNERABILITY_RESOURCE_EFFECTS.csv')],ignore_index=True)
    effects=effects[effects.strategy_id.isin(POLICIES)].copy()
    assert not effects.duplicated(['hazard','resource_scenario','strategy_id','reference_strategy','metric']).any()
    effects['case_idx']=[CASES.index((h,r)) for h,r in zip(effects.hazard,effects.resource_scenario)]
    for row in effects.itertuples():
        g=case_slice(d,(row.hazard,row.resource_scenario))
        a=g[g.strategy_id.eq(row.strategy_id)].set_index('realization_id')[row.metric]
        b=g[g.strategy_id.eq(row.reference_strategy)].set_index('realization_id')[row.metric]
        z=(a-b).dropna()
        assert len(z)==row.n_realizations
        if not len(z):
            assert pd.isna(row.paired_mean_difference) and pd.isna(row.paired_median_difference)
            assert pd.isna(row.fraction_delta_below_zero)
            continue
        assert abs(z.mean()-row.paired_mean_difference)<1e-9
        assert abs(z.median()-row.paired_median_difference)<1e-9
        assert abs((z<0).mean()-row.fraction_delta_below_zero)<1e-12
    tract=read(F/'TRACT_PAIRED_EFFECTS.parquet')
    tract=tract[tract.strategy_id.isin(POLICIES)].rename(columns={'paired_mean_delta_burden_hr':'mean_paired_delta_burden_hr','valid_paired_realizations':'valid_realizations'})
    vt=read(E/'VULNERABILITY_TRACT_EFFECTS.parquet');vt['strategy_id']='vulnerability-first';vt['resource_scenario']='C57_D1'
    tract=pd.concat([tract,vt],ignore_index=True)
    keys=['hazard','resource_scenario','strategy_id','reference_strategy']
    assert len(tract.groupby(keys))==68
    for _,g in tract.groupby(keys):assert len(g)==2315 and g.tract_id.nunique()==2315
    definitions=read(V/'SOCIAL_VULNERABILITY_GROUP_RESULT_SENSITIVITY.csv')
    measures={name:read(V/(name+'.csv')) for name in ['SOCIAL_VULNERABILITY_MEASURE_COMPARISON',
      'SOCIAL_VULNERABILITY_Q4_OVERLAP','SOCIAL_VULNERABILITY_QUARTILE_TRANSITION',
      'SOCIAL_VULNERABILITY_POLICY_RANK_SENSITIVITY','SOCIAL_VULNERABILITY_PROVENANCE','CDC_SVI_MISSING_24_EXACT']}
    # Archived +/-1-hour classes are expressly NOT silently reinstated as current effect bins.
    legacy=[read(F/'TRACT_CLASSIFICATION_POPULATION.csv'),read(E/'VULNERABILITY_CLASSIFICATION_POPULATION.csv')]
    geometry=ROOT/'Data/LA_Tracts_With_Population.shp'
    for p in geometry.parent.glob(geometry.stem+'.*'):SOURCES[rel(p)]=sha(p)
    geo=gpd.read_file(geometry);geo['tract_id']=geo.GEOID.astype(str).str.zfill(11)
    accepted_tract_ids=set(tract.tract_id.astype(str).str.zfill(11))
    geo=geo[geo.tract_id.isin(accepted_tract_ids)].copy()
    assert len(geo)==2315
    cover('Every saved primary outcome / all available realizations','primary summaries',23*84000,23*84000,'METRIC_EXPLORER.html | outcome / paired / relationship tabs')
    cover('Existing mean, median, fraction-negative and saved bootstrap CI rows','three frozen effect CSVs',len(effects),len(effects),'SAVED_PAIRED_EFFECTS.pdf; explorer saved uncertainty')
    cover('All saved spatial comparison sets (each 2315 tracts)','two tract-effect parquets',68,68,'SPATIAL_EFFECTS.pdf; explorer spatial tab')
    cover('Alternative vulnerability grouping outcome rows','group sensitivity CSV',72,len(definitions),'VULNERABILITY_DEFINITIONS.pdf; explorer definitions')
    return d,effects,tract,definitions,measures,legacy,geo

def relationships(d):
    book='ALL_METRIC_RELATIONSHIPS.pdf';ms=list(METRICS);pairs=list(itertools.combinations(ms,2))
    means=case_slice(d,('2pc50','C57_D1')).groupby('strategy_id')[ms].mean()
    with PdfPages(OUT/book) as pdf:
        for offset in range(0,len(pairs),4):
            fig,axs=figure('All saved metric pairs | 2pc50 / 57 crews',True);panels=[]
            for k,ax in enumerate(axs):
                if offset+k>=len(pairs):ax.set_axis_off();continue
                x,y=pairs[offset+k]
                for p in POLICIES:
                    ax.scatter(means.loc[p,x],means.loc[p,y],s=22,c=STYLE[p][0],marker=MARKERS[p],edgecolors='white',linewidths=.25)
                title(ax,'ABCD'[k],f'Metric pair {offset+k+1} of {len(pairs)}')
                ax.set_xlabel(wrap(METRICS[x]));ax.set_ylabel(wrap(METRICS[y]))
                if means[x].min()>=0:ax.set_xlim(left=0)
                if means[y].min()>=0:ax.set_ylim(bottom=0)
                panels.append(dict(direction='metric relationship',metric=x+' | '+y,source='primary summaries',context='2pc50 / C57_D1',statistic='policy means'))
            finish(pdf,fig,book,panels,'Points are means of saved outcomes. No causal/optimality claim; overlapping or identical metrics are retained. All contexts and all 1000 realizations per policy can be viewed in the explorer.')
    cover('All pairings among 23 saved primary outcomes','primary summaries',253,len(pairs),book+'; explorer permits every context and reference')

def paired(effects):
    book='SAVED_PAIRED_EFFECTS.pdf';count=0
    with PdfPages(OUT/book) as pdf:
        for metric in METRICS:
            g=effects[effects.metric.eq(metric)]
            if g.empty:continue
            for first in range(0,10,4):
                fig,axs=figure('Saved matched comparisons | '+METRICS[metric]);panels=[]
                fig.subplots_adjust(left=.19,right=.915,wspace=.72)
                for j,ax in enumerate(axs):
                    idx=first+j
                    if idx>=10:ax.set_axis_off();continue
                    s=g[g.case_idx.eq(idx)].copy()
                    if s.empty:
                        ax.set_axis_off();ax.text(.02,.5,wrap('No saved confidence intervals for this metric/condition'),transform=ax.transAxes)
                    else:
                        names=[]
                        for iy,row in enumerate(s.itertuples()):
                            # Native saved CI, without bootstrap or lower-bound clipping.
                            ax.plot([row.bootstrap_ci_low,row.bootstrap_ci_high],[iy,iy],color=STYLE[row.strategy_id][0],lw=1)
                            ax.scatter(row.paired_mean_difference,iy,color=STYLE[row.strategy_id][0],marker=MARKERS[row.strategy_id],s=17)
                            names.append(LABEL[row.strategy_id].replace('-first','')+' - '+LABEL[row.reference_strategy].replace('-first',''))
                            if not row.n_realizations:ax.text(.98,iy,'NA',transform=ax.get_yaxis_transform(),ha='right',fontsize=7)
                        ax.set_yticks(range(len(s)),names);ax.invert_yaxis();ax.axvline(0,color='black',lw=.6)
                        ax.set_xlabel('Candidate minus reference\n'+('Gini (unitless)' if metric=='burden_gini' else 'h' if metric.endswith('_hr') else 'saved metric units'))
                        count+=len(s)
                    title(ax,'ABCD'[j],CASE_LABEL[idx])
                    panels.append(dict(direction='matched mean and existing bootstrap CI',metric=metric,source='three effect CSVs',context=CASE_LABEL[idx],statistic='saved mean + bootstrap95 CI'))
                finish(pdf,fig,book,panels,'Intervals are the already saved 95% bootstrap CIs of matched mean effects, NOT realization ranges. No interval is invented for a missing comparison. Lower cumulative loss is favorable; inequality measures do not define fairness alone.')
            # Every saved median and negative-effect frequency, across all conditions/references.
            comparison=list(dict.fromkeys(zip(g.strategy_id,g.reference_strategy)))
            fig,axs=figure('Uncertainty and reference dependence | '+METRICS[metric]);panels=[]
            fig.subplots_adjust(left=.19,right=.915,wspace=.72)
            fields=['paired_mean_difference','paired_median_difference','fraction_delta_below_zero','change_in_strategy_difference_vs_baseline']
            titles=['Mean matched change','Median matched change','Fraction of realizations with negative change','Resource/duration shift in the strategy contrast']
            for j,(field,t) in enumerate(zip(fields,titles)):
                ax=axs[j];arr=np.full((len(comparison),10),np.nan)
                for iy,(p,r) in enumerate(comparison):
                    q=g[g.strategy_id.eq(p)&g.reference_strategy.eq(r)]
                    for row in q.itertuples():arr[iy,row.case_idx]=getattr(row,field,np.nan)
                finite=arr[np.isfinite(arr)]
                if not len(finite):ax.set_axis_off();ax.text(.05,.5,wrap('No saved resource/duration change field for this metric'),transform=ax.transAxes)
                else:
                    limit=max(abs(finite.min()),abs(finite.max()),1e-9)
                    im=ax.imshow(np.ma.masked_invalid(arr),aspect='auto',cmap='viridis' if j==2 else 'RdBu_r',vmin=0 if j==2 else -limit,vmax=1 if j==2 else limit)
                    ax.set_yticks(range(len(comparison)),[LABEL[p].replace('-first','')+' - '+LABEL[r].replace('-first','') for p,r in comparison])
                    ax.set_xticks(range(10),['LB','SF','NR','2p','29','86','114','.75','1.25','1.5'],rotation=45,ha='right')
                    fig.colorbar(im,ax=ax,fraction=.055,pad=.04).ax.tick_params(labelsize=7)
                    ax.grid(False)
                title(ax,'ABCD'[j],t)
                panels.append(dict(direction=t,metric=metric,source='three effect CSVs',context='all 10 cases',statistic=field))
            finish(pdf,fig,book,panels,'Columns: LB/SF/NR/2p = baseline hazards; 29/86/114 = crew counts; .75/1.25/1.5 = duration factors, all 2pc50. White = unavailable. Frequency below zero is not significance. Contrast shift uses the saved 57-crew / duration-1 reference.')
    assert count==len(effects),(count,len(effects))

def redistribution(d):
    book='QUARTILE_REDISTRIBUTION.pdf'
    with PdfPages(OUT/book) as pdf:
        for case in CASES:
            g=case_slice(d,case);available=[p for p in POLICIES if p in set(g.strategy_id)]
            fig,axs=figure('Quartiles and disagreement among metrics | '+HL[case[0]]+' / '+SHORT[case[1]],True);panels=[]
            cols=[f'burden_Q{i}_hr' for i in range(1,5)]
            for p in available:
                x=g[g.strategy_id.eq(p)][cols].mean()
                axs[0].plot(range(1,5),x,color=STYLE[p][0],ls=STYLE[p][1],marker=MARKERS[p],ms=3)
                ref=g[g.strategy_id.eq(p)].set_index('realization_id')[cols]
                vf=g[g.strategy_id.eq('vulnerability-first')].set_index('realization_id')[cols]
                if p!='vulnerability-first':axs[1].plot(range(1,5),(vf-ref).mean(),color=STYLE[p][0],ls=STYLE[p][1],marker=MARKERS[p],ms=3)
                z=g[g.strategy_id.eq(p)]
                axs[2].scatter(z.signed_Q4_minus_Q1_hr.mean(),z.absolute_Q4_minus_Q1_hr.mean(),c=STYLE[p][0],marker=MARKERS[p],s=25)
                axs[3].scatter(z.burden_Q4_hr.mean(),z.burden_gini.mean(),c=STYLE[p][0],marker=MARKERS[p],s=25)
            for ax in axs[:2]:ax.set_xticks(range(1,5),['Q1','Q2','Q3','Q4']);ax.set_xlabel('Social-vulnerability quartile')
            axs[0].set_ylabel('Population-weighted cumulative\nservice loss within quartile (h)');axs[0].set_ylim(bottom=0)
            axs[1].axhline(0,color='black',lw=.6);axs[1].set_ylabel('Vulnerability-first minus\nlegend reference (h)')
            axs[2].set_xlabel('Mean signed Q4 minus Q1 loss (h)');axs[2].set_ylabel('Mean realization-wise absolute\nQ4 minus Q1 loss (h)')
            axs[2].set_ylim(0,g.absolute_Q4_minus_Q1_hr.groupby(g.strategy_id).mean().max()*1.08)
            axs[3].set_xlabel('Q4 cumulative service loss (h)');axs[3].set_ylabel('Population-weighted Gini (unitless)')
            axs[3].set_ylim(0,g.burden_gini.groupby(g.strategy_id).mean().max()*1.08)
            for i,t in enumerate(['All-policy absolute quartile outcomes','Vulnerability-first against every available reference','Signed versus absolute group separation','Q4 outcome versus tract inequality']):
                title(axs[i],'ABCD'[i],t);panels.append(dict(direction=t,metric='Q1-Q4; signed/absolute gap; Gini',source='primary summaries',context=HL[case[0]]+' / '+case[1],statistic='means of saved quantities; matched subtraction for B'))
            finish(pdf,fig,book,panels,'Q1 = lowest and Q4 = highest social vulnerability. Absolute separation is averaged AFTER taking each realization\'s absolute gap. Gini: 0 = equal tract loss; larger = more unequal loss. No policy is labeled most equitable.')

def spatial(tract,geo):
    book='SPATIAL_EFFECTS.pdf';keys=['hazard','resource_scenario','strategy_id','reference_strategy']
    geo=geo.to_crs(3310)
    with PdfPages(OUT/book) as pdf:
        for key,g in tract.groupby(keys,sort=False):
            h,r,p,ref=key;g=g.copy();g['tract_id']=g.tract_id.astype(str).str.zfill(11)
            z=geo[['tract_id','geometry']].merge(g,on='tract_id',validate='one_to_one')
            fig,axs=figure(LABEL[p]+' minus '+LABEL[ref]+' | '+HL[h]+' / '+SHORT[r]);panels=[]
            fig.subplots_adjust(right=.92)
            limit=max(abs(z.mean_paired_delta_burden_hr.min()),abs(z.mean_paired_delta_burden_hr.max()),1e-9)
            for i,col in enumerate(['mean_paired_delta_burden_hr','probability_delta_below_zero']):
                ax=axs[i];z.plot(column=col,ax=ax,cmap='RdBu_r' if i==0 else 'viridis',vmin=-limit if i==0 else 0,vmax=limit if i==0 else 1,
                    linewidth=0,missing_kwds={'color':'#ddd','hatch':'///'})
                ax.set_axis_off();ax.set_aspect('equal')
                cb=fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(-limit if i==0 else 0,limit if i==0 else 1),cmap='RdBu_r' if i==0 else 'viridis'),ax=ax,fraction=.047,pad=.025)
                cb.set_label('Mean loss change (h)' if i==0 else 'Realization fraction below zero',fontsize=7.5)
            # Population-weighted empirical distribution of TRACT MEAN effect, not raw realization effects.
            for q,color in zip(['Q1','Q2','Q3','Q4'],['#377eb8','#7c9b72','#9b738f','#a65628']):
                s=z[z.quartile.astype(str).isin([q,q[-1]])].dropna(subset=['mean_paired_delta_burden_hr']).sort_values('mean_paired_delta_burden_hr')
                if len(s) and s.population.sum()>0:axs[2].step(s.mean_paired_delta_burden_hr,s.population.cumsum()/s.population.sum(),where='post',label=q,color=color,lw=1.2)
            axs[2].axvline(0,color='black',lw=.6);axs[2].set_xlabel('Tract mean cumulative-loss change (h)');axs[2].set_ylabel('Cumulative population fraction');axs[2].legend(frameon=False,ncol=2)
            populations=[]
            for q in ['Q1','Q2','Q3','Q4']:
                s=z[z.quartile.astype(str).isin([q,q[-1]])];pop=s.population.sum()
                populations.append([s.loc[s.mean_paired_delta_burden_hr.lt(0),'population'].sum()/pop if pop else np.nan,
                                    s.loc[s.mean_paired_delta_burden_hr.gt(0),'population'].sum()/pop if pop else np.nan])
            vals=np.asarray(populations);axs[3].plot(range(1,5),vals[:,0],marker='o',color='#356d9b',label='Lower tract mean loss')
            axs[3].plot(range(1,5),vals[:,1],marker='s',color='#9b563a',ls='--',label='Higher tract mean loss')
            axs[3].set_xticks(range(1,5),['Q1','Q2','Q3','Q4']);axs[3].set_ylim(0,1);axs[3].set_ylabel('Fraction of quartile population')
            handles,names=axs[3].get_legend_handles_labels()
            fig.legend(handles,names,frameon=False,loc='lower center',bbox_to_anchor=(.735,.059))
            for i,t in enumerate(['Tract mean service-loss change','Frequency of lower loss across realizations','Spatial distribution by vulnerability quartile','Population classified by tract mean sign']):
                title(axs[i],'ABCD'[i],t);panels.append(dict(direction=t,metric='saved tract mean / empirical frequency',source='tract-effect parquets',context=' / '.join(key),statistic='saved fields; population aggregation of mean signs'))
            finish(pdf,fig,book,panels,'Mean-sign population is NOT the mean population benefiting in each realization. Negative mean does not prove significance. Frequency is a saved empirical frequency; maps do not show electricity delivery or hospital operation.')

def grouping(definitions):
    book='VULNERABILITY_DEFINITIONS.pdf'
    with PdfPages(OUT/book) as pdf:
        for key,g in definitions.groupby(['hazard','measure','grouping_scheme'],sort=False):
            h,measure,scheme=key
            fig,axs=figure(HL[h]+' | '+MEASURE_LABEL[measure]+' | '+GROUP_LABEL[scheme]);panels=[]
            for row in g.itertuples():
                p=row.strategy;color=STYLE[p][0]
                axs[0].plot(range(1,5),[getattr(row,f'burden_Q{q}_hr') for q in range(1,5)],color=color,ls=STYLE[p][1],marker=MARKERS[p],ms=3,label=LABEL[p])
                axs[2].scatter(row.signed_Q4_minus_Q1_hr,row.absolute_Q4_minus_Q1_hr,color=color,marker=MARKERS[p],s=25)
                axs[3].scatter(row.burden_Q4_hr,row.population_weighted_gini_mean,color=color,marker=MARKERS[p],s=25)
                if p=='vulnerability-first':
                    for q in range(1,5):
                        m=getattr(row,f'vuln_minus_hospital_Q{q}_hr');lo=getattr(row,f'vuln_minus_hospital_Q{q}_bootstrap95_low_hr');hi=getattr(row,f'vuln_minus_hospital_Q{q}_bootstrap95_high_hr')
                        axs[1].plot([q,q],[lo,hi],color=color,lw=1);axs[1].scatter(q,m,color=color,marker=MARKERS[p],s=30)
            for ax in axs[:2]:ax.set_xticks(range(1,5),['Q1','Q2','Q3','Q4'])
            axs[0].set_ylabel('Quartile cumulative service loss (h)');axs[0].set_ylim(bottom=0);axs[0].legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.22))
            axs[1].axhline(0,color='black',lw=.6);axs[1].set_ylabel('Vulnerability-first minus\nHospital-first (h)')
            axs[2].set_xlabel('Signed Q4 minus Q1 loss (h)');axs[2].set_ylabel('Absolute Q4 minus Q1 loss (h)')
            axs[3].set_xlabel('Q4 cumulative service loss (h)');axs[3].set_ylabel('Population-weighted Gini (unitless)')
            for i,t in enumerate(['Absolute outcomes under saved grouping','Saved matched-mean bootstrap intervals','Signed and absolute group separation','Q4 outcome and tract inequality']):
                title(axs[i],'ABCD'[i],t);panels.append(dict(direction=t,metric='grouping sensitivity saved metrics',source='SOCIAL_VULNERABILITY_GROUP_RESULT_SENSITIVITY.csv',context=' / '.join(key),statistic='saved summary / saved bootstrap95 CI'))
            finish(pdf,fig,book,panels,'Same executed policies; changing the evaluation grouping does NOT rerun vulnerability targeting. Q4 is highest social vulnerability, not income class. Missing CDC scores are excluded from groups, not treated as low vulnerability. Gini is unitless.')

def measure_views(measures,definitions):
    book='MEASURE_AND_TARGETING.pdf';a=measures['SOCIAL_VULNERABILITY_MEASURE_COMPARISON'];t=measures['SOCIAL_VULNERABILITY_QUARTILE_TRANSITION']
    with PdfPages(OUT/book) as pdf:
        for row in a.itertuples():
            fig,axs=figure(MEASURE_LABEL[row.measure_a]+' versus '+MEASURE_LABEL[row.measure_b]);panels=[]
            axs[0].bar(['Pearson','Spearman'],[row.pearson,row.spearman],color=['#537f91','#9b738f']);axs[0].set_ylim(-1,1);axs[0].set_ylabel('Saved correlation coefficient')
            axs[1].bar(['Tract Jaccard','Population overlap'],[row.q4_jaccard,row.q4_population_weighted_overlap],color=['#537f91','#9b738f']);axs[1].set_ylim(0,1);axs[1].set_ylabel('Q4 membership overlap (fraction)')
            s=t[t.measure_a.eq(row.measure_a)&t.measure_b.eq(row.measure_b)]
            for j,col in enumerate(['tract_count','population'],2):
                mat=s.pivot(index='group_a',columns='group_b',values=col);im=axs[j].imshow(mat,cmap='Blues',aspect='equal');axs[j].grid(False)
                axs[j].set_xticks(range(4),['Q1','Q2','Q3','Q4']);axs[j].set_yticks(range(4),['Q1','Q2','Q3','Q4']);axs[j].set_xlabel('Measure B quartile');axs[j].set_ylabel('Measure A quartile')
                for y in range(4):
                    for x in range(4):axs[j].text(x,y,f'{mat.iloc[y,x]:,.0f}',ha='center',va='center',fontsize=7,color='white' if mat.iloc[y,x]>mat.max().max()*.6 else 'black')
                fig.colorbar(im,ax=axs[j],fraction=.048,pad=.025)
            for j,txt in enumerate(['Score association','Highest-vulnerability group overlap','Quartile transitions: tracts','Quartile transitions: population']):
                title(axs[j],'ABCD'[j],txt);panels.append(dict(direction=txt,metric='saved comparison / transition',source='measure comparison and transition CSVs',context=row.measure_a+' / '+row.measure_b,statistic='provider/table-defined saved statistics'))
            finish(pdf,fig,book,panels,'These are agreement between vulnerability measures, not ground-truth validation. Common valid tracts = '+str(row.common_valid_tracts)+'. Missing scores remain missing. Evaluation grouping and unexecuted targeting ranks are distinct.')
        rank=measures['SOCIAL_VULNERABILITY_POLICY_RANK_SENSITIVITY']
        fig,axs=figure('Alternative vulnerability-targeting ranks | NOT executed policies');panels=[]
        for j,(measure,g) in enumerate(rank.groupby('measure',sort=False)):
            axs[j].scatter(g.frozen_rank,g.candidate_rank,s=12,color='#537f91',alpha=.65);axs[j].plot([1,92],[1,92],ls='--',color='black',lw=.6)
            axs[j].set_xlabel('Executed targeting priority rank');axs[j].set_ylabel('Alternative-definition candidate rank');axs[j].set_xlim(0,93);axs[j].set_ylim(0,93)
            title(axs[j],'ABCD'[j],MEASURE_LABEL[measure]);panels.append(dict(direction='candidate targeting identity',metric='candidate vs frozen rank',source='POLICY_RANK_SENSITIVITY.csv',context=measure,statistic='saved ranks, 92 stations'))
        finish(pdf,fig,book,panels,'No schedules or outcomes were executed for these alternative ranks. They cannot be used to claim a restoration benefit. Exact station scores and ranks are available in the explorer source table.')
        # All six stored Q4 spatial-effect quantiles, all hazard/grouping combinations.
        for h,g in definitions[definitions.strategy.eq('vulnerability-first')].groupby('hazard',sort=False):
            fig,axs=figure(HL[h]+' | Q4 spatial-effect distributions by vulnerability definition');panels=[]
            for j,qs in enumerate([(5,25,50,75,95),(5,95),(25,50,75),None]):
                ax=axs[j]
                names=[x.measure.replace('_',' ')+'\n'+x.grouping_scheme.replace('_',' ') for x in g.itertuples()]
                for iy,row in enumerate(g.itertuples()):
                    if qs:
                        vals=[getattr(row,f'Q4_tract_effect_population_weighted_q{q}_hr') for q in qs]
                        ax.plot(vals,[iy]*len(vals),ls='-',marker='o',ms=3,color='#a65628',lw=.8)
                    else:ax.scatter(row.Q4_tract_effect_population_weighted_mean_hr,iy,color='#a65628',s=18)
                ax.set_yticks(range(len(g)),[str(i+1) for i in range(len(g))]);ax.axvline(0,color='black',lw=.6);ax.set_xlabel('Tract mean loss change (h)');ax.set_ylabel('Grouping definition number')
                txt=['All five saved quantiles','5th and 95th spatial percentiles','25th, 50th and 75th spatial percentiles','Population-weighted spatial mean'][j]
                title(ax,'ABCD'[j],txt);panels.append(dict(direction=txt,metric='Q4 tract mean effect distribution',source='GROUP_RESULT_SENSITIVITY.csv',context=h,statistic='saved population-weighted spatial quantiles, not bootstrap CI'))
            # Avoid compressed very long scheme labels: full key placed on companion explorer.
            finish(pdf,fig,book,panels,'Grouping keys, in source order: 1 frozen Q; 2 NRI study quartiles; 3 NRI external bands; 4 CDC study quartiles; 5 CDC external bands; 6 Stage7 theme mean. Effects relative to Hospital-first. Spatial percentiles are not realization ranges or CIs.')

def explorer(d,effects,tract,definitions,measures,legacy,geo):
    cases=[];ms=list(METRICS)
    for case in CASES:
        g=case_slice(d,case);pol={}
        for p in POLICIES:
            s=g[g.strategy_id.eq(p)].sort_values('realization_id')
            if len(s):pol[p]={'ids':s.realization_id.tolist(),'values':s[ms].to_numpy()}
        cases.append({'name':HL[case[0]]+' | '+SHORT[case[1]],'hazard':case[0],'resource':case[1],'policies':pol})
    sets=[]
    for key,g in tract.groupby(['hazard','resource_scenario','strategy_id','reference_strategy'],sort=False):
        sets.append({'name':HL[key[0]]+' | '+SHORT[key[1]]+' | '+LABEL[key[2]]+' minus '+LABEL[key[3]],'rows':g.drop(columns=['mean_effect_classification'],errors='ignore').to_dict('records')})
    payload={'metrics':METRICS,'policies':LABEL,'colors':{p:STYLE[p][0] for p in POLICIES},
        'cases':cases,'effects':effects.to_dict('records'),'spatial':sets,
        'definitions':definitions.to_dict('records'),'measures':{k:v.to_dict('records') for k,v in measures.items()},
        'archivedClasses':[x.to_dict('records') for x in legacy]}
    encoded=base64.b64encode(gzip.compress(json.dumps(numeric_clean(payload),separators=(',',':'),allow_nan=False).encode())).decode()
    template=(OUT/'explorer_template.html').read_text(encoding='utf-8')
    template=template.replace('__PLOTLY__',get_plotlyjs()).replace('__PAYLOAD__',encoded)
    (OUT/'METRIC_EXPLORER.html').write_text(template,encoding='utf-8')

def qa_and_docs(d,effects,tract,definitions,measures,before):
    measured=[];contact=fitz.open()
    for path in sorted(OUT.glob('*.pdf')):
        if path.name=='REVIEW_CONTACT_SHEET.pdf':continue
        doc=fitz.open(path)
        for i,page in enumerate(doc):
            spans=[s for b in page.get_text('dict')['blocks'] if 'lines'in b for l in b['lines'] for s in l['spans'] if s['text'].strip()]
            assert spans and min(s['size'] for s in spans)>=6.99,(path,i,min(s['size'] for s in spans))
            assert all('Arial' in s['font'] for s in spans),(path,i,set(s['font'] for s in spans))
            assert all(fitz.Rect(s['bbox']).x0>=-.1 and fitz.Rect(s['bbox']).x1<=page.rect.width+.1 and fitz.Rect(s['bbox']).y1<=page.rect.height+.1 for s in spans),(path,i,'clipped')
            measured.append(dict(book=path.name,page=i+1,width_mm=page.rect.width*25.4/72,height_mm=page.rect.height*25.4/72,min_font_pt=min(s['size'] for s in spans),fonts=';'.join(sorted({s['font'] for s in spans}))))
            if i==0:
                page.get_pixmap(matrix=fitz.Matrix(600/72,600/72),alpha=False).save(OUT/(path.stem+'_600dpi.png'))
            # Render every page for actual output review, four per contact page.
            cell=len(measured)-1
            if cell%4==0:
                cp=contact.new_page(width=595,height=842)
                cp.insert_font(fontname='LocalArial',fontfile='C:/Windows/Fonts/arial.ttf')
            dst=contact[-1];x=10+(cell%2)*290;y=25+((cell%4)//2)*405
            dst.insert_text((x,y-6),path.stem[:36]+f' p{i+1}',fontsize=9,fontname='LocalArial')
            pix=page.get_pixmap(matrix=fitz.Matrix(1,1),alpha=False)
            dst.insert_image(fitz.Rect(x,y,x+276,y+382),pixmap=pix,keep_proportion=True)
        doc.close()
    contact.save(OUT/'REVIEW_CONTACT_SHEET.pdf',garbage=4,deflate=True);contact.close()
    pd.DataFrame(measured).to_csv(OUT/'ACTUAL_PDF_MEASUREMENTS.csv',index=False)
    # A deterministic index also supports presentation-only layout repair.
    rebuild_panel_index(effects,tract,definitions,measures)
    write_panel_index()
    # Explicit holes: not paper claims and never auto-filled.
    gaps=[
        ('Saved bootstrap CIs for every arbitrary policy/reference/metric pair','Only Hospital-reference formal metrics and VF/Hospital or VF/Impact effects have saved CIs. Other pairs available as matched raw distributions; no fresh resampling.'),
        ('Vulnerability-first resource/duration tract-level effects','Only four baseline hazards x Hospital/Impact spatial references are saved. No VF resource spatial maps generated.'),
        ('All executed strategies evaluated under alternative vulnerability definitions','Saved grouping sensitivity contains Impact, Hospital and Vulnerability only. Other policies are not inferred.'),
        ('Continuous resource response','Only four discrete crew conditions and four discrete duration factors exist. No interpolation or response-function claim.'),
        ('Electricity delivered or clinical service quantities','Metrics are modeled service-loss/recovery quantities. No delivered MW, hospital operating capability, intervention/cost evidence.'),
        ('Archived +/-1-hour affected-population categories','Tables retained with explicit legacy label in explorer; not reinstated as current tract classifications. Current maps use continuous means and empirical frequencies.')]
    for name,note in gaps:cover(name,'saved accepted evidence',1,0,'EVIDENCE_AVAILABILITY.md',note)
    pd.DataFrame(COVER).to_csv(OUT/'METRIC_DIRECTION_COVERAGE.csv',index=False)
    detailed_availability(d,effects)
    duplicates=[]
    for a,b in itertools.combinations(METRICS,2):
        x=d[a].to_numpy(float);y=d[b].to_numpy(float)
        if np.allclose(x,y,rtol=0,atol=1e-10,equal_nan=True):duplicates.append((a,b))
    (OUT/'EVIDENCE_AVAILABILITY.md').write_text('# Evidence availability, without author selection\n\n'+
        '\n\n'.join('**'+name+'**\n\n'+note for name,note in gaps)+
        '\n\n## Numerically redundant saved fields\n\n'+str(duplicates)+
        '\n\nHistorical hazards and 2pc50 use different adopted fragility parameters. Hazard contrasts are not pure PGA sensitivity. All original result fields remain accessible. No outcomes are removed because they repeat another metric.\n',encoding='utf-8')
    (OUT/'METRIC_DEFINITIONS.md').write_text('''# What these metrics mean

All cumulative service-loss metrics integrate the saved modeled deficit over 0-480 h. Units h are equivalent complete-service-loss hours, not electricity or clinical performance. “Burden” and “cumulative service loss” label the same integrated metric here.

- Population-weighted loss: normalized tract service deficit, weighted by tract population.
- Population/dependency-mass-weighted loss: population times represented dependency mass weighting; separately saved and retained even if identical within the fully resolved domain.
- Hospital-linked loss: equally weighted mean across the hospital-linked tracts, NOT hospital population weighting or actual hospital electricity.
- Q1-Q4: population weighting within each adopted social-vulnerability group. Q1 lowest, Q4 highest; these are not income classes.
- Signed gap: Q4 minus Q1 in each realization. Absolute gap: absolute value in each realization, then averaged; NOT absolute value of the mean signed gap.
- Population-weighted Gini: inequality of tract burden, 0 equal, larger more unequal. It does not decide which strategy is equitable.
- T50/T80/T90: time to the stated population-service fraction. Missing/unreached stays NA, never replaced by zero or 480.
- Local/threshold/source-path loss: adopted decomposition, dependency-mass weighted; shares are saved per-realization fractions. Ratio of mean components is not substituted for mean fractions.
- Task count, completion and travel: saved scheduling outcomes, not re-executed here.

Means, realization ranges, existing bootstrap confidence intervals, and spatial tract percentiles are distinct. The explorer identifies their definitions. Matched effects join the same saved realization IDs before differencing, without new resampling. No correlation or direction of an outcome is treated as causality, optimality or a fairness verdict.

Spatial sign populations classify the population of tracts by mean paired effect. This is not mean benefiting population per realization and is not significance. The saved negative-effect frequency is an empirical frequency, not a p-value. Alternative vulnerability groupings re-evaluate the same executed strategies; alternative priority ranks were not executed.
''',encoding='utf-8')
    (OUT/'README.md').write_text('''# Complete metric and trade-off review (no manuscript selection)

Open **METRIC_EXPLORER.html** locally in Chrome/Edge. It is self-contained: every available policy, condition, 23 outcome fields and all 1,000 realization rows are embedded without point thinning.

| Review book | Question answered |
|---|---|
| ALL_METRIC_RELATIONSHIPS.pdf | How do all 253 metric pairs relate across policies? Baseline means in PDF; all contexts/raw realizations in explorer. |
| SAVED_PAIRED_EFFECTS.pdf | How do mean, median, empirical improvement frequency and existing bootstrap intervals differ with reference/hazard/resource/duration? |
| QUARTILE_REDISTRIBUTION.pdf | Who improves or waits longer under every executed policy, and do signed gap, absolute gap and Gini disagree? |
| SPATIAL_EFFECTS.pdf | Where do mean effects occur, how often does a tract improve, and how is population distributed? All 68 saved spatial comparisons. |
| VULNERABILITY_DEFINITIONS.pdf | Are outcomes sensitive to the six saved grouping definitions, under the same executed policies? |
| MEASURE_AND_TARGETING.pdf | Do vulnerability measures agree on score/groups/ranks, and what are the saved within-Q4 spatial distributions? |

Every book is 185 mm wide with Arial text at least 7 pt; first-page PNGs are 600 dpi previews. REVIEW_CONTACT_SHEET.pdf renders EVERY book page, four per page. It is an overview, not the readable scientific authority.

METRIC_DIRECTION_COVERAGE.csv and PANEL_SOURCE_INDEX.csv identify coverage and exact page/panel. METRIC_DEFINITIONS.md explains weighting and intervals. EVIDENCE_AVAILABILITY.md identifies actual gaps without filling them. The earlier 23-page individual-metric browser is retained at ALL_SUMMARY_METRICS_REVIEW.pdf.

Nothing here selects a Main/Supplement set or promotes figures. Existing results/figures and candidate layouts are unchanged. Source/index hashes and scientific-file guards are in QA_MANIFEST.json. Regenerate only this review presentation with `python results/figure_review/Additional_Evidence/build_review.py`.
''',encoding='utf-8')
    after=protect_snapshot();assert before==after,'Existing scientific/artwork file metadata changed'
    assert all(sha(ROOT/p)==s for p,s in SOURCES.items()),'Read authority hash changed'
    qa=dict(scientific_calculations_executed=False,source_hash_changes=0,existing_file_metadata_changes=0,
        guarded_existing_files=len(before),source_sha256=SOURCES,primary_rows=len(d),metrics=len(METRICS),
        paired_effect_rows=len(effects),spatial_comparison_sets=68,group_sensitivity_rows=len(definitions),
        pdf_pages=len(measured),metric_pairs=253,minimum_font_pt=min(x['min_font_pt'] for x in measured),
        index_baseline_sha256=INDEX_SHA,policy_ids=POLICIES,
        numerical_mean_median_frequency_crosscheck='all saved rows match raw realization subtraction within 1e-9',
        presentation_semantics='No selection, no new CI, no new metrics; arithmetic summaries of existing rows only')
    (OUT/'QA_MANIFEST.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in qa.items() if k!='source_sha256'},indent=2),flush=True)

def detailed_availability(d,effects):
    """Inventory saved evidence, including unavailable CI cells; no inference."""
    rows=[];domain=[];ms=list(METRICS)
    lookup={tuple(row[k] for k in ['hazard','resource_scenario','strategy_id','reference_strategy','metric']):row
            for row in effects.to_dict('records')}
    for case in CASES:
        g=case_slice(d,case);arrays={p:s.sort_values('realization_id')[ms].to_numpy(float) for p,s in g.groupby('strategy_id')}
        for p in POLICIES:
            domain.append(dict(hazard=case[0],resource=case[1],policy=p,available=p in arrays,
                saved_realizations=len(arrays.get(p,[])),notes='' if p in arrays else 'Unconstrained not saved for this sensitivity case; not manufactured'))
        for p,r in itertools.permutations(arrays,2):
            valid=np.isfinite(arrays[p]-arrays[r]).sum(axis=0)
            for m,n in zip(ms,valid):
                s=lookup.get((*case,p,r,m))
                rows.append(dict(hazard=case[0],resource=case[1],candidate=p,reference=r,metric=m,
                    reader_facing_metric=METRICS[m],valid_raw_pairs=int(n),
                    saved_bootstrap_row=s is not None,
                    finite_saved_bootstrap_ci=s is not None and pd.notna(s['bootstrap_ci_low']) and pd.notna(s['bootstrap_ci_high']),
                    location='METRIC_EXPLORER.html | Every matched reference; existing-CI tab if saved',
                    notes='No saved CI is generated here' if s is None else 'Saved n=0/NA remains NA' if not n else 'Frozen interval copied without resampling'))
    assert len(rows)==14352,len(rows)
    pd.DataFrame(rows).to_csv(OUT/'REFERENCE_UNCERTAINTY_AVAILABILITY.csv',index=False)
    pd.DataFrame(domain).to_csv(OUT/'POLICY_CONDITION_AVAILABILITY.csv',index=False)
    per=[]
    for m in METRICS:
        e=effects[effects.metric.eq(m)];cells=[r for r in rows if r['metric']==m]
        per.append(dict(metric=m,reader_facing_metric=METRICS[m],saved_rows=len(d),finite_outcome_rows=int(d[m].notna().sum()),
            condition_count=10,policy_condition_cells=84,other_metric_partners=22,
            available_directed_reference_comparisons=len(cells),saved_bootstrap_rows=len(e),
            finite_saved_bootstrap_rows=int(e.bootstrap_ci_low.notna().sum()),
            raw_distribution='explorer absolute-outcomes tab',raw_matched_effect='explorer every-matched-reference tab',
            joint_relationship='ALL_METRIC_RELATIONSHIPS.pdf + explorer relationships',
            context='all four hazards, four discrete crew counts, four discrete duration factors',
            spatial='saved tract cumulative-loss effects only; not tract-level Gini/T80/other arbitrary metric effects',
            notes='Saved gaps shown explicitly; no fresh CI or metric definition'))
    pd.DataFrame(per).to_csv(OUT/'METRIC_BY_DIRECTION_MATRIX.csv',index=False)
    (OUT/'INFORMATION_DIRECTIONS.md').write_text('''# What was missing from the previous presentation

The earlier 23-page browser displayed individual saved outcome fields by condition. That was not a complete presentation of the new metrics and trade-off evidence.

This review makes the following distinct directions accessible without selecting policies or “favorable” results:

1. Absolute levels AND all realization distributions, including missing/unreached counts.
2. Every available matched candidate/reference combination, not only Vulnerability-first versus Hospital-first.
3. Every pair of the 23 saved outcome fields: all-policy means AND the full 1,000-realization cloud, under every available condition.
4. Saved matched means, medians, empirical frequencies and bootstrap intervals. No confidence interval is silently substituted by a realization range.
5. Q1–Q4 absolute outcomes and redistribution; signed gap versus realization-wise absolute gap; Q4 outcome versus population-weighted Gini. Disagreeing directions are visible rather than reduced to a fairness verdict.
6. Hazard, crew-count and duration contexts, including the saved change in strategy contrast relative to baseline. These are discrete comparisons, not continuous response functions.
7. All 68 saved spatial comparison sets: continuous tract mean, empirical improvement frequency, quartile distributions and population classified by mean sign.
8. Six alternative evaluation-group definitions; group counts/populations, missing-score coverage, saved quartile intervals and spatial-effect percentiles.
9. Vulnerability score associations, Q4 overlap and transitions, alternative station-targeting ranks/scores, and their distinct lack of executed outcome evidence.
10. Legacy affected-population tables remain discoverable with their original ±1-hour definitions; those definitions are not reinstated in current maps.

METRIC_BY_DIRECTION_MATRIX.csv has one row for every saved outcome. REFERENCE_UNCERTAINTY_AVAILABILITY.csv enumerates all 14,352 available metric × directed-reference × condition cells and flags precisely where a saved CI exists, is NA, or is absent. POLICY_CONDITION_AVAILABILITY.csv lists the 90 policy/condition possibilities, including the six absent Unconstrained sensitivity cases.

This is complete access to these saved metric/trade-off evidence dimensions, not a claim that every possible future analysis was already conducted. EVIDENCE_AVAILABILITY.md records missing VF sensitivity spatial outputs, absent arbitrary-reference CIs and unexecuted alternative-targeting policies. No paper Main/Supplement selection, no new uncertainty resampling and no promotion of review figures is performed.
''',encoding='utf-8')

def rebuild_panel_index(effects,tract,definitions,measures):
    PAGE_ROWS.clear()
    def add(book,page,context,metrics,source,statistic,directions):
        for letter,direction in zip('ABCD',directions):
            PAGE_ROWS.append(dict(book=book,page=page,panel=letter,direction=direction,
                metric=metrics,source=source,context=context,statistic=statistic))
    pairs=list(itertools.combinations(METRICS,2))
    for i,(x,y) in enumerate(pairs):
        PAGE_ROWS.append(dict(book='ALL_METRIC_RELATIONSHIPS.pdf',page=i//4+1,panel='ABCD'[i%4],
            direction='All-metric relationship',metric=x+' | '+y,source='Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet + Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet',context='2pc50 / C57_D1',statistic='means of saved outcomes'))
    page=0
    for m in METRICS:
        if not effects.metric.eq(m).any():continue
        for first in range(0,10,4):
            page+=1
            for j in range(min(4,10-first)):
                PAGE_ROWS.append(dict(book='SAVED_PAIRED_EFFECTS.pdf',page=page,panel='ABCD'[j],
                    direction='Existing matched mean and bootstrap95 interval',metric=m,context=CASE_LABEL[first+j],
                    source='Formal PAIRED_STRATEGY_EFFECTS.csv; VULNERABILITY_PAIRWISE_EFFECTS.csv; VULNERABILITY_RESOURCE_EFFECTS.csv',statistic='saved mean / bootstrap CI; reference stated on row'))
        page+=1
        add('SAVED_PAIRED_EFFECTS.pdf',page,'all 10 cases; candidate and reference on row',m,
            'three paired-effect CSVs','saved fields',['Mean effect','Median effect','Fraction below zero','Saved shift in contrast versus baseline'])
    for i,case in enumerate(CASES,1):
        add('QUARTILE_REDISTRIBUTION.pdf',i,CASE_LABEL[i-1],'Q1-Q4; signed/absolute gap; Gini','primary summary parquets',
            'means of saved quantities; matched raw subtraction for B',['Absolute outcomes','Vulnerability-first minus each available reference','Signed versus absolute gap','Q4 versus Gini'])
    for i,(key,g) in enumerate(tract.groupby(['hazard','resource_scenario','strategy_id','reference_strategy'],sort=False),1):
        add('SPATIAL_EFFECTS.pdf',i,' / '.join(key),'tract mean / fraction below zero / population',
            'TRACT_PAIRED_EFFECTS.parquet; VULNERABILITY_TRACT_EFFECTS.parquet','saved fields; population aggregation of tract mean signs',
            ['Mean effect map','Empirical improvement-frequency map','Population-weighted spatial ECDF','Population classified by mean sign'])
    for i,(key,g) in enumerate(definitions.groupby(['hazard','measure','grouping_scheme'],sort=False),1):
        add('VULNERABILITY_DEFINITIONS.pdf',i,' / '.join(key),'Q1-Q4; signed/absolute gap; Gini',
            'SOCIAL_VULNERABILITY_GROUP_RESULT_SENSITIVITY.csv','saved summary / saved bootstrap CI; VF minus Hospital',
            ['Absolute quartile outcomes','Saved matched bootstrap CI','Signed and absolute gaps','Q4 versus Gini'])
    a=measures['SOCIAL_VULNERABILITY_MEASURE_COMPARISON'];n=0
    for row in a.itertuples():
        n+=1;add('MEASURE_AND_TARGETING.pdf',n,row.measure_a+' / '+row.measure_b,'correlation / Q4 overlap / transitions',
            'MEASURE_COMPARISON.csv; QUARTILE_TRANSITION.csv','saved coefficients / tract and population counts',
            ['Score association','Q4 overlap','Tract transitions','Population transitions'])
    n+=1
    add('MEASURE_AND_TARGETING.pdf',n,'four definitions; all 92 stations','candidate/frozen rank',
        'SOCIAL_VULNERABILITY_POLICY_RANK_SENSITIVITY.csv','saved ranks; NOT executed policies',
        [x.replace('_',' ') for x in measures['SOCIAL_VULNERABILITY_POLICY_RANK_SENSITIVITY'].measure.unique()])
    for h in definitions.hazard.unique():
        n+=1;add('MEASURE_AND_TARGETING.pdf',n,h+' / all grouping definitions','Q4 spatial-effect population-weighted quantiles',
            'SOCIAL_VULNERABILITY_GROUP_RESULT_SENSITIVITY.csv','saved tract-effect spatial percentiles; relative to Hospital',
            ['All five spatial quantiles','5th and 95th','25th, 50th and 75th','Spatial population-weighted mean'])

def write_panel_index():
    by_book={
     'ALL_METRIC_RELATIONSHIPS.pdf':[F/'PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',E/'VULNERABILITY_PRIMARY_SUMMARY.parquet'],
     'SAVED_PAIRED_EFFECTS.pdf':[F/'PAIRED_STRATEGY_EFFECTS.csv',E/'VULNERABILITY_PAIRWISE_EFFECTS.csv',E/'VULNERABILITY_RESOURCE_EFFECTS.csv'],
     'QUARTILE_REDISTRIBUTION.pdf':[F/'PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet',E/'VULNERABILITY_PRIMARY_SUMMARY.parquet'],
     'SPATIAL_EFFECTS.pdf':[F/'TRACT_PAIRED_EFFECTS.parquet',E/'VULNERABILITY_TRACT_EFFECTS.parquet',ROOT/'Data/LA_Tracts_With_Population.shp'],
     'VULNERABILITY_DEFINITIONS.pdf':[V/'SOCIAL_VULNERABILITY_GROUP_RESULT_SENSITIVITY.csv']}
    for row in PAGE_ROWS:
        paths=by_book.get(row['book'])
        if row['book']=='MEASURE_AND_TARGETING.pdf':
            paths=[V/'SOCIAL_VULNERABILITY_MEASURE_COMPARISON.csv',V/'SOCIAL_VULNERABILITY_QUARTILE_TRANSITION.csv'] if row['page']<=6 else [V/'SOCIAL_VULNERABILITY_POLICY_RANK_SENSITIVITY.csv'] if row['page']==7 else [V/'SOCIAL_VULNERABILITY_GROUP_RESULT_SENSITIVITY.csv']
        row['source']='; '.join(rel(p) for p in paths)
        row['production_selection']='M1_UTILITY_003 / G1_BASELINE_050; source context in row; exclude sequence-equivalent direct-community reporting duplicate'
        row['reference_policy']='Absolute outcomes' if row['book']=='ALL_METRIC_RELATIONSHIPS.pdf' else 'Candidate/reference listed on row; NOT a universal Hospital reference' if row['book']=='SAVED_PAIRED_EFFECTS.pdf' else 'Each available reference in B; absolute outcomes in A/C/D' if row['book']=='QUARTILE_REDISTRIBUTION.pdf' else row['context'].split(' / ')[-1] if row['book']=='SPATIAL_EFFECTS.pdf' else 'Vulnerability-first minus Hospital-first where effect is shown; executed policies unchanged'
    pd.DataFrame(PAGE_ROWS).to_csv(OUT/'PANEL_SOURCE_INDEX.csv',index=False)

if __name__=='__main__':
    before=protect_snapshot()
    index=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT)
    INDEX_SHA=hashlib.sha256(b'\n'.join(x for x in index.split(b'\0') if x)).hexdigest()
    print('Reading existing evidence',flush=True)
    d,effects,tract,definitions,measures,legacy,geo=load()
    if '--audit-only' in sys.argv:
        cover('All pairings among 23 saved primary outcomes','primary summaries',253,253,'ALL_METRIC_RELATIONSHIPS.pdf; explorer permits every context and reference')
        explorer(d,effects,tract,definitions,measures,legacy,geo)
        qa_and_docs(d,effects,tract,definitions,measures,before)
        sys.exit(0)
    if '--repair-layout' in sys.argv:
        pairs=list(itertools.combinations(METRICS,2))
        cover('All pairings among 23 saved primary outcomes','primary summaries',253,len(pairs),'ALL_METRIC_RELATIONSHIPS.pdf; explorer permits every context and reference')
        print('Repairing ONLY review layouts',flush=True);paired(effects);redistribution(d)
        spatial(tract,geo);grouping(definitions);measure_views(measures,definitions)
        explorer(d,effects,tract,definitions,measures,legacy,geo)
        qa_and_docs(d,effects,tract,definitions,measures,before)
        sys.exit(0)
    print('Building metric relationships',flush=True);relationships(d)
    print('Building saved matched effects',flush=True);paired(effects)
    print('Building quartile redistribution',flush=True);redistribution(d)
    print('Building ALL 68 saved spatial sets',flush=True);spatial(tract,geo)
    print('Building vulnerability-definition views',flush=True);grouping(definitions)
    print('Building measure/targeting evidence',flush=True);measure_views(measures,definitions)
    print('Embedding all raw rows into offline explorer',flush=True);explorer(d,effects,tract,definitions,measures,legacy,geo)
    print('Measuring and rendering actual PDF pages',flush=True);qa_and_docs(d,effects,tract,definitions,measures,before)
