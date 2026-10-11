"""Isolated initialization experiment; no production-source or physics edits."""
from __future__ import annotations

import argparse
import ast
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
import sys
import time
import types

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
START = 'f9734afa09bd0a0e59b2b1d81d43599062d4c258'
BRANCH = 'diagnostics/ga-random-initialization-isolation-20261011'
MAIN = list(range(2026103100, 2026103120))
RESERVE = MAIN[:10]
SMOKE = [2026103000, 2026103001]
MODES = ['PURE_RANDOM_GA', 'IMPACT_SEEDED_GA']
CHECKPOINTS = [20000, 50000, 100000, 250000, 500000]
MARGIN = .001  # 3.6 equivalent full-service seconds; defined before main data.
FROZEN = 32.997840773882714
IMPACT_REF = 33.57830255999924


def lp(path):
    path = Path(path).resolve()
    return Path('\\\\?\\' + str(path)) if os.name == 'nt' and not str(path).startswith('\\\\?\\') else path


def digest(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as f:
        for block in iter(lambda: f.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(lp(path).read_text(encoding='utf-8-sig'))


def save(path, obj):
    import numpy as np
    def clean(v):
        if isinstance(v, dict): return {k: clean(x) for k, x in v.items()}
        if isinstance(v, (tuple, list)): return [clean(x) for x in v]
        if isinstance(v, np.generic): v = v.item()
        if isinstance(v, float) and not np.isfinite(v): return None
        return v
    path = lp(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(obj), indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def git(*args, root=ROOT):
    return subprocess.check_output(['git', '-c', 'filter.lfs.process=', '-c',
        'filter.lfs.required=false', *args], cwd=root)


def identity(seq):
    return hashlib.sha256(('\n'.join(seq)+'\n').encode()).hexdigest()


def hydrate(path):
    path = lp(path)
    with path.open('rb') as f: data = f.read(200)
    if not data.startswith(b'version https://git-lfs.github.com/spec/v1'): return
    fields = dict(s.split(' ', 1) for s in data.decode().splitlines())
    oid = fields['oid'][7:]
    common = Path(git('rev-parse', '--git-common-dir').decode().strip()).resolve()
    source = lp(common / 'lfs/objects' / oid[:2] / oid[2:4] / oid)
    assert digest(source) == oid and source.stat().st_size == int(fields['size'])
    path.write_bytes(source.read_bytes())


def load_model():
    # Reuse only the verified planning loader; no ILS search is imported into the experiment.
    from la_grid.diagnostics.standalone_ils_20261010 import load_model as planning_loader
    return planning_loader()


def config():
    from la_grid.diagnostics.ga_variant_engine import Variant
    return Variant(population=100, crossover=.8, mutation=.1, tournament=3,
        elites=1, initialization='paired_random_pool', mutation_operator='swap',
        crossover_operator='ordered', adaptive=False, restart=False, diversity_replacement=False)


def engine(mode, impact, capture):
    """Compile a private AST copy; change only the zero-incumbent guard/initializer."""
    from la_grid.diagnostics import ga_variant_engine as original
    tree = ast.parse(Path(original.__file__).read_text(encoding='utf-8'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_search')
    loop = next(n for n in fn.body if isinstance(n, ast.While))
    block = loop.body[0]
    assert ast.unparse(block.test) == "state['phase'] == 'incumbents'"
    ranking = next(i for i, n in enumerate(block.body)
                   if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'ranked')
    assert len(block.body[ranking:ranking+4]) == 4
    assert 'ranked[0]' in ast.unparse(block.body[ranking+1])
    block.body[ranking:ranking+4] = [ast.If(test=ast.Name(id='inc', ctx=ast.Load()),
        body=block.body[ranking:ranking+4], orelse=[])]
    module = types.ModuleType('private_ga_init_engine')
    module.__dict__['__file__'] = original.__file__
    sys.modules[module.__name__] = module
    exec(compile(ast.fix_missing_locations(tree), original.__file__, 'exec'), module.__dict__)
    def initializer(domain, inc, rng, cfg, quality):
        assert not inc and quality is None
        pool = [tuple(rng.sample(domain, len(domain))) for _ in range(100)]
        assert all(len(x) == len(set(x)) == 92 for x in pool)
        pop = pool.copy()
        if mode == 'IMPACT_SEEDED_GA': pop[0] = tuple(impact)
        capture.update(mode=mode, replacement_position=0, archive_before_first_evaluation=[],
            common_random_pool=[list(x) for x in pool], random_pool_hashes=[identity(x) for x in pool],
            initial_sequences=[list(x) for x in pop], initial_hashes=[identity(x) for x in pop],
            post_initializer_rng_sha256=hashlib.sha256(pickle.dumps(rng.getstate(), protocol=5)).hexdigest())
        return pop
    module.initialize = initializer
    return module


def preservation():
    from la_grid.diagnostics.ga_research_preserve_20261009 import snapshot
    revision = Path(read(ROOT / 'results/diagnostics/independent_validation_ready_20261010/FINAL_VALIDATION_FREEZE_RECEIPT.json')['protected_revision_checkout'])
    data = snapshot(revision)
    entries = git('ls-files', '--stage', '-z', root=revision)
    changed = git('diff', '--cached', '--name-only', '-z', root=revision).split(b'\0')
    data['index_entries_sha256'] = hashlib.sha256(entries).hexdigest()
    data['staged_count'] = len([x for x in changed if x])
    data['status_sha256'] = hashlib.sha256(git('status', '--porcelain=v1', '-z', root=revision)).hexdigest()
    protected = ['src/la_grid/diagnostics/ga_variant_engine.py',
        'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json',
        'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json']
    data['isolated_formal_sources_sha256'] = {p: digest(ROOT/p) for p in protected}
    return data


def setup():
    assert not lp(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json').exists()
    # Hydrate only source code and required planning inputs from verified shared objects.
    for p in lp(ROOT/'src').rglob('*.py'): hydrate(p)
    from la_grid.diagnostics.ga_research_preserve_20261009 import INPUTS
    for name in list(INPUTS) + ['Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz']:
        hydrate(ROOT/name)
    k, impact, model = load_model()
    save(OUT/'PRESERVATION_BASELINE.json', preservation())
    historical = []
    for folder in ['ga_ils_parameter_defense_20261010', 'standalone_ils_final_method_20261010',
                   'ga_initialization_reconciliation_20261009']:
        for p in lp(ROOT/'results/diagnostics'/folder).glob('*RESULTS.csv'):
            hydrate(p)
            import pandas as pd
            df = pd.read_csv(p)
            if 'seed' in df: historical += df.seed.dropna().astype(int).tolist()
    assert not set(MAIN+SMOKE) & set(historical)
    files = model['files_sha256'] | {str(p.relative_to(ROOT)).replace('\\','/'): digest(p) for p in
        [ROOT/'src/la_grid/diagnostics/ga_variant_engine.py', ROOT/'src/la_grid/diagnostics/standalone_ils_20261010.py', Path(__file__)]}
    design = dict(starting_commit=START, branch=BRANCH, main_seeds=MAIN, reserved_extension_seeds=RESERVE,
        engineering_seeds=SMOKE, engineering_budget=1000, main_budget=100000,
        conditional_extension_budgets=[250000,500000], checkpoints=CHECKPOINTS,
        modes=MODES, fixed_ga=asdict(config()), shared_pool_size=100, seeded_replacement_position=0,
        initial_archive='empty in BOTH; first actual evaluated population establishes archive',
        no_incumbent_prescoring=True, independent_run_caches=True, bootstrap_replicates=20000,
        bootstrap_seed=2026103200, simultaneous_family_size=5,
        practical_margin_hr=MARGIN,
        margin_justification='0.001 equivalent full-service hours = 3.6 seconds of normalized population deficit; ~0.003% of 33h planning loss. A strict prospective numerical engineering tolerance, not a validated policy-benefit threshold or physical accuracy claim.',
        high_quality_rule='J <= frozen selected J + 0.001 h; report exact wins separately',
        reliability_rule='>=18 of 20 runs meet high_quality_rule; descriptive repeated-search rate, not population-level reliability guarantee',
        extension_rule='Extend first ten same trajectories if 100k simultaneous paired mean interval is not wholly inside +/-0.001h OR pure random fails 18/20 high-quality rule. Continue to both250k and500k even if250k resolves question; no selective stop.',
        selection_rule='Prefer pure random only if final simultaneous interval wholly inside margin, >=90% tested runs high-quality, and no consequential cost disadvantage (>25% median wall/attempt ratio); otherwise recommend Impact-seeded as reproducible independently executable reference, qualifying unresolved superiority.',
        tie_tolerance_hr=1e-9, source_hashes=files, model_identity=model,
        physical_samples_generated=0, validation_outcomes_loaded=False, formal_replacement=False,
        historical_seed_overlap=False, workers=12, important_sequence_rule='best and median-final-loss run in each mode, main100k plus reserve500k if executed; complete64-state production parity',
        python=platform.python_version(), numpy_version=__import__('numpy').__version__)
    save(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json', design)
    print('DESIGN_SAVED', len(k.ids), len(model['planning_sample_hashes']), flush=True)


def run_engine(mode, seed, budget, folder, objective, ids, impact, checkpoints=CHECKPOINTS):
    captured = {}
    eng = engine(mode, impact, captured)
    result = eng.run_search(items=ids, incumbents={}, objective=objective, seed=seed, config=config(),
        max_evaluations=budget, checkpoints=checkpoints, folder=lp(folder), quality=None)
    if captured:
        save(folder/'INITIAL_POPULATION.json', captured)
    return result


def read_state(folder):
    with gzip.open(lp(folder/'CHECKPOINT.pkl.gz'), 'rb') as f: return pickle.load(f)


def smoke():
    import numpy as np
    k, impact, model = load_model()
    from la_grid.diagnostics.standalone_ils_analysis_20261010 import production
    from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
    from la_grid.revision.r1_equity_amendment_execute import execution_context
    context, _, _ = execution_context(k.ids)
    rows = []
    for seed in SMOKE:
        for mode in MODES:
            folder = OUT/'engineering'/f'{mode}_{seed}'
            prefix = run_engine(mode,seed,333,folder,k.score,k.ids,impact,checkpoints=(333,1000))
            continued = run_engine(mode,seed,1000,folder,k.score,k.ids,impact,checkpoints=(333,1000))
            whole = run_engine(mode,seed,1000,OUT/'engineering'/f'whole_{mode}_{seed}',k.score,k.ids,impact,checkpoints=(333,1000))
            a, b = read_state(folder), read_state(OUT/'engineering'/f'whole_{mode}_{seed}')
            assert a['rng'] == b['rng'] and a['cache'] == b['cache']
            for field in ['population','scores','next_index','phase','generation','attempts','best_seq','best_seen','archive_seq']:
                assert a['state'][field] == b['state'][field], field
            assert list(a['cache']) == list(b['cache']) and len(a['cache']) == 1000
            assert a['state']['expensive_calls'] == 1000 and a['state']['lookup_calls'] == 0
            assert a['state']['restart_count'] == 0
            assert all(len(key) == len(set(key)) == 92 for key in a['cache'])
            init = read(folder/'INITIAL_POPULATION.json')
            assert init['archive_before_first_evaluation'] == []
            expected_first = init['initial_sequences'][0]
            assert continued['moves'][0]['sequence'] == expected_first if 'moves' in continued else a['moves'][0]['sequence'] == expected_first
            exact = per_sample(k, continued['best_sequence'])
            errors = [abs(production(k,context,continued['best_sequence'],i)-exact[i]) for i in [0,15,63]]
            assert max(errors) < 1e-8
            rows.append(dict(seed=seed,mode=mode,distinct=1000,checkpoint_restart_exact=True,
                max_production_error_hr=max(errors), initial_first_best_sha256=identity(expected_first)))
        aa = read(OUT/'engineering'/f'{MODES[0]}_{seed}'/'INITIAL_POPULATION.json')
        bb = read(OUT/'engineering'/f'{MODES[1]}_{seed}'/'INITIAL_POPULATION.json')
        assert aa['common_random_pool'] == bb['common_random_pool']
        assert aa['post_initializer_rng_sha256'] == bb['post_initializer_rng_sha256']
        assert aa['initial_sequences'][1:] == bb['initial_sequences'][1:]
        assert aa['initial_sequences'] == aa['common_random_pool']
        assert bb['initial_sequences'][0] == list(impact)
    # Unmodified engine reproduction parity: cached synthetic92 objective avoids further physical scoring.
    from la_grid.diagnostics import ga_variant_engine as orig
    cfg = replace(config(), initialization='legacy')
    def dummy(seq): return -sum((i+1)*int(s[-3:]) for i,s in enumerate(seq))
    ref = orig.run_search(items=k.ids,incumbents={'impact-first':impact},objective=dummy,
        seed=SMOKE[0],config=cfg,max_evaluations=1000,folder=None,checkpoints=(1000,))
    private = engine(MODES[0],impact,{})
    private.initialize = orig.initialize
    replay = private.run_search(items=k.ids,incumbents={'impact-first':impact},objective=dummy,
        seed=SMOKE[0],config=cfg,max_evaluations=1000,folder=None,checkpoints=(1000,))
    assert ref['cache'] == replay['cache'] and ref['best_sequence'] == replay['best_sequence']
    assert ref['state']['attempts'] == replay['state']['attempts']
    save(OUT/'ENGINEERING_QA.json', dict(status='PASS',rows=rows, reproduction_trace_parity=True,
        original_engine_sha256=digest(ROOT/'src/la_grid/diagnostics/ga_variant_engine.py'),
        physical_objective_calls=4*2000, compiled_sample_calls=4*64, production_sample_calls=12,
        source_identity=model, all_shared99_and_rng_checks=True))
    print('ENGINEERING_PASS', flush=True)


def worker_init():
    global KERNEL, IMPACT, MODEL, SETUP_TIME
    tick = time.perf_counter()
    KERNEL, IMPACT, MODEL = load_model()
    assert abs(-KERNEL.score(IMPACT)-IMPACT_REF) < 1e-8
    SETUP_TIME = time.perf_counter()-tick


def job(args):
    mode, seed, budgets = args
    folder = OUT/'runs'/f'{mode}_{seed}'
    final_path = folder/f'FINAL_{budgets[-1]}.json'
    if lp(final_path).exists(): return read(final_path)
    commit = git('rev-parse','HEAD').decode().strip()
    receipts = []
    for budget in budgets:
        receipt_path = folder/f'FINAL_{budget}.json'
        if lp(receipt_path).exists(): receipts.append(read(receipt_path)); continue
        cpu = time.process_time()
        r = run_engine(mode,seed,budget,folder,KERNEL.score,KERNEL.ids,IMPACT)
        s = r['state']
        assert len(r['cache']) == s['expensive_calls'] == budget and s['lookup_calls'] == 0
        initial = r['history'].iloc[0]
        init = read(folder/'INITIAL_POPULATION.json')
        row = dict(mode=mode,seed=seed,budget=budget,loss_hr=-r['best_fitness'],
            sequence=list(r['best_sequence']),sequence_sha256=identity(r['best_sequence']),
            initial_best_loss_hr=initial.population_best_service_loss_hr,
            initial_mean_loss_hr=initial.population_mean_service_loss_hr,
            initial_unique=int(initial.unique_population), initial_diversity=initial.position_entropy,
            ga_generated_gain_hr=float(initial.population_best_service_loss_hr+r['best_fitness']),
            gain_vs_impact_hr=IMPACT_REF+r['best_fitness'],
            distinct_evaluations=len(r['cache']), attempts=s['attempts'],duplicate_fraction=1-len(r['cache'])/s['attempts'],
            completed_generations=int(r['history'].generation.max()), generation=s['generation'],
            wall_seconds=r['elapsed_seconds'],objective_seconds=s['score_seconds'],
            incremental_cpu_seconds=time.process_time()-cpu, last_improvement_evaluations=s['last_improvement_evaluations'],
            completed=True,initial_population_sha256=digest(folder/'INITIAL_POPULATION.json'),
            post_initializer_rng_sha256=init['post_initializer_rng_sha256'],
            checkpoint_sha256=digest(folder/'CHECKPOINT.pkl.gz'), execution_commit=commit,
            model_identity=MODEL, implementation_sha256=digest(__file__), fixed_config=asdict(config()),
            worker_pid=os.getpid(), worker_setup_seconds=SETUP_TIME, worker_setup_objective_calls=1)
        save(receipt_path,row)
        # Preserve exact boundary checkpoint instead of overwriting the sole continuation evidence.
        from shutil import copyfile
        copyfile(lp(folder/'CHECKPOINT.pkl.gz'), lp(folder/f'STATE_{budget}.pkl.gz'))
        receipts.append(row)
        print('COMPLETE',mode,seed,budget,row['loss_hr'], flush=True)
    return receipts[-1]


def batch(extension=False):
    assert read(OUT/'ENGINEERING_QA.json')['status'] == 'PASS'
    assert read(OUT/'PREREGISTRATION_COMMIT.json')['design_sha256'] == digest(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    if extension:
        assert read(OUT/'EXTENSION_DECISION.json')['extend']
        jobs = [(mode,seed,[250000,500000]) for seed in RESERVE for mode in MODES]
    else: jobs = [(mode,seed,[100000]) for seed in MAIN for mode in MODES]
    tick = time.perf_counter()
    done, failures = [], []
    with ProcessPoolExecutor(max_workers=12, initializer=worker_init) as pool:
        pending = {pool.submit(job,j):j for j in jobs}
        for f in as_completed(pending):
            try: done.append(f.result())
            except Exception as e:
                failures.append(dict(job=pending[f],error=repr(e)))
                save(OUT/'EXECUTION_FAILURES.json',failures)
    save(OUT/('EXTENSION_EXECUTION.json' if extension else 'MAIN_EXECUTION.json'), dict(
        all_completed=len(done)==len(jobs), jobs=len(jobs), failures=failures,
        batch_wall_seconds=time.perf_counter()-tick,
        final_rows=[{k:r[k] for k in ['mode','seed','budget','loss_hr','distinct_evaluations']} for r in done],
        worker_setup_calls=sum(1 for _ in {r['worker_pid'] for r in done})))
    assert not failures


def main():
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['setup','smoke','main','extension','register','verify'])
    a = p.parse_args()
    if a.phase == 'setup': setup()
    elif a.phase == 'smoke': smoke()
    elif a.phase == 'main': batch()
    elif a.phase == 'extension': batch(True)
    elif a.phase == 'register':
        assert git('show','HEAD:'+str((OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json').relative_to(ROOT)).replace('\\','/')) == lp(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json').read_bytes()
        save(OUT/'PREREGISTRATION_COMMIT.json', dict(commit=git('rev-parse','HEAD').decode().strip(),
            design_sha256=digest(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json'), implementation_sha256=digest(__file__)))
    else:
        before=read(OUT/'PRESERVATION_BASELINE.json'); after=preservation()
        assert before == after
        design=read(OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
        assert all(digest(ROOT/p)==h for p,h in design['source_hashes'].items())
        save(OUT/'REPRODUCIBILITY_AND_PRESERVATION_QA.json',dict(status='PASS',before=before,after=after,
            protected_files=len(after['files_sha256']),original_staged_count=after['staged_count'],
            all_frozen_sources_unchanged=True, no_new_physical_samples=True,no_formal_replacement=True,
            validation_outcomes_loaded=False))
        print('PRESERVATION_PASS',len(after['files_sha256']),after['staged_count'],flush=True)


if __name__ == '__main__': main()
