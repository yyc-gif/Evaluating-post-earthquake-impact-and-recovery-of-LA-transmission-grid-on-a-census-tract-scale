import unittest
import numpy as np,pandas as pd,networkx as nx
from r1_mapping_gate_robustness import *
from r1_source_gate import gate_callback
from r1_realization_scheduling import RealizationInputs,simulate_paired_realization_strategies
class RobustnessTests(unittest.TestCase):
    def setUp(self):
        self.g=nx.path_graph(['S','A','B']);self.f=pd.DataFrame([[1,.09,1],[1,1,1]],index=[0.,2.],columns=list(self.g))
        self.w=pd.DataFrame([[0,1,0],[0,0,1],[0,0,0]],index=['a','b','u'],columns=list(self.g),dtype=float)
        self.pop=pd.Series({'a':2.,'b':1.,'u':3.});self.q=pd.Series({'a':'Q1','b':'Q4','u':'Q2'})
    def test_exact_event_integral_and_decomposition(self):
        trace=evaluate_source_gate(self.f,self.g,['S']);summary,b=evaluate_mapping(trace,self.w,self.pop,self.q,{'a'})
        self.assertEqual(b.loc['a','L_self_mass_hr'],1.82)
        self.assertEqual(b.loc['a','L_threshold_mass_hr'],.18)
        self.assertEqual(b.loc['b','L_source_mass_hr'],2.)
        self.assertEqual(summary.population_T80_hr,2.)
        self.assertTrue(np.isnan(b.loc['u','normalized_burden_hr']))
        self.assertEqual(summary.unresolved_population,3.)
    def test_missing_partial_mass_no_renormalization(self):
        f=self.f.copy();f.B=np.nan;t=evaluate_source_gate(f,self.g,['S'])
        w=self.w.copy();w.loc['a']=[0,.5,.5]
        _,b=evaluate_mapping(t,w,self.pop,self.q,set())
        self.assertEqual(b.loc['a','resolved_mass'],.5)
        self.assertEqual(b.loc['a','restoration_burden_mass_hr'],1.)
        self.assertTrue(np.isnan(b.loc['b','normalized_burden_hr']))
    def test_fixed_schedule_and_offline_views(self):
        ids=list(self.g);real=RealizationInputs('fixture',pd.Series([0,2,0],index=ids),pd.Series([0.,2.,0.],index=ids))
        base=pd.DataFrame(0.,index=['Y'],columns=ids);travel=pd.DataFrame(0.,index=ids,columns=ids)
        result=simulate_paired_realization_strategies(realization=real,strategy_sequences={'fixed':ids},crew_origin_ids=['Y'],base_to_task_hr=base,task_to_task_hr=travel,time_hr=[0.,2.],source_gate=gate_callback(self.g,['S']))['fixed']
        before=result.task_events.copy(deep=True)
        summary,tract,traces=evaluate_saved_trajectory(result.raw_functionality,self.g,['S'],{'test':self.w},self.pop,self.q,set(),realization_id='fixture',strategy_id='fixed')
        pd.testing.assert_frame_equal(before,result.task_events)
        self.assertEqual(len(summary),4);self.assertEqual(traces['G2_RELAXED_005'].C.loc[0,'B'],1)
        self.assertEqual(traces['G1_BASELINE_050'].C.loc[0,'B'],0)
        self.assertIsNotNone(result.gate_trace)
    def test_supported_subset(self):
        maps,c=mapping_cases();s=maps['M3_SCE_SUPPORTED']
        self.assertEqual(len(s),337);self.assertEqual(int((s.sum(axis=1)==0).sum()),17)
        self.assertTrue((s.where(~c,0).to_numpy()==0).all())
        np.testing.assert_allclose(s.sum(axis=1)[s.sum(axis=1)>0],1)
    def test_identity_no_gate(self):
        f=self.f.copy();f[:]=1
        pd.testing.assert_frame_equal(evaluate_source_gate(f,self.g,['S']).e,evaluate_source_gate(f,self.g,['S'],mode='no_gate').e)
if __name__=='__main__':unittest.main()
