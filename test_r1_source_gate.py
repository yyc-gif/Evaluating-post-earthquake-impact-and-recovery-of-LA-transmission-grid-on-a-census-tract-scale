import unittest, ast, logging, tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
from types import SimpleNamespace
from r1_source_gate import evaluate_source_gate,save_gate_trace
class GateTests(unittest.TestCase):
    def test_decomposition_and_unknown(self):
        g=nx.path_graph(['S','A','B','U']);f=pd.DataFrame([[1,.09,1,np.nan],[1,1,1,np.nan]],index=[0.,2.],columns=list(g))
        a=evaluate_source_gate(f,g,['S'])
        self.assertEqual(a.L_threshold.loc[0,'A'],.09)
        self.assertEqual(a.L_source.loc[0,'B'],1)
        self.assertTrue(a.e.U.isna().all())
        np.testing.assert_allclose(a.L_self+a.L_threshold+a.L_source,a.L_total,equal_nan=True)
        with tempfile.TemporaryDirectory() as d:
            save_gate_trace(a,Path(d)/'x.npz',realization_id='r',strategy_id='p')
            with np.load(Path(d)/'x.npz') as z:np.testing.assert_equal(z['f'],f.to_numpy())
    def test_identity_and_no_mutation(self):
        g=nx.path_graph(['S','A']);f=pd.DataFrame(1.,index=[0.,1.],columns=list(g));before=f.copy()
        a=evaluate_source_gate(f,g,['S']);b=evaluate_source_gate(f,g,['S'],mode='no_gate')
        pd.testing.assert_frame_equal(a.e,b.e);pd.testing.assert_frame_equal(f,before)
    def test_matches_july_function(self):
        text=Path('C257H_Project_Main.py').read_text(encoding='utf-8-sig');tree=ast.parse(text)
        fs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'clean_substation_id','apply_source_gate_to_substation_series'}]
        ns={'np':np,'pd':pd,'nx':nx,'logging':logging}
        code=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+fs,type_ignores=[])
        exec(compile(ast.fix_missing_locations(code),'<July gate>','exec'),ns)
        g=nx.path_graph(['S','A','B']);f=pd.DataFrame([[1,.5,.09],[1,.04,1],[1,1,1]],index=[0.,1.,2.],columns=list(g))
        legacy=ns['apply_source_gate_to_substation_series'](f,g,SimpleNamespace(SOURCE_GATE_ENABLED=True,FUNCTIONAL_THRESHOLD=.5),source_ids={'S'})
        pd.testing.assert_frame_equal(legacy,evaluate_source_gate(f,g,['S']).e)
if __name__=='__main__':unittest.main()
