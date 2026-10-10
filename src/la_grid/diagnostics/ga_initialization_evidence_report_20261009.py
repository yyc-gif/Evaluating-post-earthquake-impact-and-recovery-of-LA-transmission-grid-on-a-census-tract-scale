"""Report reconciled GA evidence without modifying any scientific authority."""
from __future__ import annotations
import argparse,hashlib,json,random,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from la_grid.paths import REPO_ROOT as ROOT
from la_grid.diagnostics.ga_initialization_reconcile_20261009 import OUT,BASELINE,CASES,CONFIRM,DIAG_BASE,REVISION_BASE,estimate,csv,dump

def table(frame,fields,places=6):
 def render(v):
  if isinstance(v,(float,np.floating)):return f'{v:.{places}f}' if np.isfinite(v) else ''
  return str(v)
 return '| '+' | '.join(fields)+' |\n| '+' | '.join(['---']*len(fields))+' |\n'+'\n'.join('| '+' | '.join(render(row[k]) for k in fields)+' |' for _,row in frame.iterrows())

def write(name,text):(OUT/name).write_text(text.strip()+'\n',encoding='utf-8')

def init_report():
 d=pd.read_csv(OUT/'UNIQUE_INITIALIZATION_OBSERVATIONS.csv');effects=pd.read_csv(OUT/'PAIRED_INITIALIZATION_EFFECTS.csv');s=pd.read_csv(OUT/'INITIALIZATION_SUMMARY.csv');b=pd.read_csv(OUT/'SAME_20_SEED_BUDGET_STABILITY.csv')
 composition=[dict(case=k,heuristics=h,exact_prior_copies=w,inversion_neighbors=n,prior_derived_neighbors=p,impact_derived_neighbors=n-p,random_permutations=100-h-w-n) for k,(h,w,n,p) in CASES.items()]
 csv('INITIALIZATION_ALLOCATION_AUDIT.csv',composition)
 ext=s.loc[s.budget.eq(100000)].copy();ext['mean_minus_20k_same_seeds_hr']=[b.loc[b.case.eq(k)&b.budget.eq('100000'),'mean_loss_hr'].iloc[0]-b.loc[b.case.eq(k)&b.budget.eq('20000'),'mean_loss_hr'].iloc[0] for k in ext.case]
 precision=effects.copy();precision['pointwise_halfwidth_hr']=(precision.t95_high_hr-precision.t95_low_hr)/2;precision['family_halfwidth_hr']=(precision.bonferroni95_high_hr-precision.bonferroni95_low_hr)/2
 csv('INITIALIZATION_PRECISION_SUMMARY.csv',precision)
 worst=precision.loc[precision.budget.eq(20000),'pointwise_halfwidth_hr'].max();worst100=precision.loc[precision.budget.eq(100000),'pointwise_halfwidth_hr'].max()
 write('INITIALIZATION_EVIDENCE_AND_LIMITATIONS.md',f'''
# Initialization evidence and remaining uncertainty

Revision source: `{REVISION_BASE}`. Diagnostic source: `{DIAG_BASE}`. This analysis uses the completed cloud artifacts, not reruns of their GA batches. Lower planning service loss is better. All estimates concern GA randomness conditional on the same 64 saved 2pc50 planning realizations and the unchanged evaluator, scheduler, mapping and source gate. They are not uncertainty estimates for a new earthquake cohort. The original H_plan = 2855.2540131100995 h is retained; the existing planning-horizon audit establishes equivalence to the 0-480 h endpoint for these fixed inputs, and no new horizon or normalization is imposed.

## Reconciliation and observation unit

Actions [38006187607](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38006187607) contains 17 configurations for each of seeds 100-129 at 20,000 distinct queries: 510 runs. Actions [38006365076](https://github.com/yyc-gif/Evaluating-post-earthquake-impact-and-recovery-of-LA-transmission-grid-on-a-census-tract-scale/actions/runs/38006365076) contains five configurations for each of seeds 100-119 at 100,000 queries: 100 runs. All 50 artifact archives match their GitHub SHA-256 digests. `CLOUD_ARTIFACT_MANIFEST.json` records immutable source commits, IDs, archive hashes and members.

There are 610 unique final-budget run observations. The 610 per-case JSON copies and 543 previously committed partial-chunk records repeat these observations and are excluded from the analytic dataset. Their immutable sources remain available. The 100 repeated 20k prefixes have identical initial-population hashes; 90 objectives agree bitwise and ten differ by at most 2.274e-13 h (comparison tolerance 1e-10 h). Their prefix records are not counted as additional replicates. The high-budget source asserts both 100k expensive calls and 100k cache entries before exporting each record. Its field named `completed_generations` actually exports the current state generation, which may be partial; the reconciled table flags this and does not claim to know the last fully completed generation.

There are 30 distinct seed identities; the 20 higher-budget seeds are a subset, not 20 additional independent identities. Thirty plus twenty is not a 50-seed study. Actual search-query cost was 20.2 million per-run distinct objective calls; 2.0 million are paid replays of the 20k prefixes. Removing those prefixes leaves 18.2 million query-path entries, not a claim of globally unique permutations across runs.

## What was changed

{table(pd.DataFrame(composition),list(pd.DataFrame(composition).columns),0)}

All cases preserve ordered crossover 0.80, swap mutation 0.10, tournament size 3, one surviving elite, population 100, and a separately preserved heuristic incumbent archive. Each chromosome is a complete 92-station permutation. The seven original heuristic seeds include the saved Random rule as one deterministic seeded sequence; it differs from newly sampled uniform random permutations. The three-heuristic case seeds Impact-first, Hospital-first and Closeness-first. Changes to counts replace slots that would otherwise contain random permutations. Neighbor-source changes also alter the exact initialization and subsequent RNG stream.

The neighbor-source labels 25% and 75% are nominal: rounding gives 6/25 = 24% and 19/25 = 76% prior-derived neighbors. The alternating baseline gives 13/25 = 52%, not exactly 50%. Exact counts in the table govern reproduction.

The inherited sequence is the previous p100/g2000/seed46 result, J = 33.03813174326729 h, SHA-256 `3bfeafdd1adf950749e63fdbbe3b7efc21b1efd04c3b3d64c28c3d118717bbed`. Its earlier discovery cost is inherited development effort and is not included in these new run budgets. The seven-heuristic archive begins with Impact-first, J = 33.57830255999924 h.

## Control limitations

- `heuristics_0` removes the heuristic chromosomes from the evolving initial population. All seven heuristics are still evaluated and the best heuristic is retained in the archive. Twelve Impact-derived neighbors also remain. This is not removal of heuristic information.
- `warm_copies_0` removes only the exact prior-best chromosome. Thirteen inversion neighbors of that chromosome remain. This is not removal of all inherited GA information.
- `heuristics_only` removes the exact inherited sequence and all local neighbors, including Impact-derived neighbors; seven heuristic chromosomes and 93 uniform random permutations remain, with the same heuristic archive. It is a joint package comparison, not a clean isolated estimate of the exact warm-copy effect.
- `neighbors_0` retains the exact inherited sequence and all seven heuristics. It tests whether these local neighbors help at a given budget, not whether warm starts help.
- Repeated warm copies consume population slots but do not multiply expensive objective calls for the identical permutation because of caching.

These are one-factor composition contrasts conditional on a fixed population size. They do not identify independent additive contributions of all counts or their interactions. Same seed pairs provide a valid comparison across search realizations, but do not guarantee identical post-initialization random draws.

## Paired effects, not a lowest-mean contest

Variant minus 7/1/25/67 baseline, h; negative favors the variant. Pointwise intervals are paired GA-seed t intervals. The CSV also contains 50,000-resample percentile-bootstrap intervals, familywise Bonferroni t intervals, medians and seed-level differences. The family contains 16 contrasts at 20k and four at 100k. These comparisons remain conditional and exploratory; the experiment was not preregistered with a scientific equivalence margin.

{table(effects,['budget','case','mean_change_hr','t95_low_hr','t95_high_hr','bootstrap95_low_hr','bootstrap95_high_hr','bonferroni95_low_hr','bonferroni95_high_hr'])}

At 20k, the package without inherited GA information and local neighbors performs worse by 0.007447 h on average, with pointwise 95% interval [0.005322, 0.009572] h and simultaneous interval [0.004098, 0.010796] h. Initial best loss is worse by 0.540171 h, while evolutionary improvement after initialization is greater by 0.532724 h. Most of the initial advantage is recovered during search; the final advantage is much smaller than the generation-zero difference.

At 100k, the same package difference shrinks to 0.001609 h: pointwise interval [0.000111, 0.003107], bootstrap [0.000271, 0.003022], simultaneous interval [-0.000365, 0.003583] h. Report all three; the familywise result does not establish a residual package effect at this budget. It also does not establish equivalence. In the same twenty seeds, this contrast shrinks by 0.006069 h from 20k to 100k, with pointwise interval [-0.008856, -0.003281] h.

Removing the exact warm copy while retaining its neighbors initially raises mean loss by 0.007430 h. Its final 20k change is -0.000397 h, interval [-0.001663, 0.000870]. Changing heuristic counts, exact-copy counts, neighbor counts or neighbor sources produces unresolved small final effects. No result identifies 7/1/25/67, 25% neighbors, one copy or a particular neighbor-source split as optimal. The best 20k mean belongs to the nominal 75%-prior-neighbor case (19 of 25 neighbors), but that observation alone is not a reproducible selection rule.

## Computational-budget dependence

The following 100k values use the same twenty seeds at each checkpoint, not the thirty-seed 20k aggregate.

{table(ext,['case','initial_mean_hr','final_mean_hr','final_sd_hr','best_hr','mean_minus_20k_same_seeds_hr'])}

The baseline mean falls from 33.004183 h at 20k to 33.000503 h at 50k and 33.000185 h at 100k. Initialization-package advantage declines with more search, whereas other allocation differences remain unresolved. The higher-budget experiment covers only five initialization cases; claims about warm-copy counts and the remaining source fractions at 100k are unsupported.

The best individual higher-budget observation is 32.997722786 h (`neighbors_0`), below the currently recorded formal method candidate value. This is an exploratory initialization-search observation, not an authorized replacement. A single best seed is neither a mean-performance comparison nor independent physical validation.

## What thirty seeds establish

The widest pointwise mean-effect half-width is {worst:.6f} h at 20k and {worst100:.6f} h at 100k. Precision varies by contrast, and larger-budget evidence has fewer seeds. `PRACTICAL_TOLERANCE_PRECISION.csv` tests descriptive containment in +/-0.0005, 0.001, 0.002, 0.005 and 0.010 h, for pointwise and simultaneous intervals. No such margin was prospectively approved as scientifically negligible, so `equivalence_established` is false throughout.

At a hypothetical +/-0.001 h tolerance, the 100k interval for `heuristics_0` lies inside the margin pointwise but its simultaneous interval extends outside it; the neighbor-count contrasts are unresolved at that margin. An author-specified, scientifically defended tolerance and an appropriate equivalence design would be required for an equivalence claim. Failure to reject zero is not evidence of equality, and thirty seeds do not certify future-seed reliability or generalization beyond the planning inputs.

## Initialization recommendation

Use the existing 7/1/25/67 mixture as a documented comparison reference while the separate parameter study is completed, not as a newly validated optimum. Preserve the exact prior-best input identity and disclose its discovery history. The 20k evidence supports a finite-budget advantage of the inherited-information package; exact allocation percentages are indistinguishable or unresolved at the achieved precision. No tuning used the proposed independent physical-validation cohort. No new physical samples, formal strategy or manuscript artwork were changed.
''')


