"""Bounded checks of objective ties versus exact completion-array identity."""
import json,hashlib
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context


def main():
    k,inc,quality=load();context,decoder,_=execution_context(k.ids);origins=decoder.origins(context['origins']);rows=[]
    for phase in ['shortlist','operator_confirmation']:
        paths=sorted((OUT/phase).glob('*/RUN.json'))
        if not paths:continue
        path=min(paths,key=lambda p:json.loads(p.read_text())['best_planning_loss_hr']);data=json.loads(path.read_text())
        with np.load(path.parent/'CANDIDATES.npz') as z:
            fitness=z['fitness'];best=fitness.max();exact=np.flatnonzero(fitness==best);near=np.flatnonzero(abs(fitness-best)<1e-6);ids=np.unique(np.r_[exact[:50],near[:50],np.argmax(fitness)]);orders=z['orders'][ids].copy()
        signatures=[];values=[]
        for candidate_index,order in zip(ids,orders):
            seq=[k.ids[i] for i in order];completion=[]
            for b in range(64):
                finish,*_=decoder.decode(order=decoder.order(seq),damage=k.damage[b],duration=k.duration[b],origins=origins);completion.append(finish)
            a=np.stack(completion);canonical=np.nan_to_num(a,nan=np.inf).astype('<f8');signature=hashlib.sha256(canonical.tobytes()).hexdigest();signatures.append(signature);values.append(canonical);rows.append(dict(phase=phase,config_id=data['config_id'],seed=data['seed'],candidate_query_index=int(candidate_index)+1,sequence_sha256=old.identity(seq),planning_loss_hr=float(-fitness[candidate_index]),exact_tie_with_run_best=bool(fitness[candidate_index]==best),near_run_best_lt_1e_minus_6=bool(abs(fitness[candidate_index]-best)<1e-6),completion64_sha256=signature,all_completion_arrays_identical_to_first=False,exact_tie_pool_size=len(exact),sampled_tie_pool_size=len(ids),sampling_rule='First up-to-50 exact ties and first up-to-50 near ties, plus best; bounded descriptive check'))
        for row,v in zip(rows[-len(values):],values):row['all_completion_arrays_identical_to_first']=bool(np.array_equal(v,values[0]))
    pd.DataFrame(rows).to_csv(OUT/'SCHEDULE_PHENOTYPE_DIAGNOSTICS.csv',index=False);print('SCHEDULE PHENOTYPES',len(rows))
if __name__=='__main__':main()
