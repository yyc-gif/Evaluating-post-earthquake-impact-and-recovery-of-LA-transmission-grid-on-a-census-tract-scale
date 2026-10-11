"""Report the completed fixed cohort without sampling, scoring, or optimization."""
from __future__ import annotations

import argparse
import math
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from la_grid.diagnostics import standalone_ils_validation_20261011 as q

v, OUT = q.v, q.OUT
NAMES = (q.ILS, q.GA, q.IMPACT)
COLORS = {q.ILS: '#007F73', q.GA: '#6B59A5', q.IMPACT: '#AD5E24'}
STYLES = {q.ILS: '-', q.GA: '--', q.IMPACT: ':'}
SOURCE = 'src/la_grid/diagnostics/standalone_ils_validation_report_20261011.py'


def read_csv(name):
    return pd.read_csv(OUT / name, float_precision='round_trip')


def markdown(name, text):
    (OUT / name).write_text(text.strip() + '\n', encoding='utf-8', newline='\n')


def interval(row, simultaneous=False):
    prefix = 'simultaneous95_' if simultaneous else 'ci95_'
    return f"[{row[prefix+'low']:.6f}, {row[prefix+'high']:.6f}]"


def verify_tables(frame, effects, levels):
    assert set(frame.strategy) == set(NAMES)
    assert len(frame) == 6000 and frame.realization_id.nunique() == 2000
    assert not frame.duplicated(['realization_id', 'strategy']).any()
    checks, distributions = 0, []
    for metric in v.METRICS:
        pivot = frame.pivot(index='realization_id', columns='strategy', values=metric)
        for name in NAMES:
            x = pivot[name].to_numpy(float)
            row = levels[(levels.strategy == name) & (levels.metric == metric)].iloc[0]
            expected = dict(mean=x.mean(), sd=x.std(ddof=1), mcse=x.std(ddof=1)/np.sqrt(q.N),
                median=np.median(x), p05=np.quantile(x,.05), p95=np.quantile(x,.95),
                p99=np.quantile(x,.99), worst5pct_mean=np.sort(x)[-math.ceil(.05*q.N):].mean())
            for field, value in expected.items():
                assert abs(value - row[field]) < 1e-10, (name, metric, field)
                checks += 1
        for reference in (q.IMPACT, q.GA):
            x = (pivot[q.ILS] - pivot[reference]).to_numpy(float)
            row = effects[(effects.reference == reference) & (effects.metric == metric)].iloc[0]
            expected = dict(mean_difference=x.mean(), sd_difference=x.std(ddof=1),
                mcse=x.std(ddof=1)/np.sqrt(q.N), median_difference=np.median(x),
                p05=np.quantile(x,.05), p95=np.quantile(x,.95), p99=np.quantile(x,.99),
                worst5pct_mean=np.sort(x)[-math.ceil(.05*q.N):].mean(),
                min_difference=x.min(), max_difference=x.max())
            for field, value in expected.items():
                assert abs(value - row[field]) < 1e-10, (reference, metric, field)
                checks += 1
            assert row.improved_count == (x < -1e-9).sum()
            assert row.worsened_count == (x > 1e-9).sum()
            assert row.ties_count == (abs(x) <= 1e-9).sum()
            checks += 3
            if metric == v.PRIMARY:
                win, loss = x[x < -1e-9], x[x > 1e-9]
                distributions.append(dict(reference=reference, count=2000,
                    favorable_count=len(win), unfavorable_count=len(loss),
                    favorable_conditional_mean_hr=win.mean(), unfavorable_conditional_mean_hr=loss.mean(),
                    favorable_contribution_to_full_mean_hr=win.sum()/q.N,
                    unfavorable_contribution_to_full_mean_hr=loss.sum()/q.N,
                    overall_mean_hr=x.mean(), descriptive_only=True,
                    no_exclusions_or_alternative_ranking=True))
    components = ['L_self_population_mass_weighted_hr', 'L_threshold_population_mass_weighted_hr',
                  'L_source_population_mass_weighted_hr']
    conservation = np.max(abs(frame[components].sum(axis=1) - frame[v.PRIMARY]))
    assert conservation < 1e-10
    assert v.read(OUT / 'NUMERICAL_AND_COHORT_QA.json')['status'] == 'PASS'
    assert v.read(OUT / 'PRESERVATION_VERIFIED.json')['status'] == 'PASS'
    v.csv(OUT / 'PAIRED_DISTRIBUTION_DESCRIPTION.csv', pd.DataFrame(distributions))
    return dict(status='PASS', summary_statistic_checks=checks,
        primary_vs_component_sum_max_abs_error_hr=float(conservation),
        bootstrap_not_reselected_or_recomputed=True, new_scoring_calls=0, new_sampling_calls=0,
        source_sha256=v.sha(q.R / SOURCE))


