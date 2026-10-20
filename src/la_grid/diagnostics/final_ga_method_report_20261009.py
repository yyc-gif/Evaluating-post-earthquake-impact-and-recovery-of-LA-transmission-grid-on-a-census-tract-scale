"""Final GA specification, bounded attribution and validation preparation."""
from pathlib import Path
from dataclasses import asdict
import hashlib,json,platform,random,sys,re,subprocess
import numpy as np,pandas as pd,numba
from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics.final_ga_method_20261009 import OUT,PRIOR,BASE,dump
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import load
from la_grid.diagnostics.ga_variant_engine import Variant,initialize
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context
IMPACT=33.57830255999924;PREVIOUS=33.03813174326729
FINAL=Variant(mutation=.1,elites=1,initialization='quality_mix',mutation_operator='swap')
def rel(p):return Path(p).relative_to(R).as_posix()
def tab(d):return d.replace({np.nan:'not applicable'}).to_markdown(index=False,floatfmt='.9f')
def md(name,text):
 text=re.sub(r'\b(of|all|each|these|same|the|at|over|among|only|seed|generation|population|rows|StageA|StageB|before|after|across|with|for|fixed|per)(?=\d)',r'\1 ',text)
 text=text.replace('2,0002pc50','2,000 2pc50')
 text=re.sub(r'\b(unchanged|saved|ordered|empirical|post|original|previously inspected|same|received|the|any|all|by|approximate|fixed|mean|median|population|generation|Bernoulli|record|records|append|remaining|prior-best|draw|samples|generating|is|and|to|budget|mutation|final|add|another|cost|gives|equal|tolerance|approximately|form|candidate|SD|best|worst|mean|on|All|are|The|those|its|heterogeneous|bound)(?=\d)',r'\1 ',text)
 text=re.sub(r'(?<=\d)(?=(?:h\b|s\b|queries\b|slots\b|seeds\b|parents\b|children\b|neighbors\b|samples\b|realizations\b|permutations\b))',' ',text)
 for a,b in [('not the4m','not the 4m'),('total is4','total is 4'),('remaining67','remaining 67'),('bound134','bound 134'),('from1','from 1'),('the480','the 480'),('the64','the 64'),('full92','full 92'),('StageA','Stage A'),('StageB','Stage B'),('N2000','N = 2000'),('inspected1000','inspected 1,000'),('every64','every 64')]:text=text.replace(a,b)
 for a,b in [('20,000-resample95%','20,000-resample 95%'),('approximate95%','approximate 95%'),('median0.','median 0.'),('seeds42','seeds 42'),('samples and1000','samples and 1,000'),('original64/1000','original 64/1,000'),('samples;47','samples; 47')]:text=text.replace(a,b)
 (OUT/name).write_text(text.strip()+'\n',encoding='utf-8')
def record(p):return json.loads((p/'RUN.json').read_text())

def attribution():
 methods={'A_original':(PRIOR/'screen','original_p100'),'B_quality_original':(PRIOR/'screen','p100_quality_mix'),
 'C_quality_elite_inversion_m02':(OUT/'controlled_comparisons','C_quality_elite_inversion_m02'),
 'D_quality_elite_swap_m02':(OUT/'controlled_comparisons','D_quality_elite_swap_m02'),
 'D_final_swap_m01':(PRIOR/'operators','operator_swap'),'bridge_inversion_m01':(PRIOR/'operators','operator_inversion')}
 rows=[]
 for method,(parent,cid) in methods.items():
  for seed in range(42,47):
   f=parent/f'{cid}_s{seed}';q=record(f);h=pd.read_csv(f/'GENERATION_DIAGNOSTICS.csv');g0=h[h.generation.eq(0)].iloc[0]
   b=pd.read_csv(f/'BUDGET_CHECKPOINTS.csv');z=b[b.distinct_evaluations.eq(50000)].iloc[0]
   initial=float(g0.population_best_service_loss_hr);final=float(z.best_service_loss_hr)
   rows.append(dict(method=method,seed=seed,budget=50000,initial_best_generation0_hr=initial,
    initial_gain_vs_impact_hr=IMPACT-initial,postinitialization_improvement_hr=initial-final,
    final_best_hr=final,total_improvement_vs_impact_hr=IMPACT-final,prior_best_hr=PREVIOUS,
    strictly_improved_prior_best=final<PREVIOUS,initial_distinct_queries=int(g0.unique_candidates_evaluated),
    distinct_expensive_evaluations=50000,total_attempts=int(z.total_attempts),actual_generation=int(z.generation),
    wall_seconds=float(z.elapsed_seconds),process_cpu_seconds=q.get('process_cpu_seconds'),
    cpu_status='recorded' if 'process_cpu_seconds' in q else 'NOT_RECORDED',
    source_run=rel(f/'RUN.json'),source_commit=BASE if parent in [PRIOR/'screen',PRIOR/'operators'] else 'THIS_DIAGNOSTIC_COMMIT',
    source_run_sha256=old.digest(f/'RUN.json'),source_config=json.dumps(q['config'],sort_keys=True),
    warm_start_development_cost_included_in_current_budget=False,setup_validation_objective_calls=8,new_calls_this_round=50000 if parent==OUT/'controlled_comparisons' else 0))
 d=pd.DataFrame(rows);d.to_csv(OUT/'GA_INITIALIZATION_VS_SEARCH_IMPROVEMENT.csv',index=False)
 s=d.groupby('method').agg(seeds=('seed','size'),initial_mean_hr=('initial_best_generation0_hr','mean'),initial_sd_hr=('initial_best_generation0_hr','std'),postinitialization_mean_gain_hr=('postinitialization_improvement_hr','mean'),final_mean_hr=('final_best_hr','mean'),final_sd_hr=('final_best_hr','std'),improve_prior_fraction=('strictly_improved_prior_best','mean'),mean_attempts=('total_attempts','mean')).reset_index()
 s.to_csv(OUT/'INITIALIZATION_COMPARISON_SUMMARY.csv',index=False);effects=[]
 for a,b,label in [('A_original','B_quality_original','Initialization only'),('B_quality_original','C_quality_elite_inversion_m02','One elite only'),('C_quality_elite_inversion_m02','D_quality_elite_swap_m02','Swap versus inversion at mutation0.20'),('D_quality_elite_swap_m02','D_final_swap_m01','Swap rate0.10 versus0.20'),('bridge_inversion_m01','D_final_swap_m01','Swap versus inversion at rate0.10')]:
  x=d[d.method.eq(a)].set_index('seed');y=d[d.method.eq(b)].set_index('seed');v=y.final_best_hr-x.final_best_hr
  effects.append(dict(comparison=label,seeds=5,mean_final_change_hr=v.mean(),sd_seed_change_hr=v.std(),initial_mean_change_hr=(y.initial_best_generation0_hr-x.initial_best_generation0_hr).mean(),search_gain_change_hr=(y.postinitialization_improvement_hr-x.postinitialization_improvement_hr).mean()))
 e=pd.DataFrame(effects);e.to_csv(OUT/'CONTROLLED_ATTRIBUTION_EFFECTS.csv',index=False)
 return d,s,e

