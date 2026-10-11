"""Generate scoped evidence tables/reports from completed, frozen diagnostic runs."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import subprocess
import zipfile

import numpy as np
import pandas as pd
import numba
import networkx as nx
import scipy

from la_grid.diagnostics.standalone_ils_20261010 import R, OUT, MAIN, EXTEND, BUDGETS, CONFIG, read, save, sha, hydrate, preservation, load_model
from la_grid.diagnostics.standalone_ils_analysis_20261010 import csv


def md(name, value):
    (OUT / name).write_text(value.strip()+'\n', encoding='utf-8', newline='\n')


def hydration_audit():
    hydrated = []
    names = subprocess.check_output(['git','diff','--name-only','-z'], cwd=R).decode().split('\0')
    for name in filter(None,names):
        if name.startswith(('src/la_grid/diagnostics/standalone_ils_', 'tests/test_standalone_ils_',
                            'results/diagnostics/standalone_ils_final_method_20261010/')):
            continue
        blob = subprocess.check_output(['git','show','HEAD:'+name], cwd=R)
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
            fields = dict(s.split(' ',1) for s in blob.decode().splitlines())
            expected = fields['oid'][7:]
            assert sha(R/name) == expected, name
            hydrated.append(dict(path=name, original_lfs_sha256=expected, actual_sha256=sha(R/name),
                staged_for_this_study=False))
        else:
            assert hashlib.sha256(blob).hexdigest() == sha(R/name), name
    save(OUT / 'ISOLATED_HYDRATION_QA.json',dict(status='EXACT_ORIGINAL_PAYLOADS_PASS', rows=hydrated,
        original_revision_checkout_modified=False, scoped_commit_does_not_include_hydrations=True))
    print('HYDRATION_QA_PASS',len(hydrated),flush=True)


def mechanism():
    """Compare saved event traces; do not claim station-level causation."""
    ils = read(OUT / 'SAMPLE15_ILS_EVENTS.json')
    ga = read(OUT / 'SAMPLE15_FrozenGA_EVENTS.json')
    a = pd.DataFrame(ils['station_schedule']).set_index('station')
    b = pd.DataFrame(ga['station_schedule']).set_index('station').reindex(a.index)
    assert (a.damage_state == b.damage_state).all() and np.array_equal(a.duration_hr, b.duration_hr)
    delta = a.finish_hr-b.finish_hr
    times = np.unique([e['time_hr'] for trace in (ils,ga) for e in trace['events']] + [480.])
    times = times[times <= 480.]
    clocks = {name: np.asarray([e['time_hr'] for e in trace['events']]) for name,trace in [('ILS',ils),('GA',ga)]}
    rows = []
    for t,u in zip(times[:-1], times[1:]):
        x = ils['events'][np.searchsorted(clocks['ILS'], t, side='right')-1]
        y = ga['events'][np.searchsorted(clocks['GA'], t, side='right')-1]
        only_ils = sorted(set(x['source_connected_stations'])-set(y['source_connected_stations']))
        only_ga = sorted(set(y['source_connected_stations'])-set(x['source_connected_stations']))
        rows.append(dict(start_hr=t, end_hr=u,
            ILS_minus_GA_loss_hr=(u-t)*(y['effective_service']-x['effective_service']),
            ILS_effective_service=x['effective_service'], GA_effective_service=y['effective_service'],
            ILS_active_sources=';'.join(x['active_sources']), GA_active_sources=';'.join(y['active_sources']),
            ILS_only_source_connected=';'.join(only_ils), GA_only_source_connected=';'.join(only_ga),
            ILS_only_dependency_mass=float(a.loc[only_ils].population_dependency_mass.sum()),
            GA_only_dependency_mass=float(a.loc[only_ga].population_dependency_mass.sum())))
    intervals = pd.DataFrame(rows)
    audit = read(OUT / 'PRODUCTION_PARITY_AND_SAMPLE_INFLUENCE.json')['comparisons']['FrozenGA']
    assert abs(intervals.ILS_minus_GA_loss_hr.sum()-audit['sample15_delta_hr']) < 1e-8
    csv('SAMPLE15_EXACT_INTERVAL_DIFFERENCES.csv', intervals)
    station = pd.DataFrame(dict(station=a.index, damage_state=a.damage_state.values,
        ILS_finish_hr=a.finish_hr.values, frozen_GA_finish_hr=b.finish_hr.values,
        ILS_minus_GA_finish_hr=delta.values, ILS_crew_index=a.crew_index.values, frozen_GA_crew_index=b.crew_index.values,
        ILS_travel_hr=a.travel_hr.values, frozen_GA_travel_hr=b.travel_hr.values,
        source=a.source.values, population_dependency_mass=a.population_dependency_mass.values))
    csv('SAMPLE15_STATION_TIMING_DIFFERENCES.csv', station)
    top = intervals.nsmallest(8, 'ILS_minus_GA_loss_hr')
    selected_columns = ['start_hr','end_hr','ILS_minus_GA_loss_hr','ILS_effective_service','GA_effective_service',
        'ILS_only_dependency_mass','GA_only_dependency_mass']
    md('SAMPLE15_SCHEDULING_MECHANISM.md', f"""# Realization 15: Whole-Schedule Event Accounting

Selected standalone ILS minus frozen GA loss: {audit['sample15_delta_hr']:+.12f} h. Exact changes: self {audit['sample15_component_delta_hr']['L_self']:+.12f}, threshold {audit['sample15_component_delta_hr']['L_threshold']:+.12f}, source {audit['sample15_component_delta_hr']['L_source']:+.12f} h. This is the same physical state and duration vector, not new sampling or a modified objective.

