"""Read-only interpretation after the planning-only decision freeze."""
from __future__ import annotations
import argparse
import ast
import gzip
import io
import json
from pathlib import Path
import pickle
import time
import zipfile
import numpy as np
import pandas as pd
import audit as a

V=a.BASE/'results/diagnostics/pure_random_ga_final_20261011'
GA,IMPACT,LEGACY='GA-pure-random','Impact-first','legacy-warm-start-GA'
PRIMARY='population_resolved_mass_weighted_burden_hr'
COMPONENTS=['L_self_population_mass_weighted_hr','L_threshold_population_mass_weighted_hr','L_source_population_mass_weighted_hr']

def planning_records():
    """Reuse every final main100k run and its prespecified continued prefixes."""
    source=a.PRIOR/'results/diagnostics/ga_random_initialization_isolation_20261011'
    rows=[];trajectories=[];sources={}
    for seed in range(2026103100,2026103120):
        folder=source/f'runs/PURE_RANDOM_GA_{seed}'
        h=a.frame(folder/'GENERATION_DIAGNOSTICS.csv')
        checkpoints_frame=a.frame(folder/'BUDGET_CHECKPOINTS.csv')
        initial_receipt=a.read(folder/'FINAL_100000.json')
        changes=a.read(folder/'STRICT_IMPROVEMENTS.json')
        for budget in [20000,50000,100000]+([250000,500000] if seed<2026103110 else []):
            if (folder/f'FINAL_{budget}.json').exists():
                receipt=a.read(folder/f'FINAL_{budget}.json')
                sources[str(folder/f'FINAL_{budget}.json')]=a.sha(a.payload(folder/f'FINAL_{budget}.json'))
            else:
                cp=checkpoints_frame.loc[checkpoints_frame.distinct_evaluations.eq(budget)].iloc[0]
                receipt=dict(completed=True,distinct_evaluations=int(cp.distinct_evaluations),
                    sequence=ast.literal_eval(cp.sequence),
                    sequence_sha256=cp.sequence_sha256,loss_hr=cp.best_service_loss_hr,
                    initial_best_loss_hr=initial_receipt['initial_best_loss_hr'],
                    ga_generated_gain_hr=initial_receipt['initial_best_loss_hr']-cp.best_service_loss_hr,
                    attempts=int(cp.total_attempts),generation=int(cp.generation),
                    completed_generations=int(h.loc[h.unique_candidates_evaluated<=budget].generation.max()),
                    duplicate_fraction=1-int(cp.distinct_evaluations)/int(cp.total_attempts),
                    wall_seconds=cp.elapsed_seconds,objective_seconds=cp.objective_seconds)
                sources[str(folder/'BUDGET_CHECKPOINTS.csv')]=a.sha(a.payload(folder/'BUDGET_CHECKPOINTS.csv'))
            assert receipt['completed'] and receipt['distinct_evaluations']==budget
            assert a.identity(receipt['sequence'])==receipt['sequence_sha256']
            g=h.loc[h.unique_candidates_evaluated<=budget]
            init=g.iloc[0];last=g.iloc[-1]
            rows.append(dict(stage='historical',case='REF',seed=seed,budget=budget,
                initial_best_loss_hr=receipt['initial_best_loss_hr'],final_loss_hr=receipt['loss_hr'],
                gain_after_random_initialization_hr=receipt['ga_generated_gain_hr'],
                distinct=budget,attempts=receipt['attempts'],completed_generations=receipt['completed_generations'],
                parent_cache_queries=receipt['generation']*100,
                member_duplicate_queries=receipt['attempts']-budget-receipt['generation']*100,
                cache_hit_fraction=receipt['duplicate_fraction'],wall_seconds=receipt['wall_seconds'],
                objective_seconds=receipt['objective_seconds'],sequence_sha256=receipt['sequence_sha256'],
                final_position_entropy=last.position_entropy,final_unique_population=last.unique_population,
                strict_improvements_after_initialization=sum(100<x['distinct_evaluations']<=budget for x in changes),
                mean_parent_intensity=g.parent_selection_intensity.mean(),mean_parent_effective_count=g.parent_effective_count.mean(),
                source='reused existing PURE_RANDOM_GA only; repeated within-seed checkpoints'))
        checkpoints=[100,1000,5000,10000,20000,50000,100000]
        if seed<2026103110: checkpoints += [250000,500000]
        for budget in checkpoints:
            valid=[x for x in changes if x['distinct_evaluations']<=budget]
            best=min(x['service_loss_hr'] for x in valid)
            trajectories.append(dict(stage='historical',case='REF',seed=seed,distinct_evaluations=budget,
                loss_hr=best,source='exact strict-improvement record; not interpolated generation boundary'))
    a.csv('HISTORICAL_REFERENCE_REUSED.csv',rows)
    a.csv('HISTORICAL_SEARCH_TRAJECTORIES.csv',trajectories)
    a.save('HISTORICAL_REFERENCE_SOURCE_HASHES.json',sources)
    print('PLANNING_RECORDS_REUSED',len(rows),len(trajectories),flush=True)

