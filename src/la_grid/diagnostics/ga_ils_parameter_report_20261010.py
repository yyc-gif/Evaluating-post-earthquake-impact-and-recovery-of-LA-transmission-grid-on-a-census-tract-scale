"""Publication-oriented defense generated from retained seed-level evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

from la_grid.diagnostics.ga_ils_parameter_defense_20261010 import (
    R, OUT, lp, read, save, sha, START, BRANCH, SCREEN, CONFIRM, preservation,
)
from la_grid.diagnostics.ga_ils_parameter_analysis_20261010 import csv, frame, contrast
from la_grid.diagnostics.ga_search_budget_sensitivity import identity


def table(name):
    return pd.read_csv(lp(OUT/name))


def write(name, text):
    lp(OUT/name).write_text(text.strip()+'\n',encoding='utf-8',newline='\n')


def md(data, columns=None):
    data=data[columns] if columns else data
    return data.to_markdown(index=False,floatfmt='.6f')


def describe(row):
    return (f"mean {row.mean_delta_hr:+.9f} h; median {row.median_delta_hr:+.9f}; "
            f"paired SD {row.sd_delta_hr:.9f}; simultaneous 95% interval "
            f"[{row.simultaneous95_low_hr:+.9f}, {row.simultaneous95_high_hr:+.9f}]; "
            f"wins/losses/ties {int(row.wins)}/{int(row.losses)}/{int(row.ties)} (n={int(row.n)})")


def matrices():
    historical=frame('ga_initialization_reconciliation_20261009/PAIRED_PARAMETER_EFFECTS.csv')
    historical=historical[historical.budget==100000].set_index('case')
    new=table('PAIRED_PARAMETER_CONTRASTS.csv')
    confirm=new[new.family.str.startswith('confirmation_')].set_index('contrast')
    def legacy(cases):
        return '; '.join(f"{c}: {historical.loc[c,'mean_change_hr']:+.9f} h "
            f"[{historical.loc[c,'bonferroni95_low_hr']:+.9f},{historical.loc[c,'bonferroni95_high_hr']:+.9f}]"
            for c in cases)
    ga=[]
    def g(parameter,value,implementation,purpose,alternatives,evidence,interaction,budget,claim,objection,response,status='DEFENSIBLE WITH QUALIFICATION'):
        ga.append(dict(parameter=parameter,selected_value=value,implementation=implementation,purpose=purpose,
            alternatives_tested=alternatives,matched_budget_evidence=evidence,interactions=interaction,
            budget_dependence=budget,supports=claim,reviewer_objection=objection,strongest_response=response,
            classification=status,source='HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv; source code',
            formal_configuration_changed=False))
    g('Representation','92-station permutation','All IDs once; two-position mutations and permutation-preserving crossovers.',
      'Priority list decoded by unchanged realization-specific scheduler, not a physical line-route tour.',
      'Swap/insertion/inversion; OX/PMX/cycle','Permutation property tests and original-evaluator candidate parity.',
      'Scheduling-equivalent permutations create plateaus.','Flat traces do not enumerate 92!.',
      'Valid encoding; not global optimality.','Why a GA for this scheduler?',
      'Nonconvex priority-order mapping; valid order search without changing scientific decoder.','SUPPORTED')
    g('Population','100','Exactly 100 evolving chromosomes; references included; duplicates allowed.',
      'Reproducible compromise between useful recombination and generations per distinct-query budget.',
      '50, 100, 250, 500',legacy(['population50','population250','population500']),
      'Quality-mixture count changes: 7/1/12/30, 7/1/25/67, 7/1/62/180, 7/1/125/367. Not pure population intervention.',
      'Legacy P500 failed at 50k; improved P500 did not show intrinsic inferiority at 100k.',
      'Reasonable fixed reference, not uniquely best.','Larger population seems poor in old report.',
      'Distinguish old inversion/no-elite initializer from improved swap/quality/elite; equal queries, not generations.')
    g('Crossover operator','ordered','Two distinct uniform cuts; inclusive copied segment; cyclic donor fill begins after high cut; reciprocal offspring.',
      'Maintains each station exactly once and retains relative ordering information.',
      'Ordered, PMX, cycle (five-seed pilots on inversion background)',
      'HISTORICAL_PAIRED_STATISTICS.csv historical_operators: PMX/cycle contrasts against ordered+inversion.',
      'PMX/cycle pilots are not a fully powered comparison on final swap configuration.',
      'No exact-operator optimum proved.','Appropriate valid operator, not proven best.',
      'Why not PMX or cycle?','Existing alternatives retained; pilot background limits generalization.','SUPPORTED')
    g('Crossover probability','0.80','Independent Bernoulli per parent pair; no crossover copies parents.',
      'Retain recombination and some intact parental priority orders.','0.60, 0.80, 0.95',legacy(['crossover060','crossover095']),
      'Early population/mutation/initializer pilots confounded.',
      '20k rankings need not persist at 100k.','Tested operating range, not optimum.',
      'Why exactly 0.80?','Pinned reference inside tested range; unresolved intervals do not prove equivalence.')
    g('Mutation operator','swap','Two distinct uniformly sampled positions exchanged.',
      'Small positional intervention appropriate to priority scheduling, without importing TSP distance assumptions.',
      'Swap, insertion, inversion, mixed',
      'Same-background operators and 20-seed swap/mixed comparison in HISTORICAL_PAIRED_STATISTICS.csv.',
      'Final versus legacy also changes .20 to .10; that larger contrast is not operator-only.',
      '100k and fixed-seed 500k final protocol.','Conditional empirical operator support.',
      'Could the improvement come only from warm start?','Use same warm initialization operator tests; separate root-cause package changes.','SUPPORTED')
    g('Mutation probability','0.10','Independent Bernoulli per child; swap if triggered.',
      'Restrained perturbation with retained order information.','0.05, 0.10, 0.20; higher early inversion pilots',
      legacy(['mutation005','mutation020']),
      'Tournament x mutation at 100k unresolved; high-rate legacy results cannot isolate final swap probability.',
      '20k screen differences weaken at 100k.','Reasonable tested probability; not uniquely optimal.',
      '0.20 sometimes numerically better.','Report paired uncertainty and costs, retain reference without claiming .10 superiority.')
    g('Selection','tournament, k=3','Each tournament draws with replacement; exact fitness tie keeps first sampled index.',
      'Ranking-based selection insensitive to fitness units.','Tournament 2, 3, 5',legacy(['tournament2','tournament5']),
      '20k k5 advantage; population x tournament, neighbors x tournament, mutation x tournament unresolved at 100k.',
      'At 500k k5-minus-k3 +.000693217 h, simultaneous interval [-.000966832,.002353265].',
      'Avoid weak k2; k3 is defensible, not uniquely best.',
      'Is k3 selection too weak or prematurely concentrated?',
      'Measured histories, not generic rhetoric: legacy parent intensity P100 .564 vs P500 .804; entropy .312 vs .835.')
    elite='; '.join(f"{c}: {describe(confirm.loc[c+' minus ga_elite1'])}" for c in ('ga_elite0','ga_elite2','ga_elite3'))
    g('Generational elitism','1','Best distinct current-population chromosome, tie by lexicographic order, replaces final offspring after reproduction RNG draws.',
      'Keep a high-quality breeding parent; distinct from retaining best-so-far output.',
      'New fixed-config 0/1/2/3: eight 20k screening seeds and 20 fresh 100k seeds',elite,
      'No warm-start/mutation change in new elite-count intervention.',
      '20k screen and independent 100k confirmation; no new 500k elite grid.',
      'Direct comparison now available; exact count remains qualified.',
      'Archive already preserves best; why elite?',
      'Archive protects reported output only; elite preserves reproductive access. Report actual count contrasts, not a redundant-archive argument.')
    g('Initialization','7/1/25/67','Seven retained reference rules; one prior optimized chromosome; 13 prior and 12 Impact inversion neighbors; 67 random permutations.',
      'Explicit exploitation and exploration; no deduplication of initializer.',
      'Heuristic removal/reduction, prior-copy removal, prior+neighbor removal, neighbor allocations/parent sources, cold controls.',
      'Removing prior+neighbors: 100k +.001609 h, simultaneous [-.000365,.003583]; 20k +.007447. Exact allocation evidence in original ablations.',
      'Removing prior copy alone retains prior-derived neighbors; random fill and RNG consumption change.',
      'Cold controls can catch up; early protection is not guaranteed final superiority.',
      'Transparent reproducible composition, not mathematical optimality.',
      'Does GA merely inherit its solution?',
      'Prior accounts for about 93.06% of selected improvement relative to Impact; subsequent search about 6.94%, plus exact per-seed generation-zero records.')
    g('Best-so-far retention','strict archive + query-best','Archive updated at completed generations; query-best includes partial final generation; first exact tie retained.',
      'Prevent reporting worse than supplied references; no automatic archived-parent injection when restart disabled.',
      'Root-cause warm/elite controls and new cold information controls.',
      'Histories record archive absence from breeding population; original archive often preserved Impact without rediscovering it.',
      'Archive and injected prior are different: archive affects reporting; initializer changes search trajectory.',
      'Same query-boundary policy for all new cases.','Correct incumbent protection, not evidence of independent discovery.',
      'Is retention biasing the claimed gain?',
      'Charge reference queries, disclose inheritance; disabling passive reporting archive cannot isolate reproductive search improvement.','SUPPORTED')
    for p in ('Adaptive mutation','Restart','Diversity replacement'):
        g(p,'disabled','No corresponding adaptive/restart/crowding branch used in frozen configuration.',
          'Keep a pinned reproducible search protocol.','Five-seed pilots on quality+inversion, not powered final-swap factorial.',
          'Saved operator_adaptive/operator_restart/operator_crowding versus operator_inversion contrasts.',
          'Background-specific; cannot conclude all modern variants ineffective.',
          'Final swap protocol already tested at 100k and 500k.',
          'Defensible fixed omission; superiority over all enabled alternatives insufficient.',
          'Why not use adaptation or diversity control?',
          'No demonstrated need to add those mechanisms to the validated fixed method; explicit missing conditional tests remain.')
    g('Budget/stopping','20 x 100k + 5 continued x 500k','Unique cached permutation keys; repeated lookups do not count as new full64 scores; no stagnation stopping.',
      'Compare expensive scientific objective work despite duplicate candidate production.',
      '20k, 50k, 100k, 250k, 500k checkpoints/continuations.',
      'Formal total 4,000,000 distinct calls (2m stage A + 2m extension); not 4.5m. High-budget GA k3 mean gain 250k->500k zero in 10 seeds.',
      'GA attempted overhead much larger; equal distinct calls not equal wall time.',
      'ILS continues to gain at higher budgets; checkpoints not independent runs.',
      'Finite reproducible allocation, not global convergence.',
      'Was stopping chosen from validation?',
      'Frozen fixed extensions; new diagnostics use prospectively committed budgets and never inspect validation outcomes.','SUPPORTED')
    csv('GA_PARAMETER_EVIDENCE_MATRIX.csv',ga)
    ils=[]
    def i(parameter,value,implementation,purpose,cases,limitation,classification='DEFENSIBLE WITH QUALIFICATION'):
        evidence='; '.join(describe(confirm.loc[c+' minus ils_mix']) for c in cases if c+' minus ils_mix' in confirm.index)
        ils.append(dict(parameter=parameter,original_value=value,implementation=implementation,purpose=purpose,
            alternatives_tested='; '.join(cases),confirmation_evidence=evidence,
            screen_source='CONFIGURATION_SUMMARY.csv and PAIRED_PARAMETER_CONTRASTS.csv',
            classification=classification,limitation=limitation,
            exact_optimum_established=False,source='ga_alternative_optimizer_20261009.py; new parity and run records'))
    i('Neighborhood','equal swap/insertion/inversion','Choose one operator uniformly per local/perturbation move; single-op variants omit selector RNG draw.',
      'Multiple valid positional neighborhoods.',['ils_swap','ils_insertion','ils_inversion'],
      'Single swap offers a reduced neighborhood set; equal mixture and three operators are not automatically necessary.')
    i('Acceptance','fitness > current + 1e-12','Reject equal/worse local proposals; restart may worsen current while best is retained.',
      'Monotone local descent with independent best record.',[],
      'Algorithm-defining strict descent; tolerance is numerical convention, not calibrated optimum.','SUPPORTED')
    i('Stagnation','800 attempted non-improving proposals','Includes cache hits; strict acceptance resets counter.',
      'Trigger escape when local proposals stop improving.',['ils_stag2000'],
      '200 vs 800 vs 2000 screened; only prospectively selected 2000 independently confirmed. 800 not uniquely optimal.')
    i('Perturbation','cyclic 2/4/8 primitive moves','Sequential mutations; may cancel; score only final perturbed sequence.',
      'Move outside currently accessible local state.',['ils_large','ils_no_perturb'],
      '1/2/4 screened; 4/8/16 selected for independent confirmation. No-perturb may exhaust accessible neighborhood before budget.')
    i('Restart reference','global best','Perturb retained best; current alternative perturbs last local state.',
      'Concentrate restarts near best found basin.',['ils_current'],
      'Best versus current directly tested; no claim that every retained-state alternative was covered.')
    i('Focused interaction','swap x stagnation','Difference of differences against mixed operators, at thresholds 800/2000.',
      'Assess whether simpler neighborhood depends on restart threshold.',['ils_swap_stag2000','ils_swap_no_perturb'],
      'Screen-motivated contrast locked before new confirmation; not an unrestricted interaction grid.')
    i('Initialization','shared prior; seven charged references','Current prior for warm; Impact for cold. Same prior information as paired GA, not identical initial populations.',
      'Avoid unequal optimized prior access.',['ils_cold'],
      'GA has a population and Impact neighbors; cold comparison is same information access, not identical initialization operations.')
    i('Budget','100k distinct; 60 x attempted cap','Fresh within-search cache, repeated lookups recorded; attempted cap may truncate accessible local control.',
      'Bound scientific objective work and redundant-search overhead.',[],
      'Incomplete controls retained as accessibility diagnostics, not equal-budget evidence.','SUPPORTED')
    i('Deterministic refinement','optional four-neighborhood exhaustive scans','Swap/insertion/inversion/adjacent-block-exchange scans; best improving move per scan; 1e-9 tolerance; extra max150k distinct per fixed seed.',
      'Check incremental local improvement beyond stochastic ILS.',[],
      'Five independent preselected seeds; continuation and equal joint-budget GA recorded. Local tested-neighborhood certificate only, not global optimum.')
    csv('ILS_PARAMETER_EVIDENCE_MATRIX.csv',ils)
    return pd.DataFrame(ga),pd.DataFrame(ils)


def refinement_statistics():
    records=read(OUT/'REFINEMENT_MULTISEED_ACCOUNTING.json')['results']
    for record in records:
        seed=record['seed']
        base=read(OUT/'confirmation'/f'ils_mix_s{seed}.json')
        prefix=read(OUT/'confirmation'/f'ga_elite1_s{seed}.json')
        joint=read(OUT/'refinement'/f's{seed}'/'GA_JOINT_BUDGET.json')
        checkpoint=next(c for c in joint['checkpoints'] if c['distinct_evaluations']==100000)
        assert abs(checkpoint['best_service_loss_hr']-prefix['search_best_loss_hr'])<1e-10
        assert checkpoint['sequence_sha256']==prefix['sequence_sha256']
        assert joint['initial_population_sha256']==prefix['initial_population_sha256']
        assert joint['post_initializer_rng_sha256']==prefix['post_initializer_rng_sha256']
        record.update(base_ils_wall_seconds=base['elapsed_wall_seconds'],
            base_ga_wall_seconds=prefix['elapsed_wall_seconds'],
            ga_continuation_replay_wall_seconds=joint['elapsed_wall_seconds'],
            joint_ils_wall_seconds=base['elapsed_wall_seconds']+record['refinement_wall_seconds'],
            joint_ga_wall_seconds=prefix['elapsed_wall_seconds']+joint['elapsed_wall_seconds'],
            ga_100k_checkpoint_matches_original=True)
    data=pd.DataFrame(records)
    data['refined_minus_base_hr']=data.refined_loss_hr-data.base_loss_hr
    data['refined_minus_matched_ga_hr']=data.refined_loss_hr-data.ga_joint_loss_hr
    csv('MULTISEED_REFINEMENT_AND_MATCHED_GA.csv',data)
    effects=[contrast(data.refined_loss_hr-data.base_loss_hr,'refined ILS minus base ILS','refinement',2,
                      'five fixed independent confirmation seeds; extra refinement work, not same-budget base contrast'),
             contrast(data.refined_loss_hr-data.ga_joint_loss_hr,'refined ILS minus matched-joint-budget GA','refinement',2,
                      'same total distinct budgets per seed; GA continuation replayed without new prefix scores')]
    csv('REFINEMENT_PAIRED_STATISTICS.csv',effects)
    return data,pd.DataFrame(effects)


def draft_claim_audit():
    records=[]
    def add(name,line,claim,decision,replacement,evidence):
        path=R/name if '/' in name else R/'docs/reviewer'/name
        assert lp(path).is_file()
        records.append(dict(source=str(path.relative_to(R)),source_sha256=sha(path),
            line=line,historical_claim=claim,decision=decision,
            current_use_qualification=replacement,evidence=evidence,source_edited=False))
    add('GA_SEARCH_BUDGET_SENSITIVITY_20261007.md',5,
        '100 generations retained Impact; 250 generations improved 16/20 seeds.',
        'KEEP_HISTORICAL; UPDATE_IF_USED_AS_CURRENT',
        'This is the legacy inversion/no-elite protocol, not the frozen swap/elite method.',
        'GA_PARAMETER_DEFENSIBILITY_REPORT.md; EXPT inventory legacy budget records')
    add('GA_SEARCH_BUDGET_SENSITIVITY_20261007.md',29,
        'Larger legacy populations/budgets were not run at that stage.',
        'KEEP_HISTORICAL; SUPERSEDED_FOR_CURRENT_STATUS',
        'Later completed population, operator and fixed-query studies must be included.',
        'HISTORICAL_PAIRED_STATISTICS.csv; EXPERIMENT_INVENTORY.csv')
    add('GA_SEARCH_BUDGET_SENSITIVITY_20261007.md',96,
        'Old S05 caption retains Impact as formal strategy.',
        'VERSION_SPECIFIC; VERIFY_AUTHOR_PROMOTION_STATUS',
        'Do not transfer an older caption to current frozen-method interpretation or infer promotion solely from validation.',
        'Frozen formal files; FINAL_RESEARCH_DECISION.md')
    add('FIGURE_S04_S05_S06_INTERPRETATION_20261007.md',5,
        'Structural topology is not delivered capacity or a source-gated service trajectory.',
        'KEEP_QUALIFIED','Preserve the distinction between structural metrics and modeled service.',
        'Unchanged scientific evaluator and source gate')
    add('FIGURE_S04_S05_S06_INTERPRETATION_20261007.md',11,
        'Old S05 interpretation reports legacy GA budget findings.',
        'KEEP_HISTORICAL; UPDATE_IF_USED_AS_CURRENT',
        'Label protocol/version; do not describe it as the current tuned GA evidence.',
        'GA_PARAMETER_EVIDENCE_MATRIX.csv')
    add('EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md',11,
        'Archive retention is different from evolutionary rediscovery.',
        'KEEP','Report initializer inheritance and evolving-population survival separately.',
        'FROZEN_INITIALIZATION_CONTRIBUTION.json; NEW_GA_SEARCH_HISTORY_MECHANISMS.csv')
    add('EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md',26,
        'P500 does not improve in the earlier generation-limited implementation.',
        'KEEP_HISTORICAL; NO_INTRINSIC_P500_CLAIM',
        'Later improved equal-query population packages do not establish intrinsic P500 inferiority.',
        'HISTORICAL_PAIRED_STATISTICS.csv')
    add('EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md',28,
        'One resumed segment time and shared memoization counts are reported.',
        'KEEP_WITH_COST_QUALIFICATION',
        'Do not treat resumed-segment time as full runtime or shared cached counts as fresh evaluations.',
        'EXECUTION_ACCOUNTING.json; original timing notes')
    add('EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md',30,
        'Earlier selected planning best is 33.038131743 h.',
        'KEEP_HISTORICAL; NOT_CURRENT_MINIMUM',
        'This is the inherited prior, not the later frozen selected minimum of 32.997840774 h.',
        'IMPORTANT_HISTORICAL_CANDIDATES.json')
    add('EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md',63,
        'Filtered DS0 signatures do not collapse every scheduling-equivalent permutation.',
        'KEEP','Equal or nearby objective values alone do not establish identical schedules.',
        'Original actionable-delay and neutral-plateau records')
    add('EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md',77,
        'No formal strategy was replaced by that diagnostic round.',
        'KEEP_HISTORICAL; PRESERVE_CURRENT_BOUNDARY',
        'This parameter audit likewise does not authorize replacement of the formal candidate.',
        'REPRODUCIBILITY_AND_PRESERVATION_QA.json')
    add('R1_COMMENT6_7_GA_REVISION_REPORT.md',7,
        'July uses 100 generations, inversion .20 and no archive.',
        'KEEP_LEGACY_DESCRIPTION; REPLACE_IF_USED_AS_CURRENT_METHOD',
        'The frozen direct-objective method uses swap .10, an archive, one elite and distinct-query budgets.',
        'FINAL_GA_CONFIG_CANDIDATE.json; GA_PARAMETER_EVIDENCE_MATRIX.csv')
    add('R1_COMMENT6_7_GA_REVISION_REPORT.md',19,
        'Earlier revised search uses inversion and fixed generation stopping.',
        'KEEP_VERSION_SPECIFIC; NOT_CURRENT_FROZEN_ENGINE',
        'Name the engine and date rather than transferring these settings to the current Methods.',
        'FINAL_GA_METHOD_AUDIT.md; REPRODUCIBILITY.md')
    add('GA_OPTIMIZATION_DECISION_20261009.md',9,
        'Conditional operating-region recommendation; 20-seed mean includes five common screening seeds.',
        'KEEP_QUALIFIED',
        'Do not call all 20 seeds independent confirmation of parameter selection; the fresh diagnostic range is separate.',
        'HISTORICAL_RECONCILIATION_QA.json; PARAMETER_SELECTION_REGISTER.json')
    add('results/diagnostics/final_ga_method_20261009/FINAL_GA_METHOD_AUDIT.md',66,
        'Proposed Methods disclose inherited initializer, finite budgets and no global-optimality proof.',
        'KEEP_WITH_PARAMETER_EVIDENCE_SUPPLEMENT',
        'This wording is scientifically bounded; add parameter sensitivity, costs and postvalidation scope.',
        'METHODS_AND_SUPPLEMENT_READY_TEXT.md; GA_PARAMETER_DEFENSIBILITY_REPORT.md')
    add('results/diagnostics/final_ga_method_20261009/GA_BUDGET_AND_REPLICATION_DECISION.md',14,
        'Counts exclude generation-zero scoring.',
        'CLARIFY_AMBIGUOUS_COUNT_UNIT',
        'Strict postinitialization improvement counts exclude generation zero; distinct query budgets include the seven charged incumbent scores.',
        'FINAL_BUDGET_CHECKPOINTS.csv strict_after_initialization; FINAL_GA_METHOD_AUDIT.md line31; ga_variant_engine.py')
    csv('EXISTING_METHOD_CLAIM_AUDIT.csv',records)


def candidate_overview(qa):
    data=pd.DataFrame([{k:r[k] for k in (
        'sequence_sha256','production_mean_hr','mean_minus_frozen_ga_hr',
        'improved_states','worsened_states','leave_one_out_sign_reversals',
        'omit_realization15_delta_hr','omit_five_best_delta_hr')}
        for r in qa['candidates']]).sort_values('production_mean_hr')
    csv('IMPORTANT_CANDIDATE_SUMMARY.csv',data)
    display=data.head(8).copy()
    display['sequence_sha256']=display.sequence_sha256.str[:12]
    display=display.rename(columns={'sequence_sha256':'SHA256 prefix',
        'production_mean_hr':'Mean J (h)','mean_minus_frozen_ga_hr':'Delta vs frozen GA (h)',
        'improved_states':'Improved states','worsened_states':'Worsened states',
        'leave_one_out_sign_reversals':'LOO reversals',
        'omit_realization15_delta_hr':'Omit 15 delta (h)',
        'omit_five_best_delta_hr':'Omit best five delta (h)'})
    return md(display)


def dynamics():
    rows=[]
    for p in lp(OUT/'confirmation').glob('ga_*.json'):
        r=read(p); initial=r['dynamics_initial']; final=r['dynamics_final']; hist=r['history']
        rows.append(dict(case=r['case'],seed=r['seed'],generations=r['generations'],
            mean_parent_selection_intensity=r['mean_selection_intensity'],
            mean_effective_parent_count=r['mean_effective_parent_count'],
            mean_position_entropy=r['mean_position_entropy'],
            initial_position_entropy=initial['position_entropy'],final_position_entropy=final['position_entropy'],
            final_unique_population=final['unique_population'],
            final_archive_copies=final['archive_copies_in_population'],
            fraction_generations_archive_absent=np.mean([h['archive_copies_in_population']==0 for h in hist]),
            first_archive_absent_generation=next((h['generation'] for h in hist if h['archive_copies_in_population']==0),None),
            attempts=r['attempted_evaluations'],distinct=r['distinct_evaluations'],
            initial_sha256=r['initial_population_sha256'],rng_after_initializer_sha256=r['post_initializer_rng_sha256']))
    data=pd.DataFrame(rows)
    csv('NEW_GA_SEARCH_HISTORY_MECHANISMS.csv',data)
    same=data[data.case.str.startswith('ga_elite')].groupby('seed')
    assert same.initial_sha256.nunique().eq(1).all()
    assert same.rng_after_initializer_sha256.nunique().eq(1).all()
    save(OUT/'ELITISM_INITIALIZATION_PARITY.json',dict(status='PASS',seeds=20,
        exact_initial_population_and_post_initializer_rng_equal_across_elite_counts=True,
        trajectory_rng_can_diverge_after_different_survival=True))
    return data


def graphics():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'savefig.dpi':300,'font.family':'DejaVu Sans'})
    effects=table('PAIRED_PARAMETER_CONTRASTS.csv')
    subset=effects[(effects.family=='confirmation_ga_elite')|
        ((effects.family=='confirmation_ils_confirmation')&effects.fully_equal_budget.eq(True))].copy()
    label_map={
        'ga_elite0 minus ga_elite1':'GA: 0 versus 1 elite',
        'ga_elite2 minus ga_elite1':'GA: 2 versus 1 elite',
        'ga_elite3 minus ga_elite1':'GA: 3 versus 1 elite',
        'ils_swap minus ils_mix':'ILS: swap versus mixed',
        'ils_insertion minus ils_mix':'ILS: insertion versus mixed',
        'ils_inversion minus ils_mix':'ILS: inversion versus mixed',
        'ils_current minus ils_mix':'ILS: current versus best restart',
        'ils_stag2000 minus ils_mix':'ILS: stagnation 2000 versus 800',
        'ils_large minus ils_mix':'ILS: 4/8/16 versus 2/4/8 perturbation',
        'ils_swap_stag2000 minus ils_mix':'ILS: swap + 2000 versus mixed + 800',
    }
    labels=subset.contrast.map(label_map)
    assert labels.notna().all()
    fig,ax=plt.subplots(figsize=(7.1,4.8)); y=np.arange(len(subset))
    for j,(_,r) in enumerate(subset.iterrows()):
        color='#0072B2' if r.family.endswith('elite') else '#009E73'
        ax.plot([r.simultaneous95_low_hr,r.simultaneous95_high_hr],[j,j],color=color,lw=1.5)
        ax.scatter(r.mean_delta_hr,j,c=color,s=22,zorder=3)
    ax.axvline(0,color='.3',lw=.8);ax.set_yticks(y,labels);ax.invert_yaxis()
    ax.set_xlabel('Paired mean service-loss difference (h)');ax.grid(axis='x',alpha=.2)
    fig.tight_layout();fig.savefig(lp(OUT/'PARAMETER_EFFECTS_CONFIRMATION.png'));plt.close(fig)
    trajectories=table('OPTIMIZER_CONVERGENCE_AND_COST.csv')
    fig,axes=plt.subplots(1,2,figsize=(7.1,3.0))
    for case,color,label in [('ga_elite1','#0072B2','GA'),('ils_mix','#009E73','Mixed ILS'),('ils_swap','#CC79A7','Swap ILS')]:
        part=trajectories[(trajectories.phase=='confirmation')&trajectories.case.eq(case)]
        group=part.groupby('evaluations').loss_hr
        x=np.array(sorted(part.evaluations.unique()))
        axes[0].plot(x/1000,group.median().to_numpy(),marker='o',ms=3,color=color,label=label)
        axes[0].fill_between(x/1000,group.quantile(.25).to_numpy(),group.quantile(.75).to_numpy(),alpha=.12,color=color)
        obs=table('NEW_SEED_LEVEL_OBSERVATIONS.csv')
        a=obs[(obs.phase=='confirmation')&obs.case.eq(case)]
        axes[1].scatter(a.attempted_evaluations/1e6,a.search_best_loss_hr,color=color,s=12,alpha=.7,label=label)
    axes[0].set_xlabel('Distinct evaluations (thousands)');axes[0].set_ylabel('Planning service loss (h)')
    axes[1].set_xlabel('Attempted queries (millions)');axes[1].set_ylabel('Final planning service loss (h)')
    axes[0].legend(frameon=False,fontsize=8);axes[1].set_xscale('log')
    for ax in axes:
        ax.grid(alpha=.2)
        ax.ticklabel_format(axis='y',style='plain',useOffset=False)
    fig.tight_layout();fig.savefig(lp(OUT/'CONVERGENCE_AND_ATTEMPTED_COST.png'));plt.close(fig)
    write('DIAGNOSTIC_FIGURE_CAPTIONS.md',"""