def figures(frame, curves):
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10,
        'axes.labelsize': 9, 'legend.fontsize': 9, 'axes.spines.top': False, 'axes.spines.right': False,
        'savefig.dpi': 220, 'figure.dpi': 150})
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.25), layout='constrained')
    for ax, end, title in zip(axes, (480, 100), ('A. Full frozen horizon', 'B. Early recovery detail')):
        for name in NAMES:
            a = curves[curves.strategy == name]
            ax.step(a.time_hr, a.population_availability, where='post', label=name,
                    color=COLORS[name], linestyle=STYLES[name], linewidth=1.7)
        ax.set(xlim=(0,end), ylim=(-.02,1.02), xlabel='Time (h)', title=title)
        ax.grid(alpha=.18)
    axes[0].set_ylabel('Mean modeled service availability')
    axes[0].legend(loc='lower right', frameon=False)
    fig.savefig(OUT / 'DIAGNOSTIC_RECOVERY_CURVES.png')
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), layout='constrained', sharey=True)
    pivot = frame.pivot(index='realization_id', columns='strategy', values=v.PRIMARY)
    for ax, reference, panel in zip(axes, (q.IMPACT,q.GA), ('A','B')):
        x = np.sort((pivot[q.ILS]-pivot[reference]).to_numpy(float))
        ax.step(x, np.arange(1,q.N+1)/q.N, where='post', color=COLORS[reference], linewidth=1.5)
        ax.axvline(0, color='#444444', linewidth=.8)
        ax.axvline(x.mean(), color='#007F73', linestyle='--', linewidth=1.1, label='Paired mean')
        ax.axvline(np.median(x), color='#777777', linestyle=':', linewidth=1.3, label='Paired median')
        ax.set(xlabel=f'ILS minus {reference} loss (h)', ylim=(0,1),
               title=f'{panel}. Paired realization differences')
        ax.grid(alpha=.18)
        ax.legend(loc='upper left', frameon=False)
    axes[0].set_ylabel('Empirical cumulative fraction')
    fig.savefig(OUT / 'DIAGNOSTIC_PAIRED_LOSS_ECDF.png')
    plt.close(fig)


