"""Exact path/cut semantics against the retained NetworkX diagnostic."""

import networkx as nx
import numpy as np

from r1_dynamic_topology_kernel import characterize_mask
from r1_topology_robustness import characterize_topology


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
