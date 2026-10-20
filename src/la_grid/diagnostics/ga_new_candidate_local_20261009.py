"""Deterministic refinement of the planning-best new operator candidate."""
import json,psutil
from la_grid.diagnostics.ga_hyperparameter_study_20261009 import OUT,load
from la_grid.diagnostics.ga_local_refinement_20261009 import refine
from la_grid.diagnostics import ga_search_budget_sensitivity as old


def main():
    paths=list((OUT/'operator_confirmation').glob('*/RUN.json'));source=min(paths,key=lambda p:json.loads(p.read_text())['best_planning_loss_hr']);record=json.loads(source.read_text());kernel,_,_=load();result,cache=refine(kernel=kernel,start_sequence=record['best_sequence'],budget=100000,folder=OUT/'local_search/operator_best');result.update(initial_sequence_source=source.relative_to(old.ROOT).as_posix(),starting_search_cost_not_in_this_additional_budget=True,peak_rss_mb=getattr(psutil.Process().memory_info(),'peak_wset',psutil.Process().memory_info().rss)/2**20);folder=OUT/'local_search/operator_best';(folder/'RUN.json').write_text(json.dumps(result,indent=2)+'\n')
    import numpy as np
    keys=list(cache);np.savez_compressed(folder/'CANDIDATES.npz',orders=np.array([np.frombuffer(k,dtype=np.uint8) for k in keys]),fitness=np.array([cache[k] for k in keys]));print('NEW LOCAL',result['best_planning_loss_hr'],result['distinct_evaluations'],result['local_optimal_up_to_1e_minus_9'],flush=True)
if __name__=='__main__':main()
