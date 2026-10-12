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
    table=table.rename(columns={'classification':'historical_classification','selected_value':'historical_selected_value'})
    table['original_source_sha256']=a.sha(a.payload(source))
    table['initialization_boundary']='Historical quality-mix/warm or heuristic backgrounds, except generic operator property tests; not proof of pure-random optimum'
    table['current_audit_evidence']='PARAMETER_SCREEN_RESULTS.csv, PARAMETER_CONFIRMATION_RESULTS.csv, PARAMETER_GAIN_CONFIRMATION_RESULTS.csv, six-family paired effects, implementation QA; historical budget records only PURE_RANDOM_GA'
    table['new_parameter_value_adopted']=False
    a.csv('PARAMETER_TRANSFER_EVIDENCE_MATRIX.csv',table)
    old_numeric=a.frame(source.parent/'HISTORICAL_PAIRED_STATISTICS.csv')
    a.csv('HISTORICAL_PARAMETER_COMPARISONS_REUSED.csv',old_numeric)
    effects=a.frame(a.OUT/'PAIRED_PARAMETER_EFFECTS.csv')
    specs=[('Population','100',['P50','P250'],'Initial pool size, RNG length, elite fraction1/N and generations change together at equal distinct work'),
        ('Crossover operator','OX',[],'Valid order-preserving operator; no pure-random alternative-crossover superiority claim'),
        ('Crossover rate','0.80',['CX60','CX95'],'One-factor probabilities, same-size initial pool and all other settings fixed'),
        ('Mutation operator','Swap',['INVERSION','INSERTION'],'20k controlled screen only;100k operator optimum not established'),
        ('Mutation rate','0.10',['M05','M20'],'20k controlled screen only;100k exact-rate optimum not established'),
        ('Tournament','3',['T2','T5'],'With-replacement pressure, ties retain first drawn index'),
        ('Elites','1',['E0','E2'],'20k controlled screen only; current-population survival is distinct from passive output retention'),
        ('Budget and replication','100k x20',[],'Direct existing pure-random20-run records;10 continued prefixes are not fresh replicates'),
        ('Adaptive/restart/crowding','Disabled',[],'Reproducible basic reference; enabled variants not required here and not shown inferior')]
    rows=[]
    for name,value,cases,scope in specs:
        conclusions=[]
        for case in cases:
            e=effects[effects.case.eq(case)&effects.stage.eq('confirmation_six_contrast')]
            if e.empty:e=effects[effects.case.eq(case)&effects.stage.eq('screen')]
            r=e.iloc[0]
            verdict='direction unresolved, not equivalence'
            if r.simultaneous95_high_hr<0:verdict='lower loss within this budget/background'
            elif r.simultaneous95_low_hr>0:verdict='higher loss within this budget/background'
            conclusions.append(f'{case}: {r.stage}, n={r.n}, delta={r.mean_delta_hr:+.9f}h, adjusted95=[{r.simultaneous95_low_hr:+.9f},{r.simultaneous95_high_hr:+.9f}], {verdict}')
        rows.append(dict(parameter=name,frozen_reference_value=value,random_only_control_scope=scope,
            actual_comparisons='; '.join(conclusions) or 'Direct implementation/reference history; no new parameter contrast required',
            reference_status='Valid reproducible operating choice; not uniquely optimal',
            warm_start_numerical_evidence_not_used_for_admission=True,
            interactions='One-factor conditional evidence only; no interaction estimate claimed',
            frozen_method_changed=False))
    a.csv('CURRENT_RANDOM_PARAMETER_DEFENSIBILITY.csv',rows)
    costs=a.frame(a.OUT/'BUDGET_AND_DUPLICATE_ACCOUNTING.csv')
    m=costs[costs.stage.eq('confirmation')&costs.case.eq('REF')]
    t=costs[costs.stage.eq('confirmation')&costs.case.eq('T2')]
    p=costs[costs.stage.eq('confirmation')&costs.case.eq('P250')]
    a.md('PARAMETER_MECHANISM_AND_COST.md',f'''# Conditional parameter dynamics and cost

At100k, REF completed mean {m.completed_generations.mean():.2f} generations, versus {p.completed_generations.mean():.2f} for P250. These are not equal-generation interventions. All settings use only random chromosomes, but population size changes random-pool coverage, its minimum, RNG consumption and the fixed-one-elite fraction (P50/P100/P250:2%/1%/0.4%). There is no joint recommendation combining separately tested beneficial coordinates.

T2's last-complete-generation positional entropy is mean {t.final_position_entropy.mean():.6f}, versus {m.final_position_entropy.mean():.6f} for REF. Retaining more diversity does not by itself establish better budget-limited search. The pooled recorded standardized parent-selection intensity is {t.mean_parent_intensity.mean():.6f} for T2 and {m.mean_parent_intensity.mean():.6f} for REF. It depends on the evolving fitness distribution and zero-variance generations; it is not an interchangeable pressure scale on which larger pooled intensity means a stronger tournament. Source code verifies with-replacement sizes2 versus3; the one-factor paired performance contrast, not this pooled index, establishes the tested loss difference.

REF's mean all-query cache-hit fraction is {m.cache_hit_fraction.mean():.6f}. Mandatory rescanning of cached parents contributes {int(m.parent_cache_queries.sum())} queries across20 runs; duplicate member queries contribute {int(m.member_duplicate_queries.sum())}. The all-query fraction must not be mislabeled as the fraction of duplicate newly produced offspring. Elites zero still preserves the passive best-observed output; it does not secretly reinsert that archive in the breeding population.

Distinct budget means distinct full92 permutations within a private search cache, not distinct dispatched schedules or distinct scalar fitness values. EXACT_FITNESS_TIE_DIAGNOSTICS.csv counts exact scalar-score multiplicity from every terminal checkpoint. Equal objective values alone do not establish scheduler equivalence; no physical phenotype has been silently deduplicated or counted as an independent experimental replication. First exact best-fitness tie is retained as implemented.

Per-run wall/CPU measurements include search, native checkpoint and derived diagnostic serialization through the final receipt; rawZIP compression occurs after the recorded per-run timing. Batch wall includes startup and raw-evidence packaging. Twelve workers shared a host with audit/replay work; timing ratios are measured operational costs, not controlled dedicated-hardware speed constants. Distinct original-objective calls are exactly budgeted independently of these lookup and serialization costs. Complete final RNG, score cache, operator state and traces are preserved.

Mutation/elite/operator alternatives not chosen for100k confirmation remain explicitly20k-only evidence. No100k optimum is inferred for those choices. Adaptive/restart/crowding and alternative crossovers were not tested merely to enlarge the search; their disabled status is a simplicity/reference decision, not evidence they are inferior.
''')
    inventory=a.lp(a.OUT/'PARAMETER_EVIDENCE_INVENTORY.md').read_text(encoding='utf-8')
    marker='## Completed random-only evidence'
    if marker not in inventory:
        inventory+='\n'+marker+'\n\nThe initial registration above is retained. CURRENT_RANDOM_PARAMETER_DEFENSIBILITY.csv gives the completed parameter-by-parameter empirical assessment, exact adjusted intervals and limitations. PARAMETER_TRANSFER_EVIDENCE_MATRIX.csv explicitly labels the older classifications and values as historical, not current admissions. The post-screen confirmation amendment is disclosed in GAIN_CONFIRMATION_DESIGN.json and the final decision. There are244 fresh cold-start searches in28 independent seed blocks (8 screen and20 confirmation); settings share seeds for paired inference, not244 independent observations. No outcome from physical validation selected a parameter.\n'
        a.md('PARAMETER_EVIDENCE_INVENTORY.md',inventory)