def report():
    freeze = q.verify()
    frame, effects, levels = (read_csv(name) for name in
        ('REALIZATION_OUTCOMES.csv', 'PAIRED_EFFECTS.csv', 'POLICY_OUTCOMES.csv'))
    numerical, accounting, preservation = (v.read(OUT / name) for name in
        ('NUMERICAL_AND_COHORT_QA.json', 'EXECUTION_ACCOUNTING.json', 'PRESERVATION_VERIFIED.json'))
    qa = verify_tables(frame, effects, levels)
    post_tests = {}
    for name in ('POST_EXECUTION_TESTS.xml', 'POST_EXECUTION_TESTS_WORKSPACE.xml'):
        suite = ET.parse(OUT / name).getroot().find('testsuite')
        post_tests[name] = {key: int(suite.attrib[key]) for key in ('tests','failures','errors','skipped')}
    assert post_tests['POST_EXECUTION_TESTS.xml']['failures'] == 3
    assert post_tests['POST_EXECUTION_TESTS_WORKSPACE.xml'] == dict(tests=17,failures=0,errors=0,skipped=0)
    qa['post_execution_test_runs'] = post_tests
    qa['failed_test_attempt_cause'] = 'Sandbox TEMP atomic replacement denied before fixture sampling; same unchanged tests pass in checked workspace basetemp.'
    assert accounting['optimizer_calls'] == 0 and accounting['production_evaluations'] == 6000
    assert accounting['genuine_physical_sampling_calls'] == accounting['repair_sampler_calls'] == 2000
    assert len(accounting['case_accounting']) == 2000 and accounting['failed_cases'] == 0
    assert not frame.T80_censored.any() and not frame.tasks_completed_after_480.any()
    primary = effects[(effects.reference == q.IMPACT) & (effects.metric == v.PRIMARY)].iloc[0]
    secondary = effects[(effects.reference == q.GA) & (effects.metric == v.PRIMARY)].iloc[0]
    def level(name, metric=v.PRIMARY):
        return levels[(levels.strategy == name) & (levels.metric == metric)].iloc[0]
    assert primary.ci95_high < 0 and secondary.simultaneous95_high < 0
    v.write(OUT / 'FIXED_STRATEGY_IDENTITIES.json', dict(parent_commit=q.PARENT,
        strategies=freeze['strategies'], resampled_or_reselected=False, promoted=False))
    figures(frame, read_csv('RECOVERY_CURVES.csv'))
    rows = ['| Policy | Mean loss (h) | SD | MCSE | Median | P95 | P99 | Highest 5% mean |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in NAMES:
        r = level(name)
        rows.append(f'| {name} | {r["mean"]:.6f} | {r.sd:.6f} | {r.mcse:.6f} | {r["median"]:.6f} | '
                    f'{r.p95:.6f} | {r.p99:.6f} | {r.worst5pct_mean:.6f} |')
    contrasts = ['| Contrast | Mean difference (h) | MCSE | Pointwise 95% CI | Simultaneous 95% family CI | Favorable / unfavorable / tied |',
                 '|---|---:|---:|---|---|---|']
    for r in (primary, secondary):
        contrasts.append(f'| ILS minus {r.reference} | {r.mean_difference:.6f} | {r.mcse:.6f} | {interval(r)} | '
            f'{interval(r,True)} | {int(r.improved_count)} / {int(r.worsened_count)} / {int(r.ties_count)} |')
    distribution = ['| Contrast | Paired median | P05 | P95 | P99 | Minimum | Maximum | Highest 5% difference mean |',
                    '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in (primary, secondary):
        distribution.append(f'| ILS minus {r.reference} | {r.median_difference:.6f} | {r.p05:.6f} | {r.p95:.6f} | '
            f'{r.p99:.6f} | {r.min_difference:.6f} | {r.max_difference:.6f} | {r.worst5pct_mean:.6f} |')
    component_rows = ['| ILS minus reference | Self (h) | Threshold (h) | Source (h) | Sum / total (h) |',
                      '|---|---:|---:|---:|---:|']
    for ref in (q.IMPACT,q.GA):
        a = effects[effects.reference == ref].set_index('metric')
        vals = [a.loc[m,'mean_difference'] for m in ('L_self_population_mass_weighted_hr',
                'L_threshold_population_mass_weighted_hr', 'L_source_population_mass_weighted_hr')]
        component_rows.append(f'| {ref} | {vals[0]:+.6f} | {vals[1]:+.6f} | {vals[2]:+.6f} | {sum(vals):+.6f} |')
    labels = {'burden_Q1_hr':'Q1 population loss (h)', 'burden_Q2_hr':'Q2 population loss (h)',
        'burden_Q3_hr':'Q3 population loss (h)', 'burden_Q4_hr':'Q4 population loss (h)',
        'hospital_mean_normalized_burden_hr':'Mean hospital-linked tract loss (h)',
        'absolute_Q4_minus_Q1_hr':'Absolute Q4-Q1 gap (h)', 'signed_Q4_minus_Q1_hr':'Signed Q4-Q1 gap (h)',
        'burden_gini':'Population-weighted tract-loss Gini', 'T80_restricted_hr':'Population T80, restricted (h)',
        'total_travel_hr':'Total directed crew travel (crew-h)', 'makespan_hr':'Last task completion (h)'}
    other = ['| Endpoint | ILS minus Impact mean [pointwise 95% CI] | ILS minus GA mean [pointwise 95% CI] |',
             '|---|---|---|']
    for metric, label in labels.items():
        cells = []
        for ref in (q.IMPACT,q.GA):
            r = effects[(effects.reference == ref) & (effects.metric == metric)].iloc[0]
            cells.append(f'{r.mean_difference:+.6f} {interval(r)}')
        other.append(f'| {label} | {cells[0]} | {cells[1]} |')
    archive = v.read(OUT / 'FULL_EVIDENCE_MANIFEST.json')
    prereg = v.read(OUT / 'PREREGISTRATION_COMMIT.json')
    markdown('STANDALONE_ILS_PROSPECTIVE_VALIDATION_REPORT.md', f'''
# Standalone ILS: Fixed Prospective Validation

## Decision

The prespecified modeled-benefit criterion against Impact-first is met. The frozen standalone ILS also has lower mean loss than the formal GA on this new cohort under the simultaneous two-contrast interval. **This does not authorize replacing the formal GA or imply that ILS dominates GA across realizations or outcomes.** No strategy is promoted.

ILS mean loss is {level(q.ILS)['mean']:.6f} h, versus {level(q.GA)['mean']:.6f} h for GA and {level(q.IMPACT)['mean']:.6f} h for Impact-first. Relative mean reductions are {-primary.mean_difference/level(q.IMPACT)['mean']*100:.4f}% versus Impact and {-secondary.mean_difference/level(q.GA)['mean']*100:.4f}% versus GA. These are normalized cumulative service-deficit hours, not delivered MW or elapsed restoration-time savings. The GA comparison is a small mean effect with a positive paired median and a majority of unfavorable realizations.

## Prospective Authority and Integrity

- Parent research freeze: `{q.PARENT}` on `diagnostics/standalone-ils-final-method-decision-20261010`.
- The human author explicitly authorized exactly 2,000 new physical realizations and three fixed comparisons on 2026-10-11. `AUTHORIZATION.json` records the exact request.
- Execution/analysis code, seed rules, sequences, authorization and engineering checks were committed before drawing: `{prereg['commit']}`. Its receipt records zero new physical draws.
- `EXECUTION_FREEZE.json` incorporates the parent's original prospective plan and original model/input/source hashes. Its embedded pre-execution status is historical, not a claim that this now-completed experiment remains unexecuted.
- Independent PCG64 per-realization entropy `[2026110100,r]`, r=0..1999; namespace `{freeze['sampling_namespace']}`. These streams were not chosen after inspecting outcomes.
- All 2,000 DS/duration pairs were saved before policy evaluation. Each saved pair is shared by all three strategies; all 6,000 cases finish before final analysis. No interim effect-based stopping, expansion, tuning, optimizer call, candidate reselection, or exclusion.
- 2,000 distinct new physical-pair hashes; zero overlap against 3,064 prior identities (64 planning, 1,000 original 2pc50 evaluation and 2,000 earlier validation states). Earlier validation was read only for identity/entropy and byte-hash preservation, never its outcome tables or trajectories.

## Model and Endpoint

The original 92-station network, 318 graph edges, 14 Core sources, 57 C57_D1 crews, directed travel, original damage/repair samplers, 0.5 source gate and M1 population mapping of 2,315 tracts are retained. Priority lists are full 92-station permutations; realized damaged tasks are handled by the original production scheduler. The ILS name identifies the already-selected fixed order; no ILS search is executed on this cohort.

For normalized tract modeled service availability a_i(t), the endpoint is B_i = integral from 0 to 480 h of [1-a_i(t)] dt; B_pop = sum_i population_i B_i / sum_i population_i. The original evaluator's resolved-mass normalization is retained. The current M1 primary and dependency-mass-weighted component totals agree within {qa['primary_vs_component_sum_max_abs_error_hr']:.2e} h over all 6,000 records. Do not assume that equality for a different mapping.

The frozen horizon is 480 h, distinct from the longer planning bound of {freeze['prospective_plan']['planning_horizon_hr']:.9f} h. Exact completion-event left-rectangle integration is used, not trapezoids on a coarse grid. Task completion events after 480 h and censored T80 are preserved by design. In this actual cohort there are zero late task events and zero censored population T80 cases, and all three policies reach effective modeled service 1 by 480 h. This observation is not an assumption that arbitrary future samples have zero post-480 loss.

## Fixed Statistical Analysis

20,000 paired whole-realization percentile bootstrap resamples use seed 2026110200 and a shared resample bank. The unit of replication is the physical realization, not a tract, station, crew, policy row, or checkpoint. The primary two-sided pointwise 95% interval is the frozen decision rule versus Impact-first. Both population-loss contrasts additionally use Bonferroni 97.5% individual intervals for simultaneous 95% coverage of the two-contrast family. No other endpoint family is multiplicity-adjusted; all other intervals are descriptive pointwise. No equivalence or noninferiority margin was registered.

{chr(10).join(rows)}

{chr(10).join(contrasts)}

All contrasts are ILS minus reference; negative population-loss differences favor ILS. MCSE is the paired-difference SD divided by sqrt(2,000), distinct from the bootstrap interval.

## Distribution: Mean Benefit Is Not Dominance

{chr(10).join(distribution)}

Against Impact-first, {int(primary.improved_count)}/2,000 ({primary.improved_count/q.N*100:.2f}%) improve and {int(primary.worsened_count)} worsen. Against GA, only {int(secondary.improved_count)}/2,000 ({secondary.improved_count/q.N*100:.2f}%) improve; {int(secondary.worsened_count)} ({secondary.worsened_count/q.N*100:.2f}%) worsen. The paired GA median is {secondary.median_difference:+.6f} h despite mean {secondary.mean_difference:+.6f} h. Larger favorable differences offset more numerous small unfavorable differences. This is an asymmetric distribution, not evidence that a typical new realization benefits from ILS versus GA. `PAIRED_DISTRIBUTION_DESCRIPTION.csv` reports the conditional means and their contributions using the full cohort without removing samples or creating an alternative ranking.

The highest-5% policy-loss means above are each policy's own largest 100 losses, not paired differences for a shared subset. The highest-5% difference mean is the largest 100 ILS-minus-reference differences and describes unfavorable changes, not the same tail estimand. These tail summaries are descriptive, with no registered superiority test for quantiles or conditional tails.

## Exact Loss Decomposition

The original production gate partitions total loss into self, functionality threshold and source-connectivity losses. Population dependency mass weighting is retained.

{chr(10).join(component_rows)}

Against both references, lower mean source-connectivity loss offsets higher mean self and threshold losses. The GA source decrease is larger than the small final net mean decrease. This is a decomposition of the effects of each entire fixed scheduling policy under the same physical state, not proof that any single station move caused the gain. No station-level controlled counterfactual is performed here.

## Tradeoffs and Negative Results

{chr(10).join(other)}

Quartiles are the original fixed social-vulnerability groupings, not Stage 7 community classes. Hospital loss is an unweighted mean of normalized modeled loss among hospital-linked tracts, not hospital downtime, patient outcomes, or electricity delivered to individual hospitals.

The GA comparison has worse mean Q2 loss, hospital-linked tract loss, T80, absolute Q4-Q1 gap and tract-loss Gini under ILS. Mean Q3 loss and makespan differences remain unresolved at pointwise 95%; an interval crossing zero is not equivalence. Q4 mean loss improves, but its paired median difference is positive. Against Impact-first, the absolute Q4-Q1 gap and Gini also increase despite lower overall and all-quartile mean losses. Signed gap reductions do not automatically mean improved equality: mean Q4-Q1 is already negative under every policy. No claim of uniform fairness improvement is warranted.

ILS total directed crew travel is lower on average than both references, but travel summed across simultaneous crews is crew-hours, not elapsed makespan. Mean makespan is not demonstrably shorter under either comparison's pointwise interval. Do not infer faster completion of the full restoration campaign from lower cumulative population loss or summed travel alone.

## Numerical and Execution QA

- {numerical['exact_trajectory_reintegration_checks']:,} actual saved trajectory reintegrations passed; independent kernel maximum absolute disagreement: {numerical['independent_kernel_max_abs_error_hr']:.3e} h.
- Eventwise self + threshold + source conservation maximum error: {numerical['component_conservation_max_abs_error']:.3e}.
- {qa['summary_statistic_checks']:,} independent summary-statistic/sign-count checks against final realization records passed. No bootstrap reselection/recalculation in reporting.
- No missing primary records, failed prospective cases, case deletions, or resumed completed prospective cases. Synthetic late-event/censoring handling and identical saved-state crash-resume were separately tested before drawing.
- Genuine damage sampler calls: {accounting['genuine_physical_sampling_calls']:,}; repair sampler calls: {accounting['repair_sampler_calls']:,}; production evaluations: {accounting['production_evaluations']:,}; independent kernel checks: {accounting['independent_kernel_evaluations']:,}; optimizer calls: 0.
- Draw wall time: {accounting['draw_wall_seconds']:.3f} s; eight-worker evaluation batch wall time: {accounting['evaluation_batch_wall_seconds']:.3f} s; sum of case evaluation wall times: {accounting['sum_case_evaluation_wall_seconds']:.3f} s; final analysis wall time: {numerical['analysis_wall_seconds']:.3f} s. These measure this fixed-policy evaluation only, not optimizer training cost or GA-versus-ILS search speed.
- Engineering used 16 successful original/synthetic production/kernel evaluations and one additional failed-cache-attempt production evaluation; zero new physical draws. An initial scenario-registry assertion was corrected before sampling. The Windows JIT cache path was shortened without scientific source changes.
- Seventeen guard/scheduler/source-gate tests passed before sampling. Exact runtime versions and source byte hashes are in `EXECUTION_FREEZE.json`; original sampler AST/constant agreement is in `SAMPLING_SOURCE_AUDIT.json`.
- The same 17 tests passed after execution using a checked workspace `--basetemp`. A preceding post-execution attempt had three sandbox TEMP atomic-rename permission failures and 14 passes; the three failures occurred before fixture sampling. Both JUnit records are retained (`POST_EXECUTION_TESTS.xml` and `POST_EXECUTION_TESTS_WORKSPACE.xml`). No source change, new physical generation or prospective rescoring was used to resolve the environment issue.

## Preservation and Evidence

`PRESERVATION_VERIFIED.json` confirms unchanged protected revision HEAD, branch, staged-diff hash and {preservation['protected_revision_file_count']} protected files; {preservation['old_validation_file_count']} old-validation files and {preservation['frozen_source_file_count']} parent-source-package files are also byte-identical. No formal GA, model, manuscript, Stage 7 label, original trajectory or original sample is overwritten.

`FIXED2000_FULL_EVIDENCE.zip` contains {archive['member_count']:,} files ({archive['archive_bytes']:,} bytes): all physical draws and RNG receipts, all three policies' dispatch/completion records, exact event/state/tract-loss arrays and hash-completion receipts. Archive SHA256: `{archive['archive_sha256']}`. Every archive member passes SHA256 round-trip verification. Summary tables are outside the archive for direct review. `FIXED_STRATEGY_IDENTITIES.json` and `EXECUTION_FREEZE.json` retain every full permutation and sequence hash.

The diagnostic PNGs are generated only from these completed new-cohort records. The recovery curve display uses an hourly step summary; inference and loss integration use the archived exact event clock, not this displayed grid. The ECDF includes all differences, zero, paired mean and paired median without trimming the favorable tail. These are diagnostic artifacts only; no manuscript artwork is regenerated.

Commit/push and actual remote Git LFS payload verification are recorded in `REMOTE_PUBLICATION_VERIFIED.json` once completed. That receipt identifies the data commit; a later receipt-only commit leaves the data payload unchanged. `OUTPUT_HASHES.json` hashes this local report package excluding itself and later publication/visual-review receipts.

## Interpretation and Next Decision

This is independent simulated-physics generalization evidence for one previously selected standalone ILS sequence, under the unchanged 2pc50 model. It is not a fresh test of the optimizer's probability of discovering good solutions, an untouched test of every historical optimizer decision, real-world calibration, or validation against observed utility restoration. Shared fixed hazard/fragility/network/repair assumptions remain limitations.

The frozen primary benefit criterion succeeds. The secondary mean result also favors ILS, but its approximately {-secondary.mean_difference/level(q.GA)['mean']*100:.4f}% mean gain over GA must be weighed against majority-case worsening, hospital/T80/equity tradeoffs and the asymmetric difference distribution. The experiment is complete at the authorized fixed sample size; it does not justify more tuning or another candidate search on these outcomes. The formal GA remains unchanged. Author review of these mean-versus-distribution and stakeholder tradeoffs is required before any separate promotion decision.

## Reproduction and Sources

`PROTOCOL_AND_COMMANDS.md` records original execution commands. For a new checkout of this committed package, hydrate only the frozen input payloads, retain the recorded runtime and do not run `execute` to invent a second validation cohort. The evidence ZIP can reconstruct the original `cohort/` tree; analysis/report phases read that saved tree without drawing or optimizing. The existing complete-cohort execution guard refuses a second execution.

```powershell
$env:PYTHONPATH='src'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:NUMBA_NUM_THREADS='1'
$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'vils7-numba'
python -B -m la_grid.diagnostics.standalone_ils_validation_analysis_20261011 analyze
python -B -m la_grid.diagnostics.standalone_ils_validation_report_20261011 report
python -B -m la_grid.diagnostics.standalone_ils_validation_report_20261011 hashes
```

Numerical authority: the parent's `FUTURE_VALIDATION_FREEZE.json`; original `src/la_grid/revision/r1_realization_scheduling.py`, `r1_source_gate.py` and `formal/offline.py`; unchanged `src/la_grid/diagnostics/independent_validation_20261010.py`; archived new `DRAW.json`, `SUMMARY.csv`, `TASK_EXECUTION.csv` and `TRAJECTORIES.npz`. All source/version hashes are local recorded evidence, not inferred from file names.
''')
    markdown('README.md', '''
# Fixed Standalone ILS Validation Package

Start with [the completed report](STANDALONE_ILS_PROSPECTIVE_VALIDATION_REPORT.md). This package contains exactly 2,000 new physical realizations evaluated under three frozen priority orders, with no optimizer, tuning, candidate reselection, or formal strategy promotion.

- `PAIRED_EFFECTS.csv`: fixed mean contrasts and uncertainty, including negative results.
- `POLICY_OUTCOMES.csv`: levels, distributions and descriptive tails.
- `REALIZATION_OUTCOMES.csv`: all 6,000 policy records.
- `FIXED2000_FULL_EVIDENCE.zip` / `FULL_EVIDENCE_MANIFEST.json`: full physical, schedule and trajectory evidence with every member hash.
- `EXECUTION_FREEZE.json` / `FIXED_STRATEGY_IDENTITIES.json`: original inputs, runtime, seeds and full 92-station orders.
- `NUMERICAL_AND_COHORT_QA.json` / `REPORT_NUMERICAL_QA.json`: production/kernel, reintegration and report checks.
- `PRESERVATION_VERIFIED.json`: original model, formal strategy, old samples and unrelated staged content preserved.
- `REMOTE_PUBLICATION_VERIFIED.json`: actual downloaded remote Git LFS payloads and data commit, after publication.

Negative differences favor ILS only for lower-is-better metrics. Signed quartile gaps and effective availability do not share that interpretation. Other endpoint intervals are descriptive pointwise, not a multivariate superiority test. Current scientific outputs and manuscript figures are unchanged.
''')
    v.write(OUT / 'REPORT_NUMERICAL_QA.json', qa)
    print('REPORT_NUMERICAL_QA_PASS', qa['summary_statistic_checks'], flush=True)


def hashes():
    q.verify()
    excluded = {'OUTPUT_HASHES.json', 'REMOTE_PUBLICATION_VERIFIED.json', 'FIGURE_VISUAL_QA.json'}
    names = [p for p in OUT.iterdir() if p.is_file() and p.name not in excluded]
    files = {p.name: dict(bytes=p.stat().st_size,sha256=v.sha(p)) for p in sorted(names)}
    sources = {name: v.sha(q.R / name) for name in (SOURCE,
        'src/la_grid/diagnostics/standalone_ils_validation_20261011.py',
        'src/la_grid/diagnostics/standalone_ils_validation_analysis_20261011.py',
        'tests/test_standalone_ils_validation_20261011.py')}
    v.write(OUT / 'OUTPUT_HASHES.json', dict(files=files, supporting_sources=sources,
        excluded_from_self_manifest=sorted(excluded), loose_cohort_archived=True))
    print('OUTPUT_HASHES_SAVED', len(files), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['report','hashes'])
    phase = parser.parse_args().phase
    report() if phase == 'report' else hashes()
