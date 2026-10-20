"""Exact fast decode of frozen July92 event schedules, without recovery evaluation.

This implements the same static DS>0 queue and earliest-free-crew rule as
``execute_realization_schedule``. The original expanded main calls it for the
formal schedule prepass needed to freeze a single evaluation horizon.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _decode(order, ds, duration, origins, base, task):
    n = len(ds)
    clocks = np.zeros(len(origins), dtype=np.float64)
    previous = np.full(len(origins), -1, dtype=np.int64)
    completion = np.full(n, np.nan, dtype=np.float64)
    arrival = np.full(n, np.nan, dtype=np.float64)
    travel = np.full(n, np.nan, dtype=np.float64)
    crew = np.full(n, -1, dtype=np.int64)
    prior = np.full(n, -1, dtype=np.int64)
    dispatch = np.full(n, -1, dtype=np.int64)
    rank = 0
    for position in range(n):
        station = order[position]
        if ds[station] == 0:
            continue
        selected = 0
        for c in range(1, len(origins)):
            if clocks[c] < clocks[selected]:
                selected = c
        prev = previous[selected]
        leg = base[origins[selected], station] if prev < 0 else task[prev, station]
        start = clocks[selected] + leg
        finish = start + duration[station]
        arrival[station] = start
        travel[station] = leg
        completion[station] = finish
        crew[station] = selected
        prior[station] = prev
        dispatch[station] = rank
        rank += 1
        clocks[selected] = finish
        previous[selected] = station
    return completion, arrival, travel, crew, prior, dispatch, clocks


class FormalScheduleDecoder:
    def __init__(self, context):
        self.ids = tuple(map(str, context["ids"]))
        self.lookup = {name: i for i, name in enumerate(self.ids)}
        if len(self.ids) != 92 or len(self.lookup) != 92:
            raise ValueError("Formal schedule decoder requires frozen July92 IDs")
        origin_keys = tuple(map(str, context["base"].index))
        key_index = {key: i for i, key in enumerate(origin_keys)}
        self.key_index = key_index
        self.base = np.ascontiguousarray(context["base"].loc[list(origin_keys), list(self.ids)].to_numpy(float))
        self.task = np.ascontiguousarray(context["task"].loc[list(self.ids), list(self.ids)].to_numpy(float))
        if not np.isfinite(self.base).all() or not np.isfinite(self.task).all():
            raise ValueError("Frozen directed travel is incomplete")

    def order(self, sequence):
        seq = tuple(map(str, sequence))
        if len(seq) != 92 or set(seq) != set(self.ids):
            raise ValueError("Formal strategy must be a full July92 permutation")
        return np.array([self.lookup[name] for name in seq], dtype=np.int64)

    def origins(self, crew_origin_ids):
        crew = tuple(map(str, crew_origin_ids))
        if not crew or any(key not in self.key_index for key in crew):
            raise ValueError("Crew roster contains an unknown directed-travel origin")
        return np.array([self.key_index[key] for key in crew], dtype=np.int64)

    def decode(self, *, order, damage, duration, origins):
        ds = np.asarray(damage, dtype=np.int64)
        d = np.asarray(duration, dtype=np.float64)
        if ds.shape != (92,) or d.shape != (92,) or not np.isin(ds, np.arange(5)).all():
            raise ValueError("Formal damage/duration vectors must cover 92 stations")
        if not np.isfinite(d).all() or np.any(d[ds == 0] != 0) or np.any(d[ds > 0] <= 0):
            raise ValueError("Formal DS/duration contract failed")
        return _decode(np.asarray(order, dtype=np.int64), ds, d,
                       np.asarray(origins, dtype=np.int64), self.base, self.task)
