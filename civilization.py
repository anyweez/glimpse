from structs import Cell
import graph

class City(object):
    def __init__(self, cell):
        self.cell = cell
        self.location = cell.location



def PlaceCity(world, existing_cities):
    existing_cells = set( map(lambda city: city.cell.region_idx, existing_cities) )

    def survivability(cell):
        if cell.type == Cell.Type.WATER:
            return -1000.0

        return 0.0

    def economy(cell):
        # Can travel over and land cell
        def travel(source_idx, dest_idxs, context):
            cells = world.get_cells(dest_idxs)

            return list( filter(lambda cell: cell.type == Cell.Type.LAND, cells) )

        # Destination is a water cell
        def water(dest_idx):
            return world.get_cell_by_id(dest_idx).type == Cell.Type.WATER

        dist = world.graph.distance(cell, travel, water)

        return max(5 - dist, 0) * 10.0

    def threat(cell):
        # If a city already exists in this cell, threat level is high
        # if len( list(filter(lambda city: city.cell.region_idx == cell.region_idx, existing_cities)) ) > 0:
        #     print('Threat factor high for city #%d' % (len(existing_cities) + 1))
        #     return 100.0

        def travel(source_idx, dest_idxs, context):
            pass

        def other_city(dest_idx):
            return dest_idx in existing_cells

        # Find the distance to the nearest city. The closer, the more dangerous.
        dist = world.graph.distance(cell, travel, other_city, max_distance=50)

        return max(0.0, 100.0 - (dist * 2.0))

    top_cell = None
    top_score = -1000000

    print('testing %d cells...' % (len(world.cells, )))

    for cell in world.cells:
        score = survivability(cell) + economy(cell) - threat(cell)

        if score > top_score:
            top_cell = cell
            top_score = score

    return City(top_cell)