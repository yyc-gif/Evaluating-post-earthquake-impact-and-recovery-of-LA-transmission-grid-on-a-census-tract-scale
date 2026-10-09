"""Report search, exploratory evaluation and station guidance without promotion."""
import json
import numpy as np,pandas as pd
from la_grid.paths import REPO_ROOT as R
from la_grid.diagnostics import ga_search_budget_sensitivity as old
S=R/'results/diagnostics/extended_ga_20261008'

def station_candidates():
    selection=json.loads((S/'independent_evaluation/CANDIDATE_SELECTION.json').read_text())
    original=pd.read_csv(R/'results/diagnostics/selected_strategy_20261008/STATION_PRIORITY_AND_EXECUTION.csv',dtype={'station_id':str});attrs=original[original.policy.eq('impact-first')].set_index('station_id')
    rows=[]
    for c in selection['candidates']:
        events=pd.read_csv(S/'independent_evaluation'/c['candidate_id']/'TASK_EXECUTION.csv',dtype={'station_id':str});groups=events.groupby('station_id')
        for rank,station in enumerate(c['sequence'],1):
            base=attrs.loc[station].to_dict();q=groups.get_group(station);base.update(policy=c['candidate_id'],station_id=station,fixed_priority_rank=rank,damaged_realization_count=len(q),mean_effective_dispatch_rank=q.dispatch_rank.mean(),mean_completion_hr=q.completion_hr.mean(),mean_travel_hr=q.travel_hr.mean(),sequence_sha256=c['sequence_sha256'],priority_rank_change_vs_impact=rank-int(attrs.loc[station,'fixed_priority_rank']),mean_completion_change_vs_impact_hr=q.completion_hr.mean()-attrs.loc[station,'mean_completion_hr']);rows.append(base)
    pd.concat([original,pd.DataFrame(rows)],ignore_index=True).to_csv(S/'STATION_PRIORITY_AND_EXPLORATORY_EXECUTION.csv',index=False)

def table(frame,cols):
    lines=['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']
    for _,r in frame.iterrows():lines.append('| '+' | '.join(f'{r[k]:.6f}' if isinstance(r[k],float) else str(r[k]) for k in cols)+' |')
    return '\n'.join(lines)

def enrich_runs():
    impact=json.loads((R/'Formal_Experiment_20260923/Stage 4 Output_expanded/FULL_RULE_SEQUENCES.json').read_text())['2pc50']['impact-first']
    rows=[]
    for folder in sorted(S.glob('p*_g*_s*')):
        path=folder/'RUN.json';run=json.loads(path.read_text());q=run['summary'];seq=run['best_non_incumbent_sequence']
        with np.load(folder/'CANDIDATES.npz') as z:
            non=z['non_incumbent'];idx=np.flatnonzero(non)[np.argmax(z['fitness'][non])];generation=int(z['first_generation'][idx])
            assert seq==[str(z['station_ids'][j]) for j in z['orders'][idx]]
        positions=np.array([seq.index(x) for x in impact])
        q.update(best_incumbent_fitness=-q['impact_service_loss_hr'],best_ga_generated_non_incumbent_fitness=-q['best_non_incumbent_service_loss_hr'],best_non_incumbent_sequence_identity=old.identity(seq),best_non_incumbent_generation_found=generation,best_non_incumbent_gap_from_impact_hr=q['best_non_incumbent_service_loss_hr']-q['impact_service_loss_hr'],best_non_incumbent_displaced_stations=int(np.sum(positions!=np.arange(92))),best_non_incumbent_rank_correlation=float(np.corrcoef(positions,np.arange(92))[0,1]),best_non_incumbent_top10_overlap=len(set(seq[:10])&set(impact[:10])))
        run['input_identity_sha256']=old.digest(S/'INPUT_IDENTITY.json');run['runtime_scope']='Resumed segment after generation 200; earlier segment excluded' if folder.name=='p500_g500_s42' else 'Single uninterrupted search segment'
        path.write_text(json.dumps(run,indent=2)+'\n');rows.append(q)
    assert len(rows)==60
    d=pd.DataFrame(rows).sort_values(['population','generations','seed']);d.to_csv(S/'SEARCH_SUMMARY.csv',index=False);return d

