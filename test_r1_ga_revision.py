import unittest
import numpy as np
import pandas as pd
from r1_realization_scheduling import RealizationInputs
from r1_ga_revision import RevisedGAConfig,run_revised_permutation_ga,run_multiseed_revised_ga,legacy_station_completion_objective,evaluate_direct_population_burden,direct_population_burden_objective
class GA(unittest.TestCase):
 def test_archive_incumbent_and_reproducibility(self):
  items=('A','B','C','D');objective=lambda x:4.-sum(i!=items.index(v) for i,v in enumerate(x));cfg=RevisedGAConfig(8,5,.8,.2,3);inc={'fixed':items}
  a=run_revised_permutation_ga(items=items,objective=objective,incumbents=inc,seed=7,config=cfg);b=run_revised_permutation_ga(items=items,objective=objective,incumbents=inc,seed=7,config=cfg)
  self.assertEqual(a.best_sequence,items);self.assertEqual(a.candidate_source,'incumbent:fixed');self.assertEqual(a.best_fitness,4.);pd.testing.assert_frame_equal(a.history,b.history);self.assertEqual(len(a.history),6)
  x=run_multiseed_revised_ga(items=items,objective=objective,incumbents=inc,seeds=[7,8],config=cfg);self.assertEqual(set(x),{7,8})
 def test_direct_path_and_legacy_rank_mismatch(self):
  ids=pd.Index(['S','A','B']);ds=pd.Series([0,2,2],index=ids);du=pd.Series([0.,2.,2.],index=ids);real=RealizationInputs('p0',ds,du)
  base=pd.DataFrame([[0.,0.,0.]],index=['Y'],columns=ids);travel=pd.DataFrame(0.,index=ids,columns=ids);W=np.array([[0.,1.,0.],[0.,0.,1.]])
  calls=[]
  def gate(f):
   calls.append(1);o=f.copy()
   for t in o.index:
    fun={s for s in ids if o.loc[t,s]>=.5};keep={'S'} if 'S' in fun else set()
    if 'A' in fun and 'S' in keep:keep.add('A')
    if 'B' in fun and 'A' in keep:keep.add('B')
    o.loc[t,[s for s in ids if s not in keep]]=0.
   return o
  fixed=dict(realization=real,crew_origin_ids=['Y'],base_to_task_hr=base,task_to_task_hr=travel,time_hr=[0.,2.,4.,6.],source_gate=gate,tract_weight_matrix=W,tract_ids=['TA','TB'],tract_population=pd.Series({'TA':100.,'TB':1.}))
  a=('S','A','B');b=('S','B','A');da=evaluate_direct_population_burden(sequence=a,**fixed);db=evaluate_direct_population_burden(sequence=b,**fixed);self.assertLess(da['population_burden_hr'],db['population_burden_hr']);self.assertEqual(len(calls),2)
  direct=direct_population_burden_objective(**fixed);self.assertGreater(direct(a),direct(b))
  legacy=legacy_station_completion_objective(task_priority=pd.Series({'S':0.,'A':1.,'B':10.}),expected_duration_hr=pd.Series({'S':.1,'A':2.,'B':2.}),crew_origin_ids=['Y'],base_to_task_hr=base,task_to_task_hr=travel,tmax_hr=10.,makespan_weight=0.)
  self.assertGreater(legacy(b),legacy(a))
if __name__=='__main__':unittest.main()
