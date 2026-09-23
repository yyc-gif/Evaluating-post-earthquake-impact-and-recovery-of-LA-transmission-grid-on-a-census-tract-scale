import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import C257H_Project_Main as main
from C257H_Project_Main_expanded import ExpandedConfig

class EntryTests(unittest.TestCase):
    def test_output_root_and_event_kpis(self):
        old=main.OUTPUT_ROOT
        try:
            with tempfile.TemporaryDirectory() as directory:
                cfg=ExpandedConfig();cfg.OUTPUT_DIRECTORY=directory
                out=main.make_out_dirs(cfg)
                self.assertEqual(out['STAGE3_DIR'],Path(directory)/cfg.STAGE3_DIR)
        finally:main.OUTPUT_ROOT=old
        x=pd.DataFrame({'a':[.2,1.,1.]},index=[0.,10.,20.])
        k=main._revision_event_kpis(x)
        self.assertEqual(k.loc['a','Burden_hr'],8.)
        self.assertEqual(k.loc['a','T80'],10.)
        self.assertEqual(k.loc['a','AUC'],.6)
    def test_original_stages_dispatch_to_revised_functions(self):
        cfg=ExpandedConfig()
        for name,args in [('run_stage_1',[cfg,{},{}]),('run_stage_3',[cfg,{},{},{},{}]),
                          ('run_stage_4',[cfg,{},{},{},{}]),('run_stage_5',[cfg,{},{},{}]),
                          ('run_stage_6',[cfg,{},{},{},{},{}])]:
            with patch.object(main,name+'_revision',return_value={'revised':True}) as target:
                self.assertEqual(getattr(main,name)(*args),{'revised':True})
                target.assert_called_once()

if __name__=='__main__':unittest.main()
