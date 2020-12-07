import numpy, functools, math

from decorators import genreq
from world import Cell

@genreq(cellprops=['celltype', 'elevation', 'depth'])
def generate(world, vd):
    '''
    Create lakes in low 'bowls' where water runs downhill and doesn't have a way to get out to an
    ocean. Simulate rainfall and fill areas at the bottom of the hill.
    '''

    water_depth = [0,] * len(world.cell_idxs())

    # Find the cell with the lowest elevation out of a list of cells
    def lowest_cell(all_cells):
        return functools.reduce(lambda a, b: a if world.cp_elevation[a] < world.cp_elevation[b] else b, all_cells, all_cells[0])

    # For each land cell, visit neighbors @ lower elevations until you reach water or don't have
    # neighbors @ lower elevation. If you reach water, end with no side-effects. If you reach a
    # bowl, increase water depth by one.
    for cell_idx in numpy.argwhere(world.cp_celltype == Cell.Type.LAND)[:, 0]:
        neighbors = world.graph.neighbors(cell_idx)

        if len(neighbors) > 0:
            next_cell = lowest_cell(neighbors)

            # Keep flowing while we haven't hit water
            while world.cp_elevation[next_cell] < world.cp_elevation[cell_idx]:
                cell_idx = next_cell

                neighbors = world.graph.neighbors(cell_idx)
                next_cell = lowest_cell(neighbors)

                # If we've hit a cell that's already water, finish.
                if world.cp_celltype[next_cell] == Cell.Type.WATER:
                    break
            
            # If we ended on land, increase water depth.
            if world.cp_celltype[next_cell] == Cell.Type.LAND:
                water_depth[next_cell] += 1

    # Convert cells to water if enough water has pooled up. If the pool is big enough, start
    # filling up surrounding cells as well.
    celltype_arr = world.new_cp_array(None, world.cp_celltype)

    for cell_idx, depth in enumerate(water_depth):
        if depth > world.std_density(20):
            celltype_arr[cell_idx] = Cell.Type.WATER
            pool = [cell_idx,]

            # If we've over-filled a cell, flow into the next lowest cell connected to the pool.
            # Each time the pool expands, future expansions can go into the neighboring LAND cells
            # connected to any part of the pool. The lowest elevation cell will always be selected.
            for _ in range( math.floor(depth / 10) ):
                neighbors = []

                for c in pool:
                    for neighbor in [n for n in world.graph.neighbors(c) if celltype_arr[n] == Cell.Type.LAND]:
                        neighbors.append(neighbor)

                # Its rare but possible that a cell won't have any LAND neighbors, which causes a crash without this check.
                if len(neighbors) > 0:
                    lowest = lowest_cell(neighbors)

                    celltype_arr[lowest] = Cell.Type.WATER
                    pool.append(lowest)
            
            # Set depth for new lake cells
            waterline_height = max([ world.cp_elevation[idx] for idx in pool ])

            for idx in pool:
                world.cp_depth[idx] = waterline_height - world.cp_elevation[idx]

    world.add_cell_property('celltype', celltype_arr)
    world.set_param('has_lakes', True)