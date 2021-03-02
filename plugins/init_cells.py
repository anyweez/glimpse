import numpy

from decorators import genreq

@genreq(cellprops=[])
def generate(world, vd):
    '''
    Mark boundary cells and assign latitude/longitude to each cell from Voronoi diagram.

    A boundary cell is a cell that extends beyond the edge of the world. This function updates each
    cell's `boundary` property to properly reflect whether they're a boundary cell.
    '''

    # Add latitude and longitude from the Voronoi diagram
    latitude_arr = numpy.full(world.get_cellcount(), -1, dtype=numpy.double)
    longitude_arr = numpy.full(world.get_cellcount(), -1, dtype=numpy.double)

    for cell_idx in world.cell_idxs():
        (latitude, longitude) = vd.centroid(cell_idx)

        latitude_arr[cell_idx] = latitude
        longitude_arr[cell_idx] = longitude

    world.add_cell_property('latitude', latitude_arr)
    world.add_cell_property('longitude', longitude_arr)

    # A landform won't consider a high-elevation a "mountain" unless it exceeds this elevation.
    # In particular, it won't be designated as a POI and won't be named.
    world.set_param('MountainMinHeight', 0.75)