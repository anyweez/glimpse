import numpy

from world import Cell
from decorators import genreq

@genreq(cellprops=['celltype',])
def generate(world, vd):
    Unassigned = -1
    next_landform_id = 0

    # All cells start off with a plate_id of -1 (unassigned)
    landform_id_arr = world.new_cp_array(numpy.int16, Unassigned)

    # Create a subgraph containing edges for land cells only
    def land_only(edge):
        return world.cp_celltype[ edge[0] ] == Cell.Type.LAND and \
            world.cp_celltype[ edge[1] ] == Cell.Type.LAND

    landgraph = world.graph.subgraph(land_only)

    for idx in [i for i in world.cell_idxs() if world.cp_celltype[i] == Cell.Type.LAND]:
        # If this cell isn't yet assigned to a landform, create a new one and floodfill
        # to all connected cells. All connected cells should share a common landform_id
        if landform_id_arr[idx] == Unassigned:
            landform_id_arr[idx] = next_landform_id

            for filled_idx in landgraph.floodfill(idx):
                landform_id_arr[filled_idx] = next_landform_id

            next_landform_id += 1

    world.add_cell_property('landform_id', landform_id_arr)