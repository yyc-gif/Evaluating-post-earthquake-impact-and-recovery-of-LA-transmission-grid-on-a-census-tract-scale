"""Planning-only paired inference and independent production-path verification."""
from __future__ import annotations
import argparse
import itertools
import subprocess
import time

import numpy as np
import pandas as pd
from scipy import stats

from la_grid.diagnostics.standalone_ils_20261010 import (
    R, OUT, SMOKE, MAIN, EXTEND, BUDGETS, CONFIG, load_model, read, save, sha, hydrate, identity, read_state,
)
from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
from la_grid.diagnostics.ga_research_mechanism_20261009 import trace, influences
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_source_gate import evaluate_source_gate
from la_grid.revision.r1_realization_scheduling import RealizationInputs
from la_grid.revision.r1_ga_revision import evaluate_direct_population_burden_aggregate


def csv(name, rows):
    (rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)).to_csv(OUT / name, index=False, lineterminator='\n')


def production(k, context, seq, sample):
    realization = RealizationInputs(f'2pc50__planning_{sample:04}', pd.Series(k.damage[sample], index=k.ids), pd.Series(k.duration[sample], index=k.ids))
    return float(evaluate_direct_population_burden_aggregate(sequence=seq, realization=realization,
        crew_origin_ids=context['origins'], base_to_task_hr=context['base'], task_to_task_hr=context['task'],
        horizon_hr=k.horizon, source_gate=lambda raw: evaluate_source_gate(raw, context['graph'], context['sources'], threshold=.5),
        station_population_mass=k.station_mass, population_resolved_mass=k.total_mass))


def smoke_audit():
    k, impact, model = load_model()
    context, _, _ = execution_context(k.ids)
    rows = []
    for seed in SMOKE:
        p = OUT / 'smoke' / f'ils_s{seed}'
        row = read(p / 'FINAL_20000.json')
        state = read_state(p / 'STATE.pkl.gz')
        assert row['completed'] and row['distinct_evaluations'] == 20000
        assert row['initial_archive'] == row['initial_sequences'] == [list(impact)]
        assert row['config'] == CONFIG and row['sequence_sha256'] == identity(row['sequence'])
        assert len(state['cache']) == 20000 and state['attempts'] == 1+state['local_proposals']+state['restarts']
        assert all(len(key) == len(set(key)) == 92 for key in state['cache'])
        exact = per_sample(k, row['sequence'])
        assert abs(exact.mean()-row['loss_hr']) < 1e-8
        for sample in (0, 15, 63):
            prod = production(k, context, row['sequence'], sample)
            assert abs(prod-exact[sample]) < 1e-8
            rows.append(dict(seed=seed, sample=sample, production_loss_hr=prod, compiled_loss_hr=float(exact[sample]), absolute_error_hr=abs(prod-exact[sample])))
    save(OUT / 'SMOKE_QA.json', dict(status='PASS', model=model, all_eight_complete=True,
        forbidden_initial_information=False, production_sample_calls=24, compiled_sample_calls=512,
        setup_objective_calls=0, max_parity_error_hr=max(r['absolute_error_hr'] for r in rows), rows=rows))
    print('SMOKE_QA_PASS', flush=True)


def paired(values, family=5):
    d = np.asarray(values, float)
    n = len(d)
    mean, sd, median = float(d.mean()), float(d.std(ddof=1)), float(np.median(d))
    se = sd / np.sqrt(n)
    rng = np.random.default_rng(2026102200)
    boot = d[rng.integers(0, n, size=(20000, n))].mean(axis=1)
    return dict(n=n, mean_delta_hr=mean, median_delta_hr=median, sd_delta_hr=sd,
        wins=int((d < -1e-9).sum()), losses=int((d > 1e-9).sum()), ties=int((abs(d) <= 1e-9).sum()),
        t95_low_hr=mean-stats.t.ppf(.975, n-1)*se, t95_high_hr=mean+stats.t.ppf(.975, n-1)*se,
        simultaneous95_low_hr=mean-stats.t.ppf(1-.025/family, n-1)*se,
        simultaneous95_high_hr=mean+stats.t.ppf(1-.025/family, n-1)*se,
        bootstrap95_low_hr=float(np.quantile(boot, .025)), bootstrap95_high_hr=float(np.quantile(boot, .975)),
        best_delta_hr=float(d.min()), worst_delta_hr=float(d.max()))


