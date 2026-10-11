"""Seed-unit inference, exact run QA and original64-state production parity."""
from __future__ import annotations
import argparse
import json
import time
import numpy as np
import pandas as pd
from scipy import stats
import study as s


def csv(name, rows):
    (rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows)).to_csv(s.lp(s.OUT/name),index=False,lineterminator='\n')


def paired(d):
    d=np.asarray(d,float); n=len(d); mean=d.mean(); sd=d.std(ddof=1); se=sd/np.sqrt(n)
    rng=np.random.default_rng(2026103200)
    boot=d[rng.integers(0,n,size=(20000,n))].mean(axis=1)
    return dict(n=n,mean_delta_hr=mean,median_delta_hr=np.median(d),sd_delta_hr=sd,
        pure_wins=int((d < -1e-9).sum()),seeded_wins=int((d > 1e-9).sum()),ties=int((abs(d)<=1e-9).sum()),
        t95_low_hr=mean-stats.t.ppf(.975,n-1)*se,t95_high_hr=mean+stats.t.ppf(.975,n-1)*se,
        simultaneous95_low_hr=mean-stats.t.ppf(.995,n-1)*se,
        simultaneous95_high_hr=mean+stats.t.ppf(.995,n-1)*se,
        bootstrap95_low_hr=np.quantile(boot,.025),bootstrap95_high_hr=np.quantile(boot,.975),
        bootstrap_bonferroni95_low_hr=np.quantile(boot,.005),bootstrap_bonferroni95_high_hr=np.quantile(boot,.995))