Station completion: {int((delta < -1e-9).sum())} earlier, {int((delta > 1e-9).sum())} later, {int((delta.abs() <= 1e-9).sum())} unchanged. Mean completion change {delta.mean():+.9f} h over stations with finite completion values. Total directed travel: ILS {a.travel_hr.sum():.9f} h, frozen GA {b.travel_hr.sum():.9f} h. These station/crew summaries do not weight source reconnection or dependency masses in the same way as the objective.

Largest beneficial intervals, cut at the union of both exact completion clocks:

{top[selected_columns].to_markdown(index=False, floatfmt='.9f')}

Each interval contribution is duration times (frozen-GA effective service minus ILS effective service). Their complete sum matches the independently verified loss difference. Full source IDs, exclusively source-connected station sets and their dependency masses are in `SAMPLE15_EXACT_INTERVAL_DIFFERENCES.csv`; native graph-component membership and newly connected dependency masses are in the two source event JSONs. Full 92-station completion/crew/travel differences are retained separately.

Dependency mass is the fixed population-mapping contribution carried by stations, not mutually exclusive geographically identified customers or delivered electrical load. Positive/negative intervals can coexist; a lower mean does not imply every station or community improves. These comparisons describe two complete schedules. They are not a controlled single-station-edit counterfactual and do not prove that a particular station movement caused the source benefit. No new optimization or physical sampling was performed to produce this accounting.
""")


def evidence():
    hist = R / 'results/diagnostics/ga_ils_parameter_defense_20261010'
    names = ['ILS_PARAMETER_EVIDENCE_MATRIX.csv', 'PAIRED_PARAMETER_CONTRASTS.csv',
        'CONFIGURATION_SUMMARY.csv', 'HISTORICAL_PAIRED_STATISTICS.csv', 'EXPERIMENT_INVENTORY.csv']
    for n in names:
        hydrate(hist / n)
    source = pd.read_csv(hist / names[0]).fillna('')
    mapping = {
        'Neighborhood': 'swap; insertion; inversion', 'Stagnation': 'stagnation',
        'Perturbation': 'perturb', 'Restart reference': 'current',
        'Focused interaction': 'swap_stag2000; swap_stag200; insertion_stag200; swap_no_perturb',
        'Initialization': 'cold; warm', 'Acceptance': '', 'Budget': '', 'Deterministic refinement': '',
    }
    contrasts = pd.read_csv(hist / names[1]).fillna('')
    rows = []
    for _, r in source.iterrows():
        row = r.to_dict()
        terms = [x.strip() for x in mapping[r.parameter].split(';') if x.strip()]
        matches = contrasts[contrasts.contrast.astype(str).map(lambda s: any(t in s for t in terms))]
        row.update(selected_standalone_value={
            'Neighborhood': 'swap only', 'Acceptance': 'candidate loss < current loss - 1e-12; exact best archive',
            'Stagnation': '2000 nonimproving attempted local proposals including cache hits',
            'Perturbation': '2/4/8 successive swaps cyclically; final-only scoring',
            'Restart reference': 'best', 'Initialization': 'one Impact-first only',
            'Budget': '20k smoke;20 seeds100k;10 fixed500k continuations;60x attempt cap',
            'Focused interaction': 'swap/2000 package, not asserted synergistic',
            'Deterministic refinement': 'FORBIDDEN and absent'}[r.parameter],
            historical_source_sha256=sha(hist / names[0]),
            exact_contrasts_and_cost_json=json.dumps(matches.to_dict('records')),
            transfer_scope='Warm/seven-reference sensitivity supports an engineering choice, not a numerical optimum or Impact-only effect estimate. New Impact-only runs test the selected complete package.',
            new_standalone_source='STANDALONE_ILS_SEED_LEVEL_RESULTS.csv;FAIR_COLD_START_GA_COMPARISON.csv',
            unchanged_historical_evidence=True)
        rows.append(row)
    csv('PARAMETER_JUSTIFICATION_MATRIX.csv', rows)
    csv('HISTORICAL_PARAMETER_CONTRASTS_REUSED.csv', contrasts)
    csv('HISTORICAL_CONFIGURATION_SUMMARY_REUSED.csv', pd.read_csv(hist / names[2]))
    historical_stats = pd.read_csv(hist / names[3])
    csv('HISTORICAL_STOCHASTIC_COMPARISONS_REUSED.csv', historical_stats)
    inv = pd.read_csv(hist / names[4])
    # Preserve the formal protocol's actual 100k/500k distributions, not substitute the new cold baseline.
    formal = inv[inv.configuration.eq('operator_swap') & (
        (inv.family.eq('operator_and_old_ga_operator_confirmation') & inv.budget.eq(100000)) |
        (inv.family.eq('operator_and_old_ga_budget_extension') & inv.budget.eq(500000)))].copy()
    assert len(formal) == 25 and set(formal[formal.budget.eq(100000)].seed) == set(range(42,62))
    assert set(formal[formal.budget.eq(500000)].seed) == set(range(42,47))
    formal['protocol'] = 'historically selected formal swap-GA initialization; 500k continues first five, not new seeds'
    csv('HISTORICAL_GA_100K_500K_RECORDS.csv', formal)
    source_hashes = {str((hist/n).relative_to(R)): sha(hist/n) for n in names}
    for n in ('FINAL_BUDGET_CHECKPOINTS.csv','FINAL_BUDGET_SUMMARY.csv'):
        path = R / 'results/diagnostics/final_ga_method_20261009' / n
        hydrate(path)
        csv('HISTORICAL_'+n, pd.read_csv(path))
        source_hashes[str(path.relative_to(R))] = sha(path)
    save(OUT / 'HISTORICAL_REUSE_SOURCE_HASHES.json', source_hashes)
    spec_path = R / 'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json'
    spec = read(spec_path)
    save(OUT / 'HISTORICAL_GA_PROTOCOL_AUDIT.json',dict(status='PINNED_CONFIG_AND_EXACT_SEED_COUNTS_PASS',
        source_file=str(spec_path.relative_to(R)), source_sha256=sha(spec_path),
        algorithm=spec['algorithm'], original_initialization=spec['initialization'],
        search_protocol=spec['search_protocol'], objective=spec['objective'],
        records_at_100k=20, independent_seeds_100k=list(range(42,62)),
        records_at_500k=5, same_state_continuation_seeds=list(range(42,47)),
        historical_vs_fair_cold_start_difference='Initializer only; no previous optimized chromosome in new GA',
        inherited_metadata_not_new_execution=True, validation_outcomes_accessed=False))


def report(recommendation):
    assert recommendation in ('ILS', 'GA')
    tables = pd.read_csv(OUT / 'OPTIMIZER_DISTRIBUTIONS.csv')
    paired = pd.read_csv(OUT / 'FAIR_COLD_START_GA_COMPARISON.csv')
    candidate = read(OUT / 'SELECTED_STANDALONE_ILS_CANDIDATE.json')
    audit = read(OUT / 'PRODUCTION_PARITY_AND_SAMPLE_INFLUENCE.json')
    cost = read(OUT / 'COMPUTATION_ACCOUNTING.json')
    ga = audit['comparisons']['FrozenGA']
    impact = audit['comparisons']['Impact']
    historical = pd.read_csv(OUT / 'HISTORICAL_GA_100K_500K_RECORDS.csv')
    historical_summary = historical.groupby('budget').loss.agg(['count','mean','median','std','min','max']).reset_index()
    cost_table = tables[['method','budget','n','mean_wall_seconds','mean_objective_seconds','mean_attempts','mean_cache_hits']]
    ils_rows = pd.read_csv(OUT / 'STANDALONE_ILS_SEED_LEVEL_RESULTS.csv')
    operators = ils_rows.groupby('budget')[['accepted','restarts','restart_cancellations','restart_cached','restart_intermediate_revisits']].agg(['mean','min','max'])
    operators.columns = ['_'.join(c) for c in operators.columns]
    operators = operators.reset_index()
    csv('ILS_OPERATOR_ACCOUNTING.csv', operators)
    quality_table = tables[['method','budget','n','mean_hr','median_hr','sd_hr','best_hr','worst_hr']]
    paired_table = paired[['budget','n','mean_delta_hr','simultaneous95_low_hr','simultaneous95_high_hr','wins','losses','mean_wall_ratio']]
    spec = read(R / 'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json')
    assert spec['algorithm']['mutation'] == .1 and spec['algorithm']['population'] == 100
    mechanism()
    primary = 'RECOMMEND STANDALONE ILS AS THE REPLACEMENT CANDIDATE' if recommendation=='ILS' else 'RETAIN THE EXISTING VALIDATED GA'
    body = f"""# Final Single-Optimizer Decision

