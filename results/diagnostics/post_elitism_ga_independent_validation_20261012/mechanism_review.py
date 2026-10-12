"""Descriptive review of already completed outcomes; no scoring or sampling."""
import study as s
import numpy as np
import pandas as pd
import networkx as nx


def main():
    s.configure();s.verify()
    v,OUT=s.v,s.OUT
    frame=pd.read_csv(OUT/'REALIZATION_LEVEL_POLICY_RESULTS.csv',float_precision='round_trip')
    effects=pd.read_csv(OUT/'ALL_PAIRED_METRIC_RESULTS.csv',float_precision='round_trip')
    events=pd.read_csv(OUT/'SOURCE_RECONNECTION_EVENTS.csv',dtype={'simultaneous_completing_station_ids':str},float_precision='round_trip')
    model=v.load_model();mass=model['mapping'].weight.T@model['mapping'].population;mass/=mass.sum()
    ids=model['ids'];graph=model['ctx']['graph'];sources=set(model['ctx']['sources'])
    contrasts=[];selected=[]
    for ref in (s.IMPACT,s.PREVIOUS):
        delta=frame.pivot(index='r',columns='strategy',values=v.PRIMARY)[s.CANDIDATE]-frame.pivot(index='r',columns='strategy',values=v.PRIMARY)[ref]
        # Outcome-selected extremes are inspection examples, never inferential cohorts.
        for label,series in [('most_favorable',delta.nsmallest(3)),('most_adverse',delta.nlargest(3))]:
            for r,value in series.items():
                sub=frame[frame.r.eq(r)].set_index('strategy')
                p=sub.loc[s.CANDIDATE];b=sub.loc[ref]
                tasks=pd.read_csv(s.q.ARCHIVE/'cases'/f'{r:04d}'/'TASK_EXECUTION.csv',dtype={'task_id':str},float_precision='round_trip')
                t=tasks.pivot(index='task_id',columns='strategy',values='completion_hr')
                td=t[s.CANDIDATE]-t[ref]
                component=[p[m]-b[m] for m in ('L_self_population_mass_weighted_hr','L_threshold_population_mass_weighted_hr','L_source_population_mass_weighted_hr')]
                assert abs(sum(component)-value)<1e-8
                contrasts.append(dict(reference=ref,example_selection=label,r=int(r),population_difference_hr=value,
                    self_difference_hr=component[0],threshold_difference_hr=component[1],source_difference_hr=component[2],
                    candidate_T80_hr=p.T80_restricted_hr,reference_T80_hr=b.T80_restricted_hr,
                    candidate_source_dependency_integral_hr=p.source_disconnected_dependency_integral_hr,
                    reference_source_dependency_integral_hr=b.source_disconnected_dependency_integral_hr,
                    travel_difference_hr=p.total_travel_hr-b.total_travel_hr,
                    mean_completion_difference_hr=p.mean_damaged_station_completion_hr-b.mean_damaged_station_completion_hr,
                    earlier_station_count=int((td<-1e-9).sum()),later_station_count=int((td>1e-9).sum()),
                    tied_station_count=int((abs(td)<=1e-9).sum()),causal_station_counterfactual=False))
    v.csv(OUT/'MECHANISM_EXTREME_CASE_INSPECTION.csv',pd.DataFrame(contrasts))
    # Examine the largest population-dependency reconnection events within each policy.
    for name,group in events.groupby('strategy'):
        for event in group.nlargest(3,'gain').itertuples():
            with np.load(s.q.ARCHIVE/'cases'/f'{event.r:04d}'/'TRAJECTORIES.npz',allow_pickle=False) as z:
                j=z['policies'].tolist().index(name);start=int(z['event_lengths'][:j].sum());length=int(z['event_lengths'][j])
                clock=z['event_time_hr'][start:start+length]
                k=int(np.flatnonzero(np.isclose(clock,event.time_hr,rtol=0,atol=1e-9))[0])
                assert k>0
                F=z['F'][start:start+length]
                record=dict(strategy=name,r=int(event.r),time_hr=event.time_hr,dependency_gain=event.gain,
                            simultaneous_completing_station_ids=event.simultaneous_completing_station_ids,
                            outcome_selected_descriptive_example=True,causal_station_attribution=False)
                for side,ix in [('before',k-1),('after',k)]:
                    active=np.array(ids)[F[ix].astype(bool)].tolist()
                    components=[]
                    for cc in nx.connected_components(graph.subgraph(active)):
                        if not cc&sources:continue
                        components.append(dict(station_ids=sorted(cc),active_Core_sources=sorted(cc&sources),
                            population_dependency_mass=float(sum(mass[ids.index(x)] for x in cc))))
                    record[side+'_source_connected_components']=components
                gain=sum(x['population_dependency_mass'] for x in record['after_source_connected_components'])-sum(x['population_dependency_mass'] for x in record['before_source_connected_components'])
                assert abs(gain-event.gain)<1e-12
                selected.append(record)
    v.write(OUT/'MAJOR_SOURCE_RECONNECTION_COMPONENTS.json',dict(status='PASS',examples=selected,
        new_physical_draws=0,new_production_evaluations=0,selection='Largest three native reconnection gains per fixed policy; descriptive post-execution examples'))
    def ef(metric,ref):return effects[(effects.metric==metric)&(effects.reference==ref)].iloc[0]
    x,y=ef(v.PRIMARY,s.IMPACT),ef(v.PRIMARY,s.PREVIOUS)
    source=ef('L_source_population_mass_weighted_hr',s.IMPACT)
    hosp=ef('hospital_mean_normalized_burden_hr',s.PREVIOUS)
    t80=ef('T80_restricted_hr',s.PREVIOUS)
    gap=ef('absolute_Q4_minus_Q1_hr',s.PREVIOUS)
    gini=ef('burden_gini',s.PREVIOUS)
    text=f'''# Direct Scientific Answers

1. **Mean population loss versus Impact-first:** lower by {-x.mean_difference:.12f} normalized service-loss hours. The simultaneous95 interval is [{x.simultaneous95_low:+.12f}, {x.simultaneous95_high:+.12f}]h and excludes zero. This is a modeled mean comparison, not actual customer outage reduction.
2. **Favorable realization frequency:** {x.improved_count}/2000 ({x.improved_count/20:.2f}%) improve; {x.worsened_count} worsen; {x.ties_count} tie versus Impact-first.
3. **Previous pure-random GA:** the revised sequence is worse on mean population loss by {y.mean_difference:.12f}h, simultaneous95 [{y.simultaneous95_low:+.12f}, {y.simultaneous95_high:+.12f}]. Median paired difference is {y.median_difference:+.12f}h; only {y.improved_count}/2000 ({y.improved_count/20:.2f}%) improve, and {y.worsened_count} worsen. The mean difference corresponds to {y.mean_difference*3600:.4f} normalized service-loss seconds, a small but clearly resolved model difference, not elapsed restoration time for every person.
4. **Hospital-associated burden:** lower versus Impact-first, but higher versus previous GA by {hosp.mean_difference:.12f}h, descriptive95 [{hosp.ci95_low:+.12f}, {hosp.ci95_high:+.12f}]. This is not hospital operating continuity or electricity supply.
5. **Timing and source reconnection:** mean systemT80 and source-dependency80% crossing are earlier versus Impact-first but later versus previous GA by {t80.mean_difference:.12f}h. Their identical crossing times in this cohort are an observed model result, not a general identity. All6000 T80 values are uncensored and no actual task extends beyond480h; the separate engineering late-duration test verified censor handling. Revised GA uses less directed travel and has earlier mean damaged-station completion than previous GA, yet has greater population-weighted loss. Lower total travel and an unweighted earlier mean completion do not guarantee earlier restoration of important population dependencies.
6. **Distributional equality:** relative to previous GA, the mean realizationwise absoluteQ4-Q1 gap decreases by {-gap.mean_difference:.12f}h, while tract Gini increases by {gini.mean_difference:.12f}. Relative to Impact-first, both absolute disparity and Gini increase. Thus there is no uniform equity improvement. The signedQ4-Q1 level is negative under all three policies; a more negative signed gap cannot be presented as improved equality. Q1-Q4 original-unit values and paired distributions are in the equity CSV.
7. **Influence and tails:** the population benefit over Impact-first is not solely driven by a few favorable outliers: leave-one-out never reverses its sign, and after descriptive removal of the most favorable10%, the remaining mean difference is still -0.380890681229h. Relative to previous GA, every leave-one-out mean remains positive. These exclusions are influence diagnostics only; the primary estimates include all2000 outcomes without trimming.
8. **Source-loss contribution:** versus Impact-first, source-loss change is {source.mean_difference:+.12f}h, or {source.mean_difference/x.mean_difference*100:.3f}% of the net mean reduction. The value exceeds100% because self and threshold loss increase and offset some source-loss benefit. Versus previous GA, the source-loss component decreases but its self/threshold increases more than offset it, leaving a net loss increase. There is no net population improvement over previous GA for which to claim an improvement fraction.
9. **Candidate and algorithm:** **RETAIN PRIOR VALIDATED CANDIDATE**. The new candidate does not satisfy the registered author-review rule and is worse on population mean, hospital-associated mean, meanT80 and Gini versus previous GA. The post-evaluation elitism engineering correction remains valid; this fixed-sequence result neither reverses that correctness nor establishes optimizer superiority. No sequence or algorithm is automatically promoted or reverted.
10. **Conditional scope:** conclusions concern only the unchanged model, fixed2pc50 hazard, C57_D1 crews, Core-source proxy, threshold0.5, directed travel, original repair sampler and population-dependency mapping. They do not establish deliveredMW, station capacity, hospital power, actual customers restored, causality of individual station movements, other-hazard generalization or observed real-world recovery accuracy.

## Reconnection and component evidence

`SOURCE_RECONNECTION_EVENTS.csv` retains every positive native-event dependency-mass reconnection. `MAJOR_SOURCE_RECONNECTION_COMPONENTS.json` reconstructs complete active-source connected components before/after the three largest reconnections per policy, using the frozen graph and saved functional masks. Its dependency-mass gains agree with the native trace within1e-12. `MECHANISM_EXTREME_CASE_INSPECTION.csv` contains the most favorable/adverse three cases for each full-policy contrast, signed loss-component changes, task counts completing earlier/later, travel and T80 changes. These are explicitly outcome-selected descriptive examples, not new cohorts or controlled causal counterfactuals.

Source-connected dependency integral and the source-loss accounting term are distinct. The former integrates1-C against dependency mass; the latter integrates f F (1-C). Because f and F can differ between schedules, a lower source-loss component does not imply a lower disconnected-dependency integral. In this cohort the revised sequence's source-loss component improves slightly versus prior GA, while its disconnected-dependency integral worsens. Both are reported without substituting one for the other.

This supplemental inspection executes no physical sampler, policy evaluation, optimizer or bootstrap. It does not alter the committed freeze, primary analysis or decision rule. Its source is saved to make the descriptive review reproducible.
'''
    (OUT/'DIRECT_SCIENTIFIC_ANSWERS_AND_MECHANISM.md').write_text(text,encoding='utf-8',newline='\n')
    # Verify the completed source package again without reading old outcome values for selection.
    baseline=v.read(OUT/'PREEXECUTION_COMPLETE_SOURCE_QA.json')['files']
    assert all(v.sha(s.SOURCE_OUT/n)==h for n,h in baseline.items())
    assert s.preserved()==v.read(OUT/'PRESERVATION_BASELINE.json')
    v.write(OUT/'POSTEXECUTION_COMPLETE_SOURCE_QA.json',dict(status='PASS',source_files_checked=len(baseline),
        optimizer_calls=0,new_physical_draws=0,new_production_evaluations=0,
        supplemental_source_sha256=v.sha(OUT/'mechanism_review.py'),freeze_rewritten=False,
        original_source_payloads_preserved=True))
    print('MECHANISM_AND_COMPLETE_SOURCE_QA_PASS',len(contrasts),len(selected),flush=True)


if __name__=='__main__':main()
