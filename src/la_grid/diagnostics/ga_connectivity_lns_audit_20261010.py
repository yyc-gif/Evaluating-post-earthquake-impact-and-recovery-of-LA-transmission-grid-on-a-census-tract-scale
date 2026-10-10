"""Read-only evidence analysis, original-proposal replay, and validation readiness."""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
import random
import shutil
import subprocess

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import t as student_t

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_connectivity_lns_local_20261010 import OUT, METHODS, SEEDS, LARGE_SEEDS, source_times, bank
from la_grid.diagnostics.ga_research_collect_20261009 import save, long_path
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.diagnostics.ga_schedule_aware_lns_20261010 import schedule_bank
from la_grid.diagnostics.ga_schedule_aware_lns_repair_v2_20261010 import repair_candidates
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.formal.schedule import _decode
from la_grid.core.C257H_Project_Main import sample_damage_states, damage_to_functionality_and_repair, draw_positive_normal

FROZEN = REPO_ROOT / 'results/diagnostics/final_ga_method_20261009'
REFINED = REPO_ROOT / 'results/diagnostics/ga_deeper_research_20261009/ILS_REFINED_BEST_SEED304_PLANNING_CANDIDATE.json'


def sha(path):
    return hashlib.sha256(long_path(path).read_bytes()).hexdigest()


def paired(delta, family):
    x = np.asarray(delta, float)
    n = len(x)
    se = x.std(ddof=1) / np.sqrt(n)
    half = student_t.ppf(1 - .05 / (2 * family), n - 1) * se
    rng = np.random.default_rng(2026101012)
    boot = x[rng.integers(0, n, (20000, n))].mean(axis=1)
    return dict(n=n, mean_delta_hr=float(x.mean()), median_delta_hr=float(np.median(x)),
        simultaneous_95=list(map(float, [x.mean() - half, x.mean() + half])),
        pointwise_seed_bootstrap_95=list(map(float, np.quantile(boot, [.025, .975]))),
        family=family, wins=int((x < -1e-9).sum()), losses=int((x > 1e-9).sum()),
        ties=int((abs(x) <= 1e-9).sum()))


def results(budget=100000):
    seeds = SEEDS if budget == 100000 else LARGE_SEEDS
    records = []
    expected_ids = set(json.loads((FROZEN / 'SELECTED_SEQUENCE.json').read_text())['sequence'])
    for seed in seeds:
        for method in METHODS:
            p = OUT / f'budget_{budget}/seed_{seed}/{method}.json'
            r = json.loads(long_path(p).read_text())
            assert r['completed_budget'] and r['distinct_evaluations'] == budget
            assert r['seed'] == seed and r['method'] == method and r['budget'] == budget
            assert set(r['best_sequence']) == expected_ids and len(r['best_sequence']) == 92
            assert old.identity(r['best_sequence']) == r['sequence_sha256']
            records.append(r)
    losses = {m: np.array([r['search_best_loss_hr'] for r in records if r['method'] == m]) for m in METHODS}
    primary = [dict(candidate=METHODS[0], reference=m, **paired(losses[METHODS[0]] - losses[m], 4)) for m in METHODS[1:]]
    all_pairs = [dict(candidate=a, reference=b, **paired(losses[a] - losses[b], 10))
        for i, a in enumerate(METHODS) for b in METHODS[i + 1:]]
    method_rows = []
    for m in METHODS:
        rs = [r for r in records if r['method'] == m]
        a = losses[m]
        method_rows.append(dict(method=m, mean_loss_hr=float(a.mean()), sd_loss_hr=float(a.std(ddof=1)),
            median_loss_hr=float(np.median(a)), min_loss_hr=float(a.min()), max_loss_hr=float(a.max()),
            mean_attempts=float(np.mean([r['attempted_evaluations'] for r in rs])),
            mean_wall_seconds=float(np.mean([r['elapsed_wall_seconds'] for r in rs])),
            mean_accepted_current_improvements=float(np.mean([r['accepted_moves'] for r in rs])) if m != 'ga_baseline' else None,
            mean_archive_improvements_below_prior=float(np.mean([sum(v['best_loss_hr'] < 33.03813174326729 - 1e-9
                for v in r['strict_improvements']) for r in rs])) if m != 'ga_baseline' else None,
            archive_count_note='GA reference wrapper does not serialize best_path; unavailable, not zero' if m == 'ga_baseline' else 'Current acceptances and archive records distinguished',
            means_of_mechanism_counts={k: float(np.mean([r.get('mechanism_counts', {}).get(k, 0) for r in rs]))
                for k in sorted(set().union(*(r.get('mechanism_counts', {}) for r in rs)))}))
    promising = []
    for m in METHODS[:3]:
        if all(losses[m].mean() < losses[b].mean() and np.sum(losses[m] < losses[b] - 1e-9) >= 12 for b in METHODS[3:]):
            promising.append(m)
        elif losses[m].min() < 32.996137365 - 1e-6:
            promising.append(m)
    summary = dict(status='ALL_RECORDS_VERIFIED', budget=budget, seeds=list(seeds), observations=len(records),
        methods=method_rows, primary_contrasts=primary, secondary_pairwise=all_pairs,
        large_budget_gate_passed=bool(promising), gate_trigger_methods=promising,
        scope='Optimizer seeds conditional on fixed reused 64 planning states; not generalization')
    save(OUT / f'BUDGET_{budget}_SUMMARY.json', summary)
    flat = [{k: r[k] for k in ('method', 'seed', 'budget', 'distinct_evaluations', 'attempted_evaluations',
        'search_best_loss_hr', 'elapsed_wall_seconds', 'sequence_sha256')} for r in records]
    pd.DataFrame(flat).to_csv(long_path(OUT / f'SEED_LEVEL_{budget}.csv'), index=False)
    save(OUT / f'ALL_FINAL_PERMUTATIONS_{budget}.json', [dict(method=r['method'], seed=r['seed'],
        loss_hr=r['search_best_loss_hr'], sequence_sha256=r['sequence_sha256'], sequence=r['best_sequence']) for r in records])
    print('SUMMARY', json.dumps(summary), flush=True)
    return records, summary