**{primary}**

This is a methodological recommendation, not promotion authorization. The formal GA, current manuscript, scientific model and earlier independent-validation evidence remain unchanged. The manuscript should describe ONE optimizer after author approval and required independent confirmation, not a GA/ILS hybrid or operational comparison framework. The preceding parameter-defense package's Scope A/B presentation proposal is superseded for this task: the present investigation tests genuine Impact-only independence and makes one method recommendation, without editing the preceding report or claiming new physical validation.

## Completed Computation

Starting authority: `62f0c2be4f1e37f25e3db8d0d042cd5d0cfcfd3f`. Study registration commit: `{read(OUT/'PREREGISTRATION_COMMIT.json')['commit']}`. Eight smoke runs x20k completed; 20 fresh paired main seeds x100k completed; the first10 predeclared pairs continued the same search states to250k and500k. This is40 main searches, not80 independent searches; the latter number counts final-budget observations. Exactly {cost['search_mean64_calls']:,} new search calls evaluated the unchanged64-state mean. Setup and independent parity work are separately charged. No negative run was omitted, no attempt-capped case occurred in this experiment, and no physical samples were generated.

## Fair Cold-Start Evidence

{quality_table.to_markdown(index=False, floatfmt='.9f')}

Paired difference is ILS minus fair cold GA; negative favors ILS. Intervals concern optimizer seeds conditional on the same development states. The five-budget family has simultaneous Bonferroni t intervals; bootstrap intervals are pointwise, not simultaneous. No formal equivalence/noninferiority margin was registered.

{paired_table.to_markdown(index=False, floatfmt='.9f')}

Full paired medians/SDs, pointwise t/bootstrap intervals and seed values remain in `FAIR_COLD_START_GA_COMPARISON.csv` and `BUDGET_CONVERGENCE_AND_COST.csv`; no uncertainty result is discarded to shorten the table.

Both algorithms start with only the original Impact-first heuristic information. GA additionally receives99 random initial permutations, not a previous optimized prior, inversion neighbors or other heuristic archive. Equal budgets count distinct scored permutations. RNG consumption differs by method; fairness is common prior information, evaluator and budget, not identical proposals.

## Fixed Historical GA Reference

The formally selected GA remains SHA256 `8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab`, planning J32.997840773882714h. The full seed/budget comparison is `FROZEN_GA_REFERENCE_COMPARISON.csv`; historical100k/500k distributions are retained separately, with source hashes. They have a different initializer and selection history and are not a matched causal optimizer comparison.

Historical formally selected swap-GA protocol, seeds42-61 at100k; seeds42-46 are continuations at500k, not five additional replicates:

