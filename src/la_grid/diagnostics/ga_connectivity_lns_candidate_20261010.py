"""Independent production parity and planning-state influence for retained bests."""
from __future__ import annotations
import argparse
import json

import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_connectivity_lns_local_20261010 import OUT, bank
from la_grid.diagnostics.ga_connectivity_lns_audit_20261010 import results, FROZEN, REFINED
from la_grid.diagnostics.ga_research_collect_20261009 import save, long_path
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import RealizationInputs, evaluate_completion_step_functionality
from la_grid.revision.r1_source_gate import evaluate_source_gate
from la_grid.revision.r1_ga_revision import evaluate_direct_population_burden_aggregate
from la_grid.revision.formal.schedule import _decode


def influence(delta):
    d = np.asarray(delta, float)
    loo = (d.sum() - d) / 63
    order = np.argsort(d)
    return dict(mean_delta_hr=float(d.mean()), median_delta_hr=float(np.median(d)),
        sd_delta_hr=float(d.std(ddof=1)), empirical_5_25_75_95=list(map(float, np.quantile(d, [.05, .25, .75, .95]))),
        improved_states=int((d < -1e-9).sum()), worsened_states=int((d > 1e-9).sum()),
        tied_states=int((abs(d) <= 1e-9).sum()), sample15_delta_hr=float(d[15]),
        without15_mean_delta_hr=float(np.delete(d, 15).mean()),
        loo_min_hr=float(loo.min()), loo_max_hr=float(loo.max()),
        loo_ranking_reversal_indices=np.flatnonzero(np.sign(loo) != np.sign(d.mean())).tolist(),
        leave_most_beneficial_out=[dict(k=k, indices=order[:k].tolist(),
            remaining_mean_delta_hr=float(np.delete(d, order[:k]).mean())) for k in (1, 2, 4, 8)],
        largest_beneficial=[dict(realization=int(i), delta_hr=float(d[i])) for i in order[:8]],
        largest_adverse=[dict(realization=int(i), delta_hr=float(d[i])) for i in order[-8:][::-1]])


def components(kernel, context, seq, reference, sample):
    decoded = {name: _decode(np.array([kernel.index[x] for x in order], np.int64),
        kernel.damage[sample], kernel.duration[sample], kernel.origin_index, kernel.base, kernel.travel)
        for name, order in [('candidate', seq), ('frozen_ga', reference)]}
    clock = np.unique(np.r_[0., kernel.horizon, *[x[0][np.isfinite(x[0])] for x in decoded.values()]])
    mass = kernel.station_mass / kernel.total_mass
    fields = ('L_self', 'L_threshold', 'L_source', 'L_total')
    totals = {}
    gates = {}
    for name, data in decoded.items():
        raw = evaluate_completion_step_functionality(damage_state=pd.Series(kernel.damage[sample], index=kernel.ids),
            completion_time_hr=pd.Series(data[0], index=kernel.ids), time_hr=clock)
        trace = evaluate_source_gate(raw, context['graph'], context['sources'], threshold=.5)
        totals[name] = {f: float(np.dot(np.diff(clock), getattr(trace, f).loc[:, list(kernel.ids)].to_numpy()[:-1] @ mass))
            for f in fields}
        gates[name] = trace.e.loc[:, list(kernel.ids)].to_numpy()
        assert abs(sum(totals[name][f] for f in fields[:3]) - totals[name]['L_total']) < 1e-8
    deltas = {f: totals['candidate'][f] - totals['frozen_ga'][f] for f in fields}
    interval = (gates['frozen_ga'][:-1] - gates['candidate'][:-1]) @ mass * np.diff(clock)
    best = np.argsort(interval)[:8]
    return dict(sample=sample, component_integrals_hr=totals, component_changes_hr=deltas,
        earlier_completions=int(np.sum(decoded['candidate'][0] < decoded['frozen_ga'][0] - 1e-9)),
        later_completions=int(np.sum(decoded['candidate'][0] > decoded['frozen_ga'][0] + 1e-9)),
        total_directed_travel_change_hr=float(np.nansum(decoded['candidate'][2]) - np.nansum(decoded['frozen_ga'][2])),
        beneficial_intervals=[dict(start_hr=float(clock[i]), end_hr=float(clock[i + 1]),
            weighted_loss_change_hr=float(interval[i]),
            affected_stations=[kernel.ids[j] for j in np.flatnonzero(abs(gates['candidate'][i] - gates['frozen_ga'][i]) > 1e-9)])
            for i in best], descriptive_not_station_causality=True)


