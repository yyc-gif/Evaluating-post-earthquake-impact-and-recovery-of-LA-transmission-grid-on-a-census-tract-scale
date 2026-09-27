"""Small exact checks for the station-only source-terminal reliability kernel."""
import unittest

import numpy as np

from source_terminal_operational_reliability import best_paths, _component_counts


class SourceTerminalReliabilityTests(unittest.TestCase):
    def test_best_path_includes_source_not_target(self):
        ids = ["target", "middle", "source_a", "source_b"]
        u = np.array([0, 1, 0], dtype=np.int16)
        v = np.array([1, 2, 3], dtype=np.int16)
        source = np.array([False, False, True, True])
        r = np.array([0.01, 0.8, 0.9, 0.6])
        score, paths, origin = best_paths(ids, u, v, source, r)
        self.assertAlmostEqual(score[0], 0.8 * 0.9)
        self.assertEqual(paths[0], [0, 1, 2])
        self.assertEqual(origin[0], 2)
        self.assertEqual(score[2], 1.0)

    def test_conditional_connection_and_source_diversity(self):
        # Enumerate all four configurations of two source nodes. The target is
        # always sampled off, so its conditional reliability must still exist.
        states = np.array([[False, False, False], [False, True, False],
                           [False, False, True], [False, True, True]])
        u = np.array([0, 0], dtype=np.int16)
        v = np.array([1, 2], dtype=np.int16)
        adjacency = np.array([[1, 2], [0, -1], [0, -1]], dtype=np.int16)
        degree = np.array([2, 1, 1], dtype=np.int16)
        f, c, path, by_source = _component_counts(
            states, u, v, adjacency, degree,
            np.array([1, 2], dtype=np.int16), np.array([4]))
        self.assertEqual(f[0, 0], 0)
        self.assertEqual(c[0, 0], 0)
        self.assertEqual(path[0, 0], 3)
        self.assertEqual(by_source[0, 0].tolist(), [2, 2])
        # Each active source is connected to itself conditional on functioning.
        self.assertEqual(path[0, 1], 4)
        self.assertEqual(path[0, 2], 4)


if __name__ == "__main__":
    unittest.main()