def screening():
 path='results/diagnostics/ga_parameter_followup_20261009/SCREENING_DATA.json'
 data=json.loads(subprocess.check_output(['git','show',DIAG_BASE+':'+path],cwd=ROOT));rows=data['records'];unique={};dup=[]
 for row in rows:
  # The two named baseline records use the same initializer and random stream.
  key=(row['seed'], 'shared_baseline' if row['case']=='baseline' else row['phase']+':'+row['case'])
  if key in unique:
   a=unique[key]
   for field in ['final_best_loss_hr','initial_best_loss_hr','sequence_sha256','expensive_evaluations','total_attempts']:assert a[field]==row[field],field
   dup.append(dict(seed=row['seed'],excluded_phase=row['phase'],retained_phase=a['phase'],reason='Exact same-seed baseline search; runtime not an independent effect'))
  else:unique[key]=row
 assert len(rows)==90 and len(unique)==85 and len(dup)==5
 csv('PREVIOUS_SCREENING_UNIQUE_OBSERVATIONS.csv',list(unique.values()));csv('PREVIOUS_SCREENING_DUPLICATES.csv',dup)
 p=pd.DataFrame([x for x in rows if x['phase']=='parameters']);base=p[p.case.eq('baseline')].set_index('seed');contrasts=[]
 for case,z in p.groupby('case'):
  if case=='baseline':continue
  a=z.set_index('seed');v=a.final_best_loss_hr-base.final_best_loss_hr
  contrasts.append(dict(case=case,budget=20000,**estimate(v,tests=8)))
 csv('PREVIOUS_PARAMETER_SCREEN_PAIRED_EFFECTS.csv',contrasts)
 return data


