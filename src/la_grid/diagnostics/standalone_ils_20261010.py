"""Impact-only search diagnostics; original production physics remain untouched."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, replace
import gzip
import hashlib
import json
import os
from pathlib import Path
import pickle
import random
import subprocess
import time

import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_ils_parameter_defense_20261010 import lp, sha, read, hydrate, preservation
from la_grid.diagnostics.ga_research_preserve_20261009 import INPUTS
from la_grid.diagnostics.ga_init_param_20261009 import BASE
from la_grid.diagnostics import ga_variant_engine as eng
from la_grid.diagnostics.ga_search_budget_sensitivity import identity
from la_grid.revision.r1_ga_exact_kernel import ExactDirectPlanningKernel
from la_grid.revision.r1_realization_scheduling import RealizationInputs
from la_grid.revision.r1_equity_amendment_execute import execution_context

R = lp(REPO_ROOT)
OUT = R / 'results/diagnostics/standalone_ils_final_method_20261010'
SMOKE = tuple(range(2026102000, 2026102008))
MAIN = tuple(range(2026102100, 2026102120))
EXTEND = MAIN[:10]
BUDGETS = (20000, 50000, 100000, 250000, 500000)
CONFIG = dict(neighborhood='uniform distinct-position swap', tolerance_hr=1e-12,
              stagnation_attempts=2000, perturbation_swaps=[2, 4, 8],
              restart_reference='best', attempt_cap_multiplier=60)
GA_CONFIG = replace(BASE, initialization='legacy')


def save(path, value):
    path = lp(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def load_model():
    """Read frozen states, not historical optimized sequences or comparator scores."""
    form = R / 'Formal_Experiment_20260923'
    final = read(form / 'Stage 5 Output_expanded/FINAL_DIRECT_COMMUNITY_SEQUENCE.json')
    physical = form / 'Stage 1 Output_expanded/physical_inputs_2pc50.npz'
    assert sha(physical) == read(physical.parent / 'PHYSICAL_INPUTS_FROZEN.json')['files_sha256']['2pc50']
    with np.load(physical) as z:
        ids = z['station_ids'].astype(str).tolist()
        ds, duration = z['planning_ds'].T.copy(), z['planning_duration'].T.copy()
    assert ds.shape == duration.shape == (64, 92)
    samples, hashes = [], []
    for i in range(64):
        hashes.append(hashlib.sha256(('\n'.join(ids)+'\n').encode() + ds[i].astype('<i8').tobytes() + duration[i].astype('<f8').tobytes()).hexdigest())
        samples.append(RealizationInputs(f'2pc50__planning_{i:04}', pd.Series(ds[i], index=ids), pd.Series(duration[i], index=ids)))
    assert hashes == final['planning_sample_hashes']
    context, _, ctx_hash = execution_context(ids)
    context['G'] = context['graph']
    w = pd.read_csv(R / 'Data/JULY_UTILITY_CONSTRAINED_92.csv', dtype={'tract_id': str, 'substation_id': str})
    assert w.tract_id.nunique() == 2315
    pop = w.groupby('tract_id').population.first()
    matrix = w.pivot_table(index='tract_id', columns='substation_id', values='weight', aggfunc='sum', fill_value=0).reindex(columns=ids, fill_value=0)
    mass = matrix.T.to_numpy() @ pop.reindex(matrix.index).to_numpy()
    kernel = ExactDirectPlanningKernel(planning=samples, context=context, station_population_mass=mass, horizon_hr=final['H_plan_hr'])
    impact = tuple(read(form / 'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json')['2pc50']['impact-first'])
    assert len(impact) == 92 and set(impact) == set(ids)
    files = list(INPUTS) + ['Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz',
        'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json',
        'src/la_grid/revision/r1_ga_exact_kernel.py', 'src/la_grid/revision/r1_ga_revision.py',
        'src/la_grid/revision/r1_realization_scheduling.py', 'src/la_grid/revision/r1_source_gate.py',
        'config/parent_frozen_design/FINAL_EXPERIMENT_MATRIX.json']
    return kernel, impact, dict(planning_sample_hashes=hashes, context_identity=ctx_hash,
        files_sha256={p: sha(R / p) for p in files}, horizon_hr=kernel.horizon,
        impact_sha256=identity(impact), loader_objective_calls=0)


def setup():
    if (OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json').exists():
        raise RuntimeError('Do not overwrite an existing prospective study.')
    for p in list(INPUTS) + ['Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz']:
        hydrate(R / p)
    historical = R / 'results/diagnostics/ga_ils_parameter_defense_20261010/EXPERIMENT_INVENTORY.csv'
    hydrate(historical)
    seeds = pd.read_csv(historical).seed.dropna().astype(int).tolist()
    assert not set(seeds + list(range(2026101100, 2026101108)) + list(range(2026101200, 2026101220))) & set(SMOKE + MAIN)
    save(OUT / 'PRESERVATION_BASELINE.json', preservation())
    save(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json', dict(
        starting_commit='62f0c2be4f1e37f25e3db8d0d042cd5d0cfcfd3f',
        branch='diagnostics/standalone-ils-final-method-decision-20261010',
        smoke_seeds=SMOKE, main_seeds=MAIN, extension_seeds=EXTEND,
        smoke_methods=['ILS'], main_methods=['ILS', 'GA'], smoke_budget=20000,
        main_budget=100000, extension_budgets=[250000, 500000], checkpoints=BUDGETS,
        ils=CONFIG, ga=asdict(GA_CONFIG), ga_attempt_cap_multiplier=50,
        ga_initialization='exactly one Impact-first + 99 independent random permutations; no prior/no neighbors',
        candidate_pool='20 main ILS final100k and prescribed10 continuations at250k/500k; smoke excluded',
        candidate_selection='lowest exact mean planning J, exact tie SHA256 ascending then seed then budget',
        comparisons='ILS-GA paired by optimizer seed at each budget; frozenGA separately fixed-reference',
        bootstrap_replicates=20000, bootstrap_seed=2026102200,
        uncertainty='pointwise paired percentile bootstrap and paired t intervals; simultaneous Bonferroni t across 5 budget endpoints',
        diagnostic_tie_tolerance_hr=1e-9, no_new_physical_samples=True,
        no_validation_outcome_access=True, formal_policy_unchanged=True,
        workers=12, seed_overlap_with_historical=False,
        decision_criteria='independence; entire workflow simplicity; fair/frozen candidate quality; seed/budget reliability; parameter defensibility; no validation contamination',
        no_noninferiority_margin_claim='No prospective margin specified; competitive descriptive judgment, not a formal equivalence test'))
    print('REGISTERED', len(SMOKE), len(MAIN), len(EXTEND), flush=True)


class StandaloneILS:
    """One-state swap descent; state transitions complete before budget stop."""
    def __init__(self, ids, impact, objective, seed, config=None, state=None):
        self.ids, self.index = tuple(ids), {s: i for i, s in enumerate(ids)}
        self.objective, self.config = objective, dict(CONFIG if config is None else config)
        self.rng = random.Random(seed)
        self.seed = seed
        if state is not None:
            assert state['seed'] == seed and state['config'] == self.config and tuple(state['ids']) == self.ids
            self.data = state
            self.rng.setstate(state['rng'])
        else:
            assert len(impact) == len(self.ids) and set(impact) == set(self.ids)
            self.data = dict(seed=seed, config=self.config, ids=self.ids, current=tuple(impact), current_score=None,
                best=tuple(impact), best_score=None, phase='initial', stagnant=0, accepted=0, restarts=0,
                attempts=0, local_proposals=0, cache={}, improvements=[], checkpoints=[], restart_records=[],
                objective_seconds=0., wall_seconds=0., cpu_seconds=0., invalid_permutations=0,
                initial_sequences=[list(impact)], initial_archive=[list(impact)])

    def swap(self, seq):
        a, b = self.rng.sample(range(len(seq)), 2)
        v = list(seq)
        v[a], v[b] = v[b], v[a]
        return tuple(v), [a, b]

    def evaluate(self, seq):
        d = self.data
        assert len(seq) == len(self.ids) and set(seq) == set(self.ids)
        key = bytes(self.index[s] for s in seq)
        d['attempts'] += 1
        if key not in d['cache']:
            tick = time.perf_counter()
            value = float(self.objective(seq))
            d['objective_seconds'] += time.perf_counter() - tick
            assert np.isfinite(value)
            d['cache'][key] = value
            if d['best_score'] is None or value > d['best_score']:
                d['best'], d['best_score'] = tuple(seq), value
                d['improvements'].append(dict(evaluations=len(d['cache']), attempts=d['attempts'], loss_hr=-value, sequence=list(seq), sequence_sha256=identity(seq)))
        return d['cache'][key]

    def run(self, budget, checkpoints=BUDGETS):
        d = self.data
        tick, cpu = time.perf_counter(), time.process_time()
        while len(d['cache']) < budget and d['attempts'] < self.config['attempt_cap_multiplier'] * budget:
            if d['phase'] == 'initial':
                d['current_score'] = self.evaluate(d['current'])
                d['initial_loss_hr'] = -d['current_score']
                d['phase'] = 'local'
            elif d['phase'] == 'perturb':
                strength = self.config['perturbation_swaps'][d['restarts'] % len(self.config['perturbation_swaps'])]
                start = d['best']
                seq, intermediate = start, []
                for _ in range(strength):
                    seq, pair = self.swap(seq)
                    intermediate.append(dict(pair=pair, key=bytes(self.index[s] for s in seq).hex()))
                key = bytes(self.index[s] for s in seq)
                record = dict(restart=d['restarts'] + 1, strength=strength, before_attempts=d['attempts'],
                    before_distinct=len(d['cache']), result_is_reference=seq == start, cached_before=key in d['cache'],
                    revisited_intermediate=len(intermediate)-len(set(s['key'] for s in intermediate)), swaps=intermediate)
                d['current_score'] = self.evaluate(seq)
                d['current'] = seq
                d['restarts'] += 1
                d['stagnant'], d['phase'] = 0, 'local'
                d['restart_records'].append(record)
            else:
                seq, _ = self.swap(d['current'])
                value = self.evaluate(seq)
                d['local_proposals'] += 1
                if value > d['current_score'] + self.config['tolerance_hr']:
                    d['current'], d['current_score'] = seq, value
                    d['accepted'] += 1
                    d['stagnant'] = 0
                else:
                    d['stagnant'] += 1
                if d['stagnant'] >= self.config['stagnation_attempts']:
                    d['phase'] = 'perturb'
            if len(d['cache']) in checkpoints and not any(c['budget'] == len(d['cache']) for c in d['checkpoints']):
                d['checkpoints'].append(dict(budget=len(d['cache']), loss_hr=-d['best_score'], attempts=d['attempts'],
                    cache_hits=d['attempts']-len(d['cache']), objective_seconds=d['objective_seconds'],
                    wall_seconds=d['wall_seconds']+time.perf_counter()-tick,
                    cpu_seconds=d['cpu_seconds']+time.process_time()-cpu, accepted=d['accepted'], restarts=d['restarts'],
                    sequence=list(d['best']), sequence_sha256=identity(d['best'])))
        d['wall_seconds'] += time.perf_counter() - tick
        d['cpu_seconds'] += time.process_time() - cpu
        d['rng'] = self.rng.getstate()
        return d


def write_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with gzip.open(tmp, 'wb', compresslevel=1) as f:
        pickle.dump(state, f, protocol=5)
    tmp.replace(path)


def read_state(path):
    with gzip.open(path, 'rb') as f:
        return pickle.load(f)


def worker_init():
    global KERNEL, IMPACT, MODEL, SETUP_SECONDS
    tick = time.perf_counter()
    KERNEL, IMPACT, MODEL = load_model()
    # One counted JIT compilation evaluation, not injected into any run cache.
    compiled = -KERNEL.score(IMPACT)
    assert abs(compiled - 33.57830255999924) < 1e-8
    SETUP_SECONDS = time.perf_counter() - tick


def run_job(job):
    phase, method, seed, budgets = job
    folder = OUT / phase / f'{method.lower()}_s{seed}'
    final = folder / f'FINAL_{budgets[-1]}.json'
    if final.exists():
        return dict(reused=True, **read(final))
    folder.mkdir(parents=True, exist_ok=True)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip()
    records = []
    if method == 'ILS':
        path = folder / 'STATE.pkl.gz'
        state = read_state(path) if path.exists() else None
        search = StandaloneILS(KERNEL.ids, IMPACT, KERNEL.score, seed, state=state)
        for budget in budgets:
            receipt = folder / f'FINAL_{budget}.json'
            if receipt.exists():
                records.append(read(receipt))
                continue
            d = search.run(budget)
            write_state(path, d)
            row = dict(method=method, phase=phase, seed=seed, budget=budget,
                distinct_evaluations=len(d['cache']), attempts=d['attempts'], cache_hits=d['attempts']-len(d['cache']),
                loss_hr=-d['best_score'], sequence=list(d['best']), sequence_sha256=identity(d['best']),
                accepted=d['accepted'], restarts=d['restarts'], local_proposals=d['local_proposals'],
                restart_cancellations=sum(r['result_is_reference'] for r in d['restart_records']),
                restart_cached=sum(r['cached_before'] for r in d['restart_records']),
                restart_intermediate_revisits=sum(r['revisited_intermediate'] for r in d['restart_records']),
                objective_seconds=d['objective_seconds'], wall_seconds=d['wall_seconds'], cpu_seconds=d['cpu_seconds'],
                initial_sequences=d['initial_sequences'], initial_archive=d['initial_archive'],
                initialization='only Impact-first', initial_loss_hr=d['initial_loss_hr'],
                completed=len(d['cache']) == budget, checkpoint_sha256=sha(path), config=CONFIG)
            save(folder / 'STRICT_IMPROVEMENTS.json', d['improvements'])
            save(folder / 'RESTART_RECORDS.json', d['restart_records'])
            save(folder / 'BUDGET_CHECKPOINTS.json', d['checkpoints'])
            row.update(model_identity=MODEL, execution_commit=commit, implementation_sha256=sha(__file__),
                worker_pid=os.getpid(), worker_setup_seconds=SETUP_SECONDS, worker_setup_objective_calls=1)
            save(receipt, row)
            records.append(row)
            print('BOUNDARY', method, seed, budget, row['loss_hr'], flush=True)
    else:
        original = eng.initialize
        captured = {}
        def initialize(domain, inc, rng, config, quality):
            assert list(inc) == ['impact-first'] and quality is None
            pop = original(domain, inc, rng, config, quality)
            assert pop[0] == IMPACT and len(pop) == 100
            captured.update(initial_sequences=[list(s) for s in pop], initial_archive=[list(IMPACT)],
                post_initializer_rng_sha256=hashlib.sha256(pickle.dumps(rng.getstate())).hexdigest())
            save(folder / 'INITIALIZATION_RECEIPT.json', captured)
            return pop
        eng.initialize = initialize
        try:
            for budget in budgets:
                receipt = folder / f'FINAL_{budget}.json'
                if receipt.exists():
                    records.append(read(receipt))
                    continue
                tick, cpu = time.perf_counter(), time.process_time()
                result = eng.run_search(items=KERNEL.ids, incumbents={'impact-first': IMPACT}, objective=KERNEL.score,
                    seed=seed, config=GA_CONFIG, max_evaluations=budget, checkpoints=BUDGETS, folder=folder, quality=None)
                state = result['state']
                init = read(folder / 'INITIALIZATION_RECEIPT.json')
                row = dict(method=method, phase=phase, seed=seed, budget=budget,
                    distinct_evaluations=len(result['cache']), attempts=state['attempts'], cache_hits=state['attempts']-len(result['cache']),
                    loss_hr=-result['best_fitness'], sequence=list(result['best_sequence']),
                    sequence_sha256=identity(result['best_sequence']),
                    accepted=None, restarts=state['restart_count'], generation=state['generation'],
                    objective_seconds=state['score_seconds'], wall_seconds=result['elapsed_seconds'],
                    incremental_wrapper_wall_seconds=time.perf_counter()-tick,
                    incremental_cpu_seconds=time.process_time()-cpu, **init,
                    initialization='Impact-first + 99 random; archive only Impact-first',
                    completed=len(result['cache']) == budget, checkpoint_sha256=sha(folder / 'CHECKPOINT.pkl.gz'),
                    config=asdict(GA_CONFIG), model_identity=MODEL, execution_commit=commit,
                    implementation_sha256=sha(__file__), worker_pid=os.getpid(),
                    worker_setup_seconds=SETUP_SECONDS, worker_setup_objective_calls=1)
                assert state['expensive_calls'] == len(result['cache']) and state['lookup_calls'] == 0
                save(receipt, row)
                records.append(row)
                print('BOUNDARY', method, seed, budget, row['loss_hr'], flush=True)
        finally:
            eng.initialize = original
    return {k: records[-1][k] for k in ('phase', 'method', 'seed', 'budget', 'loss_hr', 'completed', 'distinct_evaluations')}


def batch(phase, workers):
    assert read(OUT / 'TEST_RECEIPT.json')['passed']
    assert read(OUT / 'PREREGISTRATION_COMMIT.json')['design_sha256'] == sha(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json')
    if phase == 'smoke':
        jobs = [(phase, 'ILS', seed, [20000]) for seed in SMOKE]
    else:
        assert read(OUT / 'smoke_EXECUTION.json')['all_completed']
        jobs = [(phase, method, seed, [100000, 250000, 500000] if seed in EXTEND else [100000]) for seed in MAIN for method in ('ILS', 'GA')]
    tick = time.perf_counter()
    complete = []
    with ProcessPoolExecutor(max_workers=workers, initializer=worker_init) as ex:
        futures = {ex.submit(run_job, job): job for job in jobs}
        for f in as_completed(futures):
            try:
                row = f.result()
            except Exception as e:
                save(OUT / f'{phase}_FAILURE.json', dict(job=futures[f], error=repr(e)))
                raise
            complete.append(row)
            print('COMPLETED', phase, len(complete), '/', len(jobs), json.dumps(row), flush=True)
    save(OUT / f'{phase}_EXECUTION.json', dict(jobs=len(jobs), workers=workers,
        all_completed=all(r['completed'] for r in complete), results=complete,
        wall_seconds=time.perf_counter()-tick, setup_objective_calls=min(workers, len(jobs))))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('task', choices=['setup', 'smoke', 'main', 'preservation'])
    p.add_argument('--workers', type=int, default=12)
    a = p.parse_args()
    if a.task == 'setup':
        setup()
    elif a.task in ('smoke', 'main'):
        batch(a.task, a.workers)
    else:
        current = preservation()
        assert current == read(OUT / 'PRESERVATION_BASELINE.json')
        save(OUT / 'PRESERVATION_VERIFIED.json', dict(status='PASS', **current))
        print('PRESERVATION_PASS', len(current['files_sha256']))


if __name__ == '__main__':
    main()
