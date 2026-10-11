"""Execute the authorized, frozen prospective cohort; never optimize a policy."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np
import pandas as pd

from la_grid.diagnostics import independent_validation_20261010 as v
from la_grid.diagnostics.ga_research_preserve_20261009 import INPUTS, snapshot, git
from la_grid.diagnostics.ga_search_budget_sensitivity import identity
from la_grid.paths import REPO_ROOT

R = v.long_path(REPO_ROOT)
OUT = R / 'results/diagnostics/standalone_ils_prospective_validation_20261011'
ARCHIVE = OUT / 'cohort'
PARENT = '740f941f3614e51b15bcf6c91b3aff3afec9f2ea'
BRANCH = 'diagnostics/standalone-ils-prospective-validation-20261011'
PRIOR = R / 'results/diagnostics/standalone_ils_final_method_20261010'
N, BOOT, BOOT_SEED, SAMPLE_SEED = 2000, 20000, 2026110200, 2026110100
ILS, GA, IMPACT = 'standalone-ILS', 'formal-GA', 'Impact-first'
REQUEST = ('授权按冻结的前瞻性方案生成新的 2000 个独立物理实现，验证选定的 standalone ILS，'
           '与正式 GA 和 Impact-first 配对比较。不调参、不重选、不复用旧验证样本，'
           '保留原模型和正式策略不变；完成计算与分析后 commit 并 push。')
MODULE = 'src/la_grid/diagnostics/standalone_ils_validation_20261011.py'


def protected_state(revision, old_validation, source):
    result = snapshot(Path(revision))
    old = v.long_path(Path(old_validation) / 'results/diagnostics/independent_validation_ready_20261010')
    result['old_validation_sha256'] = {str(p.relative_to(old)).replace('\\', '/'): v.sha(p)
                                      for p in sorted(old.rglob('*')) if p.is_file()}
    parent = v.long_path(source)
    names = ['results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json',
             'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json']
    for p in (parent / 'results/diagnostics/standalone_ils_final_method_20261010').rglob('*'):
        if p.is_file():
            names.append(str(p.relative_to(parent)).replace('\\', '/'))
    result['frozen_source_package_sha256'] = {n: v.sha(parent / n) for n in sorted(set(names))}
    result['source_staged_diff_sha256'] = hashlib.sha256(git(Path(source), 'diff', '--cached', '--binary')).hexdigest()
    result['source_head'] = git(Path(source), 'rev-parse', 'HEAD').decode().strip()
    return result


def hydrate_exact(name, source, expected=None):
    """Restore frozen runtime bytes, with separate Git LF/CRLF provenance."""
    target, origin = R / name, v.long_path(Path(source) / name)
    blob = git(Path(source), 'show', PARENT + ':' + name)
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
        fields = dict(s.split(' ', 1) for s in blob.decode().splitlines())
        oid = fields['oid'][7:]
        common = Path(git(Path(source), 'rev-parse', '--git-common-dir').decode().strip())
        if not common.is_absolute():
            common = Path(source) / common
        obj = v.long_path(common / 'lfs/objects' / oid[:2] / oid[2:4] / oid)
        data = obj.read_bytes() if obj.exists() else origin.read_bytes()
        assert hashlib.sha256(data).hexdigest() == oid and len(data) == int(fields['size']), name
    else:
        data = origin.read_bytes()
        assert data.replace(b'\r\n', b'\n') == blob.replace(b'\r\n', b'\n'), name
    if expected is not None:
        assert hashlib.sha256(data).hexdigest() == expected, name
    if target.read_bytes() != data:
        target.write_bytes(data)
    return dict(path=name, runtime_sha256=v.sha(target), git_blob_sha256=hashlib.sha256(blob).hexdigest(),
                line_endings_equal=data == blob)


def setup(source, old_validation):
    assert git(REPO_ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    if (OUT / 'EXECUTION_FREEZE.json').exists():
        raise RuntimeError('Existing prospective freeze must not be overwritten')
    plan = v.read(PRIOR / 'FUTURE_VALIDATION_FREEZE.json')
    assert plan['sample_seed_reservation'] == SAMPLE_SEED and plan['proposed_samples'] == N
    assert plan['candidate_sha256'] == '17705a83a7607862d05ec9d6b607d58e31ff644712ceb0d0652ce7e59642499f'
    assert plan['prospective_evaluation_horizon_hr'] == v.H == 480
    original_freeze = v.read(R / 'results/diagnostics/independent_validation_ready_20261010/FINAL_VALIDATION_FREEZE_RECEIPT.json')
    revision = original_freeze['protected_revision_checkout']
    before = protected_state(revision, old_validation, source)
    if (OUT / 'PRESERVATION_BASELINE.json').exists():
        assert v.read(OUT / 'PRESERVATION_BASELINE.json') == before
    else:
        v.write(OUT / 'PRESERVATION_BASELINE.json', before)
    paths = dict(plan['model_hashes']['files_sha256'])
    for name, expected in original_freeze['input_sha256'].items():
        if name.startswith(('Data/', 'Formal_Experiment_', 'provenance/reviewer_working/', 'data/travel/')):
            paths[name] = expected
    for name in v.CODE:
        paths.setdefault(name, v.sha(Path(source) / name))
    paths['src/la_grid/diagnostics/standalone_ils_20261010.py'] = plan['optimizer_source_sha256']
    paths['src/la_grid/diagnostics/standalone_ils_analysis_20261010.py'] = plan['verification_source_sha256']
    hydration = [hydrate_exact(name, source, expected) for name, expected in paths.items()]
    model = v.load_model()
    assert model['context_hashes'] == plan['model_hashes']['context_identity']
    sampling = v.sampling_audit(model['frozen'], Path(revision))
    sampling['rng_specification'] = 'PCG64 / default_rng(SeedSequence([2026110100,r])), r=0..1999'
    v.write(OUT / 'SAMPLING_SOURCE_AUDIT.json', sampling)
    selected = v.read(PRIOR / 'SELECTED_STANDALONE_ILS_CANDIDATE.json')
    formal = v.read(R / 'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json')
    rules = v.read(R / 'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json')
    strategies = [dict(strategy=ILS, sequence=selected['sequence']),
                  dict(strategy=GA, sequence=formal['sequence']),
                  dict(strategy=IMPACT, sequence=rules['2pc50']['impact-first'])]
    for p in strategies:
        assert len(p['sequence']) == len(set(p['sequence'])) == 92 and set(p['sequence']) == set(model['ids'])
        p['sequence_sha256'] = identity(p['sequence'])
    assert strategies[0]['sequence'] == plan['candidate_sequence']
    assert strategies[0]['sequence_sha256'] == plan['candidate_sha256']
    assert strategies[1]['sequence_sha256'] == '8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab'
    assert strategies[2]['sequence_sha256'] == plan['model_hashes']['impact_sha256']
    prior_hashes = {name: h for name, h in model['frozen']['sample_hashes'].items()
                    if name.startswith('2pc50__')}
    assert len(prior_hashes) == 1064
    for split, (ds, duration) in model['banks'].items():
        for i in range(len(ds)):
            assert v.physical_hash(model['ids'], ds[i], duration[i]) == prior_hashes[f'2pc50__{split}_{i:04d}']
    old_root = v.long_path(Path(old_validation) / 'results/diagnostics/independent_validation_ready_20261010/authorized_validation/fixed_2000_20261010/physical')
    old_receipts = sorted(old_root.glob('*/DRAW.json'))
    assert len(old_receipts) == 2000
    entropy, old_hashes = [], []
    for path in old_receipts:
        record = v.read(path)
        old_hashes.append(record['physical_sha256'])
        entropy.append(record['entropy'])
        assert record['entropy'][0] != SAMPLE_SEED
    assert len(set(old_hashes)) == 2000
    prior_hashes.update({f'previous_validation_{i:04d}': h for i, h in enumerate(old_hashes)})
    assert len(set(prior_hashes.values())) == 3064
    v.write(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json', prior_hashes)
    ledger = dict(status='PASS_NO_PRIOR_USE', existing_old_validation_entropy_prefix=entropy[0][:-1],
                  original_physical_ids=1064, old_validation_ids=2000,
                  reserved_seed=SAMPLE_SEED, entropy_rule=[SAMPLE_SEED, 'r'],
                  namespace=plan['sampling_namespace'], validation_outcomes_read=False,
                  new_physical_draws=0, prior_raw_physical_receipts_read_only_for_identity=True)
    v.write(OUT / 'SEED_AND_NAMESPACE_AUDIT.json', ledger)
    assert shutil.disk_usage(REPO_ROOT).free > 4_000_000_000
    code = {name: v.sha(R / name) for name in (*v.CODE, MODULE)}
    freeze = dict(status='AUTHORIZED_PROTOCOL_FROZEN_BEFORE_SAMPLING', parent_commit=PARENT,
                  source_checkout=str(source), old_validation_checkout=str(old_validation),
                  protected_revision_checkout=revision, prospective_plan_sha256=v.sha(PRIOR / 'FUTURE_VALIDATION_FREEZE.json'),
                  prospective_plan=plan, strategies=strategies, input_sha256=paths, code_sha256=code,
                  hydration=hydration, runtime=v.runtime(), sample_size=N, entropy_rule=[SAMPLE_SEED, 'r'],
                  sampling_namespace=plan['sampling_namespace'], bootstrap_seed=BOOT_SEED,
                  bootstrap_resamples=BOOT, gate_threshold=.5, horizon_hr=v.H,
                  previous_registry_sha256=v.sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json'),
                  optimizer_invocations=0, allow_reselection=False, allow_tuning=False,
                  workers=8, new_validation_samples_generated=0)
    v.write(OUT / 'EXECUTION_FREEZE.json', freeze)
    v.write(OUT / 'AUTHORIZATION.json', dict(author='human user in this chat', client_date='2026-10-11',
                  authorization_recorded_utc=datetime.now(timezone.utc).isoformat(), verbatim_request=REQUEST,
                  authorization_type='EXPLICIT_FIXED_2000_STANDALONE_ILS_VALIDATION',
                  execution_freeze_sha256=v.sha(OUT / 'EXECUTION_FREEZE.json'), sample_size=N,
                  allow_reselection=False, allow_tuning=False, allow_formal_replacement=False))
    print('PROSPECTIVE_SETUP_PASS; no new physical draws; registry=3064', flush=True)


def verify():
    f = v.read(OUT / 'EXECUTION_FREEZE.json')
    auth = v.read(OUT / 'AUTHORIZATION.json')
    assert auth['sample_size'] == N and auth['verbatim_request'] == REQUEST
    assert auth['execution_freeze_sha256'] == v.sha(OUT / 'EXECUTION_FREEZE.json')
    assert not auth['allow_reselection'] and not auth['allow_tuning'] and not auth['allow_formal_replacement']
    assert f['runtime'] == v.runtime()
    for name, h in {**f['input_sha256'], **f['code_sha256']}.items():
        assert v.sha(R / name) == h, name
    assert v.sha(PRIOR / 'FUTURE_VALIDATION_FREEZE.json') == f['prospective_plan_sha256']
    assert v.sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json') == f['previous_registry_sha256']
    assert git(REPO_ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    return f


def draw_once(model, folder, r, previous, generated):
    folder = v.long_path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    marker, target = folder / 'DRAW_STARTED.json', folder / 'DRAW.json'
    freeze_hash = v.sha(OUT / 'EXECUTION_FREEZE.json')
    if target.exists():
        record = v.read(target)
        assert record['r'] == r and record['entropy'] == [SAMPLE_SEED, r]
        assert record['freeze_sha256'] == freeze_hash and record['station_ids'] == model['ids']
        expected = record.pop('payload_sha256')
        assert hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest() == expected
        record['payload_sha256'] = expected
        ds, duration = np.array(record['damage_state'], np.int64), np.array(record['duration_hr'], float)
        assert v.physical_hash(model['ids'], ds, duration) == record['physical_sha256']
        v.check_overlap(model['ids'], ds, duration, previous, generated)
        return record
    if marker.exists():
        raise RuntimeError('Uncommitted physical draw: stop for review, never redraw')
    v.write(marker, dict(r=r, entropy=[SAMPLE_SEED, r], freeze_sha256=freeze_hash))
    rng = np.random.default_rng(np.random.SeedSequence([SAMPLE_SEED, r]))
    before = rng.bit_generator.state
    ds = v.core.sample_damage_states(model['devices']['pga_2pc50'], model['devices'], 1, rng)
    _, duration = v.core.damage_to_functionality_and_repair(ds, rng, model['cfg'])
    ds, duration = ds[:, 0], duration[:, 0]
    assert ds.shape == duration.shape == (92,)
    assert np.isfinite(duration).all() and (duration >= 0).all() and ((ds >= 0) & (ds <= 4)).all()
    h = v.check_overlap(model['ids'], ds, duration, previous, generated)
    record = dict(r=r, entropy=[SAMPLE_SEED, r], namespace=verify_namespace(), station_ids=model['ids'],
                  damage_state=ds.tolist(), duration_hr=duration.tolist(), rng_before=before,
                  rng_after=rng.bit_generator.state, physical_sha256=h, freeze_sha256=freeze_hash,
                  damage_sha256=hashlib.sha256(ds.astype('<i8').tobytes()).hexdigest(),
                  duration_sha256=hashlib.sha256(duration.astype('<f8').tobytes()).hexdigest())
    record['payload_sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    v.write(target, record)
    return record


def verify_namespace():
    return v.read(OUT / 'EXECUTION_FREEZE.json')['sampling_namespace']


def evaluate_case(model, policies, folder, r, *, interrupt_after=None):
    folder = v.long_path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    physical = v.read(ARCHIVE / 'physical' / f'{r:04d}' / 'DRAW.json')
    key = dict(r=r, physical_sha256=physical['physical_sha256'], freeze_sha256=v.sha(OUT / 'EXECUTION_FREEZE.json'))
    done = folder / 'COMPLETE.json'
    if done.exists():
        record = v.read(done)
        assert record['identity'] == key and record['policy_count'] == 3
        for name, h in record['files_sha256'].items():
            assert v.sha(folder / name) == h, name
        return dict(r=r, resumed_complete=True, seconds=0, production_calls=0, independent_kernel_calls=0)
    ds, duration = np.array(physical['damage_state'], np.int64), np.array(physical['duration_hr'], float)
    assert v.physical_hash(model['ids'], ds, duration) == key['physical_sha256']
    tick = time.perf_counter()
    summaries, tasks, times, lengths, arrays, tract, station = [], [], [], [], {}, [], []
    for i, policy in enumerate(policies):
        summary, events, clock, trace, tracts, stations, finish = v.evaluate(
            model, policy, ds, duration, f'2pc50__standalone_prospective_{r:04d}')
        component = sum(summary[k] for k in ('L_self_population_mass_weighted_hr',
                        'L_threshold_population_mass_weighted_hr', 'L_source_population_mass_weighted_hr'))
        assert abs(component - summary[v.PRIMARY]) < 1e-8
        assert len(events) == int((ds > 0).sum()) and events.task_id.nunique() == len(events)
        assert np.allclose(trace['L_total'], trace['L_self'] + trace['L_threshold'] + trace['L_source'], atol=1e-12)
        summaries.append(summary); tasks.append(events); times.append(clock); lengths.append(len(clock))
        tract.append(tracts['normalized_burden_hr'])
        station.append(np.array([stations[k] for k in ('L_self', 'L_threshold', 'L_source', 'L_total')]))
        for name, value in trace.items():
            arrays.setdefault(name, []).append(value)
        if interrupt_after == i:
            raise InterruptedError('Engineering interruption after saved physical draw')
    v.csv(folder / 'SUMMARY.csv', pd.DataFrame(summaries))
    v.csv(folder / 'TASK_EXECUTION.csv', pd.concat(tasks, ignore_index=True))
    v.npz(folder / 'TRAJECTORIES.npz', station_ids=np.array(model['ids']), tract_ids=model['mapping'].tract_ids,
          policies=np.array([p['strategy'] for p in policies]), event_lengths=np.array(lengths),
          event_time_hr=np.concatenate(times), tract_normalized_loss_hr=np.array(tract),
          station_component_integrals_hr=np.array(station), **{k: np.concatenate(a) for k, a in arrays.items()})
    v.write(done, dict(status='COMPLETE_SHARED_REALIZATION', identity=key, policy_count=3,
                      files_sha256={name: v.sha(folder / name) for name in ('SUMMARY.csv', 'TASK_EXECUTION.csv', 'TRAJECTORIES.npz')},
                      evaluation_seconds=time.perf_counter()-tick))
    return dict(r=r, resumed_complete=False, seconds=time.perf_counter()-tick,
                production_calls=3, independent_kernel_calls=3)


def worker_setup():
    global MODEL, POLICIES
    MODEL = v.load_model()
    POLICIES = verify()['strategies']


def worker(r):
    return evaluate_case(MODEL, POLICIES, ARCHIVE / 'cases' / f'{r:04d}', r)


def execute():
    freeze = verify()
    assert v.read(OUT / 'ENGINEERING_QA.json')['status'] == 'PASS'
    assert (OUT / 'PREREGISTRATION_COMMIT.json').exists()
    assert shutil.disk_usage(REPO_ROOT).free > 4_000_000_000
    assert protected_state(freeze['protected_revision_checkout'], freeze['old_validation_checkout'],
                           freeze['source_checkout']) == v.read(OUT / 'PRESERVATION_BASELINE.json')
    if (OUT / 'COHORT_COMPLETED.json').exists():
        raise RuntimeError('Completed fixed cohort must not be generated or evaluated again')
    with v.exclusive(ARCHIVE):
        previous = set(v.read(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json').values())
        model, generated, tick = v.load_model(), set(), time.perf_counter()
        for r in range(N):
            record = draw_once(model, ARCHIVE / 'physical' / f'{r:04d}', r, previous, generated)
            generated.add(record['physical_sha256'])
            if (r + 1) % 250 == 0:
                print('PHYSICAL_DRAW_SAVED', r+1, '/', N, '; no outcome analysis', flush=True)
        assert len(generated) == N and not generated & previous
        draw_seconds = time.perf_counter() - tick
        v.write(OUT / 'COHORT_FROZEN.json', dict(status='ALL2000_SAVED_BEFORE_EVALUATION', sample_count=N,
                    unique_physical_hashes=N, prior_overlap=0, draw_wall_seconds=draw_seconds,
                    draw_receipts_sha256={str(r): v.sha(ARCHIVE / 'physical' / f'{r:04d}' / 'DRAW.json') for r in range(N)}))
        tick, results = time.perf_counter(), []
        with ProcessPoolExecutor(max_workers=freeze['workers'], initializer=worker_setup) as pool:
            futures = {pool.submit(worker, r): r for r in range(N)}
            for future in as_completed(futures):
                results.append(future.result())
                if len(results) % 100 == 0:
                    print('FIXED_PAIRED_CASES_COMPLETE', len(results), '/', N, '; no interim effects', flush=True)
        v.write(OUT / 'EXECUTION_ACCOUNTING.json', dict(sample_count=N, genuine_physical_sampling_calls=N,
                    repair_sampler_calls=N, optimizer_calls=0, policy_count=3,
                    production_evaluations=sum(x['production_calls'] for x in results),
                    independent_kernel_evaluations=sum(x['independent_kernel_calls'] for x in results),
                    resumed_complete_cases=sum(x['resumed_complete'] for x in results),
                    draw_wall_seconds=draw_seconds, evaluation_batch_wall_seconds=time.perf_counter()-tick,
                    sum_case_evaluation_wall_seconds=sum(x['seconds'] for x in results),
                    negative_results_retained=True, failed_cases=0, case_accounting=sorted(results, key=lambda x:x['r'])))
        v.write(OUT / 'COHORT_COMPLETED.json', dict(status='ALL2000_FIXED_3_POLICY_CASES_COMPLETE', sample_count=N,
                    policy_records=6000, exact_prior_overlap=0, optimizer_calls=0,
                    freeze_sha256=v.sha(OUT / 'EXECUTION_FREEZE.json')))
    print('ALL2000_COMPLETE; now authorized for frozen final analysis', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['setup', 'verify', 'execute'])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--old-validation', type=Path)
    args = parser.parse_args()
    if args.phase == 'setup':
        setup(args.source, args.old_validation)
    elif args.phase == 'verify':
        verify(); print('EXECUTION_FREEZE_PASS; no draws', flush=True)
    else:
        execute()


if __name__ == '__main__':
    main()
