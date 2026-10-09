"""Decision report generated from recorded planning and exploratory outcomes."""
import json
from pathlib import Path
import pandas as pd,numpy as np
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.diagnostics import ga_search_budget_sensitivity as old


def table(d,columns,digits=6):
    return d[columns].to_markdown(index=False,floatfmt=f'.{digits}f')


def main():
    kernel,inc,previous=load();summary=pd.read_csv(OUT/'CONFIGURATION_SUMMARY.csv');factors=pd.read_csv(OUT/'CONTROLLED_FACTOR_EFFECTS.csv');quality=pd.read_csv(OUT/'BEST_SEQUENCE_QUALITY.csv');best=quality.iloc[0];local=json.loads((OUT/'local_search/previous_best/RUN.json').read_text());cv=pd.read_csv(OUT/'INTERNAL_PLANNING_CV.csv');pair=pd.read_csv(OUT/'EXISTING_EXPLORATORY_PAIR_DIFFERENCES.csv');pair=pair[pair.source_field.eq('population_weighted_normalized_burden_hr')].iloc[0];bound=json.loads((OUT/'RATIONAL_RELAXATION_BOUND.json').read_text());lower=bound['lower_bound_hr_rounded_down_1e_minus_9'];d=pd.read_csv(OUT/'GA_PARAMETER_SENSITIVITY.csv');selected=json.loads((OUT/'reused_evaluation/CANDIDATE_SELECTION.json').read_text());effects=pd.read_csv(OUT/'reused_evaluation/OUTCOME_COMPARISONS.csv');landscape=pd.read_csv(OUT/'CANDIDATE_LANDSCAPE.csv');parity=json.loads((OUT/'ORIGINAL_HISTORY_PARITY.json').read_text());short=summary[summary.phase.isin(['shortlist','operator_confirmation'])].sort_values(['mean_hr','std_hr']);recommend=short.iloc[0];configs=json.loads((OUT/'CONFIGURATIONS.json').read_text());params=configs[recommend.config_id];screen=summary[summary.phase.eq('screen')];init=pd.read_csv(OUT/'INITIALIZATION_VERSUS_SEARCH_GAINS.csv');initial=init[init.phase.eq('shortlist')].groupby('config_id')[['generation0_best_hr','final_hr','post_initialization_improvement_hr']].mean().reset_index(); ranked=factors.assign(abs_effect=lambda q:q.mean_effect_hr.abs()).sort_values('abs_effect',ascending=False).head(12); new_local=json.loads((OUT/'local_search/operator_best/RUN.json').read_text()); hybrid=pd.read_csv(OUT/'GA_LOCAL_SEARCH_AND_HYBRID_RESULTS.csv'); hybrid=hybrid[hybrid.method.eq('GA_50K_PLUS_LOCAL_50K')]
    audit=f'''# GA hyperparameter, operator and search audit — 2026-10-09

Base revision: `164f4564c0dabdeffdaf3870af000bbca725f71a`. New results are diagnostic. The original formal strategy set, scientific source tables, physical samples, repair durations, mapping, gate, schedules, evaluation trajectories and manuscript artwork are not replaced.

## Objective and exact original behavior

For station i, let m_i = sum_r P_r W_ri, F_bi(t)=I[f_bi(t)>=0.5], C_bi(t) denote connection to an active Core source, and e_bi=f_bi F_bi C_bi. The original objective is

$$J(\\pi)=\\frac1{{64}}\\sum_{{b=1}}^{{64}}\\frac{{\\sum_i m_i\\int_0^{{H_{{plan}}}}[1-e^\\pi_{{bi}}(t)]\\,dt}}{{\\sum_i m_i}},\\qquad fitness(\\pi)=-J(\\pi).$$

H_plan = {kernel.horizon:.12f} h is preserved. The existing PLANNING_HORIZON_AUDIT.json establishes an order-independent completion bound of 134.332550 h, below 480 h, and a Core source in every intact component. That proof establishes equivalence to 0-480 h integration on these planning realizations; the evaluator and objective were not replaced with a shorter-horizon surrogate. Impact-first is a deterministic reference, not the objective. Chromosomes span full 92-station permutations, a 92! decision space. DS0 stations are omitted only by the unchanged realization-specific scheduler.

Seven deterministic sequences enter the initial population and initialize the best-so-far archive. Only a strict higher fitness replaces that archive. Original ordered crossover=.80, inversion mutation=.20 and tournament size=3 are retained in the baseline; no generational elitism is present. Thus the original five coincident archives mean that tested candidates did not beat the injected incumbent, not that five searches independently rediscovered it.

Observation-only reproduction passed {len(parity)} actual history comparisons: five original 100-generation histories, five 250-generation histories, five extended P100/1,000-generation histories and five P500/1,000-generation histories. Maximum numerical discrepancy: {max(r['history_max_abs_error'] for r in parity):.3g}. Original archive sequence identities also match exactly. No unexpected expensive score was required in replay. Independent candidate/realization checks reproduce the independent pandas/NetworkX production path; see NEW_CANDIDATE_PRODUCTION_PARITY.csv. No implementation defect explaining P500 failure was detected in these tests.

## Q1 — Why P500 behaved worse

The initial deterministic fraction is 7% at P100 and 1.4% at P500. With tournament3, the probability a draw includes any deterministic position is 1-(1-7/P)^3. Expected selected deterministic positions are about 19.56 and 20.71 respectively, so the larger population does **not** simply have fewer absolute incumbent parent draws. Its good-lineage fraction is much lower, reproduction disrupts complete orders, and archive preservation does not preserve reproductive chromosomes.

Original replay profiles show incumbents leaving the evolving population early, while P500 retains high positional/adjacency diversity without useful improvement. Measured standardized selection intensity is not uniformly lower at P500, so tournament3 cannot be condemned from a generic population-size argument. The controlled interventions are stronger evidence: tournament5, explicit survival and their combinations substantially rescue P500. At equal expensive budgets, P100 also executes more generations; fixed-generation comparisons alone confound search dynamics and cost. These observations indicate reproducible parameter/population interactions, not intrinsic optimality of P100. ORIGINAL_SEARCH_DYNAMICS_SUMMARY.csv contains all five seeds and the successful-offspring, selected-parent and duplicate-call measurements.

## Controlled design and computational fairness

28 targeted configurations × five seeds at 50,000 distinct scores; eight focused combinations × five seeds at the same budget; three shortlisted configurations × twenty seeds at 100,000 scores. Nine operator variants × five seeds are followed by two twenty-seed confirmations. Each twenty-seed set includes five common screening seeds and fifteen additional seeds; NEW_RESTART_CONFIRMATION.csv reports these groups separately rather than calling all twenty an independent postselection validation. The original baseline and planning-only selected best confirmed configuration are extended to 500,000 queries for five common seeds, recording 50k/100k/250k/500k checkpoints. This is a staged design, not an exhaustive factorial. Initial pilot: 2,000 exact scores in 1.711 s, approximately 0.856 ms each; actual wall time additionally includes Python observations, cache and checkpoint costs.

Every fresh GA run has a separate cache. Attempted calls include duplicate rescoring; distinct queries count actual expensive calls, including reference and initialization scores. Seven-incumbent checks plus the saved-quality check during loader setup are outside the search budget and recorded separately. A budget boundary can stop inside a generation; best-observed includes all evaluated valid candidates and is explicitly separate from the archive after the last complete generation. Safety-capped runs are not represented as complete equal-budget runs. Parent frequencies are recorded by population-position fitness rank; diversity uses sixteen deterministic chromosome-pair probes plus positional entropy. Observations use no extra GA random draws.

Wall times describe searches run concurrently on this host, not standalone hardware benchmarks. Peak working-set memory is collected in isolated GA job processes. Hybrid reuses the recorded GA prefix: joint logical budget counts its prefix once plus local queries; actual new local calls are separately distinguished, preventing the same prefix being counted twice as newly executed computation. The initial local-only run did not meter peak RSS; it is unavailable rather than inferred from final cache size.

## Q2/Q3 — Operating region and practical influences

The original setting is not a uniformly good operating region. Low tournament pressure and crossover .95 can retain the incumbent without productive improvement; high mutation .40/.60 is generally worse here. Effects depend on population and other mechanisms. Do not extrapolate monotonic trends or declare one seed's minimum optimal.

{table(screen.sort_values('mean_hr'),['config_id','seeds','mean_hr','std_hr','min_hr','success_vs_impact','success_vs_previous'])}

{table(pd.read_csv(OUT/'GA_FACTOR_INFLUENCE_RANKING.csv'),['factor','observed_conditional_rank','largest_absolute_mean_conditional_effect_hr','comparison'])}

The ranking measures the largest absolute observed conditional contrast at the tested levels, including harmful changes; it is not a universal importance ordering. Initialization includes prior-quality advantage, while the budget row deliberately changes compute and is not part of equal-budget comparisons.

CONTROLLED_FACTOR_EFFECTS.csv gives five-common-seed paired effects and difference-in-differences for population×mutation, population×selection, population×elitism and crossover×mutation. Seed-bootstrap intervals there describe exploratory variability, are not physical-realization CIs and are not adjusted for many comparisons. Crossed factors are identified only at tested levels; unsampled interactions remain unresolved. The largest practical mechanisms are retaining productive chromosomes, suitable selection/crossover, and high-quality initialization. Initialization includes prior scientific search effort and must not be mistaken for a new operator discovery. The following ranking is of observed conditional contrasts, not universal variance attribution across an untested factorial. Operator changes have their own replicated confirmation and budget comparison.

{table(ranked,['factor','contrast','mean_effect_hr','std_across_seed_effect_hr'])}

{table(initial,['config_id','generation0_best_hr','final_hr','post_initialization_improvement_hr'])}

Twenty-seed confirmation at a common 100,000 queries:

{table(short,['phase','config_id','seeds','mean_hr','median_hr','std_hr','min_hr','success_vs_previous','mean_elapsed_seconds','max_peak_rss_mb'])}

Recommended next-stage configuration from these planning-only replicated results: `{recommend.config_id}` with `{json.dumps(params,sort_keys=True)}`. Mean planning loss {recommend.mean_hr:.9f} h, across-seed SD {recommend.std_hr:.9f} h. This recommendation is conditional on the existing model, sample and tested budgets, not an optimal hyperparameter certificate. Most follow-up effort should use this configuration and deterministic local refinement, retaining a small baseline allocation. Operator variants that do not show replicated benefit are not recommended merely because they are sophisticated.

## Q4 — Explicit elitism

The same independent archive is used with and without elitism. Controlled one-/three-elite tests change chromosomes surviving in the evolving population, not the definition of the reported archive. Their improved expensive-budget outcomes demonstrate an actual search effect. One elite was generally more effective than three at P100 in this screen; at P500, selection and mutation interactions matter. There is no universal elite-count rule.

## Q5 — New planning improvements and local/hybrid search

Best new recorded planning loss: **{best.planning_loss_hr:.12f} h**, improvement over previous best **{-best.mean_change_vs_previous_hr:.12f} h**. The previous best was 33.03813174326729 h and Impact-first 33.57830255999924 h. Source run: `{best.source_run}`, sequence hash `{best.sequence_sha256}`. Local-only refinement reached {local['best_planning_loss_hr']:.12f} h after {local['distinct_evaluations']:,} distinct scores and {local['accepted_moves']} strictly improving moves. Each move has before/after objective and full sequence in ACCEPTED_MOVES.json; no physical samples or scheduling definition were changed.

The staged local path accepts the best tested improving neighbor if its budget truncates a scan, then restarts from that accepted order when extended. It is therefore not claimed to be identical to uninterrupted steepest descent. The final complete swap/insertion/inversion/adjacent-short-block scan has local-optimal status `{local['local_optimal_up_to_1e_minus_9']}` at a 1e-9 h threshold. That statement is limited to these neighborhoods. Hybrid uses 50,000 GA queries plus local refinement through a joint 100,000-query cache. Its twenty-seed mean was {hybrid.best_planning_loss_hr.mean():.9f} h (SD {hybrid.best_planning_loss_hr.std():.9f}), worse than the confirmed swap variant at the same joint 100,000-query budget. Local refinement of the mixed-operator best {new_local['starting_planning_loss_hr'] if 'starting_planning_loss_hr' in new_local else new_local['best_planning_loss_hr']:.12f} h order used {new_local['distinct_evaluations']:,} queries and accepted no move; the complete tested neighborhood was locally stable at 1e-9 h. All accepted changes and the paired 64-realization outcomes are recorded; equality across chromosomes is allowed.

## Operator variants and landscape

Swap, insertion, mixed mutation, single-random-cycle and PMX crossover, adaptive mutation, stagnation restart and deterministic crowding are labeled variants. They do not constitute exact replays. Adaptive mutation ramps the base probability with 10,000-query stagnation toward .60; restart replaces approximately half the population after 10,000 stagnant queries; crowding compares offspring with the nearest selected parental pair by positional distance. All leave the evaluator unchanged.

CANDIDATE_LANDSCAPE.csv reports generated candidates excluding injected deterministic references, best score/identity/generation, exact ties and near ties at 1e-6/1e-4/1e-3/1e-2 h. A joint DS>0 order signature is injective because at least one planning sample has all 92 damaged stations; therefore filtering alone cannot collapse complete permutations across all samples. SCHEDULE_PHENOTYPE_DIAGNOSTICS.csv separately checks a bounded sample of equal/near-equal objectives for identical completion arrays. The fifty sampled near-best chromosomes in each of the shortlist and operator-confirmation checks had one completion-array identity. The three planning-selected full permutations likewise share the exact sixty-four completion arrays (SELECTED_PLANNING_SCHEDULE_IDENTITIES.csv). This establishes a schedule-induced plateau for these sampled orders, despite distinct joint damaged-task order signatures. Other equal objectives need not imply identical schedules, and none establish uniqueness of an optimum. Flat archives are not convergence certificates.

## Protected scope and outputs

All new numerical results and records are under results/diagnostics/ga_optimization_20261009. New review artwork is under results/figure_review/Additional_Evidence/GA_Optimization_20261009. Neither current Main/Supplement files nor results/figures are overwritten. The separate station/network/community mechanism should remain a companion to optimization evidence: S04 answers static criticality/dynamic LCC structure, whereas the companion traces f → fFC → population-dependent loss; these are related but distinct. S07 measures Core-source connectivity/redundancy, not delivered MW. S11 retains four-hazard context with historical/2pc50 parameterization limits; it is not a pure hazard-intensity experiment.

The prior 20261008 evaluation is complete (EVALUATION.json and SUMMARY.csv for both orders). SEARCH_DECISION.json's evaluation_started=false is a dated planning-selection snapshot, not current pending-work status, and is preserved as history. Current records point to completed exploratory evaluation. Formal replacement remains unapproved.
'''
    (OUT/'GA_HYPERPARAMETER_AND_OPERATOR_AUDIT.md').write_text(audit,encoding='utf-8')
    chosen=selected['candidates'][0]['candidate_id'];main_effect=effects[effects.candidate.eq(chosen)&effects.reference.eq('impact-first')];focus=main_effect[main_effect.source_field.isin(['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr','burden_gini','signed_Q4_minus_Q1_hr','absolute_Q4_minus_Q1_hr','population_T80_hr'])]
    general=f'''# Solution quality and generalization

## Q6 — What transfers and what remains unvalidated

No new physical samples were generated. The original objective always retains its 64 samples for full-comparison searches. Four fixed folds (split seed19371) use 48 training and 16 held-out samples; each fold has five seeds for predeclared legacy/archive-only and one-elite configurations, 25,000 distinct training scores. Held-out values never score candidates or select sequences. These fixed-algorithm diagnostics are not unbiased validation of all hyperparameters subsequently tuned on the full64.

{table(cv.groupby('elites')[['training_change_vs_impact_hr','heldout_change_vs_impact_hr']].agg(['mean','std']).reset_index().set_axis(['elites','training_mean_change','training_seed_fold_sd','heldout_mean_change','heldout_seed_fold_sd'],axis=1),['elites','training_mean_change','training_seed_fold_sd','heldout_mean_change','heldout_seed_fold_sd'])}

Training improvement exceeds held-out improvement, demonstrating selection optimism. Fold/seed values share samples and are descriptive, not forty independent validation cohorts. Subset-ranking stability on500 32-of64 subsets is explicitly postselection, not out-of-sample evidence. Extensive tuning on64 can overfit those samples; more objective queries do not increase physical sample information.

The previous exploratory candidate02 minus candidate01 on the already inspected1,000 cohort changes all-tract loss by {pair.mean_change:.9f} h (median {pair.median_change:.9f}, empirical5–95 range [{pair.p05:.9f}, {pair.p95:.9f}], 95% bootstrap mean CI [{pair.bootstrap_mean_ci95_low:.9f}, {pair.bootstrap_mean_ci95_high:.9f}]). Thus the planning ranking did not transfer unchanged. This cohort is no longer an untouched test.

Three new sequences were fixed by the predeclared planning-only rule and their hashes stored before reuse. Their new schedules and event arrays are confined to the diagnostic namespace. The reused1,000 cohort provides exploratory transport evidence; it cannot support an unbiased final performance claim after extensive author inspection. No evaluation-guided reselection is performed. All three selected orders tie at the best planning objective and have identical planning completion arrays. FIXED_CANDIDATE_PAIR_COMPARISONS.csv quantifies their small reused-cohort differences; their distinct full permutations do not represent three independently superior planning solutions. A genuinely independent final assessment would require a separately authorized new sample or other independent data, a fixed algorithm/selection rule, immutable sequence hashes, then one assessment. No such sampling was undertaken here.

## Q7 — Defensible quality statement

Best found planning loss: {best.planning_loss_hr:.12f} h. Rigorous unlimited-crew/zero-travel relaxation lower bound, conservatively rounded down from exact rational integration: **{lower:.9f} h**. The relaxation preserves the same damage/durations, threshold, Core-source connectivity and population dependency. Any feasible completion occurs no earlier than its saved duration; earlier station restoration increases raw functionality, threshold eligibility and source-connected service monotonically. Nonnegative weights make every relaxed loss integral a lower bound. RATIONAL_RELAXATION_BOUND.json records an exact fraction for the encoded inputs and downward rounding; RELAXATION_LOWER_BOUND.csv gives corresponding double-precision per-sample values.

The fixed-input mathematical optimum lies between this lower bound and the best feasible order. Remaining bound gap {best.planning_loss_hr-lower:.9f} h, or {100*(best.planning_loss_hr-lower)/best.planning_loss_hr:.3f}% of the best objective. This is a bound on the mathematical model, not an out-of-sample certificate. The lower-bound schedule relaxes logistics and is not operationally feasible. Full92 exact optimization is not claimed. All720 arrangements in a six-position conditional problem are enumerated with other86 positions fixed; that exact restricted minimum is a feasible upper bound, not a global lower bound.

Finite search and tested-neighborhood local stability do not prove global optimality or uniqueness. The strongest statement is a new best feasible sequence, replicated search distributions, diminishing/inconsistent budget improvements, neighborhood-qualified local optimality where a complete scan passed, and a valid nonzero global-bound gap. No policy is called globally optimal.

## Q8 — Restoration and community consequences

Planning-only selected candidate1 compared with Impact-first on the reused evaluation cohort:

{table(focus,['metric','mean_change','median_change','p05','p95','bootstrap_mean_ci95_low','bootstrap_mean_ci95_high'])}

Means, medians and5–95 ranges are realization-level quantities; the95% confidence intervals resample full physical realization differences10,000 times (seed641209). Optimization success refers only to aggregate planning loss. Quartile outcomes, signed Q4−Q1, mean realization-level |Q4−Q1|, Gini, hospital-linked loss, T80 and component losses are distinct outcomes and can disagree. In particular E|Q4−Q1| is not |E(Q4−Q1)|. Q4 is the highest social-vulnerability quartile, not an income category. Hospital-linked loss is an equal-tract modeled-service measure, not hospital electricity delivery or clinical capacity. Source-connected availability is dimensionless, not MW or full electrical adequacy.

Full comparisons retain Impact/Hospital/Degree/Betweenness/Vulnerability/Random/Unconstrained and both existing exploratory candidates. Station execution records distinguish fixed rank from damaged-task dispatch, completion and travel. Priority changes are descriptive algorithm outcomes, not isolated causal benefits of individual station movements. Candidate trajectories retain raw f, threshold F, connectivity C and effective e; all component/event outputs and task records are saved. Formal scientific results are unchanged.

## Manuscript-ready interpretation

Under the existing64-realization planning objective, search quality depended on selection, survival, initialization and their interactions with population size, rather than generation count alone. Controlled elitism and selection improved search efficiency, while refinement of previously found orders yielded additional reductions in modeled community service loss. Planning gains and reused-cohort effects are reported separately; aggregate improvement does not imply reductions in every group disparity or inequality measure. These finite searches and local-neighborhood checks identify improved feasible orders, not a globally optimal or unique restoration sequence.
'''
    (OUT/'GA_SOLUTION_QUALITY_AND_GENERALIZATION.md').write_text(general,encoding='utf-8')
    (OUT/'README.md').write_text('''# GA optimization diagnostic — 2026-10-09

Start with GA_HYPERPARAMETER_AND_OPERATOR_AUDIT.md and GA_SOLUTION_QUALITY_AND_GENERALIZATION.md. CSVs contain equal-budget parameters, computational accounting, diversity/selection, local/hybrid moves, planning quality and reused-cohort outcomes. Each run contains its configuration/seed, complete candidate orders/objectives, generation observations, parent frequencies and best sequence. Restart caches and worker logs are local-only; the scripts reproduce the records from protected inputs.

Run order: ga_hyperparameter_study_20261009 --stage parity/screen/focused/shortlist/operators; ga_optimization_followup_20261009 --stage confirm/budgets/hybrid; ga_local_refinement_20261009 --task local; ga_generalization_20261009 --task cv/stability/previous-pair/evaluate; summarize_ga_optimization_20261009; ga_relaxation_rational_bound_20261009; verify_ga_candidate_production_20261009; ga_schedule_phenotypes_20261009; ga_budget_identity_20261009; ga_selected_pair_20261009; ga_new_candidate_local_20261009. Use python -m la_grid.diagnostics.<module> in the installed src layout. Parameters and allocation rules are recorded in STUDY_DESIGN.md and selection JSONs. Fixed sequence selection precedes reused-cohort evaluation.

No original formal policy, scientific source, sample, mapping, gate, trajectory or manuscript figure is replaced. New review artwork: ../../figure_review/Additional_Evidence/GA_Optimization_20261009/GA_OPTIMIZATION_REVIEW_PACKET.pdf. Reused evaluation is exploratory, not an untouched test.
''',encoding='utf-8')
    print('REPORTS COMPLETE')
if __name__=='__main__':main()
