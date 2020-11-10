import unittest 

import voronoi

class VoronoiTestCase(unittest.TestCase):
    '''
    This test is intended to ensure that the pre-built voronoi diagrams haven't changed; if they
    have, other tests cases will break because of this change (not necessarily because the code is
    broken). This series of tests can be thought of as a canary in the coal mine.
    '''
    def test_stable_voronoi(self):
        vor = voronoi.prebuilt_vor1()

        self.assertEqual(vor.regions[0], [-1, 1, 2, 0, 3])
        self.assertEqual(vor.regions[1], [])
        self.assertEqual(vor.regions[2], [5, 1, -1, 4])

        self.assertEqual(len(vor.regions), 101)