import numpy, random, functools

from structs import Cell

SampleSize = 10
ScoreThresholdMultiplier = 0.8

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


    for forest_id in range(5):
        samples = random.choices(land_cells, k=SampleSize)
        scores = list( map(score, samples) )

        top_cell_idx = samples[scores.index(max(scores))]
        threshold = max(scores) * ScoreThresholdMultiplier

        def proximity(idx):
            '''
            Returns True if this cell is within an acceptable proximity of the center cell. There is
            a significant random component to this, though the probability of a True is higher the
            closer the cell is to the center of the forest.
            '''
            (_, dist) = landgraph.distance(top_cell_idx, lambda next_idx: next_idx == idx)

            return random.random() > (dist * 5) / 100.0

        cell_idxs = list( filter(lambda idx: score(idx) > threshold and proximity(idx), landgraph.floodfill(top_cell_idx)) )

        for idx in cell_idxs:
            forest_arr[idx] = forest_id

    world.add_cell_property('forest_id', forest_arr)