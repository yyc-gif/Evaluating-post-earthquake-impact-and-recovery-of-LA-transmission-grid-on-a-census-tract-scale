"""Offline paired inference, discarded-child audit and unchanged production checks."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import pickle
import time
import zipfile
import study as s
import numpy as np
import pandas as pd


def tables():
    budgets=[b for b in (100000,250000,500000) if s.a.lp(s.OUT/f'RUN_RESULTS_{b}.csv').exists()]
    assert budgets and budgets[0]==100000
    if s.a.read(s.OUT/'CONTINUATION_DECISION.json')['execute']:
        assert budgets==[100000,250000,500000]
    return pd.concat([s.a.frame(s.OUT/f'RUN_RESULTS_{b}.csv') for b in budgets],ignore_index=True)


def checkpoint(mode,seed,budget):
    with zipfile.ZipFile(s.a.lp(s.OUT/f'raw_evidence/{mode}_{seed}_{budget}.zip')) as z:
        return pickle.loads(gzip.decompress(z.read('CHECKPOINT.pkl.gz')))


def summarize():
    df=tables();effects=[];descriptive=[];paired_rows=[];cost=[];elites=[];trajectory=[]
    for budget,g in df.groupby('budget'):
        pivot=g.pivot(index='seed',columns='mode',values='final_loss_hr')
        for family,label in ((1,'pointwise'),(2 if budget>100000 else 1,'registered_endpoint_family'),(3 if len(df.budget.unique())==3 else 1,'conservative_all_endpoints')):
            effect=s.a.paired(pivot.POST-pivot.LEGACY,family,2026121200)
            effects.append(dict(budget=int(budget),interval_scope=label,**effect))
        for mode,h in g.groupby('mode'):
            descriptive.append(dict(budget=int(budget),mode=mode,n=len(h),
                mean_hr=h.final_loss_hr.mean(),median_hr=h.final_loss_hr.median(),sd_hr=h.final_loss_hr.std(ddof=1),
                best_hr=h.final_loss_hr.min(),worst_hr=h.final_loss_hr.max(),
                mean_generations=h.completed_generations.mean(),mean_unique_population=h.final_unique_population.mean(),
                mean_position_entropy=h.final_position_entropy.mean(),mean_hamming=h.final_hamming.mean(),
                mean_wall_seconds=h.wall_seconds.mean(),mean_objective_seconds=h.objective_seconds.mean()))
        for seed,h in g.groupby('seed'):
            x=h.set_index('mode');legacy=x.loc['LEGACY'];post=x.loc['POST']
            row=dict(seed=int(seed),budget=int(budget),legacy_loss_hr=legacy.final_loss_hr,
                post_loss_hr=post.final_loss_hr,post_minus_legacy_hr=post.final_loss_hr-legacy.final_loss_hr,
                legacy_sequence_sha256=legacy.sequence_sha256,post_sequence_sha256=post.sequence_sha256)
            for field in ('completed_generations','generated_offspring','offspring_attempts','offspring_distinct',
                          'cache_hits','attempts','objective_seconds','wall_seconds','final_unique_population',
                          'final_position_entropy','final_hamming','strict_improvements'):
                row['legacy_'+field]=legacy[field];row['post_'+field]=post[field]
                row['delta_'+field]=post[field]-legacy[field]
            row['wall_ratio']=post.wall_seconds/legacy.wall_seconds
            paired_rows.append(row)
    for row in df.to_dict('records'):
        mode,seed,budget=row['mode'],int(row['seed']),int(row['budget'])
        c=checkpoint(mode,seed,budget);st=c['state'];n=100
        assert len(c['cache'])==st['expensive_calls']==budget
        assert st['offspring_new_distinct']==budget-n
        assert st['attempts']==n+st['generation']*n+st['offspring_attempts']
        assert st['completed_generations']==len(c['history'])-1
        assert max(c['cache'].values())==st['best_seen']
        assert all(len(p)==len(set(p))==92 for p in st['population'])
        if mode=='POST':
            assert len(st['elite_events'])==st['completed_generations']
            assert sum(st[k] for k in ('elite_insertions','elite_already_present','all_offspring_better'))==st['completed_generations']
        else:assert len(st['elite_events'])==st['generation']==st['elite_insertions']
        cost.append(dict(**row,offspring_duplicate_fraction=1-st['offspring_new_distinct']/st['offspring_attempts'],
            terminal_phase=st['phase'],scored_children_in_terminal_generation=st['next_index'],
            final_population_metrics_scope='Last fully scored and finalized generation; incomplete proposal not treated as survivor population',
            scoring_state_kernels=64*budget,initialization_distinct=n,
            finalization_pending=not st['elitism_finalized']))
        events=st['elite_events']
        elites.append(dict(mode=mode,seed=seed,budget=budget,completed_generations=st['completed_generations'],
            generated_generations=st['generation'],elite_insertions=st['elite_insertions'],
            complete_generation_insertions=sum(ev['generation']<=st['completed_generations'] and ev['reason'] in ('inserted','legacy_pre_evaluation_overwrite') for ev in events),
            already_present=st['elite_already_present'],all_offspring_better=st['all_offspring_better'],
            incomplete_generation_pre_evaluation_insertions=sum(ev['generation']>st['completed_generations'] for ev in events),
            last_generated_better_than_previous=sum(ev.get('last_generated_better_than_previous',False) for ev in events),
            retained_previous_elite='Current population only; passive global archive never injected'))
        # Use each seed's longest archive once; earlier points are repeated observations.
        if budget==int(df[(df['mode']==mode)&(df.seed==seed)].budget.max()):
            for b in c['budget_rows']:
                trajectory.append(dict(mode=mode,seed=seed,distinct_evaluations=b['distinct_evaluations'],
                    loss_hr=b['best_service_loss_hr'],attempts=b['total_attempts'],
                    objective_seconds=b['objective_seconds'],elapsed_seconds=b['elapsed_seconds'],
                    sequence_sha256=b['sequence_sha256'],generation=b['generation']))
    assert len({(r['mode'],r['seed'],r['distinct_evaluations']) for r in trajectory})==len(trajectory)
    s.csv('PAIRED_SEED_LEVEL_RESULTS.csv',paired_rows)
    s.csv('PAIRED_OBJECTIVE_EFFECTS.csv',effects)
    s.csv('METHOD_DESCRIPTIVE_STATISTICS.csv',descriptive)
    s.csv('BUDGET_AND_COMPUTATIONAL_COST.csv',cost)
    s.csv('ELITE_REPLACEMENT_EVENT_COUNTS.csv',elites)
    s.csv('CONVERGENCE_COMPARISON.csv',trajectory)
    marginal=[]
    for (mode,seed),g in df.groupby(['mode','seed']):
        records=g.sort_values('budget').to_dict('records')
        for previous,current in zip(records,records[1:]):
            marginal.append(dict(mode=mode,seed=int(seed),from_budget=int(previous['budget']),
                to_budget=int(current['budget']),gain_hr=previous['final_loss_hr']-current['final_loss_hr'],
                new_distinct=current['distinct']-previous['distinct'],
                additional_attempts=current['attempts']-previous['attempts'],
                additional_generations=current['completed_generations']-previous['completed_generations'],
                additional_objective_seconds=current['objective_seconds']-previous['objective_seconds'],
                additional_wall_seconds=current['wall_seconds']-previous['wall_seconds'],
                incremental_phase_wall_seconds=current['incremental_wall_seconds'],
                new_independent_run=False))
    if marginal:s.csv('BUDGET_EXTENSION_MARGINAL_GAINS.csv',marginal)
    summary=[]
    for (mode,budget),g in pd.DataFrame(trajectory).groupby(['mode','distinct_evaluations']):
        summary.append(dict(mode=mode,distinct_evaluations=int(budget),n=len(g),mean_loss_hr=g.loss_hr.mean(),
                            median_loss_hr=g.loss_hr.median(),sd_loss_hr=g.loss_hr.std(ddof=1)))
    s.csv('CONVERGENCE_SUMMARY.csv',summary)
    print('SUMMARY_PASS',len(df),flush=True)


def shadow():
    df=tables();kernel,_,_=s.a.load_study().load_model()
    observed={};events=[];new_calls=0;tick=time.perf_counter();scoring_seconds=0.
    for mode in ('LEGACY','POST'):
        for seed,h in df[df['mode']==mode].groupby('seed'):
            budget=int(h.budget.max());c=checkpoint(mode,int(seed),budget)
            for key,value in c['cache'].items():
                if key in observed:assert observed[key]==value
                else:observed[key]=value
    # This independent map is not the optimizer cache and is never re-inserted.
    score_store={};counts=[];post_detail=[]
    for seed,h in df[df['mode']=='LEGACY'].groupby('seed'):
        maxbudget=int(h.budget.max());c=checkpoint('LEGACY',int(seed),maxbudget)
        for ev in c['state']['elite_events']:
            key=ev['discarded_key']
            if key in observed:fit=observed[key];origin='observed_in_completed_search_cache'
            elif key in score_store:fit=score_store[key];origin='separate_audit_reuse'
            else:
                seq=tuple(kernel.ids[i] for i in key);start=time.perf_counter()
                fit=float(kernel.score(seq));scoring_seconds+=time.perf_counter()-start
                score_store[key]=fit;new_calls+=1;origin='new_separate_audit_score'
            previous=ev['previous_fitness'];proposal=ev.get('discarded_fitness_at_proposal')
            if proposal is not None:assert proposal==fit
            events.append(dict(mode='LEGACY',seed=int(seed),generation=ev['generation'],
                maximum_archived_budget=maxbudget,previous_elite_loss_hr=-previous,discarded_child_loss_hr=-fit,
                child_minus_previous_loss_hr=previous-fit,child_strictly_better=fit>previous,
                known_at_proposal=ev['discarded_already_cached'],score_origin=origin,
                child_key_hex=key.hex(),child_sequence_sha256=s.a.identity(tuple(kernel.ids[i] for i in key)),
                complete_at_terminal=ev['generation']<=c['state']['completed_generations'],
                measurement_scope='Post-search observation, never optimizer feedback'))
        print('SHADOW_COMPLETE',seed,len(events),new_calls,flush=True)
    s.csv('OFFSPRING_DISCARD_EVENT_DETAIL.csv',events)
    evdf=pd.DataFrame(events)
    for row in df.to_dict('records'):
        mode,seed,budget=row['mode'],int(row['seed']),int(row['budget'])
        c=checkpoint(mode,seed,budget);st=c['state']
        if mode=='LEGACY':
            e=evdf[(evdf.seed==seed)&(evdf.generation<=st['generation'])]
            better=int(e.child_strictly_better.sum());known=int(e.known_at_proposal.sum())
            counts.append(dict(mode=mode,seed=seed,budget=budget,overwritten_children=len(e),
                overwritten_better_than_previous=better,fraction_better_than_previous=better/len(e),
                overwritten_known_at_proposal=known,unscored_at_proposal=len(e)-known,
                overwritten_best_improvement_hr=float((-e.child_minus_previous_loss_hr).max()),
                completed_generation_events=int((e.generation<=st['completed_generations']).sum()),
                partial_generation_events=int((e.generation>st['completed_generations']).sum()),
                analyzed_after_search=True))
        else:
            inserted=[ev for ev in st['elite_events'] if ev['reason']=='inserted']
            assert all(ev['discarded_fitness']<=ev['previous_fitness'] for ev in inserted)
            if budget==int(df[(df['mode']==mode)&(df.seed==seed)].budget.max()):
                for ev in st['elite_events']:
                    child=ev.get('discarded_key')
                    if child is not None:assert c['cache'][child]==ev['discarded_fitness']
                    post_detail.append(dict(seed=seed,generation=ev['generation'],maximum_archived_budget=budget,
                        reason=ev['reason'],previous_elite_loss_hr=-ev['previous_fitness'],
                        last_generated_loss_hr=-ev['last_generated_fitness'],
                        last_generated_better_than_previous=ev['last_generated_better_than_previous'],
                        discarded_index=ev.get('index'),
                        discarded_loss_hr=-ev['discarded_fitness'] if child is not None else None,
                        discarded_key_hex=child.hex() if child is not None else None,
                        discarded_score_retained_in_cache=child in c['cache'] if child is not None else None))
            counts.append(dict(mode=mode,seed=seed,budget=budget,overwritten_children=len(inserted),
                overwritten_better_than_previous=0,fraction_better_than_previous=0.,
                overwritten_known_at_proposal=len(inserted),unscored_at_proposal=0,
                last_generated_better_than_previous=sum(ev['last_generated_better_than_previous'] for ev in st['elite_events']),
                completed_generation_events=len(st['elite_events']),partial_generation_events=0,
                analyzed_after_search=True))
    s.csv('OFFSPRING_DISCARD_ANALYSIS.csv',counts)
    s.csv('POST_ELITE_EVENT_DETAIL.csv',post_detail)
    s.csv('SEPARATE_AUDIT_SCORE_CACHE.csv',[dict(key_hex=k.hex(),fitness=v,loss_hr=-v) for k,v in score_store.items()])
    s.save('SHADOW_AUDIT_ACCOUNTING.json',dict(status='PASS',separate_distinct_objective_calls=new_calls,
        separate_planning_state_kernels=64*new_calls,objective_seconds=scoring_seconds,
        wall_seconds=time.perf_counter()-tick,optimizer_budget_affected=False,
        caches_or_archives_modified=False,new_physical_samples=0,
        repeated_budget_prefixes_not_independent=True,
        cached_evaluations_reused=len(observed),scope='All legacy generated discard events, including a possible terminal partial generation; complete-generation subset identified. Cross-run cached values may establish retrospective fitness, not foreknowledge.'))


def production():
    from la_grid.diagnostics.ga_search_budget_sensitivity import per_sample
    from la_grid.diagnostics.standalone_ils_analysis_20261010 import production as native
    from la_grid.revision.r1_equity_amendment_execute import execution_context
    df=tables();chosen=[]
    for (mode,budget),g in df.groupby(['mode','budget']):
        h=g.sort_values(['final_loss_hr','seed'])
        for role,index in (('best',0),('lower_median',(len(h)-1)//2)):
            row=h.iloc[index].to_dict();row['role']=role;chosen.append(row)
    bestpost=df[df['mode']=='POST'].sort_values(['final_loss_hr','budget','seed']).iloc[0].to_dict()
    bestpost['role']='single_POST_development_candidate';chosen.append(bestpost)
    kernel,_,model=s.a.load_study().load_model();ctx,_,context_hashes=execution_context(kernel.ids)
    s.save('FIXED_PLANNING_MODEL_IDENTITY.json',dict(station_ids_in_cache_byte_index_order=list(kernel.ids),
        station_id_order_sha256=s.a.identity(kernel.ids),physical_realizations=64,
        horizon_hr=kernel.horizon,population_resolved_mass=kernel.total_mass,
        production_context_identity=context_hashes,model=model,
        cache_encoding='Each92-byte key is a permutation of0..91 indexing station_ids_in_cache_byte_index_order; all tuples in state are station ID strings',
        physical_sample_generation=False))
    records=[];realization_rows=[];checked={}
    for row in chosen:
        mode,seed,budget=row['mode'],int(row['seed']),int(row['budget'])
        run=s.a.read(s.OUT/f'runs/{mode}_{seed}_{budget}.json');seq=tuple(run['sequence']);identity=s.a.identity(seq)
        assert len(seq)==len(set(seq))==92 and set(seq)==set(kernel.ids) and identity==row['sequence_sha256']
        if identity not in checked:
            exact=per_sample(kernel,seq);actual=np.array([native(kernel,ctx,seq,i) for i in range(64)])
            assert np.max(np.abs(exact-actual))<1e-8
            assert abs(actual.mean()-row['final_loss_hr'])<1e-8
            checked[identity]=(actual,np.max(np.abs(exact-actual)))
        actual,error=checked[identity]
        record=dict(mode=mode,seed=seed,budget=budget,role=row['role'],sequence=list(seq),sequence_sha256=identity,
            planning_loss_hr=actual.mean(),search_loss_hr=row['final_loss_hr'],max_native_kernel_difference_hr=error,
            physical_realizations=64,status='PASS',formal_candidate_promoted=False,
            raw_archive=str(s.OUT/f'raw_evidence/{mode}_{seed}_{budget}.zip'),
            raw_archive_sha256=s.a.sha(s.OUT/f'raw_evidence/{mode}_{seed}_{budget}.zip'))
        records.append(record)
        for i,value in enumerate(actual):realization_rows.append(dict(mode=mode,seed=seed,budget=budget,role=row['role'],realization=i,native_loss_hr=value,sequence_sha256=identity))
        print('NATIVE_QA_PASS',mode,seed,budget,flush=True)
    s.save('IMPORTANT_CANDIDATE_PRODUCTION_QA.json',dict(status='PASS',important_candidates=records,
        unique_sequences_checked=len(checked),native_fixed_sample_evaluations=64*len(checked),
        new_physical_samples=0,independent_validation_used=False,original_scientific_modules_from=str(s.BASE/'src')))
    s.csv('IMPORTANT_CANDIDATE_PLANNING_REALIZATIONS.csv',realization_rows)
    candidate=next(r for r in records if r['role']=='single_POST_development_candidate')
    s.save('POST_DEVELOPMENT_CANDIDATE_FREEZE.json',dict(**candidate,label='Diagnostic development candidate only',
        selection_rule=s.a.read(s.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')['candidate_rule'],
        registered_design_commit='50d7318',parameters=s.a.read(s.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')['configuration']))


def decision():
    df=tables();effects=s.a.frame(s.OUT/'PAIRED_OBJECTIVE_EFFECTS.csv')
    endpoints=effects[effects.interval_scope=='registered_endpoint_family']
    paired=s.a.frame(s.OUT/'PAIRED_SEED_LEVEL_RESULTS.csv')
    costs={int(b):float(g.wall_ratio.median()) for b,g in paired.groupby('budget')}
    adverse=bool((endpoints.simultaneous95_low_hr>0).any())
    adopt=not adverse and all(r<=1.5 for r in costs.values())
    recommendation='ADOPT POST-EVALUATION WORST-OFFSPRING ELITISM' if adopt else 'RETAIN LEGACY ELITISM'
    discard=s.a.frame(s.OUT/'OFFSPRING_DISCARD_ANALYSIS.csv')
    elites=s.a.frame(s.OUT/'ELITE_REPLACEMENT_EVENT_COUNTS.csv')
    shadow=s.a.read(s.OUT/'SHADOW_AUDIT_ACCOUNTING.json')
    candidate=s.a.read(s.OUT/'POST_DEVELOPMENT_CANDIDATE_FREEZE.json')
    descriptive=s.a.frame(s.OUT/'METHOD_DESCRIPTIVE_STATISTICS.csv')
    text=f'# Final elitism decision\n\n**{recommendation}**\n\n'
    text+='The source retains legacy as the backward-compatible default. Adoption, if recommended, applies to a future explicitly configured scientific workflow, not automatic replacement of its already validated sequence. Both modes remain independently executable.\n\n'
    text+='## Empirical endpoint results\n\nNegative POST-minus-LEGACY means lower loss. Replication is paired optimizer seed, not generations or budget checkpoints.\n\n'
    for r in endpoints.to_dict('records'):
        b=int(r['budget']);h=descriptive[descriptive.budget==b].set_index('mode');p=paired[paired.budget==b]
        text+=f"- {b:,} distinct: n={int(r['n'])}; legacy mean/median/SD {h.loc['LEGACY','mean_hr']:.9f}/{h.loc['LEGACY','median_hr']:.9f}/{h.loc['LEGACY','sd_hr']:.9f} h; POST {h.loc['POST','mean_hr']:.9f}/{h.loc['POST','median_hr']:.9f}/{h.loc['POST','sd_hr']:.9f} h. Paired mean delta {r['mean_delta_hr']:+.9f} h; adjusted95% [{r['simultaneous95_low_hr']:+.9f},{r['simultaneous95_high_hr']:+.9f}] h; wins/losses/ties {int(r['wins'])}/{int(r['losses'])}/{int(r['ties'])}. Median wall ratio {costs[b]:.4f}.\n"
        text+=f"  Mean completed-generation delta {p.delta_completed_generations.mean():+.2f}; entropy delta {p.delta_final_position_entropy.mean():+.6f}; unique-survivor delta {p.delta_final_unique_population.mean():+.2f}; offspring-attempt delta {p.delta_offspring_attempts.mean():+.2f}.\n"
    text+='\nPrimary100k is one predeclared contrast. The250k/500k family, if executed, has two endpoints with Bonferroni simultaneous intervals; an all-three-endpoint conservative family is additionally provided. Paired bootstrap intervals and complete best/worst statistics are in the companion tables. A zero-crossing interval is not equivalence. All seeds and negative outcomes are retained.\n\n'
    text+='## Mechanism and nine requested answers\n\n'
    main=discard[(discard.budget==100000)&(discard['mode']=='LEGACY')]
    better=int(main.overwritten_better_than_previous.sum());total=int(main.overwritten_children.sum())
    post=discard[(discard.budget==100000)&(discard['mode']=='POST')]
    pe=elites[(elites.budget==100000)&(elites['mode']=='POST')]
    text+=f'1. At100k, legacy overwrote {better}/{total} generated last children ({100*better/total:.4f}%) that retrospective unchanged fitness shows were strictly better than the previous elite. {int(main.unscored_at_proposal.sum())} were unscored at the moment of replacement. Complete versus terminal-partial events are separately recorded. These are events, not independent trials.\n'
    text+=f'2. POST removes only a scored worst child no better than the previous elite: {int(post.overwritten_better_than_previous.sum())} stronger discarded children. At100k, insertion/presence/all-better counts are {int(pe.elite_insertions.sum())}/{int(pe.already_present.sum())}/{int(pe.all_offspring_better.sum())}. The last-child opportunity is preserved; every valid observation still enters best-observed.\n'
    text+='3. The matched algorithm comparison measures the aggregate later-search consequence; it does not identify any individual retained child as the cause. Selection and sequence trajectories may diverge after survival differs. Random-draw rules remain unchanged; the stream can remain matched at the same operator generation, while distinct-budget endpoints can stop at different generations/RNG states. Endpoint intervals determine evidence for advantage; engineering correctness alone cannot prove it.\n'
    text+='4. Paired survivor uniqueness, normalized position entropy and positional Hamming are reported above and per seed. Metrics refer to the last completed population, never an unfinished proposal. Diversity is descriptive rather than proof of search quality.\n'
    text+=f'5. Both consume exactly the same distinct objective budget, including100 initial chromosomes. Scoring the last child does not add expensive calls beyond that ceiling: it redistributes work and may reduce completed generations. Attempted/cache queries and wall/objective time are separate. Retrospective discard auditing added {shadow["separate_distinct_objective_calls"]:,} separate fixed-planning calls ({shadow["separate_planning_state_kernels"]:,} state kernels), excluded from all optimizer budgets. Median wall ratios above are operational observations from the same12-worker machine, not platform-independent speed claims.\n'
    text+='6. Paired improvement frequencies and uncertainty above answer consistency. No assertion is made that every run improves or reaches the same sequence.\n'
    text+='7. The first ten prospectively reserved states, not freshly restarted searches, supply higher-budget evidence when the registered gate allows continuation. Budget checkpoints share seeds and are not new replication. Marginal gains and incremental costs are recorded independently. No further favorable-result extension is permitted.\n'
    text+='8. POST remains a simple permutation GA: the same100random initialization, OX.80, Swap.10, Tournament3 and one current-generation elite, with conditional deterministic survivor replacement and a passive output archive. No local search, adaptation, restarts or incumbent injection.\n'
    text+=f'9. Decision follows the prospective rule: wholly adverse adjusted endpoint={adverse}; all median wall ratios<=1.5={all(r<=1.5 for r in costs.values())}. Engineering preference and empirical superiority are kept separate. This yields **{recommendation}**.\n\n'
    text+='## Candidate boundary\n\n'
    text+=f"Best POST development sequence: seed {candidate['seed']}, {candidate['budget']:,} distinct, native64-planning loss {candidate['planning_loss_hr']:.12f} h, SHA256 `{candidate['sequence_sha256']}`. Full92-station order, state lineage and native per-realization results are archived. Old frozen legacy loss32.99552241352315 h and SHA edc4ad19f61a6d89d83532c1c92f353243b5d9e7b475c1ad99873227bbfeb99a remain unchanged. Their prior2,000-sample validation is not transferred.\n\n"
    text+='No physical sampling, old independent-validation outcome analysis, manuscript, official figure, Stage7, source-gate, scheduler, objective, travel/crew, mapping or repair-duration changes occurred. A proposed validation plan is readiness only and cannot be executed without authorization.\n'
    s.md('FINAL_ELITISM_DECISION.md',text)
    s.save('FINAL_DECISION_NUMERICAL_RECORD.json',dict(recommendation=recommendation,adverse_adjusted_endpoint=adverse,
        median_wall_ratios=costs,registered_rule=s.a.read(s.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')['decision_rule'],
        empirical_superiority_at_budgets=[int(r['budget']) for r in endpoints.to_dict('records') if r['simultaneous95_high_hr']<0],
        no_equivalence_claim=True,candidate_sha256=candidate['sequence_sha256'],formal_candidate_replaced=False))
    s.save('PROPOSED_INDEPENDENT_VALIDATION_SPECIFICATION.json',dict(status='NOT_EXECUTED_REQUIRES_EXPLICIT_AUTHORIZATION',
        recommended_algorithm=recommendation,diagnostic_candidate=candidate,
        proposed_count=2000,paired_strategies=['Frozen_POST_development_candidate','Unchanged_formal_GA','Impact-first'],
        physics='Reuse existing authorized physical sampler and production evaluation/statistical path unchanged',
        sample_seed_allocation='Allocate and record unused seeds only after author authorization; disjoint from all previous planning/validation cohorts',
        analysis='Prespecify paired mean original population-weighted cumulative service loss; descriptive hospital-associated loss, recovery curves and equity remain secondary, no tuning or reselection',
        frozen_before_sampling=True,old_validation_not_transferred=True,new_samples_generated=0))
    print('DECISION',recommendation,flush=True)


def final_qa():
    before=s.a.read(s.OUT/'PRESERVATION_BASELINE.json');after=s.preservation()
    assert before==after,'Protected scientific checkout/index/file identity changed'
    design=s.a.read(s.OUT/'EXPERIMENT_DESIGN_AND_SEEDS.json')
    for path,digest in design['source_hashes'].items():assert s.a.sha(path)==digest
    paths=[];members=0
    for p in s.a.lp(s.OUT/'raw_evidence').glob('*.manifest.json'):
        manifest=json.loads(p.read_text());archive=p.with_name(p.name.replace('.manifest.json','.zip'))
        assert s.a.sha(archive)==manifest['zip_sha256']
        with zipfile.ZipFile(archive) as z:
            for row in manifest['members']:
                assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256'];members+=1
        paths.append(str(archive))
    frame=tables();assert len(frame)==(80 if design and s.a.read(s.OUT/'CONTINUATION_DECISION.json')['execute'] else 40)
    s.save('REPRODUCIBILITY_AND_PRESERVATION_QA.json',dict(status='PASS',protected_before_after_equal=True,
        protected_scientific_files=950,original_staged_items=before['staged_count'],
        previous_parameter_package_hashes_preserved=True,source_frozen_hashes_match=True,
        raw_archives=len(paths),raw_member_hashes_verified=members,
        fresh_main_runs=40,continued_endpoint_records=len(frame)-40,
        distinct_optimizer_seed_pairs=20,independent_validation_outcomes_loaded=False,
        new_physical_samples=0,formal_candidate_modified=False,
        pre_execution_design_commit='50d7318',pre_execution_source_normalization_commit='e4cef14',
        final_original_state=after))
    s.md('REPRODUCIBLE_COMMANDS.md','''# Commands and boundaries

Run from this isolated worktree with the Anaconda interpreter, OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1 and PYTHONDONTWRITEBYTECODE=1. `study.py engineering`, then `setup`, then `baseline` precede the registered commit. The20paired100k studies use `study.py main`. `study.py continuation` freezes the gate; only if execute=true use `study.py 250k`, then `study.py 500k` (same saved states).

After all searches: `analysis.py summarize`, `shadow`, `production`, `decision`, `qa`. `publication.py manifest` records every scoped payload; commit and push before `publication.py remote`. Commit the remote-byte receipt separately and verify final remote HEAD. The original cached legacy replay is100k logical lookups, not new physical draws or fresh training samples. It reproduces the authoritative seed rather than searching for a favorable baseline.

All raw score maps and RNG states are preserved inside per-seed/budget ZIPs. Budget continuation restores CHECKPOINT.pkl.gz in the same ignored runtime directory. If restoring onto another machine, recover the original scientific repository checkout identified by frozen source hashes, unpack the previous endpoint into that directory, and run the next fixed budget. No sequence from a previous strategy or independent validation is injected.

Direct API use: `run_search(..., elitism_mode=POST_EVALUATION_WORST_OFFSPRING_ELITISM)` versus `LEGACY_LAST_POSITION_ELITISM`; scientific objective remains injected unchanged. Root source is the authorized diagnostic engine only. Historical r1_ga_revision.py is not edited.

Windows testing uses short `_elitism_tmp`; the longer pytest fixture prefix exceeds MAX_PATH. Scientific/payload paths use the existing extended-length path helper. Temporary test and runtime files are not staged.
''')
    print('PRESERVATION_AND_RAW_QA_PASS',len(paths),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['summarize','shadow','production','decision','qa']);args=parser.parse_args()
    {'summarize':summarize,'shadow':shadow,'production':production,'decision':decision,'qa':final_qa}[args.phase]()
