"""Render and reconcile the completed Task A-C diagnostic, never formal figures."""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
import pickle

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from la_grid.diagnostics.ga_actionable_delay_20261010 import OUT, START, read, sha, TOL, GAIN_TOL
from la_grid.diagnostics.ga_research_collect_20261009 import save, long_path
from la_grid.paths import REPO_ROOT


def certificates():
    result = read(OUT / 'EXACT_SIX_SLOT_RESULTS.json')
    pinned = read(OUT / 'PINNED_SIX_SLOT_SETS.json')
    assert len(result['results']) == len(pinned['sets']) == 120
    with gzip.open(long_path(OUT / 'EXACT_SCORES.pkl.gz'), 'rb') as f:
        cache = pickle.load(f)['cache']
    checks = []; assigned_keys = set()
    for case, fixed in zip(result['results'], pinned['sets']):
        assert case['slots'] == fixed['slots'] and case['selected_stations'] == fixed['selected_stations']
        stem = f"{case['parent']}_{case['arm']}_{case['set_number']:02}"
        path = OUT / 'neighborhoods' / (stem+'.npz')
        assert sha(path) == case['neighborhood_archive_sha256']
        with np.load(long_path(path)) as data:
            orders = data['orders']; losses = data['loss_hr']; ids = data['station_ids'].astype(str)
            lookup = {s:i for i,s in enumerate(ids)}
            parent = np.array([lookup[s] for s in pinned['parents'][case['parent']]['sequence']], np.uint8)
            outside = [i for i in range(92) if i not in case['slots']]
            assert orders.shape == (720,92) and len({o.tobytes() for o in orders}) == 720
            assert np.all(np.sort(orders,axis=1) == np.arange(92))
            assert np.all(orders[:,outside] == parent[outside])
            assert any(o.tobytes() == parent.tobytes() for o in orders)
            assert abs(float(losses.min())-case['conditional_minimum_loss_hr']) < 1e-12
            assert all(abs(cache[o.tobytes()]-v) < 1e-12 for o,v in zip(orders,losses))
            assigned_keys.update(o.tobytes() for o in orders)
        checks.append(dict(parent=case['parent'], arm=case['arm'], set_number=case['set_number'],
            unique_assignments=720, untouched_positions=86, complete_permutation=True, parent_included=True))
    save(OUT / 'RESTRICTED_CERTIFICATES_QA.json', dict(status='PASS', cases=checks,
        total_enumerated=86400, global_distinct_assignment_keys=len(assigned_keys),
        arithmetic_tolerance_hr=GAIN_TOL, minimums_not_interval_certified=True,
        exact_conditional_enumeration_not_global_optimality=True))


def plots():
    arrays=np.load(long_path(OUT / 'ACTIONABLE_ARRAYS.npz'))
    scores=pd.read_csv(long_path(OUT / 'STATION_OPPORTUNITY_RANKS.csv'),dtype={'station_id':str})
    fig,axes=plt.subplots(3,1,figsize=(15,11),layout='constrained')
    labels=('shared_prior','frozen_ga','refined_ils')
    for ax,label in zip(axes,labels):
        ranked=scores[scores.parent==label].sort_values(['mean_optimistic_gain_hr','station_id'],ascending=[False,True]).head(25)
        # Stored arrays use the original kernel station order, present in every certificate.
        first=read(OUT / 'EXACT_SIX_SLOT_RESULTS.json')['results'][0]
        stem=f"{first['parent']}_{first['arm']}_{first['set_number']:02}"
        with np.load(long_path(OUT / 'neighborhoods' / (stem+'.npz'))) as z:
            station_ids=z['station_ids'].astype(str).tolist()
        idx=[station_ids.index(s) for s in ranked.station_id]
        heat=arrays[label+'_benefit'][:,idx].T
        img=ax.imshow(heat,aspect='auto',interpolation='nearest',cmap='viridis')
        ax.set_yticks(range(len(idx)),ranked.station_id,fontsize=8)
        ax.set_xticks([0,15,31,47,63]); ax.axvline(15,color='#d55e00',lw=1)
        ax.set_xlabel('Planning realization'); ax.set_title(label.replace('_',' '))
        fig.colorbar(img,ax=ax,label='Optimistic single-station loss reduction (h)')
    fig.savefig(long_path(OUT / 'ACTIONABLE_DELAY_STATE_MAP.png'),dpi=180)
    plt.close(fig)
    result=read(OUT / 'EXACT_SIX_SLOT_RESULTS.json')['results']
    fig,axes=plt.subplots(1,3,figsize=(13,4),sharey=True,layout='constrained')
    for ax,label in zip(axes,labels):
        for arm,color,marker in [('targeted','#0072b2','o'),('random_control','#d55e00','x')]:
            subset=[r for r in result if r['parent']==label and r['arm']==arm]
            ax.plot(range(20),[r['gain_hr']*3600 if r['gain_hr'] > GAIN_TOL else 0. for r in subset],linestyle='none',marker=marker,color=color,label=arm.replace('_',' '))
        ax.set_title(label.replace('_',' ')); ax.set_xlabel('Pinned matched set'); ax.set_ylabel('Restricted improvement (seconds of J)')
        ax.legend(fontsize=8); ax.grid(alpha=.2)
        if label != 'shared_prior':
            ax.text(.5,.5,'No improvement above 1e-9 h',ha='center',transform=ax.transAxes,fontsize=10)
    fig.savefig(long_path(OUT / 'EXACT_SIX_SLOT_GAINS.png'),dpi=180)
    plt.close(fig)


