"""Apply the author's readability corrections to saved review artwork.

Only display curves, saved outcomes, saved matched effects and native PDFs
are read. No simulation, scheduling, sampling, clustering or bootstrap runs.
"""
from pathlib import Path
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
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
BUNDLE=ROOT/'results/figure_review/final_submission_candidate_20261002'
MM=72/25.4

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

p=load('previous_author_display',ROOT/'results/figure_review/complete_author_feedback_20261004/build_author_feedback.py')
h,l,v,base=p.h,p.l,p.v,p.base
h.OUT=OUT
KEYS,CORE,COLOR,LINE,LABEL,REFS=p.KEYS,p.CORE,p.COLOR,p.LINE,p.LABEL,p.REFS
CAPTIONS={}
STEMS=['Fig03','Fig04','Fig05','Fig06','Fig07','FigS09','FigS12']
JULY_CLUSTER=['#303E4E','#C0A55B','#567E58','#BAD1DB','#724B63']
OLD_CLUSTER=['#0072B2','#E69F00','#009E73','#56B4E9','#CC79A7']
p.MARKER['unconstrained']='o'

def frozen_copy(relative):
    recorded=subprocess.check_output(['git','show','a0f60c1116976fe34cf05aabc840734914fa7df7:'+relative],cwd=ROOT)
    oid=re.search(rb'oid sha256:([0-9a-f]{64})',recorded)
    assert oid,relative
    oid=oid.group(1).decode()
    equivalents={
        'results/figure_review/final_submission_candidate_20261002/Supplement/FigS09.pdf':
            'results/figure_review/fig06_resource_redesign_20261002/FigS09_Cluster_Palette_Author_Update.pdf',
        'results/figure_review/final_submission_candidate_20261002/Supplement/FigS12.pdf':
            'results/figure_review/hospital_resource_author_feedback_20261004/FigS12.pdf',
    }
    if relative in equivalents:
        location=p.track(ROOT/equivalents[relative])
        assert h.sha(location)==oid,relative
        return location
    environment=subprocess.check_output(['git','lfs','env'],cwd=ROOT,text=True)
    media=Path(re.search(r'(?m)^LocalMediaDir=(.+)$',environment).group(1).strip())
    if not media.is_absolute():media=ROOT/media
    location=media/oid[:2]/oid[2:4]/oid
    assert h.sha(location)==oid,relative
    return location

def guard():
    path=OUT/'BEFORE_HASH_GUARD.json'
    if path.exists():return json.loads(path.read_text())
    before=json.loads((ROOT/'results/figure_review/promotion_readiness_4a4e9b5/READ_ONLY_GUARD.json').read_text())
    result={
        'science':{k:h.sha(ROOT/k) for k in before['scientific_hashes']},
        'publication':{x.relative_to(ROOT).as_posix():h.sha(x) for x in (ROOT/'results/figures').glob('*') if x.is_file()},
        'protected_artwork':{x.relative_to(ROOT).as_posix():h.sha(x) for folder in ['Main','Supplement']
            for x in (BUNDLE/folder).glob('*') if x.is_file() and x.stem not in STEMS},
    }
    path.write_text(json.dumps(result,indent=2))
    return result

def reference_key(fig,top,height):
    fig.text(28/185,1-top/height,'Vulnerability-first compared with:',fontsize=7.5,va='top')
    handles=[Line2D([],[],color=COLOR[r],marker=p.MARKER[r],ls='none',ms=3.8,
             mfc='white' if r=='degree-first' else COLOR[r],label=LABEL[r]) for r in REFS]
    fig.legend(handles=handles,frameon=False,ncol=3,fontsize=7.5,
        loc='upper left',bbox_to_anchor=(86/185,1-top/height),handletextpad=.25,
        columnspacing=.8,borderaxespad=0)

