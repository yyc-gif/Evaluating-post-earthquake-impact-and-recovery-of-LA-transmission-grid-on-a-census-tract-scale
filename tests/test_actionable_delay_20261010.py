import itertools
import unittest
import numpy as np

from la_grid.diagnostics.ga_actionable_delay_20261010 import independent_route_completion_bounds
from la_grid.revision.formal.schedule import _decode


class RouteEnvelopeTests(unittest.TestCase):
    def bounds(self, p, base, travel, mask=None):
        return independent_route_completion_bounds(durations=np.array(p,float),
            base_to_task=np.array(base,float), task_to_task=np.array(travel,float),
            scheduled=np.ones(len(p),bool) if mask is None else np.array(mask,bool))['completion']

    def test_direct_leg_is_not_general_lower_bound(self):
        value = self.bounds([1,2], [[1,10]], [[0,1],[9,0]])
        np.testing.assert_allclose(value,[2,5])

    def test_ds0_cannot_be_a_waypoint(self):
        value = self.bounds([0,2],[[0,10]],[[0,0],[0,0]],[False,True])
        np.testing.assert_allclose(value,[0,12])

    def test_only_actual_origins(self):
        np.testing.assert_allclose(self.bounds([2],[[7]],[[0]]),[9])

    def test_invalid_nonnegative_contract(self):
        for bad in (-1,float('inf'),float('nan')):
            with self.assertRaises(ValueError):
                self.bounds([2],[[bad]],[[0]])

    def test_empty_scheduled_set(self):
        np.testing.assert_allclose(self.bounds([0],[[1]],[[0]],[False]),[0])

    def test_exhaustive_twelve_thousand_small_schedules(self):
        rng=np.random.default_rng(2026101021)
        checked=0
        for instance in range(100):
            n=5
            p=rng.uniform(.01,8,n)
            base=rng.uniform(0,10,(2,n))
            travel=rng.uniform(0,10,(n,n))
            np.fill_diagonal(travel,0)
            lower=self.bounds(p,base,travel)
            for seq in itertools.permutations(range(n)):
                finish=_decode(np.array(seq,np.int64),np.ones(n,np.int64),p,
                    np.array([0,1],np.int64),base,travel)[0]
                self.assertGreaterEqual(float(np.min(finish-lower)),-1e-10)
                checked+=1
        self.assertEqual(checked,12000)


if __name__=='__main__':
    unittest.main()