def budgets():
 rows=[]
 for seed in range(42,47):
  f=PRIOR/'budget_extension'/f'operator_swap_s{seed}';q=record(f);b=pd.read_csv(f/'BUDGET_CHECKPOINTS.csv')
  moves=json.loads((f/'STRICT_IMPROVEMENTS.json').read_text());h=pd.read_csv(f/'GENERATION_DIAGNOSTICS.csv');g0=h[h.generation.eq(0)].iloc[0];last=None
  for _,z in b.sort_values('distinct_evaluations').iterrows():
   n=int(z.distinct_evaluations);interval=[] if last is None else [x for x in moves if last['n']<x['distinct_evaluations']<=n]
   rows.append(dict(seed=seed,distinct_evaluations=n,total_attempts=int(z.total_attempts),actual_generation=int(z.generation),fully_completed_generation=int(h.loc[h.unique_candidates_evaluated.le(n),'generation'].max()),best_hr=float(z.best_service_loss_hr),initial_best_hr=float(g0.population_best_service_loss_hr),gain_vs_impact_hr=IMPACT-z.best_service_loss_hr,gain_vs_prior_hr=PREVIOUS-z.best_service_loss_hr,postinitialization_gain_hr=g0.population_best_service_loss_hr-z.best_service_loss_hr,wall_seconds=z.elapsed_seconds,objective_wall_seconds=z.objective_seconds,process_cpu_seconds=None,cpu_status='NOT_RECORDED; objective timer is wall time',strict_after_initialization=sum(x['generation']>0 and x['distinct_evaluations']<=n for x in moves),new_strict_improvements=len(interval),marginal_gain_hr=None if last is None else last['j']-z.best_service_loss_hr,additional_wall_seconds=None if last is None else z.elapsed_seconds-last['wall'],source_file=rel(f/'BUDGET_CHECKPOINTS.csv'),source_sha256=old.digest(f/'BUDGET_CHECKPOINTS.csv')))
   last={'n':n,'j':z.best_service_loss_hr,'wall':z.elapsed_seconds}
 d=pd.DataFrame(rows);d.to_csv(OUT/'FINAL_BUDGET_CHECKPOINTS.csv',index=False)
 s=d.groupby('distinct_evaluations').agg(seeds=('seed','size'),best_hr=('best_hr','min'),median_hr=('best_hr','median'),mean_hr=('best_hr','mean'),sd_hr=('best_hr','std'),worst_hr=('best_hr','max'),gain_vs_impact_hr=('gain_vs_impact_hr','mean'),gain_vs_prior_hr=('gain_vs_prior_hr','mean'),mean_wall_seconds=('wall_seconds','mean'),sum_wall_seconds=('wall_seconds','sum'),mean_objective_wall_seconds=('objective_wall_seconds','mean'),min_generation=('actual_generation','min'),max_generation=('actual_generation','max'),mean_strict_count=('strict_after_initialization','mean'),mean_new_strict=('new_strict_improvements','mean'),mean_marginal_gain_hr=('marginal_gain_hr','mean')).reset_index()
 s.to_csv(OUT/'FINAL_BUDGET_SUMMARY.csv',index=False)
 c=pd.DataFrame([record(p.parent) for p in (PRIOR/'operator_confirmation').glob('operator_swap_s*/RUN.json')]);assert len(c)==20
 return d,s,c

def sig(a):return hashlib.sha256(np.nan_to_num(np.asarray(a),nan=np.inf).astype('<f8').tobytes()).hexdigest()
def equivalence(k):
 selected=json.loads((PRIOR/'reused_evaluation/CANDIDATE_SELECTION.json').read_text())['candidates'];ctx,dec,_=execution_context(k.ids);origins=dec.origins(ctx['origins']);rows=[];details=[];first=None
 for c in selected:
  order=dec.order(c['sequence']);queues=[];decoded=[]
  for b in range(64):
   queues.append(order[k.damage[b,order]>0].astype('<i8'));decoded.append(dec.decode(order=order,damage=k.damage[b],duration=k.duration[b],origins=origins))
  arrays=[np.stack([z[j] for z in decoded]) for j in range(7)]
  origin_by_station=np.full(arrays[3].shape,-1,dtype=np.int64)
  use=arrays[3]>=0;origin_by_station[use]=origins[arrays[3][use].astype(int)]
  sorted_clocks=np.array([sorted(zip(origins.tolist(),a.tolist())) for a in arrays[6]])
  if first is None:first=(queues,arrays,origin_by_station,sorted_clocks)
  for b in range(64):
   detail=dict(candidate=c['candidate_id'],planning_realization=b,damaged_order_equal=bool(np.array_equal(queues[b],first[0][b])))
   for j,key in enumerate(['completion','arrival','travel','crew','predecessor','dispatch_rank','final_clocks']):detail[key+'_equal']=bool(np.array_equal(arrays[j][b],first[1][j][b],equal_nan=True))
   detail['crew_origin_equal']=bool(np.array_equal(origin_by_station[b],first[2][b]))
   detail['origin_grouped_clock_multiset_equal']=bool(np.array_equal(sorted_clocks[b],first[3][b]))
   details.append(detail)
  rows.append(dict(candidate=c['candidate_id'],sequence_sha256=c['sequence_sha256'],planning_loss_hr=c['planning_loss_hr'],damaged_orders64_sha256=hashlib.sha256(b''.join(len(q).to_bytes(2,'little')+q.tobytes() for q in queues)).hexdigest(),completion64_sha256=sig(arrays[0]),operational_schedule64_sha256=hashlib.sha256(''.join(sig(arrays[j]) for j in [0,1,2,3,4,6]).encode()).hexdigest(),dispatch64_sha256=sig(arrays[5]),route64_sha256=hashlib.sha256((''.join(sig(arrays[j]) for j in [0,1,2,4])+sig(origin_by_station)+sig(sorted_clocks)).encode()).hexdigest(),source_file=rel(PRIOR/'reused_evaluation/CANDIDATE_SELECTION.json'),source_commit=BASE))
 s=pd.DataFrame(rows)
 for key,name in [('completion64_sha256','recovery_class'),('operational_schedule64_sha256','operational_class'),('damaged_orders64_sha256','damaged_order_class'),('route64_sha256','crew_relabelled_route_class')]:
  m={x:i+1 for i,x in enumerate(sorted(s[key].unique()))};s[name]=s[key].map(m)
 s.to_csv(OUT/'SEQUENCE_EQUIVALENCE_CLASSES.csv',index=False);p=pd.DataFrame(details);p.to_csv(OUT/'SEQUENCE_EQUIVALENCE_PER_REALIZATION.csv',index=False)
 return selected,s,p

