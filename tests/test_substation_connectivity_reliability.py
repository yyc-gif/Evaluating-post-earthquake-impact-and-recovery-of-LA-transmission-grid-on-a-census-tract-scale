import numpy as np

from la_grid.diagnostics.r1_dynamic_topology_kernel import station_independent_routes_mask
from la_grid.diagnostics.substation_connectivity_reliability import _forced_importance_counts


def test_shared_source_endpoint_allows_two_independent_station_routes():
    # The same active source may terminate paths 3-1-0 and 3-2-0.
    active = np.array([1, 1, 1, 1], dtype=np.bool_)
    source = np.array([1, 0, 0, 0], dtype=np.bool_)
    edge_u = np.array([0, 0, 1, 2], dtype=np.int16)
    edge_v = np.array([1, 2, 3, 3], dtype=np.int16)
    routes = station_independent_routes_mask(active, source, edge_u, edge_v)
    assert routes.tolist() == [-1, 2, 2, 2]


def test_forced_station_importance_uses_identical_other_states():
    source = np.array([1, 0, 0, 0], dtype=np.bool_)
    edge_u = np.array([0, 0, 1, 2], dtype=np.int16)
    edge_v = np.array([1, 2, 3, 3], dtype=np.int16)
    adjacency = np.zeros((4, 4), dtype=np.int16)
    degree = np.zeros(4, dtype=np.int16)
    for u, v in zip(edge_u, edge_v):
        adjacency[u, degree[u]] = v
        adjacency[v, degree[v]] = u
        degree[u] += 1
        degree[v] += 1
    states = np.array([[1, 1, 1, 1], [1, 1, 0, 1]], dtype=np.bool_)
    counts = _forced_importance_counts(states, source, adjacency, degree)
    assert counts[1, 3] == 1  # other route exists in only one of two states
    assert counts[1, 1] == 2  # direct availability under the intervention
    assert counts[0, 3] == 2  # forcing the sole source on versus off