# Diagnostic Figure Captions

**PARAMETER_EFFECTS_CONFIRMATION.png.** Paired final-loss mean effects over 20 new optimizer seeds and Bonferroni-adjusted two-sided 95% intervals within the prospectively declared elite (three contrasts) and ILS (nine contrasts) families. Negative favors the named intervention. Incomplete no-perturbation controls are excluded from this equal-budget graphic, not from the evidence tables. Differences are normalized modeled service-loss hours, not crew wall time or guaranteed customer outage duration. New results are postvalidation exploratory with respect to the paper.

**CONVERGENCE_AND_ATTEMPTED_COST.png.** Left: median and interquartile optimizer-seed range at identical distinct-query checkpoints; shaded ranges are descriptive, not confidence intervals. Right: each completed seed's final objective and attempted calls; logarithmic horizontal axis. A checkpoint is not a new independent search. All local cases used one numerical thread per worker on the same host. CPU, objective and total wall time are reported separately in the evidence tables; duplicate lookup overhead remains visible.
""")


def reports():
    ga,ils=matrices(); refine,ref_effects=refinement_statistics(); history=dynamics()
    draft_claim_audit()
    effects=table('PAIRED_PARAMETER_CONTRASTS.csv'); summary=table('CONFIGURATION_SUMMARY.csv')
    confirm=effects[effects.family.str.startswith('confirmation_')].set_index('contrast')
    historical=table('HISTORICAL_PAIRED_STATISTICS.csv')
    account=read(OUT/'EXECUTION_ACCOUNTING.json')
    inherited=read(OUT/'FROZEN_INITIALIZATION_CONTRIBUTION.json')
    qa=read(OUT/'IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json')
    candidate_table=candidate_overview(qa)
    best_candidate=min(qa['candidates'],key=lambda r:r['production_mean_hr'])
    inventory=table('EXPERIMENT_INVENTORY.csv')
    c=summary[summary.phase=='confirmation']
    effect_text='\n'.join(f"- `{name}`: {describe(row)}. Scope: {row.scope}." for name,row in confirm.iterrows())
    common="""All new findings are postvalidation exploratory for the manuscript. Within this diagnostic study, the committed fixed contrasts and independent confirmation seeds are prospective; selecting two settings from the separate eight-seed engineering screen is explicitly recorded. No 2,000-realization outcomes were loaded for algorithm selection and no physical realizations were generated. The frozen formal GA configuration and sequence remain unchanged.

