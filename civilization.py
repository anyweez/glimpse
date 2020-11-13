from structs import Cell
import graph

class City(object):
    def __init__(self, cell):
        self.cell = cell
        self.location = cell.location



def PlaceCity(world, existing_cities):
    existing_cells = set( map(lambda city: city.cell.region_idx, existing_cities) )

    def survivability(idx): 
        if world.get_cell(idx).type == Cell.Type.WATER:
            return -1000.0

        return 0.0

    def economy(idx):
        # Can travel over and land cell
        def travel(source_idx, dest_idxs, context):
            return [c.region_idx for c in world.get_cells(dest_idxs) if c.type == Cell.Type.LAND]

        # Destination is a water cell
        def water(dest_idx):
            return world.get_cell(dest_idx).type == Cell.Type.WATER

        (_, dist) = world.graph.distance(idx, travel, water, max_distance=5)

        return max(5 - dist, 0) * 10.0

    def threat(idx):
        # Any land cell is eligible for travel
        def travel(source_idx, next_idxs, context):
            return [c.region_idx for c in world.get_cells(next_idxs) if c.type == Cell.Type.LAND]

        def other_city(dest_idx):
            return dest_idx in existing_cells

        # Find the distance to the nearest city. The closer, the more dangerous.
        (_, dist) = world.graph.distance(idx, travel, other_city, max_distance=20)

        return max(0.0, 100.0 - (dist * 5.0))

    top_cell = None
    top_score = -1000000

    for c in world.cells:
        score = survivability(c.region_idx) + economy(c.region_idx) - threat(c.region_idx)

        if score > top_score:
            top_cell = c
            top_score = score

    return City(top_cell)