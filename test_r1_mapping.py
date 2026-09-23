import unittest
import numpy as np
from r1_mapping import generate_mapping, load_mapping, BASELINE_PATH, ROOT
class MappingTests(unittest.TestCase):
    def test_frozen_baseline_and_revised(self):
        for constrained, path in [(False,BASELINE_PATH),(True,ROOT/'R1_Comment1_July92_Utility_Constraint/JULY_UTILITY_CONSTRAINED_92.csv')]:
            w, raw = generate_mapping(utility_constrained=constrained)
            retained = load_mapping(path).reindex(index=w.index,columns=w.columns,fill_value=0)
            np.testing.assert_allclose(w,retained,rtol=0,atol=1e-12)
            np.testing.assert_allclose(w.sum(axis=1),1,atol=1e-14)
            self.assertEqual(w.shape,(2315,92))
    def test_lax_cutoff(self):
        w,raw=generate_mapping()
        self.assertAlmostEqual(raw.loc['06037980028','301637'],.011981819840446373)
        self.assertEqual(w.loc['06037980028','301637'],0)
if __name__=='__main__':unittest.main()