def main():
    d=enrich_runs();unused=pd.read_csv(S/'SEARCH_SUMMARY.csv');assert len(d)==60;best=d.sort_values('retained_service_loss_hr').iloc[0]
    outcome=pd.read_csv(S/'independent_evaluation/OUTCOME_COMPARISONS.csv');per=pd.read_csv(S/'independent_evaluation/REALIZATION_SERVICE_LOSS_CHANGES.csv')
    budget=d.groupby(['population','generations']).agg(seeds=('seed','size'),strict_improvements=('strict_improvement','sum'),lowest_planning_loss_hr=('retained_service_loss_hr','min'),unique_candidates_sum=('unique_candidates_evaluated','sum')).reset_index()
    for folder in S.glob('p*_g*_s*'):
        p=folder/'RUN.json';run=json.loads(p.read_text());run['input_identity_sha256']=old.digest(S/'INPUT_IDENTITY.json');run['runtime_scope']='Resumed segment after generation 200; earlier segment excluded' if folder.name=='p500_g500_s42' else 'Single uninterrupted search segment';p.write_text(json.dumps(run,indent=2)+'\n')
    station_candidates();bound=json.loads((S/'PLANNING_HORIZON_AUDIT.json').read_text())
    selected=outcome[outcome.source_field.isin(['population_weighted_normalized_burden_hr','burden_Q4_hr','hospital_mean_normalized_burden_hr','absolute_Q4_minus_Q1_hr','burden_gini'])&outcome.reference.isin(['impact-first','hospital-first'])]
    content=f'''# Extended GA search and selected-policy evidence

Formal strategies and original scientific outputs are not replaced. New numerical results are confined to this explicitly authorized optimization/evaluation diagnostic. The manuscript display set is six scheduled policies (Degree, Betweenness, Impact, Hospital, Vulnerability-first and fixed Random), with Unconstrained as the idealized reference. Centrality/Closeness original experiments remain intact. The protected July reference is unchanged.

## Objective and incumbent interpretation

Let m_i = sum_r P_r W_ri, F_bi(t)=I[f_bi(t)>=0.5], C_bi(t) indicate connection to an active Core source, and e_bi=f_bi F_bi C_bi. The existing objective is

$$J(\\pi)=\\frac{{1}}{{64}}\\sum_{{b=1}}^{{64}}\\frac{{\\sum_i m_i\\int_0^{{H_{{plan}}}}[1-e_{{bi}}^\\pi(t)]dt}}{{\\sum_i m_i}},\\qquad \\text{{fitness}}(\\pi)=-J(\\pi).$$

Impact-first is one of seven deterministic incumbents, not the fitness function. Each chromosome is a full permutation over the 92 stations, giving 92! possible orders. The seven fixed sequences enter generation zero; the best incumbent initializes an independent archive. Only `scored[idx] > archive_score` replaces it. Thus the original five coincident archives show no strict improvement within that budget, not independent stochastic rediscovery of Impact-first. All original crossover/mutation/tournament operations and random-number streams are preserved. Exact baseline history parity is verified; checkpoint/resume parity is also tested. Parallel processes execute independent seeds only.

H_plan = {bound['planning_horizon_hr']:.12f} h. An order-independent list-scheduling bound of {bound['all_permutation_completion_upper_bound_hr']:.6f} h is below 480 h in every planning sample. Every intact component contains a Core source; consequently loss is zero afterward. The objective ranking is therefore identical at 480 h and H_plan for every permutation on these planning samples. Numerical checks of the earlier 25 generated candidates differ by less than 3e-12 h; the optimization objective itself is not changed. The calculation and proof are in `audit_planning_horizon_20261008.py` and `PLANNING_HORIZON_AUDIT.json`.

## Completed budgets

The earlier study contains five original-budget replays and twenty population-100, 250-generation restarts. This round adds 60 runs:

{table(budget,['population','generations','seeds','strict_improvements','lowest_planning_loss_hr','unique_candidates_sum'])}

Unique-candidate sums count a permutation separately if it occurs in multiple runs; cross-run memoization and per-run caching avoid redundant exact scores. Run timings are wall-clock intervals and parallel-worker runtimes are not added as elapsed study time. The population-500, 500-generation seed-42 timing covers only its resumed segment after generation 200; its earlier segment was not separately timed, so no complete-run runtime or speedup claim is made for that run. Each run records candidate permutations, objective values, first generation, archives, best generated non-incumbent, sequence identity and all 64 realization differences. Exact ties exclude all deterministic sequences; cumulative near-tie thresholds are 1e-6, 1e-4, 1e-3 and 1e-2 h. Full details are in `SEARCH_SUMMARY.csv` and `p*_g*_s*/RUN.json`, `HISTORY.csv`, `CANDIDATES.npz`, and `PLANNING_DIFFERENCES.csv`.

Lowest completed planning loss: **{best.retained_service_loss_hr:.9f} h**, versus Impact-first **{best.impact_service_loss_hr:.9f} h**; improvement **{best.improvement_hr:.9f} h ({best.improvement_percent:.6f}%)**. Configuration: population {int(best.population)}, generations {int(best.generations)}, seed {int(best.seed)}. The retained order displaces {int(best.displaced_stations)} stations, has rank correlation {best.rank_correlation:.6f} and top-ten overlap {int(best.top10_overlap)}/10 relative to Impact-first. Improvement under some budgets does not imply improvement under every larger population: the archive is preserved, but the original GA does not force it into each offspring generation. Neither finite search nor these metrics certify a global optimum.

## Independent exploratory evaluation

Two distinct orders were selected solely by lowest planning loss and identified before any evaluation, in `independent_evaluation/CANDIDATE_SELECTION.json`. They use the original separate 1,000 2pc50/C57_D1 physical realizations, existing exact scheduling, source gate, mapping and 480-h event integration. Three Impact-first replay samples reproduce existing formal metrics within 1e-8. No evaluation score was used to select or reselect the two orders.

{table(selected,['candidate','reference','metric','mean_change','median_change','p05','p95'])}

Changes are candidate less named reference on the same physical sample; p05/p95 are realization-difference ranges, not confidence intervals. Planning and evaluation samples are separate. Quartile, signed/absolute group difference, population-weighted Gini, hospital-linked, T80, component and logistics results remain available in the new summaries. Event arrays and task execution are retained by batch. These results assess transfer of planning improvement; they do not promote a new formal strategy.

## Landscape and station interpretation

The planning family includes samples with all stations damaged. A joint signature containing such a sample cannot collapse two different full permutations merely through DS>0 filtering. Near-equivalent objective values are not proof of identical effective task orders or a broad exact plateau. The original 100-generation result was a finite-budget limitation, as improvements at longer budgets demonstrate. No global-optimality claim is made.

`STATION_PRIORITY_AND_EXPLORATORY_EXECUTION.csv` distinguishes fixed full rank from damage-filtered task dispatch and mean repair completion. It links saved degree/betweenness, population/Q4/hospital dependencies and directed travel. Differences are descriptive strategy outcomes, not a causal station-by-station early-repair benefit. Actual 92-station electrical MW capacity and power-flow outcomes are not available; S8 remains the restricted SCE planning-ceiling sensitivity.

## Reference purposes and new mechanism evidence

Hospital-first is the predeclared critical-service reference. Impact-first is the population-loss-oriented incumbent. Random is one fixed random order. Unconstrained removes crew competition and is not an operational policy. Degree and Betweenness are compared with both Hospital and Impact; complete absolute outcomes and named-reference effects cover every existing selected-policy scenario.

The new network/station/community candidate reads saved f/F/e trajectories, not recalculated dynamics. Under 2pc50/C57_D1, Degree-first relative to Hospital-first changes source-path loss by -1.646692 h and all-tract loss by +1.401244 h: substation-damage loss increases 2.944702 h and threshold loss 0.103234 h. The components account for the opposite directions. This is modeled service loss, not delivered MW. The Degree/Betweenness maps and histograms read existing station metrics; July's top-ten map used network lambda2 impact instead.

S4 remains static node-removal criticality plus dynamic functional LCC structure; S7 instead measures Core-source connectivity/redundancy. S6 is dependency and service-model assumptions: mapping cutoff, source-connectivity gate and functionality threshold, with the public-record mapping agreement shown in Fig2.

## Preservation boundary

Original physical samples, mapping, source gate, 64 planning inputs, formal sequences, original schedules/evaluation trajectories, Stage7 membership, equity and capacity results remain unchanged. The new exploratory schedules and evaluations are in a separate namespace and were explicitly requested by the author. Only presentation files/captions/indexes, diagnostic results and validation identities are updated. Author selection of a replacement formal policy is still pending.
'''
    (R/'docs/reviewer/EXTENDED_GA_AND_SELECTED_STRATEGY_20261008.md').write_text(content,encoding='utf-8')
    print('Report written',best.retained_service_loss_hr)
if __name__=='__main__':main()
