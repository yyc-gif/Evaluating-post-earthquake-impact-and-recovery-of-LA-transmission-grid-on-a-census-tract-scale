"""Present the already completed frozen analysis; never evaluate or resample."""
from __future__ import annotations
import hashlib
from pathlib import Path
import json
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import finalize as f

OUT = f.OUT
REVIEW = f.v.long_path(f.ROOT / 'Review_and_Revision/Pure_Random_GA_20261011')
ART = OUT / 'artwork'
BLUE, ORANGE = '#0072B2', '#D55E00'
LABEL = {f.CANDIDATE:'GA', f.IMPACT:'Impact-first', f.LEGACY:'Legacy GA'}
PRIMARY = f.v.PRIMARY


def write(name, content, directory=OUT):
    content = re.sub(r'\b(cohort of|unchanged|exact|seed|at|The|the|before|all|All|full|over|On|under|only|individual|prespecified|simultaneous|pointwise|Figure|Table|Panel)(?=\d)', r'\1 ', content)
    content = re.sub(r'\b(is|are|was|by|from|to|self|threshold|source-path|interval|and|in|burden|versus|increase|difference|loss|worsens|or|Impact-first|failed|of|a|with|only|every|on|respectively; none was censored at)(?=[+\-\d\[])', r'\1 ', content)
    content = re.sub(r'(\d)(h\b|million\b|hours\b)', r'\1 \2', content)
    content = content.replace('formalGA', 'formal GA').replace('Stage7', 'Stage 7').replace('PanelA', 'Panel A').replace('panelA', 'panel A').replace('PanelB', 'Panel B').replace('panelB', 'panel B').replace('first96h', 'first 96 h').replace('full0-480h', 'full 0-480 h').replace('the80%', 'the 80%').replace('TableGA1', 'Table GA1').replace(']h', '] h')
    (directory / name).write_text(content.strip()+'\n', encoding='utf-8', newline='\n')


