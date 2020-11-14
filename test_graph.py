import unittest
import graph

def g1():
    edges = [
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 5),
        (5, 7),
    ]

    return graph.Graph(edges)

class GraphTestCase(unittest.TestCase):
    # def setUp(self):
    #     vor = voronoi.prebuilt_vor1()
    #     cells = structs.Cell.FormCells(vor)
    #     worldgraph = graph.BuildGraph(cells, vor)
    
    #     self.wr = structs.WorldRegion(cells, vor, worldgraph)

    def test_node_count(self):
        self.assertEqual(g1().node_count(), 6)

    def test_edge_count(self):
        self.assertEqual(g1().edge_count(), 5)
    
    def test_neighbors(self):
        self.assertEqual( g1().neighbors(1), [2, 3, 4] )
        self.assertEqual( g1().neighbors(2), [5,] )

        self.assertEqual( g1().neighbors(1, dist=2), [5,] )
    
    def test_distance_success(self):
        self.assertEqual( g1().distance(
            1, 
            lambda _, idxs, __: idxs, 
            lambda idx: idx == 5
        ), (5, 2))

    def test_distance_overmax(self):
        self.assertEqual( g1().distance(
            1, 
            lambda _, idxs, __: idxs, 
            lambda idx: idx == 5,
            max_distance=1
        ), (None, -1))