def specification(k,inc,quality,selected):
 pool=[]
 for phase,seeds in [('operator_confirmation',range(42,62)),('budget_extension',range(42,47))]:
  for seed in seeds:
   p=PRIOR/phase/f'operator_swap_s{seed}'/'RUN.json';q=json.loads(p.read_text());pool.append((q['best_planning_loss_hr'],seed,q['budget'],q['sequence_sha256'],p,q))
 j,seed,budget,sha,p,q=min(pool,key=lambda x:(x[0],x[1],x[2],x[3]));assert sha==selected[0]['sequence_sha256']
 initial=initialize(tuple(k.ids),{n:tuple(s) for n,s in inc.items()},random.Random(42),FINAL,quality)
 dump(OUT/'INITIAL_POPULATION_SEED42.json',dict(seed=42,population=[list(x) for x in initial],slot_categories=['deterministic']*7+['prior_best']+['one_inversion_neighbor']*25+['uniform_random']*67,unique_permutations=len(set(initial))))
 dump(OUT/'SELECTED_SEQUENCE.json',dict(sequence=q['best_sequence'],sequence_sha256=sha,canonical_encoding='Ordered IDs separated by newline; UTF-8; final newline',planning_loss_hr=j,source_file=rel(p),source_file_sha256=old.digest(p),source_commit=BASE,selection_uses_evaluation=False,formal_policy_replaced=False))
 (OUT/'SELECTED_SEQUENCE.txt').write_bytes(('\n'.join(q['best_sequence'])+'\n').encode('utf-8'));assert old.digest(OUT/'SELECTED_SEQUENCE.txt')==sha
 prior=R/'results/diagnostics/extended_ga_20261008/p100_g2000_s46/RUN.json'
 spec=dict(status='METHOD_AND_SEQUENCE_PINNED_FOR_AUTHOR_REVIEW; INDEPENDENT_VALIDATION_REQUIRES_APPROVAL',base_commit=BASE,
  chromosome=dict(length=92,station_ids=list(k.ids),all_permutations_permitted=True,search_space='92!',ds0_filtering=True),algorithm=asdict(FINAL),
  initialization=dict(deterministic_order=list(inc),deterministic_count=7,prior_best_count=1,prior_best_sequence=list(quality),prior_best_sha256=old.identity(quality),prior_best_source=rel(prior),prior_best_source_sha256=old.digest(prior),prior_best_source_commit=BASE,prior_best_loss_hr=PREVIOUS,inversion_neighbors=25,neighbor_parent_rule='j0..24: even j prior-best13; odd j Impact-first12',neighbor_operator='One inclusive inversion between two distinct uniform positions; duplicates permitted',random_permutations=67,random_operator='random.Random(seed).sample(ordered_ids,92)',deduplication=False,rng_order='deterministic then prior-best then25 inversions then67 random permutations'),
  objective=dict(direction='minimize',fitness='-J',planning_samples=64,hazard='2pc50',resource='C57_D1',manuscript_integral_hr=[0,480],unchanged_kernel_horizon_hr=k.horizon,horizon_equivalence_source='results/diagnostics/extended_ga_20261008/PLANNING_HORIZON_AUDIT.json',station_mass='m_i=sum_t population_t * fixed_mapping_weight_ti',normalizer='sum_i m_i',station_availability='f * indicator(f>=0.5) * Core-source-connectivity',cache_key='92 uint8 indices in pinned station-ID order',cache_scope='Within seed only; empty at restart'),
  search_protocol=dict(stage_A_seeds=list(range(42,62)),stage_A_distinct_budget=100000,stage_B_seeds=list(range(42,47)),stage_B_rule='Fixed seeds42..46, selected before extension; no outcome ranking',stage_B_total_distinct_budget=500000,continue_stage_A=True,nominal_distinct_queries=4000000,accounting='20*100000 +5*(500000-100000)',checkpoints=[50000,100000,250000,500000],attempt_safety_limit='50 times current total distinct budget',candidate_rule='Minimum exact planning loss over evaluated StageA/StageB chromosomes; exact run ties: smallest seed, smaller total budget, sequence SHA. Within run earliest strictly improving observation.',result_record='Best-observed at query boundary, separately retain completed-generation archive',fixed_generation_limit=None,stagnation_stop=False,validation_guided_selection=False),
  selected=dict(sequence_sha256=sha,planning_loss_hr=j,seed=seed,budget=budget,source_file=rel(p),source_commit=BASE),
  reproduction=dict(python=sys.version,numpy=np.__version__,numba=numba.__version__,platform=platform.platform(),environment={'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}),
  source_sha256={x:old.digest(R/x) for x in ['src/la_grid/diagnostics/ga_variant_engine.py','src/la_grid/revision/r1_ga_revision.py','src/la_grid/revision/r1_ga_exact_kernel.py','src/la_grid/revision/formal/schedule.py','src/la_grid/diagnostics/ga_search_budget_sensitivity.py','src/la_grid/core/C257H_Project_Main.py','src/la_grid/revision/r1_source_gate.py','src/la_grid/revision/r1_realization_scheduling.py','src/la_grid/revision/formal/offline.py','src/la_grid/revision/r1_equity_amendment_execute.py','src/la_grid/diagnostics/evaluate_extended_ga_20261008.py']},
  original_input_identity=json.loads((PRIOR/'INPUT_IDENTITY.json').read_text()),new_physical_sampling=False,formal_strategy_replaced=False)
 spec['source_git_blob_sha256']={x:hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+x],cwd=R)).hexdigest() for x in spec['source_sha256']}
 spec['source_hash_note']='Working-file hashes pin the Windows runtime. Git-blob hashes additionally identify normalized source bytes at the base commit.'
 spec['implementation_details']=dict(selection='100 draws; each tournament samples3 indices with replacement; exact fitness tie retains first draw',ordered_crossover='Two distinct cuts, inclusive segment; cyclic donor fill starts after high cut; reciprocal children; probability per pair',mutation='Two distinct uniform positions exchanged; probability per child',elite='Best parent by descending fitness then ascending lexicographic tuple overwrites last offspring after RNG calls',archive='Completed-generation strict improvement only; separate best-observed query record retains first exact tie',safety_cap='Attempt cap checked at completed-generation boundaries; may overshoot by generation bookkeeping; incomplete if distinct target not reached')
 dump(OUT/'FINAL_GA_CONFIG_CANDIDATE.json',spec);return spec

