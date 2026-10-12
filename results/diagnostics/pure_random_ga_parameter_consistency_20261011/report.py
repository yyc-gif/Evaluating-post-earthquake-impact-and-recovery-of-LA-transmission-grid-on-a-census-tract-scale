"""Technical diagnostic memo/graphics only; no manuscript files are touched."""
from __future__ import annotations
import argparse
import json
import numpy as np
import pandas as pd
import audit as a
import analysis as n

BLUE,ORANGE,GREEN,GREY='#0072B2','#D55E00','#009E73','#777777'

def evidence_table():
    source=a.BASE/'results/diagnostics/ga_ils_parameter_defense_20261010/GA_PARAMETER_EVIDENCE_MATRIX.csv'
    old=a.frame(source)
    table=old.copy()
    table['original_source_sha256']=a.sha(a.payload(source))
    table['initialization_boundary']='Historical quality-mix/warm or heuristic backgrounds, except generic operator property tests; not proof of pure-random optimum'
    table['current_audit_evidence']='PARAMETER_SCREEN_RESULTS.csv, selected PARAMETER_CONFIRMATION_RESULTS.csv, implementation QA; historical budget records only PURE_RANDOM_GA'
    table['new_parameter_value_adopted']=False
    a.csv('PARAMETER_TRANSFER_EVIDENCE_MATRIX.csv',table)
    old_numeric=a.frame(source.parent/'HISTORICAL_PAIRED_STATISTICS.csv')
    a.csv('HISTORICAL_PARAMETER_COMPARISONS_REUSED.csv',old_numeric)