def parameter_summary():
    historical=a.frame(a.OUT/'HISTORICAL_REFERENCE_REUSED.csv')
    wide=historical.pivot(index='seed',columns='budget',values='final_loss_hr')
    marginal=[]
    for lo,hi in [(20000,50000),(50000,100000),(100000,250000),(250000,500000)]:
        pair=wide[[lo,hi]].dropna();change=pair[hi]-pair[lo]
        assert (change<=1e-12).all()
        marginal.append(dict(from_budget=lo,to_budget=hi,n_existing_seeds=len(pair),
            paired_mean_loss_change_hr=change.mean(),paired_median_loss_change_hr=change.median(),
            min_change_hr=change.min(),max_change_hr=change.max(),strict_score_improvements=int((change<-1e-12).sum()),
            unit='Within-seed continued prefixes, not fresh independent trials',inference='Descriptive, no extra parameter-decision test'))
    a.csv('HISTORICAL_WITHIN_SEED_BUDGET_GAINS.csv',marginal)
    frames=[historical]
    trajectories=a.frame(a.OUT/'HISTORICAL_SEARCH_TRAJECTORIES.csv').to_dict('records')
    strict=[];lineage=[]
    tables={'screen':'PARAMETER_SCREEN_RESULTS.csv',
        'confirmation':'PARAMETER_CONFIRMATION_RESULTS.csv',
        'gain_confirmation':'PARAMETER_GAIN_CONFIRMATION_RESULTS.csv'}
    for stage,table in tables.items():
        df=a.frame(a.OUT/table)
        frames.append(df)
        for row in df.to_dict('records'):
            folder=a.OUT/'runtime'/stage/f"{row['case']}_{row['seed']}"
            hist=a.frame(folder/'GENERATION_DIAGNOSTICS.csv')
            for x in hist.to_dict('records'):
                if x['generation']==0 or x['generation']%25==0 or x['generation']==hist.generation.max():
                    lineage.append(dict(stage=stage,case=row['case'],seed=row['seed'],**x))
            changes=a.read(folder/'STRICT_IMPROVEMENTS.json')
            for x in changes:
                strict.append(dict(stage=stage,case=row['case'],seed=row['seed'],
                    generation=x['generation'],distinct_evaluations=x['distinct_evaluations'],
                    loss_hr=x['service_loss_hr'],sequence_sha256=a.identity(x['sequence'])))
            for budget in [row['population'],1000,5000,10000,20000,50000,100000]:
                if budget>row['budget']: continue
                valid=[x for x in changes if x['distinct_evaluations']<=budget]
                trajectories.append(dict(stage=stage,case=row['case'],seed=row['seed'],
                    distinct_evaluations=budget,loss_hr=min(x['service_loss_hr'] for x in valid),source='exact strict-improvement archive'))
    all_rows=pd.concat(frames,ignore_index=True)
    assert (all_rows.member_duplicate_queries>=0).all()
    a.csv('BUDGET_AND_DUPLICATE_ACCOUNTING.csv',all_rows)
    a.csv('GA_SEARCH_TRAJECTORY_SUMMARY.csv',trajectories)
    a.csv('STRICT_IMPROVEMENT_OBSERVATIONS.csv',strict)
    a.csv('POPULATION_AND_SELECTION_DIAGNOSTICS.csv',lineage)
    summaries=[]
    for keys,g in all_rows.groupby(['stage','case','budget']):
        summaries.append(dict(stage=keys[0],case=keys[1],budget=keys[2],n=len(g),
            mean_final_loss_hr=g.final_loss_hr.mean(),sd_final_loss_hr=g.final_loss_hr.std(),
            median_final_loss_hr=g.final_loss_hr.median(),min_final_loss_hr=g.final_loss_hr.min(),max_final_loss_hr=g.final_loss_hr.max(),
            mean_initial_best_loss_hr=g.initial_best_loss_hr.mean(),mean_actual_search_gain_hr=g.gain_after_random_initialization_hr.mean(),
            min_actual_search_gain_hr=g.gain_after_random_initialization_hr.min(),
            mean_generations=g.completed_generations.mean(),mean_duplicate_fraction=g.cache_hit_fraction.mean(),
            mean_strict_improvements_after_initialization=g.strict_improvements_after_initialization.mean(),
            mean_last_complete_generation_entropy=g.final_position_entropy.mean(),
            mean_last_complete_generation_unique_population=g.final_unique_population.mean(),
            unique_final_sequence_hashes=g.sequence_sha256.nunique(),
            mean_objective_seconds=g.objective_seconds.mean(),mean_wall_seconds=g.wall_seconds.mean(),
            inference='same-seed budget observations are not independent replications'))
    a.csv('CONFIGURATION_SEARCH_SUMMARY.csv',summaries)
    receipt=a.OUT/'FROZEN_REFERENCE_PREFIX_REPLAY_QA.json'
    if receipt.exists():
        replay=a.read(receipt)
        assert replay['entire_cache_insertion_order_and_operator_state_exact']
        assert replay['source_checkpoint_sha256']==a.sha(a.payload(V/'candidate_lineage/STATE_100000.pkl.gz'))
        assert replay['original_final_sequence_hash']=='edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a'
    else:reference_replay()
    print('PARAMETER_SUMMARY_PASS',len(all_rows),flush=True)


