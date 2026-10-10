"""Saved-case engineering checks and readiness report; never new physical draws."""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import tempfile
import time
from unittest.mock import patch

import numpy as np
import pandas as pd

from la_grid.diagnostics import independent_validation_20261010 as v
from la_grid.diagnostics.ga_actionable_delay_20261010 import completion_loss
from la_grid.revision.r1_distributional_metrics import population_weighted_gini


def raises(kind, callback):
    try:
        callback()
    except kind:
        return True
    raise AssertionError('Expected refusal: ' + kind.__name__)


def same_schedule(model, policy, ds, duration, rid):
    original = v.evaluate(model, policy, ds, duration, rid)
    decoder = model['decoder']
    x = decoder.decode(order=decoder.order(policy['sequence']), damage=ds,
        duration=duration, origins=model['origins'])
    np.testing.assert_array_equal(original[-1].to_numpy(), x[0])
    index = {s:i for i,s in enumerate(model['ids'])}
    for _, row in original[1].iterrows():
        i = index[row.task_id]
        assert row.arrival_hr==x[1][i] and row.travel_hr==x[2][i]
        assert row.crew_index==x[3][i] and row.dispatch_rank==x[5][i]+1
        assert row.previous_task_id==(model['ids'][x[4][i]] if x[4][i]>=0 else None)
    return original