def validation(spec):
 cost=json.loads((OUT/'VALIDATION_COST_BENCHMARK.json').read_text());steady=[v['wall_seconds'] for v in cost['timings'][1:]];n=2000;strategies=10
 serial=n*strategies*float(np.median(steady));storage=cost['existing_1000_candidate_archive_bytes']*(n/1000)*strategies
 d=pd.read_csv(PRIOR/'reused_evaluation/REALIZATION_DIFFERENCES.csv',usecols=['candidate','reference','source_field','change'])
 x=d[d.candidate.eq('ga-optimized-01') & d.reference.eq('impact-first') & d.source_field.eq('population_weighted_normalized_burden_hr')].change.to_numpy();assert len(x)==1000
 sd=float(x.std(ddof=1));half=1.96*sd/np.sqrt(n)
 # Numerical normalization check, not a new mapping.
 w=pd.read_csv(R/'Data/JULY_UTILITY_CONSTRAINED_92.csv',dtype={'tract_id':str});rho=w.groupby('tract_id').weight.sum()
 protocol=dict(status='PROPOSED; NO_AUTHORIZATION_TO_GENERATE_NEW_PHYSICAL_SAMPLES',sample_size=n,hazard='2pc50',resource='C57_D1',
  randomness=dict(master_seed=202610091,hazard_index=3,split_code=2,realization_indices=[0,1999],seed_sequence='SeedSequence([202610091,3,2,r])',generator='numpy.default_rng / PCG64',sampling_functions=['sample_damage_states','damage_to_functionality_and_repair'],model_parameters='Unchanged2pc50 PGA/fragility, positive DS-specific repair durations; DS0 duration0',namespace='Separate independent validation archive, no original files overwritten',cross_strategy_sharing=True,overlap_rule='Hash against all64 planning and1000 inspected rows; any exact overlap aborts for review, no silent redraw'),
  selected_sequence_sha256=spec['selected']['sequence_sha256'],
  primary=dict(metric='Population-weighted cumulative modeled service loss',horizon_hr=[0,480],reference='Impact-first',effect='candidate minus reference',estimand='Mean realization-level difference under fixed2pc50 model'),
  secondary_references=['Hospital-first','Degree-first','Betweenness-first','Vulnerability-first','Random','Unconstrained','ga-exploratory-01','ga-exploratory-02'],
  secondary_metrics=['Population T80','Q1/Q2/Q3/Q4 service loss','Signed Q4-Q1 difference','Realization-level absolute Q4-Q1 gap','Population-weighted Gini','Equal-tract mean hospital-linked service loss','Self/threshold/source-path losses','f/F/C/e trajectories','Dispatch/arrival/completion/travel'],
  statistical=dict(bootstrap_resamples=20000,bootstrap_seed=2026100901,resampling_unit='Whole shared physical realization',primary_interval='Two-sided95% percentile bootstrap CI of mean difference; Monte Carlo SE',secondary_intervals='Pointwise95%, descriptive, no multiplicity-adjusted confirmatory claims',descriptive='Means, medians, empirical5th-95th ranges',no_optional_stopping=True,no_reselection=True),
  endpoint_normalization_audit=dict(tract_count=len(rho),mapping_mass_min=float(rho.min()),mapping_mass_max=float(rho.max()),max_deviation_from1=float(abs(rho-1).max()),mapping_recomputed=False),
  estimate=dict(saved_samples_timed=6,steady_pipeline_seconds=float(np.median(steady)),serial_metric_pipeline_seconds=serial,excludes='New physical generation, file writing, bootstrap, setup',exploratory_difference_sd_hr=sd,anticipated_normal_CI_halfwidth_hr=half,halfwidth_not_guaranteed=True,archive_bytes=storage,reserved_storage_bytes=int(3*storage),end_to_end_allowance_minutes=[10,30],allowance_status='Engineering allowance, not measured end-to-end runtime',physical_sampling_benchmarked=False,new_samples_generated=0),
  scientific_scope='Independent Monte Carlo validation conditional on fixed model; not observed-grid external validation')
 dump(OUT/'FINAL_VALIDATION_PROTOCOL.json',protocol)
 md('FINAL_INDEPENDENT_VALIDATION_PROTOCOL.md',f'''
# Independent final validation protocol â€” proposed

**No new physical samples are authorized or generated.** Approve the pinned method, budget, selection rule, sequence and statistical plan together before filling a new validation archive. FREEZE_RECEIPT.json pins protocol/config/sequence/comparator hashes before any physical draw; author approval is still required.

## Physical samples and scope

Fixed N=**2,0002pc50/C57_D1 realizations**, with no optional extension. Use `numpy.default_rng(SeedSequence([202610091,3,2,r]))`, r0..1999, and the pinned software/ordered92 IDs. Original master42 and split0/1 are not reused. Invoke the existing `sample_damage_states` and `damage_to_functionality_and_repair` functions with unchanged2pc50 PGA/fragility and duration parameters. Draw DS0-DS4 and strictly positive durations once per realization; DS0 duration0. Share the same samples across all policies. Do not introduce new correlations or physical assumptions. Record canonical DS/duration hashes and source identities; compare to all original64/1000 hashes. Any exact overlap aborts for review rather than silent redraw. Use a separate archive namespace.

This is Monte Carlo validation conditional on the same earthquake/network/service model, not empirical validation against observed outage records or a cross-hazard assessment.

## Fixed comparisons and endpoint definitions

Selected GA sequence: `{spec['selected']['sequence_sha256']}`. Primary reference **Impact-first**; secondary fixed comparators Hospital-first, Degree-first, Betweenness-first, Vulnerability-first, Random, Unconstrained and both prior exploratory GA sequences. Exact comparator sequences and hashes are pinned in VALIDATION_COMPARATOR_SEQUENCES.json before sampling. Random is the saved fixed ordering, not a new ordering per realization. Unconstrained uses the same DS/durations without crew competition. Ten policy conditions in total.

Primary endpoint: population-weighted cumulative modeled service loss over **0-480 h**, with unchanged production mapping, station/service gate and normalization. Estimand: mean within-realization candidate-minus-Impact-first difference; negative favors candidate. Audit kernel population-dependency-mass and tract-normalized endpoint agreement without changing either denominator. Production mapping row-mass minimum/maximum={rho.min():.15f}/{rho.max():.15f}; maximum deviation from1={abs(rho-1).max():.3g}. No weights were renormalized.

Secondary: Q1-Q4 service loss, signed Q4-Q1, realization-level |Q4-Q1| then average (not absolute difference of mean outcomes), population-weighted Gini, equal-tract mean hospital-linked service loss, population T80, self/threshold/source-path components, f/F/C/e trajectories, and task execution/travel/completion. Quartile assignments and hospital flags are fixed. These are consequences of aggregate optimization, not a new multi-objective fitness. Hospital-linked loss does not measure electricity delivery or clinical capacity.

Do not extend the480-h endpoint when a new realization finishes later. Report unreached-T80 counts and conditional T80 summaries with denominators; do not silently omit censored rows or assign a favorable recovery time. Population T80 and mean tract T80 are distinct. Missing outcomes trigger explicit reporting rather than imputation.

## Uncertainty and decision rule

Retain identical realization IDs across policies. Report mean/median differences and empirical5th-95th realization ranges. Obtain **20,000-resample95% percentile bootstrap CIs for mean differences**, seed2026100901, by resampling whole realizations jointly across policies/metrics in memory-bounded batches. Do not resample tracts independently. Also report primary Monte Carlo SE. Only the GA/Impact-first contrast is primary. Secondary CIs are pointwise descriptive and are not adjusted confirmatory multiple comparisons.

No validation-based chromosome tie-break, hyperparameter selection, metric/subgroup selection or optional stopping. If performance fails to transfer, report that result. Any later tuning creates a new algorithm and requires a new assessment plan; this cohort cannot remain an untouched test after that tuning.

## Sample size and estimated compute

N2000 is a bounded precision choice, not assumed power for an unknown true effect. The inspected exploratory difference SD={sd:.6f} h implies an approximate95% mean-CI half-width **{half:.6f} h** if variance transfers. This planning estimate is not a validation finding.

Timing six already inspected saved samples generated no new physical data. Warm pipeline median{np.median(steady):.6f} s per candidate-realization suggests approximately **{serial:.1f} serial seconds** for20,000 policy-realizations. That extrapolation excludes new physical generation, file writing, bootstrap and setup; the first timed call includes cold compilation/setup effects. Reserve **10-30 minutes** as an unmeasured engineering allowance, then measure authorized setup/I/O before a full run. Subsecond CPU measurements are quantized and do not justify precise CPU projections. Existing archive sizes imply about **{storage/2**30:.2f} GiB**, reserving at least **{3*storage/2**30:.2f} GiB** for temporary files and verification. Check free disk before author-approved execution. Physical sampling was not benchmarked or performed.

## Existing evidence and approval gate

The64 repeatedly optimized planning samples and previously inspected1000 evaluation samples are not untouched final validation. Existing favorable exploratory results retain that qualification. The algorithm is ready to report transparently and to enter final validation; independent performance confirmation and formal strategy promotion remain pending author authorization. No validation run has started and original formal files remain unchanged.
''')
 return protocol

