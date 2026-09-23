"""Topological redundancy only; no flow, thermal capacity, or new edges."""
import numpy as np
import pandas as pd
import networkx as nx
from r1_mapping_gate_robustness import event_integral


def characterize_topology(graph, active_sources):
    sources=set(active_sources)&set(graph);rows=[]
    if len(graph)==0:
        return pd.DataFrame(index=pd.Index([],name='station_id'),columns=['reachable_active_sources','minimum_edge_source_cut','minimum_node_source_cut','single_path','single_upstream_station'])
    bridges=list(nx.bridges(graph));arts=list(nx.articulation_points(graph))
    bridge_dependence={s:[] for s in graph};node_dependence={s:[] for s in graph}
    reachable_before={s:bool(set(nx.node_connected_component(graph,s))&sources) for s in graph}
    for u,v in bridges:
        z=graph.copy();z.remove_edge(u,v)
        for component in nx.connected_components(z):
            if not (set(component)&sources):
                for s in component:
                    if reachable_before[s]:bridge_dependence[s].append('|'.join(sorted([u,v])))
    for node in arts:
        z=graph.copy();z.remove_node(node)
        for component in nx.connected_components(z):
            if not (set(component)&sources):
                for s in component:
                    if reachable_before[s]:node_dependence[s].append(node)
    # Reuse the same auxiliary network across non-source stations in a component.
    # This changes construction cost only, not capacities or path definitions.
    from networkx.algorithms.connectivity import build_auxiliary_node_connectivity
    from networkx.algorithms.connectivity.cuts import minimum_st_node_cut
    from networkx.algorithms.flow import build_residual_network
    auxiliary_cache={}
    for station in graph:
        component=set(nx.node_connected_component(graph,station));reachable=sources & component
        # Root source has a zero-edge local supply path. Report remote redundancy
        # separately instead of a fabricated finite cut of its own source capability.
        remote=reachable-{station};h=graph.subgraph(component).copy();sink='__source_sink__'
        if sink in h:raise ValueError('Reserved node name')
        h.add_node(sink)
        flow=nx.DiGraph()
        for u,v in h.edges:flow.add_edge(u,v,capacity=1);flow.add_edge(v,u,capacity=1)
        flow.add_node(sink)
        for source in remote:flow.add_edge(source,sink,capacity=len(graph)+1);h.add_edge(source,sink)
        if remote:
            edge_cut=int(nx.minimum_cut_value(flow,station,sink,capacity='capacity'))
            key=(frozenset(component),frozenset(remote))
            if key not in auxiliary_cache:
                auxiliary=build_auxiliary_node_connectivity(h)
                auxiliary_cache[key]=(auxiliary,build_residual_network(auxiliary,'capacity'))
            auxiliary,residual=auxiliary_cache[key]
            node_cut=minimum_st_node_cut(h,station,sink,auxiliary=auxiliary,residual=residual)
            node_paths=len(node_cut)  # independent original nodes incl. distinct terminal sources
        else:edge_cut=0;node_cut=set();node_paths=0
        dependent_bridges=bridge_dependence[station];dependent_nodes=node_dependence[station]
        rows.append(dict(station_id=station,local_active_source=station in sources,reachable_active_sources=len(reachable),
            reachable_active_source_ids=';'.join(sorted(reachable)),edge_disjoint_remote_source_paths=edge_cut,
            node_disjoint_distinct_remote_source_paths=node_paths,minimum_edge_source_cut=np.nan if station in sources else edge_cut,
            minimum_node_source_cut=np.nan if station in sources else node_paths,one_minimum_node_cut=';'.join(sorted(node_cut)),
            source_removal_only_cut_size=len(reachable),bridge_dependencies=';'.join(sorted(dependent_bridges)),
            articulation_dependencies=';'.join(sorted(dependent_nodes)),single_source=len(reachable)==1,
            single_path=(station not in sources and edge_cut==1),
            single_upstream_station=(station not in sources and node_paths==1),
            disconnected=len(reachable)==0))
    return pd.DataFrame(rows).set_index('station_id')


def dynamic_redundancy(trace, graph):
    """Cache each distinct functional graph; can be expensive, never reschedules."""
    cache={};rows=[]
    for t,F in trace.F.iterrows():
        active=tuple(F.index[F.eq(1)]);key=active
        if key not in cache:cache[key]=characterize_topology(graph.subgraph(active),set(trace.source_ids)&set(active))
        df=cache[key].reindex(trace.f.columns).copy()
        df['functional']=F
        df['event_time_hr']=t
        rows.append(df.rename_axis('station_id').reset_index())
    return pd.concat(rows,ignore_index=True)


def source_loss_contributions(trace, weights, population, topology):
    """Allocation of modeled source-path loss, not causal station attribution."""
    w=weights.reindex(columns=trace.f.columns)
    pop=population.reindex(w.index)
    if pop.isna().any():raise ValueError('Missing population')
    represented_population_weight=w.T@pop
    integral=event_integral(trace.L_source.fillna(0),trace.f.index)
    known=trace.f.notna().iloc[0].to_numpy();integral[~known]=np.nan
    x=pd.DataFrame({'source_loss_integral_hr':integral,'population_dependency_weight':represented_population_weight},index=trace.f.columns)
    x['population_source_loss_mass_hr']=x.source_loss_integral_hr*x.population_dependency_weight
    total=x.population_source_loss_mass_hr.sum(min_count=1)
    x['fraction_of_source_loss']=x.population_source_loss_mass_hr/total if total>0 else np.nan
    return x.join(topology).sort_values('population_source_loss_mass_hr',ascending=False)