def planning_check(model):
    ids, ctx = model['ids'], model['ctx']
    index = {s:i for i,s in enumerate(ids)}
    neighbors, offsets = [], [0]
    for s in ids:
        neighbors.extend(index[n] for n in sorted(ctx['graph'].neighbors(s)))
        offsets.append(len(neighbors))
    flag = np.array([s in ctx['sources'] for s in ids])
    mass = model['mapping'].weight.T @ model['mapping'].population
    hplan = v.read(v.OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')['planning_horizon_hr']
    loss = {}
    for policy in v.policies():
        if policy['strategy'] not in (v.GA, v.ILS):
            continue
        values = []
        for r in range(64):
            ds, dur = (x[r] for x in model['banks']['planning'])
            completion = model['decoder'].decode(order=model['decoder'].order(policy['sequence']),
                damage=ds, duration=dur, origins=model['origins'])[0]
            values.append(completion_loss(np.nan_to_num(completion, nan=0), ds, flag,
                np.array(offsets,np.int64), np.array(neighbors,np.int64), mass, float(mass.sum()), hplan))
        loss[policy['strategy']] = np.array(values)
    assert abs(loss[v.GA].mean()-32.997840773882714)<1e-8
    assert abs(loss[v.ILS].mean()-32.99613736538884)<1e-8
    delta = loss[v.ILS]-loss[v.GA]
    assert (delta < -1e-9).sum()==14 and (delta>1e-9).sum()==50
    assert np.delete(delta,15).mean()>0
    prior = v.R / 'results/diagnostics/ga_actionable_delay_six_slot_20261010'
    exact = v.read(prior / 'EXACT_SIX_SLOT_RESULTS.json')
    audit = v.read(prior / 'TASK_AB.json')
    assert exact['status']=='COMPLETE' and len(exact['results'])==120
    assert exact['enumerated_assignments']==sum(r['enumerated'] for r in exact['results'])==86400
    assert all(r['improving_assignments']==0 for r in exact['results'] if r['parent'] in ('frozen_ga','refined_ils'))
    assert audit['status']=='PASS' and abs(audit['route_relaxation_mean_loss_hr']-31.514846689663546)<1e-10
    return dict(frozen_GA_planning_hr=float(loss[v.GA].mean()), refined_ILS_planning_hr=float(loss[v.ILS].mean()),
        ILS_minus_GA_hr=float(delta.mean()), ILS_improves_count=int((delta<-1e-9).sum()),
        ILS_worsens_count=int((delta>1e-9).sum()), without_realization15_delta_hr=float(np.delete(delta,15).mean()),
        original_enumeration_sha256=v.sha(prior / 'EXACT_SIX_SLOT_RESULTS.json'),
        original_relaxation_sha256=v.sha(prior / 'TASK_AB.json'),
        exact_enumeration_summary=dict(neighborhoods=120,assignments=86400,
            frozen_GA_and_refined_ILS_improvements=0,tolerance_hr=exact['floating_precision_tolerance_hr']),
        relaxation_summary={k:audit[k] for k in ('route_relaxation_mean_loss_hr','duration_only_mean_loss_hr',
            'maximum_completion_formula_error_hr','scheduled_station_checks')},
        planning_not_generalization=True, new_validation_samples=0)


def dry_run():
    start = time.perf_counter()
    freeze = v.verify_freeze()
    counts = {name:0 for name in v.SAMPLERS}
    def prohibited(name):
        def fail(*args, **kwargs):
            counts[name] += 1
            raise AssertionError('Preparation must not call physical sampling: '+name)
        return fail
    with patch.object(v.core,'sample_damage_states',prohibited('sample_damage_states')), \
         patch.object(v.core,'damage_to_functionality_and_repair',prohibited('damage_to_functionality_and_repair')), \
         patch.object(v.core,'draw_positive_normal',prohibited('draw_positive_normal')):
        model = v.load_model()
        planning = planning_check(model)
        v.write(v.OUT / 'OPTIMIZATION_EVIDENCE_RECONCILIATION.json', v.clean(planning))
        root = v.OUT / 'dry_run'
        selected = [('planning',r) for r in (0,15,39,55)] + [('evaluation',r) for r in (0,1,2)]
        longest = int(np.argmax(model['banks']['evaluation'][1].max(axis=1)))
        selected.append(('evaluation',longest))
        selected = list(dict.fromkeys(selected))
        records, parity, decoder_cases = [], [], 0
        tick = time.perf_counter()
        for split, r in selected:
            rid = f'2pc50__{split}_{r:04d}'
            ds, dur = (x[r] for x in model['banks'][split])
            before = v.physical_hash(model['ids'],ds,dur)
            record = v.run_case(model, root / 'cases' / rid, rid, ds, dur)
            for policy in v.policies():
                if policy['strategy']=='unconstrained':
                    values = v.evaluate(model,policy,ds,dur,rid)
                else:
                    values = same_schedule(model,policy,ds,dur,rid)
                    decoder_cases += 1
                parity.append(values[0]['independent_kernel_abs_error_hr'])
                tract = values[4]['normalized_burden_hr']
                # Independent explicit tract integration and pairwise Gini check.
                raw_loss = values[3]['L_total']
                explicit = ((raw_loss[:-1] @ model['mapping'].weight.T) * np.diff(values[2])[:,None]).sum(axis=0)
                np.testing.assert_allclose(explicit,tract,atol=1e-9,rtol=0)
                g = population_weighted_gini(pd.Series(tract,index=model['mapping'].tract_ids),
                    pd.Series(model['mapping'].population,index=model['mapping'].tract_ids))
                assert abs(g-values[0]['burden_gini'])<1e-10
                comp = sum(values[0][k+'_population_mass_weighted_hr'] for k in ('L_self','L_threshold','L_source'))
                assert abs(comp-values[0][v.PRIMARY])<1e-9
            assert v.physical_hash(model['ids'],ds,dur)==before
            records.append(record)
        case_seconds = time.perf_counter()-tick
        ids = [f'2pc50__{split}_{r:04d}' for split,r in selected]
        effects = v.export(root,model,ids,independent=False)
        old_exports = v.read(root / 'EXPORT_RECEIPT.json')['files_sha256']
        v.export(root,model,ids,independent=False)
        assert v.read(root / 'EXPORT_RECEIPT.json')['files_sha256']==old_exports
        checks = dict(original_scheduler_fast_decoder_parity=True, independent_kernel_parity=True,
            explicit_tract_integration_parity=True, independent_pairwise_gini_parity=True,
            component_accounting=True, deterministic_export_replay=True)
        ds, dur = (x[15] for x in model['banks']['planning'])
        rid = '2pc50__planning_0015'
        previous = {r['physical_sha256'] for r in v.read(v.OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json')}
        with tempfile.TemporaryDirectory(prefix='val4-qa-', dir=v.R) as temp:
            temp = Path(temp)
            checks['long_path_adapter_idempotent'] = v.long_path(v.long_path(temp))==v.long_path(temp)
            checks['protected_archive_path_refused'] = raises(ValueError,
                lambda:v.check_archive_path(Path(freeze['protected_revision_checkout']),freeze))
            checks['formal_archive_path_refused'] = raises(ValueError,
                lambda:v.check_archive_path(v.FORMAL,freeze))
            (temp/'unrelated').mkdir()
            (temp/'unrelated'/'existing.txt').write_text('preserve',encoding='utf-8')
            checks['unrelated_nonempty_archive_refused'] = raises(ValueError,
                lambda:v.check_archive_path(temp/'unrelated',freeze))
            checks['no_authorization_refused_before_sampling'] = raises(PermissionError,
                lambda:v.execute(None,temp / 'forbidden'))
            bad_auth = temp / 'BAD_AUTH.json'
            v.write(bad_auth,dict(sample_size=2001,freeze_sha256=v.sha(v.OUT / 'FINAL_VALIDATION_FREEZE_RECEIPT.json')))
            checks['wrong_authorization_refused'] = raises(PermissionError,lambda:v.require_authorization(bad_auth))
            checks['overlap_existing_1064_aborts'] = raises(ValueError,
                lambda:v.check_overlap(model['ids'],ds,dur,previous,set()))
            checks['overlap_within_new_archive_aborts'] = raises(ValueError,
                lambda:v.check_overlap(model['ids'],ds,dur,set(),{v.physical_hash(model['ids'],ds,dur)}))
            checks['deliberate_interruption'] = raises(InterruptedError,
                lambda:v.run_case(model,temp/'resume',rid,ds,dur,crash_after_policy=4))
            assert not (temp/'resume/COMPLETE.json').exists()
            # Orphan temporary bytes cannot become evidence or affect re-evaluation.
            (temp/'resume'/'SUMMARY.csv.tmp').write_bytes(b'partial crash bytes')
            resumed = v.run_case(model,temp/'resume',rid,ds,dur)
            clean = v.run_case(model,temp/'clean',rid,ds,dur)
            assert resumed==clean
            with patch.object(v,'evaluate',side_effect=AssertionError('Completed case must not re-evaluate')):
                assert v.run_case(model,temp/'resume',rid,ds,dur)==resumed
            checks['whole_realization_crash_resume_byte_equal'] = True
            checks['committed_checkpoint_reused_without_evaluation'] = True
            changed = dur.copy(); changed[np.flatnonzero(ds>0)[0]] += .001
            checks['changed_physical_resume_rejected'] = raises(AssertionError,
                lambda:v.run_case(model,temp/'resume',rid,ds,changed))
            summary = temp/'resume'/'SUMMARY.csv'
            data = summary.read_bytes(); summary.write_bytes(data+b'corrupt')
            checks['checkpoint_corruption_rejected'] = raises(AssertionError,
                lambda:v.run_case(model,temp/'resume',rid,ds,dur))
            # A crash in the draw/commit gap must stop, not generate a replacement.
            v.write(temp/'sampling/physical/0000/DRAW_STARTED.json',dict(r=0))
            checks['uncommitted_draw_aborts_without_redraw'] = raises(RuntimeError,
                lambda:v.generate_one(model,temp/'sampling',0,previous,set()))
            with v.exclusive(temp/'locking'):
                checks['concurrent_executor_refused'] = raises(FileExistsError,
                    lambda:next(v.exclusive(temp/'locking').gen))
            # Artificial engineering corner cases are transformations, not MC draws.
            long_duration = dur.copy(); long_duration[ds>0] += 1000
            truncated = v.evaluate(model,next(p for p in v.policies() if p['strategy']==v.GA),
                ds,long_duration,'synthetic_truncation_QA')
            assert truncated[2][-1]==480 and truncated[0]['T80_censored']==1
            assert truncated[0]['population_T80_hr'] is None and truncated[0]['T80_restricted_hr']==480
            assert truncated[0]['tasks_completed_after_480']>0 and truncated[1].completion_hr.max()>480
            checks['480h_censoring_and_late_task_retention'] = True
            zero = v.evaluate(model,next(p for p in v.policies() if p['strategy']==v.GA),
                np.zeros(92,dtype=np.int64),np.zeros(92),'synthetic_DS0_QA')
            assert zero[0][v.PRIMARY]==0 and zero[0]['population_T80_hr']==0
            checks['all_DS0_corner_case'] = True
            # Explicit no-dropping and whole-state resampling tests.
            frame = pd.read_csv(v.long_path(root/'REALIZATION_OUTCOMES.csv'),float_precision='round_trip')
            broken = frame.copy(); broken.loc[0,v.PRIMARY] = np.nan
            checks['missing_primary_aborts_not_dropped'] = raises(ValueError,lambda:v.paired_statistics(broken))
            checks['missing_policy_aborts'] = raises(ValueError,lambda:v.paired_statistics(frame.iloc[1:]))
            checks['duplicate_realization_policy_aborts'] = raises(ValueError,
                lambda:v.paired_statistics(pd.concat([frame,frame.iloc[:1]])))
            censored_frame = frame.copy()
            censored_frame['population_T80_hr'] = np.nan
            censored_frame['T80_restricted_hr'] = 480
            censored_frame['T80_censored'] = 1
            censor_effects,_ = v.paired_statistics(censored_frame)
            assert (censor_effects[censor_effects.metric=='T80_restricted_hr'].mean_difference==0).all()
            assert (censor_effects.n==len(ids)).all()
            checks['all_censored_records_retained'] = True
            shifted = frame.copy()
            # Identical within-case paired shifts must yield zero MCSE/CI width.
            base = frame[frame.strategy=='impact-first'].set_index('realization_id')[v.PRIMARY]
            shifted[v.PRIMARY] = shifted.realization_id.map(base)
            shifted.loc[shifted.strategy==v.GA,v.PRIMARY] += 2
            e,_ = v.paired_statistics(shifted)
            row = e[(e.candidate==v.GA)&(e.reference=='impact-first')&(e.metric==v.PRIMARY)].iloc[0]
            assert abs(row.mean_difference-2)<1e-12 and abs(row.mcse)<1e-12
            assert abs(row.ci_low-2)<1e-12 and abs(row.ci_high-2)<1e-12
            checks['paired_whole_state_bootstrap_known_effect'] = True
            # Time the production archive path alone, excluding additional QA calls.
            tick = time.perf_counter()
            for split,r in selected:
                sample_id = f'2pc50__{split}_{r:04d}'
                d,t = (a[r] for a in model['banks'][split])
                v.run_case(model,temp/'timed'/sample_id,sample_id,d,t)
            production_seconds = time.perf_counter()-tick
        assert not any(counts.values())
        assert all(checks.values())
    current = v.snapshot(Path(freeze['protected_revision_checkout']))
    assert current==v.read(v.OUT/'PRESERVATION_BASELINE.json')
    v.write(v.OUT/'PRESERVATION_VERIFIED.json',dict(status='PASS',protected_file_count=len(current['files_sha256']),
        staged_diff_sha256=current['staged_diff_sha256'],revision_head=current['revision_head'],
        revision_branch=current['revision_branch'],baseline_sha256=v.sha(v.OUT/'PRESERVATION_BASELINE.json')))
    size = sum(p.stat().st_size for p in v.long_path(root/'cases').rglob('*') if p.is_file())
    estimate = int(np.ceil(size/len(ids)*2000))
    reserve = max(4_469_082_696,estimate*3+500_000_000)
    v.write(v.OUT/'CAPACITY_RUNTIME_ESTIMATE.json',dict(old_case_count=len(ids),old_case_archive_bytes=size,
        measured_policy_case_seconds=production_seconds,measured_policy_realizations=len(ids)*13,
        additional_old_case_parity_QA_wall_seconds=case_seconds,
        estimated_2000_case_archive_bytes=estimate,reserved_storage_bytes=reserve,
        disk_free_bytes=shutil.disk_usage(v.R).free,temporary_files_same_volume=True,
        estimated_evaluation_and_case_IO_seconds=production_seconds/len(ids)*2000,
        physical_generation_runtime='NOT_BENCHMARKED: no physical sampler called',
        excluded_costs=['new physical sampling','cold setup/compilation','final bootstrap','figures and publication'],
        estimate_not_guarantee=True,headroom_pass=shutil.disk_usage(v.R).free>reserve))
    assert shutil.disk_usage(v.R).free>reserve
    qa = dict(status='PASS',scope='OLD_SAVED_CASE_ENGINEERING_ONLY_NOT_INDEPENDENT_VALIDATION',
        old_case_ids=ids,old_case_count=len(ids),policy_count=13,decoder_parity_policy_cases=decoder_cases,
        max_independent_kernel_error_hr=max(parity),checks=checks,
        physical_sampler_call_counts=counts,new_validation_samples_generated=0,
        protected_files_verified=len(current['files_sha256']),wall_seconds=time.perf_counter()-start,
        execution_code_sha256=freeze['code_sha256'],freeze_sha256=v.sha(v.OUT/'FINAL_VALIDATION_FREEZE_RECEIPT.json'),
        export_receipt_sha256=v.sha(root/'EXPORT_RECEIPT.json'),
        engineering_repairs_before_final_freeze=['Missing LFS metadata hydrated read-only with verified OID',
            'Historical source commits unavailable in isolated Git were verified in protected original Git, with CRLF/LF hashes',
            'Original samplers read from pre-reorganization historical checkout',
            'Idempotent Windows long-path handling and writable fsync mode corrected'],
        planning_means={k:planning[k] for k in ('frozen_GA_planning_hr','refined_ILS_planning_hr',
            'ILS_improves_count','ILS_worsens_count','without_realization15_delta_hr')})
    v.write(v.OUT/'VALIDATION_DRY_RUN_QA.json',qa)
    report(model,qa)
    print('READY FOR AUTHORIZED VALIDATION; engineering checks:',len(checks),'; new draws=0',flush=True)


def markdown(path,text):
    path = v.long_path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text.strip()+'\n',encoding='utf-8',newline='\n')


def report(model,qa):
    capacity = v.read(v.OUT/'CAPACITY_RUNTIME_ESTIMATE.json')
    freeze = v.read(v.OUT/'FINAL_VALIDATION_FREEZE_RECEIPT.json')
    markdown(v.OUT/'VALIDATION_EXECUTION_READINESS.md',f'''# Independent Validation Readiness

## Status
**READY FOR AUTHORIZED VALIDATION**, not **INDEPENDENT VALIDATION COMPLETED**.

No new physical validation realizations were generated. All three physical-sampling functions were patched to fail during the complete dry run; observed calls: {qa['physical_sampler_call_counts']}. This readiness statement does not authorize sampling. Only explicit author approval permits the fixed 2,000-realization execution.

## Frozen Evidence
Starting commit `{v.START}`; diagnostic branch `{v.BRANCH}`. Authoritative model: 92 stations, 318 retained edges, 14 Core sources, 57 C57_D1 crews, M1 dependency weights over 2,315 tracts, unchanged directed travel, DS>0 task queue, earliest-available crew (first index tie break), completion-step functionality and 0.5 source gate. Population and fixed SOVI quartiles/hospital membership are read from the original M1 metadata, not recomputed from validation outcomes.

Recomputed 64-case planning loss: Frozen GA {qa['planning_means']['frozen_GA_planning_hr']:.12f} h; refined ILS {qa['planning_means']['refined_ILS_planning_hr']:.12f} h. ILS improves 14/64 and worsens 50/64; without realization 15, ILS-minus-GA is {qa['planning_means']['without_realization15_delta_hr']:+.12f} h. Original 120-neighborhood / 86,400-assignment receipts and 31.514846689664 h independent-route relaxation are retained and hash-linked in OPTIMIZATION_EVIDENCE_RECONCILIATION.json. No six-slot improvement of the two selected incumbents and no global-optimality claim. Training quality is not generalization evidence; refined ILS remains secondary, not a formal GA replacement.

## Comparator And Sampling Audit
FINAL_COMPARATOR_MANIFEST.json reconciles all 12 distinct full 92-ID permutations plus Unconstrained, with source commits and file/sequence hashes. The nine original sequences plus centrality, closeness and refined ILS retain their existing identities. The formal selected candidate files are unchanged. Unconstrained retains the same physical durations and source gate, but removes travel/crew competition.

The isolated Git database does not contain the old addendum's historical nine source-commit objects. Those original declarations were therefore checked read-only in the protected repository's original Git database and verified there; missing local objects must not be mistaken for incorrect historical provenance. The manifest retains those source commits and separately records the verified isolated-copy commit, raw Git blob SHA and checked-out file SHA. CRLF/LF-only differences are explicitly recorded and content-checked; no source file was rewritten. Historical sampler source lives at root paths in the protected repository's original commit, before the later src reorganization. The audit retains original source excerpts and their file hash rather than incorrectly claiming the reorganized paths existed then.

Original sampler ASTs and physical-law constants were compared with executable commit `{model['frozen']['executable_code_commit_sha']}` and passed. PGA and fragility source hashes match FINAL_EXECUTION_VALIDATION.json. The 2pc50 sampler uses the original new-fragility columns, not historical-hazard columns. No new correlations, demand, station capacity, or duration law were introduced. All 64 planning and 1,000 inspected damage/duration pairs were rehashed and checked against the original physical manifest. The separate PCG64 namespace is SeedSequence([202610091,3,2,r]), r=0..1999. Each pair is drawn once and shared across all 13 conditions.

Exact overlap with old or earlier new pairs latches ABORT_OVERLAP.json and stops for review, never redraws. DS-only equality is not physical-pair equality; both canonical little-endian DS/duration hashes and the station-ordered composite hash are retained. There is no overlap evidence yet for the undrawn cohort. Future RNG pre/post states are archived; generation determinism is specified by pinned runtime, functions and independent per-index seeds, but has not been empirically tested using new physical draws in this preparation.

## Numerical And Operational QA
{qa['old_case_count']} original saved states, including planning realization 15 and the maximum-duration inspected case; all 13 policies. {qa['decoder_parity_policy_cases']} original-scheduler/compiled-decoder parity checks. Maximum minimax-kernel versus production loss error: {qa['max_independent_kernel_error_hr']:.3g} h. Original source gate and offline exact-event evaluator execute every case. Explicit tract integration, independent pairwise population Gini, and self/threshold/source accounting pass. Two complete exports have identical hashes, including PNGs. A deliberate interruption after five policies resumes from the same physical state and matches clean-run bytes. Changed physical context, missing policies, duplicated records, missing primary data, corrupt checkpoints, absent/wrong authorization and concurrent execution are refused.

Synthetic engineering checks transform an old duration vector (not MC sampling) to force completion beyond 480 h. They confirm clipped integration, full late-completion event retention, null/censored T80 and restricted-time=480. No T80 records are silently discarded; conditional reached-only mean is labeled and separate. All-DS0 is also tested.

## Analysis Contract
Primary: cumulative population-weighted normalized modeled service loss, exact left-rectangle integration over 0-480 h; Frozen GA minus Impact-first. Negative favors GA. The horizon is not H_plan={freeze['planning_horizon_hr']:.9f} h. Original M1 row sums equal one to numerical tolerance, so normalized population and resolved-mass forms agree. Hospital metric is equal-tract mean among hospital-linked tracts, not hospital-count weighting.

Fixed N=2,000; Monte Carlo SE of paired differences; 20,000 whole-realization paired bootstrap resamples, seed 2026100901, two-sided 95% percentile CI. A common resample bank is used across endpoints and policies. Primary effect is not selected after outcome inspection. Secondary comparisons are descriptive pointwise intervals, not simultaneous/confirmatory evidence. Signed Q4-Q1 and per-realization absolute Q4-Q1 are calculated before averaging. Gini is per-realization before averaging. T80 contrasts use explicitly restricted times and censoring proportions; reached-only means do not replace the censored estimand. No optional stopping, tuning, chromosome reselection or sample-size extension. Sample-level GA/ILS changes include all distributional and loss-component fields. Figures show recovery and Q4-Q1 availability disparity, while cumulative loss disparity is separately tabulated.

## Checkpoints And Capacity
An atomic physical DRAW.json precedes policy evaluation. A marker written before sampling detects an interrupted uncommitted draw and halts for author review rather than silently drawing again. Policy units commit only after all 13 outputs and their hashes are complete. Interrupted policy work re-evaluates the same saved physical state. Same-volume temporary files use flush/fsync and atomic replace; exclusive RUN.lock prevents simultaneous writers. A stale lock after process termination must be inspected against its recorded PID/host before removal; never automatically remove a potentially live lock. Existing nonempty unrelated archives and protected/formal output paths are refused. Readiness/freeze cannot be silently overwritten by another prepare command; changed code or inputs fail verification.

Measured old-case archive: {capacity['old_case_archive_bytes']:,} bytes. Scaled 2,000-case estimate: {capacity['estimated_2000_case_archive_bytes']:,} bytes; reserved including temporary/export headroom: {capacity['reserved_storage_bytes']:,} bytes; observed free disk: {capacity['disk_free_bytes']:,} bytes. Measured production evaluation and case I/O {capacity['measured_policy_case_seconds']:.3f} s for {capacity['measured_policy_realizations']} policy-realizations, scaling to {capacity['estimated_evaluation_and_case_IO_seconds']:.1f} s for 2,000 states. This timing uses fresh old-case archive writes and excludes the extra parity/Gini test calls. These are engineering estimates, excluding new sampling, setup/compilation, final bootstrap, figures and publication; not guaranteed runtimes. Sampling was intentionally not benchmarked. Check capacity again immediately before authorized execution.

## Preservation And Limitations
{qa['protected_files_verified']} protected revision files, revision HEAD/branch and staged binary diff verified unchanged. No restoration simulation authority, formal strategy, existing clustering result, manuscript figure or physical sample was replaced. Final artifacts here are diagnostic-only and ready for review. Explicit author authorization is the remaining execution gate; no technical QA blocker identified. Future completion requires all 2,000 unique physical pairs, 26,000 policy records, hashes, full statistics and final reproducibility receipt.

Independent simulation validation tests generalization to new states under the same model, not accuracy against actual utility restoration or an external empirical cohort. The dry-run estimates/figures are engineering fixtures with selected old states and cannot support independent-validation inference. Readiness and source hashes are frozen before any new draw. Changes to code, inputs, runtime, sample count or policies require a new reviewed freeze, not quiet substitution.
''')
    module = 'la_grid.diagnostics.independent_validation_20261010'
    markdown(v.OUT/'VALIDATION_EXECUTION_COMMANDS.md',f'''# Reproducible Commands

Run in the diagnostic checkout, with the pinned Anaconda Python runtime.

```powershell
$env:PYTHONPATH = 'src'
$env:NUMBA_CACHE_DIR = Join-Path $env:TEMP 'val4-20261010-numba'
$env:OPENBLAS_NUM_THREADS = '1'
$env:MKL_NUM_THREADS = '1'
$env:NUMBA_NUM_THREADS = '1'
& C:\\Users\\yinch\\anaconda3\\python.exe -m {module} verify
& C:\\Users\\yinch\\anaconda3\\python.exe -m {module} dry-run
```

The dry run reads only saved physical cases and synthetic engineering transformations; it never calls a physical sampler. Reproduces checks, receipts, tables, figures and same-state crash/resume tests. Exact commands for input hydration/freeze appear in SETUP_COMMAND.json. Recreating prepare after a code change intentionally creates a different freeze; it must be reviewed before authorization.

## Future Execution Only After Explicit Author Approval

No authorization file is supplied by this preparation. After approval, record the actual author name, UTC timestamp and verbatim request in an external authorization JSON with fields:

```json
{{
  "authorization_type": "EXPLICIT_AUTHOR_APPROVAL_FOR_FIXED_2000_VALIDATION",
  "author": "ACTUAL_AUTHOR",
  "authorized_at_utc": "ACTUAL_APPROVAL_TIMESTAMP",
  "verbatim_author_request": "ACTUAL_EXPLICIT_APPROVAL",
  "freeze_sha256": "{qa['freeze_sha256']}",
  "sample_size": 2000,
  "allow_policy_reselection": false
}}
```

These placeholders are documentation, not permission. The executor checks the receipt and authorization, pinned runtime/code/inputs, readiness QA and capacity before invoking sampling. Use a new external dedicated archive, never a formal-results or manuscript path. An archive inside this repository is allowed only beneath results/diagnostics/independent_validation_ready_20261010/authorized_validation:

```powershell
& C:\\Users\\yinch\\anaconda3\\python.exe -m {module} execute --authorization C:\\PATH\\ACTUAL_AUTHOR_APPROVAL.json --archive C:\\PATH\\independent_validation_fixed_2000
```

Resume using the exact same command and authorization. Completed cases are verified and reused; no optional sample-count flags exist. A completed run rechecks and republishes evidence without redrawing. Do not delete physical receipts or redefine RUN_IDENTITY to restart. If a crash leaves RUN.lock, verify recorded process is dead on the recorded host before removing only that stale lock. A DRAW_STARTED marker without DRAW.json or an ABORT_OVERLAP receipt is a stop-for-review condition, not an invitation to regenerate. No intermediate effect tables are produced before all 2,000 cases finish.

Final exports: PRIMARY_PAIRED_EFFECT.csv; PAIRED_EFFECTS.csv; POLICY_OUTCOMES.csv; T80_CENSORING.csv; REALIZATION_OUTCOMES.csv; GA_REFINED_ILS_REALIZATION_CHANGES.csv; RECOVERY_DISPARITY_CURVES.csv; RECOVERY.png; DISPARITY.png; EXPORT_RECEIPT.json; REPRODUCIBILITY_RECEIPT.json. Per-realization archives contain shared physical vectors/hashes, exact f/F/C/e and loss-component arrays, station/tract integrals, complete dispatch/crew/origin/travel/arrival/completion records, event times and policy identities. Per-draw receipts include PCG64 before/after state and canonical byte hashes.
''')
    v.write(v.OUT/'READINESS_RECEIPT.json',dict(status='READY_FOR_AUTHORIZED_VALIDATION',
        independent_validation_completed=False,new_validation_samples_generated=0,
        freeze_sha256=qa['freeze_sha256'],qa_sha256=v.sha(v.OUT/'VALIDATION_DRY_RUN_QA.json'),
        files_sha256={name:v.sha(v.OUT/name) for name in ('VALIDATION_EXECUTION_READINESS.md',
            'VALIDATION_EXECUTION_COMMANDS.md','CAPACITY_RUNTIME_ESTIMATE.json','PRESERVATION_VERIFIED.json')}))


if __name__=='__main__':
    dry_run()
