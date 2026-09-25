"""Exact discrete source-path diagnostics for an unchanged July92 graph.

This module reads functional masks only. It does not generate trajectories or
alter the gate. All path counts are undirected topological counts, not flows.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _flow(capacity, neighbors, degree, start, sink):
    residual = capacity.copy()
    n = residual.shape[0]
    parent = np.empty(n, dtype=np.int16)
    queue = np.empty(n, dtype=np.int16)
    total = 0
    while True:
        parent[:] = -1
        parent[start] = start
        queue[0] = start
        head, tail = 0, 1
        while head < tail and parent[sink] < 0:
            u = queue[head]
            head += 1
            for k in range(degree[u]):
                v = neighbors[u, k]
                if parent[v] < 0 and residual[u, v] > 0:
                    parent[v] = u
                    queue[tail] = v
                    tail += 1
                    if v == sink:
                        break
        if parent[sink] < 0:
            return total
        bottleneck = 32767
        v = sink
        while v != start:
            u = parent[v]
            if residual[u, v] < bottleneck:
                bottleneck = residual[u, v]
            v = u
        v = sink
        while v != start:
            u = parent[v]
            residual[u, v] -= bottleneck
            residual[v, u] += bottleneck
            v = u
        total += bottleneck


@njit(cache=True)
def _reachable(active, source, adjacency, degree, removed_node):
    n = len(active)
    component = np.full(n, -1, dtype=np.int16)
    sizes = np.zeros(n, dtype=np.int16)
    source_counts = np.zeros(n, dtype=np.int16)
    queue = np.empty(n, dtype=np.int16)
    next_component = 0
    for station in range(n):
        if not active[station] or station == removed_node or component[station] >= 0:
            continue
        component[station] = next_component
        queue[0] = station
        head, tail = 0, 1
        while head < tail:
            u = queue[head]
            head += 1
            sizes[next_component] += 1
            if source[u]:
                source_counts[next_component] += 1
            for k in range(degree[u]):
                v = adjacency[u, k]
                if active[v] and v != removed_node and component[v] < 0:
                    component[v] = next_component
                    queue[tail] = v
                    tail += 1
        next_component += 1
    reachable = np.zeros(n, dtype=np.int16)
    for station in range(n):
        if component[station] >= 0:
            reachable[station] = source_counts[component[station]]
    return component, sizes, reachable


@njit(cache=True)
def characterize_mask(active, source_flag, edge_u, edge_v, adjacency, degree):
    """Return 92 x 9 exact metrics: F, local source, C, source count,
    edge paths/cut, node paths/cut, bridge dependence, articulation
    dependence, single path, disconnected. Source-local cuts use -1.
    """
    n = len(active)
    source = active & source_flag
    component, sizes, source_count = _reachable(active, source, adjacency, degree, -1)
    metrics = np.zeros((n, 10), dtype=np.int16)
    metrics[:, 0] = active.astype(np.int16)
    metrics[:, 1] = source.astype(np.int16)
    metrics[:, 2] = (source_count > 0).astype(np.int16)
    metrics[:, 3] = source_count
    metrics[:, 9] = (source_count == 0).astype(np.int16)

    # Fixed adjacency lists hold both directions, including residual reverses.
    en = n + 1
    ec = np.zeros((en, en), dtype=np.int16)
    e_neighbors = np.zeros((en, en), dtype=np.int16)
    e_degree = np.zeros(en, dtype=np.int16)
    nn = 2*n + 1
    nc = np.zeros((nn, nn), dtype=np.int16)
    n_neighbors = np.zeros((nn, nn), dtype=np.int16)
    n_degree = np.zeros(nn, dtype=np.int16)
    for i in range(n):
        # In-to-out vertex edge; source terminal capacity one means paths
        # ending at distinct source nodes remain distinct.
        n_neighbors[i, n_degree[i]] = i+n
        n_degree[i] += 1
        n_neighbors[i+n, n_degree[i+n]] = i
        n_degree[i+n] += 1
        if active[i]:
            nc[i, i+n] = 1
        e_neighbors[i, e_degree[i]] = n
        e_degree[i] += 1
        e_neighbors[n, e_degree[n]] = i
        e_degree[n] += 1
        n_neighbors[i+n, n_degree[i+n]] = 2*n
        n_degree[i+n] += 1
        n_neighbors[2*n, n_degree[2*n]] = i+n
        n_degree[2*n] += 1
        if source[i]:
            ec[i, n] = n
            nc[i+n, 2*n] = 1
    active_degree = np.zeros(n, dtype=np.int16)
    for k in range(len(edge_u)):
        u, v = edge_u[k], edge_v[k]
        if not active[u] or not active[v]:
            continue
        active_degree[u] += 1
        active_degree[v] += 1
        ec[u, v] = 1
        ec[v, u] = 1
        e_neighbors[u, e_degree[u]] = v
        e_degree[u] += 1
        e_neighbors[v, e_degree[v]] = u
        e_degree[v] += 1
        nc[u+n, v] = n
        nc[v+n, u] = n
        n_neighbors[u+n, n_degree[u+n]] = v
        n_degree[u+n] += 1
        n_neighbors[v, n_degree[v]] = u+n
        n_degree[v] += 1
        n_neighbors[v+n, n_degree[v+n]] = u
        n_degree[v+n] += 1
        n_neighbors[u, n_degree[u]] = v+n
        n_degree[u] += 1

    for station in range(n):
        if not active[station] or source_count[station] == 0:
            continue
        if source[station]:
            ec[station, n] = 0
            nc[station+n, 2*n] = 0
        edge_paths = _flow(ec, e_neighbors, e_degree, station, n)
        node_paths = _flow(nc, n_neighbors, n_degree, station+n, 2*n)
        if source[station]:
            ec[station, n] = n
            nc[station+n, 2*n] = 1
        metrics[station, 4] = edge_paths
        metrics[station, 5] = node_paths
        metrics[station, 8] = (not source[station] and edge_paths == 1)
        if source[station]:
            # Own zero-length source capability has no upstream cut.
            metrics[station, 4] = -edge_paths - 1
            metrics[station, 5] = -node_paths - 1

    # An edge cut of one is precisely a source-separating bridge in this
    # undirected graph. Node dependence requires an internal articulation;
    # distinct-source terminal limits alone do not establish it.
    metrics[:, 6] = metrics[:, 8]
    for removed in range(n):
        if not active[removed] or active_degree[removed] < 2:
            continue
        remaining_component, _, remaining = _reachable(active, source, adjacency, degree, removed)
        first_component = -1
        is_articulation = False
        for station in range(n):
            if station == removed or not active[station] or component[station] != component[removed]:
                continue
            if first_component < 0:
                first_component = remaining_component[station]
            elif remaining_component[station] != first_component:
                is_articulation = True
                break
        if not is_articulation:
            continue
        for station in range(n):
            if station != removed and active[station] and source_count[station] > 0 and remaining[station] == 0:
                metrics[station, 7] = 1
    return metrics
