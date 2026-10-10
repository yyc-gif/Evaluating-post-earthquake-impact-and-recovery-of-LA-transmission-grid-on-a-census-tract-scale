"""Higher-budget GA parameter inference; reads completed diagnostic records only."""
from __future__ import annotations
import argparse,json
import numpy as np
import pandas as pd
from la_grid.diagnostics.ga_initialization_reconcile_20261009 import OUT,BASELINE,estimate,csv
from la_grid.diagnostics.ga_initialization_evidence_report_20261009 import table,write
from la_grid.diagnostics.ga_parameter_confirmation_20261009 import CASES,SEEDS,BUDGET
from la_grid.diagnostics.ga_search_budget_sensitivity import digest,identity

def report():
 paths=list((OUT/'parameter_100k').glob('*/RUN.json'))
 assert len(paths)==len(CASES)*len(SEEDS)==180,'Fixed experiment is incomplete'
 rows=[];points=[];moves=[]
 for path in paths:
  q=json.loads(path.read_text());assert q['status']=='COMPLETED' and q['distinct_evaluations']==BUDGET
  assert q['design_sha256']==digest(OUT/'PARAMETER_FOLLOWUP_DESIGN.json')
  for name,h in q['files_sha256'].items():assert digest(path.parent/name)==h
  assert identity(q['best_sequence'])==q['sequence_sha256']
  row={k:v for k,v in q.items() if not isinstance(v,(list,dict))};row.update(q['config']);row.update({'init_'+k:v for k,v in q['initialization'].items()});rows.append(row)
  for cp in json.loads((path.parent/'CHECKPOINTS.json').read_text()):
   points.append(dict(case=q['case'],seed=q['seed'],budget=cp['distinct_evaluations'],loss_hr=cp['best_service_loss_hr'],generation=cp['generation'],total_attempts=cp['total_attempts'],elapsed_seconds=cp['elapsed_seconds'],sequence_sha256=cp['sequence_sha256']))
  for x in json.loads((path.parent/'STRICT_IMPROVEMENTS.json').read_text()):
   moves.append(dict(case=q['case'],seed=q['seed'],distinct_evaluation=x['distinct_evaluation'],loss_hr=x['loss_hr'],sequence_sha256=x['sequence_sha256'],improvement_hr=x['improvement_hr']))
 d=pd.DataFrame(rows).sort_values(['case','seed']);p=pd.DataFrame(points);csv('PARAMETER_RUN_SUMMARY.csv',d);csv('PARAMETER_BUDGET_CHECKPOINTS.csv',p);csv('PARAMETER_STRICT_IMPROVEMENTS.csv',moves)
 base=pd.read_csv(OUT/'UNIQUE_BUDGET_CHECKPOINTS.csv');base=base[base.case.eq(BASELINE)&base.seed.isin(SEEDS)]
 baseline_runs=pd.read_csv(OUT/'UNIQUE_INITIALIZATION_OBSERVATIONS.csv');baseline_runs=baseline_runs[baseline_runs.budget.eq(100000)&baseline_runs.case.eq(BASELINE)].set_index('seed')
 effects=[];raw=[];stability=[]
 for level in [20000,50000,100000]:
  control=base[base.budget.eq(level)].set_index('seed').loss_hr;assert set(control.index)==set(SEEDS)
  for case in CASES:
   x=p[p.budget.eq(level)&p.case.eq(case)].set_index('seed').loss_hr;assert set(x.index)==set(SEEDS)
   delta=x-control;q=estimate(delta,tests=9)
   initial=d[d.case.eq(case)].set_index('seed').initial_best_loss_hr-baseline_runs.initial_best_loss_hr
   gain=(d[d.case.eq(case)].set_index('seed').initial_best_loss_hr-x)-(baseline_runs.initial_best_loss_hr-control)
   effects.append(dict(case=case,budget=level,mean_initial_change_hr=initial.mean(),mean_postinitialization_gain_change_hr=gain.mean(),mean_loss_hr=x.mean(),median_loss_hr=x.median(),sd_loss_hr=x.std(ddof=1),best_hr=x.min(),worst_hr=x.max(),pointwise_halfwidth_hr=(q['t95_high_hr']-q['t95_low_hr'])/2,family_halfwidth_hr=(q['bonferroni95_high_hr']-q['bonferroni95_low_hr'])/2,precision_target_hr=.004,**q))
   raw.extend(dict(case=case,seed=int(seed),budget=level,variant_loss_hr=x[seed],reused_baseline_loss_hr=control[seed],difference_hr=delta[seed]) for seed in SEEDS)
 for case in CASES:
  x=p[p.case.eq(case)].pivot(index='seed',columns='budget',values='loss_hr');control=base.pivot(index='seed',columns='budget',values='loss_hr')
  for low,high in [(20000,50000),(50000,100000),(20000,100000)]:
   stability.append(dict(case=case,low_budget=low,high_budget=high,mean_actual_gain_hr=(x[low]-x[high]).mean(),**estimate((x[high]-control[high])-(x[low]-control[low]),tests=9)))
 e=pd.DataFrame(effects);csv('PAIRED_PARAMETER_EFFECTS.csv',e);csv('PAIRED_PARAMETER_SEED_DIFFERENCES.csv',raw);csv('PARAMETER_BUDGET_STABILITY.csv',stability)
 summary=d.groupby('case').agg(seed_count=('seed','size'),initial_mean_hr=('initial_best_loss_hr','mean'),final_mean_hr=('final_best_loss_hr','mean'),final_sd_hr=('final_best_loss_hr','std'),median_hr=('final_best_loss_hr','median'),best_hr=('final_best_loss_hr','min'),max_hr=('final_best_loss_hr','max'),cpu_seconds=('process_cpu_seconds','sum'),objective_cpu_seconds=('objective_cpu_seconds','sum'),sum_job_wall_seconds=('job_wall_seconds','sum'),mean_run_wall_seconds=('elapsed_wall_seconds','mean'),max_peak_rss_mb=('peak_rss_mb','max'),total_attempts=('total_attempts','sum'),distinct_evaluations=('distinct_evaluations','sum'),min_generations=('actual_generation','min'),median_generations=('actual_generation','median'),max_generations=('actual_generation','max'),unique_final_permutations=('sequence_sha256','nunique')).reset_index()
 summary['duplicate_call_fraction']=1-summary.distinct_evaluations/summary.total_attempts;csv('PARAMETER_CONFIGURATION_SUMMARY.csv',summary)
 final=e[e.budget.eq(100000)].copy();final['pointwise_precision_target_met']=final.pointwise_halfwidth_hr.le(.004);final['family_precision_target_met']=final.family_halfwidth_hr.le(.004);csv('ACHIEVED_PARAMETER_PRECISION.csv',final)
 tolerances=[];decisions=[]
 for _,r in final.iterrows():
  for margin in [.0005,.001,.002,.005,.01]:tolerances.append(dict(case=r.case,budget=100000,margin_hr=margin,pointwise_interval_within_margin=bool(r.t95_low_hr>-margin and r.t95_high_hr<margin),simultaneous_interval_within_margin=bool(r.bonferroni95_low_hr>-margin and r.bonferroni95_high_hr<margin),scientifically_approved_margin=False,equivalence_established=False))
  if r.bonferroni95_high_hr<0:status='Lower mean on fixed planning objective; joint tuning and generalization untested'
  elif r.bonferroni95_low_hr>0:status='Higher mean on fixed planning objective; not preferred at this budget'
  else:status='Unresolved; neither superiority nor equivalence established'
  decisions.append(dict(case=r.case,effect_hr=r.mean_change_hr,simultaneous_low_hr=r.bonferroni95_low_hr,simultaneous_high_hr=r.bonferroni95_high_hr,status=status))
 csv('PARAMETER_TOLERANCE_PRECISION.csv',tolerances);csv('PARAMETER_DECISION_TABLE.csv',decisions)
 write('HIGHER_BUDGET_PARAMETER_EVIDENCE.md',f'''
# Bounded higher-budget parameter evidence

Nine one-factor variants, twenty GA seeds (100-119), 100,000 distinct expensive objective evaluations per run. The twenty controls are reused from Actions 38006365076, with exact initial-population hash parity and evaluator/model source parity verified. Five additional historical seed controls (42-46) were replayed to20k from their saved local objective caches, with zero new fitness evaluations: all reproduced the cloud best-sequence identity and objective error was at most 1.422e-13 h. This supports comparability for those five checks, not a claim of bitwise local replay of all100k controls100-119. Baseline: population 100, ordered crossover 0.80, swap mutation 0.10, tournament 3, one surviving elite, seven heuristic seeds, one exact inherited chromosome, 25 inversion neighbors and 67 random permutations. The inherited chromosome and 64 original planning samples retain their identities. The kernel retains H_plan = 2855.2540131100995 h; the existing order-independent planning-horizon audit establishes zero post-480 loss for these fixed inputs, so the endpoint is equivalent to 0-480 h here. Neither the kernel horizon nor the objective was changed.

`PARAMETER_FOLLOWUP_DESIGN.json` was committed at 62459f947e978fa3c6ce81e929dfa06f1abf5b14 before any new parameter result. The maximum five-seed 20k screening SD predicts a pointwise half-width of 0.003740 h at twenty seeds, against a predeclared 0.004 h optimizer-estimation precision target. The target resolves roughly one tenth of the previously observed post-warm-start gain; it is not a scientific equivalence margin. Pilot variance is imprecise and may not transfer to 100k. Actual precision is reported below; twenty seeds are not automatically sufficient.

## Final fixed-budget effects

Variant minus same-seed reference, h; negative favors the variant. Intervals concern expected GA search outcome conditional on the same repeatedly used 64 planning realizations. Bootstrap uses 50,000 whole GA-seed resamples. Bonferroni t intervals cover nine final-budget contrasts. The 20k/50k checkpoints are repeated-budget descriptions, not new independent seeds, and their intervals are not simultaneous bands across all budgets.

{table(final,['case','mean_loss_hr','mean_initial_change_hr','mean_postinitialization_gain_change_hr','mean_change_hr','t95_low_hr','t95_high_hr','bootstrap95_low_hr','bootstrap95_high_hr','bonferroni95_low_hr','bonferroni95_high_hr','pointwise_halfwidth_hr'])}

{table(pd.DataFrame(decisions),['case','effect_hr','simultaneous_low_hr','simultaneous_high_hr','status'])}

## Population initialization counts

| Population | Heuristics | Exact prior copies | Prior neighbors | Impact neighbors | Random | Elites |
| --- | --- | --- | --- | --- | --- | --- |
| 50 | 7 | 1 | 6 | 6 | 30 | 1 |
| 100 | 7 | 1 | 13 | 12 | 67 | 1 |
| 250 | 7 | 1 | 31 | 31 | 180 | 1 |
| 500 | 7 | 1 | 63 | 62 | 367 | 1 |

Neighbor count follows the existing floor(population/4) rule. Seven heuristic chromosomes and one exact inherited copy remain fixed counts; random permutations fill the remainder. Heuristic, exact-copy and elite percentages therefore decrease with population size. These are conditional population-plus-composition effects, not a pure population effect at fixed percentages. The initialization experiments do not justify this allocation as optimal; it remains the explicit common comparison recipe.

## Cost and budget stability

{table(summary,['case','seed_count','distinct_evaluations','total_attempts','duplicate_call_fraction','min_generations','median_generations','max_generations','cpu_seconds','mean_run_wall_seconds','max_peak_rss_mb'])}

All 180 new searches completed 100k distinct queries: 18,000,000 expensive search evaluations, plus 1,440 documented setup-parity scores outside the budgets. Cached attempts still incur overhead. Cloud-control and local-worker wall times are from different hardware/concurrency and are not a controlled hardware-efficiency comparison. Actual completed/partial generation counts are recorded; no common generation count is invented.

The first coordinator used six workers. Additional twelve-worker, six-worker and four-worker coordinators accelerated the same fixed jobs with atomic process claims. There were at most twenty-eight allocated process slots; some slots only waited on an owner or reused a completed record, so this is not a measured peak active-compute count. An overlapping process waits or reuses the completed observation; it does not repeat its search. Coordinator process counts must not be summed as new scientific observations. Per-run deduplicated records are the cost authority.

Pointwise precision target met for {int(final.pointwise_precision_target_met.sum())}/9 contrasts; simultaneous precision target met for {int(final.family_precision_target_met.sum())}/9. No seed count was enlarged in response to a p-value. `PARAMETER_BUDGET_STABILITY.csv` reports higher-minus-lower-budget changes in variant-control effects within the same twenty seeds.

## Recommendation scope

The decision table can favor or disfavor tested conditional one-factor packages on this planning objective at 100k. It does not justify combining individually favorable settings without a joint test, extrapolating across budgets, or claiming exact initialization percentages are optimal. A nonzero effect is not necessarily scientifically consequential; no prospective scientific tolerance was approved. For unresolved contrasts, retain the existing comparison setting rather than picking the lowest mean. No new setting is promoted automatically.

Population 100 / crossover 0.80 / swap 0.10 / tournament 3 / one elite remains the stable reporting reference, with initialization disclosed as a working recipe. A reproducibly favorable conditional alternative is reported as a diagnostic option, with its interval and variability. Method/candidate replacement requires author approval. New operators, interactions, true no-prior/archive controls and physical-sample generalization were not tested here.

All selected-permutation identities remain diagnostic. No new physical samples, proposed independent validation, formal strategy replacement or manuscript-artwork change occurred.
''')
 return d,e,summary


