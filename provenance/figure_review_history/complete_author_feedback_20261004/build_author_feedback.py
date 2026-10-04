"""Implement the four author feedback messages in existing review artwork.

Presentation only: reads saved outcomes, display curves, geometry and PDFs.
No simulation, sampling, scheduling, optimization, bootstrap or clustering.
The publication collection and historical artwork authorities are not written.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import shutil

import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BUNDLE = ROOT/'results/figure_review/final_submission_candidate_20261002'
MM = 72/25.4

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

h = load('feedback_pdf_tools', ROOT/'results/figure_review/supplement_author_feedback_20261004/build_supplement_feedback.py')
l = load('feedback_existing_layout', ROOT/'results/figure_review/candidate_v2.1_layout/build_layout_candidates.py')
v, base = l.v, l.base
h.OUT = OUT
HAZARD_COLORS = {'Long Beach':'#366E9F', 'San Fernando':'#00856A',
                 'Northridge':'#9a7559', '2pc50':'#a65628'}
l.HAZARD_COLORS = HAZARD_COLORS
h.HC = {key: HAZARD_COLORS[h.HN[key]] for key in h.HAZARDS}
KEYS = list(h.KEYS)
CORE = KEYS[:4]
COLOR, LINE, LABEL = h.COLOR, h.LINE, h.LABEL
MARKER = dict(zip(KEYS, ['s','o','^','D','v','P','X','x','']))
REFS = ['hospital-first','impact-first','degree-first']
CAPTIONS = {}
DISPLAY = []
INPUTS = {}

def track(path):
    path = Path(path)
    INPUTS[path.relative_to(ROOT).as_posix()] = h.sha(path)
    return path

def figure(height):
    return plt.figure(figsize=(185/25.4,height/25.4),facecolor='white')

def axbox(fig,x,top,width,height):
    total = fig.get_figheight()*25.4
    return fig.add_axes([x/185,(total-top-height)/total,width/185,height/total])

def heading(fig,x,top,text):
    fig.text(x/185,1-top/(fig.get_figheight()*25.4),text,ha='left',va='bottom',
             fontsize=9.5,fontweight='bold')

def handles(keys, lines=True):
    return [Line2D([],[],color=COLOR[k],ls=LINE[k] if lines else 'none',
            marker=MARKER[k],markersize=3.5,lw=1.45 if k in CORE else 1.0,
            markerfacecolor='white' if k=='degree-first' else COLOR[k],
            label=LABEL[k]) for k in keys]

def legend(fig, keys, top, x=105, columns=4, lines=True):
    # Matplotlib fills columns first; transpose to make the visible rows intentional.
    rows=int(np.ceil(len(keys)/columns))
    order=[keys[r*columns+c] for c in range(columns) for r in range(rows)
           if r*columns+c<len(keys)]
    lg=fig.legend(handles=handles(order,lines),frameon=False,ncol=columns,
        loc='upper center',bbox_to_anchor=(x/185,1-top/(fig.get_figheight()*25.4)),
        fontsize=7.5,handlelength=2,handletextpad=.4,columnspacing=1.2,
        labelspacing=.4,borderaxespad=0)
    for key,text in zip(order,lg.get_texts()):
        text.set_weight('bold' if key in CORE else 'normal')
    return lg

def summary(values):
    a=np.asarray(values,dtype=float)
    assert len(a)==1000 and np.isfinite(a).all()
    return float(np.mean(a)),*map(float,np.percentile(a,[5,95]))

def record(stem,panel,key,metric,mean,low,high,reference=''):
    DISPLAY.append(dict(figure=stem,panel=panel,strategy=key,metric=metric,
                        mean=mean,p5=low,p95=high,reference=reference,n=1000))

def outcomes():
    p=track(ROOT/'Formal_Experiment_20260923/Formal_Results/PRIMARY_REALIZATION_STRATEGY_SUMMARY.parquet')
    q=track(ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_PRIMARY_SUMMARY.parquet')
    d=pd.concat([pd.read_parquet(p),pd.read_parquet(q)],ignore_index=True)
    d=d[d.hazard.eq('2pc50') & d.mapping.eq('M1_UTILITY_003') &
        d.gate.eq('G1_BASELINE_050') & d.resource_scenario.eq('C57_D1') &
        d.strategy_id.isin(KEYS)].copy()
    assert len(d)==9000 and (d.groupby('strategy_id').realization_id.nunique()==1000).all()
    return d

def main02():
    def save(fig, stem):
        l.layout_02(fig); l.common_style(fig)
        for text in fig.texts:
            if text.get_text().startswith('A.'):
                text.set_text('A. Physical transmission network')
            elif text.get_text().startswith('B.'):
                text.set_text('B. Substation connection paths')
            elif text.get_text().startswith('C.'):
                text.set_text('C. Utility areas used in tract mapping')
            elif text.get_text().startswith('D.'):
                text.set_text('D. Comparison with SCE records')
        a,b,c,d=fig.axes[:4]
        for ax in [a,b]:
            for t in ax.get_legend().get_texts():
                t.set_text(t.get_text().replace('Retained grid stations','Substations')
                           .replace('Simplified topology','Substation paths'))
        for t in c.get_legend().get_texts():
            t.set_text(re.sub(r' \(n=\d+\)','',t.get_text())
                       .replace('Other/ambiguous; general pool','Other or uncertain utility'))
        d.set_yticklabels(['Any mapped\nsubstation','Highest-weight\nsubstation','Three highest-weight\nsubstations'])
        d.set_xlabel('Matches to SCE records (%)')
        for t in d.texts:
            t.set_fontsize(7.5)
        d.set_xlim(80,103)
        h.save(fig,'Fig02')
    old=v.save_figure;v.save_figure=save
    try:v.build_fig02()
    finally:v.save_figure=old
    CAPTIONS['Figure 2. System representation and tract-to-substation mapping']=(
        '(A) Physical transmission lines and substations from the California Energy Commission GIS data. '
        '(B) Substation-to-substation connection paths derived from that physical network. '
        'The geographic content of A and B is the original system representation. '
        '(C) Utility areas used to restrict tract-to-substation assignments to compatible utilities; '
        'tracts with other or uncertain utility assignment use the general candidate pool. '
        '(D) Comparison with public SCE substation records for 337 comparable tracts. '
        'A match means that at least one substation assigned to a tract is also in its public-record comparison set. '
        'The three tests use all positive-weight assigned substations, the highest-weight assigned substation, '
        'or the three highest-weight assigned substations. The distance-based baseline and utility-compatible '
        'mapping respectively match 320/337 and 329/337 tracts using all assignments, 296/337 and 302/337 '
        'using the highest-weight assignment, and 317/337 and 324/337 using the three highest-weight assignments. '
        'The separate 342-tract crosswalk is a different set: 316 tracts are shared, 26 occur only '
        'in that earlier set and 21 only in this 337-tract set; the denominators are not pooled. '
        'This agreement supports the mapping but is not feeder-level ground truth or validation of electricity delivery.')

def main03(data):
    decomp=pd.read_csv(track(h.SUITE/'Stage 3 Output_expanded/LOSS_DECOMPOSITION_ALL_DISTINCT_STRATEGIES.csv'))
    d=decomp[decomp.strategy_id.eq('unconstrained') & decomp.resource_scenario.eq('C57_D1')].set_index('hazard').loc[h.HAZARDS]
    def save(fig,stem):
        l.layout_03(fig); l.common_style(fig)
        a,b,c,hist,mp=fig.axes[:5]
        b.set_xlabel('Mean initial modeled tract\nservice availability')
        b.set_ylim(-.025,1.025)
        for i,line in enumerate(b.lines):
            line.set_marker(['o','s','^','D'][i]); line.set_markevery(260)
            line.set_markersize(2.4);line.set_markeredgewidth(.4)
        for text in fig.texts:
            if text.get_text().startswith('D.'):
                text.set_text('D. Time to 80% service')
            elif 'Mean tract T80' in text.get_text():
                text.set_text('E. Tract time to 80% service')
        hist.set_ylabel('2pc50 realizations')
        for t in list(c.texts):t.remove()
        colors=['#68757d','#8fb8c9','#d17b3f']
        c.set_xlim(0,40)
        shares=np.column_stack([1-d.source_fraction_of_mean_total-d.threshold_fraction_of_mean_total,
                                d.threshold_fraction_of_mean_total,d.source_fraction_of_mean_total])*100
        # All components receive the same annotation treatment; no selected share.
        for yy,row in enumerate(shares):
            for xx,val,color in zip([.855,.925,.995],row,['#4b5c67','#33728c','#a44d16']):
                c.text(xx,yy,f'{val:.1f}%',transform=c.get_yaxis_transform(),
                       ha='right',va='center',fontsize=7.5,color=color)
        for lg in fig.legends:
            for t in lg.get_texts():
                if t.get_text()=='Local physical damage':t.set_text('Substation damage')
        for i,hh in enumerate(h.HAZARDS):
            DISPLAY.append(dict(figure='Fig03',panel='C',hazard=hh,
                substation_share_pct=shares[i,0],threshold_share_pct=shares[i,1],source_share_pct=shares[i,2]))
        h.save(fig,'Fig03')
    old=v.save_figure;v.save_figure=save
    try:v.build_fig03(data)
    finally:v.save_figure=old
    CAPTIONS['Figure 3. Earthquake damage, service-loss mechanisms and unconstrained recovery']=(
        'Results for Long Beach, San Fernando, Northridge and 2pc50. '
        '(A) Substation mean damage states across saved realizations; box whiskers show the 5th–95th '
        'range across substations. (B) Distributions across tracts of mean initial modeled service availability. '
        '(C) Unconstrained population-weighted cumulative service loss over 0–480 h, decomposed into '
        'substation damage, the functionality threshold, and loss of a source path. The three percentages '
        'at the right of each row give these respective component shares of that row’s mean total loss, '
        'in legend order. No component is singled out for annotation. '
        '(D) Distribution of population-weighted time to 80% modeled service (T80) over the 1,000 '
        'saved physical realizations of 2pc50 under Unconstrained recovery. '
        '(E) Mean of realization-specific tract T80 values conditional on that tract reaching T80. '
        'A tract not reaching T80 does not contribute a finite T80 to that conditional mean; '
        'this is not the T80 of the mean recovery curve. T80 and cumulative service loss answer '
        'different questions: a threshold-crossing time versus an integral over the 480-h horizon. '
        'Historical hazards and 2pc50 use different fragility parameterizations and therefore are not '
        'a pure comparison of ground-motion intensity. Modeled service does not measure delivered electricity.')

def main04(data):
    fig=figure(210)
    a=axbox(fig,36,17,143,61)
    heading(fig,36,12,'A. Population-weighted service recovery')
    path=track(h.SUITE/'Stage 6 Output_expanded/ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv')
    curves=pd.read_csv(path)
    curves=curves[curves.hazard.eq('2pc50') & curves.strategy_id.isin(KEYS) & curves.time_hr.le(120)]
    for key in KEYS[::-1]:
        q=curves[curves.strategy_id.eq(key)].sort_values('time_hr')
        assert len(q)>0
        a.plot(q.time_hr,q.mean_population_availability_proxy,color=COLOR[key],ls=LINE[key],
            lw=1.45 if key in CORE else 1.2 if key=='unconstrained' else .85,
            alpha=1 if key in CORE or key=='unconstrained' else .70,
            marker=MARKER[key] or None,markersize=3 if key in CORE else 2.3,markevery=9 if key in CORE else 17,
            markeredgewidth=.45,markerfacecolor='white' if key=='degree-first' else COLOR[key],
            zorder=5 if key in CORE else 3)
    a.set(xlim=(0,100),ylim=(-.02,1.025),xlabel='Time after earthquake (h)',
          ylabel='Mean population-weighted\nmodeled service availability')
    a.grid(alpha=.2);a.set_axisbelow(True)
    legend(fig,CORE,91,columns=4)
    legend(fig,KEYS[4:],99,columns=3)
    heading(fig,36,123,'B. Cumulative service loss and recovery time')
    fig.text(36/185,1-128/210,'Dots: means; whiskers: 5th–95th realization ranges',fontsize=7.5,va='bottom')
    metrics=[('population_weighted_normalized_burden_hr','All tracts:\npopulation-weighted\nloss (h)'),
             ('burden_Q4_hr','Highest-vulnerability\nquartile loss (h)'),
             ('hospital_mean_normalized_burden_hr','Hospital-linked\ntract mean loss (h)'),
             ('L_source_population_mass_weighted_hr','Source-path\nloss (h)'),
             ('population_T80_hr','Time to 80%\nservice (h)')]
    for j,(metric,label) in enumerate(metrics):
        ax=axbox(fig,36+j*29,134,25,56)
        for yy,key in enumerate(KEYS):
            mean,low,high=summary(data.loc[data.strategy_id.eq(key),metric])
            record('Fig04','B',key,metric,mean,low,high)
            ax.errorbar(mean,yy,xerr=[[mean-low],[high-mean]],fmt=MARKER[key] or 'o',
                ms=3.3 if key in CORE else 2.8,color=COLOR[key],elinewidth=.8,capsize=1.5,
                markerfacecolor='white' if key=='degree-first' else COLOR[key],
                alpha=1 if key in CORE or key=='unconstrained' else .74)
        ax.set_yticks(range(9),[LABEL[k] for k in KEYS] if j==0 else [])
        ax.set_ylim(8.5,-.5);ax.set_xlabel(label,fontsize=7.5)
        ax.tick_params(axis='y',length=0);ax.locator_params(axis='x',nbins=3)
        ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    h.save(fig,'Fig04')
    CAPTIONS['Figure 4. Restoration priorities, community service loss and recovery time']=(
        '(A) Mean population-weighted modeled service availability under all eight scheduled policies '
        'and the Unconstrained reference for 2pc50 at the reference resource condition of 57 crews '
        'and repair-duration multiplier 1.00. Impact-first, Hospital-first, Degree-first and '
        'Vulnerability-first are emphasized using thicker lines and distinct markers; the other '
        'four scheduled policies remain visible. Only 0–100 h is shown, whereas service-loss integrals '
        'use the full 0–480 h evaluation horizon. Centrality-first is the policy that prioritizes '
        'the network λ2-impact metric; it is distinct from population-oriented Impact-first. '
        '(B) Means and 5th–95th realization ranges for population-weighted loss across all tracts, '
        'loss in the highest social-vulnerability quartile (Q4), equal-weight mean loss in hospital-linked '
        'tracts, source-path-related loss, and population-weighted time to 80% modeled service. '
        'Ranges describe 1,000 realization outcomes per policy, not confidence intervals. '
        'Cumulative service loss is the integral of one minus modeled service availability; '
        'hours therefore express unavailable-service time, not electricity consumption. '
        'Quartile loss is population-weighted within that quartile. Hospital-linked tract loss does '
        'not measure hospital electricity delivery or clinical capacity. T80 describes a threshold '
        'crossing and is not a duplicate of the cumulative-loss integral. Direct-community has the '
        'same sequence as Impact-first and is represented once.')

def matched(data,metric,ref):
    x=data[data.strategy_id.eq('vulnerability-first')][['realization_id',metric]].set_index('realization_id')
    y=data[data.strategy_id.eq(ref)][['realization_id',metric]].set_index('realization_id')
    assert x.index.is_unique and y.index.is_unique and set(x.index)==set(y.index)
    return (x[metric]-y[metric]).sort_index().to_numpy()

def main05(data):
    fig=figure(264)
    heading(fig,30,7,'A. Service loss across vulnerability quartiles')
    legend(fig,CORE,12,columns=4)
    a=axbox(fig,30,23,149,28)
    for k,key in enumerate(CORE):
        stats=np.array([summary(data.loc[data.strategy_id.eq(key),f'burden_Q{i}_hr']) for i in range(1,5)])
        xx=np.arange(1,5)+(k-1.5)*.07
        a.errorbar(xx,stats[:,0],yerr=[stats[:,0]-stats[:,1],stats[:,2]-stats[:,0]],
            color=COLOR[key],ls=LINE[key],marker=MARKER[key],ms=3.1,lw=1.2,
            markerfacecolor='white' if key=='degree-first' else COLOR[key],
            elinewidth=.8,capsize=1.6)
        for qi,(mean,low,high) in enumerate(stats,1):record('Fig05','A',key,f'burden_Q{qi}_hr',mean,low,high)
    a.set_xticks(range(1,5),['Q1 lowest','Q2','Q3','Q4 highest'])
    a.set(ylabel='Cumulative\nservice loss (h)',xlim=(.7,4.3));a.grid(axis='y',alpha=.2)
    heading(fig,30,63,'B. Overall loss and highest-vulnerability-group loss')
    legend(fig,KEYS[4:],68,columns=3,lines=False)
    b=axbox(fig,30,82,149,26)
    for key in KEYS:
        q=data[data.strategy_id.eq(key)]
        b.scatter(q.population_weighted_normalized_burden_hr.mean(),q.burden_Q4_hr.mean(),
            s=30 if key in CORE else 19,marker=MARKER[key] or 'o',
            facecolor='white' if key=='degree-first' else COLOR[key],edgecolor=COLOR[key],
            linewidth=.7,alpha=1 if key in CORE or key=='unconstrained' else .78,zorder=4 if key in CORE else 2)
    b.set(xlabel='All-tract population-weighted cumulative service loss (h)',
          ylabel='Q4 cumulative\nservice loss (h)');b.grid(alpha=.2)
    heading(fig,61,124,'C. Effects of vulnerability targeting')
    heading(fig,145,124,'D. Gini change')
    fig.text(61/185,1-128/264,'Compared with:',fontsize=7.5,va='top')
    lg=fig.legend(handles=handles(REFS,False),frameon=False,ncol=3,
        loc='upper left',bbox_to_anchor=(86/185,1-128/264),fontsize=7.5,
        handletextpad=.3,columnspacing=.7,borderaxespad=0)
    c=axbox(fig,61,138,70,34);g=axbox(fig,145,138,34,34)
    metrics=[('population_weighted_normalized_burden_hr','All tracts\n(population-weighted)'),
        ('burden_Q4_hr','Highest-vulnerability\nquartile (Q4)'),
        ('signed_Q4_minus_Q1_hr','Q4 relative to Q1\n(signed difference)'),
        ('absolute_Q4_minus_Q1_hr','Q4–Q1 separation\n(absolute difference)'),
        ('hospital_mean_normalized_burden_hr','Hospital-linked\ntract mean')]
    for i,(metric,label) in enumerate(metrics):
        for j,ref in enumerate(REFS):
            mean,low,high=summary(matched(data,metric,ref));record('Fig05','C','vulnerability-first',metric,mean,low,high,ref)
            c.errorbar(mean,i+(j-1)*.20,xerr=[[mean-low],[high-mean]],fmt=MARKER[ref],
                color=COLOR[ref],ms=3.2,elinewidth=.8,capsize=1.5,
                markerfacecolor='white' if ref=='degree-first' else COLOR[ref])
    c.set_yticks(range(5),[label for _,label in metrics]);c.set_ylim(4.6,-.6)
    c.set_xlabel('Change relative to reference (h)',fontsize=8)
    c.axvline(0,color='#333333',lw=.6,ls='--');c.grid(axis='x',alpha=.2)
    for j,ref in enumerate(REFS):
        mean,low,high=summary(matched(data,'burden_gini',ref));record('Fig05','D','vulnerability-first','burden_gini',mean,low,high,ref)
        g.errorbar(mean,j,xerr=[[mean-low],[high-mean]],fmt=MARKER[ref],color=COLOR[ref],
            ms=3.2,elinewidth=.8,capsize=1.5,markerfacecolor='white' if ref=='degree-first' else COLOR[ref])
    g.set_yticks(range(3),[LABEL[r].replace('-first','') for r in REFS],fontsize=7.5)
    g.set_ylim(2.5,-.5);g.axvline(0,color='#333333',lw=.6,ls='--');g.grid(axis='x',alpha=.2)
    g.set_xlabel('Change relative to\nreference (unitless)',fontsize=8)
    heading(fig,24,194,'E. Spatial effects of vulnerability targeting')
    fig.text(24/185,1-198/264,'Compared with Impact-first',fontsize=7.5,va='top')
    mp=axbox(fig,30,204,108,57)
    path=track(ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_TRACT_EFFECTS.parquet')
    te=pd.read_parquet(path);te=te[te.hazard.eq('2pc50') & te.reference_strategy.eq('impact-first')].copy()
    te['tract_id']=te.tract_id.astype(str).str.zfill(11)
    gm=base.projected_map_data(base.map_domain().merge(te[['tract_id','mean_paired_delta_burden_hr','population']],on='tract_id',validate='one_to_one'))
    assert gm.tract_id.nunique()==2315
    lim=max(float(np.max(np.abs(gm.mean_paired_delta_burden_hr))),.25)
    cmap=LinearSegmentedColormap.from_list('legible_tract_effect',['#225e99','#82b7d2','#dadada','#d6a2a0','#a83245'])
    norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim)
    gm.plot(column='mean_paired_delta_burden_hr',ax=mp,cmap=cmap,norm=norm,
        linewidth=.08,edgecolor='#a8a8a8',missing_kwds={'color':'#eeeeee'})
    base.style_map_axis(mp)
    cbax=axbox(fig,140,207,2.2,50)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cbax)
    cb.set_label('Mean tract service-loss change (h)',fontsize=7.5,labelpad=3)
    cb.ax.tick_params(labelsize=7.5,length=2);cb.outline.set_linewidth(.5)
    h.save(fig,'Fig05')
    CAPTIONS['Figure 5. Vulnerability-targeted restoration and distributional consequences']=(
        'Results under 2pc50 at the reference crew condition and repair-duration multiplier 1.00. '
        '(A) Population-weighted cumulative service loss within each social-vulnerability quartile '
        'for the four policies named directly above A. Q1 is the lowest and Q4 the highest vulnerability '
        'quartile. Dots are means and whiskers are 5th–95th realization ranges; these are neither '
        'boxplots, standard deviations nor confidence intervals. (B) Mean all-tract population-weighted '
        'loss versus mean Q4 loss for all eight scheduled policies and Unconstrained. B uses the four '
        'policy identities above A together with the five identities immediately above B. Points are '
        'summary estimates, not two-dimensional uncertainty regions. '
        '(C/D) Effects of Vulnerability-first compared with Hospital-first (gray circles), Impact-first '
        '(orange squares) and Degree-first (open green triangles). The comparison key above C/D applies '
        'only to C/D. Hospital-first and Impact-first are the primary reported references; Degree-first '
        'shows reference sensitivity. Every difference uses the same physical realization for the '
        'candidate and reference. Dots are means and whiskers are the 5th–95th range of these 1,000 '
        'matched differences, not bootstrap confidence intervals. '
        'C distinguishes the signed Q4-relative-to-Q1 difference from the per-realization absolute '
        'Q4–Q1 separation: the former retains direction and the latter measures between-group distance. '
        'Neither is interchangeable with D, the population-weighted Gini coefficient (0 means equal '
        'tract burden; larger values mean more unequal burden). D is unitless and uses its own labeled axis. '
        '(E) Tract mean matched loss changes relative to Impact-first, with negative values indicating '
        'less cumulative loss and positive values more loss. The map shows the sign and magnitude of '
        'mean effects, not statistical significance or per-realization benefited population. '
        'All cumulative-loss integrals cover 0–480 h. Hospital-linked loss is an equal-weight mean '
        'over hospital-linked tracts, not hospital delivery or clinical capacity. No policy is designated '
        'most equitable on the basis of one metric.')

def main07():
    # Preserve every native KDE path and the existing standardized profile values.
    source=track(ROOT/'results/figure_review/fig06_resource_redesign_20261002/Fig07_Author_Reviewed_Update.pdf')
    with fitz.open(source) as doc:
        p=doc[0];drawings=p.get_drawings()
        native=[draw for draw in drawings if draw.get('fill') and
                210<draw['rect'].x0<375 and 300<draw['rect'].y0<428 and
                29<draw['rect'].width<35 and 24.8<draw['rect'].height<25.1]
        cells={tuple(round(t,2) for t in draw['rect']):draw for draw in native[-30:]}
        assert len(cells)==30,(len(cells),list(cells)[:4])
        # Lighten only the numeric heatmap, never the cluster-ID category palette.
        for bounds,draw in cells.items():
            rgb=np.array(draw['fill']);rgb=.72*rgb+.28
            p.draw_rect(fitz.Rect(bounds),fill=tuple(rgb),color=None,overlay=True)
        ss=h.spans(p)
        for bounds in cells:
            selected=[s for _,s in ss if fitz.Rect(bounds).contains(fitz.Point(s['origin'])) and
                      re.fullmatch(r'[−-]?\d+\.\d+',h.plain(s['text']))]
            if selected:
                s=selected[-1]
                p.insert_font(fontname='ArialFeedback',fontfile=h.ARIAL)
                p.insert_text(s['origin'],h.plain(s['text']),fontsize=s['size'],fontname='ArialFeedback',color=(0,0,0))
        # Apply exactly the same lightening to the corresponding heatmap colorbar.
        bars=[i for i in p.get_image_info(xrefs=True) if
              384<i['bbox'][0]<386 and 301<i['bbox'][1]<303 and 450<i['bbox'][3]<453]
        assert len(bars)==1
        image=fitz.Pixmap(doc,bars[0]['xref'])
        if image.colorspace.n!=3:image=fitz.Pixmap(fitz.csRGB,image)
        samples=np.frombuffer(image.samples,dtype=np.uint8).reshape(image.height,image.width,image.n)
        cb=fitz.Rect(bars[0]['bbox'])
        # Exact source colorbar lookup, lightened identically to the heatmap.
        for row in range(image.height):
            rgb=.72*samples[row,image.width//2,:3].astype(float)/255+.28
            yy=cb.y0+row*cb.height/image.height
            p.draw_rect(fitz.Rect(cb.x0,yy,cb.x1,yy+cb.height/image.height),
                        color=None,fill=tuple(rgb),overlay=True)
        top=OUT/'Fig07_Top_Native.pdf'
        doc.save(top,garbage=4,deflate=True)
    # Same full-domain maps and memberships, with a quieter top-ten outline.
    authority=load('feedback_native_cluster',ROOT/'results/figure_review/fig06_resource_redesign_20261002/author_feedback_fig06_fig07.py')
    authority.OUT=OUT
    # The renderer is presentation-only; use its exact existing geometry and palette.
    map_pdf=authority.redraw_maps(v,OUT/'map.pdf')
    with fitz.open(map_pdf) as maps:
        page=maps[0]
        for xref in page.get_contents():
            stream=maps.xref_stream(xref)
            stream=re.sub(rb'(?<![\d.])0\.4 w',b'0.25 w',stream)
            maps.update_stream(xref,stream)
        quiet=OUT/'Fig07_Map_Panels.pdf';maps.save(quiet,garbage=4,deflate=True)
    with fitz.open(top) as old,fitz.open(quiet) as maps:
        doc=fitz.open();p=doc.new_page(width=185*MM,height=242*MM)
        p.show_pdf_page(fitz.Rect(0,0,185*MM,166*MM),old,0,clip=fitz.Rect(0,0,185*MM,166*MM),keep_proportion=False)
        p.show_pdf_page(fitz.Rect(0,167*MM,185*MM,242*MM),maps,0)
        p.insert_font(fontname='ArialBoldFeedback',fontfile=h.BOLD)
        for x,text in [(9,'C. Cluster membership'),(94,'D. Hotspot score')]:
            p.insert_text((x*MM,166*MM),text,fontsize=9.5,fontname='ArialBoldFeedback')
        path=OUT/'Fig07.pdf';doc.save(path,garbage=4,deflate=True);doc.close()
    h.export(path)

def supplements():
    h.style();h.s01()
    # Same source/quantity coding in S04; strengthen the four policy identities.
    original=h.save
    def emit(fig,stem):
        if stem=='FigS04':
            for lg in list(fig.legends):lg.remove()
            legend(fig,CORE,57.5,columns=4)
            legend(fig,KEYS[4:],64.5,columns=3)
            for ax in fig.axes[1:]:
                for key,line in zip(KEYS,ax.lines):
                    line.set_marker(MARKER[key])
                    line.set_markevery(10);line.set_markersize(2.6)
                    line.set_markerfacecolor('white' if key=='degree-first' else COLOR[key])
        elif stem=='FigS07':
            for lg in list(fig.legends):
                if len(lg.get_texts())==8:lg.remove()
            legend(fig,CORE,112.5,columns=4)
            legend(fig,KEYS[4:-1],119.5,columns=4)
            for i,ax in enumerate(fig.axes[:2]):
                if i==1:
                    for key,line in zip(KEYS[:-1],ax.lines):
                        line.set_marker(MARKER[key]);line.set_markevery(9)
                        line.set_markersize(2.8 if key in CORE else 2)
                        line.set_markerfacecolor('white' if key=='degree-first' else COLOR[key])
                        line.set_alpha(1 if key in CORE else .75)
                else:
                    for line in ax.lines:line.set_markevery(9)
            for ax in fig.axes:
                if 'Conditional source reachability' in ax.get_title() or 'Reliability gain' in ax.get_title():
                    for coll in ax.collections:
                        if len(coll.get_offsets())==78:
                            name='Blues' if 'Conditional' in ax.get_title() else 'Reds'
                            coll.set_cmap(LinearSegmentedColormap.from_list('legible_'+name,
                                plt.get_cmap(name)(np.linspace(.42,1,256))))
        elif stem=='FigS08':
            b=fig.axes[1]
            for key,line in zip(['impact-first','hospital-first','vulnerability-first','degree-first'],b.lines):
                line.set_marker(MARKER[key])
                line.set_markerfacecolor('white' if key=='degree-first' else COLOR[key])
            b.set_title('B. Service loss added by the SCE planning bound',loc='left',fontweight='bold')
            b.set_xlabel('Increase relative to the source-connected model\n(h; expanded scale)',fontsize=8.5)
        return original(fig,stem)
    h.save=emit
    meeting=h.load('feedback_supplement_input_geometry',ROOT/'src/la_grid/plotting/build_meeting_figure_collection.py')
    try:
        h.s04();h.s06(meeting);h.s07(meeting);h.s08()
    finally:h.save=original
    # Text-only replacement: all comparison coordinates and percentages are retained.
    p=OUT/'FigS06.pdf';tmp=OUT/'FigS06_Wording.pdf'
    h.edit_text(p,tmp,lambda s,line,page:
        {'text':'B. Comparison with SCE records'} if h.plain(s['text'])=='B. Match to public SCE sites'
        else {'text':'Matches to SCE records (%)'} if 'Public-site' in s['text'] or 'public-site evidence (%)' in s['text'] else None)
    shutil.move(tmp,p);h.export(p)

def update_package():
    stems=['Fig02','Fig03','Fig04','Fig05','Fig07','FigS01','FigS04','FigS06','FigS07','FigS08']
    md=(BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    for num,body in h.CAPTIONS.items():
        if num in {'S1','S4','S6','S7','S8'}:
            CAPTIONS['Supplementary Figure '+num]=body.replace('public-site candidate set','public SCE substation-record set').replace('public-site agreement','agreement with SCE records')
    for heading,body in CAPTIONS.items():
        prefix=heading.split('.')[0]
        pat=r'(?ms)(^## '+re.escape(prefix)+r'\.[^\n]*\n\n).*?(?=^## |\Z)'
        def replacement(match):
            actual='## '+heading+'\n\n' if '. ' in heading else match.group(1)
            return actual+body+'\n\n'
        md,n=re.subn(pat,replacement,md);assert n==1,heading
    # Provider's official metric name, with the source vintage unchanged.
    md=md.replace('FEMA NRI Social Vulnerability Score','Social Vulnerability Score (National Risk Index)')
    (BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').write_text(md.rstrip()+'\n',encoding='utf-8')
    m=pd.read_csv(BUNDLE/'FIGURE_MANIFEST.csv',dtype=str).fillna('')
    for stem in stems:
        for ext in ['.pdf','.png']:
            src=OUT/(stem+ext);dest=BUNDLE/('Supplement' if stem.startswith('FigS') else 'Main')/(stem+ext)
            shutil.copyfile(src,dest);assert h.sha(src)==h.sha(dest)
            with fitz.open(OUT/(stem+'.pdf')) as doc:
                p=doc[0];minimum=min(s['size'] for _,s in h.spans(p))
                size=f'{p.rect.width/MM:.3f} x {p.rect.height/MM:.3f}'
            idx=m.index[m.final_name.eq(dest.relative_to(BUNDLE).as_posix())];assert len(idx)==1
            m.loc[idx[0],['source_file','source_commit','sha256','size_mm','min_font_pt','status']]=[
                src.relative_to(ROOT).as_posix(),'ARTWORK_COMMIT_PENDING',h.sha(dest),size,str(minimum),'AUTHOR_REVIEW_UPDATE_NOT_PROMOTED']
    m.to_csv(BUNDLE/'FIGURE_MANIFEST.csv',index=False)
    main=[BUNDLE/f'Main/Fig{i:02d}.pdf' for i in range(1,8)]
    supp=[BUNDLE/f'Supplement/FigS{i:02d}.pdf' for i in range(1,14)]
    for name,paths in [('ALL_MAIN_FIGURES.pdf',main),('ALL_SUPPLEMENT_FIGURES.pdf',supp)]:
        book=fitz.open()
        for path in paths:
            with fitz.open(path) as src:book.insert_pdf(src)
        book.save(BUNDLE/name,garbage=4,deflate=True);book.close()
    matches=list(re.finditer(r'(?m)^## (.+)\n\n',md));caps={}
    for i,match in enumerate(matches):
        title=match.group(1);body=md[match.end():matches[i+1].start() if i+1<len(matches) else len(md)].strip()
        if title.startswith('Figure '):key=f"Main/Fig{int(title.split('.')[0].replace('Figure ','')):02d}.pdf"
        elif title.startswith('Supplementary Figure S'):key=f"Supplement/FigS{int(title.split('.')[0].replace('Supplementary Figure S','')):02d}.pdf"
        else:continue
        caps[key]=(title,body)
    book=fitz.open()
    for path in main+supp:
        with fitz.open(path) as src:book.insert_pdf(src)
        title,body=caps[path.relative_to(BUNDLE).as_posix()]
        p=book.new_page(width=185*MM,height=350*MM)
        p.insert_font(fontname='ArialPacket',fontfile=h.ARIAL)
        p.insert_font(fontname='ArialPacketBold',fontfile=h.BOLD)
        p.insert_text((14*MM,20*MM),title,fontname='ArialPacketBold',fontsize=9.5)
        assert p.insert_textbox(fitz.Rect(14*MM,29*MM,171*MM,333*MM),body,
            fontname='ArialPacket',fontsize=9.2,lineheight=1.22)>=0,title
    assert len(book)==40
    book.save(BUNDLE/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()
    return stems

def main():
    OUT.mkdir(exist_ok=True)
    guard_path=OUT/'BEFORE_HASH_GUARD.json'
    if not guard_path.exists():
        old=json.loads((ROOT/'results/figure_review/promotion_readiness_4a4e9b5/READ_ONLY_GUARD.json').read_text())
        science={p:h.sha(ROOT/p) for p in old['scientific_hashes']}
        publication={p.relative_to(ROOT).as_posix():h.sha(p) for p in (ROOT/'results/figures').glob('*') if p.is_file()}
        protected={p.relative_to(ROOT).as_posix():h.sha(p) for folder in ['Main','Supplement']
            for p in (BUNDLE/folder).glob('*') if p.is_file() and p.stem in
            ['Fig01','Fig06','FigS02','FigS03','FigS05','FigS09','FigS10','FigS11','FigS12','FigS13']}
        guard_path.write_text(json.dumps(dict(science=science,publication=publication,protected_artwork=protected),indent=2))
    h.style();data=outcomes()
    for name,operation in [('Fig02',main02),('Fig03',lambda:main03(data)),
        ('Fig04',lambda:main04(data)),('Fig05',lambda:main05(data)),('Fig07',main07),('supplements',supplements)]:
        print('Rendering '+name,flush=True);operation()
    stems=update_package()
    guard=json.loads(guard_path.read_text())
    for category,paths in guard.items():assert all(h.sha(ROOT/p)==sha for p,sha in paths.items()),category
    assert all(h.sha(ROOT/p)==sha for p,sha in INPUTS.items())
    assert all(h.sha(ROOT/p)==sha for p,sha in h.INPUT_HASHES.items())
    pd.DataFrame(DISPLAY).to_csv(OUT/'DISPLAYED_VALUES.csv',index=False)
    pd.DataFrame(h.QA).drop_duplicates('file',keep='last').to_csv(OUT/'OUTPUT_QA.csv',index=False)
    (OUT/'READ_INPUT_HASHES.json').write_text(json.dumps({**INPUTS,**h.INPUT_HASHES},indent=2))
    print(json.dumps(dict(updated=stems,scientific_hash_changes=0,publication_hash_changes=0,
                         protected_artwork_changes=0,qa=h.QA),indent=2),flush=True)

if __name__=='__main__':main()