Negative paired differences favor the first-named method/setting. The replication unit is the optimizer seed, conditional on the same 64 planning states. Tables retain paired means, medians, SD, wins/losses/ties, pointwise t intervals, 20,000 seed-block bootstrap intervals and Bonferroni simultaneous intervals. These intervals concern optimizer variability, not physical population uncertainty. No equivalence margin was invented, and an interval containing zero is not evidence of equivalence.
"""
    write('GA_PARAMETER_DEFENSIBILITY_REPORT.md',f"""
# GA Parameter Defensibility Report

## Authority and Scientific Boundary

Starting commit `{START}`, isolated branch `{BRANCH}`. {common}

The frozen objective is mean population-dependency-weighted service-loss hours across the original 64 2pc50/C57_D1 planning realizations. Station availability includes its own restoration, the 0.5 functionality threshold and connection to an active Core source. Directed travel, realization-specific damage and repair durations, crews, graph and population mapping are unchanged. The original compiled horizon remains 2855.2540131100995 h; the pre-existing planning horizon audit establishes zero post-480 loss for these fixed inputs, so this does not redefine the manuscript integral. This is not delivered MW, a capacity model, or a new fragility model.

## Parameter Decisions

{md(ga,['parameter','selected_value','classification','supports'])}

The full matrix includes ten required audit dimensions per selection. SUPPORTED means support for an appropriate design/operator under tested conditions; it does not mean a universal optimum. Exact probabilities, population, composition, tournament size and elite count remain qualified fixed choices.

