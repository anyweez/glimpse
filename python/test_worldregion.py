import unittest 

import voronoi, structs

def neighbor_ids(region, region_idx, dist=1):
    return sorted( list(map(lambda c: c.region_idx, region.neighbors(region_idx, dist))) )

class VoronoiTestCase(unittest.TestCase):
    def setUp(self):
        vor = voronoi.prebuilt_vor1()

        w = structs.World(vor)
        cells = w._form_cells()

        self.wr = structs.WorldRegion(cells, vor)

    def test_vor1_checkgraph_dist1(self):
        n1 = neighbor_ids(self.wr, 37)
        self.assertEqual(n1, [38, 39, 40, 41, 42, 65])

        n2 = neighbor_ids(self.wr, 74)
        self.assertEqual(n2, [49, 52, 53, 71, 73, 75, 77])

        n3 = neighbor_ids(self.wr, 93)
        self.assertEqual(n3, [43, 59, 90, 94, 95, 97])

        n4 = neighbor_ids(self.wr, 45)
        self.assertEqual(n4, [22, 44, 46, 51, 56, 57])
    
    def test_vor1_checkgraph_distX(self):
        n1 = neighbor_ids(self.wr, 37, dist=2)
        self.assertEqual(n1, [20, 21, 27, 28, 29, 30, 32, 43, 59, 64, 66, 67, 94])

        n2 = neighbor_ids(self.wr, 76, dist=2)
        self.assertEqual(n2, [33, 52, 66, 68, 70, 72, 74, 77, 82])

        n3 = neighbor_ids(self.wr, 65, dist=3)
        self.assertEqual(n3, [15, 16, 21, 26, 28, 29, 30, 31, 35, 50, 53, 58, 60, 63, 73, 74, 76, 81, 82, 90, 95, 96, 98, 100])

    def test_vor1_isborder(self):
        # Build a subregion containing cell 52 and all immediate neighbors
        cells = self.wr.neighbors(52) + [self.wr.cellmap[52],]
        wr = structs.WorldRegion(cells, self.wr.vor)

        self.assertEqual(wr.is_border(52), False)
        self.assertEqual(wr.is_border(66), True)
        self.assertEqual(wr.is_border(50), True)
        self.assertEqual(wr.is_border(53), True)

        with self.assertRaises(structs.InvalidCellError) as context:
            wr.is_border(115)

            self.assertTrue('Didnt raise exception, got ' + str(context.exception))