def interpretation():
    decision=a.read(a.OUT/'PARAMETER_DECISION_FROZEN.json')
    gate=a.read(a.OUT/'MECHANISM_ACCESS_GATE.json')
    assert gate['parameter_decision_sha256']==a.sha(a.OUT/'PARAMETER_DECISION_FROZEN.json')
    hist=a.frame(a.OUT/'HISTORICAL_REFERENCE_REUSED.csv');main=hist[hist.budget.eq(100000)]
    comp=a.frame(a.OUT/'SERVICE_LOSS_COMPONENT_TABLE.csv')
    benefit=a.frame(a.OUT/'PAIRED_REALIZATION_BENEFIT_SUMMARY.csv').set_index('subset')
    trade=a.frame(a.OUT/'VULNERABILITY_AND_EQUITY_TRADEOFF.csv').set_index('metric')
    completion=a.frame(a.OUT/'PAIRED_STATION_COMPLETION_AND_TRAVEL.csv')
    outcomes=a.frame(n.V/'REALIZATION_OUTCOMES.csv')
    metrics=[n.PRIMARY,'absolute_Q4_minus_Q1_hr','burden_gini','hospital_mean_normalized_burden_hr','signed_Q4_minus_Q1_hr']
    deltas={m:outcomes.pivot(index='realization_id',columns='strategy',values=m)[n.GA]-outcomes.pivot(index='realization_id',columns='strategy',values=m)[n.IMPACT] for m in metrics}
    joint=[]
    for fairness in ('absolute_Q4_minus_Q1_hr','burden_gini'):
        for benefit_flag in (True,False):
            for inequality_flag in (True,False):
                mask=(deltas[n.PRIMARY]<-1e-9).eq(benefit_flag)&(deltas[fairness]>1e-9).eq(inequality_flag)
                joint.append(dict(metric=fairness,population_loss_improves=benefit_flag,inequality_increases=inequality_flag,
                    n=int(mask.sum()),fraction=mask.mean(),mean_population_delta_hr=deltas[n.PRIMARY][mask].mean(),mean_inequality_delta=deltas[fairness][mask].mean()))
    a.csv('JOINT_EFFICIENCY_INEQUALITY_COUNTS.csv',joint)
    np.testing.assert_allclose(outcomes.absolute_Q4_minus_Q1_hr,abs(outcomes.signed_Q4_minus_Q1_hr),atol=1e-12)
    crossing=a.frame(a.OUT/'SOURCE_CONNECTED_MASS_CROSSINGS.csv')
    c=[]
    for target,g in crossing.groupby('target_fraction'):
        p=g.pivot(index='r',columns='strategy',values='first_source_connected_mass_crossing_hr')
        c.append(dict(target_fraction=target,n=len(p),ga_mean_crossing_hr=p[n.GA].mean(),impact_mean_crossing_hr=p[n.IMPACT].mean(),
            mean_paired_change_hr=(p[n.GA]-p[n.IMPACT]).mean(),censored_count=int(g.censored.sum())))
    a.csv('SOURCE_RECONNECTION_TIMING_SUMMARY.csv',c)
    sources=comp.iloc[2].difference_hr;total=comp.iloc[3].difference_hr
    a.md('SOURCE_CONNECTIVITY_MECHANISM_AUDIT.md',f'''# Frozen-policy source-connectivity mechanism

Only after PARAMETER_DECISION_FROZEN.json was sealed were the existing2,000 validation cases loaded. No new physical realization, scoring search, replacement source-gate rule or policy selection was performed.

Exact saved-event mean GA-minus-Impact loss decomposition: self {comp.iloc[0].difference_hr:+.9f}h; threshold {comp.iloc[1].difference_hr:+.9f}h; source {sources:+.9f}h; total {total:+.9f}h. Components sum exactly within1e-10h. Source improvement exceeds net improvement because the other two components increase. This is an accounting decomposition of whole policies, not a causal mediation estimate or an isolated-station counterfactual.

At each native event, f is raw own functionality, F is threshold eligibility (f>=0.5), C is membership in a functional induced component with an active Core source, and e=f*F*C. The reconstructed mass curve is sum_s C_s(t)*m_s / sum_s m_s, with m=W.T@population. It is population dependency mass, not observed customers energized or measured delivered MW. Effective service weights this mass by f, so repair completion, threshold crossing, component reconnection and full self-restoration are not interchangeable.

All4,000 GA/Impact saved source integrals were independently reintegrated on their exact event clocks. The descriptive hourly mean curves are plotting samples only; no quantitative integral is obtained from hourly samples. Exact source-connected-mass25/50/80/95% crossings are in SOURCE_RECONNECTION_TIMING_SUMMARY.csv. These are not the system effective-service T80.

The largest benefit, largest harm and nearest-median cases were deterministically selected for illustration, after the parameter decision. Their native task records, exact masks and before/after component membership are retained. Each displayed source-connected mask is independently reconstructed from the318-edge graph and14-source set. Components include station IDs, source IDs and associated mass. Timing associations are not controlled causal effects. No unobserved line failure, MW, station capacity or customer routing is inferred.

Across2,000 cases, average station-completion change is {completion.mean_completion_change_hr.mean():+.6f}h; GA has lower average completion in {int((completion.mean_completion_change_hr<0).sum())}/2000 cases. Mean directed travel change is {completion.total_directed_travel_change_hr.mean():+.6f}h. Per-case earlier/later/equal station counts and travel are saved. Lower population loss is not evidence every repaired station completes earlier.
''')
    q=[trade.loc[f'burden_Q{i}_hr'].difference for i in range(1,5)]
    gap=trade.loc['absolute_Q4_minus_Q1_hr'];gini=trade.loc['burden_gini'];hospital=trade.loc['hospital_mean_normalized_burden_hr']
    a.md('SCIENTIFIC_INTERPRETATION_MEMO.md',f'''# Scientific interpretation memo: pure-random GA

## 1. Independent algorithmic search

The frozen method uses100 independent random.sample permutations, empty cache/incumbents and a passive initially empty archive. Its existing zero-incumbent guard is necessary; invoking the generic engine without that guard is not the recorded method. Permutation validity, initial-score budget inclusion, with-replacement tournaments, OX, swap, elites and checkpoint/RNG continuation pass explicit engineering checks. The source is unchanged.

The20 reused pure-reference100k runs have initial-best mean {main.initial_best_loss_hr.mean():.6f}h, final mean {main.final_loss_hr.mean():.6f}h (SD {main.final_loss_hr.std():.6f}h, median {main.final_loss_hr.median():.6f}h, range {main.final_loss_hr.min():.6f} to {main.final_loss_hr.max():.6f}h). Actual mean gain after random initialization is {main.gain_after_random_initialization_hr.mean():.6f}h; minimum {main.gain_after_random_initialization_hr.min():.6f}h. These gains were generated after random initialization, not inherited from a prior. Selection/recombination/mutation generate the valid searched orders, but their separate causal contributions require ablation; operator success flags alone do not prove one caused the total gain. Historical93.06% inherited gain is excluded.

Twelve one-factor alternatives used8 fresh20k seeds. Three prespecified consequential contrasts received20 separate100k seeds. See FINAL_PURE_RANDOM_GA_PARAMETER_DECISION.md for the exact decision (**{decision['recommended_development_configuration']}**). Screen-only improvements do not establish a100k superior configuration. There is no unique-optimum, equivalence or global convergence claim. No adaptive/restart/crowding mechanism is needed for the reproducible reference; disabled status is not proof those methods cannot help. Population changes also alter initial coverage, RNG stream length and completed generations at fixed distinct work.

The pure-random adoption remains a post-data methodological judgment. The original automatic rule was not passed; strict100k proximity was10/20, not90%. Ten existing250k/500k trajectories are repeated prefixes, and their plateau does not prove global optimality or single-run reliability. No new high-budget continuation was launched.

## 2. Modeled source connection dominates net mean benefit

The fixed GA-minus-Impact exact source-loss change is {sources:+.6f}h; self/threshold changes are {comp.iloc[0].difference_hr:+.6f}/{comp.iloc[1].difference_hr:+.6f}h, leaving net {total:+.6f}h. Directly supported: the whole-policy mean gain comes from reduced source-connectivity loss that more than offsets increased other components. Descriptive association: the GA changes completion timing and the mass entering source-connected components. Unsupported without controlled counterfactual: a particular station move caused that net gain. No empirical power delivery is observed.

## 3. Paired physical outcomes, not just mean minima

The fixed sequence improves {int(benefit.loc['improved','n'])}/2000 paired realizations ({100*benefit.loc['improved','fraction']:.2f}%) and worsens {int(benefit.loc['worsened','n'])}. Median difference {benefit.loc['all','median_hr']:+.6f}h; full range {benefit.loc['all','min_hr']:+.6f} to {benefit.loc['all','max_hr']:+.6f}h. Improved cases contribute {benefit.loc['improved','contribution_to_overall_mean_hr']:+.6f}h and worsened cases {benefit.loc['worsened','contribution_to_overall_mean_hr']:+.6f}h to the overall mean. Tail contributions are retained without trimming. Figures compare within-realization differences, not unpaired marginal policy distributions.

## 4. Efficiency and equality move in opposite directions

All quartile mean burdens decline (Q1..Q4 changes {', '.join(f'{x:+.6f}' for x in q)}h). Q4 already has lower mean burden than Q1. Its larger decline makes the signed Q4-Q1 difference more negative; this does not reduce absolute disparity. Mean per-realization absolute gap increases {gap.difference:+.6f}h (pointwise95 [{gap.pointwise95_low:+.6f},{gap.pointwise95_high:+.6f}]); tract population-weighted Gini increases {gini.difference:+.6f} (pointwise95 [{gini.pointwise95_low:+.6f},{gini.pointwise95_high:+.6f}]). Neither abs(mean signed gap) nor Gini of mean tract burdens substitutes for mean per-realization inequality.

Quartiles are unchanged SOVI tract quartiles with original population weights within each group, not four equal-population bins. Hospital-associated tract mean falls {hospital.difference:+.6f}h, an unweighted mean across103 associated tracts, not hospital load, facility uptime or patient outcomes. System T80 is mean individual exact80% effective-service crossing, not the crossing of the averaged curve or tract-mean T80. Each pointwise secondary interval is labeled descriptive; only prior primary population contrasts use the frozen simultaneous family.

This is an observed tradeoff under the mean-population objective, directed57-crew scheduler, proxy dependency mapping and fixed physical model. It does not imply all GAs are inherently inequitable. No equity constraint or new objective is added. The joint outcome counts quantify how often lower population burden coexists with greater gap/Gini.

## 5. Generalization and role of optimization

Algorithmic improvement, comparator policy benefit, optimizer-seed reliability and physical generalization are separate claims. This study assesses optimizer randomness conditional on64 planning states, then interprets an already frozen policy across2,000 new physical realizations from an earlier authorized validation. Those outputs were not consulted for parameter selection here. Scenario-level simulation comparisons are not validation against utility outage/reconnection observations, delivered MW or customer-level power. A search plateau is not a proven optimum; independent sampling cannot remove model misspecification.

The GA obtains a useful priority order; the scientific contribution is the infrastructure/community recovery mechanism and its distributional consequences. No formal candidate, manuscript, Word review file, journal figure, Stage7 input or independent physical-validation record has changed. Any future adoption of a changed method/candidate, fairness objective or empirical utility interpretation requires explicit author approval and appropriate new evidence. No broad optimizer comparison, warm-start study or repeated validation is recommended as part of this completed bounded audit.
''')
    evidence_table()
    a.save('INTERPRETATION_DEFINITIONS_QA.json',dict(status='PASS',absolute_gap_per_realization_verified=True,
        source_connected_mass_distinct_from_effective_service=True,
        all_quartile_mean_losses_lower=all(x<0 for x in q),mean_absolute_gap_increases=gap.difference>0,gini_increases=gini.difference>0,
        physical_generalization_not_optimizer_seed_reliability=True,manuscript_changes=0))