def reports(spec,summary,effects,bs,confirmation,eq,per):
 prior=json.loads((R/'results/diagnostics/extended_ga_20261008/p100_g2000_s46/RUN.json').read_text())['summary']
 initial_gain=IMPACT-PREVIOUS;post=PREVIOUS-spec['selected']['planning_loss_hr'];percent=100*initial_gain/(initial_gain+post)
 md('FINAL_GA_METHOD_AUDIT.md',f'''
# Final GA method audit

Base `{BASE}`. **Scientifically ready for transparent method reporting and independent final validation; further open-ended algorithm development is not required for this candidate.** Independent validation and author approval of formal promotion remain pending. Existing formal policies are unchanged.

## Chromosome, scheduler and direct objective

Each chromosome contains each fixed station ID once: all92! permutations are permitted. For each of64 saved2pc50 planning samples, remove DS0 tasks without reranking. The exact scheduler dispatches the next damaged station to the earliest-free crew (lowest crew index on an exact clock tie), adds directed travel and its saved repair duration, and restores the station at completion. C57 origins, travel, graph, gate, mapping and repair distributions are unchanged.

Let W_ti be fixed tract dependency, P_t population and m_i=sum_t P_t W_ti. Raw functionality is f_ri(t), F_ri(t)=1[f_ri(t)>=0.5], and C_ri(t) is connectivity through eligible stations to any14 Core source. The objective is

$$m_i=\\sum_t P_t W_{{ti}},\\qquad J(\\pi)=\\frac{{1}}{{64}}\\sum_{{r=1}}^{{64}}\\frac{{\\sum_i m_i\\int_0^{{480}}[1-f_{{ri}}(t;\\pi)F_{{ri}}(t;\\pi)C_{{ri}}(t;\\pi)]\\,dt}}{{\\sum_i m_i}}.$$

The algorithm maximizes fitness=-J using event-exact left rectangles. The unmodified kernel uses H_plan={spec['objective']['unchanged_kernel_horizon_hr']:.12f} h. PLANNING_HORIZON_AUDIT establishes an order-independent completion upper bound134.332550166 h and a Core source in each intact component, so its post480 loss is zero for these fixed inputs. Its scores therefore equal the480-h endpoint. This is a proved equivalence for these inputs, not a silently altered horizon; do not assume it for future samples. Station masses and their encoded sum are retained without new mapping normalization.

## Exact initial population

Seven fixed rules, in saved dictionary order: **{', '.join(spec['initialization']['deterministic_order'])}**. Append one prior-best sequence; append25 independently drawn inversion neighbors (j0..24:13 even-j neighbors of prior best,12 odd-j neighbors of Impact-first); fill the remaining67 slots with uniform full permutations. Each inversion reverses the inclusive segment between two distinct uniform positions. Initialization is7+1+25+67=100 slots; duplicates are allowed and occupy slots. The25 neighbors are not uniformly random chromosomes. The complete seed42 example population is saved in INITIAL_POPULATION_SEED42.json.

Prior-best chromosome: `{spec['initialization']['prior_best_sha256']}` from `{spec['initialization']['prior_best_source']}`, seed46, population100, generation2000, J={PREVIOUS:.12f} h. That discovery run records{prior['unique_candidates_evaluated']:,} distinct candidates and{prior['elapsed_seconds']:.3f} s. These are one run's costs, not the complete earlier development cost. The source and sequence are fixed; newly found candidates do not replace this initialization source.

## Operators and RNG

Use Python `random.Random(seed)` and the pinned runtime/source hashes. Incumbents consume no RNG draws; inversion neighbors precede random permutations. At each generation draw100 parents. Each tournament samples3 indices **with replacement**; choose highest fitness and keep the first sampled index on an exact tie. Pair consecutive parents. One Bernoulli0.80 ordered-crossover draw per pair; sample two distinct cuts, include both endpoints, inherit that segment and fill remaining positions in the other parent's cyclic order starting after the segment. Produce reciprocal children. Independently draw Bernoulli0.10 mutation per child and, when triggered, swap two distinct uniformly sampled positions. Initialization still uses inversion, despite evolutionary swap mutation. Adaptive mutation, restarts, crowding, alternate crossover and mixed operators are disabled.

After generating100 children, sort the parent population by descending fitness then lexicographically ascending tuple on ties; copy its one best distinct chromosome into the last child slot. RNG draws for that overwritten child still occurred. This one-elite survival changes the evolving population and is distinct from archive preservation.

The archive starts with the best of seven deterministic incumbents; incumbent ties use rule name then sequence. A completed-generation candidate uses max(fitness,lexicographically largest tuple), and the archive updates only on strictly better fitness. The separate best-observed record updates at every first expensive query only on strict improvement, retaining the earliest encountered exact tie. If budget ends mid-generation, report best-observed and separately retain the completed-generation archive. Do not discard an evaluated improvement or claim the partial generation completed.

## Caching, stopping, restarts and selection

The cache key is92 unsigned-byte indices in the original pinned station-ID order. Cache is private to each seed and initially empty; no cross-seed scores are free. First scoring consumes one expensive query; duplicates consume attempts but no new query. Seven initial incumbent scores count against the budget; rescoring them in the initial population hits cache. No tolerance-based equivalence collapses different chromosomes.

Stop exactly at the distinct-query limit, potentially within a generation, or at the attempt safety limit50 times the total budget. The attempt cap is checked after completed generations, so it is a boundary safeguard and can overshoot by generation bookkeeping. Safety-cap runs are incomplete and cannot be reported as full budget. There is no fixed-generation or stagnation stop. Actual generations and all budget/attempt counters are saved; all reported runs reached their designated budget.

StageA: seeds42-61,100k distinct queries each. StageB: **fixed seeds42-46**, continued to500k total each with unchanged RNG/state/cache. No evaluation or best-seed ranking chooses the extension. A deterministic500k replay from scratch reproduces the prefix, but costs another100k prefix and must be charged as extra actual work. Existing prefix checks establish identity. Future fresh execution should retain checkpoints to avoid replay overhead.

Select the minimum exact planning loss over evaluated StageA/StageB chromosomes from this recommended configuration only. Across exact run ties: smallest seed, smaller total budget, sequence SHA; within a run earliest strictly improving observation wins. No evaluation-guided tie-breaking. Selected seed{spec['selected']['seed']}, total budget{spec['selected']['budget']:,}, J={spec['selected']['planning_loss_hr']:.12f} h, identity `{spec['selected']['sequence_sha256']}`. Other operator/local candidates remain diagnostics/comparators.

## Warm start versus evolutionary improvement

All following attribution rows use seeds42-46 and50k distinct queries. A/B reuse saved results. Only C and D at original mutation0.20 were missing; ten bounded new runs add500k queries. D at final0.10 and the inversion0.10 bridge are saved comparisons. This separates an operator change from a simultaneous mutation-rate change.

{tab(summary)}

{tab(effects)}

The prior-best already contributes **{initial_gain:.9f} h** of the selected sequence's{initial_gain+post:.9f} h reduction relative to Impact-first (**{percent:.2f}%**). Further reduction below that inherited best is **{post:.9f} h**. This is provenance accounting, not universal causal attribution. Seed-specific improvements made by initialization neighbors are separately counted at generation zero; subsequent gains are counted after generation zero. The full reduction cannot be presented as a new random-start discovery.

The seed46 discovery cost{prior['unique_candidates_evaluated']:,} queries is a component of earlier work, not the total cost of finding/selecting the warm start. The20261009 study separately records28,730,784 new expensive queries, including heterogeneous48-sample CV and local/hybrid work. Those development costs are not the4m final protocol; overlapping prefixes/lookup reuse retain their recorded accounting rather than being falsely called globally unique. Do not add the individual discovery run twice to aggregate development totals. Each loader also makes eight setup-validation objective calls outside the search budget; the ten new runs therefore add 80 such calls as well as 500,000 search queries. They are charged separately. New controlled comparisons record process CPU; historical runs did not.

## Manuscript-ready method description

We used an incumbent-preserving permutation genetic algorithm with ordered crossover, swap mutation, tournament selection and one-elite generational survival. Initial populations combined seven fixed-rule sequences, a previously optimized sequence, inversion variants of high-quality sequences and random permutations. Twenty independent pseudorandom restarts received100,000 distinct objective evaluations each; five fixed seeds were extended to500,000 total evaluations. Sequence selection used the unchanged64-realization planning objective only. Initialization advantage and subsequent search gains were reported separately, alongside the computational effort underlying the warm start. The best feasible ordering and tested local stability do not establish global optimality or uniqueness.
''')
 cols=['distinct_evaluations','seeds','best_hr','median_hr','mean_hr','sd_hr','mean_wall_seconds','mean_new_strict','mean_marginal_gain_hr']
 md('GA_BUDGET_AND_REPLICATION_DECISION.md',f'''
# Final computational budget and replication decision

Recommend **StageA20 seeds x100k + StageB fixed seeds42-46 continued to500k total**, with the recommended unchanged parameter set. No further open-ended sweep. StageB's seed rule is fixed before extension, not chosen using planning rank or evaluation effects. The nominal unique-query total is4,000,000:20*100k+5*(500k-100k). StageB adds2m to StageA's2m;100k and500k are unequal budgets.

## Five common extended streams at common checkpoints

{tab(bs[cols])}

FINAL_BUDGET_CHECKPOINTS.csv supplies best objectives, actual attempts/generations, completed-generation boundaries, initial/reference improvements, strict improvements and time per seed. Counts exclude generation-zero scoring. A strict tiny improvement is not automatically a practically meaningful scientific gain. No benefit threshold is invented.

Twenty-seed100k result: mean{confirmation.best_planning_loss_hr.mean():.9f} h, SD{confirmation.best_planning_loss_hr.std():.9f}, median{confirmation.best_planning_loss_hr.median():.9f}, best{confirmation.best_planning_loss_hr.min():.9f}, worst{confirmation.best_planning_loss_hr.max():.9f}. All20 improve prior best. Seeds42-46 are common screening seeds;47-61 are15 additional pseudorandom restarts. This replication assesses search stochasticity under the same64 samples and selected configuration, not independent physical validation.

Mean100k-to500k gain for the same five streams: **{bs.loc[bs.distinct_evaluations.eq(100000),'mean_hr'].iloc[0]-bs.iloc[-1].mean_hr:.9f} h**. Later gains are small relative to the approximately0.58h improvement over Impact-first. A bounded extension remains defensible for final selection; small late gains do not prove there is no remaining improvement.

## CPU, wall-clock and generation caveats

Historical process CPU time was **not recorded**. The saved objective_seconds uses perf_counter and is an objective wall timer, not CPU. Do not relabel it or invent a historical CPU estimate. New controlled comparisons record process CPU explicitly. Recorded per-run times include concurrent-host effects; their sum is aggregate run wall duration, not elapsed batch time or total CPU. The budget CSV records minimum/maximum actual generations and completed-generation boundaries; no common generation count is fabricated.

Continuation preserves RNG/state/cache. If a local checkpoint was removed after completing old runs, a from-scratch500k replay reproduces the algorithm but pays its100k prefix again. Existing saved500k source records are the reporting authority; future fresh execution should retain resume checkpoints. Count actual replay overhead separately from the nominal continuation budget. Warm-start discovery, screening and operator development are disclosed as earlier work, not free initialization. New evaluation cannot select extension seeds or chromosomes.
''')
 md('GA_SEQUENCE_EQUIVALENCE_AUDIT.md',f'''
# Sequence, schedule and recovery equivalence

{tab(eq[['candidate','sequence_sha256','planning_loss_hr','damaged_order_class','operational_class','crew_relabelled_route_class','recovery_class']])}

Three distinct full permutations form{eq.damaged_order_class.nunique()} joint DS>0-filtered queue classes. At least one planning row contains all92 damaged stations, making the joint filtered representation injective; equal loss cannot be attributed solely to DS0 removal across all64 samples.

The exact decoder comparison checks station completion/arrival/travel, crew assignment, predecessor, global dispatch rank and final crew clocks separately. It identifies **{eq.operational_class.nunique()} operational-schedule classes** (arrival/completion/travel/crew/predecessor/clocks; global dispatch rank is recorded separately). Thus completion equality alone does not establish equality of complete operational schedules. Canonical route identity additionally checks each station's crew origin and predecessor plus origin-grouped final-clock multisets while ignoring interchangeable crew labels. It yields **{eq.crew_relabelled_route_class.nunique()} route-equivalence class**. All64 rows preserve arrival, travel and predecessor; differences in crew IDs/dispatch rank alone need not describe different restoration behavior. SEQUENCE_EQUIVALENCE_PER_REALIZATION.csv records each field for every64-row comparison against candidate1; class hashes are in SEQUENCE_EQUIVALENCE_CLASSES.csv.

There is **{eq.recovery_class.nunique()} planning recovery-equivalence class**. With the same DS and station completion times, completion-step f, threshold F, source connectivity C and effective e are identical at all event times under the same graph/gate. This deterministic implication establishes recovery equivalence rather than merely a rounded scalar tie. All three losses equal{spec['selected']['planning_loss_hr']:.12f} h. Different crew labels/dispatch orders can coexist with the same station recovery behavior. These classes concern these three candidates on64 saved realizations; they do not certify identity across all possible damage/duration states. Previously inspected1000 outcomes exhibit small differences, reported without reselection.

The prior bounded tie-pool checks of100 near-best chromosomes are not an exhaustive partition of92! or every searched candidate. Alternative representations of one planning recovery behavior must not be counted as three independent scientific improvements.

## Solution quality

Best feasible J={spec['selected']['planning_loss_hr']:.12f} h; conservatively downward-rounded valid fixed-model relaxation lower bound31.360999855 h. Remaining gap **{spec['selected']['planning_loss_hr']-31.360999855:.9f} h**, **{100*(spec['selected']['planning_loss_hr']-31.360999855)/spec['selected']['planning_loss_hr']:.3f}% of the feasible value**; dividing by the lower bound instead gives{100*(spec['selected']['planning_loss_hr']-31.360999855)/31.360999855:.3f}%. State the denominator.

The relaxation eliminates crew competition/travel while preserving saved duration, threshold and source connectivity. It bounds the mathematical model conditional on fixed inputs, not out-of-sample performance. Pair swaps, insertion, inversion and tested block moves establish neighborhood-qualified local stability at tolerance1e-9 only. Other combined changes lie outside those neighborhoods. Finite search, a plateau or exact six-slot restricted enumeration does not prove full92-station global optimality or uniqueness.
''')
 md('README.md','''# Final GA method candidate and validation preparation

Read FINAL_GA_METHOD_AUDIT.md, GA_BUDGET_AND_REPLICATION_DECISION.md and FINAL_INDEPENDENT_VALIDATION_PROTOCOL.md. FINAL_GA_CONFIG_CANDIDATE.json pins the method, identities, budget and selected sequence. Independent validation is proposed and has not run. Formal strategies and manuscript artwork remain unchanged.

GA_INITIALIZATION_VS_SEARCH_IMPROVEMENT.csv separates initialization advantage and subsequent gains at a common50k budget. Only two missing five-seed comparisons were executed. Their full records are under controlled_comparisons. Sequence-equivalence tables distinguish chromosomes, damaged queues, operational schedules and recovery outcomes. Earlier sources are recorded by path, commit and hash.
''')