def reference_replay():
    # Exact replay of selected reference100k prefix uses saved scores, not a new search.
    checkpoint=V/'candidate_lineage/STATE_100000.pkl.gz'
    with gzip.open(a.payload(checkpoint),'rb') as f: state=pickle.load(f)
    count=[0]
    index={s:i for i,s in enumerate(a.load_study().load_model()[0].ids)}
    def cached(seq):
        key=bytes(index[s] for s in seq);count[0]+=1
        assert key in state['cache'];return state['cache'][key]
    replay=a.engine({}).run_search(items=tuple(index),incumbents={},objective=cached,
        seed=2026103108,config=a.REFERENCE,max_evaluations=100000,checkpoints=(20000,50000,100000))
    assert replay['cache']==state['cache'] and list(replay['cache'])==list(state['cache'])
    for key in ('population','scores','phase','generation','attempts','next_index','best_seq','best_seen'):
        assert replay['state'][key]==state['state'][key],key
    a.save('FROZEN_REFERENCE_PREFIX_REPLAY_QA.json',dict(status='PASS',seed=2026103108,logical_distinct_evaluations=count[0],
        actual_new_physical_objective_calls=0,original_final_sequence_hash=a.identity(replay['best_sequence']),
        entire_cache_insertion_order_and_operator_state_exact=True,
        source_checkpoint_sha256=a.sha(a.payload(checkpoint))))
    print('FROZEN_REFERENCE_REPLAY_PASS',count[0],flush=True)