{historical_summary.to_markdown(index=False, floatfmt='.9f')}

These source records were filtered to `operator_swap` alone, not pooled with original inversion-GA, mixed operators, or other shortlist configurations. The archived final configuration pins P100, crossover0.8, swap mutation0.1, tournament3, elite1. The two original controlled mutation0.2 bridge configurations are not its formal100k/500k distribution.

Selected standalone ILS: seed{candidate['seed']}, budget{candidate['budget']:,}, J={candidate['loss_hr']:.12f}h, SHA256 `{candidate['sequence_sha256']}`. It comes only from the preregistered main-pool rule, without extra refinement. Full92-station order and exact originating receipt are in `SELECTED_STANDALONE_ILS_CANDIDATE.json`. Its minimum is selected development performance, not an unbiased expected optimizer result. Each repeated seed's result is retained, including those above frozenGA.

## Physical-Sample Influence And Production Parity

All64 development states for ILS, frozenGA and Impact passed the independent pandas/NetworkX production path and native event decomposition:192 production sample calls and192 compiled sample calls; maximum discrepancy {audit['max_absolute_parity_error_hr']:.3g}h. The native scheduler/source gate and population dependency mass are unchanged.

ILS-minus-Impact mean {impact['mean_delta_hr']:+.12f}h, median {impact['median_delta_hr']:+.12f}, better/worse states{impact['better_samples']}/{impact['worse_samples']}; omit15 mean {impact['omission15_mean_delta_hr']:+.12f}h. ILS-minus-frozenGA mean {ga['mean_delta_hr']:+.12f}h, median {ga['median_delta_hr']:+.12f}, better/worse states{ga['better_samples']}/{ga['worse_samples']}. State15 delta {ga['sample15_delta_hr']:+.12f}h; omit15 mean {ga['omission15_mean_delta_hr']:+.12f}h. {ga['leave_one_out_sign_reversal_count']} of64 single omissions reverse its mean ranking. Removing influential states is a diagnostic only, never a new objective or selection rule.

Exact mean whole-schedule changes relative to frozenGA: self {ga['mean_component_delta_hr']['L_self']:+.12f}h, threshold {ga['mean_component_delta_hr']['L_threshold']:+.12f}h, source {ga['mean_component_delta_hr']['L_source']:+.12f}h. State15: self {ga['sample15_component_delta_hr']['L_self']:+.12f}h, threshold {ga['sample15_component_delta_hr']['L_threshold']:+.12f}h, source {ga['sample15_component_delta_hr']['L_source']:+.12f}h. The source/threshold accounting explains how aggregate gains can coexist with worse typical samples; it does not establish a causal effect of an individual station move. Native state15 crew schedules, source-connected components and dependency masses are preserved.

Definitions: self=1-f; threshold=f(1-F); source=fF(1-C); total=1-fFC. Integrate at actual completion events over the unchanged original planning horizon {audit['horizon_audit']['original_planning_horizon_hr']:.12f}h, mass weighted and normalized. The original manuscript/independent-validation endpoint is480h, not this numerical planning upper bound. Reintegrating all192 native traces at480h gives maximum absolute post480 loss {audit['horizon_audit']['max_absolute_post480_loss_hr']:.3g}h: they are equivalent for these fixed planning states and sequences only. Future physical samples must retain480h truncation/censoring explicitly, not presume zero tails. These are equivalent population-weighted service-loss hours, not person-hours, MW, energy or restoration time for every household.

## Decision Grounds

| Required criterion | Evidence and boundary | Assessment |
|---|---|---|
| Independence | Impact-first only; no optimized prior, other heuristic archive or extra refinement | PASS |
| Complete-workflow simplicity | One swap mechanism; no previous optimizer dependency, population/crossover/selection machinery | PASS; still parameterized |
| Optimization quality |18/20 paired100k and10/10 paired500k wins; all five simultaneous seed intervals favor ILS | Supported conditionally; no formal equivalence test |
| Reliability | All48 smoke/main searches complete; twenty full ILS cache replays exact; ten registered extensions | PASS on this planning model |
| Parameter defensibility | Verified original methodology, retained negative/positive historical sensitivity, independent Impact-only package test | Defensible engineering package, not unique optimum |
| Scientific integrity | No new physical samples or old validation-outcome selection; selected-sequence influence disclosed; new confirmation frozen but not executed | PASS for replacement-candidate recommendation, not policy promotion |

Standalone ILS passes independence: current and initial archive contain only Impact-first; every scored permutation is valid; no GA prior or deterministic refinement enters its search. It genuinely removes the previous-run dependency. It also removes population size, crossover probability/operator, mutation probability and tournament/elitism mechanisms. This is a complete independently executable workflow simplification, while preserving the nontrivial original scheduling/physical evaluator. It still requires documented stagnation, restart, tolerance, seeds and budget; it is not parameter-free.

The empirical repeated-search distributions, not a few thousandths in a selected minimum, support competitive planning quality. Cost records show attempted-query overhead separately from objective time. Instrumented GA records population diagnostics; ILS does not, so measured wall advantage is implementation-specific and cannot all be attributed to intrinsic algorithm complexity.

{cost_table.to_markdown(index=False, floatfmt='.3f')}

Main batch wall {cost['main_batch_wall_seconds']:.3f}s, summed recorded worker CPU {cost['main_worker_cpu_seconds']:.3f}s, worker model/JIT setup {cost['main_worker_setup_seconds']:.3f}s across{cost['main_initialized_workers']} workers. Setup objective calls total {cost['setup_mean64_calls']} across smoke/main. Worker CPU covers ILS search loops and GA wrapper intervals; setup/ILS checkpoint serialization/analysis/archive are not all included in that subtotal. ILS search wall excludes gzip checkpoint serialization; GA engine wall includes in-engine diagnostic checkpoint work, and incremental GA wrapper wall also includes final exports. Batch wall includes worker setup, concurrent scheduling and final exports. Full raw receipts retain these separate clocks; none is a universal hardware-independent speed estimate.