def main():
    freeze = f.verify()
    qa = f.v.read(OUT / 'NUMERICAL_AND_COHORT_QA.json')
    assert qa['status']=='PASS' and qa['sample_count']==2000 and qa['policy_records']==6000
    source_names = ['POLICY_OUTCOMES.csv','PAIRED_EFFECTS.csv','REALIZATION_OUTCOMES.csv',
                    'RECOVERY_CURVES.csv','REVIEW_MODEL_METADATA.json']
    inputs = {n:f.v.sha(OUT/n) for n in source_names}
    levels = pd.read_csv(OUT/'POLICY_OUTCOMES.csv',float_precision='round_trip')
    effects = pd.read_csv(OUT/'PAIRED_EFFECTS.csv',float_precision='round_trip')
    realized = pd.read_csv(OUT/'REALIZATION_OUTCOMES.csv',float_precision='round_trip')
    curves = pd.read_csv(OUT/'RECOVERY_CURVES.csv',float_precision='round_trip')
    meta = f.v.read(OUT/'REVIEW_MODEL_METADATA.json')
    def level(policy, metric):
        return levels.loc[(levels.strategy==policy)&(levels.metric==metric)].iloc[0]
    def effect(reference, metric):
        return effects.loc[(effects.reference==reference)&(effects.metric==metric)].iloc[0]
    def interval(row, family=False):
        prefix='simultaneous95' if family else 'ci95'
        return f"[{row[prefix+'_low']:.6f}, {row[prefix+'_high']:.6f}]"
    table_metrics = [PRIMARY,'hospital_mean_normalized_burden_hr','burden_Q1_hr','burden_Q2_hr',
        'burden_Q3_hr','burden_Q4_hr','signed_Q4_minus_Q1_hr','absolute_Q4_minus_Q1_hr',
        'burden_gini','T80_restricted_hr','effective_service_at_480']
    rows=[]
    for metric in table_metrics:
        for ref in (f.IMPACT,f.LEGACY):
            l, r, e = level(f.CANDIDATE,metric), level(ref,metric), effect(ref,metric)
            rows.append(dict(metric=metric,candidate=f.CANDIDATE,reference=ref,n=2000,
                candidate_mean=l['mean'],reference_mean=r['mean'],candidate_minus_reference=e.mean_difference,
                pointwise95_low=e.ci95_low,pointwise95_high=e.ci95_high,
                simultaneous95_low=e.simultaneous95_low,simultaneous95_high=e.simultaneous95_high,
                unit='dimensionless' if metric in ('burden_gini','effective_service_at_480') else 'normalized_service_loss_hours' if metric!= 'T80_restricted_hr' else 'system_crossing_hours',
                candidate_sha256=freeze['strategies'][0]['sequence_sha256']))
    f.v.csv(REVIEW/'REVIEW_NUMERICAL_TABLE.csv',pd.DataFrame(rows))
    p, old = effect(f.IMPACT,PRIMARY), effect(f.LEGACY,PRIMARY)
    hosp=effect(f.IMPACT,'hospital_mean_normalized_burden_hr')
    gap=effect(f.IMPACT,'absolute_Q4_minus_Q1_hr')
    gini=effect(f.IMPACT,'burden_gini')
    component_metrics=['L_self_population_mass_weighted_hr','L_threshold_population_mass_weighted_hr','L_source_population_mass_weighted_hr']
    components = [effect(f.IMPACT,k).mean_difference for k in component_metrics]
    assert abs(sum(components)-p.mean_difference)<1e-10
    reduction=-p.mean_difference/level(f.IMPACT,PRIMARY)['mean']*100
    summary = f'''# Frozen random only GA independent validation

The frozen random-only GA candidate is validated on a new, authorized cohort of2,000 damage/repair realizations conditional on the unchanged2pc50 field and physical model. The exact92-station sequence is seed2026103108 at100k distinct evaluations, SHA256 `{freeze['strategies'][0]['sequence_sha256']}`. The20-seed execution protocol and final selection were committed before this fresh cohort. No tuning, optimization or reselection occurred during validation.

## Population and source path mechanism

Mean normalized population-weighted service loss is{level(f.CANDIDATE,PRIMARY)['mean']:.6f}h for GA and{level(f.IMPACT,PRIMARY)['mean']:.6f}h for Impact-first. GA minus Impact-first is{p.mean_difference:.6f}h; two-contrast simultaneous95% interval{interval(p,True)}h. The mean reduction is{reduction:.3f}% of the Impact-first mean. GA has lower population loss in{int(p.improved_count)}/2,000 ({p.improved_count/20:.2f}%), higher loss in{int(p.worsened_count)} and no ties. This is modeled efficiency, not observed outages or delivered energy.

The exact component difference is self{components[0]:+.6f}h, threshold{components[1]:+.6f}h, source-path{components[2]:+.6f}h, summing to{p.mean_difference:+.6f}h. Less source-path loss offsets greater self and threshold loss. These are descriptive event-integral components, not evidence that a particular station movement caused the benefit.

## Hospital associated tracts

The103 hospital-associated tracts have mean normalized burden{level(f.CANDIDATE,'hospital_mean_normalized_burden_hr')['mean']:.6f}h under GA versus{level(f.IMPACT,'hospital_mean_normalized_burden_hr')['mean']:.6f}h under Impact-first. The paired difference is{hosp.mean_difference:.6f}h, pointwise95% interval{interval(hosp)}h. This is an unweighted mean of normalized tract burdens, not hospital-load-weighted loss, hospital uptime, patient disruption, facility capacity or MWh. It is not a comparison with Hospital-first, which is outside this fresh three-policy cohort.

## Distributional tradeoff

GA lowers all four population-weighted SOVI-quartile mean burdens relative to Impact-first. Q1-Q4 GA means are{', '.join(f"{level(f.CANDIDATE,'burden_'+q+'_hr')['mean']:.6f}" for q in ('Q1','Q2','Q3','Q4'))}h; corresponding Impact-first means are{', '.join(f"{level(f.IMPACT,'burden_'+q+'_hr')['mean']:.6f}" for q in ('Q1','Q2','Q3','Q4'))}h. Q4 is the highest vulnerability group, but its baseline mean burden is lower than Q1 in this model. A larger Q4 reduction does not establish lower disparity.

Mean per-realization absolute Q4-Q1 separation increases from{level(f.IMPACT,'absolute_Q4_minus_Q1_hr')['mean']:.6f}h to{level(f.CANDIDATE,'absolute_Q4_minus_Q1_hr')['mean']:.6f}h; paired increase{gap.mean_difference:+.6f}h, pointwise95% interval{interval(gap)}h. Population-weighted tract burden Gini increases from{level(f.IMPACT,'burden_gini')['mean']:.6f} to{level(f.CANDIDATE,'burden_gini')['mean']:.6f}; difference{gini.mean_difference:+.6f}, pointwise95% interval{interval(gini)}. Thus absolute group outcomes improve while measured dispersion worsens. Do not describe this as an equity improvement.

The fixed labels are SOVI tract quartiles, not equal-population bins. Population weighting occurs within each group. Q1-Q4 populations are{', '.join(f"{meta['quartiles'][q]['population']:,.0f}" for q in ('Q1','Q2','Q3','Q4'))}; the full2315-tract population is{meta['population']:,.0f}. Mean absolute gaps are means of realization-specific absolute differences, not absolute values of averaged signed differences. Gini is likewise averaged after per-realization computation.

## Legacy sequence traceability

The unchanged legacy formal GA has mean population loss{level(f.LEGACY,PRIMARY)['mean']:.6f}h. New-minus-legacy is{old.mean_difference:.6f}h, two-contrast simultaneous95% interval{interval(old,True)}h. Yet the new candidate worsens{int(old.worsened_count)}/2,000 ({old.worsened_count/20:.2f}%) realizations, with median difference{old.median_difference:+.6f}h. A minority of larger benefits lowers the mean; this is not uniform dominance. The new candidate's hospital-associated mean is{effect(f.LEGACY,'hospital_mean_normalized_burden_hr').mean_difference:+.6f}h higher than legacy, and both absolute-gap and Gini means increase. Retain these results as supplementary provenance. Do not present a second GA method or replace legacy results retrospectively.

## Uncertainty and interpretation

All policies share the same new physical draw per realization. Inference resamples complete paired realizations, not tracts or6,000 trajectories. The20,000-resample bootstrap uses seed2026110400. Only the two population-loss contrasts have simultaneous95% Bonferroni percentile intervals; hospital, quartile, gap, Gini and T80 intervals are descriptive pointwise. All2,000 system T80 crossings occurred before480h for all three strategies. GA mean system T80 is{level(f.CANDIDATE,'T80_restricted_hr')['mean']:.6f}h and Impact-first{level(f.IMPACT,'T80_restricted_hr')['mean']:.6f}h; these are means of per-realization system crossings, not tract-mean T80 or the crossing of the mean curve.

This is a prospective stochastic model test, not empirical validation against measured electricity outages. The post-data method choice and failed90% single-run planning-proximity criterion remain in the immutable method evidence. A fresh physical cohort does not turn those earlier choices into preregistered method development or imply reliable performance from every single optimization run.
'''
    write('VALIDATION_RESEARCH_REPORT.md',summary)
    results = f'''# Prospective GA results

On2,000 new paired physical realizations under2pc50/C57_D1/M1/G1, mean population-weighted normalized service loss was{level(f.CANDIDATE,PRIMARY)['mean']:.3f}h for GA and{level(f.IMPACT,PRIMARY)['mean']:.3f}h for Impact-first. The paired GA-minus-Impact-first difference was{p.mean_difference:.3f}h (simultaneous95% interval{interval(p,True)}h), a{reduction:.2f}% reduction. GA had lower loss in{int(p.improved_count)} realizations and higher loss in{int(p.worsened_count)}. Reduced source-path loss ({components[2]:.3f}h) offset increases in self-loss ({components[0]:.3f}h) and threshold loss ({components[1]:.3f}h). Figure1 displays the new-cohort mean effective-service curves; no legacy GA curve is relabeled.

Mean normalized burden over hospital-associated tracts was{level(f.CANDIDATE,'hospital_mean_normalized_burden_hr')['mean']:.3f}h for GA and{level(f.IMPACT,'hospital_mean_normalized_burden_hr')['mean']:.3f}h for Impact-first. The paired difference was{hosp.mean_difference:.3f}h (pointwise95% interval{interval(hosp)}h). This unweighted tract proxy does not measure hospital load, patient disruption or delivered power. System T80 averaged{level(f.CANDIDATE,'T80_restricted_hr')['mean']:.3f}h and{level(f.IMPACT,'T80_restricted_hr')['mean']:.3f}h, respectively; none was censored at480h.

The aggregate improvement did not reduce dispersion. GA lowered population-weighted burden in every frozen SOVI tract quartile, with a larger reduction in Q4 than Q1. However, because Q4's baseline burden was already lower, mean absolute Q4-Q1 separation increased by{gap.mean_difference:.3f}h (pointwise95% interval{interval(gap)}h), and population-weighted burden Gini increased by{gini.mean_difference:.5f} (pointwise95% interval{interval(gini)}). Figure4 and TableGA1 therefore report absolute group burdens and disparity separately. These results do not establish an equity improvement or a universal realization-level advantage.
'''
    write('RESULTS_GA_REPLACEMENT.md',results,REVIEW)
    write('DISCUSSION_GA_REPLACEMENT.md',f'''# GA interpretation and limitations

The frozen GA improves expected normalized population service loss relative to Impact-first in this prospective cohort, chiefly through a lower source-path component rather than shorter local self-loss. Its objective is expected aggregate loss, not hospital performance, fairness, worst-case loss or global optimality. Lower hospital-associated tract burden against Impact-first and lower absolute burdens in all SOVI groups coexist with wider absolute Q4-Q1 separation and greater Gini. An efficiency benefit should not be described as an equity benefit.

The optimization specification is one repeated-run, random-only GA; internal algorithm trials are not presented as separate manuscript methods. Its planning-side adoption was a post-data methodological choice and only10/20 individual100k runs reached the strict proximity threshold, below the prespecified90%. Independent physical validation evaluates the selected fixed strategy, not the success probability of a single GA run or empirical physical accuracy. Keep the original model assumptions and distinguish normalized service deficit from actual customer outages.

The original fixed-rule, resource, mapping and Stage7 results retain their archived physical cohorts and saved sequence. The new2,000-realization prospective evaluation does not automatically update cluster recovery coordinates, membership, hotspot rankings or intervention recommendations. Their original provenance must remain explicit; no refit or silent relabeling is undertaken here.
''',REVIEW)
    write('SUPPLEMENTARY_LEGACY_COMPARISON.md',f'''# Saved legacy strategy comparison

The new GA-minus-legacy formalGA population-loss difference is{old.mean_difference:.6f}h with simultaneous95% interval{interval(old,True)}h. The new candidate is worse in{int(old.worsened_count)} realizations, better in{int(old.improved_count)}, with median{old.median_difference:+.6f}h. It has a lower expected population loss but not typical-realization dominance. Hospital-associated loss changes by{effect(f.LEGACY,'hospital_mean_normalized_burden_hr').mean_difference:+.6f}h (pointwise95% interval{interval(effect(f.LEGACY,'hospital_mean_normalized_burden_hr'))}h), absolute gap by{effect(f.LEGACY,'absolute_Q4_minus_Q1_hr').mean_difference:+.6f}h, and Gini by{effect(f.LEGACY,'burden_gini').mean_difference:+.6f}. These paired new-cohort results cannot be substituted into the older validation package.

Legacy is a fixed provenance comparator, not a second newly described optimization method. It is omitted from the main candidate-vs-Impact figures but retained in the complete evidence and numerical tables. All physical states, schedules, trajectories, sequence hashes and evaluation/kernel QA are archived. Negative endpoints are retained without tuning, reselection or a follow-up search.
''',REVIEW)
    ART.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.5,'axes.titlesize':9.5,
        'axes.labelsize':8.5,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,
        'savefig.facecolor':'white','pdf.fonttype':42,'axes.labelpad':5})
    figure_files=[]
    def save(fig,name):
        fig.savefig(ART/(name+'.png'),dpi=350)
        fig.savefig(ART/(name+'.pdf'))
        figure_files.extend([ART/(name+'.png'),ART/(name+'.pdf')])
        plt.close(fig)
    def grid(ax):
        ax.grid(axis='y',color='#dddddd',lw=.5,zorder=0)
    def error(ax,x,y,lo,hi,color,label=None):
        x, y, lo, hi = (np.atleast_1d(value) for value in (x, y, lo, hi))
        ax.errorbar(x,y,yerr=np.vstack((y-lo,hi-y)),
            fmt='o',ms=4,capsize=3,color=color,label=label,lw=1.2,zorder=3)
    fig,axes=plt.subplots(1,2,figsize=(180/25.4,90/25.4),layout='constrained')
    for ax, limit, title in zip(axes,(96,480),('A  First 96 hours','B  Full 480-hour horizon')):
        for policy,color in ((f.CANDIDATE,BLUE),(f.IMPACT,ORANGE)):
            data=curves.loc[curves.strategy==policy]
            ax.plot(data.time_hr,data.population_availability,color=color,lw=1.6,label=LABEL[policy])
        ax.set(xlim=(0,limit),ylim=(0,1.03),xlabel='Time (hours)',ylabel='Mean modeled availability',title=title)
        grid(ax)
    axes[0].legend(loc='lower right',frameon=False)
    save(fig,'FIG_GA_RECOVERY')
    fig,axes=plt.subplots(1,2,figsize=(180/25.4,85/25.4),layout='constrained')
    for x,policy,color in ((0,f.CANDIDATE,BLUE),(1,f.IMPACT,ORANGE)):
        row=level(policy,PRIMARY)
        error(axes[0],x,row['mean'],row.ci95_low,row.ci95_high,color)
    axes[0].set(xticks=[0,1],xticklabels=['GA','Impact-first'],ylabel='Population service loss (h)',title='A  Mean and pointwise 95% interval',xlim=(-.5,1.5))
    wide=realized.pivot(index='realization_id',columns='strategy',values=PRIMARY)
    delta=np.sort((wide[f.CANDIDATE]-wide[f.IMPACT]).to_numpy())
    axes[1].step(delta,np.arange(1,2001)/2000,where='post',color=BLUE,lw=1.4)
    axes[1].axvline(0,color='#555555',ls='--',lw=.8)
    axes[1].set(xlabel='GA minus Impact-first loss (h)',ylabel='Cumulative fraction',ylim=(0,1.02),title='B  Paired physical realizations')
    axes[1].text(.03,.92,f'Lower loss: {int(p.improved_count)}/2,000',transform=axes[1].transAxes,fontsize=8)
    for ax in axes:grid(ax)
    save(fig,'FIG_GA_POPULATION_LOSS')
    fig,axes=plt.subplots(1,2,figsize=(180/25.4,85/25.4),layout='constrained')
    for x,policy,color in ((0,f.CANDIDATE,BLUE),(1,f.IMPACT,ORANGE)):
        row=level(policy,'hospital_mean_normalized_burden_hr')
        error(axes[0],x,row['mean'],row.ci95_low,row.ci95_high,color)
    axes[0].set(xticks=[0,1],xticklabels=['GA','Impact-first'],ylabel='Hospital-associated tract burden (h)',title='A  Unweighted tract mean',xlim=(-.5,1.5))
    error(axes[1],0,hosp.mean_difference,hosp.ci95_low,hosp.ci95_high,BLUE)
    axes[1].axhline(0,color='#555555',ls='--',lw=.8)
    axes[1].set(xticks=[0],xticklabels=['GA minus Impact-first'],ylabel='Paired difference (h)',xlim=(-.5,.5),ylim=(-.36,.04),title='B  Pointwise 95% interval')
    for ax in axes:grid(ax)
    save(fig,'FIG_GA_HOSPITAL_LOSS')
    fig=plt.figure(figsize=(180/25.4,125/25.4),layout='constrained')
    spec=fig.add_gridspec(2,2,height_ratios=[1.15,1])
    top=fig.add_subplot(spec[0,:]); bottom=[fig.add_subplot(spec[1,i]) for i in (0,1)]
    for policy,color,shift in ((f.CANDIDATE,BLUE,-.07),(f.IMPACT,ORANGE,.07)):
        data=[level(policy,'burden_'+q+'_hr') for q in ('Q1','Q2','Q3','Q4')]
        error(top,np.arange(4)+shift,[r['mean'] for r in data],[r.ci95_low for r in data],[r.ci95_high for r in data],color,LABEL[policy])
    top.set(xticks=range(4),xticklabels=['Q1 lowest','Q2','Q3','Q4 highest'],ylabel='Population-weighted group burden (h)',title='A  Fixed SOVI tract quartiles')
    top.legend(frameon=False,loc='upper right')
    for ax,row,label,title in zip(bottom,(gap,gini),('Absolute Q4-Q1 gap difference (h)','Burden Gini difference'),('B  Absolute group separation','C  Tract burden dispersion')):
        error(ax,0,row.mean_difference,row.ci95_low,row.ci95_high,BLUE)
        ax.axhline(0,color='#555555',ls='--',lw=.8)
        ax.set(xticks=[0],xticklabels=['GA minus Impact-first'],ylabel=label,xlim=(-.5,.5),title=title)
    for ax in [top,*bottom]:grid(ax)
    save(fig,'FIG_GA_EQUITY')
    captions={
        'FIG_GA_RECOVERY':'Mean population-weighted effective-service availability on2,000 new shared realizations. PanelA expands the first96h; panelB retains the full0-480h horizon. Blue is the frozen random-only GA, orange Impact-first. These are means of realized event trajectories, not Hazus mean curves or actual delivered MW. The average per-realization T80 is not the80% crossing of this mean curve.',
        'FIG_GA_POPULATION_LOSS':'Normalized population service loss under the fixed two main policies. PanelA shows policy means and descriptive pointwise95% bootstrap intervals. PanelB shows the full empirical CDF of paired GA-minus-Impact-first losses; negative differences favor GA. The confirmatory population comparison uses the separate simultaneous two-contrast interval in the result table, not the marginal policy-mean intervals in panelA.',
        'FIG_GA_HOSPITAL_LOSS':'Unweighted mean normalized burden over103 hospital-associated tracts. PanelA shows policy means and pointwise95% bootstrap intervals; panelB the paired mean difference and pointwise95% interval. This measures a tract association proxy, not facility load, patients, hospital uptime or energy loss.',
        'FIG_GA_EQUITY':'Population-weighted burden within the frozen SOVI tract quartiles (Q1 lowest, Q4 highest vulnerability), plus paired differences in mean per-realization absolute Q4-Q1 separation and population-weighted burden Gini. All intervals are descriptive pointwise95%. Lower group burdens coexist with higher disparity measures. Quartile groups are not equal-population bins, and mean absolute separation is not the absolute mean signed gap.'}
    write('FIGURE_CAPTIONS.md','\n\n'.join('# '+name+'\n\n'+text for name,text in captions.items()),REVIEW)
    f.v.write(OUT/'REVIEW_NUMERICAL_QA.json',dict(status='PASS',source_sha256=inputs,
        candidate_sha256=freeze['strategies'][0]['sequence_sha256'],source_records=6000,
        reused_bootstrap_outputs=True,new_bootstrap_calls=0,new_production_calls=0,new_physical_draws=0,
        source_component_delta_conservation=True,
        figures={str(p.relative_to(OUT)).replace('\\','/'):dict(sha256=f.v.sha(p),bytes=p.stat().st_size) for p in figure_files},
        physical_cohort='new fixed2000 only',legacy_curve_in_main_figures=False,
        normalized_proxy_units_preserved=True,negative_equity_results_retained=True))
    print('REPORT_AND_FOUR_FIGURES_CREATED; fresh-cohort values only; no new evaluations',flush=True)


if __name__=='__main__':main()