def fig03(data):
    original=h.save
    def emit(fig,stem):
        for line in fig.axes[1].lines:
            line.set_linestyle('-');line.set_marker('');line.set_linewidth(1.2)
        fig.axes[2].set_xlabel('Population-weighted modeled service loss (h)')
        for text in fig.texts:
            if text.get_text().startswith('D.'):text.set_text('D. Population-weighted T80')
            elif text.get_text().startswith('E.'):text.set_text('E. Mean tract T80')
        fig.axes[3].set_xlabel('Population-weighted T80 (h)')
        for ax in fig.axes[5:]:
            if 'T80' in ax.get_ylabel():ax.set_ylabel('Mean tract T80 (h)')
        # One solid-line hazard identity; all scenarios have equal emphasis.
        for legend in fig.legends:
            for handle in legend.legend_handles:
                if isinstance(handle,Line2D):handle.set_linestyle('-');handle.set_marker('')
        hazard_key=fig.axes[1].get_legend()
        if hazard_key:
            for handle in hazard_key.legend_handles:
                if isinstance(handle,Line2D):handle.set_linestyle('-');handle.set_marker('')
        return original(fig,stem)
    h.save=emit
    try:p.main03(data)
    finally:h.save=original
    CAPTIONS.update(p.CAPTIONS)
    body=CAPTIONS['Figure 3. Earthquake damage, service-loss mechanisms and unconstrained recovery']
    CAPTIONS['Figure 3. Earthquake damage, service-loss mechanisms and unconstrained recovery']=body.replace(
        '(D) Distribution of population-weighted time to 80% modeled service (T80)',
        'T80 is the time after the earthquake at which modeled service first reaches 80%. '
        '(D) Distribution of population-weighted T80')

def policy_legend(fig):
    prominent=CORE+['unconstrained']
    secondary=[k for k in KEYS if k not in prominent]
    for keys,top,cols in [(prominent,91,3),(secondary,105,4)]:
        handles=[Line2D([],[],color=COLOR[k],ls=LINE[k],lw=1.5 if k in prominent else .8,
            alpha=1 if k in prominent else .38,label=LABEL[k]) for k in keys]
        leg=fig.legend(handles=handles,frameon=False,ncol=cols,fontsize=7.5,
            loc='upper center',bbox_to_anchor=(105/185,1-top/212),
            handlelength=2.4,columnspacing=1,handletextpad=.4,labelspacing=.5)
        for k,t in zip(keys,leg.get_texts()):t.set_weight('bold' if k in prominent else 'normal')