Strict accepted local moves, restart ranges, complete-cancellation counts, final cached restarts and repeated intermediate-permutation counts are retained in `ILS_OPERATOR_ACCOUNTING.csv` and the seed-level records. A compound restart does not necessarily change exactly 2/4/8 distinct stations and is not charged for its unscored intermediate permutations. No cancellation/revisit triggers an uncounted retry. Every cached full permutation in every final main state has been checked against the same complete 92-ID universe.

All20 complete production-size ILS trajectories also passed deterministic replay from their saved fitness caches: ordered keys, budget-prefix sequences/counters and final logical/RNG states match exactly. The audit read {cost['cache_replay_saved_fitness_reads']:,} saved fitness values, used {cost['cache_replay_cpu_seconds']:.3f}s CPU/{cost['cache_replay_wall_seconds']:.3f}s wall and made zero new physical objective calls. It is a reproducibility audit, not20 more search replicates or additional optimization. Intermediate checkpoint timer/gzip bytes were overwritten during continuation, so their observed digests are retained without pretending those exact intermediate payloads remain available; final states and exact logical replay are archived.

Verification completed all192 production/event comparisons, then JSON serialization failed on a NumPy integer leave-one-out count. The report was finalized from already saved round-trip numerical tables after casting that count, with zero repeated physical scoring. The first verification's whole-loop timer was not preserved before the exception and is explicitly unavailable; finalization time and all call counts are retained. A missing timer is not replaced by an estimate or silently counted as zero.

Historical swap/mixed and swap/2000-package results justify the reduced operator set conditionally. They do not establish a universal optimum or transfer warm-start effect sizes to Impact-only. The original200/800/2000 and1/2/4,2/4/8,4/8/16 screens and independent confirmations are reused, not repeated. General ILS literature supports the architecture; our exact constants remain engineering choices tested in this application.

The remaining scientific limitation is serious: a selected candidate's tiny advantage over frozenGA is influential-state sensitive and most planning states can worsen. That is not the reason for recommending a simpler algorithm and must not be presented as universal recovery superiority. This development collection was already inspected in previous work. Independent optimizer seeds are not fresh physical validation, and historical internal cross-fitting is diagnostic rather than untouched validation.

## Required Before Formal Replacement

Freeze this exact sequence, code, model hashes and selection procedure; obtain separate author authorization; run genuinely new paired physical confirmation under the prospective plan; assess modeled benefit versus Impact and comparative risk versus frozenGA; secure author approval for promotion. Until then the validated formalGA remains the operational authority. Do not reuse the completed2000-state cohort as untouched validation, silently replace official strategy files, or modify manuscript figures in this diagnostic branch.

The new prospective plan is preparation only. No new physical validation was executed. The previous frozenGA/old refinedILS validation pertains to those exact sequences, not this standalone procedure. See the concise one-algorithm proposedMethods and separate reviewer/supplemental audit; this study does not mandate two optimizers in the paper.
"""
    md('FINAL_GA_OR_ILS_DECISION.md', body)
    md('METHOD_COMPLEXITY_COMPARISON.md', f"""# Complete Workflow Complexity

| Dimension | Existing validated GA | Truly standalone ILS |
|---|---|---|
| Numeric search controls excluding shared seeds/budget | P100, crossover0.8, mutation0.1, tournament3, elites1; plus25 neighbors | tolerance1e-12, stagnation2000, cycle2/4/8 |
| Search operators | ordered crossover + swap mutation + parent tournament + population elitism | swap only; perturbation repeats same operation |
| Initial information | seven heuristic policies, optimized prior and prior/Impact inversion neighbors | only fixed Impact-first |
| Prior optimizer dependency | actual formal workflow includes earlier optimized prior | none |
| Extra refinement | not needed for formal GA | forbidden and absent |
| State required for exact resume | population/scores, generation phase, offspring, parent metadata, RNG, archive/cache | current/score, RNG, archive/cache, stagnation/perturb phase |
| Empirical calibration | original population/operator/initialization/pressure evidence | historical conditional neighborhood/restart evidence + fresh Impact-only package test |
| Reproduction overhead | cached population scans and duplicate offspring | cached swapped permutations and restart evaluations |
| Independent future validation | previous fixed candidate already confirmed | genuinely new physical confirmation still needed |

Counting scalar fields alone is misleading: the ILS cycle has three values, both need a numerical acceptance/tie convention, cache, safety cap, initializer, seed protocol and selection rule. The reduction is fewer mechanisms and no external optimized starting information. The fixed scheduling decoder and source gate remain equally complex in both workflows; none of that physics is removed.

Measured distributions/costs: `OPTIMIZER_DISTRIBUTIONS.csv`; full paired seed/budget values: `BUDGET_CONVERGENCE_AND_COST.csv`. Instrumentation differs, so wall ratios are not universal speedup claims. Archive/checkpoint storage is diagnostic reproducibility overhead, not another optimizer. Variability is reported as SD/range over independent optimizer seeds, not variation over physical populations.

Primary recommendation: **{primary}**. ILS independence, simpler complete workflow and conditional optimization reliability are distinct from independent physical generalization. More calibration is not automatically required to claim unique optimum; no such optimum is claimed.
""")
    md('REVIEWER_CONCERNS_AND_DEFENSE.md', f"""# Reviewer Questions And Defense