def freeze_validation_comparators(spec,inc):
 rows=[]
 def add(name,seq,source):
  seq=list(map(str,seq));assert len(seq)==92 and set(seq)==set(spec['chromosome']['station_ids'])
  rows.append(dict(strategy=name,sequence=seq,sequence_sha256=old.identity(seq),source_file=source,source_file_sha256=old.digest(R/source),source_commit=BASE))
 formal='Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json'
 for n in ['impact-first','hospital-first','degree-first','betweenness-first','random']:add(n,inc[n],formal)
 vuln='Formal_Experiment_20260923/Equity_Amendment/VULNERABILITY_FIRST_SEQUENCE.json'
 add('vulnerability-first',json.loads((R/vuln).read_text())['ordered_station_ids'],vuln)
 prior='results/diagnostics/extended_ga_20261008/independent_evaluation/CANDIDATE_SELECTION.json'
 for q in json.loads((R/prior).read_text())['candidates']:add(q['candidate_id'],q['sequence'],prior)
 current=json.loads((OUT/'SELECTED_SEQUENCE.json').read_text())
 add('ga-final-method-candidate',current['sequence'],spec['selected']['source_file'])
 dump(OUT/'VALIDATION_COMPARATOR_SEQUENCES.json',dict(base_commit=BASE,selection_uses_validation=False,ordered_policies=rows,unconstrained=dict(representation='No priority permutation',completion='Saved repair duration for each DS>0 station; zero for DS0',crew_competition=False,directed_travel=False),total_conditions=10))

