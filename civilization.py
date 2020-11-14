from structs import Cell
import graph

class City(object):
    def __init__(self, cell):
        self.cell = cell
        self.location = cell.location

def Score(region_idx, world, existing_cities=[]):
    existing_cells = set( map(lambda city: city.cell.region_idx, existing_cities) )

    def survivability(idx): 
        cell = world.get_cell(idx)

        # Cities can't surive in water cells
        if cell.type == Cell.Type.WATER:
            return -1000.0

        # People strongly prefer not to settle on one-tile islands (completely
        # surrounded by water).
        neighbors = world.get_cells( world.graph.neighbors(idx) )
        if len([c for c in neighbors if c.type != Cell.Type.WATER]) == 0:
            return -100.0

        # Living at high elevations is harder
        if cell.elevation > 0.80:
            return 2.0

        return 10.0

    def economy(idx):
        # Can travel over and land cell
        def travel(source_idx, dest_idxs, _):
            return dest_idxs

        # Destination is a water cell
        def water(dest_idx):
            return world.get_cell(dest_idx).type == Cell.Type.WATER

        (_, dist) = world.graph.distance(idx, travel, water, max_distance=5)

        return (5 - dist) * 10.0 if dist > 0 else 0

    def threat(idx):
        # Any land cell is eligible for travel
        def travel(source_idx, next_idxs, _):
            return [c.region_idx for c in world.get_cells(next_idxs) if c.type == Cell.Type.LAND]

        def other_city(dest_idx):
            return dest_idx in existing_cells

        # Find the distance to the nearest city. The closer, the more dangerous.
        (_, dist) = world.graph.distance(idx, travel, other_city, max_distance=20)

        if dist >= 0 and dist < 20:
            return 100.0 - (dist * 5.0)
        else:
            return 0.0

    c = world.get_cell(region_idx)

    return survivability(c.region_idx) + economy(c.region_idx) - threat(c.region_idx)

def PlaceCity(world, existing_cities):
    top_cell = None
    top_score = -1000000

    for c in world.cells:    
        score = Score(c.region_idx, world, existing_cities)
    
        if score > top_score:
            top_cell = c
            top_score = score

    return City(top_cell)