1. **Why permutation ILS?** The fixed decoder separates feasible crew dispatch from priority search; the original mean source-gated loss is evaluated exactly. Literature precedents and limitations are in the verified original-source table.
2. **Why one swap neighborhood?** Swaps preserve every station and generate the permutation space; conditional historical sensitivity and fresh20-seed package runs support empirical adequacy, not a globally sufficient monotone path.
3. **How are assignments feasible?** Filter DS0 tasks, assign the next priority task to the earliest-free crew (index tie rule), use origin travel for its first task or directed predecessor travel thereafter, and add sampled duration. Each crew handles one task at a time. This is feasibility under modeled constraints, not real-world AC/security/work-shift certification.
4. **Why Impact-first?** It is an original fixed, independent baseline with no search-derived information; it gives an interpretable starting point. No hidden reference archive.
5. **Why2000?** Previously tested200/800/2000 and focused swap/2000 package; new repeated runs establish viability of this package. Not a unique optimum and not a local-optimality certificate.
6. **Why2/4/8?** Previously investigated bounded cycle, reused without new tuning; large/small alternatives have qualified evidence. Cancellation/cache revisits are reported. No claim all cycles or restart references were optimized.
7. **Repeatability?** Registered fresh seeds, full final92-station permutations, SHA256, RNG/state continuation, exact small and92-item replay tests.
8. **Stopping?** Distinct budgets and attempt caps declared, including initial score, duplicate lookups, worker compilation and verification costs. Continued budgets are not new replicates.
9. **Prior GA dependency?** None in standalone search. FrozenGA is loaded only by post-search reference verification. Original authority files are read for immutable sample identity/horizon, not sequence injection.
10. **Equal work?** Same64 states, originalJ, same allowed heuristic prior and matched distinct budgets. Report attempts, objective time and instrumented wall separately.
11. **Fixed sequence support?** Preregistered originalJ minimum selection over main runs, independent all64 production/event parity. Selected minima are not unbiased optimizer means.
12. **Benefit over Impact?** Selected paired development difference {impact['mean_delta_hr']:+.12f}h; all per-state results and uncertainty retained. Fresh physical confirmation remains necessary.
13. **Global optimum?** None claimed. A flat trajectory or sampled stagnation is not a proof.
14. **Missing generalization?** The completed2000-state cohort is not untouched for the new sequence; new validation requires independent authorization and reserved sampling namespace. Current conclusions concern64 inspected development states plus fresh optimizer seeds.

## Focused Supplementary Parameter Justification

`PARAMETER_JUSTIFICATION_MATRIX.csv` retains exact historical contrasts, alternatives, costs, source hashes and transfer restrictions. Swap-alone versus mixed and swap/2000-versus-mixed are different contrasts. The former interval can cross zero while the complete package has stronger conditional evidence; this is not proof of operator-by-stagnation synergy. Warm results and historical `ils_cold` retained seven heuristic references and must not be called the present Impact-only protocol. No additional deterministic refinement, no prior injection, no new sensitivity grid and no completed validation outcomes were used here.

The fairGA control changes only disclosed initialization. Historical formalGA distributions retain their selected initialization/history separately. The application-specific current recommendation is **{primary}**; the main paper should describe only the selected algorithm after approval, leaving comparison/calibration provenance in this audit.

ILS-minus-frozenGA sample15 delta {ga['sample15_delta_hr']:+.12f}h and omission15 delta {ga['omission15_mean_delta_hr']:+.12f}h must remain visible. Strong conditional optimizer evidence does not resolve sensitivity to the physical samples or promise benefits to most communities.
""")
    if recommendation=='ILS':
        methods = f"""# Proposed Single-Algorithm Methods: ILS

Author-review draft only; not a modification of the working manuscript or formal policy.

We optimized one complete priority permutation of the 92 substations using standalone iterated local search (ILS). Each evaluation used the original 57-crew C57_D1 scheduling decoder, directed travel matrices, realized repair durations, functionality threshold of 0.5, Core source-connected gate and population dependency mapping. The objective was the mean normalized population-weighted service deficit across 64 fixed planning realizations; it does not represent delivered MW. The unchanged planning evaluator integrates to {audit['horizon_audit']['original_planning_horizon_hr']:.12f} h. An event-exact audit confirms zero additional loss after 480 h for the selected sequence and its two references on all 64 planning states, so these planning burdens equal the manuscript's 0-480 h burden. This equivalence is not assumed for new physical samples.

The initial current permutation and best-ever archive contained only the original deterministic Impact-first ordering. Each local proposal uniformly selected two distinct positions and swapped their stations. The current state accepted a proposal only if the loss decreased by more than 1e-12 h; the exact best observed sequence was archived independently. After 2,000 consecutive nonimproving local proposals, including cache hits, the archived sequence was perturbed with 2, 4 or 8 successive swaps cyclically, and strict local descent resumed from that perturbation. Only the final perturbed permutation was evaluated. This stochastic stopping criterion is not a certificate of local optimality. There was no prior optimized sequence, population search or additional refinement.

Twenty independently seeded searches received 100,000 distinct-permutation evaluations each. Ten seeds designated before computation continued unchanged to 250,000 and 500,000 evaluations. Each run cached repeated permutations privately; attempts, distinct evaluations and a 60-times-budget safety cap were recorded. The final diagnostic candidate minimized the original mean planning loss over the prespecified main-run pool, with exact ties resolved by sequence SHA-256, seed and budget. Its complete permutation and identity are archived. Independent production-path evaluations verified all 64 planning losses. These repeats assess search variability on development data, not physical generalization. Formal adoption requires separately authorized fresh physical confirmation of the frozen sequence.