def fig04(data):
    fig=p.figure(212);a=p.axbox(fig,36,17,143,61)
    p.heading(fig,36,12,'A. Population-weighted service recovery')
    source=p.track(h.SUITE/'Stage 6 Output_expanded/ALL_DISTINCT_STRATEGY_RECOVERY_CURVES.csv')
    curves=pd.read_csv(source)
    curves=curves[curves.hazard.eq('2pc50') & curves.strategy_id.isin(KEYS) & curves.time_hr.le(100)]
    prominent=CORE+['unconstrained']
    for key in [k for k in KEYS if k not in prominent]+prominent:
        q=curves[curves.strategy_id.eq(key)].sort_values('time_hr')
        a.plot(q.time_hr,q.mean_population_availability_proxy,color=COLOR[key],ls=LINE[key],
            lw=1.5 if key in prominent else .75,alpha=1 if key in prominent else .25,
            zorder=5 if key in prominent else 2)
    a.set(xlim=(0,100),ylim=(-.02,1.025),xlabel='Time after earthquake (h)',
        ylabel='Mean population-weighted\nmodeled service availability')
    a.grid(alpha=.2);a.set_axisbelow(True);policy_legend(fig)
    p.heading(fig,36,127,'B. Service loss and recovery time')
    fig.text(36/185,1-132/212,'Means and 5th–95th realization ranges',fontsize=7.5,va='bottom')
    metrics=[('population_weighted_normalized_burden_hr','All tracts:\npopulation-weighted\nservice loss (h)'),
        ('burden_Q4_hr','Highest-vulnerability\nquartile service\nloss (h)'),
        ('hospital_mean_normalized_burden_hr','Hospital-linked\ntract mean service\nloss (h)'),
        ('population_T80_hr','Population-weighted\nT80 (h)')]
    for j,(metric,title) in enumerate(metrics):
        ax=p.axbox(fig,36+j*36.5,140,31,51)
        for yy,key in enumerate(KEYS):
            mean,low,high=p.summary(data.loc[data.strategy_id.eq(key),metric])
            p.record('Fig04','B',key,metric,mean,low,high)
            ax.errorbar(mean,yy,xerr=[[mean-low],[high-mean]],fmt='o',
                ms=3.4 if key in prominent else 2.0,color=COLOR[key],
                elinewidth=.85 if key in prominent else .5,capsize=1.4 if key in prominent else 0,
                alpha=1 if key in prominent else .27,zorder=5 if key in prominent else 2)
        ax.set_yticks(range(9),[LABEL[k] for k in KEYS] if j==0 else [])
        for k,t in zip(KEYS,ax.get_yticklabels()):t.set_weight('bold' if k in prominent else 'normal')
        ax.set_ylim(8.5,-.5);ax.set_xlabel(title,fontsize=7.5)
        ax.tick_params(axis='y',length=0);ax.locator_params(axis='x',nbins=3)
        ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    h.save(fig,'Fig04')
    CAPTIONS['Figure 4. Restoration priorities, community service loss and recovery time']=(
        '(A) Mean population-weighted modeled service availability for all eight scheduled policies '
        'and Unconstrained under 2pc50 at the reference resource condition. Impact-first, Hospital-first, '
        'Degree-first, Vulnerability-first and Unconstrained use stronger strokes; the remaining policies '
        'remain visible with lower opacity. No decorative point markers are superposed on recovery curves. '
        'Only 0–100 h is displayed. (B) Means and 5th–95th realization ranges for population-weighted '
        'service loss over all tracts, population-weighted service loss within the highest social-vulnerability '
        'quartile (Q4), equal-weight mean service loss in hospital-linked tracts, and population-weighted T80. '
        'All policies use 1,000 matched physical realizations; the ranges are outcome ranges, not confidence '
        'intervals. Service loss in hours is the integral of one minus modeled service availability over '
        '0–480 h: for example, 0.5 availability for 2 h contributes 1 unavailable-service hour. It is not '
        'instantaneous loss, an electricity quantity or a clinical-capacity estimate. T80 is the time to '
        '80% modeled service and does not duplicate the loss integral. Source-path loss decomposition '
        'is presented in Figure 3 and source diagnostics, rather than as another community outcome here. '
        'Centrality-first prioritizes the network lambda2-impact metric; Impact-first prioritizes mapped '
        'population impact. These remain distinct policies. Direct-community is sequence-equivalent to '
        'Impact-first and is reported once.')