def summaries():
    assert s.read(s.OUT/'MAIN_EXECUTION.json')['all_completed']
    design=s.read(s.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    assert s.digest(s.OUT/'study.py')==design['source_hashes']['results/diagnostics/ga_random_initialization_isolation_20261011/study.py']
    rows,qa,contrib,seqs,cost=[],[],[],[],[]
    extended=s.lp(s.OUT/'EXTENSION_EXECUTION.json').exists()
    if extended: assert s.read(s.OUT/'EXTENSION_EXECUTION.json')['all_completed']
    for seed in s.MAIN:
        initial_pair=[]
        for mode in s.MODES:
            folder=s.OUT/'runs'/f'{mode}_{seed}'
            init=s.read(folder/'INITIAL_POPULATION.json');initial_pair.append(init)
            initseq=[tuple(x) for x in init['initial_sequences']]
            assert init['archive_before_first_evaluation']==[]
            assert all(s.identity(x)==h for x,h in zip(initseq,init['initial_hashes']))
            r100=s.read(folder/'FINAL_100000.json')
            assert r100['implementation_sha256']==s.digest(s.OUT/'study.py')
            budgets=[100000,250000,500000] if extended and seed in s.RESERVE else [100000]
            for budget in budgets:
                receipt=s.read(folder/f'FINAL_{budget}.json')
                assert receipt['distinct_evaluations']==budget and receipt['completed']
                assert receipt['model_identity']==design['model_identity']
                assert receipt['sequence_sha256']==s.identity(receipt['sequence'])
                assert s.digest(folder/f'STATE_{budget}.pkl.gz')==receipt['checkpoint_sha256']
                seqs.append({k:receipt[k] for k in ['mode','seed','budget','sequence','sequence_sha256','loss_hr']})
            state=s.read_state(folder)
            assert len(state['cache'])==budgets[-1]==state['state']['expensive_calls']
            assert state['state']['lookup_calls']==0 and state['state']['restart_count']==0
            assert not state['config']['adaptive'] and not state['config']['diversity_replacement']
            ids=design['model_identity']['planning_sample_hashes']
            with np.load(s.lp(folder/'CANDIDATES.npz')) as z:
                orders=z['orders'];station_ids=z['station_ids'].astype(str).tolist()
                assert np.all(np.sort(orders,axis=1)==np.arange(92))
                assert len(orders)==len(state['cache'])
                expected=np.array([[station_ids.index(v) for v in seq] for seq in initseq],dtype=np.uint8)
                assert np.array_equal(orders[:100],expected)
                assert np.array_equal(z['fitness'],np.array(list(state['cache'].values())))
                assert np.all(z['first_attempt'][1:]>z['first_attempt'][:-1])
            moves=s.read(folder/'STRICT_IMPROVEMENTS.json')
            assert moves[0]['sequence']==list(initseq[0])
            assert all(a['service_loss_hr']>b['service_loss_hr'] for a,b in zip(moves,moves[1:]))
            hist=pd.read_csv(s.lp(folder/'GENERATION_DIAGNOSTICS.csv'))
            assert hist.iloc[0].unique_population==100
            for r in state['budget_rows']:
                budget=r['distinct_evaluations']
                if budget not in s.CHECKPOINTS: continue
                initbest=float(hist.iloc[0].population_best_service_loss_hr)
                loss=r['best_service_loss_hr']
                rr=dict(mode=mode,seed=seed,budget=budget,loss_hr=loss,
                    initial_best_loss_hr=initbest,initial_mean_loss_hr=hist.iloc[0].population_mean_service_loss_hr,
                    initial_unique=100,initial_position_entropy=hist.iloc[0].position_entropy,
                    initial_hamming_fraction=hist.iloc[0].positional_hamming_fraction,
                    initial_adjacency_overlap=hist.iloc[0].directed_adjacency_overlap,
                    ga_generated_gain_hr=initbest-loss,gain_vs_impact_hr=s.IMPACT_REF-loss,
                    inherited_initial_gain_vs_impact_hr=s.IMPACT_REF-initbest,
                    final_gap_from_frozen_hr=loss-s.FROZEN,
                    high_quality=loss<=s.FROZEN+s.MARGIN,beats_frozen=loss<s.FROZEN-1e-9,
                    completed_generations=int(hist.loc[hist.unique_candidates_evaluated<=budget,'generation'].max()),
                    boundary_generation=r['generation'],distinct_evaluations=budget,attempts=r['total_attempts'],
                    duplicates=r['total_attempts']-budget,duplicate_fraction=1-budget/r['total_attempts'],
                    wall_seconds=r['elapsed_seconds'],objective_seconds=r['objective_seconds'],
                    sequence_sha256=r['sequence_sha256'],
                    last_improvement_evaluations=max(x['distinct_evaluations'] for x in moves if x['distinct_evaluations']<=budget))
                # The unchanged engine re-queries all100 parents before reproduction.
                rr['mandatory_parent_cache_queries']=100*int(r['generation'])
                rr['population_member_queries']=r['total_attempts']-rr['mandatory_parent_cache_queries']
                rr['population_duplicate_queries']=rr['population_member_queries']-budget
                rr['population_duplicate_fraction']=1-budget/rr['population_member_queries']
                assert rr['population_duplicate_queries']>=0
                if budget in budgets:
                    terminal=s.read(folder/f'FINAL_{budget}.json')
                    rr['full_terminal_wrapper_wall_seconds']=terminal['wall_seconds']
                    rr['incremental_process_cpu_seconds']=terminal['incremental_cpu_seconds']
                rr['evaluations_since_improvement']=budget-rr['last_improvement_evaluations']
                rows.append(rr)
                contrib.append({k:rr[k] for k in ['mode','seed','budget','initial_best_loss_hr','initial_mean_loss_hr',
                    'initial_position_entropy','initial_hamming_fraction','initial_adjacency_overlap',
                    'ga_generated_gain_hr','inherited_initial_gain_vs_impact_hr','gain_vs_impact_hr']})
            qa.append(dict(mode=mode,seed=seed,cache_size=len(state['cache']),all_cached92_permutations_valid=True,
                first100_exact_initializer=True,empty_start_archive=True,no_external_lookup=True,
                exact_accounting=True,partial_boundary_archive_loss_hr=-state['state']['archive_score'],
                best_observed_loss_hr=-state['state']['best_seen'],strict_improvements=len(moves),
                cache_sha256=s.digest(folder/'CANDIDATES.npz')))
        a,b=initial_pair
        assert a['common_random_pool']==b['common_random_pool']
        assert a['post_initializer_rng_sha256']==b['post_initializer_rng_sha256']
        assert a['initial_sequences'][1:]==b['initial_sequences'][1:]
        assert a['initial_sequences']==a['common_random_pool']
    df=pd.DataFrame(rows).sort_values(['budget','seed','mode'])
    for mode in s.MODES: csv(mode+'_SEED_RESULTS.csv',df[df['mode']==mode])
    csv('INITIAL_POPULATION_AND_SEARCH_CONTRIBUTION.csv',contrib)
    comparisons=[]
    for budget,g in df.groupby('budget'):
        a=g[g['mode']==s.MODES[0]].set_index('seed').sort_index()
        b=g[g['mode']==s.MODES[1]].set_index('seed').sort_index()
        assert a.index.equals(b.index)
        comparisons.append(dict(budget=int(budget),**paired(a.loss_hr-b.loss_hr),
            pure_mean_hr=a.loss_hr.mean(),pure_median_hr=a.loss_hr.median(),pure_sd_hr=a.loss_hr.std(),
            seeded_mean_hr=b.loss_hr.mean(),seeded_median_hr=b.loss_hr.median(),seeded_sd_hr=b.loss_hr.std(),
            pure_high_quality_count=int(a.high_quality.sum()),seeded_high_quality_count=int(b.high_quality.sum()),
            pure_beats_frozen_count=int(a.beats_frozen.sum()),seeded_beats_frozen_count=int(b.beats_frozen.sum()),
            median_wall_ratio_pure_to_seeded=float((a.wall_seconds/b.wall_seconds).median()),
            median_attempt_ratio_pure_to_seeded=float((a.attempts/b.attempts).median()),
            pure_mean_ga_gain_hr=a.ga_generated_gain_hr.mean(),seeded_mean_ga_gain_hr=b.ga_generated_gain_hr.mean()))
    cp=pd.DataFrame(comparisons);csv('PAIRED_INITIALIZATION_COMPARISON.csv',cp)
    for (mode,seed),g in df.groupby(['mode','seed']):
        previous=None
        for _,r in g.sort_values('budget').iterrows():
            item=r.to_dict()
            item['incremental_distinct']=int(r.budget-(previous.budget if previous is not None else 0))
            item['marginal_gain_hr']=float(previous.loss_hr-r.loss_hr) if previous is not None else None
            item['incremental_attempts']=int(r.attempts-(previous.attempts if previous is not None else 0))
            item['incremental_wall_seconds']=float(r.wall_seconds-(previous.wall_seconds if previous is not None else 0))
            cost.append(item);previous=r
    csv('BUDGET_CONVERGENCE_AND_DUPLICATION.csv',cost)
    s.save(s.OUT/'ALL_SEQUENCE_IDENTITIES.json',seqs)
    s.save(s.OUT/'ALL_RUN_NUMERICAL_QA.json',dict(status='PASS',rows=qa,
        all20_shared_pool_rng_pairs_exact=True,optimizer_replicates=40,
        no_checkpoint_pseudoreplication=True,implementation_hash=s.digest(s.OUT/'study.py')))
    final=df.sort_values('budget').groupby(['mode','seed']).tail(1)
    terminals=df[df.budget.isin([100000,250000,500000])]
    s.save(s.OUT/'COMPUTATION_ACCOUNTING.json',dict(independent_main_searches=40,
        paired_optimizer_seeds=20,reserved_pairs=10 if extended else 0,
        new_search_distinct_objective_calls=int(final.distinct_evaluations.sum()),
        main_distinct_objective_calls=4000000,
        continuation_incremental_objective_calls=int(final.distinct_evaluations.sum())-4000000,
        individual_planning_state_kernel_evaluations=int(final.distinct_evaluations.sum())*64,
        total_attempts=int(final.attempts.sum()),mandatory_parent_cache_queries=int(final.mandatory_parent_cache_queries.sum()),
        population_member_duplicate_queries=int(final.population_duplicate_queries.sum()),
        summed_final_run_wall_seconds=float(final.full_terminal_wrapper_wall_seconds.sum()),
        summed_process_cpu_seconds=float(terminals.incremental_process_cpu_seconds.sum()),
        summed_objective_seconds=float(final.objective_seconds.sum()),
        engineering_mean_objective_calls=8000,engineering_compiled_individual_state_checks=256,
        engineering_production_individual_state_checks=12,engineering_synthetic_objective_calls=2000,
        main_worker_setup_mean_calls=s.read(s.OUT/'MAIN_EXECUTION.json')['worker_setup_calls'],
        extension_worker_setup_mean_calls=s.read(s.OUT/'EXTENSION_EXECUTION.json')['worker_setup_calls'] if extended else 0,
        cached_replay_physical_calls=0,loader_new_physical_samples=0,
        final_production_checks='Separately recorded in IMPORTANT_SEQUENCE_PRODUCTION_QA.json; never search-budget calls'))
    maincp=cp[cp.budget==100000].iloc[0]
    inside=maincp.simultaneous95_low_hr>=-s.MARGIN and maincp.simultaneous95_high_hr<=s.MARGIN
    extend=not inside or maincp.pure_high_quality_count<18
    if not s.lp(s.OUT/'EXTENSION_DECISION.json').exists():
        s.save(s.OUT/'EXTENSION_DECISION.json',dict(extend=bool(extend),
            registered_rule=s.read(s.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')['extension_rule'],
            evidence=maincp.to_dict(), simultaneous_inside_margin=bool(inside),
            pure_high_quality_at_least18=bool(maincp.pure_high_quality_count>=18),
            continuation_seeds=s.RESERVE if extend else []))
    print(cp[['budget','n','pure_mean_hr','seeded_mean_hr','mean_delta_hr','simultaneous95_low_hr','simultaneous95_high_hr','pure_high_quality_count']].to_string(index=False),flush=True)
    print('EXTENSION_REQUIRED',extend,flush=True)
    return df,cp


def historical():
    root=s.ROOT/'results/diagnostics/standalone_ils_final_method_20261010'
    names=['FAIR_GA_SEED_LEVEL_RESULTS.csv','HISTORICAL_GA_100K_500K_RECORDS.csv',
           'BUDGET_CONVERGENCE_AND_COST.csv','EXPERIMENT_DESIGN_AND_SEEDS.json',
           'ALL_MAIN_INITIALIZATION_AND_PERMUTATION_QA.json','HISTORICAL_GA_PROTOCOL_AUDIT.json']
    hashes={}
    for name in names:
        s.hydrate(root/name);hashes[str((root/name).relative_to(s.ROOT)).replace('\\','/')]=s.digest(root/name)
    df=pd.read_csv(s.lp(root/names[0])); assert df.seed.nunique()==20
    assert not set(df.seed)&set(s.MAIN)
    assert df[df.budget==100000].seed.nunique()==20
    assert df[df.budget==500000].seed.nunique()==10
    assert df.completed.all() and (df.budget==df.distinct_evaluations).all()
    assert s.read(root/'EXPERIMENT_DESIGN_AND_SEEDS.json')['ga_initialization'].startswith('exactly one Impact-first')
    assert s.read(root/'ALL_MAIN_INITIALIZATION_AND_PERMUTATION_QA.json')['status']=='PASS'
    csv('HISTORICAL_IMPACT_SEEDED_RECORDS_REUSED.csv',df)
    s.hydrate(root/'BUDGET_CONVERGENCE_AND_COST.csv')
    budget=pd.read_csv(s.lp(root/'BUDGET_CONVERGENCE_AND_COST.csv'))
    csv('HISTORICAL_CONVERGENCE_RECORDS_REUSED.csv',budget[budget.method=='GA'])
    s.save(s.OUT/'HISTORICAL_SOURCE_HASHES.json',hashes)


def production_qa(df):
    from la_grid.diagnostics.standalone_ils_analysis_20261010 import production
    from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
    from la_grid.revision.r1_equity_amendment_execute import execution_context
    k,impact,_=s.load_model(); context,_,_=execution_context(k.ids)
    selections=[]
    for budget in ([100000,500000] if 500000 in df.budget.values else [100000]):
        for mode in s.MODES:
            g=df[(df.budget==budget)&(df['mode']==mode)].sort_values(['loss_hr','seed'])
            for kind,pos in [('best',0),('median',len(g)//2)]:
                r=g.iloc[pos]
                saved=s.read(s.OUT/'runs'/f'{mode}_{int(r.seed)}'/f'FINAL_{budget}.json')
                selections.append(dict(kind=kind,**{key:saved[key] for key in ['mode','seed','budget','loss_hr','sequence','sequence_sha256']}))
    unique={r['sequence_sha256']:r for r in selections}
    rows=[];tick=time.perf_counter()
    for h,r in unique.items():
        exact=per_sample(k,r['sequence'])
        native=np.array([production(k,context,r['sequence'],i) for i in range(64)])
        assert np.max(abs(native-exact))<1e-8
        assert abs(native.mean()-r['loss_hr'])<1e-8
        rows.append(dict(**r,compiled64_losses=exact.tolist(),production64_losses=native.tolist(),
            max_absolute_error_hr=float(np.max(abs(native-exact))),native_mean_hr=native.mean(),
            all64_pass=True))
        print('PRODUCTION64_PASS',r['mode'],r['seed'],r['budget'],np.max(abs(native-exact)),flush=True)
    s.save(s.OUT/'IMPORTANT_SEQUENCE_PRODUCTION_QA.json',dict(status='PASS',selections=selections,
        unique_sequences=len(rows),production_individual_state_calls=len(rows)*64,
        compiled_individual_state_calls=len(rows)*64,wall_seconds=time.perf_counter()-tick,records=rows,
        no_new_physical_samples=True,formal_replacement=False))


def final_reports(df,cp):
    r=cp.sort_values('budget').iloc[-1]
    within=r.simultaneous95_low_hr>=-s.MARGIN and r.simultaneous95_high_hr<=s.MARGIN
    reliable=r.pure_high_quality_count>=.9*r.n
    costok=r.median_wall_ratio_pure_to_seeded<=1.25 and r.median_attempt_ratio_pure_to_seeded<=1.25
    choice=s.MODES[0] if within and reliable and costok else s.MODES[1]
    if 500000 in df.budget.values:
        reserve=df[df.seed.isin(s.RESERVE)].pivot(index='seed',columns=['budget','mode'],values='loss_hr')
        before=reserve[(100000,s.MODES[0])]-reserve[(100000,s.MODES[1])]
        after=reserve[(500000,s.MODES[0])]-reserve[(500000,s.MODES[1])]
        change=paired(after-before)
        budget_answer=(f"For the same ten reserved pairs, the initialization contrast changes from {before.mean():.9f}h at100k "
            f"to {after.mean():.9f}h at500k (change {change['mean_delta_hr']:.9f}h; pointwise95% interval "
            f"[{change['t95_low_hr']:.9f},{change['t95_high_hr']:.9f}]). "
            "This is a secondary within-seed budget contrast, not20 versus10 independent means. "
            +("Increasing budget reduces the absolute observed contrast, but the uncertainty and registered tolerance must still be considered." if abs(after.mean())<abs(before.mean()) else
               "Increasing budget does not reduce the absolute observed mean initialization contrast in these reserved pairs."))
    else:
        budget_answer='No higher-budget extension was warranted under the registered rule; the recorded20k/50k/100k changes bound the available budget conclusion.'
    directional=('The interval excludes zero in favor of the seeded control.' if r.simultaneous95_low_hr>0 else
        'The interval excludes zero in favor of pure random.' if r.simultaneous95_high_hr<0 else
        'A directional mean advantage is not established by this interval.')
    s.save(s.OUT/'FINAL_DECISION_MACHINE_READABLE.json',dict(recommendation=choice,
        final_budget=int(r.budget),criteria=dict(within_margin=bool(within),reliability=bool(reliable),cost=bool(costok)),
        evidence=r.to_dict(),formal_replacement=False))
    table=cp[['budget','n','pure_mean_hr','seeded_mean_hr','mean_delta_hr','simultaneous95_low_hr',
        'simultaneous95_high_hr','pure_wins','seeded_wins','pure_high_quality_count','seeded_high_quality_count']].to_markdown(index=False,floatfmt='.9f')
    init=df[df.budget==100000].groupby('mode').agg(initial_best_mean=('initial_best_loss_hr','mean'),
        final_mean=('loss_hr','mean'),ga_gain_mean=('ga_generated_gain_hr','mean'))
    base=f"""# Final GA Initialization Decision

**Recommend exactly one: `{choice}`.** This is an independently executable initialization recommendation, not a replacement of the validated formal sequence or configuration. All newly found chromosomes remain diagnostic.

## Completed Registered Evidence

Registration ca4d49e preceded main computation. Forty main searches comprise20 paired fresh seeds,4,000,000 distinct original64-state mean evaluations. The extension decision and its prespecified rule are in EXTENSION_DECISION.json. {'The first10 pairs continued their original RNG, population, archive and private cache to250k and500k;8,000,000 incremental evaluations, not new replicates.' if 500000 in df.budget.values else 'The extension was not needed under the registered rule.'} The5-endpoint Bonferroni family was reserved before data. Pointwise paired t and20,000 seed-block bootstrap intervals, medians, SDs, wins/ties, cost and all raw sequences are retained in accompanying tables. These intervals measure optimizer randomness conditional on64 planning states, not physical uncertainty.

Positive PURE_RANDOM-minus-IMPACT_SEEDED favors the seeded control:

{table}

Initial-population and subsequent-search contribution at100k:

{init.to_markdown(floatfmt='.9f')}

## Required Questions

A. A previously optimized chromosome is not a logical prerequisite: both new configurations explicitly contain none, and improvement after actual initialization is measured. This does not guarantee attaining the selected formal minimum in every seed. The historical93.06% fraction was continuation bookkeeping, not intrinsic GA capability.

B. Pure-random reliability is reported against the preregistered J<=32.998840773883h rule: {int(r.pure_high_quality_count)}/{int(r.n)} at{int(r.budget)}. {'It meets' if reliable else 'It does not meet'} the registered90% empirical rate. Exact formal-score wins are distinct from approaching within0.001h; they are not selected-minimum evidence of expected performance.

C. One Impact-first seed has final paired mean advantage {r.mean_delta_hr:.9f}h (positive favors seeded); simultaneous interval [{r.simultaneous95_low_hr:.9f},{r.simultaneous95_high_hr:.9f}]. {directional} Earlier-budget differences must be read separately, not pooled. The numerical0.001h margin is an engineering tolerance, not a physically validated policy threshold.

D. {budget_answer} Same-seed marginal gains and changes in initialization contrast are in BUDGET_CONVERGENCE_AND_DUPLICATION.csv and BUDGET_DIFFERENCE_REDUCTION.csv. Late plateau evidence applies only to tested trajectories, not global convergence.

E. Yes. Either configuration can be described as one standalone GA with no prior optimization stage. The recommended{choice} uses {'only100 random permutations' if choice==s.MODES[0] else 'one independently defined Impact-first order plus99 random permutations'}, no inherited optimized prior or engineered neighbors.

F. Adopt{choice} as the reporting recommendation, subject to separate author authorization before any formal change. {'The prospective numerical/reliability/cost gates support removing the heuristic seed.' if choice==s.MODES[0] else 'The pure-random option failed at least one prospective quality/uncertainty/cost gate; retain the simple Impact heuristic reference without claiming a unique optimum or universal superiority.'}

## Interpretation And Limitations

No independent-validation cohort, new physical realization, alternative objective, ILS, local refinement, hybrid or parameter grid enters this experiment. All non-initialization search mechanics,92 stations/318 edges/Core sources,57-crew directed-travel scheduler, physical samples, mapping and source gate remain fixed. Important best and median runs pass all64-state original production evaluations. Complete per-seed populations, changes, caches, state boundaries and objective timings are saved. Archive protection is not inherited-information injection. No seed was chosen for the extension on the basis of its result.

The formal candidate was selected using earlier optimization and need not equal a typical independent-search result. High-quality thresholds and practical comparisons are conditional numerical judgments, not new physical-validation claims. An interval crossing zero does not establish equivalence; meeting a numerical margin does not prove physical generalization. The recommendation is based on repeated seed quality and prespecified criteria, not the best single run.
"""
    s.lp(s.OUT/'FINAL_GA_INITIALIZATION_DECISION.md').write_text(base,encoding='utf-8',newline='\n')
    s.lp(s.OUT/'GA_INITIALIZATION_SCIENTIFIC_INTERPRETATION.md').write_text(
        '# Scientific Interpretation\n\n'+base.split('## Required Questions')[1],encoding='utf-8',newline='\n')
    text=f"""# Reviewer Defense And Publication Methods

## Proposed Main Methods

Restoration priorities were encoded as permutations of the92 substations. The initial population comprised {'100 independently sampled random permutations' if choice==s.MODES[0] else 'one deterministic population-Impact-first priority order and99 independently sampled random permutations'}. No previously optimized chromosome or engineered neighbor was supplied. Fitness was the negative mean population-weighted service-loss integral over the same64 planning realizations, evaluated with the original57-crew scheduler, directed travel and source-connected functionality constraint. The genetic algorithm used population100, ordered crossover with probability0.80, swap mutation with probability0.10, tournament selection of size3, and one surviving generational elite. Best-observed retention preserved every evaluated improvement, including a partial generation at the distinct-evaluation boundary. Adaptive mutation, restart and diversity replacement were disabled.

Independent searches used prespecified seeds2026103100-2026103119 and100,000 distinct scored permutations per seed. {'The first10 trajectories were prospectively reserved for continuation to250,000 and500,000 evaluations when the100k initialization-quality criterion remained unresolved.' if 500000 in df.budget.values else 'The preregistered continuation rule was not triggered.'} Parameter values were held at an earlier investigated reproducible reference setting; the present study varied initialization alone, not parameters. Reported finite-budget performance is not a global-optimality guarantee.

## Proposed Supplementary Text

Initialization sensitivity compared100 random chromosomes against replacement of position zero by Impact-first in a shared100-permutation pool. Both configurations entered reproduction with the same post-initializer RNG state and independent empty caches/archives. No prior optimized information was injected. At each declared budget, the replication unit was the optimizer seed, and differences were PURE_RANDOM minus IMPACT_SEEDED loss. We report paired t intervals,20,000 seed-block bootstrap intervals and familywise Bonferroni intervals for five declared endpoints. Reserved continuations are not additional independent searches. The prospective numerical tolerance was0.001 equivalent full-service hours (3.6s), a computational sensitivity criterion rather than an established practical policy threshold.

{table}

The recommended initialization is{choice}. Search contribution is final improvement beyond the best actually scored generation-zero chromosome; the Impact seed's initial advantage is not counted as new GA discovery. Initial populations,92-station orders and SHA-256 hashes, strict-improvement histories, duplicate queries, distinct work, generation boundaries, CPU/wall/objective times, RNG states and exact64-state production checks accompany the results. Cost includes diagnostic bookkeeping and checkpoint serialization; it is not a pure intrinsic-algorithm timing estimate. Seed uncertainty is conditional on fixed planning realizations and does not establish out-of-sample policy performance. Newly discovered sequences remain diagnostic.

## Reviewer Boundaries

The historical93.06% inherited-improvement figure described one continued selected search, not an estimate of independent GA efficacy. This experiment tests that distinction without using old validation outcomes. A heuristic seed is an independently computable initialization, not a previous optimization stage. Empty archive behavior and full reproduction parity are verified. Pointwise zero-crossing is not equivalence, minority exact-score wins are not reliability, and a plateau is not proof of a global optimum. Existing manuscript and formal strategy remain unchanged.
"""
    s.lp(s.OUT/'REVIEWER_DEFENSE_AND_METHODS_TEXT.md').write_text(text,encoding='utf-8',newline='\n')
    print('RECOMMEND',choice,flush=True)


def reduction(df):
    rows=[]
    for later in [50000,100000,250000,500000]:
        if later not in df.budget.values: continue
        earlier={50000:20000,100000:50000,250000:100000,500000:250000}[later]
        g=df[df.budget.isin([earlier,later])].pivot(index='seed',columns=['budget','mode'],values='loss_hr').dropna()
        before=g[(earlier,s.MODES[0])]-g[(earlier,s.MODES[1])]
        after=g[(later,s.MODES[0])]-g[(later,s.MODES[1])]
        rows.append(dict(earlier=earlier,later=later,change_estimand='later minus earlier initialization contrast',
            **paired(after-before),earlier_contrast_hr=before.mean(),later_contrast_hr=after.mean()))
    csv('BUDGET_DIFFERENCE_REDUCTION.csv',rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['summary','final']);a=p.parse_args()
    df,cp=summaries();historical();reduction(df)
    if a.phase=='final':production_qa(df);final_reports(df,cp)


if __name__=='__main__':main()