Methodological precedents and application-specific calibration limitations are documented in `VERIFIED_LITERATURE_AND_METHOD_PRECEDENTS.md` and the focused Supplementary audit. The original decoder defines modeled feasibility; neither the heuristic nor the observed convergence certifies a global optimum.
"""
    else:
        methods = """# Proposed Single-Algorithm Methods: Existing GA

Retain the approved GA-only manuscript method without introducing ILS as a second operational procedure. Preserve the original decoder/objective, formal initializer, operators, seed/budget protocol and fixed selected sequence. This diagnostic did not edit the source manuscript; exact approved original text remains the authority. Conditional comparisons and limitations belong to the separate methods audit, not an additional algorithm in the main paper.
"""
    md('PROPOSED_SINGLE_ALGORITHM_METHODS.md', methods)
    future = dict(status='FROZEN_PROSPECTIVE_PLAN_NOT_EXECUTED', candidate_sha256=candidate['sequence_sha256'],
        candidate_sequence=candidate['sequence'], model_hashes=audit['model_identity'],
        optimizer_source_sha256=candidate['implementation_sha256'],
        optimizer_configuration=candidate['config'],
        experimental_design_sha256=sha(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json'),
        verification_source_sha256=sha(R / 'src/la_grid/diagnostics/standalone_ils_analysis_20261010.py'),
        source_hash_rule='Exact runtime bytes, not a waived checksum; additionally record Git blob hashes for normalized checkout provenance',
        sampling_namespace='la-grid/standalone-ils/'+candidate['sequence_sha256']+'/prospective-v1',
        proposed_samples=2000, authorization_required=True, sample_seed_reservation=2026110100,
        preauthorization_seed_check='Check namespace and seed against physical sampling ledgers before any generation; do not inspect historical validation outcomes.',
        physical_generator='Original frozen2pc50 model, DS and repair-duration sampler; no altered hazard/fragility/crew/travel/gate/mapping',
        policies=['this frozen standalone ILS', 'original Impact-first', 'frozen formally validated GA'],
        planning_horizon_hr=audit['horizon_audit']['original_planning_horizon_hr'],
        prospective_evaluation_horizon_hr=480.,
        horizon_rule='Retain archived independent-validation 0-480h endpoint and late-event/censored-T80 handling; not the longer planning integration bound and no assumed zero post480 loss on new samples',
        endpoint_source='src/la_grid/diagnostics/independent_validation_20261010.py:H=480; independent_validation_qa_20261010.py',
        primary_estimand='paired mean normalized0-480h loss ILS-minus-Impact, the original manuscript/independent-validation endpoint; upper pointwise95%CI below0 establishes modeled benefit',
        secondary_estimand='ILS-minus-frozenGA paired mean, median/quantiles, improved/worsened fractions, tail losses and decomposition; report two-contrast simultaneous intervals as well',
        uncertainty='paired physical-sample bootstrap20000, seed2026110200; pointwise percentile and Bonferroni97.5% pairwise intervals for2-contrast family',
        stopping='Generate/evaluate once at fixed2000; no sequential outcome stopping or optional expansion',
        adoption='No automatic adoption. Author reviews comparative mean/tail/distribution risk and signs approval; no unregistered equivalence/noninferiority assertion.',
        prohibited=['new candidate selection', 'parameter tuning', 'reference sequence replacement', 'cohort reuse as untouched', 'additional physical generation before authorization'])
    save(OUT / 'FUTURE_VALIDATION_FREEZE.json', future)
    md('FUTURE_INDEPENDENT_VALIDATION_REQUIREMENTS.md', f"""# Prospective Independent Validation Requirements

Preparation only: **NOT EXECUTED; SEPARATE AUTHOR AUTHORIZATION REQUIRED**. Freeze sequenceSHA `{candidate['sequence_sha256']}` and exact archived92-station permutation, selected implementation/configuration, model/sample hashes and current selection ledger. Primary recommendation is {primary}; it does not itself authorize physical sampling or strategy promotion.

The registered machine-readable plan is `FUTURE_VALIDATION_FREEZE.json`. Proposed2000 genuinely new paired physical realizations in reserved namespace `{future['sampling_namespace']}`, reserved seed2026110100, with an existence/seed-ledger check before authorized generation. This is a proposed future count, not data generated now. Reuse the unchanged original2pc50 sampler/model and apply only three frozen sequences: thisILS, Impact-first and formally frozenGA. Random physical streams must be independent of all planning/previous validation streams and must be permanently hashed and archived.

Primary endpoint: the original manuscript/independent-validation480h mean normalized population-weighted loss, pairedILS-minus-Impact; report pointwise95%CI and whether its upper bound is below0. This differs from the unchanged planning evaluator's {audit['horizon_audit']['original_planning_horizon_hr']:.12f}h upper bound; current planning traces have zero tails after480h, but new samples might not. Preserve exact0-480h clipping, retain all late completion events, and report censored T80/null crossing plus restricted T80=480 rather than dropping unrecovered cases. Secondary: ILS-minus-frozenGA mean, median/quantiles, state improvement/worsening fractions, adverse tails and source/threshold/self decomposition. Report paired physical-sample bootstrap20000 with fixed seed2026110200 and two-contrast simultaneous97.5% individual intervals. Selected development advantages and majority-of-states losses motivate this distributional audit; no omitted-state objective, fairness penalty or retrospective loss-weight change.

Fixed2000 one-shot completion, no peeking-driven enlargement, tuning, candidate reselection or substitution. Before generation verify source-code/model hashes and that old cohort files remain untouched. The previous2000-state outcomes must not be used for configuration, stopping or candidate decisions, nor re-scored for a claim of untouched confirmation. Do not claim the historical refinedILS result validates this standalone algorithm/sequence even if some scheduling losses coincide.