def interpretation():
    decision=a.read(a.OUT/'PARAMETER_DECISION_FROZEN.json')
    gate=a.read(a.OUT/'MECHANISM_ACCESS_GATE.json')
    assert gate['parameter_decision_sha256']==a.sha(a.OUT/'PARAMETER_DECISION_FROZEN.json')
    hist=a.frame(a.OUT/'HISTORICAL_REFERENCE_REUSED.csv');main=hist[hist.budget.eq(100000)]
    legacy_proximity=32.998840773882714
    assert int((main.final_loss_hr<=legacy_proximity).sum())==10
    comp=a.frame(a.OUT/'SERVICE_LOSS_COMPONENT_TABLE.csv')
    benefit=a.frame(a.OUT/'PAIRED_REALIZATION_BENEFIT_SUMMARY.csv').set_index('subset')
    trade=a.frame(a.OUT/'VULNERABILITY_AND_EQUITY_TRADEOFF.csv').set_index('metric')
    completion=a.frame(a.OUT/'PAIRED_STATION_COMPLETION_AND_TRAVEL.csv')
    outcomes=a.frame(n.V/'REALIZATION_OUTCOMES.csv')
    frozen_effects=a.frame(n.V/'PAIRED_EFFECTS.csv')
    original_primary='population_weighted_normalized_burden_hr'
    alias_error=float(np.max(abs(outcomes[n.PRIMARY]-outcomes[original_primary])))
    assert alias_error<1e-8
    primary=frozen_effects[frozen_effects.candidate.eq(n.GA)&frozen_effects.reference.eq(n.IMPACT)&frozen_effects.metric.eq(original_primary)].iloc[0]
    assert abs(primary.mean_difference-comp.iloc[3].difference_hr)<1e-8
    a.csv('PRIMARY_VALIDATION_EFFECT_REUSED.csv',[primary.to_dict()])
    a.save('NORMALIZATION_ALIAS_QA.json',dict(status='PASS',saved_fields=[n.PRIMARY,original_primary],
        cases_checked=6000,max_abs_field_difference_hr=alias_error,
        original_statistical_primary_name_retained=True,objective_or_mapping_changed=False))
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
        both=p[n.GA].notna()&p[n.IMPACT].notna()
        c.append(dict(target_fraction=target,n=len(p),ga_mean_crossing_hr=p[n.GA].mean(),impact_mean_crossing_hr=p[n.IMPACT].mean(),
            mean_paired_change_hr=(p[n.GA]-p[n.IMPACT])[both].mean(),common_uncensored_pairs=int(both.sum()),
            ga_uncensored=int(p[n.GA].notna().sum()),impact_uncensored=int(p[n.IMPACT].notna().sum()),
            ga_mean_restricted480_crossing_hr=p[n.GA].fillna(480).mean(),
            impact_mean_restricted480_crossing_hr=p[n.IMPACT].fillna(480).mean(),
            mean_restricted480_paired_change_hr=(p[n.GA].fillna(480)-p[n.IMPACT].fillna(480)).mean(),
            censored_count=int(g.censored.sum()),
            mean_crossing_definition='Observed means use explicitly counted uncensored cases; restricted480 means include all2000, censoring at480h is descriptive not imputed physical crossing'))
    a.csv('SOURCE_RECONNECTION_TIMING_SUMMARY.csv',c)
    station_events=a.frame(a.OUT/'ILLUSTRATIVE_EVENT_STATION_CHANGES.csv')
    event_summaries=[]
    for (r,policy,event),g in station_events.groupby(['r','strategy','event_hr']):
        assert len(g)==92
        new=g.C_after.gt(0)&g.C_before.eq(0)
        event_summaries.append(dict(r=r,strategy=policy,event_hr=event,
            new_source_connected_dependency_fraction=g.loc[new,'dependency_mass'].sum()/g.dependency_mass.sum(),
            newly_source_connected_stations=int(new.sum()),
            native_threshold_crossing_station_ids='|'.join(g.loc[g.F_after.ne(g.F_before),'station_id'].astype(str)),
            native_task_completion_station_ids='|'.join(g.loc[g.native_task_completion_at_event,'station_id'].astype(str)),
            interpretation='Within-trajectory native event association, not a policy-movement causal counterfactual'))
    a.csv('ILLUSTRATIVE_SOURCE_EVENT_SUMMARY.csv',event_summaries)
    timing_text='\n'.join(f"- {100*x['target_fraction']:.0f}% connected mass: GA/Impact restricted480 mean crossing {x['ga_mean_restricted480_crossing_hr']:.6f}/{x['impact_mean_restricted480_crossing_hr']:.6f}h; paired change {x['mean_restricted480_paired_change_hr']:+.6f}h; uncensored counts {x['ga_uncensored']}/{x['impact_uncensored']}." for x in c)
    event_text='\n'.join(f"- Case {int(x['r']):04d}, {x['strategy']}: largest saved connection event at {x['event_hr']:.6f}h adds {100*x['new_source_connected_dependency_fraction']:.3f}% dependency mass across {x['newly_source_connected_stations']} stations; threshold-crossing IDs {x['native_threshold_crossing_station_ids'] or 'none'}, task-completion IDs {x['native_task_completion_station_ids'] or 'none'}." for x in event_summaries)
    sources=comp.iloc[2].difference_hr;total=comp.iloc[3].difference_hr
    a.md('SOURCE_CONNECTIVITY_MECHANISM_AUDIT.md',f'''# Frozen-policy source-connectivity mechanism

Only after PARAMETER_DECISION_FROZEN.json was sealed were the existing2,000 validation cases loaded. No new physical realization, scoring search, replacement source-gate rule or policy selection was performed.

Exact saved-event mean GA-minus-Impact loss decomposition: self {comp.iloc[0].difference_hr:+.9f}h; threshold {comp.iloc[1].difference_hr:+.9f}h; source {sources:+.9f}h; total {total:+.9f}h. Components sum exactly within1e-10h. Source improvement exceeds net improvement because the other two components increase. This is an accounting decomposition of whole policies, not a causal mediation estimate or an isolated-station counterfactual.

At each native event, f is raw own functionality, F is threshold eligibility (f>=0.5), C is membership in a functional induced component with an active Core source, and e=f*F*C. The reconstructed mass curve is sum_s C_s(t)*m_s / sum_s m_s, with m=W.T@population. It is population dependency mass, not observed customers energized or measured delivered MW. Effective service weights this mass by f, so repair completion, threshold crossing, component reconnection and full self-restoration are not interchangeable.

All 4,000 GA/Impact saved trajectories were independently reintegrated on their exact event clocks, checking all four loss integrals (16,000 checks). The descriptive hourly mean curves are plotting samples only; no quantitative integral is obtained from hourly samples. Exact source-connected-mass 25/50/80/95% crossings are in SOURCE_RECONNECTION_TIMING_SUMMARY.csv. These are not the system effective-service T80.

The largest benefit, largest harm and nearest-median cases were deterministically selected for illustration, after the parameter decision. Their native task records, exact per-station f/F/C changes and before/after component membership are retained. Each displayed source-connected mask is independently reconstructed from the 318-edge graph and 14-source set. Components include station IDs, source IDs and associated mass. Native task completion at an event is reported as an association, not a controlled causal effect. No unobserved line failure, MW, station capacity or customer routing is inferred.

Across2,000 cases, average matched dispatched-station completion change is {completion.mean_completion_change_hr.mean():+.6f}h; GA has lower average completion in {int((completion.mean_completion_change_hr<0).sum())}/2000 cases. Mean directed travel change is {completion.total_directed_travel_change_hr.mean():+.6f}h. Per-case earlier/later/equal task-station counts and travel are saved. These averages concern native dispatch records, not necessarily all92 stations. Lower population loss is not evidence every repaired station completes earlier.

## Actual source-reconnection timings

{timing_text}

Restricted480 summaries include all2,000 cases; uncensored-only means and denominators are separately recorded. An unreached threshold is censored, not inferred to occur at480h. These measures describe connected dependency mass, not effective-service T80.

## Reconstructed illustrative native events

{event_text}

These are post-freeze illustrations selected by the fixed benefit/harm/median rule. Complete before/after components and exact station masks are retained. They establish what occurs in each simulated trajectory, not that moving one station in isolation would produce the whole-policy difference.
''')
    q=[trade.loc[f'burden_Q{i}_hr'].difference for i in range(1,5)]
    gap=trade.loc['absolute_Q4_minus_Q1_hr'];gini=trade.loc['burden_gini'];hospital=trade.loc['hospital_mean_normalized_burden_hr']
    a.md('SCIENTIFIC_INTERPRETATION_MEMO.md',f'''# Scientific interpretation memo: pure-random GA

## 1. Independent algorithmic search

The frozen method uses 100 independent random.sample permutations, empty cache/incumbents and a passive initially empty archive. Its existing zero-incumbent guard is necessary; invoking the generic engine without that guard is not the recorded method. Permutation validity, initial-score budget inclusion, with-replacement tournaments, OX, swap, elites and checkpoint/RNG continuation pass explicit engineering checks. The source is unchanged.

The reused legacy loader reads a metadata registry that also contains a prior sequence, but accesses only planning_sample_hashes and H_plan_hr. It also constructs the Impact comparator for identity checks; that tuple and its score never initialize or participate in a new search. The exact kernel has no hidden fitness cache. Numba's compiled-code cache is not a chromosome-score cache. Thus independence refers to verified search dataflow, not an inaccurate claim that legacy registry/comparator files are never read. The loader's terse older docstring is qualified by this source audit.

The 20 reused pure-reference 100k runs have initial-best mean {main.initial_best_loss_hr.mean():.6f} h, final mean {main.final_loss_hr.mean():.6f} h (SD {main.final_loss_hr.std():.6f} h, median {main.final_loss_hr.median():.6f} h, range {main.final_loss_hr.min():.6f} to {main.final_loss_hr.max():.6f} h). Actual mean gain after random initialization is {main.gain_after_random_initialization_hr.mean():.6f} h; minimum {main.gain_after_random_initialization_hr.min():.6f} h. These gains were generated after random initialization, not inherited from a prior. Selection/recombination/mutation generate the valid searched orders, but their separate causal contributions require ablation; operator success flags alone do not prove one caused the total gain. Historical 93.06% inherited gain is excluded.

Twelve one-factor alternatives used8 fresh20k seeds. The original screen-selected confirmation family contained T2/P250/CX95, ranked by absolute mean effect. A transparent post-screen amendment registered P50/CX60/T5 before any100k confirmation result was inspected. These six alternatives each received20 fresh100k seeds, sharing the same20 reference runs once; all six final contrasts are jointly adjusted. The amendment is not described as a pre-screen registration. See FINAL_PURE_RANDOM_GA_PARAMETER_DECISION.md for the exact decision (**{decision['recommended_development_configuration']}**). Screen-only improvements do not establish a100k superior configuration. There is no unique-optimum, equivalence or global convergence claim. No adaptive/restart/crowding mechanism is needed for the reproducible reference; disabled status is not proof those methods cannot help. Population changes also alter initial coverage, RNG stream length and completed generations at fixed distinct work.

The pure-random adoption remains a post-data methodological judgment. The original automatic rule was not passed; the earlier registered J<=32.998840773882714h proximity criterion was met in10/20 at100k, not90%. That earlier computational0.001h margin is not an equivalence or policy-benefit threshold for the new parameter study. Ten existing250k/500k trajectories are repeated prefixes, and their plateau does not prove global optimality or single-run reliability. Actual within-seed budget changes are retained separately. No new high-budget continuation was launched.

## 2. Modeled source connection dominates net mean benefit

The fixed GA-minus-Impact exact source-loss change is {sources:+.6f}h; self/threshold changes are {comp.iloc[0].difference_hr:+.6f}/{comp.iloc[1].difference_hr:+.6f}h, leaving net {total:+.6f}h. Directly supported: the whole-policy mean gain comes from reduced source-connectivity loss that more than offsets increased other components. Descriptive association: the GA changes completion timing and the mass entering source-connected components. Unsupported without controlled counterfactual: a particular station move caused that net gain. No empirical power delivery is observed.

## 3. Paired physical outcomes, not just mean minima

The fixed sequence improves {int(benefit.loc['improved','n'])}/2000 paired realizations ({100*benefit.loc['improved','fraction']:.2f}%) and worsens {int(benefit.loc['worsened','n'])}. Median difference {benefit.loc['all','median_hr']:+.6f}h; full range {benefit.loc['all','min_hr']:+.6f} to {benefit.loc['all','max_hr']:+.6f}h. Improved cases contribute {benefit.loc['improved','contribution_to_overall_mean_hr']:+.6f}h and worsened cases {benefit.loc['worsened','contribution_to_overall_mean_hr']:+.6f}h to the overall mean. Tail contributions are retained without trimming. Figures compare within-realization differences, not unpaired marginal policy distributions.

The original frozen primary simultaneous95% interval is [{primary.simultaneous95_low:+.9f},{primary.simultaneous95_high:+.9f}]h (original family {primary.simultaneous_family}). It is reused, not reselected or recalibrated here. The primary saved metric name is population_weighted_normalized_burden_hr; the population-resolved-mass field used for native loss accounting agrees across all6,000 case/policy records within {alias_error:.3g}h. Both names and the exact consistency check are retained rather than silently swapping normalization definitions.

## 4. Efficiency and equality move in opposite directions

All quartile mean burdens decline (Q1..Q4 changes {', '.join(f'{x:+.6f}' for x in q)}h). Q4 already has lower mean burden than Q1. Its larger decline makes the signed Q4-Q1 difference more negative; this does not reduce absolute disparity. Mean per-realization absolute gap increases {gap.difference:+.6f}h (pointwise95 [{gap.pointwise95_low:+.6f},{gap.pointwise95_high:+.6f}]); tract population-weighted Gini increases {gini.difference:+.6f} (pointwise95 [{gini.pointwise95_low:+.6f},{gini.pointwise95_high:+.6f}]). Neither abs(mean signed gap) nor Gini of mean tract burdens substitutes for mean per-realization inequality.

Quartiles are unchanged SOVI tract quartiles with original population weights within each group, not four equal-population bins. Hospital-associated tract mean falls {hospital.difference:+.6f}h, an unweighted mean across103 associated tracts, not hospital load, facility uptime or patient outcomes. System T80 is mean individual exact80% effective-service crossing, not the crossing of the averaged curve or tract-mean T80. Each pointwise secondary interval is labeled descriptive; only prior primary population contrasts use the frozen simultaneous family.

This is an observed tradeoff under the mean-population objective, directed57-crew scheduler, proxy dependency mapping and fixed physical model. It does not imply all GAs are inherently inequitable. No equity constraint or new objective is added. The joint outcome counts quantify how often lower population burden coexists with greater gap/Gini.

## 5. Generalization and role of optimization

Algorithmic improvement, comparator policy benefit, optimizer-seed reliability and physical generalization are separate claims. This study assesses optimizer randomness conditional on 64 planning states, then interprets an already frozen policy across 2,000 physical realizations generated in an earlier authorized validation, with zero new draws here. Those outputs were not consulted for parameter selection here. Scenario-level simulation comparisons are not validation against utility outage/reconnection observations, delivered MW or customer-level power. A search plateau is not a proven optimum; independent sampling cannot remove model misspecification.

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
    fig,axs=plt.subplots(1,3,figsize=(11.6,4.2),layout='constrained',gridspec_kw={'width_ratios':[1.5,1.35,.75]})
    g=trajectory[trajectory.stage.eq('historical')]
    summary=g.groupby('distinct_evaluations').loss_hr.agg(['median','min','max','count']).reset_index()
    axs[0].plot(summary.distinct_evaluations,summary['median'],color=BLUE,label='Median reference search')
    axs[0].fill_between(summary.distinct_evaluations,summary['min'],summary['max'],color=BLUE,alpha=.14,label='Across-seed min-max')
    axs[0].set_xscale('log');axs[0].set(xlabel='Distinct objective evaluations',ylabel='Planning service loss (h)',title='A1  Independent random-start search')
    axs[0].legend(loc='upper right');axs[0].text(.03,.03,'20 runs to 100k; first 10 at 250k/500k\nInitial pool included; plateau is not optimality',transform=axs[0].transAxes,fontsize=8)
    e=effects[effects.stage.eq('confirmation_six_contrast')].sort_values('mean_delta_hr')
    for ax,sub,title in [(axs[1],e[e.case.ne('T2')],'A2  Near-reference contrasts'),(axs[2],e[e.case.eq('T2')],'A3  Tournament 2')]:
        y=np.arange(len(sub));ax.errorbar(sub.mean_delta_hr,y,xerr=np.vstack([sub.mean_delta_hr-sub.simultaneous95_low_hr,sub.simultaneous95_high_hr-sub.mean_delta_hr]),fmt='o',color=ORANGE,capsize=3)
        ax.axvline(0,color=GREY,linewidth=.8);ax.set_yticks(y,sub.case)
        ax.set(xlabel='Alternative minus reference (h)',title=title,ylim=(-.8,max(len(sub)-.2,.8)))
    axs[1].text(.02,.02,'20 fresh seeds; six-contrast adjusted 95% CI\nNegative favors alternative',transform=axs[1].transAxes,fontsize=7)
    axs[2].set_xlim(0,max(e.loc[e.case.eq('T2'),'simultaneous95_high_hr'])*1.15)
    axs[2].text(.03,.05,'Same family,\ndifferent x scale',transform=axs[2].transAxes,fontsize=7)
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
    axs[1].legend(loc='center right',bbox_to_anchor=(1,.30),fontsize=7)
    axs[1].text(.03,.03,'Full 0-480 h data retained; plot shown 0-120 h\nHourly display only; exact events define integrals',transform=axs[1].transAxes,fontsize=7)
    output(fig,'B')
    paired=a.frame(a.OUT/'PLOTTING_TABLE_C.csv');x=paired.ga_minus_impact_hr.to_numpy()
    fig,axs=plt.subplots(1,2,figsize=(10,4.1),layout='constrained')
    axs[0].hist(x,bins=45,color=BLUE,alpha=.75,edgecolor='white');axs[0].axvline(0,color=GREY,linewidth=1)
    axs[0].axvline(x.mean(),color=ORANGE,linewidth=1.5,label=f'Mean {x.mean():+.3f}h')
    axs[0].axvline(np.median(x),color=GREEN,linestyle='--',label=f'Median {np.median(x):+.3f}h')
    axs[0].set(xlabel='Paired GA minus Impact service loss (h)',ylabel='Physical realizations',title='C1  All 2,000 paired differences');axs[0].legend()
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

A: Exact strict-improvement reference records show genuine post-random-pool GA gains; shaded range describes seeds, not uncertainty of empirical utility performance. Fresh100k confirmation effects have Bonferroni simultaneous95% paired t intervals across six contrasts (three original plus three registered post-screen follow-ups, with20 shared reference runs). A2 and A3 use separate linear x scales so that Tournament2's large deterioration does not hide the five near-reference contrasts. Larger population changes initial coverage and generations; the historical10 high-budget prefixes are not20 fresh runs. A flat line does not prove global optimality. All12 screen contrasts and negative outcomes remain in CSVs.

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
