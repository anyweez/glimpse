import random, numpy, math

from world import Cell
from decorators import genreq

@genreq(cellprops=['celltype', 'latitude', 'elevation'], worldparams=['has_lakes'])
def generate(world, vd):
    min_temperature = random.random() / 5.0         # [0.0, 0.2]
    max_temperature = 1 - (random.random() / 5.0)   # [0.8, 1.0]
    
    def gen_temperature(location, elevation):
        (latitude, _) = location

        # Normalize latitude to [0, 1] so the range of `base` is properly constrained.
        norm_lat = (latitude + 90) / 180

        base = math.sin(norm_lat * math.pi) * (max_temperature - min_temperature) + min_temperature
        base -= (0.2 * elevation)

        return max(0, min(1, base))

    temperature_list = [gen_temperature(vd.centroid(idx), world.cp_elevation[idx]) for idx in world.cell_idxs()]
    temperature_arr = world.new_cp_array(numpy.double, temperature_list)

    world.add_cell_property('temperature', temperature_arr)