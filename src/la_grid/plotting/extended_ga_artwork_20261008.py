"""Expanded unchanged-operator search and separate exploratory evaluation."""
import json,re
import numpy as np,pandas as pd,matplotlib.pyplot as plt
from la_grid.plotting import selected_strategy_artwork as a
from la_grid.diagnostics import ga_search_budget_sensitivity as old
R=a.ROOT;SEARCH=R/'results/diagnostics/extended_ga_20261008'

def main():
    summary=pd.read_csv(SEARCH/'SEARCH_SUMMARY.csv');assert len(summary)==60
    best=summary.sort_values('retained_service_loss_hr').iloc[0]
    selection=json.loads((SEARCH/'independent_evaluation/CANDIDATE_SELECTION.json').read_text());effects=pd.read_csv(SEARCH/'independent_evaluation/OUTCOME_COMPARISONS.csv')
    fig=plt.figure(figsize=(185/25.4,190/25.4));ax=fig.add_axes([.115,.57,.845,.34])
    for seed in range(42,62):
        d=pd.read_csv(SEARCH/f'p100_g1000_s{seed}/HISTORY.csv');ax.plot(d.generation,-d.non_incumbent_best_so_far,color='#6a9db5',lw=.55,alpha=.55)
    folder=f'p{int(best.population)}_g{int(best.generations)}_s{int(best.seed)}';d=pd.read_csv(SEARCH/folder/'HISTORY.csv')
    ax.plot(d.generation,-d.non_incumbent_best_so_far,color='#285b79',lw=1.2,label='Best completed run: generated candidates')
    ax.axhline(best.impact_service_loss_hr,color='black',ls='--',lw=.8,label='Impact-first incumbent');ax.set_xlabel('Generation');ax.set_ylabel('Planning service loss (h)');ax.set_title('A. Search progress excluding deterministic incumbents',fontsize=9.5,pad=7);ax.legend(frameon=False,fontsize=7.5,loc='upper right');ax.grid(color='#e6e6e6',lw=.4);ax.spines[['top','right']].set_visible(False)
    bx=fig.add_axes([.115,.13,.38,.29]);oldrows=pd.read_csv(old.OUT/'GA_SEARCH_BUDGET_SENSITIVITY.csv');oldrows=oldrows.rename(columns={'best_non_incumbent_service_loss_hr':'best_non_incumbent_service_loss_hr'})
    full=pd.concat([summary,oldrows],ignore_index=True);configs=[(100,100),(100,250),(100,500),(100,1000),(100,2000),(250,500),(500,500),(500,1000)]
    for j,(p,g) in enumerate(configs):
        q=full[full.population.eq(p)&full.generations.eq(g)].drop_duplicates(['population','generations','seed']);offset=np.linspace(-.14,.14,len(q))
        bx.scatter(j+offset,q.best_non_incumbent_service_loss_hr,s=8,color='#285b79',edgecolor='none',alpha=.8)
    bx.axhline(best.impact_service_loss_hr,color='black',ls='--',lw=.8);bx.set_xticks(range(8),[f'{p}\u00d7{g}' for p,g in configs],rotation=45,ha='right');bx.set_ylabel('Planning service loss (h)');bx.set_xlabel('Population \u00d7 generations');bx.set_title('B. Final generated results by budget',fontsize=9.5,pad=7);bx.grid(axis='y',color='#e6e6e6',lw=.4);bx.spines[['top','right']].set_visible(False)
    cx=fig.add_axes([.70,.13,.26,.25]);fields=['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr'];labels=['All tracts','Q4 tracts','Hospital-linked\ntracts']
    for j,c in enumerate(selection['candidates']):
        for i,field in enumerate(fields):
            q=effects[effects.candidate.eq(c['candidate_id'])&effects.reference.eq('impact-first')&effects.source_field.eq(field)].iloc[0]
            cx.errorbar(q.mean_change,i+(j-.5)*.15,xerr=[[q.mean_change-q.p05],[q.p95-q.mean_change]],fmt='o' if j==0 else 's',ms=3,color='#285b79' if j==0 else '#b06c30',lw=.7,capsize=1,label=f'Candidate {j+1}' if i==0 else None)
    cx.set_yticks(range(3),labels);cx.set_ylim(2.5,-.5);cx.axvline(0,color='#444444',lw=.6);cx.set_xlabel('Change from Impact-first (h)',fontsize=7.5);fig.text(.83,.443,'C. Independent evaluation',ha='center',fontsize=9.5,fontweight='bold');cx.grid(axis='x',color='#e6e6e6',lw=.4);cx.spines[['top','right']].set_visible(False);cx.legend(frameon=False,fontsize=7.5,loc='center',bbox_to_anchor=(.5,1.13),ncol=2,columnspacing=.6,handletextpad=.3)
    fig.text(.98,.017,'Planning: 64 realizations; independent evaluation: 1,000 realizations',ha='right',fontsize=7.5)
    result=a.export_figure(fig,'Supplement/FigS05');result['search_runs']=60;result['best_planning_result']=best.to_dict();result['selection_sha256']=old.digest(SEARCH/'independent_evaluation/CANDIDATE_SELECTION.json')
    path=a.TEMP/'artwork_records.json';path.write_text(json.dumps(json.loads(path.read_text())+[result],indent=2))
    p=a.REVIEW/'MANUSCRIPT_FACING_CAPTIONS.md';s=p.read_text(encoding='utf-8');start=s.index('## Supplementary Figure S5.');end=s.index('## Supplementary Figure S6.',start)
    caption=f'''## Supplementary Figure S5. Genetic algorithm search budget and exploratory evaluation

The genetic algorithm (GA) maximizes the negative of direct population-dependency-weighted planning service loss on 64 fixed 2pc50 realizations. Chromosomes are full station permutations. Seven deterministic orders were directly scored and inserted into the initial population; Impact-first was their best incumbent and initialized the separate best-so-far archive. Only a strictly better score replaces this archive. The original five 100-generation runs retained Impact-first because no evaluated candidate improved it; they did not independently rediscover its permutation. Operators are unchanged across the extended budgets: ordered crossover probability 0.80, inversion mutation probability 0.20 and tournament size 3. (A) Best GA-generated performance excluding all deterministic incumbent sequences. Pale curves show twenty independent population-100, 1,000-generation searches; the darker curve is the lowest-loss completed run. The dashed black line is the Impact-first incumbent. (B) Final best generated result for each seed across the tested population/generation budgets; population-100, 250-, 500- and 1,000-generation configurations each have twenty seeds, and the other configurations five. The expanded 60-run study found a lowest planning loss of {best.retained_service_loss_hr:.6f} h, {best.improvement_hr:.6f} h ({best.improvement_percent:.3f}%) below Impact-first. (C) Two distinct sequences selected only by planning loss before independent evaluation, compared with Impact-first on the existing separate 1,000 2pc50 realizations at reference crew availability and duration. Dots show mean service-loss differences and whiskers the 5th-95th realization-difference ranges, not confidence intervals. All-tract and Q4 outcomes are population-weighted; hospital-linked loss is an equal-tract mean, not electricity delivery or clinical capacity. Planning uses the pre-search 2,855.254 h horizon, while evaluation integrates loss over 0-480 h; an order-independent completion bound below 480 h makes these planning integrals numerically equivalent on the 64 planning samples. The new sequences are exploratory comparisons, distinct from the original formal policy evaluations. Finite search improvement does not establish global optimality.

'''
    p.write_text(s[:start]+caption+s[end:],encoding='utf-8');print('S05 updated',best[['population','generations','seed','retained_service_loss_hr']].to_dict())
if __name__=='__main__':main()