def correctness(kernel, quality):
    context, decoder, _ = execution_context(kernel.ids)
    checks = 0
    for r in range(64):
        finish, *_ = _decode(decoder.order(quality), kernel.damage[r], kernel.duration[r],
            kernel.origin_index, kernel.base, kernel.travel)
        activation = np.where(kernel.damage[r] <= 1, 0., finish)
        times, path = source_times(activation, kernel.source_flag, kernel.neighbor_offset, kernel.neighbors)
        assert np.isfinite(times).all()
        for t in np.unique(np.r_[0., activation, times]):
            active = {kernel.ids[i] for i in range(92) if activation[i] <= t}
            reached = set()
            for component in nx.connected_components(context['graph'].subgraph(active)):
                if component & context['sources']:
                    reached.update(component)
            assert reached == {kernel.ids[i] for i in range(92) if times[i] <= t}
            checks += 1
    rows, _, _, _ = bank(kernel, quality)
    save(OUT / 'SOURCE_TIMING_CORRECTNESS.json', dict(status='PASS', native_event_comparisons=checks,
        planning_states=64, bank_size=len(rows), all_sample_evidence=True, no_new_physical_samples=True))
    print('SOURCE_TIMING_PASS', checks, flush=True)


def old_proposal_mechanism(kernel, quality):
    context, decoder, _ = execution_context(kernel.ids)
    origins = decoder.origins(context['origins'])
    frozen = tuple(json.loads((FROZEN / 'SELECTED_SEQUENCE.json').read_text())['sequence'])
    rows = []
    all_transfer = []
    raw = long_path(OUT / 'original_artifacts/38065546076')
    for p in raw.rglob('RESULTS.json'):
        d = json.loads(p.read_text())
        for start in d['start_results']:
            seq = tuple(quality) if start['start'] == 'prior_optimized_warm' else frozen
            seed = start['seed']
            rng = random.Random(seed)
            event_bank, _ = schedule_bank(kernel, context, decoder, origins, seq, rng)
            event = rng.choices(event_bank, weights=[max(1e-14, x['weighted_priority']) for x in event_bank], k=1)[0]
            r = event['sample']
            before = decoder.decode(order=decoder.order(seq), damage=kernel.damage[r], duration=kernel.duration[r], origins=origins)
            for mode in ('lns_repair_route', 'lns_repair_random'):
                record = next(x for x in start['records'] if x['macro'] == 0 and x['method'] == mode)
                assert record['selected_sample'] == r and record['event_station'] == event['gateway']
                choices, _ = repair_candidates(seq, event, random.Random(seed * 100000 + 1), mode, kernel)
                matching = [x for x in choices if old.identity(x) == record['best_candidate_sha256']]
                assert len(matching) == 1
                after = decoder.decode(order=decoder.order(matching[0]), damage=kernel.damage[r], duration=kernel.duration[r], origins=origins)
                ds = kernel.damage[r]
                fa, fb = before[0], after[0]
                aa = np.where(ds <= 1, 0., fa)
                ab = np.where(ds <= 1, 0., fb)
                ta, _ = source_times(aa, kernel.source_flag, kernel.neighbor_offset, kernel.neighbors)
                tb, _ = source_times(ab, kernel.source_flag, kernel.neighbor_offset, kernel.neighbors)
                scheduled = ds > 0
                first = (before[5] >= 0) & (before[5] < 57)
                origin_before = np.where(before[3] >= 0, kernel.origin_index[np.maximum(0, before[3])], -1)
                origin_after = np.where(after[3] >= 0, kernel.origin_index[np.maximum(0, after[3])], -1)
                group = [kernel.index[s] for s in event['bundle']]
                gateway = kernel.index[event['gateway']]
                rows.append(dict(start=start['start'], outer_seed=d['seed'], method=mode, sample=r,
                    archived_delta_mean64_hr=record['mean64_delta_hr'], archived_delta_origin_hr=record['event_sample_delta_hr'],
                    best_candidate_sha256=record['best_candidate_sha256'], best_sequence=list(matching[0]),
                    route_bundle=event['bundle'], route_members_already_functional=int((ds[group] <= 1).sum()),
                    changed_crew_assignments=int(((before[3] != after[3]) & scheduled).sum()),
                    changed_first_wave_crews=int(((before[3] != after[3]) & first).sum()),
                    changed_crew_origins=int(((origin_before != origin_after) & scheduled).sum()),
                    changed_first_wave_origins=int(((origin_before != origin_after) & first).sum()),
                    changed_travel_legs=int(((abs(before[2] - after[2]) > 1e-9) & scheduled).sum()),
                    changed_predecessors=int(((before[4] != after[4]) & scheduled).sum()),
                    earlier_completions=int(((fb < fa - 1e-9) & scheduled).sum()),
                    later_completions=int(((fb > fa + 1e-9) & scheduled).sum()),
                    directed_travel_delta_hr=float(np.nansum(after[2]) - np.nansum(before[2])),
                    gateway_completion_delta_hr=float(fb[gateway] - fa[gateway]),
                    source_connection_earlier_stations=int((tb < ta - 1e-9).sum()),
                    source_connection_later_stations=int((tb > ta + 1e-9).sum())))
            all_transfer.extend(start['records'])
    summaries = []
    for start in ('prior_optimized_warm', 'frozen_formal_ga'):
        for method in ('lns_repair_route', 'lns_repair_random'):
            selected = [x for x in all_transfer if x['start'] == start and x['method'] == method]
            details = [x for x in rows if x['start'] == start and x['method'] == method]
            summaries.append(dict(start=start, method=method, macros=len(selected),
                mean_origin_delta_hr=float(np.mean([x['event_sample_delta_hr'] for x in selected])),
                mean64_delta_hr=float(np.mean([x['mean64_delta_hr'] for x in selected])),
                origin_improving=int(sum(x['event_sample_delta_hr'] < -1e-9 for x in selected)),
                mean64_improving=int(sum(x['mean64_delta_hr'] < -1e-9 for x in selected)),
                replayed_macro0_count=len(details),
                mean_changed_firstwave_crews=float(np.mean([x['changed_first_wave_crews'] for x in details])),
                mean_changed_firstwave_origins=float(np.mean([x['changed_first_wave_origins'] for x in details])),
                mean_changed_travel_legs=float(np.mean([x['changed_travel_legs'] for x in details])),
                mean_changed_predecessors=float(np.mean([x['changed_predecessors'] for x in details])),
                mean_earlier_completions=float(np.mean([x['earlier_completions'] for x in details])),
                mean_later_completions=float(np.mean([x['later_completions'] for x in details]))))
    save(OUT / 'OLD_BLOCK_MECHANISM_REPLAY.json', dict(status='ARCHIVED_HASH_REPLAY_PASS',
        optimization_reruns=0, objective_score_calls=0, whole_proposal_not_station_causality=True,
        replayed_macros=32, all_archived_observations=len(all_transfer), summaries=summaries, cases=rows))
    print('OLD_BLOCK_REPLAY_PASS', json.dumps(summaries), flush=True)