def fig05(data):
    height=295;fig=p.figure(height)
    p.heading(fig,30,7,'A. Overall and highest-vulnerability service loss')
    # An ordered key for A only: emphasized policies first, then other policies.
    p.legend(fig,CORE,12,columns=4,lines=False)
    p.legend(fig,['unconstrained']+KEYS[4:8],24,columns=5,lines=False)
    a=p.axbox(fig,30,39,149,31)
    for key in KEYS:
        q=data[data.strategy_id.eq(key)];prominent=key in CORE or key=='unconstrained'
        a.scatter(q.population_weighted_normalized_burden_hr.mean(),q.burden_Q4_hr.mean(),
            s=29 if prominent else 15,marker=p.MARKER[key] or 'o',
            facecolor='white' if key=='degree-first' else COLOR[key],edgecolor=COLOR[key],
            linewidth=.7,alpha=1 if prominent else .38,zorder=5 if prominent else 2)
    a.set(xlabel='All-tract population-weighted service loss (h)',
        ylabel='Highest-vulnerability\nquartile service loss (h)');a.grid(alpha=.2)
    # Preserve the full true mean scale, including Unconstrained; no axis truncation.
    p.heading(fig,30,84,'B. Service loss across vulnerability quartiles')
    p.legend(fig,CORE,89,columns=4)
    b=p.axbox(fig,30,100,149,29)
    for k,key in enumerate(CORE):
        stats=np.array([p.summary(data.loc[data.strategy_id.eq(key),f'burden_Q{i}_hr']) for i in range(1,5)])
        b.errorbar(np.arange(1,5)+(k-1.5)*.075,stats[:,0],
            yerr=[stats[:,0]-stats[:,1],stats[:,2]-stats[:,0]],color=COLOR[key],
            ls=LINE[key],marker=p.MARKER[key],ms=3.1,lw=1.2,elinewidth=.8,capsize=1.5,
            markerfacecolor='white' if key=='degree-first' else COLOR[key])
        for qi,(mean,lo,hi) in enumerate(stats,1):p.record('Fig05','B',key,f'burden_Q{qi}_hr',mean,lo,hi)
    b.set_xticks(range(1,5),['Q1 lowest','Q2','Q3','Q4 highest'])
    b.set(ylabel='Population-weighted\nservice loss (h)',xlim=(.7,4.3));b.grid(axis='y',alpha=.2)
    p.heading(fig,55,145,'C. Vulnerability-first service-loss changes')
    p.heading(fig,144,145,'D. Gini change')
    reference_key(fig,151,height)
    c=p.axbox(fig,55,162,73,34);g=p.axbox(fig,147,162,32,34)
    metrics=[('population_weighted_normalized_burden_hr','All tracts\n(population-weighted)'),
        ('burden_Q4_hr','Highest-vulnerability\nquartile (Q4)'),
        ('absolute_Q4_minus_Q1_hr','Absolute Q4–Q1\nseparation'),
        ('hospital_mean_normalized_burden_hr','Hospital-linked\ntract mean')]
    for i,(metric,label) in enumerate(metrics):
        for j,ref in enumerate(REFS):
            mean,lo,hi=p.summary(p.matched(data,metric,ref));p.record('Fig05','C','vulnerability-first',metric,mean,lo,hi,ref)
            c.errorbar(mean,i+(j-1)*.20,xerr=[[mean-lo],[hi-mean]],fmt=p.MARKER[ref],
                color=COLOR[ref],ms=3.2,elinewidth=.8,capsize=1.5,
                markerfacecolor='white' if ref=='degree-first' else COLOR[ref])
    c.set_yticks(range(4),[s for _,s in metrics]);c.set_ylim(3.6,-.6)
    c.set_xlabel('Vulnerability-first service-loss change (h)',fontsize=7.5)
    c.axvline(0,color='#333333',lw=.6,ls='--');c.grid(axis='x',alpha=.2)
    for j,ref in enumerate(REFS):
        mean,lo,hi=p.summary(p.matched(data,'burden_gini',ref));p.record('Fig05','D','vulnerability-first','burden_gini',mean,lo,hi,ref)
        g.errorbar(mean,j,xerr=[[mean-lo],[hi-mean]],fmt=p.MARKER[ref],color=COLOR[ref],
            ms=3.2,elinewidth=.8,capsize=1.5,markerfacecolor='white' if ref=='degree-first' else COLOR[ref])
    g.set_yticks(range(3),[LABEL[r].replace('-first','') for r in REFS],fontsize=7.5)
    g.set_ylim(2.5,-.5);g.axvline(0,color='#333333',lw=.6,ls='--');g.grid(axis='x',alpha=.2)
    g.set_xlabel('Vulnerability-first\nGini change',fontsize=7.5)
    p.heading(fig,9,216,'E. Spatial service-loss changes under Vulnerability-first')
    path=p.track(ROOT/'Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_TRACT_EFFECTS.parquet')
    te=pd.read_parquet(path);te=te[te.hazard.eq('2pc50')&te.reference_strategy.isin(REFS)].copy()
    te['tract_id']=te.tract_id.astype(str).str.zfill(11)
    lim=max(float(te.mean_paired_delta_burden_hr.abs().max()),.25)
    cmap=LinearSegmentedColormap.from_list('muted_tract_effect',
        ['#296860','#8cb8ae','#ece4ce','#c89b63','#85572f'])
    norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim)
    for j,ref in enumerate(REFS[:2]):
        mp=p.axbox(fig,5+j*90,225,83,51)
        gm=base.projected_map_data(base.map_domain().merge(
            te.loc[te.reference_strategy.eq(ref),['tract_id','mean_paired_delta_burden_hr']],
            on='tract_id',validate='one_to_one'))
        assert gm.tract_id.nunique()==2315
        gm.plot(column='mean_paired_delta_burden_hr',ax=mp,cmap=cmap,norm=norm,
            linewidth=.08,edgecolor='#98998f',missing_kwds={'color':'#eeeeee'})
        base.style_map_axis(mp);mp.set_title('Compared with '+LABEL[ref],fontsize=7.5,pad=2)
    cbax=p.axbox(fig,48,282,90,1.6)
    cb=fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),cax=cbax,orientation='horizontal')
    cb.set_label('Mean tract service-loss change (h)',fontsize=7.5,labelpad=1)
    cb.ax.tick_params(labelsize=7.5,length=2);cb.outline.set_linewidth(.5)
    h.save(fig,'Fig05')
    CAPTIONS['Figure 5. Vulnerability-targeted restoration and distributional consequences']=(
        'Results for 2pc50 at the reference crew condition and repair-duration multiplier 1.00. '
        '(A) Mean population-weighted service loss across all tracts versus mean loss within Q4 for '
        'all eight scheduled policies and Unconstrained. The ordered key above A applies to A only. '
        'Points are mean outcomes, not two-dimensional uncertainty regions. '
        '(B) Population-weighted service loss within Q1–Q4 for the four policies named above B; '
        'Q1 is the lowest and Q4 the highest social-vulnerability quartile. Dots are means and whiskers '
        'are 5th–95th realization ranges, not boxplots, standard deviations or confidence intervals. '
        '(C/D) Vulnerability-first compared with Hospital-first (gray circles), Impact-first '
        '(orange squares) and Degree-first (open green triangles), as identified in the common C/D '
        'comparison key. Each reference is a different comparison, not a Vulnerability-first variant. '
        'C reports service-loss changes in all tracts, Q4, absolute Q4–Q1 separation and hospital-linked '
        'tracts, in that order. D reports changes in the population-weighted Gini coefficient on its '
        'own dimensionless axis. A Gini of 0 represents equal tract loss; larger values mean more '
        'unequal tract loss. Negative change means a lower value under Vulnerability-first. '
        'Means and 5th–95th ranges use 1,000 differences between outcomes under the same physical '
        'realization; they are not bootstrap confidence intervals. Hospital-first and Impact-first '
        'are the primary reported references; Degree-first provides reference sensitivity. '
        'Absolute Q4–Q1 separation is the absolute value of the quartile difference within each '
        'realization, then summarized. It measures distance, not direction. The signed Q4–Q1 '
        'difference preserves which quartile has more loss and is retained in the companion review '
        'evidence; the mean absolute difference is not generally the absolute difference of means. '
        '(E) Mean matched tract-level service-loss changes compared with Hospital-first and '
        'Impact-first, the two references with saved tract-level effect tables, using identical '
        'map extent and a common symmetric color scale. A Degree-first map is not available in '
        'the saved tract-effect tables; its summary comparisons remain visible in C/D. Teal indicates '
        'less loss and brown more loss under Vulnerability-first; the neutral tint marks values near '
        'zero. These maps show mean effects, not statistical significance or per-realization '
        'benefited population. Service loss integrates one minus modeled service availability over '
        '0–480 h. Hospital-linked tract loss is an equal-weight tract mean, not hospital electricity '
        'delivery or clinical capacity. No one metric establishes a most-equitable policy.')