def plot():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.font_manager import findfont,FontProperties
 findfont(FontProperties(family='Arial'),fallback_to_default=False)
 plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.titlesize':9.5,'axes.labelsize':8.5,'xtick.labelsize':7.5,'ytick.labelsize':7.5,'legend.fontsize':7.5,'axes.linewidth':.6,'pdf.fonttype':42,'savefig.facecolor':'white'})
 effects=pd.read_csv(OUT/'PAIRED_INITIALIZATION_EFFECTS.csv');budget=pd.read_csv(OUT/'SAME_20_SEED_BUDGET_STABILITY.csv');parameters=pd.read_csv(OUT/'PAIRED_PARAMETER_EFFECTS.csv')
 fig,axes=plt.subplots(2,2,figsize=(240/25.4,185/25.4),layout='constrained')
 names=['heuristics_only','heuristics_0','warm_copies_0','neighbors_0','neighbors_50'];labels=['No prior / local neighbors','No evolving heuristic copies','No exact prior copy','No neighbors','50 neighbors']
 ax=axes[0,0]
 for level,offset,color,marker in [(20000,-.13,'#477A9D','o'),(100000,.13,'#B96C35','s')]:
  x=effects[effects.budget.eq(level)].set_index('case')
  for j,name in enumerate(names):
   if name not in x.index:continue
   r=x.loc[name];ax.errorbar(r.mean_change_hr,j+offset,xerr=[[r.mean_change_hr-r.t95_low_hr],[r.t95_high_hr-r.mean_change_hr]],fmt=marker,color=color,ms=3,capsize=2,lw=.9,label=f'{level//1000}k queries' if j==0 else None)
 ax.axvline(0,color='.35',lw=.6);ax.set_yticks(range(5),labels);ax.invert_yaxis();ax.set_xlabel('Change from reference mixture (h)');ax.set_title('A   Initialization effects',loc='left');ax.legend(loc='lower right',frameon=False)
 ax=axes[0,1];z=parameters[parameters.budget.eq(100000)].sort_values('mean_change_hr');y=np.arange(len(z))
 ax.errorbar(z.mean_change_hr,y,xerr=np.vstack([z.mean_change_hr-z.t95_low_hr,z.t95_high_hr-z.mean_change_hr]),fmt='o',ms=3,color='#477A9D',capsize=2,lw=.9)
 ax.hlines(y,z.bonferroni95_low_hr,z.bonferroni95_high_hr,color='.6',lw=.6)
 labels=[f'Crossover {CASES[k]["crossover"]:.2f}' if k.startswith('crossover') else f'Swap probability {CASES[k]["mutation"]:.2f}' if k.startswith('mutation') else f'Tournament {CASES[k]["tournament"]}' if k.startswith('tournament') else f'Population {CASES[k]["population"]}' for k in z.case]
 ax.axvline(0,color='.35',lw=.6);ax.set_yticks(y,labels);ax.set_xlabel('Change from reference at 100k (h)');ax.set_title('B   Parameter effects',loc='left');ax.invert_yaxis()
 ax=axes[1,0]
 for case,label,color in [('baseline_7h_1w_25n','Reference mixture','#477A9D'),('heuristics_only','No prior / local neighbors','#B96C35'),('neighbors_0','No neighbors','#538775')]:
  x=budget[budget.case.eq(case)&budget.budget.isin(['20000','50000','100000'])]
  ax.plot(x.budget.astype(int)/1000,x.mean_loss_hr,'o-',label=label,color=color,lw=1,ms=3)
 ax.set_xlabel('Distinct evaluations per run (thousands)');ax.set_ylabel('Mean best planning service loss (h)');ax.set_title('C   Same 20 seeds at all budgets',loc='left');ax.legend(frameon=False)
 ax=axes[1,1];q=parameters[parameters.budget.eq(100000)].sort_values('pointwise_halfwidth_hr');y=np.arange(len(q))
 ax.plot(q.pointwise_halfwidth_hr,y,'o',ms=3,color='#477A9D',label='Pointwise 95%');ax.plot(q.family_halfwidth_hr,y,'s',ms=3,color='.5',label='Simultaneous 95%');ax.axvline(.004,color='#B96C35',ls='--',lw=.8,label='Estimation precision target')
 labels=[f'Crossover {CASES[k]["crossover"]:.2f}' if k.startswith('crossover') else f'Swap probability {CASES[k]["mutation"]:.2f}' if k.startswith('mutation') else f'Tournament {CASES[k]["tournament"]}' if k.startswith('tournament') else f'Population {CASES[k]["population"]}' for k in q.case]
 ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlabel('Mean-effect interval half-width (h)');ax.set_title('D   Achieved seed precision',loc='left');ax.legend(frameon=False)
 fig.savefig(OUT/'GA_INITIALIZATION_AND_PARAMETER_EVIDENCE.pdf');fig.savefig(OUT/'GA_INITIALIZATION_AND_PARAMETER_EVIDENCE.png',dpi=300);plt.close(fig)
 write('GA_INITIALIZATION_AND_PARAMETER_EVIDENCE_CAPTION.md','''Diagnostic GA evidence conditional on the original 64 planning realizations. A: same-seed initialization differences at 20k/100k; no 100k warm-copy comparison was run. Points are means and colored ranges are pointwise 95% paired-seed t intervals. B: 100k parameter effects; gray ranges are simultaneous Bonferroni intervals for nine final-budget comparisons. Negative values favor the variant. C: means at repeated checkpoints of the same twenty searches, not additional independent replicates. D: achieved mean-effect precision against the 0.004 h optimizer-estimation target, which is not a scientific equivalence margin. No physical validation or method promotion is shown.''')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--plot',action='store_true');a=p.parse_args();report()
 if a.plot:plot()
