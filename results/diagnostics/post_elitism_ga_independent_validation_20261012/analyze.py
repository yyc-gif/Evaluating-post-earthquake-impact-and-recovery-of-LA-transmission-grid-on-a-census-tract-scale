"""Frozen paired analysis, native trajectory verification, and evidence archive."""
from __future__ import annotations

import argparse
import hashlib
import math
import time
import zipfile
import study as s
import numpy as np
import pandas as pd

v, q, a, OUT = s.v, s.q, s.a, s.OUT
COMP = ['L_self_population_mass_weighted_hr', 'L_threshold_population_mass_weighted_hr',
        'L_source_population_mass_weighted_hr']
EXTRA = ['mean_damaged_station_completion_hr', 'source_disconnected_dependency_integral_hr',
         'source_dependency_T80_restricted_hr']


def md(name, text):
    (OUT / name).write_text(text.strip() + '\n', encoding='utf-8', newline='\n')


def lorenz_gini(x, p):
    keep = p > 0
    x, p = np.asarray(x)[keep], np.asarray(p)[keep]
    order = np.argsort(x, kind='stable')
    x, p = x[order], p[order]
    if np.dot(x,p) == 0: return 0.
    cw, cx = np.r_[0.,np.cumsum(p)/p.sum()], np.r_[0.,np.cumsum(p*x)/np.dot(p,x)]
    return 1-float(np.sum(np.diff(cw)*(cx[1:]+cx[:-1])))


