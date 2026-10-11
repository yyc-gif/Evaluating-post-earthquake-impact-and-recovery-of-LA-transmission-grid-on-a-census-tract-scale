"""Reconcile preserved planning experiments and analyze prospective seed contrasts."""
from __future__ import annotations
import argparse
import json
import hashlib
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy import stats

from la_grid.diagnostics.ga_ils_parameter_defense_20261010 import (
    R, OUT, lp, read, save, sha, load, CONFIRM, SCREEN, ils_config,
)
from la_grid.diagnostics import ga_search_budget_sensitivity as old

D = R / 'results/diagnostics'


def frame(name):
    return pd.read_csv(lp(D / name))


def csv(name, rows):
    data = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    data.to_csv(lp(OUT / name), index=False)


def inventory():
    sources = [
        ('deeper', 'ga_deeper_research_20261009/continuation/SEED_LEVEL_SEARCH_RESULTS.csv',
         dict(configuration='configuration', seed='seed', budget='budget', loss='planning_loss_hr',
              attempts='attempted_calls', distinct='distinct_evaluations', wall='wall_seconds', sequence='sequence_sha256', initial='initial_best_hr')),
        ('initialization', 'ga_initialization_reconciliation_20261009/UNIQUE_INITIALIZATION_OBSERVATIONS.csv',
         dict(configuration='case', seed='seed', budget='budget', loss='final_best_loss_hr',
              attempts='total_attempted_evaluations', distinct='distinct_evaluations', wall='elapsed_wall_seconds', sequence='sequence_sha256', initial='initial_best_loss_hr')),
        ('parameter_followup', 'ga_initialization_reconciliation_20261009/PARAMETER_RUN_SUMMARY.csv',
         dict(configuration='case', seed='seed', budget='budget', loss='final_best_loss_hr',
              attempts='total_attempts', distinct='distinct_evaluations', wall='elapsed_wall_seconds', sequence='sequence_sha256', initial='initial_best_loss_hr')),
        ('operator_and_old_ga', 'ga_optimization_20261009/GA_PARAMETER_SENSITIVITY.csv',
         dict(configuration='config_id', seed='seed', budget='budget', loss='best_planning_loss_hr',
              attempts='total_attempts', distinct='distinct_evaluations', wall='elapsed_seconds', sequence='sequence_sha256')),
        ('local_lns', 'ga_noncontiguous_connectivity_lns_20261010/SEED_LEVEL_100000.csv',
         dict(configuration='method', seed='seed', budget='budget', loss='search_best_loss_hr',
              attempts='attempted_evaluations', distinct='distinct_evaluations', wall='elapsed_wall_seconds', sequence='sequence_sha256')),
        ('previous_initializer_screen','ga_initialization_reconciliation_20261009/PREVIOUS_SCREENING_UNIQUE_OBSERVATIONS.csv',
         dict(configuration='case',seed='seed',budget='budget',loss='final_best_loss_hr',
              attempts='total_attempts',distinct='expensive_evaluations',wall='elapsed_seconds',sequence='sequence_sha256',initial='initial_best_loss_hr')),
        ('older_generation_limited_prior_development','extended_ga_20261008/SEARCH_SUMMARY.csv',
         dict(configuration='population',seed='seed',budget='unique_candidates_evaluated',loss='retained_service_loss_hr',
              distinct='unique_candidates_evaluated',wall='elapsed_seconds',sequence='sequence_sha256')),
        ('original_generation_limited_budget','ga_search_budget_20261007/GA_SEARCH_BUDGET_SENSITIVITY.csv',
         dict(configuration='stage',seed='seed',budget='unique_candidates_evaluated',loss='best_non_incumbent_service_loss_hr',
              distinct='unique_candidates_evaluated',wall='elapsed_seconds',sequence='best_non_incumbent_sequence_identity')),
    ]
    allrows = []
    manifest = []
    for family, name, mapping in sources:
        data = frame(name)
        digest = sha(D / name)
        manifest.append(dict(path=name, sha256=digest, rows=len(data)))
        for idx, src in data.iterrows():
            row = {target: src.get(column) for target, column in mapping.items()}
            row.update(family=family, source_table=str((D/name).relative_to(R)), source_table_sha256=digest,
                source_csv_row=int(idx)+2, physical_input='original frozen 64; physical-input SHA in MODEL_IDENTITY.json',
                objective='mean exact population dependency service-loss hours; unchanged gate/scheduler',
                source_run_id=src.get('run_id'), source_artifact_id=src.get('artifact_id'), source_commit=src.get('source_commit'),
                config_json=src.get('configuration_json'), actual_generation=src.get('actual_generation', src.get('actual_generations')),
                scope='historical development; no independent physical confirmation of settings',
                initialization='see exact source configuration/allocation; missing counters not inferred')
            row['source_row_json']=json.dumps({str(k):None if pd.isna(v) else v
                for k,v in src.items()},sort_keys=True,
                default=lambda value:value.item() if isinstance(value,np.generic) else str(value))
            if family=='deeper': row['family']=family+'_'+str(src['batch'])
            if family=='operator_and_old_ga': row['family']=family+'_'+str(src['phase'])
            if family=='previous_initializer_screen':row['family']=family+'_'+str(src['phase'])
            if family=='older_generation_limited_prior_development':
                row['configuration']=f"p{int(src.population)}_g{int(src.generations)}"
                row['actual_generation']=src.generations
                row['budget_type']='actual distinct work of generation-limited run, not matched-query target'
                row['same_seed_other_budget_or_generation_not_independent']=True
            if family=='original_generation_limited_budget':
                row['configuration']=f"{src.stage}_p{int(src.population)}_g{int(src.generations)}"
                row['actual_generation']=src.generations
                row['budget_type']='actual distinct work of generation-limited run, not matched-query target'
                row['retained_service_loss_hr']=src.retained_service_loss_hr
                row['sequence_scope']='best generated non-incumbent; its loss may exceed retained reference loss'
                row['same_seed_other_budget_or_generation_not_independent']=True
            if row.get('attempts') is not None and row.get('distinct') is not None:
                row['duplicate_calls'] = row['attempts']-row['distinct']
            allrows.append(row)
    data = pd.DataFrame(allrows)
    extra=[]
    for p in lp(D/'ga_scheduling_aware_lns_20261010/reconciliation').glob('v*_log_batch_*.json'):
        payload=read(p)
        for idx,src in enumerate(payload['records']):
            extra.append(dict(family='original_lns_'+str(payload['source_run_id']),configuration=src['method'],
                seed=src['seed'],budget=src.get('budget',src.get('distinct_evaluations')),loss=src.get('search_best_loss_hr',src.get('final_loss_hr')),
                distinct=src.get('budget',src.get('distinct_evaluations')),attempts=src['attempted_evaluations'],wall=src.get('elapsed_wall_seconds',src.get('wall_seconds')),
                sequence=src.get('sequence_sha256',src.get('best_sha')),source_table=str(p.relative_to(lp(R))),source_table_sha256=sha(p),
                source_csv_row=None,source_json_record=idx,source_run_id=payload['source_run_id'],
                physical_input='original frozen 64; completion audit ORIGINAL_160_AUDIT.json',
                objective='unchanged full64 planning objective',scope='historical final-budget records, not checkpoints'))
    cv=frame('ga_deeper_research_20261009/continuation/CROSSFIT_SEED_LEVEL_RESULTS.csv')
    for idx,src in cv.iterrows():
        extra.append(dict(family='internal_crossfit_fold'+str(src['fold']),configuration=src['method'],
            seed=src['seed'],budget=src['budget'],loss=src['training_loss_hr'],
            distinct=src['budget'],attempts=src['attempted_evaluations'],wall=None,
            sequence=src['sequence_sha256'],source_table='results/diagnostics/ga_deeper_research_20261009/continuation/CROSSFIT_SEED_LEVEL_RESULTS.csv',
            source_csv_row=idx+2,source_table_sha256=sha(D/'ga_deeper_research_20261009/continuation/CROSSFIT_SEED_LEVEL_RESULTS.csv'),
            physical_input='48 training of original64; disjoint16 held out; development cohort already inspected',
            objective='original evaluator on fixed48; holdout_loss_hr in source table',scope='diagnostic crossfit, not untouched physical validation'))
    data=pd.concat([data,pd.DataFrame(extra)],ignore_index=True)
    data['record_kind']='optimizer final-budget observation'
    refs=data.configuration.eq('impact_reference')
    data.loc[refs,'record_kind']='deterministic reference, not a search or independent seed'
    data.loc[refs,['distinct','budget']]=0
    hybrid=frame('ga_optimization_20261009/GA_LOCAL_SEARCH_AND_HYBRID_RESULTS.csv')
    additional=[]
    for idx,src in hybrid.iterrows():
        additional.append(dict(family='deterministic_local_or_hybrid',configuration=src['method'],
            seed=src.get('seed',np.nan),budget=src['budget'],loss=src['best_planning_loss_hr'],
            distinct=src['distinct_evaluations'],attempts=src['total_attempts'],wall=src['elapsed_seconds'],
            sequence=src['sequence_sha256'],record_kind='deterministic stage' if pd.isna(src.get('seed')) else 'hybrid, 50k GA prefix already counted',
            source_table='results/diagnostics/ga_optimization_20261009/GA_LOCAL_SEARCH_AND_HYBRID_RESULTS.csv',source_csv_row=idx+2,
            source_table_sha256=sha(D/'ga_optimization_20261009/GA_LOCAL_SEARCH_AND_HYBRID_RESULTS.csv'),
            physical_input='original64; prefix/additional cost separated in source record',objective='unchanged original mean planning loss',
            scope='additional stage; not an independent replication of its starting search'))
    data=pd.concat([data,pd.DataFrame(additional)],ignore_index=True)
    attribution=frame('final_ga_method_20261009/GA_INITIALIZATION_VS_SEARCH_IMPROVEMENT.csv')
    attribution=attribution[attribution.new_calls_this_round>0]
    controlled=[]
    for idx,src in attribution.iterrows():
        record=read(R/src.source_run)
        controlled.append(dict(family='final_method_missing_attribution_controls',configuration=src.method,
            seed=src.seed,budget=src.budget,loss=src.final_best_hr,distinct=src.distinct_expensive_evaluations,
            attempts=src.total_attempts,wall=src.wall_seconds,sequence=record['sequence_sha256'],
            source_table=src.source_run,source_table_sha256=src.source_run_sha256,config_json=src.source_config,
            physical_input='unchanged original64',objective='original mean planning loss',
            record_kind='controlled attribution search; reused old references omitted',
            scope='five fixed seeds; prior development reused, not independent cohort'))
    cert=read(D/'ga_deeper_research_20261009/continuation/REFINEMENT_CERTIFICATE_RECONCILED.json')
    candidates=read(D/'ga_deeper_research_20261009/continuation/IMPORTANT_CANDIDATES.json')
    retained={}
    for name in ('FrozenGA','FirstILS','RefinedILS'):
        candidate=candidates[name]
        retained[name]=dict(sequence=candidate['sequence'],sequence_sha256=candidate['sequence_sha256'],
            loss_hr=candidate.get('loss_hr',candidate.get('planning_loss_hr')))
    save(OUT/'IMPORTANT_HISTORICAL_CANDIDATES.json',retained)
    controlled.append(dict(family='historical_selected_ils_refinement',configuration='four_neighborhood_deterministic',
        seed=304,budget=cert['distinct_evaluations'],distinct=cert['distinct_evaluations'],
        attempts=cert['attempts'],loss=cert['end_loss_hr'],sequence=retained['RefinedILS']['sequence_sha256'],
        record_kind='additional deterministic stage of selected seed304, not independent optimizer seed',
        source_table='results/diagnostics/ga_deeper_research_20261009/continuation/REFINEMENT_CERTIFICATE_RECONCILED.json',
        source_table_sha256=sha(D/'ga_deeper_research_20261009/continuation/REFINEMENT_CERTIFICATE_RECONCILED.json'),
        physical_input='unchanged original64',objective='original mean planning loss',scope='selected-seed stage; additional cost separately charged'))
    data=pd.concat([data,pd.DataFrame(controlled)],ignore_index=True)
    key = ['family', 'configuration', 'seed', 'budget']
    assert not data.duplicated(key).any()
    data['replication_unit'] = 'optimizer seed conditional on fixed planning states'
    # Same seed reused across configurations is paired; across budgets is continued/replayed, not a new seed.
    data['same_seed_other_budget'] = data.groupby(['family', 'configuration', 'seed'])['budget'].transform('nunique')>1
    data['distinct_seed_count_within_family'] = data.groupby(['family', 'configuration'])['seed'].transform('nunique')
    data['same_named_configuration_seed_across_budget_or_phase']=data.groupby(['configuration','seed'])['budget'].transform('nunique')>1
    csv('EXPERIMENT_INVENTORY.csv', data)
    save(OUT / 'HISTORICAL_TABLE_HASHES.json', manifest)
    existing = sorted(set(int(s) for s in data.seed.dropna()))
    assert not set(existing)&(set(SCREEN)|set(CONFIRM))
    save(OUT / 'HISTORICAL_RECONCILIATION_QA.json', dict(status='PASS', inventory_records=len(data),
        deterministic_reference_records=int(refs.sum()),additional_stage_records=len(additional),
        tables=manifest, duplicate_primary_keys=0, historical_seeds=existing, new_seeds_disjoint=True,
        deeper_original_duplicate_audit=read(D/'ga_deeper_research_20261009/continuation/RECONCILIATION_QA.json'),
        initialization_original_duplicate_audit=read(D/'ga_initialization_reconciliation_20261009/RECONCILIATION_AUDIT.json'),
        uncertainties_source='PAIRED_SIMULTANEOUS_CONTRASTS.csv and PAIRED_PARAMETER_EFFECTS.csv',
        conflicting_claims=[
            'Older continuation says scheduling-aware LNS untested; superseded by completed scheduling/noncontiguous LNS records.',
            'Poor legacy P500 is not controlled P500 with warm initialization/swap/one elite.',
            'Historical 30 screening plus 20 nested confirmation initialization seeds are not 50 independent seeds.',
            'Original 100k ILS and selected-seed deterministic refinement are separate stages with separate costs.',
            'Original selected config status pending validation superseded by frozen completed validation; unchanged file retained.']))
    print('INVENTORY', len(data), 'historical observations and explicitly labeled stages/references', flush=True)


