import random, numpy

from world import Cell
from decorators import genreq
from noise import snoise2

NoiseConfig = {
    'scale': 3.0,           # top tweak
    'octaves': 6,
    'persistence': 1.35,    # amplitude multiplier
    'lacunarity': 1.5,      # frequency multiplier
    'base': random.randint(0, 1000)
}

def __gen_noise(x, y, config):
    scaled_x = x / config['scale']
    scaled_y = y / config['scale']

    octaves = config['octaves']
    persistence = config['persistence']
    lacunarity = config['lacunarity']

    base = config['base']

    return ( snoise2(scaled_x, scaled_y, octaves=octaves, persistence=persistence, lacunarity=lacunarity, base=base) + 1.0) / 2.0


@genreq(cellprops=['celltype', 'latitude', 'longitude'], worldparams=['has_lakes'])
def generate(world, vd):

    def calculate_cell_moisture(idx):
        base = __gen_noise(world.cp_latitude[idx], world.cp_longitude[idx], NoiseConfig)

        dist_water = world.graph.distance(idx, lambda dest_idx: world.cp_celltype[dest_idx] == Cell.Type.WATER)

        # Cells closer to water have higher moisture levels. 
        # "Moisture" refers to rainfall, not just the existance of water.
        if world.cp_celltype[idx] == Cell.Type.WATER:
            base += 0.25
        elif dist_water == 1:
            base += 0.2
        elif dist_water == 2:
            base += 0.12
        elif dist_water == 3:
            base += 0.04
        
        return max(0.0, min(0.99, base))

    moisture_list = [calculate_cell_moisture(idx) for idx in world.cell_idxs()]
    moisture_arr = world.new_cp_array(numpy.double, moisture_list)
    world.add_cell_property('moisture', moisture_arr)