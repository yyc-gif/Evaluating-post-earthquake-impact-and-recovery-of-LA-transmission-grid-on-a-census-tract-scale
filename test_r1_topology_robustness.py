import unittest
import networkx as nx
from r1_topology_robustness import characterize_topology
class TopologyTests(unittest.TestCase):
 def test_single_path_and_own_source(self):
  g=nx.path_graph(['S','A','B']);t=characterize_topology(g,['S'])
  self.assertEqual(t.loc['B','minimum_edge_source_cut'],1)
  self.assertEqual(t.loc['B','minimum_node_source_cut'],1)
  self.assertEqual(t.loc['B','articulation_dependencies'],'A')
  self.assertTrue(t.loc['B','single_path']);self.assertTrue(t.loc['S','local_active_source'])
 def test_two_independent_sources(self):
  g=nx.Graph([('X','A'),('A','S'),('X','B'),('B','T')]);t=characterize_topology(g,['S','T'])
  self.assertEqual(t.loc['X','reachable_active_sources'],2)
  self.assertEqual(t.loc['X','minimum_edge_source_cut'],2)
  self.assertEqual(t.loc['X','minimum_node_source_cut'],2)
  self.assertEqual(t.loc['X','articulation_dependencies'],'')
if __name__=='__main__':unittest.main()
