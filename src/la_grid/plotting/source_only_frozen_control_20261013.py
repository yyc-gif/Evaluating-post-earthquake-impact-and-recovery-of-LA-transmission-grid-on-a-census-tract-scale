"""Source-connectivity ablation at fixed 0.50 functionality threshold.

Exact linear accounting on saved station integrals; no trajectory or model run.
"""
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

import consolidate_current_figure_suite as u

BASE = '3c7899f0f328d37b99d2b022f1650c5288a4a664'
QA = u.ROOT / 'docs/reproducibility/figure_suite_author_clarity_numbering_20261013'
POLICIES = ['impact-first', 'hospital-first', 'degree-first']
GATE = 'G1_BASELINE_050'


def acquire():
    """Freeze only the compact arrays needed to reproduce the new control."""
    manifest = {}
    inputs = QA / 'source_control_inputs'
    for rel, name in [
        ('Data/JULY_UTILITY_CONSTRAINED_92.csv', 'MAPPING.csv'),
        ('provenance/reviewer_working/R1_Comment1_July92_Utility_Constraint/'
         'MAPPING_STRUCTURE_SENSITIVITY_TRACTS.csv', 'TRACTS.csv'),
        ('src/la_grid/revision/r1_source_gate.py', 'FROZEN_GATE_DEFINITION.py'),
        ('src/la_grid/revision/formal/offline.py', 'FROZEN_INTEGRATION_DEFINITION.py'),
    ]:
        raw = u.payload(BASE, rel)
        u.write(inputs / name, raw)
        manifest[name] = dict(commit=BASE, path=rel, sha256=u.digest(raw))
    external = u.ORIGINAL / 'Formal_Experiment_20260923/Formal_Offline_Evaluation'
    for policy in POLICIES:
        stem = '2pc50__C57_D1__' + policy
        record_path = external / (stem + '__EVALUATION.json')
        record = json.load(open(u.lp(record_path)))
        summary_path = external / (stem + '__SUMMARY.parquet')
        integral_path = external / (stem + '__INTEGRALS.npz')
        assert u.sha(summary_path) == record['summary_sha256']
        assert u.sha(integral_path) == record['integral_sha256']
        assert record['status'] == 'FORMAL_FROZEN_MATRIX_V1'
        assert record['realization_count'] == 1000
        summary = pd.read_parquet(u.lp(summary_path))
        selected = summary.loc[
            summary.mapping.eq('M1_UTILITY_003') &
            summary.comparison_domain.eq('mapping_native_domain')].copy()
        selected.to_csv(u.lp(inputs / (policy + '_SUMMARY.csv')), index=False,
                        float_format='%.17g')
        with np.load(u.lp(integral_path), allow_pickle=False) as original:
            keys = [GATE + '__' + name for name in
                    ['L_self', 'L_threshold', 'L_source', 'L_total']]
            keys += ['station_ids', 'physical_hashes']
            np.savez_compressed(u.lp(inputs / (policy + '_INTEGRALS.npz')),
                                **{k: original[k] for k in keys})
        u.dump(inputs / (policy + '_EVALUATION.json'), record)
        manifest[policy] = dict(
            external_directory=str(external), summary_sha256=record['summary_sha256'],
            integral_sha256=record['integral_sha256'],
            evaluation_record_sha256=u.sha(record_path), identity=record['identity'],
            compact_summary_sha256=u.sha(inputs / (policy + '_SUMMARY.csv')),
            compact_integrals_sha256=u.sha(inputs / (policy + '_INTEGRALS.npz')))
    u.dump(QA / 'SOURCE_ONLY_INPUT_AUTHORITY.json', manifest)


