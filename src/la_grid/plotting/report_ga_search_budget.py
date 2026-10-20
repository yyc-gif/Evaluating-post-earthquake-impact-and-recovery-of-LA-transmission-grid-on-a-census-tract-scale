"""Report and visualize completed GA-budget diagnostics; never execute a search."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tempfile
import numpy as np
import pandas as pd
import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from la_grid.paths import REPO_ROOT
from la_grid.plotting import apply_supplement_review_and_ga_diagnostic as display
from la_grid.plotting.apply_outcome_display_feedback import sha,update_csv
from la_grid.plotting.apply_map_metric_identity_feedback import export,packets

ROOT=REPO_ROOT
OUT=ROOT/'results/diagnostics/ga_search_budget_20261007'
REVIEW=ROOT/'results/figure_review'
REPORT=ROOT/'docs/reviewer/GA_SEARCH_BUDGET_SENSITIVITY_20261007.md'

S04=('Figure S04 compares structural fragmentation under station removal with structural recovery under the evaluated restoration policies. '
 '(A) Static station-removal curves start from the intact 92-node graph and measure the largest connected component after targeted or random removals. '
 'Network λ2 impact is the spectral topology-impact removal metric, not the population-impact ranking used by the restoration policy Impact-first. '
 'These attack curves diagnose structural criticality; they do not identify an optimal repair order. '
 '(B/C) Recovery curves use 1,000 2pc50 realizations per policy, 57 crews and repair-duration multiplier 1.00, displayed over 0–120 h. '
 'For each realization and time, the functional network is the induced subgraph of stations with modeled functionality at least 0.5; edges join functional endpoints. '
 'B is the mean of |LCC|/92, with the original 92-station count as denominator. C is the mean of 2E_LCC/N_LCC, where E_LCC counts edges with both endpoints in that realization’s largest component. '
 'Empty networks contribute zero, and a singleton has degree zero. The means are taken after calculating each realization’s component; they are not metrics of an average network. '
 'No confidence interval or realization range is encoded. The curves converge toward the intact graph, whose mean degree is 636/92 = 6.913. '
 'Unconstrained develops its largest component sooner, while scheduled policies differ in the evolution of component size and internal degree. '
 'Structural connectivity alone does not establish community service-loss ordering, optimal restoration, delivered MW or electrical adequacy. '
 'Unlike S04, S07 asks whether functional stations can reach an active Core source and how alternate routes improve source reachability relative to a fixed precomputed path. '
 'A large component in S04 need not contain an active Core source. S04 therefore describes network structure, while S07 describes source-connected service and route redundancy.')
S06=('Supplementary Figure S6 tests dependency and service-model assumptions, including the tract–substation mapping-weight cutoff, '
 'agreement with public SCE assignments for 337 comparable tracts, source-connectivity gating, and the station functionality threshold. '
 'The public-record comparison provides supporting agreement, not feeder validation or service-territory ground truth. '
 'Sensitivity contrasts retain the production mapping and physical realizations except for the stated assumption; they do not create another production mapping.')

def table(frame,fields):
 lines=['| '+' | '.join(label for col,label in fields)+' |','| '+' | '.join('---' for _ in fields)+' |']
 for row in frame.to_dict('records'):
  vals=[]
  for col,label in fields:
   value=row[col]
   vals.append(f'{value:.9f}' if isinstance(value,float) else str(value))
  lines.append('| '+' | '.join(vals)+' |')
 return '\n'.join(lines)

def caption5(data):
 extended=data[data.generations.eq(250)];best=extended.loc[extended.delta_J_hr.idxmin()]
 return ('Genetic algorithm (GA) searches used the same 64 2pc50 planning realizations and direct population-weighted service-loss objective. '
 '(A) Best generated candidate excluding all seven fixed-rule incumbent permutations, by generation, for seeds 42–46 at population 100 and 100 generations. '
 '(B) Final best generated candidates from population 100 and 250 generations for 20 seeds (42–61); original 100-generation results are also shown for seeds 42–46. '
 'The black dashed reference is Impact-first (33.578 h). The initial population includes the seven incumbent sequences, and the archive is initialized with the best incumbent before generation 0. '
 'The archive is replaced only by a strictly better candidate. Thus the identical retained sequence in the original five searches means that no tested candidate improved Impact-first within that budget; it does not mean the searches independently rediscovered its permutation. '
 f'Extending to 250 generations yielded strict improvements in {int(extended.strictly_improved_incumbent.sum())} of 20 seeds, with best reduction {best.improvement_hr:.3f} h ({best.improvement_percent:.2f}%). '
 'Generated candidates and retained archives are different: a worse generated result does not displace the incumbent. '
 'Planning loss uses the same pre-search horizon of 2,855.254 h, distinct from the 480 h evaluation window. Seed points encode individual search results, without an uncertainty interval. '
 'The original retained Impact-first order remains the order used in the policy evaluation; expanded-budget sequences have not been evaluated on its 1,000-realization set. '
 'These finite-budget comparisons do not establish global optimality.')

def make_figure(data):
 display.TEMP.mkdir(exist_ok=True);display.original('Supplement/FigS05')
 fig,axes=plt.subplots(2,1,figsize=(185/25.4,150/25.4));fig.subplots_adjust(left=.14,right=.985,bottom=.12,top=.93,hspace=.62)
 colors=['#366e9f','#00856a','#a65628','#9a7559','#70818d']
 inc=float(data.best_incumbent_service_loss_hr.iloc[0]);a,b=axes
 for seed,color in zip(range(42,47),colors):
  h=pd.read_csv(OUT/f'p100_g100_s{seed}/HISTORY.csv')
  a.plot(h.generation,-h.non_incumbent_best_so_far,color=color,lw=1.2,label=f'Seed {seed}')
 a.axhline(inc,color='black',ls='--',lw=1.1,label='Impact-first incumbent')
 a.set_title('A. Generated candidates: original search budget',loc='left');a.set_xlabel('Generation');a.set_ylabel('Planning service loss (h)');a.set_xlim(0,100)
 a.legend(ncol=3,frameon=False,loc='upper right',columnspacing=1.0,handletextpad=.4)
 expanded=data[data.generations.eq(250)].sort_values('seed');baseline=data[data.generations.eq(100)].sort_values('seed')
 b.scatter(expanded.seed+.11,expanded.best_non_incumbent_service_loss_hr,s=22,marker='s',color='#366e9f',zorder=3,label='250 generations')
 b.scatter(baseline.seed-.11,baseline.best_non_incumbent_service_loss_hr,s=22,marker='o',color='#70818d',zorder=3,label='100 generations (42–46)')
 b.axhline(inc,color='black',ls='--',lw=1.1,label='Impact-first incumbent')
 b.set_title('B. Generated candidates: extended budget and restarts',loc='left');b.set_xlabel('Seed');b.set_ylabel('Planning service loss (h)');b.set_xticks(range(42,62));b.set_xlim(41.4,61.6)
 b.legend(ncol=3,frameon=False,loc='upper right',columnspacing=.9,handletextpad=.4)
 for ax in axes:
  ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',color='#e5e5e5',lw=.4)
 p=display.TEMP/'ga_budget_diagnostic.pdf';fig.savefig(p);plt.close(fig)
 record=export(fitz.open(p),'Supplement/FigS05',{'change':'Show generated candidates excluding all seven incumbents, original budget and 20 expanded-budget seeds; formal strategy unchanged.'})
 for ext in ['.pdf','.png']:shutil.copy2((REVIEW/'Supplement/FigS05').with_suffix(ext),OUT/f'GA_SEARCH_BUDGET_DIAGNOSTIC{ext}')
 display.integrate([record]);return record

def main():
 assert json.loads((OUT/'SEARCH_DECISION.json').read_text())['status']=='COMPLETE'
 data=pd.read_csv(OUT/'GA_SEARCH_BUDGET_SENSITIVITY.csv');assert len(data)==25
 inp=json.loads((OUT/'INPUT_IDENTITY.json').read_text());extended=data[data.generations.eq(250)];baseline=data[data.generations.eq(100)]
 assert set(extended.seed)==set(range(42,62));assert len(baseline)==5
 best=extended.loc[extended.delta_J_hr.idxmin()];folder=OUT/f'p100_g250_s{int(best.seed)}'
 differences=pd.read_csv(folder/'PLANNING_DIFFERENCES.csv')
 assert len(differences)==64 and abs(differences.change_hr.mean()-best.delta_J_hr)<1e-10
 # Audit logged candidate tables without another objective evaluation.
 cache={};land=[];artifacts=0
 for row in data.to_dict('records'):
  run=OUT/f"p{int(row['population'])}_g{int(row['generations'])}_s{int(row['seed'])}"
  result=json.loads((run/'RUN.json').read_text())
  for name,digest in result['artifacts_sha256'].items():assert sha(run/name)==digest;artifacts+=1
  with np.load(run/'CANDIDATES.npz') as z:
   orders=z['orders'];fitness=z['fitness'];non=z['non_incumbent'];generation=z['first_generation']
   assert np.all(np.sort(orders,axis=1)==np.arange(92)[None,:]);assert len({x.tobytes() for x in orders})==len(orders)
   assert len(orders)==row['unique_candidates_evaluated']
   assert abs(-fitness[non].max()-row['best_non_incumbent_service_loss_hr'])<1e-10
   for order,f in zip(orders,fitness):
    key=order.tobytes()
    if key in cache:assert abs(cache[key]-f)<1e-12
    cache[key]=float(f)
   land.append({'population':row['population'],'generations':row['generations'],'seed':row['seed'],
    'unique_permutations':len(orders),'unique_exact_fitness_values':len(np.unique(fitness)),
    'distinct_permutation_fitness_collisions':len(orders)-len(np.unique(fitness)),
    'nonincumbent_exact_ties_with_impact':int((fitness[non]==row['best_incumbent_fitness']).sum())})
  result.update(seed=int(row['seed']),objective={'name':'direct_population_service_loss','fitness':'F = -J',
   'planning_realizations':64,'horizon_hr':inp['planning_horizon_hr'],'lower_J_is_better':True,
   'identity_file':'../INPUT_IDENTITY.json','code_sha256':inp['input_sha256']['src\\la_grid\\revision\\r1_ga_revision.py']},
   diagnostic_only=True,formal_strategy_replaced=False)
  (run/'RUN.json').write_text(json.dumps(result,indent=2)+'\n')
 pd.DataFrame(land).to_csv(OUT/'OBJECTIVE_LANDSCAPE_AUDIT.csv',index=False)
 audit={'complete_runs':25,'candidate_artifacts_checked':artifacts,'unique_full_permutations_across_runs':len(cache),
  'full_permutations_checked':sum(x['unique_permutations'] for x in land),
  'best_sequence_seed':int(best.seed),'strictly_improved_extended_seeds':int(extended.strictly_improved_incumbent.sum()),
  'distinct_extended_best_sequence_ids':int(extended.best_non_incumbent_sequence_identity.nunique()),
  'best_realization_changes':{'lower_loss':int((differences.change_hr<0).sum()),'higher_loss':int((differences.change_hr>0).sum()),
    'equal_loss':int((differences.change_hr==0).sum()),'min_hr':float(differences.change_hr.min()),'max_hr':float(differences.change_hr.max()),
    'mean_hr':float(differences.change_hr.mean()),'median_hr':float(differences.change_hr.median())},
  'joint_effective_order_collisions':int(data.effective_ordering_duplicate_count.sum()),'formal_strategy_replaced':False}
 (OUT/'POSTRUN_AUDIT.json').write_text(json.dumps(audit,indent=2)+'\n')
 record=make_figure(data)
 p=REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';captions=p.read_text(encoding='utf-8')
 start=captions.index('## Supplementary Figure S4.');end=captions.index('## Supplementary Figure S5.',start)
 captions=captions[:start]+'## Supplementary Figure S4. Network structure during station removal and recovery\n\n'+S04+'\n\n'+captions[end:]
 start=captions.index('## Supplementary Figure S5.');end=captions.index('## Supplementary Figure S6.',start)
 captions=captions[:start]+'## Supplementary Figure S5. Genetic algorithm search-budget diagnostic\n\n'+caption5(data)+'\n\n'+captions[end:]
 captions=captions.replace('## Supplementary Figure S6. Mapping support and service-assumption sensitivity','## Supplementary Figure S6. Dependency mapping and service-gate sensitivity')
 captions=captions.replace('with fliers and all station points displayed','with all station points displayed on their scenario centerline')
 # All original station values remain visible; no duplicate fliers are needed.
 p.write_text(captions,encoding='utf-8');packets(captions)
 for p in [REVIEW/'README.md',ROOT/'results/figures/README.md']:
  s=p.read_text(encoding='utf-8');s=s.replace('Mapping support and service-assumption sensitivity','Dependency mapping and service-gate sensitivity')
  s=s.replace('Mapping robustness','Dependency and service-model assumptions').replace('mapping robustness','dependency and service-model assumptions')
  p.write_text(s,encoding='utf-8')
 def index(row):
  if row['file'].startswith('FigS06'):row.update(scientific_content='Dependency and service-model assumptions',scientific_question='How sensitive are outcomes to dependency mapping and service-gate assumptions?')
  if row['file'].startswith('FigS05'):
   sources=[f'results/diagnostics/ga_search_budget_20261007/p100_g100_s{s}/HISTORY.csv' for s in range(42,47)]+['results/diagnostics/ga_search_budget_20261007/GA_SEARCH_BUDGET_SENSITIVITY.csv']
   row.update(generator=Path(__file__).relative_to(ROOT).as_posix(),source_data_path=';'.join(sources),source_data_sha256=';'.join(sha(ROOT/x) for x in sources),
    scientific_content='Incumbent-preserving GA search and finite search-budget diagnostic',source_authority='Original formal GA plus separate expanded-budget planning diagnostic')
 update_csv(ROOT/'results/figures/FIGURE_INDEX.csv',index)
 authority=ROOT/'FINAL_REVISION_RUN_SEQUENCE/CODE_AUTHORITY.json';a=json.loads(authority.read_text())
 for path in [Path(__file__),ROOT/'src/la_grid/diagnostics/ga_search_budget_sensitivity.py']:
  rel=path.relative_to(ROOT).as_posix();a['current_code_files']=[x for x in a['current_code_files'] if x['path']!=rel]+[{'path':rel,'sha256':hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest(),'tracked_in_current_git':True}]
 authority.write_text(json.dumps(a,indent=2)+'\n')
 REPORT.parent.mkdir(exist_ok=True)
 fields=[('seed','Seed'),('unique_candidates_evaluated','Unique permutations'),('best_incumbent_fitness','Incumbent F'),('best_ga_generated_non_incumbent_fitness','Generated best F'),('gap_from_impact_hr','Generated ΔJ (h)'),('exact_tie_candidate_count','Exact ties'),('near_tie_abs_gap_lt_1e-06_hr','<1e-6 h'),('near_tie_abs_gap_lt_0.0001_hr','<1e-4 h'),('near_tie_abs_gap_lt_0.001_hr','<1e-3 h'),('near_tie_abs_gap_lt_0.01_hr','<1e-2 h'),('generation_found','Generation')]
 text=f'''# GA search-budget sensitivity and figure interpretation — 2026-10-07

Base: `09fa6b08da4aaa0d88bde9b4bd62e4a567ccc6fe`, branch `revision/reviewer-driven-core-rebuild-v2`. Execution completed locally on 2026-10-08. This is a separate planning search-budget diagnostic, not formal strategy replacement.

The original 100-generation search retained Impact-first because it was the best initial incumbent and no candidate strictly improved it. Twenty 250-generation searches improved that incumbent in **{int(extended.strictly_improved_incumbent.sum())}/20 seeds**. Best planning loss fell from **{best.best_incumbent_service_loss_hr:.9f} to {best.retained_service_loss_hr:.9f} h**, an improvement of **{best.improvement_hr:.9f} h ({best.improvement_percent:.6f}%)**, seed **{int(best.seed)}**. The original result is therefore a finite-budget result. No formal policy order or evaluation result has been replaced.

## Objective and search implementation

Impact-first is one fixed-rule incumbent, not the fitness function. Let π be a full permutation of 92 stations; b indexes the 64 saved planning realizations; r indexes tracts; i indexes stations; P_r is tract population; W_ri is the unchanged dependency weight; m_r = Σ_i W_ri; and e_bi^π(t) is functionality credited only when the station meets the 0.5 functionality threshold and connects to an active Core source. The exact objective is

$$
J(\\pi)=\\frac{{1}}{{64}}\\sum_{{b=1}}^{{64}}
\\frac{{\\sum_r P_r\\int_0^H [m_r-\\sum_i W_{{ri}}e_{{bi}}^\\pi(t)]\\,dt}}
{{\\sum_r P_r m_r}},\\qquad F(\\pi)=-J(\\pi).
$$

Lower J is better; the GA maximizes F. H = **{inp['planning_horizon_hr']:.12f} h**, the same fixed pre-search bound as the formal planning run, not the 480 h evaluation horizon. Event integration, directed travel, earliest-release-crew scheduling, source gate and station population mass use the existing exact kernel. The chromosome contains every station once; its combinatorial domain is **92!**. DS>0 filtering is applied only when decoding each saved realization into damaged tasks.

The seven fixed orders—Centrality-first, Impact-first, Betweenness-first, Degree-first, Closeness-first, Hospital-first and the fixed Random order—are directly scored, inserted in the initial population, and complemented with random full permutations. The best incumbent initializes the archive before generation 0. The unchanged update is `if scored[idx] > archive_score`: equality never replaces it. The archive is preserved separately; it is not an elite forcibly reinserted in every offspring population. Operators remain ordered crossover probability 0.8, inversion mutation probability 0.2 and tournament size 3.

Baseline replay reproduces all original generation-best, generation-mean and archive histories for seeds 42–46 within 1e-9. The original CSV histories do not log candidate identities; unique/tie counts below come from instrumented exact baseline replay, not an inference from the old five flat archive curves. The wrapper logs objective calls and generations without changing RNG calls or operators. A shared exact-score memo avoids recomputing identical permutations between runs; each seed still follows its independent original RNG stream.

## Staged budget and stopping decision

| Stage | Population | Generations | Seeds | Completed result |
|---|---:|---:|---|---|
| Baseline | 100 | 100 | 42–46 | Five exact history replays; no improvement |
| A | 100 | 250 | 42–46 | Four seeds improved; first improvement in seed 42 |
| A, larger generation budgets | 100 | 500 / 1000 | Not run | Skipped under the requested early-improvement stop rule |
| B | 250 / 500 | 500 | Not run | Skipped under the same stop rule |
| C | 100 | 250 | 42–61 | Twenty independent seeds total; includes Stage A's five |

Thus 25 complete runs are recorded, without double-counting Stage A in Stage C. Larger budgets have not been tested and no claim is made about them.

## Original-budget candidate audit

{table(baseline,fields)}

## Expanded-budget candidate audit

{table(extended.sort_values('seed'),fields)}

Counts refer to unique permutations within each run. Exact/near ties exclude all seven deterministic incumbent permutations; thresholds are absolute differences from Impact-first J and are cumulative. Fitness has the opposite sign to service loss. Full sequence SHA-256, all 92 IDs, first generation, rank correlation, displaced stations and top-10 overlap appear in `GA_SEARCH_BUDGET_SENSITIVITY.csv` and each `RUN.json`.

## Best candidate and planning-realization interpretation

Seed {int(best.seed)} found its best generated sequence at generation {int(best.generation_found)}. It displaces {int(best.displaced_stations)} stations, has rank correlation {best.rank_correlation:.6f} with Impact-first and top-10 overlap {int(best.top10_overlap)}/10. Its sequence identity is `{best.best_non_incumbent_sequence_identity}`.

On the same 64 planning realizations, mean new-minus-Impact-first change is **{differences.change_hr.mean():.9f} h** and median is **{differences.change_hr.median():.9f} h**. Loss is lower in {audit['best_realization_changes']['lower_loss']}, higher in {audit['best_realization_changes']['higher_loss']} and identical in {audit['best_realization_changes']['equal_loss']} realizations. The minimum/maximum changes are {differences.change_hr.min():.6f}/{differences.change_hr.max():.6f} h. All 64 individual differences are saved. These are planning comparisons, not 1,000-realization generalization evidence.

All 20 extended runs have distinct best non-incumbent sequence identities. The largest reduction is less than 1% of the incumbent planning loss, with varied realization effects. It warrants consideration as a separate search-budget result; it does not justify automatic replacement or a claim of global optimality. Re-freezing and independent evaluation would require the author's explicit approval.

## Objective landscape and effective ordering

{audit['unique_full_permutations_across_runs']:,} distinct full permutations were scored across the 25 runs. **No generated non-incumbent tied Impact-first exactly**. Near-equivalent values exist at the reported tolerances. `OBJECTIVE_LANDSCAPE_AUDIT.csv` separately counts identical floating-point fitness values among different permutations; identical objectives need not imply identical task order.

Across the 64 saved planning samples, DS0 excludes only 0–2 tasks per sample. Many samples include all 92 stations as damaged tasks. Consequently, the joint 64-sample effective-order signature has **zero collisions between distinct full permutations** in every run. DS>0 filtering cannot explain a broad joint-order plateau here. Some individual samples collapse a few orders, and some distinct orders produce equal objectives, but an exact plateau at Impact-first is not supported. Improved candidates at 250 generations demonstrate that the 100-generation archive did not establish an optimum.

## Figure S04: manuscript/meeting interpretation

{S04}

Formally, the plotted quantities are `mean_b(|LCC_b(t)|/92)` and `mean_b(2E_LCC,b(t)/N_LCC,b(t))`, not a source-connected fraction or mean degree over every functional component. All policies use the same physical realization family and graph; only fixed repair order differs. The display table is `results/revised_suite/LA_Grid_Revised_Suite_20260925/Stage 6 Output_expanded/NETWORK_TOPOLOGY_DISPLAY_CURVES_2pc50.csv`; its creation logic is `src/la_grid/plotting/render_revised_suite.py`, functional-mask/LCC display section. Panel A uses the saved Stage 2 percolation curves. The complete PDF was actually opened before and after the stroke correction.

**Figure S04 shows how station removal fragments the network and how the largest functional component and its internal degree recover under the evaluated policies.**

## Figure S05: corrected interpretation

{caption5(data)}

## Figure S06: unified scope

Title: **Dependency mapping and service-gate sensitivity**. Narrative scope: **dependency and service-model assumptions**.

{S06}

## Records, identity and boundary

`results/diagnostics/ga_search_budget_20261007/` contains input identities, planning-sample hashes, stopping decision, full CSV summary and every complete run. Each run contains `RUN.json`, generation history, all unique candidate permutations/fitness/first generation in `CANDIDATES.npz`, and 64 realization-specific comparisons. The generated-candidate diagnostic is `GA_SEARCH_BUDGET_DIAGNOSTIC.pdf/.png`, also integrated into current S05.

Formal GA outputs, physical samples, mapping, source gate, evaluation schedules/trajectories, equity and capacity numerical results are preserved. New numerical files belong only to this explicitly authorized planning diagnostic. Presentation corrections also address the author's pending map, metric, legend, station-point and equal-priority-map requests; they do not change source values or cluster IDs. Verification results are recorded separately after testing and canonical resume.
'''
 REPORT.write_text(text,encoding='utf-8')
 (ROOT/'docs/reviewer/FIGURE_S04_S05_S06_INTERPRETATION_20261007.md').write_text('# Figure interpretations\n\n## S04\n\n'+S04+'\n\n**Figure S04 shows how station removal fragments the network and how its largest functional component recovers.**\n\n## S05\n\n'+caption5(data)+'\n\n## S06\n\n'+S06+'\n',encoding='utf-8')
 print(json.dumps(audit,indent=2))

if __name__=='__main__':main()