def analyze():
    s.configure()
    freeze = s.verify()
    assert v.read(OUT / 'COHORT_COMPLETED.json')['policy_records'] == 6000
    tick = time.perf_counter()
    model = v.load_model()
    mapping, ids = model['mapping'], model['ids']
    pop, w = mapping.population, mapping.weight
    mass = w.T @ pop
    qmass = np.array([w.T @ (pop*(mapping.quartile==c)) for c in ('Q1','Q4')])
    assert np.allclose(w.sum(axis=1),1,rtol=0,atol=1e-12)
    source_flag = np.array([x in model['ctx']['sources'] for x in ids])
    policy_names = [p['strategy'] for p in freeze['strategies']]
    curve = {p:np.zeros((481,5)) for p in policy_names}
    prior = set(v.read(OUT / 'PREVIOUS_PHYSICAL_HASH_REGISTRY.json').values())
    frozen_cohort = v.read(OUT / 'COHORT_FROZEN.json')
    physical_hashes, frames, draws, reconnect, timing = set(), [], [], [], []
    errors = dict(compiled_production_hr=0., event_integral_hr=0., component_hr=0.,
                  tract_integral_hr=0., gini=0., hospital_hr=0., quartile_hr=0., scheduler_hr=0.)
    for r in range(2000):
        folder = q.ARCHIVE / 'cases' / f'{r:04d}'
        dp = q.ARCHIVE / 'physical' / f'{r:04d}' / 'DRAW.json'
        physical = v.read(dp)
        assert v.sha(dp) == frozen_cohort['draw_receipts_sha256'][str(r)]
        payload = dict(physical); expected_payload = payload.pop('payload_sha256')
        assert hashlib.sha256(s.json.dumps(payload,sort_keys=True).encode()).hexdigest() == expected_payload
        assert physical['entropy'] == [s.SAMPLE_SEED,r] and physical['namespace'] == freeze['sampling_namespace']
        assert physical['station_ids'] == ids and physical['freeze_sha256'] == v.sha(OUT/'EXECUTION_FREEZE.json')
        ds, duration = np.array(physical['damage_state'],np.int64), np.array(physical['duration_hr'],float)
        h = v.physical_hash(ids,ds,duration)
        assert h == physical['physical_sha256'] and h not in prior and h not in physical_hashes
        physical_hashes.add(h)
        assert hashlib.sha256(ds.astype('<i8').tobytes()).hexdigest() == physical['damage_sha256']
        assert hashlib.sha256(duration.astype('<f8').tobytes()).hexdigest() == physical['duration_sha256']
        done = v.read(folder/'COMPLETE.json')
        assert done['identity']['physical_sha256'] == h and done['policy_count'] == 3
        assert done['identity']['freeze_sha256'] == v.sha(OUT/'EXECUTION_FREEZE.json')
        for n, digest in done['files_sha256'].items(): assert v.sha(folder/n) == digest
        frame = pd.read_csv(folder/'SUMMARY.csv',float_precision='round_trip')
        task = pd.read_csv(folder/'TASK_EXECUTION.csv',dtype={'task_id':str,'previous_task_id':str},float_precision='round_trip')
        assert len(frame)==3 and frame.strategy.tolist()==policy_names and frame.physical_sha256.eq(h).all()
        frame['r'] = r
        errors['compiled_production_hr'] = max(errors['compiled_production_hr'],float(frame.independent_kernel_abs_error_hr.max()))
        with np.load(folder/'TRAJECTORIES.npz',allow_pickle=False) as z:
            assert z['station_ids'].astype(str).tolist()==ids and z['tract_ids'].astype(str).tolist()==mapping.tract_ids.tolist()
            assert z['policies'].tolist()==policy_names and len(z['event_lengths'])==3
            start=0
            for j,name in enumerate(policy_names):
                length=int(z['event_lengths'][j]); sl=slice(start,start+length)
                clock=z['event_time_hr'][sl]; dt=np.diff(clock)
                assert clock[0]==0 and clock[-1]==480 and (dt>0).all()
                e,F,C,f=(z[k][sl] for k in ('e','F','C','f'))
                assert np.isfinite(e).all() and (e>=0).all() and (e<=1).all()
                assert np.array_equal(F,f>=.5) and np.allclose(e,f*F*C,rtol=0,atol=1e-12)
                loss=np.array([dt @ z[k][sl][:-1] for k in ('L_self','L_threshold','L_source','L_total')])
                total, component = float(dt @ (1-e[:-1]@mass/mass.sum())), loss @ mass/mass.sum()
                row=frame.index[frame.strategy.eq(name)][0]
                errors['event_integral_hr']=max(errors['event_integral_hr'],abs(total-float(frame.loc[row,v.PRIMARY])))
                errors['component_hr']=max(errors['component_hr'],float(np.max(abs(component[:3]-frame.loc[row,COMP].to_numpy(float)))),
                                           abs(component[:3].sum()-total))
                np.testing.assert_allclose(loss,z['station_component_integrals_hr'][j],rtol=0,atol=1e-9)
                np.testing.assert_allclose(z['L_total'][sl],z['L_self'][sl]+z['L_threshold'][sl]+z['L_source'][sl],rtol=0,atol=1e-12)
                tract=w @ loss[3]
                errors['tract_integral_hr']=max(errors['tract_integral_hr'],float(np.max(abs(tract-z['tract_normalized_loss_hr'][j]))))
                errors['gini']=max(errors['gini'],abs(lorenz_gini(tract,pop)-frame.loc[row,'burden_gini']))
                errors['hospital_hr']=max(errors['hospital_hr'],abs(float(tract[mapping.hospital].mean())-frame.loc[row,'hospital_mean_normalized_burden_hr']))
                for label in ('Q1','Q2','Q3','Q4'):
                    keep=mapping.quartile==label
                    value=float(np.dot(tract[keep],pop[keep])/pop[keep].sum())
                    errors['quartile_hr']=max(errors['quartile_hr'],abs(value-frame.loc[row,'burden_'+label+'_hr']))
                avail=e@mass/mass.sum(); conn=C@mass/mass.sum()
                hit=np.flatnonzero(avail>=.8)
                assert frame.loc[row,'T80_censored']==int(not len(hit))
                assert frame.loc[row,'T80_restricted_hr']==(clock[hit[0]] if len(hit) else 480)
                ix=np.searchsorted(clock,np.arange(481.),side='right')-1
                curve[name][:,0]+=avail[ix]
                curve[name][:,1:3]+=e[ix]@qmass.T/qmass.sum(axis=1)
                curve[name][:,3]+=conn[ix]
                curve[name][:,4]+=(F[ix][:,source_flag]).sum(axis=1)
                ce=np.flatnonzero(conn>=.8)
                frame.loc[row,'source_dependency_T80_restricted_hr']=clock[ce[0]] if len(ce) else 480.
                frame.loc[row,'source_dependency_T80_censored']=int(not len(ce))
                frame.loc[row,'source_disconnected_dependency_integral_hr']=float(dt@(1-conn[:-1]))
                frame.loc[row,'source_dependency_mass_at0']=conn[0]
                frame.loc[row,'source_dependency_mass_at480']=conn[-1]
                events=task[task.strategy.eq(name)].copy()
                assert events.task_id.nunique()==len(events)==int((ds>0).sum())
                np.testing.assert_allclose(events.realized_duration_hr,[duration[ids.index(x)] for x in events.task_id],atol=0,rtol=0)
                decoded=model['decoder'].decode(order=model['decoder'].order(freeze['strategies'][j]['sequence']),
                    damage=ds,duration=duration,origins=model['origins'])
                for event in events.itertuples():
                    i=ids.index(event.task_id)
                    errors['scheduler_hr']=max(errors['scheduler_hr'],abs(event.completion_hr-decoded[0][i]),
                        abs(event.arrival_hr-decoded[1][i]),abs(event.travel_hr-decoded[2][i]))
                    assert event.crew_index==decoded[3][i] and event.dispatch_rank==decoded[5][i]+1
                    previous=ids[decoded[4][i]] if decoded[4][i]>=0 else None
                    assert (pd.isna(event.previous_task_id) and previous is None) or event.previous_task_id==previous
                assert (events.completion_hr>480).sum()==frame.loc[row,'tasks_completed_after_480']
                frame.loc[row,'mean_damaged_station_completion_hr']=events.completion_hr.mean() if len(events) else 0.
                frame.loc[row,'first_damaged_station_completion_hr']=events.completion_hr.min() if len(events) else 0.
                frame.loc[row,'last_damaged_station_completion_hr']=events.completion_hr.max() if len(events) else 0.
                for k in np.flatnonzero(np.diff(conn)>1e-12)+1:
                    changing=events[np.isclose(events.completion_hr,clock[k],atol=1e-9,rtol=0)]
                    gained=(C[k]>C[k-1])
                    reconnect.append(dict(r=r,strategy=name,time_hr=clock[k],dependency_mass_before=conn[k-1],
                        dependency_mass_after=conn[k],gain=conn[k]-conn[k-1],gained_nodes=int(gained.sum()),
                        active_sources=int(F[k,source_flag].sum()),
                        simultaneous_completing_station_ids=';'.join(changing.task_id.tolist()),
                        reconnected_station_ids=';'.join(np.array(ids)[gained].tolist())))
                if r in (0,15,1999):
                    explicit=(dt[:,None]*(z['L_total'][sl][:-1]@w.T)).sum(axis=0)
                    np.testing.assert_allclose(explicit,tract,rtol=0,atol=1e-9)
                timing.extend(dict(r=r,strategy=name,task_id=x.task_id,completion_hr=x.completion_hr,
                                   crew_index=x.crew_index,travel_hr=x.travel_hr) for x in events.itertuples())
                start+=length
            assert start==len(z['event_time_hr'])
        frames.append(frame)
        draws.append(dict(r=r,physical_sha256=h,damage_sha256=physical['damage_sha256'],duration_sha256=physical['duration_sha256'],
                          draw_receipt_sha256=v.sha(dp),damaged_stations=int((ds>0).sum()),max_duration_hr=duration.max()))
        if (r+1)%250==0: print('NATIVE_EVIDENCE_QA',r+1,'/2000',flush=True)
    assert all(x<1e-8 for x in errors.values()),errors
    frame=pd.concat(frames,ignore_index=True)
    v.METRICS=tuple(v.METRICS)+tuple(EXTRA)
    effects,levels,differences=a.paired_analysis(frame)
    differences=differences.rename(columns={c:c.replace('_ILS_minus_','_revised_minus_') for c in differences})
    v.csv(OUT/'REALIZATION_LEVEL_POLICY_RESULTS.csv',frame)
    v.csv(OUT/'ALL_PAIRED_METRIC_RESULTS.csv',effects)
    v.csv(OUT/'POLICY_LEVEL_METRIC_RESULTS.csv',levels)
    v.csv(OUT/'PAIRED_EFFECT_DISTRIBUTIONS.csv',differences)
    v.csv(OUT/'PHYSICAL_COHORT_IDENTITY.csv',pd.DataFrame(draws))
    v.csv(OUT/'SOURCE_RECONNECTION_EVENTS.csv',pd.DataFrame(reconnect))
    v.csv(OUT/'STATION_COMPLETION_RECORDS.csv',pd.DataFrame(timing))
    groups={
        'PAIRED_POPULATION_LOSS_RESULTS.csv':[v.PRIMARY],
        'SOURCE_LOSS_DECOMPOSITION.csv':COMP+[v.PRIMARY],
        'HOSPITAL_ASSOCIATED_RESULTS.csv':['hospital_mean_normalized_burden_hr'],
        'SOVI_QUARTILE_AND_EQUITY_RESULTS.csv':['burden_Q1_hr','burden_Q2_hr','burden_Q3_hr','burden_Q4_hr',
                                             'signed_Q4_minus_Q1_hr','absolute_Q4_minus_Q1_hr','burden_gini'],
        'T80_TRAVEL_AND_COMPLETION_RESULTS.csv':['T80_restricted_hr','T80_censored','total_travel_hr','makespan_hr']+EXTRA}
    for name,metrics in groups.items():
        v.csv(OUT/name,pd.concat([levels[levels.metric.isin(metrics)].assign(record_type='policy_level'),
                                 effects[effects.metric.isin(metrics)].assign(record_type='paired_effect')],ignore_index=True))
    curves=[]
    for name,values in curve.items():
        values/=2000
        curves.append(pd.DataFrame(dict(strategy=name,time_hr=np.arange(481.),population_availability=values[:,0],
             Q1_availability=values[:,1],Q4_availability=values[:,2],source_connected_dependency_mass=values[:,3],
             mean_active_Core_sources=values[:,4])))
    v.csv(OUT/'RECOVERY_CURVE_DATA.csv',pd.concat(curves,ignore_index=True))
    influence=[]
    for ref in (s.IMPACT,s.PREVIOUS):
        delta=differences[v.PRIMARY+'_revised_minus_'+ref].to_numpy()
        loo=(delta.sum()-delta)/1999
        for frac in (0,.01,.05,.10):
            count=int(2000*frac); order=np.argsort(delta,kind='stable'); keep=order[count:]
            influence.append(dict(reference=ref,removed_most_favorable_fraction=frac,removed_n=count,
                remaining_n=len(keep),descriptive_mean_difference_hr=delta[keep].mean(),
                full_primary_mean_hr=delta.mean(),remaining_sum_hr=delta[keep].sum(),
                removed_gross_benefit_fraction=float(np.maximum(-delta[order[:count]],0).sum()/np.maximum(-delta,0).sum()),
                leave_one_out_min_hr=loo.min(),leave_one_out_max_hr=loo.max(),
                leave_one_out_ranking_reversals=int((np.sign(loo)!=np.sign(delta.mean())).sum()),
                primary_estimator_changed=False))
    v.csv(OUT/'INFLUENCE_AND_TAIL_SENSITIVITY.csv',pd.DataFrame(influence))
    event_stats=pd.DataFrame(reconnect).groupby('strategy').agg(event_count=('gain','size'),
        mean_event_time_hr=('time_hr','mean'),max_single_gain=('gain','max')).reset_index()
    v.csv(OUT/'SOURCE_EVENT_SUMMARY.csv',event_stats)
    v.write(OUT/'NEW_PHYSICAL_REALIZATION_IDENTITY_QA.json',dict(status='PASS',samples=2000,
        unique_identities=2000,previous_registry_count=len(prior),actual_damage_duration_overlap=0,
        shared_policy_physical_states=True,entropy_rule=[s.SAMPLE_SEED,'r'],complete_rng_receipts=True,
        saved_once_no_redraw=True,first_draw_after_preregistration_receipt=v.read(OUT/'PREREGISTRATION_COMMIT.json')))
    execution=v.read(OUT/'EXECUTION_ACCOUNTING.json')
    assert execution['production_evaluations']==execution['independent_kernel_evaluations']==6000
    assert execution['failed_cases']==0 and execution['optimizer_calls']==0
    v.write(OUT/'FULL_VALIDATION_EXECUTION_ACCOUNTING.json',dict(**execution,
        engineering_calls_separate=v.read(OUT/'ENGINEERING_QA.json')['production_calls'],
        analysis_decoder_replays=6000,additional_physical_samples=0,policy_records=len(frame)))
    v.write(OUT/'INDEPENDENT_NUMERICAL_QA.json',dict(status='PASS',sample_count=2000,policy_records=6000,
        max_errors=errors,tolerance_hr=1e-8,saved_event_integral_checks=6000,tract_integral_checks=6000,
        independent_Lorenz_gini_checks=6000,independent_scheduler_decoder_checks=6000,
        direct_full_time_by_tract_integral_checks=9,late_tasks_retained=int(frame.tasks_completed_after_480.sum()),
        T80_censored_count=int(frame.T80_censored.sum()),no_missing_or_excluded_cases=True,
        bootstrap_unit='complete physical realization',bootstrap_resamples=20000,bootstrap_seed=s.BOOT_SEED,
        exact_event_clock_used=True,hourly_curves_used_only_for_presentation=True,
        no_optimizer_invocations=True,analysis_wall_seconds=time.perf_counter()-tick))
    report(frame,effects,levels,pd.DataFrame(influence))
    print('ANALYSIS_COMPLETE',flush=True)