def validation_readiness():
    original = json.loads((FROZEN / 'VALIDATION_COMPARATOR_SEQUENCES.json').read_text())
    protocol = json.loads((FROZEN / 'FINAL_VALIDATION_PROTOCOL.json').read_text())
    rules_file = REPO_ROOT / 'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json'
    rules = json.loads(rules_file.read_text())['2pc50']
    refined = json.loads(REFINED.read_text())
    items = list(original['ordered_policies'])
    for name in ('centrality-first', 'closeness-first'):
        assert name not in [x['strategy'] for x in items]
        items.append(dict(strategy=name, sequence=rules[name], sequence_sha256=old.identity(rules[name]),
            source_file=str(rules_file.relative_to(REPO_ROOT)), role='secondary fixed original policy'))
    items.append(dict(strategy='refined-ils-secondary-diagnostic', sequence=refined['sequence'],
        sequence_sha256=refined['sequence_sha256'], source_file=str(REFINED.relative_to(REPO_ROOT)),
        role='secondary diagnostic; no formal promotion; fixed before any fresh physical draw'))
    expected = set(refined['sequence'])
    for x in items:
        assert len(x['sequence']) == 92 and set(x['sequence']) == expected
        assert old.identity(x['sequence']) == x['sequence_sha256']
    assert len(items) == 12
    files = ['FINAL_GA_CONFIG_CANDIDATE.json', 'SELECTED_SEQUENCE.json', 'SELECTED_SEQUENCE.txt',
        'FINAL_VALIDATION_PROTOCOL.json', 'VALIDATION_COMPARATOR_SEQUENCES.json']
    receipt = json.loads((FROZEN / 'FREEZE_RECEIPT.json').read_text())
    assert all(sha(FROZEN / f) == h for f, h in receipt['files_sha256'].items())
    save(OUT / 'VALIDATION_COMPARATORS_ADDENDUM.json', dict(status='READINESS_ONLY_NO_DRAW_AUTHORIZATION',
        ordered_policies=items, unconstrained=original['unconstrained'], total_conditions=13,
        original_freeze_receipt=receipt, original_protocol_unchanged=True,
        all_original_freeze_hashes_verified=True,
        original_files_sha256={f: sha(FROZEN / f) for f in files},
        refined_candidate_file_sha256=sha(REFINED), fresh_samples_generated=0,
        sampling_source_sha256={f.__name__: hashlib.sha256(inspect.getsource(f).encode()).hexdigest()
            for f in (sample_damage_states, damage_to_functionality_and_repair, draw_positive_normal)},
        random_namespace=protocol['randomness'], statistical=protocol['statistical'],
        primary=protocol['primary'], selected_sequence_sha256=protocol['selected_sequence_sha256'],
        engineering=dict(estimated_archive_bytes=protocol['estimate']['archive_bytes'] * 13 / 10,
            reserved_storage_bytes=int(protocol['estimate']['reserved_storage_bytes'] * 13 / 10),
            disk_free_bytes=shutil.disk_usage(str(REPO_ROOT)).free,
            estimate_not_measurement=True, core_physical_arrays_bytes=2000 * 92 * (8 + 8)),
        freeze_conditions=['Explicit author approval still required', 'All 13 conditions share each physical state',
            'Hash overlap with original64 and inspected1000 aborts; no redraw',
            'No chromosome or method selection on new states', 'Whole physical realization paired bootstrap',
            '0-480h validation endpoint distinct from original planning horizon',
            'New readiness registry must also be frozen before sampling', 'Verify source functions and fragility/config/input file hashes immediately before authorized execution']))
    print('VALIDATION_READINESS_ONLY', len(items), 'ordered + unconstrained; zero physical draws', flush=True)