def signed_companion(data):
    fig=p.figure(83);a=p.axbox(fig,62,16,115,43)
    p.heading(fig,12,7,'Signed and absolute Q4–Q1 differences answer different questions')
    for i,(metric,label) in enumerate([('signed_Q4_minus_Q1_hr','Signed Q4–Q1 difference'),
            ('absolute_Q4_minus_Q1_hr','Absolute Q4–Q1 separation')]):
        for j,ref in enumerate(REFS):
            mean,lo,hi=p.summary(p.matched(data,metric,ref))
            p.record('Q4_Q1_Definition_Companion','A','vulnerability-first',metric,mean,lo,hi,ref)
            a.errorbar(mean,i+(j-1)*.17,xerr=[[mean-lo],[hi-mean]],fmt=p.MARKER[ref],
                color=COLOR[ref],ms=3.5,elinewidth=.8,capsize=1.6)
    a.set_yticks([0,1],['Signed Q4–Q1\ndifference','Absolute Q4–Q1\nseparation'])
    a.set_ylim(1.5,-.5);a.axvline(0,color='#444444',ls='--',lw=.6)
    a.set_xlabel('Vulnerability-first change relative to named policy (h)');a.grid(axis='x',alpha=.2)
    fig.legend(handles=p.handles(REFS,False),frameon=False,ncol=3,fontsize=7.5,
        loc='lower center',bbox_to_anchor=(.62,.025))
    h.save(fig,'Q4_Q1_Definition_Companion')