def outcome_gate():
    assert (a.OUT/'PARAMETER_DECISION_FROZEN.json').exists()
    d=a.read(a.OUT/'PARAMETER_DECISION_FROZEN.json')
    assert not d['validation_outcomes_loaded'] and not d['frozen_validated_method_changed']
    for n,h in d['evidence_source_sha256'].items(): assert a.sha(a.OUT/n)==h
    a.save('MECHANISM_ACCESS_GATE.json',dict(parameter_decision_sha256=a.sha(a.OUT/'PARAMETER_DECISION_FROZEN.json'),
        parameter_decision_md_sha256=a.sha(a.OUT/'FINAL_PURE_RANDOM_GA_PARAMETER_DECISION.md'),
        new_optimizer_calls_after_gate=0,new_physical_draws=0,
        allowed='Read-only existing2000 validation, no tuning/reselection or modified definitions'))

def distributions(df):
    p=df.pivot(index='realization_id',columns='strategy',values=PRIMARY)
    assert len(p)==2000
    delta=p[GA]-p[IMPACT];x=delta.to_numpy();n=len(x)
    sums=[]
    for label,y in [('improved',x[x<-1e-9]),('worsened',x[x>1e-9]),('all',x)]:
        sums.append(dict(subset=label,n=len(y),fraction=len(y)/n,
            within_subset_mean_hr=y.mean(),contribution_to_overall_mean_hr=y.sum()/n,
            median_hr=np.median(y),min_hr=y.min(),max_hr=y.max()))
    order=np.argsort(x)
    for label,idx in [('largest_benefit_1pct',order[:20]),('largest_harm_1pct',order[-20:]),
        ('largest_benefit_5pct',order[:100]),('largest_harm_5pct',order[-100:])]:
        y=x[idx];sums.append(dict(subset=label,n=len(y),fraction=len(y)/n,within_subset_mean_hr=y.mean(),
            contribution_to_overall_mean_hr=y.sum()/n,median_hr=np.median(y),min_hr=y.min(),max_hr=y.max()))
    a.csv('PAIRED_REALIZATION_BENEFIT_SUMMARY.csv',sums)
    a.csv('PLOTTING_TABLE_C.csv',pd.DataFrame(dict(realization_id=p.index,ga_minus_impact_hr=x)))
    return delta

