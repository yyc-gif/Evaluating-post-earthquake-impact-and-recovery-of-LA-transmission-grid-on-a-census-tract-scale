"""Post-completion read-only checks and lossless evidence packaging; no sampling."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

from la_grid.diagnostics import independent_validation_20261010 as v

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / 'fixed_2000_20261010'


def audit():
    receipt = v.read(ARCHIVE / 'REPRODUCIBILITY_RECEIPT.json')
    assert receipt['status'] == 'INDEPENDENT_VALIDATION_COMPLETED'
    assert (receipt['sample_count'], receipt['unique_physical_hashes'],
            receipt['policy_count'], receipt['original_overlap_count']) == (2000, 2000, 13, 0)
    assert not (ARCHIVE / 'RUN.lock').exists()
    assert not (ARCHIVE / 'ABORT_OVERLAP.json').exists()
    freeze = v.verify_freeze()
    protected = v.snapshot(Path(freeze['protected_revision_checkout']))
    assert protected == v.read(v.OUT / 'PRESERVATION_BASELINE.json')
    export = v.read(ARCHIVE / 'EXPORT_RECEIPT.json')
    assert v.sha(ARCHIVE / 'EXPORT_RECEIPT.json') == receipt['export_sha256']
    for name, expected in export['files_sha256'].items():
        assert v.sha(ARCHIVE / name) == expected, name
    assert v.sha(HERE / 'AUTHORIZATION_FIXED_2000_20261010.json') == receipt['run_identity']['authorization_sha256']
    model = v.load_model()
    policies = v.policies()
    names = [p['strategy'] for p in policies]
    ids = model['ids']
    assert len(names) == len(set(names)) == 13
    for policy in policies[:-1]:
        assert len(policy['sequence']) == 92 and set(policy['sequence']) == set(ids)
        assert v.identity(policy['sequence']) == policy['sequence_sha256'], policy['strategy']
    frame = pd.read_csv(v.long_path(ARCHIVE / 'REALIZATION_OUTCOMES.csv'), float_precision='round_trip')
    expected_ids = [f'2pc50__independent_{r:04d}' for r in range(2000)]
    assert len(frame) == 26000 and not frame.duplicated(['realization_id', 'strategy']).any()
    assert set(frame.realization_id) == set(expected_ids) and set(frame.strategy) == set(names)
    assert np.isfinite(frame[list(v.METRICS)].to_numpy()).all()
    assert frame.groupby('realization_id').physical_sha256.nunique().eq(1).all()
    assert frame.groupby('realization_id').strategy.nunique().eq(13).all()
    np.testing.assert_array_equal(frame.population_T80_hr.isna(), frame.T80_censored.astype(bool))
    np.testing.assert_allclose(frame.population_T80_hr.fillna(480), frame.T80_restricted_hr, atol=1e-10, rtol=0)
    assert frame.T80_restricted_hr.between(0, 480).all()
    effects = pd.read_csv(v.long_path(ARCHIVE / 'PAIRED_EFFECTS.csv'), float_precision='round_trip')
    assert len(effects) == 14 * len(v.METRICS)
    recomputed_effects, recomputed_levels = v.paired_statistics(frame)
    levels = pd.read_csv(v.long_path(ARCHIVE / 'POLICY_OUTCOMES.csv'), float_precision='round_trip')
    for saved, recomputed in ((effects, recomputed_effects), (levels, recomputed_levels)):
        assert list(saved.columns) == list(recomputed.columns)
        for column in saved.columns:
            if pd.api.types.is_numeric_dtype(saved[column]):
                np.testing.assert_allclose(saved[column], recomputed[column], atol=1e-10, rtol=0)
            else:
                assert saved[column].tolist() == recomputed[column].tolist()
    for row in effects.itertuples(index=False):
        wide = frame.pivot(index='realization_id', columns='strategy', values=row.metric)
        diff = wide[row.candidate] - wide[row.reference]
        np.testing.assert_allclose([diff.mean(), diff.std(ddof=1) / np.sqrt(2000)],
                                   [row.mean_difference, row.mcse], atol=1e-10, rtol=0)
        assert ((diff < -1e-9).sum(), (diff > 1e-9).sum(), (diff.abs() <= 1e-9).sum()) == (
            row.improved_count, row.worsened_count, row.ties_count)
        assert np.isfinite([row.ci_low, row.ci_high]).all() and row.ci_low <= row.ci_high
    old = {x['physical_sha256'] for x in v.read(v.OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json')}
    generated, physical_rows = set(), []
    mass = model['mapping'].weight.T @ model['mapping'].population
    maximum_gate_error = maximum_integral_error = 0.
    for r, rid in enumerate(expected_ids):
        draw_path = ARCHIVE / 'physical' / f'{r:04d}' / 'DRAW.json'
        assert v.sha(draw_path) == receipt['physical_receipts_sha256'][str(r)]
        record = v.read(draw_path)
        payload = record.pop('payload_sha256')
        assert hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest() == payload
        assert record['r'] == r and record['entropy'] == [202610091, 3, 2, r]
        assert record['station_ids'] == ids
        ds, duration = np.asarray(record['damage_state'], dtype=np.int64), np.asarray(record['duration_hr'], float)
        assert ds.shape == duration.shape == (92,) and ((0 <= ds) & (ds <= 4)).all()
        assert np.isfinite(duration).all() and (duration[ds > 0] > 0).all() and (duration[ds == 0] == 0).all()
        assert record['damage_sha256'] == hashlib.sha256(ds.astype('<i8').tobytes()).hexdigest()
        assert record['duration_sha256'] == hashlib.sha256(duration.astype('<f8').tobytes()).hexdigest()
        h = v.check_overlap(ids, ds, duration, old, generated)
        assert h == record['physical_sha256']
        generated.add(h)
        physical_rows.append(dict(realization_id=rid, physical_sha256=h,
            task_count=int((ds > 0).sum()), mean_duration_all_stations_hr=duration.mean(),
            maximum_duration_hr=duration.max(), **{f'DS{i}_count': int((ds == i).sum()) for i in range(5)}))
        folder = ARCHIVE / 'cases' / rid
        completed = v.read(folder / 'COMPLETE.json')
        assert completed['policy_count'] == 13 and completed['identity']['physical_sha256'] == h
        for name, digest in completed['files_sha256'].items():
            assert v.sha(folder / name) == digest
        summary = frame[frame.realization_id == rid].set_index('strategy').loc[names]
        assert summary.task_count.eq((ds > 0).sum()).all()
        with np.load(v.long_path(folder / 'TRAJECTORIES.npz'), allow_pickle=False) as z:
            assert z['policies'].tolist() == names and z['station_ids'].tolist() == ids
            assert z['tract_ids'].tolist() == model['mapping'].tract_ids.tolist()
            # Decompress each stored array once for the entire shared realization.
            arrays = {k: z[k] for k in ('f', 'F', 'C', 'e', 'L_self', 'L_threshold', 'L_source', 'L_total')}
            times_all = z['event_time_hr']
            integrals = z['station_component_integrals_hr']
            tract_loss = z['tract_normalized_loss_hr']
            f, F, C, e = (arrays[k] for k in ('f', 'F', 'C', 'e'))
            assert np.isfinite(f).all() and ((0 <= f) & (f <= 1)).all()
            np.testing.assert_array_equal(F, f >= .5)
            assert np.isin(C, [0., 1.]).all() and (C <= F).all()
            maximum_gate_error = max(maximum_gate_error, float(np.abs(e - f * F * C).max()))
            np.testing.assert_allclose(arrays['L_self'] + arrays['L_threshold'] + arrays['L_source'], arrays['L_total'], atol=1e-12, rtol=0)
            np.testing.assert_allclose(arrays['L_total'], 1 - e, atol=1e-12, rtol=0)
            start = 0
            for j, length in enumerate(z['event_lengths']):
                times = times_all[start:start + length]
                assert times[0] == 0 and times[-1] == 480 and (np.diff(times) > 0).all()
                for k, name in enumerate(('L_self', 'L_threshold', 'L_source', 'L_total')):
                    integral = np.diff(times) @ arrays[name][start:start + length - 1]
                    np.testing.assert_allclose(integral, integrals[j, k], atol=1e-10, rtol=0)
                    observed = float(integral @ mass / mass.sum())
                    reported = summary.iloc[j][name + '_population_mass_weighted_hr']
                    maximum_integral_error = max(maximum_integral_error, abs(observed - reported))
                    np.testing.assert_allclose(observed, reported, atol=1e-9, rtol=0)
                weighted_tract = float(tract_loss[j] @ model['mapping'].population / model['mapping'].population.sum())
                np.testing.assert_allclose(weighted_tract, summary.iloc[j][v.PRIMARY], atol=1e-9, rtol=0)
                start += length
            assert start == len(times_all)
        if r % 500 == 499:
            print('POST_COMPLETION_INTEGRITY', r + 1, '/ 2000', flush=True)
    v.csv(HERE / 'PHYSICAL_COHORT_SUMMARY.csv', pd.DataFrame(physical_rows))
    distribution_rows = []
    for candidate, reference in ((v.GA, 'impact-first'), (v.ILS, v.GA)):
        wide = frame.pivot(index='realization_id', columns='strategy', values=v.PRIMARY)
        diff = (wide[candidate] - wide[reference]).to_numpy()
        distribution_rows.append(dict(candidate=candidate, reference=reference, n=2000,
            minimum_hr=diff.min(), maximum_hr=diff.max(), sd_hr=diff.std(ddof=1),
            **{f'p{q:02d}_hr': float(np.quantile(diff, q / 100)) for q in (1, 5, 25, 50, 75, 95, 99)}))
    v.csv(HERE / 'PAIRED_DIFFERENCE_DISTRIBUTIONS.csv', pd.DataFrame(distribution_rows))
    components = frame.groupby('strategy')[['L_self_population_mass_weighted_hr',
        'L_threshold_population_mass_weighted_hr', 'L_source_population_mass_weighted_hr', v.PRIMARY]].mean()
    np.testing.assert_allclose(components.iloc[:, :3].sum(axis=1), components[v.PRIMARY], atol=1e-9, rtol=0)
    v.csv(HERE / 'MEAN_LOSS_COMPONENTS.csv', components.reset_index())
    v.write(HERE / 'POST_COMPLETION_QA.json', dict(status='PASS', sample_count=2000,
        policy_record_count=26000, unique_physical_pairs=len(generated), old_pair_overlap=0,
        maximum_gate_identity_error=maximum_gate_error, maximum_reintegrated_loss_error_hr=maximum_integral_error,
        maximum_production_kernel_error_hr=float(frame.independent_kernel_abs_error_hr.max()),
        protected_file_count=len(protected['files_sha256']), staged_diff_sha256=protected['staged_diff_sha256'],
        frozen_code_inputs_and_runtime_unchanged=True, formal_candidate_unchanged=True,
        no_new_sampling_in_audit=True, fixed_20000_bootstrap_reproduced=True,
        audit_script_sha256=v.sha(Path(__file__)),
        export_sha256=receipt['export_sha256'], original_execution_commit=receipt['git_commit']))
    print('POST_COMPLETION_QA_PASS', flush=True)


def package():
    assert v.read(HERE / 'POST_COMPLETION_QA.json')['status'] == 'PASS'
    target = v.long_path(HERE / 'FIXED_2000_FULL_ARCHIVE.zip')
    manifest_path = HERE / 'FULL_ARCHIVE_MANIFEST.json'
    if target.exists():
        existing = v.read(manifest_path)
        assert v.sha(target) == existing['zip_sha256']
        print('EXISTING_CAPSULE_VERIFIED', flush=True)
        return
    files = sorted(p for p in v.long_path(ARCHIVE).rglob('*') if p.is_file())
    assert len([p for p in files if p.name == 'DRAW.json']) == 2000
    assert len([p for p in files if p.name == 'COMPLETE.json']) == 2000
    tmp = target.with_suffix('.zip.tmp')
    entries = {}
    with zipfile.ZipFile(tmp, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for path in files:
            relative = path.relative_to(v.long_path(ARCHIVE)).as_posix()
            data = path.read_bytes()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compresslevel=6)
            entries[relative] = dict(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    with zipfile.ZipFile(tmp) as z:
        assert z.namelist() == list(entries)
        for name, expected in entries.items():
            data = z.read(name)
            assert len(data) == expected['size'] and hashlib.sha256(data).hexdigest() == expected['sha256']
    os.replace(tmp, target)
    v.write(manifest_path, dict(status='FULL_ARCHIVE_VERIFIED', entry_count=len(entries),
        zip_sha256=v.sha(target), zip_bytes=target.stat().st_size, files=entries,
        generation='Lossless packaging only, no draws, simulations or policy selection'))
    print('FULL_ARCHIVE_VERIFIED', len(entries), target.stat().st_size, flush=True)


def report():
    assert v.read(HERE / 'POST_COMPLETION_QA.json')['status'] == 'PASS'
    receipt = v.read(ARCHIVE / 'REPRODUCIBILITY_RECEIPT.json')
    effects = pd.read_csv(v.long_path(ARCHIVE / 'PAIRED_EFFECTS.csv'), float_precision='round_trip')
    levels = pd.read_csv(v.long_path(ARCHIVE / 'POLICY_OUTCOMES.csv'), float_precision='round_trip')
    censoring = pd.read_csv(v.long_path(ARCHIVE / 'T80_CENSORING.csv'), float_precision='round_trip').set_index('strategy')
    components = pd.read_csv(v.long_path(HERE / 'MEAN_LOSS_COMPONENTS.csv'), float_precision='round_trip').set_index('strategy')
    primary = effects[(effects.candidate == v.GA) & (effects.reference == 'impact-first') & (effects.metric == v.PRIMARY)].iloc[0]
    ils = effects[(effects.candidate == v.ILS) & (effects.reference == v.GA) & (effects.metric == v.PRIMARY)].iloc[0]
    means = levels[levels.metric == v.PRIMARY].set_index('strategy')
    conclusion = ('The prespecified interval supports lower mean modeled burden for Frozen GA than Impact-first.'
        if primary.ci_high < 0 else 'The prespecified interval supports higher mean modeled burden for Frozen GA than Impact-first.'
        if primary.ci_low > 0 else 'The prespecified interval crosses zero; this batch does not resolve a mean difference between Frozen GA and Impact-first.')
    lines = ['# Fixed Independent Validation Results', '',
        'Status: **INDEPENDENT_VALIDATION_COMPLETED**. Diagnostic publication only; no formal strategy replacement.', '',
        '## Frozen Execution', '',
        f"Execution commit: `{receipt['git_commit']}`. Freeze SHA-256: `{receipt['run_identity']['freeze_sha256']}`.",
        'Author confirmation and unchanged supplied authorization are archived alongside this report.',
        'Exactly 2,000 new physical pairs and 26,000 policy-realization records; 13 frozen conditions.',
        'Original 92 stations, 318 edges, 14 sources, 57 C57_D1 crews, 2,315-tract M1 mapping, directed travel,',
        'DS>0 task queue, repair-duration laws and 0.5 source gate remain unchanged.',
        'One independent PCG64 SeedSequence([202610091,3,2,r]) per r=0..1999. Each physical pair was shared across all conditions.',
        'No overlap with the old 64 planning/1,000 inspected pairs, no within-cohort duplicate, no redraw or sample-count extension.', '',
        '## Prespecified Primary Comparison', '',
        'Population-weighted normalized modeled service deficit integrated over 0-480 hours.',
        'Effect is Frozen GA minus Impact-first; negative favors GA. Hours are equivalent normalized service-loss hours,',
        'not a change in station repair duration, outage duration for every customer, delivered MW or calendar recovery time.', '',
        f'- Impact-first mean: {means.loc["impact-first", "mean"]:.12f} h.',
        f'- Frozen GA mean: {means.loc[v.GA, "mean"]:.12f} h.',
        f'- Paired mean difference: {primary.mean_difference:.12f} h ({primary.mean_difference * 60:.9f} min).',
        f'- Monte Carlo SE: {primary.mcse:.12f} h.',
        f'- Fixed 95% paired percentile-bootstrap interval: [{primary.ci_low:.12f}, {primary.ci_high:.12f}] h.',
        f'- Relative mean difference versus Impact-first: {100 * primary.mean_difference / means.loc["impact-first", "mean"]:.9f}%.',
        f'- Improved/worsened/tied states: {int(primary.improved_count)}/{int(primary.worsened_count)}/{int(primary.ties_count)}.', '',
        conclusion,
        'This is independent Monte Carlo generalization evidence conditional on the unchanged physical and service model,',
        'not an empirical test against actual utility restoration. Statistical evidence does not establish a large practical benefit.', '',
        'The original 20,000 whole-realization resamples, seed 2026100901 and common resample bank were retained.',
        'All 2,000 observations enter the analysis. No intermediate effect inspection, tuning, selection or optional stopping occurred.', '',
        '## All Frozen Conditions', '',
        'Rows retain the frozen manifest order and are not a newly selected ranking.', '',
        '| Condition | Mean burden (h) | MCSE (h) | 95% pointwise interval (h) | Restricted mean T80 (h) | Censored / 2,000 |',
        '|---|---:|---:|---|---:|---:|']
    for policy in v.policies():
        name = policy['strategy']
        row, t80 = means.loc[name], censoring.loc[name]
        lines.append(f'| {name} | {row["mean"]:.9f} | {row.mcse:.9f} | [{row.ci_low:.9f}, {row.ci_high:.9f}] | {t80.restricted_mean_hr:.9f} | {int(t80.censored_count)} |')
    lines += ['', 'Policy-level intervals and every comparison other than the single prespecified primary are descriptive pointwise intervals.',
        'They are not multiplicity-adjusted evidence that a newly highest-ranked strategy should be promoted.',
        'Unconstrained removes travel/crew competition but retains the same physical durations and gate; it is not a feasible dispatch policy.', '',
        '## Refined ILS Secondary Diagnostic', '',
        f'ILS minus Frozen GA: {ils.mean_difference:.12f} h; MCSE {ils.mcse:.12f} h;',
        f'95% descriptive interval [{ils.ci_low:.12f}, {ils.ci_high:.12f}] h.',
        f'Improved/worsened/tied: {int(ils.improved_count)}/{int(ils.worsened_count)}/{int(ils.ties_count)}.',
        'The earlier planning objective favored the refined ILS by about 0.001703408495 h, with 14/64 improved states and a realization-15 ranking reversal.',
        'This fresh result is evaluated without replacing the formal GA candidate or choosing a new sequence from this cohort.',
        'PAIRED_DIFFERENCE_DISTRIBUTIONS.csv reports distribution quantiles for both predeclared comparisons.', '',
        '## Equity And Hospital Endpoints', '',
        'The following Frozen-GA-minus-Impact-first effects are prespecified secondary descriptions, not additional confirmatory tests.', '',
        '| Endpoint | Mean difference | MCSE | 95% pointwise interval |', '|---|---:|---:|---|']
    for metric in ('burden_Q1_hr', 'burden_Q4_hr', 'signed_Q4_minus_Q1_hr', 'absolute_Q4_minus_Q1_hr',
                   'burden_gini', 'hospital_mean_normalized_burden_hr', 'T80_restricted_hr', 'T80_censored'):
        row = effects[(effects.candidate == v.GA) & (effects.reference == 'impact-first') & (effects.metric == metric)].iloc[0]
        lines.append(f'| {metric} | {row.mean_difference:.12f} | {row.mcse:.12f} | [{row.ci_low:.12f}, {row.ci_high:.12f}] |')
    lines += ['', 'Gini is dimensionless and computed per realization before averaging. The signed Q4-Q1 gap is not the absolute gap;',
        'absolute differences are also computed per realization before averaging. Hospital burden uses equal-tract weighting among hospital-linked tracts.',
        'T80 means are restricted to 480 h with unreached observations retained as censored; the reached-only conditional mean is separately labeled in T80_CENSORING.csv.',
        'T80_censored contrasts are probability-point differences, not hours. Figure disparity is Q4-Q1 availability, not cumulative burden.', '',
        '## Exact Loss Accounting', '',
        'L_total = L_self + L_threshold + L_source. Entries below are mean normalized population-weighted integrals in hours.', '',
        '| Condition | Self | Threshold | Source connectivity | Total |', '|---|---:|---:|---:|---:|']
    for name in ('impact-first', v.GA, v.ILS, 'unconstrained'):
        row = components.loc[name]
        lines.append(f'| {name} | {row.iloc[0]:.9f} | {row.iloc[1]:.9f} | {row.iloc[2]:.9f} | {row.iloc[3]:.9f} |')
    lines += ['', 'These are accounting components, not causal station-level counterfactuals. Shared physical states do not imply identical self-loss',
        'because dispatch arrival/completion times can differ. No station movement is assigned a causal benefit here.', '',
        '## Verification And Reproduction', '',
        'POST_COMPLETION_QA.json verifies all 2,000 draw payloads, checkpoint files, shared-policy identities, saved gate algebra,',
        'exact-event station integrals, population-weighted tract loss, primary/secondary means and the complete fixed bootstrap export.',
        'Protected revision HEAD, branch, staged binary diff and 950 protected-file hashes match the pre-run baseline.',
        'No original samples, strategies, source gate, evaluator, scientific figures, manuscript or Stage 7 labels were replaced.', '',
        'Full per-state evidence is retained locally and published losslessly as FIXED_2000_FULL_ARCHIVE.zip with FULL_ARCHIVE_MANIFEST.json.',
        'Extract the capsule to a new diagnostic directory to inspect original draw RNG pre/post states, loss trajectories and dispatch records.',
        'Publication may advance the diagnostic branch only; the launcher intentionally demands the original c178bff checkout for execution.', '',
        '```powershell', "$env:PYTHONPATH='src'", "$env:OPENBLAS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'", "$env:NUMBA_NUM_THREADS='1'",
        '& C:\\Users\\yinch\\anaconda3\\python.exe -B results/diagnostics/independent_validation_ready_20261010/authorized_validation/audit_completed_validation.py audit',
        '& C:\\Users\\yinch\\anaconda3\\python.exe -B results/diagnostics/independent_validation_ready_20261010/authorized_validation/audit_completed_validation.py package',
        '```', '', 'These commands audit/package existing evidence. They do not authorize generating another cohort.', '',
        '## Decision', '',
        'The fixed independent-validation batch is complete. Preserve its prespecified primary interpretation and report secondary findings with their limits.',
        'Do not tune, select a replacement chromosome, extend this cohort, promote a strategy, or automatically update manuscript/formal figures from these results.',
        'Any scientific or editorial promotion remains a separate author decision.']
    path = v.long_path(HERE / 'INDEPENDENT_VALIDATION_RESULTS.md')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('RESULTS_REPORT_GENERATED_FROM_COMPLETED_DATA', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('audit', 'package', 'report'))
    args = parser.parse_args()
    {'audit': audit, 'package': package, 'report': report}[args.phase]()