def fig06():
    r=load('saved_resource_display',ROOT/'results/figure_review/hospital_resource_author_feedback_20261004/build_hospital_resource_feedback.py')
    r.helper.OUT=OUT
    source=p.track(ROOT/'results/figure_review/hospital_resource_author_feedback_20261004/FIG06_DISPLAYED_ROWS.csv')
    data=pd.read_csv(source)
    r.METRICS=[r.METRICS[1],r.METRICS[0],r.METRICS[2],r.METRICS[3]]
    original=r.helper.save
    def save(fig,stem):
        titles=['All tracts, population-weighted','Highest-vulnerability quartile',
                'Absolute Q4–Q1 separation','Hospital-linked tract mean']
        for i,ax in enumerate(fig.axes):
            row,col=divmod(i,2)
            ax.set_title(f'{chr(65+i)}. {titles[row]}',loc='left',fontsize=8.5,fontweight='bold',pad=5)
            if col==0:
                ax.set_xticks(range(4),['0.5','1.0','1.5','2.0'])
                ax.set_xlabel('Crew multiplier',fontsize=7.5)
                ax.set_ylabel('Service-loss change (h)' if row!=2 else 'Absolute group-gap\nchange (h)',fontsize=7.5)
            else:ax.set_xlabel('Repair-duration multiplier',fontsize=7.5)
        return original(fig,stem)
    r.helper.save=save
    try:r.main_resource(data)
    finally:r.helper.save=original
    h.QA.extend(r.helper.QA)
    body=next(iter(r.CAPTIONS.values()))
    body=body.replace('displayed as 0.51, 1.00, 1.51 and 2.00','displayed to one decimal as 0.5, 1.0, 1.5 and 2.0')
    body=body.replace('Panels A/B show cumulative service loss in Q4, the highest social-vulnerability quartile; '
        'C/D show population-weighted cumulative service loss across all study tracts;',
        'Panels A/B show population-weighted service loss across all study tracts; '
        'C/D show service loss in Q4, the highest social-vulnerability quartile;')
    CAPTIONS.update({key:body for key in r.CAPTIONS})

