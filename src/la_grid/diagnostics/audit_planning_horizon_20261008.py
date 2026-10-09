"""Verify fixed planning/evaluation horizons agree without re-optimizing."""
import json,numpy as np,networkx as nx
from la_grid.diagnostics import ga_search_budget_sensitivity as old
from la_grid.revision.r1_ga_exact_kernel import _one_sample
from la_grid.paths import REPO_ROOT as R

def main():
    kernel,inc,inputs=old.load_inputs()
    from la_grid.revision.r1_equity_amendment_execute import execution_context
    context,_,_=execution_context(kernel.ids)
    travel=max(float(np.max(kernel.base)),float(np.max(kernel.travel)));crew=len(kernel.origin_index)
    bounds=[]
    for ds,duration in zip(kernel.damage,kernel.duration):
        jobs=duration[ds>0]+travel
        bounds.append(float(jobs.sum()/crew+(1-1/crew)*jobs.max()))
    assert max(bounds)<480
    assert all(set(component)&context['sources'] for component in nx.connected_components(context['graph']))
    checks=[]
    for folder in sorted(old.OUT.glob('p*_g*_s*')):
        run=json.loads((folder/'RUN.json').read_text());seq=run['best_non_incumbent_sequence'];order=np.array([kernel.index[s] for s in seq],dtype=np.int64)
        short=np.array([_one_sample(order,kernel.damage[i],kernel.duration[i],kernel.origin_index,kernel.base,kernel.travel,kernel.neighbor_offset,kernel.neighbors,kernel.source_flag,kernel.station_mass,kernel.total_mass,480.) for i in range(64)])
        long=old.per_sample(kernel,seq);checks.append({'run':folder.name,'max_realization_abs_difference':float(np.max(abs(short-long)))})
    assert max(c['max_realization_abs_difference'] for c in checks)<1e-8
    record={'planning_horizon_hr':kernel.horizon,'manuscript_horizon_hr':480,'all_permutation_completion_upper_bound_hr':max(bounds),'per_realization_upper_bound_hr':bounds,'proof':'Earliest-release dispatch has each job occupation bounded by duration+maximum directed travel. Thus makespan <= sum(job bounds)/C + (1-1/C)*max(job bound), for every order. After all repairs, every intact component has a Core source, so service loss is zero beyond this bound.','completion_bound_is_order_independent':True,'full_graph_components_all_source_connected':True,'numerical_checks':checks}
    path=R/'results/diagnostics/extended_ga_20261008/PLANNING_HORIZON_AUDIT.json';path.write_text(json.dumps(record,indent=2)+'\n')
if __name__=='__main__':main()
