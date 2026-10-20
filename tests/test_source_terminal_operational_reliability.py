"""Small exact checks for the station-only source-terminal reliability kernel."""
import unittest

import numpy as np

from la_grid.diagnostics.source_terminal_operational_reliability import (
    best_paths, _component_counts, _required_path_masks)


def _run_kernel(states, u, v, source, r):
    n=len(r)
    adj=np.full((n,n),-1,dtype=np.int16)
    degree=np.zeros(n,dtype=np.int16)
    for a,b in zip(u,v):
        adj[a,degree[a]]=b;degree[a]+=1
        adj[b,degree[b]]=a;degree[b]+=1
    ids=[str(i) for i in range(n)]
    exact,paths,_=best_paths(ids,u,v,source,r)
    source_ix=np.flatnonzero(source).astype(np.int16)
    individual=[best_paths(ids,u,v,np.arange(n)==s,r) for s in source_ix]
    blo,bhi=_required_path_masks([[p] for p in paths])
    slo,shi=_required_path_masks([[x[1][i] for x in individual] for i in range(n)])
    counts=_component_counts(states,u,v,adj,degree,source_ix,
                             np.array([len(states)]),blo[:,0],bhi[:,0],slo,shi)
    return exact,counts


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
        exact,(f,c,path,by_source,best,residual,source_best,source_residual)=_run_kernel(
            states,u,v,np.array([False,True,True]),np.array([0.1,0.5,0.5]))
        self.assertEqual(f[0, 0], 0)
        self.assertEqual(c[0, 0], 0)
        self.assertEqual(path[0, 0], 3)
        self.assertEqual(by_source[0, 0].tolist(), [2, 2])
        # Each active source is connected to itself conditional on functioning.
        self.assertEqual(path[0, 1], 4)
        self.assertEqual(path[0, 2], 4)
        self.assertTrue(np.all(residual>=0))
        self.assertTrue(np.all(source_residual>=0))
        self.assertTrue(np.all(best<=path))  # B is an event subset of A
        self.assertTrue(np.all(source_best<=by_source))
        self.assertAlmostEqual(exact[0]+residual[0,0]/4,.75)
        self.assertEqual(source_residual[0,0].tolist(),[0,0])

    def test_exact_enumeration_and_zero_extra_hits(self):
        # Diamond: target 0 reaches source 3 through middle 1 or 2.
        # Exact P(A|F0)=r3*(r1+r2-r1*r2)=.532; best path uses 2: .42.
        u=np.array([0,1,0,2],dtype=np.int16)
        v=np.array([1,3,2,3],dtype=np.int16)
        r=np.array([.2,.4,.6,.7])
        source=np.array([False,False,False,True])
        exact,_=_run_kernel(np.zeros((1,4),dtype=np.bool_),u,v,source,r)
        self.assertAlmostEqual(exact[0],.42)
        residual_exact=0.
        for b1 in (0,1):
            for b2 in (0,1):
                for b3 in (0,1):
                    state=np.array([[False,b1,b2,b3]],dtype=np.bool_)
                    _,counts=_run_kernel(state,u,v,source,r)
                    event=int(counts[5][0,0])
                    weight=(r[1] if b1 else 1-r[1])*(r[2] if b2 else 1-r[2])*(r[3] if b3 else 1-r[3])
                    residual_exact+=weight*event
        self.assertAlmostEqual(residual_exact,.112)
        self.assertAlmostEqual(exact[0]+residual_exact,.532)
        # A finite sample with no extra-path hits still returns the exact
        # fixed-path probability, not max(raw full MC, exact path).
        states=np.zeros((3,4),dtype=np.bool_)
        _,counts=_run_kernel(states,u,v,source,r)
        self.assertEqual(counts[5][0,0],0)
        self.assertAlmostEqual(exact[0]+counts[5][0,0]/3,.42)
        rng=np.random.default_rng(123)
        sampled=rng.random((100_000,4))<r
        _,counts=_run_kernel(sampled,u,v,source,r)
        self.assertAlmostEqual(exact[0]+counts[5][0,0]/len(sampled),.532,delta=.005)


if __name__ == "__main__":
    unittest.main()
