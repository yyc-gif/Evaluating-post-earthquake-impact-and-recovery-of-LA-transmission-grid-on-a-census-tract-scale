"""Task A-C: immutable-model completion relaxation and exact fixed-slot audit."""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import heapq
import itertools
import json
from pathlib import Path
import pickle
import random
import subprocess
import time

import numpy as np
import pandas as pd
from numba import njit

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.diagnostics.ga_research_collect_20261009 import save, long_path
from la_grid.diagnostics.ga_research_preserve_20261009 import INPUTS, snapshot, git
from la_grid.diagnostics.ga_connectivity_lns_local_20261010 import source_times, bank
from la_grid.diagnostics.ga_connectivity_lns_candidate_20261010 import influence, components
from la_grid.revision.formal.schedule import _decode
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import RealizationInputs, evaluate_completion_step_functionality
from la_grid.revision.r1_source_gate import evaluate_source_gate
from la_grid.revision.r1_ga_revision import evaluate_direct_population_burden_aggregate

OUT = REPO_ROOT / 'results/diagnostics/ga_actionable_delay_six_slot_20261010'
START = '39d64133b75f7ef528725bfb3bdc7161303c4ed9'
BRANCH = 'diagnostics/actionable-delay-six-slot-audit-20261010'
PREVIOUS = REPO_ROOT / 'results/diagnostics/ga_noncontiguous_connectivity_lns_20261010'
DEEPER = REPO_ROOT / 'results/diagnostics/ga_deeper_research_20261009'
CHECKPOINT = DEEPER / 'actions_raw/38025468939/11660004802/ils_seed304_deterministic_refinement/LOCAL_CHECKPOINT.pkl.gz'
TOL = 1e-8
GAIN_TOL = 1e-9


