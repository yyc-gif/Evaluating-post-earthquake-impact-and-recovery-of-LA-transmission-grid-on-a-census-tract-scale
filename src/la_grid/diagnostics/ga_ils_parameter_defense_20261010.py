"""Prospective, planning-only GA/ILS evidence; never consumes validation outcomes."""
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
import platform
import random
import subprocess
import time

import numpy as np
import pandas as pd

from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics import ga_variant_engine as eng
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.diagnostics.ga_init_param_20261009 import BASE, load, make_initializer
from la_grid.diagnostics.ga_research_preserve_20261009 import snapshot, INPUTS

START = 'e7d05e2649f3be2ccfbf9398d86e0612407dd5ea'
BRANCH = 'diagnostics/ga-ils-reviewer-parameter-defense-20261010'
OUT = R / 'results/diagnostics/ga_ils_parameter_defense_20261010'
SCREEN = tuple(range(2026101100, 2026101108))
CONFIRM = tuple(range(2026101200, 2026101220))
SCREEN_CASES = (
    'ga_elite0', 'ga_elite1', 'ga_elite2', 'ga_elite3',
    'ils_mix', 'ils_swap', 'ils_insertion', 'ils_inversion',
    'ils_stag200', 'ils_stag2000', 'ils_small', 'ils_large',
    'ils_current', 'ils_no_perturb', 'ils_swap_stag200', 'ils_insertion_stag200',
)
ILS_CASES = {
    'ils_mix': {}, 'ils_swap': {'operators': ['swap']},
    'ils_insertion': {'operators': ['insertion']},
    'ils_inversion': {'operators': ['inversion']},
    'ils_stag200': {'stagnation': 200}, 'ils_stag2000': {'stagnation': 2000},
    'ils_small': {'perturbation': [1, 2, 4]},
    'ils_large': {'perturbation': [4, 8, 16]},
    'ils_current': {'restart_reference': 'current'},
    'ils_no_perturb': {'perturb': False},
    'ils_swap_stag200': {'operators': ['swap'], 'stagnation': 200},
    'ils_insertion_stag200': {'operators': ['insertion'], 'stagnation': 200},
    'ils_cold': {'warm': False},
    'ils_swap_stag2000': {'operators': ['swap'], 'stagnation': 2000},
    'ils_swap_no_perturb': {'operators': ['swap'], 'perturb': False},
}
GA_CASES = {f'ga_elite{n}': {'elites': n} for n in range(4)}
GA_CASES['ga_cold'] = {'warm': False}


def lp(path):
    path = Path(path)
    return Path('\\\\?\\' + str(path.resolve())) if os.name == 'nt' and not str(path).startswith('\\\\?\\') else path


