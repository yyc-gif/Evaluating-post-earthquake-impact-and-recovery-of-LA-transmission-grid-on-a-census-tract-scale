"""Tests read saved search receipts; no optimizer or genuine sampler is invoked."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finalize as f


def test_selected_candidate_is_actual_random_only_main_winner():
    rows = [f.v.read(p) for p in sorted((f.OUT / 'selection_receipts').glob('*.json'))]
    selected = f.choose(rows)
    frozen = f.v.read(f.OUT / 'FINAL_RANDOM_GA_CANDIDATE.json')
    assert selected['sequence'] == frozen['sequence']
    assert selected['seed'] == frozen['seed'] == 2026103108
    assert f.identity(frozen['sequence']) == frozen['sequence_sha256']
    assert len(frozen['sequence']) == len(set(frozen['sequence'])) == 92


def test_cross_run_ties_use_seed_not_validation_outcomes():
    rows = [dict(mode='PURE_RANDOM_GA', budget=100000, seed=s, loss_hr=1.) for s in f.MAIN]
    rows[1]['loss_hr'] -= 5e-10
    assert f.choose(rows)['seed'] == f.MAIN[0]
    rows[1]['loss_hr'] -= 2e-9
    assert f.choose(rows)['seed'] == f.MAIN[1]


def test_ineligible_budget_or_mode_refused():
    rows = [dict(mode='PURE_RANDOM_GA', budget=100000, seed=s, loss_hr=1.) for s in f.MAIN]
    rows[0]['budget'] = 500000
    with pytest.raises(AssertionError):
        f.choose(rows)
    rows[0].update(budget=100000, mode='IMPACT_SEEDED_GA')
    with pytest.raises(AssertionError):
        f.choose(rows)


def test_disclosure_retains_failed_automatic_adoption_and_reliability():
    p = f.v.read(f.OUT / 'FINAL_GA_EXECUTION_PROTOCOL.json')
    assert p['method_choice_is_post_data'] and not p['original_automatic_rule_passed']
    assert p['strict_proximity_main_successes'] / p['strict_proximity_main_n'] == .5
    assert p['reserve_proximity_successes'] / p['reserve_proximity_n'] == .8
    assert p['preregistered_reliability_required'] == .9
    assert not p['single_run_90pct_claim_permitted']


def test_prior_production64_is_reused_for_same_candidate():
    q = f.v.read(f.OUT / 'PRODUCTION64_QA_REUSED.json')
    candidate = f.v.read(f.OUT / 'FINAL_RANDOM_GA_CANDIDATE.json')
    assert q['record']['sequence'] == candidate['sequence']
    assert q['record']['all64_pass'] and len(q['record']['production64_losses']) == 64
    assert q['record']['max_absolute_error_hr'] < 1e-8
    assert q['new_search_calls'] == q['new_production_calls'] == 0


def test_missing_new_authorization_refuses_without_any_draw(tmp_path, monkeypatch):
    monkeypatch.setattr(f, 'OUT', tmp_path)
    with pytest.raises(FileNotFoundError):
        f.execute()
    assert not (tmp_path / 'cohort').exists()


def test_fresh_cohort_namespace_and_fixed_candidate():
    freeze = f.verify()
    assert freeze['sample_size'] == 2000 and freeze['entropy_rule'] == [2026110300, 'r']
    assert freeze['bootstrap_seed'] == 2026110400
    assert len(f.v.read(f.OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json')) == 5064
    assert freeze['strategies'][0]['strategy'] == 'GA-pure-random'
    assert freeze['strategies'][1]['strategy'] == 'legacy-warm-start-GA'
    assert freeze['strategies'][0]['sequence_sha256'] != freeze['strategies'][1]['sequence_sha256']