def freeze_receipt():
 files=['FINAL_GA_CONFIG_CANDIDATE.json','SELECTED_SEQUENCE.json','SELECTED_SEQUENCE.txt','FINAL_VALIDATION_PROTOCOL.json','VALIDATION_COMPARATOR_SEQUENCES.json']
 dump(OUT/'FREEZE_RECEIPT.json',dict(status='PINNED_CANDIDATE_METHOD_AND_PROPOSED_VALIDATION_PLAN; PHYSICAL_SAMPLING_NOT_AUTHORIZED',base_commit=BASE,files_sha256={x:old.digest(OUT/x) for x in files},new_physical_samples=0,formal_promotion=False,self_hash_excluded=True))
 md('REPRODUCTION_COMMANDS.md',r'''
# Reproducing the completed diagnostics

Use the recorded Python/NumPy/Numba environment, set PYTHONPATH to src, and set OPENBLAS_NUM_THREADS and MKL_NUM_THREADS to 1. Verify FREEZE_RECEIPT.json and source/input hashes before execution.

The completed bounded attribution comparisons can be regenerated with:

`python -m la_grid.diagnostics.final_ga_method_20261009`

Existing verified RUN.json files are reused. This command executes only the two missing configurations recorded in CONTROLLED_COMPARISON_DESIGN.json, five seeds each, using saved planning inputs. It does not generate physical samples or change formal results.

The report and exact method/sequence/validation freeze can be regenerated from those results with:

`python -m la_grid.diagnostics.final_ga_method_report_20261009`

This reconstructs schedules only for the three saved planning candidates to compare equivalence, and derives tables and documents. It does not launch another GA search or draw physical samples.

For a fresh reproduction of the recommended search, construct Variant from FINAL_GA_CONFIG_CANDIDATE.json and call the pinned ga_variant_engine.run_search with the same ordered station IDs, seven incumbent sequences, prior-best quality sequence, kernel.score and seeds. Stage A uses 100000 distinct queries per seed 42-61. Retain its resume checkpoint; Stage B calls the same function and folder for fixed seeds 42-46 with max_evaluations=500000. The cache and RNG must continue. Checkpoints are 50000/100000/250000/500000; report actual generation counts. A from-scratch 500000 run is a deterministic replay, with extra prefix costs disclosed, not a cost-free continuation. Do not pass a generation stop or reuse objective lookups as free calls.

No executor for new physical validation is launched by either command. The independent validation plan requires separate author approval.
''')

def main():
 k,inc,quality=load();d,s,e=attribution();b,bs,c=budgets();selected,eq,per=equivalence(k)
 spec=specification(k,inc,quality,selected);validation(spec);freeze_validation_comparators(spec,inc);reports(spec,s,e,bs,c,eq,per);freeze_receipt()
 print('BUILD_COMPLETE',OUT);print(tab(s));print(tab(e));print(tab(bs[['distinct_evaluations','best_hr','median_hr','mean_hr','sd_hr','mean_marginal_gain_hr']]))
if __name__=='__main__':main()