def cutset_context():
    kernel, _, quality, _ = load()
    context, _, _ = execution_context(kernel.ids)
    graph = context['graph'].copy()
    root = '__diagnostic_all_core__'
    graph.add_edges_from((root, source) for source in sorted(context['sources']))
    rows = []
    for target in sorted(set(kernel.ids) - context['sources']):
        cut = sorted(nx.minimum_node_cut(graph, root, target))
        reduced = graph.copy()
        reduced.remove_nodes_from(cut)
        assert not nx.has_path(reduced, root, target)
        ids = [kernel.index[s] for s in cut]
        rows.append(dict(target=target, dependency_mass=float(kernel.station_mass[kernel.index[target]]),
            minimum_internal_vertex_cut_size=len(cut), one_minimum_cut=cut,
            source_members=sorted(set(cut) & context['sources']),
            planning_states_all_cut_members_initially_below_threshold=int((kernel.damage[:, ids] >= 2).all(axis=1).sum())))
    save(OUT / 'STATIC_SOURCE_CUTSET_CONTEXT.json', dict(status='78_STATIC_SOURCE_TARGET_CUTS_VERIFIED',
        targets=rows, graph_edges=context['graph'].number_of_edges(), core_sources=14,
        authority_graph_modified=False, optimizer_unchanged=True,
        meaning='One minimum internal vertex separator per non-Core target. Not enumeration of every cut, not a time-dependent causal repair bundle.',
        no_new_physical_samples=True))
    print('STATIC_CUTSETS_VERIFIED', len(rows), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--task', choices=('mechanism', 'readiness', 'summary', 'cutsets'), required=True)
    p.add_argument('--budget', type=int, default=100000)
    a = p.parse_args()
    if a.task == 'summary':
        results(a.budget)
    elif a.task == 'readiness':
        validation_readiness()
    elif a.task == 'cutsets':
        cutset_context()
    else:
        kernel, _, quality, _ = load()
        correctness(kernel, quality)
        old_proposal_mechanism(kernel, quality)


if __name__ == '__main__':
    main()
