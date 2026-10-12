"""Read archived observations only; produce a separate S05 review candidate."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote
import zipfile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
REL = OUT.relative_to(ROOT).as_posix()
BRANCH = 'review/final-pure-random-ga-figs05-20261012'
REPO = 'yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale'
REVISION = Path(r'C:\2025-2026 Fall\CY PLAN C257H (CIV ENG C263H) - Human Mobility and Network Science\Project\LA_grid_reviewer_revision')
SEEDS = list(range(2026103100, 2026103120))
SELECTED = 2026103108
CANDIDATE_HASH = 'edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a'
SOURCES = {
    'final': ('_gaf12', 'f539e3fe6015122d73e5656109e751770550bb70', 'diagnostics/pure-random-ga-final-freeze-validation-20261011'),
    'parameters': ('_gpc13', '3da06ca6b9d5bb55d179ff1ff7bdcae583b2f231', 'diagnostics/pure-random-ga-parameter-consistency-20261011'),
    'initialization': ('_gri11', '6ac7564375dd912025e96d4da3c823857ef198d8', 'diagnostics/ga-random-initialization-isolation-20261011'),
    'later_validation': ('_gev15', '1910fbe7edafdfdf100f679ccb56060a98456e1f', 'diagnostics/post-evaluation-ga-independent-validation-20261012'),
    'manuscript_remote': ('_s05r16', 'c0a11ffb4df523111efe6c8e65cfe86eadffec3c', 'revision/reviewer-driven-core-rebuild-v2'),
}
FINAL = 'results/diagnostics/pure_random_ga_final_20261011'
RUNS = 'results/diagnostics/ga_random_initialization_isolation_20261011'
POST = 'results/diagnostics/post_elitism_ga_independent_validation_20261012'
SOURCE_RECORDS = []
RAW = {}


def lp(path):
    p = Path(path).resolve()
    return Path('\\\\?\\' + str(p)) if os.name == 'nt' and not str(p).startswith('\\\\?\\') else p


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with lp(path).open('rb') as stream:
        for block in iter(lambda: stream.read(2**20), b''):
            h.update(block)
    return h.hexdigest()


def git(root, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    return subprocess.check_output(['git', '-c', 'filter.lfs.process=', '-c',
        'filter.lfs.smudge=', '-c', 'filter.lfs.required=false', *args], cwd=root, env=env)


def write(name, data):
    p = lp(OUT / name)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        p.write_bytes(data)
    else:
        p.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def read(name):
    return json.loads(lp(OUT / name).read_text(encoding='utf-8'))


def csv(name, rows):
    pd.DataFrame(rows).to_csv(lp(OUT / name), index=False, float_format='%.17g')


def source(key, name):
    folder, commit, branch = SOURCES[key]
    root = ROOT.parent / folder
    blob = git(root, 'show', commit + ':' + name)
    oid = None
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1'):
        fields = dict(x.split(' ', 1) for x in blob.decode().splitlines())
        oid = fields['oid'][7:]
        common = Path(git(root, 'rev-parse', '--git-common-dir').decode().strip())
        if not common.is_absolute():
            common = root / common
        cached = lp(common / 'lfs/objects' / oid[:2] / oid[2:4] / oid)
        actual = lp(root / name)
        if cached.exists():
            blob = cached.read_bytes()
        elif actual.exists() and digest(actual) == oid:
            blob = actual.read_bytes()
        else:
            import requests
            url = f'https://media.githubusercontent.com/media/{REPO}/{commit}/' + quote(name, safe='/')
            response = requests.get(url, timeout=180)
            response.raise_for_status()
            blob = response.content
        assert sha(blob) == oid and len(blob) == int(fields['size']), name
    SOURCE_RECORDS.append(dict(source=key, branch=branch, commit=commit, path=name,
        original_url=f'https://github.com/{REPO}/blob/{commit}/{quote(name, safe="/")}',
        sha256=sha(blob), bytes=len(blob), git_lfs_oid=oid,
        archive_member=key + '/' + name))
    RAW[key + '/' + name] = blob
    return blob


def source_json(key, name):
    return json.loads(source(key, name))


def preserved():
    # Reuse only the read-only snapshot utility, never a model or search entrypoint.
    sys.path.insert(0, str(ROOT.parent / '_gaf12/src'))
    from la_grid.diagnostics.ga_research_preserve_20261009 import snapshot
    state = snapshot(REVISION)
    state['index_entries_sha256'] = sha(git(REVISION, 'ls-files', '--stage', '-z'))
    state['staged_count'] = len([x for x in git(REVISION, 'diff', '--cached', '--name-only', '-z').split(b'\0') if x])
    state['status_sha256'] = sha(git(REVISION, 'status', '--porcelain=v1', '-z'))
    assert len(state['files_sha256']) == 950 and state['staged_count'] == 862
    paths = ['results/figure_review/Supplement/FigS05.pdf', 'results/figure_review/Supplement/FigS05.png',
             'results/figures/FigS05_GA_Reproducibility.pdf', 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md']
    state['original_S05_sha256'] = {name: digest(REVISION / name) for name in paths}
    state['source_checkouts'] = {}
    for key, (folder, _, _) in SOURCES.items():
        if key == 'manuscript_remote':
            continue
        root = ROOT.parent / folder
        state['source_checkouts'][key] = dict(head=git(root, 'rev-parse', 'HEAD').decode().strip(),
            branch=git(root, 'branch', '--show-current').decode().strip(),
            staged_diff_sha256=sha(git(root, 'diff', '--cached', '--binary')),
            index_entries_sha256=sha(git(root, 'ls-files', '--stage', '-z')),
            status_sha256=sha(git(root, 'status', '--porcelain=v1', '-z')))
    missing = REVISION.parent / 'LA_grid_manuscript_rebuild/LA_Grid_Manuscript_Resubmission_Rebuild.docx'
    backup = Path(r'C:\2025-2026 Fall\Local_Recovery_Snapshot_20260925\Private_Backup_Small\private-la-grid-research\manuscripts\LA_Grid_Manuscript_Resubmission_Rebuild.docx')
    state['preexisting_external_exception'] = dict(path=str(missing), exists=missing.exists(),
        backup_path=str(backup), backup_sha256=digest(backup), restored=False, designated_authoritative=False)
    assert not missing.exists()
    assert state['preexisting_external_exception']['backup_sha256'] == 'a61472ed6918f505dfd0c26b88ce24f9d184f6dca076194b5032014142acd253'
    return state


def prepare():
    assert git(ROOT, 'branch', '--show-current').decode().strip() == BRANCH
    assert git(ROOT, 'rev-parse', 'HEAD').decode().strip() == SOURCES['manuscript_remote'][1]
    current = preserved()
    if lp(OUT / 'PRESERVATION_BASELINE.json').exists():
        assert current == read('PRESERVATION_BASELINE.json')
    else:
        write('PRESERVATION_BASELINE.json', current)
    remote_rows = []
    for key, (folder, commit, branch) in SOURCES.items():
        root = ROOT.parent / folder
        local = git(root, 'rev-parse', 'HEAD').decode().strip()
        remote = git(root, 'ls-remote', 'origin', 'refs/heads/' + branch).decode().split()[0]
        assert remote == commit and local == commit
        remote_rows.append(dict(source=key, local_head=local, remote_head=remote, branch=branch))
    write('SOURCE_BRANCH_IDENTITIES.json', dict(sources=remote_rows,
        protected_local_revision_head=git(REVISION, 'rev-parse', 'HEAD').decode().strip(),
        protected_local_revision_not_advanced=True, isolated_base=SOURCES['manuscript_remote'][1]))
    protocol = source_json('final', FINAL + '/FINAL_GA_EXECUTION_PROTOCOL.json')
    candidate = source_json('final', FINAL + '/FINAL_RANDOM_GA_CANDIDATE.json')
    seq = candidate['sequence']
    assert len(seq) == len(set(seq)) == 92
    assert sha(('\n'.join(seq) + '\n').encode()) == CANDIDATE_HASH == candidate['sequence_sha256']
    assert candidate['seed'] == SELECTED and candidate['planning_objective_hr'] == 32.99552241352315
    assert protocol['run_seeds'] == SEEDS and protocol['method_choice_is_post_data']
    assert not protocol['original_automatic_rule_passed'] and protocol['strict_proximity_main_successes'] == 10
    qa = source_json('final', FINAL + '/PRODUCTION64_QA_REUSED.json')
    source('final', FINAL + '/CANDIDATE_PROVENANCE_QA.json')
    source('final', FINAL + '/NUMERICAL_AND_COHORT_QA.json')
    source('final', FINAL + '/VALIDATION_ANALYSIS_PLAN.json')
    source('final', FINAL + '/EXECUTION_FREEZE.json')
    source('final', FINAL + '/COHORT_COMPLETED.json')
    source('parameters', 'results/diagnostics/pure_random_ga_parameter_consistency_20261011/FINAL_PURE_RANDOM_GA_PARAMETER_DECISION.md')
    source('initialization', RUNS + '/study.py')
    engine = source('initialization', 'src/la_grid/diagnostics/ga_variant_engine.py')
    assert sha(engine) == protocol['engine_sha256']
    assert b'children[n-len(elite)+j]=x' in engine
    source('later_validation', POST + '/FINAL_CANDIDATE_RECOMMENDATION.md')
    source('later_validation', POST + '/POST_ELITISM_GA_VALIDATION_REPORT.md')
    horizon_qa = source_json('manuscript_remote', 'results/diagnostics/extended_ga_20261008/PLANNING_HORIZON_AUDIT.json')
    assert horizon_qa['completion_bound_is_order_independent']
    assert horizon_qa['full_graph_components_all_source_connected']
    assert horizon_qa['all_permutation_completion_upper_bound_hr'] < 480
    traces, finals = [], []
    for seed in SEEDS:
        run = RUNS + '/runs/PURE_RANDOM_GA_' + str(seed)
        receipt = source_json('initialization', run + '/FINAL_100000.json')
        initial = source_json('initialization', run + '/INITIAL_POPULATION.json')
        moves = source_json('initialization', run + '/STRICT_IMPROVEMENTS.json')
        assert receipt['mode'] == 'PURE_RANDOM_GA' and receipt['budget'] == receipt['distinct_evaluations'] == 100000
        assert receipt['completed'] and receipt['initial_unique'] == 100
        assert initial['initial_sequences'] == initial['common_random_pool']
        assert initial['archive_before_first_evaluation'] == []
        assert len(initial['initial_sequences']) == 100
        assert all(len(x) == len(set(x)) == 92 and set(x) == set(seq) for x in initial['initial_sequences'])
        cfg = receipt['fixed_config']
        assert cfg == dict(population=100, crossover=.8, mutation=.1, tournament=3, elites=1,
            initialization='paired_random_pool', mutation_operator='swap', crossover_operator='ordered',
            adaptive=False, restart=False, diversity_replacement=False)
        assert sha(RAW['initialization/' + run + '/INITIAL_POPULATION.json']) == receipt['initial_population_sha256']
        limited = [x for x in moves if x['distinct_evaluations'] <= 100000]
        assert limited and all(limited[i]['service_loss_hr'] > limited[i+1]['service_loss_hr'] for i in range(len(limited)-1))
        assert all(limited[i]['distinct_evaluations'] < limited[i+1]['distinct_evaluations'] for i in range(len(limited)-1))
        init_best = [x for x in limited if x['generation'] == 0][-1]['service_loss_hr']
        assert init_best == receipt['initial_best_loss_hr']
        assert limited[-1]['service_loss_hr'] == receipt['loss_hr']
        assert limited[-1]['sequence'] == receipt['sequence']
        for x in limited:
            traces.append(dict(seed=seed, distinct_evaluations=x['distinct_evaluations'],
                best_observed_loss_hr=x['service_loss_hr'], generation=x['generation'],
                point_type='actual strict best-observed improvement'))
        if limited[-1]['distinct_evaluations'] < 100000:
            traces.append(dict(seed=seed, distinct_evaluations=100000,
                best_observed_loss_hr=receipt['loss_hr'], generation=receipt['generation'],
                point_type='actual final100k receipt, carried best observation'))
        finals.append(dict(seed=seed, initial_best_loss_hr=init_best, final_best_loss_hr=receipt['loss_hr'],
            improvement_hr=init_best-receipt['loss_hr'], selected=seed == SELECTED,
            distinct_evaluations=receipt['distinct_evaluations'], initial_population_sha256=receipt['initial_population_sha256'],
            final_sequence_sha256=receipt['sequence_sha256']))
    minimum = min(x['final_best_loss_hr'] for x in finals)
    selected = min(x['seed'] for x in finals if x['final_best_loss_hr'] <= minimum + 1e-9)
    assert selected == SELECTED and minimum == candidate['planning_objective_hr']
    effects = pd.read_csv(io.BytesIO(source('final', FINAL + '/PAIRED_EFFECTS.csv')), float_precision='round_trip')
    outcomes = pd.read_csv(io.BytesIO(source('final', FINAL + '/REALIZATION_OUTCOMES.csv')), float_precision='round_trip')
    identity = pd.read_csv(io.BytesIO(source('final', FINAL + '/PHYSICAL_COHORT_IDENTITY.csv')))
    selected_effects = effects[(effects.candidate == 'GA-pure-random') & (effects.reference == 'Impact-first')]
    ga = outcomes[outcomes.strategy == 'GA-pure-random'].set_index('realization_id').sort_index()
    impact = outcomes[outcomes.strategy == 'Impact-first'].set_index('realization_id').sort_index()
    assert len(ga) == len(impact) == len(identity) == 2000
    assert ga.index.is_unique and ga.index.equals(impact.index)
    assert (ga.physical_sha256 == impact.physical_sha256).all()
    assert ga.physical_sha256.nunique() == 2000
    assert ga.horizon_hr.eq(480).all() and impact.horizon_hr.eq(480).all()
    field = 'population_weighted_normalized_burden_hr'
    delta = ga[field] - impact[field]
    primary = selected_effects[selected_effects.metric == field].iloc[0].to_dict()
    assert abs(delta.mean() - primary['mean_difference']) < 1e-12
    assert abs(delta.mean() - (-.53267454004706827)) < 1e-12
    assert (delta < 0).sum() == 1741 and (delta > 0).sum() == 259 and (delta == 0).sum() == 0
    assert abs(primary['simultaneous95_low'] - (-.56398203866016117)) < 1e-12
    assert abs(primary['simultaneous95_high'] - (-.50232131526136481)) < 1e-12
    components = [('Self', 'L_self_population_mass_weighted_hr'),
                  ('Threshold', 'L_threshold_population_mass_weighted_hr'),
                  ('Source-path', 'L_source_population_mass_weighted_hr')]
    diffs = pd.DataFrame({label: ga[key] - impact[key] for label, key in components})
    closure = float(np.max(np.abs(diffs.sum(axis=1) - delta)))
    assert closure < 1e-10
    component_rows = []
    for label, key in components:
        saved = selected_effects[selected_effects.metric == key].iloc[0]
        value = float(diffs[label].mean())
        assert abs(value-saved.mean_difference) < 1e-12
        component_rows.append(dict(component=label, mean_difference_hr=value,
            interpretation='increased loss' if value > 0 else 'decreased loss'))
    component_rows.append(dict(component='Net', mean_difference_hr=float(delta.mean()), interpretation='net difference'))
    equity = selected_effects[selected_effects.metric.isin(['absolute_Q4_minus_Q1_hr', 'burden_gini'])]
    assert (equity.mean_difference > 0).all()
    csv('SEARCH_BEST_OBSERVED_EVENTS.csv', traces)
    csv('INITIAL_AND_FINAL_SEED_LOSSES.csv', finals)
    csv('PHYSICAL_PAIRED_DISTRIBUTION.csv', dict(realization_id=ga.index, physical_sha256=ga.physical_sha256.values,
        GA_loss_hr=ga[field].values, Impact_loss_hr=impact[field].values, GA_minus_Impact_loss_hr=delta.values))
    csv('POPULATION_LOSS_COMPONENTS.csv', component_rows)
    csv('SAVED_PRIMARY_AND_EQUITY_STATISTICS.csv', selected_effects[selected_effects.metric.isin(
        [field, 'absolute_Q4_minus_Q1_hr', 'burden_gini'])].to_dict('records'))
    write('FINAL_GA_CONFIGURATION_AND_CANDIDATE.json', dict(status='RECONCILED_LEGACY_PURE_RANDOM_GA_NO_RESELECTION',
        full_original_protocol=protocol, candidate=candidate, production64_QA_reused=qa,
        elitism='LEGACY_LAST_POSITION_ELITISM: previous-generation best overwrites final child before evaluation',
        newer_post_evaluation_algorithm_and_candidate_excluded=True,
        exact_original_seed_receipts_reused=20, selection_reproduced_from_receipts=selected,
        excluded_from_selection=['continued250k500k runs', 'control runs', 'validation outcomes'],
        publication_note='Pure random was a post-data choice. Registered90% single-run proximity rule failed:10/20 at100k.',
        new_GA_searches=0, new_physical_draws=0, new_bootstrap_resamples=0, new_production_evaluations=0))
    write('NUMERICAL_QA.json', dict(status='PASS', seed_count=20, original_100k_receipts=20,
        authentic_improvement_events=len(traces)-sum(x['point_type'].startswith('actual final') for x in traces),
        selected_seed=selected, initial_best_range=[min(x['initial_best_loss_hr'] for x in finals), max(x['initial_best_loss_hr'] for x in finals)],
        final_best_range=[minimum, max(x['final_best_loss_hr'] for x in finals)],
        validation_cohort_source=SOURCES['final'][1], validation_realizations=2000,
        same_physical_identities_paired=True, physical_ids_unique=2000, mean_difference_hr=float(delta.mean()),
        primary_saved_statistics=primary, improved_count=1741, worsened_count=259, ties_count=0,
        complete_distribution_range=[float(delta.min()), float(delta.max())], component_closure_max_abs_hr=closure,
        signed_component_means=component_rows, equity_saved_differences=equity[['metric', 'mean_difference']].to_dict('records'),
        CIs_reused_without_resampling=True, median_trajectory='Exact right-continuous observed archive at union of saved improvement clocks; no linear interpolation',
        planning_horizon_equivalence_reused=horizon_qa,
        all_new_search_simulation_resampling_calls=0))
    old_caption = source('manuscript_remote', 'results/figure_review/MANUSCRIPT_FACING_CAPTIONS.md').decode('utf-8')
    start = old_caption.index('## Supplementary Figure S5.')
    end = old_caption.index('## Supplementary Figure S6.', start)
    lp(OUT / 'EXISTING_S05_CAPTION.md').write_text(old_caption[start:end].replace('\r\n', '\n'), encoding='utf-8', newline='\n')
    for name in ['src/la_grid/plotting/extended_ga_artwork_20261008.py',
                 'src/la_grid/plotting/build_meeting_figure_collection.py',
                 'src/la_grid/plotting/selected_strategy_artwork.py',
                 'docs/reproducibility/S05_GA_INCUMBENT_DISPLAY_NOTE_20261007.md',
                 'docs/reproducibility/SUPPLEMENT_DISPLAY_FEEDBACK_20261008.json']:
        source('manuscript_remote', name)
    for name in ['results/figure_review/Supplement/FigS05.pdf', 'results/figure_review/Supplement/FigS05.png',
                 'results/figures/FigS05_GA_Reproducibility.pdf']:
        data = source('manuscript_remote', name)
        write('historical/' + name.replace('/', '__'), data)
    write('SOURCE_DATA_PROVENANCE_MANIFEST.json', dict(status='PASS_ACTUAL_SOURCE_BYTES', sources=SOURCE_RECORDS,
        interpretation='Every archived input is exact immutable Git content or verified actual LFS payload, not a pointer.',
        comparison_only_later_cohort_not_used_for_panels=True))
    target = lp(OUT / 'SOURCE_EVIDENCE.zip')
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for member, data in RAW.items():
            info = zipfile.ZipInfo(member, date_time=(2026, 10, 12, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    with zipfile.ZipFile(target) as z:
        assert all(sha(z.read(row['archive_member'])) == row['sha256'] for row in SOURCE_RECORDS)
    print('PREPARE_PASS', len(SOURCE_RECORDS), 'sources', len(traces), 'plot events', 'delta', delta.mean(), flush=True)


def render():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import PercentFormatter
    import fitz
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 8, 'axes.titlesize': 9.5,
        'axes.titleweight': 'bold', 'axes.labelsize': 8.5, 'xtick.labelsize': 7.5,
        'ytick.labelsize': 7.5, 'legend.fontsize': 7.5, 'axes.linewidth': .6,
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
    blue, pale, red, ink = '#285B79', '#779CB2', '#B64F3F', '#303A40'
    events = pd.read_csv(lp(OUT / 'SEARCH_BEST_OBSERVED_EVENTS.csv'), float_precision='round_trip')
    seeds = pd.read_csv(lp(OUT / 'INITIAL_AND_FINAL_SEED_LOSSES.csv'), float_precision='round_trip')
    validation = pd.read_csv(lp(OUT / 'PHYSICAL_PAIRED_DISTRIBUTION.csv'), float_precision='round_trip')
    components = pd.read_csv(lp(OUT / 'POPULATION_LOSS_COMPONENTS.csv'), float_precision='round_trip')
    qa = read('NUMERICAL_QA.json')
    fig = plt.figure(figsize=(185/25.4, 178/25.4))
    axes = [fig.add_axes(rect) for rect in [[.105, .59, .375, .31], [.62, .59, .35, .31],
                                          [.105, .15, .375, .26], [.70, .15, .27, .26]]]
    for ax in axes:
        ax.spines[['top', 'right']].set_visible(False)
        ax.tick_params(length=3, width=.6, pad=3)
        ax.grid(axis='y', color='#E6E8EA', linewidth=.4, zorder=0)
        ax.set_axisbelow(True)
    titles = ['A. Pure-random search convergence', 'B. Initial and final search outcomes',
              'C. Independent physical validation', 'D. Population-loss accounting']
    for ax, title in zip(axes, titles):
        ax.set_title(title, loc='left', pad=24)
    axes[3]._left_title.set_position((-.296, 1.0))
    for x, txt in [( .105, '20 optimizer seeds; 64 fixed planning realizations'),
                   ( .62, '20 paired initial/final seed observations')]:
        fig.text(x, .932, txt, fontsize=7.5, va='top', color=ink)
    fig.text(.105, .442, '2,000 new physical realizations; frozen legacy GA', fontsize=7.5, va='top', color=ink)
    fig.text(.61, .442, 'Same 2,000 realizations; GA minus Impact-first', fontsize=7.5, va='top', color=ink)
    ax = axes[0]
    grid = np.unique(np.r_[100, 100000, events.distinct_evaluations.values])
    grid = grid[grid >= 100]
    curves = []
    for seed in SEEDS:
        q = events[events.seed == seed]
        x, y = q.distinct_evaluations.values, q.best_observed_loss_hr.values
        values = y[np.searchsorted(x, grid, side='right')-1]
        curves.append(values)
        ax.step(grid/1000, values, where='post', color=pale, lw=.55, alpha=.48, zorder=2)
    median = np.median(np.array(curves), axis=0)
    ax.step(grid/1000, median, where='post', color=blue, lw=1.4, label='Across-seed median archive', zorder=4)
    with zipfile.ZipFile(lp(OUT / 'SOURCE_EVIDENCE.zip')) as z:
        receipt = json.loads(z.read('initialization/' + RUNS + f'/runs/PURE_RANDOM_GA_{SELECTED}/FINAL_100000.json'))
    impact = receipt['loss_hr'] + receipt['gain_vs_impact_hr']
    ax.axhline(impact, color=ink, ls=(0, (4, 2)), lw=.9, label='Impact-first reference', zorder=3)
    ax.set_xlim(0, 100)
    ax.set_ylim(32.6, max(seeds.initial_best_loss_hr)+.35)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel('Distinct objective evaluations (thousands)')
    ax.set_ylabel('Best-observed planning loss (h)')
    ax.legend(handles=[Line2D([], [], color=pale, lw=.7, alpha=.65, label='20 independent runs'),
        Line2D([], [], color=blue, lw=1.4, label='Median best-observed archive'),
        Line2D([], [], color=ink, lw=.9, ls='--', label='Impact-first (reference only)')],
        loc='upper right', frameon=False, handlelength=1.8, labelspacing=.4)
    ax = axes[1]
    for q in seeds.itertuples(index=False):
        chosen = q.seed == SELECTED
        color = blue if chosen else pale
        ax.plot([0, 1], [q.initial_best_loss_hr, q.final_best_loss_hr], color=color,
                lw=1.6 if chosen else .65, alpha=1 if chosen else .6, zorder=3 if chosen else 2)
        ax.scatter([0, 1], [q.initial_best_loss_hr, q.final_best_loss_hr],
                   s=20 if chosen else 8, color=color, marker='D' if chosen else 'o', zorder=4)
    ax.axhline(impact, color=ink, ls=(0, (4, 2)), lw=.9)
    ax.set_xlim(-.25, 1.45)
    ax.set_ylim(axes[0].get_ylim())
    ax.set_xticks([0, 1], ['Initial best\n100 random orders', 'Final best\n100,000 evaluations'])
    ax.set_ylabel('Planning loss (h)')
    ax.text(.98, .965, 'Selected seed: 2026103108\nFinal: 32.995522 h', transform=ax.transAxes,
            ha='right', va='top', fontsize=7.5, color=blue)
    fig.text(.62, .525, 'Strict proximity: 10/20 (90% criterion not met).\nPost-data method choice; no universal reliability.',
             va='top', fontsize=7.5, color=ink)
    ax = axes[2]
    delta = np.sort(validation.GA_minus_Impact_loss_hr.values)
    xs = np.r_[delta[0], delta]
    ys = np.r_[0, np.arange(1, len(delta)+1)/len(delta)]
    ax.step(xs, ys, where='post', color=blue, lw=1.2)
    ax.axvline(0, color=ink, lw=.8, ls=(0, (4, 2)))
    mean = qa['mean_difference_hr']
    primary = qa['primary_saved_statistics']
    lo, hi = primary['simultaneous95_low'], primary['simultaneous95_high']
    ax.axvline(mean, color=red, lw=.9, ls=(0, (1, 2)))
    ax.set_xlim(delta[0]-.18, delta[-1]+.18)
    ax.set_ylim(0, 1.02)
    ax.set_yticks([0, .25, .5, .75, 1])
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel('GA minus Impact-first service loss (h)')
    ax.set_ylabel('Cumulative fraction of physical realizations')
    ax.text(.03, .965, 'Improved: 1,741/2,000 (87.05%)\nWorsened: 259/2,000 (12.95%)',
            transform=ax.transAxes, va='top', fontsize=7.5, color=ink)
    inset = ax.inset_axes([.06, .27, .54, .22])
    inset.errorbar(mean, 0, xerr=[[mean-lo], [hi-mean]], fmt='o', color=red, ms=3.5, lw=1.1, capsize=2)
    inset.set_xlim(-.575, -.49)
    inset.set_ylim(-1, 1)
    inset.set_yticks([])
    inset.set_xticks([-.56, -.53, -.50])
    inset.tick_params(labelsize=7.5, length=2, pad=2)
    inset.spines[['left', 'top', 'right']].set_visible(False)
    inset.set_title('Paired mean: -0.532675 h\nSimultaneous 95% CI:\n[-0.563982, -0.502321] h',
                    fontsize=7.5, fontweight='normal', pad=7, color=red)
    ax = axes[3]
    values = components.mean_difference_hr.values
    colors = [red if v > 0 else blue for v in values]
    colors[-1] = ink
    ax.barh(range(4), values, height=.5, color=colors, zorder=3)
    ax.set_yticks(range(4), ['Self loss', 'Threshold loss', 'Source-path loss', 'Net difference'])
    ax.set_ylim(3.85, -.6)
    ax.set_xlim(-1.0, .48)
    ax.set_xticks([-.8, -.4, 0, .4])
    ax.axvline(0, color=ink, lw=.7)
    ax.grid(False, axis='y')
    ax.grid(axis='x', color='#E6E8EA', lw=.4)
    ax.set_xlabel('Mean service-loss difference (h)')
    for i, value in enumerate(values):
        ax.annotate(f'{value:+.6f}', (value, i), xytext=(0, -11), textcoords='offset points',
                    ha='center', va='top', fontsize=7.5, color=colors[i])
    fig.text(.62, .075, 'Blue: reduced loss   Red: increased loss\nNet benefit is dominated by source-path loss.',
             fontsize=7.5, color=ink, va='top')
    fig.text(.105, .023, 'Legacy pure-random GA; no incumbent injection. Finite-budget evidence, not global optimality.', fontsize=7.5, color=ink)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside = []
    from matplotlib.text import Text
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text():
            continue
        box = artist.get_window_extent(renderer)
        # Matplotlib creates invisible/off-axis tick labels; only actual in-axes labels matter.
        if box.width and box.height and not fig.bbox.contains(box.x0, box.y0) or box.width and box.height and not fig.bbox.contains(box.x1, box.y1):
            outside.append(artist.get_text())
    assert not outside, outside
    pdf = lp(OUT / 'FigS05_GA_Final_Candidate.pdf')
    fig.savefig(pdf, metadata={'Title': 'S05: Final legacy pure-random GA - author-review candidate',
        'Subject': 'Archived optimization and independent validation only; no new searches, simulations or resampling',
        'CreationDate': None, 'ModDate': None})
    fig.savefig(lp(OUT / 'FigS05_GA_Final_Candidate.png'), dpi=600)
    plt.close(fig)
    csv('PANEL_A_MEDIAN_ARCHIVE.csv', dict(distinct_evaluations=grid, median_best_observed_loss_hr=median))
    write('RENDER_LAYOUT_RECORD.json', dict(width_mm=185, height_mm=178, png_dpi=600,
        minimum_font_pt=7.5, font='Arial', colors=dict(GA=blue, individual_seeds=pale, increased_loss=red, net=ink),
        no_clipped_artist_text=True, all20_curves=True, summary='pointwise median of observed right-continuous archives',
        impact_reference_planning_loss_hr=impact, matched_A_B_loss_scale=list(axes[0].get_ylim()),
        interval_inset_explicitly_mean_inference_not_ECDF_quantile_range=True))
    old_path = lp(OUT / 'historical/results__figure_review__Supplement__FigS05.pdf')
    old = fitz.open(old_path)
    new = fitz.open(pdf)
    comparison = fitz.open()
    mm = 72/25.4
    page = comparison.new_page(width=405*mm, height=240*mm)
    page.insert_text((10*mm, 12*mm), 'S05 author-review comparison | existing historical evidence vs finalized legacy pure-random GA', fontsize=12)
    for x, doc, title in [(10, old, 'Existing official S05 - preserved, not finalized-method evidence'),
                          (210, new, 'Proposed S05 - review candidate; not promoted')]:
        height = doc[0].rect.height * (185*mm/doc[0].rect.width)
        page.insert_text((x*mm, 23*mm), title, fontsize=10)
        page.show_pdf_page(fitz.Rect(x*mm, 28*mm, (x+185)*mm, 28*mm+height), doc, 0)
    page.insert_text((10*mm, 223*mm), 'Both figures shown at exactly 185 mm width. Original artwork and manuscript remain unchanged.', fontsize=9)
    page.insert_text((10*mm, 229*mm), 'Left: incumbent/inversion/generation-budget research and 1,000-realization evaluation. Right: 20 random-only seeds and a distinct 2,000-realization cohort.', fontsize=9)
    comparison.save(lp(OUT / 'S05_Existing_vs_Proposed_REVIEW.pdf'), deflate=True)
    comparison.close()
    old.close()
    new.close()
    print('RENDER_PASS', flush=True)


def qa_pdf():
    import fitz
    result = {}
    for name in ['FigS05_GA_Final_Candidate.pdf', 'S05_Existing_vs_Proposed_REVIEW.pdf']:
        doc = fitz.open(lp(OUT / name))
        page = doc[0]
        assert len(doc) == 1
        spans = [s for b in page.get_text('dict')['blocks'] if b['type'] == 0 for line in b['lines'] for s in line['spans']]
        clipped = [s['text'] for s in spans if not page.rect.contains(fitz.Rect(s['bbox']))]
        assert not clipped, clipped
        pix = page.get_pixmap(dpi=200, alpha=False)
        pix.save(lp(OUT / ('runtime/' + name.replace('.pdf', '_200dpi.png'))))
        if name.startswith('FigS05_'):
            assert abs(page.rect.width / 72*25.4 - 185) < 1e-4
            assert len(page.get_images()) == 0
            assert min(s['size'] for s in spans) >= 7.49
            assert all(term in page.get_text().lower() for term in ['1,741/2,000', '32.995522', '10/20', 'simultaneous'])
        result[name] = dict(sha256=digest(OUT / name), page_count=len(doc),
            width_mm=page.rect.width/72*25.4, height_mm=page.rect.height/72*25.4,
            raster_images=len(page.get_images()), min_text_font_pt=min(s['size'] for s in spans),
            no_clipped_text=True, fonts=page.get_fonts(full=True),
            visual_review_record='VISUAL_QA_REVIEW.json; separate actual-render inspection')
        doc.close()
    write('PDF_TECHNICAL_QA.json', result)
    print('PDF_TECHNICAL_QA_PASS', flush=True)


def preservation():
    current = preserved()
    assert current == read('PRESERVATION_BASELINE.json'), 'Existing protected/source work changed; do not repair it.'
    write('PRESERVATION_VERIFIED.json', dict(status='PASS', protected_scientific_files=950,
        original_staged_items=862, original_branch_HEAD_index_status_and_all_file_hashes_unchanged=True,
        original_official_S05_and_caption_unchanged=True, evidence_source_checkouts_unchanged=True,
        preexisting_external_exception=current['preexisting_external_exception'],
        new_optimizer_calls=0, new_physical_draws=0, new_production_calls=0, new_bootstrap_resamples=0))
    print('PRESERVATION_PASS_950_862', flush=True)


def manifest():
    rows = {}
    for p in lp(OUT).rglob('*'):
        if not p.is_file() or 'runtime' in p.parts or '__pycache__' in p.parts:
            continue
        if p.name in ['OUTPUT_HASH_MANIFEST.json', 'REMOTE_PUBLICATION_VERIFIED.json', 'FINAL_REMOTE_HEAD_VERIFIED.json']:
            continue
        rows[str(p.relative_to(lp(OUT))).replace('\\', '/')] = dict(sha256=digest(p), bytes=p.stat().st_size)
    write('OUTPUT_HASH_MANIFEST.json', dict(files=rows, total_bytes=sum(x['bytes'] for x in rows.values())))


def remote():
    # Reuse the existing actual-download LFS verifier; redirect its outputs here.
    import importlib.util
    import types
    stub = types.SimpleNamespace(ROOT=ROOT, OUT=OUT, BRANCH=BRANCH, lp=lp, digest=digest,
        save=lambda p, data: write(str(Path(p).relative_to(OUT)), data), git=lambda *a: git(ROOT, *a))
    sys.modules['study'] = stub
    path = ROOT.parent / '_gaf12' / RUNS / 'publish.py'
    spec = importlib.util.spec_from_file_location('s05_remote_verifier', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.remote()


if __name__ == '__main__':
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'render', 'qa', 'preservation', 'manifest', 'remote'])
    phase = p.parse_args().phase
    {'prepare': prepare, 'render': render, 'qa': qa_pdf, 'preservation': preservation,
     'manifest': manifest, 'remote': remote}[phase]()