Author reviews practical relative risk and the full comparative distribution before formal replacement; no unregistered noninferiority/equivalence margin and no automatic promotion. If comparative mean uncertainty remains unresolved, report it rather than tuning on the new cohort. Archive failed/incomplete evaluations. Any protocol change must precede generation and receive explicit authorization, never follow observed outcomes. The source manuscript and formalGA stay unchanged until independent confirmation and approval.
""")
    save(OUT / 'DECISION_MACHINE_READABLE.json', dict(primary_recommendation=primary, selected_optimizer=recommendation,
        formal_replacement_authorized=False, new_validation_executed=False, candidate_sha256=candidate['sequence_sha256']))


REQUIRED = ('STANDALONE_ILS_METHOD_SPECIFICATION.md', 'VERIFIED_LITERATURE_AND_METHOD_PRECEDENTS.md',
    'PARAMETER_JUSTIFICATION_MATRIX.csv', 'EXPERIMENT_DESIGN_AND_SEEDS.json', 'STANDALONE_ILS_SEED_LEVEL_RESULTS.csv',
    'FAIR_COLD_START_GA_COMPARISON.csv', 'FROZEN_GA_REFERENCE_COMPARISON.csv', 'BUDGET_CONVERGENCE_AND_COST.csv',
    'SELECTED_STANDALONE_ILS_CANDIDATE.json', 'PRODUCTION_PARITY_AND_SAMPLE_INFLUENCE.json',
    'METHOD_COMPLEXITY_COMPARISON.md', 'REVIEWER_CONCERNS_AND_DEFENSE.md', 'PROPOSED_SINGLE_ALGORITHM_METHODS.md',
    'FUTURE_INDEPENDENT_VALIDATION_REQUIREMENTS.md', 'FINAL_GA_OR_ILS_DECISION.md')


def archive_and_qa():
    now = preservation()
    assert now == read(OUT / 'PRESERVATION_BASELINE.json')
    _, _, model = load_model()
    records = []
    dest = OUT / 'RAW_SEARCH_AND_RESUME_EVIDENCE.zip'
    with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for phase in ('smoke', 'main'):
            for p in sorted((OUT / phase).rglob('*')):
                if p.is_file():
                    name = str(p.relative_to(OUT)).replace('\\', '/')
                    records.append(dict(path=name, bytes=p.stat().st_size, sha256=sha(p)))
                    z.write(p, name)
    with zipfile.ZipFile(dest) as z:
        assert len(z.namelist()) == len(records) and z.testzip() is None
        for r in records:
            assert hashlib.sha256(z.read(r['path'])).hexdigest() == r['sha256']
    save(OUT / 'RAW_EVIDENCE_MANIFEST.json', dict(members=records, archive_sha256=sha(dest), archive_bytes=dest.stat().st_size))
    candidate = read(OUT / 'SELECTED_STANDALONE_ILS_CANDIDATE.json')
    assert len(candidate['sequence']) == len(set(candidate['sequence'])) == 92
    hashes = {n: sha(OUT / n) for n in REQUIRED}
    cost = read(OUT / 'COMPUTATION_ACCOUNTING.json')
    assert cost['search_mean64_calls'] == 12160000 and cost['completed_main_searches'] == 40
    assert read(OUT / 'PRODUCTION_PARITY_AND_SAMPLE_INFLUENCE.json')['status'] == 'ALL192_PRODUCTION_AND_EVENT_PARITY_PASS'
    assert read(OUT / 'ALL_MAIN_INITIALIZATION_AND_PERMUTATION_QA.json')['status'] == 'PASS'
    assert read(OUT / 'PRODUCTION_SIZE_ILS_CACHE_REPLAY_QA.json')['status'] == 'ALL20_FULL_TRAJECTORIES_PASS'
    code_hashes = {str(p.relative_to(R)): sha(p) for p in (R/'src/la_grid/diagnostics').glob('standalone_ils_*.py')}
    test = R / 'tests/test_standalone_ils_20261010.py'
    code_hashes[str(test.relative_to(R))] = sha(test)
    hydration_audit()
    save(OUT / 'REPRODUCIBILITY_AND_PRESERVATION_QA.json', dict(status='PASS', required_deliverable_sha256=hashes,
        scoped_source_sha256=code_hashes,
        original_model_identity=model, protected_file_count=len(now['files_sha256']),
        protected_revision_head=now['revision_head'], protected_revision_branch=now['revision_branch'],
        protected_staged_binary_diff_sha256=now['staged_diff_sha256'], protected_before_after_equal=True,
        preservation_baseline_sha256=sha(OUT / 'PRESERVATION_BASELINE.json'),
        originalGA_and_validation_package_sha256_unchanged=True, new_physical_samples=0,
        validation_outcomes_read=False, formal_strategy_modified=False, manuscript_modified=False,
        raw_evidence_archive_sha256=sha(dest), raw_evidence_members=len(records),
        runtime=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
            numba=numba.__version__, networkx=nx.__version__, scipy=scipy.__version__,
            os=platform.platform(), thread_environment={k: os.environ.get(k) for k in
                ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMBA_NUM_THREADS')}),
        current_execution_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip(),
        remote_verification_pending=True))
    print('QA_PASS', len(records), dest.stat().st_size, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('task', choices=['evidence', 'report', 'qa', 'hydration'])
    p.add_argument('--recommendation', choices=['ILS', 'GA'])
    a = p.parse_args()
    if a.task == 'evidence': evidence()
    elif a.task == 'report': report(a.recommendation)
    elif a.task == 'hydration': hydration_audit()
    else: archive_and_qa()