def fig07():
    authority=p.load('cluster_pdf_identity',ROOT/'results/figure_review/fig06_resource_redesign_20261002/author_feedback_fig06_fig07.py')
    with fitz.open(p.track(ROOT/'results/figure_review/complete_author_feedback_20261004/Fig07.pdf')) as source:
        authority.patch_cluster_colors(source,OLD_CLUSTER,JULY_CLUSTER)
        old=source[0];old.insert_font(fontname='ArialSingleLabel',fontfile=h.ARIAL)
        ticks=[s for _,s in h.spans(old) if s['text'] in ['C1','C2','C3','C4','C5']
               and 450<s['bbox'][1]<466]
        assert len(ticks)==5
        for _,span in h.spans(old):
            if span['text'].startswith(('C.','D.')) and 460<span['bbox'][1]<464:
                old.add_redact_annot(fitz.Rect(span['bbox']),fill=False)
        old.apply_redactions(images=0,graphics=0)
        old.insert_font(fontname='ArialSingleLabel',fontfile=h.ARIAL)
        old.draw_rect(fitz.Rect(210,453.8,375,465),color=None,fill=(1,1,1))
        for tick in ticks:
            old.insert_text(tick['origin'],tick['text'],fontname='ArialSingleLabel',fontsize=7.5)
        # Only cover the awkward split feature label; retain all native cells,
        # values, colorbar, KDE geometry and original profile hierarchy.
        old.draw_rect(fitz.Rect(36*MM,151*MM,75*MM,160*MM),color=None,fill=(1,1,1))
        old.insert_text((38*MM,155*MM),'Social vulnerability score',fontsize=7.5,fontname='ArialSingleLabel')
        doc=fitz.open();page=doc.new_page(width=185*MM,height=259*MM)
        page.show_pdf_page(fitz.Rect(0,0,185*MM,165*MM),source,0,
            clip=fitz.Rect(0,0,185*MM,165*MM),keep_proportion=False)
        # Thirteen physical millimetres between the profile axis and map headers.
        page.show_pdf_page(fitz.Rect(0,181*MM,185*MM,256*MM),source,0,
            clip=fitz.Rect(0,167*MM,185*MM,242*MM),keep_proportion=False)
        page.insert_font(fontname='ArialHeader',fontfile=h.BOLD)
        for x,text in [(9,'C. Cluster membership'),(94,'D. Hotspot score')]:
            page.insert_text((x*MM,179*MM),text,fontname='ArialHeader',fontsize=9.5)
        doc.save(OUT/'Fig07.pdf',garbage=4,deflate=True);doc.close()
    h.export(OUT/'Fig07.pdf')
    with fitz.open(frozen_copy('results/figure_review/final_submission_candidate_20261002/Supplement/FigS09.pdf')) as doc:
        authority.patch_cluster_colors(doc,OLD_CLUSTER,JULY_CLUSTER)
        doc.save(OUT/'FigS09.pdf',garbage=4,deflate=True)
    h.export(OUT/'FigS09.pdf')

def s12():
    source=frozen_copy('results/figure_review/final_submission_candidate_20261002/Supplement/FigS12.pdf')
    def replace(s,line,page):
        text=h.plain(s['text'])
        if text in ['0.51','0.51×','1.51','1.51×']:
            return {'text':text.replace('0.51','0.5').replace('1.51','1.5')}
        if text in ['1.00','2.00']:return {'text':text[:-1]}
        if text=='Cumulative service loss (h)':return {'text':'Modeled service loss (h)'}
        return None
    h.edit_text(source,OUT/'FigS12.pdf',replace);h.export(OUT/'FigS12.pdf')

