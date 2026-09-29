"""Compiled exact-value decoder for the frozen direct planning objective.

This is an implementation of the same C57 earliest-release schedule, July
completion-step functionality, 0.5 source-connected gate, and fixed-M1
population-resolved-mass left-rectangle burden. It is not a surrogate or a
different objective. The regular pandas/NetworkX production path remains the
authority for reported trajectories; real-input incumbent parity is checked
before any formal GA seed is resumed.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _find(parent, node):
    while parent[node] != node:
        parent[node] = parent[parent[node]]
        node = parent[node]
    return node


@njit(cache=True)
def _merge(parent, size, credit, has_source, left, right):
    a = _find(parent, left)
    b = _find(parent, right)
    if a == b:
        return 0.0
    old = (credit[a] if has_source[a] else 0.0) + (credit[b] if has_source[b] else 0.0)
    if size[a] < size[b]:
        a, b = b, a
    parent[b] = a
    size[a] += size[b]
    credit[a] += credit[b]
    has_source[a] = has_source[a] or has_source[b]
    new = credit[a] if has_source[a] else 0.0
    return new - old


@njit(cache=True)
def _one_sample(order, ds, duration, origin_index, base, travel, neighbor_offset,
                neighbors, source_flag, station_mass, total_mass, horizon):
    n = len(ds)
    ncrew = len(origin_index)
    clocks = np.zeros(ncrew, dtype=np.float64)
    previous = np.full(ncrew, -1, dtype=np.int64)
    finish = np.full(n, np.inf, dtype=np.float64)
    task_count = 0
    for rank in range(n):
        station = order[rank]
        if ds[station] == 0:
            continue
        crew = 0
        for c in range(1, ncrew):
            if clocks[c] < clocks[crew]:
                crew = c
        distance = (base[origin_index[crew], station] if previous[crew] < 0
                    else travel[previous[crew], station])
        end = clocks[crew] + distance + duration[station]
        clocks[crew] = end
        previous[crew] = station
        finish[station] = end
        task_count += 1

    if np.max(clocks) > horizon:
        return np.nan
    parent = np.arange(n, dtype=np.int64)
    size = np.ones(n, dtype=np.int64)
    credit = np.zeros(n, dtype=np.float64)
    has_source = np.zeros(n, dtype=np.bool_)
    active = np.zeros(n, dtype=np.bool_)
    available = 0.0
    # At threshold 0.5, DS0 and DS1 are functional at t=0.
    for station in range(n):
        if ds[station] <= 1:
            active[station] = True
            initial = 1.0 if ds[station] == 0 else 0.5
            credit[station] = station_mass[station] * initial
            has_source[station] = source_flag[station]
            if has_source[station]:
                available += credit[station]
    for station in range(n):
        if active[station]:
            for pos in range(neighbor_offset[station], neighbor_offset[station + 1]):
                other = neighbors[pos]
                if active[other] and other < station:
                    available += _merge(parent, size, credit, has_source, station, other)

    sorted_tasks = np.argsort(finish)
    previous_time = 0.0
    burden_mass = 0.0
    for rank in range(task_count):
        station = sorted_tasks[rank]
        event_time = finish[station]
        burden_mass += (event_time - previous_time) * (total_mass - available)
        previous_time = event_time
        if active[station]:
            # Only DS1 is initially functional among scheduled tasks.
            root = _find(parent, station)
            increment = station_mass[station] * 0.5
            credit[root] += increment
            if has_source[root]:
                available += increment
        else:
            active[station] = True
            credit[station] = station_mass[station]
            has_source[station] = source_flag[station]
            if has_source[station]:
                available += credit[station]
            for pos in range(neighbor_offset[station], neighbor_offset[station + 1]):
                other = neighbors[pos]
                if active[other]:
                    available += _merge(parent, size, credit, has_source, station, other)
    burden_mass += (horizon - previous_time) * (total_mass - available)
    return burden_mass / total_mass


@njit(cache=True)
def _mean_burden(order, damage, duration, origin_index, base, travel,
                 neighbor_offset, neighbors, source_flag, station_mass,
                 total_mass, horizon):
    total = 0.0
    for sample in range(damage.shape[0]):
        value = _one_sample(order, damage[sample], duration[sample], origin_index,
                            base, travel, neighbor_offset, neighbors, source_flag,
                            station_mass, total_mass, horizon)
        if not np.isfinite(value):
            return np.nan
        total += value
    return total / damage.shape[0]


class ExactDirectPlanningKernel:
    """Once-prepared fixed inputs; score full ID permutations without data copies."""

    def __init__(self, *, planning, context, station_population_mass, horizon_hr):
        ids = tuple(str(x) for x in context["ids"])
        self.ids = ids
        self.index = {station: i for i, station in enumerate(ids)}
        self.damage = np.ascontiguousarray(
            np.stack([r.damage_state.reindex(ids).to_numpy(np.int64) for r in planning]))
        self.duration = np.ascontiguousarray(
            np.stack([r.realized_duration_hr.reindex(ids).to_numpy(np.float64) for r in planning]))
        unique_origins = tuple(str(x) for x in context["base"].index)
        origin_lookup = {name: i for i, name in enumerate(unique_origins)}
        self.origin_index = np.ascontiguousarray(
            np.array([origin_lookup[str(x)] for x in context["origins"]], dtype=np.int64))
        self.base = np.ascontiguousarray(context["base"].loc[list(unique_origins), list(ids)].to_numpy(np.float64))
        self.travel = np.ascontiguousarray(context["task"].loc[list(ids), list(ids)].to_numpy(np.float64))
        adjacency = [set() for _ in ids]
        for a, b in context["G"].edges():
            i, j = self.index[str(a)], self.index[str(b)]
            adjacency[i].add(j)
            adjacency[j].add(i)
        offsets = [0]
        neighbors = []
        for row in adjacency:
            neighbors.extend(sorted(row))
            offsets.append(len(neighbors))
        self.neighbor_offset = np.array(offsets, dtype=np.int64)
        self.neighbors = np.array(neighbors, dtype=np.int64)
        self.source_flag = np.array([station in context["sources"] for station in ids], dtype=np.bool_)
        self.station_mass = np.ascontiguousarray(np.asarray(station_population_mass, dtype=np.float64))
        self.total_mass = float(self.station_mass.sum())
        self.horizon = float(horizon_hr)
        if self.damage.shape != self.duration.shape or self.damage.shape[1] != len(ids):
            raise ValueError("Planning damage/duration identity is incomplete")
        if self.station_mass.shape != (len(ids),) or self.total_mass <= 0:
            raise ValueError("Population-resolved mass is invalid")
        if len(context["sources"]) != 14 or len(ids) != 92 or self.damage.shape[0] != 64:
            raise ValueError("Kernel is restricted to the frozen July92/64 planning case")

    def score(self, sequence):
        names = tuple(str(x) for x in sequence)
        if len(names) != len(self.ids) or set(names) != set(self.ids):
            raise ValueError("Full 92-ID permutation required")
        order = np.array([self.index[name] for name in names], dtype=np.int64)
        burden = _mean_burden(order, self.damage, self.duration, self.origin_index,
                              self.base, self.travel, self.neighbor_offset,
                              self.neighbors, self.source_flag, self.station_mass,
                              self.total_mass, self.horizon)
        if not np.isfinite(burden):
            raise ValueError("Compiled direct objective produced nonfinite burden")
        return -float(burden)
