"""Noncontiguous beam repair using all-64 source-bottleneck scheduling evidence.

Only proposal construction is new. Every fitness query uses the frozen exact
kernel, and native schedule decoding is reused without changing the scheduler.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
import random
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from numba import njit

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_research_collect_20261009 import save, long_path
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import Meter, proposal, local_search, run_ga
from la_grid.revision.formal.schedule import _decode

OUT = REPO_ROOT / 'results/diagnostics/ga_noncontiguous_connectivity_lns_20261010'
METHODS = ('connectivity_lns', 'random_lns', 'scheduling_lns', 'ga_baseline', 'iterated_local')
SEEDS = tuple(range(1200, 1220))
SMOKE_SEEDS = (1180, 1181)
LARGE_SEEDS = tuple(range(1300, 1310))
TOL = 1e-9


@njit(cache=True)
def source_times(activation, source, offset, neighbors):
    """Earliest source connectivity is a minimax node-activation path problem."""
    n = len(activation)
    reached = np.full(n, np.inf)
    previous = np.full(n, -1, dtype=np.int64)
    done = np.zeros(n, dtype=np.bool_)
    for i in range(n):
        if source[i]:
            reached[i] = activation[i]
    for _ in range(n):
        node = -1
        best = np.inf
        for i in range(n):
            if not done[i] and reached[i] < best:
                node = i
                best = reached[i]
        if node < 0:
            break
        done[node] = True
        for pos in range(offset[node], offset[node + 1]):
            other = neighbors[pos]
            value = max(best, activation[other])
            if not done[other] and value < reached[other]:
                reached[other] = value
                previous[other] = node
    return reached, previous


def bank(kernel, sequence):
    order = np.array([kernel.index[x] for x in sequence], dtype=np.int64)
    evidence = defaultdict(lambda: np.zeros(64))
    schedule_weight = np.zeros(92)
    preferred = [[] for _ in range(92)]
    dependency_count = 0
    for r in range(64):
        ds = kernel.damage[r]
        finish, _, travel, crew, prior, dispatch, _ = _decode(order, ds, kernel.duration[r],
            kernel.origin_index, kernel.base, kernel.travel)
        activation = np.where(ds <= 1, 0., finish)
        connected, witness = source_times(activation, kernel.source_flag,
            kernel.neighbor_offset, kernel.neighbors)
        schedule_weight += np.nan_to_num(finish) * kernel.station_mass / 64
        # Convert a favorable first-wave crew slot to a full-priority-list slot.
        damaged_order = order[ds[order] > 0]
        for station in damaged_order:
            costs = kernel.base[kernel.origin_index, station]
            good_crews = np.flatnonzero(costs <= costs.min() + .05)
            preferred[station].extend(sequence.index(kernel.ids[damaged_order[c]])
                for c in good_crews if c < len(damaged_order))
        for target in range(92):
            wait = connected[target] - activation[target]
            if not np.isfinite(wait) or wait <= TOL or kernel.station_mass[target] <= 0:
                continue
            route = []
            node = target
            while node >= 0:
                if ds[node] >= 2 and activation[node] > activation[target] + TOL:
                    route.append(node)
                node = witness[node]
            route.sort(key=lambda x: (-activation[x], x))
            group = route[:4]
            if group:
                gateway = group[0]
                pred = int(prior[gateway])
                if pred >= 0 and pred not in group:
                    group = group[:3] + [pred]
                    dependency_count += 1
            if len(group) < 2:
                continue
            weight = wait * kernel.station_mass[target] / kernel.total_mass
            if ds[target] == 1:
                weight *= .5
            evidence[tuple(sorted(group))][r] += weight
    rows = []
    for group, samples in evidence.items():
        rows.append(dict(group=group, weight=float(samples.mean()), support=int((samples > 0).sum()),
            sample15_fraction=float(samples[15] / samples.sum()),
            weight_without15=float(np.delete(samples, 15).mean())))
    rows.sort(key=lambda x: (-x['weight'], x['group']))
    rows = rows[:128]
    preferred = [int(np.median(x)) if x else sequence.index(kernel.ids[i]) for i, x in enumerate(preferred)]
    return rows, schedule_weight, preferred, dependency_count


def weighted_pick(rng, values, weights):
    return rng.choices(values, weights=[max(float(x), 1e-12) for x in weights], k=1)[0]


def relocate(sequence, station, position):
    rest = [s for s in sequence if s != station]
    rest.insert(min(max(0, position), len(rest)), station)
    return tuple(rest)


def repair(sequence, group, preferred, kernel, rng, meter):
    """Independently relocate stations, retaining three complete permutations.

    Beam branches may retain temporarily harmful intermediate moves; no partial
    chromosome is scored. There is no contiguous-block constraint.
    """
    stations = list(group)
    rng.shuffle(stations)
    beam = [(sequence, meter.evaluate(sequence))]
    tested = 0
    partial = False
    for idx in stations:
        station = kernel.ids[idx]
        candidates = {}
        for parent, value in beam:
            old_rank = parent.index(station)
            positions = [old_rank, 0, preferred[idx], rng.randrange(92),
                         min(91, max(0, old_rank + rng.choice((-20, -8, 8, 20))))]
            for pos in sorted(set(positions)):
                candidate = relocate(parent, station, pos)
                if candidate in candidates:
                    continue
                try:
                    score = meter.evaluate(candidate)
                except StopIteration:
                    partial = True
                    break
                tested += 1
                candidates[candidate] = score
            if partial:
                break
        if candidates:
            beam = sorted(candidates.items(), key=lambda x: (-x[1], x[0]))[:3]
        if partial:
            break
    result, value = max(beam, key=lambda x: x[1])
    positions = sorted(result.index(kernel.ids[i]) for i in group)
    noncontiguous = positions[-1] - positions[0] + 1 > len(positions)
    return result, value, tested, noncontiguous


def search(kernel, incumbents, quality, method, seed, budget):
    rng = random.Random(seed)
    meter = Meter(kernel, budget)
    start = time.perf_counter()
    for s in incumbents.values():
        meter.evaluate(s)
    current = tuple(quality)
    value = meter.evaluate(current)
    count = defaultdict(int)
    checkpoints = []
    summaries = []
    last_refresh = -10000
    stale = 0
    restart = 0
    eligible = np.flatnonzero((kernel.damage > 0).any(axis=0)).tolist()
    proposal_delta = []
    while meter.expensive < budget and meter.attempts < 60 * budget:
        if meter.expensive - last_refresh >= 10000:
            start_bank = time.perf_counter()
            rows, schedule_weight, preferred, deps = bank(kernel, current)
            count['bank_milliseconds'] += int(1000 * (time.perf_counter() - start_bank))
            count['bank_refreshes'] += 1
            last_refresh = meter.expensive
            summaries.append(dict(evaluation=meter.expensive, crew_dependency_targets=deps,
                top_bundles=[{**x, 'group': [kernel.ids[i] for i in x['group']]} for x in rows[:10]]))
        before = meter.expensive
        old_value = value
        if rng.random() < .30 or not rows:
            candidate = proposal(current, rng)
            try:
                score = meter.evaluate(candidate)
            except StopIteration:
                break
            count['local_macros'] += 1
        else:
            chosen = weighted_pick(rng, rows, [x['weight'] for x in rows])
            size = len(chosen['group'])
            if method == 'connectivity_lns':
                group = chosen['group']
            elif method == 'random_lns':
                group = tuple(rng.sample(eligible, size))
            else:
                pool = list(eligible)
                group = []
                for _ in range(size):
                    selected = weighted_pick(rng, pool, [schedule_weight[i] for i in pool])
                    group.append(selected)
                    pool.remove(selected)
            candidate, score, effort, noncontiguous = repair(current, group, preferred, kernel, rng, meter)
            count['bundle_macros'] += 1
            count[f'bundle_size_{size}'] += 1
            count['repair_attempts'] += effort
            count['noncontiguous_final_repairs'] += int(noncontiguous)
            delta = old_value - score
            if len(proposal_delta) < 2048:
                proposal_delta.append(float(delta))
            count['strictly_improving_bundle_macros'] += int(score > old_value + TOL)
        improved = score > value + TOL
        neutral = abs(score - value) <= TOL and candidate != current and rng.random() < .15
        if improved or neutral:
            current, value = candidate, score
            count['accepted_strict' if improved else 'accepted_neutral'] += 1
        stale = 0 if improved else stale + max(1, meter.expensive - before)
        if stale >= 800 and meter.expensive < budget:
            current = tuple(meter.best_seq)
            for _ in range((2, 4, 8)[restart % 3]):
                current = proposal(current, rng)
            try:
                value = meter.evaluate(current)
            except StopIteration:
                break
            restart += 1
            stale = 0
        for cp in (20000, 50000, 100000, 250000, 500000):
            if before < cp <= meter.expensive:
                checkpoints.append(dict(evaluations=cp, loss_hr=-meter.best_value))
    record = meter.record()
    assert record['completed_budget'], (method, seed, meter.expensive)
    assert abs(kernel.score(record['best_sequence']) + record['search_best_loss_hr']) < TOL
    record.update(method=method, seed=seed, budget=budget,
        elapsed_wall_seconds=time.perf_counter() - start,
        accepted_moves=count['accepted_strict'], restart_count=restart,
        generation0_loss_hr=33.03813174326729, mechanism_counts=dict(count),
        checkpoints=checkpoints, bundle_bank_snapshots=summaries,
        first_2048_macro_deltas_hr=proposal_delta)
    return record


def run_case(method, seed, budget):
    dest = OUT / f'budget_{budget}' / f'seed_{seed}' / (method + '.json')
    if long_path(dest).exists():
        data = json.loads(long_path(dest).read_text())
        assert data['completed_budget'] and data['distinct_evaluations'] == budget
        return data
    started = time.perf_counter()
    kernel, incumbents, quality, identity = load()
    if method == 'ga_baseline':
        record = run_ga(kernel, incumbents, quality, seed, budget)
    elif method == 'iterated_local':
        record = local_search(kernel, incumbents, quality, method, seed, budget)
    else:
        record = search(kernel, incumbents, quality, method, seed, budget)
    record.update(status='COMPLETE', input_identity=identity, no_new_physical_samples=True,
        worker_total_wall_seconds=time.perf_counter() - started)
    save(dest, record)
    return record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=('smoke', 'confirmation', 'large'), required=True)
    p.add_argument('--workers', type=int, default=12)
    a = p.parse_args()
    seeds = SMOKE_SEEDS if a.phase == 'smoke' else SEEDS if a.phase == 'confirmation' else LARGE_SEEDS
    budget = 1000 if a.phase == 'smoke' else 100000 if a.phase == 'confirmation' else 500000
    start = time.perf_counter()
    records = []
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        futures = {pool.submit(run_case, method, seed, budget): (method, seed) for seed in seeds for method in METHODS}
        for f in as_completed(futures):
            record = f.result()
            records.append(record)
            print('RESULT', json.dumps({k: record[k] for k in ('method', 'seed', 'distinct_evaluations',
                'search_best_loss_hr', 'elapsed_wall_seconds')}), flush=True)
    save(OUT / (a.phase.upper() + '_EXECUTION.json'), dict(status='COMPLETE',
        phase=a.phase, budget=budget, seeds=seeds, methods=METHODS, count=len(records),
        workers=a.workers, total_elapsed_wall_seconds=time.perf_counter() - start,
        total_distinct_evaluations=sum(r['distinct_evaluations'] for r in records),
        total_attempts=sum(r['attempted_evaluations'] for r in records),
        total_worker_wall_seconds=sum(r['worker_total_wall_seconds'] for r in records)))


if __name__ == '__main__':
    main()
