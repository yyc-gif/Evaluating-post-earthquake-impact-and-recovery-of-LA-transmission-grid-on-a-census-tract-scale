"""Bounded frozen-parent probes separating bundle targeting and rank disruption."""
from __future__ import annotations
import json
import random
import time

import numpy as np

from la_grid.diagnostics.ga_connectivity_lns_local_20261010 import OUT, bank, repair, weighted_pick
from la_grid.diagnostics.ga_connectivity_lns_audit_20261010 import FROZEN, REFINED
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import Meter
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.diagnostics.ga_research_collect_20261009 import save
from la_grid.revision.formal.schedule import _decode


def swaps(parent, group, preferred, kernel, rng, meter, effort):
    baseline = meter.evaluate(parent)
    best, value = parent, baseline
    for _ in range(effort):
        candidate = list(parent)
        stations = list(group)
        rng.shuffle(stations)
        for i in stations:
            current = candidate.index(kernel.ids[i])
            target = rng.choice((current, preferred[i], 0, rng.randrange(92)))
            candidate[current], candidate[target] = candidate[target], candidate[current]
        candidate = tuple(candidate)
        score = meter.evaluate(candidate)
        if score > value:
            best, value = candidate, score
    return best, value


def schedule_change(kernel, parent, candidate):
    before = np.array([kernel.index[s] for s in parent], np.int64)
    after = np.array([kernel.index[s] for s in candidate], np.int64)
    crews, first_crews, earlier, later = [], [], [], []
    for r in range(64):
        args = (kernel.damage[r], kernel.duration[r], kernel.origin_index, kernel.base, kernel.travel)
        a, b = _decode(before, *args), _decode(after, *args)
        mask = kernel.damage[r] > 0
        first = (a[5] >= 0) & (a[5] < 57)
        crews.append(int(((a[3] != b[3]) & mask).sum()))
        first_crews.append(int(((a[3] != b[3]) & first).sum()))
        earlier.append(int(((b[0] < a[0] - 1e-9) & mask).sum()))
        later.append(int(((b[0] > a[0] + 1e-9) & mask).sum()))
    return dict(mean_changed_crews=float(np.mean(crews)),
        mean_changed_firstwave_crews=float(np.mean(first_crews)),
        mean_earlier_completions=float(np.mean(earlier)), mean_later_completions=float(np.mean(later)))


def main():
    started = time.perf_counter()
    kernel, _, quality, identity = load()
    parents = {'shared_prior': tuple(quality),
        'frozen_ga': tuple(json.loads((FROZEN / 'SELECTED_SEQUENCE.json').read_text())['sequence']),
        'refined_ils': tuple(json.loads(REFINED.read_text())['sequence'])}
    records = []
    meter = Meter(kernel, 1000000)
    eligible = np.flatnonzero((kernel.damage > 0).any(axis=0)).tolist()
    sample_calls = 0
    for label, parent in parents.items():
        parent_value = meter.evaluate(parent)
        baseline_samples = old.per_sample(kernel, parent)
        sample_calls += 64
        rows, _, preferred, _ = bank(kernel, parent)
        for seed in range(1400, 1424):
            rng = random.Random(seed)
            chosen = weighted_pick(rng, rows, [x['weight'] for x in rows])
            random_group = rng.sample(eligible, len(chosen['group']))
            for targeting, group in [('connectivity', chosen['group']), ('random', random_group)]:
                begin, attempts = meter.expensive, meter.attempts
                candidate, value, effort, _ = repair(parent, group, preferred, kernel,
                    random.Random(seed + 100000), meter)
                insertion = (candidate, value, meter.expensive - begin, meter.attempts - attempts)
                begin, attempts = meter.expensive, meter.attempts
                candidate, value = swaps(parent, group, preferred, kernel,
                    random.Random(seed + 200000), meter, effort)
                slot = (candidate, value, meter.expensive - begin, meter.attempts - attempts)
                for operator, data in [('insertion_beam', insertion), ('joint_slot_swaps', slot)]:
                    candidate, value, distinct, attempted = data
                    delta = old.per_sample(kernel, candidate) - baseline_samples
                    sample_calls += 64
                    assert abs(delta.mean() - (parent_value - value)) < 1e-8
                    records.append(dict(parent=label, seed=seed, targeting=targeting, repair=operator,
                        bundle=[kernel.ids[i] for i in group], parent_loss_hr=-parent_value,
                        best_loss_hr=-value, delta_mean64_hr=float(delta.mean()),
                        delta_sample15_hr=float(delta[15]), improved_states=int((delta < -1e-9).sum()),
                        worsened_states=int((delta > 1e-9).sum()), attempted_calls=attempted,
                        distinct_calls=distinct, matched_proposal_effort=effort,
                        sequence_sha256=old.identity(candidate), sequence=list(candidate),
                        **schedule_change(kernel, parent, candidate)))
    summaries = []
    for label in parents:
        for target in ('connectivity', 'random'):
            for repair_name in ('insertion_beam', 'joint_slot_swaps'):
                rs = [r for r in records if r['parent'] == label and r['targeting'] == target and r['repair'] == repair_name]
                summaries.append(dict(parent=label, targeting=target, repair=repair_name, n=len(rs),
                    mean_delta_hr=float(np.mean([r['delta_mean64_hr'] for r in rs])),
                    strict_improving_macros=sum(r['delta_mean64_hr'] < -1e-9 for r in rs),
                    mean_firstwave_changed_crews=float(np.mean([r['mean_changed_firstwave_crews'] for r in rs])),
                    total_attempts=sum(r['attempted_calls'] for r in rs), total_distinct=sum(r['distinct_calls'] for r in rs)))
    save(OUT / 'FAILURE_PROBE_RESULTS.json', dict(status='COMPLETE', adaptive_diagnostic_not_confirmatory=True,
        physical_draws=0, optimizer_reruns=0, mean_objective_calls=meter.expensive,
        attempted_mean_calls=meter.attempts, compiled_sample_calls=sample_calls,
        elapsed_wall_seconds=time.perf_counter() - started, input_identity=identity,
        summaries=summaries, records=records))
    print('FAILURE_PROBE_COMPLETE', json.dumps(summaries), flush=True)


if __name__ == '__main__':
    main()
