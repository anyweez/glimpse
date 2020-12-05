import random, numpy, math

from world import Cell
from decorators import genreq

@genreq(cellprops=['celltype', 'latitude'], worldparams=['has_lakes'])
def generate(world, vd):
    def gen_temperature(latitude, elevation):
        base = math.sin(latitude * math.pi) - (0.2 * elevation)

        return max(0, min(1, base))

    temperature_list = [gen_temperature(world.cp_latitude[idx], world.cp_elevation[idx]) for idx in world.cell_idxs()]
    temperature_arr = world.new_cp_array(numpy.double, temperature_list)

    world.add_cell_property('temperature', temperature_arr)