## Population and Selection

The same-budget 100k studies do not establish superiority of 100 over 50/250/500. Their initial compositions differ (heuristic/prior/neighbors/random): 7/1/12/30, 7/1/25/67, 7/1/62/180 and 7/1/125/367. Population comparisons therefore concern those packages, not pure population effects. At fixed distinct work, larger populations also execute fewer generations.

The older five-seed, 50k-query P100 inversion/no-elite screen had mean loss 33.126443 h at mutation 0.20, versus 33.572881 at 0.40 and 33.577103 at 0.60. These high-rate failures are retained as historical setting-specific evidence. They are not tests of final swap mutation at those probabilities. Similarly, early crossover 0.60/0.95 screens also changed mutation and cannot establish a pure crossover effect. The later nine-variant, fresh 20-seed 100k comparison isolates crossover 0.60/0.95 and swap mutation 0.05/0.20 against their reference probabilities; full effects and simultaneous intervals are in the matrix and HISTORICAL_PAIRED_STATISTICS.csv.

Tournament-2 deterioration is materially larger than unresolved small setting differences: +0.026100 h with nine-family simultaneous interval approximately [0.014669, 0.037531] at 100k. Tournament-5 beat 3 in the 20k factorial screen but not conclusively in fresh 100k or 500k contrasts. The independent 100k interaction estimates are population x tournament -0.000224304, tournament x mutation +0.000149262, and neighbor allocation x tournament +0.000182864 h; their intervals all cross zero. At 500k k5-minus-k3 is +0.000693217 h, interval [-0.000966832, 0.002353265]. Retaining k3 is defensible, not proof that k5 is inferior.

Legacy P500 underperformance cannot be attributed solely to weak tournament pressure or insufficient diversity. Its measured standardized parent intensity is approximately 0.804 versus 0.564 at P100, final positional entropy 0.835 versus 0.312, and effective parent count 179.09 versus 37.42. Larger raw diversity did not imply useful order exploration. The original reference chromosomes left the evolving population early while the passive best archive persisted. Subsequent quality initialization, survival and operator changes materially altered that behavior. Source: historical ORIGINAL_HISTORY_MECHANISM_SUMMARY.csv; new per-seed evidence NEW_GA_SEARCH_HISTORY_MECHANISMS.csv.

## Direct Elite-Count Experiment

The former no/one/three-elite screens partly changed other settings. The missing fixed-configuration 0/1/2/3 intervention was therefore executed: eight 20k seeds, then twenty independent 100k seeds. Initial-population fingerprints and post-initializer RNG states agree across all elite counts in every confirmation seed. Elite survival overwrites the offspring tail after the same reproduction draws; later trajectories can diverge. The archive itself does not inject a parent when restart is disabled.

{md(effects[effects.family.eq('confirmation_ga_elite')],['contrast','mean_delta_hr','simultaneous95_low_hr','simultaneous95_high_hr','wins','losses','ties'])}

No-elite final output remains protected by best-observed retention. That is not evidence the evolving population retained or improved the archived chromosome. Conversely, better output with an injected prior does not establish that evolutionary reproduction independently discovered it. Generational survival and passive retention have different causal roles in the algorithm.

## Initialization versus Search

Impact-first J=33.57830255999924 h; prior optimized J=33.03813174326729; frozen selected J=32.997840773882714. The inherited prior gain is {inherited['prior_gain_vs_impact_hr']:.12f} h; the selected post-prior gain is {inherited['selected_post_prior_gain_hr']:.12f} h; total {inherited['total_gain_hr']:.12f} h. Thus {100*inherited['inherited_fraction']:.2f}% of that aggregate gain already existed in the supplied prior. This decomposition is relative to the exact prior, not a claim that all neighboring generation-zero populations equal it; original per-seed initial bests are retained.

The seven references are centrality, Impact (population), betweenness, degree, closeness, hospital and the retained random-reference sequence. The prior is one independently documented older optimized chromosome. Even-numbered neighbors use that prior (13), odd-numbered neighbors use Impact (12), with one inclusive inversion each. Random fill uses 67 fresh permutations. Initializer duplicates are allowed and counted. The older prior's search cost is not part of the final 100k/500k budget and must not be described as free end-to-end optimization.