def package():
    md=(BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').read_text(encoding='utf-8')
    for title,body in CAPTIONS.items():
        prefix=title.split('.')[0]
        if prefix not in ['Figure 3','Figure 4','Figure 5','Figure 6']:continue
        pat=r'(?ms)(^## '+re.escape(prefix)+r'\.[^\n]*\n\n).*?(?=^## |\Z)'
        md,n=re.subn(pat,lambda m:'## '+title+'\n\n'+body+'\n\n',md);assert n==1,title
    md=md.replace('displayed as 0.51, 1.00, 1.51 and 2.00','displayed to one decimal as 0.5, 1.0, 1.5 and 2.0')
    md=md.replace('0.51, 1.00, 1.51, 2.00','0.5, 1.0, 1.5, 2.0')
    md=md.replace('Category colors identify the same cluster IDs in the profiles and maps.',
                  'The July muted palette identifies the same cluster IDs in the profiles, maps and Supplementary Figure S9.')
    (BUNDLE/'MANUSCRIPT_FACING_CAPTIONS.md').write_text(md.rstrip()+'\n',encoding='utf-8')
    manifest=pd.read_csv(BUNDLE/'FIGURE_MANIFEST.csv',dtype=str).fillna('')
    for stem in STEMS:
        with fitz.open(OUT/(stem+'.pdf')) as doc:
            pg=doc[0];minimum=min(s['size'] for _,s in h.spans(pg))
            size=f'{pg.rect.width/MM:.3f} x {pg.rect.height/MM:.3f}'
        for ext in ['.pdf','.png']:
            src=OUT/(stem+ext);dst=BUNDLE/('Supplement' if stem.startswith('FigS') else 'Main')/(stem+ext)
            shutil.copyfile(src,dst);assert h.sha(src)==h.sha(dst)
            mask=manifest.final_name.eq(dst.relative_to(BUNDLE).as_posix());assert mask.sum()==1
            manifest.loc[mask,['source_file','source_commit','sha256','size_mm','min_font_pt','status']]=[
                src.relative_to(ROOT).as_posix(),'ARTWORK_COMMIT_PENDING',h.sha(src),size,f'{minimum:.3f}',
                'AUTHOR_REVIEW_UPDATE_NOT_PROMOTED']
    manifest.to_csv(BUNDLE/'FIGURE_MANIFEST.csv',index=False)
    evidence=BUNDLE/'Review_Evidence';evidence.mkdir(exist_ok=True)
    for extension in ['.pdf','.png']:
        shutil.copyfile(OUT/('Q4_Q1_Definition_Companion'+extension),evidence/('Q4_Q1_Definitions'+extension))
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
        page=book.new_page(width=185*MM,height=350*MM)
        page.insert_font(fontname='ArialPacket',fontfile=h.ARIAL)
        page.insert_font(fontname='ArialPacketBold',fontfile=h.BOLD)
        page.insert_text((14*MM,20*MM),title,fontname='ArialPacketBold',fontsize=9.5)
        assert page.insert_textbox(fitz.Rect(14*MM,29*MM,171*MM,333*MM),body,
            fontname='ArialPacket',fontsize=9.2,lineheight=1.22)>=0,title
    assert len(book)==40
    book.save(BUNDLE/'ALL_FIGURES_WITH_CAPTIONS.pdf',garbage=4,deflate=True);book.close()

def main():
    before=guard();h.style();data=p.outcomes()
    for name,fun in [('Fig03',lambda:fig03(data)),('Fig04',lambda:fig04(data)),
        ('Fig05',lambda:fig05(data)),('signed-gap companion',lambda:signed_companion(data)),
        ('Fig06',fig06),('Fig07/S09',fig07),('S12',s12)]:
        print('Rendering '+name,flush=True);fun()
    package()
    for category,paths in before.items():
        assert all(h.sha(ROOT/k)==value for k,value in paths.items()),category
    pd.DataFrame(p.DISPLAY).to_csv(OUT/'DISPLAYED_VALUES.csv',index=False)
    pd.DataFrame(h.QA).drop_duplicates('file',keep='last').to_csv(OUT/'OUTPUT_QA.csv',index=False)
    (OUT/'READ_INPUT_HASHES.json').write_text(json.dumps(p.INPUTS,indent=2))
    (OUT/'VALIDATION.json').write_text(json.dumps(dict(scientific_hash_changes=0,
        publication_hash_changes=0,protected_artwork_changes=0,updated=STEMS,
        scientific_processes_executed=[],rendering='native Arial PDF and 600-dpi preview'),indent=2))
    print('PRESENTATION_RENDER_COMPLETE_SCIENCE_HASH_CHANGES_0',flush=True)

if __name__=='__main__':main()
