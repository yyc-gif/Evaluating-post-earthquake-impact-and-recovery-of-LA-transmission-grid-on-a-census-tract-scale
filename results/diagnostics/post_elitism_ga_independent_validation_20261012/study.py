"""Candidate-specific fixed-policy validation using the unchanged native engine."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT.parent / '_gaf12'
SOURCE = ROOT.parent / '_ger14'
sys.path.insert(0, str(BASE / 'src'))
from la_grid.diagnostics import independent_validation_20261010 as v
from la_grid.diagnostics import standalone_ils_validation_20261011 as q
from la_grid.diagnostics import standalone_ils_validation_analysis_20261011 as a
from la_grid.diagnostics.ga_research_preserve_20261009 import snapshot, git
from la_grid.diagnostics.ga_search_budget_sensitivity import identity
import numpy as np

OUT = v.long_path(Path(__file__).resolve().parent)
REL = 'results/diagnostics/post_elitism_ga_independent_validation_20261012'
PARENT = '866cf86ae8384ac2e77f0d697012d20f478ca693'
BRANCH = 'diagnostics/post-evaluation-ga-independent-validation-20261012'
SAMPLE_SEED, BOOT_SEED = 202610120701, 202610120702
CANDIDATE, PREVIOUS, IMPACT = 'GA-post-evaluation-elitism', 'GA-previous-pure-random', 'Impact-first'
EXPECTED = ['46732e49c3afa0827cdf37543882b3ec3f06ab0a3f600eedd92162733fa5ee82',
            'edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a',
            'd75ee1dc0fed0671b40d7f539d1e456ea42402105554cb1eb41ab3ec41bc9168']
SOURCE_OUT = v.long_path(SOURCE / 'results/diagnostics/pure_random_ga_elitism_revision_20261011')
PREVIOUS_OUT = v.long_path(BASE / 'results/diagnostics/pure_random_ga_final_20261011')
PRIOR_COHORTS = [
    PREVIOUS_OUT / 'cohort/physical',
    v.long_path(ROOT.parent / '_vils7/results/diagnostics/standalone_ils_prospective_validation_20261011/cohort/physical'),
    v.long_path(ROOT.parent / '_val4/results/diagnostics/independent_validation_ready_20261010/authorized_validation/fixed_2000_20261010/physical'),
]
REVISION = Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
MISSING = Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_manuscript_rebuild\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
BACKUP = Path(r'C:\2025-2026 Fall\Local_Recovery_Snapshot_20260925\Private_Backup_Small\private-la-grid-research\manuscripts\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
BACKUP_SHA = 'a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253'


def preserved(*unused):
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    result = snapshot(REVISION)
    result.update(index_entries_sha256=hashlib.sha256(git(REVISION, 'ls-files', '--stage', '-z')).hexdigest(),
                  staged_count=len([x for x in git(REVISION, 'diff', '--cached', '--name-only', '-z').split(b'\0') if x]),
                  revision_status_sha256=hashlib.sha256(git(REVISION, 'status', '--porcelain=v1', '-z')).hexdigest())
    assert len(result['files_sha256']) == 950 and result['staged_count'] == 862
    result['source_checkouts'] = {str(p): dict(head=git(p, 'rev-parse', 'HEAD').decode().strip(),
        branch=git(p, 'branch', '--show-current').decode().strip(),
        staged_diff_sha256=hashlib.sha256(git(p, 'diff', '--cached', '--binary')).hexdigest())
        for p in (SOURCE, BASE, ROOT.parent / '_vils7', ROOT.parent / '_val4')}
    names = ('FINAL_ELITISM_DECISION.md', 'POST_DEVELOPMENT_CANDIDATE_FREEZE.json',
             'POST_EVALUATION_ELITISM_SPECIFICATION.md', 'IMPORTANT_CANDIDATE_PRODUCTION_QA.json',
             'PROPOSED_INDEPENDENT_VALIDATION_SPECIFICATION.json', 'REPRODUCIBILITY_AND_PRESERVATION_QA.json')
    result['frozen_source_package_sha256'] = {n: v.sha(SOURCE_OUT / n) for n in names}
    result['old_validation_sha256'] = {str(p): v.sha(p) for p in (
        PREVIOUS_OUT / 'FINAL_RANDOM_GA_CANDIDATE.json', PREVIOUS_OUT / 'EXECUTION_FREEZE.json',
        PREVIOUS_OUT / 'FIXED2000_FULL_EVIDENCE.zip',
        ROOT.parent / '_vils7/results/diagnostics/standalone_ils_prospective_validation_20261011/FIXED2000_FULL_EVIDENCE.zip',
        ROOT.parent / '_val4/results/diagnostics/independent_validation_ready_20261010/FINAL_VALIDATION_FREEZE_RECEIPT.json')}
    result['preexisting_external_exception'] = dict(path=str(MISSING), exists=MISSING.exists(),
        backup_path=str(BACKUP), backup_exists=BACKUP.exists(), backup_sha256=v.sha(BACKUP),
        restored=False, designated_authoritative=False)
    assert not MISSING.exists() and result['preexisting_external_exception']['backup_sha256'] == BACKUP_SHA
    return result


def configure():
    q.OUT, q.ARCHIVE, q.PARENT, q.BRANCH = OUT, OUT / 'cohort', PARENT, BRANCH
    q.N, q.BOOT, q.SAMPLE_SEED, q.BOOT_SEED = 2000, 20000, SAMPLE_SEED, BOOT_SEED
    q.ILS, q.GA, q.IMPACT = CANDIDATE, PREVIOUS, IMPACT
    q.verify, q.protected_state, q.worker_setup = verify, preserved, worker_setup
    a.OUT, a.R, a.MODULE = OUT, v.long_path(ROOT), REL + '/study.py'


def worker_setup():
    configure()
    q.MODEL, q.POLICIES = v.load_model(), verify()['strategies']


def verify():
    f = v.read(OUT / 'EXECUTION_FREEZE.json')
    assert f['runtime'] == v.runtime()
    assert git(ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    for path, h in f['runtime_files_sha256'].items():
        assert v.sha(Path(path)) == h, path
    for name, h in f['local_files_sha256'].items():
        assert v.sha(OUT / name) == h, name
    assert v.sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json') == f['previous_registry_sha256']
    assert f['sample_size'] == 2000 and f['horizon_hr'] == 480 and len(f['strategies']) == 3
    assert [identity(p['sequence']) for p in f['strategies']] == EXPECTED
    assert v.sha(OUT / 'AUTHORIZATION_AND_EXECUTION_FREEZE.json') == f['authorization_sha256']
    return f


def setup():
    configure()
    assert not (OUT / 'EXECUTION_FREEZE.json').exists()
    assert git(ROOT, 'rev-parse', 'HEAD').decode().strip() == PARENT
    assert git(SOURCE, 'rev-parse', 'HEAD').decode().strip() == PARENT
    current = preserved()
    v.write(OUT / 'PRESERVATION_BASELINE.json', current)
    previous_freeze = v.read(PREVIOUS_OUT / 'EXECUTION_FREEZE.json')
    runtime = {}
    for name, expected in {**previous_freeze['input_sha256'], **previous_freeze['code_sha256']}.items():
        p = v.long_path(BASE / name)
        assert v.sha(p) == expected, name
        runtime[str(p)] = expected
    for name in ('src/la_grid/revision/r1_distributional_metrics.py',):
        p = v.long_path(BASE / name)
        runtime[str(p)] = v.sha(p)
    model = v.load_model()
    candidate = v.read(SOURCE_OUT / 'POST_DEVELOPMENT_CANDIDATE_FREEZE.json')
    previous = v.read(PREVIOUS_OUT / 'FINAL_RANDOM_GA_CANDIDATE.json')
    rules = v.read(v.long_path(BASE / 'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json'))
    strategies = [dict(strategy=CANDIDATE, sequence=candidate['sequence'], seed=2026121110,
                       planning_loss_hr=32.995220412410944, algorithm='POST_EVALUATION_WORST_OFFSPRING_ELITISM'),
                  dict(strategy=PREVIOUS, sequence=previous['sequence'], seed=2026103108,
                       planning_loss_hr=32.99552241352315, algorithm='LEGACY_LAST_POSITION_ELITISM'),
                  dict(strategy=IMPACT, sequence=rules['2pc50']['impact-first'], algorithm='unchanged Impact-first')]
    for p, h in zip(strategies, EXPECTED):
        assert len(p['sequence']) == len(set(p['sequence'])) == 92 and set(p['sequence']) == set(model['ids'])
        p['sequence_sha256'] = identity(p['sequence'])
        assert p['sequence_sha256'] == h
    assert candidate['seed'] == 2026121110 and candidate['budget'] == 100000
    assert candidate['planning_loss_hr'] == strategies[0]['planning_loss_hr']
    qa = v.read(SOURCE_OUT / 'IMPORTANT_CANDIDATE_PRODUCTION_QA.json')
    record = next(x for x in qa['important_candidates'] if x['sequence_sha256'] == EXPECTED[0])
    assert record['status'] == 'PASS' and record['physical_realizations'] == 64
    assert record['sequence'] == strategies[0]['sequence'] and record['max_native_kernel_difference_hr'] < 1e-8
    v.write(OUT / 'PLANNING64_PRODUCTION_QA_REUSED.json', dict(status='PASS_REUSED',
        record=record, source_sha256=v.sha(SOURCE_OUT / 'IMPORTANT_CANDIDATE_PRODUCTION_QA.json'),
        new_optimizer_calls=0, new_planning_production_calls=0))
    for name in current['frozen_source_package_sha256']:
        p = SOURCE_OUT / name
        runtime[str(p)] = v.sha(p)
    registry = {}
    for scenario, expected in model['frozen']['files_sha256'].items():
        p = v.long_path(BASE / f'Formal_Experiment_20260923/Stage 1 Output_expanded/physical_inputs_{scenario}.npz')
        assert v.sha(p) == expected
        runtime[str(p)] = expected
        with np.load(p, allow_pickle=False) as z:
            ids = z['station_ids'].astype(str).tolist()
            for split in ('planning', 'evaluation'):
                for i, (ds, dur) in enumerate(zip(z[split + '_ds'].T, z[split + '_duration'].T)):
                    name = f'{scenario}__{split}_{i:04d}'
                    h = v.physical_hash(ids, ds, dur)
                    assert h == model['frozen']['sample_hashes'][name]
                    registry[name] = h
    assert len(registry) == 4064
    namespaces, receipts = [], {}
    for j, cohort in enumerate(PRIOR_COHORTS):
        paths = sorted(cohort.glob('*/DRAW.json'))
        assert len(paths) == 2000, str(cohort)
        cohort_entropy = []
        for path in paths:
            draw = v.read(path)
            h = v.physical_hash(draw['station_ids'], np.array(draw['damage_state']), np.array(draw['duration_hr']))
            assert h == draw['physical_sha256']
            assert SAMPLE_SEED not in draw['entropy'][:-1]
            registry[f'prior_cohort{j}_{draw["r"]:04d}'] = h
            cohort_entropy.append(draw['entropy'])
            receipts[str(path)] = v.sha(path)
        namespaces.append(dict(path=str(cohort), count=2000, entropy_prefix=cohort_entropy[0][:-1],
                               all_entropies_unique=len({tuple(x) for x in cohort_entropy}) == 2000))
    assert len(registry) == len(set(registry.values())) == 10064
    v.write(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json', registry)
    v.write(OUT / 'PRIOR_PHYSICAL_RECEIPT_HASHES.json', receipts)
    v.write(OUT / 'SEED_AND_NAMESPACE_AUDIT.json', dict(status='PASS_RESERVED_BEFORE_DRAWS',
        original_saved_states=4064, prior_independent_states=6000, identity_registry_count=10064,
        prior_cohorts=namespaces, new_seed=SAMPLE_SEED, bootstrap_seed=BOOT_SEED,
        prior_validation_outcomes_read=False, actual_damage_duration_identities_verified=True,
        namespace='post_elitism_ga_fixed2000_20261012', entropy_rule=[SAMPLE_SEED, 'r']))
    sampling = v.sampling_audit(model['frozen'], REVISION)
    sampling['rng_specification'] = f'PCG64/default_rng(SeedSequence([{SAMPLE_SEED},r])), r=0..1999'
    v.write(OUT / 'SAMPLING_SOURCE_AUDIT.json', sampling)
    v.write(OUT / 'FIXED_STRATEGY_IDENTITIES.json', dict(strategies=strategies,
        station_universe=model['ids'], sequence_hash_rule='UTF8 newline-joined IDs with final newline',
        planning64_verified_candidate=True, warm_start_GA_excluded=True,
        new_searches=0, source_commit=PARENT))
    authorization = dict(status='AUTHORIZED_AND_FROZEN_BEFORE_FIRST_DRAW',
        human_request='Latest direct user instruction: Independent Physical Validation of the Revised GA Elitism; sections 4,5,6,8,15 explicitly authorize exactly 2000 NEW shared physical realizations and 6000 fixed-policy evaluations, commit and push.',
        recorded_utc=datetime.now(timezone.utc).isoformat(), source_commit=PARENT, branch=BRANCH,
        strategies=strategies, sample_size=2000, production_evaluations=6000,
        hazard='2pc50', resource='C57_D1', stations=92, edges=318, Core_sources=14,
        gate_threshold=.5, horizon_hr=480, scientific_context=model['context_hashes'],
        sampling=dict(namespace='post_elitism_ga_fixed2000_20261012', seed=SAMPLE_SEED,
                      entropy_rule=[SAMPLE_SEED,'r'], generator='PCG64', sampler_source_audit_sha256=v.sha(OUT / 'SAMPLING_SOURCE_AUDIT.json')),
        bootstrap=dict(resamples=20000, seed=BOOT_SEED, unit='complete paired physical realization',
            shared_indices_all_policies_and_metrics=True, pointwise_percentiles=[.025,.975],
            population_two_contrast_Bonferroni_percentiles=[.0125,.9875]),
        primary='Revised GA minus Impact-first: population-weighted normalized loss over0-480h',
        secondary_population='Revised GA minus previous PURE-RANDOM GA, not warm-start GA',
        descriptive_metrics=list(v.METRICS), descriptive_intervals='pointwise only; no equivalence/noninferiority claims',
        T80='First native-event population availability crossing0.8; unreached=restricted480h plus explicit censor flag',
        hospital='Unweighted mean normalized burden of frozen hospital-associated tracts; not facility electricity or patient outcomes',
        equity='Original frozen SOVI quartiles; population-weighted Q1-Q4 burden, signed and mean absolute Q4-Q1, pop-weighted tract Gini',
        curves='0..480 hourly presentation samples from verified native trajectories; not numerical integration',
        influence='Untrimmed full-cohort primary; descriptive leave-one-out and remove most favorable1%,5%,10% only to disclose concentration, never replacement estimators',
        mechanism='Exact signed component differences; source connected dependency mass and every positive reconnection event; no single-station causal attribution',
        decision_rule='Support author review only if both population-contrast simultaneous95 upper limits are negative and none of hospital burden, restrictedT80, absoluteQ4-Q1 or Gini has an entirely adverse descriptive95 interval versus previous GA. Otherwise retain prior. Unresolved secondary intervals do not establish equivalence or absence of harm; report medians, tails and adverse frequencies regardless.',
        optimizer_invocations=0, tuning=False, reselection=False, optional_stopping=False,
        allow_failed_case_exclusion=False, allow_sample_expansion=False, formal_strategy_promotion=False,
        runtime_files_sha256=runtime, frozen_algorithm=dict(population=100,random_initial_permutations=100,
            OX=.80,swap=.10,tournament=3,elite=1,independent_runs=20,distinct_evaluations_per_run=100000),
        optimizer_superiority_statistically_established=False,
        preexisting_external_exception=current['preexisting_external_exception'])
    v.write(OUT / 'AUTHORIZATION_AND_EXECUTION_FREEZE.json', authorization)
    local_names = ['study.py', 'analyze.py', 'publish.py', 'FIXED_STRATEGY_IDENTITIES.json',
                   'PLANNING64_PRODUCTION_QA_REUSED.json', 'SEED_AND_NAMESPACE_AUDIT.json',
                   'SAMPLING_SOURCE_AUDIT.json', 'PRIOR_PHYSICAL_RECEIPT_HASHES.json']
    f = dict(runtime=v.runtime(),runtime_files_sha256=runtime,
        local_files_sha256={n:v.sha(OUT / n) for n in local_names},
        authorization_sha256=v.sha(OUT / 'AUTHORIZATION_AND_EXECUTION_FREEZE.json'),
        previous_registry_sha256=v.sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json'),
        strategies=strategies, sampling_namespace=authorization['sampling']['namespace'],
        sample_size=2000,horizon_hr=480,workers=8,
        protected_revision_checkout=str(REVISION),old_validation_checkout=str(ROOT.parent/'_val4'),source_checkout=str(SOURCE))
    v.write(OUT / 'EXECUTION_FREEZE.json', f)
    verify()
    print('FREEZE_PASS; previous identities10064; no new draws; no optimizer', flush=True)


def engineering():
    configure()
    a.engineering()
    report = v.read(OUT / 'ENGINEERING_QA.json')
    report.update(previous_engineering_failures=[], extra_failed_attempt_production_calls=0,
                  extra_failed_attempt_completed_kernel_calls=0,
                  reused_function='standalone_ils_validation_analysis_20261011.engineering')
    v.write(OUT / 'ENGINEERING_QA.json', report)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['setup','engineering','verify','execute','preservation'])
    args = p.parse_args()
    configure()
    if args.phase == 'setup': setup()
    elif args.phase == 'engineering': engineering()
    elif args.phase == 'verify': verify(); print('FREEZE_HASHES_PASS', flush=True)
    elif args.phase == 'preservation':
        assert preserved() == v.read(OUT / 'PRESERVATION_BASELINE.json')
        print('PRESERVATION_PASS950_FILES862_STAGED_WITH_DISCLOSED_EXCEPTION', flush=True)
    else: q.execute()
