"""Exact-equivalence checks for computational GA acceleration, no new science."""

import unittest

import networkx as nx
import numpy as np
import pandas as pd

from r1_ga_revision import (evaluate_direct_population_burden,
                            evaluate_direct_population_burden_aggregate)
from r1_realization_scheduling import RealizationInputs
from r1_source_gate import evaluate_source_gate, gate_callback


class FormalObjectiveEquivalence(unittest.TestCase):
    def test_monotone_gate_matches_induced_components(self):
        graph=nx.Graph([('S','A'),('A','B'),('B','C')])
        raw=pd.DataFrame([[1,.09,.5,.03],[1,1,.5,.03],[1,1,1,.03],[1,1,1,1]],
                         index=[0.,2.,5.,9.],columns=['S','A','B','C'])
        trace=evaluate_source_gate(raw,graph,['S'],threshold=.5)
        for row in range(len(raw)):
            nodes={s for s in raw.columns if raw.iloc[row][s]>=.5}
            keep=set()
            for component in nx.connected_components(graph.subgraph(nodes)):
                if 'S' in component:keep.update(component)
            np.testing.assert_array_equal(trace.C.iloc[row].to_numpy(bool),
                                          np.array([s in keep for s in raw.columns]))
        self.assertTrue(np.allclose(trace.e.to_numpy(),trace.f.to_numpy()*trace.F.to_numpy()*trace.C.to_numpy()))

    def test_aggregate_direct_objective_matches_full_tract_calculation(self):
        ids=pd.Index(['S','A','B','C'])
        graph=nx.Graph([('S','A'),('A','B'),('B','C')])
        realization=RealizationInputs('fixture',pd.Series([0,2,1,4],index=ids),
                                      pd.Series([0.,2.,3.,5.],index=ids))
        base=pd.DataFrame([[0.,1.,2.,3.]],index=['yard'],columns=ids)
        travel=pd.DataFrame([[0.,1.,2.,3.],[1.,0.,1.,2.],[2.,1.,0.,1.],[3.,2.,1.,0.]],
                            index=ids,columns=ids)
        W=np.array([[.4,.6,0,0],[0,.2,.3,.5]],float)
        population=pd.Series([100.,50.],index=['t1','t2'])
        gate=gate_callback(graph,['S'],threshold=.5)
        station_mass=W.T@population.to_numpy(float)
        for sequence in [('S','A','B','C'),('C','B','A','S')]:
            fixed=dict(sequence=sequence,realization=realization,crew_origin_ids=['yard','yard'],
                       base_to_task_hr=base,task_to_task_hr=travel,source_gate=gate)
            full=evaluate_direct_population_burden(**fixed,time_hr=[0.,20.],
                       tract_weight_matrix=W,tract_ids=population.index,tract_population=population)
            fast=evaluate_direct_population_burden_aggregate(**fixed,horizon_hr=20.,
                       station_population_mass=station_mass,population_resolved_mass=float(station_mass.sum()))
            self.assertAlmostEqual(fast,full['population_burden_hr'],places=11)


if __name__=='__main__':unittest.main()
