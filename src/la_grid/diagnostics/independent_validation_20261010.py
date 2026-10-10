"""Frozen, authorization-gated independent validation; preparation draws nothing."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import networkx as nx
import numba
import numpy as np
import pandas as pd
import scipy

from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics.ga_research_preserve_20261009 import git, snapshot, INPUTS
from la_grid.diagnostics.ga_search_budget_sensitivity import identity
from la_grid.diagnostics.ga_actionable_delay_20261010 import completion_loss
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import (
    execute_realization_schedule, evaluate_completion_step_functionality, INITIAL_BY_DS,
)
from la_grid.revision.r1_source_gate import evaluate_source_gate
from la_grid.revision.formal.offline import PreparedMapping, evaluate_exact_event_arrays
from la_grid.core import C257H_Project_Main as core
from la_grid.core.legacy_entrypoints.C257H_Project_Main_expanded import ExpandedConfig

START = '950aff2291da0b92478f402881a50c0d73173a74'
BRANCH = 'diagnostics/independent-validation-ready-20261010'
OUT = R / 'results/diagnostics/independent_validation_ready_20261010'
FORMAL = R / 'Formal_Experiment_20260923'
OLD = R / 'results/diagnostics/final_ga_method_20261009'
ADDENDUM = R / 'results/diagnostics/ga_noncontiguous_connectivity_lns_20261010/VALIDATION_COMPARATORS_ADDENDUM.json'
PRIMARY = 'population_weighted_normalized_burden_hr'
GA = 'ga-final-method-candidate'
ILS = 'refined-ils-secondary-diagnostic'
H = 480.
N = 2000
BOOT = 20000
BOOT_SEED = 2026100901
SAMPLERS = ('sample_damage_states', 'damage_to_functionality_and_repair', 'draw_positive_normal')
PHYSICAL = 'Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_2pc50.npz'
META = 'provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv'
EXTRA_INPUTS = (PHYSICAL, META, 'Data/working_area_substations_with_fragility.csv',
    'Data/Substations_PGA_IDW_CEC_expanded.csv')
METRICS = (PRIMARY, 'burden_Q1_hr', 'burden_Q2_hr', 'burden_Q3_hr', 'burden_Q4_hr',
    'signed_Q4_minus_Q1_hr', 'absolute_Q4_minus_Q1_hr', 'burden_gini',
    'hospital_mean_normalized_burden_hr', 'L_self_population_mass_weighted_hr',
    'L_threshold_population_mass_weighted_hr', 'L_source_population_mass_weighted_hr',
    'T80_restricted_hr', 'T80_censored', 'effective_service_at_480',
    'total_travel_hr', 'makespan_hr')
CODE = ('src/la_grid/diagnostics/independent_validation_20261010.py',
    'src/la_grid/diagnostics/independent_validation_qa_20261010.py',
    'src/la_grid/diagnostics/ga_actionable_delay_20261010.py',
    'src/la_grid/diagnostics/ga_connectivity_lns_local_20261010.py',
    'src/la_grid/core/C257H_Project_Main.py',
    'src/la_grid/core/legacy_entrypoints/C257H_Project_Main_expanded.py',
    'src/la_grid/revision/r1_realization_scheduling.py',
    'src/la_grid/revision/r1_source_gate.py', 'src/la_grid/revision/formal/offline.py',
    'src/la_grid/revision/formal/schedule.py', 'src/la_grid/revision/r1_equity_amendment_execute.py')


def long_path(path):
    """Idempotent Windows long-path adapter, including already-prefixed children."""
    path = Path(path)
    if os.name=='nt' and not str(path).startswith('\\\\?\\'):
        return Path('\\\\?\\'+str(path.resolve()))
    return path


def sha(path):
    return hashlib.sha256(long_path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(long_path(path).read_text(encoding='utf-8'))


def write(path, data):
    """Publish a deterministic receipt only after its file is flushed."""
    path = long_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def clean(data):
    if isinstance(data, dict):
        return {str(k): clean(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [clean(v) for v in data]
    if isinstance(data, np.ndarray):
        return clean(data.tolist())
    if isinstance(data, np.generic):
        return clean(data.item())
    if isinstance(data, float) and not np.isfinite(data):
        return None
    return data


def csv(path, frame):
    path = long_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    frame.to_csv(tmp, index=False, lineterminator='\n', float_format='%.17g')
    with tmp.open('ab') as stream:
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def npz(path, **arrays):
    path = long_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('wb') as stream:
        np.savez_compressed(stream, **arrays)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def physical_hash(ids, ds, duration):
    return hashlib.sha256(('\n'.join(ids) + '\n').encode() +
        np.asarray(ds, dtype='<i8').tobytes() + np.asarray(duration, dtype='<f8').tobytes()).hexdigest()


def runtime():
    return dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
        scipy=scipy.__version__, numba=numba.__version__, networkx=nx.__version__,
        architecture=platform.architecture()[0])


def hydrate(name, source, fallback=None):
    blob = git(R, 'show', START + ':' + name)
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
        fields = dict(line.split(' ', 1) for line in blob.decode().splitlines())
        oid = fields['oid'].removeprefix('sha256:')
        common = Path(git(source, 'rev-parse', '--git-common-dir').decode().strip())
        if not common.is_absolute():
            common = source / common
        obj = long_path(common / 'lfs/objects' / oid[:2] / oid[2:4] / oid)
        data = obj.read_bytes() if obj.exists() else long_path(source / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != oid and fallback is not None:
            data = long_path(fallback / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == oid and len(data) == int(fields['size']), name
        target = long_path(R / name)
        if sha(R / name) != oid:
            target.write_bytes(data)
    return dict(path=name, sha256=sha(R / name))


def load_model():
    frozen = read(FORMAL / 'Stage 1 Output_expanded/PHYSICAL_INPUTS_FROZEN.json')
    assert sha(R / PHYSICAL) == frozen['files_sha256']['2pc50']
    with np.load(long_path(R / PHYSICAL), allow_pickle=False) as z:
        ids = z['station_ids'].astype(str).tolist()
        banks = {s: (z[s + '_ds'].T.copy(), z[s + '_duration'].T.copy()) for s in ('planning', 'evaluation')}
    assert [banks[s][0].shape for s in banks] == [(64, 92), (1000, 92)]
    ctx, decoder, hashes = execution_context(ids)
    long = pd.read_csv(long_path(R / INPUTS[0]), dtype={'tract_id': str, 'substation_id': str})
    w = long.pivot_table(index='tract_id', columns='substation_id', values='weight',
        aggfunc='sum', fill_value=0).reindex(columns=ids, fill_value=0)
    meta = pd.read_csv(long_path(R / META), dtype={'tract_id': str}).set_index('tract_id')
    mapping = PreparedMapping.from_frame('M1_UTILITY_003', w, ids, meta.population,
        meta.SOVI_quartile, set(meta.index[meta.hospital_tract]))
    assert w.shape == (2315, 92) and len(ctx['origins']) == 57
    assert ctx['graph'].number_of_edges() == 318 and len(ctx['sources']) == 14
    np.testing.assert_allclose(w.sum(axis=1), 1, atol=1e-12, rtol=0)
    cfg = ExpandedConfig()
    devices = core.load_devices(cfg.DEVICES_CSV)
    pga = core.load_pga(cfg.PGA_CSV, cfg.SCENARIOS)
    for frame in (devices, pga):
        frame['id'] = frame['id'].map(core.clean_substation_id)
        assert not frame.id.duplicated().any()
    d = devices.merge(pga, on='id', how='left', validate='one_to_one').set_index('id').loc[ids].copy()
    cols = ['pga_2pc50'] + [f'{kind}_DS{i}' for kind in ('mu', 'beta') for i in range(1, 5)]
    assert np.isfinite(d[cols].to_numpy(float)).all() and (d[cols] > 0).all().all()
    return dict(ids=ids, banks=banks, frozen=frozen, ctx=ctx, decoder=decoder,
        origins=decoder.origins(ctx['origins']), mapping=mapping, context_hashes=hashes,
        devices=d, cfg=cfg)


def sampling_audit(frozen, revision):
    original = frozen['executable_code_commit_sha']
    original_path = 'C257H_Project_Main.py'
    original_bytes = git(revision, 'show', original + ':' + original_path)
    source = original_bytes.decode('utf-8-sig')
    tree = ast.parse(source)
    rows = {}
    for name in SAMPLERS:
        sampler_path = 'r1_realization_scheduling.py' if name=='draw_positive_normal' else original_path
        sampler_source = git(revision,'show',original+':'+sampler_path).decode('utf-8-sig')
        sampler_tree = ast.parse(sampler_source)
        before = next(n for n in sampler_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        after = ast.parse(inspect.getsource(getattr(core,name))).body[0]
        assert ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False), name
        rows[name] = dict(original_commit=original, original_source_path=sampler_path,
            original_source_excerpt=ast.get_source_segment(sampler_source,before), executable_source_sha256=hashlib.sha256(
            inspect.getsource(getattr(core, name)).encode()).hexdigest(), original_AST_equal=True)
    for name in ('REPAIR_PARAM_NORMAL_HR', 'INITIAL_FUNCTIONALITY_BY_DS'):
        node = next(n for n in tree.body if isinstance(n, ast.Assign) and
            any(isinstance(t, ast.Name) and t.id == name for t in n.targets))
        assert ast.literal_eval(node.value) == getattr(core, name), name
    return dict(functions=rows, original_file_git_blob_sha256=hashlib.sha256(original_bytes).hexdigest(),
        original_git_source_checkout=str(revision), repair_parameters=core.REPAIR_PARAM_NORMAL_HR,
        initial_functionality=core.INITIAL_FUNCTIONALITY_BY_DS, changed_correlations=False,
        physical_sampling_calls=0, rng_specification='default_rng(SeedSequence([202610091,3,2,r]))')


def prepare(source, revision):
    assert git(R, 'branch', '--show-current').decode().strip() == BRANCH
    # A published readiness receipt is not silently replaced by preparation.
    if (OUT / 'READINESS_RECEIPT.json').exists():
        verify_freeze()
        print('Existing freeze verified; do not refreeze a ready experiment silently', flush=True)
        return
    baseline = snapshot(revision)
    path = OUT / 'PRESERVATION_BASELINE.json'
    if path.exists():
        assert read(path) == baseline
    else:
        write(path, baseline)
    write(OUT/'SETUP_COMMAND.json',dict(python_executable=sys.executable,
        working_directory=str(R),module='la_grid.diagnostics.independent_validation_20261010',phase='prepare',source_checkout=str(source),
        revision_checkout=str(revision),environment=dict(PYTHONPATH='src',NUMBA_CACHE_DIR=os.environ.get('NUMBA_CACHE_DIR'),
            OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMBA_NUM_THREADS='1'),
        new_validation_samples=0))
    names = list(dict.fromkeys((*INPUTS, *EXTRA_INPUTS)))
    hydration = [hydrate(name, source, revision) for name in names]
    write(OUT / 'HYDRATION_RECEIPT.json', hydration)
    model = load_model()
    registry = []
    for split, (ds, dur) in model['banks'].items():
        for b in range(len(ds)):
            rid = f'2pc50__{split}_{b:04d}'
            h = physical_hash(model['ids'], ds[b], dur[b])
            assert h == model['frozen']['sample_hashes'][rid]
            registry.append(dict(realization_id=rid, physical_sha256=h,
                damage_sha256=hashlib.sha256(ds[b].astype('<i8').tobytes()).hexdigest(),
                duration_sha256=hashlib.sha256(dur[b].astype('<f8').tobytes()).hexdigest()))
    assert len(registry) == len({x['physical_sha256'] for x in registry}) == 1064
    write(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json', registry)
    addendum = read(ADDENDUM)
    for name, expected in read(OLD / 'FREEZE_RECEIPT.json')['files_sha256'].items():
        assert sha(OLD / name) == expected, name
    policies = addendum['ordered_policies']
    expected = {'impact-first', 'hospital-first', 'centrality-first', 'closeness-first',
        'degree-first', 'betweenness-first', 'vulnerability-first', 'random',
        'ga-exploratory-01', 'ga-exploratory-02', GA, ILS}
    assert len(policies) == 12 and {p['strategy'] for p in policies} == expected
    assert len({p['sequence_sha256'] for p in policies}) == 12
    rules = read(FORMAL / 'Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json')['2pc50']
    exploratory = read(R / 'results/diagnostics/extended_ga_20261008/independent_evaluation/CANDIDATE_SELECTION.json')['candidates']
    for p in policies:
        seq = p['sequence']
        assert len(seq) == 92 and set(seq) == set(model['ids']) and identity(seq) == p['sequence_sha256']
        name = p['source_file'].replace('\\', '/')
        hydrate(name, source, revision)
        digest = sha(R / name)
        if 'source_file_sha256' in p:
            assert digest == p['source_file_sha256']
        declared = p.get('source_commit')
        commit = git(R, 'log', '-1', '--format=%H', START, '--', name).decode().strip()
        assert commit, 'Source must have committed provenance: ' + name
        blob = git(R, 'show', commit + ':' + name)
        data = long_path(R / name).read_bytes()
        assert blob.replace(b'\r\n', b'\n') == data.replace(b'\r\n', b'\n'), name
        declaration_verified = None
        original_object_available = False
        authority_checkout = str(R)
        authority_blob = blob
        if declared:
            for checkout in (R,revision):
                available = subprocess.run(['git','cat-file','-t',declared],cwd=checkout,
                    capture_output=True,check=False)
                if available.returncode!=0:
                    continue
                original_object_available = True
                prior_blob = subprocess.run(['git', 'show', declared+':'+name], cwd=checkout,
                    capture_output=True, check=False)
                declaration_verified = prior_blob.returncode==0 and prior_blob.stdout.replace(b'\r\n',b'\n')==data.replace(b'\r\n',b'\n')
                if declaration_verified:
                    authority_checkout = str(checkout)
                    authority_blob = prior_blob.stdout
                    break
            assert declaration_verified is not False, 'Available original source declaration differs: '+name
        if p['strategy'] in rules:
            assert seq == rules[p['strategy']]
        elif p['strategy'].startswith('ga-exploratory'):
            assert seq == next(c['sequence'] for c in exploratory if c['candidate_id'] == p['strategy'])
        elif p['strategy']=='vulnerability-first':
            assert seq == read(R / name)['ordered_station_ids']
        else:
            authority = read(OLD / 'SELECTED_SEQUENCE.json') if p['strategy'] == GA else read(R / name)
            assert seq == authority['sequence']
        p.update(source_file=name, source_file_sha256=digest,
            source_commit=declared if declaration_verified else commit, source_git_checkout=authority_checkout,
            isolated_copy_commit=commit, isolated_copy_git_blob_sha256=hashlib.sha256(blob).hexdigest(),
            prior_declared_source_commit=declared, prior_declared_commit_contains_verified_source=declaration_verified,
            prior_declared_commit_object_available=original_object_available if declared else None,
            source_git_blob_sha256=hashlib.sha256(authority_blob).hexdigest(),
            source_worktree_to_blob='exact' if authority_blob==data else 'content identical after CRLF-to-LF normalization',
            role='primary_selected_GA' if p['strategy'] == GA else
                'prespecified_secondary_diagnostic' if p['strategy'] == ILS else 'fixed_comparator')
    assert next(p['sequence_sha256'] for p in policies if p['strategy'] == GA) == '8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab'
    assert next(p['sequence_sha256'] for p in policies if p['strategy'] == ILS) == '75a1014c7f921c09b574eed4eebcaa412f86fcbc61487bf4a1277c4eb448ddbd'
    manifest = dict(status='FROZEN_FOR_AUTHORIZATION_NOT_VALIDATED', ordered_policies=policies,
        unconstrained=dict(strategy='unconstrained', definition='All DS>0 tasks complete at their original realized duration; zero travel and no crew queue; same source gate and M1 mapping.'),
        total_conditions=13, primary=dict(candidate=GA, reference='impact-first', metric=PRIMARY,
        difference='candidate minus reference'), station_ids=model['ids'], no_formal_replacement=True)
    write(OUT / 'FINAL_COMPARATOR_MANIFEST.json', manifest)
    inputs = {x['path']: x['sha256'] for x in hydration}
    inputs.update({p['source_file']: p['source_file_sha256'] for p in policies})
    for name in ('config/parent_frozen_design/FINAL_EXPERIMENT_MATRIX.json',
        'Formal_Experiment_20260923/Stage 1 Output_expanded/PHYSICAL_INPUTS_FROZEN.json',
        'Formal_Experiment_20260923/Stage 5 Output_expanded/FINAL_DIRECT_COMMUNITY_SEQUENCE.json',
        'Formal_Experiment_20260923/FINAL_EXECUTION_VALIDATION.json'):
        inputs[name] = sha(R / name)
    formal_hashes = read(FORMAL / 'FINAL_EXECUTION_VALIDATION.json')['input_sha256']
    for name in ('Data/working_area_substations_with_fragility.csv', 'Data/Substations_PGA_IDW_CEC_expanded.csv', INPUTS[0]):
        assert inputs[name] == formal_hashes[name.replace('/', '\\')]
    sampling = sampling_audit(model['frozen'], revision)
    write(OUT / 'SAMPLING_SOURCE_AUDIT.json', sampling)
    receipt = dict(status='FROZEN_PROSPECTIVE_SPECIFICATION_QA_IN_SEPARATE_RECEIPT', start_commit=START, branch=BRANCH,
        manifest_sha256=sha(OUT / 'FINAL_COMPARATOR_MANIFEST.json'),
        previous_hash_registry_sha256=sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json'),
        source_addendum_sha256=sha(ADDENDUM), original_protocol_sha256=sha(OLD / 'FINAL_VALIDATION_PROTOCOL.json'),
        input_sha256=inputs, code_sha256={p: sha(R / p) for p in CODE}, runtime=runtime(),
        sampling_source_audit_sha256=sha(OUT / 'SAMPLING_SOURCE_AUDIT.json'),
        sample_size=N, rng_entropy_prefix=[202610091, 3, 2], realization_indices=[0, N-1],
        generator='numpy.default_rng / PCG64', gate_threshold=.5, mapping='M1_UTILITY_003',
        hazard='2pc50', resource='C57_D1', evaluation_horizon_hr=H,
        planning_horizon_hr=read(FORMAL / 'Stage 5 Output_expanded/FINAL_DIRECT_COMMUNITY_SEQUENCE.json')['H_plan_hr'],
        primary=manifest['primary'], endpoints=list(METRICS), bootstrap=dict(resamples=BOOT,
        seed=BOOT_SEED, unit='whole shared realization', CI='two-sided 95% percentile',
        secondary_inference='pointwise descriptive only; not simultaneous or confirmatory'),
        T80=dict(reached='first exact event with population availability >=0.8',
            unreached='null T80, censored=true, restricted_time=480; no dropping',
            contrasts='restricted-time and censoring-risk contrasts; conditional reached-only mean explicitly nonprimary'),
        no_optional_stopping=True, no_reselection=True, new_validation_samples=0,
        authorization_required=True, formal_policy_replaced=False,
        protected_revision_checkout=str(revision), protected_revision_baseline_sha256=sha(path))
    write(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json', receipt)
    print('FREEZE_PREPARED', len(policies), 'fixed orders + Unconstrained; new draws=0', flush=True)


def verify_freeze():
    receipt = read(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')
    assert receipt['runtime'] == runtime(), 'Frozen numerical runtime changed'
    for p, h in {**receipt['input_sha256'], **receipt['code_sha256']}.items():
        assert sha(R / p) == h, p
    assert sha(OUT / 'FINAL_COMPARATOR_MANIFEST.json') == receipt['manifest_sha256']
    assert sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json') == receipt['previous_hash_registry_sha256']
    assert sha(OUT / 'SAMPLING_SOURCE_AUDIT.json') == receipt['sampling_source_audit_sha256']
    assert sha(ADDENDUM) == receipt['source_addendum_sha256']
    assert sha(OLD / 'FINAL_VALIDATION_PROTOCOL.json') == receipt['original_protocol_sha256']
    return receipt


def evaluate(model, policy, ds, duration, rid):
    ids, ctx, mapping = model['ids'], model['ctx'], model['mapping']
    ds_s, dur_s = pd.Series(ds, index=ids), pd.Series(duration, index=ids)
    if policy['strategy'] == 'unconstrained':
        finish = pd.Series(np.where(ds > 0, duration, np.nan), index=ids)
        events = pd.DataFrame([dict(task_id=ids[i], damage_state=int(ds[i]),
            dispatch_rank=None, crew_index=None, crew_origin_id=None, previous_task_id=None,
            crew_available_before_hr=0., travel_hr=0., arrival_hr=0.,
            realized_duration_hr=float(duration[i]), completion_hr=float(duration[i]))
            for i in range(92) if ds[i] > 0])
    else:
        events, finish, _, _ = execute_realization_schedule(full_priority_sequence=policy['sequence'],
            damage_state=ds_s, realized_duration_hr=dur_s, crew_origin_ids=ctx['origins'],
            base_to_task_hr=ctx['base'], task_to_task_hr=ctx['task'])
    finite = finish.dropna().to_numpy(float)
    event = np.unique(np.r_[0., finite[(finite > 0) & (finite < H)], H])
    raw = evaluate_completion_step_functionality(damage_state=ds_s, completion_time_hr=finish, time_hr=event)
    trace = evaluate_source_gate(raw, ctx['graph'], ctx['sources'], threshold=.5)
    arrays = {k: getattr(trace, k).to_numpy() for k in ('f', 'F', 'C', 'e', 'L_self', 'L_threshold', 'L_source', 'L_total')}
    summary, tract, station = evaluate_exact_event_arrays(mapping=mapping, event_time_hr=event,
        **{k: v for k, v in arrays.items() if k not in ('F', 'C')})
    mass = mapping.weight.T @ mapping.population
    summary.update(realization_id=rid, strategy=policy['strategy'], physical_sha256=physical_hash(ids, ds, duration),
        population_T80_censored=bool(not np.isfinite(summary['population_T80_hr'])),
        T80_censored=int(not np.isfinite(summary['population_T80_hr'])),
        T80_restricted_hr=float(summary['population_T80_hr']) if np.isfinite(summary['population_T80_hr']) else H,
        effective_service_at_480=float(arrays['e'][-1] @ mass / mass.sum()),
        makespan_hr=float(finite.max()) if len(finite) else 0., task_count=len(finite),
        tasks_completed_after_480=int((finite > H).sum()),
        total_travel_hr=float(events.travel_hr.sum()) if len(events) else 0.)
    if len(events):
        events.insert(0, 'strategy', policy['strategy'])
        events.insert(0, 'realization_id', rid)
        events['completion_within_480'] = events.completion_hr <= H
    else:
        events = pd.DataFrame(columns=['realization_id','strategy','dispatch_rank','task_id',
            'damage_state','crew_index','crew_origin_id','previous_task_id','crew_available_before_hr',
            'travel_hr','arrival_hr','realized_duration_hr','completion_hr','completion_within_480'])
    # Independent minimax kernel, not a replacement of the production gate.
    index = {x: i for i, x in enumerate(ids)}
    neighbors, offsets = [], [0]
    for s in ids:
        neighbors.extend(index[n] for n in sorted(ctx['graph'].neighbors(s)))
        offsets.append(len(neighbors))
    source_flag = np.array([s in ctx['sources'] for s in ids])
    exact = completion_loss(np.nan_to_num(finish.to_numpy(), nan=0.), ds, source_flag,
        np.array(offsets, np.int64), np.array(neighbors, np.int64), mass, float(mass.sum()), H)
    assert abs(exact - summary[PRIMARY]) < 1e-8
    summary['independent_kernel_abs_error_hr'] = float(abs(exact-summary[PRIMARY]))
    return clean(summary), events, event, arrays, tract, station, finish


def policies():
    manifest = read(OUT / 'FINAL_COMPARATOR_MANIFEST.json')
    return manifest['ordered_policies'] + [manifest['unconstrained']]


def run_case(model, folder, rid, ds, duration, *, crash_after_policy=None):
    folder = long_path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    key = dict(realization_id=rid, physical_sha256=physical_hash(model['ids'], ds, duration),
        freeze_sha256=sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json'))
    done = folder / 'COMPLETE.json'
    if done.exists():
        saved = read(done)
        assert saved['identity'] == key, 'Resume context/physical sample changed'
        for name, h in saved['files_sha256'].items():
            assert sha(folder / name) == h, 'Checkpoint corruption: ' + name
        return saved
    write(folder / 'PHYSICAL.json', dict(**key, station_ids=model['ids'], damage_state=ds.tolist(),
        duration_hr=duration.tolist(), damage_sha256=hashlib.sha256(ds.astype('<i8').tobytes()).hexdigest(),
        duration_sha256=hashlib.sha256(duration.astype('<f8').tobytes()).hexdigest()))
    summaries, tasks, times, lengths, trajectories, tract_loss, station_loss = [], [], [], [], {}, [], []
    for n, policy in enumerate(policies()):
        summary, events, clock, arrays, tract, station, _ = evaluate(model, policy, ds, duration, rid)
        summaries.append(summary)
        tasks.append(events)
        times.append(clock)
        lengths.append(len(clock))
        tract_loss.append(tract['normalized_burden_hr'])
        station_loss.append(np.array([station[k] for k in ('L_self', 'L_threshold', 'L_source', 'L_total')]))
        for k, v in arrays.items():
            trajectories.setdefault(k, []).append(v)
        if crash_after_policy == n:
            write(folder / 'PARTIAL_PROGRESS.json', dict(identity=key, completed_policy_count=n+1,
                atomic_unit='one whole shared realization; resume re-evaluates this same saved physical state'))
            raise InterruptedError('Deliberate dry-run interruption')
    csv(folder / 'SUMMARY.csv', pd.DataFrame(summaries))
    csv(folder / 'TASK_EXECUTION.csv', pd.concat(tasks, ignore_index=True))
    npz(folder / 'TRAJECTORIES.npz', station_ids=np.array(model['ids']), tract_ids=model['mapping'].tract_ids,
        policies=np.array([p['strategy'] for p in policies()]), event_lengths=np.array(lengths),
        event_time_hr=np.concatenate(times), tract_normalized_loss_hr=np.array(tract_loss),
        station_component_integrals_hr=np.array(station_loss),
        **{k: np.concatenate(v) for k, v in trajectories.items()})
    names = ('PHYSICAL.json', 'SUMMARY.csv', 'TASK_EXECUTION.csv', 'TRAJECTORIES.npz')
    record = dict(status='COMPLETE_SHARED_REALIZATION', identity=key, policy_count=13,
        files_sha256={name: sha(folder / name) for name in names})
    write(done, record)
    return record


def paired_statistics(frame):
    names = [p['strategy'] for p in policies()]
    cases = frame.realization_id.drop_duplicates().tolist()
    if frame.duplicated(['realization_id', 'strategy']).any() or len(frame) != len(cases)*13:
        raise ValueError('Incomplete or duplicated whole-realization policy records')
    y = np.stack([frame.pivot(index='realization_id', columns='strategy', values=k).loc[cases, names].to_numpy(float) for k in METRICS], axis=2)
    if not np.isfinite(y).all():
        raise ValueError('Missing primary/secondary endpoint: no silent complete-case deletion')
    n = len(cases)
    if n < 2:
        raise ValueError('At least two old cases for the engineering bootstrap')
    # A single shared resample bank drives every policy and endpoint. Bounded memory.
    rng = np.random.default_rng(BOOT_SEED)
    boot = np.empty((BOOT, 13, len(METRICS)))
    for start in range(0, BOOT, 100):
        counts = np.zeros((min(100, BOOT-start), n))
        indices = rng.integers(0, n, size=(len(counts), n))
        for row, ix in enumerate(indices):
            counts[row] = np.bincount(ix, minlength=n)/n
        boot[start:start+len(counts)] = (counts @ y.reshape(n, -1)).reshape(len(counts), 13, -1)
    rows, levels = [], []
    ref = names.index('impact-first')
    for j, name in enumerate(names):
        for k, field in enumerate(METRICS):
            v, b = y[:, j, k], boot[:, j, k]
            lo, hi = np.quantile(b, [.025, .975])
            levels.append(dict(strategy=name, metric=field, n=n, mean=v.mean(), mcse=v.std(ddof=1)/np.sqrt(n),
                ci_low=lo, ci_high=hi, median=np.median(v), p05=np.quantile(v,.05), p95=np.quantile(v,.95), inference='descriptive pointwise'))
            difference, bs = v-y[:, ref, k], b-boot[:, ref, k]
            low, high = np.quantile(bs, [.025, .975])
            rows.append(dict(candidate=name, reference='impact-first', metric=field, n=n,
                mean_difference=difference.mean(), mcse=difference.std(ddof=1)/np.sqrt(n),
                ci_low=low, ci_high=high, improved_count=int((difference < -1e-9).sum()),
                worsened_count=int((difference > 1e-9).sum()), ties_count=int((abs(difference)<=1e-9).sum()),
                inference='prespecified primary' if name==GA and field==PRIMARY else 'descriptive pointwise'))
    # Refined ILS versus GA was prespecified, not selected from these outcomes.
    j, ref = names.index(ILS), names.index(GA)
    for k, field in enumerate(METRICS):
        v = y[:,j,k]-y[:,ref,k]
        low, high = np.quantile(boot[:,j,k]-boot[:,ref,k], [.025,.975])
        rows.append(dict(candidate=ILS, reference=GA, metric=field, n=n,
            mean_difference=v.mean(), mcse=v.std(ddof=1)/np.sqrt(n), ci_low=low, ci_high=high,
            improved_count=int((v < -1e-9).sum()), worsened_count=int((v > 1e-9).sum()),
            ties_count=int((abs(v)<=1e-9).sum()), inference='prespecified descriptive diagnostic'))
    return pd.DataFrame(rows), pd.DataFrame(levels)


def export(root, model, expected_ids, *, independent):
    root = long_path(root)
    folders = [root / 'cases' / rid for rid in expected_ids]
    frames, curves = [], []
    grid = np.arange(481.)
    mass = model['mapping'].weight.T @ model['mapping'].population
    qmass = np.array([model['mapping'].weight.T @ (model['mapping'].population*(model['mapping'].quartile==q)) for q in ('Q1','Q2','Q3','Q4')])
    for folder, rid in zip(folders, expected_ids):
        record = read(folder / 'COMPLETE.json')
        assert record['identity']['realization_id'] == rid
        assert record['identity']['freeze_sha256'] == sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')
        for name, h in record['files_sha256'].items():
            assert sha(folder / name) == h
        frame = pd.read_csv(folder / 'SUMMARY.csv', float_precision='round_trip')
        assert frame.realization_id.eq(rid).all() and frame.physical_sha256.nunique()==1
        frames.append(frame)
        with np.load(folder / 'TRAJECTORIES.npz', allow_pickle=False) as z:
            start = 0
            for p, length in zip(z['policies'], z['event_lengths']):
                event = z['event_time_hr'][start:start+length]
                e = z['e'][start:start+length]
                assert event[0]==0 and event[-1]==H
                ix = np.searchsorted(event, grid, side='right')-1
                available = e[ix] @ mass / mass.sum()
                quarterly = e[ix] @ qmass.T / qmass.sum(axis=1)
                curves.append(pd.DataFrame(dict(realization_id=rid, strategy=str(p), time_hr=grid,
                    population_availability=available, Q1_availability=quarterly[:,0],
                    Q4_availability=quarterly[:,3], signed_Q4_minus_Q1_availability=quarterly[:,3]-quarterly[:,0])))
                start += length
    frame = pd.concat(frames, ignore_index=True)
    assert frame.realization_id.nunique() == len(expected_ids) and len(frame)==13*len(expected_ids)
    effects, levels = paired_statistics(frame)
    csv(root / 'REALIZATION_OUTCOMES.csv', frame)
    csv(root / 'PAIRED_EFFECTS.csv', effects)
    csv(root / 'POLICY_OUTCOMES.csv', levels)
    csv(root / 'PRIMARY_PAIRED_EFFECT.csv', effects[(effects.candidate==GA)&(effects.reference=='impact-first')&(effects.metric==PRIMARY)])
    t80 = frame.groupby('strategy').agg(n=('realization_id','size'), reached_count=('population_T80_hr','count'),
        censored_count=('T80_censored','sum'), restricted_mean_hr=('T80_restricted_hr','mean'),
        reached_only_conditional_mean_hr=('population_T80_hr','mean')).reset_index()
    t80['unreached_T80_is_missing_not_zero'] = True
    csv(root / 'T80_CENSORING.csv', t80)
    sensitivity = frame.pivot(index='realization_id', columns='strategy', values=list(METRICS))
    changes = pd.DataFrame({'realization_id': sensitivity.index})
    for metric in METRICS:
        changes[metric+'_ILS_minus_GA'] = (sensitivity[metric][ILS]-sensitivity[metric][GA]).to_numpy()
    csv(root / 'GA_REFINED_ILS_REALIZATION_CHANGES.csv', changes)
    recovery = pd.concat(curves).groupby(['strategy','time_hr'], as_index=False).mean(numeric_only=True)
    csv(root / 'RECOVERY_DISPARITY_CURVES.csv', recovery)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for field, filename, ylabel in (('population_availability','RECOVERY.png','Population service availability'),
        ('signed_Q4_minus_Q1_availability','DISPARITY.png','Q4 minus Q1 availability')):
        fig, ax = plt.subplots(figsize=(9,5))
        for strategy in ('impact-first', GA, ILS, 'unconstrained'):
            sub = recovery[recovery.strategy==strategy]
            ax.plot(sub.time_hr, sub[field], label=strategy)
        ax.set(xlabel='Time (hours)', ylabel=ylabel, xlim=(0,H),
            title='Independent validation' if independent else 'OLD-CASE ENGINEERING DRY RUN (not validation)')
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(root / filename, dpi=180)
        plt.close(fig)
    files = [p for p in root.iterdir() if p.suffix in ('.csv','.png')]
    write(root / 'EXPORT_RECEIPT.json', dict(status='INDEPENDENT_VALIDATION_COMPLETED' if independent else 'OLD_CASE_DRY_RUN_ONLY',
        realization_count=len(expected_ids), condition_count=13, bootstrap_resamples=BOOT,
        bootstrap_seed=BOOT_SEED, horizon_hr=H, new_validation_samples=len(expected_ids) if independent else 0,
        no_policy_selection=True, freeze_sha256=sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json'),
        files_sha256={p.name:sha(p) for p in files}))
    return effects


@contextmanager
def exclusive(root):
    root = long_path(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = root / 'RUN.lock'
    fd = os.open(lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd, json.dumps(dict(pid=os.getpid(), hostname=platform.node())).encode())
        os.fsync(fd)
        yield
    finally:
        os.close(fd)
        lock.unlink()


def require_authorization(path):
    if path is None:
        raise PermissionError('Explicit author authorization is required; preparation may not draw physical samples.')
    auth = read(path)
    if not (auth.get('authorization_type')=='EXPLICIT_AUTHOR_APPROVAL_FOR_FIXED_2000_VALIDATION'
        and auth.get('author') and auth.get('verbatim_author_request') and auth.get('authorized_at_utc')
        and auth.get('freeze_sha256')==sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')
        and auth.get('sample_size')==N and auth.get('allow_policy_reselection') is False):
        raise PermissionError('Incomplete, wrong-size or wrong-freeze authorization; no sampling')
    return auth


def check_overlap(ids, ds, duration, previous, generated):
    h = physical_hash(ids, ds, duration)
    if h in previous or h in generated:
        raise ValueError('EXACT_PHYSICAL_OVERLAP_STOP_FOR_REVIEW: ' + h)
    return h


def generate_one(model, root, r, previous, generated):
    """Called only inside authorized execute; draw once, then persist before policies."""
    folder = long_path(root / 'physical' / f'{r:04d}')
    folder.mkdir(parents=True, exist_ok=True)
    physical = folder / 'DRAW.json'
    marker = folder / 'DRAW_STARTED.json'
    if physical.exists():
        record = read(physical)
        expected = record.pop('payload_sha256')
        assert hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()==expected
        assert record['r']==r and record['freeze_sha256']==sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')
        assert record['station_ids']==model['ids'] and record['entropy']==[202610091,3,2,r]
        ds, duration = np.array(record['damage_state'], np.int64), np.array(record['duration_hr'], float)
        assert record['physical_sha256']==physical_hash(model['ids'], ds, duration)
        assert record['damage_sha256']==hashlib.sha256(ds.astype('<i8').tobytes()).hexdigest()
        assert record['duration_sha256']==hashlib.sha256(duration.astype('<f8').tobytes()).hexdigest()
        return ds, duration, record
    if marker.exists():
        raise RuntimeError('Interrupted during an uncommitted draw; STOP_FOR_REVIEW, never redraw silently')
    write(marker, dict(r=r, entropy=[202610091,3,2,r], freeze_sha256=sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')))
    rng = np.random.default_rng(np.random.SeedSequence([202610091,3,2,r]))
    before = rng.bit_generator.state
    ds = core.sample_damage_states(model['devices']['pga_2pc50'], model['devices'], 1, rng)
    _, duration = core.damage_to_functionality_and_repair(ds, rng, model['cfg'])
    ds, duration = ds[:,0], duration[:,0]
    record = dict(r=r, entropy=[202610091,3,2,r], station_ids=model['ids'], damage_state=ds.tolist(),
        duration_hr=duration.tolist(), rng_before=before, rng_after=rng.bit_generator.state,
        damage_sha256=hashlib.sha256(ds.astype('<i8').tobytes()).hexdigest(),
        duration_sha256=hashlib.sha256(duration.astype('<f8').tobytes()).hexdigest(),
        physical_sha256=physical_hash(model['ids'], ds, duration),
        freeze_sha256=sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json'))
    try:
        check_overlap(model['ids'], ds, duration, previous, generated)
    except ValueError:
        write(root / 'ABORT_OVERLAP.json', record)
        raise
    record['payload_sha256'] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    write(physical, record)
    return ds, duration, record


def check_archive_path(archive, freeze):
    archive = Path(archive).resolve()
    protected = Path(freeze['protected_revision_checkout']).resolve()
    if archive==Path(archive.anchor) or protected.is_relative_to(archive) or archive.is_relative_to(protected):
        raise ValueError('Archive may not contain or modify the protected revision checkout')
    if archive.is_relative_to(R.resolve()) and not archive.is_relative_to((OUT/'authorized_validation').resolve()):
        raise ValueError('Repository archives are restricted to this diagnostic authorized_validation directory')
    if archive.exists() and any(archive.iterdir()) and not (archive/'RUN_IDENTITY.json').is_file():
        raise ValueError('Refuse a nonempty unrelated directory; no overwriting existing results')
    return archive


def execute(authorization, archive):
    require_authorization(authorization)  # Must precede loading or sampling anything.
    freeze = verify_freeze()
    readiness = read(OUT / 'READINESS_RECEIPT.json')
    assert readiness['status']=='READY_FOR_AUTHORIZED_VALIDATION'
    assert readiness['freeze_sha256']==sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')
    assert readiness['qa_sha256']==sha(OUT / 'VALIDATION_DRY_RUN_QA.json')
    assert read(OUT / 'VALIDATION_DRY_RUN_QA.json')['status']=='PASS'
    for name,h in readiness['files_sha256'].items():
        assert sha(OUT/name)==h
    archive = check_archive_path(archive, freeze)
    required = read(OUT / 'CAPACITY_RUNTIME_ESTIMATE.json')['reserved_storage_bytes']
    if shutil.disk_usage(archive.parent).free < required:
        raise OSError('Insufficient archive and temporary-storage reserve')
    previous = {x['physical_sha256'] for x in read(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json')}
    model = load_model()
    with exclusive(archive):
        if (archive / 'ABORT_OVERLAP.json').exists():
            raise RuntimeError('Overlap abort is latched; review required, no continuation')
        path = archive / 'RUN_IDENTITY.json'
        run_id = dict(freeze_sha256=sha(OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json'),
            authorization_sha256=sha(authorization), sample_size=N, policies=13, runtime=runtime())
        if path.exists():
            assert read(path)==run_id
        else:
            write(path, run_id)
        generated = set()
        for r in range(N):
            ds, duration, record = generate_one(model, archive, r, previous, generated)
            h = check_overlap(model['ids'], ds, duration, previous, generated)
            generated.add(h)
            rid = f'2pc50__independent_{r:04d}'
            run_case(model, archive / 'cases' / rid, rid, ds, duration)
            if r%100==0:
                print('Checkpoint:', r+1, '/', N, '(no intermediate effect inspection)', flush=True)
        assert len(generated)==N
        export(archive, model, [f'2pc50__independent_{r:04d}' for r in range(N)], independent=True)
        write(archive / 'REPRODUCIBILITY_RECEIPT.json', dict(status='INDEPENDENT_VALIDATION_COMPLETED',
            sample_count=N, unique_physical_hashes=N, original_overlap_count=0, policy_count=13,
            freeze=freeze, run_identity=run_id, git_commit=git(R,'rev-parse','HEAD').decode().strip(),
            export_sha256=sha(archive / 'EXPORT_RECEIPT.json'),
            physical_receipts_sha256={str(r):sha(archive / 'physical' / f'{r:04d}' / 'DRAW.json') for r in range(N)},
            limitations='Fixed model, not field restoration validation; new simulated states, not external empirical cohort; secondary contrasts descriptive.'))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=('prepare','dry-run','verify','execute'))
    p.add_argument('--source', type=Path)
    p.add_argument('--revision', type=Path)
    p.add_argument('--authorization', type=Path)
    p.add_argument('--archive', type=Path)
    a = p.parse_args()
    if a.phase=='prepare':
        if a.source is None or a.revision is None:
            p.error('prepare requires --source and --revision')
        prepare(a.source, a.revision)
    elif a.phase=='dry-run':
        from la_grid.diagnostics.independent_validation_qa_20261010 import dry_run
        dry_run()
    elif a.phase=='verify':
        receipt = verify_freeze()
        assert snapshot(Path(receipt['protected_revision_checkout']))==read(OUT / 'PRESERVATION_BASELINE.json')
        print('FREEZE_AND_PRESERVATION_PASS; no new physical samples', flush=True)
    else:
        if a.archive is None:
            p.error('execute requires a new, dedicated --archive')
        execute(a.authorization, a.archive)


if __name__=='__main__':
    main()