def contrast(values, name, family, family_size, scope, costs=None):
    d = np.asarray(values, dtype=float)
    n = len(d)
    assert n>=2 and np.isfinite(d).all()
    mean = float(d.mean()); sd = float(d.std(ddof=1)); se=sd/np.sqrt(n)
    t=stats.t.ppf(.975, n-1)*se
    bt=stats.t.ppf(1-.025/family_size, n-1)*se
    rng=np.random.default_rng(2026101300)
    bank=rng.integers(0,n,size=(20000,n))
    boot=np.mean(d[bank],axis=1)
    lo,hi=np.quantile(boot,[.025,.975])
    row=dict(family=family, contrast=name, scope=scope, n=n,
        mean_delta_hr=mean, median_delta_hr=float(np.median(d)), sd_delta_hr=sd,
        wins=int((d<-1e-10).sum()), losses=int((d>1e-10).sum()), ties=int((abs(d)<=1e-10).sum()),
        t95_low_hr=mean-t,t95_high_hr=mean+t,bootstrap95_low_hr=float(lo),bootstrap95_high_hr=float(hi),
        simultaneous95_low_hr=mean-bt,simultaneous95_high_hr=mean+bt,family_size=family_size,
        bootstrap_replications=20000, bootstrap_seed=2026101300, equivalence_margin_hr=None,
        sign='negative favors first named intervention', seed_observations_json=json.dumps(d.tolist()))
    if costs: row.update(costs)
    return row


