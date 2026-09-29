"""Exact path/cut semantics against the retained NetworkX diagnostic."""

import networkx as nx
import numpy as np

from la_grid.diagnostics.r1_dynamic_topology_kernel import characterize_mask, station_independent_routes_mask
from la_grid.diagnostics.r1_topology_robustness import characterize_topology
from la_grid.diagnostics.r1_connectivity_state_analysis import state_class


def _arrays(graph, ids):
    lookup = {s:i for i,s in enumerate(ids)}
    edges = np.asarray([(lookup[u],lookup[v]) for u,v in graph.edges], dtype=np.int16)
    adj = np.zeros((len(ids),len(ids)), dtype=np.int16)
    deg = np.zeros(len(ids), dtype=np.int16)
    for u,v in edges:
        adj[u,deg[u]],adj[v,deg[v]] = v,u
        deg[u] += 1
        deg[v] += 1
    return edges[:,0],edges[:,1],adj,deg


def test_synthetic_exact_paths_and_source_local_handling():
    graph = nx.Graph()
    graph.add_nodes_from(list("ABCDEFG"))
    graph.add_edges_from([("A","B"),("B","C"),("C","D"),("B","E"),
                          ("E","F"),("F","C"),("F","G")])
    ids = sorted(graph)
    edge_u,edge_v,adj,deg = _arrays(graph, ids)
    sources = {"A","D"}
    sf = np.asarray([s in sources for s in ids], dtype=np.bool_)
    for active_names in (set(ids),set("ABCEFG"),set("BCDEFG"),set("BCEFG"),set("ACDEG")):
        active = np.asarray([s in active_names for s in ids],dtype=np.bool_)
        observed = characterize_mask(active,sf,edge_u,edge_v,adj,deg)
        old = characterize_topology(graph.subgraph(active_names),sources & active_names)
        for i,station in enumerate(ids):
            if station not in active_names:
                assert observed[i,0] == 0
                continue
            row = old.loc[station]
            assert observed[i,2] == int(not row.disconnected)
            assert observed[i,3] == row.reachable_active_sources
            expected_edge = row.edge_disjoint_remote_source_paths
            expected_node = row.node_disjoint_distinct_remote_source_paths
            if station in sources:
                assert observed[i,4] == -expected_edge-1
                assert observed[i,5] == -expected_node-1
            else:
                assert observed[i,4] == expected_edge
                assert observed[i,5] == expected_node
                assert observed[i,8] == row.single_path
            assert observed[i,6] == bool(row.bridge_dependencies)
            assert observed[i,7] == bool(row.articulation_dependencies)


def test_station_routes_can_share_one_source_but_not_internal_station():
    graph=nx.Graph()
    graph.add_edges_from([("T","A"),("T","B"),("A","S"),("B","S")])
    ids=sorted(graph)
    eu,ev,_,_=_arrays(graph,ids)
    active=np.ones(len(ids),dtype=np.bool_)
    source=np.array([i=="S" for i in ids],dtype=np.bool_)
    old=characterize_mask(active,source,eu,ev,*_arrays(graph,ids)[2:])
    routes=station_independent_routes_mask(active,source,eu,ev)
    assert old[ids.index("T"),5]==1  # old terminal allows one per source
    assert routes[ids.index("T")]==2
    assert routes[ids.index("A")]==2
    assert routes[ids.index("S")]==-1
    active[ids.index("B")]=False
    assert station_independent_routes_mask(active,source,eu,ev)[ids.index("T")]==1


def test_multiple_reachable_sources_do_not_imply_multiple_routes():
    graph=nx.Graph()
    graph.add_edges_from([("T","B"),("B","S1"),("B","S2")])
    ids=sorted(graph)
    eu,ev,adj,deg=_arrays(graph,ids)
    active=np.ones(len(ids),dtype=np.bool_)
    source=np.asarray([x in {"S1","S2"} for x in ids],dtype=np.bool_)
    old=characterize_mask(active,source,eu,ev,adj,deg)
    routes=station_independent_routes_mask(active,source,eu,ev)
    assert old[ids.index("T"),3]==2
    assert routes[ids.index("T")]==1


def test_four_classes_partition_existing_service_without_new_weights():
    q=np.zeros((4,10),dtype=np.int16)
    q[:,0]=1
    q[1:,2]=1
    q[1,1]=1
    routes=np.array([0,-1,1,2],dtype=np.int16)
    cls=state_class(q,routes)
    assert cls.tolist()==[0,1,2,3]
    e=np.array([0,.5,.8,1.])
    W=np.array([[.1,.2,.3,.4],[.4,.3,.2,.1]])
    parts=np.stack([W@(e*(cls==j)) for j in (1,2,3)])
    np.testing.assert_allclose(parts.sum(axis=0),W@e,atol=1e-15)