def report(frame,effects,levels,influence):
    def eff(metric,ref): return effects[(effects.metric==metric)&(effects.reference==ref)].iloc[0]
    def lev(metric,name): return levels[(levels.metric==metric)&(levels.strategy==name)].iloc[0]
    primary,secondary=eff(v.PRIMARY,s.IMPACT),eff(v.PRIMARY,s.PREVIOUS)
    check_metrics=['hospital_mean_normalized_burden_hr','T80_restricted_hr','absolute_Q4_minus_Q1_hr','burden_gini']
    adverse=[m for m in check_metrics if eff(m,s.PREVIOUS).ci95_low>0]
    supported=primary.simultaneous95_high<0 and secondary.simultaneous95_high<0 and not adverse
    decision='CANDIDATE SUPPORTED FOR AUTHOR REVIEW' if supported else 'RETAIN PRIOR VALIDATED CANDIDATE'
    sections=['# Post-evaluation GA prospective physical validation',
        'Exactly 2,000 fresh physical realizations, shared across three frozen sequences: 6,000 native production evaluations and 6,000 independent compiled checks. Zero optimizer searches. Native source gate, Core-source proxy, 2pc50, C57_D1, 92 stations/318 edges, directed travel, original samplers and normalized mapping are unchanged. The validation horizon is480h; the archived planning objective used its original longer horizon. All outcomes were retained.',
        '## Policy identities\n'+ '\n'.join(f"- {p['strategy']}: `{p['sequence_sha256']}`" for p in s.verify()['strategies']),
        '## Mean population loss\n'+ '\n'.join(f"- {name}: {lev(v.PRIMARY,name)['mean']:.12f}h; median {lev(v.PRIMARY,name)['median']:.9f}h." for name in (s.CANDIDATE,s.PREVIOUS,s.IMPACT))]
    for ref in (s.IMPACT,s.PREVIOUS):
        x=eff(v.PRIMARY,ref)
        sections.append(f"## Revised GA minus {ref}\nMean {x.mean_difference:+.12f}h; MCSE{x.mcse:.12f}h. Pointwise95 [{x.ci95_low:+.12f},{x.ci95_high:+.12f}]h; simultaneous95 Bonferroni [{x.simultaneous95_low:+.12f},{x.simultaneous95_high:+.12f}]h. Paired median{x.median_difference:+.12f}h; improved{x.improved_count}/2000 ({x.improved_count/20:.2f}%), worsened{x.worsened_count}, ties{x.ties_count}. p05{x.p05:+.9f}, p95{x.p95:+.9f}, p99{x.p99:+.9f}h; range[{x.min_difference:+.9f},{x.max_difference:+.9f}]h. Mean worst5% difference{x.worst5pct_mean:+.9f}h. This compares two fixed full policies, not the causal effect of elitism across optimizer seeds.")
        c=[eff(m,ref).mean_difference for m in COMP]
        assert abs(sum(c)-x.mean_difference)<1e-8
        source_ratio=c[2]/x.mean_difference if x.mean_difference!=0 else float('nan')
        sections.append(f"Loss decomposition changes: self{c[0]:+.12f}h, threshold{c[1]:+.12f}h, source{c[2]:+.12f}h. Sum{sum(c):+.12f}h; source/total signed ratio{source_ratio:.6f} ({source_ratio*100:.3f}%). This is a net signed accounting ratio, which can exceed100% when other components offset it; not a causal attribution.")
        rows=influence[influence.reference.eq(ref)]
        sections.append('Influence diagnostics (full untrimmed objective remains authoritative):\n'+ '\n'.join(
            f"- Remove most favorable{r.removed_most_favorable_fraction*100:.0f}% descriptively: mean{r.descriptive_mean_difference_hr:+.12f}h; share of gross favorable benefit removed{r.removed_gross_benefit_fraction*100:.3f}%." for r in rows.itertuples())+
            f"\nLeave-one-out mean range[{rows.iloc[0].leave_one_out_min_hr:+.12f},{rows.iloc[0].leave_one_out_max_hr:+.12f}]h; sign reversals{int(rows.iloc[0].leave_one_out_ranking_reversals)}/2000. Several-out rankings are sensitivity descriptions, not new confirmatory estimates.")
    sections.append('## Hospital, timing and equity\nAll intervals below are descriptive pointwise95; lower mean population loss is not automatically improved hospital service, timing, typical realization outcome or equity.')
    for metric in check_metrics+['signed_Q4_minus_Q1_hr','source_disconnected_dependency_integral_hr',
                               'source_dependency_T80_restricted_hr','total_travel_hr','makespan_hr','mean_damaged_station_completion_hr']:
        sections.append('### '+metric+'\n'+ '\n'.join(f"- {name}: mean{lev(metric,name)['mean']:.12f}; median{lev(metric,name)['median']:.9f}." for name in (s.CANDIDATE,s.PREVIOUS,s.IMPACT)))
        for ref in (s.IMPACT,s.PREVIOUS):
            x=eff(metric,ref)
            sections.append(f"- Revised minus{ref}: mean{x.mean_difference:+.12f}; pointwise95[{x.ci95_low:+.12f},{x.ci95_high:+.12f}]; paired median{x.median_difference:+.9f}; unfavorable{x.worsened_count}/2000; p05{x.p05:+.9f},p95{x.p95:+.9f}.")
    sections.append('## Interpretations and boundaries\nHospital endpoint is an unweighted mean burden of hospital-associated tracts, not hospital supply or patient outcomes. Q1-Q4 means use the original SOVI quartile identities and population weights. SignedQ4-Q1 and the mean realizationwise absolute gap are different. Gini uses population-weighted tract burdens. SystemT80 uses native events and explicit480h censoring; makespan may extend beyond480h. Source-connected dependency mass is neither deliveredMW, electrical capacity, actual customers nor verified power flow. Simultaneous station completion and reconnection events are descriptive full-policy timing associations, not controlled station-level causal effects.')
    sections.append('## Three distinct conclusions\nEngineering correctness: all children are evaluated before conditional worst-offspring elite replacement. Optimizer performance: the previous paired seed study did not statistically demonstrate overall optimizer superiority. Restoration policy outcome: this experiment tests exactly one frozen revised sequence on new physical states; it does not retroactively prove algorithm superiority.')
    sections.append(f"## Final recommendation\n**{decision}**. Registered decision uses both simultaneous population-contrast upper limits and checks for entirely adverse descriptive intervals on hospital burden,T80,absolute SOVI gap and Gini versus the prior pure-random GA. Entirely adverse flags: {adverse}. Unresolved intervals are not equivalence/noninferiority findings. The original mean-loss objective has not been changed; medians, unfavorable frequencies and influence sensitivity must accompany any author decision. No formal sequence is promoted.")
    sections.append('## Reproducibility and preservation\nRun `study.py setup`, `study.py engineering`, commit freeze and record `PREREGISTRATION_COMMIT.json`, then `study.py execute`, `analyze.py analyze`, `analyze.py package`, and `publish.py`. The original validation/evaluation modules in `_gaf12/src` are hash-locked, reused without editing. The inherited executor labels realization IDs with `standalone_prospective`; this is only an old identifier prefix, not an ILS strategy or a reused draw. Strategies and complete physical hashes are separately checked. SeedSequence namespace202610120701/r is new; bootstrap seed202610120702,20000 paired resamples. Prior source/draw identities were read for provenance, not outcome-guided selection. Original950 scientific files and862 staged items are verified before/after. The preexisting external manuscript path remains missing; the matching backup was checked read-only and neither restored nor declared authoritative. All conclusions remain conditional on this model, fixed hazard/resource, source proxy and population mapping; this is not empirical validation against observed grid recovery.')
    md('POST_ELITISM_GA_VALIDATION_REPORT.md','\n\n'.join(sections))
    md('FINAL_CANDIDATE_RECOMMENDATION.md',f'''# {decision}

Revised minus Impact-first: {primary.mean_difference:+.12f}h; simultaneous95 [{primary.simultaneous95_low:+.12f},{primary.simultaneous95_high:+.12f}], improved{primary.improved_count}/2000.
Revised minus previous pure-random GA: {secondary.mean_difference:+.12f}h; simultaneous95 [{secondary.simultaneous95_low:+.12f},{secondary.simultaneous95_high:+.12f}], median{secondary.median_difference:+.12f}h, improved{secondary.improved_count}/2000.
Entirely adverse descriptive hospital/T80/absolute-gap/Gini intervals versus prior: {adverse}.

The registered mean-loss objective and conservative author-review rule remain fixed. Secondary unresolved intervals do not show equivalence or safety. Full-policy distributions and net loss decomposition are in the companion report. Engineering correction, unresolved cross-seed optimizer superiority and fixed-policy validation are distinct. Do not promote formal files or transfer old validation results to this candidate.
''')
    v.write(OUT/'VALIDATION_DECISION.json',v.clean(dict(recommendation=decision,primary=primary.to_dict(),
        secondary=secondary.to_dict(),adverse_descriptive_metrics=adverse,formal_promotion=False)))