def historical_statistics():
    """Reanalyze saved seed blocks, never rerun their scientific objectives."""
    rows=[]; observations=[]
    for source, field, family in (
        ('ga_initialization_reconciliation_20261009/PAIRED_PARAMETER_SEED_DIFFERENCES.csv',
         'difference_hr','historical_parameter'),
        ('ga_initialization_reconciliation_20261009/PAIRED_SEED_EFFECTS.csv',
         'final_change_hr','historical_initialization')):
        data=frame(source)
        for budget, cohort in data.groupby('budget'):
            for case, group in cohort.groupby('case'):
                group=group.sort_values('seed')
                row=contrast(group[field],str(case)+' minus saved baseline',family+'_'+str(int(budget)),
                    cohort.case.nunique(),'retrospective reanalysis of preserved optimizer seeds')
                row.update(source_table=str(D/source),source_sha256=sha(D/source),budget=int(budget))
                rows.append(row)
                observations.extend(dict(family=row['family'],contrast=row['contrast'],seed=int(s),delta_hr=float(d))
                                    for s,d in zip(group.seed,group[field]))
    data=frame('ga_deeper_research_20261009/continuation/SEED_LEVEL_SEARCH_RESULTS.csv')
    effects=frame('ga_deeper_research_20261009/continuation/PAIRED_SIMULTANEOUS_CONTRASTS.csv')
    for _, effect in effects.iterrows():
        if pd.isna(effect.weights_json) or not str(effect.weights_json).startswith('{'):
            continue
        batch=effect.batch
        source_batch='confirmation_100k' if batch=='confirmation_100k_mechanisms' else batch
        subset=data[data.batch==source_batch]
        if batch=='root_cause_100k':
            addition=data[(data.batch=='confirmation_100k') & data.configuration.eq('p100_k3_m10_nquarter')].copy()
            addition['configuration']='final_swap_with_elite'
            subset=pd.concat([subset,addition],ignore_index=True)
        value='initial_best_hr' if 'initial_loss' in effect.contrast else 'planning_loss_hr'
        wide=subset.pivot(index='seed',columns='configuration',values=value).sort_index()
        weights=json.loads(effect.weights_json)
        delta=sum(weight*wide[case] for case,weight in weights.items())
        row=contrast(delta,effect.contrast,'historical_'+batch,int(effect.ci_family_size),
                     'retrospective saved contrast; original cohort and multiplicity family retained')
        assert abs(row['mean_delta_hr']-effect.mean_delta_hr)<1e-10
        assert abs(row['simultaneous95_low_hr']-effect.simultaneous95_low_hr)<1e-9
        row.update(weights_json=effect.weights_json,source_table=str(D/'ga_deeper_research_20261009/continuation/SEED_LEVEL_SEARCH_RESULTS.csv'))
        rows.append(row)
        observations.extend(dict(family=row['family'],contrast=row['contrast'],seed=int(s),delta_hr=float(d))
                            for s,d in delta.items())
    original=frame('ga_optimization_20261009/GA_PARAMETER_SENSITIVITY.csv')
    for phase, pairs in (
        ('screen',[('p100_m0.4','original_p100'),('p100_m0.6','original_p100')]),
        ('operators',[('operator_swap','operator_inversion'),('operator_insertion','operator_inversion'),
                      ('operator_pmx','operator_inversion'),('operator_cycle','operator_inversion'),
                      ('operator_adaptive','operator_inversion'),('operator_restart','operator_inversion'),
                      ('operator_crowding','operator_inversion')]),
        ('operator_confirmation',[('operator_swap','operator_mixed')])):
        wide=original[original.phase==phase].pivot(index='seed',columns='config_id',values='best_planning_loss_hr').sort_index()
        for a,b in pairs:
            if a not in wide or b not in wide: continue
            delta=wide[a]-wide[b]
            row=contrast(delta,a+' minus '+b,'historical_'+phase,len(pairs),
                         'historical operator comparison; five pilot seeds nested in 20-seed confirmation')
            rows.append(row)
            observations.extend(dict(family=row['family'],contrast=row['contrast'],seed=int(s),delta_hr=float(d))
                                for s,d in delta.items())
    csv('HISTORICAL_PAIRED_STATISTICS.csv',rows)
    csv('HISTORICAL_PAIRED_SEED_DIFFERENCES.csv',observations)
    print('HISTORICAL_STATISTICS',len(rows),'saved contrasts',flush=True)