def mechanism():
    outcome_gate();tick=time.perf_counter()
    from la_grid.diagnostics import independent_validation_20261010 as v
    model=v.load_model();mapping=model['mapping'];mass=mapping.weight.T@mapping.population;total=mass.sum()
    df=a.frame(V/'REALIZATION_OUTCOMES.csv');assert len(df)==6000 and df.realization_id.nunique()==2000
    effects=a.frame(V/'PAIRED_EFFECTS.csv');levels=a.frame(V/'POLICY_OUTCOMES.csv')
    assert set(df.strategy)=={GA,IMPACT,LEGACY}
    delta=distributions(df)
    comp=[]
    for name in COMPONENTS+[PRIMARY]:
        p=df.pivot(index='realization_id',columns='strategy',values=name)
        d=p[GA]-p[IMPACT]
        comp.append(dict(component=name,ga_mean_hr=p[GA].mean(),impact_mean_hr=p[IMPACT].mean(),difference_hr=d.mean(),
            paired_sd_hr=d.std(),n=2000,definition='exact saved event-clock integral',attribution='whole-policy accounting, not station-level causal effect'))
    assert abs(sum(x['difference_hr'] for x in comp[:3])-comp[3]['difference_hr'])<1e-10
    a.csv('SERVICE_LOSS_COMPONENT_TABLE.csv',comp)
    a.csv('PLOTTING_TABLE_B_COMPONENTS.csv',comp)
    paired_components=pd.DataFrame(index=delta.index)
    for name in COMPONENTS+[PRIMARY]:
        p=df.pivot(index='realization_id',columns='strategy',values=name)
        paired_components[name]=p[GA]-p[IMPACT]
    np.testing.assert_allclose(paired_components[COMPONENTS].sum(axis=1),paired_components[PRIMARY],atol=1e-10)
    a.csv('PAIRED_COMPONENT_EFFECTS_ALL2000.csv',paired_components.reset_index())
    metrics=['burden_Q1_hr','burden_Q2_hr','burden_Q3_hr','burden_Q4_hr',
        'signed_Q4_minus_Q1_hr','absolute_Q4_minus_Q1_hr','burden_gini','hospital_mean_normalized_burden_hr','T80_restricted_hr']
    trade=[]
    for metric in metrics:
        g=df.pivot(index='realization_id',columns='strategy',values=metric)
        e=effects[(effects.reference==IMPACT)&(effects.metric==metric)].iloc[0]
        trade.append(dict(metric=metric,ga_mean=g[GA].mean(),impact_mean=g[IMPACT].mean(),difference=(g[GA]-g[IMPACT]).mean(),
            pointwise95_low=e.ci95_low,pointwise95_high=e.ci95_high,interval_scope='descriptive pointwise; not population primary family',
            unit='dimensionless' if metric=='burden_gini' else 'normalized service-loss hours' if 'T80' not in metric else 'hours; mean per-realization exact system crossing'))
    a.csv('VULNERABILITY_AND_EQUITY_TRADEOFF.csv',trade)
    a.csv('PLOTTING_TABLE_D.csv',trade)
    # Deterministic illustration selection after frozen parameter decision; never calibration.
    selected=[int(str(delta.idxmin()).rsplit('_',1)[1]),int(str(delta.idxmax()).rsplit('_',1)[1])]
    central=delta.index[np.argmin(abs(delta.to_numpy()-np.median(delta.to_numpy())))];selected.append(int(str(central).rsplit('_',1)[1]))
    selected=sorted(set(selected));a.save('ILLUSTRATIVE_REALIZATION_SELECTION.json',dict(r=selected,
        rule='most negative, most positive and nearest median paired population effect; descriptive examples, not causal controls',
        decision_freeze_sha256=a.sha(a.OUT/'PARAMETER_DECISION_FROZEN.json')))
    archive=a.payload(V/'FIXED2000_FULL_EVIDENCE.zip')
    event_rows=[];case_rows=[];illustration_rows=[];curves={p:np.zeros((481,3)) for p in (GA,IMPACT)}
    max_conservation=0.;reconnection=[]
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        def member(r,file):
            candidates=[n for n in names if f'/{r:04d}/' in n and n.endswith('/'+file)]
            assert len(candidates)==1,(r,file,len(candidates))
            return z.read(candidates[0]),candidates[0]
        for r in range(2000):
            raw,entry=member(r,'TRAJECTORIES.npz')
            with np.load(io.BytesIO(raw),allow_pickle=False) as arrays:
                assert arrays['station_ids'].astype(str).tolist()==model['ids']
                start=0
                for policy,length in zip(arrays['policies'].astype(str),arrays['event_lengths']):
                    times=arrays['event_time_hr'][start:start+length]
                    c=arrays['C'][start:start+length];f=arrays['f'][start:start+length];e=arrays['e'][start:start+length]
                    loss=sum(arrays[k][start:start+length] for k in ('L_self','L_threshold','L_source'))
                    max_conservation=max(max_conservation,float(np.max(abs(loss-arrays['L_total'][start:start+length]))))
                    if policy in (GA,IMPACT):
                        connected=c@mass/total;available=e@mass/total;rawmean=f@mass/total
                        ix=np.searchsorted(times,np.arange(481.),side='right')-1
                        curves[policy]+=np.c_[available[ix],connected[ix],rawmean[ix]]
                        for j in range(1,len(times)-1):
                            gain=connected[j]-connected[j-1]
                            event_rows.append(dict(r=r,strategy=policy,time_hr=times[j],
                                new_source_connected_dependency_mass=total*gain,
                                new_source_connected_fraction=gain,effective_availability_gain=available[j]-available[j-1],
                                newly_connected_stations=int(np.sum((c[j]>0)&(c[j-1]==0)))))
                        for target in (.25,.5,.8,.95):
                            hits=np.flatnonzero(connected>=target)
                            reconnection.append(dict(r=r,strategy=policy,target_fraction=target,
                                first_source_connected_mass_crossing_hr=times[hits[0]] if len(hits) else np.nan,
                                censored=not len(hits),definition='source-connected population dependency mass, not delivered customers/MW'))
                        saved=df[df.realization_id.str.endswith(f'_{r:04d}') & df.strategy.eq(policy)]
                        assert len(saved)==1
                        for field,metric in zip(('L_self','L_threshold','L_source','L_total'),COMPONENTS+[PRIMARY]):
                            exact=np.diff(times)@(arrays[field][start:start+length-1]@mass/total)
                            assert abs(exact-saved[metric].iloc[0])<1e-8,(r,policy,field)
                        if r in selected:
                            illustration_rows.extend(dict(r=r,strategy=policy,time_hr=t,connected_mass_fraction=cm,effective_availability=av,raw_availability=rv) for t,cm,av,rv in zip(times,connected,available,rawmean))
                    start+=length
                assert start==len(arrays['event_time_hr'])
            tasks_raw,task_entry=member(r,'TASK_EXECUTION.csv')
            tasks=pd.read_csv(io.BytesIO(tasks_raw),dtype={'task_id':str})
            p=tasks.pivot(index='task_id',columns='strategy',values='completion_hr')
            diff=p[GA]-p[IMPACT]
            case_rows.append(dict(r=r,earlier_stations=int((diff<-1e-9).sum()),later_stations=int((diff>1e-9).sum()),
                equal_stations=int((abs(diff)<=1e-9).sum()),mean_completion_change_hr=diff.mean(),
                total_directed_travel_change_hr=tasks[ tasks.strategy.eq(GA)].travel_hr.sum()-tasks[tasks.strategy.eq(IMPACT)].travel_hr.sum()))
            if r in selected:
                a.csv(f'illustrations/TASK_EXECUTION_{r:04d}.csv',tasks)
                a.save(f'illustrations/SOURCE_REFERENCE_{r:04d}.json',dict(archive_sha256=a.sha(archive),native_task_entry=task_entry,native_trajectory_entry=entry))
            if r%500==0: print('NATIVE_MECHANISM_RECONSTRUCTION',r,flush=True)
    a.csv('NATIVE_SOURCE_RECONNECTION_EVENTS.csv',event_rows)
    a.csv('SOURCE_CONNECTED_MASS_CROSSINGS.csv',reconnection)
    a.csv('PAIRED_STATION_COMPLETION_AND_TRAVEL.csv',case_rows)
    a.csv('ILLUSTRATIVE_NATIVE_EVENT_TRAJECTORIES.csv',illustration_rows)
    crows=[]
    for p,c in curves.items():
        c/=2000
        crows.extend(dict(strategy=p,time_hr=i,effective_availability=row[0],source_connected_dependency_mass_fraction=row[1],raw_availability=row[2]) for i,row in enumerate(c))
    a.csv('PLOTTING_TABLE_B_CURVES.csv',crows)
    # Reconstruct exact graph components at the single largest mass-connection event
    # in each illustrative policy, matching the saved native connectivity mask.
    import networkx as nx
    component_rows=[];station_event_rows=[]
    with zipfile.ZipFile(archive) as z:
        for r in selected:
            candidates=[n for n in z.namelist() if f'/{r:04d}/' in n and n.endswith('/TRAJECTORIES.npz')]
            with np.load(io.BytesIO(z.read(candidates[0])),allow_pickle=False) as arrays:
                start=0
                for policy,length in zip(arrays['policies'].astype(str),arrays['event_lengths']):
                    if policy in (GA,IMPACT):
                        c=arrays['C'][start:start+length];F=arrays['F'][start:start+length]
                        f=arrays['f'][start:start+length]
                        cm=c@mass;idx=1+int(np.argmax(np.diff(cm)))
                        t=arrays['event_time_hr'][start+idx]
                        tasks=a.frame(a.OUT/f'illustrations/TASK_EXECUTION_{r:04d}.csv')
                        tasks['task_id']=tasks.task_id.astype(str)
                        completed=set(tasks.loc[tasks.strategy.eq(policy)&np.isclose(tasks.completion_hr,t,atol=1e-9,rtol=0),'task_id'])
                        for pos,s in enumerate(model['ids']):
                            station_event_rows.append(dict(r=r,strategy=policy,event_hr=t,station_id=s,
                                is_core_source=s in model['ctx']['sources'],dependency_mass=mass[pos],
                                f_before=f[idx-1,pos],f_after=f[idx,pos],F_before=F[idx-1,pos],F_after=F[idx,pos],
                                C_before=c[idx-1,pos],C_after=c[idx,pos],native_task_completion_at_event=s in completed,
                                interpretation='Native event association; no isolated-station counterfactual'))
                        for side,j in [('before',idx-1),('after',idx)]:
                            nodes={s for s,active in zip(model['ids'],F[j]) if active}
                            comps=list(nx.connected_components(model['ctx']['graph'].subgraph(nodes)))
                            keep=set().union(*(x for x in comps if x & set(model['ctx']['sources'])))
                            assert keep=={s for s,vv in zip(model['ids'],c[j]) if vv}
                            for ci,group in enumerate(sorted(comps,key=lambda x:tuple(sorted(x)))):
                                positions=[model['ids'].index(s) for s in group]
                                component_rows.append(dict(r=r,strategy=policy,event_hr=t,state=side,component=ci,
                                    source_ids='|'.join(sorted(group&set(model['ctx']['sources']))),
                                    station_ids='|'.join(sorted(group)),node_count=len(group),
                                    population_dependency_mass=mass[positions].sum(),source_connected=bool(group&set(model['ctx']['sources']))))
                    start+=length
    a.csv('ILLUSTRATIVE_SOURCE_COMPONENTS.csv',component_rows)
    a.csv('ILLUSTRATIVE_EVENT_STATION_CHANGES.csv',station_event_rows)
    a.save('MECHANISM_NUMERICAL_QA.json',dict(status='PASS',physical_samples_generated=0,optimizer_calls=0,
        native_record_count=2000,source_loss_reintegration_checks=4000,
        all_component_integral_checks=16000,
        exact_component_mask_reconstructions=len(selected)*4,max_loss_conservation_error=max_conservation,
        source_archive_sha256=a.sha(archive),wall_seconds=time.perf_counter()-tick))
    a.csv('VALIDATION_SOURCE_HASHES.csv',[dict(path=str(p),sha256=a.sha(a.payload(p))) for p in [V/'REALIZATION_OUTCOMES.csv',V/'PAIRED_EFFECTS.csv',V/'POLICY_OUTCOMES.csv',V/'FIXED2000_FULL_EVIDENCE.zip']])
    print('MECHANISM_PASS',len(event_rows),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['planning','summary','replay','mechanism']);x=p.parse_args()
    {'planning':planning_records,'summary':parameter_summary,'replay':reference_replay,'mechanism':mechanism}[x.phase]()