def bank_leverage(kernel, sequence, label):
    rows, _, _, _ = bank(kernel, sequence)
    order = np.array([kernel.index[x] for x in sequence], np.int64)
    finishes, dispatches = [], []
    for r in range(64):
        data = _decode(order, kernel.damage[r], kernel.duration[r], kernel.origin_index, kernel.base, kernel.travel)
        finishes.append(data[0])
        dispatches.append(data[5])
    finishes, dispatches = np.asarray(finishes), np.asarray(dispatches)
    output = []
    for row in rows[:20]:
        group = list(row['group'])
        active = kernel.damage[:, group] >= 2
        initial_travel = kernel.base[kernel.origin_index[:, None], group].min(axis=0)
        # This is a relaxed independent-origin benchmark, not a feasible schedule
        # or a proven bound when a later directed inter-task leg is shorter.
        removable = finishes[:, group] - kernel.duration[:, group] - initial_travel
        relevant = np.isfinite(removable) & active
        ratio = np.clip(removable[relevant], 0, None) / finishes[:, group][relevant]
        output.append({**row, 'group': [kernel.ids[i] for i in group],
            'functional_at_t0_fraction': float(np.mean(kernel.damage[:, group] <= 1)),
            'ds2plus_first_wave_fraction': float(np.mean(dispatches[:, group][active] < 57)),
            'relaxed_queue_travel_delay_fraction_mean': float(ratio.mean()) if len(ratio) else None,
            'interpretation': 'Witness wait includes irreducible sampled repair duration; high mass-wait is not automatically high dispatch leverage'})
    weights = np.array([x['weight'] for x in rows])
    shares15 = np.array([x['sample15_fraction'] for x in rows])
    ranks = sorted(rows, key=lambda x: (-x['weight_without15'], x['group']))
    return dict(label=label, top20=output,
        top10_group_overlap_without15=len({x['group'] for x in rows[:10]} & {x['group'] for x in ranks[:10]}),
        weighted_sample15_share=float(np.dot(weights, shares15) / weights.sum()),
        mean_bundle_sample_support=float(np.mean([x['support'] for x in rows])))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--budget', type=int, default=100000)
    a = p.parse_args()
    records, summary = results(a.budget)
    kernel, _, quality, identity = load()
    context, _, _ = execution_context(kernel.ids)
    frozen = json.loads((FROZEN / 'SELECTED_SEQUENCE.json').read_text())
    refined = json.loads(REFINED.read_text())
    selected = {}
    for method in sorted({r['method'] for r in records}):
        r = min((q for q in records if q['method'] == method), key=lambda x: (x['search_best_loss_hr'], x['seed'], x['sequence_sha256']))
        selected[method] = dict(sequence=r['best_sequence'], sequence_sha256=r['sequence_sha256'],
            expected_loss_hr=r['search_best_loss_hr'], seed=r['seed'], budget=a.budget)
    selected['frozen_ga'] = dict(sequence=frozen['sequence'], sequence_sha256=frozen['sequence_sha256'], expected_loss_hr=frozen['planning_loss_hr'])
    selected['refined_ils'] = dict(sequence=refined['sequence'], sequence_sha256=refined['sequence_sha256'], expected_loss_hr=refined['loss_hr'])
    arrays, rows = {}, []
    def gate(raw):
        return evaluate_source_gate(raw, context['graph'], context['sources'], threshold=.5)
    for label, item in selected.items():
        seq = item['sequence']
        assert old.identity(seq) == item['sequence_sha256']
        exact = old.per_sample(kernel, seq)
        production = []
        for r in range(64):
            realization = RealizationInputs(f'2pc50__planning_{r:04}', pd.Series(kernel.damage[r], index=kernel.ids),
                pd.Series(kernel.duration[r], index=kernel.ids))
            value = evaluate_direct_population_burden_aggregate(sequence=seq, realization=realization,
                crew_origin_ids=context['origins'], base_to_task_hr=context['base'], task_to_task_hr=context['task'],
                horizon_hr=kernel.horizon, source_gate=gate, station_population_mass=kernel.station_mass,
                population_resolved_mass=kernel.total_mass)
            assert abs(value - exact[r]) < 1e-8
            production.append(value)
            rows.append(dict(label=label, sample=r, production_loss_hr=value, compiled_loss_hr=float(exact[r]),
                absolute_error_hr=abs(value - exact[r])))
        arrays[label] = np.asarray(production)
        assert abs(arrays[label].mean() - item['expected_loss_hr']) < 1e-8
        print('CANDIDATE_PARITY_PASS', label, float(arrays[label].mean()), flush=True)
    comparisons, event_rows = {}, []
    for label in selected:
        if label in ('frozen_ga', 'refined_ils'):
            continue
        comparisons[label] = {reference: influence(arrays[label] - arrays[reference]) for reference in ('frozen_ga', 'refined_ils')}
        delta = arrays[label] - arrays['frozen_ga']
        for r in sorted({15, int(np.argmin(delta)), int(np.argmax(delta))}):
            row = components(kernel, context, selected[label]['sequence'], frozen['sequence'], r)
            assert abs(row['component_changes_hr']['L_total'] - delta[r]) < 1e-8
            event_rows.append(dict(candidate=label, **row))
    save(OUT / f'CANDIDATE_PRODUCTION_AND_INFLUENCE_{a.budget}.json', dict(status='ALL_64_PRODUCTION_PARITY_PASS',
        selected=selected, comparisons=comparisons, planning_identity=identity,
        maximum_absolute_parity_error_hr=max(x['absolute_error_hr'] for x in rows),
        production_sample_calls=len(rows), compiled_sample_calls=len(rows),
        selection_not_validation=True, formal_candidate_replaced=False, new_physical_samples=0))
    pd.DataFrame(rows).to_csv(long_path(OUT / f'CANDIDATE_PER_REALIZATION_{a.budget}.csv'), index=False)
    save(OUT / f'CANDIDATE_EVENT_COMPONENTS_{a.budget}.json', event_rows)
    save(OUT / f'BUNDLE_SCHEDULING_LEVERAGE_{a.budget}.json', [bank_leverage(kernel, quality, 'shared_prior'),
        *[bank_leverage(kernel, selected[m]['sequence'], m) for m in ('connectivity_lns', 'random_lns', 'scheduling_lns')]])


if __name__ == '__main__':
    main()