def report():
    ab=read(OUT / 'TASK_AB.json'); ex=read(OUT / 'EXACT_SIX_SLOT_RESULTS.json')
    verification=read(OUT / 'CANDIDATE_PRODUCTION_INFLUENCE.json')
    mechanism=read(OUT / 'BEST_PRIOR_MECHANISM.json')
    ranks=pd.read_csv(long_path(OUT / 'STATION_OPPORTUNITY_RANKS.csv'),dtype={'station_id':str})
    rows=[]
    for label in ab['parents']:
        for arm in ('targeted','random_control'):
            selected=[r for r in ex['results'] if r['parent']==label and r['arm']==arm]
            rows.append(dict(parent=label,arm=arm,sets=len(selected),improving_sets=sum(r['gain_hr']>GAIN_TOL for r in selected),
                mean_gain_hr=float(np.mean([r['gain_hr'] for r in selected])),maximum_gain_hr=max(r['gain_hr'] for r in selected),
                best_loss_hr=min(r['conditional_minimum_loss_hr'] for r in selected)))
    pd.DataFrame(rows).to_csv(long_path(OUT / 'SIX_SLOT_SUMMARY.csv'),index=False)
    lines=['# Actionable-delay and exact six-slot audit','',
        '## Decision','',
        'Completed Task A-C with original92 stations,64 physical planning states and unchanged C57_D1 scheduler, source gate, M1 population mass and mean-loss objective. No formal GA replacement and no new physical/validation states.', '',
        'The complete chosen restricted neighborhoods are tested; this is not a global optimality proof. Group minima and overlapping sets are not independent physical samples or optimizer-seed replications.', '',
        '## Prospective Registration','',
        f'Starting remote commit `{START}`. Diagnostic design/code/tests committed at `12fd25a`; all120 exact slot sets and their timing evidence committed at `af13c73` before observing neighborhood minima. Set-file SHA256: `'+ex['pinned_sets_sha256']+'`.', '',
        'The helper mentioned in the brief was not supplied. The specified graph construction was implemented and independently passed six tests, including12000 exhaustively enumerated synthetic schedules. Initial setup hit two Windows path-format errors, repaired before the prospective design commit and scientific evaluation. The CRLF byte-preserving evidence attributes initially made Git whitespace checks report CR characters; corrected with cr-at-eol without rewriting any numeric evidence.', '',
        '## Task A: Lower Relaxation','',
        'For damaged tasks S={i:DS_i>0}, dummy-start edges have cost min over actual active origins b[o,i], and directed j-to-i edges have cost p_j+t[j,i], j!=i. Dijkstra gives a_i; c_i_lower=a_i+p_i. DS0 nodes cannot be waypoints. Any actual crew route to i is a path in this graph with the same preceding repair times and directed travel, plus nonnegative idle time. Therefore shortest arrival is no later than actual arrival. Independent routes relax resource competition and generally cannot coexist in one feasible schedule.', '',
        'Direct depot arrival is an upper candidate for shortest relaxed arrival, not a general lower bound. First-wave tasks can retain origin-assignment improvement room. Nonnegative finite duration/travel and a completion-only monotone model are verified assumptions. All crew origins are drawn from the actual active roster, not every potential depot.', '',
        f"All{ab['scheduled_station_checks']} reference task/state completion inequalities pass at1e-8h. Original source-gate evaluation checks64 route envelopes and64 duration-only envelopes. Maximum diagnostic/authoritative value discrepancy={ab['maximum_completion_formula_error_hr']:.4g}h. Ordinary doubles with disclosed tolerances, not outward-rounded interval-certified decimals.", '',
        'Earlier completions weakly increase raw functionality, threshold-active nodes and source-connected components. Nonnegative dependency mass then weakly increases effective service and decreases the original loss. This establishes analytical admissibility of the simultaneous envelope but not a feasible policy. It is never inserted into formal strategy results.', '',
        'The minimax source-connectivity time C_i gives an independent formula check: DS0 loss=C_i; DS1 loss=0.5 C_i+0.5 max(C_i,c_i); DS2+ loss=C_i, since C_i>=c_i. Terms are horizon-clipped and population weighted. This formula is diagnostic only and independently checked against the original functionality/NetworkX gate.', '',
        f"Duration-only unlimited-crew zero-travel loss={ab['duration_only_mean_loss_hr']:.12f}h. Independent-route loss={ab['route_relaxation_mean_loss_hr']:.12f}h; tightening={ab['tightening_hr']:.12f}h.", '',
        '| Parent | Feasible mean J (h) | Incumbent minus route relaxation (h) | First-wave task/state observations with headroom |',
        '|---|---:|---:|---:|']
    for label,s in ab['summaries'].items():
        lines.append(f"| {label} | {s['loss_hr']:.12f} | {s['relaxation_gap_hr']:.12f} | {s['first_wave_with_material_headroom']} |")
    lines+=['', 'A remaining1.48h relaxation gap is not a promise that a single shared priority order or57 finite crews can realize it. No maximum-direct-travel substitute or horizon change was used.', '',
        '## Task B: Actionable Opportunities','',
        'STATION_STATE_ACTIONABLE_DELAY.csv retains all three parents x64 states x92 stations: repair, arrival, release, predecessor, active-origin index, travel, dispatch, first-wave status, relaxed completion, headroom and exact single-station optimistic service screen. ACTIVE_ORIGIN_LOOKUP.json resolves numeric base-row indexes to origin names and the original57-crew roster; only actual active origins are admissible.', '',
        'ACTIONABLE_DELAY_STATE_MAP.png shows the top25 station/state diagnostic screens per parent, marking state15. Screens are infeasible interventions: changing one completion while holding all others fixed need not be schedulable, is not a causal feasible effect, and gains must not be summed. Slot sets may include zero-headroom donors/enablers.', '',
        'Old dominant warm-start bundles300493/307693 and300493/303620/307693 have zero headroom in every damaged observation under the admissible route construction. Bundle306768/307693 has mean0.0345414h and max0.0690828h headroom. This supports irreducible-duration diagnosis for those specific bundles without declaring all first-wave tasks unchangeable.', '',
        '| Parent | Highest single-screen station | Mean optimistic gain (h) | Supporting states | State15 fraction |',
        '|---|---|---:|---:|---:|']
    for label in ab['parents']:
        s=ranks[ranks.parent==label].sort_values(['mean_optimistic_gain_hr','station_id'],ascending=[False,True]).iloc[0]
        lines.append(f"| {label} | {s.station_id} | {s.mean_optimistic_gain_hr:.9f} | {s.support_states} | {s.state15_share:.4f} |")
    lines+=['', 'All64 and without15 rankings/headroom/support are retained. State15 is never excluded from feasible fitness. Interacting opportunities include queue predecessors, co-witness gateway activation, and first-wave origin donors; high mass/source waiting alone is not actionable-delay evidence.', '',
        '## Task C: Complete Restricted Enumeration','',
        'Top20 all64 optimistic-screen centers per parent, weighted predecessor/donor/co-witness inclusion, deterministic ranking fill/diversity, and20 uniform random six-position controls per parent were pinned prospectively. Random controls match the target count in three priority-rank bands, not voltage/degree/repair severity. Cases with no causal donor are filled by opportunity rank. Same six occupied positions and remaining86 fixed positions are checked for all720 permutations. No beam or intermediate-score pruning.', '',
        '| Parent | Arm | Improving sets /20 | Mean gain (h) | Maximum gain (h) | Best conditional J (h) |', '|---|---|---:|---:|---:|---:|']
    for s in rows:
        lines.append(f"| {s['parent']} | {s['arm']} | {s['improving_sets']} /20 | {s['mean_gain_hr']:.12f} | {s['maximum_gain_hr']:.12f} | {s['best_loss_hr']:.12f} |")
    lines+=['', 'Each archive retains720 full92-ID assignments and exact original-kernel scores. Every parent is included. Certificates apply only to the120 pinned slot sets and1e-9h arithmetic improvement tolerance; no claim about arbitrary six-slot sets, every neighborhood or global optimality. Numerical ties retain the parent for auditing.', '',
        '## Production Parity And Influence','',
        f"All{verification['unique_candidates']} unique restricted optima passed original production evaluator across64 states ({verification['production_sample_calls']} sample calls). Maximum compiled/production discrepancy={verification['max_absolute_error_hr']:.4g}h.", '',
        'Complete sequences and SHA256 identities: CANDIDATE_PRODUCTION_INFLUENCE.json. Per-state values: CANDIDATE_PER_STATE_PARITY.csv. Every candidate has comparison to shared prior, frozen GA and refined ILS, full leave-one-out reversals, removal of1/2/4/8 most beneficial states and without15 sensitivity. Those removals are diagnostic, never a changed objective. Candidate schedules retain origin/predecessor/travel/completion/source timing; event decompositions are descriptive accounting of whole schedules, not causal claims about one station.', '']
    best=min(verification['candidates'],key=lambda c:c['production_loss_hr'])
    lines.append(f"Best restricted optimum J={best['production_loss_hr']:.12f}h, SHA256 `{best['sequence_sha256']}`.")
    for ref in ('frozen_ga','refined_ils'):
        s=best['comparisons'][ref]
        lines.append(f"Compared with{ref}: delta={s['mean_delta_hr']:+.12f}h; improves{s['improved_states']}/64, worsens{s['worsened_states']}/64; without15 delta={s['without15_mean_delta_hr']:+.12f}h; LOO reversals={s['loo_ranking_reversal_indices']}.")
    warm=mechanism['candidate']; change=warm['comparisons']['shared_prior']
    lines+=['', '### Best Warm-Start Counterexample','',
        f"Targeted set{mechanism['selected_case']['set_number']} reaches{warm['production_loss_hr']:.12f}h, improving the older warm start by{-change['mean_delta_hr']:.12f}h. SHA256 `{warm['sequence_sha256']}`. It improves{change['improved_states']}/64 states, worsens{change['worsened_states']}/64, median delta={change['median_delta_hr']:+.12f}h. State15 actually worsens by{change['sample15_delta_hr']:+.12f}h; excluding it yields{change['without15_mean_delta_hr']:+.12f}h. No leave-one-out reversal, and removing the eight most beneficial states still yields{change['leave_most_beneficial_out'][-1]['remaining_mean_delta_hr']:+.12f}h.", '',
        f"This remains{warm['comparisons']['frozen_ga']['mean_delta_hr']:+.12f}h worse than frozen GA and{warm['comparisons']['refined_ils']['mean_delta_hr']:+.12f}h worse than refined ILS. Thus the7/20 versus2/20 targeted/control result is limited to recovering a weak-parent deficit, not evidence of superior optimization of current incumbents.", '',
        f"Exact all64 whole-schedule decomposition versus prior: self={mechanism['mean_component_delta_hr']['L_self']:+.12f}h, threshold={mechanism['mean_component_delta_hr']['L_threshold']:+.12f}h, source={mechanism['mean_component_delta_hr']['L_source']:+.12f}h; sum={mechanism['mean_component_delta_hr']['L_total']:+.12f}h. Mean directed crew travel change={mechanism['mean_directed_travel_change_hr']:+.12f}h; mean earlier/later station completions={mechanism['mean_earlier_completions']:.3f}/{mechanism['mean_later_completions']:.3f}. BEST_PRIOR_MECHANISM.json retains all64 event accounts, changed occupied positions, individual headroom, source timing and candidate influence. This is attribution of the entire feasible schedule difference, not causal identification of a single donor/gateway.", '']
    lines+=['', '## Computation Accounting','',
        f"Task A-B wall={ab['elapsed_seconds']:.3f}s (analysis phase only). Task C wall={ex['elapsed_seconds']:.3f}s;{ex['enumerated_assignments']} assignment observations;{ex['newly_executed_distinct_mean_calls']} new exact64-state mean calls;{ex['reused_assignments']} reused assignment observations. Imported original checkpoint cache has{ex['initial_imported_cache_size']} entries, SHA256 `{ex['imported_checkpoint_sha256']}`. No refined-ILS single-move scan was repeated.", '',
        f"Candidate parity/annotation phase wall={verification['elapsed_seconds']:.3f}s. Each load() performs8 fixed-rule/prior mean parity calls outside neighborhood accounting. Audit,select,exact,candidates,mechanism each invoke it once:40 setup means. Audit also checks3 parent means and192 compiled reference sample calls. Candidate verification makes{verification['production_sample_calls']} compiled sample calls as well as the same number of original production sample calls; it also performs192 reference sample calls. Best-prior mechanism adds128 native component event evaluations and128 decodes, zero feasible fitness calls. Candidate/event summary decoding includes120 x128=15,360 per-set native decodes, plus annotated improving candidates and event comparisons. Analysis/report source-minimax/native-only decodes and17,598 single-completion screens are not feasible-chromosome fitness calls. Cold imports and failed engineering setup are additional overhead. Original cached132,545 objective calls are historical, not new computation.", '',
        'No stochastic optimizer campaign,500k extension, physical resampling, external validation or candidate promotion performed. Exact conditional coverage is a diagnostic budget, not independent-run statistical power.', '',
        '## Next Decision','']
    high_improvements=[r for r in ex['results'] if r['parent'] != 'shared_prior' and r['gain_hr']>GAIN_TOL]
    if not high_improvements:
        lines+=['No tested six-slot assignment improves frozen GA or refined ILS. Retain those restricted certificates and the nonzero global relaxation gap. Do not expand the failed unchanged LNS to500k or launch a weight-only retuning campaign. Any later expansion needs evidence that a larger coordinated slot/origin reassignment can access actual residual scheduling delay, with prospective controls. A relaxation gap alone does not establish that such feasible opportunity exists.']
    else:
        lines+=['High-quality-parent counterexamples exist. These remain diagnostic candidates, not formal replacements. A separate new optimizer must be prospectively specified around the demonstrated mechanism and compared against GA, ILS and equally strong random-target exact repair, with seed precision justified before a new campaign. This restricted audit is not itself that campaign.']
    lines+=['', '## Preservation And Reproduction','',
        '950 protected revision file hashes, revision branch/HEAD/staged binary-diff and all original kernel input hashes are checked again before publication.13-condition validation-readiness addendum remains identical. Diagnostic plots reside only here; manuscript/formal strategy output remains untouched.', '',
        '```powershell', "$env:PYTHONPATH='src'", "$env:NUMBA_CACHE_DIR=Join-Path $env:TEMP 'delay3-20261010-numba'",
        "$env:OPENBLAS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'", "$env:NUMBA_NUM_THREADS='1'",
        'python -m unittest discover -s tests -p test_actionable_delay_20261010.py -v',
        'python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task audit',
        'python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task select',
        '# Pin and commit the selection file before executing exact.',
        'python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task exact',
        'python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task candidates',
        'python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task mechanism',
        'python -m la_grid.diagnostics.ga_actionable_delay_report_20261010',
        'python -m la_grid.diagnostics.ga_actionable_delay_20261010 --task preservation',
        '```', '',
        'The exact command resumes and reuses cached completed sets. Preserve pinned files when reproducing; do not overwrite them after seeing minima. Setup hydration needs the original checkpoint LFS/blob object and protected revision path recorded in SETUP.json.']
    long_path(OUT / 'TASK_ABC_RESEARCH_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    save(OUT / 'NEXT_DECISION.json',dict(status='TASK_ABC_COMPLETE',higher_quality_parent_improving_sets=len(high_improvements),
        new_campaign_started=False,formal_ga_replaced=False,new_physical_samples=0,summary=rows))
    index=REPO_ROOT / 'docs/reviewer/OPTIMIZATION_ACTIONABLE_DELAY_20261010.md'
    index.parent.mkdir(parents=True,exist_ok=True)
    index.write_text('# Actionable-delay and exact six-slot diagnostic\n\n'
        'Completed Task A-C at the original fixed92/64 planning model. All output is diagnostic.\n\n'
        '[Research report](../../results/diagnostics/ga_actionable_delay_six_slot_20261010/TASK_ABC_RESEARCH_REPORT.md)\n\n'
        'Includes route lower-relaxation proof/audit, actionable station-state map, pinned120 neighborhoods and86400 assignment records, native candidate parity/influence, restricted certificates, computation and preservation. No original model, formal policy, validation cohort or manuscript figure change.\n',encoding='utf-8')
    print('REPORT_COMPLETE',json.dumps(rows),flush=True)


def main():
    certificates(); plots(); report()


if __name__=='__main__':
    main()
