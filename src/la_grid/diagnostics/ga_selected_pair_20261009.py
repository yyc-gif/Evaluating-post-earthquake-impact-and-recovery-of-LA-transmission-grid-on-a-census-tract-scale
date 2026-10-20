"""Postselection comparison of fixed candidate identities, with no reselection."""
import json,hashlib
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.diagnostics.ga_generalization_20261009 import mean_ci
from la_grid.plotting.selected_strategy_evidence import METRICS
from la_grid.revision.r1_equity_amendment_execute import execution_context

def main():
    k,inc,prior=load();context,decoder,_=execution_context(k.ids);origins=decoder.origins(context['origins']);selection=json.loads((OUT/'reused_evaluation/CANDIDATE_SELECTION.json').read_text());rows=[];pair=[]
    for c in selection['candidates']:
        completions=[]
        for b in range(64):
            finish,*_=decoder.decode(order=decoder.order(c['sequence']),damage=k.damage[b],duration=k.duration[b],origins=origins);completions.append(finish)
        a=np.nan_to_num(np.stack(completions),nan=np.inf).astype('<f8');rows.append(dict(candidate=c['candidate_id'],sequence_sha256=c['sequence_sha256'],planning_loss_hr=c['planning_loss_hr'],planning_completion64_sha256=hashlib.sha256(a.tobytes()).hexdigest()))
    for i in range(3):
        for j in range(i):
            cand=selection['candidates'][i]['candidate_id'];ref=selection['candidates'][j]['candidate_id'];q=pd.read_csv(OUT/f'reused_evaluation/{cand}/SUMMARY.csv').set_index('realization_id');r=pd.read_csv(OUT/f'reused_evaluation/{ref}/SUMMARY.csv').set_index('realization_id')
            for field,label in METRICS.items():
                values=(q[field]-r[field]).dropna().to_numpy();ci=mean_ci(values);pair.append(dict(candidate=cand,reference=ref,source_field=field,metric=label,n=len(values),mean_change=values.mean(),median_change=np.median(values),p05=np.quantile(values,.05),p95=np.quantile(values,.95),bootstrap_mean_ci95_low=ci[0],bootstrap_mean_ci95_high=ci[1],postselection_reused_cohort=True,reselection_performed=False))
    pd.DataFrame(rows).to_csv(OUT/'SELECTED_PLANNING_SCHEDULE_IDENTITIES.csv',index=False);pd.DataFrame(pair).to_csv(OUT/'reused_evaluation/FIXED_CANDIDATE_PAIR_COMPARISONS.csv',index=False)
    print('SELECTED SCHEDULE IDENTITIES',len(set(r['planning_completion64_sha256'] for r in rows)))
if __name__=='__main__':main()