def package():
    s.configure(); s.verify()
    assert v.read(OUT/'INDEPENDENT_NUMERICAL_QA.json')['status']=='PASS'
    current=s.preserved()
    assert current==v.read(OUT/'PRESERVATION_BASELINE.json')
    target=OUT/'FIXED2000_FULL_EVIDENCE.zip'
    assert not target.exists(),'Never overwrite a completed evidence archive'
    records=[]
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for folder in ('cohort','engineering'):
            for p in sorted((OUT/folder).rglob('*')):
                if p.is_file():
                    name=str(p.relative_to(OUT)).replace('\\','/')
                    records.append(dict(path=name,bytes=p.stat().st_size,sha256=v.sha(p)))
                    z.write(p,name)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None and len(z.namelist())==len(records)
        for record in records:
            assert hashlib.sha256(z.read(record['path'])).hexdigest()==record['sha256']
    v.write(OUT/'FULL_EVIDENCE_MANIFEST.json',dict(archive_sha256=v.sha(target),archive_bytes=target.stat().st_size,
        member_count=len(records),members=records,round_trip_all_members_verified=True))
    v.write(OUT/'REPRODUCIBILITY_AND_PRESERVATION_QA.json',dict(status='PASS_SCIENTIFIC_STATE_WITH_PREEXISTING_EXTERNAL_EXCEPTION',
        protected_scientific_files=950,original_staged_items=862,original_branch_head_index_diff_unchanged=True,
        original_scientific_runtime_unchanged=True,previous_validation_archives_unchanged=True,
        source_candidate_identity_unchanged=True,optimizer_calls=0,new_physical_samples=2000,production_evaluations=6000,
        preregistration=v.read(OUT/'PREREGISTRATION_COMMIT.json'),
        preexisting_external_exception=current['preexisting_external_exception'],
        manuscript_modified_or_restored=False,formal_results_or_Stage7_modified=False,
        archive_round_trip_verified=True,full_evidence_sha256=v.sha(target)))
    files={str(p.relative_to(OUT)).replace('\\','/'):dict(sha256=v.sha(p),bytes=p.stat().st_size)
        for p in sorted(OUT.rglob('*')) if p.is_file() and not str(p.relative_to(OUT)).startswith(('cohort','engineering','__pycache__'))
        and p.name not in ('OUTPUT_HASH_MANIFEST.json','REMOTE_PUBLICATION_VERIFIED.json')}
    v.write(OUT/'OUTPUT_HASH_MANIFEST.json',dict(files=files))
    print('ARCHIVE_ALL_MEMBERS_VERIFIED',len(records),target.stat().st_size,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['analyze','package']);args=p.parse_args()
    analyze() if args.phase=='analyze' else package()
