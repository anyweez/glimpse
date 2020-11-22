import random
import structs

from structs import Cell

class Forest(structs.AbstractCellGroup):
    def __init__(self, cells, vor, graph):
        super().__init__(cells, vor, graph)


SampleSize = 10
ScoreThresholdMultiplier = 0.8

def PlaceForest(world, existing_forests):
    def edge_filter(edge):
        (src, dest) = edge

        return world.get_cell(src).type == Cell.Type.LAND and \
            world.get_cell(dest).type == Cell.Type.LAND

    # Create a subgraph containing only land cells
    graph = world.graph.subgraph(edge_filter)


    def score(region_idx):
        '''
        Cells are scored based on their proximity to water and their elevation.
        Closer to water and lower elevation are both better.
        '''
        def water(dest_idx):
            return world.get_cell(dest_idx).type == structs.Cell.Type.WATER

        cell = world.get_cell(region_idx)

        if cell.type == structs.Cell.Type.WATER:
            return -100.0

        (_, dist_to_water) = graph.distance(region_idx, water, max_distance=10)

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

    def proximity(idx):
        '''
        Returns True if this cell is within an acceptable proximity of the center cell. There is
        a significant random component to this, though the probability of a True is higher the
        closer the cell is to the center of the forest.
        '''
        center = best_yet_cell.region_idx

        (_, dist) = graph.distance(center, lambda next_idx: next_idx == idx)

        return random.random() > (dist * 5) / 100.0

    cell_idxs = list( filter(lambda idx: score(idx) > threshold and proximity(idx), graph.floodfill(best_yet_cell.region_idx)) )

    return Forest( world.get_cells(cell_idxs), world.vor, world.graph )