def normalized_rows():
    rows=[]
    for phase in ('screen','confirmation'):
        for p in lp(OUT / phase).glob('*.json'):
            r=read(p)
            row={k:r.get(k) for k in ('phase','case','method','seed','budget','distinct_evaluations',
                'actual_new_expensive','prefix_cache_reused','attempted_evaluations','duplicates',
                'search_best_loss_hr','initial_best_loss_hr','elapsed_wall_seconds','objective_seconds',
                'cpu_seconds','completed_budget','generations','accepted_moves','restart_count',
                'sequence_sha256','initial_population_sha256','post_initializer_rng_sha256','censoring')}
            row.update(source_file=str(p.relative_to(lp(R))),source_sha256=sha(p),
                config_json=json.dumps(r['config'],sort_keys=True),
                operator_counts_json=json.dumps(r.get('operator_counts')),
                initial_vs_search_gain_hr=r['initial_best_loss_hr']-r['search_best_loss_hr'],
                nonobjective_wall_seconds=r['elapsed_wall_seconds']-r['objective_seconds'],
                postvalidation_exploratory=True)
            rows.append(row)
    return pd.DataFrame(rows)


def complete_inventory(data):
    historical=pd.read_csv(lp(OUT/'EXPERIMENT_INVENTORY.csv'))
    historical=historical[~historical.family.str.startswith('new_',na=False)]
    added=[]
    for _,r in data.iterrows():
        added.append(dict(family='new_'+r.phase,configuration=r['case'],seed=r.seed,
            budget=r.budget,loss=r.search_best_loss_hr,distinct=r.distinct_evaluations,
            attempts=r.attempted_evaluations,duplicate_calls=r.duplicates,wall=r.elapsed_wall_seconds,
            cpu_seconds=r.cpu_seconds,sequence=r.sequence_sha256,initial=r.initial_best_loss_hr,
            config_json=r.config_json,source_table=r.source_file,source_table_sha256=r.source_sha256,
            completed_budget=r.completed_budget,record_kind='new prospective seed-final observation',
            physical_input='original frozen64; per-run input_identity and MODEL_IDENTITY.json',
            objective='original mean exact population service loss, unchanged gate/scheduler',
            initialization='full chromosome list, initializer fingerprint and RNG state SHA in raw record',
            replication_unit='optimizer seed; paired across settings; no validation tuning',
            scope='postvalidation exploratory for paper; prospective confirmation within diagnostic study'))
    for r in read(OUT/'REFINEMENT_MULTISEED_ACCOUNTING.json')['results']:
        folder=OUT/'refinement'/f"s{r['seed']}"
        local=read(folder/'RUN.json');ga=read(folder/'GA_JOINT_BUDGET.json')
        for stage in ('refinement','ga_joint_continuation'):
            added.append(dict(family='new_'+stage,configuration=stage,seed=r['seed'],budget=r['joint_budget'],
                loss=r['refined_loss_hr'] if stage=='refinement' else r['ga_joint_loss_hr'],
                distinct=r['refinement_additional_distinct'] if stage=='refinement' else r['ga_additional_distinct'],
                attempts=local['total_attempts'] if stage=='refinement' else r['ga_attempted_replay_included'],
                wall=local['elapsed_seconds'] if stage=='refinement' else ga['elapsed_wall_seconds'],
                sequence=r['sequence_sha256'] if stage=='refinement' else ga['sequence_sha256'],
                prefix_cache_reused=0 if stage=='refinement' else r['ga_prefix_replayed'],
                source_table=f"results/diagnostics/ga_ils_parameter_defense_20261010/refinement/s{r['seed']}/JOINT_ACCOUNTING.json",
                record_kind='additional stage; not independent of its 100k prefix',
                physical_input='unchanged original frozen64',objective='original mean exact planning loss',
                scope='postvalidation; seed preselected before outcomes; prefix cost counted in primary observation'))
    combined=pd.concat([historical,pd.DataFrame(added)],ignore_index=True)
    model=read(D/'ga_deeper_research_20261009/continuation/MODEL_IDENTITY.json')
    save(OUT/'MODEL_IDENTITY.json',model)
    combined['physical_input_identity_file']='MODEL_IDENTITY.json (64 sample hashes and graph/source/travel hashes)'
    combined['uncertainty_reference']='HISTORICAL_PAIRED_STATISTICS.csv or PAIRED_PARAMETER_CONTRASTS.csv; stage effects REFINEMENT_PAIRED_STATISTICS.csv'
    csv('EXPERIMENT_INVENTORY.csv',combined)