def sha(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(lp(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    def clean(item):
        if isinstance(item, dict): return {k: clean(v) for k, v in item.items()}
        if isinstance(item, (tuple, list)): return [clean(v) for v in item]
        if isinstance(item, np.generic): item = item.item()
        if isinstance(item, float) and not np.isfinite(item): return None
        return item
    path = lp(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n', encoding='utf-8')


def hydrate(path):
    data = lp(path).read_bytes()
    if not data.startswith(b'version https://git-lfs.github.com/spec/v1'):
        return
    fields = dict(s.split(' ', 1) for s in data.decode().splitlines())
    oid = fields['oid'][7:]
    common = subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=R, text=True).strip()
    source = Path(common) / 'lfs/objects' / oid[:2] / oid[2:4] / oid
    assert sha(source) == oid
    assert lp(source).stat().st_size == int(fields['size'])
    lp(path).write_bytes(lp(source).read_bytes())


def preservation():
    revision = Path(read(R / 'results/diagnostics/independent_validation_ready_20261010/FINAL_VALIDATION_FREEZE_RECEIPT.json')['protected_revision_checkout'])
    result = snapshot(revision)
    protected = ['results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json',
                 'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json']
    validation = R / 'results/diagnostics/independent_validation_ready_20261010'
    protected += [str(p.relative_to(lp(R))) for p in lp(validation).rglob('*') if p.is_file() and '.git' not in p.parts]
    # Hash preservation only: no validation values, cases, trajectories or samples loaded.
    result['validation_and_formal_sha256'] = {p: sha(R / p) for p in sorted(protected)}
    return result


def setup():
    if lp(OUT / 'PRESERVATION_BASELINE.json').exists():
        raise RuntimeError('Existing study authority must not be overwritten; use an isolated fresh output area.')
    lp(OUT).mkdir(parents=True, exist_ok=True)
    paths = list(INPUTS)
    paths += ['Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz']
    for name in paths:
        hydrate(R / name)
    # Historical numerical tables only; do not hydrate or parse validation outcomes.
    for directory in ('ga_initialization_reconciliation_20261009', 'ga_deeper_research_20261009/continuation',
                      'ga_optimization_20261009', 'final_ga_method_20261009',
                      'ga_noncontiguous_connectivity_lns_20261010', 'ga_scheduling_aware_lns_20261010'):
        for p in lp(R / 'results/diagnostics' / directory).rglob('*.csv'):
            hydrate(p)
    save(OUT / 'PRESERVATION_BASELINE.json', preservation())
    design = dict(start=START, branch=BRANCH, screen_seeds=SCREEN, confirmation_seeds=CONFIRM,
        screen_budget=20000, confirmation_budget=100000, screen_cases=SCREEN_CASES,
        fixed_confirmation_cases=list(GA_CASES)[:4]+['ils_mix', 'ils_swap', 'ils_insertion', 'ils_inversion', 'ils_current', 'ils_no_perturb'],
        screen_selected_pairs=[['ils_stag200', 'ils_stag2000'], ['ils_small', 'ils_large']],
        selection_rule='lowest pair screen mean; exact tie first listed', cold_cases=['ga_cold', 'ils_cold'],
        refinement_seeds=CONFIRM[:5], refinement_additional_budget=150000, workers=12,
        reporting_tolerance_hr=1e-10, bootstrap_replicates=20000, bootstrap_seed=2026101300,
        ga=asdict(BASE), ils_default=ils_config('ils_mix'), no_validation_access=True,
        new_physical_samples=0, formal_candidates_changed=False,
        family_definitions={'ga_elite': ['0-1', '2-1', '3-1'],
            'ils_confirmation': ['swap-mix', 'insertion-mix', 'inversion-mix', 'current-mix',
                'no_perturb-mix (cost-censored if incomplete)', 'screen_selected_stagnation-mix', 'screen_selected_perturbation-mix'],
            'method': ['warm_ILS-GA', 'cold_ILS-GA', 'ILS_warm-cold', 'GA_warm-cold'],
            'screen_interaction': ['swap x stagnation200', 'insertion x stagnation200']})
    save(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json', design)
    print('SETUP_PRESERVATION', len(read(OUT / 'PRESERVATION_BASELINE.json')['files_sha256']), flush=True)


def ils_config(case):
    return dict(operators=['swap', 'insertion', 'inversion'], stagnation=800,
        perturbation=[2, 4, 8], restart_reference='best', perturb=True, warm=True,
        strict_tolerance_hr=1e-12, attempt_limit_multiplier=60) | ILS_CASES[case]


class Meter:
    def __init__(self, kernel, budget):
        self.kernel, self.budget = kernel, budget
        self.cache = {}
        self.attempts = 0
        self.best = -np.inf
        self.sequence = None
        self.path = []
        self.checkpoints = []
        self.objective_seconds = 0.

    def evaluate(self, sequence):
        sequence = tuple(sequence)
        key = bytes(self.kernel.index[s] for s in sequence)
        self.attempts += 1
        if key not in self.cache:
            if len(self.cache) >= self.budget:
                raise StopIteration
            tick = time.perf_counter()
            value = float(self.kernel.score(sequence))
            self.objective_seconds += time.perf_counter() - tick
            assert np.isfinite(value)
            self.cache[key] = value
            if value > self.best:
                self.best, self.sequence = value, sequence
                self.path.append(dict(evaluation=len(self.cache), loss_hr=-value, sequence_sha256=old.identity(sequence)))
            if len(self.cache) in {20000, 50000, 100000, self.budget}:
                self.checkpoints.append(dict(evaluations=len(self.cache), loss_hr=-self.best, attempts=self.attempts))
        return self.cache[key]


def ils_search(kernel, inc, quality, seed, budget, config):
    rng = random.Random(seed)
    meter = Meter(kernel, budget)
    tick = time.perf_counter()
    for seq in inc.values():
        meter.evaluate(seq)
    current = tuple(quality if config['warm'] else inc['impact-first'])
    value = meter.evaluate(current)
    initial_value = value
    initial_sequence = current
    rng_hash = hashlib.sha256(pickle.dumps(rng.getstate())).hexdigest()
    accepted = restarts = stagnant = proposals = 0
    counts = {o: dict(proposals=0, accepted=0, perturbations=0) for o in config['operators']}

    def proposal(seq, perturbation=False):
        # Single-operator variants deliberately avoid the mixture-selection RNG draw.
        ops = config['operators']
        op = ops[rng.randrange(len(ops))] if len(ops) > 1 else ops[0]
        counts[op]['perturbations' if perturbation else 'proposals'] += 1
        return eng.mutation(seq, rng, op), op

    while len(meter.cache) < budget and meter.attempts < config['attempt_limit_multiplier'] * budget:
        candidate, op = proposal(current)
        proposals += 1
        score = meter.evaluate(candidate)
        if score > value + config['strict_tolerance_hr']:
            current, value = candidate, score
            accepted += 1
            counts[op]['accepted'] += 1
            stagnant = 0
        else:
            stagnant += 1
        if config['perturb'] and stagnant >= config['stagnation']:
            current = tuple(meter.sequence) if config['restart_reference'] == 'best' else current
            for _ in range(config['perturbation'][restarts % len(config['perturbation'])]):
                current, _ = proposal(current, True)
            try:
                value = meter.evaluate(current)
            except StopIteration:
                break
            stagnant = 0
            restarts += 1
    row = dict(method='ILS', seed=seed, budget=budget, config=config,
        distinct_evaluations=len(meter.cache), attempted_evaluations=meter.attempts,
        duplicates=meter.attempts-len(meter.cache), search_best_loss_hr=-meter.best,
        best_sequence=list(meter.sequence), sequence_sha256=old.identity(meter.sequence),
        initial_best_loss_hr=-max(meter.cache[bytes(kernel.index[s] for s in seq)] for seq in list(inc.values())+[initial_sequence]),
        initial_current_loss_hr=-initial_value, initial_sequences=[list(s) for s in list(inc.values())+[initial_sequence]],
        post_initializer_rng_sha256=rng_hash, accepted_moves=accepted, restart_count=restarts,
        local_proposals=proposals, operator_counts=counts, strict_improvements=meter.path,
        checkpoints=meter.checkpoints, objective_seconds=meter.objective_seconds,
        elapsed_wall_seconds=time.perf_counter()-tick, completed_budget=len(meter.cache)==budget,
        censoring=None if len(meter.cache)==budget else 'attempt cap; neighborhood-accessibility control')
    row['initial_population_sha256'] = hashlib.sha256(json.dumps(row['initial_sequences'], separators=(',', ':')).encode()).hexdigest()
    return row


def ga_search(kernel, inc, quality, seed, budget, changes, prefix=None):
    config = replace(BASE, **{k: v for k, v in changes.items() if k != 'warm'})
    warm = changes.get('warm', True)
    original = eng.initialize
    capture = {}

    def initialize(domain, refs, rng, conf, prior):
        if warm:
            pop = original(domain, refs, rng, conf, prior)
        else:
            pop = make_initializer(dict(n=25, parents='impact', warm=False), original)(domain, refs, rng, conf, prior)
        capture.update(initial_sequences=[list(s) for s in pop],
            post_initializer_rng_sha256=hashlib.sha256(pickle.dumps(rng.getstate())).hexdigest(),
            initial_population_sha256=hashlib.sha256(json.dumps(pop, separators=(',', ':')).encode()).hexdigest())
        return pop

    eng.initialize = initialize
    try:
        res = eng.run_search(items=kernel.ids, incumbents=inc, objective=kernel.score,
            seed=seed, config=config, quality=quality, max_evaluations=budget,
            checkpoints=(20000, 50000, 100000, budget), folder=None, lookup_objective=prefix)
    finally:
        eng.initialize = original
    st = res['state']
    hist = res['history']
    first = hist.iloc[0]
    # No extra objective or RNG call in observation.
    row = dict(method='GA', seed=seed, budget=budget, config=asdict(config)|dict(warm=warm),
        distinct_evaluations=len(res['cache']), actual_new_expensive=st['expensive_calls'],
        prefix_cache_reused=st['lookup_calls'], attempted_evaluations=st['attempts'],
        duplicates=st['attempts']-len(res['cache']), search_best_loss_hr=-res['best_fitness'],
        best_sequence=list(res['best_sequence']), sequence_sha256=old.identity(res['best_sequence']),
        initial_best_loss_hr=float(first['population_best_service_loss_hr']),
        generations=st['generation'], completed_budget=len(res['cache'])==budget,
        accepted_moves=None, restart_count=st['restart_count'], objective_seconds=st['score_seconds'],
        elapsed_wall_seconds=res['elapsed_seconds'], checkpoints=res['budget_rows'],
        dynamics_initial=first.where(pd.notna(first), None).to_dict(),
        dynamics_final=hist.iloc[-1].where(pd.notna(hist.iloc[-1]), None).to_dict(), **capture)
    row['mean_selection_intensity'] = float(hist['parent_selection_intensity'].dropna().mean()) if 'parent_selection_intensity' in hist else None
    row['mean_effective_parent_count'] = float(hist['parent_effective_count'].dropna().mean()) if 'parent_effective_count' in hist else None
    row['mean_position_entropy'] = float(hist['position_entropy'].mean())
    row['history'] = hist.replace({np.nan: None}).to_dict('records')
    return row, res['cache']


def init_worker():
    global KERNEL, INC, QUALITY, IDENTITY, SETUP_SECONDS
    tick = time.perf_counter()
    KERNEL, INC, QUALITY, IDENTITY = load()
    SETUP_SECONDS = time.perf_counter()-tick


def run_job(job):
    phase, case, seed, budget = job
    dest = OUT / phase / f'{case}_s{seed}.json'
    if lp(dest).exists():
        row = read(dest)
        assert row['seed']==seed and row['case']==case and row['budget']==budget
        return dict(reused=True, path=str(dest.relative_to(R)), **{k: row[k] for k in ('case', 'seed', 'search_best_loss_hr')})
    tick = time.perf_counter()
    cpu_tick = time.process_time()
    cache = None
    if case in GA_CASES:
        row, cache = ga_search(KERNEL, INC, QUALITY, seed, budget, GA_CASES[case])
    else:
        row = ils_search(KERNEL, INC, QUALITY, seed, budget, ils_config(case))
    assert len(row['best_sequence'])==len(set(row['best_sequence']))==92
    assert set(row['best_sequence'])==set(KERNEL.ids)
    row.update(case=case, phase=phase, input_identity=IDENTITY, setup_scores_per_worker=8,
        worker_setup_seconds=SETUP_SECONDS, worker_pid=os.getpid(), cpu_seconds=time.process_time()-cpu_tick,
        runtime=dict(python=platform.python_version(), platform=platform.platform(), numpy=np.__version__),
        source_sha256=sha(__file__), execution_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'],cwd=R,text=True).strip(),
        postvalidation_exploratory=True, formal_candidate_changed=False, physical_samples_generated=0,
        wrapper_wall_seconds=time.perf_counter()-tick)
    if cache is not None and phase=='confirmation' and case=='ga_elite1' and seed in CONFIRM[:5]:
        path = lp(OUT / 'prefixes' / f'ga_s{seed}.pkl.gz')
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, 'wb', compresslevel=1) as f:
            pickle.dump(cache, f, protocol=5)
        row['prefix_path'] = str(path.relative_to(lp(R)))
        row['prefix_sha256'] = sha(path)
    save(dest, row)
    return {k: row[k] for k in ('case', 'seed', 'search_best_loss_hr', 'distinct_evaluations', 'completed_budget')}


def batch(phase, workers):
    design = read(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json')
    if phase=='screen':
        cases, seeds, budget = design['screen_cases'], SCREEN, 20000
    else:
        selected = read(OUT / 'SCREEN_SELECTION.json')['cases']
        cases, seeds, budget = design['fixed_confirmation_cases']+selected+design['cold_cases']+design.get('screen_mechanism_confirmation_cases',[]), CONFIRM, 100000
    assert not set(SCREEN)&set(CONFIRM)
    tick = time.perf_counter()
    completed = []
    # Order configurations within each seed consistently; all cases receive equal worker settings.
    jobs = [(phase, case, seed, budget) for seed in seeds for case in cases]
    with ProcessPoolExecutor(max_workers=workers, initializer=init_worker) as executor:
        futures = {executor.submit(run_job, job): job for job in jobs}
        for f in as_completed(futures):
            try:
                row = f.result()
            except Exception as exc:
                save(OUT / f'{phase}_FAILURE.json', dict(job=futures[f], error=repr(exc)))
                raise
            completed.append(row)
            print('COMPLETED', phase, len(completed), '/', len(jobs), json.dumps(row), flush=True)
    save(OUT / f'{phase}_EXECUTION.json', dict(status='COMPLETE', jobs=len(jobs), workers=workers,
        wall_seconds=time.perf_counter()-tick, results=completed, setup_scores=workers*8))


def select():
    design = read(OUT / 'EXPERIMENT_DESIGN_AND_SEEDS.json')
    rows = [read(p) for p in lp(OUT / 'screen').glob('*.json')]
    assert len(rows)==len(design['screen_cases'])*8
    means = {c: float(np.mean([r['search_best_loss_hr'] for r in rows if r['case']==c])) for c in design['screen_cases']}
    cases = [min(pair, key=lambda c: (means[c], pair.index(c))) for pair in design['screen_selected_pairs']]
    save(OUT / 'SCREEN_SELECTION.json', dict(cases=cases, means=means, rule=design['selection_rule'],
        new_confirmation_seeds=CONFIRM, postvalidation_exploratory=True))
    print('SCREEN_SELECTION', cases, flush=True)


def refine_jobs():
    from la_grid.diagnostics.ga_local_refinement_20261009 import refine
    k, inc, prior, _ = load()
    records = []
    for seed in CONFIRM[:5]:
        base = read(OUT / 'confirmation' / f'ils_mix_s{seed}.json')
        folder = OUT / 'refinement' / f's{seed}'
        if lp(folder / 'JOINT_ACCOUNTING.json').exists():
            records.append(read(folder / 'JOINT_ACCOUNTING.json'))
            continue
        class Counted:
            def __init__(self, kernel): self.k, self.calls = kernel, 0
            def __getattr__(self, name): return getattr(self.k, name)
            def score(self, seq): self.calls += 1; return self.k.score(seq)
        counted = Counted(k)
        result, _ = refine(kernel=counted, start_sequence=base['best_sequence'], budget=150001, folder=lp(folder))
        # Original routine makes three starting-score calls and seeds one cache entry.
        additional = counted.calls-3
        joint_budget = 100000+additional
        with gzip.open(lp(OUT / 'prefixes' / f'ga_s{seed}.pkl.gz'), 'rb') as f:
            prefix = pickle.load(f)
        assert len(prefix)==100000
        ga, _ = ga_search(k, inc, prior, seed, joint_budget, GA_CASES['ga_elite1'], prefix=prefix)
        assert ga['prefix_cache_reused']==100000
        assert ga['actual_new_expensive']==additional
        save(folder / 'GA_JOINT_BUDGET.json', ga)
        rec = dict(seed=seed, base_ils_distinct=100000, refinement_actual_score_calls=counted.calls,
            refinement_additional_distinct=additional, refinement_setup_calls=3,
            refinement_cache_hits=result['total_attempts']-additional,
            refinement_wall_seconds=result['elapsed_seconds'], refinement_accepted_moves=result['accepted_moves'],
            scan_complete=result['last_scan_complete'], local_certificate=result['local_optimal_up_to_1e_minus_9'],
            base_loss_hr=base['search_best_loss_hr'], refined_loss_hr=result['best_planning_loss_hr'],
            joint_budget=joint_budget, ga_joint_loss_hr=ga['search_best_loss_hr'],
            ga_prefix_replayed=100000, ga_additional_distinct=ga['actual_new_expensive'],
            ga_attempted_replay_included=ga['attempted_evaluations'],
            scope='continuation from same seeded search by deterministic cached-prefix replay; no new prefix physics calls',
            best_sequence=result['best_sequence'], sequence_sha256=result['sequence_sha256'])
        save(folder / 'JOINT_ACCOUNTING.json', rec)
        records.append(rec)
    save(OUT / 'REFINEMENT_MULTISEED_ACCOUNTING.json', dict(results=records, extra_loader_setup_scores=8))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('task', choices=['setup', 'screen', 'select', 'confirmation', 'refinement', 'preservation'])
    p.add_argument('--workers', type=int, default=12)
    a = p.parse_args()
    if a.task=='setup': setup()
    elif a.task in ('screen', 'confirmation'): batch(a.task, a.workers)
    elif a.task=='select': select()
    elif a.task=='refinement': refine_jobs()
    else:
        current = preservation()
        assert current==read(OUT / 'PRESERVATION_BASELINE.json')
        save(OUT / 'PRESERVATION_VERIFIED.json', dict(status='PASS', **current))
        print('PRESERVATION_PASS', len(current['files_sha256']), flush=True)


if __name__=='__main__':
    main()