The prior-discovery record is extended_ga_20261008/p100_g2000_s46/RUN.json: 81,187 distinct candidates and 138.831 s for that run. This is only one component of prior development, not its total screening/selection cost. It is already represented in the historical inventory and must not be added a second time. Historical shared memoization, continuations and missing CPU counters retain their original qualifications rather than being relabeled as new local work.

Removing the exact prior copy alone leaves prior-derived neighbors. Removing prior and all its neighbors changes random fill and RNG consumption, not merely a Boolean injection. The preserved ablations show a substantial 20k disadvantage of removal (+0.007447 h) that weakens at 100k (+0.001609; simultaneous interval [-0.000365, 0.003583]). Cold searches may catch up. The exact 7/1/25/67 composition is a reproducible mixture, not a calibrated mathematical optimum.

## Budget, Duplication and Stochastic Selection

Formal protocol: twenty seeds 42-61 at 100k, with fixed 42-46 continued to 500k. There are 20 independent seeds, not 25; nominal distinct work is 4 million, not 4.5 million. Best-observed chromosomes at exact query boundaries are distinguished from the completed-generation archive. Fixed extensions do not use validation to select seeds or stopping.

Historical 500k GA k3 gained on only 3/10 seeds between 100k and 250k (mean 0.000149859 h), and 0/10 between 250k and 500k. ILS gained on 8/10 and 7/10 (mean 0.002788896 and 0.000473178 h). Flat GA traces establish tested-budget saturation, not global optimality. Higher attempted-query and bookkeeping overhead remains an important weakness of the tested GA.

The minimum across multiple searches is a selected development result. Seed distributions and conditional uncertainty quantify stochastic search variation; they do not remove winner selection or physical-sample sensitivity. The fixed sequence's completed independent validation supports its reported performance, not exact parameter optimality.

## Scope and Remaining Limits

The original GA remains a defensible reproducible finite-budget reference; universal superiority, global optimum, exact hyperparameter optimum, and independently discovered total gain are unsupported. PMX/cycle, adaptive mutation, restart and crowding have only background-specific pilot evidence, not exhaustive powered comparisons under every final setting. Pure population effects holding initializer count and RNG schedule fixed remain unresolved. Archive-copy and retained-reference counts measure exact-sequence survival, not full descendant genealogy; no unrecorded lineage claim is inferred. Nothing in this diagnostic package retroactively promotes a new configuration.

Numerical sources: GA_PARAMETER_EVIDENCE_MATRIX.csv, HISTORICAL_PAIRED_STATISTICS.csv, original parameter/initialization seed tables, new GA_PARAMETER_CONTROLLED_RESULTS.csv and PAIRED_PARAMETER_CONTRASTS.csv. Reproduction: REPRODUCIBILITY.md and source-hash manifests.
""")
    best_swap=confirm.loc['ils_swap minus ils_mix']
    swap_ga=confirm.loc['ils_swap minus ga_elite1']
    swap2000_ga=confirm.loc['ils_swap_stag2000 minus ga_elite1']
    swap2000_mix=confirm.loc['ils_swap_stag2000 minus ils_mix']
    operator_interaction=confirm.loc['swap x stagnation2000']
    swap_supported=best_swap.simultaneous95_high_hr<0
    screen_no_perturb=effects[(effects.family=='screen_ils_confirmation')&
        (effects.contrast=='ils_no_perturb minus ils_mix')].iloc[0]
    write('ILS_PARAMETER_DEFENSIBILITY_REPORT.md',f"""
# ILS Parameter Defensibility Report

{common}

## Actual Algorithm, Not Informal Shorthand

Warm ILS starts its current sequence at the same declared prior available to GA; seven reference evaluations are charged and eligible for best-so-far retention. Cold ILS starts at Impact; cold GA excludes the optimized prior and prior-derived neighbors but keeps Impact neighbors and random fill. They share allowed prior information, not identical candidate populations or RNG consumption. Initial chromosomes and fingerprints are retained.

For each local proposal, select swap, insertion or inclusive inversion uniformly; accept only fitness greater than current + 1e-12. Rejected proposals, including cache hits, increment stagnation. After 800 such attempts, perturb global best by 2, 4 or 8 sequential primitive moves cyclically and evaluate the final permutation. The perturbed current state may worsen; archive best cannot worsen. Those move counts are not kilometers, rank distance, counts of distinct changed stations or additional objective evaluations; mutations may cancel. Each search begins with an empty cache. No validation states participate.

The exact original-wrapper versus instrumented mixed-ILS short parity matches sequence, loss, attempts, accepted moves and restarts. Single-operator variants deliberately remove the random mixture-choice draw and therefore do not pretend to preserve identical later RNG streams.

## Completed Sensitivity, Including Negative Evidence

Engineering screen: 16 configurations x 8 independent seeds x 20k, all completed. All three stagnation values 200/800/2000 and perturbation cycles 1/2/4, 2/4/8 and 4/8/16 were screened. The lowest predeclared pair means selected 2000 and 4/8/16 for fresh confirmation. The additional swap x 2000 and swap/no-perturb mechanisms were committed before confirmation, after the separate screen. Confirmation has 16 cases x 20 seeds, with a target of 100k each. Accessible no-perturb controls that hit the 60x attempted-call safety cap are retained as incomplete, not equal-budget quality evidence.

{md(c,['case','n','mean_hr','sd_hr','best_hr','mean_distinct','mean_attempts','mean_wall_seconds','completed_budgets'])}

{effect_text}

Swap-minus-mix: {describe(best_swap)}. Simultaneous support for lower swap mean in this confirmation is **{swap_supported}**. Regardless of significance, three operators are not automatically required. No additional two-operator mixture was launched: the predeclared individual-neighborhood screen already supported the more parsimonious single-swap check, and adding an unmotivated mixture grid would not answer a distinct mechanism.

The screen-selected settings are assessed on independent seeds, not evaluated with reused favorable screening seeds. Their precise values are not proven optimal. The focused difference-of-differences estimates whether operator performance changes with stagnation threshold; it does not generalize to untested perturbation schedules.

The completed equal-20k mixed-neighborhood no-perturbation screen gives {describe(screen_no_perturb)}. This is an engineering-screen result, not an independent confirmatory contrast. At 100k, accessibility truncation prevents an equal-distinct-work quality claim for that control. Perturbation can enable further new-order scoring without being proved better by an unfair comparison to an incomplete local search.

## Deterministic Refinement Is a Separate Stage

Historical selected seed 304 stochastic ILS achieved 32.9971211516713 h. The additional deterministic neighborhood search used 132,545 distinct scores and seven accepted improvements to reach 32.99613736538884 h. Comparing that refined result to 100k GA without the extra cost would be unfair.

This study executed refinement from the first five prospectively fixed independent mixed-ILS 100k seeds, rather than selecting the best five. Original four-family scans and the 1e-9 improvement tolerance were retained, with a maximum of 150k additional distinct evaluations. For every seed the corresponding GA 100k search was continued to the same total distinct budget by deterministic prefix replay; its 100k prefix reused cached scores, not a repeated full-64 calculation. Replay overhead remains in wall time. The replayed 100k sequence hash, loss and initializer fingerprints are checked against the original prefix. The companion CSV includes complete base-plus-refinement and base-plus-GA-replay wall time.

{md(refine,['seed','base_loss_hr','refined_loss_hr','refinement_additional_distinct','refinement_accepted_moves','refinement_wall_seconds','scan_complete','joint_budget','ga_joint_loss_hr'])}

{md(ref_effects,['contrast','mean_delta_hr','simultaneous95_low_hr','simultaneous95_high_hr','wins','losses','ties'])}

A complete tested-neighborhood scan is a local certificate under those four neighborhoods and tolerance only. An incomplete budget-capped scan is not a certificate. Refinement is not part of base stochastic ILS and must be named and charged separately. The refined-versus-base gain is an incremental additional-work result, not an equal-budget causal advantage over simply continuing stochastic ILS. That latter five-seed intervention was not separately tested; the matched-total-budget GA comparison answers a different question.

## Simplicity and Presentation

ILS avoids population size, crossover and parent-selection settings. Original ILS nevertheless requires neighborhood set/weights, acceptance tolerance, stagnation unit/threshold, perturbation strengths/cycle, restart reference, initialization, archive, budget/safety cap and optional refinement policy. Single-swap removes neighborhood-mixture choices but retains perturbation and stopping settings. No-perturb is genuinely simpler but may repeatedly exhaust its finite accessible neighborhood before equal distinct work, and is not assumed equivalent because an interval crosses zero.

The parameter matrix provides adequate conditional study of the requested factors; it does not prove a universal ILS optimum. Main-paper Scope A remains the cleanest defensible presentation: diagnostic optimizer-family check with fixed original settings, matched budgets, inheritance and limitations. This new prospective diagnostic calibration can receive full supplemental treatment, but cannot be described as independently validated paper-method replacement. Scope B is feasible as a clearly postvalidation development appendix, not an authorized formal method promotion.
""")
    write('GA_ILS_METHOD_CHOICE_DECISION.md',f"""
# GA-ILS Method Choice Decision

## Formal Method Remains Frozen

Retain the already validated GA configuration and sequence. This is a preservation decision, not an assertion that it beats every newly calibrated algorithm. No new candidate was scored on the completed 2,000-realization validation cohort.

## Matched Comparisons