def analyze():
    data=normalized_rows()
    complete_inventory(data)
    csv('NEW_SEED_LEVEL_OBSERVATIONS.csv',data)
    csv('GA_PARAMETER_CONTROLLED_RESULTS.csv',data[data.method=='GA'])
    csv('ILS_PARAMETER_CONTROLLED_RESULTS.csv',data[data.method=='ILS'])
    summary=data.groupby(['phase','case']).agg(n=('seed','size'),mean_hr=('search_best_loss_hr','mean'),
        median_hr=('search_best_loss_hr','median'),sd_hr=('search_best_loss_hr','std'),best_hr=('search_best_loss_hr','min'),
        mean_distinct=('distinct_evaluations','mean'),mean_attempts=('attempted_evaluations','mean'),
        mean_wall_seconds=('elapsed_wall_seconds','mean'),mean_search_gain=('initial_vs_search_gain_hr','mean'),
        mean_cpu_seconds=('cpu_seconds','mean'),mean_objective_seconds=('objective_seconds','mean'),
        mean_nonobjective_wall_seconds=('nonobjective_wall_seconds','mean'),
        mean_restarts=('restart_count','mean'),mean_accepted=('accepted_moves','mean'),
        completed_budgets=('completed_budget','sum')).reset_index()
    csv('CONFIGURATION_SUMMARY.csv',summary)
    rows=[];paired=[]
    for phase in ('screen','confirmation'):
        x=data[data.phase==phase].set_index(['seed','case'])
        seeds=SCREEN if phase=='screen' else CONFIRM
        selection=read(OUT/'SCREEN_SELECTION.json')['cases'] if phase=='confirmation' else []
        families={'ga_elite':[(f'ga_elite{j}','ga_elite1') for j in (0,2,3)],
            'ils_confirmation':[(c,'ils_mix') for c in ('ils_swap','ils_insertion','ils_inversion','ils_current','ils_no_perturb')]+[(c,'ils_mix') for c in selection]}
        if phase=='confirmation':
            families['ils_confirmation'] += [('ils_swap_stag2000','ils_mix'),('ils_swap_no_perturb','ils_mix')]
            families['method']=[('ils_mix','ga_elite1'),('ils_cold','ga_cold'),('ils_mix','ils_cold'),('ga_elite1','ga_cold')]
            families['method_reduced_exploratory']=[('ils_swap','ga_elite1'),('ils_swap_stag2000','ga_elite1')]
        else:
            families['ils_screen_factors']=[(c,'ils_mix') for c in ('ils_stag200','ils_stag2000','ils_small','ils_large')]
        for family, pairs in families.items():
            for a,b in pairs:
                first=x.loc[(list(seeds),a),:].sort_index();second=x.loc[(list(seeds),b),:].sort_index()
                assert list(first.index.get_level_values('seed'))==list(second.index.get_level_values('seed'))
                d=first.search_best_loss_hr.to_numpy()-second.search_best_loss_hr.to_numpy()
                complete=bool(first.completed_budget.all() and second.completed_budget.all())
                scope='prospectively fixed confirmation' if phase=='confirmation' else 'engineering screen'
                if family=='method_reduced_exploratory':scope='retrospective reduced-neighborhood method comparisons, not prospective primary family'
                if a in selection: scope+='; setting selected by independent screen'
                if not complete: scope+='; unequal actual-budget accessibility control, NOT equal-budget quality'
                rows.append(contrast(d,a+' minus '+b,phase+'_'+family,len(pairs),scope,
                    dict(mean_first_distinct=float(first.distinct_evaluations.mean()),mean_second_distinct=float(second.distinct_evaluations.mean()),
                        mean_first_attempts=float(first.attempted_evaluations.mean()),mean_second_attempts=float(second.attempted_evaluations.mean()),
                        mean_first_wall_seconds=float(first.elapsed_wall_seconds.mean()),mean_second_wall_seconds=float(second.elapsed_wall_seconds.mean()),
                        paired_mean_wall_ratio=float(np.mean(first.elapsed_wall_seconds.to_numpy()/second.elapsed_wall_seconds.to_numpy())),
                        fully_equal_budget=complete)))
                for seed,delta in zip(seeds,d):paired.append(dict(phase=phase,family=family,contrast=a+' minus '+b,seed=seed,delta_hr=delta))
    screen=data[data.phase=='screen'].pivot(index='seed',columns='case',values='search_best_loss_hr').sort_index()
    for op in ('swap','insertion'):
        d=screen[f'ils_{op}_stag200']-screen[f'ils_{op}']-(screen.ils_stag200-screen.ils_mix)
        rows.append(contrast(d,f'{op} x stagnation200','screen_interaction',2,'prespecified engineering interaction'))
        paired.extend(dict(phase='screen',family='interaction',contrast=f'{op} x stagnation200',
            seed=int(seed),delta_hr=float(delta)) for seed,delta in d.items())
    full=data[data.phase=='confirmation'].pivot(index='seed',columns='case',values='search_best_loss_hr').sort_index()
    d=full.ils_swap_stag2000-full.ils_swap-(full.ils_stag2000-full.ils_mix)
    rows.append(contrast(d,'swap x stagnation2000','confirmation_interaction',1,
        'screen-motivated interaction; independent confirmation seeds; postvalidation exploratory'))
    paired.extend(dict(phase='confirmation',family='interaction',contrast='swap x stagnation2000',
        seed=int(seed),delta_hr=float(delta)) for seed,delta in d.items())
    csv('PAIRED_PARAMETER_CONTRASTS.csv',rows);csv('PAIRED_SEED_DIFFERENCES.csv',paired)
    csv('GA_ILS_EQUAL_BUDGET_COMPARISON.csv',[r for r in rows if 'method' in r['family']])
    trajectories=[]
    for phase in ('screen','confirmation'):
        for p in lp(OUT/phase).glob('*.json'):
            r=read(p)
            for cp in r['checkpoints']:
                trajectories.append(dict(phase=phase,case=r['case'],seed=r['seed'],
                    evaluations=cp.get('evaluations',cp.get('distinct_evaluations')),
                    loss_hr=cp.get('loss_hr',cp.get('best_service_loss_hr')),
                    attempts=cp.get('attempts',cp.get('total_attempts')),checkpoint_is_independent_run=False,
                    wall_seconds=cp.get('elapsed_seconds'),sequence_sha256=cp.get('sequence_sha256')))
    csv('OPTIMIZER_CONVERGENCE_AND_COST.csv',trajectories)
    init=frame('final_ga_method_20261009/GA_INITIALIZATION_VS_SEARCH_IMPROVEMENT.csv')
    save(OUT/'FROZEN_INITIALIZATION_CONTRIBUTION.json',dict(
        prior_gain_vs_impact_hr=33.57830255999924-33.03813174326729,
        selected_post_prior_gain_hr=33.03813174326729-32.997840773882714,
        total_gain_hr=33.57830255999924-32.997840773882714,
        inherited_fraction=(33.57830255999924-33.03813174326729)/(33.57830255999924-32.997840773882714),
        exact_generation_zero_source='Per-seed initial values in cited original table, neighbors may exceed prior.',
        historical_table_sha256=sha(D/'final_ga_method_20261009/GA_INITIALIZATION_VS_SEARCH_IMPROVEMENT.csv'),
        warm_start_development_cost_in_final_budget=False))
    save(OUT/'PARAMETER_SELECTION_REGISTER.json',dict(formal_ga_retained=True,
        formal_ga_selection_sha256='8370673fdf0c23009d3c96f3bf2aa8163725bb554056923edd3a161b2251ccab',
        prospective_spec_commit='196e09c',observational_repair_commit='3766c1a',confirmation_addendum_commit='c4b765e',
        screen_selected_ils_threshold_and_perturbation=read(OUT/'SCREEN_SELECTION.json'),
        screening_and_confirmation_seeds_disjoint=True,new_settings_postvalidation_exploratory=True,
        independent_validation_not_used_for_selection=True,new_candidate_promotion=False,
        scope_decision='A in main paper; Scope B calibrated conditional development comparison supported in supplement, not formal optimizer replacement'))
    print('ANALYZED',len(data), 'runs',len(rows),'contrasts',flush=True)


