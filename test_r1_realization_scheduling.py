import unittest
import numpy as np
import pandas as pd
from r1_realization_scheduling import RealizationInputs,draw_positive_normal,execute_realization_schedule,simulate_paired_realization_strategies
class T(unittest.TestCase):
 def setUp(self):
  self.ids=pd.Index(['S','A','B','C']);self.ds=pd.Series([0,1,2,0],index=self.ids);self.du=pd.Series([0.,2.,5.,0.],index=self.ids)
  self.base=pd.DataFrame([[0.,1.,1.,1.]],index=['Y'],columns=self.ids);self.travel=pd.DataFrame(0.,index=self.ids,columns=self.ids);self.travel.loc['A','B']=2.;self.travel.loc['B','A']=7.
 def schedule(self,du=None,seq=None):return execute_realization_schedule(full_priority_sequence=self.ids if seq is None else seq,damage_state=self.ds,realized_duration_hr=self.du if du is None else du,crew_origin_ids=['Y'],base_to_task_hr=self.base,task_to_task_hr=self.travel)
 def test_tasks_duration_release(self):
  e,c,clock,q=self.schedule();self.assertEqual(q,('A','B'));self.assertTrue(np.isnan(c.S) and np.isnan(c.C));self.assertEqual(e.completion_hr.tolist(),[3.,10.]);self.assertEqual(e.crew_available_before_hr.tolist(),[0.,3.]);self.assertEqual(clock.tolist(),[10.])
 def test_duration_changes_release_not_order(self):
  _,_,a,qa=self.schedule();du=self.du.copy();du.A=8.;_,_,b,qb=self.schedule(du);self.assertEqual(qa,qb);self.assertGreater(b[0],a[0])
 def test_pair_gate_and_clock(self):
  physical=RealizationInputs('mc_000000',self.ds,self.du)
  def gate(f):
   o=f.copy()
   for t in o.index:
    fun={s for s in ['S','A','B'] if o.loc[t,s]>=.5};keep={'S'} if 'S' in fun else set()
    if 'A' in fun and 'S' in keep:keep.add('A')
    if 'B' in fun and 'A' in keep:keep.add('B')
    o.loc[t,[s for s in o.columns if s not in keep]]=0.
   return o
  x=simulate_paired_realization_strategies(realization=physical,strategy_sequences={'A':['S','A','B','C'],'B':['S','B','A','C']},crew_origin_ids=['Y'],base_to_task_hr=self.base,task_to_task_hr=self.travel,time_hr=[0.,3.,6.,10.,15.],source_gate=gate)
  self.assertEqual(x['A'].filtered_task_sequence,('A','B'));self.assertEqual(x['B'].filtered_task_sequence,('B','A'));self.assertEqual(x['A'].task_events.realized_duration_hr.sum(),7.);self.assertEqual(x['B'].task_events.realized_duration_hr.sum(),7.);self.assertEqual(x['A'].raw_functionality.loc[10.,'B'],1.);self.assertEqual(x['A'].effective_functionality.loc[0.,'B'],0.)
 def test_positive_repeat(self):
  a=draw_positive_normal(np.random.default_rng(42),mean_hr=1.,std_hr=3.,size=500);b=draw_positive_normal(np.random.default_rng(42),mean_hr=1.,std_hr=3.,size=500);self.assertTrue(np.all(a>0));np.testing.assert_array_equal(a,b)
 def test_multiple_crews_share_origin(self):
  e,c,clock,q=execute_realization_schedule(full_priority_sequence=self.ids,damage_state=self.ds,realized_duration_hr=self.du,crew_origin_ids=['Y','Y'],base_to_task_hr=self.base,task_to_task_hr=self.travel)
  self.assertEqual(e.crew_index.tolist(),[0,1]);self.assertEqual(e.arrival_hr.tolist(),[1.,1.]);self.assertEqual(clock.tolist(),[3.,6.])
if __name__=='__main__':unittest.main()
