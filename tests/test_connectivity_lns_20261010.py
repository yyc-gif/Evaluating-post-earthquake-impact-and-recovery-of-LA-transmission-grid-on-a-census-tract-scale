"""Engineering contracts for proposal-only diagnostics; no physical draws."""
import random
import unittest

import numpy as np

from la_grid.diagnostics.ga_alternative_optimizer_20261009 import Meter
from la_grid.diagnostics.ga_connectivity_lns_local_20261010 import source_times, repair, relocate


class FakeKernel:
    ids = tuple(str(i) for i in range(92))
    index = {s: int(s) for s in ids}

    def score(self, sequence):
        assert len(sequence) == 92 and set(sequence) == set(self.ids)
        return -sum((i + 1) * (int(s) + 1) for i, s in enumerate(sequence)) / 1e6


class ConnectivityTests(unittest.TestCase):
    def test_delayed_source_and_bypass(self):
        # 0--1--2 and 0--3--2: fastest activation bottleneck is through 3.
        offsets = np.array([0, 2, 4, 6, 8], np.int64)
        neighbors = np.array([1, 3, 0, 2, 1, 3, 0, 2], np.int64)
        times, path = source_times(np.array([4., 30., 0., 8.]),
            np.array([True, False, False, False]), offsets, neighbors)
        np.testing.assert_allclose(times, [4., 30., 8., 8.])
        self.assertEqual(path[2], 3)

    def test_no_source_stays_disconnected(self):
        times, _ = source_times(np.array([0., 1.]), np.array([False, False]),
            np.array([0, 1, 2], np.int64), np.array([1, 0], np.int64))
        self.assertTrue(np.isinf(times).all())

    def test_full_noncontiguous_beam_and_budget(self):
        k = FakeKernel()
        parent = k.ids
        meter = Meter(k, 80)
        candidate, score, effort, separated = repair(parent, (1, 20, 60, 85),
            list(range(91, -1, -1)), k, random.Random(1180), meter)
        self.assertEqual(set(candidate), set(parent))
        self.assertGreaterEqual(score, k.score(parent))
        self.assertLessEqual(meter.expensive, 80)
        self.assertGreater(effort, 0)
        self.assertEqual(separated, max(candidate.index(str(i)) for i in (1, 20, 60, 85))
            - min(candidate.index(str(i)) for i in (1, 20, 60, 85)) + 1 > 4)

    def test_relocation_keeps_other_relative_priorities(self):
        seq = FakeKernel.ids
        moved = relocate(seq, '80', 10)
        self.assertEqual(tuple(s for s in moved if s != '80'), tuple(s for s in seq if s != '80'))
        self.assertEqual(moved[10], '80')


if __name__ == '__main__':
    unittest.main()
