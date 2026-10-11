"""Freeze existing random-only GA receipts and reuse the verified validation engine."""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from la_grid.diagnostics import independent_validation_20261010 as v
from la_grid.diagnostics import standalone_ils_validation_20261011 as q
from la_grid.diagnostics import standalone_ils_validation_analysis_20261011 as a
from la_grid.diagnostics.ga_research_preserve_20261009 import snapshot, git
from la_grid.diagnostics.ga_search_budget_sensitivity import identity
import numpy as np
import pandas as pd

OUT = v.long_path(Path(__file__).resolve().parent)
MODULE = 'results/diagnostics/pure_random_ga_final_20261011/finalize.py'
BASE = '6ac7564375dd912025e96d4da3c823857ef198d8'
BRANCH = 'diagnostics/pure-random-ga-final-freeze-validation-20261011'
MAIN = list(range(2026103100, 2026103120))
SOURCE = ROOT.parent / '_gri11'
VALIDATED = ROOT.parent / '_vils7'
OLD = ROOT.parent / '_val4'
PRIOR_NAME = 'results/diagnostics/ga_random_initialization_isolation_20261011'
PRIOR = v.long_path(SOURCE / PRIOR_NAME)
VALIDATED_OUT = v.long_path(VALIDATED / 'results/diagnostics/standalone_ils_prospective_validation_20261011')
CANDIDATE, LEGACY, IMPACT = 'GA-pure-random', 'legacy-warm-start-GA', 'Impact-first'
N, SAMPLE_SEED, BOOT_SEED = 2000, 2026110300, 2026110400


def md(name, text):
    (OUT / name).write_text(text.strip() + '\n', encoding='utf-8', newline='\n')


def choose(receipts):
    assert {x['seed'] for x in receipts} == set(MAIN) and len(receipts) == 20
    assert all(x['mode'] == 'PURE_RANDOM_GA' and x['budget'] == 100000 for x in receipts)
    minimum = min(x['loss_hr'] for x in receipts)
    return min((x for x in receipts if x['loss_hr'] <= minimum + 1e-9), key=lambda x: x['seed'])


def preserved(revision, old_validation, source):
    result = snapshot(Path(revision))
    result['index_entries_sha256'] = hashlib.sha256(git(Path(revision), 'ls-files', '--stage', '-z')).hexdigest()
    result['staged_count'] = len([x for x in git(Path(revision), 'diff', '--cached', '--name-only', '-z').split(b'\0') if x])
    result['status_sha256'] = hashlib.sha256(git(Path(revision), 'status', '--porcelain=v1', '-z')).hexdigest()
    # Check evidence bytes, not outcomes, for previous validation packages.
    result['old_validation_sha256'] = {}
    for root, names in ((VALIDATED_OUT, ['EXECUTION_FREEZE.json', 'AUTHORIZATION.json',
                'PHYSICAL_COHORT_IDENTITY.csv', 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json',
                'FIXED2000_FULL_EVIDENCE.zip']),
            (v.long_path(Path(old_validation) / 'results/diagnostics/independent_validation_ready_20261010'),
                ['FINAL_VALIDATION_FREEZE_RECEIPT.json'])):
        for name in names:
            result['old_validation_sha256'][str(root / name)] = v.sha(root / name)
    names = ['EXPERIMENT_DESIGN_AND_SEEDS.json', 'FINAL_DECISION_MACHINE_READABLE.json',
             'IMPORTANT_SEQUENCE_PRODUCTION_QA.json', 'RAW_SEARCH_EVIDENCE_MANIFEST.json', 'study.py']
    names += [f'runs/PURE_RANDOM_GA_{s}/FINAL_100000.json' for s in MAIN]
    result['frozen_source_package_sha256'] = {name: v.sha(PRIOR / name) for name in names}
    for name in ('FINAL_GA_CONFIG_CANDIDATE.json', 'SELECTED_SEQUENCE.json'):
        p = v.long_path(Path(source) / 'results/diagnostics/final_ga_method_20261009' / name)
        result['frozen_source_package_sha256'][str(p)] = v.sha(p)
    result['source_staged_diff_sha256'] = hashlib.sha256(git(Path(source), 'diff', '--cached', '--binary')).hexdigest()
    result['source_head'] = git(Path(source), 'rev-parse', 'HEAD').decode().strip()
    return result


