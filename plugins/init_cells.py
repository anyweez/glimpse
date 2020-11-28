import numpy

from decorators import genreq

@genreq(cellprops=[])
def generate(world, vd):
    '''
    Mark boundary cells and assign latitude/longitude to each cell from Voronoi diagram.

    A boundary cell is a cell that extends beyond the edge of the world. This function updates each
    cell's `boundary` property to properly reflect whether they're a boundary cell.
    '''

    # Store the voronoi region idx for the cell.
    v_idxs = sorted(vd.vor.point_region)
    voronoi_idx = world.new_cp_array(numpy.uint32, v_idxs)

    world.add_cell_property('voronoi_idx', voronoi_idx)

    # Add latitude and longitude from the Voronoi diagram
    latitude_arr = numpy.full(world.get_cellcount(), -1, dtype=numpy.double)
    longitude_arr = numpy.full(world.get_cellcount(), -1, dtype=numpy.double)

    for point_idx, v_idx in enumerate(vd.vor.point_region):
        # Get the cell idx for the voronoi region idx
        # TODO: check performance implications; this is O(N^2) and may be slow
        cell_idx = v_idxs.index(v_idx)

        latitude_arr[cell_idx] = vd.vor.points[point_idx][0]
        longitude_arr[cell_idx] = vd.vor.points[point_idx][1]

    world.add_cell_property('latitude', latitude_arr)
    world.add_cell_property('longitude', longitude_arr)