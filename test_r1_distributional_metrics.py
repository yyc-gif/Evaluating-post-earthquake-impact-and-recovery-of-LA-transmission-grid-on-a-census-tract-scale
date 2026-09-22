import unittest
import numpy as np
import pandas as pd
from r1_distributional_metrics import assign_fixed_vulnerability_quartiles,compute_tract_burden,population_weighted_gini,summarize_distribution,classify_tract_effects,paired_realization_summary
class Metrics(unittest.TestCase):
 def setUp(self):
  self.service=pd.DataFrame({'1':[0.,.5,1.],'2':[np.nan,np.nan,np.nan]},index=[0.,1.,2.]);self.rm=pd.Series({'1':1.,'2':0.})
 def test_burden_missing(self):
  b=compute_tract_burden(self.service,self.rm);self.assertEqual(b.loc['1','normalized_burden_hr'],1.);self.assertTrue(np.isnan(b.loc['2','normalized_burden_hr']));self.assertEqual(b.loc['2','status'],'unresolved')
 def test_gini(self):self.assertAlmostEqual(population_weighted_gini(pd.Series([0.,10.]),pd.Series([1.,1.])),.5)
 def test_fixed_groups_and_absolute_outputs(self):
  q=assign_fixed_vulnerability_quartiles(pd.Series([1.,2.,3.,4.],index=['1','2','3','4']));self.assertEqual(q.tolist(),['Q1','Q2','Q3','Q4'])
  b=pd.DataFrame({'resolved_mass':[1.,1.,1.,1.],'restoration_burden_mass_hr':[1.,2.,3.,4.],'normalized_burden_hr':[1.,2.,3.,4.],'status':['resolved']*4},index=['1','2','3','4']);s=summarize_distribution(b,pd.Series(1.,index=b.index),q);self.assertEqual(s.burden_Q1_hr,1.);self.assertEqual(s.burden_Q4_hr,4.);self.assertEqual(s.signed_Q4_minus_Q1_hr,3.)
 def test_effects_and_paired_bootstrap(self):
  x=classify_tract_effects(pd.Series({'1':1.,'2':3.,'3':np.nan}),pd.Series({'1':3.,'2':1.,'3':np.nan}));self.assertEqual(x.classification.tolist(),['improved','worsened','unresolved'])
  m=pd.DataFrame({'HF':[3.,4.,5.],'GA':[2.,5.,4.]},index=['r1','r2','r3']);a=paired_realization_summary(m,'HF',bootstrap_resamples=200,bootstrap_seed=9);b=paired_realization_summary(m,'HF',bootstrap_resamples=200,bootstrap_seed=9);pd.testing.assert_frame_equal(a,b);self.assertEqual(a.loc['GA','n_realizations'],3)
if __name__=='__main__':unittest.main()