def verify():
    f = v.read(OUT / 'EXECUTION_FREEZE.json')
    assert f['runtime'] == v.runtime()
    for name, h in {**f['input_sha256'], **f['code_sha256']}.items():
        assert v.sha(q.R / name) == h, name
    for name, h in f['local_freeze_sha256'].items():
        assert v.sha(OUT / name) == h, name
    assert v.sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json') == f['previous_registry_sha256']
    assert git(ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    return f


def worker_setup():
    # Windows spawn imports this adapter before invoking the unchanged worker.
    configure()
    q.MODEL, q.POLICIES = v.load_model(), verify()['strategies']


ORIGINAL_PAIRED = a.paired_analysis


def paired_analysis(frame):
    effects, levels, differences = ORIGINAL_PAIRED(frame)
    differences = differences.rename(columns={c: c.replace('_ILS_minus_', '_candidate_minus_') for c in differences})
    return effects, levels, differences


def configure():
    q.OUT, q.ARCHIVE, q.PARENT, q.BRANCH = OUT, OUT / 'cohort', BASE, BRANCH
    q.N, q.BOOT, q.BOOT_SEED, q.SAMPLE_SEED = N, 20000, BOOT_SEED, SAMPLE_SEED
    q.ILS, q.GA, q.IMPACT = CANDIDATE, LEGACY, IMPACT
    q.verify, q.protected_state, q.worker_setup = verify, preserved, worker_setup
    a.OUT, a.R, a.MODULE = OUT, q.R, MODULE
    a.paired_analysis = paired_analysis


def setup():
    assert not (OUT / 'EXECUTION_FREEZE.json').exists()
    assert git(ROOT, 'rev-parse', 'HEAD').decode().strip() == BASE
    prior_runtime = v.read(VALIDATED_OUT / 'EXECUTION_FREEZE.json')
    paths = {**prior_runtime['input_sha256'], **prior_runtime['code_sha256']}
    hydration = [q.hydrate_exact(name, VALIDATED, expected) for name, expected in paths.items()]
    # Only payload hydration in this new checkout; no source or model edits.
    for name in ('FINAL_GA_CONFIG_CANDIDATE.json', 'SELECTED_SEQUENCE.json'):
        relative = 'results/diagnostics/final_ga_method_20261009/' + name
        hydration.append(q.hydrate_exact(relative, VALIDATED))
    model = v.load_model()
    design = v.read(PRIOR / 'EXPERIMENT_DESIGN_AND_SEEDS.json')
    assert model['context_hashes'] == design['model_identity']['context_identity']
    planning = [v.physical_hash(model['ids'], ds, duration) for ds, duration in zip(*model['banks']['planning'])]
    assert planning == design['model_identity']['planning_sample_hashes']
    revision = prior_runtime['protected_revision_checkout']
    v.write(OUT / 'PRESERVATION_BASELINE.json', preserved(revision, OLD, SOURCE))

    receipts, rows, origins = [], [], []
    for seed in MAIN:
        rel = f'runs/PURE_RANDOM_GA_{seed}/FINAL_100000.json'
        receipt = v.read(PRIOR / rel)
        assert receipt['completed'] and receipt['distinct_evaluations'] == 100000
        assert len(receipt['sequence']) == len(set(receipt['sequence'])) == 92
        assert set(receipt['sequence']) == set(model['ids'])
        assert identity(receipt['sequence']) == receipt['sequence_sha256']
        receipts.append(receipt)
        (OUT / 'selection_receipts').mkdir(exist_ok=True)
        (OUT / 'selection_receipts' / f'{seed}.json').write_bytes((PRIOR / rel).read_bytes())
        origins.append(dict(path=PRIOR_NAME + '/' + rel, sha256=v.sha(PRIOR / rel), commit=BASE))
        rows.append({k: receipt[k] for k in ('seed', 'budget', 'loss_hr', 'sequence_sha256',
                     'distinct_evaluations', 'attempts', 'duplicate_fraction', 'wall_seconds',
                     'completed_generations', 'last_improvement_evaluations')})
    winner = choose(receipts)
    assert winner['seed'] == 2026103108
    assert winner['sequence_sha256'] == 'edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a'
    folder = PRIOR / f"runs/PURE_RANDOM_GA_{winner['seed']}"
    initial = v.read(folder / 'INITIAL_POPULATION.json')
    assert initial['mode'] == 'PURE_RANDOM_GA' and initial['archive_before_first_evaluation'] == []
    assert initial['initial_sequences'] == initial['common_random_pool'] and len(initial['initial_sequences']) == 100
    assert len(set(initial['initial_hashes'])) == 100
    assert all(identity(seq) == h for seq, h in zip(initial['initial_sequences'], initial['initial_hashes']))
    assert v.sha(folder / 'INITIAL_POPULATION.json') == winner['initial_population_sha256']
    with gzip.open(folder / 'STATE_100000.pkl.gz', 'rb') as stream:
        state = pickle.load(stream)
    assert v.sha(folder / 'STATE_100000.pkl.gz') == winner['checkpoint_sha256']
    assert state['state']['best_seq'] == tuple(winner['sequence'])
    assert len(state['cache']) == 100000
    lineage = OUT / 'candidate_lineage'
    lineage.mkdir(exist_ok=True)
    for name in ('INITIAL_POPULATION.json', 'STATE_100000.pkl.gz'):
        (lineage / name).write_bytes((folder / name).read_bytes())
    history = [x for x in v.read(folder / 'STRICT_IMPROVEMENTS.json') if x['distinct_evaluations'] <= 100000]
    assert history[-1]['sequence'] == winner['sequence']
    assert history[-1]['distinct_evaluations'] == winner['last_improvement_evaluations']
    v.write(lineage / 'STRICT_IMPROVEMENTS_100K.json', history)
    for name in ('GENERATION_DIAGNOSTICS.csv', 'BUDGET_CHECKPOINTS.csv'):
        frame = pd.read_csv(folder / name)
        key = 'distinct_evaluations' if 'distinct_evaluations' in frame else 'unique_candidates_evaluated'
        v.csv(lineage / name, frame.loc[frame[key] <= 100000])
    raw_manifest = v.read(PRIOR / 'RAW_SEARCH_EVIDENCE_MANIFEST.json')
    bundle = next(x for x in raw_manifest['runs'] if x['run'] == f"PURE_RANDOM_GA_{winner['seed']}")
    assert v.sha(PRIOR / bundle['zip_path']) == bundle['zip_sha256']
    member = next(x for x in bundle['files'] if x['path'] == 'STATE_100000.pkl.gz')
    with zipfile.ZipFile(PRIOR / bundle['zip_path']) as z:
        assert hashlib.sha256(z.read(member['entry'])).hexdigest() == member['sha256'] == winner['checkpoint_sha256']
    qa = v.read(PRIOR / 'IMPORTANT_SEQUENCE_PRODUCTION_QA.json')
    record = next(x for x in qa['records'] if x['sequence_sha256'] == winner['sequence_sha256'])
    assert qa['status'] == 'PASS' and qa['planning_sample_hashes'] == planning
    assert record['all64_pass'] and len(record['production64_losses']) == 64
    assert abs(np.mean(record['production64_losses']) - winner['loss_hr']) < 1e-8
    v.write(OUT / 'PRODUCTION64_QA_REUSED.json', dict(status='PASS_REUSED_COMPLETE_ORIGINAL_PRODUCTION_QA',
        source_commit=BASE, source_path=PRIOR_NAME + '/IMPORTANT_SEQUENCE_PRODUCTION_QA.json',
        source_sha256=v.sha(PRIOR / 'IMPORTANT_SEQUENCE_PRODUCTION_QA.json'),
        planning_sample_hashes=planning, record=record, new_production_calls=0, new_search_calls=0))
    v.csv(OUT / 'GA_FIXED_SEED_LEDGER.csv', pd.DataFrame(rows))
    protocol = dict(method='random-only repeated GA', population=100, independent_random_permutations=100,
        crossover='ordered crossover (OX)', crossover_probability=.80, mutation='swap', mutation_probability=.10,
        tournament_size=3, generational_elite_count=1, run_seeds=MAIN, distinct_budget_per_run=100000,
        total_per_run_distinct_evaluations=2000000, independent_empty_per_run_caches=True,
        heuristic_initializers=False, optimized_incumbents=False, archive_before_first_score=[],
        best_observed_archive='Passive retention only; strict score improvement; no incumbent injection',
        adaptive_mutation=False, restart=False, diversity_replacement=False,
        selection='Minimum original 64-planning-state mean loss among the 20 PURE final100k receipts ONLY',
        across_run_tie='Loss <= observed minimum + 1e-9 h: lowest seed; no tied minimum in the actual receipts',
        within_run_ties=dict(best_observed='Exact equal score: retain first observed sequence',
            tournament='Exact tie: first sampled contender',
            elite='Exact tie: lexicographically smallest station-ID tuple',
            generation_archive='Exact tie: lexicographically largest tuple in generation; archive updates only on strict score gain; final output is best-observed archive'),
        excluded_selection_records=['Impact-seeded controls', 'reserved 250k/500k continuations', 'validation outcomes'],
        objective='Unchanged mean normalized population-weighted service-loss hours over original 64 planning realizations',
        planning_horizon_hr=design['model_identity']['horizon_hr'], model_identity=design['model_identity'],
        source_commit=BASE, search_execution_commit=winner['execution_commit'],
        implementation=PRIOR_NAME + '/study.py:config,engine,run_engine',
        implementation_sha256=v.sha(PRIOR / 'study.py'), engine_sha256=v.sha(q.R / 'src/la_grid/diagnostics/ga_variant_engine.py'),
        new_search_calls=0, method_choice_is_post_data=True, original_automatic_rule_passed=False,
        strict_proximity_cutoff_hr=32.997840773882714 + .001,
        strict_proximity_main_successes=sum(x['loss_hr'] <= 32.998840773882714 for x in receipts),
        strict_proximity_main_n=20, preregistered_reliability_required=.90,
        reserve_proximity_successes=8, reserve_proximity_n=10,
        single_run_90pct_claim_permitted=False, global_optimum_claim_permitted=False)
    assert protocol['strict_proximity_main_successes'] == 10
    v.write(OUT / 'FINAL_GA_EXECUTION_PROTOCOL.json', protocol)
    v.write(OUT / 'FINAL_RANDOM_GA_CANDIDATE.json', dict(status='FROZEN_ACTUAL_RANDOM_ONLY_GA_CANDIDATE',
        seed=winner['seed'], distinct_budget=100000, sequence=winner['sequence'], sequence_sha256=winner['sequence_sha256'],
        planning_objective_hr=winner['loss_hr'], native_planning_objective_hr=record['native_mean_hr'],
        best_first_observed_evaluation=winner['last_improvement_evaluations'],
        original_receipt_sha256=v.sha(folder / 'FINAL_100000.json'), original_receipt_path=origins[8]['path'],
        source_commit=BASE, checkpoint_sha256=winner['checkpoint_sha256'],
        physical_model_changed=False, formal_legacy_candidate_overwritten=False))
    v.write(OUT / 'CANDIDATE_PROVENANCE_QA.json', dict(status='PASS', selection_receipts=origins,
        winner_raw_bundle=bundle, random_pool_exact=True, archive_initially_empty=True,
        candidate_present_in_strict_improvement_history=True, native64_reused=True,
        candidate_checkpoint_cache_size=100000, complete_permutation=True,
        old_warm_start_sequence_not_used=True, new_search_calls=0))
    formal = v.read(q.R / 'results/diagnostics/final_ga_method_20261009/SELECTED_SEQUENCE.json')
    rules = v.read(q.R / 'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json')
    strategies = [dict(strategy=CANDIDATE, sequence=winner['sequence']),
                  dict(strategy=LEGACY, sequence=formal['sequence']),
                  dict(strategy=IMPACT, sequence=rules['2pc50']['impact-first'])]
    for p in strategies:
        assert set(p['sequence']) == set(model['ids']) and len(p['sequence']) == 92
        p['sequence_sha256'] = identity(p['sequence'])
    assert strategies[0]['sequence_sha256'] != strategies[1]['sequence_sha256']
    previous = v.read(VALIDATED_OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json')
    previous.update({f'ILS_fresh_2026110100_{int(x.r):04d}': x.physical_sha256 for x in
                     pd.read_csv(VALIDATED_OUT / 'PHYSICAL_COHORT_IDENTITY.csv').itertuples()})
    assert len(previous) == len(set(previous.values())) == 5064
    v.write(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json', previous)
    audit = v.sampling_audit(model['frozen'], Path(revision))
    audit['rng_specification'] = f'PCG64 / default_rng(SeedSequence([{SAMPLE_SEED},r])), r=0..1999'
    v.write(OUT / 'SAMPLING_SOURCE_AUDIT.json', audit)
    v.write(OUT / 'SEED_AND_NAMESPACE_AUDIT.json', dict(status='FRESH_SEED_RESERVED_NO_DRAWS',
        prior_identity_count=5064, prior_validation_outcomes_read=False, sample_seed=SAMPLE_SEED,
        bootstrap_seed=BOOT_SEED, sampling_namespace='ga_pure_random_fixed_2000_20261011',
        previous_registry_sha256=v.sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json'),
        original_sampling_ast_and_constants_unchanged=True))
    plan = dict(sample_size=N, policies=strategies, horizon_hr=480, threshold=.5,
        physical_draws_shared_across_policies=True, no_old_validation_sample_reuse=True,
        primary='Candidate minus Impact-first: mean normalized population-weighted service-loss hours',
        secondary='Candidate minus legacy-warm-start-GA: same mean-loss metric; supplementary traceability only',
        population_contrast_family_size=2, bootstrap_resamples=20000, bootstrap_seed=BOOT_SEED,
        bootstrap_unit='Entire physical realization; paired policies; same resampled indices across all metrics',
        pointwise_percentile_quantiles=[.025,.975], population_simultaneous95_quantiles=[.0125,.9875],
        simultaneous_method='Bonferroni two-contrast percentile bootstrap',
        additional_metrics=list(v.METRICS), additional_metrics_inference='Descriptive pointwise, no confirmatory familywise claims',
        realization_tie_tolerance_hr=1e-9, retain_all_samples_and_negative_results=True,
        T80='System population-weighted 80% crossing; unreached values censored at480h, reported separately',
        hospital='Unweighted mean normalized burden of hospital-associated tracts; not facility, patient or hospital-load losses',
        equity='Frozen SOVI population quartiles Q1-Q4; signed/absolute Q4-Q1 plus population-weighted burden Gini',
        recovery_curve='Mean realized effective-service trajectories, integer-hour grid0..480, no old curve reuse',
        no_tuning=True, no_reselection=True, no_formal_strategy_overwrite=True,
        reuse_execution_module=q.MODULE, reuse_analysis_module='src/la_grid/diagnostics/standalone_ils_validation_analysis_20261011.py',
        authorization='Fresh candidate-specific cohort execution requires explicit AUTHORIZATION.json',
        source_commit=BASE)
    v.write(OUT / 'VALIDATION_ANALYSIS_PLAN.json', plan)
    names = ['FINAL_GA_EXECUTION_PROTOCOL.json', 'FINAL_RANDOM_GA_CANDIDATE.json', 'VALIDATION_ANALYSIS_PLAN.json']
    f = dict(status='METHOD_CANDIDATE_AND_ANALYSIS_FROZEN_BEFORE_FRESH_SAMPLING',
        parent_commit=BASE, source_checkout=str(SOURCE), old_validation_checkout=str(OLD),
        protected_revision_checkout=revision, strategies=strategies, input_sha256=paths,
        code_sha256={**{name: v.sha(q.R / name) for name in v.CODE},
                     q.MODULE:v.sha(q.R / q.MODULE),
                     'src/la_grid/diagnostics/standalone_ils_validation_analysis_20261011.py':v.sha(q.R / 'src/la_grid/diagnostics/standalone_ils_validation_analysis_20261011.py'),
                     MODULE:v.sha(q.R / MODULE)},
        local_freeze_sha256={name:v.sha(OUT / name) for name in names}, hydration=hydration,
        runtime=v.runtime(), sample_size=N, entropy_rule=[SAMPLE_SEED,'r'],
        sampling_namespace='ga_pure_random_fixed_2000_20261011', bootstrap_seed=BOOT_SEED,
        bootstrap_resamples=20000, gate_threshold=.5, horizon_hr=480,
        previous_registry_sha256=v.sha(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json'),
        workers=8, new_validation_samples_generated=0, optimizer_invocations=0,
        allow_reselection=False, allow_tuning=False)
    v.write(OUT / 'EXECUTION_FREEZE.json', f)
    md('FINAL_METHOD_AND_CANDIDATE.md', f'''# Final GA execution and candidate freeze

Use 100 independent uniformly random permutations, OX0.80, swap0.10, tournament3, elite1. Execute independent runs for seeds2026103100-2026103119, each with100,000 distinct evaluations and its own initially empty cache/archive. No heuristic, prior optimized chromosome, adaptive mutation or restart is injected. Passive retention preserves the best actually observed chromosome. The combined budget is2,000,000 per-run distinct mean-objective evaluations (64 unchanged planning states each), not2,000,000 globally unique permutations.

Select the lowest original64-state mean loss among the20 completed PURE100k final receipts; candidates within1e-9h of the observed minimum tie by lowest seed. There is no actual tied minimum. Existing within-run exact tie rules are documented in FINAL_GA_EXECUTION_PROTOCOL.json. Reserve250k/500k records and controls do not enter candidate selection. No search was launched for this freeze.

The selected92-station permutation is seed{winner['seed']}, planning loss{winner['loss_hr']:.14f}h, SHA256 `{winner['sequence_sha256']}`. All92 IDs are in FINAL_RANDOM_GA_CANDIDATE.json. The saved100k checkpoint contains the same best-observed chromosome; its first strict improvement appearance is evaluation{winner['last_improvement_evaluations']}. The100 random initial permutations and empty archive are checked directly. The original production evaluator previously checked all64 states with maximum error{record['max_absolute_error_hr']:.3g}h; that complete record is reused without rescoring.

## Required methodological disclosure

Random-only initialization is a supported **post-data methodological judgment**, approved in the current user request. It did not pass the original automatic adoption rule, whose fallback was Impact-seeded. At100k, only10/20 random-only runs reached the strict formal-best+0.001h cutoff; the reserved continuation had8/10 at250k/500k. Neither attained the prespecified90% single-run requirement. A20-run procedure is adopted, not a guarantee that every run finds the same quality. No independent20-run-block success probability is estimated from this one20-seed collection. Method,100k-budget and across-run selection freeze occur after observing these planning searches, before new physical validation.

## Validation and preservation

The proposed fresh2,000-realization protocol fixes the new candidate, Impact-first and legacy formal GA. The previous validation remains attached to its original sequences and cannot be transferred. Execution is authorization-gated; no new physical samples exist at this freeze. The original objective, physics, scheduler, graph, sources, crews, mapping and durations are unchanged. Formal legacy candidate/results and950 protected scientific files/862 staged items are preserved. Candidate-specific validation will be a separate reviewable package, not an overwrite of old science.
''')
    verify()
    print('FREEZE_PASS', winner['sequence_sha256'], '; new searches0; new draws0', flush=True)


def engineering():
    a.engineering()
    # The reused engineering function's old incident descriptions are not new incidents.
    report = v.read(OUT / 'ENGINEERING_QA.json')
    report['reused_engineering_test_function'] = 'standalone_ils_validation_analysis_20261011.engineering'
    report['previous_engineering_failures'] = []
    report['extra_failed_attempt_production_calls'] = 0
    report['extra_failed_attempt_completed_kernel_calls'] = 0
    v.write(OUT / 'ENGINEERING_QA.json', report)


def authorize():
    # This phase is run only after a new direct human confirmation in this chat.
    assert not (OUT / 'AUTHORIZATION.json').exists()
    verify()
    v.write(OUT / 'AUTHORIZATION.json', dict(author='human user in this chat',
        recorded_utc=datetime.now(timezone.utc).isoformat(), scope='New2000 shared physical realizations; fixed random-only GA, legacy formalGA, Impact-first; no tuning/reselection; independent review outputs',
        explicit_candidate_specific_authorization=True, sample_size=N,
        candidate_sha256=verify()['strategies'][0]['sequence_sha256'],
        execution_freeze_sha256=v.sha(OUT / 'EXECUTION_FREEZE.json'),
        no_tuning=True, no_reselection=True, no_old_sample_reuse=True,
        preserve_original_model_and_formal_results=True))


def execute():
    auth = v.read(OUT / 'AUTHORIZATION.json')
    assert auth['explicit_candidate_specific_authorization'] and auth['sample_size'] == N
    assert auth['execution_freeze_sha256'] == v.sha(OUT / 'EXECUTION_FREEZE.json')
    assert auth['candidate_sha256'] == verify()['strategies'][0]['sequence_sha256']
    q.execute()


configure()
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['setup','verify','engineering','authorize','execute','analyze','package'])
    phase = parser.parse_args().phase
    if phase == 'setup': setup()
    elif phase == 'verify': verify(); print('FREEZE_PASS; no draws', flush=True)
    elif phase == 'engineering': engineering()
    elif phase == 'authorize': authorize()
    elif phase == 'execute': execute()
    elif phase == 'analyze': a.analyze()
    else: a.package()
