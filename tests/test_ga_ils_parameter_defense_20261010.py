import random
import numpy as np
from la_grid.diagnostics.ga_ils_parameter_defense_20261010 import (
    SCREEN, CONFIRM, ils_config, ils_search, ga_search, Meter,
)
from la_grid.diagnostics.ga_alternative_optimizer_20261009 import local_search
from la_grid.diagnostics.ga_init_param_20261009 import BASE
from la_grid.diagnostics import ga_variant_engine as eng


class Toy:
    ids = tuple(str(i) for i in range(12))
    index = {s: i for i, s in enumerate(ids)}
    def score(self, seq):
        return -sum(abs(int(v)-i) for i, v in enumerate(seq))-1.


def test_ils_baseline_matches_original_rng_and_search():
    k = Toy()
    inc = {'impact-first': tuple(reversed(k.ids))}
    prior = tuple(random.Random(91).sample(k.ids, 12))
    for seed in (17, 29):
        actual = ils_search(k, inc, prior, seed, 2000, ils_config('ils_mix'))
        original = local_search(k, inc, prior, 'iterated_local', seed, 2000)
        for key in ('search_best_loss_hr', 'best_sequence', 'sequence_sha256',
                    'attempted_evaluations', 'accepted_moves', 'restart_count'):
            assert actual[key] == original[key]


def test_unchanged_ga_observation():
    k = Toy()
    inc = {'impact-first': tuple(reversed(k.ids))}
    prior = tuple(random.Random(91).sample(k.ids, 12))
    actual, _ = ga_search(k, inc, prior, 29, 2000, {'elites': 1})
    original = eng.run_search(items=k.ids, incumbents=inc, objective=k.score,
        seed=29, config=BASE, max_evaluations=2000, quality=prior)
    assert actual['best_sequence'] == list(original['best_sequence'])
    assert actual['attempted_evaluations'] == original['state']['attempts']
    assert actual['search_best_loss_hr'] == -original['best_fitness']


def test_distinct_cache_and_budget():
    k = Toy()
    m = Meter(k, 1)
    m.evaluate(k.ids)
    m.evaluate(k.ids)
    assert m.attempts == 2 and len(m.cache) == 1
    try:
        m.evaluate(tuple(reversed(k.ids)))
    except StopIteration:
        pass
    else:
        raise AssertionError('budget failed')


def test_seed_and_control_units():
    assert len(SCREEN)==8 and len(CONFIRM)==20 and not set(SCREEN)&set(CONFIRM)
    assert ils_config('ils_mix')['stagnation']==800
    assert ils_config('ils_small')['perturbation']==[1, 2, 4]
    assert not ils_config('ils_no_perturb')['perturb']


def test_setup_preserves_registered_case_set_and_existing_authority(monkeypatch,tmp_path):
    import pytest
    import la_grid.diagnostics.ga_ils_parameter_defense_20261010 as study
    assert len(study.SCREEN_CASES)==len(set(study.SCREEN_CASES))==16
    assert not {'ils_cold','ils_swap_stag2000','ils_swap_no_perturb'}&set(study.SCREEN_CASES)
    monkeypatch.setattr(study,'OUT',tmp_path)
    (tmp_path/'PRESERVATION_BASELINE.json').write_text('{}',encoding='utf-8')
    with pytest.raises(RuntimeError,match='must not be overwritten'):
        study.setup()


def test_operators_preserve_station_identity():
    from la_grid.diagnostics.ga_variant_engine import mutation, crossover
    k = Toy()
    rng = random.Random(31)
    for _ in range(40):
        other = tuple(rng.sample(k.ids, len(k.ids)))
        for op in ('swap', 'insertion', 'inversion'):
            out = mutation(other, rng, op)
            assert len(out)==len(set(out))==12 and set(out)==set(k.ids)
        for op in ('ordered', 'pmx', 'cycle'):
            for out in crossover(k.ids, other, rng, op):
                assert len(out)==len(set(out))==12 and set(out)==set(k.ids)


def test_elite_intervention_has_same_initial_population_and_rng():
    k=Toy();inc={'impact-first':tuple(reversed(k.ids))}
    prior=tuple(random.Random(91).sample(k.ids,12))
    rows=[ga_search(k,inc,prior,41,1000,{'elites':n})[0] for n in range(4)]
    assert len({r['initial_population_sha256'] for r in rows})==1
    assert len({r['post_initializer_rng_sha256'] for r in rows})==1
    assert all(r['search_best_loss_hr']<=r['initial_best_loss_hr'] for r in rows)


def test_no_perturb_is_reported_incomplete_on_finite_flat_neighborhood():
    class Flat:
        ids=tuple(str(i) for i in range(6))
        index={s:i for i,s in enumerate(ids)}
        def score(self,seq):return -1.
    k=Flat();inc={'impact-first':k.ids}
    cfg=ils_config('ils_swap_no_perturb')
    row=ils_search(k,inc,k.ids,7,40,cfg)
    assert not row['completed_budget'] and row['distinct_evaluations']<=16
    assert row['attempted_evaluations']==2400
    assert row['accepted_moves']==row['restart_count']==0
    assert row['censoring'] is not None


def test_paired_uncertainty_and_bootstrap_use_seed_blocks():
    from la_grid.diagnostics.ga_ils_parameter_analysis_20261010 import contrast
    delta=np.array([-.002,.001,-.001,.003,-.004])
    a=contrast(delta,'a minus b','family',3,'test')
    b=contrast(delta,'a minus b','family',3,'test')
    assert a==b and a['n']==5
    assert abs(a['mean_delta_hr']-delta.mean())<1e-15
    assert (a['wins'],a['losses'],a['ties'])==(3,2,0)
    assert a['simultaneous95_low_hr']<=a['t95_low_hr']
    assert a['simultaneous95_high_hr']>=a['t95_high_hr']
    assert a['equivalence_margin_hr'] is None