{md(effects[effects.family.str.contains('confirmation_method')],['contrast','mean_delta_hr','simultaneous95_low_hr','simultaneous95_high_hr','wins','losses','ties','paired_mean_wall_ratio'])}

The four original method/information contrasts form the prospectively declared family. The two reduced-neighborhood ILS-versus-GA contrasts are an additional retrospective exploratory family on the already planned 20 paired seeds, not a newly preregistered confirmatory result. They require no additional search runs and are not independent physical validation.

Shared warm comparisons give both methods the same optimized prior; cold comparisons exclude it and prior-derived neighbors. The initial candidate generation operations differ and are documented, so cold/warm effects include their composition and RNG changes. Equal distinct budgets do not imply equal attempted-query work, CPU or wall time. Local measured wall time includes diagnostic observation: GA records per-generation diversity/history, whereas ILS has no evolving-population history. Objective scoring time is retained separately; nonobjective time cannot be attributed wholly to intrinsic algorithm overhead. Attempted-query reduction is directly measured, but the wall ratio is an instrumented implementation comparison, not an instrumentation-free universal speedup.

Historical 100k mixed-ILS minus GA mean +0.001298265 h, simultaneous interval [-0.00013347, 0.00273000]; historical 500k -0.001101224 h, interval [-0.002591758, 0.000389309], with 7/10 wins. These are conditional empirical comparisons, not universal superiority. Tested simulated annealing and LNS configurations performed worse but do not invalidate all non-GA optimizers. Completed scheduling/actionable-delay evidence supersedes older notes saying LNS was untested.

New single-swap versus mixed: {describe(best_swap)}. Base, refinement and continued-GA costs remain separate. The five-seed joint-budget table is MULTISEED_REFINEMENT_AND_MATCHED_GA.csv. Best-found quality, average quality, variability, duplicate overhead and per-state influence are different questions; a low selected minimum cannot settle method choice.

## Paper Scope

The stronger reduced-neighborhood findings must not be hidden behind the older unresolved mixed-ILS comparison. Single-swap ILS versus GA gives {describe(swap_ga)}; swap with stagnation 2000 versus GA gives {describe(swap2000_ga)}. These direct GA comparisons were added retrospectively on already planned cases and belong to their separate two-contrast exploratory family. Within the prospective nine-contrast ILS family, the swap/2000 package versus original mixed/800 gives {describe(swap2000_mix)}. The focused operator-by-stagnation interaction is {describe(operator_interaction)}; an improved package is not proof of interaction synergy or a uniquely optimal threshold.

Recommend **Scope A**, diagnostic alternative in the main paper, with the complete calibration sensitivity preserved in Supplementary Information. Original ILS's several neighborhood/restart/refinement settings are not demonstrably trivial just because only one current sequence is stored. A single-swap implementation is a credible reduced-neighborhood diagnostic under the studied model, not a validated new policy. Scope B is supported as a calibrated conditional development comparison in Supplementary Information; its placement as a substantive main-paper extension requires an explicit author decision. The fresh twenty-seed algorithmic confirmation was completed here. Claims of physical generalization for the new settings would require appropriate independent evidence, not reuse of the old validation cohort as untouched confirmation.

The completed parameter evidence warrants substantive supplemental presentation of reduced-neighborhood ILS rather than only a weak untuned baseline. The main text should acknowledge that it achieved lower conditional development means and fewer attempted lookups. The simpler base method omits population/crossover/tournament choices and neighborhood-mixture weights, but still requires a stagnation threshold, perturbation cycle, restart reference, initializer, archive and budget. Scope A describes its paper role, not absence of a calibration audit; Scope B remains scientifically supportable as a clearly bounded postvalidation methods appendix, not independently validated formal-policy replacement.

## Validation and Physical-Sample Sensitivity

Previously frozen GA-minus-Impact validation mean -0.501901635445 h, 95% interval [-0.524975128718, -0.479472230142]; refined-ILS-minus-frozen-GA mean -0.024549091909 h while ILS worsened 69.6% of realizations. These aggregates were provided with the task; this study did not access their realization outcomes. They describe the frozen sequences, not parameter selection, calibration superiority, capacity or universal robustness.

Historical refined planning advantage is influential-state sensitive: 14/64 improvements and 50 worsening, with omission of realization 15 reversing the mean difference to +0.030758169262 h. Internal 48/16 crossfit produced 16/20 ranking reversals; folds already belonged to the development collection. New candidate production and leave-one-out evidence are retained, not used to redefine the mean objective or retroactively choose a different physical loss.

## Independently Checked New Candidates

The eight lowest verified development objectives are shown below. Negative deltas favor the diagnostic sequence over the frozen GA. Complete 92-station orders, hashes and origins are in IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; this selected-minimum table is not an unbiased optimizer comparison. Omission diagnostics remove planning states only from the comparison, not from the authoritative objective or search.

{candidate_table}

Differences of 0.001 normalized service-loss hour correspond to 3.6 seconds of equivalent population-weighted deficit duration. They are not 0.001 person-hours, delivered electrical energy, or a promise that every household is restored sooner.
""")
    questions=[
        ('Why a permutation GA?', 'The decision is a valid priority order decoded by the unchanged nonlinear scheduler. GA is a practical finite-budget order-search method, not a global proof. Reasonable ILS comparators were actually tested.'),
        ('How are orders valid?', 'Each chromosome contains each of the 92 pinned IDs once. Swap/insertion/inversion and OX/PMX/cycle preserve the domain; property tests and every retained final sequence identity are verified.'),
        ('Why ordered crossover?', 'OX preserves the copied segment and cyclic donor order without duplicate stations. Existing PMX/cycle pilots use an inversion background; they do not establish universal final-swap superiority.'),
        ('Why swap mutation?', 'Same-initialization operator evidence supports swap under tested settings. Legacy-to-final changes also alter mutation probability and must not be attributed solely to swap.'),
        ('Why probabilities .80/.10?', 'Fresh 20-seed 100k .60/.80/.95 crossover and .05/.10/.20 swap comparisons justify tested operating choices. Intervals overlap zero for close alternatives; no exact optimum/equivalence claim is warranted.'),
        ('Why population 100?', 'A reproducible middle reference; equal-query 50/250/500 differences are small/unresolved and initializer composition changes. Legacy P500 failure is not intrinsic P500 inferiority.'),
        ('Why tournament 3?', 'Tournament-2 adds about .026100 h, simultaneous [.014669, .037531]. k5 short-screen benefit is not conclusively reproduced at 100k/500k. Histories quantify actual intensity/diversity rather than assuming it.'),
        ('Why one elite?', 'Archive protects output; elite protects a breeding chromosome. New fixed-configuration 0/1/2/3 confirmation isolates this intervention; see the full three-contrast table, without claiming one is uniquely optimal.'),
        ('Why mixed initialization?', 'Seven references, one exact older prior, 13 prior/12 Impact inversion neighbors, and 67 random permutations. It combines declared inherited quality and search breadth. Copy removal alone retains prior information in neighbors.'),
        ('How much gain is inherited?', f"Prior gain {inherited['prior_gain_vs_impact_hr']:.12f} h; additional selected gain {inherited['selected_post_prior_gain_hr']:.12f} h. About {100*inherited['inherited_fraction']:.2f}% already existed in the prior, with per-seed generation-zero improvements reported separately."),
        ('Why the budget/stopping?', 'Distinct full-64 scores represent expensive work; duplicates, attempts and time are also reported. Twenty 100k runs plus five continuations to 500k total 4 million evaluations across 20 independent seeds. Plateau is not global convergence; fixed budgets were not validation-tuned.'),
        ('Were parameters developed on planning states?', 'Yes. All tuning and new exploratory comparisons use the same 64 development realizations. Conditional optimizer-seed intervals are not untouched physical validation.'),
        ('How was stochastic variability controlled?', 'Paired optimizer seeds; screen/confirmation disjoint; bootstrap seed blocks and simultaneous families; failures/incomplete controls retained. No chromosome or checkpoint pseudoreplication.'),
        ('Is the best chromosome lucky?', 'It is selected from a prespecified multi-seed search, so optimism is possible. Report the distribution and independent frozen-sequence result, not selected minimum as unbiased optimizer performance.'),
        ('Is GA demonstrably superior?', 'Not universally. Mixed ILS is competitive at 100k/500k; a reduced single-swap ILS receives a fresh controlled audit. Weak SA/LNS settings cannot prove superiority over all alternatives.'),
        ('What does independent validation establish?', 'Performance of already frozen sequences under the specified sample design; not exact hyperparameter optimum, new postvalidation calibration, capacity, or robustness in every physical state.'),
        ('Can it be reproduced?', 'Pinned model/input/source hashes, seed configurations, exact 92-station permutations, actual budgets/costs, RNG/initializer fingerprints, archive records, code/tests and downloaded LFS verification. Runtime-dependent wall time is not bitwise reproducible.'),
    ]
    write('REVIEWER_OBJECTIONS_AND_EVIDENCE.md','# Reviewer Objections and Evidence\n\n'+
          '\n\n'.join(f'## {j}. {q}\n\n{answer}\n\nEvidence: '+
            ('GA_PARAMETER_EVIDENCE_MATRIX.csv; HISTORICAL_PAIRED_STATISTICS.csv; PAIRED_PARAMETER_CONTRASTS.csv.' if j<=11 else
             'GA_ILS_METHOD_CHOICE_DECISION.md; EXECUTION_ACCOUNTING.json; IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json; REPRODUCIBILITY.md.')
            for j,(q,answer) in enumerate(questions,1)))
    write('METHODS_AND_SUPPLEMENT_READY_TEXT.md',f"""
# Methods and Supplement Ready Text

