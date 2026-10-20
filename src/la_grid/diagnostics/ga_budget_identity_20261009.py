"""Completed-run prefix identity and actual query-accounting audit."""
import json
from pathlib import Path
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT

def main():
    rows=[]
    for p in (OUT/'budget_extension').glob('*/RUN.json'):
        r=json.loads(p.read_text());phase='shortlist' if r['config_id']=='original_p100' else 'operator_confirmation';source=OUT/phase/p.parent.name
        with np.load(p.parent/'CANDIDATES.npz') as extended,np.load(source/'CANDIDATES.npz') as initial:
            n=len(initial['fitness']);ok=all(np.array_equal(extended[k][:n],initial[k]) for k in ['orders','fitness','first_generation','first_attempt'])
        assert ok,(p,'budget prefix differs')
        rows.append(dict(config_id=r['config_id'],seed=r['seed'],prefix_phase=phase,prefix_distinct=n,complete_order_fitness_generation_attempt_identity=True))
    assert len(rows)==10
    (OUT/'BUDGET_PREFIX_PARITY.json').write_text(json.dumps(rows,indent=2)+'\n')
    records=[];sequence=[]
    for p in OUT.glob('*/*/RUN.json'):
        r=json.loads(p.read_text());phase=p.parent.parent.name
        if 'config' in r:
            records.append(dict(phase=phase,config_id=r['config_id'],seed=r['seed'],new_expensive_search_queries=r['actual_expensive_calls'],new_attempted_search_calls=r['total_attempts'],loader_validation_calls_outside_budget=r['setup_validation_objective_calls'],postsearch_full_sample_summaries_outside_budget=r['postsearch_full_sample_summaries'],elapsed_search_seconds=r['elapsed_seconds'],peak_rss_mb=r['peak_rss_mb'],prefix_is_prior_computation=False))
            sequence.append(dict(phase=phase,config_id=r['config_id'],sequence_sha256=r['sequence_sha256'],planning_loss_hr=r['best_planning_loss_hr'],seed=r['seed']))
        elif phase=='hybrid':
            h=json.loads((p.parent/'HYBRID_IDENTITY.json').read_text());records.append(dict(phase=phase,config_id=r['config_id'],seed=r['seed'],new_expensive_search_queries=h['joint_distinct_evaluations']-h['ga_prefix_distinct_evaluations'],new_attempted_search_calls=r['total_attempts'],joint_logical_queries=h['joint_distinct_evaluations'],elapsed_search_seconds=r['elapsed_seconds'],peak_rss_mb=h['peak_rss_mb'],prefix_is_prior_computation=True,setup_validation_calls_outside_budget=8,local_initialization_score_calls_outside_budget=3,postsearch_full_sample_summaries_outside_budget=1))
        elif phase=='local_search':
            records.append(dict(phase=phase,config_id=r['method'],new_expensive_search_queries=r['distinct_evaluations'],new_attempted_search_calls=r['total_attempts'],elapsed_search_seconds=r['elapsed_seconds'],peak_rss_mb=r.get('peak_rss_mb'),prefix_is_prior_computation=False,local_initialization_score_calls=3*len(r.get('budget_staging',[0])),duplicate_initialization_calls_outside_budget=3*len(r.get('budget_staging',[0]))-1,postsearch_full_sample_summaries_outside_budget=1))
        elif phase=='internal_cv':
            records.append(dict(phase=phase,config_id='elite'+str(r['elites']),seed=r['seed'],new_expensive_search_queries=r['distinct_evaluations'],new_attempted_search_calls=r['total_attempts'],elapsed_search_seconds=r['elapsed_seconds'],observed_search_peak_rss_mb=r['observed_search_peak_rss_mb'],training_sample_count=48,heldout_sample_count=16,prefix_is_prior_computation=False,full64_equivalent_queries=False))
    pd.DataFrame(records).to_csv(OUT/'COMPUTE_ACCOUNTING.csv',index=False)
    q=pd.DataFrame(sequence);frequencies=q.groupby(['phase','config_id','sequence_sha256','planning_loss_hr']).agg(seed_count=('seed','size'),seeds=('seed',lambda s:';'.join(map(str,sorted(s))))).reset_index();frequencies.to_csv(OUT/'BEST_SEQUENCE_REPLICATION.csv',index=False)
    grouped=pd.DataFrame(records).groupby('phase').new_expensive_search_queries.sum()
    (OUT/'COMPUTE_TOTALS.json').write_text(json.dumps({'new_expensive_queries_by_phase':grouped.to_dict(),'all_query_total':int(grouped.sum()),'setup_reporting_and_bound_checks_outside_search_budget':True,'cross_validation_queries_use_48_samples_not64':True,'hybrid_prefix_already_executed_not_counted_twice':True,'existing_replay_expensive_queries':0,'note':'Query totals exclude saved-score replay, independent verification, rational bound, reduced720 exact checks, postselection summaries and evaluation; these are separate diagnostic operations.'},indent=2)+'\n')
    confirmation=[]
    parameters=pd.read_csv(OUT/'GA_PARAMETER_SENSITIVITY.csv')
    for (phase,cid),g in parameters[parameters.phase.isin(['shortlist','operator_confirmation'])].groupby(['phase','config_id']):
        for label,subset in [('common_screening_seeds',g[g.seed.between(42,46)]),('additional_15_seeds',g[g.seed.between(47,61)])]:
            v=subset.best_planning_loss_hr;confirmation.append(dict(phase=phase,config_id=cid,seed_group=label,n=len(v),mean_hr=v.mean(),std_hr=v.std(),min_hr=v.min(),max_hr=v.max()))
    pd.DataFrame(confirmation).to_csv(OUT/'NEW_RESTART_CONFIRMATION.csv',index=False)
    print('COMPUTE ACCOUNTING',grouped.to_dict())
if __name__=='__main__':main()
