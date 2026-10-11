import pickle
import random
from dataclasses import replace

from la_grid.diagnostics.standalone_ils_20261010 import StandaloneILS, CONFIG, GA_CONFIG
from la_grid.diagnostics import ga_variant_engine as eng


IDS = tuple(str(i) for i in range(8))
TARGET = tuple(reversed(IDS))


def score(seq):
    return -float(sum((int(x) - int(TARGET[i]))**2 for i, x in enumerate(seq)))


def config():
    return dict(CONFIG, stagnation_attempts=9)


def stable(state):
    return {k: v for k, v in state.items() if k not in ('wall_seconds', 'cpu_seconds', 'objective_seconds', 'checkpoints')}


def test_initial_only_impact_and_budget():
    calls = []
    s = StandaloneILS(IDS, IDS, lambda x: calls.append(tuple(x)) or score(x), 1, config())
    d = s.run(50, checkpoints=())
    assert d['initial_sequences'] == d['initial_archive'] == [list(IDS)]
    assert calls[0] == IDS and len(calls) == len(set(calls)) == 50
    assert d['attempts'] >= 50 and len(d['cache']) == 50
    assert all(len(k) == 8 and len(set(k)) == 8 for k in d['cache'])
    assert d['attempts'] == 1 + d['local_proposals'] + d['restarts']


def test_resume_replay_exact():
    full = StandaloneILS(IDS, IDS, score, 923, config()).run(250, checkpoints=())
    part = StandaloneILS(IDS, IDS, score, 923, config()).run(80, checkpoints=())
    part = pickle.loads(pickle.dumps(part))
    resumed = StandaloneILS(IDS, IDS, score, 923, config(), state=part).run(250, checkpoints=())
    assert stable(full) == stable(resumed)


def test_plateau_stagnation_cache_and_cycle():
    cfg = dict(CONFIG, stagnation_attempts=5)
    d = StandaloneILS(IDS, IDS, lambda s: 0., 19, cfg).run(120, checkpoints=())
    assert d['accepted'] == 0 and d['best'] == IDS
    assert [r['strength'] for r in d['restart_records'][:6]] == [2, 4, 8, 2, 4, 8]
    assert d['cache'] and d['attempts'] > len(d['cache'])
    records = d['restart_records']
    assert records[0]['before_attempts'] == 6
    assert all(b['before_attempts'] - a['before_attempts'] == 6 for a, b in zip(records, records[1:]))


def test_strict_tolerance_and_archive_never_worsens():
    d = StandaloneILS(IDS, IDS, lambda s: 1e-13 if s != IDS else 0., 6, config()).run(60, checkpoints=())
    assert d['accepted'] == 0
    values = [r['loss_hr'] for r in d['improvements']]
    assert all(b < a for a, b in zip(values, values[1:]))


def test_swap_uniform_rng_replay():
    s = StandaloneILS(IDS, IDS, score, 918, config())
    rng = random.Random(918)
    for _ in range(50):
        a, b = rng.sample(range(8), 2)
        expected = list(IDS)
        expected[a], expected[b] = expected[b], expected[a]
        proposed, pair = s.swap(IDS)
        assert pair == [a, b] and proposed == tuple(expected)


def test_attempt_cap_exact():
    d = StandaloneILS(('0', '1'), ('0', '1'), lambda s: 0., 3, dict(CONFIG, stagnation_attempts=2, attempt_cap_multiplier=3)).run(20, checkpoints=())
    assert d['attempts'] == 60 and len(d['cache']) == 2


def test_original_size_92_replay_and_every_cached_permutation():
    domain = tuple(str(i) for i in range(92))
    objective = lambda seq: -float(sum((i-int(x))**2 for i, x in enumerate(seq)))
    cfg = dict(CONFIG, stagnation_attempts=7)
    full = StandaloneILS(domain, domain, objective, 821, cfg).run(250, checkpoints=())
    part = StandaloneILS(domain, domain, objective, 821, cfg).run(90, checkpoints=())
    resumed = StandaloneILS(domain, domain, objective, 821, cfg, state=pickle.loads(pickle.dumps(part))).run(250, checkpoints=())
    assert stable(full) == stable(resumed)
    assert all(len(k) == len(set(k)) == 92 and set(k) == set(range(92)) for k in full['cache'])


def test_ga_impact_only_and_state_resume(tmp_path):
    cfg = replace(GA_CONFIG, population=10)
    initial = eng.initialize(IDS, {'impact-first': IDS}, random.Random(48), cfg, None)
    assert initial[0] == IDS and len(initial) == 10
    expected = [IDS] + [tuple(random.Random(48).sample(IDS, len(IDS)))]
    assert initial[:2] == expected
    args = dict(items=IDS, incumbents={'impact-first': IDS}, objective=score, seed=48, config=cfg, checkpoints=(40, 130))
    full = eng.run_search(**args, max_evaluations=130)
    folder = tmp_path / 'ga'
    eng.run_search(**args, max_evaluations=40, folder=folder)
    resumed = eng.run_search(**args, max_evaluations=130, folder=folder)
    assert full['cache'] == resumed['cache'] and full['best_sequence'] == resumed['best_sequence']
    for key in ('attempts', 'generation', 'next_index', 'best_seen', 'archive_score', 'population', 'scores'):
        assert full['state'][key] == resumed['state'][key]


def test_event_horizon_clipping_including_unrecovered_tail():
    from la_grid.diagnostics.standalone_ils_analysis_20261010 import restricted_event_loss
    events = [dict(time_hr=0., effective_service=.2),
              dict(time_hr=100., effective_service=.5),
              dict(time_hr=600., effective_service=1.)]
    assert restricted_event_loss(events, 2800., 480.) == 270.
    assert restricted_event_loss(events, 2800., 2800.) == 330.