def graphics():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,
        'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    def output(fig,letter):
        fig.savefig(a.lp(a.OUT/f'DIAGNOSTIC_FIGURE_{letter}.pdf'),bbox_inches='tight')
        fig.savefig(a.lp(a.OUT/f'DIAGNOSTIC_FIGURE_{letter}.png'),dpi=220,bbox_inches='tight')
        plt.close(fig)
    trajectory=a.frame(a.OUT/'GA_SEARCH_TRAJECTORY_SUMMARY.csv');effects=a.frame(a.OUT/'PAIRED_PARAMETER_EFFECTS.csv')
    fig,axs=plt.subplots(1,2,figsize=(10,4.1),layout='constrained')
    g=trajectory[trajectory.stage.eq('historical')]
    summary=g.groupby('distinct_evaluations').loss_hr.agg(['median','min','max']).reset_index()
    axs[0].plot(summary.distinct_evaluations,summary['median'],color=BLUE,label='Median reference search')
    axs[0].fill_between(summary.distinct_evaluations,summary['min'],summary['max'],color=BLUE,alpha=.14,label='Across-seed min-max')
    axs[0].set_xscale('log');axs[0].set(xlabel='Distinct objective evaluations',ylabel='Planning service loss (h)',title='A1  Independent random-start search')
    axs[0].legend(loc='upper right');axs[0].text(.03,.03,'20 runs to100k; first10 at250k/500k\nInitial pool included; plateau is not optimality',transform=axs[0].transAxes,fontsize=8)
    e=effects[effects.stage.eq('confirmation')].sort_values('mean_delta_hr')
    y=np.arange(len(e));axs[1].errorbar(e.mean_delta_hr,y,xerr=np.vstack([e.mean_delta_hr-e.simultaneous95_low_hr,e.simultaneous95_high_hr-e.mean_delta_hr]),fmt='o',color=ORANGE,capsize=3)
    axs[1].axvline(0,color=GREY,linewidth=.8);axs[1].set_yticks(y,e.case)
    axs[1].set(xlabel='Alternative minus reference loss (h)',title='A2  Fresh20-seed100k confirmation')
    axs[1].text(.02,.02,'Simultaneous95% paired t intervals\nThree predeclared contrasts; negative favors alternative',transform=axs[1].transAxes,fontsize=8)
    output(fig,'A')
    a.csv('PLOTTING_TABLE_A_REFERENCE.csv',summary);a.csv('PLOTTING_TABLE_A_EFFECTS.csv',e)
    comp=a.frame(a.OUT/'SERVICE_LOSS_COMPONENT_TABLE.csv');curves=a.frame(a.OUT/'PLOTTING_TABLE_B_CURVES.csv')
    fig,axs=plt.subplots(1,2,figsize=(10,4.1),layout='constrained')
    vals=comp.difference_hr.to_numpy();labels=['Self','Threshold','Source','Total']
    axs[0].bar(labels,vals,color=[ORANGE,ORANGE,BLUE,GREEN],width=.65)
    axs[0].axhline(0,color=GREY,linewidth=.8)
    for i,v in enumerate(vals): axs[0].text(i,v+(.03 if v>=0 else -.04),f'{v:+.3f}',ha='center',va='bottom' if v>=0 else 'top',fontsize=8)
    axs[0].set(ylabel='GA minus Impact loss (h)',title='B1  Exact whole-policy loss accounting',ylim=(min(vals)-.17,max(vals)+.15))
    for policy,col in [(n.GA,BLUE),(n.IMPACT,ORANGE)]:
        c=curves[curves.strategy.eq(policy)]
        axs[1].plot(c.time_hr,c.effective_availability,color=col,label=policy+' effective service')
        axs[1].plot(c.time_hr,c.source_connected_dependency_mass_fraction,color=col,linestyle='--',label=policy+' connected mass')
    axs[1].set(xlim=(0,120),ylim=(0,1.02),xlabel='Time (h)',ylabel='Normalized modeled availability / mass',title='B2  Mean frozen-policy trajectories')
    axs[1].legend(loc='lower right',fontsize=7)
    axs[1].text(.03,.03,'Full0-480h data retained; plot shown0-120h\nHourly display only; exact events define integrals',transform=axs[1].transAxes,fontsize=7)
    output(fig,'B')
    paired=a.frame(a.OUT/'PLOTTING_TABLE_C.csv');x=paired.ga_minus_impact_hr.to_numpy()
    fig,axs=plt.subplots(1,2,figsize=(10,4.1),layout='constrained')
    axs[0].hist(x,bins=45,color=BLUE,alpha=.75,edgecolor='white');axs[0].axvline(0,color=GREY,linewidth=1)
    axs[0].axvline(x.mean(),color=ORANGE,linewidth=1.5,label=f'Mean {x.mean():+.3f}h')
    axs[0].axvline(np.median(x),color=GREEN,linestyle='--',label=f'Median {np.median(x):+.3f}h')
    axs[0].set(xlabel='Paired GA minus Impact service loss (h)',ylabel='Physical realizations',title='C1  All2000 paired differences');axs[0].legend()
    xx=np.sort(x);yy=np.arange(1,len(x)+1)/len(x)
    axs[1].step(xx,yy,where='post',color=BLUE);axs[1].axvline(0,color=GREY,linewidth=1)
    axs[1].set(xlabel='Paired GA minus Impact service loss (h)',ylabel='Empirical cumulative fraction',title='C2  Benefits and harms retained',ylim=(0,1))
    axs[1].text(.04,.08,f'{(x<-1e-9).sum()}/2000 improved ({100*(x<-1e-9).mean():.2f}%)\n{(x>1e-9).sum()}/2000 worsened\nNo tail trimming or outlier deletion',transform=axs[1].transAxes)
    output(fig,'C')
    t=a.frame(a.OUT/'VULNERABILITY_AND_EQUITY_TRADEOFF.csv').set_index('metric')
    fig,axs=plt.subplots(1,3,figsize=(11,4.1),layout='constrained',gridspec_kw={'width_ratios':[1.45,1,1]})
    q=[t.loc[f'burden_Q{i}_hr'] for i in range(1,5)];ix=np.arange(4)
    axs[0].bar(ix-.18,[r.impact_mean for r in q],.35,color=ORANGE,label='Impact-first')
    axs[0].bar(ix+.18,[r.ga_mean for r in q],.35,color=BLUE,label='Frozen GA')
    axs[0].set_xticks(ix,['Q1','Q2','Q3','Q4']);axs[0].set(ylabel='Population-weighted burden (h)',title='D1  Lower mean burden in every group',ylim=(0,40));axs[0].legend()
    for ax,metric,title,unit in [(axs[1],'absolute_Q4_minus_Q1_hr','D2  Absolute quartile gap','Mean per-realization gap (h)'),(axs[2],'burden_gini','D3  Tract burden Gini','Mean population-weighted Gini')]:
        row=t.loc[metric];ax.bar(['Impact','GA'],[row.impact_mean,row.ga_mean],color=[ORANGE,BLUE],width=.6)
        ax.set(title=title,ylabel=unit,ylim=(0,max(row.impact_mean,row.ga_mean)*1.35))
        ax.text(.5,max(row.impact_mean,row.ga_mean)*1.16,f'Change {row.difference:+.4f}',ha='center')
    output(fig,'D')
    a.md('DIAGNOSTIC_FIGURE_CAPTIONS.md','''# Technical diagnostic figures

A: Exact strict-improvement reference records show genuine post-random-pool GA gains; shaded range describes seeds, not uncertainty of empirical utility performance. Fresh100k confirmation effects have Bonferroni simultaneous95% paired t intervals across3 contrasts. Larger population changes initial coverage and generations; the historical10 high-budget prefixes are not20 fresh runs. A flat line does not prove global optimality. All12 screen contrasts and negative outcomes remain in CSVs.

B: Exact event-clock self/threshold/source loss accounting; signed contribution bars are whole-policy differences, not controlled station effects. Right panel displays hourly samples of mean effective service and source-connected dependency mass over0-120h; full0-480h plotting table is saved. Quantitative loss uses native event integration, not hourly display. Connectivity is a proxy reachability condition, not delivered MW. Native examples and component membership are in illustrations/ and ILLUSTRATIVE_SOURCE_COMPONENTS.csv.

C: Full2000 within-realization GA-minus-Impact population-loss differences, empirical histogram and CDF. Means, medians, benefits and harms are untrimmed. This is paired physical-sample heterogeneity under a fixed model, not optimizer-seed variability or observed utility error.

D: Fixed SOVI tract quartiles with original within-group population weights. All absolute group means decline, while mean per-realization absoluteQ4-Q1 gap and weighted tractGini rise. Axes start at zero; h and dimensionless units remain separate. Q4 already has lower mean burden thanQ1. Figures are technical author-inspection diagnostics only; no manuscript artwork is replaced. Companion tables include signed gap, hospital-associated unweighted tract loss, systemT80 and correctly labeled descriptive pointwise intervals.
''')
    a.save('FIGURE_RENDER_SOURCE_QA.json',dict(status='NUMERICAL_SOURCES_PASS_VISUAL_REVIEW_PENDING',
        figures=['A','B','C','D'],clipping_outcome_range=False,manuscript_figures_modified=False,
        plotting_table_sha256={p.name:a.sha(p) for p in a.OUT.glob('PLOTTING_TABLE*.csv')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['memo','figures']);x=p.parse_args()
    {'memo':interpretation,'figures':graphics}[x.phase]()