def parity_and_sources():
 from la_grid.diagnostics.ga_variant_engine import Variant,initialize
 config=json.loads((ROOT/'results/diagnostics/final_ga_method_20261009/FINAL_GA_CONFIG_CANDIDATE.json').read_text())
 formal=json.loads((ROOT/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']
 inc={k:tuple(formal[k]) for k in config['initialization']['deterministic_order']};prior=tuple(config['initialization']['prior_best_sequence']);domain=tuple(config['chromosome']['station_ids']);controls=pd.read_csv(OUT/'UNIQUE_INITIALIZATION_OBSERVATIONS.csv');rows=[]
 v=Variant(population=100,crossover=.8,mutation=.1,tournament=3,elites=1,initialization='quality_mix',mutation_operator='swap')
 for seed in range(100,120):
  population=initialize(domain,inc,random.Random(seed),v,prior)
  h=hashlib.sha256(('\n'.join('|'.join(x) for x in population)+'\n').encode()).hexdigest()
  expected=controls[controls.budget.eq(100000)&controls.case.eq(BASELINE)&controls.seed.eq(seed)].iloc[0]
  assert h==expected.initial_population_sha256
  rows.append(dict(seed=seed,current_initializer_sha256=h,cloud_initializer_sha256=expected.initial_population_sha256,exact_equal=True,expensive_search_queries=0))
 csv('REUSED_BASELINE_INITIALIZER_PARITY.csv',rows)
 names=['src/la_grid/diagnostics/ga_variant_engine.py','src/la_grid/diagnostics/ga_search_budget_sensitivity.py','src/la_grid/revision/r1_ga_revision.py','src/la_grid/revision/r1_ga_exact_kernel.py','src/la_grid/revision/r1_realization_scheduling.py','src/la_grid/revision/r1_equity_amendment_execute.py']
 rows=[]
 for name in names:
  base=subprocess.check_output(['git','show',DIAG_BASE+':'+name],cwd=ROOT);local=(ROOT/name).read_bytes().replace(b'\r\n',b'\n');assert local==base.replace(b'\r\n',b'\n'),name
  rows.append(dict(file=name,diagnostic_base_sha256=hashlib.sha256(base).hexdigest(),current_sha256=hashlib.sha256(local).hexdigest(),equal_after_line_endings=True))
 dump('REUSED_CONTROL_SOURCE_PARITY.json',dict(files=rows,no_model_changes=True,baseline_queries_rerun=0,validation_cohort_used=False,initialization_prior_sha256=config['initialization']['prior_best_sha256']))


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--initialization',action='store_true');args=parser.parse_args()
 if args.initialization:init_report();screening();parity_and_sources()

if __name__=='__main__':main()