## Main Methods: Frozen Algorithm

We represented recovery priority as a permutation of 92 substations and evaluated each order using the fixed realization-specific crew scheduler, directed travel and source-connected service model. Fitness was the negative mean population-weighted service-loss integral over 64 planning realizations. Genetic search used 100 chromosomes, reciprocal ordered crossover with probability 0.80 per parent pair, two-position swap mutation with probability 0.10 per child, tournament selection of size 3 and one surviving parent elite. Each tournament sampled with replacement; exact ties retained the first draw. The best distinct parent, with lexicographic tie-breaking, replaced the final offspring after reproduction. Passive best-so-far retention was separate from generational elite survival.

Initial populations comprised seven retained heuristic orders, one previously optimized order, 25 single-inversion neighbors (13 from that prior and 12 from Impact-first), and 67 random permutations. This starting information was disclosed rather than treated as an improvement newly discovered by genetic search. Relative to Impact-first, the prior supplied {inherited['prior_gain_vs_impact_hr']:.6f} h of the total {inherited['total_gain_hr']:.6f} h selected planning gain; subsequent optimization supplied {inherited['selected_post_prior_gain_hr']:.6f} h. Search used 20 seeds at 100,000 distinct order evaluations, with five fixed seeds continued to 500,000. Repeated cached lookups were excluded from the expensive-query budget but included in attempted calls and time. The selected minimum is a development result, not an estimate of universal optimizer superiority or global optimality.

## Main Methods: Diagnostic Alternative

An iterated local-search comparator used the same planning objective and declared prior information. It selected swap, insertion or inversion proposals uniformly and accepted strict improvements (1e-12 numerical tolerance). After 800 attempted non-improving proposals, including cache hits, it perturbed the retained best by cyclic 2/4/8 primitive moves. The final perturbed sequence alone was scored; the current sequence could worsen while the best remained retained. Deterministic multi-neighborhood refinement, when reported, was a separate additional-budget stage. Equal distinct-query comparisons retained attempted work and wall time. Neither optimizer family was assumed universally superior.

## Supplement: Parameter Evidence and Postvalidation Audit

Earlier paired-seed studies tested population packages, crossover/mutation probabilities, tournament pressure, operator alternatives, initialization ablations and parameter interactions. Population comparisons changed initializer composition and were not interpreted as pure population effects. Small unresolved differences justified a reproducible reference, not exact optimality or equivalence. Weak tournament-2 selection deteriorated by approximately 0.026100 service-loss h relative to tournament-3, whereas close 3/5 comparisons remained budget- and setting-dependent.

After frozen-sequence independent validation, a separate prospectively registered diagnostic audit executed 128 engineering cases and 320 targeted confirmation cases using eight screening and twenty fresh confirmation seeds. It directly tested elite counts 0/1/2/3, individual versus mixed ILS neighborhoods, stagnation, perturbation, restart reference and warm/cold prior access. Incomplete no-perturbation cases were retained as neighborhood-accessibility diagnostics, not equal-budget optimizer replications. All new algorithmic conclusions are postvalidation development findings and were not tested on the old validation cohort.

{md(effects[effects.family.eq('confirmation_ga_elite')|effects.family.eq('confirmation_method')],['contrast','mean_delta_hr','simultaneous95_low_hr','simultaneous95_high_hr','wins','losses','ties'])}

Five preselected independent ILS seeds received deterministic refinement and corresponding equal-total-distinct-budget GA continuation. A final exhaustive tested-neighborhood scan certifies only local non-improvement under its specified neighborhoods and tolerance. Per-state production parity, leave-one-out influence and cost accounting were retained. Optimizer-seed confidence intervals are conditional on fixed physical planning states; checkpoints, chromosome evaluations and overlapping seed phases are not independent replications. No new physical realizations were generated.

## Claims Not Authorized by This Evidence

Do not describe exact parameters as optimal, the total gain as independently discovered by GA, ILS as automatically simpler, the selected planning minimum as unbiased expected performance, or postvalidation candidates as independently validated. Do not promote a new policy, alter formal outputs, or use an influential-sample finding to redefine the original mean objective. This text is a separate review resource, not an in-place manuscript edit.
""")
    write('FINAL_RESEARCH_DECISION.md',f"""
# Final Research Decision

## Completed Work

Reconciled historical inventory and original duplicate/overlap audits; executed the precommitted engineering and independent confirmation studies; ran five fixed-seed deterministic refinements and matched-total-budget GA continuations; independently verified {len(qa['candidates'])} important new 92-station sequences through all 64 production realizations. Their exact permutations, hashes, objectives and influence are in IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json. All are diagnostic, not formal policy replacements.

The strongest new verified development candidate has objective {best_candidate['production_mean_hr']:.14f} h and SHA-256 `{best_candidate['sequence_sha256']}`. It improves {best_candidate['improved_states']}/64 planning realizations but worsens {best_candidate['worsened_states']}/64. Its mean difference from the frozen GA is {best_candidate['mean_minus_frozen_ga_hr']:+.14f} h; excluding realization 15 reverses that difference to {best_candidate['omit_realization15_delta_hr']:+.14f} h. The better planning minimum is therefore not evidence of robust physical generalization or grounds for formal promotion.

## GA Decision

{md(ga,['parameter','classification'])}

The formal fixed method remains scientifically defensible with these qualifications. The missing elite-count comparison was completed instead of deferred. Exact population, probabilities, tournament size, one-elite count and initializer allocation are not certified optima. Background-specific disabled adaptation/restart/crowding and alternative crossovers are documented limitations rather than claims all such mechanisms fail.

## ILS Decision

The requested neighborhoods, three stagnation thresholds, three perturbation cycles, best/current restart, no-perturbation accessibility and a focused operator/stagnation interaction were actually studied. Only screen-selected threshold/strength alternatives received full independent confirmation; the other alternatives retain engineering-screen status. Single-swap has a reduced neighborhood description; its contrast is {describe(best_swap)}. Original multi-operator ILS plus optional refinement is not automatically simpler than GA.

The swap/2000 package improves the original mixed ILS under the prospective confirmation family: {describe(swap2000_mix)}. Direct comparison with GA, {describe(swap2000_ga)}, is a separate retrospective exploratory finding. It provides real conditional evidence for a competitive reduced-neighborhood optimizer, not grounds to continue claiming GA superiority against only weak alternatives. The interaction itself remains unresolved and does not establish synergy.

Recommend Scope A in the main manuscript and the complete parameter audit in supplement. Scope B can be presented as postvalidation methodological development, but requires an explicit editorial decision and cannot inherit untouched validation status. A lower planning minimum alone does not select a formal optimizer.

## Computation and Preservation

{account['search_distinct_calls']:,} new distinct main-batch objective calls; {account['attempted_search_calls']:,} attempted main-batch queries; {account['within_search_cache_hits']:,} duplicate lookups. Refinement adds {account['refinement_distinct_calls']:,} distinct calls, matched GA continuation adds {account['matched_ga_continuation_new_distinct']:,}, and {account['matched_ga_prefix_reused']:,} prefix scores are reused. Setup/parity/export full-64 equivalents: {account['setup_parity_full64_equivalent_calls']:,}; total new full-64 calls: {account['new_expensive_full64_calls']:,}. Additional independent production checks: {account['production_state_calls']:,} single-realization calls, reported as a different unit. Main-batch incomplete controls: {account['incomplete_searches']}. First serializer-only QA failure and its repeated bounded parity work are disclosed and counted.

Screen wall {account['screen_batch_wall_seconds']:.1f}s; confirmation wall {account['confirmation_batch_wall_seconds']:.1f}s; summed worker CPU {account['search_worker_cpu_seconds']:.1f}s. Concurrent worker-wall sums are not elapsed study time. GA cached-prefix replay time is included separately. EXECUTION_ACCOUNTING.json gives the complete ledger.

No physical samples were generated or changed; no completed validation outcomes were used. Before/after protected950-file and revision-index comparisons, formal configuration/sequence and validation artifact hashes are recorded. Source-content checks distinguish Git/LF identities from Windows CRLF working bytes. Publication includes actual remote HEAD and downloaded LFS object verification, not merely local commit success.

## Remaining Insufficient Evidence

No global optimum or exact hyperparameter optimum; no pure population intervention with all initializer and RNG composition held fixed; no powered final-swap comparison of every crossover/adaptive/restart/crowding option; no new untouched physical confirmation of postvalidation settings; no claim that every planning-state improvement is robust to influential-state omission. Five-seed deterministic refinement is a bounded consistency check, not exhaustive optimizer-family validation. All feasible missing targeted studies requested here were completed; these remaining broader questions do not justify an uncontrolled new grid.

## Existing Draft Claims to Qualify

Historical docs/reviewer/FIGURE_S04_S05_S06_INTERPRETATION_20261007.md, GA_SEARCH_BUDGET_SENSITIVITY_20261007.md and EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md describe older version-specific decisions. Do not transfer those decisions to the current frozen method without version labels. Older continuation's 'LNS untested' statement is superseded by completed LNS/actionable-delay packages. Prohibited current claims include globally optimal GA, universal optimizer superiority, all improvement produced after initialization, exact parameters independently validated, or ILS simpler merely because it stores one sequence. No existing manuscript was edited.

EXISTING_METHOD_CLAIM_AUDIT.csv identifies the relevant source lines and distinguishes valid historical statements from claims that would exceed the evidence if used as current Methods. The strongest new development candidates and their sample sensitivity are summarized in IMPORTANT_CANDIDATE_SUMMARY.csv, without promotion.

