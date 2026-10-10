"""Consolidate completed local evidence without changing scientific outputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import psutil

from la_grid.paths import REPO_ROOT
from la_grid.diagnostics.ga_connectivity_lns_local_20261010 import OUT, METHODS
from la_grid.diagnostics.ga_connectivity_lns_audit_20261010 import results
from la_grid.diagnostics.ga_research_collect_20261009 import save, long_path
from la_grid.diagnostics.ga_init_param_20261009 import load
from la_grid.diagnostics.ga_connectivity_lns_failure_probe_20261010 import schedule_change
from la_grid.revision.formal.schedule import _decode


def read(name):
    return json.loads(long_path(OUT / name).read_text())


def sha(path):
    return hashlib.sha256(long_path(path).read_bytes()).hexdigest()


def reannotate_probe():
    # Reuse every retained proposal. Only native schedules are decoded again;
    # no fitness query or failed optimizer batch is replayed.
    data = read('FAILURE_PROBE_RESULTS.json')
    kernel, _, quality, _ = load()
    from la_grid.diagnostics.ga_connectivity_lns_audit_20261010 import FROZEN, REFINED
    parents = dict(shared_prior=tuple(quality),
        frozen_ga=tuple(json.loads((FROZEN / 'SELECTED_SEQUENCE.json').read_text())['sequence']),
        refined_ils=tuple(json.loads(REFINED.read_text())['sequence']))
    for r in data['records']:
        r.update(schedule_change(kernel, parents[r['parent']], r['sequence']))
    for s in data['summaries']:
        rows = [r for r in data['records'] if all(r[k] == s[k] for k in ('parent', 'targeting', 'repair'))]
        for field in ('mean_changed_crew_origins', 'mean_changed_firstwave_origins', 'mean_changed_travel_legs', 'mean_changed_predecessors'):
            s[field] = float(np.mean([r[field] for r in rows]))
    data['native_reannotation_schedule_decodes'] = 2 * 64 * len(data['records'])
    data['reannotation_objective_calls'] = 0
    save(OUT / 'FAILURE_PROBE_RESULTS.json', data)


def phenotypes(budget=100000):
    records, _ = results(budget)
    kernel, _, _, identity = load()
    cache, rows = {}, []
    for r in records:
        sha_seq = r['sequence_sha256']
        if sha_seq not in cache:
            order = np.array([kernel.index[x] for x in r['best_sequence']], np.int64)
            completion = hashlib.sha256()
            operational = hashlib.sha256()
            for b in range(64):
                data = _decode(order, kernel.damage[b], kernel.duration[b], kernel.origin_index, kernel.base, kernel.travel)
                for j in (0, 1, 2):
                    raw = np.nan_to_num(data[j], nan=np.inf).astype('<f8').tobytes()
                    operational.update(raw)
                    if j == 0:
                        completion.update(raw)
                crew_origin = np.where(data[3] >= 0, kernel.origin_index[np.maximum(data[3], 0)], -1)
                operational.update(crew_origin.astype('<i8').tobytes())
                operational.update(data[4].astype('<i8').tobytes())
            cache[sha_seq] = dict(completion64_sha256=completion.hexdigest(),
                origin_predecessor_travel_completion64_sha256=operational.hexdigest())
        rows.append(dict(method=r['method'], seed=r['seed'], sequence_sha256=sha_seq,
            loss_hr=r['search_best_loss_hr'], **cache[sha_seq]))
    save(OUT / f'FINAL_SCHEDULE_PHENOTYPES_{budget}.json', dict(input_identity=identity,
        native_decodes=len(cache) * 64, objective_calls=0, final_solutions_only=True,
        ignore_interchangeable_same_origin_crew_labels=True, rows=rows,
        summary=[dict(method=m, final_records=20, unique_chromosomes=len({r['sequence_sha256'] for r in rows if r['method'] == m}),
            unique_completion_classes=len({r['completion64_sha256'] for r in rows if r['method'] == m}),
            unique_origin_route_classes=len({r['origin_predecessor_travel_completion64_sha256'] for r in rows if r['method'] == m})) for m in METHODS]))


def report():
    records, summary = results()
    original = read('ORIGINAL_160_AUDIT.json')
    replay = read('OLD_BLOCK_MECHANISM_REPLAY.json')
    candidate = read('CANDIDATE_PRODUCTION_AND_INFLUENCE_100000.json')
    leverage = read('BUNDLE_SCHEDULING_LEVERAGE_100000.json')
    execution = read('CONFIRMATION_EXECUTION.json')
    probe = read('FAILURE_PROBE_RESULTS.json')
    readiness = read('VALIDATION_COMPARATORS_ADDENDUM.json')
    cuts = read('STATIC_SOURCE_CUTSET_CONTEXT.json')
    preservation = read('PRESERVATION_VERIFIED.json')
    phenotype = read('FINAL_SCHEDULE_PHENOTYPES_100000.json')
    assert preservation['status'] == 'PASS'
    lines = ['# Local noncontiguous connectivity LNS investigation', '',
        '## Decision', '',
        'Completed the archived-study audit, five-method 20-seed local comparison, engineering checks, bounded mechanism probes, independent all-64 production parity, sample-influence audit, and validation-readiness addendum. No formal policy, physics, planning sample, revision output or artwork was replaced.', '',
        'The tested connectivity-targeted insertion beam is not a better optimizer. Source-wait importance does not imply removable dispatch delay. The exact negative results are retained; they do not prove that every connectivity-aware optimizer would fail.', '',
        '## Authority and prospective design', '',
        '- Starting remote branch: `diagnostics/scheduling-aware-lns-20261010`, commit `79ac982afeb09fdfb3b79d8579208f4cda4c0133`.',
        '- Isolated standalone checkout and branch: `diagnostics/noncontiguous-connectivity-lns-local-20261010`.',
        '- Confirmation algorithm/design committed at `6de7efa` before any 100k case; bounded adaptive failure probe committed at `e69d0c9` before its outcomes.',
        '- Preserved original July92/318-edge/14-Core, C57_D1, 2pc50, 64 planning states, directed travel, realized repair durations, M1 population mapping, 0.5 gate and mean-loss objective.',
        '- Original planning horizon: 2855.2540131100995 h. This normalized population-weighted service-loss integral is not wall-clock recovery time or T80.',
        '- Shared older prior J=33.03813174326729 h plus seven rules, charged within every search budget. Frozen GA/refined ILS were not injected as priors.',
        '- Seeds1200..1219, 100,000 distinct full-permutation exact evaluations per method. Full seed records and SHA-256 identities: `ALL_FINAL_PERMUTATIONS_100000.json` and `SEED_LEVEL_100000.csv`.',
        '- First engineering invocation followed a failed Git commit due missing local author identity. The new-arm smoke invocation failed at bank serialization before LNS proposal construction; four reference smoke results completed and were retained. The collision was repaired, identity configured, and algorithm committed before successful new-arm smoke and all confirmation runs. No seed or algorithm-performance decision used these smoke outcomes.', '',
        '## Archived evidence, not reruns', '',
        'Official original runs: [LNS v1](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38033702030), [LNS v2](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38034064901), [160-outcome audit](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065463263), [proposal transfer](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38065546076). Original ZIPs, GitHub artifact digests, extracted-member hashes and run commits are retained in `ORIGINAL_ACTIONS_MANIFEST.json`.', '',
        'All160 full-budget observations pass original92-ID, 92-unique permutation, checksum, seed, exact100k budget and completion checks. Smoke/checkpoints are not additional independent optimizer observations. All8 transfer seeds pass, with2,048 arm-level observations /1,024 paired macros; no completed optimizer was rerun.', '',
        'Existing three-primary-contrast family is distinguished from two secondary contrasts. `ORIGINAL_160_AUDIT.json` also gives family-five simultaneous intervals; this avoids describing all five old contrasts as a simultaneous family-three result.', '',
        '| Parent | Old repair | Origin improved /512 | Mean64 improved /512 | Replayed first-wave origin changes | Earlier / later completions |',
        '|---|---|---:|---:|---:|---:|']
    for r in replay['summaries']:
        lines.append(f"| {r['start']} | {r['method']} | {r['origin_improving']} | {r['mean64_improving']} | {r['mean_changed_firstwave_origins']:.3f} | {r['mean_earlier_completions']:.3f} / {r['mean_later_completions']:.3f} |")
    lines += ['', 'Replay covers macro0 for each8 seeds, each2 parents and2 arms, locating the archived best candidate by hash without any objective reevaluation. Raw crew-label changes are larger, but same-origin crews may be interchangeable. Origin, predecessor, travel and completion differences are retained separately. These whole-proposal comparisons do not isolate a causal effect of one moved station.', '',
        'The old repaired witness is collected after reconnection and may include already-functional or non-bottleneck members. A rigid block alters other priorities, crew origins and downstream routes. Since most proposals fail their own originating state as well, negative cross-state transfer alone cannot explain the failure.', '',
        '## New mechanism and correctness', '',
        'All64 native schedules supply activation times. Minimax source paths account for alternative source routes; delayed path nodes plus queued predecessors form2-4-station bundles. Population dependency mass times source waiting is aggregated over64 states. A width-three beam relocates each member independently; every intermediate chromosome is a full92 permutation. Random-damaged and population-completion controls use the same size distribution, slots and repair effort. This random control inherits the size distribution from the connectivity bank, not its station identities.', '',
        'The original gate constrains every fitness value; a truncated witness bundle does not guarantee a particular component reconnects earlier. Source-wait weights are proposal heuristics, not a changed objective or a proof of causal gateway leverage. DS1 target-credit weights are conservatively half credit.', '',
        f"Minimax reachability matches native graph components at {read('SOURCE_TIMING_CORRECTNESS.json')['native_event_comparisons']:,} event points across all64 states. Four unit tests cover delayed sources, bypass routes, no sources, full-permutation repair and relative-order preservation. The static context audit verifies78 source-to-non-Core minimum internal vertex separators on a copied graph; cut-size counts are `{dict(sorted(Counter(r['minimum_internal_vertex_cut_size'] for r in cuts['targets']).items()))}`. These are one representative separator per target, not every cut or a time-dependent causal repair plan.", '',
        '## Completed 100k comparison', '',
        '| Method | Mean J (h) | SD (h) | Best J (h) | Mean attempts | Mean worker search wall (s) | Accepted current improvements | Archive improvements below prior |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in summary['methods']:
        ac = 'not recorded' if r['mean_accepted_current_improvements'] is None else f"{r['mean_accepted_current_improvements']:.2f}"
        ar = 'not recorded' if r['mean_archive_improvements_below_prior'] is None else f"{r['mean_archive_improvements_below_prior']:.2f}"
        lines.append(f"| {r['method']} | {r['mean_loss_hr']:.9f} | {r['sd_loss_hr']:.9f} | {r['min_loss_hr']:.9f} | {r['mean_attempts']:.0f} | {r['mean_wall_seconds']:.2f} | {ac} | {ar} |")
    lines += ['', 'GA reference wrapper does not serialize its best-path/acceptance counters; these are unavailable, not zero. A population GA has no directly comparable single-current acceptance count. The unchanged reference was not rerun to invent missing history.', '',
        '| Primary pair (connectivity minus reference) | Mean delta (h) | Family-four 95% simultaneous interval | Connectivity wins / losses / ties |',
        '|---|---:|---:|---:|']
    for c in summary['primary_contrasts']:
        lines.append(f"| connectivity - {c['reference']} | {c['mean_delta_hr']:+.9f} | [{c['simultaneous_95'][0]:+.9f}, {c['simultaneous_95'][1]:+.9f}] | {c['wins']} / {c['losses']} / {c['ties']} |")
    ils_ga = next(c for c in summary['secondary_pairwise'] if c['candidate'] == 'ga_baseline' and c['reference'] == 'iterated_local')
    lines += ['', f"Secondary GA-minus-ILS mean={ils_ga['mean_delta_hr']:+.9f} h, family-ten interval=[{ils_ga['simultaneous_95'][0]:+.9f}, {ils_ga['simultaneous_95'][1]:+.9f}]. All ten secondary paired comparisons and pointwise bootstrap intervals are supplied in `BUDGET_100000_SUMMARY.json`. Intervals concern optimizer seeds under this reused training model; an interval crossing zero is not equivalence or external robustness.", '',
        '## Why this new repair still struggles', '']
    prior = leverage[0]
    lines.append(f"The all64 bank is not uniformly cross-state consensus: retained bundles have mean support {prior['mean_bundle_sample_support']:.3f}/64; the weighted sample15 share is {100*prior['weighted_sample15_share']:.3f}%, and top10 membership overlap without15 is {prior['top10_group_overlap_without15']}/10. Thus sample15 does not dominate this initial proposal bank, while many exact bundle combinations remain state-specific.")
    for row in prior['top20'][:3]:
        lines.append(f"- `{','.join(row['group'])}`: support={row['support']}/64, DS2+ first-wave fraction={row['ds2plus_first_wave_fraction']:.4f}, mean relaxed queue/travel-delay fraction={row['relaxed_queue_travel_delay_fraction_mean']:.6g}.")
    lines += ['', 'The highest weighted witnesses largely have irreducible sampled repair durations and already-favorable first-wave origins. Moving them earlier in the priority list cannot remove those durations. The relaxed independent-origin benchmark is not a feasible schedule or a certified bound, especially when a later directed inter-task leg can be shorter.', '',
        'Insertion repair still shifts intervening ranks even though its bundle is noncontiguous. Width-three pruning may also omit useful jointly harmful intermediate moves. Restarts generate many accepted improvements back toward the archived prior; accepted-current progress must not be confused with improving the global archive.', '',
        'Thirty percent local *macros* is not thirty percent local objective queries: a bundle macro tests many candidates. The measured local-macro counts give an upper bound on local distinct calls; the bulk of the budget is allocated to beam repair. This is a concrete efficiency limitation relative to100k ILS neighborhoods, not a proof that network information is useless.', '',
        '## Bounded rank-disruption probe', '',
        'Registered during confirmation after its first outcomes; adaptive diagnosis, not another confirmatory optimizer trial. Seeds1400..1423, fixed shared-prior/frozen-GA/refined-ILS parents, four targeting/repair combinations, matched attempted proposal effort and full mean64 fitness. No parent was updated. All288 macros retained.', '',
        '| Parent | Targeting | Repair | Improving /24 | Mean delta (h) | Mean changed first-wave origins |',
        '|---|---|---|---:|---:|---:|']
    for r in probe['summaries']:
        lines.append(f"| {r['parent']} | {r['targeting']} | {r['repair']} | {r['strict_improving_macros']} | {r['mean_delta_hr']:+.9f} | {r['mean_changed_firstwave_origins']:.3f} |")
    lines += ['', 'Joint swaps preserve other slots and improve the older prior in some probes; the tested probes do not improve the frozen GA or refined ILS. Different operator RNG streams and beams generate different candidate sets, so this is evidence of a repair/disruption mechanism, not an equal-search-space superiority claim. Zero loss changes can still have raw crew-label differences; operational origins/travel/predecessors are reported separately.', '',
        '## Independent candidate verification and influence', '',
        f"Every method's best confirmation permutation plus frozen GA/refined ILS passed all64 original pandas/NetworkX production evaluations ({candidate['production_sample_calls']} sample calls; maximum absolute compiled/production discrepancy {candidate['maximum_absolute_parity_error_hr']:.3g} h). Full identities and92-station permutations are in `CANDIDATE_PRODUCTION_AND_INFLUENCE_100000.json`; per-state values and event-exact self/threshold/source decomposition are in companion CSV/JSON files.", '',
        '| Best method candidate | Seed | Production J (h) | Delta vs frozen GA (h) | Improved / worsened states | Delta without15 (h) | Leave-one-out reversal count |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for m in METHODS:
        c = candidate['selected'][m]
        d = candidate['comparisons'][m]['frozen_ga']
        lines.append(f"| {m} | {c['seed']} | {c['expected_loss_hr']:.12f} | {d['mean_delta_hr']:+.9f} | {d['improved_states']} / {d['worsened_states']} | {d['without15_mean_delta_hr']:+.9f} | {len(d['loo_ranking_reversal_indices'])} |")
    ils = candidate['comparisons']['iterated_local']
    events = read('CANDIDATE_EVENT_COMPONENTS_100000.json')
    event15 = next(r for r in events if r['candidate'] == 'iterated_local' and r['sample'] == 15)
    changes = event15['component_changes_hr']
    lines += ['', f"The new ILS best (seed{candidate['selected']['iterated_local']['seed']}) remains {ils['refined_ils']['mean_delta_hr']:+.9f} h worse than the previously refined ILS. Against frozen GA it improves only{ils['frozen_ga']['improved_states']}/64 states and worsens{ils['frozen_ga']['worsened_states']}; its median change is {ils['frozen_ga']['median_delta_hr']:+.9f} h. Sample15 contributes {ils['frozen_ga']['sample15_delta_hr']:+.9f} h, and excluding15 reverses the mean to {ils['frozen_ga']['without15_mean_delta_hr']:+.9f} h. Six leave-one-out removals reverse its frozen-GA ranking. None of those removals is used in optimization.",
        f"Sample15's event-exact difference is self={changes['L_self']:+.9f}, threshold={changes['L_threshold']:+.9f}, source={changes['L_source']:+.9f}, total={changes['L_total']:+.9f} h. The benefit is source reconnection, overcoming worse self-restoration and threshold contributions. This is exact accounting for the whole schedule comparison, not proof that one station move caused it."]
    lines += ['', 'Differences against refined ILS, medians, empirical quantiles, all leave-one-out changes, largest beneficial/adverse states and leave1/2/4/8-most-beneficial-out diagnostics are retained. Outcome-selected sample removals are sensitivity diagnostics, not a revised objective. All64 samples still determine every optimized mean.', '',
        'Complete event trajectories compare candidate and frozen GA at sample15 and each candidate\'s strongest beneficial/adverse state. `L_total=L_self+L_threshold+L_source` is integrated on the union of native completion events over the original planning horizon. Affected station dependency mass and interval timing are descriptive, not station-level causal interventions.', '',
        '## Computation and identities', '',
        f"Confirmation: {execution['count']} runs, {execution['total_distinct_evaluations']:,} distinct search queries and {execution['total_attempts']:,} attempted calls. Elapsed parallel batch wall={execution['total_elapsed_wall_seconds']:.2f} s at{execution['workers']} workers; aggregate worker wall including setup={execution['total_worker_wall_seconds']:.2f} s. Worker timings are contention-dependent, not isolated serial speed benchmarks.",
        f"Completed smoke contributes10,000 search queries. Bounded probe contributes{probe['mean_objective_calls']:,} distinct/{probe['attempted_mean_calls']:,} attempted mean calls, plus{probe['compiled_sample_calls']:,} compiled single-state audit calls. Native-only reannotation adds{probe.get('native_reannotation_schedule_decodes', 0):,} decodes; final-phenotype audit adds{phenotype['native_decodes']:,} decodes and zero objective queries.",
        'Each successful worker loader also makes8 setup-parity mean calls outside its search budget and one final best-score verification;100 confirmation runs add800+100 such calls. Analysis loaders have the same8-call setup. Failed smoke initialization and cold compilation overhead were not fully instrumented and are explicitly additional, not counted as zero. Search-distinct means chromosome identity, not guaranteed unique scheduling behavior or globally distinct queries across methods.',
        'Per-run checkpoints, archive trajectories, attempted-call overhead, acceptance/restart counters, weighted bundle support and complete candidate hashes are retained. The final-phenotype audit ignores interchangeable same-origin crew labels but preserves per-station origin, predecessor, travel, arrival and completion. It concerns final candidates, not an unobserved whole-search neutral fraction.', '',
        '## Validation readiness, without generating states', '',
        f"Original freeze hashes pass. Addendum retains the original nine ordered policies and addsCentrality-first, Closeness-first and fixed refined ILS as secondary diagnostic:12 ordered+unconstrained=13 conditions. Original primary frozenGA-minus-Impact remains unchanged. The original protocol and formal strategies are not overwritten. Physical sampling function/source hashes, RNG namespace and bootstrap plan are recorded in `VALIDATION_COMPARATORS_ADDENDUM.json`.",
        f"Projected archive={readiness['engineering']['estimated_archive_bytes']/2**30:.3f} GiB; reserve={readiness['engineering']['reserved_storage_bytes']/2**30:.3f} GiB; checked free disk={readiness['engineering']['disk_free_bytes']/2**30:.2f} GiB. These are scaled engineering estimates, not measured new-archive sizes. Physical DS/duration arrays alone require{readiness['engineering']['core_physical_arrays_bytes']:,} bytes; trajectories and metrics dominate storage.",
        'No sampling functions were called. Keep SeedSequence([202610091,3,2,r]), shared physical states, overlap-abort against64 planning and1000 previously inspected states, fixed comparator hashes,20k whole-state paired bootstrap, no optional stopping/reselection, and explicit author approval. Validation0-480 h is distinct from H_plan. This addendum must itself be frozen and all fragility/PGA/config hashes rechecked immediately before an authorized executor.', '',
        '## Remaining research decision', '',
        f"Prespecified500k trigger passed: **{summary['large_budget_gate_passed']}**, triggering methods: `{summary['gate_trigger_methods']}`. No unchanged underperforming LNS batch was extended just to repeat its plateau. This is a gate decision, not a claim that current GA parameters are optimal.",
        'The executed evidence narrows the unresolved mechanism to removable scheduling leverage and rank-preserving repair, rather than generic source importance or merely sampling more optimizer seeds. Slot swaps help an older prior but currently give no evidence of beating the fixed high-quality comparators. GA versus ILS must be judged using the actual paired uncertainty and computation, not the failure of this LNS or one weak baseline. Generalization remains untested on untouched states; no new scientific policy is promoted.', '',
        f"Preservation passes for{len(preservation['files_sha256'])} protected revision files plus exact revision HEAD/branch and staged binary-diff hash. The isolated checkout hydrated only8 verified LFS inputs. Their payload SHA-256 equals the original pointer OIDs; this is hydration, not a model modification. No source gate, scheduler, kernel, physical file or manuscript figure changed in the diagnostic commits.", '',
        '## Reproduction', '', '```powershell', "$env:PYTHONPATH='src'", "$env:OPENBLAS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'", "$env:NUMBA_NUM_THREADS='1'", "$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'lns2-20261010-numba'",
        'python -m unittest discover -s tests -p test_connectivity_lns_20261010.py -v',
        'python -m la_grid.diagnostics.ga_connectivity_lns_local_20261010 --phase smoke --workers 2',
        'python -m la_grid.diagnostics.ga_connectivity_lns_local_20261010 --phase confirmation --workers 12',
        'python -m la_grid.diagnostics.ga_connectivity_lns_audit_20261010 --task mechanism',
        'python -m la_grid.diagnostics.ga_connectivity_lns_audit_20261010 --task cutsets',
        'python -m la_grid.diagnostics.ga_connectivity_lns_audit_20261010 --task readiness',
        'python -m la_grid.diagnostics.ga_connectivity_lns_failure_probe_20261010',
        'python -m la_grid.diagnostics.ga_connectivity_lns_candidate_20261010 --budget 100000',
        'python -m la_grid.diagnostics.ga_connectivity_lns_report_20261010 --task reannotate',
        'python -m la_grid.diagnostics.ga_connectivity_lns_report_20261010 --task phenotypes',
        'python -m la_grid.diagnostics.ga_connectivity_lns_report_20261010 --task report', '```', '',
        'The optimizer command verifies and reuses completed per-case records. It does not resample physics. Frozen input hydration requires the checked original LFS objects; setup command and run IDs are recorded in the setup module. Publication uses only this research prefix, new diagnostic modules/tests and the dedicated review index.', '']
    long_path(OUT / 'LOCAL_RESEARCH_REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    review = REPO_ROOT / 'docs/reviewer/OPTIMIZATION_NONCONTIGUOUS_LNS_20261010.md'
    long_path(review).parent.mkdir(parents=True, exist_ok=True)
    long_path(review).write_text('# Local noncontiguous connectivity LNS review\n\n'
        'Completed local20-seed, five-method100k comparison and archived160-run audit. '
        'Negative connectivity-LNS evidence retained; original physics, formal policies and manuscript artwork unchanged.\n\n'
        '[Full report](../../results/diagnostics/ga_noncontiguous_connectivity_lns_20261010/LOCAL_RESEARCH_REPORT.md)\n\n'
        '[Seed-level statistics](../../results/diagnostics/ga_noncontiguous_connectivity_lns_20261010/SEED_LEVEL_100000.csv)\n\n'
        '[Candidate parity and influence](../../results/diagnostics/ga_noncontiguous_connectivity_lns_20261010/CANDIDATE_PRODUCTION_AND_INFLUENCE_100000.json)\n\n'
        '[Validation readiness only](../../results/diagnostics/ga_noncontiguous_connectivity_lns_20261010/VALIDATION_COMPARATORS_ADDENDUM.json)\n', encoding='utf-8')
    files = {str(p.relative_to(long_path(OUT))): hashlib.sha256(p.read_bytes()).hexdigest() for p in long_path(OUT).rglob('*') if p.is_file()
        and p.name != 'EVIDENCE_FILE_HASHES.json'}
    save(OUT / 'EVIDENCE_FILE_HASHES.json', dict(generated_at=datetime.now(timezone.utc).isoformat(),
        files_sha256=files, self_excluded=True, python=sys.version, numpy=np.__version__, platform=platform.platform(),
        logical_cpus=psutil.cpu_count(), memory_total_bytes=psutil.virtual_memory().total,
        confirmation_algorithm_commit='6de7efa', failure_probe_design_commit='e69d0c9',
        current_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO_ROOT, text=True).strip()))
    print('LOCAL_REPORT_COMPLETE', len(files), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--task', choices=('report', 'reannotate', 'phenotypes'), required=True)
    a = p.parse_args()
    if a.task == 'reannotate':
        reannotate_probe()
    elif a.task == 'phenotypes':
        phenotypes()
    else:
        report()


if __name__ == '__main__':
    main()