def summarize():
    assert read(OUT / 'main_EXECUTION.json')['all_completed']
    rows, convergence = [], []
    for method in ('ILS', 'GA'):
        for seed in MAIN:
            folder = OUT / 'main' / f'{method.lower()}_s{seed}'
            boundaries = [100000, 250000, 500000] if seed in EXTEND else [100000]
            for budget in boundaries:
                row = read(folder / f'FINAL_{budget}.json')
                assert row['completed'] and row['distinct_evaluations'] == budget
                assert identity(row['sequence']) == row['sequence_sha256']
                assert row['initial_archive'] == row['initial_sequences'][:1]
                flat = {k: v for k, v in row.items() if k not in ('initial_sequences', 'initial_archive', 'model_identity', 'sequence', 'config')}
                rows.append(flat)
            if method == 'ILS':
                checkpoints = read(folder / 'BUDGET_CHECKPOINTS.json')
                final_state = read_state(folder / 'STATE.pkl.gz')
                assert len(final_state['cache']) == boundaries[-1]
                assert all(len(key) == len(set(key)) == 92 for key in final_state['cache'])
                for c in checkpoints:
                    convergence.append(dict(method=method, seed=seed, **c))
            else:
                checkpoints = pd.read_csv(folder / 'BUDGET_CHECKPOINTS.csv')
                for _, c in checkpoints.iterrows():
                    convergence.append(dict(method=method, seed=seed, budget=int(c.distinct_evaluations), loss_hr=c.best_service_loss_hr,
                        attempts=int(c.total_attempts), cache_hits=int(c.total_attempts-c.distinct_evaluations),
                        objective_seconds=c.objective_seconds, wall_seconds=c.elapsed_seconds, sequence_sha256=c.sequence_sha256))
    df = pd.DataFrame(rows)
    assert len(df) == 80 and not df.duplicated(['method', 'seed', 'budget']).any()
    csv('STANDALONE_ILS_SEED_LEVEL_RESULTS.csv', df[df.method == 'ILS'])
    csv('FAIR_GA_SEED_LEVEL_RESULTS.csv', df[df.method == 'GA'])
    conv = pd.DataFrame(convergence).drop(columns=['sequence'], errors='ignore')
    assert len(conv) == 160 and not conv.duplicated(['method', 'seed', 'budget']).any()
    conv = conv.sort_values(['method', 'seed', 'budget'])
    conv['incremental_distinct'] = conv.groupby(['method', 'seed']).budget.diff().fillna(conv.budget)
    conv['incremental_wall_seconds'] = conv.groupby(['method', 'seed']).wall_seconds.diff().fillna(conv.wall_seconds)
    conv['incremental_objective_seconds'] = conv.groupby(['method', 'seed']).objective_seconds.diff().fillna(conv.objective_seconds)
    conv['marginal_gain_hr'] = -conv.groupby(['method', 'seed']).loss_hr.diff()
    csv('BUDGET_CONVERGENCE_AND_COST.csv', conv)
    comparisons, distribution = [], []
    frozen = read(R / 'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json')
    assert frozen['sequence_sha256'] == '8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab'
    frozenrows = []
    for budget in BUDGETS:
        a = conv[(conv.method == 'ILS') & (conv.budget == budget)].set_index('seed')
        b = conv[(conv.method == 'GA') & (conv.budget == budget)].set_index('seed').reindex(a.index)
        assert b.loss_hr.notna().all()
        comp = dict(budget=budget, contrast='ILS-minus-fair-cold-GA', **paired(a.loss_hr.to_numpy()-b.loss_hr.to_numpy()),
            mean_ILS_hr=float(a.loss_hr.mean()), mean_GA_hr=float(b.loss_hr.mean()),
            mean_wall_ratio=float(np.mean(a.wall_seconds/b.wall_seconds)),
            mean_objective_seconds_ratio=float(np.mean(a.objective_seconds/b.objective_seconds)),
            mean_attempts_ILS=float(a.attempts.mean()), mean_attempts_GA=float(b.attempts.mean()))
        comparisons.append(comp)
        for method, table in [('ILS', a), ('GA', b)]:
            distribution.append(dict(method=method, budget=budget, n=len(table), mean_hr=float(table.loss_hr.mean()),
                median_hr=float(table.loss_hr.median()), sd_hr=float(table.loss_hr.std()), best_hr=float(table.loss_hr.min()),
                worst_hr=float(table.loss_hr.max()), mean_wall_seconds=float(table.wall_seconds.mean()),
                mean_objective_seconds=float(table.objective_seconds.mean()), mean_attempts=float(table.attempts.mean()),
                mean_cache_hits=float(table.cache_hits.mean())))
        for seed, r in a.iterrows():
            frozenrows.append(dict(seed=int(seed), budget=budget, standalone_ils_hr=float(r.loss_hr),
                frozen_GA_hr=frozen['planning_loss_hr'], delta_hr=float(r.loss_hr-frozen['planning_loss_hr']),
                sequence_sha256=r.sequence_sha256, frozen_sha256=frozen['sequence_sha256'], comparison_type='selected historical chromosome; not optimizer superiority'))
    csv('FAIR_COLD_START_GA_COMPARISON.csv', comparisons)
    csv('OPTIMIZER_DISTRIBUTIONS.csv', distribution)
    csv('FROZEN_GA_REFERENCE_COMPARISON.csv', frozenrows)
    pool = [read(p) for p in (OUT / 'main').glob('ils_s*/FINAL_*.json')]
    selected = min(pool, key=lambda r: (r['loss_hr'], r['sequence_sha256'], r['seed'], r['budget']))
    assert len(pool) == 40
    save(OUT / 'SELECTED_STANDALONE_ILS_CANDIDATE.json', dict(sequence=selected['sequence'],
        sequence_sha256=selected['sequence_sha256'], loss_hr=selected['loss_hr'], seed=selected['seed'], budget=selected['budget'],
        source_file=str((OUT / 'main' / f"ils_s{selected['seed']}" / f"FINAL_{selected['budget']}.json").relative_to(R)),
        source_sha256=sha(OUT / 'main' / f"ils_s{selected['seed']}" / f"FINAL_{selected['budget']}.json"),
        config=CONFIG, initialization='Impact-first only; no other optimized information',
        selection_rule=read(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json')['candidate_selection'],
        candidate_pool_observations=40, independent_main_seeds=20, selected_for_diagnostic_verification_only=True,
        no_refinement=True, no_formal_promotion=True, no_validation_access=True))
    main_final = df.sort_values('budget').groupby(['method', 'seed']).tail(1)
    smoke = [read(OUT / 'smoke' / f'ils_s{s}/FINAL_20000.json') for s in SMOKE]
    save(OUT / 'COMPUTATION_ACCOUNTING.json', dict(
        search_mean64_calls=int(main_final.distinct_evaluations.sum())+sum(r['distinct_evaluations'] for r in smoke),
        main_search_mean64_calls=int(main_final.distinct_evaluations.sum()), smoke_search_mean64_calls=160000,
        main_attempts=int(main_final.attempts.sum()), smoke_attempts=sum(r['attempts'] for r in smoke),
        main_cache_hits=int(main_final.cache_hits.sum()), smoke_cache_hits=sum(r['cache_hits'] for r in smoke),
        setup_mean64_calls=read(OUT / 'smoke_EXECUTION.json')['setup_objective_calls']+read(OUT / 'main_EXECUTION.json')['setup_objective_calls'],
        smoke_extra_compiled_sample_calls=512, smoke_production_sample_calls=24,
        main_worker_cpu_seconds=float(df[df.method == 'ILS'].sort_values('budget').groupby('seed').tail(1).cpu_seconds.sum()) + float(df[df.method == 'GA'].incremental_cpu_seconds.sum()),
        main_wrapper_wall_seconds=float(df[df.method == 'GA'].incremental_wrapper_wall_seconds.sum()),
        main_batch_wall_seconds=read(OUT / 'main_EXECUTION.json')['wall_seconds'],
        smoke_batch_wall_seconds=read(OUT / 'smoke_EXECUTION.json')['wall_seconds'],
        evaluations_are_complete_original64_means=True, no_replayed_prefixes=True,
        units='mean64 calls separate from individual-sample verification calls; continuations/checkpoints are not independent runs',
        completed_smoke_runs=8, completed_main_searches=40, completed_main_budget_observations=80,
        main_cost_records_with_same_state_continuation=True, no_new_physical_samples=True))
    print('SELECTED', selected['seed'], selected['budget'], selected['loss_hr'], selected['sequence_sha256'], flush=True)
    print(pd.DataFrame(comparisons).to_string(index=False), flush=True)


def verify():
    k, impact, model = load_model()
    context, decoder, _ = execution_context(k.ids)
    origins = decoder.origins(context['origins'])
    candidate = read(OUT / 'SELECTED_STANDALONE_ILS_CANDIDATE.json')
    ga = read(R / 'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json')
    sequences = dict(ILS=tuple(candidate['sequence']), FrozenGA=tuple(ga['sequence']), Impact=impact)
    losses, parity, components = {}, [], []
    tick = time.perf_counter()
    for label, seq in sequences.items():
        exact = per_sample(k, seq)
        losses[label] = np.array([production(k, context, seq, s) for s in range(64)])
        for s in range(64):
            assert abs(exact[s]-losses[label][s]) < 1e-8
            integrals, detail = trace(k, context, decoder, origins, seq, s)
            assert abs(integrals['L_total']-losses[label][s]) < 1e-8
            components.append(dict(strategy=label, sample=s, **integrals))
            parity.append(dict(strategy=label, sample=s, production_hr=float(losses[label][s]), compiled_hr=float(exact[s]), absolute_error_hr=abs(float(exact[s]-losses[label][s]))))
            if s == 15:
                save(OUT / f'SAMPLE15_{label}_EVENTS.json', detail)
        print('PRODUCTION_PASS', label, float(losses[label].mean()), flush=True)
    assert abs(losses['ILS'].mean()-candidate['loss_hr']) < 1e-8
    assert abs(losses['FrozenGA'].mean()-ga['planning_loss_hr']) < 1e-8
    csv('PRODUCTION_SAMPLE_PARITY.csv', parity)
    csv('ALL64_EXACT_LOSS_COMPONENTS.csv', components)
    perstate = pd.DataFrame(dict(sample=range(64), standalone_ILS_hr=losses['ILS'], frozen_GA_hr=losses['FrozenGA'], Impact_hr=losses['Impact'],
        ILS_minus_GA_hr=losses['ILS']-losses['FrozenGA'], ILS_minus_Impact_hr=losses['ILS']-losses['Impact']))
    csv('SAMPLE_INFLUENCE.csv', perstate)
    audit = {}
    comp = pd.DataFrame(components)
    for label in ('FrozenGA', 'Impact'):
        d = losses['ILS']-losses[label]
        result = influences(d)
        result.update(paired(d, family=2), quantiles_hr=np.quantile(d, [0, .05, .25, .5, .75, .95, 1]).tolist(),
            omission15_mean_delta_hr=float(np.delete(d, 15).mean()), sample15_delta_hr=float(d[15]),
            sample15_fraction_of_net_sum=float(d[15]/d.sum()),
            mean_component_delta_hr={f: float(comp[comp.strategy=='ILS'][f].mean()-comp[comp.strategy==label][f].mean()) for f in ('L_self', 'L_threshold', 'L_source', 'L_total')},
            sample15_component_delta_hr={f: float(comp[(comp.strategy=='ILS')&(comp['sample']==15)][f].iloc[0]-comp[(comp.strategy==label)&(comp['sample']==15)][f].iloc[0]) for f in ('L_self', 'L_threshold', 'L_source', 'L_total')})
        # The legacy helper flags positive LOO values; here explicitly compare signs.
        result['leave_one_out_sign_reversal_count'] = sum(np.sign(r['leave_one_out_mean_delta_hr']) != np.sign(d.mean()) for r in result['leave_one_out'])
        audit[label] = result
    save(OUT / 'PRODUCTION_PARITY_AND_SAMPLE_INFLUENCE.json', dict(status='ALL192_PRODUCTION_AND_EVENT_PARITY_PASS',
        selected_candidate=candidate, frozen_GA_identity=ga['sequence_sha256'], model_identity=model,
        planning_samples=64, production_sample_calls=192, compiled_sample_calls=192,
        event_decoder_calls=192, event_extra_objective_calls=0,
        max_absolute_parity_error_hr=max(r['absolute_error_hr'] for r in parity),
        selected_ILS_production_mean_hr=float(losses['ILS'].mean()), comparisons=audit,
        wall_seconds=time.perf_counter()-tick, new_physical_samples=0, no_validation_access=True,
        interpretation='Selected-sequence development diagnostics; decomposition is exact whole-schedule accounting, not causal effects of individual station edits'))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('task', choices=['smoke', 'summarize', 'verify'])
    a = p.parse_args()
    {'smoke': smoke_audit, 'summarize': summarize, 'verify': verify}[a.task]()