def calculate():
    inputs = QA / 'source_control_inputs'
    authority = json.load(open(u.lp(QA / 'SOURCE_ONLY_INPUT_AUTHORITY.json')))
    tracts = pd.read_csv(u.lp(inputs / 'TRACTS.csv'), dtype={'tract_id': str})
    mapping = pd.read_csv(u.lp(inputs / 'MAPPING.csv'),
                          dtype={'tract_id': str, 'substation_id': str})
    assert len(tracts) == 2315 and tracts.tract_id.str.fullmatch(r'\d{11}').all()
    assert int(tracts.population.sum()) == 9066522
    assert tracts.tract_id.is_unique and not mapping.duplicated(['tract_id', 'substation_id']).any()
    records, estimates, tract_means, checks = [], [], [], []
    physical = None
    station_order = None
    identity = None
    for policy in POLICIES:
        info = authority[policy]
        for suffix, key in [('SUMMARY.csv', 'compact_summary_sha256'),
                            ('INTEGRALS.npz', 'compact_integrals_sha256')]:
            assert u.sha(inputs / (policy + '_' + suffix)) == info[key]
        current_identity = {k: v for k, v in info['identity'].items() if k != 'strategy'}
        if identity is None:
            identity = current_identity
        else:
            assert current_identity == identity
        assert identity['H_eval_hr'] == 480 and identity['resource_case'] == 'C57_D1'
        assert identity['hazard'] == '2pc50'
        frame = pd.read_csv(u.lp(inputs / (policy + '_SUMMARY.csv')), float_precision='round_trip')
        baseline = frame.loc[frame.gate.eq(GATE)].sort_values('realization_id')
        expected_ids = [f'2pc50__evaluation_{i:04d}' for i in range(1000)]
        assert baseline.realization_id.tolist() == expected_ids
        assert baseline.strategy_id.eq(policy).all()
        assert baseline.horizon_hr.eq(480).all()
        assert baseline.resolved_tract_count.eq(2315).all()
        assert baseline.unresolved_population.eq(0).all()
        with np.load(u.lp(inputs / (policy + '_INTEGRALS.npz')), allow_pickle=False) as z:
            stations = z['station_ids'].astype(str)
            hashes = z['physical_hashes'].astype(str)
            if physical is None:
                physical, station_order = hashes.copy(), stations.copy()
            else:
                np.testing.assert_array_equal(hashes, physical)
                np.testing.assert_array_equal(stations, station_order)
            assert u.digest(('\n'.join(hashes) + '\n').encode()) == identity['physical_hashes_sha256']
            w = mapping.pivot(index='tract_id', columns='substation_id', values='weight').fillna(0)
            w = w.reindex(index=tracts.tract_id, columns=stations, fill_value=0).to_numpy()
            np.testing.assert_allclose(w.sum(axis=1), 1, atol=1e-12, rtol=0)
            pop = tracts.population.to_numpy(float)
            station_pop_weights = w.T @ pop / pop.sum()
            arrays = {name: z[GATE + '__' + name].copy() for name in
                      ['L_self', 'L_threshold', 'L_source', 'L_total']}
        assert all(x.shape == (1000, 92) and np.isfinite(x).all() for x in arrays.values())
        np.testing.assert_allclose(arrays['L_total'], arrays['L_self'] + arrays['L_threshold'] +
                                   arrays['L_source'], atol=1e-10, rtol=0)
        # Removing C only retains F=1[f >= .50], hence L_off = L_self + L_threshold.
        source_off_station = arrays['L_self'] + arrays['L_threshold']
        off = source_off_station @ station_pop_weights
        on = arrays['L_total'] @ station_pop_weights
        source = arrays['L_source'] @ station_pop_weights
        frozen = baseline.population_weighted_normalized_burden_hr.to_numpy()
        np.testing.assert_allclose(on, frozen, atol=1e-10, rtol=0)
        np.testing.assert_allclose(source, baseline.L_source_population_mass_weighted_hr,
                                   atol=1e-10, rtol=0)
        np.testing.assert_allclose(off, frozen - source, atol=1e-10, rtol=0)
        assert (off >= -1e-12).all() and (off <= frozen + 1e-10).all()
        diff = off - frozen
        for i, rid in enumerate(expected_ids):
            records.append(dict(policy=policy, realization_id=rid, physical_sample_sha256=hashes[i],
                source_gate='disabled', functionality_threshold=.5, mapping='M1_UTILITY_003',
                horizon_hr=480, baseline_loss_h=frozen[i], source_off_loss_h=off[i],
                source_path_loss_h=source[i], service_loss_gap_h=diff[i]))
        for case, values in [('G4_SOURCE_OFF_050', diff),
                             ('G2_RELAXED_005', None), ('G3_STRICT_075', None)]:
            if values is None:
                other = frame.loc[frame.gate.eq(case)].sort_values('realization_id')
                assert other.realization_id.tolist() == expected_ids
                values = other.population_weighted_normalized_burden_hr.to_numpy() - frozen
            estimates.append(dict(policy=policy, case=case, n=1000, mean_gap_h=values.mean(),
                p05_gap_h=np.quantile(values, .05), p95_gap_h=np.quantile(values, .95),
                reference='G1_BASELINE_050', threshold=.5 if case.startswith('G4') else
                .05 if case.startswith('G2') else .75,
                source_gate='disabled' if case.startswith('G4') else 'retained'))
        on_mean = w @ arrays['L_total'].mean(axis=0)
        off_mean = w @ source_off_station.mean(axis=0)
        src_mean = w @ arrays['L_source'].mean(axis=0)
        np.testing.assert_allclose(on_mean - off_mean, src_mean, atol=1e-10, rtol=0)
        for i, row in tracts.iterrows():
            tract_means.append(dict(tract_id=row.tract_id, population=row.population, policy=policy,
                baseline_mean_loss_h=on_mean[i], source_off_mean_loss_h=off_mean[i],
                source_path_mean_loss_h=src_mean[i]))
        checks.append(dict(policy=policy, realizations=1000, stations=92, tracts=2315,
            baseline_normalization_max_error_h=float(np.max(abs(on - frozen))),
            source_off_identity_max_error_h=float(np.max(abs(off - (frozen - source)))),
            mean_baseline_loss_h=float(frozen.mean()), mean_source_off_loss_h=float(off.mean()),
            mean_gap_h=float(diff.mean())))
    u.write_csv(QA / 'SOURCE_ONLY_REALIZATION_VALUES.csv', records)
    u.write_csv(QA / 'SOURCE_AND_THRESHOLD_DISPLAY_VALUES.csv', estimates)
    u.write_csv(QA / 'SOURCE_ONLY_TRACT_MEANS.csv', tract_means)
    u.dump(QA / 'SOURCE_GATE_AND_THRESHOLD_QA.json', dict(
        source_gate_visible_and_separate=True, independent_source_only_control_available=True,
        counterfactual='e_off = f * 1[f >= 0.50]; connectivity factor alone removed',
        exact_integral_identity='B_off = B_reference - L_source',
        reference_gate=GATE, new_control='G4_SOURCE_OFF_050', functionality_threshold=.5,
        threshold_tests=[.05, .75], source_connectivity_fixed_in_threshold_tests=True,
        station_order_identical=True, physical_sample_hashes_identical=True,
        physical_hashes_sha256=identity['physical_hashes_sha256'],
        all_1000_realization_ids_matched=True, full_study_population=9066522,
        G0='Removes BOTH F and C; excluded from this source-only control',
        no_damage_scheduling_ga_sampling_or_trajectory_generation=True,
        checks=checks, interpretation='Diagnostic relaxation, not evidence of delivered electricity'))
    return pd.DataFrame(estimates)


if __name__ == '__main__':
    import sys
    if '--acquire' in sys.argv:
        acquire()
    calculate()
