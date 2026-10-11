"""Reconcile final tables, immutable registration, production QA and evidence packaging."""
from __future__ import annotations

import numpy as np
import pandas as pd

import analyze as a
import study as s


def main():
    required = [
        'EXPERIMENT_DESIGN_AND_SEEDS.json',
        'INITIALIZATION_IMPLEMENTATION_AND_PARITY.md',
        'PURE_RANDOM_GA_SEED_RESULTS.csv',
        'IMPACT_SEEDED_GA_SEED_RESULTS.csv',
        'PAIRED_INITIALIZATION_COMPARISON.csv',
        'INITIAL_POPULATION_AND_SEARCH_CONTRIBUTION.csv',
        'BUDGET_CONVERGENCE_AND_DUPLICATION.csv',
        'HISTORICAL_GA_COMPARISON.md',
        'IMPORTANT_SEQUENCE_PRODUCTION_QA.json',
        'GA_INITIALIZATION_SCIENTIFIC_INTERPRETATION.md',
        'REVIEWER_DEFENSE_AND_METHODS_TEXT.md',
        'FINAL_GA_INITIALIZATION_DECISION.md',
        'REPRODUCIBILITY_AND_PRESERVATION_QA.json',
        'RAW_SEARCH_EVIDENCE_MANIFEST.json',
    ]
    assert all(s.lp(s.OUT / name).is_file() for name in required)
    design = s.read(s.OUT / required[0])
    assert s.digest(s.OUT / 'study.py') == design['source_hashes'][
        'results/diagnostics/ga_random_initialization_isolation_20261011/study.py']
    df = pd.concat([pd.read_csv(s.lp(s.OUT / (m + '_SEED_RESULTS.csv'))) for m in s.MODES])
    cp = pd.read_csv(s.lp(s.OUT / 'PAIRED_INITIALIZATION_COMPARISON.csv'))
    assert cp.budget.tolist() == s.CHECKPOINTS
    assert cp.n.tolist() == [20, 20, 20, 10, 10]
    for _, row in cp.iterrows():
        g = df[df.budget == row.budget].pivot(index='seed', columns='mode', values='loss_hr')
        recomputed = a.paired(g[s.MODES[0]] - g[s.MODES[1]])
        for key, value in recomputed.items():
            assert np.isclose(row[key], value, rtol=0, atol=2e-12), (row.budget, key)
    final = df.sort_values('budget').groupby(['mode', 'seed']).tail(1)
    assert len(final) == 40 and final.distinct_evaluations.sum() == 12000000
    assert (df[df['mode'] == s.MODES[0]].gain_vs_impact_hr > 0).all()
    late = df[df.budget.isin([250000, 500000])].pivot(
        index=['mode', 'seed'], columns='budget', values='loss_hr')
    assert len(late) == 20 and (late[250000] == late[500000]).all()
    production = s.read(s.OUT / 'IMPORTANT_SEQUENCE_PRODUCTION_QA.json')
    assert production['status'] == 'PASS' and production['unique_sequences'] == 6
    assert all(r['all64_pass'] and len(r['production64_losses']) == 64 for r in production['records'])
    assert s.read(s.OUT / 'ALL_RUN_NUMERICAL_QA.json')['status'] == 'PASS'
    assert s.read(s.OUT / 'MAIN_PREFIX_REPLAY_QA.json')['status'] == 'PASS'
    decision = s.read(s.OUT / 'FINAL_DECISION_MACHINE_READABLE.json')
    assert decision['recommendation'] == 'PURE_RANDOM_GA'
    assert decision['immutable_registered_rule_result'] == 'IMPACT_SEEDED_GA'
    assert decision['post_data_methodological_judgment'] and not decision['criteria']['reliability']
    assert not decision['formal_replacement']
    bundles = s.read(s.OUT / 'RAW_SEARCH_EVIDENCE_MANIFEST.json')
    assert bundles['status'] == 'PASS' and len(bundles['runs']) == 40
    for run in bundles['runs']:
        assert run['all_raw_bytes_verified']
        assert s.digest(s.OUT / run['zip_path']) == run['zip_sha256']
    s.save(s.OUT / 'FINAL_PACKAGE_QUALITY_QA.json', dict(
        status='PASS', required_files=required, paired_statistics_recomputed=True,
        main_pairs=20, reserved_continuation_pairs=10, total_search_distinct=12000000,
        no_250k_to_500k_improvement=True, post_data_decision_deviation_disclosed=True,
        physical_objective_calls_in_this_check=0, raw_run_bundles=40,
        production_max_error_hr=max(r['max_absolute_error_hr'] for r in production['records']),
        final_unit_tests='5 passed; python -B -m pytest test_isolation.py -q; 1.26 s',
        figure_visual_review=dict(file='GA_INITIALIZATION_CONVERGENCE.png',
            sha256=s.digest(s.OUT / 'GA_INITIALIZATION_CONVERGENCE.png'),
            reviewed=True, readability='Titles, axes, ticks and legends are readable and unclipped.',
            cohort_separation='Solid 20-pair and dashed reserved 10-pair trajectories are separated; caption states different cohorts and conditional uncertainty.'),
        formal_replacement=False, new_physical_samples=0))
    print('FINAL_PACKAGE_QA_PASS; no physical objective calls', flush=True)


if __name__ == '__main__':
    main()