def sha(path):
    return hashlib.sha256(long_path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(long_path(path).read_text(encoding='utf-8'))


def hydrate_file(name, source):
    target = long_path(REPO_ROOT / name)
    pointer = git(REPO_ROOT, 'show', START + ':' + name)
    if pointer.startswith(b'version https://git-lfs.github.com/spec/v1'):
        fields = dict(line.split(' ', 1) for line in pointer.decode().splitlines())
        oid = fields['oid'][7:]
        common = Path(git(source, 'rev-parse', '--git-common-dir').decode().strip())
        if not common.is_absolute():
            common = source / common
        obj = long_path(common / 'lfs/objects' / oid[:2] / oid[2:4] / oid)
        data = obj.read_bytes() if obj.exists() else long_path(source / name).read_bytes()
        assert len(data) == int(fields['size']) and hashlib.sha256(data).hexdigest() == oid, name
        target.write_bytes(data)
    return dict(path=name, sha256=sha(REPO_ROOT / name))


def setup(source, revision):
    assert git(REPO_ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    current = snapshot(revision)
    save(OUT / 'PRESERVATION_BASELINE.json', current)
    names = list(INPUTS) + [CHECKPOINT.relative_to(REPO_ROOT).as_posix()]
    receipt = [hydrate_file(name, source) for name in names]
    # The checkpoint is an original, hash-verified artifact, never regenerated.
    save(OUT / 'HYDRATION_RECEIPT.json', receipt)
    save(OUT / 'SETUP.json', dict(start_commit=START, branch=BRANCH,
        source_checkout=str(source), protected_revision_checkout=str(revision),
        current_status=git(REPO_ROOT, 'status', '--short').decode(),
        user_brief_sha256=sha(Path('C:/Users/yinch/Downloads/LOCAL_NEXT_STAGE.md')),
        supplied_helper_present=False, helper_implemented_from_brief=True))
    print('SETUP_PASS', len(current['files_sha256']), flush=True)


def independent_route_completion_bounds(*, durations, base_to_task, task_to_task, scheduled):
    """Dijkstra relaxation; only executed damaged tasks can be waypoints."""
    p = np.asarray(durations, float)
    base = np.asarray(base_to_task, float)
    travel = np.asarray(task_to_task, float)
    mask = np.asarray(scheduled, bool)
    n = len(p)
    if p.ndim != 1 or mask.shape != (n,) or base.ndim != 2 or base.shape[1] != n or base.shape[0] == 0 or travel.shape != (n, n):
        raise ValueError('Incomplete route arrays or no active crew origins')
    if not all(np.isfinite(a).all() and np.all(a >= 0) for a in (p, base, travel)):
        raise ValueError('Duration and directed travel must be finite and nonnegative')
    tasks = np.flatnonzero(mask)
    arrival = np.full(n, np.inf)
    predecessor = np.full(n, -1, int)
    if len(tasks):
        arrival[tasks] = base[:, tasks].min(axis=0)
    heap = [(arrival[i], int(i)) for i in tasks]
    heapq.heapify(heap)
    while heap:
        value, j = heapq.heappop(heap)
        if value != arrival[j]:
            continue
        for i in tasks:
            if i == j:
                continue
            candidate = value + p[j] + travel[j, i]
            if candidate < arrival[i]:
                arrival[i] = candidate
                predecessor[i] = j
                heapq.heappush(heap, (candidate, int(i)))
    completion = arrival + p
    completion[~mask] = 0.
    return dict(arrival=arrival, completion=completion, predecessor=predecessor)


@njit(cache=True)
def completion_loss(finish, ds, sources, offsets, neighbors, mass, total, horizon):
    activation = np.where(ds <= 1, 0., finish)
    reached, _ = source_times(activation, sources, offsets, neighbors)
    loss = 0.
    for i in range(len(ds)):
        connected = min(horizon, reached[i])
        if ds[i] == 1:
            loss += mass[i] * (.5 * connected + .5 * min(horizon, max(reached[i], finish[i])))
        else:
            loss += mass[i] * connected
    return loss / total


def relaxed_score(k, r, finish):
    return float(completion_loss(finish, k.damage[r], k.source_flag, k.neighbor_offset,
        k.neighbors, k.station_mass, k.total_mass, k.horizon))


def parents(k, prior):
    frozen = read(REPO_ROOT / 'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json')
    refined = read(DEEPER / 'ILS_REFINED_BEST_SEED304_PLANNING_CANDIDATE.json')
    data = dict(shared_prior=dict(sequence=list(prior), expected_loss_hr=33.03813174326729),
        frozen_ga=dict(sequence=frozen['sequence'], expected_loss_hr=frozen['planning_loss_hr']),
        refined_ils=dict(sequence=refined['sequence'], expected_loss_hr=refined['loss_hr']))
    for item in data.values():
        item['sequence_sha256'] = old.identity(item['sequence'])
        assert set(item['sequence']) == set(k.ids) and len(item['sequence']) == 92
        assert abs(-k.score(item['sequence']) - item['expected_loss_hr']) < TOL
    return data


def native_decode(k, sequence, r):
    return _decode(np.array([k.index[x] for x in sequence], np.int64), k.damage[r],
        k.duration[r], k.origin_index, k.base, k.travel)


def native_envelope_loss(k, context, r, finish):
    clock = np.unique(np.r_[0., k.horizon, finish[k.damage[r] > 0]])
    raw = evaluate_completion_step_functionality(damage_state=pd.Series(k.damage[r], index=k.ids),
        completion_time_hr=pd.Series(finish, index=k.ids), time_hr=clock)
    trace = evaluate_source_gate(raw, context['graph'], context['sources'], threshold=.5)
    return float(np.diff(clock) @ (trace.L_total.loc[:, list(k.ids)].to_numpy()[:-1] @ k.station_mass) / k.total_mass)


def audit():
    tick = time.perf_counter()
    k, _, prior, identity = load()
    data = parents(k, prior)
    context, _, _ = execution_context(k.ids)
    lower = np.array([independent_route_completion_bounds(durations=k.duration[r],
        base_to_task=k.base[k.origin_index], task_to_task=k.travel,
        scheduled=k.damage[r] > 0)['completion'] for r in range(64)])
    lower_loss = np.array([relaxed_score(k, r, lower[r]) for r in range(64)])
    duration_loss = np.array([relaxed_score(k, r, k.duration[r]) for r in range(64)])
    assert np.all(lower_loss >= duration_loss - TOL)
    parity = []
    for r in range(64):
        for label, finish in [('route_relaxation', lower[r]), ('duration_only', k.duration[r])]:
            authoritative = native_envelope_loss(k, context, r, finish)
            calculated = relaxed_score(k, r, finish)
            parity.append(dict(label=label, state=r, production_loss_hr=authoritative,
                diagnostic_loss_hr=calculated, error_hr=abs(authoritative-calculated)))
            assert abs(authoritative - calculated) < TOL
    rows, scores, bundle_rows, summaries = [], [], [], {}
    arrays = {}
    for label, item in data.items():
        sequence = item['sequence']
        full_loss = old.per_sample(k, sequence)
        benefit = np.zeros((64, 92))
        headroom = np.zeros((64, 92))
        allfinish, allpred, allcrew, alldispatch, allreach, allwitness = [], [], [], [], [], []
        for r in range(64):
            finish, arrival, travel, crew, pred, dispatch, _ = native_decode(k, sequence, r)
            actual = np.nan_to_num(finish)
            headroom[r] = np.where(k.damage[r] > 0, actual - lower[r], 0.)
            assert headroom[r].min() >= -TOL
            assert lower_loss[r] <= full_loss[r] + TOL
            assert abs(relaxed_score(k, r, actual) - full_loss[r]) < TOL
            connected, witness = source_times(np.where(k.damage[r] <= 1, 0., actual),
                k.source_flag, k.neighbor_offset, k.neighbors)
            allfinish.append(actual); allpred.append(pred); allcrew.append(crew)
            alldispatch.append(dispatch); allreach.append(connected); allwitness.append(witness)
            for i, station in enumerate(k.ids):
                if k.damage[r, i] > 0:
                    changed = actual.copy(); changed[i] = lower[r, i]
                    benefit[r, i] = full_loss[r] - relaxed_score(k, r, changed)
                    assert benefit[r, i] >= -TOL
                rows.append(dict(parent=label, state=r, station_id=station, damage_state=int(k.damage[r, i]),
                    scheduled=bool(k.damage[r, i] > 0), priority_rank_zero_based=sequence.index(station),
                    dispatch_rank_zero_based=int(dispatch[i]), first_wave=bool(0 <= dispatch[i] < len(k.origin_index)),
                    completion_hr=float(actual[i]), repair_duration_hr=float(k.duration[r, i]),
                    arrival_hr=float(arrival[i]) if crew[i] >= 0 else None,
                    crew_release_hr=float(arrival[i]-travel[i]) if crew[i] >= 0 else None,
                    predecessor_id=k.ids[pred[i]] if pred[i] >= 0 else None,
                    crew_index=int(crew[i]), origin_index=int(k.origin_index[crew[i]]) if crew[i] >= 0 else None,
                    travel_leg_hr=float(travel[i]) if crew[i] >= 0 else None,
                    relaxed_completion_hr=float(lower[r, i]), potential_earliness_upper_hr=float(headroom[r, i]),
                    source_connection_hr=float(connected[i]), optimistic_single_station_gain_hr=float(benefit[r, i])))
            parity.append(dict(label=label, state=r, production_loss_hr=float(full_loss[r]),
                diagnostic_loss_hr=relaxed_score(k, r, actual), error_hr=abs(relaxed_score(k, r, actual)-full_loss[r])))
        benefit = np.maximum(benefit, 0.)
        for i, station in enumerate(k.ids):
            scores.append(dict(parent=label, station_id=station, mean_optimistic_gain_hr=float(benefit[:, i].mean()),
                mean_gain_without15_hr=float(np.delete(benefit[:, i], 15).mean()),
                support_states=int((benefit[:, i] > GAIN_TOL).sum()),
                state15_share=float(benefit[15, i] / benefit[:, i].sum()) if benefit[:, i].sum() else 0.,
                mean_headroom_hr=float(headroom[:, i].mean()),
                maximum_headroom_hr=float(headroom[:, i].max()),
                source=bool(k.source_flag[i])))
        bundles, _, _, _ = bank(k, sequence)
        for b in bundles[:20]:
            idx = list(b['group'])
            damaged = k.damage[:, idx] > 0
            relevant_headroom = headroom[:, idx][damaged]
            bundle_rows.append(dict(parent=label, stations=[k.ids[i] for i in idx],
                old_source_wait_weight_hr=b['weight'], old_support_states=b['support'],
                damaged_observations=int(damaged.sum()), mean_route_headroom_hr=float(relevant_headroom.mean()),
                maximum_route_headroom_hr=float(relevant_headroom.max()),
                near_zero_headroom_fraction=float((relevant_headroom <= TOL).mean())))
        arrays[label+'_finish'] = np.asarray(allfinish)
        arrays[label+'_pred'] = np.asarray(allpred)
        arrays[label+'_crew'] = np.asarray(allcrew)
        arrays[label+'_dispatch'] = np.asarray(alldispatch)
        arrays[label+'_reach'] = np.asarray(allreach)
        arrays[label+'_witness'] = np.asarray(allwitness)
        arrays[label+'_benefit'] = benefit
        arrays[label+'_headroom'] = headroom
        arrays[label+'_loss'] = full_loss
        summaries[label] = dict(loss_hr=float(full_loss.mean()), relaxation_gap_hr=float((full_loss-lower_loss).mean()),
            gap_without15_hr=float(np.delete(full_loss-lower_loss, 15).mean()),
            minimum_bound_slack_hr=float(headroom[k.damage > 0].min()),
            first_wave_with_material_headroom=int(np.sum((np.asarray(alldispatch) >= 0) &
                (np.asarray(alldispatch) < len(k.origin_index)) & (headroom > TOL))),
            queued_observations=int(np.sum(np.asarray(alldispatch) >= len(k.origin_index))))
        print('ACTIONABLE_AUDIT', label, summaries[label], flush=True)
    np.savez_compressed(long_path(OUT / 'ACTIONABLE_ARRAYS.npz'), lower=lower,
        route_loss=lower_loss, duration_loss=duration_loss, **arrays)
    pd.DataFrame(rows).to_csv(long_path(OUT / 'STATION_STATE_ACTIONABLE_DELAY.csv'), index=False)
    pd.DataFrame(scores).to_csv(long_path(OUT / 'STATION_OPPORTUNITY_RANKS.csv'), index=False)
    pd.DataFrame(parity).to_csv(long_path(OUT / 'COMPLETION_ENVELOPE_PARITY.csv'), index=False)
    save(OUT / 'DOMINANT_OLD_BUNDLES_RECONCILIATION.json', bundle_rows)
    save(OUT / 'TASK_AB.json', dict(status='PASS', parents=data, input_identity=identity,
        numerical_tolerance_hr=TOL, maximum_completion_formula_error_hr=max(x['error_hr'] for x in parity),
        route_relaxation_mean_loss_hr=float(lower_loss.mean()), duration_only_mean_loss_hr=float(duration_loss.mean()),
        tightening_hr=float((lower_loss-duration_loss).mean()), summaries=summaries,
        ordinary_double_not_interval_certified=True, scheduled_station_checks=int((k.damage > 0).sum())*3,
        source_gate_production_envelope_evaluations=128, native_decodes=192,
        optimistic_single_station_screens=int((k.damage > 0).sum())*3,
        loss_monotonicity_checks=192, elapsed_seconds=time.perf_counter()-tick,
        single_station_screens_not_feasible_or_additive=True, new_physical_samples=0))


def select():
    """Pin all 120 six-slot sets before any conditional-minimum observations."""
    a = read(OUT / 'TASK_AB.json')
    k, _, _, _ = load()
    arrays = np.load(long_path(OUT / 'ACTIONABLE_ARRAYS.npz'))
    sets = []
    for parent_number, (label, item) in enumerate(a['parents'].items()):
        sequence = item['sequence']
        order = [k.index[s] for s in sequence]
        rank = {i: j for j, i in enumerate(order)}
        benefit = arrays[label+'_benefit']
        pred = arrays[label+'_pred']; crew = arrays[label+'_crew']
        dispatch = arrays[label+'_dispatch']; witness = arrays[label+'_witness']
        ranking = sorted(range(92), key=lambda i: (-benefit[:, i].mean(), i))
        seen = set()
        rng = random.Random(2026101017+parent_number)
        for set_number, center in enumerate(ranking[:20]):
            members = [center]
            reasons = ['optimistic-service-benefit center']
            def add(i, reason):
                if i >= 0 and i not in members and len(members) < 6:
                    members.append(int(i)); reasons.append(reason)
            weights = Counter(); donors = Counter(); gateways = Counter()
            for r in range(64):
                w = float(benefit[r, center])
                if w <= GAIN_TOL:
                    continue
                if pred[r, center] >= 0:
                    weights[int(pred[r, center])] += w
                target_origin = int(np.argmin(k.base[k.origin_index, center]))
                for donor in np.flatnonzero(dispatch[r] == target_origin):
                    if k.origin_index[crew[r, center]] != k.origin_index[target_origin]:
                        donors[int(donor)] += w
                for target in range(92):
                    node = target
                    visited = []
                    while node >= 0:
                        visited.append(node); node = int(witness[r, node])
                    if center in visited:
                        for j in visited:
                            if j != center and k.damage[r, j] >= 2:
                                gateways[j] += w*k.station_mass[target]/k.total_mass
            for counter, reason in [(weights, 'queued dispatch predecessor'),
                (donors, 'first-wave donor at favorable actual origin'),
                (gateways, 'co-witness gateway')]:
                for i, _ in sorted(counter.items(), key=lambda x: (-x[1], x[0]))[:1]:
                    add(i, reason)
            for i in ranking:
                add(i, 'next service-opportunity station')
                if len(members) == 6:
                    break
            slots = tuple(sorted(rank[i] for i in members))
            if slots in seen:
                # Deterministic diversity substitution, never driven by fitness.
                for i in ranking:
                    alternative = tuple(sorted(rank[j] for j in members[:5]+[i]))
                    if len(set(alternative)) == 6 and alternative not in seen:
                        slots = alternative; break
            assert len(slots) == 6 and slots not in seen
            seen.add(slots)
            counts = Counter(0 if s < 29 else 1 if s < 57 else 2 for s in slots)
            while True:
                control = tuple(sorted(sum([rng.sample(list(range(lo, hi)), counts[b])
                    for b, (lo, hi) in enumerate(((0, 29), (29, 57), (57, 92)))], [])))
                if control not in seen:
                    break
            seen.add(control)
            for arm, selected in [('targeted', slots), ('random_control', control)]:
                sets.append(dict(parent=label, set_number=set_number, arm=arm, slots=list(selected),
                    selected_stations=[sequence[s] for s in selected], center=k.ids[center] if arm == 'targeted' else None,
                    proposed_members=[dict(station_id=k.ids[i], reason=r) for i, r in zip(members, reasons)] if arm == 'targeted' else [],
                    rank_band_counts=dict(counts), control_seed=2026101017+parent_number))
    save(OUT / 'PINNED_SIX_SLOT_SETS.json', dict(status='PINNED_BEFORE_MINIMA',
        selection='Top20 individual optimistic benefit centers; one weighted predecessor, origin donor and co-witness if present; fill next benefit rank. Deterministic diversity fallback.',
        control='Uniform six positions without replacement, matched counts in priority bands [0,29),[29,57),[57,92); unique within parent across both arms.',
        evidence_sha256=sha(OUT / 'ACTIONABLE_ARRAYS.npz'), parents=a['parents'], sets=sets,
        total_sets=120, permutations_per_set=720, enumerated_assignment_budget=86400,
        tolerance_hr=GAIN_TOL, followup='No adaptive expansion or optimizer campaign authorized by an observed minimum alone.'))
    print('PINNED', len(sets), sha(OUT / 'PINNED_SIX_SLOT_SETS.json'), flush=True)


def exact():
    tick = time.perf_counter()
    k, _, _, identity = load()
    pinned = read(OUT / 'PINNED_SIX_SLOT_SETS.json')
    with gzip.open(long_path(CHECKPOINT), 'rb') as f:
        original = pickle.load(f)
    cache = {key: -float(value) for key, value in original['cache'].items()}
    assert original['state']['local_optimal'] and old.identity(original['state']['current']) == pinned['parents']['refined_ils']['sequence_sha256']
    initial = len(cache)
    imported_hash = sha(CHECKPOINT)
    outputs = []; newly = 0; attempts = 0
    scores_path = long_path(OUT / 'EXACT_SCORES.pkl.gz')
    if scores_path.exists():
        with gzip.open(scores_path, 'rb') as f:
            resumed = pickle.load(f)
        assert resumed['pinned_sha256'] == sha(OUT / 'PINNED_SIX_SLOT_SETS.json')
        cache.update(resumed['cache']); outputs = resumed['outputs']; newly = resumed['newly']; attempts = resumed['attempts']
    for number, case in enumerate(pinned['sets']):
        if number < len(outputs):
            continue
        seq = pinned['parents'][case['parent']]['sequence']
        parent_key = bytes(k.index[s] for s in seq)
        parent_value = pinned['parents'][case['parent']]['expected_loss_hr']
        cache.setdefault(parent_key, parent_value)
        orders, values = [], []
        new_this = 0
        for assignment in itertools.permutations(case['selected_stations']):
            candidate = list(seq)
            for pos, station in zip(case['slots'], assignment):
                candidate[pos] = station
            assert set(candidate) == set(seq) and len(candidate) == 92
            assert all(candidate[i] == seq[i] for i in range(92) if i not in case['slots'])
            key = bytes(k.index[s] for s in candidate)
            attempts += 1
            if key not in cache:
                cache[key] = -k.score(candidate); newly += 1; new_this += 1
            orders.append(np.frombuffer(key, np.uint8)); values.append(cache[key])
        minimum = min(values)
        best_index = next((i for i, key in enumerate(orders) if key.tobytes() == parent_key), int(np.argmin(values))) if abs(minimum-parent_value) <= GAIN_TOL else int(np.argmin(values))
        best = [k.ids[i] for i in orders[best_index]]
        assert abs(values[best_index]-minimum) <= GAIN_TOL
        assert minimum <= parent_value+TOL
        stem = f"{case['parent']}_{case['arm']}_{case['set_number']:02}"
        np.savez_compressed(long_path(OUT / 'neighborhoods' / (stem+'.npz')),
            station_ids=np.array(k.ids), orders=np.asarray(orders), loss_hr=np.asarray(values),
            slots=np.array(case['slots']), parent=np.array(seq))
        outputs.append(dict(**case, enumerated=720, new_exact_mean_calls=new_this,
            cached_assignments=720-new_this, parent_loss_hr=parent_value, conditional_minimum_loss_hr=minimum,
            gain_hr=parent_value-minimum, parent_conditionally_optimal_within_tolerance=parent_value-minimum <= GAIN_TOL,
            best_sequence=best, sequence_sha256=old.identity(best), improving_assignments=int(np.sum(np.asarray(values) < parent_value-GAIN_TOL)),
            neighborhood_archive_sha256=sha(OUT / 'neighborhoods' / (stem+'.npz'))))
        with gzip.open(scores_path, 'wb') as f:
            pickle.dump(dict(pinned_sha256=sha(OUT / 'PINNED_SIX_SLOT_SETS.json'),
                cache=cache, outputs=outputs, newly=newly, attempts=attempts), f, protocol=5)
        if (number+1) % 10 == 0:
            print('EXACT_PROGRESS', number+1, '/120', 'new_calls', newly, 'last_gain', parent_value-minimum, flush=True)
    save(OUT / 'EXACT_SIX_SLOT_RESULTS.json', dict(status='COMPLETE', results=outputs,
        initial_imported_cache_size=initial, imported_checkpoint_sha256=imported_hash,
        imported_single_move_scan_repeated=False, source_complete_scan=original['state']['local_optimal'],
        enumerated_assignments=attempts, newly_executed_distinct_mean_calls=newly,
        reused_assignments=attempts-newly, total_cache_entries=len(cache),
        input_identity=identity, elapsed_seconds=time.perf_counter()-tick,
        restricted_only_not_global_optimality=True, floating_precision_tolerance_hr=GAIN_TOL,
        pinned_sets_sha256=sha(OUT / 'PINNED_SIX_SLOT_SETS.json')))


def schedule_changes(k, parent, candidate):
    rows = []
    for r in range(64):
        a = native_decode(k, parent, r); b = native_decode(k, candidate, r)
        ac = source_times(np.where(k.damage[r] <= 1, 0., a[0]), k.source_flag,k.neighbor_offset,k.neighbors)[0]
        bc = source_times(np.where(k.damage[r] <= 1, 0., b[0]), k.source_flag,k.neighbor_offset,k.neighbors)[0]
        for i in np.flatnonzero(k.damage[r] > 0):
            rows.append(dict(state=r, station_id=k.ids[i], parent_completion_hr=float(a[0][i]),
                candidate_completion_hr=float(b[0][i]), completion_delta_hr=float(b[0][i]-a[0][i]),
                parent_origin=int(k.origin_index[a[3][i]]), candidate_origin=int(k.origin_index[b[3][i]]),
                parent_predecessor=k.ids[a[4][i]] if a[4][i] >= 0 else None,
                candidate_predecessor=k.ids[b[4][i]] if b[4][i] >= 0 else None,
                directed_travel_delta_hr=float(b[2][i]-a[2][i]),
                source_connection_delta_hr=float(bc[i]-ac[i])))
    return rows


def verify_candidates():
    tick = time.perf_counter()
    k, _, _, _ = load()
    ab = read(OUT / 'TASK_AB.json'); results = read(OUT / 'EXACT_SIX_SLOT_RESULTS.json')['results']
    context, _, _ = execution_context(k.ids)
    references = {name: old.per_sample(k, item['sequence']) for name, item in ab['parents'].items()}
    candidates = {}
    for row in results:
        candidates.setdefault(row['sequence_sha256'], dict(sequence=row['best_sequence'],
            expected_loss_hr=row['conditional_minimum_loss_hr'], originating_sets=[]))['originating_sets'].append(
                dict(parent=row['parent'], arm=row['arm'], set_number=row['set_number']))
    records = []; parity_rows = []; schedule_rows = []; events = []
    def gate(raw):
        return evaluate_source_gate(raw, context['graph'], context['sources'], threshold=.5)
    for number, (digest, item) in enumerate(candidates.items()):
        exact_values = old.per_sample(k, item['sequence'])
        production = []
        for r in range(64):
            realization = RealizationInputs(f'2pc50__planning_{r:04}', pd.Series(k.damage[r], index=k.ids),pd.Series(k.duration[r], index=k.ids))
            value = evaluate_direct_population_burden_aggregate(sequence=item['sequence'], realization=realization,
                crew_origin_ids=context['origins'], base_to_task_hr=context['base'], task_to_task_hr=context['task'],
                horizon_hr=k.horizon, source_gate=gate, station_population_mass=k.station_mass,population_resolved_mass=k.total_mass)
            assert abs(value-exact_values[r]) < TOL
            production.append(value)
            parity_rows.append(dict(sequence_sha256=digest, state=r, production_loss_hr=value,
                compiled_loss_hr=float(exact_values[r]), absolute_error_hr=abs(value-exact_values[r])))
        production = np.asarray(production)
        assert abs(production.mean()-item['expected_loss_hr']) < TOL
        comparisons = {name: influence(production-value) for name, value in references.items()}
        records.append(dict(sequence_sha256=digest, **item, production_loss_hr=float(production.mean()), comparisons=comparisons))
        if any(production.mean() < ab['parents'][s['parent']]['expected_loss_hr']-GAIN_TOL for s in item['originating_sets']):
            for parent in sorted({s['parent'] for s in item['originating_sets']}):
                for row in schedule_changes(k, ab['parents'][parent]['sequence'], item['sequence']):
                    schedule_rows.append(dict(sequence_sha256=digest, parent=parent, **row))
            delta = production-references['frozen_ga']
            for r in sorted({15, int(np.argmin(delta)), int(np.argmax(delta))}):
                events.append(dict(sequence_sha256=digest, **components(k,context,item['sequence'],ab['parents']['frozen_ga']['sequence'],r)))
        if (number+1) % 5 == 0:
            print('PRODUCTION_PARITY', number+1, '/',len(candidates), flush=True)
    # Native schedule evidence and parity attached to every restricted optimum.
    for row in results:
        changes = schedule_changes(k, ab['parents'][row['parent']]['sequence'], row['best_sequence'])
        row['mean_station_completion_delta_hr'] = float(np.mean([x['completion_delta_hr'] for x in changes]))
        row['origin_changed_station_states'] = sum(x['parent_origin'] != x['candidate_origin'] for x in changes)
        row['predecessor_changed_station_states'] = sum(x['parent_predecessor'] != x['candidate_predecessor'] for x in changes)
        row['total_directed_travel_delta_over64_hr'] = sum(x['directed_travel_delta_hr'] for x in changes)
        row['source_earlier_station_states'] = sum(x['source_connection_delta_hr'] < -GAIN_TOL for x in changes)
    save(OUT / 'NEIGHBORHOOD_SCHEDULE_SUMMARIES.json', results)
    save(OUT / 'CANDIDATE_PRODUCTION_INFLUENCE.json', dict(status='ALL_PRODUCTION_PARITY_PASS',
        candidates=records, unique_candidates=len(candidates), production_sample_calls=64*len(candidates),
        max_absolute_error_hr=max(x['absolute_error_hr'] for x in parity_rows),
        formal_candidate_replaced=False, physical_samples_created=0, elapsed_seconds=time.perf_counter()-tick))
    pd.DataFrame(parity_rows).to_csv(long_path(OUT / 'CANDIDATE_PER_STATE_PARITY.csv'), index=False)
    pd.DataFrame(schedule_rows).to_csv(long_path(OUT / 'IMPROVING_CANDIDATE_SCHEDULE_CHANGES.csv'), index=False)
    save(OUT / 'CANDIDATE_EVENT_DECOMPOSITION.json', events)


def preservation():
    setup_record = read(OUT / 'SETUP.json')
    current = snapshot(Path(setup_record['protected_revision_checkout']))
    assert current == read(OUT / 'PRESERVATION_BASELINE.json'), 'Protected revision changed externally; never overwrite it.'
    expected = read(OUT / 'TASK_AB.json')['input_identity']
    for name, digest in expected['input_sha256'].items():
        assert sha(REPO_ROOT / name) == digest, name
    # The prior readiness addendum and all scientific files have identical Git blobs.
    changed = git(REPO_ROOT, 'diff', '--name-only', START).decode().splitlines()
    allowed = ('results/diagnostics/ga_actionable_delay_six_slot_20261010/',
        'src/la_grid/diagnostics/ga_actionable_delay_', 'tests/test_actionable_delay_',
        'docs/reviewer/OPTIMIZATION_ACTIONABLE_DELAY_')
    assert all(p.startswith(allowed) for p in changed), changed
    save(OUT / 'PRESERVATION_VERIFIED.json', dict(status='PASS', **current,
        original_input_hashes_verified=True, new_physical_samples=0, formal_candidate_replaced=False,
        readiness_addendum_sha256=sha(PREVIOUS / 'VALIDATION_COMPARATORS_ADDENDUM.json')))
    hashes = {str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name != 'EVIDENCE_HASHES.json'}
    save(OUT / 'EVIDENCE_HASHES.json', hashes)
    print('PRESERVATION_PASS',len(current['files_sha256']), 'EVIDENCE',len(hashes),flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--task', required=True, choices=['setup','audit','select','exact','candidates','preservation'])
    p.add_argument('--source', type=Path)
    p.add_argument('--revision', type=Path)
    a = p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True); (OUT / 'neighborhoods').mkdir(exist_ok=True)
    if a.task == 'setup':
        setup(a.source,a.revision)
    else:
        {'audit':audit,'select':select,'exact':exact,'candidates':verify_candidates,'preservation':preservation}[a.task]()


if __name__ == '__main__':
    main()
