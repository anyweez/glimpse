import numpy, random, functools

from decorators import genreq
from world import Cell

NumForests = 10
SampleSize = 10
ScoreThresholdMultiplier = 0.8

# FIXME: forest generation needs to run after lake generation
@genreq(cellprops=['celltype', 'elevation'], worldparams=['has_lakes'])
def generate(world, vd):
    '''
    Generate a series of forests across the map.

    TODO: replace hard-coded n=5 forests below with something based on
    a score threshold.

    TODO: forests can't spread into cells that are already forests
    '''
    
    forest_arr = world.new_cp_array(numpy.int8, -1)
    
    def land_only(edge):
        (src, dest) = edge

        return world.cp_celltype[src] == Cell.Type.LAND and \
            world.cp_celltype[dest] == Cell.Type.LAND

    landgraph = world.graph.subgraph(land_only)

    def score(region_idx):
        '''
        Cells are scored based on their proximity to water and their elevation.
        Closer to water and lower elevation are both better.
        '''
        if world.cp_celltype[region_idx] == Cell.Type.WATER:
            return -100.0

        def water(dest_idx):
            return world.cp_celltype[dest_idx] == Cell.Type.WATER

        (_, dist_to_water) = landgraph.distance(region_idx, water, max_distance=10)

        return (10 - dist_to_water) + (1.0 - world.cp_elevation[region_idx]) * 10

    # Sample a bunch of different cells and pick the one with the highest score
    land_cells = numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0]


    for forest_id in range(NumForests):
        samples = random.choices(land_cells, k=SampleSize)
        scores = [score(idx) for idx in samples]

        top_cell_idx = samples[scores.index(max(scores))]
        threshold = max(scores) * ScoreThresholdMultiplier

        forest = set([top_cell_idx,])

        for dist in range(1, 10):
            if random.random() < (dist / 20.0):
                break

            expanded = [ 
                idx 
                for idx in landgraph.neighbors(top_cell_idx, dist=dist) 
                if score(idx) > threshold and random.random() > 0.30
            ]

            forest.update(expanded)

        for idx in list(forest):
            forest_arr[idx] = forest_id

    world.add_cell_property('forest_id', forest_arr)