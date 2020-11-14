import random
import structs

class Forest(structs.AbstractCellGroup):
    def __init__(self, cells, vor, graph):
        super().__init__(cells, vor, graph)


SampleSize = 10
ScoreThresholdMultiplier = 0.8

def PlaceForest(world, existing_forests):
    def score(region_idx):
        '''
        Cells are scored based on their proximity to water and their elevation.
        Closer to water and lower elevation are both better.
        '''
        def land(region_idx, dest_idxs, _):
            return list( filter(lambda idx: world.get_cell(idx).type == structs.Cell.Type.LAND, dest_idxs) )

        def water(dest_idx):
            return world.get_cell(dest_idx).type == structs.Cell.Type.WATER

        cell = world.get_cell(region_idx)
        if cell.type == structs.Cell.Type.WATER:
            return -100.0

        (_, dist_to_water) = world.graph.distance(region_idx, land, water, max_distance=10)

        return (10 - dist_to_water) + (1.0 - cell.elevation) * 10

    best_yet_cell = None
    best_yet_score = -10000.0

    # Sample a bunch of different cells and pick the one with the highest score
    land_cells = [c for c in world.cells if c.type == structs.Cell.Type.LAND]
    for _ in range(SampleSize):
        current_cell = random.choice(land_cells)
        current_score = score(current_cell.region_idx)

        if current_score > best_yet_score:
            best_yet_cell = current_cell
            best_yet_score = current_score
    
    threshold = best_yet_score * ScoreThresholdMultiplier

    forest_size = 1
    def eligible(region_idx):
        nonlocal forest_size

        is_land = world.get_cell(region_idx).type == structs.Cell.Type.LAND

        if is_land and score(region_idx) >= threshold and random.random() > (forest_size / 100.0):
            forest_size += 1

            return True

    cell_idxs = world.graph.floodfill(best_yet_cell.region_idx, eligible)

    return Forest( world.get_cells(cell_idxs), world.vor, world.graph )