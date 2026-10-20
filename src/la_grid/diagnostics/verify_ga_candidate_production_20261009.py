"""Independent production-path checks on diagnostic candidates."""
import json,random
import numpy as np,pandas as pd
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_equity_amendment_execute import execution_context
from la_grid.revision.r1_realization_scheduling import RealizationInputs
from la_grid.revision.r1_source_gate import evaluate_source_gate
from la_grid.revision.r1_ga_revision import evaluate_direct_population_burden_aggregate
from la_grid.revision.r1_ga_exact_kernel import _one_sample


def main():
    kernel,inc,quality=load();context,decoder,hashes=execution_context(kernel.ids);best=json.loads((OUT/'local_search/previous_best/RUN.json').read_text())['best_sequence'];rng=random.Random(9937109);sequences=[('local_best',best),('random_check_1',rng.sample(kernel.ids,92)),('random_check_2',rng.sample(kernel.ids,92))];rows=[]
    selection=OUT/'reused_evaluation/CANDIDATE_SELECTION.json'
    if selection.exists():sequences.extend((c['candidate_id'],c['sequence']) for c in json.loads(selection.read_text())['candidates'])
    for name,seq in sequences:
        order=np.array([kernel.index[s] for s in seq],dtype=np.int64)
        for b in [0,17,63]:
            realization=RealizationInputs(f'2pc50__planning_{b:04}',pd.Series(kernel.damage[b],index=kernel.ids),pd.Series(kernel.duration[b],index=kernel.ids))
            gate=lambda raw:evaluate_source_gate(raw,context['graph'],context['sources'],threshold=.5)
            a=evaluate_direct_population_burden_aggregate(sequence=seq,realization=realization,crew_origin_ids=context['origins'],base_to_task_hr=context['base'],task_to_task_hr=context['task'],horizon_hr=kernel.horizon,source_gate=gate,station_population_mass=kernel.station_mass,population_resolved_mass=kernel.total_mass)
            v=_one_sample(order,kernel.damage[b],kernel.duration[b],kernel.origin_index,kernel.base,kernel.travel,kernel.neighbor_offset,kernel.neighbors,kernel.source_flag,kernel.station_mass,kernel.total_mass,kernel.horizon);assert abs(a-v)<1e-8,(a,v);rows.append(dict(sequence=name,sequence_sha256=old.identity(seq),planning_realization=b,production_loss_hr=a,compiled_exact_loss_hr=v,absolute_error=abs(a-v)))
    pd.DataFrame(rows).to_csv(OUT/'NEW_CANDIDATE_PRODUCTION_PARITY.csv',index=False);print('PRODUCTION PARITY',max(r['absolute_error'] for r in rows))
if __name__=='__main__':main()