def candidate_qa():
    from la_grid.revision.r1_equity_amendment_execute import execution_context
    from la_grid.revision.r1_realization_scheduling import RealizationInputs
    from la_grid.revision.r1_source_gate import evaluate_source_gate
    from la_grid.revision.r1_ga_revision import evaluate_direct_population_burden_aggregate
    tick=time.perf_counter();k,inc,prior,ident=load()
    candidates={}
    data=normalized_rows()
    for (phase,case),group in data.groupby(['phase','case']):
        best=group.sort_values(['search_best_loss_hr','seed']).iloc[0]
        src=read(R/best.source_file)
        candidates.setdefault(src['sequence_sha256'],dict(sequence=src['best_sequence'],expected_loss_hr=src['search_best_loss_hr'],origins=[]))['origins'].append(dict(phase=phase,case=case,seed=int(src['seed'])))
    for p in lp(OUT/'refinement').glob('s*/JOINT_ACCOUNTING.json'):
        r=read(p)
        candidates.setdefault(r['sequence_sha256'],dict(sequence=r['best_sequence'],expected_loss_hr=r['refined_loss_hr'],origins=[]))['origins'].append(dict(phase='refinement',seed=r['seed']))
        joint=read(p.parent/'GA_JOINT_BUDGET.json')
        candidates.setdefault(joint['sequence_sha256'],dict(sequence=joint['best_sequence'],expected_loss_hr=joint['search_best_loss_hr'],origins=[]))['origins'].append(dict(phase='matched_ga_continuation',seed=r['seed']))
    formal=read(D/'final_ga_method_20261009/SELECTED_SEQUENCE.json')
    seq=formal.get('sequence',formal.get('selected_sequence'))
    assert seq is not None
    reference=old.per_sample(k,seq)
    context,_,_=execution_context(k.ids)
    rows=[];reports=[]
    for digest,item in candidates.items():
        assert old.identity(item['sequence'])==digest
        exact=old.per_sample(k,item['sequence']);production=[]
        for r in range(64):
            realization=RealizationInputs(f'2pc50__planning_{r:04}',pd.Series(k.damage[r],index=k.ids),pd.Series(k.duration[r],index=k.ids))
            value=evaluate_direct_population_burden_aggregate(sequence=item['sequence'],realization=realization,
                crew_origin_ids=context['origins'],base_to_task_hr=context['base'],task_to_task_hr=context['task'],
                horizon_hr=k.horizon,source_gate=lambda raw:evaluate_source_gate(raw,context['graph'],context['sources'],threshold=.5),
                station_population_mass=k.station_mass,population_resolved_mass=k.total_mass)
            assert abs(value-exact[r])<1e-8
            production.append(value)
            rows.append(dict(sequence_sha256=digest,realization=r,production_loss_hr=value,compiled_loss_hr=exact[r],
                frozen_ga_loss_hr=reference[r],delta_hr=value-reference[r],absolute_parity_error_hr=abs(value-exact[r])))
        values=np.array(production);delta=values-reference
        assert abs(values.mean()-item['expected_loss_hr'])<1e-8
        loo=(delta.sum()-delta)/63
        reports.append(dict(sequence_sha256=digest,**item,production_mean_hr=float(values.mean()),
            mean_minus_frozen_ga_hr=float(delta.mean()),median_delta_hr=float(np.median(delta)),
            improved_states=int((delta<-1e-10).sum()),worsened_states=int((delta>1e-10).sum()),
            most_improved_realization=int(np.argmin(delta)),most_improved_delta_hr=float(delta.min()),
            most_worsened_realization=int(np.argmax(delta)),most_worsened_delta_hr=float(delta.max()),
            mean_improvement_component_hr=float(np.minimum(delta,0).mean()),
            mean_worsening_component_hr=float(np.maximum(delta,0).mean()),
            delta_q10_hr=float(np.quantile(delta,.1)),delta_q90_hr=float(np.quantile(delta,.9)),
            leave_one_out_min_hr=float(loo.min()),leave_one_out_max_hr=float(loo.max()),
            leave_one_out_sign_reversals=int((np.sign(loo)!=np.sign(delta.mean())).sum()),
            omit_realization15_delta_hr=float(np.delete(delta,15).mean()),
            omit_five_best_delta_hr=float(np.sort(delta)[5:].mean()),
            maximum_parity_error_hr=float(np.max(abs(values-exact))),postvalidation_exploratory=True))
        print('CANDIDATE_PRODUCTION_QA',len(reports),'/',len(candidates),digest[:12],float(values.mean()),flush=True)
    csv('CANDIDATE_PRODUCTION_PER_STATE.csv',rows)
    save(OUT/'IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json',dict(status='PASS',candidates=reports,
        compiled_full64_calls=len(candidates)+1,production_state_calls=64*len(candidates),loader_setup_calls=8,
        wall_seconds=time.perf_counter()-tick,input_identity=ident,formal_candidate_changed=False,
        new_physical_samples=0,validation_outcomes_accessed=False))


