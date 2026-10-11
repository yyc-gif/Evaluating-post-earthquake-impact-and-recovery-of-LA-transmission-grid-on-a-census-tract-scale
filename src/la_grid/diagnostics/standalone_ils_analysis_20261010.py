"""Planning-only paired inference and independent production-path verification."""
from __future__ import annotations
import argparse
import itertools
import random
import subprocess
import time

import numpy as np
import pandas as pd
from scipy import stats

from la_grid.diagnostics.standalone_ils_20261010 import (
    R, OUT, SMOKE, MAIN, EXTEND, BUDGETS, CONFIG, StandaloneILS, load_model, read, save, sha, hydrate, identity, read_state,
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


def restricted_event_loss(events, terminal_horizon, endpoint):
    """Clip the existing left-step event trace without rescoring a schedule."""
    assert 0 < endpoint <= terminal_horizon
    times = np.asarray([e['time_hr'] for e in events] + [terminal_horizon])
    assert times[0] == 0 and np.all(np.diff(times) > 0)
    widths = np.maximum(0, np.minimum(times[1:], endpoint)-times[:-1])
    return float(widths @ (1-np.asarray([e['effective_service'] for e in events])))


def cached_replay():
    """Replay recorded ILS fitness lookups, with zero physical evaluator calls."""
    tick, cpu, rows = time.perf_counter(), time.process_time(), []
    for seed in MAIN:
        folder = OUT / 'main' / f'ils_s{seed}'
        actual = read_state(folder / 'STATE.pkl.gz')
        index = {s:i for i,s in enumerate(actual['ids'])}
        def lookup(seq):
            return actual['cache'][bytes(index[s] for s in seq)]
        search = StandaloneILS(actual['ids'], tuple(actual['initial_sequences'][0]), lookup, seed, actual['config'])
        boundaries = [100000,250000,500000] if seed in EXTEND else [100000]
        for budget in boundaries:
            d = search.run(budget)
            row = read(folder / f'FINAL_{budget}.json')
            assert d['attempts'] == row['attempts'] and d['accepted'] == row['accepted'] and d['restarts'] == row['restarts']
            assert identity(d['best']) == row['sequence_sha256'] and -d['best_score'] == row['loss_hr']
        ignored = {'wall_seconds','cpu_seconds','objective_seconds','checkpoints'}
        assert {k:v for k,v in d.items() if k not in ignored} == {k:v for k,v in actual.items() if k not in ignored}
        assert list(d['cache']) == list(actual['cache'])
        checkpoints = read(folder / 'BUDGET_CHECKPOINTS.json')
        fields = ('budget','loss_hr','attempts','cache_hits','accepted','restarts','sequence','sequence_sha256')
        assert [{f:r[f] for f in fields} for r in d['checkpoints']] == [{f:r[f] for f in fields} for r in checkpoints]
        rows.append(dict(seed=seed, distinct_cache_reads=len(actual['cache']), attempts=d['attempts'],
            all_budget_prefixes_exact=True, final_rng_and_logical_state_exact=True, private_key_order_exact=True,
            loss_sha_exact=True, original_checkpoint_time_bytes_recreated=False))
        print('CACHE_REPLAY_PASS',seed,flush=True)
    save(OUT / 'PRODUCTION_SIZE_ILS_CACHE_REPLAY_QA.json',dict(status='ALL20_FULL_TRAJECTORIES_PASS',rows=rows,
        distinct_saved_fitness_reads=sum(r['distinct_cache_reads'] for r in rows),
        physical_objective_calls=0, fresh_optimizer_searches=0,
        cpu_seconds=time.process_time()-cpu, wall_seconds=time.perf_counter()-tick,
        original_intermediate_checkpoint_payloads='Overwritten in normal continuation; observed digests retained; final states and exact logical prefix replay retained',
        timing_and_gzip_bytes_excluded_from_semantic_equality=True))


def summarize():
    assert read(OUT / 'main_EXECUTION.json')['all_completed']
    rows, convergence, initialization_checks, final_sequences = [], [], [], []
    valid_positions = set(range(92))
    baseline_model = read(OUT / 'SMOKE_QA.json')['model']
    implementation_hash = sha(R / 'src/la_grid/diagnostics/standalone_ils_20261010.py')
    for method in ('ILS', 'GA'):
        for seed in MAIN:
            folder = OUT / 'main' / f'{method.lower()}_s{seed}'
            boundaries = [100000, 250000, 500000] if seed in EXTEND else [100000]
            for budget in boundaries:
                row = read(folder / f'FINAL_{budget}.json')
                assert row['completed'] and row['distinct_evaluations'] == budget
                assert row['model_identity'] == baseline_model and row['implementation_sha256'] == implementation_hash
                assert identity(row['sequence']) == row['sequence_sha256']
                assert len(row['sequence']) == len(set(row['sequence'])) == 92
                assert row['initial_archive'] == row['initial_sequences'][:1]
                final_sequences.append(dict(method=method, seed=seed, budget=budget,
                    loss_hr=row['loss_hr'], sequence=row['sequence'], sequence_sha256=row['sequence_sha256'],
                    source_receipt=str((folder/f'FINAL_{budget}.json').relative_to(OUT)).replace('\\','/'),
                    source_receipt_sha256=sha(folder/f'FINAL_{budget}.json')))
                flat = {k: v for k, v in row.items() if k not in ('initial_sequences', 'initial_archive', 'model_identity', 'sequence', 'config')}
                rows.append(flat)
            if method == 'ILS':
                checkpoints = read(folder / 'BUDGET_CHECKPOINTS.json')
                final_state = read_state(folder / 'STATE.pkl.gz')
                assert len(final_state['cache']) == boundaries[-1]
                assert all(len(key) == 92 and set(key) == valid_positions for key in final_state['cache'])
                assert final_state['initial_sequences'] == final_state['initial_archive']
                assert len(final_state['initial_archive']) == 1
                assert final_state['attempts'] == 1+final_state['local_proposals']+final_state['restarts']
                for c in checkpoints:
                    convergence.append(dict(method=method, seed=seed, **c))
            else:
                final_state = read_state(folder / 'CHECKPOINT.pkl.gz')
                assert len(final_state['cache']) == boundaries[-1]
                assert all(len(key) == 92 and set(key) == valid_positions for key in final_state['cache'])
                init = read(folder / 'INITIALIZATION_RECEIPT.json')
                rng = random.Random(seed)
                with np.load(folder / 'CANDIDATES.npz') as z:
                    domain = tuple(z['station_ids'].astype(str))
                expected = init['initial_archive'] + [rng.sample(domain, 92) for _ in range(99)]
                assert init['initial_sequences'] == expected and len(init['initial_archive']) == 1
                assert final_state['state']['expensive_calls'] == boundaries[-1]
                assert final_state['state']['lookup_calls'] == 0
                checkpoints = pd.read_csv(folder / 'BUDGET_CHECKPOINTS.csv')
                for _, c in checkpoints.iterrows():
                    convergence.append(dict(method=method, seed=seed, budget=int(c.distinct_evaluations), loss_hr=c.best_service_loss_hr,
                        attempts=int(c.total_attempts), cache_hits=int(c.total_attempts-c.distinct_evaluations),
                        objective_seconds=c.objective_seconds, wall_seconds=c.elapsed_seconds, sequence_sha256=c.sequence_sha256))
            initialization_checks.append(dict(method=method, seed=seed, final_distinct_evaluations=boundaries[-1],
                all_cached_permutations_valid=True, initializer_exact=True, private_cache=True,
                no_external_lookup_values=True, checkpoint_sha256=sha(folder / ('STATE.pkl.gz' if method=='ILS' else 'CHECKPOINT.pkl.gz'))))
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
    save(OUT / 'ALL_FINAL_MAIN_SEQUENCES.json',dict(count=80, independent_searches=40, records=final_sequences,
        dependent_budget_observations_explicit=True, encoding='Ordered station IDs separated by newline, final newline, UTF-8'))
    save(OUT / 'ALL_MAIN_INITIALIZATION_AND_PERMUTATION_QA.json',dict(status='PASS', rows=initialization_checks,
        count=40, expensive_verification_calls=0, no_shared_scored_candidates=True))
    pool = [read(p) for p in (OUT / 'main').glob('ils_s*/FINAL_*.json')]
    selected = min(pool, key=lambda r: (r['loss_hr'], r['sequence_sha256'], r['seed'], r['budget']))
    assert len(pool) == 40
    save(OUT / 'SELECTED_STANDALONE_ILS_CANDIDATE.json', dict(sequence=selected['sequence'],
        sequence_sha256=selected['sequence_sha256'], loss_hr=selected['loss_hr'], seed=selected['seed'], budget=selected['budget'],
        source_file=str((OUT / 'main' / f"ils_s{selected['seed']}" / f"FINAL_{selected['budget']}.json").relative_to(R)),
        source_sha256=sha(OUT / 'main' / f"ils_s{selected['seed']}" / f"FINAL_{selected['budget']}.json"),
        implementation_sha256=selected['implementation_sha256'],
        config=CONFIG, initialization='Impact-first only; no other optimized information',
        selection_rule=read(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json')['candidate_selection'],
        candidate_pool_observations=40, independent_main_seeds=20, selected_for_diagnostic_verification_only=True,
        no_refinement=True, no_formal_promotion=True, no_validation_access=True))
    main_final = df.sort_values('budget').groupby(['method', 'seed']).tail(1)
    smoke = [read(OUT / 'smoke' / f'ils_s{s}/FINAL_20000.json') for s in SMOKE]
    replay = read(OUT / 'PRODUCTION_SIZE_ILS_CACHE_REPLAY_QA.json')
    assert replay['physical_objective_calls'] == 0 and replay['status'] == 'ALL20_FULL_TRAJECTORIES_PASS'
    save(OUT / 'COMPUTATION_ACCOUNTING.json', dict(
        search_mean64_calls=int(main_final.distinct_evaluations.sum())+sum(r['distinct_evaluations'] for r in smoke),
        main_search_mean64_calls=int(main_final.distinct_evaluations.sum()), smoke_search_mean64_calls=160000,
        main_attempts=int(main_final.attempts.sum()), smoke_attempts=sum(r['attempts'] for r in smoke),
        main_cache_hits=int(main_final.cache_hits.sum()), smoke_cache_hits=sum(r['cache_hits'] for r in smoke),
        setup_mean64_calls=read(OUT / 'smoke_EXECUTION.json')['setup_objective_calls']+read(OUT / 'main_EXECUTION.json')['setup_objective_calls'],
        smoke_extra_compiled_sample_calls=512, smoke_production_sample_calls=24,
        main_worker_cpu_seconds=float(df[df.method == 'ILS'].sort_values('budget').groupby('seed').tail(1).cpu_seconds.sum()) + float(df[df.method == 'GA'].incremental_cpu_seconds.sum()),
        main_worker_setup_seconds=float(df.drop_duplicates('worker_pid').worker_setup_seconds.sum()),
        main_initialized_workers=int(df.worker_pid.nunique()),
        main_wrapper_wall_seconds=float(df[df.method == 'GA'].incremental_wrapper_wall_seconds.sum()),
        main_batch_wall_seconds=read(OUT / 'main_EXECUTION.json')['wall_seconds'],
        smoke_batch_wall_seconds=read(OUT / 'smoke_EXECUTION.json')['wall_seconds'],
        evaluations_are_complete_original64_means=True, no_replayed_prefixes=True,
        units='mean64 calls separate from individual-sample verification calls; continuations/checkpoints are not independent runs',
        completed_smoke_runs=8, completed_main_searches=40, completed_main_budget_observations=80,
        main_cost_records_with_same_state_continuation=True, no_new_physical_samples=True))
    cost = read(OUT / 'COMPUTATION_ACCOUNTING.json')
    cost.update(cache_replay_saved_fitness_reads=replay['distinct_saved_fitness_reads'],
        cache_replay_physical_objective_calls=0, cache_replay_cpu_seconds=replay['cpu_seconds'],
        cache_replay_wall_seconds=replay['wall_seconds'], cache_replay_not_new_seed_replications=True,
        independent_selected_candidate_verification='PENDING')
    save(OUT / 'COMPUTATION_ACCOUNTING.json', cost)
    print('SELECTED', selected['seed'], selected['budget'], selected['loss_hr'], selected['sequence_sha256'], flush=True)
    print(pd.DataFrame(comparisons).to_string(index=False), flush=True)


def verify():
    k, impact, model = load_model()
    assert model == read(OUT / 'SMOKE_QA.json')['model']
    context, decoder, _ = execution_context(k.ids)
    origins = decoder.origins(context['origins'])
    candidate = read(OUT / 'SELECTED_STANDALONE_ILS_CANDIDATE.json')
    ga = read(R / 'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json')
    sequences = dict(ILS=tuple(candidate['sequence']), FrozenGA=tuple(ga['sequence']), Impact=impact)
    complete_tables = ('PRODUCTION_SAMPLE_PARITY.csv','ALL64_EXACT_LOSS_COMPONENTS.csv',
        'PLANNING_VS_480H_EVENT_AUDIT.csv','SAMPLE_INFLUENCE.csv')
    if all((OUT/n).exists() for n in complete_tables):
        refs = read(OUT / 'REFERENCE_AND_SELECTED_SEQUENCES.json')
        assert all(refs[name]['sequence_sha256'] == identity(seq) for name,seq in sequences.items())
        finalize_verification(model, candidate, ga, reused_tables=True)
        return
    save(OUT / 'REFERENCE_AND_SELECTED_SEQUENCES.json',{
        name: dict(sequence=list(seq), sequence_sha256=identity(seq), station_count=92,
                   post_search_comparison_only=True) for name,seq in sequences.items()})
    losses, parity, components, horizons = {}, [], [], []
    tick = time.perf_counter()
    for label, seq in sequences.items():
        exact = per_sample(k, seq)
        losses[label] = np.array([production(k, context, seq, s) for s in range(64)])
        for s in range(64):
            assert abs(exact[s]-losses[label][s]) < 1e-8
            integrals, detail = trace(k, context, decoder, origins, seq, s)
            assert abs(integrals['L_total']-losses[label][s]) < 1e-8
            restricted = restricted_event_loss(detail['events'], k.horizon, 480.)
            full = restricted_event_loss(detail['events'], k.horizon, k.horizon)
            assert abs(full-integrals['L_total']) < 1e-8
            horizons.append(dict(strategy=label, sample=s, planning_horizon_hr=k.horizon,
                manuscript_horizon_hr=480., planning_loss_hr=full, loss_0_480_hr=restricted,
                loss_after_480_hr=full-restricted,
                final_effective_service=detail['events'][-1]['effective_service']))
            components.append(dict(strategy=label, sample=s, **integrals))
            parity.append(dict(strategy=label, sample=s, production_hr=float(losses[label][s]), compiled_hr=float(exact[s]), absolute_error_hr=abs(float(exact[s]-losses[label][s]))))
            if s == 15:
                save(OUT / f'SAMPLE15_{label}_EVENTS.json', detail)
        print('PRODUCTION_PASS', label, float(losses[label].mean()), flush=True)
    assert abs(losses['ILS'].mean()-candidate['loss_hr']) < 1e-8
    assert abs(losses['FrozenGA'].mean()-ga['planning_loss_hr']) < 1e-8
    csv('PRODUCTION_SAMPLE_PARITY.csv', parity)
    csv('ALL64_EXACT_LOSS_COMPONENTS.csv', components)
    csv('PLANNING_VS_480H_EVENT_AUDIT.csv', horizons)
    assert max(abs(r['loss_after_480_hr']) for r in horizons) < 1e-8
    perstate = pd.DataFrame(dict(sample=range(64), standalone_ILS_hr=losses['ILS'], frozen_GA_hr=losses['FrozenGA'], Impact_hr=losses['Impact'],
        ILS_minus_GA_hr=losses['ILS']-losses['FrozenGA'], ILS_minus_Impact_hr=losses['ILS']-losses['Impact']))
    csv('SAMPLE_INFLUENCE.csv', perstate)
    finalize_verification(model, candidate, ga, verification_seconds=time.perf_counter()-tick)


def finalize_verification(model, candidate, ga, verification_seconds=None, reused_tables=False):
    tick = time.perf_counter()
    names = ('PRODUCTION_SAMPLE_PARITY.csv','ALL64_EXACT_LOSS_COMPONENTS.csv','PLANNING_VS_480H_EVENT_AUDIT.csv')
    parity, comp, horizons = [pd.read_csv(OUT/n, float_precision='round_trip') for n in names]
    losses = {}
    for label in ('ILS','FrozenGA','Impact'):
        p = parity[parity.strategy.eq(label)].sort_values('sample')
        c = comp[comp.strategy.eq(label)].sort_values('sample')
        h = horizons[horizons.strategy.eq(label)].sort_values('sample')
        assert p['sample'].tolist() == c['sample'].tolist() == h['sample'].tolist() == list(range(64))
        assert np.max(np.abs(p.production_hr-p.compiled_hr)) < 1e-8
        assert np.max(np.abs(p.production_hr.to_numpy()-c.L_total.to_numpy())) < 1e-8
        assert np.max(np.abs(c.L_self+c.L_threshold+c.L_source-c.L_total)) < 1e-8
        assert np.max(np.abs(h.loss_after_480_hr)) < 1e-8
        assert np.all(h.planning_horizon_hr == model['horizon_hr'])
        losses[label] = p.production_hr.to_numpy()
    assert abs(losses['ILS'].mean()-candidate['loss_hr']) < 1e-8
    assert abs(losses['FrozenGA'].mean()-ga['planning_loss_hr']) < 1e-8
    audit = {}
    for label in ('FrozenGA', 'Impact'):
        d = losses['ILS']-losses[label]
        result = influences(d)
        result.update(paired(d, family=2), quantiles_hr=np.quantile(d, [0, .05, .25, .5, .75, .95, 1]).tolist(),
            omission15_mean_delta_hr=float(np.delete(d, 15).mean()), sample15_delta_hr=float(d[15]),
            sample15_fraction_of_net_sum=float(d[15]/d.sum()),
            mean_component_delta_hr={f: float(comp[comp.strategy=='ILS'][f].mean()-comp[comp.strategy==label][f].mean()) for f in ('L_self', 'L_threshold', 'L_source', 'L_total')},
            sample15_component_delta_hr={f: float(comp[(comp.strategy=='ILS')&(comp['sample']==15)][f].iloc[0]-comp[(comp.strategy==label)&(comp['sample']==15)][f].iloc[0]) for f in ('L_self', 'L_threshold', 'L_source', 'L_total')})
        # The legacy helper flags positive LOO values; here explicitly compare signs.
        result['leave_one_out_sign_reversal_count'] = int(sum(np.sign(r['leave_one_out_mean_delta_hr']) != np.sign(d.mean()) for r in result['leave_one_out']))
        audit[label] = result
    save(OUT / 'PRODUCTION_PARITY_AND_SAMPLE_INFLUENCE.json', dict(status='ALL192_PRODUCTION_AND_EVENT_PARITY_PASS',
        selected_candidate=candidate, frozen_GA_identity=ga['sequence_sha256'], model_identity=model,
        planning_samples=64, production_sample_calls=192, compiled_sample_calls=192,
        event_decoder_calls=192, event_extra_objective_calls=0,
        max_absolute_parity_error_hr=float(parity.absolute_error_hr.max()),
        selected_ILS_production_mean_hr=float(losses['ILS'].mean()), comparisons=audit,
        horizon_audit=dict(original_planning_horizon_hr=model['horizon_hr'], manuscript_and_prior_validation_horizon_hr=480.,
            all192_zero_post480_loss=True, max_absolute_post480_loss_hr=float(horizons.loss_after_480_hr.abs().max()),
            basis='Reintegrated existing native event traces; no new objective calls or altered planning horizon',
            future_samples_480h_equivalence_not_assumed=True),
        wall_seconds=verification_seconds, report_finalization_wall_seconds=time.perf_counter()-tick,
        reused_completed_tables=reused_tables, finalization_additional_physical_calls=0,
        completed_table_sha256={n: sha(OUT/n) for n in names},
        original_verification_timer_unavailable_due_to_serialization_failure=reused_tables,
        new_physical_samples=0, no_validation_access=True,
        interpretation='Selected-sequence development diagnostics; decomposition is exact whole-schedule accounting, not causal effects of individual station edits'))
    cost = read(OUT / 'COMPUTATION_ACCOUNTING.json')
    cost.update(independent_selected_candidate_verification='ALL192_PRODUCTION_AND_EVENT_PARITY_PASS',
        selected_reference_production_sample_calls=192, selected_reference_compiled_sample_calls=192,
        event_decoder_calls=192, event_extra_objective_calls=0,
        verification_wall_seconds=read(OUT / 'PRODUCTION_PARITY_AND_SAMPLE_INFLUENCE.json')['wall_seconds'])
    cost.update(verification_report_finalization_wall_seconds=time.perf_counter()-tick,
        verification_original_scoring_not_repeated=reused_tables,
        verification_serialization_repair='NumPy LOO count cast to Python int; completed numerical tables reused' if reused_tables else None)
    save(OUT / 'COMPUTATION_ACCOUNTING.json', cost)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('task', choices=['smoke', 'summarize', 'verify', 'replay'])
    a = p.parse_args()
    {'smoke': smoke_audit, 'summarize': summarize, 'verify': verify, 'replay': cached_replay}[a.task]()
