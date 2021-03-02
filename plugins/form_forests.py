import numpy, random

from decorators import genreq
from world import Cell

NumForests = random.randint(2, 5)
SampleSize = 10
ScoreThresholdMultiplier = 0.8

@genreq(cellprops=['celltype', 'elevation', 'biome'], worldparams=['has_lakes'])
def generate(world, vd):
    '''
    Generate a series of forests across the map.
    '''
    
    forest_arr = world.new_cp_array(numpy.int8, -1)
    
    def valid_forest_cells(edge):
        (src, dest) = edge

        return world.cp_celltype[src] == Cell.Type.LAND and \
            world.cp_celltype[dest] == Cell.Type.LAND

    landgraph = world.graph.subgraph(valid_forest_cells)

    # Relative weights of each biome's ability to support a forest.
    biome_score = (0, 10, 0, 25, 25, 0, 0, 40)

    def score(region_idx):
        '''
        Cells are scored based on their proximity to water and their elevation.
        Closer to water and lower elevation are both better.
        '''
        if world.cp_celltype[region_idx] == Cell.Type.WATER:
            return -100.0

        # Certain biomes are more supportive of forests. Higher elevations are
        # less supportive, no matter the biome type.
        points_biome = biome_score[world.cp_biome[region_idx]]
        elevation_penalty = 10 * (1.0 - world.cp_elevation[region_idx])

        return points_biome - elevation_penalty

    # Sample a bunch of different cells and pick the one with the highest score
    for forest_id in range(NumForests):
        # Choose from all unassigned land cells.
        land_cells = numpy.argwhere((forest_arr == -1) & (world.cp_celltype == Cell.Type.LAND))[:, 0]
        
        # All cultures currently require land to settle; if there are no land cells, skip.
        if len(land_cells) == 0:
            break

        samples = random.choices(land_cells, k=SampleSize)
        scores = [score(idx) for idx in samples]

        top_cell_idx = samples[scores.index(max(scores))]
        threshold = max(scores) * ScoreThresholdMultiplier

        forest = set([top_cell_idx,])

        for dist in range(1, random.randint(5, 10)):
            expanded = [ 
                idx 
                for idx in landgraph.neighbors(top_cell_idx, dist=dist) 
                if score(idx) > threshold and random.random() > 0.10 * dist
            ]

            forest.update(expanded)

        for idx in list(forest):
            forest_arr[idx] = forest_id

    world.add_cell_property('forest_id', forest_arr)