def accounting():
    data=normalized_rows()
    search=int(data.distinct_evaluations.sum());attempt=int(data.attempted_evaluations.sum())
    refine=read(OUT/'REFINEMENT_MULTISEED_ACCOUNTING.json')['results']
    refinement=sum(r['refinement_additional_distinct'] for r in refine)
    continuation=sum(r['ga_additional_distinct'] for r in refine)
    qa=read(OUT/'IMPORTANT_CANDIDATES_PRODUCTION_AND_INFLUENCE.json')
    executions=[read(OUT/f'{p}_EXECUTION.json') for p in ('screen','confirmation')]
    refinement_attempts=ga_full_attempts=ga_prefix_attempts=0
    continuation_wall=0.
    for r in refine:
        folder=OUT/'refinement'/f"s{r['seed']}"
        refinement_attempts+=read(folder/'RUN.json')['total_attempts']
        joint=read(folder/'GA_JOINT_BUDGET.json')
        prefix=read(OUT/'confirmation'/f"ga_elite1_s{r['seed']}.json")
        ga_full_attempts+=joint['attempted_evaluations']
        ga_prefix_attempts+=prefix['attempted_evaluations']
        continuation_wall+=joint['elapsed_wall_seconds']
    extra=12_000+sum(e['setup_scores'] for e in executions)+16+2+8+15+qa['loader_setup_calls']+qa['compiled_full64_calls']
    result=dict(search_distinct_calls=search,attempted_search_calls=attempt,
        within_search_cache_hits=attempt-search,refinement_distinct_calls=refinement,
        matched_ga_continuation_new_distinct=continuation,matched_ga_prefix_reused=500000,
        refinement_attempted_neighbor_queries=refinement_attempts,
        refinement_cache_hits=refinement_attempts-refinement,
        matched_ga_replay_included_attempts=ga_full_attempts,
        matched_ga_replayed_prefix_attempts=ga_prefix_attempts,
        matched_ga_continuation_new_attempts=ga_full_attempts-ga_prefix_attempts,
        matched_ga_continuation_and_replay_wall_seconds=continuation_wall,
        total_attempted_queries_including_replay=attempt+refinement_attempts+ga_full_attempts,
        setup_parity_full64_equivalent_calls=extra,production_state_calls=qa['production_state_calls'],
        new_expensive_full64_calls=search+refinement+continuation+extra,
        search_worker_cpu_seconds=float(data.cpu_seconds.sum()),search_worker_wall_seconds=float(data.elapsed_wall_seconds.sum()),
        screen_batch_wall_seconds=executions[0]['wall_seconds'],confirmation_batch_wall_seconds=executions[1]['wall_seconds'],
        refinement_wall_seconds=sum(r['refinement_wall_seconds'] for r in refine),production_qa_wall_seconds=qa['wall_seconds'],
        incomplete_searches=int((~data.completed_budget).sum()),
        accounting_notes=['12000 short QA search calls includes failed serializer invocation and successful repeat.',
            'Distinct budget is within-search permutation-cache uniqueness, not global uniqueness across all settings/seeds. Fresh-case repeated reference/permutation scores are actual new physical objective calls and are charged again.',
            '16 loader calls and 2 original-wrapper checks in the two short QA invocations.',
            '8 loader scores per worker per batch, 8 refinement loader and 15 refinement-start scores.',
            'Refinement per-sample exports invoke compiled _one_sample 64 times per seed; counted as 5 full64 equivalents.',
            'Matched GA prefix replay consumes zero new prefix physical scores; replay wall time is disclosed, not hidden.',
            'Production state calls are separate units, not added as if full64 calls.',
            'Wall includes retained diagnostic observation; GA has per-generation diversity/history instrumentation unlike sequence-only ILS. Objective time is separately retained; nonobjective time is not claimed entirely algorithm overhead.',
            'Historical experiment totals not added as new computation.'],new_physical_samples=0)
    # Five original refinement per-sample exports, each equivalent to one full64 objective.
    result['setup_parity_full64_equivalent_calls']+=5
    result['new_expensive_full64_calls']+=5
    save(OUT/'EXECUTION_ACCOUNTING.json',result)
    print('ACCOUNTING',json.dumps(result),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('task',choices=['inventory','historical_statistics','analyze','candidate_qa','accounting'])
    task=p.parse_args().task
    globals()[task]()


if __name__=='__main__': main()
