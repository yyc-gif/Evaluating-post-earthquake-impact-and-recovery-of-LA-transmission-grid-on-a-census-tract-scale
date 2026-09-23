import unittest
import numpy as np,pandas as pd
from r1_capacity_screen import screen_gna
class CapacityTests(unittest.TestCase):
 def test_units_redaction_and_planning_margin(self):
  s=pd.DataFrame({'ID':['1'],'NAME':['X'],'Owner':['SCE']})
  x=pd.DataFrame({'substation_name':['X 66/12']*3,'cumulative_demand':[11,-9999,11],'fac_load_limit':[10,10,10],'facility_loading':[110,20,50],'subst_capacity':[-1,5,-1]})
  y=screen_gna(x,s)
  self.assertEqual(y.screenable.tolist(),[True,False,False]);self.assertEqual(y.loc[0,'loading_ratio'],1.1)
  self.assertEqual(y.loc[0,'subst_capacity'],-1);self.assertTrue(np.isnan(y.loc[1,'cumulative_demand']))
  pd.testing.assert_frame_equal(x,pd.DataFrame({'substation_name':['X 66/12']*3,'cumulative_demand':[11,-9999,11],'fac_load_limit':[10,10,10],'facility_loading':[110,20,50],'subst_capacity':[-1,5,-1]}))
if __name__=='__main__':unittest.main()
