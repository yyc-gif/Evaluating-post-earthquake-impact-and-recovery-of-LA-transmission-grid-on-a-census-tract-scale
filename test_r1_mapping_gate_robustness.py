import unittest
import tempfile
from pathlib import Path
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
    def test_paired_offline_tables_and_archive_guard(self):
        from r1_source_gate import save_gate_trace
        from evaluate_mapping_gate_archive import validate_paired_archives
        summaries=[];tracts=[]
        for rid in ['r0','r1']:
            for strategy in ['reference','alternative']:
                raw=self.f.copy()
                if strategy=='alternative':raw.loc[0,'A']=1
                a,b,_=evaluate_saved_trajectory(raw,self.g,['S'],{'M1_UTILITY_003':self.w},self.pop,self.q,set(),realization_id=rid,strategy_id=strategy)
                summaries.append(a);tracts.append(b)
        a=pd.concat(summaries);b=pd.concat(tracts)
        effects=tract_effects(b,self.pop,self.q,reference_strategy='reference')
        self.assertTrue(effects.loc[effects.tract_id.eq('u'),'paired_probability_delta_below_zero'].isna().all())
        totals=classification_population_summary(effects)
        unresolved=totals[totals.quartile.eq('all')&totals.classification.eq('unresolved')]
        self.assertTrue(unresolved.population.eq(3).all())
        self.assertTrue(unresolved.population_fraction.eq(.5).all())
        self.assertFalse(paired_effects(a,'population_T80_hr',reference_strategy='reference',bootstrap_resamples=20).empty)
        self.assertFalse(paired_assumption_effects(a,'population_T80_hr',bootstrap_resamples=20).empty)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);trace=evaluate_source_gate(self.f,self.g,['S'])
            for strategy in ['reference','alternative']:
                save_gate_trace(trace,root/(strategy+'.npz'),realization_id='r0',strategy_id=strategy,physical_input_hash='a'*64,frozen_context_hash='b'*64)
            index=pd.DataFrame({'realization_id':['r0','r0'],'strategy_id':['reference','alternative'],'npz_file':['reference.npz','alternative.npz']})
            validate_paired_archives(index,root)
            save_gate_trace(trace,root/'alternative.npz',realization_id='r0',strategy_id='alternative',physical_input_hash='c'*64,frozen_context_hash='b'*64)
            with self.assertRaisesRegex(ValueError,'pairing'):validate_paired_archives(index,root)
if __name__=='__main__':unittest.main()