The proposed frozen-method paragraph in FINAL_GA_METHOD_AUDIT.md line 66 is already bounded: it discloses inherited initialization, finite budgets and no global-optimality proof. It need not be accused of claiming universal superiority. A real wording ambiguity is "Counts exclude generation-zero scoring" in GA_BUDGET_AND_REPLICATION_DECISION.md line 14: this must identify strict improvement counts, because the expensive-query budget does include the seven incumbent scores. Legacy July/inversion/generation-limited descriptions must not be copied into current frozen-method text. This is a source-bounded draft audit, not a claim that an uninspected current manuscript contains every prohibited assertion.

Stop this bounded audit after evidence publication and preservation/remote verification. Do not promote new settings or run the completed validation cohort again.
""")
    graphics()
    print('REPORTS_COMPLETE',flush=True)


def package():
    roots=['screen','confirmation','refinement','prefixes']
    members=[]
    dest=lp(OUT/'RAW_SEARCH_AND_REFINEMENT_EVIDENCE.zip')
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for dirname in roots:
            for p in sorted(lp(OUT/dirname).rglob('*')):
                if not p.is_file(): continue
                name=p.relative_to(lp(OUT)).as_posix()
                archive.write(p,arcname=name)
                members.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
    with zipfile.ZipFile(dest) as archive:
        for m in members:
            payload=archive.read(m['path'])
            assert len(payload)==m['bytes'] and hashlib.sha256(payload).hexdigest()==m['sha256']
    save(OUT/'RAW_EVIDENCE_ARCHIVE_MANIFEST.json',dict(status='PASS',archive_sha256=sha(dest),
        archive_bytes=dest.stat().st_size,members=members,includes_final_permutations=True,
        includes_initializer_and_rng_fingerprints=True,includes_generation_histories=True,
        includes_refinement_checkpoints_and_continuation_cache=True))
    print('PACKAGED',len(members),dest.stat().st_size,sha(dest),flush=True)


def legacy_hashes():
    baseline=read(R/'results/diagnostics/ga_initialization_reconciliation_20261009/PRESERVATION_BASELINE.json')
    revision=Path(read(R/'results/diagnostics/independent_validation_ready_20261010/FINAL_VALIDATION_FREEZE_RECEIPT.json')['protected_revision_checkout'])
    mismatch=[]
    for name,expected in baseline['files_sha256'].items():
        actual=sha(R/name)
        if actual==expected:continue
        data=lp(R/name).read_bytes()
        lf=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
        reference=lp(revision/name).read_bytes()
        reference_sha=hashlib.sha256(reference).hexdigest()
        mixed_eol_match=(reference_sha==expected and
            reference.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n'))
        mismatch.append(dict(path=name,expected_legacy_sha256=expected,actual_working_sha256=actual,
            lf_sha256=lf,line_endings_only=lf==expected or mixed_eol_match,
            protected_revision_reference_sha256=reference_sha,
            normalized_matches_protected_revision=reference.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n'),
            unchanged_task_git_blob=(subprocess.check_output(['git','show',START+':'+name],cwd=R)==
                                     subprocess.check_output(['git','show','HEAD:'+name],cwd=R))))
    save(OUT/'LEGACY_834_BYTE_HASH_RECONCILIATION.json',dict(status='RECONCILED',
        legacy_file_count=len(baseline['files_sha256']),byte_hash_mismatches=mismatch,
        all_mismatches_are_line_endings=all(r['line_endings_only'] for r in mismatch),
        current_task_950_snapshot_is_separate=True,original_files_edited=False))
    print('LEGACY_BYTE_HASH_RECONCILIATION',len(mismatch),'mismatches',flush=True)


def qa():
    design=read(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    universe=set(read(R/'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json')['sequence'])
    rows=[]
    for phase,seeds,cases in (
        ('screen',SCREEN,design['screen_cases']),
        ('confirmation',CONFIRM,design['fixed_confirmation_cases']+
         read(OUT/'SCREEN_SELECTION.json')['cases']+design['cold_cases']+design['screen_mechanism_confirmation_cases'])):
        actual=[]
        for p in lp(OUT/phase).glob('*.json'):
            r=read(p);actual.append((r['case'],r['seed']))
            assert len(r['best_sequence'])==92 and set(r['best_sequence'])==universe
            assert identity(r['best_sequence'])==r['sequence_sha256']
            assert r['attempted_evaluations']>=r['distinct_evaluations']
            assert r['search_best_loss_hr']<=r['initial_best_loss_hr']+1e-9
            assert r['source_sha256'] in {read(OUT/phase/f'{cases[0]}_s{seeds[0]}.json')['source_sha256']}
            assert r['completed_budget']==(r['budget']==r['distinct_evaluations'])
            rows.append(dict(phase=phase,case=r['case'],seed=r['seed'],raw_sha256=sha(p),
                             sequence_sha256=r['sequence_sha256'],completed_budget=r['completed_budget']))
        assert sorted(actual)==sorted((c,s) for s in seeds for c in cases)
    assert not set(SCREEN)&set(CONFIRM)
    assert preservation()==read(OUT/'PRESERVATION_BASELINE.json')
    candidate=read(OUT/'IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json')
    assert candidate['status']=='PASS' and candidate['new_physical_samples']==0
    assert not candidate['formal_candidate_changed'] and not candidate['validation_outcomes_accessed']
    for row in candidate['candidates']:
        assert len(row['sequence'])==92 and set(row['sequence'])==universe
        assert identity(row['sequence'])==row['sequence_sha256']
        assert row['maximum_parity_error_hr']<1e-8
    archive=read(OUT/'RAW_EVIDENCE_ARCHIVE_MANIFEST.json')
    assert archive['status']=='PASS'
    assert sha(OUT/'RAW_SEARCH_AND_REFINEMENT_EVIDENCE.zip')==archive['archive_sha256']
    assert lp(OUT/'RAW_SEARCH_AND_REFINEMENT_EVIDENCE.zip').stat().st_size==archive['archive_bytes']
    visual=read(OUT/'FIGURE_VISUAL_QA.json')
    assert visual['status']=='PASS'
    for name,record in visual['images'].items():
        assert sha(OUT/name)==record['sha256']
    unit=read(OUT/'UNIT_TEST_QA.json')
    assert unit['final_focused_rerun']['passed']==9 and unit['final_focused_rerun']['failed']==0
    assert unit['final_ast_parse']['status']=='PASS'
    assert read(OUT/'LEGACY_834_BYTE_HASH_RECONCILIATION.json')['all_mismatches_are_line_endings']
    source_rows=[]
    frozen=read(R/'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json')
    for name,expected in frozen['source_git_blob_sha256'].items():
        current=subprocess.check_output(['git','show','HEAD:'+name],cwd=R)
        digest=hashlib.sha256(current).hexdigest()
        # Diagnostics evolved before this task; compare this task's base for preservation separately.
        base=subprocess.check_output(['git','show',START+':'+name],cwd=R)
        assert current==base
        source_rows.append(dict(path=name,current_git_blob_sha256=digest,frozen_candidate_git_blob_sha256=expected,
            unchanged_from_task_start=True,working_sha256=sha(R/name),
            lf_working_sha256=hashlib.sha256(lp(R/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()))
    required=['EXPERIMENT_INVENTORY.csv','GA_PARAMETER_EVIDENCE_MATRIX.csv','ILS_PARAMETER_EVIDENCE_MATRIX.csv',
        'PARAMETER_SELECTION_REGISTER.json','GA_PARAMETER_CONTROLLED_RESULTS.csv','ILS_PARAMETER_CONTROLLED_RESULTS.csv',
        'GA_ILS_EQUAL_BUDGET_COMPARISON.csv','OPTIMIZER_CONVERGENCE_AND_COST.csv','EXPERIMENT_DESIGN_AND_SEEDS.json',
        'GA_PARAMETER_DEFENSIBILITY_REPORT.md','ILS_PARAMETER_DEFENSIBILITY_REPORT.md','GA_ILS_METHOD_CHOICE_DECISION.md',
        'REVIEWER_OBJECTIONS_AND_EVIDENCE.md','METHODS_AND_SUPPLEMENT_READY_TEXT.md','FINAL_RESEARCH_DECISION.md']
    assert all(lp(OUT/n).stat().st_size>0 for n in required)
    receipt=dict(status='PASS',starting_commit=START,branch=BRANCH,screen_cases=128,confirmation_cases=320,
        complete_case_seed_sets=True,sequence_and_record_hashes_verified=True,raw_records=rows,
        source_content_and_line_endings=source_rows,protected_file_count=950,protected_before_after_equal=True,
        preservation_snapshot_sha256=sha(OUT/'PRESERVATION_BASELINE.json'),
        formal_sequence_sha256=frozen['selected']['sequence_sha256'],
        formal_configuration_file_sha256=sha(R/'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json'),
        no_validation_outcomes_accessed=True,new_physical_samples=0,new_candidate_promotion=False,
        production_candidate_qa_sha256=sha(OUT/'IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json'),
        accounting_sha256=sha(OUT/'EXECUTION_ACCOUNTING.json'),required_deliverable_sha256={n:sha(OUT/n) for n in required},
        raw_archive_manifest_sha256=sha(OUT/'RAW_EVIDENCE_ARCHIVE_MANIFEST.json'),
        unit_test_receipt=unit,figure_visual_review=visual)
    save(OUT/'REPRODUCIBILITY_AND_PRESERVATION_QA.json',receipt)
    print('QA_PASS',len(rows),'new main cases; protected950',flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('task',choices=['reports','package','legacy_hashes','qa'])
    globals()[p.parse_args().task]()


if __name__=='__main__':main()
